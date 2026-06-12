"""
Plexis SGP v4 — Stage 9: amenity extras per scale.

Bundles 5 small POI layers into one parquet per scale:
  tourist_attractions   109 attractions
  hawker_centres        129 NEA official hawker centre points
  chas_clinics         1193 CHAS-subsidised clinics
  preschools           2290 ECDA preschools
  silver_zones           42 elderly-friendly traffic-calmed zone polygons

Per scale (~12 cols + key):
  tourist_attraction_count, nearest_tourist_dist_m
  hawker_centre_count, nearest_hawker_centre_dist_m
  chas_clinic_count, chas_clinics_within_500m, nearest_chas_clinic_dist_m
  preschool_count, preschools_within_400m, nearest_preschool_dist_m
  silver_zone_count, in_silver_zone
"""
import json, os, time
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from sklearn.neighbors import BallTree
import h3

ROOT = Path(__file__).parent


def _resolve_data_root():
    if os.environ.get("PLEXIS_DATA_ROOT"):
        return Path(os.environ["PLEXIS_DATA_ROOT"])
    for c in [Path("/home/azureuser/digital-atlas-sgp/data"), ROOT.parent / "data"]:
        if c.exists(): return c
    raise FileNotFoundError("data root not found")


DATA = _resolve_data_root()
SOURCES = {
    "tourist":  DATA / "amenities_updated/tourist_attractions.geojson",
    "hawker":   DATA / "amenities_updated/hawker_centres.geojson",
    "chas":     DATA / "amenities_updated/chas_clinics.geojson",
    "preschool":DATA / "new_datasets/preschools.geojson",
    "silver":   DATA / "amenities_updated/silver_zones.geojson",
}


def hex_poly_3414(cell):
    ring = [(lng, lat) for lat, lng in h3.cell_to_boundary(cell)]
    return Polygon(ring)


def main():
    t0 = time.time()
    print("Loading sources...")
    layers = {}
    for tag, path in SOURCES.items():
        g = gpd.read_file(path).to_crs(3414)
        layers[tag] = g
        print(f"  {tag:12s}  {len(g):>5,} rows  {g.geometry.iloc[0].geom_type if len(g) else 'NA'}")

    # Hex9 universe + centroids
    print("\nBuilding hex9 grid (centroids in EPSG:3414)...")
    h9 = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
    cent_4326 = np.array([h3.cell_to_latlng(c) for c in h9["hex9_id"]])
    cent_gdf = gpd.GeoDataFrame(
        {"hex9_id": h9["hex9_id"]},
        geometry=gpd.points_from_xy(cent_4326[:, 1], cent_4326[:, 0]),
        crs="EPSG:4326"
    ).to_crs(3414)
    h9_xy = np.column_stack([cent_gdf.geometry.x.values, cent_gdf.geometry.y.values])
    print(f"  {len(h9_xy):,} hex9 centroids")

    # Hex9 polygons (3414) for the silver_zone polygon overlap
    print("Building hex9 polygons for silver_zone overlap...")
    h9_polys_3414 = gpd.GeoDataFrame(
        {"hex9_id": h9["hex9_id"]},
        geometry=[hex_poly_3414(c) for c in h9["hex9_id"]],
        crs="EPSG:4326"
    ).to_crs(3414)

    out = h9[["hex9_id"]].copy()

    # Helper: assign each POI to a hex9 via h3, count per hex9
    def hex_count(g, tag, count_col, dist_col, radii=None):
        # Each POI gets hex9 via h3.latlng_to_cell from its 4326 lat/lng
        pts_4326 = g.to_crs(4326)
        hex_ids = [h3.latlng_to_cell(pt.y, pt.x, 9) for pt in pts_4326.geometry]
        cnt = pd.Series(hex_ids).value_counts().rename_axis("hex9_id").reset_index(name=count_col)
        out_local = out.merge(cnt, on="hex9_id", how="left").fillna({count_col: 0})
        out_local[count_col] = out_local[count_col].astype(int)
        # Nearest distance via BallTree
        xy = np.column_stack([g.geometry.x.values, g.geometry.y.values])
        tree = BallTree(xy)
        d, _ = tree.query(h9_xy, k=1)
        out_local[dist_col] = d[:, 0].round(1)
        # Optional radii counts
        if radii:
            for r, col in radii:
                out_local[col] = tree.query_radius(h9_xy, r=r, count_only=True).astype(int)
        return out_local

    # --- Point amenities ---
    print("\nComputing per-amenity hex9 metrics...")

    new_cols_t = ["tourist_attraction_count","nearest_tourist_dist_m"]
    t = hex_count(layers["tourist"], "tourist",
                  "tourist_attraction_count", "nearest_tourist_dist_m")
    out = out.merge(t[["hex9_id"] + new_cols_t], on="hex9_id", how="left")

    new_cols_h = ["hawker_centre_count","nearest_hawker_centre_dist_m"]
    h = hex_count(layers["hawker"], "hawker",
                  "hawker_centre_count", "nearest_hawker_centre_dist_m")
    out = out.merge(h[["hex9_id"] + new_cols_h], on="hex9_id", how="left")

    new_cols_c = ["chas_clinic_count","nearest_chas_clinic_dist_m","chas_clinics_within_500m"]
    c = hex_count(layers["chas"], "chas",
                  "chas_clinic_count", "nearest_chas_clinic_dist_m",
                  radii=[(500, "chas_clinics_within_500m")])
    out = out.merge(c[["hex9_id"] + new_cols_c], on="hex9_id", how="left")

    new_cols_p = ["preschool_count","nearest_preschool_dist_m","preschools_within_400m"]
    p = hex_count(layers["preschool"], "preschool",
                  "preschool_count", "nearest_preschool_dist_m",
                  radii=[(400, "preschools_within_400m")])
    out = out.merge(p[["hex9_id"] + new_cols_p], on="hex9_id", how="left")

    # --- Silver zones (polygon overlap) ---
    print("Computing silver-zone overlaps...")
    sj = gpd.sjoin(h9_polys_3414, layers["silver"], how="left", predicate="intersects")
    has_zone = sj[sj["SITENAME"].notna()]
    sz_count = has_zone.groupby("hex9_id").size().reset_index(name="silver_zone_count")
    out = out.merge(sz_count, on="hex9_id", how="left")
    out["silver_zone_count"] = out["silver_zone_count"].fillna(0).astype(int)
    out["in_silver_zone"] = (out["silver_zone_count"] > 0).astype(int)

    # Normalize column types
    int_cols = ["tourist_attraction_count","hawker_centre_count","chas_clinic_count",
                "chas_clinics_within_500m","preschool_count","preschools_within_400m",
                "silver_zone_count","in_silver_zone"]
    for c in int_cols:
        if c in out.columns: out[c] = out[c].fillna(0).astype(int)

    out.to_parquet(ROOT / "hex/hex9_amenities_extra.parquet", index=False)
    print(f"  hex9_amenities_extra: {out.shape}")

    # === HEX-8 ===
    print("\n--- HEX-8 ---")
    h8_uni = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")[["hex8_id"]]
    h9_with_p = out.merge(h9[["hex9_id","parent_hex8"]], on="hex9_id", how="left")
    sum_cols = ["tourist_attraction_count","hawker_centre_count","chas_clinic_count",
                "chas_clinics_within_500m","preschool_count","preschools_within_400m",
                "silver_zone_count"]
    min_cols = ["nearest_tourist_dist_m","nearest_hawker_centre_dist_m",
                "nearest_chas_clinic_dist_m","nearest_preschool_dist_m"]
    h8_sum = h9_with_p.groupby("parent_hex8")[sum_cols].sum().reset_index().rename(columns={"parent_hex8":"hex8_id"})
    h8_min = h9_with_p.groupby("parent_hex8")[min_cols].min().reset_index().rename(columns={"parent_hex8":"hex8_id"})
    h8_out = h8_uni.merge(h8_sum, on="hex8_id", how="left").merge(h8_min, on="hex8_id", how="left")
    h8_out["in_silver_zone"] = (h8_out["silver_zone_count"].fillna(0) > 0).astype(int)
    for c in sum_cols: h8_out[c] = h8_out[c].fillna(0).astype(int)
    h8_out.to_parquet(ROOT / "hex/hex8_amenities_extra.parquet", index=False)
    print(f"  hex8_amenities_extra: {h8_out.shape}")

    # === SUBZONE ===
    print("\n--- SUBZONE ---")
    sz_lu = pd.read_parquet(ROOT / "hex/subzone_land_use.parquet")[["subzone_c"]].drop_duplicates()
    h9_with_sz = out.merge(h9[["hex9_id","parent_subzone"]], on="hex9_id", how="left")
    sz_sum = h9_with_sz.groupby("parent_subzone")[sum_cols].sum().reset_index().rename(columns={"parent_subzone":"subzone_c"})
    sz_min = h9_with_sz.groupby("parent_subzone")[min_cols].min().reset_index().rename(columns={"parent_subzone":"subzone_c"})
    sz_out = sz_lu.merge(sz_sum, on="subzone_c", how="left").merge(sz_min, on="subzone_c", how="left")
    sz_out["in_silver_zone"] = (sz_out["silver_zone_count"].fillna(0) > 0).astype(int)
    for c in sum_cols: sz_out[c] = sz_out[c].fillna(0).astype(int)
    sz_out.to_parquet(ROOT / "hex/subzone_amenities_extra.parquet", index=False)
    print(f"  subzone_amenities_extra: {sz_out.shape}")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "input_counts": {tag: len(g) for tag, g in layers.items()},
        "shapes": {"hex9": list(out.shape), "hex8": list(h8_out.shape), "subzone": list(sz_out.shape)},
    }
    with open(ROOT / "hex/amenities_extra_report.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n{json.dumps(summary, indent=2)}")


if __name__ == "__main__":
    main()
