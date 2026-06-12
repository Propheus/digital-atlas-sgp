#!/usr/bin/env python3
"""Plexis-Mind inference smoke test — base gemma-4-12b-it + LoRA adapter.
Generates 3 completions to confirm inference works + show the context-vs-closed-book gap.
Loads tokenizer + chat template FROM THE ADAPTER DIR (matches training)."""
import torch, time
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

BASE = "google/gemma-4-12b-it"
ADAPTER = "/root/plexis-mind-sft-lora"
SYS = ("You are Plexis-Mind, an assistant that reasons about Singapore's urban geography "
       "grounded in the Plexis atlas. Answer concisely. If asked about something not in the "
       "atlas (crime, weather, real-time, income figures), say you don't track it.")

bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
print("loading tokenizer (from adapter)…")
tok = AutoTokenizer.from_pretrained(ADAPTER)
print("loading base 4-bit…")
t0=time.time()
model = AutoModelForCausalLM.from_pretrained(BASE, quantization_config=bnb,
        device_map="auto", dtype=torch.bfloat16, attn_implementation="eager")
print(f"  base loaded {time.time()-t0:.0f}s; attaching adapter…")
model = PeftModel.from_pretrained(model, ADAPTER)
model.eval()
print("ready\n"+"="*70)

def gen(user):
    msgs=[{"role":"system","content":SYS},{"role":"user","content":user}]
    ids = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt").to(model.device)
    t0=time.time()
    with torch.no_grad():
        out = model.generate(ids, max_new_tokens=220, do_sample=False,
                             pad_token_id=tok.eos_token_id)
    txt = tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True)
    return txt.strip(), time.time()-t0

TESTS = [
 ("CLOSED-BOOK stable-geo", "What region of Singapore is Bishan in?"),
 ("CLOSED-BOOK casual",     "Is Bishan a good area for families?"),
 ("CONTEXT-INJECTED",
  "Context: Bedok North subzone — population 21,340; walkability_index 0.81; "
  "hawker_eateries 34; mrt_stations 1 (Bedok North); region East.\n\n"
  "Question: Is Bedok North walkable, and roughly how big is it?"),
 ("CASUAL hawker (over-abstain risk)", "Any good hawker food around Clementi?"),
]
for label, q in TESTS:
    a, dt = gen(q)
    print(f"\n### {label}  ({dt:.1f}s)\nQ: {q}\nA: {a}\n"+"-"*70)
