# Vector Databases Cheatsheet

## 1. Feature Comparison Table

| Database | Architecture | Metadata Filtering | Hybrid Search | Primary Use Case |
| :--- | :--- | :--- | :--- | :--- |
| **pgvector** | PostgreSQL Extension | B-Tree / GIN / SQL | Custom via SQL | RDBMS integration, ACID, Joins |
| **Pinecone** | Managed SaaS | Single-stage | Native | High-scale, zero-ops production |
| **Qdrant** | Rust, gRPC/REST | Single-stage | Native (Sparse/Dense) | High-performance, self-hosted/cloud |
| **Weaviate** | Go, GraphQL | Post/Pre | Native (BM25) | Built-in embedding, complex schema |
| **Chroma** | Python/JS Embedded | Pre-filter | No | Local prototyping, basic RAG |
| **Milvus** | Distributed Cluster | Pre-filter | Native | Extreme scale (billions), enterprise |

---

## 2. pgvector SQL Cheat Code

```sql
-- Enable extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table
CREATE TABLE items (
    id serial PRIMARY KEY,
    embedding vector(3)
);

-- Insert vectors
INSERT INTO items (embedding) VALUES ('[1,2,3]'), ('[4,5,6]');

-- HNSW Index (Requires pgvector 0.5.0+)
-- Using cosine distance
CREATE INDEX ON items USING hnsw (embedding vector_cosine_ops);

-- IVFFlat Index (lists = rows / 1000)
CREATE INDEX ON items USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);

-- Nearest Neighbor Query (L2 distance)
SELECT id FROM items ORDER BY embedding <-> '[3,1,2]' LIMIT 5;

-- Nearest Neighbor Query (Cosine distance)
SELECT id, 1 - (embedding <=> '[3,1,2]') as similarity FROM items ORDER BY embedding <=> '[3,1,2]' LIMIT 5;
```

---

## 3. Python SDK Snippets

### Pinecone
```python
from pinecone import Pinecone, ServerlessSpec

# Initialize
pc = Pinecone(api_key="YOUR_API_KEY")

# Create Index
pc.create_index(
    name="quickstart",
    dimension=1536,
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)

index = pc.Index("quickstart")

# Upsert vectors with metadata and namespace
index.upsert(
    vectors=[
        {"id": "vec1", "values": [0.1, 0.2, 0.3], "metadata": {"genre": "drama"}}
    ],
    namespace="namespace1"
)

# Query with metadata filter
results = index.query(
    namespace="namespace1",
    vector=[0.1, 0.2, 0.3],
    top_k=3,
    include_values=True,
    include_metadata=True,
    filter={"genre": {"$eq": "drama"}}
)
```

### Qdrant
```python
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Initialize (In-memory for testing)
client = QdrantClient(":memory:")

# Create Collection
client.recreate_collection(
    collection_name="my_collection",
    vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE)
)

# Upsert (Insert)
client.upsert(
    collection_name="my_collection",
    points=[
        models.PointStruct(
            id=1,
            vector=[0.05, 0.61, 0.76],
            payload={"city": "Berlin"}
        )
    ]
)

# Query with Payload filter
hits = client.search(
    collection_name="my_collection",
    query_vector=[0.2, 0.1, 0.9],
    query_filter=models.Filter(
        must=[models.FieldCondition(key="city", match=models.MatchValue(value="Berlin"))]
    ),
    limit=3
)
```

### Chroma
```python
import chromadb

# Initialize local persistent client
client = chromadb.PersistentClient(path="./chroma_data")

# Get or create collection
collection = client.get_or_create_collection(
    name="my_collection",
    metadata={"hnsw:space": "cosine"} # l2, ip, or cosine
)

# Add documents (Chroma hashes documents to create embeddings if none provided, using default model)
collection.add(
    documents=["This is a document", "This is another document"],
    metadatas=[{"source": "my_source"}, {"source": "my_source"}],
    ids=["id1", "id2"],
    # vectors=[[0.1, 0.2], [0.3, 0.4]] # Alternatively provide own embeddings
)

# Query
results = collection.query(
    query_texts=["This is a query document"],
    n_results=2,
    where={"source": "my_source"} # Metadata filter
)
```
