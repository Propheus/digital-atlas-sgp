# Plexis SGP v4 — Feature Catalog

**Generated:** 2026-04-29 04:18 · **Features:** 1,007

## `hex/hex8_all_features.parquet`

_110 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `avg_gpr` | float64 | ratio | 0.0 | 0 → 11.03 (median 0.5845) | Area-weighted Gross Plot Ratio |
| `best_max_floors` | float64 | floors | 0.0 | 0 → 70 (median 0) | Max floor count (Overture or HDB authoritative) |
| `bldg_commercial_count` | float64 | count | 0.0 | 0 → 191 (median 0) | Commercial buildings |
| `bldg_count` | float64 | count | 0.0 | 0 → 1968 (median 136) | Building footprints in hex (Overture + HDB + OSM) |
| `bldg_density_per_km2` | float64 | count/km² | 0.0 | 0 → 2670 (median 184.5) | Buildings per km² |
| `bldg_footprint_m2` | float64 | m² | 0.0 | 0 → 4.288e+05 (median 4.936e+04) | Total clipped building footprint area in hex |
| `bldg_footprint_share` | float64 | ratio [0,1] | 0.0 | 0 → 0.5818 (median 0.067) | Footprint as fraction of hex area (clipped, ≤1) |
| `bldg_industrial_count` | float64 | count | 0.0 | 0 → 165 (median 0) | Industrial buildings |
| `bldg_institutional_count` | float64 | count | 0.0 | 0 → 45 (median 0) | Institutional buildings |
| `bldg_residential_count` | float64 | count | 0.0 | 0 → 1084 (median 0) | Residential buildings |
| `bridge_length_m` | float64 | m | 0.0 | 0 → 1.07e+04 (median 89.88) | Bridge segment length |
| `bus_routes_per_stop_max` | float64 | count | 0.0 | 0 → 50 (median 0) | Max # routes serving a stop in hex (GTFS) |
| `bus_routes_per_stop_mean` | float64 | count | 0.0 | 0 → 20.36 (median 0) | Mean routes/stop in hex |
| `bus_stop_count` | float64 | count | 0.0 | 0 → 31 (median 0) | Bus stops in hex |
| `centr_betweenness_max` | float64 | ratio | 0.0 | 0 → 0.108 (median 0) | Max betweenness centrality of major-road nodes |
| `centr_bridge_count` | float64 | count | 0.0 | 0 → 64 (median 0) | Tarjan bridge endpoints (network cut points) |
| `daily_bus_taps` | float64 | taps/day | 0.0 | 0 → 1.187e+05 (median 0) | Daily bus taps (Dec 2025 LTA monthly / 31) |
| `daily_train_taps` | float64 | taps/day | 0.0 | 0 → 2.476e+05 (median 0) | Daily MRT/LRT taps (Jan 2026 LTA monthly / 31) |
| `dist_bus_m` | float64 | m | 0.0 | 5.326 → 1.336e+04 (median 281.7) | Centroid distance to nearest bus stop |
| `dist_expressway_m` | float64 | m | 0.0 | 0.00143 → 1.372e+04 (median 1503) | Centroid distance to nearest motorway/trunk segment |
| `dist_mrt_exit_m` | float64 | m | 0.0 | 7.807 → 1.376e+04 (median 1731) | Centroid distance to nearest MRT exit |
| `dist_mrt_m` | float64 | m | 0.0 | 0 → 1.373e+04 (median 1655) | Centroid distance to nearest MRT/LRT station |
| `dist_walk_clinic_m` | float64 | m | 0.0 | 1.673 → 1.599e+04 (median 915.2) | Walk distance to nearest clinic |
| `dist_walk_food_m` | float64 | m | 0.0 | 1.963 → 1.596e+04 (median 385.1) | Walk distance to nearest restaurant/cafe/hawker/bakery/fast-food |
| `dist_walk_hawker_m` | float64 | m | 0.0 | 1.963 → 1.599e+04 (median 1046) | Walk distance to nearest hawker (Euclidean × 1.3 detour) |
| `dist_walk_park_m` | float64 | m | 0.0 | 0 → 2.054e+04 (median 1037) | Walk distance to nearest park |
| `dist_walk_school_m` | float64 | m | 0.0 | 2.142 → 1.581e+04 (median 610.4) | Walk distance to nearest school |
| `dist_walk_supermarket_m` | float64 | m | 0.0 | 4.861 → 1.79e+04 (median 857.1) | Walk distance to nearest supermarket |
| `dominant_use` | str | categorical | 0.0 | 11 unique · `transport` | Bucket with highest area share |
| `est_built_far` | float64 | ratio | 0.0 | 0 → 3.686 (median 0.2114) | Estimated built-up FAR = total floor area / hex area |
| `est_total_floor_area_m2` | float64 | m² | 0.0 | 0 → 2.716e+06 (median 1.558e+05) | Sum of footprint × est_floors per building |
| `expressway_severance` | bool | bool | 0.0 | 0 → 1 (median 0) | Expressway < 200m AND no exit < 400m (barrier without benefit) |
| `gtfs_headway_am_min` | float64 | min | 0.0 | 0.1389 → 999 (median 999) | Best AM-peak headway (lowest minutes between buses) at any stop in hex |
| `hdb_avg_age_years` | float64 | years | 0.0 | 0 → 63.75 (median 0) | Avg years since HDB completion (year_completed filtered ≥1960) |
| `hdb_block_count` | float64 | count | 0.0 | 0 → 147 (median 0) | HDB blocks (authoritative) |
| `hdb_dwelling_units` | float64 | count | 0.0 | 0 → 1.319e+04 (median 0) | Total dwelling units across HDB blocks |
| `hdb_max_floors` | float64 | floors | 0.0 | 0 → 50 (median 0) | Max HDB floor count |
| `hdb_mscp_count` | float64 | count | 0.0 | 0 → 23 (median 0) | Authoritative HDB multi-storey carparks |
| `hex8_id` | str | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `is_highrise` | bool | bool | 0.0 | 0 → 1 (median 0) | True if max_floors >= 10 |
| `is_mrt_interchange` | bool | bool | 0.0 | 0 → 1 (median 0) | True if any station has ≥2 lines (slash-PT_CODE) |
| `lane_km_per_km2` | float64 | km/km² | 0.0 | 0 → 97.19 (median 22.81) | Lane-km per km² (lane count × length / area) |
| `lat` | float64 | degrees | 0.0 | 1.159 → 1.47 (median 1.349) | Hex centroid latitude |
| `lng` | float64 | degrees | 0.0 | 103.6 → 104.1 (median 103.8) | Hex centroid longitude |
| `lu_business_park_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.523 (median 0) | Business park share |
| `lu_business_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Land area share zoned business (industrial) |
| `lu_commercial_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.4744 (median 0) | Land area share zoned commercial |
| `lu_educational_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.7291 (median 0) | Educational institution share |
| `lu_entropy` | float64 | nats | 0.0 | -0 → 2.09 (median 0.6931) | Shannon entropy across 14 LU buckets |
| `lu_health_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.2255 (median 0) | Health & medical share |
| `lu_hotel_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.2884 (median 0) | Hotel zone share |
| `lu_institutional_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Civic/community/place-of-worship |
| `lu_mixed_use_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.3002 (median 0) | Mixed-use zone share (residential + commercial) |
| `lu_open_space_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0346) | Park / open space share |
| `lu_other_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0 (median 0) | Other / unmapped |
| `lu_parcel_count` | int64 | count | 0.0 | 1 → 2096 (median 30) | URA parcels intersecting hex |
| `lu_reserve_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Reserve site share |
| `lu_residential_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9368 (median 0) | Land area share zoned residential |
| `lu_total_m2` | float64 | m² | 0.0 | 0.02469 → 8.596e+05 (median 8.331e+05) | Total land area covered by URA parcels in hex |
| `lu_transport_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.1035) | Transport infra share |
| `lu_utility_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Utility infra share |
| `lu_water_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9207 (median 0.0005) | Water body share |
| `max_gpr` | float64 | ratio | 0.0 | 0 → 25 (median 1) | Max GPR within hex |
| `mrt_exit_count` | float64 | count | 0.0 | 0 → 21 (median 0) | MRT exits in hex |
| `mrt_station_count` | float64 | count | 0.0 | 0 → 5 (median 0) | MRT/LRT stations in hex |
| `n_children` | int64 |  | 0.0 | 1 → 7 (median 7) |  |
| `n_highrise_bldgs` | float64 | count | 0.0 | 0 → 979 (median 0) | Number of buildings with floors ≥ 10 |
| `near_bus_300m` | bool | bool | 0.0 | 0 → 1 (median 1) | True if bus < 300m |
| `near_expressway_exit_400m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if motorway_link/trunk_link < 400m (drive-thru flag) |
| `near_mrt_400m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if MRT < 400m |
| `nl_2022` | float64 | nanoWatts/cm²/sr | 0.0 | 3.077 → 153.6 (median 46.03) | VIIRS night light radiance 2022 (subzone-broadcast) |
| `nl_2024` | float64 | nanoWatts/cm²/sr | 0.0 | 2.682 → 161.4 (median 49.34) | VIIRS night light radiance 2024 (subzone-broadcast) |
| `nl_change_pct` | float64 | % | 0.0 | -28.01 → 107.9 (median 4.208) | VIIRS 2022→2024 brightness change |
| `nl_commercial_indicator` | float64 | composite | 0.0 | 2.682 → 158.6 (median 29.56) | nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) |
| `nl_decline_zone` | bool | bool | 0.0 | 0 → 1 (median 0) | True if night light declined ≥ 20% |
| `nl_growth_corridor` | bool | bool | 0.0 | 0 → 1 (median 0) | True if night light grew ≥ 20% |
| `nl_per_capita` | float64 | radiance/person | 0.0 | 0 → 0.8876 (median 0) | nl_2024 / pop_resident (commercial vs residential signal) |
| `nonres_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.1962) | Non-resident share of total pop |
| `oneway_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.1692) | Fraction of vehicular length that's one-way |
| `parent_pa` | str | string | 0.0 | 55 unique · `TUAS` | URA planning area name (one of 55) |
| `parent_region` | str | string | 0.0 | 5 unique · `WEST REGION` | URA region (5 regions) |
| `parent_subzone` | str | string | 0.0 | 270 unique · `TSSZ06` | URA subzone parent (max-overlap) |
| `parent_subzone_name` | str | string | 0.0 | 270 unique · `TUAS VIEW EXTENSION` | URA subzone full name |
| `parking_lot_count` | float64 | count | 0.0 | 0 → 28 (median 0) | OSM amenity=parking points |
| `ped_path_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 74.58 (median 6.807) | Pedestrian-network density |
| `ped_path_length_m` | float64 | m | 0.0 | 0 → 5.482e+04 (median 4281) | Footway + path + cycleway + steps length |
| `pop_0_14` | float64 | persons | 0.0 | 0 → 7331 (median 0.116) | Population age 0-14 |
| `pop_15_64` | float64 | persons | 0.0 | 0 → 2.713e+04 (median 1.383) | Population age 15-64 |
| `pop_65plus` | float64 | persons | 0.0 | 0 → 7770 (median 0.108) | Population age 65+ |
| `pop_hdb` | float64 | persons | 0.0 | 0 → 3.511e+04 (median 0) | Residents in HDB flats |
| `pop_hdb_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | HDB share of resident pop |
| `pop_non_hdb` | float64 | persons | 0.0 | 0 → 9783 (median 1.622) | Residents in non-HDB housing |
| `pop_nonresident` | float64 | persons | 0.0 | 0 → 1.855e+04 (median 454.1) | Non-residents (FW + EP + MDW) |
| `pop_resident` | float64 | persons | 0.0 | 0 → 3.844e+04 (median 2.033) | Resident population (citizens + PRs) |
| `pop_total_all` | float64 | persons | 0.0 | 0 → 4.338e+04 (median 607.7) | Total population (residents + non-residents) |
| `rail_line_through_m` | float64 | m | 0.0 | 0 → 7810 (median 0) | Rail line length through hex (above + underground) |
| `road_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 112.5 (median 22.68) | Road km per km² |
| `road_intersection_count_total` | int64 |  | 0.0 | 0 → 523 (median 73) |  |
| `road_intersection_density_per_km2` | float64 | count/km² | 0.0 | 0 → 709.6 (median 99.05) | Vehicle-network nodes with deg ≥ 3 per km² (Jacobs) |
| `road_length_total_m` | float64 | m | 0.0 | 0 → 8.288e+04 (median 1.671e+04) | Total OSM road length clipped to hex |
| `road_max_class_through` | str | categorical | 0.0 | 13 unique · `none` | Highest road class running through hex |
| `road_walkable_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.3055) | Pedestrian-only roads as fraction of total |
| `signalized_crossing_count` | float64 | count | 0.0 | 0 → 365 (median 0) | LTA traffic signals in hex |
| `transit_score` | float64 | score [0,1] | 0.0 | 4.345e-08 → 0.9879 (median 0.3623) | 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) |
| `walk_amenities_400m` | int64 | count | 0.0 | 0 → 1.148e+04 (median 29) | Place count within 400m walk |
| `walk_food_400m` | int64 | count | 0.0 | 0 → 2499 (median 1) | Food places within 400m walk |
| `walk_hawker_400m` | int64 | count | 0.0 | 0 → 630 (median 0) | Hawkers within 400m walk |
| `walk_park_400m` | int64 | count | 0.0 | 0 → 30 (median 0) | Parks within 400m walk |
| `walkability_score` | float64 | score [0,1] | 0.0 | 0 → 0.9217 (median 0.1915) | Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |
| `wp_pop` | float64 | persons | 0.0 | 0 → 9.262e+04 (median 0) | WorldPop count per hex (single snapshot — only one valid TIF available) |

## `hex/hex8_buildings_clean.parquet`

_19 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `best_max_floors` | float64 | floors | 52.3 | 1 → 70 (median 25) | Max floor count (Overture or HDB authoritative) |
| `bldg_commercial_count` | float64 | count | 0.0 | 0 → 191 (median 0) | Commercial buildings |
| `bldg_count` | float64 | count | 0.0 | 0 → 1968 (median 136) | Building footprints in hex (Overture + HDB + OSM) |
| `bldg_density_per_km2` | float64 | count/km² | 0.0 | 0 → 2670 (median 184.5) | Buildings per km² |
| `bldg_footprint_m2` | float64 | m² | 0.0 | 0 → 4.288e+05 (median 4.936e+04) | Total clipped building footprint area in hex |
| `bldg_footprint_share` | float64 | ratio [0,1] | 0.0 | 0 → 0.5818 (median 0.067) | Footprint as fraction of hex area (clipped, ≤1) |
| `bldg_industrial_count` | float64 | count | 0.0 | 0 → 165 (median 0) | Industrial buildings |
| `bldg_institutional_count` | float64 | count | 0.0 | 0 → 45 (median 0) | Institutional buildings |
| `bldg_residential_count` | float64 | count | 0.0 | 0 → 1084 (median 0) | Residential buildings |
| `est_built_far` | float64 | ratio | 0.0 | 0 → 3.686 (median 0.2114) | Estimated built-up FAR = total floor area / hex area |
| `est_total_floor_area_m2` | float64 | m² | 0.0 | 0 → 2.716e+06 (median 1.558e+05) | Sum of footprint × est_floors per building |
| `hdb_avg_age_years` | float64 | years | 76.0 | 8.062 → 63.75 (median 45.48) | Avg years since HDB completion (year_completed filtered ≥1960) |
| `hdb_block_count` | float64 | count | 0.0 | 0 → 147 (median 0) | HDB blocks (authoritative) |
| `hdb_dwelling_units` | float64 | count | 0.0 | 0 → 1.319e+04 (median 0) | Total dwelling units across HDB blocks |
| `hdb_max_floors` | float64 | floors | 76.0 | 12 → 50 (median 40) | Max HDB floor count |
| `hex8_id` | str | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `is_highrise` | bool | bool | 0.0 | 0 → 1 (median 0) | True if max_floors >= 10 |
| `n_children` | int64 |  | 0.0 | 1 → 7 (median 7) |  |
| `n_highrise_bldgs` | float64 | count | 0.0 | 0 → 979 (median 0) | Number of buildings with floors ≥ 10 |

## `hex/hex8_built_environment_features.parquet`

_40 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `avg_gpr` | float64 | ratio | 0.0 | 0 → 13.05 (median 1) | Area-weighted Gross Plot Ratio |
| `best_max_floors` | float64 | floors | 0.0 | 0 → 70 (median 0) | Max floor count (Overture or HDB authoritative) |
| `bldg_commercial_count` | float64 | count | 0.0 | 0 → 191 (median 0) | Commercial buildings |
| `bldg_count` | float64 | count | 0.0 | 0 → 1968 (median 136) | Building footprints in hex (Overture + HDB + OSM) |
| `bldg_density_per_km2` | float64 | count/km² | 0.0 | 0 → 2670 (median 184.5) | Buildings per km² |
| `bldg_footprint_m2` | float64 | m² | 0.0 | 0 → 4.288e+05 (median 4.936e+04) | Total clipped building footprint area in hex |
| `bldg_footprint_share` | float64 | ratio [0,1] | 0.0 | 0 → 0.5818 (median 0.067) | Footprint as fraction of hex area (clipped, ≤1) |
| `bldg_industrial_count` | float64 | count | 0.0 | 0 → 165 (median 0) | Industrial buildings |
| `bldg_institutional_count` | float64 | count | 0.0 | 0 → 45 (median 0) | Institutional buildings |
| `bldg_residential_count` | float64 | count | 0.0 | 0 → 1084 (median 0) | Residential buildings |
| `dominant_use` | str | categorical | 0.0 | 11 unique · `transport` | Bucket with highest area share |
| `est_built_far` | float64 | ratio | 0.0 | 0 → 3.686 (median 0.2114) | Estimated built-up FAR = total floor area / hex area |
| `est_total_floor_area_m2` | float64 | m² | 0.0 | 0 → 2.716e+06 (median 1.558e+05) | Sum of footprint × est_floors per building |
| `hdb_avg_age_years` | float64 | years | 0.0 | 0 → 63.75 (median 0) | Avg years since HDB completion (year_completed filtered ≥1960) |
| `hdb_block_count` | float64 | count | 0.0 | 0 → 147 (median 0) | HDB blocks (authoritative) |
| `hdb_dwelling_units` | float64 | count | 0.0 | 0 → 1.319e+04 (median 0) | Total dwelling units across HDB blocks |
| `hdb_max_floors` | float64 | floors | 0.0 | 0 → 50 (median 0) | Max HDB floor count |
| `hex8_id` | str | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `is_highrise` | bool | bool | 0.0 | 0 → 1 (median 0) | True if max_floors >= 10 |
| `lu_business_park_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.5231 (median 0) | Business park share |
| `lu_business_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Land area share zoned business (industrial) |
| `lu_commercial_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.4369 (median 0) | Land area share zoned commercial |
| `lu_educational_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.729 (median 0) | Educational institution share |
| `lu_entropy` | float64 | nats | 0.0 | 0 → 1.726 (median 0.449) | Shannon entropy across 14 LU buckets |
| `lu_health_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.2255 (median 0) | Health & medical share |
| `lu_hotel_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.3256 (median 0) | Hotel zone share |
| `lu_institutional_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Civic/community/place-of-worship |
| `lu_mixed_use_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.2079 (median 0) | Mixed-use zone share (residential + commercial) |
| `lu_open_space_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0354) | Park / open space share |
| `lu_other_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0 (median 0) | Other / unmapped |
| `lu_parcel_count` | int64 | count | 0.0 | 1 → 2096 (median 30) | URA parcels intersecting hex |
| `lu_reserve_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Reserve site share |
| `lu_residential_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9368 (median 0) | Land area share zoned residential |
| `lu_total_m2` | float64 | m² | 0.0 | 0.02469 → 8.596e+05 (median 8.331e+05) | Total land area covered by URA parcels in hex |
| `lu_transport_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0957) | Transport infra share |
| `lu_utility_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Utility infra share |
| `lu_water_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9207 (median 0.0005) | Water body share |
| `max_gpr` | float64 | ratio | 0.0 | 0 → 25 (median 1) | Max GPR within hex |
| `n_children` | int64 |  | 0.0 | 1 → 7 (median 7) |  |
| `n_highrise_bldgs` | float64 | count | 0.0 | 0 → 979 (median 0) | Number of buildings with floors ≥ 10 |

## `hex/hex8_land_use.parquet`

_22 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `avg_gpr` | float64 | ratio | 0.0 | 0 → 11.03 (median 0.5845) | Area-weighted Gross Plot Ratio |
| `dominant_use` | str | categorical | 0.0 | 11 unique · `transport` | Bucket with highest area share |
| `hex8_id` | str | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `lu_business_park_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.523 (median 0) | Business park share |
| `lu_business_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Land area share zoned business (industrial) |
| `lu_commercial_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.4744 (median 0) | Land area share zoned commercial |
| `lu_educational_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.7291 (median 0) | Educational institution share |
| `lu_entropy` | float64 | nats | 0.0 | -0 → 2.09 (median 0.6931) | Shannon entropy across 14 LU buckets |
| `lu_health_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.2255 (median 0) | Health & medical share |
| `lu_hotel_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.2884 (median 0) | Hotel zone share |
| `lu_institutional_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Civic/community/place-of-worship |
| `lu_mixed_use_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.3002 (median 0) | Mixed-use zone share (residential + commercial) |
| `lu_open_space_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0346) | Park / open space share |
| `lu_other_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0 (median 0) | Other / unmapped |
| `lu_parcel_count` | int64 | count | 0.0 | 1 → 2096 (median 30) | URA parcels intersecting hex |
| `lu_reserve_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Reserve site share |
| `lu_residential_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9368 (median 0) | Land area share zoned residential |
| `lu_total_m2` | float64 | m² | 0.0 | 0.02469 → 8.596e+05 (median 8.331e+05) | Total land area covered by URA parcels in hex |
| `lu_transport_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.1035) | Transport infra share |
| `lu_utility_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Utility infra share |
| `lu_water_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9207 (median 0.0005) | Water body share |
| `max_gpr` | float64 | ratio | 45.0 | 1 → 25 (median 2.8) | Max GPR within hex |

## `hex/hex8_mobility_features.parquet`

_50 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `bridge_length_m` | float64 | m | 0.0 | 0 → 1.07e+04 (median 89.88) | Bridge segment length |
| `bus_routes_per_stop_max` | float64 | count | 0.0 | 0 → 50 (median 0) | Max # routes serving a stop in hex (GTFS) |
| `bus_routes_per_stop_mean` | float64 | count | 0.0 | 0 → 20.36 (median 0) | Mean routes/stop in hex |
| `bus_stop_count` | float64 | count | 0.0 | 0 → 31 (median 0) | Bus stops in hex |
| `centr_betweenness_max` | float64 | ratio | 0.0 | 0 → 0.108 (median 0) | Max betweenness centrality of major-road nodes |
| `centr_bridge_count` | float64 | count | 0.0 | 0 → 64 (median 0) | Tarjan bridge endpoints (network cut points) |
| `daily_bus_taps` | float64 | taps/day | 0.0 | 0 → 1.187e+05 (median 0) | Daily bus taps (Dec 2025 LTA monthly / 31) |
| `daily_train_taps` | float64 | taps/day | 0.0 | 0 → 2.476e+05 (median 0) | Daily MRT/LRT taps (Jan 2026 LTA monthly / 31) |
| `dist_bus_m` | float64 | m | 0.0 | 5.326 → 1.336e+04 (median 281.7) | Centroid distance to nearest bus stop |
| `dist_expressway_m` | float64 | m | 0.0 | 0.00143 → 1.372e+04 (median 1503) | Centroid distance to nearest motorway/trunk segment |
| `dist_mrt_exit_m` | float64 | m | 0.0 | 7.807 → 1.376e+04 (median 1731) | Centroid distance to nearest MRT exit |
| `dist_mrt_m` | float64 | m | 0.0 | 0 → 1.373e+04 (median 1655) | Centroid distance to nearest MRT/LRT station |
| `dist_walk_clinic_m` | float64 | m | 0.0 | 1.673 → 1.599e+04 (median 915.2) | Walk distance to nearest clinic |
| `dist_walk_food_m` | float64 | m | 0.0 | 1.963 → 1.596e+04 (median 385.1) | Walk distance to nearest restaurant/cafe/hawker/bakery/fast-food |
| `dist_walk_hawker_m` | float64 | m | 0.0 | 1.963 → 1.599e+04 (median 1046) | Walk distance to nearest hawker (Euclidean × 1.3 detour) |
| `dist_walk_park_m` | float64 | m | 0.0 | 0 → 2.054e+04 (median 1037) | Walk distance to nearest park |
| `dist_walk_school_m` | float64 | m | 0.0 | 2.142 → 1.581e+04 (median 610.4) | Walk distance to nearest school |
| `dist_walk_supermarket_m` | float64 | m | 0.0 | 4.861 → 1.79e+04 (median 857.1) | Walk distance to nearest supermarket |
| `expressway_severance` | bool | bool | 0.0 | 0 → 1 (median 0) | Expressway < 200m AND no exit < 400m (barrier without benefit) |
| `gtfs_headway_am_min` | float64 | min | 0.0 | 0.1389 → 999 (median 999) | Best AM-peak headway (lowest minutes between buses) at any stop in hex |
| `hdb_mscp_count` | float64 | count | 0.0 | 0 → 23 (median 0) | Authoritative HDB multi-storey carparks |
| `hex8_id` | str | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `is_mrt_interchange` | bool | bool | 0.0 | 0 → 1 (median 0) | True if any station has ≥2 lines (slash-PT_CODE) |
| `lane_km_per_km2` | float64 | km/km² | 0.0 | 0 → 97.19 (median 22.81) | Lane-km per km² (lane count × length / area) |
| `mrt_exit_count` | float64 | count | 0.0 | 0 → 21 (median 0) | MRT exits in hex |
| `mrt_station_count` | float64 | count | 0.0 | 0 → 5 (median 0) | MRT/LRT stations in hex |
| `n_children` | int64 |  | 0.0 | 1 → 7 (median 7) |  |
| `n_children_tr` | int64 |  | 0.0 | 1 → 7 (median 7) |  |
| `n_children_wk` | int64 |  | 0.0 | 1 → 7 (median 7) |  |
| `near_bus_300m` | bool | bool | 0.0 | 0 → 1 (median 1) | True if bus < 300m |
| `near_expressway_exit_400m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if motorway_link/trunk_link < 400m (drive-thru flag) |
| `near_mrt_400m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if MRT < 400m |
| `oneway_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.1692) | Fraction of vehicular length that's one-way |
| `parking_lot_count` | float64 | count | 0.0 | 0 → 28 (median 0) | OSM amenity=parking points |
| `ped_path_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 74.58 (median 6.807) | Pedestrian-network density |
| `ped_path_length_m` | float64 | m | 0.0 | 0 → 5.482e+04 (median 4281) | Footway + path + cycleway + steps length |
| `rail_line_through_m` | float64 | m | 0.0 | 0 → 7810 (median 0) | Rail line length through hex (above + underground) |
| `road_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 112.5 (median 22.68) | Road km per km² |
| `road_intersection_count_total` | int64 |  | 0.0 | 0 → 523 (median 73) |  |
| `road_intersection_density_per_km2` | float64 | count/km² | 0.0 | 0 → 709.6 (median 99.05) | Vehicle-network nodes with deg ≥ 3 per km² (Jacobs) |
| `road_length_total_m` | float64 | m | 0.0 | 0 → 8.288e+04 (median 1.671e+04) | Total OSM road length clipped to hex |
| `road_max_class_through` | str | categorical | 0.0 | 13 unique · `none` | Highest road class running through hex |
| `road_walkable_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.3055) | Pedestrian-only roads as fraction of total |
| `signalized_crossing_count` | float64 | count | 0.0 | 0 → 365 (median 0) | LTA traffic signals in hex |
| `transit_score` | float64 | score [0,1] | 0.0 | 4.345e-08 → 0.9879 (median 0.3623) | 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) |
| `walk_amenities_400m` | int64 | count | 0.0 | 0 → 1.148e+04 (median 29) | Place count within 400m walk |
| `walk_food_400m` | int64 | count | 0.0 | 0 → 2499 (median 1) | Food places within 400m walk |
| `walk_hawker_400m` | int64 | count | 0.0 | 0 → 630 (median 0) | Hawkers within 400m walk |
| `walk_park_400m` | int64 | count | 0.0 | 0 → 30 (median 0) | Parks within 400m walk |
| `walkability_score` | float64 | score [0,1] | 0.0 | 0 → 0.9217 (median 0.1915) | Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |

## `hex/hex8_population.parquet`

_17 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `hex8_id` | str | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `lat` | float64 | degrees | 0.0 | 1.159 → 1.47 (median 1.349) | Hex centroid latitude |
| `lng` | float64 | degrees | 0.0 | 103.6 → 104.1 (median 103.8) | Hex centroid longitude |
| `nonres_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.1962) | Non-resident share of total pop |
| `parent_pa` | str | string | 0.0 | 55 unique · `TUAS` | URA planning area name (one of 55) |
| `parent_region` | str | string | 0.0 | 5 unique · `WEST REGION` | URA region (5 regions) |
| `parent_subzone` | str | string | 0.0 | 270 unique · `TSSZ06` | URA subzone parent (max-overlap) |
| `parent_subzone_name` | str | string | 0.0 | 270 unique · `TUAS VIEW EXTENSION` | URA subzone full name |
| `pop_0_14` | float64 | persons | 0.0 | 0 → 7331 (median 0.116) | Population age 0-14 |
| `pop_15_64` | float64 | persons | 0.0 | 0 → 2.713e+04 (median 1.383) | Population age 15-64 |
| `pop_65plus` | float64 | persons | 0.0 | 0 → 7770 (median 0.108) | Population age 65+ |
| `pop_hdb` | float64 | persons | 0.0 | 0 → 3.511e+04 (median 0) | Residents in HDB flats |
| `pop_hdb_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | HDB share of resident pop |
| `pop_non_hdb` | float64 | persons | 0.0 | 0 → 9783 (median 1.622) | Residents in non-HDB housing |
| `pop_nonresident` | float64 | persons | 0.0 | 0 → 1.855e+04 (median 454.1) | Non-residents (FW + EP + MDW) |
| `pop_resident` | float64 | persons | 0.0 | 0 → 3.844e+04 (median 2.033) | Resident population (citizens + PRs) |
| `pop_total_all` | float64 | persons | 0.0 | 0 → 4.338e+04 (median 607.7) | Total population (residents + non-residents) |

## `hex/hex8_roads_clean.parquet`

_18 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `bridge_length_m` | float64 | m | 0.0 | 0 → 1.07e+04 (median 89.88) | Bridge segment length |
| `centr_betweenness_max` | float64 | ratio | 0.0 | 0 → 0.108 (median 0) | Max betweenness centrality of major-road nodes |
| `centr_bridge_count` | float64 | count | 0.0 | 0 → 64 (median 0) | Tarjan bridge endpoints (network cut points) |
| `dist_expressway_m` | float64 | m | 0.0 | 0.00143 → 1.372e+04 (median 1503) | Centroid distance to nearest motorway/trunk segment |
| `hdb_mscp_count` | float64 | count | 0.0 | 0 → 23 (median 0) | Authoritative HDB multi-storey carparks |
| `hex8_id` | str | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `lane_km_per_km2` | float64 | km/km² | 0.0 | 0 → 97.19 (median 22.81) | Lane-km per km² (lane count × length / area) |
| `n_children` | int64 |  | 0.0 | 1 → 7 (median 7) |  |
| `near_expressway_exit_400m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if motorway_link/trunk_link < 400m (drive-thru flag) |
| `oneway_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.1692) | Fraction of vehicular length that's one-way |
| `parking_lot_count` | float64 | count | 0.0 | 0 → 28 (median 0) | OSM amenity=parking points |
| `road_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 112.5 (median 22.68) | Road km per km² |
| `road_intersection_count_total` | int64 |  | 0.0 | 0 → 523 (median 73) |  |
| `road_intersection_density_per_km2` | float64 | count/km² | 0.0 | 0 → 709.6 (median 99.05) | Vehicle-network nodes with deg ≥ 3 per km² (Jacobs) |
| `road_length_total_m` | float64 | m | 0.0 | 0 → 8.288e+04 (median 1.671e+04) | Total OSM road length clipped to hex |
| `road_max_class_through` | str | categorical | 0.0 | 13 unique · `none` | Highest road class running through hex |
| `road_walkable_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.3055) | Pedestrian-only roads as fraction of total |
| `signalized_crossing_count` | float64 | count | 0.0 | 0 → 365 (median 0) | LTA traffic signals in hex |

## `hex/hex8_satellite.parquet`

_9 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `hex8_id` | str | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `nl_2022` | float64 | nanoWatts/cm²/sr | 0.0 | 3.077 → 153.6 (median 46.03) | VIIRS night light radiance 2022 (subzone-broadcast) |
| `nl_2024` | float64 | nanoWatts/cm²/sr | 0.0 | 2.682 → 161.4 (median 49.34) | VIIRS night light radiance 2024 (subzone-broadcast) |
| `nl_change_pct` | float64 | % | 0.0 | -28.01 → 107.9 (median 4.208) | VIIRS 2022→2024 brightness change |
| `nl_commercial_indicator` | float64 | composite | 0.0 | 2.682 → 158.6 (median 29.56) | nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) |
| `nl_decline_zone` | bool | bool | 0.0 | 0 → 1 (median 0) | True if night light declined ≥ 20% |
| `nl_growth_corridor` | bool | bool | 0.0 | 0 → 1 (median 0) | True if night light grew ≥ 20% |
| `nl_per_capita` | float64 | radiance/person | 0.0 | 0 → 0.8876 (median 0) | nl_2024 / pop_resident (commercial vs residential signal) |
| `wp_pop` | float64 | persons | 0.0 | 0 → 9.262e+04 (median 0) | WorldPop count per hex (single snapshot — only one valid TIF available) |

## `hex/hex8_transit_clean.parquet`

_18 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `bus_routes_per_stop_max` | float64 | count | 0.0 | 0 → 50 (median 0) | Max # routes serving a stop in hex (GTFS) |
| `bus_routes_per_stop_mean` | float64 | count | 0.0 | 0 → 20.36 (median 0) | Mean routes/stop in hex |
| `bus_stop_count` | float64 | count | 0.0 | 0 → 31 (median 0) | Bus stops in hex |
| `daily_bus_taps` | float64 | taps/day | 0.0 | 0 → 1.187e+05 (median 0) | Daily bus taps (Dec 2025 LTA monthly / 31) |
| `daily_train_taps` | float64 | taps/day | 0.0 | 0 → 2.476e+05 (median 0) | Daily MRT/LRT taps (Jan 2026 LTA monthly / 31) |
| `dist_bus_m` | float64 | m | 0.0 | 5.326 → 1.336e+04 (median 281.7) | Centroid distance to nearest bus stop |
| `dist_mrt_exit_m` | float64 | m | 0.0 | 7.807 → 1.376e+04 (median 1731) | Centroid distance to nearest MRT exit |
| `dist_mrt_m` | float64 | m | 0.0 | 0 → 1.373e+04 (median 1655) | Centroid distance to nearest MRT/LRT station |
| `gtfs_headway_am_min` | float64 | min | 0.0 | 0.1389 → 999 (median 999) | Best AM-peak headway (lowest minutes between buses) at any stop in hex |
| `hex8_id` | str | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `is_mrt_interchange` | bool | bool | 0.0 | 0 → 1 (median 0) | True if any station has ≥2 lines (slash-PT_CODE) |
| `mrt_exit_count` | float64 | count | 0.0 | 0 → 21 (median 0) | MRT exits in hex |
| `mrt_station_count` | float64 | count | 0.0 | 0 → 5 (median 0) | MRT/LRT stations in hex |
| `n_children` | int64 |  | 0.0 | 1 → 7 (median 7) |  |
| `near_bus_300m` | bool | bool | 0.0 | 0 → 1 (median 1) | True if bus < 300m |
| `near_mrt_400m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if MRT < 400m |
| `rail_line_through_m` | float64 | m | 0.0 | 0 → 7810 (median 0) | Rail line length through hex (above + underground) |
| `transit_score` | float64 | score [0,1] | 0.0 | 4.345e-08 → 0.9879 (median 0.3623) | 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) |

## `hex/hex8_universe.parquet`

_7 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `hex8_id` | str | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `lat` | float64 | degrees | 0.0 | 1.159 → 1.47 (median 1.349) | Hex centroid latitude |
| `lng` | float64 | degrees | 0.0 | 103.6 → 104.1 (median 103.8) | Hex centroid longitude |
| `parent_pa` | str | string | 0.0 | 55 unique · `TUAS` | URA planning area name (one of 55) |
| `parent_region` | str | string | 0.0 | 5 unique · `WEST REGION` | URA region (5 regions) |
| `parent_subzone` | str | string | 0.0 | 270 unique · `TSSZ06` | URA subzone parent (max-overlap) |
| `parent_subzone_name` | str | string | 0.0 | 270 unique · `TUAS VIEW EXTENSION` | URA subzone full name |

## `hex/hex8_walkability.parquet`

_21 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `dist_walk_clinic_m` | float64 | m | 0.0 | 1.673 → 1.599e+04 (median 915.2) | Walk distance to nearest clinic |
| `dist_walk_food_m` | float64 | m | 0.0 | 1.963 → 1.596e+04 (median 385.1) | Walk distance to nearest restaurant/cafe/hawker/bakery/fast-food |
| `dist_walk_hawker_m` | float64 | m | 0.0 | 1.963 → 1.599e+04 (median 1046) | Walk distance to nearest hawker (Euclidean × 1.3 detour) |
| `dist_walk_park_m` | float64 | m | 0.0 | 0 → 2.054e+04 (median 1037) | Walk distance to nearest park |
| `dist_walk_school_m` | float64 | m | 0.0 | 2.142 → 1.581e+04 (median 610.4) | Walk distance to nearest school |
| `dist_walk_supermarket_m` | float64 | m | 0.0 | 4.861 → 1.79e+04 (median 857.1) | Walk distance to nearest supermarket |
| `expressway_severance` | bool | bool | 0.0 | 0 → 1 (median 0) | Expressway < 200m AND no exit < 400m (barrier without benefit) |
| `hex8_id` | str | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `n_children` | int64 |  | 0.0 | 1 → 7 (median 7) |  |
| `near_bus_300m` | bool | bool | 0.0 | 0 → 1 (median 1) | True if bus < 300m |
| `near_mrt_400m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if MRT < 400m |
| `ped_path_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 74.58 (median 6.807) | Pedestrian-network density |
| `ped_path_length_m` | float64 | m | 0.0 | 0 → 5.482e+04 (median 4281) | Footway + path + cycleway + steps length |
| `road_intersection_density_per_km2` | float64 | count/km² | 0.0 | 0 → 711.6 (median 110.2) | Vehicle-network nodes with deg ≥ 3 per km² (Jacobs) |
| `road_walkable_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.2303) | Pedestrian-only roads as fraction of total |
| `signalized_crossing_count` | float64 | count | 0.0 | 0 → 365 (median 0) | LTA traffic signals in hex |
| `walk_amenities_400m` | int64 | count | 0.0 | 0 → 1.148e+04 (median 29) | Place count within 400m walk |
| `walk_food_400m` | int64 | count | 0.0 | 0 → 2499 (median 1) | Food places within 400m walk |
| `walk_hawker_400m` | int64 | count | 0.0 | 0 → 630 (median 0) | Hawkers within 400m walk |
| `walk_park_400m` | int64 | count | 0.0 | 0 → 30 (median 0) | Parks within 400m walk |
| `walkability_score` | float64 | score [0,1] | 0.0 | 0 → 0.9217 (median 0.1915) | Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |

## `hex/hex9_all_features.parquet`

_114 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `avg_gpr` | float64 | ratio | 0.0 | 0 → 21.96 (median 0) | Area-weighted Gross Plot Ratio |
| `best_max_floors` | float64 | floors | 0.0 | 0 → 70 (median 0) | Max floor count (Overture or HDB authoritative) |
| `bldg_commercial_count` | float64 | count | 0.0 | 0 → 87 (median 0) | Commercial buildings |
| `bldg_count` | float64 | count | 0.0 | 0 → 541 (median 20) | Building footprints in hex (Overture + HDB + OSM) |
| `bldg_density_per_km2` | float64 | count/km² | 0.0 | 0 → 5152 (median 190.5) | Buildings per km² |
| `bldg_footprint_m2` | float64 | m² | 0.0 | 0 → 1.213e+05 (median 6765) | Total clipped building footprint area in hex |
| `bldg_footprint_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0644) | Footprint as fraction of hex area (clipped, ≤1) |
| `bldg_industrial_count` | float64 | count | 0.0 | 0 → 71 (median 0) | Industrial buildings |
| `bldg_institutional_count` | float64 | count | 0.0 | 0 → 27 (median 0) | Institutional buildings |
| `bldg_residential_count` | float64 | count | 0.0 | 0 → 474 (median 0) | Residential buildings |
| `bridge_length_m` | float64 | m | 0.0 | 0 → 4369 (median 0) | Bridge segment length |
| `bus_routes_per_stop_max` | float64 | count | 0.0 | 0 → 50 (median 0) | Max # routes serving a stop in hex (GTFS) |
| `bus_routes_per_stop_mean` | float64 | count | 0.0 | 0 → 50 (median 0) | Mean routes/stop in hex |
| `bus_stop_count` | float64 | count | 0.0 | 0 → 13 (median 0) | Bus stops in hex |
| `centr_betweenness_max` | float64 | ratio | 0.0 | 0 → 0.108 (median 0) | Max betweenness centrality of major-road nodes |
| `centr_bridge_count` | float64 | count | 0.0 | 0 → 31 (median 0) | Tarjan bridge endpoints (network cut points) |
| `daily_bus_taps` | float64 | taps/day | 0.0 | 0 → 1.042e+05 (median 0) | Daily bus taps (Dec 2025 LTA monthly / 31) |
| `daily_train_taps` | float64 | taps/day | 0.0 | 0 → 2.212e+05 (median 0) | Daily MRT/LRT taps (Jan 2026 LTA monthly / 31) |
| `dist_bus_m` | float64 | m | 0.0 | 5.326 → 1.373e+04 (median 463.5) | Centroid distance to nearest bus stop |
| `dist_expressway_m` | float64 | m | 0.0 | 0.00143 → 1.409e+04 (median 1463) | Centroid distance to nearest motorway/trunk segment |
| `dist_mrt_exit_m` | float64 | m | 0.0 | 7.807 → 1.413e+04 (median 1762) | Centroid distance to nearest MRT exit |
| `dist_mrt_m` | float64 | m | 0.0 | 0 → 1.409e+04 (median 1657) | Centroid distance to nearest MRT/LRT station |
| `dist_walk_clinic_m` | float64 | m | 0.0 | 1.673 → 1.639e+04 (median 1102) | Walk distance to nearest clinic |
| `dist_walk_convenience_m` | float64 | m | 0.0 | 3.638 → 1.41e+04 (median 755.2) | Walk distance to nearest convenience store |
| `dist_walk_food_m` | float64 | m | 0.0 | 1.963 → 1.636e+04 (median 645) | Walk distance to nearest restaurant/cafe/hawker/bakery/fast-food |
| `dist_walk_hawker_m` | float64 | m | 0.0 | 1.963 → 1.638e+04 (median 1202) | Walk distance to nearest hawker (Euclidean × 1.3 detour) |
| `dist_walk_park_m` | float64 | m | 0.0 | 0 → 2.091e+04 (median 1222) | Walk distance to nearest park |
| `dist_walk_school_m` | float64 | m | 0.0 | 2.142 → 1.625e+04 (median 845.2) | Walk distance to nearest school |
| `dist_walk_supermarket_m` | float64 | m | 0.0 | 4.861 → 1.834e+04 (median 1055) | Walk distance to nearest supermarket |
| `dominant_use` | str | categorical | 0.0 | 14 unique · `transport` | Bucket with highest area share |
| `est_built_far` | float64 | ratio | 0.0 | 0 → 10.03 (median 0.2165) | Estimated built-up FAR = total floor area / hex area |
| `est_total_floor_area_m2` | float64 | m² | 0.0 | 0 → 1.053e+06 (median 2.273e+04) | Sum of footprint × est_floors per building |
| `expressway_severance` | bool | bool | 0.0 | 0 → 1 (median 0) | Expressway < 200m AND no exit < 400m (barrier without benefit) |
| `gtfs_headway_am_min` | float64 | min | 0.0 | 0.1389 → 999 (median 999) | Best AM-peak headway (lowest minutes between buses) at any stop in hex |
| `hdb_avg_age_years` | float64 | years | 0.0 | 0 → 65 (median 0) | Avg years since HDB completion (year_completed filtered ≥1960) |
| `hdb_block_count` | float64 | count | 0.0 | 0 → 110 (median 0) | HDB blocks (authoritative) |
| `hdb_dwelling_units` | float64 | count | 0.0 | 0 → 1.055e+04 (median 0) | Total dwelling units across HDB blocks |
| `hdb_max_floors` | float64 | floors | 0.0 | 0 → 50 (median 0) | Max HDB floor count |
| `hdb_mscp_count` | float64 | count | 0.0 | 0 → 7 (median 0) | Authoritative HDB multi-storey carparks |
| `hex9_id` | str | string | 0.0 | 7318 unique · `896520c0007ffff` | H3 resolution-9 cell ID (~0.105 km², 174m edge) |
| `is_highrise` | bool | bool | 0.0 | 0 → 1 (median 0) | True if max_floors >= 10 |
| `is_mrt_interchange` | bool | bool | 0.0 | 0 → 1 (median 0) | True if any station has ≥2 lines (slash-PT_CODE) |
| `lane_km_per_km2` | float64 | km/km² | 0.0 | 0 → 147.7 (median 17.13) | Lane-km per km² (lane count × length / area) |
| `lat` | float64 | degrees | 0.0 | 1.159 → 1.472 (median 1.352) | Hex centroid latitude |
| `lng` | float64 | degrees | 0.0 | 103.6 → 104.1 (median 103.8) | Hex centroid longitude |
| `lu_business_park_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8105 (median 0) | Business park share |
| `lu_business_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Land area share zoned business (industrial) |
| `lu_commercial_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9317 (median 0) | Land area share zoned commercial |
| `lu_educational_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Educational institution share |
| `lu_entropy` | float64 | nats | 0.0 | -0 → 2.084 (median 0.514) | Shannon entropy across 14 LU buckets |
| `lu_health_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8857 (median 0) | Health & medical share |
| `lu_hotel_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8988 (median 0) | Hotel zone share |
| `lu_institutional_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Civic/community/place-of-worship |
| `lu_mixed_use_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.6274 (median 0) | Mixed-use zone share (residential + commercial) |
| `lu_open_space_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0026) | Park / open space share |
| `lu_other_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0 (median 0) | Other / unmapped |
| `lu_parcel_count` | int64 | count | 0.0 | 1 → 533 (median 5) | URA parcels intersecting hex |
| `lu_reserve_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Reserve site share |
| `lu_residential_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Land area share zoned residential |
| `lu_total_m2` | float64 | m² | 0.0 | 0.02469 → 1.308e+05 (median 1.191e+05) | Total land area covered by URA parcels in hex |
| `lu_transport_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0926) | Transport infra share |
| `lu_utility_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Utility infra share |
| `lu_water_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Water body share |
| `max_gpr` | float64 | ratio | 0.0 | 0 → 25 (median 0) | Max GPR within hex |
| `mrt_exit_count` | float64 | count | 0.0 | 0 → 10 (median 0) | MRT exits in hex |
| `mrt_station_count` | float64 | count | 0.0 | 0 → 3 (median 0) | MRT/LRT stations in hex |
| `n_highrise_bldgs` | float64 | count | 0.0 | 0 → 474 (median 0) | Number of buildings with floors ≥ 10 |
| `near_bus_300m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if bus < 300m |
| `near_expressway_exit_400m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if motorway_link/trunk_link < 400m (drive-thru flag) |
| `near_mrt_400m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if MRT < 400m |
| `nl_2022` | float64 | nanoWatts/cm²/sr | 0.0 | 0 → 153.6 (median 46.03) | VIIRS night light radiance 2022 (subzone-broadcast) |
| `nl_2024` | float64 | nanoWatts/cm²/sr | 0.0 | 0 → 179.5 (median 48.49) | VIIRS night light radiance 2024 (subzone-broadcast) |
| `nl_change_pct` | float64 | % | 0.0 | -28.01 → 120.4 (median 4.41) | VIIRS 2022→2024 brightness change |
| `nl_commercial_indicator` | float64 | composite | 0.0 | 0 → 167.3 (median 28.12) | nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) |
| `nl_decline_zone` | bool | bool | 0.0 | 0 → 1 (median 0) | True if night light declined ≥ 20% |
| `nl_growth_corridor` | bool | bool | 0.0 | 0 → 1 (median 0) | True if night light grew ≥ 20% |
| `nl_per_capita` | float64 | radiance/person | 0.0 | 0 → 2.997 (median 0) | nl_2024 / pop_resident (commercial vs residential signal) |
| `nonres_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.1807) | Non-resident share of total pop |
| `oneway_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0407) | Fraction of vehicular length that's one-way |
| `parent_hex8` | str | string | 0.0 | 1191 unique · `886520c001fffff` | hex-9's parent hex-8 |
| `parent_pa` | str | string | 0.0 | 55 unique · `TUAS` | URA planning area name (one of 55) |
| `parent_region` | str | string | 0.0 | 5 unique · `WEST REGION` | URA region (5 regions) |
| `parent_subzone` | str | string | 0.0 | 326 unique · `TSSZ06` | URA subzone parent (max-overlap) |
| `parent_subzone_name` | str | string | 0.0 | 326 unique · `TUAS VIEW EXTENSION` | URA subzone full name |
| `parking_lot_count` | float64 | count | 0.0 | 0 → 15 (median 0) | OSM amenity=parking points |
| `ped_path_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 228.6 (median 6.367) | Pedestrian-network density |
| `ped_path_length_m` | float64 | m | 0.0 | 0 → 2.4e+04 (median 668.6) | Footway + path + cycleway + steps length |
| `pop_0_14` | float64 | persons | 0.0 | 0 → 1735 (median 0) | Population age 0-14 |
| `pop_15_64` | float64 | persons | 0.0 | 0 → 9803 (median 0.0664) | Population age 15-64 |
| `pop_65plus` | float64 | persons | 0.0 | 0 → 2108 (median 0.0027) | Population age 65+ |
| `pop_hdb` | float64 | persons | 0.0 | 0 → 1.27e+04 (median 0) | Residents in HDB flats |
| `pop_hdb_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | HDB share of resident pop |
| `pop_non_hdb` | float64 | persons | 0.0 | 0 → 2065 (median 0.0254) | Residents in non-HDB housing |
| `pop_nonresident` | float64 | persons | 0.0 | 0 → 5484 (median 51.87) | Non-residents (FW + EP + MDW) |
| `pop_resident` | float64 | persons | 0.0 | 0 → 1.332e+04 (median 0.0976) | Resident population (citizens + PRs) |
| `pop_total_all` | float64 | persons | 0.0 | 0 → 1.426e+04 (median 114.2) | Total population (residents + non-residents) |
| `rail_line_through_m` | float64 | m | 0.0 | 0 → 3704 (median 0) | Rail line length through hex (above + underground) |
| `road_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 271 (median 27.54) | Road km per km² |
| `road_intersection_density_per_km2` | float64 | count/km² | 0.0 | 0 → 1248 (median 114.3) | Vehicle-network nodes with deg ≥ 3 per km² (Jacobs) |
| `road_length_total_m` | float64 | m | 0.0 | 0 → 2.846e+04 (median 2892) | Total OSM road length clipped to hex |
| `road_max_class_through` | str | categorical | 0.0 | 13 unique · `none` | Highest road class running through hex |
| `road_walkable_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.2475) | Pedestrian-only roads as fraction of total |
| `signalized_crossing_count` | float64 | count | 0.0 | 0 → 143 (median 0) | LTA traffic signals in hex |
| `transit_score` | float64 | score [0,1] | 0.0 | 2.754e-08 → 0.9879 (median 0.3227) | 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) |
| `walk_amenities_400m` | int64 | count | 0.0 | 0 → 2111 (median 5) | Place count within 400m walk |
| `walk_clinic_400m` | int64 | count | 0.0 | 0 → 321 (median 0) | Clinics within 400m walk |
| `walk_convenience_400m` | int64 | count | 0.0 | 0 → 58 (median 0) | Convenience stores within 400m walk |
| `walk_food_400m` | int64 | count | 0.0 | 0 → 491 (median 0) | Food places within 400m walk |
| `walk_hawker_400m` | int64 | count | 0.0 | 0 → 160 (median 0) | Hawkers within 400m walk |
| `walk_park_400m` | int64 | count | 0.0 | 0 → 10 (median 0) | Parks within 400m walk |
| `walk_school_400m` | int64 | count | 0.0 | 0 → 131 (median 0) | Schools within 400m walk |
| `walk_supermarket_400m` | int64 | count | 0.0 | 0 → 42 (median 0) | Supermarkets within 400m walk |
| `walkability_score` | float64 | score [0,1] | 0.0 | 0 → 0.9587 (median 0.2351) | Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |
| `wp_pop` | float64 | persons | 0.0 | 0 → 1.645e+04 (median 0) | WorldPop count per hex (single snapshot — only one valid TIF available) |

## `hex/hex9_buildings.parquet`

_39 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `avg_floors` | Float64 |  | 67.3 | 0.5 → 60 (median 6.5) |  |
| `avg_height` | float64 |  | 91.4 | 0 → 182 (median 0) |  |
| `best_avg_floors` | Float64 | floors | 66.4 | 0.5 → 60 (median 13) | Avg floor count |
| `best_max_floors` | Float64 | floors | 66.4 | 1 → 70 (median 18) | Max floor count (Overture or HDB authoritative) |
| `bldg_commercial_area_m2` | float64 |  | 0.0 | 0 → 6.799e+04 (median 0) |  |
| `bldg_commercial_count` | float64 | count | 0.0 | 0 → 87 (median 0) | Commercial buildings |
| `bldg_commercial_share` | float64 |  | 0.0 | 0 → 1 (median 0) |  |
| `bldg_count` | float64 | count | 0.0 | 0 → 518 (median 17) | Building footprints in hex (Overture + HDB + OSM) |
| `bldg_density_per_km2` | float64 | count/km² | 0.0 | 0 → 4933 (median 161.9) | Buildings per km² |
| `bldg_footprint_share` | float64 | ratio [0,1] | 0.0 | 0 → 3.371 (median 0.0577) | Footprint as fraction of hex area (clipped, ≤1) |
| `bldg_industrial_area_m2` | float64 |  | 0.0 | 0 → 1.822e+05 (median 0) |  |
| `bldg_industrial_count` | float64 | count | 0.0 | 0 → 69 (median 0) | Industrial buildings |
| `bldg_industrial_share` | float64 |  | 0.0 | 0 → 1 (median 0) |  |
| `bldg_institutional_area_m2` | float64 |  | 0.0 | 0 → 7.197e+04 (median 0) |  |
| `bldg_institutional_count` | float64 | count | 0.0 | 0 → 21 (median 0) | Institutional buildings |
| `bldg_other_area_m2` | float64 |  | 0.0 | 0 → 2.019e+04 (median 0) |  |
| `bldg_other_count` | float64 |  | 0.0 | 0 → 26 (median 0) |  |
| `bldg_religious_area_m2` | float64 |  | 0.0 | 0 → 1.075e+04 (median 0) |  |
| `bldg_religious_count` | float64 |  | 0.0 | 0 → 14 (median 0) |  |
| `bldg_residential_area_m2` | float64 |  | 0.0 | 0 → 7.518e+04 (median 0) |  |
| `bldg_residential_count` | float64 | count | 0.0 | 0 → 454 (median 0) | Residential buildings |
| `bldg_residential_share` | float64 |  | 0.0 | 0 → 1 (median 0) |  |
| `bldg_total_area_m2` | float64 | m² | 0.0 | 0 → 3.539e+05 (median 6056) | Total building footprint area |
| `bldg_transport_area_m2` | float64 |  | 0.0 | 0 → 8.474e+04 (median 0) |  |
| `bldg_transport_count` | float64 |  | 0.0 | 0 → 6 (median 0) |  |
| `bldg_unclassified_area_m2` | float64 |  | 0.0 | 0 → 3.539e+05 (median 2308) |  |
| `bldg_unclassified_count` | float64 |  | 0.0 | 0 → 418 (median 14) |  |
| `hdb_avg_floors` | float64 | floors | 83.8 | 3 → 45 (median 21) | Avg HDB floor count |
| `hdb_avg_year` | float64 | year | 83.8 | 1937 → 2024 (median 1981) | Avg HDB completion year |
| `hdb_block_count` | float64 | count | 0.0 | 0 → 110 (median 0) | HDB blocks (authoritative) |
| `hdb_dwelling_units` | float64 | count | 0.0 | 0 → 1.07e+04 (median 0) | Total dwelling units across HDB blocks |
| `hdb_max_floors` | float64 | floors | 83.8 | 3 → 50 (median 27) | Max HDB floor count |
| `hdb_min_year` | float64 | year | 83.8 | 1937 → 2024 (median 1976) | Earliest HDB completion year |
| `hex9_id` | str | string | 0.0 | 7318 unique · `896520c0007ffff` | H3 resolution-9 cell ID (~0.105 km², 174m edge) |
| `is_highrise` | boolean | bool | 0.0 | 0 → 1 (median 0) | True if max_floors >= 10 |
| `lat` | float64 | degrees | 0.0 | 1.159 → 1.472 (median 1.352) | Hex centroid latitude |
| `lng` | float64 | degrees | 0.0 | 103.6 → 104.1 (median 103.8) | Hex centroid longitude |
| `max_floors` | Float64 |  | 67.3 | 1 → 70 (median 12) |  |
| `max_height` | float64 |  | 91.4 | 0 → 245 (median 0) |  |

## `hex/hex9_buildings_clean.parquet`

_20 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `best_max_floors` | float64 | floors | 63.6 | 1 → 70 (median 16.5) | Max floor count (Overture or HDB authoritative) |
| `bldg_commercial_count` | float64 | count | 0.0 | 0 → 87 (median 0) | Commercial buildings |
| `bldg_count` | float64 | count | 0.0 | 0 → 541 (median 20) | Building footprints in hex (Overture + HDB + OSM) |
| `bldg_density_per_km2` | float64 | count/km² | 0.0 | 0 → 5152 (median 190.5) | Buildings per km² |
| `bldg_footprint_m2` | float64 | m² | 0.0 | 0 → 1.213e+05 (median 6765) | Total clipped building footprint area in hex |
| `bldg_footprint_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0644) | Footprint as fraction of hex area (clipped, ≤1) |
| `bldg_industrial_count` | float64 | count | 0.0 | 0 → 71 (median 0) | Industrial buildings |
| `bldg_institutional_count` | float64 | count | 0.0 | 0 → 27 (median 0) | Institutional buildings |
| `bldg_residential_count` | float64 | count | 0.0 | 0 → 474 (median 0) | Residential buildings |
| `est_built_far` | float64 | ratio | 0.0 | 0 → 10.03 (median 0.2165) | Estimated built-up FAR = total floor area / hex area |
| `est_total_floor_area_m2` | float64 | m² | 0.0 | 0 → 1.053e+06 (median 2.273e+04) | Sum of footprint × est_floors per building |
| `hdb_avg_age_years` | float64 | years | 83.8 | 2 → 65 (median 44.97) | Avg years since HDB completion (year_completed filtered ≥1960) |
| `hdb_block_count` | float64 | count | 0.0 | 0 → 110 (median 0) | HDB blocks (authoritative) |
| `hdb_dwelling_units` | float64 | count | 0.0 | 0 → 1.055e+04 (median 0) | Total dwelling units across HDB blocks |
| `hdb_max_floors` | float64 | floors | 83.8 | 3 → 50 (median 27) | Max HDB floor count |
| `hex9_id` | str | string | 0.0 | 7318 unique · `896520c0007ffff` | H3 resolution-9 cell ID (~0.105 km², 174m edge) |
| `is_highrise` | bool | bool | 0.0 | 0 → 1 (median 0) | True if max_floors >= 10 |
| `n_highrise_bldgs` | float64 | count | 0.0 | 0 → 474 (median 0) | Number of buildings with floors ≥ 10 |
| `parent_hex8` | str | string | 0.0 | 1191 unique · `886520c001fffff` | hex-9's parent hex-8 |
| `parent_subzone` | str | string | 0.0 | 326 unique · `TSSZ06` | URA subzone parent (max-overlap) |

## `hex/hex9_built_environment_features.parquet`

_41 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `avg_gpr` | float64 | ratio | 0.0 | 0 → 21.96 (median 0) | Area-weighted Gross Plot Ratio |
| `best_max_floors` | float64 | floors | 0.0 | 0 → 70 (median 0) | Max floor count (Overture or HDB authoritative) |
| `bldg_commercial_count` | float64 | count | 0.0 | 0 → 87 (median 0) | Commercial buildings |
| `bldg_count` | float64 | count | 0.0 | 0 → 541 (median 20) | Building footprints in hex (Overture + HDB + OSM) |
| `bldg_density_per_km2` | float64 | count/km² | 0.0 | 0 → 5152 (median 190.5) | Buildings per km² |
| `bldg_footprint_m2` | float64 | m² | 0.0 | 0 → 1.213e+05 (median 6765) | Total clipped building footprint area in hex |
| `bldg_footprint_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0644) | Footprint as fraction of hex area (clipped, ≤1) |
| `bldg_industrial_count` | float64 | count | 0.0 | 0 → 71 (median 0) | Industrial buildings |
| `bldg_institutional_count` | float64 | count | 0.0 | 0 → 27 (median 0) | Institutional buildings |
| `bldg_residential_count` | float64 | count | 0.0 | 0 → 474 (median 0) | Residential buildings |
| `dominant_use` | str | categorical | 0.0 | 14 unique · `transport` | Bucket with highest area share |
| `est_built_far` | float64 | ratio | 0.0 | 0 → 10.03 (median 0.2165) | Estimated built-up FAR = total floor area / hex area |
| `est_total_floor_area_m2` | float64 | m² | 0.0 | 0 → 1.053e+06 (median 2.273e+04) | Sum of footprint × est_floors per building |
| `hdb_avg_age_years` | float64 | years | 0.0 | 0 → 65 (median 0) | Avg years since HDB completion (year_completed filtered ≥1960) |
| `hdb_block_count` | float64 | count | 0.0 | 0 → 110 (median 0) | HDB blocks (authoritative) |
| `hdb_dwelling_units` | float64 | count | 0.0 | 0 → 1.055e+04 (median 0) | Total dwelling units across HDB blocks |
| `hdb_max_floors` | float64 | floors | 0.0 | 0 → 50 (median 0) | Max HDB floor count |
| `hex9_id` | str | string | 0.0 | 7318 unique · `896520c0007ffff` | H3 resolution-9 cell ID (~0.105 km², 174m edge) |
| `is_highrise` | bool | bool | 0.0 | 0 → 1 (median 0) | True if max_floors >= 10 |
| `lu_business_park_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8105 (median 0) | Business park share |
| `lu_business_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Land area share zoned business (industrial) |
| `lu_commercial_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9317 (median 0) | Land area share zoned commercial |
| `lu_educational_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Educational institution share |
| `lu_entropy` | float64 | nats | 0.0 | -0 → 2.084 (median 0.514) | Shannon entropy across 14 LU buckets |
| `lu_health_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8857 (median 0) | Health & medical share |
| `lu_hotel_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8988 (median 0) | Hotel zone share |
| `lu_institutional_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Civic/community/place-of-worship |
| `lu_mixed_use_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.6274 (median 0) | Mixed-use zone share (residential + commercial) |
| `lu_open_space_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0026) | Park / open space share |
| `lu_other_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0 (median 0) | Other / unmapped |
| `lu_parcel_count` | int64 | count | 0.0 | 1 → 533 (median 5) | URA parcels intersecting hex |
| `lu_reserve_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Reserve site share |
| `lu_residential_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Land area share zoned residential |
| `lu_total_m2` | float64 | m² | 0.0 | 0.02469 → 1.308e+05 (median 1.191e+05) | Total land area covered by URA parcels in hex |
| `lu_transport_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0926) | Transport infra share |
| `lu_utility_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Utility infra share |
| `lu_water_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Water body share |
| `max_gpr` | float64 | ratio | 0.0 | 0 → 25 (median 0) | Max GPR within hex |
| `n_highrise_bldgs` | float64 | count | 0.0 | 0 → 474 (median 0) | Number of buildings with floors ≥ 10 |
| `parent_hex8` | str | string | 0.0 | 1191 unique · `886520c001fffff` | hex-9's parent hex-8 |
| `parent_subzone` | str | string | 0.0 | 326 unique · `TSSZ06` | URA subzone parent (max-overlap) |

## `hex/hex9_land_use.parquet`

_22 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `avg_gpr` | float64 | ratio | 52.8 | 0.9014 → 21.96 (median 2.5) | Area-weighted Gross Plot Ratio |
| `dominant_use` | str | categorical | 0.0 | 14 unique · `transport` | Bucket with highest area share |
| `hex9_id` | str | string | 0.0 | 7318 unique · `896520c0007ffff` | H3 resolution-9 cell ID (~0.105 km², 174m edge) |
| `lu_business_park_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8105 (median 0) | Business park share |
| `lu_business_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Land area share zoned business (industrial) |
| `lu_commercial_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9317 (median 0) | Land area share zoned commercial |
| `lu_educational_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Educational institution share |
| `lu_entropy` | float64 | nats | 0.0 | -0 → 2.084 (median 0.514) | Shannon entropy across 14 LU buckets |
| `lu_health_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8857 (median 0) | Health & medical share |
| `lu_hotel_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8988 (median 0) | Hotel zone share |
| `lu_institutional_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Civic/community/place-of-worship |
| `lu_mixed_use_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.6274 (median 0) | Mixed-use zone share (residential + commercial) |
| `lu_open_space_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0026) | Park / open space share |
| `lu_other_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0 (median 0) | Other / unmapped |
| `lu_parcel_count` | int64 | count | 0.0 | 1 → 533 (median 5) | URA parcels intersecting hex |
| `lu_reserve_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Reserve site share |
| `lu_residential_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Land area share zoned residential |
| `lu_total_m2` | float64 | m² | 0.0 | 0.02469 → 1.308e+05 (median 1.191e+05) | Total land area covered by URA parcels in hex |
| `lu_transport_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0926) | Transport infra share |
| `lu_utility_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Utility infra share |
| `lu_water_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Water body share |
| `max_gpr` | float64 | ratio | 52.8 | 1 → 25 (median 2.5) | Max GPR within hex |

## `hex/hex9_mobility_features.parquet`

_53 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `bridge_length_m` | float64 | m | 0.0 | 0 → 4369 (median 0) | Bridge segment length |
| `bus_routes_per_stop_max` | float64 | count | 0.0 | 0 → 50 (median 0) | Max # routes serving a stop in hex (GTFS) |
| `bus_routes_per_stop_mean` | float64 | count | 0.0 | 0 → 50 (median 0) | Mean routes/stop in hex |
| `bus_stop_count` | float64 | count | 0.0 | 0 → 13 (median 0) | Bus stops in hex |
| `centr_betweenness_max` | float64 | ratio | 0.0 | 0 → 0.108 (median 0) | Max betweenness centrality of major-road nodes |
| `centr_bridge_count` | float64 | count | 0.0 | 0 → 31 (median 0) | Tarjan bridge endpoints (network cut points) |
| `daily_bus_taps` | float64 | taps/day | 0.0 | 0 → 1.042e+05 (median 0) | Daily bus taps (Dec 2025 LTA monthly / 31) |
| `daily_train_taps` | float64 | taps/day | 0.0 | 0 → 2.212e+05 (median 0) | Daily MRT/LRT taps (Jan 2026 LTA monthly / 31) |
| `dist_bus_m` | float64 | m | 0.0 | 5.326 → 1.373e+04 (median 463.5) | Centroid distance to nearest bus stop |
| `dist_expressway_m` | float64 | m | 0.0 | 0.00143 → 1.409e+04 (median 1463) | Centroid distance to nearest motorway/trunk segment |
| `dist_mrt_exit_m` | float64 | m | 0.0 | 7.807 → 1.413e+04 (median 1762) | Centroid distance to nearest MRT exit |
| `dist_mrt_m` | float64 | m | 0.0 | 0 → 1.409e+04 (median 1657) | Centroid distance to nearest MRT/LRT station |
| `dist_walk_clinic_m` | float64 | m | 0.0 | 1.673 → 1.639e+04 (median 1102) | Walk distance to nearest clinic |
| `dist_walk_convenience_m` | float64 | m | 0.0 | 3.638 → 1.41e+04 (median 755.2) | Walk distance to nearest convenience store |
| `dist_walk_food_m` | float64 | m | 0.0 | 1.963 → 1.636e+04 (median 645) | Walk distance to nearest restaurant/cafe/hawker/bakery/fast-food |
| `dist_walk_hawker_m` | float64 | m | 0.0 | 1.963 → 1.638e+04 (median 1202) | Walk distance to nearest hawker (Euclidean × 1.3 detour) |
| `dist_walk_park_m` | float64 | m | 0.0 | 0 → 2.091e+04 (median 1222) | Walk distance to nearest park |
| `dist_walk_school_m` | float64 | m | 0.0 | 2.142 → 1.625e+04 (median 845.2) | Walk distance to nearest school |
| `dist_walk_supermarket_m` | float64 | m | 0.0 | 4.861 → 1.834e+04 (median 1055) | Walk distance to nearest supermarket |
| `expressway_severance` | bool | bool | 0.0 | 0 → 1 (median 0) | Expressway < 200m AND no exit < 400m (barrier without benefit) |
| `gtfs_headway_am_min` | float64 | min | 0.0 | 0.1389 → 999 (median 999) | Best AM-peak headway (lowest minutes between buses) at any stop in hex |
| `hdb_mscp_count` | float64 | count | 0.0 | 0 → 7 (median 0) | Authoritative HDB multi-storey carparks |
| `hex9_id` | str | string | 0.0 | 7318 unique · `896520c0007ffff` | H3 resolution-9 cell ID (~0.105 km², 174m edge) |
| `is_mrt_interchange` | bool | bool | 0.0 | 0 → 1 (median 0) | True if any station has ≥2 lines (slash-PT_CODE) |
| `lane_km_per_km2` | float64 | km/km² | 0.0 | 0 → 147.7 (median 17.13) | Lane-km per km² (lane count × length / area) |
| `mrt_exit_count` | float64 | count | 0.0 | 0 → 10 (median 0) | MRT exits in hex |
| `mrt_station_count` | float64 | count | 0.0 | 0 → 3 (median 0) | MRT/LRT stations in hex |
| `near_bus_300m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if bus < 300m |
| `near_expressway_exit_400m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if motorway_link/trunk_link < 400m (drive-thru flag) |
| `near_mrt_400m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if MRT < 400m |
| `oneway_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0407) | Fraction of vehicular length that's one-way |
| `parent_hex8` | str | string | 0.0 | 1191 unique · `886520c001fffff` | hex-9's parent hex-8 |
| `parent_subzone` | str | string | 0.0 | 326 unique · `TSSZ06` | URA subzone parent (max-overlap) |
| `parking_lot_count` | float64 | count | 0.0 | 0 → 15 (median 0) | OSM amenity=parking points |
| `ped_path_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 228.6 (median 6.367) | Pedestrian-network density |
| `ped_path_length_m` | float64 | m | 0.0 | 0 → 2.4e+04 (median 668.6) | Footway + path + cycleway + steps length |
| `rail_line_through_m` | float64 | m | 0.0 | 0 → 3704 (median 0) | Rail line length through hex (above + underground) |
| `road_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 271 (median 27.54) | Road km per km² |
| `road_intersection_density_per_km2` | float64 | count/km² | 0.0 | 0 → 1248 (median 114.3) | Vehicle-network nodes with deg ≥ 3 per km² (Jacobs) |
| `road_length_total_m` | float64 | m | 0.0 | 0 → 2.846e+04 (median 2892) | Total OSM road length clipped to hex |
| `road_max_class_through` | str | categorical | 0.0 | 13 unique · `none` | Highest road class running through hex |
| `road_walkable_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.2475) | Pedestrian-only roads as fraction of total |
| `signalized_crossing_count` | float64 | count | 0.0 | 0 → 143 (median 0) | LTA traffic signals in hex |
| `transit_score` | float64 | score [0,1] | 0.0 | 2.754e-08 → 0.9879 (median 0.3227) | 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) |
| `walk_amenities_400m` | int64 | count | 0.0 | 0 → 2111 (median 5) | Place count within 400m walk |
| `walk_clinic_400m` | int64 | count | 0.0 | 0 → 321 (median 0) | Clinics within 400m walk |
| `walk_convenience_400m` | int64 | count | 0.0 | 0 → 58 (median 0) | Convenience stores within 400m walk |
| `walk_food_400m` | int64 | count | 0.0 | 0 → 491 (median 0) | Food places within 400m walk |
| `walk_hawker_400m` | int64 | count | 0.0 | 0 → 160 (median 0) | Hawkers within 400m walk |
| `walk_park_400m` | int64 | count | 0.0 | 0 → 10 (median 0) | Parks within 400m walk |
| `walk_school_400m` | int64 | count | 0.0 | 0 → 131 (median 0) | Schools within 400m walk |
| `walk_supermarket_400m` | int64 | count | 0.0 | 0 → 42 (median 0) | Supermarkets within 400m walk |
| `walkability_score` | float64 | score [0,1] | 0.0 | 0 → 0.9587 (median 0.2351) | Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |

## `hex/hex9_population.parquet`

_14 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `hex9_id` | str | string | 0.0 | 7318 unique · `896520c0007ffff` | H3 resolution-9 cell ID (~0.105 km², 174m edge) |
| `nonres_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.1807) | Non-resident share of total pop |
| `parent_pa` | str | string | 0.0 | 55 unique · `TUAS` | URA planning area name (one of 55) |
| `parent_region` | str | string | 0.0 | 5 unique · `WEST REGION` | URA region (5 regions) |
| `parent_subzone_name` | str | string | 0.0 | 326 unique · `TUAS VIEW EXTENSION` | URA subzone full name |
| `pop_0_14` | float64 | persons | 0.0 | 0 → 1735 (median 0) | Population age 0-14 |
| `pop_15_64` | float64 | persons | 0.0 | 0 → 9803 (median 0.0664) | Population age 15-64 |
| `pop_65plus` | float64 | persons | 0.0 | 0 → 2108 (median 0.0027) | Population age 65+ |
| `pop_hdb` | float64 | persons | 0.0 | 0 → 1.27e+04 (median 0) | Residents in HDB flats |
| `pop_hdb_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | HDB share of resident pop |
| `pop_non_hdb` | float64 | persons | 0.0 | 0 → 2065 (median 0.0254) | Residents in non-HDB housing |
| `pop_nonresident` | float64 | persons | 0.0 | 0 → 5484 (median 51.87) | Non-residents (FW + EP + MDW) |
| `pop_resident` | float64 | persons | 0.0 | 0 → 1.332e+04 (median 0.0976) | Resident population (citizens + PRs) |
| `pop_total_all` | float64 | persons | 0.0 | 0 → 1.426e+04 (median 114.2) | Total population (residents + non-residents) |

## `hex/hex9_roads_clean.parquet`

_18 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `bridge_length_m` | float64 | m | 0.0 | 0 → 4369 (median 0) | Bridge segment length |
| `centr_betweenness_max` | float64 | ratio | 0.0 | 0 → 0.108 (median 0) | Max betweenness centrality of major-road nodes |
| `centr_bridge_count` | float64 | count | 0.0 | 0 → 31 (median 0) | Tarjan bridge endpoints (network cut points) |
| `dist_expressway_m` | float64 | m | 0.0 | 0.00143 → 1.409e+04 (median 1463) | Centroid distance to nearest motorway/trunk segment |
| `hdb_mscp_count` | float64 | count | 0.0 | 0 → 7 (median 0) | Authoritative HDB multi-storey carparks |
| `hex9_id` | str | string | 0.0 | 7318 unique · `896520c0007ffff` | H3 resolution-9 cell ID (~0.105 km², 174m edge) |
| `lane_km_per_km2` | float64 | km/km² | 0.0 | 0 → 147.7 (median 17.13) | Lane-km per km² (lane count × length / area) |
| `near_expressway_exit_400m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if motorway_link/trunk_link < 400m (drive-thru flag) |
| `oneway_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0407) | Fraction of vehicular length that's one-way |
| `parent_hex8` | str | string | 0.0 | 1191 unique · `886520c001fffff` | hex-9's parent hex-8 |
| `parent_subzone` | str | string | 0.0 | 326 unique · `TSSZ06` | URA subzone parent (max-overlap) |
| `parking_lot_count` | float64 | count | 0.0 | 0 → 15 (median 0) | OSM amenity=parking points |
| `road_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 271 (median 27.54) | Road km per km² |
| `road_intersection_density_per_km2` | float64 | count/km² | 0.0 | 0 → 1248 (median 114.3) | Vehicle-network nodes with deg ≥ 3 per km² (Jacobs) |
| `road_length_total_m` | float64 | m | 0.0 | 0 → 2.846e+04 (median 2892) | Total OSM road length clipped to hex |
| `road_max_class_through` | str | categorical | 0.0 | 13 unique · `none` | Highest road class running through hex |
| `road_walkable_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.2475) | Pedestrian-only roads as fraction of total |
| `signalized_crossing_count` | float64 | count | 0.0 | 0 → 143 (median 0) | LTA traffic signals in hex |

## `hex/hex9_satellite.parquet`

_11 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `hex9_id` | str | string | 0.0 | 7318 unique · `896520c0007ffff` | H3 resolution-9 cell ID (~0.105 km², 174m edge) |
| `nl_2022` | float64 | nanoWatts/cm²/sr | 0.0 | 0 → 153.6 (median 46.03) | VIIRS night light radiance 2022 (subzone-broadcast) |
| `nl_2024` | float64 | nanoWatts/cm²/sr | 0.0 | 0 → 179.5 (median 48.49) | VIIRS night light radiance 2024 (subzone-broadcast) |
| `nl_change_pct` | float64 | % | 0.0 | -28.01 → 120.4 (median 4.41) | VIIRS 2022→2024 brightness change |
| `nl_commercial_indicator` | float64 | composite | 0.0 | 0 → 167.3 (median 28.12) | nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) |
| `nl_decline_zone` | bool | bool | 0.0 | 0 → 1 (median 0) | True if night light declined ≥ 20% |
| `nl_growth_corridor` | bool | bool | 0.0 | 0 → 1 (median 0) | True if night light grew ≥ 20% |
| `nl_per_capita` | float64 | radiance/person | 0.0 | 0 → 2.997 (median 0) | nl_2024 / pop_resident (commercial vs residential signal) |
| `parent_hex8` | str | string | 0.0 | 1191 unique · `886520c001fffff` | hex-9's parent hex-8 |
| `parent_subzone` | str | string | 0.0 | 326 unique · `TSSZ06` | URA subzone parent (max-overlap) |
| `wp_pop` | float64 | persons | 0.0 | 0 → 1.645e+04 (median 0) | WorldPop count per hex (single snapshot — only one valid TIF available) |

## `hex/hex9_transit_clean.parquet`

_19 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `bus_routes_per_stop_max` | float64 | count | 0.0 | 0 → 50 (median 0) | Max # routes serving a stop in hex (GTFS) |
| `bus_routes_per_stop_mean` | float64 | count | 0.0 | 0 → 50 (median 0) | Mean routes/stop in hex |
| `bus_stop_count` | float64 | count | 0.0 | 0 → 13 (median 0) | Bus stops in hex |
| `daily_bus_taps` | float64 | taps/day | 0.0 | 0 → 1.042e+05 (median 0) | Daily bus taps (Dec 2025 LTA monthly / 31) |
| `daily_train_taps` | float64 | taps/day | 0.0 | 0 → 2.212e+05 (median 0) | Daily MRT/LRT taps (Jan 2026 LTA monthly / 31) |
| `dist_bus_m` | float64 | m | 0.0 | 5.326 → 1.373e+04 (median 463.5) | Centroid distance to nearest bus stop |
| `dist_mrt_exit_m` | float64 | m | 0.0 | 7.807 → 1.413e+04 (median 1762) | Centroid distance to nearest MRT exit |
| `dist_mrt_m` | float64 | m | 0.0 | 0 → 1.409e+04 (median 1657) | Centroid distance to nearest MRT/LRT station |
| `gtfs_headway_am_min` | float64 | min | 0.0 | 0.1389 → 999 (median 999) | Best AM-peak headway (lowest minutes between buses) at any stop in hex |
| `hex9_id` | str | string | 0.0 | 7318 unique · `896520c0007ffff` | H3 resolution-9 cell ID (~0.105 km², 174m edge) |
| `is_mrt_interchange` | bool | bool | 0.0 | 0 → 1 (median 0) | True if any station has ≥2 lines (slash-PT_CODE) |
| `mrt_exit_count` | float64 | count | 0.0 | 0 → 10 (median 0) | MRT exits in hex |
| `mrt_station_count` | float64 | count | 0.0 | 0 → 3 (median 0) | MRT/LRT stations in hex |
| `near_bus_300m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if bus < 300m |
| `near_mrt_400m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if MRT < 400m |
| `parent_hex8` | str | string | 0.0 | 1191 unique · `886520c001fffff` | hex-9's parent hex-8 |
| `parent_subzone` | str | string | 0.0 | 326 unique · `TSSZ06` | URA subzone parent (max-overlap) |
| `rail_line_through_m` | float64 | m | 0.0 | 0 → 3704 (median 0) | Rail line length through hex (above + underground) |
| `transit_score` | float64 | score [0,1] | 0.0 | 2.754e-08 → 0.9879 (median 0.3227) | 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) |

## `hex/hex9_universe.parquet`

_8 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `hex9_id` | str | string | 0.0 | 7318 unique · `896520c0007ffff` | H3 resolution-9 cell ID (~0.105 km², 174m edge) |
| `lat` | float64 | degrees | 0.0 | 1.159 → 1.472 (median 1.352) | Hex centroid latitude |
| `lng` | float64 | degrees | 0.0 | 103.6 → 104.1 (median 103.8) | Hex centroid longitude |
| `parent_hex8` | str | string | 0.0 | 1191 unique · `886520c001fffff` | hex-9's parent hex-8 |
| `parent_pa` | str | string | 0.0 | 55 unique · `TUAS` | URA planning area name (one of 55) |
| `parent_region` | str | string | 0.0 | 5 unique · `WEST REGION` | URA region (5 regions) |
| `parent_subzone` | str | string | 0.0 | 326 unique · `TSSZ06` | URA subzone parent (max-overlap) |
| `parent_subzone_name` | str | string | 0.0 | 326 unique · `TUAS VIEW EXTENSION` | URA subzone full name |

## `hex/hex9_walkability.parquet`

_27 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `dist_walk_clinic_m` | float64 | m | 0.0 | 1.673 → 1.639e+04 (median 1102) | Walk distance to nearest clinic |
| `dist_walk_convenience_m` | float64 | m | 0.0 | 3.638 → 1.41e+04 (median 755.2) | Walk distance to nearest convenience store |
| `dist_walk_food_m` | float64 | m | 0.0 | 1.963 → 1.636e+04 (median 645) | Walk distance to nearest restaurant/cafe/hawker/bakery/fast-food |
| `dist_walk_hawker_m` | float64 | m | 0.0 | 1.963 → 1.638e+04 (median 1202) | Walk distance to nearest hawker (Euclidean × 1.3 detour) |
| `dist_walk_park_m` | float64 | m | 0.0 | 0 → 2.091e+04 (median 1222) | Walk distance to nearest park |
| `dist_walk_school_m` | float64 | m | 0.0 | 2.142 → 1.625e+04 (median 845.2) | Walk distance to nearest school |
| `dist_walk_supermarket_m` | float64 | m | 0.0 | 4.861 → 1.834e+04 (median 1055) | Walk distance to nearest supermarket |
| `expressway_severance` | bool | bool | 0.0 | 0 → 1 (median 0) | Expressway < 200m AND no exit < 400m (barrier without benefit) |
| `hex9_id` | str | string | 0.0 | 7318 unique · `896520c0007ffff` | H3 resolution-9 cell ID (~0.105 km², 174m edge) |
| `near_bus_300m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if bus < 300m |
| `near_mrt_400m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if MRT < 400m |
| `parent_hex8` | str | string | 0.0 | 1191 unique · `886520c001fffff` | hex-9's parent hex-8 |
| `parent_subzone` | str | string | 0.0 | 326 unique · `TSSZ06` | URA subzone parent (max-overlap) |
| `ped_path_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 228.6 (median 6.367) | Pedestrian-network density |
| `ped_path_length_m` | float64 | m | 0.0 | 0 → 2.4e+04 (median 668.6) | Footway + path + cycleway + steps length |
| `road_intersection_density_per_km2` | float64 | count/km² | 0.0 | 0 → 1248 (median 114.3) | Vehicle-network nodes with deg ≥ 3 per km² (Jacobs) |
| `road_walkable_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.2475) | Pedestrian-only roads as fraction of total |
| `signalized_crossing_count` | float64 | count | 0.0 | 0 → 143 (median 0) | LTA traffic signals in hex |
| `walk_amenities_400m` | int64 | count | 0.0 | 0 → 2111 (median 5) | Place count within 400m walk |
| `walk_clinic_400m` | int64 | count | 0.0 | 0 → 321 (median 0) | Clinics within 400m walk |
| `walk_convenience_400m` | int64 | count | 0.0 | 0 → 58 (median 0) | Convenience stores within 400m walk |
| `walk_food_400m` | int64 | count | 0.0 | 0 → 491 (median 0) | Food places within 400m walk |
| `walk_hawker_400m` | int64 | count | 0.0 | 0 → 160 (median 0) | Hawkers within 400m walk |
| `walk_park_400m` | int64 | count | 0.0 | 0 → 10 (median 0) | Parks within 400m walk |
| `walk_school_400m` | int64 | count | 0.0 | 0 → 131 (median 0) | Schools within 400m walk |
| `walk_supermarket_400m` | int64 | count | 0.0 | 0 → 42 (median 0) | Supermarkets within 400m walk |
| `walkability_score` | float64 | score [0,1] | 0.0 | 0 → 0.9587 (median 0.2351) | Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |

## `hex/subzone_all_features.parquet`

_88 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `avg_gpr` | float64 | ratio | 0.0 | 0 → 14.7 (median 2.513) | Area-weighted Gross Plot Ratio |
| `best_max_floors` | float64 | floors | 0.0 | 0 → 70 (median 30) | Max floor count (Overture or HDB authoritative) |
| `bldg_commercial_count` | float64 | count | 0.0 | 0 → 205 (median 2) | Commercial buildings |
| `bldg_count` | float64 | count | 0.0 | 0 → 1.313e+04 (median 480.5) | Building footprints in hex (Overture + HDB + OSM) |
| `bldg_density_per_km2` | float64 | count/km² | 0.0 | 0 → 5030 (median 375.8) | Buildings per km² |
| `bldg_footprint_m2` | float64 | m² | 0.0 | 0 → 3.748e+06 (median 2.278e+05) | Total clipped building footprint area in hex |
| `bldg_footprint_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.1835) | Footprint as fraction of hex area (clipped, ≤1) |
| `bldg_industrial_count` | float64 | count | 0.0 | 0 → 647 (median 1) | Industrial buildings |
| `bldg_institutional_count` | float64 | count | 0.0 | 0 → 88 (median 1) | Institutional buildings |
| `bldg_residential_count` | float64 | count | 0.0 | 0 → 1998 (median 78) | Residential buildings |
| `bridge_length_m` | float64 | m | 0.0 | 0 → 7.355e+04 (median 2034) | Bridge segment length |
| `bus_stop_count` | float64 | count | 0.0 | 0 → 104 (median 14) | Bus stops in hex |
| `centr_betweenness_max` | float64 | ratio | 0.0 | 0 → 0.108 (median 0.0161) | Max betweenness centrality of major-road nodes |
| `centr_bridge_count` | float64 | count | 0.0 | 0 → 64 (median 4) | Tarjan bridge endpoints (network cut points) |
| `daily_bus_taps` | float64 | taps/day | 0.0 | 0 → 2.076e+05 (median 9208) | Daily bus taps (Dec 2025 LTA monthly / 31) |
| `daily_train_taps` | float64 | taps/day | 0.0 | 0 → 3.573e+05 (median 0) | Daily MRT/LRT taps (Jan 2026 LTA monthly / 31) |
| `dist_bus_m` | float64 | m | 0.0 | 0 → 9542 (median 35.1) | Centroid distance to nearest bus stop |
| `dist_expressway_m` | float64 | m | 0.0 | 0 → 9553 (median 31.3) | Centroid distance to nearest motorway/trunk segment |
| `dist_mrt_m` | float64 | m | 0.0 | 0 → 9633 (median 97.94) | Centroid distance to nearest MRT/LRT station |
| `dominant_use` | str | categorical | 0.0 | 13 unique · `mixed_use` | Bucket with highest area share |
| `est_built_far` | float64 | ratio | 0.0 | 0 → 7.347 (median 1.069) | Estimated built-up FAR = total floor area / hex area |
| `est_total_floor_area_m2` | float64 | m² | 0.0 | 0 → 1.054e+07 (median 1.494e+06) | Sum of footprint × est_floors per building |
| `expressway_in_subzone` | object |  | 17.2 | 2 unique · `True` |  |
| `expressway_severance` | object | bool | 17.2 | 2 unique · `False` | Expressway < 200m AND no exit < 400m (barrier without benefit) |
| `has_interchange` | object |  | 17.2 | 2 unique · `False` |  |
| `has_mrt` | object |  | 17.2 | 2 unique · `False` |  |
| `hdb_block_count` | float64 | count | 0.0 | 0 → 416 (median 11) | HDB blocks (authoritative) |
| `hdb_dwelling_units` | float64 | count | 0.0 | 0 → 3.249e+04 (median 922.6) | Total dwelling units across HDB blocks |
| `hdb_mscp_count` | float64 | count | 0.0 | 0 → 42 (median 1) | Authoritative HDB multi-storey carparks |
| `lane_km_per_km2` | float64 | km/km² | 0.0 | 0 → 97.19 (median 50.21) | Lane-km per km² (lane count × length / area) |
| `lu_business_park_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.6194 (median 0) | Business park share |
| `lu_business_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9114 (median 0.0125) | Land area share zoned business (industrial) |
| `lu_commercial_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.6369 (median 0.0008) | Land area share zoned commercial |
| `lu_educational_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.79 (median 0.0212) | Educational institution share |
| `lu_entropy` | float64 | nats | 0.0 | 0.021 → 2.115 (median 1.424) | Shannon entropy across 14 LU buckets |
| `lu_health_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.371 (median 0) | Health & medical share |
| `lu_hotel_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.1804 (median 0) | Hotel zone share |
| `lu_institutional_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9115 (median 0.0138) | Civic/community/place-of-worship |
| `lu_mixed_use_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.3615 (median 0.009) | Mixed-use zone share (residential + commercial) |
| `lu_open_space_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9969 (median 0.0483) | Park / open space share |
| `lu_other_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0 (median 0) | Other / unmapped |
| `lu_parcel_count` | int64 | count | 0.0 | 22 → 7026 (median 227.5) | URA parcels intersecting hex |
| `lu_reserve_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9576 (median 0.0127) | Reserve site share |
| `lu_residential_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8106 (median 0.3315) | Land area share zoned residential |
| `lu_total_m2` | float64 | m² | 0.0 | 1.19e+05 → 6.798e+07 (median 1.294e+06) | Total land area covered by URA parcels in hex |
| `lu_transport_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8373 (median 0.1926) | Transport infra share |
| `lu_utility_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.7739 (median 0.0027) | Utility infra share |
| `lu_water_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.7043 (median 0.012) | Water body share |
| `max_gpr` | float64 | ratio | 0.0 | 0 → 25 (median 3.5) | Max GPR within hex |
| `max_transit_score` | float64 |  | 0.0 | 0 → 0.9879 (median 0.7723) |  |
| `mrt_exit_count` | float64 | count | 0.0 | 0 → 33 (median 0) | MRT exits in hex |
| `mrt_station_count` | float64 | count | 0.0 | 0 → 6 (median 0) | MRT/LRT stations in hex |
| `n_hex8` | float64 |  | 0.0 | 0 → 121 (median 1.5) |  |
| `n_highrise_bldgs` | float64 | count | 0.0 | 0 → 1865 (median 65) | Number of buildings with floors ≥ 10 |
| `n_interchanges` | float64 |  | 0.0 | 0 → 2 (median 0) |  |
| `nl_2022` | float64 | nanoWatts/cm²/sr | 0.0 | 0 → 153.6 (median 58.86) | VIIRS night light radiance 2022 (subzone-broadcast) |
| `nl_2024` | float64 | nanoWatts/cm²/sr | 0.0 | 0 → 179.5 (median 63.89) | VIIRS night light radiance 2024 (subzone-broadcast) |
| `nl_change_pct` | float64 | % | 0.0 | -28.01 → 120.4 (median 8.999) | VIIRS 2022→2024 brightness change |
| `nl_commercial_indicator` | float64 | composite | 0.0 | 0 → 165 (median 30.88) | nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) |
| `nl_decline_zone` | bool | bool | 0.0 | 0 → 1 (median 0) | True if night light declined ≥ 20% |
| `nl_growth_corridor` | bool | bool | 0.0 | 0 → 1 (median 0) | True if night light grew ≥ 20% |
| `nl_per_capita` | float64 | radiance/person | 0.0 | 0 → 1.61 (median 0.0463) | nl_2024 / pop_resident (commercial vs residential signal) |
| `nonres_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.3111) | Non-resident share of total pop |
| `parking_lot_count` | float64 | count | 0.0 | 0 → 61 (median 6) | OSM amenity=parking points |
| `ped_path_length_m` | float64 | m | 0.0 | 0 → 3.072e+05 (median 3.284e+04) | Footway + path + cycleway + steps length |
| `pop_0_14` | float64 | persons | 0.0 | 0 → 1.543e+04 (median 761) | Population age 0-14 |
| `pop_15_64` | float64 | persons | 0.0 | 0 → 8.31e+04 (median 3572) | Population age 15-64 |
| `pop_65plus` | float64 | persons | 0.0 | 0 → 2.664e+04 (median 1087) | Population age 65+ |
| `pop_hdb` | float64 | persons | 0.0 | 0 → 1.134e+05 (median 2069) | Residents in HDB flats |
| `pop_hdb_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.5671) | HDB share of resident pop |
| `pop_non_hdb` | float64 | persons | 0.0 | 0 → 3.066e+04 (median 1224) | Residents in non-HDB housing |
| `pop_nonresident` | float64 | persons | 0.0 | 0 → 8.901e+04 (median 3539) | Non-residents (FW + EP + MDW) |
| `pop_resident` | float64 | persons | 0.0 | 0 → 1.252e+05 (median 5446) | Resident population (citizens + PRs) |
| `pop_total_all` | float64 | persons | 0.0 | 0 → 1.448e+05 (median 1.175e+04) | Total population (residents + non-residents) |
| `rail_line_through_m` | float64 | m | 0.0 | 0 → 2.05e+04 (median 1344) | Rail line length through hex (above + underground) |
| `road_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 264.1 (median 48.75) | Road km per km² |
| `road_intersection_count_total` | float64 |  | 0.0 | 0 → 5204 (median 350.5) |  |
| `road_intersection_density_per_km2` | float64 | count/km² | 0.0 | 0 → 1538 (median 255.7) | Vehicle-network nodes with deg ≥ 3 per km² (Jacobs) |
| `road_length_total_m` | float64 | m | 0.0 | 0 → 1.062e+06 (median 6.254e+04) | Total OSM road length clipped to hex |
| `road_max_class_through` | str | categorical | 17.2 | 8 unique · `motorway` | Highest road class running through hex |
| `road_walkable_share` | float64 | ratio [0,1] | 0.0 | 0 → 0.7701 (median 0.4667) | Pedestrian-only roads as fraction of total |
| `signalized_crossing_count` | float64 | count | 0.0 | 0 → 968 (median 104) | LTA traffic signals in hex |
| `subzone_area_km2` | float64 |  | 0.0 | 0 → 68.55 (median 1.231) |  |
| `subzone_area_m2` | float64 |  | 0.0 | 0 → 6.855e+07 (median 1.231e+06) |  |
| `subzone_c` | str | string | 0.0 | 326 unique · `AMSZ01` | URA subzone code |
| `walk_amenities_400m` | float64 | count | 0.0 | 0 → 1.562e+04 (median 974.5) | Place count within 400m walk |
| `walkability_score` | float64 | score [0,1] | 0.0 | 0 → 0.9132 (median 0.5462) | Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |
| `wp_pop` | float64 | persons | 0.0 | 0 → 1.618e+05 (median 1.504e+04) | WorldPop count per hex (single snapshot — only one valid TIF available) |

## `hex/subzone_buildings_clean.parquet`

_17 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `best_max_floors` | float64 | floors | 3.0 | 1 → 70 (median 38) | Max floor count (Overture or HDB authoritative) |
| `bldg_commercial_count` | float64 | count | 0.0 | 0 → 205 (median 3) | Commercial buildings |
| `bldg_count` | float64 | count | 0.0 | 1 → 1.313e+04 (median 621) | Building footprints in hex (Overture + HDB + OSM) |
| `bldg_density_per_km2` | float64 | count/km² | 0.0 | 0.6206 → 5030 (median 433.3) | Buildings per km² |
| `bldg_footprint_m2` | float64 | m² | 0.0 | 102.1 → 3.748e+06 (median 2.705e+05) | Total clipped building footprint area in hex |
| `bldg_footprint_share` | float64 | ratio [0,1] | 0.0 | 6.339e-05 → 1 (median 0.2178) | Footprint as fraction of hex area (clipped, ≤1) |
| `bldg_industrial_count` | float64 | count | 0.0 | 0 → 647 (median 3) | Industrial buildings |
| `bldg_institutional_count` | float64 | count | 0.0 | 0 → 88 (median 2) | Institutional buildings |
| `bldg_residential_count` | float64 | count | 0.0 | 0 → 1998 (median 109.5) | Residential buildings |
| `est_built_far` | float64 | ratio | 0.0 | 0.0001902 → 7.347 (median 1.254) | Estimated built-up FAR = total floor area / hex area |
| `est_total_floor_area_m2` | float64 | m² | 0.0 | 306.4 → 1.054e+07 (median 1.743e+06) | Sum of footprint × est_floors per building |
| `hdb_block_count` | float64 | count | 0.0 | 0 → 416 (median 27) | HDB blocks (authoritative) |
| `hdb_dwelling_units` | float64 | count | 0.0 | 0 → 3.249e+04 (median 2366) | Total dwelling units across HDB blocks |
| `n_hex8` | int64 |  | 0.0 | 1 → 121 (median 2) |  |
| `n_highrise_bldgs` | float64 | count | 0.0 | 0 → 1865 (median 90) | Number of buildings with floors ≥ 10 |
| `subzone_area_m2` | float64 |  | 0.0 | 2.36e+05 → 6.855e+07 (median 1.46e+06) |  |
| `subzone_c` | str | string | 0.0 | 270 unique · `AMSZ02` | URA subzone code |

## `hex/subzone_built_environment_features.parquet`

_38 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `avg_gpr` | float64 | ratio | 0.0 | 0 → 12.96 (median 2.61) | Area-weighted Gross Plot Ratio |
| `best_max_floors` | float64 | floors | 0.0 | 0 → 70 (median 36) | Max floor count (Overture or HDB authoritative) |
| `bldg_commercial_count` | float64 | count | 0.0 | 0 → 205 (median 3) | Commercial buildings |
| `bldg_count` | float64 | count | 0.0 | 1 → 1.313e+04 (median 621) | Building footprints in hex (Overture + HDB + OSM) |
| `bldg_density_per_km2` | float64 | count/km² | 0.0 | 0.6206 → 5030 (median 433.3) | Buildings per km² |
| `bldg_footprint_m2` | float64 | m² | 0.0 | 102.1 → 3.748e+06 (median 2.705e+05) | Total clipped building footprint area in hex |
| `bldg_footprint_share` | float64 | ratio [0,1] | 0.0 | 6.339e-05 → 1 (median 0.2178) | Footprint as fraction of hex area (clipped, ≤1) |
| `bldg_industrial_count` | float64 | count | 0.0 | 0 → 647 (median 3) | Industrial buildings |
| `bldg_institutional_count` | float64 | count | 0.0 | 0 → 88 (median 2) | Institutional buildings |
| `bldg_residential_count` | float64 | count | 0.0 | 0 → 1998 (median 109.5) | Residential buildings |
| `dominant_use` | str | categorical | 0.0 | 11 unique · `residential` | Bucket with highest area share |
| `est_built_far` | float64 | ratio | 0.0 | 0.0001902 → 7.347 (median 1.254) | Estimated built-up FAR = total floor area / hex area |
| `est_total_floor_area_m2` | float64 | m² | 0.0 | 306.4 → 1.054e+07 (median 1.743e+06) | Sum of footprint × est_floors per building |
| `hdb_block_count` | float64 | count | 0.0 | 0 → 416 (median 27) | HDB blocks (authoritative) |
| `hdb_dwelling_units` | float64 | count | 0.0 | 0 → 3.249e+04 (median 2366) | Total dwelling units across HDB blocks |
| `lu_business_park_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.3942 (median 0) | Business park share |
| `lu_business_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9423 (median 0.0208) | Land area share zoned business (industrial) |
| `lu_commercial_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.4369 (median 0.0006) | Land area share zoned commercial |
| `lu_educational_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.637 (median 0.0232) | Educational institution share |
| `lu_entropy` | float64 | nats | 0.0 | 0.009144 → 1.726 (median 0.9879) | Shannon entropy across 14 LU buckets |
| `lu_health_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.2255 (median 0) | Health & medical share |
| `lu_hotel_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.1651 (median 0) | Hotel zone share |
| `lu_institutional_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8335 (median 0.0133) | Civic/community/place-of-worship |
| `lu_mixed_use_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.1856 (median 0.0087) | Mixed-use zone share (residential + commercial) |
| `lu_open_space_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9591 (median 0.0561) | Park / open space share |
| `lu_other_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0 (median 0) | Other / unmapped |
| `lu_parcel_count` | int64 | count | 0.0 | 22 → 8931 (median 287.5) | URA parcels intersecting hex |
| `lu_reserve_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.863 (median 0.0165) | Reserve site share |
| `lu_residential_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8108 (median 0.3333) | Land area share zoned residential |
| `lu_total_m2` | float64 | m² | 0.0 | 4.709e+05 → 6.869e+07 (median 1.667e+06) | Total land area covered by URA parcels in hex |
| `lu_transport_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8517 (median 0.1831) | Transport infra share |
| `lu_utility_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.5228 (median 0.0031) | Utility infra share |
| `lu_water_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.5622 (median 0.0144) | Water body share |
| `max_gpr` | float64 | ratio | 0.0 | 0 → 25 (median 3.2) | Max GPR within hex |
| `n_hex8` | int64 |  | 0.0 | 1 → 121 (median 2) |  |
| `n_highrise_bldgs` | float64 | count | 0.0 | 0 → 1865 (median 90) | Number of buildings with floors ≥ 10 |
| `subzone_area_m2` | float64 |  | 0.0 | 2.36e+05 → 6.855e+07 (median 1.46e+06) |  |
| `subzone_c` | str | string | 0.0 | 270 unique · `AMSZ02` | URA subzone code |

## `hex/subzone_land_use.parquet`

_22 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `avg_gpr` | float64 | ratio | 0.0 | 0 → 14.7 (median 2.513) | Area-weighted Gross Plot Ratio |
| `dominant_use` | str | categorical | 0.0 | 13 unique · `mixed_use` | Bucket with highest area share |
| `lu_business_park_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.6194 (median 0) | Business park share |
| `lu_business_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9114 (median 0.0125) | Land area share zoned business (industrial) |
| `lu_commercial_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.6369 (median 0.0008) | Land area share zoned commercial |
| `lu_educational_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.79 (median 0.0212) | Educational institution share |
| `lu_entropy` | float64 | nats | 0.0 | 0.021 → 2.115 (median 1.424) | Shannon entropy across 14 LU buckets |
| `lu_health_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.371 (median 0) | Health & medical share |
| `lu_hotel_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.1804 (median 0) | Hotel zone share |
| `lu_institutional_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9115 (median 0.0138) | Civic/community/place-of-worship |
| `lu_mixed_use_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.3615 (median 0.009) | Mixed-use zone share (residential + commercial) |
| `lu_open_space_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9969 (median 0.0483) | Park / open space share |
| `lu_other_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0 (median 0) | Other / unmapped |
| `lu_parcel_count` | int64 | count | 0.0 | 22 → 7026 (median 227.5) | URA parcels intersecting hex |
| `lu_reserve_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9576 (median 0.0127) | Reserve site share |
| `lu_residential_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8106 (median 0.3315) | Land area share zoned residential |
| `lu_total_m2` | float64 | m² | 0.0 | 1.19e+05 → 6.798e+07 (median 1.294e+06) | Total land area covered by URA parcels in hex |
| `lu_transport_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8373 (median 0.1926) | Transport infra share |
| `lu_utility_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.7739 (median 0.0027) | Utility infra share |
| `lu_water_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.7043 (median 0.012) | Water body share |
| `max_gpr` | float64 | ratio | 3.1 | 1 → 25 (median 3.5) | Max GPR within hex |
| `subzone_c` | str | string | 0.0 | 326 unique · `AMSZ01` | URA subzone code |

## `hex/subzone_mobility_features.parquet`

_38 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `bridge_length_m` | float64 | m | 0.0 | 0 → 7.355e+04 (median 2636) | Bridge segment length |
| `bus_stop_count` | float64 | count | 0.0 | 0 → 104 (median 16) | Bus stops in hex |
| `centr_betweenness_max` | float64 | ratio | 0.0 | 0 → 0.108 (median 0.0193) | Max betweenness centrality of major-road nodes |
| `centr_bridge_count` | float64 | count | 0.0 | 0 → 64 (median 5) | Tarjan bridge endpoints (network cut points) |
| `daily_bus_taps` | float64 | taps/day | 0.0 | 0 → 2.076e+05 (median 1.428e+04) | Daily bus taps (Dec 2025 LTA monthly / 31) |
| `daily_train_taps` | float64 | taps/day | 0.0 | 0 → 3.573e+05 (median 0) | Daily MRT/LRT taps (Jan 2026 LTA monthly / 31) |
| `dist_bus_m` | float64 | m | 0.0 | 5.326 → 9542 (median 42.01) | Centroid distance to nearest bus stop |
| `dist_expressway_m` | float64 | m | 0.0 | 0.00143 → 9553 (median 77.23) | Centroid distance to nearest motorway/trunk segment |
| `dist_mrt_m` | float64 | m | 0.0 | 0 → 9633 (median 150.6) | Centroid distance to nearest MRT/LRT station |
| `expressway_in_subzone` | bool |  | 0.0 | 0 → 1 (median 1) |  |
| `expressway_severance` | bool | bool | 0.0 | 0 → 1 (median 0) | Expressway < 200m AND no exit < 400m (barrier without benefit) |
| `has_interchange` | bool |  | 0.0 | 0 → 1 (median 0) |  |
| `has_mrt` | bool |  | 0.0 | 0 → 1 (median 0) |  |
| `hdb_mscp_count` | float64 | count | 0.0 | 0 → 42 (median 2.5) | Authoritative HDB multi-storey carparks |
| `lane_km_per_km2` | float64 | km/km² | 0.0 | 0 → 97.19 (median 54.64) | Lane-km per km² (lane count × length / area) |
| `max_transit_score` | float64 |  | 0.0 | 6.178e-06 → 0.9879 (median 0.8407) |  |
| `mrt_exit_count` | float64 | count | 0.0 | 0 → 33 (median 0) | MRT exits in hex |
| `mrt_station_count` | float64 | count | 0.0 | 0 → 6 (median 0) | MRT/LRT stations in hex |
| `n_hex8` | int64 |  | 0.0 | 1 → 121 (median 2) |  |
| `n_hex8_tr` | int64 |  | 0.0 | 1 → 121 (median 2) |  |
| `n_hex8_wk` | int64 |  | 0.0 | 1 → 121 (median 2) |  |
| `n_interchanges` | int64 |  | 0.0 | 0 → 2 (median 0) |  |
| `parking_lot_count` | float64 | count | 0.0 | 0 → 61 (median 8) | OSM amenity=parking points |
| `ped_path_length_m` | float64 | m | 0.0 | 0 → 3.072e+05 (median 3.666e+04) | Footway + path + cycleway + steps length |
| `rail_line_through_m` | float64 | m | 0.0 | 0 → 2.05e+04 (median 1732) | Rail line length through hex (above + underground) |
| `road_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 264.1 (median 56.98) | Road km per km² |
| `road_intersection_count_total` | int64 |  | 0.0 | 0 → 5204 (median 394.5) |  |
| `road_intersection_density_per_km2` | float64 | count/km² | 0.0 | 0 → 1538 (median 305.1) | Vehicle-network nodes with deg ≥ 3 per km² (Jacobs) |
| `road_length_total_m` | float64 | m | 0.0 | 0 → 1.062e+06 (median 7.348e+04) | Total OSM road length clipped to hex |
| `road_max_class_through` | str | categorical | 0.0 | 8 unique · `motorway` | Highest road class running through hex |
| `road_walkable_share` | float64 | ratio [0,1] | 0.0 | 0 → 0.7701 (median 0.4958) | Pedestrian-only roads as fraction of total |
| `road_walkable_share_wk` | float64 |  | 0.0 | 0 → 0.8394 (median 0.479) |  |
| `signalized_crossing_count` | float64 | count | 0.0 | 0 → 968 (median 143.5) | LTA traffic signals in hex |
| `signalized_crossing_count_wk` | float64 |  | 0.0 | 0 → 968 (median 143.5) |  |
| `subzone_area_km2` | float64 |  | 0.0 | 0.236 → 68.55 (median 1.46) |  |
| `subzone_c` | str | string | 0.0 | 270 unique · `AMSZ02` | URA subzone code |
| `walk_amenities_400m` | int64 | count | 0.0 | 4 → 1.562e+04 (median 1230) | Place count within 400m walk |
| `walkability_score` | float64 | score [0,1] | 0.0 | 0.0001536 → 0.9132 (median 0.6135) | Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |

## `hex/subzone_population.parquet`

_11 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `nonres_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.3111) | Non-resident share of total pop |
| `pop_0_14` | float64 | persons | 0.0 | 0 → 1.543e+04 (median 761) | Population age 0-14 |
| `pop_15_64` | float64 | persons | 0.0 | 0 → 8.31e+04 (median 3572) | Population age 15-64 |
| `pop_65plus` | float64 | persons | 0.0 | 0 → 2.664e+04 (median 1087) | Population age 65+ |
| `pop_hdb` | float64 | persons | 0.0 | 0 → 1.134e+05 (median 2069) | Residents in HDB flats |
| `pop_hdb_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.5671) | HDB share of resident pop |
| `pop_non_hdb` | float64 | persons | 0.0 | 0 → 3.066e+04 (median 1224) | Residents in non-HDB housing |
| `pop_nonresident` | float64 | persons | 0.0 | 0 → 8.901e+04 (median 3539) | Non-residents (FW + EP + MDW) |
| `pop_resident` | float64 | persons | 0.0 | 0 → 1.252e+05 (median 5446) | Resident population (citizens + PRs) |
| `pop_total_all` | float64 | persons | 0.0 | 0 → 1.448e+05 (median 1.175e+04) | Total population (residents + non-residents) |
| `subzone_c` | str | string | 0.0 | 326 unique · `AMSZ01` | URA subzone code |

## `hex/subzone_roads_clean.parquet`

_18 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `bridge_length_m` | float64 | m | 0.0 | 0 → 7.355e+04 (median 2636) | Bridge segment length |
| `centr_betweenness_max` | float64 | ratio | 0.0 | 0 → 0.108 (median 0.0193) | Max betweenness centrality of major-road nodes |
| `centr_bridge_count` | float64 | count | 0.0 | 0 → 64 (median 5) | Tarjan bridge endpoints (network cut points) |
| `dist_expressway_m` | float64 | m | 0.0 | 0.00143 → 9553 (median 77.23) | Centroid distance to nearest motorway/trunk segment |
| `expressway_in_subzone` | bool |  | 0.0 | 0 → 1 (median 1) |  |
| `hdb_mscp_count` | float64 | count | 0.0 | 0 → 42 (median 2.5) | Authoritative HDB multi-storey carparks |
| `lane_km_per_km2` | float64 | km/km² | 0.0 | 0 → 97.19 (median 54.64) | Lane-km per km² (lane count × length / area) |
| `n_hex8` | int64 |  | 0.0 | 1 → 121 (median 2) |  |
| `parking_lot_count` | float64 | count | 0.0 | 0 → 61 (median 8) | OSM amenity=parking points |
| `road_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 264.1 (median 56.98) | Road km per km² |
| `road_intersection_count_total` | int64 |  | 0.0 | 0 → 5204 (median 394.5) |  |
| `road_intersection_density_per_km2` | float64 | count/km² | 0.0 | 0 → 1538 (median 305.1) | Vehicle-network nodes with deg ≥ 3 per km² (Jacobs) |
| `road_length_total_m` | float64 | m | 0.0 | 0 → 1.062e+06 (median 7.348e+04) | Total OSM road length clipped to hex |
| `road_max_class_through` | str | categorical | 0.0 | 8 unique · `motorway` | Highest road class running through hex |
| `road_walkable_share` | float64 | ratio [0,1] | 0.0 | 0 → 0.7701 (median 0.4958) | Pedestrian-only roads as fraction of total |
| `signalized_crossing_count` | float64 | count | 0.0 | 0 → 968 (median 143.5) | LTA traffic signals in hex |
| `subzone_area_km2` | float64 |  | 0.0 | 0.236 → 68.55 (median 1.46) |  |
| `subzone_c` | str | string | 0.0 | 270 unique · `AMSZ02` | URA subzone code |

## `hex/subzone_satellite.parquet`

_9 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `nl_2022` | float64 | nanoWatts/cm²/sr | 0.0 | 0 → 153.6 (median 58.86) | VIIRS night light radiance 2022 (subzone-broadcast) |
| `nl_2024` | float64 | nanoWatts/cm²/sr | 0.0 | 0 → 179.5 (median 63.89) | VIIRS night light radiance 2024 (subzone-broadcast) |
| `nl_change_pct` | float64 | % | 0.0 | -28.01 → 120.4 (median 8.999) | VIIRS 2022→2024 brightness change |
| `nl_commercial_indicator` | float64 | composite | 0.0 | 0 → 165 (median 30.88) | nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) |
| `nl_decline_zone` | bool | bool | 0.0 | 0 → 1 (median 0) | True if night light declined ≥ 20% |
| `nl_growth_corridor` | bool | bool | 0.0 | 0 → 1 (median 0) | True if night light grew ≥ 20% |
| `nl_per_capita` | float64 | radiance/person | 0.0 | 0 → 1.61 (median 0.0463) | nl_2024 / pop_resident (commercial vs residential signal) |
| `subzone_c` | str | string | 0.0 | 326 unique · `AMSZ01` | URA subzone code |
| `wp_pop` | float64 | persons | 0.0 | 0 → 1.618e+05 (median 1.504e+04) | WorldPop count per hex (single snapshot — only one valid TIF available) |

## `hex/subzone_transit_clean.parquet`

_14 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `bus_stop_count` | float64 | count | 0.0 | 0 → 104 (median 16) | Bus stops in hex |
| `daily_bus_taps` | float64 | taps/day | 0.0 | 0 → 2.076e+05 (median 1.428e+04) | Daily bus taps (Dec 2025 LTA monthly / 31) |
| `daily_train_taps` | float64 | taps/day | 0.0 | 0 → 3.573e+05 (median 0) | Daily MRT/LRT taps (Jan 2026 LTA monthly / 31) |
| `dist_bus_m` | float64 | m | 0.0 | 5.326 → 9542 (median 42.01) | Centroid distance to nearest bus stop |
| `dist_mrt_m` | float64 | m | 0.0 | 0 → 9633 (median 150.6) | Centroid distance to nearest MRT/LRT station |
| `has_interchange` | bool |  | 0.0 | 0 → 1 (median 0) |  |
| `has_mrt` | bool |  | 0.0 | 0 → 1 (median 0) |  |
| `max_transit_score` | float64 |  | 0.0 | 6.178e-06 → 0.9879 (median 0.8407) |  |
| `mrt_exit_count` | float64 | count | 0.0 | 0 → 33 (median 0) | MRT exits in hex |
| `mrt_station_count` | float64 | count | 0.0 | 0 → 6 (median 0) | MRT/LRT stations in hex |
| `n_hex8` | int64 |  | 0.0 | 1 → 121 (median 2) |  |
| `n_interchanges` | int64 |  | 0.0 | 0 → 2 (median 0) |  |
| `rail_line_through_m` | float64 | m | 0.0 | 0 → 2.05e+04 (median 1732) | Rail line length through hex (above + underground) |
| `subzone_c` | str | string | 0.0 | 270 unique · `AMSZ02` | URA subzone code |

## `hex/subzone_walkability.parquet`

_8 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `expressway_severance` | bool | bool | 0.0 | 0 → 1 (median 0) | Expressway < 200m AND no exit < 400m (barrier without benefit) |
| `n_hex8` | int64 |  | 0.0 | 1 → 121 (median 2) |  |
| `ped_path_length_m` | float64 | m | 0.0 | 0 → 3.072e+05 (median 3.666e+04) | Footway + path + cycleway + steps length |
| `road_walkable_share` | float64 | ratio [0,1] | 0.0 | 0 → 0.8394 (median 0.479) | Pedestrian-only roads as fraction of total |
| `signalized_crossing_count` | float64 | count | 0.0 | 0 → 968 (median 143.5) | LTA traffic signals in hex |
| `subzone_c` | str | string | 0.0 | 270 unique · `AMSZ02` | URA subzone code |
| `walk_amenities_400m` | int64 | count | 0.0 | 4 → 1.562e+04 (median 1230) | Place count within 400m walk |
| `walkability_score` | float64 | score [0,1] | 0.0 | 0.0001536 → 0.9132 (median 0.6135) | Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |

## `places/sgp_places_final.parquet`

_27 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `brand` | str |  | 0.0 | 251 unique · `` |  |
| `brand_norm` | str | string | 92.1 | 268 unique · `Marina Bay Sands` | Normalized brand name |
| `brand_source` | str | categorical | 92.1 | 2 unique · `scrape` | scrape | name_pattern |
| `has_rating` | bool |  | 0.0 | 0 → 1 (median 1) |  |
| `has_reviews` | bool |  | 0.0 | 0 → 1 (median 1) |  |
| `hdb_town` | str |  | 47.5 | 27 unique · `BUKIT BATOK` |  |
| `hex8_id` | str | string | 0.0 | 911 unique · `886520c95bfffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `hex9_id` | str | string | 0.0 | 4224 unique · `896520c95a7ffff` | H3 resolution-9 cell ID (~0.105 km², 174m edge) |
| `id` | str | string | 0.0 | 190591 unique · `c5Wl6sW53JSX` | Place ID (string hash) |
| `in_sgp` | bool |  | 0.0 | 1 → 1 (median 1) |  |
| `is_long_tail` | bool | bool | 0.0 | 0 → 1 (median 1) | reviews < 5 OR no rating |
| `is_magnet` | bool | bool | 0.0 | 0 → 1 (median 0) | rating ≥ 4 AND reviews ≥ 100 |
| `latitude` | float64 |  | 0.0 | 1.16 → 1.471 (median 1.331) |  |
| `longitude` | float64 |  | 0.0 | 103.6 → 104.1 (median 103.8) |  |
| `magnet_strength` | float64 | ratio | 42.6 | 0.6931 → 55.06 (median 12.67) | rating × log(reviews+1) |
| `name` | str | string | 0.0 | 175228 unique · `Golden Hill Landscape Pte. Ltd.` | Place name |
| `parent_pa` | str | string | 0.0 | 55 unique · `LIM CHU KANG` | URA planning area name (one of 55) |
| `parent_region` | str | string | 0.0 | 5 unique · `NORTH REGION` | URA region (5 regions) |
| `parent_subzone_c` | str |  | 0.0 | 331 unique · `LKSZ01` |  |
| `parent_subzone_name` | str | string | 0.0 | 331 unique · `LIM CHU KANG` | URA subzone full name |
| `parent_subzone_source` | str |  | 0.0 | 90 unique · `contains` |  |
| `plexis_category` | str | categorical | 0.0 | 24 unique · `services` | Resolved 24-category Plexis taxonomy |
| `primary_category` | str | string | 0.0 | 166 unique · `Landscape Design` | Original Google Maps category |
| `rating` | float64 | stars | 42.6 | 1 → 5 (median 4.5) | Google Maps rating (0–5) |
| `review_bucket` | str |  | 0.0 | 5 unique · `1-9` |  |
| `review_quality_pctl_in_cat` | float64 | ratio [0,1] | 42.6 | 0.0006369 → 1 (median 0.4997) | magnet_strength percentile within category |
| `reviews_count` | int64 | count | 0.0 | 0 → 1.109e+05 (median 2) | Google Maps reviews count |
