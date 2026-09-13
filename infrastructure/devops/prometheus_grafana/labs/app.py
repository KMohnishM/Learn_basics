"""
Guided Lab: Instrumenting a Python App with Prometheus

This app demonstrates all four Prometheus metric types:
- Counter: Total request count
- Gauge: Number of active in-flight requests  
- Histogram: Request duration (for p95/p99 latency)
- Summary: (Shown for comparison, but Histogram is preferred)

Run this app with:
    pip install flask prometheus_client
    python app.py

Then visit:
    http://localhost:5000/       -> Normal endpoint
    http://localhost:5000/slow   -> Simulates a slow response
    http://localhost:5000/error  -> Simulates an error
    http://localhost:5000/metrics -> What Prometheus will scrape!
"""

import time
import random
from flask import Flask, Response
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

app = Flask(__name__)

# ==============================================================================
# 1. DEFINE YOUR METRICS
# ==============================================================================

# Counter: Monotonically increasing. Use for things that only go UP.
REQUEST_COUNT = Counter(
    "http_requests_total",                        # Metric name
    "Total number of HTTP requests received",     # Help text
    ["method", "endpoint", "status_code"],        # Labels for filtering
)

# Gauge: Can go up or down. Snapshot of current state.
IN_PROGRESS_REQUESTS = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently being processed",
)

# Histogram: Records the distribution of values across buckets.
# This is how you measure API latency properly (enables p95, p99 queries).
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["endpoint"],
    # Define the buckets. Values here are in SECONDS.
    # A request goes into a bucket if it's <= that bucket's value.
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

# ==============================================================================
# 2. INSTRUMENT YOUR ROUTES
# ==============================================================================

@app.route("/")
def home():
    start_time = time.time()
    
    # Increment the in-progress gauge BEFORE doing work
    IN_PROGRESS_REQUESTS.inc()
    
    try:
        # Simulate some work
        time.sleep(random.uniform(0.01, 0.1))
        
        # Increment the counter with specific label values
        REQUEST_COUNT.labels(method="GET", endpoint="/", status_code=200).inc()
        
        return {"message": "Hello! Check /metrics to see your instrumentation."}
    finally:
        # ALWAYS decrement the gauge after work is done (even on error)
        IN_PROGRESS_REQUESTS.dec()
        
        # Record the latency in the histogram
        duration = time.time() - start_time
        REQUEST_LATENCY.labels(endpoint="/").observe(duration)


@app.route("/slow")
def slow_endpoint():
    """Simulates a slow endpoint - great for demonstrating histogram p99."""
    start_time = time.time()
    IN_PROGRESS_REQUESTS.inc()

    try:
        # Simulate a slow operation (500ms - 2 seconds)
        time.sleep(random.uniform(0.5, 2.0))
        REQUEST_COUNT.labels(method="GET", endpoint="/slow", status_code=200).inc()
        return {"message": "That was slow!"}
    finally:
        IN_PROGRESS_REQUESTS.dec()
        duration = time.time() - start_time
        REQUEST_LATENCY.labels(endpoint="/slow").observe(duration)


@app.route("/error")
def error_endpoint():
    """Simulates an error - great for demonstrating error rate queries."""
    start_time = time.time()
    IN_PROGRESS_REQUESTS.inc()

    try:
        time.sleep(random.uniform(0.01, 0.05))
        # Record the error status code in the counter label
        REQUEST_COUNT.labels(method="GET", endpoint="/error", status_code=500).inc()
        return {"error": "Something went wrong!"}, 500
    finally:
        IN_PROGRESS_REQUESTS.dec()
        duration = time.time() - start_time
        REQUEST_LATENCY.labels(endpoint="/error").observe(duration)


# ==============================================================================
# 3. EXPOSE THE /metrics ENDPOINT FOR PROMETHEUS TO SCRAPE
# ==============================================================================

@app.route("/metrics")
def metrics():
    """
    This is the endpoint Prometheus will hit every scrape_interval seconds.
    generate_latest() converts all registered metrics into the Prometheus
    plain-text exposition format.
    """
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    print("Starting instrumented Flask app on http://localhost:5000")
    print("Prometheus metrics available at: http://localhost:5000/metrics")
    app.run(host="0.0.0.0", port=5000, debug=True)
