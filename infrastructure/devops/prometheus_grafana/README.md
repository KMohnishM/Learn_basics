# Prometheus & Grafana — Deep Dive

This is a dedicated, standalone module for Prometheus and Grafana. 
Module 6 introduced the concepts at a high level. Here, we go deep on every feature, configuration option, and real-world pattern you will encounter in production.

---

## 1. Why Prometheus? (The Problem It Solves)

Traditional monitoring tools (like Nagios, Zabbix) worked by running agents on each server that would *push* metrics to a central server. This created problems:
- **Firewall complexity**: Every server had to have an outbound connection.
- **Scaling**: A central receiver needed to handle all pushes simultaneously.
- **Discovery**: You had to manually register every new server.

Prometheus solved this by **inverting the model**. Prometheus *reaches out* to your services and *scrapes* (pulls) their metrics. This means:
- Services just need to expose a simple HTTP endpoint (`/metrics`).
- Prometheus handles its own discovery and scheduling.
- It's far easier to add new services — just update the Prometheus config.

---

## 2. Prometheus Architecture — Every Component Explained

```
┌──────────────────────────────────────────────────┐
│                PROMETHEUS SERVER                  │
│                                                   │
│  ┌──────────────┐    ┌──────────────────────────┐ │
│  │   Retrieval  │ →  │  Time Series Database    │ │
│  │  (Scraper)   │    │  (TSDB - on local disk)  │ │
│  └──────────────┘    └──────────────────────────┘ │
│          ↑                        ↓               │
│  ┌───────────────┐    ┌───────────────────────┐   │
│  │  Service      │    │  HTTP API             │   │
│  │  Discovery    │    │  (PromQL Queries)     │   │
│  └───────────────┘    └───────────────────────┘   │
└──────────────────────────────────────────────────┘
          ↓                        ↓
┌──────────────────┐    ┌──────────────────────┐
│  Your App        │    │  Grafana /            │
│  /metrics        │    │  Alertmanager         │
└──────────────────┘    └──────────────────────┘
```

### a) Retrieval (Scraper)
The core loop. Every `scrape_interval` (default: 15s), Prometheus fetches the `/metrics` endpoint of every configured target and stores the results as a timestamped snapshot.

### b) Time Series Database (TSDB)
Prometheus stores all data on **local disk** in a highly compressed, custom binary format. It is NOT a traditional SQL database. Data is organized as:
- **Time Series**: A stream of timestamped values identified by a metric name and a set of labels.
- **Blocks**: Data is written to in-memory chunks first, then flushed to disk as 2-hour blocks.
- **Retention**: By default, Prometheus keeps data for **15 days** (`--storage.tsdb.retention.time=15d`).

### c) Service Discovery
In a dynamic environment like Kubernetes, pods come and go constantly. You can't hardcode IPs. Prometheus supports:
- **Static Config**: You hardcode the `host:port` of targets.
- **File-Based Discovery**: Prometheus reads a JSON/YAML file you update dynamically.
- **Kubernetes Discovery**: Prometheus talks to the K8s API Server and automatically discovers all Pods, Services, or Nodes matching a label selector.

### d) Alertmanager
A separate process that handles alerts fired by Prometheus. Prometheus evaluates **alerting rules** and *fires* an alert when a rule is breached. Alertmanager then handles:
- **Routing**: Send database alerts to the DB team, app alerts to the app team.
- **Grouping**: Combine 50 identical alerts into a single notification.
- **Silencing**: Mute alerts during a planned maintenance window.
- **Notification**: Send to Slack, PagerDuty, email, webhooks, etc.

---

## 3. The `/metrics` Endpoint & Exposition Format

Any service that exposes Prometheus metrics must do so at an HTTP endpoint. The format is simple plain text:

```
# HELP http_requests_total The total number of HTTP requests received.
# TYPE http_requests_total counter
http_requests_total{method="GET", status="200"} 12847
http_requests_total{method="POST", status="200"} 3291
http_requests_total{method="GET", status="404"} 128

# HELP process_memory_bytes Current memory usage in bytes.
# TYPE process_memory_bytes gauge
process_memory_bytes 52428800
```

- `# HELP`: Human-readable description.
- `# TYPE`: The metric type (see next section).
- `{key="value"}`: Labels that add dimensions to a metric.
- The final number: The current value.

---

## 4. The Four Metric Types

### Counter
A value that **only ever goes up** (or resets to 0 on restart). 
- ✅ Use for: Total requests, total errors, total bytes sent.
- ❌ Never use for: Temperature, memory usage (which can go up AND down).
- **Key insight**: You almost never query the raw counter value. You query its **rate of change**.

```
# Raw value (not very useful alone)
http_requests_total 1048576

# Useful: rate of requests per second over the last 5 minutes
rate(http_requests_total[5m])
```

### Gauge
A value that **can go up or down** — a snapshot of the current state.
- ✅ Use for: Current memory usage, CPU temperature, number of active connections, queue size.
- You query the raw value directly.

```
memory_usage_bytes 524288000
active_connections 42
```

### Histogram
Counts observations and places them into pre-configured **buckets**. This allows you to calculate **percentile latencies** (p50, p95, p99) — the gold standard for measuring API response time.

When you declare a histogram named `http_request_duration_seconds`, Prometheus automatically creates:
- `http_request_duration_seconds_bucket{le="0.1"}`: Requests that took ≤ 100ms
- `http_request_duration_seconds_bucket{le="0.5"}`: Requests that took ≤ 500ms
- `http_request_duration_seconds_bucket{le="1.0"}`: Requests that took ≤ 1 second
- `http_request_duration_seconds_sum`: Total duration of all requests
- `http_request_duration_seconds_count`: Total number of requests

```promql
# Calculate the 95th percentile latency over the last 5 minutes
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### Summary
Similar to Histogram, but calculates quantiles **on the client side** (inside your application). Less flexible but more accurate for specific quantiles. Not commonly recommended for new applications — prefer Histogram.

---

## 5. PromQL — The Query Language

PromQL is a functional query language. Everything revolves around **Selectors** and **Functions**.

### Selectors
```promql
# Select all time series with this metric name
http_requests_total

# Filter by labels (exact match)
http_requests_total{status="200"}

# Filter by labels (regex match — all 5xx errors)
http_requests_total{status=~"5.."}

# Filter by labels (NOT equal)
http_requests_total{method!="GET"}
```

### Range Vectors
Add a time duration in square brackets to get a range of data points (used with rate/increase):
```promql
# Last 5 minutes of data for this metric
http_requests_total[5m]
```

### Essential Functions

| Function | Use Case | Example |
|---|---|---|
| `rate()` | Per-second rate of a counter | `rate(http_requests_total[5m])` |
| `increase()` | Total increase of a counter over a time range | `increase(http_requests_total[1h])` |
| `sum()` | Aggregate across multiple label values | `sum(http_requests_total)` |
| `avg()` | Average across multiple instances | `avg(cpu_usage_percent)` |
| `max()` | Max value across instances | `max(memory_usage_bytes)` |
| `by()` | Group results by specific labels | `sum by(status) (http_requests_total)` |
| `histogram_quantile()` | Calculate percentile from histogram | `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))` |

### Real-World PromQL Examples
```promql
# 1. Error rate (% of requests that are errors)
rate(http_requests_total{status=~"5.."}[5m])
/
rate(http_requests_total[5m])

# 2. p99 request latency in milliseconds
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) * 1000

# 3. Memory usage as a percentage of total
(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes)
/
node_memory_MemTotal_bytes * 100

# 4. CPU usage (1 - idle time) across all cores
1 - avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m]))
```

---

## 6. Alerting Rules

Alerts are defined in YAML rules files and evaluated by Prometheus.

```yaml
# alert_rules.yml
groups:
  - name: api_alerts
    rules:
      # Alert if error rate is above 5% for more than 5 minutes
      - alert: HighErrorRate
        expr: |
          rate(http_requests_total{status=~"5.."}[5m])
          /
          rate(http_requests_total[5m]) > 0.05
        for: 5m   # Must be true for 5 consecutive minutes before firing
        labels:
          severity: critical
        annotations:
          summary: "High error rate on {{ $labels.instance }}"
          description: "Error rate is {{ $value | humanizePercentage }} on {{ $labels.instance }}"
          
      # Alert if a service is completely down
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"
```

---

## 7. Grafana — Deep Dive

Grafana is not just a "pretty dashboard" tool. It is a full observability platform.

### Data Sources
Grafana connects to external databases. You add a data source, and Grafana uses it for all queries. Supported sources include: Prometheus, Loki (logs), PostgreSQL, MySQL, AWS CloudWatch, Elasticsearch, and many more.

### Dashboard Architecture
```
Dashboard
└── Row (visual grouping)
    └── Panel (a single visualization)
        ├── Query (PromQL / SQL / etc.)
        ├── Transform (post-process data)
        └── Visualization (Graph, Stat, Gauge, Table, Heatmap...)
```

### Panel Types
- **Time Series**: Line/bar chart over time. Best for rate-of-change metrics.
- **Stat**: Shows a single large number. Great for "current value" gauges.
- **Gauge**: A needle/arc visualization showing how far a value is between min and max.
- **Table**: Tabular data, supports sorting and filtering.
- **Heatmap**: Shows distribution of values over time (great for histograms).
- **Logs**: Shows log lines from Loki.

### Variables (Templated Dashboards)
The most powerful Grafana feature. Variables let you make dynamic dashboards where users can filter by `instance`, `environment`, or `job` without creating separate dashboards.

```
# Define a variable called "instance"
# Query: label_values(up, instance)
# This populates a dropdown with all unique instance label values in Prometheus!
```

Then in your panels, use `$instance` in your PromQL:
```promql
rate(http_requests_total{instance="$instance"}[5m])
```

### Alerting in Grafana
Grafana has its own alerting system (separate from Prometheus Alertmanager). It supports multi-dimensional alerts, contact points (Slack, email, PagerDuty), and notification policies.

---

## Next Steps
Head over to `labs/` to run a full Prometheus + Grafana + instrumented Python app stack locally!
