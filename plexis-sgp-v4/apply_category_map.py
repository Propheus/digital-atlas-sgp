"""
Plexis SGP v4 — Stage 1b.1 — apply deterministic category map to geo-attached places.
Adds `plexis_category` column. Rows where it's null are queued for Stage 1b.2 (LLM).
"""
import json, time
from pathlib import Path
import pandas as pd
from category_map import classify, TAXONOMY

ROOT = Path(__file__).parent
IN_PQ = ROOT / "places/sgp_places_geoattached.parquet"
OUT_PQ = ROOT / "places/sgp_places_categorized.parquet"
UNRESOLVED_PQ = ROOT / "places/sgp_places_unresolved_category.parquet"
REPORT = ROOT / "places/category_map_report.json"


def main():
    t0 = time.time()
    df = pd.read_parquet(IN_PQ)
    print(f"Loaded {len(df):,} places")

    df["plexis_category"] = df["primary_category"].map(classify)
    resolved = df["plexis_category"].notna().sum()
    unresolved = df["plexis_category"].isna().sum()
    print(f"Resolved: {resolved:,} ({100*resolved/len(df):.2f}%)")
    print(f"Unresolved (Other/Uncategorized → needs LLM): {unresolved:,}")

    df.to_parquet(OUT_PQ, index=False)
    df_unres = df[df["plexis_category"].isna()].copy()
    df_unres.to_parquet(UNRESOLVED_PQ, index=False)

    # Category distribution
    cat_counts = df["plexis_category"].fillna("__unresolved").value_counts()
    print("\n=== Plexis 24-category distribution ===")
    for cat, c in cat_counts.items():
        print(f"  {c:>7,}  {cat}")

    # Sanity: every taxonomy category should have ≥1 place (except maybe bar_nightlife if none)
    missing_taxo = [t for t in TAXONOMY if t not in cat_counts.index]
    print(f"\nTaxonomy categories missing from data: {missing_taxo}")

    # Per-region breakdown
    print("\n=== Places by plexis_category × region ===")
    pivot = df.pivot_table(
        index="plexis_category",
        columns="parent_region",
        values="id",
        aggfunc="count",
        fill_value=0,
    ).astype(int)
    print(pivot.to_string())

    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "input_rows": len(df),
        "resolved_rows": int(resolved),
        "unresolved_rows": int(unresolved),
        "resolution_rate_pct": round(100 * resolved / len(df), 4),
        "missing_taxonomy_categories": missing_taxo,
        "distribution": {k: int(v) for k, v in cat_counts.items()},
        "wall_clock_s": round(time.time() - t0, 2),
    }
    with open(REPORT, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport: {REPORT}")
    print(f"Resolved: {OUT_PQ}")
    print(f"Unresolved (for LLM): {UNRESOLVED_PQ}  ({len(df_unres):,} rows)")


if __name__ == "__main__":
    main()
