"""
Hex v10 — amenities and transit points per hex, computed from source geojsons.

Each source file contains points (or small polygons whose centroids we use).
We compute the H3-9 cell from centroid and count per hex.

Sources:
    data/transit_updated/train_stations_mar2026.geojson   (231 MRT/LRT)
    data/transit_updated/bus_stops_mar2026.geojson        (5,177 bus stops)
    data/amenities/hawker_centres.geojson                 (129)
    data/amenities/chas_clinics.geojson                   (1,193)
    data/amenities/preschools.geojson                     (2,290)
    data/amenities/hotels.geojson                         (468)
    data/amenities/tourist_attractions.geojson            (109)
    data/amenities/eating_establishments_sfa.geojson      (34,378)
    data/amenities/silver_zones.geojson                   (42)
    data/amenities/school_zones.geojson                   (211)
    data/amenities/park_facilities.geojson                (parks)

Output:
    data/hex_v10/hex_amenities.parquet

Schema:
    hex_id
    mrt_stations, lrt_stations
    bus_stops
    hawker_centres
    chas_clinics
    preschools_gov
    hotels
    tourist_attractions
    sfa_eating_establishments
    silver_zones
    school_zones
    park_facilities
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import geopandas as gpd
import h3
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
UNI = ROOT / "data" / "hex_v10" / "hex_universe.parquet"
OUT = ROOT / "data" / "hex_v10" / "hex_amenities.parquet"


def count_points_per_hex(
    path: Path,
    col_name: str,
    filter_fn: Optional[callable] = None,
) -> tuple[str, pd.Series]:
    """Read a geojson, take each feature's representative point, count per H3-9 cell.

    Returns (col_name, counts_series) — col_name is explicit because pandas
    `value_counts()` drops the Series name.
    """
    g = gpd.read_file(path).to_crs(4326)
    if filter_fn is not None:
        g = g[filter_fn(g)]
    pts = g.geometry.representative_point()
    lngs = pts.x.to_numpy()
    lats = pts.y.to_numpy()
    hex_ids = [h3.latlng_to_cell(y, x, 9) for x, y in zip(lngs, lats)]
    counts = pd.Series(hex_ids).value_counts()
    return col_name, counts


def add(out: dict[str, dict], col: str, counts: pd.Series) -> None:
    for hid, cnt in counts.items():
        out.setdefault(hid, {}).setdefault(col, 0)
        out[hid][col] += int(cnt)


def main() -> None:
    uni = pd.read_parquet(UNI, columns=["hex_id"])
    uni_set = set(uni["hex_id"])

    counts_store: dict[str, dict[str, int]] = {}

    # --- Transit ---
    trains_path = ROOT / "data" / "transit_updated" / "train_stations_mar2026.geojson"
    print(f"  {trains_path}")
    g = gpd.read_file(trains_path).to_crs(4326)
    # Split MRT vs LRT using a best-effort field heuristic
    type_col = None
    for c in ["TYPE", "type", "line_type", "station_type", "category"]:
        if c in g.columns:
            type_col = c
            break
    if type_col is not None:
        print(f"    detected type col: {type_col}")
    pts = g.geometry.representative_point()
    for i, (x, y) in enumerate(zip(pts.x, pts.y)):
        hid = h3.latlng_to_cell(y, x, 9)
        is_lrt = False
        if type_col is not None:
            v = str(g.iloc[i][type_col]).upper()
            is_lrt = "LRT" in v
        key = "lrt_stations" if is_lrt else "mrt_stations"
        counts_store.setdefault(hid, {}).setdefault(key, 0)
        counts_store[hid][key] += 1

    # --- Bus stops ---
    bus_path = ROOT / "data" / "transit_updated" / "bus_stops_mar2026.geojson"
    print(f"  {bus_path}")
    col, s = count_points_per_hex(bus_path, "bus_stops")
    add(counts_store, col, s)

    # --- Amenities ---
    amenity_sources = [
        (ROOT / "data" / "amenities" / "hawker_centres.geojson", "hawker_centres"),
        (ROOT / "data" / "amenities" / "chas_clinics.geojson", "chas_clinics"),
        (ROOT / "data" / "amenities" / "preschools.geojson", "preschools_gov"),
        (ROOT / "data" / "amenities" / "hotels.geojson", "hotels"),
        (ROOT / "data" / "amenities" / "tourist_attractions.geojson", "tourist_attractions"),
        (ROOT / "data" / "amenities" / "eating_establishments_sfa.geojson", "sfa_eating_establishments"),
        (ROOT / "data" / "amenities" / "silver_zones.geojson", "silver_zones"),
        (ROOT / "data" / "amenities" / "school_zones.geojson", "school_zones"),
        (ROOT / "data" / "amenities" / "park_facilities.geojson", "park_facilities"),
    ]
    for path, col in amenity_sources:
        if not path.exists():
            print(f"  MISS {path}")
            continue
        print(f"  {path}")
        col_name, s = count_points_per_hex(path, col)
        add(counts_store, col_name, s)

    # Build output frame keyed on the full hex universe
    cols = [
        "mrt_stations", "lrt_stations", "bus_stops",
        "hawker_centres", "chas_clinics", "preschools_gov",
        "hotels", "tourist_attractions", "sfa_eating_establishments",
        "silver_zones", "school_zones", "park_facilities",
    ]
    rows = []
    for hid in uni["hex_id"]:
        row = {"hex_id": hid}
        vals = counts_store.get(hid, {})
        for c in cols:
            row[c] = int(vals.get(c, 0))
        rows.append(row)
    out = pd.DataFrame(rows)

    print(f"Output shape: {out.shape}")
    # How many amenity hits were outside the hex universe?
    all_hids = set(counts_store.keys())
    outside = all_hids - uni_set
    print(f"  amenity hits outside v10 universe: {sum(sum(counts_store[h].values()) for h in outside):,}")

    print()
    print("Per-column totals:")
    print(out[cols].sum().to_string())

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT, index=False)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
