# Apache Kafka Operations

## Topic Retention and Cleanup Policies

Kafka topics store data durably, but they don't store it forever (unless explicitly configured to do so). How long data is kept is governed by the topic's cleanup policy, which is controlled by the `cleanup.policy` configuration.

There are two primary cleanup policies in Kafka: `delete` (Time/Size-based Retention) and `compact` (Log Compaction).

### 1. Delete (Retention Policy)

The default `cleanup.policy` is `delete`. Under this policy, Kafka periodically evaluates log segments and discards them if they exceed specific time or size limits.

**Time-based Retention:**
- Configured via `log.retention.hours`, `log.retention.minutes`, or `log.retention.ms` (topic level: `retention.ms`).
- Default is typically 7 days (168 hours).
- A segment is eligible for deletion when the timestamp of its latest message is older than the retention period.

**Size-based Retention:**
- Configured via `log.retention.bytes` (topic level: `retention.bytes`).
- Default is usually -1 (infinite).
- Defines the maximum size of a single partition. If a partition exceeds this size, the oldest segments are deleted to free up space.

When both time and size limits are configured, whichever threshold is hit first triggers deletion.

### 2. Log Compaction

When `cleanup.policy` is set to `compact`, Kafka ensures that it always retains at least the last known value for each message key within the partition. This is highly useful for restoring state, configuration topics, or KTables in Kafka Streams.

**How Compaction Works:**
1. A Kafka partition is divided into the "head" (where new messages are appended) and the "tail" (where old messages reside).
2. The Log Cleaner is a background thread that periodically scans the tail of the log.
3. It builds a map of the latest offset for each key.
4. It then copies the log segments into new segments, filtering out older records that have newer updates for the same key.
5. The original segments are then replaced with the newly compacted segments.

**Tombstone Mechanics:**
To delete a key entirely from a compacted topic, a producer sends a record with the key and a `null` value. This is called a tombstone record.
- The Log Cleaner sees the tombstone and knows to delete all older records for that key.
- To prevent consumers from missing the deletion event, the tombstone itself is retained for a configurable period, defined by `delete.retention.ms` (default 24 hours).
- After `delete.retention.ms` has passed, the tombstone is purged during the next compaction cycle.

```bash
# Set cleanup policy to compact for an existing topic
kafka-configs.sh --bootstrap-server broker:9092 --alter --entity-type topics --entity-name my-topic --add-config cleanup.policy=compact
```

## Partition Capacity Sizing

Sizing partitions correctly is critical for performance, scalability, and load balancing in a Kafka cluster.

### Why Partition Sizing Matters

- **Parallelism:** The number of partitions dictates the maximum number of concurrent consumers within a consumer group. If you have 10 partitions, you can have at most 10 active consumers.
- **Throughput:** Partitions distribute load across brokers. More partitions mean the topic can be handled by more brokers simultaneously.
- **Overhead:** Each partition has overhead (file descriptors, Zookeeper/KRaft metadata, replication overhead). Too many partitions can destabilize a cluster.

### Guidelines for Sizing

1. **Calculate Throughput Requirements:**
   - Estimate target read throughput (`t_r`) and write throughput (`t_w`).
   - Benchmark a single producer throughput (`p`) and a single consumer throughput (`c`) for your specific hardware and message size.
   - Required partitions = Max(`t_r / c`, `t_w / p`).

2. **Rule of Thumb for Limits:**
   - A single broker should generally not host more than 4,000 partitions (including replicas).
   - An entire cluster should ideally stay under 200,000 partitions total (though KRaft expands these limits significantly compared to ZooKeeper).

3. **Future-Proofing:**
   - It is easy to add partitions later (`kafka-topics.sh --alter --partitions N`).
   - It is **impossible** to decrease the number of partitions without creating a new topic and migrating data.
   - Therefore, slightly over-provision initially, but don't go to extremes. Avoid using a prime number of partitions if you plan to use key-based routing, as changing partition counts breaks key hashing.

## Key JMX Metrics

Monitoring Kafka requires observing Java Management Extensions (JMX) metrics. Key metrics to monitor include:

### Broker Metrics

- **UnderReplicatedPartitions** (`kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions`): MUST be 0. Any value > 0 means a broker is down or struggling to keep up with replication.
- **ActiveControllerCount** (`kafka.controller:type=KafkaController,name=ActiveControllerCount`): Should be exactly 1 across the cluster. If 0, no controller exists. If >1, split-brain condition.
- **OfflinePartitionsCount** (`kafka.controller:type=KafkaController,name=OfflinePartitionsCount`): MUST be 0. Indicates partitions without an active leader, meaning they are unavailable for reading/writing.
- **BytesInPerSec / BytesOutPerSec** (`kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec`): Measures network traffic. Essential for capacity planning and detecting anomalies.
- **NetworkProcessorAvgIdlePercent** / **RequestHandlerAvgIdlePercent**: Should be > 30%. If lower, the broker is CPU/network bound.

### Consumer Metrics

- **RecordsLagMax** (`kafka.consumer:type=consumer-fetch-manager-metrics,client-id=*,name=records-lag-max`): The maximum lag in terms of number of records for any partition in this window. High lag indicates the consumer is too slow.
- **CommitRate** and **CommitLatency**: Monitors consumer offset commit performance.

## Kafka Connect

Kafka Connect is a framework included with Apache Kafka that integrates Kafka with other systems. It is designed to reliably and scalably stream data into and out of Kafka.

### Core Concepts

- **Connectors:** The logical job that defines where data should be copied to/from. Connectors manage the integration with the external system (e.g., JDBC Connector, S3 Connector).
- **Tasks:** Connectors break down jobs into Tasks. Tasks perform the actual data copying. They provide the parallelism.
- **Workers:** The running processes that execute Connectors and Tasks. In distributed mode, multiple workers form a Connect cluster.
- **Source Connectors:** Ingest data from an external system into Kafka topics (e.g., reading rows from a Postgres database and publishing to Kafka).
- **Sink Connectors:** Export data from Kafka topics to an external system (e.g., reading from Kafka and writing files to Amazon S3).

### Deployment Modes

- **Standalone Mode:** A single worker process runs all connectors and tasks. Simple to setup, but lacks fault tolerance and scalability. Suitable for development or lightweight jobs.
- **Distributed Mode:** Multiple workers form a cluster. Configuration, status, and offsets are stored in internal Kafka topics. Provides high availability, scalability, and automatic rebalancing of tasks if a worker fails.

## Schema Registry and Compatibility Modes

When producing data to Kafka, especially structured data like Avro, Protobuf, or JSON Schema, it is vital to enforce schemas to prevent breaking consumers. The Confluent Schema Registry provides a centralized repository for schemas.

### How it Works

1. **Producer:** Before sending a message, the producer checks the schema against the Registry. If new, it registers it (if allowed). It then serializes the message, embedding a unique Schema ID (not the full schema) at the beginning of the payload.
2. **Kafka:** Stores the serialized binary data containing the Schema ID.
3. **Consumer:** Reads the payload, extracts the Schema ID, fetches the corresponding schema from the Registry (caching it locally), and deserializes the data.

### Compatibility Modes

Schemas evolve over time. The Schema Registry enforces compatibility rules when a new schema version is registered, ensuring changes won't break existing applications.

**1. BACKWARD (Default)**
- **Meaning:** Consumers using the *new* schema can read data produced by the *old* schema.
- **Allowed Changes:** Deleting fields, adding optional fields.
- **Upgrade Path:** Upgrade Consumers first, then Producers.

**2. FORWARD**
- **Meaning:** Consumers using the *old* schema can read data produced by the *new* schema.
- **Allowed Changes:** Adding fields, deleting optional fields.
- **Upgrade Path:** Upgrade Producers first, then Consumers.

**3. FULL**
- **Meaning:** Both BACKWARD and FORWARD compatible.
- **Allowed Changes:** Modifying optional fields only (adding/deleting).
- **Upgrade Path:** Any order.

**4. NONE**
- **Meaning:** Schema validation is disabled. All changes are accepted.

**Transitive Compatibility:**
Modes like `BACKWARD_TRANSITIVE` enforce that the new schema is compatible not just with the immediately previous version, but with *all* previous versions registered for that subject.

```bash
# Check compatibility of a new schema via API
curl -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  --data '{"schema": "{\"type\": \"string\"}"}' \
  http://localhost:8081/compatibility/subjects/my-subject/versions/latest
```

## Security and ACLs

Operating Kafka securely involves implementing Encryption, Authentication, and Authorization.

### 1. Encryption (SSL/TLS)
Secures data in transit between clients and brokers, and between brokers. Prevents packet sniffing. It involves setting up keystores and truststores on the brokers.

### 2. Authentication (SASL/SSL)
Validates the identity of clients connecting to the broker. Common mechanisms include:
- **SASL/PLAIN:** Username and password (must be used over SSL).
- **SASL/SCRAM:** Salted Challenge Response (more secure than PLAIN).
- **SASL/GSSAPI (Kerberos):** Used in enterprise environments.
- **mTLS (Mutual TLS):** Uses client certificates for authentication.

### 3. Authorization (ACLs)
Once authenticated, Access Control Lists (ACLs) dictate what a user can do (e.g., User 'Alice' can Read from Topic 'Sales', but cannot Write). Kafka uses an authorizer (like the default `AclAuthorizer`) to check permissions.

```bash
# Example: Allow user Alice to read from topic 'test-topic'
kafka-acls.sh --authorizer-properties zookeeper.connect=localhost:2181 \
  --add --allow-principal User:Alice --operation Read --topic test-topic
```

## Maintenance Operations

### Reassigning Partitions
When adding new brokers to a cluster, existing partitions do not automatically move to the new brokers. You must manually generate and execute a partition reassignment plan to balance the load.
- Tool: `kafka-reassign-partitions.sh`
- This tool generates a JSON plan of where replicas should go, which you then execute to trigger the data movement.

### Preferred Replica Election
Each partition has a "preferred" leader (the broker that was designated as the leader when the topic was created). If brokers fail and restart, leadership may shift to other brokers, causing imbalance.
- Tool: `kafka-leader-election.sh`
- Restores leadership to the preferred replica to rebalance cluster load. (Often handled automatically by `auto.leader.rebalance.enable=true`).
