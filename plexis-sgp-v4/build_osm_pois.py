"""
Plexis SGP v4 — Stage 19: OSM POI counts per scale.

Counts of OSM POIs by category per hex/subzone (recovers v3 `osm_*` family).

Sources (data/osm_pois/):
  amenities.geojson    ~28K  (restaurant, cafe, bench, ATM, school, ...)
  leisure.geojson      ~6K   (park, playground, fitness_centre, sports_centre, ...)
  shops.geojson        ~10K  (supermarket, clothes, convenience, ...)
  tourism.geojson      ~2K   (hotel, attraction, museum, viewpoint, ...)

Per-hex columns (4):
  osm_amenities_count, osm_leisure_count, osm_shops_count, osm_tourism_count

Outputs:
  hex/hex9_osm_pois.parquet
  hex/hex8_osm_pois.parquet
  hex/subzone_osm_pois.parquet
"""
import json, os, time
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import h3

ROOT = Path(__file__).parent


def _resolve_data_root():
    if os.environ.get("PLEXIS_DATA_ROOT"):
        return Path(os.environ["PLEXIS_DATA_ROOT"])
    for c in [Path("/home/azureuser/digital-atlas-sgp/data"), ROOT.parent / "data"]:
        if c.exists(): return c
    raise FileNotFoundError("data root not found")


DATA = _resolve_data_root()
SOURCES = {
    "amenities": DATA / "osm_pois/amenities.geojson",
    "leisure":   DATA / "osm_pois/leisure.geojson",
    "shops":     DATA / "osm_pois/shops.geojson",
    "tourism":   DATA / "osm_pois/tourism.geojson",
}


def hex_count_layer(g, key="hex9_id"):
    pts = g.to_crs(4326)
    # Convert any polygon geometries to centroids
    centroids = pts.geometry.centroid
    valid = centroids.is_valid & ~centroids.is_empty
    centroids = centroids[valid]
    hex_ids = [h3.latlng_to_cell(p.y, p.x, 9) for p in centroids]
    return pd.Series(hex_ids).value_counts().rename_axis("hex9_id").reset_index(name="cnt")


def main():
    t0 = time.time()
    h9 = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")[["hex9_id","parent_hex8","parent_subzone"]]
    out_h9 = h9[["hex9_id"]].copy()

    for tag, path in SOURCES.items():
        print(f"  loading {tag}...")
        try:
            g = gpd.read_file(path)
        except Exception as e:
            print(f"    skipped: {e}")
            continue
        cnt = hex_count_layer(g)
        cnt.columns = ["hex9_id", f"osm_{tag}_count"]
        out_h9 = out_h9.merge(cnt, on="hex9_id", how="left")
        print(f"    {len(g):,} POIs → {len(cnt):,} hexes touched")

    for c in out_h9.columns:
        if c.startswith("osm_"):
            out_h9[c] = out_h9[c].fillna(0).astype(int)

    out_h9.to_parquet(ROOT / "hex/hex9_osm_pois.parquet", index=False)
    print(f"\n  hex9_osm_pois: {out_h9.shape}")

    # Aggregate to hex8 + subzone (sum)
    sum_cols = [c for c in out_h9.columns if c.startswith("osm_")]
    h9wp = out_h9.merge(h9, on="hex9_id")

    h8_uni = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")[["hex8_id"]]
    h8_agg = h9wp.groupby("parent_hex8")[sum_cols].sum().reset_index().rename(columns={"parent_hex8":"hex8_id"})
    out_h8 = h8_uni.merge(h8_agg, on="hex8_id", how="left")
    for c in sum_cols: out_h8[c] = out_h8[c].fillna(0).astype(int)
    out_h8.to_parquet(ROOT / "hex/hex8_osm_pois.parquet", index=False)
    print(f"  hex8_osm_pois: {out_h8.shape}")

    sz_lu = pd.read_parquet(ROOT / "hex/subzone_land_use.parquet")[["subzone_c"]].drop_duplicates()
    sz_agg = h9wp.groupby("parent_subzone")[sum_cols].sum().reset_index().rename(columns={"parent_subzone":"subzone_c"})
    out_sz = sz_lu.merge(sz_agg, on="subzone_c", how="left")
    for c in sum_cols: out_sz[c] = out_sz[c].fillna(0).astype(int)
    out_sz.to_parquet(ROOT / "hex/subzone_osm_pois.parquet", index=False)
    print(f"  subzone_osm_pois: {out_sz.shape}")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "shapes": {"hex9": list(out_h9.shape), "hex8": list(out_h8.shape), "subzone": list(out_sz.shape)},
    }
    with open(ROOT / "hex/osm_pois_report.json", "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
