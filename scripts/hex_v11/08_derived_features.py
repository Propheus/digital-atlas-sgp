"""Step 3: Derived features — per-capita ratios, composites, equity helpers.

Adds:
  pop_density_per_km2 (refresh)
  walking_dependent_count
  low_income_pop                  — pop_resident × hdb_low_income_share
  mrt_taps_per_capita, bus_taps_per_capita, total_taps_per_capita
  land_use_entropy                — Shannon over lu_*_pct
  multimodal_score                — 0..1 from transit_mode_count + mrt_lines + bus_routes
  last_mile_friction              — composite of dist_to_stop + lack-of-crossings
  cbd_proximity_km                — straight-line km to Raffles
  industrial_adjacency_score      — sp_max_lu_business_pct (already exists; rename for clarity)
  cell_active_flag                — 1 if pop_total >= 50 OR commercial activity
"""

import pandas as pd
import numpy as np
from pathlib import Path

IN_PATH = Path('data/hex_v11/hex8_adequacy_features.parquet')

CBD_LAT, CBD_LNG = 1.2843, 103.8511

def cbd_km(row):
    dlat = (row['lat'] - CBD_LAT) * 110.540
    dlng = (row['lng'] - CBD_LNG) * 111.320 * np.cos(np.radians(CBD_LAT))
    return np.sqrt(dlat*dlat + dlng*dlng)

def shannon(p):
    """Shannon entropy of a probability vector (already non-negative). Normalised to [0,1]."""
    p = np.asarray(p, dtype=float)
    p = p / max(p.sum(), 1e-9)
    p = p[p > 0]
    if len(p) == 0: return 0.0
    H = -np.sum(p * np.log(p))
    return H / np.log(len(p)) if len(p) > 1 else 0.0

def main():
    h = pd.read_parquet(IN_PATH)
    print(f'Loaded {h.shape}')

    # Density (refresh in case area_km2 was updated)
    h['pop_density_per_km2'] = h['pop_total'] / h['area_km2'].replace(0, np.nan)

    # Vulnerable groups
    h['walking_dependent_count'] = (h['children_count'].fillna(0) + h['elderly_count'].fillna(0))

    # Low-income proxy: hdb_pop_share is fraction of resident pop in HDB.
    # Within HDB, smaller flats correlate with lower income.
    # Use hdb_pop_share × pop_resident × 0.5 as a coarse "low-income" estimate
    # (HDB 1-3R pop is roughly 35% of HDB pop nationally)
    if 'hdb_pop_share' in h.columns:
        h['low_income_pop'] = h['pop_resident'] * h['hdb_pop_share'].fillna(0) * 0.35
    else:
        h['low_income_pop'] = 0.0

    # Per-capita transit usage
    for src, dst in [('mrt_daily_taps','mrt_taps_per_capita'),
                     ('bus_daily_taps','bus_taps_per_capita'),
                     ('transit_daily_taps','total_taps_per_capita')]:
        if src in h.columns:
            h[dst] = h[src].fillna(0) / h['pop_total'].replace(0, np.nan)
            h[dst] = h[dst].fillna(0)

    # Land use entropy across the canonical 5 categories
    lu_cols = [c for c in ['lu_residential_pct','lu_commercial_pct','lu_business_pct',
                            'lu_mixed_use_pct','lu_institutional_pct'] if c in h.columns]
    if lu_cols:
        h['land_use_entropy'] = h[lu_cols].fillna(0).apply(shannon, axis=1)
    else:
        h['land_use_entropy'] = 0.0

    # Multimodal score: combines mode count (0..3) + log of routes/lines reachable
    # max realistic: 3 modes + 8 lines + 100 routes
    mode_part = (h.get('transit_mode_count', pd.Series(0, index=h.index)).fillna(0) / 3.0).clip(0,1)
    lines_part = (np.log1p(h.get('mrt_lines_count', pd.Series(0, index=h.index)).fillna(0)) / np.log(9)).clip(0,1)
    routes_part = (np.log1p(h.get('bus_routes_count', pd.Series(0, index=h.index)).fillna(0)) / np.log(101)).clip(0,1)
    h['multimodal_score'] = (mode_part * 0.45 + lines_part * 0.30 + routes_part * 0.25).clip(0,1)

    # Last-mile friction: high when MRT is far AND walkability is poor AND few crossings
    dist_mrt = h.get('dist_nearest_mrt_m', h.get('dist_mrt_m', pd.Series(np.nan, index=h.index))).fillna(5000)
    walk_score = h.get('walk_mrt_score', pd.Series(0, index=h.index)).fillna(0).clip(0,1)
    cross_n = h.get('pedestrian_crossings_count', h.get('ped_crossings', pd.Series(0, index=h.index))).fillna(0)
    friction = (1 - walk_score) * 0.5 + (dist_mrt / 1500.0).clip(0, 1) * 0.4 + (1 - (cross_n / 10.0).clip(0,1)) * 0.1
    h['last_mile_friction'] = friction.clip(0, 1)

    # CBD proximity
    h['cbd_km'] = h.apply(cbd_km, axis=1)
    h['cbd_proximity_score'] = 1.0 / (1.0 + h['cbd_km'] / 3.0)

    # Industrial adjacency (rename existing for clarity)
    if 'sp_max_lu_business_pct' in h.columns:
        h['industrial_adjacency_score'] = h['sp_max_lu_business_pct'].fillna(0).clip(0,1)
    else:
        h['industrial_adjacency_score'] = 0.0

    # Active cell flag: pop ≥ 50 OR has commercial activity OR has dorms
    h['cell_active_flag'] = (
        (h['pop_total'] >= 50) |
        (h.get('bldg_commercial', 0).fillna(0) > 0) |
        (h.get('pop_nr_dorm', 0).fillna(0) > 50)
    ).astype(int)

    h.to_parquet(IN_PATH, index=False)
    print(f'\nWrote {IN_PATH}  ({h.shape[1]} cols)')

    # Summary
    print(f'\nActive cells: {h["cell_active_flag"].sum()} / {len(h)}')
    print(f'Mean multimodal_score: {h["multimodal_score"].mean():.3f}')
    print(f'Mean last_mile_friction: {h["last_mile_friction"].mean():.3f}')
    print(f'Mean land_use_entropy: {h["land_use_entropy"].mean():.3f}')

if __name__ == '__main__':
    main()
