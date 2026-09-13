# Exercise: Idempotent Retry with Tenacity

## The Problem

Your service sends emails via a third-party email provider (Mailgun, SendGrid). The API is flaky — it randomly times out.

Without retry logic: users don't get their emails.
With naive retry logic: users get the same email 3 times.

## Your Task

Write `solution/idempotent_email.py` that:

1. Uses the `tenacity` library to retry failed email sends with:
   - `stop_after_attempt(3)` — Maximum 3 attempts
   - `wait_exponential(multiplier=0.5, min=0.5, max=4)` — 0.5s, 1s, 2s waits
   - `retry_if_exception_type(ConnectionError)` — Only retry transient errors
   - NOT retrying on `ValueError` (e.g., invalid email address — retrying won't fix it)

2. Uses an idempotency key to prevent duplicate emails:
   - Before sending: check if `idempotency_key` exists in a dict (simulating Redis)
   - If yes: return `{"status": "already_sent", "idempotent": True}`
   - If no: attempt the send, store the result, return it

3. Simulates the flaky email API with a function that fails 60% of the time with `ConnectionError` but always succeeds if retried enough times.

**Expected behavior:**
```
call 1: attempt → fail → wait → retry → fail → wait → retry → success ✅
call 2 (same key): instant return without calling API (idempotent) ✅
call 3 (bad email): raise ValueError immediately, no retry ❌ (correctly)
```
