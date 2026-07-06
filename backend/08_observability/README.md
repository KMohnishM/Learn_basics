# Module 8: Observability — Knowing What Your System Is Doing

Observability is the ability to understand the internal state of your system from its external outputs. A system without observability is a black box. When something breaks at 3am, you have three ways to understand what happened:

1. **Metrics**: Aggregated numbers over time (request rate, error rate, latency percentiles)
2. **Logs**: Discrete events with timestamps and context
3. **Traces**: The path a single request took through your entire system

These are the three pillars of observability. This module covers all three.

---

## 1. Structured Logging

Unstructured logs (plain text) are searchable with `grep` but don't scale. When you have 100 services generating 10,000 log lines per second, you need logs that are machine-parseable.

### Unstructured (Don't Do This)
```
2024-03-15 14:23:05 INFO User 42 placed order 1234 for $89.99
```
To find all orders over $100, you'd need a regex. To correlate with a user ID, you'd need string parsing.

### Structured (JSON Logs)
```json
{
  "timestamp": "2024-03-15T14:23:05Z",
  "level": "INFO",
  "event": "order_placed",
  "user_id": 42,
  "order_id": 1234,
  "amount_usd": 89.99,
  "trace_id": "abc123",
  "service": "order-service",
  "version": "2.3.1"
}
```
Now you can query: `amount_usd > 100 AND event = "order_placed"` — in Elasticsearch, Splunk, or DataDog in milliseconds.

### Python Structured Logging Setup

```python
import logging
import json
import sys
from datetime import datetime, UTC

class JSONFormatter(logging.Formatter):
    """Format log records as JSON."""
    
    def __init__(self, service: str, version: str):
        super().__init__()
        self.service = service
        self.version = version
    
    def format(self, record: logging.LogRecord) -> str:
        log_dict = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "service": self.service,
            "version": self.version,
            "logger": record.name,
        }
        # Include any extra fields passed to the logger
        if hasattr(record, "extra"):
            log_dict.update(record.extra)
        # Include exception info if present
        if record.exc_info:
            log_dict["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_dict)


def setup_logging(service: str, version: str) -> logging.Logger:
    logger = logging.getLogger(service)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter(service, version))
    logger.addHandler(handler)
    return logger

logger = setup_logging("order-service", "2.3.1")

# Usage:
# Don't: logger.info(f"User {user_id} placed order {order_id}")
# Do:
logger.info("order_placed", extra={"user_id": 42, "order_id": 1234, "amount_usd": 89.99})
```

---

## 2. Correlation IDs — Tracing a Request Across Logs

When a user's request touches 5 services (API gateway → auth → order → inventory → payment), the logs are scattered across 5 different log streams. Without a correlation ID, debugging a specific request means searching 5 systems independently.

A **correlation ID** (also called trace ID or request ID) is a random UUID generated at the edge (API gateway or the first service) and propagated through every service call as an HTTP header.

```python
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.base import BaseHTTPMiddleware

app = FastAPI()

class CorrelationIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Accept from upstream or generate a new one
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        
        # Attach to request state for use in this service
        request.state.correlation_id = correlation_id
        
        # Process the request
        response = await call_next(request)
        
        # Include in response headers so clients can reference it for support
        response.headers["X-Correlation-ID"] = correlation_id
        return response

app.add_middleware(CorrelationIDMiddleware)

@app.get("/orders/{order_id}")
async def get_order(order_id: int, request: Request):
    logger.info("order_fetched", extra={
        "order_id": order_id,
        "correlation_id": request.state.correlation_id,   # Every log includes this!
    })
    
    # When calling downstream services, pass the correlation ID forward
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://inventory.internal/items/{order_id}",
            headers={"X-Correlation-ID": request.state.correlation_id}
        )
    return response.json()
```

Now you can search your log aggregation system for `correlation_id = "abc-123"` and see the entire journey of that one request across all services.

---

## 3. Metrics with Prometheus

Prometheus is the de facto standard for metrics in cloud-native systems. Your application exposes a `/metrics` endpoint with data in a specific text format, and Prometheus scrapes it on a schedule.

### The Four Golden Signals (Google SRE Book)
1. **Latency**: How long requests take (measure p50, p95, p99)
2. **Traffic**: Request rate (requests per second)
3. **Errors**: Error rate (% of requests that fail)
4. **Saturation**: How full your system is (CPU %, memory %, queue depth)

### Prometheus Metric Types

**Counter**: Monotonically increasing count. Never decreases. Use for: total requests, total errors, total bytes sent.
```python
requests_total = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
requests_total.labels(method="GET", endpoint="/users", status="200").inc()
```

**Gauge**: A value that goes up and down. Use for: active connections, queue length, memory usage.
```python
active_connections = Gauge("active_connections", "Number of active WebSocket connections")
active_connections.inc()   # On connect
active_connections.dec()   # On disconnect
```

**Histogram**: Samples observations and counts them in configurable buckets. Use for: request latency, response sizes.
```python
request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)
# Usage in FastAPI middleware:
with request_duration.labels(endpoint="/users").time():
    response = await call_next(request)
```

---

## 4. Distributed Tracing with OpenTelemetry

Metrics tell you "something is slow." Logs tell you "this error happened." Traces tell you "THIS specific request hit THIS endpoint, then called THIS database query that took 4.2 seconds."

**OpenTelemetry** is the vendor-neutral standard for distributed tracing. Instruments automatically for FastAPI, SQLAlchemy, httpx, and more.

### Key Concepts

**Span**: A single unit of work (one function call, one HTTP request, one DB query). Has a start time, end time, and attributes.

**Trace**: A collection of spans linked together by a parent-child relationship. Shows the full tree of operations for one request.

**Span Attributes**: Key-value metadata on a span (`user.id`, `db.statement`, `http.status_code`).

```
Trace for request: POST /orders
├── [0ms - 250ms] POST /orders (FastAPI handler)
│   ├── [2ms - 45ms]  SELECT * FROM users WHERE id = 42 (SQLAlchemy)
│   ├── [50ms - 180ms] POST https://payment.api/charge (httpx)
│   │   └── [55ms - 175ms] stripe.charge() (Stripe SDK)
│   └── [185ms - 245ms] INSERT INTO orders (SQLAlchemy)
```

Without tracing, you'd see the 250ms latency in your metrics but have no idea which of the 3 operations caused it. Tracing pinpoints it instantly.

---

## 5. Health Checks

Every service should expose health check endpoints. Kubernetes (and load balancers) use these to decide whether to route traffic to an instance.

### Liveness vs Readiness vs Startup

**Liveness** (`/health/live`): "Is the process alive?" If this returns 500, Kubernetes kills and restarts the container.
```python
@app.get("/health/live")
def liveness():
    return {"status": "alive"}
```

**Readiness** (`/health/ready`): "Is the process ready to accept traffic?" If this returns 500, Kubernetes stops routing requests to this pod but doesn't restart it. Use for: warming up caches, waiting for DB migrations to complete.
```python
@app.get("/health/ready")
async def readiness():
    checks = {}
    
    # Check database connectivity
    try:
        await db.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"
    
    # Check Redis connectivity
    try:
        await redis.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"
    
    all_ok = all(v == "ok" for v in checks.values())
    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={"status": "ready" if all_ok else "not_ready", "checks": checks}
    )
```

---

## 6. SLIs, SLOs, and Error Budgets

**SLI (Service Level Indicator)**: A metric that measures your service quality.
- Request success rate: `(successful requests) / (total requests)`
- Latency p99: 99th percentile response time

**SLO (Service Level Objective)**: A target for your SLI.
- "99.9% of requests must succeed"
- "p99 latency must be below 500ms"

**Error Budget**: `100% - SLO = budget for failures`
- 99.9% SLO → 0.1% error budget
- Over 30 days → 43.8 minutes of downtime allowed

**Why this matters**: Error budgets give teams a clear, objective framework for trading off reliability vs velocity. If you've consumed 80% of your error budget in 10 days, you stop shipping features and focus on reliability.

---

## 7. Alerting — Alerting on Symptoms, Not Causes

The most common alerting mistake: alert on everything you can measure.

- CPU > 80% → alert
- Memory > 70% → alert
- 500 errors > 0 → alert

Result: Alert fatigue. Engineers stop responding because most alerts are false positives.

**The correct approach**: Alert on **symptoms** (things that hurt users) not causes.

**Good alerts** (user-impacting):
- Error rate > 1% for 5 minutes
- p99 latency > 2 seconds for 5 minutes
- Success rate drops below SLO

**Investigate, don't alert** (potential causes):
- CPU high (maybe fine if throughput is also high)
- Memory increasing (might be a cache filling up, not a leak)

---

## Next Steps

Go to `labs/` to instrument a FastAPI service with Prometheus metrics, structured JSON logging, correlation IDs, and health checks — then run Grafana to visualize the metrics!
