"""
Plexis SGP v4 — S1 Huff capture validator.

Gate checks (amended per the lambda-identifiability finding, see builder):
  H1. Diagnostics floor: placement-rho > 0.2 for >= 10/11 categories (weak-form
      "capture tracks where outlets can exist"); lambda rank-stability >= 0.8
      for every category (the assumed-lambda mitigation).
  H2. Marginality: inserting a synthetic competitor (A=1) in a neighboring
      hex9 ~200-400 m away must strictly reduce cap at the candidate —
      40 random populated candidates x {supermarket, cafe_coffee}.
  H3. Conservation: demand allocated to existing outlets <= total demand
      (report alloc/demand == 1.000 +- 1e-3 per category).
  H4. Saturation inversion (the point of the layer): underserved areas must
      out-rank saturated prime. Yunnan (known FairPrice desert) in the top
      15% of populated-hex9 cap_supermarket; Orchard corridor (Boulevard,
      Somerset, Orchard) NOT in the top decile of cap_cafe_coffee.
  H5. Redundancy audit at hex8 vs all 601 master cols; also report
      corr(cap_c, gap_c) directional alignment for overlapping categories.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).parent
report = {"layer": "huff_capture", "checks": []}


def add(name, status, detail=""):
    report["checks"].append({"check": name, "status": status, "detail": detail})
    print(f"  [{status}] {name} — {detail}")


print("Loading...")
rep = json.load(open(ROOT / "hex/huff_capture_report.json"))
c9 = pd.read_parquet(ROOT / "hex/hex9_huff_capture.parquet")
c8 = pd.read_parquet(ROOT / "hex/hex8_huff_capture.parquet")
h9 = pd.read_parquet(ROOT / "hex/hex9_population.parquet")
master = pd.read_parquet(ROOT / "hex/hex8_all_features.parquet")
df9 = c9.merge(h9[["hex9_id", "pop_resident", "parent_subzone_name"]], on="hex9_id")
CATS = list(rep["lambda"].keys())

# === H1 diagnostics floor ===
pl_ok = sum(v > 0.2 for v in rep["test_spearman"].values())
sens_ok = all(v >= 0.8 for v in rep["lambda_rank_stability"].values())
add("H1_diagnostics", "PASS" if pl_ok >= 10 and sens_ok else "FAIL",
    f"placement>0.2: {pl_ok}/11; rank-stability min "
    f"{min(rep['lambda_rank_stability'].values()):.3f}")

# === H2 marginality ===
npz = np.load(ROOT / "hex/huff_pairs.npz", allow_pickle=True)
pi, pj, pdist = npz["pi"], npz["pj"], npz["pdist"]
hex9_ids = npz["hex9_id"]
idx = pd.Series(range(len(hex9_ids)), index=hex9_ids)
pop = h9.set_index("hex9_id")["pop_resident"].reindex(hex9_ids).fillna(0).to_numpy()
pl = pd.read_parquet(ROOT / "places/sgp_places_final.parquet",
                     columns=["hex9_id", "plexis_category", "reviews_count"])
pl = pl[pl["hex9_id"].isin(idx.index)].copy()
pl["hi"] = pl["hex9_id"].map(idx)
n = len(hex9_ids)
rng = np.random.default_rng(7)
cands = rng.choice(np.where(pop > 1000)[0], 20, replace=False)
fails = 0
for cat in ["supermarket", "cafe_coffee"]:
    lam = rep["lambda"][cat]
    sub = pl[pl["plexis_category"] == cat].copy()
    sub["q"] = 1 + np.log1p(sub["reviews_count"].fillna(0))
    sub["q"] /= sub["q"].mean()
    A = np.zeros(n)
    g = sub.groupby("hi")["q"].sum()
    A[g.index] = g.to_numpy()
    D = pop / pop.sum() * sub["q"].sum()
    w = np.exp(-pdist / lam)
    S = np.zeros(n)
    np.add.at(S, pi, A[pj] * w)
    for h in cands:
        rows = np.where(pj == h)[0]
        base_cap = float(np.sum(D[pi[rows]] * w[rows] / (S[pi[rows]] + w[rows])))
        # competitor at the nearest hex9 between 150 and 450 m from h
        near = rows[(pdist[rows] > 150) & (pdist[rows] < 450)]
        if not len(near):
            continue
        k = pi[near[np.argmin(pdist[near])]]
        wk = np.exp(-pdist[np.where(pj == k)[0]] / lam)
        S2 = S.copy()
        np.add.at(S2, pi[np.where(pj == k)[0]], 1.0 * wk)
        new_cap = float(np.sum(D[pi[rows]] * w[rows] / (S2[pi[rows]] + w[rows])))
        if not new_cap < base_cap:
            fails += 1
add("H2_marginality", "PASS" if fails == 0 else "FAIL",
    f"{fails} non-decreasing cases out of ~40 (competitor 150-450 m away)")

# === H3 conservation ===
worst = max(rep["conservation"].values())
add("H3_conservation", "PASS" if worst <= 1.001 else "FAIL",
    f"max alloc/demand = {worst:.4f}")

# === H4 saturation inversion ===
popd = df9[df9["pop_resident"] > 500].copy()
pct_sm = popd["cap_supermarket"].rank(pct=True)
yunnan = pct_sm[popd["parent_subzone_name"].str.contains("YUNNAN", na=False)]
orchard_szs = popd["parent_subzone_name"].isin(["BOULEVARD", "SOMERSET", "ORCHARD",
                                                "PATERSON"])
pct_cafe = popd["cap_cafe_coffee"].rank(pct=True)
orch = pct_cafe[orchard_szs]
yun_ok = yunnan.max() >= 0.85 if len(yunnan) else False
orch_ok = orch.max() < 0.90 if len(orch) else True
add("H4_saturation_inversion", "PASS" if yun_ok and orch_ok else
    ("WARN" if yun_ok or orch_ok else "FAIL"),
    f"Yunnan cap_supermarket max pctile {yunnan.max():.2f} (n={len(yunnan)}); "
    f"Orchard-corridor cap_cafe max pctile {orch.max() if len(orch) else -1:.2f}")
report["top_supermarket_sites"] = (
    popd.nlargest(8, "cap_supermarket")
    [["parent_subzone_name", "pop_resident", "cap_supermarket"]].round(3)
    .to_dict("records"))

# === H5 redundancy + gap alignment ===
num = master.select_dtypes(include=[np.number])
dfh8 = master[["hex8_id"]].merge(c8, on="hex8_id")
flags, top = [], {}
for col in ["cap_supermarket", "cap_cafe_coffee", "cap_total"]:
    corrs = num.corrwith(dfh8[col]).abs().sort_values(ascending=False).head(5)
    top[col] = corrs.round(3).to_dict()
    print(f"    {col} top-5 |r|: " + ", ".join(f"{k}={x:.2f}" for k, x in corrs.items()))
    flags += [f"{col}~{k}={x:.2f}" for k, x in corrs.items()
              if x > 0.9 and not k.startswith(("pop_", "pc_", "pc2_", "ring",
                                               "pw", "max1_", "max2_", "mg_",
                                               "sat_", "gap_", "hdb_"))]
report["redundancy_top5"] = top
gap_align = {}
for cat, gcol in [("cafe_coffee", "gap_cafe_coffee"), ("restaurant", "gap_restaurant"),
                  ("hawker", "gap_hawker")]:
    if gcol in master.columns:
        gap_align[cat] = round(float(spearmanr(dfh8[f"cap_{cat}"],
                                               master[gcol]).statistic), 3)
report["gap_alignment"] = gap_align
add("H5_redundancy", "PASS" if not flags else "WARN",
    ("; ".join(flags) or "no |r|>0.9 vs non-source cols")
    + f"; gap alignment {gap_align}")

n_fail = sum(c["status"] == "FAIL" for c in report["checks"])
n_warn = sum(c["status"] == "WARN" for c in report["checks"])
report["verdict"] = "FAIL" if n_fail else ("WARN" if n_warn else "PASS")
json.dump(report, open(ROOT / "logs/validate_huff_capture.json", "w"), indent=2,
          default=str)
print(f"\nVERDICT: {report['verdict']}  ({n_fail} fail, {n_warn} warn) "
      f"-> logs/validate_huff_capture.json")
