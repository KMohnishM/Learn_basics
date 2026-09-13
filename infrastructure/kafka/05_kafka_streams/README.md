# Apache Kafka Streams

## Introduction to Kafka Streams

Apache Kafka Streams is a client library for building applications and microservices, where the input and output data are stored in Kafka clusters. It combines the simplicity of writing and deploying standard Java and Scala applications on the client side with the benefits of Kafka's server-side cluster technology. 

Kafka Streams allows you to perform continuous, real-time processing of data streams. It is designed to be highly scalable, elastic, fault-tolerant, and distributed.

### Core Concepts

1. **Stream:** A stream is the most important abstraction provided by Kafka Streams: it represents an unbounded, continuously updating data set. A stream is an ordered, replayable, and fault-tolerant sequence of immutable data records, where a data record is defined as a key-value pair.
2. **Stream Processing Application:** A Java application that makes use of the Kafka Streams library.
3. **Processor Topology:** A graph of stream processors (nodes) that are connected by streams (edges).

## Topology and StreamThreads

### Processor Topology

A processor topology defines the computational logic of the data processing that needs to be performed by a stream processing application. A topology is a graph of stream processors (nodes) that are connected by streams (edges).

There are two special types of processors in the topology:
- **Source Processor:** A special type of stream processor that does not have any upstream processors. It produces an input stream to its topology from one or multiple Kafka topics by consuming records from these topics and forwarding them to its down-stream processors.
- **Sink Processor:** A special type of stream processor that does not have down-stream processors. It sends any received records from its up-stream processors to a specified Kafka topic.

### StreamThreads

Kafka Streams enables concurrent processing by using threads. The configuration `num.stream.threads` allows you to specify the number of threads (StreamThreads) that the library will create to execute stream processing.

Each StreamThread executes one or more stream tasks. A stream task acts as the unit of parallelism in Kafka Streams. The library automatically creates a number of tasks based on the number of partitions of the input topics. For example, if you read from a topic with 5 partitions, Kafka Streams will create 5 stream tasks.

If you have `num.stream.threads = 2`, the 5 tasks will be distributed among the 2 threads (e.g., 3 tasks for thread 1, 2 tasks for thread 2). If you run multiple instances of your application (across different machines), the tasks will be distributed across all available threads in all instances.

#### Threading Model Details

Kafka Streams leverages the Kafka consumer coordinator to assign tasks to instances and threads. The `StreamThread` is essentially a loop that:
1. Polls records from Kafka (using the consumer).
2. Routes the records to the appropriate stream tasks.
3. Executes the processor topology for each record.
4. Flushes state stores and commits offsets periodically.

This threading model ensures that ordering is preserved per partition, as all records for a specific partition are always processed by the exact same stream task.

## KStream, KTable, and GlobalKTable

The Kafka Streams DSL provides three main abstractions for working with streams of data: KStream, KTable, and GlobalKTable.

### KStream

A `KStream` represents an abstraction of a record stream, where each data record represents a self-contained datum in the unbounded data set. 

You can think of a KStream as an insert-only stream. Every record is a new independent event. For example, a stream of financial transactions:
- Alice sends $100 to Bob
- Charlie sends $50 to Alice

In a KStream, both records are appended to the stream. There is no concept of updating a previous record.

```java
StreamsBuilder builder = new StreamsBuilder();
KStream<String, String> textLines = builder.stream("TextLinesTopic");
textLines.mapValues(v -> v.toUpperCase()).to("UppercasedTextLinesTopic");
```

### KTable

A `KTable` represents an abstraction of a changelog stream, where each data record represents an update or delete.

You can think of a KTable as an upsert stream. Records with the same key overwrite the previous value. If a record has a null value, it is considered a delete (tombstone).

For example, tracking the current balance of users:
- Record 1: {"Alice", $100} (Alice has $100)
- Record 2: {"Alice", $150} (Alice now has $150, overwriting the previous value)

A KTable provides a view of the "current state" of the stream.

```java
StreamsBuilder builder = new StreamsBuilder();
KTable<String, Long> userBalances = builder.table("UserBalancesTopic");
```

### GlobalKTable

A `GlobalKTable` is similar to a KTable, but with a crucial difference in how data is partitioned and distributed across the application instances.

- **KTable:** Data is partitioned. Each Kafka Streams instance (or task) only maintains the state for a subset of the partitions. When joining a KStream with a KTable, the data must be co-partitioned (same number of partitions, partitioned by the same key).
- **GlobalKTable:** Data is fully replicated. Every Kafka Streams instance maintains a full, complete copy of the underlying topic's data in its local state store.

GlobalKTable is extremely useful for broadcasting reference data (e.g., user profiles, product catalogs) to all instances, allowing you to join a stream with the reference data without worrying about co-partitioning. However, it requires more local storage space since every instance holds the entire dataset.

## RocksDB State Stores

Kafka Streams provides stateful processing operations, such as aggregations, joins, and windowing. To support this, it uses state stores.

By default, Kafka Streams uses **RocksDB** as its storage engine for persistent state stores. RocksDB is an embedded, highly performant, key-value store optimized for fast storage environments like SSDs.

### How State Stores Work

1. **Local Storage:** RocksDB writes data to the local disk of the machine running the Kafka Streams instance. This provides extremely fast read and write access for the stream processing tasks.
2. **Fault Tolerance (Changelog Topics):** Because local disks can fail, Kafka Streams automatically backs up all state store modifications to a compacted Kafka topic called a changelog topic.
3. **Recovery:** If an instance fails and is restarted (or moved to another machine), Kafka Streams restores the RocksDB state store by reading the data from the changelog topic before resuming processing.

### RocksDB Configuration and Tuning

RocksDB performance heavily depends on its configuration. By default, Kafka Streams provides a balanced configuration, but you can tune it by implementing the `RocksDBConfigSetter` interface.

Key areas for tuning:
- **Block Cache:** Used to cache uncompressed blocks of data in memory. Increasing the block cache size can significantly improve read performance.
- **Write Buffers (MemTable):** Data is initially written to an in-memory Write Buffer. When it fills up, it is flushed to disk as an SST (Static Sorted Table) file.
- **Compaction:** RocksDB performs background compactions to merge SST files and remove overwritten or deleted data. Tuning compaction algorithms can reduce write amplification.

```java
public class CustomRocksDBConfig implements RocksDBConfigSetter {
    @Override
    public void setConfig(final String storeName, final Options options, final Map<String, Object> configs) {
        BlockBasedTableConfig tableConfig = new BlockBasedTableConfig();
        // Set block cache to 256MB
        tableConfig.setBlockCacheSize(256 * 1024 * 1024L);
        // Set block size to 16KB
        tableConfig.setBlockSize(16 * 1024L);
        options.setTableFormatConfig(tableConfig);
        options.setMaxWriteBufferNumber(3);
    }
    
    @Override
    public void close(final String storeName, final Options options) {
        // Cleanup if necessary
    }
}
```

## Windowing

Windowing allows you to group records that have the same key into time-based buckets. This is essential for operations like aggregations (e.g., counting events per minute).

Kafka Streams supports several types of windowing:

### 1. Tumbling Windows

Tumbling windows are fixed-size, non-overlapping, and gap-less windows. A record belongs to exactly one window.

- Example: 5-minute tumbling window.
- Windows: [00:00 - 00:05), [00:05 - 00:10), [00:10 - 00:15)

```java
KGroupedStream<String, String> grouped = stream.groupByKey();
TimeWindowedKStream<String, String> windowed = grouped.windowedBy(TimeWindows.ofSizeWithNoGrace(Duration.ofMinutes(5)));
```

### 2. Hopping Windows

Hopping windows are fixed-size, overlapping windows. A record can belong to multiple windows. They are defined by a window size and an advance interval (hop size).

- Example: 5-minute window, advancing every 1 minute.
- Windows: [00:00 - 00:05), [00:01 - 00:06), [00:02 - 00:07)

```java
TimeWindowedKStream<String, String> windowed = grouped.windowedBy(
    TimeWindows.ofSizeWithNoGrace(Duration.ofMinutes(5)).advanceBy(Duration.ofMinutes(1))
);
```

### 3. Sliding Windows

Sliding windows are used for operations like joins. They are fixed-size windows that slide continuously over the time axis. Unlike tumbling or hopping windows, which are aligned to epochs, sliding windows are aligned to the timestamps of the actual records.

A sliding window is defined by a maximum time difference. Two records are in the same sliding window if the absolute difference between their timestamps is less than or equal to the window size.

```java
SlidingWindows sliding = SlidingWindows.ofTimeDifferenceWithNoGrace(Duration.ofMinutes(5));
```

### 4. Session Windows

Session windows are dynamically sized, data-driven windows. They group periods of activity separated by periods of inactivity (the inactivity gap).

- If a new record arrives within the inactivity gap of a previous record (with the same key), it is added to the existing session, and the session is expanded.
- If a new record arrives after the inactivity gap, a new session is created.

Session windows are ideal for analyzing user behavior (e.g., website visits).

```java
SessionWindowedKStream<String, String> windowed = grouped.windowedBy(
    SessionWindows.ofInactivityGapWithNoGrace(Duration.ofMinutes(30))
);
```

### Grace Period and Late Data

Windowing in Kafka Streams operates on event time (the timestamp embedded in the Kafka record). Because distributed systems experience network delays, records may arrive out of order or late.

The **grace period** defines how long a window remains open to accept late-arriving records after the window end time has passed (according to the stream's stream-time). Once the grace period expires, the window is closed, and any subsequent late records for that window are dropped.

## ksqlDB

ksqlDB is an event streaming database built on top of Kafka Streams. It provides a SQL interface for defining stream processing applications, making it accessible to users who are familiar with SQL but may not have Java programming expertise.

### Key Features of ksqlDB

1. **SQL Abstraction:** You can express complex stream processing topologies (filtering, joins, aggregations, windowing) using standard SQL syntax.
2. **Streams and Tables:** ksqlDB uses the same concepts of Streams (append-only) and Tables (mutable state) as the Kafka Streams API.
3. **Push and Pull Queries:**
   - **Push Queries:** Continuous queries that emit results as new data arrives (e.g., `SELECT * FROM STREAM EMIT CHANGES;`).
   - **Pull Queries:** Point-in-time queries against the current state of a materialized view (e.g., `SELECT * FROM TABLE WHERE KEY='X';`).
4. **Connect Integration:** ksqlDB integrates seamlessly with Kafka Connect, allowing you to run source and sink connectors directly using SQL statements (e.g., `CREATE SOURCE CONNECTOR...`).

### Architecture

ksqlDB operates in a client-server architecture. 
- **ksqlDB Server:** The engine that executes the stream processing logic. It translates SQL queries into underlying Kafka Streams topologies and runs them.
- **ksqlDB CLI/UI:** The interface used to submit queries and interact with the server.

### Example ksqlDB Query

Creating a stream from an existing Kafka topic:
```sql
CREATE STREAM users_stream (
    userid VARCHAR KEY,
    registertime BIGINT,
    gender VARCHAR,
    regionid VARCHAR
) WITH (
    KAFKA_TOPIC = 'users',
    VALUE_FORMAT = 'JSON'
);
```

Creating a materialized table by aggregating the stream:
```sql
CREATE TABLE users_per_region AS
SELECT regionid, COUNT(*) AS user_count
FROM users_stream
GROUP BY regionid
EMIT CHANGES;
```

In this example, ksqlDB automatically creates the necessary RocksDB state stores and changelog topics to maintain the `users_per_region` table.

## Advanced Topics

### Exactly-Once Semantics (EOS)

Kafka Streams supports Exactly-Once Semantics, which guarantees that a stream processing application will process each record exactly once, even in the event of failures.

To enable EOS, you configure the processing guarantee in the Streams configuration:
```java
Properties props = new Properties();
props.put(StreamsConfig.PROCESSING_GUARANTEE_CONFIG, StreamsConfig.EXACTLY_ONCE_V2);
```

Under the hood, EOS leverages Kafka's transactional capabilities (transactional producer) and consumer offsets to ensure that reading from input topics, updating state stores, and writing to output topics happen atomically.

### Custom Processors (Processor API)

While the DSL provides high-level abstractions (KStream, KTable), you can drop down to the Processor API for maximum control. The Processor API allows you to implement custom logic, manually interact with state stores, and schedule punctuation (periodic tasks based on time).

```java
public class MyProcessor implements Processor<String, String, String, String> {
    private ProcessorContext<String, String> context;
    private KeyValueStore<String, Integer> kvStore;

    @Override
    public void init(ProcessorContext<String, String> context) {
        this.context = context;
        this.kvStore = context.getStateStore("my-state-store");
        
        // Schedule a punctuation every 10 seconds
        context.schedule(Duration.ofSeconds(10), PunctuationType.WALL_CLOCK_TIME, timestamp -> {
            // Punctuation logic
        });
    }

    @Override
    public void process(Record<String, String> record) {
        // Custom processing logic
    }
}
```

### State Store Querying (Interactive Queries)

Interactive Queries allow you to query the state stores of a Kafka Streams application from outside the application (e.g., via a REST API). This turns your stream processing application into a distributed database.

To do this, you use the `KafkaStreams.store()` method to get a reference to a specific state store. If the application has multiple instances, you can use the `KafkaStreams.metadataForAllStreamsClients()` to find which instance hosts the partition containing the specific key you want to query.

### Summary

Kafka Streams provides a powerful, robust, and scalable framework for event streaming applications. By understanding the core abstractions (Topology, Streams, Tables), state management (RocksDB), and temporal processing (Windowing), developers can build complex real-time data pipelines. Tools like ksqlDB further democratize these capabilities by offering a familiar SQL interface over the Kafka Streams engine.
