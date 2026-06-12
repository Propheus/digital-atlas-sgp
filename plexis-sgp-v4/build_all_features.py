"""
Plexis SGP v4 — master `all_features` bundle per scale.

Joins every standalone layer at each scale into a single parquet.

For each scale (hex9, hex8, subzone):
  identity (universe)
  + population
  + land_use (the standalone, not the bundled)
  + buildings_clean
  + roads_clean
  + transit_clean
  + walkability

= one master parquet downstream consumers can use without joins.

Outputs:
  hex/hex9_all_features.parquet     (~140+ cols)
  hex/hex8_all_features.parquet     (~130+)
  hex/subzone_all_features.parquet  (~80+)
"""
import json, time
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent


def safe_merge(left, right, on, label, drop_cols=None):
    if drop_cols is None: drop_cols = []
    rcols = [c for c in right.columns if c == on or c not in left.columns]
    rcols = [c for c in rcols if c not in drop_cols]
    return left.merge(right[rcols], on=on, how="left")


# Site-selection columns where NaN means "not applicable / no data", NOT zero
# (SITE_SELECTION_METRICS.md gate 4: NaN != 0). Zero-filling dt_ratio or
# rent would fabricate "empties by day" / "free rent" hexes.
NAN_KEEP = ("dt_ratio", "iso_severance_ratio", "rent_resi_psf_med",
            "roi_cap_per_rent_", "biz_dead_share", "biz_recent_dead_share",
            "biz_median_age_yrs", "biz_per_address", "biz_company_share",
            "female_pop_share")   # NaN = zero-population subzone, not 0.0


def fill_defaults(df, key_col):
    """Fill numeric NaN with 0; categorical with empty; bool with False."""
    for c in df.columns:
        if c == key_col: continue
        if c.startswith(NAN_KEEP):
            continue
        if df[c].dtype == bool:
            df[c] = df[c].fillna(False)
        elif df[c].dtype.kind in "if":
            # special: headway_am_min keeps 999 sentinel
            if "headway" in c:
                df[c] = df[c].fillna(999)
            else:
                df[c] = df[c].fillna(0)
    return df


def main():
    t0 = time.time()
    print("Loading layers...")

    # === HEX-9 ===
    print("\n--- HEX-9 ---")
    h9_uni = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
    h9_pop = pd.read_parquet(ROOT / "hex/hex9_population.parquet")
    h9_lu = pd.read_parquet(ROOT / "hex/hex9_land_use.parquet")
    h9_bld = pd.read_parquet(ROOT / "hex/hex9_buildings_clean.parquet")
    h9_rd = pd.read_parquet(ROOT / "hex/hex9_roads_clean.parquet")
    h9_tr = pd.read_parquet(ROOT / "hex/hex9_transit_clean.parquet")
    h9_wk = pd.read_parquet(ROOT / "hex/hex9_walkability.parquet")
    h9_sat_path = ROOT / "hex/hex9_satellite.parquet"
    h9_sat = pd.read_parquet(h9_sat_path) if h9_sat_path.exists() else None
    h9_pc_path = ROOT / "hex/hex9_place_composition.parquet"
    h9_pc = pd.read_parquet(h9_pc_path) if h9_pc_path.exists() else None
    h9_pr_path = ROOT / "hex/hex9_hdb_resale.parquet"
    h9_pr = pd.read_parquet(h9_pr_path) if h9_pr_path.exists() else None
    h9_sc_path = ROOT / "hex/hex9_schools.parquet"
    h9_sc = pd.read_parquet(h9_sc_path) if h9_sc_path.exists() else None
    h9_ax_path = ROOT / "hex/hex9_amenities_extra.parquet"
    h9_ax = pd.read_parquet(h9_ax_path) if h9_ax_path.exists() else None
    h9_rg_path = ROOT / "hex/hex9_spatial_rings.parquet"
    h9_rg = pd.read_parquet(h9_rg_path) if h9_rg_path.exists() else None
    h9_cp_path = ROOT / "hex/hex9_composites.parquet"
    h9_cp = pd.read_parquet(h9_cp_path) if h9_cp_path.exists() else None
    h9_dp_path = ROOT / "hex/hex9_demand_pull.parquet"
    h9_dp = pd.read_parquet(h9_dp_path) if h9_dp_path.exists() else None
    h9_sy_path = ROOT / "hex/hex9_synergy.parquet"
    h9_sy = pd.read_parquet(h9_sy_path) if h9_sy_path.exists() else None
    h9_sg_path = ROOT / "hex/hex9_saturation_gap.parquet"
    h9_sg = pd.read_parquet(h9_sg_path) if h9_sg_path.exists() else None
    h9_ar_path = ROOT / "hex/hex9_archetypes.parquet"
    h9_ar = pd.read_parquet(h9_ar_path) if h9_ar_path.exists() else None
    h9_in_path = ROOT / "hex/hex9_influence.parquet"
    h9_in = pd.read_parquet(h9_in_path) if h9_in_path.exists() else None
    h9_mr_path = ROOT / "hex/hex9_micrograph_rollup.parquet"
    h9_mr = pd.read_parquet(h9_mr_path) if h9_mr_path.exists() else None
    h9_ws_path = ROOT / "hex/hex9_walk_scores.parquet"
    h9_ws = pd.read_parquet(h9_ws_path) if h9_ws_path.exists() else None
    h9_op_path = ROOT / "hex/hex9_osm_pois.parquet"
    h9_op = pd.read_parquet(h9_op_path) if h9_op_path.exists() else None
    h9_lc_path = ROOT / "hex/hex9_landcover.parquet"
    h9_lc = pd.read_parquet(h9_lc_path) if h9_lc_path.exists() else None
    h9_pw_path = ROOT / "hex/hex9_pop_weighted.parquet"
    h9_pw = pd.read_parquet(h9_pw_path) if h9_pw_path.exists() else None
    h9_ts_path = ROOT / "hex/hex9_traffic_signals.parquet"
    h9_ts = pd.read_parquet(h9_ts_path) if h9_ts_path.exists() else None
    h9_gw_path = ROOT / "hex/hex9_gtfs_windows.parquet"
    h9_gw = pd.read_parquet(h9_gw_path) if h9_gw_path.exists() else None
    h9_pc2_path = ROOT / "hex/hex9_place_composition_v2.parquet"
    h9_pc2 = pd.read_parquet(h9_pc2_path) if h9_pc2_path.exists() else None
    h9_lpv_path = ROOT / "hex/hex9_lta_pv.parquet"
    h9_lpv = pd.read_parquet(h9_lpv_path) if h9_lpv_path.exists() else None
    h9_ldn_path = ROOT / "hex/hex9_lta_dynamic.parquet"
    h9_ldn = pd.read_parquet(h9_ldn_path) if h9_ldn_path.exists() else None

    h9 = h9_uni.copy()
    layers9 = [("pop", h9_pop), ("lu", h9_lu), ("bld", h9_bld),
                ("rd", h9_rd), ("tr", h9_tr), ("wk", h9_wk)]
    if h9_sat is not None: layers9.append(("sat", h9_sat))
    if h9_pc is not None: layers9.append(("pc", h9_pc))
    if h9_pr is not None: layers9.append(("pr", h9_pr))
    if h9_sc is not None: layers9.append(("sc", h9_sc))
    if h9_ax is not None: layers9.append(("ax", h9_ax))
    if h9_rg is not None: layers9.append(("rg", h9_rg))
    if h9_cp is not None: layers9.append(("cp", h9_cp))
    if h9_dp is not None: layers9.append(("dp", h9_dp))
    if h9_sy is not None: layers9.append(("sy", h9_sy))
    if h9_sg is not None: layers9.append(("sg", h9_sg))
    if h9_ar is not None: layers9.append(("ar", h9_ar))
    if h9_in is not None: layers9.append(("in", h9_in))
    if h9_mr is not None: layers9.append(("mr", h9_mr))
    if h9_ws is not None: layers9.append(("ws", h9_ws))
    if h9_op is not None: layers9.append(("op", h9_op))
    if h9_lc is not None: layers9.append(("lc", h9_lc))
    if h9_pw is not None: layers9.append(("pw", h9_pw))
    if h9_ts is not None: layers9.append(("ts", h9_ts))
    if h9_gw is not None: layers9.append(("gw", h9_gw))
    if h9_pc2 is not None: layers9.append(("pc2", h9_pc2))
    if h9_lpv is not None: layers9.append(("lpv", h9_lpv))
    if h9_ldn is not None: layers9.append(("ldn", h9_ldn))
    # site-selection layers (hex9-grain: Huff capture + co-location fit)
    for name in ["hex9_huff_capture", "hex9_colo_fit"]:
        p = ROOT / f"hex/{name}.parquet"
        if p.exists():
            layers9.append((name.replace("hex9_", ""),
                            pd.read_parquet(p).drop(columns=["hex8_of"],
                                                    errors="ignore")))
    for label, df in layers9:
        h9 = safe_merge(h9, df, "hex9_id", label, drop_cols=["parent_hex8", "parent_subzone"])
    h9 = fill_defaults(h9, "hex9_id")
    h9.to_parquet(ROOT / "hex/hex9_all_features.parquet", index=False)
    print(f"  hex9_all_features: {h9.shape}")

    # === HEX-8 ===
    print("\n--- HEX-8 ---")
    h8_uni = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")
    h8_pop = pd.read_parquet(ROOT / "hex/hex8_population.parquet")
    h8_lu = pd.read_parquet(ROOT / "hex/hex8_land_use.parquet")
    h8_bld = pd.read_parquet(ROOT / "hex/hex8_buildings_clean.parquet")
    h8_rd = pd.read_parquet(ROOT / "hex/hex8_roads_clean.parquet")
    h8_tr = pd.read_parquet(ROOT / "hex/hex8_transit_clean.parquet")
    h8_wk = pd.read_parquet(ROOT / "hex/hex8_walkability.parquet")
    h8_sat_path = ROOT / "hex/hex8_satellite.parquet"
    h8_sat = pd.read_parquet(h8_sat_path) if h8_sat_path.exists() else None
    h8_pc_path = ROOT / "hex/hex8_place_composition.parquet"
    h8_pc = pd.read_parquet(h8_pc_path) if h8_pc_path.exists() else None
    h8_pr_path = ROOT / "hex/hex8_hdb_resale.parquet"
    h8_pr = pd.read_parquet(h8_pr_path) if h8_pr_path.exists() else None
    h8_sc_path = ROOT / "hex/hex8_schools.parquet"
    h8_sc = pd.read_parquet(h8_sc_path) if h8_sc_path.exists() else None
    h8_ax_path = ROOT / "hex/hex8_amenities_extra.parquet"
    h8_ax = pd.read_parquet(h8_ax_path) if h8_ax_path.exists() else None
    h8_rg_path = ROOT / "hex/hex8_spatial_rings.parquet"
    h8_rg = pd.read_parquet(h8_rg_path) if h8_rg_path.exists() else None
    h8_cp_path = ROOT / "hex/hex8_composites.parquet"
    h8_cp = pd.read_parquet(h8_cp_path) if h8_cp_path.exists() else None
    h8_dp_path = ROOT / "hex/hex8_demand_pull.parquet"
    h8_dp = pd.read_parquet(h8_dp_path) if h8_dp_path.exists() else None
    h8_sy_path = ROOT / "hex/hex8_synergy.parquet"
    h8_sy = pd.read_parquet(h8_sy_path) if h8_sy_path.exists() else None
    h8_sg_path = ROOT / "hex/hex8_saturation_gap.parquet"
    h8_sg = pd.read_parquet(h8_sg_path) if h8_sg_path.exists() else None
    h8_mr_path = ROOT / "hex/hex8_micrograph_rollup.parquet"
    h8_mr = pd.read_parquet(h8_mr_path) if h8_mr_path.exists() else None
    h8_ws_path = ROOT / "hex/hex8_walk_scores.parquet"
    h8_ws = pd.read_parquet(h8_ws_path) if h8_ws_path.exists() else None
    h8_op_path = ROOT / "hex/hex8_osm_pois.parquet"
    h8_op = pd.read_parquet(h8_op_path) if h8_op_path.exists() else None
    h8_lc_path = ROOT / "hex/hex8_landcover.parquet"
    h8_lc = pd.read_parquet(h8_lc_path) if h8_lc_path.exists() else None
    h8_pw_path = ROOT / "hex/hex8_pop_weighted.parquet"
    h8_pw = pd.read_parquet(h8_pw_path) if h8_pw_path.exists() else None
    h8_ts_path = ROOT / "hex/hex8_traffic_signals.parquet"
    h8_ts = pd.read_parquet(h8_ts_path) if h8_ts_path.exists() else None
    h8_gw_path = ROOT / "hex/hex8_gtfs_windows.parquet"
    h8_gw = pd.read_parquet(h8_gw_path) if h8_gw_path.exists() else None
    h8_pc2_path = ROOT / "hex/hex8_place_composition_v2.parquet"
    h8_pc2 = pd.read_parquet(h8_pc2_path) if h8_pc2_path.exists() else None
    h8_lpv_path = ROOT / "hex/hex8_lta_pv.parquet"
    h8_lpv = pd.read_parquet(h8_lpv_path) if h8_lpv_path.exists() else None
    h8_ldn_path = ROOT / "hex/hex8_lta_dynamic.parquet"
    h8_ldn = pd.read_parquet(h8_ldn_path) if h8_ldn_path.exists() else None
    h8_od_path = ROOT / "hex/hex8_od_features.parquet"
    h8_od = pd.read_parquet(h8_od_path) if h8_od_path.exists() else None
    h8_ca_path = ROOT / "hex/hex8_commercial_activity.parquet"
    h8_ca = pd.read_parquet(h8_ca_path) if h8_ca_path.exists() else None
    h8_nvp_path = ROOT / "hex/hex8_personas_nv.parquet"
    h8_nvp = pd.read_parquet(h8_nvp_path) if h8_nvp_path.exists() else None

    # site-selection layers (S1-S9, all gated — SITE_SELECTION_VALIDATION.md)
    SS_LAYERS8 = ["hex8_daytime_pop", "hex8_iso_walk", "hex8_iso_transit",
                  "hex8_huff_capture", "hex8_acra_biz", "hex8_colo_fit",
                  "hex8_labor_shed", "hex8_visibility", "hex8_rent_surface",
                  "hex8_pipeline", "hex8_context_pack"]

    h8 = h8_uni.copy()
    layers8 = [("pop", h8_pop), ("lu", h8_lu), ("bld", h8_bld),
                ("rd", h8_rd), ("tr", h8_tr), ("wk", h8_wk)]
    if h8_sat is not None: layers8.append(("sat", h8_sat))
    if h8_pc is not None: layers8.append(("pc", h8_pc))
    if h8_pr is not None: layers8.append(("pr", h8_pr))
    if h8_sc is not None: layers8.append(("sc", h8_sc))
    if h8_ax is not None: layers8.append(("ax", h8_ax))
    if h8_rg is not None: layers8.append(("rg", h8_rg))
    if h8_cp is not None: layers8.append(("cp", h8_cp))
    if h8_dp is not None: layers8.append(("dp", h8_dp))
    if h8_sy is not None: layers8.append(("sy", h8_sy))
    if h8_sg is not None: layers8.append(("sg", h8_sg))
    if h8_mr is not None: layers8.append(("mr", h8_mr))
    if h8_ws is not None: layers8.append(("ws", h8_ws))
    if h8_op is not None: layers8.append(("op", h8_op))
    if h8_lc is not None: layers8.append(("lc", h8_lc))
    if h8_pw is not None: layers8.append(("pw", h8_pw))
    if h8_ts is not None: layers8.append(("ts", h8_ts))
    if h8_gw is not None: layers8.append(("gw", h8_gw))
    if h8_pc2 is not None: layers8.append(("pc2", h8_pc2))
    if h8_lpv is not None: layers8.append(("lpv", h8_lpv))
    if h8_ldn is not None: layers8.append(("ldn", h8_ldn))
    if h8_od is not None: layers8.append(("od", h8_od))
    if h8_ca is not None: layers8.append(("ca", h8_ca))
    if h8_nvp is not None: layers8.append(("nvp", h8_nvp))
    for name in SS_LAYERS8:
        p = ROOT / f"hex/{name}.parquet"
        if p.exists():
            layers8.append((name.replace("hex8_", ""), pd.read_parquet(p)))
    for label, df in layers8:
        h8 = safe_merge(h8, df, "hex8_id", label)
    h8 = fill_defaults(h8, "hex8_id")
    h8.to_parquet(ROOT / "hex/hex8_all_features.parquet", index=False)
    print(f"  hex8_all_features: {h8.shape}")

    # === SUBZONE ===
    print("\n--- SUBZONE ---")
    sz_pop = pd.read_parquet(ROOT / "hex/subzone_population.parquet")
    sz_lu = pd.read_parquet(ROOT / "hex/subzone_land_use.parquet")
    sz_bld = pd.read_parquet(ROOT / "hex/subzone_buildings_clean.parquet")
    sz_rd = pd.read_parquet(ROOT / "hex/subzone_roads_clean.parquet")
    sz_tr = pd.read_parquet(ROOT / "hex/subzone_transit_clean.parquet")
    sz_wk = pd.read_parquet(ROOT / "hex/subzone_walkability.parquet")
    sz_sat_path = ROOT / "hex/subzone_satellite.parquet"
    sz_sat = pd.read_parquet(sz_sat_path) if sz_sat_path.exists() else None
    sz_pc_path = ROOT / "hex/subzone_place_composition.parquet"
    sz_pc = pd.read_parquet(sz_pc_path) if sz_pc_path.exists() else None
    sz_pr_path = ROOT / "hex/subzone_hdb_resale.parquet"
    sz_pr = pd.read_parquet(sz_pr_path) if sz_pr_path.exists() else None
    sz_sc_path = ROOT / "hex/subzone_schools.parquet"
    sz_sc = pd.read_parquet(sz_sc_path) if sz_sc_path.exists() else None
    sz_ax_path = ROOT / "hex/subzone_amenities_extra.parquet"
    sz_ax = pd.read_parquet(sz_ax_path) if sz_ax_path.exists() else None
    sz_cp_path = ROOT / "hex/subzone_composites.parquet"
    sz_cp = pd.read_parquet(sz_cp_path) if sz_cp_path.exists() else None
    sz_dp_path = ROOT / "hex/subzone_demand_pull.parquet"
    sz_dp = pd.read_parquet(sz_dp_path) if sz_dp_path.exists() else None
    sz_sy_path = ROOT / "hex/subzone_synergy.parquet"
    sz_sy = pd.read_parquet(sz_sy_path) if sz_sy_path.exists() else None
    sz_sg_path = ROOT / "hex/subzone_saturation_gap.parquet"
    sz_sg = pd.read_parquet(sz_sg_path) if sz_sg_path.exists() else None
    sz_ar_path = ROOT / "hex/subzone_archetypes.parquet"
    sz_ar = pd.read_parquet(sz_ar_path) if sz_ar_path.exists() else None
    sz_mr_path = ROOT / "hex/subzone_micrograph_rollup.parquet"
    sz_mr = pd.read_parquet(sz_mr_path) if sz_mr_path.exists() else None
    sz_ws_path = ROOT / "hex/subzone_walk_scores.parquet"
    sz_ws = pd.read_parquet(sz_ws_path) if sz_ws_path.exists() else None
    sz_op_path = ROOT / "hex/subzone_osm_pois.parquet"
    sz_op = pd.read_parquet(sz_op_path) if sz_op_path.exists() else None
    sz_lc_path = ROOT / "hex/subzone_landcover.parquet"
    sz_lc = pd.read_parquet(sz_lc_path) if sz_lc_path.exists() else None
    sz_ts_path = ROOT / "hex/subzone_traffic_signals.parquet"
    sz_ts = pd.read_parquet(sz_ts_path) if sz_ts_path.exists() else None
    sz_gw_path = ROOT / "hex/subzone_gtfs_windows.parquet"
    sz_gw = pd.read_parquet(sz_gw_path) if sz_gw_path.exists() else None
    sz_pc2_path = ROOT / "hex/subzone_place_composition_v2.parquet"
    sz_pc2 = pd.read_parquet(sz_pc2_path) if sz_pc2_path.exists() else None
    sz_lpv_path = ROOT / "hex/subzone_lta_pv.parquet"
    sz_lpv = pd.read_parquet(sz_lpv_path) if sz_lpv_path.exists() else None
    sz_ldn_path = ROOT / "hex/subzone_lta_dynamic.parquet"
    sz_ldn = pd.read_parquet(sz_ldn_path) if sz_ldn_path.exists() else None

    # Use sz_lu as base since it has subzone_c column (others rely on it)
    sz = sz_pop.copy()
    layers_sz = [("lu", sz_lu), ("bld", sz_bld), ("rd", sz_rd),
                  ("tr", sz_tr), ("wk", sz_wk)]
    if sz_sat is not None: layers_sz.append(("sat", sz_sat))
    if sz_pc is not None: layers_sz.append(("pc", sz_pc))
    if sz_pr is not None: layers_sz.append(("pr", sz_pr))
    if sz_sc is not None: layers_sz.append(("sc", sz_sc))
    if sz_ax is not None: layers_sz.append(("ax", sz_ax))
    if sz_cp is not None: layers_sz.append(("cp", sz_cp))
    if sz_dp is not None: layers_sz.append(("dp", sz_dp))
    if sz_sy is not None: layers_sz.append(("sy", sz_sy))
    if sz_sg is not None: layers_sz.append(("sg", sz_sg))
    if sz_ar is not None: layers_sz.append(("ar", sz_ar))
    if sz_mr is not None: layers_sz.append(("mr", sz_mr))
    if sz_ws is not None: layers_sz.append(("ws", sz_ws))
    if sz_op is not None: layers_sz.append(("op", sz_op))
    if sz_lc is not None: layers_sz.append(("lc", sz_lc))
    if sz_ts is not None: layers_sz.append(("ts", sz_ts))
    if sz_gw is not None: layers_sz.append(("gw", sz_gw))
    if sz_pc2 is not None: layers_sz.append(("pc2", sz_pc2))
    if sz_lpv is not None: layers_sz.append(("lpv", sz_lpv))
    if sz_ldn is not None: layers_sz.append(("ldn", sz_ldn))
    for label, df in layers_sz:
        sz = safe_merge(sz, df, "subzone_c", label)
    sz = fill_defaults(sz, "subzone_c")
    sz.to_parquet(ROOT / "hex/subzone_all_features.parquet", index=False)
    print(f"  subzone_all_features: {sz.shape}")

    # Summary
    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "shapes": {
            "hex9_all_features": list(h9.shape),
            "hex8_all_features": list(h8.shape),
            "subzone_all_features": list(sz.shape),
        },
    }
    with open(ROOT / "hex/all_features_report.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n=== Summary ===")
    print(f"  hex9: {h9.shape[0]:,} × {h9.shape[1]} cols")
    print(f"  hex8: {h8.shape[0]:,} × {h8.shape[1]} cols")
    print(f"  subzone: {sz.shape[0]:,} × {sz.shape[1]} cols")


if __name__ == "__main__":
    main()
