# Advanced RAG Questions and Answers

## 1. Why does naive fixed-size chunking cause retrieval failures? Explain semantic chunking with a threshold-based sentence boundary algorithm.
Naive fixed-size chunking divides text into arbitrary blocks of tokens or characters.
This segmentation occurs without respecting semantic boundaries or natural language structures.
This causes retrieval failures because a single coherent idea might be split across two chunks.
If a query pertains to that idea, neither chunk alone may contain enough context.
This failure to capture complete thoughts leads to low similarity scores and false negatives.
Moreover, a chunk might begin in the middle of a sentence, omitting the subject entirely.
Semantic chunking addresses this by splitting text only at logical, linguistic boundaries.
A threshold-based sentence boundary algorithm first splits the text into full sentences.
It then generates dense vector embeddings for each individual sentence using an NLP model.
The algorithm calculates the cosine similarity between adjacent sentence embeddings.
If the similarity between two sentences falls below a predefined threshold, it indicates a topic shift.
A chunk boundary is placed there, while highly similar sentences are concatenated together.
This ensures chunks represent cohesive thoughts, improving the quality of retrieved context.

## 2. Explain Parent-Document hierarchical chunking. How does it resolve the tension between small retrieval chunks and large LLM context needs? Give concrete token size recommendations.
Parent-Document hierarchical chunking is a strategy that decouples retrieval units from synthesis units.
In this approach, a large document is first split into larger "parent" chunks of text.
Each parent chunk is then further divided into much smaller "child" chunks.
Only the smaller child chunks are embedded and indexed within the vector database.
Each child chunk maintains a metadata reference pointing back to its corresponding parent chunk.
This resolves a fundamental tension inherent in all RAG system architectures.
Embedding models perform best on short segments where semantic meaning is not diluted.
Conversely, LLMs require broader context to generate answers without hallucinating facts.
When a query is issued, the vector search retrieves the most relevant small child chunks.
Before generation, the system swaps these child chunks for their full parent chunks.
If multiple child chunks from the same parent are retrieved, the parent is included only once.
A typical token size recommendation is to set parent chunks to 1024 or 2048 tokens.
The child chunks should be sized around 128 to 256 tokens for optimal dense embedding.

## 3. What is HyDE (Hypothetical Document Embeddings)? Walk through the full lifecycle: query -> hypothetical answer generation -> embedding -> retrieval -> answer generation. When does it fail?
HyDE is an advanced retrieval technique addressing the semantic gap between short queries and long documents.
The lifecycle begins when a user submits a naturally phrased question or query.
Instead of embedding the query directly, the system passes the query to a generative LLM.
The prompt instructs the LLM to write a hypothetical answer to the specific query.
This hypothetical document mimics the lexical and semantic structure of a real target document.
The system then embeds this hypothetical document using a standard dense encoder model.
This generated embedding is used to perform a vector similarity search against the corpus.
Because the hypothetical document resembles actual documents, it retrieves more relevant results.
Finally, the retrieved real documents are passed to the LLM alongside the original query.
The LLM uses these grounded documents to generate the final, factually accurate answer.
HyDE typically fails when the initial generative LLM lacks basic domain understanding.
This results in a hypothetical document that is wildly off-topic or uses incorrect terminology.
It also struggles with highly specific factual lookups where the LLM cannot guess the semantic neighborhood.

## 4. How does Anthropic Contextual Retrieval add chunk-level context? Show the prompting technique. How does it reduce retrieval failure by 49%?
Anthropic Contextual Retrieval solves the problem of chunks losing meaning when isolated from documents.
Traditional chunking strips away broader context, rendering specific details ambiguous.
A chunk stating "revenue increased by 20%" is useless without knowing the company or quarter.
Contextual Retrieval addresses this by using an LLM to generate a short summary for every chunk.
The system passes the entire original document and the specific chunk to an LLM simultaneously.
The prompting technique is: "Here is a document: {document}. Here is a chunk: {chunk}."
The prompt continues: "Write a short context that situates this chunk within the document."
The LLM might output: "This chunk describes Acme Corp's Q3 2023 financial performance."
This generated context is prepended directly to the chunk text before it is embedded.
By explicitly embedding the missing context, the model creates a much more accurate vector.
This reduces retrieval failure by up to 49% by preserving critical semantic signals.
It prevents situations where implicit context is lost during the document segmentation process.
The chunks now contain the necessary keywords to match user queries with high precision.

## 5. What is Late Chunking (ColBERT-style)? How does passing the full document through the encoder before pooling chunk embeddings preserve cross-chunk semantic context?
Late Chunking fundamentally shifts when a document is broken into pieces during embedding.
Traditional early chunking splits the text before passing it to the transformer encoder.
Late Chunking passes the entire document through the transformer encoder first.
Inside the transformer, self-attention mechanisms allow tokens to attend to the entire document.
This means the contextualized embedding for a word is influenced by surrounding paragraphs.
Only after this full-document contextualization are the token embeddings pooled into chunks.
Because token embeddings were generated with global knowledge, chunk embeddings preserve context.
An ambiguous pronoun in a later chunk will reflect its antecedent from an earlier chunk.
This approach allows chunks to remain small for efficient and fast vector retrieval.
Simultaneously, the chunks possess the deep contextual awareness of the full source document.
It significantly reduces the loss of semantic meaning that plagues traditional chunking.
ColBERT utilizes this by enabling fine-grained, token-level interactions at search time.
This creates a highly robust retrieval mechanism that understands document-wide semantics.

## 6. Compare Dense Vector Search (bi-encoders) and Sparse BM25 Search. Give concrete failure examples for each. Why does dense search fail on product SKUs like 'F-450-XL-BLK'?
Dense Vector Search uses bi-encoders to map text into a continuous semantic vector space.
It retrieves documents based on conceptual similarity and cosine distance calculations.
Sparse BM25 Search relies on exact keyword matching and term frequency-inverse document frequency.
Dense search excels at understanding synonyms and conceptual overlap between different terms.
A concrete failure of dense search occurs when precise keyword matching is strictly required.
For instance, searching for a specific error code might retrieve conceptually similar but wrong codes.
BM25 excels at these exact matches but fails entirely on vocabulary mismatches and synonyms.
If a query uses "terminate" and the document uses "fire," BM25 yields zero results.
Dense search struggles significantly with product SKUs like "F-450-XL-BLK" due to tokenization.
These alphanumeric strings lack inherent semantic meaning in standard pre-training text corpora.
The dense encoder treats them as out-of-vocabulary tokens or splits them into meaningless subwords.
The resulting vector represents a vague amalgamation rather than a precise product identifier.
This makes distinguishing between "F-450-XL-BLK" and "F-350-XL-BLK" nearly impossible in vector space.

## 7. Explain the Reciprocal Rank Fusion (RRF) formula: RRF(d) = sum(1 / (k + rank_m(d))). How does it merge ranked lists without score normalization? What is the typical k value?
Reciprocal Rank Fusion (RRF) combines results of multiple retrieval methods into one list.
The formula calculates a score for document 'd' across all retrieval methods 'm'.
The variable 'rank_m(d)' is the ordinal rank of that document in method 'm's results.
The system calculates this score for every document and sorts them descending by RRF score.
This method brilliantly circumvents the need for complex and brittle score normalization.
Different algorithms produce scores on entirely different scales (e.g., cosine vs. BM25).
Attempting to normalize these disparate mathematical distributions is practically impossible.
By relying exclusively on the ordinal rank, RRF treats all retrieval methods equally.
A document ranked highly in multiple lists receives a compounding high RRF score.
A document appearing in only one list will naturally be penalized in the final fusion.
The constant 'k' mitigates the outsized impact of outlier top ranks in a single list.
A typical and empirically validated value for the constant 'k' is 60.
This balances top-ranked documents while ensuring consensus across methods wins out.

## 8. What is the difference between a Bi-Encoder and a Cross-Encoder reranker? Why are Cross-Encoders too slow for initial retrieval but ideal for reranking top-100 to top-5 candidates?
A Bi-Encoder processes the query and the document completely independently of each other.
It passes the query through a transformer, passes the document through a transformer, then compares them.
This allows document embeddings to be pre-computed and stored for blazing-fast search.
A Cross-Encoder concatenates the query and the document together into a single sequence.
It passes this combined sequence through a single transformer model to output a relevance score.
Cross-Encoders are significantly more accurate because tokens can cross-attend to each other.
The self-attention mechanism captures deep lexical and semantic interactions between query and document.
However, Cross-Encoders are computationally catastrophic for large-scale initial retrieval.
Because they must be processed together, you cannot pre-compute document representations.
Scoring a million documents requires a million forward passes at query time, taking hours.
Therefore, a fast Bi-Encoder retrieves the top 100 candidate documents in milliseconds.
The Cross-Encoder then deeply analyzes only those 100 candidates to find the best 5.
This hybrid approach balances the speed of Bi-Encoders with the accuracy of Cross-Encoders.

## 9. Describe the Self-RAG architecture. What are the four reflection tokens ([Retrieve], [IsRel], [IsSup], [IsUse]) and what decision does each represent?
Self-RAG is an active generation framework that trains an LLM to reflect on its process.
It dynamically decides when to retrieve information and how to properly evaluate it.
Unlike standard RAG, Self-RAG interleaves generation, retrieval, and self-critique steps.
The model is fine-tuned to output specific reflection tokens alongside standard text tokens.
The [Retrieve] token signals a decision to search the external knowledge base proactively.
Once retrieved, the [IsRel] token evaluates if the chunks are relevant to the context.
This filters out noisy search results before they contaminate the model's output generation.
After generating a segment, the model outputs the [IsSup] (Is Supported) token.
This token represents a self-critique on whether the claim is fully supported by evidence.
It acts as a powerful built-in hallucination check during the generation phase.
Finally, the [IsUse] token evaluates the overall utility of the generated response segment.
By emitting these tokens, the model dynamically controls its own logical control flow.
This allows it to retry retrievals, discard useless data, and ensure high-quality answers.

## 10. What is Corrective RAG (CRAG)? What three corrective actions (CORRECT, AMBIGUOUS, INCORRECT) are triggered based on relevance evaluation scores?
Corrective RAG (CRAG) improves generation robustness by introducing a retrieval evaluator module.
This module assesses the quality of retrieved documents before any generation begins.
After initial retrieval, the evaluator analyzes the relationship between query and chunks.
It assigns a confidence score to the retrieval results based on semantic relevance.
Based on this score, CRAG triggers one of three specific corrective actions.
If the score is high, it triggers the CORRECT action, proceeding to standard generation.
In this state, the retrieved documents are deemed sufficient and factually accurate.
If the score is low, it triggers the INCORRECT action, completely discarding the retrieval.
CRAG then falls back to a broad web search to prevent generation based on faulty premises.
If the score falls into a middle threshold, it triggers the AMBIGUOUS action.
The system recognizes the information is partially useful but fundamentally incomplete.
It attempts to refine the search space by rewriting the query for secondary retrievals.
This supplements the ambiguous context before passing data to the final generation LLM.

## 11. How does Multi-Query Expansion work? Show a Python example generating 5 query variants and deduplicating retrieved chunks with a set-based approach.
Multi-Query Expansion overcomes the semantic fragility of single-query vector search.
A single query might use terminology that fails to align with the target document's embeddings.
Multi-Query uses an LLM to generate multiple varied phrasings of the original query.
These variations capture different keywords, synonyms, and semantic angles for search.
The system executes a separate vector search for every single generated query variant.
This dramatically increases recall, ensuring relevant documents aren't missed by bad phrasing.
Because queries are similar, the resulting retrieved chunks will often heavily overlap.
The system must deduplicate these results to prevent flooding the LLM context window.
```python
def retrieve_multi_query(original_query, llm, vector_db):
    prompt = f"Generate 5 varied phrasings of this query: '{original_query}'"
    variants = llm.generate(prompt).split('\n')
    all_chunks = []
    for query in variants:
        all_chunks.extend(vector_db.search(query, top_k=5))
    unique_chunks = {}
    for chunk in all_chunks:
        if chunk.id not in unique_chunks:
            unique_chunks[chunk.id] = chunk
    return list(unique_chunks.values())
```
This script uses the chunk's unique identifier as a dictionary key for set-based deduplication.
This guarantees each unique piece of context is only passed to the generation phase once.

## 12. What strategies prevent context stuffing when 20 retrieved chunks are provided to the LLM? Explain LLM Lingua, Selective Compression, and position-based pruning.
Passing too many chunks to an LLM leads to context stuffing and increased latency.
It also triggers the "Lost in the Middle" phenomenon where central context is ignored.
LLM Lingua uses a smaller, efficient language model to identify redundant prompt tokens.
It calculates token perplexity and strips out highly predictable, low-information words.
This compresses the prompt while retaining its core semantic meaning and facts.
Selective Compression involves using an LLM to extract only essential sentences from chunks.
It discards conversational filler or tangential information from the original document text.
Position-based pruning relies on the ranking order of the retrieved document chunks.
Since models return results ordered by relevance, pruning simply truncates the bottom chunks.
A more sophisticated position-based strategy involves reordering the remaining retained chunks.
It places the highest-scoring chunks at the very beginning and very end of the context window.
LLMs demonstrate the highest recall capabilities at the extremes of their context windows.
Lower-ranked chunks are placed in the middle where attention mechanisms are weakest.

## 13. How should tables, markdown structures, and semi-structured data be indexed for RAG? Compare Markdown table extraction vs tabular embedding vs NL-to-SQL.
Standard text chunking destroys row-column relationships in tabular and semi-structured data.
Markdown table extraction involves parsing the document to isolate complete markdown tables.
An LLM generates a textual summary of the table, and both summary and table are embedded.
During retrieval, the summary matches the query, and the full table is passed to the LLM.
Tabular embedding involves serializing each row into a structured natural language string.
These row-level representations are embedded, allowing fine-grained data point retrieval.
However, this approach struggles significantly with complex multi-table joins or aggregations.
NL-to-SQL completely bypasses vector embeddings for highly structured relational data.
The tabular data is loaded directly into a standard relational SQL database environment.
When a query arrives, an LLM translates the natural language into an executable SQL statement.
The deterministic results from the database are then used as context for the final answer.
NL-to-SQL is mandatory for questions requiring aggregations, averages, or complex filtering.
Markdown extraction is preferred for small, reference tables embedded within large text documents.

## 14. Define the key RAG retrieval evaluation metrics: Hit Rate@K, Mean Reciprocal Rank (MRR@K), and NDCG@K. How do you compute each?
Evaluating the retrieval phase is critical for optimizing any production RAG system.
Hit Rate@K measures what percentage of queries had a relevant document in the top K results.
To compute it, check if any ground truth document appears in the top K retrieved list.
The formula is (queries with a hit in top K) divided by (total number of queries).
Mean Reciprocal Rank (MRR@K) evaluates how high the first relevant document was ranked.
For a single query, the reciprocal rank is 1 divided by the rank of the first relevant document.
If the first relevant document is at rank 3, the score is exactly 1/3.
MRR is the average of these individual reciprocal rank scores across all evaluated queries.
Normalized Discounted Cumulative Gain (NDCG@K) handles scenarios with multiple relevant documents.
It calculates Cumulative Gain, applying a logarithmic discount factor based on rank position.
It normalizes this by dividing by the Ideal DCG, representing a perfectly ranked list.
NDCG provides the most nuanced, comprehensive view of ranking quality in complex datasets.

## 15. How do you implement metadata filtering in Qdrant or Chroma to enforce row-level tenant isolation and role-based access control (RBAC) in a multi-tenant enterprise RAG system?
In multi-tenant systems, it is catastrophic if one client retrieves data belonging to another.
Metadata filtering in vector databases provides database-level security to enforce isolation.
During indexing, every document chunk must be strictly tagged with metadata payloads.
At a minimum, this payload must include a unique `tenant_id` for the owning organization.
For RBAC, it should also include an `allowed_roles` array or `clearance_level` tag.
When a user queries, the backend authenticates them and retrieves their `tenant_id` and roles.
The backend constructs a vector search request that explicitly includes a mandatory metadata filter.
In Qdrant, this uses the `Filter` construct with strict `must` match conditions.
The query specifies the system must only return vectors matching the user's `tenant_id`.
It also specifies the chunk's `allowed_roles` array must intersect with the user's roles.
The vector database evaluates these constraints before or during the vector similarity search.
This guarantees highly relevant documents are invisible if the user lacks metadata clearance.
This mechanism ensures absolute row-level data isolation and compliance across the enterprise.
