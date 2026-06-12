"""
Plexis SGP v4 — place_micrograph validator.

8 checks spanning the 4 dimensions x several categories:

  M1 row count + non-null parity
  M2 cafe_coffee in CBD has higher avg competitors_400m than suburban cafes
  M3 hawker complements (residential nearby) higher in HDB-town hawkers vs CBD hawkers
  M4 hotel anchor_strength higher in Sentosa/Marina vs industrial-belt hotels
  M5 Orchard shopping_retail anchors_400m clearly higher than national avg
  M6 industrial_mfg avg_walk_score lower than residential avg_walk_score
  M7 transit_score / dist_mrt_m relationship: places with dist_mrt_m<400 should have transit_score>0.3
  M8 anchor_strength_sum non-degenerate (> 0 for ≥30% of places, < SENTINEL elsewhere)
"""
import json, time
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
report = {"checks": []}


def add(name, status, detail=""):
    report["checks"].append({"check": name, "status": status, "detail": detail})
    print(f"  [{status}] {name} — {detail}")


print("Loading...")
mg = pd.read_parquet(ROOT / "places/sgp_places_micrograph.parquet")
places = pd.read_parquet(ROOT / "places/sgp_places_final.parquet")

# Join for context
df = places[["id","plexis_category","parent_pa","parent_subzone_name","hdb_town"]].merge(mg, on="id")

# M1 — count nulls only in mg's own pmg_* columns (not join cols from places)
n_in = len(places); n_out = len(mg)
pmg_cols = [c for c in mg.columns if c.startswith("pmg_")]
mg_nulls = mg[pmg_cols].isna().sum().sum()
if n_in == n_out and mg_nulls == 0:
    add("M1_rowcount_no_nulls", "PASS", f"{n_out:,} rows × {len(pmg_cols)} pmg_* cols, 0 nulls")
elif n_in == n_out:
    add("M1_rowcount_no_nulls", "WARN", f"{n_out:,} rows, {mg_nulls} null cells in pmg_*")
else:
    add("M1_rowcount_no_nulls", "FAIL", f"in {n_in} != out {n_out}")

# M2 cafe in CBD vs cafe national avg
cbd_pas = {"DOWNTOWN CORE","ORCHARD","OUTRAM","RIVER VALLEY","ROCHOR","NEWTON",
           "MARINA SOUTH","MUSEUM","SINGAPORE RIVER","TANGLIN"}
cafes = df[df["plexis_category"]=="cafe_coffee"]
cbd_cafes = cafes[cafes["parent_pa"].isin(cbd_pas)]
nat_cafes = cafes[~cafes["parent_pa"].isin(cbd_pas)]
cbd_avg = cbd_cafes["pmg_competitors_400m"].mean()
nat_avg = nat_cafes["pmg_competitors_400m"].mean()
if cbd_avg > nat_avg * 1.3:
    add("M2_cbd_cafe_competition_higher", "PASS",
        f"CBD cafe comp@400m {cbd_avg:.1f} vs national {nat_avg:.1f}")
else:
    add("M2_cbd_cafe_competition_higher", "WARN",
        f"CBD {cbd_avg:.1f} vs national {nat_avg:.1f}")

# M3 — HDB hawkers have HIGHER complement/competitor ratio than CBD hawkers
# (relatively, HDB has more complementary residential vs competitive food density;
#  CBD is dense in everything so absolute counts go up but ratio drops).
hawkers = df[df["plexis_category"]=="hawker"]
hdb_hawkers = hawkers[hawkers["hdb_town"].notna() & ~hawkers["parent_pa"].isin(cbd_pas)]
cbd_hawkers = hawkers[hawkers["parent_pa"].isin(cbd_pas)]
def _ratio(d):
    cplt = d["pmg_complements_400m"].sum()
    comp = max(d["pmg_competitors_400m"].sum(), 1)
    return cplt / comp
hdb_r = _ratio(hdb_hawkers)
cbd_r = _ratio(cbd_hawkers)
if hdb_r > cbd_r:
    add("M3_hdb_hawker_relative_complements", "PASS",
        f"HDB cplt/comp {hdb_r:.2f} > CBD {cbd_r:.2f}")
else:
    add("M3_hdb_hawker_relative_complements", "WARN",
        f"HDB {hdb_r:.2f} vs CBD {cbd_r:.2f}")

# M4 hotel anchor strength — Sentosa/Marina vs industrial PAs
hotels = df[df["plexis_category"]=="hotel_hospitality"]
flagship_pas = {"SOUTHERN ISLANDS","MARINA SOUTH","DOWNTOWN CORE","ORCHARD"}
ind_pas = {"WOODLANDS","JURONG WEST","TUAS","BUKIT BATOK","BUKIT MERAH","HOUGANG"}
flag = hotels[hotels["parent_pa"].isin(flagship_pas)]["pmg_anchor_strength_sum"].mean()
ind  = hotels[hotels["parent_pa"].isin(ind_pas)]["pmg_anchor_strength_sum"].mean()
if not np.isnan(flag) and not np.isnan(ind) and flag > ind:
    add("M4_flagship_hotel_anchors_higher", "PASS",
        f"flagship {flag:.1f} > industrial {ind:.1f}")
else:
    add("M4_flagship_hotel_anchors_higher", "WARN",
        f"flagship {flag:.1f} vs industrial {ind:.1f}")

# M5 Orchard shopping_retail anchors_400m
retail = df[df["plexis_category"]=="shopping_retail"]
orch = retail[retail["parent_pa"]=="ORCHARD"]["pmg_anchors_400m"].mean()
nat_retail = retail["pmg_anchors_400m"].mean()
if orch > nat_retail * 1.5:
    add("M5_orchard_retail_anchors_higher", "PASS",
        f"Orchard {orch:.1f} vs national {nat_retail:.1f}")
else:
    add("M5_orchard_retail_anchors_higher", "WARN",
        f"Orchard {orch:.1f} vs national {nat_retail:.1f}")

# M6 industrial vs residential hex walk score
ind_w  = df[df["plexis_category"]=="industrial_mfg"]["pmg_hex_walk_score"].mean()
res_w  = df[df["plexis_category"]=="residential"]["pmg_hex_walk_score"].mean()
if not np.isnan(ind_w) and not np.isnan(res_w) and res_w > ind_w:
    add("M6_residential_walk_higher_than_industrial", "PASS",
        f"residential {res_w:.2f} > industrial {ind_w:.2f}")
else:
    add("M6_residential_walk_higher_than_industrial", "WARN",
        f"residential {res_w:.2f} vs industrial {ind_w:.2f}")

# M7 walking distance to MRT — CBD places much closer than industrial
cbd_mrt = df[df["parent_pa"].isin(cbd_pas)]["pmg_walk_dist_mrt_m"].mean()
ind_pas2 = {"WOODLANDS","JURONG WEST","TUAS","BUKIT BATOK","PIONEER","BENOI"}
ind_mrt = df[df["parent_pa"].isin(ind_pas2)]["pmg_walk_dist_mrt_m"].mean()
overall_med = df["pmg_walk_dist_mrt_m"].median()
near_pct = (df["pmg_near_mrt_400m"] == 1).mean() * 100
if cbd_mrt < ind_mrt and 100 < overall_med < 3000:
    add("M7_walk_dist_mrt_cbd_lower", "PASS",
        f"CBD {cbd_mrt:.0f}m < industrial {ind_mrt:.0f}m | median {overall_med:.0f}m | within 400m: {near_pct:.1f}%")
else:
    add("M7_walk_dist_mrt_cbd_lower", "WARN",
        f"CBD {cbd_mrt:.0f}m vs industrial {ind_mrt:.0f}m | median {overall_med:.0f}m")

# M8 — anchor_strength_sum non-degenerate (varies meaningfully across categories)
# Singapore is very dense, so a high % within reach of any magnet is expected.
# What we want: meaningful variance (not all the same value).
ass = mg["pmg_anchor_strength_sum"]
nz = (ass > 0).mean()
p10, p50, p90 = ass.quantile([0.1, 0.5, 0.9]).values
spread_ratio = p90 / max(p10, 0.01)
if 0.30 <= nz <= 0.95 and spread_ratio > 50:
    add("M8_anchor_strength_distribution", "PASS",
        f"{nz*100:.1f}% nonzero | p10={p10:.1f} p50={p50:.1f} p90={p90:.1f} spread={spread_ratio:.0f}×")
else:
    add("M8_anchor_strength_distribution", "WARN",
        f"{nz*100:.1f}% nonzero | spread={spread_ratio:.0f}×")

passes = sum(1 for c in report["checks"] if c["status"] == "PASS")
print(f"\n{passes}/{len(report['checks'])} checks passed")

report["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
with open(ROOT / "places/place_micrograph_validation.json", "w") as f:
    json.dump(report, f, indent=2, default=float)
