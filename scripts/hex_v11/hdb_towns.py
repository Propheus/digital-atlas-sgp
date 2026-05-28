"""Authoritative HDB Town classification of the 55 SG Planning Areas.

Source: HDB official site (Towns we manage, 2025). HDB groups residential
PAs into 25 'towns' plus several 'estates' (smaller residential pockets).
The non-residential PAs (Tuas, Sungei Kadut, Western Water Catchment,
nature reserves, port, military zones) are not classified as towns.

For our 'HDB Town' rollup view we use the 25 canonical towns.
"""

# 25 canonical HDB Towns (matches PA names in hex_v11)
HDB_TOWNS = {
    'Ang Mo Kio': 'Ang Mo Kio',
    'Bedok': 'Bedok',
    'Bishan': 'Bishan',
    'Bukit Batok': 'Bukit Batok',
    'Bukit Merah': 'Bukit Merah',
    'Bukit Panjang': 'Bukit Panjang',
    'Choa Chu Kang': 'Choa Chu Kang',
    'Clementi': 'Clementi',
    'Geylang': 'Geylang',
    'Hougang': 'Hougang',
    'Jurong East': 'Jurong East',
    'Jurong West': 'Jurong West',
    'Kallang': 'Kallang / Whampoa',  # HDB's display label
    'Marine Parade': 'Marine Parade',
    'Pasir Ris': 'Pasir Ris',
    'Punggol': 'Punggol',
    'Queenstown': 'Queenstown',
    'Sembawang': 'Sembawang',
    'Sengkang': 'Sengkang',
    'Serangoon': 'Serangoon',
    'Tampines': 'Tampines',
    'Tengah': 'Tengah',
    'Toa Payoh': 'Toa Payoh',
    'Woodlands': 'Woodlands',
    'Yishun': 'Yishun',
}

# Estates (residential but smaller; HDB treats as estates rather than towns)
HDB_ESTATES = {
    'Bukit Timah': 'Bukit Timah Estate',
    # Central Area umbrella covers Downtown Core / Museum / Outram / Rochor / River Valley / Singapore River
    'Downtown Core':   'Central Area',
    'Museum':          'Central Area',
    'Outram':          'Central Area',
    'Rochor':          'Central Area',
    'River Valley':    'Central Area',
    'Singapore River': 'Central Area',
}

# Non-residential PAs — explicitly NOT towns or estates
NON_RESIDENTIAL_PAS = {
    'Boon Lay',                 # industrial
    'Changi',                   # airport + perimeter
    'Changi Bay',               # reclamation
    'Central Water Catchment',  # reservoir
    'Lim Chu Kang',             # agriculture + military
    'Mandai',                   # nature + zoo
    'Marina East', 'Marina South', 'Straits View',  # CBD reclamation
    'Newton', 'Novena', 'Paya Lebar', 'Tanglin',    # mature mixed-use, but HDB doesn't manage them as towns
    'Pioneer',                  # industrial
    'North-Eastern Islands', 'Southern Islands', 'Western Islands',
    'Seletar',                  # aerospace
    'Simpang',                  # future development
    'Sungei Kadut',             # industrial
    'Tuas',                     # industrial / port
    'Western Water Catchment',  # reservoir
}

# Detailed zone_type per PA — drives map rendering at SZ/PA/Town levels.
# 'residential' zones get scored adequacy colors; everything else is
# rendered as "Not Applicable" (dark gray) at aggregate levels because the
# adequacy framing assumes a residential commute pattern that doesn't apply
# to airports / ports / nature reserves / reclamation / military.
ZONE_TYPE = {
    # === RESIDENTIAL — get full scoring ===
    # (all 25 HDB towns implicitly residential — see HDB_TOWNS dict)
    # HDB estates also residential:
    'Bukit Timah':     'residential',
    'Downtown Core':   'residential',   # Central Area — has some HDB + private residential
    'Museum':          'residential',
    'Outram':          'residential',
    'Rochor':          'residential',
    'River Valley':    'residential',
    'Singapore River': 'residential',
    # Mature mixed-use PAs that have substantial residential:
    'Newton':     'residential',
    'Novena':     'residential',
    'Paya Lebar': 'residential',
    'Tanglin':    'residential',

    # === INDUSTRIAL — workers in dorms, employer shuttles, not regular transit ===
    'Boon Lay':       'industrial',
    'Pioneer':        'industrial',
    'Sungei Kadut':   'industrial',
    'Tuas':           'industrial',

    # === AIRPORT / AEROSPACE ===
    'Changi':  'airport',
    'Seletar': 'airport',

    # === RECLAMATION / FUTURE DEVELOPMENT — no current residential ===
    'Changi Bay':   'future',
    'Marina East':  'future',
    'Marina South': 'future',
    'Straits View': 'future',
    'Simpang':      'future',

    # === NATURE / WATER CATCHMENT ===
    'Central Water Catchment': 'nature',
    'Western Water Catchment': 'nature',
    'Mandai':                  'nature',
    'Lim Chu Kang':            'nature',  # agriculture + military training

    # === ISLANDS (resort + special) ===
    'North-Eastern Islands': 'islands',
    'Southern Islands':      'islands',  # Sentosa + others
    'Western Islands':       'islands',  # Jurong Island chemical complex
}

# Default for any PA not listed above: assume residential (the 25 HDB towns)
def zone_type_of(pa_name):
    if pa_name in ZONE_TYPE: return ZONE_TYPE[pa_name]
    if pa_name in HDB_TOWNS: return 'residential'
    return 'unknown'

# === Granular per-hex refinement ===
# The PA-level zone_type is broad (e.g. all of Changi PA is "airport"), but
# within a single PA the hexes vary: some have MRT, some have dorm clusters,
# some are runway. We refine the type PER HEX based on MRT + dorm presence.
def refine_zone_type(broad_type, hex_row):
    """Return a granular zone_type for a single hex.

    hex_row: dict-like with keys mrt_stations, mrt_stations_in_1km,
             pop_nr_dorm, pop_total, parent_pa, etc.
    """
    if broad_type == 'residential':
        return 'residential'

    n_mrt_cell   = float(hex_row.get('mrt_stations') or 0)
    n_mrt_1km    = float(hex_row.get('mrt_stations_in_1km') or 0)
    n_mrt_500m   = float(hex_row.get('mrt_stations_in_500m') or 0)
    dorm         = float(hex_row.get('pop_nr_dorm') or 0)
    pop_total    = float(hex_row.get('pop_total') or 0)
    pa           = hex_row.get('parent_pa') or ''

    if broad_type == 'industrial':
        # Tuas Bay, Joo Koon, etc. with MRT in cell or within walking
        if n_mrt_1km >= 1 and dorm >= 500:
            return 'industrial_with_transit'
        # Sungei Kadut, parts of Pioneer, Tuas inland — dorm clusters, no MRT
        if dorm >= 500:
            return 'industrial_isolated'
        # Industrial cell without significant dorm population (warehouses, factories)
        return 'industrial_empty'

    if broad_type == 'airport':
        # Changi Lodge / airport-edge dorm clusters (S11 complex etc.)
        if dorm >= 500:
            return 'airport_residential_edge'
        # The actual airport, runways, terminals, ops zones
        return 'airport_operations'

    if broad_type == 'islands':
        # Sentosa (Southern Islands PA) — has Sentosa Cove residents + visitors,
        # uses Sentosa Express monorail + cable car instead of MRT
        if pa == 'Southern Islands' and pop_total >= 500:
            return 'islands_resort'
        # Jurong Island = chemical plant access-restricted, NE Islands = military
        return 'islands_restricted'

    if broad_type == 'future':
        # Marina South/East/Straits View — CBD reclamation with future MRT
        return 'future_development'

    if broad_type == 'nature':
        return 'nature'

    return 'unknown'

# Zone types where adequacy is computed and SHOWN with full coloring
SCORED_ZONES = {
    'residential',
    'industrial_with_transit',
    'industrial_isolated',
    'airport_residential_edge',
}

# Zone types where data is computed but shown with caveat (not the usual gap colors)
DATA_SHOWN_ZONES = {
    'islands_resort',       # Sentosa Cove with alternative transit
    'future_development',   # CBD reclamation — interesting but pre-population
}

# Zone types that stay Not Applicable
NA_ZONES = {
    'industrial_empty',     # warehouses without workers — no signal
    'airport_operations',   # runways, terminals — not residential context
    'islands_restricted',   # Jurong Island chemicals, NE Islands military
    'nature',               # catchments, Mandai, Lim Chu Kang
    'unknown',              # sea hexes, no PA
}

# Human-readable labels for UI
ZONE_LABELS = {
    'residential':              ('🏘', 'Residential'),
    'industrial_with_transit':  ('🏭', 'Industrial — MRT-served (worker context)'),
    'industrial_isolated':      ('🏭', 'Industrial — bus-only (worker context)'),
    'industrial_empty':         ('🏭', 'Industrial — warehouses (no scoring)'),
    'airport_residential_edge': ('✈️', 'Airport edge — dorm cluster (worker context)'),
    'airport_operations':       ('✈️', 'Airport operations (Not applicable)'),
    'islands_resort':           ('🏝', 'Resort island — Sentosa Express + cable car'),
    'islands_restricted':       ('🏝', 'Restricted island (Not applicable)'),
    'future_development':       ('🚧', 'Future development — MRT pre-population'),
    'nature':                   ('🌳', 'Nature reserve / catchment (Not applicable)'),
    'unknown':                  ('⬜', 'No data'),
}

def classify_pa(pa_name):
    """Return (is_hdb_town: bool, display_label: str | None, category: str)."""
    if pa_name in HDB_TOWNS:
        return True, HDB_TOWNS[pa_name], 'town'
    if pa_name in HDB_ESTATES:
        return False, HDB_ESTATES[pa_name], 'estate'
    if pa_name in NON_RESIDENTIAL_PAS:
        return False, pa_name, 'non_residential'
    return False, pa_name, 'unknown'
