# SQL Joins Cheatsheet

## Quick Reference Visuals

```text
INNER JOIN              LEFT JOIN               RIGHT JOIN
  ---     ---             ---     ---             ---     ---
 |   |===|   |           |===|===|   |           |   |===|===|
  ---     ---             ---     ---             ---     ---
 Matches only            All Left + Matches      All Right + Matches

FULL OUTER JOIN         CROSS JOIN              ANTI-JOIN (Left)
  ---     ---             ---     ---             ---     ---
 |===|===|===|           | X | x | Y |           |===|   |   |
  ---     ---             ---     ---             ---     ---
 All rows, both sides    Cartesian Product       Left ONLY (no match)
```

## Syntax Templates

### 1. INNER JOIN (Intersection)
*Use when: You only want records that exist in BOTH tables.*
```sql
SELECT a.col1, b.col2
FROM table_a a
INNER JOIN table_b b ON a.id = b.a_id;
```

### 2. LEFT JOIN (Enrichment)
*Use when: You want all base records, and related data IF it exists.*
```sql
SELECT a.col1, b.col2
FROM table_a a
LEFT JOIN table_b b ON a.id = b.a_id;
```

### 3. RIGHT JOIN
*Note: Usually rewritten as a LEFT JOIN for readability.*
```sql
SELECT a.col1, b.col2
FROM table_a a
RIGHT JOIN table_b b ON a.id = b.a_id;
```

### 4. FULL OUTER JOIN
*Use when: You need everything from both tables (Reconciliation).*
```sql
SELECT a.col1, b.col2
FROM table_a a
FULL OUTER JOIN table_b b ON a.id = b.a_id;
```

### 5. CROSS JOIN
*Use when: You need every possible combination (N * M rows).*
```sql
SELECT a.col1, b.col2
FROM table_a a
CROSS JOIN table_b b;
```

### 6. SELF JOIN
*Use when: Hierarchical data (manager/employee).*
```sql
SELECT t1.col1, t2.col2
FROM table_a t1
JOIN table_a t2 ON t1.parent_id = t2.id;
```

---

## Essential Patterns

### The Anti-Join (Find missing records)
Find rows in Table A that do NOT exist in Table B.
```sql
SELECT a.*
FROM table_a a
LEFT JOIN table_b b ON a.id = b.a_id
WHERE b.id IS NULL; -- Must check a non-nullable column on the right side
```

### The Multiple Condition Join
Filtering during the join phase rather than the WHERE phase.
```sql
SELECT a.*, b.*
FROM table_a a
LEFT JOIN table_b b 
    ON a.id = b.a_id 
    AND b.is_active = TRUE; -- Keeps all 'a', only attaches active 'b'
```

### The Range Join (Non-Equi Join)
```sql
SELECT p.product_name, t.tax_rate
FROM products p
JOIN tax_brackets t 
    ON p.price BETWEEN t.min_price AND t.max_price;
```

---

## Decision Guide: JOIN vs Subquery

| Scenario | Recommendation | Example Pattern |
| :--- | :--- | :--- |
| Need columns from Table A and Table B | **JOIN** | `SELECT a.x, b.y FROM a JOIN b` |
| Filter Table A based on existence in Table B | **EXISTS** (Subquery) | `WHERE EXISTS (SELECT 1 FROM b WHERE b.a_id = a.id)` |
| Filter Table A based on non-existence in B | **NOT EXISTS** / Anti-Join | `WHERE NOT EXISTS (...)` |
| Need aggregate from Table B attached to Table A | **CTE + JOIN** | `WITH aggs AS (...) SELECT * FROM a JOIN aggs` |
| Need a single scalar value per row | **Correlated Subquery** | `SELECT a.x, (SELECT MAX(y) FROM b WHERE...)` (Careful: Slow) |

---

## Common Pitfalls

1. **Fan-out / Duplicates**: If joining one-to-many, the left table rows will duplicate. Fix by pre-aggregating the many-side.
2. **`WHERE` vs `ON` in Outer Joins**: 
   - `ON condition`: Evaluated *during* the join. Failed conditions result in `NULL` right-side values.
   - `WHERE condition`: Evaluated *after* the join. Failed conditions remove the entire row.
3. **Data Type Mismatch**: Joining `INT` to `VARCHAR` requires implicit casting, which disables index usage and causes full table scans. Always join on matching data types.
