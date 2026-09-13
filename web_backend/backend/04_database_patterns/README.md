# Module 4: Advanced Database Patterns

The database is almost always the bottleneck in a backend service. This module covers the patterns that distinguish engineers who can ship fast, correct systems from those who accidentally introduce data loss and performance crises.

---

## 1. The N+1 Problem

The N+1 problem is one of the most common — and most preventable — performance killers in production backends. It happens when you fetch a collection and then make one additional query per item.

### Example

```python
# Fetch all blog posts
posts = db.query("SELECT * FROM posts LIMIT 100")

# For each post, fetch its author — THIS IS N+1!
for post in posts:
    author = db.query("SELECT * FROM users WHERE id = %s", post.author_id)
    post.author = author
```

This is 1 query for posts + 100 queries for authors = 101 queries total. On a table with millions of rows, this buries your database.

### Solutions

**JOIN (preferred for SQL)**
```sql
SELECT posts.*, users.name as author_name, users.email as author_email
FROM posts
JOIN users ON posts.author_id = users.id
LIMIT 100;
```
One query. Always prefer JOINs over application-level loops.

**Eager Loading (SQLAlchemy)**
```python
from sqlalchemy.orm import selectinload

posts = session.execute(
    select(Post).options(selectinload(Post.author))
).scalars().all()
# Generates: SELECT * FROM posts; SELECT * FROM users WHERE id IN (1, 2, 3, ...)
```

**DataLoader Pattern (GraphQL)**
Batches individual per-record lookups into a single query (covered in API Design module).

---

## 2. Query Optimization with EXPLAIN ANALYZE

Never guess why a query is slow. Use `EXPLAIN ANALYZE`.

```sql
EXPLAIN ANALYZE
SELECT * FROM orders WHERE customer_id = 42 AND status = 'pending'
ORDER BY created_at DESC
LIMIT 20;
```

**Reading the output:**

```
Seq Scan on orders (cost=0.00..45000.00 rows=2 width=120) (actual time=0.100..8234.543 rows=15 loops=1)
  Filter: (customer_id = 42 AND status = 'pending')
  Rows Removed by Filter: 5000000
Planning Time: 2.3 ms
Execution Time: 8238.2 ms
```

**Key things to look for:**
- `Seq Scan`: Full table scan — no index is being used. Very slow for large tables.
- `Index Scan`: Using an index. Fast.
- `Bitmap Heap Scan`: Using an index to collect row pointers, then fetching. Good.
- `Rows Removed by Filter`: Many rows are being loaded and discarded — you need an index.

**Adding the right index:**
```sql
-- Composite index: covers both filter conditions AND the ORDER BY
CREATE INDEX CONCURRENTLY idx_orders_customer_status_created
ON orders(customer_id, status, created_at DESC);
```

After this index, the same query runs in <1ms.

### Composite Index Column Order

The order of columns in a composite index matters enormously. The index is only useful for queries that filter on the **leftmost** columns first.

`CREATE INDEX ON orders(customer_id, status, created_at)`:
- ✅ `WHERE customer_id = 42 AND status = 'pending'` — uses index
- ✅ `WHERE customer_id = 42` — uses index (partial)
- ❌ `WHERE status = 'pending'` — does NOT use this index!

**Rule**: Put the most selective (highest cardinality) column first. Put equality conditions before range conditions.

---

## 3. Database Transactions and Isolation Levels

### ACID Properties (Deep Dive)

**Atomicity**: A transaction either fully succeeds or fully fails. If you transfer $100 from Account A to Account B, and the system crashes after debiting A but before crediting B, the debit is rolled back. No money is lost.

**Consistency**: Transactions can only bring the database from one valid state to another. Constraints (foreign keys, unique constraints, check constraints) are enforced within transactions.

**Isolation**: Concurrent transactions behave as if they were serial. Transaction A doesn't see partial results from Transaction B that hasn't committed yet.

**Durability**: Once a transaction commits, it stays committed. Even if the server crashes immediately after, the data is safe (because it was written to the WAL — Write-Ahead Log — before commit).

### Isolation Levels

SQL defines four isolation levels, each with different anomalies they allow:

**Read Uncommitted**: Allows **dirty reads** — reading uncommitted data from another transaction. Almost never used.

**Read Committed** (PostgreSQL default): No dirty reads. Can have **non-repeatable reads**: reading the same row twice in one transaction might give different results if another transaction commits between the two reads.

**Repeatable Read**: No dirty reads, no non-repeatable reads. Can have **phantom reads**: a second query for a range might return different rows if another transaction inserted rows in that range.

**Serializable**: The gold standard. No anomalies. Transactions are completely isolated. Slowest.

### SELECT FOR UPDATE — Pessimistic Locking

```python
async with db.begin():
    # Lock the row so no other transaction can read/modify it
    account = await db.execute(
        select(Account)
        .where(Account.id == account_id)
        .with_for_update()   # Acquires a row-level lock
    )
    account = account.scalar_one()
    
    if account.balance < amount:
        raise InsufficientFunds()
    
    account.balance -= amount
    # Lock is released when transaction commits
```

This prevents two concurrent withdrawals from both seeing the same balance and both succeeding.

---

## 4. CQRS — Command Query Responsibility Segregation

The core idea: separate the data model for reads from the data model for writes.

**Commands** (writes): Strict consistency required. All business rules enforced. Can be slower.
**Queries** (reads): Optimized for speed and the specific shape of data needed. Can be denormalized.

### The Problem CQRS Solves

```python
# Normalized write model (correct)
class Order:
    id, customer_id, status, created_at

class OrderItem:
    id, order_id, product_id, quantity, unit_price

# But to display an order summary, you need:
# customer name, each item's product name, total price
# That's 3 tables, 2 JOINs, always
```

With CQRS, you maintain a separate **read model** (materialized view or Redis cache) that's pre-joined and exactly shaped for your UI.

```python
# Write side: strict, normalized
def place_order(customer_id, items):
    order = Order(customer_id=customer_id)
    db.add(order)
    for item in items:
        db.add(OrderItem(order_id=order.id, ...))

# Read side: denormalized, pre-computed, fast
def get_order_summary(order_id):
    # Read from Redis or a materialized view — no JOINs needed
    return redis.get(f"order_summary:{order_id}")

# Update read side when write side changes (event-driven)
def on_order_placed(event):
    summary = build_summary(event.order_id)  # Do the JOIN once
    redis.set(f"order_summary:{event.order_id}", summary)
```

---

## 5. Event Sourcing

Traditional persistence: store the **current state** of an object.

```
Account table: {id: 1, balance: $850}
```

Event Sourcing: store every **event** that happened to an object. The current state is derived by replaying all events.

```
Events table:
  {account_id: 1, type: "deposited", amount: 1000, at: 09:00}
  {account_id: 1, type: "withdrew", amount: 150, at: 10:30}
  → Current balance: $1000 - $150 = $850
```

### Advantages
- **Audit log for free**: Every change is recorded with who did it and when.
- **Time travel**: Reconstruct the account balance at any point in time.
- **Event replay**: If you add a new feature, replay all historical events through the new logic.
- **Debugging**: When something goes wrong, you can see exactly what sequence of events led to the bad state.

### Disadvantages
- Current state requires replaying all events (mitigated with snapshots)
- More complex to implement and query
- Eventual consistency when projecting read models

---

## 6. Zero-Downtime Database Migrations

Running `ALTER TABLE ADD COLUMN NOT NULL` on a 50M row table in production? That table is **locked for writes for 30 minutes** while Postgres rewrites every row.

### The Expand/Contract Pattern

Split breaking schema changes into multiple phases:

**Phase 1: Expand** (backwards compatible)
- Add new column as nullable (no lock!)
- Deploy new code that writes to BOTH old and new columns
- Backfill historical data: `UPDATE table SET new_col = ... WHERE new_col IS NULL LIMIT 1000` (batched!)

**Phase 2: Contract**
- Once backfill is complete, add the NOT NULL constraint (with a default, to avoid a full table rewrite)
- Deploy code that only uses the new column
- Drop the old column in a future release

```sql
-- Phase 1: Safe, no lock
ALTER TABLE users ADD COLUMN phone VARCHAR(20);

-- Backfill in batches to avoid a long lock
UPDATE users SET phone = '' WHERE id BETWEEN 1 AND 10000 AND phone IS NULL;
-- Repeat...

-- Phase 2: Add constraint (fast, no row rewrite if using DEFAULT)
ALTER TABLE users ALTER COLUMN phone SET NOT NULL,
                  ALTER COLUMN phone SET DEFAULT '';
```

---

## Next Steps

Go to `labs/` to build a bank account system using Event Sourcing with CQRS!
