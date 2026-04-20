"""
Hex v10 — improved influence features (replaces old k-ring aggregation).

Evidence from validation:
    Old k-ring (150 features): +2% PA-match accuracy (contrast/rank features HURT)
    New influence (120 features): +34% PA-match accuracy (spatial k=5 + transit-augmented)

Two complementary neighborhoods per hex:
    SPATIAL:  H3 k=5 ring (90 neighbors, ~875m radius, walkable/driving reach)
    TRANSIT:  MRT-connected stations + their catchment (variable reach via rail network)

For each neighborhood, two aggregations:
    max_influence: features of the single densest neighbor (by pc_total) — captures
                   "what is the biggest commercial center in my reach?"
    place_weighted_mean: average of neighbors weighted by pc_total — captures
                        "what does the typical commercial activity look like around me?"

Output:
    data/hex_v10/hex_influence.parquet   (7,318 × 125)

Schema:
    hex_id
    # spatial k=5 (30 each)
    sp_max_{basis_feature}          max-influence neighbor's feature value
    sp_pw_{basis_feature}           place-weighted mean of k=5 ring

    # transit-augmented (30 each)
    tr_max_{basis_feature}          max-influence via transit reach
    tr_pw_{basis_feature}           place-weighted mean via transit reach

    # scalar context (4)
    sp_max_distance_rings           H3 distance to spatial max-influence hex
    sp_max_pc_total                 that hex's pc_total
    tr_nearest_station_rings        H3 distance to nearest MRT station hex
    tr_reachable_hexes              total hexes in transit-augmented reach

Also writes:
    data/hex_v10/hex_influence_graph.npz  (sparse adjacency for downstream GNN use)
"""
from __future__ import annotations

from collections import defaultdict
from math import radians, cos, sin, asin, sqrt as msqrt
from pathlib import Path

import h3
import numpy as np
import pandas as pd
import scipy.sparse as sp

ROOT = Path(__file__).resolve().parents[3]
V10 = ROOT / "data" / "hex_v10"
MERGED = V10 / "hex_features_v10_merged.parquet"
STATIONS = ROOT / "data" / "transit_updated" / "train_stations_mar2026.geojson"
OUT = V10 / "hex_influence.parquet"
OUT_GRAPH = V10 / "hex_influence_graph.npz"

INFLUENCE_BASIS = [
    "population", "elderly_count", "children_count", "walking_dependent_count",
    "bldg_count", "hdb_blocks", "bldg_footprint_sqm", "residential_floor_area_sqm",
    "mrt_stations", "bus_stops",
    "pc_total", "pc_cat_restaurant", "pc_cat_cafe_coffee", "pc_cat_shopping_retail",
    "pc_cat_hawker_street_food", "pc_cat_health_medical", "pc_cat_education",
    "pc_cat_office_workspace", "pc_cat_bar_nightlife",
    "pc_unique_brands", "pc_cat_entropy",
    "lu_residential_pct", "lu_commercial_pct", "lu_business_pct", "avg_gpr",
    "mg_mean_transit", "mg_mean_competitor", "mg_mean_complementary", "mg_mean_demand",
    "mg_mean_anchor_count",
]

SPATIAL_K = 5  # k=5 ring (~90 neighbors, ~875m radius)
TRANSIT_STATION_RADIUS_M = 5000  # station-to-station edge threshold
TRANSIT_CATCHMENT_K = 2  # ring around each connected station


def haversine(lat1, lng1, lat2, lng2):
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    return 2 * 6371 * asin(msqrt(a)) * 1000


def main() -> None:
    import geopandas as gpd

    print("Loading merged base...")
    df = pd.read_parquet(MERGED)
    hex_ids = df["hex_id"].tolist()
    id_to_idx = {h: i for i, h in enumerate(hex_ids)}
    n = len(hex_ids)
    pc_arr = df["pc_total"].fillna(0).to_numpy()
    X = df[INFLUENCE_BASIS].astype("float64").fillna(0).to_numpy()
    f = X.shape[1]
    print(f"  {n} hexes × {f} influence basis features")

    # ---- Build transit graph ----
    print("Building transit graph...")
    g = gpd.read_file(STATIONS).to_crs(4326)
    pts = g.geometry.representative_point()
    station_hexes = set()
    station_list = []
    for x, y in zip(pts.x, pts.y):
        hid = h3.latlng_to_cell(y, x, 9)
        if hid in id_to_idx:
            station_hexes.add(hid)
            station_list.append({"hex_id": hid, "lat": y, "lng": x})
    stations = pd.DataFrame(station_list).drop_duplicates("hex_id").to_dict("records")
    print(f"  unique station hexes: {len(stations)}")

    # Station-to-station edges (Haversine < 5km)
    station_adj: dict[str, set[str]] = defaultdict(set)
    for i, si in enumerate(stations):
        for j, sj in enumerate(stations):
            if i >= j:
                continue
            d = haversine(si["lat"], si["lng"], sj["lat"], sj["lng"])
            if d < TRANSIT_STATION_RADIUS_M:
                station_adj[si["hex_id"]].add(sj["hex_id"])
                station_adj[sj["hex_id"]].add(si["hex_id"])
    n_edges = sum(len(v) for v in station_adj.values()) // 2
    print(f"  station-station transit edges: {n_edges}")

    # For each hex, find nearest station
    station_set = set(s["hex_id"] for s in stations)
    nearest_station: dict[str, str | None] = {}
    nearest_station_dist: dict[str, int] = {}
    for hid in hex_ids:
        if hid in station_set:
            nearest_station[hid] = hid
            nearest_station_dist[hid] = 0
        else:
            found = False
            for k in range(1, 30):
                ring = h3.grid_ring(hid, k)
                hits = [h for h in ring if h in station_set]
                if hits:
                    nearest_station[hid] = hits[0]
                    nearest_station_dist[hid] = k
                    found = True
                    break
            if not found:
                nearest_station[hid] = None
                nearest_station_dist[hid] = 999

    # ---- Compute influence features ----
    print("Computing spatial + transit influence features...")
    sp_max = np.zeros((n, f))
    sp_pw = np.zeros((n, f))
    sp_max_dist = np.zeros(n)
    sp_max_pc = np.zeros(n)
    tr_max = np.zeros((n, f))
    tr_pw = np.zeros((n, f))
    tr_nearest_rings = np.zeros(n)
    tr_reachable = np.zeros(n)

    # Also build sparse adjacency for potential GNN use
    adj_rows, adj_cols, adj_weights = [], [], []

    for i, hid in enumerate(hex_ids):
        # --- SPATIAL k=5 ---
        disk = h3.grid_disk(hid, SPATIAL_K)
        sp_nbrs = [id_to_idx[h] for h in disk if h in id_to_idx and h != hid]
        if sp_nbrs:
            best_j = max(sp_nbrs, key=lambda j: pc_arr[j])
            sp_max[i] = X[best_j]
            sp_max_dist[i] = h3.grid_distance(hid, hex_ids[best_j])
            sp_max_pc[i] = pc_arr[best_j]
            w = np.array([pc_arr[j] for j in sp_nbrs])
            tw = w.sum()
            if tw > 0:
                sp_pw[i] = X[sp_nbrs].T @ w / tw

            # adjacency: connect to k=1 ring for sparse graph
            for h in h3.grid_ring(hid, 1):
                if h in id_to_idx and h != hid:
                    j = id_to_idx[h]
                    adj_rows.append(i)
                    adj_cols.append(j)
                    adj_weights.append(1.0)

        # --- TRANSIT ---
        tr_nearest_rings[i] = nearest_station_dist.get(hid, 999)
        ns = nearest_station.get(hid)
        transit_hexes = set()
        if ns and ns in station_adj:
            connected = station_adj[ns]
            for sh in connected:
                transit_hexes |= set(h3.grid_disk(sh, TRANSIT_CATCHMENT_K)) & set(id_to_idx.keys())
        tr_nbrs = list(transit_hexes - {hid})
        tr_reachable[i] = len(tr_nbrs)
        if tr_nbrs:
            tr_nbr_idx = [id_to_idx[h] for h in tr_nbrs]
            best_j = max(tr_nbr_idx, key=lambda j: pc_arr[j])
            tr_max[i] = X[best_j]
            w = np.array([pc_arr[j] for j in tr_nbr_idx])
            tw = w.sum()
            if tw > 0:
                tr_pw[i] = X[tr_nbr_idx].T @ w / tw

            # transit adjacency edges (to station hexes)
            if ns and ns in id_to_idx:
                j = id_to_idx[ns]
                adj_rows.append(i)
                adj_cols.append(j)
                adj_weights.append(2.0)  # stronger weight for transit link

    # ---- Assemble output ----
    out = pd.DataFrame({"hex_id": hex_ids})
    for k, M in [("sp_max_", sp_max), ("sp_pw_", sp_pw), ("tr_max_", tr_max), ("tr_pw_", tr_pw)]:
        for j, feat in enumerate(INFLUENCE_BASIS):
            out[f"{k}{feat}"] = M[:, j]
    out["sp_max_distance_rings"] = sp_max_dist
    out["sp_max_pc_total"] = sp_max_pc
    out["tr_nearest_station_rings"] = tr_nearest_rings
    out["tr_reachable_hexes"] = tr_reachable

    print(f"Output shape: {out.shape}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT, index=False)
    print(f"Wrote {OUT}")

    # Save sparse graph
    adj = sp.csr_matrix(
        (adj_weights, (adj_rows, adj_cols)), shape=(n, n)
    )
    sp.save_npz(OUT_GRAPH, adj)
    print(f"Wrote {OUT_GRAPH} ({adj.nnz} edges)")

    # Quick summary
    print()
    print("Feature groups in hex_influence.parquet:")
    print(f"  sp_max_*:  {f} features (spatial k=5 max-influence neighbor)")
    print(f"  sp_pw_*:   {f} features (spatial k=5 place-weighted mean)")
    print(f"  tr_max_*:  {f} features (transit-augmented max-influence)")
    print(f"  tr_pw_*:   {f} features (transit-augmented place-weighted)")
    print(f"  scalars:   4 features (distances, reachable count)")
    print(f"  total:     {out.shape[1] - 1} features + hex_id")


if __name__ == "__main__":
    main()
