# System Design — Complete Interview Curriculum

A comprehensive, production-grade guide to designing large-scale distributed systems. This curriculum covers architectural foundations, scalability patterns, database selection, messaging, consensus, microservices, and real-world system architecture. 

Designed for software engineers preparing for System Design interviews (from mid-level SDE-2 to principal/staff SDE-3+ roles).

---

## Curriculum Structure

Each module is designed with hands-on labs and practical design assignments:
```
system_design/
├── [Module]/
│   ├── README.md       ← Comprehensive theoretical breakdown of first principles
│   ├── exercise/       ← System design interview prompt or practical task
│   ├── labs/           ← Code, simulator, or dockerized environment to run locally
│   └── solution/       ← Reference architectures, calculations, and solution code
```

---

## Curriculum Map

| Module | Core Topics | Hands-On Labs | Design Exercise |
|--------|-------------|---------------|-----------------|
| **[M1: Foundations](./01_foundations/)** | Network layers (DNS, TCP, HTTP), Latency numbers, availability (99.9% to 99.999%), Back-of-Envelope estimation, RADIO framework | `estimation_calculator.py` (Worked math for major platforms) | Back-of-envelope estimation for a URL shortener |
| **[M2: Scalability](./02_scalability/)** | Vertical vs Horizontal, stateless services, load balancing (L4/L7), Consistent Hashing, Geo-routing | Multi-container setup (3 FastAPI instances behind an Nginx load balancer) | Configure weighted round-robin and implement consistent hashing |
| **[M3: Databases](./03_databases/)** | Indexing internals (B-Trees, Hash), ACID & isolation levels, replication topologies, sharding strategies, NoSQL types | Query optimizer demo (`EXPLAIN ANALYZE` on 1M rows), sharding simulator | Optimize a bottlenecked database query and implement a custom index |
| **[M4: Caching](./04_caching/)** | Cache strategies (aside, through, back), eviction (LRU/LFU), Redis data structures, stampede, penetration (Bloom filters), CDNs | Caching comparison (FastAPI with Redis vs direct Postgres access) | Implement a write-through caching pattern and build a Bloom filter |
| **[M5: Message Queues](./05_message_queues/)** | Sync vs Async, queues vs streams, delivery guarantees, Outbox Pattern, DLQ, Sagas, RabbitMQ vs SQS vs Kafka | E-commerce event broker (FastAPI producer publishing to RabbitMQ consumers) | Build a Dead Letter Queue (DLQ) with message replay logic |
| **[M6: Distributed Systems](./06_distributed_systems/)** | CAP & PACELC theorems, consistency models, consensus algorithms (Raft), distributed transactions (2PC, Sagas), logical clocks | Network partition simulator (AP vs CP systems), Lamport clocks | Implement a choreography-based Saga transaction pattern |
| **[M7: Microservices](./07_microservices/)** | Monolith decomposition, DDD, REST/gRPC/GraphQL, API Gateway, Circuit Breaker, rate-limiting algorithms | Microservice ecosystem (Nginx Gateway routing to 3 separate backend services) | Secure the gateway with JWT verification and token bucket rate limits |
| **[M8: Case Studies](./08_case_studies/)** | Real-world architectures (Twitter feed, YouTube, WhatsApp, Uber, Netflix, TinyURL) | *Pure architectural case studies* | Design a Pastebin-style text sharing system (full design doc) |

---

## Suggested Study Order

### Week 1: Core Building Blocks
* **Day 1**: M1 — Foundations (Master latency intuition and back-of-envelope math)
* **Day 2–3**: M2 — Scalability (Understand load balancing, stateless layers, and consistent hashing)
* **Day 4–5**: M3 — Databases (Go deep into indexing, partitioning, and replication trade-offs)
* **Day 6–7**: M4 — Caching (Study caching strategies and mitigation of stampedes/penetration)

### Week 2: Distributed Infrastructure & Architecture
* **Day 8–9**: M5 — Message Queues (Understand pub/sub, delivery guarantees, and event-driven patterns)
* **Day 10–11**: M6 — Distributed Systems (Master CAP/PACELC, consensus, and logical clocks)
* **Day 12–13**: M7 — Microservices (Learn API gateways, circuit breakers, rate limiting, and REST vs gRPC vs GraphQL)
* **Day 14**: M8 — Case Studies (Apply all concepts to design Twitter, Uber, Netflix, and YouTube)

---

## Latency Numbers Every Engineer Must Know

These system design constants (originally from Jeff Dean) are critical for making informed design decisions during estimations:

| Operation | Latency (ns) | Latency (Human Readable) | Contextual Comparison |
|-----------|--------------|--------------------------|-----------------------|
| L1 Cache Reference | 0.5 ns | - | Snapping fingers |
| Branch Misprediction | 5 ns | - | - |
| L2 Cache Reference | 7 ns | - | - |
| Mutex Lock/Unlock | 25 ns | - | - |
| Main Memory (RAM) Reference | 100 ns | - | Taking a single breath |
| Compress 1K bytes with Zippy | 3,000 ns | 3 μs | - |
| Send 1K bytes over 1 Gbps Network | 10,000 ns | 10 μs | - |
| Read 4K sequentially from SSD | 150,000 ns | 150 μs | - |
| Read 1 MB sequentially from RAM | 250,000 ns | 250 μs | - |
| Round trip within same Data Center | 500,000 ns | 0.5 ms | - |
| Read 1 MB sequentially from SSD | 1,000,000 ns | 1 ms | - |
| Disk Seek (Rotational HDD) | 10,000,000 ns | 10 ms | Blinking your eyes |
| Read 1 MB sequentially from HDD | 20,000,000 ns | 20 ms | - |
| WAN Packet Round Trip (US to EU) | 150,000,000 ns | 150 ms | - |

---

## System Availability Targets

| "Nines" | Availability | Allowed Downtime per Year | Target Use Case |
|---------|--------------|---------------------------|-----------------|
| **3 Nines** | 99.9% | 8 hours, 45 minutes | Internal business tools, non-critical web apps |
| **4 Nines** | 99.99% | 52 minutes, 35 seconds | E-commerce checkout, payment gateways |
| **5 Nines** | 99.999% | 5 minutes, 15 seconds | Telecommunication networks, core banking ledgers |
