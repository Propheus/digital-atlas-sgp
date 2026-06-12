"""
Plexis SGP v4 — building allocation validator.

Six checks:
  B1. HDB block count matches authoritative (13,386)
  B2. Hexes with HDB (~1,184) have HDB residential class > 0 in fused
  B3. Total buildings inside SGP universe = ~244K (377K total file − ~133K cross-border)
  B4. Bucket counts sum to bldg_count per hex
  B5. is_highrise hexes (>=10 floors) cluster in expected CBD/HDB-tower areas
  B6. No negatives, no impossible floor counts (-1 to 100 reasonable range)
"""
import json, os
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
b = pd.read_parquet(ROOT / "hex/hex9_buildings.parquet")
h9 = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
print(f"  hex9_buildings: {b.shape}  cols: {list(b.columns)[:8]}...")

# === B1 HDB total ===
hdb_total = b["hdb_block_count"].sum()
EXPECTED_HDB = 13_386
if hdb_total == EXPECTED_HDB:
    add("B1_hdb_block_total", "PASS", f"{int(hdb_total):,} == {EXPECTED_HDB:,}")
else:
    add("B1_hdb_block_total", "FAIL", f"{int(hdb_total):,} vs {EXPECTED_HDB:,}")

# === B2 HDB hexes have residential buildings ===
hdb_hexes = b[b["hdb_block_count"] > 0]
res_in_hdb = (hdb_hexes["bldg_residential_count"] > 0).sum()
pct = 100 * res_in_hdb / max(len(hdb_hexes), 1)
if pct >= 95:
    add("B2_hdb_hexes_have_residential", "PASS", f"{res_in_hdb}/{len(hdb_hexes)} ({pct:.1f}%)")
elif pct >= 85:
    add("B2_hdb_hexes_have_residential", "WARN", f"{res_in_hdb}/{len(hdb_hexes)} ({pct:.1f}%)")
else:
    add("B2_hdb_hexes_have_residential", "FAIL", f"{res_in_hdb}/{len(hdb_hexes)} ({pct:.1f}%)")

# === B3 total buildings within SGP ===
total = b["bldg_count"].sum()
# Reasonable range: 230K–260K (the bulk of SGP's permanent built stock)
if 230_000 <= total <= 260_000:
    add("B3_buildings_in_sgp_bounds", "PASS", f"{int(total):,} buildings (230K–260K expected for SGP-only)")
else:
    add("B3_buildings_in_sgp_bounds", "WARN", f"{int(total):,} buildings (out of expected 230–260K range)")

# === B4 bucket counts sum to total ===
bucket_cols = [c for c in b.columns if c.startswith("bldg_") and c.endswith("_count") and c != "bldg_count"]
bucket_sum = b[bucket_cols].sum(axis=1)
discrepancy = (bucket_sum - b["bldg_count"]).abs().max()
if discrepancy <= 1e-9:
    add("B4_bucket_sums_match_total", "PASS", f"all hexes consistent (max disc {discrepancy:.0e})")
else:
    add("B4_bucket_sums_match_total", "FAIL", f"max disc {discrepancy}")

# === B5 highrise geography ===
hi = b[b["is_highrise"]].merge(h9[["hex9_id", "parent_pa"]].rename(columns={"parent_pa": "pa"}), on="hex9_id")
expected_pas = {"DOWNTOWN CORE", "ORCHARD", "OUTRAM", "BUKIT MERAH", "MARINA SOUTH",
                "TANGLIN", "MARINA EAST", "NEWTON", "ROCHOR", "RIVER VALLEY",
                "GEYLANG", "QUEENSTOWN", "BISHAN", "TOA PAYOH", "PASIR RIS",
                "TAMPINES", "BEDOK", "ANG MO KIO", "WOODLANDS", "JURONG WEST",
                "JURONG EAST", "PUNGGOL", "SENGKANG", "KALLANG", "BUKIT BATOK",
                "CHOA CHU KANG", "BUKIT TIMAH", "HOUGANG", "CLEMENTI"}
in_expected = hi["pa"].isin(expected_pas).sum()
pct_in = 100 * in_expected / max(len(hi), 1)
if pct_in >= 90:
    add("B5_highrise_in_known_dense_pas", "PASS",
        f"{in_expected}/{len(hi)} highrise hexes ({pct_in:.0f}%) in known dense PAs")
else:
    add("B5_highrise_in_known_dense_pas", "WARN",
        f"{in_expected}/{len(hi)} ({pct_in:.0f}%)")

# === B6 sanity ranges ===
neg_count = (b[bucket_cols].values < 0).sum()
neg_count += (b["bldg_count"] < 0).sum()
neg_count += (b["bldg_total_area_m2"] < 0).sum()
max_floors = b["best_max_floors"].max() if b["best_max_floors"].notna().any() else 0
ok_floors = (b["best_max_floors"].dropna() >= -2).all() and max_floors <= 100
if neg_count == 0 and ok_floors:
    add("B6_sanity_ranges", "PASS",
        f"no negatives; max floors {int(max_floors)}")
else:
    add("B6_sanity_ranges", "FAIL", f"negatives={neg_count}, ok_floors={ok_floors}, max={max_floors}")

passes = sum(1 for c in report["checks"] if c["status"] == "PASS")
print(f"\n{passes}/{len(report['checks'])} checks passed")
for c in report["checks"]:
    print(f"  {c['status']:4s}  {c['check']}  — {c['detail']}")

report["generated_at"] = __import__("time").strftime("%Y-%m-%dT%H:%M:%S")
with open(ROOT / "hex/buildings_validation.json", "w") as f:
    json.dump(report, f, indent=2)
