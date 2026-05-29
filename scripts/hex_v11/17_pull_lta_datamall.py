"""Pull LTA DataMall supply-side data for the adequacy model.

What it fetches (all written to data/lta_datamall/YYYY-MM/):
  bus_stops.jsonl       — paginated BusStops (~5,200 entries)
  bus_services.jsonl    — BusServices w/ peak/offpeak headways (~3,200 service-dir rows)
  bus_routes.jsonl      — stop-by-stop sequence per service (~26,000 rows)
  taxi_stands.jsonl     — fixed taxi stand locations
  cycling_path/         — extracted CyclingPathRetrieval zip
  facilities/           — per-station lift/escalator status (queries per station code)
  geospatial/           — bulk geojsons via GeospatialWholeIsland (rail topology, etc.)

Auth: AccountKey read from ~/notes/lta-datamall-key.txt.
"""

import json, os, sys, time, zipfile, io
import urllib.request, urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

OUT_BASE = Path('data/lta_datamall/2026-05')
OUT_BASE.mkdir(parents=True, exist_ok=True)

KEY_FILE = Path('~/notes/lta-datamall-key.txt').expanduser()
API_KEY = KEY_FILE.read_text().strip()

BASE = 'https://datamall2.mytransport.sg/ltaodataservice/'

HEADERS = {
    'AccountKey': API_KEY,
    'accept': 'application/json',
}

def get_json(url, retries=3):
    """GET a URL with the API headers, return parsed JSON. Retries on transient errors."""
    req = urllib.request.Request(url, headers=HEADERS)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read())
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(0.5 + attempt)
            else:
                raise e

def paginate(endpoint, page_size=500, max_pages=200):
    """Pull a paginated LTA endpoint via $skip. Yields rows one at a time."""
    page = 0
    while page < max_pages:
        url = f'{BASE}{endpoint}?$skip={page * page_size}'
        data = get_json(url)
        rows = data.get('value', [])
        if not rows: break
        for r in rows: yield r
        if len(rows) < page_size: break
        page += 1

def pull_to_jsonl(endpoint, out_name):
    out = OUT_BASE / out_name
    n = 0
    with out.open('w') as f:
        for row in paginate(endpoint):
            f.write(json.dumps(row) + '\n')
            n += 1
            if n % 1000 == 0:
                print(f'  {endpoint}: {n} rows', flush=True)
    print(f'  ✓ {endpoint} → {out} ({n:,} rows)')
    return n

def fetch_link_zip(endpoint, out_dir):
    """Endpoints like CyclingPathRetrieval return {'value': [{'Link': '<zip url>'}]}."""
    out_dir.mkdir(parents=True, exist_ok=True)
    # Most retrieval endpoints want a Date param like YYYYMM
    from datetime import date
    today = date.today()
    yyyymm = today.strftime('%Y%m')
    # Try previous month first (more likely to be released)
    for ym in [today.replace(day=1) - __import__('datetime').timedelta(days=20), today]:
        ym_str = ym.strftime('%Y%m') if hasattr(ym, 'strftime') else yyyymm
        url = f'{BASE}{endpoint}?Date={ym_str}'
        try:
            data = get_json(url)
            link = data.get('value', [{}])[0].get('Link') if data.get('value') else None
            if not link: continue
            print(f'  {endpoint} ({ym_str}) → {link[:80]}…')
            with urllib.request.urlopen(link, timeout=60) as r:
                blob = r.read()
            try:
                with zipfile.ZipFile(io.BytesIO(blob)) as z:
                    z.extractall(out_dir)
                    members = z.namelist()
                print(f'  ✓ {endpoint} extracted {len(members)} files to {out_dir}')
            except zipfile.BadZipFile:
                # Maybe it's a raw geojson/shapefile, not a zip
                with (out_dir / f'{endpoint}.bin').open('wb') as f:
                    f.write(blob)
                print(f'  ✓ {endpoint} saved raw blob to {out_dir}')
            return True
        except Exception as e:
            print(f'  ⚠ {endpoint} ({ym_str}): {e}')
    return False

def fetch_geospatial_layer(layer_id, out_dir):
    """GeospatialWholeIsland exposes a curated set of bulk layers."""
    out_dir.mkdir(parents=True, exist_ok=True)
    url = f'{BASE}GeospatialWholeIsland?ID={layer_id}'
    try:
        data = get_json(url)
        link = data.get('value', [{}])[0].get('Link') if data.get('value') else None
        if not link:
            print(f'  ⚠ GeospatialWholeIsland({layer_id}): no link in response')
            return False
        print(f'  GeospatialWholeIsland({layer_id}) → {link[:80]}…')
        with urllib.request.urlopen(link, timeout=60) as r:
            blob = r.read()
        try:
            with zipfile.ZipFile(io.BytesIO(blob)) as z:
                target = out_dir / layer_id
                target.mkdir(exist_ok=True)
                z.extractall(target)
                print(f'  ✓ {layer_id}: {len(z.namelist())} files extracted')
        except zipfile.BadZipFile:
            with (out_dir / f'{layer_id}.bin').open('wb') as f:
                f.write(blob)
            print(f'  ✓ {layer_id}: saved raw blob')
        return True
    except Exception as e:
        print(f'  ⚠ GeospatialWholeIsland({layer_id}): {e}')
        return False

def fetch_facilities_for_stations(station_codes, out_dir):
    """FacilitiesMaintenance returns a Link to a zipped Excel/JSON per station code.
    We sample a representative set (60 stations covering all lines) rather than
    hammer all 200+ stations on first pull."""
    out_dir.mkdir(parents=True, exist_ok=True)
    def fetch_one(code):
        url = f'{BASE}FacilitiesMaintenance?StationCode={code}'
        try:
            data = get_json(url)
            link = data.get('value', [{}])[0].get('Link') if data.get('value') else None
            if not link: return code, 'no_link'
            with urllib.request.urlopen(link, timeout=30) as r:
                blob = r.read()
            target = out_dir / f'{code}.bin'
            with target.open('wb') as f: f.write(blob)
            return code, 'ok'
        except Exception as e:
            return code, f'err:{e}'
    results = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(fetch_one, c): c for c in station_codes}
        for fut in as_completed(futs):
            code, status = fut.result()
            results[code] = status
    ok = sum(1 for v in results.values() if v == 'ok')
    print(f'  ✓ FacilitiesMaintenance: {ok}/{len(station_codes)} stations fetched')
    return results

def fetch_platform_crowd_forecast(out_dir):
    """PlatformCrowdDensityForecast returns ~1 week of hourly forecasts per line."""
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = ['CCL','CEL','CGL','DTL','EWL','NEL','NSL','BPL','SLRT','PLRT','TEL']
    for line in lines:
        url = f'{BASE}PCDForecast?TrainLine={line}'
        try:
            data = get_json(url)
            stations = data.get('value', [])
            (out_dir / f'{line}.json').write_text(json.dumps(data, indent=2))
            n_stations = len(stations[0].get('Stations', [])) if stations else 0
            print(f'  ✓ {line}: {n_stations} stations forecast')
        except Exception as e:
            print(f'  ⚠ {line}: {e}')

def main():
    print('=== LTA DataMall pull ===')
    print(f'Out: {OUT_BASE}\n')

    # 1. Bus stops (paginated)
    print('--- BusStops ---')
    pull_to_jsonl('BusStops', 'bus_stops.jsonl')

    # 2. Bus services (paginated)
    print('\n--- BusServices ---')
    pull_to_jsonl('BusServices', 'bus_services.jsonl')

    # 3. Bus routes (paginated, large)
    print('\n--- BusRoutes ---')
    pull_to_jsonl('BusRoutes', 'bus_routes.jsonl')

    # 4. Taxi stands
    print('\n--- TaxiStands ---')
    try:
        pull_to_jsonl('TaxiStands', 'taxi_stands.jsonl')
    except Exception as e:
        print(f'  ⚠ TaxiStands: {e}')

    # 5. Geospatial WholeIsland — rail topology, bus stops, etc.
    print('\n--- GeospatialWholeIsland ---')
    for layer in ['TrainStation','TrainStationExit','MRTLRTLine','BusStopLocation',
                  'PedestrianOverheadBridge','CoveredLinkway','SilverZone','SchoolZone']:
        fetch_geospatial_layer(layer, OUT_BASE / 'geospatial')

    # 6. Cycling path
    print('\n--- CyclingPathRetrieval ---')
    fetch_link_zip('CyclingPathRetrieval', OUT_BASE / 'cycling_path')

    # 7. Facilities maintenance — sample 60 stations across all lines
    print('\n--- FacilitiesMaintenance (sample) ---')
    sample_codes = (
        # NSL spread
        ['NS1','NS5','NS10','NS15','NS17','NS22','NS24','NS26','NS28'] +
        # EWL spread
        ['EW1','EW5','EW13','EW16','EW21','EW24','EW27','EW33'] +
        # NEL
        ['NE1','NE7','NE12','NE16','NE17'] +
        # CCL
        ['CC1','CC9','CC15','CC22','CC29','CE1'] +
        # DTL
        ['DT1','DT9','DT14','DT19','DT26','DT32','DT35'] +
        # TEL
        ['TE1','TE3','TE9','TE13','TE17','TE20','TE25'] +
        # CGL
        ['CG1','CG2']
    )
    fetch_facilities_for_stations(sample_codes, OUT_BASE / 'facilities')

    # 8. Platform crowd density forecast (per line)
    print('\n--- PlatformCrowdDensityForecast ---')
    fetch_platform_crowd_forecast(OUT_BASE / 'crowd_forecast')

    print(f'\n✓ All pulls complete → {OUT_BASE}')

if __name__ == '__main__':
    main()
