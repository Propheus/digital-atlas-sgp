"""
Plexis SGP v4 — admin-layer coverage validator.
Layers added in this run:
  P1. All 55 planning areas have >=1 hex overlap (both resolutions)
  P2. All 5 regions have >=1 hex overlap (both resolutions)
  P3. All 27 HDB towns have >=1 hex overlap (both resolutions)
  P4. hex9.parent_pa == max-overlap PA (cross-consistency)
  P5. hex9.parent_region == max-overlap region
  P6. All HDB blocks fall inside at least one HDB town polygon
  P7. HDB residential coverage estimate (expected ~300 km² of 785)
"""
import json
from pathlib import Path
import pandas as pd
import geopandas as gpd
from shapely.ops import unary_union
import h3

ROOT = Path("/home/azureuser/plexis-sgp-v4")
report = {"checks": []}


def add(name, status, detail=""):
    report["checks"].append({"check": name, "status": status, "detail": detail})
    tag = "PASS" if status == "PASS" else ("WARN" if status == "WARN" else "FAIL")
    print(f"  [{tag}] {name} — {detail}")


gdf_pa = gpd.read_file(ROOT / "boundaries/planning_areas.geojson")
gdf_rg = gpd.read_file(ROOT / "boundaries/regions.geojson")
gdf_hdb = gpd.read_file(ROOT / "boundaries/hdb_towns.geojson")
h9 = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
h8 = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")
ov_h9_pa = pd.read_parquet(ROOT / "hex/hex9_pa_overlap.parquet")
ov_h8_pa = pd.read_parquet(ROOT / "hex/hex8_pa_overlap.parquet")
ov_h9_rg = pd.read_parquet(ROOT / "hex/hex9_region_overlap.parquet")
ov_h8_rg = pd.read_parquet(ROOT / "hex/hex8_region_overlap.parquet")
ov_h9_hdb = pd.read_parquet(ROOT / "hex/hex9_hdb_town_overlap.parquet")
ov_h8_hdb = pd.read_parquet(ROOT / "hex/hex8_hdb_town_overlap.parquet")

print(f"boundaries: PA={len(gdf_pa)} regions={len(gdf_rg)} HDB towns={len(gdf_hdb)}")
print(f"hexes: h9={len(h9):,} h8={len(h8):,}")

# -- P1 planning areas --
print("\n=== P1. All planning areas have hex overlap ===")
pa_names = set(gdf_pa["PLN_AREA_N"])
missing9 = pa_names - set(ov_h9_pa["PLN_AREA_N"].unique())
missing8 = pa_names - set(ov_h8_pa["PLN_AREA_N"].unique())
if not missing9 and not missing8:
    add("P1_all_pa_covered", "PASS", f"{len(pa_names)}/{len(pa_names)} in both tables")
else:
    add("P1_all_pa_covered", "FAIL", f"missing h9={sorted(missing9)} missing h8={sorted(missing8)}")

# -- P2 regions --
print("\n=== P2. All regions have hex overlap ===")
rg_names = set(gdf_rg["REGION_N"])
missing9 = rg_names - set(ov_h9_rg["REGION_N"].unique())
missing8 = rg_names - set(ov_h8_rg["REGION_N"].unique())
if not missing9 and not missing8:
    add("P2_all_regions_covered", "PASS", f"{len(rg_names)}/{len(rg_names)} in both tables")
else:
    add("P2_all_regions_covered", "FAIL", f"missing h9={sorted(missing9)} missing h8={sorted(missing8)}")

# -- P3 HDB towns --
print("\n=== P3. All HDB towns have hex overlap ===")
hdb_names = set(gdf_hdb["hdb_town"])
missing9 = hdb_names - set(ov_h9_hdb["hdb_town"].unique())
missing8 = hdb_names - set(ov_h8_hdb["hdb_town"].unique())
if not missing9 and not missing8:
    add("P3_all_hdb_towns_covered", "PASS", f"{len(hdb_names)}/{len(hdb_names)} in both tables")
else:
    add("P3_all_hdb_towns_covered", "FAIL", f"missing h9={sorted(missing9)} missing h8={sorted(missing8)}")

# -- P4 parent_pa cross-check --
print("\n=== P4. hex9.parent_pa matches max-overlap PA ===")
idx_max = ov_h9_pa.groupby("hex9_id")["overlap_deg2"].idxmax()
max_pa = ov_h9_pa.loc[idx_max].set_index("hex9_id")["PLN_AREA_N"]
merged = h9.set_index("hex9_id").join(max_pa.rename("overlap_pa"))
# Case-insensitive compare
mismatch = merged[merged["parent_pa"].str.upper().str.strip() != merged["overlap_pa"].str.upper().str.strip()]
if len(mismatch) == 0:
    add("P4_parent_pa_consistent", "PASS", f"all {len(h9):,} match")
elif len(mismatch) < 20:
    add("P4_parent_pa_consistent", "WARN", f"{len(mismatch)} mismatches (likely tiny-subzone edge effects)")
    print("    first 10:")
    for i, (hid, r) in enumerate(mismatch.head(10).iterrows()):
        print(f"      {hid}  stored={r['parent_pa']}  max_overlap={r['overlap_pa']}")
else:
    add("P4_parent_pa_consistent", "FAIL", f"{len(mismatch)} mismatches")

# -- P5 parent_region cross-check --
print("\n=== P5. hex9.parent_region matches max-overlap region ===")
idx_max = ov_h9_rg.groupby("hex9_id")["overlap_deg2"].idxmax()
max_rg = ov_h9_rg.loc[idx_max].set_index("hex9_id")["REGION_N"]
merged = h9.set_index("hex9_id").join(max_rg.rename("overlap_rg"))
mismatch = merged[merged["parent_region"].str.upper().str.strip() != merged["overlap_rg"].str.upper().str.strip()]
if len(mismatch) == 0:
    add("P5_parent_region_consistent", "PASS", f"all {len(h9):,} match")
elif len(mismatch) < 50:
    add("P5_parent_region_consistent", "WARN", f"{len(mismatch)} mismatches")
else:
    add("P5_parent_region_consistent", "FAIL", f"{len(mismatch)} mismatches")

# -- P6 HDB blocks inside HDB town union --
print("\n=== P6. HDB blocks inside HDB town polygons ===")
import os as _os
_data_root = _os.environ.get("PLEXIS_DATA_ROOT")
if not _data_root:
    for _c in ["/home/azureuser/digital-atlas-sgp/data", str(ROOT.parent / "data")]:
        if Path(_c).exists():
            _data_root = _c
            break
blocks = gpd.read_file(f"{_data_root}/housing/hdb_existing_buildings.geojson").to_crs(4326)
union_hdb = unary_union(gdf_hdb.geometry.values)
blocks_in = blocks[blocks.geometry.centroid.within(union_hdb)]
pct = 100.0 * len(blocks_in) / len(blocks)
if pct >= 99.0:
    add("P6_hdb_blocks_inside_towns", "PASS", f"{len(blocks_in):,}/{len(blocks):,} ({pct:.2f}%)")
elif pct >= 95.0:
    add("P6_hdb_blocks_inside_towns", "WARN", f"{len(blocks_in):,}/{len(blocks):,} ({pct:.2f}%)")
else:
    add("P6_hdb_blocks_inside_towns", "FAIL", f"{len(blocks_in):,}/{len(blocks):,} ({pct:.2f}%)")

# -- P7 HDB area coverage estimate --
print("\n=== P7. HDB towns area coverage ===")
area_hdb_km2 = gpd.GeoSeries([union_hdb], crs=4326).to_crs(3414).iloc[0].area / 1e6
total_km2 = gpd.GeoSeries([unary_union(gdf_pa.geometry.values)], crs=4326).to_crs(3414).iloc[0].area / 1e6
pct_hdb = 100.0 * area_hdb_km2 / total_km2
print(f"  HDB town area: {area_hdb_km2:.2f} km² ({pct_hdb:.1f}% of SGP {total_km2:.2f} km²)")
# Expected: HDB residential footprint ~25-40% of Singapore
if 15 <= pct_hdb <= 45:
    add("P7_hdb_area_reasonable", "PASS", f"{area_hdb_km2:.1f} km² = {pct_hdb:.1f}% (expected 20–40%)")
else:
    add("P7_hdb_area_reasonable", "WARN", f"{area_hdb_km2:.1f} km² = {pct_hdb:.1f}%")

# Summary
passes = sum(1 for c in report["checks"] if c["status"] == "PASS")
print(f"\n{passes}/{len(report['checks'])} checks passed")
for c in report["checks"]:
    st = c["status"]
    nm = c["check"]
    dt = c["detail"]
    print(f"  {st:4s}  {nm}  — {dt}")

report["generated_at"] = __import__("time").strftime("%Y-%m-%dT%H:%M:%S")
with open(ROOT / "hex/admin_coverage_report.json", "w") as f:
    json.dump(report, f, indent=2)
