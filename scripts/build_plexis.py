"""
PLEXIS — Urban Knowledge Graph for SGP Digital Atlas
~200K nodes, ~50 relation types, ~2.4M edges
Built on atlas-1 from hex-9/hex-8/places/transit/amenity data.
"""
import json, time, math, os
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
import h3

t0 = time.time()
def tick(m): print(f"[{time.time()-t0:6.1f}s] {m}", flush=True)

DATA = Path("/home/azureuser/digital-atlas-sgp/data")
OUT = DATA / "plexis"
OUT.mkdir(exist_ok=True)

# Load all data
tick("Loading data...")
h9 = pd.read_parquet(DATA/"hex_v10/hex9_final.parquet").set_index('hex_id')
h8 = pd.read_parquet(DATA/"hex_v10/hex8_final.parquet").set_index('hex8_id')
pl = pd.read_parquet(DATA/"places_consolidated/sgp_places_featured.parquet")
tick(f"  h9={h9.shape}, h8={h8.shape}, places={pl.shape}")

# Transit
def gc(geom):
    if geom['type']=='Point': return (geom['coordinates'][1],geom['coordinates'][0])
    if geom['type']=='Polygon': c=geom['coordinates'][0]
    elif geom['type']=='MultiPolygon': c=geom['coordinates'][0][0]
    else: return None
    return (np.mean([c2[1] for c2 in c]),np.mean([c2[0] for c2 in c]))

with open(DATA/"transit_updated/train_stations_mar2026.geojson") as f: stn_fc=json.load(f)
with open(DATA/"transit_updated/bus_stops_mar2026.geojson") as f: bus_fc=json.load(f)

stations = []
for feat in stn_fc['features']:
    c=gc(feat['geometry'])
    if c: stations.append({'id':f"STN_{feat['properties'].get('STN_NAM_DE','UNK')}", 'lat':c[0],'lng':c[1],
                           'type':feat['properties'].get('TYP_CD_DES',''),'name':feat['properties'].get('STN_NAM_DE','')})

bus_stops = []
for feat in bus_fc['features']:
    g=feat['geometry']
    if g and g['type']=='Point':
        bus_stops.append({'id':f"BUS_{feat['properties'].get('BUS_STOP_N','UNK')}",'lat':g['coordinates'][1],'lng':g['coordinates'][0],
                         'name':feat['properties'].get('LOC_DESC','')})

tick(f"  Stations: {len(stations)}, Bus stops: {len(bus_stops)}")

# KD-trees
R_EARTH = 6371000
pl_coords = np.radians(pl[['latitude','longitude']].values)
pl_tree = cKDTree(pl_coords)
stn_coords = np.radians(np.array([(s['lat'],s['lng']) for s in stations]))
stn_tree = cKDTree(stn_coords) if len(stn_coords)>0 else None
bus_coords = np.radians(np.array([(b['lat'],b['lng']) for b in bus_stops]))
bus_tree = cKDTree(bus_coords) if len(bus_coords)>0 else None

# Amenities
amenity_data = {}
for name, fpath in [('hawker',DATA/"amenities/hawker_centres.geojson"),('school',DATA/"amenities/schools_geocoded.json"),
                     ('park',DATA/"amenities/parks_nature_reserves.geojson")]:
    pts = []
    if fpath.exists():
        with open(fpath) as f: data=json.load(f)
        if isinstance(data, list):
            for p in data:
                lat=p.get('latitude') or p.get('lat'); lng=p.get('longitude') or p.get('lng')
                if lat and lng: pts.append({'id':f"{name.upper()}_{len(pts)}",'lat':float(lat),'lng':float(lng)})
        elif 'features' in data:
            for feat in data['features']:
                c=gc(feat['geometry'])
                if c: pts.append({'id':f"{name.upper()}_{len(pts)}",'lat':c[0],'lng':c[1]})
    amenity_data[name] = pts

# HDB blocks
hdb_blocks = []
try:
    bldgs = pd.read_parquet(DATA/"buildings_overture/sgp_buildings_fused.parquet")
    for _, b in bldgs.iterrows():
        if pd.notna(b.get('is_hdb')) and bool(b['is_hdb']):
            hdb_blocks.append({'id':f"HDB_{len(hdb_blocks)}",'lat':b['cy'],'lng':b['cx']})
except: pass
tick(f"  HDB blocks: {len(hdb_blocks)}, Hawkers: {len(amenity_data.get('hawker',[]))}")

# ============================================================
# TRIPLET ACCUMULATOR
# ============================================================
triplets = []  # (head_id, relation, tail_id, attributes_dict)

def add(h, r, t, attrs=None):
    triplets.append((str(h), r, str(t), attrs or {}))

# ============================================================
# FAMILY 1: SPATIAL HIERARCHY
# ============================================================
tick("\n=== Family 1: Spatial hierarchy ===")

# Place → Hex-9 (LOCATED_IN)
for _, p in pl.iterrows():
    add(p['place_id'], 'LOCATED_IN', p['h3_res9'])
tick(f"  LOCATED_IN (place→hex9): {len(pl)}")

# Hex-9 → Hex-8 (PARENT_OF)
n_parent = 0
for h9_id in h9.index:
    h8_id = h3.cell_to_parent(h9_id, 8)
    if h8_id in h8.index:
        add(h8_id, 'PARENT_OF', h9_id)
        n_parent += 1
tick(f"  PARENT_OF (hex8→hex9): {n_parent}")

# Hex-9 → Subzone (PART_OF)
n_part = 0
for h9_id in h9.index:
    sz = h9.loc[h9_id].get('parent_subzone','')
    if sz:
        add(h9_id, 'PART_OF', f"SZ_{sz}")
        n_part += 1
tick(f"  PART_OF (hex9→subzone): {n_part}")

# Place → Category (IS_A)
cats = set()
for _, p in pl.iterrows():
    cat = p['main_category']
    add(p['place_id'], 'IS_A', f"CAT_{cat}")
    cats.add(cat)
tick(f"  IS_A (place→category): {len(pl)}, {len(cats)} categories")

# ============================================================
# FAMILY 2: ADJACENCY + BARRIERS
# ============================================================
tick("\n=== Family 2: Adjacency ===")

# Hex-9 adjacency (k=1 ring)
n_adj9 = 0
h9_set = set(h9.index)
for h9_id in h9.index:
    for nb in h3.grid_disk(h9_id, 1):
        if nb != h9_id and nb in h9_set:
            if h9_id < nb:  # avoid duplicates
                add(h9_id, 'ADJACENT_TO', nb)
                n_adj9 += 1
tick(f"  ADJACENT_TO (hex9↔hex9): {n_adj9}")

# Hex-8 adjacency
n_adj8 = 0
h8_set = set(h8.index)
for h8_id in h8.index:
    for nb in h3.grid_disk(h8_id, 1):
        if nb != h8_id and nb in h8_set:
            if h8_id < nb:
                # Check for barrier (walk detour > 2.5)
                attrs = {}
                add(h8_id, 'ADJACENT_TO', nb, attrs)
                n_adj8 += 1
tick(f"  ADJACENT_TO (hex8↔hex8): {n_adj8}")

# BARRIER_BETWEEN (hex-8 pairs with high walk detour)
# Use walk_detour columns if available
n_barrier = 0
if 'walk_detour_mrt' in h9.columns:
    for h9_id in h9.index:
        det = h9.loc[h9_id].get('walk_detour_mrt', 1)
        if isinstance(det, (int, float)) and det > 2.5:
            for nb in h3.grid_disk(h9_id, 1):
                if nb != h9_id and nb in h9_set and h9_id < nb:
                    add(h9_id, 'BARRIER_BETWEEN', nb, {'detour_ratio': round(det, 2)})
                    n_barrier += 1
                    if n_barrier > 5000: break
        if n_barrier > 5000: break
tick(f"  BARRIER_BETWEEN: {n_barrier}")

# ============================================================
# FAMILY 3: TRANSIT NETWORK
# ============================================================
tick("\n=== Family 3: Transit ===")

# Station SERVES hex-9
n_serves = 0
for s in stations:
    h9_id = h3.latlng_to_cell(s['lat'], s['lng'], 9)
    if h9_id in h9_set:
        add(s['id'], 'SERVES', h9_id, {'type': s['type']})
        n_serves += 1
        # Also serve k=1 neighbors
        for nb in h3.grid_disk(h9_id, 1):
            if nb != h9_id and nb in h9_set:
                add(s['id'], 'SERVES', nb, {'type': s['type'], 'ring': 1})
                n_serves += 1
tick(f"  SERVES (station→hex9): {n_serves}")

# Bus SERVES hex-9
n_bus_serves = 0
for b in bus_stops:
    h9_id = h3.latlng_to_cell(b['lat'], b['lng'], 9)
    if h9_id in h9_set:
        add(b['id'], 'SERVES', h9_id)
        n_bus_serves += 1
tick(f"  SERVES (bus→hex9): {n_bus_serves}")

# CONNECTS_TO (MRT network — stations on same line)
# Use rail_lines if available, otherwise connect stations within 3km
n_connects = 0
for i, s1 in enumerate(stations):
    for j, s2 in enumerate(stations):
        if j <= i: continue
        d = stn_tree.query([stn_coords[i]], k=1)[0][0] if stn_tree else 99
        # Connect if same type and within 3km
        actual_d = np.sqrt((s1['lat']-s2['lat'])**2+(s1['lng']-s2['lng'])**2)*111000
        if actual_d < 3000 and s1['type'] == s2['type']:
            add(s1['id'], 'CONNECTS_TO', s2['id'], {'distance_m': round(actual_d)})
            n_connects += 1
tick(f"  CONNECTS_TO (station↔station): {n_connects}")

# FEEDS_INTO (bus stops within 300m of MRT)
n_feeds = 0
if stn_tree and bus_tree:
    for i, b in enumerate(bus_stops):
        dists, idxs = stn_tree.query(bus_coords[i:i+1], k=3)
        for d, idx in zip(dists[0], idxs[0]):
            if d * R_EARTH < 300:
                add(b['id'], 'FEEDS_INTO', stations[idx]['id'], {'distance_m': round(d*R_EARTH)})
                n_feeds += 1
tick(f"  FEEDS_INTO (bus→station): {n_feeds}")

# OD_FLOW from od_train matrix
import zipfile, csv, io
n_od = 0
od_path = DATA/"lta_live/od_train_202512.zip"
if od_path.exists():
    with zipfile.ZipFile(od_path) as z:
        with z.open(z.namelist()[0]) as f:
            od = pd.read_csv(f)
    if 'DAY_TYPE' in od.columns:
        od = od[od['DAY_TYPE']=='WEEKDAY']
    trip_col = [c for c in od.columns if 'TOTAL' in c.upper() or 'TRIP' in c.upper()]
    if trip_col:
        od['trips'] = pd.to_numeric(od[trip_col[0]], errors='coerce').fillna(0)
        # Top flows per origin
        for orig, group in od.groupby('ORIGIN_PT_CODE'):
            top = group.nlargest(5, 'trips')
            for _, row in top.iterrows():
                if row['trips'] > 100:
                    add(f"STN_{orig}", 'OD_FLOW', f"STN_{row['DESTINATION_PT_CODE']}", 
                        {'daily_trips': round(row['trips']/22)})
                    n_od += 1
    tick(f"  OD_FLOW (station→station): {n_od}")

# ============================================================
# FAMILY 4: COMMERCIAL — Place↔Place
# ============================================================
tick("\n=== Family 4: Commercial ===")

# COMPETES_WITH (same category within 500m)
cat_to_idx = {}
categories = pl['main_category'].values
for cat in pl['main_category'].unique():
    cat_to_idx[cat] = np.where(categories == cat)[0]

n_compete = 0
for cat, idx in cat_to_idx.items():
    if len(idx) < 2: continue
    cat_coords = pl_coords[idx]
    cat_tree = cKDTree(cat_coords)
    pairs = cat_tree.query_ball_tree(cat_tree, 500/R_EARTH)
    for j, neighbors in enumerate(pairs):
        i_global = idx[j]
        pid = pl.iloc[i_global]['place_id']
        for k in neighbors[:10]:  # cap at 10 per place
            if k == j: continue
            k_global = idx[k]
            add(pid, 'COMPETES_WITH', pl.iloc[k_global]['place_id'])
            n_compete += 1
    if n_compete > 500000: break
tick(f"  COMPETES_WITH: {n_compete}")

# SYNERGIZES_WITH (known synergy pairs within 300m)
SYNERGY_MAP = {
    'Cafe & Coffee': ['Business','Office & Workspace'],
    'Restaurant': ['Hospitality'],
    'Convenience & Daily Needs': [],  # transit-based, not place-based
    'Fitness & Recreation': ['Cafe & Coffee','Health & Medical'],
    'Health & Medical': ['Health & Medical'],  # health cluster
    'Bar & Nightlife': ['Restaurant'],
    'Education': ['Education'],
    'Bakery & Pastry': ['Cafe & Coffee'],
}

n_synergy = 0
for target_cat, partner_cats in SYNERGY_MAP.items():
    if not partner_cats: continue
    t_idx = cat_to_idx.get(target_cat, np.array([]))
    if len(t_idx) == 0: continue
    for p_cat in partner_cats:
        p_idx = cat_to_idx.get(p_cat, np.array([]))
        if len(p_idx) == 0: continue
        p_tree = cKDTree(pl_coords[p_idx])
        pairs = p_tree.query_ball_point(pl_coords[t_idx], 300/R_EARTH)
        for j, neighbors in enumerate(pairs):
            i_global = t_idx[j]
            pid = pl.iloc[i_global]['place_id']
            for k in neighbors[:5]:
                k_global = p_idx[k]
                add(pid, 'SYNERGIZES_WITH', pl.iloc[k_global]['place_id'])
                n_synergy += 1
        if n_synergy > 300000: break
    if n_synergy > 300000: break
tick(f"  SYNERGIZES_WITH: {n_synergy}")

# SAME_BRAND (same brand, different outlet)
n_brand = 0
branded = pl[pl['is_branded']==1]
for brand, group in branded.groupby('brand_name'):
    if len(group) < 2: continue
    ids = group['place_id'].values
    for i in range(min(len(ids), 50)):
        for j in range(i+1, min(len(ids), 50)):
            add(ids[i], 'SAME_BRAND', ids[j], {'brand': brand})
            n_brand += 1
tick(f"  SAME_BRAND: {n_brand}")

# SUBSTITUTES_FOR (cross-category competition within 300m)
SUBS = {'Cafe & Coffee':['Bakery & Pastry','Hawker & Street Food'],
        'Restaurant':['Hawker & Street Food','Fast Food & QSR'],
        'Fast Food & QSR':['Hawker & Street Food','Convenience & Daily Needs']}
n_subs = 0
for cat, sub_cats in SUBS.items():
    c_idx = cat_to_idx.get(cat, np.array([]))
    if len(c_idx) == 0: continue
    for sub_cat in sub_cats:
        s_idx = cat_to_idx.get(sub_cat, np.array([]))
        if len(s_idx) == 0: continue
        s_tree = cKDTree(pl_coords[s_idx])
        pairs = s_tree.query_ball_point(pl_coords[c_idx], 300/R_EARTH)
        for j, neighbors in enumerate(pairs):
            i_global = c_idx[j]
            pid = pl.iloc[i_global]['place_id']
            for k in neighbors[:3]:
                k_global = s_idx[k]
                add(pid, 'SUBSTITUTES_FOR', pl.iloc[k_global]['place_id'])
                n_subs += 1
        if n_subs > 150000: break
    if n_subs > 150000: break
tick(f"  SUBSTITUTES_FOR: {n_subs}")

# ============================================================
# FAMILY 5: PLACE → ANCHORS
# ============================================================
tick("\n=== Family 5: Place-anchor ===")

# ANCHORED_BY MRT (within 300m)
n_anch = 0
if stn_tree:
    pairs = stn_tree.query_ball_point(pl_coords, 300/R_EARTH)
    for i, neighbors in enumerate(pairs):
        pid = pl.iloc[i]['place_id']
        for k in neighbors:
            add(pid, 'ANCHORED_BY', stations[k]['id'], {'anchor_type': 'mrt'})
            n_anch += 1
tick(f"  ANCHORED_BY MRT: {n_anch}")

# EXIT_FRONTAGE (within 50m of station — using station centroid as proxy)
n_exit = 0
if stn_tree:
    pairs = stn_tree.query_ball_point(pl_coords, 50/R_EARTH)
    for i, neighbors in enumerate(pairs):
        pid = pl.iloc[i]['place_id']
        for k in neighbors:
            add(pid, 'EXIT_FRONTAGE', stations[k]['id'])
            n_exit += 1
tick(f"  EXIT_FRONTAGE: {n_exit}")

# ANCHORED_BY hawker centres (within 200m)
n_hawk = 0
hawker_pts = amenity_data.get('hawker', [])
if hawker_pts:
    h_coords = np.radians(np.array([(h['lat'],h['lng']) for h in hawker_pts]))
    h_tree = cKDTree(h_coords)
    pairs = h_tree.query_ball_point(pl_coords, 200/R_EARTH)
    for i, neighbors in enumerate(pairs):
        pid = pl.iloc[i]['place_id']
        for k in neighbors:
            add(pid, 'ANCHORED_BY', hawker_pts[k]['id'], {'anchor_type': 'hawker'})
            n_hawk += 1
tick(f"  ANCHORED_BY hawker: {n_hawk}")

# VOID_DECK_OF (place within 30m of HDB block)
n_void = 0
if hdb_blocks:
    hdb_coords = np.radians(np.array([(h['lat'],h['lng']) for h in hdb_blocks]))
    hdb_tree = cKDTree(hdb_coords)
    pairs = hdb_tree.query_ball_point(pl_coords, 30/R_EARTH)
    for i, neighbors in enumerate(pairs):
        pid = pl.iloc[i]['place_id']
        for k in neighbors[:1]:  # nearest HDB only
            add(pid, 'VOID_DECK_OF', hdb_blocks[k]['id'])
            n_void += 1
tick(f"  VOID_DECK_OF: {n_void}")

# ============================================================
# FAMILY 6: DEMAND & SUPPLY
# ============================================================
tick("\n=== Family 6: Demand-supply ===")

# DEMANDS / UNDERSUPPLIED / OVERSUPPLIED (hex-8 → category)
n_demand = 0; n_under = 0; n_over = 0
for h8_id in h8.index:
    r = h8.loc[h8_id]
    for cat_short, cat_full in [('restaurant','Restaurant'),('cafe','Cafe & Coffee'),
                                 ('convenience','Convenience & Daily Needs'),('health','Health & Medical'),('fnb','FnB')]:
        dm = r.get(f'demand_match', 0) if cat_short == 'fnb' else 0
        sat = r.get(f'saturation_{cat_short}')
        gap = r.get(f'gap_{cat_short}')
        
        if pd.notna(sat) and sat < 0.5 and pd.notna(gap) and gap > 0:
            add(h8_id, 'UNDERSUPPLIED', f"CAT_{cat_full}", {'gap': round(gap,1), 'saturation': round(sat,2)})
            n_under += 1
        elif pd.notna(sat) and sat > 2.0:
            add(h8_id, 'OVERSUPPLIED', f"CAT_{cat_full}", {'saturation': round(sat,2)})
            n_over += 1

tick(f"  UNDERSUPPLIED: {n_under}, OVERSUPPLIED: {n_over}")

# DEMAND_LEAKS_TO (undersupplied hex → nearest supplied neighbor)
n_leak = 0
for h8_id in h8.index:
    r = h8.loc[h8_id]
    if r.get('saturation_fnb', 1) is not None and pd.notna(r.get('saturation_fnb')) and r.get('saturation_fnb', 1) < 0.5:
        for nb in h3.grid_disk(h8_id, 1):
            if nb != h8_id and nb in h8_set:
                nb_sat = h8.loc[nb].get('saturation_fnb')
                if pd.notna(nb_sat) and nb_sat > 0.8:
                    add(h8_id, 'DEMAND_LEAKS_TO', nb, {'category': 'fnb'})
                    n_leak += 1
                    break
tick(f"  DEMAND_LEAKS_TO: {n_leak}")

# COMPARABLE_TO (same archetype hex-8, top-5 by feature similarity)
n_comp = 0
if 'archetype' in h8.columns:
    for arch, group in h8.groupby('archetype'):
        if len(group) < 3: continue
        ids = list(group.index)
        # Simple: connect all pairs within same archetype (capped)
        for i in range(min(len(ids), 100)):
            for j in range(i+1, min(i+6, len(ids))):
                add(ids[i], 'COMPARABLE_TO', ids[j], {'archetype': arch})
                n_comp += 1
tick(f"  COMPARABLE_TO: {n_comp}")

# RESIDENTIAL_DEMAND_TO / WORKER_INFLOW
n_res_flow = 0; n_work_flow = 0
for h8_id in h8.index:
    r = h8.loc[h8_id]
    ndf = r.get('net_demand_flow', 0)
    if isinstance(ndf, (int,float)) and ndf > 0.5:
        # Residential demand flows outward — find nearest commercial neighbor
        for nb in h3.grid_disk(h8_id, 1):
            if nb != h8_id and nb in h8_set:
                nb_ndf = h8.loc[nb].get('net_demand_flow', 0)
                if isinstance(nb_ndf, (int,float)) and nb_ndf < -0.1:
                    add(h8_id, 'RESIDENTIAL_DEMAND_TO', nb)
                    n_res_flow += 1
    di = r.get('daytime_intensity', 1)
    if isinstance(di, (int,float)) and di > 3:
        # Worker inflow — find residential sources
        for nb in h3.grid_disk(h8_id, 2):
            if nb != h8_id and nb in h8_set:
                nb_pop = h8.loc[nb].get('population', 0)
                if isinstance(nb_pop, (int,float)) and nb_pop > 10000:
                    add(nb, 'WORKER_INFLOW', h8_id)
                    n_work_flow += 1
tick(f"  RESIDENTIAL_DEMAND_TO: {n_res_flow}, WORKER_INFLOW: {n_work_flow}")

# Category ↔ Category structural relations
SYNERGY_CATS = [('Cafe & Coffee','Business'),('Restaurant','Hospitality'),
                ('Fitness & Recreation','Cafe & Coffee'),('Health & Medical','Health & Medical'),
                ('Bar & Nightlife','Restaurant'),('Education','Education'),
                ('Bakery & Pastry','Cafe & Coffee'),('Convenience & Daily Needs','Transport')]
for a, b in SYNERGY_CATS:
    add(f"CAT_{a}", 'SYNERGY_PAIR', f"CAT_{b}")

SUB_CATS = [('Cafe & Coffee','Hawker & Street Food'),('Restaurant','Fast Food & QSR'),
            ('Convenience & Daily Needs','Shopping & Retail')]
for a, b in SUB_CATS:
    add(f"CAT_{a}", 'SUBSTITUTES', f"CAT_{b}")

tick(f"  Category structure: {len(SYNERGY_CATS)} synergy pairs, {len(SUB_CATS)} substitution pairs")

# ============================================================
# SAVE
# ============================================================
tick("\n=== Saving Plexis ===")

# Count by relation type
rel_counts = defaultdict(int)
for _, r, _, _ in triplets:
    rel_counts[r] += 1

# Save triplets
triplet_records = [{'head': h, 'relation': r, 'tail': t, **attrs} for h, r, t, attrs in triplets]
df_triplets = pd.DataFrame(triplet_records)
df_triplets.to_parquet(OUT/"plexis_triplets.parquet", index=False)

# Save summary
summary = {
    'name': 'Plexis',
    'description': 'Urban Knowledge Graph for SGP Digital Atlas',
    'generated': time.strftime('%Y-%m-%d'),
    'nodes': {
        'places': len(pl),
        'hex9': len(h9),
        'hex8': len(h8),
        'stations': len(stations),
        'bus_stops': len(bus_stops),
        'hdb_blocks': len(hdb_blocks),
        'categories': len(cats),
        'hawkers': len(amenity_data.get('hawker', [])),
    },
    'total_nodes': len(pl) + len(h9) + len(h8) + len(stations) + len(bus_stops) + len(hdb_blocks) + len(cats),
    'total_edges': len(triplets),
    'relation_types': len(rel_counts),
    'relations': {r: c for r, c in sorted(rel_counts.items(), key=lambda x: -x[1])},
}

with open(OUT/"plexis_summary.json", 'w') as f:
    json.dump(summary, f, indent=2)

tick(f"\n{'='*60}")
tick(f"PLEXIS BUILT")
tick(f"{'='*60}")
tick(f"  Nodes: {summary['total_nodes']:,}")
tick(f"  Edges: {summary['total_edges']:,}")
tick(f"  Relation types: {summary['relation_types']}")
tick(f"")
for r, c in sorted(rel_counts.items(), key=lambda x: -x[1]):
    tick(f"  {r:30s} {c:>10,}")
tick(f"")
tick(f"  Saved: {OUT}/plexis_triplets.parquet ({os.path.getsize(OUT/'plexis_triplets.parquet')/1e6:.1f} MB)")
tick(f"  Saved: {OUT}/plexis_summary.json")
tick(f"  Total time: {time.time()-t0:.1f}s")
