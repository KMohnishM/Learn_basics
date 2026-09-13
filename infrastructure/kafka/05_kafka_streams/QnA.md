# Kafka Streams Q&A

**Q1: What is the primary difference between a KStream and a KTable?**
A: A KStream represents an insert-only (append-only) stream of independent records, where every event is appended. A KTable represents an upsert (changelog) stream, where records with the same key overwrite previous values, reflecting the current state.

**Q2: How does a GlobalKTable differ from a standard KTable?**
A: A KTable is partitioned, meaning each application instance holds only a subset of the data. A GlobalKTable is fully replicated, meaning every application instance holds a complete copy of the entire underlying dataset, useful for broadcasting reference data without requiring co-partitioning.

**Q3: What is the role of a StreamThread in Kafka Streams?**
A: A StreamThread is the execution unit in Kafka Streams. It polls records from Kafka, routes them to stream tasks, executes the processing topology, flushes state stores, and commits offsets. Multiple StreamThreads can run concurrently to parallelize processing.

**Q4: How does Kafka Streams achieve fault tolerance for its state stores?**
A: State stores (like RocksDB) are backed by compacted Kafka topics called changelog topics. If a local state store is lost due to an instance failure, Kafka Streams can perfectly reconstruct the state by reading from the changelog topic upon restart.

**Q5: What is the purpose of RocksDB in Kafka Streams?**
A: RocksDB is the default embedded key-value storage engine used by Kafka Streams to maintain local state for stateful operations (like aggregations and joins). It provides high-performance reads and writes to local disk.

**Q6: Explain the difference between Tumbling and Hopping windows.**
A: Tumbling windows are fixed-size and non-overlapping (e.g., every 5 minutes). Hopping windows are fixed-size but overlapping, defined by a window size and an advance interval (e.g., 5-minute window advancing every 1 minute).

**Q7: When would you use Session Windows instead of Time Windows?**
A: Session windows are dynamic and data-driven, defined by an inactivity gap. They are ideal for grouping periods of user activity (e.g., user sessions on a website) rather than arbitrary, fixed time buckets.

**Q8: What is a grace period in the context of windowing?**
A: A grace period dictates how long a window remains open to accept late-arriving records (based on their event time) after the window's nominal end time has passed according to the stream's progression.

**Q9: How does co-partitioning affect joins between a KStream and a KTable?**
A: To join a KStream and a KTable, both inputs must have the same number of partitions, and they must be partitioned by the same key format. This ensures that records with the same key from both inputs are processed by the same stream task.

**Q10: What is the Processor API, and when should you use it over the DSL?**
A: The Processor API is a lower-level API that allows developers to define custom processors, interact directly with state stores, and schedule periodic tasks (punctuation). It is used when the high-level DSL (KStream/KTable operations) cannot express the required logic.

**Q11: What is a tombstone record in the context of a KTable?**
A: A tombstone record is a Kafka message with a key and a null value. In a KTable (or compacted topic), it acts as a delete instruction, indicating that the entry for that key should be removed from the state store.

**Q12: How does ksqlDB relate to Kafka Streams?**
A: ksqlDB is an event streaming database built on top of the Kafka Streams library. It provides a SQL-like interface that translates queries into Kafka Streams topologies, executing them on a backend server.

**Q13: What does the `num.stream.threads` configuration do?**
A: It defines the number of parallel threads executing within a single instance of a Kafka Streams application. Increasing this value increases the concurrency of processing up to the number of input partitions.

**Q14: Explain the difference between push queries and pull queries in ksqlDB.**
A: Push queries are continuous and emit results as new data arrives in the stream. Pull queries are point-in-time lookups against the current state of a materialized view (like querying a traditional database).

**Q15: How do you achieve Exactly-Once Semantics (EOS) in Kafka Streams?**
A: EOS is enabled by setting `processing.guarantee="exactly_once_v2"`. This uses Kafka's transactional producer and consumer features to ensure that state updates, offset commits, and output records are written atomically.
