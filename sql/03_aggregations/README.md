# SQL Aggregations Deep Dive

This module covers aggregate functions, grouping, and advanced aggregation techniques in SQL. All examples use PostgreSQL syntax, with notes on MySQL differences where applicable.

## Core Concepts

Aggregation operations collapse multiple rows into a single summary row. When combined with grouping, aggregations are performed per group rather than across the entire table.

### Schema Reference

The following schema is used throughout this document:

```sql
CREATE TABLE employees(
    emp_id INT PRIMARY KEY,
    name VARCHAR(100),
    dept_id INT,
    salary NUMERIC,
    manager_id INT,
    hire_date DATE,
    is_active BOOLEAN
);

CREATE TABLE departments(
    dept_id INT PRIMARY KEY,
    dept_name VARCHAR(100),
    location VARCHAR(100)
);

CREATE TABLE orders(
    order_id INT PRIMARY KEY,
    customer_id INT,
    product_id INT,
    quantity INT,
    amount NUMERIC,
    order_date DATE,
    status VARCHAR(50)
);

CREATE TABLE customers(
    customer_id INT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    country VARCHAR(100),
    created_at TIMESTAMP
);

CREATE TABLE products(
    product_id INT PRIMARY KEY,
    name VARCHAR(100),
    category VARCHAR(100),
    price NUMERIC
);
```

## Aggregate Functions Deep Dive

### The COUNT Function

The `COUNT` function behaves differently depending on its argument:

*   `COUNT(*)`: Counts the total number of rows in the result set or group, regardless of NULL values. It is the only aggregate function that does not ignore NULLs.
*   `COUNT(column_name)`: Counts the number of non-NULL values in `column_name`.
*   `COUNT(DISTINCT column_name)`: Counts the number of unique, non-NULL values in `column_name`.

```sql
-- Total number of employees (including those with no department or salary)
SELECT COUNT(*) FROM employees;

-- Total number of employees who have a salary defined
SELECT COUNT(salary) FROM employees;

-- Number of unique department IDs assigned to employees
SELECT COUNT(DISTINCT dept_id) FROM employees;
```

### SUM, AVG, MIN, MAX

These functions calculate the sum, average, minimum, and maximum values of a column, respectively. All of these functions ignore NULL values.

```sql
-- Sum of all salaries
SELECT SUM(salary) FROM employees;

-- Average salary (calculated only over non-NULL salary values)
SELECT AVG(salary) FROM employees;

-- Minimum and maximum hire dates
SELECT MIN(hire_date), MAX(hire_date) FROM employees;
```

**NULL Behavior Impact:** When `AVG` ignores NULLs, it calculates `SUM(salary) / COUNT(salary)`, not `SUM(salary) / COUNT(*)`. If you want to treat NULLs as zero for the average, use `COALESCE`:

```sql
-- Average salary treating NULLs as 0
SELECT AVG(COALESCE(salary, 0)) FROM employees;
```

## GROUP BY Mechanics

The `GROUP BY` clause divides the result set into subsets (groups) based on the values of one or more columns or expressions. Aggregate functions are then applied to each group.

### The Grouping Rule

When using `GROUP BY`, any column in the `SELECT` list that is not enclosed in an aggregate function *must* appear in the `GROUP BY` clause.

```sql
-- Correct: dept_id is in both SELECT and GROUP BY
SELECT dept_id, COUNT(*)
FROM employees
GROUP BY dept_id;

-- Incorrect: name is neither aggregated nor in GROUP BY
-- SELECT dept_id, name, COUNT(*) FROM employees GROUP BY dept_id;
```

**Exception (Primary Key Dependency):** In standard SQL (and supported by PostgreSQL and MySQL under certain strict modes), if you group by a table's primary key, you can select functionally dependent columns without explicitly listing them in the `GROUP BY`.

```sql
-- Valid in modern SQL if dept_id is the primary key of departments
SELECT d.dept_id, d.dept_name, COUNT(e.emp_id)
FROM departments d
LEFT JOIN employees e ON d.dept_id = e.dept_id
GROUP BY d.dept_id;
```

### Grouping by Expressions

You can group by the result of an expression or function.

```sql
-- Grouping by the year of hire_date
SELECT EXTRACT(YEAR FROM hire_date) AS hire_year, COUNT(*)
FROM employees
GROUP BY EXTRACT(YEAR FROM hire_date);
```

### Grouping by Column Alias

PostgreSQL and MySQL allow you to group by the alias defined in the `SELECT` clause, though this is not strictly standard SQL.

```sql
-- PostgreSQL / MySQL dialect feature
SELECT EXTRACT(YEAR FROM hire_date) AS hire_year, COUNT(*)
FROM employees
GROUP BY hire_year;
```

## HAVING vs WHERE

### Execution Order

Understanding the logical execution order of a query is crucial for using `WHERE` and `HAVING` correctly:
1.  `FROM` (including `JOIN`s)
2.  `WHERE`
3.  `GROUP BY`
4.  `HAVING`
5.  `SELECT`
6.  `ORDER BY`
7.  `LIMIT`

### Filtering Raw Rows with WHERE

`WHERE` filters individual rows *before* aggregation takes place. It cannot contain aggregate functions.

```sql
-- Filters active employees before grouping
SELECT dept_id, SUM(salary)
FROM employees
WHERE is_active = true
GROUP BY dept_id;
```

### Filtering on Aggregates with HAVING

`HAVING` filters groups *after* aggregation has occurred. It is specifically designed to work with aggregate functions.

```sql
-- Filters groups to only those with total salary > 1000000
SELECT dept_id, SUM(salary)
FROM employees
GROUP BY dept_id
HAVING SUM(salary) > 1000000;
```

### Combining WHERE and HAVING

It is common and efficient to use both clauses in the same query. Filter as much data as possible with `WHERE` before aggregating, then filter the resulting groups with `HAVING`.

```sql
SELECT c.country, SUM(o.amount) AS total_revenue
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.status = 'completed'      -- Filter raw rows first
GROUP BY c.country
HAVING SUM(o.amount) > 50000;     -- Filter aggregated groups second
```

## Conditional Aggregation

Conditional aggregation allows you to perform different aggregations based on conditions within the same query.

### The FILTER Clause (PostgreSQL)

PostgreSQL implements the SQL standard `FILTER` clause, which is the cleanest way to perform conditional aggregation. It applies an aggregate function only to rows that meet a specific condition.

```sql
SELECT 
    dept_id,
    COUNT(*) AS total_employees,
    COUNT(*) FILTER (WHERE is_active = true) AS active_employees,
    SUM(salary) FILTER (WHERE is_active = true) AS active_payroll
FROM employees
GROUP BY dept_id;
```

### Conditional Aggregation with CASE

The `CASE` statement is the universal way to perform conditional aggregation, supported by nearly all SQL databases (including MySQL, which lacks the `FILTER` clause).

```sql
SELECT 
    dept_id,
    COUNT(*) AS total_employees,
    SUM(CASE WHEN is_active = true THEN 1 ELSE 0 END) AS active_employees,
    SUM(CASE WHEN is_active = true THEN salary ELSE 0 END) AS active_payroll
FROM employees
GROUP BY dept_id;
```

Note that `COUNT(CASE WHEN condition THEN 1 END)` also works because `COUNT` ignores the implicit `NULL` when the condition is false.

## Pivoting Data (Cross-Tab Queries)

Conditional aggregation is the primary technique for pivoting data—converting rows into columns.

```sql
-- Pivot orders amount by status
SELECT 
    EXTRACT(MONTH FROM order_date) AS order_month,
    SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END) AS pending_revenue,
    SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END) AS completed_revenue,
    SUM(CASE WHEN status = 'cancelled' THEN amount ELSE 0 END) AS cancelled_revenue
FROM orders
GROUP BY EXTRACT(MONTH FROM order_date);
```

## Advanced Grouping Constructs

SQL provides extensions to `GROUP BY` for generating multiple levels of aggregation in a single query.

### ROLLUP

`ROLLUP` generates a hierarchy of subtotals and a grand total. It drops columns from the right to left to create broader groups.

```sql
-- Generates:
-- 1. Sales by category and status
-- 2. Sales by category (subtotal)
-- 3. Total sales (grand total)
SELECT 
    p.category, 
    o.status, 
    SUM(o.amount) AS total_sales
FROM products p
JOIN orders o ON p.product_id = o.product_id
GROUP BY ROLLUP(p.category, o.status);
```

### The GROUPING() Function

When using `ROLLUP`, the resulting rows will contain NULLs for the columns that were rolled up. The `GROUPING()` function distinguishes between a true NULL value in the data and a NULL generated by `ROLLUP`. It returns 1 if the column is aggregated (rolled up) and 0 if it is part of the detail row.

```sql
SELECT 
    CASE WHEN GROUPING(p.category) = 1 THEN 'All Categories' ELSE p.category END AS category,
    CASE WHEN GROUPING(o.status) = 1 THEN 'All Statuses' ELSE o.status END AS status,
    SUM(o.amount) AS total_sales
FROM products p
JOIN orders o ON p.product_id = o.product_id
GROUP BY ROLLUP(p.category, o.status);
```

### CUBE

`CUBE` generates aggregations for all possible combinations of the specified grouping columns.

```sql
-- Generates groupings for:
-- (category, status)
-- (category)
-- (status)
-- () -> grand total
SELECT 
    p.category, 
    o.status, 
    SUM(o.amount) AS total_sales
FROM products p
JOIN orders o ON p.product_id = o.product_id
GROUP BY CUBE(p.category, o.status);
```

### GROUPING SETS

`GROUPING SETS` allows you to specify exactly which grouping combinations you want, providing fine-grained control and performance benefits over `CUBE` when you do not need all combinations.

```sql
-- Generates groupings only for:
-- 1. By category
-- 2. By status
-- 3. Grand total
SELECT 
    p.category, 
    o.status, 
    SUM(o.amount) AS total_sales
FROM products p
JOIN orders o ON p.product_id = o.product_id
GROUP BY GROUPING SETS (
    (p.category),
    (o.status),
    ()
);
```

## High-Performance Distinct Counting

### COUNT DISTINCT at Scale

`COUNT(DISTINCT col)` is resource-intensive because it requires sorting or hashing the entire result set in memory to find unique values. At massive scale (billions of rows), this becomes a bottleneck.

### Approximate Counting (HyperLogLog)

For large datasets where an exact count is not required, approximate distinct counting algorithms like HyperLogLog (HLL) are used. HLL uses a fraction of the memory and time.
While not part of standard PostgreSQL, it is available via the `postgresql-hll` extension.

```sql
-- Example using an HLL extension (hypothetical syntax)
-- SELECT hll_count_distinct(customer_id) FROM orders;
```

## Advanced Aggregation Functions

PostgreSQL provides several powerful aggregation functions beyond numerical calculations.

### STRING_AGG / GROUP_CONCAT

Aggregates string values into a single concatenated string, with a specified separator.
(MySQL equivalent: `GROUP_CONCAT()`).

```sql
-- PostgreSQL
SELECT 
    dept_id,
    STRING_AGG(name, ', ' ORDER BY name) AS employee_names
FROM employees
GROUP BY dept_id;

-- MySQL Equivalent
-- SELECT dept_id, GROUP_CONCAT(name ORDER BY name SEPARATOR ', ') FROM employees GROUP BY dept_id;
```

### ARRAY_AGG (PostgreSQL)

Aggregates values into a PostgreSQL array. This preserves data types better than string concatenation.

```sql
SELECT 
    dept_id,
    ARRAY_AGG(emp_id ORDER BY hire_date) AS employee_ids
FROM employees
GROUP BY dept_id;
```

### JSON_AGG (PostgreSQL)

Aggregates values into a JSON array, often used to build complex JSON structures directly in the database.

```sql
SELECT 
    d.dept_name,
    JSON_AGG(
        JSON_BUILD_OBJECT(
            'id', e.emp_id,
            'name', e.name,
            'salary', e.salary
        )
    ) AS employees_json
FROM departments d
LEFT JOIN employees e ON d.dept_id = e.dept_id
GROUP BY d.dept_name;
```

## Common Aggregation Pitfalls

### Double-Counting from Joins

When joining tables with a one-to-many relationship before aggregating, the rows from the "one" side are duplicated, leading to incorrect sums.

```sql
-- PITFALL: The order amounts might be summed multiple times if a product has multiple categories (hypothetical schema change) or due to fan-out.
-- Example of fan-out: Joining orders to another table with a 1:N relationship.
-- Suppose an order can have multiple tracking updates.
-- SELECT o.order_id, SUM(o.amount) FROM orders o JOIN tracking t ON o.order_id = t.order_id GROUP BY o.order_id;
-- amount is summed for every tracking update!

-- Correct Approach: Aggregate before joining, or use DISTINCT if applicable (though DISTINCT on SUM is dangerous).
```

### The AVG of AVGs Problem

Taking the average of averages yields mathematically incorrect results unless all groups have exactly the same number of items.

```sql
-- PITFALL: Calculating overall average salary by averaging department averages.
-- WITH DeptAverages AS (
--     SELECT dept_id, AVG(salary) as dept_avg FROM employees GROUP BY dept_id
-- )
-- SELECT AVG(dept_avg) FROM DeptAverages; -- THIS IS WRONG

-- Correct Approach: Calculate the overall average directly from the base data.
SELECT AVG(salary) FROM employees;
```
