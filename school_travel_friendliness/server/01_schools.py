"""Step 1 — primary schools as points from the v4 places master (server-native)."""
import geopandas as gpd
import pandas as pd
from common import SRC, ART, WGS84, SVY21

d = pd.read_parquet(SRC["places"], columns=["name", "primary_category", "latitude", "longitude",
                                            "parent_region", "parent_subzone_c"])
mask = d["name"].astype(str).str.contains("primary school", case=False, na=False)
s = d[mask].dropna(subset=["latitude", "longitude"]).copy()
# dedupe by name (keep first)
s = s.sort_values("name").drop_duplicates("name").reset_index(drop=True)
gdf = gpd.GeoDataFrame(
    s[["name", "parent_region", "parent_subzone_c"]].rename(columns={"parent_region": "zone"}),
    geometry=gpd.points_from_xy(s["longitude"], s["latitude"]), crs=WGS84,
).to_crs(SVY21)
gdf["school_id"] = range(len(gdf))
gdf.to_file(ART["schools"], driver="GeoJSON")
print(f"{len(gdf)} primary schools -> {ART['schools'].name}")
print(gdf["zone"].value_counts().to_dict())
