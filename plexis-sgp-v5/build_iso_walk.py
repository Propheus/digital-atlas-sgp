"""
Plexis SGP v4 — S2a Walk isochrone catchments (iso_*) per hex8.

Spec: SITE_SELECTION_METRICS.md §S2 (walk part; transit15 = S2b, separate build).

Real-network 10-min walk catchment (800 m at 4.8 km/h) from each hex8 centroid
over the OSM pedestrian-usable graph, replacing fixed k-ring context:

  demand  — hex9 dasymetric population distributed onto the network nodes
            inside each hex9 (node-weighted field; ~29 nodes per hex9).
            A v1 used all-or-nothing hex9-centroid snapping and undercounted
            ~2.5x (Toa Payoh Central reached 4 of ~10 contributing cells) —
            node distribution removes target-snap penalty and quantization.
  supply  — place-point grain (190,591 places, exact outlet locations)

  origin  — the hex8 ACTIVITY centroid (mean of its places' coords; fallback
            pop-weighted hex9 centroid; fallback geometric centroid), snapped
            to k=4 nearest nodes, multi-source min-Dijkstra. A v1 snapped the
            geometric centroid to a single node and was hostage to enclave
            pockets (Lorong 8 Toa Payoh: 56 of 870 nearby nodes reachable).

  reached pop  :=  sum node_pop where  snap_o + d_graph(sources, n)        <= 800 m
  reached place:=  1 where             snap_o + d_graph(sources, p) + snap_p <= 800 m

Walk graph: all OSM classes except motorway/trunk (+links) — SG primaries and
secondaries carry sidewalks. Edges undirected for pedestrians; restricted to
the giant connected component (snapping to stranded fragments would produce
phantom-empty catchments).

iso_severance_ratio = network-reached pop / euclid-800m pop on the SAME node
field. An ideal grid scores ~(1/detour)^2 ~= 0.55 (median detour 1.35); low
values mean barriers (expressways, depots, rivers), NOT missing data.

Competitor-free population ("unserved"): residents reached from the hex who do
NOT already have an outlet of the category within 800 m euclidean of their
home hex9 centroid (euclid for the served flag — documented approximation).

Output: hex/hex8_iso_walk.parquet + hex/iso_walk_report.json
"""
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import shapely
from pyproj import Transformer
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.spatial import cKDTree

ROOT = Path(__file__).parent

LIMIT_M = 800.0            # 10 min at 4.8 km/h
EXCLUDED = {"motorway", "motorway_link", "trunk", "trunk_link"}
COMPETITOR_CATS = ["cafe_coffee", "supermarket", "restaurant", "fitness_recreation"]
CHUNK = 64


def to3414(lng, lat):
    tr = Transformer.from_crs(4326, 3414, always_xy=True)
    x, y = tr.transform(np.asarray(lng), np.asarray(lat))
    return np.column_stack([x, y])


def main():
    t0 = time.time()

    # ---- 1. walk graph ----------------------------------------------------
    print("Loading roads.geojson (220 MB)...")
    import pyogrio
    roads = pyogrio.read_dataframe(ROOT.parent / "data/roads/roads.geojson",
                                   columns=["u", "v", "highway", "length"])
    n_all = len(roads)
    roads = roads[~roads["highway"].isin(EXCLUDED)]
    print(f"  {n_all:,} edges -> {len(roads):,} walkable")

    p0 = shapely.get_point(roads.geometry.values, 0)
    p1 = shapely.get_point(roads.geometry.values, -1)
    u = roads["u"].to_numpy()
    v = roads["v"].to_numpy()
    nodes, idx = np.unique(np.concatenate([u, v]), return_inverse=True)
    ui, vi = idx[: len(u)], idx[len(u):]
    n_nodes = len(nodes)
    node_xy = np.full((n_nodes, 2), np.nan)
    node_xy[ui] = to3414(shapely.get_x(p0), shapely.get_y(p0))
    node_xy[vi] = to3414(shapely.get_x(p1), shapely.get_y(p1))

    w = roads["length"].to_numpy(dtype=np.float64)
    g = coo_matrix((np.concatenate([w, w]),
                    (np.concatenate([ui, vi]), np.concatenate([vi, ui]))),
                   shape=(n_nodes, n_nodes)).tocsr()
    ncomp, labels = connected_components(g, directed=False)
    giant = np.bincount(labels).argmax()
    in_giant = labels == giant
    giant_share = in_giant.mean()
    print(f"  {n_nodes:,} nodes, {ncomp} components, giant covers {giant_share:.1%}")

    tree = cKDTree(node_xy[in_giant])
    giant_ids = np.where(in_giant)[0]

    def snap(lng, lat):
        d, k = tree.query(to3414(lng, lat))
        return d, giant_ids[k]

    # ---- 2. snap sources & targets ----------------------------------------
    h8 = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")
    h9 = pd.read_parquet(ROOT / "hex/hex9_population.parquet")
    h9ll = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")[["hex9_id", "lat", "lng"]]
    h9 = h9.merge(h9ll, on="hex9_id")
    pl = pd.read_parquet(ROOT / "places/sgp_places_final.parquet",
                         columns=["id", "latitude", "longitude", "plexis_category",
                                  "is_magnet", "in_sgp", "hex8_id"])
    pl = pl[pl["in_sgp"] != False].reset_index(drop=True)  # noqa: E712 (nullable)

    # activity centroid per hex8: places mean > pop-weighted hex9 mean > geometric
    import h3
    act = pl.groupby("hex8_id")[["longitude", "latitude"]].mean()
    h9w = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")[["hex9_id", "lat", "lng"]] \
        .merge(h9[["hex9_id", "pop_resident"]], on="hex9_id")
    h9w["hex8_of"] = [h3.cell_to_parent(c, 8) for c in h9w["hex9_id"]]
    h9w = h9w[h9w["pop_resident"] > 0]
    popw = h9w.groupby("hex8_of").apply(
        lambda x: pd.Series({"lng": np.average(x["lng"], weights=x["pop_resident"]),
                             "lat": np.average(x["lat"], weights=x["pop_resident"])}))
    h8 = h8.set_index("hex8_id")
    h8["o_lng"] = act["longitude"].reindex(h8.index)
    h8["o_lat"] = act["latitude"].reindex(h8.index)
    h8["o_lng"] = h8["o_lng"].fillna(popw["lng"].reindex(h8.index)).fillna(h8["lng"])
    h8["o_lat"] = h8["o_lat"].fillna(popw["lat"].reindex(h8.index)).fillna(h8["lat"])
    origin_src = {"places": h8.index.isin(act.index).sum(),
                  "popw": int((~h8.index.isin(act.index) & h8.index.isin(popw.index)).sum())}
    h8 = h8.reset_index()

    K_SRC = 4
    o_xy = to3414(h8["o_lng"], h8["o_lat"])
    kd, kk = tree.query(o_xy, k=K_SRC)          # (1191, 4) dists + giant-local idx
    src_nodes = giant_ids[kk]                    # original node ids
    snap_o_d = kd[:, 0]                          # min snap = the honest penalty
    snap_p_d, snap_p_n = snap(pl["longitude"], pl["latitude"])
    print(f"  origin from places: {origin_src['places']}, pop-weighted: {origin_src['popw']}, "
          f"geometric: {len(h8)-origin_src['places']-origin_src['popw']}")
    print(f"  snap>150m: hex8 origins {np.mean(snap_o_d > 150):.2%}, "
          f"places {np.mean(snap_p_d > 150):.2%}")

    # ---- 3. distribute hex9 demand onto network nodes ----------------------
    import h3
    # node -> hex9 via h3 (reverse-transform giant-component node coords)
    tr_inv = Transformer.from_crs(3414, 4326, always_xy=True)
    g_lng, g_lat = tr_inv.transform(node_xy[in_giant, 0], node_xy[in_giant, 1])
    node_h9 = np.array([h3.latlng_to_cell(la, lo, 9) for la, lo in zip(g_lat, g_lng)])

    master8 = pd.read_parquet(ROOT / "hex/hex8_all_features.parquet",
                              columns=["hex8_id", "parent_pa", "nvp_affluence_idx"])
    pa_affl = master8.groupby("parent_pa")["nvp_affluence_idx"].mean()
    h9 = h9.assign(
        affl=h9["parent_pa"].map(pa_affl).fillna(0.0),
        pop=h9["pop_resident"].fillna(0.0),
    ).set_index("hex9_id")

    nodes_per_h9 = pd.Series(node_h9).value_counts()
    h9["n_nodes"] = nodes_per_h9.reindex(h9.index).fillna(0)
    covered = h9["n_nodes"] > 0
    print(f"  populated hex9 with >=1 network node: "
          f"{(covered & (h9['pop'] > 0)).sum()}/{(h9['pop'] > 0).sum()}")

    # per-node weights (full-size arrays over ALL nodes; zero outside giant)
    node_pop = np.zeros(n_nodes)
    node_spend = np.zeros(n_nodes)
    share = (h9["pop"] / h9["n_nodes"].clip(lower=1)).reindex(node_h9).fillna(0.0).to_numpy()
    affl_n = h9["affl"].reindex(node_h9).fillna(0.0).to_numpy()
    node_pop[giant_ids] = share
    node_spend[giant_ids] = share * affl_n
    # populated hex9 with no node inside: assign to nearest giant node
    orphan = h9[covered.eq(False) & (h9["pop"] > 0)]
    if len(orphan):
        _, on = snap(orphan["lng"], orphan["lat"])
        np.add.at(node_pop, on, orphan["pop"].to_numpy())
        np.add.at(node_spend, on, (orphan["pop"] * orphan["affl"]).to_numpy())
        print(f"  {len(orphan)} populated node-less hex9 -> nearest node "
              f"({orphan['pop'].sum():,.0f} persons)")
    assert abs(node_pop.sum() - h9["pop"].sum()) < 1

    # unserved (competitor-free) node pop: served if outlet within 800m euclid
    unserved = {}
    for cat in COMPETITOR_CATS:
        out_xy = to3414(pl.loc[pl["plexis_category"] == cat, "longitude"],
                        pl.loc[pl["plexis_category"] == cat, "latitude"])
        served_d, _ = cKDTree(out_xy).query(node_xy[in_giant])
        m = np.zeros(n_nodes)
        m[giant_ids] = served_d > LIMIT_M
        unserved[cat] = node_pop * m

    # euclid 800 m baseline population on the SAME node field, SAME origin
    giant_pop = node_pop[giant_ids]
    euclid_pop = np.array([giant_pop[tree.query_ball_point(p, LIMIT_M)].sum()
                           for p in o_xy])

    # place category matrix (columns: total, magnets, competitor cats)
    cat_mat = np.column_stack(
        [np.ones(len(pl)), pl["is_magnet"].fillna(False).astype(float).to_numpy()]
        + [(pl["plexis_category"] == c).to_numpy(float) for c in COMPETITOR_CATS])

    # ---- 4. chunked dijkstra ----------------------------------------------
    print("Multi-source Dijkstra from 1,191 hex8 activity origins...")
    res = np.zeros((len(h8), 5 + 2 * len(COMPETITOR_CATS)))
    unsv = np.column_stack([unserved[c] for c in COMPETITOR_CATS])
    for i in range(len(h8)):
        d = dijkstra(g, indices=src_nodes[i], min_only=True, limit=LIMIT_M + 1)
        m_nd = d <= LIMIT_M - snap_o_d[i]        # node-field reachability
        m_pl = (d[snap_p_n] + snap_p_d + snap_o_d[i]) <= LIMIT_M
        res[i] = np.concatenate([
            [m_nd @ node_pop, m_nd @ node_spend, m_nd.sum()],
            m_nd @ unsv,
            m_pl @ cat_mat,
        ])
    cols = (["iso_walk10_pop", "iso_walk10_spend", "iso_reached_node_n"]
            + [f"iso_walk10_unserved_pop_{c}" for c in COMPETITOR_CATS]
            + ["iso_walk10_places", "iso_walk10_magnets"]
            + [f"iso_walk10_competitors_{c}" for c in COMPETITOR_CATS])
    out = pd.DataFrame(res, columns=cols)
    out.insert(0, "hex8_id", h8["hex8_id"].to_numpy())
    out["iso_euclid800_pop"] = euclid_pop
    out["iso_severance_ratio"] = np.where(
        euclid_pop >= 200, (out["iso_walk10_pop"] / np.maximum(euclid_pop, 1)), np.nan)
    out["iso_snap_dist_m"] = snap_o_d
    for c in out.columns:
        if out[c].dtype == float:
            out[c] = out[c].round(3)
    out.to_parquet(ROOT / "hex/hex8_iso_walk.parquet", index=False)

    rep = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "spec": "SITE_SELECTION_METRICS.md S2a (walk)",
        "limit_m": LIMIT_M,
        "edges_walkable": int(len(roads)),
        "nodes": int(n_nodes),
        "giant_component_share": round(float(giant_share), 4),
        "snap_gt150m_share": {"hex8": float(np.mean(snap_o_d > 150)),
                              "places": float(np.mean(snap_p_d > 150))},
        "populated_hex9_with_node": f"{(covered & (h9['pop'] > 0)).sum()}/{(h9['pop'] > 0).sum()}",
        "orphan_pop_to_nearest_node": float(orphan["pop"].sum()) if len(orphan) else 0.0,
        "places_used": int(len(pl)),
        "median_iso_pop": float(out["iso_walk10_pop"].median()),
        "median_severance_ratio": float(out["iso_severance_ratio"].median()),
        "feature_cols": [c for c in out.columns if c != "hex8_id"],
        "wall_clock_s": round(time.time() - t0, 2),
    }
    json.dump(rep, open(ROOT / "hex/iso_walk_report.json", "w"), indent=2)
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()
