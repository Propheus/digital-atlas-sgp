"""
Build subzone_state.parquet — the primary per-subzone state vector (t=0).

Authority: v8_subzone_table.parquet (already has population, elderly_pct, hdb_pct, etc.)
Augmented with: persona class mix from persona_features_by_subzone.parquet.

Output schema:
  subzone_code (pk), subzone_name, planning_area, region, area_km2,
  population, elderly_share, working_share, young_share,
  hdb_share, total_dwellings, mrt_stations_in_zone, bus_stops_in_zone,
  affluence_idx, family_idx, retirement_idx,
  excluded (bool — true for sub-500 population zones like water catchment, military, airport)
"""
import pandas as pd
import sys

BASE = "/home/azureuser/digital-atlas-sgp"
OUT = f"{BASE}/scenario_sim/cache/subzone_state.parquet"

def main():
    # --- primary source: V8 subzone table
    v8 = pd.read_parquet(f"{BASE}/model/v8_subzone_table.parquet")
    print(f"[01] V8 table: {v8.shape}")

    keep = [
        "subzone_code", "subzone_name", "planning_area", "region",
        "area_km2", "population", "elderly_pct",
        "hdb_total_pct", "total_dwellings",
        "mrt_stations_in_zone", "bus_stops_in_zone",
    ]
    missing = [c for c in keep if c not in v8.columns]
    if missing:
        print(f"[01] ERROR: V8 table missing expected columns: {missing}", file=sys.stderr)
        sys.exit(1)

    state = v8[keep].copy()
    state = state.rename(columns={
        "hdb_total_pct": "hdb_share",
        "elderly_pct": "elderly_share_v8",
    })

    # --- persona enrichment
    pers = pd.read_parquet(f"{BASE}/data/personas/persona_features_by_subzone.parquet")
    print(f"[01] persona table: {pers.shape}")
    pers_cols = [
        "pct_young_18_30", "pct_working_31_60", "pct_senior_60plus",
        "affluence_idx", "family_idx", "retirement_idx",
    ]
    pers_small = pers[pers_cols].reset_index()  # index is subzone_code
    state = state.merge(pers_small, on="subzone_code", how="left")

    # Normalize class shares. Elderly > pct_senior from persona (60+); if missing, fall back to V8 elderly_pct.
    state["elderly_share"] = state["pct_senior_60plus"].fillna(state["elderly_share_v8"] / 100.0)
    state["young_share"]   = state["pct_young_18_30"].fillna(0.18)
    state["working_share"] = state["pct_working_31_60"].fillna(
        (1.0 - state["elderly_share"] - state["young_share"]).clip(lower=0)
    )
    # Renormalize so the three sum to ~1
    tot = state[["elderly_share", "working_share", "young_share"]].sum(axis=1)
    for c in ["elderly_share", "working_share", "young_share"]:
        state[c] = state[c] / tot

    state = state.drop(columns=["elderly_share_v8", "pct_senior_60plus", "pct_young_18_30", "pct_working_31_60"])

    # --- hdb_share normalization: V8 has it as 0-100, convert to 0-1
    state["hdb_share"] = state["hdb_share"] / 100.0

    # --- exclusion flag: low-population subzones (water catchment, military, airport, industrial-only)
    state["excluded"] = state["population"] < 500
    n_excl = int(state["excluded"].sum())
    print(f"[01] excluded {n_excl} low-population subzones (population < 500)")

    # --- sanity
    assert state["subzone_code"].is_unique, "subzone_code not unique"
    assert len(state) == 332, f"expected 332 subzones, got {len(state)}"

    # --- write
    state.to_parquet(OUT, index=False)
    print(f"[01] wrote {OUT}  shape={state.shape}")
    print(f"[01] sample:\n{state.head(3).to_string()}")

    # summary
    incl = state[~state["excluded"]]
    print(f"\n[01] included: {len(incl)}  total_pop: {incl['population'].sum():,.0f}")
    print(f"[01] population percentiles (included): "
          f"p10={incl['population'].quantile(0.1):.0f} "
          f"p50={incl['population'].quantile(0.5):.0f} "
          f"p90={incl['population'].quantile(0.9):.0f}")

if __name__ == "__main__":
    main()
