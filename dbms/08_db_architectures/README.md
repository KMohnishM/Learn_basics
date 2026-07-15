# Module 8: Database Architectures & NoSQL

---

## 1. Centralized vs. Distributed Databases

- **Centralized Database**: Runs on a single physical machine.
  - *Pros*: Simple transaction management, no network latency between nodes, strong ACID compliance is easy.
  - *Cons*: Single point of failure, limited by hardware capacity (vertical scaling limits).
- **Distributed Database**: Runs across multiple physically separated machines connected via a network.
  - *Pros*: High availability, fault tolerance, horizontal scalability (add more cheap servers).
  - *Cons*: Complex transaction management (requires distributed consensus protocols like 2PC), network latency, consistency challenges.

---

## 2. Partitioning and Sharding

To handle datasets larger than a single server's disk, databases split tables.

### Database Partitioning (Single Instance)
Logical division of a table within the same database engine instance.
- **Range Partitioning**: Rows are mapped to partitions based on a range of values (e.g., partition by `Year` of transaction).
- **List Partitioning**: Rows mapped based on a discrete list of values (e.g., partition by `Country`).
- **Hash Partitioning**: A hash function is applied to a partition key to determine the partition. Distributes rows evenly.

### Sharding (Horizontal Partitioning Across Nodes)
Splitting a table horizontally and storing the partitions across **different physical database servers** (shards).
- **Shared-Nothing Architecture**: Each shard has its own independent CPU, RAM, and disk. No shared state.
- **Sharding Key**: The column used to route queries to specific shards. Choosing a poor sharding key leads to "hot spots" (one shard gets all traffic, others idle).

### Consistent Hashing (Scale In/Out)
Traditional hashing (`node = hash(key) % N`) causes massive data migration when the number of shards ($N$) changes. If $N$ changes from 4 to 5, nearly 80% of keys hash to different nodes and must move.

**Consistent Hashing** resolves this using a **Hash Ring**:

```
                 Node 0 (Hash: 1200)
                    ┌─────────┐
             *key2  │         │   *key1
              (800) │         │   (300)
                    │  RING   │
          Node 2 ───┤         ├─── Node 1 (Hash: 500)
         (Hash: 900)│         │
                    │         │
                    └─────────┘
```

1. **Ring Setup**: Hash both keys and physical node addresses to a 32-bit integer space (represented as a circle/ring).
2. **Key Mapping**: To find which node stores a key, hash the key and traverse the ring clockwise until you encounter the first node.
3. **Adding a Node**: If Node 1.5 is added between Node 1 and Node 2, only the keys that map between Node 1 and Node 1.5 need to move to the new node. Other nodes are unaffected.
4. **Virtual Nodes**: To prevent uneven key distribution (hot spots), map each physical node to multiple "virtual nodes" scattered across the ring.

---

## 3. Database Replication Topologies

Replication copies data across multiple nodes to ensure high availability.

### 1. Leader-Follower (Master-Slave)
- **Design**: All **Writes** go to a single designated Leader node. The leader records changes and broadcasts them to one or more Follower nodes. Clients can read from any follower (Read scalability).
- **Synchronous Replication**: Leader waits for all followers to write the change before acknowledging the client. Safe (no data loss on crash), but high write latency (slowest follower dictates speed).
- **Asynchronous Replication**: Leader writes locally, immediately responds to the client, and sends updates to followers in the background. Low write latency, but risk of data loss if the leader crashes before updates propagate.

### 2. Multi-Leader (Master-Master)
- **Design**: Writes can go to multiple leader nodes. They synchronize updates asynchronously.
- **Conflict Resolution**: Writes can conflict (e.g., concurrent updates to same field). Requires conflict resolution strategies (Last-Write-Wins, CRDTs, or client-side conflict resolution).

### 3. Leaderless (Decentralized / Quorum-Based)
- **Design**: Clients write to and read from multiple nodes in parallel. No single leader. (Popularized by Amazon's Dynamo, Apache Cassandra).
- **Quorum Invariant**: To ensure strong consistency without a leader, the read quorum ($R$) and write quorum ($W$) must overlap:
  $$R + W > N \quad (\text{where } N \text{ is the total replica count})$$
  If $N = 3$ and we configure $W = 2$ and $R = 2$, any read is guaranteed to fetch at least one copy containing the most recent write.

---

## 4. CAP and PACELC Theorems

### CAP Theorem (Brewer's Theorem)
A distributed data store can guarantee at most two of the following three properties simultaneously during a network partition:

1. **Consistency (Linearizability)**: Every read receives the most recent write or an error. (All nodes see identical data at the same time).
2. **Availability**: Every non-failing node returns a non-error response (without guarantee that it contains the most recent write).
3. **Partition Tolerance**: The system continues to operate despite arbitrary message loss or link failures in the network.

**The Real Choice: CP vs. AP**
Because networks will inevitably experience partitions ($P$), a distributed database must choose:
- **CP (Consistency / Partition Tolerance)**: Reject writes or block reads on partition components that cannot communicate with the majority. (Prefers correctness over uptime). E.g., MongoDB, HBase.
- **AP (Availability / Partition Tolerance)**: Allow writes and reads on all partitioned nodes. Nodes will return stale data and diverge, resolving conflicts later. (Prefers uptime over correctness). E.g., Cassandra, CouchDB.

### PACELC Theorem (Extension of CAP)
CAP only describes system behavior *during* a partition. **PACELC** adds behavior during normal operation:
```
If there is a Partition (P) -> Choose Availability (A) or Consistency (C)
Else (E)                  -> Choose Latency (L) or Consistency (C)
```

- **Cassandra (PA/EL)**: During partitions, choose Availability. During normal operation, choose low Latency (uses asynchronous replication).
- **MongoDB (PC/EC)**: During partitions, choose Consistency. During normal operation, choose Consistency (waits for replica acknowledgments, adding latency).

---

## 5. Storage Engine Internals: B+ Trees vs. LSM-Trees

Database engines use different on-disk data structures depending on workload profiles:

### B+ Trees (Read-Optimized)
Used by standard relational engines (MySQL InnoDB, Postgres).
- **Design**: In-place updates. Modifying a row requires reading its page, updating it in memory, and writing it back to its specific physical location on disk.
- **Pros**: Fast point lookups ($O(\log N)$). Low **read amplification** (only need to load path pages to leaf).
- **Cons**: High **write overhead** (random writes, page splits, write amplification from dirty page flushing).

### LSM-Trees (Log-Structured Merge-Trees - Write-Optimized)
Used by write-heavy NoSQL systems (Cassandra, RocksDB, LevelDB).
- **Design**: Append-only updates. Updates are never done in-place.
  1. **MemTable**: Writes are written to a sorted in-memory buffer (MemTable) and a sequential commit log on disk (for recovery).
  2. **SSTables**: When the MemTable is full, it is flushed to disk as an immutable **SSTable** (Sorted String Table).
  3. **Compaction**: A background process constantly merges sorted SSTables (using merge sort) to remove duplicate/deleted keys and limit file count.
- **Pros**: High-speed sequential writes (no random disk seeks). Highly write-optimized.
- **Cons**: High **read amplification** (a read must search multiple SSTables to find the latest key). High **write amplification** (records are read and rewritten multiple times by the background compaction process).

---

## 6. NoSQL Classifications

NoSQL (Not Only SQL) databases relax relational constraints to achieve horizontal scale.

| NoSQL Type | Data Model | Key Feature | Common Systems |
|------------|------------|-------------|----------------|
| **Key-Value** | Hash Table (Key $\rightarrow$ Blob) | Extreme speed, simple lookup | Redis, Riak, DynamoDB |
| **Document** | Nested objects (JSON/BSON) | Schema-flexible, query nested fields | MongoDB, CouchDB |
| **Wide-Column** | Row keys $\rightarrow$ Column families | Scalable columnar partitions, sparse data | Apache Cassandra, ScyllaDB, HBase |
| **Graph** | Nodes, Edges, Properties | Fast relationship/graph traversal | Neo4j, JanusGraph |
