"""
Solution: LLM Cost Tracking System

Tracks per-user token consumption and USD cost in Redis.
Enforces spending limits and exposes an admin dashboard endpoint.
"""

from fastapi import FastAPI, HTTPException
import redis.asyncio as aioredis

app = FastAPI()
redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=True)

PRICING = {
    "gpt-4o":       {"input": 2.50,  "output": 10.00},
    "gpt-4o-mini":  {"input": 0.15,  "output": 0.60},
    "claude-haiku": {"input": 0.25,  "output": 1.25},
}

USER_COST_LIMIT_USD = 5.00


class CostTracker:
    def __init__(self, redis):
        self.redis = redis

    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        prices = PRICING.get(model, PRICING["gpt-4o-mini"])
        input_cost = (prompt_tokens / 1_000_000) * prices["input"]
        output_cost = (completion_tokens / 1_000_000) * prices["output"]
        return round(input_cost + output_cost, 8)

    async def record(self, user_id: str, model: str, prompt_tokens: int, completion_tokens: int):
        """Record usage and update running totals in Redis."""
        cost = self._calculate_cost(model, prompt_tokens, completion_tokens)

        async with self.redis.pipeline() as pipe:
            pipe.incrbyfloat(f"cost:user:{user_id}:total", cost)
            pipe.incr(f"cost:user:{user_id}:requests")
            pipe.incrbyfloat("cost:global:total", cost)
            pipe.sadd("cost:users", user_id)   # Track all seen users
            await pipe.execute()

        return cost

    async def get_user_cost(self, user_id: str) -> float:
        val = await self.redis.get(f"cost:user:{user_id}:total")
        return float(val or 0)

    async def check_limit(self, user_id: str) -> bool:
        """Returns True if user is within their limit."""
        cost = await self.get_user_cost(user_id)
        return cost < USER_COST_LIMIT_USD

    async def get_leaderboard(self, top_n: int = 10) -> list[dict]:
        user_ids = await self.redis.smembers("cost:users")
        leaderboard = []
        for uid in user_ids:
            cost = float(await self.redis.get(f"cost:user:{uid}:total") or 0)
            requests = int(await self.redis.get(f"cost:user:{uid}:requests") or 0)
            leaderboard.append({"user_id": uid, "cost_usd": round(cost, 4), "requests": requests})

        return sorted(leaderboard, key=lambda x: x["cost_usd"], reverse=True)[:top_n]


tracker = CostTracker(redis_client)


@app.post("/simulate_call")
async def simulate_call(user_id: str, model: str = "gpt-4o-mini",
                        prompt_tokens: int = 200, completion_tokens: int = 100):
    """Simulate an LLM call to test cost tracking."""
    # Check spending limit
    within_limit = await tracker.check_limit(user_id)
    if not within_limit:
        raise HTTPException(
            status_code=402,
            detail=f"Spending limit of ${USER_COST_LIMIT_USD:.2f} exceeded. Contact billing."
        )

    cost = await tracker.record(user_id, model, prompt_tokens, completion_tokens)
    total = await tracker.get_user_cost(user_id)
    return {"call_cost_usd": cost, "user_total_usd": round(total, 6)}


@app.get("/admin/costs")
async def cost_dashboard():
    global_total = float(await redis_client.get("cost:global:total") or 0)
    leaderboard = await tracker.get_leaderboard()
    return {
        "total_cost_usd": round(global_total, 4),
        "top_users": leaderboard,
    }
