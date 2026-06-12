"""
Plexis SGP v4 — Stage 2: building features per hex-9.

Sources (all on atlas-1):
  data/buildings_overture/sgp_buildings_fused.parquet  (377,331 buildings,
       class fused from Overture + OSM, with cx/cy centroids, area_deg, is_hdb,
       best_floors, best_height)
  data/housing/hdb_existing_buildings.geojson           (13,386 HDB blocks
       authoritative — used to override and to merge in max_floor_lvl from
       hdb_property_info.csv)
  data/housing/hdb_property_info.csv                    (13,267 blocks ×
       max_floor_lvl, year_completed, total_dwelling_units)

Method:
  1. Buildings → hex-9 via centroid lat/lng (H3 latlng_to_cell).
  2. HDB authoritative override: every HDB block polygon centroid → hex-9.
     Floor count from hdb_property_info.max_floor_lvl when available, else
     from the fused.best_floors fallback.
  3. Per-hex aggregations: count, total area, area by class (residential/
     commercial/industrial/institutional), avg/max floors, height stats,
     HDB block count + dwelling units, derived metrics.

Output:
  hex/hex9_buildings.parquet  (7,318 × ~22 cols)
  hex/buildings_report.json
"""
import json, os, time
from pathlib import Path
import pandas as pd
import geopandas as gpd
import numpy as np
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
FUSED = DATA / "buildings_overture/sgp_buildings_fused.parquet"
HDB_GEO = DATA / "housing/hdb_existing_buildings.geojson"
HDB_INFO = DATA / "housing/hdb_property_info.csv"
HEX9 = ROOT / "hex/hex9_universe.parquet"

OUT_PQ = ROOT / "hex/hex9_buildings.parquet"
REPORT = ROOT / "hex/buildings_report.json"

# fused_class -> Plexis bucket
CLASS_TO_BUCKET = {
    "private_residential": "residential",
    "hdb_residential":     "residential",
    "commercial":          "commercial",
    "industrial":          "industrial",
    "institutional":       "institutional",
    "transport":           "transport",
    "religious":           "religious",
    "other":               "other",
    "unclassified":        "unclassified",
}


def main():
    t0 = time.time()
    print("Loading...")
    fused = pd.read_parquet(FUSED)
    print(f"  fused buildings: {len(fused):,}")
    h9 = pd.read_parquet(HEX9)
    print(f"  hex-9 cells: {len(h9):,}")

    # Compute hex-9 ID per building from centroid (cy=lat, cx=lng)
    print("  Hashing building centroids → hex9_id...")
    fused["hex9_id"] = [h3.latlng_to_cell(lat, lng, 9)
                        for lat, lng in zip(fused["cy"].values, fused["cx"].values)]

    # Estimate area in m² from area_deg using local equal-area conversion
    # Singapore: 1° lat ≈ 110,574 m, 1° lng @ 1.35°N ≈ 111,316 × cos(1.35°) ≈ 111,288 m
    # So 1 deg² ≈ 1.231e10 m². Use this constant for all of SGP (rounding ok at ±0.1%).
    DEG2_TO_M2 = 1.231e10
    fused["area_m2"] = fused["area_deg"] * DEG2_TO_M2

    # Bucket
    fused["bucket"] = fused["fused_class"].map(CLASS_TO_BUCKET).fillna("other")

    # === Aggregate per hex-9 ===
    print("  Aggregating per hex...")
    agg = fused.groupby("hex9_id").agg(
        bldg_count=("id", "count"),
        bldg_total_area_m2=("area_m2", "sum"),
        avg_floors=("best_floors", "mean"),
        max_floors=("best_floors", "max"),
        avg_height=("best_height", "mean"),
        max_height=("best_height", "max"),
    ).reset_index()

    # Counts per bucket
    bucket_counts = fused.pivot_table(
        index="hex9_id", columns="bucket", values="id", aggfunc="count", fill_value=0
    )
    bucket_counts.columns = [f"bldg_{c}_count" for c in bucket_counts.columns]
    bucket_counts = bucket_counts.reset_index()

    # Area per bucket
    bucket_areas = fused.pivot_table(
        index="hex9_id", columns="bucket", values="area_m2", aggfunc="sum", fill_value=0
    )
    bucket_areas.columns = [f"bldg_{c}_area_m2" for c in bucket_areas.columns]
    bucket_areas = bucket_areas.reset_index()

    # === HDB authoritative override ===
    print("  Loading authoritative HDB blocks...")
    hdb_geo = gpd.read_file(HDB_GEO).to_crs(4326)
    hdb_info = pd.read_csv(HDB_INFO)

    # Centroid → hex-9 (use proper projected centroid)
    hdb_3414 = hdb_geo.to_crs(3414)
    hdb_3414["centroid_3414"] = hdb_3414.geometry.centroid
    cent_4326 = gpd.GeoSeries(hdb_3414["centroid_3414"], crs=3414).to_crs(4326)
    hdb_geo["hex9_id"] = [h3.latlng_to_cell(p.y, p.x, 9) for p in cent_4326]
    hdb_geo["BLK_NO_N"] = hdb_geo["BLK_NO"].astype(str).str.upper().str.strip()
    hdb_info["blk_no_n"] = hdb_info["blk_no"].astype(str).str.upper().str.strip()
    info_floors = hdb_info.groupby("blk_no_n")["max_floor_lvl"].max().to_dict()
    info_units = hdb_info.groupby("blk_no_n")["total_dwelling_units"].sum().to_dict()
    info_year = hdb_info.groupby("blk_no_n")["year_completed"].min().to_dict()
    geo_counts = hdb_geo["BLK_NO_N"].value_counts().to_dict()

    def _floors(b): return info_floors.get(b, np.nan)
    def _units(b):
        n = geo_counts.get(b, 1)
        return info_units.get(b, 0) / max(n, 1)
    def _year(b): return info_year.get(b, np.nan)

    hdb_geo["hdb_floors"] = hdb_geo["BLK_NO_N"].map(_floors)
    hdb_geo["hdb_units"] = hdb_geo["BLK_NO_N"].apply(_units)
    hdb_geo["hdb_year"] = hdb_geo["BLK_NO_N"].map(_year)

    hdb_agg = hdb_geo.groupby("hex9_id").agg(
        hdb_block_count=("OBJECTID", "count"),
        hdb_dwelling_units=("hdb_units", "sum"),
        hdb_max_floors=("hdb_floors", "max"),
        hdb_avg_floors=("hdb_floors", "mean"),
        hdb_min_year=("hdb_year", "min"),
        hdb_avg_year=("hdb_year", "mean"),
    ).reset_index()
    print(f"  HDB blocks linked to {hdb_agg['hdb_block_count'].sum():,} blocks across {len(hdb_agg):,} hexes")

    # === Build final table ===
    out = h9[["hex9_id", "lat", "lng"]].copy()
    out = out.merge(agg, on="hex9_id", how="left")
    out = out.merge(bucket_counts, on="hex9_id", how="left")
    out = out.merge(bucket_areas, on="hex9_id", how="left")
    out = out.merge(hdb_agg, on="hex9_id", how="left")

    # Fill numeric NaNs with 0 for counts/areas; leave floors/heights as NaN
    fill_zero = [c for c in out.columns if c.endswith("_count") or c.endswith("_m2") or c == "hdb_dwelling_units"]
    for c in fill_zero:
        out[c] = out[c].fillna(0)

    # Override HDB residential floors with authoritative HDB max_floor_lvl where available
    # (HDB blocks have authoritative floor counts; the fused stack often misses them)
    out["best_max_floors"] = out[["max_floors", "hdb_max_floors"]].max(axis=1)
    out["best_avg_floors"] = out[["avg_floors", "hdb_avg_floors"]].max(axis=1)

    # Derived metrics
    HEX_AREA_M2 = 105_000  # ~0.105 km² per hex-9
    out["bldg_density_per_km2"] = out["bldg_count"] * (1e6 / HEX_AREA_M2)
    out["bldg_footprint_share"] = out["bldg_total_area_m2"] / HEX_AREA_M2  # fraction of hex covered
    out["bldg_residential_share"] = np.where(
        out["bldg_total_area_m2"] > 0,
        out["bldg_residential_area_m2"] / out["bldg_total_area_m2"], 0,
    )
    out["bldg_commercial_share"] = np.where(
        out["bldg_total_area_m2"] > 0,
        out["bldg_commercial_area_m2"] / out["bldg_total_area_m2"], 0,
    )
    out["bldg_industrial_share"] = np.where(
        out["bldg_total_area_m2"] > 0,
        out["bldg_industrial_area_m2"] / out["bldg_total_area_m2"], 0,
    )
    # is_highrise = max floors >= 10
    out["is_highrise"] = (out["best_max_floors"] >= 10).fillna(False)

    out.to_parquet(OUT_PQ, index=False)

    # Summary
    bldg_total = out["bldg_count"].sum()
    res_total = out["bldg_residential_count"].sum() if "bldg_residential_count" in out else 0
    hdb_total = out["hdb_block_count"].sum()
    print(f"\n=== Summary ===")
    print(f"  Total buildings allocated: {int(bldg_total):,} (expected 377,331)")
    print(f"  Residential buildings:     {int(res_total):,}")
    print(f"  HDB blocks:                {int(hdb_total):,} (expected 13,386)")
    print(f"  Hexes with buildings:      {(out['bldg_count'] > 0).sum():,} / {len(out):,}")
    print(f"  Hexes with HDB:            {(out['hdb_block_count'] > 0).sum():,}")
    print(f"  Highrise hexes:            {(out['is_highrise']).sum():,}")
    print(f"  Max max_floors:            {int(out['best_max_floors'].max())} floors")

    # Top hexes by building count
    top = out.nlargest(10, "bldg_count").merge(
        h9[["hex9_id", "parent_subzone_name", "parent_pa"]], on="hex9_id"
    )
    print(f"\n=== Top 10 hexes by building count ===")
    for _, r in top.iterrows():
        print(f"  {r['hex9_id']:<18} bldg={int(r['bldg_count']):>4}  hdb={int(r['hdb_block_count']):>3}  max_fl={int(r['best_max_floors']) if pd.notna(r['best_max_floors']) else '?':>3}  {str(r['parent_subzone_name']):<25} ({r['parent_pa']})")

    # Top hexes by max floors
    top_floors = out[out["best_max_floors"].notna()].nlargest(10, "best_max_floors").merge(
        h9[["hex9_id", "parent_subzone_name", "parent_pa"]], on="hex9_id"
    )
    print(f"\n=== Top 10 hexes by max floors ===")
    for _, r in top_floors.iterrows():
        print(f"  {r['hex9_id']:<18} max_fl={int(r['best_max_floors']):>3}  bldg={int(r['bldg_count']):>4}  {str(r['parent_subzone_name']):<25} ({r['parent_pa']})")

    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "buildings_input_total": int(len(fused)),
        "buildings_allocated_to_hexes": int(bldg_total),
        "hdb_blocks_input": int(len(hdb_geo)),
        "hdb_blocks_allocated": int(hdb_total),
        "hexes_with_buildings": int((out["bldg_count"] > 0).sum()),
        "hexes_with_hdb": int((out["hdb_block_count"] > 0).sum()),
        "hexes_highrise": int((out["is_highrise"]).sum()),
        "max_floors_observed": int(out["best_max_floors"].max() if out["best_max_floors"].notna().any() else 0),
        "wall_clock_s": round(time.time() - t0, 2),
    }
    with open(REPORT, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport: {REPORT}")
    print(f"Output: {OUT_PQ}")


if __name__ == "__main__":
    main()
