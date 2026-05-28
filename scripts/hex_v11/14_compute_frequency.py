"""Compute per-cell frequency adequacy (real peak-hour wait time).

Methodology:
  1. Parse bus_services.json AM_Peak_Freq "08-10" → midpoint 9 min headway per service
  2. Build stop_code → list of services via GTFS (already computed in step 7)
  3. For each hex8 cell, find bus stops within 400m
  4. Combine headways across services serving those stops:
       Effective headway = harmonic mean (because more services = shorter wait)
       Actually: if you can take ANY of k services with headways h1..hk that
       are independent and run continuously, your expected wait = 1 / Σ(1/hi).
  5. Add MRT contribution: line peak headway (published constants per line)
  6. Output: peak_wait_min — typical AM-peak wait at this cell

Bands for adequacy:
  ≤ 5 min  → excellent (0.0)
  5–10 min → good     (0.0–0.3)
  10–15    → moderate (0.3–0.6)
  15–25    → poor     (0.6–0.85)
  > 25 min → critical (0.85–1.0)
"""

import json, re, csv, zipfile
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict

HEX_PATH = Path('data/hex_v11/hex8_adequacy_features.parquet')
GTFS_ZIP = Path('data/gtfs/singapore-gtfs.zip')

# MRT line published peak headways (AM peak, minutes)
MRT_LINE_HEADWAYS = {
    'NS': 2.5, 'EW': 2.5, 'NE': 2.5, 'CC': 2.8, 'DT': 2.8,
    'TE': 3.5, 'CG': 5.0,  # Changi Airport branch
    'JR': 4.0,             # Jurong Region Line (when open)
}

R = 6371000.0
def haversine_m(lat1, lng1, lat2, lng2):
    p1 = np.radians(lat1); p2 = np.radians(lat2)
    dp = p2 - p1; dl = np.radians(lng2 - lng1)
    a = np.sin(dp/2)**2 + np.cos(p1)*np.cos(p2)*np.sin(dl/2)**2
    return 2*R*np.arcsin(np.sqrt(a))

def parse_headway(s):
    """'08-10' → 9.0 (midpoint); '-' or empty → None; '15-15' → 15.0."""
    if not s or s.strip() in ('-', ''): return None
    m = re.match(r'(\d+)\s*-\s*(\d+)', s)
    if m: return (int(m.group(1)) + int(m.group(2))) / 2.0
    m = re.match(r'(\d+)', s)
    if m: return float(m.group(1))
    return None

def build_stop_to_services():
    """Map bus stop code → list of service short numbers via GTFS."""
    print('Parsing GTFS to map stop → services…')
    stop_to_routes = defaultdict(set)
    with zipfile.ZipFile(GTFS_ZIP) as z:
        route_short = {}
        with z.open('routes.txt') as fh:
            for row in csv.DictReader((line.decode('utf-8') for line in fh)):
                route_short[row['route_id']] = row.get('route_short_name') or row['route_id']
        trip_route = {}
        with z.open('trips.txt') as fh:
            for row in csv.DictReader((line.decode('utf-8') for line in fh)):
                trip_route[row['trip_id']] = row['route_id']
        stop_code = {}
        with z.open('stops.txt') as fh:
            for row in csv.DictReader((line.decode('utf-8') for line in fh)):
                stop_code[row['stop_id']] = row.get('stop_code') or row['stop_id']
        n = 0
        with z.open('stop_times.txt') as fh:
            for row in csv.DictReader((line.decode('utf-8') for line in fh)):
                rid = trip_route.get(row['trip_id'])
                if not rid: continue
                code = stop_code.get(row['stop_id'])
                if not code: continue
                stop_to_routes[code].add(route_short.get(rid, rid))
                n += 1
                if n % 2_000_000 == 0:
                    print(f'  stop_times {n:,}', flush=True)
    print(f'  unique stops with services: {len(stop_to_routes)}')
    return stop_to_routes

def load_service_headways():
    """ServiceNo (e.g. '104') → median AM_Peak headway across both directions."""
    with open('data/lta_live/bus_services.json') as f:
        svcs = json.load(f)
    by_svc = defaultdict(list)
    for s in svcs:
        h = parse_headway(s.get('AM_Peak_Freq'))
        if h is not None:
            by_svc[str(s['ServiceNo'])].append(h)
    out = {sn: np.median(hs) for sn, hs in by_svc.items() if hs}
    print(f'Bus services with AM peak headway: {len(out)} / {len(svcs)} entries')
    return out

def main():
    h = pd.read_parquet(HEX_PATH)
    print(f'Loaded {h.shape}')

    stop_to_routes = build_stop_to_services()
    svc_headways = load_service_headways()

    # Load bus stops with codes + lat/lng
    with open('data/transit_updated/bus_stops_mar2026.geojson') as f:
        bgj = json.load(f)
    bus_pts = []
    for feat in bgj['features']:
        geom = feat.get('geometry') or {}
        if geom.get('type') == 'Point':
            lng, lat = geom['coordinates']
            code = str(feat.get('properties', {}).get('BUS_STOP_N') or '')
            bus_pts.append((lat, lng, code))
    bus_lats = np.array([p[0] for p in bus_pts])
    bus_lngs = np.array([p[1] for p in bus_pts])
    bus_codes = [p[2] for p in bus_pts]
    # Pre-compute headway-set per stop
    stop_headway_set = []
    for code in bus_codes:
        routes = stop_to_routes.get(code, set())
        # For each route, look up its headway; drop unknowns
        hs = [svc_headways.get(r) for r in routes if svc_headways.get(r) is not None]
        stop_headway_set.append([h for h in hs if h is not None])
    print(f'Bus stops with at least one headway-known service: '
          f'{sum(1 for s in stop_headway_set if s)} / {len(bus_pts)}')

    # MRT station centroids + line lookup
    # Reuse the loader from step 13
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from mrt_network import LINES, normalise_station_name
    from shapely.geometry import shape
    with open('data/transit_updated/train_stations_mar2026.geojson') as f:
        tjg = json.load(f)
    station_lines = defaultdict(set)
    for line, seq in LINES.items():
        for st in seq:
            station_lines[st].add(line)
    mrt_pts = []
    for feat in tjg['features']:
        p = feat['properties']
        if 'LRT' in (p.get('TYP_CD_DES') or '').upper(): continue
        raw = p.get('STN_NAM_DE') or ''
        name = normalise_station_name(raw)
        if not name or 'DEPOT' in raw.upper(): continue
        try:
            c = shape(feat['geometry']).centroid
            mrt_pts.append((c.y, c.x, name))
        except Exception:
            continue
    mrt_lats = np.array([p[0] for p in mrt_pts])
    mrt_lngs = np.array([p[1] for p in mrt_pts])
    mrt_names = [p[2] for p in mrt_pts]

    # Per-cell computation
    print('\nComputing per-cell peak wait time…')
    cell_lat = h['lat'].to_numpy()
    cell_lng = h['lng'].to_numpy()
    n = len(h)
    peak_wait = np.full(n, np.nan)
    bus_only_wait = np.full(n, np.nan)
    mrt_only_wait = np.full(n, np.nan)

    for i in range(n):
        # Bus stops within 400m
        d_bus = haversine_m(cell_lat[i], cell_lng[i], bus_lats, bus_lngs)
        bus_idx = np.where(d_bus <= 400)[0]
        # Collect all headways from these stops; cap each at 30 min (services beyond
        # 30 min are essentially unreliable for daily use)
        bus_hws = []
        for j in bus_idx:
            bus_hws.extend(min(hw, 30) for hw in stop_headway_set[j])
        # MRT stations within 1km
        d_mrt = haversine_m(cell_lat[i], cell_lng[i], mrt_lats, mrt_lngs)
        mrt_idx = np.where(d_mrt <= 1000)[0]
        mrt_hws = []
        for j in mrt_idx:
            for ln in station_lines.get(mrt_names[j], []):
                hw = MRT_LINE_HEADWAYS.get(ln)
                if hw: mrt_hws.append(hw)

        # Effective wait = headway of the *best frequent service* the rider
        # would actually use (most trips have ONE preferred route, not 20).
        # Use the minimum headway across nearby services, but never below
        # 1.5 min (physical platform turnaround floor). Cells with multiple
        # services with similar headways get a small bonus (10% reduction)
        # to reflect overlap benefit.
        bus_hws = [max(h, 1.5) for h in bus_hws]
        mrt_hws = [max(h, 1.5) for h in mrt_hws]
        all_hws = bus_hws + mrt_hws
        if all_hws:
            best = min(all_hws)
            # Small bonus for multiple competitive services (cap 25% reduction)
            competitive = sum(1 for h in all_hws if h <= best * 1.5)
            overlap_bonus = min(0.25, 0.05 * (competitive - 1))
            peak_wait[i] = best * (1 - overlap_bonus)
        if bus_hws: bus_only_wait[i] = min(bus_hws)
        if mrt_hws: mrt_only_wait[i] = min(mrt_hws)

        if (i+1) % 200 == 0:
            print(f'  {i+1}/{n}', flush=True)

    h['peak_wait_min']           = peak_wait
    h['peak_wait_bus_only_min']  = bus_only_wait
    h['peak_wait_mrt_only_min']  = mrt_only_wait

    # Frequency factor [0,1] — 0 = great, 1 = critical
    # Bands: ≤5=0.0, 10=0.30, 15=0.60, 25=0.85, ∞=1.0
    pw = np.where(np.isnan(peak_wait), 30.0, peak_wait)
    def to_factor(w):
        if w <= 5:  return 0.0
        if w <= 10: return 0.3 * (w - 5) / 5
        if w <= 15: return 0.3 + 0.3 * (w - 10) / 5
        if w <= 25: return 0.6 + 0.25 * (w - 15) / 10
        return min(1.0, 0.85 + 0.15 * (w - 25) / 25)
    h['frequency_adequacy_gap'] = [to_factor(w) for w in pw]

    h.to_parquet(HEX_PATH, index=False)
    print(f'\nWrote {HEX_PATH}')

    active = h[h['cell_active_flag'] == 1]
    print('\n=== FREQUENCY ADEQUACY SUMMARY (active cells) ===')
    print(f'  Mean peak_wait:       {active["peak_wait_min"].mean():.1f} min')
    print(f'  Median peak_wait:     {active["peak_wait_min"].median():.1f} min')
    print(f'  Cells with no service: {int(active["peak_wait_min"].isna().sum())}')
    print(f'  Mean frequency_gap:   {active["frequency_adequacy_gap"].mean():.3f}')

if __name__ == '__main__':
    main()
