# SGP Digital Atlas — Complete Context Document

**Version:** 2.0  
**Date:** 2026-04-20  
**Repo:** `Propheus/digital-atlas-sgp`  
**Servers:** atlas-1 (10.2.2.5, processing), atlas-deploy (10.2.2.7, serving)  
**Local:** `/Users/sumanth/propheus-projs/da-sgp/digital-atlas-sgp`  

---

## 1. What This Is

A mathematical representation of Singapore's urban-commercial structure. Every neighborhood, every planning unit, and every commercial place described by a structured feature vector — capturing what it is, what surrounds it, who needs it, how well it's served, and whether it fits its context.

**Total footprint:** 843 MB of processed data, 1,794 unique features across 4 spatial levels.

---

## 2. Scale

| Dimension | Value |
|---|---|
| **Area** | 771 km² (Singapore mainland + islands) |
| **Population** | 5,982,320 (4,212,320 residents + 1,770,000 non-residents) |
| **Commercial places** | 174,711 (Overture Maps + OSM + LLM-classified) |
| **Buildings** | 377,331 (Overture fused with OSM) |
| **Road segments** | 550,991 (OSM pedestrian network: 213,978 nodes) |
| **Transit** | 231 rail stations (187 MRT + 44 LRT), 5,172 bus stops |
| **Transit ridership** | 12.3M daily taps (5.9M MRT + 6.9M bus) |
| **GTFS trips** | 230,914 weekday trips across 602 routes |
| **Data sources** | 19 independent layers |
| **HDB blocks** | 10,431 (housing 80% of population) |
| **Subzones** | 332 (URA Master Plan) |
| **Planning areas** | 55 |
| **Regions** | 5 (Central, East, North, North-East, West) |

---

## 3. Spatial Levels

```
┌─────────────────────────────────────────────────┐
│  SUBZONE (326)         ~2.4 km²    ~449 features │  Policy alignment
├─────────────────────────────────────────────────┤
│  HEX-8 (1,191)        ~0.74 km²   628 features  │  PRIMARY: neighborhood analysis
├─────────────────────────────────────────────────┤
│  HEX-9 (7,318)        ~0.11 km²   603 features  │  Fine-grain: place context
├─────────────────────────────────────────────────┤
│  PLACES (174,711)      Point       114 features  │  Micro: individual business
└─────────────────────────────────────────────────┘
```

| Level | Units | Features | Grain | Primary use |
|---|---:|---:|---|---|
| **Subzone** | 326 | ~449 | URA planning unit | Policy, reporting, census alignment |
| **Hex-8** | 1,191 | 628 | ~461m edge, ~0.74 km² | Demand analysis, gap detection, archetypes |
| **Hex-9** | 7,318 | 603 | ~174m edge, ~0.11 km² | Place context, walkability, micrograph |
| **Places** | 174,711 | 114 | Individual business | Competition, synergy, survivability |

**Hex-8 is the primary analytical unit** — large enough for meaningful per-capita metrics, small enough for neighborhood-level variation. Hex-9 provides granularity. Subzone provides policy alignment.

**Hierarchy:** Every place carries its hex-9 and hex-8 ID. Every hex-9 has a hex-8 parent. Every hex maps to a subzone. Queries can traverse up and down.

---

## 4. Feature Pillars — Region Level (Hex-8: 628 features)

### 4.1 Demographics (18 features)
`population`, `population_total`, `population_nonresident`, `elderly_count`, `children_count`, `working_age_count`, `pct_elderly`, `pct_children`, `dependency_ratio`, `nonresident_share`, `daytime_intensity`, `hdb_pop_share`, `pop_density`, `pop_density_total`, `taps_per_capita_total`, `taps_per_capita_resident`, `places_per_1000_total`, `places_per_1000_resident`

**Key design:** All demand metrics use `population_total` (5.98M) not resident-only (4.21M). This makes industrial/CBD zones visible.

**Source:** SingStat 2025 subzone population by age/sex/floor-area, dasymetrically allocated to hexes using building footprints.

### 4.2 Dwelling Type Population (12 features)
`pop_tod_hdb_1__and_2_room_flats`, `pop_tod_hdb_3_room_flats`, `pop_tod_hdb_4_room_flats`, `pop_tod_hdb_5_room_and_executive_flats`, `pop_tod_condominiums_and_other_apartments`, `pop_tod_landed_properties`, `pop_tod_others`, `pop_<=60`, `pop_>60_to_80`, `pop_>80_to_100`, `pop_>100_to_120`, `pop_>120`

**Source:** SingStat 2025 population by type of dwelling and floor area.

### 4.3 Built Environment (16 features)
`bldg_count`, `bldg_density`, `hdb_blocks`, `bldg_commercial`, `bldg_residential`, `bldg_industrial`, `avg_floors`, `max_floors`, `total_floor_area_sqm`, `residential_floor_area_sqm`, `commercial_floor_area_sqm`, `avg_gpr`, `bldg_footprint_sqm`, `bldg_hdb_residential`, `bldg_private_residential`, `residential_floor_weight`

**Source:** Overture Maps 2026 building footprints (377,331), fused with OSM. HDB detection via classification.

### 4.4 Land Use (12 features)
`lu_residential_pct`, `lu_commercial_pct`, `lu_business_pct`, `lu_institutional_pct`, `lu_open_space_pct`, `lu_transport_pct`, `lu_mixed_use_pct`, `lu_entropy`, `lu_total_sqm`, `dominant_use`, `lu_fragmentation`, `ura_development_gap`

**Source:** URA Master Plan 2019 land use parcels (113,212), tessellated by area.

### 4.5 Transit Infrastructure (18 features)
`mrt_stations`, `lrt_stations`, `bus_stops`, `mrt_daily_taps`, `bus_daily_taps`, `transit_daily_taps`, `transit_mode_count`, `mrt_taps_am_peak`, `mrt_taps_pm_peak`, `mrt_taps_offpeak`, `mrt_taps_night`, `bus_taps_am_peak`, `bus_taps_pm_peak`, `transit_peak_ratio`, `dist_mrt_m`, `dist_bus_m`, `dist_nearest_mrt_m`, `mrt_hex_rings`

**Source:** LTA station register (Mar 2026), LTA ridership (Jan 2026 train, Dec 2025 bus), hourly tap volumes.

### 4.6 GTFS Frequency (8 features)
`gtfs_headway_am_min`, `gtfs_headway_pm_min`, `gtfs_headway_offpeak_min`, `gtfs_headway_night_min`, `gtfs_routes_served`, `gtfs_daily_departures`, `gtfs_stops_with_service`, `gtfs_frequency_score`

**Source:** Singapore GTFS 2026 (230,914 trips, 5,376 stops, 602 routes).

### 4.7 Walkability (26 features)
**Euclidean:** `walk_mrt_m`, `walk_bus_m`, `walk_hawker_m`, `walk_clinic_m`, `walk_park_m`, `walk_super_m`, `walk_school_m` + scores
**Network:** `nwalk_mrt_m`, `nwalk_bus_m`, `nwalk_hawker_m`, `nwalk_clinic_m`, `nwalk_park_m`, `nwalk_super_m` + scores + `nwalkability_composite`
**Detour:** `walk_detour_mrt`, `walk_detour_bus`, `walk_detour_hawker`, `walk_detour_clinic`, `walk_detour_park`, `walk_detour_super`
**Composite:** `walkability_score`, `walkability_composite`

**Source:** Amenity geojson files + OSM road network (213,978 nodes, 306,511 pedestrian edges).

### 4.8 Amenities (16 features)
`hawker_centres`, `supermarkets`, `clinics`, `parks`, `hotels`, `tourist_attractions`, `sfa_eating_count`, `sfa_eating_establishments`, `schools_primary`, `schools_secondary`, `preschools_gov`, `formal_schools`, `park_facilities`, `parks_nature`, `silver_zones`, `school_zones`

**Source:** LTA, SFA, MOE, URA, NEA geojson datasets.

### 4.9 Place Composition (79 features)
`pc_total`, `pc_density`, 24 category counts (`pc_cat_restaurant`, `pc_cat_shopping_retail`, etc.), 24 category percentages, `pc_cat_entropy`, `pc_cat_hhi`, 5 price tiers (`pc_tier_luxury` through `pc_tier_budget`), `pc_branded_count`, `pc_branded_pct`, `pc_unique_brands`, `pc_unique_place_types`, `pc_seg_entropy`, `pc_per_1000pop`

**Source:** sgp_places_v2.jsonl (174,711 places) assigned to hex via H3.

### 4.10 Demand Pull (12 features)
`pull_office`, `pull_residential`, `pull_transit`, `pull_hotel`, `pull_school`, `pull_hawker` + `_pctl` percentile ranks + `pull_total_pop`, `pull_total_pop_pctl`

**Formula:** `pull(h) = Σ_neighbors source_strength(n) × exp(-distance / λ)`
**Decay constants (hex-8):** office=600m, residential=800m, transit=500m, hotel=800m, school=800m, hawker=600m

### 4.11 Synergy Scores (20 features)
10 scores + 10 percentile ranks: `synergy_cafe_office`, `synergy_grocery_residential`, `synergy_conv_transit`, `synergy_rest_hotel`, `synergy_lifestyle`, `synergy_health`, `synergy_nightlife`, `synergy_education`, `synergy_financial`, `synergy_morning`

**Formula:** `synergy = category_count × relevant_pull`

### 4.12 Supply-Demand Saturation (13 features)
`saturation_restaurant`, `saturation_cafe`, `saturation_convenience`, `saturation_health`, `saturation_fnb` + corresponding `gap_*` + `supply_demand_gap_composite`, `fnb_total`

**Formula:** `saturation = actual / expected`, where `expected = population_total × benchmark_per_1000` (60th percentile of well-served hexes). Only computed for hexes with pop_total > 500.

### 4.13 Satellite Intelligence (12 features)
`nl_2022`, `nl_2024`, `nl_change_pct`, `nl_growth_corridor`, `nl_decline_zone`, `nl_per_capita`, `nl_commercial_indicator`, `worldpop_2020`, `worldpop_2025`, `wp_pop_growth_pct`, `wc_is_built`, `wc_is_tree`, `wc_is_water`, `wc_class`

**Source:** NASA VIIRS Black Marble (2022 + 2024), WorldPop 2020/2025, ESA WorldCover 2021.

### 4.14 Archetype & Composites (13 features)
`archetype` (6 types), `archetype_id`, `archetype_confidence`, `idx_vitality`, `idx_accessibility`, `idx_demand`, `idx_competition`, `idx_growth_potential`, `idx_redevelopment_pressure`, `idx_residential_quality`, `idx_urban_intensity`

**Method:** K-means (k=6) on 46 normalized features. Archetypes: Dense HDB, Mature HDB, Green/Institutional, Tourist/Commercial, Mixed.

### 4.15 Proxy Features (4 features)
`proxy_daytime_pop` (office×15 + retail×8 + F&B×5 + hotel×20 + school×25), `proxy_night_economy`, `proxy_tourism`, `proxy_footfall`

### 4.16 Influence & Structure (8 features, hex-8 only)
`interface_score`, `gradient_position`, `net_demand_flow`, `pop_concentration`, `place_clustering`, `pop_commercial_correlation`, `lu_fragmentation`, `ecosystem_completeness`, `self_containment`

### 4.17 Spatial Context (123 features)
Ring-1 and ring-2 neighbor aggregates: `sp_max_*` (31), `sp_pw_*` (30), `tr_max_*` (31), `tr_pw_*` (31) — maximum and population-weighted mean of population, elderly, buildings, places, categories, land use, micrograph means.

### 4.18 Micrograph (156 features)
12 categories × 13 features: `mg_{cat}_n`, `mg_{cat}_cv_transit`, `mg_{cat}_cv_competitor`, `mg_{cat}_cv_complementary`, `mg_{cat}_cv_demand`, `mg_{cat}_anchor_count`, `mg_{cat}_comp_pressure`, `mg_{cat}_demand_diversity`, `mg_{cat}_walkability`, `mg_{cat}_pct_hyperdense`, `mg_{cat}_pct_dense`, `mg_{cat}_pct_moderate`, `mg_{cat}_pct_sparse`

Categories: cafe, rest, hawk, fast, bake, bar, beau, heal, conv, educ, fitn, shop

### 4.19 Property (2 features)
`hdb_median_psf`, `hdb_txn_count`

**Source:** HDB resale transactions (227,207 records, 2025 subset), mapped by planning area.

### 4.20 Additional (6 features)
`osm_amenities`, `osm_leisure`, `osm_shops`, `osm_tourism`, `park_connector_segments`, `ev_charging_points`

---

## 5. Feature Pillars — Place Level (114 features)

### 5.1 Identity (14)
place_id, name, address, latitude, longitude, main_category (24 types), place_type, price_tier (luxury/premium/mid/value/budget), is_branded, brand_name, source, confidence, h3_res9, h3_res8

### 5.2 Competition (5)
competitors_200m, competitors_500m, nearest_competitor_m, market_share_proxy, substitution_risk

### 5.3 Complementary (5)
complementary_diversity (unique categories within 300m), total_places_300m, complementary_fnb_300m, complementary_retail_300m, complementary_score

### 5.4 Anchor Proximity (19)
9 anchor types × (count within radius + nearest distance) + anchor_score composite:
- MRT (300m), Bus (200m), Hawker (300m), Clinic (500m), Park (500m), Supermarket (300m), Hotel (300m), School (500m), Tourist (500m)
- Additional: Library (500m), Sports (500m), Worship (300m), Community (500m), University (500m)

### 5.5 Demand Pull (8)
pull_office, pull_residential, pull_transit, pull_hotel, pull_school, pull_hawker, pull_total_pop, demand_context_score

### 5.6 Synergy (10)
Target-category-only firing: synergy_cafe_office, synergy_grocery_residential, synergy_convenience_transit, synergy_restaurant_hotel, synergy_lifestyle, synergy_health_cluster, synergy_nightlife, synergy_education, synergy_financial, synergy_morning

### 5.7 Transit (8)
nwalk_mrt_m, nwalk_bus_m, nwalk_mrt_score, nwalk_bus_score, gtfs_headway_am_min, gtfs_routes_served, transit_daily_taps, transit_score

### 5.8 Catchment (5)
catchment_pop, catchment_elderly, catchment_nonresident, catchment_nonres_share, catchment_daytime

### 5.9 Building Context (8)
bld_bldg_count, bld_avg_floors, bld_max_floors, bld_hdb_blocks, bld_lu_residential, bld_lu_commercial, bld_lu_business, bld_lu_entropy

### 5.10 Neighborhood Character (8)
char_pop_density, char_pct_elderly, char_hdb_share, char_ecosystem, char_interface, char_gradient, char_hdb_psf, char_nonres_share + char_archetype, idx_vitality, idx_demand, idx_accessibility, idx_urban_intensity, idx_growth_potential, nl_radiance, nl_commercial

### 5.11 Supply-Demand Fit (5)
saturation_own_category, gap_own_category, demand_match, gap_fill_score, survivability_index

### 5.12 Composite (1)
context_score = 0.30×complementary + 0.30×anchor + 0.25×transit + 0.15×(1/(1+competitors))

---

## 6. Category Taxonomy (24 L1 categories)

| Category | Places | Description |
|---|---:|---|
| Shopping & Retail | 27,137 | Clothing, electronics, home, general retail |
| Restaurant | 20,914 | Full-service dining, all cuisines |
| Services | 16,919 | Laundry, repair, professional services |
| Business | 16,689 | Offices, workspaces, corporate |
| Beauty & Personal Care | 11,529 | Salons, spas, aesthetics |
| Education | 10,508 | Schools, tuition, enrichment |
| Health & Medical | 8,004 | Clinics, pharmacy, dental, TCM |
| Cafe & Coffee | 6,643 | Cafes, kopi shops, specialty coffee |
| Fitness & Recreation | 6,357 | Gyms, studios, sports |
| Convenience & Daily Needs | 6,019 | 7-Eleven, provision shops, minimarts |
| Hawker & Street Food | 5,960 | Hawker stalls, food courts, kopitiams |
| Automotive | 5,531 | Workshops, car dealers, petrol |
| Transport | 4,255 | Logistics, parking, vehicle rental |
| Bar & Nightlife | 3,370 | Bars, pubs, clubs, KTV |
| Civic & Government | 3,206 | Government offices, community clubs |
| Residential | 3,019 | Residential services, property agents |
| Fast Food & QSR | 2,941 | McDonald's, KFC, chain fast food |
| Office & Workspace | 2,876 | Co-working, serviced offices |
| Culture & Entertainment | 2,795 | Museums, cinemas, arcades |
| Hospitality | 2,432 | Hotels, hostels, serviced apartments |
| Bakery & Pastry | 2,373 | Bakeries, cake shops, confectionery |
| General | 2,036 | Unclassified commercial |
| Religious | 1,953 | Temples, mosques, churches |
| NGO | 1,060 | Charities, social organizations |

---

## 7. Embedding Space

### 7.1 Region embeddings (from hex_v10 pipeline)
- **Graph fingerprint (135d):** 88 region features + 47 graph statistics, percentile-normalized
- **Place2vec (64d):** Place composition vectors per hex, trained via Word2Vec analogy on category co-occurrence
- **GCN embeddings (64d):** Graph Convolutional Network on hex adjacency + features (R²=0.755 on gap prediction)

### 7.2 Place embeddings (planned, not yet built)
- 96 numeric features → PCA/autoencoder to 32-64d dense vector
- Enables: similarity search, clustering, anomaly detection, recommendation
- Planned as part of MoE corpus generation

### 7.3 Spatial indices
- **H3 hierarchy:** res-9 → res-8 → res-7 parent chain for multi-scale queries
- **KD-tree:** Built at runtime for spatial radius queries (competition, complementary, anchors)
- **DuckDB:** Column-oriented queries on parquet in <7ms

---

## 8. Data Sources (19)

| # | Source | Records | Role | Update |
|---|---|---|---|---|
| 1 | Overture Maps + OSM | 174,711 places | Commercial POIs | Quarterly |
| 2 | Overture Buildings | 377,331 | Built form, HDB detection | Quarterly |
| 3 | LTA Station Register | 231 (187 MRT + 44 LRT) | Transit network | As-built |
| 4 | LTA Bus Stops | 5,177 | Bus network | Monthly |
| 5 | LTA Ridership (train Jan 2026) | 7,259 hourly records | MRT demand | Monthly |
| 6 | LTA Ridership (bus Dec 2025) | 203,589 hourly records | Bus demand | Monthly |
| 7 | Singapore GTFS 2026 | 230,914 trips, 602 routes | Service frequency | Annual |
| 8 | OSM Road Network | 550,991 segments | Walk distances | Continuous |
| 9 | SingStat Population (FA) | 4,172,350 by subzone | Demographics | Annual |
| 10 | SingStat Population (TOD) | 4,212,800 by dwelling | Dwelling types | Annual |
| 11 | SingStat Dwellings | 326 subzones | Housing stock | Annual |
| 12 | HDB Resale Transactions | 227,207 | Property prices | Monthly |
| 13 | URA Master Plan | 113,212 parcels | Land use zoning | Periodic |
| 14 | NEA/SFA Eating Establishments | 34,366 licensed | F&B validation | Quarterly |
| 15 | NASA VIIRS Black Marble | 2 epochs (2022, 2024) | Nightlight commercial | Annual |
| 16 | WorldPop | 2 epochs (2020, 2025) | Population grid | Annual |
| 17 | ESA WorldCover | 2021 | Land cover | Multi-year |
| 18 | JRC GHSL | SMOD 2020 | Urbanization class | Multi-year |
| 19 | OSM POIs (4 layers) | 52,317 | Supplementary coverage | Continuous |

---

## 9. Gaps & Limitations

### Data not available
| Gap | Impact | Workaround |
|---|---|---|
| **Census income** | Can't segment by affluence at subzone level | HDB PSF as proxy ($520-$700/sqft range) |
| **Actual footfall** | No telco/mobility data | Transit taps + proxy_footfall composite |
| **Place ratings** (Google reviews) | Can't distinguish quality within category | Price tier as partial proxy |
| **Shelter / covered walkway** | Critical for tropical SGP, no dataset | Network walk is a floor estimate |
| **Hawker centre capacity** | Have count but not stall count / seating | Treat each as equivalent |
| **School quality / MOE ranking** | Have location but not band | Count only |
| **Real-time bus frequency** | GTFS is static schedule, not actual | GTFS is close enough for planning |
| **Floor-level use** (vertical) | Buildings counted flat, not by floor | avg_floors + building class is partial |

### Methodological limitations
| Limitation | Impact | Mitigation |
|---|---|---|
| Walk distances are network but not isochrone | Underestimates barriers (stairs, underpasses) | Use as lower bound |
| Population is subzone-level, dasymetrically allocated | Allocation noise at hex-9 | Hex-8 smooths this |
| Saturation uses relative benchmark (P60) | Benchmark is relative, not absolute | Sensitivity analysis |
| Demand pull is symmetric (no directionality) | People walk toward MRT not away | Transit pull partially corrects |
| Non-resident allocation is uniform within subzone | Workers cluster in specific hexes | Daytime intensity helps |
| GTFS MRT headways are synthetic (3-6 min) | Exact train timetable not public | Realistic assumption |
| 5,417 places outside hex grid | 3% of places at ocean/border edge | Acceptable for analytics |
| Archetype naming is heuristic | Labels may not match human intuition | Use metrics, not labels |

### Comparison to HKG (remaining gaps)
| Feature | HKG has | SGP has | Gap |
|---|---|---|---|
| Census income/ethnicity | 206 features | 18 features | Cannot close (data unavailable) |
| GHSL multi-epoch (2010/2020/2025) | 3 epochs, age proxy | SMOD only | Download blocked (wrong tile) |
| Nightlight temporal (37 months) | Monthly composites | 2 yearly snapshots | Could add more months |
| Terrain / DEM | Elevation, hillside, ruggedness | None | Not critical (SGP is flat) |
| Place anchor types | 16 types × 3 = 48 features | 14 types × 2 = 28 features | Minor |
| Place features total | 142 | 114 | Partially closed |

### SGP advantages over HKG
| Feature | SGP | HKG |
|---|---|---|
| GTFS frequency | 8 features | None |
| Network walk (OSM graph) | 6 amenities | Euclidean only |
| Supply-demand saturation | 10 features | None |
| Total pop (resident + non-resident) | Explicit split | WorldPop only |
| Micrograph (12 cat × 13) | 156 features | None at region |
| Spatial context (ring aggregates) | 123 features | ~20 |
| Price tier per place | 5 tiers | None |
| Substitution risk | Per place | None |
| HDB context | 3 features | N/A |
| Internal structure (cross-scale) | 5 features | None |

---

## 10. Aggregation Logic

### Hex-9 → Hex-8
| Feature type | Method | Example |
|---|---|---|
| Counts (people, places, buildings, taps, stops) | **SUM** | population, pc_total, transit_daily_taps |
| Rates / percentages / scores | **Population-weighted MEAN** | walkability, land use %, context vectors |
| Distances | **MIN** | walk_mrt_m (nearest matters) |
| Heights / maxima | **MAX** | max_floors |
| Demand pull | **NATIVE recompute** | Different decay constants for hex-8 scale |
| Internal structure | **CROSS-SCALE** | Uses hex-9 children as sub-samples |

All SUM columns verified at **0.00% difference** between hex-8 and hex-9 system totals.

---

## 11. Key Numbers

| Metric | Value |
|---|---|
| Total features across all levels | ~1,794 |
| Hex-8 features | 628 |
| Hex-9 features | 603 |
| Place features | 114 |
| Population (resident) | 4,212,320 |
| Population (total incl. non-resident) | 5,982,320 |
| Places assigned to hexes | 169,294 (of 174,711 — 5,417 at boundary) |
| MRT stations | 187 (+ 44 LRT) |
| Bus stops | 5,172 |
| Daily transit taps | 12,279,205 |
| Median network walk to MRT (hex-9) | 1,600m |
| Median network walk to bus (hex-9) | 537m |
| Median GTFS headway AM peak (hex-8) | 25.1 min |
| Hexes with GTFS service | 364/1,191 (hex-8), 1,219/7,318 (hex-9) |
| HDB median PSF range | $520-$700/sqft (by planning area) |
| Nightlight coverage | 97% of hexes |
| DuckDB query latency | <7ms |

---

## 12. Files

### On all servers (atlas-1, atlas-deploy, local)

| File | Path | Size | Shape |
|---|---|---|---|
| hex9_final.parquet | hex_v10/ | 8 MB | 7,318 × 603 |
| hex8_final.parquet | hex_v10/ | 3 MB | 1,191 × 628 |
| hex9_features.json | hex_v10/ | 126 MB | 7,318 × 602 |
| hex8_features.json | hex_v10/ | 22 MB | 1,191 × 627 |
| sgp_places_featured.parquet | places_consolidated/ | 50 MB | 174,711 × 114 |
| subzone_features_full.json | features/ | 4 MB | 326 × ~449 |
| singapore-gtfs.zip | gtfs/ | 336 MB | 230K trips |
| sgp_places_v2.jsonl | places_consolidated/ | 87 MB | 174,711 raw |
| sgp_buildings_fused.parquet | buildings_overture/ | 24 MB | 377,331 |
| roads.geojson | roads/ | 231 MB | 550,991 segments |

### Documentation

| File | Description |
|---|---|
| docs/SGP_DIGITAL_ATLAS_METHODOLOGY.md | Full methodology (this is the reference) |
| docs/SGP_DIGITAL_ATLAS_CONTEXT.md | This file (complete context) |
| docs/UNIFIED_PLACE_REPRESENTATION.md | Place pipeline design |
| docs/PLACE_REPRESENTATION_PLAN.md | Original place ideation |
| docs/LLM_MOE_SPATIAL_EXPERT_IDEATION.md | MoE training idea |
| transport_gaps_validated.html | Transport claim validation |
| transport_adequacy_app_ideation.html | App design doc |

---

## 13. Models & Analytics (built on this atlas)

| Model | What it does | Performance |
|---|---|---|
| **Gap model v7** | Predicts commercial adequacy per hex | R²=0.755 |
| **Population model v8** | Predicts residential density from commercial signals | R²=0.816 |
| **Micrograph pipeline** | Per-place context vectors (12 categories) | Production |
| **Archetype clustering** | K-means (k=6) on 46 features | 6 interpretable types |
| **Saturation model** | Expected vs actual places per category | Identifies 233 under-served hex-8 cells |
| **Survivability index** | demand_match × (1-saturation) × transit × gap_fill | Per-place ranking |
| **Place2vec** | Category co-occurrence embeddings | Validated analogies |
| **GCN (64d)** | Graph neural network on hex adjacency | Feature learning |

---

## 14. Applications

| App | Port | Description | Stack |
|---|---|---|---|
| **Hex Adequacy Explorer** | 16789 | H3 hex choropleth map | React + Mapbox GL |
| **SGP Atlas App** | 18067 | Subzone-level explorer | React + Deck.gl + D3 |
| **Scenario Sim** | 18070 | What-if analysis | Python + Mapbox |
| **Merlion** | 18700/18701 | NL query orchestrator | FastAPI + Next.js |
| **Atlas API** (planned) | 18080 | DuckDB-backed feature API | FastAPI + DuckDB |

---

## 15. What's Next

1. **Atlas API** — DuckDB-backed serving on atlas-deploy (all data ready, script written)
2. **LLM MoE corpus** — Convert 183K entities to "what am I / where am I" natural language
3. **Place embeddings** — PCA/autoencoder on 96 numeric place features → 32-64d vectors
4. **Transport adequacy gap report** — Segment-conditioned (seniors, commuters, tourists, school kids)
5. **Interactive app v2** — MapLibre + React on atlas-deploy, using hex-8 + places
6. **Cross-city benchmarking** — Compare SGP hexes against NYC/Chicago/LA via atlas datarepo
7. **GHSL multi-epoch** — Download correct tile (not R7_C29, need equatorial tile for SGP)
8. **More VIIRS months** — Download 24+ monthly composites for trend analysis

---

*Context document v2.0 — 2026-04-20*  
*Built over 5 sessions, validated against 19 raw sources, 13 sanity checks, cross-resolution consistency verified at 0.00% diff*
