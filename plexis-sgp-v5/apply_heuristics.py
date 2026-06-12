"""
Plexis SGP v4 — Stage 1b.2a — apply heuristic name classifier to unresolved rows.
Updates `plexis_category` in the categorized parquet; remaining nulls go to Stage 1b.2b (LLM).
"""
import json, time
from pathlib import Path
import pandas as pd
from classify_heuristics import classify_by_name

ROOT = Path(__file__).parent
IN_PQ = ROOT / "places/sgp_places_categorized.parquet"  # output of apply_category_map
OUT_PQ = ROOT / "places/sgp_places_categorized.parquet"  # overwrite same file
RESIDUE_PQ = ROOT / "places/sgp_places_unresolved_after_heuristics.parquet"
REPORT = ROOT / "places/heuristics_report.json"


def main():
    t0 = time.time()
    df = pd.read_parquet(IN_PQ)
    print(f"Loaded {len(df):,} places")
    before = df["plexis_category"].notna().sum()
    print(f"Resolved before heuristics: {before:,}")

    # Only run heuristics on rows without plexis_category
    mask = df["plexis_category"].isna()
    print(f"Unresolved rows: {mask.sum():,}")

    # Apply
    heur_cat = df[mask].apply(
        lambda r: classify_by_name(r.get("name") or "", r.get("address") or ""),
        axis=1,
    )
    df.loc[mask, "plexis_category"] = heur_cat
    after = df["plexis_category"].notna().sum()
    added = after - before
    print(f"Added by heuristics: {added:,}")
    print(f"Resolved after heuristics: {after:,} ({100*after/len(df):.2f}%)")
    print(f"Still unresolved: {len(df)-after:,}")

    # Persist
    df.to_parquet(OUT_PQ, index=False)
    df[df["plexis_category"].isna()].to_parquet(RESIDUE_PQ, index=False)

    cat_counts = df["plexis_category"].fillna("__unresolved").value_counts()
    print("\n=== Plexis category distribution (after heuristics) ===")
    for cat, c in cat_counts.items():
        print(f"  {c:>7,}  {cat}")

    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "input_rows": len(df),
        "before_resolved": int(before),
        "added_by_heuristics": int(added),
        "after_resolved": int(after),
        "still_unresolved": int(len(df) - after),
        "resolution_rate_pct": round(100 * after / len(df), 4),
        "distribution": {k: int(v) for k, v in cat_counts.items()},
        "wall_clock_s": round(time.time() - t0, 2),
    }
    with open(REPORT, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport: {REPORT}")


if __name__ == "__main__":
    main()
