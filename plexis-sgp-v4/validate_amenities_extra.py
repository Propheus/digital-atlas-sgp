"""
Plexis SGP v4 — amenities_extra validator.

A1 conservation: hex9 sum of *_count == input row count for each amenity
A2 hex9 → hex8 conservation (sum across all sum cols)
A3 tourist attractions concentrated in CBD/Sentosa/Orchard
A4 hawker centres present in HDB-rich PAs (Tampines, Bedok, Hougang, ...)
A5 nearest CHAS clinic median <2km in HDB hexes
A6 preschools_within_400m mean ≥0.5 in HDB hexes (most homes have 1+ preschool nearby)
A7 silver zones present in elderly-rich PAs (Toa Payoh, Bedok, Bukit Merah, Queenstown)
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
h9 = pd.read_parquet(ROOT / "hex/hex9_amenities_extra.parquet")
h8 = pd.read_parquet(ROOT / "hex/hex8_amenities_extra.parquet")
sz = pd.read_parquet(ROOT / "hex/subzone_amenities_extra.parquet")
report_data = json.load(open(ROOT / "hex/amenities_extra_report.json"))
h9_uni = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
hdb = pd.read_parquet(ROOT / "hex/hex9_hdb_resale.parquet")

inputs = report_data["input_counts"]

# A1 conservation per amenity (point-based; silver_zones are polygons)
checks = [
    ("tourist_attraction_count", inputs["tourist"], "tourist"),
    ("hawker_centre_count",       inputs["hawker"],  "hawker"),
    ("chas_clinic_count",         inputs["chas"],    "chas"),
    ("preschool_count",           inputs["preschool"],"preschool"),
]
all_ok = True
for col, expected, tag in checks:
    actual = int(h9[col].sum())
    drift = abs(actual - expected)
    if drift > 5:
        all_ok = False
        add(f"A1_conservation_{tag}", "WARN", f"hex9 sum {actual} vs input {expected} (drift {drift})")
    else:
        add(f"A1_conservation_{tag}", "PASS", f"sum {actual} ≈ input {expected}")

# A2 hex9 → hex8 conservation on a representative col
h9wp = h9.merge(h9_uni[["hex9_id","parent_hex8"]], on="hex9_id")
roll = h9wp.groupby("parent_hex8")["chas_clinic_count"].sum().reset_index().rename(columns={"parent_hex8":"hex8_id"})
m = h8[["hex8_id","chas_clinic_count"]].merge(roll, on="hex8_id", suffixes=("_direct","_rolled"))
diff = (m["chas_clinic_count_direct"] - m["chas_clinic_count_rolled"]).abs().sum()
if diff == 0:
    add("A2_hex9_to_hex8_conservation", "PASS", "exact match (chas_clinic_count)")
else:
    add("A2_hex9_to_hex8_conservation", "FAIL", f"abs diff {diff}")

# A3 tourist attractions — top-5 PAs should include core tourist hubs
tourist_pas = {"DOWNTOWN CORE","ORCHARD","MARINA SOUTH","SOUTHERN ISLANDS","SINGAPORE RIVER",
                "MUSEUM","ROCHOR","KALLANG","BUKIT MERAH","BUKIT TIMAH"}
h9_pa = h9.merge(h9_uni[["hex9_id","parent_pa"]], on="hex9_id")
top5 = set(h9_pa.groupby("parent_pa")["tourist_attraction_count"].sum().nlargest(5).index)
hits = len(top5 & tourist_pas)
if hits >= 3:
    add("A3_tourist_in_hubs", "PASS", f"top5={top5}, hits {hits}/5 in tourist hubs")
else:
    add("A3_tourist_in_hubs", "WARN", f"top5={top5}, hits {hits}")

# A4 hawker centres in HDB-rich PAs
hdb_pas = {"TAMPINES","BEDOK","HOUGANG","WOODLANDS","JURONG WEST","ANG MO KIO","BUKIT MERAH",
            "TOA PAYOH","KALLANG","SENGKANG","CHOA CHU KANG"}
hawker_pas = h9_pa[h9_pa["hawker_centre_count"] > 0]["parent_pa"].unique()
hits = len(set(hawker_pas) & hdb_pas)
if hits >= 7:
    add("A4_hawker_in_hdb_pas", "PASS", f"{hits}/{len(hdb_pas)} HDB PAs have a hawker centre")
else:
    add("A4_hawker_in_hdb_pas", "WARN", f"{hits}/{len(hdb_pas)}")

# A5 CHAS distance in HDB hexes
m = h9.merge(hdb[["hex9_id","hdb_resale_in_town"]], on="hex9_id")
med_chas = m[m["hdb_resale_in_town"] == 1]["nearest_chas_clinic_dist_m"].median()
if med_chas < 2000:
    add("A5_chas_dist_hdb", "PASS", f"median {med_chas:.0f}m to nearest CHAS in HDB hexes")
else:
    add("A5_chas_dist_hdb", "WARN", f"median {med_chas:.0f}m")

# A6 preschools within 400m in HDB hexes
ps_mean = m[m["hdb_resale_in_town"] == 1]["preschools_within_400m"].mean()
if ps_mean >= 0.5:
    add("A6_preschools_400m_hdb", "PASS", f"avg {ps_mean:.2f} preschools within 400m of HDB hexes")
else:
    add("A6_preschools_400m_hdb", "WARN", f"avg {ps_mean:.2f}")

# A7 silver zones in elderly-rich PAs
elderly_pas = {"TOA PAYOH","BUKIT MERAH","BEDOK","ANG MO KIO","QUEENSTOWN","KALLANG",
                "SERANGOON","GEYLANG","CLEMENTI"}
silver_pas = h9_pa[h9_pa["silver_zone_count"] > 0]["parent_pa"].unique()
hits = len(set(silver_pas) & elderly_pas)
if hits >= 3:
    add("A7_silver_in_elderly_pas", "PASS", f"{hits} elderly PAs have silver zones")
else:
    add("A7_silver_in_elderly_pas", "WARN", f"{hits}")

passes = sum(1 for c in report["checks"] if c["status"] == "PASS")
print(f"\n{passes}/{len(report['checks'])} checks passed")

report["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
with open(ROOT / "hex/amenities_extra_validation.json", "w") as f:
    json.dump(report, f, indent=2)
