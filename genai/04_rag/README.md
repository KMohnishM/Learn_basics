# Module 4: Retrieval-Augmented Generation (RAG) — Deep Internals

LLMs have two fundamental limitations:
1. **Knowledge cutoff**: GPT-4 has training data up to April 2023. It knows nothing about your company's Q3 2024 earnings, a paper published last week, or your internal Confluence docs.
2. **Hallucination**: When an LLM doesn't know something, it often confidently makes up a plausible-sounding answer.

**RAG solves both** by giving the LLM access to a real-time, authoritative knowledge base at query time. Instead of relying on parameters baked in during training, the model retrieves relevant documents and uses them as context.

---

## 1. Why RAG Instead of Fine-Tuning?

| | Fine-Tuning | RAG |
|---|---|---|
| **Knowledge update** | Requires retraining ($$$) | Update the vector store (minutes) |
| **Transparency** | "Black box" — hard to audit | Can show which documents were used |
| **Hallucination risk** | Still present | Reduced (grounded in retrieved docs) |
| **Cost** | High (training compute) | Low (inference + vector search) |
| **Best for** | Teaching new *skills*, style, format | Teaching new *knowledge*, facts, proprietary data |

Use fine-tuning to change how the model talks. Use RAG to change what the model knows.

---

## 2. Embeddings — The Mathematics of Meaning

Embeddings are the foundation of RAG. To find documents relevant to a query, you need a way to measure "semantic similarity" — not keyword overlap, but meaning.

### How Embedding Models Work

An embedding model (like `text-embedding-3-small`) is a neural network that takes a piece of text and outputs a dense vector of fixed dimensions.

`"The cat sat on the mat"` → `[0.023, -0.187, 0.441, ..., 0.012]` (1536 numbers)

These numbers aren't random — they encode the semantic content of the text. The vectors are positioned in space so that semantically similar texts have vectors that point in similar directions.

### Why Cosine Similarity, Not Euclidean Distance

Two vectors can be far apart in Euclidean distance but still point in the same direction (just at different magnitudes). Magnitude in embedding space often reflects text length, not content. Cosine similarity ignores magnitude and measures only the angle between vectors.

```python
import numpy as np

def cosine_similarity(a: list[float], b: list[float]) -> float:
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

# Example:
# "I love Python programming" and "Python is my favorite language"
# should have similarity ~0.93
```

### Embedding Models Compared

| Model | Dimensions | Cost | Quality |
|-------|-----------|------|---------|
| `text-embedding-3-small` (OpenAI) | 1536 | $0.02/1M tokens | Great |
| `text-embedding-3-large` (OpenAI) | 3072 | $0.13/1M tokens | Best |
| `all-MiniLM-L6-v2` (Sentence Transformers) | 384 | Free (local) | Good |
| `BAAI/bge-large-en-v1.5` (HuggingFace) | 1024 | Free (local) | Very Good |

For production: `text-embedding-3-small` is the default sweet spot. For cost-sensitive workloads: run a local model.

---

## 3. Vector Databases

A vector database stores embeddings and lets you search them by similarity. Traditional databases (Postgres, MySQL) can't do this efficiently — `SELECT * WHERE embedding ≈ query_embedding` doesn't work with B-Trees.

Vector databases use approximate nearest neighbor (ANN) algorithms (HNSW, IVF) that can find the top-K most similar vectors out of millions in milliseconds.

### pgvector — Postgres with Vector Search

The simplest option if you already use Postgres. No new infrastructure.

```sql
-- Enable the extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Table with an embedding column
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT,
    embedding vector(1536)  -- dimension matches your model
);

-- HNSW index for fast ANN search
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops);

-- Find 5 most similar documents to a query embedding
SELECT id, content, 1 - (embedding <=> '[...]') AS similarity
FROM documents
ORDER BY embedding <=> '[...]'  -- <=> is cosine distance
LIMIT 5;
```

### Qdrant, Pinecone, Weaviate — Dedicated Vector DBs

When to use dedicated vector databases over pgvector:
- **Scale**: pgvector starts struggling above ~5M vectors. Dedicated DBs handle hundreds of millions.
- **Metadata filtering**: "Find similar documents where `year > 2023 AND category = 'finance'`". Dedicated DBs optimize this with pre-filtering.
- **Hybrid search**: Built-in support for combining vector search with keyword search.
- **Managed service**: No infrastructure to manage.

---

## 4. Chunking Strategies

You can't embed an entire 200-page PDF as one vector. The embedding model has a token limit, and even if it didn't, a single vector can't represent 200 pages of content meaningfully.

You must split documents into chunks. Chunking strategy dramatically affects retrieval quality.

### Fixed-Size Chunking
Split every 500 tokens regardless of content boundaries.
```python
def fixed_chunk(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    tokens = text.split()  # Simplified; use tiktoken in practice
    chunks = []
    for i in range(0, len(tokens), chunk_size - overlap):
        chunks.append(" ".join(tokens[i:i + chunk_size]))
    return chunks
```
Simple and predictable. Bad at preserving semantic units (splits mid-sentence, mid-paragraph).

### Recursive Character Text Splitter (Most Common)
Split on paragraph breaks (`\n\n`), then sentences (`\n`), then words. Keeps semantic units together as much as possible.

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
)
chunks = splitter.split_text(document_text)
```

### Semantic Chunking
Embed every sentence, then group consecutive sentences whose embeddings are similar. Split when similarity drops sharply (topic change). More expensive but highest quality.

### Sentence-Window Chunking
Embed small units (1-2 sentences). At retrieval time, fetch the surrounding window (5-10 sentences around the matching sentences). Combines precise retrieval with sufficient context.

---

## 5. The Complete RAG Pipeline

```
Document Ingestion (offline):
  Raw Document
    → Text Extraction (PyMuPDF for PDF, Docx, etc.)
    → Chunking (RecursiveCharacterTextSplitter)
    → Embedding (OpenAI text-embedding-3-small)
    → Storage (pgvector / Qdrant)

Query (online, per user request):
  User Question
    → Embed Question (same embedding model!)
    → Vector Search (top-K most similar chunks)
    → Optional: Re-rank results (cross-encoder)
    → Build context window (concatenate top chunks)
    → LLM Generation (question + retrieved context)
    → Answer
```

---

## 6. Retrieval Strategies

### Dense Retrieval (Vector Search)
Standard semantic similarity search. Great for paraphrasing and conceptual queries. Struggles with exact keyword matches (names, product codes, serial numbers).

### Sparse Retrieval (BM25 / Keyword Search)
Traditional keyword search. Great for exact matches. Struggles with paraphrasing.

### Hybrid Search (Best of Both)
Run both dense and sparse retrieval, combine their scores (Reciprocal Rank Fusion or weighted sum). This is what production RAG systems should use.

```python
# Reciprocal Rank Fusion (RRF)
def reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> list[str]:
    scores = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
    return sorted(scores, key=scores.get, reverse=True)
```

### Reranking (Cross-Encoders)
After vector search retrieves top-50 candidates, a cross-encoder (slower but more accurate) re-scores them and reorders the top-10 to send to the LLM. Cross-encoders process the query and document together (unlike bi-encoders which embed separately), giving much higher relevance judgements.

```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
scores = reranker.predict([(query, doc) for doc in candidate_docs])
reranked = sorted(zip(candidate_docs, scores), key=lambda x: x[1], reverse=True)
```

---

## 7. Advanced RAG Techniques

### HyDE (Hypothetical Document Embeddings)
Problem: The user's question "How does transformer attention work?" is short. The relevant document is a long paragraph explaining attention. Their embeddings might not be that similar in shape.

Solution: Ask the LLM to generate a hypothetical answer to the question. Embed the hypothetical answer (which looks more like the target document) and use that for retrieval.

```python
def hyde_retrieve(query: str, vector_store, k: int = 5) -> list[str]:
    # Step 1: Generate a hypothetical answer
    hypothetical = llm.invoke(f"Write a detailed answer to: {query}")
    
    # Step 2: Embed the hypothetical answer (not the original query!)
    hyp_embedding = embed(hypothetical)
    
    # Step 3: Search with the hypothetical embedding
    return vector_store.similarity_search_by_vector(hyp_embedding, k=k)
```

### Multi-Query Retrieval
The user's single question might not capture all relevant angles. Generate 3-5 different phrasings of the question, retrieve documents for each, deduplicate, and merge.

### Self-Query Retrieval
Let the LLM generate structured metadata filters alongside the semantic query.

User: "What were our Q4 2023 sales in APAC?"

LLM decomposes this into:
- Semantic query: "quarterly sales revenue performance"
- Metadata filter: `region = "APAC" AND year = 2023 AND quarter = "Q4"`

---

## 8. RAG Evaluation with RAGAS

You can't just "eyeball" RAG quality. You need systematic evaluation.

RAGAS provides automated metrics:
- **Faithfulness**: Are the claims in the answer supported by the retrieved context? (Measures hallucination)
- **Answer Relevancy**: Does the answer actually address the user's question?
- **Context Recall**: Did the retrieval pipeline find the documents that actually contain the answer?
- **Context Precision**: Of the retrieved documents, what fraction were actually relevant?

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall

results = evaluate(
    dataset=your_dataset,  # questions, answers, contexts, ground_truths
    metrics=[faithfulness, answer_relevancy, context_recall]
)
print(results)
# Output: faithfulness: 0.82, answer_relevancy: 0.91, context_recall: 0.76
```

---

## Next Steps

Go to `labs/` to build a complete RAG system over a set of PDF documents with pgvector, hybrid search, and RAGAS evaluation!
