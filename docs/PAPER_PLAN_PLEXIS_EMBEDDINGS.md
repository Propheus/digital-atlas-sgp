# Paper plan — "Region2Vec + Place2Vec via contrastive training: the structure of Singapore"

2026-06-13. Working plan for a methods paper covering plexis-e1 (hex8) and
plexis-p1 (places). Status: literature swept, contributions drafted,
experiment gaps identified. NOT yet written.

## Working titles

1. **"Audited City Fingerprints: Validation-First Contrastive Embeddings of
   Regions and Places, with Singapore as a Complete Worked Example"**
2. "What a Place Is, Not How Loved It Is: Popularity-Free Contrastive
   Embeddings of 190,591 Places and 1,191 Regions"
3. "The Exam Comes First: Locked-Harness Evaluation for Urban Representation
   Learning" (short/position-paper variant)

## The pitch (abstract draft, one paragraph)

Urban representation learning has produced a family of region and place
embeddings (Place2Vec, Hex2Vec, GeoVeX, RegionDCL, multi-view contrastive
methods), but three habits weaken the field: evaluation is designed after
training (and often circular — predicting inputs back), popularity signals
leak into geometry, and global structure is rarely audited. We present a
validation-first protocol: a battery of falsifiable checks — including checks
designed to FAIL (a forbidden probe) — locked before any training, which
makes the ship/no-ship decision instead of the loss. Applying it at two
scales of one city built on an exhaustively validated feature base (801
region features; 190,591 places), we contribute: (1) **chain-sibling natural
supervision** — outlets of the same brand as ground-truth positive pairs, and
held-out chain retrieval as an external, non-circular benchmark (0.814 over
190K candidates); (2) a **popularity-free place embedding** with an audited
guarantee that ratings are unrecoverable (R²=0.094); (3) an empirical caution:
the pure contrastive model scored best on probes yet collapsed global
geometry (opposite districts drawn together) and was rejected by the locked
harness — a hybrid of classical and contrastive dimensions passes everything;
(4) external validity: the embeddings independently re-derive a
government-documented supermarket desert three different ways. All data,
exams and interactive demonstrations are released.

## Claimable contributions (checked against prior work)

| # | Claim | Why it's defensible |
|---|---|---|
| C1 | **Locked-exam protocol** (exam frozen pre-training, incl. forbidden probe + opposites-apart + leave-one-family-out) as a first-class method | Surveys note evaluation weakness; no urban-embedding paper we found locks falsifiable checks before training or reports rejecting its best-scoring model |
| C2 | **Chain siblings as natural supervision + held-out chain retrieval benchmark** | Closest prior art is place *deduplication* (same physical venue) — different task. Nothing found using brand outlets as functional-similarity ground truth |
| C3 | **Popularity-free guarantee, audited** | Prior place embeddings happily ingest check-ins/ratings; none we found *prove* reputation is absent from the geometry |
| C4 | **Hybrid > pure-neural finding** (global-geometry collapse under InfoNCE on tabular urban data) | Echoes known dimensional-collapse issues but documented here on city data with a concrete failure (Tuas↔Orchard p32) and a fix (160 PCA + 96 contrastive, Procrustes .987) |
| C5 | **Two-scale coherence**: the place model consumes the frozen region model (cross-view tower), giving composable region→place reasoning | Multi-view region papers fuse views *within* a scale; coupling across scales with a frozen validated base is unusual |
| C6 | **External replication as validation**: Yunnan desert re-derived by capture model, by unserved-demand metric, and by twin-ghost logic | "Model never saw the study" triangulation is a stronger validity argument than benchmark R² alone |

## Related-work map (citations to use)

- **Place level**: Place2Vec (Yan et al., SIGSPATIAL 2017 — POI-type
  co-occurrence); POI2Vec; place dedup embeddings (Yang et al. 2019);
  multi-modal contrastive POI urban-space embeddings (Wang et al., CEUS 2025);
  mobility-embedded POIs (2026); training-free POI-graph representations (2025).
- **Region level**: Hex2Vec (Woźniak & Szymański 2021 — H3 + OSM tags, skip-gram);
  GeoVeX (2023 — hexagonal ZIP autoencoder); **RegionDCL (Li et al., KDD 2023 —
  building-footprint contrastive, evaluated ON SINGAPORE — our natural baseline)**;
  Region2Vec / MGFN multi-graph (CIKM 2022); ReCP multi-view contrastive
  prediction (AAAI 2024); Demo2Vec (2024); UrbanCLIP (2024); CGAP; HyperRegion;
  FlexiReg (2025); UrbanVerse (2026).
- **Foundation-model adjacent**: SatCLIP, GeoCLIP, AlphaEarth, PDFM —
  satellite/coordinate-anchored; we are *attribute-anchored* (what the city
  contains, not what it looks like from above) — positioning paragraph.
- **Tabular contrastive machinery**: SCARF (Bahri et al., ICLR 2022) — our
  corruption view; InfoNCE/SimCLR; CLIP-style cross-view; SupCon (chain loss
  is SupCon-flavoured with brands as labels).
- **Surveys**: Self-Supervised Representation Learning for Geospatial Objects
  (2024, arXiv 2408.12133); urban region representation learning surveys.

## Paper structure

1. Intro — the three bad habits; validation-first thesis; Singapore as the
   complete worked example (atlas: 64/64 gates, 2,735 described features).
2. Related work (map above).
3. The feature substrate (brief; cite atlas reports; 5 views WHO/WHERE/WHAT/FLOW/PRICE).
4. Method A — region2vec (plexis-e1): SCARF + view-masking; hybrid construction.
5. Method B — place2vec (plexis-p1): two towers; essence+micrograph vs
   context (frozen e1 + 400 m mix); chain-sibling positives w/ denylist +
   per-brand caps; hard-negative batch composition; the no-rating rule.
6. **The locked exam** — full check tables for both models, thresholds,
   and the protocol rules (lock before training; harness decides; forbidden
   probe; failure ladder). This is the heart of the paper.
7. Results — exams passed; pure-neural failure post-mortem; baselines
   (see gaps); downstream probes; qualitative atlas figures.
8. Applications & external validity — twins/rollout, rent benchmarking,
   ghost maps, misfits; Yunnan triple-derivation; the three public apps.
9. Limitations — single city; no trajectory/mobility data at place level;
   brand supervision sparse (8,797 outlets); UMAP figures are illustrative,
   not evidential; hex8-only grain.

## Experiments we already have vs. must add

**Have (in repo, reproducible):** both exams w/ JSONs; 3-seed stability;
hybrid-ratio sweep (Z_hybrid_160_96 vs 192_64 etc.); pure vs PCA vs hybrid
scoreboard; per-view dominance rho analysis; probe suite; archetype panels;
chain holdout retrieval; runs.jsonl timing (8-min / 52-s training).

**Must add for review-proofing (ranked):**
1. **Baselines on identical tasks**: Hex2Vec, GeoVeX (srai library makes both
   cheap) and RegionDCL (authors' code; already Singapore-tuned) on our probe
   tasks + twins quality. Place level: Place2Vec-style category-context
   baseline + the v4 PCA embeddings (already have).
2. **Leave-one-family-out** retrains for e1 (deferred check #12 — the one
   honest gap in the harness).
3. Ablations for p1: drop chain loss / drop cross-view / mask-rate sweep —
   each vs the exam (the natural ablation table IS the exam).
4. Transfer sanity: train p1 on West-of-island, exam on East (spatial holdout).
5. Optional reviewer-pleaser: one more city is out of scope — say so plainly
   and lean on RegionDCL's Singapore numbers for comparability.

## Figures (mostly already exist)

F1 protocol diagram (exam-first pipeline) · F2 scoreboard table (PCA/pure/hybrid
× checks, the FAILED cell highlighted) · F3 galaxy UMAP w/ named clusters +
geo-rainbow counterfactual · F4 twin star on map (Toa Payoh) + why-traits ·
F5 chain-retrieval curve (top-k) · F6 Yunnan triple-derivation panel ·
F7 misfit examples · F8 LOFO/ablation deltas.

## Venue options

- **ACM SIGSPATIAL** (methods + city scale; RegionDCL/Place2Vec lineage) — best fit.
- **Computers, Environment and Urban Systems** (urban analytics audience;
  validation-first angle lands well) — strong second.
- KDD ADS track (applied) / WWW; **EPB: Urban Analytics and City Science** for
  a more planning-flavoured rewrite; NeurIPS D&B if we package the exam +
  atlas as a benchmark ("SG-Bench") — bigger lift, biggest upside.

## Next actions (when user says go)

1. srai baselines (hex2vec, GeoVeX) on e1's probe tasks — 1 day.
2. RegionDCL baseline — 1–2 days (their Singapore configs).
3. LOFO program for e1 (5 retrains × exam) — half a day on azold.
4. p1 ablation table (4 retrains × exam) — half a day.
5. Draft sections 4–7 from the existing reports (much is written).
