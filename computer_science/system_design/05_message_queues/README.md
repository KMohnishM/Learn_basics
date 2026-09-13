# Module 5: Message Queues and Event Streams

> **Goal**: Deeply understand asynchronous communication, the differences between message queues and event streams, and the internals of industry-standard systems like Kafka and RabbitMQ. Master delivery guarantees, dead letter queues, and advanced patterns like the Outbox pattern.

---

## Table of Contents

1. [Why Async Communication?](#1-why-async-communication)
2. [Message Queues vs Event Streams](#2-message-queues-point-to-point-vs-event-streams-pubsub)
3. [Kafka Architecture Deep Dive](#3-kafka-architecture-deep-dive)
4. [Delivery Guarantees](#4-delivery-guarantees)
5. [RabbitMQ Internals](#5-rabbitmq-internals)
6. [Dead Letter Queues (DLQ)](#6-dead-letter-queues-dlq)
7. [The Outbox Pattern](#7-the-outbox-pattern)
8. [Advanced Patterns](#8-advanced-patterns)
9. [Performance Tuning](#9-performance-tuning)

---

## 1. Why Async Communication?

Modern distributed systems rely heavily on communication between microservices. This communication can be broadly categorized into Synchronous and Asynchronous.

### 1.1 Synchronous vs Asynchronous

**Synchronous Communication (RPC/REST/gRPC)**:
The caller sends a request and blocks (waits) until the receiver processes the request and sends a response.
- **Example**: An HTTP GET request to fetch user profile data.
- **Characteristics**: Strong consistency, immediate feedback, but tightly coupled.
- **Failure Mode**: If the downstream service is down, the caller fails or times out. Cascading failures are common.

**Asynchronous Communication (Queues/Streams)**:
The caller sends a message to an intermediary broker and immediately continues its work without waiting for the receiver to process the message.
- **Example**: Publishing a `UserCreated` event to Kafka.
- **Characteristics**: Eventual consistency, fire-and-forget, loosely coupled.
- **Failure Mode**: If the downstream service is down, the message remains in the queue. The sender is unaffected.

```text
Synchronous Flow (Tight Coupling):
[Service A] ---(Wait 500ms)---> [Service B] ---(Wait 200ms)---> [Service C]
    |                               ^                               ^
    |___(Fails if B or C is down)___|_______________________________|

Asynchronous Flow (Loose Coupling):
[Service A] ---> [Message Broker] ---> (A continues work immediately)
                        |
                        +---> [Service B] (Reads at its own pace)
                        +---> [Service C] (Reads at its own pace)
```

### 1.2 Problems Solved by Async

1. **Temporal Decoupling**: Services do not need to be online at the same time. Service A can produce messages even if Service B is down for maintenance. When Service B comes back online, it resumes processing where it left off.
2. **Load Leveling (Buffering)**: Protects downstream systems from traffic spikes. If a marketing campaign causes a 10x spike in orders, the Order Service can quickly write to a queue. The Payment Service can process these orders at its maximum safe capacity (e.g., 100/sec) without being overwhelmed.
3. **Fan-out**: A single event can be consumed by multiple independent services without the producer needing to know about them. For example, a `UserSignup` event can trigger the Welcome Email Service, the Analytics Service, and the Fraud Detection Service simultaneously.

### 1.3 When to Use Sync vs Async

- **Use Sync (REST/gRPC)** when:
  - You need immediate confirmation of an action (e.g., "Did my credit card get charged?").
  - The caller needs the result to proceed (e.g., querying for a user's balance).
  - The operation is a simple read query.
- **Use Async (Queues/Streams)** when:
  - The work is resource-intensive and can be done in the background (e.g., video encoding, PDF generation).
  - You need to notify multiple services of a state change (Event-Driven Architecture).
  - You want to build resilient systems that survive downstream outages.

---

## 2. Message Queues (Point-to-Point) vs Event Streams (Pub/Sub)

While often used interchangeably, Message Queues (like RabbitMQ) and Event Streams (like Kafka) have fundamentally different architectures and use cases.

### 2.1 Message Queues (e.g., RabbitMQ, SQS, ActiveMQ)

Message queues implement the **Point-to-Point** or **Competing Consumers** pattern.
- **Smart Broker, Dumb Consumer**: The broker keeps track of which messages have been consumed.
- **Message Deletion**: Once a consumer successfully processes a message and sends an Acknowledgement (ACK), the broker deletes the message.
- **Competing Consumers**: Multiple consumers can listen to the same queue to scale out processing. The broker ensures each message is delivered to only ONE consumer.
- **Use Case**: Task processing, worker queues (e.g., sending emails, resizing images).

```text
Message Queue Model:
[Producer] ---> [Message Queue (Broker)]
                       |
                       +--> Message 1 ---> [Consumer A] (ACKs -> Msg 1 deleted)
                       +--> Message 2 ---> [Consumer B] (ACKs -> Msg 2 deleted)
```

### 2.2 Event Streams (e.g., Kafka, Kinesis)

Event streams implement the **Publish-Subscribe (Pub/Sub)** and **Append-Only Log** patterns.
- **Dumb Broker, Smart Consumer**: The broker just stores messages sequentially. Consumers keep track of their own position (offset).
- **Retention**: Messages are NOT deleted upon consumption. They are retained for a configured period (e.g., 7 days) or size.
- **Multiple Consumer Groups**: Different groups of consumers can read the exact same stream of messages independently, each maintaining its own offset.
- **Use Case**: Event sourcing, log aggregation, real-time analytics, microservice state replication.

```text
Event Stream Model:
[Producer] ---> [Append-Only Log (Kafka Topic)]
                | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
                -----------------------------
                       ^              ^
                       |              |
      [Consumer Group A]              [Consumer Group B]
      (Offset: 2)                     (Offset: 5)
      (Analytics Service)             (Search Indexing Service)
```

### 2.3 Comparison Table

| Feature | Message Queue (RabbitMQ/SQS) | Event Stream (Kafka/Kinesis) |
| :--- | :--- | :--- |
| **Data Structure** | Queue (FIFO, often memory-first) | Append-only distributed log (Disk) |
| **Message Lifetime** | Deleted after ACK | Retained by time/size policy |
| **State Tracking** | Broker tracks acks per message | Consumer tracks offset per partition |
| **Ordering** | Hard to guarantee with multiple consumers | Guaranteed per partition |
| **Replayability** | No (messages are gone) | Yes (just rewind the offset) |
| **Fan-out** | Requires complex routing (Exchanges) | Native (multiple consumer groups) |
| **Primary Use** | Task distribution, async workers | Event sourcing, stream processing |

---

## 3. Kafka Architecture Deep Dive

Apache Kafka is a distributed event streaming platform. It is fundamentally a distributed commit log.

### 3.1 Core Concepts

- **Broker**: A single Kafka server. A cluster consists of multiple brokers.
- **Topic**: A logical category or feed name to which records are published (e.g., `orders`).
- **Partition**: A topic is divided into multiple partitions for scalability. A partition is an ordered, immutable sequence of records. This is the unit of parallelism in Kafka.
- **Replica**: Copies of a partition stored across different brokers for fault tolerance.
- **Leader & Follower**: For each partition, one replica is the "Leader" (handles all reads and writes). The others are "Followers" (passively replicate from the leader).
- **ISR (In-Sync Replicas)**: The subset of replicas that are fully caught up with the leader. If a leader fails, only a replica in the ISR can be elected as the new leader.

```text
Kafka Topic Partitioning and Replication (RF=3):
Broker 1: [TopicA-Part0 (Leader)]  [TopicA-Part2 (Follower)]
Broker 2: [TopicA-Part1 (Leader)]  [TopicA-Part0 (Follower)]
Broker 3: [TopicA-Part2 (Leader)]  [TopicA-Part1 (Follower)]
```

### 3.2 Producer Internals

When a producer sends a message, it doesn't send it immediately.
- **Batching**: Messages are grouped into batches by partition. Controlled by `batch.size` (bytes) and `linger.ms` (time to wait for more messages). This drastically improves throughput.
- **Compression**: Batches can be compressed (e.g., snappy, lz4, zstd) on the producer side, stored compressed on the broker, and decompressed by the consumer.
- **Acks (Acknowledgements)**:
  - `acks=0`: Fire and forget. Maximum throughput, highest data loss risk.
  - `acks=1`: Leader writes to local log and acks. If leader crashes before followers replicate, data is lost.
  - `acks=all` (or `-1`): Leader waits for all replicas in the ISR to write before acking. Highest durability.
- **Retries**: Configurable automatic retries for transient errors.
- **Idempotent Producer**: (`enable.idempotence=true`). Prevents duplicates caused by network retries. Kafka assigns a Producer ID (PID) and sequence numbers to messages. The broker deduplicates based on this combination.

### 3.3 Consumer Internals

- **Consumer Groups**: Consumers with the same `group.id` form a group.
- **Partition Assignment**: Each partition in a topic is consumed by EXACTLY ONE consumer within a consumer group.
  - If Consumers > Partitions, some consumers sit idle.
  - If Partitions > Consumers, some consumers handle multiple partitions.
  - **Assignment Strategies**: Range, RoundRobin, Sticky, CooperativeSticky.
- **Offsets**: A unique integer identifying the position of a record within a partition.
- **Offset Committing**: Consumers must commit their offsets to Kafka (to a special internal topic `__consumer_offsets`) to record their progress.
  - **Auto Commit**: (`enable.auto.commit=true`). Commits periodically in the background. Dangerous if a crash happens after reading but before processing (data loss).
  - **Manual Commit**: Committing explicitly after business logic is complete (`commitSync()` or `commitAsync()`). Guarantees at-least-once processing.

### 3.4 Log Structure on Disk

Kafka writes data sequentially to disk, bypassing the JVM heap and relying heavily on the OS Page Cache.
- A partition is a directory on disk.
- It is split into **Segment Files** (e.g., 1GB chunks).
- Each segment has:
  - `.log` file: The actual message data.
  - `.index` file: Maps offsets to byte positions in the `.log` file.
  - `.timeindex` file: Maps timestamps to offsets.
- **Sparse Index**: The `.index` file doesn't map every single offset. It maps roughly every 4KB of data. To find an offset, Kafka binary searches the index, then linearly scans the log file from that point.

### 3.5 Ordering Guarantees

- **Kafka guarantees ordering strictly PER PARTITION.**
- If you need global ordering across an entire topic, you must use a topic with exactly 1 partition.
- **Trade-off**: A 1-partition topic limits your throughput to a single consumer. You lose horizontal scalability.
- **Best Practice**: Use a good partition key (e.g., `user_id`, `order_id`). All events for the same key will go to the same partition, ensuring causal ordering for that entity, while still allowing the system to scale horizontally across many keys.

### 3.6 Retention Policies

Kafka does not delete messages when consumed. Messages are deleted based on:
1. **Time-based**: e.g., `log.retention.hours=168` (7 days).
2. **Size-based**: e.g., `log.retention.bytes=1073741824` (1GB per partition).

**Log Compaction**:
For specific use cases (like CDC - Change Data Capture, or restoring state), you only care about the latest state of a key.
- If compaction is enabled, Kafka periodically scans the log and deletes older records for a given key, keeping only the most recent one.
- **CRITICAL**: Log compaction retains only the LATEST value per key, not all events. It is a "changelog" semantic.
- A null payload for a key acts as a "tombstone" (delete marker).

### 3.7 Rebalancing

Rebalancing is the process of reassigning partitions among consumers in a group.
- **Triggers**: A consumer joins, a consumer crashes/leaves, or topic partitions change.
- **Stop-the-World Rebalancing**: Traditional approach. All consumers stop fetching, revoke their partitions, and wait for new assignments. Causes latency spikes.
- **Cooperative Incremental Rebalancing**: Modern approach. Consumers keep their existing partitions unless they need to be moved, minimizing disruption.

### 3.8 Kafka Connect & Schema Registry

- **Kafka Connect**: A framework for connecting Kafka with external systems without writing code.
  - **Source Connectors**: Stream data from a system INTO Kafka (e.g., Debezium for DB CDC).
  - **Sink Connectors**: Stream data FROM Kafka into a system (e.g., Elasticsearch, S3, Snowflake).
- **Schema Registry**: A centralized repository for schemas (Avro, Protobuf, JSON Schema).
  - Producers fetch schemas and serialize data compactly.
  - Consumers fetch schemas to deserialize.
  - Enforces **Compatibility Modes**:
    - `BACKWARD`: Consumers using new schema can read data written by old schema. (Safe to upgrade consumers first).
    - `FORWARD`: Consumers using old schema can read data written by new schema. (Safe to upgrade producers first).
    - `FULL`: Both backward and forward compatible.

---

## 4. Delivery Guarantees

Distributed messaging systems offer different levels of delivery guarantees.

### 4.1 At-Most-Once (Fire and Forget)
- **Mechanism**: Producer sends and doesn't wait for ack. Consumer reads and commits offset BEFORE processing.
- **Result**: Messages may be lost (if network drops or consumer crashes during processing), but are never duplicated.
- **Use Case**: Telemetry, non-critical logging where data loss is acceptable.

### 4.2 At-Least-Once
- **Mechanism**: Producer waits for ack (retries on failure). Consumer reads, processes, and commits offset AFTER processing.
- **Result**: Messages are never lost, but may be processed multiple times (if producer retries a successful write due to network timeout, or if consumer crashes after processing but before committing).
- **Requirement**: **Idempotency** is strictly required downstream.

### 4.3 Exactly-Once (EOS)
- **Within Kafka**: Achieved using Idempotent Producers (deduplication on broker) + Kafka Transactions. A stream processing app can read from Kafka, process, and write back to Kafka atomically (read-process-write).
- **IMPORTANT LIMITATION**: Kafka transactions only guarantee EOS *within* Kafka.
- If your consumer reads from Kafka and writes to an external sink (like a PostgreSQL database or calling an external HTTP API), Kafka's EOS cannot help you. You must use:
  - Idempotent sinks (e.g., database UPSERTs).
  - Two-Phase Commit (2PC) - generally avoided due to performance overhead.

### 4.4 Idempotency Patterns

Since At-Least-Once is the standard, idempotency is crucial.
1. **Deduplication Key**: Generate a unique UUID for every message. The consumer tracks processed IDs in a database or Redis cache. If ID exists, skip processing.
2. **Idempotency Token / Revision Number**: Use a monotonic version number on entities. Update DB only if `event.version > current_db.version`.
3. **Database UPSERT**: `INSERT ... ON CONFLICT (id) DO UPDATE`. Sending the same data twice yields the exact same final state.

---

## 5. RabbitMQ Internals

RabbitMQ is a mature, feature-rich message broker based on the AMQP (Advanced Message Queuing Protocol).

### 5.1 The AMQP Model

Unlike Kafka where producers write directly to topics, RabbitMQ introduces a routing layer.
- **Producer**: Sends messages.
- **Exchange**: Receives messages from producers and routes them to queues based on rules (bindings).
- **Queue**: Buffers messages until consumed.
- **Consumer**: Reads from queues.

**Exchange Types**:
1. **Direct**: Routes to a queue where the `routing_key` exactly matches the binding key. (e.g., routing key `pdf_tasks` -> Queue `pdf_worker`).
2. **Fanout**: Routes to ALL bound queues indiscriminately. (Pub/Sub pattern).
3. **Topic**: Routes based on wildcard matches in the routing key (e.g., `logs.error.*`, `*.critical`).
4. **Headers**: Routes based on message headers instead of routing keys.

### 5.2 Consumer Prefetch (`basic.qos`)

This is the most critical setting in RabbitMQ for performance and stability.
- **IMPORTANT**: Without setting a prefetch count, RabbitMQ's default behavior is to push ALL unacknowledged messages to the first consumer it finds as fast as the network allows. It does NOT round-robin them automatically if one consumer gets overwhelmed.
- If you have 100,000 messages in a queue and start a consumer, RabbitMQ will dump all 100,000 into the consumer's RAM.
- **Solution**: Set `basic.qos` (prefetch count) to a small number, e.g., 1 or 10.
- With `prefetch=1`, RabbitMQ gives 1 message to Consumer A. It will not give Consumer A another message until A sends an ACK. Meanwhile, it gives the next message to Consumer B. **This enables true fair dispatch and round-robin load balancing.**

### 5.3 Message Durability

To ensure messages survive a RabbitMQ server crash, two things must be true:
1. The Queue must be declared as **Durable** (persisted to disk).
2. The Message must be published with `delivery_mode=2` (**Persistent**).
Writing to disk adds latency but guarantees safety.

### 5.4 Dead Letter Exchange (DLX)

In RabbitMQ, a DLQ is implemented using a Dead Letter Exchange.
Messages are routed to a DLX when:
- The message is rejected (`basic.reject` or `basic.nack`) with `requeue=false`.
- The message expires (TTL - Time To Live reached).
- The queue length limit is exceeded.

### 5.5 Kafka vs RabbitMQ Trade-offs

| Feature | RabbitMQ | Kafka |
| :--- | :--- | :--- |
| **Architecture** | Smart Broker / Dumb Consumer | Dumb Broker / Smart Consumer |
| **Routing** | Highly flexible (Exchanges) | Basic (Topics) |
| **Message Order** | Hard with competing consumers | Strict per partition |
| **Throughput** | ~50k - 100k msg/sec | Millions of msg/sec |
| **Latency** | Sub-millisecond | Few milliseconds (due to batching) |
| **Retention** | Ephemeral (deleted on ACK) | Persistent (logs on disk) |
| **Replay** | No | Yes |

---

## 6. Dead Letter Queues (DLQ)

A DLQ is a holding area for messages that cannot be processed successfully.

### 6.1 Why Messages end up in a DLQ
1. **Poison Pills**: The message payload is malformed or cannot be deserialized (e.g., missing required fields, bad JSON). No amount of retrying will fix this.
2. **Max Retries Exceeded**: A transient error (e.g., downstream DB is down) lasts too long. After N retries, the message is moved to the DLQ to avoid blocking the queue.
3. **TTL Expiry**: The message sat in the queue too long and is no longer relevant.
4. **Explicit Rejection**: The consumer explicitly rejects the message.

### 6.2 DLQ Best Practices
- **Never ignore the DLQ**: A growing DLQ means data loss or business process failures.
- **Monitoring and Alerting**: Set up strict alerts on DLQ depth. If it exceeds 0 (or a small threshold), page an engineer.
- **Include Metadata**: When moving a message to a DLQ, always append headers detailing the reason for failure, the timestamp, and the original queue name.

### 6.3 Replay Strategies
- **Manual Inspection**: Engineers inspect the DLQ, fix the underlying bug (e.g., deploy a new parser), and manually requeue the messages.
- **Automated Replay**: A script pulls from the DLQ and puts them back into the main queue or a dedicated retry queue with exponential backoff.

---

## 7. The Outbox Pattern

The Outbox Pattern solves the distributed data management problem of atomically updating a database and publishing a message.

### 7.1 The Dual-Write Problem

```python
# Anti-pattern: Dual Write
def create_order(order_data):
    db.execute("INSERT INTO orders ...") # Step 1: Write to DB
    kafka.produce("OrderCreated", order_data) # Step 2: Publish Event
```
**Failure Modes**:
- If Step 1 succeeds and Step 2 fails (network error), the database is updated but the system never knows. Inconsistent state.
- If you swap them (publish first, then DB), and the DB write fails, downstream services process a phantom order.

### 7.2 The Solution: Transactional Outbox

Instead of writing directly to the message broker, write the event to an "outbox" table in the SAME database, within the SAME local transaction.

```python
# The Outbox Pattern
def create_order(order_data):
    with db.transaction():
        # Step 1: Write business entity
        db.execute("INSERT INTO orders (id, amount) VALUES (1, 100)")
        
        # Step 2: Write event to outbox table IN THE SAME TRANSACTION
        event_payload = json.dumps({"order_id": 1, "amount": 100})
        db.execute("INSERT INTO outbox (aggregate_id, event_type, payload) VALUES (1, 'OrderCreated', ?)", event_payload)
```
Because it is a single relational transaction, it is atomic. Either both succeed or both fail.

### 7.3 Publishing from the Outbox

How do messages get from the outbox table to Kafka?

**Approach 1: Polling Publisher (Worker)**
A background worker continuously queries the outbox table:
`SELECT * FROM outbox WHERE published = false ORDER BY id ASC LIMIT 100;`
It publishes to Kafka, then marks them as `published = true` (or deletes them).
- **Pros**: Simple to implement.
- **Cons**: Polling overhead on the DB, higher latency.

**Approach 2: Change Data Capture (CDC) - e.g., Debezium**
A tool like Debezium tails the database's Transaction Log (WAL in Postgres, Binlog in MySQL). When it sees an insert into the `outbox` table, it instantly streams it to Kafka.
- **Pros**: Extremely low latency, zero overhead on the database queries, highly scalable.
- **Cons**: Complex infrastructure setup.

---

## 8. Advanced Patterns

### 8.1 Event Sourcing
Instead of storing the current state of an entity, you store a sequence of state-changing events.
- **Traditional**: `UPDATE account SET balance = 150 WHERE id = 1`
- **Event Sourcing**: Store `AccountOpened(0)`, `Deposited(100)`, `Deposited(50)`.
- The current state is derived by replaying the events.
- **Event Store**: A specialized database for storing these append-only events.
- **Projections**: Views of the data built by listening to the event stream, optimized for reading.

### 8.2 CQRS (Command Query Responsibility Segregation)
Separates the write model (Commands) from the read model (Queries).
- Writes go to a normalized transactional database.
- An event stream updates one or more denormalized read databases (e.g., Elasticsearch, Redis).
- Allows optimizing writes and reads independently. Often paired with Event Sourcing.

### 8.3 Saga Pattern
Solves the problem of distributed transactions across microservices.
- **Choreography**: Decentralized. Service A emits an event, Service B listens and does its part, emits another event. No central brain. (Good for simple workflows).
- **Orchestration**: Centralized. A Saga Orchestrator service manages the workflow, sending commands to Services A, B, and C, and handling compensating transactions (rollbacks) if a step fails. (Good for complex workflows).

### 8.4 Change Data Capture (CDC)
The process of capturing changes made in a database and delivering them in real-time to downstream systems.
- E.g., Debezium reads the PostgreSQL WAL (Write-Ahead Log) and pushes every INSERT/UPDATE/DELETE as an event to Kafka.
- Enables zero-downtime migrations, search index updates, and cache invalidation.

---

## 9. Performance Tuning

### 9.1 Kafka Tuning
- **Throughput vs Latency**: 
  - Increase `batch.size` (e.g., 64KB -> 256KB) and `linger.ms` (e.g., 0 -> 10ms) to increase throughput at the cost of slight latency.
- **Compression**: Use `snappy` or `zstd` to save network bandwidth and disk space, increasing overall throughput.
- **Partition Count**: Rule of thumb: Aim for a single partition to handle 10-100 MB/s of traffic. Too few partitions limits consumer parallelism. Too many partitions overloads the broker's metadata management. (Target max 4000 partitions per broker).

### 9.2 Consumer Lag Monitoring
Consumer lag is the difference between the latest offset produced and the latest offset committed by the consumer.
- **Real-time systems**: Target lag < 1 second.
- **Near-real-time / Batch**: Target lag < 1 minute.
- Consistently growing lag means your consumers cannot keep up with your producers. You must scale out the consumer group (and ensure you have enough partitions).

### 9.3 Performance Comparison Numbers
Rough benchmarks on standard hardware (for intuition):
- **RabbitMQ**: ~50,000 - 100,000 messages/sec per broker. Latency ~1ms.
- **Amazon SQS**: Virtually unlimited throughput (horizontally scales transparently). Latency ~10-20ms.
- **Apache Kafka**: ~1,000,000+ messages/sec per broker (batching is key). Latency ~2-5ms. Disk sequential write speed is the limit.
