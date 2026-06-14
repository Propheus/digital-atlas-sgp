"""Domain Pack 2 — Real Estate. Heroes: feasibility + livability + momentum.
v1 = HDB/rent/comps/feasibility; private-price AVM is v2 (paywalled)."""
from pack_util import load, col, minmax, score100, save


def main():
    df = load()
    o = {}
    o["re_feasibility_score"] = score100(minmax(col(df, "pipe_dev_capacity_res"))
                                         + minmax(col(df, "pipe_dev_capacity_com")))
    o["re_livability_score"] = score100(minmax(col(df, "livability_index"))
                                        + minmax(col(df, "family_index"))
                                        + minmax(col(df, "min15_score")))
    o["re_momentum_score"] = score100(minmax(col(df, "nl_change_pct").clip(lower=0))
                                      + minmax(col(df, "biz_formation_5y")))
    o["re_enbloc_score"] = score100(col(df, "enbloc_upside_score"))
    o["re_collateral_score"] = score100(minmax(col(df, "collateral_value_proxy"))
                                        * minmax(col(df, "livability_index"))
                                        - 0.3 * minmax(col(df, "nuisance_penalty")))
    o["re_yield_proxy"] = (col(df, "rent_resi_psf_med")
                           / col(df, "hdb_resale_4r_median_psm", 1).clip(lower=1)).round(4)
    o["re_lease_decay_penalty"] = (col(df, "lease_decay_penalty") * 100).round(0).astype(int)
    for k, v in o.items():
        df[k] = v
    save(df, list(o), "realestate")


if __name__ == "__main__":
    main()
