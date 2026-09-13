# Exercise: Fix the Async Bug

## The Code

Your team inherited this FastAPI service. Users are complaining it feels slow during peak hours, even though each request is only supposed to take 100ms.

```python
import httpx
import time
from fastapi import FastAPI

app = FastAPI()
sync_http_client = httpx.Client()  # ← Synchronous client

@app.get("/weather/{city}")
async def get_weather(city: str):
    # Calls external weather API
    response = sync_http_client.get(f"https://wttr.in/{city}?format=j1")
    return {"city": city, "temp": response.json()["current_condition"][0]["temp_C"]}

@app.get("/report")
async def get_report():
    cities = ["London", "Tokyo", "New York", "Mumbai", "Sydney"]
    results = []
    for city in cities:
        response = sync_http_client.get(f"https://wttr.in/{city}?format=j1")
        temp = response.json()["current_condition"][0]["temp_C"]
        results.append({"city": city, "temp": temp})
    return results
```

## The Problems

1. `httpx.Client()` is a **synchronous** client. Using it inside `async def` blocks the event loop.
2. The `/report` endpoint fetches 5 cities **sequentially**. Even after fixing the sync issue, it's still slower than it needs to be.

## Your Task

Fix both bugs in `solution/fixed_weather.py`:

1. Replace `httpx.Client` with `httpx.AsyncClient` and use `await` for all HTTP calls.
2. In `/report`, fetch all 5 cities **concurrently** using `asyncio.gather()`.
3. Add a timing decorator that logs how long each endpoint takes.

**Expected improvement**: `/report` should go from ~5 seconds to ~1 second.

Note: `wttr.in` is a free, no-key-needed weather API. Use it for real!
