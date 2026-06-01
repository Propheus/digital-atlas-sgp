"""
Plexis SGP v4 — Stage 1a: attach hex IDs + admin parents to every place.

Inputs:
  places/sgp_place_V1.jsonl           (190,591 rows)
  boundaries/subzones.geojson         (332)
  boundaries/planning_areas.geojson   (55)
  boundaries/regions.geojson          (5)
  boundaries/hdb_towns.geojson        (27)

Outputs:
  places/sgp_places_geoattached.jsonl  (one row per place, + geo columns)
  places/sgp_places_geoattached.parquet (same, parquet for fast joins)
  places/geoattach_report.json         (coverage breakdown)

Columns added per place:
  hex9_id, hex8_id
  parent_subzone_c, parent_subzone_name
  parent_pa, parent_region
  hdb_town  (or null if place is outside any HDB town polygon)
  in_sgp    (bool — fails if lat/lng outside the SGP bbox)
"""
import json, time
from pathlib import Path
from collections import Counter

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from shapely.strtree import STRtree
import h3

ROOT = Path(__file__).parent
PLACES_IN = ROOT / "places/sgp_place_V1.jsonl"
PLACES_OUT_JSONL = ROOT / "places/sgp_places_geoattached.jsonl"
PLACES_OUT_PQ = ROOT / "places/sgp_places_geoattached.parquet"
REPORT = ROOT / "places/geoattach_report.json"


def main():
    t0 = time.time()
    print("Loading boundaries...")
    gdf_sz = gpd.read_file(ROOT / "boundaries/subzones.geojson").to_crs(4326)
    gdf_pa = gpd.read_file(ROOT / "boundaries/planning_areas.geojson").to_crs(4326)
    gdf_rg = gpd.read_file(ROOT / "boundaries/regions.geojson").to_crs(4326)
    gdf_hdb = gpd.read_file(ROOT / "boundaries/hdb_towns.geojson").to_crs(4326)
    print(f"  subzones={len(gdf_sz)} PAs={len(gdf_pa)} regions={len(gdf_rg)} HDB={len(gdf_hdb)}")

    # STRtrees for fast point-in-polygon
    sz_tree = STRtree(gdf_sz.geometry.values)
    pa_tree = STRtree(gdf_pa.geometry.values)
    rg_tree = STRtree(gdf_rg.geometry.values)
    hdb_tree = STRtree(gdf_hdb.geometry.values)

    sz_geoms = list(gdf_sz.geometry.values); sz_codes = list(gdf_sz["SUBZONE_C"]); sz_names = list(gdf_sz["SUBZONE_N"])
    pa_geoms = list(gdf_pa.geometry.values); pa_names = list(gdf_pa["PLN_AREA_N"])
    rg_geoms = list(gdf_rg.geometry.values); rg_names = list(gdf_rg["REGION_N"])
    hdb_geoms = list(gdf_hdb.geometry.values); hdb_names = list(gdf_hdb["hdb_town"])

    # SGP bounding box (generous)
    SGP_BBOX = (103.5, 1.0, 104.2, 1.5)  # (lng_min, lat_min, lng_max, lat_max)

    # Projected boundary geometries for nearest-neighbour fallback (meters)
    gdf_sz_3414 = gdf_sz.to_crs(3414)
    gdf_pa_3414 = gdf_pa.to_crs(3414)
    gdf_rg_3414 = gdf_rg.to_crs(3414)
    gdf_hdb_3414 = gdf_hdb.to_crs(3414)

    def lookup_by_tree(pt, tree, geoms, keys):
        for i in tree.query(pt):
            if geoms[i].contains(pt):
                return keys[i]
        return None

    def nearest_by_projection(pt_4326, gdf_proj, key_col, max_m=500):
        """For points just outside all polygons (coastal jetties, bridges):
        project to meters, find the nearest polygon, return key if within max_m."""
        pt_proj = gpd.GeoSeries([pt_4326], crs=4326).to_crs(3414).iloc[0]
        dists = gdf_proj.geometry.distance(pt_proj)
        min_idx = dists.idxmin()
        min_d = dists.iloc[min_idx]
        if min_d <= max_m:
            return gdf_proj.iloc[min_idx][key_col], float(min_d)
        return None, float(min_d)

    # Stream the input; write enriched rows
    n_in = 0
    n_ok = 0
    n_missing_coords = 0
    n_outside_bbox = 0
    n_missing_sz = 0
    n_missing_pa = 0
    n_missing_rg = 0
    n_in_hdb = 0
    cat_counts = Counter()
    hex9_counts = Counter()
    hex8_counts = Counter()

    out_rows = []  # for parquet; jsonl streamed separately

    t = time.time()
    print(f"\nEnriching {PLACES_IN}...")
    with open(PLACES_IN) as f_in, open(PLACES_OUT_JSONL, "w") as f_out:
        for line in f_in:
            n_in += 1
            try:
                r = json.loads(line)
            except Exception:
                continue
            lat = r.get("latitude")
            lng = r.get("longitude")
            if not (isinstance(lat, (int, float)) and isinstance(lng, (int, float))):
                n_missing_coords += 1
                r["_enrichment_error"] = "missing_coords"
                f_out.write(json.dumps(r) + "\n")
                continue
            in_bbox = (SGP_BBOX[0] <= lng <= SGP_BBOX[2]) and (SGP_BBOX[1] <= lat <= SGP_BBOX[3])
            r["in_sgp"] = bool(in_bbox)
            if not in_bbox:
                n_outside_bbox += 1
                r["_enrichment_error"] = "outside_sgp"
                f_out.write(json.dumps(r) + "\n")
                continue

            # H3 IDs (always computable)
            h9 = h3.latlng_to_cell(lat, lng, 9)
            h8 = h3.latlng_to_cell(lat, lng, 8)
            r["hex9_id"] = h9
            r["hex8_id"] = h8
            hex9_counts[h9] += 1
            hex8_counts[h8] += 1

            pt = Point(lng, lat)
            # parent subzone
            sz_idx = None
            for i in sz_tree.query(pt):
                if sz_geoms[i].contains(pt):
                    sz_idx = i
                    break
            nearest_m = None
            if sz_idx is not None:
                r["parent_subzone_c"] = sz_codes[sz_idx]
                r["parent_subzone_name"] = sz_names[sz_idx]
                r["parent_subzone_source"] = "contains"
            else:
                # Coastal fallback: nearest subzone within 500 m
                nearest_c, nearest_m = nearest_by_projection(pt, gdf_sz_3414, "SUBZONE_C", max_m=500)
                if nearest_c:
                    # Look up the full name
                    sz_row = gdf_sz[gdf_sz["SUBZONE_C"] == nearest_c].iloc[0]
                    r["parent_subzone_c"] = nearest_c
                    r["parent_subzone_name"] = sz_row["SUBZONE_N"]
                    r["parent_subzone_source"] = f"nearest({nearest_m:.0f}m)"
                else:
                    # Farther than 500 m from any subzone — treat as offshore/marine
                    r["parent_subzone_c"] = None
                    r["parent_subzone_name"] = None
                    r["parent_subzone_source"] = f"offshore_marine({nearest_m:.0f}m_to_land)" if nearest_m else "offshore_marine"
                    n_missing_sz += 1
            # parent PA
            pa_name = lookup_by_tree(pt, pa_tree, pa_geoms, pa_names)
            if pa_name is None:
                pa_name, _ = nearest_by_projection(pt, gdf_pa_3414, "PLN_AREA_N", max_m=500)
            r["parent_pa"] = pa_name
            if pa_name is None: n_missing_pa += 1
            # parent region
            rg_name = lookup_by_tree(pt, rg_tree, rg_geoms, rg_names)
            if rg_name is None:
                rg_name, _ = nearest_by_projection(pt, gdf_rg_3414, "REGION_N", max_m=500)
            r["parent_region"] = rg_name
            if rg_name is None: n_missing_rg += 1
            # HDB town — no fallback; a place is only "in" an HDB town if inside its polygon
            hdb_name = lookup_by_tree(pt, hdb_tree, hdb_geoms, hdb_names)
            r["hdb_town"] = hdb_name
            if hdb_name: n_in_hdb += 1

            cat_counts[r.get("primary_category") or "unknown"] += 1
            n_ok += 1
            f_out.write(json.dumps(r) + "\n")
            out_rows.append({
                "id": r.get("id"),
                "name": r.get("name"),
                "primary_category": r.get("primary_category"),
                "brand": r.get("brand"),
                "rating": r.get("rating"),
                "reviews_count": r.get("reviews_count"),
                "latitude": lat, "longitude": lng,
                "hex9_id": h9, "hex8_id": h8,
                "parent_subzone_c": r.get("parent_subzone_c"),
                "parent_subzone_name": r.get("parent_subzone_name"),
                "parent_subzone_source": r.get("parent_subzone_source"),
                "parent_pa": r.get("parent_pa"),
                "parent_region": r.get("parent_region"),
                "hdb_town": r.get("hdb_town"),
                "in_sgp": True,
            })
            if n_in % 20000 == 0:
                print(f"  ...{n_in:,} rows processed ({n_in/(time.time()-t):.0f} rows/s)")

    # Parquet
    df = pd.DataFrame(out_rows)
    df.to_parquet(PLACES_OUT_PQ, index=False)

    # Coverage per admin layer
    sz_places = df["parent_subzone_c"].value_counts().to_dict()
    pa_places = df["parent_pa"].value_counts().to_dict()
    rg_places = df["parent_region"].value_counts().to_dict()
    hdb_places = df[df["hdb_town"].notna()]["hdb_town"].value_counts().to_dict()

    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "input_rows": n_in,
        "enriched_ok": n_ok,
        "missing_coords": n_missing_coords,
        "outside_sgp_bbox": n_outside_bbox,
        "missing_subzone": n_missing_sz,
        "missing_pa": n_missing_pa,
        "missing_region": n_missing_rg,
        "places_in_hdb_town": n_in_hdb,
        "unique_hex9_populated": len(hex9_counts),
        "unique_hex8_populated": len(hex8_counts),
        "hex9_places_median": sorted(hex9_counts.values())[len(hex9_counts)//2] if hex9_counts else 0,
        "hex9_places_max": max(hex9_counts.values()) if hex9_counts else 0,
        "top_categories": cat_counts.most_common(20),
        "subzones_with_any_places": len(sz_places),
        "pas_with_any_places": len(pa_places),
        "regions_with_any_places": len(rg_places),
        "hdb_towns_with_any_places": len(hdb_places),
        "wall_clock_s": round(time.time() - t0, 2),
    }
    with open(REPORT, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n=== Coverage ===")
    print(f"  input: {n_in:,}")
    print(f"  enriched OK: {n_ok:,} ({100*n_ok/n_in:.2f}%)")
    print(f"  missing coords: {n_missing_coords:,}")
    print(f"  outside SGP bbox: {n_outside_bbox:,}")
    print(f"  missing subzone/PA/region: {n_missing_sz}/{n_missing_pa}/{n_missing_rg}")
    print(f"  inside HDB town: {n_in_hdb:,} ({100*n_in_hdb/n_ok:.1f}%)")
    print(f"  unique hex-9 populated: {len(hex9_counts):,} / 7,318 ({100*len(hex9_counts)/7318:.1f}%)")
    print(f"  unique hex-8 populated: {len(hex8_counts):,} / 1,191 ({100*len(hex8_counts)/1191:.1f}%)")
    print(f"  subzones with any places: {len(sz_places)} / 332")
    print(f"  PAs with any places: {len(pa_places)} / 55")
    print(f"  regions with any places: {len(rg_places)} / 5")
    print(f"  HDB towns with any places: {len(hdb_places)} / 27")
    print(f"\n  wall clock: {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
