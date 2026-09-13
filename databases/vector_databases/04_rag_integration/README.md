# Module 4: Retrieval-Augmented Generation (RAG) Integration

## 1. RAG Architecture — The Complete Picture

Retrieval-Augmented Generation (RAG) is a paradigm that bridges the gap between static Large Language Models (LLMs) and dynamic, proprietary data. Standard LLMs are trained on point-in-time snapshots of public data and lack context regarding private, recent, or highly specific information. RAG solves this by introducing a retrieval step before generation, fetching relevant context from a knowledge base (typically a vector database) and injecting it into the prompt.

The architecture consists of two primary pipelines operating asynchronously or in sequence:
1. The Indexing Pipeline (offline or continuous)
2. The Retrieval and Generation Pipeline (online/real-time)

Here is a complete ASCII architecture diagram illustrating the data flow:

```text
+-----------------------------------------------------------------------------------------+
|                                  INDEXING PIPELINE (OFFLINE)                            |
+-----------------------------------------------------------------------------------------+
|                                                                                         |
|  [Raw Documents] (PDFs, HTML, Markdown, Text)                                           |
|        |                                                                                |
|        v                                                                                |
|  [Document Loaders] -> Extract text and metadata (Author, Date, Source URL)             |
|        |                                                                                |
|        v                                                                                |
|  [Text Splitters / Chunkers] -> Break text into overlapping chunks (e.g., 512 tokens)   |
|        |                                                                                |
|        v                                                                                |
|  [Embedding Model] -> Convert chunks into dense vector representations (e.g., 768-dim)  |
|        |                                                                                |
|        v                                                                                |
|  [Vector Database] -> Upsert vectors along with raw text payload and metadata           |
|                                                                                         |
+-----------------------------------------------------------------------------------------+

+-----------------------------------------------------------------------------------------+
|                              RETRIEVAL PIPELINE (ONLINE)                                |
+-----------------------------------------------------------------------------------------+
|                                                                                         |
|  [User Query] -> "How does cross-encoder reranking improve accuracy?"                   |
|        |                                                                                |
|        v                                                                                |
|  [Query Transformation] -> (Optional) HyDE, Query Expansion, Multi-Query Generation     |
|        |                                                                                |
|        v                                                                                |
|  [Embedding Model] -> Embed the formulated query into the same vector space             |
|        |                                                                                |
|        v                                                                                |
|  [Vector Database] -> ANN Search (Approximate Nearest Neighbors) using Cosine/Dot Prod  |
|        |                                                                                |
|        v                                                                                |
|  [Retrieved Candidates] -> Top-K documents (e.g., K=20)                                 |
|        |                                                                                |
|        v                                                                                |
|  [Reranker / Cross-Encoder] -> Score candidates accurately against the original query   |
|        |                                                                                |
|        v                                                                                |
|  [Diversity Filter] -> (Optional) Maximum Marginal Relevance (MMR)                      |
|        |                                                                                |
|        v                                                                                |
|  [Final Context] -> Top-N documents (e.g., N=5) injected into the LLM Prompt            |
|        |                                                                                |
|        v                                                                                |
|  [Large Language Model] -> Generates the final synthesized answer citing sources        |
|                                                                                         |
+-----------------------------------------------------------------------------------------+
```

### Data Flow Breakdown
1. Ingestion: Raw data is ingested. This requires parsing various formats accurately.
2. Processing: Text is split. If chunks are too large, retrieval precision drops. If too small, context is lost.
3. Embedding: The embedding model maps semantic meaning to a high-dimensional vector space.
4. Storage: The vector database indexes these vectors using structures like HNSW (Hierarchical Navigable Small World) for fast approximate search.
5. Querying: The user's prompt is embedded.
6. Retrieval: The database returns the most mathematically similar vectors.
7. Post-Processing: Initial retrieval (bi-encoder) is fast but imprecise. A cross-encoder reranker performs deep attention between the query and each document to reorder them based on actual relevance.
8. Generation: The LLM reads the verified context and answers the query without hallucinating.

---

## 2. Indexing Pipeline — Complete Implementation

The indexing pipeline is responsible for preparing your data for retrieval. It involves document loading, text splitting (chunking), embedding generation, and vector database upsertion. The implementation must handle batches efficiently and manage metadata appropriately.

```python
import uuid
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import pinecone # Or any other vector DB client
import tiktoken

class IndexingPipeline:
    def __init__(self, embedding_model_name: str, index_name: str, api_key: str):
        """
        Initializes the indexing pipeline.
        
        Args:
            embedding_model_name: The HuggingFace model string for embeddings.
            index_name: Name of the vector database index.
            api_key: API key for the vector database.
        """
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Initialize Vector DB (Pseudocode for Pinecone as example)
        pinecone.init(api_key=api_key, environment="us-west1-gcp")
        self.index = pinecone.Index(index_name)
        
    def chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
        """
        Splits text into chunks of specified token length with overlap.
        
        Args:
            text: The raw input text string.
            chunk_size: Maximum tokens per chunk.
            overlap: Number of overlapping tokens between consecutive chunks.
            
        Returns:
            A list of string chunks.
        """
        tokens = self.tokenizer.encode(text)
        chunks = []
        
        if len(tokens) == 0:
            return chunks
            
        start_idx = 0
        while start_idx < len(tokens):
            end_idx = min(start_idx + chunk_size, len(tokens))
            chunk_tokens = tokens[start_idx:end_idx]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text)
            
            # Move start index forward, accounting for overlap
            start_idx += (chunk_size - overlap)
            
        return chunks
        
    def generate_embeddings(self, chunks: List[str]) -> List[List[float]]:
        """
        Generates dense vector embeddings for a list of text chunks.
        
        Args:
            chunks: List of text chunks.
            
        Returns:
            List of embedding vectors (list of floats).
        """
        # sentence-transformers handles batching internally, but for very large 
        # lists, you should batch this call as well.
        embeddings = self.embedding_model.encode(chunks, show_progress_bar=False)
        return embeddings.tolist()
        
    def batch_upsert(self, documents: List[Dict[str, Any]], batch_size: int = 100):
        """
        Processes and upserts documents into the vector database in batches.
        
        Args:
            documents: List of dicts containing 'text' and 'metadata'.
            batch_size: Number of vectors to upsert per API call.
        """
        vectors_to_upsert = []
        
        for doc in documents:
            raw_text = doc.get("text", "")
            metadata = doc.get("metadata", {})
            
            # 1. Chunking
            chunks = self.chunk_text(raw_text, chunk_size=400, overlap=40)
            
            # 2. Embedding
            embeddings = self.generate_embeddings(chunks)
            
            # 3. Prepare Vector Records
            for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
                vector_id = str(uuid.uuid4())
                
                # Enrich metadata with the actual text payload
                chunk_metadata = metadata.copy()
                chunk_metadata["text"] = chunk
                chunk_metadata["chunk_index"] = i
                
                vectors_to_upsert.append((vector_id, emb, chunk_metadata))
                
                # 4. Upsert in batches
                if len(vectors_to_upsert) >= batch_size:
                    self.index.upsert(vectors_to_upsert)
                    vectors_to_upsert = []
                    
        # Upsert any remaining vectors in the buffer
        if vectors_to_upsert:
            self.index.upsert(vectors_to_upsert)
            
        print("Batch upsert completed successfully.")

```

The code above demonstrates a robust, production-ready indexing flow. It handles token-based chunking rather than character-based chunking, which is crucial because embedding models have strict token limits. It also safely manages metadata and batching to avoid API timeouts.

---

## 3. Retrieval Pipeline — Naive vs Advanced

The standard, naive retrieval pipeline involves taking the user query, embedding it, and doing a direct vector search. While fast and easy to implement, it suffers from severe limitations.

### Naive Retrieval Implementation

```python
class NaiveRetriever:
    def __init__(self, embedding_model, index):
        self.embedding_model = embedding_model
        self.index = index
        
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Performs a naive vector search.
        """
        # 1. Embed the query
        query_embedding = self.embedding_model.encode([query])[0].tolist()
        
        # 2. Query the index
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        # 3. Extract metadata (which contains the text)
        retrieved_docs = []
        for match in results.get("matches", []):
            retrieved_docs.append(match["metadata"])
            
        return retrieved_docs
```

### Problems with Naive Retrieval
1. Vocabulary Mismatch: The user's query might be phrased as a question ("How do I reset my password?"), while the target document is phrased as an imperative ("To reset your password, click here."). The vector space might map these slightly apart.
2. Lack of Context: A short query lacks the dense contextual keywords present in long-form documents.
3. Bi-Encoder Limitation: The embeddings used for fast search (bi-encoders) compress all semantic meaning into a single vector independently. They cannot model the complex interaction between the query terms and the document terms.

To solve these, we introduce advanced retrieval techniques.

---

## 4. Advanced Retrieval Techniques

### Hypothetical Document Embeddings (HyDE)

HyDE is a query transformation technique. Instead of embedding the raw user query, we ask an LLM to generate a hypothetical, fake answer to the query. We then embed this fake answer and use it for retrieval. The rationale is that a fake answer, even if factually incorrect, will have the exact linguistic structure and vocabulary of the true target document, bridging the semantic gap in the vector space.

```python
import openai

def generate_hyde_document(query: str, api_key: str) -> str:
    """
    Generates a hypothetical document based on the query.
    """
    openai.api_key = api_key
    
    prompt = f"Please write a short passage that answers the following question. Do not worry about factual accuracy, focus on structure and vocabulary.\n\nQuestion: {query}\n\nPassage:"
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=200
    )
    
    return response.choices[0].message.content.strip()

# Usage in pipeline:
# fake_doc = generate_hyde_document(user_query, api_key)
# query_embedding = embedding_model.encode(fake_doc)
```

### Multi-Query Retrieval with Reciprocal Rank Fusion (RRF)

Users often write poorly formulated queries. Multi-query retrieval asks an LLM to rewrite the query in N different ways (e.g., expanding acronyms, rephrasing). We run all N queries against the vector DB, retrieve candidates for each, and combine them using Reciprocal Rank Fusion.

```python
def reciprocal_rank_fusion(list_of_result_lists: List[List[Dict]], k: int = 60) -> List[Dict]:
    """
    Fuses multiple ranked lists using RRF.
    Score = 1 / (k + rank)
    
    Args:
        list_of_result_lists: A list where each element is a list of retrieved documents.
        k: Smoothing constant.
        
    Returns:
        A sorted list of unique documents based on their RRF score.
    """
    fused_scores = {}
    doc_store = {}
    
    for result_list in list_of_result_lists:
        for rank, doc in enumerate(result_list):
            doc_id = doc.get("id", str(hash(doc.get("text"))))
            if doc_id not in fused_scores:
                fused_scores[doc_id] = 0
                doc_store[doc_id] = doc
                
            fused_scores[doc_id] += 1 / (k + rank + 1)
            
    # Sort documents by fused score descending
    sorted_docs = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Return sorted document dictionaries
    return [doc_store[doc_id] for doc_id, score in sorted_docs]
```

---

## 5. Cross-Encoder Reranking — The Most Important Advanced Technique

Retrieval relies on Bi-Encoders: the query and document are embedded separately and compared via cosine similarity. This is fast but mathematically shallow.
Cross-Encoders process the query and the document simultaneously through the transformer layers. The self-attention mechanism evaluates the interaction between every word in the query and every word in the document, producing a highly accurate relevance score.

Because cross-encoders are slow, we use a two-stage pipeline:
1. Retrieve Top-100 using a Bi-Encoder (Vector DB).
2. Rerank the Top-100 using a Cross-Encoder and keep the Top-5.

### Local Cross-Encoder Implementation

```python
from sentence_transformers import CrossEncoder

class Reranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initializes a local cross-encoder model.
        """
        self.model = CrossEncoder(model_name)
        
    def rerank(self, query: str, documents: List[Dict[str, Any]], top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Reranks a list of documents based on cross-encoder scores.
        """
        if not documents:
            return []
            
        # Prepare pairs of (query, document_text)
        pairs = [[query, doc["text"]] for doc in documents]
        
        # Predict relevance scores
        scores = self.model.predict(pairs)
        
        # Attach scores to documents
        for idx, doc in enumerate(documents):
            doc["rerank_score"] = float(scores[idx])
            
        # Sort documents by the new score descending
        reranked_docs = sorted(documents, key=lambda x: x["rerank_score"], reverse=True)
        
        # Return the top N most relevant documents
        return reranked_docs[:top_n]
```

If local hosting is not viable, managed API alternatives like Cohere Rerank or BGE-Reranker via HuggingFace Inference Endpoints provide excellent drop-in replacements with multi-lingual support.

---

## 6. Maximum Marginal Relevance (MMR)

Often, the top N results returned by vector search are highly relevant but entirely redundant (e.g., five chunks from the exact same paragraph). If you feed redundant data to an LLM, you waste context window space and lose out on diverse perspectives that might contain the full answer.

Maximum Marginal Relevance (MMR) solves this by balancing relevance to the query against diversity among the selected documents.

The MMR formula is:
MMR = argmax_{D_i \in R \setminus S} [ \lambda * Sim_1(D_i, Q) - (1 - \lambda) * \max_{D_j \in S} Sim_2(D_i, D_j) ]

Where:
- R is the set of retrieved documents.
- S is the set of already selected documents.
- \lambda controls the trade-off. \lambda=1 means pure relevance (standard search). \lambda=0 means pure diversity.

### NumPy MMR Implementation

```python
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def maximal_marginal_relevance(
    query_embedding: np.ndarray,
    doc_embeddings: np.ndarray,
    documents: List[Dict],
    top_k: int = 5,
    lambda_mult: float = 0.5
) -> List[Dict]:
    """
    Selects documents to maximize relevance and diversity using MMR.
    """
    if len(documents) <= top_k:
        return documents
        
    # Calculate similarity of all docs to query
    query_sim = cosine_similarity(query_embedding.reshape(1, -1), doc_embeddings)[0]
    
    # Calculate similarity matrix among all docs
    doc_sim_matrix = cosine_similarity(doc_embeddings, doc_embeddings)
    
    selected_indices = []
    unselected_indices = list(range(len(documents)))
    
    # Select the first document (most relevant)
    best_idx = int(np.argmax(query_sim))
    selected_indices.append(best_idx)
    unselected_indices.remove(best_idx)
    
    # Iteratively select the remaining top_k - 1 documents
    while len(selected_indices) < top_k and unselected_indices:
        best_score = -np.inf
        idx_to_add = -1
        
        for idx in unselected_indices:
            # Relevance to query
            rel_score = query_sim[idx]
            
            # Maximum similarity to already selected docs
            sim_to_selected = np.max([doc_sim_matrix[idx, s_idx] for s_idx in selected_indices])
            
            # MMR Equation
            mmr_score = (lambda_mult * rel_score) - ((1 - lambda_mult) * sim_to_selected)
            
            if mmr_score > best_score:
                best_score = mmr_score
                idx_to_add = idx
                
        selected_indices.append(idx_to_add)
        unselected_indices.remove(idx_to_add)
        
    return [documents[i] for i in selected_indices]
```

---

## 7. The Full Advanced RAG Pipeline

We now assemble the components: Naive Retrieval -> Cross-Encoder Reranking -> LLM Generation.

```python
import openai

class AdvancedRAGPipeline:
    def __init__(self, retriever, reranker, openai_api_key: str):
        self.retriever = retriever
        self.reranker = reranker
        openai.api_key = openai_api_key
        
    def generate_answer(self, query: str) -> str:
        """
        Executes the full retrieve-rerank-generate pipeline.
        """
        print(f"Executing query: {query}")
        
        # 1. Retrieve broadly (High Recall)
        print("Retrieving candidates...")
        initial_candidates = self.retriever.retrieve(query, top_k=50)
        
        if not initial_candidates:
            return "I could not find any relevant information to answer your question."
            
        # 2. Rerank accurately (High Precision)
        print("Reranking candidates...")
        top_context_docs = self.reranker.rerank(query, initial_candidates, top_n=5)
        
        # 3. Format context
        context_string = ""
        for i, doc in enumerate(top_context_docs):
            context_string += f"\n--- Document {i+1} ---\n{doc['text']}\n"
            
        # 4. Generate with Guardrails
        prompt = f"""
You are a highly capable and precise engineering assistant.
Answer the user's question based strictly on the provided context below.
If the context does not contain the answer, reply exactly with: "I do not have enough information to answer."
Do not attempt to guess or use outside knowledge.

Context:
{context_string}

Question: {query}
Answer:"""

        print("Generating final answer...")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.0
        )
        
        return response.choices[0].message.content.strip()
```

This pipeline guarantees that the LLM is only fed the highest quality, most relevant text chunks, drastically reducing hallucination rates and saving token costs.

---

## 8. RAG Evaluation — RAGAS Framework

You cannot improve what you cannot measure. Traditional LLM metrics (BLEU, ROUGE) are useless for RAG. We need frameworks like RAGAS (Retrieval Augmented Generation Assessment) that evaluate the pipeline without requiring human-labeled ground truth datasets. RAGAS uses an LLM-as-a-judge to compute four critical metrics:

1. Context Precision: Evaluates whether all of the ground-truth relevant items present in the contexts are ranked high. High precision means the top retrieved chunks are perfectly relevant to the query.
2. Context Recall: Measures the extent to which the retrieved context aligns with the annotated answer as ground truth. Is the retrieval pipeline fetching all necessary facts?
3. Faithfulness (Hallucination metric): Measures the factual consistency of the generated answer against the retrieved context. If the answer claims something not found in the context, faithfulness drops.
4. Answer Relevancy: Measures how directly the generated answer addresses the user's query.

### Example RAGAS Evaluation Setup

```python
# Note: Ragas requires setting up metrics and datasets.
# This is a conceptual implementation of how you'd wrap it.
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_recall,
    context_precision,
)
from datasets import Dataset

def evaluate_rag_system(questions: List[str], ground_truths: List[str], pipeline: AdvancedRAGPipeline):
    """
    Evaluates the RAG pipeline over a test set.
    """
    answers = []
    contexts = []
    
    # Generate data
    for q in questions:
        # We modify the pipeline slightly to return contexts alongside the answer for evaluation
        initial_candidates = pipeline.retriever.retrieve(q, top_k=50)
        top_context_docs = pipeline.reranker.rerank(q, initial_candidates, top_n=5)
        
        context_texts = [doc['text'] for doc in top_context_docs]
        contexts.append(context_texts)
        
        answer = pipeline.generate_answer(q) # In real implementation, pass contexts to avoid re-running
        answers.append(answer)
        
    # Build huggingface dataset
    data = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    }
    dataset = Dataset.from_dict(data)
    
    # Run Evaluation
    result = evaluate(
        dataset,
        metrics=[
            context_precision,
            faithfulness,
            answer_relevancy,
            context_recall,
        ]
    )
    
    print("RAGAS Evaluation Results:")
    print(result)
```

By tracking these metrics over time, you can quantify whether a change in chunk size or a new embedding model actually improves the system.

---

## 9. Chunking Strategies Revisited for RAG

Naive fixed-size token chunking often fractures logical boundaries. Advanced chunking strategies maintain context.

### Parent-Child Retrieval (Auto-Merging Retriever)
Instead of retrieving small, disjointed chunks, we map large "Parent" chunks (e.g., a whole page) to multiple smaller "Child" chunks (e.g., sentences).
We embed and search over the Child chunks because smaller chunks yield higher similarity scores and better retrieval accuracy.
However, if a Child chunk is matched, we do not feed the Child to the LLM. Instead, we fetch its Parent chunk and feed the entire Parent to the LLM. This gives the LLM broad surrounding context while maintaining the sharp retrieval accuracy of small chunks.

### Sentence Window Retrieval
Similar to Parent-Child. The document is split into individual sentences. The vector DB stores embeddings of single sentences.
When a sentence matches the query, the retrieval system fetches a "window" of sentences around it (e.g., 2 sentences before, 2 sentences after). The LLM is provided the 5-sentence block. This prevents the "lost in the middle" problem while ensuring the semantic search is highly localized.

---

## 10. Guardrails and Production Safety

A production RAG system requires strict safety mechanisms.

1. Query Validation: Before processing a query, validate it against a lightweight classifier to ensure it is not a prompt injection attack or severely off-topic.
2. Empty Retrieval Handling: If the vector DB returns scores below a certain threshold (e.g., Cosine Similarity < 0.7), the system should short-circuit and reply, "I don't have information on this topic," rather than forcing the LLM to hallucinate from irrelevant context.
3. Source Attribution: Always require the LLM to cite the document IDs or URLs provided in the context metadata. This builds user trust and allows auditing.
4. PII Detection: Run retrieved contexts through a PII scrubber (like Presidio) before sending them to external LLM APIs like OpenAI to ensure data compliance.
5. Rate Limiting and Caching: Implement semantic caching (e.g., GPTCache). If a new query has a >0.95 semantic similarity to a previously answered query, return the cached answer immediately to save latency and compute costs.

```python
# Semantic Caching Example
def get_cached_or_generate(query: str, cache_index, pipeline: AdvancedRAGPipeline):
    query_emb = pipeline.retriever.embedding_model.encode([query])[0].tolist()
    cache_results = cache_index.query(vector=query_emb, top_k=1)
    
    if cache_results["matches"] and cache_results["matches"][0]["score"] > 0.95:
        print("Cache hit!")
        return cache_results["matches"][0]["metadata"]["answer"]
        
    print("Cache miss. Generating new answer...")
    answer = pipeline.generate_answer(query)
    
    # Store in cache
    cache_index.upsert([(str(uuid.uuid4()), query_emb, {"answer": answer})])
    return answer
```

By implementing these strategies, your RAG architecture evolves from a simple tutorial project into a robust, enterprise-grade AI system.
