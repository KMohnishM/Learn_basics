# Solution

The most optimal index for the query `SELECT * FROM orders WHERE user_id = 49281 ORDER BY order_date DESC;` is a **Composite Index** on `user_id` and `order_date`.

```sql
CREATE INDEX idx_user_orders ON orders (user_id, order_date DESC);
```

## Why this works (The B-Tree Internals):

Order matters in a composite index! 

If you create an index on `(user_id, order_date)`, the database builds a B-Tree sorted primarily by `user_id`, and then sub-sorted by `order_date`.

1. **The Filter**: The database traverses the B-Tree to instantly find the block of records where `user_id = 49281`. 
2. **The Sort**: Because we added `order_date` as the second column in the index, the records belonging to user 49281 are *already physically sorted by date* inside the index! 

The database doesn't need to do an expensive in-memory `Sort` operation anymore. It just grabs the records and returns them immediately. 

If you created the index backwards `(order_date, user_id)`, the B-tree would be sorted by date first. The database would not be able to instantly find user 49281, and would have to scan massive portions of the index. Always index the equality filter (`WHERE user_id = X`) before the range/sort filter (`ORDER BY`).
