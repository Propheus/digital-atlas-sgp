"""
Plexis SGP v4 — schools validator.

S1 conservation: hex9 sum of school_count_total == # geocoded schools (within drift)
S2 hex9 → hex8 sum conservation
S3 most populous PA (Tampines / Sengkang / Bedok / Jurong West / Woodlands) has ≥10 schools
S4 in_primary_school_zone share between 30-90% of hex9 cells (zones don't blanket SGP)
S5 nearest_primary_school_dist_m median <2000m (most of SGP is near a primary school)
S6 premium school count ≥30 (SAP + Gifted nationally)
"""
import json, time
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent
report = {"checks": []}


def add(name, status, detail=""):
    report["checks"].append({"check": name, "status": status, "detail": detail})
    print(f"  [{status}] {name} — {detail}")


print("Loading...")
h9 = pd.read_parquet(ROOT / "hex/hex9_schools.parquet")
h8 = pd.read_parquet(ROOT / "hex/hex8_schools.parquet")
sz = pd.read_parquet(ROOT / "hex/subzone_schools.parquet")
report_data = json.load(open(ROOT / "hex/schools_report.json"))

# S1 conservation
total_in = report_data["input_schools"]
h9_total = int(h9["school_count_total"].sum())
if abs(h9_total - total_in) <= 5:
    add("S1_conservation_h9", "PASS", f"hex9 sum {h9_total} ≈ input {total_in}")
else:
    add("S1_conservation_h9", "WARN", f"hex9 sum {h9_total} vs input {total_in}")

# S2 hex9 → hex8 conservation
h9_uni = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
h9wp = h9.merge(h9_uni[["hex9_id","parent_hex8"]], on="hex9_id")
roll = h9wp.groupby("parent_hex8")["school_count_total"].sum().reset_index().rename(columns={"parent_hex8":"hex8_id"})
m = h8[["hex8_id","school_count_total"]].merge(roll, on="hex8_id", suffixes=("_direct","_rolled"))
diff = (m["school_count_total_direct"] - m["school_count_total_rolled"]).abs().sum()
if diff == 0:
    add("S2_hex9_to_hex8_conservation", "PASS", "exact match")
else:
    add("S2_hex9_to_hex8_conservation", "FAIL", f"abs diff {diff}")

# S3 populous PAs have ≥ 10 schools
expected_pas = {"TAMPINES","SENGKANG","BEDOK","JURONG WEST","WOODLANDS","HOUGANG","CHOA CHU KANG","ANG MO KIO"}
h9_pa = h9.merge(h9_uni[["hex9_id","parent_pa"]], on="hex9_id")
pa_counts = h9_pa.groupby("parent_pa")["school_count_total"].sum().reset_index()
hits = pa_counts[(pa_counts["parent_pa"].isin(expected_pas)) & (pa_counts["school_count_total"] >= 10)]
if len(hits) >= 5:
    add("S3_populous_pas_have_schools", "PASS", f"{len(hits)}/{len(expected_pas)} populous PAs have ≥10 schools")
else:
    add("S3_populous_pas_have_schools", "WARN", f"{len(hits)}/{len(expected_pas)}")

# S4 — primary catchment coverage: hex9s with ≥1 primary school within 1km
near_1km_share = (h9["primary_schools_within_1km"] >= 1).mean()
if 0.25 <= near_1km_share <= 0.85:
    add("S4_primary_catchment_share", "PASS",
        f"{near_1km_share*100:.1f}% of hex9 have ≥1 primary within 1km")
else:
    add("S4_primary_catchment_share", "WARN", f"{near_1km_share*100:.1f}%")

# S5 — nearest primary distance: residential hexes (in HDB town) should have median < 1500m
hdb_hexes = pd.read_parquet(ROOT / "hex/hex9_hdb_resale.parquet")
m = h9.merge(hdb_hexes[["hex9_id","hdb_resale_in_town"]], on="hex9_id")
med_hdb = m[m["hdb_resale_in_town"] == 1]["nearest_primary_school_dist_m"].median()
if med_hdb < 1500:
    add("S5_nearest_primary_in_hdb_towns", "PASS", f"median {med_hdb:.0f}m to nearest primary (HDB hexes)")
else:
    add("S5_nearest_primary_in_hdb_towns", "WARN", f"median {med_hdb:.0f}m")

# S6 premium count
prem_total = int(h9["school_count_premium"].sum())
if prem_total >= 30:
    add("S6_premium_count", "PASS", f"{prem_total} premium (SAP/Gifted/IP) schools nationally")
else:
    add("S6_premium_count", "WARN", f"{prem_total} premium")

passes = sum(1 for c in report["checks"] if c["status"] == "PASS")
print(f"\n{passes}/{len(report['checks'])} checks passed")

report["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
with open(ROOT / "hex/schools_validation.json", "w") as f:
    json.dump(report, f, indent=2)
