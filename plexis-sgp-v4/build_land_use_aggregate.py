"""
Plexis SGP v4 — aggregate land_use from hex-9 → hex-8 + subzone.

Aggregation rules:
  - lu_total_m2, lu_parcel_count: SUM
  - lu_*_pct shares: AREA-WEIGHTED MEAN (weight = lu_total_m2)
  - lu_entropy: re-derive from new shares
  - dominant_use: argmax of new shares
  - avg_gpr: area-weighted mean
  - max_gpr: MAX

Outputs:
  hex/hex8_land_use.parquet
  hex/subzone_land_use.parquet
"""
import json, time
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).parent


def aggregate(df, group_col):
    share_cols = [c for c in df.columns if c.startswith("lu_") and c.endswith("_pct")]
    # Sum totals first
    sum_cols = ["lu_total_m2", "lu_parcel_count"]
    summed = df.groupby(group_col)[sum_cols].sum().reset_index()
    # Area-weighted mean for shares
    df_w = df.copy()
    df_w["_w"] = df_w["lu_total_m2"]
    weighted = pd.DataFrame({group_col: df_w[group_col].unique()}).set_index(group_col)
    for c in share_cols:
        # weighted: sum(share × weight) / sum(weight)
        ws = df_w.groupby(group_col).apply(
            lambda g: (g[c] * g["_w"]).sum() / g["_w"].sum() if g["_w"].sum() > 0 else 0,
            include_groups=False
        )
        weighted[c] = ws
    weighted = weighted.reset_index()
    # GPR aggregation
    gpr = df_w.groupby(group_col).apply(
        lambda g: pd.Series({
            "avg_gpr": (g["avg_gpr"].fillna(0) * g["_w"]).sum() / g["_w"].sum() if g["_w"].sum() > 0 else np.nan,
            "max_gpr": g["max_gpr"].max(),
        }), include_groups=False
    ).reset_index()
    out = summed.merge(weighted, on=group_col).merge(gpr, on=group_col)
    # Entropy from new shares
    eps = 1e-12
    shares = out[share_cols].values
    safe = np.clip(shares, eps, 1.0)
    out["lu_entropy"] = -np.sum(shares * np.log(safe), axis=1)
    # dominant_use
    bucket_names = [c[3:-4] for c in share_cols]
    idxs = np.argmax(shares, axis=1)
    out["dominant_use"] = [bucket_names[i] if shares[r, i] > 0 else None for r, i in enumerate(idxs)]
    return out


def main():
    t0 = time.time()
    print("Loading...")
    lu9 = pd.read_parquet(ROOT / "hex/hex9_land_use.parquet")
    h9 = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
    h8 = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")
    print(f"  hex9_land_use: {lu9.shape}")

    # === hex-8 ===
    print("\n  Aggregating to hex-8...")
    lu_with_h8 = lu9.merge(h9[["hex9_id", "parent_hex8"]], on="hex9_id", how="left")
    h8_lu = aggregate(lu_with_h8, "parent_hex8").rename(columns={"parent_hex8": "hex8_id"})
    h8_lu.to_parquet(ROOT / "hex/hex8_land_use.parquet", index=False)
    print(f"  hex8_land_use: {h8_lu.shape}")

    # === subzone ===
    print("  Aggregating to subzone...")
    lu_with_sz = lu9.merge(h9[["hex9_id", "parent_subzone"]], on="hex9_id", how="left")
    sz_lu = aggregate(lu_with_sz, "parent_subzone").rename(columns={"parent_subzone": "subzone_c"})
    sz_lu.to_parquet(ROOT / "hex/subzone_land_use.parquet", index=False)
    print(f"  subzone_land_use: {sz_lu.shape}")

    # Sanity
    src_total = lu9["lu_total_m2"].sum()
    h8_total = h8_lu["lu_total_m2"].sum()
    sz_total = sz_lu["lu_total_m2"].sum()
    print(f"\n=== Conservation check ===")
    print(f"  hex9 total m²: {src_total:,.0f}")
    print(f"  hex8 total m²: {h8_total:,.0f}  drift {(h8_total-src_total):+.0f}")
    print(f"  subzone total m²: {sz_total:,.0f}  drift {(sz_total-src_total):+.0f}")
    print(f"\nwall: {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
