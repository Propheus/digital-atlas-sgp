"""
Representation v1 — sqrt normalization pass for hex features.

Inputs:
    model/representation_v1/hex_features_v1.parquet   (raw)
    model/representation_v1/hex_features_v1_catalog.md (reference)

Outputs:
    model/representation_v1/hex_features_v1_normalized.parquet
    model/representation_v1/hex_features_v1_mask.parquet
    model/representation_v1/hex_features_v1_normalization_report.md

Normalization rules (sqrt-first, preserves variance better than log):
    identity cols (hex_id, lat, lng, parent_*, area_km2): passed through untouched
    raw counts:                        sqrt(x)
    densities (per-km2 derived):       sqrt(x / area_km2)
    shares / percentages / entropies:  pass-through (already 0-1 or bounded)
    distances in meters:               exp(-d / 500) — "closer is larger", 0-1
    contrasts (signed):                sign(x) * sqrt(|x|)
    ranks:                             pass-through (already 0-1)
    money (psf / price):               sqrt(x)
    persona p_pct_* / p_hobby_*:       pass-through (already 0-1)
    persona p_*_idx:                   pass-through (already normalized indices)
    p_persona_count / p_median_age:    sqrt(x)

After rule-based transform, all numeric columns are z-scored across the 5,897 hexes
using the mean and std of *present* values (NaN and inf ignored). NaNs are replaced
with 0 in the final normalized matrix; the companion mask parquet marks where that
happened so downstream models can add a missingness channel if desired.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
IN_PARQUET = ROOT / "model" / "representation_v1" / "hex_features_v1.parquet"
OUT_PARQUET = ROOT / "model" / "representation_v1" / "hex_features_v1_normalized.parquet"
MASK_PARQUET = ROOT / "model" / "representation_v1" / "hex_features_v1_mask.parquet"
REPORT_MD = ROOT / "model" / "representation_v1" / "hex_features_v1_normalization_report.md"
STATS_JSON = ROOT / "model" / "representation_v1" / "hex_features_v1_normalization_stats.json"

IDENTITY_COLS = {
    "hex_id", "lat", "lng", "area_km2",
    "parent_subzone", "parent_subzone_name", "parent_pa", "parent_region",
}

# Explicit columns that should be passed through (already 0-1 or bounded index).
PASSTHROUGH_PREFIXES = (
    "pc_pct_",          # place composition shares
    "p_pct_",           # persona shares
    "p_hobby_",         # persona hobby indices (0-1)
    "rank_",            # neighbor percentile ranks
    "pc_branded_pct",
    "pc_cat_hhi",
)
PASSTHROUGH_EXACT = {
    "pc_cat_entropy", "pc_seg_entropy",
    "elderly_pct", "walking_dependent_pct",
    "p_affluence_idx", "p_youth_idx", "p_family_idx", "p_retirement_idx",
    "hex_jam_pct", "hex_flow_pct",
    "mg_pct_hyperdense", "mg_pct_dense", "mg_pct_moderate", "mg_pct_sparse",
    "walkability_score", "walkability_score_v2",
    "residential_weight",
    "walk_mrt_score", "walk_hawker_score", "walk_park_score",
    "walk_clinic_score", "walk_super_score", "walk_bus_score",
}

# Distance-in-meters columns → exponential decay with 500m scale.
DISTANCE_COLS_ENDSWITH = ("_m", "_dist_m", "_nearest_m")
DISTANCE_COLS_EXACT = {
    "dist_nearest_mrt_m", "dist_school_m", "walk_mrt_m", "walk_hawker_m",
    "walk_park_m", "walk_school_m", "walk_super_m", "walk_clinic_m",
    "walk_bus_m", "dist_mrt_m", "dist_bus_m", "dist_hawker_m",
    "dist_park_m", "dist_clinic_m", "dist_super_m",
}
DIST_SCALE_M = 500.0

# Money / price columns → sqrt
MONEY_COLS = {"hdb_median_psf", "hdb_median_price"}

# Signed contrast columns (from ring aggregation) → signed sqrt
# recognized by prefix "contrast_"


def rule_for(col: str) -> str:
    if col in IDENTITY_COLS:
        return "identity"
    if col in PASSTHROUGH_EXACT:
        return "passthrough"
    for pre in PASSTHROUGH_PREFIXES:
        if col.startswith(pre):
            return "passthrough"
    if col in DISTANCE_COLS_EXACT:
        return "distance_decay"
    # catch remaining "*_m" distance columns (but not percentile _m_pct etc.)
    if col.endswith("_m") and ("dist" in col or "walk_" in col):
        return "distance_decay"
    if col in MONEY_COLS:
        return "sqrt"
    if col.startswith("contrast_"):
        return "signed_sqrt"
    # density patterns (mean of counts over neighbors) — just sqrt
    if col.startswith("nbr1_mean_") or col.startswith("nbr1_max_") or col.startswith("nbr2_mean_"):
        return "sqrt"
    # place composition: pc_total, pc_cat_* (counts), pc_tier_* (counts), pc_unique_*, pc_branded_count
    if col.startswith("pc_tier_") or col.startswith("pc_cat_") or col in {"pc_total", "pc_unique_brands", "pc_branded_count", "pc_unique_place_types"}:
        return "sqrt"
    # micrograph means: already bounded context-vector weights 0-1, mean anchor count is ~0-20
    if col.startswith("mg_mean_"):
        return "passthrough"
    if col in {"mg_n", "mg_cafe_n"}:
        return "sqrt"
    # persona absolute counts
    if col in {"p_persona_count", "p_median_age"}:
        return "sqrt"
    # default for other numeric columns: sqrt
    return "sqrt"


def apply_rule(series: pd.Series, rule: str) -> pd.Series:
    x = series.astype("float64")
    if rule == "passthrough":
        return x
    if rule == "sqrt":
        # negatives → nan (shouldn't happen for counts, but safe)
        return np.sqrt(x.clip(lower=0))
    if rule == "signed_sqrt":
        return np.sign(x) * np.sqrt(np.abs(x))
    if rule == "distance_decay":
        return np.exp(-x.clip(lower=0) / DIST_SCALE_M)
    raise ValueError(f"unknown rule {rule}")


def main() -> None:
    df = pd.read_parquet(IN_PARQUET)
    print(f"Loaded {df.shape}")

    # Separate identity and feature columns
    id_df = df[[c for c in df.columns if c in IDENTITY_COLS]].copy()
    feat_cols = [c for c in df.columns if c not in IDENTITY_COLS]
    feats = df[feat_cols].copy()

    # Mask: True where value was NaN before normalization
    mask = feats.isna()

    # Apply rules
    transformed = {}
    rule_counts: dict[str, int] = {}
    for c in feat_cols:
        r = rule_for(c)
        rule_counts[r] = rule_counts.get(r, 0) + 1
        transformed[c] = apply_rule(feats[c], r)
    tf = pd.DataFrame(transformed)

    # Replace any inf that may have come from sqrt of huge numbers (shouldn't, but safe)
    tf = tf.replace([np.inf, -np.inf], np.nan)

    # z-score per column using present values only
    stats: dict[str, dict] = {}
    for c in tf.columns:
        col = tf[c]
        present = col.dropna()
        if present.empty:
            mu, sd = 0.0, 1.0
        else:
            mu = float(present.mean())
            sd = float(present.std(ddof=0))
            if not np.isfinite(sd) or sd < 1e-9:
                sd = 1.0
        tf[c] = (col - mu) / sd
        stats[c] = {"rule": rule_for(c), "mu": mu, "sd": sd}

    # NaN → 0 in normalized matrix (mask retains the null signal)
    n_nan_before = tf.isna().sum().sum()
    tf = tf.fillna(0.0)
    print(f"NaNs replaced with 0 in normalized matrix: {int(n_nan_before):,}")

    # Assemble final normalized frame — identity first, then features
    normalized = pd.concat([id_df.reset_index(drop=True), tf.reset_index(drop=True)], axis=1)
    print(f"Normalized shape: {normalized.shape}")

    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    normalized.to_parquet(OUT_PARQUET, index=False)
    print(f"Wrote {OUT_PARQUET}")

    # Mask parquet — only for feature columns, keyed by hex_id
    mask_out = pd.concat(
        [id_df[["hex_id"]].reset_index(drop=True), mask.reset_index(drop=True)],
        axis=1,
    )
    mask_out.to_parquet(MASK_PARQUET, index=False)
    print(f"Wrote {MASK_PARQUET}")

    STATS_JSON.write_text(json.dumps(stats, indent=2))
    print(f"Wrote {STATS_JSON}")

    # Report
    lines: list[str] = []
    lines.append("# Hex Features v1 — Normalization Report")
    lines.append("")
    lines.append(f"**Input:** `{IN_PARQUET.relative_to(ROOT)}` ({df.shape[0]:,} × {df.shape[1]})  ")
    lines.append(f"**Output:** `{OUT_PARQUET.relative_to(ROOT)}` ({normalized.shape[0]:,} × {normalized.shape[1]})  ")
    lines.append(f"**Mask:** `{MASK_PARQUET.relative_to(ROOT)}` (boolean, `True` = value was NaN before normalization)  ")
    lines.append(f"**NaNs zero-filled after rule + z-score:** {int(n_nan_before):,}")
    lines.append("")
    lines.append("## Rule application counts")
    lines.append("")
    lines.append("| Rule | # columns | Formula |")
    lines.append("|---|---|---|")
    formulas = {
        "identity": "pass-through, excluded from z-score",
        "passthrough": "x → x (already bounded or 0-1)",
        "sqrt": "√(max(x,0))",
        "signed_sqrt": "sign(x)·√|x| (for contrast features)",
        "distance_decay": f"exp(-d / {DIST_SCALE_M:.0f}m) → 0-1, closer is larger",
    }
    for r, n in sorted(rule_counts.items(), key=lambda kv: -kv[1]):
        lines.append(f"| `{r}` | {n} | {formulas.get(r, '')} |")
    lines.append("")
    lines.append("## Post-transform z-score")
    lines.append("")
    lines.append("After rule application, every feature column is z-scored using its own mean and std "
                 f"across the {df.shape[0]:,} hexes (computed on present values only). Per-column stats "
                 "are stored in `hex_features_v1_normalization_stats.json` so the same transform can be "
                 "re-applied to new hexes or an updated table.")
    lines.append("")
    lines.append("## Missingness handling")
    lines.append("")
    lines.append("Null values are replaced with 0 in the normalized matrix (which means \"at the feature mean\"). "
                 "The companion mask parquet preserves the original null pattern so downstream models can "
                 "add explicit missingness channels if desired.")
    REPORT_MD.write_text("\n".join(lines))
    print(f"Wrote {REPORT_MD}")

    # final sanity — normalized col means should be ~0 and std ~1 for non-identity
    feat_means = normalized[feat_cols].mean()
    feat_stds = normalized[feat_cols].std(ddof=0)
    print()
    print(f"Normalized feature means: min={feat_means.min():.4f}  max={feat_means.max():.4f}  (target ~0)")
    print(f"Normalized feature stds:  min={feat_stds.min():.4f}  max={feat_stds.max():.4f}  (target ~1, <1 if many zero-fills)")


if __name__ == "__main__":
    main()
