# Plexis SGP — Checkpoint v4.0.2

**Generated:** 2026-04-29T04:18:15  
**Pipeline total:** 228s = 3.8 min  
**Datasets:** 34 (in catalog) · **Features:** 1007 (931 with curated descriptions)  
**Files indexed:** 107 · **Total size:** 248.0 MB

## Pipeline stages

| Stage | Status | Time (s) |
|---|---|---|
| 0 | PASS | 7.0 |
| 0b | PASS | 23.5 |
| 0c | PASS | 23.6 |
| 1a | PASS | 18.3 |
| 1b1 | PASS | 0.7 |
| 1b2 | PASS | 2.5 |
| 1bf | PASS | 0.5 |
| 1c | PASS | 7.6 |
| 1d | PASS | 0.7 |
| 2 | PASS | 3.0 |
| 3 | PASS | 5.9 |
| 4 | PASS | 18.5 |
| 3b | PASS | 0.5 |
| 6 | PASS | 75.1 |
| 6c | PASS | 1.4 |
| 5 | PASS | 18.8 |
| 5c | PASS | 0.5 |

## Validators

| Validator | Pass | Warn | Fail | Total |
|---|---|---|---|---|
| `buildings_clean_validation` | 5 | 1 | 0 | 6 |
| `population_validation` | 6 | 0 | 0 | 6 |
| `land_use_validation` | 6 | 0 | 0 | 6 |
| `road_centrality_validation` | 4 | 1 | 0 | 5 |
| `non_resident_validation` | 5 | 0 | 0 | 5 |
| `buildings_validation` | 5 | 1 | 0 | 6 |
| `transit_validation` | 6 | 0 | 0 | 6 |
| `satellite_validation` | 3 | 2 | 0 | 5 |
| `roads_validation` | 6 | 2 | 0 | 8 |

## Datasets in catalog

| Dataset | Scale | Rows × Cols | Owner | Description |
|---|---|---|---|---|
| `hex/hex8_all_features.parquet` | hex8 | 1,191 × 110 | all | MASTER — all standalone layers joined per hex-8 |
| `hex/hex8_buildings_clean.parquet` | hex8 | 1,191 × 19 | 2c | Buildings clean aggregated to hex-8 |
| `hex/hex8_built_environment_features.parquet` | hex8 | 1,191 × 40 | 24 | BUNDLE — buildings + land_use aggregated to hex-8 |
| `hex/hex8_land_use.parquet` | hex8 | 1,191 × 22 | 4agg | URA land-use aggregated to hex-8 (area-weighted) |
| `hex/hex8_mobility_features.parquet` | hex8 | 1,191 × 50 | 56 | BUNDLE — roads + transit + walkability aggregated to hex-8 |
| `hex/hex8_population.parquet` | hex8 | 1,191 × 17 | 3agg | Population aggregated to hex-8 |
| `hex/hex8_roads_clean.parquet` | hex8 | 1,191 × 18 | 6c | Roads + parking + centrality aggregated to hex-8 |
| `hex/hex8_satellite.parquet` | hex8 | 1,191 × 9 | 5b | VIIRS + WorldPop aggregated to hex-8 |
| `hex/hex8_transit_clean.parquet` | hex8 | 1,191 × 18 | 5c | Transit aggregated to hex-8 |
| `hex/hex8_universe.parquet` | hex8 | 1,191 × 7 | 0 | Hex-8 cell universe (1,191 cells) |
| `hex/hex8_walkability.parquet` | hex8 | 1,191 × 21 | 7w | Walkability aggregated to hex-8 |
| `hex/hex9_all_features.parquet` | hex9 | 7,318 × 114 | all | MASTER — all standalone layers joined per hex-9 |
| `hex/hex9_buildings.parquet` | hex9 | 7,318 × 39 | 2 | Buildings (counts, classes, floors, HDB) per hex-9 |
| `hex/hex9_buildings_clean.parquet` | hex9 | 7,318 × 20 | 2c | Buildings clean (clipped, est-FAR, HDB age) per hex-9 |
| `hex/hex9_built_environment_features.parquet` | hex9 | 7,318 × 41 | 24 | BUNDLE — buildings + land_use per hex-9 |
| `hex/hex9_land_use.parquet` | hex9 | 7,318 × 22 | 4 | URA land-use 14-bucket shares per hex-9 |
| `hex/hex9_mobility_features.parquet` | hex9 | 7,318 × 53 | 56 | BUNDLE — roads + transit + walkability per hex-9 |
| `hex/hex9_population.parquet` | hex9 | 7,318 × 14 | 3+3b | Population (residents + non-residents) per hex-9 |
| `hex/hex9_roads_clean.parquet` | hex9 | 7,318 × 18 | 6+6c | Roads + parking + centrality (clean) per hex-9 |
| `hex/hex9_satellite.parquet` | hex9 | 7,318 × 11 | 5b | VIIRS night lights + WorldPop per hex-9 |
| `hex/hex9_transit_clean.parquet` | hex9 | 7,318 × 19 | 5+5c | Transit (MRT/LRT/bus/GTFS/ridership) per hex-9 |
| `hex/hex9_universe.parquet` | hex9 | 7,318 × 8 | 0 | Hex-9 cell universe (7,318 cells across SGP) |
| `hex/hex9_walkability.parquet` | hex9 | 7,318 × 27 | 7w | Walkability composite + amenity walk distances per hex-9 |
| `places/sgp_places_final.parquet` | place | 190,591 × 27 | 1 | Stage-1 deliverable: 190,591 places × 27 cols (geo + cat + brand + quality) |
| `hex/subzone_all_features.parquet` | subzone | 326 × 88 | all | MASTER — all standalone layers joined per subzone |
| `hex/subzone_buildings_clean.parquet` | subzone | 270 × 17 | 2c | Buildings clean aggregated to subzone |
| `hex/subzone_built_environment_features.parquet` | subzone | 270 × 38 | 24 | BUNDLE — buildings + land_use aggregated to subzone |
| `hex/subzone_land_use.parquet` | subzone | 326 × 22 | 4agg | URA land-use aggregated to subzone (area-weighted) |
| `hex/subzone_mobility_features.parquet` | subzone | 270 × 38 | 56 | BUNDLE — roads + transit + walkability aggregated to subzone |
| `hex/subzone_population.parquet` | subzone | 326 × 11 | 3agg | Population aggregated to subzone |
| `hex/subzone_roads_clean.parquet` | subzone | 270 × 18 | 6c | Roads + parking + centrality aggregated to subzone |
| `hex/subzone_satellite.parquet` | subzone | 326 × 9 | 5b | VIIRS + WorldPop aggregated to subzone |
| `hex/subzone_transit_clean.parquet` | subzone | 270 × 14 | 5c | Transit aggregated to subzone |
| `hex/subzone_walkability.parquet` | subzone | 270 × 8 | 7w | Walkability aggregated to subzone |

## Top 15 files by size

| Path | Size (MB) |
|---|---|
| `places/sgp_places_geoattached.jsonl` | 111.5 |
| `places/sgp_place_V1.jsonl` | 61.2 |
| `places/sgp_places_final.parquet` | 12.0 |
| `places/sgp_places_branded.parquet` | 10.9 |
| `places/sgp_places_categorized.parquet` | 10.9 |
| `places/sgp_places_geoattached.parquet` | 10.7 |
| `hex/hex9_universe.geojson` | 3.5 |
| `boundaries/subzones.geojson` | 3.2 |
| `hex/hex9_all_features.parquet` | 2.7 |
| `places/sgp_places_unresolved_category.parquet` | 2.4 |
| `boundaries/planning_areas.geojson` | 1.8 |
| `hex/hex9_roads.parquet` | 1.5 |
| `hex/hex9_roads_raw.parquet` | 1.5 |
| `hex/hex9_mobility_features.parquet` | 1.4 |
| `boundaries/hdb_towns.geojson` | 1.3 |

---

_Checkpoint manifest: `CHECKPOINT_v4.0.2.json`. Atlas-1 backup: `plexis-sgp-v4.0.2.tar.gz`._