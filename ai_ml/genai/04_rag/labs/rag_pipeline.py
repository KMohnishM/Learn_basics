"""
Lab: Complete RAG Pipeline with pgvector

Steps:
  1. Ingest documents → chunk → embed → store in pgvector
  2. Query → embed → search → rerank → generate answer

Prerequisites:
  pip install openai psycopg2-binary langchain langchain-openai langchain-community
  docker-compose up -d   (starts pgvector)
  export OPENAI_API_KEY=your_key
"""

import os
import psycopg2
import numpy as np
from openai import OpenAI

client = OpenAI()

# ─────────────────────────────────────────────
# Database Setup
# ─────────────────────────────────────────────

def get_conn():
    return psycopg2.connect(
        dbname="ragdb",
        user="raguser",
        password="ragpassword",
        host="localhost",
        port=5432,
    )

def setup_db():
    """Create the documents table with pgvector support."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            source TEXT,
            content TEXT,
            embedding vector(1536)
        );
    """)
    # HNSW index for fast approximate nearest neighbor search
    cur.execute("""
        CREATE INDEX IF NOT EXISTS docs_embedding_idx
        ON documents USING hnsw (embedding vector_cosine_ops);
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Database and vector index ready.")

# ─────────────────────────────────────────────
# Chunking
# ─────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> list[str]:
    """Recursive character splitter (simplified)."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks

# ─────────────────────────────────────────────
# Embedding
# ─────────────────────────────────────────────

def embed(text: str) -> list[float]:
    """Get embedding vector for a piece of text."""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return response.data[0].embedding

# ─────────────────────────────────────────────
# Ingestion
# ─────────────────────────────────────────────

SAMPLE_DOCUMENTS = [
    {
        "source": "python_docs",
        "content": """
Python is a high-level, general-purpose programming language. Its design philosophy emphasizes 
code readability with the use of significant indentation. Python is dynamically typed and 
garbage-collected. It supports multiple programming paradigms, including structured, 
object-oriented and functional programming. Python is often described as a "batteries included" 
language due to its comprehensive standard library.
        """
    },
    {
        "source": "ml_intro",
        "content": """
Machine learning is a subset of artificial intelligence that enables systems to learn and 
improve from experience without being explicitly programmed. ML focuses on developing computer 
programs that can access data and use it to learn for themselves. The primary aim is to allow 
computers to learn automatically without human intervention. Deep learning uses neural networks 
with many layers to model complex patterns in data.
        """
    },
    {
        "source": "rag_paper",
        "content": """
Retrieval-Augmented Generation (RAG) is an AI technique that combines information retrieval 
with text generation. Instead of relying solely on the LLM's parametric knowledge, RAG retrieves 
relevant documents from an external knowledge base and uses them as context for generation. 
This grounds the model's responses in factual, up-to-date information and reduces hallucination.
RAG systems typically use dense retrieval with vector embeddings to find semantically similar documents.
        """
    },
]

def ingest_documents(documents: list[dict]):
    """Chunk, embed, and store documents in pgvector."""
    conn = get_conn()
    cur = conn.cursor()

    total_chunks = 0
    for doc in documents:
        chunks = chunk_text(doc["content"].strip())
        for chunk in chunks:
            if not chunk.strip():
                continue
            embedding = embed(chunk)
            cur.execute(
                "INSERT INTO documents (source, content, embedding) VALUES (%s, %s, %s)",
                (doc["source"], chunk, embedding)
            )
            total_chunks += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Ingested {len(documents)} documents → {total_chunks} chunks stored.")

# ─────────────────────────────────────────────
# Retrieval
# ─────────────────────────────────────────────

def retrieve(query: str, top_k: int = 3) -> list[dict]:
    """Find the most semantically similar chunks for a query."""
    query_embedding = embed(query)

    conn = get_conn()
    cur = conn.cursor()

    # <=> is cosine distance in pgvector (lower = more similar)
    cur.execute("""
        SELECT id, source, content, 1 - (embedding <=> %s::vector) AS similarity
        FROM documents
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
    """, (query_embedding, query_embedding, top_k))

    results = [
        {"id": r[0], "source": r[1], "content": r[2], "similarity": round(r[3], 4)}
        for r in cur.fetchall()
    ]
    cur.close()
    conn.close()
    return results

# ─────────────────────────────────────────────
# Generation
# ─────────────────────────────────────────────

def generate_answer(query: str, context_chunks: list[dict]) -> str:
    """Generate an answer grounded in retrieved context."""
    context = "\n\n---\n\n".join(
        f"[Source: {c['source']} | Similarity: {c['similarity']}]\n{c['content']}"
        for c in context_chunks
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. Answer the user's question using ONLY "
                    "the provided context. If the answer is not in the context, say "
                    "'I don't have information about this in my knowledge base.'"
                )
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {query}"
            }
        ],
        temperature=0,
        max_tokens=500,
    )
    return response.choices[0].message.content

# ─────────────────────────────────────────────
# Full Pipeline Demo
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=== RAG Pipeline Demo ===\n")

    # 1. Setup
    setup_db()

    # 2. Ingest
    print("\n📥 Ingesting documents...")
    ingest_documents(SAMPLE_DOCUMENTS)

    # 3. Query
    queries = [
        "What is RAG and why does it reduce hallucinations?",
        "How does Python handle memory management?",
        "What is the difference between machine learning and deep learning?",
    ]

    for query in queries:
        print(f"\n{'='*60}")
        print(f"❓ Query: {query}")

        # Retrieve relevant chunks
        chunks = retrieve(query, top_k=3)
        print(f"\n📚 Retrieved {len(chunks)} chunks:")
        for c in chunks:
            print(f"  - [{c['source']}] Similarity: {c['similarity']:.4f}")

        # Generate grounded answer
        answer = generate_answer(query, chunks)
        print(f"\n💬 Answer:\n{answer}")
