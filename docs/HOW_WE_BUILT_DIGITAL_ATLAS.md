# How the Digital Atlas SGP Was Built — Enumerated

**Date:** 2026-04-23
**Scope:** Full build chain from raw data to deployed apps, stage by stage.

---

## Stage 0 — Raw data collection (14 sources, 5.7 GB)

Landed in `data/`:

- **Places:** Overture 2025 (147K) + OSM POIs + SFA → dedupe → consolidate → `sgp_places_v2.jsonl` (**174,713**)
- **Buildings:** Overture (377K) + HDB authoritative (13,386 blocks) + OSM → `sgp_buildings_fused.parquet`
- **Boundaries:** URA subzones (332) + planning areas (55)
- **Transit:** LTA station register (231 MRT + 44 LRT), bus stops (5,177), rail lines, MRT exits, LTA live (ridership, PV, traffic signals, carpark, taxi)
- **Roads:** OSM (550,991 segments)
- **Land use:** URA Master Plan (113,212 parcels)
- **Demographics:** SingStat `pop_age_sex_tod_2025`, `dwellings_subzone_2025`
- **Property:** HDB resale (227K), private resi (287K)
- **Amenities:** SFA eating (34K), CHAS clinics (1,193), preschools (2,290), hawker centres (129), parks (450), park connector (883), supermarkets (526), schools (337), hotels (468)
- **Business:** ACRA entities (2.08M)
- **Personas:** NVIDIA 148K personas
- **Satellite:** VIIRS night lights 2022→2024, WorldPop, WorldCover
- **GTFS:** Singapore 2026 (230K trips, 602 routes)

---

## Stage 1 — Place consolidation (`data/places_consolidated/`)

1. Ingest Overture + OSM → `sgp_places_consolidated.jsonl`
2. Dedupe (geohash + name similarity) → `sgp_places_clean.jsonl`
3. **LLM classification** (Gemini 2.0 Flash): 53,584 unclassified places → 24-category taxonomy → `llm_classified.jsonl`
4. Enrich (brand linking via 233 brand taxonomy) → `sgp_places_enriched.jsonl`
5. Final master → `sgp_places_v2.jsonl` (**174,713 × 18 cols**)

---

## Stage 2 — V1 subzone pipeline (legacy, `scripts/step_*`)

19-step pipeline (`docs/PROCESSING_PLAN.md`) — demographics → property → roads → buildings → land use → transit → place composition → brand/quality → validation → amenity → graphs → merge. Output: `subzone_features_raw.parquet` (332 × 205), evolved into V8 table (332 × 243).

---

## Stage 3 — V7 gap model + V5/V6 embeddings (subzone-level)

- `atlas_model_v1..v5.py` — iterative subzone gap analysis (4th-root transform, R²=0.755)
- `model/embeddings_v5/` — 431 features → **32-dim autoencoder** (separation 0.720)
- `model/embeddings_v6/` — V5 + personas → 32-dim (+9.5% lift)
- Reports: `CATEGORY_INTELLIGENCE.html`, `V8_FEATURE_REPORT.html`, `FEATURE_INVENTORY.html`

---

## Stage 4 — Hex-9 v9 intermediate (5,897 hexes × 154 features)

`data/hex_v9/` — first hex-level attempt. Superseded by v10.

---

## Stage 5 — Hex v10: the authoritative stack (`scripts/representation_v1/v10/`)

Built as 12 pillars merged into one matrix. Run order:

1. `build_hex_v10_universe.py` — define the 7,318 hex-9 / 1,191 hex-8 universe
2. `build_hex_v10_population.py` — dasymetric allocation (SingStat → hex via Overture building weights)
3. `build_hex_v10_buildings.py` — 377K Overture+OSM+HDB fused, counts/floors/FAR per hex
4. `build_hex_v10_land_use.py` — URA parcels tessellated, 12 land-use features + entropy
5. `build_hex_v10_place_composition.py` — 174K places → 24-category counts + % + brand + price tier
6. `build_hex_v10_amenities.py` — MRT/bus/hawker/clinic/park/supermarket/hotel/school per hex
7. `build_hex_v10_hdb_prices.py` — HDB resale $/psf mapped by planning area
8. `build_hex_v10_personas.py` — NVIDIA persona features by subzone → hex
9. `build_hex_v10_rings.py` — ring-1/ring-2 neighbor aggregates (123 spatial-context features)
10. `build_hex_v10_micrograph.py` — 12 category context vectors × 13 features = **156 micrograph features**
11. `build_hex_v10_influence.py` — `interface_score`, `gradient_position`, `net_demand_flow` (no broadcast leakage)
12. `build_hex_v10_merge.py` → `hex_features_v10.parquet`
13. `normalize_hex_v10.py` → `hex_features_v10_normalized.parquet` (sqrt-rule + z-score)
14. `build_hex_v10_final.py` → `hex9_final.parquet` (**7,318 × 613**) + `hex8_final.parquet` (**1,191 × 638**) with demand pull computed natively at each resolution (decay λ differs per resolution)

**Validation:** 33 checks, 32 PASS (`data/hex_v10/hex_v10_validation_report.md`). Place/population/MRT/hawker/hotel/HDB totals conserved; 8/8 named-landmark spot checks (VivoCity, MBS, ION, Raffles Pl, Changi T1, Sentosa, NUS, Jurong Island).

---

## Stage 6 — Place featurization (`scripts/place_enrichment.py`, on atlas-1)

For each of 174,711 places, compute **114 features** across 11 pillars:

- Identity (14) · Competition (5, KD-tree) · Complementary (5, single batched ball-tree query) · Anchor proximity (19, 9 anchor types × count+dist) · Demand pull (8, from hex) · **Synergy (10, fires only on target category)** · Transit (8, includes network walk + GTFS headway) · Catchment (5) · Building (8) · Neighborhood char (8) · Supply-demand fit (5, includes `survivability_index`) · Composite (1)

Output: `sgp_places_featured.parquet` (174,711 × 114). 11-check validation, 10 pass.

---

## Stage 7 — Plexis relational graph (`scripts/build_plexis.py`, `data/plexis/`)

The core intelligence asset — a heterogeneous relational knowledge graph built on top of the hex-v10 + place-featured stack. **This is a standalone artifact**, queryable without any neural model.

- **Nodes (195,756 total):** 174,711 places · 7,318 hex-9 · 1,191 hex-8 · category/archetype meta-nodes
- **Edges (1,485,547):** **39 typed relations**
- **Output:** `plexis_triplets_v2.parquet` (head, relation, tail, + 12 edge attributes: type, ring, distance_m, anchor_type, gap, saturation, category, archetype, roads, change, from, to)

**Relation families:**

| Family | Relations | Count |
|---|---|---|
| Structural | LOCATED_IN · PARENT_OF · PART_OF · IS_A · ADJACENT_TO · SERVES | 390K |
| Commercial | COMPETES_WITH · SYNERGIZES_WITH · SUBSTITUTES_FOR · ANCHORED_BY | 1,024K |
| Spatial context | WALK_CATCHMENT · SAME_CLUSTER · SAME_CORRIDOR · COMMERCIAL_GRADIENT · HEIGHT_GRADIENT · DENSITY_GRADIENT · PRICE_GRADIENT · LU_TRANSITION · EXIT_FRONTAGE · DEVELOPMENT_FRONT · CONNECTS_TO · ROAD_CONNECTED | 28K |
| Directional | NORTH_OF · SOUTH_OF · EAST_OF · WEST_OF | 3.3K |
| Transport | FEEDS_INTO · EXPRESSWAY_CORRIDOR · EXPRESSWAY_CONNECTED · BUS_CORRIDOR | 2.8K |
| Supply/demand | UNDERSUPPLIED · OVERSUPPLIED · WORKER_INFLOW · DEMAND_LEAKS_TO | 2.6K |
| Comparable | COMPARABLE_TO · SYNERGY_PAIR · SUBSTITUTES | 2.7K |
| SGP-specific | VOID_DECK_OF (21,690 HDB ground-floor) · COASTAL (83) | 22K |

**Direct uses of the graph (no embedding required):**
- Path queries (A → SYNERGIZES_WITH → X → SAME_CLUSTER → B)
- Relation-filtered neighborhood extraction (all WALK_CATCHMENT of a hex)
- Subgraph analytics (UNDERSUPPLIED ∩ SAME_CORRIDOR for expansion targeting)
- Evidence traversal for LLM explanations

## Stage 7b — Plexis-Embed: GNN over the graph (`scripts/plexis_v3.py`, `plexis_v6.py`)

Optional downstream layer — a **GAT-R-GCN** (not a plain GNN: 4-layer, 4-head GAT with relational message passing) trained on the Plexis graph to produce dense vectors.

- **Architecture:** 4-layer GAT-R-GCN, 192 hidden dim, two heads (128d spatial + 128d commercial = **256d full embedding**), 364,711 parameters
- **Input features:** 64d PCA init (32d place + 32d hex, raw)
- **Training:** 200 epochs with early stopping (patience=30), cosine LR 1e-3 → 1e-5, multi-task loss: 0.10 link + 0.15 contrastive + 0.35 category + 0.40 regression (15 regression targets)
- **Output:** `plexis_v6_embeddings.npz` (250 MB) — 256d per node for 174,711 places, 7,318 hex-9, 1,191 hex-8
- **Metrics:** category accuracy 78.1% · walkability R² 0.921 · pull_residential R² 0.920/0.938 (hex/place) · anchor_score R² 0.909 · survivability R² 0.513

## Stage 7c — Other embedding baselines

- `build_baselines_node2vec_umap_transformer.py` → 64-dim (node2vec, UMAP, transformer)
- `gcn_masked_hex.py` + `gcn_dim_sweep.py` → GCN 64-dim on hex influence subgraph
- `gcn64_continuous_engine.py` — continuous training loop (atlas-1)
- `xgboost_masked_hex.py` → per-category predictors (24 categories)
- `build_place2vec.py` / `build_place2vec_v2.py` → place-level vectors + evaluation
- `build_serving_bundle.py` + `build_shareable_bundle.py` → 93-col shareable parquet/CSV

---

## Stage 8 — Micrograph pipeline (`micrograph_pipeline/`)

- V2 pipeline (`run_cafe_v2.py`) — quality anchors (MRT only for T1, 10+ reviews for competitors, 30+ for demand magnets) across 12 categories → 650 MB output
- V3 pipeline (`compute_micrograph_v3_on_server.py`) — covers all **174K places**, 1.6 GB output

---

## Stage 9 — Scenario simulator (`scenario_sim/`)

332 subzone agents + Huff gravity model + logsum welfare. 3 scenario knobs: new transit link / add CHAS clinic / add FairPrice. Rebuilt from source, not minified-patched.

---

## Stage 10 — Merlion engine (`merlion/`, `merlion-app/`)

- `merlion/intent/` — NL → use case routing (rule-based + LLM entities, 84% correct)
- `merlion/resolver.py` — entity resolver (brand, category, location)
- `merlion/use_cases/` — 9 registered: `site_selection`, `gap_analysis`, `archetype_clustering`, `comparable_market`, `whitespace_analysis`, `category_prediction`, `feature_query`, `amenity_desert`, `fifteen_minute_city`
- `merlion/models/` — node2vec, GCN, UMAP, transformer, xgboost, raw_features, bundle, graph
- `merlion/explain.py` — per-result LLM explanations
- FastAPI backend on :18700 + Next.js UI on :18701 (atlas-1)

---

## Stage 11 — Apps & reports

- **Hex Adequacy Explorer** (:16789) — static hex map, 10 metrics, 332 subzone profiles, transit gap report
- **SGP Atlas Subzone Explorer** (:18067) — React 19 + Vite + Mapbox + Deck.gl + Framer Motion + Zustand
- **Scenario Sim** (:18070)
- **Merlion / RWE** (:18700 + :18701)
- Tabbed insights report: `satellite_insights.html` (7 tabs: Satellite View · Gap Opportunities · Subzone Twins · Space × Model · Model Deep Dive · Data Sources · Satellite Uplift)
- Standalone: `CATEGORY_INTELLIGENCE.html`, `V8_FEATURE_REPORT.html`, `FAIRPRICE_ADEQUACY.html`, `HEX_FEATURE_REPORT.html`, `NIGHT_LIGHT_GROWTH.html`, `DEEP_ANOMALIES.html`

---

## Stage 12 — Infra migration (2026-04-14)

rwm-server → atlas-1 (10.2.2.5) via propheusdatalake2 ADLS Gen2. atlas-deploy (10.2.2.7) readied for serving role. NYC atlas left untouched on rwm-server.

---

## Totals

| Metric | Value |
|---|---|
| Total runtime (Stage 5 + Stage 6) | ~5 min on atlas-1 (16 cores, 62 GB RAM) |
| Hex-9 feature table | 7,318 × 613 |
| Hex-8 feature table | 1,191 × 638 |
| Subzone feature table | 332 × 243 (V8) |
| Place feature table | 174,711 × 114 |
| Data sources | 14 (5.7 GB) |
| Validation checks | 33 hex (32 pass) + 11 place (10 pass) |
