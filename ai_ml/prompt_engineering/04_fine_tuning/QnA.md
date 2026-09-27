# Questions and Answers: Prompt Engineering & Advanced Reasoning (Module 4)

### 1. Provide a comprehensive decision framework comparing Prompt Engineering, RAG, Supervised Fine-Tuning (SFT), and Continued Pre-training.
**Answer:**

The decision framework for model customization hinges on several factors:
- The specific task requirements.
- The volatility of the underlying knowledge.
- The available compute resources.
- The latency constraints of the production environment.

**Prompt Engineering (Zero/Few-Shot):**
This should always be the starting point. 
It is training-free, requires zero infrastructure changes, and leverages existing parametric knowledge. 
Use it for general reasoning, text transformation, and basic formatting. 
However, it consumes valuable context window space.

**Retrieval-Augmented Generation (RAG):**
Introduce RAG when the application requires access to external or factual data. 
RAG solves the knowledge cutoff problem but does not change the model's fundamental behavior. 
It is highly resistant to hallucination.

**Supervised Fine-Tuning (SFT):**
Choose SFT when the model must adopt a highly specific style or persona.
It embeds the *behavior* directly into the weights, saving context window space.
However, it is notoriously poor at memorizing new factual knowledge.

**Continued Pre-training:**
Only attempt this when adapting the model to a fundamentally new domain.
This approach requires thousands of GPUs, millions of dollars, and massive text corpora.

### 2. Explain the mathematical mechanics of LoRA (Low-Rank Adaptation). How does decomposing delta W into matrices A and B drastically reduce trainable parameters?
**Answer:**

During standard full fine-tuning, updating a pre-trained weight matrix $W_0$ requires learning a gradient update matrix $\Delta W$.
This matrix has the exact same dimensions ($d \times k$). 
For modern LLMs, this means tracking tens of millions of parameters per layer.
This demands immense memory for optimizer states.

LoRA hypothesizes that the intrinsic rank of the adaptations needed is very low. 
Therefore, instead of learning the massive $\Delta W$ directly, LoRA constrains $\Delta W$.
It represents it as the matrix product of two smaller matrices: $\Delta W = B \times A$.

- Matrix $A$ has dimensions $r \times k$ and is initialized with random Gaussian values.
- Matrix $B$ has dimensions $d \times r$ and is initialized with zeros.
- Here, $r$ is the "rank" (a hyperparameter, typically between 8 and 64), and $r \ll \min(d, k)$. 

By freezing the massive $W_0$ matrix and only computing gradients for $A$ and $B$, parameters drop significantly.
For a $4096 \times 4096$ matrix with $r=8$, parameters drop from 16.7 million to just 65,536.
This represents a ~99.6% reduction in compute and memory overhead.

### 3. What is QLoRA, and what are its three core innovations (NF4 quantization, Double Quantization, Paged Optimizers)?
**Answer:**

While standard LoRA significantly reduces the number of *trainable* parameters, it still requires the massive base model weights.
These weights must be loaded into VRAM, often in 16-bit precision. 
QLoRA solves this memory bottleneck by heavily quantizing the base model to 4-bit precision.
The small, trainable LoRA adapters are kept in higher precision (16-bit or 32-bit). 

QLoRA relies on three core algorithmic and systems innovations:

1. **NormalFloat4 (NF4) Quantization:** 
Standard quantization spaces bins evenly. 
However, neural network weights usually follow a Gaussian (normal) distribution. 
NF4 spaces its 16 quantization bins so that there is an equal area under the standard normal curve in each bin. 

2. **Double Quantization:** 
Quantizing millions of parameters requires storing quantization constants for each block of weights. 
Double Quantization takes these 32-bit constants and quantizes them a second time down to 8-bit.
This saves an average of 0.37 bits per parameter.

3. **Paged Optimizers:** 
Optimizer states require significant memory that can spike unpredictably. 
QLoRA leverages NVIDIA unified memory to transparently page these optimizer states out to CPU RAM.
This prevents Out-Of-Memory (OOM) crashes during training.

### 4. What is the role of the LoRA hyperparameters: rank r, scaling factor alpha, and dropout? How does the alpha/r scaling factor stabilize training?
**Answer:**

The effectiveness of a LoRA adapter is highly dependent on tuning three primary hyperparameters:

**Rank ($r$):** 
This dictates the informational bottleneck of the adapter. 
A higher rank allows the adapter to learn more complex transformations.
However, it increases memory usage and the risk of overfitting. 
Common values are 8, 16, 32, and 64 depending on task complexity.

**Alpha ($\alpha$):** 
This is a scaling factor applied to the output of the LoRA adapter. 
During the forward pass, the adapter's output is scaled by $\frac{\alpha}{r}$. 

**Stabilizing Training:** 
The $\frac{\alpha}{r}$ scaling mechanism ensures stability as you change the rank $r$.
The overall magnitude of the LoRA update remains relatively constant. 
Without this scaling, increasing $r$ would mathematically increase the magnitude of the adapter's output sum.
Usually, setting $\alpha = 2 \times r$ is a strong starting heuristic.

**Dropout:** 
LoRA dropout randomly zeroes out elements of the adapter output during the training forward pass. 
This prevents the very small number of parameters from simply memorizing the training dataset.
It acts as a crucial regularization technique.

### 5. Why is it standard practice to compute cross-entropy loss only on the assistant completion tokens rather than the prompt tokens during SFT?
**Answer:**

Supervised Fine-Tuning (SFT) is fundamentally an exercise in behavioral cloning. 
The goal is to teach the model how to *respond* to user instructions, not how to *generate* the instructions themselves. 

During training, the model receives a concatenated sequence of the user prompt and the target assistant response. 
The objective function is next-token prediction using standard Cross-Entropy Loss. 

If we compute the loss over the prompt tokens, we force the model to update its weights poorly.
It learns to better predict what a user is going to ask next based on the system prompt. 
This is detrimental for two major reasons:

1. **Wasted Capacity:** 
The model wastes its limited parameter capacity learning to emulate user query distributions.
It should be focusing entirely on being a helpful, precise assistant.

2. **Hallucination Risk:** 
It can cause the model to spontaneously generate user prompts during inference.
This leads to weird behaviors where the model tries to play both sides of the conversation.

By masking the prompt tokens (setting their labels to -100 in PyTorch), the loss calculation entirely ignores them. 
The model only receives gradient updates based on its accuracy in predicting the assistant's tokens.

### 6. Explain the Direct Preference Optimization (DPO) algorithm. How does DPO mathematically bypass the need for training a separate reward model as in RLHF/PPO?
**Answer:**

Traditional RLHF involves three complex, unstable phases: 
1. Training an SFT model.
2. Training a separate Reward Model (RM) to predict human preferences.
3. Using PPO to optimize the SFT policy against the RM. 

This requires immense memory to hold multiple models and is highly prone to reward hacking.
DPO mathematically bypasses the RM and the complex RL phase entirely. 
Researchers demonstrated that the mathematical objective of RLHF can be analytically re-parameterized. 

In DPO, the optimal policy can be expressed directly in terms of two things:
- The initial SFT reference model.
- The preference data (chosen vs. rejected responses). 

DPO turns the RL problem back into a simple, stable classification problem. 
The algorithm minimizes a loss function based on the log probabilities of the chosen and rejected responses.
It mathematically enforces that the policy model should assign higher relative probability to the chosen response.
This entirely bypasses the need for a standalone Reward Model.

### 7. What is the LIMA (Less Is More for Alignment) hypothesis, and what implications does it have for dataset curation?
**Answer:**

The LIMA hypothesis proposes that almost all factual knowledge is learned early on.
Specifically, core reasoning capabilities are learned during the massive, unstructured pre-training phase. 
The alignment phase (SFT) does not teach the model new facts.
Rather, it simply teaches the model the specific *format* and *style* of interacting with users.

The core implication is that dataset *quantity* is vastly less important than dataset *quality*. 

The LIMA authors demonstrated this by fine-tuning a base model on just 1,000 highly curated examples.
This small dataset produced a model that rivaled models fine-tuned on 500,000 lower-quality examples.

For practitioners, this means resources should be allocated to hand-crafting a small, immaculate dataset. 
Every example should have:
- Perfect grammar.
- Exceptional reasoning steps.
- Absolutely zero artifacts.
- The exact tone desired.

"Garbage in, garbage out" is amplified exponentially in SFT.

### 8. How does Catastrophic Forgetting occur during domain-specific fine-tuning, and what techniques (like mixing general pre-training data or replay buffers) mitigate it?
**Answer:**

Catastrophic forgetting occurs when a neural network is trained on a new, highly specialized dataset.
It completely loses its ability to perform general tasks it previously mastered. 
Because standard gradient descent blindly optimizes for the new data distribution, it overwrites weights.
It heavily overwrites the intricate weight distributions that supported older, broader knowledge.

For example, if you perform full fine-tuning on an LLM exclusively using a dataset of Python code:
It might suddenly lose its ability to speak French or summarize historical documents.

To mitigate catastrophic forgetting, practitioners must use several deliberate strategies:

1. **Low Learning Rates & Few Epochs:** 
SFT is usually strictly limited to 1-3 epochs with very small learning rates.
This prevents massive, destructive weight shifts.

2. **PEFT/LoRA:** 
By freezing the base model and only training a small adapter, the core knowledge remains intact.

3. **Data Mixing / Replay Buffers:** 
If performing full fine-tuning, you should aggressively mix high-quality general instruction data.
Mix data (like Alpaca) into your domain-specific dataset (often in a 10:1 or 5:1 ratio). 
This forces the model to continuously "remember" how to be a general-purpose assistant.

### 9. Compare RLHF with PPO to DPO. Why has DPO become the dominant alignment approach for open-source models?
**Answer:**

RLHF with PPO was the pioneering alignment technique used to create ChatGPT. 
However, PPO is a highly complex actor-critic RL algorithm that requires maintaining four distinct models in memory: 
1. The Actor (Policy being trained)
2. The Reference model (frozen SFT)
3. The Reward Model
4. The Value Network

This creates astronomical VRAM requirements and necessitates complex distributed training setups. 
Furthermore, PPO is highly sensitive to hyperparameters and prone to reward hacking and mode collapse.

DPO (Direct Preference Optimization), conversely, requires only two models in memory: 
- The Policy model being trained.
- The frozen Reference model. 

There is no separate Reward Model and no Value Network. 
DPO formulates alignment as a straightforward cross-entropy-style classification loss.
Because it relies on standard, stable gradient descent, DPO is dramatically more stable.
Due to its reduced hardware requirements and superior stability, DPO has entirely usurped PPO.

### 10. What is the difference between merging LoRA weights with the base model versus serving the base model with dynamic LoRA adapter loading (e.g., in vLLM)?
**Answer:**

After training a LoRA adapter, you are left with a massive frozen base model and a small adapter folder.

**Merging:** 
Merging involves performing the matrix addition $W_{new} = W_0 + (B \times A)$ offline. 
You save a brand new, massive model checkpoint that contains the updated weights natively. 
The advantage is that inference code requires no modifications; it just loads the model normally. 
There is zero latency overhead, and the model behaves exactly like a fully fine-tuned model.

**Dynamic Loading (Multi-LoRA):** 
Alternatively, you can load the massive base model into GPU memory exactly once.
Then, dynamically apply different LoRA adapters at runtime on a per-request basis. 
Because LoRA adapters are tiny (e.g., 50MB to 200MB), an inference server can hold hundreds of them in RAM. 

When a request comes in, the server routes the tensors through the base model.
It dynamically computes the $+ (B \times A)$ step only for the specific adapter requested. 
This allows a single massive GPU cluster to serve thousands of completely different fine-tuned models.

### 11. How do you evaluate a fine-tuned model's performance to ensure it didn't overfit or lose general reasoning abilities?
**Answer:**

Evaluating an LLM requires a multi-faceted, rigorous approach.
A single loss metric during training is profoundly misleading. 
A model with perfectly decreasing training loss has likely severely overfit.

1. **General Capability Benchmarks:** 
After training, you must run standard benchmarks like MMLU, GSM8K, and HumanEval.
Use tools like EleutherAI's `lm-evaluation-harness`. 
If your base model scored 70 on MMLU and your fine-tuned model scores 40, you have suffered severe forgetting.

2. **Domain-Specific Holdout Sets:** 
Calculate loss and perplexity on a validation set of your specific domain data.
Ensure the model absolutely never saw this data during training.

3. **LLM-as-a-Judge (MT-Bench):** 
Use a frontier model (like GPT-4) to blindly grade outputs from your base model versus your fine-tuned model.
This is highly correlated with human preference.

4. **Human Evaluation (Vibe Check):** 
There is no substitute for manually chatting with the model. 
Humans can instantly detect tonal shifts, repetitive loop failures, and formatting artifacts.

### 12. What are the VRAM hardware requirements for full fine-tuning, LoRA (16-bit), and QLoRA (4-bit) for an 8B and 70B parameter model?
**Answer:**

VRAM calculations must account for the model weights, optimizer states, gradients, and activations.

**For an 8B Model (e.g., Llama-3-8B):**
- *Full Fine-Tuning (16-bit):* Requires ~16GB for weights, plus gradients, and massive Adam optimizer states. Total VRAM required is roughly 80-100GB.
- *LoRA (16-bit base):* Base weights take ~16GB. Optimizer only tracks the tiny adapter parameters. Total VRAM required is ~24GB (can fit on a single RTX 3090/4090).
- *QLoRA (4-bit base):* Base weights take ~5GB. Optimizer tracks the adapter. Total VRAM required is roughly 10-12GB (can fit on a consumer RTX 3060).

**For a 70B Model (e.g., Llama-3-70B):**
- *Full Fine-Tuning (16-bit):* Model is ~140GB. Optimizer states are ~280GB. Total VRAM exceeds 600GB+. Requires an 8x H100 or A100 node.
- *LoRA (16-bit base):* Base model is ~140GB. Total VRAM is ~160GB. Requires at least 2-3x 80GB GPUs.
- *QLoRA (4-bit base):* Base model is ~35GB. Total VRAM required is roughly 48-60GB. Can fit on a single 80GB A100 or spread across two 24GB GPUs.

### 13. How does synthetic data generation using frontier models (e.g. UltraFeedback, Evol-Instruct) accelerate fine-tuning dataset creation?
**Answer:**

Curating thousands of high-quality human demonstrations is prohibitively expensive and slow.
It is also prone to formatting errors. 
Synthetic data generation leverages frontier models to programmatically generate perfectly formatted training data at scale.

**Evol-Instruct:** 
This is a technique where a simple instruction is iteratively made more complex.
You prompt the frontier model to add constraints, deepen the reasoning, or obscure the prompt. 
This creates a rigorous curriculum of increasingly difficult data.
It ensures the fine-tuned model doesn't just memorize trivial, simple tasks.

**UltraFeedback:** 
For preference alignment (like DPO), you need chosen and rejected responses. 
You can use a frontier model as an impartial judge to rank multiple responses to the same prompt.
This automatically creates high-quality datasets of (Prompt, Best Response, Worst Response) pairs.

By using these techniques, practitioners can generate 100,000 highly curated training pairs in a matter of hours.

### 14. What is Odds Ratio Preference Optimization (ORPO), and how does it combine SFT and preference alignment into a single monolithic training step?
**Answer:**

Traditionally, aligning a model involves a two-stage pipeline: 
1. Performing SFT on positive demonstrations.
2. Running DPO on preference data. 

This is computationally expensive, requires curating two distinct datasets, and involves managing multiple models.

ORPO (Odds Ratio Preference Optimization) radically simplifies this pipeline.
It fuses both stages into a single, monolithic training step. 
Furthermore, it operates without a frozen reference model entirely, saving massive amounts of VRAM.

ORPO achieves this by modifying the standard next-token prediction cross-entropy loss. 
It adds a penalty term based on the log odds ratio of the model generating the chosen response versus the rejected response. 

Mathematically, while the model is aggressively learning to predict the chosen tokens:
It is simultaneously penalized if the probability of the rejected sequence does not sufficiently decrease.
This ensures that the model learns the desired behavior and actively unlearns the undesirable behavior simultaneously.

### 15. Explain how to configure quantization parameters in bitsandbytes (BitsAndBytesConfig) for 4-bit QLoRA training in Python.
**Answer:**

To initialize a base model for QLoRA, we use the `BitsAndBytesConfig` class from the `transformers` library.
This interfaces directly with the robust `bitsandbytes` backend. 

```python
from transformers import BitsAndBytesConfig
import torch

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)
```

**Parameters explained:**
- `load_in_4bit=True`: Triggers the quantization engine to compress the linear layers of the model.
- `bnb_4bit_quant_type="nf4"`: Specifies NormalFloat4. This leverages the normal distribution of neural network weights to minimize quantization error.
- `bnb_4bit_compute_dtype=torch.bfloat16`: Weights are *stored* in 4-bit, but must be dynamically dequantized to do matrix multiplication. This specifies that the actual math should be done in 16-bit brain float.
- `bnb_4bit_use_double_quant=True`: Tells the engine to quantize the quantization constants themselves from 32-bit to 8-bit, squeezing out maximum VRAM efficiency.
