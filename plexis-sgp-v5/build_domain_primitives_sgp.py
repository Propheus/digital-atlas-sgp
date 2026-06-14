"""
Plexis SGP v5 — Phase 0 domain-pack shared primitives.

Derives cross-pack columns from hex8_all_features (no new downloads).
Feeds: retail, realestate, utilities, transport, insurance pack builders.

Output: hex/hex8_domain_primitives.parquet + hex/domain_primitives_report.json

See docs/DOMAIN_PACKS_BUILD_SPEC.md §3.
"""
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
MASTER = ROOT / "hex/hex8_all_features.parquet"
OUT = ROOT / "hex/hex8_domain_primitives.parquet"
REPORT = ROOT / "hex/domain_primitives_report.json"


def minmax(s):
    s = pd.Series(s, dtype=float).fillna(0)
    lo, hi = s.quantile(0.01), s.quantile(0.99)
    if hi <= lo:
        return pd.Series(np.zeros(len(s)), index=s.index)
    return ((s - lo) / (hi - lo)).clip(0, 1)


def inv_dist(s, half=400):
    s = pd.Series(s, dtype=float).fillna(9999)
    return np.exp(-s / half).clip(0, 1)


def col(df, name, default=0.0):
    if name in df.columns:
        return pd.to_numeric(df[name], errors="coerce").fillna(default)
    return pd.Series(default, index=df.index, dtype=float)


def main():
    t0 = time.time()
    df = pd.read_parquet(MASTER)
    key = "hex8_id" if "hex8_id" in df.columns else df.columns[0]
    out = df[[key]].copy()
    log = {"source": str(MASTER), "n_hex": len(df), "cols": [], "skipped": []}

    pop = col(df, "pop_resident", 1)
    dt = col(df, "dt_pop", pop)
    rent = col(df, "rent_resi_psf_med")
    resale = col(df, "hdb_resale_4r_median_psm")

    # --- Retail / shared ---
    cap = col(df, "cap_cafe_coffee") if "cap_cafe_coffee" in df.columns else col(df, "cap_total")
    sat = col(df, "sat_cafe_coffee_per_1k") if "sat_cafe_coffee_per_1k" in df.columns else col(df, "sat_restaurant_per_1k")
    iso_pop = col(df, "iso_walk10_pop")
    pc_rest = col(df, "pc_cat_restaurant")

    out["cannibalization_pressure"] = (minmax(sat) * minmax(cap)).round(4)
    out["delivery_demand_density"] = (
        minmax(iso_pop) * minmax(pc_rest) * (1 - minmax(sat))
    ).round(4)

    wealth_parts = [minmax(rent)]
    for c in ("rwi", "affluence_index", "low_income_share"):
        if c in df.columns:
            wealth_parts.append(minmax(col(df, c)) if c != "low_income_share"
                                else (1 - minmax(col(df, c))))
    out["spend_proxy_index"] = pd.concat(wealth_parts, axis=1).mean(axis=1).round(4)

    # --- Utilities ---
    out["diurnal_load_am"] = dt.round(1)
    out["diurnal_load_pm"] = pop.round(1)
    out["diurnal_swing"] = ((dt - pop) / pop.clip(lower=1)).round(4)

    lu_com = col(df, "lu_commercial_share") if "lu_commercial_share" in df.columns else col(df, "lu_commercial_pct")
    floor_area = col(df, "est_total_floor_area_m2", 1)
    out["water_demand_proxy"] = (pop * 0.15 + floor_area * lu_com * 0.02).round(2)
    comm_density = col(df, "commercial_poi_density", col(df, "pc_total", 0))
    out["waste_gen_proxy"] = (pop * 0.45 + comm_density * 0.1).round(2)

    parking = col(df, "parking_lot_count") + col(df, "hdb_mscp_count")
    car_proxy = minmax(parking) * minmax(rent)
    out["ev_demand_proxy"] = (car_proxy * dt).round(4)
    chargers = col(df, "pc2_cat_transport_ev_count")   # real EV-charger count
    out["ev_charging_gap"] = (out["ev_demand_proxy"] - minmax(chargers)).clip(lower=0).round(4)

    # --- Transport ---
    # total unserved walking demand = sum of per-category iso_walk10_unserved_pop_*
    uns_cols = [c for c in df.columns if c.startswith("iso_walk10_unserved_pop_")]
    unserved = df[uns_cols].apply(pd.to_numeric, errors="coerce").fillna(0).sum(axis=1) \
        if uns_cols else pd.Series(0.0, index=df.index)
    dist_mrt = col(df, "dist_mrt_m", col(df, "pipe_mrt_dist_m", 2000))
    transit = col(df, "transit_score", col(df, "mrt_reach_index", 0.5))

    out["first_last_mile_gap"] = (minmax(unserved) * inv_dist(dist_mrt, 800)).round(4)
    out["transit_desert_score"] = (
        minmax(pop) * inv_dist(dist_mrt, 1200) * (1 - minmax(transit))
    ).round(4)

    footfall = col(df, "vis_exit_footfall", col(df, "od_throughput", 0))
    headway = col(df, "gtfs_headway_am_min", 10).clip(lower=1)
    out["crowding_stress"] = (footfall / headway).round(4)
    out["ridehail_demand_proxy"] = (
        out["first_last_mile_gap"] * minmax(dt) * out["spend_proxy_index"]
    ).round(4)

    # --- Insurance / RE ---
    bldg_d = minmax(col(df, "bldg_density_per_km2", 0))
    age = minmax(col(df, "hdb_avg_age_years", 0))
    lu_ind = col(df, "lu_business_pct", 0)   # SG zones industrial as Business/B1/B2
    ind_adj = minmax(col(df, "industrial_adjacency_score", 0))
    dist_exp = col(df, "dist_expressway_m", 5000)
    out["fire_risk_score"] = (bldg_d * age * (minmax(lu_ind) + ind_adj).clip(0, 1)).round(4)

    inter = minmax(col(df, "road_intersection_density_per_km2", 0))
    od = minmax(col(df, "od_throughput", 0))
    out["auto_exposure_score"] = (inter * inv_dist(dist_exp, 500) * od).round(4)
    out["industrial_hazard_buffer"] = ((minmax(lu_ind) + ind_adj).clip(0, 1) * inv_dist(dist_exp, 300)).round(4)

    silver = minmax(col(df, "pop_65plus", col(df, "silver", 0)))
    min15_h = minmax(col(df, "min15_health", 0))
    vuln = minmax(col(df, "vulnerability_share", col(df, "vulnerability", 0)))
    out["pop_health_risk"] = (silver * (1 - min15_h) * vuln).round(4)

    out["collateral_value_proxy"] = (resale * floor_area * 0.3).round(2)
    sev = minmax(col(df, "expressway_severance", 0))
    # (no airport-distance column in the SG atlas → airport-nuisance term dropped)
    out["nuisance_penalty"] = (sev + minmax(lu_ind) + ind_adj).clip(0, 2).round(4)

    pipe_res = minmax(col(df, "pipe_dev_capacity_res", 0))
    nl_chg = minmax(col(df, "nl_change_pct", col(df, "nl_change", 0)))
    out["enbloc_upside_score"] = (age * pipe_res * nl_chg).round(4)

    lease = col(df, "hdb_resale_avg_lease_remaining_yrs", col(df, "avg_lease_remaining_yrs", 80))
    out["lease_decay_penalty"] = (1 - minmax(lease)).round(4)

    out.to_parquet(OUT, index=False)
    log["cols"] = [c for c in out.columns if c != key]
    log["elapsed_s"] = round(time.time() - t0, 1)
    log["spot"] = {
        "transit_desert_p90": float(out["transit_desert_score"].quantile(0.9)),
        "crowding_stress_p90": float(out["crowding_stress"].quantile(0.9)),
    }
    REPORT.write_text(json.dumps(log, indent=2))
    print(f"Wrote {OUT} ({len(out)} rows, {len(log['cols'])} cols) in {log['elapsed_s']}s")
    print(json.dumps(log["spot"], indent=2))


if __name__ == "__main__":
    main()