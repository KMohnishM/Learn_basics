"""
Solution: Idempotent Payment API

Uses an in-memory store to cache responses keyed by the Idempotency-Key header.
In production, use Redis with a TTL of 24 hours.
"""

import uuid
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Idempotent Payment API")

# In production, this would be Redis with TTL
idempotency_store: dict[str, dict] = {}


class PaymentRequest(BaseModel):
    user_id: int
    amount: float
    currency: str = "USD"


def simulate_charge(user_id: int, amount: float) -> str:
    """Simulate a Stripe charge. Returns a unique charge ID."""
    return f"ch_{uuid.uuid4().hex[:12]}"


@app.post("/payments", status_code=200)
def process_payment(
    payload: PaymentRequest,
    idempotency_key: Optional[str] = Header(
        default=None,
        alias="Idempotency-Key",
        description="Unique key to prevent duplicate payments on retry"
    ),
):
    # 1. Reject requests without an idempotency key
    if not idempotency_key:
        raise HTTPException(
            status_code=400,
            detail="Missing required header: Idempotency-Key. "
                   "Generate a UUID and include it with every payment request."
        )

    # 2. Check if we've seen this key before
    if idempotency_key in idempotency_store:
        cached = idempotency_store[idempotency_key]
        # Return the original response, with a flag indicating it was deduplicated
        return {**cached, "idempotent": True}

    # 3. This is a new request — process the payment
    charge_id = simulate_charge(payload.user_id, payload.amount)

    response = {
        "charge_id": charge_id,
        "user_id": payload.user_id,
        "amount": payload.amount,
        "currency": payload.currency,
        "status": "success",
        "idempotent": False,
    }

    # 4. Store the response so retries return the same result
    # In production: redis.setex(idempotency_key, 86400, json.dumps(response))
    idempotency_store[idempotency_key] = response

    return response


# Run with: uvicorn solution:app --reload
# Test with:
#   curl -X POST http://localhost:8000/payments \
#        -H "Content-Type: application/json" \
#        -H "Idempotency-Key: test-key-001" \
#        -d '{"user_id": 1, "amount": 99.99}'
