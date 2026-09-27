# Advanced RAG - Cheatsheet

## Advanced Chunking Strategies Decision Matrix

| Strategy | Best For | Pros | Cons |
| :--- | :--- | :--- | :--- |
| **Fixed-Size (Naive)** | Prototypes, basic articles | Fast, easy to implement | Destroys semantic context, cuts sentences |
| **Semantic Chunking** | Narrative text, reports | Keeps topics/ideas unified | Computationally expensive (embeds every sentence) |
| **Parent-Child (Hierarchical)** | Complex docs, mixed topics | High precision search + deep context | Complex to orchestrate, higher DB storage |
| **AST / Code Chunking** | Software repositories, code | Preserves functions, classes | Requires language-specific parsers |
| **Late Chunking (Jina)** | Long-form contiguous text | Retains global context in embeddings | Requires specialized models, high compute at index |

---

## Hybrid Search & RRF Formula Reference

### When to use which search?
- **Dense Vector Search (Cosine Similarity):** Queries with synonyms, abstract concepts, "how to" questions.
- **Sparse Lexical Search (BM25):** Exact IDs, specific model numbers, acronyms, out-of-vocabulary terms.

### Reciprocal Rank Fusion (RRF) Formula
Combines the rankings of multiple search algorithms without worrying about disparate score scales.

```text
RRF_Score(document) = Σ [ 1 / ( k + Rank_in_list_i ) ]

Where:
- k = Smoothing constant (typically set to 60)
- Rank = The 1-based index of the document in the specific result list
```

---

## Two-Stage Retrieval (Dense + Sparse + Reranker) Python Template

```python
from qdrant_client import QdrantClient
from sentence_transformers import CrossEncoder

# 1. Initialize Clients
qdrant = QdrantClient("localhost", port=6333)
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def robust_search(query: str, top_k: int = 5):
    # Stage 1a: Fast Dense Search (Top 50)
    dense_results = qdrant.search(
        collection_name="docs",
        query_vector=dense_embed(query),
        limit=50
    )
    
    # Stage 1b: Fast Sparse Search (Top 50)
    sparse_results = qdrant.search(
        collection_name="docs",
        query_vector=sparse_embed(query),
        limit=50
    )
    
    # Stage 1c: Combine with RRF
    merged_candidates = rrf_merge(dense_results, sparse_results, k=60)
    top_candidates = [doc.payload['text'] for doc in merged_candidates[:50]]
    
    # Stage 2: Cross-Encoder Reranking
    pairs = [[query, doc] for doc in top_candidates]
    scores = reranker.predict(pairs)
    
    # Sort by Cross-Encoder scores
    scored_docs = sorted(zip(scores, top_candidates), key=lambda x: x[0], reverse=True)
    return [doc for score, doc in scored_docs[:top_k]]
```

---

## Self-RAG & CRAG Architecture Flowchart

```text
========================================================================
                      CORRECTIVE RAG (CRAG) FLOW
========================================================================

 [ User Query ] 
       │
       ▼
 [ Vector Database Search ]  --> Retrieves top K documents
       │
       ▼
 [ Retrieval Evaluator LLM ] --> Grades relevance of docs
       │
       ├────► (Score: CORRECT) ───► [ Generator LLM ] ──► Final Answer
       │
       ├────► (Score: INCORRECT) ─► [ Web Search API ] ──► [ Generator LLM ] ──► Final Answer
       │                            (Discard internal docs)
       │
       └────► (Score: AMBIGUOUS) ─► [ Query Reformulation ] 
                                           │
                                           ▼
                                 [ Web Search + Vector DB ] ──► [ Generator LLM ] ──► Final Answer

========================================================================
                      SELF-RAG REFLECTION TOKENS
========================================================================

Input: "What is the capital of France?"
Model Output stream:
1. [Retrieve]           <-- Model pauses, triggers external DB search
2. (System injects DB results into context)
3. [Relevant]           <-- Model confirms the retrieved doc is helpful
4. "The capital of France is Paris."
5. [Fully Supported]    <-- Model confirms the generated sentence matches the doc
```
