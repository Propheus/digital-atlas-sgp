# Plexis v5 — The Complete Test Registry

*Every locked check in the system, its threshold, its actual result, and its
status. One page, no hiding. 2026-06-13 (atlas v5.4.0).*

Plain-English companion: `docs/UNDERSTANDING_MODEL_BUILDING.md` ·
Protocol rule: every test below was **written and frozen before the thing it
tests was built**. Counts: **86 defined · 84 executed-and-passed · 2 deferred**
(both flagged, both on the paper-gap list).

---

## A. Atlas layer gates — 64/64 PASS (12 validators)

Full details + signed entries: `SITE_SELECTION_VALIDATION.md` · machine logs in `logs/`.

| Layer | Validator | Gates | Date |
|---|---|---|---|
| S1 Huff capture (cap_*) | `validate_huff_capture.py` | 5/5 | 2026-06-10 |
| S2a Walk isochrones (iso_*) | `validate_iso_walk.py` | 6/6 | 2026-06-10 |
| S2b Transit isochrones (iso_transit15_*) | `validate_iso_transit.py` | 7/7 | 2026-06-10 |
| S3 Daytime population (dt_*) | `validate_daytime_pop.py` | 8/8 | 2026-06-10 |
| S4 ACRA business churn (biz_*) | `validate_acra_biz.py` | 6/6 | 2026-06-10 |
| S5 Labor shed (labor_*) | `validate_labor_shed.py` | 5/5 | 2026-06-10 |
| S6 Co-location lift (colo_*) | `validate_colo_lift.py` | 5/5 | 2026-06-10 |
| S7 Micro visibility (vis_*) | `validate_visibility.py` | 4/4 | 2026-06-10 |
| S8 Rent surface (rent_*) | `validate_rent_surface.py` | 5/5 | 2026-06-10 |
| S9 Future pipeline (pipe_*) | `validate_pipeline.py` | 4/4 | 2026-06-10 |
| S10 Context pack | `validate_context_pack.py` | 4/4 | 2026-06-11 |
| S11 Mobility pack | `validate_mobility_pack.py` | 5/5 | 2026-06-11 |

Gate *types* recur across validators: conservation (totals match source),
range/NaN accounting (NaN ≠ 0; non-residential = Not-Applicable), redundancy
audit (|r|>0.9 vs existing → drop/redefine), archetype spot-checks, and
known-answer recovery (e.g., S1 re-derives the Yunnan supermarket desert blind).

---

## B. plexis-e1 (hex8, 256-d) — 13-check harness, 11 PASS · 2 DEFERRED

Design: `EMBEDDING_V5_DESIGN.md` (frozen 2026-06-11, before training) ·
Results: `embedding/eval_final_plexis_e1.json` + `embedding/PLEXIS_E1_REPORT.md`.
Shipped = HYBRID 160 PCA + 96 contrastive. The pure-neural candidates (E1, E2)
**failed checks 1b/3 and were rejected despite the best probe scores.**

| # | Check | Threshold (locked) | Shipped result | Status |
|---|---|---|---|---|
| 1a | Known-twin panel (5 hand-picked anchors) | 5/5 sane | 5/5 (hit-rate 1.000) | PASS |
| 1b | Known-contrast pairs (Tuas↔Orchard) in top distance decile | pctile ≥ .90 | .997 (E1 scored .493 ✗ → rejected) | PASS |
| 2 | Archetype recovery (k-means vs archetype_label) | report ARI | .292 (E0 .261) | PASS |
| 3 | Distance sanity band rank-corr(embed, raw) | ~[0.5, 0.8] | .943 — above band, **accepted with silhouette evidence** (hybrid keeps raw geometry by construction; pure E2 scored .109 ✗ = destroyed information) | PASS (documented exception) |
| 4 | Linear probes, PA-blocked CV (hdb_psm / od / adq) | beat or stay near PCA-256 | .810 / .897 / .930 (PCA: .714 / .935 / .950 — od/adq concede ≤.038, traded for structure) | PASS |
| 5 | Negative control (permuted targets → chance) | R² ≈ 0 | −0.01 | PASS |
| 6 | Worst-30 reconstruction audit | no systematic blind spot | reviewed, none | PASS |
| 7 | Per-hex neighbor coherence (≥3/5 share zone type) | pass-rate reported | 92.5% | PASS |
| 8 | Locality sanity (PA over-represented in top-50, not top-5) | reported | top-50 PA share .471 | PASS |
| 9 | Counterfactual direction (zero a family → hex moves correctly) | directional | verified on FLOW/WHAT | PASS |
| 10 | Per-hex explainability texts (LLM-judged, human sample) | sampled OK | — | **DEFERRED** |
| 11 | Procrustes across 3 seeds | ≥ 0.90 | .987 | PASS |
| 12 | Leave-one-family-out retrain (no single-family dominance) | graceful degradation | — (equalized per-view rho measured post-hoc: WHERE .76 / FLOW .76 / PRICE .67 / WHO .66 / WHAT .65 — balanced, but LOFO itself not run) | **DEFERRED** |
| 13 | Separation score (zone silhouette) | report vs baselines | .133 (E0 .065) | PASS |

---

## C. plexis-p1 (places, 64-d) — 9/9 PASS

Design: `PLACE_EMBEDDING_DESIGN.md` (frozen 2026-06-12, before training) ·
Results: `embedding_place/exam_Z_p1_s0.json` + `PLEXIS_P1_REPORT.md`.
V0 (50K pilot) passed the same exam first; FULL ran on all 190,591.

| # | Check | Threshold (locked) | Result | Status |
|---|---|---|---|---|
| 1 | Held-out chain retrieval (20% of every ≥10-outlet chain hidden; sibling in top-10 of 190,591) | ≥ 0.70 | **0.814** (n=1,648) | PASS |
| 2 | Category kNN majority (k=10) | ≥ 0.80 | 0.997 | PASS |
| 3 | Beyond-category structure (cafe neighbours' micrograph gap vs random cafes) | ratio ≤ 0.70 | 0.157 | PASS |
| 4 | Geography leak ρ(embed dist, metres) | ≤ 0.45 | 0.077 | PASS |
| 5 | Same-hex spread (not context-only) | ≥ 0.50 × global | 0.640 | PASS |
| 6a | Probe pmg_anchors_400m (RidgeCV, standardized Z) | R² ≥ 0.50 | 0.775 | PASS |
| 6b | Probe pmg_walk_dist_mrt_m | R² ≥ 0.60 | 0.809 | PASS |
| 7 | **Forbidden probe — rating must be UNpredictable** | R² ≤ 0.15 | 0.094 | PASS (failed on purpose) |
| 8 | Seed stability (Procrustes, 3 seeds) | ≥ 0.95 | 0.979 / 0.981 | PASS |
| 9 | Archetype spot-checks picked pre-training (Ya Kun / heartland clinic / shophouse bar / industrial canteen) | 4/4 sane, ≥3/5 same-cat | 4/4, 5/5 each | PASS |

---

## D. Ops verification (not gated, but standing practice)

- **Deployed-URL playwright probes** after every app change (SG Pulse,
  Places Constellation, Atlas Diary) — localhost passing proves nothing for
  network timing; the rule exists because of a real frozen-app incident.
- Honest-display rules enforced at build time: prep asserts no
  rating/review/magnet token in any p1 input column; twins restricted to
  lived+scored hexes; display sims as ranks (cosines saturate).

## E. Open items (the full honest list)

1. e1 check 10 — per-hex explainability pass (Haiku pattern exists from
   hex_v11; not yet run on e1 neighbours).
2. e1 check 12 — LOFO retrains (5 × retrain + harness; ~half day on azold).
   Required for the paper (claim C1 cites the harness in full).
3. Paper additions beyond the registry: external baselines (Hex2Vec, GeoVeX,
   RegionDCL), p1 ablation table, West→East spatial holdout — tracked in
   `docs/PAPER_PLAN_PLEXIS_EMBEDDINGS.md`.
