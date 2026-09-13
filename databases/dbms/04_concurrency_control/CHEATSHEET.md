# Concurrency Control Cheatsheet

## 1. Lock Compatibility Matrix

| Lock Type | Shared (S) | Exclusive (X) | Intent Shared (IS) | Intent Exclusive (IX) | Shared + Intent Exclusive (SIX) |
|---|---|---|---|---|---|
| **Shared (S)** | Compatible | Incompatible | Compatible | Incompatible | Incompatible |
| **Exclusive (X)** | Incompatible | Incompatible | Incompatible | Incompatible | Incompatible |
| **Intent Shared (IS)** | Compatible | Incompatible | Compatible | Compatible | Compatible |
| **Intent Exclusive (IX)**| Incompatible | Incompatible | Compatible | Compatible | Incompatible |
| **SIX** | Incompatible | Incompatible | Compatible | Incompatible | Incompatible |

## 2. MVCC Tuple Visibility Rules

PostgreSQL uses system columns (`xmin`, `xmax`, `cmin`, `cmax`) to handle visibility. 

*   **`xmin`**: The ID of the transaction that inserted the row.
*   **`xmax`**: The ID of the transaction that deleted or updated the row (0 if not deleted).

**Visibility Condition (Simplified):**
A tuple is visible to a transaction if:
1.  `xmin` is committed and `xmin` < `snapshot_xmax`.
2.  `xmax` is 0, OR `xmax` is aborted, OR `xmax` >= `snapshot_xmax`.

## 3. VACUUM Operations

| Command | Purpose | Locks Acquired | Disk Space Reclaimed to OS | Updates Statistics |
|---|---|---|---|---|
| `VACUUM` | Marks dead tuples as free space for future inserts/updates. | `SHARE UPDATE EXCLUSIVE` (Allows concurrent reads/writes) | No | No |
| `VACUUM ANALYZE` | Same as `VACUUM`, but also updates planner statistics. | `SHARE UPDATE EXCLUSIVE` | No | Yes |
| `VACUUM FULL` | Rewrites the entire table, removing dead space completely. | `ACCESS EXCLUSIVE` (Blocks all access) | Yes | No |

## 4. PgBouncer Pool Modes

| Mode | Description | Best For | Limitations |
|---|---|---|---|
| **Session** | Client holds a server connection for the entire session. | Legacy apps expecting dedicated connections. | Very low scalability. Defeats the purpose of pooling for large scale. |
| **Transaction**| Client gets a connection only for the duration of a transaction. | High-concurrency web apps, microservices. | Cannot use session-level features (prepared statements without special config, advisory locks, `SET LOCAL`). |
| **Statement** | Client gets a connection for a single statement. | Extreme concurrency with short reads. | Multi-statement transactions are not allowed. |

## 5. Useful Monitoring Queries

### XID Age Monitoring (Prevent Wraparound)
```sql
SELECT datname, age(datfrozenxid) AS xid_age,
       pg_size_pretty(pg_database_size(datname)) AS db_size
FROM pg_database
ORDER BY xid_age DESC;
```

### Deadlock and Blocked Query Monitoring
```sql
SELECT
  blocked.pid AS blocked_pid,
  blocked.query AS blocked_query,
  blocking.pid AS blocking_pid,
  blocking.query AS blocking_query
FROM pg_stat_activity blocked
JOIN pg_stat_activity blocking
  ON blocked.wait_event = blocking.pid::text
WHERE blocked.wait_event_type = 'Lock';
```

### Find Queries using `pg_blocking_pids`
```sql
SELECT pid, pg_blocking_pids(pid) AS blocking_pids, query
FROM pg_stat_activity
WHERE cardinality(pg_blocking_pids(pid)) > 0;
```

## 6. Two-Phase Locking (2PL) Phases Diagram

```text
Lock Count
    ^
    |       Phase 1 (Growing)           Phase 2 (Shrinking)
    |      -------------------        ----------------------
    |     /                   \      /                      \
    |    /                     \    /                        \
    |   /                       \  /                          \
    |  /                         \/                            \
    | /                          |                              \
    |/                           |                               \
    +---------------------------------------------------------------> Time
                             Lock Point
```
