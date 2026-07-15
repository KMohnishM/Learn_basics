# Exercise: Cost Tracking Dashboard

## Background

Your LLM API is live and serving thousands of users. The engineering team asks: "How much did we spend on OpenAI this week, and which users are driving the most costs?"

You realize you're logging requests but not tracking token costs systematically.

## Your Task

Extend the production API with a cost tracking system. Create `solution/cost_tracker.py` with:

1. A `CostTracker` class that:
   - Accepts `(user_id, model, prompt_tokens, completion_tokens)` per call
   - Stores cumulative cost per user in Redis
   - Calculates cost using the pricing table:
     ```python
     PRICING = {
         "gpt-4o":      {"input": 2.50, "output": 10.00},   # per 1M tokens
         "gpt-4o-mini": {"input": 0.15, "output": 0.60},
         "claude-haiku": {"input": 0.25, "output": 1.25},
     }
     ```

2. A `GET /admin/costs` endpoint that returns a leaderboard:
   ```json
   {
     "total_cost_usd": 12.45,
     "top_users": [
       {"user_id": "alice", "cost_usd": 4.23, "requests": 142},
       {"user_id": "bob", "cost_usd": 3.11, "requests": 89}
     ]
   }
   ```

3. A per-user cost limit: if a user exceeds $5.00 total spend, all their subsequent requests get a `402 Payment Required` response.

This is exactly how platforms like LangSmith, Helicone, and OpenMeter work under the hood.
