"""
Plexis SGP v4 — built_environment_features bundle.

Combines buildings + land_use into a single joinable bundle per scale.
Mirrors the mobility_features pattern.

Output:
  hex/hex9_built_environment_features.parquet      (buildings 17 + land_use 21 + ID = ~38)
  hex/hex8_built_environment_features.parquet
  hex/subzone_built_environment_features.parquet
"""
import json, time
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent


def main():
    t0 = time.time()
    print("Loading inputs...")
    b9 = pd.read_parquet(ROOT / "hex/hex9_buildings_clean.parquet")
    b8 = pd.read_parquet(ROOT / "hex/hex8_buildings_clean.parquet")
    b_sz = pd.read_parquet(ROOT / "hex/subzone_buildings_clean.parquet")
    lu = pd.read_parquet(ROOT / "hex/hex9_land_use.parquet")
    print(f"  b9 {b9.shape}  b8 {b8.shape}  b_sz {b_sz.shape}  lu {lu.shape}")

    # === HEX-9 ===
    print("\nBuilding hex-9 bundle...")
    h9 = b9.merge(lu.drop(columns=["lat", "lng"], errors="ignore"), on="hex9_id", how="left")
    for c in h9.columns:
        if c == "hex9_id" or h9[c].dtype == "object" or h9[c].dtype == bool: continue
        if h9[c].dtype.kind in "if":
            h9[c] = h9[c].fillna(0)
    h9.to_parquet(ROOT / "hex/hex9_built_environment_features.parquet", index=False)
    print(f"  hex9_built_environment_features: {h9.shape}")

    # === HEX-8 ===
    print("Building hex-8 bundle...")
    # Aggregate land_use to hex-8 first by area-weighted mean of shares
    h9_univ = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
    lu_with_hex8 = lu.merge(h9_univ[["hex9_id", "parent_hex8"]], on="hex9_id")
    share_cols = [c for c in lu.columns if c.endswith("_pct")]
    lu_h8 = lu_with_hex8.groupby("parent_hex8").agg({
        **{c: "mean" for c in share_cols},
        "lu_entropy": "mean",
        "lu_total_m2": "sum",
        "lu_parcel_count": "sum",
        "avg_gpr": "mean",
        "max_gpr": "max",
    }).reset_index().rename(columns={"parent_hex8": "hex8_id"})
    # dominant_use: max share among bucket cols
    if share_cols:
        lu_h8["dominant_use"] = lu_h8[share_cols].idxmax(axis=1).str.replace("lu_", "").str.replace("_pct", "")
    h8 = b8.merge(lu_h8, on="hex8_id", how="left")
    for c in h8.columns:
        if c == "hex8_id" or h8[c].dtype == "object" or h8[c].dtype == bool: continue
        if h8[c].dtype.kind in "if":
            h8[c] = h8[c].fillna(0)
    h8.to_parquet(ROOT / "hex/hex8_built_environment_features.parquet", index=False)
    print(f"  hex8_built_environment_features: {h8.shape}")

    # === SUBZONE ===
    print("Building subzone bundle...")
    h8_univ = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")
    lu_h8_with_sz = lu_h8.merge(h8_univ[["hex8_id", "parent_subzone"]], on="hex8_id", how="left")
    lu_sz = lu_h8_with_sz.groupby("parent_subzone").agg({
        **{c: "mean" for c in share_cols},
        "lu_entropy": "mean",
        "lu_total_m2": "sum",
        "lu_parcel_count": "sum",
        "avg_gpr": "mean",
        "max_gpr": "max",
    }).reset_index().rename(columns={"parent_subzone": "subzone_c"})
    if share_cols:
        lu_sz["dominant_use"] = lu_sz[share_cols].idxmax(axis=1).str.replace("lu_", "").str.replace("_pct", "")
    sz = b_sz.merge(lu_sz, on="subzone_c", how="left")
    for c in sz.columns:
        if c == "subzone_c" or sz[c].dtype == "object" or sz[c].dtype == bool: continue
        if sz[c].dtype.kind in "if":
            sz[c] = sz[c].fillna(0)
    sz.to_parquet(ROOT / "hex/subzone_built_environment_features.parquet", index=False)
    print(f"  subzone_built_environment_features: {sz.shape}")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "shapes": {"hex9": list(h9.shape), "hex8": list(h8.shape), "subzone": list(sz.shape)},
        "feature_groups": {
            "buildings": [c for c in b9.columns if c != "hex9_id"],
            "land_use": [c for c in lu.columns if c != "hex9_id"],
        },
    }
    with open(ROOT / "hex/built_environment_features_report.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n=== Summary ===")
    print(f"  hex9: {h9.shape[0]:,} × {h9.shape[1]} cols")
    print(f"  hex8: {h8.shape[0]:,} × {h8.shape[1]} cols")
    print(f"  subzone: {sz.shape[0]:,} × {sz.shape[1]} cols")
    print(f"  Buildings: {len(summary['feature_groups']['buildings'])} cols")
    print(f"  Land use: {len(summary['feature_groups']['land_use'])} cols")


if __name__ == "__main__":
    main()
