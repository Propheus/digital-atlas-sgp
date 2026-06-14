"""Domain Pack 4 — Transport. Heroes: access + desert + crowding + TOD + ride-hail.
Atlas's strongest area — mostly curate od_*/iso_*; daypart OD is Phase 3."""
from pack_util import load, col, minmax, inv_dist, score100, save


def main():
    df = load()
    o = {}
    o["mobility_access_score"] = score100(minmax(col(df, "transit_score"))
                                          + minmax(col(df, "walkability_score"))
                                          + minmax(col(df, "multimodal_score")))
    o["mobility_desert_priority"] = score100(col(df, "transit_desert_score") * minmax(col(df, "pop_resident")))
    o["mobility_crowding_score"] = score100(col(df, "crowding_stress"))
    o["mobility_tod_score"] = score100(inv_dist(col(df, "pipe_mrt_dist_m", 5000), 800)
                                       * minmax(col(df, "pipe_dev_capacity_res"))
                                       * minmax(col(df, "od_throughput")))
    o["mobility_ridehail_score"] = score100(col(df, "ridehail_demand_proxy"))
    o["mobility_firstlast_gap_score"] = score100(col(df, "first_last_mile_gap"))
    o["mobility_parking_stress"] = score100(col(df, "dt_pop")
                                            / (col(df, "parking_lot_count") + col(df, "hdb_mscp_count") + 1))
    o["modal_split_proxy"] = score100(minmax(col(df, "parking_lot_count"))
                                      * (1 - minmax(col(df, "transit_score"))))
    for k, v in o.items():
        df[k] = v
    save(df, list(o), "transport")


if __name__ == "__main__":
    main()
