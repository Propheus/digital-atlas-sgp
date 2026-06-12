# Plexis — Digital Atlas Build Methodology

**Version:** 1.0
**Date:** 2026-04-23
**Scope:** Generalized, portable methodology for building a digital atlas of any city or country, with repeatable tests to validate the build.

---

## 1. What Plexis is

**Plexis** is the end-to-end methodology, pipeline, and output schema for converting a city's raw public data into a **multi-resolution feature representation + typed relational knowledge graph** that supports site selection, gap analysis, similarity search, and simulation.

Plexis has three named artifacts:

| Name | What it is | Portable? |
|---|---|---|
| **Plexis** (umbrella) | The build methodology + stage sequence | Yes — any city/country |
| **Plexis-Graph** | The heterogeneous relational knowledge graph (nodes + 39 typed relations) | Yes — relations parameterized, some city-specific |
| **Plexis-Embed** | Optional GAT-R-GCN trained on Plexis-Graph → 256d embeddings | Yes — architecture is universal |

Everything else (V10 hex stack, Merlion, Scenario Sim) sits as a **consumer** of these three artifacts.

### 1.1 What Plexis is not

- Not a dataset — it is a methodology that produces datasets
- Not a model — Plexis-Embed is one model among several consumers
- Not tied to Singapore — SGP is reference implementation #1; HKG is #2
- Not tied to H3 — any tessellation works; H3 is the reference

### 1.2 Scope diagram

```
   Raw public data (14+ sources, ~5 GB typical)
                  │
                  ▼
   ┌──────────────────────────────────────┐
   │  Plexis build stages 0–17            │  Feature stack
   │  → hex9_final, hex8_final,           │  (multi-resolution)
   │    subzone_features, places_featured │
   └──────────────────┬───────────────────┘
                      │
            ┌─────────┴────────┐
            ▼                  ▼
   ┌────────────────┐   ┌────────────────┐
   │ Plexis-Graph   │   │ Feature tables │
   │ 1.5M edges     │   │ (direct ML)    │
   │ 39 relations   │   └────────────────┘
   └───────┬────────┘
           ▼
   ┌────────────────┐
   │ Plexis-Embed   │   (optional)
   │ 256d vectors   │
   └────────────────┘
```

---

## 2. Design principles

Seven principles, each forced by a past mistake.

### 2.1 Multi-resolution by design, not by aggregation
The atlas carries place, hex-9, hex-8, and subzone as **first-class representations**. Features that depend on neighborhood context (demand pull, saturation) are computed **natively at each resolution**, with different decay constants. Do not aggregate hex-9 pull up to hex-8 — re-derive it.

**Why:** hex-9 k=1 ring ≈ 370 m (walking scale). hex-8 k=1 ring ≈ 800 m (neighborhood scale). Same formula with same λ would blur one or over-decay the other.

### 2.2 No broadcast leakage
A feature whose value is constant within a coarser unit (e.g., "condo %" from subzone broadcast to every hex inside it) is **forbidden at hex level unless explicitly derived from hex-local data**. All broadcasts are flagged and excluded from downstream models.

**Why:** V10 caught VivoCity showing identical commercial features as Sentosa because both shared the parent subzone. Rebuild fixed this (check 4 in validation).

### 2.3 Population-total over resident-only for demand metrics
`population_total` (residents + non-residents + estimated daytime inflow) drives all demand-side metrics. Resident-only population is kept but not used for pull or saturation.

**Why:** CBD / industrial / tourist hexes show zero residents but thousands of daily users. Using resident-only makes them look "empty" in the demand model.

### 2.4 Target-category-only synergy at place level
At hex level, `synergy_cafe_office = cafe_count × pull_office` fires on all hexes. At place level, `synergy_cafe_office` fires **only on records whose main_category is Cafe & Coffee** — zero elsewhere.

**Why:** a bar record should not accrue cafe synergy credit; otherwise every place in the same hex looks identical.

### 2.5 Two-distance walkability
Every walkable amenity carries **both** a Euclidean distance (`walk_*_m`) and a network distance on the OSM pedestrian graph (`nwalk_*_m`). Expressways, canals, gated estates create big gaps between the two.

**Why:** Euclidean alone overstates access. Network alone hides the availability of the direct path.

### 2.6 Validate at totals, ranges, coherence, landmarks, and models
Build validation in five layers. A feature is shipped only when it passes all five. See §11.

### 2.7 Graph is primary, embedding is optional
Build Plexis-Graph even if you never train an embedding. All downstream use cases have a graph-only fallback.

**Why:** graph supports path queries and relation-typed neighborhood search that dense vectors cannot, and graph-only queries are auditable and explainable.

---

## 3. Spatial hierarchy (portable)

Plexis uses a **4-tier spatial hierarchy**. Tiers 2–4 are H3 hexagons; tier 1 is the local planning unit.

| Tier | Unit | Area (typical) | Typical count | Primary use |
|---|---|---|---|---|
| 1 | Planning unit (subzone / census tract / arrondissement / ward) | 1–10 km² | 100–1,000 | Policy, reporting |
| 2 | Hex-8 | 0.74 km² (461 m edge) | 500–5,000 | Neighborhood analytics, demand pull, saturation |
| 3 | Hex-9 | 0.11 km² (174 m edge) | 3,000–30,000 | Place context, micrograph, walkability |
| 4 | Place | point | 50,000–500,000 | Business-level ranking |

### 3.1 How to pick resolution for a new city

```
city_area_km²     hex-9 count    hex-8 count    recommended tier-1
  200 – 1,500    1K – 15K       0.2K – 2.5K    official planning unit
  1,500 – 10K    15K – 100K     2.5K – 17K     official unit; consider hex-7
  10K+           100K+          17K+           hex-7 as tier-1; skip admin
```

For country-wide builds, drop to hex-7 (2.57 km² per cell) as the top tier.

### 3.2 Tier-1 source ladder (in preference order)

1. **Official planning unit with polygons** (URA subzones, NYC census tracts, US planning areas) — best
2. **Official administrative boundary** (ward, arrondissement, barrio)
3. **OSM admin_level=8/9/10** — fallback when no official data
4. **Computed Voronoi** on population-weighted centroids — last resort

### 3.3 Mandatory spatial conventions

- **Coordinate system:** EPSG:4326 at ingest. Reproject to local metric CRS (e.g., EPSG:3414 for SGP, EPSG:2263 for NYC) for distance calculations, then project results back to EPSG:4326 for serving.
- **H3 indexing:** store as string hex at `h3.latlng_to_cell(lat, lng, res)`.
- **Tier containment:** every place has `h3_res9`, `h3_res8`, `parent_subzone`, `parent_planning_area` as fixed columns.

---

## 4. Portable input-data contract

### 4.1 Mandatory inputs (7)

A Plexis build is not possible without these. Substitutes exist per country.

| # | Input | What it provides | SGP source | NYC source | Generic source |
|---|---|---|---|---|---|
| 1 | **City boundary** | Scope of build | URA master plan | NYC boro boundaries | OSM `admin_level=4/5` |
| 2 | **Planning units with polygons** | Tier-1 | URA subzones (332) | Census tracts (2,168) | OSM admin + TIGER |
| 3 | **Points of interest** | Places layer | Overture + OSM + SFA | Overture + OSM | Overture (global), OSM Nominatim |
| 4 | **Buildings with footprints** | Built environment | Overture + HDB + OSM | Overture + PLUTO | Overture Buildings (global) |
| 5 | **Population by age** | Demographics | SingStat | ACS 5-year | UN WorldPop + local census |
| 6 | **Transit stops & lines** | Transit | LTA + GTFS | MTA GTFS | OSM public_transport + agency GTFS |
| 7 | **Road network** | Walkability | OSM | OSM | OSM |

### 4.2 Optional but high-leverage inputs

| Input | What it unlocks | Availability |
|---|---|---|
| Zoning / land use parcels | Land-use entropy, `lu_fragmentation`, `dominant_use` | Most large cities (URA, NYC PLUTO, LA zoning) |
| HDB / social housing polygons | Housing-type pop split, VOID_DECK_OF relation | City-specific |
| Transit ridership (daily taps) | `pull_transit`, peak splits | LTA, MTA (partial), TfL, Tokyo Metro |
| Property transactions | `hdb_median_psf`, market signal | HDB resale, Zillow, Rightmove, PropertyGuru |
| F&B licensing | Ground-truth validation | NEA/SFA, NYC DOH, Chicago Open Data |
| Satellite night lights | `nl_radiance`, temporal change | VIIRS (global, free) |
| Population density raster | Dasymetric allocation validator | WorldPop (global, free) |
| Personas / psychographics | Audience segmentation | NVIDIA personas (global synthetic), Experian |
| Review text (Google Places / OSM) | Quality, price, vibe, dietary | Google Places API, Overture |

### 4.3 City-specific substitutes

When a mandatory input is missing, Plexis has documented fallbacks:

| Missing | Fallback | Trade-off |
|---|---|---|
| Planning-unit polygons | Compute Voronoi on pop-weighted centroids | No policy alignment |
| Transit ridership | GTFS frequency only | Lose peak/off-peak, magnitude |
| Building footprints | Overture global (lower density outside top cities) | Lower count fidelity |
| Land use | OSM `landuse=*` tags | Entropy is noisier, ~60% coverage |
| Floor count | Derive from building height (3.5 m/floor rule) | Introduces 10–15% MAE |
| HDB / housing type | Dwelling counts by tract + nearest-neighbor | Lose VOID_DECK_OF relation |

---

## 5. Build stages (0–17) — the feature stack

Each stage has: **inputs · outputs · derived metrics · formulas · runtime · dependencies**.

Full tabular catalog in §7. The list below is the pipeline order.

### Stage 0 — Universe definition
**In:** city boundary, planning-unit polygons
**Out:** `hex_universe.parquet` (hex_id, h3_res, parent_subzone, parent_planning_area, area_km², water_share, land_share)
**Derived:** H3 cells at res-8 and res-9 covering the city; filter out pure-water cells (water_share > 0.95)
**Formula:** `H3.polyfill(city_boundary, resolution)` ∪ `H3.polyfill(each subzone, resolution)`
**Runtime:** < 1 min

### Stage 1 — Places consolidation
**In:** Overture places, OSM amenities + shops + leisure + tourism, government F&B licensing, brand taxonomy
**Out:** `places_master.jsonl` with canonical schema (id, name, lat, lng, address, raw_category, brand, confidence)
**Derived:**
- Dedupe by geohash-8 + name Jaro-Winkler > 0.85
- LLM classify to 24-category taxonomy (unclassified ≤ 1% target)
- Brand linking against global + local taxonomy
**Formula:** `dedupe → cluster (dbscan on coords, eps=30m) → name-merge → llm_classify → brand_link`
**Runtime:** 15–30 min (LLM calls dominate)

### Stage 2 — Buildings fusion
**In:** Overture buildings, OSM buildings, city-specific housing (HDB, PLUTO, cadastre)
**Out:** `buildings_fused.parquet` (polygon, height_m, floor_count, class_residential, class_commercial, is_hdb, subzone)
**Derived:**
- Height → floor_count via 3.5 m/floor (if floors missing)
- Class inference: `class = residential|commercial|industrial|institutional|mixed`
- HDB detection: polygon intersection with authoritative dataset if available, else name/class regex
**Runtime:** 3–5 min

### Stage 3 — Population dasymetric allocation
**In:** planning-unit population (by age, sex, dwelling type), buildings_fused
**Out:** `hex_population.parquet` (hex_id, pop_total, pop_resident, pop_nonresident, pop_0_14, pop_15_64, pop_65p, pop_by_dwelling_type[12])
**Derived:** allocate subzone pop proportional to (residential_floor_area × occupancy_factor) per hex child of the subzone
**Formula:**
```
pop_hex_i = subzone_pop × (resi_floor_area_hex_i / Σ resi_floor_area_subzone)
pop_nonresident_hex = subzone_nonres × daytime_intensity_hex
pop_total = pop_resident + pop_nonresident
```
**Conservation check:** Σ pop_hex == planning-unit pop (tolerance 0.02%).
**Runtime:** 2 min

### Stage 4 — Land use
**In:** zoning parcels (URA, PLUTO, OSM landuse)
**Out:** `hex_land_use.parquet` (12 land-use shares, `lu_entropy`, `dominant_use`, `lu_fragmentation`)
**Derived:**
- `lu_entropy = -Σ p_i × ln(p_i)` over 12 uses
- `lu_fragmentation` = count of distinct dominant_use across hex-9 children within a hex-8
**Runtime:** 3 min

### Stage 5 — Transit
**In:** stations GeoJSON, GTFS feed, ridership (optional)
**Out:** `hex_transit.parquet` (mrt_stations, bus_stops, lrt_stations, daily_taps, peak_taps_am, peak_taps_pm, off_peak_taps, night_taps, gtfs_headway_am_min, gtfs_routes_served, gtfs_daily_departures)
**Derived:**
- Headway = (window_hours × 60) / daily_arrivals at nearest stop
- Peak ratio = peak_taps_am / off_peak_taps
**Runtime:** 4 min

### Stage 5b — Satellite layer (optional, multi-source)

**In:** VIIRS annual night-lights, GHSL built-up series, WorldPop density raster, ESA WorldCover 10m
**Out:** 16 hex-level features grouped into 4 sub-layers:

| Sub-layer | Cols | Derivation |
|---|---|---|
| VIIRS night lights | `nl_radiance`, `nl_2022`, `nl_2024`, `nl_change_pct`, `nl_commercial_indicator` | zonal mean of raster per hex; year-over-year delta |
| GHSL built-up change | `ghsl_built_change`, `ghsl_built_growth_pct`, `ghsl_is_new_dev`, `ghsl_est_floors`, `ghsl_is_highrise`, `ghsl_height` | GHSL_BUILT_H + _C time series; new-dev flag = growth > P90 |
| WorldPop | `wp_pop_growth_pct` | WorldPop year-over-year density delta |
| WorldCover | `wc_tree_cover_pct`, `wc_cropland_pct`, `wc_water_pct`, `wc_urban_pct` | ESA WorldCover 10m class shares |

**Why:** night-light temporal change is the single most valuable satellite signal for detecting emerging commercial districts; GHSL captures vertical growth (new high-rises) that 2D data misses; WorldCover ground-truths greenery against zoning claims.
**Tunable:** safely skipped if rasters aren't available — atlas still works via built environment, land use, and place composition. The `ura_development_gap` features in Stage 14b provide a satellite-free substitute for "plan vs reality" detection.
**Runtime:** 3–5 min (zonal stats dominate)

### Stage 6 — Road network + walk graph
**In:** OSM roads, pedestrian-accessible filter
**Out:** `pedestrian_graph.pkl` (NetworkX, ~200K nodes, ~300K edges typical)
**Derived:** filter out motorways, trunks, and anything tagged `foot=no`. Add connectors for zebra crossings, pedestrian bridges, park paths.
**Runtime:** 5 min (one-time)

### Stage 7 — Place composition (at hex)
**In:** places_master, hex_universe
**Out:** `hex_place_composition.parquet` (24 category counts, 24 category shares, brand_count, branded_share, price_tier_mix, `pc_total`, `pc_entropy`, `pc_hhi`)
**Derived:**
- Entropy over 24 categories
- HHI = Σ share_i² (market concentration)
**Runtime:** 1 min

### Stage 8 — Amenity anchors
**In:** amenity point sets (MRT, bus, hawker, clinic, park, supermarket, hotel, school, tourist, library, sports, worship, community, university)
**Out:** `hex_amenities.parquet` with count + distance for each anchor type
**Derived:** `anchor_score = Σ w_i × exp(-dist_i / 1000)` across anchor types, weighted by importance
**Runtime:** 3 min

### Stage 9 — Demand pull (NATIVE per resolution)
**In:** population_total, place_composition, transit
**Out:** `hex_demand_pull.parquet` — 6 pulls: `pull_office`, `pull_residential`, `pull_transit`, `pull_hotel`, `pull_school`, `pull_hawker` (+ `_pctl` percentiles)
**Formula:**
```
pull_X(h) = Σ over neighbors n in k-ring(h, 2):
            source_strength_X(n) × exp(-distance(h, n) / λ_X)
```
**Decay constants (do not reuse across resolutions):**

| Pull | λ at hex-9 | λ at hex-8 |
|---|---|---|
| pull_office | 400 m | 600 m |
| pull_residential | 500 m | 800 m |
| pull_transit | 400 m | 500 m |
| pull_hotel | 500 m | 800 m |
| pull_school | 500 m | 800 m |
| pull_hawker | 400 m | 600 m |

**Runtime:** 4 min (ring expansion dominates)

### Stage 10 — Synergy (at hex, fires on all)
**Out:** 10 synergy scores: `synergy_cafe_office`, `synergy_grocery_residential`, `synergy_conv_transit`, `synergy_rest_hotel`, `synergy_lifestyle`, `synergy_health`, `synergy_nightlife`, `synergy_education`, `synergy_financial`, `synergy_morning`
**Formula:** `synergy_cat_pull = cat_count × pull_X(h)` at hex level
**Runtime:** < 1 min

### Stage 11 — Supply-demand saturation
**Out:** `saturation_{cat}`, `gap_{cat}` for 5 categories (restaurant, cafe, convenience, health, fnb_total)
**Formula:**
```
benchmark_per_1000 = P60(actual_density among hexes with pop_total > 500)
expected = pop_total × benchmark_per_1000 / 1000
saturation = actual / expected
gap       = expected - actual
```
**Filter:** only compute where `pop_total > 500` (prevents infinite saturation in empty industrial hexes).
**Runtime:** 1 min

### Stage 12 — Spatial context rings
**Out:** 123 ring-aggregate features — `sp_max_*`, `sp_pw_*` (pop-weighted) for ring-1 and ring-2 neighbors on key metrics
**Formula:**
```
sp_pw_X(h) = Σ (X(n) × pop(n)) / Σ pop(n)  for n in k-ring(h, r)
sp_max_X(h) = max X(n)                      for n in k-ring(h, r)
```
**Runtime:** 3 min

### Stage 13 — Micrograph features
**In:** per-category filtered place set (cafe, restaurant, convenience, health, etc.)
**Out:** 156 features = 12 categories × 13 features (transit_context, competitor_pressure, complementary_context, demand_context, anchor_count, competition_pressure, density_band_hyperdense, density_band_dense, density_band_moderate, density_band_sparse, walkability, etc.)
**Derived:** anchor-style embedding of each hex from the perspective of each category; see `micrograph_pipeline/` for V3 spec
**Runtime:** 8–12 min

### Stage 14 — Influence features (no broadcast leakage)
**Out:** `interface_score`, `gradient_position`, `net_demand_flow`, `ecosystem_completeness`, `self_containment`, `lu_fragmentation`
**Formula:**
```
interface_score  = lu_transition_count / lu_count_total  (edge mixing)
gradient_position = (self_metric - ring1_mean) / ring1_std
net_demand_flow = (pull_residential - pull_office) / (pull_residential + pull_office + ε)
ecosystem_completeness = fraction of 7 daily-needs categories present
self_containment       = fraction of 4 key amenities present (hawker, supermarket, clinic, park)
lu_fragmentation       = count of distinct dominant_use across hex-9 children in one hex-8
```
**Runtime:** 2 min

### Stage 14b — Development gap (plan vs built, satellite-free)
**In:** URA/zoning parcels, `buildings_fused`
**Out:** 4 features — `ura_development_gap`, `gap_residential`, `gap_commercial`, `gap_industrial`
**Formula:**
```
ura_development_gap = (lu_res + lu_com + lu_bus + lu_inst) − total_footprint_ratio
gap_residential     = lu_residential_pct − residential_footprint_ratio
gap_commercial      = (lu_commercial + lu_mixed_use) − commercial_footprint_ratio
gap_industrial      = lu_business_pct − industrial_footprint_ratio
```
**Why:** captures plan-vs-reality mismatch without any satellite rasters. CBD shows +commercial gap, HDB heartlands show +residential gap, industrial belt shows +industrial gap. Validated against k=6 archetypes.
**Runtime:** < 1 min

### Stage 14c — Dynamic LTA layer (optional, live features)
**In:** LTA DataMall endpoints (taxi availability, carpark, traffic speed bands, jam factor)
**Out:** 18 features — `dyn_taxi_count`, `dyn_taxi_density`, `dyn_carpark_available`, `dyn_carpark_count`, `dyn_carpark_per_1000pop`, `dyn_avg_speed`, `dyn_pct_jammed`, `dyn_traffic_segs`, `dyn_car_dependency`, `hex_avg_speed_kmh`, `hex_jam_pct`, `hex_jam_segments`, `hex_flow_pct`, `hex_flow_segments`, `hex_seg_count`, `carpark_count`, `carpark_lots`, `taps_per_capita_total`, `taps_per_capita_resident`
**Why:** distinguishes structural features from time-varying load. The "static" part of the atlas does not change day-to-day; the dynamic pillar is refreshed as often as the live feeds allow.
**For other cities:** replace LTA DataMall with the local live-transit + traffic API (NYC MTA + NYC DOT, TfL, Tokyo Metro OpenData, etc.). Skip entirely if no live data source is available; the atlas still works.
**Runtime:** 2 min per refresh

### Stage 15 — Merge + normalize
**Out:** `hex_features_v10.parquet`, `hex_features_v10_normalized.parquet`
**Derived:** sqrt-rule: `x' = sqrt(x)` for count features; z-score for rates; clip to [-5, 5] after z-score
**Runtime:** 1 min

### Stage 16 — Hex-9 → Hex-8 aggregation
**Rule table:**

| Feature type | Method | Examples |
|---|---|---|
| Counts | SUM | population, places, buildings, taps, stations |
| Rates / pct | Population-weighted mean | walkability, land-use shares, context vectors |
| Distances | MIN | walk_mrt_m |
| Heights | MAX | max_floors |
| Demand pull | NATIVE recompute | different λ |
| Internal structure | CROSS-SCALE | pop_concentration Gini across hex-9 children |

Also emit hex-8-only features: `pop_concentration`, `place_clustering`, `pop_commercial_correlation`, `lu_fragmentation`, `ecosystem_completeness`, `self_containment`.

**Check:** all SUM columns must match hex-9 total to 0.00%.
**Runtime:** 1 min

### Stage 17 — Place enrichment
**In:** places_master, hex_features_v10, pedestrian_graph
**Out:** `places_featured.parquet` — 114 features per place
**Derived (11 pillars, 114 features):**

| Pillar | Count | Notes |
|---|---|---|
| Identity | 14 | name, coords, category, price_tier, brand flags |
| Competition | 5 | KD-tree; same-category 200m/500m |
| Complementary | 5 | Cross-category diversity 300m (batched ball-tree) |
| Anchor proximity | 19 | 9 anchor types × count+dist + composite |
| Demand pull | 8 | Broadcast from host hex |
| **Synergy (target-only)** | 10 | Fires **only** on target category |
| Transit | 8 | Network walk + GTFS headway |
| Catchment | 5 | From hex |
| Building | 8 | From hex |
| Neighborhood character | 8 | From parent hex-8 |
| Supply-demand fit | 5 | saturation_own_category, demand_match, gap_fill, survivability |
| Composite | 1 | context_score |

**Runtime:** 3–5 min
**Total build wall-clock (Stage 0–17):** ~60 minutes on 16-core 62 GB machine.

---

## 6. Stage 18 — Plexis-Graph (the relational knowledge graph)

The primary intelligence artifact. Built on top of the feature stack.

### 6.1 Nodes (4 types)

| Node type | Count (SGP) | Attributes |
|---|---|---|
| `place` | 174,711 | id, name, lat, lng, category, brand, price_tier |
| `hex9` | 7,318 | id, pop_total, features 603d |
| `hex8` | 1,191 | id, pop_total, features 628d |
| `category` / `archetype` / `brand` | ~280 | id, label |

### 6.2 Edges — 39 typed relations

Each relation has: head type → tail type · derivation formula · optional edge attributes. Edges are **directed** unless marked symmetric (sym).

#### 6.2.1 Structural (universal — any city)

| Relation | Head→Tail | Derivation | Count (SGP) |
|---|---|---|---|
| `LOCATED_IN` | place → hex9 | spatial containment | 174,711 |
| `PARENT_OF` / `PART_OF` | hex8 → hex9 (and reverse) | H3 parent/child | 7,318 × 2 |
| `IS_A` | place → category | place.category | 174,711 |
| `ADJACENT_TO` | hex9 → hex9 (sym) | H3 k-ring 1 | 24,174 |
| `SERVES` | hex → place (via amenity) | anchor-type proximity | 6,788 |

#### 6.2.2 Commercial (universal — any city)

| Relation | Head→Tail | Derivation | Count |
|---|---|---|---|
| `COMPETES_WITH` | place → place | same main_category AND within 500 m AND same price_tier | 503,310 |
| `SYNERGIZES_WITH` | place → place | different categories in documented co-location pair (cafe↔office, conv↔transit) within 300 m | 262,781 |
| `SUBSTITUTES_FOR` | place → place | substitution-map match (cafe↔bakery↔kopitiam) within 200 m | 150,300 |
| `ANCHORED_BY` | place → anchor-place | demand-generator within category-specific radius (MRT@300m, hawker@300m, hotel@300m) | 107,622 |

#### 6.2.3 Spatial context (universal)

| Relation | Head→Tail | Derivation | Count |
|---|---|---|---|
| `WALK_CATCHMENT` | hex → hex | nwalk ≤ 800 m | 6,643 |
| `SAME_CLUSTER` | place → place | DBSCAN on coords, eps=200m, shared cluster | 5,334 |
| `SAME_CORRIDOR` | hex → hex | along same primary road/transit corridor | 1,891 |
| `COMMERCIAL_GRADIENT` | hex → hex | Δ(place_density) crossing boundary; head = higher | 4,205 |
| `HEIGHT_GRADIENT` | hex → hex | Δ(max_floors) ≥ 10 crossing boundary | 2,494 |
| `DENSITY_GRADIENT` | hex → hex | Δ(pop_total) ≥ 2× crossing boundary | 2,127 |
| `PRICE_GRADIENT` | hex → hex | Δ(hdb_median_psf) ≥ 15% crossing boundary | 437 |
| `LU_TRANSITION` | hex → hex | dominant_use change across hex-9 edge | 904 |
| `EXIT_FRONTAGE` | place → mrt_exit | within 50 m of a rail exit point | 3,051 |
| `DEVELOPMENT_FRONT` | hex → hex | new construction inferred from satellite delta | 3,001 |
| `CONNECTS_TO` | hex → hex | shared pedestrian-graph component | 2,279 |
| `ROAD_CONNECTED` | hex → hex | shared primary road segment | 1,013 |

#### 6.2.4 Directional (universal)

| Relation | Derivation |
|---|---|
| `NORTH_OF` / `SOUTH_OF` / `EAST_OF` / `WEST_OF` | centroid azimuth ± 22.5° sector, only emit for same SAME_CLUSTER or COMPARABLE_TO peer |

#### 6.2.5 Transport (universal where GTFS exists)

| Relation | Derivation |
|---|---|
| `FEEDS_INTO` | bus_stop → rail_station (within same trip chain from OD matrix) |
| `EXPRESSWAY_CORRIDOR` / `EXPRESSWAY_CONNECTED` | hex → hex along labeled expressway |
| `BUS_CORRIDOR` | hex → hex sharing ≥ 3 bus routes |

#### 6.2.6 Supply/demand (universal)

| Relation | Derivation |
|---|---|
| `UNDERSUPPLIED` | hex → category where gap_cat > P75 |
| `OVERSUPPLIED` | hex → category where saturation_cat > P75 |
| `WORKER_INFLOW` | hex → hex where net_demand_flow shows office-inflow |
| `DEMAND_LEAKS_TO` | hex → hex where residents WALK_CATCHMENT to oversupplied neighbor |

#### 6.2.7 Comparable (universal)

| Relation | Derivation |
|---|---|
| `COMPARABLE_TO` | hex → hex in top-K cosine on 32-dim PCA (K=5) |
| `SYNERGY_PAIR` | category → category, from synergy matrix |
| `SUBSTITUTES` | category → category, from substitution matrix |

#### 6.2.8 City-specific (localize or drop)

| Relation | SGP count | Meaning | For other cities |
|---|---|---|---|
| `VOID_DECK_OF` | 21,690 | HDB ground-floor commercial | Replace with `GROUND_FLOOR_OF` for public housing; drop if no social housing |
| `COASTAL` | 83 | hex intersects coastline | Keep globally; zero for landlocked cities |

### 6.3 Edge attributes

Twelve optional attributes carried on edges where meaningful: `type`, `ring`, `distance_m`, `anchor_type`, `gap`, `saturation`, `category`, `archetype`, `roads`, `change`, `from`, `to`. Allow null for relations where not applicable.

### 6.4 Graph output

```
plexis_triplets.parquet    # (head, relation, tail, 12 attrs)  — ~100 MB typical
plexis_graph_summary.json  # relation counts, node counts, density
```

Graph is queryable directly via pandas/DuckDB for path queries, without any embedding.

---

## 7. Stage 19 — Plexis-Embed (optional)

### 7.1 Why it's optional

Plexis-Graph supports all core use cases (site selection, gap analysis, comparable market, 15-minute city) via graph traversal and feature-table joins. Plexis-Embed adds dense-vector similarity, category classification, and cold-start node scoring. Train it when:

- Dataset stabilizes (features don't change daily)
- Dense similarity is needed in a user-facing product
- ML-downstream consumer (e.g., a recommender, a classifier)

### 7.2 Production spec (v6)

```
Architecture: GAT-R-GCN
  Layers:         4
  Attention:      4-head, per layer
  Hidden dim:     192
  Heads:          2 × 128d (spatial head + commercial head)
  Output:         256d per node
  Parameters:     364,711

Input:
  Feature init:   64d PCA (32d place + 32d hex)  — raw, no log/box-cox
  Graph:          1,485,547 edges × 39 relations
  Nodes:          195,756

Training:
  Epochs:         200 (early stop patience=30)
  LR:             1e-3 → 1e-5 cosine
  Loss:           0.10 link + 0.15 contrastive + 0.35 category + 0.40 regression
  Regression targets: 15 features (walkability, pull_residential, anchor_score, …)
  Classification target: main_category (24 classes)
```

### 7.3 Output

```
plexis_v6_embeddings.npz
  place_ids      (n_place,)
  place_embeds   (n_place, 256)
  place_spatial  (n_place, 128)
  place_commercial (n_place, 128)
  hex9_ids       (n_hex9,)
  hex9_embeds    (n_hex9, 256)
  hex8_ids       (n_hex8,)
  hex8_embeds    (n_hex8, 256)
```

### 7.4 Quality targets (must pass before accepting a new version)

| Metric | Threshold | Meaning |
|---|---|---|
| Category accuracy | ≥ 70% | Classifier head over 24 cats |
| Walkability R² | ≥ 0.85 | Hex regression target |
| pull_residential R² | ≥ 0.85 (hex), ≥ 0.90 (place) | Regression target |
| Anchor R² (place) | ≥ 0.85 | Regression target |
| P@5 similarity | ≥ 0.08 | Top-5 neighbor precision |
| Hits@10 link pred | ≥ 7% | Held-out edge recovery |

---

## 8. Feature catalog (summary)

Column-level dictionary: `docs/FEATURE_CATALOG.md` (authoritative, reconciled against live parquets on atlas-1, 2026-04-23). Totals below reflect actual on-disk schemas.

| Level | Record count (SGP) | Feature count |
|---|---|---|
| Place | 174,711 | **114** (across 11 pillars) |
| Hex-9 | 7,318 | **613** |
| Hex-8 | 1,191 | **638** |
| Subzone | 332 | 243 (V8) |

### Pillars at hex-8 (638 cols)

| # | Pillar | Cols | Portable? | Notes |
|---|---|---|---|---|
| 1 | Identity | 6 | ✓ | hex_id, h3_res8, parent_*, centroid_* |
| 2 | Demographics | 14 | ✓ | population, pct_elderly, pct_children, pct_nonresident, daytime_intensity, dependency_ratio |
| 3 | Buildings | 18 | ✓ | bldg_count, avg_floors, max_floors, floor_area, HDB blocks, commercial_floor_area |
| 4 | Land use | 14 | ✓ | 9 zoning shares, avg_gpr, lu_entropy, dominant_use, lu_fragmentation |
| 5 | Transit | 18 | ✓ | MRT/LRT/bus counts, daily taps, peak splits, taps_per_capita |
| 6 | GTFS | 8 | if GTFS available | headways (AM/PM/off/night), routes, departures, frequency score |
| 7 | Walkability — Euclidean | 14 | ✓ | `walk_*_score` from straight-line distances |
| 8 | Walkability — Network | 12 | ✓ (needs walk graph) | `nwalk_*_score` from OSM pedestrian graph |
| 9 | Place composition | 79 | ✓ | 24 cat counts + shares, 5 price tiers, brands, HHI, entropy |
| 10 | Distance-to-amenity (Euclidean) | 8 | ✓ | `dist_bus_m`, `dist_mrt_m`, `dist_hawker_m`, `dist_clinic_m`, `dist_park_m`, `dist_school_m`, `dist_super_m` |
| 11 | Demand pull | 14 | ✓ | 6 pulls × 2 (raw + pctl) + 2 totals (total_pop, daytime) |
| 12 | Synergy | 23 | ✓ | 10 core synergies + sub-variants |
| 13 | Micrograph | 156 | ✓ | 12 categories × 13 context features |
| 14 | Saturation | 13 | ✓ | 5 `saturation_*` + 5 `gap_*` + composites |
| 15 | Spatial rings (max) | 61 | ✓ | `sp_max_*` over ring-1/2 |
| 16 | Spatial rings (transit) | 62 | if transit | `tr_*` via MRT graph |
| 17 | Composites | 8 | ✓ | `idx_vitality`, `idx_accessibility`, `idx_demand`, `idx_growth_potential`, `idx_urban_intensity` … |
| 18 | Proxies | 4 | ✓ | `proxy_daytime_pop`, `proxy_footfall`, `proxy_tourism`, `proxy_night_economy` |
| 19 | Influence (no-leakage) | 6 | ✓ | `interface_score`, `gradient_position`, `net_demand_flow`, `ecosystem_completeness`, `self_containment`, `lu_fragmentation` |
| 20 | Archetype | 3 | ✓ (post-clustering) | `archetype`, `archetype_id`, `archetype_confidence` |
| 21 | Amenities (counts) | 9 | ✓ | hawkers, clinics, preschools, hotels, attractions, parks, supermarkets, schools, libraries |
| 22 | Roads & signals | 15 | ✓ | road category counts, `sig_*` traffic signals, `ped_*` pedestrian crossings |
| 23 | Satellite | 16 | if rasters | VIIRS nightlights (3–4) + **GHSL built-up change (6)** + WorldPop (1) + WorldCover (4–6) |
| 24 | Property | 2 | if txn data | `hdb_median_psf`, `hdb_txn_count` (flagged as broadcast-from-PA) |
| 25 | OSM POI | 4 | ✓ | amenities, leisure, shops, tourism |
| 26 | **Development gap (plan vs built)** | 1–4 | ✓ if zoning + buildings | `ura_development_gap`, `gap_residential`, `gap_commercial`, `gap_industrial` — captures satellite-free dev mismatch |
| 27 | **Dynamic LTA (live)** | 18 | if live API | `dyn_taxi_*`, `dyn_carpark_*`, `dyn_avg_speed`, `dyn_pct_jammed`, `dyn_car_dependency`, `hex_jam_pct`, `hex_flow_pct`, `carpark_lots`, `taps_per_capita_*` |
| 28 | Infra misc | 3 | ✓ | `park_connector`, `fnb_*`, `pcn_*` |

### Pillars at hex-9 (613 cols)

Same pillar list, except:
- Composites (8), Proxies (4), Archetype (3) are computed only at hex-8 (not present at hex-9)
- Satellite pillar is slightly larger at hex-9 (23 cols — finer granularity on GHSL + WorldCover)
- Influence is 3 cols at hex-9 (vs 6 at hex-8 — cross-scale features are hex-8 only)

### Pillars at place (114 cols)

| Pillar | Cols | Notes |
|---|---|---|
| Identity | 14 | name, coords, category, price_tier, brand flags, confidence |
| Competition | 5 | `competitors_200m`, `competitors_500m`, `nearest_competitor_m`, `market_share_proxy`, `substitution_risk` |
| Complementary | 5 | `complementary_diversity`, `total_places_300m`, `complementary_fnb_300m`, `complementary_retail_300m`, `complementary_score` |
| Anchor proximity | 29 | 14 anchor types × (count + dist) + composite (more than the 19 cited in the first draft) |
| Demand pull | 8 | 6 pulls + `pull_total_pop` + `demand_context_score` broadcast from host hex |
| Synergy (target-only) | 10 | Fires only on matching main_category |
| Transit | 8 | `nwalk_mrt_m`, `nwalk_bus_m`, scores, GTFS headway, routes, daily taps, composite |
| Catchment | 5 | `catchment_pop`, elderly, nonresident, nonres_share, daytime |
| Building | 8 | From hex: bldg_count, floors, hdb_blocks, land-use shares |
| Neighborhood char | 8 | From parent hex-8 |
| Supply-demand fit | 5 | `saturation_own_category`, `gap_own_category`, `demand_match`, `gap_fill_score`, `survivability_index` |
| Archetype | 9 | Per-place archetype tags (inherited from hex-8 + place-local) |
| Satellite | 2 | `nl_radiance`, `nl_change` broadcast from hex |
| Composite | 1 | `context_score` |

---

## 9. Derived-metric formula reference

Copy-paste reference, no hidden constants.

```python
# Walkability decay
walk_score(d_m) = exp(-d_m / 800.0)

# Demand pull (native per resolution)
pull_X(h) = sum( src_X(n) * exp(-dist(h,n)/lambda_X)
                 for n in k_ring(h, 2) )

# Synergy (hex-level, fires on all)
synergy_cat_pull(h) = cat_count(h) * pull_X(h)

# Synergy (place-level, fires only on target-category records)
synergy_cat_pull(place) = pull_X(place.hex) if place.category == cat else 0

# Saturation
benchmark_per_1000 = P60(actual_density_hex[pop_total > 500])
expected(h) = pop_total(h) * benchmark_per_1000 / 1000
saturation(h) = actual(h) / expected(h)
gap(h)        = expected(h) - actual(h)

# Anchor score
anchor_score(h) = sum(w_a * exp(-dist_a(h)/1000) for a in anchor_types)

# Context score (place-level composite)
context_score(p) =   0.30 * complementary_score(p)
                   + 0.30 * anchor_score(p.hex)
                   + 0.25 * transit_score(p.hex)
                   + 0.15 * (1 / (1 + competitors_200m(p)))

# Survivability (place-level)
survivability(p) =   demand_match(p)
                   * (1 - min(saturation_own(p)/5, 1))
                   * transit_score(p.hex)
                   * gap_fill_score(p)

# Influence
interface_score(h)  = lu_transitions(h) / max(lu_count(h), 1)
gradient_position(h, metric)
    = (self(h) - mean(ring1(h))) / (std(ring1(h)) + eps)
net_demand_flow(h)  = (pull_residential(h) - pull_office(h))
                    / (pull_residential(h) + pull_office(h) + eps)
```

---

## 10. Aggregation rules (hex-9 → hex-8)

Per-feature rule (stored as metadata on every feature):

| Feature type | Method | Example |
|---|---|---|
| Counts | SUM | pop, place_count, mrt_stations |
| Rates / percentages | POP-WEIGHTED MEAN | lu_residential_pct, walkability |
| Distances | MIN | walk_mrt_m |
| Heights / extremes | MAX | max_floors |
| Demand pull | NATIVE recompute (different λ) | pull_office_hex8 |
| Internal structure | CROSS-SCALE | pop_concentration (Gini over hex-9 children) |
| Categorical | MODE | dominant_use |
| Distributions | STACK (keep both) | age bins, dwelling types |

**Rule:** every feature is tagged with its aggregation method at build time; the aggregator reads the tag, no hand-coded lookup.

---

## 11. Validation & Test Suite

The Plexis test suite has **ten layers**. A city build is "shipped" only when all layers ≥ 95% pass (with documented exceptions).

### 11.1 Layer 1 — Totals conservation (deterministic)

Verify SUM features equal the raw inputs.

| Check | Tolerance | Example |
|---|---|---|
| Σ place_count_hex == n_places_master | 0 | SGP: 169,294 + 5,419 outside = 174,713 |
| Σ pop_hex == census_pop | 0.02% | SGP: 4,212,320 / 4,212,800 (-0.011%) |
| Σ mrt_stations_hex == station_register | 0 | SGP: 231 exact |
| Σ hdb_blocks_hex == authoritative | 0 | SGP: 13,386 exact |
| Σ hawker_centres == registry | 0 | SGP: 129 exact |
| Σ hotels == registry | 0 | SGP: 468 exact |

### 11.2 Layer 2 — Value ranges

| Check | Rule |
|---|---|
| Percentage columns | in [0, 1] |
| Count columns | ≥ 0 |
| Elderly / children ≤ pop_total | per-hex |
| Σ category counts == pc_total | per-hex |
| Σ land-use shares ≈ 1.0 | per-hex (tol 1e-3) |
| Entropy | in [0, ln(24)] |
| Saturation | in [0, 50] with computed-only-where-pop>500 |

### 11.3 Layer 3 — Cross-feature coherence (correlation signatures)

Each Plexis build produces these correlation numbers. They fail if they regress.

| Signature | Expected r |
|---|---|
| corr(population, residential_floor_area) | ≥ 0.9 |
| corr(hdb_blocks, population) | ≥ 0.80 |
| corr(walkability, anchor_score) | ≥ 0.5 |
| % of hexes with MRT-taps > 0 also having MRT station in-hex | ≥ 90% |
| % of hexes with lu_residential > 0.5 having pop > 0 | ≥ 85% |

### 11.4 Layer 4 — Named-landmark spot checks (city-specific)

For each city, curate a **landmark fixture** of 10–20 iconic places with known commercial character. Every build must match expectation.

SGP fixture (8/8 PASS):

| Landmark | Expected | Feature asserted |
|---|---|---|
| VivoCity | Shopping retail anchor | ≥ 150 shopping places in hex |
| Marina Bay Sands | Luxury tier dominant | ≥ 50 luxury places |
| ION Orchard | High place density | ≥ 1,000 places in hex |
| Raffles Place | Business-class dominant | ≥ 300 business places |
| Changi Airport T1 | Shopping + hotel | ≥ 80 shopping places |
| Universal Studios Sentosa | Culture/entertainment | ≥ 20 culture places |
| NUS Kent Ridge | Education + institutional | lu_institutional = 1.00 |
| Jurong Island | Industrial | lu_business = 1.00 |

**Template for new cities:** pick the most-queried landmarks (a mall, a CBD block, a university, a tourist site, a transit interchange, a major hospital, an industrial park) and assert category mix + land use.

### 11.5 Layer 5 — Well-known brand tests

Do known brands show up where they should, and does site-selection place them there?

| Test | Input | Expected behavior |
|---|---|---|
| Starbucks → CBD | `/api/ask "where should Starbucks open?"` | Top-5 all in CBD planning areas (SGP: Raffles Place, Downtown Core, Tanjong Pagar) |
| FairPrice → HDB estates | `/api/ask "where should FairPrice open?"` | Top-5 all in mature HDB planning areas (SGP: Bedok, Tampines, Woodlands) |
| McDonald's → transit-anchored high-footfall | Top-5 | Hexes with mrt_stations ≥ 1 AND pull_transit > P75 |
| Chanel → luxury corridor | Top-5 | Hexes in Orchard planning area OR Marina Bay |
| 7-Eleven → commuter transit | Top-5 | pull_transit > P75 AND population_total > 1,000 |

Each city has its own brand fixture. Run `run_brand_tests.py`, count pass rate, fail build if < 70%.

### 11.6 Layer 6 — Places micrograph tests

For each of 12 micrograph categories, a hand-picked fixture of 5 known-good places must score as expected on their category's micrograph.

| Category | Fixture | Assertion |
|---|---|---|
| Cafe (mature market) | Starbucks @ Raffles Place | competitor_pressure > P75, anchor_count ≥ 3 (MRT + hotel + office) |
| Cafe (captive market) | Ya Kun @ Bedok MRT | pull_residential > P50, pull_transit > P75 |
| Restaurant (tourist) | Din Tai Fung @ Ion Orchard | pull_hotel > P75, competitor_pressure > P75 |
| Hawker (destination) | Newton Food Centre | density_band=hyperdense, complementary_retail_300m > P75 |
| Clinic (HDB estate) | CHAS clinic @ Toa Payoh void deck | pull_residential > P75, catchment_elderly > P50 |
| Gym (residential) | ActiveSG @ Tampines | pull_residential > P75, anchor_score > P50 |
| Bar (nightlife) | Clarke Quay | pull_hotel > P75, competitor_pressure > P75, synergy_nightlife > P75 |

### 11.7 Layer 7 — Paper replication tests

The atlas must reproduce the empirical findings of the canonical urban-economics literature. Current scorecard: **9/10 papers replicated, 8/8 theories validated** (from `digital-atlas-apps/backend/static/reports/paper_replication_v2.html`).

| # | Paper | Finding to reproduce | Plexis assertion |
|---|---|---|---|
| 1 | Jacobs 1961 — *Death and Life of Great American Cities* | Mixed-use, dense neighborhoods have more street vitality | lu_entropy × pop_density predicts place_count (R² ≥ 0.5) |
| 2 | Krugman 1991 — *Geography and Trade* | Firms agglomerate | ANCHORED_BY + SYNERGIZES_WITH density → firm count (R² ≥ 0.4) |
| 3 | Hotelling 1929 — *Stability in Competition* | Competitors locate near each other | COMPETES_WITH edge density > random baseline at 500 m |
| 4 | Sampson 2012 — *Great American City* | Neighborhood effects persist across time | hex archetype stability across resamples ≥ 80% |
| 5 | Chetty et al. 2018 — *Opportunity Atlas* | Upward mobility varies by tract | archetype predicts HDB price growth (R² ≥ 0.3) |
| 6 | Kwate 2008 — *Fried Chicken and Fresh Apples* | Fast-food density correlates with income | corr(QSR density, HDB psf) < 0 |
| 7 | Glaeser et al. 2001 — *Consumer City* | Cities with amenities attract skilled labor | anchor_score predicts daytime_intensity (R² ≥ 0.4) |
| 8 | Wilson 1987 — *The Truly Disadvantaged* | Poverty concentrates spatially | low-pop-density hexes with low anchor_score cluster |
| 9 | Florida 2002 — *Rise of the Creative Class* | Creative clusters emerge in dense mixed-use areas | lu_entropy predicts business-density in young-pop hexes |
| 10 | Schuetz et al. 2012 — *Poor Neighborhoods Retail Deserts?* | Retail gaps correlate with income (partial) | corr(saturation_retail, HDB psf) weak but positive |

Plus 8 theories of urban form (Central Place Theory, Retail Hierarchy, Agglomeration, Consumer City, TOD, Spatial Mismatch, Creative Class, Neighborhood Effects) — each has one quantitative signature the build must produce.

### 11.8 Layer 8 — Model performance tests

On held-out splits:

| Model | Metric | Threshold |
|---|---|---|
| V7 gap model | R² (cross-category) | ≥ 0.70 |
| V8 population model | R² | ≥ 0.80 |
| Plexis-Embed category classifier | Accuracy | ≥ 0.70 |
| Plexis-Embed walkability regression | R² | ≥ 0.85 |
| XGBoost per-category | R² (median across 24) | ≥ 0.55 |

### 11.9 Layer 9 — Use-case integration tests

50 queries across the 9 Merlion use cases. Current SGP score: **27/50 = 54%**. Per-use-case:

| Use case | Pass rate | Issue if < 70% |
|---|---|---|
| site_selection (branded) | 5/5 (Starbucks, FairPrice, McDonald's, …) | — |
| site_selection (generic) | 0/5 | Category-aware scoring missing |
| gap_analysis | 2/5 | XGBoost predicts high where features already high |
| archetype_clustering | 0/5 | Handler empty |
| comparable_market | 3/5 | — |
| whitespace_analysis | 3/5 | — |
| category_prediction | 0/5 | Handler empty |
| feature_query | 0/5 | Handler empty — needs DuckDB wiring |
| amenity_desert | 1/5 | Scores by absolute gap, not per-capita |
| fifteen_minute_city | 5/5 | — |

Build fails if any use case is 0/5 after fixes.

### 11.10 Layer 10 — Cross-city replication

A Plexis build is "portable" only if the same pipeline produces coherent results in a second city. Reference targets:

| City | Status | Key checks |
|---|---|---|
| SGP | Reference | 33/33 hex checks |
| NYC | Partial | Papers 10/10 replicated (primary city) |
| LA | Partial | Papers 10/10 |
| SF | Partial | Papers 7/10 (smaller, different form) |
| SJ | Partial | Papers 8/10 |
| Chicago | Partial | Papers 10/10 |
| HKG | In progress | Pipeline being ported |

Expect to **lose** city-specific relations (VOID_DECK_OF → GROUND_FLOOR_OF, or drop). Expect to **gain** city-specific relations for new cities (e.g., TRANSIT_CARD_ZONE for NYC fare zones).

### 11.11 Full test-suite invocation

```
scripts/tests/
  test_layer1_totals.py
  test_layer2_ranges.py
  test_layer3_coherence.py
  test_layer4_landmarks.py              # fixture: city_landmarks.yaml
  test_layer5_brand_sites.py            # fixture: city_brands.yaml
  test_layer6_micrograph.py             # fixture: city_micrograph_fixtures.yaml
  test_layer7_paper_replication.py      # fixture: papers.yaml (universal)
  test_layer8_model_perf.py
  test_layer9_usecase_integration.py    # fixture: city_query_set.yaml
  test_layer10_cross_city.py            # compares signatures across cities
```

Each layer emits a JSON report. `run_all_tests.py` aggregates into `plexis_test_scorecard.json`.

---

## 12. Adaptation playbook — new city / country

### 12.1 Pre-flight (day 0)

| Step | Output |
|---|---|
| Inventory data sources against §4.1 mandatory list | coverage_matrix.csv |
| Pick tier-1 unit per §3 | boundaries.geojson |
| Pick H3 resolutions per §3.1 | resolution_spec.json |
| Build category taxonomy (start from 24 SGP cats, add local specials) | taxonomy.yaml |
| Curate landmark fixture (§11.4), brand fixture (§11.5), micrograph fixture (§11.6), query set (§11.9) | city_*.yaml |
| Decide which of the 39 relations to include / drop / add | relations_config.yaml |

### 12.2 Build order

1. Stage 0 universe → **gate:** hex count within expected range per §3.1
2. Stage 1 places → **gate:** place/km² within 50–500 depending on density
3. Stages 2–6 physical layers → **gate:** Layer 1 (totals)
4. Stages 7–14 derived features → **gate:** Layer 2, 3 (ranges, coherence)
5. Stages 15–17 normalize + aggregate + places → **gate:** Layer 4, 6 (landmarks, micrographs)
6. Stage 18 graph → **gate:** Layer 5 (brand tests via graph queries)
7. Stage 19 embed (optional) → **gate:** Layer 8 (model perf)
8. Integration → **gate:** Layer 9, 10 (use cases, cross-city)

### 12.3 Decay-constant tuning

Default constants (§9) are SGP-tuned. For a new city, tune via grid search on:
- λ_office ∈ {300, 400, 500, 600} m for hex-9
- λ_residential ∈ {400, 500, 600, 700, 800} m

Objective: maximize R² of `pull_residential → place_count_residential-complementary` on held-out hexes.

### 12.4 Relation localization

| Relation | Always include | Include if data available | Localize | Drop if |
|---|---|---|---|---|
| LOCATED_IN, PARENT_OF, IS_A, ADJACENT_TO | ✓ | — | — | — |
| COMPETES_WITH, SYNERGIZES_WITH, SUBSTITUTES_FOR | ✓ | — | substitution map per culture | — |
| ANCHORED_BY | ✓ | — | anchor list per city | — |
| FEEDS_INTO, BUS_CORRIDOR, EXPRESSWAY_* | — | if GTFS + roads | — | no transit data |
| UNDERSUPPLIED, OVERSUPPLIED | ✓ | — | — | — |
| VOID_DECK_OF | — | — | **replace** with GROUND_FLOOR_OF_PUBLIC_HOUSING if applicable | no social housing data |
| COASTAL | ✓ | — | — | landlocked |
| PRICE_GRADIENT | — | if property-txn data | — | no property data |

---

## 13. Outputs contract

Downstream consumers (Merlion, atlas apps, scenario sim) read only these files:

| File | Schema | Guarantee |
|---|---|---|
| `hex9_final.parquet` | 7,318 rows × 613 cols | H3 res-9 cells, all features named per catalog |
| `hex8_final.parquet` | 1,191 × 638 | H3 res-8 cells |
| `subzone_features.parquet` | 332 × 243 | Tier-1 planning units |
| `places_featured.parquet` | 174,711 × 114 | One row per place |
| `plexis_triplets.parquet` | ~1.5M × 15 | Relational graph |
| `plexis_v*_embeddings.npz` | 256d per node | Optional |
| `hex_features_v10_catalog.md` | — | Feature dictionary |
| `plexis_graph_summary.json` | — | Relation counts |

Columns are never renamed in-place. Renames bump the output version (`_v11`, etc.).

---

## 14. Runtime + infra

### 14.1 Per-stage runtime (SGP reference, 16-core 62 GB)

| Stage | Runtime |
|---|---|
| 0 universe | < 1 min |
| 1 places (LLM-heavy) | 15–30 min |
| 2 buildings | 3–5 min |
| 3 population | 2 min |
| 4 land use | 3 min |
| 5 transit | 4 min |
| 6 walk graph | 5 min (one-time) |
| 7 composition | 1 min |
| 8 amenities | 3 min |
| 9 pull (native × 2 resolutions) | 4 min |
| 10 synergy | < 1 min |
| 11 saturation | 1 min |
| 12 rings | 3 min |
| 13 micrograph | 8–12 min |
| 14 influence | 2 min |
| 15 merge+normalize | 1 min |
| 16 hex-8 aggregate | 1 min |
| 17 place enrichment | 3–5 min |
| 18 graph construction | 3–5 min |
| **Total feature + graph** | **60–90 min** |
| 19 embed training (v6) | 84 min (GPU), 4–6 h (CPU) |

### 14.2 Memory ceiling

Peak: ~40 GB during Stage 13 (micrograph, per-category ball-tree). All other stages < 16 GB.

### 14.3 Serving

- DuckDB over parquet: < 7 ms per query, no index required
- Plexis-Graph via pandas/pyarrow with edge-type index: < 50 ms for ring-2 traversal
- Embeddings via numpy memmap: < 10 ms per top-K cosine

### 14.4 Validated against live data (2026-04-23)

Feature counts in §8 are reconciled against the live parquets on atlas-1. Column-level inventory in `docs/FEATURE_CATALOG.md` (§4 contains the discrepancy audit vs this doc's v1.0 draft).

---

## 15. Glossary

| Term | Definition |
|---|---|
| **Plexis** | Umbrella methodology — feature stack + graph + optional embed |
| **Plexis-Graph** | Heterogeneous relational graph (39 typed relations) |
| **Plexis-Embed** | Optional 256d GAT-R-GCN embeddings |
| **Hex-9 / Hex-8** | H3 cells at resolution 9 / 8 |
| **Tier-1** | Planning unit — subzone / census tract / arrondissement |
| **Pull** | Distance-decay weighted demand score |
| **Synergy** | Category × pull co-location score (fires only on target category at place level) |
| **Saturation** | Actual / expected supply ratio |
| **Anchor** | Demand-generator amenity (MRT, hawker, etc.) |
| **Micrograph** | Per-category context vector for each hex |
| **Broadcast leakage** | Using a subzone-constant feature at hex level |
| **Native recompute** | Re-deriving a metric at a new resolution (not aggregating) |
| **Archetype** | K-means cluster label over hex features |
| **Landmark fixture** | Curated list of iconic places for spot-check validation |
| **Brand fixture** | Known brand → expected locality map |

---

## 16. Version history

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-04-23 | First release — extracted from SGP v10 reference build |
| 1.1 | 2026-04-23 | Reconciled feature catalog against live parquets. Added pillars: Dynamic LTA (18), Development gap (4), Distance-to-amenity Euclidean (8), Roads & signals (15). Expanded satellite into 4 sub-layers (VIIRS, GHSL, WorldPop, WorldCover). Corrected hex totals: 603→613 (hex-9), 628→638 (hex-8). |

---

*For the SGP reference implementation see `docs/SGP_DIGITAL_ATLAS_METHODOLOGY.md` and `docs/HOW_WE_BUILT_DIGITAL_ATLAS.md`.*
*For the Plexis-Embed training history see `docs/PLEXIS_EVOLUTION.md`.*
*For the Plexis-Graph quick-start see `data/plexis/README.md`.*
