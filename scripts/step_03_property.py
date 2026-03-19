#!/usr/bin/env python3
"""Step 3: Property data by Subzone"""
import pandas as pd
import numpy as np
import os, time

BASE = "/home/azureuser/digital-atlas-sgp/data"
OUT = "/home/azureuser/digital-atlas-sgp/intermediate"

def log(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)

log("STEP 3: PROPERTY BY SUBZONE")

# Load HDB resale
hdb = pd.read_csv(BASE + "/property/hdb_resale_prices.csv", low_memory=False)
log("HDB resale: %d rows, cols: %s" % (len(hdb), list(hdb.columns)[:8]))

# Parse
hdb["resale_price"] = pd.to_numeric(hdb["resale_price"], errors="coerce")
hdb["floor_area_sqm"] = pd.to_numeric(hdb["floor_area_sqm"], errors="coerce")
hdb["price_psf"] = hdb["resale_price"] / (hdb["floor_area_sqm"] * 10.764)  # sqm to sqft

# Recent 12 months
hdb["month_dt"] = pd.to_datetime(hdb["month"], format="%Y-%m")
latest = hdb["month_dt"].max()
cutoff = latest - pd.DateOffset(months=12)
hdb_recent = hdb[hdb["month_dt"] >= cutoff].copy()
log("HDB recent (12m): %d transactions" % len(hdb_recent))

# Aggregate by town (planning area proxy)
hdb_by_town = hdb_recent.groupby("town").agg(
    median_hdb_psf=("price_psf", "median"),
    hdb_transaction_count=("resale_price", "count"),
    median_hdb_price=("resale_price", "median"),
).reset_index()

# YoY: compare last 12m vs prior 12m
prior_cutoff = cutoff - pd.DateOffset(months=12)
hdb_prior = hdb[(hdb["month_dt"] >= prior_cutoff) & (hdb["month_dt"] < cutoff)]
prior_by_town = hdb_prior.groupby("town").agg(prior_median=("price_psf", "median")).reset_index()
hdb_by_town = hdb_by_town.merge(prior_by_town, on="town", how="left")
hdb_by_town["hdb_price_yoy_pct"] = ((hdb_by_town["median_hdb_psf"] - hdb_by_town["prior_median"]) / hdb_by_town["prior_median"] * 100)
hdb_by_town.drop(columns=["prior_median"], inplace=True)

log("HDB stats by town: %d towns" % len(hdb_by_town))

# Load private residential
priv = pd.read_csv(BASE + "/property/private_resi_transactions.csv", low_memory=False)
log("Private resi: %d rows, cols: %s" % (len(priv), list(priv.columns)[:8]))

# Parse price columns
for col in priv.columns:
    if "price" in col.lower() or "psf" in col.lower() or "area" in col.lower():
        priv[col] = pd.to_numeric(priv[col], errors="coerce")

# Find the right columns
price_col = [c for c in priv.columns if "price" in c.lower() and "psf" not in c.lower()]
psf_col = [c for c in priv.columns if "psf" in c.lower() or "unit price" in c.lower()]
area_col = [c for c in priv.columns if "area" in c.lower()]
district_col = [c for c in priv.columns if "district" in c.lower() or "postal" in c.lower()]

log("  Price cols: %s" % price_col)
log("  PSF cols: %s" % psf_col)
log("  District cols: %s" % district_col)

# Aggregate private by planning area if possible
# Map postal district to planning area (rough mapping)
priv_agg = None
if psf_col:
    psf = psf_col[0]
    priv["private_psf"] = pd.to_numeric(priv[psf], errors="coerce")
    priv_summary = pd.DataFrame({
        "median_private_psf": [priv["private_psf"].median()],
        "private_transaction_count": [len(priv)],
    })
    log("Private median PSF: $%.0f" % priv["private_psf"].median())

# Load demographics to get subzone → planning_area mapping
demo = pd.read_parquet(OUT + "/demographics_by_subzone.parquet")

# Map HDB town names to planning area names (they're similar but not exact)
town_to_pa = {}
for town in hdb_by_town["town"].unique():
    # Try exact match first
    match = demo[demo["planning_area"].str.upper() == town.upper()]
    if len(match) > 0:
        town_to_pa[town] = match.iloc[0]["planning_area"]
    else:
        # Fuzzy: central area, bukit timah etc
        for pa in demo["planning_area"].unique():
            if pa and town.upper() in pa.upper() or pa.upper() in town.upper():
                town_to_pa[town] = pa
                break

log("Town→PA mapping: %d/%d matched" % (len(town_to_pa), len(hdb_by_town)))

hdb_by_town["planning_area"] = hdb_by_town["town"].map(town_to_pa)

# Merge to subzone via planning_area
result = demo[["subzone_code", "subzone_name", "planning_area"]].copy()
result = result.merge(
    hdb_by_town[["planning_area", "median_hdb_psf", "hdb_transaction_count", "median_hdb_price", "hdb_price_yoy_pct"]],
    on="planning_area", how="left"
)

# Add global private stats (we don't have district-level private mapping yet)
if priv_agg is not None or psf_col:
    result["median_private_psf_national"] = priv["private_psf"].median() if psf_col else np.nan

# Save
outpath = OUT + "/property_by_subzone.parquet"
result.to_parquet(outpath, index=False)
log("Saved: %s" % outpath)

# === VALIDATION ===
log("\n--- VALIDATION ---")
assert len(result) >= 300, "Too few: %d" % len(result)
assert result["subzone_code"].is_unique, "Duplicate subzone codes"
assert result["median_hdb_psf"].notna().sum() > 200, "Too many null HDB prices"
assert result["median_hdb_psf"].min() > 0, "Zero HDB price"
assert result["median_hdb_psf"].max() < 3000, "Unreasonable HDB PSF (>$3000)"
log("All validations PASSED")

log("\nKey stats:")
log("  Subzones with HDB price: %d" % result["median_hdb_psf"].notna().sum())
log("  HDB PSF range: $%.0f - $%.0f" % (result["median_hdb_psf"].min(), result["median_hdb_psf"].max()))
log("  Features: %s" % list(result.columns))
