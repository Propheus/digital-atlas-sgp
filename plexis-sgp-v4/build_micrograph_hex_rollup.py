"""
Plexis SGP v4 — Stage 17: per-place micrograph → per-hex per-category rollup.

For each hex9 × category C, average the micrograph features of places in
category C that fall in that hex. This recovers the v3 `mg_*` family.

Per (hex, category) we keep three rollups:
  mg_<cat>_pressure_400m     mean pmg_competitors_400m  for category-C places in hex
  mg_<cat>_support_400m      mean pmg_complements_400m
  mg_<cat>_anchor_strength   mean pmg_anchor_strength_sum

Plus 3 hex-wide rollups across all categories:
  mg_avg_competitors_400m
  mg_avg_anchor_strength
  mg_avg_walk_dist_mrt_m

= 3 × 24 + 3 = 75 cols + key. Lean but recovers the analytical core of v3 mg.

Outputs:
  hex/hex9_micrograph_rollup.parquet
  hex/hex8_micrograph_rollup.parquet
  hex/subzone_micrograph_rollup.parquet
"""
import json, time
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent

CATEGORIES = [
    "bakery","bar_nightlife","beauty_personal","business_office","cafe_coffee",
    "convenience","education","entertainment_culture","fast_food","fitness_recreation",
    "government_public","hawker","health_medical","hotel_hospitality","industrial_mfg",
    "other_uncategorized","park_open","religious_worship","residential","restaurant",
    "services","shopping_retail","supermarket","transportation",
]


def per_cat_rollup(places_with_mg, key_col):
    """For each (key, category), compute mean of pmg_* features."""
    g = places_with_mg.groupby([key_col, "plexis_category"])
    agg = g.agg(
        pressure=("pmg_competitors_400m", "mean"),
        support=("pmg_complements_400m", "mean"),
        anchor_strength=("pmg_anchor_strength_sum", "mean"),
    ).reset_index()

    # Pivot wide: one column per (cat, metric)
    out = pd.DataFrame({key_col: places_with_mg[key_col].drop_duplicates().values})
    for metric, src in [("pressure_400m","pressure"),
                        ("support_400m","support"),
                        ("anchor_strength","anchor_strength")]:
        wide = agg.pivot(index=key_col, columns="plexis_category", values=src)
        wide = wide.reindex(columns=CATEGORIES, fill_value=0).reset_index()
        wide.columns = [key_col] + [f"mg_{c}_{metric}" for c in CATEGORIES]
        out = out.merge(wide, on=key_col, how="left")

    # Hex-wide rollups (across all places regardless of category)
    hex_wide = places_with_mg.groupby(key_col).agg(
        mg_avg_competitors_400m=("pmg_competitors_400m", "mean"),
        mg_avg_anchor_strength=("pmg_anchor_strength_sum", "mean"),
        mg_avg_walk_dist_mrt_m=("pmg_walk_dist_mrt_m", "mean"),
    ).reset_index()
    out = out.merge(hex_wide, on=key_col, how="left")
    return out


def main():
    t0 = time.time()
    print("Loading places + micrograph...")
    places = pd.read_parquet(ROOT / "places/sgp_places_final.parquet")
    mg = pd.read_parquet(ROOT / "places/sgp_places_micrograph.parquet")
    print(f"  places: {len(places):,}  micrograph: {len(mg):,}")

    # Re-key via hex9 universe (consistent with rest of pipeline)
    h9_uni = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
    places = places.drop(columns=["hex8_id"], errors="ignore").merge(
        h9_uni[["hex9_id","parent_hex8","parent_subzone"]].rename(
            columns={"parent_hex8":"hex8_id","parent_subzone":"subzone_c_v4"}),
        on="hex9_id", how="left",
    )
    pmg = places[["id","plexis_category","hex9_id","hex8_id","subzone_c_v4"]].merge(mg, on="id")
    print(f"  joined places+mg: {pmg.shape}")

    # === HEX-9 ===
    print("\n--- HEX-9 ---")
    h9 = per_cat_rollup(pmg, "hex9_id")
    # Reindex to full universe (hexes with no places get 0s)
    h9 = h9_uni[["hex9_id"]].merge(h9, on="hex9_id", how="left").fillna(0)
    # Round
    for c in h9.columns:
        if c != "hex9_id":
            h9[c] = h9[c].astype(float).round(3)
    h9.to_parquet(ROOT / "hex/hex9_micrograph_rollup.parquet", index=False)
    print(f"  hex9_micrograph_rollup: {h9.shape}")

    # === HEX-8 ===
    print("\n--- HEX-8 ---")
    h8_uni = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")
    h8 = per_cat_rollup(pmg, "hex8_id")
    h8 = h8_uni[["hex8_id"]].merge(h8, on="hex8_id", how="left").fillna(0)
    for c in h8.columns:
        if c != "hex8_id":
            h8[c] = h8[c].astype(float).round(3)
    h8.to_parquet(ROOT / "hex/hex8_micrograph_rollup.parquet", index=False)
    print(f"  hex8_micrograph_rollup: {h8.shape}")

    # === SUBZONE ===
    print("\n--- SUBZONE ---")
    sz_lu = pd.read_parquet(ROOT / "hex/subzone_land_use.parquet")[["subzone_c"]].drop_duplicates()
    sz_pmg = pmg.dropna(subset=["subzone_c_v4"]).rename(columns={"subzone_c_v4":"subzone_c"})
    sz = per_cat_rollup(sz_pmg, "subzone_c")
    sz = sz_lu.merge(sz, on="subzone_c", how="left").fillna(0)
    for c in sz.columns:
        if c != "subzone_c":
            sz[c] = sz[c].astype(float).round(3)
    sz.to_parquet(ROOT / "hex/subzone_micrograph_rollup.parquet", index=False)
    print(f"  subzone_micrograph_rollup: {sz.shape}")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "shapes": {"hex9": list(h9.shape), "hex8": list(h8.shape), "subzone": list(sz.shape)},
        "categories": len(CATEGORIES),
    }
    with open(ROOT / "hex/micrograph_rollup_report.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n{json.dumps(summary, indent=2)}")


if __name__ == "__main__":
    main()
