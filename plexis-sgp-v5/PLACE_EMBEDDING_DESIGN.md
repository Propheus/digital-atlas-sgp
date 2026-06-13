# Plexis-P v1 — per-place embedding (design locked BEFORE training)

2026-06-12. Companion to `EMBEDDING_V5_DESIGN.md` (hex8 plexis-e1).
Goal: every one of the 190,591 places gets a **small, usable embedding** such
that distance = *functional similarity of the place itself*: same kind of
venue, in the same kind of spatial context, with the same kind of micro-world
around it.

## Hard design rules (user-set)

1. **NO rating, NO review signals — anywhere.** Excluded from inputs AND from
   training signals: `rating`, `has_rating`, `reviews_count`, `has_reviews`,
   `review_bucket`, `review_quality_pctl_in_cat`, `magnet_strength`,
   `is_magnet`, `is_long_tail` (review-volume derived). The embedding is
   structural, not reputational. (Popularity can always be joined back ON TOP
   of the embedding by a product; it must not shape the geometry.)
2. Small and usable: **64 dimensions**, float32 (190,591 × 64 ≈ 49 MB),
   kNN-ready raw — same "use RAW, never re-standardize" rule as plexis-e1.
3. hex8 is the only context grain (hex9 internal-only, per project rule).

## Inputs — three blocks

| Block | Source | Features |
|---|---|---|
| **ESSENCE** (what it is) | `places/sgp_places_final.parquet` | `plexis_category` one-hot (24), `primary_category` hashed/grouped (~60 buckets), chain flag, brand-size bucket (independent / 2–4 / 5–19 / 20+ outlets) |
| **MICROGRAPH** (its 400/800 m world) | `places/sgp_places_micrograph.parquet` | all 19 `pmg_*`: competitors 400/800, closest competitor, complement counts + diversity, anchors + strength, walk-to-MRT/bus, hex walk/transit scores. EXCLUDE `pmg_competitor_rating_avg` (rating rule). |
| **SPATIAL CONTEXT** (where it sits) | `hex/hex8_embedding_plexis_e1_256d.parquet` | the validated hex8 e1 vector of its hex, FROZEN (no gradient into it), PCA-compressed to 64 before entering the tower; plus neighbour place-mix: bag-of-categories within 400 m (24 counts, log1p) |

Transforms as e1: log1p skewed counts → z-score → NaN→0 with indicator
channels (micrograph NaNs are real signal: isolated places).

## Architecture — two towers, contrastive

```
ESSENCE+MICROGRAPH ──► tower A (MLP 2×256) ─► 64d   ← THE embedding
CONTEXT (hex-e1 + mix) ► tower B (MLP 2×256) ─► 64d   ← thrown away after training
```

Training signal (InfoNCE, τ=0.5):
1. **SCARF self-corruption** on tower A inputs (mask 0.3) — base recipe,
   covers all 190K places.
2. **Chain-sibling positives** — two outlets of the same `brand_norm` are a
   positive pair. **Brand filter first**: drop unmanned utility pseudo-brands
   (iJooz, ATM/AXS, EV chargers, vending, parcel lockers — anything in a
   denylist built by eyeballing the top-50 brand list), require ≥5 staffed
   outlets, cap 50 sampled pairs per brand per epoch so 7-Eleven doesn't own
   the loss.
3. **Cross-view A↔B** — a place's essence+micrograph must agree with its
   context vector. This bakes *place-context fit* into the space.
4. **Hard negatives**: same category, far-apart context (and same hex,
   different category) sampled at 2× rate of random negatives.

Loss = weighted sum (1.0 / 0.5 / 0.5 / hard-negs inside each term).
CPU-feasible: ~190K × ~200 cols; e1's full program ran in 8 min on the server.

## The locked exam — 9 checks, thresholds fixed NOW

| # | Check | Pass bar |
|---|---|---|
| 1 | **Held-out chain retrieval**: hide 20% of outlets of each real chain (≥10 outlets); a held-out outlet's top-10 must contain a sibling | ≥70% of held-out outlets |
| 2 | Category kNN recovery (k=10 majority) | ≥80% |
| 3 | **Beyond-category structure**: within ONE category (cafes), kNN must beat random-same-category on micrograph similarity (anchor strength, complement diversity) | median neighbour |Δpmg-z| < random-pair baseline × 0.7 |
| 4 | Geography-leak cap: Spearman(embedding dist, metres) on random pairs | ρ ≤ 0.45 |
| 5 | NOT context-only: same-hex places must spread — mean within-hex pairwise dist ≥ 0.5 × global mean | ≥0.5× |
| 6 | Probe (RidgeCV on standardized Z — the e1 lesson): predict held-out `pmg_anchors_400m` and `pmg_walk_dist_mrt_m` | R² ≥ 0.5 / ≥ 0.6 |
| 7 | Probe must FAIL on a forbidden target: predicting `rating` from Z should be weak — proves the rating rule held | R² ≤ 0.15 |
| 8 | Seed stability, 3 seeds, Procrustes | ≥ 0.95 |
| 9 | Archetype spot-checks, hand-picked BEFORE training: a Ya Kun outlet → other kopi chains in malls; a void-deck clinic → other heartland clinics; a Duxton shophouse bar → other shophouse F&B; a Tuas canteen → other industrial canteens | 4/4 sane to a human |

Check 7 is the novel one: we *want* a near-zero score there. If rating is
predictable from a rating-free embedding, fine — that means structure explains
reputation — but it must come from structure, so the bar is on INPUTS, and
this check documents the leak level honestly.

## Failure protocol (e1 precedent)

The exam, not the loss curve, makes the ship/no-ship call. If pure contrastive
fails (as pure-neural did for hexes), the fallback ladder is:
hybrid (PCA-32 of tower-A inputs ⊕ 32 contrastive) → PCA-only → no-ship.

## Artifacts

- `places/place_embedding_plexis_p1_64d.parquet` (id + d0..d63)
- `embedding_place/` — prep.py, train.py, exam.py, runs.jsonl, PLEXIS_P1_REPORT.md
- catalog rows + dataset_catalog entry on ship (100%-described rule)

## Phased plan

1. **v0 — 50K showcase subset** (the places already in SG Pulse): fastest
   iteration loop, exam on this set first.
2. **v1 — full 190,591** with the same frozen exam.
3. Products after gating: "places like this" in SG Pulse Places tab; brand
   siting-DNA (mean context of a chain's outlets → rank empty hexes);
   misfit detection (place far from context expectation, cross-ref ACRA).

## What this is NOT

- Not a popularity model (rule 1).
- Not a demand model — `cap_*` (Huff) answers "how much"; this answers
  "what kind".
- Not text/semantic: no review text, no name NLP in v1 (name tokens are a
  v2 idea, kept out to keep the exam clean).
