# Plexis SGP — Feature Catalog (v5.7.1)

*1929 columns across 5 master datasets · 2026-06-21T11:28:59*


## hex8_all_features (846 cols)

| Column | Description | Type | Range/μ or sample |
|---|---|---|---|
| `hex8_id` | H3 resolution-8 cell ID (~0.737 km², 461m edge) | object | e.g. 886520c001fffff |
| `lat` | Hex centroid latitude | float64 | 1.1594–1.4696 (μ 1.3431) |
| `lng` | Hex centroid longitude | float64 | 103.6014–104.0917 (μ 103.8198) |
| `parent_subzone` | URA subzone parent (max-overlap) | object | e.g. TSSZ06 |
| `parent_subzone_name` | URA subzone full name | object | e.g. TUAS VIEW EXTENSION |
| `parent_pa` | URA planning area name (one of 55) | object | e.g. TUAS |
| `parent_region` | URA region (5 regions) | object | e.g. WEST REGION |
| `pop_resident` | Resident population (citizens + PRs) | float64 | 0.0–38134.7828 (μ 3509.4878) |
| `pop_hdb` | Residents in HDB flats | float64 | 0.0–34839.6523 (μ 2663.8885) |
| `pop_non_hdb` | Residents in non-HDB housing | float64 | 0.0–9706.7212 (μ 845.5993) |
| `pop_0_14` | Population age 0-14 | float64 | 0.0–7273.8795 (μ 477.1231) |
| `pop_15_64` | Population age 15-64 | float64 | 0.0–26916.1195 (μ 2372.2365) |
| `pop_65plus` | Population age 65+ | float64 | 0.0–7709.0289 (μ 660.1283) |
| `pop_nonresident` | Non-residents (FW + EP + MDW) | float64 | 0.0–33391.404 (μ 1559.2779) |
| `pop_dorm` | Migrant-worker dormitory population at real MOM dorm locations (439,198 national, DASL H2-2024); subset of non-resident | float64 | 0.0–30951.5094 (μ 368.7641) |
| `pop_total_all` | Total population (residents + non-residents) | float64 | 0.0–42097.9757 (μ 5068.7657) |
| `pop_hdb_share` | HDB share of resident pop | float64 | 0.0–1.0 (μ 0.1793) |
| `nonres_share` | Non-resident share of total pop | float64 | 0.0–1.0 (μ 0.3864) |
| `lu_total_m2` | Total land area covered by URA parcels in hex | float64 | 0.0247–859608.4143 (μ 658860.3825) |
| `lu_parcel_count` | URA parcels intersecting hex | int64 | 1.0–2096.0 (μ 136.9353) |
| `lu_residential_pct` | Land area share zoned residential | float64 | 0.0–0.9368 (μ 0.133) |
| `lu_mixed_use_pct` | Mixed-use zone share (residential + commercial) | float64 | 0.0–0.3002 (μ 0.0078) |
| `lu_commercial_pct` | Land area share zoned commercial | float64 | 0.0–0.4744 (μ 0.0063) |
| `lu_hotel_pct` | Hotel zone share | float64 | 0.0–0.2884 (μ 0.0021) |
| `lu_business_pct` | Land area share zoned business (industrial) | float64 | 0.0–1.0 (μ 0.1689) |
| `lu_business_park_pct` | Business park share | float64 | 0.0–0.523 (μ 0.0033) |
| `lu_educational_pct` | Educational institution share | float64 | 0.0–0.7291 (μ 0.0183) |
| `lu_health_pct` | Health & medical share | float64 | 0.0–0.2255 (μ 0.0023) |
| `lu_institutional_pct` | Civic/community/place-of-worship | float64 | 0.0–1.0 (μ 0.0614) |
| `lu_open_space_pct` | Park / open space share | float64 | 0.0–1.0 (μ 0.2181) |
| `lu_transport_pct` | Transport infra share | float64 | 0.0–1.0 (μ 0.1625) |
| `lu_utility_pct` | Utility infra share | float64 | 0.0–1.0 (μ 0.0231) |
| `lu_water_pct` | Water body share | float64 | 0.0–0.9207 (μ 0.048) |
| `lu_reserve_pct` | Reserve site share | float64 | 0.0–1.0 (μ 0.1448) |
| `lu_other_pct` | Other / unmapped | float64 | 0.0–0.0 (μ 0.0) |
| `avg_gpr` | Area-weighted Gross Plot Ratio | float64 | 0.0–11.0313 (μ 0.9818) |
| `max_gpr` | Max GPR within hex | float64 | 0.0–25.0 (μ 1.5936) |
| `lu_entropy` | Shannon entropy across 14 LU buckets | float64 | -0.0–2.0902 (μ 0.7583) |
| `dominant_use` | Bucket with highest area share | object | e.g. transport |
| `n_children` | Child count used as dasymetric denominator (bookkeeping) | int64 | 1.0–7.0 (μ 6.1444) |
| `bldg_count` | Building footprints in hex (Overture + HDB + OSM) | float64 | 0.0–1968.0 (μ 229.6734) |
| `bldg_footprint_m2` | Total clipped building footprint area in hex | float64 | 0.0–428768.3772 (μ 89541.9105) |
| `bldg_residential_count` | Residential buildings | float64 | 0.0–1084.0 (μ 45.1385) |
| `bldg_commercial_count` | Commercial buildings | float64 | 0.0–191.0 (μ 3.2636) |
| `bldg_industrial_count` | Industrial buildings | float64 | 0.0–165.0 (μ 4.1385) |
| `bldg_institutional_count` | Institutional buildings | float64 | 0.0–45.0 (μ 1.3056) |
| `best_max_floors` | Max floor count (Overture or HDB authoritative) | float64 | 0.0–70.0 (μ 11.0714) |
| `n_highrise_bldgs` | Number of buildings with floors ≥ 10 | float64 | 0.0–979.0 (μ 36.597) |
| `est_total_floor_area_m2` | Sum of footprint × est_floors per building | float64 | 0.0–2716419.7251 (μ 482585.5306) |
| `hdb_block_count` | HDB blocks (authoritative) | float64 | 0.0–147.0 (μ 11.2393) |
| `hdb_dwelling_units` | Total dwelling units across HDB blocks | float64 | 0.0–13186.4183 (μ 979.4828) |
| `hdb_max_floors` | Max HDB floor count | float64 | 0.0–50.0 (μ 8.4374) |
| `hdb_avg_age_years` | Avg years since HDB completion (year_completed filtered ≥1960) | float64 | 0.0–63.75 (μ 10.4574) |
| `bldg_density_per_km2` | Buildings per km² | float64 | 0.0–2670.2849 (μ 311.6328) |
| `bldg_footprint_share` | Footprint as fraction of hex area (clipped, ≤1) | float64 | 0.0–0.5818 (μ 0.1215) |
| `est_built_far` | Estimated built-up FAR = total floor area / hex area | float64 | 0.0–3.6858 (μ 0.6548) |
| `is_highrise` | True if max_floors >= 10 | bool | e.g. False |
| `road_length_total_m` | Total OSM road length clipped to hex | float64 | 0.0–82877.8236 (μ 23851.454) |
| `road_density_km_per_km2` | Road km per km² | float64 | 0.0–112.4529 (μ 32.3629) |
| `road_walkable_share` | Pedestrian-only roads as fraction of total | float64 | 0.0–1.0 (μ 0.287) |
| `road_max_class_through` | Highest road class running through hex | object | e.g. none |
| `road_intersection_count_total` | Road-network metric: road intersection count total | int64 | 0.0–523.0 (μ 123.927) |
| `road_intersection_density_per_km2` | Vehicle-network nodes with deg ≥ 3 per km² (Jacobs) | float64 | 0.0–709.6336 (μ 168.1505) |
| `dist_expressway_m` | Centroid distance to nearest motorway/trunk segment | float64 | 0.0014–13722.8475 (μ 2956.149) |
| `near_expressway_exit_400m` | True if motorway_link/trunk_link < 400m (drive-thru flag) | bool | e.g. False |
| `lane_km_per_km2` | Lane-km per km² (lane count × length / area) | float64 | 0.0–97.1944 (μ 28.132) |
| `oneway_pct` | Fraction of vehicular length that's one-way | float64 | 0.0–1.0 (μ 0.2151) |
| `bridge_length_m` | Bridge segment length | float64 | 0.0–10702.7369 (μ 951.6198) |
| `signalized_crossing_count` | LTA traffic signals in hex | float64 | 0.0–365.0 (μ 37.7137) |
| `parking_lot_count` | OSM amenity=parking points | float64 | 0.0–28.0 (μ 2.6499) |
| `hdb_mscp_count` | Authoritative HDB multi-storey carparks | float64 | 0.0–23.0 (μ 1.0369) |
| `centr_betweenness_max` | Max betweenness centrality of major-road nodes | float64 | 0.0–0.108 (μ 0.0097) |
| `centr_bridge_count` | Tarjan bridge endpoints (network cut points) | float64 | 0.0–64.0 (μ 1.9286) |
| `mrt_station_count` | MRT/LRT stations in hex | float64 | 0.0–5.0 (μ 0.194) |
| `mrt_exit_count` | MRT exits in hex | float64 | 0.0–21.0 (μ 0.4996) |
| `bus_stop_count` | Bus stops in hex | float64 | 0.0–31.0 (μ 4.3426) |
| `dist_mrt_m` | Centroid distance to nearest MRT/LRT station | float64 | 0.0–13725.4975 (μ 3051.9622) |
| `dist_mrt_exit_m` | Centroid distance to nearest MRT exit | float64 | 7.8069–13761.6228 (μ 3124.6448) |
| `dist_bus_m` | Centroid distance to nearest bus stop | float64 | 5.326–13364.995 (μ 1615.3772) |
| `near_mrt_400m` | True if MRT < 400m | bool | e.g. False |
| `near_bus_300m` | True if bus < 300m | bool | e.g. False |
| `rail_line_through_m` | Rail line length through hex (above + underground) | float64 | 0.0–7809.6612 (μ 505.6442) |
| `daily_train_taps` | Daily MRT/LRT taps (Jan 2026 LTA monthly / 31) | float64 | 0.0–247589.1935 (μ 6959.1634) |
| `daily_bus_taps` | Daily bus taps (Dec 2025 LTA monthly / 31) | float64 | 0.0–118676.9032 (μ 5328.1019) |
| `is_mrt_interchange` | True if any station has ≥2 lines (slash-PT_CODE) | bool | e.g. False |
| `transit_score` | 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) | float64 | 0.0–0.9879 (μ 0.3884) |
| `bus_routes_per_stop_max` | Max # routes serving a stop in hex (GTFS) | float64 | 0.0–50.0 (μ 3.8421) |
| `bus_routes_per_stop_mean` | Mean routes/stop in hex | float64 | 0.0–20.3571 (μ 1.2995) |
| `gtfs_headway_am_min` | Best AM-peak headway (lowest minutes between buses) at any stop in hex | float64 | 0.1389–999.0 (μ 539.9272) |
| `ped_path_length_m` | Footway + path + cycleway + steps length | float64 | 0.0–54819.2009 (μ 10737.1306) |
| `ped_path_density_km_per_km2` | Pedestrian-network density | float64 | 0.0–74.5839 (μ 14.8422) |
| `dist_walk_hawker_m` | Walk distance to nearest hawker (Euclidean × 1.3 detour) | float64 | 1.9626–15991.7708 (μ 2526.456) |
| `dist_walk_clinic_m` | Walk distance to nearest clinic | float64 | 1.6728–15994.3655 (μ 2006.0603) |
| `dist_walk_supermarket_m` | Walk distance to nearest supermarket | float64 | 4.8613–17902.7002 (μ 2387.9878) |
| `dist_walk_park_m` | Walk distance to nearest park | float64 | 0.0–20540.5077 (μ 3315.7158) |
| `dist_walk_school_m` | Walk distance to nearest school | float64 | 2.1423–15807.1187 (μ 1711.4229) |
| `dist_walk_food_m` | Walk distance to nearest restaurant/cafe/hawker/bakery/fast-food | float64 | 1.9626–15963.7226 (μ 1570.8805) |
| `walk_amenities_400m` | Place count within 400m walk | int64 | 0.0–11482.0 (μ 400.2435) |
| `walk_food_400m` | Food places within 400m walk | int64 | 0.0–2499.0 (μ 52.0008) |
| `walk_hawker_400m` | Hawkers within 400m walk | int64 | 0.0–630.0 (μ 12.0243) |
| `walk_park_400m` | Parks within 400m walk | int64 | 0.0–30.0 (μ 2.4307) |
| `expressway_severance` | Expressway < 200m AND no exit < 400m (barrier without benefit) | bool | e.g. False |
| `walkability_score` | Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) | float64 | 0.0–0.9217 (μ 0.2891) |
| `nl_2022` | VIIRS night light radiance 2022 (subzone-broadcast) | float64 | 3.0768–153.5743 (μ 43.7695) |
| `nl_2024` | VIIRS night light radiance 2024 (subzone-broadcast) | float64 | 2.6816–161.4246 (μ 46.584) |
| `nl_change_pct` | VIIRS 2022→2024 brightness change | float64 | -28.0109–107.9263 (μ 4.7842) |
| `nl_growth_corridor` | True if night light grew ≥ 20% | bool | e.g. False |
| `nl_decline_zone` | True if night light declined ≥ 20% | bool | e.g. False |
| `nl_per_capita` | nl_2024 / pop_resident (commercial vs residential signal) | float64 | 0.0–0.8876 (μ 0.044) |
| `nl_commercial_indicator` | nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) | float64 | 2.6816–158.5698 (μ 37.7557) |
| `wp_pop` | WorldPop count per hex (single snapshot — only one valid TIF available) | float64 | 0.0–92621.793 (μ 6530.4545) |
| `hdb_resale_in_town` | hdb resale in town (see layer docs) | int64 | 0.0–1.0 (μ 0.2905) |
| `hdb_resale_txns_total` | hdb resale txns total (see layer docs) | float64 | 0.0–18517.0 (μ 2887.1419) |
| `hdb_resale_txns_12m` | hdb resale txns 12m (see layer docs) | float64 | 0.0–1948.0 (μ 326.4727) |
| `hdb_resale_median_price` | hdb resale median price (see layer docs) | float64 | 0.0–760000.0 (μ 147677.7632) |
| `hdb_resale_median_psm` | hdb resale median psm (see layer docs) | float64 | 0.0–7628.866 (μ 1565.6564) |
| `hdb_resale_4r_median_price` | hdb resale 4r median price (see layer docs) | float64 | 0.0–835000.0 (μ 157375.4593) |
| `hdb_resale_4r_median_psm` | hdb resale 4r median psm (see layer docs) | float64 | 0.0–9175.2577 (μ 1658.1313) |
| `hdb_resale_12m_median_price` | hdb resale 12m median price (see layer docs) | float64 | 0.0–980000.0 (μ 186294.0991) |
| `hdb_resale_avg_lease_remaining_yrs` | hdb resale avg lease remaining yrs (see layer docs) | float64 | 0.0–89.8692 (μ 20.7509) |
| `school_count_total` | school count total (see layer docs) | int64 | 0.0–6.0 (μ 0.283) |
| `school_count_primary` | school count primary (see layer docs) | int64 | 0.0–4.0 (μ 0.1528) |
| `school_count_secondary` | school count secondary (see layer docs) | int64 | 0.0–3.0 (μ 0.1117) |
| `school_count_jc` | school count jc (see layer docs) | int64 | 0.0–1.0 (μ 0.0185) |
| `school_count_mixed` | school count mixed (see layer docs) | int64 | 0.0–0.0 (μ 0.0) |
| `school_count_premium` | school count premium (see layer docs) | int64 | 0.0–3.0 (μ 0.0344) |
| `primary_school_zone_count` | Primary-school zones overlapping cell | int64 | 0.0–9.0 (μ 0.3846) |
| `primary_schools_within_1km` | Count of primary schools within 1km | float64 | 0.0–6.71 (μ 0.579) |
| `primary_schools_within_2km` | Count of primary schools within 2km | float64 | 0.0–18.0 (μ 2.3004) |
| `nearest_school_dist_m` | Distance to nearest school | float64 | 4.5–15626.5 (μ 3742.827) |
| `nearest_primary_school_dist_m` | Distance to nearest primary school | float64 | 9.5–16024.4 (μ 3871.7988) |
| `in_primary_school_zone` | Cell intersects a primary-school zone | int64 | 0.0–1.0 (μ 0.1671) |
| `tourist_attraction_count` | tourist attraction count (see layer docs) | int64 | 0.0–16.0 (μ 0.0915) |
| `hawker_centre_count` | hawker centre count (see layer docs) | int64 | 0.0–6.0 (μ 0.1083) |
| `chas_clinic_count` | chas clinic count (see layer docs) | int64 | 0.0–20.0 (μ 1.0008) |
| `chas_clinics_within_500m` | Count of chas clinics within 500m | int64 | 0.0–120.0 (μ 6.5869) |
| `preschool_count` | preschool count (see layer docs) | int64 | 0.0–26.0 (μ 1.9228) |
| `preschools_within_400m` | Count of preschools within 400m | int64 | 0.0–104.0 (μ 8.1318) |
| `silver_zone_count` | silver zone count (see layer docs) | int64 | 0.0–7.0 (μ 0.1528) |
| `nearest_tourist_dist_m` | Distance to nearest tourist | float64 | 12.7–15184.9 (μ 4197.23) |
| `nearest_hawker_centre_dist_m` | Distance to nearest hawker centre | float64 | 17.8–16466.5 (μ 3728.7094) |
| `nearest_chas_clinic_dist_m` | Distance to nearest chas clinic | float64 | 1.4–13789.8 (μ 2641.9226) |
| `nearest_preschool_dist_m` | Distance to nearest preschool | float64 | 1.3–15719.9 (μ 3147.1213) |
| `in_silver_zone` | Cell intersects an elderly-priority Silver Zone | int64 | 0.0–1.0 (μ 0.0672) |
| `ring1_pop_resident` | Sum over H3 ring-1 neighbours (~±1 km) of: Resident population (citizens + PRs) | float64 | 0.0–32318.824 (μ 3526.4109) |
| `ring1_pop_nonresident` | Sum over H3 ring-1 neighbours (~±1 km) of: Non-residents (FW + EP + MDW) | float64 | 0.0–15001.244 (μ 1586.0648) |
| `ring1_pc_total` | Sum over H3 ring-1 neighbours (~±1 km) of: Total mapped places (POIs) in cell — overall point-of-interest density | float64 | 0.0–2340.5 (μ 161.1579) |
| `ring1_pc_magnets` | Sum over H3 ring-1 neighbours (~±1 km) of: High-draw anchor places (malls, hubs, 30+ review demand magnets) | float64 | 0.0–452.5 (μ 18.2148) |
| `ring1_walkability_score` | Sum over H3 ring-1 neighbours (~±1 km) of: Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) | float64 | 0.0–0.864 (μ 0.2918) |
| `ring1_transit_score` | Sum over H3 ring-1 neighbours (~±1 km) of: 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) | float64 | 0.0–0.988 (μ 0.5286) |
| `ring1_nl_2024` | Sum over H3 ring-1 neighbours (~±1 km) of: VIIRS night light radiance 2024 (subzone-broadcast) | float64 | 0.0–158.585 (μ 46.5264) |
| `ring1_hdb_resale_4r_median_psm` | Sum over H3 ring-1 neighbours (~±1 km) of: hdb resale 4r median psm (see layer docs) | float64 | 0.0–8833.333 (μ 1665.7539) |
| `ring1_school_count_total` | Sum over H3 ring-1 neighbours (~±1 km) of: school count total (see layer docs) | float64 | 0.0–16.0 (μ 1.6961) |
| `ring2_pop_resident` | Sum over H3 ring-2 neighbours (~±2 km) of: Resident population (citizens + PRs) | float64 | 0.0–21396.993 (μ 3588.4366) |
| `ring2_pop_nonresident` | Sum over H3 ring-2 neighbours (~±2 km) of: Non-residents (FW + EP + MDW) | float64 | 0.0–9340.831 (μ 1594.0353) |
| `ring2_pc_total` | Sum over H3 ring-2 neighbours (~±2 km) of: Total mapped places (POIs) in cell — overall point-of-interest density | float64 | 0.0–1608.0 (μ 164.2968) |
| `ring2_pc_magnets` | Sum over H3 ring-2 neighbours (~±2 km) of: High-draw anchor places (malls, hubs, 30+ review demand magnets) | float64 | 0.0–291.0 (μ 18.6112) |
| `ring2_walkability_score` | Sum over H3 ring-2 neighbours (~±2 km) of: Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) | float64 | 0.0–0.808 (μ 0.2937) |
| `ring2_transit_score` | Sum over H3 ring-2 neighbours (~±2 km) of: 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) | float64 | 0.0–0.988 (μ 0.6156) |
| `ring2_nl_2024` | Sum over H3 ring-2 neighbours (~±2 km) of: VIIRS night light radiance 2024 (subzone-broadcast) | float64 | 0.0–158.585 (μ 46.51) |
| `ring2_hdb_resale_4r_median_psm` | Sum over H3 ring-2 neighbours (~±2 km) of: hdb resale 4r median psm (see layer docs) | float64 | 0.0–7560.362 (μ 1690.861) |
| `ring2_school_count_total` | Sum over H3 ring-2 neighbours (~±2 km) of: school count total (see layer docs) | float64 | 0.0–20.0 (μ 3.3568) |
| `vibrancy_index` | Composite: places + magnets + reviews + transit + night lights | float64 | 0.0–0.988 (μ 0.1741) |
| `livability_index` | Composite: walkability + green + amenities + transit | float64 | 0.063–0.972 (μ 0.4299) |
| `commercial_intensity` | Supply/morphology composite: commercial place mix + commercial night-light + commercial land-use share | float64 | 0.0–0.998 (μ 0.0913) |
| `family_index` | Composite: children + schools + preschools + family amenities | float64 | 0.0–0.934 (μ 0.2066) |
| `density_pressure` | Composite: population + buildings + low road space | float64 | 0.0–0.778 (μ 0.11) |
| `accessibility_composite` | Composite access score across transit + walk + road reach | float64 | 0.0–0.957 (μ 0.3009) |
| `pull_cbd` | Gravity pull toward cbd (distance-decayed attraction) | float64 | 0.0–0.969 (μ 0.1433) |
| `pull_mall` | Gravity pull toward mall (distance-decayed attraction) | float64 | 0.0–0.952 (μ 0.0935) |
| `pull_hospital` | Gravity pull toward hospital (distance-decayed attraction) | float64 | 0.0–0.979 (μ 0.1442) |
| `pull_mrt_interchange` | Gravity pull toward mrt interchange (distance-decayed attraction) | float64 | 0.0–0.976 (μ 0.1021) |
| `pull_school_premium` | Gravity pull toward school premium (distance-decayed attraction) | float64 | 0.0–0.975 (μ 0.2148) |
| `pull_airport` | Gravity pull toward airport (distance-decayed attraction) | float64 | 0.001–0.998 (μ 0.3171) |
| `pull_composite` | Gravity pull toward composite (distance-decayed attraction) | float64 | 0.001–0.755 (μ 0.1692) |
| `syn_pop_x_walk` | Synergy interaction term: pop x walk (cross-feature product) | float64 | 0.0–0.866 (μ 0.0739) |
| `syn_pop_x_transit` | Synergy interaction term: pop x transit (cross-feature product) | float64 | 0.0–0.959 (μ 0.0829) |
| `syn_office_x_transit` | Synergy interaction term: office x transit (cross-feature product) | float64 | 0.0–0.988 (μ 0.046) |
| `syn_retail_x_anchors` | Synergy interaction term: retail x anchors (cross-feature product) | float64 | 0.0–1.0 (μ 0.0258) |
| `syn_density_x_amenities` | Synergy interaction term: density x amenities (cross-feature product) | float64 | 0.0–1.0 (μ 0.0672) |
| `syn_far_x_transit` | Synergy interaction term: far x transit (cross-feature product) | float64 | 0.0–0.0 (μ 0.0) |
| `syn_residential_x_school` | Synergy interaction term: residential x school (cross-feature product) | float64 | 0.0–1.0 (μ 0.0624) |
| `syn_premium_school_x_4r` | Synergy interaction term: premium school x 4r (cross-feature product) | float64 | 0.0–1.0 (μ 0.0187) |
| `sat_cafe_coffee_per_1k` | Supply saturation: cafe coffee outlets per 1,000 residents | float64 | 0.0–105.481 (μ 1.5194) |
| `gap_cafe_coffee` | Saturation gap for cafe coffee: actual minus expected per-1k supply (positive = oversupplied) | float64 | -1.0–1.0 (μ 0.8429) |
| `sat_restaurant_per_1k` | Supply saturation: restaurant outlets per 1,000 residents | float64 | 0.0–171.954 (μ 3.0514) |
| `gap_restaurant` | Saturation gap for restaurant: actual minus expected per-1k supply (positive = oversupplied) | float64 | -1.0–1.0 (μ 0.8324) |
| `sat_hawker_per_1k` | Supply saturation: hawker outlets per 1,000 residents | float64 | 0.0–75.804 (μ 1.0806) |
| `gap_hawker` | Saturation gap for hawker: actual minus expected per-1k supply (positive = oversupplied) | float64 | -1.0–1.0 (μ 0.8551) |
| `sat_fast_food_per_1k` | Supply saturation: fast food outlets per 1,000 residents | float64 | 0.0–22.39 (μ 0.1969) |
| `gap_fast_food` | Saturation gap for fast food: actual minus expected per-1k supply (positive = oversupplied) | float64 | -1.0–1.0 (μ 0.9046) |
| `sat_supermarket_per_1k` | Supply saturation: supermarket outlets per 1,000 residents | float64 | 0.0–36.185 (μ 0.6024) |
| `gap_supermarket` | Saturation gap for supermarket: actual minus expected per-1k supply (positive = oversupplied) | float64 | -1.0–1.0 (μ 0.8505) |
| `sat_bakery_per_1k` | Supply saturation: bakery outlets per 1,000 residents | float64 | 0.0–38.857 (μ 0.4153) |
| `gap_bakery` | Saturation gap for bakery: actual minus expected per-1k supply (positive = oversupplied) | float64 | -1.0–1.0 (μ 0.8794) |
| `sat_beauty_personal_per_1k` | Supply saturation: beauty personal outlets per 1,000 residents | float64 | 0.0–80.036 (μ 1.1662) |
| `gap_beauty_personal` | Saturation gap for beauty personal: actual minus expected per-1k supply (positive = oversupplied) | float64 | -1.0–1.0 (μ 0.8468) |
| `sat_fitness_recreation_per_1k` | Supply saturation: fitness recreation outlets per 1,000 residents | float64 | 0.0–23.404 (μ 0.6494) |
| `gap_fitness_recreation` | Saturation gap for fitness recreation: actual minus expected per-1k supply (positive = oversupplied) | float64 | -1.0–1.0 (μ 0.7973) |
| `sat_health_medical_per_1k` | Supply saturation: health medical outlets per 1,000 residents | float64 | 0.0–87.65 (μ 1.306) |
| `gap_health_medical` | Saturation gap for health medical: actual minus expected per-1k supply (positive = oversupplied) | float64 | -1.0–1.0 (μ 0.856) |
| `walk_mrt_score` | Walk-access score to nearest mrt (distance-decayed) | float64 | 0.0–1.0 (μ 0.2165) |
| `walk_bus_score` | Walk-access score to nearest bus (distance-decayed) | float64 | 0.0–0.987 (μ 0.4529) |
| `walk_school_score` | Walk-access score to nearest school (distance-decayed) | float64 | 0.0–0.995 (μ 0.3737) |
| `walk_clinic_score` | Walk-access score to nearest clinic (distance-decayed) | float64 | 0.0–0.996 (μ 0.3129) |
| `walk_hawker_score` | Walk-access score to nearest hawker (distance-decayed) | float64 | 0.0–0.995 (μ 0.2873) |
| `walk_supermarket_score` | Walk-access score to nearest supermarket (distance-decayed) | float64 | 0.0–0.988 (μ 0.3092) |
| `walk_park_score` | Walk-access score to nearest park (distance-decayed) | float64 | 0.0–1.0 (μ 0.3468) |
| `walk_food_score` | Walk-access score to nearest food (distance-decayed) | float64 | 0.0–0.995 (μ 0.4213) |
| `walk_convenience_score` | Walk-access score to nearest convenience (distance-decayed) | float64 | 0.0–0.0 (μ 0.0) |
| `walk_score_avg` | Mean of the 9 amenity walk-access scores | float64 | 0.0–0.848 (μ 0.3023) |
| `osm_amenities_count` | OSM amenity-tagged POIs in cell (independent ground truth) | int64 | 0.0–940.0 (μ 24.2527) |
| `osm_leisure_count` | OSM leisure-tagged POIs in cell | int64 | 0.0–147.0 (μ 10.539) |
| `osm_shops_count` | OSM shop-tagged POIs in cell — independent retail frontage | int64 | 0.0–310.0 (μ 7.2771) |
| `osm_tourism_count` | OSM tourism-tagged POIs in cell | int64 | 0.0–183.0 (μ 2.2158) |
| `wc_tree_share` | ESA WorldCover land-cover share: tree share | float64 | 0.0–1.0 (μ 0.2762) |
| `wc_built_share` | ESA WorldCover land-cover share: built share | float64 | 0.0–0.964 (μ 0.3243) |
| `wc_water_share` | ESA WorldCover land-cover share: water share | float64 | 0.0–1.0 (μ 0.2653) |
| `wc_grass_share` | ESA WorldCover land-cover share: grass share | float64 | 0.0–0.73 (μ 0.0879) |
| `wc_other_share` | ESA WorldCover land-cover share: other share | float64 | 0.0–0.747 (μ 0.0463) |
| `wc_dominant_class` | ESA WorldCover land-cover share: dominant class | int64 | 10.0–95.0 (μ 47.1117) |
| `sig_total` | Road-network metric: sig total | int64 | 0.0–365.0 (μ 37.7137) |
| `sig_overhead` | Road-network metric: sig overhead | int64 | 0.0–34.0 (μ 3.9824) |
| `sig_ground` | Road-network metric: sig ground | int64 | 0.0–133.0 (μ 14.1772) |
| `sig_pedestrian` | Road-network metric: sig pedestrian | int64 | 0.0–122.0 (μ 10.8732) |
| `sig_beacon` | Road-network metric: sig beacon | int64 | 0.0–65.0 (μ 4.5458) |
| `sig_rag` | Road-network metric: sig rag | int64 | 0.0–35.0 (μ 1.6961) |
| `sig_filter_arrow` | Road-network metric: sig filter arrow | int64 | 0.0–47.0 (μ 2.2183) |
| `sig_bicycle` | Road-network metric: sig bicycle | int64 | 0.0–4.0 (μ 0.0269) |
| `ped_countdown` | Road-network metric: ped countdown | int64 | 0.0–34.0 (μ 1.3006) |
| `gtfs_headway_midday_min` | GTFS-derived transit service metric: headway midday min (weekday schedule) | float64 | 0.1–999.0 (μ 534.3552) |
| `gtfs_headway_pm_min` | GTFS-derived transit service metric: headway pm min (weekday schedule) | float64 | 0.1–999.0 (μ 534.0495) |
| `gtfs_headway_night_min` | GTFS-derived transit service metric: headway night min (weekday schedule) | float64 | 0.3–999.0 (μ 540.0868) |
| `gtfs_dep_am` | GTFS-derived transit service metric: dep am (weekday schedule) | int64 | 0.0–2567.0 (μ 241.3468) |
| `gtfs_dep_midday` | GTFS-derived transit service metric: dep midday (weekday schedule) | int64 | 0.0–3796.0 (μ 348.4643) |
| `gtfs_dep_pm` | GTFS-derived transit service metric: dep pm (weekday schedule) | int64 | 0.0–2612.0 (μ 237.1931) |
| `gtfs_dep_night` | GTFS-derived transit service metric: dep night (weekday schedule) | int64 | 0.0–3390.0 (μ 251.9966) |
| `gtfs_daily_departures` | GTFS-derived transit service metric: daily departures (weekday schedule) | int64 | 0.0–24161.0 (μ 2123.927) |
| `gtfs_routes_served` | GTFS-derived transit service metric: routes served (weekday schedule) | int64 | 0.0–291.0 (μ 21.8438) |
| `gtfs_stops_with_service` | GTFS-derived transit service metric: stops with service (weekday schedule) | int64 | 0.0–31.0 (μ 4.4509) |
| `bus_taps_in_am` | Daily bus tap-ins in the am time window (LTA PV) | int64 | 0.0–186259.0 (μ 10735.7632) |
| `bus_taps_in_midday` | Daily bus tap-ins in the midday time window (LTA PV) | int64 | 0.0–158171.0 (μ 8919.8992) |
| `bus_taps_in_night` | Daily bus tap-ins in the night time window (LTA PV) | int64 | 0.0–77898.0 (μ 2708.2158) |
| `bus_taps_in_offpeak` | Daily bus tap-ins in the offpeak time window (LTA PV) | int64 | 0.0–600016.0 (μ 28495.0588) |
| `bus_taps_in_pm` | Daily bus tap-ins in the pm time window (LTA PV) | int64 | 0.0–237051.0 (μ 10522.5819) |
| `bus_taps_out_am` | Daily bus tap-outs in the am time window (LTA PV) | int64 | 0.0–222106.0 (μ 11060.1377) |
| `bus_taps_out_midday` | Daily bus tap-outs in the midday time window (LTA PV) | int64 | 0.0–191790.0 (μ 8728.9782) |
| `bus_taps_out_night` | Daily bus tap-outs in the night time window (LTA PV) | int64 | 0.0–57524.0 (μ 3149.3039) |
| `bus_taps_out_offpeak` | Daily bus tap-outs in the offpeak time window (LTA PV) | int64 | 0.0–556302.0 (μ 28534.9236) |
| `bus_taps_out_pm` | Daily bus tap-outs in the pm time window (LTA PV) | int64 | 0.0–185541.0 (μ 10177.9454) |
| `bus_taps_in_total` | Daily bus tap-ins in the total time window (LTA PV) | int64 | 0.0–1249819.0 (μ 61381.5189) |
| `bus_taps_out_total` | Daily bus tap-outs in the total time window (LTA PV) | int64 | 0.0–1183695.0 (μ 61651.2888) |
| `carpark_count_avail` | carpark count avail (see layer docs) | int64 | 0.0–45.0 (μ 2.1763) |
| `carpark_lots_avail` | carpark lots avail (see layer docs) | int64 | 0.0–9318.0 (μ 430.5323) |
| `speed_band_count` | speed band count (see layer docs) | int64 | 0.0–330.0 (μ 47.6784) |
| `speed_band_avg` | speed band avg (see layer docs) | float64 | 0.0–6.7 (μ 1.785) |
| `jam_pct` | jam pct (see layer docs) | float64 | 0.0–62.79 (μ 9.7332) |
| `dyn_avg_speed_kmh` | dyn avg speed kmh (see layer docs) | float64 | 0.0–61.06 (μ 15.2366) |
| `od_out_trips` | LTA origin-destination flow metric: out trips (weekday monthly, bus+train) | float64 | 0.0–2935466.0 (μ 127080.67) |
| `od_out_am` | LTA origin-destination flow metric: out am (weekday monthly, bus+train) | float64 | 0.0–681016.0 (μ 30140.8774) |
| `od_out_pm` | LTA origin-destination flow metric: out pm (weekday monthly, bus+train) | float64 | 0.0–1106017.0 (μ 32842.3115) |
| `od_n_dest_hex` | LTA origin-destination flow metric: n dest hex (weekday monthly, bus+train) | float64 | 0.0–327.0 (μ 47.445) |
| `od_in_trips` | LTA origin-destination flow metric: in trips (weekday monthly, bus+train) | float64 | 0.0–2988755.0 (μ 127000.759) |
| `od_in_am` | LTA origin-destination flow metric: in am (weekday monthly, bus+train) | float64 | 0.0–1241221.0 (μ 30148.3812) |
| `od_in_pm` | LTA origin-destination flow metric: in pm (weekday monthly, bus+train) | float64 | 0.0–839376.0 (μ 32822.6104) |
| `od_self_trips` | LTA origin-destination flow metric: self trips (weekday monthly, bus+train) | float64 | 0.0–149742.0 (μ 5718.2922) |
| `od_dest_entropy` | LTA origin-destination flow metric: dest entropy (weekday monthly, bus+train) | float64 | 0.0–4.6443 (μ 1.2693) |
| `od_throughput` | LTA origin-destination flow metric: throughput (weekday monthly, bus+train) | float64 | 0.0–5924221.0 (μ 254081.4291) |
| `od_net_flow` | LTA origin-destination flow metric: net flow (weekday monthly, bus+train) | float64 | -227885.0–185012.0 (μ -79.911) |
| `od_self_containment` | LTA origin-destination flow metric: self containment (weekday monthly, bus+train) | float64 | 0.0–0.1757 (μ 0.0116) |
| `od_am_pm_out_ratio` | LTA origin-destination flow metric: am pm out ratio (weekday monthly, bus+train) | float64 | -0.9981–0.6117 (μ -0.082) |
| `ca_nl` | Commercial-activity component: nl | float64 | 0.0–1.0 (μ 0.2816) |
| `ca_spend` | Commercial-activity component: spend | float64 | 0.0–1.0 (μ 0.2251) |
| `ca_taps` | Commercial-activity component: taps | float64 | 0.0–1.0 (μ 0.0587) |
| `ca_places` | Commercial-activity component: places | float64 | 0.0–1.0 (μ 0.0624) |
| `ca_footfall` | Commercial-activity component: footfall | float64 | 0.0–1.0 (μ 0.0697) |
| `commercial_activity_index` | Footfall-weighted economic activity: night lights + spend proxy + transit taps + place density + OD throughput (distinct from supply-only commercial_intensity, corr 0.84) | float64 | 0.0–0.9549 (μ 0.1395) |
| `nvp_persona_n` | NVIDIA Nemotron persona distribution: persona n (PA-resolution broadcast) | float64 | 0.0–10399.0 (μ 2187.7893) |
| `nvp_median_age` | NVIDIA Nemotron persona distribution: median age (PA-resolution broadcast) | float64 | 0.0–90.0 (μ 39.1826) |
| `nvp_pct_age_18_34` | NVIDIA Nemotron persona distribution: pct age 18 34 (PA-resolution broadcast) | float64 | 0.0–0.5 (μ 0.2193) |
| `nvp_pct_age_35_54` | NVIDIA Nemotron persona distribution: pct age 35 54 (PA-resolution broadcast) | float64 | 0.0–1.0 (μ 0.2865) |
| `nvp_pct_age_55plus` | NVIDIA Nemotron persona distribution: pct age 55plus (PA-resolution broadcast) | float64 | 0.0–1.0 (μ 0.3255) |
| `nvp_pct_female` | NVIDIA Nemotron persona distribution: pct female (PA-resolution broadcast) | float64 | 0.0–1.0 (μ 0.345) |
| `nvp_pct_married` | NVIDIA Nemotron persona distribution: pct married (PA-resolution broadcast) | float64 | 0.0–1.0 (μ 0.5196) |
| `nvp_pct_single` | NVIDIA Nemotron persona distribution: pct single (PA-resolution broadcast) | float64 | 0.0–0.5 (μ 0.2315) |
| `nvp_pct_univ` | NVIDIA Nemotron persona distribution: pct univ (PA-resolution broadcast) | float64 | 0.0–1.0 (μ 0.2641) |
| `nvp_pct_poly` | NVIDIA Nemotron persona distribution: pct poly (PA-resolution broadcast) | float64 | 0.0–1.0 (μ 0.0831) |
| `nvp_pct_secondary_below` | NVIDIA Nemotron persona distribution: pct secondary below (PA-resolution broadcast) | float64 | 0.0–1.0 (μ 0.3103) |
| `nvp_occ_professional` | NVIDIA Nemotron persona distribution: occ professional (PA-resolution broadcast) | float64 | 0.0–1.0 (μ 0.109) |
| `nvp_occ_manager` | NVIDIA Nemotron persona distribution: occ manager (PA-resolution broadcast) | float64 | 0.0–0.2143 (μ 0.0636) |
| `nvp_occ_assoc_prof` | NVIDIA Nemotron persona distribution: occ assoc prof (PA-resolution broadcast) | float64 | 0.0–0.5 (μ 0.1612) |
| `nvp_occ_service_sales` | NVIDIA Nemotron persona distribution: occ service sales (PA-resolution broadcast) | float64 | 0.0–0.1429 (μ 0.0283) |
| `nvp_occ_clerical` | NVIDIA Nemotron persona distribution: occ clerical (PA-resolution broadcast) | float64 | 0.0–0.0714 (μ 0.0242) |
| `nvp_occ_manual` | NVIDIA Nemotron persona distribution: occ manual (PA-resolution broadcast) | float64 | 0.0–0.5 (μ 0.0847) |
| `nvp_occ_retired` | NVIDIA Nemotron persona distribution: occ retired (PA-resolution broadcast) | float64 | 0.0–1.0 (μ 0.2187) |
| `nvp_occ_student` | NVIDIA Nemotron persona distribution: occ student (PA-resolution broadcast) | float64 | 0.0–0.1429 (μ 0.0163) |
| `nvp_occ_unemployed` | NVIDIA Nemotron persona distribution: occ unemployed (PA-resolution broadcast) | float64 | 0.0–0.1333 (μ 0.0422) |
| `nvp_occ_homemaker` | NVIDIA Nemotron persona distribution: occ homemaker (PA-resolution broadcast) | float64 | 0.0–0.25 (μ 0.0781) |
| `nvp_ind_finance` | NVIDIA Nemotron persona distribution: ind finance (PA-resolution broadcast) | float64 | 0.0–0.2143 (μ 0.0394) |
| `nvp_ind_infocomm` | NVIDIA Nemotron persona distribution: ind infocomm (PA-resolution broadcast) | float64 | 0.0–0.0714 (μ 0.0218) |
| `nvp_ind_manufacturing` | NVIDIA Nemotron persona distribution: ind manufacturing (PA-resolution broadcast) | float64 | 0.0–0.3571 (μ 0.0378) |
| `nvp_ind_retail` | NVIDIA Nemotron persona distribution: ind retail (PA-resolution broadcast) | float64 | 0.0–0.25 (μ 0.0614) |
| `nvp_ind_health` | NVIDIA Nemotron persona distribution: ind health (PA-resolution broadcast) | float64 | 0.0–1.0 (μ 0.0333) |
| `nvp_ind_construction` | NVIDIA Nemotron persona distribution: ind construction (PA-resolution broadcast) | float64 | 0.0–0.5 (μ 0.0687) |
| `nvp_ind_prof_services` | NVIDIA Nemotron persona distribution: ind prof services (PA-resolution broadcast) | float64 | 0.0–0.1053 (μ 0.0347) |
| `nvp_ind_public_edu` | NVIDIA Nemotron persona distribution: ind public edu (PA-resolution broadcast) | float64 | 0.0–0.1429 (μ 0.03) |
| `nvp_ind_food_accom` | NVIDIA Nemotron persona distribution: ind food accom (PA-resolution broadcast) | float64 | 0.0–0.0714 (μ 0.019) |
| `nvp_ind_transport` | NVIDIA Nemotron persona distribution: ind transport (PA-resolution broadcast) | float64 | 0.0–0.25 (μ 0.033) |
| `nvp_affluence_idx` | NVIDIA Nemotron persona distribution: affluence idx (PA-resolution broadcast) | float64 | 0.0–0.6667 (μ 0.166) |
| `nvp_low_n` | NVIDIA Nemotron persona distribution: low n (PA-resolution broadcast) | float64 | 0.0–1.0 (μ 0.3543) |
| `dt_pop` | Commuter daytime headcount: pop_resident − AM transit out + AM in (0.62 PT mode share, /22 weekdays). Clipped ≥0. | float64 | 0.0–87879.28 (μ 3516.6441) |
| `dt_pop_unadj` | Daytime pop, transit-observed only (no mode-share scale-up) | float64 | 0.0–54729.44 (μ 3513.232) |
| `dt_ratio` | dt_pop / pop_resident; NaN where pop<50 & no OD (no-data, NOT 0) | float64 | 0.0–138.76 (μ 4.1892) |
| `dt_inflow_am_persons` | AM-window inbound persons (mode-share adjusted) | float64 | 0.0–90998.61 (μ 2210.2918) |
| `dt_outflow_am_persons` | AM-window outbound persons (mode-share adjusted) | float64 | 0.0–49927.86 (μ 2209.7418) |
| `dt_net_am_persons` | AM net inflow (in − out). THE directional day-night signal; basis of redefined breathing_idx | float64 | -18869.87–87236.44 (μ 0.5501) |
| `dt_clipped` | True if pop+net was clipped at 0 (12 hexes) | bool | e.g. False |
| `dt_class` | job_center (>1.5) / balanced / bedroom (<0.67) / no_data | object | e.g. no_data |
| `iso_walk10_pop` | Population within 800 m NETWORK walk of hex activity centroid (node-field demand, k=4 multi-source Dijkstra) | float64 | 0.0–35340.87 (μ 2577.6237) |
| `iso_walk10_spend` | iso pop × PA affluence index — catchment spending proxy | float64 | 0.0–9745.245 (μ 607.8348) |
| `iso_reached_node_n` | Walk-graph nodes reached within budget (QA) | float64 | 0.0–1018.0 (μ 134.3325) |
| `iso_walk10_unserved_pop_cafe_coffee` | Catchment residents with NO cafe_coffee within 800 m euclid of home — network-precise underserved demand | float64 | 0.0–817.787 (μ 7.8289) |
| `iso_walk10_unserved_pop_supermarket` | Catchment residents with NO supermarket within 800 m euclid of home — network-precise underserved demand | float64 | 0.0–2316.064 (μ 14.1455) |
| `iso_walk10_unserved_pop_restaurant` | Catchment residents with NO restaurant within 800 m euclid of home — network-precise underserved demand | float64 | 0.0–226.661 (μ 1.8803) |
| `iso_walk10_unserved_pop_fitness_recreation` | Catchment residents with NO fitness_recreation within 800 m euclid of home — network-precise underserved demand | float64 | 0.0–395.567 (μ 4.0597) |
| `iso_walk10_places` | Exact place points reached within 800 m network walk | float64 | 0.0–4508.0 (μ 125.2393) |
| `iso_walk10_magnets` | Magnet anchors reached within the walk catchment | float64 | 0.0–953.0 (μ 16.9572) |
| `iso_walk10_competitors_cafe_coffee` | Existing cafe_coffee outlets inside the 800 m walk catchment | float64 | 0.0–217.0 (μ 4.4971) |
| `iso_walk10_competitors_supermarket` | Existing supermarket outlets inside the 800 m walk catchment | float64 | 0.0–44.0 (μ 1.6138) |
| `iso_walk10_competitors_restaurant` | Existing restaurant outlets inside the 800 m walk catchment | float64 | 0.0–513.0 (μ 7.9337) |
| `iso_walk10_competitors_fitness_recreation` | Existing fitness_recreation outlets inside the 800 m walk catchment | float64 | 0.0–95.0 (μ 1.9513) |
| `iso_euclid800_pop` | Euclid-800m baseline pop on the same node field | float64 | 0.0–93957.246 (μ 9376.8777) |
| `iso_severance_ratio` | network pop / euclid pop. Ideal grid ≈0.55 (detour²); low = barriers. NaN where euclid pop < 200 | float64 | 0.0–0.77 (μ 0.2279) |
| `iso_snap_dist_m` | Activity-origin snap distance to walk graph (QA) | float64 | 1.634–10188.825 (μ 842.9274) |
| `iso_transit15_pop` | Population reachable door-to-door in 15 min weekday-AM transit (GTFS route-dir-stop graph + walk arms) | float64 | 0.0–312084.4 (μ 25084.8238) |
| `iso_transit15_places` | Places (hex9 pc_total) within the 15-min transit reach | float64 | 0.0–21915.0 (μ 1156.6826) |
| `iso_transit15_hex9_n` | hex9 cells reached in 15 min | int64 | 1.0–111.0 (μ 26.56) |
| `iso_transit15_stops_used` | Transit stops reachable within 15 min (network-access measure) | int64 | 0.0–272.0 (μ 35.7246) |
| `biz_live_robust` | Live count with per-postal contribution winsorized at 100 — registered-agent buildings (Paya Lebar Sq 19K/postal) damped | float64 | 0.0–10466.0 (μ 286.2645) |
| `biz_per_address` | Live entities per unique postal — high = corporate-secretary building (City Hall 109–131) | float64 | 1.0–746.129 (μ 13.0026) |
| `biz_live_count` | ACRA live ('Registered') entities at building-precise postals (offline OneMap dump, 94.2% coverage) | float64 | 0.0–48598.0 (μ 522.4215) |
| `biz_total_ever` | All entities ever registered (live + dead) | float64 | 0.0–128662.0 (μ 1638.8262) |
| `biz_formation_5y` | Entities issued in the last 5 years (any status) | float64 | 0.0–30740.0 (μ 278.6356) |
| `biz_dead_share` | Deregistered / total ever — LIFETIME mortality (no cessation dates in ACRA). NaN where no entities | float64 | 0.0–1.0 (μ 0.6472) |
| `biz_recent_dead_share` | Dead share among 2018+ cohort (closer to churn). NaN where no 2018+ entities | float64 | 0.0–1.0 (μ 0.3389) |
| `biz_median_age_yrs` | Median age of live entities | float64 | 0.3915–63.1923 (μ 9.9651) |
| `biz_company_share` | 'Local Company' share of live entities (formality mix) | float64 | 0.0–1.0 (μ 0.6598) |
| `biz_density_per_km2` | Live entities per km² | float64 | 0.0–65940.3 (μ 708.8503) |
| `labor_pool_30m` | Working-age pop reaching this hex within 30-min weekday-AM transit | float64 | 0.0–822784.0 (μ 158840.6196) |
| `labor_pool_45m` | Working-age pop within 45-min transit (CBD 1.68M = 59.6% of workforce; Tuas p0) | float64 | 0.0–2116188.0 (μ 494489.9899) |
| `jobs_reach_45m` | Job proxy (office+industrial+services places, scaled 2.4M) within 45 min | float64 | 0.0–1799458.0 (μ 439567.2149) |
| `labor_accessibility_pct` | labor_pool_45m / national working-age pop | float64 | 0.0–0.749 (μ 0.175) |
| `labor_jobs_balance_45m` | jobs_reach / labor_pool — divergence flags job-rich/transit-poor (Jurong Island, Tuas) | float64 | 0.0–85037.0 (μ 1082.8153) |
| `vis_exit_footfall` | Weekday taps at nearest MRT/LRT exit ≤400 m, split per exit from per-station PV. Few-exit busy stations beat 13-exit Orchard | float64 | 0.0–40845.39 (μ 1447.9206) |
| `vis_exit_station` | Name of that nearest station | object | e.g. KRANJI MRT STATION |
| `vis_dist_exit_origin_m` | Activity origin → nearest exit distance | float64 | 9.6–14036.8 (μ 3387.2736) |
| `vis_main_road_m` | LTA speed-band cat A/B segment length in hex | float64 | 0.0–8095.03 (μ 519.0422) |
| `vis_traffic_pass_proxy` | Σ road-category weights over speed-band segments — drive-past exposure | float64 | 0.0–839.5 (μ 35.8325) |
| `vis_corner_premium` | Signalized crossings × main-road presence | float64 | 0.0–323.0 (μ 18.6037) |
| `pipe_new_mrt_within_800m` | Future rail station (MP2019 minus existing Mar-2026; 37 stations: full JRL + Keppel CCL6) within 800 m | bool | e.g. False |
| `pipe_mrt_name` | Nearest future station name | object | e.g. JURONG PIER |
| `pipe_mrt_dist_m` | Distance to nearest future rail station | float64 | 11.4–15354.9 (μ 4854.4106) |
| `pipe_dev_capacity_res` | FAR headroom (avg_gpr − est_built_far)⁺ × residential zoning share. Matilda 0.50 / Bidadari 0.34 / built-out Toa Payoh Ctrl 0 | float64 | 0.0–1.793 (μ 0.0672) |
| `pipe_dev_capacity_com` | FAR headroom × (commercial + mixed) zoning share | float64 | 0.0–1.7807 (μ 0.0153) |
| `cons_bldg_count` | URA conserved buildings in hex (MP2019 SDCP layer, 7,235 islandwide) — shophouse/heritage density | float64 | 0.0–1351.0 (μ 6.0747) |
| `cons_cluster_flag` | >=20 conserved buildings — heritage shophouse cluster (Chinatown, Little India, Jalan Besar belt) | bool | e.g. False |
| `carpark_count_hdb` | HDB carparks in hex (HDB Carpark Information) | float64 | 0.0–26.0 (μ 1.9026) |
| `carpark_capacity_lots` | Summed car-lot CAPACITY (live availability total_lots, lot type C; 696K national) | float64 | 0.0–13668.0 (μ 584.4551) |
| `polyclinic_count` | Public polyclinics in hex (27 islandwide) | float64 | 0.0–1.0 (μ 0.0227) |
| `dist_polyclinic_m` | Centroid distance to nearest polyclinic — public primary-care competition signal | float64 | 103.9–16680.5 (μ 5081.0458) |
| `wet_market_count` | NEA market & food centres flagged as wet markets (63 of 129) | float64 | 0.0–5.0 (μ 0.0529) |
| `dist_wet_market_m` | Distance to nearest wet market — morning-circuit / grocery-substitution signal | float64 | 37.6–17938.3 (μ 5740.7148) |
| `petrol_station_count` | Fuel stations in hex (OSM, 201 islandwide) | float64 | 0.0–4.0 (μ 0.1688) |
| `dist_petrol_m` | Distance to nearest petrol station | float64 | 2.5–14067.0 (μ 3268.7606) |
| `coworking_count` | Coworking venues (places name-match, 171 islandwide; 40% CBD-core) | float64 | 0.0–20.0 (μ 0.1436) |
| `condo_project_count` | Private strata projects with transactions in hex (URA, 2,384) | float64 | 0.0–87.0 (μ 2.0017) |
| `condo_txn_units` | Units TRANSACTED across those projects — private-housing density weight, NOT stock | float64 | 0.0–1624.0 (μ 84.0092) |
| `female_pop_share` | Female share of resident pop (SingStat 2025, subzone-broadcast). NaN = zero-population subzone; tiny subzones can skew genuinely | float64 | 0.2381–0.6471 (μ 0.5163) |
| `bto_uc_units_town` | FY2024 HDB units under construction in the hex's town (town-broadcast; Kallang/Whampoa 11.5K, Tengah 11.1K top) | float64 | 0.0–11480.0 (μ 1397.4761) |
| `bto_pipeline_est` | Town under-construction units allocated within town by FAR headroom share — MODELED estate-growth estimate | float64 | 0.0–3430.6 (μ 77.1964) |
| `time_to_cbd_min` | Door-to-door transit travel time to CBD (Raffles Place) (mobility-v2 reach model) | float64 | 6.5774–66.2925 (μ 38.3047) |
| `time_to_orchard_min` | Door-to-door transit travel time to Orchard (mobility-v2 reach model) | float64 | 5.9956–75.2925 (μ 39.1269) |
| `time_to_jurong_east_min` | Door-to-door transit travel time to Jurong East (mobility-v2 reach model) | float64 | 5.4398–78.5362 (μ 39.8833) |
| `time_to_one_north_min` | Door-to-door transit travel time to one-north (mobility-v2 reach model) | float64 | 5.1784–75.0362 (μ 39.3867) |
| `time_to_changi_business_min` | Door-to-door transit travel time to Changi Business Park (mobility-v2 reach model) | float64 | 4.7856–97.7925 (μ 56.3371) |
| `time_to_tampines_hub_min` | Door-to-door transit travel time to Tampines Hub (mobility-v2 reach model) | float64 | 4.5879–96.2925 (μ 53.7239) |
| `time_to_nus_min` | Door-to-door transit travel time to NUS (mobility-v2 reach model) | float64 | 7.2097–77.5362 (μ 41.3105) |
| `time_to_ntu_min` | Door-to-door transit travel time to NTU (mobility-v2 reach model) | float64 | 5.4642–88.5362 (μ 48.8244) |
| `time_to_sgh_min` | Door-to-door transit travel time to SGH (mobility-v2 reach model) | float64 | 6.1969–61.2925 (μ 37.1766) |
| `time_to_cgh_min` | Door-to-door transit travel time to CGH (mobility-v2 reach model) | float64 | 4.7856–97.7925 (μ 56.3371) |
| `time_to_kkh_min` | Door-to-door transit travel time to KKH (mobility-v2 reach model) | float64 | 4.1235–71.7925 (μ 37.0796) |
| `time_to_ttsh_min` | Door-to-door transit travel time to TTSH (mobility-v2 reach model) | float64 | 2.4494–75.7925 (μ 40.1385) |
| `n_dest_reachable` | Key destinations reachable by transit (mobility-v2) | int64 | 0.0–17.0 (μ 6.1805) |
| `n_dest_within_45min` | Key destinations within 45-min transit | int64 | 0.0–17.0 (μ 3.2267) |
| `pct_dest_within_45min` | Share of key destinations within 45 min | float64 | 0.0–100.0 (μ 18.9806) |
| `pct_dest_within_60min` | Share of key destinations within 60 min | float64 | 0.0–100.0 (μ 29.8118) |
| `n_lines_to_cbd` | Distinct rail lines connecting toward the CBD | int64 | 0.0–5.0 (μ 0.3728) |
| `n_stations_walking` | Stations within walking reach | int64 | 0.0–9.0 (μ 0.4744) |
| `mrt_reach_bus_min` | Feeder-bus leg of MRT reach | float64 | 4.6–40.7 (μ 13.3917) |
| `mrt_reach_bus_wait_min` | Feeder wait of MRT reach | float64 | 0.1–15.0 (μ 1.7159) |
| `mrt_reach_crowd` | Crowding multiplier on the reach path | float64 | 0.0–0.9931 (μ 0.4585) |
| `mrt_reach_index` | Composite MRT reach quality | float64 | 0.0–1.0 (μ 0.4349) |
| `mrt_reach_n_feeders` | Feeder bus services to nearest MRT | int64 | 0.0–36.0 (μ 2.2788) |
| `mrt_reach_mode` | Reach mode: walk / feeder / poor | object | e.g. walk |
| `peak_wait_min` | Expected peak-hour wait (best mode) | float64 | 1.275–12.5 (μ 3.9835) |
| `peak_wait_bus_only_min` | Peak wait, bus only | float64 | 1.5–30.0 (μ 7.1524) |
| `peak_wait_mrt_only_min` | Peak wait, MRT only | float64 | 2.5–5.0 (μ 2.7203) |
| `crowding_load_factor` | Peak load factor on serving lines | float64 | 0.0–0.9931 (μ 0.1924) |
| `min15_score` | 15-minute-city score (calibrated: Toa Payoh 100 / Lim Chu Kang 13) | float64 | 0.0–100.0 (μ 45.2491) |
| `min15_essentials` | 15-min subscore: daily essentials | float64 | 0.0–100.0 (μ 39.5052) |
| `min15_health` | 15-min subscore: health | float64 | 0.0–100.0 (μ 43.3263) |
| `min15_retail` | 15-min subscore: retail | float64 | 0.0–100.0 (μ 63.8736) |
| `min15_school` | 15-min subscore: schools | float64 | 0.0–100.0 (μ 40.0347) |
| `min15_count_essentials` | Essential amenities within 15 min | int64 | 0.0–283.0 (μ 25.916) |
| `min15_count_health` | Health amenities within 15 min | int64 | 0.0–814.0 (μ 28.2872) |
| `min15_count_retail` | Retail within 15 min | int64 | 0.0–6070.0 (μ 222.0596) |
| `min15_count_school` | Schools within 15 min | int64 | 0.0–651.0 (μ 40.4475) |
| `min15_nearest_super_m` | Nearest supermarket | float64 | 6.0–14368.0 (μ 2687.2024) |
| `pop_nr_ep` | Employment-pass holders | float64 | 0.0–17487.6503 (μ 380.3526) |
| `pop_nr_fdw` | Foreign domestic workers | float64 | 0.0–4191.834 (μ 266.0789) |
| `pop_nr_sp` | S-pass holders | float64 | 0.0–7114.944 (μ 171.2846) |
| `pop_nr_wp_other` | Other work-permit holders (non-dorm) | float64 | 0.0–9061.5435 (μ 380.7725) |
| `walking_dependent_count` | Walking-dependent residents (no car/PT-captive) | float64 | 0.0–12449.7897 (μ 1146.1797) |
| `vulnerability_share` | Vulnerable-population share (adequacy v3 multiplier input) | float64 | 0.0–0.55 (μ 0.1261) |
| `vulnerability_penalty` | Adequacy penalty from vulnerability double-threshold | float64 | 0.0–0.0 (μ 0.0) |
| `access_vuln_share` | Access-vulnerable share | float64 | 0.0–1.0 (μ 0.0979) |
| `access_vuln_penalty` | Access-vulnerability penalty | float64 | 0.0–0.25 (μ 0.0097) |
| `crowd_sensitive_share` | Crowding-sensitive share | float64 | 0.0–0.55 (μ 0.1029) |
| `crowd_equity_penalty` | Crowding equity penalty | float64 | 0.0–0.2338 (μ 0.0293) |
| `ped_greenman_count` | Green Man+ (extended-time) crossings | int64 | 0.0–12.0 (μ 0.2141) |
| `lrt_stations` | LRT stations in hex | float64 | 0.0–3.0 (μ 0.0369) |
| `lrt_stations_in_500m` | LRT stations within 500 m | int64 | 0.0–3.0 (μ 0.0344) |
| `dist_to_nearest_lrt_m` | Distance to nearest LRT station | float64 | 65.0814–24209.5415 (μ 9378.0039) |
| `bus_stops_in_400m` | Bus stops within 400 m of centroid | int64 | 0.0–18.0 (μ 2.5995) |
| `bus_stops_in_800m` | Bus stops within 800 m | int64 | 0.0–59.0 (μ 10.3778) |
| `mrt_stations_in_500m` | MRT stations within 500 m | int64 | 0.0–5.0 (μ 0.1453) |
| `mrt_stations_in_1km` | MRT stations within 1 km | int64 | 0.0–12.0 (μ 0.5869) |
| `nearest_mrt_st_peak_taps` | Peak taps at the nearest MRT station | float64 | 0.0–386243.0 (μ 112671.3484) |
| `last_mile_friction` | Last-mile friction composite | float64 | 0.1719–1.0 (μ 0.7747) |
| `multimodal_score` | Multi-modal option richness | float64 | 0.0–0.7522 (μ 0.1685) |
| `transit_mode_count` | Distinct transit modes serving hex | int64 | 0.0–3.0 (μ 0.6071) |
| `industrial_adjacency_score` | Adjacency to industrial estates (guard signal) | float64 | 0.0–1.0 (μ 0.2649) |
| `zone_type` | URA zone type of the hex (PA→SZ→hex8 propagated) | object | e.g. unknown |
| `zone_type_broad` | Broad zone class (residential/industrial/airport/nature/islands/future) — the NA-masking rule | object | e.g. unknown |
| `adq_default` | Transport adequacy v3 (default profile, 0-100) | float64 | 0.0677–1.0 (μ 0.5998) |
| `adq_core` | Adequacy core (pre-vulnerability) | float64 | 0.1839–1.0 (μ 0.6352) |
| `adq_v2` | Adequacy v2 (availability-floored legacy) | float64 | 0.0677–1.0 (μ 0.6077) |
| `adq_default_elderly` | Adequacy, elderly profile | float64 | 0.0677–1.0 (μ 0.6368) |
| `adq_default_family` | Adequacy, family profile | float64 | 0.0606–1.0 (μ 0.6267) |
| `adq_default_workers` | Adequacy, workers profile | float64 | 0.0606–1.0 (μ 0.5641) |
| `adq_core_elderly` | Adequacy core, elderly | float64 | 0.1634–1.0 (μ 0.5983) |
| `adq_core_family` | Adequacy core, family | float64 | 0.1967–1.0 (μ 0.64) |
| `adq_core_workers` | Adequacy core, workers | float64 | 0.1938–1.0 (μ 0.6723) |
| `adq_gap_default` | Adequacy gap (default profile) | float64 | 0.1409–0.965 (μ 0.5293) |
| `adq_gap_core` | Adequacy gap (core) | float64 | 0.1614–0.95 (μ 0.5852) |
| `adq_gap_equity_max` | Worst per-profile equity gap | float64 | 0.0–1.0 (μ 0.3989) |
| `adq_availability_v2` | Transit availability composite | float64 | 0.0606–1.0 (μ 0.5271) |
| `adq_worst_factor_value` | Score of the worst adequacy factor | float64 | 0.1084–1.0 (μ 0.7221) |
| `adq_worst_factor` | Name of the worst adequacy factor | object | e.g. f_accessibility |
| `adq_primary_factor` | Primary driving factor (default profile) | object | e.g. reach |
| `adq_primary_gap_reason` | Primary gap explanation tag | object | e.g. walk_unfriendly |
| `adq_f_accessibility` | Adequacy v3 factor score: composite access (mobility-v2 model) | float64 | 0.2829–1.0 (μ 0.667) |
| `adq_f_connectivity` | Adequacy v3 factor score: network connectivity (mobility-v2 model) | float64 | 0.0–1.0 (μ 0.6482) |
| `adq_f_distance` | Adequacy v3 factor score: distance to transit (mobility-v2 model) | float64 | 0.0047–1.0 (μ 0.4445) |
| `adq_f_last_mile` | Adequacy v3 factor score: last-mile friction (mobility-v2 model) | float64 | 0.1719–1.0 (μ 0.691) |
| `adq_f_line_pressure` | Adequacy v3 factor score: line crowding pressure (mobility-v2 model) | float64 | 0.0–1.0 (μ 0.0408) |
| `adq_f_low_frequency` | Adequacy v3 factor score: service frequency shortfall (mobility-v2 model) | float64 | 0.0–1.0 (μ 0.5524) |
| `adq_f_reach_gap` | Adequacy v3 factor score: destination reach shortfall (mobility-v2 model) | float64 | 0.0–1.0 (μ 0.4212) |
| `adq_f_children_gap` | Adequacy v3 factor score: child-population service gap (mobility-v2 model) | float64 | 0.0–0.9322 (μ 0.2342) |
| `adq_f_elderly_gap` | Adequacy v3 factor score: elderly service gap (mobility-v2 model) | float64 | 0.0–1.0 (μ 0.1501) |
| `adq_f_dorm_gap` | Adequacy v3 factor score: dorm-worker service gap (mobility-v2 model) | float64 | 0.0–1.0 (μ 0.0294) |
| `adq_f_fdw_gap` | Adequacy v3 factor score: FDW service gap (mobility-v2 model) | float64 | 0.0–0.7624 (μ 0.0596) |
| `adq_f_low_income_gap` | Adequacy v3 factor score: low-income service gap (mobility-v2 model) | float64 | 0.0–0.5804 (μ 0.2521) |
| `linkway_len_m` | Covered-linkway length in hex (7,012-segment LTA layer) — sheltered-walk density | float64 | 0.0–4704.6 (μ 205.9605) |
| `cycling_path_len_m` | Cycling-path length in hex | float64 | 0.0–10475.2 (μ 752.7751) |
| `linkway_per_road_km` | Covered-linkway metres per road km — shelter coverage ratio | float64 | 0.0–65.59 (μ 4.682) |
| `pr_share` | PR share of resident population (citizen/PR ratio signal; levels deduped away) | float64 | 0.1286–0.1286 (μ 0.1286) |
| `low_income_share` | Low-income share of residents (level deduped vs pop_hdb; share is the signal) | float64 | 0.0–0.2998 (μ 0.1379) |
| `retail_whitespace_score` | Retail white-space — unmet, winnable demand for a new store (0–100) | int64 | 0.0–100.0 (μ 17.8682) |
| `retail_competition_pressure` | Competition pressure from existing same-format retail (0–100) | int64 | 0.0–100.0 (μ 8.8573) |
| `format_fit_score` | Best-fit store format (kiosk→flagship) suitability (0–100) | int64 | 0.0–100.0 (μ 5.3308) |
| `retail_cannibalization_score` | Self-cannibalisation risk vs own-brand nearby outlets (0–100) | int64 | 0.0–100.0 (μ 6.6902) |
| `retail_delivery_score` | Dark-store / delivery viability (0–100) | int64 | 0.0–100.0 (μ 5.5063) |
| `retail_footfall_score` | Footfall / visit potential (0–100) | int64 | 0.0–100.0 (μ 10.2712) |
| `rent_demand_tier` | Demand-vs-rent tier (residential-rent proxy) | int64 | 0.0–100.0 (μ 59.534) |
| `re_feasibility_score` | Development feasibility — FAR headroom × buildability (0–100) | int64 | 0.0–100.0 (μ 10.7154) |
| `re_livability_score` | Neighbourhood livability / quality (0–100) | int64 | 0.0–100.0 (μ 34.6767) |
| `re_momentum_score` | Momentum / gentrification signal (0–100) | int64 | 0.0–100.0 (μ 16.1931) |
| `re_enbloc_score` | En-bloc redevelopment upside (0–100) | int64 | 0.0–100.0 (μ 6.9782) |
| `re_collateral_score` | Mortgage collateral tier (0–100) | int64 | 0.0–100.0 (μ 29.9051) |
| `re_yield_proxy` | Rental-yield proxy (0–100) | float64 | 0.0–8.174 (μ 1.0847) |
| `re_lease_decay_penalty` | HDB lease-decay penalty (0–100) | int64 | 0.0–100.0 (μ 76.9211) |
| `utility_load_score` | Relative electricity load (0–100) | int64 | 0.0–100.0 (μ 16.6096) |
| `utility_load_growth_score` | Projected load growth (0–100) | int64 | 0.0–100.0 (μ 13.1763) |
| `utility_water_score` | Water-demand estimate (0–100) | int64 | 0.0–100.0 (μ 11.0999) |
| `utility_waste_score` | Waste-generation estimate (0–100; ∝ population) | int64 | 0.0–100.0 (μ 10.5987) |
| `utility_ev_gap_score` | EV-charger provision gap (0–100) | int64 | 0.0–100.0 (μ 6.644) |
| `utility_diurnal_swing` | Day/night load swing (0–100) | int64 | -100.0–500.0 (μ 64.0319) |
| `utility_equity_score` | Infrastructure-equity priority (0–100) | int64 | 0.0–100.0 (μ 4.9547) |
| `utility_resilience_score` | Critical-customer resilience need (0–100) | int64 | 0.0–100.0 (μ 27.3619) |
| `mobility_access_score` | Transit / multimodal access (0–100; ≈ adequacy) | int64 | 0.0–100.0 (μ 34.2502) |
| `mobility_desert_priority` | Transit-desert intervention priority (0–100) | int64 | 0.0–100.0 (μ 6.2435) |
| `mobility_crowding_score` | Network crowding stress (0–100) | int64 | 0.0–100.0 (μ 5.2452) |
| `mobility_tod_score` | Transit-oriented-development opportunity (0–100) | int64 | 0.0–100.0 (μ 3.2259) |
| `mobility_ridehail_score` | Ride-hail demand hotspot (0–100) | int64 | 0.0–100.0 (μ 1.8304) |
| `mobility_firstlast_gap_score` | First / last-mile gap (0–100) | int64 | 0.0–100.0 (μ 3.1159) |
| `mobility_parking_stress` | Parking stress (0–100) | int64 | 0.0–100.0 (μ 8.796) |
| `modal_split_proxy` | Public-transport modal-split proxy (0–100) | int64 | 0.0–100.0 (μ 10.0697) |
| `risk_fire_score` | Property / fire peril (0–100) | int64 | 0.0–100.0 (μ 4.7767) |
| `risk_auto_score` | Motor / auto exposure (0–100) | int64 | 0.0–100.0 (μ 5.1192) |
| `risk_health_score` | Life / health exposure (0–100) | int64 | 0.0–100.0 (μ 4.7179) |
| `risk_bi_failure_score` | Business-interruption risk (≈ biz_recent_dead_share) | int64 | 0.0–100.0 (μ 22.461) |
| `risk_collateral_score` | Collateral-value risk tier (0–100) | int64 | 0.0–100.0 (μ 14.7212) |
| `risk_nuisance_score` | Nuisance / liability peril (0–100) | int64 | 0.0–100.0 (μ 21.7506) |
| `risk_coastal_proxy` | Coastal / flood proxy (weak; 0–100) | int64 | 0.0–100.0 (μ 7.3132) |
| `insurance_risk_score` | Blended underwriting risk score (0–100) | int64 | 0.0–100.0 (μ 21.916) |
| `insurance_accumulation_band` | Accumulation / concentration band | int64 | 0.0–100.0 (μ 9.8883) |
| `pw1_pc_total` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Total mapped places (POIs) in cell — overall point-of-interest density | float64 | 0.0–3861.822 (μ 203.899) |
| `pw1_pc_magnets` | Proximity-weighted (distance-decayed) ring-1 aggregate of: High-draw anchor places (malls, hubs, 30+ review demand magnets) | float64 | 0.0–739.356 (μ 22.8375) |
| `pw1_pc_unique_brands` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Distinct retail/F&B brands present — chain richness | float64 | 0.0–74.353 (μ 12.1134) |
| `pw1_pc_cat_business_office` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: business office category (24-cat taxonomy) | float64 | 0.0–619.164 (μ 18.0242) |
| `pw1_pc_cat_shopping_retail` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: shopping retail category (24-cat taxonomy) | float64 | 0.0–291.577 (μ 15.3301) |
| `pw1_pc_cat_hawker` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: hawker category (24-cat taxonomy) | float64 | 0.0–172.63 (μ 7.6691) |
| `pw1_pc_cat_residential` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: residential category (24-cat taxonomy) | float64 | 0.0–130.259 (μ 22.1605) |
| `pw1_pc_cat_industrial_mfg` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: industrial mfg category (24-cat taxonomy) | float64 | 0.0–254.978 (μ 13.8847) |
| `pw1_pc_cat_cafe_coffee` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: cafe coffee category (24-cat taxonomy) | float64 | 0.0–170.74 (μ 7.6655) |
| `pw1_pc_cat_restaurant` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: restaurant category (24-cat taxonomy) | float64 | 0.0–458.361 (μ 12.5064) |
| `pw1_pc_cat_education` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: education category (24-cat taxonomy) | float64 | 0.0–118.759 (μ 13.4401) |
| `pw1_pc_cat_health_medical` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: health medical category (24-cat taxonomy) | float64 | 0.0–172.292 (μ 8.3831) |
| `pw1_transit_score` | Proximity-weighted (distance-decayed) ring-1 aggregate of: 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) | float64 | 0.0–0.976 (μ 0.3945) |
| `pw1_walkability_score` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) | float64 | 0.0–0.892 (μ 0.3221) |
| `pw1_nl_2024` | Proximity-weighted (distance-decayed) ring-1 aggregate of: VIIRS night light radiance 2024 (subzone-broadcast) | float64 | 0.0–158.585 (μ 33.1417) |
| `pw1_nl_commercial_indicator` | Proximity-weighted (distance-decayed) ring-1 aggregate of: nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) | float64 | 0.0–158.49 (μ 19.3836) |
| `pw1_hdb_resale_4r_median_psm` | Proximity-weighted (distance-decayed) ring-1 aggregate of: hdb resale 4r median psm (see layer docs) | float64 | 0.0–8850.716 (μ 2261.2209) |
| `pw1_primary_schools_within_1km` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Count of primary schools within 1km | float64 | 0.0–5.408 (μ 0.8543) |
| `pw1_preschools_within_400m` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Count of preschools within 400m | float64 | 0.0–70.56 (μ 12.8485) |
| `pw1_chas_clinic_count` | Proximity-weighted (distance-decayed) ring-1 aggregate of: chas clinic count (see layer docs) | float64 | 0.0–14.277 (μ 1.6177) |
| `pw1_hawker_centre_count` | Proximity-weighted (distance-decayed) ring-1 aggregate of: hawker centre count (see layer docs) | float64 | 0.0–4.125 (μ 0.1829) |
| `pw1_tourist_attraction_count` | Proximity-weighted (distance-decayed) ring-1 aggregate of: tourist attraction count (see layer docs) | float64 | 0.0–9.488 (μ 0.0863) |
| `pw1_vibrancy_index` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Composite: places + magnets + reviews + transit + night lights | float64 | 0.0–0.891 (μ 0.1698) |
| `pw1_commercial_intensity` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Supply/morphology composite: commercial place mix + commercial night-light + commercial land-use share | float64 | 0.0–0.839 (μ 0.0854) |
| `pw1_family_index` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Composite: children + schools + preschools + family amenities | float64 | 0.0–0.876 (μ 0.2525) |
| `pw1_density_pressure` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Composite: population + buildings + low road space | float64 | 0.0–0.767 (μ 0.1476) |
| `pw1_pull_cbd` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Gravity pull toward cbd (distance-decayed attraction) | float64 | 0.0–0.942 (μ 0.126) |
| `pw1_pull_mall` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Gravity pull toward mall (distance-decayed attraction) | float64 | 0.0–0.901 (μ 0.0917) |
| `pw1_pull_mrt_interchange` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Gravity pull toward mrt interchange (distance-decayed attraction) | float64 | 0.0–0.903 (μ 0.1021) |
| `pw1_wc_built_share` | Proximity-weighted (distance-decayed) ring-1 aggregate of: ESA WorldCover land-cover share: built share | float64 | 0.0–0.909 (μ 0.3135) |
| `pw1_wc_tree_share` | Proximity-weighted (distance-decayed) ring-1 aggregate of: ESA WorldCover land-cover share: tree share | float64 | 0.0–1.0 (μ 0.2005) |
| `max1_pc_total` | Max over ring-1 neighbours of: Total mapped places (POIs) in cell — overall point-of-interest density | float64 | 0.0–4929.0 (μ 366.1721) |
| `max1_pc_magnets` | Max over ring-1 neighbours of: High-draw anchor places (malls, hubs, 30+ review demand magnets) | float64 | 0.0–980.0 (μ 52.9916) |
| `max1_pc_unique_brands` | Max over ring-1 neighbours of: Distinct retail/F&B brands present — chain richness | float64 | 0.0–126.0 (μ 22.2813) |
| `max1_pc_cat_business_office` | Max over ring-1 neighbours of: Place count in cell: business office category (24-cat taxonomy) | float64 | 0.0–755.0 (μ 52.3988) |
| `max1_pc_cat_shopping_retail` | Max over ring-1 neighbours of: Place count in cell: shopping retail category (24-cat taxonomy) | float64 | 0.0–851.0 (μ 37.7825) |
| `max1_pc_cat_hawker` | Max over ring-1 neighbours of: Place count in cell: hawker category (24-cat taxonomy) | float64 | 0.0–248.0 (μ 14.8497) |
| `max1_pc_cat_residential` | Max over ring-1 neighbours of: Place count in cell: residential category (24-cat taxonomy) | float64 | 0.0–153.0 (μ 30.0974) |
| `max1_pc_cat_industrial_mfg` | Max over ring-1 neighbours of: Place count in cell: industrial mfg category (24-cat taxonomy) | float64 | 0.0–441.0 (μ 42.5055) |
| `max1_pc_cat_cafe_coffee` | Max over ring-1 neighbours of: Place count in cell: cafe coffee category (24-cat taxonomy) | float64 | 0.0–226.0 (μ 14.6339) |
| `max1_pc_cat_restaurant` | Max over ring-1 neighbours of: Place count in cell: restaurant category (24-cat taxonomy) | float64 | 0.0–621.0 (μ 27.0873) |
| `max1_pc_cat_education` | Max over ring-1 neighbours of: Place count in cell: education category (24-cat taxonomy) | float64 | 0.0–172.0 (μ 22.335) |
| `max1_pc_cat_health_medical` | Max over ring-1 neighbours of: Place count in cell: health medical category (24-cat taxonomy) | float64 | 0.0–500.0 (μ 18.0571) |
| `max1_transit_score` | Max over ring-1 neighbours of: 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) | float64 | 0.0–0.988 (μ 0.5286) |
| `max1_walkability_score` | Max over ring-1 neighbours of: Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) | float64 | 0.0–0.922 (μ 0.4369) |
| `max1_nl_2024` | Max over ring-1 neighbours of: VIIRS night light radiance 2024 (subzone-broadcast) | float64 | 0.0–161.425 (μ 57.7254) |
| `max1_nl_commercial_indicator` | Max over ring-1 neighbours of: nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) | float64 | 0.0–158.57 (μ 48.6746) |
| `max1_hdb_resale_4r_median_psm` | Max over ring-1 neighbours of: hdb resale 4r median psm (see layer docs) | float64 | 0.0–9175.258 (μ 2648.9224) |
| `max1_primary_schools_within_1km` | Max over ring-1 neighbours of: Count of primary schools within 1km | float64 | 0.0–6.71 (μ 1.1603) |
| `max1_preschools_within_400m` | Max over ring-1 neighbours of: Count of preschools within 400m | float64 | 0.0–104.0 (μ 18.0915) |
| `max1_chas_clinic_count` | Max over ring-1 neighbours of: chas clinic count (see layer docs) | float64 | 0.0–20.0 (μ 2.7884) |
| `max1_hawker_centre_count` | Max over ring-1 neighbours of: hawker centre count (see layer docs) | float64 | 0.0–6.0 (μ 0.3988) |
| `max1_tourist_attraction_count` | Max over ring-1 neighbours of: tourist attraction count (see layer docs) | float64 | 0.0–16.0 (μ 0.3552) |
| `max1_vibrancy_index` | Max over ring-1 neighbours of: Composite: places + magnets + reviews + transit + night lights | float64 | 0.0–0.988 (μ 0.2623) |
| `max1_commercial_intensity` | Max over ring-1 neighbours of: Supply/morphology composite: commercial place mix + commercial night-light + commercial land-use share | float64 | 0.0–0.998 (μ 0.1697) |
| `max1_family_index` | Max over ring-1 neighbours of: Composite: children + schools + preschools + family amenities | float64 | 0.0–0.934 (μ 0.3325) |
| `max1_density_pressure` | Max over ring-1 neighbours of: Composite: population + buildings + low road space | float64 | 0.0–0.778 (μ 0.2229) |
| `max1_pull_cbd` | Max over ring-1 neighbours of: Gravity pull toward cbd (distance-decayed attraction) | float64 | 0.0–0.969 (μ 0.1666) |
| `max1_pull_mall` | Max over ring-1 neighbours of: Gravity pull toward mall (distance-decayed attraction) | float64 | 0.0–0.952 (μ 0.1172) |
| `max1_pull_mrt_interchange` | Max over ring-1 neighbours of: Gravity pull toward mrt interchange (distance-decayed attraction) | float64 | 0.0–0.976 (μ 0.1309) |
| `max1_wc_built_share` | Max over ring-1 neighbours of: ESA WorldCover land-cover share: built share | float64 | 0.0–0.964 (μ 0.5226) |
| `max1_wc_tree_share` | Max over ring-1 neighbours of: ESA WorldCover land-cover share: tree share | float64 | 0.0–1.0 (μ 0.488) |
| `pw2_pc_total` | Proximity-weighted ring-2 aggregate of: Total mapped places (POIs) in cell — overall point-of-interest density | float64 | 0.0–3056.623 (μ 249.5529) |
| `pw2_pc_magnets` | Proximity-weighted ring-2 aggregate of: High-draw anchor places (malls, hubs, 30+ review demand magnets) | float64 | 0.0–612.004 (μ 27.1288) |
| `pw2_pc_unique_brands` | Proximity-weighted ring-2 aggregate of: Distinct retail/F&B brands present — chain richness | float64 | 0.0–70.052 (μ 15.9207) |
| `pw2_pc_cat_business_office` | Proximity-weighted ring-2 aggregate of: Place count in cell: business office category (24-cat taxonomy) | float64 | 0.0–483.964 (μ 19.9265) |
| `pw2_pc_cat_shopping_retail` | Proximity-weighted ring-2 aggregate of: Place count in cell: shopping retail category (24-cat taxonomy) | float64 | 0.0–251.061 (μ 18.2531) |
| `pw2_pc_cat_hawker` | Proximity-weighted ring-2 aggregate of: Place count in cell: hawker category (24-cat taxonomy) | float64 | 0.0–113.233 (μ 10.0219) |
| `pw2_pc_cat_residential` | Proximity-weighted ring-2 aggregate of: Place count in cell: residential category (24-cat taxonomy) | float64 | 0.0–121.291 (μ 29.9118) |
| `pw2_pc_cat_industrial_mfg` | Proximity-weighted ring-2 aggregate of: Place count in cell: industrial mfg category (24-cat taxonomy) | float64 | 0.0–212.964 (μ 15.5453) |
| `pw2_pc_cat_cafe_coffee` | Proximity-weighted ring-2 aggregate of: Place count in cell: cafe coffee category (24-cat taxonomy) | float64 | 0.0–140.953 (μ 9.6274) |
| `pw2_pc_cat_restaurant` | Proximity-weighted ring-2 aggregate of: Place count in cell: restaurant category (24-cat taxonomy) | float64 | 0.0–366.615 (μ 14.8971) |
| `pw2_pc_cat_education` | Proximity-weighted ring-2 aggregate of: Place count in cell: education category (24-cat taxonomy) | float64 | 0.0–102.367 (μ 17.254) |
| `pw2_pc_cat_health_medical` | Proximity-weighted ring-2 aggregate of: Place count in cell: health medical category (24-cat taxonomy) | float64 | 0.0–147.628 (μ 10.5513) |
| `pw2_transit_score` | Proximity-weighted ring-2 aggregate of: 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) | float64 | 0.0–0.963 (μ 0.4594) |
| `pw2_walkability_score` | Proximity-weighted ring-2 aggregate of: Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) | float64 | 0.0–0.846 (μ 0.3877) |
| `pw2_nl_2024` | Proximity-weighted ring-2 aggregate of: VIIRS night light radiance 2024 (subzone-broadcast) | float64 | 0.0–158.585 (μ 38.1092) |
| `pw2_nl_commercial_indicator` | Proximity-weighted ring-2 aggregate of: nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) | float64 | 0.0–158.511 (μ 19.817) |
| `pw2_hdb_resale_4r_median_psm` | Proximity-weighted ring-2 aggregate of: hdb resale 4r median psm (see layer docs) | float64 | 0.0–8537.339 (μ 2824.7757) |
| `pw2_primary_schools_within_1km` | Proximity-weighted ring-2 aggregate of: Count of primary schools within 1km | float64 | 0.0–5.557 (μ 1.1615) |
| `pw2_preschools_within_400m` | Proximity-weighted ring-2 aggregate of: Count of preschools within 400m | float64 | 0.0–70.703 (μ 17.1557) |
| `pw2_chas_clinic_count` | Proximity-weighted ring-2 aggregate of: chas clinic count (see layer docs) | float64 | 0.0–10.444 (μ 2.1737) |
| `pw2_hawker_centre_count` | Proximity-weighted ring-2 aggregate of: hawker centre count (see layer docs) | float64 | 0.0–2.591 (μ 0.2359) |
| `pw2_tourist_attraction_count` | Proximity-weighted ring-2 aggregate of: tourist attraction count (see layer docs) | float64 | 0.0–7.5 (μ 0.0924) |
| `pw2_vibrancy_index` | Proximity-weighted ring-2 aggregate of: Composite: places + magnets + reviews + transit + night lights | float64 | 0.0–0.831 (μ 0.2007) |
| `pw2_commercial_intensity` | Proximity-weighted ring-2 aggregate of: Supply/morphology composite: commercial place mix + commercial night-light + commercial land-use share | float64 | 0.0–0.769 (μ 0.1005) |
| `pw2_family_index` | Proximity-weighted ring-2 aggregate of: Composite: children + schools + preschools + family amenities | float64 | 0.0–0.851 (μ 0.3176) |
| `pw2_density_pressure` | Proximity-weighted ring-2 aggregate of: Composite: population + buildings + low road space | float64 | 0.0–0.72 (μ 0.1935) |
| `pw2_pull_cbd` | Proximity-weighted ring-2 aggregate of: Gravity pull toward cbd (distance-decayed attraction) | float64 | 0.0–0.923 (μ 0.1355) |
| `pw2_pull_mall` | Proximity-weighted ring-2 aggregate of: Gravity pull toward mall (distance-decayed attraction) | float64 | 0.0–0.794 (μ 0.1004) |
| `pw2_pull_mrt_interchange` | Proximity-weighted ring-2 aggregate of: Gravity pull toward mrt interchange (distance-decayed attraction) | float64 | 0.0–0.825 (μ 0.1133) |
| `pw2_wc_built_share` | Proximity-weighted ring-2 aggregate of: ESA WorldCover land-cover share: built share | float64 | 0.0–0.883 (μ 0.3778) |
| `pw2_wc_tree_share` | Proximity-weighted ring-2 aggregate of: ESA WorldCover land-cover share: tree share | float64 | 0.0–0.988 (μ 0.2091) |
| `max2_pc_total` | Max over ring-2 neighbours of: Total mapped places (POIs) in cell — overall point-of-interest density | float64 | 0.0–4929.0 (μ 529.4584) |
| `max2_pc_magnets` | Max over ring-2 neighbours of: High-draw anchor places (malls, hubs, 30+ review demand magnets) | float64 | 0.0–980.0 (μ 81.8069) |
| `max2_pc_unique_brands` | Max over ring-2 neighbours of: Distinct retail/F&B brands present — chain richness | float64 | 0.0–126.0 (μ 32.817) |
| `max2_pc_cat_business_office` | Max over ring-2 neighbours of: Place count in cell: business office category (24-cat taxonomy) | float64 | 0.0–755.0 (μ 83.3031) |
| `max2_pc_cat_shopping_retail` | Max over ring-2 neighbours of: Place count in cell: shopping retail category (24-cat taxonomy) | float64 | 0.0–851.0 (μ 58.6356) |
| `max2_pc_cat_hawker` | Max over ring-2 neighbours of: Place count in cell: hawker category (24-cat taxonomy) | float64 | 0.0–248.0 (μ 22.7515) |
| `max2_pc_cat_residential` | Max over ring-2 neighbours of: Place count in cell: residential category (24-cat taxonomy) | float64 | 0.0–153.0 (μ 43.4559) |
| `max2_pc_cat_industrial_mfg` | Max over ring-2 neighbours of: Place count in cell: industrial mfg category (24-cat taxonomy) | float64 | 0.0–441.0 (μ 65.7607) |
| `max2_pc_cat_cafe_coffee` | Max over ring-2 neighbours of: Place count in cell: cafe coffee category (24-cat taxonomy) | float64 | 0.0–226.0 (μ 21.8665) |
| `max2_pc_cat_restaurant` | Max over ring-2 neighbours of: Place count in cell: restaurant category (24-cat taxonomy) | float64 | 0.0–621.0 (μ 42.0529) |
| `max2_pc_cat_education` | Max over ring-2 neighbours of: Place count in cell: education category (24-cat taxonomy) | float64 | 0.0–172.0 (μ 32.8455) |
| `max2_pc_cat_health_medical` | Max over ring-2 neighbours of: Place count in cell: health medical category (24-cat taxonomy) | float64 | 0.0–500.0 (μ 28.466) |
| `max2_transit_score` | Max over ring-2 neighbours of: 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) | float64 | 0.0–0.988 (μ 0.6156) |
| `max2_walkability_score` | Max over ring-2 neighbours of: Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) | float64 | 0.0–0.922 (μ 0.5226) |
| `max2_nl_2024` | Max over ring-2 neighbours of: VIIRS night light radiance 2024 (subzone-broadcast) | float64 | 0.0–161.425 (μ 68.2295) |
| `max2_nl_commercial_indicator` | Max over ring-2 neighbours of: nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) | float64 | 0.0–158.57 (μ 58.8361) |
| `max2_hdb_resale_4r_median_psm` | Max over ring-2 neighbours of: hdb resale 4r median psm (see layer docs) | float64 | 0.0–9175.258 (μ 3373.2959) |
| `max2_primary_schools_within_1km` | Max over ring-2 neighbours of: Count of primary schools within 1km | float64 | 0.0–6.71 (μ 1.6725) |
| `max2_preschools_within_400m` | Max over ring-2 neighbours of: Count of preschools within 400m | float64 | 0.0–104.0 (μ 25.9202) |
| `max2_chas_clinic_count` | Max over ring-2 neighbours of: chas clinic count (see layer docs) | float64 | 0.0–20.0 (μ 4.1755) |
| `max2_hawker_centre_count` | Max over ring-2 neighbours of: hawker centre count (see layer docs) | float64 | 0.0–6.0 (μ 0.6306) |
| `max2_tourist_attraction_count` | Max over ring-2 neighbours of: tourist attraction count (see layer docs) | float64 | 0.0–16.0 (μ 0.6264) |
| `max2_vibrancy_index` | Max over ring-2 neighbours of: Composite: places + magnets + reviews + transit + night lights | float64 | 0.0–0.988 (μ 0.3288) |
| `max2_commercial_intensity` | Max over ring-2 neighbours of: Supply/morphology composite: commercial place mix + commercial night-light + commercial land-use share | float64 | 0.0–0.998 (μ 0.2284) |
| `max2_family_index` | Max over ring-2 neighbours of: Composite: children + schools + preschools + family amenities | float64 | 0.0–0.934 (μ 0.4229) |
| `max2_density_pressure` | Max over ring-2 neighbours of: Composite: population + buildings + low road space | float64 | 0.0–0.778 (μ 0.3043) |
| `max2_pull_cbd` | Max over ring-2 neighbours of: Gravity pull toward cbd (distance-decayed attraction) | float64 | 0.0–0.969 (μ 0.192) |
| `max2_pull_mall` | Max over ring-2 neighbours of: Gravity pull toward mall (distance-decayed attraction) | float64 | 0.0–0.952 (μ 0.1435) |
| `max2_pull_mrt_interchange` | Max over ring-2 neighbours of: Gravity pull toward mrt interchange (distance-decayed attraction) | float64 | 0.0–0.976 (μ 0.162) |
| `max2_wc_built_share` | Max over ring-2 neighbours of: ESA WorldCover land-cover share: built share | float64 | 0.0–0.964 (μ 0.622) |
| `max2_wc_tree_share` | Max over ring-2 neighbours of: ESA WorldCover land-cover share: tree share | float64 | 0.0–1.0 (μ 0.593) |
| `cap_cafe_coffee` | Huff capture for a NEW cafe_coffee outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) | float64 | 0.0–3.9242 (μ 0.5934) |
| `cap_restaurant` | Huff capture for a NEW restaurant outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) | float64 | 0.0–3.7734 (μ 0.7323) |
| `cap_hawker` | Huff capture for a NEW hawker outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) | float64 | 0.0–4.9628 (μ 0.6071) |
| `cap_fast_food` | Huff capture for a NEW fast_food outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) | float64 | 0.0–2.1472 (μ 0.4812) |
| `cap_supermarket` | Huff capture for a NEW supermarket outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) | float64 | 0.0–3.206 (μ 0.5143) |
| `cap_convenience` | Huff capture for a NEW convenience outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) | float64 | 0.0–4.0129 (μ 0.5394) |
| `cap_fitness_recreation` | Huff capture for a NEW fitness_recreation outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) | float64 | 0.0–3.5699 (μ 0.607) |
| `cap_health_medical` | Huff capture for a NEW health_medical outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) | float64 | 0.0–4.4454 (μ 0.6242) |
| `cap_beauty_personal` | Huff capture for a NEW beauty_personal outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) | float64 | 0.0–3.9384 (μ 0.6154) |
| `cap_shopping_retail` | Huff capture for a NEW shopping_retail outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) | float64 | 0.0–4.2264 (μ 0.7709) |
| `cap_education` | Huff capture for a NEW education outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) | float64 | 0.0–2.4924 (μ 0.5225) |
| `cap_total` | Sum of per-category Huff capture: demand (outlet-equivalents) a NEW outlet at the best hex9 in this hex would win vs existing competition. λ ASSUMED (500/700/1000/1500m priors; not identifiable from data — rankings λ-robust ρ≥0.83) | float64 | 0.0–38.4057 (μ 6.5494) |
| `cap_best_category` | Category with the highest capture at this hex | object | e.g. cafe_coffee |
| `pc2_total` | Fine-taxonomy place metric: total | int64 | 0.0–4929.0 (μ 159.9992) |
| `pc2_branded_count` | Fine-taxonomy place metric: branded count | int64 | 0.0–221.0 (μ 12.7011) |
| `pc2_unbranded_count` | Fine-taxonomy place metric: unbranded count | int64 | 0.0–4752.0 (μ 147.2981) |
| `pc2_cat_biz_office_count` | Place count in cell: biz office (55-cat fine taxonomy) | int64 | 0.0–209.0 (μ 3.78) |
| `pc2_cat_civic_community_count` | Place count in cell: civic community (55-cat fine taxonomy) | int64 | 0.0–9.0 (μ 0.5298) |
| `pc2_cat_civic_government_count` | Place count in cell: civic government (55-cat fine taxonomy) | int64 | 0.0–35.0 (μ 0.927) |
| `pc2_cat_civic_nonprofit_count` | Place count in cell: civic nonprofit (55-cat fine taxonomy) | int64 | 0.0–52.0 (μ 2.0218) |
| `pc2_cat_civic_religious_count` | Place count in cell: civic religious (55-cat fine taxonomy) | int64 | 0.0–37.0 (μ 0.9656) |
| `pc2_cat_edu_preschool_count` | Place count in cell: edu preschool (55-cat fine taxonomy) | int64 | 0.0–35.0 (μ 2.2149) |
| `pc2_cat_edu_primary_secondary_count` | Place count in cell: edu primary secondary (55-cat fine taxonomy) | int64 | 0.0–60.0 (μ 0.9857) |
| `pc2_cat_edu_specialty_count` | Place count in cell: edu specialty (55-cat fine taxonomy) | int64 | 0.0–12.0 (μ 0.1982) |
| `pc2_cat_edu_tertiary_count` | Place count in cell: edu tertiary (55-cat fine taxonomy) | int64 | 0.0–19.0 (μ 0.3426) |
| `pc2_cat_edu_tuition_count` | Place count in cell: edu tuition (55-cat fine taxonomy) | int64 | 0.0–129.0 (μ 4.3165) |
| `pc2_cat_food_bakery_count` | Place count in cell: food bakery (55-cat fine taxonomy) | int64 | 0.0–36.0 (μ 1.5323) |
| `pc2_cat_food_bar_count` | Place count in cell: food bar (55-cat fine taxonomy) | int64 | 0.0–79.0 (μ 0.6994) |
| `pc2_cat_food_cafe_count` | Place count in cell: food cafe (55-cat fine taxonomy) | int64 | 0.0–152.0 (μ 3.9857) |
| `pc2_cat_food_caterer_count` | Place count in cell: food caterer (55-cat fine taxonomy) | int64 | 0.0–17.0 (μ 0.152) |
| `pc2_cat_food_dessert_count` | Place count in cell: food dessert (55-cat fine taxonomy) | int64 | 0.0–66.0 (μ 1.4702) |
| `pc2_cat_food_fast_food_count` | Place count in cell: food fast food (55-cat fine taxonomy) | int64 | 0.0–18.0 (μ 0.7145) |
| `pc2_cat_food_hawker_count` | Place count in cell: food hawker (55-cat fine taxonomy) | int64 | 0.0–246.0 (μ 4.8766) |
| `pc2_cat_food_restaurant_count` | Place count in cell: food restaurant (55-cat fine taxonomy) | int64 | 0.0–503.0 (μ 7.9429) |
| `pc2_cat_health_clinic_count` | Place count in cell: health clinic (55-cat fine taxonomy) | int64 | 0.0–133.0 (μ 1.9169) |
| `pc2_cat_health_hospital_count` | Place count in cell: health hospital (55-cat fine taxonomy) | int64 | 0.0–46.0 (μ 0.2603) |
| `pc2_cat_health_pharmacy_count` | Place count in cell: health pharmacy (55-cat fine taxonomy) | int64 | 0.0–32.0 (μ 0.639) |
| `pc2_cat_health_specialist_count` | Place count in cell: health specialist (55-cat fine taxonomy) | int64 | 0.0–183.0 (μ 1.6071) |
| `pc2_cat_health_tcm_count` | Place count in cell: health tcm (55-cat fine taxonomy) | int64 | 0.0–16.0 (μ 0.4341) |
| `pc2_cat_leisure_entertainment_count` | Place count in cell: leisure entertainment (55-cat fine taxonomy) | int64 | 0.0–32.0 (μ 0.5214) |
| `pc2_cat_leisure_park_count` | Place count in cell: leisure park (55-cat fine taxonomy) | int64 | 0.0–28.0 (μ 3.0512) |
| `pc2_cat_leisure_tourist_count` | Place count in cell: leisure tourist (55-cat fine taxonomy) | int64 | 0.0–50.0 (μ 0.749) |
| `pc2_cat_other_count` | Place count in cell: other (55-cat fine taxonomy) | int64 | 0.0–926.0 (μ 32.5617) |
| `pc2_cat_res_aged_care_count` | Place count in cell: res aged care (55-cat fine taxonomy) | int64 | 0.0–8.0 (μ 0.3048) |
| `pc2_cat_res_hdb_count` | Place count in cell: res hdb (55-cat fine taxonomy) | int64 | 0.0–90.0 (μ 5.6558) |
| `pc2_cat_res_private_count` | Place count in cell: res private (55-cat fine taxonomy) | int64 | 0.0–103.0 (μ 3.9765) |
| `pc2_cat_retail_apparel_count` | Place count in cell: retail apparel (55-cat fine taxonomy) | int64 | 0.0–265.0 (μ 2.22) |
| `pc2_cat_retail_convenience_count` | Place count in cell: retail convenience (55-cat fine taxonomy) | int64 | 0.0–64.0 (μ 4.3191) |
| `pc2_cat_retail_electronics_count` | Place count in cell: retail electronics (55-cat fine taxonomy) | int64 | 0.0–87.0 (μ 0.9387) |
| `pc2_cat_retail_furniture_home_count` | Place count in cell: retail furniture home (55-cat fine taxonomy) | int64 | 0.0–85.0 (μ 2.5206) |
| `pc2_cat_retail_general_count` | Place count in cell: retail general (55-cat fine taxonomy) | int64 | 0.0–94.0 (μ 3.3401) |
| `pc2_cat_retail_jewelry_cosmetics_count` | Place count in cell: retail jewelry cosmetics (55-cat fine taxonomy) | int64 | 0.0–265.0 (μ 1.3375) |
| `pc2_cat_retail_mall_count` | Place count in cell: retail mall (55-cat fine taxonomy) | int64 | 0.0–31.0 (μ 0.403) |
| `pc2_cat_retail_supermarket_count` | Place count in cell: retail supermarket (55-cat fine taxonomy) | int64 | 0.0–55.0 (μ 1.707) |
| `pc2_cat_service_automotive_count` | Place count in cell: service automotive (55-cat fine taxonomy) | int64 | 0.0–234.0 (μ 3.1847) |
| `pc2_cat_service_beauty_count` | Place count in cell: service beauty (55-cat fine taxonomy) | int64 | 0.0–324.0 (μ 5.9572) |
| `pc2_cat_service_cleaning_repair_count` | Place count in cell: service cleaning repair (55-cat fine taxonomy) | int64 | 0.0–29.0 (μ 1.0806) |
| `pc2_cat_service_consulting_count` | Place count in cell: service consulting (55-cat fine taxonomy) | int64 | 0.0–637.0 (μ 10.4962) |
| `pc2_cat_service_fitness_count` | Place count in cell: service fitness (55-cat fine taxonomy) | int64 | 0.0–86.0 (μ 2.5835) |
| `pc2_cat_service_legal_finance_count` | Place count in cell: service legal finance (55-cat fine taxonomy) | int64 | 0.0–378.0 (μ 2.4081) |
| `pc2_cat_service_logistics_count` | Place count in cell: service logistics (55-cat fine taxonomy) | int64 | 0.0–312.0 (μ 10.7976) |
| `pc2_cat_service_other_count` | Place count in cell: service other (55-cat fine taxonomy) | int64 | 0.0–304.0 (μ 7.042) |
| `pc2_cat_service_pet_count` | Place count in cell: service pet (55-cat fine taxonomy) | int64 | 0.0–9.0 (μ 0.2771) |
| `pc2_cat_service_real_estate_count` | Place count in cell: service real estate (55-cat fine taxonomy) | int64 | 0.0–113.0 (μ 0.9186) |
| `pc2_cat_transport_air_count` | Place count in cell: transport air (55-cat fine taxonomy) | int64 | 0.0–7.0 (μ 0.0781) |
| `pc2_cat_transport_bus_count` | Place count in cell: transport bus (55-cat fine taxonomy) | int64 | 0.0–42.0 (μ 3.1436) |
| `pc2_cat_transport_ev_count` | Place count in cell: transport ev (55-cat fine taxonomy) | int64 | 0.0–23.0 (μ 2.2418) |
| `pc2_cat_transport_mrt_count` | Place count in cell: transport mrt (55-cat fine taxonomy) | int64 | 0.0–10.0 (μ 0.4072) |
| `pc2_cat_transport_other_count` | Place count in cell: transport other (55-cat fine taxonomy) | int64 | 0.0–6.0 (μ 0.246) |
| `pc2_cat_transport_parking_count` | Place count in cell: transport parking (55-cat fine taxonomy) | int64 | 0.0–39.0 (μ 2.2561) |
| `pc2_cat_unmapped_count` | Place count in cell: unmapped (55-cat fine taxonomy) | int64 | 0.0–62.0 (μ 0.7615) |
| `pc2_dominant_category` | Fine-taxonomy place metric: dominant category | object | e.g. none |
| `mg_bakery_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for bakery | float64 | 0.0–37.957 (μ 1.4887) |
| `mg_bar_nightlife_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for bar nightlife | float64 | 0.0–18.892 (μ 0.1977) |
| `mg_beauty_personal_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for beauty personal | float64 | 0.0–84.188 (μ 1.7573) |
| `mg_business_office_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for business office | float64 | 0.0–170.442 (μ 3.7388) |
| `mg_cafe_coffee_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for cafe coffee | float64 | 0.0–32.912 (μ 1.6288) |
| `mg_convenience_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for convenience | float64 | 0.0–23.651 (μ 1.3746) |
| `mg_education_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for education | float64 | 0.0–54.286 (μ 1.4879) |
| `mg_entertainment_culture_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for entertainment culture | float64 | 0.0–16.714 (μ 0.1843) |
| `mg_fast_food_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for fast food | float64 | 0.0–88.0 (μ 3.0449) |
| `mg_fitness_recreation_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for fitness recreation | float64 | 0.0–16.805 (μ 0.361) |
| `mg_government_public_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for government public | float64 | 0.0–11.553 (μ 0.1883) |
| `mg_hawker_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for hawker | float64 | 0.0–106.48 (μ 4.0904) |
| `mg_health_medical_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for health medical | float64 | 0.0–120.4 (μ 1.3119) |
| `mg_hotel_hospitality_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for hotel hospitality | float64 | 0.0–56.389 (μ 0.2758) |
| `mg_industrial_mfg_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for industrial mfg | float64 | 0.0–107.818 (μ 2.9506) |
| `mg_other_uncategorized_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for other uncategorized | float64 | 0.0–0.0 (μ 0.0) |
| `mg_park_open_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for park open | float64 | 0.0–7.37 (μ 0.3525) |
| `mg_religious_worship_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for religious worship | float64 | 0.0–13.316 (μ 0.2622) |
| `mg_residential_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for residential | float64 | 0.0–17.736 (μ 1.1275) |
| `mg_restaurant_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for restaurant | float64 | 0.0–117.465 (μ 4.7974) |
| `mg_services_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for services | float64 | 0.0–129.318 (μ 3.4096) |
| `mg_shopping_retail_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for shopping retail | float64 | 0.0–101.341 (μ 3.376) |
| `mg_supermarket_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for supermarket | float64 | 0.0–27.312 (μ 1.256) |
| `mg_transportation_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for transportation | float64 | 0.0–16.948 (μ 1.212) |
| `mg_bakery_support_400m` | Magnet model: complementary-category support density within 400 m for bakery (demand context, not supply) | float64 | 0.0–156.311 (μ 5.6948) |
| `mg_bar_nightlife_support_400m` | Magnet model: complementary-category support density within 400 m for bar nightlife (demand context, not supply) | float64 | 0.0–80.754 (μ 1.8953) |
| `mg_beauty_personal_support_400m` | Magnet model: complementary-category support density within 400 m for beauty personal (demand context, not supply) | float64 | 0.0–170.216 (μ 5.592) |
| `mg_business_office_support_400m` | Magnet model: complementary-category support density within 400 m for business office (demand context, not supply) | float64 | 0.0–222.274 (μ 6.2692) |
| `mg_cafe_coffee_support_400m` | Magnet model: complementary-category support density within 400 m for cafe coffee (demand context, not supply) | float64 | 0.0–153.583 (μ 6.4191) |
| `mg_convenience_support_400m` | Magnet model: complementary-category support density within 400 m for convenience (demand context, not supply) | float64 | 0.0–22.595 (μ 2.3331) |
| `mg_education_support_400m` | Magnet model: complementary-category support density within 400 m for education (demand context, not supply) | float64 | 0.0–26.676 (μ 1.8421) |
| `mg_entertainment_culture_support_400m` | Magnet model: complementary-category support density within 400 m for entertainment culture (demand context, not supply) | float64 | 0.0–84.269 (μ 1.1172) |
| `mg_fast_food_support_400m` | Magnet model: complementary-category support density within 400 m for fast food (demand context, not supply) | float64 | 0.0–127.667 (μ 4.5054) |
| `mg_fitness_recreation_support_400m` | Magnet model: complementary-category support density within 400 m for fitness recreation (demand context, not supply) | float64 | 0.0–110.273 (μ 2.8849) |
| `mg_government_public_support_400m` | Magnet model: complementary-category support density within 400 m for government public (demand context, not supply) | float64 | 0.0–159.333 (μ 3.064) |
| `mg_hawker_support_400m` | Magnet model: complementary-category support density within 400 m for hawker (demand context, not supply) | float64 | 0.0–30.815 (μ 2.5011) |
| `mg_health_medical_support_400m` | Magnet model: complementary-category support density within 400 m for health medical (demand context, not supply) | float64 | 0.0–116.086 (μ 3.1652) |
| `mg_hotel_hospitality_support_400m` | Magnet model: complementary-category support density within 400 m for hotel hospitality (demand context, not supply) | float64 | 0.0–88.25 (μ 1.4757) |
| `mg_industrial_mfg_support_400m` | Magnet model: complementary-category support density within 400 m for industrial mfg (demand context, not supply) | float64 | 0.0–311.606 (μ 7.0638) |
| `mg_other_uncategorized_support_400m` | Magnet model: complementary-category support density within 400 m for other uncategorized (demand context, not supply) | float64 | 0.0–0.0 (μ 0.0) |
| `mg_park_open_support_400m` | Magnet model: complementary-category support density within 400 m for park open (demand context, not supply) | float64 | 0.0–68.375 (μ 1.9045) |
| `mg_religious_worship_support_400m` | Magnet model: complementary-category support density within 400 m for religious worship (demand context, not supply) | float64 | 0.0–19.491 (μ 0.6389) |
| `mg_residential_support_400m` | Magnet model: complementary-category support density within 400 m for residential (demand context, not supply) | float64 | 0.0–33.6 (μ 1.6342) |
| `mg_restaurant_support_400m` | Magnet model: complementary-category support density within 400 m for restaurant (demand context, not supply) | float64 | 0.0–94.874 (μ 2.8875) |
| `mg_services_support_400m` | Magnet model: complementary-category support density within 400 m for services (demand context, not supply) | float64 | 0.0–209.333 (μ 6.3744) |
| `mg_shopping_retail_support_400m` | Magnet model: complementary-category support density within 400 m for shopping retail (demand context, not supply) | float64 | 0.0–132.825 (μ 4.9896) |
| `mg_supermarket_support_400m` | Magnet model: complementary-category support density within 400 m for supermarket (demand context, not supply) | float64 | 0.0–120.312 (μ 3.8826) |
| `mg_transportation_support_400m` | Magnet model: complementary-category support density within 400 m for transportation (demand context, not supply) | float64 | 0.0–201.824 (μ 5.216) |
| `mg_bakery_anchor_strength` | Magnet model: strength of the biggest bakery anchor place nearby | float64 | 0.0–1061.391 (μ 16.5256) |
| `mg_bar_nightlife_anchor_strength` | Magnet model: strength of the biggest bar nightlife anchor place nearby | float64 | 0.0–190.138 (μ 3.4953) |
| `mg_beauty_personal_anchor_strength` | Magnet model: strength of the biggest beauty personal anchor place nearby | float64 | 0.0–877.934 (μ 16.1674) |
| `mg_business_office_anchor_strength` | Magnet model: strength of the biggest business office anchor place nearby | float64 | 0.0–247.847 (μ 5.4519) |
| `mg_cafe_coffee_anchor_strength` | Magnet model: strength of the biggest cafe coffee anchor place nearby | float64 | 0.0–1123.877 (μ 21.9851) |
| `mg_convenience_anchor_strength` | Magnet model: strength of the biggest convenience anchor place nearby | float64 | 0.0–62.344 (μ 3.1894) |
| `mg_education_anchor_strength` | Magnet model: strength of the biggest education anchor place nearby | float64 | 0.0–30.155 (μ 0.6627) |
| `mg_entertainment_culture_anchor_strength` | Magnet model: strength of the biggest entertainment culture anchor place nearby | float64 | 0.0–756.988 (μ 9.0258) |
| `mg_fast_food_anchor_strength` | Magnet model: strength of the biggest fast food anchor place nearby | float64 | 0.0–909.984 (μ 16.1578) |
| `mg_fitness_recreation_anchor_strength` | Magnet model: strength of the biggest fitness recreation anchor place nearby | float64 | 0.0–762.9 (μ 9.5959) |
| `mg_government_public_anchor_strength` | Magnet model: strength of the biggest government public anchor place nearby | float64 | 0.0–62.716 (μ 1.4588) |
| `mg_hawker_anchor_strength` | Magnet model: strength of the biggest hawker anchor place nearby | float64 | 0.0–67.717 (μ 2.2275) |
| `mg_health_medical_anchor_strength` | Magnet model: strength of the biggest health medical anchor place nearby | float64 | 0.0–56.689 (μ 2.2331) |
| `mg_hotel_hospitality_anchor_strength` | Magnet model: strength of the biggest hotel hospitality anchor place nearby | float64 | 0.0–777.08 (μ 10.1035) |
| `mg_industrial_mfg_anchor_strength` | Magnet model: strength of the biggest industrial mfg anchor place nearby | float64 | 0.0–247.896 (μ 5.0027) |
| `mg_other_uncategorized_anchor_strength` | Magnet model: strength of the biggest other uncategorized anchor place nearby | float64 | 0.0–0.0 (μ 0.0) |
| `mg_park_open_anchor_strength` | Magnet model: strength of the biggest park open anchor place nearby | float64 | 0.0–27.708 (μ 0.5224) |
| `mg_religious_worship_anchor_strength` | Magnet model: strength of the biggest religious worship anchor place nearby | float64 | 0.0–22.459 (μ 0.4768) |
| `mg_residential_anchor_strength` | Magnet model: strength of the biggest residential anchor place nearby | float64 | 0.0–494.497 (μ 7.5267) |
| `mg_restaurant_anchor_strength` | Magnet model: strength of the biggest restaurant anchor place nearby | float64 | 0.0–988.916 (μ 18.6324) |
| `mg_services_anchor_strength` | Magnet model: strength of the biggest services anchor place nearby | float64 | 0.0–933.967 (μ 16.6037) |
| `mg_shopping_retail_anchor_strength` | Magnet model: strength of the biggest shopping retail anchor place nearby | float64 | 0.0–1007.613 (μ 18.2283) |
| `mg_supermarket_anchor_strength` | Magnet model: strength of the biggest supermarket anchor place nearby | float64 | 0.0–42.406 (μ 0.7219) |
| `mg_transportation_anchor_strength` | Magnet model: strength of the biggest transportation anchor place nearby | float64 | 0.0–955.376 (μ 11.7942) |
| `mg_avg_competitors_400m` | Magnet model: mean same-category competitor count within 400 m across categories | float64 | 0.0–90.983 (μ 3.8686) |
| `mg_avg_anchor_strength` | Magnet model: strength of the biggest avg anchor place nearby | float64 | 0.0–650.046 (μ 11.7139) |
| `mg_avg_walk_dist_mrt_m` | Magnet model: mean walk distance to MRT across category micrographs | float64 | 0.0–9999.0 (μ 3885.6039) |
| `colo_fit_cafe_coffee` | Co-location mix-match for cafe_coffee: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) | float64 | -0.3437–0.1978 (μ 0.0701) |
| `colo_fit_restaurant` | Co-location mix-match for restaurant: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) | float64 | -0.1142–0.5724 (μ 0.186) |
| `colo_fit_hawker` | Co-location mix-match for hawker: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) | float64 | -0.5932–0.2667 (μ -0.0098) |
| `colo_fit_fast_food` | Co-location mix-match for fast_food: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) | float64 | -0.7249–0.266 (μ 0.021) |
| `colo_fit_supermarket` | Co-location mix-match for supermarket: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) | float64 | -0.3589–0.1712 (μ -0.0192) |
| `colo_fit_convenience` | Co-location mix-match for convenience: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) | float64 | -0.3274–0.187 (μ 0.0) |
| `colo_fit_fitness_recreation` | Co-location mix-match for fitness_recreation: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) | float64 | -0.5516–0.1304 (μ -0.0436) |
| `colo_fit_health_medical` | Co-location mix-match for health_medical: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) | float64 | -0.4839–0.2461 (μ 0.0504) |
| `colo_fit_beauty_personal` | Co-location mix-match for beauty_personal: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) | float64 | -0.4114–0.547 (μ 0.1568) |
| `colo_fit_shopping_retail` | Co-location mix-match for shopping_retail: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) | float64 | 0.0–0.4489 (μ 0.1399) |
| `colo_fit_education` | Co-location mix-match for education: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) | float64 | -0.5625–0.2059 (μ -0.0569) |
| `pc_total` | Total mapped places (POIs) in cell — overall point-of-interest density | float64 | 0.0–4929.0 (μ 159.9992) |
| `pc_unique_brands` | Distinct retail/F&B brands present — chain richness | float64 | 0.0–414.0 (μ 13.1436) |
| `pc_magnets` | High-draw anchor places (malls, hubs, 30+ review demand magnets) | float64 | 0.0–980.0 (μ 18.1075) |
| `pc_long_tail` | Places with few/no reviews — independent long-tail share base | float64 | 0.0–2392.0 (μ 90.9757) |
| `pc_with_rating` | Places carrying a Google rating | float64 | 0.0–3078.0 (μ 91.8455) |
| `pc_total_reviews` | Sum of review counts — popularity/footfall proxy | float64 | 0.0–895143.0 (μ 16382.9152) |
| `pc_avg_rating` | Mean rating of rated places — quality proxy | float64 | 0.0–5.0 (μ 2.9317) |
| `pc_cat_bakery` | Place count in cell: bakery category (24-cat taxonomy) | float64 | 0.0–45.0 (μ 1.7112) |
| `pc_cat_bar_nightlife` | Place count in cell: bar nightlife category (24-cat taxonomy) | float64 | 0.0–100.0 (μ 0.9404) |
| `pc_cat_beauty_personal` | Place count in cell: beauty personal category (24-cat taxonomy) | float64 | 0.0–371.0 (μ 6.5214) |
| `pc_cat_business_office` | Place count in cell: business office category (24-cat taxonomy) | float64 | 0.0–755.0 (μ 18.1293) |
| `pc_cat_cafe_coffee` | Place count in cell: cafe coffee category (24-cat taxonomy) | float64 | 0.0–226.0 (μ 5.4736) |
| `pc_cat_convenience` | Place count in cell: convenience category (24-cat taxonomy) | float64 | 0.0–43.0 (μ 1.817) |
| `pc_cat_education` | Place count in cell: education category (24-cat taxonomy) | float64 | 0.0–172.0 (μ 9.3829) |
| `pc_cat_entertainment_culture` | Place count in cell: entertainment culture category (24-cat taxonomy) | float64 | 0.0–104.0 (μ 1.8228) |
| `pc_cat_fast_food` | Place count in cell: fast food category (24-cat taxonomy) | float64 | 0.0–24.0 (μ 0.7876) |
| `pc_cat_fitness_recreation` | Place count in cell: fitness recreation category (24-cat taxonomy) | float64 | 0.0–94.0 (μ 3.377) |
| `pc_cat_government_public` | Place count in cell: government public category (24-cat taxonomy) | float64 | 0.0–52.0 (μ 1.6238) |
| `pc_cat_hawker` | Place count in cell: hawker category (24-cat taxonomy) | float64 | 0.0–248.0 (μ 4.9471) |
| `pc_cat_health_medical` | Place count in cell: health medical category (24-cat taxonomy) | float64 | 0.0–500.0 (μ 6.2578) |
| `pc_cat_hotel_hospitality` | Place count in cell: hotel hospitality category (24-cat taxonomy) | float64 | 0.0–67.0 (μ 0.9874) |
| `pc_cat_industrial_mfg` | Place count in cell: industrial mfg category (24-cat taxonomy) | float64 | 0.0–441.0 (μ 15.0747) |
| `pc_cat_other_uncategorized` | Place count in cell: other uncategorized category (24-cat taxonomy) | float64 | 0.0–90.0 (μ 2.848) |
| `pc_cat_park_open` | Place count in cell: park open category (24-cat taxonomy) | float64 | 0.0–36.0 (μ 3.7204) |
| `pc_cat_religious_worship` | Place count in cell: religious worship category (24-cat taxonomy) | float64 | 0.0–57.0 (μ 1.4517) |
| `pc_cat_residential` | Place count in cell: residential category (24-cat taxonomy) | float64 | 0.0–153.0 (μ 13.6616) |
| `pc_cat_restaurant` | Place count in cell: restaurant category (24-cat taxonomy) | float64 | 0.0–621.0 (μ 9.4744) |
| `pc_cat_services` | Place count in cell: services category (24-cat taxonomy) | float64 | 0.0–831.0 (μ 19.0521) |
| `pc_cat_shopping_retail` | Place count in cell: shopping retail category (24-cat taxonomy) | float64 | 0.0–851.0 (μ 12.9076) |
| `pc_cat_supermarket` | Place count in cell: supermarket category (24-cat taxonomy) | float64 | 0.0–80.0 (μ 2.4677) |
| `pc_cat_transportation` | Place count in cell: transportation category (24-cat taxonomy) | float64 | 0.0–153.0 (μ 10.8321) |
| `pc_cat_financial_services` | Count of financial venues in cell (ATM/bank/insurance/remittance) | float64 | 0.0–295.0 (μ 3.1234) |
| `pc_cat_automated_kiosk` | Count of unmanned automated points (vending/locker/AXS) in cell | float64 | 0.0–23.0 (μ 1.6062) |
| `pc_diversity` | Category entropy of the place mix — high = mixed-use | float64 | 0.0–2.953 (μ 1.3054) |
| `pc_dominant_category` | Most common place category in cell | object | e.g. none |
| `rent_resi_psf_med` | URA private-resi median rent (913 projects, last 4 quarters, IDW k=5 ≤2.5 km). COMMERCIAL rent not openly available. NaN = no observation in range | float64 | 2.02–8.174 (μ 4.5362) |
| `rent_resi_n_obs` | Projects within 2.5 km supporting the estimate | int64 | 0.0–5.0 (μ 2.4022) |
| `rent_resolution` | local (≤800 m) / idw / none | object | e.g. none |
| `roi_cap_per_rent_cafe_coffee` | cap_cafe_coffee / rent_resi_psf_med — opportunity per occupancy-cost proxy (rank heuristic). NaN where no rent | float64 | 0.0019–1.1364 (μ 0.2534) |
| `roi_cap_per_rent_supermarket` | cap_supermarket / rent_resi_psf_med — opportunity per occupancy-cost proxy (rank heuristic). NaN where no rent | float64 | 0.0006–0.9534 (μ 0.223) |
| `roi_cap_per_rent_restaurant` | cap_restaurant / rent_resi_psf_med — opportunity per occupancy-cost proxy (rank heuristic). NaN where no rent | float64 | 0.0012–1.1234 (μ 0.3036) |
| `roi_cap_per_rent_shopping_retail` | cap_shopping_retail / rent_resi_psf_med — opportunity per occupancy-cost proxy (rank heuristic). NaN where no rent | float64 | 0.0023–1.2582 (μ 0.3166) |
| `roi_cap_per_rent_total` | cap_total / rent_resi_psf_med — opportunity per occupancy-cost proxy (rank heuristic). NaN where no rent | float64 | 0.0287–11.4337 (μ 2.7839) |
| `rent_hdb_4r_est_pm` | Rent hdb 4r est pm | float64 | 2634.0–5080.0 (μ 3333.9474) |
| `rent_hdb_est_psf` | Rent hdb est psf | float64 | 2.718–5.243 (μ 3.4406) |
| `rent_occ_cost_psf` | Rent occ cost psf | float64 | 2.02–8.174 (μ 4.5238) |
| `rent_occ_cost_source` | Rent occ cost source | object | e.g. none |

## hex9_all_features (597 cols)

| Column | Description | Type | Range/μ or sample |
|---|---|---|---|
| `hex9_id` | H3 resolution-9 cell ID (~0.105 km², 174m edge) | object | e.g. 896520c0007ffff |
| `lat` | Hex centroid latitude | float64 | 1.1594–1.4722 (μ 1.348) |
| `lng` | Hex centroid longitude | float64 | 103.6041–104.0894 (μ 103.8197) |
| `parent_subzone` | URA subzone parent (max-overlap) | object | e.g. TSSZ06 |
| `parent_subzone_name` | URA subzone full name | object | e.g. TUAS VIEW EXTENSION |
| `parent_pa` | URA planning area name (one of 55) | object | e.g. TUAS |
| `parent_region` | URA region (5 regions) | object | e.g. WEST REGION |
| `parent_hex8` | hex-9's parent hex-8 | object | e.g. 886520c001fffff |
| `pop_resident` | Resident population (citizens + PRs) | float64 | 0.0–13216.5004 (μ 571.167) |
| `pop_hdb` | Residents in HDB flats | float64 | 0.0–12604.7757 (μ 433.5462) |
| `pop_non_hdb` | Residents in non-HDB housing | float64 | 0.0–2049.0359 (μ 137.6208) |
| `pop_0_14` | Population age 0-14 | float64 | 0.0–1721.1563 (μ 77.6515) |
| `pop_15_64` | Population age 15-64 | float64 | 0.0–9726.5558 (μ 386.08) |
| `pop_65plus` | Population age 65+ | float64 | 0.0–2091.8286 (μ 107.4355) |
| `pop_hdb_share` | HDB share of resident pop | float64 | 0.0–1.0 (μ 0.1324) |
| `pop_nonresident` | Non-residents (FW + EP + MDW) | float64 | 0.0–30337.0147 (μ 253.7715) |
| `pop_total_all` | Total population (residents + non-residents) | float64 | 0.0–31046.0345 (μ 824.9385) |
| `nonres_share` | Non-resident share of total pop | float64 | 0.0–1.0 (μ 0.3983) |
| `pop_dorm` | Migrant-worker dormitory population at real MOM dorm locations (439,198 national, DASL H2-2024); subset of non-resident | float64 | 0.0–29776.1356 (μ 60.0161) |
| `lu_total_m2` | Total land area covered by URA parcels in hex | float64 | 0.0247–130806.9603 (μ 107229.1221) |
| `lu_residential_pct` | Land area share zoned residential | float64 | 0.0–1.0 (μ 0.149) |
| `lu_mixed_use_pct` | Mixed-use zone share (residential + commercial) | float64 | 0.0–0.6274 (μ 0.0087) |
| `lu_commercial_pct` | Land area share zoned commercial | float64 | 0.0–0.9317 (μ 0.0064) |
| `lu_hotel_pct` | Hotel zone share | float64 | 0.0–0.8988 (μ 0.002) |
| `lu_business_pct` | Land area share zoned business (industrial) | float64 | 0.0–1.0 (μ 0.1619) |
| `lu_business_park_pct` | Business park share | float64 | 0.0–0.8105 (μ 0.0038) |
| `lu_educational_pct` | Educational institution share | float64 | 0.0–1.0 (μ 0.0208) |
| `lu_health_pct` | Health & medical share | float64 | 0.0–0.8857 (μ 0.0026) |
| `lu_institutional_pct` | Civic/community/place-of-worship | float64 | 0.0–1.0 (μ 0.0658) |
| `lu_open_space_pct` | Park / open space share | float64 | 0.0–1.0 (μ 0.2119) |
| `lu_transport_pct` | Transport infra share | float64 | 0.0–1.0 (μ 0.1642) |
| `lu_utility_pct` | Utility infra share | float64 | 0.0–1.0 (μ 0.0208) |
| `lu_water_pct` | Water body share | float64 | 0.0–1.0 (μ 0.0509) |
| `lu_reserve_pct` | Reserve site share | float64 | 0.0–1.0 (μ 0.1313) |
| `lu_other_pct` | Other / unmapped | float64 | 0.0–0.0 (μ 0.0) |
| `lu_entropy` | Shannon entropy across 14 LU buckets | float64 | -0.0–2.0839 (μ 0.5561) |
| `dominant_use` | Bucket with highest area share | object | e.g. transport |
| `avg_gpr` | Area-weighted Gross Plot Ratio | float64 | 0.0–21.9551 (μ 1.0645) |
| `max_gpr` | Max GPR within hex | float64 | 0.0–25.0 (μ 1.207) |
| `lu_parcel_count` | URA parcels intersecting hex | int64 | 1.0–533.0 (μ 22.2861) |
| `bldg_count` | Building footprints in hex (Overture + HDB + OSM) | float64 | 0.0–541.0 (μ 37.3792) |
| `bldg_density_per_km2` | Buildings per km² | float64 | 0.0–5152.381 (μ 355.9924) |
| `bldg_footprint_m2` | Total clipped building footprint area in hex | float64 | 0.0–121282.1725 (μ 14572.8909) |
| `bldg_footprint_share` | Footprint as fraction of hex area (clipped, ≤1) | float64 | 0.0–1.0 (μ 0.1388) |
| `bldg_residential_count` | Residential buildings | float64 | 0.0–474.0 (μ 7.3463) |
| `bldg_commercial_count` | Commercial buildings | float64 | 0.0–87.0 (μ 0.5312) |
| `bldg_industrial_count` | Industrial buildings | float64 | 0.0–71.0 (μ 0.6735) |
| `bldg_institutional_count` | Institutional buildings | float64 | 0.0–27.0 (μ 0.2125) |
| `best_max_floors` | Max floor count (Overture or HDB authoritative) | float64 | 0.0–70.0 (μ 6.7241) |
| `n_highrise_bldgs` | Number of buildings with floors ≥ 10 | float64 | 0.0–474.0 (μ 5.9561) |
| `is_highrise` | True if max_floors >= 10 | bool | e.g. False |
| `est_total_floor_area_m2` | Sum of footprint × est_floors per building | float64 | 0.0–1052737.4234 (μ 78540.4983) |
| `est_built_far` | Estimated built-up FAR = total floor area / hex area | float64 | 0.0–10.0261 (μ 0.748) |
| `hdb_block_count` | HDB blocks (authoritative) | float64 | 0.0–110.0 (μ 1.8292) |
| `hdb_dwelling_units` | Total dwelling units across HDB blocks | float64 | 0.0–10552.568 (μ 159.4102) |
| `hdb_max_floors` | Max HDB floor count | float64 | 0.0–50.0 (μ 4.7178) |
| `hdb_avg_age_years` | Avg years since HDB completion (year_completed filtered ≥1960) | float64 | 0.0–65.0 (μ 6.9391) |
| `road_length_total_m` | Total OSM road length clipped to hex | float64 | 0.0–28457.0027 (μ 3881.8095) |
| `road_density_km_per_km2` | Road km per km² | float64 | 0.0–271.0191 (μ 36.9696) |
| `road_walkable_share` | Pedestrian-only roads as fraction of total | float64 | 0.0–1.0 (μ 0.2861) |
| `road_max_class_through` | Highest road class running through hex | object | e.g. none |
| `road_intersection_density_per_km2` | Vehicle-network nodes with deg ≥ 3 per km² (Jacobs) | float64 | 0.0–1247.619 (μ 192.1459) |
| `dist_expressway_m` | Centroid distance to nearest motorway/trunk segment | float64 | 0.0014–14092.9957 (μ 2849.2223) |
| `near_expressway_exit_400m` | True if motorway_link/trunk_link < 400m (drive-thru flag) | bool | e.g. False |
| `lane_km_per_km2` | Lane-km per km² (lane count × length / area) | float64 | 0.0–147.7497 (μ 26.9232) |
| `oneway_pct` | Fraction of vehicular length that's one-way | float64 | 0.0–1.0 (μ 0.2068) |
| `bridge_length_m` | Bridge segment length | float64 | 0.0–4369.4968 (μ 154.8755) |
| `signalized_crossing_count` | LTA traffic signals in hex | float64 | 0.0–143.0 (μ 6.1379) |
| `parking_lot_count` | OSM amenity=parking points | float64 | 0.0–15.0 (μ 0.4313) |
| `hdb_mscp_count` | Authoritative HDB multi-storey carparks | float64 | 0.0–7.0 (μ 0.1688) |
| `centr_betweenness_max` | Max betweenness centrality of major-road nodes | float64 | 0.0–0.108 (μ 0.0041) |
| `centr_bridge_count` | Tarjan bridge endpoints (network cut points) | float64 | 0.0–31.0 (μ 0.3139) |
| `mrt_station_count` | MRT/LRT stations in hex | float64 | 0.0–3.0 (μ 0.0316) |
| `mrt_exit_count` | MRT exits in hex | float64 | 0.0–10.0 (μ 0.0813) |
| `bus_stop_count` | Bus stops in hex | float64 | 0.0–13.0 (μ 0.7068) |
| `dist_mrt_m` | Centroid distance to nearest MRT/LRT station | float64 | 0.0–14093.879 (μ 2965.8853) |
| `dist_mrt_exit_m` | Centroid distance to nearest MRT exit | float64 | 7.8069–14129.4822 (μ 3042.1028) |
| `dist_bus_m` | Centroid distance to nearest bus stop | float64 | 5.326–13726.348 (μ 1540.2296) |
| `near_mrt_400m` | True if MRT < 400m | bool | e.g. False |
| `near_bus_300m` | True if bus < 300m | bool | e.g. False |
| `rail_line_through_m` | Rail line length through hex (above + underground) | float64 | 0.0–3703.9287 (μ 82.2933) |
| `daily_train_taps` | Daily MRT/LRT taps (Jan 2026 LTA monthly / 31) | float64 | 0.0–221204.1935 (μ 1132.5996) |
| `daily_bus_taps` | Daily bus taps (Dec 2025 LTA monthly / 31) | float64 | 0.0–104185.871 (μ 867.1453) |
| `bus_routes_per_stop_max` | Max # routes serving a stop in hex (GTFS) | float64 | 0.0–50.0 (μ 1.8096) |
| `bus_routes_per_stop_mean` | Mean routes/stop in hex | float64 | 0.0–50.0 (μ 1.4741) |
| `gtfs_headway_am_min` | Best AM-peak headway (lowest minutes between buses) at any stop in hex | float64 | 0.1389–999.0 (μ 703.0503) |
| `is_mrt_interchange` | True if any station has ≥2 lines (slash-PT_CODE) | bool | e.g. False |
| `transit_score` | 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) | float64 | 0.0–0.9879 (μ 0.3431) |
| `ped_path_length_m` | Footway + path + cycleway + steps length | float64 | 0.0–24004.4205 (μ 1747.4614) |
| `ped_path_density_km_per_km2` | Pedestrian-network density | float64 | 0.0–228.6135 (μ 16.6425) |
| `dist_walk_hawker_m` | Walk distance to nearest hawker (Euclidean × 1.3 detour) | float64 | 1.9626–16384.7179 (μ 2493.7523) |
| `dist_walk_clinic_m` | Walk distance to nearest clinic | float64 | 1.6728–16387.5223 (μ 1968.2089) |
| `dist_walk_supermarket_m` | Walk distance to nearest supermarket | float64 | 4.8613–18338.1628 (μ 2327.32) |
| `dist_walk_park_m` | Walk distance to nearest park | float64 | 0.0–20907.396 (μ 3166.6492) |
| `dist_walk_school_m` | Walk distance to nearest school | float64 | 2.1423–16249.3804 (μ 1693.1823) |
| `dist_walk_food_m` | Walk distance to nearest restaurant/cafe/hawker/bakery/fast-food | float64 | 1.9626–16356.8436 (μ 1543.6847) |
| `dist_walk_convenience_m` | Walk distance to nearest convenience store | float64 | 3.6376–14096.1005 (μ 1842.5428) |
| `walk_amenities_400m` | Place count within 400m walk | int64 | 0.0–2111.0 (μ 65.1394) |
| `walk_food_400m` | Food places within 400m walk | int64 | 0.0–491.0 (μ 8.4631) |
| `walk_hawker_400m` | Hawkers within 400m walk | int64 | 0.0–160.0 (μ 1.957) |
| `walk_clinic_400m` | Clinics within 400m walk | int64 | 0.0–321.0 (μ 2.2375) |
| `walk_supermarket_400m` | Supermarkets within 400m walk | int64 | 0.0–42.0 (μ 0.8446) |
| `walk_park_400m` | Parks within 400m walk | int64 | 0.0–10.0 (μ 0.3956) |
| `walk_school_400m` | Schools within 400m walk | int64 | 0.0–131.0 (μ 3.5798) |
| `walk_convenience_400m` | Convenience stores within 400m walk | int64 | 0.0–58.0 (μ 1.957) |
| `expressway_severance` | Expressway < 200m AND no exit < 400m (barrier without benefit) | bool | e.g. False |
| `walkability_score` | Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) | float64 | 0.0–0.9587 (μ 0.3214) |
| `nl_2022` | VIIRS night light radiance 2022 (subzone-broadcast) | float64 | 0.0–153.5743 (μ 43.8436) |
| `nl_2024` | VIIRS night light radiance 2024 (subzone-broadcast) | float64 | 0.0–179.5402 (μ 46.8279) |
| `nl_change_pct` | VIIRS 2022→2024 brightness change | float64 | -28.0109–120.3925 (μ 5.231) |
| `nl_growth_corridor` | True if night light grew ≥ 20% | bool | e.g. False |
| `nl_decline_zone` | True if night light declined ≥ 20% | bool | e.g. False |
| `nl_per_capita` | nl_2024 / pop_resident (commercial vs residential signal) | float64 | 0.0–2.9968 (μ 0.0493) |
| `nl_commercial_indicator` | nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) | float64 | 0.0–167.2595 (μ 36.8024) |
| `wp_pop` | WorldPop count per hex (single snapshot — only one valid TIF available) | float64 | 0.0–16454.5723 (μ 1062.8274) |
| `hdb_resale_in_town` | hdb resale in town (see layer docs) | int64 | 0.0–1.0 (μ 0.2417) |
| `hdb_resale_txns_total` | hdb resale txns total (see layer docs) | float64 | 0.0–18517.0 (μ 2440.2088) |
| `hdb_resale_txns_12m` | hdb resale txns 12m (see layer docs) | float64 | 0.0–1948.0 (μ 276.7991) |
| `hdb_resale_median_price` | hdb resale median price (see layer docs) | float64 | 0.0–760000.0 (μ 122509.7874) |
| `hdb_resale_median_psm` | hdb resale median psm (see layer docs) | float64 | 0.0–7628.866 (μ 1301.0473) |
| `hdb_resale_4r_median_price` | hdb resale 4r median price (see layer docs) | float64 | 0.0–835000.0 (μ 130733.443) |
| `hdb_resale_4r_median_psm` | hdb resale 4r median psm (see layer docs) | float64 | 0.0–9175.2577 (μ 1376.9756) |
| `hdb_resale_12m_median_price` | hdb resale 12m median price (see layer docs) | float64 | 0.0–980000.0 (μ 154680.2662) |
| `hdb_resale_avg_lease_remaining_yrs` | hdb resale avg lease remaining yrs (see layer docs) | float64 | 0.0–89.8692 (μ 17.2898) |
| `school_count_total` | school count total (see layer docs) | int64 | 0.0–3.0 (μ 0.0461) |
| `school_count_primary` | school count primary (see layer docs) | int64 | 0.0–2.0 (μ 0.0249) |
| `school_count_secondary` | school count secondary (see layer docs) | int64 | 0.0–2.0 (μ 0.0182) |
| `school_count_jc` | school count jc (see layer docs) | int64 | 0.0–1.0 (μ 0.003) |
| `school_count_mixed` | school count mixed (see layer docs) | int64 | 0.0–0.0 (μ 0.0) |
| `school_count_premium` | school count premium (see layer docs) | int64 | 0.0–2.0 (μ 0.0056) |
| `nearest_school_dist_m` | Distance to nearest school | float64 | 4.5–15898.9 (μ 3575.8081) |
| `nearest_primary_school_dist_m` | Distance to nearest primary school | float64 | 9.5–16294.1 (μ 3706.8579) |
| `primary_schools_within_1km` | Count of primary schools within 1km | int64 | 0.0–9.0 (μ 0.657) |
| `primary_schools_within_2km` | Count of primary schools within 2km | int64 | 0.0–19.0 (μ 2.5909) |
| `primary_school_zone_count` | Primary-school zones overlapping cell | int64 | 0.0–3.0 (μ 0.0626) |
| `in_primary_school_zone` | Cell intersects a primary-school zone | int64 | 0.0–1.0 (μ 0.0556) |
| `tourist_attraction_count` | tourist attraction count (see layer docs) | int64 | 0.0–5.0 (μ 0.0149) |
| `nearest_tourist_dist_m` | Distance to nearest tourist | float64 | 12.7–15501.7 (μ 4196.4684) |
| `hawker_centre_count` | hawker centre count (see layer docs) | int64 | 0.0–2.0 (μ 0.0176) |
| `nearest_hawker_centre_dist_m` | Distance to nearest hawker centre | float64 | 17.8–16750.7 (μ 3635.0801) |
| `chas_clinic_count` | chas clinic count (see layer docs) | int64 | 0.0–12.0 (μ 0.1629) |
| `nearest_chas_clinic_dist_m` | Distance to nearest chas clinic | float64 | 1.4–14129.1 (μ 2563.7461) |
| `chas_clinics_within_500m` | Count of chas clinics within 500m | int64 | 0.0–22.0 (μ 1.072) |
| `preschool_count` | preschool count (see layer docs) | int64 | 0.0–14.0 (μ 0.3129) |
| `nearest_preschool_dist_m` | Distance to nearest preschool | float64 | 1.3–15998.2 (μ 2983.8749) |
| `preschools_within_400m` | Count of preschools within 400m | int64 | 0.0–25.0 (μ 1.3234) |
| `silver_zone_count` | silver zone count (see layer docs) | int64 | 0.0–2.0 (μ 0.0249) |
| `in_silver_zone` | Cell intersects an elderly-priority Silver Zone | int64 | 0.0–1.0 (μ 0.0243) |
| `ring1_pop_resident` | Sum over H3 ring-1 neighbours (~±1 km) of: Resident population (citizens + PRs) | float64 | 0.0–6591.979 (μ 572.2502) |
| `ring1_pop_nonresident` | Sum over H3 ring-1 neighbours (~±1 km) of: Non-residents (FW + EP + MDW) | float64 | 0.0–5939.589 (μ 255.2309) |
| `ring1_pc_total` | Sum over H3 ring-1 neighbours (~±1 km) of: Total mapped places (POIs) in cell — overall point-of-interest density | float64 | 0.0–812.167 (μ 26.1003) |
| `ring1_pc_magnets` | Sum over H3 ring-1 neighbours (~±1 km) of: High-draw anchor places (malls, hubs, 30+ review demand magnets) | float64 | 0.0–139.0 (μ 2.9544) |
| `ring1_walkability_score` | Sum over H3 ring-1 neighbours (~±1 km) of: Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) | float64 | 0.0–0.934 (μ 0.3232) |
| `ring1_transit_score` | Sum over H3 ring-1 neighbours (~±1 km) of: 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) | float64 | 0.0–0.988 (μ 0.4277) |
| `ring1_nl_2024` | Sum over H3 ring-1 neighbours (~±1 km) of: VIIRS night light radiance 2024 (subzone-broadcast) | float64 | 0.0–160.437 (μ 46.8226) |
| `ring1_hdb_resale_4r_median_psm` | Sum over H3 ring-1 neighbours (~±1 km) of: hdb resale 4r median psm (see layer docs) | float64 | 0.0–9175.258 (μ 1378.4278) |
| `ring1_school_count_total` | Sum over H3 ring-1 neighbours (~±1 km) of: school count total (see layer docs) | float64 | 0.0–6.0 (μ 0.2762) |
| `ring2_pop_resident` | Sum over H3 ring-2 neighbours (~±2 km) of: Resident population (citizens + PRs) | float64 | 0.0–5621.947 (μ 573.3042) |
| `ring2_pop_nonresident` | Sum over H3 ring-2 neighbours (~±2 km) of: Non-residents (FW + EP + MDW) | float64 | 0.0–4970.692 (μ 257.3408) |
| `ring2_pc_total` | Sum over H3 ring-2 neighbours (~±2 km) of: Total mapped places (POIs) in cell — overall point-of-interest density | float64 | 0.0–509.917 (μ 26.1918) |
| `ring2_pc_magnets` | Sum over H3 ring-2 neighbours (~±2 km) of: High-draw anchor places (malls, hubs, 30+ review demand magnets) | float64 | 0.0–80.917 (μ 2.9571) |
| `ring2_walkability_score` | Sum over H3 ring-2 neighbours (~±2 km) of: Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) | float64 | 0.0–0.916 (μ 0.324) |
| `ring2_transit_score` | Sum over H3 ring-2 neighbours (~±2 km) of: 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) | float64 | 0.0–0.988 (μ 0.4868) |
| `ring2_nl_2024` | Sum over H3 ring-2 neighbours (~±2 km) of: VIIRS night light radiance 2024 (subzone-broadcast) | float64 | 0.0–158.585 (μ 46.8003) |
| `ring2_hdb_resale_4r_median_psm` | Sum over H3 ring-2 neighbours (~±2 km) of: hdb resale 4r median psm (see layer docs) | float64 | 0.0–8833.333 (μ 1381.0793) |
| `ring2_school_count_total` | Sum over H3 ring-2 neighbours (~±2 km) of: school count total (see layer docs) | float64 | 0.0–9.0 (μ 0.5522) |
| `vibrancy_index` | Composite: places + magnets + reviews + transit + night lights | float64 | 0.0–0.99 (μ 0.1549) |
| `livability_index` | Composite: walkability + green + amenities + transit | float64 | 0.027–0.977 (μ 0.4285) |
| `commercial_intensity` | Supply/morphology composite: commercial place mix + commercial night-light + commercial land-use share | float64 | 0.0–1.0 (μ 0.0737) |
| `family_index` | Composite: children + schools + preschools + family amenities | float64 | 0.0–0.974 (μ 0.2253) |
| `density_pressure` | Composite: population + buildings + low road space | float64 | 0.0–0.809 (μ 0.1012) |
| `accessibility_composite` | Composite access score across transit + walk + road reach | float64 | 0.0–0.975 (μ 0.2546) |
| `pull_cbd` | Gravity pull toward cbd (distance-decayed attraction) | float64 | 0.0–1.0 (μ 0.1495) |
| `pull_mall` | Gravity pull toward mall (distance-decayed attraction) | float64 | 0.0–1.0 (μ 0.1019) |
| `pull_hospital` | Gravity pull toward hospital (distance-decayed attraction) | float64 | 0.0–1.0 (μ 0.1551) |
| `pull_mrt_interchange` | Gravity pull toward mrt interchange (distance-decayed attraction) | float64 | 0.0–1.0 (μ 0.1117) |
| `pull_school_premium` | Gravity pull toward school premium (distance-decayed attraction) | float64 | 0.0–1.0 (μ 0.235) |
| `pull_airport` | Gravity pull toward airport (distance-decayed attraction) | float64 | 0.0–1.0 (μ 0.3184) |
| `pull_composite` | Gravity pull toward composite (distance-decayed attraction) | float64 | 0.0–0.762 (μ 0.1786) |
| `syn_pop_x_walk` | Synergy interaction term: pop x walk (cross-feature product) | float64 | 0.0–0.93 (μ 0.0708) |
| `syn_pop_x_transit` | Synergy interaction term: pop x transit (cross-feature product) | float64 | 0.0–0.984 (μ 0.0641) |
| `syn_office_x_transit` | Synergy interaction term: office x transit (cross-feature product) | float64 | 0.0–0.987 (μ 0.0288) |
| `syn_retail_x_anchors` | Synergy interaction term: retail x anchors (cross-feature product) | float64 | 0.0–1.0 (μ 0.0185) |
| `syn_density_x_amenities` | Synergy interaction term: density x amenities (cross-feature product) | float64 | 0.0–1.0 (μ 0.0409) |
| `syn_far_x_transit` | Synergy interaction term: far x transit (cross-feature product) | float64 | 0.0–0.0 (μ 0.0) |
| `syn_residential_x_school` | Synergy interaction term: residential x school (cross-feature product) | float64 | 0.0–1.0 (μ 0.0501) |
| `syn_premium_school_x_4r` | Synergy interaction term: premium school x 4r (cross-feature product) | float64 | 0.0–0.0 (μ 0.0) |
| `sat_cafe_coffee_per_1k` | Supply saturation: cafe coffee outlets per 1,000 residents | float64 | 0.0–169.781 (μ 1.2891) |
| `gap_cafe_coffee` | Saturation gap for cafe coffee: actual minus expected per-1k supply (positive = oversupplied) | float64 | -1.0–1.0 (μ 0.9229) |
| `sat_restaurant_per_1k` | Supply saturation: restaurant outlets per 1,000 residents | float64 | 0.0–329.314 (μ 2.6093) |
| `gap_restaurant` | Saturation gap for restaurant: actual minus expected per-1k supply (positive = oversupplied) | float64 | -1.0–1.0 (μ 0.9243) |
| `sat_hawker_per_1k` | Supply saturation: hawker outlets per 1,000 residents | float64 | 0.0–127.329 (μ 0.8005) |
| `gap_hawker` | Saturation gap for hawker: actual minus expected per-1k supply (positive = oversupplied) | float64 | -1.0–1.0 (μ 0.9434) |
| `sat_fast_food_per_1k` | Supply saturation: fast food outlets per 1,000 residents | float64 | 0.0–53.542 (μ 0.2067) |
| `gap_fast_food` | Saturation gap for fast food: actual minus expected per-1k supply (positive = oversupplied) | float64 | -1.0–1.0 (μ 0.9725) |
| `sat_supermarket_per_1k` | Supply saturation: supermarket outlets per 1,000 residents | float64 | 0.0–49.014 (μ 0.4029) |
| `gap_supermarket` | Saturation gap for supermarket: actual minus expected per-1k supply (positive = oversupplied) | float64 | -1.0–1.0 (μ 0.9307) |
| `sat_bakery_per_1k` | Supply saturation: bakery outlets per 1,000 residents | float64 | 0.0–66.693 (μ 0.3362) |
| `gap_bakery` | Saturation gap for bakery: actual minus expected per-1k supply (positive = oversupplied) | float64 | -1.0–1.0 (μ 0.9495) |
| `sat_beauty_personal_per_1k` | Supply saturation: beauty personal outlets per 1,000 residents | float64 | 0.0–196.433 (μ 1.291) |
| `gap_beauty_personal` | Saturation gap for beauty personal: actual minus expected per-1k supply (positive = oversupplied) | float64 | -1.0–1.0 (μ 0.9268) |
| `sat_fitness_recreation_per_1k` | Supply saturation: fitness recreation outlets per 1,000 residents | float64 | 0.0–59.537 (μ 0.6573) |
| `gap_fitness_recreation` | Saturation gap for fitness recreation: actual minus expected per-1k supply (positive = oversupplied) | float64 | -1.0–1.0 (μ 0.9057) |
| `sat_health_medical_per_1k` | Supply saturation: health medical outlets per 1,000 residents | float64 | 0.0–174.343 (μ 1.2733) |
| `gap_health_medical` | Saturation gap for health medical: actual minus expected per-1k supply (positive = oversupplied) | float64 | -1.0–1.0 (μ 0.9305) |
| `archetype_id` | k-means (K=8) urban archetype cluster id | int64 | 0.0–7.0 (μ 4.0353) |
| `archetype_label` | Human label of the archetype cluster | object | e.g. CBD_office |
| `archetype_dist` | Distance to archetype centroid (typicality) | float64 | 0.081–28.445 (μ 1.8582) |
| `outbound_influence` | Gravity-decayed influence the cell exerts on neighbours (hex9 influence model) | float64 | 0.0–1.0 (μ 0.4325) |
| `inbound_influence` | Gravity-decayed influence neighbours exert on the cell (hex9 influence model) | float64 | 0.0–1.0 (μ 0.1372) |
| `net_influence` | Outbound minus inbound influence (hex9 influence model) | float64 | 0.0–1.0 (μ 0.5816) |
| `walk_mrt_score` | Walk-access score to nearest mrt (distance-decayed) | float64 | 0.0–1.0 (μ 0.1372) |
| `walk_bus_score` | Walk-access score to nearest bus (distance-decayed) | float64 | 0.0–0.987 (μ 0.3588) |
| `walk_school_score` | Walk-access score to nearest school (distance-decayed) | float64 | 0.0–0.995 (μ 0.2768) |
| `walk_clinic_score` | Walk-access score to nearest clinic (distance-decayed) | float64 | 0.0–0.996 (μ 0.2161) |
| `walk_hawker_score` | Walk-access score to nearest hawker (distance-decayed) | float64 | 0.0–0.995 (μ 0.1816) |
| `walk_supermarket_score` | Walk-access score to nearest supermarket (distance-decayed) | float64 | 0.0–0.988 (μ 0.2043) |
| `walk_park_score` | Walk-access score to nearest park (distance-decayed) | float64 | 0.0–1.0 (μ 0.2391) |
| `walk_food_score` | Walk-access score to nearest food (distance-decayed) | float64 | 0.0–0.995 (μ 0.3008) |
| `walk_convenience_score` | Walk-access score to nearest convenience (distance-decayed) | float64 | 0.0–0.991 (μ 0.2647) |
| `walk_score_avg` | Mean of the 9 amenity walk-access scores | float64 | 0.0–0.933 (μ 0.2422) |
| `osm_amenities_count` | OSM amenity-tagged POIs in cell (independent ground truth) | int64 | 0.0–229.0 (μ 3.9471) |
| `osm_leisure_count` | OSM leisure-tagged POIs in cell | int64 | 0.0–68.0 (μ 1.7152) |
| `osm_shops_count` | OSM shop-tagged POIs in cell — independent retail frontage | int64 | 0.0–161.0 (μ 1.1843) |
| `osm_tourism_count` | OSM tourism-tagged POIs in cell | int64 | 0.0–73.0 (μ 0.3606) |
| `wc_tree_share` | ESA WorldCover land-cover share: tree share | float64 | 0.0–1.0 (μ 0.3046) |
| `wc_built_share` | ESA WorldCover land-cover share: built share | float64 | 0.0–1.0 (μ 0.3596) |
| `wc_water_share` | ESA WorldCover land-cover share: water share | float64 | 0.0–1.0 (μ 0.193) |
| `wc_grass_share` | ESA WorldCover land-cover share: grass share | float64 | 0.0–1.0 (μ 0.0961) |
| `wc_other_share` | ESA WorldCover land-cover share: other share | float64 | 0.0–1.0 (μ 0.0467) |
| `wc_dominant_class` | ESA WorldCover land-cover share: dominant class | int64 | 10.0–95.0 (μ 43.8446) |
| `sig_total` | Road-network metric: sig total | int64 | 0.0–143.0 (μ 6.1379) |
| `sig_overhead` | Road-network metric: sig overhead | int64 | 0.0–14.0 (μ 0.6481) |
| `sig_ground` | Road-network metric: sig ground | int64 | 0.0–51.0 (μ 2.3073) |
| `sig_pedestrian` | Road-network metric: sig pedestrian | int64 | 0.0–48.0 (μ 1.7696) |
| `sig_beacon` | Road-network metric: sig beacon | int64 | 0.0–20.0 (μ 0.7398) |
| `sig_rag` | Road-network metric: sig rag | int64 | 0.0–24.0 (μ 0.276) |
| `sig_filter_arrow` | Road-network metric: sig filter arrow | int64 | 0.0–22.0 (μ 0.361) |
| `sig_bicycle` | Road-network metric: sig bicycle | int64 | 0.0–4.0 (μ 0.0044) |
| `ped_countdown` | Road-network metric: ped countdown | int64 | 0.0–17.0 (μ 0.2117) |
| `gtfs_headway_midday_min` | GTFS-derived transit service metric: headway midday min (weekday schedule) | float64 | 0.1–999.0 (μ 696.5264) |
| `gtfs_headway_pm_min` | GTFS-derived transit service metric: headway pm min (weekday schedule) | float64 | 0.1–999.0 (μ 696.36) |
| `gtfs_headway_night_min` | GTFS-derived transit service metric: headway night min (weekday schedule) | float64 | 0.3–999.0 (μ 701.0777) |
| `gtfs_dep_am` | GTFS-derived transit service metric: dep am (weekday schedule) | int64 | 0.0–1229.0 (μ 39.279) |
| `gtfs_dep_midday` | GTFS-derived transit service metric: dep midday (weekday schedule) | int64 | 0.0–1739.0 (μ 56.7124) |
| `gtfs_dep_pm` | GTFS-derived transit service metric: dep pm (weekday schedule) | int64 | 0.0–1173.0 (μ 38.603) |
| `gtfs_dep_night` | GTFS-derived transit service metric: dep night (weekday schedule) | int64 | 0.0–1383.0 (μ 41.0123) |
| `gtfs_daily_departures` | GTFS-derived transit service metric: daily departures (weekday schedule) | int64 | 0.0–10671.0 (μ 345.6678) |
| `gtfs_routes_served` | GTFS-derived transit service metric: routes served (weekday schedule) | int64 | 0.0–94.0 (μ 3.5551) |
| `gtfs_stops_with_service` | GTFS-derived transit service metric: stops with service (weekday schedule) | int64 | 0.0–12.0 (μ 0.7244) |
| `bus_taps_in_am` | Daily bus tap-ins in the am time window (LTA PV) | int64 | 0.0–178119.0 (μ 1747.2389) |
| `bus_taps_in_midday` | Daily bus tap-ins in the midday time window (LTA PV) | int64 | 0.0–130378.0 (μ 1451.7081) |
| `bus_taps_in_night` | Daily bus tap-ins in the night time window (LTA PV) | int64 | 0.0–74447.0 (μ 440.7605) |
| `bus_taps_in_offpeak` | Daily bus tap-ins in the offpeak time window (LTA PV) | int64 | 0.0–556162.0 (μ 4637.5533) |
| `bus_taps_in_pm` | Daily bus tap-ins in the pm time window (LTA PV) | int64 | 0.0–223966.0 (μ 1712.5437) |
| `bus_taps_out_am` | Daily bus tap-outs in the am time window (LTA PV) | int64 | 0.0–185062.0 (μ 1800.0306) |
| `bus_taps_out_midday` | Daily bus tap-outs in the midday time window (LTA PV) | int64 | 0.0–153312.0 (μ 1420.6358) |
| `bus_taps_out_night` | Daily bus tap-outs in the night time window (LTA PV) | int64 | 0.0–41644.0 (μ 512.5473) |
| `bus_taps_out_offpeak` | Daily bus tap-outs in the offpeak time window (LTA PV) | int64 | 0.0–463572.0 (μ 4644.0413) |
| `bus_taps_out_pm` | Daily bus tap-outs in the pm time window (LTA PV) | int64 | 0.0–178666.0 (μ 1656.4544) |
| `bus_taps_in_total` | Daily bus tap-ins in the total time window (LTA PV) | int64 | 0.0–1161327.0 (μ 9989.8045) |
| `bus_taps_out_total` | Daily bus tap-outs in the total time window (LTA PV) | int64 | 0.0–982501.0 (μ 10033.7093) |
| `carpark_count_avail` | carpark count avail (see layer docs) | int64 | 0.0–16.0 (μ 0.3542) |
| `carpark_lots_avail` | carpark lots avail (see layer docs) | int64 | 0.0–3336.0 (μ 70.0689) |
| `speed_band_count` | speed band count (see layer docs) | int64 | 0.0–119.0 (μ 7.7596) |
| `speed_band_avg` | speed band avg (see layer docs) | float64 | 0.0–8.0 (μ 1.9965) |
| `jam_pct` | jam pct (see layer docs) | float64 | 0.0–100.0 (μ 10.9946) |
| `dyn_avg_speed_kmh` | dyn avg speed kmh (see layer docs) | float64 | 0.0–74.0 (μ 17.0314) |
| `pw1_pc_total` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Total mapped places (POIs) in cell — overall point-of-interest density | float64 | 0.0–796.154 (μ 27.3161) |
| `pw1_pc_magnets` | Proximity-weighted (distance-decayed) ring-1 aggregate of: High-draw anchor places (malls, hubs, 30+ review demand magnets) | float64 | 0.0–147.857 (μ 3.0099) |
| `pw1_pc_unique_brands` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Distinct retail/F&B brands present — chain richness | float64 | 0.0–50.731 (μ 2.1786) |
| `pw1_pc_cat_business_office` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: business office category (24-cat taxonomy) | float64 | 0.0–162.085 (μ 2.2215) |
| `pw1_pc_cat_shopping_retail` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: shopping retail category (24-cat taxonomy) | float64 | 0.0–111.493 (μ 2.0249) |
| `pw1_pc_cat_hawker` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: hawker category (24-cat taxonomy) | float64 | 0.0–55.38 (μ 1.1452) |
| `pw1_pc_cat_residential` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: residential category (24-cat taxonomy) | float64 | 0.0–25.561 (μ 3.2234) |
| `pw1_pc_cat_industrial_mfg` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: industrial mfg category (24-cat taxonomy) | float64 | 0.0–98.817 (μ 1.6578) |
| `pw1_pc_cat_cafe_coffee` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: cafe coffee category (24-cat taxonomy) | float64 | 0.0–33.772 (μ 1.0475) |
| `pw1_pc_cat_restaurant` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: restaurant category (24-cat taxonomy) | float64 | 0.0–86.452 (μ 1.6448) |
| `pw1_pc_cat_education` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: education category (24-cat taxonomy) | float64 | 0.0–43.891 (μ 1.7915) |
| `pw1_pc_cat_health_medical` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: health medical category (24-cat taxonomy) | float64 | 0.0–73.256 (μ 1.1974) |
| `pw1_transit_score` | Proximity-weighted (distance-decayed) ring-1 aggregate of: 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) | float64 | 0.0–0.962 (μ 0.2933) |
| `pw1_walkability_score` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) | float64 | 0.0–0.934 (μ 0.2995) |
| `pw1_nl_2024` | Proximity-weighted (distance-decayed) ring-1 aggregate of: VIIRS night light radiance 2024 (subzone-broadcast) | float64 | 0.0–167.313 (μ 29.9905) |
| `pw1_nl_commercial_indicator` | Proximity-weighted (distance-decayed) ring-1 aggregate of: nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) | float64 | 0.0–163.215 (μ 16.1521) |
| `pw1_hdb_resale_4r_median_psm` | Proximity-weighted (distance-decayed) ring-1 aggregate of: hdb resale 4r median psm (see layer docs) | float64 | 0.0–9175.258 (μ 1597.3413) |
| `pw1_primary_schools_within_1km` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Count of primary schools within 1km | float64 | 0.0–7.369 (μ 0.7271) |
| `pw1_preschools_within_400m` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Count of preschools within 400m | float64 | 0.0–17.719 (μ 1.661) |
| `pw1_chas_clinic_count` | Proximity-weighted (distance-decayed) ring-1 aggregate of: chas clinic count (see layer docs) | float64 | 0.0–4.642 (μ 0.2309) |
| `pw1_hawker_centre_count` | Proximity-weighted (distance-decayed) ring-1 aggregate of: hawker centre count (see layer docs) | float64 | 0.0–1.758 (μ 0.0288) |
| `pw1_tourist_attraction_count` | Proximity-weighted (distance-decayed) ring-1 aggregate of: tourist attraction count (see layer docs) | float64 | 0.0–3.437 (μ 0.0126) |
| `pw1_vibrancy_index` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Composite: places + magnets + reviews + transit + night lights | float64 | 0.0–0.963 (μ 0.1261) |
| `pw1_commercial_intensity` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Supply/morphology composite: commercial place mix + commercial night-light + commercial land-use share | float64 | 0.0–0.9 (μ 0.0533) |
| `pw1_family_index` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Composite: children + schools + preschools + family amenities | float64 | 0.0–0.925 (μ 0.2213) |
| `pw1_density_pressure` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Composite: population + buildings + low road space | float64 | 0.0–0.729 (μ 0.1164) |
| `pw1_pull_cbd` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Gravity pull toward cbd (distance-decayed attraction) | float64 | 0.0–0.985 (μ 0.1197) |
| `pw1_pull_mall` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Gravity pull toward mall (distance-decayed attraction) | float64 | 0.0–0.971 (μ 0.0895) |
| `pw1_pull_mrt_interchange` | Proximity-weighted (distance-decayed) ring-1 aggregate of: Gravity pull toward mrt interchange (distance-decayed attraction) | float64 | 0.0–0.984 (μ 0.0987) |
| `pw1_wc_built_share` | Proximity-weighted (distance-decayed) ring-1 aggregate of: ESA WorldCover land-cover share: built share | float64 | 0.0–0.991 (μ 0.2923) |
| `pw1_wc_tree_share` | Proximity-weighted (distance-decayed) ring-1 aggregate of: ESA WorldCover land-cover share: tree share | float64 | 0.0–1.0 (μ 0.1918) |
| `max1_pc_total` | Max over ring-1 neighbours of: Total mapped places (POIs) in cell — overall point-of-interest density | float64 | 0.0–1215.0 (μ 64.201) |
| `max1_pc_magnets` | Max over ring-1 neighbours of: High-draw anchor places (malls, hubs, 30+ review demand magnets) | float64 | 0.0–266.0 (μ 9.3639) |
| `max1_pc_unique_brands` | Max over ring-1 neighbours of: Distinct retail/F&B brands present — chain richness | float64 | 0.0–96.0 (μ 5.5864) |
| `max1_pc_cat_business_office` | Max over ring-1 neighbours of: Place count in cell: business office category (24-cat taxonomy) | float64 | 0.0–324.0 (μ 8.6845) |
| `max1_pc_cat_shopping_retail` | Max over ring-1 neighbours of: Place count in cell: shopping retail category (24-cat taxonomy) | float64 | 0.0–251.0 (μ 6.9477) |
| `max1_pc_cat_hawker` | Max over ring-1 neighbours of: Place count in cell: hawker category (24-cat taxonomy) | float64 | 0.0–96.0 (μ 3.3873) |
| `max1_pc_cat_residential` | Max over ring-1 neighbours of: Place count in cell: residential category (24-cat taxonomy) | float64 | 0.0–33.0 (μ 4.7973) |
| `max1_pc_cat_industrial_mfg` | Max over ring-1 neighbours of: Place count in cell: industrial mfg category (24-cat taxonomy) | float64 | 0.0–148.0 (μ 7.2574) |
| `max1_pc_cat_cafe_coffee` | Max over ring-1 neighbours of: Place count in cell: cafe coffee category (24-cat taxonomy) | float64 | 0.0–51.0 (μ 2.89) |
| `max1_pc_cat_restaurant` | Max over ring-1 neighbours of: Place count in cell: restaurant category (24-cat taxonomy) | float64 | 0.0–112.0 (μ 4.9482) |
| `max1_pc_cat_education` | Max over ring-1 neighbours of: Place count in cell: education category (24-cat taxonomy) | float64 | 0.0–78.0 (μ 4.1923) |
| `max1_pc_cat_health_medical` | Max over ring-1 neighbours of: Place count in cell: health medical category (24-cat taxonomy) | float64 | 0.0–248.0 (μ 3.4664) |
| `max1_transit_score` | Max over ring-1 neighbours of: 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) | float64 | 0.0–0.988 (μ 0.4277) |
| `max1_walkability_score` | Max over ring-1 neighbours of: Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) | float64 | 0.0–0.959 (μ 0.4614) |
| `max1_nl_2024` | Max over ring-1 neighbours of: VIIRS night light radiance 2024 (subzone-broadcast) | float64 | 0.0–179.54 (μ 52.2798) |
| `max1_nl_commercial_indicator` | Max over ring-1 neighbours of: nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) | float64 | 0.0–167.26 (μ 44.2612) |
| `max1_hdb_resale_4r_median_psm` | Max over ring-1 neighbours of: hdb resale 4r median psm (see layer docs) | float64 | 0.0–9175.258 (μ 1921.0803) |
| `max1_primary_schools_within_1km` | Max over ring-1 neighbours of: Count of primary schools within 1km | float64 | 0.0–9.0 (μ 1.0097) |
| `max1_preschools_within_400m` | Max over ring-1 neighbours of: Count of preschools within 400m | float64 | 0.0–25.0 (μ 2.5655) |
| `max1_chas_clinic_count` | Max over ring-1 neighbours of: chas clinic count (see layer docs) | float64 | 0.0–12.0 (μ 0.6129) |
| `max1_hawker_centre_count` | Max over ring-1 neighbours of: hawker centre count (see layer docs) | float64 | 0.0–2.0 (μ 0.0902) |
| `max1_tourist_attraction_count` | Max over ring-1 neighbours of: tourist attraction count (see layer docs) | float64 | 0.0–5.0 (μ 0.0589) |
| `max1_vibrancy_index` | Max over ring-1 neighbours of: Composite: places + magnets + reviews + transit + night lights | float64 | 0.0–0.99 (μ 0.2176) |
| `max1_commercial_intensity` | Max over ring-1 neighbours of: Supply/morphology composite: commercial place mix + commercial night-light + commercial land-use share | float64 | 0.0–1.0 (μ 0.1371) |
| `max1_family_index` | Max over ring-1 neighbours of: Composite: children + schools + preschools + family amenities | float64 | 0.0–0.974 (μ 0.3186) |
| `max1_density_pressure` | Max over ring-1 neighbours of: Composite: population + buildings + low road space | float64 | 0.0–0.809 (μ 0.1912) |
| `max1_pull_cbd` | Max over ring-1 neighbours of: Gravity pull toward cbd (distance-decayed attraction) | float64 | 0.0–1.0 (μ 0.1586) |
| `max1_pull_mall` | Max over ring-1 neighbours of: Gravity pull toward mall (distance-decayed attraction) | float64 | 0.0–1.0 (μ 0.1114) |
| `max1_pull_mrt_interchange` | Max over ring-1 neighbours of: Gravity pull toward mrt interchange (distance-decayed attraction) | float64 | 0.0–1.0 (μ 0.1235) |
| `max1_wc_built_share` | Max over ring-1 neighbours of: ESA WorldCover land-cover share: built share | float64 | 0.0–1.0 (μ 0.5591) |
| `max1_wc_tree_share` | Max over ring-1 neighbours of: ESA WorldCover land-cover share: tree share | float64 | 0.0–1.0 (μ 0.518) |
| `pw2_pc_total` | Proximity-weighted ring-2 aggregate of: Total mapped places (POIs) in cell — overall point-of-interest density | float64 | 0.0–734.091 (μ 31.2474) |
| `pw2_pc_magnets` | Proximity-weighted ring-2 aggregate of: High-draw anchor places (malls, hubs, 30+ review demand magnets) | float64 | 0.0–127.86 (μ 3.3156) |
| `pw2_pc_unique_brands` | Proximity-weighted ring-2 aggregate of: Distinct retail/F&B brands present — chain richness | float64 | 0.0–40.115 (μ 2.6181) |
| `pw2_pc_cat_business_office` | Proximity-weighted ring-2 aggregate of: Place count in cell: business office category (24-cat taxonomy) | float64 | 0.0–162.703 (μ 2.2632) |
| `pw2_pc_cat_shopping_retail` | Proximity-weighted ring-2 aggregate of: Place count in cell: shopping retail category (24-cat taxonomy) | float64 | 0.0–83.119 (μ 2.1897) |
| `pw2_pc_cat_hawker` | Proximity-weighted ring-2 aggregate of: Place count in cell: hawker category (24-cat taxonomy) | float64 | 0.0–47.026 (μ 1.4158) |
| `pw2_pc_cat_residential` | Proximity-weighted ring-2 aggregate of: Place count in cell: residential category (24-cat taxonomy) | float64 | 0.0–24.181 (μ 4.0476) |
| `pw2_pc_cat_industrial_mfg` | Proximity-weighted ring-2 aggregate of: Place count in cell: industrial mfg category (24-cat taxonomy) | float64 | 0.0–84.21 (μ 1.6767) |
| `pw2_pc_cat_cafe_coffee` | Proximity-weighted ring-2 aggregate of: Place count in cell: cafe coffee category (24-cat taxonomy) | float64 | 0.0–28.866 (μ 1.2401) |
| `pw2_pc_cat_restaurant` | Proximity-weighted ring-2 aggregate of: Place count in cell: restaurant category (24-cat taxonomy) | float64 | 0.0–75.025 (μ 1.8615) |
| `pw2_pc_cat_education` | Proximity-weighted ring-2 aggregate of: Place count in cell: education category (24-cat taxonomy) | float64 | 0.0–38.489 (μ 2.1083) |
| `pw2_pc_cat_health_medical` | Proximity-weighted ring-2 aggregate of: Place count in cell: health medical category (24-cat taxonomy) | float64 | 0.0–46.309 (μ 1.3976) |
| `pw2_transit_score` | Proximity-weighted ring-2 aggregate of: 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) | float64 | 0.0–0.925 (μ 0.3256) |
| `pw2_walkability_score` | Proximity-weighted ring-2 aggregate of: Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) | float64 | 0.0–0.928 (μ 0.3382) |
| `pw2_nl_2024` | Proximity-weighted ring-2 aggregate of: VIIRS night light radiance 2024 (subzone-broadcast) | float64 | 0.0–165.732 (μ 33.0311) |
| `pw2_nl_commercial_indicator` | Proximity-weighted ring-2 aggregate of: nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) | float64 | 0.0–158.471 (μ 16.1838) |
| `pw2_hdb_resale_4r_median_psm` | Proximity-weighted ring-2 aggregate of: hdb resale 4r median psm (see layer docs) | float64 | 0.0–9020.329 (μ 1909.1035) |
| `pw2_primary_schools_within_1km` | Proximity-weighted ring-2 aggregate of: Count of primary schools within 1km | float64 | 0.0–7.053 (μ 0.8642) |
| `pw2_preschools_within_400m` | Proximity-weighted ring-2 aggregate of: Count of preschools within 400m | float64 | 0.0–16.684 (μ 2.0434) |
| `pw2_chas_clinic_count` | Proximity-weighted ring-2 aggregate of: chas clinic count (see layer docs) | float64 | 0.0–4.189 (μ 0.2923) |
| `pw2_hawker_centre_count` | Proximity-weighted ring-2 aggregate of: hawker centre count (see layer docs) | float64 | 0.0–1.541 (μ 0.0369) |
| `pw2_tourist_attraction_count` | Proximity-weighted ring-2 aggregate of: tourist attraction count (see layer docs) | float64 | 0.0–2.487 (μ 0.012) |
| `pw2_vibrancy_index` | Proximity-weighted ring-2 aggregate of: Composite: places + magnets + reviews + transit + night lights | float64 | 0.0–0.947 (μ 0.1402) |
| `pw2_commercial_intensity` | Proximity-weighted ring-2 aggregate of: Supply/morphology composite: commercial place mix + commercial night-light + commercial land-use share | float64 | 0.0–0.876 (μ 0.0577) |
| `pw2_family_index` | Proximity-weighted ring-2 aggregate of: Composite: children + schools + preschools + family amenities | float64 | 0.0–0.917 (μ 0.2541) |
| `pw2_density_pressure` | Proximity-weighted ring-2 aggregate of: Composite: population + buildings + low road space | float64 | 0.0–0.722 (μ 0.1422) |
| `pw2_pull_cbd` | Proximity-weighted ring-2 aggregate of: Gravity pull toward cbd (distance-decayed attraction) | float64 | 0.0–0.973 (μ 0.1283) |
| `pw2_pull_mall` | Proximity-weighted ring-2 aggregate of: Gravity pull toward mall (distance-decayed attraction) | float64 | 0.0–0.945 (μ 0.0955) |
| `pw2_pull_mrt_interchange` | Proximity-weighted ring-2 aggregate of: Gravity pull toward mrt interchange (distance-decayed attraction) | float64 | 0.0–0.968 (μ 0.1061) |
| `pw2_wc_built_share` | Proximity-weighted ring-2 aggregate of: ESA WorldCover land-cover share: built share | float64 | 0.0–0.978 (μ 0.332) |
| `pw2_wc_tree_share` | Proximity-weighted ring-2 aggregate of: ESA WorldCover land-cover share: tree share | float64 | 0.0–1.0 (μ 0.1999) |
| `max2_pc_total` | Max over ring-2 neighbours of: Total mapped places (POIs) in cell — overall point-of-interest density | float64 | 0.0–1215.0 (μ 93.8101) |
| `max2_pc_magnets` | Max over ring-2 neighbours of: High-draw anchor places (malls, hubs, 30+ review demand magnets) | float64 | 0.0–266.0 (μ 14.8715) |
| `max2_pc_unique_brands` | Max over ring-2 neighbours of: Distinct retail/F&B brands present — chain richness | float64 | 0.0–96.0 (μ 8.7282) |
| `max2_pc_cat_business_office` | Max over ring-2 neighbours of: Place count in cell: business office category (24-cat taxonomy) | float64 | 0.0–324.0 (μ 13.8461) |
| `max2_pc_cat_shopping_retail` | Max over ring-2 neighbours of: Place count in cell: shopping retail category (24-cat taxonomy) | float64 | 0.0–251.0 (μ 11.0354) |
| `max2_pc_cat_hawker` | Max over ring-2 neighbours of: Place count in cell: hawker category (24-cat taxonomy) | float64 | 0.0–96.0 (μ 5.515) |
| `max2_pc_cat_residential` | Max over ring-2 neighbours of: Place count in cell: residential category (24-cat taxonomy) | float64 | 0.0–33.0 (μ 6.5779) |
| `max2_pc_cat_industrial_mfg` | Max over ring-2 neighbours of: Place count in cell: industrial mfg category (24-cat taxonomy) | float64 | 0.0–148.0 (μ 11.501) |
| `max2_pc_cat_cafe_coffee` | Max over ring-2 neighbours of: Place count in cell: cafe coffee category (24-cat taxonomy) | float64 | 0.0–51.0 (μ 4.4209) |
| `max2_pc_cat_restaurant` | Max over ring-2 neighbours of: Place count in cell: restaurant category (24-cat taxonomy) | float64 | 0.0–112.0 (μ 7.7167) |
| `max2_pc_cat_education` | Max over ring-2 neighbours of: Place count in cell: education category (24-cat taxonomy) | float64 | 0.0–78.0 (μ 6.2282) |
| `max2_pc_cat_health_medical` | Max over ring-2 neighbours of: Place count in cell: health medical category (24-cat taxonomy) | float64 | 0.0–248.0 (μ 5.5212) |
| `max2_transit_score` | Max over ring-2 neighbours of: 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) | float64 | 0.0–0.988 (μ 0.4868) |
| `max2_walkability_score` | Max over ring-2 neighbours of: Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) | float64 | 0.0–0.959 (μ 0.5316) |
| `max2_nl_2024` | Max over ring-2 neighbours of: VIIRS night light radiance 2024 (subzone-broadcast) | float64 | 0.0–179.54 (μ 57.3556) |
| `max2_nl_commercial_indicator` | Max over ring-2 neighbours of: nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) | float64 | 0.0–167.26 (μ 49.7915) |
| `max2_hdb_resale_4r_median_psm` | Max over ring-2 neighbours of: hdb resale 4r median psm (see layer docs) | float64 | 0.0–9175.258 (μ 2362.8734) |
| `max2_primary_schools_within_1km` | Max over ring-2 neighbours of: Count of primary schools within 1km | float64 | 0.0–9.0 (μ 1.3254) |
| `max2_preschools_within_400m` | Max over ring-2 neighbours of: Count of preschools within 400m | float64 | 0.0–25.0 (μ 3.5709) |
| `max2_chas_clinic_count` | Max over ring-2 neighbours of: chas clinic count (see layer docs) | float64 | 0.0–12.0 (μ 0.9662) |
| `max2_hawker_centre_count` | Max over ring-2 neighbours of: hawker centre count (see layer docs) | float64 | 0.0–2.0 (μ 0.157) |
| `max2_tourist_attraction_count` | Max over ring-2 neighbours of: tourist attraction count (see layer docs) | float64 | 0.0–5.0 (μ 0.0992) |
| `max2_vibrancy_index` | Max over ring-2 neighbours of: Composite: places + magnets + reviews + transit + night lights | float64 | 0.0–0.99 (μ 0.2661) |
| `max2_commercial_intensity` | Max over ring-2 neighbours of: Supply/morphology composite: commercial place mix + commercial night-light + commercial land-use share | float64 | 0.0–1.0 (μ 0.1837) |
| `max2_family_index` | Max over ring-2 neighbours of: Composite: children + schools + preschools + family amenities | float64 | 0.0–0.974 (μ 0.3786) |
| `max2_density_pressure` | Max over ring-2 neighbours of: Composite: population + buildings + low road space | float64 | 0.0–0.809 (μ 0.2504) |
| `max2_pull_cbd` | Max over ring-2 neighbours of: Gravity pull toward cbd (distance-decayed attraction) | float64 | 0.0–1.0 (μ 0.168) |
| `max2_pull_mall` | Max over ring-2 neighbours of: Gravity pull toward mall (distance-decayed attraction) | float64 | 0.0–1.0 (μ 0.1214) |
| `max2_pull_mrt_interchange` | Max over ring-2 neighbours of: Gravity pull toward mrt interchange (distance-decayed attraction) | float64 | 0.0–1.0 (μ 0.1359) |
| `max2_wc_built_share` | Max over ring-2 neighbours of: ESA WorldCover land-cover share: built share | float64 | 0.0–1.0 (μ 0.653) |
| `max2_wc_tree_share` | Max over ring-2 neighbours of: ESA WorldCover land-cover share: tree share | float64 | 0.0–1.0 (μ 0.6274) |
| `cap_cafe_coffee` | Huff capture for a NEW cafe_coffee outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) | float64 | 0.0–3.9242 (μ 0.5417) |
| `cap_restaurant` | Huff capture for a NEW restaurant outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) | float64 | 0.0–3.7734 (μ 0.7137) |
| `cap_hawker` | Huff capture for a NEW hawker outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) | float64 | 0.0–4.9628 (μ 0.5444) |
| `cap_fast_food` | Huff capture for a NEW fast_food outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) | float64 | 0.0–2.1472 (μ 0.4473) |
| `cap_supermarket` | Huff capture for a NEW supermarket outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) | float64 | 0.0–3.206 (μ 0.467) |
| `cap_convenience` | Huff capture for a NEW convenience outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) | float64 | 0.0–4.0129 (μ 0.4901) |
| `cap_fitness_recreation` | Huff capture for a NEW fitness_recreation outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) | float64 | 0.0–3.5699 (μ 0.5689) |
| `cap_health_medical` | Huff capture for a NEW health_medical outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) | float64 | 0.0–4.4454 (μ 0.5853) |
| `cap_beauty_personal` | Huff capture for a NEW beauty_personal outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) | float64 | 0.0–3.9384 (μ 0.5779) |
| `cap_shopping_retail` | Huff capture for a NEW shopping_retail outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) | float64 | 0.0–4.2264 (μ 0.7594) |
| `cap_education` | Huff capture for a NEW education outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) | float64 | 0.0–2.4924 (μ 0.491) |
| `cap_total` | Sum of per-category Huff capture: demand (outlet-equivalents) a NEW outlet at the best hex9 in this hex would win vs existing competition. λ ASSUMED (500/700/1000/1500m priors; not identifiable from data — rankings λ-robust ρ≥0.83) | float64 | 0.0–38.4057 (μ 6.1866) |
| `cap_best_category` | Category with the highest capture at this hex | object | e.g. cafe_coffee |
| `pc2_total` | Fine-taxonomy place metric: total | int64 | 0.0–1215.0 (μ 26.0398) |
| `pc2_branded_count` | Fine-taxonomy place metric: branded count | int64 | 0.0–123.0 (μ 2.0671) |
| `pc2_unbranded_count` | Fine-taxonomy place metric: unbranded count | int64 | 0.0–1189.0 (μ 23.9727) |
| `pc2_cat_biz_office_count` | Place count in cell: biz office (55-cat fine taxonomy) | int64 | 0.0–109.0 (μ 0.6152) |
| `pc2_cat_civic_community_count` | Place count in cell: civic community (55-cat fine taxonomy) | int64 | 0.0–7.0 (μ 0.0862) |
| `pc2_cat_civic_government_count` | Place count in cell: civic government (55-cat fine taxonomy) | int64 | 0.0–23.0 (μ 0.1509) |
| `pc2_cat_civic_nonprofit_count` | Place count in cell: civic nonprofit (55-cat fine taxonomy) | int64 | 0.0–20.0 (μ 0.3291) |
| `pc2_cat_civic_religious_count` | Place count in cell: civic religious (55-cat fine taxonomy) | int64 | 0.0–18.0 (μ 0.1571) |
| `pc2_cat_edu_preschool_count` | Place count in cell: edu preschool (55-cat fine taxonomy) | int64 | 0.0–14.0 (μ 0.3605) |
| `pc2_cat_edu_primary_secondary_count` | Place count in cell: edu primary secondary (55-cat fine taxonomy) | int64 | 0.0–23.0 (μ 0.1604) |
| `pc2_cat_edu_specialty_count` | Place count in cell: edu specialty (55-cat fine taxonomy) | int64 | 0.0–5.0 (μ 0.0322) |
| `pc2_cat_edu_tertiary_count` | Place count in cell: edu tertiary (55-cat fine taxonomy) | int64 | 0.0–15.0 (μ 0.0558) |
| `pc2_cat_edu_tuition_count` | Place count in cell: edu tuition (55-cat fine taxonomy) | int64 | 0.0–59.0 (μ 0.7025) |
| `pc2_cat_food_bakery_count` | Place count in cell: food bakery (55-cat fine taxonomy) | int64 | 0.0–20.0 (μ 0.2494) |
| `pc2_cat_food_bar_count` | Place count in cell: food bar (55-cat fine taxonomy) | int64 | 0.0–20.0 (μ 0.1138) |
| `pc2_cat_food_cafe_count` | Place count in cell: food cafe (55-cat fine taxonomy) | int64 | 0.0–39.0 (μ 0.6487) |
| `pc2_cat_food_caterer_count` | Place count in cell: food caterer (55-cat fine taxonomy) | int64 | 0.0–14.0 (μ 0.0247) |
| `pc2_cat_food_dessert_count` | Place count in cell: food dessert (55-cat fine taxonomy) | int64 | 0.0–26.0 (μ 0.2393) |
| `pc2_cat_food_fast_food_count` | Place count in cell: food fast food (55-cat fine taxonomy) | int64 | 0.0–12.0 (μ 0.1163) |
| `pc2_cat_food_hawker_count` | Place count in cell: food hawker (55-cat fine taxonomy) | int64 | 0.0–95.0 (μ 0.7937) |
| `pc2_cat_food_restaurant_count` | Place count in cell: food restaurant (55-cat fine taxonomy) | int64 | 0.0–84.0 (μ 1.2927) |
| `pc2_cat_health_clinic_count` | Place count in cell: health clinic (55-cat fine taxonomy) | int64 | 0.0–61.0 (μ 0.312) |
| `pc2_cat_health_hospital_count` | Place count in cell: health hospital (55-cat fine taxonomy) | int64 | 0.0–25.0 (μ 0.0424) |
| `pc2_cat_health_pharmacy_count` | Place count in cell: health pharmacy (55-cat fine taxonomy) | int64 | 0.0–11.0 (μ 0.104) |
| `pc2_cat_health_specialist_count` | Place count in cell: health specialist (55-cat fine taxonomy) | int64 | 0.0–81.0 (μ 0.2615) |
| `pc2_cat_health_tcm_count` | Place count in cell: health tcm (55-cat fine taxonomy) | int64 | 0.0–8.0 (μ 0.0706) |
| `pc2_cat_leisure_entertainment_count` | Place count in cell: leisure entertainment (55-cat fine taxonomy) | int64 | 0.0–13.0 (μ 0.0849) |
| `pc2_cat_leisure_park_count` | Place count in cell: leisure park (55-cat fine taxonomy) | int64 | 0.0–17.0 (μ 0.4966) |
| `pc2_cat_leisure_tourist_count` | Place count in cell: leisure tourist (55-cat fine taxonomy) | int64 | 0.0–17.0 (μ 0.1219) |
| `pc2_cat_other_count` | Place count in cell: other (55-cat fine taxonomy) | int64 | 0.0–241.0 (μ 5.2994) |
| `pc2_cat_res_aged_care_count` | Place count in cell: res aged care (55-cat fine taxonomy) | int64 | 0.0–4.0 (μ 0.0496) |
| `pc2_cat_res_hdb_count` | Place count in cell: res hdb (55-cat fine taxonomy) | int64 | 0.0–26.0 (μ 0.9205) |
| `pc2_cat_res_private_count` | Place count in cell: res private (55-cat fine taxonomy) | int64 | 0.0–25.0 (μ 0.6472) |
| `pc2_cat_retail_apparel_count` | Place count in cell: retail apparel (55-cat fine taxonomy) | int64 | 0.0–75.0 (μ 0.3613) |
| `pc2_cat_retail_convenience_count` | Place count in cell: retail convenience (55-cat fine taxonomy) | int64 | 0.0–29.0 (μ 0.7029) |
| `pc2_cat_retail_electronics_count` | Place count in cell: retail electronics (55-cat fine taxonomy) | int64 | 0.0–52.0 (μ 0.1528) |
| `pc2_cat_retail_furniture_home_count` | Place count in cell: retail furniture home (55-cat fine taxonomy) | int64 | 0.0–44.0 (μ 0.4102) |
| `pc2_cat_retail_general_count` | Place count in cell: retail general (55-cat fine taxonomy) | int64 | 0.0–31.0 (μ 0.5436) |
| `pc2_cat_retail_jewelry_cosmetics_count` | Place count in cell: retail jewelry cosmetics (55-cat fine taxonomy) | int64 | 0.0–90.0 (μ 0.2177) |
| `pc2_cat_retail_mall_count` | Place count in cell: retail mall (55-cat fine taxonomy) | int64 | 0.0–14.0 (μ 0.0656) |
| `pc2_cat_retail_supermarket_count` | Place count in cell: retail supermarket (55-cat fine taxonomy) | int64 | 0.0–16.0 (μ 0.2778) |
| `pc2_cat_service_automotive_count` | Place count in cell: service automotive (55-cat fine taxonomy) | int64 | 0.0–143.0 (μ 0.5183) |
| `pc2_cat_service_beauty_count` | Place count in cell: service beauty (55-cat fine taxonomy) | int64 | 0.0–96.0 (μ 0.9695) |
| `pc2_cat_service_cleaning_repair_count` | Place count in cell: service cleaning repair (55-cat fine taxonomy) | int64 | 0.0–11.0 (μ 0.1759) |
| `pc2_cat_service_consulting_count` | Place count in cell: service consulting (55-cat fine taxonomy) | int64 | 0.0–225.0 (μ 1.7083) |
| `pc2_cat_service_fitness_count` | Place count in cell: service fitness (55-cat fine taxonomy) | int64 | 0.0–35.0 (μ 0.4205) |
| `pc2_cat_service_legal_finance_count` | Place count in cell: service legal finance (55-cat fine taxonomy) | int64 | 0.0–200.0 (μ 0.3919) |
| `pc2_cat_service_logistics_count` | Place count in cell: service logistics (55-cat fine taxonomy) | int64 | 0.0–116.0 (μ 1.7573) |
| `pc2_cat_service_other_count` | Place count in cell: service other (55-cat fine taxonomy) | int64 | 0.0–105.0 (μ 1.1461) |
| `pc2_cat_service_pet_count` | Place count in cell: service pet (55-cat fine taxonomy) | int64 | 0.0–7.0 (μ 0.0451) |
| `pc2_cat_service_real_estate_count` | Place count in cell: service real estate (55-cat fine taxonomy) | int64 | 0.0–106.0 (μ 0.1495) |
| `pc2_cat_transport_air_count` | Place count in cell: transport air (55-cat fine taxonomy) | int64 | 0.0–5.0 (μ 0.0127) |
| `pc2_cat_transport_bus_count` | Place count in cell: transport bus (55-cat fine taxonomy) | int64 | 0.0–16.0 (μ 0.5116) |
| `pc2_cat_transport_ev_count` | Place count in cell: transport ev (55-cat fine taxonomy) | int64 | 0.0–8.0 (μ 0.3649) |
| `pc2_cat_transport_mrt_count` | Place count in cell: transport mrt (55-cat fine taxonomy) | int64 | 0.0–5.0 (μ 0.0663) |
| `pc2_cat_transport_other_count` | Place count in cell: transport other (55-cat fine taxonomy) | int64 | 0.0–3.0 (μ 0.04) |
| `pc2_cat_transport_parking_count` | Place count in cell: transport parking (55-cat fine taxonomy) | int64 | 0.0–10.0 (μ 0.3672) |
| `pc2_cat_unmapped_count` | Place count in cell: unmapped (55-cat fine taxonomy) | int64 | 0.0–51.0 (μ 0.1239) |
| `pc2_dominant_category` | Fine-taxonomy place metric: dominant category | object | e.g. none |
| `mg_bakery_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for bakery | float64 | 0.0–45.0 (μ 0.581) |
| `mg_bar_nightlife_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for bar nightlife | float64 | 0.0–25.429 (μ 0.0947) |
| `mg_beauty_personal_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for beauty personal | float64 | 0.0–103.868 (μ 0.8423) |
| `mg_business_office_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for business office | float64 | 0.0–309.964 (μ 2.0602) |
| `mg_cafe_coffee_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for cafe coffee | float64 | 0.0–52.286 (μ 0.7985) |
| `mg_convenience_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for convenience | float64 | 0.0–34.286 (μ 0.6024) |
| `mg_education_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for education | float64 | 0.0–71.034 (μ 0.8539) |
| `mg_entertainment_culture_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for entertainment culture | float64 | 0.0–18.375 (μ 0.1005) |
| `mg_fast_food_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for fast food | float64 | 0.0–114.5 (μ 0.9366) |
| `mg_fitness_recreation_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for fitness recreation | float64 | 0.0–22.66 (μ 0.1901) |
| `mg_government_public_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for government public | float64 | 0.0–19.833 (μ 0.0765) |
| `mg_hawker_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for hawker | float64 | 0.0–120.529 (μ 1.5937) |
| `mg_health_medical_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for health medical | float64 | 0.0–156.694 (μ 0.6272) |
| `mg_hotel_hospitality_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for hotel hospitality | float64 | 0.0–56.389 (μ 0.1112) |
| `mg_industrial_mfg_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for industrial mfg | float64 | 0.0–133.679 (μ 1.5856) |
| `mg_other_uncategorized_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for other uncategorized | float64 | 0.0–0.0 (μ 0.0) |
| `mg_park_open_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for park open | float64 | 0.0–10.0 (μ 0.1926) |
| `mg_religious_worship_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for religious worship | float64 | 0.0–20.31 (μ 0.1048) |
| `mg_residential_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for residential | float64 | 0.0–27.962 (μ 0.8242) |
| `mg_restaurant_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for restaurant | float64 | 0.0–141.09 (μ 2.4842) |
| `mg_services_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for services | float64 | 0.0–231.214 (μ 1.9984) |
| `mg_shopping_retail_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for shopping retail | float64 | 0.0–136.132 (μ 1.7156) |
| `mg_supermarket_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for supermarket | float64 | 0.0–46.5 (μ 0.5726) |
| `mg_transportation_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for transportation | float64 | 0.0–25.0 (μ 0.8888) |
| `mg_bakery_support_400m` | Magnet model: complementary-category support density within 400 m for bakery (demand context, not supply) | float64 | 0.0–241.0 (μ 2.3582) |
| `mg_bar_nightlife_support_400m` | Magnet model: complementary-category support density within 400 m for bar nightlife (demand context, not supply) | float64 | 0.0–144.0 (μ 0.8738) |
| `mg_beauty_personal_support_400m` | Magnet model: complementary-category support density within 400 m for beauty personal (demand context, not supply) | float64 | 0.0–202.219 (μ 3.1053) |
| `mg_business_office_support_400m` | Magnet model: complementary-category support density within 400 m for business office (demand context, not supply) | float64 | 0.0–329.671 (μ 3.9712) |
| `mg_cafe_coffee_support_400m` | Magnet model: complementary-category support density within 400 m for cafe coffee (demand context, not supply) | float64 | 0.0–221.737 (μ 3.4892) |
| `mg_convenience_support_400m` | Magnet model: complementary-category support density within 400 m for convenience (demand context, not supply) | float64 | 0.0–49.0 (μ 1.1125) |
| `mg_education_support_400m` | Magnet model: complementary-category support density within 400 m for education (demand context, not supply) | float64 | 0.0–45.167 (μ 1.3708) |
| `mg_entertainment_culture_support_400m` | Magnet model: complementary-category support density within 400 m for entertainment culture (demand context, not supply) | float64 | 0.0–109.4 (μ 0.7306) |
| `mg_fast_food_support_400m` | Magnet model: complementary-category support density within 400 m for fast food (demand context, not supply) | float64 | 0.0–188.0 (μ 1.4261) |
| `mg_fitness_recreation_support_400m` | Magnet model: complementary-category support density within 400 m for fitness recreation (demand context, not supply) | float64 | 0.0–156.0 (μ 1.8382) |
| `mg_government_public_support_400m` | Magnet model: complementary-category support density within 400 m for government public (demand context, not supply) | float64 | 0.0–236.714 (μ 1.5127) |
| `mg_hawker_support_400m` | Magnet model: complementary-category support density within 400 m for hawker (demand context, not supply) | float64 | 0.0–59.167 (μ 1.1193) |
| `mg_health_medical_support_400m` | Magnet model: complementary-category support density within 400 m for health medical (demand context, not supply) | float64 | 0.0–224.0 (μ 1.9707) |
| `mg_hotel_hospitality_support_400m` | Magnet model: complementary-category support density within 400 m for hotel hospitality (demand context, not supply) | float64 | 0.0–125.0 (μ 0.7266) |
| `mg_industrial_mfg_support_400m` | Magnet model: complementary-category support density within 400 m for industrial mfg (demand context, not supply) | float64 | 0.0–588.614 (μ 4.1444) |
| `mg_other_uncategorized_support_400m` | Magnet model: complementary-category support density within 400 m for other uncategorized (demand context, not supply) | float64 | 0.0–0.0 (μ 0.0) |
| `mg_park_open_support_400m` | Magnet model: complementary-category support density within 400 m for park open (demand context, not supply) | float64 | 0.0–109.0 (μ 1.3884) |
| `mg_religious_worship_support_400m` | Magnet model: complementary-category support density within 400 m for religious worship (demand context, not supply) | float64 | 0.0–26.5 (μ 0.2671) |
| `mg_residential_support_400m` | Magnet model: complementary-category support density within 400 m for residential (demand context, not supply) | float64 | 0.0–60.0 (μ 1.2601) |
| `mg_restaurant_support_400m` | Magnet model: complementary-category support density within 400 m for restaurant (demand context, not supply) | float64 | 0.0–126.465 (μ 1.5855) |
| `mg_services_support_400m` | Magnet model: complementary-category support density within 400 m for services (demand context, not supply) | float64 | 0.0–331.805 (μ 4.1099) |
| `mg_shopping_retail_support_400m` | Magnet model: complementary-category support density within 400 m for shopping retail (demand context, not supply) | float64 | 0.0–197.833 (μ 2.7523) |
| `mg_supermarket_support_400m` | Magnet model: complementary-category support density within 400 m for supermarket (demand context, not supply) | float64 | 0.0–186.0 (μ 2.0078) |
| `mg_transportation_support_400m` | Magnet model: complementary-category support density within 400 m for transportation (demand context, not supply) | float64 | 0.0–277.8 (μ 4.1957) |
| `mg_bakery_anchor_strength` | Magnet model: strength of the biggest bakery anchor place nearby | float64 | 0.0–1311.777 (μ 7.0553) |
| `mg_bar_nightlife_anchor_strength` | Magnet model: strength of the biggest bar nightlife anchor place nearby | float64 | 0.0–277.887 (μ 1.9934) |
| `mg_beauty_personal_anchor_strength` | Magnet model: strength of the biggest beauty personal anchor place nearby | float64 | 0.0–1009.705 (μ 9.1461) |
| `mg_business_office_anchor_strength` | Magnet model: strength of the biggest business office anchor place nearby | float64 | 0.0–328.273 (μ 3.4904) |
| `mg_cafe_coffee_anchor_strength` | Magnet model: strength of the biggest cafe coffee anchor place nearby | float64 | 0.0–1272.626 (μ 12.7137) |
| `mg_convenience_anchor_strength` | Magnet model: strength of the biggest convenience anchor place nearby | float64 | 0.0–81.789 (μ 1.4772) |
| `mg_education_anchor_strength` | Magnet model: strength of the biggest education anchor place nearby | float64 | 0.0–47.168 (μ 0.5145) |
| `mg_entertainment_culture_anchor_strength` | Magnet model: strength of the biggest entertainment culture anchor place nearby | float64 | 0.0–1661.486 (μ 5.5447) |
| `mg_fast_food_anchor_strength` | Magnet model: strength of the biggest fast food anchor place nearby | float64 | 0.0–1167.813 (μ 5.9024) |
| `mg_fitness_recreation_anchor_strength` | Magnet model: strength of the biggest fitness recreation anchor place nearby | float64 | 0.0–1008.704 (μ 6.5371) |
| `mg_government_public_anchor_strength` | Magnet model: strength of the biggest government public anchor place nearby | float64 | 0.0–72.098 (μ 0.7446) |
| `mg_hawker_anchor_strength` | Magnet model: strength of the biggest hawker anchor place nearby | float64 | 0.0–88.851 (μ 1.0416) |
| `mg_health_medical_anchor_strength` | Magnet model: strength of the biggest health medical anchor place nearby | float64 | 0.0–92.734 (μ 1.3248) |
| `mg_hotel_hospitality_anchor_strength` | Magnet model: strength of the biggest hotel hospitality anchor place nearby | float64 | 0.0–2006.901 (μ 5.4609) |
| `mg_industrial_mfg_anchor_strength` | Magnet model: strength of the biggest industrial mfg anchor place nearby | float64 | 0.0–321.675 (μ 2.9018) |
| `mg_other_uncategorized_anchor_strength` | Magnet model: strength of the biggest other uncategorized anchor place nearby | float64 | 0.0–0.0 (μ 0.0) |
| `mg_park_open_anchor_strength` | Magnet model: strength of the biggest park open anchor place nearby | float64 | 0.0–28.691 (μ 0.3682) |
| `mg_religious_worship_anchor_strength` | Magnet model: strength of the biggest religious worship anchor place nearby | float64 | 0.0–27.932 (μ 0.1845) |
| `mg_residential_anchor_strength` | Magnet model: strength of the biggest residential anchor place nearby | float64 | 0.0–1144.985 (μ 6.5066) |
| `mg_restaurant_anchor_strength` | Magnet model: strength of the biggest restaurant anchor place nearby | float64 | 0.0–1179.978 (μ 11.0284) |
| `mg_services_anchor_strength` | Magnet model: strength of the biggest services anchor place nearby | float64 | 0.0–1089.115 (μ 11.5536) |
| `mg_shopping_retail_anchor_strength` | Magnet model: strength of the biggest shopping retail anchor place nearby | float64 | 0.0–1171.713 (μ 10.1764) |
| `mg_supermarket_anchor_strength` | Magnet model: strength of the biggest supermarket anchor place nearby | float64 | 0.0–42.406 (μ 0.334) |
| `mg_transportation_anchor_strength` | Magnet model: strength of the biggest transportation anchor place nearby | float64 | 0.0–1156.737 (μ 9.7752) |
| `mg_avg_competitors_400m` | Magnet model: mean same-category competitor count within 400 m across categories | float64 | 0.0–181.72 (μ 2.5313) |
| `mg_avg_anchor_strength` | Magnet model: strength of the biggest avg anchor place nearby | float64 | 0.0–765.357 (μ 8.2117) |
| `mg_avg_walk_dist_mrt_m` | Magnet model: mean walk distance to MRT across category micrographs | float64 | 0.0–9999.0 (μ 2329.332) |
| `colo_fit_cafe_coffee` | Co-location mix-match for cafe_coffee: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) | float64 | -0.3437–0.1978 (μ 0.0159) |
| `colo_fit_restaurant` | Co-location mix-match for restaurant: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) | float64 | -0.1142–0.5724 (μ 0.1284) |
| `colo_fit_hawker` | Co-location mix-match for hawker: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) | float64 | -0.5932–0.2667 (μ -0.1151) |
| `colo_fit_fast_food` | Co-location mix-match for fast_food: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) | float64 | -0.7249–0.266 (μ -0.0864) |
| `colo_fit_supermarket` | Co-location mix-match for supermarket: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) | float64 | -0.3589–0.1712 (μ -0.0755) |
| `colo_fit_convenience` | Co-location mix-match for convenience: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) | float64 | -0.3274–0.187 (μ -0.0542) |
| `colo_fit_fitness_recreation` | Co-location mix-match for fitness_recreation: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) | float64 | -0.5516–0.1304 (μ -0.1253) |
| `colo_fit_health_medical` | Co-location mix-match for health_medical: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) | float64 | -0.4839–0.2461 (μ -0.0194) |
| `colo_fit_beauty_personal` | Co-location mix-match for beauty_personal: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) | float64 | -0.4114–0.547 (μ 0.0778) |
| `colo_fit_shopping_retail` | Co-location mix-match for shopping_retail: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) | float64 | -0.0667–0.4489 (μ 0.1013) |
| `colo_fit_education` | Co-location mix-match for education: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) | float64 | -0.5625–0.2059 (μ -0.149) |
| `pc_total` | Total mapped places (POIs) in cell — overall point-of-interest density | float64 | 0.0–1215.0 (μ 26.0398) |
| `pc_unique_brands` | Distinct retail/F&B brands present — chain richness | float64 | 0.0–201.0 (μ 2.5793) |
| `pc_magnets` | High-draw anchor places (malls, hubs, 30+ review demand magnets) | float64 | 0.0–266.0 (μ 2.947) |
| `pc_long_tail` | Places with few/no reviews — independent long-tail share base | float64 | 0.0–725.0 (μ 14.8062) |
| `pc_with_rating` | Places carrying a Google rating | float64 | 0.0–704.0 (μ 14.9478) |
| `pc_total_reviews` | Sum of review counts — popularity/footfall proxy | float64 | 0.0–340605.0 (μ 2666.3094) |
| `pc_avg_rating` | Mean rating of rated places — quality proxy | float64 | 0.0–5.0 (μ 2.2365) |
| `pc_cat_bakery` | Place count in cell: bakery category (24-cat taxonomy) | float64 | 0.0–22.0 (μ 0.2785) |
| `pc_cat_bar_nightlife` | Place count in cell: bar nightlife category (24-cat taxonomy) | float64 | 0.0–28.0 (μ 0.153) |
| `pc_cat_beauty_personal` | Place count in cell: beauty personal category (24-cat taxonomy) | float64 | 0.0–106.0 (μ 1.0614) |
| `pc_cat_business_office` | Place count in cell: business office category (24-cat taxonomy) | float64 | 0.0–324.0 (μ 2.9505) |
| `pc_cat_cafe_coffee` | Place count in cell: cafe coffee category (24-cat taxonomy) | float64 | 0.0–51.0 (μ 0.8908) |
| `pc_cat_convenience` | Place count in cell: convenience category (24-cat taxonomy) | float64 | 0.0–17.0 (μ 0.2957) |
| `pc_cat_education` | Place count in cell: education category (24-cat taxonomy) | float64 | 0.0–78.0 (μ 1.5271) |
| `pc_cat_entertainment_culture` | Place count in cell: entertainment culture category (24-cat taxonomy) | float64 | 0.0–25.0 (μ 0.2967) |
| `pc_cat_fast_food` | Place count in cell: fast food category (24-cat taxonomy) | float64 | 0.0–12.0 (μ 0.1282) |
| `pc_cat_fitness_recreation` | Place count in cell: fitness recreation category (24-cat taxonomy) | float64 | 0.0–47.0 (μ 0.5496) |
| `pc_cat_government_public` | Place count in cell: government public category (24-cat taxonomy) | float64 | 0.0–29.0 (μ 0.2643) |
| `pc_cat_hawker` | Place count in cell: hawker category (24-cat taxonomy) | float64 | 0.0–96.0 (μ 0.8051) |
| `pc_cat_health_medical` | Place count in cell: health medical category (24-cat taxonomy) | float64 | 0.0–248.0 (μ 1.0184) |
| `pc_cat_hotel_hospitality` | Place count in cell: hotel hospitality category (24-cat taxonomy) | float64 | 0.0–51.0 (μ 0.1607) |
| `pc_cat_industrial_mfg` | Place count in cell: industrial mfg category (24-cat taxonomy) | float64 | 0.0–148.0 (μ 2.4534) |
| `pc_cat_other_uncategorized` | Place count in cell: other uncategorized category (24-cat taxonomy) | float64 | 0.0–25.0 (μ 0.4635) |
| `pc_cat_park_open` | Place count in cell: park open category (24-cat taxonomy) | float64 | 0.0–19.0 (μ 0.6055) |
| `pc_cat_religious_worship` | Place count in cell: religious worship category (24-cat taxonomy) | float64 | 0.0–29.0 (μ 0.2363) |
| `pc_cat_residential` | Place count in cell: residential category (24-cat taxonomy) | float64 | 0.0–33.0 (μ 2.2234) |
| `pc_cat_restaurant` | Place count in cell: restaurant category (24-cat taxonomy) | float64 | 0.0–112.0 (μ 1.542) |
| `pc_cat_services` | Place count in cell: services category (24-cat taxonomy) | float64 | 0.0–260.0 (μ 3.1007) |
| `pc_cat_shopping_retail` | Place count in cell: shopping retail category (24-cat taxonomy) | float64 | 0.0–251.0 (μ 2.1007) |
| `pc_cat_supermarket` | Place count in cell: supermarket category (24-cat taxonomy) | float64 | 0.0–28.0 (μ 0.4016) |
| `pc_cat_transportation` | Place count in cell: transportation category (24-cat taxonomy) | float64 | 0.0–31.0 (μ 1.7629) |
| `pc_cat_financial_services` | Count of financial venues in cell (ATM/bank/insurance/remittance) | float64 | 0.0–154.0 (μ 0.5083) |
| `pc_cat_automated_kiosk` | Count of unmanned automated points (vending/locker/AXS) in cell | float64 | 0.0–10.0 (μ 0.2614) |
| `pc_diversity` | Category entropy of the place mix — high = mixed-use | float64 | 0.0–2.969 (μ 0.8499) |
| `pc_dominant_category` | Most common place category in cell | object | e.g. none |
| `rent_resi_psf_med` | URA private-resi median rent (913 projects, last 4 quarters, IDW k=5 ≤2.5 km). COMMERCIAL rent not openly available. NaN = no observation in range | float64 | 2.02–8.298 (μ 4.5274) |
| `rent_resi_n_obs` | Projects within 2.5 km supporting the estimate | int64 | 0.0–5.0 (μ 2.6021) |
| `rent_resolution` | local (≤800 m) / idw / none | object | e.g. none |
| `roi_cap_per_rent_cafe_coffee` | cap_cafe_coffee / rent_resi_psf_med — opportunity per occupancy-cost proxy (rank heuristic). NaN where no rent | float64 | 0.0009–1.0506 (μ 0.2168) |
| `roi_cap_per_rent_supermarket` | cap_supermarket / rent_resi_psf_med — opportunity per occupancy-cost proxy (rank heuristic). NaN where no rent | float64 | 0.0003–0.948 (μ 0.1897) |
| `roi_cap_per_rent_restaurant` | cap_restaurant / rent_resi_psf_med — opportunity per occupancy-cost proxy (rank heuristic). NaN where no rent | float64 | 0.0009–1.1242 (μ 0.2786) |
| `roi_cap_per_rent_shopping_retail` | cap_shopping_retail / rent_resi_psf_med — opportunity per occupancy-cost proxy (rank heuristic). NaN where no rent | float64 | 0.0017–1.2293 (μ 0.2945) |
| `roi_cap_per_rent_total` | cap_total / rent_resi_psf_med — opportunity per occupancy-cost proxy (rank heuristic). NaN where no rent | float64 | 0.017–11.0215 (μ 2.4671) |
| `rent_hdb_4r_est_pm` | Rent hdb 4r est pm | float64 | 2634.0–5080.0 (μ 3323.7436) |
| `rent_hdb_est_psf` | Rent hdb est psf | float64 | 2.718–5.243 (μ 3.4301) |
| `rent_occ_cost_psf` | Rent occ cost psf | float64 | 2.02–8.298 (μ 4.5202) |
| `rent_occ_cost_source` | Rent occ cost source | object | e.g. none |

## subzone_all_features (430 cols)

| Column | Description | Type | Range/μ or sample |
|---|---|---|---|
| `subzone_c` | URA subzone code | object | e.g. AMSZ01 |
| `pop_resident` | Resident population (citizens + PRs) | float64 | 0.0–124194.4362 (μ 12821.4724) |
| `pop_hdb` | Residents in HDB flats | float64 | 0.0–112465.6735 (μ 9732.1817) |
| `pop_non_hdb` | Residents in non-HDB housing | float64 | 0.0–30419.8262 (μ 3089.2907) |
| `pop_0_14` | Population age 0-14 | float64 | 0.0–15309.9759 (μ 1743.1091) |
| `pop_15_64` | Population age 15-64 | float64 | 0.0–82451.304 (μ 8666.6677) |
| `pop_65plus` | Population age 65+ | float64 | 0.0–26433.1563 (μ 2411.6956) |
| `pop_nonresident` | Non-residents (FW + EP + MDW) | float64 | 0.0–71711.6131 (μ 5696.6258) |
| `pop_dorm` | Migrant-worker dormitory population at real MOM dorm locations (439,198 national, DASL H2-2024); subset of non-resident | float64 | 0.0–42705.2471 (μ 1347.2331) |
| `pop_total_all` | Total population (residents + non-residents) | float64 | 0.0–139906.912 (μ 18518.0982) |
| `pop_hdb_share` | HDB share of resident pop | float64 | 0.0–1.0 (μ 0.4612) |
| `nonres_share` | Non-resident share of total pop | float64 | 0.0–1.0 (μ 0.4279) |
| `lu_total_m2` | Total land area covered by URA parcels in hex | float64 | 119020.5624–67979222.428 (μ 2407063.5447) |
| `lu_parcel_count` | URA parcels intersecting hex | int64 | 22.0–7026.0 (μ 500.2761) |
| `lu_residential_pct` | Land area share zoned residential | float64 | 0.0–0.8106 (μ 0.302) |
| `lu_mixed_use_pct` | Mixed-use zone share (residential + commercial) | float64 | 0.0–0.3615 (μ 0.0276) |
| `lu_commercial_pct` | Land area share zoned commercial | float64 | 0.0–0.6369 (μ 0.0286) |
| `lu_hotel_pct` | Hotel zone share | float64 | 0.0–0.1804 (μ 0.0065) |
| `lu_business_pct` | Land area share zoned business (industrial) | float64 | 0.0–0.9114 (μ 0.1235) |
| `lu_business_park_pct` | Business park share | float64 | 0.0–0.6194 (μ 0.0082) |
| `lu_educational_pct` | Educational institution share | float64 | 0.0–0.79 (μ 0.0396) |
| `lu_health_pct` | Health & medical share | float64 | 0.0–0.371 (μ 0.0064) |
| `lu_institutional_pct` | Civic/community/place-of-worship | float64 | 0.0–0.9115 (μ 0.0463) |
| `lu_open_space_pct` | Park / open space share | float64 | 0.0–0.9969 (μ 0.0948) |
| `lu_transport_pct` | Transport infra share | float64 | 0.0–0.8373 (μ 0.1966) |
| `lu_utility_pct` | Utility infra share | float64 | 0.0–0.7739 (μ 0.0107) |
| `lu_water_pct` | Water body share | float64 | 0.0–0.7043 (μ 0.0388) |
| `lu_reserve_pct` | Reserve site share | float64 | 0.0–0.9576 (μ 0.0705) |
| `lu_other_pct` | Other / unmapped | float64 | 0.0–0.0 (μ 0.0) |
| `avg_gpr` | Area-weighted Gross Plot Ratio | float64 | 0.0–14.6966 (μ 2.3193) |
| `max_gpr` | Max GPR within hex | float64 | 0.0–25.0 (μ 3.919) |
| `lu_entropy` | Shannon entropy across 14 LU buckets | float64 | 0.021–2.115 (μ 1.3516) |
| `dominant_use` | Bucket with highest area share | object | e.g. mixed_use |
| `n_hex8` | Number of hex8 children (bookkeeping) | float64 | 0.0–121.0 (μ 3.6534) |
| `bldg_count` | Building footprints in hex (Overture + HDB + OSM) | float64 | 0.0–13134.0 (μ 839.0828) |
| `bldg_footprint_m2` | Total clipped building footprint area in hex | float64 | 0.0–3747708.8766 (μ 327130.1087) |
| `bldg_residential_count` | Residential buildings | float64 | 0.0–1998.0 (μ 164.908) |
| `bldg_commercial_count` | Commercial buildings | float64 | 0.0–205.0 (μ 11.9233) |
| `bldg_industrial_count` | Industrial buildings | float64 | 0.0–647.0 (μ 15.1196) |
| `bldg_institutional_count` | Institutional buildings | float64 | 0.0–88.0 (μ 4.7699) |
| `best_max_floors` | Max floor count (Overture or HDB authoritative) | float64 | 0.0–70.0 (μ 25.7239) |
| `n_highrise_bldgs` | Number of buildings with floors ≥ 10 | float64 | 0.0–1865.0 (μ 133.7025) |
| `est_total_floor_area_m2` | Sum of footprint × est_floors per building | float64 | 0.0–10536155.4627 (μ 1763065.5427) |
| `hdb_block_count` | HDB blocks (authoritative) | float64 | 0.0–416.0 (μ 41.0613) |
| `hdb_dwelling_units` | Total dwelling units across HDB blocks | float64 | 0.0–32486.272 (μ 3578.4172) |
| `subzone_area_m2` | Subzone polygon area | float64 | 0.0–68550559.2976 (μ 2344053.2327) |
| `bldg_density_per_km2` | Buildings per km² | float64 | 0.0–5030.4785 (μ 478.2112) |
| `bldg_footprint_share` | Footprint as fraction of hex area (clipped, ≤1) | float64 | 0.0–1.0 (μ 0.1935) |
| `est_built_far` | Estimated built-up FAR = total floor area / hex area | float64 | 0.0–7.347 (μ 1.2171) |
| `subzone_area_km2` | Subzone polygon area | float64 | 0.0–68.5506 (μ 2.3441) |
| `road_length_total_m` | Total OSM road length clipped to hex | float64 | 0.0–1061979.8275 (μ 87138.2876) |
| `road_density_km_per_km2` | Road km per km² | float64 | 0.0–264.1348 (μ 52.2282) |
| `road_walkable_share` | Pedestrian-only roads as fraction of total | float64 | 0.0–0.7701 (μ 0.3879) |
| `road_max_class_through` | Highest road class running through hex | object | e.g. motorway |
| `road_intersection_count_total` | Road-network metric: road intersection count total | float64 | 0.0–5204.0 (μ 452.7515) |
| `road_intersection_density_per_km2` | Vehicle-network nodes with deg ≥ 3 per km² (Jacobs) | float64 | 0.0–1538.1555 (μ 281.984) |
| `dist_expressway_m` | Centroid distance to nearest motorway/trunk segment | float64 | 0.0–9552.6208 (μ 544.1322) |
| `expressway_in_subzone` | An expressway segment crosses the subzone | object | e.g. True |
| `lane_km_per_km2` | Lane-km per km² (lane count × length / area) | float64 | 0.0–97.1944 (μ 42.9786) |
| `bridge_length_m` | Bridge segment length | float64 | 0.0–73545.4908 (μ 3476.6231) |
| `signalized_crossing_count` | LTA traffic signals in hex | float64 | 0.0–968.0 (μ 137.7822) |
| `parking_lot_count` | OSM amenity=parking points | float64 | 0.0–61.0 (μ 9.681) |
| `hdb_mscp_count` | Authoritative HDB multi-storey carparks | float64 | 0.0–42.0 (μ 3.7883) |
| `centr_betweenness_max` | Max betweenness centrality of major-road nodes | float64 | 0.0–0.108 (μ 0.0213) |
| `centr_bridge_count` | Tarjan bridge endpoints (network cut points) | float64 | 0.0–64.0 (μ 7.046) |
| `mrt_station_count` | MRT/LRT stations in hex | float64 | 0.0–6.0 (μ 0.7086) |
| `mrt_exit_count` | MRT exits in hex | float64 | 0.0–33.0 (μ 1.8252) |
| `bus_stop_count` | Bus stops in hex | float64 | 0.0–104.0 (μ 15.865) |
| `dist_mrt_m` | Centroid distance to nearest MRT/LRT station | float64 | 0.0–9633.2929 (μ 415.7928) |
| `dist_bus_m` | Centroid distance to nearest bus stop | float64 | 0.0–9542.3434 (μ 111.2483) |
| `rail_line_through_m` | Rail line length through hex (above + underground) | float64 | 0.0–20502.9798 (μ 1847.3076) |
| `daily_train_taps` | Daily MRT/LRT taps (Jan 2026 LTA monthly / 31) | float64 | 0.0–357291.0645 (μ 25424.4281) |
| `daily_bus_taps` | Daily bus taps (Dec 2025 LTA monthly / 31) | float64 | 0.0–207571.871 (μ 19465.5504) |
| `n_interchanges` | Interchange stations in subzone | float64 | 0.0–2.0 (μ 0.1012) |
| `max_transit_score` | Best hex8 transit score within subzone | float64 | 0.0–0.9879 (μ 0.6282) |
| `has_mrt` | Subzone contains at least one MRT/LRT station | object | e.g. False |
| `has_interchange` | Subzone contains an interchange station | object | e.g. False |
| `ped_path_length_m` | Footway + path + cycleway + steps length | float64 | 0.0–307164.9088 (μ 39226.7563) |
| `walk_amenities_400m` | Place count within 400m walk | float64 | 0.0–15625.0 (μ 1462.2393) |
| `walkability_score` | Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) | float64 | 0.0–0.9132 (μ 0.4596) |
| `expressway_severance` | Expressway < 200m AND no exit < 400m (barrier without benefit) | object | e.g. False |
| `nl_2022` | VIIRS night light radiance 2022 (subzone-broadcast) | float64 | 0.0–153.5743 (μ 57.5262) |
| `nl_2024` | VIIRS night light radiance 2024 (subzone-broadcast) | float64 | 0.0–179.5402 (μ 65.4029) |
| `nl_change_pct` | VIIRS 2022→2024 brightness change | float64 | -28.0109–120.3925 (μ 12.3429) |
| `nl_growth_corridor` | True if night light grew ≥ 20% | bool | e.g. True |
| `nl_decline_zone` | True if night light declined ≥ 20% | bool | e.g. False |
| `nl_per_capita` | nl_2024 / pop_resident (commercial vs residential signal) | float64 | 0.0–1.6098 (μ 0.1122) |
| `nl_commercial_indicator` | nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) | float64 | 0.0–165.0284 (μ 41.0113) |
| `wp_pop` | WorldPop count per hex (single snapshot — only one valid TIF available) | float64 | 0.0–161771.4753 (μ 23858.194) |
| `hdb_resale_in_town` | hdb resale in town (see layer docs) | int64 | 0.0–1.0 (μ 0.7791) |
| `hdb_resale_txns_total` | hdb resale txns total (see layer docs) | float64 | 0.0–18517.0 (μ 6933.4018) |
| `hdb_resale_txns_12m` | hdb resale txns 12m (see layer docs) | float64 | 0.0–1948.0 (μ 788.6319) |
| `hdb_resale_median_price` | hdb resale median price (see layer docs) | float64 | 0.0–760000.0 (μ 402716.7607) |
| `hdb_resale_median_psm` | hdb resale median psm (see layer docs) | float64 | 0.0–7628.866 (μ 4379.8789) |
| `hdb_resale_4r_median_price` | hdb resale 4r median price (see layer docs) | float64 | 0.0–835000.0 (μ 448502.4049) |
| `hdb_resale_4r_median_psm` | hdb resale 4r median psm (see layer docs) | float64 | 0.0–9175.2577 (μ 4760.0999) |
| `hdb_resale_12m_median_price` | hdb resale 12m median price (see layer docs) | float64 | 0.0–980000.0 (μ 504116.8221) |
| `hdb_resale_avg_lease_remaining_yrs` | hdb resale avg lease remaining yrs (see layer docs) | float64 | 0.0–89.8692 (μ 55.4714) |
| `school_count_total` | school count total (see layer docs) | int64 | 0.0–12.0 (μ 1.0337) |
| `school_count_primary` | school count primary (see layer docs) | int64 | 0.0–6.0 (μ 0.5583) |
| `school_count_secondary` | school count secondary (see layer docs) | int64 | 0.0–5.0 (μ 0.408) |
| `school_count_jc` | school count jc (see layer docs) | int64 | 0.0–2.0 (μ 0.0675) |
| `school_count_mixed` | school count mixed (see layer docs) | int64 | 0.0–0.0 (μ 0.0) |
| `school_count_premium` | school count premium (see layer docs) | int64 | 0.0–3.0 (μ 0.1258) |
| `primary_school_zone_count` | Primary-school zones overlapping cell | int64 | 0.0–17.0 (μ 1.4049) |
| `primary_schools_within_1km` | Count of primary schools within 1km | float64 | 0.0–6.18 (μ 1.4169) |
| `primary_schools_within_2km` | Count of primary schools within 2km | float64 | 0.0–17.82 (μ 5.0806) |
| `nearest_school_dist_m` | Distance to nearest school | float64 | 4.5–10554.2 (μ 644.2123) |
| `nearest_primary_school_dist_m` | Distance to nearest primary school | float64 | 9.5–11258.3 (μ 743.7574) |
| `in_primary_school_zone` | Cell intersects a primary-school zone | int64 | 0.0–1.0 (μ 0.4294) |
| `tourist_attraction_count` | tourist attraction count (see layer docs) | int64 | 0.0–15.0 (μ 0.3344) |
| `hawker_centre_count` | hawker centre count (see layer docs) | int64 | 0.0–5.0 (μ 0.3957) |
| `chas_clinic_count` | chas clinic count (see layer docs) | int64 | 0.0–42.0 (μ 3.6564) |
| `chas_clinics_within_500m` | Count of chas clinics within 500m | int64 | 0.0–266.0 (μ 24.0644) |
| `preschool_count` | preschool count (see layer docs) | int64 | 0.0–68.0 (μ 7.0245) |
| `preschools_within_400m` | Count of preschools within 400m | int64 | 0.0–289.0 (μ 29.7086) |
| `silver_zone_count` | silver zone count (see layer docs) | int64 | 0.0–11.0 (μ 0.5583) |
| `nearest_tourist_dist_m` | Distance to nearest tourist | float64 | 12.7–9975.4 (μ 1876.9933) |
| `nearest_hawker_centre_dist_m` | Distance to nearest hawker centre | float64 | 17.8–9842.3 (μ 805.3365) |
| `nearest_chas_clinic_dist_m` | Distance to nearest chas clinic | float64 | 1.4–9742.0 (μ 329.389) |
| `nearest_preschool_dist_m` | Distance to nearest preschool | float64 | 1.3–9695.5 (μ 386.9859) |
| `in_silver_zone` | Cell intersects an elderly-priority Silver Zone | int64 | 0.0–1.0 (μ 0.1779) |
| `vibrancy_index` | Composite: places + magnets + reviews + transit + night lights | float64 | 0.005–0.97 (μ 0.2075) |
| `livability_index` | Composite: walkability + green + amenities + transit | float64 | 0.045–0.956 (μ 0.67) |
| `commercial_intensity` | Supply/morphology composite: commercial place mix + commercial night-light + commercial land-use share | float64 | 0.002–0.86 (μ 0.1683) |
| `family_index` | Composite: children + schools + preschools + family amenities | float64 | 0.0–0.934 (μ 0.3652) |
| `density_pressure` | Composite: population + buildings + low road space | float64 | 0.0–0.73 (μ 0.1314) |
| `accessibility_composite` | Composite access score across transit + walk + road reach | float64 | 0.0–0.893 (μ 0.298) |
| `pull_cbd` | Gravity pull toward cbd (distance-decayed attraction) | float64 | 0.009–1.0 (μ 0.3038) |
| `pull_mall` | Gravity pull toward mall (distance-decayed attraction) | float64 | 0.001–0.995 (μ 0.2563) |
| `pull_hospital` | Gravity pull toward hospital (distance-decayed attraction) | float64 | 0.004–0.986 (μ 0.3275) |
| `pull_mrt_interchange` | Gravity pull toward mrt interchange (distance-decayed attraction) | float64 | 0.0–0.976 (μ 0.2702) |
| `pull_school_premium` | Gravity pull toward school premium (distance-decayed attraction) | float64 | 0.003–0.961 (μ 0.4031) |
| `pull_airport` | Gravity pull toward airport (distance-decayed attraction) | float64 | 0.014–0.949 (μ 0.3069) |
| `pull_composite` | Gravity pull toward composite (distance-decayed attraction) | float64 | 0.005–0.762 (μ 0.3113) |
| `syn_pop_x_walk` | Synergy interaction term: pop x walk (cross-feature product) | float64 | 0.0–0.785 (μ 0.1053) |
| `syn_pop_x_transit` | Synergy interaction term: pop x transit (cross-feature product) | float64 | 0.0–0.0 (μ 0.0) |
| `syn_office_x_transit` | Synergy interaction term: office x transit (cross-feature product) | float64 | 0.0–0.0 (μ 0.0) |
| `syn_retail_x_anchors` | Synergy interaction term: retail x anchors (cross-feature product) | float64 | 0.0–1.0 (μ 0.0537) |
| `syn_density_x_amenities` | Synergy interaction term: density x amenities (cross-feature product) | float64 | 0.0–1.0 (μ 0.0698) |
| `syn_far_x_transit` | Synergy interaction term: far x transit (cross-feature product) | float64 | 0.0–0.0 (μ 0.0) |
| `syn_residential_x_school` | Synergy interaction term: residential x school (cross-feature product) | float64 | 0.0–0.731 (μ 0.0812) |
| `syn_premium_school_x_4r` | Synergy interaction term: premium school x 4r (cross-feature product) | float64 | 0.0–0.818 (μ 0.0385) |
| `sat_cafe_coffee_per_1k` | Supply saturation: cafe coffee outlets per 1,000 residents | float64 | 0.0–171.671 (μ 9.0022) |
| `gap_cafe_coffee` | Saturation gap for cafe coffee: actual minus expected per-1k supply (positive = oversupplied) | float64 | -1.0–1.0 (μ 0.6575) |
| `sat_restaurant_per_1k` | Supply saturation: restaurant outlets per 1,000 residents | float64 | 0.0–399.734 (μ 19.4283) |
| `gap_restaurant` | Saturation gap for restaurant: actual minus expected per-1k supply (positive = oversupplied) | float64 | -1.0–1.0 (μ 0.6783) |
| `sat_hawker_per_1k` | Supply saturation: hawker outlets per 1,000 residents | float64 | 0.0–187.632 (μ 6.3907) |
| `gap_hawker` | Saturation gap for hawker: actual minus expected per-1k supply (positive = oversupplied) | float64 | -1.0–1.0 (μ 0.6861) |
| `sat_fast_food_per_1k` | Supply saturation: fast food outlets per 1,000 residents | float64 | 0.0–34.515 (μ 0.9259) |
| `gap_fast_food` | Saturation gap for fast food: actual minus expected per-1k supply (positive = oversupplied) | float64 | -1.0–1.0 (μ 0.7655) |
| `sat_supermarket_per_1k` | Supply saturation: supermarket outlets per 1,000 residents | float64 | 0.0–73.271 (μ 3.4469) |
| `gap_supermarket` | Saturation gap for supermarket: actual minus expected per-1k supply (positive = oversupplied) | float64 | -1.0–1.0 (μ 0.6872) |
| `sat_bakery_per_1k` | Supply saturation: bakery outlets per 1,000 residents | float64 | 0.0–39.184 (μ 2.0989) |
| `gap_bakery` | Saturation gap for bakery: actual minus expected per-1k supply (positive = oversupplied) | float64 | -1.0–1.0 (μ 0.6981) |
| `sat_beauty_personal_per_1k` | Supply saturation: beauty personal outlets per 1,000 residents | float64 | 0.0–265.822 (μ 10.387) |
| `gap_beauty_personal` | Saturation gap for beauty personal: actual minus expected per-1k supply (positive = oversupplied) | float64 | -1.0–1.0 (μ 0.7337) |
| `sat_fitness_recreation_per_1k` | Supply saturation: fitness recreation outlets per 1,000 residents | float64 | 0.0–54.049 (μ 2.9683) |
| `gap_fitness_recreation` | Saturation gap for fitness recreation: actual minus expected per-1k supply (positive = oversupplied) | float64 | -1.0–1.0 (μ 0.5594) |
| `sat_health_medical_per_1k` | Supply saturation: health medical outlets per 1,000 residents | float64 | 0.0–194.49 (μ 8.5719) |
| `gap_health_medical` | Saturation gap for health medical: actual minus expected per-1k supply (positive = oversupplied) | float64 | -1.0–1.0 (μ 0.6743) |
| `archetype_id` | k-means (K=8) urban archetype cluster id | int64 | 0.0–7.0 (μ 2.589) |
| `archetype_label` | Human label of the archetype cluster | object | e.g. Mature_HDB |
| `archetype_dist` | Distance to archetype centroid (typicality) | float64 | 0.69–11.935 (μ 2.4777) |
| `walk_mrt_score` | Walk-access score to nearest mrt (distance-decayed) | float64 | 0.0–1.0 (μ 0.4802) |
| `walk_bus_score` | Walk-access score to nearest bus (distance-decayed) | float64 | 0.0–0.987 (μ 0.7113) |
| `walk_school_score` | Walk-access score to nearest school (distance-decayed) | float64 | 0.0–0.0 (μ 0.0) |
| `walk_clinic_score` | Walk-access score to nearest clinic (distance-decayed) | float64 | 0.0–0.0 (μ 0.0) |
| `walk_hawker_score` | Walk-access score to nearest hawker (distance-decayed) | float64 | 0.0–0.0 (μ 0.0) |
| `walk_supermarket_score` | Walk-access score to nearest supermarket (distance-decayed) | float64 | 0.0–0.0 (μ 0.0) |
| `walk_park_score` | Walk-access score to nearest park (distance-decayed) | float64 | 0.0–0.0 (μ 0.0) |
| `walk_food_score` | Walk-access score to nearest food (distance-decayed) | float64 | 0.0–0.0 (μ 0.0) |
| `walk_convenience_score` | Walk-access score to nearest convenience (distance-decayed) | float64 | 0.0–0.0 (μ 0.0) |
| `walk_score_avg` | Mean of the 9 amenity walk-access scores | float64 | 0.0–0.22 (μ 0.1324) |
| `osm_amenities_count` | OSM amenity-tagged POIs in cell (independent ground truth) | int64 | 0.0–745.0 (μ 88.6043) |
| `osm_leisure_count` | OSM leisure-tagged POIs in cell | int64 | 0.0–407.0 (μ 38.5031) |
| `osm_shops_count` | OSM shop-tagged POIs in cell — independent retail frontage | int64 | 0.0–301.0 (μ 26.5859) |
| `osm_tourism_count` | OSM tourism-tagged POIs in cell | int64 | 0.0–342.0 (μ 8.0951) |
| `wc_tree_share` | ESA WorldCover land-cover share: tree share | float64 | 0.019–0.884 (μ 0.2702) |
| `wc_built_share` | ESA WorldCover land-cover share: built share | float64 | 0.0–0.966 (μ 0.5717) |
| `wc_water_share` | ESA WorldCover land-cover share: water share | float64 | 0.0–0.864 (μ 0.0739) |
| `wc_grass_share` | ESA WorldCover land-cover share: grass share | float64 | 0.0–0.437 (μ 0.0624) |
| `wc_other_share` | ESA WorldCover land-cover share: other share | float64 | 0.0–0.286 (μ 0.0218) |
| `wc_dominant_class` | ESA WorldCover land-cover share: dominant class | int64 | 10.0–80.0 (μ 43.1288) |
| `sig_total` | Road-network metric: sig total | int64 | 0.0–905.0 (μ 137.7822) |
| `sig_overhead` | Road-network metric: sig overhead | int64 | 0.0–82.0 (μ 14.5491) |
| `sig_ground` | Road-network metric: sig ground | int64 | 0.0–356.0 (μ 51.7945) |
| `sig_pedestrian` | Road-network metric: sig pedestrian | int64 | 0.0–266.0 (μ 39.7239) |
| `sig_beacon` | Road-network metric: sig beacon | int64 | 0.0–124.0 (μ 16.6074) |
| `sig_rag` | Road-network metric: sig rag | int64 | 0.0–64.0 (μ 6.1963) |
| `sig_filter_arrow` | Road-network metric: sig filter arrow | int64 | 0.0–81.0 (μ 8.1043) |
| `sig_bicycle` | Road-network metric: sig bicycle | int64 | 0.0–6.0 (μ 0.0982) |
| `ped_countdown` | Road-network metric: ped countdown | int64 | 0.0–64.0 (μ 4.7515) |
| `gtfs_headway_am_min` | Best AM-peak headway (lowest minutes between buses) at any stop in hex | float64 | 0.1–999.0 (μ 56.581) |
| `gtfs_headway_midday_min` | GTFS-derived transit service metric: headway midday min (weekday schedule) | float64 | 0.1–999.0 (μ 56.6687) |
| `gtfs_headway_pm_min` | GTFS-derived transit service metric: headway pm min (weekday schedule) | float64 | 0.1–999.0 (μ 56.6132) |
| `gtfs_headway_night_min` | GTFS-derived transit service metric: headway night min (weekday schedule) | float64 | 0.3–999.0 (μ 59.566) |
| `gtfs_dep_am` | GTFS-derived transit service metric: dep am (weekday schedule) | int64 | 0.0–7713.0 (μ 881.7301) |
| `gtfs_dep_midday` | GTFS-derived transit service metric: dep midday (weekday schedule) | int64 | 0.0–11218.0 (μ 1273.0706) |
| `gtfs_dep_pm` | GTFS-derived transit service metric: dep pm (weekday schedule) | int64 | 0.0–7682.0 (μ 866.5552) |
| `gtfs_dep_night` | GTFS-derived transit service metric: dep night (weekday schedule) | int64 | 0.0–8405.0 (μ 920.638) |
| `gtfs_daily_departures` | GTFS-derived transit service metric: daily departures (weekday schedule) | int64 | 0.0–68823.0 (μ 7759.5) |
| `gtfs_routes_served` | GTFS-derived transit service metric: routes served (weekday schedule) | int64 | 0.0–560.0 (μ 79.8037) |
| `gtfs_stops_with_service` | GTFS-derived transit service metric: stops with service (weekday schedule) | int64 | 0.0–88.0 (μ 16.2607) |
| `bus_taps_in_am` | Daily bus tap-ins in the am time window (LTA PV) | int64 | 0.0–435595.0 (μ 39221.7607) |
| `bus_taps_in_midday` | Daily bus tap-ins in the midday time window (LTA PV) | int64 | 0.0–389259.0 (μ 32587.7301) |
| `bus_taps_in_night` | Daily bus tap-ins in the night time window (LTA PV) | int64 | 0.0–131658.0 (μ 9894.1258) |
| `bus_taps_in_offpeak` | Daily bus tap-ins in the offpeak time window (LTA PV) | int64 | 0.0–1290054.0 (μ 104103.1135) |
| `bus_taps_in_pm` | Daily bus tap-ins in the pm time window (LTA PV) | int64 | 0.0–453383.0 (μ 38442.9294) |
| `bus_taps_out_am` | Daily bus tap-outs in the am time window (LTA PV) | int64 | 0.0–479735.0 (μ 40406.8221) |
| `bus_taps_out_midday` | Daily bus tap-outs in the midday time window (LTA PV) | int64 | 0.0–404576.0 (μ 31890.2239) |
| `bus_taps_out_night` | Daily bus tap-outs in the night time window (LTA PV) | int64 | 0.0–119151.0 (μ 11505.5859) |
| `bus_taps_out_offpeak` | Daily bus tap-outs in the offpeak time window (LTA PV) | int64 | 0.0–1243804.0 (μ 104248.7546) |
| `bus_taps_out_pm` | Daily bus tap-outs in the pm time window (LTA PV) | int64 | 0.0–438900.0 (μ 37183.8436) |
| `bus_taps_in_total` | Daily bus tap-ins in the total time window (LTA PV) | int64 | 0.0–2699949.0 (μ 224249.6595) |
| `bus_taps_out_total` | Daily bus tap-outs in the total time window (LTA PV) | int64 | 0.0–2686166.0 (μ 225235.2301) |
| `carpark_count_avail` | carpark count avail (see layer docs) | int64 | 0.0–74.0 (μ 7.9509) |
| `carpark_lots_avail` | carpark lots avail (see layer docs) | int64 | 0.0–14498.0 (μ 1572.8957) |
| `speed_band_count` | speed band count (see layer docs) | int64 | 0.0–1127.0 (μ 174.1871) |
| `speed_band_avg` | speed band avg (see layer docs) | float64 | 0.0–5.92 (μ 3.1079) |
| `jam_pct` | jam pct (see layer docs) | float64 | 0.0–60.72 (μ 20.7045) |
| `dyn_avg_speed_kmh` | dyn avg speed kmh (see layer docs) | float64 | 0.0–53.14 (μ 26.1779) |
| `retail_whitespace_score` | Retail white-space — unmet, winnable demand for a new store (0–100) | float64 | 0.0–78.1 (μ 35.3485) |
| `retail_competition_pressure` | Competition pressure from existing same-format retail (0–100) | float64 | 0.0–100.0 (μ 22.5393) |
| `format_fit_score` | Best-fit store format (kiosk→flagship) suitability (0–100) | float64 | 0.0–100.0 (μ 15.8678) |
| `retail_cannibalization_score` | Self-cannibalisation risk vs own-brand nearby outlets (0–100) | float64 | 0.0–100.0 (μ 16.2396) |
| `retail_delivery_score` | Dark-store / delivery viability (0–100) | float64 | 0.0–100.0 (μ 16.7256) |
| `retail_footfall_score` | Footfall / visit potential (0–100) | float64 | 0.0–100.0 (μ 28.5274) |
| `rent_demand_tier` | Demand-vs-rent tier (residential-rent proxy) | float64 | 0.0–100.0 (μ 56.1196) |
| `re_feasibility_score` | Development feasibility — FAR headroom × buildability (0–100) | float64 | 0.0–100.0 (μ 30.2974) |
| `re_livability_score` | Neighbourhood livability / quality (0–100) | float64 | 0.0–100.0 (μ 69.2941) |
| `re_momentum_score` | Momentum / gentrification signal (0–100) | float64 | 0.0–100.0 (μ 29.6485) |
| `re_enbloc_score` | En-bloc redevelopment upside (0–100) | float64 | 0.0–100.0 (μ 21.6604) |
| `re_collateral_score` | Mortgage collateral tier (0–100) | float64 | 3.4–100.0 (μ 47.2404) |
| `re_yield_proxy` | Rental-yield proxy (0–100) | float64 | 0.0–8.2 (μ 0.8859) |
| `re_lease_decay_penalty` | HDB lease-decay penalty (0–100) | float64 | 0.0–100.0 (μ 42.0) |
| `utility_load_score` | Relative electricity load (0–100) | float64 | 0.0–100.0 (μ 37.7896) |
| `utility_load_growth_score` | Projected load growth (0–100) | float64 | 0.0–100.0 (μ 34.1867) |
| `utility_water_score` | Water-demand estimate (0–100) | float64 | 0.0–100.0 (μ 31.9085) |
| `utility_waste_score` | Waste-generation estimate (0–100; ∝ population) | float64 | 0.0–100.0 (μ 30.4104) |
| `utility_ev_gap_score` | EV-charger provision gap (0–100) | float64 | 0.0–100.0 (μ 20.2074) |
| `utility_diurnal_swing` | Day/night load swing (0–100) | float64 | -100.0–500.0 (μ 62.66) |
| `utility_equity_score` | Infrastructure-equity priority (0–100) | float64 | 0.0–94.0 (μ 7.2956) |
| `utility_resilience_score` | Critical-customer resilience need (0–100) | float64 | 0.0–100.0 (μ 58.9819) |
| `mobility_access_score` | Transit / multimodal access (0–100; ≈ adequacy) | float64 | 0.0–100.0 (μ 67.903) |
| `mobility_desert_priority` | Transit-desert intervention priority (0–100) | float64 | 0.0–100.0 (μ 18.3556) |
| `mobility_crowding_score` | Network crowding stress (0–100) | float64 | 0.0–100.0 (μ 15.0978) |
| `mobility_tod_score` | Transit-oriented-development opportunity (0–100) | float64 | 0.0–100.0 (μ 10.4078) |
| `mobility_ridehail_score` | Ride-hail demand hotspot (0–100) | float64 | 0.0–100.0 (μ 2.3048) |
| `mobility_firstlast_gap_score` | First / last-mile gap (0–100) | float64 | 0.0–91.0 (μ 2.997) |
| `mobility_parking_stress` | Parking stress (0–100) | float64 | 0.0–100.0 (μ 19.3137) |
| `modal_split_proxy` | Public-transport modal-split proxy (0–100) | float64 | 0.0–100.0 (μ 22.1822) |
| `risk_fire_score` | Property / fire peril (0–100) | float64 | 0.0–100.0 (μ 12.6111) |
| `risk_auto_score` | Motor / auto exposure (0–100) | float64 | 0.0–100.0 (μ 15.1041) |
| `risk_health_score` | Life / health exposure (0–100) | float64 | 0.0–100.0 (μ 10.5533) |
| `risk_bi_failure_score` | Business-interruption risk (≈ biz_recent_dead_share) | float64 | 0.0–100.0 (μ 45.8222) |
| `risk_collateral_score` | Collateral-value risk tier (0–100) | float64 | 0.0–100.0 (μ 40.9904) |
| `risk_nuisance_score` | Nuisance / liability peril (0–100) | float64 | 0.0–100.0 (μ 22.4281) |
| `risk_coastal_proxy` | Coastal / flood proxy (weak; 0–100) | float64 | 0.0–57.0 (μ 5.8126) |
| `insurance_risk_score` | Blended underwriting risk score (0–100) | float64 | 0.0–100.0 (μ 43.2607) |
| `insurance_accumulation_band` | Accumulation / concentration band | float64 | 0.0–100.0 (μ 27.8319) |
| `pc2_total` | Fine-taxonomy place metric: total | int64 | 1.0–4639.0 (μ 584.5368) |
| `pc2_branded_count` | Fine-taxonomy place metric: branded count | int64 | 0.0–405.0 (μ 46.4018) |
| `pc2_unbranded_count` | Fine-taxonomy place metric: unbranded count | int64 | 1.0–4571.0 (μ 538.135) |
| `pc2_cat_biz_office_count` | Place count in cell: biz office (55-cat fine taxonomy) | int64 | 0.0–224.0 (μ 13.8098) |
| `pc2_cat_civic_community_count` | Place count in cell: civic community (55-cat fine taxonomy) | int64 | 0.0–16.0 (μ 1.9356) |
| `pc2_cat_civic_government_count` | Place count in cell: civic government (55-cat fine taxonomy) | int64 | 0.0–35.0 (μ 3.3865) |
| `pc2_cat_civic_nonprofit_count` | Place count in cell: civic nonprofit (55-cat fine taxonomy) | int64 | 0.0–136.0 (μ 7.3865) |
| `pc2_cat_civic_religious_count` | Place count in cell: civic religious (55-cat fine taxonomy) | int64 | 0.0–91.0 (μ 3.5276) |
| `pc2_cat_edu_preschool_count` | Place count in cell: edu preschool (55-cat fine taxonomy) | int64 | 0.0–82.0 (μ 8.092) |
| `pc2_cat_edu_primary_secondary_count` | Place count in cell: edu primary secondary (55-cat fine taxonomy) | int64 | 0.0–96.0 (μ 3.6012) |
| `pc2_cat_edu_specialty_count` | Place count in cell: edu specialty (55-cat fine taxonomy) | int64 | 0.0–12.0 (μ 0.7239) |
| `pc2_cat_edu_tertiary_count` | Place count in cell: edu tertiary (55-cat fine taxonomy) | int64 | 0.0–30.0 (μ 1.2515) |
| `pc2_cat_edu_tuition_count` | Place count in cell: edu tuition (55-cat fine taxonomy) | int64 | 0.0–138.0 (μ 15.7699) |
| `pc2_cat_food_bakery_count` | Place count in cell: food bakery (55-cat fine taxonomy) | int64 | 0.0–56.0 (μ 5.5982) |
| `pc2_cat_food_bar_count` | Place count in cell: food bar (55-cat fine taxonomy) | int64 | 0.0–63.0 (μ 2.5552) |
| `pc2_cat_food_cafe_count` | Place count in cell: food cafe (55-cat fine taxonomy) | int64 | 0.0–115.0 (μ 14.5613) |
| `pc2_cat_food_caterer_count` | Place count in cell: food caterer (55-cat fine taxonomy) | int64 | 0.0–21.0 (μ 0.5552) |
| `pc2_cat_food_dessert_count` | Place count in cell: food dessert (55-cat fine taxonomy) | int64 | 0.0–57.0 (μ 5.3712) |
| `pc2_cat_food_fast_food_count` | Place count in cell: food fast food (55-cat fine taxonomy) | int64 | 0.0–27.0 (μ 2.6104) |
| `pc2_cat_food_hawker_count` | Place count in cell: food hawker (55-cat fine taxonomy) | int64 | 0.0–201.0 (μ 17.816) |
| `pc2_cat_food_restaurant_count` | Place count in cell: food restaurant (55-cat fine taxonomy) | int64 | 0.0–400.0 (μ 29.0184) |
| `pc2_cat_health_clinic_count` | Place count in cell: health clinic (55-cat fine taxonomy) | int64 | 0.0–110.0 (μ 7.0031) |
| `pc2_cat_health_hospital_count` | Place count in cell: health hospital (55-cat fine taxonomy) | int64 | 0.0–50.0 (μ 0.9509) |
| `pc2_cat_health_pharmacy_count` | Place count in cell: health pharmacy (55-cat fine taxonomy) | int64 | 0.0–26.0 (μ 2.3344) |
| `pc2_cat_health_specialist_count` | Place count in cell: health specialist (55-cat fine taxonomy) | int64 | 0.0–148.0 (μ 5.8712) |
| `pc2_cat_health_tcm_count` | Place count in cell: health tcm (55-cat fine taxonomy) | int64 | 0.0–16.0 (μ 1.5859) |
| `pc2_cat_leisure_entertainment_count` | Place count in cell: leisure entertainment (55-cat fine taxonomy) | int64 | 0.0–25.0 (μ 1.9049) |
| `pc2_cat_leisure_park_count` | Place count in cell: leisure park (55-cat fine taxonomy) | int64 | 0.0–80.0 (μ 11.1472) |
| `pc2_cat_leisure_tourist_count` | Place count in cell: leisure tourist (55-cat fine taxonomy) | int64 | 0.0–62.0 (μ 2.7362) |
| `pc2_cat_other_count` | Place count in cell: other (55-cat fine taxonomy) | int64 | 0.0–1114.0 (μ 118.9601) |
| `pc2_cat_res_aged_care_count` | Place count in cell: res aged care (55-cat fine taxonomy) | int64 | 0.0–12.0 (μ 1.1135) |
| `pc2_cat_res_hdb_count` | Place count in cell: res hdb (55-cat fine taxonomy) | int64 | 0.0–204.0 (μ 20.6626) |
| `pc2_cat_res_private_count` | Place count in cell: res private (55-cat fine taxonomy) | int64 | 0.0–197.0 (μ 14.5276) |
| `pc2_cat_retail_apparel_count` | Place count in cell: retail apparel (55-cat fine taxonomy) | int64 | 0.0–199.0 (μ 8.1104) |
| `pc2_cat_retail_convenience_count` | Place count in cell: retail convenience (55-cat fine taxonomy) | int64 | 0.0–136.0 (μ 15.7791) |
| `pc2_cat_retail_electronics_count` | Place count in cell: retail electronics (55-cat fine taxonomy) | int64 | 0.0–67.0 (μ 3.4294) |
| `pc2_cat_retail_furniture_home_count` | Place count in cell: retail furniture home (55-cat fine taxonomy) | int64 | 0.0–151.0 (μ 9.2086) |
| `pc2_cat_retail_general_count` | Place count in cell: retail general (55-cat fine taxonomy) | int64 | 0.0–119.0 (μ 12.2025) |
| `pc2_cat_retail_jewelry_cosmetics_count` | Place count in cell: retail jewelry cosmetics (55-cat fine taxonomy) | int64 | 0.0–203.0 (μ 4.8865) |
| `pc2_cat_retail_mall_count` | Place count in cell: retail mall (55-cat fine taxonomy) | int64 | 0.0–23.0 (μ 1.4724) |
| `pc2_cat_retail_supermarket_count` | Place count in cell: retail supermarket (55-cat fine taxonomy) | int64 | 0.0–55.0 (μ 6.2362) |
| `pc2_cat_service_automotive_count` | Place count in cell: service automotive (55-cat fine taxonomy) | int64 | 0.0–508.0 (μ 11.635) |
| `pc2_cat_service_beauty_count` | Place count in cell: service beauty (55-cat fine taxonomy) | int64 | 0.0–265.0 (μ 21.7638) |
| `pc2_cat_service_cleaning_repair_count` | Place count in cell: service cleaning repair (55-cat fine taxonomy) | int64 | 0.0–66.0 (μ 3.9479) |
| `pc2_cat_service_consulting_count` | Place count in cell: service consulting (55-cat fine taxonomy) | int64 | 0.0–751.0 (μ 38.3466) |
| `pc2_cat_service_fitness_count` | Place count in cell: service fitness (55-cat fine taxonomy) | int64 | 0.0–65.0 (μ 9.4387) |
| `pc2_cat_service_legal_finance_count` | Place count in cell: service legal finance (55-cat fine taxonomy) | int64 | 0.0–230.0 (μ 8.7975) |
| `pc2_cat_service_logistics_count` | Place count in cell: service logistics (55-cat fine taxonomy) | int64 | 0.0–573.0 (μ 39.4479) |
| `pc2_cat_service_other_count` | Place count in cell: service other (55-cat fine taxonomy) | int64 | 0.0–584.0 (μ 25.727) |
| `pc2_cat_service_pet_count` | Place count in cell: service pet (55-cat fine taxonomy) | int64 | 0.0–13.0 (μ 1.0123) |
| `pc2_cat_service_real_estate_count` | Place count in cell: service real estate (55-cat fine taxonomy) | int64 | 0.0–112.0 (μ 3.3558) |
| `pc2_cat_transport_air_count` | Place count in cell: transport air (55-cat fine taxonomy) | int64 | 0.0–26.0 (μ 0.2853) |
| `pc2_cat_transport_bus_count` | Place count in cell: transport bus (55-cat fine taxonomy) | int64 | 0.0–62.0 (μ 11.4847) |
| `pc2_cat_transport_ev_count` | Place count in cell: transport ev (55-cat fine taxonomy) | int64 | 0.0–58.0 (μ 8.1902) |
| `pc2_cat_transport_mrt_count` | Place count in cell: transport mrt (55-cat fine taxonomy) | int64 | 0.0–11.0 (μ 1.4877) |
| `pc2_cat_transport_other_count` | Place count in cell: transport other (55-cat fine taxonomy) | int64 | 0.0–13.0 (μ 0.8988) |
| `pc2_cat_transport_parking_count` | Place count in cell: transport parking (55-cat fine taxonomy) | int64 | 0.0–64.0 (μ 8.2423) |
| `pc2_cat_unmapped_count` | Place count in cell: unmapped (55-cat fine taxonomy) | int64 | 0.0–84.0 (μ 2.7822) |
| `pc2_dominant_category` | Fine-taxonomy place metric: dominant category | object | e.g. other |
| `mg_bakery_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for bakery | float64 | 0.0–39.8 (μ 5.1398) |
| `mg_bar_nightlife_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for bar nightlife | float64 | 0.0–23.256 (μ 0.9243) |
| `mg_beauty_personal_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for beauty personal | float64 | 0.0–103.868 (μ 6.9841) |
| `mg_business_office_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for business office | float64 | 0.0–210.207 (μ 13.6028) |
| `mg_cafe_coffee_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for cafe coffee | float64 | 0.0–35.492 (μ 5.468) |
| `mg_convenience_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for convenience | float64 | 0.0–26.231 (μ 4.2629) |
| `mg_education_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for education | float64 | 0.0–55.782 (μ 4.8288) |
| `mg_entertainment_culture_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for entertainment culture | float64 | 0.0–18.111 (μ 0.7744) |
| `mg_fast_food_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for fast food | float64 | 0.0–104.5 (μ 10.0553) |
| `mg_fitness_recreation_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for fitness recreation | float64 | 0.0–22.14 (μ 1.3294) |
| `mg_government_public_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for government public | float64 | 0.0–11.176 (μ 0.692) |
| `mg_hawker_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for hawker | float64 | 0.0–120.529 (μ 14.1877) |
| `mg_health_medical_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for health medical | float64 | 0.0–113.343 (μ 5.16) |
| `mg_hotel_hospitality_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for hotel hospitality | float64 | 0.0–42.369 (μ 0.9698) |
| `mg_industrial_mfg_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for industrial mfg | float64 | 0.0–77.843 (μ 8.8949) |
| `mg_other_uncategorized_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for other uncategorized | float64 | 0.0–0.0 (μ 0.0) |
| `mg_park_open_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for park open | float64 | 0.0–7.364 (μ 0.9172) |
| `mg_religious_worship_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for religious worship | float64 | 0.0–11.436 (μ 0.8188) |
| `mg_residential_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for residential | float64 | 0.0–15.721 (μ 2.9595) |
| `mg_restaurant_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for restaurant | float64 | 0.0–128.087 (μ 16.9372) |
| `mg_services_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for services | float64 | 0.0–177.692 (μ 13.2109) |
| `mg_shopping_retail_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for shopping retail | float64 | 0.0–101.153 (μ 12.297) |
| `mg_supermarket_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for supermarket | float64 | 0.0–32.742 (μ 3.9794) |
| `mg_transportation_pressure_400m` | Magnet model: 400 m distance-decayed SAME-category competitive pressure for transportation | float64 | 0.0–21.614 (μ 3.6032) |
| `mg_bakery_support_400m` | Magnet model: complementary-category support density within 400 m for bakery (demand context, not supply) | float64 | 0.0–208.0 (μ 21.2663) |
| `mg_bar_nightlife_support_400m` | Magnet model: complementary-category support density within 400 m for bar nightlife (demand context, not supply) | float64 | 0.0–91.372 (μ 8.1114) |
| `mg_beauty_personal_support_400m` | Magnet model: complementary-category support density within 400 m for beauty personal (demand context, not supply) | float64 | 0.0–199.378 (μ 21.8048) |
| `mg_business_office_support_400m` | Magnet model: complementary-category support density within 400 m for business office (demand context, not supply) | float64 | 0.0–269.812 (μ 24.005) |
| `mg_cafe_coffee_support_400m` | Magnet model: complementary-category support density within 400 m for cafe coffee (demand context, not supply) | float64 | 0.0–168.045 (μ 23.2711) |
| `mg_convenience_support_400m` | Magnet model: complementary-category support density within 400 m for convenience (demand context, not supply) | float64 | 0.0–33.5 (μ 6.781) |
| `mg_education_support_400m` | Magnet model: complementary-category support density within 400 m for education (demand context, not supply) | float64 | 0.0–37.811 (μ 5.736) |
| `mg_entertainment_culture_support_400m` | Magnet model: complementary-category support density within 400 m for entertainment culture (demand context, not supply) | float64 | 0.0–92.0 (μ 5.5003) |
| `mg_fast_food_support_400m` | Magnet model: complementary-category support density within 400 m for fast food (demand context, not supply) | float64 | 0.0–144.5 (μ 15.076) |
| `mg_fitness_recreation_support_400m` | Magnet model: complementary-category support density within 400 m for fitness recreation (demand context, not supply) | float64 | 0.0–153.75 (μ 11.4846) |
| `mg_government_public_support_400m` | Magnet model: complementary-category support density within 400 m for government public (demand context, not supply) | float64 | 0.0–182.062 (μ 11.6401) |
| `mg_hawker_support_400m` | Magnet model: complementary-category support density within 400 m for hawker (demand context, not supply) | float64 | 0.0–42.135 (μ 7.6654) |
| `mg_health_medical_support_400m` | Magnet model: complementary-category support density within 400 m for health medical (demand context, not supply) | float64 | 0.0–157.474 (μ 11.4273) |
| `mg_hotel_hospitality_support_400m` | Magnet model: complementary-category support density within 400 m for hotel hospitality (demand context, not supply) | float64 | 0.0–98.68 (μ 6.3291) |
| `mg_industrial_mfg_support_400m` | Magnet model: complementary-category support density within 400 m for industrial mfg (demand context, not supply) | float64 | 0.0–422.128 (μ 27.6518) |
| `mg_other_uncategorized_support_400m` | Magnet model: complementary-category support density within 400 m for other uncategorized (demand context, not supply) | float64 | 0.0–0.0 (μ 0.0) |
| `mg_park_open_support_400m` | Magnet model: complementary-category support density within 400 m for park open (demand context, not supply) | float64 | 0.0–81.5 (μ 6.87) |
| `mg_religious_worship_support_400m` | Magnet model: complementary-category support density within 400 m for religious worship (demand context, not supply) | float64 | 0.0–17.0 (μ 1.9008) |
| `mg_residential_support_400m` | Magnet model: complementary-category support density within 400 m for residential (demand context, not supply) | float64 | 0.0–48.667 (μ 5.3141) |
| `mg_restaurant_support_400m` | Magnet model: complementary-category support density within 400 m for restaurant (demand context, not supply) | float64 | 0.0–95.404 (μ 11.0315) |
| `mg_services_support_400m` | Magnet model: complementary-category support density within 400 m for services (demand context, not supply) | float64 | 0.0–252.779 (μ 22.6362) |
| `mg_shopping_retail_support_400m` | Magnet model: complementary-category support density within 400 m for shopping retail (demand context, not supply) | float64 | 0.0–165.614 (μ 19.2249) |
| `mg_supermarket_support_400m` | Magnet model: complementary-category support density within 400 m for supermarket (demand context, not supply) | float64 | 0.0–169.0 (μ 14.1141) |
| `mg_transportation_support_400m` | Magnet model: complementary-category support density within 400 m for transportation (demand context, not supply) | float64 | 0.0–237.159 (μ 20.5023) |
| `mg_bakery_anchor_strength` | Magnet model: strength of the biggest bakery anchor place nearby | float64 | 0.0–1103.76 (μ 68.3285) |
| `mg_bar_nightlife_anchor_strength` | Magnet model: strength of the biggest bar nightlife anchor place nearby | float64 | 0.0–214.617 (μ 18.3208) |
| `mg_beauty_personal_anchor_strength` | Magnet model: strength of the biggest beauty personal anchor place nearby | float64 | 0.0–895.955 (μ 70.9227) |
| `mg_business_office_anchor_strength` | Magnet model: strength of the biggest business office anchor place nearby | float64 | 0.0–327.893 (μ 22.9059) |
| `mg_cafe_coffee_anchor_strength` | Magnet model: strength of the biggest cafe coffee anchor place nearby | float64 | 0.0–1117.662 (μ 92.4653) |
| `mg_convenience_anchor_strength` | Magnet model: strength of the biggest convenience anchor place nearby | float64 | 0.0–78.349 (μ 10.4346) |
| `mg_education_anchor_strength` | Magnet model: strength of the biggest education anchor place nearby | float64 | 0.0–19.713 (μ 1.7651) |
| `mg_entertainment_culture_anchor_strength` | Magnet model: strength of the biggest entertainment culture anchor place nearby | float64 | 0.0–730.922 (μ 43.6543) |
| `mg_fast_food_anchor_strength` | Magnet model: strength of the biggest fast food anchor place nearby | float64 | 0.0–1152.151 (μ 66.1408) |
| `mg_fitness_recreation_anchor_strength` | Magnet model: strength of the biggest fitness recreation anchor place nearby | float64 | 0.0–921.263 (μ 46.8929) |
| `mg_government_public_anchor_strength` | Magnet model: strength of the biggest government public anchor place nearby | float64 | 0.0–66.329 (μ 5.5896) |
| `mg_hawker_anchor_strength` | Magnet model: strength of the biggest hawker anchor place nearby | float64 | 0.0–69.595 (μ 7.8559) |
| `mg_health_medical_anchor_strength` | Magnet model: strength of the biggest health medical anchor place nearby | float64 | 0.0–72.521 (μ 8.091) |
| `mg_hotel_hospitality_anchor_strength` | Magnet model: strength of the biggest hotel hospitality anchor place nearby | float64 | 0.0–856.17 (μ 49.7212) |
| `mg_industrial_mfg_anchor_strength` | Magnet model: strength of the biggest industrial mfg anchor place nearby | float64 | 0.0–209.603 (μ 15.7735) |
| `mg_other_uncategorized_anchor_strength` | Magnet model: strength of the biggest other uncategorized anchor place nearby | float64 | 0.0–0.0 (μ 0.0) |
| `mg_park_open_anchor_strength` | Magnet model: strength of the biggest park open anchor place nearby | float64 | 0.0–13.262 (μ 1.2933) |
| `mg_religious_worship_anchor_strength` | Magnet model: strength of the biggest religious worship anchor place nearby | float64 | 0.0–23.572 (μ 1.4746) |
| `mg_residential_anchor_strength` | Magnet model: strength of the biggest residential anchor place nearby | float64 | 0.0–655.238 (μ 38.8704) |
| `mg_restaurant_anchor_strength` | Magnet model: strength of the biggest restaurant anchor place nearby | float64 | 0.0–928.002 (μ 82.5768) |
| `mg_services_anchor_strength` | Magnet model: strength of the biggest services anchor place nearby | float64 | 0.0–934.166 (μ 72.769) |
| `mg_shopping_retail_anchor_strength` | Magnet model: strength of the biggest shopping retail anchor place nearby | float64 | 0.0–1029.621 (μ 79.5007) |
| `mg_supermarket_anchor_strength` | Magnet model: strength of the biggest supermarket anchor place nearby | float64 | 0.0–25.926 (μ 1.896) |
| `mg_transportation_anchor_strength` | Magnet model: strength of the biggest transportation anchor place nearby | float64 | 0.0–932.972 (μ 53.7179) |
| `mg_avg_competitors_400m` | Magnet model: mean same-category competitor count within 400 m across categories | float64 | 0.0–124.374 (μ 12.155) |
| `mg_avg_anchor_strength` | Magnet model: strength of the biggest avg anchor place nearby | float64 | 0.0–632.758 (μ 49.9264) |
| `mg_avg_walk_dist_mrt_m` | Magnet model: mean walk distance to MRT across category micrographs | float64 | 143.023–9999.0 (μ 2283.1408) |
| `pc_total` | Total mapped places (POIs) in cell — overall point-of-interest density | int64 | 1.0–4639.0 (μ 584.5368) |
| `pc_unique_brands` | Distinct retail/F&B brands present — chain richness | int64 | 0.0–348.0 (μ 44.8405) |
| `pc_magnets` | High-draw anchor places (malls, hubs, 30+ review demand magnets) | int64 | 0.0–747.0 (μ 66.1534) |
| `pc_long_tail` | Places with few/no reviews — independent long-tail share base | int64 | 1.0–2962.0 (μ 332.3681) |
| `pc_with_rating` | Places carrying a Google rating | int64 | 0.0–2345.0 (μ 335.546) |
| `pc_total_reviews` | Sum of review counts — popularity/footfall proxy | int64 | 0.0–609314.0 (μ 59852.9202) |
| `pc_avg_rating` | Mean rating of rated places — quality proxy | float64 | 0.0–4.87 (μ 4.3979) |
| `pc_cat_bakery` | Place count in cell: bakery category (24-cat taxonomy) | int64 | 0.0–64.0 (μ 6.2515) |
| `pc_cat_bar_nightlife` | Place count in cell: bar nightlife category (24-cat taxonomy) | int64 | 0.0–79.0 (μ 3.4356) |
| `pc_cat_beauty_personal` | Place count in cell: beauty personal category (24-cat taxonomy) | int64 | 0.0–304.0 (μ 23.8252) |
| `pc_cat_business_office` | Place count in cell: business office category (24-cat taxonomy) | int64 | 0.0–1205.0 (μ 66.2331) |
| `pc_cat_cafe_coffee` | Place count in cell: cafe coffee category (24-cat taxonomy) | int64 | 0.0–170.0 (μ 19.9969) |
| `pc_cat_convenience` | Place count in cell: convenience category (24-cat taxonomy) | int64 | 0.0–55.0 (μ 6.638) |
| `pc_cat_education` | Place count in cell: education category (24-cat taxonomy) | int64 | 0.0–280.0 (μ 34.2791) |
| `pc_cat_entertainment_culture` | Place count in cell: entertainment culture category (24-cat taxonomy) | int64 | 0.0–107.0 (μ 6.6595) |
| `pc_cat_fast_food` | Place count in cell: fast food category (24-cat taxonomy) | int64 | 0.0–27.0 (μ 2.8773) |
| `pc_cat_fitness_recreation` | Place count in cell: fitness recreation category (24-cat taxonomy) | int64 | 0.0–85.0 (μ 12.3374) |
| `pc_cat_government_public` | Place count in cell: government public category (24-cat taxonomy) | int64 | 0.0–51.0 (μ 5.9325) |
| `pc_cat_hawker` | Place count in cell: hawker category (24-cat taxonomy) | int64 | 0.0–202.0 (μ 18.0736) |
| `pc_cat_health_medical` | Place count in cell: health medical category (24-cat taxonomy) | int64 | 0.0–417.0 (μ 22.862) |
| `pc_cat_hotel_hospitality` | Place count in cell: hotel hospitality category (24-cat taxonomy) | int64 | 0.0–93.0 (μ 3.6074) |
| `pc_cat_industrial_mfg` | Place count in cell: industrial mfg category (24-cat taxonomy) | int64 | 0.0–910.0 (μ 55.0736) |
| `pc_cat_other_uncategorized` | Place count in cell: other uncategorized category (24-cat taxonomy) | int64 | 0.0–103.0 (μ 10.4049) |
| `pc_cat_park_open` | Place count in cell: park open category (24-cat taxonomy) | int64 | 0.0–89.0 (μ 13.592) |
| `pc_cat_religious_worship` | Place count in cell: religious worship category (24-cat taxonomy) | int64 | 0.0–133.0 (μ 5.3037) |
| `pc_cat_residential` | Place count in cell: residential category (24-cat taxonomy) | int64 | 0.0–523.0 (μ 49.911) |
| `pc_cat_restaurant` | Place count in cell: restaurant category (24-cat taxonomy) | int64 | 0.0–493.0 (μ 34.6135) |
| `pc_cat_services` | Place count in cell: services category (24-cat taxonomy) | int64 | 0.0–1148.0 (μ 69.6043) |
| `pc_cat_shopping_retail` | Place count in cell: shopping retail category (24-cat taxonomy) | int64 | 0.0–646.0 (μ 47.1564) |
| `pc_cat_supermarket` | Place count in cell: supermarket category (24-cat taxonomy) | int64 | 0.0–67.0 (μ 9.0153) |
| `pc_cat_transportation` | Place count in cell: transportation category (24-cat taxonomy) | int64 | 0.0–242.0 (μ 39.5736) |
| `pc_cat_financial_services` | Count of financial venues in cell (ATM/bank/insurance/remittance) | int64 | 0.0–177.0 (μ 11.411) |
| `pc_cat_automated_kiosk` | Count of unmanned automated points (vending/locker/AXS) in cell | int64 | 0.0–42.0 (μ 5.8681) |
| `pc_diversity` | Category entropy of the place mix — high = mixed-use | float64 | -0.0–2.943 (μ 2.5129) |
| `pc_dominant_category` | Most common place category in cell | object | e.g. beauty_personal |

## sgp_places_final (36 cols)

| Column | Description | Type | Range/μ or sample |
|---|---|---|---|
| `id` | Place ID (string hash) | object | e.g. c5Wl6sW53JSX |
| `name` | Place name | object | e.g. Golden Hill Landscape Pte. Ltd. |
| `primary_category` | Original Google Maps category | object | e.g. Landscape Design |
| `brand` | Raw brand string of the place (pre-normalisation) | object | 251 unique |
| `rating` | Google Maps rating (0–5) | float64 | 1.0–5.0 (μ 4.326) |
| `reviews_count` | Google Maps reviews count | int64 | 0.0–110870.0 (μ 102.3962) |
| `latitude` | Place latitude (WGS84) | float64 | 1.16–1.4709 (μ 1.3386) |
| `longitude` | Place longitude (WGS84) | float64 | 103.6102–104.09 (μ 103.8382) |
| `hex9_id` | H3 resolution-9 cell ID (~0.105 km², 174m edge) | object | e.g. 896520c95a7ffff |
| `hex8_id` | H3 resolution-8 cell ID (~0.737 km², 461m edge) | object | e.g. 886520c95bfffff |
| `parent_subzone_c` | URA subzone code of parent | object | e.g. LKSZ01 |
| `parent_subzone_name` | URA subzone full name | object | e.g. LIM CHU KANG |
| `parent_subzone_source` | How the place→subzone attach was resolved (bookkeeping) | object | e.g. contains |
| `parent_pa` | URA planning area name (one of 55) | object | e.g. LIM CHU KANG |
| `parent_region` | URA region (5 regions) | object | e.g. NORTH REGION |
| `hdb_town` | hdb town (see layer docs) | object | e.g. BUKIT BATOK |
| `in_sgp` | Place lies within Singapore boundary (QA flag) | bool | e.g. True |
| `plexis_category` | Resolved 24-category Plexis taxonomy | object | e.g. services |
| `brand_norm` | Normalized brand name | object | e.g. Osia |
| `brand_source` | scrape | name_pattern | object | e.g. llm |
| `has_rating` | Place carries a Google rating | bool | e.g. True |
| `has_reviews` | Place carries at least one review | bool | e.g. True |
| `review_bucket` | Review-volume tier of the place | object | e.g. 1-9 |
| `magnet_strength` | rating × log(reviews+1) | float64 | 0.6931–55.0577 (μ 14.0269) |
| `review_quality_pctl_in_cat` | magnet_strength percentile within category | float64 | 0.0006–1.0 (μ 0.5001) |
| `is_magnet` | rating ≥ 4 AND reviews ≥ 100 | bool | e.g. False |
| `is_long_tail` | reviews < 5 OR no rating | bool | e.g. False |
| `is_storefront` | True = manned commercial premise; False = unmanned (ATM/vending/locker) or pure transit infra | bool | e.g. True |
| `operator_name` | Operator name | object | e.g. Golden Hill Landscape Pte. Ltd. |
| `host_venue` | Venue this place sits inside (co-located tenant), else empty | object | 4361 unique |
| `parent_brand` | Operator brand for stalls inside a food court / coffeeshop | object | 32 unique |
| `is_duplicate` | True = a duplicate/alias of canonical_id (filter out for supply counts) | bool | e.g. False |
| `canonical_id` | The canonical place id this row maps to | object | e.g. c5Wl6sW53JSX |
| `zero_reviews` | True if reviews_count == 0 (new/unlisted vs no-traffic — ambiguous) | bool | e.g. False |
| `is_phantom_suspect` | Duplicate with 0 reviews — likely phantom/alias | bool | e.g. False |
| `operator` | Food-court / coffeeshop operator above the stall (parent_brand) | object | 13 unique |

## sgp_places_micrograph (20 cols)

| Column | Description | Type | Range/μ or sample |
|---|---|---|---|
| `id` | Place ID (string hash) | object | e.g. c5Wl6sW53JSX |
| `pmg_competitors_400m` | SAME-category places within 400 m of this place | int32 | 0.0–476.0 (μ 20.4374) |
| `pmg_competitors_800m` | SAME-category places within 800 m | int32 | 0.0–1381.0 (μ 69.2194) |
| `pmg_closest_competitor_m` | Distance to the nearest same-category place | float32 | 0.505–9999.0 (μ 1387.8237) |
| `pmg_competitor_rating_avg` | Mean rating of nearby competitors — incumbent quality bar | float32 | 0.0–5.0 (μ 3.712) |
| `pmg_complements_400m` | Complementary-category places within 400 m (demand context) | int32 | 0.0–814.0 (μ 31.8176) |
| `pmg_complements_800m` | Complementary-category places within 800 m | int32 | 0.0–2362.0 (μ 125.2291) |
| `pmg_complement_categories_present` | Distinct complementary categories present within 400 m | int32 | 0.0–5.0 (μ 2.6167) |
| `pmg_complement_diversity` | Entropy of the complementary mix around the place | float32 | 0.0–1.587 (μ 0.703) |
| `pmg_anchors_400m` | Magnet/anchor places within 400 m | int32 | 0.0–78.0 (μ 2.6241) |
| `pmg_anchors_800m` | Magnet/anchor places within 800 m | int32 | 0.0–260.0 (μ 9.8655) |
| `pmg_closest_anchor_m` | Distance to the nearest anchor place | float32 | 1.208–9999.0 (μ 4011.01) |
| `pmg_anchor_strength_sum` | Summed anchor strength in the place's neighbourhood | float32 | 0.0–2110.5559 (μ 84.9436) |
| `pmg_walk_dist_mrt_m` | Walk distance from the place to nearest MRT/LRT | float32 | 0.609–9999.0 (μ 1564.7184) |
| `pmg_walk_dist_bus_m` | Walk distance to nearest bus stop | float32 | 0.111–9999.0 (μ 452.7582) |
| `pmg_near_mrt_400m` | MRT within 400 m of the place | int8 | 0.0–1.0 (μ 0.2003) |
| `pmg_near_bus_300m` | Bus stop within 300 m of the place | int8 | 0.0–1.0 (μ 0.4685) |
| `pmg_snap_delta_m` | Geocode-to-network snap distance (QA) | float32 | 0.025–10188.8242 (μ 35.3392) |
| `pmg_hex_walk_score` | Walkability score of the place's hex (context copy) | float64 | 0.0–0.959 (μ 0.7539) |
| `pmg_hex_transit_score` | Transit score of the place's hex (context copy) | float64 | 0.0–0.988 (μ 0.6934) |
