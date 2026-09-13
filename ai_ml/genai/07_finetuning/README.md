# Module 7: Fine-Tuning LLMs

Fine-tuning is not the right tool for most problems. Before spending compute time and money on fine-tuning, ask yourself: can prompt engineering or RAG solve this instead?

**Use fine-tuning when:**
- You need the model to consistently follow a very specific output format or style
- You need to reduce prompt length (fine-tuned behavior needs no examples in the prompt)
- You need significantly better performance on a narrow, specialized domain
- You have high-quality labeled data (500+ examples minimum; 5000+ preferred)

**Don't use fine-tuning when:**
- You need access to recent information (use RAG)
- You just need to teach the model new facts (use RAG)
- You haven't tried aggressive prompt engineering first

---

## 1. How Pre-Training and Fine-Tuning Relate

### Pre-Training
LLaMA-3, GPT-4, and Mistral are pre-trained on trillions of tokens from the internet. This gives them broad world knowledge and the ability to predict the next token. The resulting model is called a **base model** — it can continue text but doesn't follow instructions.

### Instruction Fine-Tuning (IFT / SFT)
The base model is further trained on (instruction, response) pairs to teach it to follow instructions. This is called **Supervised Fine-Tuning (SFT)**. The result is the "chat" version of a model.

### RLHF (Reinforcement Learning from Human Feedback)
Human raters rank model responses. These rankings train a **Reward Model**. The base model is then optimized using PPO to maximize the Reward Model's scores. This is what makes models "helpful, harmless, and honest."

### DPO (Direct Preference Optimization)
A simpler alternative to RLHF. Instead of training a separate reward model, DPO directly optimizes the language model from human preference data (pairs of "preferred" vs "rejected" responses). DPO requires less compute and is more stable than PPO.

---

## 2. Full Fine-Tuning vs PEFT

### Full Fine-Tuning
Update all parameters of the model. For a 7B model, you're updating 7 billion weights. Requires massive GPU RAM (e.g., a 7B model in fp32 needs ~28GB of GPU RAM just for the weights — before gradients).

**Not feasible on consumer hardware.**

### Parameter-Efficient Fine-Tuning (PEFT)
Only update a small fraction of the parameters while keeping the rest frozen.

---

## 3. LoRA — Low-Rank Adaptation

LoRA (Hu et al., 2022) is the dominant PEFT technique. The key insight:

> The weight updates during fine-tuning have a low "intrinsic rank." This means we can represent the update as the product of two small matrices instead of one large matrix.

For a weight matrix `W` of dimension (d × k), LoRA adds two small matrices:
- `A` of dimension (d × r)
- `B` of dimension (r × k)

where `r` (rank) is much smaller than both `d` and `k` (typically `r = 8` to `r = 64`).

The updated weight becomes: `W' = W + α * (A × B)`

where `α` (alpha) is a scaling factor.

**Why this works**: Full fine-tuning changes all d×k weights. LoRA only changes d×r + r×k weights. For r=16, d=4096, k=4096: LoRA uses 131,072 parameters vs 16,777,216 — **128x fewer parameters**!

The original `W` is frozen and never changes. Only `A` and `B` are trained.

### Choosing Rank (r) and Alpha (α)

- **r=8**: Light fine-tuning, small style changes. Fast training.
- **r=16**: Standard choice. Good balance of quality and efficiency.
- **r=64**: Heavy fine-tuning, large domain shifts.
- **α**: Usually set to 2× the rank. `r=16 → α=32`.

### Which Layers to Apply LoRA To

LoRA is typically applied to the attention projection matrices: `q_proj`, `v_proj` (minimum), and optionally `k_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj` for stronger adaptation.

---

## 4. QLoRA — Fine-Tuning on a Single GPU

Even with LoRA, a 7B model needs ~14GB GPU RAM (fp16). Not everyone has an A100.

**QLoRA** (Dettmers et al., 2023) adds quantization to LoRA:
1. Quantize the base model to **4-bit** (using NF4 — NormalFloat4 format). Memory: 7B × 0.5 bytes ≈ **3.5GB** for the base model.
2. Keep LoRA adapters in **bf16** (16-bit). They're tiny, so this is fine.
3. Use **paged optimizers** to offload optimizer states to CPU RAM when GPU is full.

Result: Fine-tune LLaMA-3-8B on a **free Google Colab T4 GPU** (16GB VRAM).

---

## 5. Dataset Formats

### Alpaca Format (Instruction Tuning)
```json
{
  "instruction": "Classify the sentiment of this tweet.",
  "input": "This new phone is absolutely incredible! Best purchase ever!",
  "output": "POSITIVE"
}
```

### ShareGPT Format (Multi-turn Conversations)
```json
{
  "conversations": [
    {"from": "human", "value": "What is LoRA?"},
    {"from": "gpt", "value": "LoRA (Low-Rank Adaptation) is a parameter-efficient..."},
    {"from": "human", "value": "How does it compare to full fine-tuning?"},
    {"from": "gpt", "value": "Full fine-tuning updates all model weights..."}
  ]
}
```

### Data Quality Over Quantity
- 1,000 high-quality examples >> 100,000 mediocre examples.
- Each example should represent behavior you actually want.
- Avoid examples with factual errors, inconsistent formatting, or contradictory instructions.

---

## 6. The Training Loop (with HuggingFace + PEFT + TRL)

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer, SFTConfig

# 1. Load model in 4-bit quantization (QLoRA)
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype="bfloat16",
)

model = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-v0.1",
    quantization_config=bnb_config,
    device_map="auto",
)

# 2. Configure LoRA
lora_config = LoraConfig(
    r=16,                    # Rank
    lora_alpha=32,           # Alpha = 2 * rank
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

# Apply LoRA adapters to the model
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# Trainable params: 13,631,488 (0.20% of total!) — that's the power of LoRA

# 3. Train
trainer = SFTTrainer(
    model=model,
    train_dataset=your_dataset,
    args=SFTConfig(
        output_dir="./output",
        num_train_epochs=3,
        per_device_train_batch_size=4,
        learning_rate=2e-4,
        fp16=True,
    ),
)

trainer.train()

# 4. Save only the LoRA adapters (a few MB, not the full 14GB model!)
model.save_pretrained("./my_lora_adapters")
```

---

## 7. Evaluation

### Automated Metrics
- **ROUGE**: Measures n-gram overlap between generated and reference text. Good for summarization.
- **BLEU**: Similar to ROUGE, widely used for translation. Not great for open-ended generation.
- **Perplexity**: How "surprised" the model is by a held-out test set. Lower = better.

### The Real Metric: Human Evaluation
Automated metrics correlate poorly with human judgement for chat and instruction following. Always pair automated metrics with human evaluation.

### Before Fine-Tuning, Establish a Baseline
- Run your test set through the base model.
- Record baseline accuracy/quality.
- Fine-tune.
- Compare. Fine-tuning should only proceed if it meaningfully improves on the baseline.

---

## Next Steps

Check out the `exercise/` for a guided approach to preparing your own fine-tuning dataset and running QLoRA on Google Colab!
