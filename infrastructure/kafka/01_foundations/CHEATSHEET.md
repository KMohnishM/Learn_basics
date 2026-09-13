# Foundations Cheatsheet

## Terminology

| Term | Definition |
|---|---|
| **Broker** | A single Kafka server node. |
| **Topic** | A logical category for messages. |
| **Partition** | A physical subdivision of a topic, ordered and immutable. |
| **Offset** | A unique, sequential ID assigned to each message in a partition. |
| **Replica** | A copy of a partition stored on a different broker. |
| **Leader** | The replica that handles all reads and writes for a partition. |
| **Follower** | A replica that passive copies data from the leader. |
| **ISR (In-Sync Replica)** | A follower that is fully caught up with the leader. |
| **Controller** | The broker responsible for cluster state and leader election. |
| **Log Segment** | A physical file on disk containing a chunk of a partition's data. |

## Binary Message Layout

A Kafka message (Record) on disk consists of several fields to ensure integrity and provide metadata.

* **Length**: Size of the record.
* **Attributes**: Compression codec used, timestamp type, etc.
* **Timestamp**: Time the record was produced (or appended to the log).
* **Key Length**: Length of the key.
* **Key**: The message key (used for partitioning and compaction).
* **Value Length**: Length of the payload.
* **Value**: The actual message payload.
* **Headers**: Optional metadata (key-value pairs) added in Kafka 0.11+.

## KRaft vs Zookeeper

| Feature | Zookeeper | KRaft |
|---|---|---|
| **Architecture** | External cluster dependency | Internal, built into Kafka |
| **Consensus Protocol** | ZAB (Zookeeper Atomic Broadcast) | Raft |
| **Metadata Storage** | Zookeeper znodes | Kafka internal topic (`__cluster_metadata`) |
| **Scalability Limit** | ~200k partitions | Millions of partitions |
| **Failover Time** | Slower (requires fetching state from ZK) | Faster (standby controllers have state replicated) |
| **Management** | Harder (two systems to secure/monitor) | Simpler (single system) |
