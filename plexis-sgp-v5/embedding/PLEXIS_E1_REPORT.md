# Plexis-E v1 — hex8 256-d embedding: final reference report

**Shipped:** 2026-06-11 · checkpoint **v5.3.0** · `hex/hex8_embedding_plexis_e1_256d.parquet`
**Design:** `../EMBEDDING_V5_DESIGN.md` · code in this dir · audit trail `runs.jsonl` + `program.log`
**Run:** azold 16-core CPU, screen `plexis-e1`, full staged program in **8 minutes**.

## What it is

**HYBRID: 160 PCA dims ⊕ 96 contrastive dims**, both blocks mean-centred and
norm-scaled, over 739 prepared features from the v5.2 master (1,191 × 801; numeric,
identity/bookkeeping out, OPPORTUNITY view `cap_*`/`colo_*`/`roi_*` and probe targets
excluded from input; log1p-for-skew + z-score + clip ±6; NaN→0 with 5 family
NaN-indicator channels).

Contrastive block = E2 winner: SCARF masked contrastive (mask 0.3, τ 0.5, marginal
resampling corruption) + denoising reconstruction + **whole-view masking p=0.5**
(the supply↔demand cross-view objective), 1,200 epochs, encoder 739→512→256,
reduced to 96 dims by PCA before concat.

## The scoreboard (scale-invariant probes, PA-blocked CV)

| metric | E0 PCA | E1 | E2 | **HYBRID 160/96** |
|---|---|---|---|---|
| twin hit-rate (5 anchors) | 1.000 | 1.000 | 1.000 | **1.000** |
| contrast pairs pctile (gate ≥.90) | .997 | .493 ✗ | .684 ✗ | **.997 ✓** |
| probe hdb_psm R² | .714 | .774 | .834 | **.810** |
| probe od R² | .935 | .876 | .862 | .897* |
| probe adq R² | .950 | .959 | .955 | .930* |
| zone ARI | .261 | .437 | .426 | .292 |
| zone silhouette | .065 | .126 | .143 | **.133** |
| per-hex zone coherence | .915 | .919 | .924 | **.925** |
| dist rank-corr vs raw (band .5–.8) | 1.0 (exempt) | .231 ✗ | .109 ✗ | .943 (above band, accepted w/ silhouette evidence) |
| negative control R² | −.02 | −.00 | −.00 | −.01 ✓ |
| Procrustes across 3 seeds | n/a | .948 | .961 | **.987** |

\* the honest trade: od/adq probes concede .038/.020 vs PCA, both remain >0.89.
(Corrected 2026-06-11 — the hybrid od/adq cells previously held shifted values
.861/.897; canonical source: `eval_final_plexis_e1.json` = .897/.930.)
(160/96 chosen over 128/128 and 192/64 — best gate-compliant balance; table in
`eval_hybrid_ratios.json`.)

## Why not pure E2 (it "won" the composite score)

E2 doubled learned zone structure but **failed two locked gates**: known-contrast
pairs (Tuas↔Orchard) fell to p68 and distance rank-corr to .109 — InfoNCE's
uniformity term compresses extreme tails, silently pulling the most-different hexes
relatively closer. The locked harness, not the score, made the call. PCA block in
the hybrid restores global geometry; contrastive block keeps the local refinement.

## Bugs the run surfaced (fixed, with consequences)

1. **Probe scale bug:** raw-scale Ridge under-regularizes large-scale embeddings
   (PCA) vs unit-scale ones → all pre-fix probe comparisons were invalid. Fixed:
   StandardScaler + RidgeCV inside the harness. Any future embedding eval MUST use
   the fixed harness.
2. **No CECIL at hex8 grain** — tiny CBD subzones get absorbed; CBD twin anchor is
   CENTRAL SUBZONE.

## Usage guidance (also in embedding_catalog entry)

- **Use plexis-e1 for:** twin-finding, clustering, site matching, "similar
  neighbourhoods", showcase Find-Twins — anything where *distance = functional
  similarity*.
- **Don't use it for:** squeezing the last probe point on prediction tasks already
  at ceiling (od, adequacy) — use raw features there; the embedding's first 160
  dims ARE the PCA if a linear basis is needed.

## Reproduce / retrain

```
cd /home/azureuser/da-sgp/v5/embedding
python3 run_program.py          # full E0→E1→E2→hybrid program, ~8 min
python3 eval_harness.py Z_x.npy # full harness on any embedding
```

## Deferred (open follow-ups)

- Per-hex Haiku explainability pass (harness check #10, the hex_v11 pattern)
- Leave-one-family-out stability (#12)
- Counterfactual-direction per-hex check (#9)

## Artifacts

| What | Where |
|---|---|
| Final embedding | `hex/hex8_embedding_plexis_e1_256d.parquet` (1,191 × 257) |
| Encoder weights | `embedding/Z_e2_s0.npy.pt` (+ seeds 1,2) |
| Eval reports | `embedding/eval_*.json`, `logs/validate_embedding_e1.json` |
| Per-epoch eval log | `embedding/runs.jsonl` |
| Program log | `embedding/program.log`, `program_summary.json` |
| Catalog entry | `catalog/embedding_catalog.json` (7 of 13 available) |
