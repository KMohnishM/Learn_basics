# Module 1: SQL Cheatsheet

## Execution Order
```text
1. FROM / JOIN     (Get the base data)
2. WHERE           (Filter rows)
3. GROUP BY        (Group data)
4. HAVING          (Filter groups)
5. SELECT          (Return columns / evaluate AS aliases)
6. ORDER BY        (Sort results)
7. LIMIT / OFFSET  (Paginate results)
```
*Note: Column aliases defined in `SELECT` cannot be used in `WHERE`, `GROUP BY`, or `HAVING`.*

## NULL Comparison Rules
| Expression | Result |
| :--- | :--- |
| `WHERE col = NULL` | **FAIL** (Always returns 0 rows) |
| `WHERE col != NULL` | **FAIL** (Always returns 0 rows) |
| `WHERE col IS NULL` | **PASS** (Matches NULL values) |
| `WHERE col IS NOT NULL`| **PASS** (Matches non-NULL values) |
| `10 + NULL` | `NULL` |
| `TRUE AND NULL` | `NULL` |
| `FALSE AND NULL` | `FALSE` |
| `TRUE OR NULL` | `TRUE` |

## Data Type Quick Reference
| Type | Use Case | PostgreSQL Example |
| :--- | :--- | :--- |
| `INTEGER` | Standard IDs, counts, integers | `142` |
| `BIGINT` | Very large numbers, global IDs | `9876543210` |
| `NUMERIC(p,s)` | Exact precision, Money | `NUMERIC(10,2)` -> `19.99` |
| `VARCHAR(n)` | Strings with a max limit | `VARCHAR(255)` |
| `TEXT` | Unlimited length strings | `TEXT` |
| `BOOLEAN` | True/False/Null flags | `TRUE` |
| `TIMESTAMPTZ` | Absolute date & time (Best Practice) | `2023-10-15 14:30:00+00` |
| `JSONB` | Flexible semi-structured data | `'{"key": "value"}'::jsonb` |
| `UUID` | Unique 128-bit identifiers | `'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'` |

## Core String Functions
```sql
-- Concatenation
SELECT first_name || ' ' || last_name;
SELECT CONCAT(first_name, ' ', last_name);

-- Case modification
SELECT UPPER(name), LOWER(name);

-- Substrings (1-indexed)
SELECT SUBSTRING('PostgreSQL' FROM 1 FOR 4); -- 'Post'

-- Replacing text
SELECT REPLACE('foo bar foo', 'foo', 'baz'); -- 'baz bar baz'

-- Trimming whitespace
SELECT TRIM('  hello  '); -- 'hello'
```

## Core Date Functions
```sql
-- Current Date/Time
SELECT NOW();               -- 2023-10-27 10:00:00.123+00
SELECT CURRENT_DATE;        -- 2023-10-27

-- Extracting parts (returns numbers)
SELECT EXTRACT(YEAR FROM order_date);  -- 2023
SELECT EXTRACT(MONTH FROM order_date); -- 10

-- Truncating dates (returns timestamps)
SELECT DATE_TRUNC('month', order_date); -- 2023-10-01 00:00:00+00
SELECT DATE_TRUNC('day', order_date);   -- 2023-10-27 00:00:00+00

-- Date Arithmetic
SELECT NOW() - INTERVAL '7 days';
SELECT NOW() + INTERVAL '1 month';
```

## CASE Expression Syntax
**1. Simple CASE (Exact matches)**
```sql
CASE category_id
    WHEN 1 THEN 'Electronics'
    WHEN 2 THEN 'Clothing'
    ELSE 'Other'
END
```

**2. Searched CASE (Boolean logic)**
```sql
CASE
    WHEN price > 1000 AND status = 'Active' THEN 'Premium'
    WHEN price > 500 THEN 'Standard'
    ELSE 'Basic'
END
```

**3. Conditional Aggregation (Pivoting)**
```sql
COUNT(CASE WHEN status = 'Shipped' THEN 1 END) AS shipped_count
SUM(CASE WHEN is_refunded = TRUE THEN amount ELSE 0 END) AS total_refunds
```

## Crucial Control Flow Functions
```sql
-- Return first non-null value (Great for defaults)
COALESCE(description, 'No description provided')

-- Return NULL if arguments match (Great for avoiding Division by Zero)
NULLIF(denominator, 0)
```
