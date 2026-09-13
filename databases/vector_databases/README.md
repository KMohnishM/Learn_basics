# Vector Databases & Semantic Search Curriculum

This curriculum provides a comprehensive, production-quality guide to understanding, building, and deploying vector databases and semantic search systems. It is designed for software engineers, machine learning practitioners, and data scientists who want to build robust Retrieval-Augmented Generation (RAG) applications and semantic search engines.

## Module Map

| Module | Key Topics | Difficulty |
|--------|------------|------------|
| **01_embeddings** | Vector spaces, embedding models, similarity metrics, chunking strategies | Beginner |
| **02_ann_algorithms** | kNN vs ANN, HNSW, IVF, PQ, SCaNN, latency vs recall | Advanced |
| **03_databases_compared**| pgvector, Pinecone, Qdrant, Weaviate, Chroma, Milvus architecture | Intermediate |
| **04_rag_integration** | End-to-end RAG, advanced retrieval (MMR, hybrid search), reranking | Intermediate |
| **05_production** | Capacity planning, multi-tenancy, metadata filtering, caching, monitoring | Advanced |

## Suggested Study Path

1. **Week 1:** Master embeddings and distance metrics (Module 01). Practice embedding texts and calculating similarities using NumPy.
2. **Week 2:** Understand the inner workings of Approximate Nearest Neighbors (Module 02). This is crucial for understanding database configuration.
3. **Week 3:** Evaluate and experiment with different vector databases (Module 03). Set up local instances using Docker.
4. **Week 4:** Build an end-to-end RAG pipeline with advanced retrieval techniques (Module 04).
5. **Week 5:** Learn productionization concepts, capacity planning, and operational best practices (Module 05).

**Estimated Total Time:** 40-50 hours of study and practical implementation.

## How to Practice

To get the most out of this curriculum, you should implement the code examples and run local instances of the databases.

### Python Environment Setup

Create a virtual environment and install the core dependencies:

```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Unix
source venv/bin/activate

pip install numpy pandas sentence-transformers openai cohere
pip install pinecone-client qdrant-client chromadb pymilvus psycopg2-binary pgvector
pip install langchain llamaindex ragas
```

### Local Database Setup (Docker)

**pgvector:**
```bash
docker run --name pgvector-container -e POSTGRES_PASSWORD=mysecretpassword -p 5432:5432 -d pgvector/pgvector:pg16
```

**Qdrant:**
```bash
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage:z \
    qdrant/qdrant
```

**Milvus (Standalone):**
Download the docker-compose.yml from Milvus docs and run:
```bash
wget https://github.com/milvus-io/milvus/releases/download/v2.3.0/milvus-standalone-docker-compose.yml -O docker-compose.yml
docker-compose up -d
```

### Vector Benchmark Tools

To understand performance trade-offs, explore the `ann-benchmarks` library, which provides standardized evaluations of various ANN algorithms across different datasets.
