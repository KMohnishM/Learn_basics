# Module 6: Monitoring & Observability

You have deployed your application. It is running in Kubernetes. The CI/CD pipeline is humming.
Two weeks later, the CEO calls you at 3 AM. "The website is down!"
You log into the server. Everything *looks* fine. Where is the bug? Is the database slow? Is the server out of memory? Is the network dropping packets?

Without Observability, you are flying blind.

## The Three Pillars of Observability

1. **Metrics**: Numeric data measured over time (e.g., "CPU usage is at 85%", "We are getting 500 requests per second"). Great for alerts and dashboards.
2. **Logs**: Immutable records of discrete events (e.g., "User kmohn logged in at 10:04 AM", "Database connection failed"). Great for debugging *why* something broke.
3. **Traces**: The path a single request takes as it travels through a distributed microservice architecture. (e.g., Request -> API -> Auth Service -> Database).

## Prometheus (Metrics Collection)
Prometheus is an open-source systems monitoring and alerting toolkit. 
Unlike many monitoring tools that wait for applications to "push" data to them, **Prometheus is pull-based.**

1. You configure your applications to expose a `/metrics` HTTP endpoint.
2. You configure Prometheus to "scrape" that endpoint every 15 seconds.
3. Prometheus stores the data in a highly efficient **Time-Series Database (TSDB)**.

### PromQL (Prometheus Query Language)
To get data out of Prometheus, you use PromQL. It allows you to aggregate data mathematically.
- Ex: `http_requests_total` (Shows the total number of requests)
- Ex: `rate(http_requests_total[5m])` (Calculates the *per-second rate* of requests over the last 5 minutes).

## Grafana (Visualization)
Prometheus is great at storing data, but its UI is very basic.
**Grafana** is an open-source analytics and interactive visualization web application. It connects to Prometheus (and other data sources like Elasticsearch for logs) and allows you to build beautiful, real-time dashboards.

You can set up alerts in Grafana: "If the `rate(http_requests_total)` drops below 10 for more than 5 minutes, send a message to the team's Slack channel."

---

## Next Steps
Head to the `labs/` directory. We have a `docker-compose.yml` file that sets up both Prometheus and Grafana locally, so you can see how they connect!
