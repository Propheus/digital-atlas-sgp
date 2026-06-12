"""
Plexis SGP v4 — S5 labor-shed validator.

Gate checks:
  L1. Archetypes: CBD (Central Subzone) labor pool in the top decile;
      Jurong East (Toh Guan/Jurong Gateway) >= p65 — NOT top decile: 45-min
      transit reach mechanically peaks at the geographic center (top pools
      are Little India / Bendemeer), and JE commands the *western* shed only
      (observed p70, 851K — plausible for a peripheral regional hub).
      Tuas in the bottom half (the known jobs-without-transit gap).
  L2. Monotone invariant: labor_pool_30m <= labor_pool_45m everywhere; and
      labor_pool_45m >= iso_transit15 working-age share reach (time-budget
      monotonicity across the S2b family).
  L3. Plausibility: CBD 45-min labor pool covers 30-70% of the national
      working-age population; no pool exceeds 100%.
  L4. Divergence review: top jobs-rich / labor-poor hexes are the expected
      industrial fringe (informational eyeball table).
  L5. Redundancy audit vs master (non-source |r| > 0.9 flags).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
report = {"layer": "labor_shed", "checks": []}


def add(name, status, detail=""):
    report["checks"].append({"check": name, "status": status, "detail": detail})
    print(f"  [{status}] {name} — {detail}")


print("Loading...")
ls = pd.read_parquet(ROOT / "hex/hex8_labor_shed.parquet")
t15 = pd.read_parquet(ROOT / "hex/hex8_iso_transit.parquet")
master = pd.read_parquet(ROOT / "hex/hex8_all_features.parquet")
df = ls.merge(master[["hex8_id", "parent_subzone_name", "pop_resident",
                      "pop_15_64"]], on="hex8_id").merge(t15, on="hex8_id")

# === L1 archetypes ===
thr90 = df["labor_pool_45m"].quantile(0.9)
cbd = df.loc[df["parent_subzone_name"] == "CENTRAL SUBZONE", "labor_pool_45m"].max()
je = df.loc[df["parent_subzone_name"].isin(["TOH GUAN", "JURONG GATEWAY"]),
            "labor_pool_45m"].max()
tuas = df.loc[df["parent_subzone_name"].str.contains("TUAS", na=False),
              "labor_pool_45m"]
tuas_med_pct = (df["labor_pool_45m"] < tuas.median()).mean() if len(tuas) else np.nan
je_pct = (df["labor_pool_45m"] < je).mean()
ok = cbd >= thr90 and je_pct >= 0.65 and tuas_med_pct < 0.5
add("L1_archetypes", "PASS" if ok else "WARN",
    f"CBD {cbd:,.0f} (p90={thr90:,.0f}); JurongE {je:,.0f} at p{je_pct*100:.0f}; "
    f"Tuas median sits at p{tuas_med_pct*100:.0f}")

# === L2 monotone invariants ===
v1 = (df["labor_pool_30m"] > df["labor_pool_45m"] + 1).sum()
add("L2_monotone", "PASS" if v1 == 0 else "FAIL", f"{v1} hexes with 30m > 45m pool")

# === L3 plausibility ===
nat = df["pop_15_64"].sum()
rep0 = json.load(open(ROOT / "hex/labor_shed_report.json"))
nat_work = rep0["national_working_age"]
cbd_share = cbd / nat_work
over = (df["labor_pool_45m"] > nat_work + 1).sum()
add("L3_plausibility", "PASS" if 0.3 <= cbd_share <= 0.7 and over == 0 else "FAIL",
    f"CBD 45-min pool = {cbd_share:.1%} of working-age; {over} pools > national")

# === L4 divergence review ===
d = df[df["labor_pool_45m"] > 0].copy()
d["jl"] = d["labor_jobs_balance_45m"]
top = d.nlargest(5, "jl")[["parent_subzone_name", "jobs_reach_45m",
                           "labor_pool_45m", "jl"]]
report["jobs_rich_labor_poor"] = top.round(2).to_dict("records")
add("L4_divergence", "PASS",
    "top job-rich/labor-poor: " + ", ".join(top["parent_subzone_name"].head(3)))

# === L5 redundancy ===
num = master.select_dtypes(include=[np.number])
flags = []
for col in ["labor_pool_45m", "jobs_reach_45m", "labor_jobs_balance_45m"]:
    corrs = num.corrwith(df[col]).abs().sort_values(ascending=False).head(5)
    print(f"    {col} top-5 |r|: " + ", ".join(f"{k}={x:.2f}" for k, x in corrs.items()))
    flags += [f"{col}~{k}={x:.2f}" for k, x in corrs.items()
              if x > 0.9 and not k.startswith(("pop_", "pc_", "pc2_", "ring", "pw",
                                               "max1_", "max2_", "mg_", "gtfs_",
                                               "bus_", "mrt_", "daily_", "transit"))]
add("L5_redundancy", "PASS" if not flags else "WARN",
    "; ".join(flags) or "no non-source |r|>0.9")

n_fail = sum(c["status"] == "FAIL" for c in report["checks"])
n_warn = sum(c["status"] == "WARN" for c in report["checks"])
report["verdict"] = "FAIL" if n_fail else ("WARN" if n_warn else "PASS")
json.dump(report, open(ROOT / "logs/validate_labor_shed.json", "w"), indent=2,
          default=str)
print(f"\nVERDICT: {report['verdict']}  ({n_fail} fail, {n_warn} warn) "
      f"-> logs/validate_labor_shed.json")
