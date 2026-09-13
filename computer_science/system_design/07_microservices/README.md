# Module 7: Microservices Architecture and Distributed Systems

> **Goal**: Understand the architectural transition from monoliths to microservices, how to design resilient distributed systems, and the operational complexity required to run them in production. This module goes beyond high-level theory and covers the practical, concrete details of service boundaries, API contracts, network resilience, and distributed data management.

---

## Table of Contents

1. [Monolith vs Microservices vs Serverless](#1-monolith-vs-microservices-vs-serverless)
2. [Service Boundaries (Domain-Driven Design)](#2-service-boundaries-domain-driven-design)
3. [API Design](#3-api-design)
4. [API Gateway Pattern](#4-api-gateway-pattern)
5. [Service Discovery](#5-service-discovery)
6. [Resilience Patterns](#6-resilience-patterns)
7. [Service Mesh](#7-service-mesh)
8. [Distributed Tracing & Observability](#8-distributed-tracing--observability)
9. [Data Management Across Services](#9-data-management-across-services)
10. [Deployment Strategies](#10-deployment-strategies)
11. [Appendix: Code & Config Examples](#11-appendix-code--config-examples)

---

## 1. Monolith vs Microservices vs Serverless

Choosing the right architectural style is the most consequential decision in system design. There is no silver bullet; each pattern optimizes for different constraints, primarily team topology and deployment frequency.

### 1.1 The Monolithic Architecture

A monolith is a single deployable unit containing all business logic, UI serving, background jobs, and database access code.

**When it's the RIGHT choice:**
- **Early Stage Startups**: When product-market fit is unproven, iteration speed is paramount.
- **Small Teams**: A team of 5-15 engineers will be significantly slowed down by microservice operational overhead.
- **Tight Domain Coupling**: If domain boundaries are unclear or shifting rapidly, a monolith allows easy, IDE-assisted refactoring.
- **Conway's Law**: "Organizations design systems that mirror their own communication structure." A single cohesive team naturally builds a well-structured monolith.

**The Breaking Point:**
Monoliths typically fail when team size exceeds 50-100 engineers.
- Deployment coordination becomes a nightmare (release trains, merge conflicts).
- Build and CI times exceed 30-45 minutes.
- A single memory leak in a minor module (e.g., PDF generation) crashes the entire application, taking down checkout flows.
- Vertical scaling (buying bigger EC2 instances) hits practical and financial limits.

### 1.2 Microservices Architecture

Microservices divide the application into independently deployable, loosely coupled services organized around specific business capabilities.

**Key Characteristics:**
- **Independent Deployment**: Service A can deploy without coordinating with Service B.
- **Team Autonomy**: Small teams (two-pizza teams) own a service end-to-end (build, test, deploy, monitor).
- **Polyglot Stack**: The ML team can use Python, the high-throughput gateway uses Go, and the legacy enterprise system uses Java.
- **Fault Isolation**: A crash in the Review service does not affect the core Checkout service.

**The Operational Cost (The Microservices Premium):**
You are trading software complexity (spaghetti code) for operational complexity (spaghetti networks). You now require:
- Automated CI/CD pipelines for 50+ repositories.
- Centralized logging and distributed tracing.
- Advanced monitoring, alerting, and on-call rotations.
- Network security, mTLS, and identity management between services.

### 1.3 Serverless (Function-as-a-Service)

Serverless (e.g., AWS Lambda, Google Cloud Functions) abstracts away infrastructure entirely. You write business logic; the cloud provider scales it dynamically from 0 to 10,000 concurrent executions.

**Key Characteristics:**
- **Event-driven**: Triggered by HTTP requests, queue messages, object storage uploads, or database stream events.
- **Scale-to-Zero**: You pay only for execution time (down to the millisecond) and memory consumed.
- **The Cold Start Problem**: When a function scales from 0 to 1, the provider must allocate a container, initialize the runtime (e.g., JVM, Node), and load your code.
  - *Metrics*: A Node.js cold start might take 200-500ms. A Java/Spring Boot cold start can take 2-5 seconds.
  - *Solutions*: Provisioned Concurrency (keeping containers warm at a cost), or using native compilation (e.g., GraalVM) to reduce startup times to <50ms.

### 1.4 Decision Matrix

| Constraint | Monolith | Microservices | Serverless |
| :--- | :--- | :--- | :--- |
| **Team Size** | 1-20 engineers | 50+ engineers | Any (great for small/medium) |
| **Deployment Freq.** | Weekly / Monthly | Multiple times a day | Multiple times a day |
| **Domain Complexity**| Low to Medium | High | Variable |
| **Data Ownership** | Shared Database | Database per Service | Cloud Native DBs (DynamoDB) |
| **Operational Overhead**| Low | Extremely High | Low (Provider handles it) |
| **Scaling Granularity**| Whole app scales | Service-level scaling | Function-level scaling |

### 1.5 The Strangler Fig Pattern

Migrating from a monolith to microservices is dangerous if done as a "big bang" rewrite. The **Strangler Fig Pattern** (named by Martin Fowler after the tree that grows around and replaces a host tree) is the industry standard for safe, incremental migration.

```text
Strangler Fig Migration (ASCII Diagram):

Phase 1: Initial State        Phase 2: Strangling Begins     Phase 3: Completion
                                                             
[ Clients ]                   [ Clients ]                    [ Clients ]
    |                              |                              |
    v                              v                              v
[ API Gateway ]               [ API Gateway ]                [ API Gateway ]
    |                              | \                            |   |   |
    |                              |  \                           v   v   v
    v                              v   v                     [ Svc A ][ Svc B ][ Svc C ]
[ Monolith ]                  [ Monolith ] [ Svc A ]              
```

**Steps:**
1. Put an API Gateway (or reverse proxy like Nginx) in front of the monolith.
2. Identify a bounded context to extract (e.g., Billing).
3. Build the new Billing Microservice alongside the monolith.
4. Route `/billing/*` traffic at the Gateway to the new service; route everything else to the monolith.
5. Repeat until the monolith handles no traffic and can be decommissioned.

---

## 2. Service Boundaries (Domain-Driven Design)

The hardest part of microservices is drawing the correct boundaries. If you draw them wrong, you build a "distributed monolith" where every deployment requires updating five services simultaneously, losing all the benefits of microservices while paying all the operational costs.

### 2.1 Bounded Contexts

Coined in Domain-Driven Design (DDD) by Eric Evans, a **Bounded Context** is a conceptual boundary within which a specific domain model is defined and applicable.

- **Example**: The concept of a "Product" means entirely different things depending on the context.
  - *Inventory Context*: A Product is a physical item with dimensions, weight, warehouse location, and SKU.
  - *E-commerce Context*: A Product is an item with a title, description, price, and customer reviews.
- **Rule**: Services should share NOTHING. They communicate strictly via APIs or asynchronous events. Do not share code libraries that contain business logic (sharing a logging library is fine; sharing a `PricingCalculator` library leads to tight coupling).

### 2.2 Ubiquitous Language

The terminology used in the code must precisely match the terminology used by domain experts (business stakeholders). If the business calls it a "Subscription," the database table, class name, and API endpoint must all use "Subscription," not "RecurringPlan" or "UserBillingCycle." This eliminates translation overhead during requirements gathering and debugging.

### 2.3 Aggregates and Transaction Boundaries

An **Aggregate** is a cluster of domain objects that are treated as a single unit for data changes. It defines the transactional consistency boundary.
- An Aggregate has a "Root" entity. External objects only hold references to the Root.
- If an Aggregate is updated, all its internal state must be consistent immediately upon database commit.
- A microservice should ideally own one or more Aggregates. Transactions should not span multiple Aggregates.

### 2.4 Anti-Corruption Layer (ACL)

When a modern microservice needs to communicate with a legacy system that uses a poorly designed or incompatible data model, you build an ACL.
- The ACL is an adapter, facade, or translation layer.
- It translates requests from the new domain model into the legacy format, and responses back into the new model.
- It prevents the legacy system's bad concepts from "leaking" and corrupting the new service's clean domain model.

### 2.5 Data Ownership (The Database-per-Service Pattern)

**CRITICAL RULE**: Microservices must NOT share a single database. 

If Service A and Service B read and write to the same database tables:
- Service A cannot change its schema without coordinating with Service B's team (breaking independent deployment).
- A long-running analytical query in Service B can lock rows or exhaust connection pools needed by Service A.
- You have failed to achieve loose coupling.

Each service must have its own logical database. If Service A needs Service B's data, it must call Service B's API or subscribe to Service B's published events.

---

## 3. API Design

Microservices communicate over networks. The design of these APIs dictates the performance, evolvability, and usability of the system.

### 3.1 REST (Representational State Transfer)

REST is the industry standard for external-facing APIs. It is resource-oriented, stateless, and leverages standard HTTP verbs (GET, POST, PUT, PATCH, DELETE).

**Richardson Maturity Model**:
- **Level 0**: Swamp of POX (Plain Old XML/JSON). Using HTTP just as a transport mechanism, often with a single endpoint (e.g., `POST /api` with an action payload).
- **Level 1**: Resources. Introduce endpoints per resource (e.g., `/users/123`).
- **Level 2**: HTTP Verbs. Standardize actions (GET to read, DELETE to remove, POST to create, PUT to replace entirely).
- **Level 3**: HATEOAS (Hypermedia As The Engine Of Application State). Responses include links to discoverable actions (e.g., `{ "id": 123, "links": [{"rel": "self", "href": "/users/123"}] }`). This is rarely fully implemented in pragmatic production systems.

**Versioning Strategies**:
- **URL Path**: `https://api.example.com/v1/users` (Most common, pragmatic, easily routable at the API Gateway).
- **Header**: `Accept: application/vnd.example.v1+json` (Cleaner URLs, technically more RESTful, but harder to test in browser and requires header parsing for routing).
- **Query Param**: `?version=1` (Rare, usually avoided).

**Pagination**:
- **Offset-based**: `?limit=50&offset=100`. Maps directly to `LIMIT` and `OFFSET` in SQL. 
  - *Problem*: Degrades severely on large datasets because the database must scan and skip the first N rows before returning results. O(N) performance.
- **Cursor-based**: `?limit=50&cursor=eyJpZCI6MTI1fQ==`. Uses an opaque pointer to the last seen record. Maps to `WHERE id > 125 LIMIT 50`.
  - *Advantage*: O(1) performance regardless of table size. Required for infinite scroll feeds (Twitter, Instagram).

### 3.2 gRPC

Developed by Google, gRPC uses HTTP/2 for transport and Protocol Buffers (Protobuf) as the interface description language.

**Realistic Benchmark**: 
In practice, gRPC is typically **2-7x faster** than JSON-over-HTTP REST. (Do not claim a flat 10x; it heavily depends on payload size, network conditions, and serialization overhead).
The speed comes from:
- Binary serialization (Protobuf is much smaller and faster to parse than JSON).
- HTTP/2 multiplexing (multiple concurrent requests on a single TCP connection).
- Header compression (HPACK).

**Streaming Capabilities**:
- **Unary**: Standard Request/Response.
- **Server Streaming**: Client sends one request, server streams multiple responses (e.g., live stock ticker).
- **Client Streaming**: Client streams data, server sends one response (e.g., large file upload).
- **Bidirectional Streaming**: Both sides stream messages independently (e.g., real-time chat or telemetry).

**When to use gRPC**:
- Internal service-to-service communication.
- High-throughput environments.
- Polyglot architectures (Protobuf generates strictly typed client and server stubs for 10+ languages automatically).

### 3.3 GraphQL

Developed by Facebook, GraphQL allows clients to specify exactly what data they need, solving the over-fetching and under-fetching problems of REST.

**The N+1 Problem**:
Because GraphQL resolvers execute independently, a query for 50 posts and their authors can result in 1 query for the posts + 50 individual queries for each author.
**Solution**: Use `DataLoader`, which batches and caches requests, converting the 50 author queries into a single `SELECT * FROM authors WHERE id IN (...)`.

### 3.4 Comparison Table

| Feature | REST | gRPC | GraphQL |
| :--- | :--- | :--- | :--- |
| **Payload** | JSON (Text) | Protobuf (Binary) | JSON (Text) |
| **Transport** | HTTP/1.1 or HTTP/2 | HTTP/2 | HTTP/1.1 or HTTP/2 |
| **Coupling** | Loose | Tight (Contracts) | Loose |
| **Best For** | Public APIs, Web | Internal Microservices | Mobile/Web Frontends |
| **Performance** | Good | Excellent (2-7x faster) | Good |

---

## 4. API Gateway Pattern

As a system grows to dozens of microservices, exposing them directly to clients is an anti-pattern. 

### 4.1 Responsibilities of an API Gateway

An API Gateway sits at the edge of the network and acts as a reverse proxy, routing requests to internal services while abstracting the internal architecture.

1. **Routing**: Maps external endpoints like `/api/users` to the internal User Service IP and `/api/orders` to the Order Service IP.
2. **Authentication/Authorization**: Validates API keys, verifies OAuth tokens, and validates JWTs at the edge before traffic hits internal networks.
3. **Rate Limiting**: Throttles abusive clients (e.g., max 100 req/min per IP or User ID) to protect backend services.
4. **SSL Termination**: Decrypts HTTPS traffic at the edge to reduce CPU load on internal services.
5. **Observability**: Central point for logging edge metrics (e.g., overall 4xx/5xx rates, P99 latency).
6. **Request Aggregation**: Can fan out a single client request to multiple internal services and aggregate the response (though this can become a bottleneck).

**Examples**: Kong, AWS API Gateway, Nginx, Traefik.

### 4.2 API Gateway vs Service Mesh

It is critical to distinguish these two layers:
- **API Gateway** operates at the **edge** (North-South traffic). It handles traffic coming from the outside world into your cluster.
- **Service Mesh** operates **internally** (East-West traffic). It handles L4/L7 communication between microservices within the cluster.

### 4.3 Backend for Frontend (BFF) Pattern

Instead of a single monolithic API Gateway for all clients, the BFF pattern provisions a dedicated gateway per client type.
- **Mobile BFF**: Optimizes payload sizes for cellular networks, aggregates aggressive calls to reduce battery drain.
- **Web BFF**: Handles session cookies, CSRF tokens, and serves larger payloads suitable for desktop browsers.
- **Public API BFF**: Enforces strict rate limits, third-party API key validation, and billing metering.

---

## 5. Service Discovery

In a cloud-native environment, microservices dynamically scale up and down. Containers crash and are rescheduled. IP addresses change constantly. Service Discovery solves the problem of "How does Service A reliably find the current IP address of Service B?"

### 5.1 Client-Side Discovery

- The service registry (e.g., Netflix Eureka, HashiCorp Consul) maintains a dynamic database of available service instances.
- The client queries the registry, gets a list of IPs, and performs load balancing itself (e.g., Round Robin, Least Connections).
- **Pros**: Fewer network hops; decentralized load balancing.
- **Cons**: The client must implement complex load balancing logic; couples the client to the registry stack, requiring SDKs in every language.

### 5.2 Server-Side Discovery

- The client sends the request to a dedicated Load Balancer (e.g., AWS ALB).
- The Load Balancer queries the service registry (or integrates directly) and routes the traffic.
- **Pros**: The client is dumb and simple; no language-specific SDKs needed.
- **Cons**: The Load Balancer becomes a single point of failure and adds an extra network hop.

### 5.3 DNS-Based Discovery

- Relies on internal DNS resolution.
- **Kubernetes DNS (CoreDNS)**: Service A resolves the hostname `service-b.default.svc.cluster.local`, and CoreDNS returns the virtual IP of Service B. Kubernetes manages mapping that VIP to the actual pods via iptables/IPVS.
- **Consul**: Offers DNS interfaces for service discovery along with rich HTTP APIs.

**Health Checks**:
Service registries continuously ping instances (e.g., HTTP `GET /health` or TCP checks). If an instance fails, it is automatically removed from the registry, preventing traffic from being routed to a dead node.

---

## 6. Resilience Patterns

Distributed systems fail constantly. Network packets drop, instances crash, GC pauses freeze applications, and downstream services slow down. You must design for resilience.

### 6.1 Timeouts

**Rule**: Never make a network call without a strict timeout.
If Service A calls Service B without a timeout, and Service B hangs, Service A will wait indefinitely. Service A's thread pool will eventually exhaust, bringing down Service A. This causes a cascading failure across the entire system.

### 6.2 Retries with Exponential Backoff and Jitter

Transient network glitches happen. Retrying the request can fix them, but must be done safely.
- **Limit max retries**: Usually 3 times.
- **Exponential Backoff**: Wait 1s, then 2s, then 4s, to avoid hammering a struggling service.
- **Jitter**: Add randomness to the wait time. If a database goes down for 5 seconds, and 1,000 clients all retry at exactly `t=1s`, they create a "thundering herd" that will immediately crash the database when it comes back up. Jitter scatters the retries.
- **Requirement**: The API must be **idempotent** (safe to retry without side effects, e.g., using an `Idempotency-Key` header for payments).

### 6.3 Circuit Breaker Pattern

If a downstream service is completely down, retrying only worsens the problem and wastes resources. A Circuit Breaker stops calls to a failing service immediately, returning a fast error.

```text
Circuit Breaker State Machine:

                     [ CLOSED ] (Normal Operation)
                    /          ^
         Threshold /            \ Success Threshold
          Exceeded/              \ Reached
                 v                \
            [ OPEN ] --------> [ HALF-OPEN ]
      (Fails Fast, returns     (Tests a few requests
       cached/default value)    after timeout period)
```

- **Libraries**: Resilience4j (Java), Polly (.NET).
- **Modern Approach**: Offload this logic to a Service Mesh (e.g., Istio Envoy proxy) so application code is unaware of it.
- **Fallback Strategies**: When the circuit is OPEN, return a cached response, a degraded UI element (e.g., hiding recommendations), or fail fast gracefully.

### 6.4 Bulkhead Pattern

Named after the waterproof compartments in a ship's hull. If one compartment floods, the ship doesn't sink.
- **Implementation**: Allocate separate connection pools, thread pools, or rate limits for different downstream dependencies.
- If the external Email Service is slow, it exhausts only the Email thread pool. The Payment Service thread pool remains healthy, allowing core transactions to proceed.

### 6.5 Rate Limiting Algorithms

Protect your services from abusive clients, scrapers, and DDoS attacks.

1. **Token Bucket**: 
   - A bucket holds a maximum number of tokens. Tokens are added at a fixed rate (e.g., 10 per second).
   - Each request consumes a token. If empty, the request is rejected (429 Too Many Requests).
   - **Advantage**: Allows bursts of traffic up to the bucket size. (Standard for public APIs).

2. **Leaky Bucket**:
   - Requests enter a bucket (queue). The bucket leaks (processes) requests at a fixed, constant rate.
   - **Advantage**: Smooths out bursty traffic into a highly consistent output rate.

3. **Fixed Window Counter**:
   - Tracks requests in a fixed time window (e.g., 100 reqs from 12:00 to 12:01).
   - **Problem**: The Boundary Problem. A user can send 100 requests at 12:00:59 and 100 more at 12:01:01, resulting in 200 requests processed in just 2 seconds, violating the intended limit.

4. **Sliding Window Log**:
   - Stores a precise timestamp for every single request in a fast data store (like Redis).
   - Calculates the exact number of requests in the trailing 60 seconds by counting timestamps.
   - **Advantage**: Perfectly precise.
   - **Disadvantage**: High memory usage (O(N) where N is the number of requests).

5. **Sliding Window Counter**:
   - **Crucial Distinction**: Do not conflate this with the Sliding Window Log. They are entirely different algorithms.
   - Tracks counts in fixed windows, but calculates a weighted average of the current window and the previous window.
   - E.g., if you are 30% into the current minute, the estimated count is `(previous_minute_count * 0.7) + current_minute_count`.
   - **Advantage**: Highly memory efficient O(1) while effectively smoothing out the boundary problem. Approximates the precise log effectively.

---

## 7. Service Mesh

As the number of services grows, implementing retries, circuit breaking, distributed tracing, and mTLS in every language/framework library becomes unmanageable.

### 7.1 The Sidecar Pattern

A Service Mesh deploys a lightweight, high-performance proxy (e.g., Envoy) alongside every microservice instance (in the same Kubernetes pod).
- The microservice only talks to `localhost`.
- The sidecar proxy intercepts all inbound and outbound traffic, applying policies, encrypting payloads, and routing to destinations.

```text
Service Mesh Sidecar Architecture:

+-------------------+                     +-------------------+
|     POD A         |                     |     POD B         |
|                   |                     |                   |
|  [ Microservice ] |                     |  [ Microservice ] |
|         |         |                     |         ^         |
|         v         |                     |         |         |
|  [ Envoy Proxy ]  | ===== mTLS =======> |  [ Envoy Proxy ]  |
+-------------------+                     +-------------------+
          |                                         |
          |                                         |
          +-----------> [ Control Plane ] <---------+
                         (Istio/Linkerd)
                         - Cert management
                         - Routing rules
```

### 7.2 Architecture (Control Plane vs Data Plane)

- **Data Plane**: The actual network of sidecar proxies (Envoy) moving the packets, terminating TLS, and enforcing rate limits.
- **Control Plane**: The central management layer (e.g., Istio, Linkerd) that configures the proxies, distributes certificates, and gathers telemetry.

**Key Features provided by the Mesh**:
- **mTLS (Mutual TLS)**: Automatically encrypts all internal traffic and verifies identities without application code changes.
- **Traffic Management**: Enables advanced routing like Canary deployments (shift exactly 5% of traffic to v2) or header-based routing.
- **Observability**: Automatically generates tracing spans and latency metrics for every hop.

### 7.3 API Gateway vs Service Mesh

Remember the distinction clearly:
- **API Gateway**: Edge routing, AuthN, external rate limiting, billing (North-South).
- **Service Mesh**: Internal routing, mTLS, internal circuit breaking, identity verification (East-West at L4/L7).

---

## 8. Distributed Tracing & Observability

In a monolith, you grep a single log file. In microservices, a single user request might touch 15 different services across 50 servers. 

### 8.1 The Three Pillars of Observability

1. **Logs**: Immutable records of discrete events (e.g., "User 123 logged in"). Best for deep debugging.
2. **Metrics**: Aggregated numeric data over time (e.g., CPU utilization, HTTP error rates). Best for alerting and dashboards.
3. **Traces**: End-to-end flow of a request across distributed systems. Best for performance bottlenecks and flow analysis.

### 8.2 Distributed Tracing Concepts

- **Trace ID**: A unique identifier generated at the API Gateway and passed in HTTP headers to every downstream service.
- **Span**: Represents a single unit of work (e.g., a DB query or a service call).
- **Parent-Child Spans**: Spans link together to form a waterfall graph showing exactly where time was spent, revealing sequential bottlenecks vs parallel execution.
- **W3C Trace Context**: The standardized HTTP headers (`traceparent`, `tracestate`) used to propagate context across boundaries.

### 8.3 The OpenTelemetry Standard (OTel)

Historically, tracing meant vendor lock-in (Datadog agents, New Relic SDKs). **OpenTelemetry** is the CNCF standard that provides vendor-neutral SDKs to capture logs, metrics, and traces, allowing you to instrument code once and export data to any backend (Prometheus, Jaeger, DataDog).

### 8.4 Key Microservice Metrics (RED Method)

When monitoring a microservice, focus on the **RED** metrics:
- **Rate**: Number of requests per second.
- **Errors**: Number of failed requests.
- **Duration**: P99 and P95 latency of requests.
(Also monitor **Saturation**: how "full" the service is, e.g., CPU %, memory %, or thread pool usage/queue depth).

---

## 9. Data Management Across Services

Distributed data is the hardest computer science problem in microservices architectures. Since transactions cannot span databases, maintaining consistency requires complex patterns.

### 9.1 Database-per-Service Reality

Because services cannot share databases, how do you perform a simple `JOIN` across User data and Order data?

### 9.2 API Composition

The API Gateway or a dedicated aggregator service makes an API call to the User Service and another call to the Order Service, then joins the data in memory.
- **Drawbacks**: High network overhead, potential N+1 query problems, and lack of strong consistency.

### 9.3 CQRS (Command Query Responsibility Segregation)

Separate the system into a **Write Model** (Commands) and a **Read Model** (Queries).
- **Commands**: Change state (e.g., `PlaceOrder`). Highly normalized, optimized for consistency, strong validation.
- **Queries**: Read state. Highly denormalized, optimized for fast reads, often stored in a separate database like Elasticsearch or Redis.

### 9.4 Event-Driven Data Sharing and Materialized Views

To solve the distributed JOIN problem reliably and at scale:
1. When a User is updated, the User Service publishes a `UserUpdated` event to a message broker (e.g., Kafka).
2. The Order Service consumes this event asynchronously.
3. The Order Service updates a local replica (a **Materialized View**) of the user data within its own database.
4. When a user requests their orders, the Order Service has all the necessary data locally. No cross-service synchronous API calls are needed for the read.

**Trade-off**: You achieve high availability, autonomy, and low latency at the cost of **Eventual Consistency** (the Order Service's view of the User might be a few milliseconds stale).

### 9.5 Distributed Transactions: The Saga Pattern

Two-Phase Commit (2PC) does not scale in microservices due to locking. Instead, use the **Saga Pattern**.
A Saga is a sequence of local transactions. Each local transaction updates the database and publishes a message to trigger the next transaction.
- If a step fails, the Saga executes a series of **Compensating Transactions** to undo the previous steps.

**Choreography Saga**: 
Services publish and listen to events directly (no central coordinator). Best for simple sagas (2-4 steps).
```text
OrderSvc -> produces OrderCreated -> InventorySvc
InventorySvc -> produces InventoryReserved -> PaymentSvc
PaymentSvc -> produces PaymentProcessed -> DeliverySvc
```

**Orchestration Saga**: 
A central orchestrator service tells the participants what local transactions to execute. Best for complex sagas where you need a single place to view the entire workflow state.

---

## 10. Deployment Strategies

Microservices require sophisticated deployment strategies to minimize risk, as releasing multiple services simultaneously is error-prone.

### 10.1 Blue-Green Deployment

- Maintain two identical production environments (Blue and Green).
- Blue is currently live, taking 100% of traffic.
- Deploy the new version to Green and run automated integration and smoke tests.
- Flip the load balancer or DNS to point 100% of traffic to Green.
- **Advantage**: Instant rollback (flip the router back to Blue if things go wrong). Zero downtime.
- **Disadvantage**: Expensive (requires 2x infrastructure cost) and difficult with stateful database migrations.

### 10.2 Canary Deployment

- Route a small percentage of traffic (e.g., 1% or 5%) to the new version (the "Canary").
- Monitor the RED metrics (latency, error rate).
- If metrics are healthy, gradually shift more traffic to the Canary (5% → 25% → 50% → 100%).
- If error rates spike, automatically roll back the traffic to the stable version.
- Heavily utilized in Service Mesh architectures (Istio makes this a 3-line configuration change).

### 10.3 Rolling Update

- Replace instances one by one (or in small batches) behind the load balancer.
- Example: In a cluster of 10 nodes, take down 2, upgrade them to the new version, put them back, repeat until all 10 are updated.
- **Advantage**: Cost-effective (no duplicate infrastructure needed).
- **Disadvantage**: Rollbacks take just as much time as rollouts. Old and new versions run concurrently, requiring strict backward and forward compatibility in APIs and databases.

### 10.4 Feature Flags (Toggles)

Decouple **Deployment** (putting code on a server) from **Release** (exposing the feature to users).
- Wrap new code in a conditional flag check (e.g., `if (FeatureFlags.isEnabled("NEW_CHECKOUT_FLOW", user.id))`).
- Deploy the code to production with the flag turned completely off.
- Gradually enable the flag: first for internal QA users, then 1% beta testers, and finally 100% of the user base.
- If a critical bug occurs, turn off the flag instantly via a dashboard without redeploying code or rolling back infrastructure.

---

## 11. Appendix: Code & Config Examples

### 11.1 gRPC Protobuf Contract

Defining a tight API contract using Protocol Buffers (`.proto` file):

```protobuf
syntax = "proto3";
package payments;

// Service definition
service PaymentService {
  rpc ProcessPayment (PaymentRequest) returns (PaymentResponse) {}
}

// Request payload
message PaymentRequest {
  string user_id = 1;
  double amount = 2;
  string currency = 3;
  string idempotency_key = 4;
}

// Response payload
message PaymentResponse {
  string transaction_id = 1;
  enum Status {
    SUCCESS = 0;
    FAILED = 1;
    INSUFFICIENT_FUNDS = 2;
  }
  Status status = 2;
}
```

### 11.2 API Gateway Rate Limiting (Kong / Nginx pattern)

Example of configuring an API Gateway route with the Token Bucket rate limit algorithm:

```yaml
routes:
  - name: process-payment-route
    paths:
      - /v1/payments
    service:
      name: payment-microservice
      port: 8080
    plugins:
      - name: rate-limiting
        config:
          second: 10
          minute: 100
          policy: local
          fault_tolerant: true
```

### 11.3 Circuit Breaker Configuration (Resilience4j)

A typical Circuit Breaker configuration in a Spring Boot microservice:

```yaml
resilience4j.circuitbreaker:
  instances:
    inventoryService:
      slidingWindowSize: 100               # Track last 100 calls
      permittedNumberOfCallsInHalfOpenState: 10
      waitDurationInOpenState: 10s         # Wait 10s before half-open retry
      failureRateThreshold: 50             # Trip if 50% of calls fail
      slowCallRateThreshold: 50
      slowCallDurationThreshold: 2s        # Any call taking > 2s is a "failure"
```

### 11.4 Feature Flag Toggling Structure

How a feature flag configuration typically looks in a system like LaunchDarkly:

```json
{
  "feature_flags": {
    "new_checkout_flow": {
      "enabled": true,
      "rollout_percentage": 10,
      "targeted_users": ["qa-team", "beta-users"],
      "default_variation": false
    }
  }
}
```
