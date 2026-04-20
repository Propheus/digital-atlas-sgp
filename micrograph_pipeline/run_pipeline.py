#!/usr/bin/env python3
"""
Digital Atlas SGP — Micrograph Pipeline v3
Builds per-place micro-graphs for all categories.

Steps:
1. Load data (places, MRT, bus stops, hawker centres)
2. Detect anchors (MRT, bus interchanges, hawker centres, malls, schools, HDB)
3. Build dynamic tier mapping per category using COMPETITION_SETS
4. Classify places into tiers
5. Compute density bands
6. Build micro-graphs (star-graph per place)
7. Compute derived scores
8. Output JSONL + slim JSON + per-subzone details + stats

Run: python3 run_pipeline.py [--category cafe] [--limit 100] [--all]
"""
import json, os, sys, time, argparse
import numpy as np
import pandas as pd
import geopandas as gpd
from math import radians, sin, cos, sqrt, atan2, log, exp
from collections import Counter, defaultdict
from scipy.spatial import cKDTree

# ── Import config ──
sys.path.insert(0, os.path.dirname(__file__))
from config import *

def log_msg(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)

import re

def clean_address(addr):
    """Clean address: remove 'Singapore', postal-only junk, plus codes."""
    if not addr:
        return ""
    # Remove plus codes (e.g., "6PH5+XX Singapore")
    addr = re.sub(r'\b[23456789CFGHJMPQRVWX]{4}\+[23456789CFGHJMPQRVWX]{2,3}\b\s*', '', addr)
    # Remove ", Singapore XXXXXX" or "Singapore XXXXXX" at end
    addr = re.sub(r',?\s*Singapore\s*\d*\s*$', '', addr, flags=re.IGNORECASE)
    # Remove standalone "Singapore" anywhere
    addr = re.sub(r'\bSingapore\b', '', addr, flags=re.IGNORECASE)
    # Clean up extra commas, spaces
    addr = re.sub(r'\s*,\s*,\s*', ', ', addr)
    addr = re.sub(r'\s+', ' ', addr).strip().strip(',').strip()
    return addr

def haversine_m(lat1, lon1, lat2, lon2):
    R = EARTH_RADIUS_M
    dlat, dlon = radians(lat2-lat1), radians(lon2-lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

# ============================================================
# STEP 1: LOAD DATA
# ============================================================
def load_places():
    log_msg("Loading places...")
    places = []
    with open(PLACES_FILE) as f:
        for line in f:
            places.append(json.loads(line))
    log_msg("  %d places loaded" % len(places))
    return places

def load_mrt_stations():
    log_msg("Loading MRT stations...")
    mrt = gpd.read_file(MRT_FILE)
    stations = []
    for _, row in mrt.iterrows():
        c = row.geometry.centroid
        if c and not c.is_empty:
            # STN_NAM_DE has full name ("HOUGANG MRT STATION"), STN_NAM is often None
            name = None
            for col in ["STN_NAM_DE", "STN_NAM", "STATION", "NAME"]:
                if col in mrt.columns and row.get(col):
                    name = str(row[col]).strip()
                    # Clean up: "HOUGANG MRT STATION" -> "Hougang"
                    name = name.replace(" MRT STATION", "").replace(" LRT STATION", "").title()
                    break
            if not name:
                name = "MRT Station"
            stn_type = str(row.get("TYP_CD_DES", "")).upper()
            if "LRT" in stn_type:
                atype = "mrt_minor"
            else:
                atype = "mrt_standard"
            stations.append({
                "anchor_id": "mrt_%d" % len(stations),
                "name": name,
                "anchor_type": atype,
                "latitude": c.y,
                "longitude": c.x,
                "radius_m": ANCHOR_SCALE[atype]["radius_m"],
                "daily_flow": ANCHOR_FLOW_TIERS[atype],
                "directional": True,
            })
    log_msg("  %d MRT stations (%d LRT)" % (len(stations), sum(1 for s in stations if s["anchor_type"]=="mrt_minor")))
    return stations

def load_bus_interchanges():
    """Load bus stops and filter for interchanges/terminals only."""
    log_msg("Loading bus interchanges...")
    if not os.path.exists(BUS_FILE):
        log_msg("  SKIP: bus file not found")
        return []
    bus = gpd.read_file(BUS_FILE)
    interchanges = []
    for _, row in bus.iterrows():
        c = row.geometry
        if c is None or c.is_empty:
            continue
        pt = c.centroid if c.geom_type != "Point" else c
        desc = str(row.get("LOC_DESC", "")).upper()
        # Only keep interchanges and terminals
        if any(kw in desc for kw in BUS_INTERCHANGE_KEYWORDS):
            interchanges.append({
                "anchor_id": "bus_%s" % row.get("BUS_STOP_N", len(interchanges)),
                "name": row.get("LOC_DESC", "Bus Interchange"),
                "anchor_type": "bus_interchange",
                "latitude": pt.y,
                "longitude": pt.x,
                "radius_m": ANCHOR_SCALE["bus_interchange"]["radius_m"],
                "daily_flow": ANCHOR_FLOW_TIERS["bus_interchange"],
                "directional": True,
            })
    log_msg("  %d bus interchanges (of %d total stops)" % (len(interchanges), len(bus)))
    return interchanges

def load_hawker_centres():
    log_msg("Loading hawker centres...")
    if not os.path.exists(HAWKER_FILE):
        log_msg("  SKIP: hawker file not found")
        return []
    hc = gpd.read_file(HAWKER_FILE)
    centres = []
    for _, row in hc.iterrows():
        c = row.geometry
        if c and not c.is_empty:
            pt = c.centroid if c.geom_type != "Point" else c
            name = row.get("ADDRESSBUILDINGNAME") or row.get("NAME") or row.get("Name") or "Hawker Centre"
            centres.append({
                "anchor_id": "hawker_%d" % len(centres),
                "name": name,
                "anchor_type": "hawker_centre",
                "latitude": pt.y,
                "longitude": pt.x,
                "radius_m": ANCHOR_SCALE["hawker_centre"]["radius_m"],
                "daily_flow": ANCHOR_FLOW_TIERS["hawker_centre"],
                "directional": False,
            })
    log_msg("  %d hawker centres" % len(centres))
    return centres

# ============================================================
# STEP 2: SPATIAL INDEX
# ============================================================
class SpatialIndex:
    def __init__(self, ids, lats, lons, records=None):
        self.ids = np.array(ids)
        self.lats = np.array(lats, dtype=np.float64)
        self.lons = np.array(lons, dtype=np.float64)
        self.records = records or [None] * len(ids)

        self.x = self.lons * M_PER_DEG_LNG
        self.y = self.lats * M_PER_DEG_LAT
        self.tree = cKDTree(np.column_stack([self.x, self.y]))

    def query_radius(self, lat, lon, radius_m):
        x = lon * M_PER_DEG_LNG
        y = lat * M_PER_DEG_LAT
        idxs = self.tree.query_ball_point([x, y], radius_m)
        results = []
        for i in idxs:
            d = haversine_m(lat, lon, self.lats[i], self.lons[i])
            if d <= radius_m:
                results.append((i, d))
        results.sort(key=lambda x: x[1])
        return results

    def get_record(self, idx):
        return self.records[idx]

# ============================================================
# STEP 3: DETECT ANCHORS
# ============================================================
def detect_anchors(places, mrt_stations, hawker_centres, bus_interchanges):
    log_msg("Detecting anchors from places...")
    anchors = list(mrt_stations) + list(hawker_centres) + list(bus_interchanges)

    for p in places:
        pt = p.get("place_type", "")
        reviews = p.get("review_count", 0) or 0
        name = p.get("name", "")

        # Shopping malls
        if pt == "Shopping Mall" and reviews >= 50:
            anchors.append({
                "anchor_id": "mall_%s" % p["id"],
                "name": name, "anchor_type": "shopping_mall",
                "latitude": p["latitude"], "longitude": p["longitude"],
                "radius_m": ANCHOR_SCALE["shopping_mall"]["radius_m"],
                "daily_flow": ANCHOR_FLOW_TIERS["shopping_mall"],
                "directional": False, "reviews": reviews,
            })

        # Supermarkets
        elif pt == "Supermarket" and reviews >= 30:
            anchors.append({
                "anchor_id": "super_%s" % p["id"],
                "name": name, "anchor_type": "supermarket",
                "latitude": p["latitude"], "longitude": p["longitude"],
                "radius_m": ANCHOR_SCALE["supermarket"]["radius_m"],
                "daily_flow": ANCHOR_FLOW_TIERS["supermarket"],
                "directional": False, "reviews": reviews,
            })

        # Hospitals
        elif pt == "Hospital" and reviews >= 30:
            anchors.append({
                "anchor_id": "hosp_%s" % p["id"],
                "name": name, "anchor_type": "hospital",
                "latitude": p["latitude"], "longitude": p["longitude"],
                "radius_m": ANCHOR_SCALE["hospital"]["radius_m"],
                "daily_flow": ANCHOR_FLOW_TIERS["hospital"],
                "directional": False, "reviews": reviews,
            })

        # Universities
        elif pt == "University" and reviews >= 20:
            anchors.append({
                "anchor_id": "uni_%s" % p["id"],
                "name": name, "anchor_type": "university",
                "latitude": p["latitude"], "longitude": p["longitude"],
                "radius_m": ANCHOR_SCALE["university"]["radius_m"],
                "daily_flow": ANCHOR_FLOW_TIERS["university"],
                "directional": False, "reviews": reviews,
            })

        # Schools (primary, secondary, international)
        elif pt in ("Primary School", "Secondary School", "International School") and reviews >= 10:
            anchors.append({
                "anchor_id": "school_%s" % p["id"],
                "name": name, "anchor_type": "school",
                "latitude": p["latitude"], "longitude": p["longitude"],
                "radius_m": ANCHOR_SCALE["school"]["radius_m"],
                "daily_flow": ANCHOR_FLOW_TIERS["school"],
                "directional": False, "reviews": reviews,
            })

        # HDB blocks (residential clusters) — use HDB places with any reviews
        elif pt == "HDB" and reviews >= 5:
            anchors.append({
                "anchor_id": "hdb_%s" % p["id"],
                "name": name, "anchor_type": "hdb_cluster",
                "latitude": p["latitude"], "longitude": p["longitude"],
                "radius_m": ANCHOR_SCALE["hdb_cluster"]["radius_m"],
                "daily_flow": ANCHOR_FLOW_TIERS["hdb_cluster"],
                "directional": False, "reviews": reviews,
            })

        # Office buildings/clusters
        elif pt in ("Office", "Office Building") and reviews >= 20:
            anchors.append({
                "anchor_id": "office_%s" % p["id"],
                "name": name, "anchor_type": "office_cluster",
                "latitude": p["latitude"], "longitude": p["longitude"],
                "radius_m": ANCHOR_SCALE["office_cluster"]["radius_m"],
                "daily_flow": ANCHOR_FLOW_TIERS["office_cluster"],
                "directional": False, "reviews": reviews,
            })

    log_msg("  Total anchors: %d" % len(anchors))
    by_type = Counter(a["anchor_type"] for a in anchors)
    for t, c in by_type.most_common():
        log_msg("    %s: %d" % (t, c))

    return anchors

# ============================================================
# STEP 4: CLASSIFY PLACES INTO TIERS (DYNAMIC)
# ============================================================
def classify_places(places, category):
    """Classify each place into tier 1-4 or None using dynamic tier mapping."""
    log_msg("Classifying places for '%s' pipeline (dynamic)..." % category)

    tier_mapping = build_tier_mapping(category)

    tiers = []
    for p in places:
        brand = p.get("brand")
        pt = p.get("place_type", "")

        # Brand override first
        brand_tier = get_brand_tier(brand, category) if brand else None
        if brand_tier is not None:
            tiers.append(brand_tier)
            continue

        # Place type mapping
        if pt in tier_mapping:
            tiers.append(tier_mapping[pt])
            continue

        # Main category fallback for demand magnets
        mc = p.get("main_category", "")
        if mc in ("Office & Workspace", "Business"):
            tiers.append(4)
        elif mc in ("Education",):
            tiers.append(4)
        elif mc in ("Residential",):
            tiers.append(4)
        elif mc in ("Shopping & Retail",):
            tiers.append(4)
        elif mc in ("Civic & Government",):
            tiers.append(4)
        elif mc in ("Hospitality",):
            tiers.append(4)
        else:
            tiers.append(None)

    counts = Counter(t for t in tiers if t is not None)
    excluded = sum(1 for t in tiers if t is None)
    log_msg("  T2 (competitors): %d, T3 (complementary): %d, T4 (demand): %d, excluded: %d" %
            (counts.get(2, 0), counts.get(3, 0), counts.get(4, 0), excluded))

    return tiers

# ============================================================
# STEP 5: COMPUTE DENSITY BANDS
# ============================================================
def compute_density_bands(places, place_index):
    log_msg("Computing density bands...")
    bands = []
    for p in places:
        nearby = place_index.query_radius(p["latitude"], p["longitude"], 200)
        count = len(nearby)
        if count >= DENSITY_THRESHOLDS["hyperdense"]:
            bands.append("hyperdense")
        elif count >= DENSITY_THRESHOLDS["dense"]:
            bands.append("dense")
        elif count >= DENSITY_THRESHOLDS["moderate"]:
            bands.append("moderate")
        else:
            bands.append("sparse")

    band_counts = Counter(bands)
    for b in ["hyperdense", "dense", "moderate", "sparse"]:
        log_msg("  %s: %d" % (b, band_counts.get(b, 0)))

    return bands

# ============================================================
# STEP 6: SIGMOID DECAY
# ============================================================
def sigmoid_decay(walk_time_s, budget_s):
    t_half = SIGMOID_T_HALF_RATIO * budget_s
    return 1.0 / (1.0 + exp((walk_time_s - t_half) / SIGMOID_STEEPNESS))

# ============================================================
# STEP 7: BUILD MICRO-GRAPH PER PLACE
# ============================================================
def build_micro_graph(target_place, target_idx, density_band,
                      places, tiers, place_index,
                      anchors, anchor_index,
                      target_category="cafe"):
    """Build star-graph for one target place."""

    budgets = TIER_BUDGETS[density_band]
    quotas = TIER_QUOTAS
    max_budget = max(budgets.values())

    max_radius_m = max_budget * OSM_WALK_SPEED_MS

    # Find nearby places
    nearby_places = place_index.query_radius(
        target_place["latitude"], target_place["longitude"], min(max_radius_m, MAX_SEARCH_RADIUS_M))

    # Find nearby anchors
    nearby_anchors = anchor_index.query_radius(
        target_place["latitude"], target_place["longitude"], ANCHOR_SEARCH_RADIUS_M)

    selected = {1: [], 2: [], 3: [], 4: []}
    eligible_counts = {1: 0, 2: 0, 3: 0, 4: 0}

    # T1: Anchors (MRT, bus interchanges, hawker centres, malls...)
    for idx, dist_m in nearby_anchors:
        anchor = anchor_index.get_record(idx)
        if dist_m > anchor.get("radius_m", 300):
            continue
        walk_time = dist_m / OSM_WALK_SPEED_MS
        if walk_time > budgets.get(1, 600):
            continue

        eligible_counts[1] += 1
        if len(selected[1]) >= quotas[1]["max"]:
            continue

        decay = sigmoid_decay(walk_time, budgets[1])
        flow = anchor.get("daily_flow", 1000)
        magnitude = log(1 + flow) * 0.8
        raw_weight = decay * TIER_IMPORTANCE[1] * magnitude

        selected[1].append({
            "anchor_id": anchor["anchor_id"],
            "name": anchor["name"],
            "anchor_type": anchor.get("anchor_type", "unknown"),
            "latitude": anchor["latitude"],
            "longitude": anchor["longitude"],
            "tier": 1,
            "distance_m": round(dist_m, 1),
            "walk_time_s": round(walk_time, 1),
            "decay": round(decay, 4),
            "magnitude": round(magnitude, 3),
            "raw_weight": round(raw_weight, 4),
            "daily_flow": flow,
        })

    # Build set of T1 anchor locations for deduplication
    t1_locs = set()
    for a in selected[1]:
        t1_locs.add((round(a["latitude"], 5), round(a["longitude"], 5)))

    # T2, T3, T4: Places
    for idx, dist_m in nearby_places:
        if idx == target_idx:
            continue
        tier = tiers[idx]
        if tier is None or tier == 1:
            continue

        p = places[idx]
        reviews = p.get("review_count", 0) or 0
        rating = p.get("rating", 0) or 0

        # Skip T4 places that duplicate a T1 anchor (same location)
        if tier == 4:
            p_loc = (round(p["latitude"], 5), round(p["longitude"], 5))
            if p_loc in t1_locs:
                continue

        if reviews < MIN_REVIEWS and tier != 4:
            continue

        walk_time = dist_m / OSM_WALK_SPEED_MS
        if walk_time > budgets.get(tier, 600):
            continue

        # Skip same brand for T2
        if tier == 2 and target_place.get("brand") and p.get("brand") == target_place.get("brand"):
            continue

        eligible_counts[tier] += 1
        if len(selected[tier]) >= quotas[tier]["max"]:
            continue

        decay = sigmoid_decay(walk_time, budgets[tier])
        magnitude = log(1 + reviews) * (rating / 5.0) if reviews > 0 and rating > 0 else 0.1
        raw_weight = decay * TIER_IMPORTANCE[tier] * magnitude

        # Higher minimum weight for T4 to filter noise
        min_w = EDGE_WEIGHT_MIN * 3 if tier == 4 else EDGE_WEIGHT_MIN
        if raw_weight < min_w:
            continue

        selected[tier].append({
            "place_id": p["id"],
            "name": p["name"],
            "place_type": p.get("place_type", ""),
            "brand": p.get("brand"),
            "latitude": p["latitude"],
            "longitude": p["longitude"],
            "tier": tier,
            "distance_m": round(dist_m, 1),
            "walk_time_s": round(walk_time, 1),
            "decay": round(decay, 4),
            "magnitude": round(magnitude, 3),
            "raw_weight": round(raw_weight, 4),
            "reviews": reviews,
            "rating": rating,
        })

    # Sort T2 by strategy
    strategy = T2_SELECTION.get(density_band, "walktime")
    if strategy == "magnitude":
        selected[2].sort(key=lambda x: -x["raw_weight"])
    else:
        selected[2].sort(key=lambda x: x["walk_time_s"])

    # Merge all anchors
    all_anchors = (selected[1] +
                   selected[2][:quotas[2]["max"]] +
                   selected[3][:quotas[3]["max"]] +
                   selected[4][:quotas[4]["max"]])

    # Hard cap
    if len(all_anchors) > TOTAL_MAX_ANCHORS:
        all_anchors.sort(key=lambda x: -x["raw_weight"])
        all_anchors = all_anchors[:TOTAL_MAX_ANCHORS]

    # L1 normalize
    total_weight = sum(a["raw_weight"] for a in all_anchors)
    for a in all_anchors:
        a["normalized_weight"] = round(a["raw_weight"] / total_weight, 4) if total_weight > 0 else 0

    all_anchors.sort(key=lambda x: -x["normalized_weight"])

    return {
        "place_id": target_place["id"],
        "name": target_place["name"],
        "brand": target_place.get("brand"),
        "address": clean_address(target_place.get("address", "")),
        "place_type": target_place.get("place_type", ""),
        "latitude": target_place["latitude"],
        "longitude": target_place["longitude"],
        "subzone": target_place.get("subzone", ""),
        "subzone_code": target_place.get("subzone_code", ""),
        "density_band": density_band,
        "anchor_count": len(all_anchors),
        "anchors": all_anchors,
        "eligible_counts": eligible_counts,
    }

# ============================================================
# STEP 8: DERIVED SCORES
# ============================================================
def compute_derived_scores(result):
    anchors = result.get("anchors", [])
    if not anchors:
        result["context_vector"] = {"transit": 0, "competitor": 0, "complementary": 0, "demand": 0}
        result["transit_access"] = 0
        result["competitive_pressure"] = 0
        result["competitor_count"] = 0
        result["demand_diversity"] = 0
        result["fnb_density"] = 0
        result["walkability_index"] = 0
        result["has_gaps"] = True
        result["gap_tiers"] = [1, 2, 3, 4]
        return

    cv = {"transit": 0, "competitor": 0, "complementary": 0, "demand": 0}
    tier_map = {1: "transit", 2: "competitor", 3: "complementary", 4: "demand"}
    for a in anchors:
        cv[tier_map.get(a["tier"], "demand")] += a.get("normalized_weight", 0)
    result["context_vector"] = {k: round(v, 4) for k, v in cv.items()}

    t1 = [a for a in anchors if a["tier"] == 1]
    result["transit_access"] = round(max((a["normalized_weight"] for a in t1), default=0), 4)

    t2 = [a for a in anchors if a["tier"] == 2]
    result["competitive_pressure"] = round(np.mean([a["normalized_weight"] for a in t2]), 4) if t2 else 0
    result["competitor_count"] = len(t2)

    t4_cats = [a.get("place_type", a.get("anchor_type", "")) for a in anchors if a["tier"] == 4]
    if t4_cats:
        cat_counts = Counter(t4_cats)
        total = len(t4_cats)
        probs = [c / total for c in cat_counts.values()]
        result["demand_diversity"] = round(-sum(p * log(p) for p in probs if p > 0), 3)
    else:
        result["demand_diversity"] = 0

    result["fnb_density"] = len([a for a in anchors if a["tier"] == 3])

    walk_times = [a["walk_time_s"] for a in anchors]
    result["walkability_index"] = round(np.mean(walk_times), 1) if walk_times else 0

    gaps = {}
    tier_counts = Counter(a["tier"] for a in anchors)
    for tier, quota in TIER_QUOTAS.items():
        if tier_counts.get(tier, 0) < quota["min"]:
            gaps[tier] = True
    result["has_gaps"] = len(gaps) > 0
    result["gap_tiers"] = list(gaps.keys())

# ============================================================
# STEP 9: OUTPUT
# ============================================================
def write_outputs(results, category, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    # JSONL
    jsonl_path = os.path.join(output_dir, "%s_micrographs.jsonl" % category)
    with open(jsonl_path, "w") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    log_msg("  JSONL: %s (%.1f MB)" % (jsonl_path, os.path.getsize(jsonl_path) / 1048576))

    # Slim (for frontend) — 13 elements matching app's expected format
    # [0:id, 1:name, 2:brand, 3:lat, 4:lon, 5:density_band_short, 6:anchor_count,
    #  7:transit_cv, 8:competitor_cv, 9:complementary_cv, 10:demand_cv,
    #  11:competitive_pressure (None placeholder), 12:subzone_code]
    BAND_SHORT = {"hyperdense": "hd", "dense": "de", "moderate": "mo", "sparse": "sp"}
    slim = []
    for r in results:
        slim.append([
            r["place_id"], r["name"], r.get("brand"),
            r["latitude"], r["longitude"],
            BAND_SHORT.get(r["density_band"], r["density_band"][:2]),
            r["anchor_count"],
            r.get("context_vector", {}).get("transit", 0),
            r.get("context_vector", {}).get("competitor", 0),
            r.get("context_vector", {}).get("complementary", 0),
            r.get("context_vector", {}).get("demand", 0),
            None,
            r.get("subzone_code", ""),
        ])
    slim_path = os.path.join(output_dir, "%s_slim.json" % category)
    with open(slim_path, "w") as f:
        json.dump(slim, f, separators=(",", ":"))
    log_msg("  Slim: %s (%.1f KB)" % (slim_path, os.path.getsize(slim_path) / 1024))

    # Per-subzone detail files — keyed by subzone_code (e.g., AMSZ01.json)
    detail_dir = os.path.join(output_dir, "%s_details" % category)
    os.makedirs(detail_dir, exist_ok=True)
    by_subzone = defaultdict(list)
    for r in results:
        sz_code = r.get("subzone_code") or r.get("subzone", "unknown")
        by_subzone[sz_code].append(r)
    for sz_code, items in by_subzone.items():
        with open(os.path.join(detail_dir, "%s.json" % sz_code), "w") as f:
            json.dump(items, f, ensure_ascii=False, indent=1)
    log_msg("  Details: %d subzone files" % len(by_subzone))

    # Stats
    stats = {
        "category": category,
        "total": len(results),
        "density_bands": dict(Counter(r["density_band"] for r in results)),
        "anchor_count_mean": round(np.mean([r["anchor_count"] for r in results]), 1),
        "anchor_count_min": min(r["anchor_count"] for r in results),
        "anchor_count_max": max(r["anchor_count"] for r in results),
        "with_gaps": sum(1 for r in results if r.get("has_gaps")),
        "tier_distribution": {
            "T1_transit": sum(1 for r in results for a in r.get("anchors", []) if a["tier"] == 1),
            "T2_competitor": sum(1 for r in results for a in r.get("anchors", []) if a["tier"] == 2),
            "T3_complementary": sum(1 for r in results for a in r.get("anchors", []) if a["tier"] == 3),
            "T4_demand": sum(1 for r in results for a in r.get("anchors", []) if a["tier"] == 4),
        },
        "mean_context_vector": {
            "transit": round(np.mean([r.get("context_vector", {}).get("transit", 0) for r in results]), 4),
            "competitor": round(np.mean([r.get("context_vector", {}).get("competitor", 0) for r in results]), 4),
            "complementary": round(np.mean([r.get("context_vector", {}).get("complementary", 0) for r in results]), 4),
            "demand": round(np.mean([r.get("context_vector", {}).get("demand", 0) for r in results]), 4),
        },
        "branded": sum(1 for r in results if r.get("brand")),
        "independent": sum(1 for r in results if not r.get("brand")),
    }
    stats_path = os.path.join(output_dir, "%s_stats.json" % category)
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    log_msg("  Stats: %s" % stats_path)

# ============================================================
# VALIDATION
# ============================================================
def validate_results(results, category):
    log_msg("\n--- VALIDATION: %s ---" % category)
    tests = []

    n = len(results)
    tests.append(("result count > 0", n > 0, "%d" % n))

    anchored = sum(1 for r in results if r["anchor_count"] > 0)
    tests.append(("most have anchors", anchored / max(n, 1) > 0.5, "%d/%d (%.0f%%)" % (anchored, n, anchored/max(n,1)*100)))

    cvs = [r.get("context_vector", {}) for r in results if r.get("context_vector")]
    if cvs:
        avg_sum = np.mean([sum(cv.values()) for cv in cvs])
        tests.append(("context vectors sum ~1", 0.8 < avg_sum < 1.2, "avg_sum=%.3f" % avg_sum))

    bands = Counter(r["density_band"] for r in results)
    tests.append(("multiple density bands", len(bands) >= 2, "%d bands" % len(bands)))

    walk_times = [a["walk_time_s"] for r in results for a in r.get("anchors", [])]
    if walk_times:
        tests.append(("walk times positive", min(walk_times) >= 0, "min=%.0f" % min(walk_times)))
        tests.append(("walk times reasonable", max(walk_times) < 1200, "max=%.0f" % max(walk_times)))

    # Check tier distribution
    tier_counts = Counter(a["tier"] for r in results for a in r.get("anchors", []))
    tests.append(("T2 competitors exist", tier_counts.get(2, 0) > 0, "T2=%d" % tier_counts.get(2, 0)))
    tests.append(("T2 > T3", tier_counts.get(2, 0) >= tier_counts.get(3, 0),
                  "T2=%d, T3=%d" % (tier_counts.get(2, 0), tier_counts.get(3, 0))))

    all_pass = True
    for name, passed, detail in tests:
        status = "PASS" if passed else "FAIL"
        log_msg("  [%s] %s %s" % (status, name, detail))
        if not passed:
            all_pass = False

    return all_pass

# ============================================================
# MAIN
# ============================================================
def run_category(category, places, mrt_stations, hawker_centres, bus_interchanges,
                 anchors, anchor_index, place_index, bands, limit=0):
    """Run pipeline for a single category."""
    log_msg("\n" + "=" * 60)
    log_msg("CATEGORY: %s" % category)
    log_msg("=" * 60)

    # Classify places for this category
    tiers = classify_places(places, category)

    # Identify target places
    target_types = CATEGORY_TARGETS.get(category, set())
    if not target_types:
        log_msg("  WARNING: No target types defined for '%s', skipping" % category)
        return []

    targets = [(i, p) for i, p in enumerate(places)
               if p.get("place_type") in target_types]

    # Fallback: also match by main_category if place_type didn't match
    if not targets:
        mc_key = category.replace("_", " ").title().replace(" And ", " & ")
        targets = [(i, p) for i, p in enumerate(places)
                   if p.get("main_category", "") == mc_key]

    if limit > 0:
        targets = targets[:limit]

    log_msg("Target places: %d (of %d total)" % (len(targets), len(places)))

    if not targets:
        log_msg("  WARNING: No targets found for '%s', skipping" % category)
        return []

    # Build micro-graphs
    log_msg("Building micro-graphs...")
    results = []
    t0 = time.time()

    for idx, (place_idx, place) in enumerate(targets):
        result = build_micro_graph(
            place, place_idx, bands[place_idx],
            places, tiers, place_index,
            anchors, anchor_index,
            category,
        )
        compute_derived_scores(result)
        results.append(result)

        if (idx + 1) % 500 == 0:
            elapsed = time.time() - t0
            rate = (idx + 1) / elapsed
            eta = (len(targets) - idx - 1) / rate / 60
            log_msg("  %d/%d (%.0f/s, ETA %.1fm)" % (idx + 1, len(targets), rate, eta))

    elapsed = time.time() - t0
    log_msg("  Done: %d micro-graphs in %.1fs (%.0f/s)" % (len(results), elapsed, len(results)/max(elapsed,1)))

    # Validate
    ok = validate_results(results, category)

    # Write output
    log_msg("Writing outputs...")
    write_outputs(results, category, OUTPUT_DIR)

    log_msg("PIPELINE COMPLETE: %s — %d places, validation: %s" %
            (category, len(results), "PASSED" if ok else "SOME FAILED"))

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", default="cafe", help="Category pipeline to run")
    parser.add_argument("--limit", type=int, default=0, help="Limit target places (0=all)")
    parser.add_argument("--all", action="store_true", help="Run all categories")
    args = parser.parse_args()

    log_msg("=" * 60)
    log_msg("DIGITAL ATLAS SGP — MICROGRAPH PIPELINE v3")
    log_msg("=" * 60)

    # Load data (shared across all categories)
    places = load_places()
    mrt_stations = load_mrt_stations()
    hawker_centres = load_hawker_centres()
    bus_interchanges = load_bus_interchanges()

    # Detect anchors
    anchors = detect_anchors(places, mrt_stations, hawker_centres, bus_interchanges)

    # Build spatial indices (shared)
    log_msg("Building spatial indices...")
    place_index = SpatialIndex(
        ids=list(range(len(places))),
        lats=[p["latitude"] for p in places],
        lons=[p["longitude"] for p in places],
        records=places,
    )
    anchor_index = SpatialIndex(
        ids=list(range(len(anchors))),
        lats=[a["latitude"] for a in anchors],
        lons=[a["longitude"] for a in anchors],
        records=anchors,
    )
    log_msg("  Place index: %d, Anchor index: %d" % (len(places), len(anchors)))

    # Compute density bands (shared)
    bands = compute_density_bands(places, place_index)

    # Run categories
    if args.all:
        categories = list(CATEGORY_TARGETS.keys())
        log_msg("\nRunning ALL %d categories: %s" % (len(categories), ", ".join(categories)))
    else:
        categories = [args.category]

    all_results = {}
    for cat in categories:
        results = run_category(
            cat, places, mrt_stations, hawker_centres, bus_interchanges,
            anchors, anchor_index, place_index, bands, args.limit,
        )
        all_results[cat] = results

    # Summary
    log_msg("\n" + "=" * 60)
    log_msg("ALL PIPELINES COMPLETE")
    log_msg("=" * 60)
    total_places = 0
    for cat, results in all_results.items():
        n = len(results)
        total_places += n
        avg_anchors = np.mean([r["anchor_count"] for r in results]) if results else 0
        log_msg("  %-25s %5d places, avg %.1f anchors" % (cat, n, avg_anchors))
    log_msg("  TOTAL: %d place micrographs" % total_places)
    log_msg("=" * 60)


if __name__ == "__main__":
    main()
