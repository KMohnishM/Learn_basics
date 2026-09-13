# Kafka Reliability: Questions and Answers

**Q1: What is the purpose of replication in Kafka?**
A1: Replication ensures data durability and high availability. By copying partitions across multiple brokers, the system can tolerate broker failures without losing data.

**Q2: What is an In-Sync Replica (ISR)?**
A2: An ISR is a follower replica that is fully caught up with the leader partition. It has fetched the latest messages within the configured `replica.lag.time.max.ms` window.

**Q3: How do `acks=all` and `min.insync.replicas` work together?**
A3: When a producer uses `acks=all`, the leader broker will not acknowledge the write until the message has been written by at least `min.insync.replicas` (including the leader). This guarantees durability.

**Q4: What happens if the ISR size drops below `min.insync.replicas` while producers are writing with `acks=all`?**
A4: The broker will reject the writes and return a `NotEnoughReplicasException` to the producer. The partition remains available for reads but blocks writes to ensure data consistency.

**Q5: Explain the implications of `unclean.leader.election.enable=true`.**
A5: It allows a replica not in the ISR to become the leader if the current leader fails and no ISR replicas are available. This prioritizes availability over consistency and will result in data loss.

**Q6: Describe At-Least-Once delivery semantics.**
A6: Messages are guaranteed to be delivered and processed, but in failure scenarios (like network timeouts during acknowledgments), messages might be redelivered and processed multiple times.

**Q7: How does an Idempotent Producer prevent duplicate messages?**
A7: It assigns a Producer ID and sequence numbers to messages. The broker tracks the sequence numbers. If it receives a duplicate sequence number for a given Producer ID, it ignores the payload but returns a successful acknowledgment.

**Q8: What specific problem does the Kafka Transactions API solve?**
A8: It solves the problem of atomic multi-partition writes and offset commits. It ensures Exactly-Once Semantics in stream processing by grouping reading from source topics, producing to output topics, and committing consumer offsets into a single atomic transaction.

**Q9: What configuration must a consumer have to read transactional messages correctly?**
A9: The consumer must configure `isolation.level=read_committed`. This ensures it only processes messages that are part of successfully committed transactions.

**Q10: What is a Dead Letter Queue (DLQ) in Kafka?**
A10: A DLQ is a dedicated topic where applications route messages that they fail to process (e.g., due to invalid schema or transient errors) after a certain number of retries, allowing the main processing loop to continue.

**Q11: Why is an infinite retry loop on a consumer dangerous?**
A11: If a consumer infinitely retries a single message and blocks its thread, it stops processing new messages. If the retry loop exceeds `max.poll.interval.ms`, the consumer will be evicted from the group.

**Q12: How can you implement non-blocking exponential backoff?**
A12: Instead of sleeping the main thread, the application can publish failed messages to intermediate 'retry topics' (e.g., 1-min delay, 5-min delay). Separate consumers process these topics, handle the delays, and requeue or DLQ the messages.

**Q13: Which component decides which follower becomes the new leader?**
A13: The active Kafka Controller broker is responsible for monitoring broker health and electing new leaders for partitions when the existing leader fails.

**Q14: If a topic has a replication factor of 3 and `min.insync.replicas` of 2, how many broker failures can it tolerate while continuing to accept writes?**
A14: It can tolerate 1 broker failure. If one fails, 2 replicas remain (meeting the `min.insync.replicas` requirement), so writes with `acks=all` will still succeed.

**Q15: Does Kafka guarantee order across multiple partitions?**
A15: No, Kafka only guarantees message ordering within a single partition. If total ordering is required, you must use a topic with a single partition, though this severely limits scalability.
