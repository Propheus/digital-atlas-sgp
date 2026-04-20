"""
Hex v10 — sqrt normalization + z-score.

Same rule table as representation_v1/normalize_hex_features_v1.py with two changes:
    - Operates on data/hex_v10/hex_features_v10.parquet
    - Bookkeeping columns (subzone_pop_total etc.) are excluded from the normalized
      matrix entirely

Outputs:
    data/hex_v10/hex_features_v10_normalized.parquet
    data/hex_v10/hex_features_v10_mask.parquet
    data/hex_v10/hex_features_v10_normalization_stats.json
    data/hex_v10/hex_features_v10_normalization_report.md
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
V10 = ROOT / "data" / "hex_v10"
IN_PARQUET = V10 / "hex_features_v10.parquet"
OUT_PARQUET = V10 / "hex_features_v10_normalized.parquet"
MASK_PARQUET = V10 / "hex_features_v10_mask.parquet"
REPORT_MD = V10 / "hex_features_v10_normalization_report.md"
STATS_JSON = V10 / "hex_features_v10_normalization_stats.json"

IDENTITY_COLS = {
    "hex_id", "lat", "lng", "area_km2",
    "parent_subzone", "parent_subzone_name", "parent_pa", "parent_region",
}
BOOKKEEPING_COLS = {
    "subzone_pop_total", "subzone_res_floor_area", "residential_floor_weight",
    "hex_area_sqm",
}

PASSTHROUGH_PREFIXES = ("pc_pct_", "rank_", "lu_")  # lu_*_pct are 0-1
PASSTHROUGH_EXACT = {
    "pc_cat_entropy", "pc_seg_entropy",
    "pc_branded_pct", "pc_cat_hhi",
    "mg_pct_hyperdense", "mg_pct_dense", "mg_pct_moderate", "mg_pct_sparse",
    "walkability_score", "walkability_score_v2",
    "walk_mrt_score", "walk_hawker_score", "walk_park_score",
    "walk_clinic_score", "walk_super_score", "walk_bus_score",
    "hex_jam_pct", "hex_flow_pct",
    "lu_entropy",
}

DISTANCE_COLS_EXACT = {
    "dist_nearest_mrt_m", "dist_school_m", "walk_mrt_m", "walk_hawker_m",
    "walk_park_m", "walk_school_m", "walk_super_m", "walk_clinic_m",
    "walk_bus_m", "dist_mrt_m", "dist_bus_m", "dist_hawker_m",
    "dist_park_m", "dist_clinic_m", "dist_super_m",
}
DIST_SCALE_M = 500.0


def rule_for(col: str) -> str:
    if col in IDENTITY_COLS or col in BOOKKEEPING_COLS:
        return "identity"
    if col in PASSTHROUGH_EXACT:
        return "passthrough"
    for pre in PASSTHROUGH_PREFIXES:
        if col.startswith(pre):
            return "passthrough"
    if col in DISTANCE_COLS_EXACT or (col.endswith("_m") and ("dist" in col or "walk_" in col)):
        return "distance_decay"
    if col == "avg_gpr":
        return "sqrt"
    if col.startswith("contrast_"):
        return "signed_sqrt"
    if col.startswith("nbr1_mean_") or col.startswith("nbr1_max_") or col.startswith("nbr2_mean_"):
        return "sqrt"
    if col.startswith("pc_tier_") or col.startswith("pc_cat_") or col in {"pc_total", "pc_unique_brands", "pc_branded_count", "pc_unique_place_types"}:
        return "sqrt"
    if col.startswith("mg_mean_"):
        return "passthrough"
    if col in {"mg_n", "mg_cafe_n"}:
        return "sqrt"
    return "sqrt"


def apply_rule(series: pd.Series, rule: str) -> pd.Series:
    x = series.astype("float64")
    if rule == "passthrough":
        return x
    if rule == "sqrt":
        return np.sqrt(x.clip(lower=0))
    if rule == "signed_sqrt":
        return np.sign(x) * np.sqrt(np.abs(x))
    if rule == "distance_decay":
        return np.exp(-x.clip(lower=0) / DIST_SCALE_M)
    raise ValueError(f"unknown rule {rule}")


def main() -> None:
    df = pd.read_parquet(IN_PARQUET)
    print(f"Loaded {df.shape}")

    id_cols = [c for c in df.columns if c in IDENTITY_COLS]
    feat_cols = [c for c in df.columns if c not in IDENTITY_COLS and c not in BOOKKEEPING_COLS]
    print(f"  identity cols: {len(id_cols)}  feature cols: {len(feat_cols)}  (excluded {len(BOOKKEEPING_COLS & set(df.columns))} bookkeeping)")

    id_df = df[id_cols].copy()
    feats = df[feat_cols].copy()
    mask = feats.isna()

    transformed = {}
    rule_counts: dict[str, int] = {}
    for c in feat_cols:
        r = rule_for(c)
        rule_counts[r] = rule_counts.get(r, 0) + 1
        transformed[c] = apply_rule(feats[c], r)
    tf = pd.DataFrame(transformed)
    tf = tf.replace([np.inf, -np.inf], np.nan)

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

    n_nan_before = tf.isna().sum().sum()
    tf = tf.fillna(0.0)
    print(f"NaNs replaced with 0 in normalized matrix: {int(n_nan_before):,}")

    normalized = pd.concat([id_df.reset_index(drop=True), tf.reset_index(drop=True)], axis=1)
    print(f"Normalized shape: {normalized.shape}")

    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    normalized.to_parquet(OUT_PARQUET, index=False)
    print(f"Wrote {OUT_PARQUET}")

    mask_out = pd.concat(
        [id_df[["hex_id"]].reset_index(drop=True), mask.reset_index(drop=True)],
        axis=1,
    )
    mask_out.to_parquet(MASK_PARQUET, index=False)
    print(f"Wrote {MASK_PARQUET}")

    STATS_JSON.write_text(json.dumps(stats, indent=2))
    print(f"Wrote {STATS_JSON}")

    # report
    lines: list[str] = []
    lines.append("# Hex Features v10 — Normalization Report")
    lines.append("")
    lines.append(f"**Input:** `{IN_PARQUET.relative_to(ROOT)}` ({df.shape[0]:,} × {df.shape[1]})  ")
    lines.append(f"**Output:** `{OUT_PARQUET.relative_to(ROOT)}` ({normalized.shape[0]:,} × {normalized.shape[1]})  ")
    lines.append(f"**Mask:** `{MASK_PARQUET.relative_to(ROOT)}`  ")
    lines.append(f"**NaNs zero-filled after rule + z-score:** {int(n_nan_before):,}")
    lines.append("")
    lines.append("## Rule application counts")
    lines.append("")
    lines.append("| Rule | # columns | Formula |")
    lines.append("|---|---|---|")
    formulas = {
        "identity": "pass-through, excluded from z-score",
        "passthrough": "x → x",
        "sqrt": "√(max(x,0))",
        "signed_sqrt": "sign(x)·√|x|",
        "distance_decay": f"exp(-d / {DIST_SCALE_M:.0f}m)",
    }
    for r, n in sorted(rule_counts.items(), key=lambda kv: -kv[1]):
        lines.append(f"| `{r}` | {n} | {formulas.get(r,'')} |")
    lines.append("")
    REPORT_MD.write_text("\n".join(lines))
    print(f"Wrote {REPORT_MD}")


if __name__ == "__main__":
    main()
