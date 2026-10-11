#!/usr/bin/env python3
"""Supervised fine-tuning of an open instruction model with a small AKSI LoRA adapter.

Run on a CUDA GPU (for example a GPU notebook/runtime), not on GitHub Pages or the
production free web service. Training only changes adapter weights; it does not
magically give the model world knowledge. Keep private user data out of datasets.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from datasets import Dataset, load_dataset
from peft import LoraConfig
from transformers import AutoTokenizer
from trl import SFTConfig, SFTTrainer


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default=os.getenv("AKSI_BASE_MODEL", "Qwen/Qwen3-0.6B"))
    p.add_argument("--dataset", default="training/data/aksi_seed.jsonl")
    p.add_argument("--output", default="artifacts/aksi-lora")
    p.add_argument("--epochs", type=float, default=3.0)
    p.add_argument("--batch-size", type=int, default=1)
    p.add_argument("--grad-accum", type=int, default=8)
    p.add_argument("--max-length", type=int, default=1536)
    p.add_argument("--learning-rate", type=float, default=1e-4)
    p.add_argument("--validation-ratio", type=float, default=0.1)
    p.add_argument("--qlora", action="store_true", help="Use 4-bit bitsandbytes quantization on CUDA.")
    return p.parse_args()


def main():
    args = parse_args()
    import torch

    if not torch.cuda.is_available():
        raise SystemExit(
            "CUDA GPU not detected. This training job is not run on GitHub Pages or the "
            "production API. Launch it in a GPU runtime; do not claim a model was trained until artifacts exist."
        )

    source = Path(args.dataset)
    if not source.exists():
        raise SystemExit(f"Dataset not found: {source}")
    raw = load_dataset("json", data_files=str(source), split="train")
    if len(raw) < 10:
        raise SystemExit(f"Dataset has only {len(raw)} examples; add reviewed examples before training.")

    split = raw.train_test_split(test_size=args.validation_ratio, seed=42)
    tokenizer = AutoTokenizer.from_pretrained(args.model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    lora = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )

    quantization_config = None
    if args.qlora:
        from transformers import BitsAndBytesConfig
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
        )

    config = SFTConfig(
        output_dir=args.output,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.learning_rate,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        logging_steps=5,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        max_length=args.max_length,
        packing=False,
        report_to="none",
        gradient_checkpointing=True,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        seed=42,
    )

    model_kwargs = {"torch_dtype": "auto"}
    if quantization_config is not None:
        model_kwargs["quantization_config"] = quantization_config
        model_kwargs["device_map"] = "auto"

    trainer = SFTTrainer(
        model=args.model,
        args=config,
        train_dataset=split["train"],
        eval_dataset=split["test"],
        processing_class=tokenizer,
        peft_config=lora,
        model_init_kwargs=model_kwargs,
    )
    trainer.train()
    trainer.save_model(args.output)
    tokenizer.save_pretrained(args.output)

    metadata = {
        "base_model": args.model,
        "adapter_dir": args.output,
        "train_examples": len(split["train"]),
        "validation_examples": len(split["test"]),
        "epochs": args.epochs,
        "dataset": str(source),
        "note": "LoRA adapter saved; evaluate against the base model before deployment.",
    }
    Path(args.output).mkdir(parents=True, exist_ok=True)
    (Path(args.output) / "aksi-training-manifest.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
