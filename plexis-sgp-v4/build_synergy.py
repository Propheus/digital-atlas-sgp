"""
Plexis SGP v4 — Stage 13: synergy interactions per scale.

Cross-products of meaningful feature pairs that capture *interaction* effects
(neither feature alone tells the whole story).

  syn_pop_x_walk            pop_resident × walkability_score
  syn_pop_x_transit         pop_resident × transit_score
  syn_office_x_transit      pc_cat_business_office × transit_score
  syn_retail_x_anchors      pc_cat_shopping_retail × pc_magnets
  syn_density_x_amenities   density_pressure × (chas+preschool+hawker counts)
  syn_far_x_transit         (bld_total_floors_est OR pop) × transit_score
  syn_residential_x_school  pc_cat_residential × primary_schools_within_1km
  syn_premium_school_x_4r   school_count_premium × hdb_resale_4r_median_psm

Each col is min-max normalized to [0, 1].

Outputs:
  hex/hex9_synergy.parquet
  hex/hex8_synergy.parquet
  hex/subzone_synergy.parquet
"""
import json, time
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent


def minmax01(s):
    s = pd.Series(s, dtype=float).fillna(0)
    lo, hi = s.quantile(0.01), s.quantile(0.99)
    if hi <= lo: return pd.Series(np.zeros(len(s)))
    return ((s - lo) / (hi - lo)).clip(0, 1)


def synergy(df):
    out = pd.DataFrame(index=df.index)
    cols = df.columns

    def has(c): return c in cols
    def col(c, default=0): return df[c].fillna(default) if has(c) else pd.Series(default, index=df.index)

    out["syn_pop_x_walk"]           = (minmax01(col("pop_resident")) * col("walkability_score").clip(0, 1)).round(3)
    out["syn_pop_x_transit"]        = (minmax01(col("pop_resident")) * col("transit_score").clip(0, 1)).round(3)
    out["syn_office_x_transit"]     = (minmax01(col("pc_cat_business_office")) * col("transit_score").clip(0, 1)).round(3)
    out["syn_retail_x_anchors"]     = (minmax01(col("pc_cat_shopping_retail")) * minmax01(col("pc_magnets"))).round(3)
    out["syn_density_x_amenities"]  = (minmax01(col("density_pressure"))
                                       * minmax01(col("chas_clinic_count") + col("preschool_count") + col("hawker_centre_count"))).round(3)
    out["syn_far_x_transit"]        = (minmax01(col("bld_footprint_share")) * col("transit_score").clip(0, 1)).round(3)
    out["syn_residential_x_school"] = (minmax01(col("pc_cat_residential")) * minmax01(col("primary_schools_within_1km"))).round(3)
    out["syn_premium_school_x_4r"]  = (minmax01(col("school_count_premium")) * minmax01(col("hdb_resale_4r_median_psm"))).round(3)
    return out


def main():
    t0 = time.time()
    for scale, key in [("hex9","hex9_id"),("hex8","hex8_id"),("subzone","subzone_c")]:
        print(f"\n--- {scale.upper()} ---")
        df = pd.read_parquet(ROOT / f"hex/{scale}_all_features.parquet")
        s = synergy(df)
        out = pd.concat([df[[key]], s], axis=1)
        out.to_parquet(ROOT / f"hex/{scale}_synergy.parquet", index=False)
        print(f"  {scale}_synergy: {out.shape}")
        for c in s.columns:
            print(f"    {c:<28}  median={s[c].median():.3f}  p90={s[c].quantile(0.90):.3f}")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "interactions": ["syn_pop_x_walk","syn_pop_x_transit","syn_office_x_transit",
                          "syn_retail_x_anchors","syn_density_x_amenities","syn_far_x_transit",
                          "syn_residential_x_school","syn_premium_school_x_4r"],
    }
    with open(ROOT / "hex/synergy_report.json", "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
