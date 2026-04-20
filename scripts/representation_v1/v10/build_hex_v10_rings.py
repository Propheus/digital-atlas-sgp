"""
Hex v10 — k-ring neighbor features (spatial influence).

Same logic as representation_v1/build_hex_rings.py but:
    - Reads from v10 base (hex_features_v10_base.parquet) instead of the merged v1 base
    - Joins place composition + micrograph from their v10 locations under data/hex_v10/
    - Influence basis updated: no persona columns (dropped at hex level), no v9_rings
      columns (which would double-count the ring features we're computing)
    - Writes to data/hex_v10/hex_rings.parquet

Rings computed per influence feature:
    nbr1_mean_{f}    mean over k=1 ring (6 neighbors, excluding self)
    nbr1_max_{f}     max over k=1 ring
    nbr2_mean_{f}    mean over k=2 ring (18 neighbors, excluding self)
    contrast_{f}     self_value - nbr1_mean_{f}
    rank_{f}         percentile rank of self within (self + k=1 ring) ∈ [0,1]

Neighbors whose hex_id is not in the v10 universe are excluded (not imputed).
"""
from __future__ import annotations

from pathlib import Path

import h3
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
V10 = ROOT / "data" / "hex_v10"
BASE_PATH = V10 / "hex_features_v10_base.parquet"
PC_PATH = V10 / "hex_place_composition.parquet"
MG_PATH = V10 / "hex_micrograph.parquet"
OUT_MERGED = V10 / "hex_features_v10_merged.parquet"
OUT_RINGS = V10 / "hex_rings.parquet"

INFLUENCE_BASIS = [
    # market size (from dasymetric population)
    "population", "elderly_count", "children_count", "walking_dependent_count",
    # building stock (from fused source)
    "bldg_count", "hdb_blocks", "bldg_footprint_sqm",
    "residential_floor_area_sqm",  # dasymetric weight — meaningful ring signal
    # transit supply
    "mrt_stations", "bus_stops",
    # commercial density (from place composition)
    "pc_total",
    "pc_cat_restaurant", "pc_cat_cafe_coffee", "pc_cat_shopping_retail",
    "pc_cat_hawker_street_food", "pc_cat_health_medical", "pc_cat_education",
    "pc_cat_office_workspace", "pc_cat_bar_nightlife",
    # composition signals
    "pc_unique_brands", "pc_cat_entropy",
    # land use signal
    "lu_residential_pct", "lu_commercial_pct", "lu_business_pct", "avg_gpr",
    # micrograph spatial context
    "mg_mean_transit", "mg_mean_competitor", "mg_mean_complementary", "mg_mean_demand",
    "mg_mean_anchor_count",
]


def build_merged_base() -> pd.DataFrame:
    print("Loading v10 base + composition + micrograph...")
    base = pd.read_parquet(BASE_PATH)
    pc = pd.read_parquet(PC_PATH)
    mg = pd.read_parquet(MG_PATH)
    print(f"  base: {base.shape}  composition: {pc.shape}  micrograph: {mg.shape}")

    merged = base.merge(pc, on="hex_id", how="left").merge(mg, on="hex_id", how="left")
    assert len(merged) == len(base), "row count changed during merge"
    print(f"  merged: {merged.shape}")
    OUT_MERGED.parent.mkdir(parents=True, exist_ok=True)
    merged.to_parquet(OUT_MERGED, index=False)
    print(f"  wrote {OUT_MERGED}")
    return merged


def compute_rings(base: pd.DataFrame) -> pd.DataFrame:
    hex_ids = base["hex_id"].tolist()
    id_to_idx = {h: i for i, h in enumerate(hex_ids)}

    missing = [c for c in INFLUENCE_BASIS if c not in base.columns]
    if missing:
        raise KeyError(f"Influence basis columns missing from base: {missing}")
    X = base[INFLUENCE_BASIS].astype("float64").to_numpy()
    n, f = X.shape
    print(f"Ring aggregation over {n} hexes × {f} influence features")

    nbr1_mean = np.full((n, f), np.nan)
    nbr1_max = np.full((n, f), np.nan)
    nbr2_mean = np.full((n, f), np.nan)
    rank = np.full((n, f), np.nan)

    for i, hid in enumerate(hex_ids):
        disk1 = h3.grid_disk(hid, 1)
        idx1 = [id_to_idx[h] for h in disk1 if h in id_to_idx and h != hid]
        if idx1:
            slab1 = X[idx1]
            with np.errstate(all="ignore"):
                nbr1_mean[i] = np.nanmean(slab1, axis=0)
                nbr1_max[i] = np.nanmax(slab1, axis=0)
            combined = np.vstack([X[i : i + 1], slab1])
            for j in range(f):
                col = combined[:, j]
                valid = ~np.isnan(col)
                if valid.sum() <= 1 or np.isnan(col[0]):
                    continue
                vc = col[valid]
                self_val = col[0]
                lt = np.sum(vc < self_val)
                eq = np.sum(vc == self_val)
                total = len(vc)
                if total > 1:
                    rank[i, j] = (lt + 0.5 * (eq - 1)) / (total - 1)

        disk2 = h3.grid_disk(hid, 2)
        idx2 = [id_to_idx[h] for h in disk2 if h in id_to_idx and h != hid]
        if idx2:
            slab2 = X[idx2]
            with np.errstate(all="ignore"):
                nbr2_mean[i] = np.nanmean(slab2, axis=0)

    contrast = X - nbr1_mean

    def cols(prefix: str) -> list[str]:
        return [f"{prefix}{c}" for c in INFLUENCE_BASIS]

    out = pd.DataFrame(nbr1_mean, columns=cols("nbr1_mean_"))
    out = pd.concat(
        [
            pd.DataFrame({"hex_id": hex_ids}),
            out,
            pd.DataFrame(nbr1_max, columns=cols("nbr1_max_")),
            pd.DataFrame(nbr2_mean, columns=cols("nbr2_mean_")),
            pd.DataFrame(contrast, columns=cols("contrast_")),
            pd.DataFrame(rank, columns=cols("rank_")),
        ],
        axis=1,
    )
    print(f"Ring output shape: {out.shape}")
    return out


def main() -> None:
    base = build_merged_base()
    rings = compute_rings(base)
    rings.to_parquet(OUT_RINGS, index=False)
    print(f"Wrote {OUT_RINGS}")


if __name__ == "__main__":
    main()
