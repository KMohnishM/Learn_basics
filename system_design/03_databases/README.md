# Module 3: Databases Deep Dive

When interviewing for or designing large-scale systems, 80% of the complexity lies in the database layer. 
Stateless backend servers are easy to scale (just add more of them). Databases have *state*, which makes scaling them incredibly difficult.

## 1. SQL vs NoSQL (The Real Differences)

The classic comparison is "SQL is for structured data, NoSQL is for unstructured data." This is a massive oversimplification.

### Relational (SQL) Databases
- **Examples**: PostgreSQL, MySQL, Oracle
- **Structure**: Tables with rigid schemas.
- **Relationships**: Foreign keys enforce referential integrity.
- **Scaling**: Historically vertical (buy a bigger server). Modern solutions allow some horizontal scaling, but it's complex.
- **When to use**: Financial systems, ERPs, systems where ACID compliance and data integrity are non-negotiable.

### NoSQL Databases
NoSQL actually refers to 4 distinct families of databases:

1. **Document Stores** (MongoDB, Couchbase)
   - Store data as JSON-like documents.
   - Great for rapidly changing schemas and storing hierarchical data.
2. **Key-Value Stores** (Redis, DynamoDB)
   - Extremely fast. Access data only by its primary key.
   - Great for caching, user sessions, shopping carts.
3. **Wide-Column Stores** (Cassandra, HBase)
   - Optimized for massive write-heavy workloads (time-series, IoT, logging).
4. **Graph Databases** (Neo4j)
   - Optimized for highly connected data (social networks, recommendation engines).

## 2. ACID Properties

Relational databases guarantee ACID properties for transactions:
- **Atomicity**: "All or nothing." If a transaction fails halfway through, the whole thing is rolled back. (e.g., deducting money from Account A and adding to Account B must both succeed, or neither).
- **Consistency**: A transaction takes the database from one valid state to another valid state (enforcing constraints like "balance >= 0").
- **Isolation**: Concurrent transactions don't interfere with each other. (e.g., Two people booking the last seat on a flight at the same time).
- **Durability**: Once a transaction is committed, it remains committed even if the database crashes immediately after (written to disk/Write-Ahead Log).

### Isolation Levels (from weakest to strongest)
1. **Read Uncommitted**: Dirty reads allowed (reading data from another transaction that hasn't committed yet). Fast, but dangerous.
2. **Read Committed**: No dirty reads. But if you read the same row twice in one transaction, it might change if someone else committed an update. (Default in Postgres).
3. **Repeatable Read**: If you read a row twice, it stays the same. But new rows might appear ("Phantom reads").
4. **Serializable**: The database executes concurrent transactions as if they were executed sequentially. Slowest, but safest.

## 3. Database Indexing

An index is a separate data structure (usually a B-Tree) that speeds up data retrieval. 
Without an index, the database must perform a **Full Table Scan** (checking every single row).

- **How B-Trees work**: They keep data sorted and allow searches, sequential access, insertions, and deletions in logarithmic time O(log N).
- **The Trade-off**: Indexes make reads faster, but writes SLOWER (because every INSERT/UPDATE/DELETE requires updating the B-Tree).
- **Composite Indexes**: Indexes on multiple columns (e.g., `INDEX(last_name, first_name)`). *Rule of thumb: The order matters.* An index on (A, B) can speed up queries filtering on A, or A and B, but NOT queries filtering just on B.

## 4. Scaling Databases

### Replication (High Availability & Read Scaling)
Copying data across multiple servers.
- **Leader-Follower (Master-Slave)**: All writes go to the Leader. The leader streams changes to Followers. Reads can go to any Follower. (Increases read capacity, but write capacity is still limited to one machine).
- **Replication Lag**: Because replication takes time, a user might write to the Leader, then immediately read from a Follower and see stale data.

### Sharding (Write Scaling)
Splitting a single logical database into multiple physical databases (shards).
- **Hash-based Sharding**: `hash(user_id) % 4` determines which of the 4 shards the data goes to. Evenly distributes data, but adding a 5th shard requires moving almost all data (resharding).
- **Range-based Sharding**: e.g., Users A-H on Shard 1, I-P on Shard 2. Easy to implement, but can lead to "hot spots" (e.g., everyone is writing to the '2023' partition simultaneously).

---
## Next Steps
Head to `labs/` to simulate sharding and see the actual impact of B-Tree indexing in Postgres!
