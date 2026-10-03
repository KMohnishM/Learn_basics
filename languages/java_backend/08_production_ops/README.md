# Production Operations and JVM Performance Engineering

This guide provides an exhaustive, production-grade reference for running, tuning, monitoring, and operating Java backend applications in high-throughput enterprise environments, Kubernetes clusters, and cloud-native infrastructure.

---

## Table of Contents
1. [JVM Memory Model](#1-jvm-memory-model)
2. [Garbage Collection Algorithms](#2-garbage-collection-algorithms)
3. [JVM Performance Tuning](#3-jvm-performance-tuning)
4. [GraalVM Native Image](#4-graalvm-native-image)
5. [Spring Boot on Kubernetes](#5-spring-boot-on-kubernetes)
6. [Micrometer Metrics](#6-micrometer-metrics)
7. [Distributed Tracing](#7-distributed-tracing)
8. [Database Migrations with Flyway](#8-database-migrations-with-flyway)
9. [Caching in Production](#9-caching-in-production)
10. [Connection Pool Tuning](#10-connection-pool-tuning)
11. [Spring Boot Performance Tips](#11-spring-boot-performance-tips)
12. [Health Checks and Readiness](#12-health-checks-and-readiness)
13. [Profiling and Heap Dumps](#13-profiling-and-heap-dumps)
14. [Production Checklist](#14-production-checklist)

---

## 1. JVM Memory Model

The Java Virtual Machine (HotSpot JVM) divides memory into distinct regions, each serving dedicated roles with specific allocation characteristics, garbage collection dynamics, and failure modes.

```
+-----------------------------------------------------------------------------------+
|                                  Total JVM Process Memory                         |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  |                             Java Heap Space                                 |  |
|  |                                                                             |  |
|  |  +---------------------------------------+  +----------------------------+  |  |
|  |  |               Young Gen               |  |          Old Gen           |  |  |
|  |  |  +--------------+  +----+  +----+     |  |       (Tenured Gen)        |  |  |
|  |  |  |  Eden Space  |  | S0 |  | S1 |     |  |                            |  |  |
|  |  |  +--------------+  +----+  +----+     |  |                            |  |  |
|  |  +---------------------------------------+  +----------------------------+  |  |
|  +-----------------------------------------------------------------------------+  |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  |                             Non-Heap Memory                                 |  |
|  |                                                                             |  |
|  |  +----------------+  +-------------------+  +-------------+  +-----------+  |  |
|  |  |   Metaspace    |  |    Code Cache     |  | Thread      |  | Off-Heap  |  |  |
|  |  |  (Class Meta)  |  |   (JIT Native)    |  | Stacks      |  | Direct IO |  |  |
|  |  +----------------+  +-------------------+  +-------------+  +-----------+  |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

### Memory Regions

1. **Young Generation (Heap):**
   - **Eden Space:** The landing area where all new object instances are initially allocated via `new`.
   - **Survivor Spaces (S0 / From and S1 / To):** Two identically sized spaces used during Minor GC copying. Live objects surviving Eden compaction alternate between S0 and S1. Objects surviving a specified number of Minor GC cycles (governed by `-XX:MaxTenuringThreshold`, default 15) are promoted to Old Generation.
2. **Old Generation / Tenured Space (Heap):**
   - Stores long-lived objects, singletons, application caches, connection pools, and long-lived data structures promoted from Survivor spaces. Major / Full GC cleans this region.
3. **Metaspace (Non-Heap):**
   - Replaced PermGen in Java 8. Resides in native host memory outside the Java heap. Stores runtime class definitions, method bytecode, constant pool tables, annotations, and method dispatch tables.
   - Defaults to expanding unbounded up to native OS limits unless bounded via `-XX:MaxMetaspaceSize`.
4. **Thread Stacks (Non-Heap):**
   - Dedicated memory allocated per OS/platform thread (`-Xss`, default 1MB on 64-bit platforms). Holds stack frames containing local primitive variables, object references, and return addresses.
5. **Code Cache (Non-Heap):**
   - Native memory region where the HotSpot JIT (Just-In-Time) compiler compiles interpreted Java bytecode into native machine instructions.
6. **Direct Memory / Off-Heap:**
   - Memory allocated via `ByteBuffer.allocateDirect()` (used heavily by Netty, gRPC, and Kafka clients) bypassing JVM garbage collection for zero-copy socket I/O.

### Memory Flags Reference

```bash
# Sizing Heap Space
-Xms4g                           # Initial Java heap size
-Xmx4g                           # Maximum Java heap size (set Xms=Xmx to prevent resizing pauses)

# Sizing Metaspace
-XX:MetaspaceSize=256m           # Initial threshold for GC of class metadata
-XX:MaxMetaspaceSize=512m        # Hard ceiling to prevent native host exhaustion

# Sizing Thread Stacks
-Xss1m                           # Per-thread stack size (lower for virtual thread heavy workloads)

# Off-Heap Limits
-XX:MaxDirectMemorySize=1g       # Bounds NIO direct buffer allocations
```

### OutOfMemoryError (OOM) Root Causes

| OOM Error Type | Root Cause | Diagnosis Strategy |
|---|---|---|
| `java.lang.OutOfMemoryError: Java heap space` | Heap full. Memory leak retaining dead objects in collections, or traffic spike exceeding `-Xmx`. | Inspect heap dump using Eclipse MAT; check dominator tree and retained size. |
| `java.lang.OutOfMemoryError: Metaspace` | Dynamic class generation leaking (CGLIB, Groovy scripts, reflection proxies, uncleaned hot-redeployments). | Take Metaspace dump via `jcmd <pid> VM.classloader_stats`; limit `-XX:MaxMetaspaceSize`. |
| `java.lang.OutOfMemoryError: GC overhead limit exceeded` | JVM spent more than 98% of total CPU time in GC recovering less than 2% of heap. | Application is thrashing at near-maximum heap capacity. Scale heap or fix memory leak. |
| `java.lang.OutOfMemoryError: unable to create new native thread` | Host OS process limit (`ulimit -u` / `max user processes`) reached or host out of native RAM for thread stacks. | Check `jstack`, review thread pool bounds, migrate to Java 21 Virtual Threads. |
| `java.lang.OutOfMemoryError: Direct buffer memory` | Netty or direct NIO buffers allocated faster than cleaned or leaking off-heap references. | Profile direct memory via `jcmd <pid> VM.native_memory baseline` and check Netty leak detection. |

---

## 2. Garbage Collection Algorithms

Choosing and tuning the Garbage Collector directly dictates latency, pause times, and overall throughput of enterprise Java services.

### Modern GC Collectors Overview

```
Collector Trade-off Spectrum:

High Throughput (Batch Processing)               Ultra-Low Latency (Real-time APIs)
<--------------------------------------------------------------------------------->
Parallel GC             G1 GC (Default Java 9+)         Shenandoah GC / ZGC
(Full stop-the-world)    (Region-based, balanced)        (Concurrent evacuation, <1ms)
```

1. **Parallel GC (`-XX:+UseParallelGC`):**
   - Multi-threaded Stop-The-World (STW) collector. Maximizes throughput by dedicating 100% of CPU cores to GC during pauses.
   - Best for offline batch jobs, ETL pipelines, and non-interactive data processing where 500ms+ pause times are acceptable.
2. **Garbage-First (G1) GC (`-XX:+UseG1GC`):**
   - Default collector since Java 9. Divides the heap into 2,048 equal contiguous regions (1MB to 32MB each).
   - Dynamically designates regions as Eden, Survivor, or Old. Prioritizes collecting regions containing the most dead objects ("garbage first").
   - Meets a target pause time goal (`-XX:MaxGCPauseMillis=200`) using incremental, parallel, and concurrent phases.
3. **ZGC (Z Garbage Collector) (`-XX:+UseZGC`):**
   - Scalable low-latency collector introduced in Java 11, production-ready in Java 15, and generational in Java 21 (`-XX:+UseZGC -XX:+ZGenerational`).
   - Performs all heavy GC work concurrently: marking, reference processing, and relocation/compaction.
   - Guarantees sub-millisecond maximum pause times regardless of heap size (from 16MB to 16TB).
4. **Shenandoah GC (`-XX:+UseShenandoahGC`):**
   - Ultra-low latency collector developed by Red Hat. Performs concurrent evacuation alongside running application mutator threads using Brooks load-reference pointers.

### GC Tuning Flags Reference

```bash
# Recommended production flags for G1GC (Spring Boot default baseline)
-XX:+UseG1GC
-XX:MaxGCPauseMillis=150
-XX:InitiatingHeapOccupancyPercent=45
-XX:G1ReservePercent=15
-XX:G1HeapRegionSize=16m

# Low-latency configuration using Generational ZGC (Java 21+)
-XX:+UseZGC
-XX:+ZGenerational
-XX:SoftMaxHeapSize=12g
```

### Modern GC Unified Logging (`-Xlog`)

Java 9+ unified JVM logging replaces legacy `-XX:+PrintGCDetails`.

```bash
# Comprehensive production GC logging configuration
-Xlog:gc*,gc+phases=debug,gc+safepoint=info:file=/var/log/jvm/gc-%t.log:time,uptime,pid:filecount=5,filesize=50M
```

Sample GC log entry:
```
[2026-11-07T08:14:22.104+0000][0.845s][14210][info][gc,start    ] GC(14) Pause Young (Normal) (G1 Evacuation Pause)
[2026-11-07T08:14:22.118+0000][0.859s][14210][info][gc          ] GC(14) Pause Young (Normal) (G1 Evacuation Pause) 2048M->512M(4096M) 14.120ms
[2026-11-07T08:14:22.118+0000][0.859s][14210][info][gc,cpu      ] GC(14) User=0.08s Sys=0.01s Real=0.01s
```

---

## 3. JVM Performance Tuning

Optimizing HotSpot runtime behavior involves understanding JIT compilation tiers and leveraging live diagnosis tooling.

### Just-In-Time (JIT) Compilation and Tiered Compilation

HotSpot executes bytecode through an interpreter initially, counting method invocations and loop back-edges. Once thresholds are crossed, JIT compiles hot code into native instructions:
- **Tier 0:** Interpreted bytecode.
- **Tier 1 to 3 (C1 Compiler / Client Compiler):** Fast compilation with light profiling counters. Rapid startup.
- **Tier 4 (C2 Compiler / Server Compiler):** Aggressive optimizations (inlining, loop unrolling, escape analysis, dead code elimination, devirtualization). High runtime throughput.

Tiered compilation is enabled by default (`-XX:+TieredCompilation`). In containerized environments with short lifecycles, understanding compilation warmup is critical.

### Production Diagnostic CLI Tools

```bash
# 1. Inspect live JVM properties and memory overview
jcmd <PID> VM.version
jcmd <PID> VM.flags -all
jcmd <PID> GC.heap_info

# 2. Track garbage collection activity in real time (every 1000ms)
jstat -gcutil <PID> 1000 10

# 3. Capture thread dumps for deadlock and contention analysis
jcmd <PID> Thread.print > /tmp/thread-dump.txt
# Alternatively:
jstack -l <PID> > /tmp/thread-dump.txt

# 4. Trigger on-demand heap dump for memory leak investigation
jcmd <PID> GC.heap_dump /var/dumps/heap-dump.hprof

# 5. Native Memory Tracking (NMT) to isolate non-heap memory leaks
# Start JVM with: -XX:NativeMemoryTracking=summary
jcmd <PID> VM.native_memory baseline
# Later, compare against baseline:
jcmd <PID> VM.native_memory detail.diff
```

---

## 4. GraalVM Native Image

GraalVM Native Image compiles Java bytecode Ahead-of-Time (AOT) into a self-contained, standalone platform-native binary (e.g., Linux ELF binary), completely bypassing the JVM runtime.

### Architectural Trade-offs

| Characteristic | Standard OpenJDK JVM | GraalVM Native Image |
|---|---|---|
| Startup Time | 1.5s to 15s (class loading, verification, JIT) | 0.005s to 0.050s (sub-50ms instant start) |
| Memory Footprint (RSS) | 250MB to 1GB+ base memory | 25MB to 80MB base memory |
| Peak Throughput | Maximum (C2 JIT runtime profiling optimization) | Slightly lower (no runtime profile-guided JIT) |
| Build Duration | Seconds (`mvn package`) | 3 to 10+ minutes (AOT static closed-world analysis) |
| Dynamic Reflection | Unrestricted at runtime | Requires build-time reachability configuration |

### Handling Reflection and Dynamic Proxies

GraalVM enforces the **Closed-World Assumption**: all classes, methods, and reflection calls must be discoverable during static compilation analysis. Code relying on dynamic class loading fails at runtime unless registered.

Spring Boot 3 introduces first-class AOT engine support via `@RegisterReflectionForBinding`:

```java
package com.example.ops.nativeimg;

import org.springframework.aot.hint.RuntimeHints;
import org.springframework.aot.hint.RuntimeHintsRegistrar;
import org.springframework.context.annotation.ImportRuntimeHints;
import org.springframework.stereotype.Service;

import java.io.Serializable;

// Domain record requiring reflection registration for third-party serialization
public record FinancialPayload(String transactionId, double amount, String currency) implements Serializable {}

// Custom Runtime Hints Registrar for GraalVM AOT Compilation
public class FinancialServiceRuntimeHints implements RuntimeHintsRegistrar {
    @Override
    public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
        hints.reflection().registerType(FinancialPayload.class,
                builder -> builder.withMembers(
                        org.springframework.aot.hint.MemberCategory.INVOKE_PUBLIC_CONSTRUCTORS,
                        org.springframework.aot.hint.MemberCategory.INVOKE_PUBLIC_METHODS
                ));
        hints.resources().registerPattern("certificates/prod-public-key.pem");
    }
}

@Service
@ImportRuntimeHints(FinancialServiceRuntimeHints.class)
public class NativePaymentProcessor {
    public void process(FinancialPayload payload) {
        // Business logic running inside native binary
    }
}
```

---

## 5. Spring Boot on Kubernetes

Running Java inside containerized environments (Docker, Podman, Kubernetes) requires strict container resource awareness and lifecycle integration.

### Container Resource Awareness

Legacy Java runtimes misread container CPU and memory cgroups, calculating heap allocations based on the underlying bare-metal host rather than container limits. Modern OpenJDK (11.0.16+, 17+, 21+) includes native container detection:

```bash
# Recommended production JVM container execution entrypoint
java \
  -XX:+UseContainerSupport \
  -XX:MaxRAMPercentage=75.0 \
  -XX:InitialRAMPercentage=75.0 \
  -XX:MinRAMPercentage=50.0 \
  -XX:+ExitOnOutOfMemoryError \
  -Djava.security.egd=file:/dev/./urandom \
  -jar /app/application.jar
```

### Kubernetes Health Probes Configuration

Spring Boot Actuator integrates natively with Kubernetes liveness and readiness states.

*`application.yml`:*
```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,prometheus,metrics
  endpoint:
    health:
      probes:
        enabled: true
      show-details: when_authorized
  health:
    livenessstate:
      enabled: true
    readinessstate:
      enabled: true
server:
  shutdown: graceful
spring:
  lifecycle:
    timeout-per-shutdown-phase: 30s
```

*Production Kubernetes Deployment Manifest (`deployment.yaml`):*

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
  namespace: production
  labels:
    app: order-service
spec:
  replicas: 4
  selector:
    matchLabels:
      app: order-service
  template:
    metadata:
      labels:
        app: order-service
    spec:
      containers:
        - name: order-service
          image: registry.internal.net/order-service:1.4.2
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8080
              name: http
            - containerPort: 8081
              name: management
          resources:
            requests:
              memory: "1024Mi"
              cpu: "500m"
            limits:
              memory: "1536Mi"
              cpu: "2000m"
          env:
            - name: SPRING_PROFILES_ACTIVE
              value: "production"
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: postgres-password
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
          startupProbe:
            httpGet:
              path: /actuator/health/liveness
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 5
            failureThreshold: 12
```

---

## 6. Micrometer Metrics

Micrometer is the vendor-neutral metrics facade for JVM applications, analogous to SLF4J for logging. It exposes metrics to monitoring systems like Prometheus, Datadog, and InfluxDB.

### Core Meter Types

1. **Counter:** Monotonically increasing metric tracking cumulative frequency (e.g., total requests, errors).
2. **Gauge:** Current instantaneous value that can increase or decrease (e.g., active thread count, queue size).
3. **Timer:** Measures short durations alongside event counts (e.g., HTTP latency, database query time).
4. **DistributionSummary:** Tracks distribution of non-time values (e.g., payload size in bytes).

### Production Micrometer Implementation

```java
package com.example.ops.metrics;

import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.DistributionSummary;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import org.springframework.stereotype.Service;

import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

@Service
public class OrderMetricsService {

    private final Counter successfulOrdersCounter;
    private final Counter failedOrdersCounter;
    private final Timer orderProcessingTimer;
    private final DistributionSummary payloadSizeSummary;
    private final AtomicInteger pendingOrdersQueueGauge;

    public OrderMetricsService(MeterRegistry registry) {
        this.successfulOrdersCounter = Counter.builder("business.orders.created")
                .description("Total successfully created orders")
                .tag("region", "us-east")
                .tag("channel", "web")
                .register(registry);

        this.failedOrdersCounter = Counter.builder("business.orders.failed")
                .description("Total failed order operations")
                .tag("reason", "validation_error")
                .register(registry);

        this.orderProcessingTimer = Timer.builder("business.orders.processing.time")
                .description("Latency distribution of order processing")
                .publishPercentiles(0.50, 0.95, 0.99)
                .publishPercentileHistogram()
                .register(registry);

        this.payloadSizeSummary = DistributionSummary.builder("business.orders.payload.bytes")
                .baseUnit("bytes")
                .maximumExpectedValue(10_000_000.0)
                .register(registry);

        this.pendingOrdersQueueGauge = registry.gauge(
                "business.orders.queue.depth",
                new AtomicInteger(0)
        );
    }

    public void recordOrderPlaced(int payloadBytes, long durationNanos) {
        successfulOrdersCounter.increment();
        payloadSizeSummary.record(payloadBytes);
        orderProcessingTimer.record(durationNanos, TimeUnit.NANOSECONDS);
    }

    public void updateQueueDepth(int depth) {
        pendingOrdersQueueGauge.set(depth);
    }
}
```

### Essential PromQL Alert Queries

```promql
# 1. HTTP P99 Latency over 5m window exceeding 500ms
histogram_quantile(0.99, sum(rate(http_server_requests_seconds_bucket[5m])) by (le)) > 0.5

# 2. JVM Heap Utilization exceeding 85%
(jvm_memory_used_bytes{area="heap"} / jvm_memory_max_bytes{area="heap"}) * 100 > 85

# 3. Connection Pool Exhaustion (Active threads waiting for connection)
hikaricp_connections_pending > 0
```

---

## 7. Distributed Tracing

Distributed tracing tracks the execution flow of requests traversing microservice topologies. Micrometer Tracing (introduced in Spring Boot 3, succeeding Spring Cloud Sleuth) standardizes span and trace collection.

```
Client ---> [ Order Service ] (TraceId: T1, SpanId: S1)
                  |
                  v HTTP Request (Headers: traceparent=00-T1-S2-01)
            [ Payment Service ] (TraceId: T1, SpanId: S2)
                  |
                  v gRPC Call (Headers: traceparent=00-T1-S3-01)
            [ Fraud Service ] (TraceId: T1, SpanId: S3)
```

### TraceId vs SpanId

- **TraceId:** A globally unique 128-bit or 64-bit hexadecimal identifier assigned when an external request enters the system boundary. Retained across all downstream network calls.
- **SpanId:** Represents a single unit of contiguous work within a specific service boundary.
- **Baggage:** Key-value pairs propagated across network boundaries alongside trace context (e.g., `tenant-id`).

### Micrometer Tracing Configuration and Custom Spans

```java
package com.example.ops.tracing;

import io.micrometer.tracing.BaggageInScope;
import io.micrometer.tracing.Span;
import io.micrometer.tracing.Tracer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class SettlementTracingService {

    private static final Logger log = LoggerFactory.getLogger(SettlementTracingService.class);
    private final Tracer tracer;

    public SettlementTracingService(Tracer tracer) {
        this.tracer = tracer;
    }

    public void executeSettlement(String settlementId, String customerTier) {
        // Create custom span
        Span newSpan = tracer.nextSpan().name("executeSettlementCalculation").start();

        try (Tracer.SpanInScope ws = tracer.withSpan(newSpan.start())) {
            // Attach contextual baggage propagated downstream
            try (BaggageInScope baggage = tracer.createBaggageInScope("customer.tier", customerTier)) {
                newSpan.tag("settlement.id", settlementId);

                log.info("Processing settlement within custom tracing span.");
                performFinancialMath(settlementId);
            }
        } catch (Exception ex) {
            newSpan.error(ex);
            throw ex;
        } finally {
            newSpan.end(); // Stop span timing
        }
    }

    private void performFinancialMath(String id) {
        // Computational work
    }
}
```

*Logback pattern capturing TraceId and SpanId (`logback-spring.xml`):*
```xml
<pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %-5level [%X{traceId:-},%X{spanId:-}] %logger{36} - %msg%n</pattern>
```

---

## 8. Database Migrations with Flyway

Flyway delivers versioned, deterministic database schema evolution. Migration files execute sequentially, logging checksums into the `flyway_schema_history` metadata table.

### Migration Script Naming Convention

```
V1_0_0__create_customer_schema.sql
|  | |  |  |
|  | |  |  `-- Description (words separated by underscores)
|  | |  `----- Separator (EXACTLY two underscores: __)
|  `-`-------- Version number (periods or underscores represent dots)
`------------- Prefix: V (Versioned), U (Undo), R (Repeatable)
```

- **Versioned (`V`):** Executes exactly once. Modifying an already-executed versioned script triggers a checksum validation error.
- **Repeatable (`R`):** Executes whenever its content checksum changes. Ideal for stored procedures, views, and functions.
- **Undo (`U`):** Reverts associated versioned migration (Flyway Enterprise).

### Production Flyway Configuration

*`application.yml`:*
```yaml
spring:
  flyway:
    enabled: true
    baseline-on-migrate: true
    baseline-version: "0"
    locations: classpath:db/migration,classpath:db/custom
    validate-on-migrate: true
    out-of-order: false
    clean-disabled: true # MANDATORY IN PRODUCTION to prevent accidental DROP DATABASE
```

### Resolving Migration Checksum Failures

If a developer accidentally edits an already applied migration script, Flyway halts boot with:
`FlywayException: Validate failed: Migration checksum mismatch for migration version 1.2.0`

**Resolution Workflow:**
1. Revert the file edits to match the exact applied state.
2. If the change was legitimate and executed manually in database:
```bash
mvn flyway:repair
# Or CLI:
flyway -url=jdbc:postgresql://host:5432/db -user=app -password=secret repair
```

---

## 9. Caching in Production

In-memory caching reduces database query pressure and improves latency, but introduces critical cache consistency challenges.

### Spring Cache Configuration with Redis

```java
package com.example.ops.cache;

import org.springframework.boot.autoconfigure.cache.RedisCacheManagerBuilderCustomizer;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.CachePut;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.cache.RedisCacheConfiguration;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.RedisSerializationContext;
import org.springframework.stereotype.Service;

import java.io.Serializable;
import java.time.Duration;

public record UserProfileDto(Long id, String email, String status) implements Serializable {}

@Configuration
public class RedisCacheConfigurationSetup {

    @Bean
    public RedisCacheManagerBuilderCustomizer redisCacheManagerBuilderCustomizer() {
        return builder -> builder
                .withCacheConfiguration("users",
                        RedisCacheConfiguration.defaultCacheConfig()
                                .entryTtl(Duration.ofMinutes(15))
                                .disableCachingNullValues()
                                .serializeValuesWith(RedisSerializationContext.SerializationPair
                                        .fromSerializer(new GenericJackson2JsonRedisSerializer())))
                .withCacheConfiguration("exchangeRates",
                        RedisCacheConfiguration.defaultCacheConfig()
                                .entryTtl(Duration.ofHours(1)));
    }
}

@Service
public class UserProfileService {

    @Cacheable(value = "users", key = "#userId", unless = "#result == null")
    public UserProfileDto fetchUserProfile(Long userId) {
        // Heavy database query executes only on cache miss
        return queryDatabase(userId);
    }

    @CachePut(value = "users", key = "#dto.id()")
    public UserProfileDto updateUserProfile(UserProfileDto dto) {
        updateDatabase(dto);
        return dto; // Refreshes cached entry
    }

    @CacheEvict(value = "users", key = "#userId")
    public void deleteUserProfile(Long userId) {
        deleteFromDatabase(userId);
    }

    private UserProfileDto queryDatabase(Long id) { return new UserProfileDto(id, "user@test.org", "ACTIVE"); }
    private void updateDatabase(UserProfileDto dto) {}
    private void deleteFromDatabase(Long id) {}
}
```

### Cache Stampede (Thundering Herd) Mitigation

A **Cache Stampede** occurs when a highly requested cache key expires under heavy concurrent load, causing hundreds of concurrent requests to hit the underlying database simultaneously.

**Mitigation Strategies:**
1. **Distributed Mutex / Lock:** Only one thread recomputes the cache; other threads wait.
2. **Probabilistic Early Expiration (XFetch algorithm):** Recompute cache asynchronously before actual TTL expiration based on request probability.

```java
package com.example.ops.cache;

import org.redisson.api.RLock;
import org.redisson.api.RedissonClient;
import org.springframework.stereotype.Service;

import java.util.concurrent.TimeUnit;
import java.util.function.Supplier;

@Service
public class ResilientCacheFetcher {

    private final RedissonClient redissonClient;

    public ResilientCacheFetcher(RedissonClient redissonClient) {
        this.redissonClient = redissonClient;
    }

    public <T> T fetchWithStampedeProtection(String cacheKey, Supplier<T> dbFallback) {
        // Attempt fast cache lookup (pseudo-code)
        T cachedValue = getFromCache(cacheKey);
        if (cachedValue != null) {
            return cachedValue;
        }

        // Cache miss: acquire distributed lock to recompute
        RLock lock = redissonClient.getLock("lock:" + cacheKey);
        try {
            if (lock.tryLock(5, 10, TimeUnit.SECONDS)) {
                try {
                    // Double-check after lock acquisition
                    cachedValue = getFromCache(cacheKey);
                    if (cachedValue != null) return cachedValue;

                    T computed = dbFallback.get();
                    putInCache(cacheKey, computed);
                    return computed;
                } finally {
                    lock.unlock();
                }
            } else {
                // Fallback or retry cache fetch
                return getFromCache(cacheKey);
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new RuntimeException("Cache fetch interrupted", e);
        }
    }

    @SuppressWarnings("unchecked")
    private <T> T getFromCache(String key) { return null; }
    private <T> void putInCache(String key, T value) {}
}
```

---

## 10. Connection Pool Tuning

HikariCP is the default JDBC connection pool in Spring Boot. Improper pool configuration causes thread starvation, connection leaks, and database saturation.

### Sizing Formula

Allocating excessive connections harms performance due to CPU core contention and disk queue saturation.

$$\text{maximumPoolSize} = (\text{CPU Cores} \times 2) + \text{Effective Spindle Count}$$

For a database instance running on an 8-core CPU with fast NVMe storage:
$$\text{maximumPoolSize} = (8 \times 2) + 1 = 17$$

### Production `application.yml` Tuning

```yaml
spring:
  datasource:
    hikari:
      pool-name: OrdersHikariPool
      maximum-pool-size: 16
      minimum-idle: 16 # Fixed pool sizing eliminates allocation latency spikes
      connection-timeout: 10000 # 10 seconds before throwing SQLException
      idle-timeout: 300000 # 5 minutes
      max-lifetime: 1800000 # 30 minutes (must be < database wait_timeout)
      leak-detection-threshold: 5000 # Logs warning if connection checked out > 5s
      auto-commit: true
      data-source-properties:
        cachePrepStmts: true
        prepStmtCacheSize: 250
        prepStmtCacheSqlLimit: 2048
        useServerPrepStmts: true
```

---

## 11. Spring Boot Performance Tips

Optimizing Spring Boot for enterprise throughput requires modern concurrency settings and streamlined configuration.

### 1. Enabling Virtual Threads (Java 21+)

Virtual threads (Project Loom) eliminate thread-per-request blocking overhead, allowing applications to process tens of thousands of concurrent I/O operations on minimal hardware.

```yaml
# In Spring Boot 3.2+ / Java 21:
spring:
  threads:
    virtual:
      enabled: true
```

### 2. Lazy Initialization

Defers bean creation until the bean is first requested, dramatically reducing startup time for development and local testing.

```yaml
spring:
  main:
    lazy-initialization: false # Keep false in production to fail-fast on startup
```

### 3. Dedicated Custom Thread Pools for `@Async`

Never rely on Spring's default `SimpleAsyncTaskExecutor` (which spawns a new unpooled thread per invocation).

```java
package com.example.ops.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

import java.util.concurrent.Executor;
import java.util.concurrent.ThreadPoolExecutor;

@Configuration
@EnableAsync
public class AsyncThreadPoolConfig {

    @Bean(name = "productionTaskExecutor")
    public Executor productionTaskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(16);
        executor.setMaxPoolSize(64);
        executor.setQueueCapacity(500);
        executor.setThreadNamePrefix("ProdAsyncWorker-");
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        executor.setWaitForTasksToCompleteOnShutdown(true);
        executor.setAwaitTerminationSeconds(30);
        executor.initialize();
        return executor;
    }
}
```

---

## 12. Health Checks and Readiness

Kubernetes relies on probes to orchestrate pod lifecycles. Health indicators inform the orchestrator whether traffic can be routed or if the container must be restarted.

### Custom HealthIndicator Implementation

```java
package com.example.ops.health;

import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.HealthIndicator;
import org.springframework.stereotype.Component;

import java.net.InetSocketAddress;
import java.net.Socket;

@Component("downstreamPaymentGatewayHealthIndicator")
public class DownstreamPaymentGatewayHealthIndicator implements HealthIndicator {

    private static final String GATEWAY_HOST = "payment-gateway.internal.net";
    private static final int GATEWAY_PORT = 443;
    private static final int TIMEOUT_MS = 2000;

    @Override
    public Health health() {
        try (Socket socket = new Socket()) {
            socket.connect(new InetSocketAddress(GATEWAY_HOST, GATEWAY_PORT), TIMEOUT_MS);
            return Health.up()
                    .withDetail("gateway", GATEWAY_HOST)
                    .withDetail("latencyStatus", "NOMINAL")
                    .build();
        } catch (Exception e) {
            return Health.down()
                    .withDetail("gateway", GATEWAY_HOST)
                    .withDetail("error", e.getMessage())
                    .build();
        }
    }
}
```

### Health Groups Configuration

Segment probes so transient downstream service failures do not cause Kubernetes to kill and restart healthy pods.

```yaml
management:
  endpoint:
    health:
      group:
        readiness:
          include: db,redis,downstreamPaymentGatewayHealthIndicator
        liveness:
          include: ping,livenessState
```

---

## 13. Profiling and Heap Dumps

Diagnosing production latency regressions and memory leaks requires non-intrusive profiling and heap dump extraction.

### Capturing Heap Dumps

```bash
# Capture heap dump using jcmd
jcmd <PID> GC.heap_dump /var/dumps/heap_analysis.hprof

# Trigger automatic heap dump on OutOfMemoryError
# Add to JVM startup arguments:
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/var/dumps/oom_dump.hprof
```

### Analyzing Dumps with Eclipse MAT

1. Open `.hprof` in Eclipse Memory Analyzer Tool (MAT).
2. Generate **Leak Suspects Report**.
3. Inspect the **Dominator Tree**: identifies top objects retaining the largest total heap memory (Retained Size vs Shallow Size).
4. Run OQL (Object Query Language) to inspect leaked objects:
```sql
SELECT c FROM com.example.model.CustomerSession c WHERE c.active = false
```

### Continuous Profiling with Java Flight Recorder (JFR)

JFR runs inside the JVM kernel with under 1% overhead, capturing CPU usage, lock contention, allocation hotspots, and I/O pauses.

```bash
# Start a 5-minute production profiling recording
jcmd <PID> JFR.start name=ProdAudit duration=300s filename=/tmp/audit.jfr settings=profile.jfc

# Dump live recording on demand
jcmd <PID> JFR.dump name=ProdAudit filename=/tmp/audit_snapshot.jfr

# Stop recording
jcmd <PID> JFR.stop name=ProdAudit
```

Open the resulting `.jfr` file in **JDK Mission Control (JMC)** or analyze with async-profiler flame graphs to isolate lock contention and GC allocation hotspots.

---

## 14. Production Checklist

Ensure all items are verified before production release:

1. **Structured JSON Logging:** Use Logstash Logback encoder to output unified JSON logs containing `timestamp`, `level`, `traceId`, `spanId`, and `threadName`.
2. **Externalized Secrets:** Never hardcode credentials. Inject passwords via Kubernetes Secrets, HashiCorp Vault, or AWS Secrets Manager.
3. **Resilience & Circuit Breaking:** Guard external downstream integrations with Resilience4j circuit breakers, timeouts, and fallbacks.
4. **Rate Limiting:** Protect APIs against abuse using Bucket4j token bucket algorithms or API Gateway rate limits.
5. **Graceful Shutdown:** Enable `server.shutdown=graceful` with a 30s timeout to allow in-flight requests to complete before pod termination.
6. **Connection Pool Sizing:** Explicitly configure HikariCP bounds and set `leak-detection-threshold`.
7. **Stateless Scalability:** Store no user session state in local JVM memory; offload sessions to distributed caches (Redis).
8. **GC Tuning & OutOfMemory Handling:** Explicitly set `-XX:+ExitOnOutOfMemoryError` and configure `-XX:MaxRAMPercentage`.
