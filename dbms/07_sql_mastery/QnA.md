# Q&A — SQL Query Mastering (MySQL)

---

## 🟢 Easy

**Q1. What is the logical execution order of an SQL query? Why does it matter?**

1. `FROM` (and JOINs)
2. `ON`
3. `WHERE`
4. `GROUP BY`
5. `HAVING`
6. `SELECT`
7. `DISTINCT`
8. `ORDER BY`
9. `LIMIT` / `OFFSET`

**Why it matters**: It explains query errors. For example, you cannot use an alias defined in `SELECT` inside a `WHERE` clause because `WHERE` runs before `SELECT`. However, you can use it in `ORDER BY` because `ORDER BY` runs after `SELECT`.

---

**Q2. Compare `UNION` and `UNION ALL`. Which is faster and why?**

- **`UNION`**: Combines the results of two queries, removing duplicate rows.
- **`UNION ALL`**: Combines the results of two queries, preserving all rows (including duplicates).

**Performance**: **`UNION ALL` is faster** because the database engine simply appends the second result set to the first. `UNION` requires sorting the combined result set and performing duplicate elimination, which is CPU and memory-intensive (often spilling to disk for large datasets).

---

**Q3. What do `ON DELETE CASCADE` and `ON DELETE SET NULL` do?**

They define the action to take on child rows in a foreign key relationship when the corresponding parent row is deleted:
- **`ON DELETE CASCADE`**: Automatically deletes the child rows (e.g., if you delete a `User`, all `Orders` belonging to that user are deleted).
- **`ON DELETE SET NULL`**: Sets the foreign key column in the child rows to `NULL` (requires the foreign key column to be nullable). Useful for keeping history (e.g., keeping orders but removing the personal user reference).

---

## 🟡 Medium

**Q4. Contrast `ROW_NUMBER()`, `RANK()`, and `DENSE_RANK()`.**

Suppose we partition by department and order by salary (descending) with values: `[100, 90, 90, 80]`.

- **`ROW_NUMBER()`**: Assigns a sequential, unique integer: `1, 2, 3, 4`. No duplicates, no gaps.
- **`RANK()`**: Assigns equal ranks to duplicates, and skips the next ranks: `1, 2, 2, 4`. Has duplicate values and gaps.
- **`DENSE_RANK()`**: Assigns equal ranks to duplicates, but does not skip any ranks: `1, 2, 2, 3`. Has duplicates, no gaps.

---

**Q5. How do SQL aggregate functions handle NULL values? How can you calculate average while treating NULL as 0?**

- **Aggregation Handling**: Functions like `SUM()`, `AVG()`, `COUNT(column)`, `MIN()`, and `MAX()` **ignore NULL values** entirely. 
  - E.g., if a column has values `[10, 20, NULL]`, `AVG(column)` calculates $(10 + 20) / 2 = 15$. It does not count the NULL row in the denominator.
  - Exception: `COUNT(*)` counts all rows including NULL rows.
- **Treating NULL as 0**: Use the `COALESCE` or `IFNULL` function to convert NULLs before aggregating:
  ```sql
  SELECT AVG(COALESCE(score, 0)) FROM exams;
  ```
  This will evaluate as $(10 + 20 + 0) / 3 = 10$.

---

**Q6. How do you perform a FULL OUTER JOIN in MySQL?**

MySQL does not support `FULL OUTER JOIN` directly. You must emulate it by combining a `LEFT JOIN` and a `RIGHT JOIN` using `UNION` (which eliminates duplicates):
```sql
SELECT a.id, a.name, b.amount
FROM table_a a
LEFT JOIN table_b b ON a.id = b.id

UNION

SELECT a.id, a.name, b.amount
FROM table_a a
RIGHT JOIN table_b b ON a.id = b.id;
```

---

## 🔴 Hard

**Q7. Write a MySQL query to find the $N$-th highest salary from the `employees` table. Provide both a modern window function approach and a legacy compatible approach.**

#### Option 1: Modern Window Function (MySQL 8.0+)
Using `DENSE_RANK()` to handle duplicate salaries correctly:
```sql
WITH RankedSalaries AS (
    SELECT salary,
           DENSE_RANK() OVER (ORDER BY salary DESC) AS rnk
    FROM employees
)
SELECT DISTINCT salary
FROM RankedSalaries
WHERE rnk = N;  -- Replace N with the target rank (e.g., 3 for 3rd highest)
```

#### Option 2: Legacy LIMIT / OFFSET (MySQL-Specific)
This is simple but requires offset math (Offset = $N-1$):
```sql
SELECT DISTINCT salary
FROM employees
ORDER BY salary DESC
LIMIT 1 OFFSET N-1; -- Offset is N-1 (e.g., OFFSET 2 for 3rd highest)
```

#### Option 3: Correlated Subquery (Universal SQL)
Finds the salary where exactly $N-1$ salaries are greater than it:
```sql
SELECT DISTINCT e1.salary
FROM employees e1
WHERE N-1 = (
    SELECT COUNT(DISTINCT e2.salary)
    FROM employees e2
    WHERE e2.salary > e1.salary
);
```

---

**Q8. Given a `user_logins(user_id, login_date)` table, write a query to identify all users who have logged in on 3 or more consecutive days.**

#### The Solution (ROW_NUMBER Difference Pattern)
This is a classic SQL puzzle. If dates are consecutive, subtracting a sequential row number from the date will yield a **constant date** for that streak.

```sql
WITH UniqueLogins AS (
    -- Remove multiple logins on the same day
    SELECT DISTINCT user_id, DATE(login_date) AS login_day
    FROM user_logins
),
SequencedLogins AS (
    -- Assign row numbers grouped by user
    SELECT user_id, login_day,
           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY login_day) AS row_num
    FROM UniqueLogins
),
StreakGroups AS (
    -- Subtract row number (as days) from login_day to find the streak start group
    SELECT user_id, login_day,
           DATE_SUB(login_day, INTERVAL row_num DAY) AS streak_start
    FROM SequencedLogins
)
-- Group by user and streak_start, and filter groups with count >= 3
SELECT user_id, 
       MIN(login_day) AS streak_start_date,
       MAX(login_day) AS streak_end_date,
       COUNT(*) AS consecutive_days
FROM StreakGroups
GROUP BY user_id, streak_start
HAVING COUNT(*) >= 3;
```

---

**Q9. Write a query to fetch the manager hierarchy for each employee in the `employees(id, name, manager_id)` table. Output should list the employee, their path to the CEO, and their hierarchical level.**

#### The Solution (Recursive CTE)
```sql
WITH RECURSIVE org_hierarchy AS (
    -- Anchor: Start with the CEO (manager_id is NULL)
    SELECT id, name, manager_id,
           1 AS level,
           CAST(name AS CHAR(255)) AS manager_path
    FROM employees
    WHERE manager_id IS NULL
    
    UNION ALL
    
    -- Recursive step: Join child employees with their parent manager
    SELECT e.id, e.name, e.manager_id,
           h.level + 1 AS level,
           CONCAT(h.manager_path, ' -> ', e.name) AS manager_path
    FROM employees e
    INNER JOIN org_hierarchy h ON e.manager_id = h.id
)
SELECT name AS employee,
       level,
       manager_path
FROM org_hierarchy
ORDER BY level, name;
```
- **How it works**: The anchor member grabs the root of the hierarchy (level 1). The recursive member joins the base table against the CTE (`org_hierarchy`) to build paths dynamically. `CONCAT` appends names to build the routing chain.
