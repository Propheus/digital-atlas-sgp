"""
Plexis SGP v4 — Stage 7s: Schools layer per scale.

Sources:
  amenities_updated/schools_directory.csv  337 MOE schools (geocoded via OneMap)
  amenities_updated/school_zones.geojson   211 primary school catchment polygons

Per hex/subzone:
  school_count_total
  school_count_primary / secondary / jc / mixed
  school_count_premium       (SAP | Gifted | IP indicator)
  primary_school_zone_count  (overlapping primary catchment polygons)
  in_primary_school_zone     (hex-centroid in any primary catchment)
  nearest_school_dist_m
  nearest_primary_school_dist_m

Outputs:
  hex/hex9_schools.parquet
  hex/hex8_schools.parquet
  hex/subzone_schools.parquet
"""
import json, os, time
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
from sklearn.neighbors import BallTree
import h3
import requests

ROOT = Path(__file__).parent


def _resolve_data_root():
    if os.environ.get("PLEXIS_DATA_ROOT"):
        return Path(os.environ["PLEXIS_DATA_ROOT"])
    for c in [Path("/home/azureuser/digital-atlas-sgp/data"), ROOT.parent / "data"]:
        if c.exists(): return c
    raise FileNotFoundError("data root not found")


DATA = _resolve_data_root()
SCHOOLS_CSV = DATA / "amenities_updated/schools_directory.csv"
ZONES_GJ    = DATA / "amenities_updated/school_zones.geojson"
GEOCODE_CACHE = ROOT / "cache/schools_geocoded.csv"


def geocode_postal(postal):
    """OneMap search by 6-digit postal code."""
    if pd.isna(postal): return None, None
    p = str(int(postal)).zfill(6)
    try:
        r = requests.get(
            "https://www.onemap.gov.sg/api/common/elastic/search",
            params={"searchVal": p, "returnGeom": "Y", "getAddrDetails": "Y"},
            timeout=10,
        )
        d = r.json()
        if d.get("found", 0) >= 1:
            res = d["results"][0]
            return float(res["LATITUDE"]), float(res["LONGITUDE"])
    except Exception:
        pass
    return None, None


def load_schools():
    print(f"Loading {SCHOOLS_CSV.name}...")
    s = pd.read_csv(SCHOOLS_CSV)
    print(f"  {len(s)} schools")

    # Cache hit?
    if GEOCODE_CACHE.exists():
        cache = pd.read_csv(GEOCODE_CACHE, dtype={"postal_code": str})
        print(f"  cache hit: {len(cache)} schools")
        s["postal_str"] = s["postal_code"].apply(lambda x: str(int(x)).zfill(6) if pd.notna(x) else "")
        cache["postal_str"] = cache["postal_code"].astype(str).str.zfill(6)
        s = s.merge(cache[["postal_str","lat","lng"]], on="postal_str", how="left")
    else:
        s["lat"] = np.nan
        s["lng"] = np.nan

    missing = s[s["lat"].isna() | s["lng"].isna()]
    if len(missing):
        print(f"  geocoding {len(missing)} schools via OneMap...")
        rows = []
        for i, r in missing.iterrows():
            lat, lng = geocode_postal(r["postal_code"])
            s.at[i, "lat"] = lat
            s.at[i, "lng"] = lng
            rows.append({"postal_code": r["postal_code"], "lat": lat, "lng": lng})
            if (i + 1) % 25 == 0:
                print(f"    {i+1}/{len(s)} done")
        # Persist updated cache
        GEOCODE_CACHE.parent.mkdir(exist_ok=True)
        s_out = s[["postal_code","lat","lng"]].drop_duplicates(subset=["postal_code"]).dropna(subset=["lat","lng"])
        s_out.to_csv(GEOCODE_CACHE, index=False)
        print(f"  cache written: {GEOCODE_CACHE}")

    print(f"  geocoded ok: {s['lat'].notna().sum()}/{len(s)}")
    return s.dropna(subset=["lat","lng"])


def main():
    t0 = time.time()
    schools = load_schools()
    print(f"\nClassifying levels...")
    schools["level"] = schools["mainlevel_code"].fillna("OTHER").map(
        lambda x: ("primary" if "PRIMARY" in x or "P1" in x else
                   "jc" if "JUNIOR" in x or "JC" in x or "CENTRALISED" in x else
                   "secondary" if "SECONDARY" in x or "S1" in x else
                   "mixed")
    )
    schools["is_premium"] = (
        (schools.get("sap_ind", "No") == "Yes") |
        (schools.get("gifted_ind", "No") == "Yes") |
        (schools.get("ip_ind", "No") == "Yes")
    ).astype(int)

    print(schools["level"].value_counts())
    print(f"  premium: {int(schools['is_premium'].sum())}")

    # === Project schools to 3414 ===
    schools_gdf = gpd.GeoDataFrame(
        schools, geometry=gpd.points_from_xy(schools["lng"], schools["lat"]),
        crs="EPSG:4326"
    ).to_crs(3414)
    school_xy = np.column_stack([schools_gdf.geometry.x.values, schools_gdf.geometry.y.values])

    # === Hex9 setup ===
    print("\n--- HEX-9 ---")
    h9 = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
    # h9_id → centroid lat/lng, then 3414
    h9_centroids_4326 = np.array([h3.cell_to_latlng(c) for c in h9["hex9_id"]])
    h9_gdf = gpd.GeoDataFrame(
        {"hex9_id": h9["hex9_id"]},
        geometry=gpd.points_from_xy(h9_centroids_4326[:, 1], h9_centroids_4326[:, 0]),
        crs="EPSG:4326"
    ).to_crs(3414)
    h9_xy = np.column_stack([h9_gdf.geometry.x.values, h9_gdf.geometry.y.values])

    # Assign each school to a hex9 via h3
    schools["hex9_id"] = [h3.latlng_to_cell(lat, lng, 9) for lat, lng in zip(schools["lat"], schools["lng"])]
    schools["hex8_id"] = [h3.cell_to_parent(c, 8) for c in schools["hex9_id"]]

    # Per-hex school counts via groupby
    cnt_total = schools.groupby("hex9_id").size().reset_index(name="school_count_total")
    cnt_lvl = schools.groupby(["hex9_id","level"]).size().unstack(fill_value=0).reset_index()
    for L in ["primary","secondary","jc","mixed"]:
        if L not in cnt_lvl.columns: cnt_lvl[L] = 0
    cnt_lvl = cnt_lvl[["hex9_id","primary","secondary","jc","mixed"]].rename(columns={
        "primary": "school_count_primary",
        "secondary": "school_count_secondary",
        "jc": "school_count_jc",
        "mixed": "school_count_mixed",
    })
    cnt_premium = schools[schools["is_premium"]==1].groupby("hex9_id").size().reset_index(name="school_count_premium")

    h9_out = h9[["hex9_id"]].merge(cnt_total, on="hex9_id", how="left")
    h9_out = h9_out.merge(cnt_lvl, on="hex9_id", how="left")
    h9_out = h9_out.merge(cnt_premium, on="hex9_id", how="left")

    # Nearest distances via BallTree
    school_tree = BallTree(school_xy)
    primary_mask = (schools["level"] == "primary").values
    primary_xy = school_xy[primary_mask]
    primary_tree = BallTree(primary_xy)

    nd_any, _ = school_tree.query(h9_xy, k=1)
    nd_pri, _ = primary_tree.query(h9_xy, k=1)
    h9_out["nearest_school_dist_m"] = nd_any[:, 0].round(1)
    h9_out["nearest_primary_school_dist_m"] = nd_pri[:, 0].round(1)

    # Catchment counts: primary schools within 1km / 2km of hex centroid
    # (HDB priority is 1km; Phase 2C registration is 2km)
    print("  computing primary catchment counts (1km, 2km)...")
    cnt_1km = primary_tree.query_radius(h9_xy, r=1000, count_only=True)
    cnt_2km = primary_tree.query_radius(h9_xy, r=2000, count_only=True)
    h9_out["primary_schools_within_1km"] = cnt_1km.astype(int)
    h9_out["primary_schools_within_2km"] = cnt_2km.astype(int)

    # School-zone overlap (polygon ∩ hex9 polygon)
    print("  computing primary school zone overlaps...")
    zones = gpd.read_file(ZONES_GJ).to_crs(3414)
    # Build hex9 polygons in 3414
    def _hex_poly_3414(cell):
        ring_4326 = [(lng, lat) for lat, lng in h3.cell_to_boundary(cell)]
        return Polygon(ring_4326)
    h9_polys_4326 = gpd.GeoDataFrame(
        {"hex9_id": h9["hex9_id"]},
        geometry=[_hex_poly_3414(c) for c in h9["hex9_id"]],
        crs="EPSG:4326"
    ).to_crs(3414)
    sj = gpd.sjoin(h9_polys_4326, zones, how="left", predicate="intersects")
    zone_count = sj.groupby("hex9_id").size().reset_index(name="primary_school_zone_count")
    # if no intersection, sjoin still keeps the hex but with NaN for zone fields → size = 1 incorrectly
    # Fix: count only rows where SITENAME (zone field) is not null
    has_zone = sj[sj["SITENAME"].notna()]
    zone_count = has_zone.groupby("hex9_id").size().reset_index(name="primary_school_zone_count")
    h9_out = h9_out.merge(zone_count, on="hex9_id", how="left")
    h9_out["in_primary_school_zone"] = (h9_out["primary_school_zone_count"].fillna(0) > 0).astype(int)

    # Fill NaNs
    fill_cols = ["school_count_total","school_count_primary","school_count_secondary",
                 "school_count_jc","school_count_mixed","school_count_premium",
                 "primary_school_zone_count",
                 "primary_schools_within_1km","primary_schools_within_2km"]
    for c in fill_cols: h9_out[c] = h9_out[c].fillna(0).astype(int)
    h9_out.to_parquet(ROOT / "hex/hex9_schools.parquet", index=False)
    print(f"  hex9_schools: {h9_out.shape}")

    # SUM cols (one school is in exactly one hex9, so SUMs roll up cleanly)
    sum_cols = ["school_count_total","school_count_primary","school_count_secondary",
                "school_count_jc","school_count_mixed","school_count_premium",
                "primary_school_zone_count"]
    # MEAN cols (catchment counts — average accessibility across constituent hex9s)
    mean_cols = ["primary_schools_within_1km","primary_schools_within_2km"]
    # MIN cols
    min_cols = ["nearest_school_dist_m","nearest_primary_school_dist_m"]

    # === HEX-8 ===
    print("\n--- HEX-8 ---")
    h8_uni = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")[["hex8_id"]]
    h9_with_p = h9_out.merge(h9[["hex9_id","parent_hex8"]], on="hex9_id", how="left")
    h8_sum = h9_with_p.groupby("parent_hex8")[sum_cols].sum().reset_index().rename(columns={"parent_hex8":"hex8_id"})
    h8_mean = h9_with_p.groupby("parent_hex8")[mean_cols].mean().reset_index().rename(columns={"parent_hex8":"hex8_id"})
    h8_min = h9_with_p.groupby("parent_hex8")[min_cols].min().reset_index().rename(columns={"parent_hex8":"hex8_id"})
    h8_out = h8_uni.merge(h8_sum, on="hex8_id", how="left").merge(h8_mean, on="hex8_id", how="left").merge(h8_min, on="hex8_id", how="left")
    h8_out["in_primary_school_zone"] = (h8_out["primary_school_zone_count"].fillna(0) > 0).astype(int)
    for c in sum_cols: h8_out[c] = h8_out[c].fillna(0).astype(int)
    for c in mean_cols: h8_out[c] = h8_out[c].fillna(0).round(2)
    h8_out.to_parquet(ROOT / "hex/hex8_schools.parquet", index=False)
    print(f"  hex8_schools: {h8_out.shape}")

    # === SUBZONE ===
    print("\n--- SUBZONE ---")
    sz_lu = pd.read_parquet(ROOT / "hex/subzone_land_use.parquet")[["subzone_c"]].drop_duplicates()
    h9_with_sz = h9_out.merge(h9[["hex9_id","parent_subzone"]], on="hex9_id", how="left")
    sz_sum = h9_with_sz.groupby("parent_subzone")[sum_cols].sum().reset_index().rename(columns={"parent_subzone":"subzone_c"})
    sz_mean = h9_with_sz.groupby("parent_subzone")[mean_cols].mean().reset_index().rename(columns={"parent_subzone":"subzone_c"})
    sz_min = h9_with_sz.groupby("parent_subzone")[min_cols].min().reset_index().rename(columns={"parent_subzone":"subzone_c"})
    sz_out = sz_lu.merge(sz_sum, on="subzone_c", how="left").merge(sz_mean, on="subzone_c", how="left").merge(sz_min, on="subzone_c", how="left")
    sz_out["in_primary_school_zone"] = (sz_out["primary_school_zone_count"].fillna(0) > 0).astype(int)
    for c in sum_cols: sz_out[c] = sz_out[c].fillna(0).astype(int)
    for c in mean_cols: sz_out[c] = sz_out[c].fillna(0).round(2)
    sz_out.to_parquet(ROOT / "hex/subzone_schools.parquet", index=False)
    print(f"  subzone_schools: {sz_out.shape}")

    # Summary
    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "input_schools": len(schools),
        "input_zones": len(zones),
        "by_level": schools["level"].value_counts().to_dict(),
        "premium_count": int(schools["is_premium"].sum()),
        "shapes": {"hex9": list(h9_out.shape), "hex8": list(h8_out.shape), "subzone": list(sz_out.shape)},
        "hexes_with_school": int((h9_out["school_count_total"] > 0).sum()),
        "hexes_in_zone": int(h9_out["in_primary_school_zone"].sum()),
    }
    with open(ROOT / "hex/schools_report.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n{json.dumps(summary, indent=2)}")


if __name__ == "__main__":
    main()
