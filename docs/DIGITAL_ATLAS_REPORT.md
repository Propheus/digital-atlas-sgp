# Digital Atlas Singapore — Final Report

## Executive Summary

We built a mathematical representation of Singapore's urban structure at the subzone level (332 zones), integrating 15 data layers into a 202-dimensional feature vector per zone. The model learns what urban structure determines about place composition and what it doesn't — providing an honest foundation for gap analysis and location intelligence.

**Key finding:** Physical urban structure strongly predicts *how many* places exist in an area (R²=0.77) but weakly predicts *what kind* (R²=0.11-0.53). Place composition is primarily market-driven, not infrastructure-driven.

---

## The Data

### Scale
| Metric | Value |
|--------|-------|
| Population covered | 4,172,350 residents |
| Geographic area | 784.8 km² |
| Places catalogued | 66,845 |
| Subzones (regions) | 332 (229 viable for modeling) |
| Brands identified | 232 |
| Features per subzone | 202 |
| Data layers | 15 |
| Total data size | 1.9 GB |

### Place Composition

| Category | Places | Share |
|----------|------:|------:|
| Shopping & Retail | 12,280 | 18.4% |
| Restaurant | 5,656 | 8.5% |
| Services | 4,848 | 7.3% |
| Education | 3,949 | 5.9% |
| Beauty & Personal Care | 3,967 | 5.9% |
| Convenience & Daily Needs | 3,930 | 5.9% |
| Cafe & Coffee | 3,367 | 5.0% |
| Hawker & Street Food | 3,157 | 4.7% |
| Fitness & Recreation | 2,818 | 4.2% |
| Office & Workspace | 2,636 | 3.9% |
| Residential | 2,440 | 3.7% |
| Transport | 2,316 | 3.5% |
| Business | 2,251 | 3.4% |
| General | 1,973 | 3.0% |
| Civic & Government | 1,601 | 2.4% |
| Health & Medical | 1,561 | 2.3% |
| Bar & Nightlife | 1,388 | 2.1% |
| Automotive | 1,356 | 2.0% |
| Culture & Entertainment | 1,289 | 1.9% |
| Fast Food & QSR | 1,203 | 1.8% |
| Religious | 938 | 1.4% |
| Bakery & Pastry | 925 | 1.4% |
| NGO | 554 | 0.8% |
| Hospitality | 442 | 0.7% |

### Densest Subzones

| Subzone | Places | Per km² | Population |
|---------|------:|--------:|-----------:|
| Kampong Glam | 368 | 2,148 | 0 |
| Victoria | 415 | 1,937 | 1,660 |
| Little India | 408 | 1,466 | 2,760 |
| Boulevard (Orchard) | 660 | 1,433 | 310 |
| Crawford | 318 | 1,347 | 7,570 |
| Farrer Park | 291 | 1,334 | 2,360 |
| Bencoolen | 227 | 1,330 | 1,200 |
| Bugis | 365 | 1,303 | 1,200 |

Note: Kampong Glam and Victoria have high place density but low resident population — these are commercial/tourism destinations, not residential areas.

---

## Feature Architecture (202 dimensions per subzone)

### Block 1: Demographics (8 features)
Population total, density, age brackets (0-14, 15-64, 65+), gender ratio. Source: Singstat 2025 census at subzone level.

### Block 2: Dwelling Type (7 features)
HDB 1-2 room through 5-room/exec percentages, condo percentage, landed percentage. Proxy for income stratification — HDB 1-2 room correlates with lower income, condos with higher.

### Block 3: Property Market (4 features)
Median HDB resale price per sqft, YoY price change, transaction volume. Covers 216 of 332 subzones (HDB towns only).

### Block 4: Road Network (11 features)
Total road length, density (km per km²), breakdown by type: motorway, trunk, primary, secondary, tertiary, residential, service, footway, cycleway. Source: OpenStreetMap via OSMnx (550,991 road edges).

### Block 5: Land Use Zoning (13 features)
Percentage of area zoned residential, commercial, industrial, mixed-use, open space, institutional, transport, reserve, nature. Plus average GPR, land use entropy (Shannon), green ratio. Source: URA Master Plan (113,212 parcels).

### Block 6: Transit Accessibility (5 features)
Distance to nearest MRT, MRT stations within 1km, bus stops within 1km, bus density per km². Source: LTA shapefiles (231 MRT stations, 5,177 bus stops — March 2026).

### Block 7: Amenity Accessibility (9 features)
Distance to nearest park, hawker centre, supermarket, school. Count within 1km for parks, hawkers, supermarkets, schools, hotels. Source: government amenity datasets.

### Block 8: Place Composition (24 features)
Count of places in each of 24 main categories. This IS the target variable for prediction.

### Block 9: Place Type Counts (80 features)
Count of places in top 80 place_types (granular: Cafe, Gym, GP Clinic, Hawker Stall, etc.)

### Block 10: Brand & Quality (10 features)
Branded place count and percentage, unique brand count, average/median rating, rating std, high-rated percentage, review count, phone/website coverage.

### Block 11: Government Cross-Reference (6 features)
SFA licensed eating establishment count (34,378), CHAS clinic count (1,193), government preschool count (2,290), our place count vs government count, F&B coverage ratio.

---

## The Model

### Architecture: Two-Stage XGBoost

**Stage 1 — Density Prediction**
- Input: 70 physical features (no place data)
- Output: Total place count per subzone
- Model: GradientBoostingRegressor (300 trees, depth 5)
- **R² = 0.773** (10-fold CV)

**Stage 2 — Composition Prediction**
- Input: 70 physical features + observed category proportions (minus target)
- Output: Proportion for the masked category
- Model: One GradientBoostingRegressor per category (24 models)
- **R² = 0.11 (average) to 0.53 (best category)**

### Why Not Neural Networks?
We tested GCN-MLP (graph neural network) but XGBoost consistently outperformed it. With only 332 subzones, gradient boosted trees handle tabular data better than neural nets which need thousands of samples. The graph structure (spatial adjacency, transit connectivity) added marginal value — a subzone's composition is driven more by its own physical attributes than by its neighbors.

---

## What Urban Structure Determines (and What It Doesn't)

### Strong Signals (R² > 0.3)

| What we can predict | R² | Key drivers |
|--------------------:|---:|-------------|
| Total place density | 0.773 | Population, roads, land use, GPR |
| Office/Workspace proportion | 0.529 | Industrial zoning, commercial area |
| Shopping/Retail proportion | 0.467 | Commercial zoning, road density |
| Culture/Entertainment | 0.384 | Distance to CBD, institutional zoning |
| Residential places | 0.376 | Residential zoning, HDB blocks |
| Beauty/Personal Care | 0.365 | Population density, residential area |
| Education | 0.356 | Residential area, distance to schools |
| Fast Food/QSR | 0.335 | Transit proximity, population |
| Convenience/Daily Needs | 0.329 | Population, residential zoning |

These categories follow urban structure rules: offices go where there's commercial zoning, schools go near residential areas, retail follows road density and accessibility.

### Weak Signals (R² < 0.2)

| What we can't predict well | R² | Why |
|----------------------------:|---:|-----|
| Restaurant proportion | 0.176 | Entrepreneur choice, not zoning |
| Bakery/Pastry | 0.142 | Market demand, not infrastructure |
| Automotive | -0.073 | Legacy industrial locations |
| Health/Medical | -0.167 | Regulated placement, not market |
| Bar/Nightlife | -0.284 | Nighttime economy, tourism demand |
| Hospitality | -0.392 | Tourism flow, event calendars |
| Religious | -0.641 | Historical, community-driven |
| NGO | -0.692 | Mission-driven, not market |

These categories are driven by demand signals (foot traffic, tourism, spending patterns) and non-market forces (regulation, community, history) that our physical features don't capture.

---

## What Drives Place Composition

Top features from the model (averaged across all category models):

| Rank | Feature | Importance | Interpretation |
|-----:|---------|--------:|----------------|
| 1 | Industrial zoning % | 4.3% | Strongest structural separator |
| 2 | SFA eating establishment count | 2.5% | Gov food licensing = F&B signal |
| 3 | Distance to Orchard Road | 2.3% | Proximity to prime commercial |
| 4 | Distance to supermarket | 2.0% | Existing amenity infrastructure |
| 5 | Distance to hawker centre | 1.7% | Residential neighborhood signal |
| 6 | Open space zoning % | 1.7% | Parks reduce commercial density |
| 7 | Institutional zoning % | 1.6% | Schools/hospitals create demand |
| 8 | Average GPR | 1.6% | Development intensity |
| 9 | Land use entropy | 1.5% | Mixed-use = diverse composition |
| 10 | Road density | 1.5% | Accessibility drives places |

**Key insight:** Zoning is the #1 driver. Singapore's master plan literally determines where industrial, commercial, and residential activities can occur. The model learns this regulatory structure.

---

## Place Co-location Patterns

From the PMI (Pointwise Mutual Information) analysis of which place types appear together:

### Types that co-locate (positive PMI)
| Pair | PMI | Why |
|------|----:|-----|
| Library + Stadium | 2.42 | Both in large community hubs |
| Buffet + Lounge | 2.37 | Hotels/entertainment zones |
| Entertainment + Internet Cafe | 2.25 | Youth entertainment clusters |
| Hospital + Specialist Clinic | 1.72 | Medical clusters |
| International School + Library | 1.78 | Education corridors |

### Types that avoid each other (negative PMI)
| Pair | PMI | Why |
|------|----:|-----|
| HDB + Lounge | -10.0 | Lounges don't go in public housing |
| Mosque + Stadium | -10.0 | Different community functions |
| Lounge + Residential | -2.0 | Nightlife avoids residential |
| Buddhist Temple + Lounge | -1.6 | Cultural/religious vs entertainment |
| Lounge + Primary School | -1.4 | Regulatory separation |

---

## Gap Analysis: Where Singapore Has Opportunities

The density model identifies subzones where physical structure supports more places than currently exist:

### Potentially Underserved (predicted > actual)
These are areas where the physical infrastructure (roads, transit, population, zoning) suggests more places should exist.

### Potentially Oversaturated (actual > predicted)
These are areas with more places than the physical structure would predict — potentially competitive.

**Important caveat:** Gap scores are based on the density model (R²=0.77). The model captures structural capacity but not all demand factors. A "gap" could also mean: the area is newly developed and filling in, or there's a market reason for fewer places (high rents, low foot traffic).

---

## Data Quality Assessment

| Layer | Coverage | Quality |
|-------|---------|---------|
| Places | 66,845 (est. 20-25% of all SGP businesses) | Good — Google Maps sourced |
| Demographics | 332 subzones (100%) | Good — Singstat 2025 |
| Roads | 550,991 edges (complete) | Excellent — OSM |
| Buildings | 125,973 footprints | Good — OSM |
| Land Use | 113,212 parcels (100%) | Excellent — URA Master Plan |
| Transit | 5,177 bus + 231 MRT (2026) | Excellent — LTA |
| Property | 216 subzones (65%) — HDB only | Partial |
| Brands | 232 brands, 4,695 branded places | Fair |
| Cross-ref | SFA 34K, CHAS 1.2K, Preschools 2.3K | Good — government data |

### Known Gaps
- No foot traffic / passenger volume data (LTA API key required)
- No commercial rental rates
- No business registration/closure rates
- Private property prices only at national level
- Places cover ~25% of actual businesses (bias toward customer-facing)

---

## Utility & Applications

### What This Atlas Can Do Today

1. **Density opportunity scoring** — Identify subzones where physical structure supports more places than currently exist (R²=0.77, reliable)

2. **Category affinity ranking** — For well-predicted categories (office, retail, education, beauty), rank subzones by structural fit

3. **Urban structure profiling** — Characterize any subzone by its 202-dimension vector: is it residential-dominant? commercial? mixed? transit-rich? underserved?

4. **Competitive landscape** — Count same-category places at any radius, identify cluster density

5. **Cross-reference validation** — Compare our places data against government records (SFA, CHAS, ECDA) to identify data gaps

### What It Can't Do Yet (needs more data)

1. **Precise category mix prediction** — "Should this subzone have more cafes or more clinics?" (R²=0.11-0.53, category-dependent)

2. **Demand-based scoring** — "How many customers would a new cafe get here?" (no foot traffic data)

3. **Revenue estimation** — "What revenue can a business expect?" (no spending/rental data)

4. **Temporal trends** — "Is this area growing or declining?" (single snapshot)

---

## Technical Artifacts

### On Server (`rwm-server:/home/azureuser/digital-atlas-sgp/`)

```
data/                    1.9 GB — 15 data layers
intermediate/            11 parquet files — per-step features
final/
  subzone_features_raw.parquet    332 x 205 features
  subzone_features.parquet        332 x 205 (z-score normalized)
  place_features.parquet          66,851 x 13 features
  feature_catalog.csv             202 features documented
graphs/
  subzone_adjacency.json          332 nodes, 1,001 edges
  colocation_pmi.json             155 types, 5,397 PMI edges
  transit_connectivity.json       139 MRT-connected subzones
model_results_v5/
  report_v5.json                  Full metrics
  gap_analysis_v5.parquet         332 x 72 gap scores
scripts/
  test_framework.py               Validation suite (30 tests)
  atlas_model_v5.py               Reproducible training pipeline
```

### Documentation
- `ARCHITECTURE.md` — Feature design and model architecture
- `DATA_CATALOG.md` — Full data inventory
- `DATA_NEEDS.md` — What data exists and what's needed
- `MODEL_DIAGNOSIS.md` — Honest analysis of model weaknesses
- `BEST_MODEL.md` — Usage guide
- `PROCESSING_PLAN.md` — 19-step data pipeline

---

## What Would Improve This

| Data | Expected Impact | Source |
|------|----------------|--------|
| MRT/bus passenger volume | +0.10-0.15 R² for F&B, retail | LTA DataMall (API key) |
| Commercial rental rates | +0.05-0.10 for composition | URA rental data |
| Business registration/closure | Temporal validation | ACRA (partial — we have 2M entities) |
| Mobile phone movement | +0.15-0.20 for all categories | Telco / aggregator |
| Two timepoints (2020 vs 2025) | Trend detection | Historical scrape |

---

*Report generated: 2026-03-19*
*Digital Atlas Singapore v1.0*
