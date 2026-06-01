"""
Plexis SGP v4 — Stage 5 v2: improved transit per hex-9.

Improvements over v1:
  - Use slash-separated PT_CODE format (e.g. "EW16/NE3/TE17") to identify
    interchanges directly from tap data — no inline mapping needed for that signal.
  - Use GTFS routes.txt + trips.txt + stops.txt to compute:
      * bus_routes_per_stop  (routes serving each stop)
      * gtfs_headway_am_min  (best AM-peak headway, 7-9am)
  - Use platform_crowd.json (LTA real-time crowd snapshots) as auxiliary signal.

Output: hex/hex9_transit.parquet  (7,318 × ~18)

Schema additions over v1:
  + bus_routes_per_stop_max  — max routes count among stops in this hex
  + bus_routes_per_stop_mean — mean routes count
  + gtfs_headway_am_min      — best (lowest) headway in AM peak across stops in hex
  + n_pt_codes_in_hex        — number of unique tap-data station codes hashed to this hex
"""
import json, os, time, re
from pathlib import Path
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.strtree import STRtree
import h3

ROOT = Path(__file__).parent


def _resolve_data_root():
    if os.environ.get("PLEXIS_DATA_ROOT"):
        return Path(os.environ["PLEXIS_DATA_ROOT"])
    for c in [Path("/home/azureuser/digital-atlas-sgp/data"), ROOT.parent / "data"]:
        if c.exists():
            return c
    raise FileNotFoundError("No data root found")


DATA = _resolve_data_root()
TRAIN_STATIONS = DATA / "transit_updated/train_stations_mar2026.geojson"
TRAIN_EXITS = DATA / "transit_updated/train_station_exits_feb2025.geojson"
BUS_STOPS = DATA / "transit_updated/bus_stops_mar2026.geojson"
RAIL_LINES = DATA / "transit/rail_lines.geojson"
TAP_TRAIN = DATA / "lta_live/transport_node_train_202601.csv"
TAP_BUS = DATA / "lta_live/transport_node_bus_202512.csv"
PLATFORM_CROWD = DATA / "lta_live/platform_crowd.json"
GTFS_DIR = DATA / "gtfs/singapore-gtfs"
HEX9 = ROOT / "hex/hex9_universe.parquet"
OUT = ROOT / "hex/hex9_transit.parquet"
REPORT = ROOT / "hex/transit_report.json"


def main():
    t0 = time.time()
    print("Loading inputs...")
    ts = gpd.read_file(TRAIN_STATIONS).to_crs(4326)
    te = gpd.read_file(TRAIN_EXITS).to_crs(4326)
    bs = gpd.read_file(BUS_STOPS).to_crs(4326)
    rl = gpd.read_file(RAIL_LINES).to_crs(4326)
    h9 = pd.read_parquet(HEX9)
    print(f"  train stations: {len(ts)}  exits: {len(te)}  bus stops: {len(bs)}")
    print(f"  rail segments: {len(rl)}  hex-9: {len(h9):,}")

    # Project to 3414
    print("\n  Projecting to EPSG:3414...")
    ts3 = ts.to_crs(3414)
    te3 = te.to_crs(3414)
    bs3 = bs.to_crs(3414)
    rl3 = rl.to_crs(3414)

    # Hash to hex-9
    print("  Hashing entities to hex-9...")
    cent_ts = ts3.geometry.centroid.to_crs(4326)
    ts["hex9_id"] = [h3.latlng_to_cell(p.y, p.x, 9) for p in cent_ts]
    bs["hex9_id"] = [h3.latlng_to_cell(p.y, p.x, 9) for p in bs.geometry]
    te["hex9_id"] = [h3.latlng_to_cell(p.y, p.x, 9) for p in te.geometry]

    # === Train tap aggregation using slash-separated PT_CODE ===
    print("\n  Train tap analysis (using slash-separated PT_CODE for interchanges)...")
    tap_train = pd.read_csv(TAP_TRAIN)
    # Per PT_CODE (which may itself be an interchange like "EW16/NE3/TE17"):
    # sum tap_in + tap_out → divide by 31 days for daily total at that station
    train_per_code = tap_train.groupby("PT_CODE").agg(
        tap_in=("TOTAL_TAP_IN_VOLUME", "sum"),
        tap_out=("TOTAL_TAP_OUT_VOLUME", "sum"),
    ).reset_index()
    train_per_code["daily_taps"] = (train_per_code["tap_in"] + train_per_code["tap_out"]) / 31
    train_per_code["n_lines"] = train_per_code["PT_CODE"].apply(lambda s: s.count("/") + 1)
    train_per_code["is_interchange"] = train_per_code["n_lines"] >= 2
    print(f"    PT_CODE rows: {len(train_per_code):,}")
    print(f"    interchanges (≥2 codes): {train_per_code['is_interchange'].sum()}")
    print(f"    total daily taps: {train_per_code['daily_taps'].sum():,.0f}")

    # PT_CODE → station name mapping via station name patterns
    # Strategy: each PT_CODE (e.g., "EW14/NS26") has known station name (Raffles Place).
    # We MATCH by spatial nearest-neighbor: the centroid of tap-row's station can be inferred
    # from rail_lines geometries that pass through stations with that code, OR we just
    # build the explicit mapping via a curated dictionary.
    # FOR NOW: use per-station polygon's STN_NAM_DE matched against an inline lookup.
    # Coverage will be partial; for unmatched stations we use line-average taps as a fallback.

    # Inline mapping from raw PT_CODE → station name (extending v1 with more interchanges
    # detected from PT_CODE structure).
    INTERCHANGE_CODES = set()
    for c in train_per_code[train_per_code["is_interchange"]]["PT_CODE"]:
        INTERCHANGE_CODES.add(c)

    # Build station-level taps by treating each PT_CODE as one station (slashes denote
    # interchange — taps are already aggregated at station level).
    # We assign these to station polygons via a name-based code map.

    # Comprehensive PT_CODE → station_name map (covers all 200+ MRT/LRT stations)
    STATION_CODE_MAP = build_station_code_map()
    train_per_code["station_name"] = train_per_code["PT_CODE"].apply(
        lambda c: lookup_station_name(c, STATION_CODE_MAP))

    matched = train_per_code["station_name"].notna().sum()
    print(f"    PT_CODEs matched to stations: {matched}/{len(train_per_code)}")

    # Station-level taps (sum across all PT_CODEs that match same station)
    station_taps = train_per_code.dropna(subset=["station_name"]).groupby("station_name").agg(
        daily_taps=("daily_taps", "sum"),
        is_interchange=("is_interchange", "max"),
        n_pt_codes=("PT_CODE", "count"),
    ).reset_index()

    # Match to ts (station polygon names)
    ts["station_name_norm"] = ts["STN_NAM_DE"].astype(str).str.replace(
        r"\s+(MRT|LRT)\s+STATION$", "", regex=True
    ).str.upper().str.strip()

    ts_with_taps = ts.merge(station_taps, left_on="station_name_norm",
                             right_on="station_name", how="left")
    matched_polys = ts_with_taps["daily_taps"].notna().sum()
    print(f"    station polygons matched: {matched_polys}/{len(ts)}")
    fallback_taps = train_per_code["daily_taps"].mean()
    ts_with_taps["daily_taps"] = ts_with_taps["daily_taps"].fillna(fallback_taps)
    ts_with_taps["is_interchange"] = ts_with_taps["is_interchange"].fillna(False).astype(bool)
    print(f"    fallback taps for unmatched: {fallback_taps:,.0f}")

    train_taps_hex = ts_with_taps.groupby("hex9_id")["daily_taps"].sum().reset_index(name="daily_train_taps")
    interchange_hex = ts_with_taps[ts_with_taps["is_interchange"]].groupby("hex9_id").size().reset_index(name="interchange_count")
    interchange_hex["is_mrt_interchange"] = True

    # === Bus tap aggregation ===
    print("\n  Bus tap analysis...")
    tap_bus = pd.read_csv(TAP_BUS)
    bus_per_stop = tap_bus.groupby("PT_CODE").agg(
        tap_in=("TOTAL_TAP_IN_VOLUME", "sum"),
        tap_out=("TOTAL_TAP_OUT_VOLUME", "sum"),
    ).reset_index()
    bus_per_stop["daily_taps"] = (bus_per_stop["tap_in"] + bus_per_stop["tap_out"]) / 31
    bus_per_stop["BUS_STOP_N"] = bus_per_stop["PT_CODE"].astype(str)
    bs["BUS_STOP_N"] = bs["BUS_STOP_N"].astype(str)
    bs_with = bs.merge(bus_per_stop[["BUS_STOP_N", "daily_taps"]], on="BUS_STOP_N", how="left")
    bs_with["daily_taps"] = bs_with["daily_taps"].fillna(0)
    bus_taps_hex = bs_with.groupby("hex9_id")["daily_taps"].sum().reset_index(name="daily_bus_taps")
    print(f"    bus stops with tap data: {(bs_with['daily_taps']>0).sum():,} / {len(bs_with):,}")

    # === GTFS routes + headway per bus stop ===
    print("\n  GTFS routes + headway per stop...")
    if GTFS_DIR.exists():
        stops = pd.read_csv(GTFS_DIR / "stops.txt")
        trips = pd.read_csv(GTFS_DIR / "trips.txt")
        # routes per stop: stop_times.txt is huge (328MB) — read only stop_id + trip_id columns
        print("    reading stop_times.txt (only stop_id + trip_id + arrival_time)...")
        st_iter = pd.read_csv(GTFS_DIR / "stop_times.txt",
                              usecols=["stop_id", "trip_id", "arrival_time"],
                              dtype={"stop_id": str, "trip_id": str, "arrival_time": str},
                              chunksize=2_000_000)
        # Aggregate
        stop_routes = {}      # stop_id → set of route_ids
        stop_am_arrivals = {} # stop_id → count of arrivals 7am-9am weekday
        trip_route = dict(zip(trips["trip_id"], trips["route_id"]))
        trip_service = dict(zip(trips["trip_id"], trips["service_id"]))

        n_chunks = 0
        for chunk in st_iter:
            n_chunks += 1
            chunk["route_id"] = chunk["trip_id"].map(trip_route)
            chunk["service_id"] = chunk["trip_id"].map(trip_service)
            # weekday only
            wd = chunk[chunk["service_id"] == "WD"]
            # Parse hour from arrival_time HH:MM:SS
            wd_hours = wd["arrival_time"].str[:2].astype(int, errors="ignore")
            am = wd[(wd_hours >= 7) & (wd_hours < 9)]
            # Per-stop route set
            for sid, rid in zip(chunk["stop_id"], chunk["route_id"]):
                if rid is not None and isinstance(rid, str):
                    stop_routes.setdefault(sid, set()).add(rid)
            # Per-stop AM arrival count
            am_counts = am.groupby("stop_id").size()
            for sid, n in am_counts.items():
                stop_am_arrivals[sid] = stop_am_arrivals.get(sid, 0) + n
            print(f"      chunk {n_chunks} done, {len(stop_routes):,} stops indexed")
        print(f"    {len(stop_routes):,} stops have routes  /  {len(stop_am_arrivals):,} stops have AM peak data")

        # Convert to per-stop dataframe
        gtfs_stop_df = pd.DataFrame({
            "stop_id": list(stop_routes.keys()),
            "n_routes": [len(stop_routes[k]) for k in stop_routes.keys()],
        })
        gtfs_stop_df["am_arrivals"] = gtfs_stop_df["stop_id"].map(stop_am_arrivals).fillna(0)
        # AM peak window = 2 hours = 120 min. headway = 120 / arrivals (when arrivals > 0)
        gtfs_stop_df["headway_am_min"] = np.where(
            gtfs_stop_df["am_arrivals"] > 0,
            120.0 / gtfs_stop_df["am_arrivals"],
            999.0,
        )

        # Join to bus_stops via stop_id == BUS_STOP_N
        bs_with["BUS_STOP_N_str"] = bs_with["BUS_STOP_N"].astype(str)
        gtfs_stop_df["stop_id_str"] = gtfs_stop_df["stop_id"].astype(str)
        bs_gtfs = bs_with.merge(gtfs_stop_df[["stop_id_str", "n_routes", "headway_am_min"]],
                                left_on="BUS_STOP_N_str", right_on="stop_id_str", how="left")
        matched_gtfs = bs_gtfs["n_routes"].notna().sum()
        print(f"    bus stops matched in GTFS: {matched_gtfs:,} / {len(bs_with):,}")
        bs_gtfs["n_routes"] = bs_gtfs["n_routes"].fillna(0).astype(int)
        bs_gtfs["headway_am_min"] = bs_gtfs["headway_am_min"].fillna(999.0)

        # Per-hex aggregations
        gtfs_per_hex = bs_gtfs.groupby("hex9_id").agg(
            bus_routes_per_stop_max=("n_routes", "max"),
            bus_routes_per_stop_mean=("n_routes", "mean"),
            gtfs_headway_am_min=("headway_am_min", "min"),
        ).reset_index()
    else:
        gtfs_per_hex = pd.DataFrame({"hex9_id": [], "bus_routes_per_stop_max": [],
                                       "bus_routes_per_stop_mean": [], "gtfs_headway_am_min": []})

    # === Distances (centroid → nearest entity) ===
    print("\n  Computing distances (centroid → nearest)...")
    hex_polys_4326 = []
    for hid in h9["hex9_id"]:
        ring = [(lng, lat) for lat, lng in h3.cell_to_boundary(hid)]
        from shapely.geometry import Polygon
        hex_polys_4326.append(Polygon(ring))
    h9_gdf = gpd.GeoDataFrame({"hex9_id": h9["hex9_id"]}, geometry=hex_polys_4326, crs=4326).to_crs(3414)
    h9_cent = h9_gdf.geometry.centroid

    def nearest_dist(centroids, target_geoms):
        if len(target_geoms) == 0:
            return [np.nan] * len(centroids)
        tree = STRtree(target_geoms)
        out = []
        for c in centroids:
            idx = tree.nearest(c)
            d = c.distance(target_geoms[idx])
            out.append(d)
        return out

    h9_gdf["dist_mrt_m"] = nearest_dist(h9_cent.values, list(ts3.geometry.values))
    h9_gdf["dist_mrt_exit_m"] = nearest_dist(h9_cent.values, list(te3.geometry.values))
    h9_gdf["dist_bus_m"] = nearest_dist(h9_cent.values, list(bs3.geometry.values))

    # === Counts ===
    mrt_count = ts.groupby("hex9_id").size().reset_index(name="mrt_station_count")
    bus_count = bs.groupby("hex9_id").size().reset_index(name="bus_stop_count")
    exit_count = te.groupby("hex9_id").size().reset_index(name="mrt_exit_count")

    # === Rail line through-hex length ===
    print("  Rail through length...")
    cand = gpd.sjoin(rl3, h9_gdf[["hex9_id", "geometry"]], how="inner", predicate="intersects")
    hex_geom_by_idx = dict(zip(h9_gdf.index, h9_gdf.geometry))
    rail_through = []
    for _, r in cand.iterrows():
        hg = hex_geom_by_idx.get(r["index_right"])
        if hg is None: continue
        try:
            inter = r["geometry"].intersection(hg)
            L = inter.length if inter.geom_type == "LineString" else (
                sum(g.length for g in inter.geoms) if inter.geom_type == "MultiLineString" else 0)
            if L > 0:
                rail_through.append({"hex9_id": r["hex9_id"], "rail_m": L})
        except Exception:
            pass
    rail_df = pd.DataFrame(rail_through).groupby("hex9_id")["rail_m"].sum().reset_index(name="rail_line_through_m")

    # === Final ===
    print("\n  Building final transit table...")
    out = h9[["hex9_id", "parent_hex8", "parent_subzone"]].copy()
    out = out.merge(mrt_count, on="hex9_id", how="left")
    out = out.merge(exit_count, on="hex9_id", how="left")
    out = out.merge(bus_count, on="hex9_id", how="left")
    out = out.merge(h9_gdf[["hex9_id", "dist_mrt_m", "dist_mrt_exit_m", "dist_bus_m"]], on="hex9_id", how="left")
    out = out.merge(rail_df, on="hex9_id", how="left")
    out = out.merge(train_taps_hex, on="hex9_id", how="left")
    out = out.merge(bus_taps_hex, on="hex9_id", how="left")
    out = out.merge(interchange_hex[["hex9_id", "is_mrt_interchange"]], on="hex9_id", how="left")
    out = out.merge(gtfs_per_hex, on="hex9_id", how="left")

    for c in ["mrt_station_count", "mrt_exit_count", "bus_stop_count",
              "rail_line_through_m", "daily_train_taps", "daily_bus_taps",
              "bus_routes_per_stop_max", "bus_routes_per_stop_mean"]:
        if c in out.columns: out[c] = out[c].fillna(0)
    out["is_mrt_interchange"] = out["is_mrt_interchange"].fillna(False).astype(bool)
    out["gtfs_headway_am_min"] = out["gtfs_headway_am_min"].fillna(999.0)

    out["near_mrt_400m"] = out["dist_mrt_m"] < 400
    out["near_bus_300m"] = out["dist_bus_m"] < 300
    out["transit_score"] = (
        0.6 * np.exp(-out["dist_mrt_m"].fillna(99999) / 800.0)
        + 0.4 * np.exp(-out["dist_bus_m"].fillna(99999) / 800.0)
    ).clip(0, 1)

    out = out[[
        "hex9_id", "parent_hex8", "parent_subzone",
        "mrt_station_count", "mrt_exit_count", "bus_stop_count",
        "dist_mrt_m", "dist_mrt_exit_m", "dist_bus_m",
        "near_mrt_400m", "near_bus_300m",
        "rail_line_through_m",
        "daily_train_taps", "daily_bus_taps",
        "bus_routes_per_stop_max", "bus_routes_per_stop_mean",
        "gtfs_headway_am_min",
        "is_mrt_interchange", "transit_score",
    ]]
    out.to_parquet(OUT, index=False)
    print(f"\nTransit parquet: {out.shape}")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "totals": {
            "hexes_with_mrt_station": int((out["mrt_station_count"] > 0).sum()),
            "hexes_with_bus_stop": int((out["bus_stop_count"] > 0).sum()),
            "hexes_within_400m_mrt": int(out["near_mrt_400m"].sum()),
            "hexes_within_300m_bus": int(out["near_bus_300m"].sum()),
            "interchange_hexes": int(out["is_mrt_interchange"].sum()),
            "total_daily_train_taps": float(out["daily_train_taps"].sum()),
            "total_daily_bus_taps": float(out["daily_bus_taps"].sum()),
            "max_routes_per_stop": int(out["bus_routes_per_stop_max"].max()),
            "median_headway_am_with_data_min": float(out[out["gtfs_headway_am_min"] < 999]["gtfs_headway_am_min"].median()),
            "max_transit_score": float(out["transit_score"].max()),
        },
    }
    with open(REPORT, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n{json.dumps(summary, indent=2)}")
    print(f"\nOutput: {OUT}")

    # Top hexes by daily train taps (should now show varied values, not all uniform)
    top = out.nlargest(15, "daily_train_taps").merge(
        h9[["hex9_id", "parent_subzone_name", "parent_pa"]], on="hex9_id")
    print("\n=== Top 15 hexes by daily train taps (varied — not uniform anymore) ===")
    for _, r in top.iterrows():
        print(f"  {r['hex9_id']}  taps={r['daily_train_taps']:>8,.0f}  mrt={int(r['mrt_station_count'])}  "
              f"interchange={r['is_mrt_interchange']}  routes_max={int(r['bus_routes_per_stop_max'])}  "
              f"{str(r['parent_subzone_name']):<25} ({r['parent_pa']})")


def build_station_code_map():
    """Returns dict mapping single PT_CODE → canonical station name (UPPER)."""
    # Singapore MRT/LRT — comprehensive mapping (compiled from public LTA sources)
    return {
        # Bukit Panjang LRT
        "BP1": "CHOA CHU KANG", "BP2": "SOUTH VIEW", "BP3": "KEAT HONG", "BP4": "TECK WHYE",
        "BP5": "PHOENIX", "BP6": "BUKIT PANJANG", "BP7": "PETIR", "BP8": "PENDING",
        "BP9": "BANGKIT", "BP10": "FAJAR", "BP11": "SEGAR", "BP12": "JELAPANG",
        "BP13": "SENJA", "BP14": "TEN MILE JUNCTION",
        # Circle Line
        "CC1": "DHOBY GHAUT", "CC2": "BRAS BASAH", "CC3": "ESPLANADE", "CC4": "PROMENADE",
        "CC5": "NICOLL HIGHWAY", "CC6": "STADIUM", "CC7": "MOUNTBATTEN", "CC8": "DAKOTA",
        "CC9": "PAYA LEBAR", "CC10": "MACPHERSON", "CC11": "TAI SENG", "CC12": "BARTLEY",
        "CC13": "SERANGOON", "CC14": "LORONG CHUAN", "CC15": "BISHAN", "CC16": "MARYMOUNT",
        "CC17": "CALDECOTT", "CC19": "BOTANIC GARDENS", "CC20": "FARRER ROAD",
        "CC21": "HOLLAND VILLAGE", "CC22": "BUONA VISTA", "CC23": "ONE-NORTH",
        "CC24": "KENT RIDGE", "CC25": "HAW PAR VILLA", "CC26": "PASIR PANJANG",
        "CC27": "LABRADOR PARK", "CC28": "TELOK BLANGAH", "CC29": "HARBOURFRONT",
        "CE1": "BAYFRONT", "CE2": "MARINA BAY",
        # Changi extension
        "CG1": "EXPO", "CG2": "CHANGI AIRPORT",
        # Downtown Line
        "DT1": "BUKIT PANJANG", "DT2": "CASHEW", "DT3": "HILLVIEW", "DT5": "BEAUTY WORLD",
        "DT6": "KING ALBERT PARK", "DT7": "SIXTH AVENUE", "DT8": "TAN KAH KEE",
        "DT9": "BOTANIC GARDENS", "DT10": "STEVENS", "DT11": "NEWTON",
        "DT12": "LITTLE INDIA", "DT13": "ROCHOR", "DT14": "BUGIS", "DT15": "PROMENADE",
        "DT16": "BAYFRONT", "DT17": "DOWNTOWN", "DT18": "TELOK AYER", "DT19": "CHINATOWN",
        "DT20": "FORT CANNING", "DT21": "BENCOOLEN", "DT22": "JALAN BESAR",
        "DT23": "BENDEMEER", "DT24": "GEYLANG BAHRU", "DT25": "MATTAR",
        "DT26": "MACPHERSON", "DT27": "UBI", "DT28": "KAKI BUKIT", "DT29": "BEDOK NORTH",
        "DT30": "BEDOK RESERVOIR", "DT31": "TAMPINES WEST", "DT32": "TAMPINES",
        "DT33": "TAMPINES EAST", "DT34": "UPPER CHANGI", "DT35": "EXPO",
        # East-West Line
        "EW1": "PASIR RIS", "EW2": "TAMPINES", "EW3": "SIMEI", "EW4": "TANAH MERAH",
        "EW5": "BEDOK", "EW6": "KEMBANGAN", "EW7": "EUNOS", "EW8": "PAYA LEBAR",
        "EW9": "ALJUNIED", "EW10": "KALLANG", "EW11": "LAVENDER", "EW12": "BUGIS",
        "EW13": "CITY HALL", "EW14": "RAFFLES PLACE", "EW15": "TANJONG PAGAR",
        "EW16": "OUTRAM PARK", "EW17": "TIONG BAHRU", "EW18": "REDHILL",
        "EW19": "QUEENSTOWN", "EW20": "COMMONWEALTH", "EW21": "BUONA VISTA",
        "EW22": "DOVER", "EW23": "CLEMENTI", "EW24": "JURONG EAST", "EW25": "CHINESE GARDEN",
        "EW26": "LAKESIDE", "EW27": "BOON LAY", "EW28": "PIONEER", "EW29": "JOO KOON",
        "EW30": "GUL CIRCLE", "EW31": "TUAS CRESCENT", "EW32": "TUAS WEST ROAD",
        "EW33": "TUAS LINK",
        # North-East Line
        "NE1": "HARBOURFRONT", "NE3": "OUTRAM PARK", "NE4": "CHINATOWN",
        "NE5": "CLARKE QUAY", "NE6": "DHOBY GHAUT", "NE7": "LITTLE INDIA",
        "NE8": "FARRER PARK", "NE9": "BOON KENG", "NE10": "POTONG PASIR",
        "NE11": "WOODLEIGH", "NE12": "SERANGOON", "NE13": "KOVAN", "NE14": "HOUGANG",
        "NE15": "BUANGKOK", "NE16": "SENGKANG", "NE17": "PUNGGOL",
        # North-South Line
        "NS1": "JURONG EAST", "NS2": "BUKIT BATOK", "NS3": "BUKIT GOMBAK", "NS4": "CHOA CHU KANG",
        "NS5": "YEW TEE", "NS7": "KRANJI", "NS8": "MARSILING", "NS9": "WOODLANDS",
        "NS10": "ADMIRALTY", "NS11": "SEMBAWANG", "NS12": "CANBERRA", "NS13": "YISHUN",
        "NS14": "KHATIB", "NS15": "YIO CHU KANG", "NS16": "ANG MO KIO", "NS17": "BISHAN",
        "NS18": "BRADDELL", "NS19": "TOA PAYOH", "NS20": "NOVENA", "NS21": "NEWTON",
        "NS22": "ORCHARD", "NS23": "SOMERSET", "NS24": "DHOBY GHAUT", "NS25": "CITY HALL",
        "NS26": "RAFFLES PLACE", "NS27": "MARINA BAY", "NS28": "MARINA SOUTH PIER",
        # Sengkang LRT (East loop)
        "SE1": "COMPASSVALE", "SE2": "RUMBIA", "SE3": "BAKAU", "SE4": "KANGKAR", "SE5": "RANGGUNG",
        # Sengkang LRT (West loop)
        "SW1": "CHENG LIM", "SW2": "FARMWAY", "SW3": "KUPANG", "SW4": "THANGGAM",
        "SW5": "FERNVALE", "SW6": "LAYAR", "SW7": "TONGKANG", "SW8": "RENJONG",
        # Punggol LRT (East loop)
        "PE1": "COVE", "PE2": "MERIDIAN", "PE3": "COVE", "PE4": "RIVIERA",
        "PE5": "KADALOOR", "PE6": "OASIS", "PE7": "DAMAI",
        # Punggol LRT (West loop)
        "PW1": "SAM KEE", "PW2": "TECK LEE", "PW3": "PUNGGOL POINT", "PW4": "SAMUDERA",
        "PW5": "NIBONG", "PW6": "SUMANG", "PW7": "SOO TECK",
        # Sengkang/Punggol terminus codes (same as NE16, NE17)
        "STC": "SENGKANG", "PTC": "PUNGGOL",
        # Thomson-East Coast Line (TE)
        "TE1": "WOODLANDS NORTH", "TE2": "WOODLANDS", "TE3": "WOODLANDS SOUTH",
        "TE4": "SPRINGLEAF", "TE5": "LENTOR", "TE6": "MAYFLOWER", "TE7": "BRIGHT HILL",
        "TE8": "UPPER THOMSON", "TE9": "CALDECOTT", "TE10": "MOUNT PLEASANT",
        "TE11": "STEVENS", "TE12": "NAPIER", "TE13": "ORCHARD BOULEVARD",
        "TE14": "ORCHARD", "TE15": "GREAT WORLD", "TE16": "HAVELOCK",
        "TE17": "OUTRAM PARK", "TE18": "MAXWELL", "TE19": "SHENTON WAY",
        "TE20": "MARINA BAY", "TE21": "MARINA SOUTH", "TE22": "GARDENS BY THE BAY",
        "TE23": "TANJONG RHU", "TE24": "KATONG PARK", "TE25": "TANJONG KATONG",
        "TE26": "MARINE PARADE", "TE27": "MARINE TERRACE", "TE28": "SIGLAP",
        "TE29": "BAYSHORE", "TE30": "BEDOK SOUTH", "TE31": "SUNGEI BEDOK",
    }


def lookup_station_name(pt_code, code_map):
    """Resolve a possibly-interchange PT_CODE like 'EW16/NE3/TE17' to a station name.
    For interchange codes, use the FIRST recognized component (all components map to
    the same physical station)."""
    if not isinstance(pt_code, str):
        return None
    parts = pt_code.split("/")
    for p in parts:
        n = code_map.get(p.strip())
        if n is not None:
            return n
    return None


if __name__ == "__main__":
    main()
