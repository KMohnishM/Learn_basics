# PostgreSQL Indexing Cheatsheet

## 1. Index Types Overview

| Index Type | Primary Use Case | Supported Operators | Pros | Cons |
| :--- | :--- | :--- | :--- | :--- |
| **B-Tree** (Default) | Equality, Range, Sorting | `=`, `<`, `>`, `<=`, `>=`, `BETWEEN`, `IN` | Versatile, fast for ordered data | Write amplification on splits |
| **Hash** | Pure Equality | `=` | O(1) lookups, crash-safe (PG10+) | Cannot do range queries or sorting |
| **GiST** | Geometry, Text Search, Ranges | `<<`, `>>`, `&&`, `@>`, `<@`, `~` | Highly extensible, 2D/3D capable | Slower read performance than B-Tree |
| **GIN** | Arrays, JSONB, Full Text | `@>`, `<@`, `?`, `?&`, `?\|` | Inverted indexing, incredibly fast reads | Slower updates, high maintenance overhead |
| **BRIN** | Very large, naturally ordered tables | `=`, `<`, `>`, `<=`, `>=` | Tiny size, zero maintenance overhead | Coarse filtering, requires heap scans |

## 2. B-Tree Math and Height

*   **Page Size (Block):** 8192 bytes (8KB) default.
*   **Branching Factor (b):** Number of children per node. `b ≈ (PageSize / KeySize)`.
*   **Max Tuples per Page (Heap):** ≈ 290 (due to header overhead and alignment).
*   **B-Tree Height Formula:** $h = \log_b(N)$ where $N$ is total rows.
*   **Cost of B-Tree Lookup:** $O(h)$ page reads.

## 3. Index Design Rules

1.  **Equality Precedes Range:** `(A, B)` is correct for `WHERE A = 1 AND B > 2`.
2.  **High Cardinality First (for Equalities):** If both are `=`, place the column with more unique values first to prune the tree faster.
3.  **Covering Indexes for Performance:** Use `INCLUDE` to append payload data. `CREATE INDEX idx ON tbl (key) INCLUDE (payload);` enables Index-Only Scans.
4.  **Avoid Indexing Booleans:** Full indexes on low-cardinality flags are ignored. Use partial indexes: `CREATE INDEX idx_active ON tbl (id) WHERE active = true;`.
5.  **Correlated Data:** Use BRIN for time-series append-only tables to save space.

## 4. Query Planner Nodes (EXPLAIN)

| Node Name | Description | Cost / I/O Profile |
| :--- | :--- | :--- |
| **Seq Scan** | Reads entire table block by block | High volume, fast sequential I/O |
| **Index Scan** | Traverses index, fetches heap tuple | Low volume, slow random I/O |
| **Index Only Scan**| Reads only index, checks Visibility Map | Lowest volume, avoids heap fetch |
| **Bitmap Index Scan**| Scans index, builds in-memory page bitmap | Translates random to sequential I/O |
| **Bitmap Heap Scan** | Reads heap using bitmap from previous step | Efficient for moderate data retrieval |
| **Nested Loop** | For each outer row, scans inner relation | Best for small outer, indexed inner |
| **Hash Join** | Builds hash table, probes with outer | Best for large, unsorted sets (needs RAM)|
| **Merge Join** | Zips two sorted inputs | Best when inputs are already sorted |

## 5. VACUUM vs ANALYZE

| Command | Primary Function | Modifies Data File? | Updates Statistics? |
| :--- | :--- | :--- | :--- |
| **VACUUM** | Marks dead tuples (MVCC) as free space | No (unless VACUUM FULL) | No |
| **ANALYZE** | Samples data to update planner statistics | No | Yes (`pg_statistic`) |
| **VACUUM ANALYZE**| Does both concurrently | No | Yes |

*Rule of thumb:* Run ANALYZE after bulk inserts/updates to fix bad planner estimates.

## 6. Crucial pg_stat Queries

**Find Unused Indexes (Candidate for drop):**
```sql
SELECT
    schemaname || '.' || relname AS table,
    indexrelname AS index,
    pg_size_pretty(pg_relation_size(i.indexrelid)) AS size,
    idx_scan AS scans
FROM pg_stat_user_indexes i
JOIN pg_index USING (indexrelid)
WHERE idx_scan = 0 AND indisunique IS FALSE
ORDER BY pg_relation_size(i.indexrelid) DESC;
```

**Find Cache Hit Ratio (Should be >99% in memory):**
```sql
SELECT
    sum(heap_blks_read) as heap_read,
    sum(heap_blks_hit)  as heap_hit,
    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as ratio
FROM pg_statio_user_tables;
```

**Check Table Statistics (When was it last analyzed?):**
```sql
SELECT relname, last_vacuum, last_autovacuum, last_analyze, last_autoanalyze
FROM pg_stat_user_tables
WHERE relname = 'your_table_name';
```
