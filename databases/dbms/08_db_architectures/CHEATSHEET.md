# Database Architectures Cheatsheet

## OLTP vs OLAP

| Feature | OLTP (Online Transaction Processing) | OLAP (Online Analytical Processing) |
| :--- | :--- | :--- |
| **Primary Goal** | Fast, reliable transactional execution | Complex analytical queries, Business Intelligence |
| **Workload** | High volume of short, simple atomic transactions | Low volume of long, complex read-heavy queries |
| **Data Layout** | Row-oriented storage | Column-oriented storage |
| **Schema Design** | Highly Normalized (3NF) | Denormalized (Star, Snowflake) |
| **Operations** | CRUD (Insert, Update, Delete, Point Lookup) | Complex Selects, Joins, Aggregations (SUM, AVG) |
| **History** | Current state of operational data | Historical data spanning months/years |
| **Examples** | PostgreSQL, MySQL, Oracle DB | Snowflake, Redshift, ClickHouse, BigQuery |

## Storage Formats

| Format | Layout Structure | Best For | Pros | Cons |
| :--- | :--- | :--- | :--- | :--- |
| **Row-Oriented** | Contiguous by row on disk | OLTP, point lookups, single-record updates | Fast full-record reads and appends | Inefficient for large aggregations (high I/O waste) |
| **Column-Oriented**| Contiguous by column on disk| OLAP, aggregations, scanning specific fields| Extreme compression (RLE), minimal I/O for analytics| Very slow for single-record inserts/updates/deletes |

## Sharding Strategies (Horizontal Partitioning)

| Strategy | Mechanism | Pros | Cons |
| :--- | :--- | :--- | :--- |
| **Hash Sharding** | `hash(key) % N` | Perfectly uniform data/write distribution | Range queries are inefficient; hard to reshard (unless using consistent hashing) |
| **Range Sharding** | Grouping by value intervals (e.g., Dates A-C) | Extremely fast and efficient range queries | High risk of hot spots (e.g., all writes hit "today's" shard) |
| **Directory Sharding**| Lookup table mapping key to shard | Maximum flexibility, easy manual migrations | Lookup table becomes single point of failure and bottleneck |

## Consistency, Availability, Partition Tolerance (CAP Theorem)

**Core Rule:** A distributed database can guarantee at most TWO out of three properties in the presence of a network partition (P). Since P is guaranteed in distributed networks, systems must choose between AP and CP.

| Type | Definition | Behavior during Partition | Examples |
| :--- | :--- | :--- | :--- |
| **CP** | Consistency + Partition Tolerance | System rejects writes/reads to avoid stale data | MongoDB, Zookeeper, etcd, HBase |
| **AP** | Availability + Partition Tolerance | System returns data (potentially stale) to remain online | Cassandra, DynamoDB, Riak, CouchDB |
| **CA** | Consistency + Availability | Practically impossible on a distributed network | Single-node PostgreSQL/MySQL (not distributed) |

### PACELC Theorem
If **P** (Partition), choose **A** or **C**. **E**lse (Normal operation), choose **L** (Latency) or **C** (Consistency).
- Cassandra = **PA/EL**
- Spanner = **PC/EC**

## Replication Patterns

1. **Single-Leader**: One node accepts writes, followers replicate. (Risk: Write bottleneck).
2. **Multi-Leader**: Multiple nodes accept writes. (Risk: Complex conflict resolution).
3. **Leaderless**: Any node accepts reads/writes. Uses **Quorum**:
   - `W + R > N` (Strict Consistency)
   - `W + R <= N` (Eventual Consistency)
   *(N = Total Replicas, W = Write Nodes, R = Read Nodes)*

## Consistency Models (Strongest to Weakest)

1. **Strict / Linearizable**: Acts like a single global copy. Atomic operations.
2. **Sequential**: All nodes see operations in the same exact order.
3. **Causal**: Causally related operations are seen in order; concurrent ops can be reordered.
4. **Eventual**: If updates stop, all nodes will eventually hold the same data.

## Schema Modeling for Data Warehouses

| Type | Structure | Pros | Cons |
| :--- | :--- | :--- | :--- |
| **Star Schema** | Central Fact table linked directly to denormalized Dimension tables | Fast queries, very few joins, simple to query | High disk space usage, massive data redundancy |
| **Snowflake** | Central Fact table linked to normalized hierarchy of Dimension tables | Low redundancy, preserves hierarchical integrity | Slower queries, complex SQL requiring deep joins |
