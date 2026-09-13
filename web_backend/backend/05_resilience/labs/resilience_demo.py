"""
Lab: Circuit Breaker + Bulkhead Demo

Shows how Circuit Breakers prevent cascading failures when a dependency goes down.

Run: pip install fastapi uvicorn tenacity
     uvicorn resilience_demo:app --reload
"""

import time
import random
from enum import Enum
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Resilience Patterns Demo")

# ─────────────────────────────────────────────
# Circuit Breaker Implementation
# ─────────────────────────────────────────────

class State(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 3, recovery_timeout: int = 10):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = State.CLOSED
        self.failures = 0
        self.last_failure_time = 0.0

    def call(self, func, *args, **kwargs):
        if self.state == State.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                print(f"  [CB:{self.name}] HALF-OPEN — testing recovery...")
                self.state = State.HALF_OPEN
            else:
                remaining = self.recovery_timeout - (time.time() - self.last_failure_time)
                raise RuntimeError(f"Circuit '{self.name}' is OPEN. Retry in {remaining:.1f}s")

        try:
            result = func(*args, **kwargs)
            if self.state == State.HALF_OPEN:
                print(f"  [CB:{self.name}] Recovery succeeded → CLOSED")
                self.state = State.CLOSED
                self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            if self.failures >= self.failure_threshold or self.state == State.HALF_OPEN:
                print(f"  [CB:{self.name}] Threshold reached → OPEN!")
                self.state = State.OPEN
            raise e

    @property
    def status(self) -> dict:
        return {
            "name": self.name,
            "state": self.state.value,
            "failures": self.failures,
        }

# ─────────────────────────────────────────────
# Mock Downstream Services
# ─────────────────────────────────────────────

payment_failure_rate = 0.0    # Control this via /control endpoint
inventory_failure_rate = 0.0

def call_payment_service() -> dict:
    if random.random() < payment_failure_rate:
        raise ConnectionError("Payment service is down!")
    time.sleep(0.05)
    return {"status": "charged", "amount": 99.99}

def call_inventory_service() -> dict:
    if random.random() < inventory_failure_rate:
        raise ConnectionError("Inventory service is down!")
    time.sleep(0.03)
    return {"status": "reserved", "sku": "PROD-001"}

# ─────────────────────────────────────────────
# Circuit Breakers per dependency
# ─────────────────────────────────────────────

payment_breaker = CircuitBreaker("payment", failure_threshold=3, recovery_timeout=10)
inventory_breaker = CircuitBreaker("inventory", failure_threshold=3, recovery_timeout=10)

# ─────────────────────────────────────────────
# API Endpoints
# ─────────────────────────────────────────────

@app.post("/order")
def place_order(user_id: int = 1):
    """
    Place an order — calls payment and inventory services.
    Without circuit breakers, one failing service can cascade to take down this endpoint.
    """
    errors = {}

    # Try payment (with circuit breaker)
    try:
        payment = payment_breaker.call(call_payment_service)
    except RuntimeError as e:
        errors["payment"] = str(e)   # Circuit open — fast fail
        payment = None
    except ConnectionError as e:
        errors["payment"] = str(e)   # Actual failure
        payment = None

    # Try inventory (with circuit breaker) — payment failure doesn't affect this!
    try:
        inventory = inventory_breaker.call(call_inventory_service)
    except RuntimeError as e:
        errors["inventory"] = str(e)
        inventory = None
    except ConnectionError as e:
        errors["inventory"] = str(e)
        inventory = None

    if errors:
        return {"success": False, "errors": errors, "partial": {"payment": payment, "inventory": inventory}}
    return {"success": True, "payment": payment, "inventory": inventory}

@app.get("/status")
def get_status():
    """See the current state of all circuit breakers."""
    return {
        "circuit_breakers": [
            payment_breaker.status,
            inventory_breaker.status,
        ]
    }

@app.post("/control")
def control_failure_rates(payment: float = 0.0, inventory: float = 0.0):
    """
    Control the failure rate of mock services (0.0 = never fail, 1.0 = always fail).
    Use this to simulate failures and watch the circuit breakers trip.
    """
    global payment_failure_rate, inventory_failure_rate
    payment_failure_rate = max(0.0, min(1.0, payment))
    inventory_failure_rate = max(0.0, min(1.0, inventory))
    return {"payment_failure_rate": payment_failure_rate, "inventory_failure_rate": inventory_failure_rate}

# ─────────────────────────────────────────────
# Demo Instructions (in comments)
# ─────────────────────────────────────────────
"""
1. Start server: uvicorn resilience_demo:app --reload
2. Normal operation: curl -X POST http://localhost:8000/order
3. Break payment: curl -X POST "http://localhost:8000/control?payment=1.0"
4. Watch breaker trip: curl -X POST http://localhost:8000/order  (repeat 3+ times)
5. Check status: curl http://localhost:8000/status
6. Notice: inventory still works even though payment is broken!
7. Fix payment: curl -X POST "http://localhost:8000/control?payment=0.0"
8. Wait 10 seconds for recovery timeout, then place another order — breaker heals.
"""
