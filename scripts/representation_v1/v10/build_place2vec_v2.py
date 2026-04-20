"""
Place2Vec v2 — context-only place representation.

v1 lesson: one-hot category (24 dims) dominates the 68-dim vector, making
category kNN trivially 99.5% but the vector useless for cross-category
similarity. The identity layer IS the vector; everything else is noise.

v2 design: REMOVE category and tier from the vector. Keep them as metadata.
The vector encodes CONTEXT ONLY — the urban role of a place regardless of
what category it is. Two places with similar vectors serve the same kind of
area, the same kind of customer, the same transit pattern.

This means:
  - A premium cafe in Orchard and a premium restaurant in Orchard should be
    NEAR each other (same context: transit-rich, tourist-heavy, luxury cluster)
  - A budget hawker in Bedok and a budget convenience store in Bedok should
    be NEAR each other (same context: HDB residential, family catchment)
  - The SAME Starbucks in Orchard vs Bedok should be FAR apart (different
    context despite same identity)

Vector: 37 dimensions
  Layer 1: Spatial context (micrograph)     12 dims
  Layer 2: Hex context                      14 dims
  Layer 3: Influence context                 7 dims
  Layer 4: Competitive position              4 dims

Category and tier become METADATA columns (for filtering/labeling, not for similarity).
"""
import json
import os
from collections import Counter, defaultdict

import h3
import numpy as np
import pandas as pd

ROOT = "/home/azureuser/digital-atlas-sgp"
PLACES_PATH = os.path.join(ROOT, "data/places_consolidated/sgp_places_v2.jsonl")
MG_DIR = os.path.join(ROOT, "micrograph_output_v3")
HEX_PATH = os.path.join(ROOT, "data/hex_v10/hex_features_v10.parquet")
OUT_PATH = os.path.join(ROOT, "data/hex_v10/place_vectors_v2.parquet")
OUT_NORM = os.path.join(ROOT, "data/hex_v10/place_vectors_v2_normalized.parquet")
OUT_CATALOG = os.path.join(ROOT, "data/hex_v10/place2vec_v2_catalog.json")

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
TIER_TO_IDX = {t: i for i, t in enumerate(PRICE_TIERS)}
DENSITY_BANDS = ["hyperdense", "dense", "moderate", "sparse"]
BAND_TO_IDX = {b: i for i, b in enumerate(DENSITY_BANDS)}
CAT_TO_GAP = {
    "Shopping & Retail": "gap_commercial", "Restaurant": "gap_commercial",
    "Cafe & Coffee": "gap_commercial", "Bar & Nightlife": "gap_commercial",
    "Fast Food & QSR": "gap_commercial", "Bakery & Pastry": "gap_commercial",
    "Hospitality": "gap_commercial", "Culture & Entertainment": "gap_commercial",
    "Beauty & Personal Care": "gap_commercial", "Convenience & Daily Needs": "gap_commercial",
    "Hawker & Street Food": "gap_commercial", "Services": "gap_commercial",
    "Business": "gap_industrial", "Automotive": "gap_industrial",
    "Office & Workspace": "gap_industrial", "Education": "gap_residential",
    "Health & Medical": "gap_residential", "Fitness & Recreation": "gap_residential",
    "Residential": "gap_residential", "Civic & Government": "gap_residential",
    "Religious": "gap_residential", "NGO": "gap_residential",
    "Transport": "gap_industrial", "General": "gap_commercial",
}

def cat_slug(cat):
    return cat.lower().replace(" & ", "_").replace(" ", "_").replace("&", "_")


def main():
    print("Loading hex features...")
    hex_df = pd.read_parquet(HEX_PATH)
    hex_lookup = {row["hex_id"]: row for _, row in hex_df.iterrows()}
    hex_set = set(hex_lookup.keys())
    print(f"  {len(hex_lookup)} hexes")

    print("Loading micrographs v3...")
    mg_lookup = {}
    mg_files = [f for f in os.listdir(MG_DIR) if f.endswith("_micrographs.jsonl")]
    for fn in mg_files:
        with open(os.path.join(MG_DIR, fn)) as f:
            for ln in f:
                d = json.loads(ln)
                pid = d.get("place_id")
                if not pid:
                    continue
                cv = d.get("context_vector", {})
                if isinstance(cv, str):
                    try:
                        cv = json.loads(cv.replace("'", '"'))
                    except Exception:
                        cv = {}
                mg_lookup[pid] = {
                    "cv_transit": float(cv.get("transit", 0)),
                    "cv_competitor": float(cv.get("competitor", 0)),
                    "cv_complementary": float(cv.get("complementary", 0)),
                    "cv_demand": float(cv.get("demand", 0)),
                    "anchor_count": float(d.get("anchor_count", 0)),
                    "competitive_pressure": float(d.get("competitive_pressure", 0)),
                    "demand_diversity": float(d.get("demand_diversity", 0)),
                    "walkability_index": float(d.get("walkability_index", 0)),
                    "density_band": d.get("density_band", ""),
                }
    print(f"  {len(mg_lookup):,} micrographs")

    # Pre-compute per-hex stats
    print("Pre-computing per-hex stats...")
    hex_cat_count = defaultdict(Counter)
    hex_brand_count = defaultdict(Counter)
    hex_tier_dist = defaultdict(Counter)
    with open(PLACES_PATH) as f:
        for ln in f:
            d = json.loads(ln)
            lat, lng = d.get("latitude"), d.get("longitude")
            if lat is None or lng is None:
                continue
            hid = h3.latlng_to_cell(lat, lng, 9)
            if hid not in hex_set:
                continue
            hex_cat_count[hid][d.get("main_category", "")] += 1
            brand = d.get("brand")
            if brand and brand != "None":
                hex_brand_count[hid][brand] += 1
            tier = d.get("price_tier", "")
            if tier:
                hex_tier_dist[hid][tier] += 1

    # Build vectors
    print("Building v2 place vectors (context-only, no category/tier one-hot)...")
    rows = []
    n_total = n_in = n_mg = 0

    with open(PLACES_PATH) as f:
        for ln in f:
            d = json.loads(ln)
            n_total += 1
            lat, lng = d.get("latitude"), d.get("longitude")
            if lat is None or lng is None:
                continue
            hid = h3.latlng_to_cell(lat, lng, 9)
            if hid not in hex_set:
                continue
            n_in += 1

            cat = d.get("main_category", "")
            tier = d.get("price_tier", "")
            brand = d.get("brand")
            is_branded = 1 if brand and brand != "None" else 0
            pid = d.get("id", "")
            mg = mg_lookup.get(pid)
            has_mg = 1 if mg else 0
            if has_mg:
                n_mg += 1
            hex_row = hex_lookup[hid]

            # === LAYER 1: SPATIAL CONTEXT (micrograph) — 12 dims ===
            if mg:
                cv_t = mg["cv_transit"]
                cv_c = mg["cv_competitor"]
                cv_m = mg["cv_complementary"]
                cv_d = mg["cv_demand"]
                anch = mg["anchor_count"]
                comp = mg["competitive_pressure"]
                ddiv = mg["demand_diversity"]
                walk_mg = mg["walkability_index"]
                band_oh = [0, 0, 0, 0]
                if mg["density_band"] in BAND_TO_IDX:
                    band_oh[BAND_TO_IDX[mg["density_band"]]] = 1
            else:
                cv_t = cv_c = cv_m = cv_d = 0.0
                anch = comp = ddiv = walk_mg = 0.0
                band_oh = [0, 0, 0, 0]

            # === LAYER 2: HEX CONTEXT — 14 dims ===
            area = float(hex_row.get("area_km2", 0.105))
            pop = float(hex_row.get("population", 0))
            pop_total = float(hex_row.get("population_total", 0))
            pop_density = pop / area if area > 0 else 0
            pop_total_density = pop_total / area if area > 0 else 0
            daytime_r = float(hex_row.get("daytime_ratio", 0))
            lu_com = float(hex_row.get("lu_commercial_pct", 0))
            lu_res = float(hex_row.get("lu_residential_pct", 0))
            gpr = float(hex_row.get("avg_gpr", 0))
            pc_tot = float(hex_row.get("pc_total", 0))
            cat_sl = cat_slug(cat) if cat else ""
            pc_same_col = f"pc_cat_{cat_sl}"
            pc_same = float(hex_row.get(pc_same_col, 0)) if pc_same_col in hex_row.index else 0
            pc_ent = float(hex_row.get("pc_cat_entropy", 0))
            walk_hex = float(hex_row.get("walkability_score", 0))
            mrt = float(hex_row.get("mrt_stations", 0))
            hdb_bl = float(hex_row.get("hdb_blocks", 0))
            bldg_ct = float(hex_row.get("bldg_count", 1))
            hdb_ratio = hdb_bl / bldg_ct if bldg_ct > 0 else 0
            tourist = float(hex_row.get("tourist_draw_est", 0))
            gap_col = CAT_TO_GAP.get(cat, "ura_development_gap")
            gap_val = float(hex_row.get(gap_col, 0))

            # === LAYER 3: INFLUENCE CONTEXT — 7 dims ===
            sp_max_pc = float(hex_row.get("sp_max_pc_total", 0))
            sp_max_same_col = f"sp_max_pc_cat_{cat_sl}"
            sp_max_same = float(hex_row.get(sp_max_same_col, 0)) if sp_max_same_col in hex_row.index else 0
            sp_pw_pc = float(hex_row.get("sp_pw_pc_total", 0))
            tr_max_pc = float(hex_row.get("tr_max_pc_total", 0))
            tr_max_same_col = f"tr_max_pc_cat_{cat_sl}"
            tr_max_same = float(hex_row.get(tr_max_same_col, 0)) if tr_max_same_col in hex_row.index else 0
            tr_near = float(hex_row.get("tr_nearest_station_rings", 0))
            tr_reach = float(hex_row.get("tr_reachable_hexes", 0))

            # === LAYER 4: COMPETITIVE POSITION — 4 dims ===
            tier_idx = TIER_TO_IDX.get(tier, 2)
            hex_tiers = hex_tier_dist.get(hid, Counter())
            total_tiered = sum(hex_tiers.values())
            tiers_above = sum(hex_tiers.get(PRICE_TIERS[i], 0) for i in range(tier_idx))
            tier_rank = tiers_above / total_tiered if total_tiered > 0 else 0.5

            if is_branded and brand:
                brand_count_here = hex_brand_count[hid].get(brand, 1)
                brand_rarity = 1.0 / brand_count_here
            else:
                brand_rarity = 0.0

            total_in_hex = sum(hex_cat_count[hid].values())
            cat_share = hex_cat_count[hid].get(cat, 0) / total_in_hex if total_in_hex > 0 else 0
            sorted_cats = sorted(hex_cat_count[hid].values(), reverse=True)
            my_count = hex_cat_count[hid].get(cat, 0)
            cat_rank = (sorted_cats.index(my_count) / len(sorted_cats)) if my_count in sorted_cats and len(sorted_cats) > 1 else 0.5

            # === ASSEMBLE — 37 dims ===
            vector = (
                [cv_t, cv_c, cv_m, cv_d, anch, comp, ddiv, walk_mg] + band_oh +  # 12
                [pop_density, pop_total_density, daytime_r, lu_com, lu_res, gpr,
                 pc_tot, pc_same, pc_ent, walk_hex, mrt, hdb_ratio, tourist, gap_val] +  # 14
                [sp_max_pc, sp_max_same, sp_pw_pc, tr_max_pc, tr_max_same, tr_near, tr_reach] +  # 7
                [tier_rank, brand_rarity, cat_share, cat_rank]  # 4
            )

            rows.append({
                "place_id": pid,
                "name": d.get("name", ""),
                "hex_id": hid,
                "main_category": cat,
                "price_tier": tier,
                "brand": brand if brand and brand != "None" else "",
                "is_branded": is_branded,
                "has_micrograph": has_mg,
                "latitude": lat,
                "longitude": lng,
                **{f"v{i}": v for i, v in enumerate(vector)},
            })

    print(f"  total: {n_total:,}  in hex: {n_in:,}  micrographed: {n_mg:,}")
    print(f"  vector dim: {len(vector)}")

    out = pd.DataFrame(rows)
    meta_cols = ["place_id", "name", "hex_id", "main_category", "price_tier", "brand", "is_branded", "has_micrograph", "latitude", "longitude"]
    vec_cols = [c for c in out.columns if c.startswith("v")]

    out.to_parquet(OUT_PATH, index=False)
    print(f"  wrote {OUT_PATH} ({out.shape})")

    # Normalize
    norm = out[meta_cols].copy()
    for c in vec_cols:
        i = int(c[1:])
        raw = out[c].astype("float64")
        # bounded [0,1]: cv weights, band one-hot, shares, scores, ratios
        if i < 8 or (8 <= i < 12):  # cv + band one-hot
            t = raw
        elif i in {15, 16, 21, 25}:  # daytime, lu_com/res, walk_hex, pc_ent — bounded
            t = raw
        elif i in {33, 34, 35, 36}:  # tier_rank, brand_rarity, cat_share, cat_rank — bounded
            t = raw
        else:
            t = np.sqrt(raw.clip(lower=0))
        t = t.replace([np.inf, -np.inf], np.nan)
        mu = float(t.dropna().mean()) if t.dropna().size else 0
        sd = float(t.dropna().std(ddof=0)) if t.dropna().size else 1
        if sd < 1e-9:
            sd = 1
        norm[c] = ((t - mu) / sd).fillna(0)

    norm.to_parquet(OUT_NORM, index=False)
    print(f"  wrote {OUT_NORM}")

    # Catalog
    dim_names = (
        ["cv_transit", "cv_competitor", "cv_complementary", "cv_demand",
         "anchor_count", "competitive_pressure", "demand_diversity", "walkability_index"] +
        [f"band_{b}" for b in DENSITY_BANDS] +
        ["pop_density", "pop_total_density", "daytime_ratio", "lu_commercial_pct",
         "lu_residential_pct", "avg_gpr", "pc_total", "pc_same_category",
         "pc_cat_entropy", "walkability_score", "mrt_stations", "hdb_ratio",
         "tourist_draw", "gap_for_category"] +
        ["sp_max_pc_total", "sp_max_same_category", "sp_pw_pc_total",
         "tr_max_pc_total", "tr_max_same_category", "tr_nearest_rings", "tr_reachable_hexes"] +
        ["tier_rank_in_hex", "brand_rarity", "category_share", "category_rank"]
    )
    catalog = {
        "version": "v2",
        "design": "context-only — NO category/tier one-hot. Category is metadata, not a feature.",
        "vector_dim": len(vector),
        "total_places": n_in,
        "with_micrograph": n_mg,
        "layers": {
            "spatial_context": {"dims": "0-11", "count": 12},
            "hex_context": {"dims": "12-25", "count": 14},
            "influence": {"dims": "26-32", "count": 7},
            "competitive_position": {"dims": "33-36", "count": 4},
        },
        "dim_names": dim_names,
    }
    with open(OUT_CATALOG, "w") as f:
        json.dump(catalog, f, indent=2)

    # Quick test
    print("\nSanity: Starbucks Orchard vs Starbucks Bedok")
    sb = out[out["name"].str.contains("Starbucks", case=False, na=False)]
    hex_pa_map = dict(zip(hex_df["hex_id"], hex_df["parent_pa"]))
    sb_orch = sb[sb["hex_id"].map(hex_pa_map).isin(["ORCHARD", "DOWNTOWN CORE"])].head(1)
    sb_bed = sb[sb["hex_id"].map(hex_pa_map).isin(["BEDOK", "TAMPINES"])].head(1)
    if len(sb_orch) and len(sb_bed):
        v1 = norm.loc[sb_orch.index[0], vec_cols].values.astype(float)
        v2 = norm.loc[sb_bed.index[0], vec_cols].values.astype(float)
        cos = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9)
        print(f"  {sb_orch.iloc[0]['name'][:40]} vs {sb_bed.iloc[0]['name'][:40]}")
        print(f"  cosine: {cos:.3f} (should be LOW — different context)")

    # Cross-category test: premium cafe vs premium restaurant in same hex
    orch_hex = hex_df[hex_df["parent_pa"] == "ORCHARD"].nlargest(1, "pc_total")["hex_id"].iloc[0]
    cafe_orch = out[(out["hex_id"] == orch_hex) & (out["main_category"] == "Cafe & Coffee") & (out["price_tier"] == "Premium")].head(1)
    rest_orch = out[(out["hex_id"] == orch_hex) & (out["main_category"] == "Restaurant") & (out["price_tier"] == "Premium")].head(1)
    if len(cafe_orch) and len(rest_orch):
        v1 = norm.loc[cafe_orch.index[0], vec_cols].values.astype(float)
        v2 = norm.loc[rest_orch.index[0], vec_cols].values.astype(float)
        cos = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9)
        print(f"\n  Premium cafe vs premium restaurant in SAME Orchard hex:")
        print(f"  {cafe_orch.iloc[0]['name'][:40]} vs {rest_orch.iloc[0]['name'][:40]}")
        print(f"  cosine: {cos:.3f} (should be HIGH — same context)")


if __name__ == "__main__":
    main()
