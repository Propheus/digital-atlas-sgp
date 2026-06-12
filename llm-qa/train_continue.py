#!/usr/bin/env python3
"""
Alchemy V1 — CONTINUED fine-tune. Loads the v0 LoRA adapter as the starting point and keeps
training it on the cross-layer reasoning corpus (+ replay). Short run, builds on what we have —
NOT a retrain from base. Manual prompt-masking (same as train_sft_hf.py).

Run (after stopping the serving model to free the GPU):
  HF_TOKEN=... python3 train_continue.py
Env: MAXLEN(768) LR(5e-5) EPOCHS(2) BATCH(2) ACCUM(8) V0(/root/plexis-mind-sft-lora) OUT(plexis-mind-v1)
"""
import os, torch, glob
from transformers import (AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig,
                          Trainer, TrainingArguments, DataCollatorForSeq2Seq)
from peft import PeftModel, prepare_model_for_kbit_training
from datasets import load_dataset

BASE   = os.environ.get("MODEL", "google/gemma-4-12b-it")
V0     = os.environ.get("V0", "/root/plexis-mind-sft-lora")
MAXLEN = int(os.environ.get("MAXLEN", "768"))
EPOCHS = float(os.environ.get("EPOCHS", "2"))
SMOKE  = os.environ.get("SMOKE")
OUT    = os.environ.get("OUT", "plexis-mind-v1")

bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
tok = AutoTokenizer.from_pretrained(V0)
print("loading base 4-bit…", flush=True)
model = AutoModelForCausalLM.from_pretrained(BASE, quantization_config=bnb, device_map="auto",
        dtype=torch.bfloat16, attn_implementation="sdpa")  # faster + lighter than eager for the 768 ctx
model.config.use_cache = False
model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
print(f"attaching v0 adapter ({V0}) as TRAINABLE — continuing from v0…", flush=True)
model = PeftModel.from_pretrained(model, V0, is_trainable=True)
model.print_trainable_parameters()

def tok_mask(ex):
    msgs = ex["messages"]
    full_txt   = tok.apply_chat_template(msgs,      tokenize=False, add_generation_prompt=False)
    prompt_txt = tok.apply_chat_template(msgs[:-1], tokenize=False, add_generation_prompt=True)
    full   = tok(full_txt,   add_special_tokens=False)["input_ids"]
    prompt = tok(prompt_txt, add_special_tokens=False)["input_ids"]
    n = min(len(prompt), len(full))
    labels = [-100]*n + full[n:]
    return {"input_ids": full[:MAXLEN], "labels": labels[:MAXLEN],
            "attention_mask": [1]*len(full[:MAXLEN])}

ds = load_dataset("json", data_files={"train": "/root/train_v1.jsonl", "eval": "/root/eval_v1.jsonl"})
if SMOKE:
    ds["train"] = ds["train"].select(range(256)); ds["eval"] = ds["eval"].select(range(32))
ds = ds.map(tok_mask, remove_columns=ds["train"].column_names)

args = TrainingArguments(
    output_dir=OUT, per_device_train_batch_size=int(os.environ.get("BATCH","2")),
    gradient_accumulation_steps=int(os.environ.get("ACCUM","8")),
    num_train_epochs=(0.05 if SMOKE else EPOCHS), max_steps=(10 if SMOKE else -1),
    learning_rate=float(os.environ.get("LR","5e-5")),   # lower than v0 (1e-4): continue, don't overwrite
    lr_scheduler_type="cosine", warmup_ratio=0.03, max_grad_norm=1.0,
    optim="paged_adamw_8bit", weight_decay=0.01, bf16=True,
    gradient_checkpointing=True, gradient_checkpointing_kwargs={"use_reentrant": False},
    logging_steps=(2 if SMOKE else 20), save_steps=300, save_total_limit=3,
    eval_strategy="steps", eval_steps=(5 if SMOKE else 300),
    load_best_model_at_end=(not SMOKE), metric_for_best_model="eval_loss", greater_is_better=False,
    report_to="none", seed=42)
trainer = Trainer(model=model, args=args, train_dataset=ds["train"], eval_dataset=ds["eval"],
                  data_collator=DataCollatorForSeq2Seq(tok, padding=True, label_pad_token_id=-100))

if __name__ == "__main__":
    print(f"CONTINUE from {V0} | seq={MAXLEN} lr={args.learning_rate} ep={EPOCHS} "
          f"train={len(ds['train'])} eval={len(ds['eval'])}", flush=True)
    trainer.train()   # never resume_from_checkpoint (corrupts QLoRA) — we resume via the adapter weights
    model.save_pretrained(f"{OUT}-lora"); tok.save_pretrained(f"{OUT}-lora")
    print(f"done -> {OUT}-lora", flush=True)
