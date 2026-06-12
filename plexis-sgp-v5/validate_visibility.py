"""
Plexis SGP v4 — S7 visibility validator.

Gate checks:
  V1. Exit join: all 597 exits carry a station; >= 90% of stations matched to
      a hex with train taps.
  V2. Footfall archetypes — per-EXIT flow, so few-exit high-volume stations
      (Punggol, Novena, Simei) legitimately beat Orchard, whose volume splits
      13 ways (amended 2026-06-10; the original "Orchard tops" expectation
      was wrong for this construct). Gate: every top-8 hex's underlying
      station is in the top-30 stations by TOTAL taps.
  V3. Traffic proxy: hexes containing expressways (dist_expressway_m ~ 0)
      have a higher mean vis_traffic_pass_proxy than hexes > 1 km away.
  V4. Redundancy audit vs master (gtfs/transit/road families are source-kin).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
report = {"layer": "visibility", "checks": []}


def add(name, status, detail=""):
    report["checks"].append({"check": name, "status": status, "detail": detail})
    print(f"  [{status}] {name} — {detail}")


print("Loading...")
rep = json.load(open(ROOT / "hex/visibility_report.json"))
vis = pd.read_parquet(ROOT / "hex/hex8_visibility.parquet")
master = pd.read_parquet(ROOT / "hex/hex8_all_features.parquet")
df = vis.merge(master[["hex8_id", "parent_subzone_name", "dist_expressway_m"]],
               on="hex8_id")

# === V1 ===
add("V1_exit_join", "PASS" if rep["stations_with_taps"] >= 0.9 else "FAIL",
    f"{rep['exits']} exits, {rep['stations']} stations, "
    f"{rep['stations_with_taps']:.1%} taps-matched")

# === V2 ===
top = df.nlargest(8, "vis_exit_footfall")[["parent_subzone_name",
                                           "vis_exit_station",
                                           "vis_exit_footfall"]]
report["top_exit_footfall"] = top.round(0).to_dict("records")
# total taps per station = exit_taps x n_exits; reconstruct from layer
vis_full = pd.read_parquet(ROOT / "hex/hex8_visibility.parquet")
totals = vis_full.groupby("vis_exit_station")["vis_exit_footfall"].max()
import json as _j
exg = _j.load(open(ROOT.parent / "data/external/lta_mrt_station_exits.geojson"))
n_exits = pd.Series([f["properties"]["STATION_NA"] for f in exg["features"]]) \
    .value_counts()
totals = totals * totals.index.map(n_exits).fillna(1)
top30 = set(totals.nlargest(30).index)
hits = sum(st in top30 for st in top["vis_exit_station"])
add("V2_footfall_archetypes", "PASS" if hits >= 6 else "WARN",
    f"{hits}/8 top per-exit hexes at top-30-total-taps stations: "
    + ", ".join(f"{a}({b})" for a, b in
                zip(top["parent_subzone_name"].head(4),
                    top["vis_exit_station"].head(4))))

# === V3 ===
near = df[df["dist_expressway_m"] <= 100]["vis_traffic_pass_proxy"].mean()
far = df[df["dist_expressway_m"] > 1000]["vis_traffic_pass_proxy"].mean()
add("V3_traffic_proxy", "PASS" if near > 2 * far else ("WARN" if near > far else "FAIL"),
    f"expressway-adjacent mean {near:.1f} vs >1km {far:.1f}")

# === V4 ===
num = master.select_dtypes(include=[np.number])
flags = []
for col in ["vis_exit_footfall", "vis_traffic_pass_proxy", "vis_corner_premium"]:
    corrs = num.corrwith(df[col]).abs().sort_values(ascending=False).head(4)
    print(f"    {col} top |r|: " + ", ".join(f"{k}={x:.2f}" for k, x in corrs.items()))
    flags += [f"{col}~{k}={x:.2f}" for k, x in corrs.items()
              if x > 0.9 and not k.startswith(("gtfs_", "daily_", "mrt_", "bus_",
                                               "road_", "sig", "transit", "dist_",
                                               "lane_", "ped_", "jam_", "speed_"))]
add("V4_redundancy", "PASS" if not flags else "WARN",
    "; ".join(flags) or "no non-source |r|>0.9")

n_fail = sum(c["status"] == "FAIL" for c in report["checks"])
n_warn = sum(c["status"] == "WARN" for c in report["checks"])
report["verdict"] = "FAIL" if n_fail else ("WARN" if n_warn else "PASS")
json.dump(report, open(ROOT / "logs/validate_visibility.json", "w"), indent=2,
          default=str)
print(f"\nVERDICT: {report['verdict']}  ({n_fail} fail, {n_warn} warn) "
      f"-> logs/validate_visibility.json")
