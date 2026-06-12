"""
Plexis SGP v4 — admin boundaries builder.
Produces three extra boundary layers + hex overlap tables:
  - planning_areas.geojson (55)  — URA planning areas (copy from source)
  - regions.geojson (5)          — dissolved from planning areas
  - hdb_towns.geojson (27)       — derived from HDB block polygons + property_info
"""
import json
import re
import time
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree
import os
import h3

V4 = Path(__file__).parent


def _resolve_src():
    if os.environ.get("PLEXIS_SRC_REPO"):
        return Path(os.environ["PLEXIS_SRC_REPO"])
    for c in [
        Path("/home/azureuser/digital-atlas-sgp"),
        V4.parent,
    ]:
        if (c / "data/boundaries/planning_areas.geojson").exists():
            return c
    raise FileNotFoundError("Cannot find digital-atlas-sgp source repo")


SRC = _resolve_src()

# HDB town code -> full name (matches resale data casing)
HDB_CODE_TO_NAME = {
    "AMK": "ANG MO KIO", "BB": "BUKIT BATOK", "BD": "BEDOK", "BH": "BISHAN",
    "BM": "BUKIT MERAH", "BP": "BUKIT PANJANG", "BT": "BUKIT TIMAH",
    "CCK": "CHOA CHU KANG", "CL": "CLEMENTI", "CT": "CENTRAL AREA",
    "GL": "GEYLANG", "HG": "HOUGANG", "JE": "JURONG EAST", "JW": "JURONG WEST",
    "KWN": "KALLANG/WHAMPOA", "MP": "MARINE PARADE", "PG": "PUNGGOL",
    "PRC": "PASIR RIS", "QT": "QUEENSTOWN", "SB": "SEMBAWANG",
    "SGN": "SERANGOON", "SK": "SENGKANG", "TAP": "TAMPINES", "TG": "TENGAH",
    "TP": "TOA PAYOH", "WL": "WOODLANDS", "YS": "YISHUN",
}


def cell_poly(c):
    return Polygon([(lng, lat) for lat, lng in h3.cell_to_boundary(c)])


def build_overlap(cells, boundary_gdf, key_col, cell_key):
    """For each cell id, compute overlap with every boundary polygon (STRtree indexed)."""
    geoms = list(boundary_gdf.geometry.values)
    keys = list(boundary_gdf[key_col].values)
    tree = STRtree(geoms)
    rows = []
    for c in cells:
        cp = cell_poly(c)
        for i in tree.query(cp):
            g = geoms[i]
            if cp.intersects(g):
                try:
                    ov = cp.intersection(g).area
                except Exception:
                    ov = 0
                if ov > 0:
                    rows.append((c, keys[i], ov))
    df = pd.DataFrame(rows, columns=[cell_key, key_col, "overlap_deg2"])
    return df


def main():
    t0 = time.time()
    print("1) Copy planning areas (55) into v4/boundaries/")
    src_pa = SRC / "data/boundaries/planning_areas.geojson"
    dst_pa = V4 / "boundaries/planning_areas.geojson"
    gdf_pa = gpd.read_file(src_pa).to_crs(4326)
    print(f"   {len(gdf_pa)} planning areas")
    gdf_pa.to_file(dst_pa, driver="GeoJSON")

    print("\n2) Dissolve planning areas -> 5 regions")
    regions = gdf_pa.dissolve(by="REGION_N", aggfunc={"REGION_C": "first"}).reset_index()
    regions = regions[["REGION_N", "REGION_C", "geometry"]]
    print(f"   {len(regions)} regions: {list(regions['REGION_N'])}")
    regions.to_file(V4 / "boundaries/regions.geojson", driver="GeoJSON")

    print("\n3) Derive HDB town polygons from HDB blocks + property_info")
    t = time.time()
    blocks = gpd.read_file(SRC / "data/housing/hdb_existing_buildings.geojson").to_crs(4326)
    info = pd.read_csv(SRC / "data/housing/hdb_property_info.csv")
    print(f"   {len(blocks):,} block polygons, {len(info):,} property_info rows")

    # Join blocks to town via (blk_no, street). Blocks have BLK_NO + ST_COD (code),
    # info has blk_no + street (name). We join on blk_no and use postal/street
    # proximity. Easier: since blocks have POSTAL_COD and info has no postal, we
    # use spatial proximity — for each block, assign the nearest info row's town
    # after filtering by block number.
    # Simplest robust path: normalize blk_no, find best street match.
    blocks["BLK_NO_N"] = blocks["BLK_NO"].astype(str).str.strip().str.upper()
    info["blk_no_n"] = info["blk_no"].astype(str).str.strip().str.upper()
    info["street_norm"] = info["street"].astype(str).str.upper().str.strip()

    # ST_COD in block polygons is a 6-char code — first 3 letters match a street
    # prefix that's deterministic. Rather than reverse that, assign each block
    # to a town via centroid-inside URA-PA as sanity fallback.
    # Approach: use block centroids, nearest-neighbor match to info's geocoded
    # records. But info has no coords. Use block <-> info BLK_NO+STREET keyword
    # matching.
    #
    # Heuristic: for each distinct (blk_no_n, town_code) in info, find blocks
    # with that BLK_NO_N whose nearest-PA name matches expected town.

    # Pragmatic approach: since info covers 13,267 of 13,386 blocks (~99%),
    # and blk_no alone is ambiguous across towns, we use block centroid +
    # nearest-neighbor to a "town centroid" built from existing assignments.
    # Bootstrap: use unique (blk_no_n, town_code) pairs where the town code is
    # uniquely implied.

    # Simpler still: compute block centroid, find the HDB resale record nearest
    # to it that shares blk_no. Resale has town+block+street_name+lat/lng. But
    # resale CSV may not have coords...
    rs_path = SRC / "data/property/hdb_resale_prices.csv"
    rs = pd.read_csv(rs_path, usecols=[c for c in pd.read_csv(rs_path, nrows=0).columns])
    rs_cols = list(rs.columns)
    print(f"   resale cols: {rs_cols}")

    # Use block + street pattern match via info
    # Strategy:
    # 1. Build a dictionary: {(blk_no_n, street_keyword): town_code}
    #    where street_keyword is the first non-stopword token from info.street
    # 2. Blocks have ST_COD (code). We can't reverse the code, but we can use
    #    spatial assignment: associate each block with the nearest town centroid
    #    that is consistent with a small set of info entries.

    # Alternative: use HDB town admin boundary approximation via URA PAs.
    # The 26 HDB towns + TENGAH map deterministically to URA planning areas:
    HDB_TO_URA_PAS = {
        "ANG MO KIO":      ["ANG MO KIO"],
        "BEDOK":           ["BEDOK"],
        "BISHAN":          ["BISHAN"],
        "BUKIT BATOK":     ["BUKIT BATOK"],
        "BUKIT MERAH":     ["BUKIT MERAH"],
        "BUKIT PANJANG":   ["BUKIT PANJANG"],
        "BUKIT TIMAH":     ["BUKIT TIMAH"],
        "CENTRAL AREA":    ["DOWNTOWN CORE","OUTRAM","MUSEUM","NEWTON","RIVER VALLEY","ROCHOR","SINGAPORE RIVER"],
        "CHOA CHU KANG":   ["CHOA CHU KANG"],
        "CLEMENTI":        ["CLEMENTI"],
        "GEYLANG":         ["GEYLANG"],
        "HOUGANG":         ["HOUGANG"],
        "JURONG EAST":     ["JURONG EAST"],
        "JURONG WEST":     ["JURONG WEST"],
        "KALLANG/WHAMPOA": ["KALLANG","NOVENA"],
        "MARINE PARADE":   ["MARINE PARADE"],
        "PASIR RIS":       ["PASIR RIS","CHANGI"],
        "PUNGGOL":         ["PUNGGOL"],
        "QUEENSTOWN":      ["QUEENSTOWN"],
        "SEMBAWANG":       ["SEMBAWANG"],
        "SENGKANG":        ["SENGKANG"],
        "SERANGOON":       ["SERANGOON"],
        "TAMPINES":        ["TAMPINES"],
        "TENGAH":          ["TENGAH"],
        "TOA PAYOH":       ["TOA PAYOH"],
        "WOODLANDS":       ["WOODLANDS"],
        "YISHUN":          ["YISHUN"],
    }

    # Build each town polygon by unioning URA PAs + intersecting with a
    # concave hull of actual HDB blocks with 200m buffer (so we exclude
    # non-HDB portions of PAs like industrial tracts).
    gdf_pa_3414 = gdf_pa.to_crs(3414)
    blocks_3414 = blocks.to_crs(3414)

    # Assign blocks to town via URA PA membership of their centroid
    blocks_3414["centroid"] = blocks_3414.geometry.centroid
    pa_tree = STRtree(gdf_pa_3414.geometry.values)
    pa_names = list(gdf_pa_3414["PLN_AREA_N"].values)

    def pa_of_point(pt):
        for i in pa_tree.query(pt):
            if gdf_pa_3414.geometry.iloc[i].contains(pt):
                return pa_names[i]
        # Fallback: nearest
        dists = gdf_pa_3414.geometry.distance(pt)
        return pa_names[dists.idxmin()]

    blocks_3414["pa"] = blocks_3414["centroid"].apply(pa_of_point)

    # Now assign each block to an HDB town based on its PA
    PA_TO_HDB = {}
    for town, pas in HDB_TO_URA_PAS.items():
        for pa in pas:
            PA_TO_HDB[pa] = town
    blocks_3414["hdb_town"] = blocks_3414["pa"].map(PA_TO_HDB)

    town_counts = blocks_3414["hdb_town"].value_counts(dropna=False)
    unassigned = blocks_3414["hdb_town"].isna().sum()
    print(f"   blocks assigned to HDB town: {len(blocks_3414)-unassigned:,}/{len(blocks_3414):,}")
    print(f"   unassigned blocks (PA not in HDB map): {unassigned}")
    print("   top town assignments:")
    for t, c in town_counts.head(10).items():
        print(f"     {str(t):25s}  {c:,}")

    # Build town polygons: buffer each block 200 m, union per town
    t2 = time.time()
    town_polys = []
    for town, sub in blocks_3414.dropna(subset=["hdb_town"]).groupby("hdb_town"):
        # buffer 200 m around each block polygon, union
        buffered = sub.geometry.buffer(200)
        union_3414 = unary_union(buffered.values)
        town_polys.append({"hdb_town": town, "geometry": union_3414, "n_blocks": len(sub)})
    gdf_towns_3414 = gpd.GeoDataFrame(town_polys, crs=3414)
    # Ensure polygon (not multipolygon); a few might be. Keep as-is for realism.
    gdf_towns = gdf_towns_3414.to_crs(4326)
    gdf_towns.to_file(V4 / "boundaries/hdb_towns.geojson", driver="GeoJSON")
    print(f"   {len(gdf_towns)} HDB town polygons written  ({time.time()-t2:.1f}s)")

    # ---- Build overlap tables for hex-9 and hex-8 ----
    print("\n4) Build hex -> admin overlap tables")
    h9 = pd.read_parquet(V4 / "hex/hex9_universe.parquet")
    h8 = pd.read_parquet(V4 / "hex/hex8_universe.parquet")

    # Planning area overlaps
    print("   hex-9 x planning areas...")
    ov_h9_pa = build_overlap(h9["hex9_id"].tolist(), gdf_pa, "PLN_AREA_N", "hex9_id")
    print(f"     {len(ov_h9_pa):,} rows")
    print("   hex-8 x planning areas...")
    ov_h8_pa = build_overlap(h8["hex8_id"].tolist(), gdf_pa, "PLN_AREA_N", "hex8_id")
    print(f"     {len(ov_h8_pa):,} rows")

    print("   hex-9 x regions...")
    ov_h9_rg = build_overlap(h9["hex9_id"].tolist(), regions, "REGION_N", "hex9_id")
    print(f"     {len(ov_h9_rg):,} rows")
    print("   hex-8 x regions...")
    ov_h8_rg = build_overlap(h8["hex8_id"].tolist(), regions, "REGION_N", "hex8_id")
    print(f"     {len(ov_h8_rg):,} rows")

    print("   hex-9 x HDB towns...")
    ov_h9_hdb = build_overlap(h9["hex9_id"].tolist(), gdf_towns, "hdb_town", "hex9_id")
    print(f"     {len(ov_h9_hdb):,} rows")
    print("   hex-8 x HDB towns...")
    ov_h8_hdb = build_overlap(h8["hex8_id"].tolist(), gdf_towns, "hdb_town", "hex8_id")
    print(f"     {len(ov_h8_hdb):,} rows")

    # Save
    ov_h9_pa.to_parquet(V4 / "hex/hex9_pa_overlap.parquet", index=False)
    ov_h8_pa.to_parquet(V4 / "hex/hex8_pa_overlap.parquet", index=False)
    ov_h9_rg.to_parquet(V4 / "hex/hex9_region_overlap.parquet", index=False)
    ov_h8_rg.to_parquet(V4 / "hex/hex8_region_overlap.parquet", index=False)
    ov_h9_hdb.to_parquet(V4 / "hex/hex9_hdb_town_overlap.parquet", index=False)
    ov_h8_hdb.to_parquet(V4 / "hex/hex8_hdb_town_overlap.parquet", index=False)

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "planning_areas": len(gdf_pa),
        "regions": len(regions),
        "hdb_towns": len(gdf_towns),
        "blocks_assigned": int(len(blocks_3414) - unassigned),
        "blocks_total": len(blocks_3414),
        "overlap_rows": {
            "hex9_pa": len(ov_h9_pa),
            "hex8_pa": len(ov_h8_pa),
            "hex9_region": len(ov_h9_rg),
            "hex8_region": len(ov_h8_rg),
            "hex9_hdb_town": len(ov_h9_hdb),
            "hex8_hdb_town": len(ov_h8_hdb),
        },
        "wall_clock_s": round(time.time() - t0, 2),
    }
    with open(V4 / "hex/admin_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSummary:\n{json.dumps(summary, indent=2)}")


if __name__ == "__main__":
    main()
