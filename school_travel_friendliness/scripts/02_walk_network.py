"""Step 2 — download + cache Singapore pedestrian network (osmnx), projected SVY21.

The paper builds the walking route network via the Amap pedestrian routing API.
Amap is China-only; for Singapore we use the OSM walk network (sidewalks, paths,
footways, pedestrian streets) which is dense and well-maintained for SG.
"""
import time
import osmnx as ox
from common import ART, SVY21

ox.settings.use_cache = True
ox.settings.log_console = False

# Singapore mainland + near islands bounding box
NORTH, SOUTH, EAST, WEST = 1.480, 1.205, 104.050, 103.590

t0 = time.time()
print("downloading SG walk network (bbox)...", flush=True)
try:  # osmnx >=2 uses bbox tuple; 1.9.x uses kwargs
    G = ox.graph_from_bbox(bbox=(WEST, SOUTH, EAST, NORTH), network_type="walk", simplify=True)
except TypeError:
    G = ox.graph_from_bbox(north=NORTH, south=SOUTH, east=EAST, west=WEST,
                           network_type="walk", simplify=True)
print(f"raw: {G.number_of_nodes()} nodes / {G.number_of_edges()} edges "
      f"({time.time()-t0:.0f}s)", flush=True)

G = ox.project_graph(G, to_crs=SVY21)
ox.save_graphml(G, ART["walk_graph"])
print(f"saved -> {ART['walk_graph'].name}  ({time.time()-t0:.0f}s total)", flush=True)
