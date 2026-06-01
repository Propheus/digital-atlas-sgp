# Plexis SGP v4 — Dataset Catalog

**Generated:** 2026-04-29 04:18 · **Datasets:** 34 (34 existing)

## scale = `hex9`

| Dataset | Rows × Cols | Join key | Owner | Description |
|---|---|---|---|---|
| `hex/hex9_all_features.parquet` | 7,318 × 114 | `hex9_id` | `all` | MASTER — all standalone layers joined per hex-9 |
| `hex/hex9_buildings.parquet` | 7,318 × 39 | `hex9_id` | `2` | Buildings (counts, classes, floors, HDB) per hex-9 |
| `hex/hex9_buildings_clean.parquet` | 7,318 × 20 | `hex9_id` | `2c` | Buildings clean (clipped, est-FAR, HDB age) per hex-9 |
| `hex/hex9_built_environment_features.parquet` | 7,318 × 41 | `hex9_id` | `24` | BUNDLE — buildings + land_use per hex-9 |
| `hex/hex9_land_use.parquet` | 7,318 × 22 | `hex9_id` | `4` | URA land-use 14-bucket shares per hex-9 |
| `hex/hex9_mobility_features.parquet` | 7,318 × 53 | `hex9_id` | `56` | BUNDLE — roads + transit + walkability per hex-9 |
| `hex/hex9_population.parquet` | 7,318 × 14 | `hex9_id` | `3+3b` | Population (residents + non-residents) per hex-9 |
| `hex/hex9_roads_clean.parquet` | 7,318 × 18 | `hex9_id` | `6+6c` | Roads + parking + centrality (clean) per hex-9 |
| `hex/hex9_satellite.parquet` | 7,318 × 11 | `hex9_id` | `5b` | VIIRS night lights + WorldPop per hex-9 |
| `hex/hex9_transit_clean.parquet` | 7,318 × 19 | `hex9_id` | `5+5c` | Transit (MRT/LRT/bus/GTFS/ridership) per hex-9 |
| `hex/hex9_universe.parquet` | 7,318 × 8 | `hex9_id` | `0` | Hex-9 cell universe (7,318 cells across SGP) |
| `hex/hex9_walkability.parquet` | 7,318 × 27 | `hex9_id` | `7w` | Walkability composite + amenity walk distances per hex-9 |

## scale = `hex8`

| Dataset | Rows × Cols | Join key | Owner | Description |
|---|---|---|---|---|
| `hex/hex8_all_features.parquet` | 1,191 × 110 | `hex8_id` | `all` | MASTER — all standalone layers joined per hex-8 |
| `hex/hex8_buildings_clean.parquet` | 1,191 × 19 | `hex8_id` | `2c` | Buildings clean aggregated to hex-8 |
| `hex/hex8_built_environment_features.parquet` | 1,191 × 40 | `hex8_id` | `24` | BUNDLE — buildings + land_use aggregated to hex-8 |
| `hex/hex8_land_use.parquet` | 1,191 × 22 | `hex8_id` | `4agg` | URA land-use aggregated to hex-8 (area-weighted) |
| `hex/hex8_mobility_features.parquet` | 1,191 × 50 | `hex8_id` | `56` | BUNDLE — roads + transit + walkability aggregated to hex-8 |
| `hex/hex8_population.parquet` | 1,191 × 17 | `hex8_id` | `3agg` | Population aggregated to hex-8 |
| `hex/hex8_roads_clean.parquet` | 1,191 × 18 | `hex8_id` | `6c` | Roads + parking + centrality aggregated to hex-8 |
| `hex/hex8_satellite.parquet` | 1,191 × 9 | `hex8_id` | `5b` | VIIRS + WorldPop aggregated to hex-8 |
| `hex/hex8_transit_clean.parquet` | 1,191 × 18 | `hex8_id` | `5c` | Transit aggregated to hex-8 |
| `hex/hex8_universe.parquet` | 1,191 × 7 | `hex8_id` | `0` | Hex-8 cell universe (1,191 cells) |
| `hex/hex8_walkability.parquet` | 1,191 × 21 | `hex8_id` | `7w` | Walkability aggregated to hex-8 |

## scale = `subzone`

| Dataset | Rows × Cols | Join key | Owner | Description |
|---|---|---|---|---|
| `hex/subzone_all_features.parquet` | 326 × 88 | `subzone_c` | `all` | MASTER — all standalone layers joined per subzone |
| `hex/subzone_buildings_clean.parquet` | 270 × 17 | `subzone_c` | `2c` | Buildings clean aggregated to subzone |
| `hex/subzone_built_environment_features.parquet` | 270 × 38 | `subzone_c` | `24` | BUNDLE — buildings + land_use aggregated to subzone |
| `hex/subzone_land_use.parquet` | 326 × 22 | `subzone_c` | `4agg` | URA land-use aggregated to subzone (area-weighted) |
| `hex/subzone_mobility_features.parquet` | 270 × 38 | `subzone_c` | `56` | BUNDLE — roads + transit + walkability aggregated to subzone |
| `hex/subzone_population.parquet` | 326 × 11 | `subzone_c` | `3agg` | Population aggregated to subzone |
| `hex/subzone_roads_clean.parquet` | 270 × 18 | `subzone_c` | `6c` | Roads + parking + centrality aggregated to subzone |
| `hex/subzone_satellite.parquet` | 326 × 9 | `subzone_c` | `5b` | VIIRS + WorldPop aggregated to subzone |
| `hex/subzone_transit_clean.parquet` | 270 × 14 | `subzone_c` | `5c` | Transit aggregated to subzone |
| `hex/subzone_walkability.parquet` | 270 × 8 | `subzone_c` | `7w` | Walkability aggregated to subzone |

## scale = `place`

| Dataset | Rows × Cols | Join key | Owner | Description |
|---|---|---|---|---|
| `places/sgp_places_final.parquet` | 190,591 × 27 | `hex9_id` | `1` | Stage-1 deliverable: 190,591 places × 27 cols (geo + cat + brand + quality) |
