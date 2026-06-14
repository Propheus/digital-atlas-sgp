# Plexis-Reasoner — Resume Here

Paused 2026-06-14 (day 2). Everything below is staged for a one-command resume.
Full background in memory `project_plexis_reasoner.md`.

## State at pause

| Thing | Status |
|---|---|
| **Trace corpus** | **17,715 verified traces** — SAFE on HF: `paperclip123/plexis-reasoner-sg-traces` (private) + on box `/workspace/traces/sft_v1.jsonl` |
| SFT data split | `/workspace/traces/sft_train.jsonl` (6,169) + `sft_eval.jsonl` (400 held-out subzones) — re-run `train/prep_sft.py` to refresh from 17.7K |
| Pipeline code | local `plexis-reasoner/{tools,harness,train}/` + on box `/workspace/plexis-reasoner/` |
| Clean training env | **venv `/workspace/sftenv`** (torch 2.7.1+cu128, trl/peft/transformers/bnb — ALL IMPORTS OK). System python is BROKEN — always `source /workspace/sftenv/bin/activate` |
| SFT proven | YES — Qwen3.5-9B logged loss 2.958 @ 91% GPU. Switched to **Qwen3-8B** (Qwen3.5's linear-attn needs uncompilable kernels → 20h; Qwen3-8B ~1-2h, same skill) |
| Currently training? | NO — paused. `run_sft.sh` (Qwen3-8B) is on box, verified clean |

## The blocker (not a code problem)

**Box SSH is brutally flaky** — intermittent timeouts all day, occasional full outages. The box (`runpod-finetune`, 1× L40S) is fine; the connection isn't. Use `-o ConnectTimeout=30 -o ServerAliveInterval=8` + retry loops. `screen` survives drops.

## RESUME — exact steps

```bash
# 1. confirm box reachable + nothing running
ssh -o ConnectTimeout=30 runpod-finetune 'screen -ls; nvidia-smi --query-gpu=utilization.gpu --format=csv'

# 2. (optional) refresh data split from the full 17.7K corpus
ssh runpod-finetune 'cd /workspace/plexis-reasoner/train && python3 prep_sft.py'

# 3. LAUNCH SFT (Qwen3-8B, clean venv) — the one command
ssh runpod-finetune 'screen -dmS plexis-sft bash /workspace/run_sft.sh'

# 4. watch for loss (logs every 10 steps; Qwen3-8B std attention = fast)
ssh runpod-finetune 'tail -5 /workspace/sft.log'
```

run_sft.sh contents (on box, verified): activates venv → `STUDENT_MODEL=Qwen/Qwen3-8B` → `python -u sft.py` → logs to `/workspace/sft.log`.

## After SFT

1. **Eval** on `sft_eval.jsonl` (held-out subzones) — run rollouts with the trained model via the harness, grade with `harness/verify.py` (tool-choice + answer-verify + abstention).
2. **GRPO** — build `train/grpo.py`; `harness/verify.py grade()` IS the reward (already written). The hard tier (T2 filter-rank) is what GRPO sharpens.
3. Push final model to HF.

## Gotchas to remember

- SSH flaky → atomic short commands + retries + screen.
- System python broken → only use `/workspace/sftenv`.
- Qwen3.5 needs flash-linear-attention + causal-conv1d (causal-conv1d WON'T build here) → using Qwen3-8B instead.
- Tool-call `arguments` must be dict not JSON-string for Qwen chat template (handled in `prep_sft.py`).
- Teacher/generation: OpenRouter key `/workspace/.or_key` (= `~/notes/openrouter-keys-batch1.txt`); gen loop screen `plexis-gen` (may still be running, topping up sft_v1.jsonl).
- Cost so far: ~$2-3 teacher tokens. Full run was tracking ~$50 corpus + GPU.
