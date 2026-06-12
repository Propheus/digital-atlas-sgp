#!/usr/bin/env python3
"""Push Plexis-Mind v0 LoRA adapter to the HF Hub with a real model card."""
import os
from huggingface_hub import HfApi, whoami

TOKEN = open(os.path.expanduser("~/notes/hf-prop-token.txt")).read().strip()
ADAPTER = "/root/plexis-mind-sft-lora"
api = HfApi(token=TOKEN)
user = whoami(token=TOKEN)["name"]
REPO = f"{user}/plexis-mind-v0-gemma4-12b-lora"
print("user:", user, "-> repo:", REPO)

CARD = """---
base_model: google/gemma-4-12b-it
library_name: peft
pipeline_tag: text-generation
license: gemma
language: [en]
tags: [lora, gemma, singapore, spatial-reasoning, urban, geospatial, qlora]
---

# Plexis-Mind v0 — Singapore Spatial-Reasoning LLM (Gemma-4-12B QLoRA)

A QLoRA adapter on **google/gemma-4-12b-it** that reasons about Singapore's urban
geography, grounded in the **Plexis v4.9.0 atlas** (332 subzones / 55 planning areas /
5 regions, H3-8 hexes, places, demographics, walkability, night-lights, HDB resale,
weekday commuter OD flows).

## The design
**Reasoning lives in the weights; facts come from the atlas.** Every training answer was
computed *deterministically* in Python from the atlas parquet; the LLM only learned to
**phrase and reason**, never to memorize numbers. Result: a grounded reasoner that does not
hallucinate figures and abstains on out-of-scope questions (crime, weather, real-time, income).

## How to use (production = reason-in-context)
Prepend a `Context:` line with the relevant atlas row, then ask — this is the 88% mode:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel
import torch
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
tok = AutoTokenizer.from_pretrained("USER/plexis-mind-v0-gemma4-12b-lora")
m = AutoModelForCausalLM.from_pretrained("google/gemma-4-12b-it", quantization_config=bnb,
        device_map="auto", dtype=torch.bfloat16, attn_implementation="eager")
m = PeftModel.from_pretrained(m, "USER/plexis-mind-v0-gemma4-12b-lora")
msgs = [{"role":"user","content":
  "Context: Bedok North — population 21,340; walkability 0.81; hawker_eateries 34; region East.\\n\\n"
  "Question: Is Bedok North walkable, and how big is it?"}]
txt = tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)
enc = tok(txt, return_tensors="pt", add_special_tokens=False).to(m.device)
print(tok.decode(m.generate(**enc, max_new_tokens=200)[0][enc.input_ids.shape[1]:], skip_special_tokens=True))
```

## Eval (held-out subzones, n=4,385)
~**88% overall**. Strong: places 95%, factual 93%, context-mode reasoning 88%, honest
abstention, stable-geography recall. Weak (v1 targets): filter-then-rank from scratch,
precise closed-book recall, over-abstention without context (use the `Context:` pattern).

## Training
QLoRA (4-bit nf4, r32, all 7 proj), HF Trainer, MAXLEN 512, eff-batch 16, lr 1e-4 cosine,
2 epochs, ~30h on one RTX PRO 4500 (Blackwell, 32GB). ~160K Q&A across 3 registers
(casual / standard / deep-reasoning). Data cost ~$25.

**Intended use:** Singapore urban-geography Q&A grounded in the atlas. Not for precise
closed-book recall — pair with the atlas tool layer for exact/fresh figures.
"""

api.create_repo(REPO, private=True, exist_ok=True, repo_type="model")
# write the card locally then upload the folder
open(f"{ADAPTER}/README.md","w").write(CARD.replace("USER", user))
print("uploading folder…")
api.upload_folder(folder_path=ADAPTER, repo_id=REPO, repo_type="model",
                  commit_message="Plexis-Mind v0 — Gemma-4-12B QLoRA adapter + model card")
print("DONE ->", f"https://huggingface.co/{REPO}")
