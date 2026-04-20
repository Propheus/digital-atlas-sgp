"""
Layer 1 — model layer (atomic operations per embedding/predictor).

v0.1: stubs only. Real implementations will load:
  - GCN-64 from data/hex_v10/gcn_results/gcn_embedding_64.parquet
  - Node2Vec-64 from data/hex_v10/baselines/node2vec_64.parquet
  - UMAP-64 from data/hex_v10/baselines/umap_64.parquet
  - Transformer-64 from data/hex_v10/baselines/transformer_64.parquet
  - 24 XGBoost models from data/hex_v10/serving/xgboost_models/*.json
  - Raw 391 features from data/hex_v10/hex_features_v10_normalized.parquet

Each model exposes:
  load() → load the embedding/predictor into memory
  similar(hex_id, k) → top-k similar hex_ids by cosine
  predict(hex_id) → for XGBoost only, return 24 predicted counts

TODO (v0.2): implement actual loading and queries.
"""
