"""
Plexis SGP v4 — transit validator.

Six checks:
  T1. MRT station total = 231 (matches geojson)
  T2. Bus stop total ≈ 5,177
  T3. Interchange hexes contain known interchange names (Dhoby Ghaut, Raffles Place, Bishan, ...)
  T4. CBD hexes have low dist_mrt_m (<400m typically)
  T5. transit_score ∈ [0, 1]
  T6. Top hexes by daily_train_taps are in expected MRT-rich PAs
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
t = pd.read_parquet(ROOT / "hex/hex9_transit_clean.parquet")
h9 = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
print(f"  shape: {t.shape}")

# T1 MRT count
n_mrt = int(t["mrt_station_count"].sum())
if n_mrt == 231:
    add("T1_mrt_count", "PASS", f"{n_mrt} stations match geojson 231")
elif 220 <= n_mrt <= 240:
    add("T1_mrt_count", "WARN", f"{n_mrt} (off by {abs(n_mrt-231)}, possible station-on-hex-boundary)")
else:
    add("T1_mrt_count", "FAIL", f"{n_mrt} stations vs 231 expected")

# T2 bus count
n_bus = int(t["bus_stop_count"].sum())
if 5000 <= n_bus <= 5300:
    add("T2_bus_count", "PASS", f"{n_bus} bus stops (expected ~5,177)")
else:
    add("T2_bus_count", "WARN", f"{n_bus} vs ~5,177")

# T3 interchange landmark
inter_h9 = t[t["is_mrt_interchange"]].merge(
    h9[["hex9_id", "parent_subzone_name", "parent_pa"]], on="hex9_id")
known_inter_subzones = {
    "DHOBY GHAUT", "RAFFLES PLACE", "CITY HALL", "BISHAN", "JURONG EAST",
    "BUGIS", "ORCHARD", "PAYA LEBAR", "MARINA BAY", "TAMPINES", "SERANGOON",
    "BUONA VISTA", "OUTRAM", "CENTRAL SUBZONE", "MUSEUM", "BAYFRONT SUBZONE",
    "SINGAPORE GENERAL HOSPITAL", "BISHAN EAST", "TYERSALL", "BOTANIC GARDENS",
    "CHINATOWN", "PROMENADE", "WOODLANDS",
}
matched = inter_h9["parent_subzone_name"].isin(known_inter_subzones).sum()
if matched >= 8:
    add("T3_interchange_landmarks", "PASS", f"{matched}/{len(inter_h9)} interchange hexes in known interchange subzones")
else:
    add("T3_interchange_landmarks", "WARN", f"{matched}/{len(inter_h9)}")

# T4 CBD walkable to MRT
cbd_pas = {"DOWNTOWN CORE", "OUTRAM", "MARINA SOUTH", "ORCHARD", "ROCHOR", "MUSEUM"}
cbd = t.merge(h9[["hex9_id", "parent_pa"]], on="hex9_id")
cbd = cbd[cbd["parent_pa"].isin(cbd_pas)]
near_mrt = cbd["near_mrt_400m"].sum()
total_cbd = len(cbd)
pct = 100 * near_mrt / max(total_cbd, 1)
if pct >= 60:
    add("T4_cbd_mrt_walkable", "PASS",
        f"{near_mrt}/{total_cbd} ({pct:.0f}%) of CBD hexes within 400m of MRT")
else:
    add("T4_cbd_mrt_walkable", "WARN", f"{near_mrt}/{total_cbd} ({pct:.0f}%)")

# T5 transit_score bounds
ts_max = t["transit_score"].max()
ts_min = t["transit_score"].min()
if 0 <= ts_min and ts_max <= 1:
    add("T5_transit_score_bounds", "PASS", f"range [{ts_min:.4f}, {ts_max:.4f}]")
else:
    add("T5_transit_score_bounds", "FAIL", f"range [{ts_min}, {ts_max}]")

# T6 top hexes by train taps
top = t.nlargest(10, "daily_train_taps").merge(
    h9[["hex9_id", "parent_pa"]], on="hex9_id")
expected_pas = {"DOWNTOWN CORE", "OUTRAM", "MARINA SOUTH", "ORCHARD", "MUSEUM",
                "BUKIT MERAH", "ROCHOR", "BISHAN", "TANGLIN", "GEYLANG",
                "JURONG EAST", "TAMPINES", "BUKIT PANJANG", "CHOA CHU KANG",
                "TOA PAYOH", "WOODLANDS", "PUNGGOL", "SENGKANG", "QUEENSTOWN"}
in_pa = top["parent_pa"].isin(expected_pas).sum()
if in_pa >= 8:
    add("T6_top_taps_in_mrt_rich_pas", "PASS", f"{in_pa}/10 top-tap hexes in expected MRT-rich PAs")
else:
    add("T6_top_taps_in_mrt_rich_pas", "WARN", f"{in_pa}/10")

passes = sum(1 for c in report["checks"] if c["status"] == "PASS")
print(f"\n{passes}/{len(report['checks'])} checks passed")
for c in report["checks"]:
    print(f"  {c['status']:4s}  {c['check']}  — {c['detail']}")

report["generated_at"] = __import__("time").strftime("%Y-%m-%dT%H:%M:%S")
with open(ROOT / "hex/transit_validation.json", "w") as f:
    json.dump(report, f, indent=2)
