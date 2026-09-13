# Module 1: How Large Language Models Actually Work

Most people use LLMs like a black box — they type a prompt, get a response, and move on. That works until something breaks or you need to optimize for cost, latency, or quality. This module tears open the black box and explains the actual mechanics.

---

## 1. The Transformer Architecture

Before LLMs, the dominant approach for language tasks was Recurrent Neural Networks (RNNs). They processed text one word at a time, left to right. The problem: by the time you reached word 200, the network had almost completely "forgotten" word 1. Long-range dependencies (like a subject and its verb separated by 100 words) were extremely hard to learn.

In 2017, Google Brain published the landmark paper **"Attention Is All You Need"** (Vaswani et al.). It introduced the Transformer architecture, which completely replaced RNNs for most NLP tasks.

The core insight: instead of processing tokens sequentially, process them **all at once** and let the model learn which tokens should "pay attention" to which other tokens.

### The Attention Mechanism

For every token in the input, the model computes three vectors:
- **Query (Q)**: "What am I looking for?"
- **Key (K)**: "What do I contain?"
- **Value (V)**: "What information do I carry?"

The attention score between token A and token B is computed as:

```
Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) * V
```

In plain English: token A computes how similar its Query is to every other token's Key. Higher similarity = more attention. The result is a weighted sum of all Values, where the weights are the attention scores.

This means the word "bank" in "I went to the **bank** to deposit money" will learn to pay high attention to "deposit" and "money", and the word "bank" in "I sat on the **bank** of the river" will pay high attention to "river" and "sat". Same word, different context, different meaning — the attention mechanism handles this naturally.

### Multi-Head Attention

A single attention head captures one type of relationship (e.g., subject-verb agreement). But language has many types of relationships simultaneously (syntactic, semantic, positional).

**Multi-Head Attention** runs the attention mechanism `h` times in parallel with different learned weight matrices. Each head captures a different type of relationship. The outputs of all heads are concatenated and projected back to the model dimension. GPT-4 reportedly uses 96 attention heads.

### Positional Encoding

A critical limitation of attention: it has no inherent notion of word order. "The cat sat on the mat" and "the mat sat on the cat" would have the same attention scores if order wasn't encoded somehow.

The solution: **Positional Encoding**. Before feeding tokens into the Transformer, add a position-dependent vector to each token's embedding. This vector encodes the token's position using sine and cosine functions of different frequencies. The model learns to use these to understand word order.

Modern models (like LLaMA) use **Rotary Positional Embeddings (RoPE)** instead, which encode relative positions rather than absolute ones and extrapolate better to longer sequences.

### The Full Transformer Block

Each layer in a Transformer model consists of:
1. **Multi-Head Self-Attention** — tokens attend to each other
2. **Add & Norm** — residual connection + Layer Normalization (stabilizes training)
3. **Feed-Forward Network (FFN)** — two linear layers with a nonlinear activation (usually GeLU) applied to each token independently
4. **Add & Norm** — another residual connection

Modern LLMs (GPT-4, LLaMA, etc.) stack dozens to hundreds of these blocks. GPT-3 has 96 layers. Each layer adds more abstract representations.

---

## 2. Tokenization

You might think LLMs process words. They don't. They process **tokens**.

A token is a chunk of text — it could be a full word, a word fragment, a punctuation mark, or a space. The exact tokenization depends on the algorithm used.

### Why Not Just Use Words?

- Vocabulary size explodes: English has 170,000+ words, and you'd need entries for every inflection, compound word, rare technical term, etc.
- Out-of-vocabulary (OOV) problem: any word not seen during training becomes `<UNK>`.
- No handling of morphology: "run", "running", "runs" are treated as completely separate tokens despite sharing meaning.

### Byte-Pair Encoding (BPE)

Used by GPT models. The algorithm:
1. Start with a vocabulary of individual characters.
2. Count all adjacent character pairs in the training corpus.
3. Merge the most frequent pair into a new token.
4. Repeat until the vocabulary reaches a target size (e.g., 50,257 for GPT-2).

Result: Common words become single tokens. Rare words get split into subword fragments.

```
"unhappiness" → ["un", "happiness"]  
"GPT"         → ["G", "PT"]
"Hello"       → ["Hello"]  (common enough to be one token)
```

### Practical Implications for Engineers

- **Cost**: You pay per token, not per word. `gpt-4o` costs ~$5 per 1M input tokens. A typical English word is ~1.3 tokens. A page of text is ~750 tokens.
- **Context window limits**: GPT-4o has a 128,000 token context window. A full novel (~100,000 words) is ~130,000 tokens — barely fits.
- **Non-English languages**: BPE vocabularies are trained mostly on English text. Many non-English languages require 2-5x more tokens per word, making them proportionally more expensive.
- **Code**: Code is tokenized differently. Python's whitespace is meaningful and gets its own tokens.

### Counting Tokens

```python
import tiktoken

encoding = tiktoken.encoding_for_model("gpt-4o")
text = "Hello, how are you today?"
tokens = encoding.encode(text)
print(f"Token IDs: {tokens}")
print(f"Token count: {len(tokens)}")
# Decode individual tokens to see what they are
for token_id in tokens:
    print(f"  {token_id} → '{encoding.decode([token_id])}'")
```

---

## 3. Embeddings

When a token enters the Transformer, it's first converted to a **dense vector** called an embedding. This is a lookup table: token ID 1234 maps to a 768-dimensional vector (for GPT-2) or 12,288-dimensional vector (for GPT-4).

These vectors aren't arbitrary numbers — they're learned during training and encode semantic meaning geometrically.

### The Geometry of Meaning

The famous example: `king - man + woman ≈ queen`.

If you take the embedding for "king", subtract the embedding for "man", and add the embedding for "woman", you get a vector very close to the embedding for "queen". This means the difference vector "man → woman" encodes the concept of gender, and that encoding is consistent across the embedding space.

Similarly:
- `Paris - France + Germany ≈ Berlin` (capital city relationship)
- `walked - walk + run ≈ ran` (verb tense relationship)

### Cosine Similarity

How do you measure similarity between embeddings? Not Euclidean distance (sensitive to vector magnitude) but **cosine similarity**: the cosine of the angle between two vectors.

```python
import numpy as np

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# Values range from -1 (opposite) to 1 (identical)
```

A score of 0.95 means the two texts are very semantically similar. A score of 0.2 means they're largely unrelated.

### Text Embeddings vs Token Embeddings

- **Token embeddings**: What happens inside a Transformer. Each token has a vector.
- **Text embeddings**: A single vector representing an entire sentence/document. You get this by passing text through an embedding model (like `text-embedding-3-large`) and taking a specific output (usually the mean of all token vectors, or a special `[CLS]` token).

Text embeddings are what you use for semantic search and RAG systems.

---

## 4. Autoregressive Generation

How does an LLM generate text? It doesn't generate the full response at once. It generates **one token at a time**, and each generated token is fed back as input for the next step.

```
Input:  "The capital of France is"
Step 1: Model predicts next token → " Paris" (probability: 0.92)
Step 2: Input becomes "The capital of France is Paris"
        Model predicts next token → "." (probability: 0.78)
Step 3: And so on...
```

This is called **autoregressive generation** (each step depends on all previous steps).

### Sampling Parameters

At each step, the model produces a probability distribution over the entire vocabulary (~50,000 tokens). How do you pick which token to use?

**Temperature** (most important parameter):
- Controls the "randomness" or "creativity" of the output.
- Temperature = 1.0: Use the probabilities as-is.
- Temperature → 0: Always pick the highest probability token (greedy/deterministic). Perfect for code, math, factual Q&A.
- Temperature = 1.5+: Flatten the distribution, boosting lower-probability tokens. More creative, more likely to hallucinate.

```python
import numpy as np

logits = [3.2, 1.1, 0.5, 2.8]  # Raw model output for 4 tokens

def softmax_with_temperature(logits, temperature):
    logits = np.array(logits) / temperature
    e_logits = np.exp(logits - np.max(logits))
    return e_logits / e_logits.sum()

print("T=0.1:", softmax_with_temperature(logits, 0.1))  # Very peaked
print("T=1.0:", softmax_with_temperature(logits, 1.0))  # Normal
print("T=2.0:", softmax_with_temperature(logits, 2.0))  # Flatter
```

**Top-p (nucleus sampling)**:
- Consider only the smallest set of tokens whose cumulative probability exceeds `p`.
- `top_p=0.9`: Only sample from tokens that together account for 90% of the probability mass. Ignores the long tail of unlikely tokens.

**Top-k**:
- Only consider the top `k` most likely tokens at each step.
- `top_k=50`: Only sample from the 50 most likely next tokens.

In practice, most production systems use `temperature=0` for factual tasks (code generation, data extraction) and `temperature=0.7-1.0` for creative tasks.

---

## 5. The Context Window

The context window is the maximum number of tokens the model can "see" at once — both the input (your prompt) and the output (the response) combined.

| Model | Context Window |
|-------|---------------|
| GPT-3.5 | 16,385 tokens |
| GPT-4o | 128,000 tokens |
| Claude 3.5 Sonnet | 200,000 tokens |
| Gemini 1.5 Pro | 1,000,000 tokens |
| LLaMA 3.1 405B | 128,000 tokens |

### Why Context Window Size Matters

1. **Long documents**: Can you fit an entire contract, codebase, or research paper in one prompt?
2. **Conversation history**: For chatbots, you need to include previous turns. A 16K context = ~20 pages of conversation.
3. **Cost**: Larger context windows = more tokens processed = higher API costs.
4. **"Lost in the middle" problem**: Research shows LLMs perform significantly worse at recalling information from the middle of a long context compared to the beginning and end. Relevance + recency bias is real.

---

## 6. Model Families & How to Choose

### OpenAI (GPT Series)
- **GPT-4o**: The current flagship. Best for complex reasoning, coding, and multimodal tasks. Most expensive.
- **GPT-4o-mini**: 80% of the quality at 10% of the cost. Use this by default for most tasks.
- **o1/o3**: Chain-of-thought "reasoning" models. Spend extra time "thinking" before responding. Dramatically better at math, science, and logical reasoning. Very slow and expensive.

### Anthropic (Claude Series)
- **Claude 3.5 Sonnet**: Arguably the best at coding and instruction following. Strong competitor to GPT-4o.
- **Claude 3 Haiku**: The fast, cheap option from Anthropic.

### Google (Gemini Series)
- **Gemini 1.5 Pro**: 1M token context window. Best for processing extremely long documents.
- **Gemini 2.0 Flash**: Fast and cheap with multimodal capabilities.

### Open-Source (Self-Hosted)
- **LLaMA 3.1 405B**: Near GPT-4 quality, fully open source. Can self-host for data privacy.
- **Mistral 7B / 8x7B**: Excellent quality-to-size ratio. Runs on consumer hardware.
- **Ollama**: The easiest way to run open-source models locally.

### Decision Framework

```
Need maximum quality?         → GPT-4o or Claude 3.5 Sonnet
High-volume, cost-sensitive?  → GPT-4o-mini or Claude Haiku
Math/Science/Reasoning?       → o1 or o3
Very long documents?          → Gemini 1.5 Pro
Data privacy (no cloud)?      → LLaMA 3.1 via Ollama
```

---

## 7. Inference Providers & APIs

### OpenAI API
```python
from openai import OpenAI

client = OpenAI()  # Uses OPENAI_API_KEY env var

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain the attention mechanism in 3 sentences."}
    ],
    temperature=0.7,
    max_tokens=500
)

print(response.choices[0].message.content)
print(f"Tokens used: {response.usage.total_tokens}")
```

### Anthropic API
```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=500,
    system="You are a helpful assistant.",
    messages=[{"role": "user", "content": "Explain the attention mechanism."}]
)
print(response.content[0].text)
```

### Ollama (Local / Free)
```python
from openai import OpenAI

# Ollama exposes an OpenAI-compatible API!
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

response = client.chat.completions.create(
    model="llama3.2",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

---

## Next Steps

Head to `labs/` to run the hands-on lab where you'll:
1. Connect to multiple model providers
2. Measure the effect of temperature on output diversity
3. Count tokens and estimate API costs
4. Compare response quality vs cost across model tiers
