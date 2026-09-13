"""
Lab: Production LLM API

Features:
  - Async streaming (SSE)
  - Redis-based rate limiting (10 req/min per user)
  - In-memory semantic cache (cosine similarity > 0.95 → cache hit)
  - Automatic fallback to Ollama when OpenAI fails
  - Structured observability logging for every call

Run:
  pip install fastapi uvicorn openai redis numpy httpx
  docker-compose up -d   (starts Redis)
  export OPENAI_API_KEY=your_key
  uvicorn production_llm_api:app --reload

Test streaming:
  curl -N "http://localhost:8000/chat?user_id=alice&message=What+is+RAG?"
"""

import time
import json
import uuid
import logging
import numpy as np
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI, APIError
import redis.asyncio as aioredis

# ─────────────────────────────────────────────
# Setup
# ─────────────────────────────────────────────

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Production LLM API")

openai_client = AsyncOpenAI()
# Ollama uses the OpenAI-compatible API on port 11434
ollama_client = AsyncOpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=True)

# ─────────────────────────────────────────────
# Semantic Cache (In-Memory for this lab)
# In production: store embeddings in Redis with vector similarity
# ─────────────────────────────────────────────

semantic_cache: list[dict] = []  # List of {embedding, response}
CACHE_SIMILARITY_THRESHOLD = 0.95

async def get_embedding(text: str) -> list[float]:
    resp = await openai_client.embeddings.create(
        model="text-embedding-3-small", input=text
    )
    return resp.data[0].embedding

def cosine_similarity(a: list[float], b: list[float]) -> float:
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

async def cache_lookup(query: str) -> str | None:
    if not semantic_cache:
        return None
    q_emb = await get_embedding(query)
    for entry in semantic_cache:
        sim = cosine_similarity(q_emb, entry["embedding"])
        if sim >= CACHE_SIMILARITY_THRESHOLD:
            logger.info(f"CACHE HIT (similarity={sim:.4f})")
            return entry["response"]
    return None

async def cache_store(query: str, response: str):
    q_emb = await get_embedding(query)
    semantic_cache.append({"embedding": q_emb, "response": response, "query": query})

# ─────────────────────────────────────────────
# Rate Limiter (Sliding Window via Redis)
# ─────────────────────────────────────────────

RATE_LIMIT = 10    # requests
RATE_WINDOW = 60   # seconds

async def check_rate_limit(user_id: str) -> bool:
    now = time.time()
    window_start = now - RATE_WINDOW
    key = f"rate:{user_id}"

    async with redis_client.pipeline() as pipe:
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, RATE_WINDOW)
        results = await pipe.execute()

    count = results[1]
    return count < RATE_LIMIT

# ─────────────────────────────────────────────
# LLM Caller with Fallback
# ─────────────────────────────────────────────

async def call_llm_stream(message: str) -> tuple[AsyncGenerator, str]:
    """Try OpenAI first, fall back to local Ollama on failure."""
    try:
        stream = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": message}],
            stream=True,
        )
        return stream, "openai/gpt-4o-mini"
    except APIError as e:
        logger.warning(f"OpenAI failed ({e}), falling back to Ollama...")
        stream = await ollama_client.chat.completions.create(
            model="llama3.2",
            messages=[{"role": "user", "content": message}],
            stream=True,
        )
        return stream, "ollama/llama3.2"

# ─────────────────────────────────────────────
# Main Endpoint
# ─────────────────────────────────────────────

@app.get("/chat")
async def chat(
    message: str = Query(..., description="Your message"),
    user_id: str = Query(..., description="User identifier for rate limiting"),
):
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    # 1. Rate limit check
    allowed = await check_rate_limit(user_id)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {RATE_LIMIT} requests per {RATE_WINDOW}s.",
            headers={"Retry-After": str(RATE_WINDOW)},
        )

    # 2. Semantic cache lookup
    cached = await cache_lookup(message)
    if cached:
        log_entry = {
            "request_id": request_id, "user_id": user_id,
            "cache_hit": True, "latency_ms": int((time.time() - start_time) * 1000)
        }
        logger.info(json.dumps(log_entry))

        async def cached_stream():
            yield f"data: {cached}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(cached_stream(), media_type="text/event-stream")

    # 3. Stream from LLM with fallback
    async def generate():
        full_response = ""
        stream, provider = await call_llm_stream(message)

        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                full_response += delta
                yield f"data: {delta}\n\n"

        yield "data: [DONE]\n\n"

        # Store in semantic cache for future similar queries
        await cache_store(message, full_response)

        # Observability log
        log_entry = {
            "request_id": request_id, "user_id": user_id,
            "provider": provider, "cache_hit": False,
            "latency_ms": int((time.time() - start_time) * 1000),
        }
        logger.info(json.dumps(log_entry))

    return StreamingResponse(generate(), media_type="text/event-stream")
