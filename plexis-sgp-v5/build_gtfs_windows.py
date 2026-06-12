"""
Plexis SGP v4 — Stage 23: multi-window GTFS headways + departures.

We already compute AM-peak headway. This adds the missing windows:
  midday   11:00-14:00
  pm peak  17:00-19:00
  night    22:00-04:00 (next day)

Plus daily totals: gtfs_daily_departures, gtfs_routes_served, gtfs_stops_with_service.

For each stop, count weekday departures in each window.
Headway (minutes) = window_minutes / max(departures, 1).
Aggregate to hex by stop coords (we already snap stops via build_transit.py).

Outputs:
  hex/hex9_gtfs_windows.parquet
  hex/hex8_gtfs_windows.parquet
  hex/subzone_gtfs_windows.parquet
"""
import json, os, time
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import h3

ROOT = Path(__file__).parent


def _resolve_data_root():
    if os.environ.get("PLEXIS_DATA_ROOT"):
        return Path(os.environ["PLEXIS_DATA_ROOT"])
    for c in [Path("/home/azureuser/digital-atlas-sgp/data"), ROOT.parent / "data"]:
        if c.exists(): return c
    raise FileNotFoundError("data root not found")


DATA = _resolve_data_root()
GTFS = DATA / "gtfs/singapore-gtfs"


def to_seconds(t):
    """Convert HH:MM:SS to seconds-since-midnight; tolerates 24:xx:xx."""
    h, m, s = t.split(":")
    return int(h) * 3600 + int(m) * 60 + int(s)


# Window definitions in seconds-since-midnight
WINDOWS = {
    "am":     (7*3600,  9*3600),    # 7-9
    "midday": (11*3600, 14*3600),   # 11-14
    "pm":     (17*3600, 19*3600),   # 17-19
    "night":  (22*3600, 28*3600),   # 22 → 04 next day
}
WINDOW_MINUTES = {k: (v[1] - v[0]) // 60 for k, v in WINDOWS.items()}


def main():
    t0 = time.time()
    print(f"Loading GTFS...")
    stops = pd.read_csv(GTFS / "stops.txt")
    trips = pd.read_csv(GTFS / "trips.txt")
    routes = pd.read_csv(GTFS / "routes.txt")
    cal = pd.read_csv(GTFS / "calendar.txt")

    # Find weekday service IDs
    wd_service = cal[(cal["monday"] == 1) & (cal["tuesday"] == 1) & (cal["wednesday"] == 1)
                      & (cal["thursday"] == 1) & (cal["friday"] == 1)]["service_id"].tolist()
    print(f"  weekday service ids: {len(wd_service)}")
    wd_trips = trips[trips["service_id"].isin(wd_service)].copy()
    print(f"  weekday trips: {len(wd_trips):,}")

    # Stream stop_times in chunks; keep only weekday trips
    print("  scanning stop_times.txt (8M+ rows in chunks)...")
    wd_trip_set = set(wd_trips["trip_id"].astype(str).values)

    # Pre-init counters: stop_id → window → count
    stop_window = {win: {} for win in WINDOWS}
    stop_total = {}
    stop_routes = {}  # stop_id → set of route_ids

    trip_to_route = dict(zip(wd_trips["trip_id"].astype(str), wd_trips["route_id"]))

    for chunk in pd.read_csv(GTFS / "stop_times.txt",
                              usecols=["trip_id","departure_time","stop_id"],
                              chunksize=2_000_000, dtype=str):
        chunk = chunk[chunk["trip_id"].isin(wd_trip_set)]
        if len(chunk) == 0: continue
        chunk["secs"] = chunk["departure_time"].apply(to_seconds)
        for _, r in chunk.iterrows():
            sid = r["stop_id"]
            sec = r["secs"]
            stop_total[sid] = stop_total.get(sid, 0) + 1
            for win, (lo, hi) in WINDOWS.items():
                if lo <= sec < hi:
                    stop_window[win][sid] = stop_window[win].get(sid, 0) + 1
                    break
            # routes served
            tid = r["trip_id"]
            rid = trip_to_route.get(tid)
            if rid:
                stop_routes.setdefault(sid, set()).add(rid)
    print(f"  unique stops with service: {len(stop_total):,}")

    # Build per-stop dataframe
    rows = []
    for sid in stop_total:
        row = {"stop_id": sid, "gtfs_daily_departures": stop_total[sid],
                "gtfs_routes_served": len(stop_routes.get(sid, []))}
        for win in WINDOWS:
            cnt = stop_window[win].get(sid, 0)
            row[f"gtfs_dep_{win}"] = cnt
            row[f"gtfs_headway_{win}_min"] = WINDOW_MINUTES[win] / max(cnt, 1)
        rows.append(row)
    stop_df = pd.DataFrame(rows)
    print(f"  stop_df: {stop_df.shape}")

    # Merge with stops to get coords (stop_id might be int in stops, str here)
    stops["stop_id"] = stops["stop_id"].astype(str)
    stop_df = stop_df.merge(stops[["stop_id","stop_lat","stop_lon"]], on="stop_id", how="left")
    stop_df = stop_df.dropna(subset=["stop_lat","stop_lon"])
    stop_df["hex9_id"] = [h3.latlng_to_cell(la, lo, 9) for la, lo in zip(stop_df["stop_lat"], stop_df["stop_lon"])]
    print(f"  snapped stops to hex9: {len(stop_df)} stops, {stop_df['hex9_id'].nunique()} unique hexes")

    # Aggregate per hex9
    headway_cols = [f"gtfs_headway_{w}_min" for w in WINDOWS]
    dep_cols = [f"gtfs_dep_{w}" for w in WINDOWS] + ["gtfs_daily_departures"]
    h9_agg = stop_df.groupby("hex9_id").agg(
        **{c: (c, "min") for c in headway_cols},   # min headway = best service
        **{c: (c, "sum") for c in dep_cols},
        gtfs_routes_served=("gtfs_routes_served", "sum"),
        gtfs_stops_with_service=("stop_id", "count"),
    ).reset_index()

    h9 = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
    out = h9[["hex9_id"]].merge(h9_agg, on="hex9_id", how="left")
    # Hexes with no stops: headway = 999 (sentinel = no service), counts = 0
    for c in headway_cols:
        out[c] = out[c].fillna(999.0).round(1)
    for c in dep_cols + ["gtfs_routes_served","gtfs_stops_with_service"]:
        out[c] = out[c].fillna(0).astype(int)

    out.to_parquet(ROOT / "hex/hex9_gtfs_windows.parquet", index=False)
    print(f"\n  hex9_gtfs_windows: {out.shape}")

    # Aggregate to hex8 + subzone
    h9wp = out.merge(h9[["hex9_id","parent_hex8","parent_subzone"]], on="hex9_id")

    h8_uni = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")[["hex8_id"]]
    h8_min = h9wp.groupby("parent_hex8")[headway_cols].min().reset_index().rename(columns={"parent_hex8":"hex8_id"})
    h8_sum = h9wp.groupby("parent_hex8")[dep_cols + ["gtfs_routes_served","gtfs_stops_with_service"]].sum().reset_index().rename(columns={"parent_hex8":"hex8_id"})
    h8_out = h8_uni.merge(h8_min, on="hex8_id", how="left").merge(h8_sum, on="hex8_id", how="left")
    for c in headway_cols: h8_out[c] = h8_out[c].fillna(999.0).round(1)
    for c in dep_cols + ["gtfs_routes_served","gtfs_stops_with_service"]: h8_out[c] = h8_out[c].fillna(0).astype(int)
    h8_out.to_parquet(ROOT / "hex/hex8_gtfs_windows.parquet", index=False)
    print(f"  hex8_gtfs_windows: {h8_out.shape}")

    sz_lu = pd.read_parquet(ROOT / "hex/subzone_land_use.parquet")[["subzone_c"]].drop_duplicates()
    sz_min = h9wp.groupby("parent_subzone")[headway_cols].min().reset_index().rename(columns={"parent_subzone":"subzone_c"})
    sz_sum = h9wp.groupby("parent_subzone")[dep_cols + ["gtfs_routes_served","gtfs_stops_with_service"]].sum().reset_index().rename(columns={"parent_subzone":"subzone_c"})
    sz_out = sz_lu.merge(sz_min, on="subzone_c", how="left").merge(sz_sum, on="subzone_c", how="left")
    for c in headway_cols: sz_out[c] = sz_out[c].fillna(999.0).round(1)
    for c in dep_cols + ["gtfs_routes_served","gtfs_stops_with_service"]: sz_out[c] = sz_out[c].fillna(0).astype(int)
    sz_out.to_parquet(ROOT / "hex/subzone_gtfs_windows.parquet", index=False)
    print(f"  subzone_gtfs_windows: {sz_out.shape}")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "input_stop_times_rows": "8M+",
        "stops_with_weekday_service": len(stop_total),
        "windows": {k: f"{v[0]//3600:02d}:00-{v[1]//3600:02d}:00" for k, v in WINDOWS.items()},
        "shapes": {"hex9": list(out.shape), "hex8": list(h8_out.shape), "subzone": list(sz_out.shape)},
    }
    with open(ROOT / "hex/gtfs_windows_report.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n{json.dumps(summary, indent=2)}")


if __name__ == "__main__":
    main()
