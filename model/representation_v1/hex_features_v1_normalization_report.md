# Hex Features v1 — Normalization Report

**Input:** `model/representation_v1/hex_features_v1.parquet` (5,897 × 376)  
**Output:** `model/representation_v1/hex_features_v1_normalized.parquet` (5,897 × 376)  
**Mask:** `model/representation_v1/hex_features_v1_mask.parquet` (boolean, `True` = value was NaN before normalization)  
**NaNs zero-filled after rule + z-score:** 364

## Rule application counts

| Rule | # columns | Formula |
|---|---|---|
| `sqrt` | 206 | √(max(x,0)) |
| `passthrough` | 119 | x → x (already bounded or 0-1) |
| `signed_sqrt` | 28 | sign(x)·√|x| (for contrast features) |
| `distance_decay` | 15 | exp(-d / 500m) → 0-1, closer is larger |

## Post-transform z-score

After rule application, every feature column is z-scored using its own mean and std across the 5,897 hexes (computed on present values only). Per-column stats are stored in `hex_features_v1_normalization_stats.json` so the same transform can be re-applied to new hexes or an updated table.

## Missingness handling

Null values are replaced with 0 in the normalized matrix (which means "at the feature mean"). The companion mask parquet preserves the original null pattern so downstream models can add explicit missingness channels if desired.