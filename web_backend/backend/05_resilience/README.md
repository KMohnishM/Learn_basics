# Module 5: Building Resilient Services

In a distributed system, failures are not exceptional — they are the normal operating condition. Networks drop. Databases slow down. Third-party APIs go down for hours. The question is not "will dependencies fail?" but "what happens to my service when they do?"

This module covers the patterns that prevent individual failures from becoming system-wide outages.

---

## 1. The Fallacies of Distributed Computing

Peter Deutsch's classic list of assumptions developers make that are always false:
1. The network is reliable
2. Latency is zero
3. Bandwidth is infinite
4. The network is secure
5. Topology doesn't change
6. There is one administrator
7. Transport cost is zero
8. The network is homogeneous

Every resilience pattern in this module exists to address one or more of these fallacies.

---

## 2. Timeouts — The Most Basic Resilience Tool

Every network call MUST have a timeout. A call without a timeout can hang forever, holding a thread/connection that can never serve other requests.

### Setting Timeouts in Python

```python
import httpx

# ❌ Wrong — can hang forever
response = httpx.get("https://slow-api.com/data")

# ✅ Correct — will raise httpx.TimeoutException after 5 seconds
response = httpx.get("https://slow-api.com/data", timeout=5.0)

# For fine-grained control:
timeout = httpx.Timeout(connect=2.0, read=5.0, write=3.0, pool=1.0)
response = httpx.get("https://slow-api.com/data", timeout=timeout)
```

### How to Choose Timeout Values

A common approach: measure the 99th percentile (p99) response time of the dependency under normal conditions, and set the timeout to 2-3x that value.

If the payment API normally responds in p50=200ms, p99=800ms, set your timeout to 2000ms. This allows for some slowness while still failing fast enough to be useful.

---

## 3. Retries with Exponential Backoff and Jitter

When a call fails due to a transient error (network blip, temporary overload), retrying immediately often makes things worse — you're hammering an already stressed service.

**Exponential Backoff**: Wait longer between each retry attempt.
- Attempt 1: wait 1 second
- Attempt 2: wait 2 seconds
- Attempt 3: wait 4 seconds
- Attempt 4: wait 8 seconds

**Jitter**: Add randomness to the wait time. Without jitter, if 1,000 clients all fail at the same time, they all retry at the same time (the "thundering herd"). Jitter spreads their retries out.

```python
import time
import random
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

@retry(
    stop=stop_after_attempt(4),                              # Max 4 attempts
    wait=wait_exponential(multiplier=1, min=1, max=10),      # 1s, 2s, 4s, 8s (with jitter built in)
    retry=retry_if_exception_type(httpx.TransientError),     # Only retry on transient errors
)
def call_payment_api(amount: float):
    response = httpx.post("https://payment.api/charge", json={"amount": amount}, timeout=5.0)
    response.raise_for_status()
    return response.json()
```

### What to Retry vs What Not to Retry

**Retry**: `500`, `502`, `503`, `504` (server errors, usually transient), `429` (rate limit — with Retry-After header!), network timeouts.

**Do NOT retry**: `400` (bad request — retrying won't fix malformed data), `401` (auth failure — retrying won't magically authenticate you), `404` (resource doesn't exist — retrying won't create it).

### Idempotency is Required for Safe Retries

If `POST /payments` creates a payment, and you retry after a network timeout (you don't know if the first attempt succeeded), you might create a duplicate payment. Always use idempotency keys on any non-idempotent operation you retry.

---

## 4. Circuit Breaker — Preventing Cascading Failures

Imagine Service A depends on Service B. Service B goes down. Without a circuit breaker:
1. Every request to Service A tries to call Service B
2. Each call waits for the timeout (e.g., 5 seconds)
3. Service A's thread pool fills up with requests waiting for timeouts
4. Service A runs out of threads to handle new requests
5. Service A also goes down
6. Service C, which depends on A, also goes down

This is a **cascading failure**. The Circuit Breaker prevents it.

### Circuit Breaker States

**CLOSED** (normal operation):
- Calls pass through
- Track the error rate over a rolling window (e.g., last 10 calls)
- If error rate exceeds threshold (e.g., 50%), TRIP to OPEN

**OPEN** (broken):
- All calls FAIL IMMEDIATELY without actually trying
- Set a recovery timer (e.g., 30 seconds)
- After timer expires, transition to HALF-OPEN

**HALF-OPEN** (testing recovery):
- Allow exactly one test call through
- If it succeeds → CLOSE (the dependency has recovered)
- If it fails → back to OPEN (still down, reset the timer)

```python
import time
from enum import Enum
from tenacity import stop_after_attempt, wait_exponential

class State(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=30, half_open_attempts=1):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_attempts = half_open_attempts
        
        self.state = State.CLOSED
        self.failures = 0
        self.last_failure_time = 0
        self.half_open_successes = 0

    def call(self, func, *args, **kwargs):
        if self.state == State.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = State.HALF_OPEN
                self.half_open_successes = 0
            else:
                raise RuntimeError(f"Circuit OPEN — fast failing. Wait {self.recovery_timeout}s")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        if self.state == State.HALF_OPEN:
            self.half_open_successes += 1
            if self.half_open_successes >= self.half_open_attempts:
                self.state = State.CLOSED
                self.failures = 0
        elif self.state == State.CLOSED:
            self.failures = max(0, self.failures - 1)

    def _on_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold or self.state == State.HALF_OPEN:
            self.state = State.OPEN
```

---

## 5. Bulkhead Pattern — Isolation Through Resource Partitioning

A bulkhead is a partition in a ship that prevents flooding in one compartment from sinking the whole ship.

In services: if all downstream calls share the same thread pool, one slow dependency exhausts the pool and starves all other operations.

```python
import concurrent.futures

# WRONG: One shared executor for everything
shared_executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)

# RIGHT: Separate executors (bulkheads) per dependency
payment_executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)    # Max 5 concurrent payment calls
inventory_executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)  # Max 5 concurrent inventory calls
email_executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)      # Max 3 email sends

# If the payment API slows down and fills payment_executor,
# inventory and email calls are completely unaffected
```

---

## 6. Graceful Degradation

When a dependency is unavailable, fail gracefully instead of failing completely.

```python
import redis
from functools import lru_cache

redis_client = redis.Redis()
payment_breaker = CircuitBreaker(failure_threshold=3)

def get_product_recommendations(user_id: str) -> list[str]:
    """
    Get recommendations — but gracefully degrade if the ML service is down.
    """
    try:
        # Try the ML recommendation engine first
        return payment_breaker.call(ml_service.get_recommendations, user_id)
    except Exception:
        # Fall back to cached recommendations from last successful run
        cached = redis_client.get(f"recommendations:{user_id}")
        if cached:
            return json.loads(cached)

        # Fall back to generic popular items
        return ["product_1", "product_2", "product_3"]  # Static fallback
```

---

## Next Steps

Go to `labs/` to build a service with multiple failing dependencies and demonstrate that Circuit Breakers prevent cascading failures!
