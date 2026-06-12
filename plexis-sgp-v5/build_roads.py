"""
Plexis SGP v4 — Stage 6: roads + parking per hex-9.

Single-pass builder. Inputs (atlas-1):
  data/roads/roads.geojson                     550,991 OSM segments (with u/v topology)
  data/transit/traffic_signals.geojson          44,922 LTA signals
  data/osm_pois/amenities.geojson               OSM amenities incl. parking
  data/housing/hdb_property_info.csv            HDB block-level carpark flags
  data/housing/hdb_existing_buildings.geojson   13,386 HDB block polygons (for centroid → hex)

Outputs:
  hex/hex9_roads.parquet
  hex/hex9_parking.parquet
  hex/roads_report.json

Pillars (per hex-9):
  A — lengths + density
  B — class composition
  C — local topology (nodes, intersections, degree, dead-ends, gridiness, components, clustering)
  D — motorway/highway proximity (through, adjacent, severance, exits) — §9
  E — walkability infra (pedestrian path, cycleway, signalized crossings)
  F — vehicle capacity (lane-km, oneway, bridge/tunnel)

Plus a separate parking parquet covering §10 Tier 1.
"""
import json
import os
import time
from pathlib import Path
from collections import defaultdict, Counter

import pandas as pd
import geopandas as gpd
import numpy as np
import networkx as nx
from shapely.geometry import Polygon, LineString, Point, MultiLineString
from shapely.ops import linemerge
from shapely.strtree import STRtree
import h3

ROOT = Path(__file__).parent


def _resolve_data_root():
    if os.environ.get("PLEXIS_DATA_ROOT"):
        return Path(os.environ["PLEXIS_DATA_ROOT"])
    for c in [Path("/home/azureuser/digital-atlas-sgp/data"), ROOT.parent / "data"]:
        if c.exists():
            return c
    raise FileNotFoundError("No data root found")


DATA = _resolve_data_root()
ROADS_GEO = DATA / "roads/roads.geojson"
SIGNALS_GEO = DATA / "transit/traffic_signals.geojson"
AMENITIES_GEO = DATA / "osm_pois/amenities.geojson"
HDB_INFO = DATA / "housing/hdb_property_info.csv"
HDB_GEO = DATA / "housing/hdb_existing_buildings.geojson"
HEX9 = ROOT / "hex/hex9_universe.parquet"

OUT_ROADS = ROOT / "hex/hex9_roads.parquet"
OUT_PARKING = ROOT / "hex/hex9_parking.parquet"
REPORT = ROOT / "hex/roads_report.json"

HEX_AREA_M2 = 105_000  # ~0.105 km² per hex-9

CLASS_BUCKETS = {
    "motorway": "motorway", "motorway_link": "motorway_link",
    "trunk": "trunk", "trunk_link": "trunk_link",
    "primary": "primary", "primary_link": "primary",
    "secondary": "secondary", "secondary_link": "secondary",
    "tertiary": "tertiary", "tertiary_link": "tertiary",
    "residential": "residential", "living_street": "residential",
    "service": "service", "unclassified": "unclassified", "road": "unclassified",
    "footway": "footway", "pedestrian": "footway", "corridor": "footway",
    "path": "path", "steps": "steps",
    "cycleway": "cycleway",
    "track": "track",
    "bridleway": "track",
    "elevator": "footway", "bus_stop": "service",
}

PEDESTRIAN_CLASSES = {"footway", "path", "steps", "cycleway"}
VEHICLE_CLASSES = {"motorway", "motorway_link", "trunk", "trunk_link",
                    "primary", "secondary", "tertiary", "residential",
                    "service", "unclassified", "track"}
EXPRESSWAY_CLASSES = {"motorway", "trunk"}
EXPRESSWAY_LINK_CLASSES = {"motorway_link", "trunk_link"}

# default lane counts when missing
DEFAULT_LANES = {
    "motorway": 4, "trunk": 3, "primary": 3, "primary_link": 1,
    "secondary": 2, "tertiary": 2, "residential": 2, "service": 1,
    "unclassified": 1, "motorway_link": 1, "trunk_link": 1, "secondary_link": 1,
    "tertiary_link": 1,
}


def parse_lanes(val):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    try:
        s = str(val).split(";")[0]
        return float(s)
    except Exception:
        return None


def main():
    t0 = time.time()
    print("Loading inputs (this may take ~60s for 550K road segments)...")
    roads = gpd.read_file(ROADS_GEO).to_crs(4326)
    print(f"  roads: {len(roads):,} segments")
    h9 = pd.read_parquet(HEX9)
    print(f"  hex-9: {len(h9):,} cells")

    # Project to metric
    print("  Projecting roads to EPSG:3414...")
    roads_3414 = roads.to_crs(3414)
    roads_3414["length_m"] = roads_3414.geometry.length

    # Bucket class
    roads_3414["bucket"] = roads_3414["highway"].map(CLASS_BUCKETS).fillna("other")
    roads_3414["lanes_n"] = roads_3414["lanes"].apply(parse_lanes)
    # Fill missing lanes from class default
    roads_3414["lanes_eff"] = roads_3414.apply(
        lambda r: r["lanes_n"] if r["lanes_n"] is not None else DEFAULT_LANES.get(r["bucket"], 0),
        axis=1
    )
    roads_3414["lane_km_segment"] = roads_3414["lanes_eff"] * roads_3414["length_m"] / 1000.0
    def _to_bool(v):
        if v is None or (isinstance(v, float) and np.isnan(v)): return False
        if isinstance(v, (list, tuple, np.ndarray)):
            return any(_to_bool(x) for x in v)
        return str(v).lower() in ("yes", "true", "1")
    roads_3414["is_oneway"] = roads_3414["oneway"].apply(_to_bool)
    roads_3414["is_bridge"] = roads_3414["bridge"].apply(_to_bool)
    roads_3414["is_tunnel"] = roads_3414["tunnel"].apply(_to_bool)

    # === Build hex polygons in 3414 ===
    print("  Building hex polygons (3414)...")
    hex_polys_4326 = []
    for hid in h9["hex9_id"]:
        ring = [(lng, lat) for lat, lng in h3.cell_to_boundary(hid)]
        hex_polys_4326.append(Polygon(ring))
    h9_gdf = gpd.GeoDataFrame({"hex9_id": h9["hex9_id"]}, geometry=hex_polys_4326, crs=4326).to_crs(3414)

    # === Pillars A + B + F: lengths, classes, lane-km via clip ===
    print("  Spatial join: roads × hex (sjoin candidates)...")
    cand = gpd.sjoin(roads_3414, h9_gdf, how="inner", predicate="intersects")
    print(f"    candidate road-hex pairs: {len(cand):,}")

    print("  Clipping each segment to its candidate hex (precise length)...")
    rows = []
    hex_geom_by_idx = dict(zip(h9_gdf.index, h9_gdf.geometry))
    n = 0
    for _, r in cand.iterrows():
        hg = hex_geom_by_idx.get(r["index_right"])
        if hg is None: continue
        seg = r["geometry"]
        try:
            inter = seg.intersection(hg)
            if inter.is_empty:
                continue
            if inter.geom_type == "LineString":
                clip_len = inter.length
            elif inter.geom_type == "MultiLineString":
                clip_len = sum(g.length for g in inter.geoms)
            else:
                continue
            if clip_len <= 0: continue
        except Exception:
            continue
        # lane-km adjusted
        lane_km = r["lanes_eff"] * clip_len / 1000.0
        rows.append({
            "hex9_id": r["hex9_id"],
            "bucket": r["bucket"],
            "highway": r["highway"],
            "clip_len_m": clip_len,
            "lane_km": lane_km,
            "is_oneway": r["is_oneway"],
            "is_bridge": r["is_bridge"],
            "is_tunnel": r["is_tunnel"],
            "u": r["u"],
            "v": r["v"],
            "name": r["name"],
        })
        n += 1
        if n % 100000 == 0:
            print(f"    ...{n:,} clips")
    df = pd.DataFrame(rows)
    print(f"  total clipped segments: {len(df):,}")

    # === Per-hex aggregations ===
    print("  Aggregating per hex...")
    # Lengths total + by bucket
    hex_total_len = df.groupby("hex9_id")["clip_len_m"].sum().reset_index(name="road_length_total_m")

    bucket_lengths = df.pivot_table(
        index="hex9_id", columns="bucket", values="clip_len_m", aggfunc="sum", fill_value=0
    )
    bucket_lengths.columns = [f"road_{c}_length_m" for c in bucket_lengths.columns]
    bucket_lengths = bucket_lengths.reset_index()

    # Lane-km
    hex_lanekm = df.groupby("hex9_id")["lane_km"].sum().reset_index(name="lane_km")
    # Bridge / tunnel length
    bridge_len = df[df["is_bridge"]].groupby("hex9_id")["clip_len_m"].sum().reset_index(name="bridge_length_m")
    tunnel_len = df[df["is_tunnel"]].groupby("hex9_id")["clip_len_m"].sum().reset_index(name="tunnel_length_m")
    # Oneway pct (vehicle only)
    veh_mask = df["bucket"].isin(VEHICLE_CLASSES)
    veh_total = df[veh_mask].groupby("hex9_id")["clip_len_m"].sum().reset_index(name="veh_total_m")
    oneway_total = df[veh_mask & df["is_oneway"]].groupby("hex9_id")["clip_len_m"].sum().reset_index(name="oneway_total_m")

    # Pedestrian / vehicular roll-ups
    df["is_ped"] = df["bucket"].isin(PEDESTRIAN_CLASSES)
    df["is_veh"] = df["bucket"].isin(VEHICLE_CLASSES)
    ped_len = df[df["is_ped"]].groupby("hex9_id")["clip_len_m"].sum().reset_index(name="road_pedestrian_length_m")
    veh_len = df[df["is_veh"]].groupby("hex9_id")["clip_len_m"].sum().reset_index(name="road_vehicular_length_m")

    # === Pillar C — local topology ===
    print("  Computing local topology (vehicle-only subgraph) per hex...")
    # Vehicle-only edges with u, v
    veh = df[df["is_veh"]].copy()
    # Build node→hex assignment from edge: a node is "in" the hex if any of its incident edges have
    # at least 50% of length in that hex. Simpler approximation: for each edge, both endpoints
    # belong to that hex if the clip is full-length-ish; we use a per-hex node set = unique u,v
    # of edges with clip_len_m / segment_length_m > 0.5.
    # For simplicity here, treat any node touching a hex (via clipped edge presence) as in that hex.
    # This slightly over-counts boundary nodes but is consistent.
    veh["edge_id"] = veh["u"].astype(str) + "_" + veh["v"].astype(str)
    nodes_per_hex = (
        pd.concat([
            veh[["hex9_id", "u"]].rename(columns={"u": "node"}),
            veh[["hex9_id", "v"]].rename(columns={"v": "node"}),
        ])
        .drop_duplicates()
        .groupby("hex9_id")["node"]
        .apply(set)
    )
    edges_per_hex = veh.groupby("hex9_id")["edge_id"].apply(set)

    # Build full SGP vehicle graph (for degree calc) once
    print("    building full SGP vehicle graph for degree lookup...")
    G_veh = nx.MultiGraph()
    veh_full = roads_3414[roads_3414["bucket"].isin(VEHICLE_CLASSES)]
    for _, r in veh_full.iterrows():
        G_veh.add_edge(r["u"], r["v"])
    print(f"      G_veh: {G_veh.number_of_nodes():,} nodes, {G_veh.number_of_edges():,} edges")
    deg = dict(G_veh.degree())

    print("    computing per-hex topology metrics...")
    topo_rows = []
    for hex_id, nodes in nodes_per_hex.items():
        edges = edges_per_hex.get(hex_id, set())
        n_nodes = len(nodes)
        n_edges = len(edges)
        if n_nodes == 0:
            continue
        degs = [deg.get(n, 0) for n in nodes]
        deg_arr = np.array(degs)
        n_intersection = int((deg_arr >= 3).sum())
        n_dead = int((deg_arr == 1).sum())
        n_3way = int((deg_arr == 3).sum())
        n_4way = int((deg_arr == 4).sum())
        n_5plus = int((deg_arr >= 5).sum())
        gridiness = n_4way / max(n_3way + n_4way + n_5plus, 1)
        avg_deg = float(deg_arr.mean()) if len(deg_arr) else 0
        # Internal connected components: subgraph of G_veh restricted to these nodes
        sub = G_veh.subgraph(nodes)
        n_components = nx.number_connected_components(sub) if sub.number_of_nodes() > 0 else 0
        # Local clustering coeff (project to simple Graph for clustering)
        try:
            simple = nx.Graph(sub)
            cc_vals = list(nx.clustering(simple).values())
            cc_mean = float(np.mean(cc_vals)) if cc_vals else 0
        except Exception:
            cc_mean = 0
        topo_rows.append({
            "hex9_id": hex_id,
            "road_node_count": n_nodes,
            "road_edge_count": n_edges,
            "road_intersection_count": n_intersection,
            "road_dead_end_count": n_dead,
            "road_3way_count": n_3way,
            "road_4way_count": n_4way,
            "road_5plus_way_count": n_5plus,
            "road_gridiness_score": float(gridiness),
            "road_avg_node_degree": avg_deg,
            "road_internal_components": n_components,
            "road_local_clustering_coeff": cc_mean,
        })
    topo = pd.DataFrame(topo_rows)
    print(f"    topology rows: {len(topo):,}")

    # === Pillar D — motorway/highway proximity ===
    print("  Pillar D: motorway/highway proximity (§9)...")
    # Through length per class
    through_classes = ["motorway", "trunk", "primary"]
    through_lens = {}
    for cls in through_classes:
        m = df[df["bucket"] == cls].groupby("hex9_id")["clip_len_m"].sum().rename(f"road_{cls}_in_hex_m")
        through_lens[cls] = m
    # Distance from centroid to nearest segment of each class (entire SGP)
    print("    distance to expressway (motorway/trunk)...")
    expressway = roads_3414[roads_3414["bucket"].isin(EXPRESSWAY_CLASSES)]
    if len(expressway):
        expressway_geoms = list(expressway.geometry.values)
        tree_x = STRtree(expressway_geoms)
        # hex centroids in 3414
        h9_gdf["centroid"] = h9_gdf.geometry.centroid
        dist_x = []
        for cent in h9_gdf["centroid"].values:
            # nearest index
            nearest = tree_x.nearest(cent)
            d = cent.distance(expressway_geoms[nearest])
            dist_x.append(d)
        h9_gdf["dist_expressway_m"] = dist_x
    print("    distance to expressway exit (motorway_link/trunk_link)...")
    expr_link = roads_3414[roads_3414["bucket"].isin(EXPRESSWAY_LINK_CLASSES)]
    if len(expr_link):
        link_geoms = list(expr_link.geometry.values)
        tree_l = STRtree(link_geoms)
        dist_l = []
        for cent in h9_gdf["centroid"].values:
            nearest = tree_l.nearest(cent)
            d = cent.distance(link_geoms[nearest])
            dist_l.append(d)
        h9_gdf["dist_expressway_exit_m"] = dist_l
    print("    distance to primary road...")
    primary = roads_3414[roads_3414["bucket"] == "primary"]
    if len(primary):
        prim_geoms = list(primary.geometry.values)
        tree_p = STRtree(prim_geoms)
        dist_p = []
        for cent in h9_gdf["centroid"].values:
            nearest = tree_p.nearest(cent)
            d = cent.distance(prim_geoms[nearest])
            dist_p.append(d)
        h9_gdf["dist_primary_m"] = dist_p

    proximity = h9_gdf[["hex9_id", "dist_expressway_m", "dist_expressway_exit_m", "dist_primary_m"]].copy()
    proximity["expressway_within_200m"] = proximity["dist_expressway_m"] < 200
    proximity["expressway_within_500m"] = proximity["dist_expressway_m"] < 500
    proximity["near_expressway_exit_400m"] = proximity["dist_expressway_exit_m"] < 400

    # road_max_class_through (highest class with clip_len_m > 0 in hex)
    CLASS_RANK = ["motorway", "trunk", "primary", "secondary", "tertiary",
                  "residential", "service", "unclassified", "track",
                  "footway", "cycleway", "path", "steps", "other"]
    by_hex_classes = df.groupby("hex9_id")["bucket"].apply(set)
    def max_class(buckets):
        for c in CLASS_RANK:
            if c in buckets:
                return c
        return "none"
    max_class_df = by_hex_classes.apply(max_class).reset_index(name="road_max_class_through")

    # === Pillar E — walkability infra (signalized crossings) ===
    print("  Pillar E: signalized crossings...")
    sig = gpd.read_file(SIGNALS_GEO).to_crs(3414)
    # filter null geometries
    sig = sig[sig.geometry.notna()].copy()
    sig["sig_type"] = sig["TYP_NAM"].fillna("OTHER").str.upper()
    sig_4326 = sig.to_crs(4326)
    sig["hex9_id"] = [h3.latlng_to_cell(g.y, g.x, 9) if g is not None else None for g in sig_4326.geometry]
    sig = sig[sig["hex9_id"].notna()]
    # Pedestrian-related signal types: anything with "PED"
    sig["is_ped_sig"] = sig["sig_type"].str.contains("PED")
    sig_agg = sig.groupby("hex9_id").agg(
        signalized_crossing_count=("OBJECTID_1", "count"),
        ped_signal_count=("is_ped_sig", "sum"),
    ).reset_index()

    # === Build final roads table ===
    print("  Building final roads table...")
    out = h9[["hex9_id", "lat", "lng"]].copy()
    out = out.merge(hex_total_len, on="hex9_id", how="left")
    out = out.merge(ped_len, on="hex9_id", how="left")
    out = out.merge(veh_len, on="hex9_id", how="left")
    out = out.merge(bucket_lengths, on="hex9_id", how="left")
    # Merge through_lens for motorway/trunk/primary
    for cls, ser in through_lens.items():
        out = out.merge(ser.reset_index(), on="hex9_id", how="left")
    out = out.merge(hex_lanekm, on="hex9_id", how="left")
    out = out.merge(bridge_len, on="hex9_id", how="left")
    out = out.merge(tunnel_len, on="hex9_id", how="left")
    out = out.merge(veh_total, on="hex9_id", how="left")
    out = out.merge(oneway_total, on="hex9_id", how="left")
    out = out.merge(topo, on="hex9_id", how="left")
    out = out.merge(proximity, on="hex9_id", how="left")
    out = out.merge(max_class_df, on="hex9_id", how="left")
    out = out.merge(sig_agg, on="hex9_id", how="left")

    # Fill numeric NaNs with 0 for counts/lengths
    fill_zero = [c for c in out.columns if c.endswith("_m") or c.endswith("_count")
                  or c.endswith("_km") or c in ("oneway_total_m", "veh_total_m", "ped_signal_count")]
    for c in fill_zero:
        if c in out.columns:
            out[c] = out[c].fillna(0)

    # Derived metrics
    out["road_density_km_per_km2"] = out["road_length_total_m"] / 1000.0 * (1e6 / HEX_AREA_M2)
    out["road_walkable_share"] = np.where(
        out["road_length_total_m"] > 0,
        out["road_pedestrian_length_m"] / out["road_length_total_m"], 0,
    )
    out["lane_km_per_km2"] = out["lane_km"] * (1e6 / HEX_AREA_M2)
    out["oneway_pct"] = np.where(
        out["veh_total_m"] > 0,
        out["oneway_total_m"] / out["veh_total_m"], 0,
    )
    out["road_intersection_density_per_km2"] = out["road_intersection_count"].fillna(0) * (1e6 / HEX_AREA_M2)
    out["pedestrian_path_density_km_per_km2"] = (
        (out.get("road_footway_length_m", 0) + out.get("road_path_length_m", 0)
         + out.get("road_steps_length_m", 0) + out.get("road_cycleway_length_m", 0))
        / 1000.0 * (1e6 / HEX_AREA_M2)
    )
    # Class % shares (based on total length)
    bucket_cols = [c for c in out.columns if c.startswith("road_") and c.endswith("_length_m")
                    and c not in ("road_length_total_m", "road_pedestrian_length_m", "road_vehicular_length_m")]
    for bc in bucket_cols:
        cls = bc[5:-9]
        out[f"road_{cls}_pct"] = np.where(out["road_length_total_m"] > 0,
                                            out[bc] / out["road_length_total_m"], 0)

    # Class entropy (over bucket lengths)
    pcts = out[[f"road_{c}_pct" for c in ["motorway", "trunk", "primary", "secondary",
                                            "tertiary", "residential", "service", "footway",
                                            "cycleway", "path", "unclassified"] if f"road_{c}_pct" in out.columns]]
    eps = 1e-12
    out["road_class_entropy"] = -((pcts + eps) * np.log(pcts + eps)).sum(axis=1)
    # Mask: entropy is 0 if no roads
    out.loc[out["road_length_total_m"] == 0, "road_class_entropy"] = 0

    # Drop scratch columns
    out = out.drop(columns=["veh_total_m", "oneway_total_m"], errors="ignore")

    out.to_parquet(OUT_ROADS, index=False)
    print(f"\nRoads parquet: {out.shape}")

    # ============= PARKING (§10 Tier 1) =============
    print("\n=== Parking Tier 1 ===")
    print("  Loading OSM amenities...")
    am = gpd.read_file(AMENITIES_GEO).to_crs(4326)
    print(f"    OSM features: {len(am):,}")
    # Centroid → hex
    am_3414 = am.to_crs(3414)
    am["centroid"] = am_3414.geometry.centroid.to_crs(4326) if False else am.geometry.centroid
    am["hex9_id"] = [h3.latlng_to_cell(g.y, g.x, 9) for g in am.geometry.centroid]
    am["amenity_norm"] = am["amenity"].astype(str).str.lower()

    # Re-hash hex_id properly using projected centroid to avoid CRS warning
    am_3414 = am.to_crs(3414)
    am_3414["centroid_3414"] = am_3414.geometry.centroid
    cent_4326 = gpd.GeoSeries(am_3414["centroid_3414"], crs=3414).to_crs(4326)
    am["hex9_id"] = [h3.latlng_to_cell(p.y, p.x, 9) for p in cent_4326]

    parking_lots = am[am["amenity_norm"] == "parking"].copy()
    parking_entries = am[am["amenity_norm"] == "parking_entrance"].copy()
    parking_spaces = am[am["amenity_norm"] == "parking_space"].copy()
    bicycle_parking = am[am["amenity_norm"] == "bicycle_parking"].copy()

    # OSM SGP parking is points-only (no polygons). Estimate area from typical lot size.
    # Median SGP surface lot ~1500 m²; MSCP ~3000 m² footprint. Use 1500 as default.
    PARKING_LOT_EST_AREA_M2 = 1500
    parking_lots_3414 = parking_lots.to_crs(3414)
    parking_lots["area_m2"] = parking_lots_3414.geometry.area.fillna(0).values
    polygon_count = (parking_lots["area_m2"] > 0).sum()
    point_count = (parking_lots["area_m2"] == 0).sum()
    print(f"  parking lot polygons with area>0: {polygon_count}")
    print(f"  parking lot point-only entries (will use est area): {point_count}")
    parking_lots["area_m2_est"] = parking_lots["area_m2"].where(
        parking_lots["area_m2"] > 0, PARKING_LOT_EST_AREA_M2
    )
    print(f"  estimated total parking area: {parking_lots['area_m2_est'].sum() / 1e6:.4f} km²")

    park_lots_agg = parking_lots.groupby("hex9_id").agg(
        parking_lot_count=("id", "count"),
        parking_lot_area_m2_est=("area_m2_est", "sum"),
    ).reset_index()
    park_entries_agg = parking_entries.groupby("hex9_id").size().reset_index(name="parking_entrance_count")
    park_spaces_agg = parking_spaces.groupby("hex9_id").size().reset_index(name="parking_space_count")
    bike_park_agg = bicycle_parking.groupby("hex9_id").size().reset_index(name="bicycle_parking_count")

    # HDB carparks via property_info → block geo
    print("  HDB MSCPs and surface carparks...")
    hdb_geo = gpd.read_file(HDB_GEO).to_crs(4326)
    hdb_info = pd.read_csv(HDB_INFO)
    hdb_info["blk_no_n"] = hdb_info["blk_no"].astype(str).str.upper().str.strip()
    hdb_geo["BLK_NO_N"] = hdb_geo["BLK_NO"].astype(str).str.upper().str.strip()
    # blk_no alone is non-unique across SGP. The reliable join is (blk_no, hdb_town).
    # Use the HDB town polygons (already built in admin stage) to spatially assign each block.
    HDB_TOWN_GEO = ROOT / "boundaries/hdb_towns.geojson"
    if HDB_TOWN_GEO.exists():
        hdb_towns = gpd.read_file(HDB_TOWN_GEO).to_crs(3414)
        hdb_geo_3414 = hdb_geo.to_crs(3414)
        hdb_geo_3414["centroid"] = hdb_geo_3414.geometry.centroid
        # Spatial join centroid → town
        cent_gdf = gpd.GeoDataFrame(hdb_geo_3414[["BLK_NO_N"]].reset_index(drop=True),
                                     geometry=hdb_geo_3414["centroid"].reset_index(drop=True), crs=3414)
        cent_gdf["_orig_idx"] = cent_gdf.index
        joined = gpd.sjoin(cent_gdf, hdb_towns[["hdb_town", "geometry"]],
                           how="left", predicate="within")
        # Some centroids fall inside multiple buffered town polygons → keep first match
        joined_unique = joined.drop_duplicates(subset="_orig_idx").set_index("_orig_idx")
        # Reindex to original block order
        town_assignment = joined_unique["hdb_town"].reindex(range(len(hdb_geo_3414))).values
        hdb_geo["town_full"] = town_assignment
        # Map full town name → short code used in property_info.bldg_contract_town
        TOWN_NAME_TO_CODE = {
            "ANG MO KIO": "AMK", "BEDOK": "BD", "BISHAN": "BH",
            "BUKIT BATOK": "BB", "BUKIT MERAH": "BM", "BUKIT PANJANG": "BP",
            "BUKIT TIMAH": "BT", "CENTRAL AREA": "CT", "CHOA CHU KANG": "CCK",
            "CLEMENTI": "CL", "GEYLANG": "GL", "HOUGANG": "HG",
            "JURONG EAST": "JE", "JURONG WEST": "JW",
            "KALLANG/WHAMPOA": "KWN", "MARINE PARADE": "MP",
            "PASIR RIS": "PRC", "PUNGGOL": "PG", "QUEENSTOWN": "QT",
            "SEMBAWANG": "SB", "SENGKANG": "SK", "SERANGOON": "SGN",
            "TAMPINES": "TAP", "TENGAH": "TG", "TOA PAYOH": "TP",
            "WOODLANDS": "WL", "YISHUN": "YS",
        }
        hdb_geo["town_code"] = hdb_geo["town_full"].map(TOWN_NAME_TO_CODE)
        hdb_info["town_norm"] = hdb_info["bldg_contract_town"].astype(str).str.upper()
        info_mscp = set(zip(hdb_info[hdb_info["multistorey_carpark"] == "Y"]["blk_no_n"],
                            hdb_info[hdb_info["multistorey_carpark"] == "Y"]["town_norm"]))
        info_misc = set(zip(hdb_info[hdb_info["miscellaneous"] == "Y"]["blk_no_n"],
                            hdb_info[hdb_info["miscellaneous"] == "Y"]["town_norm"]))
        hdb_geo["is_mscp"] = hdb_geo.apply(
            lambda r: (r["BLK_NO_N"], r["town_code"]) in info_mscp if r.get("town_code") else False, axis=1)
        hdb_geo["is_misc"] = hdb_geo.apply(
            lambda r: (r["BLK_NO_N"], r["town_code"]) in info_misc if r.get("town_code") else False, axis=1)
    else:
        # Fallback: blk_no alone (over-counts)
        info_mscp = set(hdb_info[hdb_info["multistorey_carpark"] == "Y"]["blk_no_n"])
        info_misc = set(hdb_info[hdb_info["miscellaneous"] == "Y"]["blk_no_n"])
        hdb_geo["is_mscp"] = hdb_geo["BLK_NO_N"].isin(info_mscp)
        hdb_geo["is_misc"] = hdb_geo["BLK_NO_N"].isin(info_misc)
    print(f"  HDB MSCP matches: {hdb_geo['is_mscp'].sum():,} blocks (expected ~1,114)")
    print(f"  HDB misc matches: {hdb_geo['is_misc'].sum():,} blocks (expected ~3,109)")
    cent_4326 = hdb_geo.to_crs(3414).geometry.centroid.to_crs(4326)
    hdb_geo["hex9_id"] = [h3.latlng_to_cell(p.y, p.x, 9) for p in cent_4326]

    hdb_park_agg = hdb_geo.groupby("hex9_id").agg(
        hdb_mscp_count=("is_mscp", "sum"),
        hdb_surface_carpark_count=("is_misc", "sum"),
    ).reset_index()
    hdb_park_agg["hdb_mscp_count"] = hdb_park_agg["hdb_mscp_count"].astype(int)
    hdb_park_agg["hdb_surface_carpark_count"] = hdb_park_agg["hdb_surface_carpark_count"].astype(int)

    # Build parking table
    park = h9[["hex9_id"]].copy()
    park = park.merge(park_lots_agg, on="hex9_id", how="left")
    park = park.merge(park_entries_agg, on="hex9_id", how="left")
    park = park.merge(park_spaces_agg, on="hex9_id", how="left")
    park = park.merge(bike_park_agg, on="hex9_id", how="left")
    park = park.merge(hdb_park_agg, on="hex9_id", how="left")
    for c in park.columns:
        if c != "hex9_id":
            park[c] = park[c].fillna(0)
    park["parking_density_per_km2"] = park["parking_lot_count"] * (1e6 / HEX_AREA_M2)
    park["parking_footprint_share_est"] = park["parking_lot_area_m2_est"] / HEX_AREA_M2
    park["is_parking_dominant"] = park["parking_footprint_share_est"] > 0.15

    park.to_parquet(OUT_PARKING, index=False)
    print(f"  Parking parquet: {park.shape}")

    # === Summary report ===
    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "roads": {
            "input_segments": int(len(roads)),
            "clipped_segments": int(len(df)),
            "total_road_length_km": round(out["road_length_total_m"].sum() / 1000, 2),
            "total_pedestrian_length_km": round(out["road_pedestrian_length_m"].sum() / 1000, 2),
            "total_vehicular_length_km": round(out["road_vehicular_length_m"].sum() / 1000, 2),
            "total_lane_km": round(out["lane_km"].sum(), 2),
            "hexes_with_road": int((out["road_length_total_m"] > 0).sum()),
            "hexes_with_motorway_through": int((out.get("road_motorway_in_hex_m", 0) > 0).sum() if "road_motorway_in_hex_m" in out else 0),
            "hexes_within_200m_expressway": int(out["expressway_within_200m"].sum()),
            "hexes_near_expressway_exit_400m": int(out["near_expressway_exit_400m"].sum()),
            "max_intersection_density_per_km2": float(out["road_intersection_density_per_km2"].max()),
            "max_road_density_km_per_km2": float(out["road_density_km_per_km2"].max()),
        },
        "parking": {
            "total_parking_lots": int(park["parking_lot_count"].sum()),
            "total_parking_lot_area_km2_est": round(park["parking_lot_area_m2_est"].sum() / 1e6, 4),
            "total_parking_entrances": int(park["parking_entrance_count"].sum()),
            "total_bicycle_parking": int(park["bicycle_parking_count"].sum()),
            "total_hdb_mscp": int(park["hdb_mscp_count"].sum()),
            "total_hdb_surface_carpark": int(park["hdb_surface_carpark_count"].sum()),
            "hexes_parking_dominant": int(park["is_parking_dominant"].sum()),
        }
    }
    with open(REPORT, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSummary:\n{json.dumps(summary, indent=2)}")
    print(f"\nOutputs:")
    print(f"  {OUT_ROADS}")
    print(f"  {OUT_PARKING}")
    print(f"  {REPORT}")


if __name__ == "__main__":
    main()
