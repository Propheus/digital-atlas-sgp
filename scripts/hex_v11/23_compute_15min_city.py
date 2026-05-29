"""15-minute city score per hex.

For each hex centroid, count nearby places across 4 buckets and compute
a 0-100 composite score that says: "Can you live your daily life within
a 15-minute walk?"

Walking model:
  - 0-400 m   ≈ 5-min walk   → full credit (1.0)
  - 400-1000m ≈ 5-12 min     → linear decay (1.0 → 0.6)
  - 1000-1500m ≈ 12-18 min   → linear decay (0.6 → 0.0)
  - >1500 m                  → 0

Buckets (user-locked):
  - essentials   : hawker + supermarket + chas_clinic + park + convenience
  - school       : preschool + school (authoritative) + education places
  - retail_lei   : restaurant + cafe + fitness + entertainment + retail + bar
  - healthcare   : chas_clinic + health & medical places (full)

Composite weights:
  essentials 0.40   school 0.20   retail_lei 0.20   healthcare 0.20

Diversity bonus: +0.10 to the bucket sub-score if 3+ distinct *micro*-categories
are within walking range (rewards variety, not just density).

Outputs to hex8_adequacy.parquet (and re-emitted geojson via 22):
  - min15_score              (0-100, weighted composite)
  - min15_essentials         (0-100)
  - min15_school             (0-100)
  - min15_retail             (0-100)
  - min15_health             (0-100)
  - min15_count_essentials   (raw count within 1km)
  - min15_count_school
  - min15_count_retail
  - min15_count_health
  - min15_nearest_hawker_m
  - min15_nearest_super_m
  - min15_nearest_clinic_m
  - min15_nearest_park_m
  - min15_nearest_school_m
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.neighbors import BallTree

ADQ_PATH = Path('data/hex_v11/hex8_adequacy.parquet')
PLACES   = Path('data/places_consolidated/sgp_places_v2.jsonl')
AMEN_DIR = Path('data/amenities')

R_EARTH = 6371000.0  # meters
WALK_CUTOFF_M = 1500.0
WALK_CUTOFF_RAD = WALK_CUTOFF_M / R_EARTH


def access_score(d_m):
    """Distance → 0-1 access score."""
    if d_m is None or np.isnan(d_m): return 0.0
    if d_m <= 400:  return 1.0
    if d_m <= 1000: return 1.0 - 0.4 * (d_m - 400) / 600.0    # 1.0 → 0.6
    if d_m <= 1500: return 0.6 - 0.6 * (d_m - 1000) / 500.0   # 0.6 → 0.0
    return 0.0


def load_authoritative():
    """Authoritative point datasets (small, curated)."""
    pts = {}  # name → list[(lat,lng)]

    def from_geojson(path, lat_key=None, lng_key=None):
        out = []
        with open(path) as f:
            gj = json.load(f)
        for ft in gj['features']:
            g = ft.get('geometry') or {}
            if g.get('type') == 'Point':
                lng, lat = g['coordinates'][0], g['coordinates'][1]
                out.append((lat, lng))
            elif g.get('type') in ('Polygon','MultiPolygon'):
                # use centroid via mean of first ring
                coords = g['coordinates']
                if g['type'] == 'MultiPolygon': coords = coords[0]
                ring = coords[0]
                lats = [p[1] for p in ring]; lngs = [p[0] for p in ring]
                out.append((sum(lats)/len(lats), sum(lngs)/len(lngs)))
        return out

    pts['hawker']  = from_geojson(AMEN_DIR / 'hawker_centres.geojson')
    pts['super']   = from_geojson(AMEN_DIR / 'supermarkets.geojson')
    pts['clinic']  = from_geojson(AMEN_DIR / 'chas_clinics.geojson')
    pts['park']    = from_geojson(AMEN_DIR / 'parks_nature_reserves.geojson')
    pts['presch']  = from_geojson(AMEN_DIR / 'preschools.geojson')

    # Schools from geocoded JSON (keys: name, lat, lon)
    with open(AMEN_DIR / 'schools_geocoded.json') as fh:
        schools = json.load(fh)
    school_pts = []
    for s in schools:
        lat = s.get('lat'); lng = s.get('lon')
        if lat is None or lng is None: continue
        school_pts.append((float(lat), float(lng)))
    pts['school'] = school_pts

    for k, v in pts.items():
        print(f'  authoritative {k:>8s}: {len(v):>5,d}')
    return pts


def load_places():
    """Sort 174K places into category lists."""
    cats = {
        'restaurant':   ['Restaurant','Fast Food & QSR','Bakery & Pastry'],
        'cafe':         ['Cafe & Coffee'],
        'fitness':      ['Fitness & Recreation'],
        'entertainment':['Culture & Entertainment','Bar & Nightlife'],
        'retail':       ['Shopping & Retail'],
        'convenience':  ['Convenience & Daily Needs'],
        'health_med':   ['Health & Medical'],
        'education':    ['Education'],
        'civic':        ['Civic & Government'],
    }
    cat_pts = {k: [] for k in cats}
    with PLACES.open() as f:
        for line in f:
            p = json.loads(line)
            lat = p.get('latitude'); lng = p.get('longitude')
            if lat is None or lng is None: continue
            mc = p.get('main_category')
            for k, mcs in cats.items():
                if mc in mcs:
                    cat_pts[k].append((lat, lng))
                    break
    for k, v in cat_pts.items():
        print(f'  places       {k:>13s}: {len(v):>6,d}')
    return cat_pts


def build_tree(pts):
    if not pts: return None, None
    arr = np.deg2rad(np.array(pts, dtype=np.float64))  # (N,2) [lat,lng] in rad
    tree = BallTree(arr, metric='haversine')
    return tree, arr


def nearest_dist_m(tree, lat_rad, lng_rad):
    if tree is None: return np.nan
    d, _ = tree.query([[lat_rad, lng_rad]], k=1)
    return float(d[0][0]) * R_EARTH


def count_within(tree, lat_rad, lng_rad, cutoff_m=1000.0):
    if tree is None: return 0
    r = cutoff_m / R_EARTH
    return int(tree.query_radius([[lat_rad, lng_rad]], r=r, count_only=True)[0])


def main():
    print('Loading inputs…')
    auth = load_authoritative()
    plc  = load_places()

    print('Building spatial trees…')
    trees = {}
    for k, pts in {**auth, **plc}.items():
        t, _ = build_tree(pts)
        trees[k] = t

    print('Reading adequacy parquet…')
    adq = pd.read_parquet(ADQ_PATH)
    print(f'  {len(adq):,} hexes')

    # Bucket → contributors
    # Each contributor: (tree_key, weight inside the bucket)
    BUCKETS = {
        'essentials': [('hawker',0.25),('super',0.20),('clinic',0.20),
                       ('park',0.15),('convenience',0.20)],
        'school':     [('presch',0.40),('school',0.40),('education',0.20)],
        'retail':     [('restaurant',0.25),('cafe',0.20),('retail',0.20),
                       ('fitness',0.20),('entertainment',0.15)],
        'health':     [('clinic',0.50),('health_med',0.50)],
    }
    BUCKET_WEIGHTS = {'essentials':0.40,'school':0.20,'retail':0.20,'health':0.20}

    out_rows = []
    for _, r in adq.iterrows():
        lat = r['lat']; lng = r['lng']
        if pd.isna(lat) or pd.isna(lng):
            out_rows.append({})
            continue
        lat_r = np.deg2rad(lat); lng_r = np.deg2rad(lng)

        row = {}
        # per-bucket sub-score
        for bucket, parts in BUCKETS.items():
            sub = 0.0
            diversity_hits = 0  # contributors with at least one place within 1km
            total_count = 0
            for tkey, w in parts:
                d = nearest_dist_m(trees.get(tkey), lat_r, lng_r)
                acc = access_score(d)
                cnt = count_within(trees.get(tkey), lat_r, lng_r, 1000.0)
                sub += w * acc
                if cnt > 0: diversity_hits += 1
                total_count += cnt
            # diversity bonus: +0.10 if 3+ distinct micro-cats represented within 1km
            if diversity_hits >= 3:
                sub = min(1.0, sub + 0.10)
            row[f'min15_{bucket}']        = round(sub * 100.0, 1)
            row[f'min15_count_{bucket}']  = total_count

        # composite
        composite = sum(BUCKET_WEIGHTS[b] * (row[f'min15_{b}']/100.0) for b in BUCKET_WEIGHTS)
        row['min15_score'] = round(composite * 100.0, 1)

        # nearest distances for tooltip
        row['min15_nearest_hawker_m'] = round(nearest_dist_m(trees['hawker'], lat_r, lng_r), 0)
        row['min15_nearest_super_m']  = round(nearest_dist_m(trees['super'],  lat_r, lng_r), 0)
        row['min15_nearest_clinic_m'] = round(nearest_dist_m(trees['clinic'], lat_r, lng_r), 0)
        row['min15_nearest_park_m']   = round(nearest_dist_m(trees['park'],   lat_r, lng_r), 0)
        row['min15_nearest_school_m'] = round(nearest_dist_m(trees['school'], lat_r, lng_r), 0)

        out_rows.append(row)

    addn = pd.DataFrame(out_rows)
    print(f'\nComputed {len(addn.columns)} new columns')
    for col in addn.columns:
        if col in adq.columns:
            adq = adq.drop(columns=[col])
    adq = pd.concat([adq.reset_index(drop=True), addn.reset_index(drop=True)], axis=1)

    # Summary
    print('\n=== 15-min score distribution ===')
    s = adq['min15_score'].dropna()
    print(f'  count: {len(s):,}')
    print(f'  mean:  {s.mean():.1f}')
    print(f'  p25:   {s.quantile(0.25):.1f}')
    print(f'  p50:   {s.quantile(0.50):.1f}')
    print(f'  p75:   {s.quantile(0.75):.1f}')
    print(f'  >=80:  {(s>=80).sum():,} ({(s>=80).mean()*100:.0f}%)')
    print(f'  <40:   {(s<40).sum():,} ({(s<40).mean()*100:.0f}%)')

    print('\n=== Top 5 best 15-min cells ===')
    top = adq.nlargest(5, 'min15_score')[['parent_subzone','min15_score','min15_essentials','min15_school','min15_retail','min15_health']]
    print(top.to_string(index=False))

    print('\n=== Bottom 5 (with residents only) ===')
    bot = adq[(adq.get('pop_total',0)>500) & (adq['min15_score'].notna())].nsmallest(5, 'min15_score')[['parent_subzone','pop_total','min15_score','min15_essentials','min15_school']]
    print(bot.to_string(index=False))

    adq.to_parquet(ADQ_PATH, index=False)
    print(f'\nWrote {ADQ_PATH}  ({len(adq.columns)} cols)')


if __name__ == '__main__':
    main()
