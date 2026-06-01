"""
Plexis SGP v4 — Stage 1d — quality/review-derived features per place.

Inputs:
  places/sgp_places_branded.parquet
Outputs:
  places/sgp_places_final.parquet      (190,591 × ~23 cols — the Stage 1 deliverable)
  places/quality_report.json
  places/category_quality_benchmarks.parquet  (per-category rating/review percentiles)

Added columns:
  has_rating, has_reviews            (bool)
  review_bucket                      (none | 1-9 | 10-99 | 100-999 | 1000+)
  magnet_strength                    (float: rating * log(reviews_count+1), nan if no rating)
  review_quality_pctl_in_cat         (percentile within plexis_category, 0-1)
  is_magnet                          (reviews_count >= 100 AND rating >= 4.0)
  is_long_tail                       (reviews_count < 5 OR rating is null)
"""
import json, time
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
IN_PQ = ROOT / "places/sgp_places_branded.parquet"
OUT_PQ = ROOT / "places/sgp_places_final.parquet"
BENCH_PQ = ROOT / "places/category_quality_benchmarks.parquet"
REPORT = ROOT / "places/quality_report.json"


def main():
    t0 = time.time()
    df = pd.read_parquet(IN_PQ)
    print(f"Loaded {len(df):,} places")

    # Clean types
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df["reviews_count"] = pd.to_numeric(df["reviews_count"], errors="coerce").fillna(0).astype(int)
    df.loc[df["rating"] == 0, "rating"] = np.nan  # treat 0 as no rating

    # has_rating / has_reviews
    df["has_rating"] = df["rating"].notna()
    df["has_reviews"] = df["reviews_count"] > 0
    print(f"has_rating: {df['has_rating'].sum():,} ({100*df['has_rating'].mean():.1f}%)")
    print(f"has_reviews (>0): {df['has_reviews'].sum():,} ({100*df['has_reviews'].mean():.1f}%)")

    # Review bucket
    def bucket(n):
        if n == 0: return "none"
        if n < 10: return "1-9"
        if n < 100: return "10-99"
        if n < 1000: return "100-999"
        return "1000+"
    df["review_bucket"] = df["reviews_count"].apply(bucket)

    # Magnet strength = rating * log(reviews_count + 1)
    df["magnet_strength"] = df["rating"] * np.log1p(df["reviews_count"])

    # Per-category percentile of magnet_strength (only among places with a rating)
    # Rank within each plexis_category
    def pct_rank(s):
        return s.rank(pct=True)

    df["review_quality_pctl_in_cat"] = (
        df.groupby("plexis_category")["magnet_strength"].transform(pct_rank)
    )

    # Flags
    df["is_magnet"] = (df["reviews_count"] >= 100) & (df["rating"] >= 4.0)
    df["is_long_tail"] = (df["reviews_count"] < 5) | df["rating"].isna()

    # Summary
    print(f"\nBucket distribution:")
    for k in ["none", "1-9", "10-99", "100-999", "1000+"]:
        n = (df["review_bucket"] == k).sum()
        print(f"  {k:>8s}  {n:>7,}  ({100*n/len(df):.1f}%)")
    print(f"\nMagnets (rating ≥ 4 AND reviews ≥ 100): {df['is_magnet'].sum():,} ({100*df['is_magnet'].mean():.1f}%)")
    print(f"Long-tail (reviews < 5 OR no rating): {df['is_long_tail'].sum():,} ({100*df['is_long_tail'].mean():.1f}%)")

    # Per-category benchmarks
    bench = df.groupby("plexis_category").agg(
        n=("id", "count"),
        n_with_rating=("has_rating", "sum"),
        median_rating=("rating", "median"),
        p75_rating=("rating", lambda s: s.quantile(0.75)),
        median_reviews=("reviews_count", "median"),
        p75_reviews=("reviews_count", lambda s: s.quantile(0.75)),
        p95_reviews=("reviews_count", lambda s: s.quantile(0.95)),
        p75_magnet=("magnet_strength", lambda s: s.quantile(0.75)),
        magnets=("is_magnet", "sum"),
        long_tail=("is_long_tail", "sum"),
    ).reset_index()
    bench["pct_with_rating"] = (bench["n_with_rating"] / bench["n"]).round(3)
    bench["pct_magnets"] = (bench["magnets"] / bench["n"]).round(3)
    bench = bench.sort_values("n", ascending=False).reset_index(drop=True)
    bench.to_parquet(BENCH_PQ, index=False)

    print(f"\n=== Category benchmarks (top 15 categories) ===")
    print(bench.head(15).to_string(index=False))

    # Per-region quality signal
    print(f"\n=== Magnet count by region ===")
    reg = df.groupby("parent_region").agg(
        n=("id", "count"),
        magnets=("is_magnet", "sum"),
        pct_magnets=("is_magnet", "mean"),
    ).reset_index().sort_values("magnets", ascending=False)
    print(reg.to_string(index=False))

    # Top magnet places overall
    print(f"\n=== Top 20 magnet places (high rating × many reviews) ===")
    top = df[df["is_magnet"]].nlargest(20, "magnet_strength")
    for _, r in top.iterrows():
        print(f"  {r['magnet_strength']:>6.2f}  [{r['plexis_category']:22s}]  {str(r['name'])[:45]:45s}  {r['rating']}★ × {r['reviews_count']:,} reviews  ({r['parent_pa']})")

    df.to_parquet(OUT_PQ, index=False)

    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_places": len(df),
        "has_rating": int(df["has_rating"].sum()),
        "has_reviews": int(df["has_reviews"].sum()),
        "pct_with_rating": round(100 * df["has_rating"].mean(), 2),
        "pct_with_reviews": round(100 * df["has_reviews"].mean(), 2),
        "magnets": int(df["is_magnet"].sum()),
        "long_tail": int(df["is_long_tail"].sum()),
        "bucket_distribution": {k: int((df["review_bucket"] == k).sum()) for k in ["none","1-9","10-99","100-999","1000+"]},
        "region_magnets": {r["parent_region"]: int(r["magnets"]) for _, r in reg.iterrows()},
        "wall_clock_s": round(time.time() - t0, 2),
    }
    with open(REPORT, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport: {REPORT}")
    print(f"Final: {OUT_PQ}")


if __name__ == "__main__":
    main()
