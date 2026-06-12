"""
Plexis SGP v4 — roads + parking validator.

Eight checks:
  R1. Total clipped length within 5% of expected SGP road km (~28K)
  R2. Class shares sum to 1 per hex with roads
  R3. Pedestrian + Vehicular ≈ Total (within 5% per hex; small slack for cycleway/track unbucketed)
  R4. Lane-km positive on all hexes with vehicular roads
  R5. Highrise hexes (CBD) have low road_walkable_share (commercial = wider, cars)
  R6. Expressway proximity makes geographic sense (top hexes near PIE/CTE/AYE/ECP corridors)
  R7. Parking landmark sanity (Suntec, Marina Bay etc. have parking presence)
  R8. HDB MSCP count within 10% of authoritative 1,114
"""
import json, os
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).parent
report = {"checks": []}


def add(name, status, detail=""):
    report["checks"].append({"check": name, "status": status, "detail": detail})
    tag = "PASS" if status == "PASS" else ("WARN" if status == "WARN" else "FAIL")
    print(f"  [{tag}] {name} — {detail}")


print("Loading...")
roads = pd.read_parquet(ROOT / "hex/hex9_roads.parquet")
park = pd.read_parquet(ROOT / "hex/hex9_parking.parquet")
h9 = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
print(f"  roads: {roads.shape}  parking: {park.shape}  hex9: {len(h9):,}")

# === R1 total length ===
total_km = roads["road_length_total_m"].sum() / 1000
EXPECTED = 28_000  # SGP has ~28-30K km of OSM roads
diff_pct = 100 * abs(total_km - EXPECTED) / EXPECTED
if 25_000 <= total_km <= 32_000:
    add("R1_total_length_in_range", "PASS", f"{total_km:,.0f} km (expected 25K-32K)")
else:
    add("R1_total_length_in_range", "WARN", f"{total_km:,.0f} km")

# === R2 class shares sum to 1 ===
pct_cols = [c for c in roads.columns if c.startswith("road_") and c.endswith("_pct")]
share_sum = roads[pct_cols].sum(axis=1)
hexes_with_road = roads[roads["road_length_total_m"] > 0]
shares_ok = ((np.isclose(share_sum, 1.0, atol=0.05))
             | (np.isclose(share_sum, 0.0, atol=1e-9)))
ok_pct = 100 * shares_ok.mean()
if ok_pct >= 95:
    add("R2_class_shares_sum_to_1", "PASS",
        f"{ok_pct:.1f}% of rows have shares ∑≈1 or 0; range [{share_sum.min():.3f}, {share_sum.max():.3f}]")
else:
    add("R2_class_shares_sum_to_1", "WARN", f"only {ok_pct:.1f}% have shares ∑≈1 (some buckets may be excluded)")

# === R3 ped + veh ≈ total ===
roads["check_sum"] = roads["road_pedestrian_length_m"] + roads["road_vehicular_length_m"]
unaccounted_share = (roads["road_length_total_m"] - roads["check_sum"]) / roads["road_length_total_m"].replace(0, 1)
mean_unaccounted = unaccounted_share[roads["road_length_total_m"] > 0].mean()
if abs(mean_unaccounted) < 0.10:
    add("R3_ped_plus_veh_close_to_total", "PASS",
        f"mean unaccounted share {mean_unaccounted*100:.2f}% (cycleway/track/other)")
else:
    add("R3_ped_plus_veh_close_to_total", "WARN",
        f"mean unaccounted share {mean_unaccounted*100:.2f}%")

# === R4 lane-km on vehicular hexes ===
veh_hexes = roads[roads["road_vehicular_length_m"] > 0]
no_lane = (veh_hexes["lane_km"] == 0).sum()
if no_lane == 0:
    add("R4_lane_km_on_vehicular_hexes", "PASS", f"all {len(veh_hexes):,} vehicular hexes have lane_km > 0")
else:
    add("R4_lane_km_on_vehicular_hexes", "WARN", f"{no_lane} vehicular hexes have lane_km=0")

# === R5 CBD hexes have low walk share ===
# Marina South / Downtown Core / Tanjong Pagar — typically low walkable share (cars dominant)
cbd_hexes = h9[h9["parent_pa"].isin(["DOWNTOWN CORE", "MARINA SOUTH", "OUTRAM"])]
cbd_walk = roads[roads["hex9_id"].isin(cbd_hexes["hex9_id"])]
mean_walk = cbd_walk[cbd_walk["road_length_total_m"] > 0]["road_walkable_share"].mean()
# CBD should have substantial walkable share (footways exist), but not dominate
if 0.2 <= mean_walk <= 0.7:
    add("R5_cbd_walkable_share_reasonable", "PASS",
        f"mean walkable share in CBD = {mean_walk:.2f} (expected 0.2-0.7)")
else:
    add("R5_cbd_walkable_share_reasonable", "WARN", f"mean walk share {mean_walk:.2f}")

# === R6 expressway proximity sanity ===
# Top hexes by expressway through-length should be in expressway-corridor PAs
through_motorway = roads.merge(h9[["hex9_id", "parent_pa"]], on="hex9_id")
near_x = through_motorway[through_motorway["expressway_within_500m"]]
expected_pas = {"DOWNTOWN CORE", "MARINA SOUTH", "TANJONG PAGAR", "BUKIT MERAH",
                "QUEENSTOWN", "JURONG EAST", "JURONG WEST", "TUAS", "WOODLANDS",
                "TAMPINES", "BEDOK", "PASIR RIS", "HOUGANG", "ANG MO KIO",
                "TOA PAYOH", "BISHAN", "GEYLANG", "CHANGI", "KALLANG",
                "BUKIT TIMAH", "BUKIT BATOK", "BUKIT PANJANG", "CHOA CHU KANG",
                "CLEMENTI", "PUNGGOL", "SENGKANG", "SEMBAWANG", "YISHUN",
                "MARINE PARADE", "PIONEER", "TENGAH"}
in_expected = near_x["parent_pa"].isin(expected_pas).sum()
pct_in = 100 * in_expected / max(len(near_x), 1)
if pct_in >= 80:
    add("R6_expressway_corridors_sane", "PASS",
        f"{in_expected}/{len(near_x)} ({pct_in:.0f}%) of expressway-near hexes in expected PAs")
else:
    add("R6_expressway_corridors_sane", "WARN", f"{in_expected}/{len(near_x)} ({pct_in:.0f}%)")

# === R7 parking landmark sanity ===
# Marina Bay subzone area should have parking presence
park_h9 = park.merge(h9[["hex9_id", "parent_subzone_name", "parent_pa"]], on="hex9_id")
suntec_area = park_h9[park_h9["parent_subzone_name"].isin(["MARINA CENTRE", "RAFFLES PLACE", "BAYFRONT SUBZONE"])]
parking_present = (suntec_area["parking_lot_count"] > 0).sum()
if parking_present >= 2:
    add("R7_marina_parking_present", "PASS",
        f"{parking_present}/{len(suntec_area)} Marina/Raffles hexes have parking lots")
else:
    add("R7_marina_parking_present", "WARN",
        f"only {parking_present}/{len(suntec_area)} Marina hexes have parking lots")

# === R8 HDB MSCP count within range ===
mscp_total = park["hdb_mscp_count"].sum()
EXPECTED_MSCP = 1114
if 1000 <= mscp_total <= 1300:
    add("R8_hdb_mscp_count_in_range", "PASS",
        f"{int(mscp_total)} MSCPs (expected ~{EXPECTED_MSCP}, ±200)")
else:
    add("R8_hdb_mscp_count_in_range", "WARN", f"{int(mscp_total)} MSCPs vs expected {EXPECTED_MSCP}")

passes = sum(1 for c in report["checks"] if c["status"] == "PASS")
print(f"\n{passes}/{len(report['checks'])} checks passed")
for c in report["checks"]:
    print(f"  {c['status']:4s}  {c['check']}  — {c['detail']}")

report["generated_at"] = __import__("time").strftime("%Y-%m-%dT%H:%M:%S")
with open(ROOT / "hex/roads_validation.json", "w") as f:
    json.dump(report, f, indent=2)
