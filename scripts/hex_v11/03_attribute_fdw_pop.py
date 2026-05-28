"""Distribute 316,900 Migrant Domestic Workers (MDW/FDW) across hex8 cells.

MDWs live inside employer households. Employment rate varies sharply by dwelling type:
landed/condo are FDW-heavy; small HDBs almost none.

Method:
  Step 1: Per (subzone, TOD), estimate FDW count = Pop / avg_HH_size_TOD × FDW_rate_TOD.
  Step 2: Aggregate to subzone total FDW.
  Step 3: Top-down scale subzone totals to 316,900.
  Step 4: Within each subzone, distribute to hex8 cells by residential_floor_area_sqm
          (since FDWs live in residential floor area, not commercial/industrial).

Inputs:
  data/demographics/pop_age_sex_tod_2025.csv
  data/hex_v10/hex8_final.parquet
"""

import pandas as pd
from pathlib import Path

OUT = Path('data/hex_v11/hex8_fdw_pop.parquet')
FDW_BUDGET = 316_900  # MOM Dec 2025

# Per-TOD parameters: (avg_household_size, fdw_per_household)
# avg HH sizes from SingStat; FDW rates calibrated to sum near 316.9K nationally
TOD_PARAMS = {
    'HDB 1- and 2-Room Flats':                     (2.0, 0.01),
    'HDB 3-Room Flats':                            (2.7, 0.03),
    'HDB 4-Room Flats':                            (3.1, 0.07),
    'HDB 5-Room and Executive Flats':              (3.4, 0.15),
    'HUDC Flats (excluding those privatised)':     (3.0, 0.10),
    'Condominiums and Other Apartments':           (2.7, 0.32),
    'Landed Properties':                           (3.4, 0.65),
    'Others':                                      (2.5, 0.10),
}

def main():
    pop = pd.read_csv('data/demographics/pop_age_sex_tod_2025.csv')
    # Aggregate population per (PA, SZ, TOD)
    sz_tod = pop.groupby(['PA','SZ','TOD'])['Pop'].sum().reset_index()

    sz_tod['hh_size'] = sz_tod['TOD'].map(lambda t: TOD_PARAMS[t][0])
    sz_tod['fdw_rate'] = sz_tod['TOD'].map(lambda t: TOD_PARAMS[t][1])
    sz_tod['households'] = sz_tod['Pop'] / sz_tod['hh_size']
    sz_tod['fdw_raw'] = sz_tod['households'] * sz_tod['fdw_rate']

    sz_total = sz_tod.groupby(['PA','SZ'])['fdw_raw'].sum().reset_index()
    print(f'Raw FDW total before scaling: {sz_total["fdw_raw"].sum():,.0f}')
    scale = FDW_BUDGET / sz_total['fdw_raw'].sum()
    sz_total['fdw_subzone'] = sz_total['fdw_raw'] * scale
    print(f'Scale factor: {scale:.4f}; after scaling: {sz_total["fdw_subzone"].sum():,.0f}')

    # Top subzones
    print('\nTop 15 FDW subzones (after scaling):')
    print(sz_total.nlargest(15, 'fdw_subzone')[['PA','SZ','fdw_subzone']].to_string(index=False))

    # Load hex8 to distribute within subzone by residential floor area
    hex8 = pd.read_parquet('data/hex_v10/hex8_final.parquet')[
        ['hex8_id','parent_subzone','parent_pa','parent_region','residential_floor_area_sqm','population']
    ].copy()

    # Subzone names in census = parent_subzone here? Let's check overlap
    sz_total['SZ_norm'] = sz_total['SZ'].str.strip().str.upper()
    hex8['SZ_norm'] = hex8['parent_subzone'].astype(str).str.strip().str.upper()

    # Compute weights per subzone
    sz_weight_sum = hex8.groupby('SZ_norm')['residential_floor_area_sqm'].sum()
    hex8 = hex8.merge(sz_weight_sum.rename('sz_floor_total'), on='SZ_norm', how='left')
    hex8['floor_share'] = hex8['residential_floor_area_sqm'] / hex8['sz_floor_total'].replace(0, pd.NA)
    # Where no floor area (rural cells), fallback to population share within subzone
    sz_pop_sum = hex8.groupby('SZ_norm')['population'].sum()
    hex8 = hex8.merge(sz_pop_sum.rename('sz_pop_total'), on='SZ_norm', how='left')
    hex8['pop_share'] = hex8['population'] / hex8['sz_pop_total'].replace(0, pd.NA)
    hex8['share'] = hex8['floor_share'].fillna(hex8['pop_share']).fillna(0)

    # Subzone FDW lookup
    sz_lookup = dict(zip(sz_total['SZ_norm'], sz_total['fdw_subzone']))
    hex8['sz_fdw'] = hex8['SZ_norm'].map(sz_lookup).fillna(0)
    hex8['pop_nr_fdw'] = hex8['sz_fdw'] * hex8['share']

    print(f'\nMatched subzones: {hex8["sz_fdw"].gt(0).any() and (hex8["SZ_norm"].isin(sz_lookup).sum())} hex8 rows')
    matched_sz = set(sz_lookup) & set(hex8['SZ_norm'].unique())
    missing_sz = set(sz_lookup) - matched_sz
    print(f'Subzones matched (hex8 ↔ census): {len(matched_sz)} | census-only: {len(missing_sz)}')
    if missing_sz:
        # Subzones in census but not in hex8 — typically water/special bodies; their FDW pop should redistribute
        miss_fdw = sum(sz_lookup[s] for s in missing_sz)
        print(f'  Census subzones with no hex8 match account for: {miss_fdw:,.0f} FDW (will be reallocated proportionally)')
        # Rescale survivors so total still = budget
        cur_sum = hex8['pop_nr_fdw'].sum()
        if cur_sum > 0:
            hex8['pop_nr_fdw'] *= FDW_BUDGET / cur_sum

    print(f'\nFinal FDW pop sum on hex8: {hex8["pop_nr_fdw"].sum():,.0f}  (target {FDW_BUDGET:,})')
    print(f'Cells with any FDW pop: {(hex8["pop_nr_fdw"] > 0).sum()} / {len(hex8)}')

    out = hex8[['hex8_id','parent_subzone','parent_pa','parent_region','pop_nr_fdw']].copy()
    out.to_parquet(OUT, index=False)
    print(f'Wrote {OUT}')

    # Sanity
    print('\nTop 15 FDW hex8 cells:')
    print(out.nlargest(15, 'pop_nr_fdw').to_string(index=False))

if __name__ == '__main__':
    main()
