"""Step 4 — 1 km network-distance catchments per school (parallel, 16 cores).

Catchment = streets reachable within 1 km network distance (MOE priority band),
as the corridor polygon (reachable edges buffered 40 m). Parallelised with a
fork-based process pool; the undirected graph is a module global shared
copy-on-write across workers.
"""
import time
from multiprocessing import Pool
import networkx as nx
import osmnx as ox
import geopandas as gpd
from shapely.ops import unary_union
from shapely.geometry import LineString
from common import ART, SVY21, CATCHMENT_M, CORRIDOR_BUF_M

t0 = time.time()
G = ox.load_graphml(ART["walk_graph"])
Gu = ox.convert.to_undirected(G)
schools = gpd.read_file(ART["schools"]).to_crs(SVY21)
nn = ox.distance.nearest_nodes(Gu, schools.geometry.x.values, schools.geometry.y.values)
print(f"graph {Gu.number_of_nodes()} nodes; {len(schools)} schools ({time.time()-t0:.0f}s)", flush=True)


def catchment(args):
    i, src = args
    ego = nx.ego_graph(Gu, src, radius=CATCHMENT_M, distance="length")
    geoms, tot = [], 0.0
    for u, v, d in ego.edges(data=True):
        tot += d.get("length", 0.0)
        g = d.get("geometry")
        if g is None:
            g = LineString([(Gu.nodes[u]["x"], Gu.nodes[u]["y"]),
                            (Gu.nodes[v]["x"], Gu.nodes[v]["y"])])
        geoms.append(g)
    poly = unary_union(geoms).buffer(CORRIDOR_BUF_M) if geoms else None
    return i, ego.number_of_nodes(), round(tot, 1), poly


with Pool(12) as pool:
    res = pool.map(catchment, list(enumerate(nn)))

rows = []
for i, nnodes, tot, poly in sorted(res):
    sch = schools.iloc[i]
    if poly is None:
        poly = sch.geometry.buffer(CATCHMENT_M)
    rows.append({"school_id": int(sch["school_id"]), "name": sch["name"], "zone": sch["zone"],
                 "subzone_c": sch.get("parent_subzone_c"),
                 "n_nodes": nnodes, "net_length_m": tot,
                 "catch_area_m2": round(poly.area, 1), "geometry": poly})

gdf = gpd.GeoDataFrame(rows, crs=SVY21)
gdf.to_file(ART["catchments"], driver="GPKG")
print(f"saved {len(gdf)} catchments -> {ART['catchments'].name} ({time.time()-t0:.0f}s total)", flush=True)
print(gdf[["net_length_m", "catch_area_m2", "n_nodes"]].describe().round(0).to_string())
