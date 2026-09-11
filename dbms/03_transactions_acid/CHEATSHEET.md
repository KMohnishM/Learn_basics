# Database Transactions Cheatsheet

## ACID Properties

| Property | Description | Goal |
| :--- | :--- | :--- |
| **Atomicity** | All operations within a transaction succeed, or none do. | Prevent partial updates (all-or-nothing). |
| **Consistency** | The database remains in a valid state before and after the transaction. | Enforce constraints, triggers, and rules. |
| **Isolation** | Concurrent transactions behave as if executed sequentially. | Prevent interference between concurrent tasks. |
| **Durability** | Committed changes are permanent, surviving system crashes. | Ensure data is safely written to disk. |

## Concurrency Anomalies

| Anomaly | Description | Example Scenario |
| :--- | :--- | :--- |
| **Dirty Read** | Reading data written by an uncommitted transaction. | TX1 reads balance updated by TX2, TX2 rolls back. |
| **Non-Repeatable Read** | Reading the same row twice yields different results. | TX1 reads row, TX2 updates row & commits, TX1 reads again. |
| **Phantom Read** | Re-executing a query yields a different set of rows. | TX1 counts rows, TX2 inserts a new row & commits, TX1 counts again. |
| **Write Skew** | Disjoint updates based on overlapping reads violate constraints. | TX1 & TX2 check constraint, both update different rows, breaking constraint. |
| **Lost Update** | Overwriting an uncommitted change based on stale read. | TX1 & TX2 read value, TX1 updates, TX2 updates overwriting TX1. |

## Isolation Levels (Standard vs PostgreSQL)

| Isolation Level | Dirty Read | Non-Repeatable Read | Phantom Read | Serialization Anomaly |
| :--- | :--- | :--- | :--- | :--- |
| **Read Uncommitted** | Allowed *(PG Prevents)* | Allowed | Allowed | Allowed |
| **Read Committed** (Default) | Prevented | Allowed | Allowed | Allowed |
| **Repeatable Read** | Prevented | Prevented | Allowed *(PG Prevents)* | Allowed |
| **Serializable** | Prevented | Prevented | Prevented | Prevented |

## Explicit Locking Modes (Row Level)

| Lock Mode | Usage | Conflicts With |
| :--- | :--- | :--- |
| **FOR UPDATE** | Full exclusive lock for UPDATE/DELETE. | FOR UPDATE, FOR NO KEY UPDATE, FOR SHARE, FOR KEY SHARE |
| **FOR NO KEY UPDATE** | Exclusive lock, but no primary key changes. | FOR UPDATE, FOR NO KEY UPDATE, FOR SHARE |
| **FOR SHARE** | Shared lock, reading data, preventing updates. | FOR UPDATE, FOR NO KEY UPDATE |
| **FOR KEY SHARE** | Weak shared lock, validating foreign keys. | FOR UPDATE |

## Explicit Locking Modes (Table Level Examples)

| Lock Mode | Acquired By (Implicitly) | Conflicts With |
| :--- | :--- | :--- |
| **ACCESS SHARE** | SELECT | ACCESS EXCLUSIVE |
| **ROW EXCLUSIVE** | UPDATE, DELETE, INSERT | SHARE, SHARE ROW EXCLUSIVE, EXCLUSIVE, ACCESS EXCLUSIVE |
| **ACCESS EXCLUSIVE** | DROP TABLE, TRUNCATE, ALTER TABLE | ALL OTHER LOCK MODES |

## Deadlock Rules & Prevention

1.  **Consistent Ordering:** Always acquire locks on multiple resources in the exact same alphabetical or logical order across all application code.
2.  **Short Transactions:** Keep transaction blocks as brief as possible.
3.  **No User Input:** Never wait for user interaction while holding a transaction open.
4.  **Appropriate Isolation:** Use Read Committed unless stricter guarantees are explicitly required.
5.  **Detect & Retry:** Ensure application code catches `ERROR: deadlock detected` (SQLSTATE 40P01) and retries the transaction.

## MVCC (Multiversion Concurrency Control) Basics

*   **Writers do not block readers.**
*   **Readers do not block writers.**
*   Each row has `xmin` (creating transaction ID) and `xmax` (deleting transaction ID).
*   Transactions only see rows where `xmin` is committed and `xmax` is either uncommitted, aborted, or NULL.
*   Requires `VACUUM` to physically remove dead tuples (rows where `xmax` is committed and no longer visible to any snapshot).
