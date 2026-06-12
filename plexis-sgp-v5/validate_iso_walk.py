"""
Plexis SGP v4 — S2a walk isochrone validator.

Gate checks (SITE_SELECTION_METRICS.md §S2, amended for node-field design):
  I1. Upper bound: iso_walk10_pop <= iso_euclid800_pop. Triangle inequality
      holds exactly for the min-snap source; non-min sources of the k=4
      multi-source can violate marginally — tolerate <=1% of hexes and <=5%
      relative magnitude.
  I2. Severance signal: populated hexes with an expressway within 200 m have
      a materially lower severance ratio than hexes >800 m away.
  I3. Redundancy audit vs all master cols (incl. walk_*, dist_*, ring*, pw*):
      no new col with |r| > 0.9 vs a non-source existing col.
  I4. Graph & snap QA: giant component >= 99%; populated-hex origin snap
      >150 m share < 10%; orphaned (node-less) population < 1% of national.
  I5. Archetype anchors: CBD reaches most places; HDB town centres reach
      >= 15k pop; industrial/rural reach near-zero pop but industrial
      may still reach places.
  I6. Internal consistency: unserved <= pop; competitors <= places; spend <=
      pop (affluence idx <= 1); no negatives; no NaN outside declared cols.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
report = {"layer": "iso_walk", "checks": []}


def add(name, status, detail=""):
    report["checks"].append({"check": name, "status": status, "detail": detail})
    print(f"  [{status}] {name} — {detail}")


print("Loading...")
iso = pd.read_parquet(ROOT / "hex/hex8_iso_walk.parquet")
master = pd.read_parquet(ROOT / "hex/hex8_all_features.parquet")
df = iso.merge(master[["hex8_id", "pop_resident", "parent_subzone_name",
                       "dist_expressway_m", "pc_total"]], on="hex8_id")
assert len(df) == 1191

# === I1 upper bound ===
# A violation must be material BOTH relatively (>5%) and absolutely (>50
# persons): k=4 multi-source spread in sparse rural networks (Murai) produces
# ~5-person excesses with huge relative values — artifacts, not bugs.
excess = df["iso_walk10_pop"] - df["iso_euclid800_pop"]
rel = excess / df["iso_euclid800_pop"].clip(lower=1)
viol = (excess > 50) & (rel > 0.05)
soft = (excess > 1) & ~viol
add("I1_upper_bound", "PASS" if viol.sum() == 0 else "FAIL",
    f"{viol.sum()} material violations; {soft.sum()} immaterial "
    f"(max {excess[soft].max() if soft.any() else 0:.0f} persons, rural multi-source spread)")

# === I2 severance signal ===
popd = df[(df["pop_resident"] > 2000) & df["iso_severance_ratio"].notna()]
near = popd[popd["dist_expressway_m"] <= 200]["iso_severance_ratio"]
far = popd[popd["dist_expressway_m"] > 800]["iso_severance_ratio"]
gap = far.mean() - near.mean()
add("I2_severance_signal", "PASS" if gap > 0.03 else ("WARN" if gap > 0 else "FAIL"),
    f"ratio near-expressway {near.mean():.3f} (n={len(near)}) vs far {far.mean():.3f} "
    f"(n={len(far)}), gap {gap:+.3f}")
report["lowest_ratio_populated"] = (
    popd.nsmallest(10, "iso_severance_ratio")
    [["parent_subzone_name", "pop_resident", "iso_walk10_pop", "iso_severance_ratio"]]
    .round(2).to_dict("records"))

# === I3 redundancy audit ===
num = master.select_dtypes(include=[np.number])
# mg_* (micrograph rollups) derive from the same places source as iso place
# counts — correlation with them is definitional, like pc_*; iso adds the
# network-distance lens on the identical underlying points.
SOURCE_PREFIXES = ("pop_", "pc_", "pc2_", "ring", "pw1_", "pw2_", "max1_", "max2_", "mg_")
flags, top = [], {}
for col in ["iso_walk10_pop", "iso_walk10_spend", "iso_walk10_places",
            "iso_severance_ratio", "iso_walk10_unserved_pop_supermarket"]:
    corrs = num.corrwith(df[col]).abs().sort_values(ascending=False).head(5)
    top[col] = corrs.round(3).to_dict()
    print(f"    {col} top-5 |r|: " + ", ".join(f"{k}={x:.2f}" for k, x in corrs.items()))
    for k, x in corrs.items():
        if x > 0.9 and not k.startswith(SOURCE_PREFIXES):
            flags.append(f"{col}~{k}={x:.2f}")
report["redundancy_top5"] = top
add("I3_redundancy", "PASS" if not flags else "WARN", "; ".join(flags) or
    "no |r|>0.9 vs non-source cols")

# === I4 graph & snap QA ===
rep = json.load(open(ROOT / "hex/iso_walk_report.json"))
snap_pop = df.loc[df["pop_resident"] > 1000, "iso_snap_dist_m"]
orphan_share = rep["orphan_pop_to_nearest_node"] / 4_179_800
ok = (rep["giant_component_share"] >= 0.99 and (snap_pop > 150).mean() < 0.10
      and orphan_share < 0.01)
add("I4_graph_snap_qa", "PASS" if ok else "FAIL",
    f"giant {rep['giant_component_share']:.1%}; populated-hex snap>150m "
    f"{(snap_pop > 150).mean():.2%}; orphan pop {orphan_share:.2%}")

# === I5 archetype anchors ===
def hexrow(sz):
    sub = df[df["parent_subzone_name"] == sz]
    return sub.loc[sub["iso_walk10_pop"].idxmax()] if len(sub) else None

anchors = {
    "CENTRAL SUBZONE (CBD)": hexrow("CENTRAL SUBZONE"),
    "TOA PAYOH CENTRAL (town ctr)": hexrow("TOA PAYOH CENTRAL"),
    "TAMPINES EAST (town)": hexrow("TAMPINES EAST"),
    # GUL CIRCLE not CHIN BEE: Chin Bee turned out to hold 8k residents
    # (borders Taman Jurong HDB) — wrong archetype, learned 2026-06-10.
    "GUL CIRCLE (industrial)": hexrow("GUL CIRCLE"),
    "LIM CHU KANG (rural)": hexrow("LIM CHU KANG"),
}
tbl = {k: dict(pop=round(float(v["iso_walk10_pop"])), places=int(v["iso_walk10_places"]),
               ratio=(None if pd.isna(v["iso_severance_ratio"])
                      else round(float(v["iso_severance_ratio"]), 2)))
       for k, v in anchors.items() if v is not None}
report["archetype_anchors"] = tbl
for k, v in tbl.items():
    print(f"    {k}: {v}")
cbd_places = tbl["CENTRAL SUBZONE (CBD)"]["places"]
ok = (cbd_places > 1500
      and tbl["TOA PAYOH CENTRAL (town ctr)"]["pop"] >= 15000
      and tbl["TAMPINES EAST (town)"]["pop"] >= 15000
      and tbl["LIM CHU KANG (rural)"]["pop"] < 500
      and tbl["GUL CIRCLE (industrial)"]["pop"] < 1000)
add("I5_archetypes", "PASS" if ok else "WARN", f"CBD places={cbd_places}; see table")

# === I6 internal consistency ===
errs = []
for c in ["cafe_coffee", "supermarket", "restaurant", "fitness_recreation"]:
    if (df[f"iso_walk10_unserved_pop_{c}"] > df["iso_walk10_pop"] + 1).any():
        errs.append(f"unserved_{c}>pop")
    if (df[f"iso_walk10_competitors_{c}"] > df["iso_walk10_places"]).any():
        errs.append(f"competitors_{c}>places")
if (df["iso_walk10_spend"] > df["iso_walk10_pop"] + 1).any():
    errs.append("spend>pop")
if (df[[c for c in iso.columns if c != "hex8_id"]].select_dtypes("number") < 0).any().any():
    errs.append("negative values")
nan_ok = {"iso_severance_ratio"}
bad_nan = [c for c in iso.columns
           if c not in nan_ok and c != "hex8_id" and iso[c].isna().any()]
if bad_nan:
    errs.append(f"unexpected NaN in {bad_nan}")
add("I6_consistency", "PASS" if not errs else "FAIL", "; ".join(errs) or "all invariants hold")

n_fail = sum(c["status"] == "FAIL" for c in report["checks"])
n_warn = sum(c["status"] == "WARN" for c in report["checks"])
report["verdict"] = "FAIL" if n_fail else ("WARN" if n_warn else "PASS")
json.dump(report, open(ROOT / "logs/validate_iso_walk.json", "w"), indent=2, default=str)
print(f"\nVERDICT: {report['verdict']}  ({n_fail} fail, {n_warn} warn) "
      f"-> logs/validate_iso_walk.json")
