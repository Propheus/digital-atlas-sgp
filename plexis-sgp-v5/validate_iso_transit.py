"""
Plexis SGP v4 — S2b transit isochrone validator.

Gate checks:
  T1. Logic floor: transit15 reach >= 0.7x walk10 reach for >=99% of hexes
      (transit includes a pure-walk arm; 0.7 tolerance because the walk arm
      uses euclid x1.3 vs S2a's true network distances).
  T2. Archetypes: interchange town centres (Yishun Central, Tampines East,
      Woodlands East) in the top decile of t15 pop reach; rural Lim Chu Kang
      near-zero; CBD reaches >50k.
  T3. Stratified mechanics test. FINDING (2026-06-10): raw Spearman(t15_pop,
      transit_score) is only ~0.16 — and that is CORRECT, not a bug: t15_pop
      = access quality x surrounding density. High-score/low-reach hexes are
      MRT stations amid landed estates (Hillview, Swiss Club, Toh Tuck);
      low-score/high-reach are bus-dense HDB corridors without MRT (Hong Kah,
      Yunnan, Yishun East reaches 190k on buses alone). Replacement gate:
      within each ambient-density tercile (ring1_pop), Spearman(t15_pop,
      stops_used) >= 0.5 — transit quantity must drive reach given density.
  T4. Plausibility band: populated-hex median t15 pop in [30k, 200k]; max
      < 400k (15-min door-to-door cannot cover half of SG); no NaN/inf.
  T5. MRT lift: among populated hexes, those with an MRT station reach more
      than those without (mean ratio > 1.2).
  T6. Redundancy audit vs master: no |r| > 0.9 vs non-source cols.
  T7. Cached matrix (for S5): shape (1191, 7318); 45-min reach from CBD
      covers 1.5-4.5M (plausible half-of-SG band); finite share sane.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).parent
report = {"layer": "iso_transit", "checks": []}


def add(name, status, detail=""):
    report["checks"].append({"check": name, "status": status, "detail": detail})
    print(f"  [{status}] {name} — {detail}")


print("Loading...")
t = pd.read_parquet(ROOT / "hex/hex8_iso_transit.parquet")
w = pd.read_parquet(ROOT / "hex/hex8_iso_walk.parquet")[["hex8_id", "iso_walk10_pop"]]
master = pd.read_parquet(ROOT / "hex/hex8_all_features.parquet")
df = t.merge(w, on="hex8_id").merge(
    master[["hex8_id", "parent_subzone_name", "pop_resident", "transit_score",
            "mrt_station_count", "daily_train_taps"]], on="hex8_id")
assert len(df) == 1191
popd = df[df["pop_resident"] > 2000]

# === T1 logic floor ===
bad = df["iso_transit15_pop"] < 0.7 * df["iso_walk10_pop"]
add("T1_logic_floor", "PASS" if bad.mean() <= 0.01 else "FAIL",
    f"{bad.sum()} hexes below 0.7x walk reach ({bad.mean():.2%})")
if bad.any():
    report["t1_violators"] = df.loc[bad, ["parent_subzone_name", "iso_transit15_pop",
                                          "iso_walk10_pop"]].round(0).to_dict("records")

# === T2 archetypes ===
thr90 = df["iso_transit15_pop"].quantile(0.9)
hits, det = 0, []
for sz in ["YISHUN CENTRAL", "TAMPINES EAST", "WOODLANDS EAST"]:
    v = df.loc[df["parent_subzone_name"] == sz, "iso_transit15_pop"].max()
    hits += v >= thr90
    det.append(f"{sz} {v:,.0f}")
cbd = df.loc[df["parent_subzone_name"] == "CENTRAL SUBZONE", "iso_transit15_pop"].max()
lck = df.loc[df["parent_subzone_name"] == "LIM CHU KANG", "iso_transit15_pop"].max()
ok = hits == 3 and cbd > 50_000 and lck < 5_000
add("T2_archetypes", "PASS" if ok else ("WARN" if hits >= 2 else "FAIL"),
    f"interchange>=p90: {hits}/3 ({'; '.join(det)}); CBD {cbd:,.0f}; Lim Chu Kang {lck:,.0f}")

# === T3 stratified mechanics ===
pp = popd.merge(master[["hex8_id", "ring1_pop_resident"]], on="hex8_id")
pp["tier"] = pd.qcut(pp["ring1_pop_resident"], 3, labels=["lo", "mid", "hi"])
rhos = {str(g): spearmanr(s["iso_transit15_pop"], s["iso_transit15_stops_used"]).statistic
        for g, s in pp.groupby("tier", observed=True)}
raw = spearmanr(popd["iso_transit15_pop"], popd["transit_score"]).statistic
ok = all(r >= 0.5 for r in rhos.values())
add("T3_stratified_mechanics", "PASS" if ok else "FAIL",
    f"within-density-tercile Spearman(reach, stops): "
    + ", ".join(f"{k}={v:.2f}" for k, v in rhos.items())
    + f" (raw vs transit_score {raw:.2f} — divergence is the documented finding)")

# === T4 plausibility band ===
med = popd["iso_transit15_pop"].median()
mx = df["iso_transit15_pop"].max()
n_bad = int(df["iso_transit15_pop"].isna().sum() + np.isinf(df["iso_transit15_pop"]).sum())
ok = 30_000 <= med <= 200_000 and mx < 400_000 and n_bad == 0
add("T4_plausibility", "PASS" if ok else "FAIL",
    f"populated median {med:,.0f}; max {mx:,.0f}; NaN/inf {n_bad}")

# === T5 MRT lift ===
has = popd[popd["mrt_station_count"] > 0]["iso_transit15_pop"].mean()
no = popd[popd["mrt_station_count"] == 0]["iso_transit15_pop"].mean()
add("T5_mrt_lift", "PASS" if has / no > 1.2 else ("WARN" if has / no > 1.05 else "FAIL"),
    f"with-MRT mean {has:,.0f} vs without {no:,.0f} (x{has/no:.2f})")

# === T6 redundancy ===
num = master.select_dtypes(include=[np.number])
SOURCE_PREFIXES = ("pop_", "pc_", "pc2_", "ring", "pw1_", "pw2_", "max1_", "max2_",
                   "mg_", "gtfs_", "bus_", "mrt_", "daily_", "transit")
flags, top = [], {}
for col in ["iso_transit15_pop", "iso_transit15_places", "iso_transit15_stops_used"]:
    corrs = num.corrwith(df[col]).abs().sort_values(ascending=False).head(5)
    top[col] = corrs.round(3).to_dict()
    print(f"    {col} top-5 |r|: " + ", ".join(f"{k}={x:.2f}" for k, x in corrs.items()))
    flags += [f"{col}~{k}={x:.2f}" for k, x in corrs.items()
              if x > 0.9 and not k.startswith(SOURCE_PREFIXES)]
report["redundancy_top5"] = top
add("T6_redundancy", "PASS" if not flags else "WARN",
    "; ".join(flags) or "no |r|>0.9 vs non-source cols")

# === T7 cached matrix for S5 ===
npz = np.load(ROOT / "hex/hex8_hex9_transit_min.npz", allow_pickle=True)
tm = npz["minutes"]
h9pop = pd.read_parquet(ROOT / "hex/hex9_population.parquet")
pop9 = h9pop["pop_resident"].fillna(0).to_numpy()
cbd_i = df.index[df["parent_subzone_name"] == "CENTRAL SUBZONE"][0]
reach45 = pop9[tm[cbd_i] <= 45].sum()
ok = tm.shape == (1191, 7318) and 1_500_000 <= reach45 <= 4_500_000
add("T7_cached_matrix", "PASS" if ok else "FAIL",
    f"shape {tm.shape}; CBD 45-min pop reach {reach45:,.0f}")

n_fail = sum(c["status"] == "FAIL" for c in report["checks"])
n_warn = sum(c["status"] == "WARN" for c in report["checks"])
report["verdict"] = "FAIL" if n_fail else ("WARN" if n_warn else "PASS")
json.dump(report, open(ROOT / "logs/validate_iso_transit.json", "w"), indent=2, default=str)
print(f"\nVERDICT: {report['verdict']}  ({n_fail} fail, {n_warn} warn) "
      f"-> logs/validate_iso_transit.json")
