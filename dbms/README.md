# Database Management Systems (DBMS) & SQL — Complete Interview Curriculum

A comprehensive, production-grade guide to understanding Database Management Systems (DBMS) internals, database design theory, and MySQL query optimization. 

Built for software engineers preparing for backend, data engineering, and distributed systems interviews.

---

## Curriculum Structure

Each module contains three files:
```
dbms/
└── [Module]/
    ├── README.md       ← Full textbook-depth internals & core principles
    ├── QnA.md          ← Tiered interview Q&A (Easy / Medium / Hard with numericals)
    └── CHEATSHEET.md   ← One-page quick reference (formulas, syntax, diagrams)
```

---

## Curriculum Map

| Module | Core Internals | Practical Topics | Numerical / Design Focus |
|--------|----------------|------------------|--------------------------|
| **[M1: Relational Model & Normalization](./01_relational_normalization/)** | Functional Dependencies, Armstrong's Axioms, Attribute Closure, Lossless Joins | ER Diagrams, Schema mapping, Anomalies, 1NF/2NF/3NF/BCNF/4NF | Finding Candidate Keys, Normal Form detection, Chase algorithm |
| **[M2: File Structures & Indexing](./02_file_indexing/)** | Slotted-page layout, Heap vs Sequential, Primary/Secondary indexes, Clustered/Unclustered, Dense/Sparse | B+ Trees node insertion/deletion splits, MySQL execution scans | B+ Tree order page capacity limits, height calculations |
| **[M3: Transactions & ACID Semantics](./03_transactions_acid/)** | Transaction states, ACID guarantees, Concurrency anomalies, Recoverability | Schedule types, Conflict vs View Serializability | Precedence Graph cycle checks, schedule recovery classification |
| **[M4: Concurrency Control](./04_concurrency_control/)** | Shared/Exclusive locks, 2PL (Strict/Rigorous/Static), Timestamp ordering, Thomas' Write Rule, MVCC | Deadlocks (Wait-For Graph), prevention (Wait-Die vs Wound-Wait), MySQL InnoDB Read Views | Wound-Wait vs Wait-Die traces, MVCC read-view snapshot trace |
| **[M5: Recovery Systems](./05_recovery_systems/)** | Failure classes, Write-Ahead Logging (WAL) protocol, Steal/No-Force buffer pools, Shadow paging | Recovery schemes (Deferred vs Immediate modifications), ARIES algorithm | Reconstructing Transaction & Dirty Page tables, crash log traces |
| **[M6: Query Processing & Optimization](./06_query_optimization/)** | Relational Algebra, evaluation costs, Join algorithms (Block nested, Index nested, Sort-merge, Hash) | Query trees, optimization equivalence rules, Selection/Projection pushdown | Disk I/O cost comparisons, External Merge Sort block cost calculations |
| **[M7: SQL Query Mastering (MySQL)](./07_sql_mastery/)** | Logical execution order, Referential integrity actions (Cascade/Set Null) | Advanced Joins, self joins, subqueries, CTEs, Window functions | Writing recursive hierarchies, consecutive login streaks, Nth salary |
| **[M8: Database Architectures & NoSQL](./08_db_architectures/)** | Distributed databases, partitioning (Range/List/Hash), replication topologies, CAP & PACELC theorems | Consistent Hashing ring, NoSQL database engines (B+ Trees vs LSM-Trees) | Read/Write Quorum equations, sharding key selection design case |

---

## Suggested Study Order

### Week 1: Database Internals & Query Theory
- **Day 1**: M1 — Relational Model & Normalization Theory (Build core schema design foundations)
- **Day 2**: M2 — File Structures & Indexing (Learn physical layouts and B+ Tree structures)
- **Day 3**: M3 — Transactions & ACID Semantics (Understand anomalies and serializability)
- **Day 4**: M4 — Concurrency Control (Study locking protocols, 2PL, MVCC, and deadlocks)
- **Day 5**: M5 — Recovery Systems (Learn WAL and the ARIES recovery process)
- **Day 6**: M6 — Query Processing & Optimization (Calculate join costs and relational algebra trees)
- **Day 7**: Review cheatsheets for Modules 1–6 and solve the numerical Q&As.

### Week 2: Practical SQL & Scale
- **Day 8–10**: M7 — SQL Query Mastering (Write and optimize complex MySQL queries, window functions, and recursive CTEs)
- **Day 11–12**: M8 — Database Architectures & NoSQL (Study partitioning, sharding, replication, CAP, and LSM-trees)
- **Day 13–14**: Mock interviews. Practice mock SQL problems and system design DB selection tasks.

---

## Most Commonly Asked Interview Topics

### Almost Certain to Appear
- SQL Query writing (Joins, aggregations, GROUP BY vs HAVING) (M7)
- Indexes — what they are, how they speed up queries, and B+ Trees (M2)
- ACID properties and their database implementations (M3)
- Transaction isolation levels & anomalies (Dirty Read, Non-repeatable, Phantom) (M3)

### Very Likely
- Optimizing queries using `EXPLAIN` (Seq Scan vs Index Scan) (M6)
- B+ Trees vs LSM-Trees (Read-optimized vs Write-optimized engines) (M8)
- NoSQL vs SQL Database selection (CAP/PACELC trade-offs) (M8)
- Sharding vs Replication (Consensus, quorums, consistent hashing) (M8)

### For Senior / Lead / Systems Roles
- MVCC implementation details (Undo logs, read views) (M4)
- ARIES crash recovery protocol phases (Analysis, Redo, Undo) (M5)
- Normalization theory & Candidate Key calculations (M1)
- Concurrency control details (Strict 2PL, Wound-Wait vs Wait-Die) (M4)
- Join cost estimations (Block nested loop vs Hash joins) (M6)

---

## Key Numbers to Memorize

| Concept | Standard / Invariant |
|---------|----------------------|
| **MySQL default page size** | 16 KB |
| **B+ Tree height (typical)** | 3 to 4 levels (even for millions of records) |
| **Write-Ahead Log (WAL)** | Log record written to disk *before* dirty database page |
| **RAID 5 write penalty** | 4 disk I/Os per logical write |
| **Quorum consistency** | $R + W > N$ (Read Quorum + Write Quorum > Replica Count) |
| **ANSI SQL isolation levels** | Read Uncommitted, Read Committed, Repeatable Read, Serializable |
| **MySQL default isolation level**| Repeatable Read (prevents phantoms too via next-key locking) |
| **SQL execution start** | Evaluated starting from `FROM` clause, NOT the `SELECT` clause |
| **Thomas' Write Rule** | Obsolete writes are ignored instead of aborting the transaction |
| **External Merge Sort Cost** | $2b_r \cdot (\text{passes})$ block transfers |
| **LSM-Tree flush target** | Immutable SSTables on disk, sorted by key |
