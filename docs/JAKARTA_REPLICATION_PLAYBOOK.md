# Digital Atlas — Jakarta Replication Playbook

*Bridging the existing `da-jkt` build up to Singapore v5 parity: the missing
layers, the contrastive embeddings, and the locked-exam protocol. Written
2026-06-13 from the live SG pipeline (`plexis-sgp-v5/`) and the current state
of `rwm-server:~/da-jkt`.*

> **Server note:** the Jakarta data lives at **`rwm-server:~/da-jkt`** (6.6 GB,
> reachable, inspected for this plan). The alias **`da0jkt` did not resolve**
> from this machine — if it's a separate box, add it to `~/.ssh/config`;
> otherwise everything below assumes `rwm-server:~/da-jkt`.

---

## 0. Good news — Jakarta is NOT starting from zero

`da-jkt` is already a working **first-generation atlas** — roughly where
Singapore was at "v1", before the S1–S11 metrics and the contrastive
embeddings. What already exists on the server:

| Already built | Detail |
|---|---|
| **H3-8 grid** | 862 hex8 cells over DKI Jakarta (bbox −6.38/−6.08, 106.65/107.02) |
| **Foundation layers** | population, buildings (428 MB), roads (91 MB), places (414 MB), transit (TransJakarta + MRT + KRL), elevation, **flood**, landcover, nightlights (5.3 GB VIIRS) |
| **Feature table** | `data/features/hex_features.parquet` — **862 × 233** |
| **Admin hierarchy** | kota → kecamatan → kelurahan (Jakarta's region → PA → subzone) |
| **Jakarta-native features** | `kampung_score`, `formality_index`, `informal_ratio`, `flood_risk_proxy`, `dist_to_coast_km`, warung/warteg/warkop POI counts — the informal economy, already quantified |
| **A first embedding** | 32-d **autoencoder** (`model/features/hex_embeddings_32d.parquet` + `autoencoder.pt`) |
| **Scripts** | `step_00_h3_foundation.py`, `classify_places.py`, `download_overture.py`, `step_anchors_embeddings.py` |

**So this is a catch-up project, not a from-scratch build.** Two-thirds of the
foundation is done. The work is to add the derived-metric layers, replace the
autoencoder with the validated contrastive embedding, add the place embedding,
and wrap the whole thing in the locked-exam protocol.

---

## 1. The gap to Singapore v5 parity

| Capability | SG v5 | da-jkt today | Action |
|---|---|---|---|
| Grid + foundation | ✅ 1,191 hex8 | ✅ 862 hex8 | keep |
| Place micrograph (per-venue 400/800 m) | ✅ | ❌ | **build** |
| S1–S11 derived metrics | ✅ 11 layers | partial (basic indices only) | **build most** |
| Region embedding | ✅ plexis-e1 contrastive 256-d, 13-check exam | ⚠ 32-d autoencoder, no exam | **replace** |
| Place embedding | ✅ plexis-p1 64-d, 9-check exam | ❌ | **build** |
| Validation gates | ✅ 30 validators, signed ledger | ❌ | **add** |
| Catalogs + checkpoint | ✅ 100% described | partial (feature_catalog.csv) | **upgrade** |

The whole job is the four **build** / **replace** rows. Everything in §3–§6
maps onto reusable SG code.

---

## 2. The grid — already done, just formalise

Jakarta is already on **H3-8** with kelurahan/kecamatan/kota joins — the hard
part is finished. Two cleanups before going further:

- **Add `zone_type_broad`** per cell (residential / commercial / industrial /
  green / water / port / airport) to drive Not-Applicable masking — exactly as
  SG does for water catchment & military. Jakarta needs it for green space,
  the Thousand Islands, ports, and Soekarno–Hatta airport.
- **Decide the footprint: DKI Jakarta (current 862) vs Jabodetabek.** DKI alone
  misses the commuter belt (Bekasi, Depok, Tangerang, Bogor) that drives
  daytime population and labour-shed — the very metrics S3/S5 need. Recommend
  **DKI for v1** (matches existing data), Jabodetabek as a v2 expansion.

---

## 3. THE SOURCE MAP — Singapore → Jakarta

| Layer | Singapore source | **Jakarta / Indonesia source** | Status in da-jkt |
|---|---|---|---|
| **Open-data hub** | data.gov.sg | **Satu Data Indonesia** + **Jakarta Satu / Jakarta One Data** (DKI portal) + **BPS** (jakarta.bps.go.id) | — |
| **Boundaries** | OneMap subzones | **GADM / HDX** admin levels (kelurahan = L4); BPS wilayah | ✅ have |
| **Population** | SingStat dasymetric | **BPS Sensus Penduduk 2020 + Podes 2025** by kelurahan; dasymetrise on buildings. Global fallback: **WorldPop / GHS-POP** | ✅ have |
| **Buildings** | Overture+OSM+HDB | **Microsoft GlobalML (88M Indonesia footprints)** + **Overture/OSM** + HOT-OSM (Jakarta well-mapped) | ✅ have (428 MB) |
| **Land use / zoning** | URA Master Plan + GPR | **RDTR / RTRW** Jakarta spatial plans (Jakarta Satu); Bappeda zoning | ⚠ partial — **add** |
| **Roads** | LTA/OSM | **OSM** (Geofabrik Indonesia) — Jakarta densely mapped | ✅ have (91 MB) |
| **Transit (static)** | LTA DataMall + GTFS | **TransJakarta GTFS** (Transitland `f-transjakarta~id`, 236 routes/8,421 stops, incl. Mikrotrans) + **MRT Jakarta** + **KRL Commuterline (KAI)** + LRT | ✅ have (18 MB) — verify GTFS windows |
| **Places / POI** | Overture + LLM-classified | **Overture/OSM** + Google scrape; **classify in Bahasa Indonesia** (warung, warteg, kaki lima…) | ✅ have (414 MB) |
| **Place micrograph** | per-venue 400/800 m | — | ❌ **build** (`build_place_micrograph.py`) |
| **Business registry** | ACRA bulk (2.07 M) | ⚠ **OSS/NIB** (online single submission) not bulk-open; **no churn feed** | ❌ gap — see §5 |
| **Rent / price** | URA + HDB resale | **No open transaction registry**; proxy via **listing scrapes** (Rumah123, Lamudi) + BPS rent index | ❌ gap — see §5 |
| **Night lights** | VIIRS | **VIIRS** — identical, global | ✅ have (5.3 GB) |
| **Flood / elevation** | *(SG has none)* | **DKI flood hazard maps + DEM/subsidence** — Jakarta-specific, **already ingested** | ✅ have — a Jakarta advantage |
| **Future pipeline** | URA MP2019 rail | **MRT Jakarta Phase 2/3 + LRT Jabodebek + RDTR** planned zones | ⚠ **add** |
| **Origin-Destination** | LTA OD matrix | ⚠ **No open passenger OD**; proxy via TransJakarta tap data (if obtainable) + commuter survey | ❌ gap — see §5 |

---

## 4. Build order — what to add, in dependency sequence

Re-use the SG `build_*.py` / `validate_*.py` templates; re-point inputs to
`da-jkt/data/`. Run one layer at a time, gate before proceeding.

**Phase 1 — formalise foundation (mostly done)**
- `zone_type_broad` tagging + Not-Applicable masking · re-validate population
  conservation against BPS totals · confirm GTFS time-windows
  (`build_gtfs_windows.py`).

**Phase 2 — place micrograph (new, unlocks p1 later)**
- `build_place_micrograph.py` → per-venue rivals/complements/anchors/transit
  within 400/800 m, on the existing 414 MB places.

**Phase 3 — S1–S11 derived metrics (the bulk of the work)**
Order as SG: S1 Huff capture · S2a walk isochrones · S2b transit isochrones
(TransJakarta+MRT+KRL graph) · S3 daytime population · S4 business
churn *(gap — §5)* · S5 labour shed · S6 co-location lift · S7 micro-visibility
· S8 rent surface *(gap — §5)* · S9 future pipeline · S10 context pack ·
S11 mobility pack. Each has a SG `build_` + `validate_` to copy.

**Phase 4 — assemble & catalog**
- `build_all_features.py` → `hex8jkt_all_features.parquet` (replaces the 233-col
  table with the full SG-parity set) · `build_catalog*.py` (100% described) ·
  `publish_checkpoint.py` (VERSION = a JKT tag).

---

## 5. Jakarta gotchas (where SG — and even HK — assumptions break)

1. **The informal economy is the main event — and you already measure it.**
   `kampung_score`, `formality_index`, `informal_ratio`, warung/warteg counts
   are *Jakarta's killer features* and have no SG equivalent. Keep them as
   first-class inputs to the embedding; they'll dominate the WHAT/WHERE views
   and are exactly the structure the contrastive model should learn. This is
   Jakarta's version of SG's "covered linkways" — the most-local signal.
2. **Flooding + land subsidence are structural, not noise.** SG has no flood
   layer; Jakarta already has `flood_risk_proxy` + DEM + `dist_to_coast_km`.
   North Jakarta is sinking ~10 cm/yr — make flood/elevation first-class, and
   consider a "subsidence trajectory" the way SG does new-town trajectory.
3. **No business-churn registry.** ACRA gave SG `biz_recent_dead_share` (a star
   metric). Indonesia's OSS/NIB isn't bulk-open and has no death signal.
   **Workarounds:** POI presence-vs-absence over time (re-scrape), or ship v1
   without the churn family and flag it (as the HK plan also does). Don't fake it.
4. **No open rent/price transactions.** URA/HDB gave SG a real price surface.
   Jakarta: scrape listing portals (Rumah123/Lamudi) for an asking-price IDW
   surface, flag it as asking-not-transaction, keep SG's `rent_resolution`
   flag pattern.
5. **No open OD matrix.** Feeds SG's daytime-pop, labour-shed, mobility layers.
   Jakarta: build a gravity model over the GTFS travel-time graph; if
   TransJakarta tap-card aggregates can be obtained, use them as priors.
   Document loudly (as SG did for Huff λ).
6. **Bahasa, not English.** POI classification, brand normalisation and LLM
   labelling must run in Indonesian (warung makan, warteg, kaki lima, pasar,
   ruko). Chain-sibling supervision for p1 still works beautifully — Indomaret,
   Alfamart (tens of thousands of outlets!), Warung Tegal franchises, KFC,
   J.CO, Kopi Kenangan give enormous same-brand positive-pair pools.
7. **DKI vs Jabodetabek.** The metro spills far past DKI's 862 cells. v1 on DKI
   is honest and matches the data; note the commuter-belt truncation in any
   daytime-population claim.

---

## 6. Training — replace the autoencoder, add the place model, lock the exams

The current 32-d autoencoder is the *pre-contrastive* generation. Upgrade to
the validated SG method — same code, Jakarta inputs:

- **Region (replace):** stand up **plexis-e1** (`embedding/`) — SCARF
  corruption + view-masking, ship the hybrid (PCA + contrastive). Re-run
  `run_program.py` on `hex8jkt_all_features.parquet`. Expect 256-d (or scale
  to dim by feature count; 862 cells is fine for CPU).
- **Place (new):** build **plexis-p1** (`embedding_place/`) — two towers
  (essence+micrograph vs context = frozen JKT-e1 + 400 m mix), SCARF +
  **chain-sibling positives** (build the Jakarta brand denylist: drop GoTo/OVO
  top-up points, ATM-only nodes, gerbang tol; keep Indomaret/Alfamart/etc) +
  cross-view. Re-run `run_program.py`.
- **Lock the exams BEFORE training** — re-use `EMBEDDING_V5_DESIGN.md` and
  `PLACE_EMBEDDING_DESIGN.md` check lists verbatim. The forbidden-probe (rating
  unpredictable — and Jakarta should *also* exclude ratings) and held-out
  chain-retrieval are city-agnostic. Pick Jakarta archetype anchors *before*
  training: a warteg in a kampung, a mall in SCBD/Sudirman, a pasar in Tanah
  Abang, a KRL-station shophouse cluster, a North-Jakarta flood-prone strip.

---

## 7. Effort & sequencing

| Phase | Work | Effort |
|---|---|---|
| 1 | Formalise foundation: zone-type mask, re-validate pop, GTFS windows | 2–3 days |
| 2 | Place micrograph | 2 days |
| 3 | S1–S11 derived metrics (most of the work; OD/churn/rent need workarounds) | 2–2.5 weeks |
| 4 | Master table + catalogs + checkpoint | 2–3 days |
| 5 | Train e1 (replace AE) + p1, lock + run exams | 3–4 days |
| 6 | Stand up the 3 apps on JKT data (re-point Mapbox to −6.20, 106.85) | 1 week |

**Critical path = the three data gaps (OD, business churn, rent).** Decide
early: ship v1 without them (clean, honest, and Jakarta still has flood +
informal-economy signals SG lacks) or invest in scrape/proxy workarounds.

---

## 8. What you copy from this repo

- All `build_*.py` / `validate_*.py` in `plexis-sgp-v5/` — re-point to `da-jkt/data/`.
- `embedding/` + `embedding_place/` — re-run as-is (replaces the 32-d AE).
- Design + exam docs (`EMBEDDING_V5_DESIGN.md`, `PLACE_EMBEDDING_DESIGN.md`,
  `TEST_REGISTRY.md`) — the protocol is the product; lock before training JKT.
- The three apps (`apps/sg-pulse`, `apps/place-graph`, `apps/atlas-diary`) —
  swap the data folder, re-point Mapbox centre to **−6.20°S, 106.85°E**.
- `publish_checkpoint.py`, `build_catalog*.py` — versioning + metadata.

Suggested layout: keep `rwm-server:~/da-jkt` as the data home, add a
`da-jkt/plexis-jkt-v1/` mirroring `plexis-sgp-v5/` for the build scripts +
embeddings + catalogs, so Jakarta gets the same disciplined, versioned
structure SG has.

### Key Jakarta / Indonesia portals
- **Jakarta Satu / Jakarta One Data** — DKI provincial open-data + spatial (RDTR)
- **Satu Data Indonesia** — national open-data portal
- **BPS** — jakarta.bps.go.id (census, Podes, by kelurahan)
- **Transitland** — `f-transjakarta~id` GTFS; **MRT Jakarta**, **KAI Commuter** feeds
- **Geofabrik / HOT-OSM** — Indonesia OSM extracts (roads, POI, buildings)
- **Microsoft GlobalML Building Footprints** — 88 M Indonesia polygons
