# Digital Atlas SGP — Demand & Supply Signals Ideation

**Date:** 2026-03-26
**Status:** Ideation — not yet implemented

---

## Core Question

For each subzone × category × tier: **"Is there more demand than supply, or more supply than demand?"**

Demand and supply are multi-dimensional, time-varying, and category-specific. A subzone can be oversupplied with hawker stalls but undersupplied with premium cafes. It can have high lunch demand but dead evenings.

---

## SUPPLY SIGNALS

### S1: Raw Place Count
- Places per category per subzone (24 categories × 328 subzones)
- Places per place_type per subzone (3,034 types × 328 subzones)
- Places per price_tier per subzone (5 tiers × 328 subzones)
- Places per segment per subzone (40+ segments × 328 subzones)
- **Source:** 174K consolidated places
- **Limitation:** Count alone doesn't capture quality or capacity

### S2: Supply Capacity
- Seating capacity: place type → avg seats (hawker stall ~20, restaurant ~60, cafe ~30, food court ~500)
- Operating hours: category → typical hours (hawker 6am-2pm, bar 6pm-2am, cafe 8am-6pm)
- Throughput: seats × turnover rate × hours (hawker: 20 × 4 turns × 8hrs = 640 meals/day)
- Floor area proxy: building data + place count per building → avg sqft per place
- **Source:** Place type lookup tables + building footprints (126K)

### S3: Supply Quality
- Price tier distribution (Luxury/Premium/Mid/Value/Budget)
- Brand penetration (chain vs independent ratio)
- Rating distribution (Google ratings, 50K places)
- Category diversity (Herfindahl index)
- Business age/tenure (ACRA registration dates)
- Churn rate (ACRA cessations / total)
- **Source:** Tier classification, ACRA (2M entities), Google ratings

### S4: Supply Concentration
- Competitive pressure (T2 weights from micrographs)
- Same-brand density (cannibalization risk)
- Category HHI within subzone
- Walk-time to nearest competitor
- **Source:** 42K micrographs, place data

### S5: Supply Gaps
- Peer gap: this subzone has 5 cafes, similar subzones average 12 → gap of 7
- Model gap: density model predicts 15 based on demographics → gap of 10
- Category gap: has restaurants but no cafes → category void
- Tier gap: has value F&B but no premium → tier void
- Co-location gap: high PMI between cafe+bakery, has cafes but no bakeries
- **Source:** Density model (R²=0.773), peer comparison, co-location PMI

---

## DEMAND SIGNALS

### D1: Residential Demand (who lives here)
| Signal | Source | What It Captures |
|---|---|---|
| Population | Census 2025 (332 subzones) | Base residential demand |
| Population density | Pop / area | Demand concentration |
| Age profile | Census age bands | Youth→bubble tea/QSR; elderly→clinics/hawker; working age→cafes |
| Dwelling type | HDB vs condo vs landed | Income proxy: HDB 3-room→value; condo→premium; landed→luxury |
| HDB resale price | 227K transactions | Actual purchasing power |
| Private property price | 287K transactions | High-end purchasing power |
| Household size | Census | Family demand (grocery, preschool) vs singles (cafes, bars) |
| Population trend | 2011-2025 time series | Growing→rising demand; shrinking→declining |

**Key insight:** Residential demand is always there but varies by time of day.

### D2: Worker/Commuter Demand (who works here)
| Signal | Source | What It Captures |
|---|---|---|
| Office place count | 2,775 office/workspace places | Worker population proxy |
| Office building density | Building footprints + land use | Employment density |
| MRT tap-out volume (AM peak) | LTA DataMall (need API key) | Morning arrivals = workers |
| Land use: commercial % | URA master plan | Zoned for work |
| Business registration density | ACRA (2M entities) | Company count per subzone |

**Key insight:** Worker demand is time-concentrated (lunch 11:30-2pm, after-work 5-7pm) and category-specific (cafes morning, restaurants lunch, bars after-work).

### D3: Transit/Pass-Through Demand (who passes through)
| Signal | Source | What It Captures |
|---|---|---|
| MRT station ridership | LTA (need API) | Through-traffic volume |
| Bus stop ridership | LTA (need API) | Local transit flow |
| MRT interchange status | Station metadata | Interchange = 2-3x footfall |
| Transit node centrality | Graph analysis on MRT network | How many routes pass through |
| Road traffic volume | LTA traffic counts | Drive-through demand |
| Carpark utilization | Carpark availability data | Car-based visitors |

**Key insight:** Transit demand is highest volume but lowest dwell-time. MRT commuters spend 2-5 min — they buy coffee and grab-and-go, not sit-down meals.

### D4: Visitor/Tourist Demand (who visits)
| Signal | Source | What It Captures |
|---|---|---|
| Hotel room count | 468 hotels | Tourist bed capacity |
| Hotel price tier | Tier classification | Tourist segment (budget vs luxury) |
| Tourist attraction proximity | 109 attractions | Draw-in factor |
| Shopping mall traffic | SpaceOut data | Retail visitor volume |

**Key insight:** Tourist demand is seasonal, location-clustered (Orchard, Marina Bay, Chinatown, Sentosa) and spend-heavy (3-5x locals per visit).

### D5: Event/Temporal Demand (when demand spikes)
| Signal | Source | What It Captures |
|---|---|---|
| Google Popular Times | Scrape per place | Hourly demand curve by day of week |
| Event venues nearby | Culture/entertainment places | Periodic demand spikes |
| School proximity + hours | 337 schools | 7-8am, 12-1pm, 3-4pm demand waves |
| Place of worship proximity | 2,063 religious places | Weekend/prayer time demand |
| Sports facility proximity | 6,357 fitness places | Morning/evening workout crowd |

### D6: Digital/Delivery Demand (invisible demand)
| Signal | Source | What It Captures |
|---|---|---|
| GrabFood/Foodpanda coverage | Scrape | Delivery radius = demand catchment |
| Dark kitchen locations | Places data | Pure delivery demand (no walk-in) |
| E-commerce density | ACRA e-commerce registrations | Online spending |

**Key insight:** Some demand is met digitally and never shows as footfall. Subzone with high delivery orders might look undersupplied physically but demand is served by dark kitchens 2km away.

---

## TIME-OF-DAY DEMAND PROFILES

| Time | Primary Demand | Categories |
|---|---|---|
| 6-9 AM | Commuters, students | Coffee, breakfast, convenience |
| 11:30-2 PM | Workers, residents | Lunch: hawker, restaurant, QSR |
| 2-5 PM | Shoppers, students | Bubble tea, dessert, retail |
| 5-8 PM | After-work, families | Dinner: restaurant, hawker, bars |
| 8-11 PM | Leisure | Bars, nightlife, late dining |
| Weekends | Families, tourists | Brunch, shopping, recreation |

Different categories have different temporal demand profiles. The gap for "breakfast cafe" and "dinner restaurant" in the same subzone can be completely different.

---

## THE DEMAND-SUPPLY EQUATION

```
Effective Demand = D1_residential × time_weight
                 + D2_workers × time_weight
                 + D3_transit × time_weight
                 + D4_visitors × time_weight
                 + D5_temporal_boost
                 - D6_digital_diversion

Effective Supply = S1_place_count × S2_capacity_per_place × S3_quality_weight

Gap Score = (Effective Demand - Effective Supply) / Effective Demand
```

- **Gap > 0:** Undersupplied → opportunity
- **Gap < 0:** Oversupplied → saturated
- **Gap ≈ 0:** Balanced → stable

---

## ADJUSTMENTS

### Cross-Boundary Demand Leakage
People don't respect subzone boundaries. Model needs a gravity function:
```
Demand_at_X = Local_demand_X + Σ(Demand_neighbor_Y × gravity_decay(distance_XY))
```

### Category Substitution
If no premium cafe, people either:
1. Go to next subzone (leakage)
2. Go to mid-tier cafe (downgrade substitution)
3. Go to restaurant with coffee (category substitution)
4. Don't buy (unmet demand)

Model should capture substitution elasticity.

### Temporal Variation
Gap for "breakfast cafe" and "dinner restaurant" in the same subzone can be opposite. Must compute per time period.

---

## PROXIES FOR MISSING FOOTFALL DATA

| Proxy | Formula | Source |
|---|---|---|
| Population-weighted | population × per_capita_spending_by_category | Census |
| Transit-volume | MRT_stations × avg_ridership × capture_rate (SGP avg: 17,600/station/day) | Station counts |
| Building-density | floor_area × occupancy_rate × people_per_sqm | Building footprints |
| Place-revealed | existing_supply × (1 + utilization_headroom) | Places + Popular Times |
| Peer-based | f(demographics, infrastructure, land_use) → expected supply | Density model |

---

## FRAMEWORK DIAGRAM

```
┌─────────────────────────────────────────────┐
│           DEMAND SIGNALS                     │
│                                              │
│  D1 Residential (population, income, age)    │
│  D2 Worker (offices, ACRA, land use)         │
│  D3 Transit (MRT stations, bus stops)        │
│  D4 Visitor (hotels, attractions)            │
│  D5 Temporal (popular times, events)         │
│  D6 Digital (delivery, e-commerce)           │
│                                              │
│  → Demand Vector per subzone × category ×    │
│    tier × time_of_day                        │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│           GAP ANALYSIS ENGINE                │
│                                              │
│  Gap = Demand - Supply                       │
│  Adjusted for:                               │
│    - Cross-boundary leakage (gravity model)  │
│    - Category substitution                   │
│    - Temporal variation                      │
│    - Quality/tier mismatch                   │
│                                              │
│  Output: Gap score per subzone × category ×  │
│          tier × time_period                  │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│           SUPPLY SIGNALS                     │
│                                              │
│  S1 Place count (174K places)                │
│  S2 Capacity (seats × turnover × hours)      │
│  S3 Quality (tier, rating, brand)            │
│  S4 Concentration (competitive pressure)     │
│  S5 Gaps (peer comparison, model prediction) │
│                                              │
│  → Supply Vector per subzone × category ×    │
│    tier                                      │
└─────────────────────────────────────────────┘
```

---

## WHAT WE CAN BUILD TODAY

| Component | Data Ready? | Effort |
|---|---|---|
| S1-S5 Supply signals | YES (174K places, tiers, micrographs) | 1-2 days |
| D1 Residential demand | YES (census, HDB prices, dwelling types) | 1 day |
| D2 Worker demand | PARTIAL (office counts, ACRA, land use) | 1 day |
| D3 Transit demand | PARTIAL (station counts, no ridership yet) | 0.5 day proxy, 1 day with LTA API |
| D4 Visitor demand | YES (hotels, attractions) | 0.5 day |
| D5 Temporal demand | NO (need Google Popular Times) | 2-3 days |
| D6 Digital demand | NO (need delivery platform scrape) | 2-3 days |
| Gap model (peer-based) | YES (density model, needs category split) | 2 days |
| Cross-boundary gravity | YES (adjacency graph + distances) | 1 day |
| Category substitution | PARTIAL (co-location PMI as proxy) | 1 day |

**v1 demand-supply model: ~7-10 days with existing data.**
**With footfall (LTA + Popular Times): +3-5 days, significantly better accuracy.**
