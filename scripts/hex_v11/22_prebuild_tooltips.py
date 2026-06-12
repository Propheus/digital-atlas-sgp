"""For every scored hex, precompute per-profile tooltip strings so the
React popup can render with zero runtime computation.

Reads the ADEQUACY parquet (after 10_score_bands has set is_scored +
zone_type), pulls raw factor inputs from the FEATURES parquet, then:
  - writes 12 new columns back to hex8_adequacy.parquet
  - rebuilds hex8_adequacy.geojson so the React app picks them up
"""

import json
import pandas as pd
import numpy as np
import h3
from pathlib import Path

ADQ_PATH  = Path('data/hex_v11/hex8_adequacy.parquet')
FEAT_PATH = Path('data/hex_v11/hex8_adequacy_features.parquet')
GEO_PATH  = Path('data/hex_v11/hex8_adequacy.geojson')

# Profile-specific factor weights (must match 16_compose_adequacy.py)
AVAIL_WEIGHTS = {
    'default': {'f_distance': 0.30, 'f_accessibility': 0.25, 'f_last_mile': 0.25, 'f_connectivity': 0.20},
    'elderly': {'f_distance': 0.40, 'f_accessibility': 0.35, 'f_last_mile': 0.20, 'f_connectivity': 0.05},
    'family':  {'f_distance': 0.25, 'f_accessibility': 0.35, 'f_last_mile': 0.30, 'f_connectivity': 0.10},
    'workers': {'f_distance': 0.20, 'f_accessibility': 0.15, 'f_last_mile': 0.30, 'f_connectivity': 0.35},
}
QUALITY_WEIGHTS = {
    'default': {'frequency': 0.42, 'reach': 0.33, 'crowding': 0.17, 'resilience': 0.08},
    'elderly': {'frequency': 0.55, 'reach': 0.15, 'crowding': 0.25, 'resilience': 0.05},
    'family':  {'frequency': 0.40, 'reach': 0.20, 'crowding': 0.30, 'resilience': 0.10},
    'workers': {'frequency': 0.30, 'reach': 0.40, 'crowding': 0.20, 'resilience': 0.10},
}

FACTOR_COL = {
    'f_distance':      'f_distance',
    'f_accessibility': 'f_accessibility',
    'f_last_mile':     'f_last_mile',
    'f_connectivity':  'f_connectivity',
    'frequency':       'frequency_adequacy_gap',
    'reach':           'reach_adequacy_gap',
    'crowding':        'crowding_adequacy_gap',
    'resilience':      'resilience_adequacy_gap',
}

def text_for_factor(factor, r):
    def num(k, default=0):
        v = r.get(k)
        try: return float(v) if v is not None and not pd.isna(v) else default
        except Exception: return default

    if factor == 'f_distance':
        d_mrt = num('dist_nearest_mrt_m')
        if d_mrt > 1500: return f'📏 MRT {d_mrt/1000:.1f} km away'
        if d_mrt > 500:  return f'📏 MRT {int(d_mrt)} m away'
        return '📏 MRT within walking range'
    if factor == 'f_accessibility':
        return '♿ Walk-unfriendly area'
    if factor == 'f_last_mile':
        d_bus = num('dist_bus_m')
        if d_bus > 400: return f'🚶 Long walk to bus ({int(d_bus)} m)'
        return '🚶 Last-mile friction'
    if factor == 'f_connectivity':
        n_routes = int(num('bus_routes_count'))
        n_lines  = int(num('mrt_lines_count'))
        return f'🔗 Limited transit ({n_lines} lines · {n_routes} routes)'
    if factor == 'frequency':
        w = num('peak_wait_min')
        return f'⏱ Peak wait {w:.0f} min'
    if factor == 'reach':
        t = num('time_to_cbd_min')
        if not pd.isna(t) and t > 0:
            return f'🎯 CBD takes {int(t)} min'
        pct = num('pct_dest_within_45min')
        return f'🎯 Only {int(pct)}% destinations in 45 min'
    if factor == 'crowding':
        return '😤 Crowded at peak'
    if factor == 'resilience':
        n = int(num('n_lines_to_cbd'))
        if n == 0: return '🛡 No direct line to CBD'
        if n == 1: return '🛡 Single line to CBD'
        return f'🛡 {n} lines to CBD'
    return ''

def primary_for_profile(r, profile):
    aw = AVAIL_WEIGHTS[profile]
    qw = QUALITY_WEIGHTS[profile]
    contributions = {}
    for f, col in FACTOR_COL.items():
        v = r.get(col)
        if v is None or pd.isna(v): continue
        v = float(v)
        if f in aw:
            contributions[f] = aw[f] * v
        elif f in qw:
            contributions[f] = qw[f] * v
    if not contributions: return None
    return max(contributions.items(), key=lambda kv: kv[1])[0]

def fmt_num(n):
    n = int(round(n))
    if n >= 100000: return f'{n/1000:.0f}K'
    if n >= 1000:   return f'{n/1000:.1f}K'
    return f'{n:,}'

def pop_callout(r, profile):
    def num(k, default=0):
        v = r.get(k)
        try: return float(v) if v is not None and not pd.isna(v) else default
        except Exception: return default

    pop_total = num('pop_total')
    if pop_total <= 0:
        return '⬜ Sparse / no residents'

    if profile == 'elderly':
        eld = num('elderly_count')
        share = (eld / pop_total) * 100 if pop_total else 0
        if eld < 50:
            return f'👵 Few elderly ({int(eld)} · {share:.0f}%)'
        d_mrt = num('dist_nearest_mrt_m')
        return f'👵 {fmt_num(eld)} elderly ({share:.0f}%) · MRT {int(d_mrt)}m'

    if profile == 'family':
        ch = num('children_count')
        share = (ch / pop_total) * 100 if pop_total else 0
        if ch < 30:
            return f'🎒 Few children ({int(ch)} · {share:.0f}%)'
        d_school = num('dist_school_m')
        return f'🎒 {fmt_num(ch)} children ({share:.0f}%) · school {int(d_school)}m'

    if profile == 'workers':
        dorm = num('pop_nr_dorm')
        ep = num('pop_nr_ep') + num('pop_nr_sp') + num('pop_nr_wp_other') + num('pop_nr_fdw')
        nr_total = dorm + ep
        if nr_total < 100:
            return f'👷 Few NR workers ({int(nr_total)})'
        if dorm > nr_total * 0.4:
            return f'👷 {fmt_num(dorm)} dorm + {fmt_num(ep)} other NR'
        return f'👷 {fmt_num(int(nr_total))} non-residents'

    # default
    res = num('pop_resident')
    nr  = num('pop_non_resident')
    if nr > 100:
        return f'👥 {fmt_num(res)} residents · {fmt_num(nr)} NR'
    return f'👥 {fmt_num(res)} residents'

def hex8_to_polygon(hex_id):
    boundary = h3.cell_to_boundary(hex_id)
    coords = [[lng, lat] for (lat, lng) in boundary]
    coords.append(coords[0])
    return [coords]

def safe_json(v):
    if v is None: return None
    if isinstance(v, float):
        if np.isnan(v): return None
        return float(v)
    if isinstance(v, (np.integer,)): return int(v)
    if isinstance(v, (np.floating,)): return None if np.isnan(v) else float(v)
    if isinstance(v, np.bool_): return bool(v)
    if hasattr(v, 'item'): return v.item()
    return v

def main():
    print('Reading parquets…')
    adq = pd.read_parquet(ADQ_PATH)
    feat = pd.read_parquet(FEAT_PATH)

    # Merge raw factor inputs (from feat) onto adq for the cells where adq has them
    feat_extras = [c for c in feat.columns
                   if c not in adq.columns
                   and c not in ('hex8_id','lat','lng','area_km2','parent_subzone','parent_pa','parent_region')]
    merged = adq.merge(feat[['hex8_id'] + feat_extras], on='hex8_id', how='left')
    print(f'Merged {len(merged):,} rows  ({len(feat_extras)} extra cols from features)')

    # Compute tooltip fields per cell
    print('Computing tooltips…')
    cols = {f'primary_factor_{p}': [] for p in ('default','elderly','family','workers')}
    cols.update({f'primary_text_{p}':   [] for p in ('default','elderly','family','workers')})
    cols.update({f'pop_callout_{p}':    [] for p in ('default','elderly','family','workers')})

    for _, r in merged.iterrows():
        is_active = bool(r.get('is_scored')) or bool(r.get('is_data_shown'))
        for prof in ('default','elderly','family','workers'):
            if not is_active:
                cols[f'primary_factor_{prof}'].append(None)
                cols[f'primary_text_{prof}'].append(None)
                cols[f'pop_callout_{prof}'].append(None)
                continue
            f = primary_for_profile(r, prof)
            cols[f'primary_factor_{prof}'].append(f)
            cols[f'primary_text_{prof}'].append(text_for_factor(f, r) if f else None)
            cols[f'pop_callout_{prof}'].append(pop_callout(r, prof))

    for k, v in cols.items():
        adq[k] = v

    adq.to_parquet(ADQ_PATH, index=False)
    print(f'Wrote {ADQ_PATH}  (now {len(adq.columns)} cols)')

    # Re-emit hex8_adequacy.geojson with tooltip fields included
    print('Re-emitting geojson…')
    features = []
    n_with_tooltip = 0
    for _, r in adq.iterrows():
        props = {k: safe_json(v) for k, v in r.to_dict().items()}
        if props.get('primary_text_default'): n_with_tooltip += 1
        features.append({
            'type': 'Feature',
            'geometry': {'type': 'Polygon', 'coordinates': hex8_to_polygon(r['hex8_id'])},
            'properties': props,
        })
    gj = {'type': 'FeatureCollection', 'features': features}
    with GEO_PATH.open('w') as f:
        json.dump(gj, f, separators=(',', ':'))
    size_mb = GEO_PATH.stat().st_size / 1e6
    print(f'Wrote {GEO_PATH} ({size_mb:.2f} MB) — {n_with_tooltip} cells tagged with tooltips')

    # Quick sample
    sample = adq[adq['is_scored'] == True].head(1)
    if len(sample):
        r = sample.iloc[0]
        print(f'\nSample: {r["parent_subzone"]}')
        for p in ('default','elderly','family','workers'):
            print(f'  {p:>8s}: text="{r[f"primary_text_{p}"]}"  |  pop="{r[f"pop_callout_{p}"]}"')

if __name__ == '__main__':
    main()
