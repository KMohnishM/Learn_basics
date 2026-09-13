# Concurrency Control in Database Management Systems

## 1. Why Concurrency Control Matters

In any modern Database Management System (DBMS), concurrency control is a fundamental pillar that ensures data integrity, consistency, and reliability. A typical enterprise database does not serve a single user in isolation; rather, it handles thousands or even tens of thousands of concurrent transactions every second. 

When multiple transactions attempt to read and write the exact same data items simultaneously, the interleaved execution of their operations can lead to severe data anomalies. Without a robust concurrency control mechanism, the database would quickly descend into a state of corruption and inconsistency.

### Common Concurrency Anomalies

1.  **Dirty Reads (Read Uncommitted)**
    A dirty read occurs when a transaction is allowed to read data that has been modified by another concurrent transaction that has not yet committed. If the modifying transaction later aborts and rolls back its changes, the first transaction will have based its logic on data that technically never existed in the database's committed state.
    
2.  **Lost Updates**
    A lost update happens when two separate transactions read the same row, calculate a new value based on that row, and then write the new value back. The transaction that writes last will silently overwrite the changes made by the first transaction, effectively causing the first update to be "lost."
    
3.  **Non-Repeatable Reads (Fuzzy Reads)**
    This anomaly occurs when a transaction reads the same row twice, but gets different data each time because another transaction updated that row and committed its changes between the two reads of the first transaction.
    
4.  **Phantoms (Phantom Reads)**
    A phantom read is similar to a non-repeatable read, but instead of a single row changing, it involves a set of rows. If a transaction executes a query returning a set of rows matching a search condition, and another transaction subsequently inserts, updates, or deletes rows that affect that condition, a re-execution of the identical query will yield a different set of rows (the "phantoms").
    
5.  **Write Skew**
    Write skew is a subtle anomaly that occurs when two concurrent transactions read overlapping data sets, make decisions based on those reads, and then modify disjoint data sets. This can violate business rules that span multiple rows, even if no single row was concurrently updated by both transactions.

### The Gold Standard: Serializability

To prevent these anomalies, databases strive for **Serializability**. Serializability is the highest level of isolation. It guarantees that the outcome of executing a set of transactions concurrently is exactly equivalent to the outcome of executing those same transactions serially (one after the other, in some order). 

There are two primary approaches to implementing concurrency control and achieving serializability:
- **Lock-Based Protocols (e.g., Two-Phase Locking - 2PL)**
- **Version-Based Protocols (e.g., Multi-Version Concurrency Control - MVCC)**

---

## 2. Two-Phase Locking (2PL)

Two-Phase Locking (2PL) is a pessimistic concurrency control protocol that guarantees conflict serializability by dividing a transaction's lock management into two distinct phases.

### The Two Phases

1.  **Phase 1: Growing Phase**
    During the growing phase, a transaction may request and acquire as many locks as it needs to read and write data. However, the critical rule is that once a transaction releases a single lock, it immediately enters the shrinking phase.
    
2.  **Phase 2: Shrinking Phase**
    During the shrinking phase, a transaction may release locks it previously acquired. However, it is absolutely forbidden from acquiring any new locks. Once the shrinking phase begins, the transaction can only give up control.

By strictly adhering to these two phases, 2PL guarantees that all conflicting operations between transactions are ordered consistently, thereby ensuring conflict serializability.

### Variations of 2PL

While basic 2PL guarantees serializability, it is vulnerable to cascading aborts (where the failure of one transaction forces the rollback of other dependent transactions). To solve this, databases use stricter variants:

-   **Strict 2PL (S2PL)**
    A transaction must hold all its **Exclusive (write)** locks until it either commits or aborts. Shared (read) locks can be released during the shrinking phase. This completely prevents dirty reads and cascading aborts.
    
-   **Rigorous 2PL (SS2PL or Strong Strict 2PL)**
    A transaction must hold **ALL** of its locks (both Shared and Exclusive) until it commits or aborts. This is easier to implement and provides strict serializability, though it can reduce concurrency.

### Lock Types and Compatibility

The two most fundamental types of locks are:
-   **Shared Lock (S):** Used for reading data. Multiple transactions can hold a Shared lock on the same data item simultaneously.
-   **Exclusive Lock (X):** Used for writing data. If a transaction holds an Exclusive lock on an item, no other transaction can acquire any lock (S or X) on that same item.

**Standard Lock Compatibility Matrix:**

| Lock Held \ Lock Requested | Shared (S) | Exclusive (X) |
| :--- | :--- | :--- |
| **Shared (S)** | Compatible | Conflict |
| **Exclusive (X)** | Conflict | Conflict |

### Deadlocks and Starvation

-   **Deadlock Risk:** Because transactions acquire locks incrementally over time, a deadlock can occur. For example, Transaction T1 holds a lock on item A and requests a lock on item B. Meanwhile, Transaction T2 holds a lock on item B and requests a lock on item A. Neither can proceed.
-   **Starvation:** A transaction might wait indefinitely to acquire an Exclusive lock if a continuous stream of other transactions keeps acquiring Shared locks on the target item. Modern databases prevent starvation by using FIFO (First-In, First-Out) wait queues for lock acquisition.

---

## 3. Intention Locks (Multi-Granularity Locking)

In a relational database, data is organized hierarchically: Database -> Table -> Page -> Row. 
If a transaction wants to read or write a specific row, it acquires a lock on that row. However, if another transaction wants to drop the entire table, how does it know if any row inside the table is currently locked? Checking every single row would be prohibitively expensive.

This problem is solved using **Intention Locks**, which form the basis of Multi-Granularity Locking (MGL).

### Intention Lock Types

-   **Intention Shared (IS):** Indicates that the transaction intends to acquire Shared (S) locks on some descendant nodes (e.g., rows) lower in the hierarchy.
-   **Intention Exclusive (IX):** Indicates that the transaction intends to acquire Exclusive (X) locks on some descendant nodes lower in the hierarchy.
-   **Shared with Intention Exclusive (SIX):** A combination of S and IX. The transaction reads the entire current node (e.g., the whole table) but also intends to update some specific descendant nodes (e.g., specific rows).

### The MGL Protocol

To lock a node at a fine granularity (like a row), the transaction must first acquire the appropriate Intention locks on all ancestor nodes (table, page) from the root down.
- To get an S or IS lock on a node, it must hold an IS or IX lock on the parent.
- To get an X, IX, or SIX lock on a node, it must hold an IX or SIX lock on the parent.

**5x5 Compatibility Matrix:**

| Lock Held \ Requested | IS | IX | S | SIX | X |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **IS** | Yes | Yes | Yes | Yes | No |
| **IX** | Yes | Yes | No | No | No |
| **S** | Yes | No | Yes | No | No |
| **SIX** | Yes | No | No | No | No |
| **X** | No | No | No | No | No |

### PostgreSQL Table Lock Modes Map

PostgreSQL maps these concepts to its own specific table-level lock modes.

```sql
-- Lock modes (weakest to strongest):
-- 1. ACCESS SHARE: Acquired by SELECT statements. Conflicts only with ACCESS EXCLUSIVE.
-- 2. ROW SHARE: Acquired by SELECT FOR UPDATE/SHARE.
-- 3. ROW EXCLUSIVE: Acquired by INSERT, UPDATE, DELETE.
-- 4. SHARE UPDATE EXCLUSIVE: Acquired by VACUUM, ANALYZE, CREATE INDEX CONCURRENTLY.
-- 5. SHARE: Acquired by CREATE INDEX.
-- 6. SHARE ROW EXCLUSIVE: Acquired by CREATE TRIGGER.
-- 7. EXCLUSIVE: Rarely used explicitly.
-- 8. ACCESS EXCLUSIVE: Acquired by ALTER TABLE, DROP TABLE, VACUUM FULL, REINDEX.

-- You can monitor these table locks in real-time using the system catalogs:
SELECT 
    l.relation::regclass AS table_name, 
    l.mode, 
    l.granted, 
    a.pid, 
    a.query
FROM pg_locks l
JOIN pg_stat_activity a ON l.pid = a.pid
WHERE l.relation IS NOT NULL
ORDER BY l.relation, l.mode;
```

---

## 4. MVCC Deep Dive — PostgreSQL Implementation

Multi-Version Concurrency Control (MVCC) is the primary concurrency strategy used by PostgreSQL. Instead of locking rows for reading and blocking writers (as in strict 2PL), MVCC maintains multiple versions of the same row. This allows readers to view a consistent snapshot of the database from a point in the past, meaning **readers never block writers, and writers never block readers.**

### System Columns

To implement MVCC, PostgreSQL silently adds hidden system columns to every row in every table.

```sql
-- You can view these hidden columns explicitly:
SELECT xmin, xmax, ctid, * FROM accounts LIMIT 5;

-- xmin: The transaction ID (txid) that INSERTed or created this specific row version.
-- xmax: The transaction ID (txid) that DELETEd or UPDATEd this row version. 
--       If xmax is 0, the row version is still "live" and has not been deleted.
-- ctid: The physical location of the row version on disk, represented as (page_number, tuple_index).
--       For example, (0,1) means page 0, slot 1.
```

### The Mechanics of UPDATE and DELETE

In PostgreSQL, an `UPDATE` is not an in-place modification. It is actually a combination of a `DELETE` and an `INSERT`.

```sql
-- Consider what happens during an UPDATE executed by a transaction with txid=500:
BEGIN;  -- txid = 500
UPDATE accounts SET balance = 900 WHERE id = 1;

-- Under the hood, PostgreSQL does the following:
-- 1. Finds the current live version of the row (let's say its xmin is 100).
-- 2. Sets the xmax of this old version to 500, marking it as deleted by txid 500.
-- 3. Inserts a completely new version of the row with the updated data.
--    This new version has xmin=500 and xmax=0.

-- OLD TUPLE: xmin=100, xmax=500, balance=1000 (becomes dead after commit)
-- NEW TUPLE: xmin=500, xmax=0,   balance=900  (becomes live after commit)

COMMIT;

-- For a DELETE operation, PostgreSQL simply sets the xmax to the current txid.
-- The row is NOT physically removed from the disk immediately. It is left behind as a "dead tuple."
```

### Snapshot Construction and Visibility

When a query runs, it needs to know which versions of which rows it is allowed to see. It does this by taking a **Snapshot**.
A snapshot primarily consists of three pieces of data:
-   `xmin`: The lowest transaction ID of any currently active transaction. Any txid strictly less than this `xmin` is definitely committed (or aborted) and not active.
-   `xmax`: The next transaction ID that will be assigned. Any txid greater than or equal to this `xmax` belongs to a transaction that hasn't even started yet from the perspective of this snapshot.
-   `xip`: An array (or list) of all in-progress transaction IDs that fall between `xmin` and `xmax`.

**The Visibility Rule:**
A tuple version is visible to the current snapshot if and only if:
1.  The tuple's `xmin` is committed, and is NOT in the `xip` list.
2.  AND the tuple's `xmax` is either 0 (never deleted), or the transaction in `xmax` is aborted, or the `xmax` transaction is currently in progress (in the `xip` list) and thus its deletion is not yet visible.

```sql
-- Demonstrate snapshot isolation using the REPEATABLE READ isolation level.

-- Session 1: Starts a transaction and takes a snapshot.
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ;
SELECT balance FROM accounts WHERE id = 1;  
-- Let's say this reads 1000. The snapshot is locked in.

-- Session 2 (concurrent connection): Updates the row and commits.
BEGIN;
UPDATE accounts SET balance = 500 WHERE id = 1; 
COMMIT;

-- Session 1 (still running): Reads the same row again.
SELECT balance FROM accounts WHERE id = 1;  
-- STILL reads 1000. 
-- Why? Because Session 2's txid is greater than Session 1's snapshot xmax, 
-- or Session 2's txid was in the xip list when Session 1 took its snapshot.
-- The new version (balance=500) is invisible to Session 1.
COMMIT;
```

### Dead Tuples and VACUUM

Because updates and deletes create new versions and leave old versions behind, tables accumulate "dead tuples." These consume disk space and slow down sequential scans. The `VACUUM` process is responsible for cleaning them up.

```sql
-- Check the number of dead tuples per table:
SELECT 
    relname, 
    n_live_tup, 
    n_dead_tup,
    round(n_dead_tup::numeric / NULLIF(n_live_tup + n_dead_tup, 0) * 100, 2) AS dead_pct,
    last_autovacuum
FROM pg_stat_user_tables 
ORDER BY n_dead_tup DESC 
LIMIT 10;

-- PostgreSQL runs a background daemon called 'autovacuum' to clean tables automatically.
-- The autovacuum trigger formula for a given table is:
-- dead_tuples > autovacuum_vacuum_threshold + (autovacuum_vacuum_scale_factor * n_live_tuples)

-- Default configuration:
-- threshold = 50
-- scale_factor = 0.20 (20%)
-- For a 1,000,000 row table, autovacuum triggers at approximately 200,050 dead tuples.

-- Manual Vacuum operations:
VACUUM orders;              -- Reclaims space from dead tuples (does NOT take an exclusive lock, allows concurrent reads/writes).
VACUUM ANALYZE orders;      -- Vacuums the table and also updates planner statistics.
VACUUM FULL orders;         -- Completely rewrites the table to eliminate fragmentation. 
                            -- WARNING: Takes an ACCESS EXCLUSIVE lock. Avoid in production!
VACUUM FREEZE orders;       -- Aggressively freezes old tuples to prevent transaction ID wraparound.
VACUUM VERBOSE orders;      -- Prints detailed progress output to the console.

-- Tuning autovacuum for high-churn tables (tables with frequent updates/deletes):
-- You want these tables to be vacuumed more frequently to prevent bloat.
ALTER TABLE orders SET (
  autovacuum_vacuum_scale_factor = 0.05,  -- Trigger at 5% instead of 20%
  autovacuum_vacuum_threshold = 100,
  autovacuum_analyze_scale_factor = 0.02  -- Analyze more frequently as well
);
```

### Transaction ID Wraparound

PostgreSQL uses 32-bit integers for transaction IDs. This means there are a maximum of roughly 4.29 billion possible transaction IDs.
To handle the fact that a database will eventually process more than 4 billion transactions, PostgreSQL uses modular arithmetic. The ID space is treated as a circle. At any given time, for any specific transaction ID, approximately 2 billion IDs are considered to be "in the past" (committed and visible), and 2 billion are considered to be "in the future" (not yet visible).

If a table is not vacuumed for a very long time, and the global transaction counter advances by more than 2 billion, the extremely old tuples in that table will suddenly appear to have a transaction ID that is in the "future." Consequently, all that old data will instantaneously become invisible to all queries. This catastrophic event is called **Transaction ID Wraparound**.

To prevent this, `VACUUM` replaces very old transaction IDs with a special frozen ID. This process is called "freezing."

```sql
-- Monitor the age of the oldest unfrozen transaction ID in your databases.
-- This is a CRITICAL monitoring metric. Alert immediately if xid_age > 1.5 billion.
SELECT 
    datname, 
    age(datfrozenxid) AS xid_age,
    pg_size_pretty(pg_database_size(datname)) AS size
FROM pg_database 
ORDER BY xid_age DESC;

-- You can also check the XID age on a per-table basis:
SELECT 
    relname, 
    age(relfrozenxid) AS table_xid_age
FROM pg_class 
WHERE relkind = 'r'
ORDER BY age(relfrozenxid) DESC 
LIMIT 20;

-- The setting 'autovacuum_freeze_max_age' (default 200,000,000) controls when 
-- PostgreSQL forces an aggressive "freeze" vacuum on a table, regardless of dead tuple count.
-- If the system-wide age reaches a hardcoded safety threshold (typically around 2 billion minus a few million),
-- PostgreSQL will force an emergency shutdown to prevent data loss. 
-- The database will refuse to start until a manual, single-user VACUUM is performed.
```

---

## 5. Row-Level Locking

While MVCC handles most concurrency needs elegantly, there are times when an application must explicitly lock specific rows to serialize business logic or prevent concurrent modifications. PostgreSQL provides several explicit row-level lock modes.

### Standard Row Locks

```sql
-- 1. FOR UPDATE: Exclusive row lock.
-- This is the strongest row-level lock. It completely locks the selected rows.
-- It prevents any other transaction from acquiring FOR UPDATE, FOR SHARE, FOR NO KEY UPDATE, or FOR KEY SHARE locks.
-- It also prevents other transactions from executing UPDATE or DELETE on these rows.
SELECT * FROM accounts WHERE id = 1 FOR UPDATE;

-- 2. FOR SHARE: Shared row lock.
-- Multiple transactions can hold a FOR SHARE lock on the same row simultaneously.
-- It prevents other transactions from modifying the row (UPDATE or DELETE) or acquiring an exclusive FOR UPDATE lock.
SELECT * FROM accounts WHERE id = 1 FOR SHARE;

-- 3. FOR NO KEY UPDATE: Weaker exclusive lock.
-- Acquired automatically by UPDATE statements that do not modify the primary key or unique constraints.
-- It is exclusive, but it ALLOWS other transactions to acquire a FOR KEY SHARE lock.
SELECT * FROM accounts WHERE id = 1 FOR NO KEY UPDATE;

-- 4. FOR KEY SHARE: Weakest shared lock.
-- Acquired automatically by PostgreSQL when checking foreign key constraints.
-- It prevents the referenced row from being deleted or its key from being updated.
SELECT * FROM accounts WHERE id = 1 FOR KEY SHARE;
```

### Advanced Locking Modifiers

```sql
-- By default, if a transaction tries to acquire a lock on a row that is already locked, it will block and wait.

-- NOWAIT: Modifies the locking behavior to fail immediately instead of waiting.
-- If the lock cannot be acquired instantly, PostgreSQL raises an error.
SELECT * FROM accounts WHERE id = 1 FOR UPDATE NOWAIT;
-- ERROR: could not obtain lock on row in relation "accounts"
-- The application can catch this error and decide to retry later or inform the user.

-- SKIP LOCKED: Modifies the locking behavior to simply ignore any rows that are currently locked by other transactions.
-- This is incredibly powerful for implementing highly concurrent job queues.
SELECT * FROM jobs
WHERE status = 'pending'
ORDER BY priority DESC, created_at
LIMIT 1
FOR UPDATE SKIP LOCKED;

-- Complete implementation of a robust, highly concurrent job queue worker:
BEGIN;

-- 1. Find and lock the highest priority pending job.
-- 2. Skip any jobs that other concurrent workers are already locking.
-- 3. Update the selected job's status in the same atomic statement.
UPDATE jobs
SET 
    status = 'processing', 
    started_at = NOW(), 
    worker_id = pg_backend_pid()
WHERE id = (
  SELECT id FROM jobs
  WHERE status = 'pending'
  ORDER BY priority DESC, created_at
  LIMIT 1
  FOR UPDATE SKIP LOCKED
)
RETURNING *;

-- 4. The application processes the job payload here...

-- 5. Mark the job as completed.
UPDATE jobs SET status = 'completed', finished_at = NOW() WHERE id = :job_id;

COMMIT;
```

---

## 6. Deadlock Detection and Prevention

When transactions acquire locks on multiple resources in different orders, deadlocks can occur. PostgreSQL has a built-in background process to detect and resolve these situations.

### Detection Mechanism

```sql
-- PostgreSQL does not check for deadlocks immediately upon every lock wait, because the check is computationally expensive.
-- Instead, it waits for a configured amount of time before constructing and analyzing the "wait-for graph".
SHOW deadlock_timeout;  -- The default is usually 1s (1000ms).

-- If a cycle is detected in the wait-for graph, a deadlock exists.
-- PostgreSQL will arbitrarily choose one of the transactions involved as a "victim" and abort it.
-- The victim transaction receives the following error:
-- ERROR: deadlock detected (SQLSTATE 40P01)
-- DETAIL: Process 1234 waits for ShareLock on transaction 5678; blocked by process 4321.
-- It is the responsibility of the application code to catch this SQLSTATE and retry the transaction from the beginning.
```

### Deadlock Prevention

The best way to handle deadlocks is to prevent them entirely through careful application design. The golden rule is: **Always acquire locks in a consistent, deterministic order.**

```sql
-- BAD PRACTICE (Leads to Deadlocks):
-- Transaction 1: Locks account 1, then attempts to lock account 2.
-- Transaction 2: Locks account 2, then attempts to lock account 1.
-- If they run concurrently, they will deadlock.

-- GOOD PRACTICE (Deadlock-Free):
-- Always sort the IDs or resources before acquiring locks.
BEGIN;
-- Lock rows in strict ascending order by ID.
SELECT * FROM accounts
WHERE id IN (1, 2) 
ORDER BY id 
FOR UPDATE;

-- Now perform the updates.
UPDATE accounts SET balance = balance - 500 WHERE id = 1;
UPDATE accounts SET balance = balance + 500 WHERE id = 2;
COMMIT;
```

### Monitoring and Intervention

```sql
-- Query to monitor current lock waits and identify blocking queries:
SELECT
  blocked_locks.pid          AS blocked_pid,
  blocked_activity.query     AS blocked_query,
  blocking_locks.pid         AS blocking_pid,
  blocking_activity.query    AS blocking_query,
  blocked_activity.wait_event
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks
  ON blocking_locks.locktype = blocked_locks.locktype
  AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
  AND blocking_locks.granted
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;

-- If a transaction is hopelessly blocked and causing a system-wide outage, a DBA can intervene manually:
SELECT pg_cancel_backend(pid);    -- Graceful termination. Sends SIGINT to the backend process. Only aborts the current query.
SELECT pg_terminate_backend(pid); -- Forceful termination. Sends SIGTERM to the backend process. Kills the entire connection.
```

---

## 7. Advisory Locks

Relational constraints and row locks protect the physical data in the database. However, sometimes an application needs a distributed locking mechanism to synchronize arbitrary, logical application-level operations across multiple servers. PostgreSQL provides **Advisory Locks** for exactly this purpose.

Advisory locks have no implicit meaning to the database engine. They do not lock tables or rows. They are simply integer keys that the database manages on behalf of the application. The application defines what the keys mean and must enforce the locking protocol itself.

### Types of Advisory Locks

Advisory locks can be acquired at two levels: Session and Transaction.

```sql
-- 1. Session-Level Advisory Locks
-- These locks are held until they are explicitly released by the application, or until the database session (connection) disconnects.
-- They are NOT released automatically when a transaction commits or rolls back.

SELECT pg_advisory_lock(12345);          -- Blocking: Waits indefinitely until the lock on key '12345' is acquired.
SELECT pg_try_advisory_lock(12345);      -- Non-blocking: Returns true if acquired, false if held by someone else. Returns instantly.

SELECT pg_advisory_unlock(12345);        -- Explicitly release the lock.
SELECT pg_advisory_unlock_all();         -- Utility function to release all session-level advisory locks held by the current connection.

-- Shared Advisory Locks
-- Multiple sessions can hold a shared advisory lock on the same key simultaneously.
SELECT pg_advisory_lock_shared(12345);
SELECT pg_try_advisory_lock_shared(12345);


-- 2. Transaction-Level Advisory Locks
-- These behave more like standard database locks. They are automatically released when the current transaction ends (COMMIT or ROLLBACK).
-- There is no explicit unlock function for transaction-level advisory locks.

BEGIN;
SELECT pg_advisory_xact_lock(12345);         -- Blocks until acquired.
SELECT pg_try_advisory_xact_lock(12345);     -- Non-blocking.
-- Do work...
COMMIT;  -- The lock on 12345 is automatically released here.
```

### Real-World Use Cases

```sql
-- Use Case 1: Distributed Cron Job Deduplication
-- You have multiple application servers, but a scheduled nightly job should only run on ONE server at a time.
DO $$
BEGIN
  -- We use hashtext() to convert a string name into a 32-bit integer key.
  IF pg_try_advisory_lock(hashtext('nightly_report')) THEN
    -- We successfully acquired the lock. This server is the leader.
    PERFORM do_nightly_report();
    -- Must explicitly unlock because we used a session-level lock.
    PERFORM pg_advisory_unlock(hashtext('nightly_report'));
  ELSE
    -- Another server holds the lock. We skip the job.
    RAISE NOTICE 'Job already running on another server';
  END IF;
END;
$$;


-- Use Case 2: Per-Entity Logical Processing Lock
-- Prevent concurrent processing of a specific user's complex workflow, even if it spans multiple database tables or external API calls.
BEGIN;
-- Acquire a transaction-level lock based on the user's ID.
SELECT pg_advisory_xact_lock(user_id) FROM users WHERE id = :user_id;

-- Now we can safely query, calculate, and update multiple tables for this user.
-- No other transaction can acquire the advisory lock for this specific user_id.
-- This is much cleaner than trying to acquire row locks on 5 different tables.

COMMIT;


-- Monitoring Advisory Locks
-- You can view all currently active advisory locks in the pg_locks view.
SELECT 
    pid, 
    classid, 
    objid, 
    mode, 
    granted
FROM pg_locks 
WHERE locktype = 'advisory';
```

---

## 8. Row-Level Security (RLS)

Historically, database permissions were granted at the table level (e.g., User A can read Table X). With the rise of multi-tenant SaaS applications, this is often insufficient. **Row-Level Security (RLS)** allows database administrators to define policies that restrict which specific rows within a table a given user is allowed to read, update, or delete.

### Enabling RLS and Basic Policies

```sql
-- First, RLS must be explicitly enabled on the target table.
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;

-- Note: By default, the table owner and superusers bypass RLS policies.
-- If you want the policies to apply even to the table owner, you must force it:
ALTER TABLE accounts FORCE ROW LEVEL SECURITY;


-- Creating a simple user isolation policy:
-- This policy states that a row is only visible/modifiable if the 'owner_id' column matches the current database user's name.
CREATE POLICY user_isolation ON accounts
  USING (owner_id = current_user);


-- You can create separate, highly granular policies for different DML operations.
CREATE POLICY accounts_select ON accounts
  FOR SELECT 
  USING (owner_id = current_user);

-- WITH CHECK ensures that new data being inserted conforms to the rule.
-- You cannot insert a row claiming it belongs to someone else.
CREATE POLICY accounts_insert ON accounts
  FOR INSERT 
  WITH CHECK (owner_id = current_user);

-- UPDATE policies often require both USING (can I see the old row?) and WITH CHECK (is the new state allowed?).
CREATE POLICY accounts_update ON accounts
  FOR UPDATE
  USING (owner_id = current_user)
  WITH CHECK (owner_id = current_user);
```

### Multi-Tenant Architecture with RLS

In many modern applications, all database connections use a single generic database user, but the application manages logical "tenants." RLS can still be used powerfully here via session variables.

```sql
-- Define a policy that filters rows based on a custom session setting.
CREATE POLICY tenant_isolation ON orders
  USING (tenant_id = current_setting('app.tenant_id')::int);

-- The application backend must set this variable at the start of every transaction.
BEGIN;
-- Use SET LOCAL to ensure the variable is scoped ONLY to the current transaction.
-- This prevents leakage if connections are pooled.
SET LOCAL app.tenant_id = '42';  

-- When the application executes a generic SELECT, PostgreSQL transparently appends the RLS filter.
SELECT * FROM orders;  
-- The database engine executes it as: SELECT * FROM orders WHERE tenant_id = 42;

COMMIT;


-- Creating administrative bypasses:
-- You might have admin processes that need to see all rows across all tenants.
CREATE ROLE app_admin BYPASSRLS;

-- Testing RLS policies interactively via psql:
SET ROLE regular_user;
SELECT COUNT(*) FROM accounts;  -- Output will be restricted to this user's rows.
RESET ROLE;                     -- Revert back to the superuser to see everything.
```

---

## 9. Connection Pooling

Because of PostgreSQL's multi-process architecture, connection pooling is an absolute necessity for any application operating at scale.

### The Problem with Direct Connections

Unlike databases that use a thread-per-connection model (like MySQL), PostgreSQL uses a **process-per-connection** model. When a client application connects to PostgreSQL, the postmaster daemon forks a completely new operating system process to handle that connection.
-   **Memory Overhead:** Each backend process consumes approximately 5MB to 10MB of base RAM, plus additional memory for query execution (work_mem).
-   **CPU Overhead:** Forking a process is expensive. The negotiation of authentication and parameters takes time.
-   **Scaling Limits:** If an application opens 500 connections, that's up to 5GB of RAM consumed just by idle processes doing nothing. Consequently, PostgreSQL's practical limit for direct connections is typically between 100 and 300, depending on the hardware and workload.

To bridge the gap between thousands of application threads and a small number of heavy PostgreSQL backend processes, a connection pooler like **PgBouncer** is placed in between.

### PgBouncer Configuration and Architecture

PgBouncer is a lightweight connection pooler specifically built for PostgreSQL. It maintains a pool of persistent connections to the database and multiplexes thousands of incoming application connections across them.

```ini
# Example /etc/pgbouncer/pgbouncer.ini configuration file

[databases]
# Map internal aliases to actual database connection strings
app = host=127.0.0.1 port=5432 dbname=app_production
app_ro = host=replica.internal port=5432 dbname=app_production

[pgbouncer]
listen_port = 6432
listen_addr = 0.0.0.0
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt

# The most critical setting is the pool_mode.
# 1. session:     A server connection is assigned to the client for the entire duration of the client session.
#                 This is very safe and supports all PostgreSQL features, but scales poorly.
# 2. transaction: A server connection is assigned to the client ONLY for the duration of a single transaction.
#                 When the transaction commits/rolls back, the connection is returned to the pool for another client to use.
#                 This is the RECOMMENDED mode for massive scalability.
# 3. statement:   A server connection is assigned for a single SQL statement.
#                 Transactions containing multiple statements are not supported. Rarely used.
pool_mode = transaction

max_client_conn = 2000       # Maximum number of application connections allowed to PgBouncer.
default_pool_size = 25       # Actual persistent PostgreSQL connections maintained per database/user pair.
min_pool_size = 5
reserve_pool_size = 5
reserve_pool_timeout = 3
server_idle_timeout = 600
```

### Caveats of Transaction Pool Mode

While `transaction` pool mode is essential for scaling, it breaks the concept of stateful sessions. Because an application connection might be routed to physical connection A for one transaction, and physical connection B for the next transaction, any state set on the connection is either lost or, worse, bleeds into other clients' sessions.

```sql
-- DANGEROUS / BROKEN PATTERN in transaction pool mode:
SET app.tenant_id = '42';   -- This executes in an implicit transaction. The server connection is then returned to the pool.
-- ... later in the application code ...
SELECT * FROM orders;       -- This grabs a DIFFERENT connection from the pool. The tenant_id setting is missing!


-- CORRECT PATTERN for transaction pool mode:
BEGIN;
-- Use SET LOCAL. The setting is explicitly bound to the current transaction.
SET LOCAL app.tenant_id = '42';  
SELECT * FROM orders;             -- Executes on the same connection, the setting is active.
COMMIT;                           
-- The transaction ends. The connection is returned to the pool, and PostgreSQL automatically clears the SET LOCAL variable.


-- Features that are strictly incompatible or dangerous in PgBouncer transaction pool mode:
-- 1. SET commands (session-level). Must use SET LOCAL inside BEGIN/COMMIT blocks.
-- 2. LISTEN / NOTIFY (pub/sub). Requires a dedicated, long-lived session.
-- 3. Named Prepared Statements. 
--    (Application frameworks must use protocol-level unnamed prepared statements, or PgBouncer must be configured with max_prepared_statements).
-- 4. Session-level Advisory Locks (pg_advisory_lock). 
--    (You must use transaction-level locks: pg_advisory_xact_lock).
-- 5. Temporary Tables. Since they are scoped to the session, they will disappear or be accessed by the wrong client.
```
