# Module 5: Distributed Tracing and Observability

## 1. Why Observability in Microservices Is Hard

In a monolithic application, debugging is relatively straightforward. When an error occurs, you have a single log file, a single unified call stack, and a single database transaction. 

In a microservices architecture, a single user request (e.g., `POST /checkout`) might traverse 10 to 15 different services across network boundaries. 
- A failure in the `Order Service` might actually be caused by high latency in the `Inventory Service`.
- The `Inventory Service` might be slow because of a locked row in its database.
- Finding this root cause requires piecing together isolated logs from multiple distinct systems running in different containers, potentially written in different languages.

To solve this, we rely on the **Three Pillars of Observability**:
1. **Logs**: Discrete events with context and timestamps (What happened?).
2. **Metrics**: Aggregated numerical data over time (How much/How fast?).
3. **Traces**: Request-scoped causality tracking across boundaries (Why did it happen?).

---

## 2. Distributed Tracing Concepts

Distributed tracing allows developers to track the lifecycle of a request as it hops across microservice boundaries.

### Visualizing a Trace
```text
User Request: POST /orders
|
|-- [Trace ID: abc123]
    |
    |-- [Span: order-service.create_order] (Total: 45ms)
        |
        |-- [Span: inventory-service.check_stock] (12ms)
        |   (parent_span_id: create_order)
        |
        |-- [Span: inventory-service.reserve_stock] (8ms)
        |
        |-- [Span: payment-service.charge] (18ms)
        |   |
        |   |-- [Span: stripe-api.charge] (15ms)
        |       (external call via HTTP)
        |
        |-- [Span: kafka.publish.OrderPlaced] (2ms)
```

### Core Terminology
- **Trace**: The complete end-to-end journey of a single request across the distributed system.
- **Span**: A single unit of work within a trace (e.g., an HTTP request, a DB query, an internal function).
- **Trace ID**: A globally unique identifier assigned at the API Gateway and propagated to every downstream service.
- **Span ID**: A unique identifier for a specific operation.
- **Parent Span ID**: The ID of the span that triggered the current span. This creates the hierarchical tree structure.
- **Span Attributes**: Key-value pairs attached to a span providing business context (e.g., `user.id=99`, `order.total=150.00`).
- **Baggage**: Key-value pairs that are propagated alongside the Trace ID to all downstream services (e.g., passing a tenant ID through the whole system).

---

## 3. OpenTelemetry (OTel) — The Standard

Historically, organizations used vendor-specific SDKs (Datadog, New Relic) to instrument their code. This created severe vendor lock-in. 

**OpenTelemetry** is a CNCF project that standardizes telemetry data generation. 
- **Vendor-neutral**: You instrument your code once using OTel libraries. You can then route that data to any backend (Jaeger, Prometheus, Datadog) without changing application code.
- **Unifies Signals**: It handles traces, metrics, and logs under one API.
- **Auto-instrumentation**: It can automatically wrap popular libraries (FastAPI, Express, SQLAlchemy) without manual coding.

### Python OTel Setup (FastAPI & SQLAlchemy)

```python
import os
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource

# 1. Configure the Resource (who is emitting the telemetry)
resource = Resource.create({
    'service.name': 'order-service',
    'service.version': '2.1.0',
    'deployment.environment': os.getenv('ENV', 'production')
})

# 2. Configure the Exporter (where to send the telemetry)
exporter = OTLPSpanExporter(endpoint='http://otel-collector:4317')
provider = TracerProvider(resource=resource)
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)

app = FastAPI()

# 3. Auto-instrument frameworks and clients
FastAPIInstrumentor.instrument_app(app)
# SQLAlchemyInstrumentor().instrument(engine=engine)
HTTPXClientInstrumentor().instrument()

# 4. Manual Span Creation for Business Logic
tracer = trace.get_tracer(__name__)

async def process_order(order_data: dict) -> dict:
    # Start a custom span representing a logical block of work
    with tracer.start_as_current_span('business_logic.process_order') as span:
        # Add rich business context for searching in Jaeger
        span.set_attribute('order.customer_id', order_data.get('customer_id'))
        span.set_attribute('order.item_count', len(order_data.get('items', [])))
        
        try:
            # Simulate DB work
            result = {"status": "success", "id": 123}
            span.set_status(trace.StatusCode.OK)
            return result
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            raise
```

---

## 4. Context Propagation (W3C TraceContext)

For tracing to work, the Trace ID must be passed over the network from Service A to Service B. The industry standard is the W3C TraceContext specification, which uses specific HTTP headers.

Header Example:
`traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`
Format: `version`-`trace_id`-`parent_span_id`-`flags`

### Manual Propagation (If auto-instrumentation fails)

```python
import requests
from opentelemetry import propagate

def make_downstream_call(url: str, payload: dict) -> dict:
    headers = {}
    # Inject the current trace context into the HTTP headers dict
    propagate.inject(headers)  
    
    # The headers will now contain 'traceparent'
    response = requests.post(url, json=payload, headers=headers)
    return response.json()
```

---

## 5. The OpenTelemetry Collector

The OTel Collector is a proxy deployed in your cluster (usually as a DaemonSet). Instead of applications sending data directly to Datadog or Jaeger, they send it to the local Collector. The Collector processes, batches, and routes the data.

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 1s
    send_batch_size: 1024
  memory_limiter:
    check_interval: 1s
    limit_mib: 512
  # Append cluster-level metadata to all incoming spans
  resource:
    attributes:
    - action: upsert
      key: cluster.name
      value: production-us-east-1

exporters:
  jaeger:
    endpoint: jaeger-collector:14250
    tls:
      insecure: true
  prometheus:
    endpoint: 0.0.0.0:8889

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch, resource]
      exporters: [jaeger]
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [prometheus]
```

---

## 6. Prometheus Metrics in Microservices

Metrics provide a high-level view of system health. Prometheus is a pull-based monitoring system.

### Metric Types
- **Counter**: Only goes up (e.g., total HTTP requests).
- **Gauge**: Can go up and down (e.g., current active orders, CPU usage).
- **Histogram**: Samples observations into buckets (e.g., request latency).

### Implementing Metrics in Python

```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import FastAPI, Request, Response
import time

app = FastAPI()

# Define Metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

ACTIVE_DB_CONNECTIONS = Gauge(
    'db_connections_active',
    'Current active database connections'
)

@app.middleware('http')
async def prometheus_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    # Record metrics
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code
    ).inc()

    return response

# Prometheus scrapes this endpoint
@app.get('/metrics')
def expose_metrics():
    return Response(content=generate_latest(), media_type='text/plain')
```

---

## 7. Grafana Dashboards and PromQL

Grafana visualizes Prometheus data. PromQL is the query language.

### Essential PromQL Queries (The RED Method)

**1. Rate (Traffic)**: Requests per second over the last 5 minutes.
```promql
sum(rate(http_requests_total{service="order-service"}[5m])) by (endpoint)
```

**2. Errors**: Percentage of 5xx errors.
```promql
sum(rate(http_requests_total{status_code=~"5..", service="order-service"}[5m])) 
/ 
sum(rate(http_requests_total{service="order-service"}[5m]))
```

**3. Duration (Latency)**: 99th percentile (P99) latency.
```promql
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{service="order-service"}[5m])) by (le, endpoint))
```

---

## 8. Structured Logging (JSON)

Plain text logs (`"User 123 logged in"`) are impossible to query at scale. Structured logging outputs JSON, allowing central log aggregators (Elasticsearch, Loki) to index fields efficiently.

### Linking Logs to Traces

Crucially, every log line must contain the `trace_id`. This allows you to jump from a trace in Jaeger directly to the specific logs in Grafana.

```python
import structlog
import uuid
from opentelemetry import trace

# Setup structlog for JSON output
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt='iso'),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

def handle_request():
    # Retrieve current OTel trace ID
    current_span = trace.get_current_span()
    trace_id = format(current_span.get_span_context().trace_id, '032x')
    
    # Bind context to all future log statements in this async context
    structlog.contextvars.bind_contextvars(
        trace_id=trace_id,
        request_id=str(uuid.uuid4())
    )
    
    # Output: {"event": "payment_failed", "amount": 50, "level": "error", "trace_id": "4bf...", "timestamp": "..."}
    logger.error("payment_failed", amount=50.00, reason="insufficient_funds")
```

---

## 9. SLOs and Error Budgets

Service Level Objectives (SLOs) provide mathematical rigor to system reliability.

- **SLI (Service Level Indicator)**: The actual measurement (e.g., 99.5% of requests succeed).
- **SLO (Service Level Objective)**: The target you want to hit (e.g., target = 99.9%).
- **Error Budget**: The acceptable amount of failure before you violate the SLO. 
  - For a 99.9% availability SLO over 30 days, the error budget is **43.2 minutes** of downtime.

### Burn Rate Alerts
Instead of alerting when the system is fully down (which is too late) or when a single error occurs (which is noisy), you alert on **Burn Rate**—how fast you are consuming your monthly error budget.

```yaml
# Prometheus Alert Rule for Fast Burn Rate
alert: ErrorBudgetBurnRateFast
expr: |
  (
    sum(rate(http_requests_total{status_code=~"5..",service="order-service"}[1h]))
    /
    sum(rate(http_requests_total{service="order-service"}[1h]))
  ) > 14.4 * 0.001
severity: critical
annotations:
  description: "Burning through monthly error budget 14.4x faster than allowed. Budget will exhaust in 2 days."
```

## 10. Tracing Backends: Jaeger vs. Tempo

Once the OTel Collector processes spans, it sends them to a backend for storage and querying.
- **Jaeger**: The traditional standard. Requires Elasticsearch or Cassandra for scalable storage. Excellent standalone UI.
- **Grafana Tempo**: A newer backend. Uses object storage (S3) making it significantly cheaper at massive scale. Integrates perfectly with the Grafana ecosystem, allowing seamless jumping between Logs (Loki), Metrics (Prometheus), and Traces (Tempo).

## 11. Advanced Tracing Concepts: Tail-Based vs Head-Based Sampling

As your microservices architecture grows, tracing every single request (100% sampling) becomes prohibitively expensive.

### Head-Based Sampling
- The decision to sample is made at the very beginning of the trace (usually at the API Gateway).
- **Pros**: Very lightweight. Downstream services immediately know whether to sample.
- **Cons**: You might drop traces of requests that encounter an error downstream, because the decision to drop was made randomly at the edge before the error occurred.

### Tail-Based Sampling
- Every service generates 100% of traces, but they are sent to the OTel Collector (or a dedicated proxy) which buffers them in memory.
- The Collector waits until the trace finishes, then analyzes it. If the trace contains an error or high latency, it keeps it. If it was a fast, successful request, it drops it.
- **Pros**: You never lose an error trace.
- **Cons**: Highly memory-intensive at the Collector layer.

## 12. Correlation: Tying it All Together

A mature observability platform allows seamless context switching:
1. Receive a Slack alert from Alertmanager about an SLO violation (Burn Rate Alert).
2. Click the link to view the Grafana Dashboard showing the exact microservice and endpoint causing the error rate spike.
3. Highlight a spike in the graph to view Exemplars (Trace IDs linked to metric data points).
4. Click an Exemplar Trace ID to instantly jump into Jaeger/Tempo to view the distributed trace waterfall.
5. In the trace waterfall, identify the exact slow/failing span (e.g., a DB call).
6. Click the span to jump directly into Loki to view the structured JSON logs with the same `trace_id` for that exact microsecond.

This eliminates manual searching and allows mean-time-to-recovery (MTTR) to drop from hours to minutes.

### Section: Sampling Strategies

```python
# Why sampling: at 10,000 req/s, tracing every request = 10,000 spans/s
# Storage cost is prohibitive; most requests are uninteresting (200 OK, fast)

# Head-based sampling: decision made at first service (before seeing full trace)
# Pros: simple, low overhead
# Cons: may miss rare slow/error traces
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased, ParentBased

# Sample 5% of all traces
sampler = ParentBased(root=TraceIdRatioBased(rate=0.05))
# ParentBased: if parent span is sampled, child is always sampled (trace completeness)

provider = TracerProvider(sampler=sampler, resource=resource)

# Tail-based sampling: decision made AFTER full trace is collected
# Can sample based on: error traces (always), slow traces (P99 > 2s), user tier
# Requires: collect all spans first, then decide
# Tool: OpenTelemetry Tail Sampling Processor

# otel-collector tail sampling config:
# processors:
#   tail_sampling:
#     decision_wait: 10s  # wait 10s for all spans before deciding
#     policies:
#       - name: sample-errors
#         type: status_code
#         status_code: {status_codes: [ERROR]}
#       - name: sample-slow
#         type: latency
#         latency: {threshold_ms: 2000}
#       - name: sample-5pct-rest
#         type: probabilistic
#         probabilistic: {sampling_percentage: 5}
```

### Section: Log Aggregation with Loki

```yaml
# Grafana Loki: log aggregation system ("Prometheus for logs")
# Indexes only metadata (labels), not log content (much cheaper than Elasticsearch)
# Integrates natively with Grafana

# Promtail config: scrape logs from Kubernetes pods
clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: kubernetes-pods
    kubernetes_sd_configs:
      - role: pod
    pipeline_stages:
      - json:
          expressions:
            level: level
            trace_id: trace_id
            service: service_name
      - labels:
          level:
          trace_id:
          service:
      - timestamp:
          source: timestamp
          format: RFC3339
    relabel_configs:
      - source_labels: [__meta_kubernetes_namespace]
        target_label: namespace
      - source_labels: [__meta_kubernetes_pod_name]
        target_label: pod
```

LogQL queries (Loki query language):
```logql
# All error logs from order-service in last 5 minutes:
{service="order-service", level="error"} |= `` | json

# Count errors per service over time:
sum by (service) (count_over_time({level="error"}[5m]))

# Find logs for a specific trace (correlate with Jaeger):
{namespace="production"} | json | trace_id="4bf92f3577b34da6a3ce929d0e0e4736"

# Payment failures with context:
{service="payment-service", level="error"} | json | line_format "{{.timestamp}} ORDER:{{.order_id}} REASON:{{.failure_reason}}"

# Latency distribution from logs:
{service="order-service"} | json | unwrap duration_ms | quantile_over_time(0.99, [5m]) by (endpoint)
```

### Section: Alerting Rules

```yaml
# Prometheus alerting rules for microservices
groups:
  - name: microservices
    rules:

    # Service down: no healthy instances
    - alert: ServiceDown
      expr: up{job="microservices"} == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "Service {{ $labels.service }} is down"
        description: "No healthy instances of {{ $labels.service }} for 1 minute"

    # High error rate (>5% 5xx for 5 minutes)
    - alert: HighErrorRate
      expr: |
        sum(rate(http_requests_total{status_code=~"5.."}[5m])) by (service)
        /
        sum(rate(http_requests_total[5m])) by (service)
        > 0.05
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High error rate on {{ $labels.service }}"
        description: "{{ $labels.service }} error rate is {{ $value | humanizePercentage }}"

    # P99 latency too high
    - alert: HighP99Latency
      expr: |
        histogram_quantile(0.99,
          sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service)
        ) > 1.0
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "P99 latency > 1s on {{ $labels.service }}"

    # Kafka consumer lag too high
    - alert: KafkaConsumerLagHigh
      expr: kafka_consumer_group_lag{group=~".*"} > 10000
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "Kafka consumer lag high for group {{ $labels.group }}"
        description: "Consumer group {{ $labels.group }} is {{ $value }} messages behind"

    # Outbox relay falling behind
    - alert: OutboxRelayLagging
      expr: outbox_pending_events_total > 1000
      for: 2m
      labels:
        severity: critical
      annotations:
        summary: "Outbox relay is falling behind"
        description: "{{ $value }} events stuck in outbox -- check relay process"
```

### Section: Golden Signals Dashboard

```python
# Google SRE Golden Signals: Latency, Traffic, Errors, Saturation
# Every microservice should have a dashboard with these 4 panels

# Grafana dashboard JSON (key panels):
golden_signals_panels = [
    {
        'title': '1. Traffic (Requests per Second)',
        'type': 'timeseries',
        'query': 'sum(rate(http_requests_total[5m])) by (service)',
        'description': 'How much demand is being placed on the system'
    },
    {
        'title': '2. Errors (Error Rate %)',
        'type': 'timeseries',
        'query': '''
            100 * sum(rate(http_requests_total{status_code=~"5.."}[5m])) by (service)
            / sum(rate(http_requests_total[5m])) by (service)
        ''',
        'thresholds': [{'value': 1, 'color': 'yellow'}, {'value': 5, 'color': 'red'}]
    },
    {
        'title': '3. Latency (P50, P95, P99)',
        'type': 'timeseries',
        'queries': [
            'histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service))',
            'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service))',
            'histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service))'
        ]
    },
    {
        'title': '4. Saturation (CPU + Memory)',
        'type': 'timeseries',
        'queries': [
            'sum(rate(container_cpu_usage_seconds_total[5m])) by (pod) / sum(kube_pod_container_resource_limits{resource="cpu"}) by (pod)',
            'sum(container_memory_working_set_bytes) by (pod) / sum(kube_pod_container_resource_limits{resource="memory"}) by (pod)'
        ]
    }
]
```
