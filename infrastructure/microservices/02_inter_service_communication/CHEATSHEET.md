# Module 2 Cheatsheet: Inter-Service Communication

## Synchronous vs Asynchronous

| Feature | Synchronous (REST, gRPC) | Asynchronous (RabbitMQ, Kafka) |
| :--- | :--- | :--- |
| **Coupling** | High (Temporal & Spatial) | Low (Broker acts as middleman) |
| **Latency** | Wait for full processing | Immediate return (Fire and forget) |
| **Failure Scope**| Cascading without patterns | Contained (message stays in queue)|
| **Complexity** | Easy to debug/trace | Harder (requires Distributed Tracing)|
| **Best For** | Reads, user-facing APIs | Writes, heavy processing, notifications |

## gRPC vs REST

| Feature | gRPC | REST |
| :--- | :--- | :--- |
| **Protocol** | HTTP/2 | HTTP/1.1 (mostly) |
| **Payload** | Binary (Protobuf) | Text (JSON, XML) |
| **Contract** | Strict (code generated) | Loose (OpenAPI optional) |
| **Performance**| High (Multiplexing, compression) | Moderate |
| **Browser Support**| Poor (requires grpc-web proxy) | Native / Excellent |

## Message Queue vs Event Streaming

| Feature | Message Queue (RabbitMQ) | Event Stream (Kafka) |
| :--- | :--- | :--- |
| **Data Structure**| Queue | Append-only Log |
| **Message Life** | Deleted upon ACK | Retained by time/size |
| **State Tracking**| Broker tracks message state | Consumer tracks offset state |
| **Routing** | Complex routing topologies | Simple topic partitioning |
| **Replayability** | Hard/Impossible | Trivial (just reset offset) |

## Resilience Patterns

| Pattern | Problem Solved | Mechanism |
| :--- | :--- | :--- |
| **Timeout** | Threads blocking indefinitely | Abort request after `x` ms. |
| **Retry** | Transient network hiccups | Try again with exponential backoff & jitter. |
| **Circuit Breaker**| Cascading failures / Thundering herd| Fail fast. Open circuit on error threshold. |
| **Bulkhead** | One slow dependency exhausting resources| Isolate thread/connection pools per dependency. |
| **Fallback** | Service unavailable | Return default data or cached stale data. |

## Delivery Semantics

| Semantics | Description | Risk | Requirement |
| :--- | :--- | :--- | :--- |
| **At-most-once** | Delivered 0 or 1 times. | Data Loss | None |
| **At-least-once** | Delivered 1 or more times. | Duplicates | Consumers MUST be idempotent |
| **Exactly-once** | Delivered exactly 1 time. | High latency/complexity | Distributed Transactions |

## HTTP Status Codes for Microservices

| Code | Usage |
| :--- | :--- |
| **200 OK** | Success. |
| **201 Created** | Resource created synchronously. |
| **202 Accepted** | Async processing started (return tracking URI). |
| **400 Bad Request** | Validation error (client fault). |
| **401 Unauthorized** | Missing/invalid authentication. |
| **403 Forbidden** | Authenticated, but lacks authorization (RBAC). |
| **404 Not Found** | Resource does not exist. |
| **409 Conflict** | State mismatch, or Idempotency Key collision. |
| **429 Too Many Req** | Rate limiting triggered. |
| **500 Internal Error**| Unexpected server crash. |
| **503 Service Unav.**| Circuit breaker open, or shedding load. |

## ASCII Diagrams

### Circuit Breaker States
```text
      [CLOSED]
       |    ^
 Failures   | Timeout
       v    |
       [OPEN] <--- Failures ---- [HALF-OPEN]
                                  ^      |
                                  |      |
                                  +------+
                                  Success
```

### Async Request-Reply
```text
Client ---(msg: reply_to=Q2)---> [Exchange] ---> [Queue 1] ---> Worker
Client <-------(msg)------------ [Queue 2] <---- [Exchange] <-- Worker
```

## Idempotency Key Implementation Checklist
- [ ] Client generates UUIDv4 `Idempotency-Key` header.
- [ ] Server checks distributed cache (Redis) for key.
- [ ] If key exists & complete -> Return cached HTTP response.
- [ ] If key exists & pending -> Return `409 Conflict`.
- [ ] If key missing -> Acquire lock, execute business logic.
- [ ] Serialize HTTP response (status, headers, body) to cache.
- [ ] Release lock.
