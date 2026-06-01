"""
Plexis SGP v4 — place_composition validator.

P1. pc_total conserved (sum across hex9, hex8 == 190,591; subzone == 190,578)
P2. hex9 → hex8 conservation (pc_total per parent_hex8 matches hex8 directly)
P3. Top 10 hex9 by pc_total are CBD / mall / MRT-dense PAs
P4. Top 10 hex9 by pc_magnets are landmark hexes
P5. pc_diversity in [0, log(24)≈3.18]
P6. Top-10 most-populous subzones — at least half should be dominant=residential
"""
import json, math, time
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent
report = {"checks": []}


def add(name, status, detail=""):
    report["checks"].append({"check": name, "status": status, "detail": detail})
    print(f"  [{status}] {name} — {detail}")


print("Loading...")
h9 = pd.read_parquet(ROOT / "hex/hex9_place_composition.parquet")
h8 = pd.read_parquet(ROOT / "hex/hex8_place_composition.parquet")
sz = pd.read_parquet(ROOT / "hex/subzone_place_composition.parquet")
h9_uni = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
places = pd.read_parquet(ROOT / "places/sgp_places_final.parquet")

# P1 — totals conserved within tolerance.
# Some places are at coords whose h3 cell is outside our SGP hex universe
# (32/16 places at hex9/hex8 — boundary edge effects). Tolerate ≤50 drift.
total_in = len(places)
h9_total = int(h9["pc_total"].sum())
h8_total = int(h8["pc_total"].sum())
sz_total = int(sz["pc_total"].sum())
h9_drift = total_in - h9_total
h8_drift = total_in - h8_total
sz_drift = total_in - sz_total
TOL = 50
if h9_drift <= TOL and h8_drift <= TOL and sz_drift <= TOL:
    add("P1_totals_conserved", "PASS",
        f"hex9={h9_total} (drift {h9_drift}) hex8={h8_total} (drift {h8_drift}) sz={sz_total} (drift {sz_drift})")
else:
    add("P1_totals_conserved", "FAIL",
        f"hex9_drift={h9_drift} hex8_drift={h8_drift} sz_drift={sz_drift} (tol {TOL})")

# P2 hex9 → hex8 conservation
h9wp = h9.merge(h9_uni[["hex9_id","parent_hex8"]], on="hex9_id")
rolled = h9wp.groupby("parent_hex8")["pc_total"].sum().reset_index().rename(columns={"parent_hex8":"hex8_id"})
m = h8[["hex8_id","pc_total"]].merge(rolled, on="hex8_id", suffixes=("_direct","_rolled"))
diff = (m["pc_total_direct"] - m["pc_total_rolled"]).abs().sum()
if diff == 0:
    add("P2_hex9_to_hex8_conservation", "PASS", "exact match")
else:
    add("P2_hex9_to_hex8_conservation", "FAIL", f"abs diff sum: {diff}")

# P3 top hex9 by pc_total
hubs = {"DOWNTOWN CORE","ORCHARD","ROCHOR","BUGIS","OUTRAM","MARINA SOUTH","TANGLIN",
        "RIVER VALLEY","MUSEUM","NEWTON","TOA PAYOH","NOVENA","JURONG EAST","QUEENSTOWN",
        "BISHAN","ANG MO KIO","BEDOK","TAMPINES","GEYLANG","KALLANG","CLEMENTI",
        "SINGAPORE RIVER","MARINA EAST"}
top = h9.nlargest(10, "pc_total").merge(h9_uni[["hex9_id","parent_pa","parent_subzone_name"]], on="hex9_id")
hits = top["parent_pa"].isin(hubs).sum()
if hits >= 7:
    add("P3_top_pc_total_in_hubs", "PASS", f"{hits}/10 in known activity hubs")
else:
    add("P3_top_pc_total_in_hubs", "WARN", f"{hits}/10 — top: " + ", ".join(top["parent_pa"].head(5).tolist()))

# P4 top by magnets
top_m = h9.nlargest(10, "pc_magnets").merge(h9_uni[["hex9_id","parent_pa"]], on="hex9_id")
hits_m = top_m["parent_pa"].isin(hubs).sum()
if hits_m >= 6:
    add("P4_top_magnets_in_hubs", "PASS", f"{hits_m}/10 in hubs")
else:
    add("P4_top_magnets_in_hubs", "WARN", f"{hits_m}/10")

# P5 diversity bounds
maxh = math.log(24)
ok = ((h9["pc_diversity"] >= 0) & (h9["pc_diversity"] <= maxh + 0.01)).all()
if ok:
    add("P5_diversity_bounds", "PASS", f"all in [0, {maxh:.3f}]; max={h9['pc_diversity'].max():.3f}")
else:
    add("P5_diversity_bounds", "FAIL", "out of bounds")

# P6 dominant category for top-pop subzones
pop = pd.read_parquet(ROOT / "hex/subzone_population.parquet")
top_pop = pop.nlargest(10, "pop_resident")[["subzone_c","pop_resident"]]
m = top_pop.merge(sz[["subzone_c","pc_dominant_category"]], on="subzone_c", how="left")
res_share = (m["pc_dominant_category"] == "residential").sum()
if res_share >= 5:
    add("P6_top_pop_subzones_residential", "PASS", f"{res_share}/10 dominant=residential")
else:
    add("P6_top_pop_subzones_residential", "WARN",
        f"{res_share}/10 — actuals: " + ", ".join(m["pc_dominant_category"].head(5).tolist()))

passes = sum(1 for c in report["checks"] if c["status"] == "PASS")
print(f"\n{passes}/{len(report['checks'])} checks passed")
for c in report["checks"]:
    print(f"  {c['status']:4s}  {c['check']}  — {c['detail']}")

report["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
with open(ROOT / "hex/place_composition_validation.json", "w") as f:
    json.dump(report, f, indent=2)
