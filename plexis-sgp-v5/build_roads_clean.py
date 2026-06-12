"""
Plexis SGP v4 — Stage 6 cleanup.

Reads the bloated hex9_roads.parquet (66 cols), hex9_parking.parquet (11 cols),
hex9_road_centrality.parquet (11 cols) and produces three lean tables:

  hex/hex9_roads_clean.parquet     (15 cols)
  hex/hex8_roads_clean.parquet     (16 cols, aggregated from hex-9)
  hex/subzone_roads_clean.parquet  (12 cols, aggregated from hex-8)

Kept features (decision rationale in chat):
  hex9_roads_clean:
    Identity:          hex9_id
    Length & density:  road_length_total_m, road_density_km_per_km2,
                        road_walkable_share
    Class:             road_max_class_through  (categorical, top-class wins)
    Topology:          road_intersection_density_per_km2  (rest dropped — noisy at 0.1 km²)
    Motorway proximity: dist_expressway_m, near_expressway_exit_400m
    Vehicle:           lane_km_per_km2, oneway_pct, bridge_length_m
    Walkability infra: signalized_crossing_count
    Parking:           parking_lot_count, hdb_mscp_count
    Centrality:        centr_betweenness_max, centr_bridge_count

After cleanup, the bloated parquets are kept as `_raw.parquet` for archival.
"""
import json, os, time
from pathlib import Path
import pandas as pd
import numpy as np
import h3

ROOT = Path(__file__).parent

CLASS_RANK = ["motorway", "trunk", "primary", "secondary", "tertiary",
              "residential", "service", "unclassified", "track",
              "footway", "cycleway", "path", "steps", "other", "none"]


def _pick(root, base):
    """Return existing parquet, preferring base.parquet then base_raw.parquet."""
    for suffix in (".parquet", "_raw.parquet"):
        p = root / f"{base}{suffix}"
        if p.exists(): return p
    raise FileNotFoundError(f"Neither {base}.parquet nor {base}_raw.parquet exists")


def main():
    t0 = time.time()
    print("Loading raw stage-6 outputs...")
    rd = pd.read_parquet(_pick(ROOT, "hex/hex9_roads"))
    pk = pd.read_parquet(_pick(ROOT, "hex/hex9_parking"))
    ce = pd.read_parquet(_pick(ROOT, "hex/hex9_road_centrality"))
    h9 = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
    print(f"  rd={rd.shape}  pk={pk.shape}  ce={ce.shape}")

    # Archive raw versions (rename, don't delete)
    print("\nArchiving raw bloated parquets to _raw if not already...")
    for name in ["hex9_roads", "hex9_parking", "hex9_road_centrality"]:
        src = ROOT / f"hex/{name}.parquet"
        dst = ROOT / f"hex/{name}_raw.parquet"
        if src.exists() and not dst.exists():
            src.rename(dst)
            print(f"  {name}.parquet → {name}_raw.parquet")

    # === hex-9 clean ===
    print("\nBuilding hex9_roads_clean.parquet...")
    out = h9[["hex9_id", "parent_hex8", "parent_subzone"]].copy()
    out = out.merge(
        rd[["hex9_id", "road_length_total_m", "road_density_km_per_km2",
            "road_walkable_share", "road_max_class_through",
            "road_intersection_density_per_km2",
            "dist_expressway_m", "near_expressway_exit_400m",
            "lane_km_per_km2", "oneway_pct", "bridge_length_m",
            "signalized_crossing_count"]],
        on="hex9_id", how="left",
    )
    out = out.merge(
        pk[["hex9_id", "parking_lot_count", "hdb_mscp_count"]],
        on="hex9_id", how="left",
    )
    out = out.merge(
        ce[["hex9_id", "centr_betweenness_max", "centr_bridge_count"]],
        on="hex9_id", how="left",
    )
    # Fill numerics with 0; keep "none" for missing categorical
    for c in out.columns:
        if c in ("hex9_id", "parent_hex8", "parent_subzone", "road_max_class_through"):
            continue
        out[c] = out[c].fillna(0)
    out["road_max_class_through"] = out["road_max_class_through"].fillna("none")
    out["near_expressway_exit_400m"] = out["near_expressway_exit_400m"].astype(bool)

    out.to_parquet(ROOT / "hex/hex9_roads_clean.parquet", index=False)
    print(f"  hex9_roads_clean: {out.shape}")

    # === hex-8 clean (aggregated) ===
    print("\nAggregating hex-9 → hex-8...")
    h9c = out  # alias
    # Helpers
    def length_weighted_mean(df, value_col, weight_col="road_length_total_m"):
        # weighted mean over groups; return Series indexed by group
        def f(g):
            w = g[weight_col].sum()
            if w == 0: return 0.0
            return (g[value_col] * g[weight_col]).sum() / w
        return df.groupby("parent_hex8").apply(f, include_groups=False)

    # Class hierarchy: pick highest class across children
    rank = {c: i for i, c in enumerate(CLASS_RANK)}
    def max_class(s):
        valid = [v for v in s if isinstance(v, str)]
        if not valid: return "none"
        return min(valid, key=lambda c: rank.get(c, 999))

    h8 = h9c.groupby("parent_hex8").agg(
        road_length_total_m=("road_length_total_m", "sum"),
        road_intersection_count_total=("road_intersection_density_per_km2",
                                        lambda s: int((s * 0.105).sum())),  # density × ha → count
        bridge_length_m=("bridge_length_m", "sum"),
        signalized_crossing_count=("signalized_crossing_count", "sum"),
        parking_lot_count=("parking_lot_count", "sum"),
        hdb_mscp_count=("hdb_mscp_count", "sum"),
        dist_expressway_m=("dist_expressway_m", "min"),
        near_expressway_exit_400m=("near_expressway_exit_400m", "any"),
        centr_betweenness_max=("centr_betweenness_max", "max"),
        centr_bridge_count=("centr_bridge_count", "sum"),
        road_max_class_through=("road_max_class_through", max_class),
        n_children=("hex9_id", "count"),
    ).reset_index().rename(columns={"parent_hex8": "hex8_id"})

    # Length-weighted aggregations: walk_share, lane_km_per_km2, oneway_pct
    walk_share = length_weighted_mean(h9c, "road_walkable_share")
    lane_km = length_weighted_mean(h9c, "lane_km_per_km2")
    oneway = length_weighted_mean(h9c, "oneway_pct")
    h8 = h8.merge(walk_share.rename("road_walkable_share"), left_on="hex8_id", right_index=True, how="left")
    h8 = h8.merge(lane_km.rename("lane_km_per_km2"), left_on="hex8_id", right_index=True, how="left")
    h8 = h8.merge(oneway.rename("oneway_pct"), left_on="hex8_id", right_index=True, how="left")

    # Density per km² (hex-8 area = ~0.737 km²)
    HEX8_AREA_KM2 = 0.737
    h8["road_density_km_per_km2"] = h8["road_length_total_m"] / 1000 / HEX8_AREA_KM2
    h8["road_intersection_density_per_km2"] = h8["road_intersection_count_total"] / HEX8_AREA_KM2

    # Reorder cleanly
    h8 = h8[[
        "hex8_id", "n_children",
        "road_length_total_m", "road_density_km_per_km2",
        "road_walkable_share", "road_max_class_through",
        "road_intersection_count_total", "road_intersection_density_per_km2",
        "dist_expressway_m", "near_expressway_exit_400m",
        "lane_km_per_km2", "oneway_pct", "bridge_length_m",
        "signalized_crossing_count",
        "parking_lot_count", "hdb_mscp_count",
        "centr_betweenness_max", "centr_bridge_count",
    ]]
    for c in h8.columns:
        if c == "hex8_id" or c == "road_max_class_through":
            continue
        h8[c] = h8[c].fillna(0)
    h8["road_max_class_through"] = h8["road_max_class_through"].fillna("none")
    h8["near_expressway_exit_400m"] = h8["near_expressway_exit_400m"].astype(bool)

    h8.to_parquet(ROOT / "hex/hex8_roads_clean.parquet", index=False)
    print(f"  hex8_roads_clean: {h8.shape}")

    # === subzone clean (aggregated from hex-8 via parent) ===
    print("\nAggregating hex-8 → subzone...")
    # Need hex-8 → subzone link. hex9 has parent_subzone; for hex-8 we need the same.
    # Read hex8_universe for parent_subzone.
    h8_univ = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")
    h8_with_sz = h8.merge(h8_univ[["hex8_id", "parent_subzone"]], on="hex8_id", how="left")

    sz_agg = h8_with_sz.groupby("parent_subzone").agg(
        n_hex8=("hex8_id", "count"),
        road_length_total_m=("road_length_total_m", "sum"),
        road_intersection_count_total=("road_intersection_count_total", "sum"),
        bridge_length_m=("bridge_length_m", "sum"),
        signalized_crossing_count=("signalized_crossing_count", "sum"),
        parking_lot_count=("parking_lot_count", "sum"),
        hdb_mscp_count=("hdb_mscp_count", "sum"),
        dist_expressway_m=("dist_expressway_m", "min"),
        expressway_in_subzone=("road_max_class_through",
                                lambda s: bool(any(c in ("motorway", "trunk") for c in s))),
        centr_bridge_count=("centr_bridge_count", "sum"),
        centr_betweenness_max=("centr_betweenness_max", "max"),
        road_max_class_through=("road_max_class_through", max_class),
    ).reset_index().rename(columns={"parent_subzone": "subzone_c"})

    # Length-weighted walk_share + lane_km + oneway from hex-8 children
    def lwm_h8(value_col):
        def f(g):
            w = g["road_length_total_m"].sum()
            if w == 0: return 0.0
            return (g[value_col] * g["road_length_total_m"]).sum() / w
        return h8_with_sz.groupby("parent_subzone").apply(f, include_groups=False)
    sz_agg = sz_agg.merge(lwm_h8("road_walkable_share").rename("road_walkable_share"),
                           left_on="subzone_c", right_index=True, how="left")
    sz_agg = sz_agg.merge(lwm_h8("lane_km_per_km2").rename("lane_km_per_km2"),
                           left_on="subzone_c", right_index=True, how="left")

    # Density: subzone area from polygon
    import geopandas as gpd
    sz_gdf = gpd.read_file(ROOT / "boundaries/subzones.geojson").to_crs(3414)
    sz_gdf["area_km2"] = sz_gdf.geometry.area / 1e6
    sz_areas = dict(zip(sz_gdf["SUBZONE_C"], sz_gdf["area_km2"]))
    sz_agg["subzone_area_km2"] = sz_agg["subzone_c"].map(sz_areas).fillna(0)
    sz_agg["road_density_km_per_km2"] = np.where(
        sz_agg["subzone_area_km2"] > 0,
        sz_agg["road_length_total_m"] / 1000 / sz_agg["subzone_area_km2"], 0,
    )
    sz_agg["road_intersection_density_per_km2"] = np.where(
        sz_agg["subzone_area_km2"] > 0,
        sz_agg["road_intersection_count_total"] / sz_agg["subzone_area_km2"], 0,
    )

    sz_agg = sz_agg[[
        "subzone_c", "subzone_area_km2", "n_hex8",
        "road_length_total_m", "road_density_km_per_km2",
        "road_walkable_share", "road_max_class_through",
        "road_intersection_count_total", "road_intersection_density_per_km2",
        "dist_expressway_m", "expressway_in_subzone",
        "lane_km_per_km2", "bridge_length_m",
        "signalized_crossing_count",
        "parking_lot_count", "hdb_mscp_count",
        "centr_betweenness_max", "centr_bridge_count",
    ]]
    for c in sz_agg.columns:
        if c in ("subzone_c", "road_max_class_through"):
            continue
        sz_agg[c] = sz_agg[c].fillna(0)
    sz_agg["road_max_class_through"] = sz_agg["road_max_class_through"].fillna("none")
    sz_agg["expressway_in_subzone"] = sz_agg["expressway_in_subzone"].astype(bool)

    sz_agg.to_parquet(ROOT / "hex/subzone_roads_clean.parquet", index=False)
    print(f"  subzone_roads_clean: {sz_agg.shape}")

    # === Summary ===
    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "shapes": {
            "hex9_roads_clean":   list(out.shape),
            "hex8_roads_clean":   list(h8.shape),
            "subzone_roads_clean": list(sz_agg.shape),
        },
        "hex9_clean_cols": list(out.columns),
        "hex8_clean_cols": list(h8.columns),
        "subzone_clean_cols": list(sz_agg.columns),
        "totals": {
            "subzones_with_road_data": int((sz_agg["road_length_total_m"] > 0).sum()),
            "subzones_with_expressway": int(sz_agg["expressway_in_subzone"].sum()),
            "total_road_km":   round(out["road_length_total_m"].sum() / 1000, 1),
            "total_lane_km":   round((out["lane_km_per_km2"] * 0.105).sum(), 1),  # density × hex-9 area
            "total_parking_lots": int(out["parking_lot_count"].sum()),
            "total_mscps":     int(out["hdb_mscp_count"].sum()),
        },
    }
    with open(ROOT / "hex/roads_clean_report.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n{json.dumps(summary, indent=2)}")
    print(f"\nOutputs:")
    print(f"  hex9_roads_clean.parquet      ({out.shape[1]} cols)")
    print(f"  hex8_roads_clean.parquet      ({h8.shape[1]} cols)")
    print(f"  subzone_roads_clean.parquet   ({sz_agg.shape[1]} cols)")
    print(f"  Raw parquets archived as _raw.parquet for reference.")


if __name__ == "__main__":
    main()
