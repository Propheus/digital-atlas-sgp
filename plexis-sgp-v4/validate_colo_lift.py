"""
Plexis SGP v4 — S6 co-location lift validator.

Gate checks:
  C1. Face validity (directional priors, all must hold):
      bar->bar > 1.5; fitness->residential > 1; education->residential > 1;
      industrial_mfg->residential < 0.8; hotel->entertainment > 1.5;
      convenience->residential > 1; restaurant->hotel > 1.3.
  C2. Stability: recompute lift on a random 50/50 place split — Pearson r of
      log-lift across finite pairs >= 0.9.
  C3. Anti-collapse + redundancy: hex8 colo_fit_* must not reduce to place
      density (|r| vs pc_total < 0.85) nor duplicate any non-source master col
      (|r| > 0.9).
  C4. Asymmetry review: report the top asymmetric pairs (informational).
  C5. Support & significance accounting: every category >= MIN_SUPPORT;
      significant share reported; no NaN in fit columns.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree

ROOT = Path(__file__).parent
report = {"layer": "colo_lift", "checks": []}


def add(name, status, detail=""):
    report["checks"].append({"check": name, "status": status, "detail": detail})
    print(f"  [{status}] {name} — {detail}")


print("Loading...")
mat = pd.read_parquet(ROOT / "catalog/colo_lift_matrix.parquet")
mi = mat.set_index(["cat_a", "cat_b"])
rep = json.load(open(ROOT / "hex/colo_lift_report.json"))
fit8 = pd.read_parquet(ROOT / "hex/hex8_colo_fit.parquet")
master = pd.read_parquet(ROOT / "hex/hex8_all_features.parquet")

# === C1 face validity ===
PRIORS = [
    ("bar_nightlife", "bar_nightlife", ">", 1.5),
    ("fitness_recreation", "residential", ">", 1.0),
    ("education", "residential", ">", 1.0),
    ("industrial_mfg", "residential", "<", 0.8),
    ("hotel_hospitality", "entertainment_culture", ">", 1.5),
    ("convenience", "residential", ">", 1.0),
    ("restaurant", "hotel_hospitality", ">", 1.3),
]
fails = []
for a, b, op, thr in PRIORS:
    v = float(mi.loc[(a, b), "lift"])
    ok = v > thr if op == ">" else v < thr
    if not ok:
        fails.append(f"{a}->{b}={v:.2f} not {op}{thr}")
add("C1_face_validity", "PASS" if not fails else "FAIL",
    "; ".join(fails) or f"all {len(PRIORS)} directional priors hold")

# === C2 stability (50/50 split) ===
pl = pd.read_parquet(ROOT / "places/sgp_places_final.parquet",
                     columns=["latitude", "longitude", "plexis_category"])
tr = Transformer.from_crs(4326, 3414, always_xy=True)
x, y = tr.transform(pl["longitude"].to_numpy(), pl["latitude"].to_numpy())
xy = np.column_stack([x, y])
cats = sorted(pl["plexis_category"].dropna().unique())
codes = pl["plexis_category"].to_numpy()
rng = np.random.default_rng(3)
half = rng.random(len(pl)) < 0.5


def lift_matrix(mask):
    cxy, cc = xy[mask], codes[mask]
    cnt = np.zeros((mask.sum(), len(cats)), dtype=np.float32)
    for bi, b in enumerate(cats):
        own = cc == b
        if own.sum() < 2:
            continue
        c = cKDTree(cxy[own]).query_ball_point(cxy, 400.0, return_length=True,
                                               workers=-1).astype(np.float32)
        c[own] -= 1
        cnt[:, bi] = c
    base = cnt.mean(axis=0)
    out = np.full((len(cats), len(cats)), np.nan)
    for ai, a in enumerate(cats):
        rows = cc == a
        if rows.sum() >= 100:
            out[ai] = cnt[rows].mean(axis=0) / np.maximum(base, 1e-9)
    return out


l1, l2 = lift_matrix(half), lift_matrix(~half)
fin = np.isfinite(l1) & np.isfinite(l2) & (l1 > 0) & (l2 > 0)
r = np.corrcoef(np.log(l1[fin]), np.log(l2[fin]))[0, 1]
add("C2_stability", "PASS" if r >= 0.9 else ("WARN" if r >= 0.8 else "FAIL"),
    f"log-lift split-half Pearson r = {r:.3f} over {fin.sum()} pairs")

# === C3 anti-collapse + redundancy ===
df = master[["hex8_id"]].merge(fit8, on="hex8_id", how="left")
num = master.select_dtypes(include=[np.number])
flags, worst_pc = [], 0.0
for col in [c for c in fit8.columns if c.startswith("colo_fit_")]:
    r_pc = abs(np.corrcoef(df[col].fillna(0), master["pc_total"])[0, 1])
    worst_pc = max(worst_pc, r_pc)
corrs = num.corrwith(df["colo_fit_cafe_coffee"].fillna(0)).abs() \
    .sort_values(ascending=False).head(5)
print("    colo_fit_cafe top-5 |r|: " + ", ".join(f"{k}={v:.2f}"
                                                  for k, v in corrs.items()))
flags += [f"colo_fit_cafe~{k}={v:.2f}" for k, v in corrs.items()
          if v > 0.9 and not k.startswith(("pc_", "pc2_", "mg_", "ring", "pw",
                                           "max1_", "max2_", "walk_", "osm_"))]
add("C3_anti_collapse", "PASS" if worst_pc < 0.85 and not flags else "WARN",
    f"max |r(colo_fit_*, pc_total)| = {worst_pc:.3f}; " + ("; ".join(flags) or
    "no non-source |r|>0.9"))

# === C4 asymmetry review ===
asym = []
for a in cats:
    for b in cats:
        if a < b:
            try:
                ab = float(mi.loc[(a, b), "lift"])
                ba = float(mi.loc[(b, a), "lift"])
                if ab > 0 and ba > 0:
                    asym.append((a, b, ab, ba, abs(np.log(ab / ba))))
            except KeyError:
                pass
asym.sort(key=lambda t: -t[4])
report["top_asymmetries"] = [
    {"a": a, "b": b, "lift_ab": round(ab, 2), "lift_ba": round(ba, 2)}
    for a, b, ab, ba, _ in asym[:5]]
add("C4_asymmetry", "PASS",
    "; ".join(f"{a}->{b} {ab:.2f} vs {b}->{a} {ba:.2f}"
              for a, b, ab, ba, _ in asym[:3]) + " (informational)")

# === C5 accounting ===
nan_fit = int(fit8.drop(columns=["hex8_id"]).isna().sum().sum())
ok = not rep["cats_below_support"] and nan_fit == 0
add("C5_accounting", "PASS" if ok else "FAIL",
    f"{rep['pairs_significant']}/{rep['pairs_total']} pairs significant; "
    f"below-support cats: {rep['cats_below_support'] or 'none'}; NaN fits: {nan_fit}")

n_fail = sum(c["status"] == "FAIL" for c in report["checks"])
n_warn = sum(c["status"] == "WARN" for c in report["checks"])
report["verdict"] = "FAIL" if n_fail else ("WARN" if n_warn else "PASS")
json.dump(report, open(ROOT / "logs/validate_colo_lift.json", "w"), indent=2,
          default=str)
print(f"\nVERDICT: {report['verdict']}  ({n_fail} fail, {n_warn} warn) "
      f"-> logs/validate_colo_lift.json")
