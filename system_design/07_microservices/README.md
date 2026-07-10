# Module 7: Microservices & API Design

A monolith is a single deployable unit containing all your application's logic (e.g., users, billing, inventory). 
Microservices break that application down into many small, independently deployable services that communicate over the network.

## 1. The Monolith vs Microservices Trade-off
**Do NOT build microservices by default.** They introduce massive operational complexity.
- **Monolith Pros**: Easy to test, easy to deploy, zero network latency between modules, simple ACID transactions.
- **Monolith Cons**: Any bug can crash the whole app. Long build times. Large teams step on each other's toes. Forced to use one tech stack.
- **Microservice Pros**: Teams can deploy independently. Isolate failures. Scale specific parts (e.g., scale the `search-service` to 100 nodes while `billing-service` stays at 2). Polyglot programming.
- **Microservice Cons**: Network latency, distributed transactions are incredibly hard, requires heavy DevOps (K8s, CI/CD, tracing).

## 2. API Design
How do microservices talk to each other (or the outside world)?
- **REST (Representational State Transfer)**: Uses HTTP verbs (GET, POST, PUT, DELETE) and JSON. Easy to read, human-friendly, ubiquitous.
- **gRPC (Google Remote Procedure Call)**: Uses HTTP/2 and Protocol Buffers (binary). Up to 10x faster and smaller than JSON REST. Requires defining rigid `.proto` contracts. Ideal for *internal* service-to-service communication.
- **GraphQL**: Clients query exactly the fields they want. Solves the over-fetching and under-fetching problems of REST. Great for frontend-to-backend.

## 3. The API Gateway Pattern
Instead of a mobile app talking directly to 50 different microservices, it talks to a single API Gateway.
The Gateway acts as a reverse proxy and handles:
1. **Routing**: `api.com/users` goes to User Service. `api.com/billing` goes to Billing Service.
2. **Authentication/Authorization**: Validates JWT tokens so every downstream service doesn't have to.
3. **Rate Limiting**: Stops malicious users from hammering the API.
4. **Request Aggregation**: The Gateway can call 3 microservices in parallel, combine their JSON, and send it back to the client as one response.

## 4. Resilience Patterns
Because the network is unreliable, services WILL fail. You must build for failure.
- **Timeouts**: Never make a network call without a timeout.
- **Retries with Exponential Backoff**: If a call fails, try again in 1s, then 2s, then 4s. Add "Jitter" (randomness) so 1,000 failing clients don't all retry at the exact same millisecond.
- **Circuit Breaker**: If the `billing-service` goes down, the `order-service` will keep trying to call it, building up a massive backlog of threads waiting for timeouts until the `order-service` also crashes (cascading failure). 
  - A Circuit Breaker monitors the error rate. If it crosses a threshold (e.g., 50% errors), the breaker "Trips" (opens). 
  - For the next 30 seconds, any calls to the billing service instantly fail (Fast Fail). This saves the `order-service`'s resources.
  - After 30 seconds, it enters "Half-Open" and lets one request through. If it succeeds, the breaker closes.

## 5. Rate Limiting Algorithms
- **Token Bucket**: You have a bucket of 10 tokens. Every request costs 1 token. A background process adds 1 token per second. Allows bursts.
- **Leaky Bucket**: Requests enter a queue. The queue processes requests at a fixed rate (e.g., 5 per second). Smooths out bursts.
- **Fixed Window**: "100 requests per minute". Resets at 12:01, 12:02. Problem: A user can send 100 requests at 12:01:59, and 100 requests at 12:02:01 (200 requests in 2 seconds!).
- **Sliding Window**: Combines fixed window and tracking the exact timestamp of requests to solve the boundary problem.

---
## Next Steps
Go to `labs/` to see how an API Gateway routes traffic, and check the `exercise/` to implement a Circuit Breaker!
