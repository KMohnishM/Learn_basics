# Microservices Decomposition Cheatsheet

## Monolith vs Microservices

| Feature | Monolith | Microservices |
|---------|----------|---------------|
| **Deployment** | Single unit (WAR, Directory) | Independent units |
| **Scaling** | Scale everything together | Scale individual services |
| **Data** | Single shared database | Database per service |
| **Communication** | In-memory function calls | Network calls (HTTP/gRPC/Events) |
| **Failure Impact** | High (one bug crashes all) | Low (isolated fault domains) |
| **Tech Stack** | Homogeneous (Locked-in) | Polyglot (Choose best tool) |
| **Complexity** | High cognitive load in code | High operational complexity |

## DDD Building Blocks

| Concept | Definition |
|---------|------------|
| **Domain** | The sphere of knowledge the software addresses. |
| **Subdomain** | A segment of the domain (Core, Supporting, Generic). |
| **Bounded Context**| The boundary within which a specific domain model applies. |
| **Ubiquitous Lang**| Shared vocabulary between devs and business experts. |
| **Aggregate** | A cluster of domain objects treated as a single unit. |
| **Aggregate Root** | The only entry point to modify objects in an aggregate. |
| **Entity** | Object with identity spanning time (e.g., User). |
| **Value Object** | Immutable object defined by attributes (e.g., Money). |
| **Domain Event** | Record of a significant business occurrence. |

## Decomposition Strategies

| Strategy | Description | Best For |
|----------|-------------|----------|
| **Business Capability** | Aligned with what business does (Shipping, Sales). | High-level organizational alignment. |
| **Subdomain (DDD)** | Aligned with bounded contexts. | Deeply complex business logic. |
| **Use Case / Verb** | Aligned with specific actions (Checkout, Search). | High-performance, isolated operations. |
| **Strangler Fig** | Incremental migration via an API Gateway routing. | Safely modernizing legacy systems. |

## Anti-Patterns

| Anti-Pattern | Description | Fix |
|--------------|-------------|-----|
| **Distributed Monolith**| Services must be deployed together. | Re-evaluate bounded contexts. |
| **Chatty Services** | Dozens of network hops for one request. | Consolidate or use GraphQL/BFF. |
| **Shared DB** | Multiple services query the same tables. | Enforce Database-per-Service. |
| **Shared Domain Lib** | Sharing business logic via a common JAR. | Duplicate code or extract service. |
| **Synchronous Chains** | Service A -> B -> C -> D (HTTP). | Use asynchronous Domain Events. |

## Service Sizing Heuristics
- **Two-Pizza Team:** Can the owning team be fed by two pizzas (6-10 devs)?
- **Independent Deployability:** Can it go to production without coordinating with other teams?
- **Single Reason to Change:** Does it encapsulate a cohesive set of responsibilities?
- **Cognitive Load:** Can a new dev understand the service in a few days?

## Strangler Fig Phases Diagram

```text
PHASE 1: Monolith Only

      [ Client ]
          |
    (All traffic)
          v
   +---------------+
   |   Monolith    |
   | (All logic)   |
   +---------------+


PHASE 2: API Gateway & First Microservice

      [ Client ]
          |
          v
   +---------------+
   | API Gateway   |
   +---------------+
     /           \
 (Legacy)     (New Route)
   /               \
  v                 v
+----------+   +--------------+
| Monolith |   | OrderService |
|          |   | (New Logic)  |
+----------+   +--------------+


PHASE 3: Full Migration (Strangled)

      [ Client ]
          |
          v
   +---------------+
   | API Gateway   |
   +---------------+
       |       |
      v         v
+---------+ +---------+
| Service | | Service |
|    A    | |    B    |
+---------+ +---------+
   (Monolith Deleted)
```
