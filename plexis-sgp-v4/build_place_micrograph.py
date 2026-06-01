"""
Plexis SGP v4 — Stage 8: per-place micrograph (NETWORK distances).

Walking distances are computed over the OSM pedestrian graph (footway / path /
service / residential / cycleway / tertiary / secondary / primary / etc.;
motorway + trunk are excluded). Each entity (place / MRT exit / bus stop) is
snapped to its nearest walkable node; walking distance = snap_delta + network
shortest-path + neighbor_snap_delta.

For each of 190,591 places, compute four context dimensions:
  TRANSIT       — true network walking distance to nearest MRT exit + bus stop
                  (multi-source SSSP from all transit nodes)
  COMPETITION   — same-category density at 400m / 800m network walk
  COMPLEMENTARY — category-mix support per category playbook
  ANCHOR        — magnet density and distance-decayed strength per playbook

Outputs:
  places/sgp_places_micrograph.parquet     id + ~18 pmg_* cols
  places/place_micrograph_report.json
"""
import json, os, time
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
from sklearn.neighbors import BallTree
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

ROOT = Path(__file__).parent


def _resolve_data_root():
    if os.environ.get("PLEXIS_DATA_ROOT"):
        return Path(os.environ["PLEXIS_DATA_ROOT"])
    for c in [Path("/home/azureuser/digital-atlas-sgp/data"), ROOT.parent / "data"]:
        if c.exists(): return c
    raise FileNotFoundError("data root not found")

DATA = _resolve_data_root()
ROADS_GJ = DATA / "roads/roads.geojson"
MRT_EXITS_GJ = DATA / "transit/mrt_exits.geojson"
BUS_STOPS_GJ = DATA / "transit_updated/bus_stops_mar2026.geojson"

# Highway types EXCLUDED from pedestrian graph (vehicular-only)
NONWALKABLE_HIGHWAYS = {"motorway", "motorway_link", "trunk", "trunk_link"}

R_NEAR = 400.0
R_FAR  = 800.0
R_FAR_BUDGET = R_FAR + 100.0   # search budget allowing for small snap deltas
DECAY_HALF = 400.0             # exp(-d/DECAY_HALF) for anchor strength
SENTINEL = 9999.0

PLAYBOOK = {
    "bakery":              {"competitors": ["bakery","cafe_coffee"],
                            "complements": ["cafe_coffee","restaurant","shopping_retail","supermarket"],
                            "anchors":     ["shopping_retail","transportation"]},
    "bar_nightlife":       {"competitors": ["bar_nightlife"],
                            "complements": ["restaurant","entertainment_culture","hotel_hospitality"],
                            "anchors":     ["entertainment_culture","hotel_hospitality","transportation"]},
    "beauty_personal":     {"competitors": ["beauty_personal"],
                            "complements": ["shopping_retail","fitness_recreation","services"],
                            "anchors":     ["shopping_retail"]},
    "business_office":     {"competitors": ["business_office"],
                            "complements": ["cafe_coffee","restaurant","services","transportation"],
                            "anchors":     ["transportation","business_office"]},
    "cafe_coffee":         {"competitors": ["cafe_coffee","bakery"],
                            "complements": ["bakery","restaurant","shopping_retail","education"],
                            "anchors":     ["shopping_retail","transportation","education"]},
    "convenience":         {"competitors": ["convenience","supermarket"],
                            "complements": ["residential","transportation"],
                            "anchors":     ["residential","transportation"]},
    "education":           {"competitors": ["education"],
                            "complements": ["cafe_coffee","fast_food","residential"],
                            "anchors":     ["residential"]},
    "entertainment_culture": {"competitors": ["entertainment_culture"],
                            "complements": ["restaurant","bar_nightlife","hotel_hospitality"],
                            "anchors":     ["shopping_retail","transportation"]},
    "fast_food":           {"competitors": ["fast_food","restaurant","hawker"],
                            "complements": ["shopping_retail","education","transportation"],
                            "anchors":     ["shopping_retail","transportation"]},
    "fitness_recreation":  {"competitors": ["fitness_recreation"],
                            "complements": ["residential","beauty_personal","restaurant"],
                            "anchors":     ["residential","shopping_retail"]},
    "government_public":   {"competitors": ["government_public"],
                            "complements": ["services","transportation"],
                            "anchors":     ["transportation"]},
    "hawker":              {"competitors": ["hawker","fast_food","restaurant"],
                            "complements": ["residential","supermarket","transportation"],
                            "anchors":     ["residential","transportation"]},
    "health_medical":      {"competitors": ["health_medical"],
                            "complements": ["residential","services"],
                            "anchors":     ["residential","transportation"]},
    "hotel_hospitality":   {"competitors": ["hotel_hospitality"],
                            "complements": ["restaurant","entertainment_culture","bar_nightlife"],
                            "anchors":     ["entertainment_culture","transportation","shopping_retail"]},
    "industrial_mfg":      {"competitors": ["industrial_mfg"],
                            "complements": ["services","business_office"],
                            "anchors":     ["industrial_mfg","transportation"]},
    "other_uncategorized": {"competitors": [],
                            "complements": [],
                            "anchors":     []},
    "park_open":           {"competitors": ["park_open"],
                            "complements": ["fitness_recreation","residential","restaurant"],
                            "anchors":     ["residential"]},
    "religious_worship":   {"competitors": ["religious_worship"],
                            "complements": ["residential"],
                            "anchors":     ["residential"]},
    "residential":         {"competitors": ["residential"],
                            "complements": ["convenience","supermarket","transportation","park_open"],
                            "anchors":     ["transportation","shopping_retail"]},
    "restaurant":          {"competitors": ["restaurant","fast_food","hawker","cafe_coffee"],
                            "complements": ["bar_nightlife","entertainment_culture","shopping_retail"],
                            "anchors":     ["shopping_retail","transportation","hotel_hospitality"]},
    "services":            {"competitors": ["services"],
                            "complements": ["business_office","residential","shopping_retail"],
                            "anchors":     ["shopping_retail","business_office","residential"]},
    "shopping_retail":     {"competitors": ["shopping_retail","supermarket"],
                            "complements": ["restaurant","cafe_coffee","fast_food","beauty_personal","fitness_recreation"],
                            "anchors":     ["shopping_retail","transportation"]},
    "supermarket":         {"competitors": ["supermarket","convenience"],
                            "complements": ["residential","restaurant","beauty_personal"],
                            "anchors":     ["residential"]},
    "transportation":      {"competitors": ["transportation"],
                            "complements": ["shopping_retail","restaurant","fast_food","services"],
                            "anchors":     ["shopping_retail","residential"]},
}


def build_walkable_graph():
    print(f"Loading {ROADS_GJ.name}...")
    r = gpd.read_file(ROADS_GJ)
    walkable = r[~r["highway"].isin(NONWALKABLE_HIGHWAYS)].copy()
    print(f"  total edges {len(r):,}; walkable {len(walkable):,}")

    # Extract node coords from edge endpoints (in EPSG:4326)
    print("Extracting node coords from edge endpoints...")
    u_arr = walkable["u"].values
    v_arr = walkable["v"].values
    geoms = walkable.geometry.values

    node_coords = {}
    for i in range(len(walkable)):
        coords = list(geoms[i].coords)
        u, v = u_arr[i], v_arr[i]
        if u not in node_coords: node_coords[u] = coords[0]
        if v not in node_coords: node_coords[v] = coords[-1]
    nodes = np.array(sorted(node_coords.keys()))
    n_nodes = len(nodes)
    node2idx = {n: i for i, n in enumerate(nodes)}
    print(f"  nodes: {n_nodes:,}")

    # Project node coords → EPSG:3414
    print("Projecting nodes → EPSG:3414...")
    lng = np.array([node_coords[n][0] for n in nodes])
    lat = np.array([node_coords[n][1] for n in nodes])
    node_gdf = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(lng, lat), crs="EPSG:4326"
    ).to_crs(3414)
    node_xy = np.column_stack([node_gdf.geometry.x.values, node_gdf.geometry.y.values])

    # Build CSR (undirected)
    print("Building CSR graph...")
    u_idx = np.array([node2idx[u] for u in u_arr], dtype=np.int32)
    v_idx = np.array([node2idx[v] for v in v_arr], dtype=np.int32)
    length = walkable["length"].values.astype(np.float64)
    G = csr_matrix(
        (np.concatenate([length, length]),
         (np.concatenate([u_idx, v_idx]),
          np.concatenate([v_idx, u_idx]))),
        shape=(n_nodes, n_nodes),
    )
    print(f"  CSR: {G.shape}, nnz {G.nnz:,}")
    return G, node_xy, n_nodes


def snap_to_nodes(xy, node_tree):
    d, i = node_tree.query(xy, k=1)
    return i[:, 0], d[:, 0]


def main():
    t0 = time.time()
    G, node_xy, n_nodes = build_walkable_graph()
    node_tree = BallTree(node_xy)

    # === Snap places + transit nodes ===
    print("\nLoading + snapping places...")
    places = pd.read_parquet(ROOT / "places/sgp_places_final.parquet").reset_index(drop=True)
    n_p = len(places)
    place_gdf = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(places["longitude"], places["latitude"]), crs="EPSG:4326"
    ).to_crs(3414)
    place_xy = np.column_stack([place_gdf.geometry.x.values, place_gdf.geometry.y.values])
    place_node, place_snap = snap_to_nodes(place_xy, node_tree)
    print(f"  {n_p:,} places snapped, median snap-delta {np.median(place_snap):.1f}m, max {place_snap.max():.0f}m")

    print("Loading + snapping MRT exits...")
    mrt = gpd.read_file(MRT_EXITS_GJ).to_crs(3414)
    mrt_xy = np.column_stack([mrt.geometry.x.values, mrt.geometry.y.values])
    mrt_node, _ = snap_to_nodes(mrt_xy, node_tree)
    mrt_node = np.unique(mrt_node)
    print(f"  {len(mrt_xy)} MRT exits → {len(mrt_node)} unique nodes")

    print("Loading + snapping bus stops...")
    bus = gpd.read_file(BUS_STOPS_GJ).to_crs(3414)
    bus_xy = np.column_stack([bus.geometry.x.values, bus.geometry.y.values])
    bus_node, _ = snap_to_nodes(bus_xy, node_tree)
    bus_node = np.unique(bus_node)
    print(f"  {len(bus_xy)} bus stops → {len(bus_node)} unique nodes")

    # === Multi-source SSSP for transit ===
    print("\nMulti-source SSSP for MRT/bus walking distances...")
    t1 = time.time()
    mrt_d = dijkstra(G, indices=mrt_node, limit=3000.0, min_only=True, return_predecessors=False)
    print(f"  MRT MSS: {time.time()-t1:.1f}s")
    t1 = time.time()
    bus_d = dijkstra(G, indices=bus_node, limit=3000.0, min_only=True, return_predecessors=False)
    print(f"  Bus MSS: {time.time()-t1:.1f}s")

    # Per-place transit walk = snap + node-to-nearest
    pmg_walk_dist_mrt_m = mrt_d[place_node] + place_snap
    pmg_walk_dist_bus_m = bus_d[place_node] + place_snap
    pmg_walk_dist_mrt_m = np.where(np.isfinite(pmg_walk_dist_mrt_m), pmg_walk_dist_mrt_m, SENTINEL)
    pmg_walk_dist_bus_m = np.where(np.isfinite(pmg_walk_dist_bus_m), pmg_walk_dist_bus_m, SENTINEL)
    print(f"  median walk_mrt {np.median(pmg_walk_dist_mrt_m):.0f}m, walk_bus {np.median(pmg_walk_dist_bus_m):.0f}m")
    print(f"  near_mrt_400m {(pmg_walk_dist_mrt_m<=400).mean()*100:.1f}%, near_bus_300m {(pmg_walk_dist_bus_m<=300).mean()*100:.1f}%")

    # === Build node→places inverse map (CSR-style) ===
    print("\nBuilding node→places inverse map...")
    order = np.argsort(place_node, kind="stable")
    place_node_sorted = place_node[order]
    boundaries = np.concatenate(([0], np.where(np.diff(place_node_sorted) > 0)[0] + 1, [len(place_node)]))
    unique_nodes_with_places = place_node_sorted[boundaries[:-1]]
    # node_idx → (start, end) into `order`
    node_to_place_range = {ni: (boundaries[i], boundaries[i+1]) for i, ni in enumerate(unique_nodes_with_places)}
    print(f"  {len(node_to_place_range):,} unique nodes carry ≥1 place")

    # === Per-place bounded Dijkstra ===
    print(f"\nPer-place bounded Dijkstra (cutoff={R_FAR_BUDGET}m, {n_p:,} sources)...")
    cat_arr = places["plexis_category"].values
    mag_arr = places["is_magnet"].values.astype(bool)
    rate_arr = places["rating"].fillna(0).values
    revs_arr = places["reviews_count"].fillna(0).values
    msg_arr = places["magnet_strength"].fillna(0).values

    pmg = {
        "pmg_competitors_400m":         np.zeros(n_p, dtype=np.int32),
        "pmg_competitors_800m":         np.zeros(n_p, dtype=np.int32),
        "pmg_closest_competitor_m":     np.full(n_p, SENTINEL, dtype=np.float32),
        "pmg_competitor_rating_avg":    np.zeros(n_p, dtype=np.float32),
        "pmg_complements_400m":         np.zeros(n_p, dtype=np.int32),
        "pmg_complements_800m":         np.zeros(n_p, dtype=np.int32),
        "pmg_complement_categories_present": np.zeros(n_p, dtype=np.int32),
        "pmg_complement_diversity":     np.zeros(n_p, dtype=np.float32),
        "pmg_anchors_400m":             np.zeros(n_p, dtype=np.int32),
        "pmg_anchors_800m":             np.zeros(n_p, dtype=np.int32),
        "pmg_closest_anchor_m":         np.full(n_p, SENTINEL, dtype=np.float32),
        "pmg_anchor_strength_sum":      np.zeros(n_p, dtype=np.float32),
    }

    # Pre-cache rule arrays per category for fast np.isin
    rule_cache = {}
    for cat, rules in PLAYBOOK.items():
        rule_cache[cat] = {
            "comps": np.array(rules["competitors"]) if rules["competitors"] else None,
            "cplts": np.array(rules["complements"]) if rules["complements"] else None,
            "ancs":  np.array(rules["anchors"])     if rules["anchors"]     else None,
        }

    t_loop = time.time()
    PROG = 5000
    for pi in range(n_p):
        ni = place_node[pi]
        snap_self = place_snap[pi]

        dist_arr = dijkstra(G, indices=ni, limit=R_FAR_BUDGET, return_predecessors=False)
        # Reachable nodes within budget
        reach_mask = dist_arr < R_FAR_BUDGET
        reach_nodes = np.where(reach_mask)[0]
        if reach_nodes.size == 0:
            continue

        # Collect neighbor places (vectorized via inverse map)
        nb_p = []
        nb_d = []
        for rn in reach_nodes:
            rng = node_to_place_range.get(int(rn))
            if rng is None: continue
            s, e = rng
            slice_indices = order[s:e]
            slice_d = snap_self + dist_arr[rn] + place_snap[slice_indices]
            nb_p.append(slice_indices)
            nb_d.append(slice_d)
        if not nb_p:
            continue
        nb_idx = np.concatenate(nb_p)
        nb_dist = np.concatenate(nb_d)
        # exclude self + clip to R_FAR
        keep = (nb_idx != pi) & (nb_dist <= R_FAR)
        nb_idx = nb_idx[keep]
        nb_dist = nb_dist[keep]
        if nb_idx.size == 0:
            continue

        nb_cats = cat_arr[nb_idx]
        nb_mag  = mag_arr[nb_idx]
        nb_msg  = msg_arr[nb_idx]
        nb_rate = rate_arr[nb_idx]
        nb_revs = revs_arr[nb_idx]

        cache = rule_cache.get(cat_arr[pi], {"comps": None, "cplts": None, "ancs": None})

        if cache["comps"] is not None:
            cmask = np.isin(nb_cats, cache["comps"])
            if cmask.any():
                cd = nb_dist[cmask]
                pmg["pmg_competitors_400m"][pi] = int((cd <= R_NEAR).sum())
                pmg["pmg_competitors_800m"][pi] = int(cd.size)
                pmg["pmg_closest_competitor_m"][pi] = float(cd.min())
                cr = nb_rate[cmask]; cre = nb_revs[cmask]
                rated = (cr > 0) & (cre > 0)
                if rated.any():
                    pmg["pmg_competitor_rating_avg"][pi] = float(
                        (cr[rated] * cre[rated]).sum() / cre[rated].sum())

        if cache["cplts"] is not None:
            xmask = np.isin(nb_cats, cache["cplts"])
            if xmask.any():
                xd = nb_dist[xmask]
                pmg["pmg_complements_400m"][pi] = int((xd <= R_NEAR).sum())
                pmg["pmg_complements_800m"][pi] = int(xd.size)
                cats_present = nb_cats[xmask]
                uniq, counts = np.unique(cats_present, return_counts=True)
                pmg["pmg_complement_categories_present"][pi] = int(uniq.size)
                p = counts / counts.sum()
                pmg["pmg_complement_diversity"][pi] = float(-(p * np.log(p)).sum())

        if cache["ancs"] is not None:
            amask = np.isin(nb_cats, cache["ancs"]) & nb_mag
            if amask.any():
                ad = nb_dist[amask]
                pmg["pmg_anchors_400m"][pi] = int((ad <= R_NEAR).sum())
                pmg["pmg_anchors_800m"][pi] = int(ad.size)
                pmg["pmg_closest_anchor_m"][pi] = float(ad.min())
                a_strength = nb_msg[amask]
                decay = np.exp(-ad / DECAY_HALF)
                pmg["pmg_anchor_strength_sum"][pi] = float((a_strength * decay).sum())

        if pi and pi % PROG == 0:
            elapsed = time.time() - t_loop
            eta = elapsed / pi * (n_p - pi)
            print(f"  {pi:>6}/{n_p}  ({pi/n_p*100:5.1f}%)  elapsed {elapsed:>5.0f}s  ETA {eta/60:5.1f}m")
    loop_secs = time.time() - t_loop
    print(f"  Per-place loop done: {loop_secs:.0f}s ({loop_secs/n_p*1000:.2f}ms/place)")

    # === Inherit hex-level walk + transit composite scores ===
    print("\nInheriting hex-level walk + transit scores...")
    h9_wk = pd.read_parquet(ROOT / "hex/hex9_walkability.parquet")[["hex9_id","walkability_score"]]
    h9_tr = pd.read_parquet(ROOT / "hex/hex9_transit_clean.parquet")[["hex9_id","transit_score"]]

    out_df = pd.DataFrame(pmg)
    out_df.insert(0, "id", places["id"].values)
    out_df["pmg_walk_dist_mrt_m"] = pmg_walk_dist_mrt_m.astype(np.float32)
    out_df["pmg_walk_dist_bus_m"] = pmg_walk_dist_bus_m.astype(np.float32)
    out_df["pmg_near_mrt_400m"] = (pmg_walk_dist_mrt_m <= 400).astype(np.int8)
    out_df["pmg_near_bus_300m"] = (pmg_walk_dist_bus_m <= 300).astype(np.int8)
    out_df["pmg_snap_delta_m"] = place_snap.astype(np.float32)

    out_df["hex9_id"] = places["hex9_id"].values
    out_df = out_df.merge(h9_wk, on="hex9_id", how="left")
    out_df = out_df.merge(h9_tr, on="hex9_id", how="left")
    out_df = out_df.rename(columns={
        "walkability_score": "pmg_hex_walk_score",
        "transit_score":     "pmg_hex_transit_score",
    }).drop(columns=["hex9_id"])

    # Fill nulls (places at hex9-ids outside our universe = 0 hex score)
    for c in ("pmg_hex_walk_score", "pmg_hex_transit_score"):
        out_df[c] = out_df[c].fillna(0)

    # Round float cols
    for c in out_df.columns:
        if out_df[c].dtype.kind == "f":
            out_df[c] = out_df[c].round(3)

    out_df.to_parquet(ROOT / "places/sgp_places_micrograph.parquet", index=False)
    print(f"\n  places_micrograph: {out_df.shape}")

    # Per-category summary
    print(f"\n=== Per-category averages (network distances) ===")
    summary = places[["id","plexis_category"]].merge(out_df, on="id")
    by_cat = summary.groupby("plexis_category").agg(
        n=("id","count"),
        avg_comp_400=("pmg_competitors_400m","mean"),
        avg_cplt_400=("pmg_complements_400m","mean"),
        avg_anc_400=("pmg_anchors_400m","mean"),
        avg_anc_str=("pmg_anchor_strength_sum","mean"),
        avg_walk_mrt=("pmg_walk_dist_mrt_m","mean"),
        avg_walk_bus=("pmg_walk_dist_bus_m","mean"),
    ).round(2).sort_values("n", ascending=False)
    print(by_cat.to_string())

    summary_json = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "shape": list(out_df.shape),
        "graph_nodes": n_nodes,
        "graph_edges_walkable": int(G.nnz / 2),
        "snap_delta_median_m": float(np.median(place_snap)),
        "snap_delta_max_m": float(place_snap.max()),
        "median_walk_dist_mrt_m": float(np.median(pmg_walk_dist_mrt_m)),
        "median_walk_dist_bus_m": float(np.median(pmg_walk_dist_bus_m)),
        "near_mrt_400m_pct": float((pmg_walk_dist_mrt_m <= 400).mean() * 100),
        "near_bus_300m_pct": float((pmg_walk_dist_bus_m <= 300).mean() * 100),
        "input_places": n_p,
    }
    with open(ROOT / "places/place_micrograph_report.json", "w") as f:
        json.dump(summary_json, f, indent=2)
    print(f"\nWall clock: {summary_json['wall_clock_s']}s")


if __name__ == "__main__":
    main()
