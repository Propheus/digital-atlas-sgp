#!/usr/bin/env python3
"""
Digital Atlas SGP — Data Composer
Transforms raw SGP data into frontend-ready JSON files.

Output:
  public/data/subzone_profiles.json    — 332 subzone profiles (equivalent to tract_profiles)
  public/data/subzones_geo.geojson     — Subzone boundaries for choropleth
  public/data/places_slim.json         — All 66K places as compact tuples
  public/data/summary_stats.json       — Global statistics
  public/data/category_stats.json      — Per-category statistics
  public/data/brands.json              — Brand registry
  public/data/mrt_lines.geojson        — MRT network for overlay
"""
import json, os, sys
import pandas as pd
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "app", "public", "data")
os.makedirs(OUT, exist_ok=True)

def log(msg):
    print("[compose] %s" % msg, flush=True)

# ============================================================
# 1. SUBZONE PROFILES
# ============================================================
def compose_subzone_profiles():
    log("Building subzone profiles...")

    sf = pd.read_parquet(os.path.join(BASE, "model", "features", "subzone_features_raw.parquet"))

    # Also load gap analysis
    gap_path = os.path.join(BASE, "model", "results", "gap_analysis_v5.parquet")
    gaps = pd.read_parquet(gap_path) if os.path.exists(gap_path) else None

    profiles = {}
    for _, row in sf.iterrows():
        code = row.get("subzone_code", "")
        if not code:
            continue

        p = {}
        # Core identity
        p["subzone_name"] = row.get("subzone_name", "")
        p["planning_area"] = row.get("planning_area", "")
        p["area_km2"] = round(row.get("area_km2", 0), 3)

        # Demographics
        p["population"] = int(row.get("total_population", 0))
        p["pop_density"] = round(row.get("pop_density", 0), 0)
        p["elderly_pct"] = round(row.get("age_65_plus_pct", 0), 1)
        p["male_pct"] = round(row.get("male_pct", 0), 1)

        # Dwelling
        for col in sf.columns:
            if col.endswith("_pct") and any(w in col for w in ["HDB", "Condo", "Landed"]):
                key = col.replace(" ", "_").replace("-", "_").replace("(", "").replace(")", "").lower()
                p[key] = round(row.get(col, 0), 1)

        # Property
        p["median_hdb_psf"] = round(row.get("median_hdb_psf", 0), 0) if pd.notna(row.get("median_hdb_psf")) else None
        p["hdb_price_yoy"] = round(row.get("hdb_price_yoy_pct", 0), 1) if pd.notna(row.get("hdb_price_yoy_pct")) else None

        # Roads
        p["road_density"] = round(row.get("road_density_km_per_km2", 0), 1)
        p["total_road_km"] = round(row.get("total_road_length_km", 0), 1)

        # Land use
        for col in sf.columns:
            if col.startswith("lu_") and col.endswith("_pct"):
                p[col] = round(row.get(col, 0), 1)
        p["avg_gpr"] = round(row.get("avg_gpr", 0), 2) if pd.notna(row.get("avg_gpr")) else None
        p["lu_entropy"] = round(row.get("lu_entropy", 0), 3)
        p["green_ratio"] = round(row.get("green_ratio", 0), 3)

        # Transit
        p["dist_nearest_mrt"] = round(row.get("dist_nearest_mrt", 99999), 0)
        p["mrt_stations_1km"] = int(row.get("mrt_stations_1km", 0))
        p["bus_stop_count_1km"] = int(row.get("bus_stop_count_1km", 0))
        p["bus_density"] = round(row.get("bus_density_per_km2", 0), 1)

        # Amenities
        for col in ["dist_nearest_park", "parks_within_1km", "dist_nearest_hawker",
                     "hawkers_within_1km", "dist_nearest_supermarket", "supermarkets_within_1km",
                     "dist_nearest_school", "schools_within_1km", "hotel_count_1km"]:
            if col in sf.columns:
                val = row.get(col, 0)
                p[col] = round(val, 0) if pd.notna(val) else 0

        # Places
        p["total_places"] = int(row.get("total_place_count", 0)) if pd.notna(row.get("total_place_count")) else 0
        p["place_density"] = round(row.get("place_density_per_km2", 0), 0) if pd.notna(row.get("place_density_per_km2")) else 0
        p["category_entropy"] = round(row.get("category_entropy", 0), 3) if pd.notna(row.get("category_entropy")) else 0

        # Category counts
        for col in sf.columns:
            if col.startswith("cat_") and not col.endswith("_pct"):
                key = col.replace("cat_", "n_")
                p[key] = int(row.get(col, 0)) if pd.notna(row.get(col)) else 0

        # Brand quality
        for col in ["branded_count", "branded_pct", "unique_brand_count",
                     "avg_rating", "median_rating", "high_rated_pct", "total_reviews"]:
            if col in sf.columns:
                val = row.get(col, 0)
                p[col] = round(val, 2) if pd.notna(val) else 0

        # Validation
        for col in ["sfa_eating_count", "chas_clinic_count", "preschool_count_gov",
                     "our_place_count", "fnb_coverage_ratio"]:
            if col in sf.columns:
                val = row.get(col, 0)
                p[col] = round(val, 2) if pd.notna(val) else 0

        # Gap scores (from model)
        if gaps is not None:
            gap_row = gaps[gaps["subzone_code"] == code]
            if len(gap_row) > 0:
                gr = gap_row.iloc[0]
                p["predicted_total"] = round(gr.get("predicted_total", 0), 0) if pd.notna(gr.get("predicted_total")) else 0
                p["density_gap"] = round(p["predicted_total"] - p["total_places"], 0)

                for col in gaps.columns:
                    if col.startswith("gap_score_"):
                        cat = col.replace("gap_score_", "")
                        val = gr.get(col, 0)
                        p["gap_" + cat] = round(val, 3) if pd.notna(val) else 0

        profiles[code] = p

    outpath = os.path.join(OUT, "subzone_profiles.json")
    with open(outpath, "w") as f:
        json.dump(profiles, f, separators=(",", ":"))
    log("  Saved %d profiles (%.1f MB)" % (len(profiles), os.path.getsize(outpath)/1048576))
    return profiles


# ============================================================
# 2. SUBZONE BOUNDARIES (simplified for frontend)
# ============================================================
def compose_subzone_geo():
    log("Building subzone GeoJSON...")

    import geopandas as gpd
    sz = gpd.read_file(os.path.join(DATA, "boundaries", "subzones.geojson"))

    # Simplify geometry for faster rendering
    sz_simple = sz.to_crs(epsg=3414)
    sz_simple["geometry"] = sz_simple.geometry.simplify(tolerance=20)
    sz_simple = sz_simple.to_crs(epsg=4326)

    # Keep minimal properties
    sz_out = sz_simple[["SUBZONE_C", "SUBZONE_N", "PLN_AREA_N", "REGION_N", "geometry"]].copy()
    sz_out.columns = ["id", "name", "planning_area", "region", "geometry"]

    outpath = os.path.join(OUT, "subzones_geo.geojson")
    sz_out.to_file(outpath, driver="GeoJSON")
    log("  Saved %d subzones (%.1f MB)" % (len(sz_out), os.path.getsize(outpath)/1048576))


# ============================================================
# 3. PLACES SLIM (compact array-of-tuples)
# ============================================================
def compose_places_slim():
    log("Building places slim...")

    places = []
    with open(os.path.join(DATA, "places", "sgp_places.jsonl")) as f:
        for line in f:
            places.append(json.loads(line))

    # Tuple format: [id, name, brand, lat, lon, main_category, place_type, rating, review_count, subzone_code]
    slim = []
    for p in places:
        slim.append([
            p["id"],
            p["name"],
            p.get("brand"),
            round(p["latitude"], 5),
            round(p["longitude"], 5),
            p.get("main_category", ""),
            p.get("place_type", ""),
            p.get("rating"),
            p.get("review_count"),
            p.get("subzone_code", p.get("subzone", "")),
        ])

    outpath = os.path.join(OUT, "places_slim.json")
    with open(outpath, "w") as f:
        json.dump(slim, f, separators=(",", ":"))
    log("  Saved %d places (%.1f MB)" % (len(slim), os.path.getsize(outpath)/1048576))
    return places


# ============================================================
# 4. SUMMARY STATS
# ============================================================
def compose_summary_stats(places, profiles):
    log("Building summary stats...")

    from collections import Counter

    cat_counts = Counter(p.get("main_category", "") for p in places)
    type_counts = Counter(p.get("place_type", "") for p in places)
    brand_counts = Counter(p.get("brand", "Independent") or "Independent" for p in places)

    branded = sum(1 for p in places if p.get("brand"))
    rated = [p["rating"] for p in places if p.get("rating")]

    stats = {
        "total_places": len(places),
        "total_subzones": len(profiles),
        "total_population": sum(p.get("population", 0) for p in profiles.values()),
        "total_area_km2": round(sum(p.get("area_km2", 0) for p in profiles.values()), 1),
        "branded_places": branded,
        "independent_places": len(places) - branded,
        "unique_brands": len(set(p.get("brand") for p in places if p.get("brand"))),
        "avg_rating": round(np.mean(rated), 2) if rated else 0,
        "category_counts": dict(cat_counts.most_common()),
        "top_place_types": dict(type_counts.most_common(30)),
        "top_brands": dict(brand_counts.most_common(30)),
    }

    outpath = os.path.join(OUT, "summary_stats.json")
    with open(outpath, "w") as f:
        json.dump(stats, f, indent=2)
    log("  Saved summary stats")


# ============================================================
# 5. CATEGORY STATS (per main_category breakdown)
# ============================================================
def compose_category_stats(places):
    log("Building category stats...")

    from collections import Counter, defaultdict

    by_cat = defaultdict(list)
    for p in places:
        by_cat[p.get("main_category", "General")].append(p)

    cat_stats = {}
    for cat, cat_places in by_cat.items():
        rated = [p["rating"] for p in cat_places if p.get("rating")]
        brands = Counter(p.get("brand", "Independent") or "Independent" for p in cat_places)
        types = Counter(p.get("place_type", "") for p in cat_places)

        cat_stats[cat] = {
            "count": len(cat_places),
            "avg_rating": round(np.mean(rated), 2) if rated else None,
            "branded_pct": round(sum(1 for p in cat_places if p.get("brand")) / max(len(cat_places), 1) * 100, 1),
            "top_types": dict(types.most_common(10)),
            "top_brands": dict(brands.most_common(10)),
        }

    outpath = os.path.join(OUT, "category_stats.json")
    with open(outpath, "w") as f:
        json.dump(cat_stats, f, indent=2)
    log("  Saved category stats for %d categories" % len(cat_stats))


# ============================================================
# 6. BRANDS
# ============================================================
def compose_brands():
    log("Building brand data...")

    brands = []
    brand_path = os.path.join(DATA, "places", "sgp_brands.jsonl")
    if os.path.exists(brand_path):
        with open(brand_path) as f:
            for line in f:
                brands.append(json.loads(line))

    outpath = os.path.join(OUT, "brands.json")
    with open(outpath, "w") as f:
        json.dump(brands, f, indent=2)
    log("  Saved %d brands" % len(brands))


# ============================================================
# 7. MRT NETWORK (for map overlay)
# ============================================================
def compose_transit():
    log("Building transit overlay...")

    import geopandas as gpd

    # MRT stations
    for d in ["transit", "transit_updated"]:
        p = os.path.join(DATA, d, "train_stations_mar2026.geojson")
        if os.path.exists(p):
            mrt = gpd.read_file(p)
            # Simplify to centroids for point layer
            mrt_pts = mrt.copy()
            mrt_pts["geometry"] = mrt_pts.geometry.centroid
            outpath = os.path.join(OUT, "mrt_stations.geojson")
            mrt_pts.to_file(outpath, driver="GeoJSON")
            log("  Saved %d MRT stations" % len(mrt_pts))
            break

    # Bus stops
    for d in ["transit", "transit_updated"]:
        p = os.path.join(DATA, d, "bus_stops_mar2026.geojson")
        if os.path.exists(p):
            bus = gpd.read_file(p)
            outpath = os.path.join(OUT, "bus_stops.geojson")
            bus.to_file(outpath, driver="GeoJSON")
            log("  Saved %d bus stops" % len(bus))
            break

    # Hawker centres
    for d in ["amenities", "amenities_updated"]:
        p = os.path.join(DATA, d, "hawker_centres.geojson")
        if os.path.exists(p):
            hawkers = gpd.read_file(p)
            outpath = os.path.join(OUT, "hawker_centres.geojson")
            hawkers.to_file(outpath, driver="GeoJSON")
            log("  Saved %d hawker centres" % len(hawkers))
            break


# ============================================================
# 8. CO-LOCATION DATA
# ============================================================
def compose_colocation():
    log("Building co-location data...")

    graph_path = os.path.join(DATA, "graphs", "colocation_pmi.json")
    if os.path.exists(graph_path):
        with open(graph_path) as f:
            pmi = json.load(f)

        # Top positive and negative pairs
        edges = pmi.get("edges", [])
        top_pos = sorted([e for e in edges if e["pmi"] > 0], key=lambda x: -x["pmi"])[:50]
        top_neg = sorted([e for e in edges if e["pmi"] < 0], key=lambda x: x["pmi"])[:20]

        outpath = os.path.join(OUT, "colocation.json")
        with open(outpath, "w") as f:
            json.dump({"positive": top_pos, "negative": top_neg}, f, indent=2)
        log("  Saved co-location data (%d pos, %d neg)" % (len(top_pos), len(top_neg)))


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    log("=" * 60)
    log("DIGITAL ATLAS SGP — DATA COMPOSER")
    log("=" * 60)

    profiles = compose_subzone_profiles()
    compose_subzone_geo()
    places = compose_places_slim()
    compose_summary_stats(places, profiles)
    compose_category_stats(places)
    compose_brands()
    compose_transit()
    compose_colocation()

    log("\nAll data composed. Files:")
    for f in sorted(os.listdir(OUT)):
        fp = os.path.join(OUT, f)
        log("  %s: %.1f KB" % (f, os.path.getsize(fp)/1024))

    total = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
    log("\nTotal: %.1f MB" % (total/1048576))
    log("DONE.")
