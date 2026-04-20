#!/usr/bin/env python3
"""
XGBoost Masked Category Predictor — Hex v10
Head-to-head comparison with GCN on IDENTICAL task, data, split.

Same setup as gcn_masked_hex.py:
  - 7,318 hexes
  - 391 context features (non-pc_*)
  - 24 category counts as targets (log1p transformed)
  - 30% random masking of categories
  - 5-fold cross validation
  - Same random seed

Three XGBoost variants:
  A. Physical only (no visible categories) — baseline
  B. Physical + visible categories with random 30% mask — matches GCN
  C. Leave-one-out per category (mask exactly 1, see other 23) — v5 style

Plus influence-graph features already baked into the 391 physical features
(sp_max_*, tr_max_* are the GCN's "graph propagation" in pre-computed form).
So this tests: does LEARNED graph propagation beat PRE-COMPUTED influence features?

Run ON SERVER.
"""
import numpy as np
import pandas as pd
import json, os, time
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score, mean_absolute_error

try:
    from xgboost import XGBRegressor
    HAS_XGB = True
except ImportError:
    from sklearn.ensemble import GradientBoostingRegressor as XGBRegressor
    HAS_XGB = False
    print("Warning: xgboost not installed, using sklearn GradientBoostingRegressor")

ROOT = "/home/azureuser/digital-atlas-sgp"
HEX_RAW = f"{ROOT}/data/hex_v10/hex_features_v10.parquet"
HEX_NORM = f"{ROOT}/data/hex_v10/hex_features_v10_normalized.parquet"
RESULTS = f"{ROOT}/data/hex_v10/xgboost_results"
os.makedirs(RESULTS, exist_ok=True)

def log(m):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), m), flush=True)

ID_COLS = {"hex_id","lat","lng","area_km2","parent_subzone","parent_subzone_name","parent_pa","parent_region"}
BK_COLS = {"subzone_pop_total","subzone_res_floor_area","residential_floor_weight"}
SEED = 42

def make_xgb():
    if HAS_XGB:
        return XGBRegressor(
            n_estimators=200, max_depth=5, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            reg_lambda=1.0, random_state=SEED, n_jobs=-1, verbosity=0,
        )
    else:
        return XGBRegressor(
            n_estimators=200, max_depth=5, learning_rate=0.05,
            subsample=0.8, random_state=SEED,
        )

def load_data():
    log("Loading hex v10 data...")
    raw = pd.read_parquet(HEX_RAW)
    norm = pd.read_parquet(HEX_NORM)

    cat_cols = sorted([c for c in raw.columns if c.startswith("pc_cat_") and
                       c not in {"pc_cat_hhi","pc_cat_entropy"}])
    target = raw[cat_cols].to_numpy(dtype=np.float32)
    target_log = np.log1p(target)

    feat_cols = [c for c in norm.columns if c not in ID_COLS and c not in BK_COLS]
    context_cols = [c for c in feat_cols if not c.startswith("pc_")]
    context = norm[context_cols].to_numpy(dtype=np.float32)
    stds = context.std(axis=0); keep = stds > 1e-9
    context = context[:, keep]

    log(f"  Context: {context.shape[1]}, Categories: {len(cat_cols)}, Hexes: {len(raw)}")
    return context, target_log, target, cat_cols

def evaluate_all_cats(y_true_log, y_pred_log, y_true_raw):
    """R² and MAE on RAW counts (after expm1)."""
    y_pred_raw = np.expm1(np.clip(y_pred_log, 0, None))
    r2s = []
    maes = []
    for j in range(y_true_log.shape[1]):
        ss_res = ((y_true_log[:, j] - y_pred_log[:, j]) ** 2).sum()
        ss_tot = ((y_true_log[:, j] - y_true_log[:, j].mean()) ** 2).sum()
        r2 = 1 - ss_res / max(ss_tot, 1e-9)
        r2s.append(r2)
        maes.append(np.abs(y_true_raw[:, j] - y_pred_raw[:, j]).mean())
    return np.array(r2s), np.array(maes)

# ============================================================
# VARIANT A: Physical only (baseline)
# ============================================================
def variant_a(context, target_log, target, cat_cols):
    log("\n=== Variant A: XGBoost physical-only (no visible categories) ===")
    n = len(context)
    kf = KFold(n_splits=5, shuffle=True, random_state=SEED)
    all_pred = np.zeros_like(target_log)
    for fold, (tr, va) in enumerate(kf.split(np.arange(n))):
        X_tr, X_va = context[tr], context[va]
        for j in range(len(cat_cols)):
            m = make_xgb()
            m.fit(X_tr, target_log[tr, j])
            all_pred[va, j] = m.predict(X_va)
        log(f"  Fold {fold+1}/5 done")
    r2s, maes = evaluate_all_cats(target_log, all_pred, target)
    return r2s, maes, all_pred

# ============================================================
# VARIANT B: Physical + random-masked visible categories (matches GCN)
# ============================================================
def variant_b(context, target_log, target, cat_cols, mask_rate=0.3):
    log(f"\n=== Variant B: XGBoost physical + {int(mask_rate*100)}%-masked visible categories ===")
    n = len(context)
    n_cats = len(cat_cols)
    kf = KFold(n_splits=5, shuffle=True, random_state=SEED)
    all_pred = np.zeros_like(target_log)
    rng = np.random.default_rng(SEED)

    for fold, (tr, va) in enumerate(kf.split(np.arange(n))):
        # For training: generate random masks, augment with visible categories
        # For each training sample, randomly mask 30% of categories and use the rest as features
        # Target is the MASKED categories
        # Simplification: generate one mask per sample, train 24 per-category models
        # Each sample: features = physical + (target with masked positions zeroed)
        #              target j = target_log[sample, j] IF j is masked, else not used

        # For reproducibility & fairness: we train each j-th model to predict target_log[:, j]
        # using physical features + target_log[:, other] with 30% of OTHERS masked
        # The j-th category is ALWAYS masked (that's the target).
        for j in range(n_cats):
            # Build training data: for each training sample, generate a mask that INCLUDES j
            # and has 30% of other categories masked
            n_mask_others = int(0.3 * (n_cats - 1))
            X_tr_parts = []
            y_tr_parts = []
            # Use multiple mask realizations per sample (data augmentation)
            n_aug = 3
            for aug in range(n_aug):
                # for each training sample, mask j + n_mask_others random other categories
                mask = np.zeros((len(tr), n_cats), dtype=bool)
                mask[:, j] = True  # always mask target
                for i in range(len(tr)):
                    other_idx = [k for k in range(n_cats) if k != j]
                    masked_others = rng.choice(other_idx, n_mask_others, replace=False)
                    mask[i, masked_others] = True
                # Features: physical + target_log with masked positions zeroed
                X_aug = np.hstack([context[tr], target_log[tr] * (1 - mask.astype(np.float32))])
                y_aug = target_log[tr, j]
                X_tr_parts.append(X_aug)
                y_tr_parts.append(y_aug)
            X_tr_all = np.vstack(X_tr_parts)
            y_tr_all = np.concatenate(y_tr_parts)

            # Validation: mask j + random 30% of others for each val sample, predict
            mask_va = np.zeros((len(va), n_cats), dtype=bool)
            mask_va[:, j] = True
            for i in range(len(va)):
                other_idx = [k for k in range(n_cats) if k != j]
                masked_others = rng.choice(other_idx, n_mask_others, replace=False)
                mask_va[i, masked_others] = True
            X_va = np.hstack([context[va], target_log[va] * (1 - mask_va.astype(np.float32))])

            m = make_xgb()
            m.fit(X_tr_all, y_tr_all)
            all_pred[va, j] = m.predict(X_va)

        log(f"  Fold {fold+1}/5 done")

    r2s, maes = evaluate_all_cats(target_log, all_pred, target)
    return r2s, maes, all_pred

# ============================================================
# VARIANT C: Leave-one-out (mask 1, see other 23) — v5 style
# ============================================================
def variant_c(context, target_log, target, cat_cols):
    log("\n=== Variant C: XGBoost leave-one-out (mask 1, see 23) ===")
    n = len(context)
    n_cats = len(cat_cols)
    kf = KFold(n_splits=5, shuffle=True, random_state=SEED)
    all_pred = np.zeros_like(target_log)

    for fold, (tr, va) in enumerate(kf.split(np.arange(n))):
        for j in range(n_cats):
            other_idx = [k for k in range(n_cats) if k != j]
            X_tr = np.hstack([context[tr], target_log[tr][:, other_idx]])
            X_va = np.hstack([context[va], target_log[va][:, other_idx]])
            y_tr = target_log[tr, j]
            m = make_xgb()
            m.fit(X_tr, y_tr)
            all_pred[va, j] = m.predict(X_va)
        log(f"  Fold {fold+1}/5 done")

    r2s, maes = evaluate_all_cats(target_log, all_pred, target)
    return r2s, maes, all_pred

# ============================================================
# MAIN
# ============================================================
def main():
    t0 = time.time()
    log("="*60)
    log("XGBOOST vs GCN — HEAD-TO-HEAD on hex v10")
    log("="*60)

    context, target_log, target, cat_cols = load_data()

    r2_a, mae_a, _ = variant_a(context, target_log, target, cat_cols)
    r2_b, mae_b, _ = variant_b(context, target_log, target, cat_cols)
    r2_c, mae_c, _ = variant_c(context, target_log, target, cat_cols)

    # GCN results (from previous run)
    gcn_path = f"{ROOT}/data/hex_v10/gcn_results/gcn_report.json"
    if os.path.exists(gcn_path):
        with open(gcn_path) as f:
            gcn_report = json.load(f)
        gcn_r2 = np.array([gcn_report["per_category_r2"][c] for c in cat_cols])
    else:
        gcn_r2 = None

    log("\n" + "="*60)
    log("RESULTS SUMMARY")
    log("="*60)
    log(f"\n{'Method':<45} {'Mean R²':>9} {'Mean MAE':>9}")
    log("-"*70)
    log(f"{'A. XGBoost physical-only':<45} {np.mean(r2_a):>9.3f} {np.mean(mae_a):>9.3f}")
    log(f"{'B. XGBoost phys + masked visible (GCN-match)':<45} {np.mean(r2_b):>9.3f} {np.mean(mae_b):>9.3f}")
    log(f"{'C. XGBoost leave-one-out (v5 style)':<45} {np.mean(r2_c):>9.3f} {np.mean(mae_c):>9.3f}")
    if gcn_r2 is not None:
        log(f"{'GCN masked prediction (previous)':<45} {np.mean(gcn_r2):>9.3f} {gcn_report['mean_mae']:>9.3f}")

    log("\n\nPer-category R² comparison:")
    log(f"{'Category':<32} {'A (phys)':>10} {'B (masked)':>12} {'C (LOO)':>10} {'GCN':>8} {'Winner':>10}")
    log("-"*90)
    for i, c in enumerate(cat_cols):
        name = c.replace("pc_cat_","")[:30]
        values = [("A", r2_a[i]), ("B", r2_b[i]), ("C", r2_c[i])]
        if gcn_r2 is not None:
            values.append(("GCN", gcn_r2[i]))
        winner = max(values, key=lambda x: x[1])
        gcn_str = f"{gcn_r2[i]:>8.3f}" if gcn_r2 is not None else "    —"
        log(f"  {name:<32} {r2_a[i]:>10.3f} {r2_b[i]:>12.3f} {r2_c[i]:>10.3f} {gcn_str} {winner[0]:>10}")

    # Save report
    report = {
        "task": "masked_category_prediction",
        "n_hexes": len(context),
        "n_context_features": context.shape[1],
        "n_categories": len(cat_cols),
        "variants": {
            "A_physical_only": {
                "mean_r2": float(np.mean(r2_a)),
                "mean_mae": float(np.mean(mae_a)),
                "per_category_r2": {c: float(r2_a[i]) for i, c in enumerate(cat_cols)},
            },
            "B_physical_plus_masked_visible": {
                "mean_r2": float(np.mean(r2_b)),
                "mean_mae": float(np.mean(mae_b)),
                "per_category_r2": {c: float(r2_b[i]) for i, c in enumerate(cat_cols)},
                "note": "matches GCN masking protocol",
            },
            "C_leave_one_out": {
                "mean_r2": float(np.mean(r2_c)),
                "mean_mae": float(np.mean(mae_c)),
                "per_category_r2": {c: float(r2_c[i]) for i, c in enumerate(cat_cols)},
            },
        },
        "gcn_comparison": {
            "mean_r2": float(np.mean(gcn_r2)) if gcn_r2 is not None else None,
            "per_category_r2": {c: float(gcn_r2[i]) for i, c in enumerate(cat_cols)} if gcn_r2 is not None else None,
        },
        "time_seconds": round(time.time() - t0),
    }
    with open(f"{RESULTS}/xgboost_report.json", "w") as f:
        json.dump(report, f, indent=2)

    log(f"\n\nWrote {RESULTS}/xgboost_report.json")
    log(f"Total time: {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
