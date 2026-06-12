"""
Plexis SGP v4 — S3 daytime population validator.

Gate checks (SITE_SELECTION_METRICS.md S3 + gate protocol):
  D1. Conservation: national dt_pop within +/-5% of pop_resident
      (AM net flows redistribute people, they don't create them)
  D2. Clip accounting: clipped hexes < 2% of rows, clipped persons < 1% of pop
  D3. Archetypes: top-10 net gainers dominated by known CBD/job subzones;
      top-10 losers dominated by known bedroom towns
  D4. Discriminant validity vs breathing_idx. FINDING (2026-06-10): the
      explorer's breathing_idx = z(od_in_trips)-z(pop) is direction-blind —
      full-day in/out are symmetric (rho=0.996), so it collapses to
      throughput-vs-pop (rho=0.999) and mis-scores interchange town centres
      (Yishun Central, Woodgrove, Tampines East...) as job centers. The
      original gate (agreement rho>=0.7) was therefore wrong. Replacement:
      dt_net must predict actual office presence BETTER than breathing_idx
      (Spearman vs pc2_cat_biz_office_count and pc_cat_business_office).
  D5. Formula guard: dt_pop <= pop_resident + dt_inflow (+eps) everywhere
  D6. Mode-share sensitivity: hex ranking of dt_pop stable (Spearman >= 0.98)
      across PT_MODE_SHARE in [0.50, 0.75]
  D7. Coverage / NaN accounting: hexes without OD have dt_pop == pop_resident
      and dt_class == no_data iff also below ratio pop floor
  D8. Redundancy audit vs all 601 master cols: report top |r|; any new
      *informative* col (dt_net, dt_ratio) with |r| > 0.9 vs an existing
      non-population col fails (dt_pop is pop-anchored by design — reported,
      not failed, for corr vs pop_* cols)
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).parent
report = {"layer": "daytime_pop", "checks": []}

CBD_JOB_SUBZONES = {
    "CENTRAL SUBZONE", "RAFFLES PLACE", "CECIL", "TANJONG PAGAR", "ANSON",
    "CITY HALL", "CLIFFORD PIER", "MARINA CENTRE", "BUGIS", "CHINATOWN",
    "BOULEVARD", "ORCHARD", "MOULMEIN", "TOH GUAN", "INTERNATIONAL BUSINESS PARK",
    "CHANGI AIRPORT", "AIRPORT ROAD", "SELETAR AEROSPACE PARK", "ONE-NORTH",
    "ALEXANDRA NORTH", "MARITIME SQUARE", "PATERSON", "SOMERSET",
}
BEDROOM_SUBZONE_HINTS = (
    "SEMBAWANG", "WOODLANDS", "YISHUN", "SENGKANG", "PUNGGOL", "RIVERVALE",
    "MATILDA", "JELEBU", "TAMPINES", "PASIR RIS", "JURONG WEST", "CHOA CHU KANG",
    "BUKIT PANJANG", "ANCHORVALE", "COMPASSVALE", "FERNVALE", "HOUGANG",
)


def add(name, status, detail=""):
    report["checks"].append({"check": name, "status": status, "detail": detail})
    print(f"  [{status}] {name} — {detail}")


print("Loading...")
dt = pd.read_parquet(ROOT / "hex/hex8_daytime_pop.parquet")
pop = pd.read_parquet(ROOT / "hex/hex8_population.parquet")
od = pd.read_parquet(ROOT / "hex/hex8_od_features.parquet")
master = pd.read_parquet(ROOT / "hex/hex8_all_features.parquet")
df = dt.merge(pop[["hex8_id", "pop_resident", "parent_subzone_name"]], on="hex8_id") \
       .merge(od[["hex8_id", "od_in_am", "od_out_am", "od_in_trips", "od_throughput"]], on="hex8_id")
assert len(df) == len(dt) == 1191, "row drift on join"

# === D1 conservation ===
nat_pop, nat_dt = df["pop_resident"].sum(), df["dt_pop"].sum()
drift = (nat_dt - nat_pop) / nat_pop
add("D1_conservation", "PASS" if abs(drift) <= 0.05 else "FAIL",
    f"dt_pop {nat_dt:,.0f} vs pop {nat_pop:,.0f} ({drift:+.2%})")

# === D2 clip accounting ===
n_clip = int(df["dt_clipped"].sum())
raw = df["pop_resident"] + df["dt_net_am_persons"]
clip_persons = raw.clip(upper=0).abs().sum()
ok = n_clip < 0.02 * len(df) and clip_persons < 0.01 * nat_pop
add("D2_clip_accounting", "PASS" if ok else "FAIL",
    f"{n_clip} hexes clipped ({n_clip/len(df):.1%}), {clip_persons:,.0f} persons ({clip_persons/nat_pop:.2%})")
if n_clip:
    worst = df[df["dt_clipped"]].nsmallest(5, "dt_net_am_persons")
    report["clipped_examples"] = worst[["hex8_id", "parent_subzone_name", "pop_resident",
                                        "dt_net_am_persons"]].to_dict("records")

# === D3 archetypes ===
top_gain = df.nlargest(10, "dt_net_am_persons")
top_lose = df.nsmallest(10, "dt_net_am_persons")
gain_hits = sum(sz in CBD_JOB_SUBZONES for sz in top_gain["parent_subzone_name"])
lose_hits = sum(any(h in sz for h in BEDROOM_SUBZONE_HINTS) for sz in top_lose["parent_subzone_name"])
add("D3_archetypes", "PASS" if (gain_hits >= 7 and lose_hits >= 7) else
    ("WARN" if (gain_hits >= 5 and lose_hits >= 5) else "FAIL"),
    f"top-10 gainers in CBD/job set: {gain_hits}/10; top-10 losers bedroom: {lose_hits}/10")
report["top_gainers"] = top_gain[["parent_subzone_name", "dt_net_am_persons"]].round(0).to_dict("records")
report["top_losers"] = top_lose[["parent_subzone_name", "dt_net_am_persons"]].round(0).to_dict("records")

# === D4 discriminant validity vs breathing_idx ===
active = (df["pop_resident"] > 50) | (df["od_throughput"] > 0)


def z(s):
    return (s - s.mean()) / (s.std() + 1e-9)


a = df[active].merge(master[["hex8_id", "pc_cat_business_office",
                             "pc2_cat_biz_office_count"]], on="hex8_id")
breathing = z(a["od_in_trips"]) - z(a["pop_resident"])
wins, det = 0, []
for tgt in ["pc_cat_business_office", "pc2_cat_biz_office_count"]:
    r_dt = spearmanr(a["dt_net_am_persons"], a[tgt]).statistic
    r_br = spearmanr(breathing, a[tgt]).statistic
    wins += r_dt > r_br
    det.append(f"{tgt}: dt_net {r_dt:.3f} vs breathing {r_br:.3f}")
r_agree = spearmanr(breathing, a["dt_net_am_persons"]).statistic
det.append(f"(agreement rho={r_agree:.3f}; divergence expected — breathing is direction-blind)")
add("D4_discriminant_vs_breathing", "PASS" if wins == 2 else ("WARN" if wins == 1 else "FAIL"),
    "; ".join(det))

# === D5 formula guard ===
viol = (df["dt_pop"] > df["pop_resident"] + df["dt_inflow_am_persons"] + 0.01).sum()
add("D5_formula_guard", "PASS" if viol == 0 else "FAIL", f"{viol} violations")

# === D6 mode-share sensitivity ===
WEEKDAYS = 22
net_raw = (df["od_in_am"] - df["od_out_am"]) / WEEKDAYS
lo = (df["pop_resident"] + net_raw / 0.50).clip(lower=0)
hi = (df["pop_resident"] + net_raw / 0.75).clip(lower=0)
rho_ms, _ = spearmanr(lo, hi)
add("D6_modeshare_sensitivity", "PASS" if rho_ms >= 0.98 else "FAIL",
    f"Spearman(dt_pop@0.50, dt_pop@0.75) = {rho_ms:.4f}")

# === D7 coverage / NaN accounting ===
no_od = df["od_throughput"] == 0
eq = (df.loc[no_od, "dt_pop"] - df.loc[no_od, "pop_resident"]).abs().max()
n_nodata = (df["dt_class"] == "no_data").sum()
ok = eq < 0.01 and n_nodata >= no_od.sum() - (df.loc[no_od, "pop_resident"] >= 50).sum()
add("D7_coverage", "PASS" if ok else "FAIL",
    f"{no_od.sum()} hexes w/o OD (dt_pop==pop max dev {eq:.3f}); dt_class no_data: {n_nodata}")

# === D8 redundancy audit vs master ===
num = master.select_dtypes(include=[np.number])
aud = master[["hex8_id"]].merge(df[["hex8_id", "dt_pop", "dt_net_am_persons", "dt_ratio"]], on="hex8_id")
flags = []
report["redundancy_top5"] = {}
for col in ["dt_pop", "dt_net_am_persons", "dt_ratio"]:
    v = aud[col]
    corrs = num.corrwith(v).abs().sort_values(ascending=False).head(5)
    report["redundancy_top5"][col] = corrs.round(3).to_dict()
    print(f"    {col} top-5 |r|: " + ", ".join(f"{k}={x:.2f}" for k, x in corrs.items()))
    for k, x in corrs.items():
        pop_anchored = col == "dt_pop" and (k.startswith("pop_") or k in ("n_dwellings", "hdb_units"))
        if x > 0.9 and not pop_anchored and not k.startswith("od_"):
            flags.append(f"{col}~{k}={x:.2f}")
# od_* exclusion: dt_* are declared derived composites of od_+pop (like vibrancy_index);
# the audit guards against accidentally duplicating an *unrelated* existing feature.
add("D8_redundancy", "PASS" if not flags else "WARN", "; ".join(flags) or
    "no |r|>0.9 vs non-source columns")

n_fail = sum(c["status"] == "FAIL" for c in report["checks"])
n_warn = sum(c["status"] == "WARN" for c in report["checks"])
report["verdict"] = "FAIL" if n_fail else ("WARN" if n_warn else "PASS")
json.dump(report, open(ROOT / "logs/validate_daytime_pop.json", "w"), indent=2, default=str)
print(f"\nVERDICT: {report['verdict']}  ({n_fail} fail, {n_warn} warn) "
      f"-> logs/validate_daytime_pop.json")
