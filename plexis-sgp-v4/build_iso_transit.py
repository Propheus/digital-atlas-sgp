"""
Plexis SGP v4 — S2b Transit isochrone catchments (iso_transit15_*) per hex8.

Spec: SITE_SELECTION_METRICS.md §S2 (transit part). Companion to build_iso_walk.py.

Door-to-door time model (weekday AM peak):
  origin (hex8 activity centroid)
    -> access walk to stops within 600 m euclid (x1.3 detour, 80 m/min)
    -> board: wait = min(headway_am/2, 30 min) at the (route, direction, stop)
    -> ride: median in-vehicle time between consecutive stops (AM trips)
    -> alight 0.5 min; transfers via stop-stop walk edges (<=200 m)
    -> egress walk from stop to hex9 demand centroids (<=700 m)
  plus a pure-walk arm (origin -> hex9 direct, x1.3 detour) so hexes without
  AM transit still get their walk reach counted.

Graph: directed, nodes = stops + (route,dir,stop) with AM service + 1,191
origin nodes; one Dijkstra pass (chunked) for all origins, capped at 50 min.
The full origin->hex9 minute matrix is cached (hex8_hex9_transit_min.npz) —
S2b thresholds it at 15 min; S5 labor-shed reuses it at 30/45 min.

Demand at hex9 grain (transit reach is multi-km; hex9 quantization is fine
here, unlike the 800 m walk case — documented grain difference vs S2a).

Output: hex/hex8_iso_transit.parquet, hex/hex8_hex9_transit_min.npz,
        hex/iso_transit_report.json
"""
import json
import time
from pathlib import Path

import h3
import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree

ROOT = Path(__file__).parent
GTFS = ROOT.parent / "data/gtfs/singapore-gtfs"

WALK_MPM = 80.0          # metres per minute (4.8 km/h)
DETOUR = 1.3             # euclid -> network walk factor for access/egress legs
ACCESS_M = 600.0
EGRESS_M = 700.0
TRANSFER_M = 200.0
ALIGHT_MIN = 0.5
MAX_WAIT_MIN = 30.0
AM = (7 * 3600, 9 * 3600)
RIDE_WIN = (6.5 * 3600, 9.5 * 3600)
CAP_MIN = 50.0           # computed horizon (S5 needs 45)
T15 = 15.0


def to3414(lng, lat):
    tr = Transformer.from_crs(4326, 3414, always_xy=True)
    x, y = tr.transform(np.asarray(lng), np.asarray(lat))
    return np.column_stack([x, y])


def hhmmss_to_s(col):
    p = col.str.split(":", expand=True).astype(int)
    return p[0] * 3600 + p[1] * 60 + p[2]


def activity_origins():
    """Same origin definition as build_iso_walk.py (S2a)."""
    h8 = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")
    pl = pd.read_parquet(ROOT / "places/sgp_places_final.parquet",
                         columns=["hex8_id", "latitude", "longitude"])
    act = pl.groupby("hex8_id")[["longitude", "latitude"]].mean()
    h9 = pd.read_parquet(ROOT / "hex/hex9_population.parquet")[["hex9_id", "pop_resident"]]
    h9 = h9.merge(pd.read_parquet(ROOT / "hex/hex9_universe.parquet")[["hex9_id", "lat", "lng"]],
                  on="hex9_id")
    h9["hex8_of"] = [h3.cell_to_parent(c, 8) for c in h9["hex9_id"]]
    h9 = h9[h9["pop_resident"] > 0]
    popw = h9.groupby("hex8_of").apply(
        lambda x: pd.Series({"lng": np.average(x["lng"], weights=x["pop_resident"]),
                             "lat": np.average(x["lat"], weights=x["pop_resident"])}))
    h8 = h8.set_index("hex8_id")
    h8["o_lng"] = act["longitude"].reindex(h8.index) \
        .fillna(popw["lng"].reindex(h8.index)).fillna(h8["lng"])
    h8["o_lat"] = act["latitude"].reindex(h8.index) \
        .fillna(popw["lat"].reindex(h8.index)).fillna(h8["lat"])
    return h8.reset_index()


def main():
    t0 = time.time()

    # ---- GTFS load ---------------------------------------------------------
    print("Loading GTFS...")
    stops = pd.read_csv(GTFS / "stops.txt")
    trips = pd.read_csv(GTFS / "trips.txt")
    trips = trips[trips["service_id"] == "WD"]
    st = pd.read_csv(GTFS / "stop_times.txt",
                     usecols=["trip_id", "arrival_time", "departure_time",
                              "stop_id", "stop_sequence"],
                     dtype={"stop_id": str})
    st = st.merge(trips[["trip_id", "route_id", "direction_id"]], on="trip_id",
                  how="inner")
    st["dep_s"] = hhmmss_to_s(st["departure_time"])
    st["arr_s"] = hhmmss_to_s(st["arrival_time"])
    print(f"  weekday stop_times: {len(st):,} over {st['trip_id'].nunique():,} trips")

    # ---- ride edges (AM trips, median per route-dir-hop) -------------------
    st = st.sort_values(["trip_id", "stop_sequence"])
    am_trip_start = st.groupby("trip_id")["dep_s"].transform("min")
    ride = st[(am_trip_start >= RIDE_WIN[0]) & (am_trip_start <= RIDE_WIN[1])].copy()
    nxt = ride.groupby("trip_id").shift(-1)
    hops = ride.assign(stop_b=nxt["stop_id"], arr_b=nxt["arr_s"]).dropna(subset=["stop_b"])
    hops["ride_min"] = (hops["arr_b"] - hops["dep_s"]) / 60.0
    hops = hops[(hops["ride_min"] >= 0) & (hops["ride_min"] <= 30)]
    edges_ride = (hops.groupby(["route_id", "direction_id", "stop_id", "stop_b"])
                  ["ride_min"].median().reset_index())
    print(f"  ride edges: {len(edges_ride):,}")

    # ---- AM headway per (route, dir, stop) ----------------------------------
    am_dep = st[(st["dep_s"] >= AM[0]) & (st["dep_s"] < AM[1])]
    hw = (am_dep.groupby(["route_id", "direction_id", "stop_id"])
          .size().rename("n").reset_index())
    hw["wait_min"] = np.minimum(120.0 / hw["n"] / 2.0, MAX_WAIT_MIN)

    # ---- node index ---------------------------------------------------------
    stops = stops[stops["stop_id"].isin(st["stop_id"].astype(str).unique())].reset_index(drop=True)
    stop_idx = {s: i for i, s in enumerate(stops["stop_id"])}
    n_stop = len(stops)
    rds = pd.concat([
        hw[["route_id", "direction_id", "stop_id"]],
        edges_ride[["route_id", "direction_id", "stop_id"]],
        edges_ride[["route_id", "direction_id", "stop_b"]]
        .rename(columns={"stop_b": "stop_id"}),
    ]).drop_duplicates().reset_index(drop=True)
    rds_idx = {(r, d, s): n_stop + i
               for i, (r, d, s) in enumerate(zip(rds["route_id"], rds["direction_id"],
                                                 rds["stop_id"]))}
    h8 = activity_origins()
    n_rds = len(rds)
    n_origin = len(h8)
    n_nodes = n_stop + n_rds + n_origin
    o_base = n_stop + n_rds
    print(f"  nodes: {n_stop} stops + {n_rds:,} route-dir-stops + {n_origin} origins")

    rows, cols, wts = [], [], []

    def add_edges(a, b, w):
        rows.extend(a); cols.extend(b); wts.extend(w)

    # board: stop -> route-dir-stop (wait)
    bi = hw["stop_id"].map(stop_idx)
    bj = [rds_idx[(r, d, s)] for r, d, s in zip(hw["route_id"], hw["direction_id"],
                                                hw["stop_id"])]
    add_edges(bi.tolist(), bj, hw["wait_min"].tolist())
    # alight: route-dir-stop -> stop
    add_edges(list(rds_idx.values()),
              [stop_idx[s] for s in rds["stop_id"]],
              [ALIGHT_MIN] * n_rds)
    # ride
    ri = [rds_idx[(r, d, s)] for r, d, s in zip(edges_ride["route_id"],
                                                edges_ride["direction_id"],
                                                edges_ride["stop_id"])]
    rj = [rds_idx[(r, d, s)] for r, d, s in zip(edges_ride["route_id"],
                                                edges_ride["direction_id"],
                                                edges_ride["stop_b"])]
    add_edges(ri, rj, edges_ride["ride_min"].tolist())

    # transfers: stop -> stop within 200 m
    sxy = to3414(stops["stop_lon"], stops["stop_lat"])
    stree = cKDTree(sxy)
    pairs = stree.query_pairs(TRANSFER_M, output_type="ndarray")
    tmin = np.linalg.norm(sxy[pairs[:, 0]] - sxy[pairs[:, 1]], axis=1) * DETOUR / WALK_MPM
    add_edges(pairs[:, 0].tolist(), pairs[:, 1].tolist(), tmin.tolist())
    add_edges(pairs[:, 1].tolist(), pairs[:, 0].tolist(), tmin.tolist())

    # access: origin -> stops within 600 m
    o_xy = to3414(h8["o_lng"], h8["o_lat"])
    acc = stree.query_ball_point(o_xy, ACCESS_M)
    n_acc = 0
    for i, lst in enumerate(acc):
        if lst:
            d = np.linalg.norm(sxy[lst] - o_xy[i], axis=1) * DETOUR / WALK_MPM
            add_edges([o_base + i] * len(lst), lst, d.tolist())
            n_acc += len(lst)
    print(f"  edges: {len(wts):,} (access {n_acc:,}, transfers {2*len(pairs):,})")

    g = coo_matrix((wts, (rows, cols)), shape=(n_nodes, n_nodes)).tocsr()

    # ---- one dijkstra pass for all origins ----------------------------------
    print("Dijkstra (directed, 50-min cap)...")
    t_stop = np.full((n_origin, n_stop), np.inf, dtype=np.float32)
    for lo in range(0, n_origin, 200):
        hi = min(lo + 200, n_origin)
        d = dijkstra(g, indices=np.arange(o_base + lo, o_base + hi),
                     limit=CAP_MIN, directed=True)
        t_stop[lo:hi] = d[:, :n_stop]
        del d

    # ---- egress min-plus onto hex9 ------------------------------------------
    h9 = pd.read_parquet(ROOT / "hex/hex9_population.parquet")
    h9 = h9.merge(pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
                  [["hex9_id", "lat", "lng"]], on="hex9_id")
    h9_xy = to3414(h9["lng"], h9["lat"])
    h9_pop = h9["pop_resident"].fillna(0).to_numpy(np.float64)
    h9_places = pd.read_parquet(ROOT / "hex/hex9_all_features.parquet",
                                columns=["hex9_id", "pc_total"]) \
        .set_index("hex9_id")["pc_total"].reindex(h9["hex9_id"]).fillna(0).to_numpy()

    h9tree = cKDTree(h9_xy)
    eg = h9tree.query_ball_point(sxy, EGRESS_M)
    eg_s, eg_h, eg_w = [], [], []
    for si, lst in enumerate(eg):
        if lst:
            d = np.linalg.norm(h9_xy[lst] - sxy[si], axis=1) * DETOUR / WALK_MPM
            eg_s.extend([si] * len(lst)); eg_h.extend(lst); eg_w.extend(d.tolist())
    eg_s = np.array(eg_s); eg_h = np.array(eg_h); eg_w = np.array(eg_w, np.float32)

    t_h9 = np.full((n_origin, len(h9)), np.inf, dtype=np.float32)
    for i in range(n_origin):
        cand = t_stop[i, eg_s] + eg_w
        np.minimum.at(t_h9[i], eg_h, cand)
    # pure-walk arm
    for i in range(n_origin):
        dw = np.linalg.norm(h9_xy - o_xy[i], axis=1) * DETOUR / WALK_MPM
        t_h9[i] = np.minimum(t_h9[i], dw)
    t_h9 = np.minimum(t_h9, CAP_MIN + 1)

    np.savez_compressed(ROOT / "hex/hex8_hex9_transit_min.npz",
                        minutes=t_h9, hex8_id=h8["hex8_id"].to_numpy(),
                        hex9_id=h9["hex9_id"].to_numpy())

    m15 = t_h9 <= T15
    out = pd.DataFrame({
        "hex8_id": h8["hex8_id"],
        "iso_transit15_pop": (m15 @ h9_pop).round(1),
        "iso_transit15_places": (m15 @ h9_places).round(1),
        "iso_transit15_hex9_n": m15.sum(1),
        "iso_transit15_stops_used": (t_stop <= T15).sum(1),
    })
    out.to_parquet(ROOT / "hex/hex8_iso_transit.parquet", index=False)

    rep = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "spec": "SITE_SELECTION_METRICS.md S2b (transit)",
        "params": {"walk_mpm": WALK_MPM, "detour": DETOUR, "access_m": ACCESS_M,
                   "egress_m": EGRESS_M, "transfer_m": TRANSFER_M,
                   "max_wait_min": MAX_WAIT_MIN, "cap_min": CAP_MIN},
        "ride_edges": int(len(edges_ride)),
        "route_dir_stops": int(n_rds),
        "median_t15_pop": float(out["iso_transit15_pop"].median()),
        "wall_clock_s": round(time.time() - t0, 2),
    }
    json.dump(rep, open(ROOT / "hex/iso_transit_report.json", "w"), indent=2)
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()
