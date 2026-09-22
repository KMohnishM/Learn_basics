# Distributed Tracing and Observability QnA

## 1. What are the three pillars of observability (logs, metrics, traces)? Why are metrics alone insufficient to diagnose a microservice failure? Give a specific scenario requiring all three.
The three pillars of observability are essential for understanding complex systems.
Metrics are aggregated numerical data measured over intervals of time (e.g., CPU usage %, HTTP error rates). They are cheap to store and excellent for alerting ("System is broken!").
Logs are immutable, timestamped records of discrete events (e.g., "User 123 logged in"). They provide high-fidelity context for debugging ("Why did it break?").
Traces track the progression of a single request across distributed microservices, showing latency and dependencies.
Metrics alone are insufficient because they only indicate a symptom, not a root cause. If a dashboard shows a spike in 500 errors in the API Gateway, metrics cannot tell you *which* downstream service caused it.
Scenario: An alert fires because the `checkout_latency_p99` metric spikes to 10 seconds. You investigate. First, you look at Traces to see the execution path. The trace reveals that the API Gateway called the Order Service, which then called the Payment Service, and the Payment Service took 9.8 seconds. Now you know the bottleneck. Next, you use the `Trace ID` to filter the Logs within the Payment Service. The logs reveal a specific error message: "ConnectionTimeout to database cluster." All three pillars were required to go from high-level alert to specific root cause.

## 2. What is a distributed trace? Define Trace ID, Span, Parent Span ID, and Span Attributes. Draw an ASCII diagram of a trace for POST /orders touching Order, Inventory, Payment, and Notification services.
A distributed trace is a representation of the complete lifecycle of a single request as it travels across multiple services in a distributed architecture. It allows engineers to visualize latency, bottlenecks, and error propagation.
Definitions:
- Trace ID: A globally unique identifier (e.g., a 128-bit UUID) assigned to a request at the system's entry point. Every subsequent microservice includes this ID in its telemetry data.
- Span: Represents a single logical unit of work within a trace (e.g., executing a database query, or making an HTTP call).
- Parent Span ID: The ID of the span that triggered the current span. This creates a causal, hierarchical tree structure. The root span has no parent.
- Span Attributes: Key-value metadata attached to a span for context (e.g., `http.status_code=200`, `user.id=123`).
ASCII Diagram:
```text
Trace ID: a1b2c3d4
[API Gateway: POST /orders] (Span A) -----------------------------------> (Total: 800ms)
  |
  +-> [Order Service: validate_order] (Span B, Parent: A) -----> (200ms)
  |
  +-> [Inventory Service: reserve_stock] (Span C, Parent: A) ---> (300ms)
  |
  +-> [Payment Service: charge_card] (Span D, Parent: A) -------> (250ms)
  |
  +-> [Notification Service: async_email] (Span E, Parent: A) -> (50ms)
```

## 3. What is OpenTelemetry? What problem does it solve over vendor-specific SDKs? What are the three signals it standardizes and what does auto-instrumentation cover?
OpenTelemetry (OTel) is an open-source observability framework and CNCF project comprising APIs, SDKs, and tools to generate, collect, and export telemetry data.
It solves the problem of vendor lock-in. Historically, if you used Datadog, you had to embed Datadog's proprietary SDKs throughout your codebase. If you switched to New Relic or Jaeger, you had to rewrite all your instrumentation code. OpenTelemetry provides a single, vendor-neutral standard. You instrument your code once using OTel SDKs, and configure an external OTel Collector to route the data to any backend vendor without changing application code.
It standardizes three signals: Traces, Metrics, and Logs.
Auto-instrumentation is a powerful feature where the OTel agent dynamically injects bytecode (in Java/Node) or wraps libraries (in Python) at runtime. It automatically captures telemetry for popular frameworks (like Flask, Django, Spring Boot), HTTP clients (requests, httpx), and database drivers (SQLAlchemy, psycopg2) without requiring developers to write any manual tracing code.

## 4. What is the W3C TraceContext standard? What does the traceparent header contain? How does context propagation work when Order Service calls Payment Service with httpx?
The W3C TraceContext standard defines a unified format for propagating tracing context across network boundaries via HTTP headers. Before this standard, different vendors used proprietary headers (e.g., `X-B3-TraceId`, `x-datadog-trace-id`), causing broken traces in heterogeneous environments.
The standard defines the `traceparent` header. It contains four fields separated by hyphens:
`traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`
- `00`: Version number.
- `4bf9...`: Trace ID (16-byte array).
- `00f0...`: Parent Span ID (8-byte array).
- `01`: Trace Flags (e.g., indicating if this trace is sampled).
Context Propagation with `httpx` in Python: When the Order Service prepares an HTTP request to the Payment Service, the OpenTelemetry auto-instrumentation intercepts the `httpx.post()` call. It reads the current active Trace ID from Python's contextvars (thread-local storage). It formats these IDs according to the W3C standard and injects the `traceparent` header into the outgoing HTTP request. The Payment Service receives the request, extracts the header, and sets it as the active context, thus linking the two services into a single trace.

## 5. What is the OpenTelemetry Collector? What are its three component types (receivers, processors, exporters)? Show a complete collector config that receives OTel data and exports to Jaeger and Prometheus.
The OpenTelemetry Collector is a vendor-agnostic proxy that receives, processes, and exports telemetry data. It offloads data handling from application processes, allowing for centralized configuration of sampling, filtering, and routing.
Its pipeline consists of three component types:
1. Receivers: How data gets into the collector (e.g., OTLP via gRPC, Prometheus scrape, Jaeger thrift).
2. Processors: Manipulate data before exporting (e.g., batching, tail-sampling, obfuscating PII data, adding environment tags).
3. Exporters: How data is sent to backend destinations (e.g., Jaeger, Prometheus, Datadog).
```yaml
receivers:
  otlp:
    protocols:
      grpc: { endpoint: "0.0.0.0:4317" }

processors:
  batch:
    timeout: 1s
    send_batch_size: 1024
  resource:
    attributes:
    - key: environment
      value: production
      action: insert

exporters:
  jaeger:
    endpoint: "jaeger-all-in-one:14250"
    tls: { insecure: true }
  prometheus:
    endpoint: "0.0.0.0:8889"

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch, resource]
      exporters: [jaeger]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus]
```

## 6. What is the difference between a Prometheus Counter, Histogram, and Gauge? Give a real microservice example of each. What metric type would you use to measure request latency?
Prometheus defines distinct metric types based on how the underlying data behaves.
1. Counter: A cumulative metric that only ever goes up (or resets to zero on restart). You cannot decrement a counter. 
   - Example: `http_requests_total`. Used to measure the total number of orders processed or total errors encountered.
2. Gauge: A metric that represents a single numerical value that can arbitrarily go up and down.
   - Example: `active_database_connections`, `memory_usage_bytes`, or `queue_depth`. Used for point-in-time state.
3. Histogram: Samples observations (usually things like durations or file sizes) and counts them in configurable buckets. It provides a statistical distribution of values, allowing calculation of percentiles.
   - Example: `http_request_duration_seconds`. 
To measure request latency, you MUST use a Histogram. A Gauge cannot capture the distribution of thousands of concurrent requests, and an average (sum/count) hides outliers (the long tail). A Histogram allows you to calculate the P99 latency, showing exactly what the slowest 1% of users are experiencing.

## 7. Write the PromQL query to calculate: (a) 5-minute request rate by service, (b) 5-minute error rate percentage, (c) P99 latency per endpoint. Explain each query.
PromQL is the query language for Prometheus.
(a) 5-minute request rate by service:
`sum by (service) (rate(http_requests_total[5m]))`
Explanation: `http_requests_total` is a counter. `rate(...[5m])` calculates the per-second rate of increase over a 5-minute rolling window. `sum by (service)` aggregates the rates across all pods/instances of a specific service.
(b) 5-minute error rate percentage:
`sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100`
Explanation: Divides the rate of requests with 5xx status codes by the rate of all requests over the same 5-minute window, multiplied by 100 to get a percentage.
(c) P99 latency per endpoint:
`histogram_quantile(0.99, sum by (le, endpoint) (rate(http_request_duration_seconds_bucket[5m])))`
Explanation: `http_request_duration_seconds_bucket` is a histogram. `rate(...[5m])` calculates the rate of observations falling into each bucket (`le`). `sum by (le, endpoint)` aggregates these buckets across all instances for a specific endpoint. Finally, `histogram_quantile(0.99, ...)` mathematically interpolates the 99th percentile latency from those aggregated buckets.

## 8. What is structured logging? Why is JSON output better than plaintext for microservices at scale? Show how structlog automatically binds trace_id and request_id to every log line in a FastAPI request lifecycle.
Structured logging means emitting logs as machine-readable data structures (typically JSON) rather than unstructured strings of text.
JSON output is vastly superior for microservices at scale because log aggregators (Elasticsearch, Loki, Splunk) can natively index JSON fields. If a log is plaintext: `INFO: User 123 failed to purchase item 456`, searching for all failures for item 456 requires fragile regex parsing. With JSON: `{"level":"info", "event":"purchase_failed", "user_id":123, "item_id":456}`, you can execute strict, fast analytical queries: `item_id=456 AND level=error`.
In Python, libraries like `structlog` handle this elegantly by using thread-local context variables.
```python
import structlog
from fastapi import Request

logger = structlog.get_logger()

# Middleware executed on every incoming HTTP request
@app.middleware("http")
async def inject_logging_context(request: Request, call_next):
    # Bind context variables; these will automatically attach to ALL logs
    # emitted during this specific request's lifecycle.
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request.headers.get("X-Request-ID", generate_id()),
        trace_id=get_current_trace_id(),
        path=request.url.path
    )
    
    # Process request
    response = await call_next(request)
    return response

@app.get("/checkout")
def checkout():
    # Developer just logs normally. The output JSON will automatically 
    # include request_id and trace_id injected by the middleware.
    logger.info("Starting checkout process") 
```

## 9. What is an SLO, SLI, and error budget? Define a concrete SLO for an order creation endpoint. Calculate the error budget in minutes for 99.9% availability over 30 days.
Service Level Indicators (SLIs) are quantitative measures of a specific aspect of the level of service provided. They are the actual metrics (e.g., percentage of HTTP 200s, P99 latency).
Service Level Objectives (SLOs) are target values or ranges of values for a service level that is measured by an SLI. It represents the reliability goal agreed upon with the business.
An Error Budget is the maximum allowable number of errors/downtime a service can have over a specific period before violating the SLO. It flips the conversation from "zero downtime" to "acceptable risk."
Concrete SLO for Order Creation: "99.9% of POST /orders requests will complete successfully (HTTP 20x) within 500ms, measured over a rolling 30-day window."
Calculation:
- 30 days * 24 hours * 60 minutes = 43,200 total minutes.
- 99.9% availability means 0.1% allowable failure.
- Error budget = 43,200 * 0.001 = 43.2 minutes.
If the service is down for more than 43.2 minutes in a 30-day window, the error budget is exhausted, and the team should halt feature development to focus on reliability.

## 10. What is a burn rate alert? Why is it more effective than a simple threshold alert? Explain why a 14.4x burn rate in 1 hour is cause for a critical alert.
A burn rate alert measures how quickly a service is consuming its error budget relative to the overall time window. A burn rate of 1 means the budget will be exactly exhausted at the end of the 30-day window.
It is vastly more effective than a simple threshold alert (e.g., "Alert if error rate > 5%"). Simple thresholds suffer from false positives (a brief 5% spike might be harmless) and false negatives (a constant 0.5% error rate might silently exhaust the budget without triggering the 5% alert). Burn rates tie alerts directly to business impact (the SLO).
A 14.4x burn rate means the budget is being consumed 14.4 times faster than normal.
Why is it critical? If you maintain this burn rate, you will exhaust your entire 30-day error budget in just a few days. Specifically, 100% / (14.4 * 30 days) = exhausting the budget in ~2 days. A 14.4x burn rate sustained over 1 hour indicates a severe, ongoing outage that requires immediate paging of the on-call engineer before the SLO is permanently violated.

## 11. What is tail-based sampling vs head-based sampling in distributed tracing? When does each make sense? Show the OpenTelemetry Collector tail_sampling processor configuration.
Because generating and storing traces for 100% of traffic at massive scale is cost-prohibitive, systems use sampling.
Head-based sampling makes the sampling decision at the very beginning of the trace (the API gateway). A coin is flipped (e.g., 10% chance). If true, the `traceparent` header indicates sampling, and all downstream services record the trace. This is computationally cheap but flawed: you might drop traces for rare errors because they weren't randomly selected.
Tail-based sampling records 100% of spans into memory at the collector level. The sampling decision is made at the END of the trace. This allows intelligent decisions: you can configure it to keep 1% of successful traces, but keep 100% of traces containing an error or exceeding 2 seconds in latency. It guarantees you capture the most valuable data.
```yaml
processors:
  tail_sampling:
    decision_wait: 10s # Wait 10s for all spans to arrive
    num_traces: 100000 # Keep traces in memory
    policies:
      # Keep 100% of traces with errors
      - name: errors-policy
        type: status_code
        status_code: {status_codes: [ERROR]}
      # Keep 100% of slow traces (> 1000ms)
      - name: slow-policy
        type: latency
        latency: {threshold_ms: 1000}
      # Keep 5% of all other normal traces
      - name: baseline-policy
        type: probabilistic
        probabilistic: {sampling_percentage: 5}
```

## 12. What is the RED method for microservice monitoring? Define Rate, Errors, Duration. Write the three Prometheus queries implementing RED for an order-service.
The RED method is a monitoring philosophy specifically designed for microservices, defining the three fundamental metrics every request-driven service must measure.
1. Rate: The number of requests the service is receiving per second.
2. Errors: The number of failed requests per second.
3. Duration: The time taken to process requests (latency distributions).
Prometheus Queries for `order-service`:
Rate (Requests per second):
`sum(rate(http_requests_total{service="order-service"}[1m]))`
Errors (Errors per second):
`sum(rate(http_requests_total{service="order-service", status=~"5.."}[1m]))`
Duration (P95 Latency):
`histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket{service="order-service"}[1m])))`
By putting these three panels side-by-side on a Grafana dashboard for every microservice, engineers can instantly identify which service in a complex chain is anomalous.

## 13. What is Grafana Loki? How does it differ from Elasticsearch for log storage? Show three LogQL queries: error logs by service, logs for a specific trace ID, and error rate over time.
Grafana Loki is a horizontally scalable, highly available, multi-tenant log aggregation system inspired by Prometheus.
It differs drastically from Elasticsearch in its indexing strategy. Elasticsearch parses every log line and indexes every single word, creating massive, computationally expensive indexes (often larger than the logs themselves). Loki, however, only indexes metadata labels (like `service=frontend`, `env=prod`)—similar to Prometheus labels—and leaves the actual log payload unindexed as compressed text. This makes Loki incredibly cheap to operate and fast for ingestion, relying on brute-force distributed grep across the unindexed text at query time.
LogQL Queries:
1. Error logs for a specific service:
`{service="payment-service"} |= "error" | json | level="error"`
(Selects stream by label, greps for "error", parses JSON, filters by parsed level field).
2. Logs for a specific Trace ID across all services:
`{namespace="production"} |= "a1b2c3d4"`
3. Error rate over time (Metric query from logs):
`sum by (service) (rate({namespace="production"} |= "error" [5m]))`
This powerful feature allows you to generate Prometheus-style graphs directly from raw logs.

## 14. How do you write Prometheus alerting rules for microservices? Show four alert rules: ServiceDown, HighErrorRate (>5%), HighP99Latency (>1s), and KafkaConsumerLagHigh (>10000).
Prometheus alerting rules evaluate PromQL queries periodically. If a query returns results, the alert fires and is sent to the Alertmanager for routing (to Slack, PagerDuty).
```yaml
groups:
- name: microservices_alerts
  rules:
  # 1. Service Down: Up metric is 0 for more than 1 minute
  - alert: ServiceDown
    expr: up == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Instance {{ $labels.instance }} is down"

  # 2. High Error Rate: > 5% errors over 5 minutes
  - alert: HighErrorRate
    expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.05
    for: 2m
    labels:
      severity: page
    annotations:
      summary: "Service {{ $labels.service }} has > 5% error rate"

  # 3. High Latency: P99 > 1 second
  - alert: HighP99Latency
    expr: histogram_quantile(0.99, sum by (le, service) (rate(http_request_duration_seconds_bucket[5m]))) > 1.0
    for: 5m
    labels:
      severity: warning

  # 4. Kafka Consumer Lag: Lag exceeds 10,000 messages
  - alert: KafkaConsumerLagHigh
    expr: sum by (consumergroup) (kafka_consumergroup_lag) > 10000
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Consumer group {{ $labels.consumergroup }} is falling behind"
```

## 15. What is log correlation between Grafana and Jaeger? What field in the log enables clicking from a Loki log line directly to the Jaeger trace? How do you ensure this field is always present in logs?
Log correlation is the seamless integration between the logging pillar (Grafana/Loki) and the tracing pillar (Jaeger). When troubleshooting, an engineer often finds an error in the logs. Without correlation, they must manually copy a timestamp, switch to Jaeger, and try to guess which trace corresponds to that error. With correlation, a button appears next to the log line in Grafana; clicking it instantly opens the exact trace in Jaeger.
The critical field that enables this is the `trace_id`. The log aggregator must extract this field. Grafana is then configured to render any field named `trace_id` as a hyperlink to the Jaeger UI, passing the ID in the URL.
To ensure this field is always present, you must use a standardized logging framework and middleware (as discussed in structlog context vars). The OpenTelemetry auto-instrumentation provides this natively. When configured, OTel automatically injects the active `trace_id` and `span_id` into the thread-local context of the application's logging library (e.g., Python's standard `logging` or Java's Logback). Every single `logger.info()` call automatically appends these IDs to the JSON output, guaranteeing perfect correlation.
