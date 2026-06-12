# Plexis SGP v4 — Checkpoint

**Date:** 2026-04-25 (updated: roads + centrality)
**Authoritative location:** `atlas-1:/home/azureuser/plexis-sgp-v4/`
**Local mirror:** `digital-atlas-sgp/plexis-sgp-v4/`
**Total disk:** 226 MB

## Stages added since previous checkpoint

| Stage | Builder | Validator | Pass | Wall-clock |
|---|---|---|---|---|
| **2** | Buildings (Overture + HDB authoritative) | validate_buildings.py | 5/6 + 1 WARN | 3.0s + 0.4s |
| **3b** | Non-resident allocation (5.98M total) | validate_non_residents.py | 5/5 | 0.4s + 0.4s |
| **6** | Roads + Parking (lengths, topology, motorway proximity, parking lots, MSCPs) | validate_roads.py | 6/8 + 2 WARN | 75.3s + 0.4s |
| **6g** | Road centrality (betweenness, closeness, PageRank, bridges) | validate_road_centrality.py | 4/5 + 1 WARN | ~17 min + 0.5s |
| **Updated pipeline** | | | **41/45 + 4 WARN** | **3.5 min** (excl. 6g) |

## Per-hex layers now (7 layers, ~155 cols total)

| Layer | Cols | What |
|---|---|---|
| Identity (Stage 0) | 8 | hex9_id, lat, lng, parent_hex8/subzone/PA/region |
| Population (3 + 3b) | 11 | resident, nonres, total_all, age buckets, hdb_share, nonres_share |
| Land use (4) | 21 | 14 lu_*_pct buckets, entropy, dominant_use, GPR, parcels |
| Buildings (2) | 39 | counts, areas, 9 class buckets, floors, heights, HDB stats |
| **Roads (6)** | **66** | lengths total/ped/veh, 14 class shares, intersections, dead ends, gridiness, motorway through+adjacent+exits, lane-km, oneway, bridge, tunnel, signalized crossings |
| **Parking (6)** | **11** | OSM lots, entrances, bicycle parking, HDB MSCPs, surface carparks, footprint share |
| **Road centrality (6g)** | **11** | betweenness mean/max, closeness, PageRank, eigenvector, bridge count |

---

---

## 1. Stages complete (5 of 19)

| # | Stage | Builder | Validator | Pass | Wall-clock |
|---|---|---|---|---|---|
| 0 | Hex universe (hex-9 + hex-8) | `build_hex_universe.py` | `validate_coverage.py` | **6/6** | 6.9s |
| 0b | Post-sweep (close coverage to 100%) | `post_sweep.py` | `validate_coverage.py` | **6/6** | 23.9s |
| 0c | Admin boundaries (PA + region + HDB town) | `build_admin_boundaries.py` | `validate_admin.py` | **5/7 + 2 WARN** | 23.5s |
| 1a | Place geo-attach | `enrich_places.py` | — | — | 18.9s |
| 1b | Categories (det + heuristic + finalize) | `apply_category_map.py` + `apply_heuristics.py` + `finalize_categories.py` | — | — | 3.7s |
| 1c | Brand normalization + name detection | `apply_brands.py` | — | — | 7.9s |
| 1d | Quality / review signals | `apply_quality.py` | — | — | 0.7s |
| 3 | Population dasymetric | `build_population.py` | `validate_population.py` | **6/6** | 6.0s |
| 4 | Land use (URA Master Plan) | `build_land_use.py` | `validate_land_use.py` | **6/6** | 18.6s |
| **Pipeline total** | | | | **∑ 25/27 + 2 WARN** | **102.7s + 18.6s = 2 min** |

Pipeline runner: `run_pipeline.py` orchestrates all stages with timing + pass/fail tracking.
Skipped: Stage 2 buildings (HDB blocks alone cover 77% of population, sufficient for Stage 3).
Pending LLM key: Stage 1b.2b (18,015 `other_uncategorized` → 24-bucket).

---

## 2. Spatial universe (Stage 0 + 0c)

| Layer | Count | Source | Coverage |
|---|---|---|---|
| Hex-9 | **7,318** | derived (H3 res-9, ~174 m edge, ~0.11 km²) | 100.0000% of SGP, 0 m² gap |
| Hex-8 | **1,191** | derived (H3 res-8, ~461 m edge, ~0.74 km²) | parent-closure of all hex-9 |
| Subzones | **332** | URA authoritative | 332/332 in overlap table |
| Planning Areas | **55** | URA authoritative | 55/55 |
| Regions | **5** | dissolved from PAs | CENTRAL · NORTH · NORTH-EAST · EAST · WEST |
| HDB Towns | **27** | derived from 13,386 HDB blocks (200 m buffered union) | 152.10 km² (19.4% of SGP) |

Each hex carries: `hex9_id`, `hex8_id`, `parent_hex8`, `parent_subzone`, `parent_subzone_name`, `parent_pa`, `parent_region`. Many-to-many overlap tables (`hex_*_overlap.parquet`) track all subzone/PA/region/HDB-town relationships.

**Validation:** L1 every subzone has hex (332/332) · L2 every PA has hex (55/55) · L3 every region (5/5) · L4 every HDB town (27/27) · L5 areal coverage 100.0000% · L6 per-subzone coverage 100% · all 13,386 HDB blocks inside HDB town polygons.

---

## 3. Population (Stage 3)

`hex/hex9_population.parquet` (7,318 × 11)

| Field | Value |
|---|---|
| SGP residents | **4,212,800 / 4,212,800** allocated (0.000% drift) |
| HDB residents | 3,197,740 (75.9% of pop) |
| Non-HDB residents | 1,015,060 |
| Hexes with population | **3,693 / 7,318** (50.5%) |
| Method | HDB blocks via dwelling units + non-HDB via subzone area share, all at chunk level |

Top populated hex-9 (sanity ✓):
```
13,321  PASIR RIS WEST        (PASIR RIS)
 8,434  JURONG WEST CENTRAL   (JURONG WEST)
 8,341  KEAT HONG             (CHOA CHU KANG)
 7,936  MATILDA               (PUNGGOL)
 7,827  WOODLANDS SOUTH       (WOODLANDS)
```

**Validation 6/6 PASS:** P1 global total ✓ · P2 HDB total ✓ · P3 non-HDB total ✓ · P4 per-subzone chunk reconstruction (mean drift 0.0000%) ✓ · P5 age sums = pop_total ✓ · P6 no negatives/nulls ✓

---

## 4. Land use (Stage 4)

`hex/hex9_land_use.parquet` (7,318 × 21)

| Field | Value |
|---|---|
| URA parcels processed | **113,212** |
| Hex × parcel intersections | 163,090 |
| Hexes with land-use data | **7,318 / 7,318** (100%) |
| Total area | 784.70 km² (vs URA 784.85, **0.019% diff**) |
| 14 buckets | residential, mixed_use, commercial, hotel, business, business_park, educational, health, institutional, open_space, transport, utility, water, reserve (+ "other") |

Per-hex columns:
- 15 share columns `lu_*_pct` summing to 1
- `lu_total_m2`, `lu_entropy`, `dominant_use`
- `avg_gpr`, `max_gpr` (area-weighted), `lu_parcel_count`

Top hexes per bucket (sanity ✓):
```
commercial    93.2%  MARITIME SQUARE       (Bukit Merah, VivoCity area)
residential  100.0%  RIDOUT, MT PLEASANT
business_park 81.1%  INTERNATIONAL BIZ PK  (Jurong East)
hotel         89.9%  SENTOSA               (Southern Islands)
```

**Validation 6/6 PASS:** L1 total area = URA (0.019% diff) · L2 every hex has data · L3 shares ∑=1 · L4 entropy bounds · L5 dominant_use present · L6 5/5 landmarks (Sentosa hotel, NUS Kent Ridge inst+bp, Maritime Square commercial, Tuas business, Mt Pleasant residential)

---

## 5. Places (Stage 1, all sub-stages)

`places/sgp_places_final.parquet` (190,591 × 27)

| Sub-stage | Output | Resolution |
|---|---|---|
| 1a geo-attach | hex9, hex8, subzone, PA, region, HDB town per place | 100% (+ 13 offshore-marine reefs) |
| 1b category | `plexis_category` (24 buckets) via deterministic + heuristic | **172,576 / 90.55%** classified |
| 1c brand | `brand_norm` via alias normalization + name patterns | **15,127 branded / 7.94%** (268 unique) |
| 1d quality | `magnet_strength`, percentile, magnet/long-tail flags | 21,570 magnets (11.3%) |

### Distribution

```
Top-10 plexis_category:
  business_office        21,377  (11.22%)
  services               20,303  (10.65%)
  other_uncategorized    18,015  ( 9.45%)   ← LLM refinement pending
  industrial_mfg         16,940  ( 8.89%)
  residential            15,554  ( 8.16%)
  shopping_retail        14,211  ( 7.46%)
  transportation         12,367  ( 6.49%)
  education              10,438  ( 5.48%)
  restaurant             10,119  ( 5.31%)
  beauty_personal         7,557  ( 3.97%)

Region split:
  CENTRAL         91,086 places (47.8%)
  WEST            32,611
  NORTH-EAST      24,228
  EAST            23,597
  NORTH           19,056

HDB town presence: 99,973 places / 52.5%
```

### Top brand validations (sanity ✓)

```
Starbucks         128 locs  → DOWNTOWN CORE       (CBD ✓)
7-Eleven          434       → DOWNTOWN CORE       (CBD/transit ✓)
NTUC FairPrice    241       → BUKIT MERAH         (HDB estates ✓)
McDonald's        157       → TAMPINES            (suburban ✓)
PCF Sparkletots   372       → WOODLANDS           (new towns ✓)
```

### Top magnets (rating ≥ 4 × reviews ≥ 100)

```
Jewel Changi Airport      4.8★ × 95,831 reviews
Universal Studios         4.6★ × 110,870
Resorts World Sentosa     4.6★ × 91,643
Singapore Changi Airport  4.7★ × 67,025
Marina Bay Sands          4.7★ × 63,341
Merlion Park              4.6★ × 75,253
Supertree Grove           4.7★ × 53,489
Singapore Zoo             4.6★ × 51,455
VivoCity                  4.5★ × 54,697
```

All iconic SGP attractions ✓.

---

## 6. Unified joinable view

All Stage outputs share `hex9_id` / `hex8_id` / `parent_subzone_*` keys. Confirmed joinable:

```python
import pandas as pd
from pathlib import Path
ROOT = Path("plexis-sgp-v4")

h9     = pd.read_parquet(ROOT/"hex/hex9_universe.parquet")        # 7,318 × 8
pop    = pd.read_parquet(ROOT/"hex/hex9_population.parquet")       # 7,318 × 11
lu     = pd.read_parquet(ROOT/"hex/hex9_land_use.parquet")         # 7,318 × 21
places = pd.read_parquet(ROOT/"places/sgp_places_final.parquet")   # 190,591 × 27

# Unified hex view (7,318 × 39)
hex_view = h9.merge(pop, on="hex9_id").merge(lu, on="hex9_id")

# Place + hex (190,591 × 65)
combined = places.merge(hex_view, on="hex9_id")
```

---

## 7. File inventory

### Boundaries (`boundaries/`, 7.3 MB)
```
subzones.geojson         3.1 MB  332 features
planning_areas.geojson   1.8 MB  55
regions.geojson          1.2 MB  5
hdb_towns.geojson        1.3 MB  27
```

### Hex universe + features (`hex/`, 5.1 MB)
```
Universe:
  hex9_universe.parquet      224 KB  7,318 cells
  hex9_universe.geojson      3.5 MB
  hex8_universe.parquet      42 KB   1,191 cells
  hex8_universe.geojson      567 KB

Overlap tables (4 admin layers × 2 resolutions = 8):
  hex{9,8}_subzone_overlap.parquet
  hex{9,8}_pa_overlap.parquet
  hex{9,8}_region_overlap.parquet
  hex{9,8}_hdb_town_overlap.parquet

Features:
  hex9_population.parquet    270 KB  Stage 3 (10 cols)
  hex9_land_use.parquet      416 KB  Stage 4 (20 cols)

Reports:
  universe_summary.json      coverage_report.json     admin_summary.json
  admin_coverage_report.json population_report.json   population_validation.json
  land_use_report.json       land_use_validation.json
```

### Places (`places/`, 158 MB)
```
Source:
  sgp_place_V1.jsonl          61 MB    190,591 raw
  sgp_places_geoattached.jsonl 111 MB  enriched line-delim

Parquets (each 190,591 rows):
  sgp_places_geoattached.parquet     11 MB  Stage 1a output
  sgp_places_categorized.parquet     11 MB  Stage 1b output
  sgp_places_branded.parquet         11 MB  Stage 1c output
  sgp_places_final.parquet           12 MB  ← Stage 1 deliverable (27 cols)

Rollups:
  brand_rollup.parquet                16 KB   268 brands
  category_quality_benchmarks.parquet 11 KB   24 categories
  hex9_place_counts.parquet           35 KB   per-hex9 density
  hex8_place_counts.parquet           10 KB
  subzone_place_counts.parquet        5 KB
  pa_place_counts.parquet             3 KB
  hdb_town_place_counts.parquet       2 KB

Reports:
  geoattach_report.json     category_map_report.json
  heuristics_report.json    stage_1b_final_report.json
  brand_report.json         quality_report.json
```

### Scripts (21 total in v4 root)
```
Builders:
  build_hex_universe.py         build_population.py
  post_sweep.py                 build_land_use.py
  build_admin_boundaries.py
  enrich_places.py
  apply_category_map.py + classify_heuristics.py + apply_heuristics.py + finalize_categories.py
  apply_brands.py + brand_map.py
  apply_quality.py
  llm_classify.py               (Stage 1b.2b — pending OpenRouter key)

Lookup tables:
  category_map.py     classify_heuristics.py    brand_map.py

Validators:
  validate_coverage.py     validate_admin.py
  validate_population.py   validate_land_use.py

Orchestration:
  run_pipeline.py        Master pipeline runner
  analyze_places.py      Stage 1a summary
```

### Logs (`logs/`)
```
pipeline_run.json    Last full-pipeline timing + pass/fail
```

---

## 8. Validation scorecard (current)

| Layer | Status | Detail |
|---|---|---|
| Hex universe coverage | **6/6 PASS** | 100.0000% strict areal coverage, 0 m² gap |
| Admin boundaries | **5/7 + 2 WARN** | All 4 layers covered; 12 hex/PA boundary edge cases (max-overlap vs nested parent_pa — flagged as WARN, expected) |
| Population dasymetric | **6/6 PASS** | Global, HDB, non-HDB, per-subzone all 0.000% drift; age sums exact |
| Land use | **6/6 PASS** | 0.019% area diff vs URA; 5/5 landmarks |
| **Total** | **23/25 PASS, 2 WARN** | All WARNs are documented edge effects, not data errors |

---

## 9. Schema reference (for downstream consumers)

### Hex-9 unified view (39 cols when joined)

```
Identity (8):
  hex9_id, lat, lng,
  parent_subzone, parent_subzone_name, parent_pa, parent_region, parent_hex8

Population (8 cols, Stage 3):
  pop_total, pop_hdb, pop_non_hdb, pop_hdb_share,
  pop_0_14, pop_15_64, pop_65plus

Land use (20 cols, Stage 4):
  lu_total_m2,
  lu_residential_pct, lu_mixed_use_pct, lu_commercial_pct, lu_hotel_pct,
  lu_business_pct, lu_business_park_pct, lu_educational_pct, lu_health_pct,
  lu_institutional_pct, lu_open_space_pct, lu_transport_pct, lu_utility_pct,
  lu_water_pct, lu_reserve_pct, lu_other_pct,
  lu_entropy, dominant_use,
  avg_gpr, max_gpr, lu_parcel_count
```

### Places final (27 cols)

```
Identity (8):           id, name, primary_category, brand, rating, reviews_count, latitude, longitude
Geo (9 — Stage 1a):     hex9_id, hex8_id, parent_subzone_c, parent_subzone_name,
                         parent_subzone_source, parent_pa, parent_region, hdb_town, in_sgp
Category (1 — 1b):      plexis_category
Brand (2 — 1c):         brand_norm, brand_source
Quality (7 — 1d):       has_rating, has_reviews, review_bucket, magnet_strength,
                         review_quality_pctl_in_cat, is_magnet, is_long_tail
```

---

## 10. What's missing / next

### Immediate next stages (data already on atlas-1)
- **Stage 5 — transit + GTFS** — 231 MRT/LRT, 5,177 bus stops, 88.6M monthly taps, 230K GTFS trips
- **Stage 6 — walk graph + roads** — 550,991 OSM road segments
- **Stage 7 — place composition** — aggregate Stage 1 outputs to hex (24-cat counts/shares, brand mix)
- **Stage 8 — amenity anchors** — MRT/hawker/clinic/park distance & count per hex
- **Stage 9 — demand pull** — 6 distance-decay weighted demand scores

### Medium-term
- **Stage 1b.2b LLM refinement** — 18K `other_uncategorized` → cleaner classification (needs OpenRouter key)
- **Stage 5b satellite** — VIIRS night lights + GHSL built-up + WorldCover (data on atlas-1, optional)
- **Stage 10–15** — synergy, saturation, spatial rings, micrograph, influence, merge+normalize

### Long-term
- **Stages 16–17** — composites, place enrichment (114-feature place table)
- **Stage 18 — Plexis-Graph** — 39-relation knowledge graph
- **Stage 19 — Plexis-Embed** — GAT-R-GCN 256d embeddings (optional)

---

## 11. Build environment confirmed

- **Authoritative compute:** atlas-1 (16 vCPU / 62 GB / Python 3.12 / h3 v4.4.2 / shapely v2.1.2 / geopandas v1.1.3)
- **Path resolution:** all scripts use `PLEXIS_DATA_ROOT` env override or auto-detect (`/home/azureuser/digital-atlas-sgp/data` on atlas-1, `../data` locally)
- **Sync pattern:** local Mac mirror for inspection; heavy compute (URA, OSM, GTFS) runs on atlas-1
- **Pipeline runner:** `python3 run_pipeline.py [--from STAGE] [--only STAGE] [--skip A,B]`

Last full pipeline run: **2026-04-25**, total **2 min**, all 23 checks PASS + 2 documented WARNs.

---

*Checkpoint saved 2026-04-25. Mirrored to local at `digital-atlas-sgp/plexis-sgp-v4/CHECKPOINT.md`.*
