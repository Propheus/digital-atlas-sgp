"""
Representation v1 — hex place composition.

Input:
    data/places_consolidated/sgp_places_v2.jsonl   (174,713 places)
    data/hex_v9/hex_features_v2.parquet            (5,897 H3-9 hexes)

Output:
    model/representation_v1/hex_place_composition.parquet

Schema (one row per hex in the hex universe):
    hex_id                             (H3-9 string)
    pc_total                           (int — total places inside hex)
    pc_cat_<slug>        x 24          (int — count per main_category)
    pc_tier_<Luxury..Budget> x 5       (int — count per price tier)
    pc_pct_cat_<slug>    x 24          (float 0-1)
    pc_pct_tier_<...>    x 5           (float 0-1)
    pc_unique_brands                   (int)
    pc_branded_count                   (int)
    pc_branded_pct                     (float 0-1)
    pc_unique_place_types              (int)
    pc_cat_hhi                         (float 0-1, Herfindahl on main_category)
    pc_cat_entropy                     (float — Shannon nats)
    pc_seg_entropy                     (float — Shannon nats on `segment`)

Hexes with zero places are present as all-zero rows so downstream joins are lossless.
No normalization applied here — raw counts/ratios. Normalization is a later step.
"""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import h3
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PLACES_PATH = ROOT / "data" / "places_consolidated" / "sgp_places_v2.jsonl"
HEX_PATH = ROOT / "data" / "hex_v9" / "hex_features_v2.parquet"
OUT_PATH = ROOT / "model" / "representation_v1" / "hex_place_composition.parquet"

# 24 canonical main categories (fixed order — do not reorder without rebuilding downstream).
MAIN_CATEGORIES = [
    "Shopping & Retail", "Restaurant", "Services", "Business",
    "Beauty & Personal Care", "Education", "Health & Medical", "Cafe & Coffee",
    "Fitness & Recreation", "Convenience & Daily Needs", "Hawker & Street Food",
    "Automotive", "Transport", "Civic & Government", "Bar & Nightlife",
    "Fast Food & QSR", "Residential", "Culture & Entertainment",
    "Office & Workspace", "Hospitality", "Bakery & Pastry", "General",
    "Religious", "NGO",
]

PRICE_TIERS = ["Luxury", "Premium", "Mid", "Value", "Budget"]


def slugify(s: str) -> str:
    return (
        s.lower()
        .replace(" & ", "_")
        .replace(" ", "_")
        .replace("&", "_")
    )


CAT_SLUGS = {c: slugify(c) for c in MAIN_CATEGORIES}


def entropy_nats(counts: list[int]) -> float:
    total = sum(counts)
    if total == 0:
        return 0.0
    h = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            h -= p * math.log(p)
    return h


def hhi(counts: list[int]) -> float:
    total = sum(counts)
    if total == 0:
        return 0.0
    return sum((c / total) ** 2 for c in counts)


def main() -> None:
    print(f"Loading hex universe: {HEX_PATH}")
    hex_df = pd.read_parquet(HEX_PATH, columns=["hex_id"])
    hex_universe = hex_df["hex_id"].tolist()
    hex_set = set(hex_universe)
    print(f"  {len(hex_universe)} hexes")

    print(f"Streaming places: {PLACES_PATH}")
    # per-hex accumulators
    cat_count: dict[str, Counter] = defaultdict(Counter)
    tier_count: dict[str, Counter] = defaultdict(Counter)
    brand_set: dict[str, set] = defaultdict(set)
    branded_count: Counter = Counter()
    type_set: dict[str, set] = defaultdict(set)
    seg_count: dict[str, Counter] = defaultdict(Counter)
    total_count: Counter = Counter()

    # quality counters
    n_total = 0
    n_outside = 0  # places whose computed hex is not in the V9 universe
    n_missing_cat = 0

    with PLACES_PATH.open() as f:
        for ln in f:
            d = json.loads(ln)
            n_total += 1
            lat = d.get("latitude")
            lng = d.get("longitude")
            if lat is None or lng is None:
                continue
            hex_id = h3.latlng_to_cell(lat, lng, 9)
            if hex_id not in hex_set:
                n_outside += 1
                continue
            cat = d.get("main_category")
            if not cat or cat not in CAT_SLUGS:
                n_missing_cat += 1
                continue
            total_count[hex_id] += 1
            cat_count[hex_id][cat] += 1
            tier = d.get("price_tier")
            if tier in PRICE_TIERS:
                tier_count[hex_id][tier] += 1
            brand = d.get("brand")
            if brand and brand != "None":
                brand_set[hex_id].add(brand)
                branded_count[hex_id] += 1
            ptype = d.get("place_type")
            if ptype:
                type_set[hex_id].add(ptype)
            seg = d.get("segment")
            if seg:
                seg_count[hex_id][seg] += 1

    print(f"  read {n_total:,} places")
    print(f"  outside hex universe: {n_outside:,}")
    print(f"  missing/unknown main_category: {n_missing_cat:,}")
    print(f"  hexes with >=1 place: {len(total_count):,}")

    # assemble dataframe — one row per hex in the universe
    rows = []
    for hex_id in hex_universe:
        tot = total_count.get(hex_id, 0)
        row: dict = {"hex_id": hex_id, "pc_total": tot}

        # per-category counts + shares
        cc = cat_count.get(hex_id, Counter())
        cat_counts = [cc.get(c, 0) for c in MAIN_CATEGORIES]
        for c, n in zip(MAIN_CATEGORIES, cat_counts):
            row[f"pc_cat_{CAT_SLUGS[c]}"] = n
        if tot > 0:
            for c, n in zip(MAIN_CATEGORIES, cat_counts):
                row[f"pc_pct_cat_{CAT_SLUGS[c]}"] = n / tot
        else:
            for c in MAIN_CATEGORIES:
                row[f"pc_pct_cat_{CAT_SLUGS[c]}"] = 0.0

        # price tier
        tc = tier_count.get(hex_id, Counter())
        tier_counts = [tc.get(t, 0) for t in PRICE_TIERS]
        tier_total = sum(tier_counts)
        for t, n in zip(PRICE_TIERS, tier_counts):
            row[f"pc_tier_{t.lower()}"] = n
        if tier_total > 0:
            for t, n in zip(PRICE_TIERS, tier_counts):
                row[f"pc_pct_tier_{t.lower()}"] = n / tier_total
        else:
            for t in PRICE_TIERS:
                row[f"pc_pct_tier_{t.lower()}"] = 0.0

        # brands
        row["pc_unique_brands"] = len(brand_set.get(hex_id, ()))
        bcount = branded_count.get(hex_id, 0)
        row["pc_branded_count"] = bcount
        row["pc_branded_pct"] = (bcount / tot) if tot > 0 else 0.0

        # place_type diversity
        row["pc_unique_place_types"] = len(type_set.get(hex_id, ()))

        # concentration metrics on main_category
        row["pc_cat_hhi"] = hhi(cat_counts)
        row["pc_cat_entropy"] = entropy_nats(cat_counts)

        # segment entropy
        sc = seg_count.get(hex_id, Counter())
        row["pc_seg_entropy"] = entropy_nats(list(sc.values()))

        rows.append(row)

    out = pd.DataFrame(rows)
    print(f"Output shape: {out.shape}")
    print(f"Non-empty hexes: {(out['pc_total']>0).sum():,}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT_PATH, index=False)
    print(f"Wrote {OUT_PATH}")

    # quick sanity printout
    print()
    print("Top 5 hexes by pc_total:")
    print(out.nlargest(5, "pc_total")[["hex_id", "pc_total", "pc_cat_restaurant", "pc_cat_cafe_coffee", "pc_cat_shopping_retail", "pc_cat_entropy"]])


if __name__ == "__main__":
    main()
