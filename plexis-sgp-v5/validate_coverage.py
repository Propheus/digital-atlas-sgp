"""
Plexis SGP v4 — strict coverage validator.

Six layers:
  L1. every subzone has >=1 overlap row in hex9_subzone_overlap
  L2. every subzone has >=1 overlap row in hex8_subzone_overlap
  L3. no duplicate hex_ids
  L4. every hex-9's parent_hex8 is inside hex-8 universe (closure)
  L5. areal coverage: union(hex9 polygons) fully contains union(subzones)
  L6. per-subzone coverage 100.0000% (strict, tolerance 0.001 km²)
"""
import json
from pathlib import Path
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from shapely.ops import unary_union
import h3

ROOT = Path("/home/azureuser/plexis-sgp-v4")
report = {"checks": []}


def add(name, status, detail=""):
    report["checks"].append({"check": name, "status": status, "detail": detail})
    tag = "PASS" if status == "PASS" else ("WARN" if status == "WARN" else "FAIL")
    print(f"  [{tag}] {name} — {detail}")


print("Loading...")
gdf_sz = gpd.read_file(ROOT / "boundaries" / "subzones.geojson").to_crs(4326)
h9 = pd.read_parquet(ROOT / "hex" / "hex9_universe.parquet")
h8 = pd.read_parquet(ROOT / "hex" / "hex8_universe.parquet")
ov9 = pd.read_parquet(ROOT / "hex" / "hex9_subzone_overlap.parquet")
ov8 = pd.read_parquet(ROOT / "hex" / "hex8_subzone_overlap.parquet")
print(f"  subzones={len(gdf_sz)}  hex8={len(h8)}  hex9={len(h9)}  ov9={len(ov9):,}  ov8={len(ov8):,}")

print("\n=== L1. Every subzone has >=1 hex-9 overlap ===")
sz_codes = set(gdf_sz["SUBZONE_C"])
sz_in_ov9 = set(ov9["subzone_c"].unique())
missing9 = sz_codes - sz_in_ov9
if not missing9:
    add("L1_subzones_in_hex9_overlap", "PASS", f"{len(sz_codes)}/{len(sz_codes)} subzones represented")
else:
    add("L1_subzones_in_hex9_overlap", "FAIL", f"missing: {sorted(missing9)}")

print("\n=== L2. Every subzone has >=1 hex-8 overlap ===")
sz_in_ov8 = set(ov8["subzone_c"].unique())
missing8 = sz_codes - sz_in_ov8
if not missing8:
    add("L2_subzones_in_hex8_overlap", "PASS", f"{len(sz_codes)}/{len(sz_codes)} subzones represented")
else:
    add("L2_subzones_in_hex8_overlap", "FAIL", f"missing: {sorted(missing8)}")

print("\n=== L3. No duplicate hex_ids ===")
dup9 = h9["hex9_id"].duplicated().sum()
dup8 = h8["hex8_id"].duplicated().sum()
if dup9 == 0 and dup8 == 0:
    add("L3_no_dupes", "PASS", "hex9_id unique, hex8_id unique")
else:
    add("L3_no_dupes", "FAIL", f"hex9 dupes={dup9} hex8 dupes={dup8}")

print("\n=== L4. Every hex-9 parent_hex8 is in hex-8 universe ===")
h8_set = set(h8["hex8_id"])
h9["computed_parent_hex8"] = h9["hex9_id"].apply(lambda c: h3.cell_to_parent(c, 8))
mismatch = (h9["parent_hex8"] != h9["computed_parent_hex8"]).sum()
orphan = h9[~h9["computed_parent_hex8"].isin(h8_set)]
if mismatch == 0 and len(orphan) == 0:
    add("L4_hex9_to_hex8_parent", "PASS", f"all {len(h9):,} hex-9 map to an existing hex-8")
else:
    add("L4_hex9_to_hex8_parent", "FAIL", f"stored_vs_computed={mismatch} orphan={len(orphan)}")

print("\n=== L5. Areal coverage (strict) ===")
sz_union = unary_union(gdf_sz.geometry.values)
def _cell_poly(c):
    return Polygon([(lng, lat) for lat, lng in h3.cell_to_boundary(c)])
hex_union = unary_union([_cell_poly(c) for c in h9["hex9_id"]])
uncov = sz_union.difference(hex_union)
uncov_km2 = gpd.GeoSeries([uncov], crs=4326).to_crs(3414).iloc[0].area / 1e6
sz_km2 = gpd.GeoSeries([sz_union], crs=4326).to_crs(3414).iloc[0].area / 1e6
hex_km2 = gpd.GeoSeries([hex_union], crs=4326).to_crs(3414).iloc[0].area / 1e6
pct = 100.0 * (1 - uncov_km2 / sz_km2)
print(f"  subzone: {sz_km2:.4f} km²  hex: {hex_km2:.4f} km²  overflow: {hex_km2-sz_km2:.4f} km²  uncovered: {uncov_km2:.6f} km²")
if uncov_km2 < 0.001:
    add("L5_areal_coverage", "PASS", f"{pct:.4f}% covered, gap={uncov_km2*1e6:.0f} m²")
elif uncov_km2 < 0.02:
    add("L5_areal_coverage", "WARN", f"{pct:.4f}% covered, gap={uncov_km2*1e6:,.0f} m²")
else:
    add("L5_areal_coverage", "FAIL", f"{pct:.4f}% covered, gap={uncov_km2:.4f} km²")

print("\n=== L6. Per-subzone coverage ===")
gdf_sz_3414 = gdf_sz.to_crs(3414)
hex_union_3414 = gpd.GeoSeries([hex_union], crs=4326).to_crs(3414).iloc[0]
per_sz = []
for _, r in gdf_sz.iterrows():
    g = gdf_sz_3414[gdf_sz_3414["SUBZONE_C"] == r["SUBZONE_C"]].iloc[0].geometry
    a = g.area
    try:
        c = g.intersection(hex_union_3414).area
    except Exception:
        c = 0
    p = 100.0 * c / a if a > 0 else 100.0
    per_sz.append((r["SUBZONE_C"], r["SUBZONE_N"], a / 1e6, p))
per_sz.sort(key=lambda x: x[3])
worst = [x for x in per_sz if x[3] < 99.9999]
if not worst:
    add("L6_per_subzone_coverage", "PASS", f"all {len(per_sz)} subzones at 100%")
else:
    print(f"  {len(worst)} subzones below 99.9999%:")
    for c, n, km2, pc in worst[:10]:
        print(f"    {c}  {n:30s}  {km2:8.4f} km²  {pc:9.5f}%")
    status = "WARN" if worst[0][3] > 99.0 else "FAIL"
    add("L6_per_subzone_coverage", status, f"{len(worst)} subzones below 99.9999%, worst={worst[0][3]:.4f}%")

report["generated_at"] = __import__("time").strftime("%Y-%m-%dT%H:%M:%S")
report["subzones"] = len(gdf_sz)
report["hex9_count"] = len(h9)
report["hex8_count"] = len(h8)
report["areas"] = {
    "subzones_km2": round(sz_km2, 4),
    "hex9_union_km2": round(hex_km2, 4),
    "uncovered_km2": round(uncov_km2, 6),
}
report["worst_subzones"] = [
    {"code": c, "name": n, "km2": round(km2, 4), "pct": round(p, 4)} for c, n, km2, p in per_sz[:20]
]
with open(ROOT / "hex" / "coverage_report.json", "w") as f:
    json.dump(report, f, indent=2)

passes = sum(1 for c in report["checks"] if c["status"] == "PASS")
print(f"\n{passes}/{len(report['checks'])} checks passed")
for c in report["checks"]:
    st = c["status"]
    nm = c["check"]
    dt = c["detail"]
    print(f"  {st:4s}  {nm}  — {dt}")
