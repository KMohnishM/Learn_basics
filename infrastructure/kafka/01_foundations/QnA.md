# Module 1: Foundations Q&A

**Q1: What is the primary data structure Kafka uses for storage?**
A: Kafka uses an append-only, immutable commit log. Data is stored on disk in segments and read sequentially.

**Q2: How does Kafka achieve high throughput for disk reads?**
A: Kafka heavily utilizes the OS page cache and sequential I/O. It also uses the `sendfile` system call (Zero-copy) to transfer data directly from the page cache to the network socket, bypassing application memory.

**Q3: What is the difference between a Topic and a Partition?**
A: A topic is a logical grouping of messages, like a table in a database. A partition is a physical breakdown of a topic. Topics are split into multiple partitions for scalability and parallelism.

**Q4: What is an In-Sync Replica (ISR)?**
A: An ISR is a follower replica that has fully caught up with the leader replica up to a certain threshold (defined by time or offset lag). Only replicas in the ISR list are eligible to become leaders if the current leader fails.

**Q5: What happens when a Kafka topic is log compacted?**
A: Log compaction ensures that Kafka retains at least the last known value for each message key within the log of data for a single topic partition. Older records with the same key are periodically removed.

**Q6: What is a sparse index in Kafka?**
A: Kafka uses a sparse index (`.index` files) to map offsets to physical file positions. It does not index every single message; instead, it indexes messages at regular intervals. To find a message, Kafka performs a binary search on the index to find the nearest offset and then sequentially scans the log segment.

**Q7: Why are partitions the unit of parallelism?**
A: In a consumer group, each partition is assigned to exactly one consumer thread. Therefore, the maximum number of concurrent consumers reading from a topic is equal to the number of partitions.

**Q8: What is KRaft?**
A: KRaft (Kafka Raft) is the consensus protocol that replaces Zookeeper for managing Kafka cluster metadata. It stores metadata directly in a Kafka topic and uses Raft for leader election among controller nodes.

**Q9: What is the role of the Active Controller?**
A: The controller manages state for partitions and replicas. It handles broker failures by electing new leaders for partitions that were hosted on the failed broker, and it propagates these changes to the rest of the cluster.

**Q10: What is the High Watermark?**
A: The high watermark is the offset of the last message that has been successfully copied to all In-Sync Replicas. Consumers can only read messages up to the high watermark, ensuring they don't read data that might be lost if the leader fails.

**Q11: How does Kafka handle retention?**
A: Kafka retains data based on time (e.g., 7 days) or size (e.g., 10GB per partition). Once a log segment violates the retention policy, it is deleted from disk.

**Q12: What is the `__consumer_offsets` topic?**
A: An internal Kafka topic used to store the committed offsets for consumer groups. This allows consumers to resume reading from where they left off after a restart or rebalance.

**Q13: Can you decrease the number of partitions for a topic?**
A: No. You can only increase the number of partitions. Decreasing partitions is not supported because it would require massive data shuffling and re-keying logic.

**Q14: What is the difference between a Leader replica and a Follower replica?**
A: All read and write requests for a partition go to the Leader replica. Follower replicas passively fetch data from the leader to stay in sync.

**Q15: How does a Kafka cluster avoid the "split-brain" problem in KRaft mode?**
A: KRaft relies on the Raft consensus algorithm, which requires a strict majority (quorum) of voters to elect a leader. If the network partitions, only the partition with the majority of nodes can elect a controller, preventing split-brain.
