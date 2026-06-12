# Plexis-Mind — Fine-Tuning Plan: SFT + GRPO

How we turn the ~170K-pair SGP spatial-reasoning dataset into a fine-tuned model.
Two stages: **SFT** (cold start — knowledge + reasoning shape) → **GRPO** (level up — correctness
+ planning quality, using the atlas itself as a verifiable reward).

Target base: **Gemma 12B-class** (Gemma-3 12B). Math/approach is identical for any 7–14B model.

---

## PART 1 — SFT (Supervised Fine-Tuning)

### 1.1 What to expect (set expectations honestly)
A 12B SFT on ~170K SGP pairs will:
- ✅ **Reason spatially in the right shape** — the reasoning traces (OD asymmetry, multi-hop,
  filter-then-rank, why-explanations) teach a *skill* that transfers. This is the real prize.
- ✅ **Know SGP structure** — regions, planning areas, adjacency, what a hawker centre / OD flow is.
- ✅ **Refuse gracefully** — the abstention pairs teach it to say "not in the atlas" instead of inventing.
- ⚠️ **NOT be a precise database** — a 12B won't memorise exact figures for all 326 subzones / 190K
  places. It approximates specific numbers. → train the *skill* hard; treat exact numbers as soft;
  pair with retrieval (RAG) at inference for precise figures (the reasoning skill transfers to that).

### 1.2 Format decision (decide before training)
Each pair = `{question, reasoning, answer, fact, provenance}`. Two ways to use `fact`:

| Mode | Prompt | Teaches | Trade-off |
|---|---|---|---|
| **Reason-in-context** (~70%) | `Context: {fact}\nQ: {question}` → `{reasoning}{answer}` | read evidence → compute → answer (RAG-ready) | needs atlas at inference |
| **Closed-book** (~30%, stable geography only) | `Q: {question}` → `{reasoning}{answer}` | parametric SGP knowledge | numbers go stale / approximate |

Recommended hybrid (matches the strategy's Decision #0): reason-in-context primary + a small
closed-book slice for stable structural geography. Reason-in-context makes the traces genuinely
valuable (extract + compute, not memorise) and is robust to atlas updates.

### 1.3 Memory math — 12B fine-tuning

| Method | What's in VRAM | Total VRAM | Fits on |
|---|---|---|---|
| **QLoRA** (4-bit base + LoRA) | 4-bit weights ~7 GB + adapters/optim ~1–2 GB + activations ~4–8 GB | **~14–18 GB** | **single 24 GB** (4090/3090/A10) ✅ |
| **LoRA** (bf16 base + adapters) | bf16 weights 24 GB + adapters ~2 GB + activations ~6 GB | **~30–35 GB** | 48 GB (A6000/A40) or 80 GB |
| **Full FT** (AdamW) | weights 24 + grads 24 + Adam m/v/master ~144 GB | **~190 GB+** | 4–8× 80 GB (FSDP/ZeRO-3) — not single-GPU |

**→ Use QLoRA.** Fits a single 24 GB GPU; ~95% of full-FT quality for domain SFT at a fraction of cost.
Assumes gradient checkpointing, seq len ~1024 (our pairs are short, mostly <300 tok), batch 1–2 +
grad accumulation. *Inference later:* 12B at 4-bit ≈ 7–8 GB, bf16 ≈ 24 GB.

### 1.4 Recommended config
- **Tooling:** **Unsloth** (lowest-memory, ~2× faster Gemma QLoRA). Alts: Axolotl, TRL `SFTTrainer`.
- **LoRA:** rank 32–64, alpha = rank, target `q,k,v,o,gate,up,down`, dropout 0.05.
- **Train:** LR 2e-4 cosine, warmup 3%, **1–2 epochs** (more overfits), bf16, seq 1024, sample packing on.
- **Loss masking:** train only on the assistant turn (reasoning+answer); mask the prompt.
- **Eval:** the **`dataset/eval.jsonl` entity-holdout** (whole subzones held out → measures
  generalisation, not memorisation) + a small hand-written gold set. Exact-match for factual/counts,
  tolerance-band for numeric, rubric for reasoning traces, abstention-accuracy for out-of-scope Qs.

### 1.5 Curation step before training (important)
The raw corpus is lopsided — `hex8_multi` (~62K) + `quant` (~52K) = **114K of two formulaic templates**.
Training on all of it overfits those surface forms. **Downsample each to ~15–20K**, keep the diverse
families (OD asym/share, filt-super, multi-hop, similarity, why, abstention, multi-entity, planning) at
full weight. Target a balanced **~150–170K** training mix.

### 1.6 Time & cost
~150K examples × ~350 tok × 2 epochs ≈ 100M tokens (QLoRA 12B):
- A100-80GB ≈ 2k tok/s → **~14 h** · RTX 4090 (24GB) ≈ 1k tok/s → **~28 h**
- → ~1–2 days on a single GPU; ~$30–80 cloud, or free on your own card.

---

## PART 2 — GRPO (Group Relative Policy Optimization)

### 2.1 What it is
The RL method behind DeepSeek-R1's reasoning, stripped down:
1. For a prompt, **sample a group** of G answers (8–16) from the current model.
2. **Score each** with a *reward function* (a program, not a learned critic).
3. **Advantage = reward relative to the group mean** (above-average → reinforce, below → suppress).
4. Update policy toward better chains, with a KL leash to the reference model.

Key simplification vs PPO/RLHF: **no critic/value model, no human preference labels** — just a reward
function. Anywhere you can *verify* an answer, you can GRPO toward it. The model learns to *find* better
reasoning by exploration + outcome reward, instead of only imitating fixed SFT targets.

### 2.2 Why Plexis-Mind is unusually well-positioned
**The thing most people lack for GRPO is a reward function — we already built one.** The deterministic
answer engine that generates every pair's ground truth *is* a verifiable reward oracle. We reuse the
exact Python that computes "Tampines East elder share = 20%" to **score** the model's answer. That is
the entire unlock, and it's rare.

Pipeline: **SFT first** (competent starting policy — can't GRPO from scratch) → **GRPO second**.

### 2.3 Reward design by question type
| Type | Reward (programmatic, from the atlas) |
|---|---|
| Factual / counts / rankings | exact / tolerance match to computed answer; bonus for correct order |
| Multi-hop / arithmetic | final number within tolerance **+** intermediate steps consistent |
| OD / flow | compare to the real OD matrix value |
| **Abstention** | reward refusing out-of-atlas Qs; **penalise fabrication** → trains away hallucination |
| **Planning / counterfactual** | partial-verifier blend — see 2.4 |

### 2.4 Planning reward — the "+20 bus stops in Jurong East" case (biggest payoff)
No single ground truth, so build a **partial-verifier reward** from the atlas:
1. **Direction/magnitude** — a gravity/accessibility + OD model (`demand_pull`, OD matrix, walk-scores)
   computes the sign + rough magnitude of the effect (↑ accessibility, ↑ ridership, equity shift).
   Reward chains whose conclusions match.
2. **Grounding** — did it cite Jurong East's *real* current numbers (bus density, dist_mrt, population)?
3. **Structure** — right factors (ridership, accessibility, cost, equity) + explicit assumptions + caveats?
4. **Consistency** — a rubric LLM-judge for internal coherence.

GRPO samples ~12 planning chains, scores each on this blend, reinforces the best → the model produces
better-reasoned, better-calibrated planning analyses. SFT can only imitate our bounded planning
templates; GRPO can *discover* stronger chains under an outcome reward.

### 2.5 Memory / compute
GRPO is heavier than SFT (generate G samples per step + keep a reference model):
- **12B QLoRA-GRPO:** ~**24–48 GB** with vLLM-backed generation (Unsloth + TRL both support GRPO).
  Fits a single 48 GB card; tight on 24 GB.
- **Generation-bound** → slower than SFT (inference ×G per step). Expect days, not hours.
- Needs a solid SFT checkpoint first.

### 2.6 Honest caveats
- **Reward hacking** is the real risk — gameable reward → exploited. Deterministic answers make factual
  reward robust; the planning reward needs careful design + held-out checks.
- For **verifiable-answer** questions, GRPO's edge over good SFT is modest (SFT on correct answers
  already teaches them). **GRPO's payoff concentrates in planning/open-ended reasoning and abstention.**
- More complex/finicky than SFT. SFT alone already yields a strong, useful model.

---

## PART 3 — Execution order
1. **Finish dataset generation** (base + v2 curated + v3 diverse/abstention).
2. **Curate + balance** → `train_balanced.jsonl` (downsample formulaic giants).
3. **Format** into Gemma chat template, ~70/30 context/closed-book, loss-masked.
4. **SFT** (Unsloth QLoRA, 12B) → base checkpoint. Eval on entity-holdout + gold.
5. **Build `reward.py`** reusing the deterministic answer engine + a gravity/OD planning-effect reward.
6. **GRPO Phase 2** focused on planning + abstention.
7. (Optional) RAG layer at inference for precise figures — the reasoning skill transfers to it.

**One-line summary:** SFT makes Plexis-Mind *fluent and knowledgeable*; GRPO makes it a genuinely better
*reasoner and planner* — and we're rare in actually owning the verifiable reward machine to do it right.
