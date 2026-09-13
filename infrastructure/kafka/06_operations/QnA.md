# Kafka Operations Q&A

**Q1: What happens when a topic reaches its `log.retention.bytes` limit?**
A: Kafka will start deleting the oldest log segments in the partition until the size of the partition falls below the configured limit, regardless of the messages' age.

**Q2: How does Log Compaction differ from the standard Delete retention policy?**
A: Delete discards old records based on age or size. Log compaction retains the most recent value for each specific message key, ensuring the final state of all keys is preserved indefinitely.

**Q3: What is a tombstone record, and what is its purpose in a compacted topic?**
A: A tombstone is a record with a specific key and a `null` value. It signals the Log Cleaner to permanently delete all previous records associated with that key during the next compaction cycle.

**Q4: Why might you avoid creating a topic with 10,000 partitions on a small cluster?**
A: Partitions introduce overhead (open file handlers, metadata, replication load). Too many partitions can lead to slow leader elections, increased Zookeeper/KRaft load, and cluster instability. 

**Q5: What is the significance of the `UnderReplicatedPartitions` JMX metric?**
A: It indicates the number of partitions that do not have enough in-sync replicas to satisfy the replication factor. It must always be 0; >0 indicates a failed broker, network issue, or a broker unable to keep up.

**Q6: How do you increase the number of partitions for an existing topic, and what is the risk?**
A: You use `kafka-topics.sh --alter --partitions N`. The risk is that if you are using key-based routing, the hashing algorithm will map existing keys to different partitions, breaking ordering guarantees for those keys.

**Q7: Can you decrease the number of partitions in an existing topic?**
A: No, Kafka does not support decreasing partitions. You must create a new topic with fewer partitions and use a tool (like MirrorMaker or Kafka Streams) to copy the data over.

**Q8: Explain the `BACKWARD` compatibility mode in Schema Registry.**
A: BACKWARD compatibility means consumers updated with the new schema can successfully process data written by producers using the old schema. You must update consumers before updating producers.

**Q9: In Schema Registry, what changes are allowed under `FORWARD` compatibility?**
A: Adding new fields and deleting optional fields. Old consumers can read data from new producers because they will ignore new fields and won't fail if optional fields are missing.

**Q10: What is the difference between Standalone and Distributed modes in Kafka Connect?**
A: Standalone runs all tasks on a single process, lacking fault tolerance. Distributed mode groups multiple workers into a cluster, storing configuration and state in Kafka topics, providing high availability and automatic task rebalancing.

**Q11: What is the `ActiveControllerCount` metric, and what does a value of 2 imply?**
A: It shows the number of active controllers in the cluster. It should always be 1. A value of 2 implies a "split-brain" scenario, often caused by Zookeeper/KRaft connection issues, leading to severe cluster instability.

**Q12: How are offsets managed for Kafka Connect Source connectors?**
A: Source connectors track their progress by writing offsets to an internal Kafka topic (e.g., `connect-offsets`). Upon restart, the connector reads this topic to resume ingestion from where it left off.

**Q13: What is a Preferred Replica Election?**
A: Over time, broker failures can cause leadership of partitions to drift away from their intended (preferred) brokers, causing load imbalance. Preferred Replica Election forces leadership back to the initially assigned broker for each partition.

**Q14: How does `delete.retention.ms` interact with tombstone records?**
A: It determines how long a tombstone record is kept in the log before it is permanently purged. This delay gives consumers time to read the tombstone and update their own local state before the marker disappears.

**Q15: What is the purpose of the `kafka-reassign-partitions.sh` tool?**
A: It is used to move partition replicas from one set of brokers to another. This is crucial for load balancing, migrating data off retiring brokers, or rebalancing data when adding new brokers to the cluster.
