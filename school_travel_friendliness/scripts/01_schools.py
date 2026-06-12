"""Step 1 — primary schools as points (SVY21), with region for spatial-pattern analysis."""
import json
import geopandas as gpd
from shapely.geometry import Point
from common import SRC, ART, WGS84, SVY21

schools = json.load(open(SRC["schools"]))
prim = [s for s in schools if s["type"] == "PRIMARY"]
gdf = gpd.GeoDataFrame(
    [{"name": s["name"], "zone": s.get("zone"), "postal": s.get("postal_code")} for s in prim],
    geometry=[Point(s["lon"], s["lat"]) for s in prim],
    crs=WGS84,
).to_crs(SVY21)
gdf["school_id"] = range(len(gdf))
gdf.to_file(ART["schools"], driver="GeoJSON")
print(f"{len(gdf)} primary schools -> {ART['schools'].name}")
print(gdf["zone"].value_counts().to_dict())
