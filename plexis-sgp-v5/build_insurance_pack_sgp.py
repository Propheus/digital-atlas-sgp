"""Domain Pack 5 — Insurance & Risk. Hero: location risk score by peril.
Honest: hazard stratification, not actuarial pricing. No crime/theft data in SG.
Flood/heat are Phase 3 (lu_water_pct is a weak coastal proxy for v1)."""
from pack_util import load, col, minmax, score100, save


def main():
    df = load()
    o = {}
    o["risk_fire_score"] = score100(col(df, "fire_risk_score"))
    o["risk_auto_score"] = score100(col(df, "auto_exposure_score"))
    o["risk_health_score"] = score100(col(df, "pop_health_risk"))
    o["risk_bi_failure_score"] = score100(col(df, "biz_recent_dead_share"))   # the unique asset
    o["risk_collateral_score"] = score100(col(df, "collateral_value_proxy"))
    o["risk_nuisance_score"] = score100(col(df, "nuisance_penalty") + col(df, "industrial_hazard_buffer"))
    o["risk_coastal_proxy"] = score100(col(df, "lu_water_pct"))   # weak flood proxy (Phase 3 deepens)

    # blended hero (flood omitted in v1; weights renormalised)
    blend = (0.30 * minmax(col(df, "fire_risk_score"))
             + 0.25 * minmax(col(df, "biz_recent_dead_share"))
             + 0.20 * minmax(col(df, "auto_exposure_score"))
             + 0.15 * minmax(col(df, "pop_health_risk"))
             + 0.10 * minmax(col(df, "nuisance_penalty")))
    o["insurance_risk_score"] = score100(blend)
    o["insurance_accumulation_band"] = score100(blend * minmax(col(df, "collateral_value_proxy")))
    for k, v in o.items():
        df[k] = v
    save(df, list(o), "insurance")


if __name__ == "__main__":
    main()
