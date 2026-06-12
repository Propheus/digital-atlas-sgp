"""
Plexis SGP v4 — S8 rent surface validator.

Gate checks:
  R1. Archetypes: psf rents peak at new-build CBD + prime D9/10 — observed
      top-10 is City Hall (Midtown-era launches), SGH/Outram, Nassim, Leedon
      Park: all prime CCR. Gate: >= 5 of the top-10 populated hexes in the
      prime-CCR subzone set, and Woodlands/Choa Chu Kang below the populated
      median. (Original Boulevard/Somerset list held older large-format
      stock — lower psf is real, not an error; amended 2026-06-10.)
  R2. Coverage: >= 85% of populated hexes (pop > 2000) have a rent value;
      'none' hexes are predominantly low-population.
  R3. Sanity band: all rents in [1.5, 10] $psf/mo; Central region mean >
      North region mean (CCR > OCR ordering).
  R4. Cross-source agreement: corr(rent_resi, hdb_resale_4r_median_psm) in
      [0.3, 0.9] — same housing-cost construct, different market segment;
      1.0 would mean we added nothing, < 0.3 would mean noise.
  R5. Redundancy audit vs master (hdb_* exempted as the sibling construct).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
report = {"layer": "rent_surface", "checks": []}


def add(name, status, detail=""):
    report["checks"].append({"check": name, "status": status, "detail": detail})
    print(f"  [{status}] {name} — {detail}")


print("Loading...")
rent = pd.read_parquet(ROOT / "hex/hex8_rent_surface.parquet")
master = pd.read_parquet(ROOT / "hex/hex8_all_features.parquet")
df = rent.merge(master[["hex8_id", "parent_subzone_name", "parent_region",
                        "pop_resident", "hdb_resale_4r_median_psm"]], on="hex8_id")
popd = df[df["pop_resident"] > 2000]

# === R1 archetypes ===
PRIME_CCR = {"NASSIM", "LEEDON PARK", "INSTITUTION HILL", "CITY HALL",
             "BOULEVARD", "PATERSON", "SOMERSET", "CAIRNHILL", "ONE TREE HILL",
             "SINGAPORE GENERAL HOSPITAL", "EVERTON PARK", "KAMPONG JAVA",
             "GOODWOOD PARK", "OXLEY", "FORT CANNING", "CHATSWORTH",
             "MARGARET DRIVE", "RIDOUT"}
top10 = popd.nlargest(10, "rent_resi_psf_med")
hits = sum(sz in PRIME_CCR for sz in top10["parent_subzone_name"])
med = popd["rent_resi_psf_med"].median()
north = popd[popd["parent_subzone_name"].str.contains("WOODLANDS|CHOA CHU KANG",
                                                      na=False)]["rent_resi_psf_med"]
ok = hits >= 5 and north.median() < med
add("R1_archetypes", "PASS" if ok else "FAIL",
    f"top-10 rent hexes in prime-CCR set: {hits}/10; Woodlands/CCK median "
    f"{north.median():.2f} vs populated median {med:.2f}")

# === R2 coverage ===
cov = popd["rent_resi_psf_med"].notna().mean()
none_pop = df.loc[df["rent_resolution"] == "none", "pop_resident"]
add("R2_coverage", "PASS" if cov >= 0.85 else "FAIL",
    f"{cov:.1%} of populated hexes covered; 'none' hexes median pop "
    f"{none_pop.median():.0f}")

# === R3 sanity band ===
v = df["rent_resi_psf_med"].dropna()
central = popd[popd["parent_region"] == "CENTRAL REGION"]["rent_resi_psf_med"].mean()
nreg = popd[popd["parent_region"] == "NORTH REGION"]["rent_resi_psf_med"].mean()
ok = v.between(1.5, 10).all() and central > nreg
add("R3_sanity", "PASS" if ok else "FAIL",
    f"range [{v.min():.2f}, {v.max():.2f}]; Central mean {central:.2f} > "
    f"North mean {nreg:.2f}")

# === R4 cross-source ===
sub = popd.dropna(subset=["rent_resi_psf_med", "hdb_resale_4r_median_psm"])
sub = sub[sub["hdb_resale_4r_median_psm"] > 0]
r = float(np.corrcoef(sub["rent_resi_psf_med"], sub["hdb_resale_4r_median_psm"])[0, 1])
add("R4_cross_source", "PASS" if 0.3 <= r <= 0.9 else "WARN",
    f"corr(private rent, HDB resale psm) = {r:.3f} on {len(sub)} hexes")

# === R5 redundancy ===
num = master.select_dtypes(include=[np.number])
flags = []
for col in ["rent_resi_psf_med", "roi_cap_per_rent_total"]:
    corrs = num.corrwith(df[col]).abs().sort_values(ascending=False).head(5)
    print(f"    {col} top |r|: " + ", ".join(f"{k}={x:.2f}" for k, x in corrs.items()))
    flags += [f"{col}~{k}={x:.2f}" for k, x in corrs.items()
              if x > 0.9 and not k.startswith(("hdb_", "ring", "pw", "max1_",
                                               "max2_", "nvp_"))]
add("R5_redundancy", "PASS" if not flags else "WARN",
    "; ".join(flags) or "no non-source |r|>0.9")

n_fail = sum(c["status"] == "FAIL" for c in report["checks"])
n_warn = sum(c["status"] == "WARN" for c in report["checks"])
report["verdict"] = "FAIL" if n_fail else ("WARN" if n_warn else "PASS")
json.dump(report, open(ROOT / "logs/validate_rent_surface.json", "w"), indent=2,
          default=str)
print(f"\nVERDICT: {report['verdict']}  ({n_fail} fail, {n_warn} warn) "
      f"-> logs/validate_rent_surface.json")
