"""
Plexis SGP v4 — buildings v2 validator.

Six checks:
  B1. HDB block count == 13,386 (authoritative)
  B2. footprint_share ∈ [0, 1] for ALL hexes (the v1 bug)
  B3. CBD hexes have est_built_far > 3 (high-rise commercial → high FAR)
  B4. HDB-heavy hexes (≥ 5 blocks) have residential count > 0
  B5. Highrise count >= n_highrise_bldgs is consistent
  B6. Year sanity: hdb_avg_age between 0 and 70 years
"""
import json
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).parent
report = {"checks": []}


def add(name, status, detail=""):
    report["checks"].append({"check": name, "status": status, "detail": detail})
    tag = "PASS" if status == "PASS" else ("WARN" if status == "WARN" else "FAIL")
    print(f"  [{tag}] {name} — {detail}")


print("Loading...")
b = pd.read_parquet(ROOT / "hex/hex9_buildings_clean.parquet")
h9 = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
print(f"  shape: {b.shape}")

# B1
hdb_total = int(b["hdb_block_count"].sum())
if hdb_total == 13_386:
    add("B1_hdb_block_total", "PASS", f"{hdb_total:,} == 13,386")
else:
    add("B1_hdb_block_total", "FAIL", f"{hdb_total:,} vs 13,386")

# B2 footprint share bounds
n_violations = ((b["bldg_footprint_share"] < 0) | (b["bldg_footprint_share"] > 1.001)).sum()
if n_violations == 0:
    add("B2_footprint_share_in_unit_interval", "PASS",
        f"all {len(b):,} hexes have footprint_share ∈ [0,1]; max={b['bldg_footprint_share'].max():.3f}")
else:
    add("B2_footprint_share_in_unit_interval", "FAIL", f"{n_violations} hexes violate")

# B3 CBD high FAR — restrict to actual CBD core subzones
cbd_subzones = {"CECIL", "RAFFLES PLACE", "TANJONG PAGAR", "ANSON",
                 "BAYFRONT SUBZONE", "MARINA SOUTH SUBZONE", "MARINA CENTRE",
                 "CENTRAL SUBZONE", "CITY HALL", "CHINATOWN", "BOAT QUAY"}
cbd = b.merge(h9[["hex9_id", "parent_subzone_name"]], on="hex9_id")
cbd = cbd[cbd["parent_subzone_name"].isin(cbd_subzones)]
total_cbd_bldg = (cbd["bldg_count"] > 0).sum()
cbd_high = (cbd["est_built_far"] > 3).sum()
pct = 100 * cbd_high / max(total_cbd_bldg, 1)
if pct >= 50:
    add("B3_cbd_core_high_far", "PASS",
        f"{cbd_high}/{total_cbd_bldg} ({pct:.0f}%) of CBD-core hexes (with bldgs) have FAR > 3")
elif pct >= 30:
    add("B3_cbd_core_high_far", "WARN", f"{cbd_high}/{total_cbd_bldg} ({pct:.0f}%)")
else:
    add("B3_cbd_core_high_far", "FAIL", f"{cbd_high}/{total_cbd_bldg} ({pct:.0f}%) — expected ≥ 50%")

# B4 HDB-heavy hexes have residential
hdb_h = b[b["hdb_block_count"] >= 5]
res_in_hdb = (hdb_h["bldg_residential_count"] > 0).sum()
pct = 100 * res_in_hdb / max(len(hdb_h), 1)
if pct >= 90:
    add("B4_hdb_hexes_have_residential", "PASS", f"{res_in_hdb}/{len(hdb_h)} ({pct:.0f}%)")
else:
    add("B4_hdb_hexes_have_residential", "WARN", f"{res_in_hdb}/{len(hdb_h)} ({pct:.0f}%)")

# B5 highrise consistency
n_invalid = (b["n_highrise_bldgs"] > b["bldg_count"]).sum()
if n_invalid == 0:
    add("B5_highrise_count_consistent", "PASS", "n_highrise_bldgs ≤ bldg_count for all hexes")
else:
    add("B5_highrise_count_consistent", "FAIL", f"{n_invalid} violations")

# B6 hdb age sanity
ages = b[b["hdb_avg_age_years"].notna()]["hdb_avg_age_years"]
if len(ages) > 0:
    in_range = ((ages >= 0) & (ages <= 70)).all()
    if in_range:
        add("B6_hdb_age_sanity", "PASS",
            f"all {len(ages):,} HDB-hexes have age ∈ [0, 70], median {ages.median():.1f} years")
    else:
        add("B6_hdb_age_sanity", "FAIL",
            f"out-of-range: min {ages.min():.1f}, max {ages.max():.1f}")
else:
    add("B6_hdb_age_sanity", "WARN", "no HDB age data")

passes = sum(1 for c in report["checks"] if c["status"] == "PASS")
print(f"\n{passes}/{len(report['checks'])} checks passed")
for c in report["checks"]:
    print(f"  {c['status']:4s}  {c['check']}  — {c['detail']}")

report["generated_at"] = __import__("time").strftime("%Y-%m-%dT%H:%M:%S")
with open(ROOT / "hex/buildings_clean_validation.json", "w") as f:
    json.dump(report, f, indent=2)
