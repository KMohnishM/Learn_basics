# QnA: SQL Mastery

## 1. Explain the window function frame clause. What is the difference between ROWS and RANGE?
The window function frame clause defines the exact subset of rows within a partition that the window function should operate on for the current row. It allows for moving calculations like rolling averages.
`ROWS BETWEEN 6 PRECEDING AND CURRENT ROW` counts exactly physical rows. It takes the current row and the 6 rows immediately preceding it in the sorted partition, regardless of their actual values.
`RANGE BETWEEN INTERVAL '7 days' PRECEDING AND CURRENT ROW` looks at the logical value of the `ORDER BY` column (which must be a date/timestamp). It includes all rows whose date is within the past 7 days from the current row's date.
Example with date gaps in the data:
Dates in data: Jan 1, Jan 2, Jan 8.
For the row on Jan 8:
Using `ROWS 6 PRECEDING`: It will include Jan 8, Jan 2, and Jan 1 (the last 3 physical rows available).
Using `RANGE INTERVAL '7 days' PRECEDING`: It evaluates (Jan 8 - 7 days) = Jan 1. It will include Jan 8, Jan 2, and Jan 1.
If the dates were Jan 1, Jan 7, Jan 8:
For Jan 8, `ROWS 2 PRECEDING` includes Jan 8, Jan 7, Jan 1.
For Jan 8, `RANGE '7 days' PRECEDING` includes Jan 8, Jan 7, and Jan 1 (since Jan 1 is exactly 7 days prior).
However, if the dates were Jan 1, Jan 5, Jan 9:
For Jan 9, `ROWS 2 PRECEDING` includes Jan 9, Jan 5, Jan 1.
For Jan 9, `RANGE '7 days' PRECEDING` evaluates to dates >= Jan 2. It will only include Jan 9 and Jan 5. It strictly respects the logical time window, while ROWS blindly takes adjacent physical rows.

## 2. What is the difference between ROW_NUMBER(), RANK(), and DENSE_RANK() when there are ties?
These three window functions assign a sequential integer to rows within a partition, but they handle ties (rows with identical values in the `ORDER BY` clause) fundamentally differently.
Consider the input values ordered descending: 100, 95, 95, 80, 80, 70.
1. `ROW_NUMBER()` assigns a strictly unique, incrementing integer to every single row, ignoring ties completely. The order of tied rows is non-deterministic unless additional sorting criteria are provided.
   Output: 1, 2, 3, 4, 5, 6
2. `RANK()` assigns the exact same rank to tied rows, but it leaves gaps in the ranking sequence afterward. The next rank assigned will be the total number of preceding rows plus one.
   Output: 1, 2, 2, 4, 4, 6 (Notice that ranks 3 and 5 are completely skipped).
3. `DENSE_RANK()` also assigns the same rank to tied rows, but it does NOT leave gaps in the sequence. The next rank is always the immediately following integer.
   Output: 1, 2, 2, 3, 3, 4.
Choosing between them depends on the business requirement. If you need exactly a "Top 3" list regardless of ties, `ROW_NUMBER` is used. If multiple people can tie for 1st place and the next person should be 2nd, use `DENSE_RANK`.

## 3. Explain LAG() and LEAD(). Write a complete SQL query that calculates month-over-month revenue growth.
`LAG()` and `LEAD()` are positional window functions that allow a query to access data from a preceding (LAG) or following (LEAD) row in the same result set without requiring a complex self-join. They are essential for comparative analytics.
`LAG(column, offset, default)` returns the value of the column `offset` rows before the current row. `LEAD()` does the opposite.
Here is a complete SQL query for month-over-month (MoM) revenue growth percentage:
```sql
WITH MonthlyRevenue AS (
    SELECT
        DATE_TRUNC('month', order_date) AS month,
        SUM(order_total) AS revenue
    FROM orders
    GROUP BY DATE_TRUNC('month', order_date)
)
SELECT
    month,
    revenue,
    LAG(revenue, 1) OVER (ORDER BY month) AS prev_month_revenue,
    CASE
        WHEN LAG(revenue, 1) OVER (ORDER BY month) IS NULL THEN NULL
        ELSE ((revenue - LAG(revenue, 1) OVER (ORDER BY month)) / LAG(revenue, 1) OVER (ORDER BY month)) * 100.0
    END AS mom_growth_percentage
FROM MonthlyRevenue
ORDER BY month;
```
This query correctly handles the first month by explicitly checking for NULL from the LAG function and outputting NULL for growth, preventing a division by zero or a false growth calculation.

## 4. Explain the recursive CTE structure. How does PostgreSQL prevent infinite recursion?
A Recursive Common Table Expression (CTE) is used to traverse hierarchical or graph data (like trees, org charts, or bill of materials).
It consists of three mandatory parts:
1. Anchor Member: A non-recursive baseline query that produces the initial set of rows.
2. `UNION ALL`: The operator bridging the base and the recursive steps.
3. Recursive Member: A query that references the CTE's own name. It executes repeatedly, each time taking the results of the *previous* iteration as its input, until it returns an empty set.
PostgreSQL does not strictly prevent infinite recursion automatically unless told to. A poorly written CTE will run until it consumes all memory. However, you can enforce termination using the `CYCLE` clause (introduced in newer versions) or by hardcoding a depth limit in the WHERE clause.
Org chart query returning depth and path:
```sql
WITH RECURSIVE OrgChart AS (
    -- Anchor: Find the CEO (no manager)
    SELECT emp_id, name, manager_id, 1 AS depth, name::TEXT AS path
    FROM employees WHERE manager_id IS NULL

    UNION ALL

    -- Recursive: Find direct reports of the current level
    SELECT e.emp_id, e.name, e.manager_id, o.depth + 1, o.path || ' -> ' || e.name
    FROM employees e
    INNER JOIN OrgChart o ON e.manager_id = o.emp_id
    -- Optional termination safety: WHERE o.depth < 100
)
SELECT * FROM OrgChart ORDER BY path;
```

## 5. What are GROUPING SETS, ROLLUP, and CUBE?
These are advanced `GROUP BY` extensions that allow computing multiple levels of aggregation in a single query, drastically improving performance over `UNION ALL` approaches.
`GROUPING SETS` allows explicitly specifying the exact combinations of columns you want to group by.
`ROLLUP` generates hierarchical grouping sets. It is perfect for subtotals and grand totals along a dimensional hierarchy.
Given `GROUP BY ROLLUP(year, quarter, month)`, PostgreSQL computes exactly 4 groupings:
1. (year, quarter, month) -- Lowest level detail
2. (year, quarter) -- Subtotals per quarter
3. (year) -- Subtotals per year
4. () -- Grand total for everything.
It "rolls up" from right to left based on the specified order.
`CUBE`, on the other hand, generates all mathematically possible combinations of the specified columns.
Given `GROUP BY CUBE(year, quarter, month)`, it computes 2^3 = 8 groupings:
1. (year, quarter, month)
2. (year, quarter)
3. (year, month)
4. (quarter, month)
5. (year)
6. (quarter)
7. (month)
8. () -- Grand total
CUBE is heavily used in cross-tabulation reports where users might slice data by any arbitrary combination of dimensions.

## 6. Explain the FILTER clause in window functions and aggregates.
The `FILTER (WHERE condition)` clause is a powerful Postgres extension to standard SQL aggregates. It allows an aggregate function to only process rows that satisfy a specific condition, effectively acting as an inline conditional aggregate.
It is vastly superior to the older `SUM(CASE WHEN condition THEN 1 ELSE 0 END)` pattern because it is more readable, standard-compliant, and often optimized better by the execution engine, particularly for complex aggregates like array aggregations or percentiles.
It can be applied to standard `GROUP BY` aggregates and window functions.
Query calculating order statuses in a single table scan:
```sql
SELECT
    customer_id,
    COUNT(order_id) AS total_orders,
    COUNT(order_id) FILTER (WHERE status = 'pending') AS pending_orders,
    COUNT(order_id) FILTER (WHERE status = 'completed') AS completed_orders,
    COUNT(order_id) FILTER (WHERE status = 'cancelled') AS cancelled_orders
FROM orders
GROUP BY customer_id;
```
This executes incredibly fast as it scans the `orders` table exactly once, evaluating the filters on the fly during aggregation, rather than executing four separate subqueries or multiple joins.

## 7. What is the difference between JSON and JSONB storage in PostgreSQL?
PostgreSQL offers two distinct JSON types.
`JSON` stores an exact character-by-character copy of the input text. It preserves whitespace, the exact order of keys, and duplicate keys. However, it requires re-parsing the text every time a function operates on it, making queries slow.
`JSONB` (JSON Binary) stores data in a decomposed binary format. Whitespace is removed, object keys are sorted, and duplicate keys keep only the last value. The massive advantage is that JSONB does not require re-parsing. It is heavily optimized for fast processing and indexing.
Operators:
- `->` extracts a JSON object/array field by key or index, returning a JSON type.
- `->>` extracts the field but returns it as SQL `TEXT`.
- `#>>` extracts a text value at a specific path using a text array (e.g., `data #>> '{user, profile, name}'`).
- `@>` is the containment operator. `A @> B` asks "Does JSONB A contain the top-level structure and values of JSONB B?".
A GIN (Generalized Inverted Index) on a JSONB column is absolutely necessary when you are querying deeply into the JSON structure across millions of rows, specifically when using the `@>`, `?`, `?&`, or `?|` containment and key-existence operators. B-Tree indexes cannot efficiently index the internal structure of JSONB documents.

## 8. What is INSERT ... ON CONFLICT DO UPDATE (upsert)?
The `INSERT ... ON CONFLICT` statement is PostgreSQL's implementation of an "upsert" (update or insert). It allows a single, atomic statement to attempt an insertion, and if a unique constraint or primary key violation occurs, it seamlessly falls back to updating the conflicting row instead of throwing an error.
The `EXCLUDED` pseudo-table represents the row that was proposed for insertion but was rejected due to the conflict. It is used in the `DO UPDATE` clause to apply the new values.
Example for a product inventory system where receiving a shipment adds to the stock quantity:
```sql
INSERT INTO inventory (product_id, quantity_in_stock, last_restocked)
VALUES (1042, 50, CURRENT_DATE)
ON CONFLICT (product_id)
DO UPDATE SET
    -- Add the new shipment quantity to the existing stock
    quantity_in_stock = inventory.quantity_in_stock + EXCLUDED.quantity_in_stock,
    -- Update the restock date to the new proposed date
    last_restocked = EXCLUDED.last_restocked;
```
This is critical for high-concurrency environments because it completely avoids race conditions that occur with a "SELECT then INSERT/UPDATE" application-level transaction logic.

## 9. What does DELETE ... RETURNING do? Write an atomic archive query.
Standard SQL DML statements (INSERT, UPDATE, DELETE) typically only return the number of rows affected. PostgreSQL's `RETURNING` clause forces the statement to return the actual data of the rows that were modified or deleted, identical to a `SELECT` output.
When used with `DELETE`, it returns the exact snapshot of the rows just before they were removed from the table.
This is incredibly powerful for atomic data movement tasks. By combining a CTE with `DELETE ... RETURNING`, you can move rows between tables without ever locking the rows in a transaction block to prevent race conditions.
Archiving expired sessions atomically:
```sql
WITH deleted_sessions AS (
    DELETE FROM active_sessions
    WHERE expires_at < NOW()
    RETURNING session_id, user_id, created_at, expires_at, 'expired_naturally' AS termination_reason
)
INSERT INTO sessions_archive (session_id, user_id, created_at, expires_at, reason)
SELECT session_id, user_id, created_at, expires_at, termination_reason
FROM deleted_sessions;
```
This entire block acts as a single statement atomic operation. No other transaction can modify those rows between the read and the delete, guaranteeing zero data loss during archival.

## 10. What is the MERGE statement introduced in PostgreSQL 15?
The SQL-standard `MERGE` statement provides a comprehensive way to conditionally insert, update, or delete rows in a target table based on a join with a source table (often a staging or temporary table).
While `INSERT ... ON CONFLICT` handles upserts purely based on unique constraint violations, `MERGE` is vastly more flexible. It evaluates arbitrary boolean conditions and can handle `DELETE` actions, which ON CONFLICT cannot do.
Example: Syncing a live `products` table from a `staging_products` import:
```sql
MERGE INTO products AS target
USING staging_products AS source
ON target.product_id = source.product_id
-- Match found, and source says it's deleted
WHEN MATCHED AND source.is_deleted = true THEN
    DELETE
-- Match found, and prices differ
WHEN MATCHED AND target.price != source.price THEN
    UPDATE SET price = source.price, updated_at = NOW()
-- No match found, new product
WHEN NOT MATCHED THEN
    INSERT (product_id, name, price)
    VALUES (source.product_id, source.name, source.price);
```
This performs a full synchronization (ETL upsert/delete) in one pass, greatly simplifying data warehousing pipelines without needing multiple standalone statements.

## 11. Explain FIRST_VALUE() and LAST_VALUE(). Why does LAST_VALUE() require framing?
`FIRST_VALUE(col)` and `LAST_VALUE(col)` are window functions that return the value of the specified column from the very first and very last row of the current window frame, respectively.
They are heavily dependent on the default framing rules of window functions.
If you use an `ORDER BY` clause in your window function, the default frame is `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`.
For `FIRST_VALUE()`, this default works perfectly. The start of the frame is the beginning of the partition, which contains the true "first value".
However, for `LAST_VALUE()`, the default frame is disastrous. Because the frame ends at the `CURRENT ROW`, the "last value" in the frame will always just be the value of the *current row itself*. It will not look ahead to the true end of the partition.
To get the actual last value of the entire partition, you must explicitly expand the frame to the end using:
`OVER (PARTITION BY ... ORDER BY ... ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)`.
This forces the engine to look at the entire partition when evaluating `LAST_VALUE()` for any given row, producing the expected true last value result.

## 12. What is PERCENT_RANK() vs CUME_DIST()? Write a query for the top 25%.
Both functions calculate the relative rank of a row within a partition, expressed as a decimal between 0 and 1.
`PERCENT_RANK()` calculates the percentage of rows that rank *strictly lower* than the current row. Formula: (rank - 1) / (total_rows - 1). The first row is always 0.0.
`CUME_DIST()` (Cumulative Distribution) calculates the percentage of rows that rank *lower than or equal to* the current row. Formula: row_number / total_rows. The last row is always 1.0.
Query for top 25% of products by revenue:
```sql
WITH ProductRanks AS (
    SELECT
        product_name,
        revenue,
        PERCENT_RANK() OVER (ORDER BY revenue DESC) AS pct_rank
    FROM product_sales
)
SELECT product_name, revenue, pct_rank
FROM ProductRanks
WHERE pct_rank <= 0.25; -- Top 25%
```
Explanation of the threshold value: By ordering `DESC`, the highest revenue product gets rank 1, and its `PERCENT_RANK` is 0.0. A `pct_rank` of 0.25 means that exactly 25% of the items are ranked strictly "lower" (meaning higher revenue in descending order) than the current item. Thus, `pct_rank <= 0.25` captures the top quartile of performers accurately.

## 13. How does generate_series() work? Write a query generating dates.
`generate_series(start, stop, step)` is a set-returning function (SRF) in PostgreSQL that dynamically generates a continuous series of values (integers, timestamps, or dates) directly in memory, acting as a virtual table.
It is an essential tool for gap-filling in reports. When reporting on daily sales, days with zero sales won't appear in the `orders` table. `generate_series` creates a complete calendar to LEFT JOIN against.
Query for 2024 daily sales, including zero-sale days:
```sql
WITH Calendar AS (
    SELECT generate_series(
        '2024-01-01'::DATE,
        '2024-12-31'::DATE,
        '1 day'::INTERVAL
    )::DATE AS report_date
)
SELECT
    c.report_date,
    COALESCE(SUM(s.amount), 0) AS total_sales
FROM Calendar c
LEFT JOIN sales s
    ON c.report_date = DATE(s.sale_timestamp)
GROUP BY c.report_date
ORDER BY c.report_date;
```
Without the calendar CTE, missing days would simply vanish from the report. The `COALESCE` ensures NULL sums become 0 for those days with no sales records.

## 14. What is the WITHIN GROUP ordered-set aggregate?
The `WITHIN GROUP` clause is used with ordered-set aggregate functions. Unlike standard aggregates (like SUM or MAX) which don't care about row order, ordered-set functions mathematically require the input data to be sorted to calculate their results correctly.
The most common use cases are statistical medians, percentiles, and mode calculations.
Query to find the exact median order value:
```sql
SELECT
    category,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY order_value) AS median_value
FROM orders
GROUP BY category;
```
`PERCENTILE_CONT(0.5)` computes the continuous 50th percentile (the median). If there is an even number of rows, it interpolates the average of the two middle values.
Why `AVG()` is not equivalent: The mean (`AVG`) is highly sensitive to outliers. In e-commerce, one massive $10,000 enterprise order will drastically skew the average upward, making it unrepresentative of a typical customer's order. The median simply finds the middle value, completely ignoring the magnitude of extreme outliers, providing a much more accurate picture of normal behavior for skewed distributions.

## 15. What is NTILE()? Write a query dividing customers into quartiles.
`NTILE(n)` is a window function that distributes the rows in an ordered partition into a specified number of roughly equal groups or "buckets", numbering them from 1 to `n`.
It is heavily used in statistical binning, RFM analysis (Recency, Frequency, Monetary), and tier assignments. If the total number of rows isn't perfectly divisible by `n`, the larger buckets are placed at the beginning.
Query for customer spending quartiles:
```sql
WITH CustomerTiers AS (
    SELECT
        customer_id,
        total_spend,
        NTILE(4) OVER (ORDER BY total_spend DESC) AS quartile
    FROM customer_spending
)
SELECT
    CASE quartile
        WHEN 1 THEN 'Platinum'
        WHEN 2 THEN 'Gold'
        WHEN 3 THEN 'Silver'
        WHEN 4 THEN 'Bronze'
    END AS spending_tier,
    COUNT(customer_id) AS customer_count,
    ROUND(AVG(total_spend), 2) AS average_spend
FROM CustomerTiers
GROUP BY quartile, spending_tier
ORDER BY quartile;
```
In this query, `NTILE(4)` ranks all customers from highest to lowest spend and slices them into exactly four groups. The top 25% get bucket 1 (Platinum), the next get 2 (Gold), and so on. We then aggregate on those dynamically generated buckets to show the count and average spend per quartile.
