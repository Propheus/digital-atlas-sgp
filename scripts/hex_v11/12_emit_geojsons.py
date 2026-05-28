"""Emit per-level geojsons by joining boundary polygons with aggregate parquets.

Outputs (all in data/hex_v11/):
  subzone_adequacy.geojson   ~258 features
  pa_adequacy.geojson        52 features
  town_adequacy.geojson      25 features

All three geojsons share a flat property schema so the React map can swap
sources by changing the URL + source name only.
"""

import json
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from hdb_towns import classify_pa

BANDS = [(0.30, 'excellent'), (0.50, 'good'), (0.70, 'moderate'), (0.85, 'poor'), (1.01, 'critical')]

def band_of(v):
    if v is None or (isinstance(v, float) and v != v): return 'unknown'
    for thr, name in BANDS:
        if v < thr: return name
    return 'critical'

def title_case(s):
    if not s: return s
    return s.title().replace("/Whampoa", " / Whampoa")

def safe_props(d):
    """Coerce numpy types → native python for JSON."""
    out = {}
    for k, v in d.items():
        if v is None: out[k] = None
        elif isinstance(v, float):
            out[k] = None if v != v else float(v)  # NaN → None
        elif isinstance(v, (int,)): out[k] = int(v)
        elif hasattr(v, 'item'): out[k] = v.item()
        else: out[k] = v
    return out

def emit(boundary_path, agg_df, key_in_boundary, key_in_agg, out_path, title_case_match=True, hdb_filter=False):
    """Generic join boundary geojson with aggregate dataframe."""
    with open(boundary_path) as f:
        gj = json.load(f)

    lookup = {}
    for _, row in agg_df.iterrows():
        k = str(row[key_in_agg])
        lookup[k.upper()] = row.to_dict()

    out_features = []
    matched = 0
    for feat in gj['features']:
        bname = (feat['properties'].get(key_in_boundary) or '').strip()
        if not bname: continue
        if hdb_filter:
            tc = title_case(bname)
            is_town, _, cat = classify_pa(tc)
            if not is_town:
                continue
        agg = lookup.get(bname.upper())
        if not agg:
            continue
        matched += 1
        gap = agg.get('gap_default')
        agg['gap_default_band'] = band_of(gap)
        adq = agg.get('adequacy_default')
        if adq is not None:
            agg['adequacy_default_band'] = band_of(adq)
        agg[key_in_boundary] = bname  # keep original
        # Make display name title-cased for UI
        agg['display_name'] = title_case(bname)
        new_feat = {
            'type': 'Feature',
            'geometry': feat['geometry'],
            'properties': safe_props(agg),
        }
        out_features.append(new_feat)
    out_gj = {'type': 'FeatureCollection', 'features': out_features}
    with open(out_path, 'w') as f:
        json.dump(out_gj, f, separators=(',', ':'))
    size_mb = out_path.stat().st_size / 1e6
    print(f'  {out_path.name}: {matched} features, {size_mb:.2f} MB')

def main():
    # === Subzone ===
    print('=== Subzone geojson ===')
    sz_agg = pd.read_parquet('data/hex_v11/subzone_adequacy.parquet')
    print(f'  agg rows: {len(sz_agg)}')
    emit(
        Path('data/boundaries/subzones.geojson'), sz_agg,
        key_in_boundary='SUBZONE_N', key_in_agg='parent_subzone',
        out_path=Path('data/hex_v11/subzone_adequacy.geojson'),
    )

    # === Planning Area ===
    print('\n=== PA geojson ===')
    pa_agg = pd.read_parquet('data/hex_v11/pa_adequacy.parquet')
    print(f'  agg rows: {len(pa_agg)}')
    emit(
        Path('data/boundaries/planning_areas.geojson'), pa_agg,
        key_in_boundary='PLN_AREA_N', key_in_agg='parent_pa',
        out_path=Path('data/hex_v11/pa_adequacy.geojson'),
    )

    # === HDB Town (PA boundaries filtered) ===
    print('\n=== HDB Town geojson ===')
    town_agg = pd.read_parquet('data/hex_v11/town_adequacy.parquet')
    print(f'  agg rows: {len(town_agg)}')
    emit(
        Path('data/boundaries/planning_areas.geojson'), town_agg,
        key_in_boundary='PLN_AREA_N', key_in_agg='parent_pa',
        out_path=Path('data/hex_v11/town_adequacy.geojson'),
        hdb_filter=True,
    )

    # Summary
    print('\n=== Output summary ===')
    import os
    for f in ['subzone_adequacy.geojson','pa_adequacy.geojson','town_adequacy.geojson']:
        p = Path('data/hex_v11') / f
        if p.exists():
            print(f'  {f}: {p.stat().st_size/1e6:.2f} MB')

if __name__ == '__main__':
    main()
