# Module 3: Databases and Data Systems

> **Goal**: Deeply understand database internals, indexing structures, replication topologies, and partitioning strategies. 
> Databases are the heart of any stateful system; knowing how they work under the hood is non-negotiable for system design.

---

## Table of Contents

1. [SQL vs NoSQL — The Real Differences](#1-sql-vs-nosql-the-real-differences)
2. [Database Indexing Deep Dive](#2-database-indexing-deep-dive)
3. [Replication](#3-replication)
4. [Sharding and Partitioning](#4-sharding-and-partitioning)
5. [Connection Pooling](#5-connection-pooling)
6. [Schema Evolution & Migrations](#6-schema-evolution--migrations)
7. [PACELC Theorem](#7-pacelc-theorem)

---

## 1. SQL vs NoSQL — The Real Differences

The "SQL vs NoSQL" debate is often oversimplified to "relational vs non-relational" or "schema vs schemaless". The real differences lie in their storage engines, consistency models, and intended access patterns.

### 1.1 Row-store vs Columnar Storage Internals

At the lowest level, databases map logical tables to physical bytes on disk. The orientation of this mapping changes performance drastically.

**Row-Oriented Storage (PostgreSQL, MySQL)**
Data is stored sequentially row-by-row. When you read a row, you fetch all its columns together because they sit contiguously on disk.
* **Use Case**: **OLTP (Online Transaction Processing)**. High-throughput, low-latency writes and point reads of entire records.

```
Logical Table:
ID | Name  | Age | City
---+-------+-----+-------
1  | Alice | 30  | NYC
2  | Bob   | 25  | SFO

Row-Store Disk Layout:
[1, Alice, 30, NYC] [2, Bob, 25, SFO] ...
```

**Column-Oriented Storage (Redshift, Cassandra, ClickHouse)**
Data is stored sequentially column-by-column. 
* **Use Case**: **OLAP (Online Analytical Processing)**. Aggregations (SUM, AVG) over massive datasets where you only care about a few columns.
* **Benefit**: Massive compression. Storing identical data types contiguously allows run-length encoding (e.g., storing 1000 "NYC" strings as `1000xNYC`).

```
Column-Store Disk Layout:
[1, 2] [Alice, Bob] [30, 25] [NYC, SFO] ...
```

### 1.2 ACID Properties and Failure Scenarios

**ACID** ensures reliable transaction processing. To understand it, consider a bank transfer of $100 from Account A to Account B.

1. **Atomicity (All or Nothing)**
   * **Failure Scenario**: The system crashes after subtracting $100 from A, but before adding to B. 
   * **Why it matters**: Without Atomicity, the $100 is lost forever. Atomicity guarantees that if the transaction aborts mid-flight, all partial changes are rolled back.

2. **Consistency (Data Validity)**
   * **Failure Scenario**: A rule states account balances cannot be negative. Account A has $50. A transfer of $100 executes.
   * **Why it matters**: Consistency ensures the transaction transitions the database from one valid state to another valid state, rejecting the transaction if constraints (like `CHECK balance >= 0`) are violated.

3. **Isolation (Concurrency Control)**
   * **Failure Scenario**: Transaction 1 reads A's balance ($100). Transaction 2 also reads A's balance ($100). Both add $50 and save ($150). The final balance is $150 instead of $200.
   * **Why it matters**: Isolation ensures concurrent transactions execute as if they were running serially, preventing data corruption from race conditions.

4. **Durability (Persistence)**
   * **Failure Scenario**: The transaction commits successfully, returning "OK" to the user. A millisecond later, the server loses power.
   * **Why it matters**: Durability guarantees that once a commit is acknowledged, the data survives even permanent hardware failure, usually by flushing a **Write-Ahead Log (WAL)** to disk before acknowledging the commit.

### 1.3 Isolation Levels and Anomalies

The ANSI SQL standard defines four isolation levels based on which concurrency anomalies they prevent.

| Isolation Level | Dirty Read | Non-Repeatable Read | Phantom Read |
| :--- | :--- | :--- | :--- |
| **Read Uncommitted** | Allowed | Allowed | Allowed |
| **Read Committed** | Prevented | Allowed | Allowed |
| **Repeatable Read** | Prevented | Prevented | Allowed* |
| **Serializable** | Prevented | Prevented | Prevented |

* **Dirty Read**: Reading uncommitted changes from another transaction.
* **Non-Repeatable Read**: Reading the same row twice in a transaction and getting different data because another transaction updated it.
* **Phantom Read**: Running a range query twice and seeing new "phantom" rows inserted by another transaction.

> **IMPORTANT ACCURACY NOTE**: The ANSI standard says Repeatable Read *allows* phantom reads. However, **PostgreSQL's implementation of Repeatable Read actually PREVENTS phantom reads**! It does this using **MVCC (Multi-Version Concurrency Control)**, which gives the transaction a consistent snapshot of the database at the start of the transaction.

### 1.4 BASE Properties for NoSQL

While traditional relational databases prioritize ACID, distributed NoSQL databases originally prioritized **BASE**:
* **B**asically **A**vailable: The system guarantees availability for reads/writes even during partial failures.
* **S**oft State: The state of the system can change over time without input, due to replication convergence.
* **E**ventual Consistency: Given enough time without new inputs, all nodes will converge to the same data.

### 1.5 When to Use SQL vs NoSQL

| Factor | Use SQL (RDBMS) | Use NoSQL |
| :--- | :--- | :--- |
| **Schema** | Rigid, well-defined upfront | Evolving, dynamic, or highly nested |
| **Relationships** | Complex, requiring JOINs | Minimal, or modeled via denormalization |
| **Scaling** | Vertical scaling, read replicas | Horizontal scaling (sharding) out of the box |
| **Transactions** | Complex multi-row ACID required | Single-document ACID is sufficient |
| **Data Size** | Gigabytes to Terabytes | Petabytes and beyond |

### 1.6 NoSQL Types and Internal Storage Models

1. **Document (MongoDB, Couchbase)**
   * **Model**: JSON-like objects. Great for nested data (e.g., a user profile with an array of addresses).
   * **Internal**: BSON (Binary JSON) trees allowing fast traversal and indexing of inner fields.
2. **Key-Value (Redis, Memcached, DynamoDB)**
   * **Model**: O(1) dictionary lookups. Keys map to opaque blobs.
   * **Internal**: Hash tables in memory (Redis) or LSM-Trees on disk (DynamoDB).
3. **Wide-Column (Cassandra, HBase)**
   * **Model**: Nested maps `RowKey -> ColumnFamily -> ColumnKey -> Value`.
   * **Internal**: Highly partitioned LSM-Trees optimized for heavy write throughput.
4. **Graph (Neo4j)**
   * **Model**: Nodes, edges, and properties.
   * **Internal**: "Index-free adjacency" where nodes contain direct pointers to connected nodes, making deep traversals O(1) per hop.

---

## 2. Database Indexing Deep Dive

Indexes speed up read queries at the cost of write performance and storage space. Understanding the underlying data structures is critical.

### 2.1 B-Tree Index Internals

The **B-Tree (Balanced Tree)**, specifically the **B+Tree**, is the default index structure for nearly all relational databases.

* **Node Structure**: Nodes contain keys (values being indexed) and pointers. In a B+Tree, all actual data pointers/rows are stored *only* in the leaf nodes. Internal nodes just act as traffic cops directing the search.
* **Page Alignment**: B-Tree nodes are strictly sized to align with OS page sizes, typically **4KB to 16KB**. This minimizes disk I/O; reading one node is exactly one disk block fetch.
* **Why Height Stays Low**: Because the node size is large, the **branching factor** (number of children per node) is huge (often 100-500). 
* **Real-World Math**: A B-Tree with branching factor $b=100$.
  * Level 1 (Root): 1 node, 100 records
  * Level 2: 100 nodes, 10,000 records
  * Level 3: 10,000 nodes, 1,000,000 records
  * Level 4: 1,000,000 nodes, 100,000,000 records
  * Thus, finding a row among **100 million rows** requires a maximum height of 4. Only 4 disk reads! $O(\log n)$ is effectively constant.

```
B+Tree ASCII Diagram:

                     [ 45 | 80 ]                      <-- Root Node (in RAM)
                   /      |      \
                 /        |        \
    [ 10 | 25 ]      [ 50 | 65 ]      [ 85 | 92 ]     <-- Internal Nodes
     /   |   \        /   |   \        /   |   \
   [10] [25] [40]   [50] [65] [75]   [85] [92] [99]   <-- Leaf Nodes (on Disk)
   |->  |->  |->    |->  |->  |->    |->  |->  |->
  Row1 Row2 Row3   Row4 Row5 Row6   Row7 Row8 Row9    <-- Actual Data (Heap)
```

### 2.2 LSM-Tree Internals (Log-Structured Merge Tree)

While B-Trees overwrite data in-place (slow for writes), **LSM-Trees** optimize for extremely high write throughput by appending data sequentially. Used by Cassandra, RocksDB, and DynamoDB.

**The Pipeline**:
1. **MemTable**: Incoming writes are inserted into an in-memory balanced tree (like a Red-Black tree). Writes are extremely fast.
2. **Immutable MemTable**: Once the MemTable reaches a size limit (e.g., 32MB), it is frozen. A new MemTable is created for new writes.
3. **SSTable Flush**: The Immutable MemTable is flushed to disk as a **Sorted String Table (SSTable)**. It is written sequentially (fast disk I/O) and is immutable.
4. **Compaction**: Over time, many SSTables accumulate on disk. Reading requires checking multiple SSTables. A background compaction process merges overlapping SSTables, removes deleted keys (tombstones), and writes new, larger SSTables in **Level-tiered** or **Size-tiered** structures.

```
LSM-Tree Pipeline ASCII Diagram:

[Write] ---> [MemTable (RAM)] ---> (flushes) ---> [SSTable 1 (Disk)]
                                                   [SSTable 2 (Disk)]
                                                   [SSTable 3 (Disk)]
                                                           |
                                                      (Compaction)
                                                           |
                                                           v
                                                [Merged SSTable (Disk)]
```

### 2.3 B-Tree vs LSM-Tree Comparison

| Feature | B-Tree (PostgreSQL) | LSM-Tree (Cassandra) |
| :--- | :--- | :--- |
| **Write Amplification** | High (must update index pages) | Low (sequential appends) |
| **Read Amplification** | Low (direct pointer traversal) | High (must check MemTables and multiple SSTables) |
| **Space Amplification** | Medium (fragmentation in pages) | High (multiple versions of same key exist until compaction) |
| **Best Use Case** | Read-heavy, OLTP, transactions | Write-heavy, event logging, time-series |

### 2.4 Advanced Indexing Concepts

**Composite Indexes and the Leftmost Prefix Rule**
A composite index indexes multiple columns. The order matters critically.
```sql
CREATE INDEX idx_user ON users(last_name, first_name, age);
```
* Queries on `(last_name)` -> Uses Index
* Queries on `(last_name, first_name)` -> Uses Index
* Queries on `(first_name)` -> **Does NOT use Index** (requires full table scan)
* Think of it like a telephone book sorted by Last Name, then First Name. You can't efficiently find all "Johns" without knowing the Last Name.

**Covering Indexes**
If an index contains all the columns required by the `SELECT` clause, the database does not need to visit the actual table row (the heap). This saves a disk hop.
```sql
-- If we only select last_name and age, the index 'idx_user' acts as a covering index.
SELECT last_name, age FROM users WHERE last_name = 'Smith';
```

**Index Selectivity**
An index is useless if the column has low cardinality (e.g., a boolean `is_active` column where 99% of users are true). The database query planner will calculate that doing a full table scan is cheaper than reading the index and then fetching 99% of the rows.

**Other Index Types**:
* **Hash Indexes**: Only support equality (`=`), no range queries (`<, >`). Fast O(1) lookups.
* **GIN (Generalized Inverted Index)**: Used in PostgreSQL for arrays and JSONB full-text search.
* **GiST**: Used for spatial/geographic data (PostGIS).

### 2.5 EXPLAIN / EXPLAIN ANALYZE

Always profile your queries.
```sql
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';

-- Bad output (Sequential Scan):
Seq Scan on users  (cost=0.00..15243.00 rows=1 width=128) (actual time=0.012..45.120 rows=1 loops=1)
  Filter: ((email)::text = 'test@example.com'::text)
  Rows Removed by Filter: 1000000

-- Good output (Index Scan):
Index Scan using idx_users_email on users  (cost=0.42..8.44 rows=1 width=128) (actual time=0.015..0.016 rows=1 loops=1)
  Index Cond: ((email)::text = 'test@example.com'::text)
```

---

## 3. Replication

Replication means keeping a copy of the same data on multiple machines connected via a network to ensure high availability and read scalability.

### 3.1 Leader-Follower (Master-Slave)

All writes go to the Leader. The Leader streams changes to Followers. Reads can go to any node.
* **Synchronous Replication**: Leader waits for Followers to acknowledge the write before responding to the client. Extremely safe, but slow. If a Follower dies, writes halt.
* **Asynchronous Replication**: Leader writes locally, responds to client, then sends data to Followers. Fast, but if Leader dies before replication, data is permanently lost.
* **Replication Lag**: The time delay for async Followers to catch up. Causes **stale reads**.

### 3.2 Multi-Leader (Active-Active)

Multiple nodes accept writes simultaneously and sync with each other. Great for multi-datacenter setups.
* **Conflict Resolution is Hard**: What if Node A sets $x=1$ and Node B sets $x=2$ simultaneously?
* **Strategies**: Last-Write-Wins (LWW) based on timestamps, merge operations (CRDTs), or pushing conflict resolution to the application logic.

### 3.3 Leaderless (Dynamo-style)

Any node can accept writes. To ensure consistency without a leader, we use **Quorum**.
The invariant equation for strong consistency is: **$R + W > N$**
* $N$ = Replication factor (total copies)
* $W$ = Write quorum (number of nodes that must ACK a write)
* $R$ = Read quorum (number of nodes that must respond to a read)

**Quorum Math Example**: 
If $N=3$. We can set $W=2$ and $R=2$. $2 + 2 > 3$.
Because $R+W>N$, the set of nodes we write to and the set of nodes we read from will *always* overlap by at least one node. The reader looks at the timestamps and picks the most recent version, ensuring strong consistency.

**Repair Mechanisms**:
* **Read Repair**: If a reader notices a node returned stale data, it pushes the updated data to that node in the background.
* **Hinted Handoff**: If Node C is down during a write, Node A temporarily stores a "hint" for C. When C comes back online, A forwards the missed writes.

> **IMPORTANT ACCURACY NOTE**: Because of Dynamo-style origins, people incorrectly assume AWS DynamoDB is inherently AP (Available/Partition-tolerant) and eventually consistent. **This is false.** In 2024, DynamoDB supports Strongly Consistent Reads and fully ACID multi-table transactions.

### 3.4 Raft Consensus Algorithm

How do systems agree on a Leader without human intervention? Systems like etcd and ZooKeeper use consensus algorithms like **Raft**.
* **Leader Election**: Nodes start as followers. If they don't hear a heartbeat, they become candidates, vote for themselves, and request votes. Majority wins.
* **Log Replication**: Leader receives a command, appends to its log, sends `AppendEntries` to followers. Once a majority write to their logs, the leader commits and applies to its state machine.

### 3.5 Addressing Replication Lag

1. **Read-Your-Writes Guarantee**: If a user updates their profile and refreshes the page, they expect to see the update. Solution: Route a user's reads to the Leader for a few seconds after they perform a write.
2. **Monotonic Reads Guarantee**: A user shouldn't read from a fast replica, see new data, then refresh, hit a slow replica, and see the data go "back in time." Solution: Hash the UserID so the same user always reads from the same replica.

---

## 4. Sharding and Partitioning

When data exceeds the capacity of a single machine (Vertical Scaling limit), you must horizontally partition the data across multiple machines.

### 4.1 Range-Based Sharding

Data is partitioned by a continuous range of the shard key.
* **Example**: Users A-H on Shard 1, I-P on Shard 2.
* **Pro**: Excellent for range queries.
* **Con (The Hot Spot Problem)**: If you shard by Timestamp, today's shard will receive 100% of the write traffic, melting the server while historical shards sit idle.

### 4.2 Hash-Based Sharding

The shard key is hashed to distribute data evenly.

**The Modulo Problem**:
Naive hashing uses `hash(key) % N` where N is the number of servers.
* If you have 4 servers, key `100` goes to server `100 % 4 = 0`.
* **The Resharding Problem**: You grow to 5 servers. Now `100 % 5 = 0` (still 0), but `101 % 4 = 1`, and `101 % 5 = 1`... wait. Most keys will change their mapping! Adding a server requires migrating almost the entire database.

**The Solution: Consistent Hashing**:
Instead of modulo, map servers and keys onto a circular hash ring (e.g., 0 to $2^{32}-1$). A key belongs to the first server found by moving clockwise on the ring.
* When adding a new server, it only takes over a slice of the ring from its immediate clockwise neighbor.
* **Result**: Only $1/N$ keys need to move.

```
Consistent Hashing Ring ASCII:

           [Server 0]
          /          \
         /            \
        /              \
[Server 3]            [Server 1]
        \              /
         \            /
          \          /
           [Server 2]

If we add Server 4 between Server 0 and Server 1, ONLY keys between 0 and 4 move.
```

### 4.3 Virtual Nodes / Virtual Buckets

Real-world servers have different capacities, and basic consistent hashing can lead to unequal distribution.
* **Solution**: Create **Virtual Nodes (vnodes)**. A single physical server might represent 256 virtual nodes scattered randomly around the hash ring.
* Redis Cluster uses 16,384 fixed "hash slots". Cassandra uses vnodes.

### 4.4 Sharding Challenges

* **Cross-Shard Queries**: If a query lacks the shard key, it must be sent to *all* shards (Scatter-Gather). This is extremely slow.
* **Denormalization**: To avoid cross-shard joins, data is often duplicated. E.g., embed user details directly inside their comments.
* **Resharding / Cutover**: Moving data live requires Dual-Writes (writing to old and new shards simultaneously) or Log Tailing, followed by validation, before flipping the read switch.

---

## 5. Connection Pooling

A database connection is highly expensive to establish. 

### 5.1 Why Connections are Expensive
Every new connection requires:
1. TCP 3-way handshake
2. TLS handshake (encryption)
3. Authentication and permission checking
4. The DB spawning a dedicated OS thread/process and allocating memory (PostgreSQL allocates ~10MB per connection).

If an app server handles 1,000 req/sec and opens/closes a DB connection for each, the database will spend more CPU establishing connections than running queries, leading to immediate collapse.

### 5.2 The Solution: Connection Pools

An intermediary keeps a pool of pre-established, long-lived connections open to the database. When the app needs to query, it borrows a connection, uses it, and returns it.

* **Application-Level Pools**: **HikariCP** (Java), SQLAlchemy Pool (Python).
* **External Poolers**: **PgBouncer** (PostgreSQL).
  * **Session Pooling**: Connection tied to client for lifespan of client.
  * **Transaction Pooling**: Connection returned to pool after `COMMIT`. (Most common/efficient).
  * **Statement Pooling**: Connection returned immediately after a single statement.

### 5.3 Connection Pool Sizing Formula

A common mistake is making the pool size huge (e.g., 500 connections). This causes massive context switching thrashing on the DB CPU. The optimal pool size is surprisingly small.

**PostgreSQL Recommended Formula**:
`pool_size = (core_count * 2) + effective_spindle_count`

For an 8-core DB with SSDs (effective spindle ~1): `(8 * 2) + 1 = 17 connections`.

**Python Code Example (psycopg2)**:
```python
from psycopg2 import pool

# Create a connection pool with minimum 1, max 20 connections
db_pool = psycopg2.pool.SimpleConnectionPool(
    1, 20,
    user="postgres",
    password="password",
    host="127.0.0.1",
    port="5432",
    database="production_db"
)

def get_user(user_id):
    # Borrow a connection from the pool
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            return cursor.fetchone()
    finally:
        # ALWAYS return the connection, even if an exception occurs
        db_pool.putconn(conn)
```

---

## 6. Schema Evolution & Migrations

In production, you cannot bring the system down to alter a table. Schema changes must be zero-downtime and backwards compatible.

### 6.1 Backwards Compatible vs Breaking Changes

* **Compatible**: Adding a nullable column, adding an index.
* **Breaking**: Renaming a column, dropping a column, changing a data type.

### 6.2 Expand-Contract Pattern

To perform a breaking change (like renaming `first_name` to `given_name`) without downtime, use the Expand-Contract pattern over multiple deployments:

1. **Expand (DB)**: Add the new column `given_name`.
2. **Dual-Write (App)**: Deploy app code that writes to BOTH `first_name` and `given_name`, but still reads from `first_name`.
3. **Backfill (Script)**: Run a background script to copy historical data from `first_name` to `given_name`.
4. **Transition (App)**: Deploy app code that reads from `given_name`.
5. **Contract (DB)**: Drop the old `first_name` column.

### 6.3 Tooling

Always version control your database schema using tools like **Flyway** or **Liquibase**. Migrations should be automated in CI/CD, not run manually by DBAs.

```sql
-- V1.2__Add_email_index.sql
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
-- Note: CONCURRENTLY is required in Postgres to build the index 
-- without locking the table for writes!
```

---

## 7. PACELC Theorem

The CAP Theorem (Consistency, Availability, Partition Tolerance) states that during a network Partition (P), a distributed system must choose between Availability (A) and Consistency (C). 

However, network partitions are rare. What happens during normal operation? **PACELC** extends CAP to answer this.

**PACELC**: 
* If **P** (Partition), choose between **A** (Availability) and **C** (Consistency).
* **E**lse (Normal operation), choose between **L** (Latency) and **C** (Consistency).

**Examples:**
* **Cassandra**: PA/EL system. During a partition, it is available (PA). During normal operation, it sacrifices consistency for low latency (EL).
* **MongoDB**: PA/EC system (historically). 
* **DynamoDB**: Can be configured. Typically PA/EL, but with Strongly Consistent reads enabled, it shifts towards PC/EC.
* **Relational DBs (Sync Replication)**: PC/EC. They prioritize consistency at all times, paying the price in higher latency during normal operations and unavailability during partitions.
