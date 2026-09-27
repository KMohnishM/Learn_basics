# CHEATSHEET: Fine-Tuning and Alignment

## Customization Spectrum Decision Matrix

| Approach | Difficulty | Compute Cost | Use Case | Changes Weights? | Hallucination Risk |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Prompting** | Low | None (Inference only) | Formatting, basic reasoning, zero-shot tasks | No | High |
| **RAG** | Medium | Low (Vector DB + Inference) | Private data, factual accuracy, living knowledge bases | No | Low |
| **SFT (LoRA)** | High | Medium (1x GPU for 8B) | Specific behaviors, tone, complex output formatting | Yes | Medium |
| **Pre-training** | Extreme | Astronomical (Cluster) | Fundamentally new domains, languages, massive corpora | Yes | Varies |

## LoRA & QLoRA Hyperparameter Tuning Guide

| Parameter | Recommended Starting Value | Impact / Notes |
| :--- | :--- | :--- |
| **Rank (`r`)** | 8 or 16 | The information bottleneck. Use 8 for simple styling, 64 for complex reasoning tasks. |
| **Alpha (`lora_alpha`)** | `2 * r` (e.g., 16 or 32) | Scaling factor. Always keep a constant ratio relative to `r` when tuning. |
| **Dropout** | 0.05 or 0.1 | Regularization. Increase if validation loss diverges from training loss. |
| **Learning Rate** | `2e-4` (SFT), `5e-6` (DPO) | LoRA requires higher learning rates than full fine-tuning. DPO requires very low LR. |
| **Target Modules** | `all-linear` (Attention + MLP) | Targeting only Q and V projections is outdated. Target all linear layers for best results. |

## Quick Reference: QLoRA Architecture

```text
======================= FORWARD PASS =======================
Input (X) 
   │
   ├──> [ 4-bit Base Matrix (W0) ] ────> (Dequantize to bf16) ────> X * W0
   │                                                                 +
   └──> [ 16-bit LoRA Adapter A  ] ──> [ 16-bit LoRA Adapter B ] ─> X * BA
                                                                     =
                                                                Output (Y)
============================================================
```

## Hugging Face SFTTrainer Template

```python
# Minimal viable QLoRA SFT setup
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer
import torch

# 1. 4-bit Config
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True, bnb_4bit_quant_type="nf4", 
    bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True
)

# 2. Load Model
model = AutoModelForCausalLM.from_pretrained("meta-llama/Meta-Llama-3-8B-Instruct", quantization_config=bnb_config)
model = prepare_model_for_kbit_training(model)
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B-Instruct")

# 3. Apply LoRA
peft_config = LoraConfig(r=16, lora_alpha=32, target_modules="all-linear", bias="none", task_type="CAUSAL_LM")
model = get_peft_model(model, peft_config)

# 4. Train
args = TrainingArguments(output_dir="./out", per_device_train_batch_size=4, optim="paged_adamw_32bit")
trainer = SFTTrainer(model=model, args=args, train_dataset=my_dataset, dataset_text_field="text", peft_config=peft_config)
trainer.train()
```

## VRAM Hardware Requirements Reference Table

| Model Size | Full FT (16-bit) | LoRA (16-bit base) | QLoRA (4-bit base) | Min GPU Recommendation (QLoRA) |
| :--- | :--- | :--- | :--- | :--- |
| **7B - 8B** | ~80 GB | ~24 GB | **~10 GB** | 1x RTX 3060 (12GB) or RTX 4070 |
| **13B - 14B** | ~140 GB | ~48 GB | **~18 GB** | 1x RTX 3090 / 4090 (24GB) |
| **32B - 34B** | ~350 GB | ~96 GB | **~35 GB** | 2x RTX 3090 / 4090 (Pipeline Par.) |
| **70B - 72B** | ~750 GB | ~160 GB | **~60 GB** | 1x A100 (80GB) or 3x RTX 3090 |
| **104B+** | >1 TB | ~240 GB | **~85 GB** | 2x A100 (80GB) |

*Note: VRAM estimates assume batch size of 1-4 with gradient checkpointing enabled.*
