"""
Plexis SGP v4 — road centrality validator.

Five checks:
  C1. Output coverage (hexes with centrality > 0)
  C2. Top betweenness hexes are in expected hub PAs (CBD, expressway interchanges)
  C3. PageRank distribution is non-degenerate (max/min ratio finite, not all equal)
  C4. Bridge count is positive (network has cut edges; some sub-region severance)
  C5. No infinite/nan values
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
c = pd.read_parquet(ROOT / "hex/hex9_road_centrality.parquet")
h9 = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
print(f"  shape: {c.shape}")

# C1 coverage
hexes_with = (c["centr_node_count"] > 0).sum()
pct = 100 * hexes_with / len(c)
if pct >= 50:
    add("C1_coverage", "PASS", f"{hexes_with}/{len(c)} ({pct:.0f}%) hexes have centrality")
else:
    add("C1_coverage", "WARN", f"{hexes_with}/{len(c)} ({pct:.0f}%) — expected major-road network ≥50% of hexes")

# C2 top betweenness hubs
top = c.nlargest(15, "centr_betweenness_max").merge(
    h9[["hex9_id", "parent_subzone_name", "parent_pa"]], on="hex9_id")
hub_pas = {"DOWNTOWN CORE", "MARINA SOUTH", "BUKIT MERAH", "QUEENSTOWN",
           "OUTRAM", "TANGLIN", "KALLANG", "GEYLANG", "TOA PAYOH",
           "BISHAN", "ANG MO KIO", "TAMPINES", "BEDOK", "WOODLANDS",
           "JURONG EAST", "JURONG WEST", "BUKIT TIMAH", "BUKIT BATOK",
           "PASIR RIS", "HOUGANG", "SERANGOON", "CHANGI", "MARINE PARADE",
           "ROCHOR", "NEWTON", "RIVER VALLEY", "CLEMENTI", "PIONEER",
           "BUKIT PANJANG", "CHOA CHU KANG", "PUNGGOL", "SENGKANG",
           "SEMBAWANG", "YISHUN", "TENGAH", "SUNGEI KADUT", "MUSEUM",
           "SINGAPORE RIVER", "NOVENA"}
hub_count = top["parent_pa"].isin(hub_pas).sum()
if hub_count >= 12:
    add("C2_top_betweenness_in_hubs", "PASS", f"{hub_count}/15 in known hub PAs")
else:
    add("C2_top_betweenness_in_hubs", "WARN", f"{hub_count}/15 in hubs")

# C3 PageRank non-degenerate
pr_max = c["centr_pagerank_max"].max()
pr_min_pos = c[c["centr_pagerank_max"] > 0]["centr_pagerank_max"].min() if (c["centr_pagerank_max"] > 0).any() else 0
ratio = pr_max / pr_min_pos if pr_min_pos > 0 else 0
if 5 <= ratio <= 1e6:
    add("C3_pagerank_non_degenerate", "PASS", f"max/min ratio = {ratio:.1f}")
else:
    add("C3_pagerank_non_degenerate", "WARN", f"ratio = {ratio:.2g}")

# C4 bridges
bridge_total = c["centr_bridge_count"].sum()
if bridge_total > 0:
    add("C4_bridges_present", "PASS", f"{int(bridge_total)} bridge endpoints across {(c['centr_bridge_count']>0).sum()} hexes")
else:
    add("C4_bridges_present", "WARN", "no bridges detected (network too dense?)")

# C5 no inf/nan
for col in c.columns:
    if c[col].dtype.kind in "if":
        n_bad = c[col].replace([np.inf, -np.inf], np.nan).isna().sum()
        if n_bad > 0:
            add("C5_no_inf_nan", "FAIL", f"{col} has {n_bad} inf/nan")
            break
else:
    add("C5_no_inf_nan", "PASS", "no inf/nan values across all numeric cols")

passes = sum(1 for c in report["checks"] if c["status"] == "PASS")
print(f"\n{passes}/{len(report['checks'])} checks passed")
for ck in report["checks"]:
    print(f"  {ck['status']:4s}  {ck['check']}  — {ck['detail']}")

report["generated_at"] = __import__("time").strftime("%Y-%m-%dT%H:%M:%S")
with open(ROOT / "hex/road_centrality_validation.json", "w") as f:
    json.dump(report, f, indent=2)
