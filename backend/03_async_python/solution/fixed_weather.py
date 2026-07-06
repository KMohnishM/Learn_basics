"""
Solution: Fixed Async Weather Service

Fixes:
  1. Replaced httpx.Client (sync) with httpx.AsyncClient (async)
  2. Cities fetched concurrently with asyncio.gather() in /report
  3. Added timing decorator for observability
"""

import time
import asyncio
import functools
import logging
import httpx
from fastapi import FastAPI

app = FastAPI()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

WEATHER_URL = "https://wttr.in/{city}?format=j1"

# ─────────────────────────────────────────────
# Timing Decorator
# ─────────────────────────────────────────────

def timed(func):
    """Log the execution time of an async endpoint."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = time.time() - start
        logger.info(f"{func.__name__} completed in {elapsed:.2f}s")
        return result
    return wrapper


# ─────────────────────────────────────────────
# Fixed Endpoints
# ─────────────────────────────────────────────

@app.get("/weather/{city}")
@timed
async def get_weather(city: str):
    # ✅ Use AsyncClient + await for non-blocking HTTP
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(WEATHER_URL.format(city=city))
    data = response.json()
    return {"city": city, "temp_c": data["current_condition"][0]["temp_C"]}


@app.get("/report")
@timed
async def get_report():
    cities = ["London", "Tokyo", "New York", "Mumbai", "Sydney"]

    # ✅ Fetch ALL cities concurrently — total time ≈ slowest single request
    async def fetch_city(city: str, client: httpx.AsyncClient) -> dict:
        response = await client.get(WEATHER_URL.format(city=city))
        temp = response.json()["current_condition"][0]["temp_C"]
        return {"city": city, "temp_c": temp}

    async with httpx.AsyncClient(timeout=10.0) as client:
        results = await asyncio.gather(*[fetch_city(city, client) for city in cities])

    return list(results)

# Run with: uvicorn fixed_weather:app --reload
# Compare: curl http://localhost:8000/report  (should be ~1s, not ~5s)
