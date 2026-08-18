# Interview Strategy Q&A

**1. How should you approach a SQL interview question you've never seen before?**
Never start coding immediately. Follow a structured approach:
1. Re-read the prompt out loud and confirm the goal.
2. Examine the schema and sample data. Look for edge cases (NULLs, duplicates, one-to-many relationships).
3. Think about the output. Write down the expected columns.
4. Verbally formulate a plan (e.g., "I'll join these two tables, filter for X, and aggregate by Y").
5. Write the code iteratively, starting with the core query and wrapping it in CTEs or window functions if necessary.

**2. What clarifying questions should you ask before writing the query?**
Ask questions that define edge cases:
- "Are there NULL values in this column?"
- "Can an employee belong to multiple departments, or just one?"
- "How should ties be handled? (e.g., if two people have the top salary)"
- "What granularity do you want the final output? (per day, per month, per user?)"
- "Do we want to include users who have NO actions? (Determines LEFT JOIN vs INNER JOIN)."

**3. What are the most commonly tested SQL topics across top companies?**
The core pillars are:
- **Window Functions:** `ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`, `LEAD()`, `LAG()`.
- **Aggregations & Grouping:** `GROUP BY`, `HAVING`, conditional aggregations (`SUM(CASE WHEN...)`).
- **Joins:** Especially `LEFT JOIN` to find non-matching records, and Self-Joins.
- **CTEs (Common Table Expressions):** Structuring complex queries for readability.
- **Date/Time Manipulation:** `DATE_TRUNC`, `EXTRACT`, date intervals.

**4. How do you think through a window function problem step by step?**
Break it down into three parts:
- **Function:** What am I calculating? (e.g., `SUM()`, `RANK()`).
- **PARTITION BY:** What is the grouping grain? (e.g., per department, per user). If calculating over the whole dataset, omit this.
- **ORDER BY:** In what sequence should the calculation occur? (e.g., chronological order for running totals, descending order for ranks).

**5. When should you reach for a CTE vs a subquery in an interview setting?**
Always default to CTEs. CTEs make code readable top-to-bottom, which is critical when an interviewer is reading your code live. Subqueries can quickly become deeply nested and difficult to debug. The only exception is very simple `IN` or `EXISTS` clauses where a one-line subquery is cleaner.

**6. How do you explain your query choices to the interviewer?**
Talk through the logical order of operations. Instead of reading the syntax line-by-line, explain the data transformation:
"First, I'm going to create a CTE to filter the active orders. Next, I'll join that to the customers table to get the demographic data. Finally, in the main query, I'll group by region and use a window function to find the top performer in each."

**7. What is the typical SQL difficulty progression in interviews (phone screen vs onsite)?**
- **Phone Screen:** Usually Easy to Medium. Focuses on basic syntax, joins, aggregations, and basic window functions. Speed and accuracy are key.
- **Onsite:** Medium to Hard. Focuses on complex business logic, edge cases, multi-step data transformations (CTEs), gaps and islands, and sometimes basic query optimization concepts.

**8. How do you handle a case where you know two approaches — which do you write first?**
Always write the solution you can complete flawlessly and quickly first, even if it is brute-force or slightly less optimal. Get a working solution on the board. Then, tell the interviewer, "This works, but a more optimal approach would use X to avoid the extra scan. I can write that out if you'd like."

**9. What are the most common mistakes candidates make in SQL interviews?**
- Assuming `INNER JOIN` when `LEFT JOIN` is needed to handle missing data.
- Forgetting that `COUNT(column)` ignores NULLs, whereas `COUNT(*)` includes them.
- Grouping by a non-unique identifier (e.g., grouping by name instead of user_id).
- Filtering aggregated results in the `WHERE` clause instead of `HAVING`.
- Writing highly nested subqueries instead of readable CTEs.

**10. How do you practice SQL to actually get better (not just memorize)?**
Do not just look at solutions. If you fail a problem, read the solution to understand the pattern, then close the solution and write it yourself from scratch. Categorize problems by pattern (e.g., "This is a Top-N per group pattern") so you recognize the structure, not just the specific business context.

**11. What is the difference between SQL interviews at product companies vs data engineering roles?**
- **Product/Data Science:** Focuses heavily on product analytics scenarios—retention, funnel analysis, A/B testing metrics, user segmentations.
- **Data Engineering:** Focuses on ETL logic, handling slowly changing dimensions, recursive queries, performance optimization, and deeply understanding indexing and execution plans.

**12. How do you optimize a query on the spot without running EXPLAIN?**
Look for logical inefficiencies:
- Are you joining massive tables before filtering? (Filter first in a CTE, then join).
- Are you using `OR` or `LIKE '%pattern%'` which usually prevents index usage?
- Are you doing a full table scan using `ORDER BY` when a window function could avoid a self-join?
- Mention that adding indexes on frequently joined or filtered columns would improve physical performance.

**13. What should you do if you're stuck in a SQL interview?**
Do not stay silent. Tell the interviewer where you are stuck. "I know I need to find the previous day's row for each user, but I'm blanking on how to partition it." Often, the interviewer will give a hint (e.g., "Have you thought about using LAG?"). Use the hint and keep moving.

**14. How do you practice gap-and-island and consecutive streak problems effectively?**
These are notoriously tricky. Memorize the core mathematical trick: 
`Row_Number()` or `Date - Row_Number() as interval`. If the sequence is consecutive, the difference between the value and its row number is constant. That constant becomes your grouping key. Practice this specific pattern repeatedly until it clicks.

**15. What resources beyond LeetCode should you use for SQL practice?**
- **StrataScratch:** Excellent for data science specific SQL questions from real companies.
- **DataLemur:** Highly curated SQL interview questions.
- **PostgreSQL Documentation:** For deeply understanding window functions and date/time functions.
- Build a local database, generate dummy data, and try to write queries to answer arbitrary business questions.
