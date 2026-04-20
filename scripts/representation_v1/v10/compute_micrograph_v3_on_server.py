"""
Compute per-category micrograph v3 features per hex.
Run ON THE SERVER where micrograph_output_v3/ lives.

Input:
    /home/azureuser/digital-atlas-sgp/micrograph_output_v3/*.jsonl (93,788 places × 12 categories)
    /home/azureuser/digital-atlas-sgp/data/hex_v10/hex_universe.parquet

Output:
    /home/azureuser/digital-atlas-sgp/data/hex_v10/hex_micrograph_v3.parquet
"""
import json
import os
from collections import defaultdict

import h3
import numpy as np
import pandas as pd

ROOT = "/home/azureuser/digital-atlas-sgp"
MG_DIR = os.path.join(ROOT, "micrograph_output_v3")
UNI_PATH = os.path.join(ROOT, "data/hex_v10/hex_universe.parquet")
OUT_PATH = os.path.join(ROOT, "data/hex_v10/hex_micrograph_v3.parquet")

CATEGORIES = {
    "cafe": "cafe_micrographs.jsonl",
    "rest": "restaurant_micrographs.jsonl",
    "hawk": "hawker_micrographs.jsonl",
    "fast": "fast_food_qsr_micrographs.jsonl",
    "bake": "bakery_pastry_micrographs.jsonl",
    "bar": "bar_nightlife_micrographs.jsonl",
    "beau": "beauty_personal_care_micrographs.jsonl",
    "heal": "health_medical_micrographs.jsonl",
    "fitn": "fitness_recreation_micrographs.jsonl",
    "educ": "education_micrographs.jsonl",
    "shop": "shopping_retail_micrographs.jsonl",
    "conv": "convenience_daily_needs_micrographs.jsonl",
}

DENSITY_BANDS = ["hyperdense", "dense", "moderate", "sparse"]
CV_KEYS = ["transit", "competitor", "complementary", "demand"]
NUM_KEYS = ["anchor_count", "competitive_pressure", "demand_diversity", "walkability_index"]


def main():
    uni = pd.read_parquet(UNI_PATH)
    hex_set = set(uni["hex_id"])
    hex_ids = uni["hex_id"].tolist()
    print(f"Hex universe: {len(hex_set)} hexes")

    all_results = {hid: {} for hid in hex_ids}

    for cat_prefix, filename in CATEGORIES.items():
        path = os.path.join(MG_DIR, filename)
        print(f"  {cat_prefix} ({filename})...", end="", flush=True)

        n = defaultdict(int)
        sums = defaultdict(lambda: defaultdict(float))
        bands = defaultdict(lambda: defaultdict(int))

        with open(path) as f:
            for ln in f:
                d = json.loads(ln)
                lat = d.get("latitude")
                lng = d.get("longitude")
                if lat is None or lng is None:
                    continue
                hid = h3.latlng_to_cell(lat, lng, 9)
                if hid not in hex_set:
                    continue

                cv = d.get("context_vector", {})
                if isinstance(cv, str):
                    try:
                        cv = json.loads(cv.replace("'", '"'))
                    except Exception:
                        cv = {}

                n[hid] += 1
                for k in CV_KEYS:
                    sums[hid][k] += float(cv.get(k, 0))
                for k in NUM_KEYS:
                    sums[hid][k] += float(d.get(k, 0))
                band = d.get("density_band")
                if band in DENSITY_BANDS:
                    bands[hid][band] += 1

        # Compute means
        p = f"mg_{cat_prefix}"
        for hid in hex_ids:
            count = n.get(hid, 0)
            all_results[hid][f"{p}_n"] = count
            if count > 0:
                for k in CV_KEYS:
                    all_results[hid][f"{p}_cv_{k}"] = sums[hid][k] / count
                all_results[hid][f"{p}_anchor_count"] = sums[hid]["anchor_count"] / count
                all_results[hid][f"{p}_comp_pressure"] = sums[hid]["competitive_pressure"] / count
                all_results[hid][f"{p}_demand_diversity"] = sums[hid]["demand_diversity"] / count
                all_results[hid][f"{p}_walkability"] = sums[hid]["walkability_index"] / count
                for band in DENSITY_BANDS:
                    all_results[hid][f"{p}_pct_{band}"] = bands[hid][band] / count
            else:
                for k in CV_KEYS:
                    all_results[hid][f"{p}_cv_{k}"] = 0.0
                for s in ["anchor_count", "comp_pressure", "demand_diversity", "walkability"]:
                    all_results[hid][f"{p}_{s}"] = 0.0
                for band in DENSITY_BANDS:
                    all_results[hid][f"{p}_pct_{band}"] = 0.0

        total = sum(n.values())
        hexes_with = sum(1 for v in n.values() if v > 0)
        print(f" {total:,} places → {hexes_with} hexes")

    out = pd.DataFrame([{"hex_id": hid, **all_results[hid]} for hid in hex_ids])
    out.to_parquet(OUT_PATH, index=False)
    print(f"\nOutput: {out.shape}")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
