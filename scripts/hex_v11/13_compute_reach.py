"""Compute journey-time-to-destination + reach % per hex8 cell.

For each hex8 cell:
  1. Find the nearest MRT station (with lat/lng) via haversine
  2. Compute walk-in time: dist / 80 m/min
  3. Dijkstra from that station to all 17 destination stations through the MRT graph,
     adding INTERCHANGE_MIN when the line changes
  4. Add walk-out time for the destination station's last-100m approach (estimated 1 min)
  5. Output: time_to_X_min for each destination + reach metrics

Outputs added to hex8_adequacy.parquet:
  time_to_cbd_min          (avg of Raffles Place + Marina Bay)
  time_to_orchard_min
  time_to_jurong_east_min
  time_to_changi_business_min
  time_to_nus_min
  pct_dest_within_45min    (key metric — LTA 2040 target)
  n_dest_reachable         (out of 17)
"""

import json, heapq, math, sys
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mrt_network import (
    LINES, DESTINATIONS, build_graph, all_stations, normalise_station_name,
    INTER_STATION_MIN, INTERCHANGE_MIN, WALK_SPEED_M_MIN, MAX_ACCESS_WALK_M,
)
from shapely import wkt as shp_wkt
from shapely.geometry import shape

HEX_PATH = Path('data/hex_v11/hex8_adequacy_features.parquet')
OUT = HEX_PATH  # in-place update

R = 6371000.0
def haversine_m(lat1, lng1, lat2, lng2):
    """Vectorised — accepts scalars or numpy arrays."""
    p1 = np.radians(lat1); p2 = np.radians(lat2)
    dp = p2 - p1; dl = np.radians(lng2 - lng1)
    a = np.sin(dp/2)**2 + np.cos(p1)*np.cos(p2)*np.sin(dl/2)**2
    return 2*R*np.arcsin(np.sqrt(a))

def load_station_centroids():
    """Return {NORMALISED_NAME: (lat, lng)} for all MRT stations (centroid of polygon)."""
    with open('data/transit_updated/train_stations_mar2026.geojson') as f:
        g = json.load(f)
    out = {}
    for feat in g['features']:
        p = feat['properties']
        typ = (p.get('TYP_CD_DES') or '').upper()
        if 'LRT' in typ: continue  # skip LRT (loops, not core network)
        raw_name = p.get('STN_NAM_DE') or p.get('STN_NAM') or ''
        name = normalise_station_name(raw_name)
        if not name or 'DEPOT' in raw_name.upper(): continue
        try:
            geom = shape(feat['geometry'])
            c = geom.centroid
            # Use first occurrence; duplicates (north/south platforms) collapse
            if name not in out:
                out[name] = (c.y, c.x)
        except Exception:
            continue
    return out

def dijkstra_from(graph, start, all_targets):
    """Return {target: time_min} for all stations reachable from start.
    Track current_line per node to apply interchange penalty correctly.
    State: (cost, node, last_line_used_to_arrive)."""
    # Multi-state Dijkstra: visited[(node, line_in)] = cost
    visited = {}
    # Initial state: at start, no incoming line
    heap = [(0.0, start, None)]
    distances = {}
    while heap:
        cost, node, line_in = heapq.heappop(heap)
        key = (node, line_in)
        if key in visited:
            continue
        visited[key] = cost
        # Best cost to this node (across any arrival line)
        if node not in distances or cost < distances[node]:
            distances[node] = cost
        for nbr, w, line_out in graph.get(node, []):
            extra = w
            if line_in is not None and line_in != line_out:
                extra += INTERCHANGE_MIN
            new_cost = cost + extra
            if (nbr, line_out) not in visited or new_cost < visited.get((nbr, line_out), float('inf')):
                heapq.heappush(heap, (new_cost, nbr, line_out))
    return distances

def main():
    h = pd.read_parquet(HEX_PATH)
    print(f'Loaded {h.shape}')

    print('Building MRT graph…')
    graph = build_graph()
    stations_known = all_stations()
    print(f'  Lines: {len(LINES)}  Stations in graph: {len(stations_known)}')

    print('Loading station centroids from geojson…')
    centroids = load_station_centroids()
    print(f'  Stations with coords: {len(centroids)}')

    # Sanity: how many of our hardcoded stations have coordinates?
    matched = sum(1 for s in stations_known if s in centroids)
    print(f'  Coverage: {matched}/{len(stations_known)} graph-stations matched to coords')
    missing = [s for s in stations_known if s not in centroids][:10]
    if missing:
        print(f'  Missing centroids (first 10): {missing}')

    # Pre-compute Dijkstra from EVERY destination station (faster than from every cell)
    # Because graph is small (~170 stations), this is O(D × V log V).
    print('\nRunning Dijkstra from each destination station…')
    dest_distances = {}
    for dest_name, meta in DESTINATIONS.items():
        st = meta['station']
        if st not in graph:
            print(f'  ⚠ Destination station "{st}" not in graph (skipping {dest_name})')
            continue
        dest_distances[dest_name] = dijkstra_from(graph, st, stations_known)
    print(f'  Computed distances for {len(dest_distances)} destinations')

    # For each cell, find nearest station, then look up its distance to each destination.
    print('\nProjecting onto hex8 cells…')
    station_names = sorted(centroids.keys())
    st_lat = np.array([centroids[s][0] for s in station_names])
    st_lng = np.array([centroids[s][1] for s in station_names])

    n = len(h)
    cell_nearest_st = np.empty(n, dtype=object)
    cell_walk_in_min = np.full(n, np.nan)

    cell_lat = h['lat'].to_numpy()
    cell_lng = h['lng'].to_numpy()

    for i in range(n):
        dists = haversine_m(cell_lat[i], cell_lng[i], st_lat, st_lng)
        j = int(np.argmin(dists))
        d = float(dists[j])
        cell_nearest_st[i] = station_names[j]
        cell_walk_in_min[i] = d / WALK_SPEED_M_MIN if d <= MAX_ACCESS_WALK_M else np.nan
        if (i+1) % 200 == 0:
            print(f'  {i+1}/{n}', flush=True)

    h['nearest_mrt_station'] = cell_nearest_st
    h['mrt_walk_in_min'] = cell_walk_in_min

    # Now: for each cell × destination, total journey = walk_in + station_to_dest + walk_out
    # walk_out: 1 min fixed (assume residents/destinations within 100m of station)
    WALK_OUT_MIN = 1.0

    print('\nComputing time-to-destination for each cell…')
    # Build per-destination column
    dest_cols = {}
    for dest_name in DESTINATIONS:
        if dest_name not in dest_distances: continue
        col = []
        for i in range(n):
            walk_in = cell_walk_in_min[i]
            ns = cell_nearest_st[i]
            if pd.isna(walk_in) or ns not in graph:
                col.append(np.nan); continue
            d = dest_distances[dest_name].get(ns)
            if d is None:
                col.append(np.nan); continue
            col.append(walk_in + d + WALK_OUT_MIN)
        dest_cols[dest_name] = np.asarray(col)

    # Materialise summary columns
    raffles  = dest_cols.get('Raffles Place')
    marina   = dest_cols.get('Marina Bay')
    h['time_to_cbd_min'] = np.fmin(raffles, marina) if raffles is not None and marina is not None else (raffles or marina)
    h['time_to_orchard_min']         = dest_cols.get('Orchard')
    h['time_to_jurong_east_min']     = dest_cols.get('Jurong East (JLD)')
    h['time_to_tampines_hub_min']    = dest_cols.get('Tampines Regional')
    h['time_to_changi_business_min'] = dest_cols.get('Changi Business Park')
    h['time_to_one_north_min']       = dest_cols.get('One-North')
    h['time_to_nus_min']             = dest_cols.get('NUS (Kent Ridge)')
    h['time_to_ntu_min']             = dest_cols.get('NTU (Boon Lay/Pioneer)')
    h['time_to_sgh_min']             = dest_cols.get('SGH (Outram)')
    h['time_to_ttsh_min']            = dest_cols.get('TTSH (Novena)')
    h['time_to_kkh_min']             = dest_cols.get('KKH (Little India)')
    h['time_to_cgh_min']             = dest_cols.get('CGH (Expo)')

    # Reach: % of destinations within 45 min (LTA 2040 target)
    arr = np.column_stack([v for v in dest_cols.values()])
    n_dest = arr.shape[1]
    within_45 = (arr <= 45).sum(axis=1)  # NaN counted as not within
    reachable = (~np.isnan(arr)).sum(axis=1)
    h['n_dest_reachable']        = reachable
    h['n_dest_within_45min']     = within_45
    h['pct_dest_within_45min']   = (within_45 / max(n_dest, 1)) * 100.0
    h['pct_dest_within_60min']   = ((arr <= 60).sum(axis=1) / max(n_dest, 1)) * 100.0

    h.to_parquet(OUT, index=False)
    print(f'\nWrote {OUT}')

    # Quick summary
    active = h[h['cell_active_flag'] == 1]
    print(f'\n=== REACH SUMMARY (active cells) ===')
    print(f'  Mean time to CBD:        {active["time_to_cbd_min"].mean():.1f} min')
    print(f'  Median time to CBD:      {active["time_to_cbd_min"].median():.1f} min')
    print(f'  Mean pct_dest_within_45: {active["pct_dest_within_45min"].mean():.1f}%')
    print(f'  Median pct_dest_within_45: {active["pct_dest_within_45min"].median():.1f}%')
    print(f'  Cells unreachable from MRT: {int(active["pct_dest_within_45min"].fillna(0).eq(0).sum())}')

if __name__ == '__main__':
    main()
