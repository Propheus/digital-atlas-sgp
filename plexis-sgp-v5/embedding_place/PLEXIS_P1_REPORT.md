# Plexis-P1 — per-place embedding: training + exam report

2026-06-12 · design locked BEFORE training in `../PLACE_EMBEDDING_DESIGN.md`
· trained on azold (16-core CPU, screen `plexis-p1`) · log `program.log`,
ledger `runs.jsonl`.

## What shipped

`places/place_embedding_plexis_p1_64d.parquet` — **190,591 places × 64d**
(float32, L2-normalized; **use RAW**, never re-standardize per-dim — the
plexis-e1 lesson). Distance = functional similarity of the place: same kind
of venue, in the same kind of spatial context, with the same micro-world.

**The hard rule held: zero rating/review signal.** Excluded from inputs and
training: rating, reviews_count, review buckets, magnet flags,
pmg_competitor_rating_avg. Audited by exam check 7 (below).

## Inputs

| Tower | Features |
|---|---|
| A — essence + micrograph (THE embedding) | 108 cols: plexis_category (24) + primary_category top-60 + chain flag + brand-size bucket + 18 `pmg_*` (no rating col) + NaN indicators |
| B — context (discarded after training) | 89 cols: frozen hex8 plexis-e1 PCA-64 (95.0% var) + 400 m neighbour category mix (24) + hex-missing flag |

Chain-sibling positives: 17,046 pairs from 203 real brands (≥5 staffed
outlets). Denylist removed 6,242 unmanned outlets (iJooz, ATM networks,
EV charging, lockers, vending, MBS-internal). 1,648 outlets (20% of every
≥10-outlet chain) hidden from training for exam check 1.

## Training

Two towers (MLP 2×256→64), InfoNCE τ=0.5:
scarf(mask 0.3) ×1.0 + chain pairs ×0.5 + cross-view A↔B ×0.5.
Hard negatives by batch construction (half of each 1024-batch = same-category
quads). Adam 1e-3, wd 1e-5.

| Stage | Data | Seeds | Epochs | Time |
|---|---|---|---|---|
| V0 | random 50K | 3 | 30 | 21 s/seed |
| FULL | 190,591 | 3 | 20 | 52 s/seed |

## The locked exam — FULL results (seed 0), 9/9 PASS

| # | Check | Bar | Score | |
|---|---|---|---|---|
| 1 | Held-out chain retrieval (1,648 outlets, top-10 finds sibling) | ≥0.70 | **0.814** | ✅ |
| 2 | Category kNN majority (k=10) | ≥0.80 | **0.997** | ✅ |
| 3 | Beyond-category: cafe neighbours' micrograph gap vs random cafes | ≤0.70 | **0.157** | ✅ |
| 4 | Geography leak ρ(emb dist, metres) | ≤0.45 | **0.077** | ✅ |
| 5 | Same-hex spread vs global | ≥0.50 | **0.640** | ✅ |
| 6a | Probe pmg_anchors_400m (RidgeCV, standardized Z) | ≥0.50 | **0.775** | ✅ |
| 6b | Probe pmg_walk_dist_mrt_m | ≥0.60 | **0.809** | ✅ |
| 7 | **Forbidden probe — rating must be UNpredictable** | ≤0.15 | **0.094** | ✅ |
| 8 | Seed stability (Procrustes, 3 seeds) | ≥0.95 | **0.979 / 0.981** | ✅ |
| 9 | Archetype spot-checks (picked pre-training) | 4/4 | **4/4, 5/5 same-cat each** | ✅ |

V0 (50K) passed first try as well (chain 0.786, full table in
`exam_Z_v0_s0.json`) — no failure-ladder fallback needed.

### Archetype neighbours (check 9, human-readable)

- **Ya Kun (Holland Village)** → kopi/cafe chains in AMK Town Centre, Jelebu
  (Bukit Panjang mall), Moulmein
- **TCM clinic (AMK Town Centre)** → heartland clinics in Telok Blangah Drive,
  Geylang East, Tampines East
- **The Lions Den (Chinatown bar)** → three more Chinatown shophouse bars
- **Seatrium Canteen (Pioneer)** → industrial canteens in Samulun, Seletar
  Aerospace Park, Jurong River

## Reading the numbers honestly

- Check 1 at 0.814 means: for 4 in 5 never-paired chain outlets, the model
  re-discovers a sibling among 190K candidates from structure alone.
- Check 4 at 0.077: "similar" is NOT "nearby" — twins span the island.
- Check 7 at 0.094: reputation is near-unrecoverable from the embedding,
  so the geometry cannot be a popularity ranking in disguise.
- Check 2 at 0.997 is *expected* to be high (category is an input); the
  informative part is check 3: within one category, neighbours share
  micro-context far beyond chance (0.157 vs 0.70 bar).

## Artifacts

- `places/place_embedding_plexis_p1_64d.parquet` (local + azold v5)
- `embedding_place/`: prep.py, train.py, exam.py, run_program.py,
  Z_p1_s{0,1,2}.npy (+.pt encoders), exam_*.json, runs.jsonl, program.log
- catalog: `embedding_catalog.json` (14 embeddings), dataset_catalog row
- Predecessors `place_embedding_what_64d` / `combined_128d` (v4 PCA) remain
  catalogued but P1 supersedes them for products.
