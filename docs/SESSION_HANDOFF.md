# Session Handoff — SGP Digital Atlas
## Everything needed to continue development

**Date:** 2026-04-21  
**Session scope:** Built the complete SGP Digital Atlas from scratch, validated, deployed to 3 servers, audited the Merlion engine.  
**Next session:** Build the app (rename engine to Nous or Thesis — user deciding)

---

## 1. What Exists Right Now

### Data (on local + atlas-1 + atlas-deploy, all synced)

| Asset | Path | Shape |
|---|---|---|
| Hex-9 features | `data/hex_v10/hex9_final.parquet` | 7,318 × 603 |
| Hex-8 features | `data/hex_v10/hex8_final.parquet` | 1,191 × 628 |
| Hex-9 JSON | `data/hex_v10/hex9_features.json` | 126 MB |
| Hex-8 JSON | `data/hex_v10/hex8_features.json` | 22 MB |
| Places | `data/places_consolidated/sgp_places_featured.parquet` | 174,711 × 114 |
| Subzone | `data/features/subzone_features_full.json` | 326 × ~449 |
| Places source | `data/places_consolidated/sgp_places_v2.jsonl` | 174,711 raw |
| GTFS | `data/gtfs/singapore-gtfs.zip` | 230K trips |
| Buildings | `data/buildings_overture/sgp_buildings_fused.parquet` | 377K |
| Roads | `data/roads/roads.geojson` | 551K segments |
| All amenities | `data/amenities/` | hawkers, clinics, parks, supermarkets, hotels, schools |
| All transit | `data/transit/` + `data/transit_updated/` | stations, bus stops |
| Demographics | `data/demographics/` | pop by age, dwelling type |

### Code

| Component | Path | What it does |
|---|---|---|
| **Merlion package** | `merlion/` | Core engine: intent parsing, use case routing, model execution |
| **Merlion API** | `merlion-app/backend/server.py` | FastAPI on :18700 |
| **Merlion UI** | `merlion-app/frontend/` | Next.js on :18701 ("Real World Engine") |
| **Hex adequacy app** | `apps/hex-adequacy/` | React + Mapbox GL on :16789 |
| **Subzone explorer** | `app/` | React + Deck.gl on :18067 |
| **Scenario sim** | `scenario_sim/` | Gravity model + web UI on :18070 |
| **Feature pipelines** | `scripts/representation_v1/v10/` | 40+ scripts building hex features |
| **Micrograph pipeline** | `micrograph_pipeline/` | Per-category context vectors |
| **Place enrichment** | `scripts/place_enrichment.py` | 114-feature place pipeline (on atlas-1) |
| **Satellite enrichment** | `scripts/enrich_satellite.py` | VIIRS + WorldPop + archetypes (on atlas-1) |

### Servers

| Server | IP | Role | What's running |
|---|---|---|---|
| **Local** (Mac) | — | Development | Merlion API :18700, UI :18701 |
| **atlas-1** | 10.2.2.5 | Processing | hex-adequacy :16789, sgp-atlas :18067, scenario-sim :18070, merlion :18700/18701 |
| **atlas-deploy** | 10.2.2.7 | App deployment | Clean setup: Python 3.12, Node 20, all data, DuckDB <7ms, 237GB free |

### Repo
- **GitHub:** `Propheus/digital-atlas-sgp` (needs to be made private — user lacks admin on org)
- **Branch:** `main`, latest commit: `85ad6e1 v2.0: Multi-resolution feature stack + place representation`

---

## 2. Merlion Engine Audit (54% pass rate)

### What works
- **Intent routing:** 84% correct (NL → use case classification is solid)
- **15-minute city:** 5/5 correct (Outram, Rochor — mature walkable areas)
- **Comparable market:** 3/5 correct (Orchard → Newton, Tanjong Pagar → Downtown Core)
- **Branded site selection:** Starbucks → CBD, FairPrice → HDB estates (correct)

### What's broken
1. **Food deserts return Orchard/CBD** — scores by absolute gap, not per-capita need
2. **Generic site selection returns SAME hexes for all categories** — no differentiation between gym vs cafe vs luxury restaurant (all return Rochor, Kallang, Geylang)
3. **3 handlers return empty:** category_prediction, archetype_clustering, feature_query
4. **Gap analysis returns already-oversaturated areas** — XGBoost predicts highest counts where features are highest

### Root cause
Engine uses **old hex-9 v10 features (471 columns)**. Our enriched stack has saturation, demand pull, total population, archetypes, GTFS, network walk — none of it is wired in.

### Priority fixes
1. Wire hex-8 (628 features) into handlers — saturation, demand pull, population_total
2. Category-aware site selection using demand-match lookup table
3. Fix 3 broken handlers (archetype → precomputed, feature_query → DuckDB, category_prediction → location resolver)
4. Amenity desert: score by `gap / population_total`, filter to pop > 5K

Full audit: `docs/MERLION_ENGINE_AUDIT.md`

---

## 3. Feature Architecture (for building the app)

### Hex-8 feature pillars (628 features)

| Pillar | Count | Key columns |
|---|---|---|
| Demographics | 18 | population, population_total (5.98M), pct_elderly, nonresident_share, daytime_intensity |
| Dwelling type pop | 12 | pop_tod_hdb_4_room_flats, pop_tod_condominiums, etc. |
| Built environment | 16 | bldg_count, hdb_blocks, avg_floors, commercial_floor_area |
| Land use | 12 | lu_residential_pct, lu_entropy, dominant_use, lu_fragmentation |
| Transit | 18 | mrt_stations, bus_stops, transit_daily_taps, temporal splits (AM/PM/off/night) |
| GTFS frequency | 8 | gtfs_headway_am_min, gtfs_routes_served, gtfs_frequency_score |
| Walkability | 26 | walk_mrt_m (Euclidean), nwalk_mrt_m (network), detour ratios, composites |
| Amenities | 16 | hawker_centres, clinics, parks, supermarkets, hotels, schools |
| Place composition | 79 | 24 categories (count + %), entropy, HHI, price tiers, brands |
| Demand pull | 12 | pull_office, pull_residential, pull_transit, pull_hotel, pull_school, pull_hawker + pctls |
| Synergy | 20 | 10 co-location scores + percentiles |
| Saturation | 13 | saturation_restaurant/cafe/convenience/health/fnb + gap_* + composite |
| Satellite | 12 | nl_2022, nl_2024, nl_change_pct, nl_commercial_indicator, worldpop, worldcover |
| Archetype | 3 | archetype (6 types), archetype_id, archetype_confidence |
| Composites | 8 | idx_vitality, idx_accessibility, idx_demand, idx_growth_potential, idx_urban_intensity, etc. |
| Proxies | 4 | proxy_daytime_pop, proxy_footfall, proxy_tourism, proxy_night_economy |
| Structure | 8 | interface_score, gradient_position, net_demand_flow, ecosystem_completeness |
| Spatial context | 123 | sp_max_*, sp_pw_*, tr_max_*, tr_pw_* (ring aggregates) |
| Micrograph | 156 | 12 categories × 13 features (context vectors, density bands) |
| Property | 2 | hdb_median_psf, hdb_txn_count |
| Other | 6 | osm_amenities, osm_leisure, osm_shops, osm_tourism, park_connector, ev_charging |

### Place feature pillars (114 features)

| Pillar | Count | Key columns |
|---|---|---|
| Identity | 14 | name, category (24 types), price_tier, is_branded, h3_res9, h3_res8 |
| Competition | 5 | competitors_200m/500m, nearest_competitor_m, market_share_proxy, substitution_risk |
| Complementary | 5 | diversity, total_places_300m, fnb_300m, retail_300m, score |
| Anchor | 19 | 14 types × (count + distance): mrt, bus, hawker, clinic, park, supermarket, hotel, school, tourist, library, sports, worship, community, university |
| Demand pull | 8 | pull_office/residential/transit/hotel/school/hawker/total_pop + demand_context_score |
| Synergy | 10 | Target-category-only: cafe_office, grocery_residential, conv_transit, etc. |
| Transit | 8 | nwalk_mrt_m, nwalk_bus_m, gtfs_headway, routes, transit_score |
| Catchment | 5 | pop, elderly, nonresident, nonres_share, daytime |
| Building | 8 | bldg_count, floors, hdb_blocks, land use from hex |
| Neighborhood | 8+ | char_archetype, idx_vitality, idx_demand, nl_radiance, char_hdb_psf |
| Supply-demand | 5 | saturation_own_category, gap_own_category, demand_match, survivability_index |
| Composite | 1 | context_score |

### Demand-match lookup (for category-aware scoring)

| Category | Primary pull (weight) | Secondary pull |
|---|---|---|
| Cafe & Coffee | pull_office (0.6) | pull_transit (0.4) |
| Restaurant | pull_residential (0.5) | pull_hotel (0.5) |
| Fast Food / QSR | pull_transit (0.6) | pull_residential (0.4) |
| Convenience | pull_transit (0.7) | pull_residential (0.3) |
| Health & Medical | pull_residential (1.0) | — |
| Education | pull_school (0.6) | pull_residential (0.4) |
| Beauty | pull_residential (0.6) | pull_office (0.4) |
| Bar & Nightlife | pull_hotel (0.5) | pull_office (0.5) |
| Shopping & Retail | pull_transit (0.5) | pull_hotel (0.5) |
| Fitness | pull_residential (0.6) | pull_office (0.4) |
| Hawker | pull_residential (0.6) | pull_transit (0.4) |
| Bakery | pull_transit (0.5) | pull_residential (0.5) |
| Supermarket | pull_residential (1.0) | — |

### Archetype types (hex-8, K-means k=6)

| Archetype | Count | Character |
|---|---|---|
| Green/Institutional | 475 | Parks, reserves, military, open space |
| Mixed (2 clusters) | 432 | Transitional areas, mixed use |
| Mature HDB | 131 | Established estates (Toa Payoh, Ang Mo Kio, Bedok) |
| Dense HDB | 119 | High-population new towns (Sengkang, Woodlands, Jurong West) |
| Tourist/Commercial | 34 | CBD, Orchard, Marina, Sentosa |

---

## 4. Key Numbers

| Metric | Value |
|---|---|
| Population (resident) | 4,212,320 |
| Population (total) | 5,982,320 |
| Non-residents | 1,770,000 |
| Places | 174,711 |
| Buildings | 377,331 |
| MRT stations | 187 (+44 LRT) |
| Bus stops | 5,172 |
| Daily transit taps | 12,279,205 |
| GTFS trips | 230,914 |
| Road segments | 550,991 |
| Pedestrian graph nodes | 213,978 |
| DuckDB query time | <7ms |
| Total features across levels | ~1,794 |

---

## 5. Documentation Index

| Doc | What it covers |
|---|---|
| `docs/SGP_DIGITAL_ATLAS_CONTEXT.md` | **Complete context** — features, levels, sources, gaps, everything |
| `docs/SGP_DIGITAL_ATLAS_METHODOLOGY.md` | How it was built, aggregation logic, usage examples |
| `docs/UNIFIED_PLACE_REPRESENTATION.md` | Place pipeline design (ported from HKG) |
| `docs/PLACE_REPRESENTATION_PLAN.md` | Original place ideation |
| `docs/LLM_MOE_SPATIAL_EXPERT_IDEATION.md` | MoE training idea — "what am I / where am I" corpus |
| `docs/MERLION_ENGINE_AUDIT.md` | 50-test audit with root causes and fix plan |
| `CLAUDE.md` | Project context for Claude sessions |
| `CONTEXT.md` | Server + data catalog |
| `transport_gaps_validated.html` | Transport claim validation against raw LTA data |
| `transport_adequacy_app_ideation.html` | Transport app design |

---

## 6. Naming Decision Pending

Engine rename from "Real World Engine" to:
- **Nous** (νοῦς) — "mind, direct understanding" — 4 letters, punchier
- **Thesis** (θέσις) — "a placing, a proposition" — 6 letters, more advisory tone

User is deciding. Update `merlion-app/frontend/src/app/page.js` and `merlion-app/backend/server.py` when chosen.

---

## 7. What to Build Next

### Immediate (app development)
1. **Rename engine** (Nous or Thesis)
2. **Wire enriched hex-8 features** into Merlion handlers (fix the 54% → 90%+ pass rate)
3. **Atlas API** on atlas-deploy — DuckDB-backed, serves hex/place features (script written but not deployed, was blocked by server being down)
4. **New app UI** — build on atlas-deploy with the enriched data

### Medium-term
5. **Transport adequacy gap report** — segment-conditioned (seniors, commuters, tourists, school kids)
6. **LLM MoE corpus generation** — "what am I / where am I" for 183K entities
7. **Place embeddings** — PCA/autoencoder on 96 numeric place features → 32-64d vectors

### Stretch
8. **Cross-city benchmarking** — SGP vs NYC/Chicago/LA via atlas datarepo
9. **GHSL multi-epoch** — download correct equatorial tile for SGP
10. **Interactive scenario simulation** — "what if we add a station at X?"

---

*Handoff v1.0 — 2026-04-21*  
*This document contains everything needed to continue in a new session.*
