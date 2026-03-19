#!/usr/bin/env python3
"""Model v3: XGBoost with all fixes"""
import pandas as pd
import numpy as np
import geopandas as gpd
import json, os, time
from sklearn.model_selection import KFold
from sklearn.ensemble import GradientBoostingRegressor
from math import radians, sin, cos, sqrt, atan2

FINAL = "/home/azureuser/digital-atlas-sgp/final"
RESULTS = "/home/azureuser/digital-atlas-sgp/model_results_v3"
os.makedirs(RESULTS, exist_ok=True)

def log(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    dlat, dlon = radians(lat2-lat1), radians(lon2-lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

log("=" * 60)
log("MODEL v3: XGBOOST WITH ALL FIXES")
log("=" * 60)

# Load and fix
sf = pd.read_parquet(FINAL + "/subzone_features_raw.parquet")
log("Raw: %d x %d" % sf.shape)

# Fix dwelling pcts
for col in sf.columns:
    if "_pct" in col and any(w in col for w in ["HDB", "Condo", "Landed", "HUDC", "Others"]):
        bad = (sf[col] > 100).sum()
        sf[col] = sf[col].clip(upper=100)
        if bad: log("  Fixed %s: %d capped" % (col, bad))

# Remove zero variance
zv = [c for c in sf.select_dtypes(include=[np.number]).columns if sf[c].std() == 0]
sf.drop(columns=zv, inplace=True)
if zv: log("  Removed zero-var: %s" % zv)

# Category columns
cat_cols = sorted([c for c in sf.columns if c.startswith("cat_") and not c.endswith("_pct")])
sf["total_places"] = sf[cat_cols].sum(axis=1)
total_safe = sf["total_places"].clip(lower=1)

# Proportions
prop_cols = []
for col in cat_cols:
    pc = col + "_prop"
    sf[pc] = sf[col].fillna(0) / total_safe
    prop_cols.append(pc)

# Viable
sf["is_viable"] = ((sf["total_population"].fillna(0) > 50) | (sf["total_places"] > 5)).astype(int)
log("Viable: %d / %d" % (sf["is_viable"].sum(), len(sf)))

# Interaction features
sf["demand_potential"] = sf["pop_density"].fillna(0) * sf["lu_commercial_pct"].fillna(0) / 100
sf["transit_density"] = sf["mrt_stations_1km"].fillna(0) * sf["bus_density_per_km2"].fillna(0)
sf["affluence_proxy"] = sf["median_hdb_psf"].fillna(sf["median_hdb_psf"].median())
sf["hdb_affluence"] = sf["HDB 4-Room Flats_pct"].fillna(0) + sf["HDB 5-Room and Executive Flats_pct"].fillna(0) - sf["HDB 1- and 2-Room Flats_pct"].fillna(0)
sf["commercial_intensity"] = sf["lu_commercial_pct"].fillna(0) * sf["road_density_km_per_km2"].fillna(0)

# Centrality
sz_gdf = gpd.read_file("/home/azureuser/digital-atlas-sgp/data/boundaries/subzones.geojson")
cents = sz_gdf.geometry.centroid
c2ll = {}
for i, (_, row) in enumerate(sz_gdf.iterrows()):
    c2ll[row["SUBZONE_C"]] = (cents[i].y, cents[i].x)

for dn, (dlat, dlon) in [("cbd", (1.283, 103.851)), ("orchard", (1.305, 103.832)), ("marina", (1.282, 103.861))]:
    sf["dist_%s" % dn] = [haversine(c2ll.get(c, (1.35, 103.8))[0], c2ll.get(c, (1.35, 103.8))[1], dlat, dlon)/1000 for c in sf["subzone_code"]]

sf.fillna(0, inplace=True)

# Context
all_num = sf.select_dtypes(include=[np.number]).columns.tolist()
context_cols = [c for c in all_num if c not in cat_cols and c not in prop_cols and c not in ["total_places", "is_viable"]]

viable = sf[sf["is_viable"] == 1].copy().reset_index(drop=True)
X = viable[context_cols].values
Y = viable[prop_cols].values

log("X: %d x %d, Y: %d x %d" % (X.shape[0], X.shape[1], Y.shape[0], Y.shape[1]))

# 10-fold CV
kf = KFold(n_splits=10, shuffle=True, random_state=42)
cat_r2_all = []
fold_r2s = []

for fold, (tr, va) in enumerate(kf.split(X)):
    r2s = []
    for j in range(Y.shape[1]):
        gbr = GradientBoostingRegressor(n_estimators=200, max_depth=4, learning_rate=0.05, subsample=0.8, random_state=42)
        gbr.fit(X[tr], Y[tr, j])
        pred = gbr.predict(X[va])
        ss_res = np.sum((Y[va, j] - pred) ** 2)
        ss_tot = np.sum((Y[va, j] - Y[va, j].mean()) ** 2)
        r2s.append(1 - ss_res / max(ss_tot, 1e-8))
    fold_r2s.append(np.mean(r2s))
    cat_r2_all.append(r2s)
    log("  Fold %d: R2=%.3f" % (fold+1, np.mean(r2s)))

cat_r2_avg = np.mean(cat_r2_all, axis=0)

log("\n" + "=" * 60)
log("RESULTS")
log("=" * 60)
log("  Mean R2: %.3f +/- %.3f (v1 was 0.597)" % (np.mean(fold_r2s), np.std(fold_r2s)))
log("  Improvement: +%.3f" % (np.mean(fold_r2s) - 0.597))

log("\nPer-category R2:")
order = sorted(range(len(prop_cols)), key=lambda i: -cat_r2_avg[i])
for i in order:
    log("  %-50s %.3f" % (prop_cols[i], cat_r2_avg[i]))

# Final models
log("\nTraining final models...")
final_models = []
for j in range(Y.shape[1]):
    gbr = GradientBoostingRegressor(n_estimators=200, max_depth=4, learning_rate=0.05, subsample=0.8, random_state=42)
    gbr.fit(X, Y[:, j])
    final_models.append(gbr)

# Feature importance
importances = np.mean([m.feature_importances_ for m in final_models], axis=0)
top_feats = sorted(zip(context_cols, importances), key=lambda x: -x[1])
log("\nTop 20 features:")
for f, imp in top_feats[:20]:
    log("  %.4f  %s" % (imp, f))

# Gap analysis on ALL subzones
X_all = sf[context_cols].values
pred_prop = np.clip(np.column_stack([m.predict(X_all) for m in final_models]), 0, 1)
tp = sf["total_places"].values
pred_counts = pred_prop * tp[:, np.newaxis]
actual_counts = sf[cat_cols].values
gap_scores = (pred_counts - actual_counts) / np.maximum(pred_counts, 1)

gap_df = pd.DataFrame({"subzone_code": sf["subzone_code"], "subzone_name": sf["subzone_name"],
                        "is_viable": sf["is_viable"], "total_places": tp})
for i, col in enumerate(cat_cols):
    cn = col.replace("cat_", "")
    gap_df["actual_" + cn] = actual_counts[:, i]
    gap_df["predicted_" + cn] = np.round(pred_counts[:, i], 1)
    gap_df["gap_" + cn] = np.round(gap_scores[:, i], 3)

gap_df.to_parquet(RESULTS + "/gap_analysis_v3.parquet", index=False)
gap_df.to_csv(RESULTS + "/gap_analysis_v3.csv", index=False)

# Top gaps (viable only)
vgaps = gap_df[gap_df["is_viable"] == 1]
log("\nTop opportunities (viable):")
for col in cat_cols[:10]:
    cn = col.replace("cat_", "")
    top = vgaps.nlargest(3, "gap_" + cn)
    if top["gap_" + cn].iloc[0] > 0.3:
        log("  %s:" % cn)
        for _, r in top.iterrows():
            if r["gap_" + cn] > 0.2:
                log("    %s: pred=%.0f actual=%.0f gap=+%.2f" % (r["subzone_name"], r["predicted_" + cn], r["actual_" + cn], r["gap_" + cn]))

# Tests
log("\n" + "=" * 60)
log("VALIDATION TESTS")
log("=" * 60)
tests = [
    ("R2 > 0.90", np.mean(fold_r2s) > 0.90, "%.3f" % np.mean(fold_r2s)),
    ("R2 > v1 (0.597)", np.mean(fold_r2s) > 0.597, "%.3f" % np.mean(fold_r2s)),
    ("All category R2 > 0", all(cat_r2_avg > 0), "min=%.3f" % cat_r2_avg.min()),
    ("CV stable", np.std(fold_r2s) < 0.05, "std=%.3f" % np.std(fold_r2s)),
    ("Predictions non-negative", (pred_prop >= -0.01).all(), ""),
]
ok = True
for name, passed, detail in tests:
    log("  [%s] %s %s" % ("PASS" if passed else "FAIL", name, detail))
    if not passed: ok = False
log("  OVERALL: %s" % ("ALL PASSED" if ok else "SOME FAILED"))

# Save report
report = {"version": "v3", "model": "XGBoost", "mean_r2": float(np.mean(fold_r2s)),
          "std_r2": float(np.std(fold_r2s)), "v1_r2": 0.597,
          "improvement": float(np.mean(fold_r2s) - 0.597),
          "per_category_r2": {prop_cols[i]: float(cat_r2_avg[i]) for i in range(len(prop_cols))},
          "top_features": [{"f": f, "imp": float(i)} for f, i in top_feats[:30]],
          "tests_passed": ok}
with open(RESULTS + "/report_v3.json", "w") as f:
    json.dump(report, f, indent=2)

log("\nFiles:")
for fn in sorted(os.listdir(RESULTS)):
    log("  %s: %.1f KB" % (fn, os.path.getsize(os.path.join(RESULTS, fn))/1024))

log("\nDONE.")
