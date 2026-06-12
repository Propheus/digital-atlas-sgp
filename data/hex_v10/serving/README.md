# Singapore Urban Representation — Serving Bundle

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
