"""Step 3 — space-syntax centralities on the walk network (cityseer).

The paper uses space syntax (integration, choice/connectivity) computed on the
walking network. cityseer angular ("simplest path") analysis is the modern
equivalent of axial/segment space-syntax:
  - angular HARMONIC closeness  -> Integration  (how easy to reach all else)
  - angular BETWEENNESS         -> Choice        (through-movement potential)
We also keep metric (shortest-path) closeness density as a connectivity measure.
Distance thresholds 800 m and 1600 m bracket the MOE 1 km / 2 km catchment tiers.
Computed on the FULL network (distance-thresholded) so there are no subgraph
clip artifacts — catchment aggregation happens in step 5.
"""
import time
import osmnx as ox
from cityseer.tools import io
from cityseer.metrics import networks
from common import ART, SVY21

DISTANCES = [800, 1600]

t0 = time.time()
print("loading walk graph...", flush=True)
G = ox.load_graphml(ART["walk_graph"])
print(f"  {G.number_of_nodes()} nodes / {G.number_of_edges()} edges", flush=True)

print("converting to cityseer + building network structure...", flush=True)
# Build cityseer topology directly from edge LineStrings (robust to osmnx
# graphml round-trip quirks that break io.nx_from_osm_nx).
edges = ox.graph_to_gdfs(G, nodes=False).reset_index()[["geometry"]]
G_cs = io.nx_from_generic_geopandas(edges)
nodes_gdf, edges_gdf, net = io.network_structure_from_nx(G_cs, crs=SVY21)
print(f"  cityseer: {len(nodes_gdf)} nodes / {len(edges_gdf)} edges  ({time.time()-t0:.0f}s)", flush=True)

print("angular (simplest-path) centrality: Integration + Choice...", flush=True)
nodes_gdf = networks.node_centrality_simplest(net, nodes_gdf, distances=DISTANCES)
print(f"  done ({time.time()-t0:.0f}s)", flush=True)

print("metric (shortest-path) centrality: connectivity/density...", flush=True)
nodes_gdf = networks.node_centrality_shortest(net, nodes_gdf, distances=DISTANCES,
                                              compute_betweenness=False)
print(f"  done ({time.time()-t0:.0f}s)", flush=True)

cc = [c for c in nodes_gdf.columns if c not in ("geometry", "ns_node_idx")]
print("metric columns produced:", cc)
nodes_gdf.to_file(ART["syntax_nodes"], driver="GPKG")
print(f"saved -> {ART['syntax_nodes'].name}  ({time.time()-t0:.0f}s total)", flush=True)
