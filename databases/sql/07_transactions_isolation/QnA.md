# Q&A: Transactions and Isolation

**1. What are the four ACID properties? Explain Isolation specifically.**
The four ACID properties are Atomicity, Consistency, Isolation, and Durability.
*   **Atomicity** guarantees that a transaction is an all-or-nothing proposition; partial updates never happen.
*   **Consistency** ensures that the database transitions from one valid state to another, enforcing all constraints and triggers.
*   **Durability** guarantees that once a transaction commits, the changes are permanently saved and will survive a system crash.
*   **Isolation** specifically dictates how concurrent transactions interact. It ensures that the intermediate states of a transaction are invisible to other transactions, preventing them from interfering with each other. Different isolation levels provide different trade-offs between strict isolation and performance/concurrency.

**2. What is a dirty read? At which isolation level is it prevented?**
A dirty read occurs when Transaction A reads data that has been modified by a concurrent Transaction B, but Transaction B has not yet committed. If Transaction B subsequently rolls back its changes, Transaction A has based its logic on data that effectively never existed in the database.
Dirty reads are allowed at the `READ UNCOMMITTED` isolation level. They are prevented at `READ COMMITTED`, `REPEATABLE READ`, and `SERIALIZABLE` levels. Note that in PostgreSQL, MVCC makes dirty reads impossible even if you explicitly request `READ UNCOMMITTED`.

**3. What is the difference between a non-repeatable read and a phantom read?**
*   **Non-repeatable read** applies to a specific row. It happens when a transaction reads a row, another transaction updates or deletes that *same row* and commits, and then the first transaction reads the row again and sees the new value (or finds the row gone).
*   **Phantom read** applies to a set of rows matching a condition. It happens when a transaction executes a query (e.g., `WHERE status = 'active'`), another transaction inserts a *new row* that matches the condition and commits, and then the first transaction executes the query again and sees the new "phantom" row in its result set.

**4. What is write skew? Which isolation level prevents it?**
Write skew occurs when two concurrent transactions read disjoint sets of overlapping data, make business logic decisions based on those reads, and then modify different parts of the data. Because they modify different rows, standard row-level locking or basic MVCC doesn't stop them, resulting in a violation of a business rule. For example, two doctors on call; both see that there are 2 doctors on call, so both update the database to take themselves off call simultaneously, leaving 0 doctors on call.
Write skew is only prevented by the **SERIALIZABLE** isolation level.

**5. How does PostgreSQL implement MVCC? What are its advantages over lock-based isolation?**
PostgreSQL implements Multi-Version Concurrency Control (MVCC) by keeping multiple versions of a row in the table when updates or deletes occur. When a transaction starts, it receives a "snapshot" of the database state. It only reads row versions that were committed before that snapshot was taken.
The primary advantage over strict lock-based isolation (like older databases used) is that **readers do not block writers, and writers do not block readers**. This vastly improves concurrency and read performance, as long `SELECT` queries don't stop applications from updating data.

**6. What is the difference between READ COMMITTED and REPEATABLE READ in PostgreSQL?**
*   **READ COMMITTED (Default)**: Each individual statement within the transaction takes a new snapshot when it begins executing. If `SELECT * FROM table` is run twice in the same transaction, and another transaction commits an update in between, the second `SELECT` will see the new data.
*   **REPEATABLE READ**: The transaction takes a single snapshot when the *first non-transaction-control statement* is executed. Every subsequent query in that transaction sees the exact same snapshot, guaranteeing that data read early in the transaction won't change if read later, even if other transactions commit.

**7. When would you use `SELECT ... FOR UPDATE`? What does it do?**
You use `SELECT ... FOR UPDATE` when you need to read a row and ensure nobody else can modify it before you finish updating it yourself. This is the classic way to prevent the **Lost Update** anomaly.
It places an exclusive row-level lock on the returned rows. If another transaction tries to `UPDATE`, `DELETE`, or `SELECT ... FOR UPDATE` those same rows, it will be blocked and forced to wait until your transaction commits or rolls back.

**8. What is `SELECT ... FOR UPDATE SKIP LOCKED` used for? Give a real-world example.**
`SKIP LOCKED` attempts to lock rows for update, but instead of waiting if a row is already locked by another transaction, it immediately skips that row and continues searching for unlocked rows.
**Real-world example**: Implementing a reliable job queue or background worker system in PostgreSQL. Multiple worker processes can constantly query `SELECT * FROM jobs WHERE status = 'pending' LIMIT 1 FOR UPDATE SKIP LOCKED`. They will gracefully grab independent jobs without blocking each other, ensuring high throughput.

**9. How do deadlocks occur? How does PostgreSQL handle them?**
A deadlock occurs when two or more transactions are waiting for locks held by each other, forming a cycle. Neither transaction can proceed because it is blocked by the other.
PostgreSQL handles them via an automatic deadlock detector. Every `deadlock_timeout` (default 1s), it checks for wait cycles. If it finds one, it chooses one transaction as the "victim", aborts it with an `ERROR: deadlock detected`, and allows the other transaction(s) to proceed.

**10. How do you prevent deadlocks in application code?**
The most effective way to prevent deadlocks is to ensure all application code **acquires locks in a consistent, deterministic order**.
For example, if you need to update a `customer` and an `order`, always lock (update) the `customer` row first, then the `order` row. If every transaction follows this rule, one transaction will simply queue up behind the other, preventing cycles from forming.

**11. What is a SAVEPOINT? Give a use case where it's necessary.**
A `SAVEPOINT` creates a marker within an active transaction. You can use `ROLLBACK TO SAVEPOINT` to undo only the work done since that marker, without abandoning the entire transaction.
**Use case**: Bulk importing data where a few rows might fail validation constraints. You can set a savepoint before inserting each row. If the insert throws an error, you rollback to the savepoint (rescuing the transaction state), log the error, and continue processing the rest of the batch.

**12. What is the default isolation level in PostgreSQL? In MySQL?**
*   **PostgreSQL**: `READ COMMITTED`.
*   **MySQL (InnoDB)**: `REPEATABLE READ`. (This is an important distinction when migrating applications between the two systems).

**13. How do long-running transactions cause problems beyond just holding locks?**
In an MVCC system like PostgreSQL, long-running transactions prevent the database from cleaning up old row versions (dead tuples) that have been modified by other transactions since the long-running transaction started. Because the old transaction *might* need to look at them, the autovacuum process cannot delete them. This leads to **table bloat** (wasted disk space and slower sequential scans). Furthermore, they can cause transaction ID wraparound issues on heavily loaded systems.

**14. What is the difference between ROLLBACK and ROLLBACK TO SAVEPOINT?**
*   **`ROLLBACK`**: Aborts the *entire* transaction. All changes made since `BEGIN` are discarded, and the transaction is closed.
*   **`ROLLBACK TO SAVEPOINT <name>`**: Aborts only the changes made since the specific savepoint was created. The transaction remains open and active, allowing you to execute further statements and eventually issue a `COMMIT`.

**15. Describe an implementation of a rate limiter using database transactions and SELECT FOR UPDATE.**
To implement a simple API rate limiter (e.g., 5 requests per minute):
1.  Create a table: `rate_limits (user_id, token_count, last_updated)`.
2.  Begin transaction.
3.  `SELECT token_count, last_updated FROM rate_limits WHERE user_id = $1 FOR UPDATE;`
4.  In application code: calculate how many tokens to add based on the time difference between `now()` and `last_updated`. Add them to `token_count` (capped at max 5).
5.  If `token_count` > 0, deduct 1, set `last_updated = now()`, and `UPDATE` the row. Allow the request.
6.  If `token_count` == 0, `UPDATE` `last_updated` and deny the request.
7.  Commit the transaction. The `FOR UPDATE` prevents race conditions where multiple rapid requests read the same initial token count.
