"""Merge per-hex explainability into hex8_adequacy.geojson + propagate to
subzone / PA / town geojsons (aggregated as a sentence picked from the
worst-gap child cell).
"""

import json
from pathlib import Path
from collections import defaultdict

EXPL_PATH = Path('data/hex_v11/hex8_explainability.jsonl')
HEX_PATH = Path('data/hex_v11/hex8_adequacy.geojson')
SZ_PATH = Path('data/hex_v11/subzone_adequacy.geojson')
PA_PATH = Path('data/hex_v11/pa_adequacy.geojson')
TOWN_PATH = Path('data/hex_v11/town_adequacy.geojson')

def main():
    # Load explanations
    expl = {}
    for line in EXPL_PATH.open():
        r = json.loads(line)
        expl[r['hex8_id']] = r
    print(f'Loaded {len(expl):,} explanations')

    # === HEX8 ===
    with HEX_PATH.open() as f:
        gj = json.load(f)
    n = 0
    for feat in gj['features']:
        p = feat['properties']
        hid = p.get('hex8_id') or p.get('hex_id')
        if hid in expl:
            r = expl[hid]
            p['availability_score'] = r['availability_score']
            p['adequacy_score']     = r['adequacy_score']
            p['explanation']        = r['explanation']
            p['primary_factor']     = r['primary_factor']
            n += 1
    with HEX_PATH.open('w') as f:
        json.dump(gj, f, separators=(',', ':'))
    print(f'  hex8_adequacy.geojson: {n} features tagged with explanations')

    # === Aggregate-level — pick the WORST cell's explanation as representative ===
    # Build subzone → list of (gap_default, expl)
    expl_with_zone = []
    for r in expl.values():
        # We need gap_default to pick the "worst" one; pull from hex8 geojson properties
        pass
    # Easier: rebuild by reading the hex8 props directly
    sz_worst = defaultdict(lambda: {'gap': -1.0, 'expl_id': None})
    pa_worst = defaultdict(lambda: {'gap': -1.0, 'expl_id': None})
    pa_to_town_label = {}
    for feat in gj['features']:
        p = feat['properties']
        hid = p.get('hex8_id')
        if hid not in expl: continue
        gap = float(p.get('gap_default') or 0)
        sz = p.get('parent_subzone')
        pa = p.get('parent_pa')
        if sz and gap > sz_worst[sz]['gap']:
            sz_worst[sz]['gap'] = gap
            sz_worst[sz]['expl_id'] = hid
        if pa and gap > pa_worst[pa]['gap']:
            pa_worst[pa]['gap'] = gap
            pa_worst[pa]['expl_id'] = hid

    def annotate(path, key_col, lookup):
        with path.open() as f: g = json.load(f)
        n_ann = 0
        for feat in g['features']:
            p = feat['properties']
            key = p.get(key_col)
            if not key: continue
            best = lookup.get(key)
            if not best or not best['expl_id']: continue
            r = expl[best['expl_id']]
            # Aggregate-level scores from the stored gap (avail and adequacy)
            avail_gap = float(p.get('availability_adequacy_gap_mean') or
                              p.get('availability_adequacy_gap') or 0)
            adeq_gap  = float(p.get('adequacy_default') or 0)
            p['availability_score'] = max(0, min(100, int(100 - round(avail_gap * 100))))
            p['adequacy_score']     = max(0, min(100, int(100 - round(adeq_gap * 100))))
            p['explanation']        = r['explanation']
            p['explanation_source'] = f'worst-cell: hex {best["expl_id"][-6:]}'
            n_ann += 1
        with path.open('w') as f: json.dump(g, f, separators=(',', ':'))
        print(f'  {path.name}: {n_ann} features tagged')

    annotate(SZ_PATH, 'parent_subzone', sz_worst)
    annotate(PA_PATH, 'parent_pa', pa_worst)
    annotate(TOWN_PATH, 'parent_pa', pa_worst)  # towns are PA-keyed

    print('\nDone.')

if __name__ == '__main__':
    main()
