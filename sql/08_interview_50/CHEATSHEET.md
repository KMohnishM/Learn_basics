# SQL Interview Cheatsheet

## Problem-Type Recognition Table

| If the prompt asks for... | Reach for... |
| :--- | :--- |
| "Top N within each group" | `RANK()` or `DENSE_RANK()` partitioned by group |
| "Previous/Next value in sequence" | `LAG()` or `LEAD()` |
| "Cumulative sum / Running total" | `SUM() OVER(ORDER BY ...)` |
| "Moving average" | Window functions with `ROWS BETWEEN` |
| "Find records with NO match" | `LEFT JOIN` + `WHERE id IS NULL` or `NOT EXISTS` |
| "Compare row to group average" | Window function: `AVG() OVER(PARTITION BY ...)` |
| "First/Last record per group" | `ROW_NUMBER() OVER(PARTITION BY ... ORDER BY ...)` |
| "Consecutive streaks / Islands" | `date - ROW_NUMBER()` trick |
| "Convert Rows to Columns" | Conditional Aggregation (`SUM(CASE WHEN...)`) |
| "Hierarchy or Tree traversal" | Recursive CTE (`WITH RECURSIVE`) |
| "Month-over-month growth" | `LAG()` to get previous month, then math |
| "Rolling 7-day metrics" | `ROWS BETWEEN 6 PRECEDING AND CURRENT ROW` |

---

## One-Line Solution Templates (The 12 Most Common Patterns)

**1. Top N per Group**
```sql
WITH Ranked AS (SELECT *, DENSE_RANK() OVER(PARTITION BY group_col ORDER BY val DESC) as rnk FROM t) SELECT * FROM Ranked WHERE rnk <= N;
```

**2. Anti-Join (Find non-matching)**
```sql
SELECT a.* FROM tableA a LEFT JOIN tableB b ON a.id = b.id WHERE b.id IS NULL;
```

**3. Running Total**
```sql
SELECT date, SUM(amount) OVER (ORDER BY date) as cumulative_amt FROM sales;
```

**4. Moving Average (7-day)**
```sql
SELECT date, AVG(val) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) FROM metrics;
```

**5. First Event per User**
```sql
WITH First As (SELECT *, ROW_NUMBER() OVER(PARTITION BY user_id ORDER BY timestamp ASC) as rn FROM events) SELECT * FROM First WHERE rn = 1;
```

**6. Month-over-Month Growth**
```sql
SELECT month, rev, (rev - LAG(rev) OVER(ORDER BY month)) / LAG(rev) OVER(ORDER BY month) as growth FROM monthly_rev;
```

**7. Conditional Aggregation (Pivot)**
```sql
SELECT user_id, SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as successes FROM jobs GROUP BY user_id;
```

**8. Median Calculation**
```sql
WITH Cnt AS (SELECT val, ROW_NUMBER() OVER(ORDER BY val) as rn, COUNT(*) OVER() as c FROM t) SELECT AVG(val) FROM Cnt WHERE rn IN ((c+1)/2, (c+2)/2);
```

**9. Rolling Date Overlaps**
```sql
SELECT a.id FROM spans a JOIN spans b ON a.id=b.id AND a.start < b.end AND a.end > b.start;
```

**10. Gaps and Islands (Streaks)**
```sql
SELECT MIN(date), MAX(date), COUNT(*) FROM (SELECT date, date - (ROW_NUMBER() OVER(ORDER BY date) * INTERVAL '1 day') as grp FROM t) sub GROUP BY grp;
```

**11. Update using Subquery**
```sql
UPDATE target SET col = (SELECT val FROM source WHERE target.id = source.id) WHERE EXISTS (SELECT 1 FROM source WHERE target.id = source.id);
```

**12. Cross Join for Permutations**
```sql
SELECT items.name, sizes.size FROM items CROSS JOIN sizes;
```

---

## Interview Approach Checklist

Before you write `SELECT`:
- [ ] **Acknowledge and Clarify:** Repeat the question. Ask about NULLs, duplicates, and expected grain of output.
- [ ] **Data Types:** Check if dates need formatting (`DATE_TRUNC`) or numbers need casting.
- [ ] **Plan:** Say your plan out loud. "I will use a CTE to filter, then join, then aggregate."

While Coding:
- [ ] **Format:** Capitalize keywords, indent subqueries, use table aliases (`employees e`).
- [ ] **Iterate:** Write the innermost CTE first. Explain what it outputs.
- [ ] **Join types:** Explicitly state why you chose `LEFT JOIN` or `INNER JOIN`.

After Coding:
- [ ] **Edge Cases:** Walk through a NULL row or duplicate row in your head against your code.
- [ ] **Performance:** Mention if a window function saves you an expensive self-join.
- [ ] **Review:** Do not wait for the interviewer to find the missing `GROUP BY`. Check your aggregates.
