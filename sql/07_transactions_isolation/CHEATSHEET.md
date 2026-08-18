# CHEATSHEET: Transactions & Isolation

## ACID Properties

| Property | Description | PostgreSQL Mechanism |
| :--- | :--- | :--- |
| **Atomicity** | All operations succeed, or none do. | Write-Ahead Log (WAL), Rollbacks |
| **Consistency** | Database moves between valid states. | Constraints (Foreign Key, Check, Unique) |
| **Isolation** | Concurrent transactions don't interfere. | MVCC, explicit row/table Locking |
| **Durability** | Committed data survives crashes. | WAL flushed to disk (`fsync`) |

## Isolation Levels & Anomalies Matrix

| Isolation Level | Dirty Read | Non-Repeatable Read | Phantom Read | Serialization Anomalies (Write Skew) |
| :--- | :--- | :--- | :--- | :--- |
| **READ UNCOMMITTED** | *Impossible in PG* | Allowed | Allowed | Allowed |
| **READ COMMITTED** (PG Default)| Prevented | Allowed | Allowed | Allowed |
| **REPEATABLE READ** | Prevented | Prevented | *Prevented in PG* | Allowed |
| **SERIALIZABLE** | Prevented | Prevented | Prevented | Prevented |

*Note: PostgreSQL's implementation of REPEATABLE READ is stricter than the SQL standard, automatically preventing phantom reads via MVCC snapshots.*

## MVCC (Multi-Version Concurrency Control) Concept

```text
Time --->
      [Row A, v1: id=1, status='Active']

Tx1: BEGIN (Snapshot taken)
Tx1: SELECT status FROM table (Sees 'Active')

Tx2: BEGIN
Tx2: UPDATE table SET status = 'Inactive'
Tx2: COMMIT
      [Row A, v1: id=1, status='Active'] <--- "Dead" tuple, kept for Tx1
      [Row A, v2: id=1, status='Inactive'] <-- New active tuple

Tx1: SELECT status FROM table (Still sees 'Active' via snapshot)
Tx1: COMMIT
      (VACUUM process eventually cleans up v1)
```

## Row Locking Syntax

Used within a transaction block (`BEGIN; ... COMMIT;`) to prevent Lost Updates or build queues.

| Syntax | Description | Use Case |
| :--- | :--- | :--- |
| `SELECT ... FOR UPDATE` | Exclusive lock. Blocks other updates/locks. | Read-modify-write cycles to prevent lost updates. |
| `SELECT ... FOR SHARE` | Shared lock. Blocks updates, allows other shares. | Ensuring a row isn't deleted/modified while you work. |
| `SELECT ... FOR NO KEY UPDATE`| Weaker exclusive. Allows `FOR KEY SHARE`. | Updating non-key columns (avoids foreign key blocking).|
| `... FOR UPDATE SKIP LOCKED` | Skips rows locked by others instead of waiting. | High-concurrency work queues / job processing. |
| `... FOR UPDATE NOWAIT` | Throws immediate error if row is locked. | Failing fast when resources are busy. |

## Deadlock Prevention Checklist

*   [ ] **Consistent Ordering**: Always acquire locks (updates/deletes) on multiple tables/rows in the exact same alphabetical or hierarchical order across the entire application.
*   [ ] **Short Transactions**: Keep transactions as brief as possible. Do not wait for API calls or user input inside a transaction.
*   [ ] **Lock Early**: If you know you will update a row, use `SELECT ... FOR UPDATE` immediately when reading it, rather than waiting until the end of the transaction.
*   [ ] **Batch Operations**: Instead of updating rows one by one in a loop inside a transaction, use bulk `UPDATE ... FROM` to let the database handle internal locking efficiently.
