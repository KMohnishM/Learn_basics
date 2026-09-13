# Kafka Streams Cheatsheet

## KStream vs KTable vs GlobalKTable Matrix

| Feature | KStream | KTable | GlobalKTable |
| :--- | :--- | :--- | :--- |
| **Concept** | Append-only stream of independent events | Upsert stream representing current state | Fully replicated upsert stream |
| **Record Meaning** | Insert (New Event) | Upsert (Update) or Delete (if value is null) | Upsert (Update) or Delete (if value is null) |
| **Partitioning** | Partitioned across instances | Partitioned across instances | **Not partitioned**; fully replicated on all instances |
| **Use Case** | Financial transactions, logs, clicks | Current user balances, latest configurations | Broadcasting reference data, lookup tables |
| **Join Requirement** | Co-partitioning required | Co-partitioning required | **No co-partitioning required** |
| **State Storage** | Stateless (unless aggregated) | Stateful (Local RocksDB + Changelog topic) | Stateful (Local RocksDB, no changelog backup needed) |
| **Storage Cost** | Minimal (unless windowed) | Moderate (fraction of total state) | High (entire state duplicated on every instance) |

## Windowing Types Summary

| Window Type | Characteristics | Key Parameters | Example Use Case |
| :--- | :--- | :--- | :--- |
| **Tumbling** | Fixed-size, gap-less, non-overlapping | Size | Count total events per hour |
| **Hopping** | Fixed-size, overlapping | Size, Advance (Hop) | Moving average over 1 hour, updated every 5 mins |
| **Sliding** | Fixed-size, continuous slide, tied to record timestamps | Maximum Time Difference | Join records that occurred within 10 minutes of each other |
| **Session** | Dynamic size, data-driven | Inactivity Gap | Group events into a user session that ends after 30 mins of inactivity |

## Common Configuration Properties

- `application.id`: Unique identifier for the streams application (used for consumer group and state store names).
- `bootstrap.servers`: List of broker addresses.
- `num.stream.threads`: Number of threads to execute stream processing (default 1).
- `state.dir`: Local directory for RocksDB state stores.
- `processing.guarantee`: `at_least_once` (default) or `exactly_once_v2`.
- `default.key.serde` / `default.value.serde`: Serializer/Deserializer classes.
- `commit.interval.ms`: Frequency to save state and commit offsets.
