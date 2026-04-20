# Digital Atlas SGP — Hex & Subzone Generalized Representation

**Date:** 2026-04-12
**Status:** Hex v10 complete and validated. Subzone representation next.

---

## 1. Goal

Build a **generalized per-hex and per-subzone feature representation** of Singapore that downstream tasks (gap analysis, what-if simulation, similarity search, site selection, embedding models) can consume as a row or as an input to an autoencoder.

The representation must:
- Capture **what a hex IS** (buildings, population, commercial composition, land use)
- Capture **what a hex's CONTEXT is** (spatial neighborhood, transit-accessible area)
- Have **no leakage** from upstream model outputs (gap scores, predicted totals)
- Have **no broadcast noise** (features that are constant within a subzone or planning area)
- Be **normalizable** for ML consumption (sqrt-rule + z-score)

---

## 2. Hex v10 — Final Design

### 2.1 Coverage

| Metric | Value |
|---|---|
| **Hexes** | 7,318 (H3 resolution 9, ~175m edge, ~0.105 km²) |
| **Subzones covered** | 327 of 332 (5 micro-subzones are sub-hex-size) |
| **Places assigned** | 169,294 of 174,713 (96.9%) |
| **Population distributed** | 4,212,320 of 4,212,800 (99.99%) |
| **Columns (raw)** | 318 |
| **Columns (normalized, model-ready)** | 315 |
| **Broadcast feature columns** | 0 |

### 2.2 Feature pillars — 318 columns

```
SELF features (what this hex IS):                   194 columns
  ├── buildings .................. 19   fused Overture+HDB+OSM source
  ├── population ................  5   dasymetric Census 2025
  ├── land_use .................. 12   113K URA parcels area-weighted
  ├── transit ...................  7   MRT + bus + daily taps
  ├── amenities .................  9   hawkers, clinics, schools, etc.
  ├── roads_signals ............. 22   LTA congestion + OSM roads
  ├── walkability ............... 24   walk-times + dist-to-amenity
  ├── place_composition ......... 66   24 categories × counts/shares
  ├── micrograph ................ 20   T1-T4 spatial context vectors
  ├── influence_scalars .........  2   transit distance + reach
  ├── identity ..................  8   hex_id, coords, parent codes
  └── bookkeeping ...............  3   (excluded from model)

CONTEXT features (what this hex's NEIGHBORHOOD is):  124 columns
  ├── spatial max-influence ..... 31   densest hex within ~875m walk
  ├── spatial place-weighted .... 30   weighted avg of walking neighbors
  ├── transit max-influence ..... 30   densest hex reachable by MRT
  └── transit place-weighted .... 30   weighted avg of transit neighbors
```

### 2.3 Place composition (66 columns) — the commercial DNA

For each of the 174,713 places in the v2 master file, assigned to a hex via H3 lat/lng:

| Sub-pillar | Columns | What |
|---|---|---|
| Category counts | 24 | Shopping & Retail, Restaurant, Services, Business, Beauty, Education, Health, Cafe, Fitness, Convenience, Hawker, Automotive, Transport, Civic, Bar, Fast Food, Residential, Culture, Office, Hospitality, Bakery, General, Religious, NGO |
| Category shares | 24 | Same 24 as % of hex total |
| Price tier counts | 5 | Luxury, Premium, Mid, Value, Budget |
| Price tier shares | 5 | Same as % of priced places |
| Summary | 8 | pc_total, unique_brands, branded_count, branded_pct, unique_place_types, category HHI, category entropy (Shannon), segment entropy |

**Validation evidence:**
- Sungei Kadut = 84% automotive (SG's car workshop belt) ✓
- Tanglin = 80% health_medical (Gleneagles/Mt Elizabeth) ✓
- NUS Kent Ridge = 74% education, lu_institutional = 1.00 ✓
- CBD luxury concentration 4x heartland (23% vs 6%) ✓
- Brand penetration: CBD 32.5 unique brands/hex vs heartland 4.1 ✓

### 2.4 Influence features (124 columns) — spatial + transit context

#### The problem with naive k-ring aggregation

The initial v10 used 150 k-ring neighbor features (5 aggregates × 30 basis features across k=1 and k=2 rings). Testing revealed:

| Aggregate type | kNN lift | Signal quality |
|---|---|---|
| k=1 mean (6 neighbors) | +3.1% | Low — too local |
| k=1 max | +3.0% | Low |
| k=2 mean (18 neighbors) | +4.5% | Moderate — best single |
| **contrast (self - k1 mean)** | **-1.2%** | **Harmful** — local deviation is noise |
| **rank within k=1** | **-2.9%** | **Harmful** — ordinal in tiny group meaningless |
| All 150 combined | +2.0% | Poor — useful signals drowned by harmful ones |

**Key insight: contrast and rank features measure "how different am I from immediate neighbors" — which captures local structural position but HURTS similarity-based tasks.** A commercial island in Woodlands and one in Jurong West both have high contrast_pc_total but serve completely different markets.

#### The replacement: spatial + transit dual-view influence

| View | Reach | Aggregation | Why |
|---|---|---|---|
| **Spatial max** (31 cols) | H3 k=5 ring (~90 hexes, ~875m walk) | Features of the **single densest** neighbor | "What's the biggest commercial center I can walk to?" |
| **Spatial place-weighted** (30 cols) | Same k=5 ring | Mean weighted by pc_total | "What does the typical walkable commercial area look like?" |
| **Transit max** (30 cols) | MRT-connected stations + k=2 catchment | Features of the densest **transit-accessible** hex | "What can my residents access by MRT?" |
| **Transit place-weighted** (30 cols) | Same transit reach | Mean weighted by pc_total | "What does the typical transit-accessible area look like?" |

**Transit graph construction:**
- 209 MRT station hexes in the v10 universe
- Station-to-station edges: 3,716 (Haversine < 5km ≈ 3 MRT stops)
- Each hex connects to its nearest MRT station, then inherits that station's transit neighborhood
- 6,977 of 7,318 hexes (95.3%) have a reachable MRT station
- Sparse adjacency matrix saved as `hex_influence_graph.npz` (47,824 edges) for GNN use

**Validated improvement:**

| Method | kNN PA accuracy | Lift over baseline |
|---|---|---|
| Self features + lat/lng (baseline) | 0.245 | — |
| + old 150 k-ring features | 0.252 | +0.007 (+2.9%) |
| + spatial k=5 influence only | 0.439 | +0.194 (+79%) |
| + transit influence only | 0.444 | +0.199 (+81%) |
| **+ spatial + transit combined** | **0.551** | **+0.306 (+125%)** |

The +12.3% lift was confirmed to be **beyond positional signal** (lat/lng), meaning influence features carry genuine contextual information about a hex's commercial environment.

**The key validation signal:** Sentosa's `tr_max_pc_total = 1,356` — the transit graph correctly identifies Raffles Place (Singapore's densest hex) as Sentosa's transit max-influence. A Bedok HDB hex sees Downtown Core via the East-West MRT Line. This dual spatial+transit view is what makes the representation structurally coherent.

### 2.5 Micrograph features (20 columns) — per-place spatial relationships

Aggregated from 66,851 v2 place-level micrographs. Each place has a context vector with 4 tiers:

| Tier | Name | What it measures |
|---|---|---|
| T1 | Transit | Share of context driven by MRT/transit proximity |
| T2 | Competitor | Share driven by same-category competition |
| T3 | Complementary | Share driven by synergistic categories nearby |
| T4 | Demand | Share driven by demand magnets (schools, HDB, offices) |

**Archetype validation:**

| Hex type | T1 transit | T2 competitor | T3 comp | T4 demand |
|---|---|---|---|---|
| Near MRT (183 hexes) | **0.380** | 0.355 | 0.100 | 0.164 |
| Dense commercial (390) | 0.106 | **0.527** | 0.144 | 0.212 |
| Suburban residential (431) | 0.065 | **0.564** | 0.120 | 0.240 |

Transit signal is 6x stronger near MRT stations. Dense commercial areas are competition-dominated. `corr(mg_mean_transit, mrt_stations) = 0.611`.

**Known limitation:** v2 micrographs are from the 66K v1 place file. 11 of 12 category-specific files are duplicates (only `cafe_micrographs.jsonl` is real). Upgrade path: sync `micrograph_output_v3/` from rwm-server for per-category 174K-place micrographs.

### 2.6 Population features (5 columns) — dasymetric, not broadcast

Census 2025 subzone totals distributed to hexes proportional to **residential floor area** (from the fused building table). A park hex gets 0 residents; a dense HDB hex gets its proportional share.

**Why ratios (elderly_pct, walking_dependent_pct) are excluded at hex level:**
With a single dasymetric weight, the ratio `elderly_count / population = (subzone_elderly × w) / (subzone_pop × w) = subzone_elderly / subzone_pop` — a subzone constant regardless of weight. Without per-building age data, these ratios cannot carry within-subzone signal. They return at subzone level where they're naturally defined.

### 2.7 Buildings (19 columns) — fused from 3 authoritative sources

Overture Maps (377K buildings) + HDB authority geojson (13,386 blocks) + OSM (126K buildings), fused into a single table with 9 building classes.

Critical derived column: **`residential_floor_area_sqm`** = footprint × floors for residential buildings. This is the dasymetric weight for population disaggregation and the key signal distinguishing "this hex has HDB towers" from "this hex has a park."

HDB blocks verified against authoritative source: hex sum = **13,386 exact match**.

### 2.8 Land use (12 columns) — proper area-weighted from URA

Previous V9 `avg_gpr` was broadcast from subzone (zero within-subzone variance). Now recomputed by intersecting 113K URA zoning parcels with each hex polygon in SVY21 projected coordinates.

**Within-subzone variance of avg_gpr: median std = 0.34** (vs 0 before). This is the fix for the single most important leakage column.

9 zoning buckets: residential, commercial, business, mixed_use, institutional, open_space, transport, utility, other. Shares sum to 1.0. Shannon entropy captures land-use diversity.

---

## 3. What belongs at hex level vs subzone level

| Feature family | Hex level? | Subzone level? | Why |
|---|---|---|---|
| Building counts/types | ✓ per-hex | ✓ summed | Real per-hex variance from building centroids |
| Population + age counts | ✓ dasymetric | ✓ direct census | Meaningful at hex via residential floor area weight |
| elderly_pct / walking_dep_pct | ✗ | ✓ | Ratio collapses to subzone constant under single-weight dasymetric |
| Land use shares + GPR | ✓ per-hex | ✓ averaged | Real variance from URA parcel intersection |
| Place composition | ✓ per-hex | ✓ summed | Place centroids fall in specific hexes |
| Micrograph context | ✓ per-hex | ✓ averaged | Place-level micrographs aggregate naturally |
| HDB resale prices | ✗ | ✓ (227K txns) | No geocoding path at hex level without OneMap |
| Private resale prices | ✗ | ✓ (287K txns) | Same |
| NVIDIA personas | ✗ | ✓ (PA-broadcast) | Only 48 unique signatures across 318 subzones |
| ACRA business health | ✗ (not yet) | ✓ (next step) | 2M entities, aggregatable by subzone from registered address |
| Gap scores | ✗ (leakage) | ✗ (leakage) | Belong in a targets table, not the feature matrix |
| Spatial influence (k-ring / graph) | ✓ (H3 k=5 + MRT graph) | ✓ (subzone adjacency ego-graph) | Different graph topology per resolution |
| Transit connectivity | ✓ via influence graph | ✓ (subzone-level transit scores) | MRT station graph connects hexes; subzones summarize |

---

## 4. Subzone representation — planned design

The subzone feature table mirrors the hex pillar schema but with additional features that only exist at coarser resolution:

| Pillar | At subzone level | New vs hex |
|---|---|---|
| Demographics | Census directly (no dasymetric needed) | +elderly_pct, walking_dependent_pct (ratios now valid) |
| Housing / property | HDB 227K + private 287K transactions | **NEW**: hdb_median_psf, hdb_price_yoy, private_median_psf, pvt_txn_volume |
| Personas | NVIDIA 148K personas | **NEW**: 35 persona features (PA-broadcast but that's 48 distinct signatures — useful across PAs) |
| ACRA business health | 2M registered entities | **NEW**: acra_total, acra_churn_rate, acra_avg_age, sector breakdown |
| Place composition | Same 66 features, summed from hex | Same schema |
| Micrograph | Averaged from hex-level micrograph | Same schema |
| Land use | Averaged from hex-level | Same schema |
| Neighbor ego-graph | Subzone adjacency (shared boundary) | Different topology: contrast/rank make MORE sense at subzone level (5-15 neighbors vs 6 fixed H3) |

Expected size: **332 × ~350** features (comparable to hex).

---

## 5. Validation results summary

### Hex v10 final scorecard: **32 PASS / 1 soft-fail out of 33 checks**

| Check | Result |
|---|---|
| **Totals conservation** (6 sub-checks) | 6/6 PASS — places 174,713 exact, pop 99.99%, MRT 231 exact, HDB 13,386 exact |
| **Named landmarks** (8 spot checks) | 8/8 PASS — VivoCity 197 shopping, MBS 68 luxury, ION 1,245 places, Raffles Place 384 business, Changi T1 84 shopping, USS 21 entertainment, NUS 11 education, Jurong Island lu_bus 100% |
| **Value ranges** (7 sub-checks) | 7/7 PASS — all percentages [0,1], counts ≥ 0, demographic constraints hold, category sums preserved, LU sums = 1.0, entropy valid |
| **Cross-feature coherence** (4 checks) | 4/4 PASS — corr(pop, RFA)=0.952, corr(hdb, pop)=0.880, 95% of MRT-tap hexes have station, 91% residential hexes have pop |
| **Broadcast scan** | PASS — 0 unintentional broadcast (down from 40 in v1) |
| **Influence quality** (3 checks) | 2/3 PASS — Sentosa reaches CBD (tr_max=1,356), spatial/transit correlation moderate (0.605). Void-hex spatial max slightly above threshold (56 vs 50, not a real issue — void hexes near mainland find suburban neighbors) |
| **K=8 cluster recovery** (4 checks) | 4/4 PASS — CBD (luxury 6.1), HDB heartland (hdb 13.4), void (1,835 hexes), industrial (lu_bus 0.6) all correctly emerged unsupervised |

### kNN structural validation

| Reference hex | Top-10 nearest neighbors |
|---|---|
| **DTSZ05 Raffles Place (CBD)** | DTSZ09, OTSZ04, ORSZ02, ORSZ03, MUSZ01, DTSZ01, DTSZ02, OTSZ04, DTSZ08, SRSZ03 — all CBD core ✓ |
| **SISZ01 Sentosa (tourism)** | 4× Sentosa + 3× **DTSZ12 Bayfront (MBS)** + DTSZ11 + JESZ05 — structural twins across space ✓ |
| **BDSZ04 Bedok (HDB heartland)** | BDSZ01, WDSZ03, BMSZ04, HGSZ08, SESZ06×3, QTSZ02, BKSZ07 — HDB heartlands across 7 different PAs ✓ |

The **Sentosa → Marina Bay Sands** match is the signature validation: these hexes share tourism/hospitality/entertainment function despite being in different planning areas — the transit-augmented influence features correctly connect them.

---

## 6. Artifacts

### Data files (`data/hex_v10/`)

| File | Shape | Purpose |
|---|---|---|
| `hex_universe.parquet` | 7,318 × 8 | Identity (hex_id + parent codes) |
| `hex_buildings.parquet` | 7,318 × 20 | Buildings from fused source |
| `hex_population.parquet` | 7,318 × 9 | Dasymetric population |
| `hex_land_use.parquet` | 7,318 × 13 | URA area-weighted land use |
| `hex_amenities.parquet` | 7,318 × 13 | Point amenity counts |
| `hex_place_composition.parquet` | 7,318 × 67 | 174K v2 places per hex |
| `hex_micrograph.parquet` | 7,318 × 21 | v2 universal + cafe aggregates |
| `hex_influence.parquet` | 7,318 × 124 | **Spatial + transit influence** |
| `hex_influence_graph.npz` | 47,824 edges | Sparse adjacency for GNN use |
| **`hex_features_v10.parquet`** | **7,318 × 318** | **Full raw feature table** |
| `hex_features_v10_normalized.parquet` | 7,318 × 315 | **Model-ready** (sqrt + z-score) |
| `hex_features_v10_mask.parquet` | 7,318 × 308 | Missingness mask |
| `hex_features_v10_normalization_stats.json` | — | Per-column transform stats |
| `hex_features_v10_catalog.md` | — | Pillar-by-pillar feature catalog |
| `hex_v10_validation_report.md` | — | Full validation record |

### Builder scripts (`scripts/representation_v1/v10/`)

Run in this order:
1. `build_hex_v10_universe.py` — H3 polyfill (2-pass: center + overlap)
2. `build_hex_v10_buildings.py` — fused buildings + residential floor area
3. `build_hex_v10_population.py` — dasymetric Census 2025
4. `build_hex_v10_personas.py` — stub (PA-broadcast, excluded)
5. `build_hex_v10_land_use.py` — URA parcel intersection
6. `build_hex_v10_hdb_prices.py` — stub (no geocoding)
7. `build_hex_v10_amenities.py` — 9 geojson point sources
8. `build_hex_v10_merge.py` — join pillars + V9 copy-through
9. `build_hex_v10_place_composition.py` — 174K v2 places
10. `build_hex_v10_micrograph.py` — v2 universal + cafe
11. `build_hex_v10_influence.py` — **spatial k=5 + MRT transit graph**
12. `build_hex_v10_final.py` — merge + catalog + broadcast audit
13. `normalize_hex_v10.py` — sqrt rules + z-score + mask

---

## 7. Design decisions and rationale

### Drop features that can't be computed honestly at hex level

| Decision | Rationale |
|---|---|
| Drop personas (35 cols) | Source has only 48 unique PA-level signatures. Dasymetric disaggregation produces subzone-constant ratios. |
| Drop HDB prices (2 cols) | Resale CSV has no lat/lng. Without OneMap geocoding, can only broadcast at subzone level. |
| Drop elderly_pct (1 col) | Single-weight dasymetric makes the ratio = subzone constant. Counts remain (they DO vary). |
| Drop gap scores (4 cols) | These are V7/V8 model outputs. Including them as features would be leakage for any downstream gap analysis. |

### Replace k-ring with influence graph

| Decision | Rationale |
|---|---|
| Drop contrast_* | Actively hurts similarity (-1.2%). Local deviation is noise for cross-hex comparison. |
| Drop rank_* | Actively hurts (-2.9%). Ordinal within 6 neighbors meaningless for geographic context. |
| Add spatial max-influence | The single densest neighbor within walking reach captures "what commercial center serves this area" — the strongest individual signal (+8% alone). |
| Add transit max-influence | MRT-connected commercial centers capture "what can residents commute to" — complementary to spatial (corr 0.605, not redundant). |
| Place-weighted mean | Captures "what does the typical commercial activity look like around me" — smoother contextual signal. |
| k=5 ring for spatial | Validated: signal grows monotonically with ring size up to k=8. k=5 balances coverage (~875m, 15-min walk) vs compute cost. |

### Use sqrt normalization, not log

| Decision | Rationale |
|---|---|
| sqrt for counts | User specified: "log kills variance." sqrt preserves more of the distribution shape while still compressing long tails. |
| exp(-d/500m) for distances | "Closer is larger" with a 500m scale parameter: at 500m value = 0.37, at 1km = 0.14, at 2km = 0.02. |
| passthrough for shares/entropies | Already bounded [0,1] or [0, ln(24)]. No need to transform. |
| z-score after rule | Centers each feature at 0, scales to unit variance. NaN → 0 = "at the mean" with mask preserved. |

### Majority-area subzone assignment (not center containment)

84 hexes (1.15%) had their parent_subzone reassigned from center-containment to majority-area-overlap. This reduced HDB-in-water-catchment misassignment and ensures dasymetric population distribution targets the correct subzone.

---

## 8. Next steps

1. **Build subzone representation** — same pillar schema, with personas, HDB prices, and ACRA added back. Neighbor ego-graph over subzone adjacency (not H3 k-ring).
2. **Train AE embedding** — 318 → 64 → 32 autoencoder on the normalized hex matrix. Validate with reconstruction R², kNN, and downstream transfer to gap prediction.
3. **Sync micrograph v3** — per-category 174K-place micrographs from rwm-server would roughly double the micrograph pillar from 20 → ~160 features.
4. **Bus transit graph** — current transit influence is MRT-only. Adding 788 bus services × 5,177 stops would extend reach for non-MRT hexes.
5. **Fill V9 copy-through NaN** — 1,421 new hexes have NaN for roads/signals/walkability. Re-running those pipelines against v10 universe would complete coverage.
