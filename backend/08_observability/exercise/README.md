# Exercise: Build an SLO Dashboard

## The Problem

Your team has agreed to these SLOs for the Orders API:
- **Success Rate SLO**: 99.5% of requests must succeed (HTTP < 500)
- **Latency SLO**: p99 latency must be below 500ms

But there's no way to currently see if you're meeting them!

## Your Task

Write `solution/slo_reporter.py` — a script that:

1. **Queries Prometheus** (running on `http://localhost:9090`) using its HTTP API to fetch:
   - Total requests in the last 30 minutes: `sum(http_requests_total)`
   - Error requests in the last 30 minutes: `sum(http_requests_total{http_status=~"5.."})` 
   - p99 latency: `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))`

2. **Calculates** the current SLO status:
   - `success_rate = (total - errors) / total * 100`
   - `error_budget_consumed = (1 - success_rate) / (1 - slo_target) * 100`

3. **Prints a clear report**:
   ```
   ═══════════════════════════════════════════
    Orders API — SLO Report (Last 30 minutes)
   ═══════════════════════════════════════════
   
   ✅ Success Rate:     99.73%    (SLO: 99.5%)
      Error Budget:     54% consumed  (margin: 46%)
   
   ⚠️  p99 Latency:     523ms     (SLO: <500ms)  ← SLO BREACH!
   
   Recommendation: Investigate latency — p99 is above target.
   ═══════════════════════════════════════════
   ```

4. Returns exit code `0` if all SLOs are met, `1` if any are breached (so it can be used in CI/CD checks).

**Hint**: Prometheus HTTP API is at `http://localhost:9090/api/v1/query`.
```python
response = requests.get("http://localhost:9090/api/v1/query", params={"query": "your_promql_here"})
value = response.json()["data"]["result"][0]["value"][1]
```
