# Production Operations and JVM Cheatsheet

---

## 1. JVM Flags Quick Reference

| Flag | Purpose | Recommended Value / Example |
|---|---|---|
| `-Xms<size>` / `-Xmx<size>` | Initial and maximum heap size | `-Xms4g -Xmx4g` (Set equal in prod) |
| `-XX:+UseContainerSupport` | Container cgroups CPU/memory auto-detection | Enabled by default in Java 17+ |
| `-XX:MaxRAMPercentage` | Heap ceiling as % of container memory limit | `-XX:MaxRAMPercentage=75.0` |
| `-XX:MaxMetaspaceSize` | Bounds Metaspace native memory | `-XX:MaxMetaspaceSize=512m` |
| `-XX:+ExitOnOutOfMemoryError`| Immediately terminates JVM process on OOM | Fail-fast for orchestrator restart |
| `-XX:+HeapDumpOnOutOfMemoryError` | Automatically captures `.hprof` on OOM | Pair with `-XX:HeapDumpPath=/var/dumps` |
| `-XX:+AlwaysPreTouch` | Pre-faults heap pages into RAM at boot | Reduces runtime request latency spikes |

---

## 2. GC Algorithms Comparison

| Garbage Collector | HotSpot Flag | Pause Latency | Throughput | Primary Target Workload |
|---|---|---|---|---|
| G1GC | `-XX:+UseG1GC` | Predictable (20-150ms) | High | General microservices (Default) |
| Generational ZGC | `-XX:+UseZGC -XX:+ZGenerational` | Sub-millisecond (< 1ms) | Moderate-High | Strict P99 SLAs, large heaps (> 8GB) |
| Shenandoah | `-XX:+UseShenandoahGC` | Ultra-low (< 10ms) | Moderate | Low-latency latency-critical APIs |
| Parallel GC | `-XX:+UseParallelGC` | High (100ms - 2s+) | Maximum | Batch computations, offline ETL |

---

## 3. Micrometer Meter Types

| Meter Type | Characteristic | Usage Scenario | Core Metric Methods |
|---|---|---|---|
| `Counter` | Monotonically increments | Total HTTP requests, errors, events | `counter.increment()`, `increment(amount)` |
| `Gauge` | Arbitrary instantaneous float/int | Thread count, queue depth, heap used | `registry.gauge(name, targetObj, fn)` |
| `Timer` | Duration distribution + count | Endpoint response latency, DB queries | `timer.record(Duration)`, `timer.record(fn)` |
| `DistributionSummary` | Distribution of non-time units | Payload byte sizes, batch sizes | `summary.record(doubleAmount)` |

---

## 4. Flyway Migration Naming Convention

| Prefix | Pattern | Purpose | Re-execution Behavior |
|---|---|---|---|
| `V` | `V<Version>__<Description>.sql` | Versioned schema migration | Runs once; checksum locked forever |
| `U` | `U<Version>__<Description>.sql` | Undo previous version | Rolls back specified versioned step |
| `R` | `R__<Description>.sql` | Repeatable script (views/procs) | Re-runs whenever checksum changes |

*Example:* `db/migration/V2_1_0__create_audit_ledger_table.sql`

---

## 5. HikariCP Key Configuration Properties

| Property Name | Default | Recommended Production Value | Description |
|---|---|---|---|
| `maximumPoolSize` | 10 | `(cores * 2) + spindles` (e.g. 16) | Maximum active connections |
| `minimumIdle` | 10 | Equal to `maximumPoolSize` | Fixed pool prevents allocation spikes |
| `connectionTimeout` | 30000 | `10000` (10 seconds) | Max wait time before `SQLException` |
| `idleTimeout` | 600000 | `300000` (5 minutes) | Inactive connection lifetime |
| `maxLifetime` | 1800000 | `1800000` (30 minutes) | Max physical socket lifetime (< DB timeout) |
| `leakDetectionThreshold` | 0 | `4000` (4 seconds) | Warns when connection checked out > N ms |

---

## 6. Kubernetes Probes Configuration Template

```yaml
livenessProbe:
  httpGet:
    path: /actuator/health/liveness
    port: 8080
  initialDelaySeconds: 20
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 3
readinessProbe:
  httpGet:
    path: /actuator/health/readiness
    port: 8080
  initialDelaySeconds: 15
  periodSeconds: 5
  timeoutSeconds: 2
  failureThreshold: 2
```

---

## 7. Spring Boot Actuator Endpoints Reference

| Endpoint URI | Method | Production Purpose | Security Exposure |
|---|---|---|---|
| `/actuator/health` | GET | Aggregated health status (UP/DOWN) | Public / Restricted details |
| `/actuator/health/liveness` | GET | Kubernetes container liveness | Internal cluster only |
| `/actuator/health/readiness`| GET | Kubernetes traffic readiness | Internal cluster only |
| `/actuator/prometheus` | GET | OpenMetrics formatted scrape target | Scraped by Prometheus agents |
| `/actuator/metrics` | GET | List and inspect individual meters | Admin / Internal role |
| `/actuator/threaddump` | GET | Captures live thread stack traces | Admin only |
| `/actuator/env` | GET | Active profiles and environment vars | Strictly restricted / Sanitized |
