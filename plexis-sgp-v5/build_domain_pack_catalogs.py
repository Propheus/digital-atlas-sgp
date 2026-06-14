"""Phase 2 — emit pack catalog JSONs (100%-described discipline)."""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent
META = {
 "retail": {"heroes": ["retail_whitespace_score", "format_fit_score"],
            "use_cases": ["R1","R2","R3","R4","R5","R6","R7","R9","R10"],
            "limits": ["Placement & demand TIER, not store revenue (cap_* is Huff outlet-equivalent)",
                       "Commercial rent is residential-proxy until the 🔴 commercial-rent surface lands"]},
 "realestate": {"heroes": ["re_feasibility_score", "re_livability_score", "re_momentum_score"],
                "use_cases": ["E2","E4","E5","E8","E9","E11"],
                "limits": ["v1 on HDB resale + rent + feasibility; private-unit AVM is v2 (🔴 paywalled)"]},
 "utilities": {"heroes": ["utility_load_score", "utility_ev_gap_score"],
               "use_cases": ["U1","U2","U3","U5","U8","U9","U10"],
               "limits": ["Modelled RELATIVE load, not SCADA/kWh; calibrate to SP if shared"]},
 "transport": {"heroes": ["mobility_access_score", "mobility_desert_priority"],
               "use_cases": ["T1","T2","T3","T4","T9","T10","T11"],
               "limits": ["OD is aggregate in v1; daypart OD is Phase 3"]},
 "insurance": {"heroes": ["insurance_risk_score"],
               "use_cases": ["I1","I3","I4","I5","I6","I7","I8"],
               "limits": ["Hazard stratification, not actuarial pricing",
                          "No crime/theft data in SG open data — that peril omitted, not proxied",
                          "Flood/heat are Phase 3 (lu_water_pct is a weak coastal proxy)"]},
}


def main():
    for pack, meta in META.items():
        p = pd.read_parquet(ROOT / f"hex/hex8_{pack}_pack.parquet")
        cols = [c for c in p.columns if c not in
                ("hex8_id", "parent_subzone", "parent_pa", "parent_region", "zone_type_broad")]
        cat = {"pack": pack, "version": "1.0.0", "scale": "hex8 + subzone rollup",
               "hex8_key": "hex8_id", "n_hex": len(p), "columns": cols,
               "hero_scores": meta["heroes"], "use_cases": meta["use_cases"],
               "limits": meta["limits"],
               "hex8_path": f"hex/hex8_{pack}_pack.parquet",
               "subzone_path": f"hex/subzone_{pack}_pack.parquet"}
        json.dump(cat, open(ROOT / f"catalog/pack_{pack}_catalog.json", "w"), indent=1)
        print(f"pack_{pack}_catalog.json: {len(cols)} cols, heroes {meta['heroes']}")


if __name__ == "__main__":
    main()
