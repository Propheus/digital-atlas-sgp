"""Step 2 — download Singapore walk network + amenity layers from OSM (on server).

Replaces both the network build and the raw-layer loads. Multi-source big data,
fetched server-side via Overpass:
  walk network  (footways/paths/pedestrian)  -> space syntax + catchments
  crossings     highway=crossing             -> safety
  signals       highway=traffic_signals      -> safety
  parks         leisure/landuse green        -> greenery
  bus stops     highway=bus_stop             -> transport-convenience driver
  mrt stations  railway=station              -> transport-convenience driver
"""
import time
import osmnx as ox
from common import ART, BBOX, SVY21

ox.settings.use_cache = True
ox.settings.log_console = False
t0 = time.time()

def fetch_features(tags, keep_geom=None):
    g = ox.features_from_bbox(bbox=BBOX, tags=tags).to_crs(SVY21).reset_index()
    g = g[["geometry"]].copy()
    if keep_geom == "point":
        g["geometry"] = g.geometry.centroid
        g = g[g.geom_type == "Point"]
    elif keep_geom == "poly":
        g = g[g.geom_type.isin(["Polygon", "MultiPolygon"])]
    return g

print("walk network...", flush=True)
G = ox.graph_from_bbox(bbox=BBOX, network_type="walk", simplify=True)
G = ox.project_graph(G, to_crs=SVY21)
ox.save_graphml(G, ART["walk_graph"])
print(f"  {G.number_of_nodes()} nodes / {G.number_of_edges()} edges ({time.time()-t0:.0f}s)", flush=True)

for name, tags, kind in [
    ("crossings", {"highway": "crossing", "footway": "crossing"}, "point"),
    ("signals",   {"highway": "traffic_signals"}, "point"),
    ("parks",     {"leisure": ["park", "garden", "nature_reserve", "recreation_ground"],
                   "landuse": ["recreation_ground", "grass", "forest"]}, "poly"),
    ("bus",       {"highway": "bus_stop"}, "point"),
    ("mrt",       {"railway": ["station", "halt"], "station": "subway"}, "point"),
]:
    try:
        g = fetch_features(tags, kind)
        g.to_file(ART[name], driver="GPKG")
        print(f"  {name}: {len(g)} -> {ART[name].name} ({time.time()-t0:.0f}s)", flush=True)
    except Exception as e:
        print(f"  {name}: ERROR {e}", flush=True)

print(f"done ({time.time()-t0:.0f}s)", flush=True)
