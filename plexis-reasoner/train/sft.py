"""
SFT — QLoRA fine-tune Qwen3.5-9B on the verified tool-use trajectories.
The model learns to PRODUCE the assistant turns (reasoning + tool calls + final
answer); tool/user turns are context. Runs on one L40S (48GB).

  python3 sft.py
"""
import json
import os
from pathlib import Path

import torch
from datasets import Dataset
from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from trl import SFTConfig, SFTTrainer

os.environ.setdefault("HF_HOME", "/workspace/hf")
MODEL = os.environ.get("STUDENT_MODEL", "Qwen/Qwen3.5-9B")
TRACES = "/workspace/traces"
OUTDIR = "/workspace/plexis-sft-qwen9b"


def load_rows(path):
    return [json.loads(l) for l in open(path)]


def main():
    tok = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    # render each trajectory to a single training string via the chat template
    # (tools schema is applied so tool_calls render natively for Qwen)
    import sys
    sys.path.insert(0, "/workspace/plexis-reasoner/harness")
    from teacher import tool_schemas
    tools = [t["function"] for t in tool_schemas()]

    def render(rows):
        out = []
        for r in rows:
            try:
                text = tok.apply_chat_template(r["messages"], tools=tools,
                                               tokenize=False)
                out.append({"text": text})
            except Exception:
                # fallback: no tools kwarg (older template)
                out.append({"text": tok.apply_chat_template(r["messages"],
                            tokenize=False)})
        return out

    train = Dataset.from_list(render(load_rows(f"{TRACES}/sft_train.jsonl")))
    print(f"train rows: {len(train)}  | example chars: {len(train[0]['text'])}")

    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=torch.bfloat16,
                             bnb_4bit_use_double_quant=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL, quantization_config=bnb, torch_dtype=torch.bfloat16,
        device_map="auto", trust_remote_code=True)

    lora = LoraConfig(r=32, lora_alpha=64, lora_dropout=0.05, bias="none",
                      task_type="CAUSAL_LM",
                      target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                                      "gate_proj", "up_proj", "down_proj"])

    cfg = SFTConfig(
        output_dir=OUTDIR, num_train_epochs=2, per_device_train_batch_size=2,
        gradient_accumulation_steps=8, learning_rate=1e-4, warmup_ratio=0.03,
        lr_scheduler_type="cosine", logging_steps=10, save_steps=200,
        save_total_limit=2, bf16=True, gradient_checkpointing=True,
        max_length=4096, packing=False, report_to="none",
        dataset_text_field="text")

    trainer = SFTTrainer(model=model, args=cfg, train_dataset=train,
                         peft_config=lora, processing_class=tok)
    print("=== starting SFT ===")
    trainer.train()
    trainer.save_model(OUTDIR)
    tok.save_pretrained(OUTDIR)
    print(f"=== SFT done -> {OUTDIR} ===")


if __name__ == "__main__":
    main()
