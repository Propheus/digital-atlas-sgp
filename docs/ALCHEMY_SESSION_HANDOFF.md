# Alchemy / Plexis-Mind — Session Handoff & Resume Guide

**Read this first to resume.** Everything built, where it lives, the server, and how to bring it back.
Companions: `ALCHEMY_RESTORE_RUNBOOK.md` (restore steps) · `ALCHEMY_URBAN_REASONING_MODEL.md` (design) ·
`ALCHEMY_METRIC_ONTOLOGY.md` · `ALCHEMY_REASONING_ROADMAP.md` · `PLEXIS_MIND_MASTER.md` · `ALCHEMY_FINETUNE_REPORT.html`.

**Status as of pause:** v1 model trained, deployed, archived to HF, persisted to `/workspace`, **services stopped,
pod to be stopped by user.** Fully recoverable.

---

## 0. TL;DR — resume in one command
After the RunPod pod is Started again:
```bash
ssh runpod-finetune 'bash /workspace/alchemy/START.sh'
# wait ~20s, then: ssh runpod-finetune 'curl -s localhost:8080/health'
# public chat: https://e4245qvdon7vok-7780.proxy.runpod.net/
```
If `/workspace` is gone (full terminate), follow `ALCHEMY_RESTORE_RUNBOOK.md` Scenario B (rebuild from HF + repo).

---

## 1. What this is
**Alchemy (internal: Plexis-Mind)** = a Gemma-4-12B QLoRA fine-tune that reasons about Singapore's urban
geography across **6 data layers**, grounded in the Plexis v4.9.0 atlas. Keystone: *reasoning in the weights,
facts from the atlas* — a deterministic engine generates + verifies + rewards + serves. Deployed as a
ChatGPT-style web app with a Compare panel (fine-tuned vs raw Gemma).

- **v0**: QLoRA on ~160K deterministic Q&A (3 registers). ~88% on held-out subzones.
- **v1**: continued FT of v0 on ~3K cross-layer reasoning pairs + 5K replay (~2.2h). Leads with outcome
  indices, reasons demand/gap/opportunity. Deployed.

---

## 2. Everything's location (the map)
| Thing | Where |
|---|---|
| **Model v1 (adapter + card + methods/)** | HF `paperclip123/plexis-mind-v1-gemma4-12b-lora` (private) |
| **Model v0** | HF `paperclip123/plexis-mind-v0-gemma4-12b-lora` (private) |
| **Training data** | HF dataset `paperclip123/plexis-mind-sgp-reasoning-data` (private) |
| **Persisted full stack (fast restart)** | `runpod-finetune:/workspace/alchemy/` (27 GB; base-model cache, adapter, built app, scripts, DBs, START.sh) |
| **Local code** | this repo `llm-qa/` (generators, training, serving, atlas_tools) · `apps/plexis-chat/` (web app) |
| **Local docs** | this repo `docs/ALCHEMY_*.md` + `.html`, `PLEXIS_MIND_*.md` |
| **Local backups** | this repo `backups/runpod-finetune/` (plexis_chat.db, plexis_memory.db, run_*.sh, copy_to_workspace.sh) |
| **Atlas source** | `azold-test-server:/home/azureuser/da-sgp/v4/` (parquets) |
| **Memory observatory** | local `~/mem/memory-observatory/` (for kb_memory; copied to box) |
| **Public chat URL** | `https://e4245qvdon7vok-7780.proxy.runpod.net/` |

---

## 3. Server & services
**Box:** `runpod-finetune` — RTX PRO 4500 Blackwell, 32 GB. SSH via `~/.ssh/config` alias (host 213.173.102.25,
RunPod proxy pod id `e4245qvdon7vok`; HTTP ports proxied: 7780, 8080, 8888).

| Service | Port | Screen | Script | Notes |
|---|---|---|---|---|
| **Model** | 8080 | `plexis` | `run_serve.sh` | base bf16 + v1 adapter (sdpa, toggleable), ~24 GB; `/chat` + `/compare` SSE; ADAPTER=/root/plexis-mind-v1-lora |
| **Store** | 8091 | `store` | `run_store.sh` | SQLite conversations+feedback; off-GPU; MEMORY_ENABLED=false |
| **Chat** | 7780 | `chat` | `run_chat.sh` | Next.js (`next start -p 7780`); proxies model+store; no-store header so the RunPod CF proxy doesn't cache |

**Ops rules (hard-won):**
- ALWAYS kill old `plexis` screens AND verify `nvidia-smi` GPU ≈ **2 MiB** before relaunching the model —
  zombie processes accumulate, OOM the GPU, and cause **empty/0-byte generations**.
- `pgrep -fc serve_plexis` self-matches its own shell (returns 1 when clean) — verify by GPU mem, not pgrep.
- Reliable launch+test = detached self-contained script writing to a logfile (ssh drops at 255 mid-command).
- Chat must serve on **7780** (CF cache clean / BYPASS); **18080 is CF-poisoned** (1-yr cached old build) — avoid.

---

## 4. The pipeline (how it was built / how to extend)
All scripts in `llm-qa/` (local) and HF model `methods/`:
1. `atlas_tools.py` — deterministic tool/verifier over the atlas parquet (get_metric/rank/gap/compare/od + `verify()`).
2. `generate_metric_reasoning.py` — verifiable metric reasoning (draw/gap/saturation/compare/rank).
3. `generate_cross_layer.py` — cross-layer families (index-decomposition[verifiable], behavioural, demo-gap,
   opportunity[caveated], index-rank, tool-call); filters incomplete-data subzones.
4. `build_v1_data.py` — REASON-IN-CONTEXT chat data (Context block so numbers trace) + replay + entity-holdout.
5. `train_continue.py` — continued QLoRA from the v0 adapter (lr 5e-5, 1 epoch, MAXLEN 768, sdpa). v0: `train_sft_hf.py`.
6. `serve_plexis.py` — FastAPI serving + auto context-injection (subzone & PA loc-intel, domain-filtered gaps).
7. `store_server.py` + `kb_memory.py` — persistence + (flagged) memory-observatory borrow.
8. `push_v1_to_hf.py` — archive to HF. `merge_lora.py` — merge adapter→bf16 (optional fast serve).

Design rationale: `ALCHEMY_URBAN_REASONING_MODEL.md` (6 layers + cross-layer patterns + verifiability line)
and `ALCHEMY_METRIC_ONTOLOGY.md` (metric semantics; **anchor = demand generator**, gap +1 = under-served).

---

## 5. Honest state of the fine-tune (for V2)
- **Works / improved (in weights):** index-leading reads, cross-layer synthesis, under-served diagnosis,
  behavioural role, abstention, register (replay preserved voice).
- **Regressed:** open-ended **opportunity/siting** over-fit a formulaic "argmax-gap" template (worse than base
  Gemma). Mitigated at inference by **domain-filtering gaps** (F&B → only food gaps) + analyst-synthesis prompt.
- **Base Gemma-12B is a strong reasoner** — fine-tune's reliable edge is *discipline* (abstention, structural
  zeros, data-semantics, calibration), not raw horsepower.
- **V2 method ideas:** regenerate opportunity family **richer + non-templated + domain-aware**; add tool-calling
  traces; **GRPO with the deterministic verifier as reward** (closes filt_super/multi-step); filter training
  examples where prompt > MAXLEN (caused the cosmetic `eval_loss: nan`); consider self-reflection-using-memory
  loop (reflect on verifier-fails/feedback → store lessons → retrieve) — design discussed, not built.

---

## 6. Credentials (locations, not values)
- HF token: `~/notes/hf-prop-token.txt` (and box `/root/.hf_token.txt`, `/workspace/alchemy/data/.hf_token.txt`).
- OpenRouter (data gen): `~/notes/openrouter-llm-build-key.txt`, `~/notes/openrouter-kosha.txt`.
- GCS: `~/notes/gcp-key-service-account.json` + `gs://databay-test/`.

---

## 7. Resume checklist
1. Start the pod (RunPod dashboard).
2. `ssh runpod-finetune 'bash /workspace/alchemy/START.sh'` → model+store+chat up.
3. Verify: `curl localhost:8080/health`, open the public URL.
4. To iterate on V2: data lives on HF + `/root` (via START.sh); rent/keep the GPU; use `train_continue.py` pattern.
5. Memory files (auto-loaded) already summarize all of this — see `project_plexis_mind`, `project_plexis_chat_app`.
