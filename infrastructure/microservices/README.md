# Microservices Architecture Curriculum

Welcome to the Microservices Architecture Curriculum. This repository serves as a comprehensive, deep-dive guide into designing, building, and maintaining distributed systems.

## What are Microservices?

Microservices architecture is an approach to software development where a large application is built as a suite of modular services. Each module supports a specific business goal and uses a simple, well-defined interface to communicate with other sets of services. 

Unlike monolithic architectures—where all components (UI, business logic, data access) are unified in a single deployable unit with shared memory and a shared database—microservices are independently deployable, loosely coupled, and organized around business capabilities. 

### The Problems They Solve
- **Independent Scaling**: Scale only the components that need it, rather than the entire application.
- **Fault Isolation**: A memory leak or crash in one service does not bring down the entire system.
- **Technological Freedom**: Different services can be written in different languages and use different databases (Polyglot Persistence).
- **Organizational Alignment**: Enables Conway's Law by allowing small, autonomous teams to own the entire lifecycle of a service.

### The Distributed Systems Tax
Microservices are not a free lunch. They introduce the "distributed systems tax":
- Network latency and unreliability.
- Complex operational requirements (deployment, monitoring, tracing).
- Data consistency challenges (eventual consistency over ACID).
- Distributed transactions (Sagas instead of database locks).

Microservices make sense when the organizational size, scaling requirements, and fault isolation needs justify the operational complexity. They do not make sense for small teams, early-stage startups searching for product-market fit, or systems with ultra-low latency requirements.

## Curriculum Module Map

| Module | Title | Key Topics Covered |
|--------|-------|--------------------|
| **01** | Decomposition Patterns | Monolith vs Microservices, Domain-Driven Design (DDD), Bounded Contexts, Strangler Fig Pattern, Database per Service. |
| **02** | Inter-Service Communication | Synchronous vs Asynchronous, REST vs gRPC, Message Queues (RabbitMQ) vs Event Streaming (Kafka), Resilience (Circuit Breaker). |
| **03** | Distributed Transactions | The Two-Phase Commit problem, Saga Pattern (Choreography vs Orchestration), Outbox Pattern, Change Data Capture (CDC). |
| **04** | API Gateways & Service Mesh | Authentication, Rate Limiting, Request Routing, Envoy, Istio, mTLS, Traffic Shaping. (Coming Soon) |
| **05** | Observability & Operations | Distributed Tracing (OpenTelemetry), Metrics (Prometheus), Log Aggregation, Chaos Engineering, CI/CD for Microservices. (Coming Soon) |

## Prerequisites

Before diving into the modules, ensure you have a solid understanding of the following:
1. **Containerization**: Familiarity with Docker, building images, and container orchestration concepts.
2. **RESTful APIs**: Understanding of HTTP verbs, status codes, and resource-based routing.
3. **Database Fundamentals**: Relational vs NoSQL databases, ACID properties, and basic SQL.
4. **Messaging Basics**: Concept of publishers, subscribers, queues, and topics.

## How to Use This Curriculum

Each module in this curriculum builds upon the previous one:
- **Module 01** teaches you how to break the system apart.
- **Module 02** teaches you how to connect the separated pieces reliably.
- **Module 03** teaches you how to maintain data integrity across those connected pieces.

Within each module directory, you will find:
- `README.md`: An extensive, deep technical exploration of the topic.
- `QnA.md`: 15 deeply answered questions testing your understanding.
- `CHEATSHEET.md`: A highly dense, scannable reference guide.

Begin with `01_decomposition_patterns` and progress sequentially. Good luck.
