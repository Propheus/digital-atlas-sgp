"""
Place2Vec — vector representation for every place in Singapore.

Architecture: 5 layers of context per place, concatenated into a single vector.

Layer 1 — IDENTITY (what this place IS)
    main_category      24-dim one-hot (Shopping, Restaurant, Cafe, etc.)
    price_tier          5-dim one-hot (Luxury → Budget)
    is_branded          1-dim binary
    has_micrograph      1-dim binary (91K have it, 83K don't)

Layer 2 — SPATIAL CONTEXT (micrograph — what's around THIS specific place)
    cv_transit          T1 weight: how much is this place driven by transit access?
    cv_competitor       T2 weight: how much by same-category competition?
    cv_complementary    T3 weight: how much by complementary categories?
    cv_demand           T4 weight: how much by demand magnets (HDB, offices, schools)?
    anchor_count        richness of the place's spatial graph
    competitive_pressure  how crowded is this category here?
    demand_diversity    breadth of demand sources
    walkability_index   pedestrian accessibility of this specific location
    density_band        4-dim one-hot (hyperdense / dense / moderate / sparse)

Layer 3 — HEX CONTEXT (what the region provides to this place)
    pop_density         population / area_km2 (demand base)
    pop_total_density   total population including non-residents
    daytime_ratio       daytime / nighttime pop (is this a 9-to-5 area or 24h?)
    lu_commercial_pct   share of hex that's commercial zoning
    lu_residential_pct  share that's residential
    avg_gpr             development intensity
    pc_total            total commercial density (competition level)
    pc_same_cat         count of same-category places in this hex
    pc_cat_entropy      commercial diversity of the hex
    walkability_score   hex-level walkability
    mrt_access          mrt_stations (0/1/2/3) — does this hex have an MRT?
    hdb_ratio           hdb_blocks / bldg_count — is this HDB-dominated?
    tourist_draw        estimated tourist daily draw
    gap_for_category    development gap relevant to this place's category
                        (gap_commercial for retail, gap_residential for services)

Layer 4 — INFLUENCE CONTEXT (what's reachable from this place's location)
    sp_max_pc_total     biggest commercial node within walking distance
    sp_max_same_cat     biggest same-category cluster within walk
    sp_pw_pc_total      average commercial density in walking neighborhood
    tr_max_pc_total     biggest commercial node via MRT
    tr_max_same_cat     biggest same-category cluster via MRT
    tr_nearest_rings    how far to the nearest MRT (accessibility)
    tr_reachable        how many hexes can be reached by transit

Layer 5 — COMPETITIVE POSITION (where this place sits among its peers)
    tier_rank_in_hex    is this among the expensive or cheap in its hex?
    brand_rarity        how rare is this brand in this hex? (1/count if branded, 0 if indie)
    category_share      what % of the hex's places is this category?
    category_rank       is this category dominant or minor here?

Total: 24 + 5 + 2 + 4 + 4 + 4 + 14 + 7 + 4 = 68 dimensions per place

Run ON THE SERVER:
    python3 build_place2vec.py

Inputs:
    /home/azureuser/digital-atlas-sgp/data/places_consolidated/sgp_places_v2.jsonl
    /home/azureuser/digital-atlas-sgp/micrograph_output_v3/*.jsonl
    /home/azureuser/digital-atlas-sgp/data/hex_v10/hex_features_v10.parquet

Output:
    /home/azureuser/digital-atlas-sgp/data/hex_v10/place_vectors.parquet
    /home/azureuser/digital-atlas-sgp/data/hex_v10/place_vectors_normalized.parquet
    /home/azureuser/digital-atlas-sgp/data/hex_v10/place2vec_catalog.json
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
OUT_PATH = os.path.join(ROOT, "data/hex_v10/place_vectors.parquet")
OUT_NORM = os.path.join(ROOT, "data/hex_v10/place_vectors_normalized.parquet")
OUT_CATALOG = os.path.join(ROOT, "data/hex_v10/place2vec_catalog.json")

MAIN_CATEGORIES = [
    "Shopping & Retail", "Restaurant", "Services", "Business",
    "Beauty & Personal Care", "Education", "Health & Medical", "Cafe & Coffee",
    "Fitness & Recreation", "Convenience & Daily Needs", "Hawker & Street Food",
    "Automotive", "Transport", "Civic & Government", "Bar & Nightlife",
    "Fast Food & QSR", "Residential", "Culture & Entertainment",
    "Office & Workspace", "Hospitality", "Bakery & Pastry", "General",
    "Religious", "NGO",
]
CAT_TO_IDX = {c: i for i, c in enumerate(MAIN_CATEGORIES)}
PRICE_TIERS = ["Luxury", "Premium", "Mid", "Value", "Budget"]
TIER_TO_IDX = {t: i for i, t in enumerate(PRICE_TIERS)}
DENSITY_BANDS = ["hyperdense", "dense", "moderate", "sparse"]
BAND_TO_IDX = {b: i for i, b in enumerate(DENSITY_BANDS)}

# Category → which gap feature is most relevant
CAT_TO_GAP = {
    "Shopping & Retail": "gap_commercial", "Restaurant": "gap_commercial",
    "Cafe & Coffee": "gap_commercial", "Bar & Nightlife": "gap_commercial",
    "Fast Food & QSR": "gap_commercial", "Bakery & Pastry": "gap_commercial",
    "Hospitality": "gap_commercial", "Culture & Entertainment": "gap_commercial",
    "Beauty & Personal Care": "gap_commercial", "Convenience & Daily Needs": "gap_commercial",
    "Hawker & Street Food": "gap_commercial",
    "Services": "gap_commercial", "Business": "gap_industrial",
    "Automotive": "gap_industrial", "Office & Workspace": "gap_industrial",
    "Education": "gap_residential", "Health & Medical": "gap_residential",
    "Fitness & Recreation": "gap_residential",
    "Residential": "gap_residential", "Civic & Government": "gap_residential",
    "Religious": "gap_residential", "NGO": "gap_residential",
    "Transport": "gap_industrial", "General": "gap_commercial",
}

# Category slug mapping for hex-level pc_cat_ column lookup
def cat_slug(cat):
    return cat.lower().replace(" & ", "_").replace(" ", "_").replace("&", "_")


def main():
    # Load hex features
    print("Loading hex features...")
    hex_df = pd.read_parquet(HEX_PATH)
    hex_lookup = {}
    for _, row in hex_df.iterrows():
        hex_lookup[row["hex_id"]] = row
    hex_set = set(hex_lookup.keys())
    print(f"  {len(hex_lookup)} hexes loaded")

    # Load micrographs — build place_id → micrograph lookup
    print("Loading micrographs v3...")
    mg_lookup = {}  # place_id → {cv_transit, cv_competitor, ...}
    mg_files = {
        "cafe_micrographs.jsonl", "restaurant_micrographs.jsonl",
        "hawker_micrographs.jsonl", "fast_food_qsr_micrographs.jsonl",
        "bakery_pastry_micrographs.jsonl", "bar_nightlife_micrographs.jsonl",
        "beauty_personal_care_micrographs.jsonl", "health_medical_micrographs.jsonl",
        "fitness_recreation_micrographs.jsonl", "education_micrographs.jsonl",
        "shopping_retail_micrographs.jsonl", "convenience_daily_needs_micrographs.jsonl",
    }
    for fn in mg_files:
        path = os.path.join(MG_DIR, fn)
        if not os.path.exists(path):
            continue
        with open(path) as f:
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
    print(f"  {len(mg_lookup):,} micrographs loaded")

    # Pre-compute per-hex brand counts and per-hex same-category counts
    print("Pre-computing per-hex category/brand stats...")
    hex_cat_count = defaultdict(Counter)  # hex_id → {category: count}
    hex_brand_count = defaultdict(Counter)  # hex_id → {brand: count}
    hex_tier_dist = defaultdict(Counter)  # hex_id → {tier: count}

    with open(PLACES_PATH) as f:
        for ln in f:
            d = json.loads(ln)
            lat, lng = d.get("latitude"), d.get("longitude")
            if lat is None or lng is None:
                continue
            hid = h3.latlng_to_cell(lat, lng, 9)
            if hid not in hex_set:
                continue
            cat = d.get("main_category", "")
            hex_cat_count[hid][cat] += 1
            brand = d.get("brand")
            if brand and brand != "None":
                hex_brand_count[hid][brand] += 1
            tier = d.get("price_tier", "")
            if tier:
                hex_tier_dist[hid][tier] += 1

    # Build place vectors
    print("Building place vectors...")
    rows = []
    n_total = 0
    n_in_hex = 0
    n_with_mg = 0

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
            n_in_hex += 1

            cat = d.get("main_category", "")
            tier = d.get("price_tier", "")
            brand = d.get("brand")
            is_branded = 1 if brand and brand != "None" else 0
            pid = d.get("id", "")
            mg = mg_lookup.get(pid)
            has_mg = 1 if mg else 0
            if has_mg:
                n_with_mg += 1

            hex_row = hex_lookup[hid]

            # ===== LAYER 1: IDENTITY =====
            cat_onehot = [0] * 24
            if cat in CAT_TO_IDX:
                cat_onehot[CAT_TO_IDX[cat]] = 1

            tier_onehot = [0] * 5
            if tier in TIER_TO_IDX:
                tier_onehot[TIER_TO_IDX[tier]] = 1

            # ===== LAYER 2: SPATIAL CONTEXT (micrograph) =====
            if mg:
                cv_t = mg["cv_transit"]
                cv_c = mg["cv_competitor"]
                cv_m = mg["cv_complementary"]
                cv_d = mg["cv_demand"]
                anch = mg["anchor_count"]
                comp = mg["competitive_pressure"]
                ddiv = mg["demand_diversity"]
                walk_mg = mg["walkability_index"]
                band_oh = [0] * 4
                if mg["density_band"] in BAND_TO_IDX:
                    band_oh[BAND_TO_IDX[mg["density_band"]]] = 1
            else:
                cv_t = cv_c = cv_m = cv_d = 0.0
                anch = comp = ddiv = walk_mg = 0.0
                band_oh = [0] * 4

            # ===== LAYER 3: HEX CONTEXT =====
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
            cat_slug_name = cat_slug(cat) if cat else ""
            pc_same_col = f"pc_cat_{cat_slug_name}"
            pc_same = float(hex_row.get(pc_same_col, 0)) if pc_same_col in hex_row.index else 0
            pc_ent = float(hex_row.get("pc_cat_entropy", 0))
            walk_hex = float(hex_row.get("walkability_score", 0))
            mrt = float(hex_row.get("mrt_stations", 0))
            hdb_bl = float(hex_row.get("hdb_blocks", 0))
            bldg_ct = float(hex_row.get("bldg_count", 1))
            hdb_ratio = hdb_bl / bldg_ct if bldg_ct > 0 else 0
            tourist = float(hex_row.get("tourist_draw_est", 0))
            # gap relevant to this category
            gap_col = CAT_TO_GAP.get(cat, "ura_development_gap")
            gap_val = float(hex_row.get(gap_col, 0))

            # ===== LAYER 4: INFLUENCE CONTEXT =====
            sp_max_pc = float(hex_row.get("sp_max_pc_total", 0))
            sp_max_same_col = f"sp_max_pc_cat_{cat_slug_name}"
            sp_max_same = float(hex_row.get(sp_max_same_col, 0)) if sp_max_same_col in hex_row.index else 0
            sp_pw_pc = float(hex_row.get("sp_pw_pc_total", 0))
            tr_max_pc = float(hex_row.get("tr_max_pc_total", 0))
            tr_max_same_col = f"tr_max_pc_cat_{cat_slug_name}"
            tr_max_same = float(hex_row.get(tr_max_same_col, 0)) if tr_max_same_col in hex_row.index else 0
            tr_near = float(hex_row.get("tr_nearest_station_rings", 0))
            tr_reach = float(hex_row.get("tr_reachable_hexes", 0))

            # ===== LAYER 5: COMPETITIVE POSITION =====
            # Tier rank: where does this place sit in the hex's price distribution?
            # 1.0 = most expensive, 0.0 = cheapest
            tier_idx = TIER_TO_IDX.get(tier, 2)  # default to Mid
            hex_tiers = hex_tier_dist.get(hid, Counter())
            total_tiered = sum(hex_tiers.values())
            tiers_above = sum(hex_tiers.get(PRICE_TIERS[i], 0) for i in range(tier_idx))
            tier_rank = tiers_above / total_tiered if total_tiered > 0 else 0.5

            # Brand rarity: if branded, 1/count of this brand in hex. If indie, 0.
            if is_branded and brand:
                brand_count_here = hex_brand_count[hid].get(brand, 1)
                brand_rarity = 1.0 / brand_count_here
            else:
                brand_rarity = 0.0

            # Category share and rank
            total_in_hex = sum(hex_cat_count[hid].values())
            cat_share = hex_cat_count[hid].get(cat, 0) / total_in_hex if total_in_hex > 0 else 0
            # Rank: is this category dominant (1.0) or minor (0.0)?
            sorted_cats = sorted(hex_cat_count[hid].values(), reverse=True)
            my_count = hex_cat_count[hid].get(cat, 0)
            cat_rank = (sorted_cats.index(my_count) / len(sorted_cats)) if my_count in sorted_cats and len(sorted_cats) > 1 else 0.5

            # ===== ASSEMBLE VECTOR =====
            vector = (
                cat_onehot +              # 24
                tier_onehot +             # 5
                [is_branded, has_mg] +    # 2
                [cv_t, cv_c, cv_m, cv_d] + # 4
                [anch, comp, ddiv, walk_mg] + # 4
                band_oh +                 # 4
                [pop_density, pop_total_density, daytime_r, lu_com, lu_res, gpr,
                 pc_tot, pc_same, pc_ent, walk_hex, mrt, hdb_ratio, tourist, gap_val] + # 14
                [sp_max_pc, sp_max_same, sp_pw_pc, tr_max_pc, tr_max_same, tr_near, tr_reach] + # 7
                [tier_rank, brand_rarity, cat_share, cat_rank] # 4
            )

            rows.append({
                "place_id": pid,
                "name": d.get("name", ""),
                "hex_id": hid,
                "main_category": cat,
                "price_tier": tier,
                "brand": brand if brand and brand != "None" else "",
                "latitude": lat,
                "longitude": lng,
                **{f"v{i}": v for i, v in enumerate(vector)},
            })

    print(f"  total places: {n_total:,}")
    print(f"  in hex universe: {n_in_hex:,}")
    print(f"  with micrograph: {n_with_mg:,}")
    print(f"  vector dim: {len(vector)}")

    # Build DataFrame
    out = pd.DataFrame(rows)

    # Separate metadata and vector columns
    meta_cols = ["place_id", "name", "hex_id", "main_category", "price_tier", "brand", "latitude", "longitude"]
    vec_cols = [c for c in out.columns if c.startswith("v")]
    print(f"  output shape: {out.shape} ({len(meta_cols)} meta + {len(vec_cols)} vector)")

    # Save raw
    out.to_parquet(OUT_PATH, index=False)
    print(f"  wrote {OUT_PATH}")

    # Normalize vector columns (sqrt for counts, passthrough for bounded)
    norm = out[meta_cols].copy()
    stats = {}
    for c in vec_cols:
        i = int(c[1:])
        raw = out[c].astype("float64")
        # one-hot and bounded [0,1] features → passthrough
        # counts and unbounded → sqrt
        if i < 31:  # cat_onehot(24) + tier(5) + branded(1) + has_mg(1) = 31
            t = raw
        elif i < 43:  # micrograph cv(4) + nums(4) + band(4) = 12 → all bounded
            t = raw
        elif i < 57:  # hex context (14) — some counts, some bounded
            if i in {43, 44, 49, 55}:  # pop densities, pc_total, tourist → sqrt
                t = np.sqrt(raw.clip(lower=0))
            elif i == 45:  # daytime_ratio → sqrt (can be 0-999)
                t = np.sqrt(raw.clip(lower=0))
            else:
                t = raw  # bounded shares, scores
        elif i < 64:  # influence (7) — counts → sqrt
            if i in {57, 59, 60}:  # sp_max_pc, tr_max_pc → sqrt
                t = np.sqrt(raw.clip(lower=0))
            elif i == 62:  # tr_nearest → passthrough (already bounded)
                t = raw
            elif i == 63:  # tr_reachable → sqrt
                t = np.sqrt(raw.clip(lower=0))
            else:
                t = np.sqrt(raw.clip(lower=0))
        else:  # competitive position (4) — all bounded [0,1]
            t = raw

        t = t.replace([np.inf, -np.inf], np.nan)
        mu = float(t.dropna().mean()) if t.dropna().size else 0
        sd = float(t.dropna().std(ddof=0)) if t.dropna().size else 1
        if sd < 1e-9:
            sd = 1
        norm[c] = ((t - mu) / sd).fillna(0)
        stats[c] = {"dim_index": i, "mu": mu, "sd": sd}

    norm.to_parquet(OUT_NORM, index=False)
    print(f"  wrote {OUT_NORM}")

    # Catalog
    dim_names = (
        [f"cat_{c}" for c in MAIN_CATEGORIES] +  # 0-23
        [f"tier_{t}" for t in PRICE_TIERS] +      # 24-28
        ["is_branded", "has_micrograph"] +         # 29-30
        ["cv_transit", "cv_competitor", "cv_complementary", "cv_demand"] +  # 31-34
        ["anchor_count", "competitive_pressure", "demand_diversity", "walkability_index"] +  # 35-38
        [f"band_{b}" for b in DENSITY_BANDS] +     # 39-42
        ["pop_density", "pop_total_density", "daytime_ratio", "lu_commercial_pct",
         "lu_residential_pct", "avg_gpr", "pc_total", "pc_same_category",
         "pc_cat_entropy", "walkability_score", "mrt_stations", "hdb_ratio",
         "tourist_draw", "gap_for_category"] +    # 43-56
        ["sp_max_pc_total", "sp_max_same_category", "sp_pw_pc_total",
         "tr_max_pc_total", "tr_max_same_category", "tr_nearest_rings",
         "tr_reachable_hexes"] +                  # 57-63
        ["tier_rank_in_hex", "brand_rarity", "category_share", "category_rank"]  # 64-67
    )
    catalog = {
        "vector_dim": len(vector),
        "total_places": n_in_hex,
        "with_micrograph": n_with_mg,
        "layers": {
            "identity": {"dims": "0-30", "count": 31, "features": dim_names[:31]},
            "spatial_context": {"dims": "31-42", "count": 12, "features": dim_names[31:43]},
            "hex_context": {"dims": "43-56", "count": 14, "features": dim_names[43:57]},
            "influence": {"dims": "57-63", "count": 7, "features": dim_names[57:64]},
            "competitive_position": {"dims": "64-67", "count": 4, "features": dim_names[64:68]},
        },
        "dim_names": dim_names,
        "normalization_stats": stats,
    }
    with open(OUT_CATALOG, "w") as f:
        json.dump(catalog, f, indent=2)
    print(f"  wrote {OUT_CATALOG}")

    # Quick sanity
    print()
    print("SANITY CHECKS:")
    # Find two Starbucks in different contexts
    starbucks = out[out["name"].str.contains("Starbucks", case=False, na=False)]
    if len(starbucks) >= 2:
        s1 = starbucks.iloc[0]
        s2 = starbucks.iloc[-1]
        v1 = np.array([s1[c] for c in vec_cols])
        v2 = np.array([s2[c] for c in vec_cols])
        cos = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9)
        print(f"  Starbucks '{s1['name'][:40]}' vs '{s2['name'][:40]}'")
        print(f"  cosine similarity: {cos:.3f} (same brand, different context)")

    # Find most similar place to a random cafe
    cafe = out[out["main_category"] == "Cafe & Coffee"].sample(1, random_state=42).iloc[0]
    cafe_v = np.array([cafe[c] for c in vec_cols])
    all_v = out[vec_cols].to_numpy()
    norms = np.linalg.norm(all_v, axis=1, keepdims=True)
    norms[norms < 1e-9] = 1
    sims = (all_v / norms) @ (cafe_v / (np.linalg.norm(cafe_v) + 1e-9))
    top5 = np.argsort(-sims)[1:6]
    print(f"\n  Nearest to '{cafe['name'][:40]}' ({cafe['hex_id'][:12]}):")
    for idx in top5:
        r = out.iloc[idx]
        print(f"    {r['name'][:35]:<35} cat={r['main_category']:<20} tier={r['price_tier']:<8} sim={sims[idx]:.3f}")


if __name__ == "__main__":
    main()
