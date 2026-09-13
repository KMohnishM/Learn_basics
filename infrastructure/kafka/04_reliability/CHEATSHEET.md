# Kafka Reliability Cheatsheet

## Delivery Semantics Matrix

| Semantic | Producer Config | Consumer Config | Data Loss Risk | Duplication Risk |
| :--- | :--- | :--- | :--- | :--- |
| **At-Most-Once** | `acks=0` | Auto-commit, process *after* commit | High (Network failure) | None |
| **At-Least-Once**| `acks=1` or `all`, Retries | Process *before* commit | Low | High (Broker failure during ack) |
| **Exactly-Once** | `enable.idempotence=true`, Txn API | `isolation.level=read_committed` | None | None |

---

## Zero Data Loss Configuration Checklist

Ensure these settings are applied for maximum reliability:

**Broker / Topic Level:**
* `replication.factor = 3` (minimum)
* `min.insync.replicas = 2`
* `unclean.leader.election.enable = false`

**Producer Level:**
* `acks = all` (or `-1`)
* `enable.idempotence = true`
* `retries = Integer.MAX_VALUE` (or high number)
* `delivery.timeout.ms = 120000` (2 minutes, adjust as needed)
* `max.in.flight.requests.per.connection = 5` (max allowed with idempotence for strict ordering)

**Consumer Level:**
* `enable.auto.commit = false` (Commit manually after processing)
* `isolation.level = read_committed` (If reading from transactional producers)

---

## Transaction Flow (ASCII Diagram)

```text
  [Producer Application]
       |
       | 1. initTransactions()
       v
  [Transaction Coordinator] <-- Assigns PID, Epoch
       |
       | 2. beginTransaction()
       |
       | 3. send() (Writes messages to partitions)
       |-----------------------------------------> [Topic A Partition 0]
       |-----------------------------------------> [Topic B Partition 1]
       |
       | 4. sendOffsetsToTransaction() 
       |-----------------------------------------> [__consumer_offsets]
       |
       | 5. commitTransaction()
       v
  [Transaction Coordinator]
       |
       | 6. Writes COMMIT Markers
       |-----------------------------------------> [Topic A Partition 0]
       |-----------------------------------------> [Topic B Partition 1]
       |-----------------------------------------> [__consumer_offsets]
```

---

## Dead Letter Queue (DLQ) Implementation Pattern

1. **Consume:** Poll record from `source-topic`.
2. **Process:** Attempt business logic (e.g., parse JSON) inside a `try-catch` block.
3. **Catch:** On exception (e.g., `SerializationException`):
   * Do NOT crash the consumer.
   * Extract original payload (byte array or string).
   * Extract metadata (topic, partition, offset, exception stack trace).
   * Construct a new `ProducerRecord` wrapping this info.
4. **Publish:** Send the new record to `source-topic-dlq` using a Kafka Producer.
5. **Acknowledge:** Commit the offset for the original message in `source-topic`.
6. **Continue:** The consumer moves to the next message. 

*Monitor the DLQ topic with alerts to identify and resolve systemic data issues.*
