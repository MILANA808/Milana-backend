# AKSI fine-tuning pipeline

This folder is the reproducible starting point for training an AKSI-specific adapter for an open model.

## Important boundary

The initial seed file is a **small starter dataset**, not enough to create a frontier model. Fine-tuning teaches response format and project-specific behaviour; it does not replace retrieval, tools, or a capable base model. The adapter is not trained until a GPU run finishes and writes artifacts. GitHub Pages is static hosting and cannot train model weights.

The current pipeline uses Hugging Face Transformers + TRL SFTTrainer + PEFT LoRA, following the upstream [TRL PEFT guide](https://huggingface.co/docs/trl/peft_integration). Check each base model and dataset license before commercial use.

## Run on a CUDA GPU

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r training/requirements-training.txt
python training/train_lora.py --model Qwen/Qwen3-0.6B --epochs 3
```

For 4-bit QLoRA where supported:

```bash
python training/train_lora.py --model Qwen/Qwen3-0.6B --qlora --batch-size 1 --grad-accum 16
```

Output defaults to `artifacts/aksi-lora`. Keep generated weights out of Git unless they are small enough and licensing allows it. Use a model registry or artifact storage for large files.

## Before using a trained adapter

1. Expand the dataset with reviewed, licensed examples from project documentation and user-approved data. Do not scrape or train on private chat history without explicit consent.
2. Deduplicate examples and remove secrets, tokens, keys, and personal data that is not required.
3. Keep a held-out evaluation set that is not included in training.
4. Compare base and adapter on the same prompts: factuality, Russian instruction following, memory use, math/tool selection, refusal boundaries and regression rate.
5. Only deploy if the adapter improves the metrics. Preserve a rollback to the base model.

## Connect to runtime

The current production gateway supports xAI/OpenAI-compatible APIs and Ollama. The adapter must be loaded by a compatible inference runtime (for example a Transformers/vLLM deployment or an Ollama-compatible converted model) before it affects live answers. Saving an adapter to this repository does not automatically deploy it.
