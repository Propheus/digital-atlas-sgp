# Digital Atlas SGP — Ideation: From NYC to Singapore

## What NYC Atlas Does (Current)

The NYC Digital Atlas v2 is a **9-layer storytelling map** that progressively reveals urban structure:

1. **Who Lives Here** — Population, density, age, diversity
2. **What They Earn** — Income, rent, poverty
3. **How They Live** — Renters, vacancies, commute, cars
4. **How They Move** — Subway, bus, bike (MTA ridership)
5. **What's Built** — Buildings, heights, density (PLUTO)
6. **How Safe It Is** — Crime counts and rates
7. **What's There** — 253K places, category entropy
8. **What's Demanded** — Effective demand by time of day
9. **Where It Flows** — Gravity model, trade areas, cross-tract flows

For each place (cafe, QSR, grocery, restaurant), it computes:
- Micro-graph: nearby competitors, complementary places, anchors
- Walk/drive routing via OSM
- Tier classification (T1-T4)
- Location quality score
- Gap analysis

---

## What Makes SGP Different From NYC

### 1. Singapore is government-planned, NYC is market-evolved
- URA Master Plan literally dictates what can go where
- HDB (80% of housing) is government-built
- Land use is not emergent — it's designed
- **Implication:** Zoning IS the story. Show the master plan layer prominently.

### 2. Singapore is small and dense, NYC is sprawling
- 785 km² vs 783 km² (nearly same area!)
- But SGP has 332 subzones vs NYC's 2,327 tracts
- Every point in SGP is within 1km of MRT or bus
- **Implication:** Transit accessibility is universal. The differentiator is QUALITY of transit, not presence.

### 3. Singapore has hawker culture, NYC has bodegas
- 129 hawker centres are government-managed food infrastructure
- Eating at hawkers is a national identity, not just convenience
- Food court + hawker + coffeeshop form a distinct food ecosystem
- **Implication:** F&B layer needs SGP-specific taxonomy. "Hawker stall" is not "fast food."

### 4. Singapore is multi-ethnic with spatial patterns
- Chinese, Malay, Indian, Others — each with distinct place preferences
- Ethnic enclaves (Little India, Kampong Glam, Chinatown) are preserved by design
- Religious buildings (temples, mosques, churches) cluster by community
- **Implication:** Ethnicity layer becomes a powerful composition predictor.

### 5. Singapore has no crime data but has safety perception
- Crime is extremely low — not a differentiator
- No public crime data at subzone level
- **Implication:** Drop the safety layer. Replace with something SGP-specific.

### 6. HDB resale market is the economic heartbeat
- 80% live in HDB
- Resale prices vary 2x across the island
- Price = strongest affluence signal at subzone level
- **Implication:** HDB price layer is more impactful than income (which is only at planning area level).

---

## SGP Atlas: Proposed Layers

### Act I: The People

**Layer 1: "Who Lives Here"**
- Population, density per subzone
- Age pyramid: young families vs elderly vs working age
- Dependency ratio
- SGP-specific: Show HDB block density as physical population proxy
- Color: population density choropleth

**Layer 2: "How They Live"**
- Dwelling type mix: HDB 1-2rm → 5rm → condo → landed
- This IS the income proxy in SGP
- HDB resale PSF (strongest affluence signal)
- Year-on-year price trend (growing vs declining areas)
- Color: HDB PSF gradient

**Layer 3: "Who Their Neighbors Are"**
- Ethnic composition: Chinese, Malay, Indian, Others %
- Religious diversity index
- Language diversity proxy (from school type distribution)
- SGP-specific: Highlight the ethnic enclaves
- Color: diversity index or dominant ethnicity

### Act II: The Infrastructure

**Layer 4: "How It's Zoned"**
- Master Plan land use (THE most important SGP layer)
- Residential vs commercial vs industrial vs mixed
- GPR (development intensity allowed)
- Land use entropy (mixed-use score)
- Show the URA zones as the skeleton of the city
- Color: land use type

**Layer 5: "How They Move"**
- MRT/LRT network with station catchments (500m, 1km)
- Bus stop density
- EV charging density (future mobility)
- Distance to nearest MRT (the #1 transit metric)
- SGP-specific: Show MRT lines overlaid, station names
- Color: transit accessibility score

**Layer 6: "What's Built"**
- Building footprints from OSM (125K)
- HDB blocks (13K) with age/floor count
- Building density and height proxy
- Road network density and type
- Color: built density

### Act III: The Places

**Layer 7: "What's There"**
- 66,851 curated places
- 24 categories, 165 place types
- Category entropy per subzone (diversity of place mix)
- Place density per km²
- Scatter plot of all places colored by category
- Click any place → full details (rating, phone, brand)

**Layer 8: "Who Owns It"**
- 232 brands mapped
- Chain vs independent ratio per subzone
- Brand concentration (HHI index)
- Luxury places highlighted
- SGP-specific: Show 7-Eleven density, FairPrice coverage, hawker centre distribution
- Click subzone → brand breakdown pie chart

**Layer 9: "The Food Map"**
- SGP-specific layer — food is identity
- Hawker stalls (2,462) + hawker centres (129) + food courts (410)
- Cafes (3,303) + coffee shops
- Restaurants by cuisine (Chinese, Japanese, Indian, Malay, Western...)
- QSR + bubble tea + bakeries
- Show the food desert metric: subzones with low food accessibility
- Color: F&B density with hawker centre markers

### Act IV: The Gaps

**Layer 10: "What's Expected"**
- Model prediction: expected total place count per subzone
- Shows what the physical structure SHOULD support
- Based on density model (R²=0.77)
- Color: predicted density

**Layer 11: "What's Missing"**
- Gap = predicted - actual per subzone
- Positive gap highlighted in warm colors (opportunity)
- Negative gap in cool colors (saturated)
- Click subzone → breakdown by category gaps
- SGP-specific: Cross-reference with SFA (34K eating establishments), CHAS (1.2K clinics), ECDA preschools

**Layer 12: "The Ground Truth"**
- ACRA registered entities (2M) vs our places (67K)
- Coverage ratio per subzone
- Government facility counts vs our counts
- Data confidence score per subzone
- This is the honesty layer — shows where we know vs where we guess

---

## SGP-Specific Features (Not in NYC Version)

### 1. HDB Estate Profiler
Click any HDB town → show:
- Population age distribution
- Dwelling type mix
- Resale price trends (sparkline from 226K transactions)
- Place composition vs similar towns
- "This town is aging — more elderly care needed"

### 2. Hawker Centre Atlas
All 129 hawker centres as a dedicated view:
- Each centre with stall count, distance to nearest MRT
- Catchment analysis: population within 500m
- Food desert detection: residential areas >1km from any hawker
- Compare: government hawker vs commercial food court coverage

### 3. Master Plan Overlay
Toggle URA Master Plan zoning:
- See exactly what each parcel is zoned for
- GPR limits → how much more can be built
- White sites (flexible zoning) as opportunity zones
- Upcoming government land sales overlaid

### 4. Ethnic Composition Storyteller
Click any subzone → see:
- Ethnic breakdown with historical comparison
- Nearby religious facilities by type
- Food places by cuisine mapped to ethnicity
- "Little India has 5x the Indian restaurant density of island average"

### 5. Brand Penetration Map
Select a brand (e.g., "Starbucks") → see:
- All 50 locations on map
- Subzones with brand present vs absent
- Predicted vs actual → where should next outlet be?
- Competitor proximity analysis (Coffee Bean, Flash Coffee nearby?)

### 6. New Town Readiness Score
For developing areas (Tengah, Bayshore, Bidadari):
- Current place count vs projected population
- What's planned (from master plan)
- Gap: what categories need to come first?
- Timeline: which places typically arrive first in new towns?

---

## Interaction Design Differences

### NYC: Dense, busy, data-heavy
The NYC app works because 2,327 tracts give smooth choropleth gradients and 253K places give rich scatter plots.

### SGP: Smaller, more intimate, more narrative
332 subzones = coarser grain. Need to:
- **Zoom into subzones** more aggressively — show individual buildings and places
- **Tell stories per subzone** — "Aljunied: 1,808 places, 42K residents, most diverse food scene"
- **Compare subzones** — side-by-side panel: "Orchard vs Geylang vs Jurong"
- **Use the HDB blocks** as visual anchors — 13K building polygons give the map texture
- **Overlay MRT lines** as the visual spine of the city

### SGP-Specific UI Patterns

**"Neighborhood DNA" Card**
For each subzone, a radar chart showing:
```
        F&B ●
       /    \
Retail ●      ● Services
       \    /
     Transit ●
```
Instant visual of what this neighborhood IS.

**"Missing Pieces" Widget**
When clicking a subzone:
```
┌──────────────────────────────┐
│ ALJUNIED                     │
│ 1,808 places | 42K pop      │
├──────────────────────────────┤
│ ✅ F&B: 416 (above expected) │
│ ✅ Retail: 350 (on track)    │
│ ⚠️  Cafe: 51 (below by 12)  │
│ ❌ Gym: 8 (expected 14)      │
│ ❌ Clinic: 3 (expected 7)    │
└──────────────────────────────┘
```

**"Time Machine" Slider**
If we get two timepoints:
- Slide between 2020 → 2025
- Watch areas grow/decline
- New MRT stations → see composition shift

---

## Data Pipeline: NYC → SGP Mapping

| NYC Data | SGP Equivalent | Status |
|----------|---------------|--------|
| Census tracts (2,327) | Subzones (332) | ✅ Ready |
| ACS demographics | Singstat pop by subzone (2025) | ✅ Ready |
| MTA ridership | LTA passenger volume | ❌ Need API key |
| PLUTO (lots) | Master Plan land use (113K parcels) | ✅ Ready |
| Building footprints | OSM buildings (125K) + HDB (13K) | ✅ Ready |
| Crime data | N/A (replace with something else) | N/A |
| 253K Google places | 66,851 curated places | ✅ Ready |
| Income by tract | HDB resale PSF by subzone | ✅ Ready |
| Gravity model | Not built yet | ❌ Need to compute |
| Demand model | Not built yet | ❌ Need foot traffic |

### What We Can Ship Today (v1)
Layers 1-9 + 10-11 are buildable from existing data. Layer 12 is buildable from ACRA cross-reference.

### What Needs More Data (v2)
- Demand layer (needs MRT passenger volume)
- Gravity/flow model (needs OD matrix)
- Time machine (needs historical snapshot)

---

## Impact: Why SGP Atlas > NYC Atlas

### 1. Singapore actually uses data for planning
NYC atlas is interesting but the city doesn't centrally plan. SGP does. The URA, HDB, and LTA actively make decisions about where to zone, where to build, what to allow. An atlas that shows gaps IS actionable here.

### 2. The data is cleaner and more complete
Government data quality in SGP is exceptional. Master Plan is comprehensive. Census is at subzone level. Transit is well-documented. We don't have the data fragmentation problem of US cities.

### 3. The market is concentrated
SGP is one city, one government, one market. A gap identified in Tampines West can be acted on. In NYC, each borough is practically a different city.

### 4. F&B is a $15B industry in SGP
Food is the #1 spending category. Hawker centres are a UNESCO heritage item. An atlas that helps understand food infrastructure has immediate commercial and policy value.

### 5. New towns are being built RIGHT NOW
Tengah, Bayshore, Great Southern Waterfront — major new developments. An atlas that predicts what these areas need is immediately useful for developers, retailers, and government planners.

---

*Ideation date: 2026-03-19*
