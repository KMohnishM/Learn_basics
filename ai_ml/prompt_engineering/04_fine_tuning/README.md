# Module 4: Prompt Engineering & Advanced Reasoning - Fine-Tuning and Alignment

## 1. The Customization Spectrum

When deploying Large Language Models (LLMs) to production, practitioners face a critical architectural decision: how to adapt a general-purpose model to their specific domain, task, or organizational knowledge. This decision space is known as the Customization Spectrum. The spectrum ranges from low-effort, training-free methods (Prompt Engineering and RAG) to high-effort, compute-intensive methods (Fine-Tuning and Pre-training). 

Understanding where your use case falls on this spectrum is the most important prerequisite to building an AI system. Choosing the wrong customization strategy can result in massive technical debt, exorbitant compute costs, or catastrophic degradation of model capabilities.

### 1.1 Prompt Engineering (Zero-Shot, Few-Shot, Chain-of-Thought)
Prompt engineering is the baseline for all LLM interactions. It involves modifying the input context at inference time without altering the underlying model weights. 
- **Mechanism:** In-context learning. The model uses its existing parametric knowledge and adapts its statistical outputs based on the provided text.
- **When to use:** For general tasks, rapid prototyping, formatting output, or when the task can be fully specified within the context window limits.
- **Limitations:** Context window constraints, higher inference costs (more tokens to process), latency, and inability to teach the model fundamentally new knowledge or complex, deeply nuanced behaviors that require thousands of examples.

### 1.2 Retrieval-Augmented Generation (RAG)
RAG combines the parametric knowledge of the LLM with non-parametric external knowledge retrieved from a database (usually a vector database).
- **Mechanism:** A query is embedded, relevant chunks are retrieved from a knowledge base, and these chunks are dynamically injected into the prompt before generation.
- **When to use:** When the application requires access to private, proprietary, or constantly updating information. RAG is the gold standard for reducing hallucinations on factual, knowledge-intensive tasks.
- **Limitations:** Dependent on the quality of the retriever. If the retriever fails, the generator fails. RAG does not change the "style" or intrinsic capabilities of the model.

### 1.3 Parameter-Efficient Fine-Tuning (PEFT) and Supervised Fine-Tuning (SFT)
Fine-tuning involves actually updating the model's weights based on a dataset of examples. SFT teaches the model how to behave, how to format its output, or how to reason through specific types of problems.
- **Mechanism:** Gradient descent. The model is trained on domain-specific data to minimize a loss function (usually Cross-Entropy Loss on the next token). PEFT techniques like LoRA allow us to train only a small fraction of the weights.
- **When to use:** When the model needs to learn a specific style, tone, or complex behavior that cannot be reliably elicited via prompting. When you want to reduce prompt length (moving few-shot examples into the weights). 
- **Limitations:** High compute costs, risk of catastrophic forgetting (where the model loses its general knowledge), and complex dataset curation requirements.

### 1.4 Continued Pre-training (Domain Adaptation)
This is the process of taking a base model and continuing the pre-training phase on a massive corpus of unstructured domain-specific text (e.g., medical journals, legal documents, or specialized programming languages).
- **Mechanism:** Self-supervised learning (next-token prediction) on raw text, updating all model weights.
- **When to use:** When the target domain has a vocabulary, syntax, or knowledge base that is fundamentally unrepresented in the original pre-training data.
- **Limitations:** Astronomically expensive, requires millions or billions of tokens, highly susceptible to catastrophic forgetting, and requires massive GPU clusters.

---

## 2. Dataset Preparation & Formatting

The quality of a fine-tuned model is entirely dependent on the quality of its dataset. The "LIMA (Less Is More for Alignment)" hypothesis suggests that a small number (e.g., 1,000) of extremely high-quality, carefully curated examples can outperform tens of thousands of mediocre examples.

### 2.1 Standard Formats: Alpaca and ShareGPT
There are two dominant data formats in the open-source fine-tuning ecosystem: Alpaca and ShareGPT.

#### Alpaca Format
The Alpaca format was popularized by the Stanford Alpaca project. It uses a flat, instruction-response structure.
```json
[
  {
    "instruction": "Evaluate the following mathematical expression.",
    "input": "4 * (3 + 2)",
    "output": "The expression evaluates to 20. First, we add the numbers in the parentheses: 3 + 2 = 5. Then, we multiply the result by 4: 4 * 5 = 20."
  },
  {
    "instruction": "Translate the sentence to French.",
    "input": "The weather is beautiful today.",
    "output": "Le temps est magnifique aujourd'hui."
  }
]
```
While simple, the Alpaca format is inherently limited because it only supports single-turn interactions. It cannot easily represent multi-turn conversations.

#### ShareGPT Format
The ShareGPT format is designed for multi-turn conversational data. It is the modern standard for chat models.
```json
[
  {
    "conversations": [
      {
        "from": "system",
        "value": "You are a helpful, precise coding assistant."
      },
      {
        "from": "human",
        "value": "How do I reverse a list in Python?"
      },
      {
        "from": "gpt",
        "value": "You can reverse a list in Python using the `reverse()` method, slicing `[::-1]`, or the `reversed()` function."
      },
      {
        "from": "human",
        "value": "Which one is the most memory efficient?"
      },
      {
        "from": "gpt",
        "value": "The `reverse()` method is the most memory efficient as it reverses the list in place, requiring O(1) extra space."
      }
    ]
  }
]
```

### 2.2 DataCollatorForCompletionOnlyLM
During Supervised Fine-Tuning, we feed the model a sequence containing both the prompt (user instruction) and the target completion. However, we only want the model to learn to generate the completion. If we compute the loss over the prompt tokens, the model will waste capacity learning how to predict user instructions.

To solve this, we use a custom data collator that masks out the labels for the prompt tokens, setting them to -100 (which PyTorch's CrossEntropyLoss ignores).

```python
from trl import DataCollatorForCompletionOnlyLM
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B-Instruct")
tokenizer.pad_token = tokenizer.eos_token

# We identify the tokens that signal the start of the assistant's response.
# For Llama 3 ChatML/Instruct format, this is typically the <|start_header_id|>assistant<|end_header_id|> sequence.
response_template = "<|start_header_id|>assistant<|end_header_id|>\n\n"
response_template_ids = tokenizer.encode(response_template, add_special_tokens=False)

# The collator will find the response_template in the sequence and set all preceding labels to -100.
collator = DataCollatorForCompletionOnlyLM(
    response_template=response_template_ids,
    tokenizer=tokenizer,
    mlm=False
)
```

By ensuring that the loss is only computed on the assistant's tokens, we force the gradient updates to focus entirely on improving the quality of the model's responses.

---

## 3. Parameter-Efficient Fine-Tuning (PEFT): LoRA & QLoRA

Training a modern LLM (like a 70B parameter model) from scratch or performing full fine-tuning requires hundreds of gigabytes of VRAM. Parameter-Efficient Fine-Tuning (PEFT) methods allow us to adapt these models using consumer hardware.

### 3.1 The Mathematics of LoRA (Low-Rank Adaptation)
LoRA operates on a simple but profound mathematical principle: while the pre-trained weight matrices of an LLM are massive and full-rank, the *updates* required to adapt the model to a specific task have a very low intrinsic rank.

Let $W_0 \in \mathbb{R}^{d \times k}$ be a pre-trained weight matrix in a linear layer (such as the Query or Value projections in multi-head attention). During standard fine-tuning, we would update this matrix by adding a delta:
$$ W_{new} = W_0 + \Delta W $$
Where $\Delta W$ has the exact same dimensions as $W_0$, requiring us to compute and store gradients for $d \times k$ parameters.

LoRA constrains the update matrix $\Delta W$ by representing it as the product of two low-rank matrices, $A$ and $B$:
$$ \Delta W = B \times A $$
Where:
- $A \in \mathbb{R}^{r \times k}$
- $B \in \mathbb{R}^{d \times r}$
- $r \ll \min(d, k)$ is the rank.

During training, $W_0$ is frozen and receives no gradient updates. Only $A$ and $B$ contain trainable parameters. The forward pass becomes:
$$ h = W_0 x + \Delta W x = W_0 x + B A x $$

If $d = 4096$, $k = 4096$, and we choose rank $r = 8$:
- Full Fine-Tuning parameters: $4096 \times 4096 = 16,777,216$
- LoRA parameters: $(4096 \times 8) + (8 \times 4096) = 32,768 + 32,768 = 65,536$
- Parameter reduction: 99.6%!

#### Initialization and Scaling
- Matrix $A$ is initialized with random Gaussian values.
- Matrix $B$ is initialized with zeros.
- Therefore, at the start of training, $\Delta W = B \times A = 0$, meaning the model behaves exactly like the base model.
- The update is scaled by a factor of $\frac{\alpha}{r}$, where $\alpha$ (alpha) is a hyperparameter. This scaling helps stabilize training when the rank $r$ is changed.

### 3.2 QLoRA (Quantized LoRA)
While LoRA reduces the number of *trainable* parameters, the base model $W_0$ still needs to be loaded into VRAM. A 70B model in 16-bit precision requires ~140GB of VRAM just to sit in memory. QLoRA solves this by quantizing the base model to 4-bit precision while keeping the LoRA adapters in 16-bit or 32-bit.

QLoRA introduces three critical innovations:
1. **NormalFloat4 (NF4) Data Type:** An information-theoretically optimal quantization data type for normally distributed weights. Neural network weights are roughly Gaussian. NF4 creates 16 quantization bins that have equal area under the standard normal distribution, maximizing the information retained in 4 bits.
2. **Double Quantization:** QLoRA quantizes the quantization constants themselves, saving an additional ~0.37 bits per parameter.
3. **Paged Optimizers:** Uses NVIDIA unified memory features to page optimizer states (like Adam's momentum and variance) to CPU RAM when GPU VRAM is full, preventing out-of-memory errors during memory spikes.

---

## 4. Alignment Techniques: SFT, DPO, and RLHF

Once a model has been pre-trained to predict the next token, it is a "base model" (like Llama-3-8B). Base models are not helpful assistants; if you prompt a base model with a question, it might just generate more questions. We must "align" the model.

### 4.1 Supervised Fine-Tuning (SFT)
SFT is behavioral cloning. We provide the model with high-quality demonstrations of desired behavior (human or synthetic). The model is trained using Cross-Entropy Loss:
$$ L_{SFT} = -\sum_{t=1}^{T} \log P(y_t | x, y_{<t}) $$
Where $x$ is the prompt, and $y_t$ is the target token at step $t$. SFT teaches the model the format of a conversation and the general style of a helpful assistant. However, SFT does not penalize the model for generating bad answers; it only encourages generating the specific answers in the dataset.

### 4.2 Reinforcement Learning from Human Feedback (RLHF/PPO)
RLHF was the breakthrough that made ChatGPT possible. It involves three steps:
1. Train an SFT model.
2. Train a Reward Model (RM) on human preference data (e.g., prompt $x$, chosen response $y_c$, rejected response $y_r$). The RM learns to output a scalar score representing human preference.
3. Use Proximal Policy Optimization (PPO), a reinforcement learning algorithm, to optimize the SFT model to generate responses that maximize the Reward Model's score, while adding a KL-divergence penalty to ensure the model doesn't drift too far from the original SFT model (which would result in catastrophic mode collapse or hacking the reward model).

RLHF is notoriously unstable, requires loading 4 different models into memory (Policy, Reference, Reward, Value), and involves highly sensitive hyperparameter tuning.

### 4.3 Direct Preference Optimization (DPO)
DPO mathematically proves that the exact same objective as RLHF can be optimized *without* a separate reward model and *without* reinforcement learning.

By manipulating the Bradley-Terry model of human preference, DPO expresses the optimal policy directly in terms of the chosen and rejected responses. The DPO loss function is a simple classification loss (similar to binary cross-entropy) on the difference in log probabilities between the policy model and the reference model:

$$ L_{DPO} = -\log \sigma \left( \beta \log \frac{\pi_\theta(y_c|x)}{\pi_{ref}(y_c|x)} - \beta \log \frac{\pi_\theta(y_r|x)}{\pi_{ref}(y_r|x)} \right) $$

Where:
- $\pi_\theta$ is the model we are training.
- $\pi_{ref}$ is the frozen reference model (the initial SFT model).
- $y_c$ is the chosen response, $y_r$ is the rejected response.
- $\beta$ controls the strength of the KL penalty (typically 0.1).

DPO is vastly simpler, more stable, and requires less memory than PPO, making it the dominant alignment algorithm in the open-source community today.

### 4.4 Odds Ratio Preference Optimization (ORPO)
ORPO is a recent advancement that combines SFT and preference alignment into a single, monolithic step. It eliminates the need for a separate reference model entirely, reducing memory requirements even further. It adds a penalty based on the odds ratio of generating the chosen response versus the rejected response directly to the standard cross-entropy loss.

---

## 5. End-to-End Training Pipeline in Python

This section provides a complete, production-ready script for performing QLoRA Supervised Fine-Tuning on a Llama-3 model using the Hugging Face ecosystem (`transformers`, `peft`, `trl`, `bitsandbytes`).

### 5.1 SFT Training Script

```python
import os
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    pipeline,
    logging,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer, DataCollatorForCompletionOnlyLM

# -----------------------------------------------------------------------------
# 1. Configuration & Hyperparameters
# -----------------------------------------------------------------------------
# We define all the necessary hyperparameters before initializing the training pipeline.
MODEL_NAME = "meta-llama/Meta-Llama-3-8B-Instruct"
DATASET_NAME = "HuggingFaceH4/ultrachat_200k"  # High-quality chat dataset
OUTPUT_DIR = "./llama-3-8b-sft-custom"

# LoRA Parameters
# r determines the intrinsic rank of the LoRA matrices (A and B).
# Higher r means more expressive power but requires more compute.
LORA_RANK = 16

# lora_alpha is a scaling factor for the weight updates.
# A common rule of thumb is to set alpha to 2x the rank.
LORA_ALPHA = 32

# lora_dropout is used for regularization to prevent overfitting on small datasets.
LORA_DROPOUT = 0.05

# Training Parameters
# Batch size is kept small to fit in consumer GPU VRAM. 
BATCH_SIZE = 4
# Gradient accumulation simulates a larger batch size by accumulating gradients over multiple steps.
GRADIENT_ACCUMULATION_STEPS = 4

# Learning rate for LoRA is typically higher than for full fine-tuning (e.g., 2e-4 vs 2e-5).
LEARNING_RATE = 2e-4
NUM_EPOCHS = 1
MAX_SEQ_LENGTH = 2048

# -----------------------------------------------------------------------------
# 2. BitsAndBytes QLoRA Configuration
# -----------------------------------------------------------------------------
# This configures the base model to be loaded in 4-bit precision using NF4
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16, # Use bfloat16 for computation on modern GPUs
    bnb_4bit_use_double_quant=True,       # Enable double quantization to save more VRAM
)

# -----------------------------------------------------------------------------
# 3. Load Model and Tokenizer
# -----------------------------------------------------------------------------
print(f"Loading tokenizer for {MODEL_NAME}...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
# Llama models don't have a pad token by default. We use the EOS token to pad shorter sequences.
tokenizer.pad_token = tokenizer.eos_token
# We must use right-padding for causal language models during training to ensure next-token prediction works correctly.
tokenizer.padding_side = "right" 

print(f"Loading base model {MODEL_NAME} in 4-bit...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=bnb_config,
    device_map="auto", # Automatically dispatch layers to available GPUs based on memory
    torch_dtype=torch.bfloat16
)

# Prepare the model for k-bit training (freezes base weights, casts layer norms to fp32)
# This is a crucial step to ensure training stability when using quantized base models.
model = prepare_model_for_kbit_training(model)

# -----------------------------------------------------------------------------
# 4. LoRA Adapter Configuration
# -----------------------------------------------------------------------------
# We target all linear layers in the attention mechanism and the MLP blocks
# This gives the model maximum flexibility to learn new behaviors across all layers.
target_modules = [
    "q_proj", "k_proj", "v_proj", "o_proj", 
    "gate_proj", "up_proj", "down_proj"
]

peft_config = LoraConfig(
    r=LORA_RANK,
    lora_alpha=LORA_ALPHA,
    lora_dropout=LORA_DROPOUT,
    bias="none",
    task_type="CAUSAL_LM",
    target_modules=target_modules
)

# Wrap the base model with the PEFT config to create the trainable adapters
model = get_peft_model(model, peft_config)
# This will output a summary showing the exact number of trainable parameters (usually ~1-2%).
model.print_trainable_parameters() 

# -----------------------------------------------------------------------------
# 5. Dataset Loading and Formatting
# -----------------------------------------------------------------------------
print(f"Loading dataset {DATASET_NAME}...")
# For demonstration, we load a small subset of the training split
dataset = load_dataset(DATASET_NAME, split="train_sft[:5000]")

def format_chat_template(example):
    """
    Applies the model's specific chat template to the conversation data.
    The Hugging Face tokenizer automatically handles ChatML or Llama-3 specific 
    formatting tags like <|start_header_id|> and <|eot_id|>.
    """
    conversation = example["messages"]
    # Apply chat template and return as text string.
    # We set add_generation_prompt=False because we are training, not doing inference.
    formatted_text = tokenizer.apply_chat_template(
        conversation, 
        tokenize=False, 
        add_generation_prompt=False
    )
    return {"text": formatted_text}

# Map the formatting function across the dataset, using multiple processors to speed up the transformation.
formatted_dataset = dataset.map(format_chat_template, num_proc=4)

# Define the data collator to only calculate loss on the assistant responses.
# This ensures the model learns to answer questions, not to ask them.
response_template = "<|start_header_id|>assistant<|end_header_id|>\n\n"
response_template_ids = tokenizer.encode(response_template, add_special_tokens=False)
collator = DataCollatorForCompletionOnlyLM(
    response_template=response_template_ids, 
    tokenizer=tokenizer,
    mlm=False
)

# -----------------------------------------------------------------------------
# 6. Training Configuration
# -----------------------------------------------------------------------------
# The TrainingArguments define the hyperparameters and logging settings for the training loop.
training_arguments = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=NUM_EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,
    # We use a 32-bit paged optimizer to offload state to CPU RAM if GPU VRAM spikes, preventing OOM.
    optim="paged_adamw_32bit", 
    save_steps=100,
    logging_steps=10,
    learning_rate=LEARNING_RATE,
    weight_decay=0.001,
    fp16=False,
    bf16=True, # Use bfloat16 for modern Ampere+ GPUs (e.g., RTX 3090, A100)
    max_grad_norm=0.3,
    max_steps=-1,
    warmup_ratio=0.03,
    group_by_length=True,
    lr_scheduler_type="cosine",
    report_to="tensorboard" # Log metrics to TensorBoard for visualization
)

# -----------------------------------------------------------------------------
# 7. Initialize Trainer and Train
# -----------------------------------------------------------------------------
# SFTTrainer is a high-level wrapper from the trl library that simplifies the setup
# of supervised fine-tuning pipelines.
trainer = SFTTrainer(
    model=model,
    train_dataset=formatted_dataset,
    peft_config=peft_config,
    dataset_text_field="text",
    max_seq_length=MAX_SEQ_LENGTH,
    tokenizer=tokenizer,
    args=training_arguments,
    data_collator=collator
)

print("Starting training loop...")
trainer.train()

# -----------------------------------------------------------------------------
# 8. Save the Final Adapter
# -----------------------------------------------------------------------------
print(f"Saving LoRA adapters to {OUTPUT_DIR}...")
# We only save the adapters, not the massive base model weights.
trainer.model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print("Training successfully complete!")
```

### 5.2 Merging Adapters for Inference

After training, you have the frozen base model and a small adapter folder containing the LoRA weights (`adapter_model.bin` or `adapter_model.safetensors`). For deployment (e.g., using vLLM), you often want to merge these adapters back into a single base model.

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch

BASE_MODEL = "meta-llama/Meta-Llama-3-8B-Instruct"
ADAPTER_PATH = "./llama-3-8b-sft-custom"
MERGED_OUTPUT = "./llama-3-8b-sft-merged"

print("Loading base model in fp16...")
# Note: We load the base model in standard fp16/bf16, NOT 4-bit, for merging.
# Merging a 16-bit adapter into a 4-bit quantized base model is mathematically complex
# and often results in significant degradation in model quality.
base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    low_cpu_mem_usage=True,
    return_dict=True,
    torch_dtype=torch.bfloat16,
    device_map="auto"
)

print("Loading PEFT adapters...")
# We load the small trained adapter matrices.
model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)

print("Merging LoRA weights with base model...")
# This performs the mathematical operation W_new = W_0 + (B * A) across all targeted layers.
merged_model = model.merge_and_unload()

print(f"Saving fully merged model to {MERGED_OUTPUT}...")
# We serialize the full new model, which can now be loaded directly into any inference engine.
merged_model.save_pretrained(MERGED_OUTPUT, safe_serialization=True)
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
tokenizer.save_pretrained(MERGED_OUTPUT)
print("Merge operation successfully complete!")
```

---

## 6. Implementing DPO (Direct Preference Optimization)

Once you have completed SFT, you can further align the model using DPO. The script is remarkably similar, but uses the `DPOTrainer` and requires a specialized preference dataset.

### 6.1 DPO Training Script

```python
import torch
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import DPOTrainer

MODEL_NAME = "./llama-3-8b-sft-merged" # We start with our merged SFT model
DATASET_NAME = "argilla/ultrafeedback-binarized-preferences-cleaned"
OUTPUT_DIR = "./llama-3-8b-dpo"

# 1. Load Dataset
print("Loading preference dataset...")
dataset = load_dataset(DATASET_NAME, split="train_prefs[:2000]")

# 2. QLoRA Config
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16
)

# 3. Load Models
# In DPO, we technically need a Policy model and a Reference model.
# trl handles the Reference model automatically for us (or we can pass it).
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME, quantization_config=bnb_config, device_map="auto"
)
model = prepare_model_for_kbit_training(model)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
tokenizer.pad_token = tokenizer.eos_token

# 4. Apply LoRA
peft_config = LoraConfig(
    r=16, lora_alpha=32, target_modules=["q_proj", "v_proj"], task_type="CAUSAL_LM"
)
model = get_peft_model(model, peft_config)

# 5. DPO Training Arguments
dpo_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=8,
    learning_rate=5e-6, # DPO requires an extremely small learning rate
    optim="paged_adamw_32bit",
    num_train_epochs=1,
    bf16=True,
    logging_steps=10
)

# 6. Initialize DPOTrainer
trainer = DPOTrainer(
    model=model,
    args=dpo_args,
    beta=0.1, # The KL penalty coefficient
    train_dataset=dataset,
    tokenizer=tokenizer,
    peft_config=peft_config
)

print("Starting DPO training...")
trainer.train()
trainer.model.save_pretrained(OUTPUT_DIR)
```

---

## 7. Evaluating the Fine-Tuned Model

Training loss is an insufficient metric for LLM success. You must rigorously evaluate your fine-tuned model against the base model to ensure no catastrophic forgetting occurred.

### 7.1 EleutherAI LM Evaluation Harness
The `lm-evaluation-harness` is the industry standard for running standardized benchmarks like MMLU, GSM8K, and HumanEval.

```bash
# Example command to run the MMLU (Massive Multitask Language Understanding) benchmark
lm_eval --model hf \
    --model_args pretrained=./llama-3-8b-sft-merged \
    --tasks mmlu \
    --device cuda:0 \
    --batch_size auto
```

### 7.2 Interpreting Results
When reviewing your evaluation results, check for the following:
1. **Target Metric Improvements:** Did performance improve on your domain-specific validation set? (This is the primary goal).
2. **General Capability Retention:** Did MMLU or ARC scores drop significantly? If they fell by more than 2-3 points, your model has likely suffered catastrophic forgetting. You should re-train with a lower learning rate or a smaller LoRA rank.
3. **Overfitting Artifacts:** Does the model suddenly generate `<|end_of_text|>` tokens prematurely, or repeat the same phrase endlessly? This implies overfitting to the dataset formatting.

---

## 8. Common Pitfalls and Troubleshooting

When undertaking fine-tuning or alignment training, several common failure modes often arise. Below are troubleshooting steps to mitigate them.

### 8.1 Catastrophic Forgetting
**Symptom:** The model performs well on your new domain but scores terribly on general tasks like MMLU or coding, or it loses its ability to follow simple instructions.
**Solution:** 
- Lower the learning rate and reduce the number of epochs (try 1-2 epochs max).
- Implement a replay buffer: mix 10-20% general instruction data (like Alpaca or an UltraChat subset) into your domain-specific dataset.
- Reduce the LoRA rank (`r`). A massive rank gives the model too much capacity to overwrite core knowledge.

### 8.2 Loss Spikes and Instability (NaN Loss)
**Symptom:** The training loss suddenly spikes to infinity or becomes `NaN` during the middle of the training run.
**Solution:**
- Ensure you are using `torch.bfloat16` instead of `float16`. Standard `float16` has a smaller numerical range and is prone to overflow gradients.
- Check for corrupted data or extremely long sequences in your dataset.
- Increase the warmup steps (`warmup_ratio=0.1`) to ease the optimizer into the learning process.

### 8.3 Out of Memory (OOM) Errors
**Symptom:** The training crashes with a CUDA Out of Memory error right at the start or during validation.
**Solution:**
- Reduce the `per_device_train_batch_size`.
- Ensure gradient checkpointing is enabled in the training arguments.
- Switch to a paged optimizer (`paged_adamw_8bit` or `paged_adamw_32bit`).
- Lower the `max_seq_length` to truncate longer examples.

### Conclusion
Fine-tuning is a powerful tool, but it is an art as much as a science. Start with prompt engineering. If that fails, move to RAG. Only when you need specialized behavioral formatting, complex reasoning patterns, or massive context reduction should you embark on the PEFT pipeline. When you do, QLoRA and DPO provide the most robust, accessible path to state-of-the-art custom models.
