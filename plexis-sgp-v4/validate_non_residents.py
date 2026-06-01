"""
Plexis SGP v4 — non-resident allocation validator.

Five checks:
  N1. National non-resident total = 1,769,520 (SingStat)
  N2. National grand total = 5,982,320 (residents + non-residents)
  N3. pop_total_all == pop_resident + pop_nonresident per hex (no drift)
  N4. nonres_share in [0, 1] (sane range)
  N5. Top hexes match expected industrial-dorm geography
       (Senoko, Kampong Ubi, Tai Seng, Wenya, Toh Tuck etc.)
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
pop = pd.read_parquet(ROOT / "hex/hex9_population.parquet")
h9 = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
print(f"  hex9_population: {pop.shape}  cols: {list(pop.columns)}")

required = {"pop_resident", "pop_nonresident", "pop_total_all", "nonres_share"}
missing = required - set(pop.columns)
if missing:
    print(f"  FAIL: missing columns {missing}")
    raise SystemExit(1)

# === N1 national non-resident total ===
nr = pop["pop_nonresident"].sum()
EXPECTED_NR = 1_769_520
if abs(nr - EXPECTED_NR) < 1:
    add("N1_national_nonres_total", "PASS", f"{nr:,.0f} == {EXPECTED_NR:,}")
else:
    add("N1_national_nonres_total", "FAIL", f"{nr:,.0f} vs {EXPECTED_NR:,}, drift={(nr-EXPECTED_NR):,.0f}")

# === N2 grand total ===
total = pop["pop_total_all"].sum()
EXPECTED_TOTAL = 5_982_320
if abs(total - EXPECTED_TOTAL) < 5:
    add("N2_national_grand_total", "PASS", f"{total:,.0f} == {EXPECTED_TOTAL:,}")
else:
    add("N2_national_grand_total", "FAIL", f"{total:,.0f} vs {EXPECTED_TOTAL:,}")

# === N3 per-hex: pop_total_all == pop_resident + pop_nonresident ===
discrepancy = (pop["pop_total_all"] - pop["pop_resident"] - pop["pop_nonresident"]).abs().max()
if discrepancy < 1e-6:
    add("N3_per_hex_sum", "PASS", f"max discrepancy {discrepancy:.6e}")
else:
    add("N3_per_hex_sum", "FAIL", f"max discrepancy {discrepancy}")

# === N4 nonres_share bounds ===
in_range = ((pop["nonres_share"] >= -1e-9) & (pop["nonres_share"] <= 1 + 1e-9)).all()
if in_range:
    add("N4_nonres_share_bounds", "PASS", f"all in [0, 1], max={pop['nonres_share'].max():.4f}")
else:
    add("N4_nonres_share_bounds", "FAIL",
        f"out-of-range: min={pop['nonres_share'].min()}, max={pop['nonres_share'].max()}")

# === N5 top-hex geography sanity check ===
expected_subzones = {
    "SENOKO SOUTH", "KAMPONG UBI", "TAI SENG", "WENYA", "TOH TUCK", "DEFU", "ALJUNIED",
    "TUAS", "PIONEER", "JOO SENG", "KALLANG BAHRU", "BUKIT MERAH", "ONE NORTH", "SEMBAWANG",
}
h9_lookup = h9[["hex9_id", "parent_subzone_name"]].rename(
    columns={"parent_subzone_name": "subzone_label"}
)
top20 = pop.nlargest(20, "pop_nonresident").merge(h9_lookup, on="hex9_id")
matched = sum(any(e in str(s) for e in expected_subzones) for s in top20["subzone_label"])
if matched >= 12:
    add("N5_top_hex_industrial_geography", "PASS", f"{matched}/20 top hexes in known industrial/dorm zones")
elif matched >= 8:
    add("N5_top_hex_industrial_geography", "WARN", f"{matched}/20 in industrial zones (expected ≥12)")
else:
    add("N5_top_hex_industrial_geography", "FAIL", f"only {matched}/20")
print(f"  Top-20 subzones: {sorted(set(top20['subzone_label']))[:10]}...")

passes = sum(1 for c in report["checks"] if c["status"] == "PASS")
print(f"\n{passes}/{len(report['checks'])} checks passed")
for c in report["checks"]:
    print(f"  {c['status']:4s}  {c['check']}  — {c['detail']}")

report["generated_at"] = __import__("time").strftime("%Y-%m-%dT%H:%M:%S")
with open(ROOT / "hex/non_resident_validation.json", "w") as f:
    json.dump(report, f, indent=2)
