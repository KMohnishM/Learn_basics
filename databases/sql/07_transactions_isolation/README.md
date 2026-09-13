# Module 7: Transactions and Isolation

## 1. What is a Transaction?

A transaction is a single logical unit of work performed within a database system. It consists of one or more SQL statements executed as a whole. Transactions ensure that either all the statements within the transaction are successfully executed, or none of them are. This prevents the database from being left in an inconsistent state due to partial updates, software crashes, or hardware failures.

### Basic Transaction Control Commands

*   **`BEGIN` or `START TRANSACTION`**: Initiates a new transaction.
*   **`COMMIT`**: Saves all changes made during the current transaction, making them permanent and visible to other transactions.
*   **`ROLLBACK`**: Discards all changes made during the current transaction, reverting the database to its state before the transaction began.

**Example: A Simple Bank Transfer**
While we have an `orders` and `customers` schema, let's illustrate a classic transfer first, then adapt to our schema. Suppose an employee gets a bonus deducted from a departmental budget.

```sql
BEGIN;

-- Deduct 5000 from the Marketing department's budget (assuming budget column exists)
-- UPDATE departments SET budget = budget - 5000 WHERE dept_name = 'Marketing';

-- Give a $5000 raise to employee 101
UPDATE employees 
SET salary = salary + 5000 
WHERE emp_id = 101 AND dept_id = (SELECT dept_id FROM departments WHERE dept_name = 'Marketing');

-- If everything above succeeds
COMMIT;
```

If an error occurred after the first `UPDATE` (e.g., the server crashed, or a constraint was violated), a `ROLLBACK` would be issued (either explicitly by the application or implicitly by the database upon connection loss/crash), and the department's budget deduction would be undone.

---

## 2. SAVEPOINT: Nested Rollback Points

A `SAVEPOINT` allows you to set a marker within a transaction. If an error occurs after a savepoint, you can rollback to that specific point without rolling back the entire transaction.

*   **`SAVEPOINT savepoint_name`**: Creates a savepoint.
*   **`ROLLBACK TO SAVEPOINT savepoint_name`**: Undoes changes made since the savepoint was created. The transaction remains active.
*   **`RELEASE SAVEPOINT savepoint_name`**: Destroys the savepoint. It does not commit the changes, but you can no longer rollback to it.

**Example:**

```sql
BEGIN;

INSERT INTO customers (customer_id, name, email, country, created_at)
VALUES (1, 'Alice Smith', 'alice@example.com', 'USA', CURRENT_TIMESTAMP);

SAVEPOINT after_alice;

-- Try inserting a duplicate customer_id intentionally to cause an error
INSERT INTO customers (customer_id, name, email, country, created_at)
VALUES (1, 'Bob Jones', 'bob@example.com', 'UK', CURRENT_TIMESTAMP);
-- ERROR: duplicate key value violates unique constraint "customers_pkey"

-- The transaction is now in an aborted state. We cannot commit.
-- However, we can rollback to our savepoint to rescue the first insert.
ROLLBACK TO SAVEPOINT after_alice;

-- Now we can continue with other operations
INSERT INTO customers (customer_id, name, email, country, created_at)
VALUES (2, 'Charlie Brown', 'charlie@example.com', 'Canada', CURRENT_TIMESTAMP);

COMMIT;
```
After this transaction, only Alice and Charlie exist in the database.

---

## 3. ACID Properties Deep Dive

Transactions guarantee the ACID properties, which are fundamental to relational databases.

### 3.1. Atomicity (All-or-Nothing)
Atomicity guarantees that a transaction is treated as a single, indivisible unit. Either all its operations succeed, or none do. If a crash occurs mid-transaction, the database uses its Write-Ahead Log (WAL) to ensure partial changes are not persisted upon recovery.

**Crash Recovery with WAL:**
PostgreSQL (and most modern RDBMS) uses a Write-Ahead Log. Before any data file (table/index) is modified on disk, the intended change is written to the WAL and flushed to persistent storage. If the system crashes, upon restart, the database replays the WAL. It will redo committed transactions that didn't make it to the data files, and it will undo (rollback) any uncommitted transactions found in the data files.

### 3.2. Consistency
Consistency ensures that a transaction takes the database from one valid state to another valid state, maintaining all defined rules, constraints, cascades, and triggers.

**Constraint Enforcement Examples:**
*   **Foreign Keys**: Ensuring a department exists before assigning an employee to it.
*   **Check Constraints**: Ensuring a product price is always greater than 0.
*   **Unique Constraints**: Ensuring no two customers have the same email address.

```sql
-- This will fail and rollback if the constraint is violated
ALTER TABLE products ADD CONSTRAINT check_positive_price CHECK (price > 0);

BEGIN;
UPDATE products SET price = -10 WHERE product_id = 1; 
-- ERROR: new row for relation "products" violates check constraint "check_positive_price"
ROLLBACK;
```

### 3.3. Isolation
Isolation dictates how concurrent transactions interact and how visible their uncommitted changes are to each other. Because multiple transactions often run simultaneously, strict isolation is required to prevent them from interfering with one another. However, higher isolation levels reduce concurrency, so databases offer different levels (discussed in Section 4).

### 3.4. Durability
Durability guarantees that once a transaction has been committed, its changes will survive system failures (e.g., power loss, crashes). This is primarily achieved by ensuring that the WAL records for the transaction are physically flushed to disk (using `fsync` or similar OS-level commands) before the database acknowledges the `COMMIT` as successful to the client.

---

## 4. Concurrent Transaction Anomalies

When transactions run concurrently without adequate isolation, various data anomalies can occur.

### 4.1. Dirty Read
A dirty read occurs when Transaction A reads data that has been modified by Transaction B, but Transaction B has not yet committed. If Transaction B later rolls back, Transaction A is left operating on data that technically never existed.

**Example Scenario:**
*   **T1 (Transaction 1)**: `UPDATE employees SET salary = salary + 1000 WHERE emp_id = 1;` (Uncommitted)
*   **T2 (Transaction 2)**: `SELECT salary FROM employees WHERE emp_id = 1;` (Reads the new, uncommitted salary)
*   **T1**: `ROLLBACK;` (The salary was never actually increased)
*   **T2**: Uses the dirty data for some calculation, leading to an incorrect result.

### 4.2. Non-repeatable Read
A non-repeatable read occurs when a transaction reads the same row twice during its lifetime and gets different values because another transaction modified and committed the row in between the reads.

**Example Scenario:**
*   **T1**: `SELECT price FROM products WHERE product_id = 42;` (Returns $100)
*   **T2**: `UPDATE products SET price = $150 WHERE product_id = 42; COMMIT;`
*   **T1**: `SELECT price FROM products WHERE product_id = 42;` (Returns $150 - different from the first read)

### 4.3. Phantom Read
A phantom read occurs when a transaction executes a query returning a set of rows matching a search condition, and a second transaction inserts or deletes rows matching that condition. If the first transaction repeats the query, it sees a different set of rows (the "phantoms").

**Example Scenario:**
*   **T1**: `SELECT COUNT(*) FROM employees WHERE dept_id = 5;` (Returns 10)
*   **T2**: `INSERT INTO employees (emp_id, name, dept_id, salary) VALUES (99, 'Eve', 5, 60000); COMMIT;`
*   **T1**: `SELECT COUNT(*) FROM employees WHERE dept_id = 5;` (Returns 11 - a phantom row appeared)

### 4.4. Lost Update
A lost update occurs when two concurrent transactions read the same row, calculate a new value based on the read value, and then both update the row. One transaction's update will overwrite the other's, effectively "losing" the first update.

**Example Scenario:**
*   **T1**: `SELECT quantity FROM inventory WHERE product_id = 1;` (Reads 10)
*   **T2**: `SELECT quantity FROM inventory WHERE product_id = 1;` (Reads 10)
*   **T1**: `UPDATE inventory SET quantity = 10 - 2 WHERE product_id = 1; COMMIT;` (Sets to 8)
*   **T2**: `UPDATE inventory SET quantity = 10 - 5 WHERE product_id = 1; COMMIT;` (Sets to 5, overwriting T1's deduction. The correct final state should be 3).

### 4.5. Write Skew
Write skew happens when two transactions concurrently read overlapping data sets, make decisions based on that data, and then modify disjoint parts of the data, resulting in a violation of a business rule that spans the data sets. It often involves constraints that the database cannot automatically enforce.

**Example Scenario:**
Rule: A department must have at least one active manager.
Current State: Department 1 has two active managers: Alice and Bob.
*   **T1 (Alice resigning)**: `SELECT count(*) FROM employees WHERE dept_id = 1 AND is_manager = true;` (Reads 2). Checks rule (2 > 1), decides to proceed.
*   **T2 (Bob resigning)**: `SELECT count(*) FROM employees WHERE dept_id = 1 AND is_manager = true;` (Reads 2). Checks rule (2 > 1), decides to proceed.
*   **T1**: `UPDATE employees SET is_manager = false WHERE name = 'Alice'; COMMIT;`
*   **T2**: `UPDATE employees SET is_manager = false WHERE name = 'Bob'; COMMIT;`
Result: Department 1 now has zero managers, violating the business rule.

---

## 5. Isolation Levels

The SQL standard defines four isolation levels based on which anomalies they permit.

| Isolation Level | Dirty Read | Non-Repeatable Read | Phantom Read | Lost Update / Write Skew |
| :--- | :--- | :--- | :--- | :--- |
| **READ UNCOMMITTED** | Allowed | Allowed | Allowed | Allowed |
| **READ COMMITTED** | Prevented | Allowed | Allowed | Allowed |
| **REPEATABLE READ** | Prevented | Prevented | Allowed (Standard) / Prevented (PG) | Allowed (Standard) / Prevented (PG SSI) |
| **SERIALIZABLE** | Prevented | Prevented | Prevented | Prevented |

### PostgreSQL Implementation specifics:
1.  **READ UNCOMMITTED**: PostgreSQL treats this exactly like READ COMMITTED. It is impossible to have a dirty read in PostgreSQL due to MVCC.
2.  **READ COMMITTED (Default)**: A statement only sees data committed before it began. Successive statements in the same transaction can see different data if other transactions commit in between.
3.  **REPEATABLE READ**: A transaction only sees data committed before the *transaction* began (it takes a snapshot at the start of the first non-transaction-control statement).
    *   *Note*: In PostgreSQL, this level also prevents Phantom Reads, surpassing the SQL standard requirement.
4.  **SERIALIZABLE**: Provides strict serializability. Transactions are executed concurrently but the database guarantees the result is the same as if they were executed one after another in some serial order. PostgreSQL uses Serializable Snapshot Isolation (SSI) to achieve this without excessive locking.

```sql
-- Setting isolation level for a specific transaction
BEGIN ISOLATION LEVEL SERIALIZABLE;
-- ... queries ...
COMMIT;

-- Or changing it for the session
SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL REPEATABLE READ;
```

---

## 6. Multi-Version Concurrency Control (MVCC)

PostgreSQL (like Oracle and InnoDB in MySQL) uses MVCC to manage concurrent access. Instead of locking a row when reading it, PostgreSQL creates a new version of the row when it is updated.

**Key Principles of MVCC:**
*   **Readers do not block Writers**: A `SELECT` query reads the version of the data that was valid when the query/transaction started. It ignores concurrent uncommitted updates.
*   **Writers do not block Readers**: An `UPDATE` or `DELETE` creates a new row version but leaves the old version intact for any transactions that still need to see it based on their snapshot.
*   **Writers only block Writers**: If two transactions try to modify the exact same row concurrently, the second transaction will block until the first one commits or rolls back.

When a row is updated, PostgreSQL doesn't overwrite it in place. It marks the old row as "dead" (expired) and inserts a completely new version. A background process called `VACUUM` is responsible for eventually reclaiming the space occupied by dead rows.

---

## 7. Locking in PostgreSQL

While MVCC handles most read/write concurrency automatically, sometimes you need explicit locking, especially to prevent Lost Updates.

### 7.1. Row-Level Locks

Row-level locks block other transactions from modifying the specific locked rows, but do not prevent reading (unless the reader also requests a lock).

*   **`SELECT ... FOR UPDATE`**: Acquires an exclusive lock on the selected rows. Used when you intend to `UPDATE` or `DELETE` those rows later in the transaction. Prevents concurrent updates, deletes, or `FOR UPDATE/SHARE` requests on those rows.
*   **`SELECT ... FOR SHARE`**: Acquires a shared lock. Used when you want to read a row and ensure it isn't modified by anyone else before your transaction finishes, but you don't intend to modify it yourself. Multiple transactions can hold a `FOR SHARE` lock simultaneously.
*   **`SELECT ... FOR NO KEY UPDATE`**: A slightly weaker exclusive lock. Used when updating a row but not changing its primary or unique keys. It allows concurrent `FOR KEY SHARE` locks.
*   **`SELECT ... FOR KEY SHARE`**: The weakest shared lock, acquired automatically when verifying foreign keys.

**Example: Safely processing an order (Preventing Lost Update)**

```sql
BEGIN;

-- Lock the specific product row. Other transactions trying to update
-- product_id = 45 will wait here.
SELECT quantity FROM products WHERE product_id = 45 FOR UPDATE;

-- Application logic calculates new quantity: old_quantity - order_quantity
-- Let's say order_quantity is 2.
UPDATE products SET quantity = quantity - 2 WHERE product_id = 45;

COMMIT;
```

### 7.2. SKIP LOCKED and NOWAIT

When acquiring row locks, a transaction usually waits if the lock is held by another transaction.

*   **`NOWAIT`**: If the lock cannot be acquired immediately, the statement fails immediately with an error instead of waiting.
*   **`SKIP LOCKED`**: If a row is locked by another transaction, it is skipped entirely in the result set. This is incredibly useful for building robust queueing systems or distributed workers.

**Example: A concurrent job queue**
Suppose `orders` table has `status = 'PENDING'`. Multiple worker processes want to claim orders to process them.

```sql
BEGIN;

-- Find one pending order, lock it, and skip any that other workers are already locking
SELECT order_id 
FROM orders 
WHERE status = 'PENDING' 
ORDER BY created_at ASC
LIMIT 1 
FOR UPDATE SKIP LOCKED;

-- If a row is returned, process it and update status
UPDATE orders SET status = 'PROCESSING' WHERE order_id = <returned_id>;

COMMIT;
```
Without `SKIP LOCKED`, workers would constantly block each other waiting on the same rows.

### 7.3. Table-Level Locks

Table-level locks affect the entire table. Most are acquired automatically by DDL commands (like `ALTER TABLE`) or DML commands (`SELECT`, `UPDATE`).

*   **`ACCESS SHARE`**: Acquired by `SELECT`. Conflicts only with `ACCESS EXCLUSIVE`.
*   **`ROW SHARE`**, **`ROW EXCLUSIVE`**, **`SHARE UPDATE EXCLUSIVE`**, **`SHARE`**, **`SHARE ROW EXCLUSIVE`**, **`EXCLUSIVE`**
*   **`ACCESS EXCLUSIVE`**: Acquired by `DROP TABLE`, `TRUNCATE`, `VACUUM FULL`. Conflicts with locks of all modes (blocks all reads and writes).

You can explicitly lock a table:
```sql
BEGIN;
LOCK TABLE employees IN EXCLUSIVE MODE;
-- ...
COMMIT;
```
Generally, avoid explicit table locks unless absolutely necessary, as they severely limit concurrency.

---

## 8. Deadlocks

A deadlock occurs when two or more transactions hold locks that the others need, creating a cycle of dependencies where neither can proceed.

**Example Scenario:**
*   **T1**: `UPDATE employees SET salary = 50000 WHERE emp_id = 1;` (Acquires lock on emp_id 1)
*   **T2**: `UPDATE departments SET location = 'NY' WHERE dept_id = 10;` (Acquires lock on dept_id 10)
*   **T1**: `UPDATE departments SET location = 'SF' WHERE dept_id = 10;` (Blocks, waiting for T2)
*   **T2**: `UPDATE employees SET salary = 60000 WHERE emp_id = 1;` (Blocks, waiting for T1)

**PostgreSQL Detection and Handling:**
PostgreSQL has an automatic deadlock detector. If it detects a cycle of waiting transactions that has persisted longer than the `deadlock_timeout` setting (default 1 second), it will automatically abort one of the transactions (the "victim") with an error:
`ERROR: deadlock detected`
The other transaction can then proceed.

**Prevention:**
The best way to prevent deadlocks is to **always acquire locks in the same consistent order** across your application. For example, if you always lock employees before departments, the scenario above is impossible; T2 would block on the first update waiting for T1, rather than acquiring a lock and causing a cycle.

---

## 9. Advisory Locks

Advisory locks are application-defined locks managed by PostgreSQL. They are not tied to tables or rows. They are useful when you need to coordinate distributed application logic that doesn't map cleanly to database tables.

They use 64-bit integers as identifiers.

```sql
-- Try to acquire an exclusive advisory lock with ID 12345.
-- Returns true if successful, false if someone else holds it (doesn't wait).
SELECT pg_try_advisory_lock(12345);

-- Do some application-level task that requires mutual exclusion
-- ...

-- Release the lock
SELECT pg_advisory_unlock(12345);
```
Advisory locks are fast and avoid table bloat, making them perfect for tasks like leader election or rate limiting external API calls.

---

## 10. The Danger of Long-Running Transactions

Transactions should generally be kept as short as possible. Long-running transactions (transactions that stay open for minutes, hours, or days) cause several severe problems in an MVCC database:

1.  **Table Bloat**: Because MVCC relies on keeping old row versions around for any transaction that might need to see them, a transaction that has been open for an hour prevents the `VACUUM` process from cleaning up any rows deleted or updated across the *entire database* during that hour. The tables physically grow larger on disk.
2.  **Lock Contention**: Holding row or table locks for a long time prevents other transactions from modifying those resources, leading to application hangs and timeouts.
3.  **Replication Lag**: In environments with read replicas, a long-running transaction on the primary can stall replication or cause queries on the replica to be cancelled to allow replication to proceed.
4.  **Transaction ID Wraparound Risk**: PostgreSQL uses 32-bit transaction IDs. If transactions remain open indefinitely while millions of other transactions process, the system can run out of IDs, requiring an emergency database shutdown to fix.

**Best Practices:**
*   Never wait for user input (e.g., leaving a transaction open while displaying a form) inside a database transaction.
*   Commit or rollback as quickly as the atomic operation is completed.
*   Monitor for queries lingering in the `active` or `idle in transaction` states in the `pg_stat_activity` view.
