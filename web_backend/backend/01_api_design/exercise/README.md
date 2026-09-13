# Exercise: Idempotent Payment API

## The Problem

You're building a payment processing endpoint:

```python
@app.post("/payments")
def process_payment(user_id: int, amount: float, currency: str):
    # Charge the user's credit card
    charge_id = stripe.charge(user_id, amount)
    db.save_payment(charge_id, user_id, amount)
    return {"charge_id": charge_id, "status": "success"}
```

This API has a critical bug: **it is not idempotent**.

If a client sends the payment request and the network drops before receiving the response, the client will retry. The user gets charged twice.

This is not a theoretical problem — it happens in production constantly.

## Your Task

Make the payment endpoint idempotent using an **Idempotency Key**.

Write `solution/idempotent_payment.py` (a FastAPI app) that:

1. Accepts an `Idempotency-Key` HTTP header on the `POST /payments` endpoint.
2. Before processing the payment, checks an in-memory dict (simulating a cache/DB) for the key.
3. If the key already exists → return the original response immediately (no duplicate charge).
4. If the key is new → process the payment (simulate with `uuid.uuid4()`), store the result with the key, return the response.
5. If the header is missing → return `400 Bad Request` with a clear error message.

## Expected Behavior

```bash
# First call — processes payment
curl -X POST /payments \
  -H "Idempotency-Key: abc-123" \
  -d '{"user_id": 1, "amount": 99.99}'
# → {"charge_id": "ch_xyz789", "status": "success", "idempotent": false}

# Retry with same key — returns same result, no double charge!
curl -X POST /payments \
  -H "Idempotency-Key: abc-123" \
  -d '{"user_id": 1, "amount": 99.99}'
# → {"charge_id": "ch_xyz789", "status": "success", "idempotent": true}
```
