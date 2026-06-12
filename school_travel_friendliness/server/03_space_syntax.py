"""Step 3 — angular space-syntax centralities (cityseer) on the walk network.

angular harmonic closeness -> Integration ; angular betweenness -> Choice.
Computed on the full network, distance-thresholded (800/1600 m), so no clip
artifacts. Topology built from edge LineStrings (robust to graphml round-trip).
"""
import time
import osmnx as ox
from cityseer.tools import io, graphs
from cityseer.metrics import networks
from common import ART, SVY21, SYNTAX_DIST

t0 = time.time()
G = ox.load_graphml(ART["walk_graph"])
print(f"graph {G.number_of_nodes()} nodes / {G.number_of_edges()} edges", flush=True)

edges = ox.graph_to_gdfs(G, nodes=False).reset_index()[["geometry"]]
G_cs = io.nx_from_generic_geopandas(edges)          # primal
G_dual = graphs.nx_to_dual(G_cs)                     # dual graph for ANGULAR analysis
nodes_gdf, edges_gdf, net = io.network_structure_from_nx(G_dual, crs=SVY21)
print(f"cityseer dual {len(nodes_gdf)} nodes / {len(edges_gdf)} edges ({time.time()-t0:.0f}s)", flush=True)

# angular (simplest-path) centrality on the dual: Integration (harmonic closeness) + Choice (betweenness)
nodes_gdf = networks.node_centrality_simplest(net, nodes_gdf, distances=SYNTAX_DIST)
print(f"angular centrality done ({time.time()-t0:.0f}s)", flush=True)

print("columns:", [c for c in nodes_gdf.columns if c != "geometry"])
nodes_gdf.to_file(ART["syntax_nodes"], driver="GPKG")
print(f"saved -> {ART['syntax_nodes'].name} ({time.time()-t0:.0f}s total)", flush=True)
