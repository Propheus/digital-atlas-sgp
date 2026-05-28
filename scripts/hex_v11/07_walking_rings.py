"""Step 2: Compute walking-ring station/stop counts + lines/routes per hex8.

FIXED:
  - Train stations are POLYGONS (not Points) → compute centroid
  - Bus routes from GTFS stop_times → trips → routes (stop_code matched on bus_stops_mar2026)
"""

import pandas as pd
import numpy as np
import json
import csv
import zipfile
from collections import defaultdict
from pathlib import Path
from shapely import wkt as shp_wkt
from shapely.geometry import shape

IN_PATH = Path('data/hex_v11/hex8_adequacy_features.parquet')
OUT = IN_PATH

GTFS_ZIP = Path('data/gtfs/singapore-gtfs.zip')

R = 6371000.0
def haversine_m(lat1, lng1, lat2, lng2):
    p1 = np.radians(lat1); p2 = np.radians(lat2)
    dp = p2 - p1; dl = np.radians(lng2 - lng1)
    a = np.sin(dp/2)**2 + np.cos(p1)*np.cos(p2)*np.sin(dl/2)**2
    return 2*R*np.arcsin(np.sqrt(a))

def load_train_stations():
    """Train stations are POLYGON features. Return (lat, lng, station_name, is_lrt) tuples."""
    with open('data/transit_updated/train_stations_mar2026.geojson') as f:
        gj = json.load(f)
    out = []
    for feat in gj['features']:
        props = feat.get('properties', {})
        # type from TYP_CD_DES — 'MRT' or 'LRT'
        typ = (props.get('TYP_CD_DES') or '').upper()
        is_lrt = 'LRT' in typ
        name = props.get('STN_NAM_DE') or props.get('STN_NAM') or ''
        try:
            geom = shape(feat['geometry'])
            c = geom.centroid
            out.append((c.y, c.x, name, is_lrt))
        except Exception:
            continue
    print(f'  Loaded {len(out)} train stations')
    return out

def parse_mrt_lines_from_name(name):
    """Extract MRT line code from station name prefix.
    SG stations have format like 'NS1', 'EW24', 'CC9' etc. encoded in STN_NAM_DE.
    But mar2026 station names are like 'JURONG EAST MRT STATION'."""
    # Fallback: keep set empty here; we count lines another way via station_code if present
    return set()

def build_gtfs_stop_routes():
    """Stream GTFS to build stop_code → set(route_short_name)."""
    print('Parsing GTFS for stop-route mapping…')
    with zipfile.ZipFile(GTFS_ZIP) as z:
        # 1. routes.txt → route_id → route_short_name
        route_short = {}
        with z.open('routes.txt') as fh:
            rdr = csv.DictReader((line.decode('utf-8') for line in fh))
            for row in rdr:
                route_short[row['route_id']] = row.get('route_short_name') or row['route_id']
        print(f'  routes: {len(route_short)}')

        # 2. trips.txt → trip_id → route_id
        trip_route = {}
        with z.open('trips.txt') as fh:
            rdr = csv.DictReader((line.decode('utf-8') for line in fh))
            for row in rdr:
                trip_route[row['trip_id']] = row['route_id']
        print(f'  trips: {len(trip_route)}')

        # 3. stops.txt → stop_id → stop_code (the BUS_STOP_N value)
        stop_id_to_code = {}
        stop_id_to_latlng = {}
        with z.open('stops.txt') as fh:
            rdr = csv.DictReader((line.decode('utf-8') for line in fh))
            for row in rdr:
                stop_id_to_code[row['stop_id']] = row.get('stop_code') or row['stop_id']
                try:
                    stop_id_to_latlng[row['stop_id']] = (float(row['stop_lat']), float(row['stop_lon']))
                except Exception:
                    pass
        print(f'  stops: {len(stop_id_to_code)}')

        # 4. stop_times.txt — stream
        stop_routes = defaultdict(set)
        n = 0
        with z.open('stop_times.txt') as fh:
            rdr = csv.DictReader((line.decode('utf-8') for line in fh))
            for row in rdr:
                rid = trip_route.get(row['trip_id'])
                if rid:
                    code = stop_id_to_code.get(row['stop_id'])
                    if code:
                        stop_routes[code].add(route_short.get(rid, rid))
                n += 1
                if n % 2_000_000 == 0:
                    print(f'    stop_times rows: {n:,}', flush=True)
        print(f'  total stop_times rows: {n:,}')
        print(f'  unique stops with routes: {len(stop_routes)}')
    return stop_routes

def main():
    h = pd.read_parquet(IN_PATH)
    print(f'Loaded {h.shape}')

    # === Train stations ===
    train = load_train_stations()
    mrt = [t for t in train if not t[3]]
    lrt = [t for t in train if t[3]]
    print(f'  MRT: {len(mrt)}  LRT: {len(lrt)}')

    mrt_lats = np.array([t[0] for t in mrt])
    mrt_lngs = np.array([t[1] for t in mrt])
    mrt_names = [t[2] for t in mrt]

    lrt_lats = np.array([t[0] for t in lrt])
    lrt_lngs = np.array([t[1] for t in lrt])

    # MRT line classification from station name
    # SG MRT lines and their stations have suffix codes. We infer from common name patterns.
    def mrt_line_of(name):
        n = (name or '').upper()
        if any(s in n for s in ['JURONG EAST','BUKIT BATOK','BUKIT GOMBAK','CHOA CHU KANG','YEW TEE','KRANJI','MARSILING','WOODLANDS','ADMIRALTY','SEMBAWANG','CANBERRA','YISHUN','KHATIB','YIO CHU KANG','ANG MO KIO','BISHAN','BRADDELL','TOA PAYOH','NOVENA','NEWTON','ORCHARD','SOMERSET','DHOBY GHAUT','CITY HALL','RAFFLES PLACE','MARINA BAY','MARINA SOUTH PIER']):
            return 'NS'
        if any(s in n for s in ['PASIR RIS','TAMPINES','SIMEI','TANAH MERAH','BEDOK','KEMBANGAN','EUNOS','PAYA LEBAR','ALJUNIED','KALLANG','LAVENDER','BUGIS','TANJONG PAGAR','OUTRAM PARK','TIONG BAHRU','REDHILL','QUEENSTOWN','COMMONWEALTH','BUONA VISTA','DOVER','CLEMENTI','CHINESE GARDEN','LAKESIDE','BOON LAY','PIONEER','JOO KOON','GUL CIRCLE','TUAS CRESCENT','TUAS WEST ROAD','TUAS LINK','EXPO','CHANGI AIRPORT']):
            return 'EW'
        if any(s in n for s in ['HARBOURFRONT','TELOK BLANGAH','LABRADOR PARK','PASIR PANJANG','HAW PAR VILLA','KENT RIDGE','ONE-NORTH','HOLLAND VILLAGE','FARRER ROAD','BOTANIC GARDENS','CALDECOTT','MARYMOUNT','BISHAN','LORONG CHUAN','SERANGOON','BARTLEY','TAI SENG','MACPHERSON','MOUNTBATTEN','DAKOTA','PAYA LEBAR','STADIUM','PROMENADE','NICOLL HIGHWAY','BAYFRONT']):
            return 'CC'
        if any(s in n for s in ['HARBOURFRONT','OUTRAM PARK','CHINATOWN','CLARKE QUAY','DHOBY GHAUT','LITTLE INDIA','FARRER PARK','BOON KENG','POTONG PASIR','WOODLEIGH','SERANGOON','KOVAN','HOUGANG','BUANGKOK','SENGKANG','PUNGGOL']):
            return 'NE'
        if any(s in n for s in ['BUKIT PANJANG','CASHEW','HILLVIEW','HUME','BEAUTY WORLD','KING ALBERT PARK','SIXTH AVENUE','TAN KAH KEE','BOTANIC GARDENS','STEVENS','NEWTON','LITTLE INDIA','ROCHOR','BUGIS','PROMENADE','BAYFRONT','DOWNTOWN','TELOK AYER','CHINATOWN','FORT CANNING','BENCOOLEN','JALAN BESAR','BENDEMEER','GEYLANG BAHRU','MATTAR','MACPHERSON','UBI','KAKI BUKIT','BEDOK NORTH','BEDOK RESERVOIR','TAMPINES WEST','TAMPINES','TAMPINES EAST','UPPER CHANGI','EXPO']):
            return 'DT'
        if any(s in n for s in ['WOODLANDS','SPRINGLEAF','LENTOR','MAYFLOWER','BRIGHT HILL','UPPER THOMSON','CALDECOTT','MOUNT PLEASANT','STEVENS','NAPIER','ORCHARD','ORCHARD BOULEVARD','GREAT WORLD','HAVELOCK','OUTRAM PARK','MAXWELL','SHENTON WAY','MARINA BAY','GARDENS BY THE BAY','TANJONG RHU','KATONG PARK','TANJONG KATONG','MARINE PARADE','MARINE TERRACE','SIGLAP','BAYSHORE','BEDOK SOUTH','SUNGEI BEDOK']):
            return 'TE'
        return None

    n = len(h)
    out = {
        'mrt_stations_in_500m': np.zeros(n, dtype=int),
        'mrt_stations_in_1km':  np.zeros(n, dtype=int),
        'lrt_stations_in_500m': np.zeros(n, dtype=int),
        'lrt_stations_in_1km':  np.zeros(n, dtype=int),
        'dist_to_nearest_lrt_m': np.full(n, np.nan),
        'dist_to_nearest_mrt_real_m': np.full(n, np.nan),
        'mrt_lines_count':       np.zeros(n, dtype=int),
        'bus_stops_in_400m':    np.zeros(n, dtype=int),
        'bus_stops_in_800m':    np.zeros(n, dtype=int),
        'bus_routes_count':      np.zeros(n, dtype=int),
    }

    # === Bus stops with GTFS routes ===
    stop_routes = build_gtfs_stop_routes()

    with open('data/transit_updated/bus_stops_mar2026.geojson') as f:
        bgj = json.load(f)
    bus_pts = []
    for feat in bgj['features']:
        geom = feat.get('geometry') or {}
        if geom.get('type') == 'Point':
            lng, lat = geom['coordinates']
            code = feat.get('properties', {}).get('BUS_STOP_N') or ''
            bus_pts.append((lat, lng, code))
    print(f'  Bus stops: {len(bus_pts)}')
    bus_lats = np.array([p[0] for p in bus_pts])
    bus_lngs = np.array([p[1] for p in bus_pts])
    bus_codes = [str(p[2]) for p in bus_pts]
    bus_routes_per = [stop_routes.get(c, set()) for c in bus_codes]
    matched = sum(1 for r in bus_routes_per if r)
    print(f'  Bus stops with GTFS routes match: {matched} / {len(bus_pts)} ({matched/len(bus_pts)*100:.1f}%)')

    centroids = h[['lat','lng']].to_numpy()

    for i in range(n):
        clat, clng = centroids[i]
        if len(mrt_lats) > 0:
            d_mrt = haversine_m(clat, clng, mrt_lats, mrt_lngs)
            mask500 = d_mrt <= 500
            mask1k  = d_mrt <= 1000
            out['mrt_stations_in_500m'][i] = mask500.sum()
            out['mrt_stations_in_1km'][i]  = mask1k.sum()
            out['dist_to_nearest_mrt_real_m'][i] = d_mrt.min()
            lines = set()
            for j in np.where(mask1k)[0]:
                ln = mrt_line_of(mrt_names[j])
                if ln: lines.add(ln)
            out['mrt_lines_count'][i] = len(lines)
        if len(lrt_lats) > 0:
            d_lrt = haversine_m(clat, clng, lrt_lats, lrt_lngs)
            out['lrt_stations_in_500m'][i] = (d_lrt <= 500).sum()
            out['lrt_stations_in_1km'][i]  = (d_lrt <= 1000).sum()
            out['dist_to_nearest_lrt_m'][i] = d_lrt.min()
        d_bus = haversine_m(clat, clng, bus_lats, bus_lngs)
        mask400 = d_bus <= 400
        mask800 = d_bus <= 800
        out['bus_stops_in_400m'][i] = mask400.sum()
        out['bus_stops_in_800m'][i] = mask800.sum()
        routes = set()
        for j in np.where(mask400)[0]:
            routes |= bus_routes_per[j]
        out['bus_routes_count'][i] = len(routes)

        if (i+1) % 200 == 0:
            print(f'  hex {i+1}/{n}', flush=True)

    for k, v in out.items():
        h[k] = v

    h.to_parquet(OUT, index=False)
    print(f'\nWrote {OUT}')
    for k in out:
        nonzero_mean = h.loc[h[k] > 0, k].mean() if h[k].dtype != float else h[k].mean()
        print(f'  {k}: mean={h[k].mean():.2f} max={h[k].max()}')

if __name__ == '__main__':
    main()
