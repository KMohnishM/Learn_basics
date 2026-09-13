# Concurrency Control Q&A

**1. Explain Two-Phase Locking (2PL). What are the growing and shrinking phases? Why does 2PL guarantee conflict serializability? What does Strict 2PL add and why does it prevent cascading aborts?**
Two-Phase Locking (2PL) is a concurrency control protocol that ensures serializability by dividing a transaction's execution into two distinct phases. The first phase is the "growing phase," during which a transaction may obtain locks but cannot release any. The second phase is the "shrinking phase," during which the transaction may release locks but cannot acquire any new ones. By adhering to this rule, 2PL guarantees conflict serializability because all conflicting operations are strictly ordered across transactions; no cyclic dependencies can form since a transaction must have all needed locks before it starts releasing them. However, basic 2PL suffers from the risk of cascading aborts: if transaction T1 modifies data and releases its lock, and T2 reads that data, an abort of T1 would necessitate an abort of T2. Strict 2PL prevents this by requiring that a transaction hold all its exclusive (write) locks until it either commits or aborts. This ensures that uncommitted data is never read by other transactions, completely eliminating the possibility of cascading aborts and ensuring recoverability.
```sql
BEGIN;
-- Growing phase: acquiring locks
SELECT * FROM accounts WHERE id = 1 FOR UPDATE;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
-- Strict 2PL ensures this lock is held until COMMIT
COMMIT;
```

**2. What is the lock compatibility matrix? What is the difference between a Shared lock and an Exclusive lock? If transaction T1 holds a Shared lock and T2 requests an Exclusive lock, what happens?**
The lock compatibility matrix is a predefined table used by the database lock manager to determine whether a newly requested lock by one transaction can be granted concurrently with locks already held by other transactions on the same resource. A Shared (S) lock is typically used for read operations; multiple transactions can hold Shared locks on the same item simultaneously because reading data does not alter it or conflict with other reads. An Exclusive (X) lock is used for write operations (insert, update, delete). It guarantees exclusive access to the resource, meaning no other transaction can hold any lock (Shared or Exclusive) on that item concurrently. If transaction T1 holds a Shared lock on a row, and transaction T2 requests an Exclusive lock on that same row, the lock manager will consult the compatibility matrix. Since S and X are incompatible, T2's request will be blocked. T2 must wait in a queue until T1 (and any other transactions holding Shared locks on that resource) releases the lock, at which point T2 can acquire its Exclusive lock.
```sql
-- T1 acquires Shared lock
BEGIN;
SELECT * FROM products WHERE id = 42 FOR SHARE;

-- T2 requests Exclusive lock (will block until T1 commits/aborts)
BEGIN;
UPDATE products SET stock = stock - 1 WHERE id = 42;
```

**3. What are intention locks? What problem do they solve in multi-granularity locking? Explain IS, IX, and SIX, and describe the protocol for acquiring them.**
Intention locks are a mechanism used in multi-granularity locking systems to efficiently determine if a resource at a finer level of granularity (like a row) is already locked, without having to scan all the fine-grained locks. They solve the performance problem of a transaction wanting to lock an entire table having to check every single row to ensure no row is locked. Intention Shared (IS) indicates the transaction intends to acquire Shared locks at a lower level. Intention Exclusive (IX) indicates the intent to acquire Exclusive locks at a lower level. Shared Intention Exclusive (SIX) means the transaction holds a Shared lock on the entire higher-level resource (reading all of it) but intends to acquire Exclusive locks on some lower-level items. The protocol requires acquiring locks top-down: before acquiring an S or IS lock on a node (e.g., a row), a transaction must first acquire an IS or IX lock on its parent (e.g., the table). Before acquiring an X or IX or SIX lock on a node, it must acquire an IX or SIX lock on its parent.
```sql
-- Acquiring an explicit table-level intention lock in PostgreSQL
BEGIN;
LOCK TABLE employees IN ROW EXCLUSIVE MODE; -- Acts like an IX lock
-- Now safe to acquire exclusive row locks
UPDATE employees SET salary = salary * 1.1 WHERE department_id = 5;
COMMIT;
```

**4. Explain PostgreSQL MVCC. What are the `xmin` and `xmax` system columns on every row? What values do they hold before and after an UPDATE operation commits?**
PostgreSQL implements Multi-Version Concurrency Control (MVCC) to handle concurrent access without excessive locking, famously ensuring that "readers do not block writers, and writers do not block readers." Instead of modifying data in place, operations create new versions of rows. Every row in PostgreSQL contains hidden system columns, notably `xmin` and `xmax`, which track the transaction IDs (XIDs) that created and deleted the row. `xmin` stores the XID of the transaction that inserted the row. `xmax` stores the XID of the transaction that deleted or updated the row (an update is logically a delete followed by an insert). When an UPDATE occurs, the existing row's `xmax` is set to the current transaction's XID, marking it as expired, and a completely new row is inserted with its `xmin` set to the same current XID and `xmax` set to 0. Before the UPDATE commits, the new row is only visible to the transaction that created it. After the UPDATE commits, subsequent transactions will see the new row (because its `xmin` is committed) and will ignore the old row (because its `xmax` is committed).
```sql
-- Examining system columns
SELECT xmin, xmax, * FROM users WHERE id = 1;

BEGIN;
-- Current XID is assigned to xmax of old row, xmin of new row
UPDATE users SET name = 'Alice' WHERE id = 1;
-- Inside this transaction, the new row is visible.
COMMIT;
```

**5. How does PostgreSQL compute a transaction snapshot? What are `xmin`, `xmax`, and `xip` in the snapshot? Given a snapshot, state the exact rule for determining whether a tuple version is visible.**
A transaction snapshot in PostgreSQL defines exactly which transaction IDs are considered committed and which are in progress at the moment the snapshot is taken, providing an isolated view of the database. The snapshot consists of three main components: `xmin` (not to be confused with the tuple header field), `xmax`, and `xip` (transactions in progress). In a snapshot context, `xmin` is the earliest XID that is still active; any XID strictly less than `xmin` is guaranteed to be committed and visible. `xmax` is the first unassigned XID (the next one to be handed out); any XID strictly greater than or equal to `xmax` is in the future and invisible. The `xip` is an array of active transaction IDs that fall between `xmin` and `xmax`. The visibility rule for a tuple with creation XID `t_xmin` is: the tuple is visible if `t_xmin` < snapshot.`xmin` OR (`t_xmin` >= snapshot.`xmin` AND `t_xmin` < snapshot.`xmax` AND `t_xmin` NOT IN snapshot.`xip`). Furthermore, if the tuple has a deletion XID `t_xmax`, it must NOT be visible according to the exact same logic (meaning it hasn't been deleted from this snapshot's perspective).
```sql
-- You can view the current snapshot using txid_current_snapshot()
SELECT txid_current_snapshot();
-- Output format: xmin:xmax:xip_list (e.g., 100:105:102,104)
-- This means XIDs < 100 are committed, >= 105 are future, and 102, 104 are active.
```

**6. What are dead tuples in PostgreSQL? How do they accumulate from UPDATE and DELETE operations? What does VACUUM do? What is the autovacuum trigger formula?**
Dead tuples are outdated versions of rows that are no longer visible to any active transaction snapshot, but still physically occupy space on disk. Because PostgreSQL's MVCC creates a new row version for every UPDATE and marks the old version's `xmax`, and simply marks `xmax` for DELETEs, these operations leave behind the old physical records. Over time, high update/delete activity causes these dead tuples to accumulate, leading to table bloat, slower sequential scans, and larger index sizes. The `VACUUM` process scans tables to identify these dead tuples and marks their space as available for future inserts or updates, effectively recycling the space without returning it to the operating system (unless `VACUUM FULL` is used). Autovacuum is a daemon that automates this process. The autovacuum trigger formula determines when a table needs vacuuming: it triggers when the number of obsolete tuples exceeds a base threshold plus a scale factor multiplied by the table size. The default formula is: `autovacuum_vacuum_threshold (50) + autovacuum_vacuum_scale_factor (0.2) * pg_class.reltuples`.
```sql
-- Checking for dead tuples and bloat
SELECT relname, n_live_tup, n_dead_tup,
       last_autovacuum, last_autoanalyze
FROM pg_stat_user_tables
WHERE n_dead_tup > 0;

-- Manually running vacuum on a specific table
VACUUM VERBOSE my_bloated_table;
```

**7. What is the PostgreSQL transaction ID wraparound problem? What are the consequences if it is not prevented? How does VACUUM FREEZE prevent it, and how do you monitor XID age?**
PostgreSQL transaction IDs (XIDs) are 32-bit integers, meaning there are roughly 4.2 billion available values. To handle infinite transactions, XIDs wrap around, meaning XID 1 follows XID 4.2 billion. PostgreSQL uses modulo-2^32 arithmetic to determine if an XID is in the "past" or "future," splitting the space into 2 billion past and 2 billion future transactions. The wraparound problem occurs if an old row's `xmin` remains unmodified for more than 2 billion transactions; suddenly, its `xmin` will appear to be in the "future" according to the modulo arithmetic, making the row invisible and effectively causing data loss. To prevent this catastrophic consequence, PostgreSQL implements a "freeze" process. `VACUUM FREEZE` scans for old tuples and replaces their specific `xmin` with a special `FrozenTransactionId` (XID 2). This special XID is hardcoded to always be considered strictly in the past, regardless of wraparound. Autovacuum automatically triggers freeze operations before the limit is reached. You monitor XID age by querying `pg_class.relfrozenxid` and comparing it to the current XID.
```sql
-- Monitoring the age of tables to prevent wraparound
SELECT relname,
       age(relfrozenxid) AS xid_age,
       current_setting('autovacuum_freeze_max_age') AS limit
FROM pg_class
WHERE relkind = 'r'
ORDER BY xid_age DESC LIMIT 5;
```

**8. Explain the row-level lock modes in PostgreSQL: FOR UPDATE, FOR SHARE, FOR NO KEY UPDATE, FOR KEY SHARE. What does each allow and prevent? When would you use FOR NO KEY UPDATE?**
PostgreSQL provides four explicit row-level lock modes to handle fine-grained concurrency, often used in `SELECT ...` statements. `FOR UPDATE` is the most restrictive; it locks rows exclusively, preventing any concurrent updates, deletes, or other locks on those rows until the transaction ends. `FOR SHARE` acquires a shared lock, allowing concurrent reads and other `FOR SHARE` locks, but blocks any updates, deletes, or exclusive locks. `FOR NO KEY UPDATE` is slightly weaker than `FOR UPDATE`; it behaves exclusively but allows concurrent `FOR KEY SHARE` locks. It is used when modifying columns that are not part of a unique index or primary key, meaning the row's identity doesn't change. `FOR KEY SHARE` is the weakest lock, often acquired automatically when verifying foreign key constraints; it allows concurrent reads and non-key updates (`FOR NO KEY UPDATE`), but blocks any changes to the key columns. You would use `FOR NO KEY UPDATE` explicitly when you intend to update non-indexed payload columns of a row and want to maximize concurrency by not blocking other transactions that might merely be checking foreign key constraints against that row.
```sql
-- T1: Updating a non-key column
BEGIN;
SELECT * FROM users WHERE id = 1 FOR NO KEY UPDATE;
UPDATE users SET last_login = now() WHERE id = 1;
-- T2 (concurrent): Can still insert a child record needing this user as FK
-- INSERT INTO posts (user_id, body) VALUES (1, 'hello'); -- Acquires FOR KEY SHARE, does not block!
COMMIT;
```

**9. What is `SELECT FOR UPDATE SKIP LOCKED`? Implement a reliable concurrent job queue in PostgreSQL using this pattern. Why is this superior to polling with status='pending'?**
`SELECT FOR UPDATE SKIP LOCKED` is a powerful concurrency feature that attempts to acquire row-level exclusive locks but, instead of blocking when it encounters an already-locked row, it simply skips that row and moves to the next available one. This fundamentally solves the problem of implementing highly concurrent task queues in a relational database. Traditional approaches using `status = 'pending'` and polling suffer from race conditions or severe contention: multiple workers will try to grab the same pending row, blocking each other or causing deadlocks. With `SKIP LOCKED`, dozens of concurrent worker processes can query the exact same table simultaneously; each worker will instantly grab the next available, unlocked row without waiting for or interfering with other workers. This provides massive throughput and reliability without needing external message brokers.
```sql
-- Implementing a concurrent job queue worker
BEGIN;
WITH next_task AS (
  SELECT id FROM jobs
  WHERE status = 'pending'
  ORDER BY created_at ASC
  FOR UPDATE SKIP LOCKED
  LIMIT 1
)
UPDATE jobs
SET status = 'processing',
    started_at = now()
WHERE id = (SELECT id FROM next_task)
RETURNING *;
-- Worker processes the job here...
COMMIT; -- Or UPDATE status='completed' before commit
```

**10. What is a deadlock? How does PostgreSQL detect it? What SQLSTATE does a deadlock produce? How should application code handle it? Give the canonical prevention technique with code.**
A deadlock is a situation in which two or more transactions hold locks that the other transactions need, resulting in a circular dependency where neither can proceed. PostgreSQL detects deadlocks automatically using a background process called the deadlock detector. When a transaction waits on a lock for more than `deadlock_timeout` (default 1 second), the detector traverses the wait-for graph. If it finds a cycle, it forces one of the transactions to abort, rolling back its changes and releasing its locks to break the deadlock. The aborted transaction receives a specific error with `SQLSTATE = '40P01'`. Application code should handle this by implementing retry logic: catching the specific deadlock exception and safely re-executing the entire transaction block from the beginning. The canonical prevention technique is to ensure that all transactions acquire locks in the exact same consistent order across the entire application.
```sql
-- Canonical prevention: Always lock in primary key order
-- Bad: T1 locks 1 then 2; T2 locks 2 then 1 (Deadlock!)
-- Good: Both transactions sort the IDs before locking
BEGIN;
-- In application code, sort the array of IDs before executing this query:
SELECT * FROM accounts 
WHERE id IN (1, 2, 5, 42) -- sorted
ORDER BY id 
FOR UPDATE;
-- Proceed with updates
COMMIT;
```

**11. What is an advisory lock in PostgreSQL? What is the difference between a session-level advisory lock and a transaction-level advisory lock? Give two real-world use cases.**
Advisory locks are application-defined, arbitrary locks managed by the PostgreSQL server. Unlike standard locks tied to tables or rows, advisory locks are associated with a 64-bit integer identifier chosen by the developer. They are fast, avoid table bloat, and bypass MVCC overhead. A session-level advisory lock (`pg_advisory_lock`) is held by the database connection until explicitly released or the connection drops; it persists across transaction boundaries. A transaction-level advisory lock (`pg_advisory_xact_lock`) behaves like standard locks: it is automatically released at the end of the current transaction, making it immune to connection-pooling leak issues. Two real-world use cases include: 1) Preventing concurrent executions of a scheduled cron job (the script acquires a well-known advisory lock ID on startup; if it fails to acquire, another instance is running). 2) Throttling or synchronizing access to external rate-limited APIs, where the lock ID represents the API resource rather than database rows.
```sql
-- Transaction-level advisory lock (automatically released on commit)
BEGIN;
-- Lock ID 12345 represents an external API constraint
SELECT pg_advisory_xact_lock(12345);
-- Perform DB updates and call external API...
COMMIT;

-- Session-level advisory lock (must explicitly release)
SELECT pg_try_advisory_lock(999); -- Returns true if acquired
-- Do work...
SELECT pg_advisory_unlock(999);
```

**12. What is Row-Level Security (RLS) in PostgreSQL? Write a policy that implements multi-tenant data isolation using a session variable. What does FORCE ROW LEVEL SECURITY do?**
Row-Level Security (RLS) is a security feature that restricts which rows a database user can `SELECT`, `UPDATE`, `DELETE`, or `INSERT` based on evaluating a boolean SQL expression, effectively enforcing security at the data layer rather than the application layer. When enabled, the database automatically appends the policy conditions to every query. A common use case is multi-tenant isolation, ensuring users can only access their own tenant's data. By setting a session variable (e.g., via `current_setting`), the policy can dynamically filter rows. `FORCE ROW LEVEL SECURITY` is a table property that ensures RLS policies are applied even for table owners. Normally, the owner of a table bypasses RLS policies, which can be dangerous if the application connects using the owner role. Forcing RLS ensures the policy is universally applied.
```sql
-- Enable RLS
ALTER TABLE tenant_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_data FORCE ROW LEVEL SECURITY;

-- Create policy using a session variable
CREATE POLICY tenant_isolation_policy ON tenant_data
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant')::integer);

-- Application connection logic:
-- SET app.current_tenant = '42';
-- SELECT * FROM tenant_data; -- implicitly adds WHERE tenant_id = 42
```

**13. What is connection pooling and why is it necessary for PostgreSQL? Compare PgBouncer's session, transaction, and statement pool modes. What features break in transaction pool mode?**
Connection pooling is a middleware layer that maintains a cache of active database connections, reusing them for incoming application requests instead of opening and closing a new connection per request. In PostgreSQL, establishing a new connection is very expensive because it requires forking a new OS process and allocating substantial memory. High connection churn destroys throughput. PgBouncer is a popular pooler offering three modes. In 'session' mode, an application gets a dedicated backend connection for the lifetime of its connection to PgBouncer; this supports all features but requires as many backend connections as active clients. In 'transaction' mode, the backend connection is returned to the pool the moment the transaction commits; this allows thousands of clients to share a few dozen backend connections. In 'statement' mode, connections are swapped after every statement (rarely used because it breaks multi-statement transactions). Transaction mode breaks session-level features because consecutive transactions from one client might land on different backend processes. Broken features include: session-level advisory locks, PREPARE statements without pooler support, SET/RESET session variables, and temporary tables.
```ini
-- Example pgbouncer.ini snippet
[databases]
mydb = host=127.0.0.1 port=5432 dbname=mydb

[pgbouncer]
listen_port = 6432
listen_addr = *
auth_type = md5
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
```

**14. What is the visibility map in PostgreSQL? How does it enable index-only scans? What process keeps the visibility map updated?**
The visibility map is a compact bitmap data structure associated with every table that tracks which data blocks (pages) contain only tuples that are known to be visible to all active transactions. Each bit corresponds to a page; if the bit is set, it means every single row on that page is fully committed and not currently being updated or deleted. This map is the crucial enabler for index-only scans. When an index-only scan fetches a row from the index, it normally must visit the actual table (the heap) to check MVCC headers (`xmin`/`xmax`) to ensure the row isn't deleted or uncommitted. However, if the visibility map indicates the target page is fully visible, PostgreSQL can completely skip the expensive heap fetch and return the data directly from the index. The visibility map is updated and maintained primarily by the VACUUM process. When VACUUM scans a page and determines all tuples are visible to everyone, it sets the corresponding bit in the map.
```sql
-- Checking index-only scan usage and visibility map effectiveness
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, name FROM users WHERE id > 1000;
-- Look for "Index Only Scan" and "Heap Fetches: 0"
-- If Heap Fetches is high, the visibility map is outdated, requiring a VACUUM.
VACUUM users;
```

**15. Explain the difference between optimistic concurrency control (OCC) implemented in application code with a version column vs PostgreSQL's built-in MVCC. When would you implement application-level OCC on top of PostgreSQL?**
PostgreSQL's built-in MVCC handles concurrent reads and writes transparently at the row level, ensuring isolation and consistency during a single database transaction. However, MVCC locks are held only for the duration of the database transaction. Optimistic Concurrency Control (OCC) implemented at the application level involves adding a `version` or `updated_at` column to a table. It is used to protect data across "long business transactions" that span multiple HTTP requests, where holding a database lock is impossible. For example, a user fetches a record (HTTP GET), edits it in a web form for 10 minutes, and submits it (HTTP POST). PostgreSQL MVCC cannot protect against another user modifying the record during those 10 minutes. Application-level OCC solves this: the application reads the record and its `version=1`. Upon submission, the update statement explicitly checks the version: `UPDATE table SET ..., version = 2 WHERE id = X AND version = 1`. If another user modified it, the version is now 2, the UPDATE affects 0 rows, and the application throws a "stale data" or "concurrent modification" error. You implement OCC on top of PostgreSQL when dealing with disconnected clients or long-running user interactions.
```sql
-- Application-level Optimistic Concurrency Control
-- Step 1: Read data and version
SELECT id, status, version FROM tickets WHERE id = 42; -- Assume returns version 5

-- User spends 5 minutes looking at the screen, then clicks "Resolve"

-- Step 2: Attempt update requiring the original version
UPDATE tickets 
SET status = 'resolved', version = version + 1 
WHERE id = 42 AND version = 5;

-- The application must check the number of rows affected. 
-- If 0, someone else modified the ticket; return an error to the user.
```
