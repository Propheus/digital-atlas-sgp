"""
Hex v10 — buildings per hex, computed from the fused building table.

Source: data/buildings_overture/sgp_buildings_fused.parquet
    Columns: id, cx (lng), cy (lat), area_deg (polygon area in deg^2),
             class, fused_class, is_hdb, best_floors, best_height, osm_name
    377,331 rows.

For each building we take its centroid (cx, cy) and assign it to an H3-9 cell.
We convert `area_deg` to square meters using a constant suitable for Singapore:
    1 deg^2 ≈ (111_000 m)(111_000 m × cos(1.35°)) ≈ 1.231e10 m²
Footprint in sqm is area_deg × 1.231e10.

When best_floors is missing, we impute a default per class:
    hdb_residential     -> 12
    private_residential -> 6
    commercial          -> 4
    industrial          -> 2
    institutional       -> 3
    transport           -> 2
    religious           -> 2
    other               -> 2
    unclassified        -> 2

The critical output is `residential_floor_area` = footprint × floors for rows where
fused_class is a residential type. This is the dasymetric weight for population
and persona disaggregation in the next steps.

Output:
    data/hex_v10/hex_buildings.parquet

Schema (one row per hex present in hex_universe.parquet):
    hex_id
    bldg_count, hdb_blocks, bldg_footprint_sqm
    bldg_hdb_residential, bldg_private_residential, bldg_commercial, bldg_industrial,
    bldg_institutional, bldg_transport, bldg_religious, bldg_other, bldg_unclassified
    avg_floors, max_floors, avg_height, max_height
    residential_floor_area_sqm       (KEY — dasymetric weight)
    commercial_floor_area_sqm
    total_floor_area_sqm
"""
from __future__ import annotations

from pathlib import Path

import h3
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "data" / "buildings_overture" / "sgp_buildings_fused.parquet"
UNI = ROOT / "data" / "hex_v10" / "hex_universe.parquet"
OUT = ROOT / "data" / "hex_v10" / "hex_buildings.parquet"

H3_RES = 9
DEG2_TO_SQM = 1.231e10  # at Singapore latitude; constant — max ~1% error across island

DEFAULT_FLOORS = {
    "hdb_residential": 12,
    "private_residential": 6,
    "commercial": 4,
    "industrial": 2,
    "institutional": 3,
    "transport": 2,
    "religious": 2,
    "other": 2,
    "unclassified": 2,
}

RESIDENTIAL_CLASSES = {"hdb_residential", "private_residential"}
COMMERCIAL_CLASSES = {"commercial", "industrial", "institutional"}

BLDG_TYPES = [
    "hdb_residential", "private_residential", "commercial", "industrial",
    "institutional", "transport", "religious", "other", "unclassified",
]


def main() -> None:
    print(f"Loading buildings: {SRC}")
    bf = pd.read_parquet(SRC)
    print(f"  {len(bf):,} buildings")

    print("Computing H3-9 cell for each building centroid...")
    bf["hex_id"] = [
        h3.latlng_to_cell(y, x, H3_RES)
        for x, y in zip(bf["cx"].to_numpy(), bf["cy"].to_numpy())
    ]

    # Restrict to v10 universe
    uni = pd.read_parquet(UNI, columns=["hex_id"])
    uni_set = set(uni["hex_id"])
    inside = bf["hex_id"].isin(uni_set)
    print(f"  buildings inside v10 hex universe: {inside.sum():,} / {len(bf):,}")
    bf = bf[inside].reset_index(drop=True)

    # footprint in sqm
    bf["footprint_sqm"] = bf["area_deg"] * DEG2_TO_SQM

    # impute floors
    default_floors_arr = bf["fused_class"].map(DEFAULT_FLOORS).fillna(2).astype(float)
    bf["floors_eff"] = bf["best_floors"].astype("Float64").astype(float).fillna(default_floors_arr)

    # per-building floor area
    bf["floor_area_sqm"] = bf["footprint_sqm"] * bf["floors_eff"]

    # flag residential / commercial buildings
    bf["is_residential"] = bf["fused_class"].isin(RESIDENTIAL_CLASSES)
    bf["is_commercial_like"] = bf["fused_class"].isin(COMMERCIAL_CLASSES)

    # height (not always present)
    bf["height_eff"] = bf["best_height"].astype("Float64").astype(float)

    print("Aggregating per hex...")
    agg = bf.groupby("hex_id").agg(
        bldg_count=("id", "count"),
        bldg_footprint_sqm=("footprint_sqm", "sum"),
        avg_floors=("floors_eff", "mean"),
        max_floors=("floors_eff", "max"),
        avg_height=("height_eff", "mean"),
        max_height=("height_eff", "max"),
        total_floor_area_sqm=("floor_area_sqm", "sum"),
        residential_floor_area_sqm=("floor_area_sqm", lambda s: s[bf.loc[s.index, "is_residential"]].sum()),
        commercial_floor_area_sqm=("floor_area_sqm", lambda s: s[bf.loc[s.index, "is_commercial_like"]].sum()),
        hdb_blocks=("is_hdb", "sum"),
    )

    # class counts per hex: pivot
    class_counts = (
        bf.groupby(["hex_id", "fused_class"]).size().unstack(fill_value=0)
    )
    # ensure all expected columns exist
    for t in BLDG_TYPES:
        if t not in class_counts.columns:
            class_counts[t] = 0
    class_counts = class_counts[BLDG_TYPES].rename(columns={t: f"bldg_{t}" for t in BLDG_TYPES})

    out = agg.join(class_counts, how="left").reset_index()

    # left-join onto the universe so empty hexes get zero rows
    uni_full = pd.read_parquet(UNI)
    out = uni_full[["hex_id"]].merge(out, on="hex_id", how="left")

    # Fill numeric NaN with 0 except avg_floors / avg_height / max_* — which stay NaN for hexes with no buildings
    count_cols = ["bldg_count", "bldg_footprint_sqm", "total_floor_area_sqm",
                  "residential_floor_area_sqm", "commercial_floor_area_sqm",
                  "hdb_blocks"] + [f"bldg_{t}" for t in BLDG_TYPES]
    for c in count_cols:
        out[c] = out[c].fillna(0)

    print(f"Output shape: {out.shape}")
    print(f"Hexes with ≥1 building: {(out['bldg_count'] > 0).sum():,} / {len(out):,}")
    print(f"Hexes with residential floor area: {(out['residential_floor_area_sqm'] > 0).sum():,}")
    print()
    print("Residential floor area distribution (sqm):")
    ra = out["residential_floor_area_sqm"]
    ra_nz = ra[ra > 0]
    print(f"  nonzero: {len(ra_nz):,}  min={ra_nz.min():,.0f}  median={ra_nz.median():,.0f}  max={ra_nz.max():,.0f}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT, index=False)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
