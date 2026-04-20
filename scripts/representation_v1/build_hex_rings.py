"""
Representation v1 — hex k-ring neighbor features (spatial influence).

For each hex, compute k=1 (6 neighbors) and k=2 (18 additional neighbors) aggregates
of a chosen "influence basis" of features drawn from the already-built base table.
This is how we capture *how each hex influences other hexes*.

Aggregates per feature × per ring:
    nbr1_mean_{f}         mean over k=1 ring (excluding self)
    nbr1_max_{f}          max over k=1 ring
    nbr2_mean_{f}         mean over k=2 ring (excluding self)
    contrast_{f}          self_value - nbr1_mean_{f}   (+ = self is higher than neighbors)
    rank_{f}              percentile rank of self within (self + k=1 ring) ∈ [0,1]

Input:
    model/representation_v1/hex_base_merged.parquet
        (= V9 survivors + place composition + micrograph aggregates, built inline below)

Output:
    model/representation_v1/hex_rings.parquet   (5,897 × N ring features)

Note on hex universe:
    Neighbors of an edge hex can fall outside the 5,897-hex V9 universe. We treat those
    as missing (excluded from the mean/max/rank, not imputed as 0), which is the honest
    behavior: we simply don't have features for them.
"""
from __future__ import annotations

from pathlib import Path

import h3
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HEX_PATH = ROOT / "data" / "hex_v9" / "hex_features_v2.parquet"
PC_PATH = ROOT / "model" / "representation_v1" / "hex_place_composition.parquet"
MG_PATH = ROOT / "model" / "representation_v1" / "hex_micrograph.parquet"
OUT_MERGED = ROOT / "model" / "representation_v1" / "hex_base_merged.parquet"
OUT_RINGS = ROOT / "model" / "representation_v1" / "hex_rings.parquet"

# Columns from V9 we drop (leakage — gap scores from upstream models)
DROP_V9 = ["transit_gap_score", "elderly_transit_stress", "clinic_gap_score", "school_gap_score"]

# The "influence basis" — features used to compute ring aggregates.
# Keep this small and high-signal (every additional feature triples the ring column count).
INFLUENCE_BASIS = [
    # demographics / market size
    "population", "elderly_count", "children_count", "walking_dependent_count",
    # building stock
    "bldg_count", "hdb_blocks", "bldg_footprint_sqm",
    # transit supply
    "mrt_stations", "bus_stops",
    # commercial density (from place composition)
    "pc_total",
    "pc_cat_restaurant", "pc_cat_cafe_coffee", "pc_cat_shopping_retail",
    "pc_cat_hawker_street_food", "pc_cat_health_medical", "pc_cat_education",
    "pc_cat_office_workspace", "pc_cat_bar_nightlife",
    # composition signals
    "pc_unique_brands", "pc_cat_entropy",
    # persona affluence / family
    "p_affluence_idx", "p_family_idx", "p_youth_idx",
    # micrograph spatial context
    "mg_mean_transit", "mg_mean_competitor", "mg_mean_complementary", "mg_mean_demand",
    "mg_mean_anchor_count",
]


def build_base_merged() -> pd.DataFrame:
    print("Loading V9 hex table...")
    v9 = pd.read_parquet(HEX_PATH).drop(columns=DROP_V9)
    print(f"  V9 shape after drop: {v9.shape}")

    pc = pd.read_parquet(PC_PATH)
    mg = pd.read_parquet(MG_PATH)
    print(f"  place comp: {pc.shape}   micrograph: {mg.shape}")

    merged = v9.merge(pc, on="hex_id", how="left").merge(mg, on="hex_id", how="left")
    assert len(merged) == len(v9), "row count changed during merge"
    print(f"  merged base: {merged.shape}")
    OUT_MERGED.parent.mkdir(parents=True, exist_ok=True)
    merged.to_parquet(OUT_MERGED, index=False)
    print(f"  wrote {OUT_MERGED}")
    return merged


def compute_rings(base: pd.DataFrame) -> pd.DataFrame:
    # index hex_id -> row index for O(1) lookup
    hex_ids = base["hex_id"].tolist()
    id_to_idx = {h: i for i, h in enumerate(hex_ids)}

    # feature matrix of the influence basis — must be float, NaNs preserved
    missing = [c for c in INFLUENCE_BASIS if c not in base.columns]
    if missing:
        raise KeyError(f"Influence basis columns missing from base: {missing}")
    X = base[INFLUENCE_BASIS].astype("float64").to_numpy()
    n, f = X.shape
    print(f"Ring aggregation over {n} hexes × {f} influence features")

    # output arrays
    nbr1_mean = np.full((n, f), np.nan)
    nbr1_max = np.full((n, f), np.nan)
    nbr2_mean = np.full((n, f), np.nan)
    rank = np.full((n, f), np.nan)

    # iterate hexes — n=5897, f=28 — light enough for a Python loop
    for i, hid in enumerate(hex_ids):
        # k=1 neighbors (grid_disk with k=1 returns self + 6)
        disk1 = h3.grid_disk(hid, 1)
        idx1 = [id_to_idx[h] for h in disk1 if h in id_to_idx and h != hid]
        if idx1:
            slab1 = X[idx1]
            # nanmean / nanmax across neighbors
            with np.errstate(all="ignore"):
                nbr1_mean[i] = np.nanmean(slab1, axis=0)
                nbr1_max[i] = np.nanmax(slab1, axis=0)
            # rank of self within (self + neighbors) per feature
            combined = np.vstack([X[i : i + 1], slab1])
            for j in range(f):
                col = combined[:, j]
                valid = ~np.isnan(col)
                if valid.sum() <= 1 or np.isnan(col[0]):
                    continue
                vc = col[valid]
                # fraction strictly less than self / (n-1)  — ties handled by midrank
                self_val = col[0]
                lt = np.sum(vc < self_val)
                eq = np.sum(vc == self_val)
                total = len(vc)
                if total > 1:
                    rank[i, j] = (lt + 0.5 * (eq - 1)) / (total - 1)

        # k=2 neighbors (grid_disk with k=2 = self + 18)
        disk2 = h3.grid_disk(hid, 2)
        idx2 = [id_to_idx[h] for h in disk2 if h in id_to_idx and h != hid]
        if idx2:
            slab2 = X[idx2]
            with np.errstate(all="ignore"):
                nbr2_mean[i] = np.nanmean(slab2, axis=0)

    # self - nbr1_mean
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
    base = build_base_merged()
    rings = compute_rings(base)
    rings.to_parquet(OUT_RINGS, index=False)
    print(f"Wrote {OUT_RINGS}")

    # sanity: for a random dense hex, show self vs nbr1_mean
    dense = base.sort_values("pc_total", ascending=False).head(1)
    hid = dense["hex_id"].iloc[0]
    print()
    print(f"Sanity — hex {hid}:")
    self_row = base[base["hex_id"] == hid][INFLUENCE_BASIS[:6]].iloc[0]
    ring_row = rings[rings["hex_id"] == hid][[f"nbr1_mean_{c}" for c in INFLUENCE_BASIS[:6]]].iloc[0]
    print(pd.concat([self_row.rename("self"), ring_row.rename("nbr1_mean").reset_index(drop=True).set_axis(INFLUENCE_BASIS[:6])], axis=1))


if __name__ == "__main__":
    main()
