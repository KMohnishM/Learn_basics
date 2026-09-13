# Window Functions Cheatsheet

## Syntax Anatomy
```sql
FUNCTION_NAME(expr) OVER (
    [PARTITION BY col1, col2] 
    [ORDER BY col3 ASC|DESC] 
    [ROWS|RANGE BETWEEN frame_start AND frame_end]
)
```

## Ranking Functions Comparison
| Function | Description | Tie Behavior (Scores: 100, 100, 90) |
| :--- | :--- | :--- |
| `ROW_NUMBER()` | Unique integer for every row | 1, 2, 3 (Arbitrary on tie) |
| `RANK()` | Rank with gaps after ties | 1, 1, 3 |
| `DENSE_RANK()` | Rank with NO gaps after ties | 1, 1, 2 |
| `NTILE(n)` | Divides into `n` equal buckets | Bucket number (1 to n) |

## Offset Functions
```sql
-- Previous Row
LAG(column, offset, default_value) OVER (ORDER BY col)

-- Next Row
LEAD(column, offset, default_value) OVER (ORDER BY col)

-- First Value in Frame
FIRST_VALUE(column) OVER (ORDER BY col)

-- Last Value in Frame (REQUIRES EXPLICIT FRAME TO WORK AS EXPECTED)
LAST_VALUE(column) OVER (ORDER BY col ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
```

## Window Frame Options
*Format:* `[ROWS | RANGE] BETWEEN <start> AND <end>`

**Boundaries:**
- `UNBOUNDED PRECEDING`: Absolute start of partition
- `N PRECEDING`: N rows before current
- `CURRENT ROW`: The current row
- `N FOLLOWING`: N rows after current
- `UNBOUNDED FOLLOWING`: Absolute end of partition

**Default Frame Behavior:**
- If `ORDER BY` is missing: `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING`
- If `ORDER BY` is present: `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`

## Common Patterns

### 1. Running Total
```sql
SELECT date, amount, SUM(amount) OVER (ORDER BY date) as running_total
FROM sales;
```

### 2. Rolling Average (e.g., 7 rows)
```sql
SELECT date, amount, 
       AVG(amount) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
FROM sales;
```

### 3. Top-N per Group (e.g., Highest salary per dept)
```sql
WITH Ranked AS (
    SELECT emp_id, dept_id, salary,
           DENSE_RANK() OVER (PARTITION BY dept_id ORDER BY salary DESC) as rnk
    FROM employees
)
SELECT * FROM Ranked WHERE rnk <= 3;
```

### 4. Deduplication (Keep latest record)
```sql
WITH Dedup AS (
    SELECT id, 
           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY updated_at DESC) as rn
    FROM users
)
SELECT * FROM Dedup WHERE rn = 1;
```

### 5. Year-Over-Year / Month-Over-Month Difference
```sql
SELECT month, revenue,
       revenue - LAG(revenue, 1) OVER (ORDER BY month) as revenue_growth
FROM monthly_metrics;
```
