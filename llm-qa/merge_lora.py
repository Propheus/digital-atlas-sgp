#!/usr/bin/env python3
"""Merge the Plexis-Mind LoRA into the base in bf16 -> a standalone fast model.
Removes bnb-4bit dequant + PEFT runtime matmuls. Output also usable by vLLM."""
import os, torch, time
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

BASE    = "google/gemma-4-12b-it"
ADAPTER = "/root/plexis-mind-sft-lora"
OUT     = "/root/plexis-mind-merged"

print("loading base in bf16…", flush=True); t0=time.time()
base = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.bfloat16,
        device_map="auto", attn_implementation="sdpa")
print(f"  base loaded {time.time()-t0:.0f}s; attaching + merging adapter…", flush=True)
m = PeftModel.from_pretrained(base, ADAPTER)
m = m.merge_and_unload()
print("saving merged bf16 model…", flush=True)
m.save_pretrained(OUT, safe_serialization=True)
AutoTokenizer.from_pretrained(ADAPTER).save_pretrained(OUT)
print("DONE ->", OUT, flush=True)
