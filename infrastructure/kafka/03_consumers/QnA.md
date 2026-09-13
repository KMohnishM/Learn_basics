# Kafka Consumers: Questions and Answers

**Q1: What is the primary role of a Consumer Group in Kafka?**
A1: A consumer group allows multiple consumer instances to coordinate and share the load of consuming data from a topic. It ensures that each partition is processed by exactly one consumer within the group, enabling horizontal scalability.

**Q2: How does the Group Coordinator determine if a consumer has failed?**
A2: The Group Coordinator expects periodic heartbeat requests from each consumer. If it does not receive a heartbeat within the configured `session.timeout.ms`, it considers the consumer dead and initiates a rebalance.

**Q3: What happens during a rebalance?**
A3: During a rebalance, the assignment of partitions to consumers is recalculated and redistributed. The coordinator revokes partitions from existing consumers and reassigns them based on the active members of the group and the configured assignment strategy.

**Q4: Describe the 'stop-the-world' effect in Eager Rebalancing.**
A4: In the Eager rebalancing protocol, all consumers in the group must stop processing, revoke all their assigned partitions, and rejoin the group. This causes a complete halt in consumption for the entire group until the new assignment is distributed.

**Q5: How does Incremental Cooperative Rebalancing (KIP-429) solve the 'stop-the-world' problem?**
A5: Cooperative rebalancing allows consumers to retain partitions that they will continue to own after the rebalance. Only partitions that need to move to another consumer are revoked, allowing continuous processing on the retained partitions.

**Q6: Compare RangeAssignor and RoundRobinAssignor.**
A6: RangeAssignor works on a per-topic basis, often leading to uneven distribution if consumers subscribe to multiple topics. RoundRobinAssignor distributes all available partitions across all subscribed topics evenly among all consumers, providing better balance.

**Q7: What is the primary benefit of the StickyAssignor?**
A7: The StickyAssignor provides a balanced distribution while minimizing the number of partitions that move between consumers during a rebalance. This reduces the overhead of tearing down and rebuilding state for partitions.

**Q8: Why might `commitSync()` impact consumer throughput?**
A8: `commitSync()` blocks the consumer thread until it receives a response from the broker confirming the offset commit. This network round-trip time directly reduces the time available for fetching and processing new records.

**Q9: What is the risk of relying solely on `commitAsync()`?**
A9: `commitAsync()` does not block and generally does not retry on failure. If a commit fails and the consumer subsequently crashes before a successful commit occurs, it may reprocess records it had already completed.

**Q10: When is it essential to use `commitSync()`?**
A10: `commitSync()` should be used before closing a consumer, during a rebalance operation (e.g., in a `ConsumerRebalanceListener`), or when strong consistency is required before acknowledging a transaction to external systems.

**Q11: What is Consumer Lag?**
A11: Consumer Lag is the numerical difference between the latest offset in a partition (Log End Offset) and the last offset committed by the consumer group. It represents the backlog of unprocessed messages.

**Q12: How does `max.poll.interval.ms` protect the consumer group?**
A12: If a consumer's processing logic hangs or takes too long, it might still send background heartbeats but fail to process records. `max.poll.interval.ms` sets a limit on the time between `poll()` calls. If exceeded, the consumer proactively leaves the group, allowing another instance to take over its partitions.

**Q13: What happens if you add more consumers to a group than there are partitions in the subscribed topic?**
A13: The excess consumers will remain idle. A partition can only be assigned to a single consumer within a group at any given time.

**Q14: Explain the `auto.offset.reset` configuration.**
A14: It dictates behavior when a consumer starts reading a partition without a valid committed offset (e.g., new group, or offset retention expired). `earliest` starts from the beginning, `latest` starts from new messages, and `none` throws an exception.

**Q15: Are Kafka Consumers thread-safe?**
A15: No, Kafka consumers are not thread-safe. A single `KafkaConsumer` instance should generally be accessed by only one thread. Multi-threaded consumption usually involves running multiple consumer instances, each in its own thread.
