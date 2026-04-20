# Digital Atlas SGP — Data Catalog

**Generated:** 2026-03-26 10:14
**Total files:** 193
**Total size:** 2.6 GB

---

## Places & POIs (763.1 MB, 26 files)

| File | Size | Records | Columns | Key Fields |
|------|------|---------|---------|------------|
| `data/places_consolidated/sgp_places_final.jsonl` | 98.3 MB | 175,627 | 19 | id, ov_id, name, address, latitude |
| `data/places_consolidated/sgp_places_consolidated.jsonl` | 96.9 MB | 175,627 | 19 | id, ov_id, name, address, latitude |
| `data/results/sgp_places_curated.jsonl` | 96.5 MB | 79,257 | 3 | place_id, status, candidates |
| `data/places_consolidated/sgp_places_v2.jsonl` | 83.1 MB | 174,713 | 18 | id, name, address, latitude, longitude |
| `data/places_consolidated/sgp_places_enriched.jsonl` | 74.8 MB | 174,713 | 16 | id, name, address, latitude, longitude |
| `data/places_consolidated/sgp_places_clean.jsonl` | 74.7 MB | 174,713 | 16 | id, name, address, latitude, longitude |
| `data/results/sgp_places_final.jsonl` | 44.4 MB | 68,269 | 15 | id, name, address, latitude, longitude |
| `data/results/sgp_places_deduped.jsonl` | 43.5 MB | 68,269 | 15 | place_id, name, lat, lon, geohash9 |
| `data/places/sgp_places.jsonl` | 33.2 MB | 66,851 | 16 | id, name, address, latitude, longitude |
| `data/results/sgp_places_kepler.geojson` | 26.1 MB | 66,851 | 10 | id, name, main_category, place_type, sub_category |
| `data/overture_places_2025/sgp_places.parquet` | 26.0 MB | 147,501 | 17 | id, geometry, categories, confidence, websites |
| `data/results/sgp_places.jsonl` | 24.5 MB | 66,851 | 11 | id, name, address, latitude, longitude |
| `data/results/sgp_places_kepler.csv` | 11.1 MB | 66,851 | 12 | id, name, latitude, longitude, main_category |
| `data/osm_pois/amenities.geojson` | 9.5 MB | 28,888 | 12 | element, id, name, amenity, shop |
| `data/places_consolidated/needs_llm_classification.jsonl` | 7.9 MB | 53,597 | 5 | id, name, ov_category, address, brand |
| `data/places_consolidated/llm_classified.jsonl` | 4.7 MB | 53,584 | 3 | id, main_category, place_type |
| `data/osm_pois/leisure.geojson` | 4.2 MB | 12,552 | 12 | element, id, name, amenity, shop |
| `data/osm_pois/shops.geojson` | 2.9 MB | 8,667 | 12 | element, id, name, amenity, shop |
| `data/osm_pois/tourism.geojson` | 855 KB | 2,641 | 11 | element, id, name, amenity, shop |
| `data/places/sgp_brands.jsonl` | 32 KB | 233 | 5 | brand, parent, locations, primary_category, primary_place_type |
| `data/results/sgp_brands.jsonl` | 32 KB | 233 | 5 | brand, parent, locations, primary_category, primary_place_type |
| `data/results/sgp_boundary.geojson` | 14 KB | 1 | 2 | GID_0, COUNTRY |
| `data/places_consolidated/classify.log` | 5 KB | — | — | — |
| `data/places_consolidated/tier.log` | 3 KB | — | — | — |
| `data/places_consolidated/enrich.log` | 3 KB | — | — | — |
| `data/overture_places_2025/sgp_places.parquet.state` | 0 KB | — | — | — |

## Boundaries & Geography (5.0 MB, 2 files)

| File | Size | Records | Columns | Key Fields |
|------|------|---------|---------|------------|
| `data/boundaries/subzones.geojson` | 3.0 MB | 332 | 13 | OBJECTID, SUBZONE_NO, SUBZONE_N, SUBZONE_C, CA_IND |
| `data/boundaries/planning_areas.geojson` | 2.0 MB | 55 | 10 | OBJECTID, PLN_AREA_N, PLN_AREA_C, CA_IND, REGION_N |

## Demographics & Population (34.7 MB, 15 files)

| File | Size | Records | Columns | Key Fields |
|------|------|---------|---------|------------|
| `data/demographics/pop_age_sex_fa_2020_2024.csv` | 16.9 MB | 315,400 | 7 | PA, SZ, AG, Sex, FA |
| `data/demographics/pop_age_sex_tod_2025.csv` | 6.8 MB | 100,928 | 7 | PA, SZ, AG, Sex, TOD |
| `data/demographics/pop_age_sex_tod_2024.csv` | 6.8 MB | 100,928 | 7 | ﻿PA, SZ, AG, Sex, TOD |
| `data/demographics/pop_age_sex_fa_2025.csv` | 3.4 MB | 63,080 | 7 | PA, SZ, AG, Sex, FA |
| `data/demographics/dwellings_subzone_2020_2024.csv` | 332 KB | 8,300 | 5 | PA, SZ, FA, HSE, Time |
| `data/population/sgp_population_2020.tif` | 200 KB | — | — | — |
| `data/census/pop_age_floor_area.csv` | 145 KB | 388 | 121 | Number, Total1_Total, Total1_0_4, Total1_5_9, Total1_10_14 |
| `data/census/pop_age_sex.csv` | 84 KB | 388 | 61 | Number, Total_Total, Total_0_4, Total_5_9, Total_10_14 |
| `data/demographics/dwellings_subzone_2025.csv` | 67 KB | 1,660 | 5 | PA, SZ, FA, HSE, Time |
| `data/census/pop_ethnic_sex.csv` | 27 KB | 388 | 16 | Number, Total_Total, Total_Males, Total_Females, Chinese_Total |
| `data/census/pop_dwelling.csv` | 17 KB | 388 | 10 | Number, Total, HDBDwellings_Total, HDBDwellings_1_and2_RoomFlats1, HDBDwellings_3_RoomFlats |
| `data/population/sgp_pop_1km_2020.tif` | 5 KB | — | — | — |
| `data/census/hh_income.csv` | 4 KB | 32 | 21 | Number, Total, NoEmployedPerson, Below_1_000, 1_000_1_999 |
| `data/census/hh_dwelling.csv` | 2 KB | 32 | 10 | Number, Total, HDBDwellings_Total, HDBDwellings_1_and2_RoomFlats1, HDBDwellings_3_RoomFlats |
| `data/census/hh_size.csv` | 2 KB | 32 | 10 | Number, Total, 1Person, 2Persons, 3Persons |

## Housing & Property (140.7 MB, 6 files)

| File | Size | Records | Columns | Key Fields |
|------|------|---------|---------|------------|
| `data/housing/hdb_existing_buildings.geojson` | 54.0 MB | 13,386 | 9 | OBJECTID, BLK_NO, ST_COD, ENTITYID, POSTAL_COD |
| `data/property/private_resi_transactions.csv` | 21.6 MB | 287,196 | 10 | month, town, flat_type, block, street_name |
| `data/property/hdb_resale_prices.csv` | 21.4 MB | 227,207 | 11 | month, town, flat_type, block, street_name |
| `data/property/hdb_resale_prices_latest.csv` | 21.4 MB | 227,207 | 11 | month, town, flat_type, block, street_name |
| `data/housing/hdb_resale_2017_onwards.csv` | 21.4 MB | 226,743 | 11 | month, town, flat_type, block, street_name |
| `data/housing/hdb_property_info.csv` | 918 KB | 13,267 | 24 | blk_no, street, max_floor_lvl, year_completed, residential |

## Transit & Mobility (41.8 MB, 24 files)

| File | Size | Records | Columns | Key Fields |
|------|------|---------|---------|------------|
| `data/transit/rail_lines.geojson` | 22.2 MB | 1,366 | 6 | OBJECTID, GRND_LEVEL, RAIL_TYPE, INC_CRC, FMEL_UPD_D |
| `data/transit/traffic_signals.geojson` | 15.7 MB | 44,922 | 6 | OBJECTID_1, BEARG_NUM, TYP_NAM, UNIQUE_ID, INC_CRC |
| `data/transit_updated/train_stations_mar2026.geojson` | 1.0 MB | 231 | 7 | TYP_CD, STN_NAM, ATTACHEMEN, SHAPE_AREA, SHAPE_LEN |
| `data/transit_updated/bus_stops_mar2026.geojson` | 939 KB | 5,177 | 2 | BUS_STOP_N, LOC_DESC |
| `data/transit/rail_stations.geojson` | 766 KB | 257 | 8 | OBJECTID, GRND_LEVEL, RAIL_TYPE, NAME, INC_CRC |
| `data/transit/bus_stops_osm.json` | 732 KB | 5,574 | 5 | name, ref, operator, lat, lon |
| `data/transit/mrt_exits.geojson` | 203 KB | 597 | 5 | OBJECTID, STATION_NA, EXIT_CODE, INC_CRC, FMEL_UPD_D |
| `data/transit_updated/train_station_exits_feb2025.geojson` | 112 KB | 595 | 2 | stn_name, exit_code |
| `data/lta/BusRoutes.json` | 63 KB | 2 | — | odata.metadata, value |
| `data/transit/mrt_lrt_stations.json` | 33 KB | 236 | 6 | name, lat, lon, exit_count, type |
| `data/transit/mrt_station_names.geojson` | 32 KB | 35 | 27 | OBJECTID, FEATUREID, ZORDER, ANNOTATIONCLASSID, SYMBOLID |
| `data/lta/BusServices.xml` | 9 KB | — | — | — |
| `data/lta/BusRoutes.xml` | 8 KB | — | — | — |
| `data/demand/travel_times.json` | 8 KB | 2 | — | odata.metadata, value |
| `data/lta/bus_routes.zip` | 5 KB | — | — | — |
| `data/lta/BusServices.json` | 3 KB | 2 | — | odata.metadata, value |
| `data/demand/platform_crowd.json` | 3 KB | 2 | — | odata.metadata, value |
| `data/transit_updated/ev_charging_points.json` | 2 KB | 1 | — | value |
| `data/demand/passenger_vol_train.json` | 2 KB | 2 | — | odata.metadata, value |
| `data/demand/passenger_vol_od_train.json` | 2 KB | 2 | — | odata.metadata, value |
| `data/demand/passenger_vol_bus.json` | 2 KB | 2 | — | odata.metadata, value |
| `data/demand/passenger_vol_od_bus.json` | 2 KB | 2 | — | odata.metadata, value |
| `data/lta/bus_services.zip` | 1 KB | — | — | — |
| `data/demand/carpark_availability.json` | 1 KB | 2 | — | odata.metadata, value |

## Amenities & Services (51.3 MB, 20 files)

| File | Size | Records | Columns | Key Fields |
|------|------|---------|---------|------------|
| `data/amenities_updated/eating_establishments_sfa.geojson` | 36.2 MB | 34,378 | 2 | Name, Description |
| `data/amenities/eating_establishments.csv` | 3.4 MB | 36,687 | 7 | licensee_name, licence_number, premises_address, grade, demerit_points |
| `data/amenities/parks_nature_reserves.geojson` | 2.7 MB | 450 | 8 | OBJECTID_1, L_CODE, NAME, N_RESERVE, INC_CRC |
| `data/amenities/park_facilities.geojson` | 2.1 MB | 5,393 | 7 | OBJECTID, UNIQUEID, NAME, CLASS, ADDITIONAL_INFO |
| `data/amenities/park_connector.geojson` | 1.9 MB | 883 | 7 | OBJECTID, PARK, PCN_LOOP, MORE_INFO, INC_CRC |
| `data/amenities_updated/chas_clinics.geojson` | 1.5 MB | 1,193 | 2 | Name, Description |
| `data/amenities_updated/preschools.geojson` | 1.2 MB | 2,290 | 2 | Name, Description |
| `data/amenities/supermarkets.geojson` | 427 KB | 526 | 2 | Name, Description |
| `data/amenities_updated/silver_zones.geojson` | 304 KB | 42 | 3 | SITENAME, INC_CRC, FMEL_UPD_D |
| `data/amenities/hotels.geojson` | 218 KB | 468 | 9 | OBJECTID, HYPERLINK, DESCRIPTION, POSTALCODE, KEEPERNAME |
| `data/amenities/parks.geojson` | 159 KB | 450 | 6 | OBJECTID, NAME, X, Y, INC_CRC |
| `data/amenities_updated/school_zones.geojson` | 146 KB | 211 | 3 | SITENAME, INC_CRC, FMEL_UPD_D |
| `data/amenities_updated/tourist_attractions.geojson` | 140 KB | 109 | 17 | OBJECTID_1, URL_PATH, IMAGE_PATH, IMAGE_ALT_TEXT, PHOTOCREDITS |
| `data/amenities_updated/hawker_centres.geojson` | 137 KB | 129 | 20 | OBJECTID, LANDXADDRESSPOINT, LANDYADDRESSPOINT, ADDRESSBUILDINGNAME, ADDRESSPOSTALCODE |
| `data/amenities/hawker_centres.geojson` | 137 KB | 129 | 20 | OBJECTID, LANDXADDRESSPOINT, LANDYADDRESSPOINT, ADDRESSBUILDINGNAME, ADDRESSPOSTALCODE |
| `data/amenities/schools.csv` | 131 KB | 337 | 31 | school_name, url_address, address, postal_code, telephone_no |
| `data/amenities_updated/schools_directory.csv` | 131 KB | 337 | 31 | school_name, url_address, address, postal_code, telephone_no |
| `data/education/school_directory.csv` | 131 KB | 337 | 31 | school_name, url_address, address, postal_code, telephone_no |
| `data/amenities/schools_geocoded.json` | 73 KB | 337 | 7 | name, postal_code, address, zone, type |
| `data/amenities/healthcare_facilities.csv` | 6 KB | 112 | 5 | year, institution_type, sector, facility_type_b, no_of_facilities |

## Infrastructure (467.3 MB, 3 files)

| File | Size | Records | Columns | Key Fields |
|------|------|---------|---------|------------|
| `data/roads/roads.geojson` | 219.9 MB | 550,991 | 12 | u, v, key, osmid, name |
| `data/land_use/master_plan_land_use.geojson` | 166.1 MB | 113,212 | 10 | OBJECTID, LU_DESC, LU_TEXT, GPR, WHI_Q_MX |
| `data/buildings/buildings.geojson` | 81.3 MB | 125,973 | 11 | element, id, building, name, building:levels |

## Business & Economy (616.1 MB, 34 files)

| File | Size | Records | Columns | Key Fields |
|------|------|---------|---------|------------|
| `data/business/acra_entities.csv` | 218.3 MB | 2,076,437 | 8 | uen, issuance_agency_desc, uen_status_desc, entity_name, entity_type_desc |
| `data/new_datasets/acra_entities.csv` | 218.3 MB | 2,076,437 | 8 | uen, issuance_agency_desc, uen_status_desc, entity_name, entity_type_desc |
| `data/new_datasets/hdb_buildings.geojson` | 54.0 MB | 13,386 | 9 | OBJECTID, BLK_NO, ST_COD, ENTITYID, POSTAL_COD |
| `data/new_datasets/eating_establishments_sfa.geojson` | 36.2 MB | 34,378 | 2 | Name, Description |
| `data/new_datasets/private_resi_transactions.csv` | 21.6 MB | 287,196 | 10 | month, town, flat_type, block, street_name |
| `data/new_datasets/hdb_resale_prices.csv` | 21.4 MB | 227,207 | 11 | month, town, flat_type, block, street_name |
| `data/new_datasets/pop_age_sex_fa_2020_2024.csv` | 16.9 MB | 315,400 | 7 | PA, SZ, AG, Sex, FA |
| `data/new_datasets/pop_age_sex_tod_2025.csv` | 6.8 MB | 100,928 | 7 | PA, SZ, AG, Sex, TOD |
| `data/new_datasets/pop_age_sex_tod_2024.csv` | 6.8 MB | 100,928 | 7 | ﻿PA, SZ, AG, Sex, TOD |
| `data/new_datasets/pop_age_sex_fa_2025.csv` | 3.4 MB | 63,080 | 7 | PA, SZ, AG, Sex, FA |
| `data/business/acra_other_entities.csv` | 3.0 MB | 22,915 | 8 | uen, issuance_agency_desc, uen_status_desc, entity_name, entity_type_desc |
| `data/new_datasets/acra_other_entities.csv` | 3.0 MB | 22,915 | 8 | uen, issuance_agency_desc, uen_status_desc, entity_name, entity_type_desc |
| `data/new_datasets/chas_clinics.geojson` | 1.5 MB | 1,193 | 2 | Name, Description |
| `data/new_datasets/preschools.geojson` | 1.2 MB | 2,290 | 2 | Name, Description |
| `data/new_datasets/train_stations_mar2026.geojson` | 1.0 MB | 231 | 7 | TYP_CD, STN_NAM, ATTACHEMEN, SHAPE_AREA, SHAPE_LEN |
| `data/new_datasets/bus_stops_mar2026.geojson` | 939 KB | 5,177 | 2 | BUS_STOP_N, LOC_DESC |
| `data/new_datasets/dwellings_subzone_2020_2024.csv` | 332 KB | 8,300 | 5 | PA, SZ, FA, HSE, Time |
| `data/new_datasets/silver_zones.geojson` | 304 KB | 42 | 3 | SITENAME, INC_CRC, FMEL_UPD_D |
| `data/business/graduate_employment.csv` | 225 KB | 1,550 | 12 | year, university, school, degree, employment_rate_overall |
| `data/new_datasets/graduate_employment.csv` | 225 KB | 1,550 | 12 | year, university, school, degree, employment_rate_overall |
| `data/new_datasets/school_zones.geojson` | 146 KB | 211 | 3 | SITENAME, INC_CRC, FMEL_UPD_D |
| `data/new_datasets/tourist_attractions.geojson` | 140 KB | 109 | 17 | OBJECTID_1, URL_PATH, IMAGE_PATH, IMAGE_ALT_TEXT, PHOTOCREDITS |
| `data/new_datasets/hawker_centres.geojson` | 137 KB | 129 | 20 | OBJECTID, LANDXADDRESSPOINT, LANDYADDRESSPOINT, ADDRESSBUILDINGNAME, ADDRESSPOSTALCODE |
| `data/new_datasets/schools_directory.csv` | 131 KB | 337 | 31 | school_name, url_address, address, postal_code, telephone_no |
| `data/new_datasets/train_station_exits_feb2025.geojson` | 112 KB | 595 | 2 | stn_name, exit_code |
| `data/new_datasets/dwellings_subzone_2025.csv` | 67 KB | 1,660 | 5 | PA, SZ, FA, HSE, Time |
| `data/new_datasets/travel_times.json` | 8 KB | 2 | — | odata.metadata, value |
| `data/new_datasets/platform_crowd.json` | 3 KB | 2 | — | odata.metadata, value |
| `data/new_datasets/ev_charging_points.json` | 2 KB | 1 | — | value |
| `data/new_datasets/passenger_vol_train.json` | 2 KB | 2 | — | odata.metadata, value |
| `data/new_datasets/passenger_vol_od_train.json` | 2 KB | 2 | — | odata.metadata, value |
| `data/new_datasets/passenger_vol_bus.json` | 2 KB | 2 | — | odata.metadata, value |
| `data/new_datasets/passenger_vol_od_bus.json` | 2 KB | 2 | — | odata.metadata, value |
| `data/new_datasets/carpark_availability.json` | 1 KB | 2 | — | odata.metadata, value |

## Raw Sources (231.3 MB, 2 files)

| File | Size | Records | Columns | Key Fields |
|------|------|---------|---------|------------|
| `data/osm/singapore-latest.osm.pbf` | 231.3 MB | — | — | — |
| `data/satellite/nightlights_202401.tif` | 9 KB | — | — | — |

## Micrographs & Models (295.2 MB, 43 files)

| File | Size | Records | Columns | Key Fields |
|------|------|---------|---------|------------|
| `micrograph_output/shopping_retail_micrographs.jsonl` | 89.8 MB | 12,190 | 22 | place_id, name, brand, address, place_type |
| `micrograph_output/restaurant_micrographs.jsonl` | 43.6 MB | 5,682 | 22 | place_id, name, brand, address, place_type |
| `micrograph_output/hawker_micrographs.jsonl` | 27.8 MB | 3,564 | 22 | place_id, name, brand, address, place_type |
| `micrograph_output/education_micrographs.jsonl` | 26.7 MB | 3,938 | 22 | place_id, name, brand, address, place_type |
| `micrograph_output/cafe_micrographs.jsonl` | 22.0 MB | 2,924 | 22 | place_id, name, brand, address, place_type |
| `micrograph_output/beauty_personal_care_micrographs.jsonl` | 19.6 MB | 3,768 | 22 | place_id, name, brand, address, place_type |
| `micrograph_output/convenience_daily_needs_micrographs.jsonl` | 19.4 MB | 3,895 | 22 | place_id, name, brand, address, place_type |
| `micrograph_output/fitness_recreation_micrographs.jsonl` | 11.7 MB | 1,898 | 22 | place_id, name, brand, address, place_type |
| `micrograph_output/fast_food_qsr_micrographs.jsonl` | 8.6 MB | 1,198 | 22 | place_id, name, brand, address, place_type |
| `micrograph_output/bar_nightlife_micrographs.jsonl` | 8.0 MB | 1,322 | 22 | place_id, name, brand, address, place_type |
| `micrograph_output/health_medical_micrographs.jsonl` | 6.6 MB | 1,296 | 22 | place_id, name, brand, address, place_type |
| `micrograph_output/bakery_pastry_micrographs.jsonl` | 6.1 MB | 928 | 22 | place_id, name, brand, address, place_type |
| `micrograph_output/shopping_retail_slim.json` | 1.4 MB | 12,190 | — | — |
| `micrograph_output/restaurant_slim.json` | 666 KB | 5,682 | — | — |
| `micrograph_output/education_slim.json` | 478 KB | 3,938 | — | — |
| `micrograph_output/convenience_daily_needs_slim.json` | 438 KB | 3,895 | — | — |
| `micrograph_output/hawker_slim.json` | 433 KB | 3,564 | — | — |
| `micrograph_output/beauty_personal_care_slim.json` | 418 KB | 3,768 | — | — |
| `micrograph_output/cafe_slim.json` | 337 KB | 2,924 | — | — |
| `micrograph_output/fitness_recreation_slim.json` | 224 KB | 1,898 | — | — |
| `micrograph_output/health_medical_slim.json` | 155 KB | 1,296 | — | — |
| `micrograph_output/bar_nightlife_slim.json` | 149 KB | 1,322 | — | — |
| `micrograph_output/fast_food_qsr_slim.json` | 139 KB | 1,198 | — | — |
| `model_results_v5/gap_analysis_v5.parquet` | 127 KB | 332 | 77 | subzone_code, subzone_name, is_viable, actual_total, predicted_total |
| `model_results_v5/gap_analysis_v5.csv` | 126 KB | 332 | 77 | subzone_code, subzone_name, is_viable, actual_total, predicted_total |
| `micrograph_output/bakery_pastry_slim.json` | 103 KB | 928 | — | — |
| `micrograph_pipeline/run_pipeline.py` | 32 KB | — | — | — |
| `micrograph_pipeline/run_all.log` | 22 KB | — | — | — |
| `micrograph_pipeline/config.py` | 19 KB | — | — | — |
| `micrograph_pipeline/run_cafe_v2.py` | 18 KB | — | — | — |
| `model_results_v5/report_v5.json` | 6 KB | 13 | — | version, timestamp, description, stage1_density_r2, stage2_loo_mean_r2 |
| `micrograph_output/shopping_retail_stats.json` | 1 KB | 11 | — | category, total, density_bands, anchor_count_mean, anchor_count_min |
| `micrograph_output/convenience_daily_needs_stats.json` | 1 KB | 11 | — | category, total, density_bands, anchor_count_mean, anchor_count_min |
| `micrograph_output/fitness_recreation_stats.json` | 1 KB | 11 | — | category, total, density_bands, anchor_count_mean, anchor_count_min |
| `micrograph_output/beauty_personal_care_stats.json` | 1 KB | 11 | — | category, total, density_bands, anchor_count_mean, anchor_count_min |
| `micrograph_output/restaurant_stats.json` | 1 KB | 11 | — | category, total, density_bands, anchor_count_mean, anchor_count_min |
| `micrograph_output/education_stats.json` | 1 KB | 11 | — | category, total, density_bands, anchor_count_mean, anchor_count_min |
| `micrograph_output/health_medical_stats.json` | 1 KB | 11 | — | category, total, density_bands, anchor_count_mean, anchor_count_min |
| `micrograph_output/bar_nightlife_stats.json` | 1 KB | 11 | — | category, total, density_bands, anchor_count_mean, anchor_count_min |
| `micrograph_output/fast_food_qsr_stats.json` | 1 KB | 11 | — | category, total, density_bands, anchor_count_mean, anchor_count_min |
| `micrograph_output/hawker_stats.json` | 1 KB | 11 | — | category, total, density_bands, anchor_count_mean, anchor_count_min |
| `micrograph_output/bakery_pastry_stats.json` | 1 KB | 11 | — | category, total, density_bands, anchor_count_mean, anchor_count_min |
| `micrograph_output/cafe_stats.json` | 1 KB | 11 | — | category, total, density_bands, anchor_count_mean, anchor_count_min |

## Pipeline Outputs (8.2 MB, 18 files)

| File | Size | Records | Columns | Key Fields |
|------|------|---------|---------|------------|
| `final/place_features.parquet` | 3.7 MB | 66,851 | 13 | place_id, latitude, longitude, main_category, place_type |
| `intermediate/transit_by_place.parquet` | 2.4 MB | 66,851 | 6 | place_id, subzone_code, dist_nearest_mrt, dist_nearest_bus, bus_stops_300m |
| `graphs/colocation_pmi.json` | 676 KB | 4 | — | type, place_types, edge_count, edges |
| `final/subzone_features.parquet` | 361 KB | 332 | 205 | subzone_code, subzone_name, planning_area, area_km2, total_population |
| `final/subzone_features_raw.parquet` | 341 KB | 332 | 205 | subzone_code, subzone_name, planning_area, area_km2, total_population |
| `graphs/subzone_adjacency.json` | 209 KB | 5 | — | type, node_count, edge_count, nodes, edges |
| `graphs/transit_connectivity.json` | 155 KB | 6 | — | type, subzones_with_mrt, mrt_stations, edge_count, nodes_with_mrt |
| `intermediate/place_composition_by_subzone.parquet` | 98 KB | 326 | 52 | subzone_code, total_place_count, cat_automotive, cat_bakery_pastry, cat_bar_nightlife |
| `intermediate/place_types_by_subzone.parquet` | 71 KB | 326 | 81 | subzone_code, type_atm, type_aged_care, type_apartment, type_arts_academy |
| `intermediate/demographics_by_subzone.parquet` | 40 KB | 332 | 17 | subzone_code, subzone_name, planning_area, area_km2, total_population |
| `intermediate/landuse_by_subzone.parquet` | 40 KB | 332 | 14 | subzone_code, lu_residential_pct, lu_commercial_pct, lu_industrial_pct, lu_mixed_use_pct |
| `intermediate/roads_by_subzone.parquet` | 36 KB | 332 | 12 | subzone_code, total_road_length_km, road_density_km_per_km2, road_motorway_km, road_trunk_km |
| `intermediate/brand_quality_by_subzone.parquet` | 27 KB | 326 | 11 | subzone_code, branded_count, branded_pct, unique_brand_count, avg_rating |
| `intermediate/amenity_by_subzone.parquet` | 22 KB | 332 | 10 | subzone_code, dist_nearest_park, parks_within_1km, dist_nearest_hawker, hawkers_within_1km |
| `intermediate/validation_by_subzone.parquet` | 13 KB | 332 | 7 | subzone_code, sfa_eating_count, chas_clinic_count, preschool_count_gov, our_place_count |
| `intermediate/property_by_subzone.parquet` | 12 KB | 332 | 7 | subzone_code, subzone_name, planning_area, median_hdb_psf, hdb_transaction_count |
| `intermediate/transit_by_subzone.parquet` | 12 KB | 332 | 5 | subzone_code, dist_nearest_mrt, mrt_stations_1km, bus_stop_count_1km, bus_density_per_km2 |
| `final/feature_catalog.csv` | 9 KB | 202 | 7 | feature, non_null, null_pct, mean, std |

---

## Key Datasets for Atlas

| Dataset | Description | Integrated? |
|---------|-------------|-------------|
| `data/places_consolidated/sgp_places_v2.jsonl` | MASTER — 174K places with categories, tiers, segments | YES |
| `data/boundaries/subzones.geojson` | 332 subzone boundaries for choropleth | YES |
| `data/demand/passenger_vol_train.json` | MRT ridership by station (footfall) | NO |
| `data/demand/passenger_vol_bus.json` | Bus ridership by stop (footfall) | NO |
| `data/demand/platform_crowd.json` | Platform crowd density | NO |
| `data/demand/travel_times.json` | Travel times between zones | NO |
| `data/new_datasets/acra_entities.csv` | Business registry (opening dates, survival) | NO |
| `data/new_datasets/hdb_resale_prices.csv` | HDB resale transactions | NO |
| `data/new_datasets/private_resi_transactions.csv` | Private property prices | NO |
| `data/housing/hdb_existing_buildings.geojson` | HDB building footprints | NO |
| `data/transit_updated/train_stations_mar2026.geojson` | MRT/LRT stations (latest) | YES |
| `data/transit_updated/bus_stops_mar2026.geojson` | Bus stops (latest) | YES |
| `data/amenities_updated/hawker_centres.geojson` | 129 hawker centres | YES |
| `data/amenities_updated/schools_directory.csv` | Schools directory | YES |
