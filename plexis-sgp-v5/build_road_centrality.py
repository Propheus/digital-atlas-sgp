"""
Plexis SGP v4 — Stage 6g: global graph centrality features per hex-9.

Builds the major-road subgraph (motorway + trunk + primary + secondary), computes:
  - betweenness centrality (sample-based for tractability)
  - closeness centrality
  - PageRank
  - eigenvector centrality
  - bridges (Tarjan's algorithm — edges whose removal disconnects)

Aggregates per hex (mean + max).

Output: hex/hex9_road_centrality.parquet (7,318 × ~12)
"""
import json, os, time
from pathlib import Path
import pandas as pd
import geopandas as gpd
import numpy as np
import networkx as nx
from shapely.geometry import Point
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
HEX9 = ROOT / "hex/hex9_universe.parquet"
OUT_PQ = ROOT / "hex/hex9_road_centrality.parquet"
REPORT = ROOT / "hex/road_centrality_report.json"

MAJOR_CLASSES = {"motorway", "motorway_link", "trunk", "trunk_link",
                 "primary", "primary_link", "secondary", "secondary_link"}


def main():
    t0 = time.time()
    print("Loading roads...")
    roads = gpd.read_file(ROADS_GEO).to_crs(4326)
    print(f"  total: {len(roads):,}")
    major = roads[roads["highway"].isin(MAJOR_CLASSES)].copy()
    print(f"  major (motorway+trunk+primary+secondary + links): {len(major):,}")

    # Build NetworkX graph from u/v
    print("\n  Building major-road graph...")
    G = nx.Graph()
    for _, r in major.iterrows():
        # Use length as edge weight for distance-based centralities
        G.add_edge(r["u"], r["v"], weight=float(r["length"]))
    print(f"  G: {G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges")

    # Get coordinates per node from the road geojson — use endpoints
    print("  Extracting node coordinates...")
    node_coords = {}
    for _, r in major.iterrows():
        # geometry is LineString; coords[0] = u endpoint, coords[-1] = v endpoint
        coords = list(r["geometry"].coords)
        if r["u"] not in node_coords:
            node_coords[r["u"]] = coords[0]  # (lng, lat)
        if r["v"] not in node_coords:
            node_coords[r["v"]] = coords[-1]
    print(f"  coords for {len(node_coords):,} nodes")

    # Centrality calculations on the largest connected component (otherwise some are infinite)
    print("\n  Identifying largest connected component...")
    components = list(nx.connected_components(G))
    components.sort(key=len, reverse=True)
    print(f"  components: {len(components)}, largest: {len(components[0]):,} nodes")
    G_main = G.subgraph(components[0]).copy()

    # === Betweenness (sample-based for tractability) ===
    print("\n  Betweenness centrality (k=500 sample)...")
    t = time.time()
    bw = nx.betweenness_centrality(G_main, k=min(500, G_main.number_of_nodes()),
                                    weight="weight", seed=42)
    print(f"    done ({time.time()-t:.1f}s)")

    # === Closeness ===
    print("  Closeness centrality (sample-based via approximation)...")
    t = time.time()
    # Full closeness on 30K nodes is ~5 min. Sample-based via a function: for each node,
    # estimate from k random sources. NetworkX doesn't have built-in, so use harmonic centrality
    # which is more robust on partial connectivity.
    # Alternative: just use harmonic_centrality which is faster per node.
    # For tractability, compute on a subsample of 1000 nodes and propagate via mean.
    # Best balance: harmonic_centrality on full G_main, ~1-2 min.
    cl = nx.harmonic_centrality(G_main, distance="weight")
    # Normalize
    n = len(cl)
    if n > 0:
        max_cl = max(cl.values())
        if max_cl > 0:
            cl = {k: v / max_cl for k, v in cl.items()}
    print(f"    done ({time.time()-t:.1f}s)")

    # === PageRank ===
    print("  PageRank...")
    t = time.time()
    pr = nx.pagerank(G_main, weight="weight")
    print(f"    done ({time.time()-t:.1f}s)")

    # === Bridges ===
    print("  Bridges (Tarjan)...")
    t = time.time()
    bridges = list(nx.bridges(G_main))
    bridge_edges = set(tuple(sorted(e)) for e in bridges)
    print(f"    bridges: {len(bridges):,} edges ({time.time()-t:.1f}s)")

    # === Eigenvector centrality ===
    print("  Eigenvector centrality (power iteration)...")
    t = time.time()
    try:
        ev = nx.eigenvector_centrality(G_main, max_iter=1000, tol=1e-6, weight="weight")
    except Exception as e:
        print(f"    eigenvector failed: {e}, using NumPy")
        ev = nx.eigenvector_centrality_numpy(G_main, weight="weight")
    print(f"    done ({time.time()-t:.1f}s)")

    # === Per-hex aggregation ===
    print("\n  Hashing nodes to hex-9...")
    h9 = pd.read_parquet(HEX9)
    node_hex = {}
    for n, (lng, lat) in node_coords.items():
        if n in G_main:
            node_hex[n] = h3.latlng_to_cell(lat, lng, 9)

    # Per-node values
    rows = []
    for n in G_main.nodes:
        if n not in node_hex: continue
        rows.append({
            "node": n,
            "hex9_id": node_hex[n],
            "betweenness": bw.get(n, 0),
            "closeness": cl.get(n, 0),
            "pagerank": pr.get(n, 0),
            "eigenvector": ev.get(n, 0),
        })
    node_df = pd.DataFrame(rows)
    print(f"  node-hex rows: {len(node_df):,}")

    # Per-hex aggregation
    agg = node_df.groupby("hex9_id").agg(
        centr_node_count=("node", "count"),
        centr_betweenness_mean=("betweenness", "mean"),
        centr_betweenness_max=("betweenness", "max"),
        centr_closeness_mean=("closeness", "mean"),
        centr_closeness_max=("closeness", "max"),
        centr_pagerank_mean=("pagerank", "mean"),
        centr_pagerank_max=("pagerank", "max"),
        centr_eigenvector_mean=("eigenvector", "mean"),
        centr_eigenvector_max=("eigenvector", "max"),
    ).reset_index()

    # Bridge counts per hex (count edges where both endpoints in same hex; if straddle, count for both)
    bridge_rows = []
    for u, v in bridges:
        hu = node_hex.get(u)
        hv = node_hex.get(v)
        if hu: bridge_rows.append({"hex9_id": hu})
        if hv and hv != hu: bridge_rows.append({"hex9_id": hv})
    bridge_df = pd.DataFrame(bridge_rows)
    if len(bridge_df) > 0:
        bridge_agg = bridge_df.groupby("hex9_id").size().reset_index(name="centr_bridge_count")
    else:
        bridge_agg = pd.DataFrame(columns=["hex9_id", "centr_bridge_count"])

    # Final
    out = h9[["hex9_id"]].merge(agg, on="hex9_id", how="left").merge(bridge_agg, on="hex9_id", how="left")
    for c in out.columns:
        if c != "hex9_id":
            out[c] = out[c].fillna(0)

    out.to_parquet(OUT_PQ, index=False)
    print(f"\n  Centrality parquet: {out.shape}")

    # Summary + top hexes
    h9_lookup = h9[["hex9_id", "parent_subzone_name", "parent_pa"]].rename(
        columns={"parent_subzone_name": "subz", "parent_pa": "pa"})
    top_bw = out.nlargest(10, "centr_betweenness_max").merge(h9_lookup, on="hex9_id")
    print(f"\n  Top 10 hexes by max betweenness:")
    for _, r in top_bw.iterrows():
        print(f"    {r['hex9_id']:<18}  bw={r['centr_betweenness_max']:.5f}  nodes={int(r['centr_node_count'])}  {str(r['subz']):<25} ({r['pa']})")

    top_pr = out.nlargest(10, "centr_pagerank_max").merge(h9_lookup, on="hex9_id")
    print(f"\n  Top 10 hexes by max PageRank:")
    for _, r in top_pr.iterrows():
        print(f"    {r['hex9_id']:<18}  pr={r['centr_pagerank_max']:.5f}  nodes={int(r['centr_node_count'])}  {str(r['subz']):<25} ({r['pa']})")

    top_br = out.nlargest(10, "centr_bridge_count").merge(h9_lookup, on="hex9_id")
    print(f"\n  Top 10 hexes by bridge count (severance flags):")
    for _, r in top_br.iterrows():
        print(f"    {r['hex9_id']:<18}  bridges={int(r['centr_bridge_count'])}  {str(r['subz']):<25} ({r['pa']})")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "graph": {
            "major_roads_input": int(len(major)),
            "G_nodes": int(G.number_of_nodes()),
            "G_edges": int(G.number_of_edges()),
            "G_main_nodes": int(G_main.number_of_nodes()),
            "G_main_edges": int(G_main.number_of_edges()),
            "components_total": len(components),
            "bridges": int(len(bridges)),
        },
        "hexes_with_centrality": int((out["centr_node_count"] > 0).sum()),
        "max_betweenness": float(out["centr_betweenness_max"].max()),
        "max_pagerank": float(out["centr_pagerank_max"].max()),
        "max_bridge_count": int(out["centr_bridge_count"].max()),
    }
    with open(REPORT, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n{json.dumps(summary, indent=2)}")
    print(f"\nOutput: {OUT_PQ}")


if __name__ == "__main__":
    main()
