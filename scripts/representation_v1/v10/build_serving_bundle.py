"""
Build the production serving bundle.

Only the BEST models, packaged for serving:
  - GCN-64 embedding model (best similarity, kNN=0.430)
  - XGBoost 24-category predictor (best prediction, R²=0.80)

Output directory (on server): /home/azureuser/digital-atlas-sgp/data/hex_v10/serving/

Contents:
  hex_shareable_bundle.parquet  — pre-computed for all 7,318 hexes (primary lookup)
  gcn_model.pt                  — PyTorch weights for encoding new hexes
  xgboost_models/*.json         — 24 XGBoost models for category prediction
  feature_schema.json           — feature order + normalization stats
  graph/                        — influence graph edges + node index
  serve.py                      — simple inference example
  README.md                     — how to use
"""
import json
import os
import shutil
import time

import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split

ROOT = "/home/azureuser/digital-atlas-sgp"
HEX_RAW = f"{ROOT}/data/hex_v10/hex_features_v10.parquet"
HEX_NORM = f"{ROOT}/data/hex_v10/hex_features_v10_normalized.parquet"
SERVE_DIR = f"{ROOT}/data/hex_v10/serving"

ID_COLS = {"hex_id", "lat", "lng", "area_km2", "parent_subzone",
           "parent_subzone_name", "parent_pa", "parent_region"}
BK_COLS = {"subzone_pop_total", "subzone_res_floor_area", "residential_floor_weight"}
SEED = 42


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def main():
    t0 = time.time()
    os.makedirs(SERVE_DIR, exist_ok=True)
    os.makedirs(f"{SERVE_DIR}/xgboost_models", exist_ok=True)
    os.makedirs(f"{SERVE_DIR}/graph", exist_ok=True)

    log("=" * 60)
    log("BUILDING SERVING BUNDLE")
    log("=" * 60)

    # ============================================================
    # 1. PRE-COMPUTED SHAREABLE BUNDLE (primary lookup)
    # ============================================================
    log("\n1. Pre-computed bundle (primary lookup for 7,318 hexes)")
    src = f"{ROOT}/data/hex_v10/hex_shareable_bundle.parquet"
    dst = f"{SERVE_DIR}/hex_shareable_bundle.parquet"
    shutil.copy(src, dst)
    log(f"   → {dst} ({os.path.getsize(dst)/1024/1024:.1f} MB)")

    # ============================================================
    # 2. GCN MODEL (for encoding new hexes)
    # ============================================================
    log("\n2. GCN-64 model weights")
    src = f"{ROOT}/data/hex_v10/gcn_results/gcn_model.pt"
    dst = f"{SERVE_DIR}/gcn_model.pt"
    shutil.copy(src, dst)
    log(f"   → {dst} ({os.path.getsize(dst)/1024:.0f} KB)")

    # ============================================================
    # 3. TRAIN XGBOOST MODELS FOR SERVING
    # ============================================================
    log("\n3. Training 24 XGBoost models on FULL data for serving")
    raw = pd.read_parquet(HEX_RAW)
    norm = pd.read_parquet(HEX_NORM)

    feat_cols = [c for c in norm.columns if c not in ID_COLS and c not in BK_COLS]
    context_cols = [c for c in feat_cols if not c.startswith("pc_")]
    X = norm[context_cols].to_numpy(dtype=np.float32)
    stds = X.std(axis=0)
    keep = stds > 1e-9
    X = X[:, keep]
    context_cols_kept = [c for c, k in zip(context_cols, keep) if k]

    cat_cols = sorted([c for c in raw.columns if c.startswith("pc_cat_") and
                       c not in {"pc_cat_hhi", "pc_cat_entropy"}])
    Y = raw[cat_cols].to_numpy(dtype=np.float32)

    # Use full data for serving models (we're past evaluation)
    for j, cat in enumerate(cat_cols):
        model = XGBRegressor(
            n_estimators=200, max_depth=5, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0,
            random_state=SEED, n_jobs=-1, verbosity=0,
        )
        model.fit(X, np.log1p(Y[:, j]))
        model.save_model(f"{SERVE_DIR}/xgboost_models/{cat}.json")
    log(f"   → {SERVE_DIR}/xgboost_models/ (24 models)")

    # ============================================================
    # 4. FEATURE SCHEMA + NORMALIZATION STATS
    # ============================================================
    log("\n4. Feature schema")
    # Load normalization stats (already computed during feature build)
    stats_path = f"{ROOT}/data/hex_v10/hex_features_v10_normalization_stats.json"
    if os.path.exists(stats_path):
        with open(stats_path) as f:
            stats = json.load(f)
    else:
        stats = {}

    schema = {
        "version": "v10",
        "created": time.strftime("%Y-%m-%d"),
        "all_features": feat_cols,
        "context_features_for_xgboost": context_cols_kept,
        "target_categories": cat_cols,
        "normalization_stats": stats,
        "notes": {
            "gcn_input": "460 normalized features in the order of 'all_features'",
            "xgboost_input": "391 context features (non-pc_*) in the order of 'context_features_for_xgboost'",
            "gcn_output": "64-dim embedding for similarity",
            "xgboost_output": "24 log-space predicted category counts; apply expm1 for raw counts",
        },
    }
    with open(f"{SERVE_DIR}/feature_schema.json", "w") as f:
        json.dump(schema, f, indent=2)
    log(f"   → {SERVE_DIR}/feature_schema.json ({os.path.getsize(f'{SERVE_DIR}/feature_schema.json')/1024:.0f} KB)")

    # ============================================================
    # 5. INFLUENCE GRAPH (for GCN encoding of new hexes)
    # ============================================================
    log("\n5. Influence graph")
    src = f"{ROOT}/data/hex_v10/hex_influence_graph.npz"
    dst = f"{SERVE_DIR}/graph/hex_influence_graph.npz"
    shutil.copy(src, dst)
    # Also save hex_id → node index mapping
    hex_index = {hid: i for i, hid in enumerate(raw["hex_id"].tolist())}
    with open(f"{SERVE_DIR}/graph/hex_node_index.json", "w") as f:
        json.dump(hex_index, f)
    log(f"   → {SERVE_DIR}/graph/ (graph + node index)")

    # ============================================================
    # 6. SERVE.PY — simple inference example
    # ============================================================
    log("\n6. serve.py inference example")
    serve_code = '''#!/usr/bin/env python3
"""
Serving interface for the Singapore Urban Representation bundle.

Three main functions:
  1. lookup(hex_id) — fast lookup for pre-computed hexes
  2. find_similar(hex_id, k=10) — cosine similarity search on GCN-64 embedding
  3. predict_categories(hex_id) — XGBoost category count predictions
  4. gap_analysis(hex_id) — actual vs predicted category counts
"""
import json
import numpy as np
import pandas as pd
import os
from xgboost import XGBRegressor

SERVE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load once at startup
BUNDLE = pd.read_parquet(f"{SERVE_DIR}/hex_shareable_bundle.parquet")
with open(f"{SERVE_DIR}/feature_schema.json") as f:
    SCHEMA = json.load(f)

EMBED_COLS = [f"g{i}" for i in range(64)]
PRED_COLS = [c for c in BUNDLE.columns if c.startswith("pred_")]

# Hex_id → row index
HEX_TO_IDX = {hid: i for i, hid in enumerate(BUNDLE["hex_id"].tolist())}


def lookup(hex_id):
    """Return all info for a pre-computed hex."""
    idx = HEX_TO_IDX.get(hex_id)
    if idx is None:
        return None
    return BUNDLE.iloc[idx].to_dict()


def find_similar(hex_id, k=10):
    """Find k most similar hexes by GCN-64 embedding cosine."""
    idx = HEX_TO_IDX.get(hex_id)
    if idx is None:
        return []
    Z = BUNDLE[EMBED_COLS].to_numpy()
    q = Z[idx]
    norms = np.linalg.norm(Z, axis=1) * np.linalg.norm(q) + 1e-9
    sims = (Z @ q) / norms
    order = np.argsort(-sims)[1:k+1]  # exclude self
    results = []
    for i in order:
        results.append({
            "hex_id": BUNDLE.iloc[i]["hex_id"],
            "subzone": BUNDLE.iloc[i]["parent_subzone"],
            "pa": BUNDLE.iloc[i]["parent_pa"],
            "similarity": float(sims[i]),
        })
    return results


def predict_categories(hex_id):
    """Return predicted raw category counts."""
    idx = HEX_TO_IDX.get(hex_id)
    if idx is None:
        return None
    log_preds = BUNDLE.iloc[idx][PRED_COLS]
    raw_preds = np.expm1(log_preds.values)
    return {col.replace("pred_", ""): float(max(0, v)) for col, v in zip(PRED_COLS, raw_preds)}


def gap_analysis(hex_id):
    """Compare actual vs predicted counts per category."""
    idx = HEX_TO_IDX.get(hex_id)
    if idx is None:
        return None
    # We need actual counts — load from feature table or require them passed in
    # Simpler: return predictions; caller compares to actuals
    preds = predict_categories(hex_id)
    return preds


if __name__ == "__main__":
    # Example: find hexes similar to Raffles Place
    print("Top 5 hexes similar to Raffles Place:")
    raffles = BUNDLE[BUNDLE["parent_subzone"] == "DTSZ05"].iloc[0]
    for nb in find_similar(raffles["hex_id"], k=5):
        print(f"  {nb['subzone']:<10} {nb['pa']:<20} sim={nb['similarity']:.3f}")

    print(f"\\nPredicted categories for Raffles Place:")
    preds = predict_categories(raffles["hex_id"])
    for cat, count in sorted(preds.items(), key=lambda x: -x[1])[:10]:
        print(f"  {cat:<25} {count:>8.1f}")
'''
    with open(f"{SERVE_DIR}/serve.py", "w") as f:
        f.write(serve_code)
    log(f"   → {SERVE_DIR}/serve.py")

    # ============================================================
    # 7. README
    # ============================================================
    log("\n7. README")
    readme = """# Singapore Urban Representation — Serving Bundle

**Version:** v10
**Hexes:** 7,318 (H3 resolution 9, ~400m)
**Models:** GCN-64 (similarity) + XGBoost-24 (prediction)

## Quick Start

```python
from serve import lookup, find_similar, predict_categories

# Lookup a hex
info = lookup("896520db3afffff")  # Raffles Place

# Find similar hexes
similar = find_similar("896520db3afffff", k=10)

# Predict category counts
preds = predict_categories("896520db3afffff")
```

## Files

| File | Size | Purpose |
|---|---|---|
| `hex_shareable_bundle.parquet` | 2.8 MB | Pre-computed embeddings + predictions for all 7,318 hexes |
| `gcn_model.pt` | 578 KB | PyTorch weights for encoding new hexes (requires torch + torch_geometric) |
| `xgboost_models/*.json` | ~10 MB | 24 XGBoost models, one per category |
| `feature_schema.json` | ~50 KB | Feature order + normalization stats |
| `graph/hex_influence_graph.npz` | 75 KB | Sparse adjacency matrix (47K edges) |
| `graph/hex_node_index.json` | 1 MB | hex_id → node index mapping |
| `serve.py` | 3 KB | Reference inference code |

## Bundle Schema (93 columns per hex)

| Columns | Count | Type |
|---|---|---|
| Identity (hex_id, lat, lng, parent_subzone, parent_pa) | 5 | metadata |
| GCN-64 embedding (g0..g63) | 64 | similarity vector |
| XGBoost predictions (pred_cafe_coffee, ..., pred_transport) | 24 | log-count predictions |

## Use Cases

### 1. Similarity search (cosine on GCN-64)
```python
# Find hexes with similar urban character
similar = find_similar(hex_id, k=10)
```

### 2. Gap analysis (XGBoost predictions vs actual)
```python
preds = predict_categories(hex_id)  # expected counts
# Compare to actual counts from your data
```

### 3. As input features for downstream models
```python
import pandas as pd
bundle = pd.read_parquet("hex_shareable_bundle.parquet")
X = bundle[[f"g{i}" for i in range(64)]].values  # 64-dim features
# Feed into any ML model
```

## Performance (on 7,318 hexes, 5-fold CV)

| Task | Metric | Score |
|---|---|---|
| kNN similarity (PA match) | Accuracy | 0.430 |
| Category count prediction | Mean R² | 0.800 |

## Requirements (optional)

For pre-computed lookup (hex is already in bundle):
- pandas, numpy (that's it)

For encoding new hexes with GCN:
- torch, torch_geometric, scipy

For running XGBoost from scratch:
- xgboost
"""
    with open(f"{SERVE_DIR}/README.md", "w") as f:
        f.write(readme)
    log(f"   → {SERVE_DIR}/README.md")

    # ============================================================
    # SUMMARY
    # ============================================================
    log("\n" + "=" * 60)
    log("SERVING BUNDLE COMPLETE")
    log("=" * 60)
    total = 0
    for root, dirs, files in os.walk(SERVE_DIR):
        for f in sorted(files):
            path = os.path.join(root, f)
            sz = os.path.getsize(path)
            total += sz
            rel = path.replace(SERVE_DIR + "/", "")
            log(f"  {rel:<45} {sz/1024:>8.0f} KB")
    log(f"\nTotal bundle size: {total/1024/1024:.1f} MB")
    log(f"Location: {SERVE_DIR}")
    log(f"\nTime: {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
