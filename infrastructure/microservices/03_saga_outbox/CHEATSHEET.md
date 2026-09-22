# CHEATSHEET: Saga and Outbox Patterns

## Saga Choreography vs Orchestration Comparison

| Feature | Choreography | Orchestration |
| :--- | :--- | :--- |
| **Control Flow** | Decentralized, event-driven | Centralized, command-driven |
| **Complexity** | Simple for small workflows | Better for complex workflows |
| **Coupling** | Services must know about domain events | Services only know their own domain |
| **Point of Failure**| None (Decentralized) | Yes (The Orchestrator component) |
| **Observability** | Difficult (Spaghetti architecture) | Easy (Centralized state machine) |
| **Cyclic Risk** | High risk of cyclic dependencies | Low risk (Orchestrator manages flow) |

## Outbox Pattern Implementation Checklist

- [ ] Ensure application writes to business tables and `outbox` table in a **single database transaction**.
- [ ] Define robust outbox schema: `id (UUID)`, `aggregate_type`, `aggregate_id`, `type`, `payload (JSON)`.
- [ ] Use a CDC tool (like Debezium) instead of application polling for high throughput and reliability.
- [ ] Ensure all downstream consumers strictly implement **idempotency** using the outbox `id`.
- [ ] Implement log compaction or routine cleanup of the `outbox` table to save database storage.

## Compensating Transactions Table

| Forward Action | Compensating Action (Semantic Undo) | Potential Failure Reason |
| :--- | :--- | :--- |
| Debit Account ($100) | Credit Account ($100) | Target service down/timeout |
| Reserve Inventory (Item A)| Release Inventory (Item A) | Payment failed later in saga |
| Create Order (PENDING) | Update Order (CANCELLED) | User credit check failed |
| Send Welcome Email | Send Cancellation Email | Saga aborted by user |
| Provision Cloud Server | Terminate Cloud Server | Billing setup failed |

## Saga State Machine States and Transitions (ASCII)

```text
       [START]
          |
          v
 +-------------------+      (Failure)
 |      PENDING      | -----------------+
 +-------------------+                  |
          |                             |
          | (Success)                   v
          v                   +-------------------+
 +-------------------+        |   COMPENSATING    |
 |     COMPLETED     |        +-------------------+
 +-------------------+                  |
          |                             | (Compensation Done)
          v                             v
       [ END ]                  +-------------------+
                                |    CANCELLED      |
                                +-------------------+
```

## CDC vs Polling Outbox Comparison

| Characteristic | CDC (e.g., Debezium) | Polling (Application Worker) |
| :--- | :--- | :--- |
| **Performance** | High (Reads database transaction logs) | Low (Constant, heavy DB queries) |
| **Latency** | Milliseconds | Seconds (Depends strictly on poll interval)|
| **Complexity** | High (Requires Kafka Connect infrastructure) | Low (Simple background thread) |
| **Database Load**| Minimal overhead | High (Especially bad at massive scale) |

## Common Saga Failure Scenarios and Recovery Strategies

| Failure Scenario | Mitigation / Recovery Strategy |
| :--- | :--- |
| Orchestrator Crashes | Resume workflow seamlessly from persisted `saga_instances` table. |
| Downstream Service Timeout | Arm SEC timeouts; auto-transition to COMPENSATING state. |
| Compensation Action Fails | Retry indefinitely. Route to Dead Letter Queue (DLQ) if fatally stuck. |
| Duplicate Message Delivery | Implement strict Idempotency Keys in all participating services. |
| Concurrent Data Updates | Use Semantic Locks (`_saga_lock` column) on database entities. |

## Idempotency Implementation Patterns Table

| Pattern | Description | Best Use Case |
| :--- | :--- | :--- |
| **Idempotency Keys** | Store processed `message_id`s in a dedicated SQL table. | General purpose message handling. |
| **Natural Idempotency**| Operations like `UPDATE status = 'SHIPPED'` | State transitions that don't compound. |
| **Event Sourcing** | Check if event already exists in the aggregate's event stream.| CQRS / Event Sourced architectures. |
| **Optimistic Locking** | Reject data updates if `version` mismatch occurs. | Preventing lost updates / race conditions. |
