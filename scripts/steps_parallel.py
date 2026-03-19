#!/usr/bin/env python3
"""Steps 4-13: All parallel processing steps"""
import pandas as pd
import geopandas as gpd
import numpy as np
import json, os, time
from math import radians, sin, cos, sqrt, atan2
from collections import Counter

BASE = "/home/azureuser/digital-atlas-sgp/data"
OUT = "/home/azureuser/digital-atlas-sgp/intermediate"
os.makedirs(OUT, exist_ok=True)

def log(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    dlat, dlon = radians(lat2-lat1), radians(lon2-lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

# Load shared data
log("Loading shared data...")
sz = gpd.read_file(BASE + "/boundaries/subzones.geojson")
sz_proj = sz.to_crs(epsg=3414)
sz_proj["area_km2"] = sz_proj.geometry.area / 1e6
sz_centroids = sz.copy()
sz_centroids["centroid"] = sz_centroids.geometry.centroid
sz_centroids["cent_lat"] = sz_centroids["centroid"].y
sz_centroids["cent_lon"] = sz_centroids["centroid"].x

places = pd.read_json(BASE + "/places/sgp_places.jsonl", lines=True)
log("Loaded: %d subzones, %d places" % (len(sz), len(places)))

# ============================================================
# STEP 4: ROAD NETWORK
# ============================================================
def step_04_roads():
    log("\n=== STEP 4: ROADS ===")
    roads = gpd.read_file(BASE + "/roads/roads.geojson")
    log("Roads: %d edges" % len(roads))

    roads_proj = roads.to_crs(epsg=3414)
    roads_proj["length_m"] = roads_proj.geometry.length

    joined = gpd.sjoin(roads_proj, sz_proj[["SUBZONE_C", "geometry"]], how="left", predicate="intersects")

    result_rows = []
    for code in sz["SUBZONE_C"].unique():
        subset = joined[joined["SUBZONE_C"] == code]
        area = sz_proj[sz_proj["SUBZONE_C"] == code]["area_km2"].values[0]
        area_safe = max(area, 0.001)

        row = {"subzone_code": code}
        row["total_road_length_km"] = subset["length_m"].sum() / 1000
        row["road_density_km_per_km2"] = row["total_road_length_km"] / area_safe

        if "highway" in subset.columns:
            for rtype in ["motorway", "trunk", "primary", "secondary", "tertiary", "residential", "service", "footway", "cycleway"]:
                row["road_%s_km" % rtype] = subset[subset["highway"] == rtype]["length_m"].sum() / 1000

        result_rows.append(row)

    result = pd.DataFrame(result_rows)
    outpath = OUT + "/roads_by_subzone.parquet"
    result.to_parquet(outpath, index=False)

    assert len(result) >= 330, "Roads: too few subzones"
    assert result["total_road_length_km"].sum() > 5000, "Roads: total too low"
    log("Roads: DONE. %d subzones, total %.0f km" % (len(result), result["total_road_length_km"].sum()))
    return True

# ============================================================
# STEP 6: LAND USE
# ============================================================
def step_06_landuse():
    log("\n=== STEP 6: LAND USE ===")
    lu = gpd.read_file(BASE + "/land_use/master_plan_land_use.geojson")
    lu_proj = lu.to_crs(epsg=3414)
    lu_proj["lu_area"] = lu_proj.geometry.area
    log("Land use: %d parcels" % len(lu))

    # Map LU_DESC to broad categories
    lu_map = {}
    for desc in lu["LU_DESC"].unique():
        d = str(desc).upper()
        if "RESIDENTIAL" in d: lu_map[desc] = "residential"
        elif "COMMERCIAL" in d: lu_map[desc] = "commercial"
        elif "BUSINESS 1" in d or "BUSINESS 2" in d or "INDUSTRIAL" in d: lu_map[desc] = "industrial"
        elif "MIXED" in d or "WHITE" in d: lu_map[desc] = "mixed_use"
        elif "OPEN" in d or "PARK" in d or "RECREATION" in d or "BEACH" in d: lu_map[desc] = "open_space"
        elif "EDUCATIONAL" in d or "CIVIC" in d or "COMMUNITY" in d or "HEALTH" in d: lu_map[desc] = "institutional"
        elif "TRANSPORT" in d or "ROAD" in d or "RAIL" in d or "PORT" in d: lu_map[desc] = "transport"
        elif "RESERVE" in d or "SPECIAL" in d: lu_map[desc] = "reserve"
        elif "AGRICULTURE" in d or "WATERBODY" in d: lu_map[desc] = "nature"
        else: lu_map[desc] = "other"

    lu_proj["lu_category"] = lu_proj["LU_DESC"].map(lu_map)

    joined = gpd.sjoin(lu_proj, sz_proj[["SUBZONE_C", "geometry"]], how="left", predicate="intersects")

    result_rows = []
    lu_cats = ["residential", "commercial", "industrial", "mixed_use", "open_space", "institutional", "transport", "reserve", "nature", "other"]

    for code in sz["SUBZONE_C"].unique():
        subset = joined[joined["SUBZONE_C"] == code]
        total_lu_area = subset["lu_area"].sum()
        total_safe = max(total_lu_area, 1)

        row = {"subzone_code": code}
        for cat in lu_cats:
            cat_area = subset[subset["lu_category"] == cat]["lu_area"].sum()
            row["lu_%s_pct" % cat] = cat_area / total_safe * 100

        row["avg_gpr"] = subset["GPR"].astype(float, errors="ignore").mean() if "GPR" in subset.columns else np.nan

        # Entropy
        pcts = [row.get("lu_%s_pct" % c, 0) / 100 for c in lu_cats]
        pcts = [p for p in pcts if p > 0]
        row["lu_entropy"] = -sum(p * np.log(p) for p in pcts) if pcts else 0

        row["green_ratio"] = (row.get("lu_open_space_pct", 0) + row.get("lu_nature_pct", 0)) / 100

        result_rows.append(row)

    result = pd.DataFrame(result_rows)
    outpath = OUT + "/landuse_by_subzone.parquet"
    result.to_parquet(outpath, index=False)

    assert len(result) >= 330
    log("Land use: DONE. %d subzones" % len(result))
    return True

# ============================================================
# STEP 7: TRANSIT
# ============================================================
def step_07_transit():
    log("\n=== STEP 7: TRANSIT ===")

    # Load transit data
    for d in ["transit_updated", "new_datasets"]:
        bp = "%s/%s/bus_stops_mar2026.geojson" % (BASE, d)
        if os.path.exists(bp):
            bus = gpd.read_file(bp)
            break

    for d in ["transit_updated", "new_datasets"]:
        tp = "%s/%s/train_stations_mar2026.geojson" % (BASE, d)
        if os.path.exists(tp):
            mrt = gpd.read_file(tp)
            break

    signals = gpd.read_file(BASE + "/transit/traffic_signals.geojson") if os.path.exists(BASE + "/transit/traffic_signals.geojson") else None

    log("Bus stops: %d, MRT stations: %d" % (len(bus), len(mrt)))

    # Get centroids
    bus_pts = [(g.y, g.x) for g in bus.geometry.centroid]
    mrt_pts = [(g.centroid.y, g.centroid.x) for g in mrt.geometry]

    result_rows = []
    place_transit_rows = []

    for _, sz_row in sz_centroids.iterrows():
        code = sz_row["SUBZONE_C"]
        clat, clon = sz_row["cent_lat"], sz_row["cent_lon"]

        # MRT distances
        mrt_dists = [haversine(clat, clon, lat, lon) for lat, lon in mrt_pts]
        mrt_dists.sort()

        # Bus stops in subzone (rough: within 1km of centroid)
        bus_nearby = sum(1 for lat, lon in bus_pts if haversine(clat, clon, lat, lon) < 1000)
        bus_500m = sum(1 for lat, lon in bus_pts if haversine(clat, clon, lat, lon) < 500)

        area = sz_proj[sz_proj["SUBZONE_C"] == code]["area_km2"].values[0]

        row = {
            "subzone_code": code,
            "dist_nearest_mrt": mrt_dists[0] if mrt_dists else 99999,
            "mrt_stations_1km": sum(1 for d in mrt_dists if d <= 1000),
            "bus_stop_count_1km": bus_nearby,
            "bus_stop_count_500m": bus_500m,
            "bus_density_per_km2": bus_nearby / max(area, 0.001),
        }

        if signals is not None:
            sig_pts = [(g.y, g.x) for g in signals.geometry]
            row["traffic_signal_count_1km"] = sum(1 for lat, lon in sig_pts if haversine(clat, clon, lat, lon) < 1000)

        result_rows.append(row)

    # Place-level transit
    log("Computing place-level transit features...")
    for _, p in places.iterrows():
        plat, plon = p["latitude"], p["longitude"]
        mrt_d = [haversine(plat, plon, lat, lon) for lat, lon in mrt_pts]
        bus_d = [haversine(plat, plon, lat, lon) for lat, lon in bus_pts]

        place_transit_rows.append({
            "place_id": p["id"],
            "subzone_code": p.get("subzone_code", ""),
            "dist_nearest_mrt": min(mrt_d) if mrt_d else 99999,
            "dist_nearest_bus": min(bus_d) if bus_d else 99999,
            "bus_stops_300m": sum(1 for d in bus_d if d <= 300),
            "mrt_within_500m": 1 if (mrt_d and min(mrt_d) <= 500) else 0,
        })

    result = pd.DataFrame(result_rows)
    result.to_parquet(OUT + "/transit_by_subzone.parquet", index=False)

    place_transit = pd.DataFrame(place_transit_rows)
    place_transit.to_parquet(OUT + "/transit_by_place.parquet", index=False)

    assert len(result) >= 330
    assert len(place_transit) >= 60000
    log("Transit: DONE. %d subzones, %d places" % (len(result), len(place_transit)))
    return True

# ============================================================
# STEP 8: PLACE CATEGORY COMPOSITION
# ============================================================
def step_08_categories():
    log("\n=== STEP 8: PLACE CATEGORY COMPOSITION ===")

    cats = places.groupby(["subzone_code", "main_category"]).size().unstack(fill_value=0)
    cats.columns = ["cat_%s" % c.lower().replace(" & ", "_").replace(" ", "_") for c in cats.columns]

    totals = cats.sum(axis=1)
    cats_pct = cats.div(totals, axis=0) * 100
    cats_pct.columns = [c + "_pct" for c in cats_pct.columns]

    result = pd.DataFrame({"subzone_code": cats.index, "total_place_count": totals.values})
    result = result.merge(cats, left_on="subzone_code", right_index=True, how="left")
    result = result.merge(cats_pct, left_on="subzone_code", right_index=True, how="left")

    # Add area for density
    areas = sz_proj[["SUBZONE_C", "area_km2"]].rename(columns={"SUBZONE_C": "subzone_code"})
    result = result.merge(areas, on="subzone_code", how="left")
    result["place_density_per_km2"] = result["total_place_count"] / result["area_km2"].clip(lower=0.001)

    # Category entropy
    pct_cols = [c for c in cats_pct.columns]
    pcts = result[pct_cols].values / 100
    pcts = np.where(pcts > 0, pcts, 1e-10)
    result["category_entropy"] = -np.sum(pcts * np.log(pcts), axis=1)

    result.drop(columns=["area_km2"], inplace=True)
    result.to_parquet(OUT + "/place_composition_by_subzone.parquet", index=False)

    assert len(result) >= 300
    assert result["total_place_count"].sum() > 60000
    log("Categories: DONE. %d subzones" % len(result))
    return True

# ============================================================
# STEP 9: PLACE TYPE COUNTS
# ============================================================
def step_09_place_types():
    log("\n=== STEP 9: PLACE TYPE COUNTS ===")

    # Top 80 place types
    top_types = places["place_type"].value_counts().head(80).index.tolist()

    type_counts = places[places["place_type"].isin(top_types)].groupby(["subzone_code", "place_type"]).size().unstack(fill_value=0)
    type_counts.columns = ["type_%s" % c.lower().replace(" & ", "_").replace(" ", "_").replace("/", "_") for c in type_counts.columns]

    result = type_counts.reset_index().rename(columns={"subzone_code": "subzone_code"})
    result.to_parquet(OUT + "/place_types_by_subzone.parquet", index=False)

    assert len(result) >= 300
    log("Place types: DONE. %d subzones, %d type features" % (len(result), len(type_counts.columns)))
    return True

# ============================================================
# STEP 10: BRAND & QUALITY
# ============================================================
def step_10_brands():
    log("\n=== STEP 10: BRAND & QUALITY ===")

    result_rows = []
    for code, group in places.groupby("subzone_code"):
        n = len(group)
        n_safe = max(n, 1)
        row = {"subzone_code": code}
        row["branded_count"] = group["brand"].notna().sum() if "brand" in group.columns else 0
        row["branded_pct"] = row["branded_count"] / n_safe * 100
        row["unique_brand_count"] = group["brand"].nunique() if "brand" in group.columns else 0
        row["avg_rating"] = group["rating"].mean() if "rating" in group.columns else np.nan
        row["median_rating"] = group["rating"].median() if "rating" in group.columns else np.nan
        row["rating_std"] = group["rating"].std() if "rating" in group.columns else np.nan
        row["high_rated_pct"] = (group["rating"] >= 4.5).sum() / n_safe * 100 if "rating" in group.columns else 0
        row["total_reviews"] = group["review_count"].sum() if "review_count" in group.columns else 0
        row["has_phone_pct"] = group["phone"].notna().sum() / n_safe * 100
        row["has_website_pct"] = group["website"].notna().sum() / n_safe * 100
        result_rows.append(row)

    result = pd.DataFrame(result_rows)
    result.to_parquet(OUT + "/brand_quality_by_subzone.parquet", index=False)

    assert len(result) >= 300
    log("Brands: DONE. %d subzones" % len(result))
    return True

# ============================================================
# STEP 12: CROSS-REFERENCE WITH GOV DATA
# ============================================================
def step_12_crossref():
    log("\n=== STEP 12: CROSS-REFERENCE ===")

    result_rows = []

    # SFA eating establishments
    sfa_path = None
    for d in ["amenities_updated", "new_datasets"]:
        p = "%s/%s/eating_establishments_sfa.geojson" % (BASE, d)
        if os.path.exists(p):
            sfa_path = p
            break

    sfa_by_sz = Counter()
    if sfa_path:
        sfa = gpd.read_file(sfa_path)
        sfa_joined = gpd.sjoin(sfa.to_crs(epsg=4326), sz[["SUBZONE_C", "geometry"]], how="left", predicate="within")
        sfa_by_sz = Counter(sfa_joined["SUBZONE_C"].dropna())
        log("SFA: %d eating establishments mapped" % len(sfa_joined))

    # CHAS clinics
    chas_by_sz = Counter()
    for d in ["amenities_updated", "new_datasets"]:
        p = "%s/%s/chas_clinics.geojson" % (BASE, d)
        if os.path.exists(p):
            chas = gpd.read_file(p)
            chas_joined = gpd.sjoin(chas.to_crs(epsg=4326), sz[["SUBZONE_C", "geometry"]], how="left", predicate="within")
            chas_by_sz = Counter(chas_joined["SUBZONE_C"].dropna())
            log("CHAS: %d clinics mapped" % len(chas_joined))
            break

    # Preschools
    pre_by_sz = Counter()
    for d in ["amenities_updated", "new_datasets"]:
        p = "%s/%s/preschools.geojson" % (BASE, d)
        if os.path.exists(p):
            pre = gpd.read_file(p)
            pre_joined = gpd.sjoin(pre.to_crs(epsg=4326), sz[["SUBZONE_C", "geometry"]], how="left", predicate="within")
            pre_by_sz = Counter(pre_joined["SUBZONE_C"].dropna())
            log("Preschools: %d mapped" % len(pre_joined))
            break

    # Our places count by subzone
    our_by_sz = places.groupby("subzone_code").size().to_dict()
    our_fnb = places[places["main_category"].isin(["Restaurant", "Cafe & Coffee", "Hawker & Street Food", "Fast Food & QSR", "Bar & Nightlife", "Bakery & Pastry"])].groupby("subzone_code").size().to_dict()

    for code in sz["SUBZONE_C"].unique():
        row = {
            "subzone_code": code,
            "sfa_eating_count": sfa_by_sz.get(code, 0),
            "chas_clinic_count": chas_by_sz.get(code, 0),
            "preschool_count_gov": pre_by_sz.get(code, 0),
            "our_place_count": our_by_sz.get(code, 0),
            "our_fnb_count": our_fnb.get(code, 0),
        }
        if row["sfa_eating_count"] > 0:
            row["fnb_coverage_ratio"] = row["our_fnb_count"] / row["sfa_eating_count"]
        else:
            row["fnb_coverage_ratio"] = np.nan
        result_rows.append(row)

    result = pd.DataFrame(result_rows)
    result.to_parquet(OUT + "/validation_by_subzone.parquet", index=False)

    assert len(result) >= 330
    log("Cross-ref: DONE. %d subzones" % len(result))
    return True

# ============================================================
# STEP 13: AMENITY ACCESSIBILITY
# ============================================================
def step_13_amenities():
    log("\n=== STEP 13: AMENITY ACCESSIBILITY ===")

    # Load amenities
    parks = gpd.read_file(BASE + "/amenities/parks.geojson") if os.path.exists(BASE + "/amenities/parks.geojson") else None
    hawkers = gpd.read_file(BASE + "/amenities/hawker_centres.geojson") if os.path.exists(BASE + "/amenities/hawker_centres.geojson") else None
    schools_geo = None
    if os.path.exists(BASE + "/amenities/schools_geocoded.json"):
        with open(BASE + "/amenities/schools_geocoded.json") as f:
            schools_list = json.load(f)
        schools_geo = [(s["lat"], s["lon"]) for s in schools_list if s.get("lat") and s.get("lon")]
    supermarkets = gpd.read_file(BASE + "/amenities/supermarkets.geojson") if os.path.exists(BASE + "/amenities/supermarkets.geojson") else None
    hotels = gpd.read_file(BASE + "/amenities/hotels.geojson") if os.path.exists(BASE + "/amenities/hotels.geojson") else None

    park_pts = [(g.y, g.x) for g in parks.geometry] if parks is not None else []
    hawker_pts = [(g.y, g.x) for g in hawkers.geometry] if hawkers is not None else []
    super_pts = [(g.y, g.x) for g in supermarkets.geometry.centroid] if supermarkets is not None else []

    result_rows = []
    for _, sz_row in sz_centroids.iterrows():
        code = sz_row["SUBZONE_C"]
        clat, clon = sz_row["cent_lat"], sz_row["cent_lon"]

        row = {"subzone_code": code}

        if park_pts:
            dists = [haversine(clat, clon, lat, lon) for lat, lon in park_pts]
            row["dist_nearest_park"] = min(dists)
            row["parks_within_1km"] = sum(1 for d in dists if d <= 1000)

        if hawker_pts:
            dists = [haversine(clat, clon, lat, lon) for lat, lon in hawker_pts]
            row["dist_nearest_hawker"] = min(dists)
            row["hawkers_within_1km"] = sum(1 for d in dists if d <= 1000)

        if super_pts:
            dists = [haversine(clat, clon, lat, lon) for lat, lon in super_pts]
            row["dist_nearest_supermarket"] = min(dists)
            row["supermarkets_within_1km"] = sum(1 for d in dists if d <= 1000)

        if schools_geo:
            dists = [haversine(clat, clon, lat, lon) for lat, lon in schools_geo]
            row["dist_nearest_school"] = min(dists)
            row["schools_within_1km"] = sum(1 for d in dists if d <= 1000)

        if hotels is not None:
            h_pts = [(g.y, g.x) for g in hotels.geometry]
            row["hotel_count_1km"] = sum(1 for lat, lon in h_pts if haversine(clat, clon, lat, lon) <= 1000)

        result_rows.append(row)

    result = pd.DataFrame(result_rows)
    result.to_parquet(OUT + "/amenity_by_subzone.parquet", index=False)

    assert len(result) >= 330
    log("Amenities: DONE. %d subzones" % len(result))
    return True

# ============================================================
# RUN ALL
# ============================================================
if __name__ == "__main__":
    results = {}

    for name, func in [
        ("step_04_roads", step_04_roads),
        ("step_06_landuse", step_06_landuse),
        ("step_07_transit", step_07_transit),
        ("step_08_categories", step_08_categories),
        ("step_09_place_types", step_09_place_types),
        ("step_10_brands", step_10_brands),
        ("step_12_crossref", step_12_crossref),
        ("step_13_amenities", step_13_amenities),
    ]:
        try:
            ok = func()
            results[name] = "OK"
        except Exception as e:
            log("FAILED: %s - %s" % (name, str(e)[:200]))
            results[name] = "FAIL: %s" % str(e)[:100]

    log("\n" + "=" * 60)
    log("PARALLEL STEPS COMPLETE")
    log("=" * 60)
    for name, status in results.items():
        log("  [%s] %s" % (status[:4], name))

    log("\nIntermediate files:")
    for f in sorted(os.listdir(OUT)):
        fp = os.path.join(OUT, f)
        log("  %s: %.1f KB" % (f, os.path.getsize(fp)/1024))
