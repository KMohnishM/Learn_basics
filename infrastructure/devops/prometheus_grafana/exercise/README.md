# Module: Prometheus & Grafana
# Exercise: Build a Production-Ready Dashboard

Now that you have the full monitoring stack running via `docker-compose up`, it is time to actually USE it.

## Part 1: Generate Some Traffic

Run this command to simulate real user traffic against your instrumented app. 
This uses `curl` in a loop to hit all three endpoints (fast, slow, and error).

On Linux/Mac:
```bash
for i in {1..200}; do
  curl -s http://localhost:5000/ > /dev/null
  curl -s http://localhost:5000/slow > /dev/null
  curl -s http://localhost:5000/error > /dev/null
  sleep 0.5
done
```

On Windows PowerShell:
```powershell
1..200 | ForEach-Object {
    Invoke-WebRequest -Uri http://localhost:5000/ -UseBasicParsing | Out-Null
    Invoke-WebRequest -Uri http://localhost:5000/slow -UseBasicParsing | Out-Null
    Invoke-WebRequest -Uri http://localhost:5000/error -UseBasicParsing | Out-Null
    Start-Sleep -Milliseconds 500
}
```

---

## Part 2: Verify Data in Prometheus

Open Prometheus at `http://localhost:9090`.

1. Go to **Status > Targets**. You should see `python-api` as `UP`. This proves Prometheus can scrape your app.
2. Go to the **Graph** tab. Try running these PromQL queries one at a time and observe the results:
   - `http_requests_total`
   - `rate(http_requests_total[1m])`
   - `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[1m]))`

---

## Part 3: Build a Grafana Dashboard

Open Grafana at `http://localhost:3000` (credentials: `admin` / `devops123`).

Your task is to create a dashboard with the following **4 panels**:

### Panel 1: Request Rate (Time Series)
- **Title**: "Requests Per Second"
- **Query**: `sum by (endpoint) (rate(http_requests_total[1m]))`
- **Type**: Time Series

### Panel 2: Error Rate (Stat)
- **Title**: "Error Rate %"
- **Query**: `sum(rate(http_requests_total{status_code=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100`
- **Type**: Stat
- **Thresholds**: Green below 1%, Yellow below 5%, Red above 5%

### Panel 3: p99 Latency (Gauge)
- **Title**: "p99 Response Time (ms)"
- **Query**: `histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[1m])) by (le)) * 1000`
- **Type**: Gauge
- **Min**: 0, **Max**: 2000 (milliseconds)

### Panel 4: In-Flight Requests (Stat)
- **Title**: "Active Requests Right Now"
- **Query**: `http_requests_in_progress`
- **Type**: Stat

---

## Part 4: Test Your Alerts

1. Stop the app container: `docker stop <app-container-name>`
2. Wait ~1 minute and check `http://localhost:9090/alerts`. You should see the `ServiceDown` alert firing!
3. Restart the app: `docker start <app-container-name>`

Good luck! Check the `solution/` folder for the PromQL queries written out.
