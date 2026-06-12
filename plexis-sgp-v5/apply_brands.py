"""
Plexis SGP v4 — Stage 1c — brand normalization + pattern detection.
  - Normalizes existing `brand` field via BRAND_ALIASES
  - For rows with empty brand, runs regex patterns on `name` to detect chains
  - Writes output to sgp_places_branded.parquet
  - Builds a brand rollup table with: brand, category, n_locations, regions
"""
import json, time
from pathlib import Path
import pandas as pd
from brand_map import normalize_brand, detect_brand_from_name, BRAND_PATTERNS

ROOT = Path(__file__).parent
IN_PQ = ROOT / "places/sgp_places_categorized.parquet"
OUT_PQ = ROOT / "places/sgp_places_branded.parquet"
BRAND_TABLE_PQ = ROOT / "places/brand_rollup.parquet"
REPORT = ROOT / "places/brand_report.json"


def main():
    t0 = time.time()
    df = pd.read_parquet(IN_PQ)
    print(f"Loaded {len(df):,} places")

    # Step 1: normalize existing brand field
    df["brand_norm"] = df["brand"].apply(normalize_brand)
    n_existing = df["brand_norm"].notna().sum()
    print(f"Existing brand (normalized): {n_existing:,}")

    # Step 2: fill missing brand from name patterns
    missing_mask = df["brand_norm"].isna()
    candidates = df[missing_mask].index
    detected = 0
    category_overrides = 0

    for idx in candidates:
        name = df.at[idx, "name"]
        res = detect_brand_from_name(name)
        if res is None:
            continue
        brand, expected_cat = res
        df.at[idx, "brand_norm"] = brand
        df.at[idx, "brand_source"] = "name_pattern"
        # If current plexis_category is 'other_uncategorized', override
        if df.at[idx, "plexis_category"] == "other_uncategorized":
            df.at[idx, "plexis_category"] = expected_cat
            category_overrides += 1
        detected += 1

    df.loc[df["brand_norm"].notna() & df["brand_source"].isna(), "brand_source"] = "scrape"
    n_total = df["brand_norm"].notna().sum()
    print(f"Detected from name: {detected:,}")
    print(f"Category overrides (from unknown -> brand's expected cat): {category_overrides:,}")
    print(f"Total branded: {n_total:,} ({100*n_total/len(df):.2f}%)")

    # Step 3: consistency check — brand.category should match plexis_category in most cases
    # Build expected_category map from BRAND_PATTERNS
    brand_to_cat = {b: c for b, _, c in BRAND_PATTERNS}
    df["brand_expected_cat"] = df["brand_norm"].map(brand_to_cat)
    df["brand_cat_mismatch"] = df["brand_expected_cat"].notna() & (df["brand_expected_cat"] != df["plexis_category"])
    mismatches = df["brand_cat_mismatch"].sum()
    print(f"Brand-category mismatches: {mismatches:,} (investigate)")
    if mismatches:
        sample = df[df["brand_cat_mismatch"]].head(5)[["name","brand_norm","plexis_category","brand_expected_cat"]]
        print("  samples:")
        for _, r in sample.iterrows():
            print(f"    {str(r['name'])[:40]:40s}  brand={r['brand_norm']:20s}  cat={r['plexis_category']}  expected={r['brand_expected_cat']}")

    # Save
    df = df.drop(columns=["brand_cat_mismatch", "brand_expected_cat"])  # keep table lean
    df.to_parquet(OUT_PQ, index=False)

    # Step 4: brand rollup
    rollup = (
        df[df["brand_norm"].notna()]
        .groupby("brand_norm")
        .agg(
            n_locations=("id", "count"),
            primary_category=("plexis_category", lambda s: s.mode().iloc[0] if len(s) else None),
            region_mix=("parent_region", lambda s: s.value_counts(normalize=True).round(3).to_dict()),
            top_pa=("parent_pa", lambda s: s.value_counts().index[0] if len(s) else None),
        )
        .sort_values("n_locations", ascending=False)
        .reset_index()
    )
    # region_mix is a dict; flatten to JSON for parquet compatibility
    rollup["region_mix"] = rollup["region_mix"].apply(json.dumps)
    rollup.to_parquet(BRAND_TABLE_PQ, index=False)

    print(f"\n=== Top 30 brands by # locations ===")
    for _, r in rollup.head(30).iterrows():
        rm = json.loads(r["region_mix"])
        top_rg = max(rm, key=rm.get) if rm else "?"
        print(f"  {r['n_locations']:>5,}  {r['brand_norm']:30s}  cat={r['primary_category']:20s}  top_rg={top_rg}  top_pa={r['top_pa']}")

    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_places": len(df),
        "branded_total": int(n_total),
        "branded_from_scrape": int(n_total - detected),
        "branded_from_name_pattern": int(detected),
        "category_overrides_from_brand": int(category_overrides),
        "brand_category_mismatches": int(mismatches),
        "unique_brands": int(df["brand_norm"].nunique(dropna=True)),
        "branded_pct": round(100 * n_total / len(df), 4),
        "wall_clock_s": round(time.time() - t0, 2),
    }
    with open(REPORT, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport: {REPORT}")


if __name__ == "__main__":
    main()
