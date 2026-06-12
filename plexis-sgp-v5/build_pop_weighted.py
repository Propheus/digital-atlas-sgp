"""
Plexis SGP v4 — Stage 21: population-weighted spatial features.

For each hex9, compute pop-weighted means over its k=1 and k=2 ring neighbors:
  pw_<feature> = Σ neighbor_pop · neighbor_F / Σ neighbor_pop

Useful for "what does the typical resident in this neighborhood see"
rather than uniform mean of constituent hexes.

Also computes max-of-ring (`max_<feature>`) — peak local exposure.

Recovers the v3 `tr_pw_*` / `tr_max_*` / `sp_pw_*` / `sp_max_*` families.

Outputs:
  hex/hex9_pop_weighted.parquet
  hex/hex8_pop_weighted.parquet
"""
import json, time
from pathlib import Path
import numpy as np
import pandas as pd
import h3

ROOT = Path(__file__).parent

# Features to pop-weight + max over rings
FEATURES = [
    "lu_residential_share","lu_commercial_share","lu_industrial_share",
    "lu_park_share","lu_mixed_share",
    "pc_total","pc_magnets","pc_unique_brands",
    "pc_cat_business_office","pc_cat_shopping_retail","pc_cat_hawker",
    "pc_cat_residential","pc_cat_industrial_mfg","pc_cat_cafe_coffee",
    "pc_cat_restaurant","pc_cat_education","pc_cat_health_medical",
    "transit_score","walkability_score",
    "nl_2024","nl_commercial_indicator",
    "hdb_resale_4r_median_psm",
    "primary_schools_within_1km","preschools_within_400m","chas_clinic_count",
    "hawker_centre_count","tourist_attraction_count",
    "vibrancy_index","commercial_intensity","family_index","density_pressure",
    "pull_cbd","pull_mall","pull_mrt_interchange",
    "wc_built_share","wc_tree_share",
]


def pw_aggregates(df, key_col, pop_col, target_features, k):
    keys = df[key_col].values
    key_to_idx = {kk: i for i, kk in enumerate(keys)}
    pop_arr = df[pop_col].fillna(0).values.astype(float)

    # Only keep features that exist
    feats = [f for f in target_features if f in df.columns]
    feat_arrs = {f: df[f].fillna(0).values.astype(float) for f in feats}

    n = len(df)
    pw_data = {f"pw{k}_{f}": np.zeros(n) for f in feats}
    mx_data = {f"max{k}_{f}": np.zeros(n) for f in feats}

    for i, cell in enumerate(keys):
        try:
            ring = h3.grid_ring(cell, k)
        except Exception:
            continue
        valid_idx = [key_to_idx[c] for c in ring if c in key_to_idx]
        if not valid_idx:
            continue
        nbr_pop = pop_arr[valid_idx]
        sum_pop = nbr_pop.sum() or 1.0
        for f in feats:
            vals = feat_arrs[f][valid_idx]
            pw_data[f"pw{k}_{f}"][i] = (vals * nbr_pop).sum() / sum_pop
            mx_data[f"max{k}_{f}"][i] = vals.max()

    out = df[[key_col]].copy()
    for d in (pw_data, mx_data):
        for kk, vv in d.items():
            out[kk] = np.round(vv, 3)
    return out


def main():
    t0 = time.time()
    print("Loading hex9_all_features...")
    h9 = pd.read_parquet(ROOT / "hex/hex9_all_features.parquet")
    feats = [f for f in FEATURES if f in h9.columns]
    print(f"  features available: {len(feats)}/{len(FEATURES)}")

    print("Computing pop-weighted ring1 + ring2 for hex9...")
    h9_r1 = pw_aggregates(h9, "hex9_id", "pop_resident", FEATURES, k=1)
    h9_r2 = pw_aggregates(h9, "hex9_id", "pop_resident", FEATURES, k=2)
    h9_out = h9_r1.merge(h9_r2, on="hex9_id", how="left")
    h9_out.to_parquet(ROOT / "hex/hex9_pop_weighted.parquet", index=False)
    print(f"  hex9_pop_weighted: {h9_out.shape}")

    print("\nComputing pop-weighted ring1 + ring2 for hex8...")
    h8 = pd.read_parquet(ROOT / "hex/hex8_all_features.parquet")
    h8_r1 = pw_aggregates(h8, "hex8_id", "pop_resident", FEATURES, k=1)
    h8_r2 = pw_aggregates(h8, "hex8_id", "pop_resident", FEATURES, k=2)
    h8_out = h8_r1.merge(h8_r2, on="hex8_id", how="left")
    h8_out.to_parquet(ROOT / "hex/hex8_pop_weighted.parquet", index=False)
    print(f"  hex8_pop_weighted: {h8_out.shape}")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "features_used": feats,
        "shapes": {"hex9": list(h9_out.shape), "hex8": list(h8_out.shape)},
    }
    with open(ROOT / "hex/pop_weighted_report.json", "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
