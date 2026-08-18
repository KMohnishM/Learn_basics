# Module 6: QnA - Indexes and Query Optimization

### 1. How does a B-Tree index work internally? Draw/describe the structure.

**Answer:**
A B-Tree (Balanced Tree) index is a hierarchical data structure optimized for disk I/O. It consists of:
- **Root Node:** The top-level entry point containing boundary values and pointers to internal nodes.
- **Internal Nodes:** Branching nodes that further divide the data ranges and point to leaf nodes.
- **Leaf Nodes:** The bottom level containing the actual indexed values in sorted order. Alongside each value is a pointer (Tuple Identifier, or TID in PostgreSQL) that points directly to the physical location of the row in the table (the heap).

Because it is balanced, every path from root to leaf has the same length. When searching for a value, the database performs a binary search within the nodes, comparing the target value against the boundaries to decide which child pointer to follow. The large branching factor (many pointers per node) keeps the tree shallow, meaning reaching any leaf node usually takes only 3 to 4 disk block reads.

### 2. What is the leftmost prefix rule for composite indexes? Give an example.

**Answer:**
The leftmost prefix rule dictates that a composite (multi-column) index can only be utilized if the query's `WHERE` clause includes conditions on the columns starting from the very first (leftmost) column of the index, without skipping any.

**Example:**
If you have `CREATE INDEX idx_emp_dept_salary ON employees(dept_id, salary);`
- `WHERE dept_id = 5` **WILL** use the index (it uses the first column).
- `WHERE dept_id = 5 AND salary > 50000` **WILL** use the index (it uses the first and second columns).
- `WHERE salary > 50000` **WILL NOT** use the index efficiently. Because the data is sorted primarily by `dept_id`, the values for `salary` are scattered throughout the index. The database would have to scan the entire index to find matching salaries, which is usually slower than just scanning the table.

### 3. What is the difference between an Index Scan and a Bitmap Heap Scan?

**Answer:**
- **Index Scan:** The database traverses the index to find a matching key, immediately fetches the corresponding row from the heap, and then returns to the index for the next key. This alternates between index I/O and heap I/O. It is highly efficient for retrieving a very small number of rows.
- **Bitmap Heap Scan:** When the planner expects to retrieve many rows via an index, an Index Scan could result in reading the same heap disk blocks multiple times randomly. Instead, it uses a Bitmap Index Scan to scan the index first and build an in-memory bitmap representing all the heap blocks that contain matching rows. Then, it performs a **Bitmap Heap Scan**, reading those required heap blocks sequentially based on the bitmap. This trades a bit of memory overhead for highly optimized, sequential disk I/O.

### 4. When would the query planner choose a sequential scan over an available index?

**Answer:**
The planner chooses a sequential scan when it calculates that reading the whole table is cheaper (less disk I/O cost) than using the index. This typically happens when:
1.  **Low Selectivity:** The query condition matches a large percentage of the table (e.g., > 10-20%). Scanning the index and then looking up rows randomly in the heap is more expensive than just reading the heap sequentially block by block.
2.  **Small Tables:** The table is so small (e.g., a few disk blocks) that the overhead of reading index blocks before heap blocks isn't worth it.
3.  **Missing Leftmost Prefix:** The query uses a composite index but doesn't filter on the leading column.
4.  **Stale Statistics:** The `pg_statistic` data is outdated, leading the planner to incorrectly assume a query will return most of the table.

### 5. What is a partial index? Give a real-world use case where it provides a significant benefit.

**Answer:**
A partial index is an index built over a subset of a table, defined by a `WHERE` clause in the `CREATE INDEX` statement.

**Real-world use case:**
Consider an `orders` table with 10 million rows, where 9.9 million have `status = 'completed'` and 100,000 have `status = 'pending'`. 
Queries frequently ask for: `SELECT * FROM orders WHERE status = 'pending';`
If you index the entire `status` column, the index is huge. Instead, use a partial index:
`CREATE INDEX idx_pending_orders ON orders(customer_id) WHERE status = 'pending';`
This index will only contain 100,000 entries. It is extremely small, fits entirely in RAM, and makes queries for pending orders instantaneous, while ignoring historical completed orders completely.

### 6. What is a covering index? How do you create one in PostgreSQL?

**Answer:**
A covering index is an index that contains all the columns necessary to satisfy a query (both the columns used in `WHERE`/`ORDER BY` and the columns returned in the `SELECT`). When this happens, the database performs an **Index-Only Scan**, meaning it reads the data straight from the index structure and never touches the underlying table (the heap).

In PostgreSQL, you create one using the `INCLUDE` clause:
`CREATE INDEX idx_prod_cat_inc_price ON products(category) INCLUDE (price);`
For the query `SELECT price FROM products WHERE category = 'Electronics';`, the engine finds 'Electronics' in the index, and the `price` payload is right there in the leaf node, bypassing heap I/O entirely.

### 7. Why does `WHERE LOWER(email) = 'test@example.com'` not use an index on the email column? How do you fix it?

**Answer:**
It does not use the standard B-Tree index on `email` because the index stores the exact values as they appear in the table (e.g., 'Test@Example.com'). When you apply a function like `LOWER()`, the database must compute the result for every row before it can compare it to 'test@example.com'. Therefore, it must perform a sequential scan.

**Fix:** Create an Expression Index.
`CREATE INDEX idx_customers_lower_email ON customers(LOWER(email));`
This computes the lowercase value at insertion/update time and stores that result in the index, allowing the planner to do a direct index lookup.

### 8. Read this EXPLAIN output:
```text
Hash Join  (cost=120.50..340.20 rows=50 width=80)
  Hash Cond: (orders.customer_id = customers.customer_id)
  ->  Seq Scan on orders  (cost=0.00..200.00 rows=10000 width=40)
  ->  Hash  (cost=100.00..100.00 rows=500 width=40)
        ->  Seq Scan on customers  (cost=0.00..100.00 rows=500 width=40)
```
**What does it tell you?**

**Answer:**
- The query joins `orders` and `customers` using a **Hash Join**.
- It sequentially scans the `customers` table (estimated 500 rows, cost 100.00) and builds an in-memory Hash table from it.
- It then sequentially scans the `orders` table (estimated 10,000 rows, cost 200.00), probing the Hash table for matches based on `customer_id`.
- Neither table is utilizing an index for the scan.
- The total estimated cost of the query is 340.20, returning an estimated 50 rows.
- The `startup_cost` of the Hash Join is 120.50 (mostly the time taken to scan `customers` and build the hash table before returning the first row).

### 9. What is index selectivity and why does it matter?

**Answer:**
Index selectivity is the ratio of distinct values in an indexed column to the total number of rows in the table. 
- A unique identifier (like `email` or `user_id`) has very high selectivity. 
- A boolean column (`is_active`) has very low selectivity.

It matters because the query planner uses selectivity to decide if an index is worth using. If a column has low selectivity, an index lookup will return a large chunk of the table. The planner knows that randomly looking up that many rows in the heap via index pointers will incur massive random disk I/O, which is slower than just reading the entire file sequentially. Thus, low selectivity columns usually result in sequential scans, making indexes on them a waste of space.

### 10. What is the difference between EXPLAIN and EXPLAIN ANALYZE?

**Answer:**
- **`EXPLAIN`** asks the database planner to generate and display the execution plan it *intends* to use, along with estimated costs and estimated row counts based on stored statistics. It does not actually run the query.
- **`EXPLAIN ANALYZE`** actually *executes* the query. It returns the planner's estimates, but also includes the actual time spent in each node, the actual number of rows processed, and the actual number of loop iterations. This is crucial for diagnosing slow queries where the planner's estimates differ wildly from reality.

### 11. How do you find unused indexes in PostgreSQL?

**Answer:**
You query the `pg_stat_user_indexes` system view, which tracks statistics on index usage.

```sql
SELECT relname AS table_name, indexrelname AS index_name, idx_scan 
FROM pg_stat_user_indexes 
WHERE idx_scan = 0;
```
If `idx_scan` (the number of times an index has been used for a scan) remains 0 or very low over a long period of application uptime, the index is likely unused for reads but is still imposing overhead on writes. It should be evaluated for deletion.

### 12. What causes index bloat and how do you fix it?

**Answer:**
Index bloat is caused by PostgreSQL's MVCC (Multi-Version Concurrency Control). When rows are updated or deleted, the old versions (dead tuples) are kept until a `VACUUM` process cleans them up. Indexes point to both live and dead tuples. If a table is updated heavily and autovacuum is not aggressive enough, the index becomes filled with dead pointers, growing physically larger and sparse (bloated). This increases disk I/O and memory usage during scans.

**Fix:** 
- To fix existing bloat, you rebuild the index. For production, use `REINDEX INDEX CONCURRENTLY idx_name;` to rebuild it without locking out writes.
- To prevent future bloat, tune autovacuum settings (e.g., lower `autovacuum_vacuum_scale_factor`) for the heavily updated table so it cleans up dead tuples more frequently.

### 13. Why might a LIKE query with a leading wildcard be slow? What are the alternatives?

**Answer:**
A query like `WHERE name LIKE '%smith'` is slow because standard B-Tree indexes sort data from left to right. When a wildcard `%` is at the beginning, the database does not know where to start searching in the tree; it essentially has to check every single entry in the index or fall back to a sequential scan of the table.

**Alternatives:**
1.  **pg_trgm extension:** Use a GIN or GiST index with trigram indexing. It breaks strings down into 3-letter chunks and indexes those, making `%smith%` queries very fast.
    `CREATE INDEX idx_name_trgm ON employees USING gin (name gin_trgm_ops);`
2.  **Full-Text Search:** If searching documents or words, use PostgreSQL's native full-text search (`to_tsvector` and `to_tsquery`) with a GIN index.

### 14. What is CREATE INDEX CONCURRENTLY and when do you need it?

**Answer:**
By default, the `CREATE INDEX` command acquires an `AccessExclusiveLock` on the table. This blocks all write operations (`INSERT`, `UPDATE`, `DELETE`) on that table until the index is fully built, which can cause significant application downtime on large tables.

`CREATE INDEX CONCURRENTLY` builds the index without blocking writes. It requires multiple passes over the table and takes longer to finish, but it keeps the table fully online for the application. You need it almost always when deploying index changes to a live production database.

### 15. You have a query that does `WHERE status = 'active' AND created_at > NOW() - INTERVAL '7 days'`. Should you index status, created_at, both, or use a partial index? Explain.

**Answer:**
The best approach depends on data distribution, but generally, a **partial index** is the most optimal choice.

- Indexing `status` alone is bad if 'active' is a low-selectivity value (e.g., 90% of rows are active).
- A composite index `(status, created_at)` is better, utilizing the leftmost prefix rule.
- **Best solution:** `CREATE INDEX idx_recent_active ON table_name(created_at) WHERE status = 'active';`

**Why:** By using a partial index, you completely omit inactive rows from the index structure. The index is extremely small and highly targeted. When the query runs, the planner recognizes the `WHERE status = 'active'` condition matches the partial index definition, and uses the tiny index to rapidly evaluate the `created_at` range condition.
