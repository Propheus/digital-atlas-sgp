#!/usr/bin/env python3
"""
Model v4: STRICT mode
- NO category _pct features (no data leakage)
- NO category count features in context
- NO place type count features in context
- ONLY physical/demographic/economic features predict composition
- This is the TRUE test: can urban structure predict what places exist?
"""
import pandas as pd
import numpy as np
import geopandas as gpd
import json, os, time
from sklearn.model_selection import KFold
from sklearn.ensemble import GradientBoostingRegressor
from math import radians, sin, cos, sqrt, atan2

FINAL = "/home/azureuser/digital-atlas-sgp/final"
RESULTS = "/home/azureuser/digital-atlas-sgp/model_results_v4"
os.makedirs(RESULTS, exist_ok=True)

def log(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    dlat, dlon = radians(lat2-lat1), radians(lon2-lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

log("=" * 70)
log("MODEL v4: STRICT — PHYSICAL FEATURES ONLY → PREDICT COMPOSITION")
log("=" * 70)

# ============================================================
# LOAD AND FIX
# ============================================================
sf = pd.read_parquet(FINAL + "/subzone_features_raw.parquet")

# Fix dwelling bugs
for col in sf.columns:
    if "_pct" in col and any(w in col for w in ["HDB", "Condo", "Landed", "HUDC", "Others"]):
        sf[col] = sf[col].clip(upper=100)

# Remove zero variance
zv = [c for c in sf.select_dtypes(include=[np.number]).columns if sf[c].std() == 0]
sf.drop(columns=zv, inplace=True)

# Category columns (TARGETS)
cat_cols = sorted([c for c in sf.columns if c.startswith("cat_") and not c.endswith("_pct")])
sf["total_places"] = sf[cat_cols].sum(axis=1)
total_safe = sf["total_places"].clip(lower=1)

# Proportion targets
prop_cols = []
for col in cat_cols:
    pc = col + "_prop"
    sf[pc] = sf[col].fillna(0) / total_safe
    prop_cols.append(pc)

# Viable
sf["is_viable"] = ((sf["total_population"].fillna(0) > 50) | (sf["total_places"] > 5)).astype(int)

# ============================================================
# STRICT CONTEXT: NO PLACE DATA LEAKAGE
# ============================================================
log("\nBuilding STRICT context features (no place/category info)...")

# Forbidden patterns - anything derived from places
forbidden = ["cat_", "type_", "prop", "total_place", "place_density",
             "category_entropy", "branded", "unique_brand", "avg_rating",
             "median_rating", "rating_std", "high_rated", "total_review",
             "has_phone", "has_website", "sfa_eating", "our_place", "our_fnb",
             "fnb_coverage", "chas_clinic_count", "preschool_count_gov"]

all_num = sf.select_dtypes(include=[np.number]).columns.tolist()
context_cols = []
for c in all_num:
    if c in ["is_viable", "total_places"]:
        continue
    if any(f in c for f in forbidden):
        continue
    context_cols.append(c)

log("  Context features (STRICT): %d" % len(context_cols))
log("  Excluded (place-derived): %d" % (len(all_num) - len(context_cols)))

# Add interaction features
sf["demand_potential"] = sf["pop_density"].fillna(0) * sf["lu_commercial_pct"].fillna(0) / 100
sf["transit_density"] = sf["mrt_stations_1km"].fillna(0) * sf["bus_density_per_km2"].fillna(0)
sf["affluence_proxy"] = sf["median_hdb_psf"].fillna(sf["median_hdb_psf"].median())
sf["hdb_affluence"] = (sf["HDB 4-Room Flats_pct"].fillna(0) +
                       sf["HDB 5-Room and Executive Flats_pct"].fillna(0) -
                       sf["HDB 1- and 2-Room Flats_pct"].fillna(0))
sf["commercial_intensity"] = sf["lu_commercial_pct"].fillna(0) * sf["road_density_km_per_km2"].fillna(0)
sf["residential_density"] = sf["total_population"].fillna(0) / sf["area_km2"].clip(lower=0.01)
sf["mixed_use_score"] = sf["lu_entropy"].fillna(0) * sf["road_density_km_per_km2"].fillna(0)
sf["green_access"] = sf["green_ratio"].fillna(0) * (1 / sf["dist_nearest_park"].clip(lower=100) * 1000)
sf["transit_premium"] = (1 / sf["dist_nearest_mrt"].clip(lower=100)) * 10000

interaction_cols = ["demand_potential", "transit_density", "affluence_proxy",
                    "hdb_affluence", "commercial_intensity", "residential_density",
                    "mixed_use_score", "green_access", "transit_premium"]
context_cols += interaction_cols

# Centrality
sz_gdf = gpd.read_file("/home/azureuser/digital-atlas-sgp/data/boundaries/subzones.geojson")
cents = sz_gdf.geometry.centroid
c2ll = {row["SUBZONE_C"]: (cents[i].y, cents[i].x) for i, (_, row) in enumerate(sz_gdf.iterrows())}

destinations = {
    "cbd": (1.283, 103.851), "orchard": (1.305, 103.832),
    "marina": (1.282, 103.861), "changi": (1.364, 103.992),
    "jurong": (1.333, 103.744), "woodlands": (1.437, 103.787),
    "sentosa": (1.249, 103.830), "clarke_quay": (1.290, 103.846),
}

for dn, (dlat, dlon) in destinations.items():
    col = "dist_%s" % dn
    sf[col] = [haversine(c2ll.get(c, (1.35, 103.8))[0], c2ll.get(c, (1.35, 103.8))[1], dlat, dlon)/1000 for c in sf["subzone_code"]]
    context_cols.append(col)

sf["min_dist_destination"] = sf[["dist_%s" % d for d in destinations]].min(axis=1)
context_cols.append("min_dist_destination")

sf.fillna(0, inplace=True)

log("  Final context features: %d" % len(context_cols))

# Print feature groups
groups = {
    "Demographics": [c for c in context_cols if any(w in c for w in ["pop", "age_", "male", "female", "dependency", "area_km"])],
    "Dwelling": [c for c in context_cols if any(w in c for w in ["HDB", "Condo", "Landed", "Others_pct"])],
    "Property": [c for c in context_cols if any(w in c for w in ["hdb_psf", "hdb_price", "hdb_transaction", "price_yoy", "affluence"])],
    "Roads": [c for c in context_cols if "road" in c and "road_density" not in c or c == "road_density_km_per_km2"],
    "Land Use": [c for c in context_cols if c.startswith("lu_") or c in ["avg_gpr", "green_ratio", "green_access", "mixed_use"]],
    "Transit": [c for c in context_cols if any(w in c for w in ["mrt", "bus_", "dist_nearest_mrt", "transit"])],
    "Amenities": [c for c in context_cols if any(w in c for w in ["park", "hawker", "school", "supermarket", "hotel_count"])],
    "Centrality": [c for c in context_cols if c.startswith("dist_") and c not in ["dist_nearest_mrt", "dist_nearest_park", "dist_nearest_hawker", "dist_nearest_supermarket", "dist_nearest_school"]],
    "Interactions": interaction_cols,
}
for gname, gcols in groups.items():
    if gcols:
        log("    %s: %d features" % (gname, len(gcols)))

# ============================================================
# TRAIN
# ============================================================
viable = sf[sf["is_viable"] == 1].copy().reset_index(drop=True)
X = viable[context_cols].values
Y = viable[prop_cols].values
log("\nTraining: X=%d x %d, Y=%d x %d" % (X.shape[0], X.shape[1], Y.shape[0], Y.shape[1]))

# Also predict total_place_count as extra target (useful for gap analysis)
Y_total = viable["total_places"].values

# 10-fold CV
kf = KFold(n_splits=10, shuffle=True, random_state=42)
cat_r2_all = []
total_r2_all = []
fold_results = []

for fold, (tr, va) in enumerate(kf.split(X)):
    r2s = []
    maes = []
    for j in range(Y.shape[1]):
        gbr = GradientBoostingRegressor(n_estimators=300, max_depth=5, learning_rate=0.05,
                                         subsample=0.8, min_samples_leaf=5, random_state=42)
        gbr.fit(X[tr], Y[tr, j])
        pred = gbr.predict(X[va])
        ss_res = np.sum((Y[va, j] - pred) ** 2)
        ss_tot = np.sum((Y[va, j] - Y[va, j].mean()) ** 2)
        r2s.append(1 - ss_res / max(ss_tot, 1e-8))
        # MAE in count space
        pred_count = pred * viable["total_places"].values[va]
        true_count = viable[cat_cols[j]].values[va]
        maes.append(np.mean(np.abs(pred_count - true_count)))

    # Also predict total places
    gbr_total = GradientBoostingRegressor(n_estimators=300, max_depth=5, learning_rate=0.05,
                                           subsample=0.8, min_samples_leaf=5, random_state=42)
    gbr_total.fit(X[tr], np.log1p(Y_total[tr]))
    pred_total = np.expm1(gbr_total.predict(X[va]))
    ss_res = np.sum((Y_total[va] - pred_total) ** 2)
    ss_tot = np.sum((Y_total[va] - Y_total[va].mean()) ** 2)
    total_r2 = 1 - ss_res / max(ss_tot, 1e-8)
    total_r2_all.append(total_r2)

    cat_r2_all.append(r2s)
    fold_r2 = np.mean(r2s)
    fold_mae = np.mean(maes)
    fold_results.append({"r2": fold_r2, "mae": fold_mae, "total_r2": total_r2})
    log("  Fold %d: R2=%.3f  MAE=%.2f  TotalR2=%.3f" % (fold+1, fold_r2, fold_mae, total_r2))

cat_r2_avg = np.mean(cat_r2_all, axis=0)
mean_r2 = np.mean([f["r2"] for f in fold_results])
mean_mae = np.mean([f["mae"] for f in fold_results])
mean_total_r2 = np.mean(total_r2_all)

# ============================================================
# RESULTS
# ============================================================
log("\n" + "=" * 70)
log("v4 STRICT RESULTS (no place data in features)")
log("=" * 70)
log("  Category proportion R2: %.3f +/- %.3f" % (mean_r2, np.std([f["r2"] for f in fold_results])))
log("  Category count MAE:     %.2f +/- %.2f" % (mean_mae, np.std([f["mae"] for f in fold_results])))
log("  Total places R2:        %.3f" % mean_total_r2)
log("")
log("  Comparison:")
log("    v1 (GCN-MLP, counts):        R2 = 0.597")
log("    v3 (XGBoost, with leakage):  R2 = 0.970  <- inflated by cat_pct features")
log("    v4 (XGBoost, STRICT):        R2 = %.3f  <- TRUE urban structure signal" % mean_r2)

log("\nPer-category R2 (STRICT):")
log("  %-45s  v4_R2   v1_R2" % "Category")
log("  " + "-" * 65)
v1_r2s = {"cat_beauty_personal_care": 0.830, "cat_convenience_daily_needs": 0.773,
           "cat_business": 0.746, "cat_services": 0.742, "cat_fitness_recreation": 0.713,
           "cat_hawker_street_food": 0.699, "cat_fast_food_qsr": 0.691,
           "cat_office_workspace": 0.684, "cat_cafe_coffee": 0.670,
           "cat_bakery_pastry": 0.667, "cat_restaurant": 0.630, "cat_general": 0.628,
           "cat_residential": 0.568, "cat_shopping_retail": 0.556,
           "cat_health_medical": 0.556, "cat_religious": 0.552,
           "cat_education": 0.549, "cat_transport": 0.544, "cat_ngo": 0.543,
           "cat_automotive": 0.531, "cat_civic_government": 0.453,
           "cat_culture_entertainment": 0.425, "cat_bar_nightlife": 0.322,
           "cat_hospitality": 0.248}

order = sorted(range(len(prop_cols)), key=lambda i: -cat_r2_avg[i])
for i in order:
    cat_name = prop_cols[i].replace("_prop", "")
    v1 = v1_r2s.get(cat_name, 0)
    delta = cat_r2_avg[i] - v1
    log("  %-45s  %.3f   %.3f  %+.3f" % (prop_cols[i], cat_r2_avg[i], v1, delta))

# ============================================================
# TRAIN FINAL MODELS
# ============================================================
log("\nTraining final models on all viable data...")
final_models = []
for j in range(Y.shape[1]):
    gbr = GradientBoostingRegressor(n_estimators=300, max_depth=5, learning_rate=0.05,
                                     subsample=0.8, min_samples_leaf=5, random_state=42)
    gbr.fit(X, Y[:, j])
    final_models.append(gbr)

# Total places model
gbr_total = GradientBoostingRegressor(n_estimators=300, max_depth=5, learning_rate=0.05,
                                       subsample=0.8, min_samples_leaf=5, random_state=42)
gbr_total.fit(X, np.log1p(Y_total))

# Feature importance (averaged across all category models)
importances = np.mean([m.feature_importances_ for m in final_models], axis=0)
top_feats = sorted(zip(context_cols, importances), key=lambda x: -x[1])

log("\nTop 25 most important features (TRUE urban structure signals):")
for f, imp in top_feats[:25]:
    log("  %.4f  %s" % (imp, f))

# ============================================================
# GAP ANALYSIS
# ============================================================
log("\n" + "=" * 70)
log("GAP ANALYSIS")
log("=" * 70)

X_all = sf[context_cols].values
pred_prop = np.clip(np.column_stack([m.predict(X_all) for m in final_models]), 0, 1)
pred_total = np.expm1(gbr_total.predict(X_all)).clip(min=0)

# Use predicted total for gaps (not actual — avoids circular reasoning)
pred_counts = pred_prop * pred_total[:, np.newaxis]
actual_counts = sf[cat_cols].values

gaps = pred_counts - actual_counts
gap_scores = gaps / np.maximum(pred_counts, 1)

# Build gap DataFrame
gap_df = pd.DataFrame({
    "subzone_code": sf["subzone_code"],
    "subzone_name": sf["subzone_name"],
    "is_viable": sf["is_viable"],
    "actual_total": sf["total_places"],
    "predicted_total": np.round(pred_total, 0),
})

for i, col in enumerate(cat_cols):
    cn = col.replace("cat_", "")
    gap_df["actual_" + cn] = actual_counts[:, i]
    gap_df["predicted_" + cn] = np.round(pred_counts[:, i], 1)
    gap_df["gap_score_" + cn] = np.round(gap_scores[:, i], 3)

gap_df.to_parquet(RESULTS + "/gap_analysis_v4.parquet", index=False)
gap_df.to_csv(RESULTS + "/gap_analysis_v4.csv", index=False)

# Show meaningful gaps (viable, predicted > 2, gap > 0.3)
log("\nTop opportunity gaps (viable, predicted > 2 places, gap > 30%):")
vgaps = gap_df[gap_df["is_viable"] == 1]
for col in cat_cols:
    cn = col.replace("cat_", "")
    gc = "gap_score_" + cn
    pc = "predicted_" + cn
    ac = "actual_" + cn

    candidates = vgaps[(vgaps[pc] > 2) & (vgaps[gc] > 0.3)].nlargest(5, gc)
    if len(candidates) > 0:
        log("\n  %s:" % cn)
        for _, r in candidates.iterrows():
            log("    %-25s pred=%4.0f actual=%3.0f gap=+%.0f%%" % (
                r["subzone_name"], r[pc], r[ac], r[gc]*100))

# ============================================================
# VALIDATION TESTS
# ============================================================
log("\n" + "=" * 70)
log("VALIDATION TESTS")
log("=" * 70)

tests = [
    ("STRICT R2 > 0.50", mean_r2 > 0.50, "%.3f" % mean_r2),
    ("STRICT R2 > v1 (0.597)", mean_r2 > 0.597, "%.3f vs 0.597" % mean_r2),
    ("All category R2 > 0", all(cat_r2_avg > 0), "min=%.3f" % cat_r2_avg.min()),
    ("Most categories R2 > 0.5", sum(cat_r2_avg > 0.5) >= 15, "%d/24 > 0.5" % sum(cat_r2_avg > 0.5)),
    ("Total places R2 > 0.7", mean_total_r2 > 0.7, "%.3f" % mean_total_r2),
    ("CV stable", np.std([f["r2"] for f in fold_results]) < 0.1, "std=%.3f" % np.std([f["r2"] for f in fold_results])),
    ("No leakage in features", not any("cat_" in c for c in context_cols), ""),
    ("No type_ in features", not any("type_" in c for c in context_cols), ""),
    ("Predictions non-negative", (pred_prop >= -0.01).all(), ""),
]

ok = True
for name, passed, detail in tests:
    status = "PASS" if passed else "FAIL"
    log("  [%s] %s %s" % (status, name, detail))
    if not passed: ok = False
log("  OVERALL: %s" % ("ALL PASSED" if ok else "SOME FAILED"))

# ============================================================
# SAVE
# ============================================================
report = {
    "version": "v4_strict",
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "description": "XGBoost predicting category proportions from PHYSICAL features only (no place data leakage)",
    "model": "GradientBoostingRegressor(n=300, depth=5, lr=0.05)",
    "viable_subzones": int(sf["is_viable"].sum()),
    "context_features": len(context_cols),
    "context_feature_list": context_cols,
    "target_categories": len(prop_cols),
    "mean_r2": float(mean_r2),
    "std_r2": float(np.std([f["r2"] for f in fold_results])),
    "mean_mae_counts": float(mean_mae),
    "total_places_r2": float(mean_total_r2),
    "comparison": {"v1_gcn_mlp": 0.597, "v3_xgb_leaky": 0.970, "v4_xgb_strict": float(mean_r2)},
    "per_category_r2": {prop_cols[i]: float(cat_r2_avg[i]) for i in range(len(prop_cols))},
    "top_features": [{"feature": f, "importance": float(imp)} for f, imp in top_feats[:40]],
    "all_tests_passed": ok,
    "fold_results": fold_results,
}

with open(RESULTS + "/report_v4.json", "w") as f:
    json.dump(report, f, indent=2, default=str)

log("\nFiles:")
for fn in sorted(os.listdir(RESULTS)):
    log("  %s: %.1f KB" % (fn, os.path.getsize(os.path.join(RESULTS, fn))/1024))

log("\n" + "=" * 70)
log("DONE. STRICT R2 = %.3f (v1=0.597, v3_leaky=0.970)" % mean_r2)
log("=" * 70)
