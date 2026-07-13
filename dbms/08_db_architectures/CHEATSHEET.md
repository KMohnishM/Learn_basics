# Cheat Sheet — Database Architectures & NoSQL

## Partitioning vs. Sharding
- **Partitioning**: Logical separation of table rows within the **same** database server instance.
- **Sharding**: Physical separation of table rows across **different** database servers (shared-nothing).

---

## Consistent Hashing (Hash Ring)
- Keys and Server Nodes are hashed to a circular integer space (ring).
- **Lookup**: Hash key $\rightarrow$ traverse clockwise $\rightarrow$ store on first node found.
- **Scaling**: Adding/removing a node only triggers data migration of $\approx 1/N$ keys (adjacent items).
- **Virtual Nodes**: Map one physical node to multiple points on the ring to prevent hot spots.

---

## CAP Theorem (Partitions)

In a network partition ($P$), choose either:
- **CP (Consistency)**: Reject writes / block reads in minority partitions to guarantee linearizability. (e.g., MongoDB, HBase).
- **AP (Availability)**: Allow reads/writes on all partitioned nodes, return stale data, resolve conflicts later. (e.g., Cassandra, CouchDB).

---

## PACELC Theorem (CAP Extension)

```
If Partition (P) -> Choose Availability (A) or Consistency (C)
Else (E)         -> Choose Latency (L) or Consistency (C)
```

| Database | PACELC Classification | Priority |
|----------|:---------------------:|----------|
| **Cassandra** | **PA / EL** | Availability (Partition), Latency (Normal) |
| **MongoDB** | **PC / EC** | Consistency (Partition), Consistency (Normal) |
| **HBase** | **PC / EC** | Consistency (Partition), Consistency (Normal) |
| **DynamoDB** | **PA / EL** | Configurable (defaults to Availability/Latency) |

---

## Quorum Invariant (Leaderless Replication)

Let $N$ = replica count, $W$ = write quorum (acknowledgments), $R$ = read quorum.

- **Strong Consistency**:
  $$R + W > N$$
  *(Guarantees at least one read replica contains the latest written version).*
- **Eventual Consistency**:
  $$R + W \le N$$
  *(Risk of stale reads).*

---

## B+ Trees vs. LSM-Trees (Storage Engines)

| Feature | B+ Trees | LSM-Trees |
|---------|----------|-----------|
| **Write Type** | In-place random writes | Append-only sequential writes |
| **Optimized For** | Point reads (read-heavy) | High-speed ingestion (write-heavy) |
| **Read Amplification**| Low | High (must search MemTable + multiple SSTables) |
| **Write Amplification**| Medium-High (dirty page flushes) | High (background compactions) |
| **Used In** | MySQL InnoDB, PostgreSQL | Cassandra, RocksDB, LevelDB |

---

## NoSQL Classifications

- **Key-Value**: Key $\rightarrow$ Blob map (e.g., Redis). Cache, sessions.
- **Document**: JSON storage (e.g., MongoDB). Flexible schemas.
- **Wide-Column**: Key $\rightarrow$ Column family (e.g., Cassandra). Large timeseries/analytics.
- **Graph**: Nodes + Edges (e.g., Neo4j). Relationships, fraud detection.
