"""Shared constants & paths — SERVER edition (azold-test-server).

Replicates Land 2024 13(8):1319 (Active School Travel Space friendliness, Lanzhou)
for Singapore. Runs entirely on azold-test-server using the v4 atlas data
(/home/azureuser/da-sgp/v4) plus OSM layers downloaded on the server.
"""
from pathlib import Path

V4   = Path("/home/azureuser/da-sgp/v4")
PKG  = Path("/home/azureuser/da-sgp/asts")
DATA = PKG / "data"
OUT  = PKG / "output"
DATA.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

WGS84 = "EPSG:4326"
SVY21 = "EPSG:3414"          # Singapore metric grid

# MOE home-school distance priority tiers
CATCHMENT_M  = 1000          # catchment = 1 km network distance
CORRIDOR_BUF_M = 40
SYNTAX_DIST  = [800, 1600]

# Singapore bbox (west, south, east, north) for osmnx 2.x
BBOX = (103.590, 1.205, 104.050, 1.480)

# Server-native source data
SRC = {
    "places":      V4 / "places/sgp_places_final.parquet",
    "subzones":    V4 / "boundaries/subzones.geojson",
    "subzone_pop": V4 / "hex/subzone_population.parquet",
}

ART = {
    "schools":     DATA / "primary_schools.geojson",
    "walk_graph":  DATA / "sg_walk.graphml",
    "crossings":   DATA / "osm_crossings.gpkg",
    "signals":     DATA / "osm_signals.gpkg",
    "parks":       DATA / "osm_parks.gpkg",
    "bus":         DATA / "osm_bus.gpkg",
    "mrt":         DATA / "osm_mrt.gpkg",
    "syntax_nodes":DATA / "syntax_nodes.gpkg",
    "catchments":  DATA / "catchments.gpkg",
    "index":       OUT  / "friendliness_index.csv",
    "index_gj":    OUT  / "friendliness_index.geojson",
    "geodetector": OUT  / "geodetector.csv",
}
