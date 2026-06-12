# Subzone Feature Map — V5 Model (431 features)

**Model:** V5 Autoencoder (431 → [128, 64] → 32-dim embedding)
**Subzones:** 332
**Data sources:** 174K places, 93K micrographs, 10,896 anchors, 2M ACRA entities, 514K property transactions

---

## Feature Composition

| Theme | Features | % | Description |
|---|---|---|---|
| Micrograph | 154 | 36% | Per-category spatial context from 93K place-level graphs |
| Neighbor Context | 60 | 14% | Ego-graph: self vs neighbors, boundary permeability |
| Place Composition | 58 | 13% | Category counts, price tiers, brand signal |
| Demand | 26 | 6% | Time-of-day demand, gravity flows, trade area |
| Accessibility | 26 | 6% | Transit, positioning, amenity proximity |
| Built Environment | 23 | 5% | Land use zoning, road/building density |
| Other (base) | 15 | 3% | F&B coverage, hotel proximity, SFA eating |
| Demographics | 11 | 3% | Population, age bands, workers |
| Brand & Quality | 11 | 3% | Ratings, brand penetration, chain ratio |
| Multi-Scale | 10 | 2% | Ring-2 (2-hop) and planning area aggregates |
| Housing | 7 | 2% | HDB/condo/landed dwelling type mix |
| Property Market | 7 | 2% | HDB resale, private PSF, transaction volumes |
| Socioeconomic | 6 | 1% | Income, poverty, vehicle ownership |
| Diversity | 5 | 1% | Category entropy, segment diversity |
| Spatial Flows | 4 | 1% | Cross-boundary micrograph anchor flows |
| Model Output | 4 | 1% | Density gap predictions |
| Business Health | 3 | 1% | ACRA churn, business age |
| Geography | 1 | 0% | Subzone area |

---

## 1. Micrograph (154 features)

Per-subzone aggregations from 93,788 place-level micrographs across 12 categories. Each category contributes ~13 features.

### Per-Category Features (×12 categories)

| Feature | What it measures |
|---|---|
| `mg_{cat}_cv_transit` | Mean T1 (transit anchor) weight across places |
| `mg_{cat}_cv_competitor` | Mean T2 (competitor) weight |
| `mg_{cat}_cv_complementary` | Mean T3 (complementary) weight |
| `mg_{cat}_cv_demand` | Mean T4 (demand magnet) weight |
| `mg_{cat}_anchor_count` | Average anchors per place |
| `mg_{cat}_competitive_pressure` | Average competitive pressure (T2 density) |
| `mg_{cat}_pct_hyperdense` | % of places in hyperdense band |
| `mg_{cat}_pct_dense` | % in dense band |
| `mg_{cat}_pct_moderate` | % in moderate band |
| `mg_{cat}_pct_sparse` | % in sparse band |
| `mg_{cat}_avg_walk` | Average walk time to anchors (seconds) |
| `mg_{cat}_t1_diversity` | Shannon entropy of T1 anchor types |
| `mg_{cat}_count` | Number of places of this category |

### Categories

| Prefix | Category | Places |
|---|---|---|
| `mg_cafe_` | Cafe & Coffee | 6,749 |
| `mg_rest_` | Restaurant | 16,753 |
| `mg_hawk_` | Hawker & Street Food | 6,016 |
| `mg_fast_` | Fast Food & QSR | 3,314 |
| `mg_bake_` | Bakery & Pastry | 2,645 |
| `mg_bar__` | Bar & Nightlife | 3,307 |
| `mg_beau_` | Beauty & Personal Care | 10,678 |
| `mg_heal_` | Health & Medical | 5,849 |
| `mg_fitn_` | Fitness & Recreation | 3,527 |
| `mg_educ_` | Education | 8,677 |
| `mg_shop_` | Shopping & Retail | 19,874 |
| `mg_conv_` | Convenience & Daily Needs | 6,399 |

---

## 2. Neighbor Context (60 features)

Ego-graph features computed from subzone adjacency graph. 11 high-signal base features × 5 aggregate types + 5 boundary features.

### Boundary Profile (5 features)

| Feature | What it measures |
|---|---|
| `nbr_count` | Number of adjacent subzones |
| `adjacency_degree` | Graph degree (same as nbr_count) |
| `avg_permeability` | Mean permeability score across boundaries |
| `min_permeability` | Lowest permeability (hardest boundary) |
| `max_neighbor_poi_density` | Strongest commercial neighbor's density |

### Ego-Graph Aggregates (55 features: 11 base × 5 types)

**Base features:**
`pop_density`, `total_places`, `place_density`, `fnb_density`, `hhi`, `entropy`, `n_shopping`, `mrt_count`, `hdb_psf`, `transit_score`, `effective_demand`

**Aggregate types:**

| Type | Prefix | What it measures |
|---|---|---|
| Weighted Mean | `nbr_mean_{X}` | What's the neighborhood average? |
| Maximum | `nbr_max_{X}` | What's the strongest neighbor? |
| Std Deviation | `nbr_std_{X}` | How diverse are neighbors? |
| Contrast | `contrast_{X}` | Self minus neighbor mean (+ = oversupplied, - = undersupplied) |
| Rank | `rank_{X}` | Position among self + neighbors (0 = lowest, 1 = highest) |

---

## 3. Place Composition (58 features)

### Category Counts (31 features)
`n_restaurant`, `n_cafe_coffee`, `n_shopping_retail`, `n_hawker_street_food`, `n_education`, `n_health_medical`, `n_beauty_personal_care`, `n_fitness_recreation`, `n_bar_nightlife`, `n_fast_food_qsr`, `n_bakery_pastry`, `n_convenience_daily_needs`, `n_automotive`, `n_business`, `n_services`, `n_hospitality`, `n_office_workspace`, `n_transport`, `n_residential`, `n_civic_government`, `n_culture_entertainment`, `n_religious`, `n_ngo`, `n_general`, `n_places`, `n_buildings`, `n_bus_stops`, `n_subway_stations`, `n_food_drink`, `n_retail`, `n_beauty`

### V2 Category Counts (24 features)
Same 24 categories re-counted from 174K consolidated places: `v2_cat_restaurant`, `v2_cat_cafe_&_cof`, `v2_cat_shopping_&`, etc.

### Price Tier (2 features)
`v2_pct_mid`, `v2_tier_mid`

### Brand Signal (1 feature)
`v2_branded` — count of branded places

---

## 4. Demand (26 features)

### Time-of-Day Demand (11)
`demand_morning`, `demand_morning_score`, `demand_lunch`, `demand_lunch_score`, `demand_evening`, `demand_evening_score`, `demand_weekend`, `demand_workers`, `demand_local`, `effective_demand`, `effective_demand_score`

### Gravity Model (5)
`gravity_in`, `gravity_in_score`, `gravity_out`, `gravity_net`, `gravity_net_score`

### Commute Flows (3)
`commute_inflow`, `commute_outflow`, `commute_ratio`

### Trade Area (4)
`trade_area_tracts`, `trade_area_tracts_score`, `inbound_tract_count`, `inbound_tract_count_score`

### Composite Scores (3)
`buzz`, `synergy`, `tension`

---

## 5. Accessibility (26 features)

### Transit (11)
`transit_score`, `transit_combined_score`, `transit_degree`, `mrt_stations_1km`, `bus_stop_count_1km`, `bus_density`, `bus_density_score`, `nearest_subway_m`, `nearby_daily_ridership`, `nearby_daily_ridership_score`, `pct_transit_commuters`

### Positioning (5)
`dist_to_cbd_m`, `dist_to_nearest_rc_m`, `has_interchange`, `mrt_type_count`, `is_cbd_area`

### Amenity Proximity (5)
`dist_nearest_mrt`, `dist_nearest_hawker`, `dist_nearest_park`, `dist_nearest_school`, `dist_nearest_supermarket`

### Amenity Density (4)
`hawkers_within_1km`, `parks_within_1km`, `schools_within_1km`, `supermarkets_within_1km`

### Composite (1)
`amenity_score`

---

## 6. Built Environment (23 features)

### Land Use Zoning (11)
`lu_residential_pct`, `lu_commercial_pct`, `lu_industrial_pct`, `lu_mixed_use_pct`, `lu_institutional_pct`, `lu_nature_pct`, `lu_open_space_pct`, `lu_reserve_pct`, `lu_transport_pct`, `lu_other_pct`, `lu_entropy`

### Road Network (4)
`road_density`, `road_density_score`, `total_road_km`, `total_road_km_score`

### Building Stock (4)
`avg_gpr`, `avg_height`, `building_density`, `building_density_score`

### Green Space (1)
`green_ratio`

### Zoning Summary (3)
`zoning_commercial_pct`, `zoning_manufacturing_pct`, `zoning_residential_pct`

---

## 7. Demographics (11 features)

### Population (7)
`population`, `pop_density`, `elderly_pct`, `male_pct`, `median_age`, `resident_workers`, `daytime_workers`, `daytime_ratio`

### Age Distribution (4)
`pct_age_0_14`, `pct_age_15_34`, `pct_age_35_54`, `pct_age_55_plus`

---

## 8. Brand & Quality (11 features)

### Brand Penetration (6)
`branded_count`, `branded_pct`, `unique_brand_count`, `brand_entropy`, `brand_hhi`, `chain_indie_ratio`

### Ratings (5)
`avg_rating`, `median_rating`, `avg_reviews`, `total_reviews`, `high_rated_pct`

---

## 9. Multi-Scale (10 features)

### Ring 2 — 2-hop neighbors (5)
`ring2_mean_pop_density`, `ring2_mean_poi_density`, `ring2_mean_hdb_psf`, `ring2_total_shopping`, `ring2_count`

### Planning Area aggregates (5)
`pa_mean_pop_density`, `pa_mean_poi_density`, `pa_mean_hdb_psf`, `pa_subzone_count`, `pa_total_pop`

---

## 10. Housing (7 features)

### HDB Dwelling Type (5)
`hdb_1__and_2_room_flats_pct`, `hdb_3_room_flats_pct`, `hdb_4_room_flats_pct`, `hdb_5_room_and_executive_flats_pct`, `hdb_txn_volume_recent`

### Private Dwelling (2)
`condominiums_and_other_apartments_pct`, `landed_properties_pct`

---

## 11. Property Market (7 features)

### HDB Resale (2)
`median_hdb_psf`, `hdb_price_yoy`

### Rental (2)
`median_rent`, `pct_renters`

### Transaction Volume (3)
`private_median_psf`, `private_price_range`, `private_txn_volume`

---

## 12. Socioeconomic (6 features)

### Income & Wealth (5)
`median_income`, `pct_high_income_hh`, `pct_low_income_hh`, `poverty_rate`, `pct_zero_vehicle`

### Safety (1)
`crime_per_1000pop_score`

---

## 13. Diversity (5 features)
`category_entropy`, `category_entropy_score`, `diversity_index`, `place_type_diversity`, `segment_entropy`

---

## 14. Spatial Flows (4 features)
`flow_inflow`, `flow_outflow`, `flow_ratio`, `flow_total`

---

## 15. Model Output (4 features)
`predicted_total`, `density_gap`, `cafe_gap_score`, `vacancy_rate`

---

## 16. Business Health (3 features)
`acra_total`, `acra_churn`, `acra_avg_age`

---

## 17. Geography (1 feature)
`area_km2`

---

## 18. Other / Base (15 features)
`total_places`, `place_density`, `place_density_score`, `cafe_count`, `cafes_branded`, `cafes_independent`, `cafes_per_1000pop`, `restaurants_per_1000pop`, `food_drink_pct`, `fnb_coverage_ratio`, `hotel_count_1km`, `our_place_count`, `sfa_eating_count`, `chas_clinic_count`, `preschool_count_gov`
