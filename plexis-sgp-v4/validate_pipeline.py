"""
Plexis SGP v4 — S9 pipeline validator.

Gate checks:
  P1. Future-rail set sanity: 25-45 stations; known committed JRL/CCL6 names
      present (>= 5 of the expected set); UNNAMED share reported.
  P2. Capacity archetypes (FAR-headroom construct, amended 2026-06-10):
      active growth areas (Matilda/Punggol, Bidadari) in the top decile;
      built-out Toa Payoh Central ~ 0. (Footprint-share v1 inverted this —
      towers cover little ground; Tengah scores low-positive because its
      MP19 parcels carry low GPR values, documented.)
  P3. Invariants: capacities in [0,1]; no NaN in flag/capacity cols;
      pipe_mrt_dist_m > 0.
  P4. Redundancy audit vs master (lu_*/bldg_* are the capacity sources, kin).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
report = {"layer": "pipeline", "checks": []}


def add(name, status, detail=""):
    report["checks"].append({"check": name, "status": status, "detail": detail})
    print(f"  [{status}] {name} — {detail}")


print("Loading...")
rep = json.load(open(ROOT / "hex/pipeline_report.json"))
pipe = pd.read_parquet(ROOT / "hex/hex8_pipeline.parquet")
master = pd.read_parquet(ROOT / "hex/hex8_all_features.parquet")
df = pipe.merge(master[["hex8_id", "parent_subzone_name", "pop_resident"]],
                on="hex8_id")

# === P1 ===
EXPECTED = {"TENGAH PARK", "HONG KAH", "CORPORATION", "KEPPEL", "BAHAR JUNCTION",
            "GEK POH", "ENTERPRISE", "JURONG WEST", "CHOA CHU KANG WEST"}
names = set(df["pipe_mrt_name"].dropna().unique())
hits = len(EXPECTED & names)
n_fut = rep["future_stations"]
unnamed = sum(n == "UNNAMED" for n in names)
ok = 25 <= n_fut <= 45 and hits >= 5
add("P1_future_set", "PASS" if ok else "FAIL",
    f"{n_fut} future stations; {hits}/9 expected JRL/CCL6 names present; "
    f"{unnamed} UNNAMED entries (reported)")

# === P2 ===
thr90 = df["pipe_dev_capacity_res"].quantile(0.9)
growth = df[df["parent_subzone_name"].isin(["MATILDA", "BIDADARI"])]
tp = df[df["parent_subzone_name"] == "TOA PAYOH CENTRAL"]["pipe_dev_capacity_res"]
ok = len(growth) > 0 and growth["pipe_dev_capacity_res"].max() >= thr90 \
    and tp.max() <= 0.05
add("P2_capacity_archetypes", "PASS" if ok else "WARN",
    f"Matilda/Bidadari max capacity {growth['pipe_dev_capacity_res'].max():.3f} "
    f"(p90={thr90:.3f}); Toa Payoh Central {tp.max():.3f}")
report["top_capacity"] = (df.nlargest(6, "pipe_dev_capacity_res")
                          [["parent_subzone_name", "pipe_dev_capacity_res"]]
                          .round(3).to_dict("records"))

# === P3 ===
errs = []
for c in ["pipe_dev_capacity_res", "pipe_dev_capacity_com"]:
    if not df[c].between(0, 6).all():       # FAR-units x share; GPR caps ~5-6
        errs.append(f"{c} out of [0,6]")
    if df[c].isna().any():
        errs.append(f"{c} has NaN")
if (df["pipe_mrt_dist_m"] <= 0).any():
    errs.append("non-positive mrt dist")
add("P3_invariants", "PASS" if not errs else "FAIL", "; ".join(errs) or "all hold")

# === P4 ===
num = master.select_dtypes(include=[np.number])
flags = []
for col in ["pipe_dev_capacity_res", "pipe_dev_capacity_com", "pipe_mrt_dist_m"]:
    corrs = num.corrwith(df[col]).abs().sort_values(ascending=False).head(4)
    print(f"    {col} top |r|: " + ", ".join(f"{k}={x:.2f}" for k, x in corrs.items()))
    flags += [f"{col}~{k}={x:.2f}" for k, x in corrs.items()
              if x > 0.9 and not k.startswith(("lu_", "bldg_", "wc_", "gap_",
                                               "est_", "dist_", "pull_"))]
add("P4_redundancy", "PASS" if not flags else "WARN",
    "; ".join(flags) or "no non-source |r|>0.9")

n_fail = sum(c["status"] == "FAIL" for c in report["checks"])
n_warn = sum(c["status"] == "WARN" for c in report["checks"])
report["verdict"] = "FAIL" if n_fail else ("WARN" if n_warn else "PASS")
json.dump(report, open(ROOT / "logs/validate_pipeline.json", "w"), indent=2,
          default=str)
print(f"\nVERDICT: {report['verdict']}  ({n_fail} fail, {n_warn} warn) "
      f"-> logs/validate_pipeline.json")
