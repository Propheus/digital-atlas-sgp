#!/usr/bin/env python3
"""Archive Alchemy/Plexis-Mind V1 to the HF Hub: model (adapter + methods + card) + dataset."""
import os
from huggingface_hub import HfApi, whoami

TOKEN = open("/root/.hf_token.txt").read().strip()
api = HfApi(token=TOKEN)
USER = whoami(token=TOKEN)["name"]
MODEL_REPO = f"{USER}/plexis-mind-v1-gemma4-12b-lora"
DATA_REPO  = f"{USER}/plexis-mind-sgp-reasoning-data"
print("user:", USER)

# ---------------------------------------------------------------- model card
MODEL_CARD = f"""---
base_model: google/gemma-4-12b-it
library_name: peft
pipeline_tag: text-generation
license: gemma
language: [en]
tags: [lora, qlora, gemma, singapore, urban, spatial-reasoning, geospatial, cross-layer]
---

# Alchemy / Plexis-Mind v1 — Singapore urban-reasoning model (Gemma-4-12B QLoRA)

A QLoRA adapter on **google/gemma-4-12b-it** that reasons about Singapore's urban geography across
**six data layers**, grounded in the Plexis atlas. v1 is a *continued fine-tune* of v0 on a cross-layer
reasoning corpus — it learned to lead with the atlas's outcome indices (livability / family /
vibrancy) and to reason about demand–supply (anchors, provision gaps, saturation).

## The design (keystone)
**Reasoning lives in the weights; facts come from the atlas.** Ground-truth answers are computed
deterministically from the parquet; the LLM only phrases & reasons. The same deterministic engine is
generator, verifier, reward oracle, and inference tool. Every claim is either a verifiable fact or an
explicitly-caveated estimate.

## The six layers it reasons across
People · Affluence/housing · Movement (incl. OD + LTA bus taps) · Places (190k POIs) ·
Demand–Supply (anchor strength, demand support, **provision gap**, saturation, demand pull, synergy) ·
Form & Activity (land-use, night-lights). Plus the atlas's **outcome indices** which make cross-layer
verdicts verifiable.

## Training (v0 → v1)
- **v0**: QLoRA on ~160K deterministic Q&A (3 registers). ~88% on held-out subzones.
- **v1**: *continued* QLoRA (load v0 adapter as trainable) on ~2,959 cross-layer reasoning pairs (index
  decomposition, under-served diagnosis, behavioural role, opportunity[caveated], + tool-call traces)
  upsampled ×2 + ~5K replay. 1 epoch, lr 5e-5, MAXLEN 768, sdpa, ~2.2h on one RTX PRO 4500 (Blackwell).
  Trained **reason-in-context** (answer numbers trace to an injected Context block — no memorised facts).

## What it's strong / weak at (validated)
- **Strong**: index-leading reads, cross-layer synthesis, under-served diagnosis (gap_C), behavioural role,
  honest abstention, register/voice (replay preserved it).
- **Known limit (be honest)**: open-ended *opportunity/siting* over-fit a formulaic "argmax gap" pattern in
  v1; mitigated at inference by domain-filtering the gaps + an analyst-synthesis prompt. v2 should
  regenerate that family non-templated. For exact/fresh figures, pair with the atlas tool layer.

## Use (reason-in-context = production mode)
Prepend a `Context:` block of the area's atlas metrics, then ask. See `methods/serve_plexis.py` for the
exact context builder used at inference, and `methods/` for the full generation + training pipeline.

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel
import torch
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
tok = AutoTokenizer.from_pretrained("{MODEL_REPO}")
m = AutoModelForCausalLM.from_pretrained("google/gemma-4-12b-it", quantization_config=bnb,
        device_map="auto", dtype=torch.bfloat16, attn_implementation="sdpa")
m = PeftModel.from_pretrained(m, "{MODEL_REPO}")
```

Data: **{DATA_REPO}**. Predecessor: `{USER}/plexis-mind-v0-gemma4-12b-lora`.
Methods, ontology, and the full design are in `methods/` (see `ALCHEMY_URBAN_REASONING_MODEL.md`).
"""

DATA_CARD = f"""---
license: cc-by-nc-4.0
language: [en]
task_categories: [text-generation, question-answering]
tags: [singapore, urban, spatial-reasoning, cross-layer, reason-in-context]
---

# Plexis-Mind / Alchemy — Singapore urban-reasoning training data

Deterministically-generated Q&A for fine-tuning a Singapore urban-reasoning model. Every answer is
computed from the Plexis atlas parquet; the model learns to phrase & reason, never to memorise numbers.

## Files
- `train_v1.jsonl` / `eval_v1.jsonl` — the **v1 continued-FT** corpus (reason-in-context chat format:
  Context block + question -> reasoned answer; cross-layer reasoning + replay; entity-holdout eval).
- `cross_layer.jsonl` — cross-layer reasoning pairs (index decomposition[verifiable], under-served
  diagnosis, behavioural role, opportunity[caveated], index rank, tool-call traces).
- `metric_reasoning.jsonl` — deterministic metric reasoning (draw/gap/saturation/compare/rank over the
  proprietary anchor/gap/saturation/pull metrics).
- `train.jsonl` — the v0 base corpus (~126K; 3 registers: casual / standard / deep-reasoning).

## Format
`{{messages:[system,user,assistant], meta}}` for v1; `{{category,kind,scale,entity,question,reasoning,
answer,fact,provenance,verdict}}` for the raw generator output.

## Honesty
Deterministic families end in a checkable fact (verifier-scored). Judgment families (opportunity, what-if)
are emitted as explicitly-caveated estimates, never as fact. See the model repo `{MODEL_REPO}` for methods.
"""

# ---------------------------------------------------------------- push model
print("=== model repo ===")
api.create_repo(MODEL_REPO, private=True, exist_ok=True, repo_type="model")
open("/root/plexis-mind-v1-lora/README.md", "w").write(MODEL_CARD)
api.upload_folder(folder_path="/root/plexis-mind-v1-lora", repo_id=MODEL_REPO, repo_type="model",
                  commit_message="Alchemy/Plexis-Mind v1 adapter + card")
# methods: scripts + docs
import tempfile, shutil
md = "/root/_methods_upload"; os.makedirs(md, exist_ok=True)
for f in ["generate_metric_reasoning.py","generate_cross_layer.py","build_v1_data.py","train_continue.py",
          "train_sft_hf.py","atlas_tools.py","serve_plexis.py","curate_and_format.py"]:
    p=f"/root/{f}"
    if os.path.exists(p): shutil.copy(p, md)
for f in os.listdir("/root/methods_docs"):
    shutil.copy(f"/root/methods_docs/{f}", md)
api.upload_folder(folder_path=md, repo_id=MODEL_REPO, repo_type="model", path_in_repo="methods",
                  commit_message="methods: generators, training, serving, ontology + design docs")
print("model ->", f"https://huggingface.co/{MODEL_REPO}")

# ---------------------------------------------------------------- push dataset
print("=== dataset repo ===")
api.create_repo(DATA_REPO, private=True, exist_ok=True, repo_type="dataset")
dd = "/root/_data_upload"; os.makedirs(dd, exist_ok=True)
open(f"{dd}/README.md","w").write(DATA_CARD)
for f in ["train_v1.jsonl","eval_v1.jsonl","cross_layer.jsonl","metric_reasoning.jsonl","train.jsonl"]:
    p=f"/root/{f}"
    if os.path.exists(p): shutil.copy(p, dd)
api.upload_folder(folder_path=dd, repo_id=DATA_REPO, repo_type="dataset",
                  commit_message="Plexis-Mind/Alchemy SGP reasoning data (v0 base + v1 cross-layer)")
print("data ->", f"https://huggingface.co/datasets/{DATA_REPO}")
print("DONE")
