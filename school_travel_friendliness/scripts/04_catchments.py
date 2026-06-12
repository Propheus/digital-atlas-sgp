"""Step 4 — network-distance catchments per school (the Active School Travel Space).

Catchment = the set of streets reachable within MOE 1 km NETWORK distance from
the school (ego-graph on the walk network, weighted by edge length). This is the
policy-grounded definition (MOE Phase-2 home-school priority band) and is the
"active school travel space" the paper evaluates. The catchment polygon is the
reachable edges buffered 40 m (street-frontage corridor) — used in step 5 to
select crossings/parks/footpaths and to average the space-syntax nodes within.
"""
import time
import networkx as nx
import osmnx as ox
import geopandas as gpd
from shapely.ops import unary_union
from shapely.geometry import LineString
from common import ART, SVY21, CATCHMENT_M

CORRIDOR_BUF_M = 40

t0 = time.time()
G = ox.load_graphml(ART["walk_graph"])
Gu = ox.convert.to_undirected(G)
schools = gpd.read_file(ART["schools"]).to_crs(SVY21)
print(f"graph {Gu.number_of_nodes()} nodes; {len(schools)} schools ({time.time()-t0:.0f}s)", flush=True)

nn = ox.distance.nearest_nodes(Gu, schools.geometry.x.values, schools.geometry.y.values)

rows = []
for i, (_, sch) in enumerate(schools.iterrows()):
    src = nn[i]
    ego = nx.ego_graph(Gu, src, radius=CATCHMENT_M, distance="length")
    edge_geoms = []
    tot_len = 0.0
    for u, v, d in ego.edges(data=True):
        tot_len += d.get("length", 0.0)
        g = d.get("geometry")
        if g is None:
            g = LineString([(Gu.nodes[u]["x"], Gu.nodes[u]["y"]),
                            (Gu.nodes[v]["x"], Gu.nodes[v]["y"])])
        edge_geoms.append(g)
    poly = unary_union(edge_geoms).buffer(CORRIDOR_BUF_M) if edge_geoms else sch.geometry.buffer(CATCHMENT_M)
    rows.append({
        "school_id": int(sch["school_id"]), "name": sch["name"], "zone": sch["zone"],
        "n_nodes": ego.number_of_nodes(),
        "net_length_m": round(tot_len, 1),       # walkable network length within catchment
        "catch_area_m2": round(poly.area, 1),
        "geometry": poly,
    })
    if (i + 1) % 30 == 0:
        print(f"  {i+1}/{len(schools)} ({time.time()-t0:.0f}s)", flush=True)

gdf = gpd.GeoDataFrame(rows, crs=SVY21)
gdf.to_file(ART["catchments"], driver="GPKG")
print(f"saved {len(gdf)} catchments -> {ART['catchments'].name}  ({time.time()-t0:.0f}s total)", flush=True)
print(gdf[["net_length_m", "catch_area_m2", "n_nodes"]].describe().round(0).to_string())
