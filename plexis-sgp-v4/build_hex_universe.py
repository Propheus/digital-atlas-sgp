"""
Plexis SGP v4 — Stage 0: build hex-8 + hex-9 universe with STRICT coverage.

Pipeline:
  1. For each resolution, run polyfill per subzone with k=3 buffer, fall back
     to centroid cell if polyfill is empty (small subzones).
  2. For hex-8, add parent-closure of all hex-9 cells.
  3. For hex-8, also add the hex-8 cell containing every subzone's
     representative point (guarantees every subzone has a home cell).
  4. Build cell<->subzone overlap table via spatial index: for each cell,
     find all subzones whose bbox intersects; test intersection; record overlap.
  5. Canonical parent_subzone = max-overlap subzone for that cell.
"""
import json, time
from pathlib import Path
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely.prepared import prep
from shapely.strtree import STRtree
import h3

ROOT = Path("/home/azureuser/plexis-sgp-v4")
SUBZONE_PATH = ROOT / "boundaries" / "subzones.geojson"


def h3shape_for(polygon):
    ext = [[y, x] for x, y in polygon.exterior.coords]
    holes = [[[y, x] for x, y in ring.coords] for ring in polygon.interiors]
    return h3.LatLngPoly(ext, *holes)


def ring_buffer(cells, k=3):
    out = set(cells)
    for c in list(cells):
        for nc in h3.grid_disk(c, k):
            out.add(nc)
    return out


def cell_poly(c):
    ring = [(lng, lat) for lat, lng in h3.cell_to_boundary(c)]
    return Polygon(ring)


def seed_cells(polygon, res, buffer_k=7):
    """Return candidate cells that might intersect polygon (polyfill + k-ring buffer).
    Fall back to centroid cell + k=1 if polyfill empty."""
    polys = [polygon] if polygon.geom_type == "Polygon" else list(polygon.geoms)
    seeds = set()
    for p in polys:
        try:
            seeds |= set(h3.h3shape_to_cells(h3shape_for(p), res))
        except Exception:
            pass
    if not seeds:
        pt = polygon.representative_point()
        seeds = {h3.latlng_to_cell(pt.y, pt.x, res)}
    return ring_buffer(seeds, k=buffer_k)


def filter_intersecting(candidate_cells, polygon):
    prepared = prep(polygon)
    return {c for c in candidate_cells if prepared.intersects(cell_poly(c))}


def build_universe(gdf, res, extra_cells=()):
    """Build a hex universe for one resolution. Returns:
        all_cells (set), overlap_rows (list of (cell, subz, overlap_area_deg2))
    """
    # Phase A: collect all candidate cells from per-subzone polyfill
    all_cells = set()
    t = time.time()
    for idx, row in gdf.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
        seeds = seed_cells(geom, res, buffer_k=7)
        all_cells |= filter_intersecting(seeds, geom)
    # Always add representative-point cell per subzone
    for idx, row in gdf.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
        pt = geom.representative_point()
        all_cells.add(h3.latlng_to_cell(pt.y, pt.x, res))
    # Plus any extras (e.g., parent-closure)
    for c in extra_cells:
        all_cells.add(c)
    print(f"  [{res}] candidate cells: {len(all_cells):,}  ({time.time()-t:.1f}s)")

    # Phase B: global overlap table via STRtree
    t = time.time()
    geoms = list(gdf.geometry.values)
    codes = list(gdf["SUBZONE_C"].values)
    tree = STRtree(geoms)
    overlap_rows = []
    for c in all_cells:
        cp = cell_poly(c)
        idxs = tree.query(cp)
        for i in idxs:
            sz_geom = geoms[i]
            if cp.intersects(sz_geom):
                try:
                    ov = cp.intersection(sz_geom).area
                except Exception:
                    ov = 0
                if ov > 0:
                    overlap_rows.append((c, codes[i], ov))
    print(f"  [{res}] overlap rows: {len(overlap_rows):,}  ({time.time()-t:.1f}s)")
    return all_cells, overlap_rows


def canonical_parents(overlap_rows, res_key):
    df = pd.DataFrame(overlap_rows, columns=[res_key, "subzone_c", "overlap_deg2"])
    idx_max = df.groupby(res_key)["overlap_deg2"].idxmax()
    return df.loc[idx_max].set_index(res_key)["subzone_c"].to_dict(), df


def main():
    t0 = time.time()
    print(f"Reading {SUBZONE_PATH}")
    gdf = gpd.read_file(SUBZONE_PATH).to_crs(4326)
    print(f"  {len(gdf)} subzones loaded")
    sgp_union = unary_union(gdf.geometry.values)
    total_km2 = gpd.GeoSeries([sgp_union], crs=4326).to_crs(3414).iloc[0].area / 1e6
    print(f"  Total area: {total_km2:.2f} km²")

    # ---- hex-9 ----
    print("\n--- hex-9 ---")
    all_h9, overlap_h9 = build_universe(gdf, 9)
    parents9, df_ov_h9 = canonical_parents(overlap_h9, "hex9_id")

    # ---- hex-8 with parent-closure of hex-9 ----
    print("\n--- hex-8 (with parent-closure) ---")
    h9_parents_in_h8 = {h3.cell_to_parent(c, 8) for c in all_h9}
    all_h8, overlap_h8 = build_universe(gdf, 8, extra_cells=h9_parents_in_h8)
    parents8, df_ov_h8 = canonical_parents(overlap_h8, "hex8_id")

    # Any cells that ended up with zero overlap (degenerate) — assign by nearest subzone centroid
    for c in all_h9 - set(parents9.keys()):
        lat, lng = h3.cell_to_latlng(c)
        pt = Point(lng, lat)
        # use projected for nearest
        sz_proj = gdf.to_crs(3414)
        pt_proj = gpd.GeoSeries([pt], crs=4326).to_crs(3414).iloc[0]
        idx = sz_proj.geometry.distance(pt_proj).idxmin()
        parents9[c] = gdf.iloc[idx]["SUBZONE_C"]
    for c in all_h8 - set(parents8.keys()):
        lat, lng = h3.cell_to_latlng(c)
        pt = Point(lng, lat)
        sz_proj = gdf.to_crs(3414)
        pt_proj = gpd.GeoSeries([pt], crs=4326).to_crs(3414).iloc[0]
        idx = sz_proj.geometry.distance(pt_proj).idxmin()
        parents8[c] = gdf.iloc[idx]["SUBZONE_C"]

    # ---- Phase C: confirm every subzone has >=1 overlapping cell ----
    for res, df_ov, name in [(9, df_ov_h9, "hex9"), (8, df_ov_h8, "hex8")]:
        sz_with_cell = set(df_ov["subzone_c"].unique())
        missing = set(gdf["SUBZONE_C"]) - sz_with_cell
        if missing:
            print(f"  NOTE: {len(missing)} subzones have no >0 overlap at {name} (nested inside cells) — captured via representative-point cell")

    # ---- Write outputs ----
    sz_lookup = gdf.set_index("SUBZONE_C")
    def row_for(c, res, parent_map):
        lat, lng = h3.cell_to_latlng(c)
        subz = parent_map[c]
        rec = sz_lookup.loc[subz]
        out = {
            f"hex{res}_id": c,
            "lat": lat, "lng": lng,
            "parent_subzone": subz,
            "parent_subzone_name": rec["SUBZONE_N"],
            "parent_pa": rec["PLN_AREA_N"],
            "parent_region": rec["REGION_N"],
        }
        if res == 9:
            out["parent_hex8"] = h3.cell_to_parent(c, 8)
        return out

    df_h9 = pd.DataFrame([row_for(c, 9, parents9) for c in sorted(all_h9)])
    df_h8 = pd.DataFrame([row_for(c, 8, parents8) for c in sorted(all_h8)])
    df_h9.to_parquet(ROOT / "hex" / "hex9_universe.parquet", index=False)
    df_h8.to_parquet(ROOT / "hex" / "hex8_universe.parquet", index=False)
    df_ov_h9.to_parquet(ROOT / "hex" / "hex9_subzone_overlap.parquet", index=False)
    df_ov_h8.to_parquet(ROOT / "hex" / "hex8_subzone_overlap.parquet", index=False)

    # GeoJSONs
    for df, res in [(df_h9, 9), (df_h8, 8)]:
        gj = {"type": "FeatureCollection", "features": []}
        for _, r in df.iterrows():
            c = r[f"hex{res}_id"]
            ring = [[lng, lat] for lat, lng in h3.cell_to_boundary(c)]
            ring.append(ring[0])
            gj["features"].append({
                "type": "Feature",
                "properties": {
                    "hex_id": c,
                    "res": res,
                    "parent_subzone": r["parent_subzone"],
                    "parent_pa": r["parent_pa"],
                },
                "geometry": {"type": "Polygon", "coordinates": [ring]},
            })
        with open(ROOT / "hex" / f"hex{res}_universe.geojson", "w") as f:
            json.dump(gj, f)

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "subzones": len(gdf),
        "total_area_km2": round(total_km2, 2),
        "hex8": {"count": len(all_h8), "m2m_overlap_rows": len(df_ov_h8)},
        "hex9": {"count": len(all_h9), "m2m_overlap_rows": len(df_ov_h9)},
        "wall_clock_s": round(time.time() - t0, 2),
    }
    with open(ROOT / "hex" / "universe_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSummary:\n{json.dumps(summary, indent=2)}")


if __name__ == "__main__":
    main()
