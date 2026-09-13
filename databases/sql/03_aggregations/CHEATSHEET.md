# SQL Aggregations Cheatsheet

## Aggregate Function Behavior with NULLs

| Function | Ignores NULLs? | Result if all inputs are NULL | Description |
| :--- | :--- | :--- | :--- |
| `COUNT(*)` | No | 0 | Counts all rows, including NULLs. |
| `COUNT(col)` | Yes | 0 | Counts non-NULL values in `col`. |
| `SUM(col)` | Yes | NULL | Sum of non-NULL values. |
| `AVG(col)` | Yes | NULL | Average of non-NULL values (Sum / Count(col)). |
| `MIN(col)` | Yes | NULL | Minimum non-NULL value. |
| `MAX(col)` | Yes | NULL | Maximum non-NULL value. |

*Note: To treat NULLs as zero in AVG, use `AVG(COALESCE(col, 0))`.*

## Execution Order: WHERE vs HAVING

```text
1. FROM / JOIN     <-- Define data sources
2. WHERE           <-- Filter RAW rows (No aggregates allowed)
3. GROUP BY        <-- Define aggregation buckets
4. HAVING          <-- Filter AGGREGATED groups (Aggregates allowed)
5. SELECT          <-- Project final columns
6. ORDER BY        <-- Sort final output
```

## Conditional Aggregation Syntax

**PostgreSQL (Modern / Preferred): The `FILTER` Clause**
```sql
SELECT 
    SUM(amount) FILTER (WHERE status = 'paid') AS paid_total
FROM orders;
```

**Universal Standard (MySQL, SQL Server, Oracle): `CASE` Statement**
```sql
SELECT 
    SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END) AS paid_total
FROM orders;
```

## Advanced Grouping Comparison

Given `GROUP BY ___ (A, B)`:

| Construct | Output Groupings Generated | Use Case |
| :--- | :--- | :--- |
| `ROLLUP(A, B)` | `(A, B)`, `(A)`, `()` | Hierarchical subtotals (e.g., Year/Month totals) |
| `CUBE(A, B)` | `(A, B)`, `(A)`, `(B)`, `()` | All possible intersections (Cross-tabular reports) |
| `GROUPING SETS((A), (B))`| `(A)`, `(B)` | Specific distinct groupings only |

## Common Aggregation Patterns

### 1. Pivoting Data (Rows to Columns)
```sql
SELECT
    dept_id,
    SUM(CASE WHEN is_active = true THEN 1 ELSE 0 END) AS active_emps,
    SUM(CASE WHEN is_active = false THEN 1 ELSE 0 END) AS inactive_emps
FROM employees
GROUP BY dept_id;
```

### 2. Concatenating Strings within Groups
**PostgreSQL:**
```sql
SELECT dept_id, STRING_AGG(name, ', ') FROM employees GROUP BY dept_id;
```
**MySQL:**
```sql
SELECT dept_id, GROUP_CONCAT(name SEPARATOR ', ') FROM employees GROUP BY dept_id;
```

### 3. Detecting Rollup Rows
Use `GROUPING()` to identify if a NULL in the result set is due to a subtotal row.
```sql
SELECT 
    CASE WHEN GROUPING(category) = 1 THEN 'Grand Total' ELSE category END AS cat,
    SUM(amount) 
FROM products p JOIN orders o USING (product_id)
GROUP BY ROLLUP(category);
```
