# Module 2: Producers Q&A

**Q1: What does the `acks=all` configuration mean?**
A: It means the leader replica will wait for all currently In-Sync Replicas (ISRs) to acknowledge they have successfully written the message to their local log before acknowledging the producer.

**Q2: How does a producer handle messages when a topic partition has no leader?**
A: The producer will receive a retriable error (like `NotLeaderOrFollowerException`). It will refresh its metadata to find the new leader and retry sending the batch, up to `delivery.timeout.ms`.

**Q3: What is the purpose of `linger.ms`?**
A: `linger.ms` introduces a small, artificial delay before sending a batch of messages to the broker. This allows more messages to accumulate in the batch, improving compression ratios and network efficiency at the cost of a slight increase in latency.

**Q4: How does Sticky Partitioning improve performance?**
A: When no key is provided, instead of round-robining every single message across partitions (which creates many small, inefficient batches), Sticky Partitioning assigns all messages to a single partition until the batch is full or `linger.ms` expires. This ensures larger batches are sent.

**Q5: What is the risk of setting `acks=1`?**
A: If the leader broker acknowledges the write and then crashes before the follower replicas have a chance to pull the data, that message is permanently lost, even though the producer received a success acknowledgement.

**Q6: How does Idempotence prevent duplicate messages?**
A: An idempotent producer assigns a unique Producer ID (PID) and monotonically increasing sequence numbers to every message. The broker tracks these. If a producer retries a message due to a network timeout, the broker recognizes the duplicate sequence number, ignores the write, but returns a success acknowledgement.

**Q7: What happens when the `RecordAccumulator` buffer is completely full?**
A: The `send()` method will block (wait) for a maximum time defined by `max.block.ms`. If space doesn't become available within that time, a `TimeoutException` is thrown.

**Q8: Why is compression applied at the batch level rather than the message level?**
A: Compression algorithms rely on finding repeated patterns in data. Compressing a single small message yields almost no benefit and adds overhead. Compressing a large batch of similar messages yields highly efficient compression ratios.

**Q9: What is `max.in.flight.requests.per.connection`?**
A: It dictates how many unacknowledged batches the producer can send to a single broker connection concurrently. Setting this > 1 improves throughput but, in older versions of Kafka without idempotence, could lead to message reordering if retries occur.

**Q10: What is the difference between a Serializer and a Partitioner?**
A: A Serializer converts the application object (e.g., a String or JSON object) into a byte array that Kafka can store. A Partitioner determines which specific partition of a topic the byte array should be sent to.

**Q11: When should you use asynchronous `send()` with callbacks vs synchronous `send().get()`?**
A: You should almost always use asynchronous `send()` with callbacks. Synchronous `send().get()` blocks the calling thread until the broker responds, destroying throughput.

**Q12: How do you guarantee absolute ordering of messages for a specific entity (e.g., a customer ID)?**
A: 1) Use the customer ID as the message key. 2) Ensure the topic has enough partitions from the start (changing partitions alters the hash mapping). 3) Enable idempotence to prevent reordering during retries.

**Q13: What happens if a message is larger than `batch.size`?**
A: The producer will not use the pre-allocated memory pool for that message. It will allocate a custom buffer just for that message and send it immediately. This is less efficient. It will fail if it exceeds `max.request.size`.

**Q14: What is the `transactional.id` used for?**
A: It is used by the Transactional Producer to guarantee atomic writes across multiple partitions. It ensures that if the producer application crashes and restarts, it can resume or abort ongoing transactions safely.

**Q15: How does the producer know the IP addresses of the brokers?**
A: The producer connects to the `bootstrap.servers` list provided in its configuration. It issues a Metadata Request to any of those nodes, and the broker responds with the full cluster topology, including the IP addresses of all partition leaders.
