# City-Wide Multi-Agent Simulation — Singapore Implementation Plan

**Date:** 2026-03-29
**Status:** Plan — ready to build
**Reference:** `~/misc/city_simulation_plan.md` (original spec)
**Data:** 174K places, 332 subzones, 93K micrographs, 431 features, satellite imagery

---

## What We're Building

A dynamic simulation where every place and region in Singapore is an autonomous agent. The existing gap model becomes the spawn function, micrographs drive competition, and satellite data validates growth. The simulation answers: "If X changes, what cascade of openings, closings, and transformations ripple outward over N months?"

---

## Architecture: Hybrid Active Frontier

From the reference plan — most of the city runs in cheap statistical mode. Only zones near a shock or query activate full agent-level simulation.

```
┌─────────────────────────────────────────────┐
│                  CITY (L2)                   │
│         Macro shocks broadcast here          │
├─────────────────────────────────────────────┤
│                                             │
│   ┌──────────┐  ┌──────────┐  ┌─────────┐  │
│   │ ACTIVE   │  │ ACTIVE   │  │STATISTIC│  │
│   │ ZONE     │──│ ZONE     │  │AL MODE  │  │
│   │ (full    │  │ (full    │  │(region- │  │
│   │  agent   │  │  agent   │  │ level   │  │
│   │  sim)    │  │  sim)    │  │ only)   │  │
│   └──────────┘  └──────────┘  └─────────┘  │
│        ↑              ↑                     │
│   User query     Anchor shock               │
└─────────────────────────────────────────────┘
```

---

## Agent Hierarchy (SGP-specific)

### L0: Place Agents (start with ~5K branded, scale to 174K)

Each place has:
- **Identity:** from `sgp_places_v2.jsonl` (name, brand, category, place_type, price_tier, address, lat/lon)
- **Micrograph context:** from `micrograph_output_v3` (T1-T4 anchors, context vector, competitive pressure)
- **State:** revenue_band, utilization, survival_probability, age_months
- **Decisions:** SURVIVE | CLOSE | EXPAND | PIVOT
- **Sensing radius:** category-dependent (cafe 300m, restaurant 500m, gym 2km, hospital 5km)

### L1: Region Agents (332 subzones)

Each subzone has:
- **Features:** from V5 feature matrix (431 features compressed to 32-dim embedding)
- **Satellite:** from VIIRS/WorldCover (night light, built-up %, green %, development index)
- **Neighbor context:** ego-graph (55 features: mean, max, std, contrast, rank)
- **State:** vacancy_rate, avg_rent, demand_capacity per category, supply per category
- **Role:** modulates entry probability, doesn't directly control places

### L2: City Agent (singleton)

Broadcasts macro shocks:
- New MRT station opening
- Economic boom/recession
- Policy change (rezoning)
- Pandemic / emergency
- Major anchor arrival/departure

---

## Communication Channels

### Competition (Place ↔ Place, same-category)
- Uses micrograph T2 edges
- Birth/death of same-category place within sensing radius → competitive_pressure change
- **SGP data:** 93K micrographs with per-place competitor weights

### Complementary (Place ↔ Place, cross-category)
- Uses micrograph T3 edges
- Birth/death of complementary place → revenue boost/loss
- **SGP data:** co-location PMI (5,351 positive pairs, 46 negative)

### Environmental (Region ↔ Place, bidirectional)
- Region → Place: rent changes, demographic shifts, infrastructure events
- Place → Region: births/deaths aggregate into region composition, vibe embedding updates
- **SGP data:** 431 region features + 81K cross-boundary anchor flows

---

## Critical Sub-Models

### 1. Survival Function
```
survival_prob = sigmoid(
    base_rate[category][age]           # bathtub curve (high early, stable mid, late decline)
    - competition_penalty              # more same-category neighbors → lower survival
    + complementary_bonus              # more complementary neighbors → higher survival
    - region_vacancy_penalty           # declining area → lower survival
    - rent_burden_penalty              # revenue < rent → lower survival
)
```
**Calibration:** ACRA churn rate (we have this), category survival benchmarks

### 2. Spawn Function (Gap Model)
```
spawn_prob = gap_score × entry_speed[category] × region_attractiveness × (1 - saturation) × macro
```
- `gap_score` from embedding-based peer comparison (V5 model)
- `entry_speed`: cafe is fast (1 month), hospital is slow (36 months)
- `region_attractiveness`: (1 - vacancy) × infrastructure_score
- `saturation`: demand_consumed / demand_capacity

### 3. Demand Ceiling (prevents runaway spawning)
```
demand_capacity[category][region] = f(
    population_within_isochrone,
    income_distribution,
    category_spend_share,
    visit_frequency,
    per_visit_revenue,
    min_viable_revenue
)
```

### 4. Shock Propagation
- **Perturbation** (local): 1-2 hops, decays in 1-2 ticks
- **Disruption** (regional): 3-5 hops, 4-8 ticks
- **Phase transition** (city-wide): all regions, 12-24 ticks

---

## Data Inventory (what we have vs need)

### Already Available
| Data | Source | Records | Status |
|---|---|---|---|
| Place locations + categories + tiers | sgp_places_v2.jsonl | 174,711 | ✅ |
| Micrograph star-graphs | micrograph_output_v3 | 93,788 | ✅ |
| Region features (431 dims) | V5 feature matrix | 332 | ✅ |
| Region embeddings (32 dims) | V5 autoencoder | 332 | ✅ |
| Satellite imagery | VIIRS + WorldCover + WorldPop | 332 | ✅ |
| Night light temporal change | VIIRS 2022→2024 | 325 | ✅ |
| Neighbor ego-graph | Adjacency + permeability | 332 | ✅ |
| Cross-boundary flows | Micrograph anchor flows | 81K connections | ✅ |
| ACRA business survival | Churn rate, avg age | 311 subzones | ✅ |
| HDB resale prices | Transactions | 227K | ✅ |
| Co-location PMI | Category pairs | 5,397 edges | ✅ |
| Transit network | MRT + bus + interchanges | 10,896 anchors | ✅ |

### Need to Build/Source
| Data | Source | Priority | Effort |
|---|---|---|---|
| Category survival curves (SGP) | ACRA open/close dates | P0 | 2 days |
| Category spending shares (SGP) | Singstat household expenditure | P1 | 1 day |
| Foot traffic proxy | LTA ridership (need API key) | P1 | 1 day |
| Commercial rent by subzone | URA REALIS | P1 | 1 day |
| Zoning permitted categories | URA Master Plan cross-ref | P2 | 2 days |

---

## Implementation Phases

### Phase 0: Minimal Viable Simulation (3 days)
**Goal:** Prove the architecture works with a tiny subset.

**Scope:**
- 50 region agents (top 50 subzones by place count)
- ~5,000 place agents (branded places in those 50 subzones)
- Monthly ticks, 12-month horizon
- Single deterministic run (no Monte Carlo)
- Rule-based survival (simplified) + gap-model spawn
- One shock type: "new place opens"

**Deliverables:**
- `simulation/core.py` — PlaceAgent, RegionAgent, CityState dataclasses
- `simulation/engine.py` — tick loop (sense → decide → spawn → propagate)
- `simulation/survival.py` — category-parameterized survival function
- `simulation/spawn.py` — gap model integration
- `simulation/loader.py` — load from our existing data files
- Test: run 12 months, verify place count changes are reasonable

### Phase 1: Full Agent Framework (1 week)
**Goal:** Scale to all 332 regions and full place set.

- Scale to 332 region agents with full V5 feature vectors
- Scale to 174K place agents (or 93K with micrographs)
- Implement hybrid activation (active zones vs statistical mode)
- Add spatial indexing (H3 or scipy cKDTree — we already use cKDTree)
- Competition and complementary channels using micrograph edges
- Performance target: 1 tick < 5 seconds

### Phase 2: Survival Calibration (1 week)
**Goal:** Make survival probabilities realistic.

- Parse ACRA open/close dates → category survival curves for SGP
- Implement bathtub curve (age effect)
- Calibrate competition_sensitivity and complement_sensitivity
- Backtest: from 2022 state, does 12-month sim approximate 2024 reality?
- Validate against satellite: brightening subzones should have positive net births

### Phase 3: Demand Ceiling + Spawn (1 week)
**Goal:** Prevent runaway spawning, make growth realistic.

- Implement demand_capacity per category per region
- Use census population + income + spending shares
- Wire gap model (V5 embeddings) as spawn location selector
- Implement region attractiveness modulation
- Validation: spawned categories should match known developments (Tengah, Jurong)

### Phase 4: Shock System + Scenarios (1 week)
**Goal:** Enable what-if queries.

- Implement shock classification (perturbation / disruption / phase transition)
- Implement propagation decay across hops and ticks
- Scenario API:
  - `what_if_open(category, location)` → 12-month cascade
  - `what_if_close(place_id)` → 12-month cascade
  - `what_if_mrt(station_location)` → city-wide impact
- Validate: "what if MRT opens at Tengah" should match actual satellite brightening

### Phase 5: Monte Carlo + Visualization (1 week)
**Goal:** Produce distributional outputs and visual reports.

- Implement 100-run Monte Carlo ensemble
- Report confidence intervals on place counts, category distribution
- Visualization: animated heatmap of births/deaths over 12 months
- HTML report: per-scenario outcomes with Propheus theme
- Dashboard: interactive scenario builder

---

## Key Design Decisions (following reference plan)

| Decision | Choice | Reason |
|---|---|---|
| Tick granularity | Monthly | Data granularity, compute budget |
| Demand model | Explicit (pop × spend share) | Prevents runaway spawning |
| Agent decisions | Rule-based first | Simpler to calibrate, RL later |
| Stochasticity | Monte Carlo (100 runs) | Report distributions, not point estimates |
| Spatial index | scipy cKDTree | Already used in micrograph pipeline |
| Graph backend | NetworkX | Simpler for 332 nodes, PyG if scaling |
| Activation | Hybrid (active + statistical) | Essential for performance at 174K agents |

---

## What Makes SGP Simulation Unique

1. **93K micrographs** — every place knows its exact competitive landscape (not just "nearby cafes" but weighted T2 edges with walk times)
2. **V5 embedding-driven spawn** — new places are located based on 431-feature structural similarity to successful subzones
3. **Satellite calibration** — night light change 2022→2024 validates growth predictions
4. **Cross-boundary flows** — 81K anchor connections model real demand leakage between subzones
5. **ACRA survival data** — Singapore-specific business mortality rates
6. **Neighbor ego-graph** — contrast features directly tell if a subzone is over/under-supplied vs neighbors

---

## Timeline

| Phase | What | Duration | Cumulative |
|---|---|---|---|
| Phase 0 | Minimal viable (50 regions, 5K places) | 3 days | 3 days |
| Phase 1 | Full agent framework (332 regions, 174K places) | 1 week | 10 days |
| Phase 2 | Survival calibration + backtest | 1 week | 17 days |
| Phase 3 | Demand ceiling + spawn | 1 week | 24 days |
| Phase 4 | Shock system + scenarios | 1 week | 31 days |
| Phase 5 | Monte Carlo + visualization | 1 week | 38 days |

**Total: ~5-6 weeks for a production-quality city simulation.**
**Phase 0 alone (3 days) proves the concept.**
