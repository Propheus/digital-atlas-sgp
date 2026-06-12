# Plexis-E v1 — hex8 256-d embedding over the full v5 feature set (design)

**Date:** 2026-06-11 · **Status:** ideation locked, build pending approval
**Goal:** one 256-d embedding per hex8 cell covering ALL v5 features (703 cols,
S1–S10 included), trained and served from azold v5.

## The governing constraint

n = 1,191 hex8 × ~680 numeric features → 256 dims is near-lossless even for PCA.
**Compression is not the objective; geometry is.** The embedding's job: distance =
functional similarity (twin-finding, clustering, downstream transfer). Every design
choice is judged by the *space* it produces on a fixed eval harness, never by loss.

## Candidates assessed

| Approach | Verdict |
|---|---|
| PCA-256 | Mandatory baseline (E0). Linear, noise-blind, but unbeatable stability. If nothing beats it, ship it. |
| Vanilla autoencoder | No real bottleneck at 703→256 → memorizes. Only useful as **masked/denoising** AE (learn feature dependencies). Ingredient, not a model. |
| Supply–demand regression encoder | The V7/V8 insight as representation learning: predict WHAT+FLOW from WHO+WHERE. Most valuable single signal; as **heads on a shared encoder**. Strict leakage rule (input XOR target). |
| GNN on H3 adjacency | Double-counts rings/pw columns already in features. GNN v6 (256d) predates S-layers. Skip message passing. |
| OD as graph edges | Trap: OD-connected ≠ similar (bedroom↔CBD). Use OD **destination-distribution similarity** as a role signal instead. |
| Contrastive (SCARF-style masking) | The small-n answer: masking = unlimited augmented pairs; directly optimizes the metric. **Backbone.** |

## Chosen design: one encoder, multi-objective

Encoder 703 → 512 → 256 (MLP, layernorm, dropout). Features z-scored with the v10
normalization rules (sqrt counts, distance decay, NaN→0 + mask channel).

```
L = L_contrastive(masked views)            # backbone metric
  + λ1 L_masked_reconstruction             # denoising structure
  + λ2 L_cross_view                        # demand→supply, demand→flow, structure→price
  + λ3 L_od_role                           # dist(z_i,z_j) ~ JS-div of OD destination rows
```

**Views (feature groups; masking + heads operate per view):**
- WHO: pop_*, nvp_*, female_pop_share, dt_*
- WHERE-structure: lu_*, bldg_*, road_*, walk/transit access, cons_*, carpark_*
- WHAT-supply: pc_*, pc2_*, mg_*, biz_*, coworking/petrol/wet market counts
- FLOW: od_*, taps, gtfs_*, iso_*, labor_*
- PRICE: rent_*, hdb_resale_*
- OPPORTUNITY (S-model outputs): cap_*, colo_fit_*, roi_* — **excluded from encoder
  input when used as probe targets** (they are model outputs themselves)
- Aggregate prefixes (ring/pw/max) ride with their base view.

**Leakage rule (inherited from the gap model + nous):** a column is encoder input XOR
cross-view target within any single objective; cross-view heads only ever predict a
view that was fully masked out of the input for that pass.

## Staged build with gates (one stage at a time, our standard protocol)

| Stage | What | Ships only if |
|---|---|---|
| E0 | PCA-256 baseline + eval harness | harness runs; this is the yardstick |
| E1 | masked-contrastive denoising encoder | beats E0 on ≥3 of 4 evals |
| E2 | + cross-view supply/demand/price heads | beats E1 |
| E3 | + OD-role term | beats E2 |

**Eval harness (fixed before any training; PCA-256 runs it first — neural ships
only if it beats PCA on probes + twins while staying stable):**

*Space-level:*
1. Known-twin panel — ~20 unambiguous hexes with hand-written neighbor
   expectations (Toa Payoh Central → mature town centres; Tengah ≈ Punggol-new;
   CBD tight cluster); plus known-CONTRAST pairs (Tuas↔Orchard) in top distance decile
2. Archetype recovery — k-means on embedding reproduces archetype_label (ARI)
3. Distance sanity band — rank-corr(embed dist, raw feature dist) in ~[0.5, 0.8]
   (≈1 learned nothing; ≈0 destroyed information)

*Information-level:*
4. Linear probes with PA-blocked CV (NOT random CV — spatial autocorrelation
   leaks) — hdb_resale_4r_median_psm, od_throughput, adq_default, archetype;
   targets excluded from input; must beat PCA-256
5. Negative control — permuted-target probes collapse to chance (harness-leak guard)
6. Per-hex reconstruction audit — worst-30 reconstructed hexes eyeballed for
   systematic blind spots

*Per-hex checklist (hex_v11 pattern; reported as pass-rate over 1,191):*
7. Neighbor coherence — ≥3/5 nearest share zone_type_broad
8. Locality sanity — parent-PA over-represented in top-50 but not the whole top-5
9. Counterfactual direction — zeroing a feature family moves the hex toward the
   matching population of hexes
10. Explainability pass — per-hex "why these neighbors" texts from feature
    deltas, LLM-judged + human sample (the validated Haiku pattern)

*Stability:*
11. Procrustes corr across 3 seeds ≥ 0.9
12. Leave-one-family-out — drop FLOW view, retrain: graceful degradation, not a
    different space (single-family dominance = finding, not pass)
13. Separation score — established V5/V6 metric (subzone AE baseline 0.720)

**RESOLVED (user decision 2026-06-11): hex8 only — always.** No hex9 pretraining, no
place-level scaling path. Masking is the augmentation that compensates for n=1,191;
if E1 is seed-unstable the remedies are stronger masking / smaller dim / ensemble
averaging — never a grain change. (Also moots the GPU question permanently: CPU on
azold is the platform.)

## Ops

- Train on azold CPU (1,191×680 is tiny; minutes/run); runpod GPU only if we scale.
- Artifacts: `hex/hex8_embedding_plexis_e1_256d.parquet` (+ encoder weights + config
  json), registered in embedding_catalog with availability flags, eval report in
  `logs/validate_embedding_e*.json`, catalog + checkpoint bump on ship.
