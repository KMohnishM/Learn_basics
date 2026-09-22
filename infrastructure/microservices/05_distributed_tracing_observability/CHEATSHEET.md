# Observability & Tracing Cheatsheet

## The Three Pillars of Observability

| Pillar | Purpose | Tools | Key Question Answered | Data Format |
| :--- | :--- | :--- | :--- | :--- |
| **Logs** | Discrete system events | ELK Stack, Loki, Splunk | *What* exactly happened? | JSON, Key-Value |
| **Metrics** | Aggregated data over time | Prometheus, Datadog | *How much* / *How fast*? | Time-series, Gauges |
| **Traces** | End-to-end request lifecycle | Jaeger, Tempo, Zipkin | *Where* did it slow down/fail? | Spans, Trees |

## OpenTelemetry (OTel) Signals

| Component | Responsibility | Examples |
| :--- | :--- | :--- |
| **Instrument SDK** | Generates spans/metrics in app code | `opentelemetry-python`, auto-instrumenters |
| **W3C Headers** | Propagates Trace ID across network | `traceparent: 00-{traceID}-{spanID}-01` |
| **OTel Collector** | Proxy that receives, batches, exports | Receivers(OTLP), Processors(batch), Exporters |
| **Backends** | Long-term storage and visualization | Jaeger (traces), Prometheus (metrics) |

## Prometheus Metric Types

| Type | Description | Use Case |
| :--- | :--- | :--- |
| **Counter** | Cumulative value, only goes UP | Total HTTP requests, total errors |
| **Gauge** | Value that goes UP or DOWN | Active memory, current DB connections |
| **Histogram** | Counts events into buckets (ranges) | Request latency, response size |
| **Summary** | Calculates quantiles on client side | Complex aggregations (rarely used over Histograms) |

## Key PromQL Patterns (The RED Method)

| Metric | PromQL Query |
| :--- | :--- |
| **R**ate | `sum(rate(http_requests_total[5m])) by (service)` |
| **E**rrors | `sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))` |
| **D**uration | `histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))` |
| **Active** | `sum(active_connections) by (service)` |

## Span Attributes Best Practices

To make traces searchable, always add these semantic attributes to your spans:
- `service.name`: The name of the microservice.
- `service.version`: The git commit or release version.
- `http.method` & `http.route`: e.g., `POST`, `/orders/{id}`.
- `user.id` or `tenant.id`: For tracking specific user issues.
- `business.entity_id`: e.g., `order_id=12345`.

## Service Level Objectives (SLOs) Template

| Concept | Definition | Example |
| :--- | :--- | :--- |
| **SLI** | Service Level Indicator (The actual math) | `200s / Total Requests` |
| **SLO** | Service Level Objective (The target) | `99.9% over 30 days` |
| **Error Budget** | 100% - SLO (Allowed downtime) | `43.2 minutes per month` |
| **Burn Rate** | How fast budget is being consumed | `Alert if Burn Rate > 14.4x` |

## Observability Stack Options

| Paradigm | Metrics | Logs | Traces | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **CNCF Open Source** | Prometheus | ELK (Elasticsearch) | Jaeger | Complex to manage at scale, requires indexing DBs |
| **Grafana LGTM** | Prometheus | Loki | Tempo | Object-storage backed. Extremely cost-effective |
| **SaaS Providers** | Datadog | Datadog | Datadog | Easiest setup, high financial cost, vendor lock-in |
