"""Distribute 482,600 CMP dorm workers across hex8 cells.

Inputs:
  - data/external/mom/migrant-worker-dormitories.geocoded.jsonl  (1,783 FEDA dorms; ~1,121 with lat/lng)
  - data/buildings_overture/sgp_buildings.parquet                 (281 class=dormitory)
  - data/hex_v10/hex8_final.parquet                               (1,191 hex8 cells)

Capacity proxy per dorm:
  1. Match to Overture dormitory building within 200m → capacity = footprint_sqm * num_floors * 0.60 / 8
  2. If unmatched: assign class default (Class 4 keyword / Class 3 named / Class 1-2 site)
Top-down scale all dorms to total 482,600.
For 662 ungeocoded dorms (mostly CTQs): assign Class 1 default (38), scale to industrial-zone fallback hexes.

Output:
  data/hex_v11/hex8_dorm_pop.parquet  (hex8_id, dorm_count, raw_capacity, pop_nr_dorm)
"""

import json, re, math
import pandas as pd
import h3
from pathlib import Path
from shapely import wkt
from shapely.geometry import Point

OUT_DIR = Path('data/hex_v11')
OUT_DIR.mkdir(parents=True, exist_ok=True)

DORM_BUDGET = 482_600  # MOM Dec 2025 — CMP work permit holders
NGO_EXCLUDE_PREFIX = '90'  # DORM-90xxx are NGO/special shelters, NOT CMP
SQM_PER_BED = 8.0
DORM_OCCUPANCY = 0.60  # fraction of footprint actually used as bed space
DEFAULT_FLOORS_PBD = 7  # median from Overture dorm-class buildings

# Class default beds — from DASL H2 2024 (Class N total / Class N dorm count)
CLASS_DEFAULTS = {
    1: 38,    # 35,814 / 950
    2: 182,   # 47,779 / 263
    3: 461,   # 77,472 / 168
    4: 4635,  # 278,133 / 60
}

PBD_NAMED_KEYWORDS = ['LODGE', 'DORMITORY']  # named dorm = at minimum Class 3
PBD_LOCATION_KEYWORDS = [
    'TUAS SOUTH', 'TUAS AVENUE', 'TUAS LINK', 'TUAS COVE', 'PENJURU',
    'MANDAI ESTATE', 'JALAN PAPAN', 'JALAN TUKANG', 'TUKANG INNOVATION',
    'SUNGEI KADUT', 'WOODLANDS INDUSTRIAL', 'WOODLANDS WALK', 'KRANJI WAY',
    'SOON LEE', 'PIONEER', 'BUROH', 'JOO KOON', 'JURONG PORT',
    'CHANGI LODGE', 'TANAH MERAH COAST', 'SELETAR NORTH',
    'KIM CHUAN TERRACE', 'KAKI BUKIT AVENUE', 'UBI AVENUE',
    'TANNERY LANE', 'TANNERY ROAD', 'BENOI', 'TECH PARK CRESCENT',
]

def load_dorms():
    rows = []
    with open('data/external/mom/migrant-worker-dormitories.geocoded.jsonl') as f:
        for line in f:
            rows.append(json.loads(line))
    df = pd.DataFrame(rows)
    return df

def is_ngo(dorm_id):
    return dorm_id.startswith(f'DORM-{NGO_EXCLUDE_PREFIX}')

def infer_class(row):
    """Return DASL class (1..4) for a dorm based on text signals."""
    addr_up = str(row.get('address', '')).upper()
    name_up = str(row.get('name', '')).upper()
    op_up = str(row.get('operator', '')).upper()
    combined = f'{addr_up} {name_up} {op_up}'

    # Class 4: known PBD location or major PBD operator
    if any(kw in combined for kw in PBD_LOCATION_KEYWORDS):
        # Tuas Avenue / Soon Lee / Mandai etc.; usually large PBD or PBD-adjacent
        # But many CTQs sit on these roads too, so additional filter:
        if any(kw in name_up for kw in PBD_NAMED_KEYWORDS):
            return 4  # named lodge in PBD area
        if 'CTQ' in addr_up or 'CTQ' in name_up:
            return 1  # CTQ explicitly = construction site
        if 'TOLQ' in addr_up:
            return 1  # Temporary Occupation Licence
        # Could be Class 3-4; default to Class 3 to be conservative
        return 3
    # Class 3: named dormitory anywhere
    if any(kw in name_up for kw in PBD_NAMED_KEYWORDS) and name_up not in ('-', ''):
        return 3
    # CTQ/TOLQ in address text = site dorm (Class 1)
    if re.search(r'\b(CTQ|TOLQ|TEMPORARY)\b', addr_up):
        return 1
    # Default: small site CDC = Class 2
    return 2

def overture_dorm_index():
    """Build a list of (lat, lng, footprint_sqm, num_floors) per Overture dorm building."""
    import pandas as pd
    b = pd.read_parquet('data/buildings_overture/sgp_buildings.parquet')
    dorms = b[b['class'] == 'dormitory'].copy()
    out = []
    for _, r in dorms.iterrows():
        try:
            geom = wkt.loads(r['geom_wkt'])
            c = geom.centroid
            # Footprint area in sqm — convert from lat/lng degrees with simple equirectangular
            # 1 deg lat ≈ 110,540 m; 1 deg lng @ 1.35° ≈ 111,320 * cos(1.35°) ≈ 111,290 m
            # so deg² → sqm factor ≈ 110540 * 111290 ≈ 1.230e10
            area_sqm = geom.area * 1.230e10
            floors = float(r['num_floors']) if pd.notna(r['num_floors']) else DEFAULT_FLOORS_PBD
            out.append((c.y, c.x, area_sqm, floors, r['id']))
        except Exception:
            continue
    print(f'Loaded {len(out)} Overture dormitory buildings (with valid geom)')
    return out

def haversine(lat1, lng1, lat2, lng2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp/2)**2 + math.cos(p1) * math.cos(p2) * math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def match_overture(dorm_lat, dorm_lng, ovr_list, max_m=200):
    best = None
    bd = max_m + 1
    for (oy, ox, area, floors, oid) in ovr_list:
        d = haversine(dorm_lat, dorm_lng, oy, ox)
        if d < bd:
            bd = d
            best = (oy, ox, area, floors, oid)
    return (best, bd) if bd <= max_m else (None, None)

def capacity_from_overture(area_sqm, floors):
    """Bed capacity proxy."""
    floor_area = max(area_sqm, 200) * floors
    return floor_area * DORM_OCCUPANCY / SQM_PER_BED

def main():
    df = load_dorms()
    print(f'\nTotal FEDA dorms: {len(df)}')

    df['is_ngo'] = df['dorm_id'].apply(is_ngo)
    df = df[~df['is_ngo']].copy()
    print(f'After NGO/shelter exclusion (DORM-90xxx): {len(df)}')

    df['class'] = df.apply(infer_class, axis=1)
    print('\nClass distribution (inferred):')
    print(df['class'].value_counts().sort_index().to_string())

    ovr = overture_dorm_index()

    # Match to Overture
    matched = []
    for _, r in df.iterrows():
        if pd.isna(r.get('lat')):
            matched.append((None, None))
            continue
        m, d = match_overture(r['lat'], r['lng'], ovr)
        matched.append((m, d))
    df['ovr_match'] = [m[0] is not None if isinstance(m, tuple) else False for m in [x[0] for x in matched]]
    # The line above is messy; clean approach:
    df['ovr_area'] = [x[0][2] if x[0] else None for x in matched]
    df['ovr_floors'] = [x[0][3] if x[0] else None for x in matched]
    df['ovr_dist_m'] = [x[1] for x in matched]
    print(f'\nMOM dorms matched to Overture building (≤200m): {df["ovr_area"].notna().sum()} / {len(df)}')

    # Raw capacity per dorm
    def raw_cap(r):
        if pd.notna(r.get('ovr_area')):
            return capacity_from_overture(r['ovr_area'], r['ovr_floors'])
        return CLASS_DEFAULTS[int(r['class'])]
    df['raw_capacity'] = df.apply(raw_cap, axis=1)

    # For ungeocoded dorms, assign a centroid in their inferred planning area later;
    # for now we still keep their raw_capacity to inform totals.
    df_geo = df[df['lat'].notna()].copy()
    df_nogeo = df[df['lat'].isna()].copy()
    print(f'\nGeocoded: {len(df_geo)} | Ungeocoded: {len(df_nogeo)}')
    print(f'Raw capacity sum (all dorms): {df["raw_capacity"].sum():,.0f}')
    print(f'Raw capacity sum (geocoded only): {df_geo["raw_capacity"].sum():,.0f}')

    # Map geocoded dorms to hex8
    df_geo['hex8_id'] = df_geo.apply(lambda r: h3.latlng_to_cell(r['lat'], r['lng'], 8), axis=1)

    # Cells lookup
    hex8 = pd.read_parquet('data/hex_v10/hex8_final.parquet')[['hex8_id','parent_subzone','parent_pa','parent_region']]
    valid_hex8 = set(hex8['hex8_id'])

    df_geo['hex8_valid'] = df_geo['hex8_id'].isin(valid_hex8)
    print(f'Dorms mapped to a known hex8 cell: {df_geo["hex8_valid"].sum()} / {len(df_geo)}')

    # For ungeocoded dorms: assign to Tuas industrial fallback (postal sector 638/639/636 area cells)
    # We pick the largest existing dorm cell (most beds) and add ungeocoded capacity there proportionally.
    # Simpler: distribute ungeocoded capacity across geocoded cells weighted by existing dorm density.
    geo_cap = df_geo[df_geo['hex8_valid']].groupby('hex8_id')['raw_capacity'].sum()
    if len(df_nogeo) > 0:
        nogeo_total = df_nogeo['raw_capacity'].sum()
        print(f'\nDistributing {nogeo_total:,.0f} ungeocoded-dorm capacity across {len(geo_cap)} dorm cells')
        # Weight by sqrt(existing capacity) to avoid mega-concentration on Tuas alone
        w = geo_cap.pow(0.5)
        share = w / w.sum()
        ungeo_alloc = share * nogeo_total
        agg = (geo_cap + ungeo_alloc).reset_index()
        agg.columns = ['hex8_id', 'raw_capacity']
    else:
        agg = geo_cap.reset_index()

    # Top-down scale to DORM_BUDGET
    scale = DORM_BUDGET / agg['raw_capacity'].sum()
    agg['pop_nr_dorm'] = agg['raw_capacity'] * scale
    print(f'\nScaling factor: {scale:.4f}  (raw sum {agg["raw_capacity"].sum():,.0f} → {agg["pop_nr_dorm"].sum():,.0f})')

    # Dorm count per cell
    dc = df_geo[df_geo['hex8_valid']].groupby('hex8_id').size().rename('dorm_count').reset_index()
    out = hex8.merge(agg, on='hex8_id', how='left').merge(dc, on='hex8_id', how='left')
    out['raw_capacity'] = out['raw_capacity'].fillna(0)
    out['pop_nr_dorm'] = out['pop_nr_dorm'].fillna(0)
    out['dorm_count'] = out['dorm_count'].fillna(0).astype(int)

    out_path = OUT_DIR / 'hex8_dorm_pop.parquet'
    out.to_parquet(out_path, index=False)
    print(f'\nWrote {out_path}')
    print(f'Total dorm pop: {out["pop_nr_dorm"].sum():,.0f}  (target {DORM_BUDGET:,})')

    # Sanity: top dorm-pop cells
    print('\nTop 10 dorm-pop cells:')
    print(out.nlargest(10, 'pop_nr_dorm')[['hex8_id','parent_subzone','parent_pa','dorm_count','pop_nr_dorm']].to_string(index=False))

if __name__ == '__main__':
    main()
