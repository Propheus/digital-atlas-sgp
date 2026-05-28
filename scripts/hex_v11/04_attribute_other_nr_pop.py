"""Distribute the other-non-resident bucket across hex8 cells.

Total budget = 1,910,000 (total NR) - 482,600 (dorm CMP) - 316,900 (FDW) = 1,110,500

Three-way split (per advisor reasoning):
  EP + dependants/students        ≈ 453,000  → premium private rental near MRT, CBD-weighted
  S Pass + some dependants        ≈ 204,000  → mixed private + HDB near MRT, OCR-balanced
  Services WP + other work passes ≈ 453,500  → industrial-fringe HDB rental / employer housing

Weighting signals (from hex8_final 628 cols):
  bldg_private_residential, bldg_hdb_residential, bldg_industrial
  walk_mrt_score, dist_mrt_m
  Raffles Place distance for CBD proximity
"""

import pandas as pd
import numpy as np
import h3
from pathlib import Path

OUT = Path('data/hex_v11/hex8_other_nr_pop.parquet')

EP_DEP_BUDGET = 453_000
SP_BUDGET = 204_000
WP_OTHER_BUDGET = 453_500
TOTAL_BUDGET = EP_DEP_BUDGET + SP_BUDGET + WP_OTHER_BUDGET

# CBD anchor: Raffles Place
CBD_LAT, CBD_LNG = 1.2843, 103.8511

def cbd_distance_km(row):
    """Approximate planar distance to Raffles Place in km."""
    dlat = (row['lat'] - CBD_LAT) * 110.540
    dlng = (row['lng'] - CBD_LNG) * 111.320 * np.cos(np.radians(CBD_LAT))
    return np.sqrt(dlat*dlat + dlng*dlng)

def main():
    h = pd.read_parquet('data/hex_v10/hex8_final.parquet').copy()
    print(f'Loaded {len(h)} hex8 cells')

    # CBD proximity: 1 at Raffles, decays with distance
    h['cbd_km'] = h.apply(cbd_distance_km, axis=1)
    h['cbd_score'] = 1.0 / (1.0 + h['cbd_km'] / 3.0)  # half-decay at 3 km

    # MRT proximity score: prefer walk_mrt_score if present, else derive from dist_mrt_m
    # walk_mrt_score ranges (let's check):
    if 'walk_mrt_score' in h.columns:
        mrt_score = h['walk_mrt_score'].fillna(0).clip(0, 1)
    else:
        mrt_score = (1.0 / (1.0 + (h['dist_mrt_m'].fillna(5000) / 800.0))).clip(0, 1)
    h['mrt_score'] = mrt_score

    # Private + HDB residential signals
    priv = h['bldg_private_residential'].fillna(0)
    hdb = h['bldg_hdb_residential'].fillna(0)
    indus = h['bldg_industrial'].fillna(0)

    # Industrial adjacency: distance to any industrial cell weighted by surrounding industrial intensity
    # Use 'sp_max_lu_business_pct' as a proxy for being near commercial/industrial activity
    indus_adj = h.get('sp_max_lu_business_pct', pd.Series(0, index=h.index)).fillna(0).clip(0, 1)

    # === Bucket 1: EP + dependants (453K) ===
    # Premium private rental near MRT, CBD-heavy
    w_ep = priv * h['mrt_score'].pow(1.2) * h['cbd_score'].pow(0.8)
    # Avoid 0 cells getting no allocation in mixed-use districts
    w_ep = w_ep + priv * 0.05  # small floor
    if w_ep.sum() <= 0: w_ep = priv.copy() + 0.1
    h['pop_nr_ep'] = (w_ep / w_ep.sum()) * EP_DEP_BUDGET

    # === Bucket 2: S Pass (204K) ===
    # Mixed private + HDB near MRT (50% private weight, 50% HDB weight)
    w_sp = (priv * 0.6 + hdb * 0.4) * h['mrt_score'].pow(1.0) * (0.4 + h['cbd_score'].pow(0.3) * 0.6)
    w_sp = w_sp + (priv + hdb) * 0.02
    if w_sp.sum() <= 0: w_sp = (priv + hdb).copy() + 0.1
    h['pop_nr_sp'] = (w_sp / w_sp.sum()) * SP_BUDGET

    # === Bucket 3: Services WP + other (453K) ===
    # HDB rental in industrial-fringe areas
    # Weight = HDB count × industrial-adjacency, with mild MRT factor (workers do commute)
    w_wp = hdb * (0.3 + indus_adj.pow(0.7) * 0.7) * (0.6 + h['mrt_score'].pow(0.5) * 0.4)
    # Add a separate small term for cells with high industrial density (employer-arranged housing
    # could be in commercial subletting)
    w_wp = w_wp + indus * h['mrt_score'].pow(0.3) * 0.3
    w_wp = w_wp + hdb * 0.03
    if w_wp.sum() <= 0: w_wp = hdb.copy() + 0.1
    h['pop_nr_wp_other'] = (w_wp / w_wp.sum()) * WP_OTHER_BUDGET

    # Total
    h['pop_nr_other'] = h['pop_nr_ep'] + h['pop_nr_sp'] + h['pop_nr_wp_other']

    print(f'\nEP+dep total:        {h["pop_nr_ep"].sum():,.0f}  (target {EP_DEP_BUDGET:,})')
    print(f'S Pass total:        {h["pop_nr_sp"].sum():,.0f}  (target {SP_BUDGET:,})')
    print(f'Services WP+other:   {h["pop_nr_wp_other"].sum():,.0f}  (target {WP_OTHER_BUDGET:,})')
    print(f'GRAND TOTAL:         {h["pop_nr_other"].sum():,.0f}  (target {TOTAL_BUDGET:,})')

    out = h[['hex8_id','parent_subzone','parent_pa','parent_region',
             'pop_nr_ep','pop_nr_sp','pop_nr_wp_other','pop_nr_other']].copy()
    out.to_parquet(OUT, index=False)
    print(f'\nWrote {OUT}')

    print('\nTop 15 EP+dependants cells:')
    print(out.nlargest(15, 'pop_nr_ep')[['parent_subzone','parent_pa','pop_nr_ep']].to_string(index=False))
    print('\nTop 15 Services-WP+other cells:')
    print(out.nlargest(15, 'pop_nr_wp_other')[['parent_subzone','parent_pa','pop_nr_wp_other']].to_string(index=False))

if __name__ == '__main__':
    main()
