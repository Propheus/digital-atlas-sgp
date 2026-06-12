"""
Plexis SGP v4 — Stage 14: saturation / gap analysis per scale.

For each commercial-amenity category, compute supply per capita and gap vs
the SGP average. A high gap = under-supplied; negative = over-supplied.

Categories analyzed:
  cafe_coffee, restaurant, hawker, fast_food, supermarket, bakery,
  beauty_personal, fitness_recreation, health_medical

Per-hex columns (~9 sat_* + 9 gap_*):
  sat_<cat>_per_1k      places per 1,000 residents (clamped)
  gap_<cat>             (national_avg - sat_local) / national_avg
                        positive → under-supplied; negative → over-supplied

Outputs:
  hex/hex9_saturation_gap.parquet
  hex/hex8_saturation_gap.parquet
  hex/subzone_saturation_gap.parquet
"""
import json, time
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent

CATEGORIES = [
    "cafe_coffee","restaurant","hawker","fast_food",
    "supermarket","bakery","beauty_personal","fitness_recreation","health_medical",
]


def compute(df, denom_col="pop_resident"):
    out = pd.DataFrame(index=df.index)
    pop = df[denom_col].fillna(0).values.astype(float)
    pop_safe = np.where(pop < 50, np.nan, pop)  # ignore industrial/empty hexes

    for cat in CATEGORIES:
        col = f"pc_cat_{cat}"
        if col not in df.columns:
            continue
        cnt = df[col].fillna(0).values.astype(float)
        per_1k = (cnt / pop_safe) * 1000
        per_1k = np.where(np.isfinite(per_1k), per_1k, 0)
        per_1k = np.clip(per_1k, 0, np.nanpercentile(per_1k[per_1k > 0], 99) if (per_1k > 0).any() else 1)
        out[f"sat_{cat}_per_1k"] = np.round(per_1k, 3)

        # Gap: positive = under-supplied
        national_avg = np.nanmean(per_1k[per_1k > 0]) if (per_1k > 0).any() else 1.0
        gap = (national_avg - per_1k) / max(national_avg, 0.001)
        out[f"gap_{cat}"] = np.round(np.clip(gap, -1, 1), 3)

    return out


def main():
    t0 = time.time()
    for scale, key in [("hex9","hex9_id"),("hex8","hex8_id"),("subzone","subzone_c")]:
        print(f"\n--- {scale.upper()} ---")
        df = pd.read_parquet(ROOT / f"hex/{scale}_all_features.parquet")
        s = compute(df)
        out = pd.concat([df[[key]], s], axis=1)
        out.to_parquet(ROOT / f"hex/{scale}_saturation_gap.parquet", index=False)
        print(f"  {scale}_saturation_gap: {out.shape}")
        # Print top gap examples
        for cat in CATEGORIES[:3]:
            gc = f"gap_{cat}"
            if gc in s.columns:
                print(f"    {gc} dist: p10={s[gc].quantile(0.1):.2f} p50={s[gc].median():.2f} p90={s[gc].quantile(0.9):.2f}")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "categories": CATEGORIES,
    }
    with open(ROOT / "hex/saturation_gap_report.json", "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
