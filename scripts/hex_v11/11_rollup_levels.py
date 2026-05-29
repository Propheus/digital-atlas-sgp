"""Aggregate hex8 → Subzone / Planning Area / HDB Town.

Each level table has the same schema for UI compatibility. Outputs:
  data/hex_v11/subzone_adequacy.parquet  (~274 rows)
  data/hex_v11/pa_adequacy.parquet       (55 rows)
  data/hex_v11/town_adequacy.parquet     (25 rows — HDB Towns only)

Aggregation rules (per advisor + ideation):
  - Sums for population (resident, NR sub-buckets, children, elderly)
  - Pop-weighted means for distances, walkability, taps-per-capita
  - DISTINCT counts (union across child cells) for MRT lines, bus routes
  - Two complementary factor aggregates: pop-weighted mean AND worst-cell max
  - Equity range = max factor − min factor across child active cells
  - within_800m_mrt_pct = pop of cells with mrt within 800m / total pop
  - dominant_gap_reason = primary_gap_reason of the child cell carrying most pop in band ≥ Moderate
  - national_rank = rank by gap_default (1 = best) per level
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hdb_towns import classify_pa, zone_type_of, SCORED_ZONES

INP = Path('data/hex_v11/hex8_adequacy.parquet')
OUT_SZ   = Path('data/hex_v11/subzone_adequacy.parquet')
OUT_PA   = Path('data/hex_v11/pa_adequacy.parquet')
OUT_TOWN = Path('data/hex_v11/town_adequacy.parquet')

FACTORS = [
    'f_distance','f_last_mile','f_low_frequency','f_accessibility',
    'f_line_pressure','f_connectivity',
    'f_children_gap','f_low_income_gap',
    'f_dorm_gap','f_elderly_gap','f_fdw_gap',
    # v2 adequacy sub-factors — same aggregation pattern
    'frequency_adequacy_gap','reach_adequacy_gap','crowding_adequacy_gap','resilience_adequacy_gap',
    'availability_adequacy_gap',
]

POP_SUMS = [
    'pop_total','pop_resident','pop_resident_citizen','pop_resident_pr',
    'pop_non_resident','pop_nr_dorm','pop_nr_fdw','pop_nr_ep','pop_nr_sp','pop_nr_wp_other',
    'children_count','elderly_count','working_age_count','walking_dependent_count',
    'low_income_pop',
    'mrt_daily_taps','bus_daily_taps','transit_daily_taps',
    'mrt_stations','lrt_stations','bus_stops','dorm_count',
    'bldg_count','bldg_hdb_residential','bldg_private_residential',
    'residential_floor_area_sqm','total_floor_area_sqm',
    'area_km2',
]
# Distinct counts via max — for MRT lines and bus routes, child cells overlap so
# the cell with the highest count typically already includes the union (approx).
# A precise distinct count would require re-running step 7 at the new resolution.
DISTINCT_FIELDS = ['mrt_stations_in_500m','mrt_stations_in_1km','mrt_lines_count',
                   'lrt_stations_in_500m','lrt_stations_in_1km',
                   'bus_stops_in_400m','bus_stops_in_800m','bus_routes_count',
                   'transit_mode_count']
# Pop-weighted mean targets
WMEAN_FIELDS = [
    'dist_nearest_mrt_m','dist_to_nearest_lrt_m','dist_bus_m',
    'walk_mrt_score','pedestrian_crossings_count',
    'last_mile_friction','multimodal_score','land_use_entropy',
    'cbd_km','cbd_proximity_score','industrial_adjacency_score',
    'mrt_taps_per_capita','bus_taps_per_capita',
    'dist_school_m','dist_clinic_m','dist_hawker_m','dist_park_m','dist_super_m',
    # v2 adequacy raw signals
    'peak_wait_min','time_to_cbd_min','time_to_orchard_min','time_to_jurong_east_min',
    'time_to_tampines_hub_min','time_to_changi_business_min','time_to_one_north_min',
    'time_to_nus_min','time_to_ntu_min','time_to_sgh_min',
    'pct_dest_within_45min','pct_dest_within_60min',
    'crowding_load_factor','nearest_mrt_st_peak_taps',
    'n_lines_to_cbd',
    # 15-min city scores (composite + 4 buckets)
    'min15_score','min15_essentials','min15_school','min15_retail','min15_health',
    'min15_nearest_hawker_m','min15_nearest_super_m','min15_nearest_clinic_m',
    'min15_nearest_park_m','min15_nearest_school_m',
]

REASON_LABELS = {
    'walk_unfriendly': 'walk_unfriendly',
    'low_service_frequency': 'low_service_frequency',
    'far_from_transit': 'far_from_transit',
    'last_mile_friction': 'last_mile_friction',
    'overcrowded_lines': 'overcrowded_lines',
    'few_modes': 'few_modes',
    'children_school_gap': 'children_school_gap',
    'low_income_transit_gap': 'low_income_transit_gap',
    'dorm_worker_connectivity_gap': 'dorm_worker_connectivity_gap',
    'elderly_isolation': 'elderly_isolation',
    'fdw_off_day_gap': 'fdw_off_day_gap',
    'well_served': 'well_served',
}

def weighted_mean(s, w):
    s = pd.to_numeric(s, errors='coerce')
    w = pd.to_numeric(w, errors='coerce').fillna(0)
    mask = s.notna() & (w > 0)
    if not mask.any(): return np.nan
    return (s[mask] * w[mask]).sum() / w[mask].sum()

def band_of(v):
    if v is None or pd.isna(v): return None
    if v < 0.30: return 'excellent'
    if v < 0.50: return 'good'
    if v < 0.70: return 'moderate'
    if v < 0.85: return 'poor'
    return 'critical'

def aggregate(df, group_col, label_col=None):
    rows = []
    for key, g in df.groupby(group_col):
        if not key or str(key).strip() == '':
            continue
        # active = cells with meaningful pop or activity
        gact = g[g['cell_active_flag'] == 1] if 'cell_active_flag' in g.columns else g
        if len(gact) == 0:
            gact = g

        out = {group_col: key}
        if label_col and label_col in g.columns:
            out['label'] = g[label_col].iloc[0]
        # Identity passthroughs
        if 'parent_region' in g.columns:
            # most-common region
            out['parent_region'] = g['parent_region'].mode().iloc[0] if not g['parent_region'].mode().empty else None
        if group_col != 'parent_pa' and 'parent_pa' in g.columns:
            out['parent_pa'] = g['parent_pa'].mode().iloc[0] if not g['parent_pa'].mode().empty else None

        # Zone type — at aggregate level we use the BROAD type (industrial /
        # airport / nature / etc.) from the parent PA. But for is_scored we
        # look at whether the MAJORITY of population in this aggregate sits in
        # scored child hexes — so Tuas Bay (subzone) shows as scored because
        # most of its hex8 children are 'industrial_with_transit', even though
        # the broad PA-level type is 'industrial'.
        pa_for_zone = g['parent_pa'].mode().iloc[0] if 'parent_pa' in g.columns and not g['parent_pa'].mode().empty else None
        zt_broad = zone_type_of(pa_for_zone) if pa_for_zone else 'unknown'
        out['zone_type_broad'] = zt_broad

        # Aggregate-level is_scored: ≥ 50% of pop in scored child hexes
        if 'is_scored' in g.columns:
            pop_in_scored = g.loc[g['is_scored'] == True, 'pop_total'].fillna(0).sum() if 'pop_total' in g.columns else 0
            total_pop = g['pop_total'].fillna(0).sum() if 'pop_total' in g.columns else 0
            agg_is_scored = (total_pop > 0 and pop_in_scored / total_pop >= 0.5) or (zt_broad == 'residential')
            out['is_scored'] = bool(agg_is_scored)
            # Aggregate-level zone_type: pick the most common refined child type
            if 'zone_type' in g.columns:
                gact_z = g[g['zone_type'].notna()]
                if len(gact_z) > 0:
                    # Weight by population
                    weighted = gact_z.groupby('zone_type')['pop_total'].sum().fillna(0)
                    if weighted.sum() > 0:
                        out['zone_type'] = weighted.idxmax()
                    else:
                        out['zone_type'] = gact_z['zone_type'].mode().iloc[0] if not gact_z['zone_type'].mode().empty else zt_broad
                else:
                    out['zone_type'] = zt_broad
            else:
                out['zone_type'] = zt_broad
        else:
            out['zone_type'] = zt_broad
            out['is_scored'] = zt_broad in SCORED_ZONES

        out['cell_count']         = len(g)
        out['active_cell_count']  = int((g['cell_active_flag'] == 1).sum()) if 'cell_active_flag' in g.columns else len(g)

        # Sums
        for c in POP_SUMS:
            if c in g.columns:
                out[c] = float(g[c].fillna(0).sum())
        # Distinct counts (approximate via max across child cells — see header comment)
        for c in DISTINCT_FIELDS:
            if c in g.columns:
                out[c] = float(g[c].fillna(0).max())
        # Pop-weighted means
        w = g['pop_total'].fillna(0)
        for c in WMEAN_FIELDS:
            if c in g.columns:
                out[c] = float(weighted_mean(g[c], w)) if w.sum() > 0 else float('nan')

        # Factors
        pop_w = gact['pop_total'].fillna(0)
        for f in FACTORS:
            if f in gact.columns:
                wm = weighted_mean(gact[f], pop_w) if pop_w.sum() > 0 else gact[f].mean()
                out[f + '_mean'] = float(wm) if pd.notna(wm) else 0.0
                out[f + '_max'] = float(gact[f].max()) if len(gact) > 0 else 0.0
                out[f + '_min'] = float(gact[f].min()) if len(gact) > 0 else 0.0
        # Composite
        if 'gap_default' in gact.columns and pop_w.sum() > 0:
            out['gap_default']       = float(weighted_mean(gact['gap_default'], pop_w))
            out['gap_default_max']   = float(gact['gap_default'].max())
            out['gap_default_min']   = float(gact['gap_default'].min())
            out['equity_range']      = float(gact['gap_default'].max() - gact['gap_default'].min())
        if 'adequacy_default' in gact.columns and pop_w.sum() > 0:
            out['adequacy_default']     = float(weighted_mean(gact['adequacy_default'], pop_w))
            out['adequacy_default_max'] = float(gact['adequacy_default'].max())
            out['adequacy_default_min'] = float(gact['adequacy_default'].min())
        if 'adequacy_core' in gact.columns and pop_w.sum() > 0:
            out['adequacy_core']     = float(weighted_mean(gact['adequacy_core'], pop_w))
        # within_800m_mrt_pct: pop_total of cells where dist_nearest_mrt_m <= 800 / total pop_total
        if 'dist_nearest_mrt_m' in g.columns:
            tot_pop = g['pop_total'].fillna(0).sum()
            near = g[g['dist_nearest_mrt_m'].fillna(9999) <= 800]['pop_total'].fillna(0).sum() if tot_pop > 0 else 0
            out['within_800m_mrt_pct'] = float(100 * near / tot_pop) if tot_pop > 0 else 0.0
        # within_400m_bus_pct
        if 'dist_bus_m' in g.columns:
            tot_pop = g['pop_total'].fillna(0).sum()
            near = g[g['dist_bus_m'].fillna(9999) <= 400]['pop_total'].fillna(0).sum() if tot_pop > 0 else 0
            out['within_400m_bus_pct'] = float(100 * near / tot_pop) if tot_pop > 0 else 0.0
        # Dominant gap reason: take cell with most pop carrying the worst gap
        if 'primary_gap_reason' in gact.columns:
            gap_cells = gact[gact['gap_default'] >= 0.30]  # only cells that are not 'well_served'
            if len(gap_cells) > 0:
                # Weighted by pop_total
                gap_cells = gap_cells.copy()
                gap_cells['_weight'] = gap_cells['pop_total'].fillna(0) * gap_cells['gap_default']
                top_reason = gap_cells.groupby('primary_gap_reason')['_weight'].sum().idxmax()
                out['dominant_gap_reason'] = top_reason
            else:
                out['dominant_gap_reason'] = 'well_served'

        # Band distribution
        if 'gap_default' in gact.columns:
            bands = gact['gap_default'].apply(band_of).value_counts().to_dict()
            for b in ['excellent','good','moderate','poor','critical']:
                out[f'cells_band_{b}'] = int(bands.get(b, 0))
        # Pop in critical/poor bands
        if 'gap_default' in gact.columns:
            poor_pop = gact[gact['gap_default'] >= 0.70]['pop_total'].fillna(0).sum()
            out['pop_in_poor_or_critical'] = float(poor_pop)
            tot_pop = gact['pop_total'].fillna(0).sum()
            out['pct_pop_poor_or_critical'] = float(100 * poor_pop / tot_pop) if tot_pop > 0 else 0.0

        rows.append(out)
    return pd.DataFrame(rows)

def rank_table(df, by='gap_default', ascending=True):
    """Add national_rank by gap_default (1 = best)."""
    df = df.copy()
    df['national_rank'] = df[by].rank(ascending=ascending, method='min').astype('Int64')
    df['total_in_level'] = len(df)
    return df

def main():
    h = pd.read_parquet(INP)
    print(f'Loaded hex8 adequacy: {h.shape}')
    print(f'Total pop: {h["pop_total"].sum():,.0f}')

    # === Subzone ===
    print('\n=== Aggregating to Subzone ===')
    sz = aggregate(h, 'parent_subzone')
    sz = sz[sz['pop_total'] > 0].reset_index(drop=True)  # drop empty SZ
    sz = rank_table(sz)
    sz.to_parquet(OUT_SZ, index=False)
    print(f'  {len(sz)} active subzones | total pop: {sz["pop_total"].sum():,.0f}')
    print(f'  cols: {len(sz.columns)}  |  wrote {OUT_SZ}')

    # === Planning Area ===
    print('\n=== Aggregating to Planning Area ===')
    pa = aggregate(h, 'parent_pa')
    pa = pa[pa['pop_total'] > 0].reset_index(drop=True)
    pa = rank_table(pa)
    pa.to_parquet(OUT_PA, index=False)
    print(f'  {len(pa)} PAs | total pop: {pa["pop_total"].sum():,.0f}')
    print(f'  cols: {len(pa.columns)}  |  wrote {OUT_PA}')

    # === HDB Town ===
    print('\n=== Aggregating to HDB Town ===')
    # Tag each hex8 with town info (only if classification is town/estate)
    h2 = h.copy()
    classifications = h2['parent_pa'].apply(lambda p: classify_pa(p) if p else (False, None, 'unknown'))
    h2['town_label'] = classifications.apply(lambda c: c[1])
    h2['town_category'] = classifications.apply(lambda c: c[2])
    h_towns_only = h2[h2['town_category'] == 'town'].copy()
    print(f'  hex8 cells in HDB towns: {len(h_towns_only)} / {len(h2)}')
    town = aggregate(h_towns_only, 'parent_pa', label_col='town_label')
    town = town[town['pop_total'] > 0].reset_index(drop=True)
    # Move town_label to be primary identifier
    if 'label' in town.columns:
        town['town_label'] = town['label']
        town = town.drop(columns=['label'])
    town = rank_table(town)
    town.to_parquet(OUT_TOWN, index=False)
    print(f'  {len(town)} HDB towns | total pop: {town["pop_total"].sum():,.0f}')
    print(f'  cols: {len(town.columns)}  |  wrote {OUT_TOWN}')

    # === Quick rankings ===
    print('\n--- Top-5 subzones (best gap_default) ---')
    print(sz.nsmallest(5, 'gap_default')[['parent_subzone','parent_pa','pop_total','gap_default','national_rank']].to_string(index=False))
    print('\n--- Bottom-5 subzones (worst gap_default) ---')
    print(sz.nlargest(5, 'gap_default')[['parent_subzone','parent_pa','pop_total','gap_default','national_rank']].to_string(index=False))
    print('\n--- Top-5 HDB Towns (best gap_default) ---')
    print(town.nsmallest(5, 'gap_default')[['town_label','pop_total','gap_default','national_rank','within_800m_mrt_pct']].to_string(index=False))
    print('\n--- Bottom-5 HDB Towns (worst gap_default) ---')
    print(town.nlargest(5, 'gap_default')[['town_label','pop_total','gap_default','national_rank','within_800m_mrt_pct']].to_string(index=False))

if __name__ == '__main__':
    main()
