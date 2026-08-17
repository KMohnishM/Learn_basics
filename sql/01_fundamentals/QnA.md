# Module 1: Questions and Answers

**1. What is the execution order of a SQL SELECT statement? Why does it matter?**
The execution order is: `FROM` -> `WHERE` -> `GROUP BY` -> `HAVING` -> `SELECT` -> `ORDER BY` -> `LIMIT`. 
It matters immensely for query structuring. Because `SELECT` is evaluated late in the process, you cannot use column aliases defined in the `SELECT` clause within the `WHERE`, `GROUP BY`, or `HAVING` clauses. For example, if you do `SELECT price * quantity AS total FROM orders WHERE total > 100`, the query will fail because `total` does not exist when the `WHERE` clause is processed. You can, however, use aliases in the `ORDER BY` clause since it executes after `SELECT`.

**2. Why does `WHERE column = NULL` never return results?**
In SQL, `NULL` does not mean "zero" or "empty string"; it represents an "unknown" or "missing" value. When you use the equality operator (`=`) to compare anything to an unknown value, the result is also unknown (`NULL`). The `WHERE` clause only returns rows where the condition evaluates to `TRUE`. Since `unknown = unknown` evaluates to `NULL` (not `TRUE`), it filters out everything. You must use the `IS NULL` or `IS NOT NULL` operators to check for the presence or absence of a value.

**3. What is the difference between CHAR and VARCHAR? When would you use CHAR?**
`CHAR(n)` is a fixed-length character type. If you store a string shorter than `n`, the database pads it with spaces up to length `n`. `VARCHAR(n)` is a variable-length character type. It only consumes storage for the actual string length plus a small header to record the length. You should almost always use `VARCHAR` or `TEXT`. You would only use `CHAR` for data that is strictly fixed in length, such as 2-letter ISO country codes ('US', 'CA') or fixed-length hashes (like MD5), as it can theoretically offer a marginal performance benefit in those specific cases by avoiding length calculation overhead.

**4. What is three-valued logic in SQL?**
Unlike standard boolean logic which has two states (TRUE and FALSE), SQL logic evaluates to TRUE, FALSE, or NULL (Unknown). This primarily affects logical operators (`AND`, `OR`, `NOT`).
- `TRUE AND NULL` evaluates to `NULL`.
- `FALSE AND NULL` evaluates to `FALSE` (since one false makes the AND false regardless of the unknown).
- `TRUE OR NULL` evaluates to `TRUE` (since one true makes the OR true).
- `FALSE OR NULL` evaluates to `NULL`.
Understanding this is critical when writing complex `WHERE` clauses involving `NULL` values.

**5. How does DISTINCT work internally? What is the performance cost?**
To determine unique rows, the database engine must compare every row in the result set against every other row. It typically does this by either sorting the result set entirely or building an in-memory hash table. For large datasets, this requires significant CPU cycles, memory, and potentially disk I/O (if the sort spills to disk). Therefore, `DISTINCT` carries a high performance penalty. It is often a code smell indicating a bad `JOIN` (causing a cartesian product) and should not be used as a lazy way to fix duplicate rows.

**6. What is the difference between COALESCE and NULLIF?**
`COALESCE(val1, val2, ...)` takes a list of arguments and returns the first one that is not `NULL`. It is used to provide default values (e.g., `COALESCE(manager_id, 0)`).
`NULLIF(val1, val2)` takes exactly two arguments. It returns `NULL` if `val1` equals `val2`; otherwise, it returns `val1`. It is effectively the inverse operation and is most commonly used to prevent division-by-zero errors.

**7. How does OFFSET-based pagination perform at scale? What is the alternative?**
`OFFSET N` performs terribly at scale. To return `LIMIT 10 OFFSET 1000000`, the database engine must generate 1,000,010 rows, scan through the first million, discard them, and return the last 10. The time taken grows linearly with the offset size. The alternative is "keyset pagination" (also known as cursor-based pagination). Instead of skipping rows blindly, you use a unique, sorted column (like an ID or timestamp) to filter the next page: `WHERE id > last_seen_id ORDER BY id ASC LIMIT 10`. This can utilize indexes effectively and remains fast regardless of page depth.

**8. What is TIMESTAMPTZ vs TIMESTAMP? Which should you prefer and why?**
`TIMESTAMP` (Timestamp Without Time Zone) stores a date and time exactly as entered, completely devoid of context. `TIMESTAMPTZ` (Timestamp With Time Zone) converts the entered time to UTC upon storage, and then converts it back to the client's local time zone upon retrieval. You should universally prefer `TIMESTAMPTZ`. Without it, you cannot accurately compare times across different geographies, handle daylight saving time changes, or migrate servers to different physical locations without corrupting the meaning of your stored data.

**9. Explain CASE expression with an example of using it inside an aggregation.**
The `CASE` expression is SQL's mechanism for conditional logic (if/then/else). Using it inside an aggregation is a technique called "conditional aggregation," which is powerful for pivoting row data into columns.
```sql
SELECT 
    dept_id,
    COUNT(CASE WHEN is_active = TRUE THEN 1 END) AS active_employees,
    COUNT(CASE WHEN is_active = FALSE THEN 1 END) AS inactive_employees
FROM employees
GROUP BY dept_id;
```
Because aggregate functions like `COUNT` ignore `NULL` values, the `CASE` statement only yields a `1` when the condition is met, and implicitly yields `NULL` otherwise. Thus, the `COUNT` only tallies rows matching the specific condition for that column.

**10. What is the difference between LIKE and ILIKE?**
Both are used for pattern matching string data using wildcards (`%` for any number of characters, `_` for one character). `LIKE` is case-sensitive, meaning 'Apple' will not match 'apple'. `ILIKE` is a PostgreSQL-specific extension that performs case-insensitive pattern matching. Note that in some dialects like MySQL, `LIKE` is case-insensitive by default depending on the table collation.

**11. How does date arithmetic work in SQL? Give an example of finding records from the last 30 days.**
Date arithmetic involves adding or subtracting standard units of time (intervals) from a date or timestamp column. You can use the `INTERVAL` keyword to specify the amount of time.
```sql
SELECT order_id, order_date
FROM orders
WHERE order_date >= NOW() - INTERVAL '30 days';
```
This takes the current exact time (`NOW()`), subtracts exactly 30 days of time from it, and filters for orders that occurred on or after that resulting timestamp.

**12. What is the difference between EXTRACT and DATE_TRUNC?**
`EXTRACT(field FROM source)` isolates and returns a specific numerical part of a timestamp, such as the month (1-12) or the year (e.g., 2023) as an integer or numeric type. It loses the rest of the date context.
`DATE_TRUNC('field', source)` rounds a timestamp down to the beginning of the specified precision. For instance, `DATE_TRUNC('month', '2023-10-15 14:30:00')` returns a full timestamp representing the start of that month: `2023-10-01 00:00:00`. It is primarily used for grouping data by time periods (e.g., monthly sales).

**13. Write a query to find all customers whose names start with 'A' or 'B' and whose orders are from the last 90 days.**
```sql
SELECT DISTINCT c.customer_id, c.name
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE (c.name LIKE 'A%' OR c.name LIKE 'B%')
  AND o.order_date >= NOW() - INTERVAL '90 days';
```
*(Note: Parentheses around the `OR` conditions are strictly necessary due to operator precedence, as `AND` binds more tightly than `OR`.)*

**14. What happens when you ORDER BY a column that has NULLs?**
When sorting, the database must decide whether `NULL` values are treated as the highest possible values or the lowest possible values. In PostgreSQL, by default, `NULL` values are considered larger than any non-NULL value. Therefore, in an `ORDER BY col ASC`, NULLs appear at the very bottom. In an `ORDER BY col DESC`, they appear at the very top. You can override this behavior explicitly using the `NULLS FIRST` or `NULLS LAST` modifiers.

**15. How does NULLIF help prevent division-by-zero errors?**
A division-by-zero operation (`10 / 0`) will crash the query and throw an error. `NULLIF(expression, 0)` checks if the expression evaluates to `0`. If it does, it returns `NULL`. If it does not, it returns the original expression. Because any arithmetic operation involving `NULL` results in `NULL`, `10 / NULLIF(0, 0)` becomes `10 / NULL`, which safely evaluates to `NULL` instead of throwing an error.
