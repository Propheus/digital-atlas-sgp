"""
Plexis SGP v4 — Stage 11: composite indices per scale.

Single-number rollups built from already-computed feature columns.
Each composite is a 0..1 normalized score.

  vibrancy_index           — places + magnets + transit + night lights
  livability_index         — walkability + green + amenities + transit + low traffic
  commercial_intensity     — office/retail mix + nl_commercial_indicator + density
  family_index             — schools + preschools + parks + healthcare + walkability
  density_pressure         — population + buildings + small road space
  accessibility_composite  — transit + walk + roads + amenities

All inputs are min-max normalized to [0, 1] before averaging into the index.

Outputs:
  hex/hex9_composites.parquet
  hex/hex8_composites.parquet
  hex/subzone_composites.parquet
"""
import json, time
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent


def minmax(s):
    s = pd.Series(s, dtype=float).fillna(0)
    lo, hi = s.quantile(0.01), s.quantile(0.99)
    if hi <= lo: return pd.Series(np.zeros(len(s)))
    return ((s - lo) / (hi - lo)).clip(0, 1)


def inv_dist_score(s, half=400):
    """Distance to score: short distance = 1, long distance = 0."""
    s = pd.Series(s, dtype=float).fillna(9999)
    return np.exp(-s / half).clip(0, 1)


def composite(df):
    """Compute the 6 composites from a dataframe with all_features cols."""
    cols = df.columns
    out = pd.DataFrame(index=df.index)

    def has(*names): return [n for n in names if n in cols]

    # 1. vibrancy
    parts = []
    for c in has("pc_total","pc_magnets","pc_total_reviews","nl_2024"):
        parts.append(minmax(df[c]))
    if "transit_score" in cols: parts.append(df["transit_score"].fillna(0).clip(0, 1))
    out["vibrancy_index"] = pd.concat(parts, axis=1).mean(axis=1).round(3) if parts else 0

    # 2. livability
    parts = []
    if "walkability_score" in cols: parts.append(df["walkability_score"].fillna(0).clip(0, 1))
    if "transit_score" in cols:     parts.append(df["transit_score"].fillna(0).clip(0, 1))
    if "lu_park_share" in cols:     parts.append(df["lu_park_share"].fillna(0))
    for c in has("preschools_within_400m","chas_clinics_within_500m","walk_food_400m"):
        parts.append(minmax(df[c]))
    if "expressway_severance" in cols:  # negative impact: subtract
        parts.append(1 - minmax(df["expressway_severance"]))
    out["livability_index"] = pd.concat(parts, axis=1).mean(axis=1).round(3) if parts else 0

    # 3. commercial intensity
    parts = []
    for c in has("pc_cat_business_office","pc_cat_shopping_retail","pc_cat_services","pc_cat_restaurant","pc_cat_cafe_coffee"):
        parts.append(minmax(df[c]))
    if "nl_commercial_indicator" in cols: parts.append(minmax(df["nl_commercial_indicator"]))
    if "lu_commercial_share" in cols:     parts.append(df["lu_commercial_share"].fillna(0))
    out["commercial_intensity"] = pd.concat(parts, axis=1).mean(axis=1).round(3) if parts else 0

    # 4. family index
    parts = []
    for c in has("primary_schools_within_1km","preschools_within_400m","chas_clinics_within_500m"):
        parts.append(minmax(df[c]))
    if "lu_park_share" in cols:        parts.append(df["lu_park_share"].fillna(0))
    if "walkability_score" in cols:    parts.append(df["walkability_score"].fillna(0).clip(0, 1))
    if "in_silver_zone" in cols:       parts.append(df["in_silver_zone"].fillna(0))
    out["family_index"] = pd.concat(parts, axis=1).mean(axis=1).round(3) if parts else 0

    # 5. density pressure
    parts = []
    for c in has("pop_resident","pop_nonresident","bld_total_count","bld_footprint_share"):
        parts.append(minmax(df[c]))
    if "lu_residential_share" in cols: parts.append(df["lu_residential_share"].fillna(0))
    out["density_pressure"] = pd.concat(parts, axis=1).mean(axis=1).round(3) if parts else 0

    # 6. accessibility composite
    parts = []
    if "transit_score" in cols:        parts.append(df["transit_score"].fillna(0).clip(0, 1))
    if "walkability_score" in cols:    parts.append(df["walkability_score"].fillna(0).clip(0, 1))
    if "near_mrt_400m" in cols:        parts.append(df["near_mrt_400m"].astype("float64").fillna(0).clip(0, 1))
    if "near_bus_300m" in cols:        parts.append(df["near_bus_300m"].astype("float64").fillna(0).clip(0, 1))
    if "primary_school_zone_count" in cols: parts.append(minmax(df["primary_school_zone_count"]))
    out["accessibility_composite"] = pd.concat(parts, axis=1).mean(axis=1).round(3) if parts else 0

    return out


def main():
    t0 = time.time()
    for scale, key in [("hex9","hex9_id"), ("hex8","hex8_id"), ("subzone","subzone_c")]:
        print(f"\n--- {scale.upper()} ---")
        df = pd.read_parquet(ROOT / f"hex/{scale}_all_features.parquet")
        comps = composite(df)
        out = pd.concat([df[[key]], comps], axis=1)
        out.to_parquet(ROOT / f"hex/{scale}_composites.parquet", index=False)
        print(f"  {scale}_composites: {out.shape}")
        for c in comps.columns:
            print(f"    {c:<25}  median={comps[c].median():.3f}  p90={comps[c].quantile(0.90):.3f}")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "indices": ["vibrancy_index","livability_index","commercial_intensity",
                    "family_index","density_pressure","accessibility_composite"],
    }
    with open(ROOT / "hex/composites_report.json", "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
