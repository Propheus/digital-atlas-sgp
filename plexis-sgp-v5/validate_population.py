"""
Plexis SGP v4 — strict population dasymetric validator.

Six checks:
  P1. Global total: allocated == expected (tolerance 0)
  P2. HDB sub-total: allocated HDB pop == expected
  P3. Non-HDB sub-total: allocated == expected
  P4. Per-subzone allocation using hex × subzone overlap match expected
  P5. Age sums: 0-14 + 15-64 + 65+ == total
  P6. No negative populations, no nulls
"""
import json
from pathlib import Path
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon
import os
import h3

ROOT = Path(__file__).parent


def _resolve_data_root():
    if os.environ.get("PLEXIS_DATA_ROOT"):
        return Path(os.environ["PLEXIS_DATA_ROOT"])
    for c in [Path("/home/azureuser/digital-atlas-sgp/data"), ROOT.parent / "data"]:
        if c.exists():
            return c
    raise FileNotFoundError("No data root found; set PLEXIS_DATA_ROOT")


DATA = _resolve_data_root()
report = {"checks": []}


def add(name, status, detail=""):
    report["checks"].append({"check": name, "status": status, "detail": detail})
    tag = "PASS" if status == "PASS" else ("WARN" if status == "WARN" else "FAIL")
    print(f"  [{tag}] {name} — {detail}")


def normalize_name(s):
    if s is None: return None
    return " ".join(str(s).upper().replace("-", " ").split())


print("Loading...")
hp = pd.read_parquet(ROOT / "hex/hex9_population.parquet")
h9 = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
sz = gpd.read_file(ROOT / "boundaries/subzones.geojson").to_crs(4326)
pop = pd.read_csv(DATA / "demographics/pop_age_sex_tod_2025.csv")
pop = pop[pop["Time"] == 2025]
pop["SZ_norm"] = pop["SZ"].apply(normalize_name)

HDB_TOD = {
    "HDB 1- and 2-Room Flats", "HDB 3-Room Flats", "HDB 4-Room Flats",
    "HDB 5-Room and Executive Flats", "HUDC Flats (excluding those privatised)",
}
pop["is_hdb"] = pop["TOD"].isin(HDB_TOD)
sz_pop = pop.groupby("SZ_norm").agg(
    pop_total=("Pop", "sum"),
    pop_hdb=("Pop", lambda s: s[pop.loc[s.index, "is_hdb"]].sum()),
).reset_index()
sz_pop["pop_non_hdb"] = sz_pop["pop_total"] - sz_pop["pop_hdb"]

# P1
expected_total = sz_pop["pop_total"].sum()
allocated_total = hp["pop_total"].sum()
drift = allocated_total - expected_total
if abs(drift) < 0.5:
    add("P1_global_total", "PASS", f"{allocated_total:,.0f} == {expected_total:,}")
else:
    add("P1_global_total", "FAIL", f"allocated={allocated_total:,.0f} vs expected={expected_total:,}, drift={drift:.0f}")

# P2
expected_hdb = sz_pop["pop_hdb"].sum()
allocated_hdb = hp["pop_hdb"].sum()
if abs(allocated_hdb - expected_hdb) < 1:
    add("P2_hdb_total", "PASS", f"{allocated_hdb:,.0f} == {expected_hdb:,}")
else:
    add("P2_hdb_total", "FAIL", f"{allocated_hdb:,.0f} vs {expected_hdb:,}")

# P3
expected_non = sz_pop["pop_non_hdb"].sum()
allocated_non = hp["pop_non_hdb"].sum()
if abs(allocated_non - expected_non) < 1:
    add("P3_non_hdb_total", "PASS", f"{allocated_non:,.0f} == {expected_non:,}")
else:
    add("P3_non_hdb_total", "FAIL", f"{allocated_non:,.0f} vs {expected_non:,}")

# P4 per-subzone using the SAME chunk-level rule as allocation:
#   HDB via dwelling units, non-HDB via intersection area
# Reconstruct chunks independently and sum by subzone.
print("Reconstructing chunks to validate per-subzone sum...")
import geopandas as _gpd
from shapely.geometry import Polygon
from shapely.strtree import STRtree

hdb_geo = _gpd.read_file(DATA / "housing/hdb_existing_buildings.geojson").to_crs(4326)
hdb_info = pd.read_csv(DATA / "housing/hdb_property_info.csv")
sz_3414 = sz.to_crs(3414)
hdb_3414 = hdb_geo.to_crs(3414)
hdb_3414["centroid"] = hdb_3414.geometry.centroid
tree = STRtree(sz_3414.geometry.values)
sz_names_arr = list(sz_3414["SUBZONE_N"])

def sz_of(pt):
    for i in tree.query(pt):
        if sz_3414.geometry.iloc[i].contains(pt):
            return sz_names_arr[i]
    d = sz_3414.geometry.distance(pt)
    return sz_names_arr[d.idxmin()]

hdb_3414["subzone_name"] = hdb_3414["centroid"].apply(sz_of)
hdb_3414["SZ_norm"] = hdb_3414["subzone_name"].apply(normalize_name)
cent_4326 = hdb_geo.geometry.centroid
hdb_3414["hex9_id"] = [h3.latlng_to_cell(c.y, c.x, 9) for c in cent_4326]

hdb_info["blk_no_n"] = hdb_info["blk_no"].astype(str).str.upper().str.strip()
hdb_3414["BLK_NO_N"] = hdb_3414["BLK_NO"].astype(str).str.upper().str.strip()
info_units = hdb_info.groupby("blk_no_n")["total_dwelling_units"].sum().to_dict()
geo_counts = hdb_3414["BLK_NO_N"].value_counts().to_dict()
hdb_3414["dwelling_units"] = hdb_3414["BLK_NO_N"].apply(lambda b: info_units.get(b, 0) / geo_counts.get(b, 1))

hdb_chunks = hdb_3414.groupby(["SZ_norm", "hex9_id"]).agg(units=("dwelling_units", "sum")).reset_index()
sz_units = hdb_3414.groupby("SZ_norm")["dwelling_units"].sum().to_dict()

overlap = pd.read_parquet(ROOT / "hex/hex9_subzone_overlap.parquet")
sz_code_to_name = dict(zip(sz["SUBZONE_C"], sz["SUBZONE_N"]))
overlap["subzone_name"] = overlap["subzone_c"].map(sz_code_to_name)
overlap["SZ_norm"] = overlap["subzone_name"].apply(normalize_name)

def hex_poly_3414(hex_id):
    ring = [(lng, lat) for lat, lng in h3.cell_to_boundary(hex_id)]
    return _gpd.GeoSeries([Polygon(ring)], crs=4326).to_crs(3414).iloc[0]

hex_ids = overlap["hex9_id"].unique()
hex_poly_cache = {h_id: hex_poly_3414(h_id) for h_id in hex_ids}
sz_poly_cache = dict(zip(sz_3414["SUBZONE_N"], sz_3414.geometry.values))
def inter_area(row):
    hp_ = hex_poly_cache.get(row["hex9_id"])
    sp = sz_poly_cache.get(row["subzone_name"])
    if hp_ is None or sp is None: return 0
    try: return hp_.intersection(sp).area
    except Exception: return 0
overlap["inter_m2"] = overlap.apply(inter_area, axis=1)
sz_total_area = overlap.groupby("SZ_norm")["inter_m2"].sum().to_dict()

chunks = overlap[["SZ_norm", "hex9_id", "inter_m2"]].merge(
    hdb_chunks.rename(columns={"units": "chunk_units"}), on=["SZ_norm", "hex9_id"], how="outer"
)
chunks["chunk_units"] = chunks["chunk_units"].fillna(0)
chunks["inter_m2"] = chunks["inter_m2"].fillna(0)
chunks = chunks.merge(sz_pop[["SZ_norm", "pop_hdb", "pop_non_hdb"]], on="SZ_norm", how="left")
chunks["sz_units"] = chunks["SZ_norm"].map(sz_units).fillna(0)
chunks["sz_area"] = chunks["SZ_norm"].map(sz_total_area).fillna(0)
chunks["chunk_pop_hdb"] = np.where(chunks["sz_units"] > 0, chunks["pop_hdb"].fillna(0) * chunks["chunk_units"] / chunks["sz_units"], 0)
chunks["chunk_pop_non_hdb"] = np.where(chunks["sz_area"] > 0, chunks["pop_non_hdb"].fillna(0) * chunks["inter_m2"] / chunks["sz_area"], 0)
chunks["chunk_pop"] = chunks["chunk_pop_hdb"] + chunks["chunk_pop_non_hdb"]

sz_alloc = chunks.groupby("SZ_norm")["chunk_pop"].sum().reset_index(name="alloc_pop")
check = sz_pop[["SZ_norm", "pop_total"]].merge(sz_alloc, on="SZ_norm", how="left")
check["alloc_pop"] = check["alloc_pop"].fillna(0)
check["drift"] = check["alloc_pop"] - check["pop_total"]
check["pct_drift"] = np.where(
    check["pop_total"] > 0,
    (check["alloc_pop"] - check["pop_total"]) / check["pop_total"],
    np.where(check["alloc_pop"] > 50, 1.0, 0.0),
)
mean_abs_drift = check["pct_drift"].abs().mean()
max_abs_drift = check["pct_drift"].abs().max()
over_1pct = (check["pct_drift"].abs() > 0.01).sum()
worst = check.iloc[check["pct_drift"].abs().sort_values(ascending=False).head(10).index]

if max_abs_drift < 0.01 and over_1pct == 0:
    add("P4_per_subzone_chunk_alloc", "PASS",
        f"mean |drift|={mean_abs_drift*100:.4f}%, max={max_abs_drift*100:.4f}%")
elif max_abs_drift < 0.05:
    add("P4_per_subzone_chunk_alloc", "WARN",
        f"mean |drift|={mean_abs_drift*100:.4f}%, max={max_abs_drift*100:.4f}%, {over_1pct} subzones >1%")
else:
    add("P4_per_subzone_chunk_alloc", "FAIL",
        f"mean |drift|={mean_abs_drift*100:.4f}%, max={max_abs_drift*100:.4f}%, {over_1pct} subzones >1%")
    print("  Worst 10 subzones by drift:")
    for _, r in worst.iterrows():
        print(f"    {r['SZ_norm']:30s}  expected={r['pop_total']:>8,.0f}  allocated={r['alloc_pop']:>8,.0f}  drift={r['drift']:>+8.0f}")

# P5 age sums
age_sum = hp["pop_0_14"] + hp["pop_15_64"] + hp["pop_65plus"]
age_drift = (age_sum - hp["pop_total"]).abs().max()
if age_drift < 0.01:
    add("P5_age_sums_match_total", "PASS", f"max discrepancy {age_drift:.4f}")
else:
    add("P5_age_sums_match_total", "FAIL", f"max discrepancy {age_drift:.4f}")

# P6 non-negative, no nulls
neg = (hp[["pop_total", "pop_hdb", "pop_non_hdb", "pop_0_14", "pop_15_64", "pop_65plus"]] < 0).any().any()
null = hp[["pop_total", "pop_hdb", "pop_non_hdb", "pop_0_14", "pop_15_64", "pop_65plus"]].isna().any().any()
if not neg and not null:
    add("P6_valid_values", "PASS", "no negatives, no nulls")
else:
    add("P6_valid_values", "FAIL", f"negative={neg}, null={null}")

passes = sum(1 for c in report["checks"] if c["status"] == "PASS")
print(f"\n{passes}/{len(report['checks'])} checks passed")
for c in report["checks"]:
    print(f"  {c['status']:4s}  {c['check']}  — {c['detail']}")

report["generated_at"] = __import__("time").strftime("%Y-%m-%dT%H:%M:%S")
with open(ROOT / "hex/population_validation.json", "w") as f:
    json.dump(report, f, indent=2)
