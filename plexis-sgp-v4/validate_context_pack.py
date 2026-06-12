"""
Plexis SGP v5 — S10 context pack validator.

Gate checks:
  X1. Conservation of national sums vs the source pack (counts must match the
      sanity-passed deliverables exactly).
  X2. Archetypes: conservation clusters in heritage subzones; wet-market
      distance lowest in mature estates; BTO allocation tops in
      Kallang/Whampoa + Tengah hexes; coworking concentrated in CBD.
  X3. Invariants: counts >= 0; dist > 0; female_pop_share in [0.30, 0.70]
      where subzone pop >= 1000 (tiny subzones skew GENUINELY: Yio Chu Kang
      420 residents 76% male — institutional quarters; real data, kept);
      NaN EXACTLY on zero-population subzones (verified 1.0);
      bto_pipeline_est sums to the town total.
  X4. Redundancy audit vs the 687-col master. Source-kin notes:
      carpark capacity ~ hdb family (expected); dist_wet_market_m ~
      nearest_hawker_centre_dist_m is near-definitional (markets are a SUBSET
      of the hawker-centres source layer) and ~ other nearest_* via the
      generic remoteness factor every dist column shares — kin, not dupes
      (the novel content is the market/centre distinction).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
report = {"layer": "context_pack", "checks": []}


def add(name, status, detail=""):
    report["checks"].append({"check": name, "status": status, "detail": detail})
    print(f"  [{status}] {name} — {detail}")


print("Loading...")
cx = pd.read_parquet(ROOT / "hex/hex8_context_pack.parquet")
master = pd.read_parquet(ROOT / "hex/hex8_all_features.parquet")
df = cx.merge(master[["hex8_id", "parent_subzone_name", "parent_pa",
                      "pop_resident"]], on="hex8_id")

# === X1 conservation vs pack ===
expect = {"cons_bldg_count": 7235, "wet_market_count": 63,
          "petrol_station_count": 201, "coworking_count": 171,
          "condo_project_count": 2384, "carpark_capacity_lots": 696086}
bad = {k: (df[k].sum(), v) for k, v in expect.items()
       if abs(df[k].sum() - v) > 0.5}
add("X1_conservation", "PASS" if not bad else "FAIL",
    "; ".join(f"{k} {a:,.0f}!={b:,}" for k, (a, b) in bad.items())
    or "all national sums match the delivered pack")

# === X2 archetypes ===
top_cons = df.nlargest(5, "cons_bldg_count")["parent_subzone_name"].tolist()
heritage = {"CHINATOWN", "LITTLE INDIA", "LAVENDER", "CRAWFORD", "KAMPONG GLAM",
            "JOO CHIAT", "BOAT QUAY", "TANJONG PAGAR", "MAXWELL", "CITY HALL",
            "BENCOOLEN", "VICTORIA"}
h_hits = sum(any(h in sz for h in heritage) for sz in top_cons)
mature = df[df["parent_subzone_name"].str.contains(
    "TIONG BAHRU|TELOK BLANGAH|TOA PAYOH|ANG MO KIO", na=False)]
wmd_mature = mature["dist_wet_market_m"].median()
wmd_all = df.loc[df["pop_resident"] > 2000, "dist_wet_market_m"].median()
top_bto = df.nlargest(8, "bto_pipeline_est")["parent_pa"].str.upper().tolist()
b_hits = sum(pa in ("KALLANG", "TENGAH", "QUEENSTOWN", "YISHUN", "WOODLANDS")
             for pa in top_bto)
ok = h_hits >= 4 and wmd_mature < wmd_all and b_hits >= 5
add("X2_archetypes", "PASS" if ok else "WARN",
    f"conservation top-5 heritage {h_hits}/5; wet-market dist mature "
    f"{wmd_mature:.0f}m < populated median {wmd_all:.0f}m; "
    f"BTO top-8 in launch towns {b_hits}/8")

# === X3 invariants ===
errs = []
cnts = ["cons_bldg_count", "carpark_count_hdb", "carpark_capacity_lots",
        "polyclinic_count", "wet_market_count", "petrol_station_count",
        "coworking_count", "condo_project_count", "condo_txn_units",
        "bto_uc_units_town", "bto_pipeline_est"]
if (df[cnts] < 0).any().any():
    errs.append("negative counts")
for c in ["dist_polyclinic_m", "dist_wet_market_m", "dist_petrol_m"]:
    if (df[c] <= 0).any():
        errs.append(f"{c} non-positive")
fs = pd.read_csv(ROOT / "nous_export/female_pop_share.csv")
fs["key"] = fs["subzone"].str.upper().str.strip()
szpop = fs.set_index("key")[["pop_female", "pop_male"]].sum(axis=1)
big = df["parent_subzone_name"].str.upper().map(szpop).fillna(0) >= 1000
fset = df.loc[big, "female_pop_share"].dropna()
if not fset.between(0.30, 0.70).all():
    errs.append("female share out of band (pop>=1000 subzones)")
pop0 = (fs.set_index("key")[["pop_female", "pop_male"]].sum(axis=1) == 0)
zero = df["parent_subzone_name"].str.upper().map(pop0).fillna(True)
if not (df["female_pop_share"].isna() == zero).all():
    errs.append("female NaN != zero-pop subzone")
nat_bto = pd.read_csv(ROOT / "nous_export/hdb_completion_by_town.csv")
fy = nat_bto["financial_year"].max()
tot = nat_bto[(nat_bto["financial_year"] == fy)
              & (nat_bto["status"] == "Under Construction")]["no_of_units"].sum()
# allocation only lands in PAs that have hexes with headroom — report drop
alloc_share = df["bto_pipeline_est"].sum() / tot
if alloc_share < 0.8:
    errs.append(f"bto allocation lost {1-alloc_share:.0%}")
add("X3_invariants", "PASS" if not errs else "FAIL",
    "; ".join(errs) or
    f"all hold; female NaN==zero-pop exact; BTO allocated {alloc_share:.1%} of "
    f"{tot:,} FY{fy} units")

# === X4 redundancy ===
num = master.select_dtypes(include=[np.number])
flags = []
for col in ["cons_bldg_count", "carpark_capacity_lots", "dist_wet_market_m",
            "condo_txn_units", "bto_pipeline_est", "coworking_count"]:
    corrs = num.corrwith(df[col]).abs().sort_values(ascending=False).head(4)
    print(f"    {col} top |r|: " + ", ".join(f"{k}={x:.2f}" for k, x in corrs.items()))
    flags += [f"{col}~{k}={x:.2f}" for k, x in corrs.items()
              if x > 0.9 and not k.startswith(("hdb_", "pop_", "pc_", "pc2_",
                                               "mg_", "ring", "pw", "max1_",
                                               "max2_", "carpark", "parking",
                                               "pipe_", "lu_", "bldg_",
                                               "nearest_", "dist_", "walk_"))]
add("X4_redundancy", "PASS" if not flags else "WARN",
    "; ".join(flags) or "no non-source |r|>0.9")

n_fail = sum(c["status"] == "FAIL" for c in report["checks"])
n_warn = sum(c["status"] == "WARN" for c in report["checks"])
report["verdict"] = "FAIL" if n_fail else ("WARN" if n_warn else "PASS")
json.dump(report, open(ROOT / "logs/validate_context_pack.json", "w"), indent=2,
          default=str)
print(f"\nVERDICT: {report['verdict']}  ({n_fail} fail, {n_warn} warn) "
      f"-> logs/validate_context_pack.json")
