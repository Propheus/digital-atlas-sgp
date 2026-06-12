"""
Plexis SGP v4 — extended bundle: roads + transit + walkability.

Output:
  hex/hex9_mobility_features.parquet      (~50 cols)
  hex/hex8_mobility_features.parquet
  hex/subzone_mobility_features.parquet
"""
import json, time
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent


def main():
    t0 = time.time()
    print("Loading inputs...")
    rd9 = pd.read_parquet(ROOT / "hex/hex9_roads_clean.parquet")
    rd8 = pd.read_parquet(ROOT / "hex/hex8_roads_clean.parquet")
    rd_sz = pd.read_parquet(ROOT / "hex/subzone_roads_clean.parquet")
    tr9 = pd.read_parquet(ROOT / "hex/hex9_transit_clean.parquet")
    tr8 = pd.read_parquet(ROOT / "hex/hex8_transit_clean.parquet")
    tr_sz = pd.read_parquet(ROOT / "hex/subzone_transit_clean.parquet")
    wk9 = pd.read_parquet(ROOT / "hex/hex9_walkability.parquet")
    wk8 = pd.read_parquet(ROOT / "hex/hex8_walkability.parquet")
    wk_sz = pd.read_parquet(ROOT / "hex/subzone_walkability.parquet")
    print(f"  rd9 {rd9.shape}  tr9 {tr9.shape}  wk9 {wk9.shape}")

    # Drop overlap cols from transit + walkability before merging
    tr9c = tr9.drop(columns=["parent_hex8", "parent_subzone"], errors="ignore")
    wk9c = wk9.drop(columns=["parent_hex8", "parent_subzone",
                              "road_walkable_share", "road_intersection_density_per_km2",
                              "signalized_crossing_count", "near_mrt_400m", "near_bus_300m"],
                     errors="ignore")

    # === HEX-9 BUNDLE ===
    print("\nBuilding hex-9 bundle...")
    h9_bundle = rd9.merge(tr9c, on="hex9_id", how="left").merge(wk9c, on="hex9_id", how="left")
    for c in h9_bundle.columns:
        if c == "hex9_id" or h9_bundle[c].dtype == "object" or h9_bundle[c].dtype == bool: continue
        h9_bundle[c] = h9_bundle[c].fillna(0 if "headway" not in c else 999)
    h9_bundle.to_parquet(ROOT / "hex/hex9_mobility_features.parquet", index=False)
    print(f"  hex9_mobility_features: {h9_bundle.shape}")

    # === HEX-8 BUNDLE ===
    print("\nBuilding hex-8 bundle...")
    wk8c = wk8.drop(columns=["road_walkable_share", "road_intersection_density_per_km2",
                              "signalized_crossing_count", "near_mrt_400m", "near_bus_300m"],
                     errors="ignore")
    h8_bundle = rd8.merge(tr8, on="hex8_id", how="left", suffixes=("", "_tr"))
    h8_bundle = h8_bundle.merge(wk8c, on="hex8_id", how="left", suffixes=("", "_wk"))
    for c in h8_bundle.columns:
        if c == "hex8_id" or c == "road_max_class_through": continue
        if h8_bundle[c].dtype == bool:
            h8_bundle[c] = h8_bundle[c].fillna(False)
        elif h8_bundle[c].dtype.kind in "if":
            h8_bundle[c] = h8_bundle[c].fillna(0 if "headway" not in c else 999)
    h8_bundle.to_parquet(ROOT / "hex/hex8_mobility_features.parquet", index=False)
    print(f"  hex8_mobility_features: {h8_bundle.shape}")

    # === SUBZONE BUNDLE ===
    print("\nBuilding subzone bundle...")
    sz_bundle = rd_sz.merge(tr_sz, on="subzone_c", how="left", suffixes=("", "_tr"))
    sz_bundle = sz_bundle.merge(wk_sz, on="subzone_c", how="left", suffixes=("", "_wk"))
    for c in sz_bundle.columns:
        if c == "subzone_c" or c == "road_max_class_through": continue
        if sz_bundle[c].dtype == bool:
            sz_bundle[c] = sz_bundle[c].fillna(False)
        elif sz_bundle[c].dtype.kind in "if":
            sz_bundle[c] = sz_bundle[c].fillna(0 if "headway" not in c else 999)
    sz_bundle.to_parquet(ROOT / "hex/subzone_mobility_features.parquet", index=False)
    print(f"  subzone_mobility_features: {sz_bundle.shape}")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "shapes": {
            "hex9": list(h9_bundle.shape),
            "hex8": list(h8_bundle.shape),
            "subzone": list(sz_bundle.shape),
        },
        "feature_groups": {
            "roads_parking_centrality": [c for c in rd9.columns if c != "hex9_id"],
            "transit": [c for c in tr9c.columns if c != "hex9_id"],
            "walkability": [c for c in wk9c.columns if c != "hex9_id"],
        },
    }
    with open(ROOT / "hex/mobility_features_report.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n=== Summary ===")
    print(f"  hex9: {h9_bundle.shape[0]:,} × {h9_bundle.shape[1]} cols")
    print(f"  hex8: {h8_bundle.shape[0]:,} × {h8_bundle.shape[1]} cols")
    print(f"  subzone: {sz_bundle.shape[0]:,} × {sz_bundle.shape[1]} cols")
    print(f"  Roads/parking/centrality: {len(summary['feature_groups']['roads_parking_centrality'])} cols")
    print(f"  Transit: {len(summary['feature_groups']['transit'])} cols")
    print(f"  Walkability: {len(summary['feature_groups']['walkability'])} cols")


if __name__ == "__main__":
    main()
