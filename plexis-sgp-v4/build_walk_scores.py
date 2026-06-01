"""
Plexis SGP v4 — Stage 18: per-amenity walk scores.

Converts existing walking-distance columns into [0,1] scores via exp(-d/L).
Recovers the v3 `walk_*_score` family as derived columns from existing data.

Score = exp(-d / L)  where L = 400m by default (= 1/e at 400m, half-life ~277m).
Higher score = closer.

Inputs (from existing layers, no new data):
  hex/hex9_walkability.parquet  (dist_walk_<amenity>_m)
  hex/hex9_transit_clean.parquet (dist_mrt_m, dist_bus_m)
  places/sgp_places_micrograph.parquet → not used here (already aggregated)

Output cols (per scale): 9 walk_*_score
  walk_mrt_score, walk_bus_score, walk_school_score, walk_clinic_score,
  walk_hawker_score, walk_supermarket_score, walk_park_score,
  walk_food_score, walk_convenience_score

Outputs:
  hex/hex9_walk_scores.parquet
  hex/hex8_walk_scores.parquet
  hex/subzone_walk_scores.parquet
"""
import json, time
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
L = 400.0  # decay scale

MAPPING = {
    "walk_mrt_score":          ("transit",     "dist_mrt_m"),
    "walk_bus_score":          ("transit",     "dist_bus_m"),
    "walk_school_score":       ("walkability", "dist_walk_school_m"),
    "walk_clinic_score":       ("walkability", "dist_walk_clinic_m"),
    "walk_hawker_score":       ("walkability", "dist_walk_hawker_m"),
    "walk_supermarket_score":  ("walkability", "dist_walk_supermarket_m"),
    "walk_park_score":         ("walkability", "dist_walk_park_m"),
    "walk_food_score":         ("walkability", "dist_walk_food_m"),
    "walk_convenience_score":  ("walkability", "dist_walk_convenience_m"),
}


def compute_for_scale(scale, key):
    wk = pd.read_parquet(ROOT / f"hex/{scale}_walkability.parquet")
    tr = pd.read_parquet(ROOT / f"hex/{scale}_transit_clean.parquet")

    out = wk[[key]].copy()
    for score_col, (src, dist_col) in MAPPING.items():
        df = tr if src == "transit" else wk
        if dist_col in df.columns:
            d = df.set_index(key)[dist_col].fillna(9999.0)
            score = np.exp(-d / L)
            out[score_col] = out[key].map(d.index.to_series().map(score)).fillna(0).round(3)
        else:
            out[score_col] = 0.0
    out["walk_score_avg"] = out[[c for c in out.columns if c.endswith("_score")]].mean(axis=1).round(3)
    return out


def main():
    t0 = time.time()
    for scale, key in [("hex9","hex9_id"),("hex8","hex8_id"),("subzone","subzone_c")]:
        print(f"\n--- {scale.upper()} ---")
        try:
            out = compute_for_scale(scale, key)
            out.to_parquet(ROOT / f"hex/{scale}_walk_scores.parquet", index=False)
            print(f"  {scale}_walk_scores: {out.shape}")
            for c in out.columns:
                if c == key: continue
                print(f"    {c:<26}  median={out[c].median():.3f}  p90={out[c].quantile(0.9):.3f}")
        except Exception as e:
            print(f"  skipped {scale}: {e}")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "decay_L_m": L,
        "score_cols": list(MAPPING.keys()) + ["walk_score_avg"],
    }
    with open(ROOT / "hex/walk_scores_report.json", "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
