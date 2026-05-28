"""Compute MRT crowding (peak load factor) + resilience (distinct lines to CBD).

CROWDING:
  Use LTA transport_node_train_202601 to get AM peak (7-9am) station boardings.
  Match to MRT stations by code, project onto hex8 cells via nearest station.
  Bands:
    < 25K AM peak  → comfortable    (0.0)
    25-50K          → moderate       (0.0-0.40)
    50-100K         → crowded        (0.40-0.75)
   100-200K         → very crowded   (0.75-0.90)
    > 200K          → severe         (0.90-1.0)

RESILIENCE:
  For each cell, count distinct MRT lines that give an INDEPENDENT path to CBD
  (Raffles Place or Marina Bay). 1 line = vulnerable to single-line disruption.
  Bands:
    3+ lines = excellent (0.0)
    2 lines = good (0.2)
    1 line = poor (0.6)
    0 lines (>45 min walk to any station) = critical (1.0)
"""

import json
import numpy as np
import pandas as pd
import pandas as pd
from pathlib import Path
from collections import defaultdict
import sys

sys.path.insert(0, str(Path(__file__).parent))
from mrt_network import LINES, normalise_station_name, build_graph

HEX_PATH = Path('data/hex_v11/hex8_adequacy_features.parquet')

# Explicit LTA station-code → canonical station name mapping.
# SG MRT codes have gaps (NS6, NS28, NE18) and EWL is numbered opposite to my
# graph direction. So we hardcode the full mapping rather than derive from line
# sequences.
PT_CODE_TO_STATION = {
    # NSL (Jurong East → Marina South Pier) — note: NS6 is unused (planned Sungei Kadut)
    'NS1':'JURONG EAST','NS2':'BUKIT BATOK','NS3':'BUKIT GOMBAK','NS4':'CHOA CHU KANG','NS5':'YEW TEE',
    'NS7':'KRANJI','NS8':'MARSILING','NS9':'WOODLANDS','NS10':'ADMIRALTY','NS11':'SEMBAWANG',
    'NS12':'CANBERRA','NS13':'YISHUN','NS14':'KHATIB','NS15':'YIO CHU KANG','NS16':'ANG MO KIO',
    'NS17':'BISHAN','NS18':'BRADDELL','NS19':'TOA PAYOH','NS20':'NOVENA','NS21':'NEWTON',
    'NS22':'ORCHARD','NS23':'SOMERSET','NS24':'DHOBY GHAUT','NS25':'CITY HALL','NS26':'RAFFLES PLACE',
    'NS27':'MARINA BAY','NS28':'MARINA SOUTH PIER',
    # EWL (Pasir Ris → Tuas Link)
    'EW1':'PASIR RIS','EW2':'TAMPINES','EW3':'SIMEI','EW4':'TANAH MERAH','EW5':'BEDOK',
    'EW6':'KEMBANGAN','EW7':'EUNOS','EW8':'PAYA LEBAR','EW9':'ALJUNIED','EW10':'KALLANG',
    'EW11':'LAVENDER','EW12':'BUGIS','EW13':'CITY HALL','EW14':'RAFFLES PLACE','EW15':'TANJONG PAGAR',
    'EW16':'OUTRAM PARK','EW17':'TIONG BAHRU','EW18':'REDHILL','EW19':'QUEENSTOWN','EW20':'COMMONWEALTH',
    'EW21':'BUONA VISTA','EW22':'DOVER','EW23':'CLEMENTI','EW24':'JURONG EAST','EW25':'CHINESE GARDEN',
    'EW26':'LAKESIDE','EW27':'BOON LAY','EW28':'PIONEER','EW29':'JOO KOON','EW30':'GUL CIRCLE',
    'EW31':'TUAS CRESCENT','EW32':'TUAS WEST ROAD','EW33':'TUAS LINK',
    # CG (Changi Airport branch, off Tanah Merah)
    'CG1':'EXPO','CG2':'CHANGI AIRPORT',
    # NEL — note NE2 unused, NE18 unused historically
    'NE1':'HARBOURFRONT','NE3':'OUTRAM PARK','NE4':'CHINATOWN','NE5':'CLARKE QUAY','NE6':'DHOBY GHAUT',
    'NE7':'LITTLE INDIA','NE8':'FARRER PARK','NE9':'BOON KENG','NE10':'POTONG PASIR','NE11':'WOODLEIGH',
    'NE12':'SERANGOON','NE13':'KOVAN','NE14':'HOUGANG','NE15':'BUANGKOK','NE16':'SENGKANG','NE17':'PUNGGOL',
    'NE18':'PUNGGOL COAST',
    # CCL — Dhoby Ghaut to HarbourFront
    'CC1':'DHOBY GHAUT','CC2':'BRAS BASAH','CC3':'ESPLANADE','CC4':'PROMENADE','CC5':'NICOLL HIGHWAY',
    'CC6':'STADIUM','CC7':'MOUNTBATTEN','CC8':'DAKOTA','CC9':'PAYA LEBAR','CC10':'MACPHERSON',
    'CC11':'TAI SENG','CC12':'BARTLEY','CC13':'SERANGOON','CC14':'LORONG CHUAN','CC15':'BISHAN',
    'CC16':'MARYMOUNT','CC17':'CALDECOTT','CC19':'BOTANIC GARDENS','CC20':'FARRER ROAD',
    'CC21':'HOLLAND VILLAGE','CC22':'BUONA VISTA','CC23':'ONE-NORTH','CC24':'KENT RIDGE',
    'CC25':'HAW PAR VILLA','CC26':'PASIR PANJANG','CC27':'LABRADOR PARK','CC28':'TELOK BLANGAH',
    'CC29':'HARBOURFRONT',
    # CE (Circle Line extension)
    'CE1':'BAYFRONT','CE2':'MARINA BAY',
    # DTL
    'DT1':'BUKIT PANJANG','DT2':'CASHEW','DT3':'HILLVIEW','DT4':'HUME','DT5':'BEAUTY WORLD',
    'DT6':'KING ALBERT PARK','DT7':'SIXTH AVENUE','DT8':'TAN KAH KEE','DT9':'BOTANIC GARDENS',
    'DT10':'STEVENS','DT11':'NEWTON','DT12':'LITTLE INDIA','DT13':'ROCHOR','DT14':'BUGIS',
    'DT15':'PROMENADE','DT16':'BAYFRONT','DT17':'DOWNTOWN','DT18':'TELOK AYER','DT19':'CHINATOWN',
    'DT20':'FORT CANNING','DT21':'BENCOOLEN','DT22':'JALAN BESAR','DT23':'BENDEMEER','DT24':'GEYLANG BAHRU',
    'DT25':'MATTAR','DT26':'MACPHERSON','DT27':'UBI','DT28':'KAKI BUKIT','DT29':'BEDOK NORTH',
    'DT30':'BEDOK RESERVOIR','DT31':'TAMPINES WEST','DT32':'TAMPINES','DT33':'TAMPINES EAST',
    'DT34':'UPPER CHANGI','DT35':'EXPO',
    # TEL
    'TE1':'WOODLANDS NORTH','TE2':'WOODLANDS','TE3':'WOODLANDS SOUTH','TE4':'SPRINGLEAF','TE5':'LENTOR',
    'TE6':'MAYFLOWER','TE7':'BRIGHT HILL','TE8':'UPPER THOMSON','TE9':'CALDECOTT','TE10':'MOUNT PLEASANT',
    'TE11':'STEVENS','TE12':'NAPIER','TE13':'ORCHARD','TE14':'ORCHARD BOULEVARD','TE15':'GREAT WORLD',
    'TE16':'HAVELOCK','TE17':'OUTRAM PARK','TE18':'MAXWELL','TE19':'SHENTON WAY','TE20':'MARINA BAY',
    'TE21':'GARDENS BY THE BAY','TE22':'TANJONG RHU','TE23':'KATONG PARK','TE24':'TANJONG KATONG',
    'TE25':'MARINE PARADE','TE26':'MARINE TERRACE','TE27':'SIGLAP','TE28':'BAYSHORE',
    # JRL (future, partial codes)
    'JS1':'CHOA CHU KANG','JS2':'CHOA CHU KANG WEST','JS3':'TENGAH','JS4':'HONG KAH','JS5':'CORPORATION',
    'JS6':'JURONG WEST','JS7':'BAHAR JUNCTION','JS8':'BOON LAY',
    # Special LRT-related codes (LTA tap data may include these)
    'STC':'SENGKANG','PTC':'PUNGGOL','BP6':'BUKIT PANJANG',
}

def _stub():
    pass

def split_combined_code(code):
    """'NS9/TE2' → ['NS9', 'TE2']. 'NE12/CC13' → ['NE12', 'CC13']."""
    return [p.strip() for p in str(code).split('/') if p.strip()]

R = 6371000.0
def haversine_m(lat1, lng1, lat2, lng2):
    p1 = np.radians(lat1); p2 = np.radians(lat2)
    dp = p2 - p1; dl = np.radians(lng2 - lng1)
    a = np.sin(dp/2)**2 + np.cos(p1)*np.cos(p2)*np.sin(dl/2)**2
    return 2*R*np.arcsin(np.sqrt(a))

def load_station_centroids():
    from shapely.geometry import shape
    with open('data/transit_updated/train_stations_mar2026.geojson') as f:
        g = json.load(f)
    out = {}
    for feat in g['features']:
        p = feat['properties']
        if 'LRT' in (p.get('TYP_CD_DES') or '').upper(): continue
        raw = p.get('STN_NAM_DE') or ''
        name = normalise_station_name(raw)
        if not name or 'DEPOT' in raw.upper(): continue
        try:
            c = shape(feat['geometry']).centroid
            if name not in out: out[name] = (c.y, c.x)
        except Exception:
            continue
    return out

def main():
    h = pd.read_parquet(HEX_PATH)
    print(f'Loaded {h.shape}')

    # === STAGE 1: STATION-LEVEL AM PEAK TAPS ===
    print('\n=== Reading LTA AM peak tap volumes ===')
    df = pd.read_csv('data/lta_live/transport_node_train_202601.csv')
    weekday_peak = df[(df['DAY_TYPE'] == 'WEEKDAY') & (df['TIME_PER_HOUR'].isin([7, 8, 9]))]
    station_peak = weekday_peak.groupby('PT_CODE').agg(
        am_peak_boardings=('TOTAL_TAP_IN_VOLUME', 'sum'),
        am_peak_alightings=('TOTAL_TAP_OUT_VOLUME', 'sum'),
    ).reset_index()
    # Map PT_CODE → station name
    name_to_taps = defaultdict(float)
    name_to_alight = defaultdict(float)
    matched = 0
    unmatched = []
    for _, r in station_peak.iterrows():
        pt_code = str(r['PT_CODE'])
        for part in split_combined_code(pt_code):
            st = PT_CODE_TO_STATION.get(part)
            if st:
                name_to_taps[st] = max(name_to_taps[st], float(r['am_peak_boardings']))
                name_to_alight[st] = max(name_to_alight[st], float(r['am_peak_alightings']))
                matched += 1
                break
        else:
            unmatched.append(pt_code)
    print(f'Mapped {matched} PT_CODEs to stations; unmatched: {len(unmatched)} (samples: {unmatched[:5]})')
    print(f'Top 10 busiest stations by AM peak boardings:')
    top = sorted(name_to_taps.items(), key=lambda x: -x[1])[:10]
    for st, taps in top:
        print(f'  {st:>25s}  {taps:>10,.0f}')

    # === STAGE 2: STATION CENTROIDS ===
    centroids = load_station_centroids()

    # For each cell: find nearest MRT station, look up that station's AM peak taps
    print('\n=== Projecting crowding onto hex8 cells ===')
    station_names = sorted(centroids.keys())
    st_lats = np.array([centroids[s][0] for s in station_names])
    st_lngs = np.array([centroids[s][1] for s in station_names])
    n = len(h)
    cell_lat = h['lat'].to_numpy()
    cell_lng = h['lng'].to_numpy()

    cell_st_name = np.empty(n, dtype=object)
    cell_st_dist = np.full(n, np.nan)
    cell_peak_taps = np.zeros(n)
    cell_load_factor = np.zeros(n)

    for i in range(n):
        dists = haversine_m(cell_lat[i], cell_lng[i], st_lats, st_lngs)
        j = int(np.argmin(dists))
        cell_st_name[i] = station_names[j]
        cell_st_dist[i] = float(dists[j])
        taps = name_to_taps.get(station_names[j], 0.0)
        cell_peak_taps[i] = taps
        # Load factor: 0 (comfortable) to 1 (severe)
        if taps < 25000:
            cell_load_factor[i] = 0.0
        elif taps < 50000:
            cell_load_factor[i] = 0.40 * (taps - 25000) / 25000
        elif taps < 100000:
            cell_load_factor[i] = 0.40 + 0.35 * (taps - 50000) / 50000
        elif taps < 200000:
            cell_load_factor[i] = 0.75 + 0.15 * (taps - 100000) / 100000
        else:
            cell_load_factor[i] = min(1.0, 0.90 + 0.10 * (taps - 200000) / 200000)
        # Only count if station is reachable (within 1.5km)
        if cell_st_dist[i] > 1500:
            cell_load_factor[i] = 0.0  # Can't be crowded if you can't reach it

    h['nearest_mrt_st_peak_taps'] = cell_peak_taps
    h['crowding_load_factor'] = cell_load_factor
    h['crowding_adequacy_gap'] = cell_load_factor  # 0=comfortable, 1=severe

    # === STAGE 3: RESILIENCE (distinct lines to CBD) ===
    print('\n=== Computing resilience (distinct lines to CBD) ===')
    # For each station, which lines stop here?
    station_lines = defaultdict(set)
    for line, seq in LINES.items():
        for st in seq:
            station_lines[st].add(line)
    # CBD-serving lines: all lines that pass through CBD core (Raffles Place,
    # City Hall, Marina Bay, Downtown, Tanjong Pagar, Bugis, Chinatown, Outram Park,
    # Bayfront, Maxwell, Shenton Way, Telok Ayer, Bras Basah, Esplanade, Promenade,
    # Dhoby Ghaut, Clarke Quay).
    cbd_core_stations = [
        'RAFFLES PLACE','CITY HALL','MARINA BAY','DOWNTOWN','TANJONG PAGAR','BUGIS',
        'CHINATOWN','OUTRAM PARK','BAYFRONT','MAXWELL','SHENTON WAY','TELOK AYER',
        'BRAS BASAH','ESPLANADE','PROMENADE','DHOBY GHAUT','CLARKE QUAY',
        'MARINA SOUTH PIER','GARDENS BY THE BAY',
    ]
    cbd_lines = set()
    for cbd_station in cbd_core_stations:
        cbd_lines.update(station_lines.get(cbd_station, set()))
    print(f'  CBD-serving lines: {sorted(cbd_lines)}')

    # For each cell, find ALL stations within 1km (not just the nearest) and
    # collect distinct CBD-serving lines reachable from them. This captures
    # cells that are between two stations on different lines, or near
    # interchanges.
    cell_resilience = np.zeros(n)
    cell_n_lines_to_cbd = np.zeros(n, dtype=int)
    cell_n_stations_walking = np.zeros(n, dtype=int)
    for i in range(n):
        if cell_st_dist[i] > 1500:
            cell_resilience[i] = 1.0
            continue
        dists = haversine_m(cell_lat[i], cell_lng[i], st_lats, st_lngs)
        # All stations within 1km walking
        walk_idx = np.where(dists <= 1000)[0]
        cell_n_stations_walking[i] = len(walk_idx)
        # Distinct CBD-serving lines reachable from any walkable station
        my_cbd_lines = set()
        for j in walk_idx:
            stj = station_names[j]
            my_cbd_lines.update(station_lines.get(stj, set()) & cbd_lines)
        n_lines = len(my_cbd_lines)
        cell_n_lines_to_cbd[i] = n_lines
        # Resilience bands: 3+ excellent, 2 good, 1 moderate, 0 (need interchange) poor
        if n_lines >= 3:   cell_resilience[i] = 0.0
        elif n_lines == 2: cell_resilience[i] = 0.20
        elif n_lines == 1: cell_resilience[i] = 0.55
        else:              cell_resilience[i] = 0.80  # near a station but not CBD-direct
    h['n_lines_to_cbd']            = cell_n_lines_to_cbd
    h['n_stations_walking']        = cell_n_stations_walking
    h['resilience_adequacy_gap']   = cell_resilience

    h.to_parquet(HEX_PATH, index=False)
    print(f'Wrote {HEX_PATH}')

    active = h[h['cell_active_flag'] == 1]
    print('\n=== CROWDING + RESILIENCE SUMMARY ===')
    print(f'  Mean crowding gap:    {active["crowding_adequacy_gap"].mean():.3f}')
    print(f'  Median crowding gap:  {active["crowding_adequacy_gap"].median():.3f}')
    print(f'  Cells crowded (>0.5): {int((active["crowding_adequacy_gap"] > 0.5).sum())}')
    print(f'  Mean resilience gap:  {active["resilience_adequacy_gap"].mean():.3f}')
    print(f'  Median resilience gap: {active["resilience_adequacy_gap"].median():.3f}')
    # Lines to CBD distribution
    print(f'  Lines to CBD distribution:')
    print(active['n_lines_to_cbd'].value_counts().sort_index().to_string())

if __name__ == '__main__':
    main()
