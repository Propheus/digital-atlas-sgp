"""Shared constants & helpers for the Active School Travel Space (ASTS) replication.

Replicates: Land 2024, 13(8), 1319 — "Evaluating the Quality of Children's
Active School Travel Spaces and the Mechanisms of School District Friendliness
Impact Based on Multi-Source Big Data" (Lanzhou, 151 primary schools).

Singapore adaptation: 179 MOE primary schools, MOE home-school distance priority
tiers (1 km / 2 km) as the catchment definition.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # repo root
PKG  = Path(__file__).resolve().parents[1]           # school_travel_friendliness/
DATA = PKG / "data"
OUT  = PKG / "output"
DATA.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)

# Coordinate systems
WGS84 = "EPSG:4326"
SVY21 = "EPSG:3414"        # Singapore metric projection (SVY21 / National Grid)

# MOE home-school distance priority tiers (Phase 2A/2C registration)
TIER_INNER_M = 1000        # 1 km priority band
TIER_OUTER_M = 2000        # 2 km priority band
CATCHMENT_M  = TIER_INNER_M   # default catchment = 1 km network distance

# Source data paths (relative to repo root)
SRC = {
    "schools":   ROOT / "data/amenities/schools_geocoded.json",
    "footpath":  ROOT / "data/lta_datamall/2026-05/footpath_mar2026.geojson",
    "crossing":  ROOT / "data/lta_datamall/2026-05/roadcrossing_mar2026.geojson",
    "signals":   ROOT / "data/transit/traffic_signals.geojson",
    "parks":     ROOT / "data/amenities/parks_nature_reserves.geojson",
    "pcn":       ROOT / "data/amenities/park_connector.geojson",
    "bus":       ROOT / "data/transit/bus_stops_mar2026.geojson",
    "mrt":       ROOT / "data/transit/train_stations_mar2026.geojson",
    "subzone_pop": ROOT / "data/hex_v11/subzone_population.parquet",
}

# Derived artifact paths
ART = {
    "schools":     DATA / "primary_schools.geojson",
    "walk_graph":  DATA / "sg_walk.graphml",
    "syntax_nodes":DATA / "syntax_nodes.gpkg",      # cityseer node metrics
    "catchments":  DATA / "catchments.gpkg",
    "index":       OUT  / "friendliness_index.csv",
    "index_gj":    OUT  / "friendliness_index.geojson",
    "geodetector": OUT  / "geodetector.csv",
}
