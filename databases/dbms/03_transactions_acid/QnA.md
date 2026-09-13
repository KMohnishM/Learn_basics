# Database Transactions QnA

### 1. What is a database transaction and why is it necessary?
1. A database transaction represents a single, logical unit of work.
2. It groups multiple SQL operations into one atomic execution block.
3. Transactions are necessary to maintain database integrity during complex updates.
4. Without them, a system crash midway through an operation leaves data corrupted.
5. They provide isolation, ensuring concurrent users do not see partial data.
6. A classic example is a financial transfer between two accounts.
7. Both the debit and the credit must succeed, or both must fail.
8. Transactions are started explicitly using the BEGIN command.
9. They are completed using the COMMIT command, making changes permanent.
10. If an error occurs, the ROLLBACK command reverts all changes.
11. Savepoints can be used for partial rollbacks within a transaction.
12. Ultimately, they are the foundation of reliable relational database management systems.
13. They are implemented using write-ahead logging and MVCC in PostgreSQL.

### 2. How do ACID properties guarantee database reliability?
1. ACID stands for Atomicity, Consistency, Isolation, and Durability.
2. Atomicity guarantees that transactions are all-or-nothing operations.
3. If any part of a transaction fails, the entire transaction fails safely.
4. Consistency ensures the database transitions from one valid state to another.
5. It enforces all constraints, foreign keys, and triggers defined in the schema.
6. Isolation ensures that concurrent transactions do not negatively impact each other.
7. It defines how changes made by one operation become visible to others.
8. Durability guarantees that committed data is never lost, even during power failures.
9. This is typically achieved by flushing transaction logs to persistent disk storage.
10. Together, these properties ensure trust in the database's data integrity.
11. Applications rely on these guarantees to process critical business logic.
12. PostgreSQL is designed to strictly adhere to these properties by default.
13. Understanding ACID is essential for designing robust backend systems.

### 3. What is a Dirty Read and how does PostgreSQL prevent it?
1. A dirty read is a concurrency anomaly involving uncommitted data.
2. It happens when Transaction A reads data written by Transaction B, before B commits.
3. If Transaction B later rolls back, Transaction A has read phantom data.
4. This can lead to incorrect calculations and severe data inconsistencies.
5. In the SQL standard, this is allowed at the Read Uncommitted isolation level.
6. However, PostgreSQL implements Multiversion Concurrency Control (MVCC).
7. Under MVCC, readers only ever see data that was committed before their snapshot.
8. Therefore, PostgreSQL strictly prevents dirty reads at all isolation levels.
9. Even if you explicitly request Read Uncommitted, PostgreSQL behaves as Read Committed.
10. This architectural decision vastly simplifies application development.
11. Developers do not need to worry about reading partially updated rows.
12. It provides a strong baseline level of consistency without sacrificing much performance.
13. Dirty reads are effectively impossible in standard PostgreSQL operations.

### 4. Explain the Non-Repeatable Read anomaly.
1. A non-repeatable read occurs within the context of a single transaction.
2. It happens when a transaction reads the exact same row twice and gets different results.
3. This is caused by another concurrent transaction modifying and committing that row.
4. For example, Transaction A reads an account balance of 100.
5. Transaction B updates the balance to 200 and commits successfully.
6. Transaction A reads the balance again and sees 200, which is unexpected.
7. This anomaly is allowed in the default Read Committed isolation level.
8. To prevent it, the database must be set to Repeatable Read or Serializable.
9. In Repeatable Read, the transaction takes a single snapshot for its entire duration.
10. Thus, subsequent reads will always return the data as it was at the snapshot time.
11. Non-repeatable reads can cause issues in report generation or complex calculations.
12. They are a common source of subtle bugs in highly concurrent applications.
13. Developers must explicitly choose stricter isolation if repeatability is required.

### 5. What is a Phantom Read and how does it differ from a Non-Repeatable Read?
1. A phantom read is a concurrency anomaly that affects sets of rows.
2. It happens when a query is executed twice, and the number of rows changes.
3. This is due to another transaction inserting or deleting rows that match the query's WHERE clause.
4. Non-repeatable reads deal with modifications to existing, previously read rows.
5. Phantom reads deal with new rows appearing or existing rows disappearing.
6. For example, Transaction A queries for all active employees and gets 10 rows.
7. Transaction B inserts a new active employee and commits.
8. Transaction A runs the same query again and gets 11 rows.
9. In standard SQL, phantom reads are allowed in the Repeatable Read isolation level.
10. However, PostgreSQL's MVCC implementation prevents phantom reads even at Repeatable Read.
11. PostgreSQL's snapshots cover the entire database state, not just locked rows.
12. To encounter a phantom read in standard systems, one must avoid Serializable level.
13. In PostgreSQL, you must use Read Committed to see phantom reads.

### 6. Describe the Write Skew anomaly and when it occurs.
1. Write skew is a complex anomaly that occurs under specific concurrent conditions.
2. It happens when two transactions read overlapping data but write to disjoint sets.
3. The individual writes are valid, but together they violate a business constraint.
4. For example, a system requires at least one doctor to be on call at all times.
5. Alice and Bob are currently on call.
6. Transaction A checks if two doctors are on call, sees yes, and removes Alice.
7. Transaction B concurrently checks, sees yes, and removes Bob.
8. Both transactions commit successfully, leaving zero doctors on call.
9. Write skew is not prevented by the Repeatable Read isolation level.
10. It requires the strict Serializable isolation level to be prevented automatically.
11. Alternatively, explicit row locking (SELECT FOR UPDATE) can be used to prevent it.
12. Write skew represents a failure of consistency due to interleaved logic.
13. It is a critical concern in distributed systems and complex state machines.

### 7. How does the Lost Update anomaly happen?
1. A lost update occurs when two transactions read and update the same row concurrently.
2. Without proper locking or isolation, one transaction's changes overwrite the other's.
3. For example, Transaction A and Transaction B both read a balance of 100.
4. Transaction A adds 50 and updates the row to 150.
5. Transaction B adds 20 and updates the row to 120.
6. Transaction B's commit overwrites Transaction A's commit.
7. The 50 added by Transaction A is permanently lost.
8. This happens because the updates were based on stale read data.
9. Lost updates can be prevented by using SELECT FOR UPDATE to lock the row.
10. They are also prevented automatically by the Repeatable Read isolation level.
11. In Repeatable Read, the second transaction will fail with a serialization error.
12. The application must then catch the error and retry the transaction.
13. Understanding lost updates is crucial for applications that increment or decrement values.

### 8. What is the Read Committed isolation level?
1. Read Committed is the default isolation level in PostgreSQL and many other databases.
2. It guarantees that a transaction only sees data that has been committed.
3. It completely prevents the dirty read anomaly by design.
4. However, it does not prevent non-repeatable reads or phantom reads.
5. Each individual SQL statement within the transaction gets its own fresh snapshot.
6. This means a SELECT statement sees the database as of the instant it began executing.
7. If another transaction commits changes between two SELECTs, the second SELECT sees them.
8. This level offers an excellent balance between data consistency and high concurrency.
9. It rarely results in serialization errors, simplifying application logic.
10. Most web applications operate perfectly well at the Read Committed level.
11. When stricter consistency is needed, developers use explicit locking strategies.
12. It is the pragmatic choice for general-purpose transactional workloads.
13. Understanding its limitations is key to avoiding race conditions in edge cases.

### 9. How does the Repeatable Read isolation level work in PostgreSQL?
1. The Repeatable Read isolation level provides a stricter consistency model.
2. It guarantees that a transaction sees a consistent snapshot of the entire database.
3. This snapshot is established at the start of the first query within the transaction.
4. As a result, non-repeatable reads are completely prevented.
5. In PostgreSQL, this level also prevents phantom reads due to its MVCC architecture.
6. All reads within the transaction will return identical results, regardless of concurrent commits.
7. However, this level introduces the possibility of serialization failures.
8. If the transaction attempts to update a row modified by another concurrent transaction, it will abort.
9. PostgreSQL will throw a "could not serialize access due to concurrent update" error.
10. Applications using Repeatable Read must be programmed to handle these retries.
11. It is ideal for long-running reports or complex multi-step calculations.
12. It ensures that data remains perfectly consistent throughout the transaction's lifespan.
13. It does not prevent write skew, which requires the Serializable level.

### 10. Explain the Serializable isolation level.
1. Serializable is the strictest transaction isolation level defined by the SQL standard.
2. It guarantees that the outcome of concurrent transactions is exactly as if they ran sequentially.
3. This means it prevents all concurrency anomalies, including dirty reads, non-repeatable reads, phantoms, and write skew.
4. PostgreSQL implements this using Serializable Snapshot Isolation (SSI).
5. SSI monitors transactions for dangerous patterns of overlapping reads and writes.
6. When it detects a pattern that could lead to an anomaly, it safely aborts one transaction.
7. This provides the highest level of data integrity possible.
8. However, it comes with a significant performance cost and high rate of transaction aborts.
9. Applications must be rigorously designed to catch serialization errors and retry automatically.
10. It requires careful tuning and understanding of workload patterns to be effective.
11. It is typically used only for the most critical financial or state-management operations.
12. For most applications, Repeatable Read with explicit locking is a more practical approach.
13. It represents the pinnacle of ACID isolation guarantees.

### 11. What is SELECT FOR UPDATE and when is it used?
1. SELECT FOR UPDATE is a SQL command used for explicit pessimistic locking.
2. It locks the rows returned by the SELECT query, preventing other transactions from modifying them.
3. It acts as an exclusive row-level lock.
4. If another transaction tries to UPDATE, DELETE, or SELECT FOR UPDATE those rows, it will block.
5. The block persists until the first transaction either commits or rolls back.
6. It is primarily used to prevent lost updates in Read Committed isolation.
7. By locking the row before reading its value, you ensure no one else can change it.
8. This guarantees that subsequent updates within the transaction are based on current data.
9. PostgreSQL offers variations like FOR NO KEY UPDATE and FOR SHARE for finer control.
10. These variations reduce lock contention by allowing certain non-conflicting operations.
11. Developers must use SELECT FOR UPDATE carefully to avoid performance bottlenecks.
12. Overuse can lead to deadlocks and severe concurrency limitations.
13. It is a powerful tool for controlling critical sections of application logic.

### 12. How do Deadlocks occur in a relational database?
1. A deadlock is a state where two or more transactions are permanently blocked.
2. This occurs because each transaction holds a lock that the other transaction needs.
3. For example, Transaction A locks Row 1 and needs Row 2.
4. Concurrently, Transaction B locks Row 2 and needs Row 1.
5. Neither transaction can proceed, creating a cyclical dependency.
6. Without external intervention, these transactions would wait indefinitely.
7. Deadlocks are a classic problem in concurrent systems using pessimistic locking.
8. They can occur with both row-level locks and table-level locks.
9. Complex transactions that update multiple tables in varying orders are highly susceptible.
10. Application design flaws are the root cause of almost all deadlocks.
11. They degrade system performance by tying up connections and resources.
12. Understanding how locks are acquired is essential for deadlock prevention.
13. Deadlocks cannot occur in purely optimistic concurrency control models.

### 13. How does PostgreSQL detect and resolve Deadlocks?
1. PostgreSQL has a built-in, automated deadlock detection mechanism.
2. It does not check for deadlocks instantly upon every lock wait, as this is expensive.
3. Instead, it waits for a configured duration, defined by the deadlock_timeout setting.
4. The default deadlock_timeout is typically one second.
5. If a transaction waits for a lock longer than this timeout, the detector activates.
6. It analyzes the wait-for graph of all currently blocked transactions.
7. If it finds a cycle in this graph, a deadlock is confirmed.
8. To resolve the deadlock, PostgreSQL forcefully aborts one of the involved transactions.
9. The aborted transaction receives an ERROR: deadlock detected message.
10. This releases its locks, allowing the other blocked transaction(s) to proceed.
11. The application must catch this error and retry the aborted transaction.
12. Monitoring server logs for deadlock errors is crucial for identifying application bugs.
13. Frequent deadlocks indicate a serious design flaw requiring immediate attention.

### 14. What are strategies to prevent Deadlocks?
1. The most effective strategy to prevent deadlocks is consistent lock ordering.
2. Applications should always acquire locks on multiple resources in the exact same sequence.
3. If all transactions lock Table A before Table B, cycles cannot form.
4. Another strategy is to keep transactions as short and fast as possible.
5. Shorter transactions hold locks for less time, reducing the window for conflict.
6. Avoid performing slow tasks, like network calls or user input, while holding locks.
7. Use the lowest acceptable isolation level (e.g., Read Committed) to minimize implicit locks.
8. Utilize finer-grained locking, such as FOR NO KEY UPDATE, when full exclusive locks aren't needed.
9. Consider optimistic concurrency control using version numbers for high-contention rows.
10. Ensure batch updates sort their input data logically before applying changes.
11. Thoroughly review complex SQL procedures for potential lock escalation issues.
12. Implement comprehensive testing under high concurrency to identify potential deadlocks early.
13. Prevention is always vastly superior to relying on the database's deadlock detector.

### 15. Explain the difference between Optimistic and Pessimistic Concurrency Control.
1. Pessimistic concurrency control assumes that conflicts between transactions are likely.
2. It prevents conflicts by eagerly acquiring locks on data before reading or modifying it.
3. This ensures strict consistency but can severely limit concurrency and lead to deadlocks.
4. SELECT FOR UPDATE is the classic example of pessimistic control.
5. Optimistic concurrency control assumes that conflicts are rare.
6. It does not lock rows; instead, it verifies data hasn't changed before updating.
7. This is usually implemented by adding a version number or timestamp column to the table.
8. The update query includes the expected version in its WHERE clause.
9. If no rows are updated, it means another transaction modified the data concurrently.
10. The application must then abort and retry the entire logical operation.
11. Optimistic control provides much higher concurrency and eliminates database-level deadlocks.
12. However, it shifts the burden of conflict resolution entirely to the application layer.
13. The choice between them depends entirely on the expected contention rates of the specific workload.
