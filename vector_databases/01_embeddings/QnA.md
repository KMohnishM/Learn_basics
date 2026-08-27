# QnA: Vector Databases & Embeddings

## Q1: Explain the curse of dimensionality and why it breaks nearest-neighbour search at high dimensions. Include the mathematical intuition.

The curse of dimensionality refers to various phenomena that arise when analyzing and organizing data in high-dimensional spaces that do not occur in low-dimensional settings. In the context of vector databases and nearest-neighbour search, the most critical issue is distance concentration. As the number of dimensions $d$ increases, the distance between any two randomly chosen points tends to converge to the same value. 

Mathematically, if we assume data points are drawn from an isotropic distribution, the ratio of the variance of distances to the mean of distances approaches zero as $d \to \infty$. We can write this as:
$$ \lim_{d \to \infty} \frac{dist_{max} - dist_{min}}{dist_{min}} = 0 $$
Because of this concentration, the concept of "nearest" neighbour loses its meaning, as all points appear to be almost equidistant from a given query point.

To mitigate this, production vector databases rely on approximate nearest neighbor (ANN) algorithms, quantization, and dimensionality reduction.

```python
import numpy as np

def simulate_distance_concentration(dims=[10, 100, 1000, 10000], num_points=1000):
    for d in dims:
        points = np.random.randn(num_points, d)
        origin = np.zeros(d)
        distances = np.linalg.norm(points - origin, axis=1)
        dist_min, dist_max = np.min(distances), np.max(distances)
        contrast = (dist_max - dist_min) / dist_min
        print(f"Dims: {d:5} | Contrast: {contrast:.4f}")
        
# Output shows contrast approaches 0 as dims increase.
```
This forces vector databases to partition space intelligently rather than relying on exact distance scans.

## Q2: What is Matryoshka Representation Learning (MRL)? How does the joint training objective work and what production benefits does it unlock?

Matryoshka Representation Learning (MRL) is a paradigm that trains embedding models to store coarse-to-fine semantic information across nested sub-dimensions of the representation vector. Like a Matryoshka doll, smaller valid embeddings are contained within the larger embedding. 

The joint training objective optimizes the loss over multiple truncation sizes $m_i$ simultaneously. For an embedding of maximum size $D$, we define a set of nested sizes, e.g., $M = \{64, 128, 256, 512, 768\}$. The loss is computed as a weighted sum of the standard contrastive loss at each dimension slice:
$$ \mathcal{L}_{MRL} = \sum_{m \in M} c_m \cdot \mathcal{L}_{contrastive}(z_{1:m}^{(q)}, z_{1:m}^{(p)}) $$

This unlocks massive production benefits. In a RAG pipeline, you can fetch the first 64 dimensions for an ultra-fast initial candidate retrieval step, and then use the full 768-dimensional vectors to re-rank the top candidates. This reduces RAM footprint, network I/O, and compute costs without sacrificing the accuracy of the final retrieval stage.

```python
import torch

def matryoshka_loss(query_emb, pos_emb, neg_emb, dims=[64, 128, 256, 768]):
    total_loss = 0
    for dim in dims:
        # Truncate embeddings to current dimension
        q_trunc = query_emb[:, :dim]
        p_trunc = pos_emb[:, :dim]
        n_trunc = neg_emb[:, :dim]
        # Calculate standard InfoNCE loss on truncated vectors
        # (Assuming a helper function infonce_loss exists)
        loss = infonce_loss(q_trunc, p_trunc, n_trunc)
        total_loss += loss
    return total_loss
```
MRL is crucial for scalable, multi-stage retrieval pipelines.

## Q3: Write the full BM25 formula with all terms defined. What do k1 and b control? What are their default values and how do you tune them?

The Okapi BM25 ranking function calculates a relevance score between a document $D$ and a query $Q$ (containing terms $q_i$):

$$ \text{score}(D,Q) = \sum_{i=1}^{n} \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot (1 - b + b \cdot \frac{|D|}{\text{avgdl}})} $$

- $f(q_i, D)$: Term frequency of query term $q_i$ in document $D$.
- $|D|$: Length of document $D$ in words.
- $\text{avgdl}$: Average document length in the corpus.
- $\text{IDF}(q_i)$: Inverse document frequency of term $q_i$, typically $\ln(\frac{N - n(q_i) + 0.5}{n(q_i) + 0.5} + 1)$.

The parameter $k_1$ (typically $1.2$ to $2.0$) controls term frequency saturation. A higher $k_1$ means the score continues to increase with more term occurrences, whereas a lower $k_1$ caps the benefit of repeated terms quickly.
The parameter $b$ (typically $0.75$) controls document length normalization. $b=1$ means fully normalizing by length, penalizing long documents heavily; $b=0$ ignores document length entirely.

```python
import math

def bm25_term_score(tf, doc_len, avgdl, idf, k1=1.5, b=0.75):
    # Length normalization
    length_norm = 1 - b + b * (doc_len / avgdl)
    # Term frequency saturation
    tf_factor = (tf * (k1 + 1)) / (tf + k1 * length_norm)
    return idf * tf_factor

# Example calculation
print(bm25_term_score(tf=3, doc_len=120, avgdl=100, idf=2.5))
```
Tuning requires evaluating against a labeled dataset using grid search to optimize nDCG or MRR.

## Q4: What is the difference between cosine similarity and dot product similarity? Prove algebraically that they are equal when vectors are L2-normalized.

Cosine similarity measures the cosine of the angle between two vectors, focusing strictly on direction, whereas dot product measures both direction and magnitude.

The formula for cosine similarity between vectors $A$ and $B$ is:
$$ \text{CosSim}(A, B) = \frac{A \cdot B}{||A||_2 ||B||_2} $$
The dot product is simply:
$$ \text{Dot}(A, B) = A \cdot B = \sum_i A_i B_i $$

Proof of equivalence for normalized vectors:
If a vector $A$ is L2-normalized, its Euclidean norm $||A||_2$ is strictly equal to 1. 
Therefore, if both $A$ and $B$ are L2-normalized:
$$ ||A||_2 = 1 \text{ and } ||B||_2 = 1 $$
Substitute these into the cosine similarity formula:
$$ \text{CosSim}(A, B) = \frac{A \cdot B}{1 \times 1} = A \cdot B = \text{Dot}(A, B) $$

```python
import numpy as np

A = np.array([1.5, 2.0, -1.0])
B = np.array([0.5, 1.0, 1.5])

# L2 normalization
A_norm = A / np.linalg.norm(A)
B_norm = B / np.linalg.norm(B)

dot_prod = np.dot(A_norm, B_norm)
cos_sim = np.dot(A, B) / (np.linalg.norm(A) * np.linalg.norm(B))

# These will be essentially identical up to float precision
assert np.isclose(dot_prod, cos_sim)
```
Production databases prefer dot product on pre-normalized vectors as it skips division, saving massive CPU cycles during billion-scale vector scans.

## Q5: How does Sentence-BERT (SBERT) differ from vanilla BERT for semantic similarity? What architectural changes and training objective make it deployment-ready?

Vanilla BERT computes semantic similarity using a cross-encoder architecture. You concatenate two sentences, `[CLS] Sentence A [SEP] Sentence B [SEP]`, and pass them through the transformer. This is computationally explosive; finding the most similar pair in a corpus of 10,000 sentences requires $(10000 \times 9999)/2 \approx 50$ million inference passes.

SBERT modifies this by using a Siamese network architecture (bi-encoder). It passes each sentence independently through the BERT model to produce fixed-size sentence embeddings. These embeddings are derived via a pooling layer (usually Mean Pooling over the output tokens).

```python
import torch.nn as nn

class SBERT(nn.Module):
    def __init__(self, bert_model):
        super().__init__()
        self.bert = bert_model
        
    def forward(self, input_ids, attention_mask):
        # Independent forward pass
        outputs = self.bert(input_ids, attention_mask=attention_mask)
        token_embeddings = outputs.last_hidden_state
        
        # Mean Pooling step
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        return sum_embeddings / sum_mask
```
Because embeddings are generated independently, they can be cached in a vector database and compared using cosine similarity. SBERT is trained using objectives like Triplet Loss or Cosine Similarity Loss on datasets like NLI and STSb, making it fully deployment-ready for RAG.

## Q6: Write the Reciprocal Rank Fusion (RRF) formula. Explain the k=60 constant. Show a concrete worked example merging BM25 and ANN rankings.

Reciprocal Rank Fusion (RRF) is an ensemble method for combining results from multiple search retrieval strategies (e.g., lexical BM25 and semantic ANN) without requiring score normalization.

The formula assigns a combined score to a document $d \in D$:
$$ \text{RRF\_Score}(d) = \sum_{r \in R} \frac{1}{k + \text{rank}_r(d)} $$
where $R$ is the set of rankers, $\text{rank}_r(d)$ is the 1-based rank of the document in ranker $r$, and $k$ is a constant.

The constant $k=60$ was empirically discovered to mitigate the impact of outlier ranks and high variance. It flattens out the steep drop-off of the reciprocal curve, giving low-ranked documents a small, non-zero weight while ensuring the top handful of documents don't wildly over-dominate.

```python
def reciprocal_rank_fusion(bm25_ranks, ann_ranks, k=60):
    rrf_scores = {}
    for doc_id, rank in bm25_ranks.items():
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k + rank)
        
    for doc_id, rank in ann_ranks.items():
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k + rank)
        
    return sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

bm25 = {"docA": 1, "docB": 2, "docC": 100}
ann = {"docB": 1, "docC": 2, "docA": 50}

# Example breakdown:
# docB: 1/(60+2) + 1/(60+1) = 0.0161 + 0.0164 = 0.0325
# docA: 1/(60+1) + 1/(60+50) = 0.0164 + 0.0091 = 0.0255
print(reciprocal_rank_fusion(bm25, ann)) 
```
In the worked example, `docB` wins because it ranks extremely well in both systems, whereas `docA` is heavily penalized by its poor ANN rank.

## Q7: What is the relationship between L2 (Euclidean) distance and cosine similarity? Prove they produce identical rankings when vectors are unit-normalized.

L2 Distance measures the straight-line distance between two points, whereas Cosine Similarity measures the angular difference. 

The squared L2 distance between vectors $A$ and $B$ is:
$$ ||A - B||^2 = (A - B) \cdot (A - B) = ||A||^2 + ||B||^2 - 2(A \cdot B) $$

If the vectors are unit-normalized ($||A||=1, ||B||=1$), the equation simplifies to:
$$ ||A - B||^2 = 1 + 1 - 2(A \cdot B) = 2 - 2(A \cdot B) $$
Since the vectors are normalized, the dot product is exactly the cosine similarity:
$$ ||A - B||^2 = 2 - 2 \cdot \text{CosSim}(A, B) $$

This monotonic inverse relationship means minimizing L2 distance is mathematically identical to maximizing cosine similarity. Therefore, the relative ranking of documents for a query will be exactly the same.

```python
import numpy as np

def compute_distances(query, docs):
    # Assume vectors are already L2 normalized
    cosine_sims = np.dot(docs, query)
    l2_sq_dists = 2.0 - 2.0 * cosine_sims
    
    # Argsort for cosine (descending) and L2 (ascending)
    rank_cos = np.argsort(-cosine_sims)
    rank_l2 = np.argsort(l2_sq_dists)
    
    return np.array_equal(rank_cos, rank_l2)

q = np.array([1, 0])/np.sqrt(1)
D = np.array([[1, 0], [0.707, 0.707], [0, 1]])
print(f"Ranks are identical: {compute_distances(q, D)}")
```
This is why Faiss and HNSW indices often just rely on inner-product index types, pushing the burden of normalization onto the data ingestion pipeline.

## Q8: Why is mean pooling of BERT token embeddings superior to using the [CLS] token for semantic similarity? Cite the SBERT paper finding.

In the original BERT paper, the `[CLS]` token is used as the aggregate representation for downstream classification tasks like Next Sentence Prediction (NSP). However, the SBERT paper ("Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks" by Reimers and Gurevych) conclusively proved that out-of-the-box `[CLS]` embeddings produce terrible sentence representations, often performing worse than simple GloVe embeddings.

The `[CLS]` token acts as a highly specialized attention sink optimized specifically for the NSP objective during pre-training. It fails to capture uniform semantic meaning across the sentence when evaluated via cosine similarity. Mean pooling, on the other hand, averages the contextualized vectors of all actual word tokens in the sequence, producing a much more stable and generalized semantic representation.

```python
import torch

def compare_pooling(transformer_output, attention_mask):
    # [CLS] pooling
    cls_embedding = transformer_output[:, 0, :]
    
    # Mean pooling
    mask_expanded = attention_mask.unsqueeze(-1).expand(transformer_output.size()).float()
    sum_embeddings = torch.sum(transformer_output * mask_expanded, 1)
    sum_mask = torch.clamp(mask_expanded.sum(1), min=1e-9)
    mean_embedding = sum_embeddings / sum_mask
    
    return cls_embedding, mean_embedding
```
By fine-tuning the mean-pooled representations over Siamese networks, SBERT achieved state-of-the-art results on semantic textual similarity benchmarks.

## Q9: Explain the parent-child chunking strategy. What two data structures does it require? How does it avoid context fragmentation?

Parent-child chunking (also known as small-to-big retrieval or auto-merging) is a strategy designed to balance precision in retrieval with completeness in generation. 

It requires two connected data structures:
1. **Vector Database**: Stores the embeddings of "child" chunks (small, granular pieces of text like a single sentence or small paragraph) along with pointers to their parent ID.
2. **Document/KV Store**: Stores the raw text of "parent" chunks (larger structures like a full section, page, or document) keyed by the parent ID.

When querying, the vector database finds the highly relevant child chunks. However, instead of passing these fragmented child chunks to the LLM, the RAG system uses the parent IDs to fetch the full parent context from the document store. 

```python
def retrieve_parent_chunks(query_vector, vector_db, doc_store, k=5):
    # Retrieve top K child chunks
    child_hits = vector_db.similarity_search(query_vector, k=k)
    
    parent_ids = set()
    for child in child_hits:
        parent_ids.add(child.metadata['parent_id'])
        
    # Fetch full context from Key-Value store
    full_contexts = []
    for pid in parent_ids:
        full_contexts.append(doc_store.get(pid))
        
    return full_contexts
```
This avoids context fragmentation because the LLM receives the full semantic context surrounding the localized hit, dramatically reducing hallucinations caused by missing information.

## Q10: Calculate the RAM required to store 50 million vectors at 1536 dimensions in float32, float16, int8 (SQ), and binary quantization. Show all arithmetic.

Calculating the memory footprint of a vector database is critical for capacity planning. A vector consists of dimensions, and each dimension requires a certain number of bytes depending on the data type. Let $N = 50,000,000$ and $D = 1536$.

**1. Float32 (4 bytes per dimension):**
Memory = $50 \times 10^6 \times 1536 \times 4 \text{ bytes}$
Memory = $307,200,000,000 \text{ bytes}$
Memory = $307.2 \text{ GB}$

**2. Float16 (2 bytes per dimension):**
Memory = $50 \times 10^6 \times 1536 \times 2 \text{ bytes}$
Memory = $153,600,000,000 \text{ bytes}$
Memory = $153.6 \text{ GB}$

**3. Int8 Scalar Quantization (1 byte per dimension):**
Memory = $50 \times 10^6 \times 1536 \times 1 \text{ bytes}$
Memory = $76,800,000,000 \text{ bytes}$
Memory = $76.8 \text{ GB}$

**4. Binary Quantization (1 bit per dimension = 0.125 bytes):**
Memory = $50 \times 10^6 \times 1536 \times 0.125 \text{ bytes}$
Memory = $9,600,000,000 \text{ bytes}$
Memory = $9.6 \text{ GB}$

```python
def calculate_ram(num_vectors, dimensions, bytes_per_dim):
    total_bytes = num_vectors * dimensions * bytes_per_dim
    gb = total_bytes / (1000**3) # Using decimal GB for simplicity
    return f"{gb:.1f} GB"

v = 50_000_000
d = 1536
print(calculate_ram(v, d, 4))     # 307.2 GB
print(calculate_ram(v, d, 0.125)) # 9.6 GB
```
These calculations omit the graph index overhead (like HNSW edges), which typically adds another 20-30% to the total RAM footprint.

## Q11: What is the difference between in-batch negatives and hard negatives in contrastive learning? Why do hard negatives produce better embedding quality?

Contrastive learning attempts to pull a query and a positive example closer while pushing negative examples away.

**In-batch negatives** are simply the positive examples from other pairs in the same training batch. Since they are randomly paired with the query, they are usually trivial negatives—completely unrelated topics. The model easily learns to push them away, resulting in vanishing gradients and slow learning once the basic topical boundaries are established.

**Hard negatives** are samples that are semantically similar or lexically overlapping with the query but do not actually answer it. For example, for the query "How to boil an egg", a hard negative might be "How to fry an egg". Hard negatives force the model to look past superficial lexical overlap and understand deep semantic distinctions.

```python
import torch
import torch.nn.functional as F

def contrastive_loss(q, pos, hard_neg, tau=0.05):
    # In-batch negatives are implicitly handled by the denominator in InfoNCE
    sim_pos = F.cosine_similarity(q, pos) / tau
    sim_neg = F.cosine_similarity(q, hard_neg) / tau
    
    # We want to maximize pos sim, minimize neg sim
    logits = torch.cat([sim_pos.unsqueeze(1), sim_neg.unsqueeze(1)], dim=1)
    labels = torch.zeros(logits.size(0), dtype=torch.long) # index 0 is positive
    
    return F.cross_entropy(logits, labels)
```
Hard negatives produce better embeddings by carving out tighter, more distinct clusters in the latent space, which is critical for fine-grained retrieval in RAG systems.

## Q12: Explain the Skip-gram objective with negative sampling. Why was softmax over full vocabulary replaced with negative sampling, and what k value is typically used?

The Skip-gram model from Word2Vec aims to predict context words given a target word. The original objective maximized the probability of context words using a softmax function over the entire vocabulary $V$:
$$ P(w_{context} | w_{target}) = \frac{\exp(v_{context} \cdot v_{target})}{\sum_{i \in V} \exp(v_i \cdot v_{target})} $$

Calculating the denominator requires summing over millions of words in $V$ for every training step, making it computationally prohibitive.

Negative sampling resolves this by casting it as a binary classification problem: classifying a word pair as "real" (from the text) or "fake" (noise). Instead of the full vocabulary, we only sample $k$ negative words. The objective becomes maximizing the dot product for the true context word, and minimizing it for $k$ randomly sampled negative words:
$$ \mathcal{L} = \log \sigma(v_{target} \cdot v_{context}) + \sum_{i=1}^{k} \log \sigma(-v_{target} \cdot v_{negative\_i}) $$

```python
import numpy as np
def sigmoid(x): return 1 / (1 + np.exp(-x))

def skip_gram_loss(target_vec, context_vec, negative_vecs):
    # Positive pair loss
    pos_score = np.log(sigmoid(np.dot(target_vec, context_vec)))
    
    # Negative pairs loss
    neg_score = 0
    for neg_vec in negative_vecs:
        neg_score += np.log(sigmoid(-np.dot(target_vec, neg_vec)))
        
    return -(pos_score + neg_score)
```
Typically, $k$ is set to 5–20 for small datasets, and 2–5 for large datasets. This approximation drastically reduces training time while maintaining high embedding quality.

## Q13: Compare fixed-size chunking, recursive character splitting, and semantic chunking. When is each optimal for a RAG system?

Chunking is a vital preprocessing step in RAG to fit documents into context windows and create granular vector representations.

**Fixed-size chunking** splits text purely by token or character count (e.g., 512 tokens), with some overlap (e.g., 50 tokens). It is computationally trivial but frequently splits sentences or thoughts in half, leading to degraded retrieval.
*Optimal for:* Highly uniform data like log files or when preprocessing speed is paramount.

**Recursive character splitting** attempts to split using natural boundaries (like `\n\n`, then `\n`, then `.`) before falling back to fixed lengths. It tries to keep paragraphs and sentences intact.
*Optimal for:* Most general-purpose RAG systems, articles, and codebases.

**Semantic chunking** uses embedding models to calculate the cosine similarity between adjacent sentences. If the similarity drops below a threshold, a chunk boundary is placed, ensuring that chunks represent cohesive semantic topics regardless of length.
*Optimal for:* Complex, unstructured data where topic boundaries shift irregularly (e.g., meeting transcripts).

```python
# Pseudo-code for Semantic Chunking
def semantic_chunk(sentences, threshold=0.7):
    chunks = [[sentences[0]]]
    for i in range(1, len(sentences)):
        sim = cosine_sim(embed(sentences[i-1]), embed(sentences[i]))
        if sim > threshold:
            chunks[-1].append(sentences[i])
        else:
            chunks.append([sentences[i]])
    return [" ".join(c) for c in chunks]
```
Choosing the right chunker balances computational cost during indexing against the context cohesion required by the LLM during generation.

## Q14: What does nDCG@10 measure in the context of MTEB? Write the formula and explain why it's the primary metric for RAG embedding evaluation.

nDCG@10 (Normalized Discounted Cumulative Gain at rank 10) is a metric used extensively in the Massive Text Embedding Benchmark (MTEB) to evaluate retrieval systems. It measures both the presence of relevant documents in the top 10 results and their exact ranking position.

First, we calculate the Discounted Cumulative Gain (DCG), which rewards highly relevant documents but penalizes them logarithmically if they appear lower in the ranking:
$$ \text{DCG@10} = \sum_{i=1}^{10} \frac{2^{rel_i} - 1}{\log_2(i + 1)} $$
Where $rel_i$ is the relevance score of the document at rank $i$.
nDCG normalizes this by dividing the DCG by the Ideal DCG (IDCG), which is the DCG if the documents were perfectly sorted by relevance. Thus, nDCG is always between 0 and 1.

```python
import numpy as np

def dcg_at_k(relevances, k):
    relevances = np.asarray(relevances)[:k]
    discounts = np.log2(np.arange(2, relevances.size + 2))
    return np.sum((2**relevances - 1) / discounts)

def ndcg_at_k(relevances, k):
    ideal_relevances = np.sort(relevances)[::-1]
    idcg = dcg_at_k(ideal_relevances, k)
    if idcg == 0: return 0.0
    return dcg_at_k(relevances, k) / idcg

# Example: Highly relevant doc at rank 1 gives better score
print(ndcg_at_k([3, 0, 0, 1], 10))
```
It is the primary metric for RAG because LLMs are highly sensitive to the order of context chunks (the "Lost in the Middle" phenomenon). Returning the best chunk at rank 1 is exponentially more useful than returning it at rank 10.

## Q15: What is domain-specific embedding fine-tuning? Describe the triplet format (query, positive, hard negative), the InfoNCE/NTXent contrastive loss, and when fine-tuning is necessary.

Domain-specific fine-tuning adapts pre-trained embedding models (like BGE or E5) to highly specialized vocabularies (e.g., legal contracts or medical records) where general-purpose semantic representations fail.

The training dataset is structured in a **triplet format**: $(Q, P, N)$. 
- $Q$ is the Query.
- $P$ is the Positive (a relevant document).
- $N$ is a Hard Negative (a document that shares keywords or structure with $Q$ but is not the correct answer).

The InfoNCE (or NT-Xent) contrastive loss optimizes the embeddings by maximizing the similarity of the $(Q, P)$ pair while simultaneously minimizing the similarity of the $(Q, N)$ pair, scaled by a temperature $\tau$:
$$ \mathcal{L} = -\log \frac{\exp(\text{sim}(Q, P)/\tau)}{\sum_{N_i \in \{P\} \cup N_{batch}} \exp(\text{sim}(Q, N_i)/\tau)} $$

```python
import torch
import torch.nn.functional as F

def info_nce_loss(q_embed, p_embed, n_embed, tau=0.05):
    # Sim(Q,P)
    pos_sim = F.cosine_similarity(q_embed, p_embed) / tau
    # Sim(Q,N)
    neg_sim = F.cosine_similarity(q_embed, n_embed) / tau
    
    # We want model to predict label 0 (the positive pair)
    logits = torch.cat([pos_sim.unsqueeze(1), neg_sim.unsqueeze(1)], dim=1)
    labels = torch.zeros(logits.size(0), dtype=torch.long)
    
    return F.cross_entropy(logits, labels)
```
Fine-tuning is necessary when out-of-the-box models fail on domain-specific jargon, acronyms, or when BM25 consistently beats the semantic search on internal benchmarks, signaling the embedding model lacks fundamental domain context.
