# Digital Atlas SGP - Data Catalog

## Overview
- Region unit: **Subzone** (332 zones)
- Total files: 41
- Total size: 809.2 MB

## amenities (11.4 MB)

| File | Format | Size | Records | Key Fields |
|------|--------|------|---------|------------|
| eating_establishments.csv | CSV | 3.4 MB | 36,689 | licensee_name, licence_number, premises_address, grade, demerit_points |
| hawker_centres.geojson | GeoJSON | 0.1 MB | 129 | OBJECTID, LANDXADDRESSPOINT, LANDYADDRESSPOINT, ADDRESSBUILDINGNAME, ADDRESSPOSTALCODE |
| healthcare_facilities.csv | CSV | 0.0 MB | 113 | year, institution_type, sector, facility_type_b, no_of_facilities |
| hotels.geojson | GeoJSON | 0.2 MB | 468 | OBJECTID, HYPERLINK, DESCRIPTION, POSTALCODE, KEEPERNAME |
| park_connector.geojson | GeoJSON | 1.9 MB | 883 | OBJECTID, PARK, PCN_LOOP, MORE_INFO, INC_CRC |
| park_facilities.geojson | GeoJSON | 2.1 MB | 5,393 | OBJECTID, UNIQUEID, NAME, CLASS, ADDITIONAL_INFO |
| parks.geojson | GeoJSON | 0.2 MB | 450 | OBJECTID, NAME, X, Y, INC_CRC |
| parks_nature_reserves.geojson | GeoJSON | 2.7 MB | 450 | OBJECTID_1, L_CODE, NAME, N_RESERVE, INC_CRC |
| schools.csv | CSV | 0.1 MB | 338 | school_name, url_address, address, postal_code, telephone_no |
| schools_geocoded.json | JSON | 0.1 MB | 337 | name, postal_code, address, zone, type |
| supermarkets.geojson | GeoJSON | 0.4 MB | 526 | Name, Description |

## boundaries (5.0 MB)

| File | Format | Size | Records | Key Fields |
|------|--------|------|---------|------------|
| planning_areas.geojson | GeoJSON | 2.0 MB | 55 | OBJECTID, PLN_AREA_N, PLN_AREA_C, CA_IND, REGION_N |
| subzones.geojson | GeoJSON | 3.0 MB | 332 | OBJECTID, SUBZONE_NO, SUBZONE_N, SUBZONE_C, CA_IND |

## census (0.3 MB)

| File | Format | Size | Records | Key Fields |
|------|--------|------|---------|------------|
| hh_dwelling.csv | CSV | 0.0 MB | 33 | Number, Total, HDBDwellings_Total, HDBDwellings_1_and2_RoomFlats1, HDBDwellings_3_RoomFlats |
| hh_income.csv | CSV | 0.0 MB | 33 | Number, Total, NoEmployedPerson, Below_1_000, 1_000_1_999 |
| hh_size.csv | CSV | 0.0 MB | 33 | Number, Total, 1Person, 2Persons, 3Persons |
| pop_age_floor_area.csv | CSV | 0.1 MB | 389 | Number, Total1_Total, Total1_0_4, Total1_5_9, Total1_10_14 |
| pop_age_sex.csv | CSV | 0.1 MB | 389 | Number, Total_Total, Total_0_4, Total_5_9, Total_10_14 |
| pop_dwelling.csv | CSV | 0.0 MB | 389 | Number, Total, HDBDwellings_Total, HDBDwellings_1_and2_RoomFlats1, HDBDwellings_3_RoomFlats |
| pop_ethnic_sex.csv | CSV | 0.0 MB | 389 | Number, Total_Total, Total_Males, Total_Females, Chinese_Total |

## housing (76.2 MB)

| File | Format | Size | Records | Key Fields |
|------|--------|------|---------|------------|
| hdb_existing_buildings.geojson | GeoJSON | 54.0 MB | 13,386 | OBJECTID, BLK_NO, ST_COD, ENTITYID, POSTAL_COD |
| hdb_property_info.csv | CSV | 0.9 MB | 13,268 | blk_no, street, max_floor_lvl, year_completed, residential |
| hdb_resale_2017_onwards.csv | CSV | 21.4 MB | 226,744 | month, town, flat_type, block, street_name |

## land_use (166.1 MB)

| File | Format | Size | Records | Key Fields |
|------|--------|------|---------|------------|
| master_plan_land_use.geojson | GeoJSON | 166.1 MB | 113,212 | OBJECTID, LU_DESC, LU_TEXT, GPR, WHI_Q_MX |

## osm (231.3 MB)

| File | Format | Size | Records | Key Fields |
|------|--------|------|---------|------------|
| singapore-latest.osm.pbf | OSM_PBF | 231.3 MB | - | - |

## places (33.2 MB)

| File | Format | Size | Records | Key Fields |
|------|--------|------|---------|------------|
| sgp_places.jsonl | JSONL | 33.2 MB | 66,851 | id, name, address, latitude, longitude |

## results (246.0 MB)

| File | Format | Size | Records | Key Fields |
|------|--------|------|---------|------------|
| sgp_boundary.geojson | GeoJSON | 0.0 MB | 1 | GID_0, COUNTRY |
| sgp_brands.jsonl | JSONL | 0.0 MB | 233 | brand, parent, locations, primary_category, primary_place_type |
| sgp_places.jsonl | JSONL | 24.5 MB | 66,851 | id, name, address, latitude, longitude |
| sgp_places_curated.jsonl | JSONL | 96.5 MB | 79,257 | place_id, status, candidates |
| sgp_places_deduped.jsonl | JSONL | 43.5 MB | 68,269 | place_id, name, lat, lon, geohash9 |
| sgp_places_final.jsonl | JSONL | 44.4 MB | 68,269 | id, name, address, latitude, longitude |
| sgp_places_kepler.csv | CSV | 11.1 MB | 66,852 | id, name, latitude, longitude, main_category |
| sgp_places_kepler.geojson | GeoJSON | 26.1 MB | 66,851 | id, name, main_category, place_type, sub_category |

## transit (39.7 MB)

| File | Format | Size | Records | Key Fields |
|------|--------|------|---------|------------|
| bus_stops_osm.json | JSON | 0.7 MB | 5,574 | name, ref, operator, lat, lon |
| mrt_exits.geojson | GeoJSON | 0.2 MB | 597 | OBJECTID, STATION_NA, EXIT_CODE, INC_CRC, FMEL_UPD_D |
| mrt_lrt_stations.json | JSON | 0.0 MB | 236 | name, lat, lon, exit_count, type |
| mrt_station_names.geojson | GeoJSON | 0.0 MB | 35 | OBJECTID, FEATUREID, ZORDER, ANNOTATIONCLASSID, SYMBOLID |
| rail_lines.geojson | GeoJSON | 22.2 MB | 1,366 | OBJECTID, GRND_LEVEL, RAIL_TYPE, INC_CRC, FMEL_UPD_D |
| rail_stations.geojson | GeoJSON | 0.8 MB | 257 | OBJECTID, GRND_LEVEL, RAIL_TYPE, NAME, INC_CRC |
| traffic_signals.geojson | GeoJSON | 15.7 MB | 44,922 | OBJECTID_1, BEARG_NUM, TYP_NAM, UNIQUE_ID, INC_CRC |

