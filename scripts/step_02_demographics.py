#!/usr/bin/env python3
"""Step 2: Demographics by Subzone"""
import pandas as pd
import geopandas as gpd
import numpy as np
import json, os, time

BASE = "/home/azureuser/digital-atlas-sgp/data"
OUT = "/home/azureuser/digital-atlas-sgp/intermediate"
os.makedirs(OUT, exist_ok=True)

def log(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)

log("STEP 2: DEMOGRAPHICS BY SUBZONE")

# Load subzone areas
sz = gpd.read_file(BASE + "/boundaries/subzones.geojson")
sz_proj = sz.to_crs(epsg=3414)
sz_proj["area_km2"] = sz_proj.geometry.area / 1e6
sz_areas = sz_proj[["SUBZONE_C", "SUBZONE_N", "PLN_AREA_N", "REGION_N", "area_km2"]].copy()
sz_areas.columns = ["subzone_code", "subzone_name", "planning_area", "region", "area_km2"]
log("Subzone areas: %d zones, total %.1f km2" % (len(sz_areas), sz_areas["area_km2"].sum()))

# === Population by Age/Sex (2025) ===
pop = pd.read_csv(BASE + "/demographics/pop_age_sex_fa_2025.csv")
log("Pop age/sex/FA 2025: %d rows, cols: %s" % (len(pop), list(pop.columns)))

# Aggregate: total pop per subzone
pop_sz = pop.groupby(["PA", "SZ"]).agg({"Pop": "sum"}).reset_index()
pop_sz.columns = ["planning_area", "subzone_name", "total_population"]
log("Unique subzones in pop data: %d" % pop_sz["subzone_name"].nunique())

# Age distribution
age_groups = pop.groupby(["PA", "SZ", "AG"]).agg({"Pop": "sum"}).reset_index()
age_pivot = age_groups.pivot_table(index=["PA", "SZ"], columns="AG", values="Pop", fill_value=0).reset_index()
age_pivot.columns.name = None

# Sex distribution
sex_groups = pop.groupby(["PA", "SZ", "Sex"]).agg({"Pop": "sum"}).reset_index()
sex_pivot = sex_groups.pivot_table(index=["PA", "SZ"], columns="Sex", values="Pop", fill_value=0).reset_index()
sex_pivot.columns.name = None

# === Population by Dwelling Type (2025) ===
pop_tod = pd.read_csv(BASE + "/demographics/pop_age_sex_tod_2025.csv")
# Fix BOM
pop_tod.columns = [c.strip().replace("\ufeff", "") for c in pop_tod.columns]
log("Pop by dwelling 2025: %d rows" % len(pop_tod))

tod_groups = pop_tod.groupby(["PA", "SZ", "TOD"]).agg({"Pop": "sum"}).reset_index()
tod_pivot = tod_groups.pivot_table(index=["PA", "SZ"], columns="TOD", values="Pop", fill_value=0).reset_index()
tod_pivot.columns.name = None

# === Dwellings by Subzone (2025) ===
dwl = pd.read_csv(BASE + "/demographics/dwellings_subzone_2025.csv")
log("Dwellings 2025: %d rows" % len(dwl))

dwl_latest = dwl[dwl["Time"] == dwl["Time"].max()].copy()
dwl_pivot = dwl_latest.pivot_table(index=["PA", "SZ"], columns="FA", values="HSE", fill_value=0).reset_index()
dwl_pivot.columns.name = None

# === Merge all demographics ===
log("Merging demographics...")

# Start with population totals
demo = pop_sz.copy()

# Merge age distribution
demo = demo.merge(age_pivot, left_on=["planning_area", "subzone_name"], right_on=["PA", "SZ"], how="left")
demo.drop(columns=["PA", "SZ"], errors="ignore", inplace=True)

# Merge sex
demo = demo.merge(sex_pivot, left_on=["planning_area", "subzone_name"], right_on=["PA", "SZ"], how="left")
demo.drop(columns=["PA", "SZ"], errors="ignore", inplace=True)

# Merge dwelling type
demo = demo.merge(tod_pivot, left_on=["planning_area", "subzone_name"], right_on=["PA", "SZ"], how="left")
demo.drop(columns=["PA", "SZ"], errors="ignore", inplace=True)

# Match to subzone_code
demo["subzone_name_upper"] = demo["subzone_name"].str.upper().str.strip()
sz_areas["subzone_name_upper"] = sz_areas["subzone_name"].str.upper().str.strip()

demo = demo.merge(sz_areas[["subzone_code", "subzone_name_upper", "area_km2"]], on="subzone_name_upper", how="left")

# Compute derived features
total = demo["total_population"]
total_safe = total.replace(0, np.nan)

demo["pop_density"] = total / demo["area_km2"]

# Age brackets - find columns
age_cols = [c for c in demo.columns if c not in ["planning_area", "subzone_name", "total_population",
            "subzone_name_upper", "subzone_code", "area_km2", "pop_density"] and c not in ["Males", "Females", "Total"]]

# Identify age bracket columns
young_cols = [c for c in age_cols if any(a in str(c) for a in ["0 - 4", "5 - 9", "10 - 14"])]
working_cols = [c for c in age_cols if any(a in str(c) for a in ["15 -", "20 -", "25 -", "30 -", "35 -", "40 -", "45 -", "50 -", "55 -", "60 -"])]
elderly_cols = [c for c in age_cols if any(a in str(c) for a in ["65 -", "70 -", "75 -", "80 -", "85 -", "90"])]

if young_cols:
    demo["age_0_14_pct"] = demo[young_cols].sum(axis=1) / total_safe * 100
if elderly_cols:
    demo["age_65_plus_pct"] = demo[elderly_cols].sum(axis=1) / total_safe * 100
if working_cols:
    demo["age_15_64_pct"] = demo[working_cols].sum(axis=1) / total_safe * 100

if "Males" in demo.columns and "Females" in demo.columns:
    demo["male_pct"] = demo["Males"] / total_safe * 100
    demo["female_pct"] = demo["Females"] / total_safe * 100

if "age_0_14_pct" in demo.columns and "age_65_plus_pct" in demo.columns and "age_15_64_pct" in demo.columns:
    working = demo[working_cols].sum(axis=1)
    working_safe = working.replace(0, np.nan)
    demo["dependency_ratio"] = (demo[young_cols].sum(axis=1) + demo[elderly_cols].sum(axis=1)) / working_safe

# Keep clean columns
keep = ["subzone_code", "subzone_name", "planning_area", "area_km2",
        "total_population", "pop_density",
        "age_0_14_pct", "age_15_64_pct", "age_65_plus_pct",
        "male_pct", "female_pct", "dependency_ratio"]
# Add dwelling type columns if present
tod_col_names = [c for c in tod_pivot.columns if c not in ["PA", "SZ"]]
for c in tod_col_names:
    if c in demo.columns and c not in keep:
        # Normalize to percentage
        demo[c + "_pct"] = demo[c] / total_safe * 100
        keep.append(c + "_pct")

available = [c for c in keep if c in demo.columns]
result = demo[available].copy()

# Drop rows without subzone_code (totals, etc.)
result = result.dropna(subset=["subzone_code"])
result = result.drop_duplicates(subset=["subzone_code"])

log("Final demographics: %d subzones, %d features" % (len(result), len(result.columns)))

# Save
outpath = OUT + "/demographics_by_subzone.parquet"
result.to_parquet(outpath, index=False)
log("Saved: %s" % outpath)

# === VALIDATION ===
log("\n--- VALIDATION ---")
assert len(result) >= 300, "Too few subzones: %d" % len(result)
assert result["subzone_code"].is_unique, "Duplicate subzone codes"
assert result["total_population"].notna().sum() > 300, "Too many null populations"
assert result["total_population"].min() >= 0, "Negative population"
assert result["pop_density"].max() < 200000, "Unreasonable pop density"
if "age_0_14_pct" in result.columns:
    assert result["age_0_14_pct"].max() <= 100, "Age pct > 100"
log("All validations PASSED")

# Stats
log("\nKey stats:")
log("  Subzones: %d" % len(result))
log("  Total population: %d" % result["total_population"].sum())
log("  Pop density range: %.0f - %.0f per km2" % (result["pop_density"].min(), result["pop_density"].max()))
if "age_65_plus_pct" in result.columns:
    log("  Elderly pct range: %.1f%% - %.1f%%" % (result["age_65_plus_pct"].min(), result["age_65_plus_pct"].max()))
log("  Features: %s" % list(result.columns))
