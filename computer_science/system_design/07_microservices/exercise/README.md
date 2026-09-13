# Exercise: Implement a Circuit Breaker

When Service A calls Service B, and Service B is completely down, Service A shouldn't keep trying and failing. It should "trip" a circuit breaker to fail instantly, saving resources and allowing Service B time to recover.

## Your Task

Implement a pure Python `CircuitBreaker` class in `solution/circuit_breaker.py`.

The class should wrap a function call and maintain three states:
1. **CLOSED**: The normal state. Calls pass through. If a call fails, increment an error counter. If the errors exceed `failure_threshold`, transition to OPEN.
2. **OPEN**: The broken state. All calls instantly raise an Exception without actually trying to execute the function. After a `recovery_timeout` has passed, transition to HALF-OPEN.
3. **HALF-OPEN**: Allow exactly *one* call to pass through as a test. If it succeeds, transition back to CLOSED. If it fails, go immediately back to OPEN.

### Boilerplate to start you off:

```python
import time

class CircuitBreakerOpenException(Exception):
    pass

class CircuitBreaker:
    def __init__(self, failure_threshold=3, recovery_timeout_sec=5):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        
        self.state = "CLOSED"
        self.failures = 0
        self.last_failure_time = None

    def call(self, func, *args, **kwargs):
        # YOUR LOGIC HERE
        pass
```

Write the full implementation in the solution folder!
