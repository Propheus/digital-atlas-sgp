"""
Build travel_matrix.parquet — 332×332 multimodal travel times between subzones.

Modes (minutes):
  T_walk  : Euclidean × 1.3 / 4 km/h, cap 2 km (else large)
  T_drive : Euclidean × 1.25 / 28 km/h + 2 min
  T_rail  : walk-to-feeder-station + 3 min wait + station path + walk-from-feeder-station
            (requires station within 1200m of both home points)
  T_bus   : 1.8 × walk-to-stop (300m avg) + 2.0 × wait (5 min) + Euclidean × 1.4 / 22 km/h
            + 1.8 × walk-from-stop
  T_composite = element-wise min across all four modes

Plus spot-checks for 10 known OD pairs against priors.

Output schema:
  from_code, to_code, T_walk, T_drive, T_rail, T_bus, T_composite
"""
import numpy as np
import pandas as pd
import geopandas as gpd
from scipy.spatial import cKDTree

BASE = "/home/azureuser/digital-atlas-sgp"
OUT = f"{BASE}/scenario_sim/cache/travel_matrix.parquet"
OUT_NPZ = f"{BASE}/scenario_sim/cache/travel_matrix.npz"

WALK_KMH = 4.0
WALK_MEANDER = 1.3
WALK_CAP_KM = 2.0
DRIVE_KMH = 35.0        # SGP expressway-assisted off-peak average
DRIVE_MEANDER = 1.2     # expressway coverage means fairly direct routes
DRIVE_EGRESS_MIN = 2.0
BUS_KMH = 24.0          # slight bump from 22; buses use bus lanes on arterials
BUS_MEANDER = 1.4
BUS_WALK_M = 300.0
BUS_WAIT_MIN = 5.0
WALK_PENALTY = 1.8
WAIT_PENALTY = 2.0
RAIL_FEEDER_M = 1200.0
RAIL_WAIT_MIN = 3.0

LARGE_MIN = 999.0  # finite sentinel for "not reachable by this mode"

def latlon_to_xy_m(lats, lons):
    """Quick equirectangular projection to meters around SG (centered lat 1.35)."""
    lat0 = 1.35
    mx = np.cos(np.deg2rad(lat0)) * 111320.0
    my = 111320.0
    return np.asarray(lons) * mx, np.asarray(lats) * my

def main():
    # --- subzone centroids (home points)
    cent = pd.read_parquet(f"{BASE}/scenario_sim/cache/centroids.parquet")
    cent = cent.sort_values("subzone_code").reset_index(drop=True)
    n = len(cent)
    codes = cent["subzone_code"].tolist()
    hx, hy = latlon_to_xy_m(cent["home_lat"].to_numpy(), cent["home_lon"].to_numpy())
    print(f"[04] subzones: {n}")

    # --- Euclidean distances in meters (n×n)
    dx = hx[:, None] - hx[None, :]
    dy = hy[:, None] - hy[None, :]
    dist_m = np.sqrt(dx * dx + dy * dy).astype(np.float32)
    print(f"[04] Euclidean dist: mean={dist_m[dist_m>0].mean():.0f}m  max={dist_m.max():.0f}m")

    # --- T_walk
    walk_dist = dist_m * WALK_MEANDER
    T_walk = walk_dist / (WALK_KMH * 1000 / 60)
    T_walk[walk_dist > WALK_CAP_KM * 1000] = LARGE_MIN
    np.fill_diagonal(T_walk, 2.0)  # within-subzone walk avg 2 min

    # --- T_drive
    drive_dist = dist_m * DRIVE_MEANDER
    T_drive = drive_dist / (DRIVE_KMH * 1000 / 60) + DRIVE_EGRESS_MIN
    np.fill_diagonal(T_drive, 3.0)

    # --- T_bus
    bus_ride = (dist_m * BUS_MEANDER) / (BUS_KMH * 1000 / 60)
    walk_to_stop_min = BUS_WALK_M / (WALK_KMH * 1000 / 60)
    T_bus = (
        WALK_PENALTY * walk_to_stop_min
        + WAIT_PENALTY * BUS_WAIT_MIN
        + bus_ride
        + WALK_PENALTY * walk_to_stop_min
    )
    np.fill_diagonal(T_bus, 4.0)

    # --- T_rail: needs station assignments
    stations = pd.read_parquet(f"{BASE}/scenario_sim/cache/stations.parquet")
    times = pd.read_parquet(f"{BASE}/scenario_sim/cache/station_times.parquet")
    print(f"[04] stations: {len(stations)}  pairs: {len(times)}")

    # Station coordinates in metric
    sx, sy = latlon_to_xy_m(stations["lat"].to_numpy(), stations["lon"].to_numpy())
    station_xy = np.column_stack([sx, sy])
    sid_to_idx = {sid: i for i, sid in enumerate(stations["station_id"].tolist())}

    # Station-to-station time matrix (dense)
    ns = len(stations)
    stn_t = np.full((ns, ns), LARGE_MIN, dtype=np.float32)
    np.fill_diagonal(stn_t, 0.0)
    for _, row in times.iterrows():
        i = sid_to_idx.get(row["from_station"])
        j = sid_to_idx.get(row["to_station"])
        if i is not None and j is not None:
            stn_t[i, j] = row["time_min"]

    # For each subzone, find feeder stations within RAIL_FEEDER_M
    home_xy = np.column_stack([hx, hy])
    tree = cKDTree(station_xy)
    feeder_dists, feeder_idxs = tree.query(home_xy, k=3)  # up to 3 nearest stations

    # For each (i, j), try every combination of (feeder_i, feeder_j) and take min
    T_rail = np.full((n, n), LARGE_MIN, dtype=np.float32)
    no_rail_count = 0
    for i in range(n):
        # Filter to stations within feeder distance
        valid_i = [(feeder_idxs[i, k], feeder_dists[i, k]) for k in range(3) if feeder_dists[i, k] <= RAIL_FEEDER_M]
        if not valid_i:
            no_rail_count += 1
            continue
        for j in range(n):
            if i == j:
                T_rail[i, j] = 5.0
                continue
            valid_j = [(feeder_idxs[j, k], feeder_dists[j, k]) for k in range(3) if feeder_dists[j, k] <= RAIL_FEEDER_M]
            if not valid_j:
                continue
            best = LARGE_MIN
            for (fi, di) in valid_i:
                walk_i_min = (di * WALK_MEANDER) / (WALK_KMH * 1000 / 60) * WALK_PENALTY
                for (fj, dj) in valid_j:
                    walk_j_min = (dj * WALK_MEANDER) / (WALK_KMH * 1000 / 60) * WALK_PENALTY
                    ride = stn_t[fi, fj]
                    total = walk_i_min + WAIT_PENALTY * RAIL_WAIT_MIN + ride + walk_j_min
                    if total < best:
                        best = total
            T_rail[i, j] = best

    print(f"[04] subzones without rail access (<{RAIL_FEEDER_M}m to station): {no_rail_count}")

    # --- Composite
    T_composite = np.minimum.reduce([T_walk, T_drive, T_rail, T_bus])

    # Stats
    for name, M in [("walk", T_walk), ("drive", T_drive), ("rail", T_rail), ("bus", T_bus), ("composite", T_composite)]:
        finite = M[M < LARGE_MIN]
        print(f"[04] T_{name:9s}: p50={np.percentile(finite, 50):5.1f}  p90={np.percentile(finite, 90):5.1f}  "
              f"max={finite.max():5.1f}  inf_share={(M >= LARGE_MIN).mean():.1%}")

    # --- Spot checks
    code_to_idx = {c: i for i, c in enumerate(codes)}
    def lookup(name_or_code):
        if name_or_code in code_to_idx:
            return code_to_idx[name_or_code]
        return None

    # Need some well-known subzones — use centroid lat/lon to find subzones in known planning areas
    # Read subzone state to get planning_area
    state = pd.read_parquet(f"{BASE}/scenario_sim/cache/subzone_state.parquet")
    state_by_code = state.set_index("subzone_code")

    def first_sz_in_pa(pa_keyword):
        m = state[state["planning_area"].str.contains(pa_keyword, case=False, na=False)]
        if len(m):
            code = m.iloc[0]["subzone_code"]
            return code_to_idx.get(code), code
        return None, None

    pairs = [
        ("Jurong East", "Downtown Core", "~20 min"),
        ("Tampines", "Tuas", "~70 min"),
        ("Ang Mo Kio", "Bishan", "~8 min"),
        ("Woodlands", "Changi", "~55 min"),
        ("Sengkang", "Orchard", "~28 min"),
        ("Yishun", "Bukit Merah", "~30 min"),
        ("Jurong West", "Pasir Ris", "~55 min"),
    ]
    print("\n[04] spot checks (composite travel time):")
    for a, b, expected in pairs:
        ia, ca = first_sz_in_pa(a)
        ib, cb = first_sz_in_pa(b)
        if ia is not None and ib is not None:
            t = T_composite[ia, ib]
            print(f"      {a:15s}({ca}) -> {b:15s}({cb}): {t:5.1f} min  expected {expected}")
        else:
            print(f"      {a:15s} -> {b:15s}: subzone not found")

    # --- Write outputs
    # Dense npz for fast engine loading
    np.savez_compressed(
        OUT_NPZ,
        codes=np.array(codes),
        T_walk=T_walk,
        T_drive=T_drive,
        T_rail=T_rail,
        T_bus=T_bus,
        T_composite=T_composite,
    )
    print(f"\n[04] wrote dense matrix: {OUT_NPZ}")

    # Long parquet — skip the all-pairs expansion to save disk; just sample for sanity
    rows = []
    sample_n = 2000
    rng = np.random.default_rng(42)
    idx_pairs = rng.choice(n, size=(sample_n, 2))
    for i, j in idx_pairs:
        rows.append({
            "from_code": codes[i], "to_code": codes[j],
            "T_walk": float(T_walk[i, j]), "T_drive": float(T_drive[i, j]),
            "T_rail": float(T_rail[i, j]), "T_bus": float(T_bus[i, j]),
            "T_composite": float(T_composite[i, j]),
        })
    df = pd.DataFrame(rows)
    df.to_parquet(OUT, index=False)
    print(f"[04] wrote sampled long-format parquet: {OUT}  ({sample_n} rows, sanity only)")

if __name__ == "__main__":
    main()
