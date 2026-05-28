"""Combine all buckets into final hex8 total-population table; validate to 6.11M.

Inputs:
  data/hex_v10/hex8_final.parquet            (resident pop, 4,212,320 — already aggregated to hex8)
  data/hex_v11/hex8_dorm_pop.parquet         (CMP dorm pop, 482,600)
  data/hex_v11/hex8_fdw_pop.parquet          (MDW/FDW pop, 316,900)
  data/hex_v11/hex8_other_nr_pop.parquet     (EP+SP+other-WP+dep+students, 1,110,500)

Output:
  data/hex_v11/hex8_population.parquet
"""

import pandas as pd
import numpy as np
from pathlib import Path

OUT = Path('data/hex_v11/hex8_population.parquet')

# DOS June 2025 targets
TARGET_TOTAL    = 6_110_000
TARGET_CITIZEN  = 3_660_000
TARGET_PR       = 540_000
TARGET_RESIDENT = TARGET_CITIZEN + TARGET_PR  # 4,200,000
TARGET_NR       = 1_910_000

def main():
    h = pd.read_parquet('data/hex_v10/hex8_final.parquet')[
        ['hex8_id','lat','lng','area_km2','parent_subzone','parent_pa','parent_region',
         'population','children_count','elderly_count','working_age_count',
         'residential_floor_area_sqm','total_floor_area_sqm']
    ].copy()
    h = h.rename(columns={'population':'pop_resident'})

    # Citizen / PR split per subzone — use national ratio uniformly (census doesn't distinguish)
    cit_share = TARGET_CITIZEN / TARGET_RESIDENT  # 0.8714
    pr_share  = TARGET_PR / TARGET_RESIDENT       # 0.1286
    # Scale resident pop to exactly 4.20M (compensate for any tiny census/dasymetric drift)
    cur_res = h['pop_resident'].sum()
    res_scale = TARGET_RESIDENT / cur_res
    print(f'Resident scale: {res_scale:.6f}  ({cur_res:,.0f} → {TARGET_RESIDENT:,})')
    h['pop_resident'] = h['pop_resident'] * res_scale
    h['pop_resident_citizen'] = h['pop_resident'] * cit_share
    h['pop_resident_pr']      = h['pop_resident'] * pr_share

    # Merge buckets
    dorm = pd.read_parquet('data/hex_v11/hex8_dorm_pop.parquet')[['hex8_id','dorm_count','raw_capacity','pop_nr_dorm']]
    fdw  = pd.read_parquet('data/hex_v11/hex8_fdw_pop.parquet')[['hex8_id','pop_nr_fdw']]
    other= pd.read_parquet('data/hex_v11/hex8_other_nr_pop.parquet')[
        ['hex8_id','pop_nr_ep','pop_nr_sp','pop_nr_wp_other']
    ]
    h = h.merge(dorm, on='hex8_id', how='left').merge(fdw, on='hex8_id', how='left').merge(other, on='hex8_id', how='left')
    for c in ['dorm_count','pop_nr_dorm','pop_nr_fdw','pop_nr_ep','pop_nr_sp','pop_nr_wp_other']:
        h[c] = h[c].fillna(0)

    # Combined columns
    h['pop_non_resident'] = h['pop_nr_dorm'] + h['pop_nr_fdw'] + h['pop_nr_ep'] + h['pop_nr_sp'] + h['pop_nr_wp_other']
    h['pop_total'] = h['pop_resident'] + h['pop_non_resident']

    # Density
    h['pop_density_per_km2'] = h['pop_total'] / h['area_km2'].replace(0, np.nan)

    # Validate against DOS June 2025 targets
    print('\n=== VALIDATION ===')
    print(f'pop_resident       sum: {h["pop_resident"].sum():>14,.0f}  target: {TARGET_RESIDENT:>14,}')
    print(f'  pop_citizen      sum: {h["pop_resident_citizen"].sum():>14,.0f}  target: {TARGET_CITIZEN:>14,}')
    print(f'  pop_pr           sum: {h["pop_resident_pr"].sum():>14,.0f}  target: {TARGET_PR:>14,}')
    print(f'pop_non_resident   sum: {h["pop_non_resident"].sum():>14,.0f}  target: {TARGET_NR:>14,}')
    print(f'  pop_nr_dorm           {h["pop_nr_dorm"].sum():>14,.0f}             482,600')
    print(f'  pop_nr_fdw            {h["pop_nr_fdw"].sum():>14,.0f}             316,900')
    print(f'  pop_nr_ep             {h["pop_nr_ep"].sum():>14,.0f}             453,000')
    print(f'  pop_nr_sp             {h["pop_nr_sp"].sum():>14,.0f}             204,000')
    print(f'  pop_nr_wp_other       {h["pop_nr_wp_other"].sum():>14,.0f}             453,500')
    print(f'pop_TOTAL          sum: {h["pop_total"].sum():>14,.0f}  target: {TARGET_TOTAL:>14,}')

    drift = abs(h["pop_total"].sum() - TARGET_TOTAL) / TARGET_TOTAL * 100
    print(f'\nTotal drift from 6.11M: {drift:.3f}%')

    # Attribution method label
    def label(row):
        if row['pop_total'] == 0: return 'empty'
        nr_share = row['pop_non_resident'] / row['pop_total']
        if nr_share > 0.6: return 'nr_dominant'
        if nr_share > 0.25: return 'mixed'
        return 'resident_majority'
    h['attrib_label'] = h.apply(label, axis=1)
    print(f'\nAttribution label counts:')
    print(h['attrib_label'].value_counts().to_string())

    # Trust score: 1.0 - residual_uncertainty
    # high trust where: dorm match has Overture footprint OR resident pop > 100
    # lower trust where: dorm pop is from defaults + ungeocoded redistribution
    h['attrib_confidence'] = 'high'  # default
    # Cells whose ENTIRE pop is small + no anchors → lower
    h.loc[(h['pop_resident'] < 50) & (h['dorm_count'] == 0) & (h['pop_total'] > 100), 'attrib_confidence'] = 'low'
    h.loc[(h['pop_resident'] < 50) & (h['dorm_count'] == 0) & (h['pop_total'] <= 100), 'attrib_confidence'] = 'sparse'

    print('\nConfidence label counts:')
    print(h['attrib_confidence'].value_counts().to_string())

    # Top 20 total-pop cells (sanity)
    print('\nTop 20 total-pop cells:')
    print(h.nlargest(20, 'pop_total')[['hex8_id','parent_subzone','parent_pa',
        'pop_resident','pop_nr_dorm','pop_nr_fdw','pop_nr_ep','pop_nr_sp','pop_nr_wp_other','pop_total'
    ]].to_string(index=False))

    # Bottom: cells with non-zero pop
    print('\nBottom 10 pop>0 cells:')
    nonzero = h[h['pop_total'] > 0].nsmallest(10, 'pop_total')
    print(nonzero[['hex8_id','parent_subzone','pop_total','attrib_confidence']].to_string(index=False))

    # Sanity check: Tuas industrial transformation
    print('\n=== Tuas industrial cell check ===')
    tuas = h[h['parent_pa'] == 'Tuas']
    print(f'Tuas hex8 cells: {len(tuas)}')
    print(f'  resident pop sum: {tuas["pop_resident"].sum():,.0f}')
    print(f'  total pop sum:    {tuas["pop_total"].sum():,.0f}')
    print(f'  dorm pop:         {tuas["pop_nr_dorm"].sum():,.0f}')
    print(f'  resident:total ratio: {tuas["pop_resident"].sum()/tuas["pop_total"].sum()*100:.1f}%')

    # Save
    h.to_parquet(OUT, index=False)
    print(f'\nWrote {OUT}')
    print(f'Schema: {len(h.columns)} cols, {len(h)} rows')

if __name__ == '__main__':
    main()
