"""
Build centroids.parquet — per-subzone home point (pop-weighted) and geometric centroid.

Home point = mean of HDB buildings within subzone (HDB buildings are where residents live).
If no HDB in subzone (private-only or non-residential) fall back to geometric polygon centroid.

Output schema:
  subzone_code, home_lat, home_lon, geom_lat, geom_lon, home_source (hdb|geom)
"""
import geopandas as gpd
import pandas as pd

BASE = "/home/azureuser/digital-atlas-sgp"
OUT = f"{BASE}/scenario_sim/cache/centroids.parquet"

def main():
    # --- load subzones
    sz = gpd.read_file(f"{BASE}/data/boundaries/subzones.geojson")
    if sz.crs is None:
        sz = sz.set_crs("EPSG:4326")
    else:
        sz = sz.to_crs("EPSG:4326")
    sz = sz.rename(columns={"SUBZONE_C": "subzone_code"})[["subzone_code", "geometry"]]
    print(f"[02] subzones: {len(sz)}")

    # --- geometric centroids (done in metric CRS for accuracy)
    sz_metric = sz.to_crs("EPSG:3414")  # SVY21 / Singapore TM
    geom_cent = sz_metric.geometry.centroid.to_crs("EPSG:4326")
    sz["geom_lat"] = geom_cent.y
    sz["geom_lon"] = geom_cent.x

    # --- load HDB buildings (54 MB)
    hdb = gpd.read_file(f"{BASE}/data/housing/hdb_existing_buildings.geojson")
    if hdb.crs is None:
        hdb = hdb.set_crs("EPSG:4326")
    else:
        hdb = hdb.to_crs("EPSG:4326")
    print(f"[02] HDB buildings: {len(hdb)}")

    # Use representative_point (guaranteed inside polygon) for each HDB building
    hdb_points = hdb.copy()
    hdb_points["geometry"] = hdb_points.geometry.representative_point()

    # Spatial join HDB points → subzones
    hdb_joined = gpd.sjoin(hdb_points, sz[["subzone_code", "geometry"]], how="inner", predicate="within")
    print(f"[02] HDB points joined to subzones: {len(hdb_joined)}")

    hdb_joined["lat"] = hdb_joined.geometry.y
    hdb_joined["lon"] = hdb_joined.geometry.x

    # Pop-weighted centroid = mean of HDB building points per subzone
    hdb_cent = hdb_joined.groupby("subzone_code").agg(
        home_lat=("lat", "mean"),
        home_lon=("lon", "mean"),
        hdb_count=("lat", "size"),
    ).reset_index()
    print(f"[02] subzones with HDB: {len(hdb_cent)}")

    # --- merge with all subzones
    out = sz[["subzone_code", "geom_lat", "geom_lon"]].merge(hdb_cent, on="subzone_code", how="left")
    out["home_source"] = out["hdb_count"].notna().map({True: "hdb", False: "geom"})
    out["home_lat"] = out["home_lat"].fillna(out["geom_lat"])
    out["home_lon"] = out["home_lon"].fillna(out["geom_lon"])
    out["hdb_count"] = out["hdb_count"].fillna(0).astype(int)

    print(f"[02] source breakdown: {out['home_source'].value_counts().to_dict()}")

    out.to_parquet(OUT, index=False)
    print(f"[02] wrote {OUT}  shape={out.shape}")
    print(f"[02] sample:\n{out.head(5).to_string()}")

if __name__ == "__main__":
    main()
