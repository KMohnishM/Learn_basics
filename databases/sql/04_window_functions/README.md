# Module 4: Window Functions in SQL

Window functions (also known as analytic functions) are among the most powerful features in modern SQL. They allow you to perform calculations across a set of table rows that are related to the current row.

Unlike standard aggregate functions (`SUM`, `COUNT`, `AVG`), which collapse multiple rows into a single summary row, window functions do not cause rows to become grouped into a single output row. The rows retain their separate identities. Instead, the window function calculates a return value for every row, based on the "window" of rows it looks at.

This module uses PostgreSQL syntax, which strictly adheres to the ANSI SQL standard for window functions. MySQL 8.0+ also supports these features with nearly identical syntax.

## Schema Context

All examples in this module use the following schema:

```sql
CREATE TABLE departments (
    dept_id INT PRIMARY KEY,
    dept_name VARCHAR(100),
    location VARCHAR(100)
);

CREATE TABLE employees (
    emp_id INT PRIMARY KEY,
    name VARCHAR(100),
    dept_id INT,
    salary NUMERIC(10, 2),
    manager_id INT,
    hire_date DATE,
    is_active BOOLEAN
);

CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    country VARCHAR(50),
    created_at TIMESTAMP
);

CREATE TABLE products (
    product_id INT PRIMARY KEY,
    name VARCHAR(100),
    category VARCHAR(50),
    price NUMERIC(10, 2)
);

CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer_id INT,
    product_id INT,
    quantity INT,
    amount NUMERIC(10, 2),
    order_date DATE,
    status VARCHAR(20)
);
```

---

## 1. Syntax Anatomy

A window function call always contains an `OVER` clause directly following the function's name and arguments.

```sql
function_name (expression) OVER (
    [PARTITION BY partition_expression, ... ]
    [ORDER BY sort_expression [ASC | DESC], ... ]
    [window_frame_clause]
)
```

- **`function_name`**: The function to apply (e.g., `SUM`, `ROW_NUMBER`, `LAG`).
- **`OVER`**: Signals that this is a window function.
- **`PARTITION BY`**: Divides the result set into groups (partitions). The window function is applied to each partition independently.
- **`ORDER BY`**: Specifies the logical order of rows within a partition for the function to process.
- **`window_frame_clause`**: Further restricts the set of rows within the partition that the function evaluates for the current row (e.g., `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`).

### Example: The Basics

Let's compare a standard aggregate function using `GROUP BY` to a window function.

**Standard Aggregate (Collapses rows):**
```sql
SELECT dept_id, AVG(salary) AS avg_dept_salary
FROM employees
GROUP BY dept_id;
```
*Result: One row per department.*

**Window Function (Preserves rows):**
```sql
SELECT 
    emp_id, 
    name, 
    dept_id, 
    salary,
    AVG(salary) OVER (PARTITION BY dept_id) AS avg_dept_salary
FROM employees;
```
*Result: Every employee row is returned, with a new column showing the average salary for their respective department.*

---

## 2. PARTITION BY

The `PARTITION BY` clause acts similarly to `GROUP BY`, but instead of reducing the result set, it resets the window function's scope for each new partition.

```sql
-- Find the total sales amount per customer alongside their individual orders
SELECT 
    order_id,
    customer_id,
    amount,
    SUM(amount) OVER (PARTITION BY customer_id) AS total_customer_spend
FROM orders;
```

If you omit `PARTITION BY`, the entire result set is treated as a single partition.

```sql
-- Calculate the overall company average salary and compare each employee to it
SELECT 
    name, 
    salary, 
    AVG(salary) OVER () AS company_avg_salary,
    salary - AVG(salary) OVER () AS diff_from_avg
FROM employees;
```

---

## 3. ORDER BY inside OVER

The `ORDER BY` clause inside the `OVER()` clause determines the sequence in which rows are processed by the window function. This is critical for functions like `ROW_NUMBER()`, `LAG()`, or when calculating running totals.

**Important Note:** When you include an `ORDER BY` clause without an explicit window frame clause, the default window frame becomes `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`. This calculates a "running" aggregation up to the current row.

```sql
-- Running total of orders by date
SELECT 
    order_id,
    order_date,
    amount,
    SUM(amount) OVER (ORDER BY order_date ASC) AS running_total
FROM orders;
```

If multiple orders occurred on the same `order_date`, `RANGE BETWEEN` will add all orders on that date together before incrementing the running total. To strictly process row-by-row even on ties, you would need a `ROWS` frame (covered later).

---

## 4. Ranking Functions

Ranking functions assign a rank or sequential number to each row within a partition.

### ROW_NUMBER()
Assigns a unique, sequential integer to each row starting from 1, regardless of ties. If an `ORDER BY` is specified, it numbers based on that order. For ties, the numbering is arbitrary unless additional tie-breaker columns are added.

```sql
SELECT 
    emp_id, 
    name, 
    salary,
    ROW_NUMBER() OVER (ORDER BY salary DESC) AS row_num
FROM employees;
```

### RANK()
Assigns a rank starting from 1. If rows have identical values in the `ORDER BY` clause, they receive the same rank. However, the next rank will skip numbers (e.g., 1, 2, 2, 4, 5).

```sql
SELECT 
    emp_id, 
    name, 
    salary,
    RANK() OVER (ORDER BY salary DESC) AS rank_val
FROM employees;
```

### DENSE_RANK()
Works exactly like `RANK()`, but does not leave gaps in the ranking sequence (e.g., 1, 2, 2, 3, 4).

```sql
SELECT 
    emp_id, 
    name, 
    salary,
    DENSE_RANK() OVER (ORDER BY salary DESC) AS dense_rank_val
FROM employees;
```

### NTILE(n)
Divides the rows in an ordered partition into `n` roughly equal groups (buckets) and assigns the bucket number (1 to n) to each row.

```sql
-- Divide employees into 4 quartiles based on salary
SELECT 
    name, 
    salary,
    NTILE(4) OVER (ORDER BY salary DESC) AS salary_quartile
FROM employees;
```

### PERCENT_RANK() and CUME_DIST()
- `PERCENT_RANK()`: Relative rank of the current row: `(rank - 1) / (total rows in partition - 1)`.
- `CUME_DIST()`: Cumulative distribution: `(number of rows preceding or peer with current row) / (total rows in partition)`.

```sql
SELECT 
    name, 
    salary,
    PERCENT_RANK() OVER (ORDER BY salary) AS pct_rank,
    CUME_DIST() OVER (ORDER BY salary) AS cume_distribution
FROM employees;
```

---

## 5. Offset Functions

Offset functions allow you to access data from other rows in the same result set, relative to the current row, without requiring self-joins.

### LAG(col, offset, default)
Returns the value evaluated at the row that is `offset` rows before the current row.
- `offset`: Defaults to 1.
- `default`: Value to return if the offset goes beyond the partition boundaries (defaults to NULL).

```sql
-- Find the previous order date for each customer
SELECT 
    customer_id,
    order_id,
    order_date,
    LAG(order_date, 1) OVER (PARTITION BY customer_id ORDER BY order_date) AS prev_order_date
FROM orders;
```

### LEAD(col, offset, default)
Returns the value evaluated at the row that is `offset` rows after the current row.

```sql
-- Find the next order date for each customer
SELECT 
    customer_id,
    order_id,
    order_date,
    LEAD(order_date, 1) OVER (PARTITION BY customer_id ORDER BY order_date) AS next_order_date
FROM orders;
```

### FIRST_VALUE(col) and LAST_VALUE(col)
Returns the value evaluated at the first or last row of the window frame.

**The `LAST_VALUE` Trap:**
Because the default frame when using `ORDER BY` is `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`, `LAST_VALUE()` will only look up to the *current row*, essentially returning the current row's value rather than the last value in the entire partition. To fix this, you must explicitly define the frame.

```sql
-- Correct way to use LAST_VALUE
SELECT 
    emp_id,
    dept_id,
    salary,
    FIRST_VALUE(salary) OVER (
        PARTITION BY dept_id 
        ORDER BY salary ASC
    ) AS lowest_dept_salary,
    LAST_VALUE(salary) OVER (
        PARTITION BY dept_id 
        ORDER BY salary ASC
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS highest_dept_salary
FROM employees;
```

### NTH_VALUE(col, n)
Returns the value from the nth row of the window frame.

```sql
-- Find the 2nd highest salary in each department
SELECT 
    name,
    dept_id,
    salary,
    NTH_VALUE(salary, 2) OVER (
        PARTITION BY dept_id 
        ORDER BY salary DESC
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS second_highest_salary
FROM employees;
```

---

## 6. Aggregate Window Functions

Standard aggregates like `SUM`, `AVG`, `MIN`, `MAX`, and `COUNT` can be used as window functions.

```sql
SELECT 
    order_id,
    customer_id,
    amount,
    SUM(amount) OVER (PARTITION BY customer_id) AS total_customer_amount,
    AVG(amount) OVER (PARTITION BY customer_id) AS avg_customer_amount,
    COUNT(order_id) OVER (PARTITION BY customer_id) AS total_orders_per_customer
FROM orders;
```

---

## 7. Running Totals

A running total accumulates values row by row. This is achieved by combining an aggregate window function (`SUM`) with an `ORDER BY` clause.

```sql
SELECT 
    order_date,
    amount,
    SUM(amount) OVER (ORDER BY order_date) AS running_total_sales
FROM orders;
```

Because `ORDER BY order_date` implies `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`, the total accumulates dynamically as it processes dates chronologically.

---

## 8. Window Frame Specification

The frame clause refines the set of rows examined by the window function.

Syntax:
`[ROWS | RANGE] BETWEEN frame_start AND frame_end`

**Modes:**
- `ROWS`: Operates on physical rows. `1 PRECEDING` means exactly 1 row before.
- `RANGE`: Operates on logical values. `1 PRECEDING` means rows where the order-by value is within 1 unit of the current row's value.

**Boundaries:**
- `UNBOUNDED PRECEDING`: The first row in the partition.
- `n PRECEDING`: `n` rows before the current row.
- `CURRENT ROW`: The current row.
- `n FOLLOWING`: `n` rows after the current row.
- `UNBOUNDED FOLLOWING`: The last row in the partition.

```sql
-- 3-order moving average (current + 2 previous)
SELECT 
    order_id,
    order_date,
    amount,
    AVG(amount) OVER (
        ORDER BY order_date
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS moving_avg_3_orders
FROM orders;
```

---

## 9. Named Windows (WINDOW clause)

When multiple window functions in the same `SELECT` statement share the exact same `OVER` clause, you can extract the definition using the `WINDOW` clause to keep the query clean and DRY (Don't Repeat Yourself).

```sql
SELECT 
    emp_id,
    dept_id,
    salary,
    AVG(salary) OVER w AS avg_dept_salary,
    MAX(salary) OVER w AS max_dept_salary,
    MIN(salary) OVER w AS min_dept_salary
FROM employees
WINDOW w AS (PARTITION BY dept_id);
```

---

## 10. Filtering on Window Function Results

Window functions are evaluated *after* the `WHERE`, `GROUP BY`, and `HAVING` clauses. Therefore, you **cannot** use a window function directly in a `WHERE` clause.

To filter based on the result of a window function, you must wrap the query in a Common Table Expression (CTE) or a subquery.

```sql
-- WRONG (Will throw an error):
-- SELECT name, salary, ROW_NUMBER() OVER(ORDER BY salary DESC) as rnk 
-- FROM employees WHERE rnk = 1;

-- RIGHT (Using a CTE):
WITH RankedEmployees AS (
    SELECT 
        name, 
        dept_id,
        salary,
        ROW_NUMBER() OVER(PARTITION BY dept_id ORDER BY salary DESC) as rnk
    FROM employees
)
SELECT name, dept_id, salary
FROM RankedEmployees
WHERE rnk <= 3;
```

---

## 11. Performance: Window Functions vs. Self-Joins

Before window functions, tasks like finding a previous value or calculating a running total required expensive self-joins or correlated subqueries. Window functions are highly optimized by database engines, typically requiring only a single pass (sort and scan) over the data.

```sql
-- Old way (Correlated Subquery) - O(N^2) complexity roughly
SELECT 
    e1.emp_id, 
    e1.salary,
    (SELECT COUNT(*) + 1 
     FROM employees e2 
     WHERE e2.salary > e1.salary) AS rank
FROM employees e1;

-- New way (Window Function) - O(N log N) complexity
SELECT 
    emp_id, 
    salary, 
    RANK() OVER (ORDER BY salary DESC) AS rank
FROM employees;
```

---

## 12. Real Examples

### Example A: Top 3 Products per Category by Price
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

### Example B: Month-over-Month Growth Percentage
```sql
WITH MonthlySales AS (
    SELECT 
        DATE_TRUNC('month', order_date) as sales_month,
        SUM(amount) as total_sales
    FROM orders
    GROUP BY DATE_TRUNC('month', order_date)
),
SalesWithLag AS (
    SELECT 
        sales_month,
        total_sales,
        LAG(total_sales) OVER (ORDER BY sales_month) as prev_month_sales
    FROM MonthlySales
)
SELECT 
    sales_month,
    total_sales,
    prev_month_sales,
    ROUND(((total_sales - prev_month_sales) / prev_month_sales) * 100, 2) as growth_pct
FROM SalesWithLag;
```

### Example C: 7-Day Rolling Average
```sql
-- Uses RANGE to account for missing days in the dataset correctly.
-- PostgreSQL specific syntax for interval subtraction in RANGE
SELECT 
    order_date,
    SUM(amount) as daily_sales,
    AVG(SUM(amount)) OVER (
        ORDER BY order_date
        RANGE BETWEEN INTERVAL '6 days' PRECEDING AND CURRENT ROW
    ) as rolling_7_day_avg
FROM orders
GROUP BY order_date;
```

### Example D: Gap and Island Detection
Finding continuous streaks (islands) of active days for a user.

```sql
WITH UserActivity AS (
    -- Assuming a generic log table for this specific conceptual example
    SELECT user_id, activity_date
    FROM activity_logs
),
NumberedActivity AS (
    SELECT 
        user_id,
        activity_date,
        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY activity_date) as rn
    FROM UserActivity
),
GroupedActivity AS (
    -- Subtracting row number (days) from date groups consecutive days together!
    SELECT 
        user_id,
        activity_date,
        activity_date - rn * INTERVAL '1 day' as streak_group
    FROM NumberedActivity
)
SELECT 
    user_id,
    MIN(activity_date) as streak_start,
    MAX(activity_date) as streak_end,
    COUNT(*) as streak_length
FROM GroupedActivity
GROUP BY user_id, streak_group
ORDER BY user_id, streak_start;
```

### Example E: Running Total that Resets Per Partition
```sql
-- Calculate a running total of order amounts for each customer individually
SELECT 
    customer_id,
    order_id,
    order_date,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id 
        ORDER BY order_date, order_id
    ) AS customer_running_total
FROM orders
ORDER BY customer_id, order_date;
```

### Example F: Assign a Row Number to Deduplicate
```sql
-- If an employee was accidentally inserted twice, keep the most recent update
WITH NumberedEmployees AS (
    SELECT 
        emp_id,
        name,
        ROW_NUMBER() OVER (
            PARTITION BY name, dept_id 
            ORDER BY hire_date DESC
        ) as rn
    FROM employees
)
-- DELETE FROM employees WHERE emp_id IN (SELECT emp_id FROM NumberedEmployees WHERE rn > 1);
SELECT * FROM NumberedEmployees WHERE rn = 1;
```
