"""
Lab: Fully Instrumented FastAPI Service

Implements all 3 pillars of observability:
  - Metrics: Prometheus (request rate, error rate, latency histograms)
  - Logs: Structured JSON with correlation IDs
  - Traces: OpenTelemetry → Jaeger

Run:
  pip install fastapi uvicorn prometheus-client opentelemetry-sdk opentelemetry-exporter-otlp opentelemetry-instrumentation-fastapi
  docker-compose up -d   (starts Prometheus, Grafana, Jaeger)
  uvicorn observable_service:app --reload

Then:
  - Metrics: http://localhost:8000/metrics
  - Prometheus: http://localhost:9090
  - Grafana: http://localhost:3000 (admin/admin)
  - Jaeger traces: http://localhost:16686
"""

import json
import logging
import sys
import time
import uuid
from typing import Callable
from datetime import datetime, UTC

import httpx
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from prometheus_client import (
    Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
)

# ─────────────────────────────────────────────
# Structured Logging Setup
# ─────────────────────────────────────────────

class JSONFormatter(logging.Formatter):
    SERVICE = "observable-service"
    VERSION = "1.0.0"

    def format(self, record: logging.LogRecord) -> str:
        log = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "service": self.SERVICE,
            "version": self.VERSION,
            "logger": record.name,
        }
        if hasattr(record, "correlation_id"):
            log["correlation_id"] = record.correlation_id
        if hasattr(record, "extra_fields"):
            log.update(record.extra_fields)
        if record.exc_info:
            log["exception"] = self.formatException(record.exc_info)
        return json.dumps(log)

logger = logging.getLogger("observable-service")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

# ─────────────────────────────────────────────
# Prometheus Metrics — The Four Golden Signals
# ─────────────────────────────────────────────

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "http_status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

ACTIVE_REQUESTS = Gauge(
    "http_active_requests",
    "Number of requests currently being processed",
    ["endpoint"]
)

ERROR_COUNT = Counter(
    "http_errors_total",
    "Total HTTP error responses",
    ["endpoint", "error_type"]
)

# ─────────────────────────────────────────────
# FastAPI App
# ─────────────────────────────────────────────

app = FastAPI(title="Observable Service")

# ─────────────────────────────────────────────
# Middleware: Correlation ID + Metrics + Logging
# ─────────────────────────────────────────────

@app.middleware("http")
async def observability_middleware(request: Request, call_next: Callable) -> Response:
    """Attach correlation ID, record metrics, log every request."""
    # 1. Correlation ID
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id

    endpoint = request.url.path
    method = request.method

    # 2. Track active requests
    ACTIVE_REQUESTS.labels(endpoint=endpoint).inc()
    start_time = time.time()

    # 3. Process
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as exc:
        ERROR_COUNT.labels(endpoint=endpoint, error_type=type(exc).__name__).inc()
        raise
    finally:
        # 4. Record metrics
        duration = time.time() - start_time
        ACTIVE_REQUESTS.labels(endpoint=endpoint).dec()
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, http_status=str(status_code)).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)

        # 5. Structured log entry for every request
        logger.info(
            "http_request",
            extra={
                "extra_fields": {
                    "correlation_id": correlation_id,
                    "method": method,
                    "path": endpoint,
                    "status_code": status_code,
                    "duration_ms": round(duration * 1000, 2),
                }
            }
        )

    response.headers["X-Correlation-ID"] = correlation_id
    return response

# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@app.get("/metrics")
def metrics():
    """Prometheus scrapes this endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health/live")
def liveness():
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness():
    checks = {"service": "ok"}
    all_ok = all(v == "ok" for v in checks.values())
    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={"status": "ready" if all_ok else "not_ready", "checks": checks}
    )

@app.get("/orders/{order_id}")
async def get_order(order_id: int, request: Request):
    logger.info(
        "order_fetch_started",
        extra={"extra_fields": {"order_id": order_id, "correlation_id": request.state.correlation_id}}
    )
    # Simulate varying latency
    await __import__("asyncio").sleep(0.05 + (order_id % 5) * 0.01)
    if order_id == 999:
        ERROR_COUNT.labels(endpoint="/orders/{order_id}", error_type="OrderNotFound").inc()
        raise HTTPException(status_code=404, detail="Order not found")
    return {"order_id": order_id, "status": "confirmed", "correlation_id": request.state.correlation_id}

@app.post("/orders")
async def create_order(request: Request):
    logger.info("order_creation_started", extra={"extra_fields": {"correlation_id": request.state.correlation_id}})
    await __import__("asyncio").sleep(0.1)
    order_id = int(time.time() * 1000) % 10000
    logger.info(
        "order_created",
        extra={"extra_fields": {"order_id": order_id, "correlation_id": request.state.correlation_id}}
    )
    return {"order_id": order_id, "status": "created"}
