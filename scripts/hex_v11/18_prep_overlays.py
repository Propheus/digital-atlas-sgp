"""Prep slimmed overlay geojsons for the React map.

Outputs to /Users/sumanth/propheus-projs/da-apps-sgp-mobility/da-apps-sgp-mobility/transport-adequacy-app/public/data/overlays/:
  mrt_lines.geojson      — rail segments tagged by RAIL_TYPE + GRND_LEVEL
  mrt_stations.geojson   — 151 MRT + 42 LRT centroid points with line_code + colour
  train_exits.geojson    — 595 exit points (stn_name + exit_code)
  bus_stops.geojson      — 5,202 stops (BusStopCode + RoadName + Description)
  covered_linkway.geojson— 7,012 sheltered walkway segments

All in WGS84 EPSG:4326 and slimmed to ~3-5 MB max.
"""

import json, sys
from pathlib import Path
import geopandas as gpd
from shapely.geometry import shape

sys.path.insert(0, str(Path(__file__).parent))
from mrt_network import LINES, normalise_station_name

OUT = Path('/Users/sumanth/propheus-projs/da-apps-sgp-mobility/da-apps-sgp-mobility/transport-adequacy-app/public/data/overlays')
OUT.mkdir(parents=True, exist_ok=True)

# Singapore MRT/LRT line colours (official LTA palette)
LINE_COLOURS = {
    'NS': '#D42E12',  # red
    'EW': '#009645',  # green
    'CG': '#009645',  # Changi Airport branch (green)
    'NE': '#9900AA',  # purple
    'CC': '#FA9E0D',  # orange
    'CE': '#FA9E0D',  # CCL extension (orange)
    'DT': '#005EC4',  # blue
    'TE': '#9D5B25',  # brown
    'JR': '#0099AA',  # cyan (future)
    'BPL': '#748477', # BP LRT (grey-green)
    'SLRT':'#748477', # Sengkang LRT
    'PLRT':'#748477', # Punggol LRT
    'LRT': '#748477', # Default LRT
}

# Build station-to-lines map (a station may be on multiple lines)
def station_to_lines():
    m = {}
    for line_code, seq in LINES.items():
        for st in seq:
            m.setdefault(st, set()).add(line_code)
    return m

def main():
    print('=== Prepping overlay geojsons ===\n')

    # 1. Rail lines — slim attrs
    print('--- mrt_lines.geojson (slimmed rail_lines) ---')
    with open('data/transit/rail_lines.geojson') as f:
        rl = json.load(f)
    out_feats = []
    for feat in rl['features']:
        p = feat['properties']
        out_feats.append({
            'type': 'Feature',
            'geometry': feat['geometry'],
            'properties': {
                'rail_type':   p.get('RAIL_TYPE'),       # MRT / LRT
                'grnd_level':  p.get('GRND_LEVEL'),      # UNDERGROUND / ABOVEGROUND
            }
        })
    out = {'type': 'FeatureCollection', 'features': out_feats}
    with (OUT / 'mrt_lines.geojson').open('w') as f:
        json.dump(out, f, separators=(',', ':'))
    sz = (OUT / 'mrt_lines.geojson').stat().st_size / 1e6
    print(f'  ✓ mrt_lines.geojson: {len(out_feats):,} segs, {sz:.1f} MB')

    # 2. Stations — convert polygons → centroids + line code
    print('\n--- mrt_stations.geojson (centroid + line) ---')
    sl = station_to_lines()
    with open('data/transit_updated/train_stations_mar2026.geojson') as f:
        sj = json.load(f)
    out_st = []
    for feat in sj['features']:
        p = feat['properties']
        raw_name = p.get('STN_NAM_DE') or p.get('STN_NAM') or ''
        if 'DEPOT' in raw_name.upper(): continue
        norm = normalise_station_name(raw_name)
        if not norm: continue
        # Compute centroid
        try:
            geom = shape(feat['geometry'])
            c = geom.centroid
        except Exception:
            continue
        typ = (p.get('TYP_CD_DES') or '').upper()
        is_lrt = 'LRT' in typ
        # Lookup line(s)
        lines = sl.get(norm, set())
        if is_lrt:
            line_codes = ['LRT']  # group all LRT
            colour = LINE_COLOURS['LRT']
        elif lines:
            line_codes = sorted(lines)
            # If multi-line (interchange), use the first; otherwise its colour
            colour = LINE_COLOURS.get(line_codes[0], '#9ca3af')
        else:
            line_codes = []
            colour = '#9ca3af'
        out_st.append({
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [c.x, c.y]},
            'properties': {
                'name':       raw_name.replace(' MRT STATION','').replace(' LRT STATION',''),
                'is_lrt':     is_lrt,
                'lines':      ','.join(line_codes),
                'colour':     colour,
                'n_lines':    len(line_codes),
            }
        })
    with (OUT / 'mrt_stations.geojson').open('w') as f:
        json.dump({'type':'FeatureCollection','features':out_st}, f, separators=(',', ':'))
    sz = (OUT / 'mrt_stations.geojson').stat().st_size / 1e6
    print(f'  ✓ mrt_stations.geojson: {len(out_st)} stations, {sz:.2f} MB')

    # 3. Train exits
    print('\n--- train_exits.geojson ---')
    with open('data/lta_datamall/2026-05/train_station_exits_mar2026.geojson') as f:
        ej = json.load(f)
    out_ex = []
    for feat in ej['features']:
        p = feat['properties']
        out_ex.append({
            'type': 'Feature',
            'geometry': feat['geometry'],
            'properties': {
                'name':      (p.get('stn_name') or '').replace(' MRT STATION','').replace(' LRT STATION',''),
                'exit':      p.get('exit_code'),
            }
        })
    with (OUT / 'train_exits.geojson').open('w') as f:
        json.dump({'type':'FeatureCollection','features':out_ex}, f, separators=(',', ':'))
    sz = (OUT / 'train_exits.geojson').stat().st_size / 1e6
    print(f'  ✓ train_exits.geojson: {len(out_ex)} exits, {sz:.2f} MB')

    # 4. Bus stops
    print('\n--- bus_stops.geojson ---')
    with open('data/transit_updated/bus_stops_mar2026.geojson') as f:
        bj = json.load(f)
    out_bs = []
    for feat in bj['features']:
        p = feat['properties']
        out_bs.append({
            'type': 'Feature',
            'geometry': feat['geometry'],
            'properties': {
                'code':  p.get('BUS_STOP_N'),
                'desc':  p.get('LOC_DESC'),
            }
        })
    with (OUT / 'bus_stops.geojson').open('w') as f:
        json.dump({'type':'FeatureCollection','features':out_bs}, f, separators=(',', ':'))
    sz = (OUT / 'bus_stops.geojson').stat().st_size / 1e6
    print(f'  ✓ bus_stops.geojson: {len(out_bs)} stops, {sz:.2f} MB')

    # 5. Covered linkway — simplify geometry slightly to slim it
    print('\n--- covered_linkway.geojson ---')
    g = gpd.read_file('data/lta_datamall/2026-05/coveredlinkway_mar2026.geojson')
    # Simplify with 1m tolerance (negligible visual loss)
    g['geometry'] = g['geometry'].to_crs('EPSG:3414').simplify(1.0).to_crs('EPSG:4326')
    # Drop attrs
    g = g[['geometry']].copy()
    g.to_file(OUT / 'covered_linkway.geojson', driver='GeoJSON')
    sz = (OUT / 'covered_linkway.geojson').stat().st_size / 1e6
    print(f'  ✓ covered_linkway.geojson: {len(g)} segs, {sz:.2f} MB')

    print('\n=== All overlays written ===')
    import os
    for f in sorted(os.listdir(OUT)):
        path = OUT / f
        if path.is_file():
            print(f'  {f:<30s}  {path.stat().st_size/1e6:>6.2f} MB')

if __name__ == '__main__':
    main()
