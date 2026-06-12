"""
Build rail_graph.pkl + station_times.parquet — MRT/LRT routing network.

v0 approach: stations as nodes, K-nearest-neighbor edges with Euclidean × meander
factor as edge weights. Shortest path via Dijkstra gives station-to-station rail
distance. Convert to minutes at 35 km/h + 0.5 min dwell per stop.

This is a simplification. The actual rail topology (rail_lines.geojson) has
1363 segments that do not form a cleanly-connected network when clustered by
endpoint proximity — probably because the geojson represents individual track
sub-segments without shared endpoints at junctions. v0.5 can do proper topology
inference.

Known limitations of KNN approach:
  - Doesn't know about lines (e.g., two stations on parallel lines but geographically
    close will get a direct edge even if the real trip requires a transfer)
  - Doesn't model interchange transfer times
  - KNN graph can miss long-distance direct connections (e.g., express segments)

These are acceptable for v0: what we need is *roughly correct* travel times for
calibration of the gravity model and sensitivity to scenario changes. We validate
against 10 known OD pairs.
"""
import geopandas as gpd
import pandas as pd
import networkx as nx
import numpy as np
import pickle
import sys
import time
from shapely.geometry import Point
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components as cc_sparse

def log(msg):
    print(f"[03] [{time.strftime('%H:%M:%S')}] {msg}", flush=True)

BASE = "/home/azureuser/digital-atlas-sgp"
OUT_GRAPH = f"{BASE}/scenario_sim/cache/rail_graph.pkl"
OUT_TIMES = f"{BASE}/scenario_sim/cache/station_times.parquet"
OUT_STATIONS = f"{BASE}/scenario_sim/cache/stations.parquet"

MRT_SPEED_KMH = 42.0            # SGP MRT network average (calibrated to in-vehicle times)
DWELL_MIN_PER_STOP = 0.35       # avg dwell per intermediate stop (short for SGP)
KNN_K = 4                       # connect each station to its K nearest neighbours
RAIL_MEANDER = 1.08             # rail routes are slightly longer than Euclidean

def main():
    # --- load rail segments (in metric CRS for distance math)
    log("loading rail_lines.geojson...")
    lines = gpd.read_file(f"{BASE}/data/transit/rail_lines.geojson").to_crs("EPSG:3414")
    if "RAIL_TYPE" in lines.columns:
        lines = lines[lines["RAIL_TYPE"].isin(["MRT", "LRT"])]
    log(f"rail segments (MRT/LRT): {len(lines)}")

    # --- load stations
    log("loading train_stations_mar2026.geojson...")
    stations = gpd.read_file(f"{BASE}/data/transit_updated/train_stations_mar2026.geojson").to_crs("EPSG:3414")
    stations["station_name"] = stations.get("STN_NAM_DE", stations.get("STN_NAM"))
    stations["station_type"] = stations.get("TYP_CD_DES", "MRT")
    stations["geometry"] = stations.geometry.centroid
    stations = stations[stations["station_name"].notna()].reset_index(drop=True)
    stations["station_id"] = [f"STN_{i:04d}" for i in range(len(stations))]
    log(f"stations: {len(stations)}")

    # --- Build KNN graph: each station connects to its K nearest neighbours
    log(f"building KNN rail graph (K={KNN_K})...")
    sx = stations.geometry.x.to_numpy()
    sy = stations.geometry.y.to_numpy()
    station_pts = np.column_stack([sx, sy])

    from scipy.spatial import cKDTree
    tree_stn = cKDTree(station_pts)
    # K+1 because nearest neighbour is the station itself
    dists, idxs = tree_stn.query(station_pts, k=KNN_K + 1)

    G = nx.Graph()
    for i in range(len(stations)):
        G.add_node(i, x=float(sx[i]), y=float(sy[i]),
                   station_id=stations.iloc[i]["station_id"],
                   name=stations.iloc[i]["station_name"])

    edge_count = 0
    for i in range(len(stations)):
        for k in range(1, KNN_K + 1):  # skip self (k=0)
            j = int(idxs[i, k])
            d_m = float(dists[i, k]) * RAIL_MEANDER
            if G.has_edge(i, j):
                if G.edges[i, j]["dist_m"] > d_m:
                    G.edges[i, j]["dist_m"] = d_m
            else:
                G.add_edge(i, j, dist_m=d_m)
                edge_count += 1
    log(f"KNN graph: {G.number_of_nodes()} stations, {G.number_of_edges()} edges ({edge_count} new)")

    cc_list = sorted(nx.connected_components(G), key=len, reverse=True)
    log(f"connected components: {len(cc_list)}  sizes (top 5): {[len(c) for c in cc_list[:5]]}")
    # With K=4, we expect either 1 connected component or a small number
    cc = cc_list

    # If somehow not fully connected, add bridges between CCs using nearest-neighbour across
    if len(cc_list) > 1:
        log("bridging disconnected components...")
        while len(cc_list) > 1:
            big = cc_list[0]
            rest = set().union(*cc_list[1:])
            big_idx = sorted(big)
            rest_idx = sorted(rest)
            big_pts = station_pts[big_idx]
            rest_pts = station_pts[rest_idx]
            t = cKDTree(rest_pts)
            d, idx = t.query(big_pts, k=1)
            best = int(np.argmin(d))
            src = big_idx[best]
            dst = rest_idx[idx[best]]
            bridge_d = float(d[best]) * RAIL_MEANDER
            G.add_edge(src, dst, dist_m=bridge_d)
            log(f"  bridge {src} <-> {dst}: {bridge_d:.0f}m")
            cc_list = sorted(nx.connected_components(G), key=len, reverse=True)
        log(f"after bridging: {len(cc_list)} component(s)")
        cc = cc_list

    # --- With KNN approach stations ARE the graph nodes (i = station index)
    stations["x"] = sx
    stations["y"] = sy
    stations["snap_node"] = np.arange(len(stations))

    # --- all-pairs station-to-station distances (Dijkstra)
    log("computing all-pairs station distances via Dijkstra...")
    sids = stations["station_id"].tolist()
    n_stn = len(stations)
    dist_matrix = np.full((n_stn, n_stn), np.inf, dtype=np.float32)
    for src in range(n_stn):
        lengths = nx.single_source_dijkstra_path_length(G, src, weight="dist_m")
        for dst, d_m in lengths.items():
            dist_matrix[src, int(dst)] = d_m

    # Convert to travel time: base ride at MRT_SPEED_KMH + 0.5 min dwell per ~1.2km intermediate stop
    log("converting distances to travel times...")
    speed_m_per_min = MRT_SPEED_KMH * 1000 / 60
    ride_time = dist_matrix / speed_m_per_min
    stop_count = np.clip(dist_matrix / 1200.0 - 1, 0, None)
    time_matrix = ride_time + stop_count * DWELL_MIN_PER_STOP
    time_matrix[dist_matrix == np.inf] = np.inf
    np.fill_diagonal(time_matrix, 0.0)

    # --- write outputs
    with open(OUT_GRAPH, "wb") as f:
        pickle.dump({"graph": G, "station_ids": sids}, f)
    log(f"wrote graph: {OUT_GRAPH}")

    stations_gdf = gpd.GeoDataFrame(
        stations[["station_id", "station_name", "station_type", "x", "y"]].copy(),
        geometry=gpd.points_from_xy(stations["x"], stations["y"]),
        crs="EPSG:3414",
    ).to_crs("EPSG:4326")
    stations_out = stations[["station_id", "station_name", "station_type"]].copy()
    stations_out["lat"] = stations_gdf.geometry.y.values
    stations_out["lon"] = stations_gdf.geometry.x.values
    stations_out.to_parquet(OUT_STATIONS, index=False)
    log(f"wrote stations: {OUT_STATIONS}  ({len(stations_out)})")

    # Times matrix — long parquet (filter out inf; keep self)
    finite_mask = np.isfinite(time_matrix)
    ii, jj = np.where(finite_mask)
    df = pd.DataFrame({
        "from_station": [sids[i] for i in ii],
        "to_station":   [sids[j] for j in jj],
        "time_min":     time_matrix[ii, jj].astype(float),
        "dist_m":       dist_matrix[ii, jj].astype(float),
    })
    df.to_parquet(OUT_TIMES, index=False)
    log(f"wrote station times: {OUT_TIMES}  ({len(df):,} finite pairs)")

    # For downstream code expecting these names
    snapped_stations = stations
    id_to_idx = {s: i for i, s in enumerate(sids)}

    # Spot-check: a few known pairs
    def find(name):
        m = snapped_stations[snapped_stations["station_name"].str.contains(name, case=False, na=False)]
        return m.iloc[0]["station_id"] if len(m) else None

    for a, b, expected in [
        ("JURONG EAST", "CITY HALL", "~20 min"),
        ("ANG MO KIO", "BISHAN", "~4 min"),
        ("TAMPINES", "JURONG EAST", "~45 min"),
        ("WOODLANDS", "CHANGI", "~55 min"),
    ]:
        sa, sb = find(a), find(b)
        if sa and sb:
            ia, ib = id_to_idx[sa], id_to_idx[sb]
            t = time_matrix[ia, ib]
            print(f"[03] spot-check  {a:15s} -> {b:15s}: {t:5.1f} min  (expected {expected})")
        else:
            print(f"[03] spot-check  {a} -> {b}: stations not found")

if __name__ == "__main__":
    main()
