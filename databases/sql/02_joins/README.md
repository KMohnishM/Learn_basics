# Module 2: SQL Joins

SQL joins are fundamental for combining data from multiple tables based on related columns. This module provides a deeply technical guide to all join types, join strategies, and common pitfalls using PostgreSQL syntax (with notes on MySQL differences).

## Schema Reference
All examples in this module use the following schema:
```sql
CREATE TABLE employees (
    emp_id INT PRIMARY KEY,
    name VARCHAR(100),
    dept_id INT,
    salary DECIMAL(10, 2),
    manager_id INT,
    hire_date DATE,
    is_active BOOLEAN
);

CREATE TABLE departments (
    dept_id INT PRIMARY KEY,
    dept_name VARCHAR(100),
    location VARCHAR(100)
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
    price DECIMAL(10, 2)
);

CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer_id INT,
    product_id INT,
    quantity INT,
    amount DECIMAL(10, 2),
    order_date TIMESTAMP,
    status VARCHAR(20)
);
```

## Join Types Overview with ASCII Diagrams

### INNER JOIN
Returns rows that have matching values in both tables.

```
Table A        Table B
  ---            ---
 |   |          |   |
 |   |==========|   | (Matches only)
 |   |          |   |
  ---            ---
```

### LEFT JOIN (LEFT OUTER JOIN)
Returns all rows from the left table, and the matched rows from the right table. The result is NULL from the right side if there is no match.

```
Table A        Table B
  ---            ---
 |===|==========|   | (All A, matching B)
 |===|          |   | (Unmatched A, B is NULL)
 |===|          |   |
  ---            ---
```

### RIGHT JOIN (RIGHT OUTER JOIN)
Returns all rows from the right table, and the matched rows from the left table.

```
Table A        Table B
  ---            ---
 |   |==========|===| (All B, matching A)
 |   |          |===| (Unmatched B, A is NULL)
 |   |          |===|
  ---            ---
```

### FULL OUTER JOIN
Returns all rows when there is a match in either left or right table.

```
Table A        Table B
  ---            ---
 |===|==========|===| (Matching A and B)
 |===|          |   | (Unmatched A, B is NULL)
 |   |          |===| (Unmatched B, A is NULL)
  ---            ---
```

### CROSS JOIN
Returns the Cartesian product of the sets of rows from the joined tables.

```
Table A (2 rows)  Table B (3 rows)
A1                B1
A2                B2
                  B3
Result: (A1,B1), (A1,B2), (A1,B3), (A2,B1), (A2,B2), (A2,B3)
```

### SELF JOIN
A regular join, but the table is joined with itself.

---

## Detailed Join Explanations

### INNER JOIN
The default join type. Use this when you strictly need rows that exist in both datasets.

```sql
SELECT 
    e.name AS employee_name,
    d.dept_name
FROM employees e
INNER JOIN departments d 
    ON e.dept_id = d.dept_id;
```

**Multiple Join Conditions (AND in ON clause):**
Sometimes joining on a single ID isn't enough (e.g., historical tracking tables, multi-tenant databases).

```sql
-- Assuming a scenario where dept_id alone isn't unique without a tenant_id or date bound
SELECT 
    e.name,
    d.dept_name
FROM employees e
INNER JOIN departments d 
    ON e.dept_id = d.dept_id 
    AND e.is_active = TRUE; -- Pre-filtering in the ON clause
```

### LEFT JOIN (LEFT OUTER JOIN)
Crucial for preserving a base dataset while enriching it with optional data.

```sql
SELECT 
    c.name,
    o.order_id,
    o.amount
FROM customers c
LEFT JOIN orders o 
    ON c.customer_id = o.customer_id;
```
If a customer has no orders, `order_id` and `amount` will be `NULL`.

**The Anti-Join Pattern (Find rows with no match):**
To find customers who have NEVER placed an order, use a `LEFT JOIN` and filter for `NULL` on the right side's primary key.

```sql
SELECT c.name
FROM customers c
LEFT JOIN orders o 
    ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL; -- o.customer_id IS NULL also works
```

### RIGHT JOIN
Functionally identical to `LEFT JOIN`, but reverses the table roles.
`A RIGHT JOIN B` is exactly `B LEFT JOIN A`.

*Why it's almost always rewritable:* Left-to-right reading is standard in Western languages. Writing `FROM a LEFT JOIN b` mentally maps better than `FROM b RIGHT JOIN a`.

*When to use it:* When you have a massive block of joins and you need to preserve the result of a subquery or a view defined at the end of the chain, though CTEs usually solve this cleaner.

```sql
-- Harder to read
SELECT e.name, d.dept_name
FROM employees e
RIGHT JOIN departments d ON e.dept_id = d.dept_id;

-- Preferred
SELECT e.name, d.dept_name
FROM departments d
LEFT JOIN employees e ON d.dept_id = e.dept_id;
```

### FULL OUTER JOIN
Used for reconciliation or finding discrepancies between two systems or tables.
*Note: MySQL does not natively support FULL OUTER JOIN. You must emulate it using a UNION of LEFT JOIN and RIGHT JOIN.*

```sql
-- Find ALL employees and ALL departments, seeing who lacks a department and which departments lack employees.
SELECT 
    e.name AS employee,
    d.dept_name AS department
FROM employees e
FULL OUTER JOIN departments d 
    ON e.dept_id = d.dept_id;
```

### CROSS JOIN
Generates every possible combination. Be extremely careful; crossing a 10k row table with a 10k row table yields 100 million rows.

*Real Use Case: Date Spine Generation.*
Creating a report showing $0 sales for days with no orders.

```sql
-- Assume we have a calendar_dates table
SELECT 
    d.date,
    c.customer_id
FROM calendar_dates d
CROSS JOIN customers c;
-- You'd then LEFT JOIN orders to this matrix to find missing days per customer.
```

### SELF JOIN
Used for hierarchical data (trees) or comparing rows within the same table.

*Classic Use Case: Employee-Manager Hierarchy.*
```sql
SELECT 
    e.name AS employee_name,
    m.name AS manager_name
FROM employees e
LEFT JOIN employees m 
    ON e.manager_id = m.emp_id;
```

## Advanced Join Concepts

### Joining on Multiple Columns (Composite Conditions)
When tables have composite primary keys or require scoped joining.

```sql
-- Example conceptually if orders were partitioned by year
SELECT c.name, o.order_id
FROM customers c
JOIN orders o 
    ON c.customer_id = o.customer_id
    AND EXTRACT(YEAR FROM c.created_at) = EXTRACT(YEAR FROM o.order_date);
```

### Non-Equi Joins
Joining on ranges or inequalities, often used for slowly changing dimensions (SCDs) or spatial data.

```sql
-- Find products whose price is greater than an employee's salary (contrived, but illustrative)
SELECT e.name, p.name
FROM employees e
JOIN products p 
    ON p.price > e.salary;

-- Real use case: Range overlaps
SELECT o.order_id, d.discount_tier
FROM orders o
JOIN discounts d 
    ON o.amount BETWEEN d.min_amount AND d.max_amount;
```

### Join on Expressions vs Columns
Joining on raw columns allows the database engine to easily use indexes (B-Tree). Joining on expressions often forces full table scans unless an expression index exists.

```sql
-- BAD for performance: forces sequential scan on customers if no index on UPPER(email)
SELECT * 
FROM customers c
JOIN some_external_list l 
    ON UPPER(c.email) = UPPER(l.email);

-- PostgreSQL Fix: Create an expression index
-- CREATE INDEX idx_cust_email_upper ON customers (UPPER(email));
```

### Joining More Than 2 Tables
The order of joins matters logically (especially with outer joins) and slightly for the planner, though most modern planners reorder inner joins optimally.

```sql
SELECT 
    o.order_id,
    c.name AS customer_name,
    p.name AS product_name
FROM orders o
INNER JOIN customers c ON o.customer_id = c.customer_id
INNER JOIN products p ON o.product_id = p.product_id;
```
Always put the base table you are querying *about* in the `FROM` clause.

### JOIN vs Subquery vs CTE
- **JOIN**: Best for retrieving columns from multiple tables. Optimizer loves them.
- **Correlated Subquery**: Executes per row. Often slow, but useful for returning a single scalar value.
- **CTE (Common Table Expression)**: Excellent for readability and modularizing complex logic before joining.

```sql
-- CTE approach (Cleanest for complex pre-aggregations)
WITH CustomerTotals AS (
    SELECT customer_id, SUM(amount) as total_spent
    FROM orders
    GROUP BY customer_id
)
SELECT c.name, ct.total_spent
FROM customers c
JOIN CustomerTotals ct ON c.customer_id = ct.customer_id;
```

### The N+1 Query Problem
Common in ORMs (Object-Relational Mappers).
- **The Problem**: You query 100 customers (`SELECT * FROM customers`). Then, for *each* customer in your application loop, you query their orders (`SELECT * FROM orders WHERE customer_id = ?`). This equals 1 + 100 queries.
- **The SQL Fix**: Use a single JOIN.
```sql
SELECT c.*, o.*
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id;
```
Now it's 1 query, and the application reconstructs the objects.

### Duplicate Rows from Joins (Fan-out)
If table A has 1 row and table B has 3 matching rows, a JOIN produces 3 rows. If you just wanted properties of A, you've created duplicates.

*Detection*: The row count of your result is higher than the row count of your driving table (for LEFT JOINs).
*Fix*: Ensure you join on unique keys, or pre-aggregate the right table before joining.

```sql
-- BAD: Duplicates customer names if they have multiple orders
SELECT c.name, c.email
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE o.status = 'COMPLETED';

-- GOOD: Use EXISTS instead if you just want filtering, not columns
SELECT c.name, c.email
FROM customers c
WHERE EXISTS (
    SELECT 1 FROM orders o 
    WHERE o.customer_id = c.customer_id 
    AND o.status = 'COMPLETED'
);
```

## Full Worked Examples

### 1. Find all customers who have never placed an order
```sql
SELECT c.customer_id, c.name, c.email
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL;
```

### 2. Find the manager of each employee
```sql
SELECT 
    emp.name AS employee_name, 
    mgr.name AS manager_name
FROM employees emp
LEFT JOIN employees mgr ON emp.manager_id = mgr.emp_id;
```

### 3. Find products that appear in no orders
```sql
SELECT p.product_id, p.name
FROM products p
LEFT JOIN orders o ON p.product_id = o.product_id
WHERE o.order_id IS NULL;
```

### 4. Reconcile two tables to find discrepancies
(Finding active employees who have no department, OR departments with no active employees)
```sql
SELECT 
    e.emp_id, 
    e.name AS employee_name, 
    d.dept_id, 
    d.dept_name
FROM (SELECT * FROM employees WHERE is_active = TRUE) e
FULL OUTER JOIN departments d ON e.dept_id = d.dept_id
WHERE e.emp_id IS NULL OR d.dept_id IS NULL;
```
