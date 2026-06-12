"""
Post-sweep to guarantee 100% coverage:
  For every subzone, compute the polyfill + k=20 buffer + intersection filter,
  and add any missing cells to the existing hex universe.
"""
import json, time
from pathlib import Path
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon
from shapely.ops import unary_union
import h3

ROOT = Path("/home/azureuser/plexis-sgp-v4")


def cell_poly(c):
    return Polygon([(lng, lat) for lat, lng in h3.cell_to_boundary(c)])


def generous_intersecting_cells(geom, res, k=20):
    polys = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
    seeds = set()
    for p in polys:
        ext = [[y, x] for x, y in p.exterior.coords]
        holes = [[[y, x] for x, y in r.coords] for r in p.interiors]
        try:
            seeds |= set(h3.h3shape_to_cells(h3.LatLngPoly(ext, *holes), res))
        except Exception:
            pass
    if not seeds:
        pt = geom.representative_point()
        seeds = {h3.latlng_to_cell(pt.y, pt.x, res)}
    cand = set(seeds)
    for c in list(seeds):
        for nc in h3.grid_disk(c, k):
            cand.add(nc)
    out = set()
    for c in cand:
        if cell_poly(c).intersects(geom):
            out.add(c)
    return out


def main():
    t0 = time.time()
    gdf = gpd.read_file(ROOT / "boundaries" / "subzones.geojson").to_crs(4326)
    h9 = pd.read_parquet(ROOT / "hex" / "hex9_universe.parquet")
    h8 = pd.read_parquet(ROOT / "hex" / "hex8_universe.parquet")
    ov9 = pd.read_parquet(ROOT / "hex" / "hex9_subzone_overlap.parquet")
    ov8 = pd.read_parquet(ROOT / "hex" / "hex8_subzone_overlap.parquet")
    h9_set = set(h9["hex9_id"])
    h8_set = set(h8["hex8_id"])
    print(f"Before: hex9={len(h9_set):,}  hex8={len(h8_set):,}  ov9={len(ov9):,}  ov8={len(ov8):,}")

    added_h9, added_h8 = set(), set()
    new_ov9, new_ov8 = [], []
    for _, row in gdf.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
        sz = row["SUBZONE_C"]
        for res, existing, added_set, new_ov in [
            (9, h9_set, added_h9, new_ov9),
            (8, h8_set, added_h8, new_ov8),
        ]:
            cells = generous_intersecting_cells(geom, res, k=20)
            new = cells - existing
            for c in new:
                existing.add(c)
                added_set.add(c)
            # also recompute overlap area for each (cell, sz)
            for c in cells:
                try:
                    ov = cell_poly(c).intersection(geom).area
                except Exception:
                    ov = 0
                if ov > 0:
                    new_ov.append((c, sz, ov))
    print(f"After sweep: added hex9={len(added_h9)}  added hex8={len(added_h8)}")

    # Recompute parent assignments from fresh overlap tables
    df_ov9 = pd.DataFrame(new_ov9, columns=["hex9_id", "subzone_c", "overlap_deg2"]).drop_duplicates(subset=["hex9_id", "subzone_c"])
    df_ov8 = pd.DataFrame(new_ov8, columns=["hex8_id", "subzone_c", "overlap_deg2"]).drop_duplicates(subset=["hex8_id", "subzone_c"])
    # Combine with old overlap to catch all
    df_ov9 = pd.concat([ov9, df_ov9], ignore_index=True).drop_duplicates(subset=["hex9_id", "subzone_c"])
    df_ov8 = pd.concat([ov8, df_ov8], ignore_index=True).drop_duplicates(subset=["hex8_id", "subzone_c"])

    # Parent-closure for hex-8
    for c in h9_set:
        p = h3.cell_to_parent(c, 8)
        if p not in h8_set:
            h8_set.add(p)

    # Compute parent_subzone = max-overlap
    idx_max9 = df_ov9.groupby("hex9_id")["overlap_deg2"].idxmax()
    parents9 = df_ov9.loc[idx_max9].set_index("hex9_id")["subzone_c"].to_dict()
    idx_max8 = df_ov8.groupby("hex8_id")["overlap_deg2"].idxmax()
    parents8 = df_ov8.loc[idx_max8].set_index("hex8_id")["subzone_c"].to_dict()

    # Nearest-fallback for any without a parent
    gdf_proj = gdf.to_crs(3414)
    from shapely.geometry import Point
    for pool, parents, res in [(h9_set, parents9, 9), (h8_set, parents8, 8)]:
        for c in pool - set(parents.keys()):
            lat, lng = h3.cell_to_latlng(c)
            pt_proj = gpd.GeoSeries([Point(lng, lat)], crs=4326).to_crs(3414).iloc[0]
            idx = gdf_proj.geometry.distance(pt_proj).idxmin()
            parents[c] = gdf.iloc[idx]["SUBZONE_C"]

    sz_lookup = gdf.set_index("SUBZONE_C")
    def row_for(c, res, parent_map):
        lat, lng = h3.cell_to_latlng(c)
        subz = parent_map[c]
        rec = sz_lookup.loc[subz]
        out = {
            f"hex{res}_id": c, "lat": lat, "lng": lng,
            "parent_subzone": subz,
            "parent_subzone_name": rec["SUBZONE_N"],
            "parent_pa": rec["PLN_AREA_N"],
            "parent_region": rec["REGION_N"],
        }
        if res == 9:
            out["parent_hex8"] = h3.cell_to_parent(c, 8)
        return out

    df_h9 = pd.DataFrame([row_for(c, 9, parents9) for c in sorted(h9_set)])
    df_h8 = pd.DataFrame([row_for(c, 8, parents8) for c in sorted(h8_set)])
    df_h9.to_parquet(ROOT / "hex" / "hex9_universe.parquet", index=False)
    df_h8.to_parquet(ROOT / "hex" / "hex8_universe.parquet", index=False)
    df_ov9.to_parquet(ROOT / "hex" / "hex9_subzone_overlap.parquet", index=False)
    df_ov8.to_parquet(ROOT / "hex" / "hex8_subzone_overlap.parquet", index=False)

    # Refresh GeoJSON
    for df, res in [(df_h9, 9), (df_h8, 8)]:
        gj = {"type": "FeatureCollection", "features": []}
        for _, r in df.iterrows():
            c = r[f"hex{res}_id"]
            ring = [[lng, lat] for lat, lng in h3.cell_to_boundary(c)]
            ring.append(ring[0])
            gj["features"].append({
                "type": "Feature",
                "properties": {
                    "hex_id": c, "res": res,
                    "parent_subzone": r["parent_subzone"],
                    "parent_pa": r["parent_pa"],
                },
                "geometry": {"type": "Polygon", "coordinates": [ring]},
            })
        with open(ROOT / "hex" / f"hex{res}_universe.geojson", "w") as f:
            json.dump(gj, f)

    print(f"After: hex9={len(h9_set):,}  hex8={len(h8_set):,}  ov9={len(df_ov9):,}  ov8={len(df_ov8):,}  ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()
