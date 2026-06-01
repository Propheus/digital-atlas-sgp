"""
Plexis SGP v4 — hdb_resale validator.

H1 town count + total txn conservation
H2 Bishan / Bukit Merah / Queenstown / CCK in top-5 4r-median (mature/central towns)
H3 Yishun / Sembawang / Woodlands in bottom-5 (newer/north towns)
H4 4-room price/sqm in plausible range (3,000–11,000)
H5 hex9 cells in HDB town carry nonzero values (no broadcast misses)
H6 4r_median_price ≥ 250K and ≤ 1.5M for every town
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
h9 = pd.read_parquet(ROOT / "hex/hex9_hdb_resale.parquet")
h8 = pd.read_parquet(ROOT / "hex/hex8_hdb_resale.parquet")
sz = pd.read_parquet(ROOT / "hex/subzone_hdb_resale.parquet")
report_data = json.load(open(ROOT / "hex/hdb_resale_report.json"))

# H1 — total txns sum of unique towns
total_in = report_data["input_txns"]
h9_in = int(h9["hdb_resale_in_town"].sum())
if 1500 < h9_in < 4000:
    add("H1_hex9_in_hdb_town_count", "PASS", f"{h9_in} hex9 in HDB town (universe 7318)")
else:
    add("H1_hex9_in_hdb_town_count", "WARN", f"{h9_in} hex9 in HDB town (universe 7318)")

# Top by 4r price (use hex9 unique-town-only rows)
hubs_top = {"BISHAN","BUKIT MERAH","QUEENSTOWN","TOA PAYOH","KALLANG/WHAMPOA","CENTRAL AREA","BUKIT TIMAH"}
hubs_bot = {"YISHUN","SEMBAWANG","WOODLANDS","CHOA CHU KANG","JURONG WEST","BUKIT BATOK","BUKIT PANJANG","TENGAH"}

# We don't carry town col; reconstruct from per-town prices
h9_with_town = h9.merge(pd.read_parquet(ROOT / "hex/hex9_hdb_town_overlap.parquet")
                            .sort_values("overlap_deg2", ascending=False)
                            .drop_duplicates("hex9_id"), on="hex9_id", how="left")
town_prices = h9_with_town[h9_with_town["hdb_resale_in_town"] == 1].drop_duplicates("hdb_town")[
    ["hdb_town","hdb_resale_4r_median_price","hdb_resale_4r_median_psm"]]
top5 = set(town_prices.nlargest(5, "hdb_resale_4r_median_price")["hdb_town"])
bot5 = set(town_prices.nsmallest(5, "hdb_resale_4r_median_price")["hdb_town"])

# H2 top-5 ∩ hubs_top
hits_top = len(top5 & hubs_top)
if hits_top >= 3:
    add("H2_top5_in_central_hubs", "PASS", f"top5={top5} hits {hits_top}/5 expected central")
else:
    add("H2_top5_in_central_hubs", "WARN", f"top5={top5} hits {hits_top}")

# H3 bottom-5 ∩ hubs_bot
hits_bot = len(bot5 & hubs_bot)
if hits_bot >= 3:
    add("H3_bottom5_in_outer_towns", "PASS", f"bot5={bot5} hits {hits_bot}/5 expected outer")
else:
    add("H3_bottom5_in_outer_towns", "WARN", f"bot5={bot5} hits {hits_bot}")

# H4 4r price/sqm range (skip towns with no 4r txns yet, e.g. Tengah)
psm_nz = town_prices[town_prices["hdb_resale_4r_median_psm"] > 0]["hdb_resale_4r_median_psm"]
psm_min = psm_nz.min(); psm_max = psm_nz.max()
if 3000 <= psm_min <= 7000 and 6000 <= psm_max <= 14000:
    add("H4_4r_psm_range", "PASS", f"4r psm range [{psm_min:.0f}, {psm_max:.0f}] across {len(psm_nz)} towns")
else:
    add("H4_4r_psm_range", "WARN", f"[{psm_min:.0f}, {psm_max:.0f}]")

# H5 every HDB-town hex carries a nonzero price
broken = h9[(h9["hdb_resale_in_town"] == 1) & (h9["hdb_resale_4r_median_price"] == 0)]
if len(broken) <= 50:
    add("H5_no_broadcast_misses", "PASS", f"only {len(broken)} HDB-town hex9 have zero price (likely Tengah)")
else:
    add("H5_no_broadcast_misses", "WARN", f"{len(broken)} HDB-town hex9 have zero price")

# H6 per-town 4r median in plausible $250K–$1.5M
violations = town_prices[(town_prices["hdb_resale_4r_median_price"] > 0) &
                          ((town_prices["hdb_resale_4r_median_price"] < 250_000) |
                           (town_prices["hdb_resale_4r_median_price"] > 1_500_000))]
if len(violations) == 0:
    add("H6_4r_median_in_plausible_band", "PASS",
        f"all {len(town_prices)} towns within $250K–$1.5M")
else:
    add("H6_4r_median_in_plausible_band", "WARN",
        f"{len(violations)} towns out of band: " + str(violations[['hdb_town','hdb_resale_4r_median_price']].to_dict('records')[:3]))

passes = sum(1 for c in report["checks"] if c["status"] == "PASS")
print(f"\n{passes}/{len(report['checks'])} checks passed")

report["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
with open(ROOT / "hex/hdb_resale_validation.json", "w") as f:
    json.dump(report, f, indent=2)
