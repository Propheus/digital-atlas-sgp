# Digital Atlas — Hong Kong Replication Playbook

*How the Singapore atlas was built, layer by layer, and exactly what to swap to
rebuild it for Hong Kong. Written 2026-06-13 from the live SG pipeline
(`plexis-sgp-v5/`, 70+ build scripts, 30 validators, v5.4.0).*

---

## 0. The mental model — what actually transfers

The atlas is **three things stacked**, and only the bottom one is
city-specific:

```
  TRAINING   plexis-e1 (hex 256-d) + plexis-p1 (place 64-d)   ← 100% reusable code
  ─────────────────────────────────────────────────────────
  DERIVED    S1–S11 metrics (capture, isochrones, churn…)     ← 100% reusable code
  ─────────────────────────────────────────────────────────
  FOUNDATION raw layers ingested from data sources            ← THIS is what you re-source for HK
```

**So the whole job is: re-point the foundation layer at Hong Kong sources,
re-run the same build scripts, re-run the same training with the same locked
exams.** The grid, the feature math, the embedding code, the validation
protocol — all of it is grid-agnostic. You are doing a *data-sourcing*
project, not a modelling project.

Everything below the dotted line already works. Budget your effort on
section 3 (source mapping) and the HK gotchas in section 5.

---

## 1. The grid (do this first)

SG uses **H3 resolution 8** hexagons (~0.46 km² each) as the product grain —
"hex8 is the only grain, always" (hex9 is internal-only for catchment math).

For HK:
- Generate the H3-8 universe clipped to Hong Kong's land boundary (Lands Dept
  coastline from CSDI). Expect **~1,800–2,400 hex8 cells** (HK land ≈ 1,100 km²
  vs SG ≈ 730 km², but ~40% is country park → many cells will be
  Not-Applicable, see §5).
- Carry a parent-administrative join from the start: **District (18) → DC
  constituency area → TPU (Tertiary Planning Unit, C&SD's census grain) →
  Street Block Group**. TPU is HK's analogue of SG's subzone.
- Tag a `zone_type_broad` per cell on day one (residential / commercial /
  industrial / country-park / harbour / airport / future) — this drives the
  Not-Applicable masking everywhere downstream. **This is non-negotiable;** in
  HK it matters more than SG because ~40% of land is non-developable.

Reusable code: `build_hex_universe.py`, `build_admin_boundaries.py` —
re-point the boundary inputs, keep the logic.

---

## 2. Foundation layers (what you must ingest)

These are the raw inputs every derived metric stands on. SG build script in
brackets — each becomes the template for its HK twin.

| Layer | What it is | SG script |
|---|---|---|
| Boundaries | land outline, admin units, planning zones | `build_admin_boundaries.py` |
| Population | dasymetric headcount by small area, age, tenure | `build_population.py`, `build_non_residents.py` |
| Buildings | footprints, height/floors, use, GFA | `build_buildings.py` / `_clean.py` |
| Land use | zoning parcels, GPR/plot ratio, mix | `build_land_use.py` |
| Roads | network, centrality, intersections, walkability | `build_roads.py`, `build_road_centrality.py`, `build_walkability.py` |
| Transit | rail/bus/tram/ferry stops, lines, GTFS timetable | `build_transit.py`, `build_gtfs_windows.py` |
| Places (POI) | every venue, category, brand | `build_osm_pois.py`, `build_place_composition.py` |
| Place micrograph | per-venue 400/800 m world | `build_place_micrograph.py` |
| Business registry | company formations + deregistrations | `build_acra_biz.py` |
| Rent/price surface | residential rent & transaction prices | `build_rent_surface.py`, `build_hdb_resale.py` |
| Night lights | VIIRS radiance (activity proxy) | `build_satellite.py` |
| Future pipeline | planned rail + development headroom | `build_pipeline.py` |
| Origin-destination | trip flows between zones | `build_od_hex8.py` |

---

## 3. THE SOURCE MAP — Singapore → Hong Kong

This table is the heart of the playbook. Each row = one foundation layer, the
SG source it came from, and the HK source you replace it with.

| Layer | Singapore source | **Hong Kong source** | Notes |
|---|---|---|---|
| **Open-data hub** | data.gov.sg (API key) | **DATA.GOV.HK** + **CSDI Portal** (portal.csdi.gov.hk, 500+ geo datasets, free API) | CSDI launched 2022; your one-stop "data supermarket" — start every search here |
| **Geocoding / boundaries** | OneMap (Lands Authority) | **Lands Dept ALS** (Address Lookup Service) + CSDI boundary layers; **C&SD TPU/Street-Block** for census grain | replaces SG subzones with TPUs |
| **Population** | SingStat dasymetric, HDB-weighted | **C&SD 2021 Population Census by TPU/Street Block**; dasymetrise onto buildings. Global fallback: **WorldPop / GHS-POP** | no HDB-unit weighting — weight by residential GFA & floors instead (§5) |
| **Buildings** | Overture + OSM + authoritative HDB blocks | **CSDI 3D Building / Building Footprint** (Lands Dept) + **Overture/OSM** (global, work anywhere) | HK buildings are far taller — height/floors are first-class features |
| **Land use / zoning** | URA Master Plan parcels + GPR | **Town Planning Board Outline Zoning Plans (OZP)** via Planning Dept / CSDI; plot-ratio from OZP | "plot ratio" = HK's GPR; podium+tower forms common |
| **Public housing** | HDB blocks + towns (authoritative) | **Hong Kong Housing Authority** estate data (public ~30%, subsidised-sale ~15%) | no "town" structure — use estate polygons as the analogue |
| **Roads** | LTA / OSM network | **OSM** (global) + **CSDI road network / centreline** | OSM is fine anywhere; CSDI adds official centrelines |
| **Transit (static)** | LTA DataMall + GTFS | **DATA.GOV.HK GTFS / headway** (MTR, KMB, Citybus, GMB minibus, tram, ferry) + community **gtfs-hk** | richer modes than SG; minibus (GMB) coverage is a HK specialty |
| **Transit (real-time)** | LTA bus arrival API | **Transport Dept real-time arrival** datasets on DATA.GOV.HK | per-operator endpoints |
| **Places / POI** | Overture 147K + scraped/LLM-classified | **Overture / OSM** (global) + Google/HKMapService scrape; **classify with a CJK-aware LLM** | Cantonese/Chinese names — see §5 |
| **Business registry** | ACRA bulk (2.07M entities, churn) | **Companies Registry (ICRIS / Cyber Search)** — *NOT bulk-open* | ⚠ biggest sourcing gap — see §5. Proxy via business-licence / F&B-licence open datasets |
| **Rent / price** | URA private + HDB resale (227K txns) | **Rating & Valuation Dept (RVD)** rent & price indices by district/class; private txns via EPRC/Centaline (paywalled) | RVD is open but coarser (district, not unit) — build an IDW surface like SG did |
| **Night lights** | VIIRS (NASA, global) | **VIIRS** — identical, global | zero change |
| **Built-up / land cover** | GHSL (global) | **GHSL** — identical, global | zero change |
| **Future rail / pipeline** | URA MP2019 rail layer | **MTR Future Railway Programme / Rail 2034** + Planning Dept land-supply | maps cleanly onto `build_pipeline.py` |
| **Origin-Destination flows** | LTA OD matrix (open) | ⚠ **No open passenger OD matrix** in HK | see §5 — biggest methodological gap; use MTR patronage + Travel Characteristics Survey as priors |
| **Personas** | NVIDIA synthetic | reuse same synthetic pack or skip | optional layer, low priority |

---

## 4. Build order (the pipeline, unchanged)

Run in dependency order — each gate must pass before the next (the
"one-at-a-time with validation" protocol; ledger = `SITE_SELECTION_VALIDATION.md`).

1. **Foundation** — grid, boundaries, population, buildings, land use, roads,
   transit, POI. (Validators: `validate_admin/population/buildings/roads/transit`.)
2. **Place micrograph** — per-venue 400/800 m fingerprint (`build_place_micrograph.py`).
3. **S1–S11 derived metrics**, in this order (each has a `build_*` + `validate_*`):
   - S1 Huff capture · S2a walk isochrones · S2b transit isochrones ·
     S3 daytime population · S4 business churn · S5 labour shed ·
     S6 co-location lift · S7 micro-visibility · S8 rent surface ·
     S9 future pipeline · S10 context pack · S11 mobility pack.
4. **Assemble master** — `build_all_features.py` → `hex8_all_features.parquet`
   (the HK equivalent of the 1,191×801 table).
5. **Catalogs** — `build_catalog.py` + `build_catalog_json.py` (keep 100%
   described — house rule).
6. **Checkpoint** — `publish_checkpoint.py` with VERSION bumped to a HK tag.

Every gate type carries over: conservation (totals match census),
NaN-vs-zero accounting, redundancy audit (|r|>0.9 → drop/redefine),
archetype spot-checks, known-answer recovery.

---

## 5. Hong Kong gotchas (where SG assumptions break)

1. **Vertical city.** SG's building features assume mostly mid-rise + HDB
   slabs. HK is towers-on-podiums, 40–60 floors common. **Make
   height/floors/GFA first-class**, and population dasymetry must weight by
   *residential floor area*, not footprint — or dense estates will read as
   low-population.
2. **~40% country park / steep terrain.** Huge non-developable area. The
   `zone_type_broad` → Not-Applicable masking (already in the SG code, built
   for water catchment + military) is *essential* here — country parks,
   reservoirs, and the harbour must be masked, never scored. Add a slope/DEM
   gate so steep undeveloped hillsides don't pollute the embedding.
3. **No open business-churn registry.** ACRA gave SG a 2M-entity formation/
   death signal (the `biz_recent_dead_share` star metric). HK's Companies
   Registry is search-only (ICRIS), not bulk. **Workarounds:** (a) F&B-licence
   and business-registration open datasets as a partial churn proxy; (b) the
   same offline-scrape pattern SG used when OneMap was rate-limited; (c) ship
   without the churn family v1 and flag it. Don't fake it.
4. **No open passenger OD matrix.** SG's LTA OD fed daytime population,
   labour-shed, and mobility layers directly. HK doesn't publish trip-level OD.
   **Workarounds:** MTR station patronage (open) + the Transport Dept **Travel
   Characteristics Survey** as district-level priors + a gravity model over
   GTFS travel times. Document the assumption loudly (as SG did for Huff λ).
5. **Cantonese / Chinese place names.** POI matching, brand normalisation and
   LLM classification all assumed English-dominant text. Use a **CJK-aware
   embedding/LLM** for place classification and keep bilingual name fields;
   brand-sibling supervision (the chain trick for p1) still works — chains like
   Café de Coral, Maxim's, Fairwood, 759 Store, Watsons give *excellent*
   same-brand positive pairs.
6. **Rent granularity.** URA gave SG project-level transactions; RVD gives HK
   district/class indices. Your rent surface will be coarser — keep the IDW
   approach but flag lower resolution (SG already has a `rent_resolution` flag
   pattern to copy).
7. **Cross-boundary & islands.** Outlying islands (Lamma, Cheung Chau) and the
   Shenzhen border zone need the same "lived-hex" presence filter the SG apps
   use (drop cells with no resident/daytime/place signal) so empty water and
   border buffer don't appear as map clutter or fake twins.

---

## 6. Training replication (identical method, re-run)

Once `hex8hk_all_features.parquet` and the HK places table exist, the two
embeddings are **the same code with new inputs** — no redesign:

- **plexis-e1 (region, 256-d):** `embedding/` — SCARF corruption + view-masking,
  ship the hybrid (160 PCA + 96 contrastive). Re-run `run_program.py`.
- **plexis-p1 (place, 64-d):** `embedding_place/` — two towers
  (essence+micrograph vs context = frozen HK-e1 + 400 m mix), SCARF +
  **chain-sibling positives** (build the HK brand denylist: drop Octopus
  add-value points, ATMs, MTR exits-as-POIs; keep real chains) + cross-view.
  Re-run `run_program.py`.

**The exams transfer verbatim** — re-use `EMBEDDING_V5_DESIGN.md` and
`PLACE_EMBEDDING_DESIGN.md` check lists, **lock them before training HK**, and
let them decide ship/no-ship exactly as in SG. The forbidden-probe (rating
unpredictable) and the held-out chain-retrieval test are city-agnostic.
Re-point the archetype spot-checks to HK anchors you pick *before* training
(e.g. a Maxim's in a mall, a wet market in Sham Shui Po, a Central office
tower, a Tuen Mun public-estate shop).

Training cost will be similar (CPU, minutes) — the data is the same order of
magnitude.

---

## 7. Effort & sequencing (realistic)

| Phase | Work | Rough effort |
|---|---|---|
| A | Grid + boundaries + zone-type masking | 2–3 days |
| B | Population + buildings + land use (the dasymetric core) | 1 week (HK vertical gotcha) |
| C | Roads + transit (GTFS) + POI + micrograph | 1 week |
| D | S1–S11 derived metrics (mostly re-run; OD + churn need workarounds) | 1.5–2 weeks |
| E | Master + catalogs + checkpoint | 2–3 days |
| F | Train e1 + p1, run locked exams, iterate | 3–4 days |
| G | Stand up the 3 apps on HK data (mostly re-point) | 1 week |

**Critical path = the two gaps (OD matrix, business churn).** Decide early:
ship v1 without them (clean, honest) or invest in the workarounds. Everything
else is well-trodden.

---

## 8. What you literally copy from this repo

- All `build_*.py` and `validate_*.py` in `plexis-sgp-v5/` — re-point inputs.
- `embedding/` and `embedding_place/` — re-run as-is.
- The design + exam docs (`EMBEDDING_V5_DESIGN.md`, `PLACE_EMBEDDING_DESIGN.md`,
  `TEST_REGISTRY.md`) — the protocol is the product.
- The three apps (`apps/sg-pulse`, `apps/place-graph`, `apps/atlas-diary`) —
  swap the data folder, re-point Mapbox centre to 22.32°N, 114.17°E.
- `publish_checkpoint.py`, `build_catalog*.py` — versioning & metadata discipline.

Start a sibling directory `plexis-hkg-v1/` (mirror of `plexis-sgp-v5/`),
keep SG frozen as the reference, and the only files you write from scratch are
the HK source-ingestion adapters at the very bottom of the stack.

---

### Key HK data portals (bookmark these)
- **CSDI Portal** — portal.csdi.gov.hk (spatial data supermarket, 500+ sets)
- **DATA.GOV.HK** — data.gov.hk (transport, GTFS, stats, APIs)
- **C&SD** — census by TPU / Street Block; Travel Characteristics Survey
- **Planning Dept** — Outline Zoning Plans, land-use, land supply
- **Lands Dept** — boundaries, 3D buildings, Address Lookup Service
- **RVD** — Rating & Valuation Dept rent/price indices
- **MTR / Transport Dept** — patronage, future railway, real-time arrivals
