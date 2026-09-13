# Module 1: SQL Fundamentals

This module covers the foundational aspects of SQL querying. It focuses on the anatomy of the SELECT statement, data types, NULL semantics, and essential functions using PostgreSQL syntax (while noting significant MySQL differences).

## 1. The Anatomy of a SELECT Statement

The `SELECT` statement is the cornerstone of SQL. While we write SQL in one order, the database engine executes it in a completely different order. Understanding this execution order is critical for writing correct and optimized queries.

### Write Order vs. Execution Order

**Write Order:**
1. `SELECT`
2. `FROM`
3. `WHERE`
4. `GROUP BY`
5. `HAVING`
6. `ORDER BY`
7. `LIMIT` / `OFFSET`

**Execution Order:**
1. `FROM` (and `JOIN`) - Choose and join tables to get base data.
2. `WHERE` - Filter the base data.
3. `GROUP BY` - Aggregate the filtered data.
4. `HAVING` - Filter the aggregated data.
5. `SELECT` - Return the final columns (and evaluate expressions like `DISTINCT`).
6. `ORDER BY` - Sort the final result set.
7. `LIMIT` / `OFFSET` - Restrict the number of rows returned.

**Why this matters:**
You cannot use column aliases defined in the `SELECT` clause within the `WHERE` clause because `WHERE` is executed *before* `SELECT`. You *can* use them in `ORDER BY` because it is executed *after*.

```sql
-- This will FAIL: 'total_cost' does not exist when WHERE is evaluated
SELECT 
    quantity * amount AS total_cost
FROM orders
WHERE total_cost > 1000;

-- This will SUCCEED: 'total_cost' exists when ORDER BY is evaluated
SELECT 
    quantity * amount AS total_cost
FROM orders
ORDER BY total_cost DESC;
```

## 2. Aliases and Identifiers

Aliases provide temporary names for columns or tables.

### Column Aliases
Use the `AS` keyword (optional but recommended for readability).
```sql
SELECT 
    emp_id AS employee_id,
    name full_name -- AS is omitted, but still works
FROM employees;
```

### Table Aliases
Crucial for joins and self-joins.
```sql
SELECT 
    e.name,
    d.dept_name
FROM employees AS e
JOIN departments AS d ON e.dept_id = d.dept_id;
```

### Quotes and Backticks
- **PostgreSQL / ANSI SQL:** Use double quotes `""` for identifiers (table/column names) and single quotes `''` for string literals.
- **MySQL:** Uses backticks `` ` `` for identifiers by default.

```sql
-- PostgreSQL
SELECT "name" FROM "employees" WHERE name = 'John Doe';
```

## 3. The WHERE Clause

The `WHERE` clause filters rows before aggregation.

### Comparison Operators
`=`, `<`, `>`, `<=`, `>=`, `<>` or `!=`

### BETWEEN and IN
`BETWEEN` is inclusive on both ends.
```sql
SELECT order_id FROM orders WHERE amount BETWEEN 100 AND 500;
-- Equivalent to: amount >= 100 AND amount <= 500
```
`IN` checks against a list of values.
```sql
SELECT name FROM customers WHERE country IN ('USA', 'Canada', 'UK');
```

### Pattern Matching (LIKE)
- `%` matches zero or more characters.
- `_` matches exactly one character.
- Use `ILIKE` in PostgreSQL for case-insensitive matching.

```sql
SELECT name FROM products WHERE name LIKE 'MacBook%'; -- Starts with MacBook
SELECT name FROM products WHERE name LIKE '%Pro';     -- Ends with Pro
SELECT name FROM products WHERE name LIKE '_Phone';   -- e.g., iPhone
```

### NULL Comparisons
You can **NEVER** use `= NULL` or `!= NULL`. This is because `NULL` represents an unknown value. The result of `unknown = unknown` is `unknown` (NULL), not TRUE.

**Incorrect:**
```sql
SELECT * FROM employees WHERE manager_id = NULL; -- Returns 0 rows
```
**Correct:**
```sql
SELECT * FROM employees WHERE manager_id IS NULL;
SELECT * FROM employees WHERE manager_id IS NOT NULL;
```

## 4. DISTINCT

`DISTINCT` removes duplicate rows from the result set.

```sql
SELECT DISTINCT category FROM products;
```

**Performance Cost:**
`DISTINCT` requires the database engine to sort or hash the results to identify duplicates, which can be highly expensive on large datasets. Use it only when necessary.

**DISTINCT ON (PostgreSQL Specific):**
Allows you to keep the "first" row of each group based on an `ORDER BY` clause.
```sql
-- Get the most recent order for each customer
SELECT DISTINCT ON (customer_id) 
    customer_id, order_id, order_date
FROM orders
ORDER BY customer_id, order_date DESC;
```

## 5. ORDER BY

Sorts the result set. Default is `ASC` (ascending).

```sql
SELECT name, salary FROM employees ORDER BY salary DESC;
```

**Ordering by Position:**
You can use column indexes (1-based), but it is generally discouraged as it breaks if the `SELECT` list changes.
```sql
SELECT name, salary FROM employees ORDER BY 2 DESC;
```

**NULLS FIRST / NULLS LAST:**
Controls where NULL values appear. Default for ASC is NULLS LAST, for DESC is NULLS FIRST (in PostgreSQL).
```sql
SELECT name, manager_id FROM employees ORDER BY manager_id DESC NULLS LAST;
```

## 6. LIMIT and OFFSET

Used to restrict the number of rows returned, often for pagination.

```sql
-- Get the top 10 most expensive products
SELECT name, price FROM products ORDER BY price DESC LIMIT 10;

-- Get the next 10 (Page 2)
SELECT name, price FROM products ORDER BY price DESC LIMIT 10 OFFSET 10;
```

**The OFFSET Performance Problem:**
`OFFSET N` forces the database to compute the first `N` rows, scan them, and then discard them. `OFFSET 1000000` is incredibly slow.
*Alternative:* Use keyset pagination (cursor-based pagination).
```sql
-- Instead of OFFSET 100, assuming the last seen product_id was 50
SELECT name, price FROM products WHERE product_id > 50 ORDER BY product_id ASC LIMIT 10;
```

## 7. Data Types

Choosing the correct data type is essential for performance and data integrity.

### Numeric Types
- `INTEGER`: Standard 4-byte integer (-2B to +2B).
- `BIGINT`: 8-byte integer for very large numbers (e.g., global IDs).
- `NUMERIC(p, s)` / `DECIMAL(p, s)`: Exact precision. Used for money. `p` is total digits, `s` is fractional digits.
- `FLOAT` / `DOUBLE PRECISION`: Approximate precision. Faster but imprecise.

### Character Types
- `VARCHAR(n)`: Variable-length string with a limit.
- `CHAR(n)`: Fixed-length string. Pads with spaces if shorter. Use only for strictly fixed data (e.g., 2-letter country codes).
- `TEXT`: Variable-length with unlimited length (PostgreSQL preferred over VARCHAR without length limit).

### Boolean
- `BOOLEAN`: Can be `TRUE`, `FALSE`, or `NULL`.

### Date/Time
- `DATE`: Date only (YYYY-MM-DD).
- `TIMESTAMP`: Date and time without timezone context.
- `TIMESTAMPTZ` (Timestamp with Time Zone): The absolute best practice for storing dates/times in PostgreSQL. Stores UTC internally.

### Semi-Structured
- `JSON`: Stores JSON as exact text.
- `JSONB` (PostgreSQL): Stores JSON in a decomposed binary format. Supports indexing. Always prefer `JSONB` over `JSON`.
- `UUID`: 128-bit universally unique identifier.

## 8. NULL Semantics

### Three-Valued Logic
SQL uses three-valued logic: `TRUE`, `FALSE`, and `NULL` (Unknown).
- `TRUE AND NULL` = `NULL`
- `FALSE AND NULL` = `FALSE`
- `TRUE OR NULL` = `TRUE`
- `FALSE OR NULL` = `NULL`
- `NOT NULL` = `NULL`

### NULL in Arithmetic
Any arithmetic operation involving `NULL` results in `NULL`.
```sql
SELECT 10 + NULL; -- NULL
```

### NULL in Aggregations
Aggregate functions (`SUM`, `COUNT`, `AVG`) ignore `NULL` values.
```sql
-- If column 'salary' has values: 100, 200, NULL
SELECT COUNT(salary); -- Returns 2
SELECT COUNT(*);      -- Returns 3 (counts rows)
```

### Handling NULLs
- `COALESCE(val1, val2, ...)`: Returns the first non-NULL value.
```sql
SELECT name, COALESCE(manager_id, 0) AS safe_manager FROM employees;
```
- `NULLIF(val1, val2)`: Returns NULL if `val1 = val2`, otherwise returns `val1`. Useful to prevent division by zero.
```sql
SELECT quantity / NULLIF(amount, 0) FROM orders;
```

## 9. Type Casting

Converting a value from one type to another.

### Explicit Casting
```sql
-- Standard SQL
SELECT CAST('100' AS INTEGER);

-- PostgreSQL Shorthand
SELECT '100'::INTEGER;
SELECT '2023-01-01'::DATE;
```

## 10. String Functions

- `CONCAT(str1, str2, ...)` or `||` operator.
```sql
SELECT name || ' - ' || category AS product_info FROM products;
```
- `SUBSTRING(string FROM start FOR length)`
- `UPPER(string)` / `LOWER(string)`
- `TRIM(string)`: Removes leading/trailing spaces.
- `LENGTH(string)`: Number of characters.
- `REPLACE(string, from, to)`
- `SPLIT_PART(string, delimiter, field)` (PostgreSQL)

```sql
SELECT REPLACE(email, '@example.com', '@gmail.com') FROM customers;
```

## 11. Date Functions

- `NOW()` / `CURRENT_TIMESTAMP`: Current transaction time (TIMESTAMPTZ).
- `CURRENT_DATE`: Current date.
- `DATE_TRUNC('precision', source)`: Truncates a timestamp to the specified precision (e.g., 'month', 'day').
```sql
-- Get the start of the month for the order date
SELECT DATE_TRUNC('month', order_date) FROM orders;
```
- `EXTRACT(field FROM source)` or `DATE_PART('field', source)`: Retrieves subfields like year or hour.
```sql
SELECT EXTRACT(YEAR FROM order_date) FROM orders;
```
- `AGE(timestamp)`: Subtracts arguments, producing a "symbolic" result that uses years and months.
- **Interval Arithmetic:**
```sql
SELECT NOW() - INTERVAL '30 days';
SELECT order_date + INTERVAL '1 year' FROM orders;
```

## 12. CASE Expression

SQL's `if/then/else` logic.

### Simple CASE
Compares an expression against simple values.
```sql
SELECT 
    name,
    CASE category
        WHEN 'Electronics' THEN 'Tech'
        WHEN 'Clothing' THEN 'Apparel'
        ELSE 'Other'
    END AS simplified_category
FROM products;
```

### Searched CASE
Evaluates boolean expressions. More flexible.
```sql
SELECT 
    order_id,
    CASE 
        WHEN amount > 1000 THEN 'High Value'
        WHEN amount > 500 THEN 'Medium Value'
        ELSE 'Low Value'
    END AS value_tier
FROM orders;
```

### CASE in Aggregations (Conditional Aggregation)
Extremely powerful pattern for pivoting data.
```sql
SELECT 
    customer_id,
    COUNT(CASE WHEN status = 'Shipped' THEN 1 END) AS shipped_orders,
    COUNT(CASE WHEN status = 'Cancelled' THEN 1 END) AS cancelled_orders
FROM orders
GROUP BY customer_id;
```
