# Digital Atlas SGP - Data Processing Plan

## Goal
Transform raw data into `subzone_features.parquet` (332 x ~200 dims) and `place_features.parquet` (66,851 x ~30 dims) for model training.

---

## PHASE 1: DATA VALIDATION & CLEANING

### Step 1: Validate All Inputs
- Load every dataset, check row counts, null rates, coordinate validity
- Verify all spatial data in EPSG:4326
- Check subzone boundary coverage (332 zones)
- Output: `validation_report.json`

### Step 2: Standardize Demographics
Input: `demographics/pop_age_sex_*.csv`, `demographics/dwellings_*.csv`
- Parse Singstat format (PA, SZ, AG, Sex, FA/TOD, Pop)
- Use 2025 as primary, 2024 fallback
- Per subzone: total_pop, pop_density, age brackets (0-14, 15-64, 65+), gender ratio, dependency ratio, dwelling type distribution
- Output: `intermediate/demographics_by_subzone.parquet`

### Step 3: Standardize Property Data
Input: `property/hdb_resale_prices.csv`, `property/private_resi_transactions.csv`
- Map transactions to subzones via town/address
- Per subzone: median_hdb_psf, hdb_price_yoy, median_private_psf, price_premium
- Output: `intermediate/property_by_subzone.parquet`

---

## PHASE 2: SPATIAL FEATURE EXTRACTION (parallel)

### Step 4: Road Network Features
Input: `roads/roads.geojson`
- Spatial join to subzones
- Per subzone: total_road_length, road_density, road_type_counts, intersection_density, avg_block_size, pedestrian_path_length
- Output: `intermediate/roads_by_subzone.parquet`

### Step 5: Building Features
Input: `buildings/buildings.geojson`, `housing/hdb_*`
- Spatial join to subzones
- Per subzone: building_count, built_area, coverage_ratio, avg_levels, max_levels, FAR, building_type_dist, hdb_block_count, avg_building_age
- Output: `intermediate/buildings_by_subzone.parquet`

### Step 6: Land Use Features
Input: `land_use/master_plan_land_use.geojson`
- Intersect with subzones
- Per subzone: land_use_distribution (10 types), avg_gpr, max_gpr, land_use_entropy, green_ratio
- Output: `intermediate/landuse_by_subzone.parquet`

### Step 7: Transit Features
Input: `transit_updated/`, `transit/`
- Per subzone: dist_nearest_mrt, mrt_within_1km, bus_stop_count, bus_density, traffic_signal_count, ev_charging_count
- Per place: dist_nearest_mrt, dist_nearest_bus, bus_stops_300m, transit_score
- Output: `intermediate/transit_by_subzone.parquet`, `intermediate/transit_by_place.parquet`

---

## PHASE 3: PLACE COMPOSITION FEATURES (parallel)

### Step 8: Category Composition
Input: `places/sgp_places.jsonl`
- Per subzone: 24-dim category distribution, total_place_count, place_density, category_entropy
- Output: `intermediate/place_composition_by_subzone.parquet`

### Step 9: Place Type Granular Counts
Input: `places/sgp_places.jsonl`
- Per subzone: top 80 place_type counts, fnb_density, retail_density, service_density
- Output: `intermediate/place_types_by_subzone.parquet`

### Step 10: Brand & Quality Features
Input: `places/sgp_places.jsonl`
- Per subzone: branded_pct, unique_brands, chain_ratio, avg_rating, total_reviews, high_rated_pct
- Output: `intermediate/brand_quality_by_subzone.parquet`

### Step 11: Competitor Density (per place)
Input: `places/sgp_places.jsonl`
- Per place: same_type at 100/200/500m, same_category at 100/200/500m, total_places at radii, diversity_200m
- Output: `intermediate/competitor_by_place.parquet`

---

## PHASE 4: VALIDATION & CROSS-REFERENCE (parallel)

### Step 12: Cross-Reference with Government Data
Input: `new_datasets/eating_establishments_sfa.geojson` (34K), `new_datasets/chas_clinics.geojson` (1.2K), `new_datasets/preschools.geojson` (2.3K), `new_datasets/acra_entities.csv` (2M)
- Per subzone: sfa_eating_count, chas_clinic_count, preschool_count_gov, acra_entity_count, coverage_ratios
- Output: `intermediate/validation_by_subzone.parquet`

### Step 13: Amenity Accessibility
Input: `amenities/`, `amenities_updated/`
- Per subzone: park_count, park_area_ratio, dist_nearest_park, hawker_centre_count, school_count, supermarket_count, hotel_rooms, tourist_attractions, silver_zone_flag
- Output: `intermediate/amenity_by_subzone.parquet`

---

## PHASE 5: GRAPH CONSTRUCTION (parallel)

### Step 14: Subzone Adjacency Graph
- Queen contiguity from subzone polygons
- Edge weight = shared boundary length
- Output: `graphs/subzone_adjacency.json`

### Step 15: Place Co-location Graph (PMI)
- PMI matrix for all place_type pairs across subzones
- Output: `graphs/colocation_pmi.json`

### Step 16: Transit Connectivity Graph
- Nodes = subzones, edges = direct MRT/bus links
- Output: `graphs/transit_connectivity.json`

---

## PHASE 6: MERGE & EXPORT (serial)

### Step 17: Merge All Subzone Features
- Join all intermediate parquets on subzone_code
- Z-score normalize numerical features
- Median imputation for missing continuous, 0 for counts
- Output: `final/subzone_features.parquet` (332 x ~200, normalized)
- Output: `final/subzone_features_raw.parquet` (332 x ~200, raw)

### Step 18: Merge All Place Features
- Join place-level features from steps 7, 11
- Attach subzone_code as foreign key
- Output: `final/place_features.parquet` (66,851 x ~30)

---

## PHASE 7: QUALITY ASSURANCE (serial)

### Step 19: Final Audit
- No nulls in critical features
- All 332 subzones present
- Feature distribution checks (no extreme outliers)
- Correlation matrix (flag r > 0.95 redundancy)
- Output: `final/FEATURE_CATALOG.md`, `final/feature_distributions.png`

---

## EXECUTION ORDER

```
Phase 1 (serial):     step_01 -> step_02 -> step_03
Phase 2 (parallel):   step_04 | step_05 | step_06 | step_07
Phase 3 (parallel):   step_08 | step_09 | step_10 | step_11
Phase 4 (parallel):   step_12 | step_13
Phase 5 (parallel):   step_14 | step_15 | step_16
Phase 6 (serial):     step_17 -> step_18
Phase 7 (serial):     step_19
```

Estimated time: ~30 min total

---

## OUTPUT STRUCTURE

```
digital-atlas-sgp/
  intermediate/         13 parquet files (per-step outputs)
  graphs/               3 JSON files (adjacency, PMI, transit)
  final/
    subzone_features.parquet      332 x ~200 (normalized)
    subzone_features_raw.parquet  332 x ~200 (raw values)
    place_features.parquet        66,851 x ~30
    FEATURE_CATALOG.md
  scripts/
    step_01_validate.py through step_19_audit.py
```
