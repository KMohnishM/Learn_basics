# Vector Databases & RAG Integration Q&A

### Q1: Explain HyDE in detail. What distribution mismatch between short queries and long documents does it fix? What are two failure modes where HyDE hurts instead of helps?

HyDE (Hypothetical Document Embeddings) is a retrieval enhancement technique designed to bridge the semantic gap between a short, often ambiguous user query and the detailed, comprehensive documents in a corpus. When a user issues a short query (e.g., "how to fix a flat tire"), its embedding often resides in a different region of the vector space compared to an instructional manual containing step-by-step procedures. This constitutes a distribution mismatch between short, intent-driven queries and long, factual documents. 
HyDE addresses this by using an LLM to generate a hypothetical, potentially factually incorrect, but structurally representative document in response to the query. Instead of embedding the short query, the system embeds this generated document. The hypothetical document's embedding will theoretically be closer in the latent space to the actual, factual documents in the corpus because they share a similar length, vocabulary, and structural distribution. 

```python
# HyDE Implementation snippet
from langchain.llms import OpenAI
from langchain.embeddings import OpenAIEmbeddings

llm = OpenAI()
query = "What is the capital of France?"
hypothetical_doc = llm.predict(f"Write a short paragraph answering: {query}")
query_embedding = OpenAIEmbeddings().embed_query(hypothetical_doc)
# Use query_embedding for nearest neighbor search in vector DB
```

However, HyDE introduces failure modes. First, in highly specialized domains (e.g., niche medical research), the LLM might generate a hypothetical document containing domain-specific jargon that is entirely irrelevant or opposite in meaning to the query, pulling the embedding away from the correct documents. Second, for precise keyword-based lookup queries like "Invoice ID 59281 status", generating a hypothetical document is counterproductive and dilutes the exact match signal, leading to poorer retrieval performance than simple query embedding.

### Q2: Why can cross-encoders not scale to full corpus retrieval? Calculate the latency: if a cross-encoder scores 1 pair in 5ms, how long to score 1M documents?

Cross-encoders are powerful models that take both a query and a document as joint input and output a relevance score, allowing for deep, bidirectional attention between the query terms and document terms. However, they cannot scale to full corpus retrieval because their architecture requires inference at query time for every single query-document pair. Unlike bi-encoders (which compute embeddings independently that can be cached and indexed using HNSW or IVF), a cross-encoder must run the full transformer stack over the concatenated string `[CLS] Query [SEP] Document [SEP]`.

This fundamentally prevents pre-computation of document representations. If a cross-encoder takes 5 milliseconds to score a single query-document pair, evaluating a full corpus of 1,000,000 documents sequentially would take:
$$ 1,000,000 \text{ documents} \times 5 \text{ ms/document} = 5,000,000 \text{ ms} = 5,000 \text{ seconds} \approx 83.33 \text{ minutes} $$

```python
# Cross-encoder latency calculation
latency_per_pair_ms = 5
num_docs = 1_000_000
total_latency_ms = latency_per_pair_ms * num_docs
total_latency_sec = total_latency_ms / 1000
print(f"Total time: {total_latency_sec} seconds")
```

Even with massive parallelization, scoring millions of documents dynamically is computationally prohibitive and too slow for user-facing applications (where sub-second latency is expected). Hence, cross-encoders are strictly relegated to a re-ranking stage, where they evaluate only a small subset of candidate documents (e.g., top 100) surfaced by a fast, scalable bi-encoder first-stage retrieval system.

### Q3: Explain all four RAGAS metrics with formulas. Which metric detects hallucinations? What LLM is used as judge, and what is the computational cost of running RAGAS on 1000 Q&A pairs?

RAGAS (Retrieval Augmented Generation Assessment) employs four primary metrics to evaluate RAG pipelines:

1. **Context Precision**: Measures the signal-to-noise ratio in retrieved contexts. It checks if the relevant chunks are ranked higher. 
   $$ \text{Context Precision} = \frac{\sum_{k=1}^K \text{Precision@k} \times v_k}{\text{Total number of relevant items}} $$
   where $v_k \in \{0, 1\}$ indicates relevance at rank $k$.
2. **Context Recall**: Measures if all the information required to answer the query is present in the retrieved context. 
   $$ \text{Context Recall} = \frac{| \text{Relevant sentences in Context} \cap \text{Ground Truth Sentences} |}{| \text{Ground Truth Sentences} |} $$
3. **Answer Relevance**: Measures how pertinent the generated answer is to the given prompt, penalizing incomplete or redundant answers. It uses reverse generation (generating queries from the answer) and computes embedding similarity.
   $$ \text{Answer Relevance} = \frac{1}{n} \sum_{i=1}^n \cos(\text{emb}(q), \text{emb}(q'_i)) $$
4. **Faithfulness**: This metric detects hallucinations. It measures the factual consistency of the generated answer with respect to the retrieved context. 
   $$ \text{Faithfulness} = \frac{| \text{Claims in Answer verifiable from Context} |}{| \text{Total Claims in Answer} |} $$

RAGAS typically uses strong LLMs like GPT-4 or GPT-3.5-Turbo as the judge. Running these metrics on 1,000 Q&A pairs is computationally expensive. Assuming GPT-4 costs roughly $0.03 per 1K input tokens and $0.06 per 1K output tokens, and an average evaluation requires 3,000 tokens (input + output across all metric prompts), a single Q&A evaluation costs about $0.15. Thus, evaluating 1,000 pairs would cost approximately $150 and take several hours due to API rate limits, highlighting the trade-off between automated evaluation scale and operational cost.

### Q4: Write the MMR formula. Set lambda=0.3 vs lambda=0.9 — describe the output difference. When is low lambda appropriate (e.g., diversity needed in legal document search)?

Maximal Marginal Relevance (MMR) is a technique used to balance relevance and diversity in search results. It iteratively selects documents from a candidate set to maximize a combined score. The formula is:
$$ \text{MMR} = \arg\max_{D_i \in R \setminus S} \left[ \lambda \cdot \text{Sim}_1(D_i, Q) - (1 - \lambda) \cdot \max_{D_j \in S} \text{Sim}_2(D_i, D_j) \right] $$
Where:
- $Q$ is the user query.
- $D_i$ is a candidate document.
- $R$ is the set of all retrieved documents.
- $S$ is the set of already selected documents.
- $\lambda$ (lambda) is a tuning parameter between 0 and 1.
- $\text{Sim}_1$ is the similarity between document and query.
- $\text{Sim}_2$ is the similarity between the candidate document and already selected documents.

```python
# Pseudo-code for MMR
def calculate_mmr(doc, query, selected_docs, lambda_val):
    relevance = similarity(doc, query)
    diversity = max([similarity(doc, s_doc) for s_doc in selected_docs]) if selected_docs else 0
    return lambda_val * relevance - (1 - lambda_val) * diversity
```

When $\lambda = 0.9$, the formula heavily prioritizes relevance over diversity. The output will be a set of highly similar documents that all address the query but may be redundant (e.g., returning 5 identical news articles from different publishers). When $\lambda = 0.3$, the formula prioritizes diversity, penalizing redundancy. The output will cover different angles or topics related to the query. A low lambda is highly appropriate in exploratory search or legal document discovery, where reading the same clause 5 times is useless, but finding 5 distinct precedents or clauses relevant to the broad case is immensely valuable.

### Q5: Walk through the full advanced RAG pipeline step by step: query embedding → retrieve 50 → rerank to 10 → MMR to 5 → prompt assembly → LLM generate. What quality issue does each step address?

An advanced RAG pipeline mitigates various retrieval and generation issues through a multi-stage approach.
1. **Query Embedding**: The user query is converted into a dense vector (e.g., using `text-embedding-3-small`). This addresses lexical mismatch, enabling semantic matching rather than exact keyword overlap.
2. **Retrieve 50 (First-Stage Retrieval)**: A fast vector database (like Pinecone or Milvus) retrieves the top 50 candidates using Approximate Nearest Neighbors (ANN). Retrieving a broad net of 50 documents addresses the "recall" issue, ensuring the actual relevant documents are captured even if their initial embedding similarity wasn't perfectly top-ranked.
3. **Rerank to 10**: A powerful cross-encoder (e.g., Cohere Rerank) scores the top 50 candidates. This addresses "precision" by fixing the shallow interactions of bi-encoders, pushing the truly relevant documents to the top and eliminating semantically similar but contextually incorrect noise.
4. **MMR to 5**: Maximal Marginal Relevance is applied to the top 10 to select the final 5 documents. This addresses "redundancy". By enforcing diversity, the LLM receives context from varied perspectives rather than repetitive chunks, maximizing the information density within the context window.
5. **Prompt Assembly**: The 5 final chunks are formatted with clear delimiters and injected into a prompt template with instructions (e.g., "Answer using ONLY the provided context"). This addresses "hallucination" and structural confusion, firmly grounding the LLM.
6. **LLM Generate**: The final prompt is sent to an LLM (e.g., GPT-4) to synthesize the response. This addresses "synthesis", providing a cohesive, natural language answer instead of a disjointed list of search snippets.

### Q6: Explain the parent-child retrieval pattern. What is stored in the vector index vs the docstore? Why does it improve generation quality over standard chunking?

The parent-child retrieval pattern (or Auto-Merging Retrieval) decouples the unit of retrieval from the unit of synthesis. In standard chunking, the document is broken into uniform chunks (e.g., 500 tokens), which are both embedded for search and fed to the LLM. However, large chunks dilute the semantic focus (hurting retrieval), while small chunks lack context (hurting generation).

Parent-child retrieval resolves this by splitting documents hierarchically. A large "parent" chunk (e.g., 1000 tokens) is divided into multiple smaller "child" chunks (e.g., 200 tokens each). 
- **Vector Index**: Only the embeddings of the small, highly focused child chunks are stored here.
- **Docstore (Key-Value Store)**: The large parent chunks are stored here, indexed by a unique ID.

```python
# Parent-child retrieval logic
child_matches = vector_db.search(query_embedding, top_k=5)
parent_ids = set([match.metadata["parent_id"] for match in child_matches])
context_chunks = [docstore.get(p_id) for p_id in parent_ids]
```

During retrieval, the query searches against the child chunks, ensuring high precision because the short children have dense semantic meanings. However, when a child chunk matches, the system retrieves its corresponding parent chunk from the docstore and feeds the parent to the LLM. This dramatically improves generation quality because the LLM receives comprehensive context (the surrounding paragraphs), reducing "lost in the middle" errors and enabling better synthesis than standard isolated chunks.

### Q7: Write the RRF formula. Show a worked example: two rankings of 5 documents each, compute the merged RRF scores. Why is k=60 used instead of a raw score average?

Reciprocal Rank Fusion (RRF) is a robust algorithm to combine multiple ranked lists (e.g., dense vector search and sparse BM25 search) without requiring score calibration. The formula is:
$$ \text{RRF}(d) = \sum_{r \in R} \frac{1}{k + r(d)} $$
Where:
- $d$ is a document.
- $R$ is the set of rankings.
- $r(d)$ is the rank of document $d$ in a specific ranking (1-indexed).
- $k$ is a constant (typically 60).

**Worked Example**:
Let $k=60$. 
Ranking A (BM25): [Doc1, Doc2, Doc3, Doc4, Doc5]
Ranking B (Vector): [Doc3, Doc1, Doc5, Doc6, Doc7]

Calculating RRF for Doc1:
- Rank in A = 1, Rank in B = 2
- $\text{RRF}(Doc1) = \frac{1}{60 + 1} + \frac{1}{60 + 2} = \frac{1}{61} + \frac{1}{62} \approx 0.01639 + 0.01613 = 0.03252$

Calculating RRF for Doc3:
- Rank in A = 3, Rank in B = 1
- $\text{RRF}(Doc3) = \frac{1}{60 + 3} + \frac{1}{60 + 1} = \frac{1}{63} + \frac{1}{61} \approx 0.01587 + 0.01639 = 0.03226$

Comparing these, Doc1 wins over Doc3.
Using $k=60$ (instead of a raw score average) provides a gentle curve that heavily weights documents consistently appearing in the top 10-20 ranks across lists while penalizing outliers. Raw score averaging fails because dense vector similarities (usually 0.7 to 1.0) and sparse BM25 scores (can be 10.0 to 100.0) occupy completely different mathematical distributions. RRF relies purely on ordinal rankings, making it entirely scale-invariant and immune to uncalibrated scores.

### Q8: Construct an example with context recall=0.95 and context precision=0.40. Explain what this means for the retrieved context quality and its effect on LLM generation.

**Scenario**: A user asks, "What are the side effects, dosage, and contradictions of Medication X?"
The ground truth requires three specific facts: 
1. Side effects: Nausea, dizziness.
2. Dosage: 50mg daily.
3. Contradictions: Do not mix with alcohol.

The retrieval system returns 10 document chunks. 
- Chunk 8 contains the side effects and dosage.
- Chunk 9 contains the contradictions.
- Chunks 1-7 and 10 are completely irrelevant marketing material about Medication X.

**Metrics analysis**:
- **Context Recall = 0.95**: High. Almost all the required factual information (side effects, dosage, contradictions) is present somewhere within the retrieved context. (Assume it misses one minor nuance, giving 95% instead of 100%).
- **Context Precision = 0.40**: Low. The relevant chunks were buried at ranks 8 and 9, meaning the first 7 retrieved chunks were useless noise. 

**Effect on LLM Generation**:
This situation represents a classic "needle in a haystack" problem. Because recall is high, the LLM technically has all the information needed to generate a correct answer. However, because precision is low, the context window is flooded with irrelevant noise (chunks 1-7). 
Due to attention mechanism limitations in LLMs (especially the "lost in the middle" phenomenon), the LLM might get distracted by the noise, hallucinate connections, or completely miss the relevant facts buried at the bottom of the prompt. Consequently, despite having the right data, the LLM generation might be degraded, overly verbose, or inaccurate.

### Q9: List 6 specific techniques to prevent hallucination in a production RAG system. For each, explain the mechanism by which it reduces hallucination.

1. **Strict Prompt Directives**: Injecting instructions like "If the answer is not contained in the context, output 'I do not know'." This mechanism forces the LLM to prioritize the grounded context over its parametric memory, establishing a hard constraint on generation.
2. **Context Citations/Attribution**: Forcing the LLM to append citations (e.g., `[Doc 1]`) to every claim. This mechanism enforces logical traceability; if the LLM cannot find a source chunk to link to its generated claim, it is less likely to produce the claim, effectively self-regulating hallucinations.
3. **Low Temperature and Top-P Settings**: Setting `temperature=0` and `top_p=0.1`. The mechanism limits the stochasticity of the token sampling process, forcing the model to pick the most mathematically probable tokens (which are heavily weighted by the provided context) rather than taking "creative" leaps.
4. **Post-Generation Fact-Checking (Self-Correction)**: Using a secondary LLM call to verify the output against the context. The mechanism acts as a critical discriminator. The second model is prompted purely to find contradictions or unsupported claims in the first model's output, catching hallucinations before they reach the user.
5. **High-Precision Reranking (Cross-Encoders)**: Implementing Cohere or BGE rerankers. The mechanism improves context quality by filtering out marginally relevant documents. By feeding the LLM only highly precise, noise-free context, the model has fewer distractors to extrapolate from, reducing hallucinated connections.
6. **Knowledge Graph Integration (GraphRAG)**: Augmenting vector search with deterministic graph traversal. The mechanism grounds generation in structured, hard-coded relationships (e.g., `Entity A -[OWNS]-> Entity B`), providing irrefutable factual paths that the LLM can rely on rather than guessing associations.

### Q10: For a factual Q&A RAG system vs a document summarization RAG system, what chunk sizes would you use? Explain the retrieval precision-context length trade-off for each.

**Factual Q&A RAG System**:
For answering specific questions (e.g., "What is the IP rating of the sensor?"), I would use small chunk sizes (e.g., 128 to 256 tokens) with a moderate overlap (e.g., 20-30 tokens). 
*Trade-off*: Small chunks maximize **retrieval precision**. Because the chunk contains only a few sentences, its vector embedding is highly concentrated around a single topic. When queried for a specific fact, the semantic similarity is strong, pulling the exact snippet to the top. The trade-off is that small chunks lack broad context; if a question requires understanding a multi-page narrative, small chunks will fail.

**Document Summarization RAG System**:
For summarization tasks (e.g., "Summarize the Q3 financial risks"), I would use large chunk sizes (e.g., 1000 to 2048 tokens) with a larger overlap (e.g., 100-200 tokens).
*Trade-off*: Large chunks maximize **context length and cohesion**. Summarization requires the LLM to understand overarching themes, transitions, and multi-paragraph arguments. Large chunks preserve this narrative structure. The trade-off is reduced retrieval precision; a 2000-token chunk embedding is an "average" of many topics. If a user searches for a tiny detail hidden in those 2000 tokens, the overall chunk embedding might not match the query strongly enough to be retrieved.

### Q11: Compare sentence window retrieval with parent-child retrieval. What is indexed vs returned in each? Give an example use case where sentence window is preferred.

Both techniques aim to decouple the retrieval unit from the generation unit to provide better context to the LLM, but they do so differently.

**Sentence Window Retrieval**:
- **What is Indexed**: Individual sentences (e.g., "The revenue grew by 20%.") are embedded and stored in the vector database.
- **What is Returned**: When a sentence matches the query, the system returns that target sentence along with a static window of surrounding sentences (e.g., 2 sentences before and 2 sentences after) from the original document.
- **Mechanism**: It relies on proximity and sequence within the raw text array.

**Parent-Child Retrieval**:
- **What is Indexed**: Small child chunks (e.g., 100-token paragraphs) are embedded and stored in the vector database.
- **What is Returned**: When a child chunk matches, the system returns a predefined, hierarchical "parent" block (e.g., an entire section or document) that encapsulates the child.
- **Mechanism**: It relies on a predefined hierarchical mapping (Child ID -> Parent ID).

**Preferred Use Case for Sentence Window**:
Sentence window is highly preferred in dense, highly technical, or legal documents where information is tightly packed, and boundaries are strict. For example, in a medical diagnostics manual, a specific sentence describing a symptom might be heavily dependent on the exact preceding sentence (a prerequisite condition) and the following sentence (a critical warning). Sentence window strictly preserves this localized linear context, whereas parent-child might return a massive 1000-token parent block that dilutes the LLM's attention away from the localized medical warning.

### Q12: How do you generate a synthetic evaluation dataset for RAG without human labels? Describe the LLM-based Q&A pair generation and RAGAS evaluation loop.

Generating a synthetic evaluation dataset involves using an LLM to act as a "Teacher" model to bootstrap ground-truth data from your corpus.
1. **Document Sampling & Chunking**: Randomly sample representative documents from your corpus and chunk them into standard sizes (e.g., 500 tokens). 
2. **Context-Conditioned Question Generation**: Feed a chunk into an LLM with a prompt like: "Based ONLY on the following text, generate 3 complex questions that a user might ask. The answers must be explicitly present in the text."
3. **Answer Generation (Ground Truth)**: For each generated question, prompt the LLM again: "Answer the following question using ONLY the provided text chunk." This creates the `(query, context, ground_truth_answer)` tuple.
4. **Filtering**: Use the LLM to filter out poor pairs by asking it to rate if the question is answerable purely from the chunk.

```python
# Synthetic Generation Loop
eval_dataset = []
for chunk in corpus_chunks:
    questions = llm.generate_questions(chunk, n=3)
    for q in questions:
        answer = llm.generate_answer(q, chunk)
        eval_dataset.append({"question": q, "ground_truth": answer, "context": chunk})
```

**The RAGAS Evaluation Loop**:
Once the synthetic dataset is built, you run the actual RAG pipeline being tested. You pass the synthetic `questions` through your retriever and generator to get the `retrieved_contexts` and `generated_answers`. 
Finally, you feed the complete tuples `(question, ground_truth, retrieved_contexts, generated_answers)` into the RAGAS framework. RAGAS uses an LLM-as-a-judge to score Context Precision/Recall (comparing retrieved contexts to ground truth) and Faithfulness/Answer Relevance (evaluating the generated answer). This automated loop allows for rapid CI/CD testing of RAG pipeline changes without expensive human annotation.

### Q13: Calculate the OpenAI API cost to embed 10M documents at 500 tokens each using text-embedding-3-small ($0.02/1M tokens). Describe the async batching architecture to achieve this in under 2 hours.

**Cost Calculation**:
- Total documents: 10,000,000
- Tokens per document: 500
- Total tokens: $10,000,000 \times 500 = 5,000,000,000$ tokens.
- Cost rate: $0.02 per 1,000,000 tokens.
- Total cost: $(5,000,000,000 / 1,000,000) \times 0.02 = 5,000 \times 0.02 = \$100.00$.
Embedding 10M documents is surprisingly cheap, costing only $100.

**Async Batching Architecture for Speed**:
To process 5 billion tokens in under 2 hours, sequential API calls will fail due to network latency and rate limits. You need a distributed, asynchronous batching system:
1. **Message Broker / Queue**: Load the 10M document IDs and payloads into a message broker like RabbitMQ, Kafka, or AWS SQS.
2. **Worker Pool (Asyncio)**: Deploy a fleet of distributed workers (e.g., using Celery or Kubernetes pods). Each worker runs an asynchronous event loop (e.g., Python `asyncio` with `aiohttp`).
3. **Batching**: Workers pull documents from the queue and batch them into payloads of 1,000 to 2,000 documents per API request (maximizing payload density up to OpenAI's token limits per request). 
4. **Concurrency and Backoff**: Using `asyncio.gather`, a single worker can manage 50+ concurrent HTTP requests. Implementing robust exponential backoff (e.g., using the `tenacity` library) is critical to handle `HTTP 429 Too Many Requests` errors. 
5. **Tier 5 Limits**: To achieve this speed, the OpenAI account must be on Tier 5, which allows up to 10,000,000 tokens per minute (TPM). 
   - 5 Billion tokens / 10M TPM = 500 minutes theoretically. 
   - *Wait, 500 minutes is over 8 hours!* To achieve under 2 hours (120 minutes), the throughput needs to be $\approx 41.6$ Million TPM. This requires negotiating a custom rate limit with OpenAI or sharding the workload across multiple high-tier Azure OpenAI instances simultaneously.

### Q14: Describe the incremental indexing workflow for a corpus where 5% of documents change daily. Include: content hash comparison, chunk-level delete identification, delete-then-upsert operation.

When 5% of a corpus changes daily, re-embedding the entire corpus is wasteful and expensive. Incremental indexing ensures only new, modified, or deleted documents are processed.

**Workflow Steps**:
1. **Content Hash Comparison**: For every document in the source corpus, compute a deterministic hash (e.g., SHA-256) of its raw content. Maintain a state tracking table (e.g., in PostgreSQL) mapping `Document_ID -> Hash`. During the daily sync, compare the new hashes against the stored hashes. 
   - If Hash matches: Skip.
   - If Hash differs: Mark as `Modified`.
   - If ID is missing in source: Mark as `Deleted`.
   - If ID is new: Mark as `New`.

2. **Chunk-Level Delete Identification**: Vector databases store *chunks*, not whole documents. Therefore, every chunk embedded in the vector DB must carry metadata linking it to its parent document (e.g., `metadata={"doc_id": "ABC"}`). 
   For any document marked `Modified` or `Deleted`, the system queries the vector database to identify all existing chunks associated with that `doc_id`.

3. **Delete-then-Upsert Operation**: 
   - For `Deleted` documents: Issue a delete command to the vector DB using the filter: `delete(where={"doc_id": "ABC"})`.
   - For `Modified` documents: Perform a "Delete-then-Upsert". First, delete the old chunks from the vector DB using the same filter. Then, pass the newly modified document through the chunking and embedding pipeline, and upsert the new vectors. This prevents chunk duplication and "ghost" contexts where old, outdated sentences are retrieved alongside new ones.

```python
# Incremental sync pseudo-code
for doc in modified_docs:
    vector_db.delete(filter={"doc_id": doc.id})
    new_chunks = chunk_and_embed(doc.text)
    vector_db.upsert(vectors=new_chunks, metadata=[{"doc_id": doc.id}]*len(new_chunks))
```

### Q15: How would you build a query router to direct queries to one of 3 specialized vector collections (medical, legal, general)? Compare embedding-based classification (using a small classifier) vs LLM-based classification.

A query router intelligently routes a user's prompt to the most appropriate backend data source, optimizing performance and relevance. If we have medical, legal, and general vector collections, we need a classification step before retrieval.

**Embedding-Based Classification**:
This involves training a lightweight classifier (like Logistic Regression, SVM, or a small neural network) on top of query embeddings. 
- **Mechanism**: The incoming query is embedded (e.g., using `MiniLM-L6-v2`). The vector is fed into the classifier, which outputs a probability distribution across the 3 classes.
- **Pros**: Blazing fast (sub 50ms latency), extremely cheap to run, and highly predictable once trained. 
- **Cons**: Requires a labeled dataset of thousands of queries (medical, legal, general) to train. It struggles with highly nuanced or ambiguous queries that blur boundaries.

**LLM-Based Classification**:
This involves passing the query to an LLM with a structured prompt.
- **Mechanism**: 
```text
Prompt: "You are a routing agent. Route the following user query to one of three databases: 'medical', 'legal', or 'general'. Output ONLY a JSON object: {'route': '<choice>'}. Query: {user_query}"
```
- **Pros**: Zero-shot capabilities; requires zero training data or labeled examples. Extremely flexible and capable of reasoning through complex, ambiguous queries (e.g., "What are the legal liabilities of prescribing this medication off-label?" -> LLM can reason to search both).
- **Cons**: High latency (adds 500ms - 1s to the pipeline before retrieval even starts) and high cost due to API calls per query. 

**Recommendation**: In production, I would use a hybrid approach: an embedding-based classifier for 95% of obvious queries to save cost/latency, falling back to an LLM-based router only when the classifier's confidence score is below a certain threshold (e.g., $< 0.7$).
