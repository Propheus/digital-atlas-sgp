"""
Hex v10 — universe build.

Polyfill every subzone polygon in data/boundaries/subzones.geojson with H3 res 9.
Deduplicate at shared subzone boundaries by assigning each hex to the subzone whose
polygon *contains* the hex center (unique by construction since polygons tile).

Output:
    data/hex_v10/hex_universe.parquet

Columns:
    hex_id               (str, H3-9)
    lat, lng             (hex center)
    area_km2             (constant for H3-9, ~0.105 km²)
    parent_subzone       (subzone code, e.g. DTSZ05)
    parent_subzone_name  (human name)
    parent_pa            (planning area name)
    parent_region        (region name)
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import h3
import numpy as np
import pandas as pd
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parents[3]
IN_PATH = ROOT / "data" / "boundaries" / "subzones.geojson"
OUT_DIR = ROOT / "data" / "hex_v10"
OUT_PATH = OUT_DIR / "hex_universe.parquet"

H3_RES = 9


def polygon_cells_overlap(polygon) -> set[str]:
    """Return the set of H3-9 cells whose area partially overlaps the given polygon.

    Uses h3.h3shape_to_cells_experimental(contain='overlap'). This catches hexes
    that strict 'center' polyfill would miss along irregular admin boundaries
    (which matters around reclamation land, island boundaries, and coastlines).
    """
    if polygon.is_empty:
        return set()
    outer = [(y, x) for x, y in polygon.exterior.coords]
    holes = []
    for interior in polygon.interiors:
        holes.append([(y, x) for x, y in interior.coords])
    h3poly = h3.LatLngPoly(outer, *holes) if holes else h3.LatLngPoly(outer)
    return set(h3.h3shape_to_cells_experimental(h3poly, H3_RES, contain="overlap"))


def polygon_cells_center(polygon) -> set[str]:
    """Strict containment: cell center must fall inside the polygon. Used for tiebreaks."""
    if polygon.is_empty:
        return set()
    outer = [(y, x) for x, y in polygon.exterior.coords]
    holes = []
    for interior in polygon.interiors:
        holes.append([(y, x) for x, y in interior.coords])
    h3poly = h3.LatLngPoly(outer, *holes) if holes else h3.LatLngPoly(outer)
    return set(h3.polygon_to_cells(h3poly, H3_RES))


def main() -> None:
    print(f"Loading subzones: {IN_PATH}")
    g = gpd.read_file(IN_PATH).to_crs(4326)
    # Rename for convenience
    g = g.rename(
        columns={
            "SUBZONE_C": "parent_subzone",
            "SUBZONE_N": "parent_subzone_name",
            "PLN_AREA_N": "parent_pa",
            "REGION_N": "parent_region",
        }
    )
    print(f"  {len(g)} subzones, CRS={g.crs}")

    # Two-pass assignment.
    # Pass 1: strict center-containment — a hex whose center is inside subzone S
    # unambiguously belongs to S (for well-formed admin tilings there are no conflicts here).
    # Pass 2: overlap mode — pick up hexes whose center falls outside every subzone polygon
    # (irregular boundaries, reclamation, island complexes) but whose area partially
    # overlaps a subzone. These hexes are assigned to the *first* subzone that claims
    # them in overlap order. Since Pass 1 ran first, Pass 2 can only fill previously-empty
    # cells, so there are no tie conflicts for hexes with a strict containing subzone.
    assignments: dict[str, tuple[str, str, str, str]] = {}  # hex_id -> (subz_code, name, pa, region)
    n_center_total = 0
    n_overlap_added = 0

    for pass_name in ("center", "overlap"):
        for _, row in g.iterrows():
            geom = row.geometry
            if geom is None or geom.is_empty:
                continue
            parts = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]
            for part in parts:
                cells = polygon_cells_center(part) if pass_name == "center" else polygon_cells_overlap(part)
                for cell in cells:
                    if cell in assignments:
                        continue  # already claimed by an earlier pass or earlier subzone
                    assignments[cell] = (
                        row["parent_subzone"],
                        row["parent_subzone_name"],
                        row["parent_pa"],
                        row["parent_region"],
                    )
                    if pass_name == "center":
                        n_center_total += 1
                    else:
                        n_overlap_added += 1

    print(f"  pass 1 (center containment) hexes: {n_center_total:,}")
    print(f"  pass 2 (overlap, boundary fill) hexes: {n_overlap_added:,}")
    print(f"  total hexes: {len(assignments):,}")

    # Coverage sanity vs previous V9 universe
    v9 = pd.read_parquet(ROOT / "data" / "hex_v9" / "hex_features_v2.parquet", columns=["hex_id"])
    v9_set = set(v9["hex_id"].tolist())
    v10_set = set(assignments.keys())
    kept = v9_set & v10_set
    lost = v9_set - v10_set
    added = v10_set - v9_set
    print(f"  V9 hexes: {len(v9_set):,}")
    print(f"  v10 hexes: {len(v10_set):,}")
    print(f"  carried from V9: {len(kept):,}")
    print(f"  dropped (not in v10 polyfill): {len(lost):,}")
    print(f"  new in v10: {len(added):,}")

    # Build output frame
    rows = []
    area = h3.average_hexagon_area(H3_RES, unit="km^2")
    for hex_id, (sc, sn, pa, region) in assignments.items():
        lat, lng = h3.cell_to_latlng(hex_id)
        rows.append(
            {
                "hex_id": hex_id,
                "lat": lat,
                "lng": lng,
                "area_km2": area,
                "parent_subzone": sc,
                "parent_subzone_name": sn,
                "parent_pa": pa,
                "parent_region": region,
            }
        )
    out = pd.DataFrame(rows).sort_values("hex_id").reset_index(drop=True)
    print(f"Output shape: {out.shape}")

    # Per-subzone hex count — should now cover all 332 subzones
    per_subz = out["parent_subzone"].value_counts()
    print(f"Subzones with ≥1 hex: {per_subz.shape[0]}/332")

    # Check: are the 11 V9-missing subzones now represented?
    missing_before = {"BDSZ07", "BMSZ01", "SISZ01", "RCSZ06", "DTSZ04", "DTSZ07", "JESZ10", "NESZ01", "RCSZ04", "RCSZ08", "SISZ02"}
    now_present = missing_before & set(out["parent_subzone"])
    print(f"Previously missing subzones now present: {len(now_present)}/{len(missing_before)}")
    for sz in sorted(missing_before):
        n = per_subz.get(sz, 0)
        print(f"  {sz}: {n} hexes")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT_PATH, index=False)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
