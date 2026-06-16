<div class="cards">
<div class="card"><div class="cv">5</div><div class="cl">methods compared</div></div>
<div class="card"><div class="cv">1.0</div><div class="cl">e1 twin hit-rate</div></div>
<div class="card"><div class="cv">0.90</div><div class="cl">probe OD R²</div></div>
<div class="card"><div class="cv">−0.01</div><div class="cl">forbidden probe</div></div>
<div class="card"><div class="cv">0.997</div><div class="cl">corruption-robust</div></div>
<div class="card"><div class="cv">5×</div><div class="cl">test families</div></div>
</div>

# Why Contrastive — and How to Know a Representation Is *Correct*

*A method note for the Singapore & Jakarta Digital Atlases. How contrastive
training compares to PCA, autoencoders, VAEs and masked autoencoders for learning
the e1 (hex) and p1 (place) embeddings — and the exam protocol that decides whether
a representation is actually right. Grounded in the real frozen-exam numbers.*

---

## TL;DR

- The atlas's goal is a **similarity metric** — *distance = functional similarity*,
  twins, retrieval, clustering. The reconstruction family (PCA / AE / VAE / MAE)
  optimizes a **proxy** ("can I rebuild the input?") and hopes good geometry falls
  out. **Contrastive optimizes the geometry directly** — the metric *is* the loss.
- Contrastive uniquely lets you (1) make the *retrieval objective* the training
  objective, (2) inject free supervision through **positive-pair design**
  (chain-siblings), (3) bake in **invariance/robustness**, and (4) **provably
  exclude** information (ratings, geography).
- It is **not universally better** — augmentation/positive design is everything,
  it needs negatives, it can't generate. The honest winner is a **hybrid** — and
  e1 already is one (160 PCA + 96 contrastive + a reconstruction anchor).
- A representation has **no single accuracy**. Correctness = a **battery of
  necessary properties**, half of which test what it must *refuse* to encode.
  Write the exam first, freeze it, let the marks decide.

---

## 1. The goal chooses the method

Every method below is a different answer to a different question:

> **Reconstruction methods ask:** *"Can I compress this hex and rebuild it?"*
> **Contrastive asks:** *"Is this hex the same kind of place as that one?"*

The atlas is used for twin search, whitespace, site matching, competitor radar,
clustering — all **similarity** operations. So the objective that *names* similarity
in its loss has a structural advantage: **what you optimize is what you ship.**
Everything else produces good similarity geometry only as a hopeful by-product.

---

## 2. Method by method

| Method | What it actually minimizes | Latent shaped by | Failure mode for *similarity* |
|---|---|---|---|
| **PCA** | linear reconstruction error (max variance) | the few highest-variance directions | linear only; dominated by high-variance columns (a `pop` swing drowns out land-use); no notion of "alike"; no noise invariance |
| **Simple autoencoder** | nonlinear reconstruction error | whatever is cheapest to reconstruct | learns easy/high-variance features; can drift toward identity; "close in latent" ≠ "same kind of place" |
| **Variational AE (VAE)** | reconstruction + KL-to-prior | a smooth Gaussian latent (generative) | objective is *generation*, not retrieval; posterior collapse / over-smoothing blurs the fine distinctions; you never need to *sample* hexes |
| **Masked AE (MAE / denoising SSL)** | reconstruct *masked* inputs | cross-feature dependencies (**good**) | closest cousin — but the embedding is a **by-product** of a reconstruction decoder; the metric isn't directly shaped; quality rides on the recon proxy |
| **Contrastive (InfoNCE + SCARF + view-masking)** | **alignment** (positives close) + **uniformity** (everything else spread) | the **distance geometry itself** | the metric *is* the loss — but only as good as the positive pairs you design |

The reconstruction family is a *spectrum of the same idea* (rebuild the input),
getting smarter from PCA → AE → VAE → MAE. MAE is the strongest of them precisely
because masking forces the model to learn how features **imply each other** —
which is why the atlas borrows it as **view-masking**. But even MAE leaves the
embedding as a residue of a reconstruction task; it never directly says "these two
should be neighbours."

---

## 3. The four levers contrastive gives you (all four are used)

1. **The metric is the objective, not a side effect.** "Pull twins together, push
   others apart" *is* InfoNCE — formally, **alignment + uniformity** on the
   hypersphere. No reconstruction method states the retrieval goal in its loss.

2. **Free supervision through positive-pair design.** The biggest lever. For
   **places**, a positive pair is *two outlets of the same chain* — **17,046
   sibling pairs across 203 real chains** taught p1 "same kind of place" with
   **zero hand labels**. PCA/AE/VAE cannot ingest that knowledge; it lives in the
   *pairing*, not the inputs.

3. **Invariance is designed in.** You choose what a positive *ignores*: SCARF
   corruption ≈ "shrug off ~30% noisy features"; view-masking ≈ "infer the FLOW
   view from WHO/WHERE/WHAT/ECON." The embedding becomes robust to exactly those
   nuisances — e1 seed-stability **0.987**, corruption-percentile min **0.997**.

4. **You can provably EXCLUDE information.** Ratings/reviews never enter, and the
   forbidden-probe confirms they're unrecoverable — **e1 −0.014**, **p1 0.094** —
   while geography is suppressed (**geo-leak ρ 0.077**). A reconstruction objective
   *wants* to encode everything it sees; contrastive lets you sculpt **presence and
   absence**.

### Honest caveats (don't over-claim)

- Contrastive is **only as good as its augmentations/positives** — wrong pairs bake
  in wrong invariances. The reconstruction family needs no such choice.
- It needs **negatives** and risks **dimensional collapse** without care
  (temperature, batch size).
- It **cannot generate or impute** — if you need to fill missing features or sample
  synthetic hexes, an AE/VAE/MAE is the right tool.
- **The real winner is a hybrid.** e1 is exactly that: **160 PCA dimensions + 96
  contrastive (view-masked SCARF, mask .3 / τ .5 / view-mask .5) + a reconstruction
  anchor**. So the honest framing is *not* "contrastive vs the rest" — it's
  **"contrastive geometry + MAE-style masking + a recon anchor, with PCA as the
  yardstick."**

---

## 4. How to know a representation is *correct*

There is **no single accuracy** and no ground-truth "true embedding." A
representation is correct iff it passes a **battery of necessary properties** — and
correctness is as much about what it *refuses* to encode as what it does. The
governing rule: **write the exam before training, freeze it, and let the marks
decide.** Five families:

| # | Family | Question | Test | Atlas result |
|---|---|---|---|---|
| 1 | **Should-predict (utility)** | is real structure *linearly* accessible? | light/linear **probe** on held-out targets | OD R² **0.90** · adequacy **0.93** · HDB-psm **0.81** |
| 2 | **Should-NOT-predict (forbidden)** | did banned info leak in? | probe for ratings, raw geography | rating e1 **−0.01** / p1 **0.09** · geo-leak ρ **0.08** |
| 3 | **Retrieval / twins** | does *distance = similarity*? | known-answer twin hit-rate · kNN purity · chain recall@10 | twin **1.0** · cat-kNN **0.997** · chain **0.814** |
| 4 | **Invariance & stability** | robust to noise & re-training? | corrupt N% features → neighbour drift · multi-seed Procrustes | Procrustes **0.987** · contrast-pct **0.997** |
| 5 | **Structure & baselines** | geometry preserves meaning; beats trivial? | distance rank-corr · cluster ARI/silhouette · **negative control** · **ablations** · **PCA baseline** | dist-rankcorr **0.94** · neg-control R² **−0.01** |

Three non-obvious points:

- **The forbidden / negative-control probes are the heart of correctness.** Anyone
  can score high on "should-predict." The proof of a *clean* representation is that
  it scores ≈ 0 on what it must *not* know — popularity, identity, a random-label
  control. That **asymmetry** is what makes the embedding trustworthy, not just
  useful.
- **Use a *linear* probe, not a deep one.** If a linear head recovers a target, the
  geometry encodes it *cleanly*. A deep probe can recover almost anything and tells
  you little about the representation.
- **Always carry a baseline + ablations.** "Contrastive is better" is only
  meaningful against PCA *on the same exam*, and every ingredient (mask, view-mask,
  chain pairs) must earn its place.

---

## 5. The experiment that actually settles it

Today the claim is asserted; it should be **proven apples-to-apples**:

> **Same input features → train {PCA, AE, VAE, MAE, SimCLR-contrastive, the hybrid}
> → run all six through the one frozen exam → tabulate.**

- **Controls** — identical feature matrix, identical dim (256), identical held-out
  splits, exam frozen *before* any training.
- **Output** — one table: utility probes ↑, forbidden probes ↓, twin/retrieval ↑,
  corruption-robustness ↑, seed-stability ↑ — across all six; plus **CKA** between
  every pair to see *how differently* each organises the space.
- **Predicted shape** — PCA strong on linear-utility but brittle and leaky; AE
  similar; VAE smoothest but weakest retrieval; MAE close to contrastive on utility
  yet worse on the *metric* tests; contrastive/hybrid wins retrieval + robustness +
  clean forbidden scores.
- **What would change the verdict** — if MAE matched contrastive on twin/chain
  retrieval, the "metric-is-the-objective" advantage would be smaller than claimed.

That benchmark is the honest, publishable answer — and it doubles as the results
section of any write-up of the method.

---

## 6. Bottom line

For a *similarity* atlas, **contrastive is the right backbone** because the metric
you care about is the metric it optimises, it lets you teach the model through
pair design, and it lets you guarantee what stays *out*. The reconstruction family
remains the right tool for compression, imputation and generation — which is why
the shipped embedding is a **hybrid**, not a purist. And "is it correct?" is never
one number: it's a **frozen battery** of should-predict, must-not-predict,
retrieve-sanely, stay-stable, and beat-the-baseline — the same discipline that
gates every embedding in this atlas.

---

*Method note for Plexis SGP v5.5.0 & Jabodetabek · numbers from the frozen e1/p1
exams (`eval_final_plexis_e1.json`, `exam_Z_p1_s0.json`) · everything review-free,
exam-gated.*
