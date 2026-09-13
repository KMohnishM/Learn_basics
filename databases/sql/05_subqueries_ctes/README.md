# Module 5: Subqueries and Common Table Expressions (CTEs)

## 1. Subqueries Overview

A subquery is a query nested inside another query. Depending on their location and the number of results they return, subqueries can be classified into different types:

### 1.1 Scalar Subquery
A scalar subquery returns exactly one column and one row (a single value). It can be used anywhere a single value is expected, such as in the `SELECT` list, `WHERE` clause, or `HAVING` clause.

```sql
-- Find employees earning more than the overall average salary
SELECT name, salary
FROM employees
WHERE salary > (
    SELECT AVG(salary) 
    FROM employees
);
```

### 1.2 Row Subquery
A row subquery returns one row but can contain multiple columns.

```sql
-- Find employees who share the same department and manager as employee 101
SELECT name
FROM employees
WHERE (dept_id, manager_id) = (
    SELECT dept_id, manager_id
    FROM employees
    WHERE emp_id = 101
)
AND emp_id != 101;
```

### 1.3 Table Subquery
A table subquery returns multiple rows and one or more columns. These are typically used in the `FROM` clause or with operators like `IN`, `EXISTS`, `ANY`, or `ALL`.

```sql
-- Find departments that have more than 5 employees
SELECT dept_id, dept_name
FROM departments
WHERE dept_id IN (
    SELECT dept_id
    FROM employees
    GROUP BY dept_id
    HAVING COUNT(*) > 5
);
```

## 2. Subqueries in the WHERE Clause

### 2.1 IN Operator
The `IN` operator checks if a value exists within the list of values returned by the subquery.

```sql
-- Find customers who have placed at least one order
SELECT customer_id, name
FROM customers
WHERE customer_id IN (
    SELECT customer_id
    FROM orders
);
```

### 2.2 EXISTS Operator
The `EXISTS` operator tests for the existence of any rows in a subquery. It evaluates to TRUE if the subquery returns at least one row, and FALSE otherwise.

```sql
-- Find customers who have placed at least one order
SELECT customer_id, name
FROM customers c
WHERE EXISTS (
    SELECT 1
    FROM orders o
    WHERE o.customer_id = c.customer_id
);
```

### 2.3 ANY / SOME Operator
`ANY` (or `SOME`, which is a synonym) compares a scalar value to a set of values returned by a subquery using a standard operator (`=`, `>`, `<`, etc.).

```sql
-- Find products whose price is greater than any product in the 'Electronics' category
SELECT name, price
FROM products
WHERE price > ANY (
    SELECT price
    FROM products
    WHERE category = 'Electronics'
);
```

### 2.4 ALL Operator
`ALL` compares a scalar value to every value returned by the subquery. The condition must be true for all values for the expression to evaluate to true.

```sql
-- Find products whose price is greater than all products in the 'Electronics' category
SELECT name, price
FROM products
WHERE price > ALL (
    SELECT price
    FROM products
    WHERE category = 'Electronics'
);
```

## 3. IN vs. EXISTS

While `IN` and `EXISTS` can often be used interchangeably to produce the same logical result, their execution semantics and performance characteristics differ.

### Semantic Difference
- `IN` compares a single column value against a list of values.
- `EXISTS` evaluates a boolean condition (presence of rows).

### Performance Difference
- **EXISTS** typically employs short-circuit evaluation. The database engine stops searching as soon as it finds the first matching row in the subquery. This makes it highly efficient for subqueries checking against large tables, especially when correlated.
- **IN** traditionally materializes the subquery results, builds a hash table or sorts the list, and then performs comparisons.
- Modern cost-based optimizers (like in PostgreSQL) often rewrite both constructs into similar physical execution plans (e.g., Hash Semi Join or Nested Loop Semi Join). However, `EXISTS` is safer and more predictable for large, correlated lookups.

### The NULL Trap with NOT IN
When dealing with negation, the difference between `NOT IN` and `NOT EXISTS` is critical due to how SQL handles `NULL` values.

```sql
-- This query may return zero rows if the subquery returns any NULL values.
SELECT customer_id, name
FROM customers
WHERE customer_id NOT IN (
    SELECT customer_id
    FROM orders
);
```
**Why does this happen?**
If `orders.customer_id` contains a `NULL`, the `NOT IN` evaluation expands to:
`customer_id != 1 AND customer_id != 2 AND customer_id != NULL`
Since any comparison with `NULL` yields `UNKNOWN` (not `TRUE`), the entire `AND` chain evaluates to `UNKNOWN`. The `WHERE` clause filters out any row that does not explicitly evaluate to `TRUE`.

**Solution: Always use NOT EXISTS for robust negation.**
```sql
SELECT customer_id, name
FROM customers c
WHERE NOT EXISTS (
    SELECT 1
    FROM orders o
    WHERE o.customer_id = c.customer_id
);
```

## 4. Correlated Subqueries

A correlated subquery contains a reference to a table in the outer query. This forces the database to evaluate the subquery once for every row processed by the outer query.

```sql
-- Find employees who earn more than the average salary of their specific department
SELECT e1.name, e1.salary, e1.dept_id
FROM employees e1
WHERE e1.salary > (
    SELECT AVG(e2.salary)
    FROM employees e2
    WHERE e2.dept_id = e1.dept_id
);
```

### Performance Implications
Correlated subqueries can lead to O(N * M) time complexity, where N is the number of rows in the outer query and M is the average rows scanned in the subquery. This is known as row-by-row processing (or "RBAR" - Row By Agonizing Row). They should generally be avoided in favor of `JOIN` operations or window functions.

## 5. Scalar Subqueries in the SELECT Clause

You can compute columns dynamically using scalar subqueries. Like `WHERE` clause correlated subqueries, these execute per row and can cause severe performance degradation on large datasets.

```sql
-- Retrieve all departments and a count of their active employees
SELECT 
    d.dept_id,
    d.dept_name,
    (SELECT COUNT(*) 
     FROM employees e 
     WHERE e.dept_id = d.dept_id AND e.is_active = TRUE) AS active_employee_count
FROM departments d;
```

## 6. Subqueries in the FROM Clause (Derived Tables)

A subquery in the `FROM` clause acts as an ephemeral table that exists only for the duration of the query. In PostgreSQL and MySQL, every derived table **must** be assigned a table alias.

```sql
-- Calculate the average number of orders per customer
SELECT AVG(order_count) AS avg_orders_per_customer
FROM (
    SELECT customer_id, COUNT(*) AS order_count
    FROM orders
    GROUP BY customer_id
) AS customer_orders;
```

## 7. Common Table Expressions (CTEs)

A Common Table Expression (CTE) provides a way to write auxiliary statements for use in a larger query. CTEs are defined using the `WITH` clause. They function similarly to derived tables but offer superior readability.

### Syntax
```sql
WITH regional_sales AS (
    SELECT c.country, SUM(o.amount) AS total_sales
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    GROUP BY c.country
)
SELECT country, total_sales
FROM regional_sales
WHERE total_sales > 10000;
```

### Multiple CTEs
You can define multiple CTEs in a single `WITH` clause by separating them with commas. A subsequent CTE can reference a preceding CTE.

```sql
WITH top_departments AS (
    SELECT dept_id, COUNT(*) as emp_count
    FROM employees
    GROUP BY dept_id
    ORDER BY emp_count DESC
    LIMIT 3
),
department_details AS (
    SELECT d.dept_name, td.emp_count
    FROM departments d
    JOIN top_departments td ON d.dept_id = td.dept_id
)
SELECT * FROM department_details;
```

### CTEs vs. Subqueries
- **Readability**: CTEs read top-to-bottom, aligning with procedural logic, whereas nested subqueries require reading inside-out.
- **Reusability**: A single CTE can be referenced multiple times in the main query, preventing code duplication.
- **Performance**: In PostgreSQL versions prior to 12, CTEs were always materialized (evaluated once and stored in memory/disk). PostgreSQL 12+ defaults to folding non-recursive CTEs into the main query plan (like derived tables) unless forced with `MATERIALIZED`.
MySQL evaluates CTEs identically to derived tables.

```sql
-- Forcing materialization in PostgreSQL
WITH heavy_calculation AS MATERIALIZED (
    SELECT ...
)
SELECT ...
```

## 8. Recursive CTEs

Recursive CTEs are used to query hierarchical data, such as organizational charts, bill of materials, or graph structures. They require the `WITH RECURSIVE` modifier.

### Syntax Structure
A recursive CTE consists of three parts:
1. **Anchor Member**: The initial query that returns the base result set.
2. **Recursive Member**: A query that references the CTE itself, joined with the results of the previous iteration.
3. **UNION ALL**: Combines the anchor and recursive members.

Execution terminates when the recursive member returns an empty set.

### 8.1 Example: Employee-Manager Hierarchy
Traverse an organization chart to find the management chain.

```sql
WITH RECURSIVE org_chart AS (
    -- Anchor: Select the CEO (manager_id is NULL)
    SELECT emp_id, name, manager_id, 1 AS level
    FROM employees
    WHERE manager_id IS NULL
    
    UNION ALL
    
    -- Recursive: Select employees managed by the current set in org_chart
    SELECT e.emp_id, e.name, e.manager_id, oc.level + 1
    FROM employees e
    JOIN org_chart oc ON e.manager_id = oc.emp_id
)
SELECT emp_id, name, level
FROM org_chart
ORDER BY level, name;
```

### 8.2 Example: Generating a Date Series
Generating a sequence of dates dynamically without a physical calendar table.

```sql
WITH RECURSIVE date_series AS (
    -- Anchor
    SELECT CAST('2023-01-01' AS DATE) AS dt
    
    UNION ALL
    
    -- Recursive
    SELECT dt + INTERVAL '1 day'
    FROM date_series
    WHERE dt < CAST('2023-01-31' AS DATE)
)
SELECT dt FROM date_series;
```

### 8.3 Example: Graph Traversal
Finding all connected products in a "frequently bought together" graph (assuming a table `product_relations(prod_a, prod_b)`).

```sql
-- Note: product_relations is a conceptual table for this example.
WITH RECURSIVE related_products AS (
    -- Anchor: Start with product 10
    SELECT prod_b AS linked_product, 1 AS depth
    FROM product_relations
    WHERE prod_a = 10
    
    UNION ALL
    
    -- Recursive: Find products linked to the already discovered products
    SELECT pr.prod_b, rp.depth + 1
    FROM product_relations pr
    JOIN related_products rp ON pr.prod_a = rp.linked_product
    WHERE rp.depth < 5 -- Prevent infinite loops / limit depth
)
SELECT DISTINCT linked_product 
FROM related_products;
```

## 9. Window Functions as Alternatives to Correlated Subqueries

Correlated subqueries often perform poorly. Window functions provide a performant alternative for calculating aggregates over a partition of rows while preserving the row-level detail.

**Correlated Subquery Approach:**
```sql
SELECT e.name, e.salary,
       (SELECT AVG(salary) FROM employees WHERE dept_id = e.dept_id) AS dept_avg
FROM employees e;
```

**Refactored with Window Function:**
```sql
SELECT name, salary,
       AVG(salary) OVER (PARTITION BY dept_id) AS dept_avg
FROM employees;
```
The window function requires only a single pass over the data, sorting or hashing by `dept_id`, which is vastly more efficient than executing a subquery N times.
