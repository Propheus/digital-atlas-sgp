"""End-to-end verification of one hex: pull all inputs, replay every formula,
compare against stored values. Exposes any inconsistencies in the pipeline.

Pick a hex by id; the script traces:
  1. Identity + zone_type classification
  2. Population breakdown by bucket (sum check)
  3. The 6 availability sub-factors → gap_core (availability_adequacy_gap)
  4. The 4 quality dimensions (freq / reach / crowd / resil)
     With per-step input inspection
  5. The composite formulas:
       quality_only = weighted mean of quality dims
       adequacy_core = max(availability, quality_only)
       adequacy_default = max(adequacy_core × 0.7 + equity × 0.3, availability)
  6. Re-aggregate to subzone level and check that totals match

Usage:
  python3 scripts/hex_v11/19_verify_hex.py <hex8_id>
"""

import sys, math
import pandas as pd
import numpy as np
from pathlib import Path

# Default: a known interesting case (Punggol Field, NEL terminus)
DEFAULT_HEX = '886526375bfffff'

def pct(a, b):
    return f'{100*a/b:.1f}%' if b else 'n/a'

def banner(s, char='='):
    print()
    print(char * 76)
    print(f' {s}')
    print(char * 76)

def check(label, expected, actual, tol=0.005):
    ok = '✓' if abs(expected - actual) <= tol else '⚠ MISMATCH'
    print(f'  {label:<55s} expected={expected:.4f}  actual={actual:.4f}  [{ok}]')
    return ok == '✓'

def main():
    hex_id = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_HEX
    # Merge the features file (has all raw inputs) with the bands file (has
    # zone_type_broad, is_data_shown, etc.) so we have one row with everything
    h_feat = pd.read_parquet('data/hex_v11/hex8_adequacy_features.parquet')
    h_band = pd.read_parquet('data/hex_v11/hex8_adequacy.parquet')
    extra = [c for c in h_band.columns if c not in h_feat.columns and c != 'hex8_id']
    h = h_feat.merge(h_band[['hex8_id'] + extra], on='hex8_id', how='left')
    row = h[h['hex8_id'] == hex_id]
    if len(row) == 0:
        print(f'Hex {hex_id} not found. Available residential hexes:')
        print(h[h['is_scored']==True].head(10)[['hex8_id','parent_subzone','pop_total']].to_string())
        return
    r = row.iloc[0]

    banner('1. IDENTITY + ZONE TYPE')
    print(f'  hex8_id           : {r["hex8_id"]}')
    print(f'  parent_subzone    : {r["parent_subzone"]}')
    print(f'  parent_pa         : {r["parent_pa"]}')
    print(f'  parent_region     : {r["parent_region"]}')
    print(f'  zone_type_broad   : {r["zone_type_broad"]}')
    print(f'  zone_type         : {r["zone_type"]}')
    print(f'  is_scored         : {r["is_scored"]}')
    print(f'  is_data_shown     : {r.get("is_data_shown")}')
    print(f'  centroid          : ({r["lat"]:.5f}, {r["lng"]:.5f})')
    print(f'  area_km2          : {r["area_km2"]:.3f}')

    banner('2. POPULATION BUCKETS')
    pop_res = float(r['pop_resident'])
    pop_nr_dorm = float(r['pop_nr_dorm'])
    pop_nr_fdw  = float(r['pop_nr_fdw'])
    pop_nr_ep   = float(r['pop_nr_ep'])
    pop_nr_sp   = float(r['pop_nr_sp'])
    pop_nr_wp   = float(r['pop_nr_wp_other'])
    pop_nr      = float(r['pop_non_resident'])
    pop_total   = float(r['pop_total'])
    nr_sum_from_buckets = pop_nr_dorm + pop_nr_fdw + pop_nr_ep + pop_nr_sp + pop_nr_wp
    print(f'  Resident                 : {pop_res:>10,.0f}')
    print(f'  NR Dorm                  : {pop_nr_dorm:>10,.0f}')
    print(f'  NR MDW (FDW)             : {pop_nr_fdw:>10,.0f}')
    print(f'  NR EP + dep              : {pop_nr_ep:>10,.0f}')
    print(f'  NR S Pass                : {pop_nr_sp:>10,.0f}')
    print(f'  NR WP-other              : {pop_nr_wp:>10,.0f}')
    print(f'  Σ NR buckets (computed)  : {nr_sum_from_buckets:>10,.0f}')
    print(f'  pop_non_resident (stored): {pop_nr:>10,.0f}')
    check_nr = check('  NR sum-of-buckets', pop_nr, nr_sum_from_buckets, tol=1.0)
    expected_total = pop_res + pop_nr
    check_total = check('  pop_total = resident + NR', pop_total, expected_total, tol=1.0)

    banner('3. AVAILABILITY — gap_core inputs + composite')
    f_dist = float(r['f_distance'])
    f_acc  = float(r['f_accessibility'])
    f_lm   = float(r['f_last_mile'])
    f_conn = float(r['f_connectivity'])
    f_freq = float(r['f_low_frequency'])
    f_lp   = float(r['f_line_pressure'])
    avail_stored = float(r['availability_adequacy_gap'])

    print(f'  Inputs to the 6 availability factors')
    print(f'    dist_nearest_mrt_m  : {r["dist_nearest_mrt_m"]:.0f}')
    print(f'    dist_bus_m          : {r["dist_bus_m"]:.0f}')
    print(f'    bus_routes_count    : {int(r["bus_routes_count"])}')
    print(f'    mrt_stations        : {int(r["mrt_stations"])}')
    print(f'    walk_mrt_score      : {r["walk_mrt_score"]:.3f}')
    print()
    print(f'  Computed factor values')
    print(f'    f_distance       = {f_dist:.4f}')
    print(f'    f_accessibility  = {f_acc:.4f}')
    print(f'    f_last_mile      = {f_lm:.4f}')
    print(f'    f_connectivity   = {f_conn:.4f}')
    print(f'    f_low_frequency  = {f_freq:.4f}')
    print(f'    f_line_pressure  = {f_lp:.4f}')
    print()
    print(f'  Replay availability composite (no double-counting):')
    avail_replay = 0.30*f_dist + 0.25*f_acc + 0.25*f_lm + 0.20*f_conn
    print(f'    0.30 × f_distance       = {0.30*f_dist:.4f}')
    print(f'    0.25 × f_accessibility  = {0.25*f_acc:.4f}')
    print(f'    0.25 × f_last_mile      = {0.25*f_lm:.4f}')
    print(f'    0.20 × f_connectivity   = {0.20*f_conn:.4f}')
    print(f'    Σ availability_replay   = {avail_replay:.4f}')
    print()
    check_avail = check('availability_adequacy_gap stored', avail_stored, avail_replay)

    banner('4. QUALITY DIMENSIONS')
    freq_g = float(r['frequency_adequacy_gap'])
    reach_g = float(r['reach_adequacy_gap'])
    crowd_g = float(r['crowding_adequacy_gap'])
    resil_g = float(r['resilience_adequacy_gap'])
    quality_stored = float(r['quality_only_gap']) if 'quality_only_gap' in r else None
    print(f'  Frequency')
    print(f'    peak_wait_min       : {r["peak_wait_min"]:.2f}')
    print(f'    → frequency gap     : {freq_g:.4f}')
    print()
    print(f'  Reach')
    print(f'    time_to_cbd_min     : {r["time_to_cbd_min"]:.1f}')
    print(f'    pct_dest_within_45  : {r["pct_dest_within_45min"]:.1f}%')
    print(f'    → reach gap         : {reach_g:.4f}    (1 - pct/80, clipped)')
    expected_reach = max(0.0, min(1.0, 1 - float(r["pct_dest_within_45min"]) / 80.0))
    check('  reach gap formula', expected_reach, reach_g)
    print()
    print(f'  Crowding')
    print(f'    nearest_mrt_st_peak_taps : {r["nearest_mrt_st_peak_taps"]:.0f}')
    print(f'    → crowding gap      : {crowd_g:.4f}')
    print()
    print(f'  Resilience')
    print(f'    n_lines_to_cbd      : {int(r["n_lines_to_cbd"])}')
    print(f'    n_stations_walking  : {int(r["n_stations_walking"])}')
    print(f'    → resilience gap    : {resil_g:.4f}')
    print()
    print(f'  Composite quality_only (renormalised weights):')
    quality_replay = 0.42*freq_g + 0.33*reach_g + 0.17*crowd_g + 0.08*resil_g
    print(f'    0.42 × frequency    = {0.42*freq_g:.4f}')
    print(f'    0.33 × reach        = {0.33*reach_g:.4f}')
    print(f'    0.17 × crowding     = {0.17*crowd_g:.4f}')
    print(f'    0.08 × resilience   = {0.08*resil_g:.4f}')
    print(f'    Σ quality_replay    = {quality_replay:.4f}')
    if quality_stored is not None:
        check('quality_only_gap stored', quality_stored, quality_replay)

    banner('5. COMPOSITE FORMULA — adequacy_core + adequacy_default')
    adequacy_core_stored = float(r['adequacy_core'])
    adequacy_default_stored = float(r['adequacy_default'])
    equity_max = float(r.get('gap_equity_max', 0))
    print(f'  Hard floor: adequacy_core = max(availability, quality_only)')
    adeq_core_replay = max(avail_replay, quality_replay)
    print(f'    max({avail_replay:.4f}, {quality_replay:.4f}) = {adeq_core_replay:.4f}')
    check_core = check('adequacy_core stored', adequacy_core_stored, adeq_core_replay)
    print()
    print(f'  Equity overlay: adequacy_default = max(core × 0.7 + equity × 0.3, availability)')
    print(f'    equity_max (max of 5 equity factors): {equity_max:.4f}')
    adeq_blend = 0.7 * adeq_core_replay + 0.3 * equity_max
    adeq_default_replay = max(adeq_blend, avail_replay)
    print(f'    0.7 × {adeq_core_replay:.4f} + 0.3 × {equity_max:.4f} = {adeq_blend:.4f}')
    print(f'    max({adeq_blend:.4f}, availability {avail_replay:.4f}) = {adeq_default_replay:.4f}')
    check_default = check('adequacy_default stored', adequacy_default_stored, adeq_default_replay)
    print()
    # Translate to user-facing scores
    avail_score = 100 - round(avail_stored * 100)
    adeq_score = 100 - round(adequacy_default_stored * 100)
    print(f'  → Availability score: {avail_score} (band: {band(avail_stored)})')
    print(f'  → Adequacy score:     {adeq_score} (band: {band(adequacy_default_stored)})')

    banner('6. SUBZONE ROLLUP — check consistency')
    sz_name = r['parent_subzone']
    sz = pd.read_parquet('data/hex_v11/subzone_adequacy.parquet')
    sz_row = sz[sz['parent_subzone'] == sz_name]
    if len(sz_row):
        sz_row = sz_row.iloc[0]
        print(f'  Subzone: {sz_name}')
        # Sum check: pop_total in subzone should equal sum of all hex8 in it
        all_hex_in_sz = h[h['parent_subzone'] == sz_name]
        hex_pop_sum = all_hex_in_sz['pop_total'].sum()
        print(f'    Σ hex8 pop_total      : {hex_pop_sum:,.0f}')
        print(f'    Stored sz pop_total   : {sz_row["pop_total"]:,.0f}')
        check_pop = check('  subzone pop_total = sum of child hexes', hex_pop_sum, sz_row['pop_total'], tol=1.0)
        # Pop-weighted availability check
        pop_w = all_hex_in_sz['pop_total'].fillna(0)
        wmean_avail = (all_hex_in_sz['availability_adequacy_gap'].fillna(0) * pop_w).sum() / pop_w.sum()
        print(f'    Σ hex8 wmean avail    : {wmean_avail:.4f}')
        print(f'    Stored sz avail_mean  : {sz_row["availability_adequacy_gap_mean"]:.4f}')
        check_wmean = check('  subzone availability = pop-weighted mean', wmean_avail, sz_row["availability_adequacy_gap_mean"])

    banner('VERIFICATION SUMMARY', char='*')
    print('All cross-checks complete. See ✓ / ⚠ markers above.')

def band(v):
    if v < 0.30: return 'Excellent'
    if v < 0.50: return 'Good'
    if v < 0.70: return 'Moderate'
    if v < 0.85: return 'Poor'
    return 'Critical'

if __name__ == '__main__':
    main()
