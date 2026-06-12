"""
Plexis SGP v5 — S11 Mobility pack per hex8.

Curated import from the validated mobility-v2 adequacy model (same hex8 grid,
direct join) + overlay-derived linkway/cycling features. Curation rationale in
S11_MOBILITY_PACK.md: TAKE ~88 / DERIVE 3 / SKIP ~117 (duplicates, display
bands, legacy, internal compounds).

Self-dedupe: any TAKE column with |r| >= 0.98 against an existing v5 master
column is DROPPED here (logged in the report) — "best of", not "all of".

Source: sgp-mobility-v2/dist/data/hex8_adequacy.geojson (deployed = validated
truth) + overlays/{covered_linkway,cycling_paths}.geojson.

Output: hex/hex8_mobility_pack.parquet + hex/mobility_pack_report.json
"""
import json
import os
import time
from pathlib import Path

import h3
import numpy as np
import pandas as pd
import shapely.geometry as sg
from pyproj import Transformer

ROOT = Path(__file__).parent
SRC = Path(os.environ.get("MOBILITY_SRC", "/home/azureuser/sgp-mobility-v2/dist/data"))

TIME_ANCHORS = ["cbd", "orchard", "jurong_east", "one_north", "changi_business",
                "tampines_hub", "nus", "ntu", "sgh", "cgh", "kkh", "ttsh"]

TAKE_PLAIN = (
    [f"time_to_{a}_min" for a in TIME_ANCHORS]
    + ["n_dest_reachable", "n_dest_within_45min", "pct_dest_within_45min",
       "pct_dest_within_60min", "n_lines_to_cbd", "n_stations_walking",
       "mrt_reach_eff_min", "mrt_reach_walk_min", "mrt_reach_bus_min",
       "mrt_reach_bus_wait_min", "mrt_reach_crowd", "mrt_reach_index",
       "mrt_reach_n_feeders", "mrt_reach_mode",
       "peak_wait_min", "peak_wait_bus_only_min", "peak_wait_mrt_only_min",
       "crowding_load_factor"]
    + ["min15_score", "min15_essentials", "min15_health", "min15_retail",
       "min15_school", "min15_count_essentials", "min15_count_health",
       "min15_count_retail", "min15_count_school", "min15_nearest_clinic_m",
       "min15_nearest_hawker_m", "min15_nearest_park_m", "min15_nearest_school_m",
       "min15_nearest_super_m"]
    + ["pop_resident_citizen", "pop_resident_pr", "pop_nr_ep", "pop_nr_fdw",
       "pop_nr_sp", "pop_nr_wp_other", "low_income_pop", "walking_dependent_count"]
    + ["vulnerability_share", "vulnerability_penalty", "access_vuln_share",
       "access_vuln_penalty", "crowd_sensitive_share", "crowd_equity_penalty"]
    + ["ped_crossings_count", "ped_greenman_count", "lrt_stations",
       "lrt_stations_in_500m", "dist_to_nearest_lrt_m", "bus_stops_in_400m",
       "bus_stops_in_800m", "mrt_stations_in_500m", "mrt_stations_in_1km",
       "nearest_mrt_st_peak_taps", "last_mile_friction", "multimodal_score",
       "transit_mode_count"]
    + ["industrial_adjacency_score", "zone_type", "zone_type_broad"]
)

RENAME = {
    "adequacy_default": "adq_default", "adequacy_core": "adq_core",
    "adequacy_v2": "adq_v2",
    "adequacy_default_elderly": "adq_default_elderly",
    "adequacy_default_family": "adq_default_family",
    "adequacy_default_workers": "adq_default_workers",
    "adequacy_core_elderly": "adq_core_elderly",
    "adequacy_core_family": "adq_core_family",
    "adequacy_core_workers": "adq_core_workers",
    "gap_default": "adq_gap_default", "gap_core": "adq_gap_core",
    "gap_equity_max": "adq_gap_equity_max",
    "availability_v2": "adq_availability_v2",
    "worst_factor_value": "adq_worst_factor_value",
    "worst_factor": "adq_worst_factor",
    "primary_factor_default": "adq_primary_factor",
    "primary_gap_reason": "adq_primary_gap_reason",
}
for f in ["accessibility", "connectivity", "distance", "last_mile",
          "line_pressure", "low_frequency", "reach_gap", "children_gap",
          "elderly_gap", "dorm_gap", "fdw_gap", "low_income_gap"]:
    RENAME[f"f_{f}"] = f"adq_f_{f}"

DEDUPE_R = 0.98


def overlay_lengths(path, h8_index):
    """Sum centerline lengths (EPSG:3414 m) per hex8 via feature centroid.

    Handles LineStrings (true length) AND thin Polygon footprints, which the
    LTA covered-linkway layer uses — for a ribbon polygon, perimeter/2 is the
    centerline length to good approximation (documented).
    """
    tr = Transformer.from_crs(4326, 3414, always_xy=True)
    d = json.load(open(path))
    acc = {}

    def seglen(coords):
        xs, ys = tr.transform(*np.array(coords).T[:2])
        return float(np.hypot(np.diff(xs), np.diff(ys)).sum())

    for f in d["features"]:
        g = sg.shape(f["geometry"])
        geoms = list(g.geoms) if hasattr(g, "geoms") else [g]
        length = 0.0
        for part in geoms:
            if part.geom_type == "LineString":
                length += seglen(part.coords)
            elif part.geom_type == "Polygon":
                length += seglen(part.exterior.coords) / 2.0   # ribbon centerline
        if length <= 0:
            continue
        c = g.centroid
        hx = h3.latlng_to_cell(c.y, c.x, 8)
        acc[hx] = acc.get(hx, 0.0) + length
    return pd.Series(acc).reindex(h8_index).fillna(0.0)


def main():
    t0 = time.time()
    src = json.load(open(SRC / "hex8_adequacy.geojson"))
    rows = [f["properties"] for f in src["features"]]
    mob = pd.DataFrame(rows)
    print(f"source: {len(mob)} hexes × {len(mob.columns)} props")

    cols = ["hex8_id"] + [c for c in TAKE_PLAIN if c in mob.columns] \
        + [c for c in RENAME if c in mob.columns]
    missing = [c for c in TAKE_PLAIN + list(RENAME) if c not in mob.columns]
    out = mob[cols].rename(columns=RENAME)

    # ---- overlay derivations ----
    out = out.set_index("hex8_id")
    out["linkway_len_m"] = overlay_lengths(SRC / "overlays/covered_linkway.geojson",
                                           out.index).round(1)
    out["cycling_path_len_m"] = overlay_lengths(SRC / "overlays/cycling_paths.geojson",
                                                out.index).round(1)
    master = pd.read_parquet(ROOT / "hex/hex8_all_features.parquet").set_index("hex8_id")
    road_km = (master["road_length_total_m"].reindex(out.index) / 1000.0)
    out["linkway_per_road_km"] = (out["linkway_len_m"]
                                  / road_km.replace(0, np.nan)).round(2)

    # ---- derived ratios: levels duplicate pop columns (dedupe kills them)
    # but the SHARES are novel signal ----
    res = mob.set_index("hex8_id")
    cit = res["pop_resident_citizen"].reindex(out.index)
    pr = res["pop_resident_pr"].reindex(out.index)
    out["pr_share"] = (pr / (cit + pr).replace(0, np.nan)).round(4)
    li = res["low_income_pop"].reindex(out.index)
    popr = res["pop_resident"].reindex(out.index)
    out["low_income_share"] = (li / popr.replace(0, np.nan)).round(4)

    # ---- self-dedupe vs the existing master (|r| >= 0.98 -> drop) ----
    dropped = {}
    num_master = master.select_dtypes(include=[np.number])
    for c in [c for c in out.columns if pd.api.types.is_numeric_dtype(out[c])]:
        r = num_master.corrwith(out[c]).abs().max()
        top = num_master.corrwith(out[c]).abs().idxmax()
        if r >= DEDUPE_R:
            dropped[c] = f"{top} (r={r:.3f})"
    out = out.drop(columns=list(dropped))

    # zone-type NA rule (established project rule): non-residential zones are
    # Not Applicable for NORMATIVE adequacy scores — NaN, never a number.
    # (The source app masks at display time; the master must carry the truth.)
    # Factual metrics (time_to_*, min15, reach) stay — they are measurements.
    NA_ZONES = {"industrial", "airport", "nature", "islands", "future"}
    na_mask = out["zone_type_broad"].isin(NA_ZONES)
    adq_num = [c for c in out.columns if c.startswith(("adq_", "vulnerability_",
                                                       "access_vuln", "crowd_"))
               and pd.api.types.is_numeric_dtype(out[c])]
    out.loc[na_mask, adq_num] = np.nan
    out = out.reset_index()
    out.to_parquet(ROOT / "hex/hex8_mobility_pack.parquet", index=False)

    rep = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "spec": "S11_MOBILITY_PACK.md",
        "source": str(SRC / "hex8_adequacy.geojson"),
        "cols_shipped": int(len(out.columns) - 1),
        "deduped_dropped": dropped,
        "missing_in_source": missing,
        "anchors": {
            "min_time_to_cbd": float(out["time_to_cbd_min"].min()),
            "max_time_to_cbd": float(out["time_to_cbd_min"].max()),
            "min15_max": float(out["min15_score"].max()),
            "linkway_total_km": round(float(out["linkway_len_m"].sum() / 1000), 1),
            "cycling_total_km": round(float(out["cycling_path_len_m"].sum() / 1000), 1),
        },
        "wall_clock_s": round(time.time() - t0, 2),
    }
    json.dump(rep, open(ROOT / "hex/mobility_pack_report.json", "w"), indent=2)
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()
