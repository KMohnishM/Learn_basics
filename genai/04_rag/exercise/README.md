# Exercise: HyDE — Hypothetical Document Embeddings

## The Problem

You're building a RAG system for a legal document corpus. A user asks:

> "Can a landlord enter the property without notice?"

The actual relevant clause in your documents reads:

> "The lessor shall provide a minimum of 24 hours written notice prior to entry of the leased premises, except in cases of emergency."

Notice the vocabulary gap:
- The user says "landlord", the document says "lessor".
- The user says "without notice", the document says "24 hours written notice".

Standard vector search may rank this document poorly because the embeddings of the question and the answer are in different semantic spaces (question space vs. answer space).

## The HyDE Technique

Instead of embedding the question, use an LLM to generate a **hypothetical answer** to the question, and embed that instead. The hypothetical answer will naturally use vocabulary similar to the actual document.

## Your Task

Write `solution/hyde_rag.py` that wraps any retrieval function with the HyDE technique:

1. Take the original user query.
2. Ask GPT-4o-mini to write a **2-sentence hypothetical answer** to the query.
3. Embed the hypothetical answer (not the original query).
4. Use that embedding to retrieve from the vector store.
5. Return the retrieved documents + show the hypothetical answer that was used.

Compare retrieval quality with and without HyDE by printing the similarity scores side by side.

**Hint**: The hypothetical answer doesn't need to be factually correct — it just needs to be *stylistically* similar to the real documents so that the embeddings align.
