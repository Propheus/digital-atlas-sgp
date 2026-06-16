# Plexis-E — the Hybrid Representation Method

*A portable spec for building learned region (`e1`) and place (`p1`) embeddings for
a city atlas. Proven on Singapore (SGP); written so a Jakarta (IDN) or New York
(NYC) builder can pick it up and reproduce it at parity. Review-free, exam-gated,
CPU-only.*

---

## 0. TL;DR

- **What it is.** One compact vector per ~0.74 km² hex (`e1`, 256-d) and per venue
  (`p1`, 64-d), where **distance = functional similarity**. Built by **composing two
  objectives**, not picking one: `e1 = PCA-160 ⊕ contrastive-96`.
- **Why hybrid.** A controlled benchmark (PCA / AE / VAE / MAE / contrastive /
  hybrid, same input, same frozen exam) showed the two halves do **different jobs**:
  **contrastive → local robustness/invariance**, **PCA → the global metric**. The
  hybrid is the only one that holds both.
- **How good.** Twin hit-rate 1.0, probe OD R² 0.90 / adequacy 0.93, corruption-
  robustness ~1.5× PCA, 2-seed stability 0.99, and the forbidden-rating probe ≈ 0
  (provably no review leakage).
- **Cost.** Trains in minutes on CPU, seed-deterministic, no GPU, no transformer.
- **Portable.** The recipe is city-agnostic; only a short list of city-specific
  inputs is swapped (§6).

---

## 1. The principle — optimise for *similarity*, not reconstruction

A city atlas is used for **similarity** operations: twins, whitespace, competitor
radar, vibe search, analog retrieval, anomaly. So the embedding objective should
**name similarity**, not proxy it.

> **Reconstruction methods** (PCA, AE, VAE, MAE) ask *"can I rebuild this hex?"* and
> *hope* good geometry follows.
> **Contrastive** asks *"is this hex the same kind of place as that one?"* — the
> retrieval goal **is** the loss.

But contrastive alone has a measured failure mode (§4): it **warps global
distances**. So Plexis-E **anchors contrastive geometry with PCA** — keeping the
global metric while gaining local robustness. That composition is the method.

---

## 2. The recipe (city-agnostic)

### 2.1 Input prep — `prep_features.py`
From the city's hex master table build `X` (n_hex × d):
- **Numeric columns only**; drop identity/bookkeeping.
- **Exclude by design (no leakage):** ratings, review counts, and any column that is
  a model *output* or a probe target (price, OD, adequacy) — these become the
  **forbidden / probe** set, never inputs.
- **Per-column transform:** `log1p` for skewed non-negative columns, then z-score,
  clip to ±6.
- **NaN → 0 after z**, with per-family **NaN-indicator channels** appended.
- **Assign every input column a VIEW** — `WHO / WHERE / WHAT / FLOW / ECON(PRICE)` —
  for view-masking later.
- Output `X.npy`, `meta.json` (cols, views), `labels.parquet` (probe targets + zone
  labels held out of `X`).

> SGP: 801-col master → **739 review-free inputs**, views
> `{WHO 64, WHERE 341, FLOW 94, PRICE 33, WHAT 202}`.

### 2.2 Encoder — a clean MLP, deliberately no transformer
```
Encoder:  Linear(d→512) → LayerNorm → GELU → Dropout(0.1) → Linear(512→dim)
          + projection head Linear(dim→128)   (for InfoNCE)
          + decoder Linear(dim→512)→GELU→Linear(512→d)   (for denoising recon)
```
The input is a fixed-length vector and spatial context already enters as ring
features — there is no sequence to attend over. The bottleneck is **information**
(we exclude rating/name/identity by design), not capacity, so an MLP + a strong
self-supervised objective is the right tool.

### 2.3 The hybrid — `e1 = PCA-160 ⊕ contrastive-96`
1. `PCA-160 = PCA(160).fit_transform(X)` — the global-metric anchor.
2. `Z_c = contrastive_encoder(X)` (256-d), then `PCA-96 = PCA(96).fit_transform(Z_c)`.
3. `e1 = concat([PCA-160, PCA-96])` → 256-d. Store as `hex8_embedding_*_256d.parquet`
   (key + `e0…e255`).

### 2.4 Contrastive training — `train.py`
SCARF-style self-supervision + view-masking:
- **Positive pair** = (clean hex, corrupted copy). **SCARF corruption:** resample a
  random ~30% of features from each column's marginal (donor = another random hex).
- **View-masking (the key extra):** with prob ~0.5, additionally **zero an entire
  view** (e.g. all FLOW), so the encoder must infer the missing domain from the
  others — the supply↔demand objective; this is the MAE idea, folded in.
- **Loss** = `InfoNCE(proj(clean), proj(corrupt))` (in-batch negatives, τ≈0.5)
  `+ λ·MSE` denoising reconstruction on the masked entries.
- AdamW, cosine LR, batch 256, ~700–1500 epochs, **2 seeds** for a stability check.

### 2.5 The ratio — sweep it, don't guess
Sweep the PCA/contrastive split on the frozen exam. SGP tried **192/64 vs 160/96**
and shipped **160/96** (it lifted HDB-price probe 0.785→0.810 and adequacy
0.918→0.930 for negligible OD cost). Re-run this sweep per city — the optimum may
shift with feature count.

### 2.6 The place embedding `p1` (64-d) — pair design is the lever
Same encoder, but the **positive pair changes**: two outlets of the **same chain**
are a positive (free domain supervision, no labels). Inputs = category one-hot +
per-venue micrograph + a down-weighted slice of the venue's hex context. SGP:
**17,046 chain-sibling pairs across 203 chains**. Note `p1` is currently
**contrastive (not hybridised)** — fine for local retrieval; hybridise it only if
global place-distance queries matter (§8).

---

## 3. The exam — write it first, freeze it, let the marks decide

Nothing ships until it passes a **battery written and frozen before training**.
Five families (`eval_harness.py`), all probes **PA-blocked** (spatial-autocorrelation
guard), Z standardized so the comparison is scale-fair:

1. **Should-predict (utility):** linear ridge probe on held-out targets (price, OD,
   adequacy). High = real structure is *linearly accessible*.
2. **Should-NOT-predict (forbidden):** probe ratings, raw geography, a **permuted-
   target negative control**. Must be ≈ 0 — *this is the ship gate.*
3. **Retrieval / twins:** hand-picked known-answer analogs + (harder) hidden-sibling
   retrieval + kNN purity.
4. **Invariance & stability:** corrupt 30% of features → neighbour drift; 2-seed
   Procrustes.
5. **Structure & baselines:** distance rank-corr, cluster ARI/silhouette, **and PCA
   as the yardstick + ablations** (every ingredient must earn its place).

> **The asymmetry is the point.** Anyone scores high on "should-predict." A *clean*
> representation scores ≈ 0 on what it must **not** know. That is what makes it
> trustworthy, not just useful.

---

## 4. How good it is — the measured evidence (SGP)

Six methods, identical input `X (1191×739 → 256-d)`, identical frozen exam, 2 seeds:

| Method | OD R² | adq R² | **robust** | **stability** | **dist-rank (global)** | neg-ctrl |
|---|---|---|---|---|---|---|
| PCA | **0.935** | 0.951 | 0.324 | 0.999 | **1.00** | −0.020 |
| AE | 0.874 | 0.959 | 0.292 | 0.863 | — | −0.011 |
| VAE | 0.871 | 0.955 | 0.306 | 0.824 | — | −0.009 |
| MAE | 0.893 | **0.961** | 0.417 | 0.923 | — | −0.010 |
| Contrastive | 0.887 | 0.960 | **0.538** | 0.975 | **0.24** ⚠ | −0.011 |
| **Hybrid (e1)** | 0.911 | 0.933 | 0.460 | 0.993 | **0.97** | −0.013 |

**What each half captures:**

| Half | Captures | Good at | Lost without it |
|---|---|---|---|
| **Contrastive-96** | **LOCAL** — "same kind of place" neighbourhoods robust to noise & re-training | robust **0.54** (best), stability 0.97 | neighbours drift; map changes each re-train |
| **PCA-160** | **GLOBAL** — faithful distances/magnitudes, linear structure | dist-rank **1.00**, OD-probe 0.94 | "how different / how far" collapses (pure contrastive → **0.24**) |

**Read it honestly:** *utility is shared* (every method 0.87–0.96 — the info is in
the features, not the embedding), and a harder K=25 functional-retrieval exam still
under-separates the methods (~0.60 for all). **The real differentiators are
robustness, stability, and the global metric** — exactly where pure contrastive
both wins (robustness) *and* fails (global distance 0.20–0.24), and exactly why the
**hybrid is the shipped choice**: it keeps the global metric (0.97) *and* the
robustness (0.46) at the best learned stability (0.99). We didn't assert it; we froze
the test and ran the field.

---

## 5. The fruits — what the method buys you

1. **One vector → every similarity product.** Twins, whitespace ghost-maps,
   competitor radar, vibe search, analog retrieval, anomaly, gradient maps — all are
   nearest-neighbour or distance operations on the same fingerprint.
2. **Local *and* global, by construction.** Retrieval that stays put under noise
   (contrastive) **and** trustworthy "how different are these two" (PCA). Most
   embeddings give you one; the hybrid gives both.
3. **Provably clean → trustable.** Review-free inputs + the forbidden probe ≈ 0 mean
   the embedding encodes *what a place is*, never *how popular it is* — safe to ship
   to customers and to expose in apps.
4. **Free domain supervision.** Pair design (chain siblings) injects "same kind of
   place" with zero hand labels — knowledge no PCA/AE can absorb.
5. **Cheap, reproducible, auditable.** CPU-only, minutes to train, seed-deterministic,
   gated by a public frozen exam. No GPU, no black box.
6. **Composable.** Drop the columns into any model as features (BYO target), feed the
   domain packs, or expose as tools to an agent/reasoner — the embedding is a
   substrate, not an endpoint.
7. **Transfers across cities at parity.** The recipe is fixed; only the inputs change
   (§6). One method, many atlases.

---

## 6. Port it to a new city (IDN / NYC checklist)

**Keep unchanged (the method):** the encoder, the hybrid 160/96 construction, SCARF
+ view-masking + InfoNCE + denoising recon, the 2-seed stability check, the
exam-first discipline and its five families.

**Swap per city (the inputs):**

| Swap | SGP | What IDN / NYC supplies |
|---|---|---|
| **Hex master table** | `hex8_all_features` (801) | your city's per-hex feature matrix |
| **Forbidden / probe targets** | ratings, HDB-psm, OD, adequacy | your price feed (resale/rent/assessed), your OD, your adequacy/access target |
| **Views** | WHO/WHERE/WHAT/FLOW/PRICE prefixes | re-map prefixes to the same 5 views |
| **Twin anchors** (exam) | Toa Payoh, CBD, Tuas, Tengah, Yishun | hand-pick 5 known archetypes (NYC: Midtown CBD, brownstone Brooklyn, industrial Bronx, a transit desert, a new-build waterfront) |
| **Category taxonomy + chains** (p1) | 24 cats, 203 chains | the city's POI taxonomy + its real chains (IDN: Indomaret/Alfamart/Kopi Kenangan; NYC: Duane Reade/Starbucks/Dunkin) |
| **Zone labels** | URA `zone_type_broad` | the city's land-use/zoning classes |
| **Ratio sweep** | 160/96 won | re-sweep — optimum shifts with feature count |

**Do NOT** import another city's z-score stats or embedding space — each city is
fit on its own marginals. For cross-city comparison, align spaces post-hoc
(Procrustes / CORAL on shared anchors); a single joint space is a separate project.

---

## 7. Reproducibility — files & order

```
embedding/prep_features.py     # master -> X.npy, meta.json, labels.parquet
embedding/train.py             # contrastive encoder (SCARF + view-mask + InfoNCE + recon)
embedding/eval_harness.py      # the frozen exam: evaluate(Z, fast=False, X_raw=X)
embedding/benchmark_methods.py # PCA/AE/VAE/MAE/contrastive/hybrid on the SAME X + exam
embedding/hard_exam.py         # K-class functional retrieval + hard-negative triplets
# place side:
embedding_place/prep.py · train.py · exam.py   # p1 (chain-sibling positives)
```
Run order: `prep → train (2 seeds) → build hybrid (PCA160 ⊕ PCA96(contrastive)) →
eval_harness → (sweep ratio) → ship the parquet`. Training is seed-deterministic;
the whole thing re-runs from source.

---

## 8. Honest limits (so a builder ships with eyes open)

- **Pure contrastive distorts global distance** — trust its neighbourhoods, not its
  far-distances. Hybridise (as `e1` does) if "how different / rank-by-distance /
  anomaly" matters. `p1` (places) is not yet hybridised — fine for local/chain
  retrieval, weak on global place-distance.
- **Utility is feature-bound, not embedding-bound** — if a probe target isn't
  recoverable from any embedding, the feature is missing, not the method.
- **The embedding encodes *kind*, not *quality* or *geography*** — by design. Use a
  separate (non-leaky) head for quality and the spatial index for "nearest X".
- **Static snapshot** — no temporal/causal/daypart. Those are separate layers.
- **Augmentation design is the whole game** — a wrong positive pair bakes in a wrong
  invariance silently. Ablate every augmentation against the exam.

---

*Method proven on Plexis SGP v5.5.0 · `e1` 256-d hybrid + `p1` 64-d · everything
review-free and exam-gated · numbers from the frozen e1/p1 exams and the
six-method benchmark. Take it, swap the inputs, pass the exam — and you have a city
atlas at parity.*
