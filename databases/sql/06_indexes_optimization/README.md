# Module 6: Indexes and Query Optimization

## 1. Introduction: Why Indexes Exist

A relational database stores table rows in unstructured files called heaps. When you execute a query like:

```sql
SELECT * FROM employees WHERE emp_id = 45012;
```

Without an index, the database engine must perform a **Sequential Scan** (or Table Scan). It reads every single row in the `employees` table from the disk into memory, checking if `emp_id` equals 45012. If the table has 10 million rows, the database must read all 10 million rows, which incurs a massive I/O cost and consumes significant CPU cycles.

An **Index** is an auxiliary data structure that stores a subset of the table's data in a highly structured way, optimized for fast retrieval. Instead of scanning millions of rows, the database can traverse the index to find the exact location (the disk pointer) of the requested row, usually in just a few operations. The tradeoff is that indexes consume additional disk space and must be maintained (updated) whenever the underlying table is modified (INSERT, UPDATE, DELETE).

---

## 2. B-Tree Index Internals

The default index type in PostgreSQL (and most relational databases) is the B-Tree (Balanced Tree). 

### Structure

A B-Tree consists of:
1.  **Root Node:** The top entry point.
2.  **Internal Nodes:** Routing nodes that guide the search.
3.  **Leaf Nodes:** The bottom layer that contains the actual index keys in sorted order, along with a pointer (TID - Tuple Identifier in PostgreSQL) to the actual row in the heap (the table file).

The B-Tree is balanced, meaning all leaf nodes are at the same depth. This ensures that the time to search for any value is consistent, regardless of where it lies in the data distribution.

### How Binary Search Works in the Tree

When searching for `emp_id = 45012`:
1.  The engine reads the root node, which might say: "Values < 50000 go left; Values >= 50000 go right."
2.  Since 45012 < 50000, it follows the left pointer to the next internal node.
3.  This process repeats until it reaches the leaf node containing exactly `45012`.
4.  The leaf node provides the TID (e.g., Block 105, Offset 14).
5.  The engine goes directly to Block 105 in the heap to fetch the row.

### Index Height and Branching Factor

-   **Branching Factor:** The number of child pointers each node can hold. Because nodes correspond to disk blocks (typically 8KB), a node can hold hundreds of keys. 
-   **Index Height:** Because of the large branching factor, B-Trees remain very shallow. A 3-level or 4-level B-Tree can easily map billions of rows. Thus, finding a row usually requires only 3 to 4 index block reads.

### Scan Types

When a query is executed, the query planner chooses an execution strategy based on the index availability and estimated costs.

1.  **Sequential Scan:** Reads the entire table block by block. Chosen when no index exists, or when the query is expected to return a large percentage of the table. Scanning sequentially is highly optimized for sequential disk I/O.
2.  **Index Scan:** Traverses the index to find matching keys, then immediately fetches each corresponding row from the heap. Ideal for retrieving a small number of rows.
3.  **Bitmap Index Scan:** Used when an index scan would fetch too many rows, potentially visiting the same heap blocks multiple times randomly. 
    - The engine first scans the index and builds an in-memory bitmap of the heap blocks that contain matching rows.
    - It then performs a **Bitmap Heap Scan**, reading the required heap blocks sequentially based on the bitmap. This minimizes random disk I/O.

---

## 3. Hash Indexes

While B-Trees handle equality (`=`) and range (`<`, `>`, `BETWEEN`) queries efficiently, Hash indexes are designed specifically and exclusively for equality comparisons.

```sql
CREATE INDEX idx_emp_dept_hash ON employees USING hash (dept_id);
```

**Characteristics:**
-   **Equality Only:** Cannot be used for `<`, `>`, or `ORDER BY`.
-   **No Ordering:** The data is stored based on a hash function, distributing keys randomly across buckets.
-   **Performance:** Slightly faster than B-Trees for pure equality lookups because the hash calculation leads directly to the bucket, bypassing tree traversal.
-   **PostgreSQL Note:** Historically, Hash indexes in PostgreSQL were not crash-safe (not WAL-logged) and therefore discouraged. Since PostgreSQL 10, Hash indexes are fully crash-safe, replicated, and performant.

---

## 4. Creating Indexes

### Basic Creation
```sql
-- Creates a standard B-Tree index on the name column
CREATE INDEX idx_customers_name ON customers(name);
```

### Unique Indexes
Enforces data integrity by preventing duplicate values in the indexed column(s).
```sql
CREATE UNIQUE INDEX idx_customers_email ON customers(email);
```

### Concurrent Index Creation (`CONCURRENTLY`)
Standard `CREATE INDEX` acquires an exclusive lock on the table, blocking all `INSERT`, `UPDATE`, and `DELETE` operations until the index is built. In production environments, this can cause massive downtime.

PostgreSQL offers the `CONCURRENTLY` keyword:
```sql
CREATE INDEX CONCURRENTLY idx_orders_status ON orders(status);
```
**Why it matters:** It builds the index without blocking writes. It takes longer and requires two passes over the table, but it ensures your application remains online.

---

## 5. Composite Indexes (Multi-column Indexes)

An index can encompass multiple columns. The order of columns is critical.

```sql
CREATE INDEX idx_orders_cust_date ON orders(customer_id, order_date);
```

### The Leftmost Prefix Rule
A composite index can only be used if the query filters on the columns starting from the leftmost column in the index.

**Will use the index:**
- `WHERE customer_id = 123` (Uses first column)
- `WHERE customer_id = 123 AND order_date = '2023-01-01'` (Uses both columns)

**Will NOT use the index effectively:**
- `WHERE order_date = '2023-01-01'` (Missing the leftmost prefix `customer_id`. The database would have to scan the entire index, which is rarely better than a seq scan).

**Best Practice:** Put the column frequently used with equality conditions (`=`) first, followed by columns used for range queries (`>`, `<`) or ordering.

---

## 6. Partial Indexes

If you frequently query a specific subset of data, you can create a partial index that only includes rows matching a condition. This saves disk space and makes the index much smaller and faster to scan.

```sql
-- Only index active employees
CREATE INDEX idx_active_employees ON employees(dept_id) WHERE is_active = true;

-- Only index incomplete orders
CREATE INDEX idx_incomplete_orders ON orders(customer_id) WHERE status != 'completed';
```

**Massive Win:** If only 2% of your `orders` are "pending", a partial index on pending orders will be tiny. Queries looking for pending orders will be lightning fast.

---

## 7. Covering Indexes (Index-Only Scans)

Normally, an index scan involves reading the index to get the TID, then reading the heap (the table) to get the actual row data.

If a query only selects columns that are present in the index, the database can perform an **Index-Only Scan**, completely bypassing the heap read. 

In PostgreSQL, you can use the `INCLUDE` clause to add non-key columns to the leaf nodes of an index specifically to make them covering indexes.

```sql
-- B-Tree search on product_id, but the leaf nodes also carry the price
CREATE INDEX idx_products_id_price ON products(product_id) INCLUDE (price);
```

When you run:
```sql
SELECT price FROM products WHERE product_id = 88;
```
The database gets the `price` directly from the index. No heap access is required, dramatically speeding up the query.

---

## 8. Expression Indexes

Sometimes queries apply functions to columns. A standard index on a column cannot be used if the column is wrapped in a function.

```sql
-- This WILL NOT use idx_customers_email
SELECT * FROM customers WHERE LOWER(email) = 'john@example.com';
```

To fix this, you create an index on the exact expression used in the query:
```sql
CREATE INDEX idx_customers_email_lower ON customers(LOWER(email));
```
Now, the previous query will use the expression index.

---

## 9. Index Selectivity

**Selectivity** refers to the number of distinct values in a column relative to the total number of rows.

-   **High Selectivity:** Many distinct values (e.g., `email`, `user_id`). An index is highly useful here because it narrows the search down to a few rows.
-   **Low Selectivity:** Few distinct values (e.g., `is_active` (boolean), `gender`). An index on a low-selectivity column is often ignored by the query planner. If 50% of employees are `is_active = true`, the planner knows that reading the index and then looking up half the table in the heap is more expensive than just sequentially scanning the table once.

---

## 10. When NOT to Index

Do not over-index. Indexes carry costs.
-   **Low-selectivity columns:** Unless used in a partial index (e.g., indexing the rare 1% value of a status column).
-   **Heavily written tables:** Every `INSERT`, `UPDATE`, and `DELETE` must update the indexes. Too many indexes will cripple write performance.
-   **Small tables:** If a table fits in a few disk blocks, a sequential scan will be faster than traversing an index and fetching from the heap.

---

## 11. EXPLAIN and EXPLAIN ANALYZE

`EXPLAIN` shows the query planner's *estimated* execution plan.
`EXPLAIN ANALYZE` actually *executes* the query and shows both the estimates and the actual execution times.

```sql
EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 500;
```

### Reading the Output

-   **Node Types:**
    -   `Seq Scan`: Reading the whole table.
    -   `Index Scan`: Reading index, then heap.
    -   `Index Only Scan`: Reading only the index.
    -   `Bitmap Index Scan` / `Bitmap Heap Scan`: Building a memory bitmap from the index, then fetching heap blocks sequentially.
    -   `Nested Loop`: For each row in table A, loop through matching rows in table B. (Good for small datasets).
    -   `Hash Join`: Hashes the smaller table into memory, then scans the larger table probing the hash table. (Good for large datasets with equality joins).
    -   `Merge Join`: Sorts both tables by the join key, then zips them together. (Good if data is already sorted via indexes).
-   **Cost (`cost=startup_cost..total_cost`):**
    -   `startup_cost`: Cost before the first row can be returned (e.g., time to sort).
    -   `total_cost`: Estimated cost to return all rows. Cost is an arbitrary unit representing disk fetches and CPU effort.
-   **Actual Time:** The real milliseconds spent (only seen with `ANALYZE`).
-   **Rows:** Estimated vs Actual rows returned by that node.
-   **Loops:** How many times the node was executed (e.g., in a Nested Loop).

---

## 12. EXPLAIN (ANALYZE, BUFFERS)

Adding `BUFFERS` provides insight into memory vs. disk usage.

```sql
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM products WHERE category = 'Electronics';
```
Output includes lines like:
`Buffers: shared hit=42 read=10`
-   **hit:** The block was already in the database's shared memory cache (RAM). Extremely fast.
-   **read:** The block had to be read from the operating system / disk. Slower.

Optimization goal: Maximize hits, minimize reads.

---

## 13. Query Planner Statistics

The query planner relies on statistics (data distribution, most common values, histograms) to estimate costs and choose between an Index Scan or Seq Scan.

These statistics are stored in `pg_class` and `pg_statistic` (accessible via `pg_stats` view).

The `ANALYZE` command samples the table and updates these statistics. If statistics are stale (e.g., after a massive bulk insert), the planner might choose a terrible execution plan.

```sql
-- Manually update statistics
ANALYZE orders;
```

---

## 14. Index Bloat and Maintenance

### Dead Tuples
PostgreSQL uses MVCC (Multi-Version Concurrency Control). When you `UPDATE` or `DELETE` a row, the old row (tuple) is not immediately deleted. It is marked as dead. Indexes still point to these dead tuples until they are cleaned up.

### VACUUM and AUTOVACUUM
`VACUUM` reclaims the space occupied by dead tuples, making it available for future inserts. It also removes the dead pointers from indexes. `AUTOVACUUM` is a background daemon that runs `VACUUM` and `ANALYZE` automatically. 

**Index Bloat:** If a table undergoes heavy updates and autovacuum cannot keep up, indexes become physically large and sparse (bloated), slowing down scans. Fix this by using `REINDEX` or recreating the index `CONCURRENTLY`.

### Finding Unused Indexes
Unused indexes slow down writes for no read benefit.
```sql
SELECT relname, indexrelname, idx_scan 
FROM pg_stat_user_indexes 
WHERE idx_scan = 0;
```
If `idx_scan` is 0 over a long period, drop the index.

---

## 15. Common Slow Query Patterns and Fixes

### 1. Function on Indexed Column
**Bad:** `WHERE DATE(order_date) = '2023-01-01'` (Disables B-Tree index on `order_date`)
**Fix:** Compare against the raw column: `WHERE order_date >= '2023-01-01 00:00:00' AND order_date < '2023-01-02 00:00:00'`

### 2. LIKE with Leading Wildcard
**Bad:** `WHERE name LIKE '%Smith%'` (B-Tree indexes sort left-to-right. A leading wildcard makes the index useless).
**Fix:** Use a GIN index with the `pg_trgm` extension for text search, or full-text search (`to_tsvector`).

### 3. Implicit Type Casting
**Bad:** `WHERE emp_id = '100'` (If `emp_id` is an integer, casting a string to an int might bypass the index depending on DB specifics).
**Fix:** Match the exact data type.

### 4. OR Conditions Splitting Usage
**Bad:** `WHERE status = 'active' OR amount > 1000` (Often results in a Seq Scan).
**Fix:** Sometimes unavoidable, but replacing `OR` with a `UNION` of two queries can allow the planner to use two separate indexes.

### 5. N+1 Queries
**Bad:** Selecting 100 orders, then running 100 individual queries to fetch the customer for each order.
**Fix:** Use a `JOIN` to fetch orders and their customers in a single query.

---

## 16. Query Optimization Techniques

-   **Limit Early:** If you only need 10 rows, use `LIMIT 10`. This changes the planner's cost estimations drastically, often favoring an index scan even on unselective columns because it can stop after finding 10 matches.
-   **Rewriting Subqueries:** Convert `IN (SELECT...)` or `NOT IN` to `EXISTS` or `JOIN`s, which the planner can often optimize better (like using a Hash Anti Join for `NOT EXISTS`).
-   **Connection Pooling:** Establishing a database connection is expensive. Use a connection pooler like `PgBouncer`. While not strictly a query optimization, it prevents the database from wasting CPU on connection handshakes, dramatically improving total query throughput.
