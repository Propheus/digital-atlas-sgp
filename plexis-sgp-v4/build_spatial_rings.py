"""
Plexis SGP v4 — Stage 10: spatial-ring context features per hex.

For each hex9, computes the 1-ring (6-neighbor) average of selected key
features. Same logic at hex8. Gives every cell awareness of its immediate
neighborhood without requiring downstream consumers to do the join.

Outputs:
  hex/hex9_spatial_rings.parquet   (~10 ring1_* cols)
  hex/hex8_spatial_rings.parquet
"""
import json, time
from pathlib import Path
import numpy as np
import pandas as pd
import h3

ROOT = Path(__file__).parent

# Features to compute ring-1 averages for (col_name, agg)
RING_FEATURES = {
    "pop_resident":              "mean",
    "pop_nonresident":           "mean",
    "bld_total_count":           "mean",
    "pc_total":                  "mean",
    "pc_magnets":                "mean",
    "walkability_score":         "mean",
    "transit_score":             "max",
    "nl_2024":                   "mean",
    "hdb_resale_4r_median_psm":  "mean",
    "school_count_total":        "sum",
}


def ring_aggregates(df, key_col, target_features, k):
    """For each cell, aggregate features over its ring-k neighbors (exact ring, not disk)."""
    keys = df[key_col].values
    key_set = set(keys)
    feat_arr = {f: df[f].fillna(0).values for f in target_features if f in df.columns}
    if not feat_arr:
        return df[[key_col]].copy()

    prefix = f"ring{k}_"
    out_data = {f"{prefix}{f}": np.zeros(len(df)) for f in feat_arr}
    key_to_idx = {kk: i for i, kk in enumerate(keys)}

    for i, cell in enumerate(keys):
        try:
            ring_cells = h3.grid_ring(cell, k)
        except Exception:
            continue
        valid_idx = [key_to_idx[c] for c in ring_cells if c in key_set]
        if not valid_idx:
            continue
        for f in feat_arr:
            vals = feat_arr[f][valid_idx]
            agg = RING_FEATURES[f]
            if agg == "mean":   out_data[f"{prefix}{f}"][i] = vals.mean()
            elif agg == "max":  out_data[f"{prefix}{f}"][i] = vals.max()
            elif agg == "sum":  out_data[f"{prefix}{f}"][i] = vals.sum()
            else:               out_data[f"{prefix}{f}"][i] = vals.mean()

    out = df[[key_col]].copy()
    for k_, v_ in out_data.items():
        out[k_] = np.round(v_, 3)
    return out


def main():
    t0 = time.time()
    # Load all_features bundles (need every input feature in one place)
    print("Loading hex9_all_features...")
    h9 = pd.read_parquet(ROOT / "hex/hex9_all_features.parquet")
    target = [f for f in RING_FEATURES if f in h9.columns]
    print(f"  ring features available: {target}")

    print("Computing hex9 ring-1 + ring-2 aggregates...")
    h9_r1 = ring_aggregates(h9, "hex9_id", target, k=1)
    h9_r2 = ring_aggregates(h9, "hex9_id", target, k=2)
    h9_out = h9_r1.merge(h9_r2, on="hex9_id", how="left")
    h9_out.to_parquet(ROOT / "hex/hex9_spatial_rings.parquet", index=False)
    print(f"  hex9_spatial_rings: {h9_out.shape}")

    print("\nLoading hex8_all_features...")
    h8 = pd.read_parquet(ROOT / "hex/hex8_all_features.parquet")
    print("Computing hex8 ring-1 + ring-2 aggregates...")
    h8_r1 = ring_aggregates(h8, "hex8_id", target, k=1)
    h8_r2 = ring_aggregates(h8, "hex8_id", target, k=2)
    h8_out = h8_r1.merge(h8_r2, on="hex8_id", how="left")
    h8_out.to_parquet(ROOT / "hex/hex8_spatial_rings.parquet", index=False)
    print(f"  hex8_spatial_rings: {h8_out.shape}")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "ring1_features_computed": list(target),
        "shapes": {"hex9": list(h9_out.shape), "hex8": list(h8_out.shape)},
    }
    with open(ROOT / "hex/spatial_rings_report.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n{json.dumps(summary, indent=2)}")


if __name__ == "__main__":
    main()
