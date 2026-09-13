# Exercise: Optimizing a Slow Query

Imagine you have just launched an e-commerce platform. It was fast at first, but now that you have 1 million users, the "Order History" page takes 5 seconds to load!

Your database looks like this:

```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INT,
    product_id INT,
    order_date DATE,
    total_amount DECIMAL
);
```

The application runs this exact query to load the page:
```sql
SELECT * FROM orders WHERE user_id = 49281 ORDER BY order_date DESC;
```

## Your Task

When you run `EXPLAIN ANALYZE` on that query in production, you see a `Seq Scan` (Sequential Scan) on the `orders` table followed by a memory `Sort` operation. This is horribly slow.

You decide to add an index.

Write the exact SQL command to create the **most optimal composite index** for this specific query.

*Hint 1: A composite index covers multiple columns.*
*Hint 2: Order matters in composite indexes! Think about what the database is filtering by FIRST, and what it is sorting by SECOND.*

Write your answer in `solution/fix.md`.
