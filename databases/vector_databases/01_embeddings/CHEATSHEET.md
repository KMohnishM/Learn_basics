# Embeddings Cheatsheet

## Similarity Metric Formulas & Code

### Cosine Similarity
Formula: $cos(\theta) = \frac{A \cdot B}{\|A\| \|B\|}$
Range: [-1, 1] (1 means identical, 0 orthogonal, -1 diametrically opposed)

```python
import numpy as np

def cosine_similarity(a, b):
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)
```

### Dot Product (Inner Product)
Formula: $A \cdot B = \sum_{i=1}^{n} A_i B_i$
Range: $(-\infty, \infty)$

```python
import numpy as np

def dot_product(a, b):
    return np.dot(a, b)
```

### Euclidean Distance (L2)
Formula: $d(A, B) = \sqrt{\sum_{i=1}^{n} (A_i - B_i)^2}$
Range: $[0, \infty)$

```python
import numpy as np

def euclidean_distance(a, b):
    return np.linalg.norm(np.array(a) - np.array(b))
```

### Manhattan Distance (L1)
Formula: $d_{1}(A, B) = \sum_{i=1}^{n} |A_i - B_i|$
Range: $[0, \infty)$

```python
import numpy as np

def manhattan_distance(a, b):
    return np.sum(np.abs(np.array(a) - np.array(b)))
```

## Chunking Strategy Comparison Matrix

| Strategy | Pros | Cons | Ideal Use Case |
|---|---|---|---|
| Fixed-Size (Character) | Fast, simple, predictable size | Breaks words/sentences context | Basic prototyping, uniform texts |
| Fixed-Size (Token) | Aligns with LLM context windows | Can still break sentence context | LLM integration pipelines |
| Sentence-Based | Maintains grammatical context | Variable chunk sizes | NLP tasks, semantic search |
| Recursive Character | Balances structure and size constraints | More complex implementation | Document parsing, varied structures |
| Semantic Chunking | Maximizes context coherence | Computationally expensive | High-accuracy RAG, complex reasoning |

## Popular Embedding Model Reference Table

| Model | Provider | Dimensions | Max Sequence Length | Use Case Notes |
|---|---|---|---|---|
| text-embedding-3-small | OpenAI | 1536 (default) | 8191 | High performance, cost-effective |
| text-embedding-3-large | OpenAI | 3072 (default) | 8191 | Highest accuracy, customizable dims |
| all-MiniLM-L6-v2 | SentenceTransformers| 384 | 256 | Local, fast, lightweight semantic search|
| bge-large-en-v1.5 | BAAI | 1024 | 512 | Open-source SOTA, retrieval tasks |
| embed-english-v3.0 | Cohere | 1024 | 512 | Enterprise search, quality multilingual |
| Nomic Embed Text | Nomic | 768 | 8192 | Long context, fully open-source weights |
