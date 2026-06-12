# Plexis-Mind — Master Record (read this first)

A fine-tuned LLM that reasons about Singapore's urban geography, grounded in the Plexis v4.9.0 atlas.
Everything you need to understand, reproduce, or extend the project. Companion docs:
`SGP_LLM_QA_STRATEGY.md` (strategy), `PLEXIS_MIND_SFT_GRPO_PLAN.md` (training plan),
`PLEXIS_MIND_V0_CAPABILITIES.md` (what v0 learned).

**Status:** v0 trained & eval'd — **~88% on held-out subzones**. Total cost ~$25 data + ~30h GPU rental.

---

## 1. The core idea (the keystone)
**Python computes every ground-truth answer deterministically from the atlas parquet; the LLM only
PHRASES it (and, for hard kinds, REASONS).** This makes correctness model-independent and unlocks:
- cheap **flash** for the bulk (phrasing needs no intelligence),
- **verification** (recompute & reject) for QC and distillation,
- the same code as a **GRPO reward oracle** and an **inference-time tool layer**.

The atlas plays **4 roles**: data generator · QC verifier · reward oracle · live tool source.

---

## 2. Where everything lives

| Thing | Location |
|---|---|
| **Atlas (Plexis v4.9.0)** | `azold-test-server:/home/azureuser/da-sgp/v4/` (masters, OD matrix, catalogs) |
| **Q&A working dir** | `azold-test-server:~/da-sgp/llm-qa/` |
| **Generators + scripts (version-controlled)** | local repo `llm-qa/` |
| **SFT dataset (model-ready)** | `azold:~/da-sgp/llm-qa/sft/{train.jsonl 126426, eval.jsonl 4385}` (also copied to `runpod:/root/`) |
| **Trained model (v0)** | `runpod-finetune:/root/plexis-mind-sft-lora/` (LoRA adapter; base `google/gemma-4-12b-it`) |
| **Training GPU** | RunPod `runpod-finetune` = RTX PRO 4500 Blackwell, 32 GB |
| **Dashboards** | training progress `runpod:7780` · training-set explorer `azold:18090` |
| **Keys** | OpenRouter `~/notes/openrouter-llm-build-key.txt` (v4-pro+flash) · HF `~/notes/hf-prop-token.txt` · GCS `~/notes/gcp-key-service-account.json` + `gs://databay-test/` |

### Q&A raw sub-dirs (on azold `~/da-sgp/llm-qa/`)
`factual/raw/{admin,hex8}` · `places/raw/full` · `reasoning/raw/{full(v1),v2,v3}` · `planning/raw/full`
· `simple/full` + `casual/full` (casual register) · `distill/full` (deep traces) · `dataset/` (curated) · `sft/`

---

## 3. The dataset (~160K curated; ~220K raw)

**Three registers** (the key to handling real users, not just analysts):
| Register | ~Count | Style |
|---|---|---|
| casual / human | ~51.5K | short, conversational ("Any hawker food around Clementi?") |
| standard | ~94K | factual/places, grounded |
| deep reasoning | 15K | full verified multi-step CoT |

**5 categories × ~50 question kinds:** Factual (subzone/PA/region + hex8-landmark-keyed) · Places
(counts/mix/brand/existence) · Reasoning (topn/compare/odflow/rank/multihop/filt/synthesis/similar/quant)
· Patterns (OD flows) · Planning (observed-change/supply-gap/mrt-analog/scenario).

**Record format:** `{category, kind, scale, entity, question, reasoning, answer, fact/context, provenance, register}`.
SFT chat format: `{messages:[system,user,assistant], meta}` — ~70% **reason-in-context** (`Context: {fact}` in
prompt) + ~30% **closed-book** (stable geography + abstention + concepts only; recall kinds = answer-only, no
phantom-fact reasoning).

**Models used:** `deepseek/deepseek-v4-flash` ($0.10/$0.20 per M) for phrasing the bulk; `deepseek/deepseek-v4-pro`
($0.43/$0.87) for the 15K deep distilled traces (verified). Pro-everywhere would've been ~$150 vs ~$25 — flash
is safe because answers are deterministic.

### Generators (local `llm-qa/`)
- `generate_factual_v2.py` — subzone/PA/region exhaustive facts
- `generate_hex8_factual.py` — hex8 keyed by nearest-landmark (solves the 91% name-collision)
- `generate_places.py` — 55-cat POI counts/mix/brand
- `generate_reasoning.py` (v1) / `generate_reasoning_v2.py` (strong, 224k) / `generate_reasoning_v3.py` (diverse + abstention)
- `generate_simple.py` / `generate_casual_v2.py` — casual register (life-spectrum, not just transport)
- `generate_distill.py` — **v4-pro deep traces + `verify()` rejection sampling** (81% accept, $4.58 for 15k)
- `curate_and_format.py` — downsample formulaic, format to chat, entity-holdout split
- `qc_and_split.py` — numeric-fidelity QC + dedup
- `atlas_tools.py` — **the tool/verifier layer** (get_metric/compare/rank/od/… + `verify()`) — used by distill, GRPO, and (next) inference tools

### Quality rules learned (framing, not math — the numbers were always right)
- **Normalize** concentration questions (elder *share*, not count — else you just rank by population)
- **Percentile semantics**: "#194 of 214 = bottom 9%", never "top 91%"
- **Structural zeros**: HDB resale `0` = no-HDB (not "cheap") → null it
- **Degenerate ties**: skip all-equal top/bottom-N
- **Label honesty**: `food_hawker` = hawker *eateries* (POIs), not gazetted *centres*
- **Affluence** = PA-resolution proxy (education/occupation/housing), exclude `nvp_low_n`
- **OD** = weekday *monthly* aggregate, not single-day, not dorm-tagged
- **No weekend/Sunday data** (gap)

---

## 4. Training (v0) — config + the hard-won gotchas

**Final stable config:** Gemma-4-12B QLoRA (4-bit nf4, r32, target all 7 proj), HF `transformers.Trainer` +
peft + bitsandbytes (NOT Unsloth), **MAXLEN=512, batch 2, accum 8 (eff 16), lr 1e-4 cosine, 2 epochs,
paged_adamw_8bit, gradient checkpointing, `load_best_model_at_end`, save_total_limit=4**. ~30h on the 32 GB card.

### GOTCHAS (the gold — every one cost hours)
1. **Blackwell sm_120** needs `pip install --index-url .../whl/cu128 torch` (got 2.11); stock torch 2.4 = "no kernel image". bnb 0.49 4-bit works on Blackwell.
2. **Use HF Trainer, not Unsloth** — Unsloth's Triton kernels lag on brand-new sm_120.
3. **`resume_from_checkpoint` CORRUPTS QLoRA** — it doesn't reload LoRA weights; loss jumped 0.25→5.5. *Never resume; restart fresh.* Always check loss after any resume.
4. **MAXLEN must match data** — data maxed at **413 tokens**; MAXLEN=1024 made the 256K-vocab cross-entropy logits OOM at 31.6 GB. Profile token lengths FIRST. 512 → 15-22 GB, safe.
5. **lr 2e-4 diverged** mid-run (loss 0.25→5.5, slow recovery). **lr 1e-4 stable.** + `load_best_model_at_end` so a wobble can't lose the model.
6. **`PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`** reclaims fragmentation (~6.7 GB).
7. **`datasets.map(num_proc>1)` HANGS when detached** (no controlling terminal) → single-proc map.
8. **self-pkill footgun**: `pkill -f <pattern>` kills your OWN launching shell if the command string contains the pattern. Use launcher scripts (cmdline = `bash run_x.sh`) or precise patterns; verify by artifacts (files/GPU), not `pgrep`.
9. **transformers-5 quirks**: `apply_chat_template(tokenize=True)` returns an `Encoding` (Arrow can't serialize) → use `tokenize=False` then `tok()`. `assistant_only_loss` needs `{% generation %}` markers Gemma lacks → manual prompt-masking (prefix-length: labels=-100 over prompt). `apply_chat_template(return_tensors="pt")` returns a dict → `return_dict=True` + `**enc`.
10. **Flaky RunPod/azold ssh** drops at 255 mid-launch → `setsid` + verify in a held connection; long-lived watcher ssh will drop (re-arm).

---

## 5. Eval (v0) — what it learned
Generation-based, `atlas_tools.verify()`, 4,385 **held-out subzones**. **~88% overall** (85.7% raw + abstention-metric fix).
- **Strong:** places 95%, factual 93%, abstention near-perfect, **context-mode reasoning 88%** (the production mode), register-matching, stable-geography recall.
- **Weak:** `filt_super` (filter-then-rank) **0%** — the real reasoning gap; closed-book precise/categorical recall (dominant-use 0%, membership 33%); over-abstention without context.
- **Validated truth:** reasoning lives in weights, facts come from the atlas → with context 88% & no hallucination; closed-book it refuses to invent (safe) and tools fill the gap.
- **Known metric bug:** `verify()` for abstain rejects refusals that cite "55 categories" (a number) → abstention scored 0% but is actually ~perfect. Fix: decline-check only.

---

## 6. v1 roadmap (data-driven from the eval)
1. **Wire `atlas_tools.py` as inference tools** → closes the closed-book gap, exact/fresh numbers (biggest lift; already built)
2. **Fold the 15K deep traces in + GRPO** (reward = `atlas_tools.verify()`) → directly fixes `filt_super`/multi-step
3. **Rebalance abstention** (less coverage-list anchoring + more closed-book positives) + fix the abstain verify metric
4. Optional: multi-turn, recommendation, citation/provenance data; merge adapter to 16-bit + serve; back up to `gs://databay-test/`

---

## 7. Reproduce / operate
```bash
# regenerate dataset (azold)
python3 generate_*.py ...           # see each script's --help
python3 curate_and_format.py --root ~/da-sgp/llm-qa --out ~/da-sgp/llm-qa/sft
# train (runpod, Blackwell env: torch cu128 + bnb + peft + trl)
MODEL=google/gemma-4-12b-it MAXLEN=512 BATCH=2 ACCUM=8 LR=1e-4 python3 train_sft_hf.py
# eval
python3 eval_run.py                 # -> eval_results.json
# dashboards
python3 dashboard_server.py 7780    # training progress
python3 browse_server.py 18090      # training-set explorer
```
Launch long jobs via a launcher script + `setsid bash run_x.sh </dev/null >/dev/null 2>&1 & disown` (NOT a self-matching pkill).

**One-liner:** owning the deterministic atlas (generator + verifier + reward + tool) let a small team build a
grounded SGP reasoning LLM — ~88% on unseen areas, honest abstention, conservative-not-hallucinatory — for ~$25 + a GPU rental.
