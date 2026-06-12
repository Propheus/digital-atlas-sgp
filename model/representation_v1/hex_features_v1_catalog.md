# Hex Features v1 — Catalog

**Rows:** 5,897 hexes (H3 res 9, Singapore, V9 universe)  
**Columns:** 376 (raw, unnormalized)  
**File:** `model/representation_v1/hex_features_v1.parquet`  

## Pillar summary

| Pillar | # features | Source |
|---|---|---|
| `place_composition` | 66 | v2 places (174K) → per-hex counts, shares, HHI, entropy |
| `personas` | 35 | V9 (NVIDIA personas, 148K) |
| `neighbor_nbr1_mean` | 28 | k=1 (6 neighbors) mean over influence basis |
| `neighbor_nbr1_max` | 28 | k=1 max |
| `neighbor_nbr2_mean` | 28 | k=2 (18 neighbors) mean |
| `neighbor_contrast` | 28 | self - nbr1_mean (positive = self exceeds neighbors) |
| `neighbor_rank` | 28 | percentile rank of self within self+k=1 ∈ [0,1] |
| `roads_signals` | 22 | V9 (LTA traffic + OSM) |
| `walkability` | 21 | V9 (OSM-derived) |
| `micrograph` | 19 | micrograph_output/ (v2, 66K generic + 2.9K cafe-specific) |
| `buildings` | 17 | V9 (Overture + HDB fused) |
| `v9_places_raw` | 13 | V9 (13 pre-aggregated categories, legacy) |
| `transit` | 12 | V9 (LTA + OSM) |
| `amenities_v9` | 10 | V9 (data.gov.sg) |
| `identity` | 8 | data/hex_v9/hex_features_v2.parquet |
| `population` | 6 | V9 (Census 2025) |
| `housing_price` | 4 | V9 (HDB resale, URA GPR) |
| `v9_rings` | 3 | V9 (pre-computed ring aggregates) |

## Provenance notes

- **Gap scores dropped** (no leakage): `transit_gap_score`, `elderly_transit_stress`, `clinic_gap_score`, `school_gap_score`.
- **Place composition** recomputed from the 174K v2 master file. 166,582 of 174,713 places landed in the V9 hex universe (95.3%); 8,131 outside (offshore islands, near-border).
- **Micrograph** uses v2 locally (66K v1 places). 11 of 12 v2 jsonl files are duplicates of the same spatial context, so we treat them as one universal per-place signal. V3 (174K, per-category) is on the server and will upgrade these features when synced.
- **Neighbor features** are built over a 28-feature influence basis (see `INFLUENCE_BASIS` in `scripts/representation_v1/build_hex_rings.py`). Neighbors outside the 5,897-hex universe are excluded (not imputed).
- **No normalization** applied in this file. Sqrt normalization is a separate downstream step.

## Columns by pillar

### `identity` (8)

- `hex_id`
- `lat`
- `lng`
- `area_km2`
- `parent_subzone`
- `parent_subzone_name`
- `parent_pa`
- `parent_region`

### `buildings` (17)

- `bldg_count`
- `hdb_blocks`
- `avg_floors`
- `max_floors`
- `avg_height`
- `max_height`
- `bldg_commercial`
- `bldg_hdb_residential`
- `bldg_industrial`
- `bldg_institutional`
- `bldg_other`
- `bldg_private_residential`
- `bldg_religious`
- `bldg_transport`
- `bldg_unclassified`
- `bldg_footprint_sqm`
- `bldg_ring1`

### `v9_places_raw` (13)

- `places_total`
- `place_shopping_retail`
- `place_restaurant`
- `place_services`
- `place_business`
- `place_beauty_personal_care`
- `place_education`
- `place_health_medical`
- `place_cafe_coffee`
- `place_fitness_recreation`
- `place_convenience_daily_needs`
- `place_hawker_street_food`
- `place_automotive`

### `transit` (12)

- `mrt_stations`
- `lrt_stations`
- `bus_stops`
- `mrt_hex_rings`
- `dist_nearest_mrt_m`
- `transit_daily_taps`
- `walk_mrt_m`
- `mrt_daily_taps`
- `bus_daily_taps`
- `dist_mrt_m`
- `mrt_ring2`
- `walk_mrt_score`

### `housing_price` (4)

- `residential_weight`
- `hdb_median_psf`
- `hdb_median_price`
- `avg_gpr`

### `population` (6)

- `population`
- `elderly_pct`
- `elderly_count`
- `children_count`
- `walking_dependent_pct`
- `walking_dependent_count`

### `roads_signals` (22)

- `hex_avg_speed_kmh`
- `hex_seg_count`
- `hex_jam_segments`
- `hex_flow_segments`
- `hex_jam_pct`
- `hex_flow_pct`
- `road_cat_expressway`
- `road_cat_major_arterial`
- `road_cat_arterial`
- `road_cat_minor_arterial`
- `road_cat_small`
- `road_cat_slip`
- `ped_elderly`
- `ped_countdown`
- `ped_standard`
- `bicycle_signal`
- `sig_overhead`
- `sig_ground`
- `sig_beacon`
- `sig_filter_arrow`
- `sig_rag`
- `ped_crossings_total`

### `amenities_v9` (10)

- `hawker_centres`
- `hotels`
- `tourist_attractions`
- `chas_clinics`
- `preschools_gov`
- `silver_zones`
- `school_zones`
- `supermarkets`
- `parks`
- `formal_schools`

### `personas` (35)

- `p_persona_count`
- `p_median_age`
- `p_pct_young_18_30`
- `p_pct_working_31_60`
- `p_pct_senior_60plus`
- `p_pct_female`
- `p_pct_married`
- `p_pct_single`
- `p_pct_university`
- `p_pct_polytechnic`
- `p_pct_low_education`
- `p_pct_professional`
- `p_pct_retired`
- `p_pct_homemaker`
- `p_pct_student`
- `p_pct_unemployed`
- `p_pct_finance`
- `p_pct_tech`
- `p_pct_fnb`
- `p_pct_manufacturing`
- `p_pct_retail`
- `p_pct_health`
- `p_pct_construction`
- `p_pct_transport`
- `p_hobby_food`
- `p_hobby_fitness`
- `p_hobby_culture`
- `p_hobby_nature`
- `p_hobby_social`
- `p_hobby_shopping`
- `p_hobby_tech`
- `p_affluence_idx`
- `p_youth_idx`
- `p_family_idx`
- `p_retirement_idx`

### `walkability` (21)

- `walk_hawker_m`
- `walk_park_m`
- `walk_school_m`
- `walk_super_m`
- `walk_clinic_m`
- `walk_bus_m`
- `amenity_types_nearby`
- `walkability_score`
- `dist_bus_m`
- `dist_hawker_m`
- `dist_park_m`
- `dist_clinic_m`
- `dist_super_m`
- `walk_hawker_score`
- `walk_park_score`
- `walk_clinic_score`
- `walk_super_score`
- `walk_bus_score`
- `walkability_score_v2`
- `dist_school_m`
- `mg_mean_walkability`

### `v9_rings` (3)

- `pop_ring1`
- `pop_ring2`
- `hdb_ring1`

### `place_composition` (66)

- `pc_total`
- `pc_cat_shopping_retail`
- `pc_cat_restaurant`
- `pc_cat_services`
- `pc_cat_business`
- `pc_cat_beauty_personal_care`
- `pc_cat_education`
- `pc_cat_health_medical`
- `pc_cat_cafe_coffee`
- `pc_cat_fitness_recreation`
- `pc_cat_convenience_daily_needs`
- `pc_cat_hawker_street_food`
- `pc_cat_automotive`
- `pc_cat_transport`
- `pc_cat_civic_government`
- `pc_cat_bar_nightlife`
- `pc_cat_fast_food_qsr`
- `pc_cat_residential`
- `pc_cat_culture_entertainment`
- `pc_cat_office_workspace`
- `pc_cat_hospitality`
- `pc_cat_bakery_pastry`
- `pc_cat_general`
- `pc_cat_religious`
- `pc_cat_ngo`
- `pc_pct_cat_shopping_retail`
- `pc_pct_cat_restaurant`
- `pc_pct_cat_services`
- `pc_pct_cat_business`
- `pc_pct_cat_beauty_personal_care`
- `pc_pct_cat_education`
- `pc_pct_cat_health_medical`
- `pc_pct_cat_cafe_coffee`
- `pc_pct_cat_fitness_recreation`
- `pc_pct_cat_convenience_daily_needs`
- `pc_pct_cat_hawker_street_food`
- `pc_pct_cat_automotive`
- `pc_pct_cat_transport`
- `pc_pct_cat_civic_government`
- `pc_pct_cat_bar_nightlife`
- `pc_pct_cat_fast_food_qsr`
- `pc_pct_cat_residential`
- `pc_pct_cat_culture_entertainment`
- `pc_pct_cat_office_workspace`
- `pc_pct_cat_hospitality`
- `pc_pct_cat_bakery_pastry`
- `pc_pct_cat_general`
- `pc_pct_cat_religious`
- `pc_pct_cat_ngo`
- `pc_tier_luxury`
- `pc_tier_premium`
- `pc_tier_mid`
- `pc_tier_value`
- `pc_tier_budget`
- `pc_pct_tier_luxury`
- `pc_pct_tier_premium`
- `pc_pct_tier_mid`
- `pc_pct_tier_value`
- `pc_pct_tier_budget`
- `pc_unique_brands`
- `pc_branded_count`
- `pc_branded_pct`
- `pc_unique_place_types`
- `pc_cat_hhi`
- `pc_cat_entropy`
- `pc_seg_entropy`

### `micrograph` (19)

- `mg_n`
- `mg_mean_transit`
- `mg_mean_competitor`
- `mg_mean_complementary`
- `mg_mean_demand`
- `mg_mean_anchor_count`
- `mg_mean_comp_pressure`
- `mg_mean_demand_diversity`
- `mg_pct_hyperdense`
- `mg_pct_dense`
- `mg_pct_moderate`
- `mg_pct_sparse`
- `mg_cafe_n`
- `mg_cafe_mean_transit`
- `mg_cafe_mean_competitor`
- `mg_cafe_mean_complementary`
- `mg_cafe_mean_demand`
- `mg_cafe_mean_anchor_count`
- `mg_cafe_mean_comp_pressure`

### `neighbor_nbr1_mean` (28)

- `nbr1_mean_population`
- `nbr1_mean_elderly_count`
- `nbr1_mean_children_count`
- `nbr1_mean_walking_dependent_count`
- `nbr1_mean_bldg_count`
- `nbr1_mean_hdb_blocks`
- `nbr1_mean_bldg_footprint_sqm`
- `nbr1_mean_mrt_stations`
- `nbr1_mean_bus_stops`
- `nbr1_mean_pc_total`
- `nbr1_mean_pc_cat_restaurant`
- `nbr1_mean_pc_cat_cafe_coffee`
- `nbr1_mean_pc_cat_shopping_retail`
- `nbr1_mean_pc_cat_hawker_street_food`
- `nbr1_mean_pc_cat_health_medical`
- `nbr1_mean_pc_cat_education`
- `nbr1_mean_pc_cat_office_workspace`
- `nbr1_mean_pc_cat_bar_nightlife`
- `nbr1_mean_pc_unique_brands`
- `nbr1_mean_pc_cat_entropy`
- `nbr1_mean_p_affluence_idx`
- `nbr1_mean_p_family_idx`
- `nbr1_mean_p_youth_idx`
- `nbr1_mean_mg_mean_transit`
- `nbr1_mean_mg_mean_competitor`
- `nbr1_mean_mg_mean_complementary`
- `nbr1_mean_mg_mean_demand`
- `nbr1_mean_mg_mean_anchor_count`

### `neighbor_nbr1_max` (28)

- `nbr1_max_population`
- `nbr1_max_elderly_count`
- `nbr1_max_children_count`
- `nbr1_max_walking_dependent_count`
- `nbr1_max_bldg_count`
- `nbr1_max_hdb_blocks`
- `nbr1_max_bldg_footprint_sqm`
- `nbr1_max_mrt_stations`
- `nbr1_max_bus_stops`
- `nbr1_max_pc_total`
- `nbr1_max_pc_cat_restaurant`
- `nbr1_max_pc_cat_cafe_coffee`
- `nbr1_max_pc_cat_shopping_retail`
- `nbr1_max_pc_cat_hawker_street_food`
- `nbr1_max_pc_cat_health_medical`
- `nbr1_max_pc_cat_education`
- `nbr1_max_pc_cat_office_workspace`
- `nbr1_max_pc_cat_bar_nightlife`
- `nbr1_max_pc_unique_brands`
- `nbr1_max_pc_cat_entropy`
- `nbr1_max_p_affluence_idx`
- `nbr1_max_p_family_idx`
- `nbr1_max_p_youth_idx`
- `nbr1_max_mg_mean_transit`
- `nbr1_max_mg_mean_competitor`
- `nbr1_max_mg_mean_complementary`
- `nbr1_max_mg_mean_demand`
- `nbr1_max_mg_mean_anchor_count`

### `neighbor_nbr2_mean` (28)

- `nbr2_mean_population`
- `nbr2_mean_elderly_count`
- `nbr2_mean_children_count`
- `nbr2_mean_walking_dependent_count`
- `nbr2_mean_bldg_count`
- `nbr2_mean_hdb_blocks`
- `nbr2_mean_bldg_footprint_sqm`
- `nbr2_mean_mrt_stations`
- `nbr2_mean_bus_stops`
- `nbr2_mean_pc_total`
- `nbr2_mean_pc_cat_restaurant`
- `nbr2_mean_pc_cat_cafe_coffee`
- `nbr2_mean_pc_cat_shopping_retail`
- `nbr2_mean_pc_cat_hawker_street_food`
- `nbr2_mean_pc_cat_health_medical`
- `nbr2_mean_pc_cat_education`
- `nbr2_mean_pc_cat_office_workspace`
- `nbr2_mean_pc_cat_bar_nightlife`
- `nbr2_mean_pc_unique_brands`
- `nbr2_mean_pc_cat_entropy`
- `nbr2_mean_p_affluence_idx`
- `nbr2_mean_p_family_idx`
- `nbr2_mean_p_youth_idx`
- `nbr2_mean_mg_mean_transit`
- `nbr2_mean_mg_mean_competitor`
- `nbr2_mean_mg_mean_complementary`
- `nbr2_mean_mg_mean_demand`
- `nbr2_mean_mg_mean_anchor_count`

### `neighbor_contrast` (28)

- `contrast_population`
- `contrast_elderly_count`
- `contrast_children_count`
- `contrast_walking_dependent_count`
- `contrast_bldg_count`
- `contrast_hdb_blocks`
- `contrast_bldg_footprint_sqm`
- `contrast_mrt_stations`
- `contrast_bus_stops`
- `contrast_pc_total`
- `contrast_pc_cat_restaurant`
- `contrast_pc_cat_cafe_coffee`
- `contrast_pc_cat_shopping_retail`
- `contrast_pc_cat_hawker_street_food`
- `contrast_pc_cat_health_medical`
- `contrast_pc_cat_education`
- `contrast_pc_cat_office_workspace`
- `contrast_pc_cat_bar_nightlife`
- `contrast_pc_unique_brands`
- `contrast_pc_cat_entropy`
- `contrast_p_affluence_idx`
- `contrast_p_family_idx`
- `contrast_p_youth_idx`
- `contrast_mg_mean_transit`
- `contrast_mg_mean_competitor`
- `contrast_mg_mean_complementary`
- `contrast_mg_mean_demand`
- `contrast_mg_mean_anchor_count`

### `neighbor_rank` (28)

- `rank_population`
- `rank_elderly_count`
- `rank_children_count`
- `rank_walking_dependent_count`
- `rank_bldg_count`
- `rank_hdb_blocks`
- `rank_bldg_footprint_sqm`
- `rank_mrt_stations`
- `rank_bus_stops`
- `rank_pc_total`
- `rank_pc_cat_restaurant`
- `rank_pc_cat_cafe_coffee`
- `rank_pc_cat_shopping_retail`
- `rank_pc_cat_hawker_street_food`
- `rank_pc_cat_health_medical`
- `rank_pc_cat_education`
- `rank_pc_cat_office_workspace`
- `rank_pc_cat_bar_nightlife`
- `rank_pc_unique_brands`
- `rank_pc_cat_entropy`
- `rank_p_affluence_idx`
- `rank_p_family_idx`
- `rank_p_youth_idx`
- `rank_mg_mean_transit`
- `rank_mg_mean_competitor`
- `rank_mg_mean_complementary`
- `rank_mg_mean_demand`
- `rank_mg_mean_anchor_count`
