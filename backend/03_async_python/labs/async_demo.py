"""
Lab: Async vs Sync FastAPI — Demonstrating the Blocking Problem

This lab has THREE versions of the same endpoint:
  1. /sync-blocking  — Synchronous endpoint with a blocking sleep
  2. /async-broken   — Async endpoint with a blocking sleep (WRONG!)
  3. /async-correct  — Async endpoint with a non-blocking sleep (RIGHT!)

Run: pip install fastapi uvicorn httpx
     uvicorn async_demo:app --workers 1 --reload

Then in another terminal:
     python benchmark.py
"""

import time
import asyncio
from fastapi import FastAPI

app = FastAPI(title="Async vs Sync Demo")

# ─────────────────────────────────────────────
# VERSION 1: Synchronous (FastAPI runs in thread pool — blocking is OK)
# ─────────────────────────────────────────────

@app.get("/sync-blocking")
def sync_blocking():
    """
    FastAPI puts sync endpoints in a thread pool.
    Blocking here doesn't block the event loop.
    Other requests can still be served by other threads.
    """
    time.sleep(1)   # Simulates 1 second DB query
    return {"endpoint": "sync", "latency": "1s per request, but concurrent"}


# ─────────────────────────────────────────────
# VERSION 2: Async with blocking call (WRONG!)
# ─────────────────────────────────────────────

@app.get("/async-broken")
async def async_broken():
    """
    ❌ WRONG: Blocking call inside async function!

    time.sleep() holds the event loop hostage.
    While this endpoint is sleeping, ZERO other requests are served.
    Under concurrency, this is catastrophic.
    """
    time.sleep(1)   # BLOCKS THE EVENT LOOP! Never do this!
    return {"endpoint": "async-broken", "latency": "1s per request, AND blocks all others"}


# ─────────────────────────────────────────────
# VERSION 3: Async with non-blocking call (RIGHT!)
# ─────────────────────────────────────────────

@app.get("/async-correct")
async def async_correct():
    """
    ✅ CORRECT: Non-blocking wait yields to event loop.

    asyncio.sleep() suspends this coroutine and lets other requests run.
    100 concurrent requests all "sleep" simultaneously, returning in ~1s total.
    """
    await asyncio.sleep(1)   # Non-blocking! Event loop serves other requests.
    return {"endpoint": "async-correct", "latency": "1s, but truly concurrent"}


# ─────────────────────────────────────────────
# Concurrent Requests Demo
# ─────────────────────────────────────────────

@app.get("/demo/concurrent-gather")
async def concurrent_gather():
    """
    Show the difference between sequential and concurrent I/O.
    """
    # Sequential: 3 seconds total
    start = time.time()
    await asyncio.sleep(1)
    await asyncio.sleep(1)
    await asyncio.sleep(1)
    sequential_time = time.time() - start

    # Concurrent: 1 second total (all three run simultaneously)
    start = time.time()
    await asyncio.gather(
        asyncio.sleep(1),
        asyncio.sleep(1),
        asyncio.sleep(1),
    )
    concurrent_time = time.time() - start

    return {
        "sequential_time_seconds": round(sequential_time, 2),
        "concurrent_time_seconds": round(concurrent_time, 2),
        "speedup": f"{sequential_time / concurrent_time:.1f}x"
    }
