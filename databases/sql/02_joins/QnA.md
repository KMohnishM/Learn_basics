# Q&A: SQL Joins

**1. What is the difference between INNER JOIN and LEFT JOIN? Give an example where the results differ.**
An `INNER JOIN` returns only the rows where there is a match in both the left and right tables based on the join condition. A `LEFT JOIN` returns all rows from the left table, regardless of whether a match exists in the right table; if no match exists, the columns from the right table will contain `NULL` values.
*Example:* 
```sql
-- INNER JOIN: Only returns customers who actually placed an order.
SELECT c.name, o.order_id FROM customers c INNER JOIN orders o ON c.customer_id = o.customer_id;

-- LEFT JOIN: Returns ALL customers. If a customer has no orders, order_id is NULL.
SELECT c.name, o.order_id FROM customers c LEFT JOIN orders o ON c.customer_id = o.customer_id;
```

**2. How do you find rows in table A that have NO matching rows in table B?**
You use an anti-join pattern. You perform a `LEFT JOIN` from table A to table B and then use the `WHERE` clause to filter for rows where the primary key (or any non-nullable column) of table B `IS NULL`.
```sql
SELECT c.name
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL;
```

**3. What is a SELF JOIN? Write a query to find each employee and their manager's name.**
A `SELF JOIN` is a regular join where a table is joined to itself. This requires using table aliases to distinguish between the two instances of the table. It is commonly used for hierarchical data (like a tree structure) or comparing rows within the same dataset.
```sql
SELECT 
    e.name AS employee,
    m.name AS manager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.emp_id;
```

**4. What is a CROSS JOIN? Give a legitimate real-world use case.**
A `CROSS JOIN` produces a Cartesian product, meaning it pairs every row in the first table with every row in the second table.
*Real-world use case:* Generating a dense "spine" of dates and entities for reporting. For example, if you need a report showing sales by day for every product—even on days when a product had 0 sales—you would `CROSS JOIN` a table of calendar dates with a table of products, and then `LEFT JOIN` the actual sales data onto that combination.

**5. What is a FULL OUTER JOIN? When would you use it?**
A `FULL OUTER JOIN` returns all rows from both tables. When a match exists, the result row contains data from both tables. When a row has no match in the other table, the missing side contains `NULL` values.
*Use case:* Data reconciliation. If you are migrating a legacy customer database to a new system and want to find records that exist in the old system but not the new, OR exist in the new but not the old, a full outer join easily surfaces both discrepancies in one query.

**6. What is the N+1 query problem? How do JOINs solve it?**
The N+1 query problem is a performance issue commonly caused by ORMs (Object-Relational Mappers). It happens when the application executes 1 query to fetch a list of N parent records (e.g., 100 customers), and then executes N additional queries in a loop to fetch the child records for each parent (e.g., 100 separate queries for each customer's orders).
*Solution:* A single `JOIN` solves this by retrieving the parent and child data together in one database round-trip.
```sql
SELECT c.name, o.amount 
FROM customers c 
LEFT JOIN orders o ON c.customer_id = o.customer_id;
```

**7. Why might a JOIN produce more rows than expected? How do you fix it?**
A join produces more rows (a phenomenon called "fan-out" or Cartesian explosion) when there is a one-to-many or many-to-many relationship and you join them without realizing it. If 1 row in the left table matches 5 rows in the right table, the join will output 5 rows.
*Fix:* 
1. If you just need data from the right side aggregated, aggregate it first (using a CTE) before joining.
2. If you only need to check for *existence*, use `EXISTS` or `IN` instead of a `JOIN`.
3. Ensure your join condition includes all necessary columns to uniquely identify relationships.

**8. What is the difference between JOIN ON and JOIN USING?**
`JOIN ON` specifies the exact boolean condition for the join, allowing for different column names or complex logic (e.g., `ON a.id = b.a_id AND a.status = 'active'`).
`JOIN USING` is syntactical sugar that can be used when the columns you are joining on have the exact same name in both tables. It outputs the join column only once.
```sql
-- Using ON
SELECT * FROM employees e JOIN departments d ON e.dept_id = d.dept_id;
-- Using USING
SELECT * FROM employees JOIN departments USING (dept_id);
```

**9. Can you join on a non-equality condition? Give an example.**
Yes, these are called non-equi joins. You can use operators like `<`, `>`, `BETWEEN`, or `<>`.
*Example:* Finding orders where the order amount falls within a specific discount tier (assuming a `discount_tiers` table with `min_val` and `max_val`).
```sql
SELECT o.order_id, d.tier_name
FROM orders o
JOIN discount_tiers d 
    ON o.amount >= d.min_val AND o.amount <= d.max_val;
```

**10. Write a query using three table JOINs to find order details including customer name and product name.**
```sql
SELECT 
    o.order_id,
    c.name AS customer_name,
    p.name AS product_name,
    o.amount
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN products p ON o.product_id = p.product_id;
```

**11. What is the difference between WHERE and ON when filtering in a LEFT JOIN?**
This is critical. 
Filtering in the `ON` clause happens *before* the join resolves the outer logic. For a `LEFT JOIN`, if a condition in the `ON` clause fails, the left row is *still kept* in the result, but the right-side columns become `NULL`.
Filtering in the `WHERE` clause happens *after* the join is complete. If a `WHERE` condition fails, the entire row is discarded.
```sql
-- Keeps ALL customers. Only attaches order data if it's over $100.
SELECT * FROM customers c LEFT JOIN orders o ON c.customer_id = o.customer_id AND o.amount > 100;

-- Discards customers who don't have an order > $100. (Effectively turns it into an INNER JOIN).
SELECT * FROM customers c LEFT JOIN orders o ON c.customer_id = o.customer_id WHERE o.amount > 100;
```

**12. How does the order of tables in a JOIN affect performance?**
Historically and theoretically, the table order matters because the database engine must decide which table to scan first (the driving table). However, modern cost-based query optimizers (like in PostgreSQL and MySQL) analyze table statistics and will dynamically reorder `INNER JOIN`s to find the most efficient execution plan regardless of the order you wrote them. 
For `LEFT/RIGHT/FULL OUTER JOIN`s, the logical order *must* be maintained to guarantee correct results, so the optimizer has less freedom to reorder.

**13. What is a hash join vs a nested loop join vs a merge join? When does the query planner use each?**
- **Nested Loop:** Iterates row-by-row through the outer table, looking up matches in the inner table (usually via an index). Best for small datasets or highly selective queries.
- **Hash Join:** Hashes the smaller table into memory, then scans the larger table probing the hash table. Best for large, unsorted datasets joined on equality.
- **Merge Join:** Requires both tables to be sorted on the join key first, then zips them together. Best for very large datasets that are already sorted (e.g., via a B-Tree index).

**14. Write a query to find customers who placed orders in both January and February of this year.**
Using joins (specifically an `INNER JOIN` on the same table, which is a self-join of sorts on the child table):
```sql
SELECT c.name
FROM customers c
JOIN orders jan ON c.customer_id = jan.customer_id 
    AND EXTRACT(MONTH FROM jan.order_date) = 1
JOIN orders feb ON c.customer_id = feb.customer_id 
    AND EXTRACT(MONTH FROM feb.order_date) = 2
GROUP BY c.name;
```
*(Note: INTERSECT or EXISTS are often better ways to write this conceptually, but the JOIN method works and is a common interview answer).*

**15. How would you rewrite a correlated subquery as a JOIN?**
A correlated subquery executes once per row and is notoriously slow.
*Correlated Subquery:*
```sql
SELECT c.name,
    (SELECT SUM(amount) FROM orders o WHERE o.customer_id = c.customer_id) as total_spent
FROM customers c;
```
*Rewritten as a JOIN (with a CTE for clean aggregation):*
```sql
WITH OrderTotals AS (
    SELECT customer_id, SUM(amount) as total_spent
    FROM orders
    GROUP BY customer_id
)
SELECT c.name, ot.total_spent
FROM customers c
LEFT JOIN OrderTotals ot ON c.customer_id = ot.customer_id;
```
