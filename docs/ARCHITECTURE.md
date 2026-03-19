# Digital Atlas SGP — Representation Architecture

## The Core Idea

Every subzone in Singapore can be described by a dense vector that captures:
- **What exists there** (places, buildings, infrastructure)
- **Who lives there** (demographics, income, housing)
- **How it connects** (transit, roads, accessibility)
- **What the rules say** (zoning, land use, density limits)
- **How it behaves** (prices, ratings, activity levels)

When you combine these into a single representation and train a model to predict
missing pieces, the model learns the **latent rules of urban composition**.

---

## LAYER 1: SUBZONE REGION VECTOR

Each of the 332 subzones gets a feature vector composed of these blocks:

### 1A. Demographics Block (~30 dims)
Source: `census/pop_age_sex.csv`, `pop_ethnic_sex.csv`, `pop_dwelling.csv`

| Feature | Dims | Description |
|---------|------|-------------|
| pop_total | 1 | Total resident population |
| pop_density | 1 | Population per km² |
| age_distribution | 13 | % in each 5-year bracket (0-4, 5-9, ..., 60-64, 65+) |
| youth_ratio | 1 | % under 15 |
| working_age_ratio | 1 | % 15-64 |
| elderly_ratio | 1 | % 65+ |
| dependency_ratio | 1 | (young + old) / working-age |
| ethnic_chinese_pct | 1 | % Chinese |
| ethnic_malay_pct | 1 | % Malay |
| ethnic_indian_pct | 1 | % Indian |
| ethnic_others_pct | 1 | % Others |
| gender_ratio | 1 | Males / Females |
| hh_median_income* | 1 | Estimated from planning area → subzone |
| hh_income_gini* | 1 | Income inequality proxy |
| hh_avg_size* | 1 | Average household size |

*Distributed from planning area to subzone using dwelling type as proxy

### 1B. Housing & Built Form Block (~20 dims)
Source: `housing/`, `buildings/buildings.geojson`

| Feature | Dims | Description |
|---------|------|-------------|
| dwelling_hdb_pct | 1 | % HDB dwellings |
| dwelling_condo_pct | 1 | % condos/apartments |
| dwelling_landed_pct | 1 | % landed properties |
| hdb_1_2_room_pct | 1 | % 1-2 room HDB (proxy for low income) |
| hdb_3_room_pct | 1 | % 3 room |
| hdb_4_room_pct | 1 | % 4 room |
| hdb_5_room_exec_pct | 1 | % 5 room / executive |
| median_resale_psf | 1 | Median HDB resale price per sqft |
| resale_price_trend | 1 | YoY price change |
| avg_building_height | 1 | Average building height/levels |
| max_building_height | 1 | Tallest building levels |
| building_density | 1 | Built footprint area / subzone area |
| total_built_area | 1 | Sum of all building footprint areas |
| floor_area_ratio | 1 | Total floor area / subzone land area |
| building_type_resi_pct | 1 | % residential buildings |
| building_type_comm_pct | 1 | % commercial buildings |
| building_type_ind_pct | 1 | % industrial buildings |
| avg_building_age | 1 | Average year_completed |
| hdb_block_count | 1 | Number of HDB blocks |
| building_count | 1 | Total building count |

### 1C. Land Use Block (~15 dims)
Source: `land_use/master_plan_land_use.geojson`

| Feature | Dims | Description |
|---------|------|-------------|
| lu_residential_pct | 1 | % area zoned residential |
| lu_commercial_pct | 1 | % commercial |
| lu_industrial_pct | 1 | % industrial (B1/B2) |
| lu_mixed_use_pct | 1 | % mixed use |
| lu_open_space_pct | 1 | % park/open space |
| lu_institutional_pct | 1 | % civic/institutional |
| lu_transport_pct | 1 | % transport facilities |
| lu_reserve_pct | 1 | % reserve/special use |
| lu_white_pct | 1 | % white site (flexible) |
| avg_gpr | 1 | Average gross plot ratio |
| max_gpr | 1 | Maximum GPR allowed |
| lu_entropy | 1 | Shannon entropy of land use mix |
| lu_dominant_type | 1 | One-hot encoded dominant type |
| developable_ratio | 1 | % of area that can be developed |
| green_ratio | 1 | (park + nature) / total area |

### 1D. Transit & Accessibility Block (~20 dims)
Source: `transit/`, `roads/roads.geojson`

| Feature | Dims | Description |
|---------|------|-------------|
| mrt_station_count | 1 | MRT/LRT stations in/adjacent to subzone |
| mrt_station_dist_min | 1 | Distance to nearest MRT (meters) |
| mrt_station_dist_avg | 1 | Average distance to 3 nearest MRT |
| mrt_exit_count | 1 | Number of MRT exits |
| bus_stop_count | 1 | Bus stops in subzone |
| bus_stop_density | 1 | Bus stops per km² |
| road_density | 1 | Total road length / subzone area |
| road_intersection_density | 1 | Intersections per km² (walkability proxy) |
| highway_access | 1 | Binary: expressway within 500m |
| primary_road_length | 1 | Length of primary/trunk roads |
| secondary_road_length | 1 | Length of secondary roads |
| residential_road_length | 1 | Length of residential streets |
| service_road_length | 1 | Length of service roads |
| pedestrian_path_length | 1 | Length of footways/pedestrian paths |
| cycling_path_length | 1 | Length of cycleways |
| traffic_signal_count | 1 | Number of traffic signals |
| ev_charging_count | 1 | EV charging stations |
| parking_area | 1 | Total parking area (from land use) |
| connectivity_score | 1 | Graph-based reachability metric |
| avg_block_size | 1 | Average road block perimeter (walkability) |

### 1E. Amenities & Services Block (~15 dims)
Source: `amenities/`

| Feature | Dims | Description |
|---------|------|-------------|
| school_count | 1 | Total schools |
| preschool_count | 1 | Preschools |
| primary_school_count | 1 | Primary schools |
| healthcare_facility_count | 1 | Clinics + hospitals |
| park_count | 1 | Parks in/adjacent |
| park_area_pct | 1 | % of subzone that is park |
| park_nearest_dist | 1 | Distance to nearest park |
| hawker_centre_count | 1 | Hawker centres |
| supermarket_count | 1 | Supermarkets |
| hotel_count | 1 | Hotels |
| hotel_total_rooms | 1 | Total hotel rooms |
| community_centre_count | 1 | Community centres |
| religious_facility_count | 1 | Temples, mosques, churches |
| park_connector_access | 1 | Distance to nearest PCN |
| eating_establishment_count | 1 | Licensed eating places |

---

## LAYER 2: PLACE COMPOSITION VECTOR

### 2A. Category Distribution (~24 dims)
For each subzone, the composition of place main_categories:

```
[cafe_pct, restaurant_pct, retail_pct, beauty_pct, fitness_pct, 
 education_pct, health_pct, fnb_pct, convenience_pct, ...]
```

This is the PRIMARY signal for masked category prediction.

### 2B. Place Type Distribution (~50 dims, top 50 place_types)
More granular: what specific types exist

```
[hawker_stall_count, cafe_count, gym_count, clinic_count, 
 convenience_store_count, bakery_count, hair_salon_count, ...]
```

### 2C. Brand Density (~10 dims)
| Feature | Description |
|---------|-------------|
| branded_place_count | Number of branded places |
| branded_pct | % of places that are branded |
| unique_brand_count | Number of distinct brands |
| chain_ratio | Chains / independents |
| luxury_count | Luxury-tagged places |
| top_brand_concentration | HHI of brand market share |
| fnb_chain_pct | % of F&B that are chains |
| retail_chain_pct | % of retail that are chains |
| brand_diversity | Shannon entropy of brands |
| avg_rating | Average rating across all places |

### 2D. Quality Signals (~8 dims)
| Feature | Description |
|---------|-------------|
| avg_rating | Mean rating |
| median_rating | Median rating |
| rating_std | Rating variance |
| high_rated_pct | % with rating >= 4.5 |
| total_reviews | Sum of all review counts |
| avg_reviews | Mean review count |
| has_phone_pct | % of places with phone |
| has_website_pct | % of places with website |

---

## LAYER 3: PLACE-LEVEL SPATIAL CONTEXT

For each individual place, compute:

### 3A. Competitor Density (per place)
| Feature | Description |
|---------|-------------|
| same_type_100m | Count of same place_type within 100m |
| same_type_200m | Within 200m |
| same_type_500m | Within 500m |
| same_category_100m | Same main_category within 100m |
| same_category_200m | Within 200m |
| same_category_500m | Within 500m |
| all_places_100m | Total places within 100m |
| all_places_200m | Within 200m |
| all_places_500m | Within 500m |

### 3B. Transit Proximity (per place)
| Feature | Description |
|---------|-------------|
| dist_nearest_mrt | Meters to nearest MRT station |
| dist_nearest_bus | Meters to nearest bus stop |
| bus_stops_300m | Bus stops within 300m walk |
| mrt_within_500m | Binary: MRT within 500m |
| transit_score | Composite transit accessibility |

### 3C. Complementary Context (per place)
| Feature | Description |
|---------|-------------|
| nearby_cafes_200m | Complementary: cafes near gym |
| nearby_retail_200m | Retail near restaurant |
| nearby_parking_200m | Parking near mall |
| place_diversity_200m | Shannon entropy of types within 200m |
| anchor_tenant_nearby | Major brand/mall within 500m |

---

## LAYER 4: GRAPH STRUCTURE

### 4A. Subzone Adjacency Graph
- Nodes: 332 subzones
- Edges: shared boundary (Queen contiguity)
- Edge weight: shared boundary length
- Used for GNN message passing

### 4B. Place Co-location Graph
- Nodes: 165 place_types
- Edges: PMI (Pointwise Mutual Information) of co-occurrence in subzones
- Positive PMI = types that co-locate (cafe + coworking)
- Negative PMI = types that avoid each other (industrial + preschool)

### 4C. Transit Connectivity Graph
- Nodes: 332 subzones
- Edges: direct MRT/bus connectivity between subzones
- Edge weight: frequency of service / travel time

---

## TOTAL FEATURE DIMENSIONALITY

| Block | Dims |
|-------|------|
| Demographics | ~30 |
| Housing & Built Form | ~20 |
| Land Use | ~15 |
| Transit & Accessibility | ~20 |
| Amenities & Services | ~15 |
| Category Distribution | ~24 |
| Place Type Distribution | ~50 |
| Brand Density | ~10 |
| Quality Signals | ~8 |
| **Subzone Total** | **~192 dims** |

Plus per-place features (~20 dims each) and graph structure.

---

## TRAINING OBJECTIVE

### Self-Supervised: Masked Category Prediction

1. For each subzone, randomly mask 20-30% of place categories
2. Task: predict the masked categories from:
   - Remaining visible categories
   - Full region vector (demographics, housing, transit, land use)
   - Graph neighbor information (GNN)
   - Place-level spatial context
3. Loss: cross-entropy over masked category distribution

### What the Model Learns

- "This subzone has demographics X, housing Y, transit Z → it SHOULD have N cafes, M clinics, K gyms"
- "Neighboring subzones have pattern P → this zone likely has pattern Q"
- "The land use says commercial + high GPR → expect dense retail, F&B, offices"

### Architecture: Hybrid MLP-GNN

```
Input:
  subzone_vector (192d) ──→ MLP Encoder ──→ latent (64d)
                                                 │
  graph adjacency ──→ GCN layers (2-3) ──────────┤
                                                 │
  place-level context ──→ Attention Pool ────────┤
                                                 │
                                         Fusion Layer (64d)
                                                 │
                                         Prediction Head
                                                 │
                                    Masked Category Distribution
```

---

## DOWNSTREAM APPLICATIONS

### 1. Gap Analysis
- Model predicts "this subzone should have 5 cafes" but only 2 exist
- Gap = predicted - observed → opportunity signal

### 2. Location Scoring
- Given a place type, score every subzone for fit
- High score = model says this type belongs here but is underserved

### 3. Cannibalization Risk
- Competitor density + model prediction → is the area saturated?

### 4. Urban Anomaly Detection
- Subzones where observed ≠ predicted by large margin
- Could be: emerging area, declining area, or data gap

### 5. What-If Simulation
- "If we add an MRT station here, what categories should appear?"
- Modify transit features → re-run prediction → see category shift

---

## COMPUTATION PIPELINE

```
Step 1: Aggregate all data to subzone level
         → subzone_features.parquet (332 × 192)

Step 2: Compute per-place spatial features
         → place_features.parquet (66,851 × 20)

Step 3: Build adjacency graphs
         → subzone_adjacency.json
         → colocation_pmi.json
         → transit_graph.json

Step 4: Train MLP-GNN with masked category prediction
         → model weights

Step 5: Run inference → gap scores per subzone × category
         → gap_analysis.parquet
```

---

*Architecture designed: 2026-03-19*
