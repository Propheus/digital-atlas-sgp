"""Emit 4 minimal places-overlay geojsons for the Mapbox layer panel.

One file per bucket — used by the map's "Places" overlay with sub-filter
chips (Essentials / School / Retail+Leisure / Health / All).

Each feature carries the minimum needed to render: lat/lng + a single
short `cat` string (the bucket micro-label). Names/ratings are dropped
to keep the wire size tight.
"""

import json
from pathlib import Path

PLACES   = Path('data/places_consolidated/sgp_places_v2.jsonl')
AMEN_DIR = Path('data/amenities')
OUT_DIR  = Path('/Users/sumanth/propheus-projs/da-apps-sgp-mobility/da-apps-sgp-mobility/transport-adequacy-app/public/data/overlays')
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Bucket → list of (source, raw_category, micro_label)
# source = 'place' (uses main_category) or 'amenity' (uses a geojson file)
ESSENTIALS = [
    ('amenity', 'hawker_centres.geojson',       'hawker'),
    ('amenity', 'supermarkets.geojson',         'super'),
    ('amenity', 'chas_clinics.geojson',         'clinic'),
    ('amenity', 'parks_nature_reserves.geojson','park'),
    ('place',   'Convenience & Daily Needs',    'conv'),
]
SCHOOL = [
    ('amenity', 'preschools.geojson', 'preschool'),
    ('place',   'Education',          'edu'),
]
RETAIL = [
    ('place',   'Restaurant',              'restaurant'),
    ('place',   'Cafe & Coffee',           'cafe'),
    ('place',   'Bakery & Pastry',         'bakery'),
    ('place',   'Fast Food & QSR',         'qsr'),
    ('place',   'Shopping & Retail',       'retail'),
    ('place',   'Fitness & Recreation',    'fitness'),
    ('place',   'Culture & Entertainment', 'culture'),
    ('place',   'Bar & Nightlife',         'bar'),
]
HEALTH = [
    ('amenity', 'chas_clinics.geojson', 'clinic'),
    ('place',   'Health & Medical',     'health'),
]


def amenity_points(filename):
    path = AMEN_DIR / filename
    pts = []
    with open(path) as f:
        gj = json.load(f)
    for ft in gj['features']:
        g = ft.get('geometry') or {}
        t = g.get('type')
        if t == 'Point':
            lng, lat = g['coordinates'][:2]
            pts.append((lat, lng))
        elif t in ('Polygon','MultiPolygon'):
            coords = g['coordinates']
            if t == 'MultiPolygon': coords = coords[0]
            ring = coords[0]
            lats = [p[1] for p in ring]; lngs = [p[0] for p in ring]
            pts.append((sum(lats)/len(lats), sum(lngs)/len(lngs)))
    return pts


def load_places_by_main_cat():
    by_cat = {}
    with PLACES.open() as f:
        for line in f:
            p = json.loads(line)
            mc = p.get('main_category')
            lat = p.get('latitude'); lng = p.get('longitude')
            if not mc or lat is None or lng is None: continue
            by_cat.setdefault(mc, []).append((lat, lng))
    return by_cat


def collect_bucket(specs, places_by_cat):
    feats = []
    for src, ref, micro in specs:
        if src == 'amenity':
            pts = amenity_points(ref)
        else:
            pts = places_by_cat.get(ref, [])
        for lat, lng in pts:
            feats.append({
                'type': 'Feature',
                'geometry': {'type': 'Point', 'coordinates': [round(lng, 5), round(lat, 5)]},
                'properties': {'cat': micro},
            })
    return feats


def emit(name, feats):
    out = OUT_DIR / f'places_{name}.geojson'
    with out.open('w') as f:
        json.dump({'type': 'FeatureCollection', 'features': feats}, f, separators=(',', ':'))
    size_kb = out.stat().st_size / 1024
    print(f'  {name:<11s}  {len(feats):>6,d} points  ({size_kb:,.0f} KB)')


def main():
    print('Loading places…')
    pc = load_places_by_main_cat()
    print(f'  {sum(len(v) for v in pc.values()):,} geocoded places')

    print('\nEmitting per-bucket overlays…')
    emit('essentials', collect_bucket(ESSENTIALS, pc))
    emit('school',     collect_bucket(SCHOOL,     pc))
    emit('retail',     collect_bucket(RETAIL,     pc))
    emit('health',     collect_bucket(HEALTH,     pc))

    print(f'\nWrote to {OUT_DIR}/')


if __name__ == '__main__':
    main()
