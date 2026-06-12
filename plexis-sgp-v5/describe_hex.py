"""
Plexis SGP v4 — Hex profiler.

Given a hex9_id (or a (lat,lng) point), print everything Plexis knows.
Works against the current Stage 0–4 outputs.

Usage:
    python3 describe_hex.py <hex9_id>
    python3 describe_hex.py <lat> <lng>
    python3 describe_hex.py --top-pop 5         # top-5 by population
    python3 describe_hex.py --top-magnets 5     # top-5 by magnet density
    python3 describe_hex.py --landmark vivocity # named landmarks
"""
import sys, argparse
from pathlib import Path
import pandas as pd
import h3

ROOT = Path(__file__).parent

LANDMARKS = {
    "vivocity":         ("MARITIME SQUARE", None),
    "raffles_place":    ("RAFFLES PLACE", None),
    "marina_bay_sands": (None, "DOWNTOWN CORE"),  # use PA
    "orchard":          ("BOULEVARD", None),
    "changi_airport":   (None, "CHANGI"),
    "sentosa":          ("SENTOSA", None),
    "nus":              ("KENT RIDGE", None),
    "tuas":             (None, "TUAS"),
    "jurong_island":    ("JURONG ISLAND AND BUKOM", None),
    "pasir_ris_west":   ("PASIR RIS WEST", None),
}


def load_all():
    h9 = pd.read_parquet(ROOT/"hex/hex9_universe.parquet")
    pop = pd.read_parquet(ROOT/"hex/hex9_population.parquet")
    lu = pd.read_parquet(ROOT/"hex/hex9_land_use.parquet")
    bldgs_path = ROOT/"hex/hex9_buildings.parquet"
    bldgs = pd.read_parquet(bldgs_path) if bldgs_path.exists() else None
    rd_clean = ROOT/"hex/hex9_roads_clean.parquet"
    rd = pd.read_parquet(rd_clean) if rd_clean.exists() else None
    tr_clean = ROOT/"hex/hex9_transit_clean.parquet"
    tr = pd.read_parquet(tr_clean) if tr_clean.exists() else None
    places = pd.read_parquet(ROOT/"places/sgp_places_final.parquet")
    return h9, pop, lu, bldgs, rd, tr, places


def describe(hex9_id, h9, pop, lu, bldgs, rd, tr, places):
    if hex9_id not in set(h9["hex9_id"]):
        print(f"Hex {hex9_id} not in universe")
        return
    h = h9[h9["hex9_id"] == hex9_id].iloc[0]
    p = pop[pop["hex9_id"] == hex9_id].iloc[0] if hex9_id in set(pop["hex9_id"]) else None
    l = lu[lu["hex9_id"] == hex9_id].iloc[0] if hex9_id in set(lu["hex9_id"]) else None
    pl = places[places["hex9_id"] == hex9_id]

    print(f"\n{'='*70}")
    print(f"HEX-9: {hex9_id}")
    print(f"{'='*70}")
    print(f"  Centroid: ({h['lat']:.5f}, {h['lng']:.5f})")
    print(f"  hex-8 parent: {h['parent_hex8']}")
    print(f"  Subzone:      {h['parent_subzone_name']} ({h['parent_subzone']})")
    print(f"  Planning Area: {h['parent_pa']}")
    print(f"  Region:       {h['parent_region']}")

    if p is not None and p.get("pop_total_all", 0) > 0:
        print(f"\n--- POPULATION ---")
        print(f"  Total (residents + non-residents):  {p['pop_total_all']:>8,.0f}")
        print(f"    Residents:                        {p['pop_resident']:>8,.0f}  ({(1-p['nonres_share'])*100:.1f}%)")
        print(f"      HDB:                            {p['pop_hdb']:>8,.0f}  ({p['pop_hdb_share']*100:.1f}% of res)")
        print(f"      Non-HDB:                        {p['pop_non_hdb']:>8,.0f}")
        print(f"    Non-residents (FW + EP + MDW):    {p['pop_nonresident']:>8,.0f}  ({p['nonres_share']*100:.1f}%)")
        print(f"  Age 0-14:                           {p['pop_0_14']:>8,.0f}  (residents)")
        print(f"  Age 15-64:                          {p['pop_15_64']:>8,.0f}")
        print(f"  Age 65+:                            {p['pop_65plus']:>8,.0f}")
    else:
        print(f"\n--- POPULATION --- (uninhabited)")

    if bldgs is not None:
        b = bldgs[bldgs["hex9_id"] == hex9_id]
        if len(b) > 0:
            br = b.iloc[0]
            print(f"\n--- BUILDINGS ---")
            print(f"  Total buildings: {int(br['bldg_count']):>4}  ({br['bldg_density_per_km2']:,.0f}/km²)")
            print(f"  Footprint share: {br['bldg_footprint_share']*100:5.1f}% of hex area")
            if br['bldg_count'] > 0:
                bucket_cols = [(c[5:-6], br[c]) for c in bldgs.columns
                               if c.startswith("bldg_") and c.endswith("_count") and c != "bldg_count"]
                bucket_cols = [(n, v) for n, v in bucket_cols if v > 0]
                bucket_cols.sort(key=lambda x: -x[1])
                print(f"  By class:")
                for name, cnt in bucket_cols[:6]:
                    bar = "█" * min(int(cnt / max(c[1] for c in bucket_cols) * 25), 25)
                    print(f"    {name:18s}  {int(cnt):>4}  {bar}")
            if pd.notna(br['best_max_floors']) and br['best_max_floors'] > 0:
                avg_fl = br['best_avg_floors'] if pd.notna(br['best_avg_floors']) else 0
                print(f"  Floors: avg {avg_fl:.1f}, max {int(br['best_max_floors'])} {'  [HIGHRISE]' if br['is_highrise'] else ''}")
            if int(br['hdb_block_count']) > 0:
                print(f"  HDB blocks: {int(br['hdb_block_count'])} ({int(br['hdb_dwelling_units']):,} units)")
                if pd.notna(br.get('hdb_avg_year')):
                    print(f"    Built: {int(br['hdb_min_year'])}–{int(br['hdb_avg_year'])} avg")

    if l is not None:
        print(f"\n--- LAND USE ---")
        print(f"  Land area:    {l['lu_total_m2']/1e4:.2f} ha ({l['lu_total_m2']/1e6:.4f} km²)")
        print(f"  Dominant use: {l['dominant_use']}")
        print(f"  Entropy:      {l['lu_entropy']:.3f}  ({'mixed' if l['lu_entropy'] > 1.0 else 'homogeneous'})")
        print(f"  Parcels:      {int(l['lu_parcel_count'])}")
        if pd.notna(l['avg_gpr']):
            print(f"  Avg GPR:      {l['avg_gpr']:.2f}  (max {l['max_gpr']:.2f})")
        bucket_cols = [c for c in lu.columns if c.startswith("lu_") and c.endswith("_pct")]
        shares = [(c[3:-4], l[c]) for c in bucket_cols if l[c] > 0.005]
        shares.sort(key=lambda x: -x[1])
        print(f"  Bucket shares (>0.5%):")
        for name, share in shares:
            bar = "█" * int(share * 30)
            print(f"    {name:14s}  {share*100:5.1f}%  {bar}")

    if rd is not None:
        rdr = rd[rd["hex9_id"] == hex9_id]
        if len(rdr) > 0 and rdr.iloc[0]["road_length_total_m"] > 0:
            r = rdr.iloc[0]
            print(f"\n--- ROADS & PARKING ---")
            print(f"  Length: {r['road_length_total_m']/1000:.2f} km  ({r['road_density_km_per_km2']:.0f} km/km²)")
            print(f"  Walkable share: {r['road_walkable_share']*100:.0f}%   |   Max class through: {r['road_max_class_through']}")
            if r['road_intersection_density_per_km2'] > 0:
                print(f"  Intersections: {int(r['road_intersection_density_per_km2']*0.105)} ({r['road_intersection_density_per_km2']:.0f}/km²)")
            tags = []
            if r['dist_expressway_m'] < 200: tags.append("EXPRESSWAY-NEAR")
            if r['near_expressway_exit_400m']: tags.append("EXIT-400m")
            if tags:
                print(f"  Expressway dist: {r['dist_expressway_m']:.0f}m  [{', '.join(tags)}]")
            if r['lane_km_per_km2'] > 0:
                print(f"  Vehicle: {r['lane_km_per_km2']*0.105:.1f} lane-km, {r['oneway_pct']*100:.0f}% oneway", end="")
                if r['bridge_length_m'] > 0: print(f", {r['bridge_length_m']:.0f}m bridges", end="")
                print()
            if r['signalized_crossing_count'] > 0:
                print(f"  Signalized crossings: {int(r['signalized_crossing_count'])}")
            if r['parking_lot_count'] > 0 or r['hdb_mscp_count'] > 0:
                bits = []
                if r['parking_lot_count'] > 0: bits.append(f"{int(r['parking_lot_count'])} OSM lots")
                if r['hdb_mscp_count'] > 0: bits.append(f"{int(r['hdb_mscp_count'])} HDB MSCPs")
                print(f"  Parking: {' · '.join(bits)}")
            if r['centr_betweenness_max'] > 0:
                print(f"  Network centrality (major roads): max betweenness {r['centr_betweenness_max']:.4f}, "
                      f"{int(r['centr_bridge_count'])} bridge endpoints")

    if tr is not None:
        trr = tr[tr["hex9_id"] == hex9_id]
        if len(trr) > 0:
            t = trr.iloc[0]
            has_transit = (t["mrt_station_count"] > 0 or t["bus_stop_count"] > 0
                           or t["near_mrt_400m"] or t["near_bus_300m"])
            if has_transit:
                print(f"\n--- TRANSIT ---")
                tags = []
                if t["is_mrt_interchange"]: tags.append("MRT-INTERCHANGE")
                if t["near_mrt_400m"]: tags.append("MRT-400m")
                if t["near_bus_300m"]: tags.append("BUS-300m")
                tag_str = f"  [{', '.join(tags)}]" if tags else ""
                print(f"  Transit score: {t['transit_score']:.2f}{tag_str}")
                line = []
                if t["mrt_station_count"] > 0: line.append(f"{int(t['mrt_station_count'])} MRT/LRT")
                if t["mrt_exit_count"] > 0: line.append(f"{int(t['mrt_exit_count'])} exits")
                if t["bus_stop_count"] > 0: line.append(f"{int(t['bus_stop_count'])} bus stops")
                if line: print(f"  Counts: {' · '.join(line)}")
                dists = []
                if t["dist_mrt_m"] < 9999: dists.append(f"MRT {t['dist_mrt_m']:.0f}m")
                if t["dist_mrt_exit_m"] < 9999: dists.append(f"exit {t['dist_mrt_exit_m']:.0f}m")
                if t["dist_bus_m"] < 9999: dists.append(f"bus {t['dist_bus_m']:.0f}m")
                if dists: print(f"  Distances: {' · '.join(dists)}")
                if t["rail_line_through_m"] > 0:
                    print(f"  Rail line through: {t['rail_line_through_m']:.0f}m")
                if t["daily_train_taps"] > 0 or t["daily_bus_taps"] > 0:
                    print(f"  Daily taps (Jan/Dec '26): train {t['daily_train_taps']:,.0f}, bus {t['daily_bus_taps']:,.0f}")
                if t.get("bus_routes_per_stop_max", 0) > 0:
                    routes_max = int(t["bus_routes_per_stop_max"])
                    routes_mean = t.get("bus_routes_per_stop_mean", 0)
                    headway = t.get("gtfs_headway_am_min", 999)
                    head_str = f"{headway:.1f} min" if headway < 999 else "n/a"
                    print(f"  GTFS: max {routes_max} routes/stop · mean {routes_mean:.1f} · best AM headway {head_str}")

    # Walkability section
    wk_path = ROOT / "hex/hex9_walkability.parquet"
    if wk_path.exists():
        wk = pd.read_parquet(wk_path)
        wkr = wk[wk["hex9_id"] == hex9_id]
        if len(wkr) > 0:
            w = wkr.iloc[0]
            if w["ped_path_length_m"] > 0 or w["walk_amenities_400m"] > 0:
                print(f"\n--- WALKABILITY ---")
                print(f"  Walkability score: {w['walkability_score']:.2f}{'  [SEVERED]' if w['expressway_severance'] else ''}")
                print(f"  Pedestrian paths: {w['ped_path_length_m']/1000:.2f} km ({w['ped_path_density_km_per_km2']:.0f} km/km²)")
                bits = []
                for k, v in [("hawker", w["dist_walk_hawker_m"]), ("clinic", w["dist_walk_clinic_m"]),
                              ("market", w["dist_walk_supermarket_m"]), ("park", w["dist_walk_park_m"]),
                              ("school", w["dist_walk_school_m"])]:
                    if pd.notna(v):
                        bits.append(f"{k} {v:.0f}m")
                if bits: print(f"  Walk distances: {' · '.join(bits)}")
                print(f"  Within 400m walk: {int(w['walk_amenities_400m'])} places "
                      f"({int(w['walk_food_400m'])} food · {int(w['walk_hawker_400m'])} hawker · "
                      f"{int(w['walk_park_400m'])} park · {int(w['walk_school_400m'])} school)")

    print(f"\n--- PLACES ({len(pl):,}) ---")
    if len(pl) == 0:
        print("  (no places in hex)")
    else:
        # category mix
        cat_mix = pl["plexis_category"].value_counts().head(8)
        print(f"  Category mix (top 8):")
        for cat, c in cat_mix.items():
            bar = "█" * min(int(c / max(cat_mix) * 25), 25)
            print(f"    {cat:22s}  {c:>4,}  {bar}")
        # quality
        magnets = pl[pl["is_magnet"]]
        print(f"\n  Magnets (rating ≥ 4 ★ × reviews ≥ 100): {len(magnets):,}")
        # branded
        branded = pl[pl["brand_norm"].notna()]
        print(f"  Branded:    {len(branded):,}  ({100*len(branded)/len(pl):.1f}%)")
        if len(branded) > 0:
            top_brands = branded["brand_norm"].value_counts().head(5)
            print(f"    Top brands: {', '.join(f'{b} ({c})' for b, c in top_brands.items())}")
        # top magnet places
        if len(magnets) > 0:
            print(f"\n  Top magnet places (by magnet_strength):")
            top_m = magnets.nlargest(5, "magnet_strength")
            for _, r in top_m.iterrows():
                stars = r["rating"] if pd.notna(r["rating"]) else "?"
                print(f"    {r['magnet_strength']:>5.1f}  {str(r['name'])[:38]:38s}  [{r['plexis_category']:18s}]  {stars}★ × {int(r['reviews_count']):,}")

    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("hex_or_lat", nargs="?", help="hex9_id or latitude")
    ap.add_argument("lng", nargs="?", type=float, help="longitude (if first arg is lat)")
    ap.add_argument("--top-pop", type=int, default=0, help="Show top-N hexes by population")
    ap.add_argument("--top-magnets", type=int, default=0, help="Show top-N hexes by magnet count")
    ap.add_argument("--landmark", help=f"Named landmark: {','.join(LANDMARKS.keys())}")
    args = ap.parse_args()

    h9, pop, lu, bldgs, rd, tr, places = load_all()
    print(f"Loaded: hex={len(h9):,}  pop_rows={len(pop):,}  lu_rows={len(lu):,}  places={len(places):,}")

    if args.top_pop:
        top = pop.nlargest(args.top_pop, "pop_total_all")
        for _, r in top.iterrows():
            describe(r["hex9_id"], h9, pop, lu, bldgs, rd, tr, places)
        return
    if args.top_magnets:
        m = places[places["is_magnet"]].groupby("hex9_id").size().sort_values(ascending=False).head(args.top_magnets)
        for hid in m.index:
            describe(hid, h9, pop, lu, bldgs, rd, tr, places)
        return
    if args.landmark:
        sz_target, pa_target = LANDMARKS.get(args.landmark.lower(), (None, None))
        if sz_target:
            cands = h9[h9["parent_subzone_name"] == sz_target]
        else:
            cands = h9[h9["parent_pa"] == pa_target]
        if len(cands) == 0:
            print(f"No hex matches landmark {args.landmark}")
            return
        # pick the one with most places
        place_counts = places.groupby("hex9_id").size()
        cands = cands.copy()
        cands["n_places"] = cands["hex9_id"].map(place_counts).fillna(0)
        top = cands.nlargest(1, "n_places")
        describe(top.iloc[0]["hex9_id"], h9, pop, lu, bldgs, rd, tr, places)
        return

    if args.hex_or_lat is None:
        ap.print_help()
        return
    if args.lng is not None:
        # treat as lat/lng
        lat = float(args.hex_or_lat)
        lng = args.lng
        hid = h3.latlng_to_cell(lat, lng, 9)
        describe(hid, h9, pop, lu, bldgs, rd, tr, places)
    else:
        describe(args.hex_or_lat, h9, pop, lu, bldgs, rd, tr, places)


if __name__ == "__main__":
    main()
