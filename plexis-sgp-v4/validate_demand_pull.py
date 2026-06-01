"""
Plexis SGP v4 — demand_pull validator.

D1 all 7 pull cols in [0,1]
D2 pull_cbd: top-20 hexes are in CBD-cluster PAs
D3 pull_mall: top-20 hexes near Orchard / Bugis / Bukit Timah / Vivocity
D4 pull_airport: top-20 hexes are in Changi/Bedok/Pasir Ris (East)
D5 pull_mrt_interchange: top-20 hexes near Bishan / Outram / Dhoby Ghaut / Jurong East
D6 pull_composite spread sane (p10 < 0.2, p90 > 0.4)
D7 hex9 → hex8 mean conservation roughly
"""
import json, time
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent
report = {"checks": []}


def add(name, status, detail=""):
    report["checks"].append({"check": name, "status": status, "detail": detail})
    print(f"  [{status}] {name} — {detail}")


print("Loading...")
h9 = pd.read_parquet(ROOT / "hex/hex9_demand_pull.parquet")
h8 = pd.read_parquet(ROOT / "hex/hex8_demand_pull.parquet")
h9_uni = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
h9_pa = h9.merge(h9_uni[["hex9_id","parent_pa","parent_subzone_name"]], on="hex9_id")

pull_cols = [c for c in h9.columns if c.startswith("pull_")]

# D1 bounds
ok = all((h9[c].between(0, 1)).all() for c in pull_cols)
if ok: add("D1_bounds", "PASS", "all 7 pull cols in [0,1]")
else:  add("D1_bounds", "FAIL", "out of bounds")

# D2 cbd top
exp = {"DOWNTOWN CORE","RAFFLES PLACE","CECIL","TANJONG PAGAR","MARINA SOUTH","OUTRAM","SINGAPORE RIVER","ROCHOR","MUSEUM","BUKIT MERAH"}
top = h9_pa.nlargest(20, "pull_cbd")
hits = top["parent_pa"].isin(exp).sum()
if hits >= 14: add("D2_cbd_top20_in_cbd_cluster", "PASS", f"{hits}/20 in CBD cluster")
else: add("D2_cbd_top20_in_cbd_cluster", "WARN", f"{hits}/20, top: {set(top['parent_pa'].head(5))}")

# D3 mall top — Orchard, Bugis, JE, Tampines, Bukit Timah, Bukit Merah
exp = {"ORCHARD","ROCHOR","DOWNTOWN CORE","NEWTON","TANGLIN","BUKIT TIMAH","BUKIT MERAH",
       "JURONG EAST","TAMPINES","TANJONG PAGAR","SINGAPORE RIVER","MUSEUM","KALLANG"}
top = h9_pa.nlargest(20, "pull_mall")
hits = top["parent_pa"].isin(exp).sum()
if hits >= 12: add("D3_mall_top20_near_retail_clusters", "PASS", f"{hits}/20")
else: add("D3_mall_top20_near_retail_clusters", "WARN", f"{hits}/20, top: {set(top['parent_pa'].head(5))}")

# D4 airport top
exp = {"CHANGI","CHANGI BAY","CHANGI POINT","PASIR RIS","BEDOK","TAMPINES","PAYA LEBAR","SIMEI"}
top = h9_pa.nlargest(20, "pull_airport")
hits = top["parent_pa"].isin(exp).sum()
if hits >= 14: add("D4_airport_top20_in_east", "PASS", f"{hits}/20 in East SGP")
else: add("D4_airport_top20_in_east", "WARN", f"{hits}/20, top: {set(top['parent_pa'].head(5))}")

# D5 MRT interchange top
exp = {"BISHAN","OUTRAM","MUSEUM","JURONG EAST","NEWTON","SERANGOON","DOWNTOWN CORE","ROCHOR",
       "MARINA SOUTH","CITY HALL","TAMPINES","KALLANG","TANJONG PAGAR","BUKIT MERAH"}
top = h9_pa.nlargest(20, "pull_mrt_interchange")
hits = top["parent_pa"].isin(exp).sum()
if hits >= 12: add("D5_mrt_intch_near_hubs", "PASS", f"{hits}/20")
else: add("D5_mrt_intch_near_hubs", "WARN", f"{hits}/20, top: {set(top['parent_pa'].head(5))}")

# D6 composite spread
p10 = h9["pull_composite"].quantile(0.10)
p90 = h9["pull_composite"].quantile(0.90)
if p10 < 0.30 and p90 > 0.40 and (p90 - p10) > 0.15:
    add("D6_composite_spread", "PASS", f"p10={p10:.3f}  p90={p90:.3f}")
else:
    add("D6_composite_spread", "WARN", f"p10={p10:.3f}  p90={p90:.3f}")

# D7 hex9 → hex8 mean conservation (within tolerance)
h9wp = h9.merge(h9_uni[["hex9_id","parent_hex8"]], on="hex9_id")
roll = h9wp.groupby("parent_hex8")["pull_composite"].mean().reset_index().rename(columns={"parent_hex8":"hex8_id"})
m = h8[["hex8_id","pull_composite"]].merge(roll, on="hex8_id", suffixes=("_direct","_rolled"))
diff = (m["pull_composite_direct"] - m["pull_composite_rolled"]).abs().max()
if diff < 0.005:
    add("D7_hex9_to_hex8_mean", "PASS", f"max abs diff {diff:.4f}")
else:
    add("D7_hex9_to_hex8_mean", "WARN", f"max abs diff {diff:.4f}")

passes = sum(1 for c in report["checks"] if c["status"] == "PASS")
print(f"\n{passes}/{len(report['checks'])} checks passed")

report["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
with open(ROOT / "hex/demand_pull_validation.json", "w") as f:
    json.dump(report, f, indent=2)
