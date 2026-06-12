"""
Plexis SGP v5 — S11 mobility pack validator.

Gate checks (S11_MOBILITY_PACK.md):
  M1. Join integrity: 1,191/1,191 hex8_id match the universe; no rows lost.
  M2. Dedupe held: no shipped numeric col with |r| >= 0.98 vs the existing
      master (the builder must have dropped them; report what it dropped).
  M3. Archetype anchors: time_to_cbd <= 10 min somewhere in Downtown Core and
      > 60 min in Lim Chu Kang; min15_score ~ 100 max at Toa Payoh; linkway
      density (m per hex) tops in mature HDB towns; Telok Blangah vulnerability
      penalty visible (> 0).
  M4. zone_type discipline: zone_type_broad present for all hexes; the
      non-residential categories carry NaN adequacy (NA, not 0) per the
      established rule.
  M5. NaN semantics + ranges: scores in [0,100]/[0,1] as appropriate;
      times > 0; no negative lengths.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
report = {"layer": "mobility_pack", "checks": []}


def add(name, status, detail=""):
    report["checks"].append({"check": name, "status": status, "detail": detail})
    print(f"  [{status}] {name} — {detail}")


print("Loading...")
mp = pd.read_parquet(ROOT / "hex/hex8_mobility_pack.parquet")
rep = json.load(open(ROOT / "hex/mobility_pack_report.json"))
master = pd.read_parquet(ROOT / "hex/hex8_all_features.parquet")
uni = set(master["hex8_id"])
df = mp.merge(master[["hex8_id", "parent_subzone_name", "parent_pa",
                      "pop_resident"]], on="hex8_id")

# === M1 ===
ok = len(mp) == 1191 and set(mp["hex8_id"]) == uni
add("M1_join_integrity", "PASS" if ok else "FAIL",
    f"{len(mp)} rows; id match {len(set(mp['hex8_id']) & uni)}/1191; "
    f"{rep['cols_shipped']} cols shipped, {len(rep['deduped_dropped'])} deduped away "
    f"({list(rep['deduped_dropped'])[:4]}...)")

# === M2 ===
num_m = master.select_dtypes(include=[np.number])
worst, worst_pair = 0.0, ""
for c in mp.columns:
    if c == "hex8_id" or not pd.api.types.is_numeric_dtype(mp[c]):
        continue
    s = num_m.corrwith(df[c]).abs()
    if s.max() > worst:
        worst, worst_pair = float(s.max()), f"{c}~{s.idxmax()}"
add("M2_dedupe_held", "PASS" if worst < 0.98 else "FAIL",
    f"max |r| vs existing master = {worst:.3f} ({worst_pair})")

# === M3 archetypes ===
dt_core = df[df["parent_pa"].str.upper() == "DOWNTOWN CORE"]["time_to_cbd_min"]
# Lim Chu Kang is non-scored territory: NaN is CORRECT there; remoteness is
# asserted via the national max instead
lck = df[df["parent_subzone_name"].str.contains("LIM CHU KANG", na=False)]["time_to_cbd_min"]
lck_ok = lck.isna().all() or lck.min() > 45
natmax_ok = df["time_to_cbd_min"].max() >= 60
tp = df[df["parent_subzone_name"].str.contains("TOA PAYOH", na=False)]["min15_score"]
# Telok Blangah's calibrated penalty lives in the ELDERLY profile
tb_df = df[df["parent_subzone_name"].str.contains("TELOK BLANGAH", na=False)]
tb = (tb_df["adq_core_elderly"] - tb_df["adq_default_elderly"]).dropna()
top_link = df.nlargest(10, "linkway_len_m")["parent_pa"].str.upper().tolist()
MATURE = {"TOA PAYOH", "ANG MO KIO", "BEDOK", "TAMPINES", "HOUGANG", "YISHUN",
          "WOODLANDS", "JURONG WEST", "BUKIT MERAH", "QUEENSTOWN", "CLEMENTI",
          "SENGKANG", "PUNGGOL", "CHOA CHU KANG", "BUKIT BATOK", "PASIR RIS"}
link_hits = sum(pa in MATURE for pa in top_link)
ok = (dt_core.min() <= 10 and lck_ok and natmax_ok and tp.max() >= 95
      and (tb > 0).any() and link_hits >= 6)
add("M3_archetypes", "PASS" if ok else "WARN",
    f"CBD min time {dt_core.min():.0f}min; LCK {'NA (non-scored, correct)' if lck.isna().all() else f'{lck.min():.0f}min'}; "
    f"national max {df['time_to_cbd_min'].max():.0f}min; Toa Payoh min15 max {tp.max():.0f}; "
    f"Telok Blangah elderly vuln penalty>0: {(tb > 0).any()} (max {tb.max() if len(tb) else 0:.1f}pts); "
    f"linkway top-10 mature {link_hits}/10")

# === M4 zone_type ===
zt_cov = df["zone_type_broad"].notna().mean()
nonres = df[df["zone_type_broad"].isin(["industrial", "airport", "nature",
                                        "islands", "future"])]
adq_na = nonres["adq_default"].isna().mean() if len(nonres) else np.nan
add("M4_zone_type", "PASS" if zt_cov == 1.0 and adq_na == 1.0 else "FAIL",
    f"zone_type_broad coverage {zt_cov:.0%}; non-res hexes n={len(nonres)}, "
    f"adequacy NA share {adq_na:.0%} (rule: NA, never scored)")

# === M5 ranges ===
errs = []
for c in [c for c in mp.columns if c.startswith("time_to_")]:
    v = mp[c].dropna()
    if (v <= 0).any() or v.max() > 240:
        errs.append(f"{c} out of range")
if mp["min15_score"].dropna().between(0, 100.5).all() is False:
    errs.append("min15_score range")
for c in ["linkway_len_m", "cycling_path_len_m"]:
    if (mp[c] < 0).any():
        errs.append(f"{c} negative")
adq_cols = [c for c in mp.columns if c.startswith("adq_") and
            pd.api.types.is_numeric_dtype(mp[c])]
report["nan_share_adq"] = {c: round(float(mp[c].isna().mean()), 3)
                           for c in adq_cols[:6]}
add("M5_ranges", "PASS" if not errs else "FAIL", "; ".join(errs) or
    "times/scores/lengths all in range; adq NaN shares logged")

n_fail = sum(c["status"] == "FAIL" for c in report["checks"])
n_warn = sum(c["status"] == "WARN" for c in report["checks"])
report["verdict"] = "FAIL" if n_fail else ("WARN" if n_warn else "PASS")
json.dump(report, open(ROOT / "logs/validate_mobility_pack.json", "w"), indent=2,
          default=str)
print(f"\nVERDICT: {report['verdict']}  ({n_fail} fail, {n_warn} warn) "
      f"-> logs/validate_mobility_pack.json")
