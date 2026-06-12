#!/usr/bin/env python3
"""
Plexis-Mind — SFT (QLoRA) on Gemma-12B. HF transformers + peft + bitsandbytes.
Blackwell-native (RTX PRO 4500, torch cu128). Plain Trainer + MANUAL prompt-masking
(prefix-length method) — no TRL chat-template machinery, so it's version-proof.

Peak VRAM ~16-22 GB @ seq 2048 on a single 32 GB card.
Run:
  export HF_TOKEN=...           # token with Gemma access
  MODEL=google/gemma-4-12b-it SMOKE=1 python3 train_sft_hf.py     # 10-step validation
  MODEL=google/gemma-4-12b-it python3 train_sft_hf.py            # full run
"""
import os, torch
from transformers import (AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig,
                          Trainer, TrainingArguments, DataCollatorForSeq2Seq)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import load_dataset

MODEL  = os.environ.get("MODEL", "google/gemma-4-12b-it")
MAXLEN = int(os.environ.get("MAXLEN", "2048"))
EPOCHS = float(os.environ.get("EPOCHS", "2"))
SMOKE  = os.environ.get("SMOKE")
OUT    = "plexis-mind-sft"

bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
tok = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(
    MODEL, quantization_config=bnb, device_map="auto",
    dtype=torch.bfloat16, attn_implementation="eager")
model.config.use_cache = False
model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
model = get_peft_model(model, LoraConfig(
    r=32, lora_alpha=32, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
    target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"]))
model.print_trainable_parameters()

# manual prompt-masking: labels = -100 over the prompt, real ids over the assistant turn.
# template -> TEXT first, then tokenize to plain int lists (transformers-5 apply_chat_template
# returns an Encoding when tokenize=True, which Arrow can't serialize).
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

ds = load_dataset("json", data_files={"train":"train.jsonl","eval":"eval.jsonl"})
if SMOKE:
    ds["train"] = ds["train"].select(range(256)); ds["eval"] = ds["eval"].select(range(64))
ds = ds.map(tok_mask, remove_columns=ds["train"].column_names)  # single-proc: multiproc map hangs when detached

args = TrainingArguments(
    output_dir=OUT, per_device_train_batch_size=int(os.environ.get("BATCH","4")),
    gradient_accumulation_steps=int(os.environ.get("ACCUM","4")),
    num_train_epochs=(0.05 if SMOKE else EPOCHS), max_steps=(10 if SMOKE else -1),
    learning_rate=float(os.environ.get("LR","1e-4")),   # lowered 2e-4->1e-4 (divergence fix)
    lr_scheduler_type="cosine", warmup_ratio=0.05, max_grad_norm=1.0,
    optim="paged_adamw_8bit", weight_decay=0.01, bf16=True,
    gradient_checkpointing=True, gradient_checkpointing_kwargs={"use_reentrant": False},
    logging_steps=(2 if SMOKE else 20), save_steps=500, save_total_limit=4,
    eval_strategy="steps", eval_steps=(5 if SMOKE else 500),
    load_best_model_at_end=(not SMOKE), metric_for_best_model="eval_loss", greater_is_better=False,
    report_to="none", seed=42)
trainer = Trainer(model=model, args=args, train_dataset=ds["train"], eval_dataset=ds["eval"],
                  data_collator=DataCollatorForSeq2Seq(tok, padding=True, label_pad_token_id=-100))

if __name__ == "__main__":
    print(f"MODEL={MODEL} seq={MAXLEN} smoke={bool(SMOKE)} train={len(ds['train'])} eval={len(ds['eval'])}")
    import glob as _g
    _ck = sorted(_g.glob(f"{OUT}/checkpoint-*"), key=lambda p:int(p.split("-")[-1]))
    _resume = _ck[-1] if (_ck and not SMOKE and os.environ.get("RESUME","1")=="1") else None
    if _resume: print(f"RESUMING from {_resume}")
    trainer.train(resume_from_checkpoint=_resume)
    model.save_pretrained(f"{OUT}-lora"); tok.save_pretrained(f"{OUT}-lora")
    print(f"done -> {OUT}-lora")
