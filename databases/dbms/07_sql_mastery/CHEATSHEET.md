# Advanced SQL Cheatsheet (PostgreSQL)

## 1. Window Functions
| Syntax / Function | Description | Example |
| :--- | :--- | :--- |
| `OVER (...)` | Defines the window. Required for window functions. | `SUM(val) OVER (PARTITION BY dep ORDER BY date)` |
| `ROW_NUMBER()` | Unique integer for each row in partition. No gaps. | `ROW_NUMBER() OVER(ORDER BY salary DESC)` |
| `RANK()` | Rank with gaps for ties (1, 1, 3). | `RANK() OVER(ORDER BY salary DESC)` |
| `DENSE_RANK()` | Rank with NO gaps for ties (1, 1, 2). | `DENSE_RANK() OVER(ORDER BY salary DESC)` |
| `LAG(col, n)` | Access value `n` rows before current row. | `LAG(revenue, 1) OVER(ORDER BY month)` |
| `LEAD(col, n)` | Access value `n` rows after current row. | `LEAD(revenue, 1) OVER(ORDER BY month)` |
| `FIRST_VALUE(col)` | First value in the window frame. | `FIRST_VALUE(name) OVER(PARTITION BY dep ORDER BY salary)` |
| `NTH_VALUE(col, n)` | Nth value in the window frame. | `NTH_VALUE(name, 2) OVER(PARTITION BY dep ORDER BY salary)` |

## 2. Window Frame Clauses (Inside OVER)
*Default if ORDER BY is present:* `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`
*Default if NO ORDER BY:* `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING`

| Frame Type | Description | Usage Note |
| :--- | :--- | :--- |
| `ROWS` | Physical rows. Ignored ties. | Best for strictly sequential data (e.g., exactly 3 previous rows). |
| `RANGE` | Logical boundaries. Groups ties. | Best for date ranges or when ties should share a total. |
| `UNBOUNDED PRECEDING` | From the start of the partition. | Used for cumulative sums. |
| `N PRECEDING` | N rows/values before current. | Used for moving averages. |
| `CURRENT ROW` | The current row (or peers for RANGE). | End point for running totals. |
| `UNBOUNDED FOLLOWING` | To the end of the partition. | Required to find last values. |

## 3. Advanced Aggregation
| Feature | Syntax Example | Use Case |
| :--- | :--- | :--- |
| `FILTER` | `SUM(amt) FILTER (WHERE status = 'PAID')` | Clean pivot tables, conditional aggregation. |
| `GROUPING SETS` | `GROUP BY GROUPING SETS ((a,b), (a), ())` | Specific combinations of subtotals and grand totals. |
| `ROLLUP` | `GROUP BY ROLLUP (year, month, day)` | Hierarchical subtotals (Year -> Month -> Day). |
| `CUBE` | `GROUP BY CUBE (color, size)` | All possible multidimensional subtotals (cross-tabs). |
| `GROUPING()` | `SELECT GROUPING(dep) ...` | Returns 1 if column is a subtotal/grand total row, 0 if raw data. |

## 4. Recursive CTEs
```sql
WITH RECURSIVE cte_name AS (
    SELECT ... -- 1. Base Case
    UNION ALL
    SELECT ... FROM cte_name WHERE ... -- 2. Recursive Step
)
SELECT * FROM cte_name;
```

## 5. JSONB Operators (PostgreSQL)
| Operator | Description | Example | Returns True For |
| :--- | :--- | :--- | :--- |
| `->` | Get JSON object/array (returns JSONB) | `'{"a":1}'::jsonb -> 'a'` | N/A (Returns `1`) |
| `->>` | Get JSON text (returns Text) | `'{"a":1}'::jsonb ->> 'a'` | N/A (Returns `'1'`) |
| `#>` | Get at path (returns JSONB) | `doc #> '{a, b}'` | N/A |
| `#>>`| Get at path (returns Text) | `doc #>> '{a, b}'` | N/A |
| `@>` | Contains (Right side inside Left) | `'{"a":1, "b":2}'::jsonb @> '{"a":1}'` | Indexable containment check. |
| `?` | Key exists at top level | `'{"a":1, "b":2}'::jsonb ? 'b'` | Simple existence check. |
| `?\|` | Any key exists | `'{"a":1}'::jsonb ?\| array['a', 'b']` | True (a exists). |
| `?&` | All keys exist | `'{"a":1}'::jsonb ?& array['a', 'b']` | False (b is missing). |

## 6. Advanced Modification Patterns
**UPSERT (Insert on Conflict)**
```sql
INSERT INTO table (id, val) VALUES (1, 100)
ON CONFLICT (id) 
DO UPDATE SET val = table.val + EXCLUDED.val; -- EXCLUDED is the proposed row
```

**MERGE (PostgreSQL 15+)**
```sql
MERGE INTO target t USING source s ON t.id = s.id
WHEN MATCHED AND s.is_deleted THEN DELETE
WHEN MATCHED THEN UPDATE SET val = s.val
WHEN NOT MATCHED THEN INSERT (id, val) VALUES (s.id, s.val);
```

**DELETE RETURNING (CTE Pattern)**
```sql
WITH moved AS (
    DELETE FROM source_table WHERE status = 'OLD' RETURNING *
)
INSERT INTO archive_table SELECT * FROM moved;
```

**Generate Series (Date Spines)**
```sql
SELECT day::date FROM generate_series('2023-01-01'::date, '2023-12-31'::date, '1 day'::interval) as day;
```
