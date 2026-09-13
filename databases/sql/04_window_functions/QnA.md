# Q&A: Window Functions

**1. What is the difference between ROW_NUMBER(), RANK(), and DENSE_RANK()? Give an example with ties.**
- `ROW_NUMBER()`: Assigns a strictly unique, sequential integer to every row (1, 2, 3, 4). Ties are assigned arbitrary distinct numbers.
- `RANK()`: Assigns the same rank to identical values, but leaves a gap in the ranking sequence afterward (1, 2, 2, 4).
- `DENSE_RANK()`: Assigns the same rank to identical values, but does not leave gaps (1, 2, 2, 3).
*Example:* If three employees have salaries 90k, 90k, and 80k:
`ROW_NUMBER()` gives 1, 2, 3.
`RANK()` gives 1, 1, 3.
`DENSE_RANK()` gives 1, 1, 2.

**2. What is the difference between window functions and GROUP BY?**
`GROUP BY` collapses all rows that share the same grouping key into a single summary row. You lose the individual row details. Window functions calculate aggregate values for a group of rows but preserve every original row in the output. The calculation is simply appended as a new column to the existing rows.

**3. Write a query to find the top 3 selling products in each category.**
```sql
WITH RankedProducts AS (
    SELECT 
        product_id, 
        name, 
        category, 
        price,
        DENSE_RANK() OVER (PARTITION BY category ORDER BY price DESC) as rnk
    FROM products
)
SELECT * FROM RankedProducts WHERE rnk <= 3;
```

**4. How do you calculate month-over-month percentage change using window functions?**
You use `LAG()` to get the previous month's total, then calculate the difference.
```sql
WITH MonthlySales AS (
    SELECT DATE_TRUNC('month', order_date) as month, SUM(amount) as total
    FROM orders GROUP BY DATE_TRUNC('month', order_date)
),
SalesWithLag AS (
    SELECT month, total, LAG(total) OVER (ORDER BY month) as prev_total
    FROM MonthlySales
)
SELECT month, total, prev_total, 
       ((total - prev_total) / prev_total) * 100 as pct_change
FROM SalesWithLag;
```

**5. What is LAG() used for? Write an example finding the difference between consecutive rows.**
`LAG()` allows you to look backwards in the result set to retrieve a value from a previous row without using a self-join.
```sql
SELECT 
    order_id, 
    order_date, 
    amount,
    LAG(amount, 1) OVER (ORDER BY order_date) as prev_amount,
    amount - LAG(amount, 1) OVER (ORDER BY order_date) as diff_from_prev
FROM orders;
```

**6. Why does LAST_VALUE() often give unexpected results? How do you fix it?**
When you use an `ORDER BY` inside the `OVER()` clause, the default window frame is `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`. Therefore, `LAST_VALUE()` only looks up to the current row, returning the current row's value instead of the absolute last value in the partition. To fix this, you must explicitly expand the window frame:
`LAST_VALUE(col) OVER (PARTITION BY x ORDER BY y ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)`.

**7. What is a window frame? Explain ROWS vs RANGE mode.**
A window frame specifies the exact subset of rows within a partition that a window function should evaluate for the current row.
- `ROWS`: Operates on physical row counts. `1 PRECEDING` means strictly the single row physically preceding the current row.
- `RANGE`: Operates on logical values of the `ORDER BY` column. `1 PRECEDING` includes all rows that have a value within 1 unit of the current row's order key.

**8. Write a query to calculate a 7-day rolling average of daily sales.**
```sql
WITH DailySales AS (
    SELECT order_date, SUM(amount) as daily_total
    FROM orders GROUP BY order_date
)
SELECT 
    order_date, 
    daily_total,
    AVG(daily_total) OVER (
        ORDER BY order_date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as rolling_7d_avg
FROM DailySales;
```

**9. How do you filter rows based on a window function result? Why can't you use WHERE directly?**
You cannot use window functions in a `WHERE` clause because logical query processing evaluates `WHERE` (and `GROUP BY` / `HAVING`) *before* window functions are calculated. To filter on them, you must calculate the window function inside a Common Table Expression (CTE) or a subquery, and then apply the `WHERE` filter on the outer query.

**10. What is the WINDOW clause used for?**
The `WINDOW` clause allows you to define a window specification once and reuse it multiple times within the same `SELECT` statement. This keeps queries clean and prevents repeating complex `OVER` expressions.
```sql
SELECT 
    emp_id, 
    SUM(salary) OVER w, 
    AVG(salary) OVER w
FROM employees
WINDOW w AS (PARTITION BY dept_id ORDER BY hire_date);
```

**11. Write a query to assign a rank within each department by salary, densely ranked.**
```sql
SELECT 
    emp_id, 
    name, 
    dept_id, 
    salary,
    DENSE_RANK() OVER (PARTITION BY dept_id ORDER BY salary DESC) as dept_salary_rank
FROM employees;
```

**12. What is the default window frame when you specify ORDER BY in OVER()?**
The default frame is `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`. This means the function will consider all rows from the start of the partition up to and including the current row, grouping ties together.

**13. How would you solve the "gaps and islands" problem using window functions?**
You can use `ROW_NUMBER()` to generate a sequential number. If you subtract this sequential number (or interval) from a sequential date or ID, all rows belonging to the same continuous "island" will yield the exact same result. You can then `GROUP BY` this resulting difference to find the start, end, and count of the island.

**14. Write a query to deduplicate a table by keeping only the latest record per user_id.**
```sql
WITH NumberedRecords AS (
    SELECT 
        customer_id, 
        name, email, 
        ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY created_at DESC) as rn
    FROM customers
)
SELECT customer_id, name, email 
FROM NumberedRecords 
WHERE rn = 1;
```

**15. How do window functions perform compared to self-joins for the same problem?**
Window functions perform vastly better than self-joins or correlated subqueries for sequential tasks like running totals or finding previous values. Self-joins often result in an $O(N^2)$ operation because the table must be joined to itself for every row. Window functions typically process data in $O(N \log N)$ time, relying on a single sort and scan mechanism implemented natively by the query execution engine.
