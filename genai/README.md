# Generative AI Engineering — Complete Curriculum

A deeply practical, industry-level curriculum for engineers who want to build real Gen AI systems — not just call the OpenAI API. Every module includes in-depth theory, runnable labs, hands-on exercises, and full solutions.

---

## Who This Is For

- Backend/ML engineers who want to build **production-quality** LLM applications
- Engineers who want to go beyond demos and understand the internals
- Anyone preparing for GenAI engineering roles at companies using AI in production

---

## Curriculum Structure

Each module follows this structure:
```
module/
├── README.md       ← Deep-dive theory (the meat — read this first)
├── labs/           ← Runnable code you execute and study
├── exercise/       ← Problem to solve without looking at the solution
└── solution/       ← Reference implementation with explanations
```

---

## Modules

> **Note**: M3 (LangChain & Agents) and M5 (Vector Databases deep-dive) have dedicated folders elsewhere in this repo. Skip them here.

| # | Module | Core Skills | Key Labs |
|---|--------|-------------|----------|
| [M1](./01_foundations/) | **LLM Foundations** | Transformer architecture, tokenization, temperature, top-p, context windows | Token counter, temperature experimenter |
| [M2](./02_prompt_engineering/) | **Prompt Engineering** | Zero/Few-shot, CoT, Self-Consistency, ReAct, Structured Output, Prompt Injection | Evaluation harness (4 strategies), Self-consistency classifier |
| [M4](./04_rag/) | **RAG — Deep Internals** | Embeddings, pgvector, chunking strategies, hybrid search, reranking, HyDE, RAGAS | Complete RAG pipeline with pgvector, HyDE retrieval |
| [M6](./06_production_llm_api/) | **Production LLM APIs** | Async streaming (SSE), semantic caching, fallback chains, rate limiting, cost tracking | Streaming API with Redis cache & fallback, Cost tracker |
| [M7](./07_finetuning/) | **Fine-Tuning LLMs** | When to fine-tune, LoRA math, QLoRA, DPO vs RLHF, dataset quality | Synthetic dataset generator, DPO preference dataset |
| [M8](./08_evaluation_guardrails/) | **Evaluation & Guardrails** | RAGAS metrics, LLM-as-judge, input/output guardrails, prompt injection defense | Full eval pipeline, Safety wrapper for healthcare chatbot |

---

## Learning Path

### Week 1 — Foundations
Work through M1 → M2. Understand how LLMs work at a mechanistic level before building on top of them.

### Week 2 — RAG Systems
Deep-dive into M4. Build the full pipeline: ingest PDFs → chunk → embed → store in pgvector → retrieve → generate. Understand HyDE and why it works.

### Week 3 — Production APIs
M6 covers everything you need to take an LLM application to production: streaming, caching, fallbacks, rate limiting, cost control.

### Week 4 — Fine-Tuning
M7 covers when (and when NOT) to fine-tune. Learn LoRA math, prepare a dataset, and understand DPO.

### Week 5 — Evaluation & Safety
M8 completes the picture: how to measure quality systematically and prevent your LLM from going rogue in production.

---

## Prerequisites

```bash
pip install openai anthropic langchain langchain-openai psycopg2-binary redis numpy pydantic fastapi uvicorn httpx tenacity ragas datasets
```

Set your API key:
```bash
export OPENAI_API_KEY=sk-...
```

---

## Key Industry Tools Covered

| Tool | Purpose | Module |
|------|---------|--------|
| OpenAI SDK | LLM calls, embeddings, structured output | M1, M2, M4 |
| pgvector | Vector storage in Postgres | M4 |
| Redis | Semantic cache, rate limiting | M6 |
| FastAPI | Async streaming API | M6 |
| HuggingFace Transformers | Fine-tuning with LoRA/QLoRA | M7 |
| RAGAS | RAG evaluation framework | M8 |
| Guardrails AI | Input/output validation | M8 |

---

## Industry Context

The skills in this curriculum map directly to real engineering roles:

- **ML Engineer / LLM Engineer**: M1, M2, M4, M7
- **AI Product Engineer**: M1, M2, M4, M6
- **Backend Engineer (AI-adjacent)**: M2, M6, M8
- **MLOps / AI Platform**: M6, M7, M8
