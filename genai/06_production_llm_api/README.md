# Module 6: Production LLM APIs

Building a demo that calls OpenAI is easy. Building a production LLM API that handles 10,000 users concurrently, controls costs, degrades gracefully when OpenAI goes down, and is observable when things go wrong — that requires a completely different set of engineering decisions.

---

## 1. Async is Not Optional at Scale

With a synchronous LLM call, one worker process handles one request at a time. An LLM response takes 2-5 seconds. If you have 100 concurrent users, you need 100 processes or threads — expensive and doesn't scale.

With async, one process can handle thousands of concurrent requests. While waiting for OpenAI to respond to request #1, the event loop processes requests #2 through #500.

```python
# ❌ WRONG: Synchronous — blocks the worker for 3 seconds per request
from openai import OpenAI
import fastapi

app = fastapi.FastAPI()
sync_client = OpenAI()

@app.get("/chat")
def chat(message: str):
    # This BLOCKS the thread! No other requests can be handled.
    response = sync_client.chat.completions.create(...)
    return {"reply": response.choices[0].message.content}

# ✅ CORRECT: Async — yields control while waiting
from openai import AsyncOpenAI

async_client = AsyncOpenAI()

@app.get("/chat")
async def chat(message: str):
    # This YIELDS to the event loop while waiting for OpenAI
    response = await async_client.chat.completions.create(...)
    return {"reply": response.choices[0].message.content}
```

**Rule**: Every LLM call in a FastAPI endpoint must use `AsyncOpenAI`, not `OpenAI`.

---

## 2. Streaming Responses

For a typical 300-token response, the user sees nothing for 3-5 seconds, then the full response appears. This feels unresponsive.

Streaming sends tokens to the user as they're generated. The first token appears in ~300ms. This dramatically improves perceived performance.

### Server-Sent Events (SSE)

The standard protocol for streaming from HTTP servers to browsers. One-way: server → client.

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI

app = FastAPI()
client = AsyncOpenAI()

async def generate_stream(message: str):
    """Async generator that yields SSE-formatted chunks."""
    stream = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": message}],
        stream=True,  # Enable streaming!
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            # SSE format: "data: {content}\n\n"
            yield f"data: {delta}\n\n"
    yield "data: [DONE]\n\n"

@app.get("/stream")
async def stream_chat(message: str):
    return StreamingResponse(
        generate_stream(message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

---

## 3. Semantic Caching — The Biggest Cost Lever

Many LLM applications receive very similar (not identical) queries repeatedly. A standard cache (Redis key = exact query string) won't help because "How do I reset my password?" and "What's the process for resetting a password?" are different strings but the same question.

**Semantic caching** embeds each incoming query and checks if a semantically similar query has been answered recently. If yes, return the cached response instantly.

```
User Query → Embed → Search cache (vector similarity)
  → If similarity > 0.95: Cache HIT → return cached response (free, <5ms)
  → If similarity < 0.95: Cache MISS → call LLM, store result in cache
```

**Cost impact**: In customer support applications, ~40-60% of queries are similar enough to benefit from semantic caching. At $10/1M tokens, this halves your LLM bill.

---

## 4. Fallback Strategy — Multi-Provider Reliability

OpenAI has outages. On March 13, 2024, the API was down for 2+ hours. If your entire product relies on one provider, every outage takes your product down with it.

**Fallback chain**: Define a priority list of models/providers. Try each in order until one succeeds.

```python
FALLBACK_CHAIN = [
    {"provider": "openai", "model": "gpt-4o-mini"},
    {"provider": "anthropic", "model": "claude-haiku-20240307"},
    {"provider": "ollama", "model": "llama3.2"},  # Local, always available
]

async def llm_with_fallback(messages: list, **kwargs) -> str:
    last_error = None
    for config in FALLBACK_CHAIN:
        try:
            response = await call_provider(config["provider"], config["model"], messages, **kwargs)
            return response
        except Exception as e:
            print(f"Provider {config['provider']} failed: {e}. Trying next...")
            last_error = e
    raise RuntimeError(f"All providers failed. Last error: {last_error}")
```

---

## 5. Per-User Rate Limiting & Token Budgets

Without rate limiting, a single automated client can run up $10,000 in API costs in minutes.

**Two levels of limiting**:
1. **Request rate limiting**: Max N requests per minute per user (Redis + sliding window)
2. **Token budget**: Max M tokens per user per day (track in database)

```python
import redis.asyncio as aioredis

redis = aioredis.from_url("redis://localhost:6379")

async def check_rate_limit(user_id: str, limit: int = 10, window_sec: int = 60) -> bool:
    """Sliding window rate limiter using Redis sorted sets."""
    import time
    now = time.time()
    window_start = now - window_sec
    key = f"rate_limit:{user_id}"

    pipe = redis.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)   # Remove old entries
    pipe.zcard(key)                                # Count remaining
    pipe.zadd(key, {str(now): now})               # Add current request
    pipe.expire(key, window_sec)                  # TTL
    results = await pipe.execute()

    request_count = results[1]
    return request_count < limit  # True = allowed
```

---

## 6. Observability — Logging Every LLM Call

When an LLM gives a bad response in production, you need to be able to:
- See the exact prompt that was sent
- See the exact response that was returned
- Know the model, temperature, and other parameters
- Track cost and latency for that specific call

**What to log for every LLM call**:
```python
{
    "timestamp": "2024-03-15T14:23:05Z",
    "user_id": "usr_abc123",
    "request_id": "req_xyz789",
    "model": "gpt-4o-mini",
    "prompt_tokens": 342,
    "completion_tokens": 89,
    "total_tokens": 431,
    "cost_usd": 0.0000647,
    "latency_ms": 1823,
    "temperature": 0.7,
    "cache_hit": false,
    "provider_used": "openai",   # Could be fallback
    "error": null
}
```

---

## 7. Prompt Versioning

As your product evolves, you'll iterate on system prompts constantly. Without versioning, you can't:
- Know which prompt version caused a regression
- Run A/B tests between prompt versions
- Roll back to a known-good prompt

**Simple approach**: Store prompts in a database/config file with a version number. Log the version with every LLM call.

```python
PROMPT_REGISTRY = {
    "support_bot_v1": "You are a helpful customer support agent for Acme Corp.",
    "support_bot_v2": "You are an expert customer support specialist for Acme Corp. Always be empathetic and solution-focused.",
    "support_bot_v3": "You are an expert customer support specialist for Acme Corp...",  # Latest
}

def get_prompt(name: str, version: str = "latest") -> tuple[str, str]:
    if version == "latest":
        # Find the highest version number
        matching = {k: v for k, v in PROMPT_REGISTRY.items() if k.startswith(name)}
        key = sorted(matching.keys())[-1]
    else:
        key = f"{name}_{version}"
    return PROMPT_REGISTRY[key], key  # Returns (prompt_text, version_key)
```

---

## Next Steps

Go to `labs/` to run a complete production LLM API with streaming, Redis semantic caching, rate limiting, and automatic fallback!
