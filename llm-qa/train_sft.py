#!/usr/bin/env python3
"""
Plexis-Mind — SFT (QLoRA) on Gemma-12B with Unsloth. Targets a single 32 GB GPU.

Peak VRAM ~14-20 GB (4-bit base + LoRA + activations at seq 2048). Trains on the assistant
turn only (prompt masked). Outputs LoRA adapters in ./plexis-mind-sft-lora.

Setup (on the GPU box):
  pip install "unsloth[cu124] @ git+https://github.com/unslothai/unsloth.git" trl datasets
  # copy train.jsonl / eval.jsonl next to this script (from azold:~/da-sgp/llm-qa/sft/)
Run:
  python3 train_sft.py
"""
import torch
from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template, train_on_responses_only
from datasets import load_dataset
from trl import SFTTrainer, SFTConfig

MODEL   = "unsloth/gemma-3-12b-it"   # swap to a newer Gemma 12B id if desired
MAXLEN  = 2048                        # our pairs are short; 2048 fits 32 GB with headroom
EPOCHS  = 2
OUTDIR  = "plexis-mind-sft"

# ---- model + QLoRA adapters ----
model, tok = FastLanguageModel.from_pretrained(
    MODEL, max_seq_length=MAXLEN, load_in_4bit=True, dtype=None)
model = FastLanguageModel.get_peft_model(
    model, r=32, lora_alpha=32, lora_dropout=0.0, bias="none",
    target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
    use_gradient_checkpointing="unsloth", random_state=42)
tok = get_chat_template(tok, chat_template="gemma-3")

# ---- data (chat-formatted: {messages:[{role,content}...]}) ----
def to_text(ex):
    return {"text": tok.apply_chat_template(ex["messages"], tokenize=False, add_generation_prompt=False)}
ds = load_dataset("json", data_files={"train":"train.jsonl","eval":"eval.jsonl"})
ds = ds.map(to_text, remove_columns=[c for c in ds["train"].column_names if c!="messages"])

# ---- trainer ----
trainer = SFTTrainer(
    model=model, tokenizer=tok, train_dataset=ds["train"], eval_dataset=ds["eval"],
    args=SFTConfig(
        per_device_train_batch_size=2, gradient_accumulation_steps=8,   # eff. batch 16
        warmup_ratio=0.05, num_train_epochs=EPOCHS, learning_rate=2e-4,
        lr_scheduler_type="cosine", optim="adamw_8bit", weight_decay=0.01,
        bf16=True, logging_steps=20, save_steps=500, eval_strategy="steps", eval_steps=500,
        max_seq_length=MAXLEN, dataset_text_field="text", packing=False,
        seed=42, output_dir=OUTDIR, report_to="none"))

# train ONLY on the assistant turn (mask the prompt) — Gemma-3 turn markers
trainer = train_on_responses_only(
    trainer, instruction_part="<start_of_turn>user\n", response_part="<start_of_turn>model\n")

if __name__ == "__main__":
    print(f"train {len(ds['train']):,} | eval {len(ds['eval']):,} | model {MODEL} | seq {MAXLEN}")
    trainer.train()
    model.save_pretrained(f"{OUTDIR}-lora"); tok.save_pretrained(f"{OUTDIR}-lora")
    print(f"done -> {OUTDIR}-lora  (merge to 16-bit for serving: model.save_pretrained_merged(...))")
