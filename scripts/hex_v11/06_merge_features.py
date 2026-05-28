"""Step 1: Merge hex_v10 feature stack + hex_v11 population overlay.

Output: data/hex_v11/hex8_adequacy_features.parquet
"""

import pandas as pd
from pathlib import Path

OUT = Path('data/hex_v11/hex8_adequacy_features.parquet')

def main():
    base = pd.read_parquet('data/hex_v10/hex8_final.parquet')
    print(f'hex_v10 base: {base.shape}')

    pop = pd.read_parquet('data/hex_v11/hex8_population.parquet')
    print(f'hex_v11 pop overlay: {pop.shape}')

    # Drop overlapping columns from pop (we keep hex_v10's identity + counts)
    drop_overlap = [c for c in pop.columns if c in base.columns and c not in (
        'hex8_id','parent_subzone','parent_pa','parent_region','area_km2','lat','lng')]
    pop_clean = pop.drop(columns=drop_overlap, errors='ignore')

    merged = base.merge(pop_clean, on=['hex8_id'], how='left',
                        suffixes=('', '_v11'))
    print(f'merged: {merged.shape}')

    # Fill NR cols with 0 for missing
    nr_cols = [c for c in merged.columns if c.startswith('pop_nr_') or c in ('pop_non_resident','pop_total')]
    for c in nr_cols:
        merged[c] = merged[c].fillna(0)

    # Standardize a 'population_resident' alias for backward compat
    if 'pop_resident' in merged.columns:
        merged['population_resident'] = merged['pop_resident']

    merged.to_parquet(OUT, index=False)
    print(f'\nWrote {OUT}')
    print(f'cols: {len(merged.columns)} | rows: {len(merged)}')
    print(f'pop_total sum: {merged["pop_total"].sum():,.0f}')

if __name__ == '__main__':
    main()
