#!/usr/bin/env python3
"""Steps 14-16: Graph Construction"""
import pandas as pd
import geopandas as gpd
import numpy as np
import json, os, time
from collections import defaultdict

BASE = "/home/azureuser/digital-atlas-sgp/data"
OUT = "/home/azureuser/digital-atlas-sgp/graphs"
os.makedirs(OUT, exist_ok=True)

def log(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)

# ============================================================
# STEP 14: SUBZONE ADJACENCY GRAPH
# ============================================================
def step_14_adjacency():
    log("=" * 60)
    log("STEP 14: SUBZONE ADJACENCY GRAPH")
    log("=" * 60)

    sz = gpd.read_file(BASE + "/boundaries/subzones.geojson")
    sz_proj = sz.to_crs(epsg=3414)
    log("Subzones: %d" % len(sz))

    # Queen contiguity: shared boundary or point
    edges = []
    nodes = {}

    for i, row_i in sz_proj.iterrows():
        code_i = row_i["SUBZONE_C"]
        centroid = sz.iloc[i].geometry.centroid
        nodes[code_i] = {
            "subzone_code": code_i,
            "subzone_name": row_i["SUBZONE_N"],
            "planning_area": row_i["PLN_AREA_N"],
            "region": row_i["REGION_N"],
            "centroid_lat": centroid.y,
            "centroid_lon": centroid.x,
            "area_km2": round(row_i.geometry.area / 1e6, 4),
        }

        for j, row_j in sz_proj.iterrows():
            if i >= j:
                continue
            code_j = row_j["SUBZONE_C"]

            if row_i.geometry.touches(row_j.geometry) or row_i.geometry.intersects(row_j.geometry):
                # Compute shared boundary length
                try:
                    intersection = row_i.geometry.intersection(row_j.geometry)
                    shared_length = intersection.length  # meters
                except:
                    shared_length = 0

                if shared_length > 0 or row_i.geometry.touches(row_j.geometry):
                    edges.append({
                        "source": code_i,
                        "target": code_j,
                        "shared_boundary_m": round(shared_length, 1),
                        "type": "adjacent",
                    })

    graph = {
        "type": "subzone_adjacency",
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
    }

    outpath = OUT + "/subzone_adjacency.json"
    with open(outpath, "w") as f:
        json.dump(graph, f, indent=2)

    # Stats
    degrees = defaultdict(int)
    for e in edges:
        degrees[e["source"]] += 1
        degrees[e["target"]] += 1

    deg_vals = list(degrees.values())
    isolated = len(nodes) - len(degrees)

    log("Nodes: %d" % len(nodes))
    log("Edges: %d" % len(edges))
    log("Avg degree: %.1f" % (np.mean(deg_vals) if deg_vals else 0))
    log("Max degree: %d" % (max(deg_vals) if deg_vals else 0))
    log("Isolated nodes: %d" % isolated)

    # Validation
    assert len(nodes) >= 330, "Too few nodes: %d" % len(nodes)
    assert len(edges) >= 500, "Too few edges: %d" % len(edges)
    assert isolated < 20, "Too many isolated: %d" % isolated
    log("Adjacency: PASSED")

    return graph


# ============================================================
# STEP 15: PLACE CO-LOCATION PMI
# ============================================================
def step_15_colocation():
    log("\n" + "=" * 60)
    log("STEP 15: PLACE CO-LOCATION PMI")
    log("=" * 60)

    places = pd.read_json(BASE + "/places/sgp_places.jsonl", lines=True)
    log("Places: %d" % len(places))

    # Count place_type per subzone
    type_counts = places.groupby(["subzone_code", "place_type"]).size().unstack(fill_value=0)
    log("Subzones x Types matrix: %d x %d" % type_counts.shape)

    # Only keep types with >= 20 total occurrences
    type_totals = type_counts.sum()
    valid_types = type_totals[type_totals >= 20].index.tolist()
    type_counts = type_counts[valid_types]
    log("Valid types (>=20 occurrences): %d" % len(valid_types))

    # Convert to binary presence (1 if type exists in subzone, 0 otherwise)
    presence = (type_counts > 0).astype(int)
    n_subzones = len(presence)

    # Compute PMI for all pairs
    # PMI(a,b) = log2( P(a,b) / (P(a) * P(b)) )
    # P(a) = fraction of subzones with type a
    # P(a,b) = fraction of subzones with both a and b

    p_single = presence.mean()  # P(type) for each type
    co_occurrence = presence.T.dot(presence) / n_subzones  # P(a,b) matrix

    pmi_matrix = {}
    pmi_edges = []

    for i, type_a in enumerate(valid_types):
        for j, type_b in enumerate(valid_types):
            if i >= j:
                continue
            p_a = p_single[type_a]
            p_b = p_single[type_b]
            p_ab = co_occurrence.loc[type_a, type_b]

            if p_a > 0 and p_b > 0 and p_ab > 0:
                pmi = np.log2(p_ab / (p_a * p_b))
            else:
                pmi = -10  # strong negative

            if abs(pmi) > 0.5:  # only keep meaningful associations
                pmi_edges.append({
                    "type_a": type_a,
                    "type_b": type_b,
                    "pmi": round(pmi, 3),
                    "co_occurrence_pct": round(p_ab * 100, 1),
                })

    # Sort by absolute PMI
    pmi_edges.sort(key=lambda x: -abs(x["pmi"]))

    graph = {
        "type": "colocation_pmi",
        "place_types": len(valid_types),
        "edge_count": len(pmi_edges),
        "edges": pmi_edges,
    }

    outpath = OUT + "/colocation_pmi.json"
    with open(outpath, "w") as f:
        json.dump(graph, f, indent=2)

    # Stats
    positive = sum(1 for e in pmi_edges if e["pmi"] > 0)
    negative = sum(1 for e in pmi_edges if e["pmi"] < 0)

    log("PMI edges: %d (positive: %d, negative: %d)" % (len(pmi_edges), positive, negative))
    log("\nTop 10 co-locating pairs (highest PMI):")
    for e in pmi_edges[:10]:
        log("  %.2f  %s <-> %s (%.1f%% co-occur)" % (e["pmi"], e["type_a"], e["type_b"], e["co_occurrence_pct"]))

    log("\nTop 10 avoiding pairs (lowest PMI):")
    for e in sorted(pmi_edges, key=lambda x: x["pmi"])[:10]:
        log("  %.2f  %s <-> %s (%.1f%% co-occur)" % (e["pmi"], e["type_a"], e["type_b"], e["co_occurrence_pct"]))

    assert len(pmi_edges) >= 100, "Too few PMI edges"
    log("Co-location PMI: PASSED")

    return graph


# ============================================================
# STEP 16: TRANSIT CONNECTIVITY GRAPH
# ============================================================
def step_16_transit():
    log("\n" + "=" * 60)
    log("STEP 16: TRANSIT CONNECTIVITY GRAPH")
    log("=" * 60)

    sz = gpd.read_file(BASE + "/boundaries/subzones.geojson")

    # Load MRT stations with names
    mrt_path = None
    for d in ["transit_updated", "new_datasets"]:
        p = "%s/%s/train_stations_mar2026.geojson" % (BASE, d)
        if os.path.exists(p):
            mrt_path = p
            break

    mrt = gpd.read_file(mrt_path)
    log("MRT stations: %d" % len(mrt))

    # Assign each MRT station to a subzone
    mrt_centroids = mrt.copy()
    mrt_centroids["geometry"] = mrt_centroids.geometry.centroid
    mrt_sz = gpd.sjoin(mrt_centroids, sz[["SUBZONE_C", "SUBZONE_N", "geometry"]], how="left", predicate="within")
    log("MRT stations with subzone: %d" % mrt_sz["SUBZONE_C"].notna().sum())

    # Build transit connectivity: if two MRT stations are adjacent on a line,
    # their subzones are connected
    # Since we don't have line data explicitly linking stations, use proximity:
    # stations within 2km of each other on the same rail corridor = connected

    from math import radians, sin, cos, sqrt, atan2
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371000
        dlat, dlon = radians(lat2-lat1), radians(lon2-lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
        return R * 2 * atan2(sqrt(a), sqrt(1-a))

    # Get station points
    stations = []
    for _, row in mrt_sz.iterrows():
        c = row.geometry
        if c and not c.is_empty and row.get("SUBZONE_C"):
            name_col = [col for col in mrt_sz.columns if "STN_NAM" in col.upper() or "STATION" in col.upper() or "NAME" in col.upper()]
            stn_name = row[name_col[0]] if name_col else "Station_%d" % len(stations)
            stations.append({
                "lat": c.y, "lon": c.x,
                "subzone_code": row["SUBZONE_C"],
                "name": stn_name,
            })

    # Connect stations within 3km (typical MRT inter-station distance)
    edges = []
    connected_sz_pairs = set()

    for i, s1 in enumerate(stations):
        for j, s2 in enumerate(stations):
            if i >= j:
                continue
            dist = haversine(s1["lat"], s1["lon"], s2["lat"], s2["lon"])
            if dist <= 3000:  # 3km
                sz_pair = tuple(sorted([s1["subzone_code"], s2["subzone_code"]]))
                if sz_pair[0] != sz_pair[1] and sz_pair not in connected_sz_pairs:
                    connected_sz_pairs.add(sz_pair)
                    edges.append({
                        "source": sz_pair[0],
                        "target": sz_pair[1],
                        "distance_m": round(dist),
                        "station_a": s1["name"],
                        "station_b": s2["name"],
                        "type": "mrt_connected",
                    })

    # Subzones with MRT
    sz_with_mrt = set()
    for s in stations:
        sz_with_mrt.add(s["subzone_code"])

    graph = {
        "type": "transit_connectivity",
        "subzones_with_mrt": len(sz_with_mrt),
        "mrt_stations": len(stations),
        "edge_count": len(edges),
        "nodes_with_mrt": list(sz_with_mrt),
        "edges": edges,
    }

    outpath = OUT + "/transit_connectivity.json"
    with open(outpath, "w") as f:
        json.dump(graph, f, indent=2)

    log("Subzones with MRT: %d" % len(sz_with_mrt))
    log("Transit edges: %d" % len(edges))

    assert len(edges) >= 50, "Too few transit edges: %d" % len(edges)
    assert len(sz_with_mrt) >= 50, "Too few subzones with MRT"
    log("Transit connectivity: PASSED")

    return graph


# ============================================================
# RUN ALL
# ============================================================
if __name__ == "__main__":
    results = {}
    for name, func in [
        ("adjacency", step_14_adjacency),
        ("colocation_pmi", step_15_colocation),
        ("transit_connectivity", step_16_transit),
    ]:
        try:
            func()
            results[name] = "OK"
        except Exception as e:
            log("FAILED: %s - %s" % (name, str(e)[:200]))
            results[name] = "FAIL"

    log("\n" + "=" * 60)
    log("GRAPH CONSTRUCTION COMPLETE")
    log("=" * 60)
    for name, status in results.items():
        log("  [%s] %s" % (status, name))

    log("\nGraph files:")
    for f in sorted(os.listdir(OUT)):
        fp = os.path.join(OUT, f)
        log("  %s: %.1f KB" % (f, os.path.getsize(fp)/1024))
