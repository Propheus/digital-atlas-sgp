"""Step 5: 5-band scores + final adequacy table.

Maps gap_default and each factor to bands:
  Excellent  v < 0.30
  Good       0.30 ≤ v < 0.50
  Moderate   0.50 ≤ v < 0.70
  Poor       0.70 ≤ v < 0.85
  Critical   v ≥ 0.85

Outputs:
  data/hex_v11/hex8_adequacy.parquet    — clean adequacy view (50 cols)
  data/hex_v11/hex8_adequacy.geojson    — for UI (Mapbox/Deck.gl)
  data/hex_v11/REPORT.md                — distribution summary
"""

import pandas as pd
import numpy as np
import json
import h3
from pathlib import Path

IN_PATH = Path('data/hex_v11/hex8_adequacy_features.parquet')
OUT_PARQ = Path('data/hex_v11/hex8_adequacy.parquet')
OUT_GEO  = Path('data/hex_v11/hex8_adequacy.geojson')
OUT_RPT  = Path('data/hex_v11/REPORT.md')

BANDS = [
    ('excellent', 0.00, 0.30),
    ('good',      0.30, 0.50),
    ('moderate',  0.50, 0.70),
    ('poor',      0.70, 0.85),
    ('critical',  0.85, 1.01),
]

FACTORS = [
    'f_accessibility','f_distance','f_last_mile','f_connectivity',
    'f_line_pressure','f_low_frequency',
    'f_children_gap','f_low_income_gap',
    'f_dorm_gap','f_elderly_gap','f_fdw_gap',
]

KEEP_COLS = [
    'hex8_id','lat','lng','area_km2',
    'parent_subzone','parent_pa','parent_region',
    'zone_type','zone_type_broad','is_scored','is_data_shown',
    # Demographics
    'pop_total','pop_resident','pop_resident_citizen','pop_resident_pr',
    'pop_non_resident','pop_nr_dorm','pop_nr_fdw','pop_nr_ep','pop_nr_sp','pop_nr_wp_other',
    'children_count','elderly_count','working_age_count','walking_dependent_count',
    'low_income_pop','pop_density_per_km2','hdb_pop_share',
    # Transit infra
    'mrt_stations','mrt_stations_in_500m','mrt_stations_in_1km','mrt_lines_count',
    'lrt_stations','lrt_stations_in_500m','dist_to_nearest_lrt_m',
    'bus_stops','bus_stops_in_400m','bus_stops_in_800m','bus_routes_count',
    'dist_nearest_mrt_m','dist_bus_m','transit_mode_count',
    # Transit usage
    'mrt_daily_taps','bus_daily_taps','transit_daily_taps',
    'mrt_taps_per_capita','bus_taps_per_capita',
    # Last mile / walk
    'walk_mrt_score','pedestrian_crossings_count','last_mile_friction',
    # Built form
    'bldg_count','bldg_hdb_residential','bldg_private_residential',
    'lu_residential_pct','lu_commercial_pct','lu_business_pct',
    'land_use_entropy','multimodal_score',
    'cbd_km','cbd_proximity_score','industrial_adjacency_score',
    # Amenities
    'dist_school_m','dist_clinic_m','dist_hawker_m','dist_park_m','dist_super_m',
    # Active flag
    'cell_active_flag',
    # Factors
    *FACTORS,
    'gap_core','gap_equity_max','gap_default',
    # === Adequacy v2 — service quality (frequency + reach + crowding + resilience) ===
    'peak_wait_min','peak_wait_bus_only_min','peak_wait_mrt_only_min',
    'time_to_cbd_min','time_to_orchard_min','time_to_jurong_east_min',
    'time_to_tampines_hub_min','time_to_changi_business_min','time_to_one_north_min',
    'time_to_nus_min','time_to_ntu_min','time_to_sgh_min','time_to_ttsh_min',
    'time_to_kkh_min','time_to_cgh_min',
    'pct_dest_within_45min','pct_dest_within_60min','n_dest_within_45min','n_dest_reachable',
    'nearest_mrt_st_peak_taps','crowding_load_factor','n_lines_to_cbd','n_stations_walking',
    'frequency_adequacy_gap','reach_adequacy_gap','crowding_adequacy_gap','resilience_adequacy_gap',
    'availability_adequacy_gap','quality_only_gap','adequacy_core','adequacy_default',
    'vulnerability_share','vulnerability_penalty',
    # Per-profile (default profile already covered above by the bare names)
    'availability_adequacy_gap_elderly','quality_only_gap_elderly','adequacy_core_elderly',
    'vulnerability_penalty_elderly','adequacy_default_elderly',
    'availability_adequacy_gap_family','quality_only_gap_family','adequacy_core_family',
    'vulnerability_penalty_family','adequacy_default_family',
    'availability_adequacy_gap_workers','quality_only_gap_workers','adequacy_core_workers',
    'vulnerability_penalty_workers','adequacy_default_workers',
]

def band(v):
    for name, lo, hi in BANDS:
        if lo <= v < hi: return name
    return 'critical'

def hex8_to_polygon(hex_id):
    boundary = h3.cell_to_boundary(hex_id)  # [(lat,lng), ...]
    # Mapbox expects [lng, lat]
    coords = [[lng, lat] for (lat, lng) in boundary]
    coords.append(coords[0])
    return [coords]

def main():
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from hdb_towns import zone_type_of, refine_zone_type, SCORED_ZONES, DATA_SHOWN_ZONES

    h = pd.read_parquet(IN_PATH)
    print(f'Loaded {h.shape}')

    # === Two-stage zone classification ===
    # Stage 1: broad type from PA name (residential/industrial/airport/etc.)
    h['zone_type_broad'] = h['parent_pa'].apply(lambda p: zone_type_of(p) if p else 'unknown')
    # Stage 2: refine PER HEX based on MRT presence + dorm population.
    # This is what lets us distinguish Tuas Bay (industrial_with_transit) from
    # Sungei Kadut warehouse (industrial_empty), and Changi Lodge dorm
    # (airport_residential_edge) from the runway (airport_operations).
    def _refine(row):
        return refine_zone_type(row['zone_type_broad'], row)
    h['zone_type'] = h.apply(_refine, axis=1)
    h['is_scored'] = h['zone_type'].isin(SCORED_ZONES)
    h['is_data_shown'] = h['zone_type'].isin(DATA_SHOWN_ZONES)
    print('Broad zone_type distribution:')
    print(h['zone_type_broad'].value_counts().to_string())
    print('\nRefined zone_type distribution:')
    print(h['zone_type'].value_counts().to_string())
    print(f'\nScored: {int(h["is_scored"].sum())}  |  Data-shown: {int(h["is_data_shown"].sum())}  |  N/A: {int((~h["is_scored"] & ~h["is_data_shown"]).sum())}')

    # Keep only intended cols (some may be missing — handle gracefully)
    cols = [c for c in KEEP_COLS if c in h.columns]
    out = h[cols].copy()
    print(f'Trimmed to {len(cols)} cols')

    # Band labels per factor and overall
    for f in FACTORS + ['gap_default', 'adequacy_default']:
        if f in out.columns:
            out[f'{f}_band'] = out[f].apply(band)

    # Worst-factor identification (the one that drives the overall band)
    factor_cols = [f for f in FACTORS if f in out.columns]
    out['worst_factor'] = out[factor_cols].idxmax(axis=1)
    out['worst_factor_value'] = out[factor_cols].max(axis=1)

    # Primary gap reason derived from worst factor (replaces stale gap_reason)
    REASON_MAP = {
        'f_accessibility': 'walk_unfriendly',
        'f_distance':      'far_from_transit',
        'f_last_mile':     'last_mile_friction',
        'f_connectivity':  'few_modes',
        'f_line_pressure': 'overcrowded_lines',
        'f_low_frequency': 'low_service_frequency',
        'f_children_gap':  'children_school_gap',
        'f_low_income_gap':'low_income_transit_gap',
        'f_dorm_gap':      'dorm_worker_connectivity_gap',
        'f_elderly_gap':   'elderly_isolation',
        'f_fdw_gap':       'fdw_off_day_gap',
    }
    out['primary_gap_reason'] = out['worst_factor'].map(REASON_MAP)
    # If worst is in excellent band, override to 'well_served'
    out.loc[out['worst_factor_value'] < 0.30, 'primary_gap_reason'] = 'well_served'

    out.to_parquet(OUT_PARQ, index=False)
    print(f'Wrote {OUT_PARQ}')

    # GeoJSON for the UI
    print('Building GeoJSON…')
    features = []
    for _, r in out.iterrows():
        props = {k: (None if pd.isna(v) else (float(v) if isinstance(v, (np.floating, float)) else (int(v) if isinstance(v, (np.integer,)) else v))) for k, v in r.to_dict().items()}
        features.append({
            'type': 'Feature',
            'geometry': {'type': 'Polygon', 'coordinates': hex8_to_polygon(r['hex8_id'])},
            'properties': props,
        })
    gj = {'type': 'FeatureCollection', 'features': features}
    with open(OUT_GEO, 'w') as f:
        json.dump(gj, f, separators=(',', ':'))
    sz_mb = OUT_GEO.stat().st_size / 1e6
    print(f'Wrote {OUT_GEO} ({sz_mb:.2f} MB)')

    # === REPORT ===
    active = out[out['cell_active_flag'] == 1] if 'cell_active_flag' in out.columns else out
    n_active = len(active)
    band_dist = active['gap_default_band'].value_counts().reindex([b[0] for b in BANDS], fill_value=0)
    pop_by_band = active.groupby('gap_default_band')['pop_total'].sum().reindex([b[0] for b in BANDS], fill_value=0)

    rpt = [
        '# hex_v11 — Transport Adequacy Report\n',
        f'**Built:** 2026-05-28  ·  **Hex resolution:** H3 res 8 (1,191 cells)  ·  **Total pop:** 6,110,000\n',
        '## Active vs gray-out',
        f'- Active cells (pop ≥ 50 OR commercial/dorm activity): **{n_active}** / {len(out)}',
        f'- Gray-out (sparse): {len(out) - n_active} cells\n',
        '## Composite gap distribution (active cells only)\n',
        '| Band | Cells | % | Population | % of pop |',
        '|---|---:|---:|---:|---:|',
    ]
    total_act_pop = active['pop_total'].sum()
    for b, _, _ in BANDS:
        cn = band_dist[b]
        pn = pop_by_band[b]
        rpt.append(f'| {b.title()} | {cn} | {cn/n_active*100:.1f}% | {pn:,.0f} | {pn/total_act_pop*100:.1f}% |')

    rpt.append('\n## Per-factor band distribution (active cells)\n')
    rpt.append('| Factor | Excellent | Good | Moderate | Poor | Critical | Median |')
    rpt.append('|---|---:|---:|---:|---:|---:|---:|')
    for f in FACTORS:
        bcol = f + '_band'
        if bcol not in active.columns: continue
        d = active[bcol].value_counts()
        med = active[f].median()
        rpt.append(f'| {f} | {d.get("excellent",0)} | {d.get("good",0)} | {d.get("moderate",0)} | {d.get("poor",0)} | {d.get("critical",0)} | {med:.3f} |')

    rpt.append('\n## Top-10 primary_gap_reason among active cells\n')
    rpt.append('| Reason | Cells | Pop |')
    rpt.append('|---|---:|---:|')
    reason_cnt = active.groupby('primary_gap_reason').agg(cells=('hex8_id','count'), pop=('pop_total','sum')).sort_values('cells', ascending=False).head(10)
    for r, row in reason_cnt.iterrows():
        rpt.append(f'| {r} | {row["cells"]} | {row["pop"]:,.0f} |')

    rpt.append('\n## Top-20 worst hex cells\n')
    rpt.append('| Subzone | Hex | Pop | gap_default | Worst factor | Reason |')
    rpt.append('|---|---|---:|---:|---|---|')
    worst = active.nlargest(20, 'gap_default')
    for _, r in worst.iterrows():
        rpt.append(f'| {r["parent_subzone"]} | {r["hex8_id"][-6:]} | {r["pop_total"]:,.0f} | {r["gap_default"]:.3f} | {r["worst_factor"]} | {r["primary_gap_reason"]} |')

    OUT_RPT.write_text('\n'.join(rpt))
    print(f'Wrote {OUT_RPT}')

if __name__ == '__main__':
    main()
