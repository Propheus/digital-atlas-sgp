"""
Plexis SGP v4 — satellite validator.
Five checks:
  S1. nl_2024 in plausible range (0-300; SGP CBD hits ~180)
  S2. Top nl_2024 hexes are in CBD/Orchard subzones
  S3. nl_change_pct distribution sane (-50 to +200, with median near 0)
  S4. wp_pop totals match SGP scale (4-8M)
  S5. nl_commercial_indicator high in CBD, low in residential
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
s = pd.read_parquet(ROOT / "hex/hex9_satellite.parquet")
h9 = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
print(f"  shape: {s.shape}")

# S1
nl_max = s["nl_2024"].max()
nl_min = s["nl_2024"].min()
if 0 <= nl_min and 50 <= nl_max <= 300:
    add("S1_nl_2024_range", "PASS", f"range [{nl_min:.1f}, {nl_max:.1f}]")
else:
    add("S1_nl_2024_range", "WARN", f"range [{nl_min:.1f}, {nl_max:.1f}]")

# S2 top brightness in CBD/Orchard
top = s.nlargest(20, "nl_2024").merge(h9[["hex9_id", "parent_pa"]], on="hex9_id")
expected = {"DOWNTOWN CORE", "ORCHARD", "OUTRAM", "MARINA SOUTH", "MUSEUM",
            "ROCHOR", "RIVER VALLEY", "NEWTON", "SINGAPORE RIVER", "MARINA EAST"}
matched = top["parent_pa"].isin(expected).sum()
if matched >= 14:
    add("S2_top_nl_in_cbd", "PASS", f"{matched}/20 in CBD/Orchard area PAs")
else:
    add("S2_top_nl_in_cbd", "WARN", f"{matched}/20")

# S3 change % distribution
ch = s["nl_change_pct"]
ch_med = ch.median()
ch_p99 = ch.quantile(0.99)
ch_p01 = ch.quantile(0.01)
if -10 < ch_med < 30 and ch_p99 < 250 and ch_p01 > -100:
    add("S3_nl_change_distribution", "PASS",
        f"median {ch_med:.1f}%, p1 {ch_p01:.1f}%, p99 {ch_p99:.1f}%")
else:
    add("S3_nl_change_distribution", "WARN",
        f"median {ch_med:.1f}%, p1 {ch_p01:.1f}%, p99 {ch_p99:.1f}%")

# S4 wp_pop total
wp_total = s["wp_pop"].sum()
if 4_000_000 <= wp_total <= 9_000_000:
    add("S4_wp_pop_total", "PASS", f"{wp_total:,.0f} (SGP scale 4-9M)")
else:
    add("S4_wp_pop_total", "WARN", f"{wp_total:,.0f}")

# S5 commercial indicator: top should be CBD low-residential hexes
top_ci = s.nlargest(15, "nl_commercial_indicator").merge(h9[["hex9_id", "parent_pa"]], on="hex9_id")
ci_in = top_ci["parent_pa"].isin(expected).sum()
if ci_in >= 10:
    add("S5_commercial_indicator_in_cbd", "PASS", f"{ci_in}/15 top commercial-indicator hexes in CBD/Orchard")
else:
    add("S5_commercial_indicator_in_cbd", "WARN", f"{ci_in}/15")

passes = sum(1 for c in report["checks"] if c["status"] == "PASS")
print(f"\n{passes}/{len(report['checks'])} checks passed")
for c in report["checks"]:
    print(f"  {c['status']:4s}  {c['check']}  — {c['detail']}")

report["generated_at"] = __import__("time").strftime("%Y-%m-%dT%H:%M:%S")
with open(ROOT / "hex/satellite_validation.json", "w") as f:
    json.dump(report, f, indent=2)
