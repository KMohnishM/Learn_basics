# SQL Mastery Curriculum

Welcome to the complete, production-quality SQL curriculum. This curriculum is designed to take you from foundational concepts to advanced, interview-ready SQL mastery. It is built primarily around **PostgreSQL**, focusing on real-world patterns, deep technical understanding, and query optimization. 

## Who is this for?
This curriculum is designed for software engineers, data analysts, data engineers, and anyone preparing for rigorous technical interviews. It assumes basic programming knowledge but starts SQL from the ground up, rapidly accelerating into complex, high-performance query design.

## Module Map

| Module | Topics | Difficulty |
|---|---|---|
| [01. Fundamentals](./01_fundamentals/) | SELECT anatomy, filtering, types, NULL logic, string/date functions | Beginner |
| [02. Joins](./02_joins/) | INNER, LEFT, RIGHT, FULL, CROSS, SELF joins, N+1 problem, duplicates | Intermediate |
| [03. Aggregations](./03_aggregations/) | GROUP BY, HAVING, FILTER, ROLLUP, CUBE, conditional aggregations | Intermediate |
| [04. Window Functions](./04_window_functions/) | OVER, PARTITION, ranking, offsets, running totals, frames | Advanced |
| [05. Subqueries & CTEs](./05_subqueries_ctes/) | Scalar/row/table subqueries, EXISTS, Correlated, Recursive CTEs | Advanced |
| [06. Indexes & Optimization](./06_indexes_optimization/) | B-Tree, partial/covering indexes, EXPLAIN, bloat, query planning | Expert |
| [07. Transactions & Isolation](./07_transactions_isolation/) | ACID, isolation levels, MVCC, locking, deadlocks | Expert |
| [08. Interview 50](./08_interview_50/) | 50 fully solved interview questions spanning all difficulty levels | Mixed |

## Suggested Study Order & Time Estimates
1. **Core Querying** (Modules 1-3): ~8 hours. Focus heavily on mastering `GROUP BY` and understanding how `LEFT JOIN` works with NULLs.
2. **Advanced Patterns** (Modules 4-5): ~10 hours. Window functions and CTEs are the bread and butter of modern data engineering.
3. **Database Internals** (Modules 6-7): ~12 hours. Essential for backend engineering and system design interviews.
4. **Practice** (Module 8): ~15 hours. Work through the 50 questions without looking at the solutions first.

## How to Practice

To get the most out of this curriculum, you must write and execute queries. Reading is not enough.

1. **Local PostgreSQL (Recommended)**: 
   Install PostgreSQL locally (via Docker or native installer). Create a database, define the schema provided in Module 1, and insert sample data. This allows you to practice `EXPLAIN` and transaction isolation.
2. **Online Sandboxes**:
   Use tools like [sqliteonline.com](https://sqliteonline.com/) or [db-fiddle.com](https://www.db-fiddle.com/) for quick query testing without local setup. Ensure you select PostgreSQL as the dialect.
3. **LeetCode / HackerRank**:
   Supplement Module 8 with live problems on LeetCode (Database section) or StrataScratch to practice against hidden test cases.

## SQL Dialect Notes

- **Primary Dialect**: This curriculum uses **PostgreSQL** as the standard dialect due to its robust feature set, strict adherence to SQL standards, and massive industry adoption.
- **MySQL Differences**: Where relevant, major differences in MySQL (e.g., lack of `FULL OUTER JOIN`, differences in window function support in older versions, transaction isolation defaults) are explicitly noted.

## Core Schema
All examples and interview questions across the modules use the following consistent schema:

```sql
employees(emp_id, name, dept_id, salary, manager_id, hire_date, is_active)
departments(dept_id, dept_name, location)
orders(order_id, customer_id, product_id, quantity, amount, order_date, status)
customers(customer_id, name, email, country, created_at)
products(product_id, name, category, price)
```
