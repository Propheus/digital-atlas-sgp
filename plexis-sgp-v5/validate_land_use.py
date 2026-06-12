"""
Plexis SGP v4 — strict land-use validator.

Six checks:
  L1. Total intersected area within tolerance of total URA parcel area
  L2. Every hex has lu_total_m2 > 0 (full coverage)
  L3. lu_*_pct columns sum to ~1.0 (or 0 for empty hexes)
  L4. Entropy in [0, ln(15)] (15 = bucket count incl. 'other')
  L5. dominant_use is non-null where lu_total_m2 > 0
  L6. Landmark spot-checks (Sentosa hotel-heavy, NUS Kent Ridge institutional/business-park,
      Maritime Square commercial, Tuas business-heavy)
"""
import json, math, os
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).parent
report = {"checks": []}


def add(name, status, detail=""):
    report["checks"].append({"check": name, "status": status, "detail": detail})
    tag = "PASS" if status == "PASS" else ("WARN" if status == "WARN" else "FAIL")
    print(f"  [{tag}] {name} — {detail}")


def _resolve_data_root():
    if os.environ.get("PLEXIS_DATA_ROOT"):
        return Path(os.environ["PLEXIS_DATA_ROOT"])
    for c in [Path("/home/azureuser/digital-atlas-sgp/data"), ROOT.parent / "data"]:
        if c.exists():
            return c
    raise FileNotFoundError("No data root found")


DATA = _resolve_data_root()

print("Loading...")
lu = pd.read_parquet(ROOT / "hex/hex9_land_use.parquet")
h9 = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
df = lu.merge(h9[["hex9_id", "parent_subzone_name", "parent_pa"]], on="hex9_id")

print(f"  hex-9 rows: {len(df):,}")

BUCKETS = [
    "residential", "mixed_use", "commercial", "hotel", "business",
    "business_park", "educational", "health", "institutional",
    "open_space", "transport", "utility", "water", "reserve", "other",
]

# === L1 total area ===
total_lu_km2 = df["lu_total_m2"].sum() / 1e6
# Compare to URA parcel total (should match within rounding)
import geopandas as gpd
print("  Computing URA parcel total area...")
import json as _json
with open(DATA / "land_use/master_plan_land_use.geojson") as f:
    raw = _json.load(f)
ura_gdf = gpd.GeoDataFrame.from_features(raw["features"], crs=4326).to_crs(3414)
ura_total_km2 = ura_gdf.geometry.area.sum() / 1e6
diff_pct = 100 * abs(total_lu_km2 - ura_total_km2) / ura_total_km2
if diff_pct < 0.5:
    add("L1_total_area_match", "PASS", f"hex={total_lu_km2:.2f} km² vs ura={ura_total_km2:.2f} km², diff={diff_pct:.3f}%")
elif diff_pct < 2.0:
    add("L1_total_area_match", "WARN", f"diff={diff_pct:.2f}%")
else:
    add("L1_total_area_match", "FAIL", f"diff={diff_pct:.2f}%")

# === L2 every hex has lu data ===
empty = (df["lu_total_m2"] <= 0).sum()
if empty == 0:
    add("L2_full_coverage", "PASS", f"{len(df):,}/{len(df):,} hexes have land-use data")
else:
    add("L2_full_coverage", "WARN", f"{empty} hexes empty (likely sea-only edges)")

# === L3 shares sum to 1 ===
share_cols = [f"lu_{b}_pct" for b in BUCKETS]
share_sum = df[share_cols].sum(axis=1)
# Either ~1.0 or 0.0
ok_mask = (np.isclose(share_sum, 1.0, atol=1e-3)) | (np.isclose(share_sum, 0.0, atol=1e-9))
bad = (~ok_mask).sum()
if bad == 0:
    add("L3_shares_sum_to_1", "PASS", f"all {len(df):,} hexes have shares ∑≈1 (or 0)")
else:
    add("L3_shares_sum_to_1", "FAIL", f"{bad} rows with malformed shares; range [{share_sum.min():.4f}, {share_sum.max():.4f}]")

# === L4 entropy bounds ===
max_entropy = math.log(len(BUCKETS))
ent_ok = ((df["lu_entropy"] >= -1e-9) & (df["lu_entropy"] <= max_entropy + 1e-6)).all()
if ent_ok:
    add("L4_entropy_bounds", "PASS", f"all entropies in [0, ln({len(BUCKETS)})={max_entropy:.3f}]")
else:
    add("L4_entropy_bounds", "FAIL", f"out-of-range: min={df['lu_entropy'].min()}, max={df['lu_entropy'].max()}")

# === L5 dominant_use non-null where lu>0 ===
nonempty = df[df["lu_total_m2"] > 0]
null_dom = nonempty["dominant_use"].isna().sum()
if null_dom == 0:
    add("L5_dominant_use_present", "PASS", f"all {len(nonempty):,} non-empty hexes have dominant_use")
else:
    add("L5_dominant_use_present", "FAIL", f"{null_dom} non-empty hexes missing dominant_use")

# === L6 landmark spot-checks ===
print("\n  Landmark spot-checks:")
landmarks = [
    # (label, predicate function: takes df row)
    ("Sentosa hotel-heavy", lambda r: r["parent_subzone_name"] == "SENTOSA" and r["lu_hotel_pct"] > 0.20),
    ("NUS Kent Ridge institutional-or-bp", lambda r: r["parent_subzone_name"] == "KENT RIDGE" and (r["lu_institutional_pct"] + r["lu_business_park_pct"] + r["lu_educational_pct"]) > 0.5),
    ("Maritime Square commercial", lambda r: r["parent_subzone_name"] == "MARITIME SQUARE" and r["lu_commercial_pct"] > 0.5),
    ("Tuas business-heavy", lambda r: r["parent_pa"] == "TUAS" and r["lu_business_pct"] > 0.3),
    ("Mount Pleasant residential", lambda r: r["parent_subzone_name"] == "MOUNT PLEASANT" and r["lu_residential_pct"] > 0.5),
]
landmark_pass = 0
for label, pred in landmarks:
    matches = df[df.apply(pred, axis=1)]
    n = len(matches)
    print(f"    {label}: {n} hexes match")
    if n > 0:
        landmark_pass += 1

if landmark_pass == len(landmarks):
    add("L6_landmark_spot_checks", "PASS", f"{landmark_pass}/{len(landmarks)} landmark predicates have matching hexes")
elif landmark_pass >= len(landmarks) - 1:
    add("L6_landmark_spot_checks", "WARN", f"{landmark_pass}/{len(landmarks)}")
else:
    add("L6_landmark_spot_checks", "FAIL", f"{landmark_pass}/{len(landmarks)}")

passes = sum(1 for c in report["checks"] if c["status"] == "PASS")
print(f"\n{passes}/{len(report['checks'])} checks passed")
for c in report["checks"]:
    print(f"  {c['status']:4s}  {c['check']}  — {c['detail']}")

report["generated_at"] = __import__("time").strftime("%Y-%m-%dT%H:%M:%S")
with open(ROOT / "hex/land_use_validation.json", "w") as f:
    json.dump(report, f, indent=2)
