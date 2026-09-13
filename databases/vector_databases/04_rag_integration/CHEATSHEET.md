# RAG Integration Cheatsheet

## Bi-Encoder vs. Cross-Encoder

| Feature | Bi-Encoder | Cross-Encoder |
| :--- | :--- | :--- |
| **Architecture** | Embeds Query and Document independently. | Concatenates Query and Document, processes simultaneously. |
| **Output** | Two dense vectors. | A single relevance score. |
| **Similarity Calculation** | Dot Product or Cosine Distance. | Deep self-attention across all tokens. |
| **Speed / Latency** | Extremely fast (milliseconds). | Slow (computationally expensive). |
| **Indexing** | Pre-computation of document embeddings is possible. | Cannot pre-compute; scoring must happen at query time. |
| **Primary Use Case** | Stage 1 Retrieval (searching millions of docs). | Stage 2 Reranking (scoring top 100 candidate docs). |

## Reciprocal Rank Fusion (RRF)

**Algorithm:** Used to combine ranked lists from different retrieval systems (e.g., Dense + Sparse/BM25).

**Formula:**
$$ \text{RRF\_Score}(d) = \sum_{r \in R} \frac{1}{k + r(d)} $$
*(where $k$ is typically 60)*

**Python Implementation:**
```python
def calculate_rrf(rank_list_1, rank_list_2, k=60):
    rrf_scores = {}
    
    for rank, doc_id in enumerate(rank_list_1, start=1):
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1.0 / (k + rank)
        
    for rank, doc_id in enumerate(rank_list_2, start=1):
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1.0 / (k + rank)
        
    return sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
```

## RAGAS Evaluation Metrics Summary

| Metric | Category | Description | Penalizes |
| :--- | :--- | :--- | :--- |
| **Faithfulness** | Generation | Is the answer strictly derived from the context? | Hallucinations, external knowledge usage. |
| **Answer Relevancy** | Generation | Does the answer directly address the question? | Tangents, incomplete answers. |
| **Context Precision** | Retrieval | Are the most relevant chunks ranked at the top? | Poor ranking, noise in top results. |
| **Context Recall** | Retrieval | Does the context contain all info needed for the answer? | Missing information, failure to retrieve ground truth. |

## RAG Pipeline Architecture (ASCII)

```text
                        [ 1. Ingestion Pipeline ]
  +---------------+       +------------------+       +------------------+
  | Raw Documents | ----> | Text Splitting   | ----> | Embedding Model  |
  +---------------+       | (Chunking)       |       | (Bi-Encoder)     |
                          +------------------+       +------------------+
                                                              |
                                                              v
                                                   +--------------------+
                                                   | Vector Database    | <---+
                                                   | (Storage & Index)  |     |
                                                   +--------------------+     |
                                                                              |
                                                                              |
                        [ 2. Query & Retrieval ]                              |
  +---------------+       +------------------+       +------------------+     |
  | User Query    | ----> | Query Expansion  | ----> | Embedding Model  | ----+
  +---------------+       | (HyDE, Multi)    |       | (Bi-Encoder)     |
                          +------------------+       +------------------+
                                                              
                                                              | (Returns Top 100)
                                                              v
                        [ 3. Reranking ]           +--------------------+
                                                   | Cross-Encoder      |
                                                   | (Cohere, BGE)      |
                                                   +--------------------+
                                                              | (Returns Top 5)
                                                              v
                        [ 4. Generation ]          +--------------------+
                                                   | LLM (GPT-4, etc.)  |
                                                   | Prompt + Context   |
                                                   +--------------------+
                                                              |
                                                              v
                                                      [ Final Answer ]
```
