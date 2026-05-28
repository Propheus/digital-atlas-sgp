"""Singapore MRT network topology (as of 2026).

Hard-coded line → ordered station sequence. Used to build a graph for
journey-time BFS (reach factor) and distinct-path counting (resilience).

Travel times follow LTA published norms:
  - Inter-station: 2.5 min (3 min for outer/widely-spaced suburban stations)
  - Interchange (walking between platforms): 4 min average
  - Walk-to-station from outside: handled separately via cell-level
    dist_nearest_mrt_m
"""

# Each line: list of station names IN ORDER (start → end).
# Names match `STN_NAM_DE` in train_stations_mar2026.geojson — UPPERCASE,
# usually with " MRT STATION" suffix. We normalise on load.
LINES = {
    # === North-South Line (red) — JE → MSP ===
    'NS': [
        'JURONG EAST', 'BUKIT BATOK', 'BUKIT GOMBAK', 'CHOA CHU KANG',
        'YEW TEE', 'KRANJI', 'MARSILING', 'WOODLANDS', 'ADMIRALTY',
        'SEMBAWANG', 'CANBERRA', 'YISHUN', 'KHATIB', 'YIO CHU KANG',
        'ANG MO KIO', 'BISHAN', 'BRADDELL', 'TOA PAYOH', 'NOVENA',
        'NEWTON', 'ORCHARD', 'SOMERSET', 'DHOBY GHAUT', 'CITY HALL',
        'RAFFLES PLACE', 'MARINA BAY', 'MARINA SOUTH PIER',
    ],
    # === East-West Line (green) — Tuas Link → Pasir Ris ===
    'EW': [
        'TUAS LINK', 'TUAS WEST ROAD', 'TUAS CRESCENT', 'GUL CIRCLE',
        'JOO KOON', 'PIONEER', 'BOON LAY', 'LAKESIDE', 'CHINESE GARDEN',
        'JURONG EAST', 'CLEMENTI', 'DOVER', 'BUONA VISTA',
        'COMMONWEALTH', 'QUEENSTOWN', 'REDHILL', 'TIONG BAHRU', 'OUTRAM PARK',
        'TANJONG PAGAR', 'RAFFLES PLACE', 'CITY HALL', 'BUGIS',
        'LAVENDER', 'KALLANG', 'ALJUNIED', 'PAYA LEBAR', 'EUNOS',
        'KEMBANGAN', 'BEDOK', 'TANAH MERAH', 'SIMEI', 'TAMPINES',
        'PASIR RIS',
    ],
    # === Changi Airport branch (green) — branches off Tanah Merah ===
    'CG': [
        'TANAH MERAH', 'EXPO', 'CHANGI AIRPORT',
    ],
    # === North-East Line (purple) — HarbourFront → Punggol Coast ===
    'NE': [
        'HARBOURFRONT', 'OUTRAM PARK', 'CHINATOWN', 'CLARKE QUAY',
        'DHOBY GHAUT', 'LITTLE INDIA', 'FARRER PARK', 'BOON KENG',
        'POTONG PASIR', 'WOODLEIGH', 'SERANGOON', 'KOVAN', 'HOUGANG',
        'BUANGKOK', 'SENGKANG', 'PUNGGOL', 'PUNGGOL COAST',
    ],
    # === Circle Line (yellow) — Dhoby Ghaut → HarbourFront via Buona Vista ===
    # Note: CC actually loops via stage 6 reopening; included in order.
    'CC': [
        'DHOBY GHAUT', 'BRAS BASAH', 'ESPLANADE', 'PROMENADE', 'NICOLL HIGHWAY',
        'STADIUM', 'MOUNTBATTEN', 'DAKOTA', 'PAYA LEBAR', 'MACPHERSON',
        'TAI SENG', 'BARTLEY', 'SERANGOON', 'LORONG CHUAN', 'BISHAN',
        'MARYMOUNT', 'CALDECOTT', 'BOTANIC GARDENS', 'FARRER ROAD',
        'HOLLAND VILLAGE', 'BUONA VISTA', 'ONE-NORTH', 'KENT RIDGE',
        'HAW PAR VILLA', 'PASIR PANJANG', 'LABRADOR PARK', 'TELOK BLANGAH',
        'HARBOURFRONT',
    ],
    # === Downtown Line (blue) — Bukit Panjang → Expo ===
    'DT': [
        'BUKIT PANJANG', 'CASHEW', 'HILLVIEW', 'HUME', 'BEAUTY WORLD',
        'KING ALBERT PARK', 'SIXTH AVENUE', 'TAN KAH KEE', 'BOTANIC GARDENS',
        'STEVENS', 'NEWTON', 'LITTLE INDIA', 'ROCHOR', 'BUGIS', 'PROMENADE',
        'BAYFRONT', 'DOWNTOWN', 'TELOK AYER', 'CHINATOWN', 'FORT CANNING',
        'BENCOOLEN', 'JALAN BESAR', 'BENDEMEER', 'GEYLANG BAHRU', 'MATTAR',
        'MACPHERSON', 'UBI', 'KAKI BUKIT', 'BEDOK NORTH', 'BEDOK RESERVOIR',
        'TAMPINES WEST', 'TAMPINES', 'TAMPINES EAST', 'UPPER CHANGI', 'EXPO',
    ],
    # === Thomson-East Coast Line (brown) — Woodlands North → Bayshore ===
    'TE': [
        'WOODLANDS NORTH', 'WOODLANDS', 'WOODLANDS SOUTH', 'SPRINGLEAF',
        'LENTOR', 'MAYFLOWER', 'BRIGHT HILL', 'UPPER THOMSON', 'CALDECOTT',
        'MOUNT PLEASANT', 'STEVENS', 'NAPIER', 'ORCHARD', 'ORCHARD BOULEVARD',
        'GREAT WORLD', 'HAVELOCK', 'OUTRAM PARK', 'MAXWELL', 'SHENTON WAY',
        'MARINA BAY', 'GARDENS BY THE BAY', 'TANJONG RHU', 'KATONG PARK',
        'TANJONG KATONG', 'MARINE PARADE', 'MARINE TERRACE', 'SIGLAP',
        'BAYSHORE',
    ],
    # === Jurong Region Line (light blue) — phased; stations open from 2027 ===
    # Phase 1: Choa Chu Kang ↔ Boon Lay
    'JR': [
        'CHOA CHU KANG', 'CHOA CHU KANG WEST', 'TENGAH', 'HONG KAH', 'CORPORATION',
        'JURONG WEST', 'BAHAR JUNCTION', 'BOON LAY', 'GEK POH', 'TAWAS',
        'NANYANG GATEWAY', 'NANYANG CRESCENT', 'PENG KANG HILL',
    ],
}

# Coordinates of named anchor destinations (used for journey-time targets).
# These are the canonical destinations residents commute to.
DESTINATIONS = {
    # CBD
    'Raffles Place':           {'station': 'RAFFLES PLACE',  'category': 'cbd'},
    'Marina Bay':              {'station': 'MARINA BAY',     'category': 'cbd'},
    # Major retail / mixed-use
    'Orchard':                 {'station': 'ORCHARD',        'category': 'retail'},
    # Regional employment hubs
    'Jurong East (JLD)':       {'station': 'JURONG EAST',    'category': 'regional_hub'},
    'Tampines Regional':       {'station': 'TAMPINES',       'category': 'regional_hub'},
    'Changi Business Park':    {'station': 'EXPO',           'category': 'regional_hub'},
    'One-North':               {'station': 'ONE-NORTH',      'category': 'regional_hub'},
    'Paya Lebar':              {'station': 'PAYA LEBAR',     'category': 'regional_hub'},
    # Healthcare hubs (nearest MRT)
    'SGH (Outram)':            {'station': 'OUTRAM PARK',    'category': 'healthcare'},
    'NUH (Kent Ridge)':        {'station': 'KENT RIDGE',     'category': 'healthcare'},
    'KKH (Little India)':      {'station': 'LITTLE INDIA',   'category': 'healthcare'},
    'TTSH (Novena)':           {'station': 'NOVENA',         'category': 'healthcare'},
    'CGH (Expo)':              {'station': 'EXPO',           'category': 'healthcare'},
    # Education clusters
    'NUS (Kent Ridge)':        {'station': 'KENT RIDGE',     'category': 'education'},
    'NTU (Boon Lay/Pioneer)':  {'station': 'PIONEER',        'category': 'education'},
    'SMU (Bras Basah)':        {'station': 'BRAS BASAH',     'category': 'education'},
    'SUTD (Upper Changi)':     {'station': 'UPPER CHANGI',   'category': 'education'},
}

INTER_STATION_MIN = 2.5    # MRT typical inter-station travel
INTERCHANGE_MIN   = 4.0    # platform-to-platform interchange penalty
WALK_SPEED_M_MIN  = 80     # 80 m/min ≈ 4.8 km/h, brisk walk
MAX_ACCESS_WALK_M = 1500   # cells beyond this from any MRT station = unreachable by MRT

def normalise_station_name(name):
    """Strip suffixes and standardise for cross-referencing."""
    if not name: return ''
    return (name.upper()
        .replace(' MRT STATION', '')
        .replace(' LRT STATION', '')
        .replace(' MRT DEPOT', '')
        .replace(' DEPOT', '')
        .strip())

def build_graph():
    """Return adjacency dict: station → [(neighbour, weight_min, line_code), ...]
    Stations that appear on multiple lines act as interchanges automatically."""
    G = {}
    def add_edge(a, b, w, line):
        G.setdefault(a, []).append((b, w, line))
        G.setdefault(b, []).append((a, w, line))
    for line, seq in LINES.items():
        for i in range(len(seq) - 1):
            add_edge(seq[i], seq[i+1], INTER_STATION_MIN, line)
    # Interchange penalty: NOT modelled as an edge — we account for it during BFS
    # by adding INTERCHANGE_MIN whenever the path changes line at a station.
    return G

def all_stations():
    """All station names known to the network (union across lines)."""
    s = set()
    for seq in LINES.values():
        s.update(seq)
    return s
