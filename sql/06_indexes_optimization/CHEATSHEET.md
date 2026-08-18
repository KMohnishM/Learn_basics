# Module 6 Cheatsheet: Indexes and Optimization

## Index Types Comparison

| Type | Best For | Characteristics | PostgreSQL Syntax |
| :--- | :--- | :--- | :--- |
| **B-Tree** | Default. `<`, `>`, `=`, `BETWEEN`, `ORDER BY` | Sorted tree. Good for high selectivity. | `USING btree (col)` (default) |
| **Hash** | Pure equality (`=`) | No sorting. Fast exact matches. | `USING hash (col)` |
| **GIN** | JSONB, Arrays, Text Search | Inverted index. Maps elements to rows. | `USING gin (col)` |
| **BRIN** | Massive time-series tables | Block Range Index. Stores min/max per block. Tiny footprint. | `USING brin (created_at)` |

---

## Index Creation Syntax Templates

**1. Standard Index:**
```sql
CREATE INDEX idx_emp_name ON employees(name);
```

**2. Composite Index (Multiple Columns):**
```sql
CREATE INDEX idx_orders_cust_date ON orders(customer_id, order_date);
```

**3. Concurrent Index (Zero Downtime):**
```sql
CREATE INDEX CONCURRENTLY idx_orders_status ON orders(status);
```

**4. Partial Index (Subset of Data):**
```sql
CREATE INDEX idx_active_users ON users(last_login) WHERE is_active = true;
```

**5. Covering Index (Index-Only Scan):**
```sql
CREATE INDEX idx_products_cat ON products(category) INCLUDE (price);
```

**6. Expression Index (Functions):**
```sql
CREATE INDEX idx_cust_email_lower ON customers(LOWER(email));
```

---

## Composite Index Rules

**The Leftmost Prefix Rule:** You must filter on columns starting from the left of the index definition.

Given: `CREATE INDEX idx_comp ON table(A, B, C);`

| Query Filter | Will it use the Index effectively? |
| :--- | :--- |
| `WHERE A = 1` | ✅ Yes |
| `WHERE A = 1 AND B = 2` | ✅ Yes |
| `WHERE A = 1 AND B = 2 AND C = 3` | ✅ Yes |
| `WHERE B = 2 AND C = 3` | ❌ No (Missing A) |
| `WHERE C = 3` | ❌ No (Missing A and B) |
| `WHERE A = 1 AND C = 3` | ⚠️ Partially (Uses A, then scans for C) |

---

## Reading EXPLAIN Output Nodes

| Node Type | What it means |
| :--- | :--- |
| **Seq Scan** | Reads the whole table disk file. Good for small tables or large result sets. |
| **Index Scan** | Reads the index tree, gets pointer, reads the heap (table) row. |
| **Index Only Scan**| Reads the index tree, gets data directly from index. No heap read. Extremely fast. |
| **Bitmap Index Scan**| Scans index to build an in-memory bitmap of matching heap blocks. |
| **Bitmap Heap Scan**| Reads heap blocks sequentially based on the bitmap from the step above. |
| **Nested Loop** | For each row in table A, loops through matching rows in table B. |
| **Hash Join** | Hashes the smaller table into memory, probes it with the larger table. |

---

## Common Slow Patterns & Fixes

| Problem | Example Pattern | How to Fix |
| :--- | :--- | :--- |
| **Function on Column** | `WHERE DATE(created_at) = '2023-01-01'` | Change query: `WHERE created_at >= '2023-01-01' AND created_at < '2023-01-02'` OR use an Expression Index. |
| **Leading Wildcard** | `WHERE name LIKE '%smith%'` | Standard B-Tree can't handle this. Use `pg_trgm` extension and create a GIN index. |
| **Type Mismatch** | `WHERE int_column = '100'` | Ensure data types match to avoid implicit casts disabling indexes. |
| **Index Bloat** | High disk I/O on updates/reads over time | Rebuild index: `REINDEX INDEX CONCURRENTLY idx_name;` Tune autovacuum. |
| **N+1 Queries** | Loop running `SELECT * FROM child WHERE parent_id = ?` | Refactor application code to use a `JOIN` or fetch parents and use `WHERE parent_id IN (...)`. |

---
**Quick Tip:** Always use `EXPLAIN ANALYZE` (not just `EXPLAIN`) when debugging a slow query to see actual execution times vs. planner estimates.
