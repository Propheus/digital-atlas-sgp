"""Step 4: Compute 11 adequacy factors. Each factor in [0,1] where 0=excellent, 1=critical gap.

Factors:
  f_accessibility   — walkability + crossings + sheltered (last 2 partial)
  f_distance        — far from MRT/bus
  f_last_mile       — already computed last_mile_friction
  f_connectivity    — inverse of multimodal_score
  f_line_pressure   — taps_per_capita above capacity
  f_low_frequency   — bus_routes_count vs population
  f_children_gap    — children × dist_to_school
  f_low_income_gap  — low_income_pop × dist_to_MRT
  f_dorm_gap        — pop_nr_dorm × (dist_to_bus_min + dist_to_industrial)
  f_elderly_gap     — elderly × dist_to_MRT × inverse(silver_zone_coverage)
  f_fdw_gap         — pop_nr_fdw × dist_to_park × dist_to_cbd (remittance hubs)
"""

import pandas as pd
import numpy as np
from pathlib import Path

IN_PATH = Path('data/hex_v11/hex8_adequacy_features.parquet')

def norm01(s, clip_lo=0, clip_hi=None):
    """Normalize series to [0,1]. clip_hi = saturation point (above = 1)."""
    s = pd.to_numeric(s, errors='coerce').fillna(0)
    if clip_hi is None:
        clip_hi = s.quantile(0.95) or 1
    out = ((s - clip_lo) / max(clip_hi - clip_lo, 1e-9)).clip(0, 1)
    return out

def safe_get(h, col, default=0):
    return h[col].fillna(default) if col in h.columns else pd.Series(default, index=h.index)

def main():
    h = pd.read_parquet(IN_PATH)
    print(f'Loaded {h.shape}')

    pop = h['pop_total'].clip(lower=1)

    # === Factor 1: f_accessibility (FIXED v2) ===
    # Multi-modal walkability. The old version relied on walk_mrt_score alone,
    # which was 0 for ~640 cells without MRT and pushed nearly every cell into
    # the "Critical" band. The new version averages walkability to 6 destinations
    # — bus, MRT, clinic, supermarket, hawker, park — so cells without MRT still
    # score on amenity walkability. Crossings remain a secondary signal.
    d_bus    = safe_get(h, 'dist_bus_m',           1000)
    d_mrt    = safe_get(h, 'dist_nearest_mrt_m',   5000)
    if 'dist_mrt_m' in h.columns:
        d_mrt = pd.concat([d_mrt, safe_get(h, 'dist_mrt_m', 5000)], axis=1).min(axis=1)
    d_clinic = safe_get(h, 'dist_clinic_m',        1500)
    d_super  = safe_get(h, 'dist_super_m',         1500)
    d_hawker = safe_get(h, 'dist_hawker_m',        1500)
    d_park   = safe_get(h, 'dist_park_m',          1500)
    # Per-destination walkability (1 = walkable, 0 = too far)
    walk_components = pd.DataFrame({
        'bus':    1 - (d_bus    / 600.0).clip(0, 1),     # bus desirable within 600m
        'mrt':    1 - (d_mrt    / 1500.0).clip(0, 1),    # MRT acceptable within 1.5km
        'clinic': 1 - (d_clinic / 1000.0).clip(0, 1),
        'super':  1 - (d_super  / 1000.0).clip(0, 1),
        'hawker': 1 - (d_hawker / 1000.0).clip(0, 1),
        'park':   1 - (d_park   / 800.0).clip(0, 1),
    })
    walk_aggregate = walk_components.mean(axis=1)
    crossings  = safe_get(h, 'pedestrian_crossings_count')
    cross_norm = (crossings / 8.0).clip(0, 1)
    h['f_accessibility'] = ((1 - walk_aggregate) * 0.75 + (1 - cross_norm) * 0.25).clip(0, 1)

    # === Factor 2: f_distance ===
    # Max distance to transit
    d_mrt = safe_get(h, 'dist_nearest_mrt_m', 5000)
    if 'dist_mrt_m' in h.columns:
        d_mrt = pd.concat([d_mrt, safe_get(h, 'dist_mrt_m', 5000)], axis=1).min(axis=1)
    d_bus = safe_get(h, 'dist_bus_m', 1000)
    # Worse of MRT or bus distance (but bus tolerable up to 400m, MRT up to 800m)
    f_mrt = (d_mrt / 1500.0).clip(0, 1)  # 1500m = critical
    f_bus = (d_bus / 600.0).clip(0, 1)
    h['f_distance'] = (f_mrt * 0.6 + f_bus * 0.4).clip(0, 1)

    # === Factor 3: f_last_mile ===
    h['f_last_mile'] = safe_get(h, 'last_mile_friction').clip(0, 1)

    # === Factor 4: f_connectivity ===
    h['f_connectivity'] = (1 - safe_get(h, 'multimodal_score').clip(0,1)).clip(0,1)

    # === Factor 5: f_line_pressure (FIXED v2) ===
    # Real station load: daily taps per station, not per cell-resident.
    # The old version compared MRT taps against the SINGLE-CELL population
    # — which was wrong because each station serves a ~1km catchment, NOT
    # just the cell it sits in. So busy hub stations were marked as
    # "critically overcrowded" while empty stations sat at "Excellent".
    # New formula only fires when MRT actually present in the cell.
    n_st = safe_get(h, 'mrt_stations', 0)
    mrt_taps = safe_get(h, 'mrt_daily_taps', 0)
    # Avoid div-by-zero; only score cells that have at least 1 station
    taps_per_st = mrt_taps / n_st.where(n_st > 0, 1)
    # Healthy: <30K/day. Heavy: 50K. Overload: >80K. (Singapore MRT station
    # design capacity is ~75K daily tap-in equivalent; some interchange
    # stations like Jurong East exceed 200K.)
    raw_pressure = ((taps_per_st - 30000) / 50000).clip(0, 1)
    has_mrt = (n_st > 0).astype(float)
    h['f_line_pressure'] = (raw_pressure * has_mrt).clip(0, 1)

    # === Factor 6: f_low_frequency (FIXED v2) ===
    # Smooth saturation curve over bus routes (and MRT lines as bonus). 8+ routes
    # reaching this cell = fully served regardless of population size. The old
    # "routes per 1000 people" version had median 0.857 — penalised mid-density
    # HDB cells with 12 routes serving 80K residents (0.15 routes/1000) as
    # critically under-served, which is wrong.
    bus_routes = safe_get(h, 'bus_routes_count')
    mrt_lines  = safe_get(h, 'mrt_lines_count')
    # Saturation: tanh(routes/8) → 0 at 0 routes, ~0.76 at 8, ~0.96 at 16
    freq_score = np.tanh(bus_routes / 8.0) + 0.20 * np.tanh(mrt_lines / 2.0)
    freq_score = freq_score.clip(0, 1.05)
    h['f_low_frequency'] = (1 - freq_score).clip(0, 1)

    # === Factor 7: f_children_gap ===
    # Children far from school
    d_school = safe_get(h, 'dist_school_m', 1500)
    n_children = safe_get(h, 'children_count')
    child_intensity = (n_children / pop).clip(0, 0.30)  # share of pop that's children
    h['f_children_gap'] = (
        (d_school / 1200.0).clip(0, 1) * 0.6 +
        (child_intensity / 0.20).clip(0, 1) * (d_school / 800.0).clip(0, 1) * 0.4
    ).clip(0, 1)

    # === Factor 8: f_low_income_gap ===
    li_pop = safe_get(h, 'low_income_pop')
    li_share = (li_pop / pop).clip(0, 1)
    h['f_low_income_gap'] = (
        (d_mrt / 1200.0).clip(0, 1) * 0.5 +
        li_share * (d_mrt / 1000.0).clip(0, 1) * 0.5
    ).clip(0, 1)

    # === NEW Factor 9: f_dorm_gap ===
    # For cells with significant dorm pop, evaluate connectivity to industrial sites
    dorm_pop = safe_get(h, 'pop_nr_dorm')
    dorm_pop_share = (dorm_pop / pop).clip(0, 1)
    # Dorm workers need: bus access (commute), proximity to industrial zones (work)
    industrial_adj = safe_get(h, 'industrial_adjacency_score')
    # Gap = high dorm pop × bus distance × inverse industrial adjacency
    h['f_dorm_gap'] = (
        dorm_pop_share *
        ((d_bus / 600.0).clip(0, 1) * 0.5 + (1 - industrial_adj) * 0.5)
    ).clip(0, 1)

    # === NEW Factor 10: f_elderly_gap ===
    n_eld = safe_get(h, 'elderly_count')
    eld_share = (n_eld / pop).clip(0, 0.30)  # share elderly (typically 0..0.20)
    # Silver-zone proxy via amenities (CHAS clinics + silver crossings if available)
    silver_proxy = safe_get(h, 'silver_zones_count', 0) if 'silver_zones_count' in h.columns else pd.Series(0, index=h.index)
    silver_score = (silver_proxy / 2.0).clip(0, 1)  # 2+ silver zones = good
    h['f_elderly_gap'] = (
        eld_share * (d_mrt / 1000.0).clip(0, 1) * 0.5 +
        eld_share * (1 - silver_score) * 0.3 +
        eld_share * (d_bus / 500.0).clip(0, 1) * 0.2
    ).clip(0, 1) * (eld_share > 0).astype(float) * 5  # amplify when elderly present
    h['f_elderly_gap'] = h['f_elderly_gap'].clip(0, 1)

    # === NEW Factor 11: f_fdw_gap ===
    # FDWs are concentrated in households; off-day mobility = transit to remittance hubs
    fdw_pop = safe_get(h, 'pop_nr_fdw')
    fdw_share = (fdw_pop / pop).clip(0, 0.30)
    # Lucky Plaza / City Plaza / Peninsula Plaza are FDW hubs near CBD
    # Use CBD proximity inverse + park distance (Sunday rest spots)
    d_park = safe_get(h, 'dist_park_m', 1500)
    cbd_remote = (1 - safe_get(h, 'cbd_proximity_score'))
    h['f_fdw_gap'] = (
        fdw_share * cbd_remote * 0.5 +
        fdw_share * (d_park / 1000.0).clip(0, 1) * 0.3 +
        fdw_share * (d_bus / 500.0).clip(0, 1) * 0.2
    ).clip(0, 1) * 4  # amplify since fdw_share is small
    h['f_fdw_gap'] = h['f_fdw_gap'].clip(0, 1)

    # Compose default gap score: weighted mean of factors (excluding equity-specific ones
    # which act as overrides). Weights revised v2 after factor formula fixes:
    # - distance: 25% — most fundamental adequacy signal
    # - accessibility: 20% — now multi-modal walkability, not just walk-to-MRT
    # - connectivity: 20% — modes + lines + routes available
    # - last_mile: 15% — friction door-to-stop
    # - low_frequency: 15% — service intensity (now saturation-based)
    # - line_pressure: 5% — only meaningful when MRT in cell, so down-weighted
    core_factors = ['f_distance','f_accessibility','f_connectivity','f_last_mile','f_low_frequency','f_line_pressure']
    core_weights = [0.25, 0.20, 0.20, 0.15, 0.15, 0.05]
    h['gap_core'] = sum(h[f] * w for f, w in zip(core_factors, core_weights)).clip(0, 1)

    # Equity overlay: max of equity gaps
    equity_factors = ['f_children_gap','f_low_income_gap','f_dorm_gap','f_elderly_gap','f_fdw_gap']
    h['gap_equity_max'] = h[equity_factors].max(axis=1)

    # Default composite: average of core and equity-max
    h['gap_default'] = (h['gap_core'] * 0.7 + h['gap_equity_max'] * 0.3).clip(0, 1)

    h.to_parquet(IN_PATH, index=False)
    print(f'\nWrote {IN_PATH}  ({h.shape[1]} cols)')

    print('\nFactor means (active cells only):')
    active = h[h['cell_active_flag'] == 1] if 'cell_active_flag' in h.columns else h
    for f in core_factors + equity_factors + ['gap_default']:
        print(f'  {f:<22s}  mean={active[f].mean():.3f}  median={active[f].median():.3f}  >0.5={int((active[f]>0.5).sum())}')

if __name__ == '__main__':
    main()
