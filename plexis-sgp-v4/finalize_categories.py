"""
Plexis SGP v4 — Stage 1b.2b (fallback): mark residue as `other_uncategorized`.
LLM pass can rerun later via llm_classify.py when an API key is available.
"""
import json, time
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent
PQ = ROOT / "places/sgp_places_categorized.parquet"
REPORT = ROOT / "places/stage_1b_final_report.json"


def main():
    df = pd.read_parquet(PQ)
    n_unresolved = df["plexis_category"].isna().sum()
    print(f"Unresolved before finalize: {n_unresolved:,}")
    df["plexis_category"] = df["plexis_category"].fillna("other_uncategorized")
    df.to_parquet(PQ, index=False)
    cat_counts = df["plexis_category"].value_counts()
    resolved_non_uncat = (df["plexis_category"] != "other_uncategorized").sum()
    print(f"\n=== Final category distribution ({len(df):,} places) ===")
    for cat, c in cat_counts.items():
        print(f"  {c:>7,}  {cat}  ({100*c/len(df):.2f}%)")
    print(f"\nNon-uncategorized: {resolved_non_uncat:,} / {len(df):,} = {100*resolved_non_uncat/len(df):.2f}%")
    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total": len(df),
        "resolved_non_uncategorized": int(resolved_non_uncat),
        "resolution_rate_pct": round(100 * resolved_non_uncat / len(df), 4),
        "filled_with_uncategorized": int(n_unresolved),
        "distribution": {k: int(v) for k, v in cat_counts.items()},
        "next_step": "LLM refinement of other_uncategorized when OpenRouter key available",
    }
    with open(REPORT, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport: {REPORT}")


if __name__ == "__main__":
    main()
