"""
Lab: Benchmark Script — Shows the danger of blocking in async functions

Run this AFTER starting the server: uvicorn async_demo:app --workers 1

This script sends 10 concurrent requests to each endpoint and measures
total time. You'll see the dramatic difference between the three approaches.
"""

import asyncio
import httpx
import time


async def benchmark_endpoint(client: httpx.AsyncClient, url: str, n_requests: int = 10) -> float:
    """Send n_requests concurrently to the given URL. Returns total elapsed time."""
    start = time.time()
    tasks = [client.get(url) for _ in range(n_requests)]
    responses = await asyncio.gather(*tasks)
    elapsed = time.time() - start

    ok = all(r.status_code == 200 for r in responses)
    return elapsed, ok


async def main():
    BASE = "http://localhost:8000"
    N = 10

    print(f"Sending {N} concurrent requests to each endpoint...")
    print(f"Expected sequential time per request: 1 second")
    print(f"Expected concurrent time (correct async): ~1 second total\n")
    print(f"{'Endpoint':<25} {'Total Time':>12} {'Expected':>12}")
    print("-" * 52)

    async with httpx.AsyncClient(timeout=30.0) as client:
        for name, path, expected in [
            ("sync-blocking",  "/sync-blocking",  f"~{N/4:.0f}-{N}s (threads)"),
            ("async-broken",   "/async-broken",   f"~{N}s (serialized!)"),
            ("async-correct",  "/async-correct",  f"~1s (true concurrency)"),
        ]:
            elapsed, ok = await benchmark_endpoint(client, f"{BASE}{path}", N)
            print(f"{name:<25} {elapsed:>11.2f}s {expected:>12}")

    print("\n📝 Key Insight:")
    print("   async-broken takes ~10s because blocking the event loop serializes all requests.")
    print("   async-correct takes ~1s because await yields control, enabling true concurrency.")


if __name__ == "__main__":
    asyncio.run(main())
