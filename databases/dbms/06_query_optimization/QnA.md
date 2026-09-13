# Module 6: Query Optimization QnA

### 1. What does EXPLAIN ANALYZE output show? Explain these fields: `cost=X..Y`, `rows=N`, `actual time=A..B`, `loops=C`, `Buffers: shared hit=X read=Y`. What does a large gap between estimated rows and actual rows indicate?
`EXPLAIN ANALYZE` actually executes the query (unlike plain `EXPLAIN`) and provides a detailed breakdown of the query plan alongside real execution metrics. The `cost=X..Y` field represents the planner's estimated arbitrary cost units; `X` is the startup cost before the first row can be returned, and `Y` is the total cost to return all rows. `rows=N` is the planner's estimate of the number of rows this node will output. `actual time=A..B` shows the true execution time in milliseconds, where `A` is the time to get the first row and `B` is the time to get all rows. `loops=C` indicates how many times this specific node was executed (e.g., in a nested loop). `Buffers: shared hit=X read=Y` shows memory usage, where `hit` means pages found in the RAM buffer pool, and `read` means pages fetched from disk. A large gap between estimated `rows` and `actual` rows indicates stale or missing statistics, causing the planner to make wildly inaccurate assumptions and often resulting in catastrophically bad query plans, like choosing a nested loop when a hash join was needed.

### 2. Explain Nested Loop, Hash, and Merge join algorithms. When does PostgreSQL choose each? What role does `work_mem` play in algorithm selection?
A Nested Loop join iterates through every row of the outer table, and for each row, scans the inner table for a match. PostgreSQL chooses it when the outer table is very small or when an index on the inner table makes the lookup extremely fast. A Hash join builds an in-memory hash table of the smaller relation using the join key, and then probes it by scanning the larger relation. It is chosen for large, unsorted datasets where equijoins (`=`) are used. A Merge join requires both input relations to be sorted on the join key; it then walks through both sets simultaneously, merging matches. It is chosen when the inputs are already sorted (e.g., via index scans) or when joining massive tables where sorting is cheaper than building a giant hash table. The `work_mem` parameter dictates how much RAM can be used for in-memory sorts and hash tables. If `work_mem` is too small to hold the hash table, PostgreSQL may spill to disk (creating batches), severely degrading performance, or it might abandon the Hash join entirely in favor of a Merge or Nested Loop join.

### 3. What is `work_mem` in PostgreSQL? How does it affect hash joins and sort operations? What does `Hash Batches: 4` in EXPLAIN ANALYZE output mean? How do you size it correctly?
`work_mem` is a configuration parameter that specifies the maximum amount of memory a single query operation (like a sort, hash table, or materialization node) can use in RAM before it is forced to write temporary files to disk. It dramatically affects hash joins and sort operations; if the data fits within `work_mem`, the operation completes entirely in high-speed RAM. If the data exceeds `work_mem`, PostgreSQL spills to disk. When `EXPLAIN ANALYZE` shows `Hash Batches: 4`, it means the hash table exceeded `work_mem` and had to be partitioned into 4 distinct batches written to temporary disk files, which massively increases I/O and latency. To size `work_mem` correctly, you must balance the total server RAM against `max_connections`, because `work_mem` is allocated per operation, not per query or per user. A complex query with multiple sorts can allocate `work_mem` several times simultaneously. A common formula is `(Total RAM - Shared Buffers) / (Max Connections * 2)`, typically resulting in values between 16MB and 64MB for general workloads.

### 4. Explain the PostgreSQL cost model. What are `seq_page_cost`, `random_page_cost`, and `cpu_tuple_cost`? Why should you set `random_page_cost = 1.1` for SSD storage? What does lowering it cause the planner to do?
The PostgreSQL cost model is a mathematical framework the query planner uses to estimate the relative expense of different execution paths, selecting the plan with the lowest total cost. The costs are arbitrary units based on physical operations. `seq_page_cost` (default 1.0) represents the cost of sequentially fetching a disk page. `random_page_cost` (default 4.0) represents the cost of fetching a disk page randomly, which is historically much slower on spinning hard drives (HDDs) due to seek time. `cpu_tuple_cost` (default 0.01) is the CPU effort required to process a single row in memory. For modern SSD storage, physical seek time is virtually zero, so you should lower `random_page_cost = 1.1` (or even 1.0) to accurately reflect the hardware's capabilities. Lowering this value causes the planner to heavily favor index scans over sequential scans, because it correctly realizes that jumping around the disk via an index is no longer a massive penalty compared to scanning the table sequentially.

### 5. What are table statistics in PostgreSQL? What information does `ANALYZE` collect and store in `pg_stats`? How do stale statistics cause catastrophically bad query plans?
Table statistics in PostgreSQL are metadata summaries about the distribution of data within columns, used exclusively by the query planner to estimate row counts and costs. The `ANALYZE` command (often run automatically by the autovacuum daemon) samples the table data and collects information stored in the `pg_stats` system view. This includes the total number of rows, the number of distinct values (`n_distinct`), the fraction of null values (`null_frac`), a list of the most common values and their frequencies (`most_common_vals`), and a histogram bounding data into buckets. Stale statistics occur when data is heavily modified (bulk inserts/updates) but `ANALYZE` hasn't run yet. This causes catastrophically bad query plans because the planner might estimate a query will return 5 rows when it actually returns 5,000,000. Operating on the false "5 row" assumption, the planner might choose a Nested Loop index scan, resulting in millions of random disk lookups, taking hours, whereas a Hash Join on a sequential scan would have finished in seconds.

### 6. What is an expression index? Give a concrete before-and-after example showing a query that cannot use a regular B-Tree index but uses an expression index. Show the CREATE INDEX and the query.
An expression index (or function-based index) evaluates a function or scalar expression on one or more columns and indexes the result, rather than indexing the raw column data. This is crucial when queries consistently filter or sort on the transformed output of a column.
**Before:**
If you query users by case-insensitive email:
`SELECT * FROM users WHERE lower(email) = 'john@example.com';`
A regular index on `email` (`CREATE INDEX idx_email ON users(email);`) cannot be used, forcing a slow sequential scan because the `lower()` function must be applied to every row during execution.
**After:**
You create an expression index:
`CREATE INDEX idx_lower_email ON users (lower(email));`
Now, when you run the exact same query:
`SELECT * FROM users WHERE lower(email) = 'john@example.com';`
PostgreSQL immediately recognizes the expression in the `WHERE` clause matches the index definition, resulting in a lightning-fast Index Scan.

### 7. What is keyset (cursor) pagination vs OFFSET pagination? Why does OFFSET become slower as the page number grows? Show both patterns in SQL and explain the trade-offs.
OFFSET pagination uses `LIMIT` and `OFFSET` to skip rows, while keyset pagination (cursor pagination) uses the last seen value (e.g., an ID or timestamp) in the `WHERE` clause to fetch the next set of rows.
**OFFSET Pagination:**
`SELECT * FROM posts ORDER BY created_at DESC LIMIT 10 OFFSET 10000;`
This becomes slower as the page number grows because PostgreSQL must physically compute, retrieve, and discard the first 10,000 rows before returning the 10 you requested. It is simple to implement but scales terribly.
**Keyset Pagination:**
`SELECT * FROM posts WHERE created_at < '2023-10-01 12:00:00' ORDER BY created_at DESC LIMIT 10;`
Keyset pagination is O(1) in performance regardless of the page depth, because it uses an index on `created_at` to jump instantly to the exact starting row. The trade-off is that it cannot support arbitrary page jumping (e.g., "Go to page 50") and requires a unique sequential column or tie-breaker to prevent missing rows if duplicate values exist.

### 8. What is the N+1 query problem? Give a real ORM scenario (e.g., loading blog posts and their comments) and show the inefficient N+1 pattern vs the correct JOIN-based SQL.
The N+1 query problem is a severe performance anti-pattern typical of ORMs (Object-Relational Mappers), where an application makes one database query to fetch a list of N parent records, and then executes N additional separate queries to fetch the associated child records for each parent. 
**Scenario:** Loading 10 blog posts and their comments.
**The inefficient N+1 pattern (11 queries total):**
`SELECT * FROM posts LIMIT 10;` (The "1" query)
`SELECT * FROM comments WHERE post_id = 1;` (The "N" queries...)
`SELECT * FROM comments WHERE post_id = 2;`
...
`SELECT * FROM comments WHERE post_id = 10;`
This incurs massive network round-trip latency and database overhead.
**The correct JOIN-based SQL (1 query total):**
`SELECT p.*, c.* FROM posts p LEFT JOIN comments c ON p.id = c.post_id WHERE p.id IN (SELECT id FROM posts LIMIT 10);`
By eagerly loading the relationships in a single query using JOINs, the database does the heavy lifting efficiently, eliminating network latency and yielding vastly superior performance.

### 9. What is a materialized view? How does `REFRESH MATERIALIZED VIEW CONCURRENTLY` differ from regular refresh? What index is required for concurrent refresh and why?
A materialized view in PostgreSQL is a database object that stores the physical result set of a complex query (like aggregations or multi-table joins) on disk, acting as a cached snapshot to provide instant read performance at the cost of data staleness. Unlike standard views, which execute their underlying query every time they are accessed, materialized views must be manually updated using `REFRESH MATERIALIZED VIEW`. A regular refresh locks the view completely, blocking all read access while the data is being replaced, causing application downtime. `REFRESH MATERIALIZED VIEW CONCURRENTLY` updates the view without blocking `SELECT` queries, allowing seamless zero-downtime cache invalidation. To use the `CONCURRENTLY` option, you are required to create a `UNIQUE INDEX` on the materialized view. This is because PostgreSQL must perform a background diff (identifying rows to insert, update, or delete) between the old snapshot and the new query results, which fundamentally requires a unique identifier to map the rows.

### 10. What is partition pruning in PostgreSQL? Show an EXPLAIN output where pruning eliminates a partition, and explain what query predicate is required for the planner to prune.
Partition pruning is an optimization technique where the query planner analyzes the `WHERE` clause and automatically skips scanning physical partitions that cannot possibly contain matching rows, drastically reducing I/O and execution time. 
**EXPLAIN output showing pruning:**
```text
EXPLAIN SELECT * FROM sales WHERE sale_date = '2023-12-15';
                           QUERY PLAN                           
----------------------------------------------------------------
 Append  (cost=0.00..25.88 rows=5 width=40)
   ->  Seq Scan on sales_2023_12  (cost=0.00..25.85 rows=5 width=40)
         Filter: (sale_date = '2023-12-15'::date)
```
In this example, the parent table `sales` has partitions for every month. Because the planner sees the predicate `sale_date = '2023-12-15'`, it aggressively prunes (ignores) `sales_2023_11`, `sales_2024_01`, and all others, only scanning the `sales_2023_12` partition. For pruning to occur, the query predicate must filter directly on the exact partition key column using operators like `=`, `>`, `<`, or `IN`. If the predicate applies a function to the partition key (e.g., `EXTRACT(MONTH FROM sale_date) = 12`), the planner generally cannot prune.

### 11. What are extended statistics in PostgreSQL (`CREATE STATISTICS`)? What specific estimation problem do they solve? Give the correlated columns example (city, zip_code) and show the CREATE STATISTICS command.
Extended statistics, created via `CREATE STATISTICS`, provide the query planner with metadata about the relationships and cross-column correlations between multiple columns in a table. Standard statistics only track data distribution for individual columns in isolation. This solves a major estimation problem: when columns are highly correlated, filtering on both columns causes the planner to multiply their independent probabilities, resulting in a massive underestimation of returned rows and terrible join plans. 
**Correlated columns example:** 
If you query `WHERE city = 'San Francisco' AND zip_code = '94105'`, the planner might estimate 1 row because it assumes City and Zip Code are completely independent variables. In reality, Zip 94105 implies San Francisco, so the correlation is 100%, and millions of rows might match.
**The command:**
`CREATE STATISTICS st_city_zip (dependencies) ON city, zip_code FROM addresses;`
Running `ANALYZE` after this allows the planner to recognize the dependency, correct its row estimate, and generate a fast execution plan.

### 12. What does `enable_seqscan = off` do? Is it appropriate to use in production? What are the correct use cases for temporarily disabling specific scan types?
Setting `enable_seqscan = off` tells the query planner to strongly discourage the use of sequential scans (reading the entire table). It assigns a massive arbitrary cost penalty to sequential scans, forcing the planner to choose an index scan if one is physically possible, regardless of whether the planner thinks it's a bad idea. It is absolutely not appropriate to use globally in production. Sequential scans are often the fastest method when reading a large portion of a table (e.g., returning 30% of rows), because sequential disk reads are vastly superior to millions of random index lookups. The correct use cases for temporarily disabling specific scan types (within a single session or transaction) are purely diagnostic. DBAs use it to debug query plans, proving whether an index is actually usable, bypassing stale statistics to force a known-good plan temporarily, or isolating planner cost-model issues by comparing the execution time of the forced index scan against the default sequential scan.

### 13. Explain parallel query in PostgreSQL. What is a `Gather` node in EXPLAIN? What settings control parallelism: `max_parallel_workers_per_gather`, `min_parallel_table_scan_size`, `parallel_tuple_cost`?
Parallel query allows PostgreSQL to utilize multiple CPU cores to execute a single query, dividing the workload (like table scans, hash joins, or aggregations) among background worker processes to drastically reduce execution time on massive datasets. In an `EXPLAIN` plan, a `Gather` (or `Gather Merge`) node indicates the point where the main query process collects and combines the partial results produced by the background parallel workers. 
Parallelism is strictly controlled by configuration settings:
- `max_parallel_workers_per_gather`: The hard limit on how many workers can be assigned to a single `Gather` node (default 2). Setting it to 0 disables parallel query entirely.
- `min_parallel_table_scan_size`: The minimum size a table must be (default 8MB) before the planner will even consider a parallel scan, preventing the overhead of worker spawning on tiny tables.
- `parallel_tuple_cost`: The planner's estimated cost (default 0.1) of transferring a single row from a parallel worker to the Gather node via shared memory, balancing the benefit of parallelism against IPC overhead.

### 14. What is a CTE in PostgreSQL and how does the `MATERIALIZED` keyword affect optimization? When is a CTE an "optimization fence" and what changed in PostgreSQL 12 regarding CTE inlining?
A CTE (Common Table Expression), created using the `WITH` clause, is a temporary named result set used to organize complex queries into readable, modular blocks. Historically (before PG 12), all CTEs were "optimization fences." This meant the query planner evaluated the CTE completely independently, materialized its full result set into memory/disk, and then the outer query scanned that materialized result. The planner could not push down filters (like `WHERE` clauses) from the outer query into the CTE, often resulting in terrible performance when only a few rows were needed. 
In PostgreSQL 12 and later, CTEs that are referenced only once and have no side-effects (like `INSERT/UPDATE`) are automatically inlined. The planner merges them into the main query tree, allowing aggressive optimization and filter push-down. You can override this behavior using the `MATERIALIZED` keyword (e.g., `WITH my_cte AS MATERIALIZED (...)`), intentionally forcing the CTE to act as an optimization fence. This is useful when you explicitly want to calculate an expensive subquery exactly once and reuse the cached result multiple times.

### 15. What does `pg_stat_statements` track? How do you enable it? Write the exact SQL query to find the top 10 slowest queries by mean execution time. What is the difference between `mean_exec_time` and `total_exec_time` for identifying optimization targets?
`pg_stat_statements` is a critical extension that tracks execution statistics (time, calls, memory usage, I/O) for all SQL statements executed by a server, normalized by parameterizing literal values to group identical queries together. You enable it by adding `shared_preload_libraries = 'pg_stat_statements'` to `postgresql.conf`, restarting the server, and then running `CREATE EXTENSION pg_stat_statements;` in the database.
**Query for top 10 slowest queries by mean execution time:**
```sql
SELECT query, calls, total_exec_time, mean_exec_time 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;
```
The difference between `mean_exec_time` and `total_exec_time` is crucial for identifying optimization targets. `mean_exec_time` highlights queries that are inherently slow per execution (e.g., a massive nightly report taking 5 minutes). `total_exec_time` (calls × mean_exec_time) highlights the queries consuming the most cumulative database resources. A query with a fast `mean_exec_time` of 10ms but executed 1,000,000 times a day (`total_exec_time` = 10,000s) is often a higher-priority optimization target than a 5-minute report run once.
