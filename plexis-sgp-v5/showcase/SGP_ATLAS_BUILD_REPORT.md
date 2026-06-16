# Building a Digital Atlas for Singapore

*A technical report on `plexis-sgp-v5` — the multi-domain location-intelligence
atlas for Singapore. 1,191 H3-8 cells × 801 features, 190,591 places, two
contrastive embeddings, five domain packs, review-free, exam-gated.*

---

## 1. What it is, and why

The Singapore atlas turns the whole island — 6.04 million residents and workers,
every HDB town and landed enclave, the CBD, the industrial west, the nature north,
190,591 venues — into a single, queryable grid where every ~0.74 km² cell carries
**801 features** describing who lives there, what's built, what's around, how
reachable it is, how commercial it is, where it's growing, and what it's worth for
retail, real estate, utilities, transport or risk.

It is the **reference build** the sibling Jakarta atlas was later cut to parity
with — but Singapore-native throughout: URA Master Plan land use, HDB resale,
LTA DataMall transit and origin-destination, ACRA business formation, NEA hawker
centres, and a planning-zone discipline where non-residential land (industrial,
airport, catchment, islands, future) is marked *Not Applicable*, never scored as
"poor".

**Three locked decisions** shaped the build:
- **Grid:** H3 resolution 8 as the product scale (1,191 cells, ~0.74 km² each).
  A res-9 grid (7,318 cells) exists for fine work but is **not used in the shipped
  products**.
- **Footprint:** the full island and its populated offshore, dissolved from the
  URA Master Plan 2019 subzone layer (332 subzones; 270 carry population).
- **Honesty rule:** ship without the feeds Singapore doesn't open — commercial
  rent transactions, private-property prices, time-of-day origin-destination,
  crime — flagged rather than faked.

A hard rule ran through everything: **no review leakage.** Ratings and review
counts are never model inputs; they exist only as a probe the embeddings must
*fail* to predict.

---

## 2. The grid

The footprint is the URA Master Plan 2019 hierarchy: **5 regions, 55 planning
areas, 332 subzones**, dissolved to the Singapore land outline. Filling it with
H3 res-8 cells yields **1,191 hexes**, each joined to its subzone / planning area /
region, tagged with a `zone_type_broad` (residential / commercial / industrial /
nature / airport / islands / future), and carrying centroid and polygon geometry
for mapping.

Population resolves to **270 populated subzones**; the remaining subzones are
genuinely non-residential and are carried but flagged Not-Applicable so the
adequacy and domain scores never penalise an airport or a reservoir for "having
no clinics".

---

## 3. Data foundation

| Layer | Source | Scale |
|---|---|---|
| Population + demographics | **SingStat / Dept of Statistics** + HDB dwelling counts | resident 4.18 M, total 6.04 M, dorm/non-resident split |
| Land use | **URA Master Plan 2019** | 22 land-use fractions per hex |
| Buildings | **Overture + OneMap** | footprints, height, GFA, high-rise count |
| Roads | **Overture / OSM** | length by class, intersection density, betweenness |
| Transit | **LTA DataMall + GTFS** | MRT/LRT stations, exits, headways, bus stops |
| Origin–destination | **LTA DataMall passenger-volume OD** | throughput, commute reach |
| Places / POI | **Google + OSM + Overture union** | **190,591** classified venues |
| Amenities | **data.gov.sg** | hawker centres, CHAS clinics, schools, parks |
| Business formation | **ACRA** | new + struck-off entities (churn) |
| Night-lights | **VIIRS** | radiance composite, commercial-activity index |
| Satellite | **Sentinel / NDVI** | greenness, built-up, change |
| Resale prices | **HDB resale transactions** | psf, lease-remaining, by flat type |

**Population validates against the census:** atlas resident total **4.18 M** vs
SingStat ~4.18 M, and island total **6.04 M** vs the ~6.04 M mid-year figure — a
clean match. Daytime population (a conserving redistribution by workplace pull)
totals **4.19 M**, a 1.00 day/night ratio at the island scale with strong local
inflow into the CBD and industrial west.

---

## 4. The feature stack — 801 per hex

Features are organised into ~30 families spanning five "views":
**WHO** (population, demographics, daytime), **WHERE** (land use, buildings,
roads, distances, terrain/satellite), **WHAT** (places/POI composition,
micrograph context, amenities, business formation), **FLOW** (transit, walk and
transit isochrones, walkability, mobility/OD, accessibility), and **ECON**
(rent/resale surface, Huff capture, saturation/whitespace gaps, co-location fit,
development pipeline, composites). A large share are **place-derived** — aggregated
from the 190,591 venues and amenity/station points up to the hex.

**Descriptive foundation**
- *Population & demographics* — resident / HDB / non-resident / dorm split, age
  bands (`pop_0_14`, `pop_15_64`, `pop_65plus`), dependency and elderly shares.
- *Land use* — 22 URA fractions (`lu_residential_pct`, `lu_business_pct`, …).
- *Buildings* — footprint, height, gross floor area, high-rise count, density.
- *Roads & topology* — length by class, intersection density per km², through-traffic
  betweenness, distance to arterials.
- *Transit & rail* — MRT/LRT station and exit counts, interchange flags, distances,
  a composite `transit_score`.

**Derived & behavioural**
- *Isochrones* — walk-10-min and transit-15-min reach (population, places, jobs).
- *Walkability & 15-min city* — pedestrian network + an adequacy `min15` score.
- *Mobility & OD* — LTA passenger-volume throughput, destinations reachable in
  45 min, transit-desert priority.
- *Huff capture* `cap_*` — count-based, **review-free** capturable demand in
  outlet-equivalents, per category.
- *Saturation & whitespace* — POIs per 1,000 residents + demand-vs-supply `gap_*`
  and per-category `iso_walk10_unserved_pop_*`.
- *Spatial context* — k=1 / k=2 ring means and gradients of the key signals.
- *Composites* — vibrancy, livability, family, adequacy, vulnerability indices.

Validation: a per-stage QA battery (population conservation, coverage, no dead
columns, zone-type integrity, archetype/transit spot-checks) plus web-checks
against SingStat, LTA and URA. The v5.4.0 checkpoint records **every stage PASS**.

---

## 5. The scale of places, and the place layer

The atlas carries **190,591 Singapore venues**, classified to a clean category
taxonomy with brand detection. From these, each commercial venue gets a per-venue
**micrograph** — a compact description of its local context:
- *Local context* — venues, rivals, F&B / retail / service counts and category
  entropy in the 400 / 800 m neighbourhood.
- *Anchors & competition* — distance to MRT, hawker pressure, same-category rivals,
  co-tenant minimarts / supermarkets nearby.

This per-venue layer is what the place embedding (p1) learns from.

---

## 6. Domain packs — five sellable verticals

On top of the 801-feature hex grid sit **five domain packs** — Retail, Real Estate,
Public Utilities, Transport, and Insurance & Risk — each turning the existing
validated features into the **one number a buyer pays for**, plus sub-scores and a
pop-weighted subzone rollup. 22 shared primitives + **39 hero scores**, all derived
with **zero new data collection**.

The packs are Singapore-correct, not a template:
- **Retail** whitespace uses real unserved-population variance (`gap_<cat>` reads
  ~0.84 island-wide, so it is *additively* blended with `iso_walk10_unserved_pop`
  and Huff `cap` — products collapse when a factor is flat).
- **Real estate** v1 is HDB-resale + residential-rent + development feasibility
  (FAR headroom); private-unit AVM is explicitly a v2 behind paywalled prices.
- **Insurance** is hazard stratification, not actuarial pricing — and where a peril
  has no open SG feed (crime/theft) it is *omitted, not proxied*.

Known-answer checks pass: RE feasibility tops **Tengah**, transit-desert tops
**Jurong West / Choa Chu Kang**, retail whitespace tops **Jurong West**, and the
insurance business-interruption score tracks the validated `biz_recent_dead_share`
at ρ = 0.99.

---

## 7. Embeddings & contrastive training

Two embeddings turn the feature tables into similarity geometry — *find places
behaviourally like this one*, anywhere on the island.

### 7.1 What and why contrastive

Both embeddings are trained **contrastively** rather than by PCA, because the goal
is a *similarity metric* (nearby = same kind of place) not variance reconstruction.
PCA was computed only as a baseline yardstick — never shipped.

### 7.2 Architecture (and a deliberate non-choice)

Both encoders are **2-layer MLPs**:
`Linear → LayerNorm → GELU → Dropout → Linear` with a projection head for InfoNCE
and a decoder for denoising reconstruction. There is **no attention and no
transformer** anywhere — the input is a fixed-length tabular vector per cell /
venue, spatial context already enters as ring features, and the bottleneck is
*information* (brand / name / review are excluded by design), not model capacity.

### 7.3 e1 — the region embedding (hex8, 256-d)

- **Inputs:** review-free numeric features (the no-leak list excluded).
- **Objective:** **SCARF** feature-corruption + whole-view masking (zero an entire
  WHO/WHERE/WHAT/FLOW/ECON view so the encoder must infer it from the others) +
  denoising reconstruction; InfoNCE in-batch negatives.
- **The exam (frozen before training):**
  - *twin hit-rate* **1.0** — every hand-labelled analog pair (Toa-Payoh-mature,
    CBD-core, Tengah-newtown, Tuas-industrial, Yishun-heartland) retrieves its twin.
  - *probes* — HDB-psm R² **0.81**, origin-destination R² **0.90**, adequacy R²
    **0.93** (the geometry carries real structure).
  - *forbidden / negative-control probe* → **−0.01** (ratings unrecoverable — the
    no-leak promise is provably kept) — **the ship gate**.
  - *stability* (2-seed Procrustes) **0.987**, distance rank-corr **0.94**.

### 7.4 p1 — the place embedding (venue, 64-d)

- **Inputs:** category + the per-venue micrograph + a down-weighted slice of the
  hex's e1 context, so place *type* and local *texture* drive the embedding, not
  "which neighbourhood".
- **Supervision:** SCARF self-positives **plus chain-sibling positives** — two
  outlets of the same chain are a positive pair.
- **The exam (9/9 pass):** chain retrieval **0.814**, category-kNN purity **0.997**,
  geo-leakage ρ **0.077** (low), same-hex spread **0.64**, anchor / MRT probes R²
  **0.78 / 0.81**, *forbidden rating* R² **0.094** (unrecoverable), stability
  **0.98**, and named-archetype neighbourhoods that read true (Ya-Kun-kopi chain,
  heartland TCM clinics, shophouse bars).

### 7.5 The exam protocol

The discipline throughout: **write the test before training, freeze it, and let the
marks decide.** Every embedding ships only on passing its locked exam — and the
forbidden-rating probe is a test the model must *fail* on purpose, which is the
proof the no-review-leak rule is real and not just a claim.

---

## 8. From atlas to applications

The atlas is a working platform, not just a feature dump:
- **Three live apps** — *SG Pulse* (day-night city engine), *Places Constellation*
  (the 190 K-venue p1 galaxy + twin retrieval), and *Atlas Diary* (ten embedding
  use-cases answered live on the map).
- **Five domain packs** — site scoring, feasibility, load, access and risk as one
  number per hex, with subzone rollups.
- **Twin search** — cosine similarity in e1 (hex) or p1 (place) finds analog
  micro-markets and venues anywhere on the island.
- **A tool-using reasoner** (in progress) — Plexis-Reasoner learns to *operate* the
  atlas through a 21-tool action layer, with the domain packs as its vocabularies.

---

## 9. Honest gaps

- **No open SG feed** for commercial-rent transactions, private-property prices,
  time-of-day origin-destination, or crime — shipped without, flagged. (Retail rent
  uses a residential proxy until a commercial-rent surface lands; private-unit AVM
  is RE v2.)
- **Climate** — flood and heat are Phase 3 new work (`lu_water_pct` is only a weak
  coastal proxy today).
- **Res-9 grid** exists (7,318 cells) but is intentionally not used in the shipped
  products.
- Three pack scores are honest *re-framings* of an existing column (waste ∝
  population, business-interruption ≈ `biz_recent_dead_share`, mobility-access ≈
  adequacy) — documented in each pack's catalog limits, not presented as new signal.

---

## 10. Reproducibility & status

- **1,191 hex8 × 801 base features (+ 39 domain-pack scores folded in → 840 cols) ·
  190,591 places · e1 256-d + p1 64-d · per-stage QA all PASS · web-validated**
  against SingStat / LTA / URA. Frozen checkpoint **`v5.5.0`**.
- Training is seed-deterministic; the whole pipeline re-runs from `plexis-sgp-v5/`.
- **Where it lives:** `azold-test-server:~/da-sgp/v5/` (authoritative) · local
  `plexis-sgp-v5/` · `github.com/Propheus/digital-atlas-sgp` (parquets via Git LFS).

*The exam decided what shipped, not us. Everything review-free. Every gap flagged,
not faked.*
