# Cheat Sheet — SQL Query Mastering (MySQL)

## Logical Execution Order
```
1. FROM (and JOINs)
2. ON
3. WHERE
4. GROUP BY
5. HAVING
6. SELECT
7. DISTINCT
8. ORDER BY
9. LIMIT / OFFSET
```

---

## Join Cheat Sheet

- **Inner Join**: Match in both tables
  ```sql
  SELECT * FROM A INNER JOIN B ON A.id = B.id;
  ```
- **Left Join**: All A, matched B (NULLs on right if unmatched)
  ```sql
  SELECT * FROM A LEFT JOIN B ON A.id = B.id;
  ```
- **Self Join**: Table joined with itself
  ```sql
  SELECT e.name, m.name FROM employees e LEFT JOIN employees m ON e.manager_id = m.id;
  ```
- **MySQL Full Outer Join emulation**:
  ```sql
  SELECT * FROM A LEFT JOIN B ON A.id = B.id
  UNION
  SELECT * FROM A RIGHT JOIN B ON A.id = B.id;
  ```

---

## MySQL Window Functions (MySQL 8.0+)

### Syntax
```sql
FUNCTION() OVER (PARTITION BY col1 ORDER BY col2 [FRAME_CLAUSE])
```

### Key Functions
- **`ROW_NUMBER()`**: Unique sequence `1, 2, 3, 4`.
- **`RANK()`**: Sequence with gaps `1, 2, 2, 4`.
- **`DENSE_RANK()`**: Sequence without gaps `1, 2, 2, 3`.
- **`LAG(col, N)`**: Get value from $N$ rows prior (default $N=1$).
- **`LEAD(col, N)`**: Get value from $N$ rows after.

### Common Frame Clauses
- **Running Total** (Default when `ORDER BY` is present):
  ```sql
  ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ```
- **Moving Average** (e.g., 7-day average):
  ```sql
  ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ```

---

## Common Table Expressions (CTEs)

### Standard CTE Template
```sql
WITH cte_name AS (
    SELECT col FROM table WHERE condition
)
SELECT * FROM cte_name;
```

### Recursive CTE Template
```sql
WITH RECURSIVE cte_name AS (
    -- Anchor member
    SELECT id, name, manager_id FROM employees WHERE manager_id IS NULL
    UNION ALL
    -- Recursive member
    SELECT e.id, e.name, e.manager_id 
    FROM employees e INNER JOIN cte_name c ON e.manager_id = c.id
)
SELECT * FROM cte_name;
```

---

## MySQL DDL & Constraints

```sql
CREATE TABLE table_name (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    age INT CHECK (age >= 18),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    parent_id INT,
    FOREIGN KEY (parent_id) REFERENCES parent_table(id)
        ON DELETE CASCADE -- Actions: CASCADE, SET NULL, RESTRICT
);
```

---

## NULL Invariants
- `col = NULL` or `col != NULL` $\implies$ **Always evaluates to UNKNOWN/FALSE** (use `IS NULL` or `IS NOT NULL`).
- `COUNT(*)` $\implies$ Counts all rows (including NULL rows).
- `COUNT(col)` $\implies$ Counts only rows where `col` is NOT NULL.
- `SUM()`, `AVG()`, `MIN()`, `MAX()` $\implies$ **Ignore NULL values**.
- `COALESCE(val1, val2, val3)` $\implies$ Returns the first non-null value.
