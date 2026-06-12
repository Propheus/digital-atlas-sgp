# Hex Features v10 — Normalization Report

**Input:** `data/hex_v10/hex_features_v10.parquet` (7,318 × 350)  
**Output:** `data/hex_v10/hex_features_v10_normalized.parquet` (7,318 × 347)  
**Mask:** `data/hex_v10/hex_features_v10_mask.parquet`  
**NaNs zero-filled after rule + z-score:** 114,613

## Rule application counts

| Rule | # columns | Formula |
|---|---|---|
| `sqrt` | 198 | √(max(x,0)) |
| `passthrough` | 96 | x → x |
| `signed_sqrt` | 30 | sign(x)·√|x| |
| `distance_decay` | 15 | exp(-d / 500m) |
