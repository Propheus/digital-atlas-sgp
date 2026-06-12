# Plexis — Steps Quick Reference

**Date:** 2026-04-23
**Purpose:** One-page summary. For detail see `PLEXIS_METHODOLOGY.md` + `FEATURE_CATALOG.md`.

---

## The 20 steps

| # | Stage | What it does | Output |
|---|---|---|---|
| **0** | Universe | Define hex-8/hex-9 cells over city boundary + planning units | `hex_universe.parquet` |
| **1** | Places consolidation | Overture + OSM + gov POIs → dedupe → LLM classify (24 cats) → brand-link | `places_master.jsonl` |
| **2** | Buildings fusion | Overture + OSM + local (HDB/PLUTO) → class, floors, HDB flag | `buildings_fused.parquet` |
| **3** | Population dasymetric | Subzone pop → hex via residential floor-area weights | `hex_population.parquet` |
| **4** | Land use | Zoning parcels → 12 shares + entropy + dominant_use | `hex_land_use.parquet` |
| **5** | Transit + GTFS | Stations, stops, ridership, headways, peak splits | `hex_transit.parquet` |
| **5b** | Satellite (opt) | VIIRS nightlights + GHSL built-up + WorldPop + WorldCover | 16 sat features |
| **6** | Walk graph | OSM pedestrian graph (motorways/trunks filtered) | `pedestrian_graph.pkl` |
| **7** | Place composition | 24 cat counts + shares, brands, price tiers, entropy, HHI | `hex_place_composition.parquet` |
| **8** | Amenity anchors | MRT / hawker / clinic / park / supermarket etc. counts + distances | `hex_amenities.parquet` |
| **9** | Demand pull | 6 pulls × distance-decay (NATIVE per resolution, different λ) | 14 pull features |
| **10** | Synergy | 10 co-location scores (cat × pull) | 23 synergy features |
| **11** | Saturation + gap | actual vs expected per category (only where `pop > 500`) | 13 features |
| **12** | Spatial rings | `sp_*` (spatial) + `tr_*` (transit) ring aggregates | 123 features |
| **13** | Micrograph | Per-category context vectors (12 × 13 = 156) | `hex_micrograph.parquet` |
| **14** | Influence | interface, gradient_position, net_demand_flow (no leakage) | 6 features |
| **14b** | Development gap | URA zoning vs actual built footprint (satellite-free) | 4 features |
| **14c** | Dynamic LTA (opt) | Live traffic, carpark, taxi, taps/capita | 18 features |
| **15** | Merge + normalize | sqrt-rule for counts, z-score for rates | `hex_features_v10_normalized.parquet` |
| **16** | Hex-9 → Hex-8 aggregate | SUM / pop-weighted mean / MIN / MAX / NATIVE-recompute | `hex8_final.parquet` (638 cols) |
| **17** | Place enrichment | Per-place: competition, complementary, anchor, synergy (target-only), catchment, survivability | `places_featured.parquet` (114 cols) |
| **18** | Plexis-Graph | Build 1.49M edges across 39 typed relations from the feature stack | `plexis_triplets.parquet` |
| **19** | Plexis-Embed (opt) | 4-layer GAT-R-GCN → 256d node embeddings | `plexis_v6_embeddings.npz` |

---

## Plexis = three artifacts

```
Stages 0–17   →  Feature stack     (hex9 613 cols, hex8 638, places 114)
Stage 18      →  Plexis-Graph      (1.49M edges × 39 relations)
Stage 19      →  Plexis-Embed      (256d per node, optional)
```

---

## Validation = 10 layers (§11 of methodology)

1. Totals conservation
2. Value ranges
3. Cross-feature coherence
4. Named landmarks
5. Brand tests
6. Micrograph fixtures
7. **Paper replication (9/10 + 8/8 theories)**
8. Model perf
9. Use-case integration (50 queries / 9 use cases)
10. Cross-city replication

---

## Build on a new city — day-0 checklist

1. Inventory data against §4.1 mandatory list
2. Pick tier-1 unit (planning unit polygons — official > admin > OSM > Voronoi)
3. Pick H3 resolutions per city area
4. Build category taxonomy (start from 24 SGP cats, add local specials)
5. Curate landmark / brand / micrograph / query fixtures
6. Decide which of 39 relations apply (universal vs city-specific)
7. Run stages 0–17 with validation gates between each layer
8. Emit graph (stage 18)
9. Optional: train embed (stage 19)

---

## Runtime

| Phase | Wall-clock (16-core / 62 GB) |
|---|---|
| Full feature stack + graph (stages 0–18) | 60–90 min |
| Embed (stage 19, GPU) | 84 min |
| Embed (stage 19, CPU) | 4–6 h |

---

*Companion docs: `PLEXIS_METHODOLOGY.md` (full detail), `FEATURE_CATALOG.md` (1,384 features with stats), `HOW_WE_BUILT_DIGITAL_ATLAS.md` (SGP narrative), `PLEXIS_EVOLUTION.md` (embed v1→v6 history).*
