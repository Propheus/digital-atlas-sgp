"""
Plexis SGP v4 — Stage 5 cleanup: aggregate transit to hex-8 + subzone.

Reads hex9_transit.parquet → produces:
  hex/hex9_transit_clean.parquet     (16 cols, just the hex-9 with sensible naming)
  hex/hex8_transit_clean.parquet     (aggregated)
  hex/subzone_transit_clean.parquet  (aggregated)
"""
import json, time
from pathlib import Path
import pandas as pd
import numpy as np
import geopandas as gpd

ROOT = Path(__file__).parent

def main():
    t0 = time.time()
    print("Loading...")
    h9_t = pd.read_parquet(ROOT / "hex/hex9_transit.parquet")
    h9 = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
    h8_univ = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")
    print(f"  h9_transit: {h9_t.shape}")

    # Archive raw → clean (just rename for clarity)
    src = ROOT / "hex/hex9_transit.parquet"
    dst = ROOT / "hex/hex9_transit_clean.parquet"
    if src.exists():
        h9_t.to_parquet(dst, index=False)
        print(f"  → {dst.name}")

    # === Hex-8 aggregation ===
    print("\nAggregating hex-9 → hex-8...")
    agg_dict = dict(
        n_children=("hex9_id", "count"),
        mrt_station_count=("mrt_station_count", "sum"),
        mrt_exit_count=("mrt_exit_count", "sum"),
        bus_stop_count=("bus_stop_count", "sum"),
        dist_mrt_m=("dist_mrt_m", "min"),
        dist_mrt_exit_m=("dist_mrt_exit_m", "min"),
        dist_bus_m=("dist_bus_m", "min"),
        near_mrt_400m=("near_mrt_400m", "any"),
        near_bus_300m=("near_bus_300m", "any"),
        rail_line_through_m=("rail_line_through_m", "sum"),
        daily_train_taps=("daily_train_taps", "sum"),
        daily_bus_taps=("daily_bus_taps", "sum"),
        is_mrt_interchange=("is_mrt_interchange", "any"),
        transit_score=("transit_score", "max"),
    )
    if "bus_routes_per_stop_max" in h9_t.columns:
        agg_dict["bus_routes_per_stop_max"] = ("bus_routes_per_stop_max", "max")
        agg_dict["bus_routes_per_stop_mean"] = ("bus_routes_per_stop_mean", "mean")
        agg_dict["gtfs_headway_am_min"] = ("gtfs_headway_am_min", "min")
    h8 = h9_t.groupby("parent_hex8").agg(**agg_dict).reset_index().rename(columns={"parent_hex8": "hex8_id"})
    h8.to_parquet(ROOT / "hex/hex8_transit_clean.parquet", index=False)
    print(f"  hex8_transit_clean: {h8.shape}")

    # === Subzone aggregation ===
    print("\nAggregating hex-8 → subzone...")
    h8_with_sz = h8.merge(h8_univ[["hex8_id", "parent_subzone"]], on="hex8_id", how="left")
    sz = h8_with_sz.groupby("parent_subzone").agg(
        n_hex8=("hex8_id", "count"),
        mrt_station_count=("mrt_station_count", "sum"),
        mrt_exit_count=("mrt_exit_count", "sum"),
        bus_stop_count=("bus_stop_count", "sum"),
        dist_mrt_m=("dist_mrt_m", "min"),
        dist_bus_m=("dist_bus_m", "min"),
        rail_line_through_m=("rail_line_through_m", "sum"),
        daily_train_taps=("daily_train_taps", "sum"),
        daily_bus_taps=("daily_bus_taps", "sum"),
        n_interchanges=("is_mrt_interchange", "sum"),
        max_transit_score=("transit_score", "max"),
    ).reset_index().rename(columns={"parent_subzone": "subzone_c"})
    sz["has_mrt"] = sz["mrt_station_count"] > 0
    sz["has_interchange"] = sz["n_interchanges"] > 0
    sz.to_parquet(ROOT / "hex/subzone_transit_clean.parquet", index=False)
    print(f"  subzone_transit_clean: {sz.shape}")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "shapes": {
            "hex9":    list(h9_t.shape),
            "hex8":    list(h8.shape),
            "subzone": list(sz.shape),
        },
        "subzone_summary": {
            "subzones_with_mrt": int(sz["has_mrt"].sum()),
            "subzones_with_interchange": int(sz["has_interchange"].sum()),
            "subzones_total": int(len(sz)),
        },
    }
    with open(ROOT / "hex/transit_clean_report.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n{json.dumps(summary, indent=2)}")
    print(f"\nOutputs:")
    print(f"  hex9_transit_clean.parquet     ({h9_t.shape[1]} cols)")
    print(f"  hex8_transit_clean.parquet     ({h8.shape[1]} cols)")
    print(f"  subzone_transit_clean.parquet  ({sz.shape[1]} cols)")


if __name__ == "__main__":
    main()
