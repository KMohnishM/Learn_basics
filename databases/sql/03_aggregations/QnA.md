# Aggregations QnA

**1. What is the difference between COUNT(*), COUNT(col), and COUNT(DISTINCT col)?**

`COUNT(*)` counts the total number of rows in the table or group, including rows with NULL values in any column. It essentially counts the cardinality of the result set. `COUNT(col)` counts the number of non-NULL values present in the specified column `col` for the given group. `COUNT(DISTINCT col)` counts the number of unique, non-NULL values in the specified column `col`.

**2. What is the difference between WHERE and HAVING? Give an example where they cannot be swapped.**

`WHERE` filters individual rows before aggregation occurs. It cannot contain aggregate functions. `HAVING` filters aggregated groups after the `GROUP BY` clause has been processed. It is designed to work with aggregate functions. 
Example where they cannot be swapped:
`SELECT dept_id, SUM(salary) FROM employees GROUP BY dept_id HAVING SUM(salary) > 500000;`
You cannot move `SUM(salary) > 500000` to the `WHERE` clause because `SUM` is an aggregate function and `WHERE` evaluates row-by-row before the sum is known.

**3. Write a query to find the second highest salary in the employees table.**

```sql
SELECT MAX(salary) AS second_highest_salary
FROM employees
WHERE salary < (SELECT MAX(salary) FROM employees);
```
Alternatively, using `LIMIT` and `OFFSET` (PostgreSQL/MySQL):
```sql
SELECT DISTINCT salary
FROM employees
ORDER BY salary DESC
LIMIT 1 OFFSET 1;
```

**4. Write a pivot query: show total sales amount per month for each product category as columns.**

```sql
SELECT 
    EXTRACT(MONTH FROM o.order_date) AS sales_month,
    SUM(CASE WHEN p.category = 'Electronics' THEN o.amount ELSE 0 END) AS electronics_sales,
    SUM(CASE WHEN p.category = 'Books' THEN o.amount ELSE 0 END) AS books_sales,
    SUM(CASE WHEN p.category = 'Clothing' THEN o.amount ELSE 0 END) AS clothing_sales
FROM orders o
JOIN products p ON o.product_id = p.product_id
GROUP BY EXTRACT(MONTH FROM o.order_date)
ORDER BY sales_month;
```

**5. What is ROLLUP? Write a query using it to get sales by region with subtotals.**

`ROLLUP` is an extension to the `GROUP BY` clause that generates hierarchical subtotals and a grand total. It aggregates data moving from right to left across the specified grouping columns.

```sql
-- Assuming a region column in customers
SELECT 
    c.country,
    c.name AS customer_name,
    SUM(o.amount) AS total_sales
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
GROUP BY ROLLUP(c.country, c.name);
```
This generates rows for each customer, subtotals for each country, and a grand total.

**6. How do you count only rows that meet a condition inside an aggregation?**

In standard SQL (and MySQL), you use a `CASE` statement inside the `SUM` or `COUNT` function:
```sql
SELECT SUM(CASE WHEN status = 'shipped' THEN 1 ELSE 0 END) FROM orders;
-- or
SELECT COUNT(CASE WHEN status = 'shipped' THEN 1 END) FROM orders;
```
In PostgreSQL, the preferred and cleaner method is the `FILTER` clause:
```sql
SELECT COUNT(*) FILTER (WHERE status = 'shipped') FROM orders;
```

**7. Why can you not use a column alias in a HAVING clause in some databases?**

The logical execution order of a SQL query processes `HAVING` before `SELECT`. Since aliases are defined in the `SELECT` clause, they technically do not exist when the `HAVING` clause is evaluated. Standard SQL strictly enforces this. However, some databases (like PostgreSQL and MySQL) extend the standard to allow aliases in `GROUP BY` and `HAVING` for convenience.

**8. What is the "AVG of AVGs" problem? Give an example.**

The "AVG of AVGs" problem occurs when you attempt to calculate an overall average by taking the average of pre-calculated subset averages. This results in an incorrect mathematical average because it gives equal weight to all groups, regardless of the number of items in each group (losing the denominator weighting).
Example: If Dept A has 1 employee earning $100k, and Dept B has 9 employees earning $50k each.
Average of averages: `(100k + 50k) / 2 = $75k`.
True overall average: `(100k + (9 * 50k)) / 10 = $55k`.

**9. Write a query to find departments where the average salary is above the company average.**

```sql
SELECT dept_id, AVG(salary) AS dept_avg
FROM employees
GROUP BY dept_id
HAVING AVG(salary) > (SELECT AVG(salary) FROM employees);
```

**10. How do you find the most recent order for each customer in a single query?**

```sql
SELECT customer_id, MAX(order_date) AS most_recent_order
FROM orders
GROUP BY customer_id;
```
To get the full row details, you would typically use a window function (covered in later modules) or join back:
```sql
SELECT o1.*
FROM orders o1
JOIN (
    SELECT customer_id, MAX(order_date) as max_date
    FROM orders
    GROUP BY customer_id
) o2 ON o1.customer_id = o2.customer_id AND o1.order_date = o2.max_date;
```

**11. What does GROUP BY 1, 2 mean? What are the risks?**

`GROUP BY 1, 2` is shorthand for grouping by the first and second columns defined in the `SELECT` list. 
Risks: It makes the query brittle. If you add, remove, or reorder columns in the `SELECT` clause, the `GROUP BY` clause silently changes its behavior, potentially introducing subtle logic bugs. It is generally considered poor practice for production code, though convenient for ad-hoc querying.

**12. How does STRING_AGG work? Write a query to list all product names per category as a comma-separated string.**

`STRING_AGG` (in PostgreSQL) concatenates string values across rows within a group into a single scalar value, separated by a specified delimiter.

```sql
SELECT 
    category,
    STRING_AGG(name, ', ' ORDER BY name) AS product_list
FROM products
GROUP BY category;
```

**13. What is GROUPING SETS and when would you use it over ROLLUP?**

`GROUPING SETS` allows you to explicitly define the exact sets of columns you want to group by within a single query. You use it over `ROLLUP` (which dictates a specific hierarchical order) or `CUBE` (which generates all combinations) when you only need specific aggregates. For example, if you want total sales by product and total sales by customer, but *not* the intersection of product and customer, `GROUPING SETS` is more efficient.

**14. Write a query to count active users and inactive users in one query without a subquery.**

```sql
SELECT 
    COUNT(CASE WHEN is_active = true THEN 1 END) AS active_count,
    COUNT(CASE WHEN is_active = false THEN 1 END) AS inactive_count
FROM employees;
```
Or using PostgreSQL `FILTER`:
```sql
SELECT 
    COUNT(*) FILTER (WHERE is_active = true) AS active_count,
    COUNT(*) FILTER (WHERE is_active = false) AS inactive_count
FROM employees;
```

**15. Why might COUNT(DISTINCT col) be slow? What are the alternatives for approximate counting?**

`COUNT(DISTINCT col)` is slow because the database engine must maintain state to check for uniqueness—usually by sorting the data or building a hash table in memory. For billions of rows, this requires significant memory and CPU.
Alternatives involve probabilistic data structures that estimate the distinct count with a known error margin while using very little memory. The most common alternative is HyperLogLog (HLL), accessible via extensions in PostgreSQL (`postgresql-hll`) or natively in systems like Redis or BigQuery.
