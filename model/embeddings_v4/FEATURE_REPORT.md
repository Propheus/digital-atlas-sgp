# Subzone Embedding Model V4 — Feature Report

**Date:** 2026-03-27
**Matrix:** 332 subzones × 351 features → 32-dim embeddings
**Micrographs:** 93,788 (from 174K places, V3 pipeline with 10,896 anchors)

---

## Summary

| Metric | Value |
|---|---|
| Total features | 351 |
| Subzones | 332 |
| Embedding dimensions | 32 |
| Micrograph features | 156 (44% of total) |
| AE Reconstruction MSE | 0.179 |
| GNN Reconstruction MSE | 0.110 |
| Data sources | 11 |

---

## Feature Groups (351 total)

### 1. Micrograph Features — 156 features (44%)
Per-subzone aggregations from 93,788 place-level micrographs across 12 categories.

Each category contributes ~13 features:
- **Context vector means** (transit, competitor, complementary, demand) — what drives places in this subzone
- **Anchor count** — average anchors per place
- **Competitive pressure** — average T2 weight
- **Density band distribution** (% hyperdense, dense, moderate, sparse)
- **Average walk time** to anchors
- **T1 anchor diversity** — entropy of anchor types (MRT vs mall vs hawker vs hotel)
- **Gap percentage** — % of places with missing tier quotas
- **Place count** — how many places of this category in the subzone

| Category | Features | Places | What It Captures |
|---|---|---|---|
| Cafe | 13 | 6,749 | Coffee shop competitive landscape |
| Restaurant | 13 | 16,753 | Dining ecosystem structure |
| Hawker | 13 | 6,016 | Street food density and access |
| Fast Food/QSR | 13 | 3,314 | Quick-serve competition |
| Bakery | 13 | 2,645 | Pastry/bakery presence |
| Bar & Nightlife | 13 | 3,307 | Nightlife character |
| Beauty | 12 | 10,678 | Salon/spa ecosystem |
| Health | 13 | 5,849 | Medical facility coverage |
| Fitness | 13 | 3,527 | Gym/sports infrastructure |
| Education | 13 | 8,677 | School/tuition density |
| Shopping | 13 | 19,874 | Retail structure |
| Convenience | 12 | 6,399 | Daily needs coverage |

### 2. Place Counts — 32 features
Raw count of places per category per subzone from the 174K consolidated dataset.

Includes: `n_restaurant`, `n_cafe_coffee`, `n_shopping_retail`, `n_hawker_street_food`, `n_education`, `n_health_medical`, `n_beauty_personal_care`, `n_fitness_recreation`, `n_bar_nightlife`, `n_fast_food_qsr`, `n_bakery_pastry`, `n_convenience_daily_needs`, `n_automotive`, `n_business`, `n_services`, `n_hospitality`, `n_office_workspace`, `n_transport`, `n_residential`, `n_civic_government`, `n_culture_entertainment`, `n_religious`, `n_ngo`, `n_general`, `n_places` (total), `n_buildings`, `n_bus_stops`, `n_subway_stations`, `n_food_drink`, `n_retail`, `n_beauty`, `n_raw_categories`

### 3. Demand & Gravity — 26 features
Demand signals by time of day, gravity model flows, trade area metrics.

- **Time-of-day demand:** `demand_morning`, `demand_lunch`, `demand_evening`, `demand_weekend`, `demand_workers`, `demand_local`
- **Gravity model:** `gravity_in`, `gravity_out`, `gravity_net` — net flow of commercial influence
- **Trade area:** `trade_area_tracts`, `inbound_tract_count` — how many subzones feed demand here
- **Composite scores:** `buzz`, `synergy`, `tension`, `effective_demand`
- **Commute:** `commute_inflow`, `commute_outflow`, `commute_ratio`

### 4. V2 Category Counts — 24 features
Recounted from the 174K consolidated places (vs original 66K).

Same 24 categories as Place Counts but from the V2 dataset which includes 108K new Overture places.

### 5. Base Features — 24 features
Area, planning metrics, food coverage, diversity indices.

Includes: `area_km2`, `avg_gpr` (gross plot ratio), `category_entropy`, `diversity_index`, `fnb_coverage_ratio`, `food_drink_pct`, `green_ratio`, `place_density`, `total_places`, `cafe_count`, `cafes_independent`, `hotel_count_1km`, `sfa_eating_count`, `chas_clinic_count`, `preschool_count_gov`, `our_place_count`, `amenity_score`, `zoning_commercial_pct`, `zoning_manufacturing_pct`

### 6. Land Use / Zoning — 11 features
URA Master Plan zoning distribution.

`lu_residential_pct`, `lu_commercial_pct`, `lu_industrial_pct`, `lu_mixed_use_pct`, `lu_institutional_pct`, `lu_nature_pct`, `lu_open_space_pct`, `lu_reserve_pct`, `lu_transport_pct`, `lu_other_pct`, `lu_entropy`

### 7. Transit & Mobility — 11 features
MRT, bus, and transit accessibility.

`transit_score` (0-100), `mrt_stations_1km`, `bus_stop_count_1km`, `bus_density`, `nearest_subway_m`, `nearby_daily_ridership`, `pct_transit_commuters`, `transit_combined_score`, `transit_degree` (graph connectivity)

### 8. Brand & Quality — 11 features
Brand penetration and place quality.

`avg_rating`, `median_rating`, `avg_reviews`, `total_reviews`, `high_rated_pct`, `branded_count`, `branded_pct`, `unique_brand_count`, `brand_entropy`, `brand_hhi`, `chain_indie_ratio`

### 9. Demographics — 10 features
Population and demographic profile.

`population`, `pop_density`, `elderly_pct`, `male_pct`, `median_age`, `resident_workers`, `cafes_per_1000pop`, `restaurants_per_1000pop`, `crime_per_1000pop_score`, `zoning_residential_pct`

### 10. Housing & Property — 10 features
Dwelling type mix and property values.

`hdb_1__and_2_room_flats_pct`, `hdb_3_room_flats_pct`, `hdb_4_room_flats_pct`, `hdb_5_room_and_executive_flats_pct`, `condominiums_and_other_apartments_pct`, `landed_properties_pct`, `median_hdb_psf`, `hdb_price_yoy`, `median_rent`, `pct_renters`

### 11. Amenity Proximity — 9 features
Distance to key amenities and counts within 1km.

`dist_nearest_mrt`, `dist_nearest_hawker`, `dist_nearest_park`, `dist_nearest_school`, `dist_nearest_supermarket`, `hawkers_within_1km`, `parks_within_1km`, `schools_within_1km`, `supermarkets_within_1km`

### 12. Infrastructure — 7 features
Road and building characteristics.

`road_density`, `total_road_km`, `building_density`, `avg_height`, road/building density scores

### 13. Socioeconomic — 5 features
Income and economic indicators.

`median_income`, `pct_high_income_hh`, `pct_low_income_hh`, `poverty_rate`, `pct_zero_vehicle`

### 14. Cross-Boundary Flows — 4 features
From micrograph anchor analysis: how many anchors cross subzone boundaries.

`flow_inflow` (anchors pointing IN from other subzones), `flow_outflow` (anchors pointing OUT), `flow_ratio` (in/out), `flow_total`

### 15. Model Predictions — 4 features
From density prediction model (R²=0.773).

`predicted_total`, `density_gap`, `cafe_gap_score`, `vacancy_rate`

### 16. ACRA Business Registry — 3 features
From 2M registered business entities matched to subzones.

`acra_total` (matched entities), `acra_churn` (cessation rate), `acra_avg_age` (average business age in years)

### 17. Price Tier & Diversity — 5 features
From V2 place classification.

`v2_pct_mid`, `v2_tier_mid`, `place_type_diversity` (unique place types), `segment_entropy`, `v2_branded` (branded count)

### 18. Graph Connectivity — 1 feature
From subzone adjacency graph.

`adjacency_degree` (number of neighboring subzones)

---

## Data Sources

| # | Source | Records | Features Derived |
|---|---|---|---|
| 1 | **Micrograph V3 pipeline** | 93,788 micrographs | 156 |
| 2 | **Consolidated places V2** | 174,711 places | 51 |
| 3 | **Tract profiles** (pre-computed) | 332 subzones × 173 fields | 81 |
| 4 | **URA Master Plan** | 113,212 land parcels | 11 |
| 5 | **Census 2025** | 332 subzones | 10 |
| 6 | **HDB resale / property** | 514K transactions | 10 |
| 7 | **Transit (LTA)** | 231 MRT + 5,177 bus stops | 11 |
| 8 | **ACRA business registry** | 2,076,437 entities | 3 |
| 9 | **Amenities (data.gov.sg)** | Hawkers, schools, parks, clinics | 9 |
| 10 | **Graph analysis** | Adjacency + transit + cross-boundary | 5 |
| 11 | **Density model V5** | R²=0.773 predictions | 4 |

---

## Model Performance

| Metric | Autoencoder | GNN |
|---|---|---|
| Architecture | 351→[128,64]→32→[64,128]→351 | 351→proj(256)→GNN(128)→GNN(64)→GNN(32)→dec(351) |
| Reconstruction MSE | 0.179 | **0.110** |
| Separation | **0.683** | 0.595 |
| Silhouette | 0.101 | **0.363** |
| Active dims | **32/32** | 20/32 |
| Graph edges | N/A | 5,846 (adj + transit + micrograph cross-boundary) |
| Best for | Global comparison, gap analysis | Spatial clustering, neighborhood context |
