"""
Hex v10 — merge all v10 pillars into a single base feature table.

Joins:
    hex_universe.parquet        (7,318 × 8)
    hex_buildings.parquet       (7,318 × 20)  [recomputed from source]
    hex_population.parquet      (7,318 × 9)   [dasymetric, no ratios]
    hex_land_use.parquet        (7,318 × 13)  [proper area-weighted GPR]
    hex_amenities.parquet       (7,318 × 13)  [point counts from source]
    + copy-through of V9 columns that are NOT broadcast, recomputed, or gap scores

Not joined (intentional — see respective script docstrings):
    hex_personas.parquet        (PA-level broadcast, dropped at hex level)
    hex_hdb_prices.parquet      (no geocoding available, dropped at hex level)

Gap-score columns from V9 are dropped entirely (leakage).

Output:
    data/hex_v10/hex_features_v10_base.parquet

Intermediate (before place composition, micrograph, ring features are joined).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
V10 = ROOT / "data" / "hex_v10"
V9 = ROOT / "data" / "hex_v9" / "hex_features_v2.parquet"
OUT = V10 / "hex_features_v10_base.parquet"

# Columns to copy-through from V9 (not recomputed, not broadcast, not gap scores).
V9_COPY_THROUGH = [
    "amenity_types_nearby", "bicycle_signal",
    "bldg_ring1", "bus_daily_taps",
    "dist_bus_m", "dist_clinic_m", "dist_hawker_m", "dist_mrt_m", "dist_nearest_mrt_m",
    "dist_park_m", "dist_school_m", "dist_super_m",
    "hdb_ring1",
    "hex_avg_speed_kmh", "hex_flow_pct", "hex_flow_segments", "hex_jam_pct",
    "hex_jam_segments", "hex_seg_count",
    "mrt_daily_taps", "mrt_hex_rings", "mrt_ring2",
    "ped_countdown", "ped_crossings_total", "ped_elderly", "ped_standard",
    "pop_ring1", "pop_ring2",
    "road_cat_arterial", "road_cat_expressway", "road_cat_major_arterial",
    "road_cat_minor_arterial", "road_cat_slip", "road_cat_small",
    "sig_beacon", "sig_filter_arrow", "sig_ground", "sig_overhead", "sig_rag",
    "transit_daily_taps",
    "walk_bus_m", "walk_bus_score", "walk_clinic_m", "walk_clinic_score",
    "walk_hawker_m", "walk_hawker_score", "walk_mrt_m", "walk_mrt_score",
    "walk_park_m", "walk_park_score", "walk_school_m", "walk_super_m", "walk_super_score",
    "walkability_score", "walkability_score_v2",
]


def main() -> None:
    print("Loading v10 pillars...")
    uni = pd.read_parquet(V10 / "hex_universe.parquet")
    bldg = pd.read_parquet(V10 / "hex_buildings.parquet")
    pop = pd.read_parquet(V10 / "hex_population.parquet")
    lu = pd.read_parquet(V10 / "hex_land_use.parquet")
    amen = pd.read_parquet(V10 / "hex_amenities.parquet")
    print(f"  universe: {uni.shape}")
    print(f"  buildings: {bldg.shape}")
    print(f"  population: {pop.shape}")
    print(f"  land use: {lu.shape}")
    print(f"  amenities: {amen.shape}")

    # Start with the universe (identity columns)
    out = uni.copy()
    out = out.merge(bldg, on="hex_id", how="left")
    out = out.merge(pop, on="hex_id", how="left")
    out = out.merge(lu, on="hex_id", how="left")
    out = out.merge(amen, on="hex_id", how="left")
    print(f"After pillar merges: {out.shape}")

    # Copy-through from V9 for overlapping hexes
    print("Copying V9 survivors for overlapping hexes...")
    v9 = pd.read_parquet(V9, columns=["hex_id"] + V9_COPY_THROUGH)
    out = out.merge(v9, on="hex_id", how="left")
    print(f"After V9 copy-through: {out.shape}")

    # Count how many new (non-V9) hexes have NaN for copy-through cols (expected)
    v9_hexes = set(v9["hex_id"])
    new_hexes = set(out["hex_id"]) - v9_hexes
    print(f"  new hexes with NaN for V9-sourced cols: {len(new_hexes):,}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT, index=False)
    print(f"Wrote {OUT}")
    print()

    # Final audit — are any columns still fully subzone-broadcast?
    ID = {"hex_id","lat","lng","area_km2","parent_subzone","parent_subzone_name","parent_pa","parent_region"}
    feat_cols = [c for c in out.columns if c not in ID and out[c].dtype != object]
    broadcast = []
    for c in feat_cols:
        col_std = out[c].std(ddof=0)
        if not np.isfinite(col_std) or col_std < 1e-9:
            continue
        s = out.groupby("parent_subzone")[c].std(ddof=0)
        sizes = out.groupby("parent_subzone").size()
        s = s[sizes > 1]
        if len(s) == 0:
            continue
        max_within = s.max(skipna=True)
        if max_within is not None and max_within < 1e-9:
            broadcast.append(c)
    print(f"Remaining subzone-broadcast feature columns: {len(broadcast)}")
    for c in broadcast:
        print(f"  {c}")


if __name__ == "__main__":
    main()
