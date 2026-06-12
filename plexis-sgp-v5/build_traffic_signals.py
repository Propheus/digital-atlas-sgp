"""
Plexis SGP v4 — Stage 22: traffic-signal + pedestrian-crossing types per scale.

Source: data/transit/traffic_signals.geojson (44,922 LTA-tagged signals).

Recovers v3 `sig_*` / `ped_*` families. Buckets signals by type:
  sig_overhead       Overhead Signal (vehicular-priority intersections)
  sig_ground         Ground Signal (street-level intersections)
  sig_pedestrian     Pedestrian Signal (with/without countdown)
  sig_beacon         Beacon (warning-only)
  sig_rag            Red-Amber-Green for elderly (priority crossings)
  sig_filter_arrow   Green filter arrow
  sig_bicycle        Bicycle crossing signal
  sig_total          all signals
  ped_countdown      pedestrian signals with countdown timer (subset of sig_pedestrian)

Outputs:
  hex/hex9_traffic_signals.parquet
  hex/hex8_traffic_signals.parquet
  hex/subzone_traffic_signals.parquet
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
SIG_GJ = DATA / "transit/traffic_signals.geojson"

BUCKETS = {
    "sig_overhead":     ["Overhead Signal", "Ovelhead Signal Centre Median"],
    "sig_ground":       ["Ground Signal", "Ground Signal (with Green Man +)", "Miniature Ground Signal"],
    "sig_pedestrian":   ["Pedestrian Signal", "Pedestrian Signal with Intergrated Count Down Timer",
                         "Count Down Timer for Pedestrian"],
    "sig_beacon":       ["Beacon"],
    "sig_rag":          ["RAG"],
    "sig_filter_arrow": ["Green Filter Arrow Signal"],
    "sig_bicycle":      ["Bicycle Crossing Signal"],
}
PED_COUNTDOWN = ["Pedestrian Signal with Intergrated Count Down Timer", "Count Down Timer for Pedestrian"]


def main():
    t0 = time.time()
    print(f"Loading {SIG_GJ.name}...")
    g = gpd.read_file(SIG_GJ)
    print(f"  {len(g):,} signals (raw)")
    g = g[g.geometry.notna() & ~g.geometry.is_empty].copy()
    print(f"  {len(g):,} with valid geometry")

    # Snap each signal to hex9
    pts_4326 = g.to_crs(4326)
    g["hex9_id"] = [h3.latlng_to_cell(p.y, p.x, 9) for p in pts_4326.geometry]

    h9 = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
    out = h9[["hex9_id"]].copy()

    # Total
    cnt = g.groupby("hex9_id").size().rename_axis("hex9_id").reset_index(name="sig_total")
    out = out.merge(cnt, on="hex9_id", how="left")

    # Per-bucket
    for col, types in BUCKETS.items():
        sub = g[g["TYP_NAM"].isin(types)]
        cnt = sub.groupby("hex9_id").size().rename_axis("hex9_id").reset_index(name=col)
        out = out.merge(cnt, on="hex9_id", how="left")

    # Pedestrian countdown
    sub = g[g["TYP_NAM"].isin(PED_COUNTDOWN)]
    cnt = sub.groupby("hex9_id").size().rename_axis("hex9_id").reset_index(name="ped_countdown")
    out = out.merge(cnt, on="hex9_id", how="left")

    int_cols = [c for c in out.columns if c != "hex9_id"]
    for c in int_cols:
        out[c] = out[c].fillna(0).astype(int)

    out.to_parquet(ROOT / "hex/hex9_traffic_signals.parquet", index=False)
    print(f"  hex9_traffic_signals: {out.shape}")

    # Aggregate to hex8 + subzone (sum)
    h9wp = out.merge(h9[["hex9_id","parent_hex8","parent_subzone"]], on="hex9_id")
    sum_cols = [c for c in out.columns if c != "hex9_id"]

    h8_uni = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")[["hex8_id"]]
    h8_agg = h9wp.groupby("parent_hex8")[sum_cols].sum().reset_index().rename(columns={"parent_hex8":"hex8_id"})
    h8_out = h8_uni.merge(h8_agg, on="hex8_id", how="left")
    for c in sum_cols: h8_out[c] = h8_out[c].fillna(0).astype(int)
    h8_out.to_parquet(ROOT / "hex/hex8_traffic_signals.parquet", index=False)
    print(f"  hex8_traffic_signals: {h8_out.shape}")

    sz_lu = pd.read_parquet(ROOT / "hex/subzone_land_use.parquet")[["subzone_c"]].drop_duplicates()
    sz_agg = h9wp.groupby("parent_subzone")[sum_cols].sum().reset_index().rename(columns={"parent_subzone":"subzone_c"})
    sz_out = sz_lu.merge(sz_agg, on="subzone_c", how="left")
    for c in sum_cols: sz_out[c] = sz_out[c].fillna(0).astype(int)
    sz_out.to_parquet(ROOT / "hex/subzone_traffic_signals.parquet", index=False)
    print(f"  subzone_traffic_signals: {sz_out.shape}")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "input_signals": len(g),
        "by_bucket": {col: int(out[col].sum()) for col in sum_cols},
        "shapes": {"hex9": list(out.shape), "hex8": list(h8_out.shape), "subzone": list(sz_out.shape)},
    }
    with open(ROOT / "hex/traffic_signals_report.json", "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
