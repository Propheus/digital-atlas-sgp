# SGP Digital Atlas — Methodology & Representation Guide

**Version:** 1.0  
**Date:** 2026-04-18  
**Coverage:** Singapore, 771 km²  
**Population:** 5,982,320 (4,212,320 residents + 1,770,000 non-residents)  
**Places:** 174,711 commercial and institutional points of interest  

---

## 1. Two Representations, One Urban Model

The SGP Digital Atlas represents Singapore's urban fabric through two complementary lenses:

**Region representation** answers: *"What kind of place is this area?"*  
**Place representation** answers: *"How does this specific business fit its context?"*

Every place record carries its region IDs (hex-9, hex-8, subzone), so the two representations are joinable. A query like "show me all cafes in under-served hex-8 cells with high office pull" crosses both layers in a single join.

```
                    ┌─────────────────────┐
                    │   SUBZONE (326)     │  URA planning units, ~449 features
                    │   ~12 km² avg       │  Policy-level analysis
                    └─────────┬───────────┘
                              │ contains ~3.5 hex-8
                    ┌─────────▼───────────┐
                    │   HEX-8 (1,191)     │  Neighborhood blocks, 597 features
                    │   ~0.74 km², 461m   │  Demand-pull, saturation, ecosystem
                    └─────────┬───────────┘
                              │ contains ~6.1 hex-9
                    ┌─────────▼───────────┐
                    │   HEX-9 (7,318)     │  Building clusters, 580 features
                    │   ~0.11 km², 174m   │  Micrograph context, walkability
                    └─────────┬───────────┘
                              │ contains ~24 places
                    ┌─────────▼───────────┐
                    │  PLACES (174,711)   │  Individual businesses, 96 features
                    │   Point locations    │  Competition, synergy, survivability
                    └─────────────────────┘
```

---

## 2. Region Representation

### 2.1 What it is

A multi-resolution spatial feature surface that describes every ~0.1–0.7 km² cell of Singapore across demographics, built environment, transit, commerce, and demand dynamics. Three levels:

| Level | Unit | Count | Area | Features | Primary use |
|-------|------|-------|------|----------|-------------|
| **Hex-9** | H3 resolution 9 | 7,318 | 0.105 km² | 580 | Fine-grained analysis, place context |
| **Hex-8** | H3 resolution 8 | 1,191 | 0.737 km² | 597 | Neighborhood analysis, gap detection |
| **Subzone** | URA planning | 326 | ~2.4 km² | ~449 | Policy, planning, reporting |

Hex-8 is the primary analytical unit — large enough for statistically meaningful per-capita metrics, small enough to capture neighborhood-level variation. Hex-9 provides granularity for place-level context. Subzone provides policy alignment.

### 2.2 Feature pillars (region)

#### Demographics (18 features at hex-8)
Population by age (children, working age, elderly), total population (residents + non-residents = 5.98M), dwelling-type breakdown, dependency ratio, elderly percentage, HDB population share, daytime intensity (worker inflow ratio), non-resident share.

**Key design decision:** All demand-side metrics use `population_total` (5.98M), not resident-only (4.21M). This prevents industrial/CBD zones with zero residents but thousands of workers from appearing as "empty" in demand calculations. The 1.77M non-residents (foreign workers, EP/S-pass holders, students) are real users of transit, food, healthcare, and retail.

**Source:** SingStat 2025 subzone population by age/sex/floor-area, dasymetrically allocated to hexes using building footprint weights from Overture Maps (377K buildings).

#### Built Environment (16 features)
Building count, density, floor count (avg/max), HDB blocks, commercial/residential/industrial building classification, gross plot ratio, floor area (total, residential, commercial).

**Source:** Overture Maps 2026 building footprints (377,331), fused with OSM building attributes. HDB detection via name-matching and building class.

#### Land Use (12 features)
URA Master Plan zoning percentages (residential, commercial, business, institutional, open space, transport), land-use entropy, dominant use classification, internal fragmentation (how many different land uses within one hex-8, measured via res-9 children).

**Source:** URA Master Plan 2019 land use parcels (113,212), tessellated to hex by area intersection.

#### Transit Infrastructure (18 features)
MRT stations (187), LRT stations (44), bus stops (5,172), transit mode count, daily tap volumes (MRT + bus = 12.3M taps/day), temporal split (AM peak / PM peak / off-peak / night), peak ratio.

**Source:** LTA station register (Mar 2026), LTA ridership data (Jan 2026 train, Dec 2025 bus), hourly tap volumes aggregated by time window.

#### GTFS Frequency (8 features)
Headway in minutes by time window (AM peak 7-9am, PM peak 5-8pm, off-peak 10am-4pm, night 9pm-5am), routes served per hex, daily departures, composite frequency score.

**Key insight:** Headway captures service quality, not just coverage. A hex with a bus stop but 45-minute headways has poor effective access. Median AM headway across served hexes: 25 min (hex-8), 31 min (hex-9).

**Source:** Singapore GTFS 2026 (230,914 trips, 5,376 stops, 602 routes). Weekday schedules extracted, stop-level arrivals aggregated by hour, headway = (window_hours × 60) / daily_arrivals.

#### Walkability (26 features at hex-9)
Two parallel distance systems:

**Euclidean distances** (`walk_*_m`): Straight-line distance from hex centroid to nearest MRT, bus stop, hawker centre, clinic, park, supermarket. Fast to compute, underestimates actual walk.

**Network distances** (`nwalk_*_m`): Shortest path on OSM pedestrian graph (213,978 nodes, 306,511 edges, motorways/trunks excluded). Accounts for road layout, expressway barriers, canal crossings.

| Amenity | Euclidean median | Network median | Ratio |
|---------|-----------------|----------------|-------|
| MRT | 1,752m | 1,600m (hex-9) | 1.6x typical |
| Bus | 464m | 537m | 1.3x |
| Hawker | 2,292m | 1,794m | varies |
| Clinic | 1,339m | 1,412m | 1.4x |

Each distance has a corresponding score: `exp(-distance / 800m)`, where 800m ≈ 10-minute comfortable walk. Composite walkability = mean of all scores.

**Source:** OSM road network (550,991 segments), filtered to pedestrian-accessible types. Amenity locations from LTA (stations/stops) and various government datasets.

#### Demand Pull (12 features)
Six distance-decay weighted demand scores, each answering "how much demand of type X flows toward this hex from its surroundings?"

| Pull | Source signal | Decay λ (hex-9/hex-8) | What it captures |
|------|-------------|----------------------|------------------|
| `pull_office` | Business + office places in neighbors | 400m / 600m | Lunch, coffee, services demand from workers |
| `pull_residential` | Total population in neighbors | 500m / 800m | Daily needs demand from residents + workers |
| `pull_transit` | Transit taps in neighbors | 400m / 500m | Commuter impulse demand (grab-and-go) |
| `pull_hotel` | Hotels in neighbors | 500m / 800m | Tourist dining, retail demand |
| `pull_school` | Schools in neighbors | 500m / 800m | Parent traffic, after-school economy |
| `pull_hawker` | Hawker centres in neighbors | 400m / 600m | Food destination gravity (SGP-specific) |

**Formula:** `pull(h) = Σ over neighbors n in k-ring(h, 2): source_strength(n) × exp(-distance(h,n) / λ)`

Each pull has a percentile-ranked version (`_pctl`) for cross-hex comparison.

**Key design decision:** Decay constants differ between hex-9 and hex-8 because the neighborhood radius differs. Hex-9 k=1 ring ≈ 370m (walking scale); hex-8 k=1 ring ≈ 800m (neighborhood scale). Demand pull is computed natively at each resolution, not aggregated.

#### Synergy Scores (20 features)
Ten co-location value scores measuring how much a category benefits from a specific demand type:

| Synergy | Formula | SGP example |
|---------|---------|-------------|
| `synergy_cafe_office` | cafe_count × pull_office | Starbucks in Raffles Place |
| `synergy_grocery_residential` | supermarket_count × pull_residential | NTUC in HDB estate |
| `synergy_conv_transit` | convenience_count × pull_transit | 7-Eleven at MRT exit |
| `synergy_rest_hotel` | restaurant_count × pull_hotel | Orchard Road dining |
| `synergy_lifestyle` | gym_count × pull_residential | Tanjong Pagar fitness cluster |
| `synergy_health` | clinic_count × pull_residential | HDB void deck medical row |
| `synergy_nightlife` | bar_count × pull_hotel | Clarke Quay |
| `synergy_education` | education_count × pull_school | Bukit Timah tuition belt |
| `synergy_financial` | business_count × pull_office | Shenton Way bank row |
| `synergy_morning` | bakery_count × pull_transit | Ya Kun at MRT station |

At region level, synergy fires on all hexes (measuring the area's synergy potential). At place level, synergy fires only on the target category (a cafe gets `synergy_cafe_office`, a bar does not).

#### Supply-Demand Saturation (10 features)
For 5 categories (restaurant, cafe, convenience, health, FnB total):

- `saturation_{cat}` = actual_places / expected_places, where expected = population_total × benchmark_per_1000 (60th percentile of well-served hexes). Values >1 = oversupplied, <1 = undersupplied.
- `gap_{cat}` = expected - actual. Positive = undersupplied (opportunity).

**Key design decision:** Uses `population_total` as denominator, and only computes for hexes with total_pop > 500. This prevents zero-population industrial hexes from showing infinite saturation.

#### Spatial Context (123 features at hex-9)
Ring-1 and ring-2 neighbor aggregates: maximum and population-weighted mean of key metrics (population, elderly, building count, place count, category counts, land use, micrograph context vectors). Captures "what's around this hex" beyond its own boundaries.

#### Micrograph (156 features at hex-9)
Per-category (12 categories) context vectors from the micrograph pipeline: transit context, competitor pressure, complementary context, demand context, anchor count, competition pressure, density band distribution (hyperdense/dense/moderate/sparse), walkability. These are the most granular commercial-context features.

#### Internal Structure (hex-8 only, 5 features)
Cross-scale features using hex-9 children as sub-samples within each hex-8:

- `pop_concentration` — Gini coefficient of child populations (high = people clustered in 1-2 towers)
- `place_clustering` — Gini of child place counts (high = mall-anchored, low = street retail)
- `pop_commercial_correlation` — do people and shops co-locate? (positive = integrated, negative = separated)
- `lu_fragmentation` — how many different dominant land uses across children (1 = homogeneous, 4+ = transitional)
- `dominant_use` — categorical label (residential/commercial/business/institutional/open_space)

#### Ecosystem Completeness (hex-8 only, 2 features)
- `ecosystem_completeness` — fraction of 7 daily-needs categories present (food, health, education, green, transit, convenience, community). Score 0-1.
- `self_containment` — fraction of 4 key amenities present (hawker, supermarket, clinic, park). Score 0-1.

These answer: "Can residents meet daily needs without leaving this neighborhood?"

#### Influence Features (3 features)
- `interface_score` — land-use transition rate across hex boundaries (high = mixed-use edge, retail opportunity)
- `gradient_position` — is this hex at the centre of a commercial cluster (+) or the edge (-)? Computed as (self_metric - ring1_mean) / ring1_std.
- `net_demand_flow` — residential pull minus office pull, normalized. Positive = demand flows in (dormitory serves captive market). Negative = demand flows out (commercial competition zone).

#### Property (2 features)
- `hdb_median_psf` — median HDB resale price per square foot (2025 transactions), mapped by planning area. Proxy for rent cost and income level.
- `hdb_txn_count` — transaction volume (market liquidity).

#### Additional Coverage
- OSM POIs (4): amenities, leisure, shops, tourism — supplementary to the main places layer
- SFA eating establishments: 34,366 licensed food outlets
- Park connector segments: 883 (active mobility infrastructure)
- EV charging points (where available)

### 2.3 Aggregation logic (hex-9 → hex-8)

Hex-8 values are derived from hex-9 children, not computed independently (except demand pull, which is native):

| Feature type | Method | Example |
|---|---|---|
| Counts | SUM | population, places, buildings, taps, stations |
| Rates / percentages | Population-weighted MEAN | walkability scores, land use %, context vectors |
| Distances | MIN | walk_mrt_m (nearest matters) |
| Heights | MAX | max_floors |
| Demand pull | NATIVE recompute | Different decay constants, different neighborhoods |
| Internal structure | CROSS-SCALE | Uses hex-9 children as sub-samples |

All SUM columns verified at 0.00% difference between hex-8 and hex-9 system totals.

---

## 3. Place Representation

### 3.1 What it is

A 96-feature vector for each of 174,711 commercial and institutional places in Singapore. Combines the place's own identity with its spatial context, competitive position, demand alignment, and survivability estimate.

**Canonical file:** `sgp_places_featured.parquet` (42 MB)

### 3.2 Feature groups (place)

#### Identity (14 features)
Name, address, coordinates, main category (24 types), place type (fine-grained), price tier (luxury/premium/mid/value/budget), brand flag, source, classification confidence.

**24 categories:** Shopping & Retail (27K), Restaurant (21K), Services (17K), Business (17K), Beauty & Personal Care (12K), Education (11K), Health & Medical (8K), Cafe & Coffee (7K), Fitness & Recreation (6K), Convenience & Daily Needs (6K), + 14 more.

**Source:** sgp_places_v2.jsonl — consolidated from Overture Maps, OSM, and LLM-classified sources.

#### Competition (5 features)
Same-category rivalry within walking distance:

- `competitors_200m` / `competitors_500m` — count of same-main_category places within radius (KD-tree spatial query)
- `nearest_competitor_m` — distance to closest same-category place
- `market_share_proxy` — 1 / (1 + competitors_500m)
- `substitution_risk` — count of substitute-category places within 300m (e.g., hawker stalls substitute for restaurants)

**Substitution map (SGP-specific):**
- Cafe competes with: Bakery, Hawker kopi stalls
- Restaurant competes with: Hawker, Fast Food
- Fast Food competes with: Hawker, Convenience ready-meals
- Convenience competes with: Supermarket

#### Complementary (5 features)
Cross-category diversity within 300m — measures the commercial ecosystem surrounding each place:

- `complementary_diversity` — unique main_categories within 300m (0-24). Higher = richer ecosystem.
- `total_places_300m` — all commercial places within 300m (footfall proxy)
- `complementary_fnb_300m` — F&B places nearby (for non-F&B places: dining options attract visitors)
- `complementary_retail_300m` — retail nearby
- `complementary_score` — normalized 0-1 (diversity / 15)

**Computation:** Single batch `query_ball_tree` call (175K × 175K within 300m), then category counting per result set. Vectorized — runs in ~3 minutes on atlas-1.

#### Anchor Proximity (19 features)
Distance and count for 9 demand-generator types:

| Anchor | Points | Radius | What it captures |
|--------|--------|--------|------------------|
| MRT station | 231 | 300m | Rail transit footfall |
| Bus stop | 5,177 | 200m | Bus network access |
| Hawker centre | 129 | 300m | SGP-unique food destination |
| Clinic | 1,193 | 500m | Healthcare ecosystem |
| Park | 450 | 500m | Green space / recreation |
| Supermarket | 526 | 300m | Daily grocery anchor |
| Hotel | 468 | 300m | Tourist demand |
| School | — | 500m | Family traffic |
| Tourist attraction | 109 | 500m | Visitor footfall |

Per anchor: `{anchor}_{radius}m` (count within radius) + `{anchor}_dist_m` (nearest distance).

`anchor_score` = weighted mean of `exp(-dist/1000)` across all anchor types. Composite 0-1.

#### Demand Pull (8 features)
Same 6 pull scores as region level, broadcast from the place's hex-9 cell: `pull_office`, `pull_residential`, `pull_transit`, `pull_hotel`, `pull_school`, `pull_hawker`, `pull_total_pop`.

`demand_context_score` = weighted composite: 0.25×residential + 0.20×office + 0.20×transit + 0.10×hotel + 0.10×school + 0.10×hawker.

#### Synergy (10 features)
**Critical design: fires ONLY on the target category.** A cafe record gets `synergy_cafe_office` (its office-pull value); a bar record gets zero for this field. This prevents the synergy signal from being diluted across irrelevant categories.

| Synergy | Fires on | Measures |
|---------|----------|----------|
| `synergy_cafe_office` | Cafe & Coffee only | Office pull at this location |
| `synergy_grocery_residential` | Convenience, Retail | Residential pull |
| `synergy_convenience_transit` | Convenience only | Transit pull |
| `synergy_restaurant_hotel` | Restaurant only | Hotel/tourist pull |
| `synergy_lifestyle` | Fitness only | Residential pull (gym near homes) |
| `synergy_health_cluster` | Health & Medical only | Residential pull |
| `synergy_nightlife` | Bar & Nightlife only | Hotel pull |
| `synergy_education` | Education only | School pull |
| `synergy_financial` | Business, Services | Office pull |
| `synergy_morning` | Bakery & Pastry only | Transit pull (commuter morning routine) |

**Difference from region-level synergy:** At region level, synergy = hex_category_count × hex_pull (aggregate). At place level, synergy = the pull score at this specific place's hex, activated only for the matching category. More precise, directly actionable.

#### Transit Access (8 features)
- `nwalk_mrt_m` / `nwalk_bus_m` — **network** walk distance (from OSM pedestrian graph, not Euclidean)
- `nwalk_mrt_score` / `nwalk_bus_score` — exponential decay scores
- `gtfs_headway_am_min` — best AM-peak headway at nearest stop (from GTFS)
- `gtfs_routes_served` — number of routes at nearest stop
- `transit_daily_taps` — tap volume at hex
- `transit_score` — composite: 0.5×MRT_decay + 0.3×bus_decay + 0.2×routes/20

**SGP advantage over HKG:** Network walk distances (not Euclidean) + GTFS frequency data. HKG had neither.

#### Catchment (5 features)
Who is around this place (from hex-9):

- `catchment_pop` — total population in hex (residents + workers)
- `catchment_elderly` — elderly count (matters for clinics, pharmacies)
- `catchment_nonresident` — non-resident workers (matters for CBD F&B)
- `catchment_nonres_share` — % non-resident
- `catchment_daytime` — daytime intensity ratio (>1 = net worker inflow)

#### Building Context (8 features)
From the hosting hex-9: building count, average/max floors, HDB blocks, commercial/residential land use percentages, land-use entropy.

#### Neighborhood Character (8 features)
From the parent hex-8: population density, elderly percentage, HDB share, ecosystem completeness, interface score, gradient position, HDB median PSF, non-resident share.

#### Supply-Demand Fit (5 features)
**New — not in HKG pipeline.** Does this place match its location's demand?

- `saturation_own_category` — is this place's category oversupplied here? (from hex-8 saturation model)
- `gap_own_category` — is there unmet demand for this category? (positive = gap exists)
- `demand_match` — category-to-pull alignment score (0-1). Uses lookup table mapping each category to its primary and secondary demand pull.
- `gap_fill_score` — 1 if this place fills a gap, 0 if it adds to oversupply
- `survivability_index` — composite: demand_match × (1 - saturation/5) × transit_score × gap_fill_score

**Demand-match lookup:**

| Category | Primary pull (weight) | Secondary pull |
|----------|----------------------|----------------|
| Cafe & Coffee | pull_office (0.6) | pull_transit (0.4) |
| Restaurant | pull_residential (0.5) | pull_hotel (0.5) |
| Fast Food / QSR | pull_transit (0.6) | pull_residential (0.4) |
| Convenience | pull_transit (0.7) | pull_residential (0.3) |
| Health & Medical | pull_residential (1.0) | — |
| Education | pull_school (0.6) | pull_residential (0.4) |
| Hawker & Street Food | pull_residential (0.6) | pull_transit (0.4) |

#### Composite (1 feature)
- `context_score` — overall place context quality: 0.30×complementary + 0.30×anchor + 0.25×transit + 0.15×(1/(1+competitors_200m))

### 3.3 Validation

11 checks, 10 pass:

| Check | Result |
|-------|--------|
| Dense areas have higher complementary diversity | ✓ |
| Grocery has higher pull_residential than bars | ✓ |
| Cafe synergy fires on cafes only, zero on bars | ✓ |
| Near-MRT places have higher anchor score | ✓ |
| Hotel-area places have higher pull_hotel | ✓ |
| context_score correlates with anchor_score (r>0.5) | ✓ |
| context_score correlates with transit_score (r>0.3) | ✓ |
| No negative competitor counts | ✓ |
| No negative catchment values | ✓ |
| survivability_index in [0,1] | ✓ |
| Cafes > hospitals in competitors_200m | ✗ (SGP-specific: medical clusters are denser) |

---

## 4. Context of Usage

### 4.1 Site selection
**Question:** "Where should I open a new cafe in Singapore?"

**How it works:**
1. Query hex-8 for `gap_cafe > 0` AND `pull_office > P75` — finds areas with unmet cafe demand near offices
2. Within those hexes, check `ecosystem_completeness > 0.7` — ensure basic infrastructure exists
3. At place level, check `survivability_index` for existing cafes — low survivability = tough market even if gap exists
4. Cross-check `saturation_cafe < 0.5` AND `gtfs_headway_am_min < 15` — undersupplied with good transit

### 4.2 Portfolio risk assessment
**Question:** "Which of my 50 outlets are at risk?"

**How it works:**
1. Load all 50 places from `sgp_places_featured.parquet`
2. Flag outlets where `saturation_own_category > 2.0` (oversupplied market)
3. Flag outlets where `demand_match < 0.3` (wrong location for this category)
4. Flag outlets where `competitors_200m > P90` (hyper-competitive)
5. Rank by `survivability_index` ascending — lowest = highest risk

### 4.3 Transport adequacy analysis
**Question:** "Where are the worst transit gaps for elderly residents?"

**How it works:**
1. Query hex-8 for `pct_elderly > 0.20` AND `nwalk_mrt_m > 2000` AND `gtfs_headway_am_min > 30`
2. Weight by `population × pct_elderly` — affected population
3. Check `ecosystem_completeness` — missing transit compounds other gaps
4. The gap report ranks hexes by population-weighted deficit

### 4.4 Demand-pull analysis
**Question:** "What demand flows toward this hex and who benefits?"

**How it works:**
1. Read hex-8 pull scores: `pull_office=500, pull_residential=80K, pull_transit=120K`
2. Interpretation: high residential + transit pull, low office → this is a commuter dormitory with captive daily-needs demand
3. Synergies that should fire: `synergy_grocery_residential`, `synergy_conv_transit`
4. Categories that fit: convenience, supermarket, clinic, hawker — NOT luxury dining, NOT office services

### 4.5 Competitive intelligence
**Question:** "How crowded is the restaurant market in Bugis?"

**How it works:**
1. Find Bugis hex-8 → `saturation_restaurant = 5.0` (max oversupply)
2. At place level: median `competitors_200m = 44` for restaurants in this hex
3. But `pull_hotel = P100` and `pull_transit = P96` — demand is real
4. Insight: market is crowded but demand-rich. Differentiation matters more than location.

### 4.6 Urban planning
**Question:** "Which neighborhoods lack basic amenities?"

**How it works:**
1. Hex-8 `ecosystem_completeness < 0.5` AND `population > 10,000` — populated areas missing essentials
2. `self_containment = 0.25` — only 1 of 4 key amenities present
3. Drill down: which category is the binding gap? Check individual amenity counts.
4. Cross-reference with `lu_fragmentation` and `interface_score` — is this a pure dormitory (low fragmentation) or a transitional zone?

---

## 5. Data Sources

| Source | Records | Role | Update frequency |
|--------|---------|------|------------------|
| Overture Maps + OSM | 174,713 places | Commercial POIs | Quarterly |
| Overture Buildings | 377,331 | Built form | Quarterly |
| LTA Station Register | 231 MRT + 44 LRT | Transit network | As-built |
| LTA Bus Stops | 5,177 | Bus network | Monthly |
| LTA Ridership | 12.3M taps/day | Transit demand | Monthly |
| Singapore GTFS 2026 | 230,914 trips | Service frequency | Annually |
| OSM Road Network | 550,991 segments | Walk distances | Continuous |
| SingStat Population | 5,982,320 | Demographics | Annually |
| SingStat Dwellings | 326 subzones | Housing types | Annually |
| HDB Resale Transactions | 227,207 | Property prices | Monthly |
| URA Master Plan | 113,212 parcels | Land use | Periodic |
| NEA/SFA | 34,366 licensed | F&B validation | Quarterly |
| Various gov datasets | ~3,000 | Amenity anchors | Varies |

---

## 6. Computation Pipeline

```
Phase 1: Raw data → Hex-9 assignment
         Places (174K), buildings (377K), stations, stops, amenities
         all assigned to hex-9 via H3.latlng_to_cell(lat, lng, 9)

Phase 2: Hex-9 feature computation
         Demographics (dasymetric), walkability (Euclidean + network),
         place composition, land use, transit taps

Phase 3: Hex-9 → Hex-8 aggregation
         SUM (counts), POP-WEIGHTED MEAN (rates), MIN (distances), MAX (heights)

Phase 4: Native hex-8 computation
         Demand pull (k-ring neighborhoods), synergies, internal structure,
         ecosystem completeness, saturation model, GTFS headways

Phase 5: Place enrichment
         Competition (per-category KD-tree), complementary (cross-category),
         anchor proximity, synergy (target-category-only), hex feature join,
         demand match, survivability index

Phase 6: Validation
         Cross-resolution consistency (all SUM columns match 0.00%),
         11 sanity checks on place features, spot-check against raw data
```

**Runtime:** ~5 minutes total on atlas-1 (16 cores, 62GB RAM).

---

## 7. Limitations

| Limitation | Impact | Mitigation |
|-----------|--------|------------|
| Walk distances are network but not isochrone | Underestimates barrier effects (overhead bridges, underpasses) | Use as lower bound; field-verify for planning |
| Population is subzone-level, dasymetrically allocated | Allocation noise at hex-9 level | Hex-8 aggregation smooths this |
| No place ratings or review counts | Can't distinguish quality within category | Price tier is a partial proxy |
| GTFS headways are synthetic for MRT | Exact train timetables are not public | Uses realistic 3-6 minute frequencies |
| Saturation model uses 60th percentile benchmark | Benchmark is relative, not absolute | Sensitivity analysis recommended |
| No temporal variation in demand pull | Office pull is 24/7 in the model | GTFS + temporal taps provide partial signal |
| Non-resident allocation is uniform within subzone | Workers may cluster in specific hexes | Daytime_ratio from census helps |
| 5,417 places fall outside hex grid boundary | 3% of places (ocean/border edge hexes) | Acceptable for analytics |

---

## 8. Files

| File | Location | Size | Records × Features |
|------|----------|------|-------------------|
| `hex9_final.parquet` | hex_v10/ | 8 MB | 7,318 × 580 |
| `hex8_final.parquet` | hex_v10/ | 3 MB | 1,191 × 597 |
| `hex9_features.json` | hex_v10/ | 122 MB | 7,318 × 580 |
| `hex8_features.json` | hex_v10/ | 21 MB | 1,191 × 597 |
| `subzone_features_full.json` | features/ | 4 MB | 326 × ~449 |
| `sgp_places_featured.parquet` | places_consolidated/ | 42 MB | 174,711 × 96 |
| `singapore-gtfs.zip` | gtfs/ | 336 MB | 230K trips |

All files present on both local and atlas-1 (10.2.2.5).

---

*Methodology v1.0 — 2026-04-18*  
*Built with: Python 3.12, DuckDB, H3, NetworkX, SciPy, Pandas*  
*Validated against 19 raw data sources, 11 sanity checks, 3 cross-resolution consistency checks*
