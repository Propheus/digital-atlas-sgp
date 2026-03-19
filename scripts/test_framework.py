#!/usr/bin/env python3
"""
Digital Atlas SGP - Test & Validation Framework
Every processing step must pass these checks.
"""
import json, os, sys, time
import pandas as pd
import geopandas as gpd
import numpy as np

BASE = "/home/azureuser/digital-atlas-sgp/data"
RESULTS = []

def log(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)

def test(name, condition, detail=""):
    passed = bool(condition)
    RESULTS.append({"name": name, "passed": passed, "detail": detail})
    status = "PASS" if passed else "FAIL"
    log("  [%s] %s %s" % (status, name, ("- " + detail) if detail else ""))
    return passed

def assert_no_nulls(df, columns, ctx=""):
    for col in columns:
        n = df[col].isna().sum()
        test("%s.%s no nulls" % (ctx, col), n == 0, "%d nulls" % n if n else "")

def assert_range(df, col, lo, hi, ctx=""):
    mn, mx = df[col].min(), df[col].max()
    test("%s.%s in [%s,%s]" % (ctx, col, lo, hi), mn >= lo and mx <= hi, "actual [%s,%s]" % (mn, mx))

def assert_unique(df, col, ctx=""):
    d = df[col].duplicated().sum()
    test("%s.%s unique" % (ctx, col), d == 0, "%d dupes" % d if d else "")

def assert_row_count(df, lo, hi, ctx=""):
    n = len(df)
    test("%s rows in [%d,%d]" % (ctx, lo, hi), lo <= n <= hi, "actual: %d" % n)

def assert_cols(df, cols, ctx=""):
    missing = [c for c in cols if c not in df.columns]
    test("%s has columns" % ctx, not missing, "missing: %s" % missing if missing else "%d OK" % len(cols))

def assert_no_leakage(df, patterns, ctx=""):
    for p in patterns:
        bad = [c for c in df.columns if p.lower() in c.lower()]
        test("%s no '%s' leakage" % (ctx, p), not bad, "found: %s" % bad if bad else "")

def assert_distributions(df, ctx=""):
    nums = df.select_dtypes(include=[np.number]).columns
    zero_var = [c for c in nums if df[c].std() == 0 and df[c].notna().sum() > 1]
    test("%s no zero-variance features" % ctx, not zero_var, "constant: %s" % zero_var if zero_var else "%d checked" % len(nums))

def print_summary():
    total = len(RESULTS)
    passed = sum(1 for r in RESULTS if r["passed"])
    failed = total - passed
    print("\n" + "=" * 60)
    print("  TEST SUMMARY: %d passed, %d failed, %d total" % (passed, failed, total))
    print("=" * 60)
    if failed:
        print("\nFAILED:")
        for r in RESULTS:
            if not r["passed"]:
                print("  [FAIL] %s - %s" % (r["name"], r["detail"]))
    return failed == 0

# ============================================================
# INPUT VALIDATION
# ============================================================
def validate_inputs():
    log("=" * 60)
    log("STEP 1: INPUT VALIDATION")
    log("=" * 60)

    # Boundaries
    sz = gpd.read_file(BASE + "/boundaries/subzones.geojson")
    test("subzones loaded", len(sz) > 0, "%d features" % len(sz))
    assert_row_count(sz, 330, 340, "subzones")
    assert_cols(sz, ["SUBZONE_N", "SUBZONE_C", "PLN_AREA_N", "REGION_N"], "subzones")
    assert_unique(sz, "SUBZONE_C", "subzones")

    # Places
    places = pd.read_json(BASE + "/places/sgp_places.jsonl", lines=True)
    test("places loaded", len(places) > 0, "%d records" % len(places))
    assert_row_count(places, 65000, 70000, "places")
    assert_cols(places, ["id", "name", "latitude", "longitude", "main_category", "place_type", "subzone"], "places")
    assert_unique(places, "id", "places")
    assert_range(places, "latitude", 1.15, 1.48, "places")
    assert_range(places, "longitude", 103.6, 104.1, "places")
    assert_no_leakage(places, ["google_place_id", "google_url"], "places")

    # ID format
    valid_ids = places["id"].apply(lambda x: len(str(x)) == 12 and str(x).isalnum()).all()
    test("places IDs 12-char alphanumeric", valid_ids)

    # Category coverage
    cats = places["main_category"].nunique()
    test("places has multiple categories", cats >= 15, "%d categories" % cats)

    # Subzone assignment
    assigned = places["subzone"].notna().sum()
    test("places subzone assigned", assigned / len(places) > 0.99, "%.1f%% assigned" % (assigned / len(places) * 100))

    # Demographics
    for f in ["pop_age_sex_fa_2025.csv", "pop_age_sex_tod_2025.csv", "dwellings_subzone_2025.csv"]:
        for d in ["demographics", "new_datasets"]:
            path = "%s/%s/%s" % (BASE, d, f)
            if os.path.exists(path):
                df = pd.read_csv(path)
                test("%s loaded" % f, len(df) > 0, "%d rows from %s/" % (len(df), d))
                break
        else:
            test("%s exists" % f, False, "not found")

    # Roads
    rpath = BASE + "/roads/roads.geojson"
    if os.path.exists(rpath):
        roads = gpd.read_file(rpath)
        test("roads loaded", len(roads) > 0, "%d edges" % len(roads))
        assert_row_count(roads, 400000, 700000, "roads")

    # Buildings
    bpath = BASE + "/buildings/buildings.geojson"
    if os.path.exists(bpath):
        bldgs = gpd.read_file(bpath)
        test("buildings loaded", len(bldgs) > 0, "%d features" % len(bldgs))

    # Land use
    lu = gpd.read_file(BASE + "/land_use/master_plan_land_use.geojson")
    test("land_use loaded", len(lu) > 0, "%d parcels" % len(lu))

    # Transit
    for f, mn in [("bus_stops_mar2026.geojson", 4000), ("train_stations_mar2026.geojson", 200)]:
        for d in ["transit_updated", "new_datasets"]:
            path = "%s/%s/%s" % (BASE, d, f)
            if os.path.exists(path):
                gdf = gpd.read_file(path)
                test("%s loaded" % f, len(gdf) >= mn, "%d features" % len(gdf))
                break

    # ACRA
    for d in ["business", "new_datasets"]:
        path = "%s/%s/acra_entities.csv" % (BASE, d)
        if os.path.exists(path):
            acra = pd.read_csv(path, low_memory=False, nrows=5)
            test("ACRA loadable", True, "from %s/" % d)
            break

    # Property
    for f in ["hdb_resale_prices.csv", "private_resi_transactions.csv"]:
        for d in ["property", "new_datasets"]:
            path = "%s/%s/%s" % (BASE, d, f)
            if os.path.exists(path):
                df = pd.read_csv(path, low_memory=False, nrows=5)
                test("%s loadable" % f, True, "from %s/" % d)
                break

    # SFA eating establishments
    for d in ["amenities_updated", "new_datasets"]:
        path = "%s/%s/eating_establishments_sfa.geojson" % (BASE, d)
        if os.path.exists(path):
            gdf = gpd.read_file(path)
            test("SFA eating establishments", len(gdf) > 30000, "%d features" % len(gdf))
            break

    # CHAS clinics
    for d in ["amenities_updated", "new_datasets"]:
        path = "%s/%s/chas_clinics.geojson" % (BASE, d)
        if os.path.exists(path):
            gdf = gpd.read_file(path)
            test("CHAS clinics", len(gdf) > 1000, "%d features" % len(gdf))
            break

    # Preschools
    for d in ["amenities_updated", "new_datasets"]:
        path = "%s/%s/preschools.geojson" % (BASE, d)
        if os.path.exists(path):
            gdf = gpd.read_file(path)
            test("Preschools", len(gdf) > 2000, "%d features" % len(gdf))
            break


# ============================================================
# INTERMEDIATE VALIDATION
# ============================================================
def validate_intermediate(filepath, ctx, min_rows=300, required_cols=None):
    log("Validating: %s" % ctx)
    test("%s exists" % ctx, os.path.exists(filepath))
    if not os.path.exists(filepath):
        return None
    df = pd.read_parquet(filepath)
    assert_row_count(df, min_rows, 340, ctx)
    if required_cols:
        assert_cols(df, required_cols, ctx)
    if "subzone_code" in df.columns:
        assert_no_nulls(df, ["subzone_code"], ctx)
    assert_distributions(df, ctx)
    return df


# ============================================================
# FINAL VALIDATION
# ============================================================
def validate_final():
    log("=" * 60)
    log("FINAL VALIDATION")
    log("=" * 60)

    fpath = "/home/azureuser/digital-atlas-sgp/final/subzone_features.parquet"
    if not os.path.exists(fpath):
        test("subzone_features.parquet exists", False)
        return

    df = pd.read_parquet(fpath)
    assert_row_count(df, 320, 335, "subzone_features")
    assert_cols(df, ["subzone_code", "subzone_name"], "subzone_features")
    assert_unique(df, "subzone_code", "subzone_features")
    assert_distributions(df, "subzone_features")
    assert_no_leakage(df, ["google"], "subzone_features")

    nums = df.select_dtypes(include=[np.number]).columns
    test("subzone_features >= 100 numeric features", len(nums) >= 100, "actual: %d" % len(nums))

    all_null = [c for c in nums if df[c].isna().all()]
    test("no all-null features", not all_null, "all null: %s" % all_null if all_null else "")

    # Null rate per feature
    null_rates = df[nums].isna().mean()
    high_null = null_rates[null_rates > 0.5]
    test(">50%% null features", len(high_null) == 0, "%d features" % len(high_null) if len(high_null) else "")

    # Correlation check
    if len(nums) > 5:
        corr = df[nums].corr().abs()
        np.fill_diagonal(corr.values, 0)
        high_corr_pairs = (corr > 0.95).sum().sum() // 2
        test("highly correlated pairs (r>0.95)", True, "%d pairs (info only)" % high_corr_pairs)

    # Place features
    ppath = "/home/azureuser/digital-atlas-sgp/final/place_features.parquet"
    if os.path.exists(ppath):
        pdf = pd.read_parquet(ppath)
        assert_row_count(pdf, 60000, 70000, "place_features")
        assert_cols(pdf, ["place_id", "subzone_code"], "place_features")
        assert_unique(pdf, "place_id", "place_features")
        assert_no_leakage(pdf, ["google"], "place_features")

        for col in [c for c in pdf.columns if "m" in c and any(r in c for r in ["100", "200", "500"])]:
            assert_range(pdf, col, 0, 9999, "place_features")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "inputs"

    if mode == "inputs":
        validate_inputs()
    elif mode == "final":
        validate_final()
    elif mode == "all":
        validate_inputs()
        validate_final()

    all_ok = print_summary()

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "mode": mode,
        "total": len(RESULTS),
        "passed": sum(1 for r in RESULTS if r["passed"]),
        "failed": sum(1 for r in RESULTS if not r["passed"]),
        "results": RESULTS
    }
    rpath = "/home/azureuser/digital-atlas-sgp/validation_report.json"
    with open(rpath, "w") as f:
        json.dump(report, f, indent=2)
    log("Report: %s" % rpath)

    sys.exit(0 if all_ok else 1)
