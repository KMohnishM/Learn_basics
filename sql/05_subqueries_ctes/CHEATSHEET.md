# Module 5 Cheatsheet: Subqueries & CTEs

## Subquery Types

| Type | Description | Where Used | Example |
| :--- | :--- | :--- | :--- |
| **Scalar** | Returns 1 row, 1 column (single value) | `SELECT`, `WHERE`, `HAVING` | `WHERE salary > (SELECT AVG(salary)...)` |
| **Row** | Returns 1 row, multiple columns | `WHERE` | `WHERE (dept, mgr) = (SELECT dept, mgr...)` |
| **Table** | Returns multiple rows/columns | `FROM`, `IN`, `EXISTS` | `FROM (SELECT id FROM...) AS sub` |

---

## IN vs EXISTS vs NOT IN vs NOT EXISTS

| Operator | Usage Semantic | Performance Note | NULL Handling Behavior |
| :--- | :--- | :--- | :--- |
| `IN` | Matches against a list of values. | Slower for large sets, may materialize. | Safe. Ignores NULLs in list. |
| `EXISTS` | Checks for presence of rows. | **Faster.** Uses short-circuit evaluation. | Safe. Only checks row existence. |
| `NOT IN` | Matches none in list. | Evaluates all values. | **DANGER!** If subquery returns any NULL, returns 0 rows. |
| `NOT EXISTS` | Checks absence of rows. | **Preferred for negation.** Efficient. | Safe. Immune to the NULL trap. |

---

## Common Table Expressions (CTEs) Template

### Simple CTE
```sql
WITH sales_summary AS (
    SELECT customer_id, SUM(amount) AS total
    FROM orders
    GROUP BY customer_id
),
top_customers AS (
    SELECT customer_id
    FROM sales_summary
    WHERE total > 1000
)
SELECT c.name, s.total
FROM top_customers t
JOIN customers c ON t.customer_id = c.customer_id
JOIN sales_summary s ON t.customer_id = s.customer_id;
```

### Recursive CTE Template
```sql
WITH RECURSIVE recursive_cte_name AS (
    -- 1. Anchor Member (Base case, runs once)
    SELECT id, parent_id, 1 AS depth
    FROM hierarchy_table
    WHERE parent_id IS NULL
    
    UNION ALL
    
    -- 2. Recursive Member (Loops until it returns 0 rows)
    SELECT child.id, child.parent_id, parent.depth + 1
    FROM hierarchy_table child
    JOIN recursive_cte_name parent ON child.parent_id = parent.id
)
-- 3. Final Output
SELECT * FROM recursive_cte_name;
```

## Recursive CTE Structure Diagram
```text
┌────────────────────────────┐
│   ANCHOR QUERY (Base)      │ -> Initial Results
└─────────────┬──────────────┘
              │ UNION ALL
┌─────────────▼──────────────┐
│  RECURSIVE QUERY (Loop)    │ -> Joins against previous iteration's results
└─────────────┬──────────────┘
              │ (Loops until empty set)
┌─────────────▼──────────────┐
│   MAIN OUTER SELECT        │ -> Returns combined results
└────────────────────────────┘
```

---

## Correlated Subquery Refactoring Patterns

**Problem: Row-By-Agonizing-Row (RBAR)**
Correlated subqueries execute once for *every* row in the outer query.

### Pattern 1: Refactoring Aggregates in SELECT to Window Functions

**Bad (Correlated):**
```sql
SELECT name, salary,
  (SELECT AVG(salary) FROM employees e2 WHERE e2.dept_id = e1.dept_id) as dept_avg
FROM employees e1;
```

**Good (Window Function):**
```sql
SELECT name, salary,
  AVG(salary) OVER (PARTITION BY dept_id) as dept_avg
FROM employees;
```

### Pattern 2: Refactoring WHERE EXISTS logic to JOINs

While `EXISTS` is fast, sometimes a standard `JOIN` provides a better execution plan when retrieving data from both tables.

**Subquery:**
```sql
SELECT name 
FROM customers c
WHERE EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id);
```

**JOIN (If duplicates are not an issue or grouped):**
```sql
SELECT DISTINCT c.name
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id;
```
