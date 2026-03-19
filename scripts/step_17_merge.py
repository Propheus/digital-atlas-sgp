#!/usr/bin/env python3
"""Steps 17-19: Merge, Export, Validate"""
import pandas as pd
import numpy as np
import os, time, json

OUT = "/home/azureuser/digital-atlas-sgp/intermediate"
FINAL = "/home/azureuser/digital-atlas-sgp/final"
os.makedirs(FINAL, exist_ok=True)

def log(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)

log("=" * 60)
log("STEP 17: MERGE ALL SUBZONE FEATURES")
log("=" * 60)

files = {
    "demographics": "demographics_by_subzone.parquet",
    "property": "property_by_subzone.parquet",
    "roads": "roads_by_subzone.parquet",
    "landuse": "landuse_by_subzone.parquet",
    "transit": "transit_by_subzone.parquet",
    "categories": "place_composition_by_subzone.parquet",
    "place_types": "place_types_by_subzone.parquet",
    "brands": "brand_quality_by_subzone.parquet",
    "validation": "validation_by_subzone.parquet",
    "amenities": "amenity_by_subzone.parquet",
}

dfs = {}
for name, fname in files.items():
    path = os.path.join(OUT, fname)
    if os.path.exists(path):
        dfs[name] = pd.read_parquet(path)
        log("  Loaded %s: %d rows, %d cols" % (name, len(dfs[name]), len(dfs[name].columns)))

base = dfs["demographics"][["subzone_code", "subzone_name", "planning_area", "area_km2"]].copy()
log("Base: %d subzones" % len(base))

for name, df in dfs.items():
    if name == "demographics":
        demo_cols = [c for c in df.columns if c not in ["subzone_name", "planning_area", "area_km2"]]
        base = base.merge(df[demo_cols], on="subzone_code", how="left")
    else:
        drop_cols = [c for c in df.columns if c in ["subzone_name", "planning_area", "area_km2"]]
        df_clean = df.drop(columns=drop_cols, errors="ignore")
        if "subzone_code" in df_clean.columns:
            base = base.merge(df_clean, on="subzone_code", how="left")
            log("  Merged %s: now %d cols" % (name, len(base.columns)))

log("Merged: %d subzones x %d features" % (len(base), len(base.columns)))

base.to_parquet(FINAL + "/subzone_features_raw.parquet", index=False)
log("Saved raw")

# Normalize
numeric_cols = base.select_dtypes(include=[np.number]).columns.tolist()
normalized = base.copy()
for col in numeric_cols:
    vals = normalized[col]
    std = vals.std()
    if std > 0:
        normalized[col] = (vals - vals.mean()) / std
    normalized[col] = normalized[col].fillna(0)

normalized.to_parquet(FINAL + "/subzone_features.parquet", index=False)
log("Saved normalized")

# Step 18: Place features
log("\nSTEP 18: PLACE FEATURES")
transit_place = pd.read_parquet(OUT + "/transit_by_place.parquet")
places = pd.read_json("/home/azureuser/digital-atlas-sgp/data/places/sgp_places.jsonl", lines=True)

pf = places[["id", "latitude", "longitude", "main_category", "place_type"]].copy()
pf = pf.rename(columns={"id": "place_id"})
if "subzone_code" in places.columns:
    pf["subzone_code"] = places["subzone_code"]
elif "subzone" in places.columns:
    # Need to map subzone name to code
    demo = dfs["demographics"]
    sz_map = dict(zip(demo["subzone_name"].str.upper(), demo["subzone_code"]))
    pf["subzone_code"] = places["subzone"].str.upper().map(sz_map)

pf = pf.merge(transit_place[["place_id", "dist_nearest_mrt", "dist_nearest_bus", "bus_stops_300m", "mrt_within_500m"]], on="place_id", how="left")

if "rating" in places.columns:
    pf["rating"] = places["rating"].values
if "review_count" in places.columns:
    pf["review_count"] = places["review_count"].values
if "brand" in places.columns:
    pf["has_brand"] = places["brand"].notna().astype(int).values

pf.to_parquet(FINAL + "/place_features.parquet", index=False)
log("Saved place_features: %d rows x %d cols" % (len(pf), len(pf.columns)))

# Step 19: Validate
log("\nSTEP 19: FINAL VALIDATION")
sf = pd.read_parquet(FINAL + "/subzone_features.parquet")
num_f = len(sf.select_dtypes(include=[np.number]).columns)

checks = []
checks.append(("subzone rows", 320 <= len(sf) <= 335, "%d" % len(sf)))
checks.append(("subzone_code unique", sf["subzone_code"].is_unique, ""))
checks.append(("numeric features >= 80", num_f >= 80, "%d" % num_f))
checks.append(("no all-null cols", not sf.select_dtypes(include=[np.number]).isna().all().any(), ""))
checks.append(("no google leakage", not any("google" in c.lower() for c in sf.columns), ""))
checks.append(("place rows", 60000 <= len(pf) <= 70000, "%d" % len(pf)))
checks.append(("place_id unique", pf["place_id"].is_unique, ""))
checks.append(("place has transit", pf["dist_nearest_mrt"].notna().sum() > 60000, ""))

all_pass = True
for name, passed, detail in checks:
    status = "PASS" if passed else "FAIL"
    log("  [%s] %s %s" % (status, name, detail))
    if not passed:
        all_pass = False

# Feature catalog
raw = pd.read_parquet(FINAL + "/subzone_features_raw.parquet")
catalog = []
for col in raw.select_dtypes(include=[np.number]).columns:
    v = raw[col]
    catalog.append({
        "feature": col, "non_null": int(v.notna().sum()),
        "null_pct": round(v.isna().mean()*100, 1),
        "mean": round(float(v.mean()), 2) if v.notna().any() else None,
        "std": round(float(v.std()), 2) if v.notna().any() else None,
        "min": round(float(v.min()), 2) if v.notna().any() else None,
        "max": round(float(v.max()), 2) if v.notna().any() else None,
    })

pd.DataFrame(catalog).to_csv(FINAL + "/feature_catalog.csv", index=False)

log("\n" + "=" * 60)
log("FINAL SUMMARY")
log("=" * 60)
log("  subzone_features: %d subzones x %d cols (%d numeric)" % (len(sf), len(sf.columns), num_f))
log("  place_features:   %d places x %d cols" % (len(pf), len(pf.columns)))
log("  feature_catalog:  %d features" % len(catalog))
log("  VALIDATION: %s" % ("ALL PASSED" if all_pass else "SOME FAILED"))

for f in sorted(os.listdir(FINAL)):
    log("  %s: %.1f KB" % (f, os.path.getsize(os.path.join(FINAL, f))/1024))
