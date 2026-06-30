# Solution: PromQL Reference Queries

## Panel 1 — Requests Per Second (split by endpoint)
```promql
sum by (endpoint) (rate(http_requests_total[1m]))
```

## Panel 2 — Error Rate as a Percentage
```promql
sum(rate(http_requests_total{status_code=~"5.."}[5m]))
/
sum(rate(http_requests_total[5m]))
* 100
```

## Panel 3 — p99 Latency in Milliseconds
```promql
histogram_quantile(
  0.99,
  sum(rate(http_request_duration_seconds_bucket[1m])) by (le)
) * 1000
```

## Panel 4 — Currently Active (In-Flight) Requests
```promql
http_requests_in_progress
```

---

## Bonus: Useful Production Queries

### p50, p95, p99 all at once (put in one panel)
```promql
histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
```

### Total request volume in the last hour
```promql
increase(http_requests_total[1h])
```

### Apdex score (Application Performance Index)
# Apdex = (Satisfactory + Tolerating/2) / Total
# Satisfactory: < 0.1s, Tolerating: < 0.5s
```promql
(
  sum(rate(http_request_duration_seconds_bucket{le="0.1"}[5m]))
  +
  sum(rate(http_request_duration_seconds_bucket{le="0.5"}[5m])) / 2
)
/
sum(rate(http_request_duration_seconds_count[5m]))
```
