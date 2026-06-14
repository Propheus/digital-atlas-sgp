"""Domain Pack 3 — Public Utilities. Hero: load proxy + diurnal + EV gap.
Honest: modelled relative load, not SCADA/kWh."""
from pack_util import load, col, minmax, score100, save


def main():
    df = load()
    o = {}
    load_proxy = (minmax(col(df, "nl_2024")) * minmax(col(df, "est_total_floor_area_m2"))
                  * (0.6 * col(df, "lu_residential_pct") + 1.0 * col(df, "lu_commercial_pct")
                     + 0.9 * col(df, "lu_business_pct")).clip(lower=0.05))
    o["utility_load_score"] = score100(load_proxy)
    o["utility_load_growth_score"] = score100(load_proxy * (1 + col(df, "nl_change_pct").clip(-0.5, 2)))
    o["utility_water_score"] = score100(col(df, "water_demand_proxy"))
    o["utility_waste_score"] = score100(col(df, "waste_gen_proxy"))
    o["utility_ev_gap_score"] = score100(col(df, "ev_charging_gap"))
    o["utility_diurnal_swing"] = (col(df, "diurnal_swing").clip(-1, 5) * 100).round(0).astype(int)
    o["utility_equity_score"] = score100((1 - minmax(col(df, "min15_score")))
                                         * minmax(col(df, "vulnerability_share")))
    o["utility_resilience_score"] = score100(minmax(col(df, "min15_health"))
                                             + minmax(col(df, "pop_65plus")))  # critical-customer density
    for k, v in o.items():
        df[k] = v
    save(df, list(o), "utilities")


if __name__ == "__main__":
    main()
