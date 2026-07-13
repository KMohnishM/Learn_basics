# Module 7: SQL Query Mastering (MySQL)

---

## 1. SQL Logical Query Execution Order

Understanding the order in which a database engine evaluates a query is essential for writing correct and optimized SQL. What you write is not what the database executes:

```
Written SQL Order:                  Logical Execution Order:
1. SELECT                           1. FROM (and JOINs)
2. FROM                             2. ON
3. JOIN                             3. OUTER JOIN (reconstructs table)
4. WHERE                            4. WHERE (filters rows)
5. GROUP BY                         5. GROUP BY (groups rows)
6. HAVING                           6. HAVING (filters groups)
7. ORDER BY                         7. SELECT (evaluates projections & expressions)
8. LIMIT                            8. DISTINCT (removes duplicates)
                                    9. ORDER BY (sorts rows)
                                    10. LIMIT / OFFSET (picks subset)
```

- **Implication**: You cannot use an alias declared in the `SELECT` clause (e.g., `SELECT cost * 1.1 AS total_cost`) in the `WHERE` clause because `WHERE` is evaluated before `SELECT`. However, you *can* use it in `ORDER BY` because `ORDER BY` is evaluated after `SELECT`.

---

## 2. MySQL Constraints & Cascade Operations

DDL (Data Definition Language) defines the structure of the database and enforces business integrity rules at the schema level.

```sql
CREATE TABLE orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    total_amount DECIMAL(10, 2) CHECK (total_amount >= 0.00),
    CONSTRAINT fk_user FOREIGN KEY (user_id) 
        REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
```

### Referential Integrity Action Options:
- **`ON DELETE CASCADE`**: If a parent row (in `users`) is deleted, all child rows (in `orders`) pointing to it are automatically deleted.
- **`ON DELETE SET NULL`**: If a parent row is deleted, the foreign key column in the child rows is set to `NULL` (requires the column to be nullable).
- **`ON DELETE RESTRICT` (or `NO ACTION`)**: The database rejects the deletion of the parent row if any child rows still reference it. (Default behavior in MySQL).

---

## 3. Joins in MySQL

Joins combine rows from two or more tables based on a related column.

```
      INNER JOIN                      LEFT JOIN                     RIGHT JOIN
   ┌───────────┐                   ┌───────────┐                  ┌───────────┐
   │   A ∩ B   │                   │ A (A ∩ B) │                  │ (A ∩ B) B │
   └───────────┘                   └───────────┘                  └───────────┘
```

- **`INNER JOIN`**: Returns rows only when there is a match in both tables.
- **`LEFT JOIN` (or `LEFT OUTER JOIN`)**: Returns all rows from the left table, and the matched rows from the right table. If no match, right-side columns are `NULL`.
- **`RIGHT JOIN`**: Returns all rows from the right table, and matched rows from the left.
- **`CROSS JOIN`**: Returns the Cartesian product of the two tables (every row in A joined with every row in B). No `ON` clause is used.
- **`SELF JOIN`**: A table joined with itself (used for hierarchical tables, e.g., employee with manager ID). Requires using aliases:
  ```sql
  SELECT e.name AS Employee, m.name AS Manager
  FROM employees e
  LEFT JOIN employees m ON e.manager_id = m.id;
  ```

### Emulating FULL OUTER JOIN in MySQL
MySQL does not natively support `FULL OUTER JOIN`. To get all rows from both tables (with NULLs where no matches exist), you must perform a `LEFT JOIN` and a `RIGHT JOIN` and combine them using `UNION`:
```sql
SELECT * FROM table_a a LEFT JOIN table_b b ON a.id = b.id
UNION
SELECT * FROM table_a a RIGHT JOIN table_b b ON a.id = b.id;
```

---

## 4. Advanced Grouping & Aggregations

Aggregations summarize rows into single values.

- **`COUNT(*)`**: Counts the total number of rows returned, including rows containing NULLs.
- **`COUNT(column)`**: Counts only the rows where `column` is **not NULL**.
- **NULL Handling in Aggregates**:
  - `SUM()`, `AVG()`, `MIN()`, `MAX()` **ignore NULL values** completely.
  - If a column contains `[10, 20, NULL]`, `AVG(column)` is $(10 + 20) / 2 = 15$, NOT $(10 + 20 + 0) / 3 = 10$.
  - To treat NULL as 0, use `COALESCE`: `AVG(COALESCE(column, 0))`.

### GROUP BY and HAVING
- `GROUP BY` partitions rows into groups.
- `HAVING` filters those groups *after* aggregation has occurred.
- **Rule**: You cannot use `WHERE` to filter on aggregate values (e.g., `WHERE COUNT(id) > 5` is invalid) because `WHERE` runs before groups are created. You must use `HAVING COUNT(id) > 5`.

---

## 5. Subqueries & Common Table Expressions (CTEs)

### Subqueries
A query nested inside another query.
- **Scalar Subquery**: Returns a single value (1 row, 1 column). Can be used in SELECT, WHERE, or HAVING.
- **Correlated Subquery**: References columns of the outer query. It is evaluated once for each row processed by the outer query (can be slow for large datasets).
  ```sql
  SELECT name FROM products p
  WHERE price > (SELECT AVG(price) FROM products WHERE category = p.category);
  ```
- **`EXISTS` vs `IN`**:
  - `EXISTS` returns true/false as soon as it finds a single match (optimal for early exit).
  - `IN` fetches the entire list of values from the subquery before evaluating.

### Common Table Expressions (CTEs)
A CTE is a temporary named result set that exists only within the scope of a single query. It is cleaner and more readable than nested subqueries:
```sql
WITH regional_sales AS (
    SELECT region, SUM(amount) AS total_sales
    FROM orders
    GROUP BY region
)
SELECT region, total_sales
FROM regional_sales
WHERE total_sales > 100000;
```

### Recursive CTEs (`WITH RECURSIVE`)
Used to query hierarchical or graph data (e.g., organizational charts, category trees):
```sql
WITH RECURSIVE org_chart AS (
    -- Anchor member: Start with the CEO (manager_id is NULL)
    SELECT id, name, manager_id, 1 AS level
    FROM employees
    WHERE manager_id IS NULL
    
    UNION ALL
    
    -- Recursive member: Join with children
    SELECT e.id, e.name, e.manager_id, o.level + 1
    FROM employees e
    INNER JOIN org_chart o ON e.manager_id = o.id
)
SELECT * FROM org_chart;
```

---

## 6. Window Functions (MySQL 8.0+)

Window functions perform calculations across a set of table rows that are somehow related to the current row, without collapsing the rows into a single summary row (unlike `GROUP BY`).

### Syntax
```sql
FUNCTION() OVER (
    PARTITION BY partition_column
    ORDER BY sort_column
    FRAME_CLAUSE
)
```

### Key Window Functions

#### 1. Ranking Functions
- **`ROW_NUMBER()`**: Assigns a unique sequential integer starting from 1.
- **`RANK()`**: Assigns ranking; if duplicate values exist, they get the same rank, and the next rank is skipped (e.g., `1, 2, 2, 4`).
- **`DENSE_RANK()`**: Like `RANK()`, but no ranks are skipped (e.g., `1, 2, 2, 3`).

```sql
SELECT name, department, salary,
       ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) as row_num,
       RANK() OVER (PARTITION BY department ORDER BY salary DESC) as rnk,
       DENSE_RANK() OVER (PARTITION BY department ORDER BY salary DESC) as dense_rnk
FROM employees;
```

#### 2. Offset Functions
- **`LAG(column, offset)`**: Accesses data from a previous row in the partition (default offset = 1).
- **`LEAD(column, offset)`**: Accesses data from a subsequent row in the partition.
- Useful for calculating period-over-period growth rates.

#### 3. Frame Clauses (`ROWS` vs `RANGE`)
Defines the subset of the partition (the "frame") used for the calculation relative to the current row:
- `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`: Running total from the start of the partition to the current row (default behavior when `ORDER BY` is present).
- `ROWS BETWEEN 6 PRECEDING AND CURRENT ROW`: 7-day moving average calculation.
