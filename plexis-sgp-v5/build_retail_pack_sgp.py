"""Domain Pack 1 — Retail. Hero: whitespace + format-fit (per default category)."""
from pack_util import load, col, minmax, score100, save

CAT = "cafe_coffee"   # default category (parameterise later)


def main():
    df = load()
    o = {}
    # hero: under-supplied AND winnable. NOTE: gap_<cat> is ~0.84 everywhere
    # (no variance) so it collapses a product → use UNSERVED residents (real
    # variance) + winnable demand as an additive blend.
    o["retail_whitespace_score"] = score100(
        0.5 * minmax(col(df, f"cap_{CAT}"))
        + 0.5 * minmax(col(df, f"iso_walk10_unserved_pop_{CAT}")))
    o["retail_competition_pressure"] = score100(minmax(col(df, f"sat_{CAT}_per_1k"))
                                                + minmax(col(df, f"mg_{CAT}_pressure_400m")))
    # V4: footfall component = the decontaminated retail_footfall_score (NOT vis_exit point-source)
    o["format_fit_score"] = score100(minmax(col(df, "walkability_score"))
                                     * minmax(col(df, "retail_footfall_score"))
                                     * minmax(col(df, f"colo_fit_{CAT}")).clip(lower=0.05))
    o["retail_cannibalization_score"] = score100(col(df, "cannibalization_pressure"))
    o["retail_delivery_score"] = score100(col(df, "delivery_demand_density"))
    # V4: retail_footfall_score is OWNED upstream by the base feature fix (dt-mostly + hub
    # decile + dead-port NA). Pass it through unchanged so a re-fold never reverts it.
    o["retail_footfall_score"] = col(df, "retail_footfall_score")
    # demand-tier vs rent-tier (honest: tier match, not ROI)
    cap_p = minmax(col(df, f"cap_{CAT}"))
    rent_p = minmax(col(df, "rent_resi_psf_med"))
    tier = (cap_p - rent_p)                 # demand richer than cost = value site
    o["rent_demand_tier"] = score100(tier)  # high = demand-rich for the rent tier

    for k, v in o.items():
        df[k] = v
    save(df, list(o), "retail")


if __name__ == "__main__":
    main()
