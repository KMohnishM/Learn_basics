# Module 8: The SQL Interview 50

## Introduction and Practice Setup
Welcome to Module 8. This module is designed to simulate a high-pressure SQL interview environment. 

### Practice Setup
Use the following schema for all exercises. We recommend setting up a local PostgreSQL instance or using an online SQL fiddle.

```sql
CREATE TABLE departments (
    dept_id INT PRIMARY KEY,
    dept_name VARCHAR(100),
    location VARCHAR(100)
);

CREATE TABLE employees (
    emp_id INT PRIMARY KEY,
    name VARCHAR(100),
    dept_id INT,
    salary DECIMAL(10, 2),
    manager_id INT,
    hire_date DATE,
    is_active BOOLEAN
);

CREATE TABLE products (
    product_id INT PRIMARY KEY,
    name VARCHAR(100),
    category VARCHAR(50),
    price DECIMAL(10, 2)
);

CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    country VARCHAR(50),
    created_at TIMESTAMP
);

CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer_id INT,
    product_id INT,
    quantity INT,
    amount DECIMAL(10, 2),
    order_date DATE,
    status VARCHAR(20)
);
```

### Recommended Practice Method
1. Read the problem.
2. Set a timer (3 mins for Easy, 10 mins for Medium, 20 mins for Hard).
3. Write the query.
4. Compare your solution to the one provided.

---

## Easy (Q1 - Q20)

**Q1: Find all active employees with a salary greater than 70,000.**
```sql
SELECT emp_id, name, salary
FROM employees
WHERE salary > 70000 AND is_active = TRUE;
```
*Explanation:* Basic filtering using the WHERE clause.

**Q2: Find the total number of employees in each department.**
```sql
SELECT dept_id, COUNT(emp_id) AS employee_count
FROM employees
GROUP BY dept_id;
```
*Explanation:* Simple aggregation using GROUP BY.

**Q3: List all departments and their employees, including departments with no employees.**
```sql
SELECT d.dept_name, e.name
FROM departments d
LEFT JOIN employees e ON d.dept_id = e.dept_id;
```
*Explanation:* A LEFT JOIN ensures all records from the left table (departments) are included.

**Q4: Find the average salary of active employees.**
```sql
SELECT AVG(salary) AS avg_salary
FROM employees
WHERE is_active = TRUE;
```
*Explanation:* Combining an aggregate function (AVG) with a WHERE clause filter.

**Q5: Find all products in the 'Electronics' category priced under $500.**
```sql
SELECT product_id, name, price
FROM products
WHERE category = 'Electronics' AND price < 500;
```
*Explanation:* Multi-condition filtering.

**Q6: Retrieve the names of customers who created their account in 2023.**
```sql
SELECT name
FROM customers
WHERE EXTRACT(YEAR FROM created_at) = 2023;
```
*Explanation:* Using EXTRACT to filter by year. In MySQL, `YEAR(created_at) = 2023` is also valid.

**Q7: Find the highest salary in the company.**
```sql
SELECT MAX(salary) AS highest_salary
FROM employees;
```
*Explanation:* Basic MAX aggregation.

**Q8: List the top 5 most expensive products.**
```sql
SELECT name, price
FROM products
ORDER BY price DESC
LIMIT 5;
```
*Explanation:* Sorting with ORDER BY DESC and restricting output with LIMIT.

**Q9: Find the total revenue generated from all 'Completed' orders.**
```sql
SELECT SUM(amount) AS total_revenue
FROM orders
WHERE status = 'Completed';
```
*Explanation:* SUM aggregation with a filter.

**Q10: Find employees hired in the last 30 days (assuming today is CURRENT_DATE).**
```sql
SELECT name, hire_date
FROM employees
WHERE hire_date >= CURRENT_DATE - INTERVAL '30 days';
```
*Explanation:* Date arithmetic. MySQL syntax: `DATE_SUB(CURDATE(), INTERVAL 30 DAY)`.

**Q11: Find the number of distinct countries our customers are from.**
```sql
SELECT COUNT(DISTINCT country) AS distinct_countries
FROM customers;
```
*Explanation:* COUNT DISTINCT removes duplicates before counting.

**Q12: List all employees whose names start with 'A'.**
```sql
SELECT name
FROM employees
WHERE name LIKE 'A%';
```
*Explanation:* Pattern matching using LIKE.

**Q13: Find the lowest and highest price of products in each category.**
```sql
SELECT category, MIN(price) AS lowest_price, MAX(price) AS highest_price
FROM products
GROUP BY category;
```
*Explanation:* Multiple aggregations per group.

**Q14: Find all orders where the quantity is exactly 10.**
```sql
SELECT order_id, customer_id, order_date
FROM orders
WHERE quantity = 10;
```
*Explanation:* Simple equality filter.

**Q15: Find the employee with the earliest hire date.**
```sql
SELECT name, hire_date
FROM employees
ORDER BY hire_date ASC
LIMIT 1;
```
*Explanation:* Sorting by date to find the earliest.

**Q16: Calculate the total quantity of products ordered by customer_id 101.**
```sql
SELECT SUM(quantity) AS total_quantity
FROM orders
WHERE customer_id = 101;
```
*Explanation:* Filter and sum.

**Q17: Find all customers who have not provided an email address (email is null).**
```sql
SELECT customer_id, name
FROM customers
WHERE email IS NULL;
```
*Explanation:* IS NULL check.

**Q18: Retrieve a unique list of all order statuses.**
```sql
SELECT DISTINCT status
FROM orders;
```
*Explanation:* Removing duplicates from a result set using DISTINCT.

**Q19: Find employees who do not belong to department 5.**
```sql
SELECT name, dept_id
FROM employees
WHERE dept_id != 5 OR dept_id IS NULL;
```
*Explanation:* Handling inequality and NULLs.

**Q20: Find the total number of orders placed on '2023-10-01'.**
```sql
SELECT COUNT(order_id) AS orders_count
FROM orders
WHERE order_date = '2023-10-01';
```
*Explanation:* Exact date filtering.

---

## Medium (Q21 - Q40)

**Q21: Rank employees by salary within their respective departments.**
```sql
SELECT 
    emp_id, 
    dept_id, 
    salary,
    RANK() OVER (PARTITION BY dept_id ORDER BY salary DESC) as salary_rank
FROM employees;
```
*Explanation:* Uses window function RANK() partitioned by department.

**Q22: Find the top 3 highest paid employees in each department.**
```sql
WITH RankedSalaries AS (
    SELECT 
        emp_id, 
        name, 
        dept_id, 
        salary,
        DENSE_RANK() OVER (PARTITION BY dept_id ORDER BY salary DESC) as rnk
    FROM employees
)
SELECT name, dept_id, salary
FROM RankedSalaries
WHERE rnk <= 3;
```
*Explanation:* Uses a CTE and DENSE_RANK() to find top N per group.

**Q23: Calculate the running total of revenue by order date.**
```sql
SELECT 
    order_date,
    SUM(amount) as daily_revenue,
    SUM(SUM(amount)) OVER (ORDER BY order_date) as running_total
FROM orders
WHERE status = 'Completed'
GROUP BY order_date;
```
*Explanation:* Window function SUM() OVER() with ORDER BY creates a cumulative sum.

**Q24: Find employees whose salary is higher than their manager's salary.**
```sql
SELECT e.name AS employee_name, e.salary AS employee_salary, m.salary AS manager_salary
FROM employees e
JOIN employees m ON e.manager_id = m.emp_id
WHERE e.salary > m.salary;
```
*Explanation:* Self-join on the employees table.

**Q25: Find departments that have less than 3 active employees.**
```sql
SELECT d.dept_name, COUNT(e.emp_id) as active_count
FROM departments d
LEFT JOIN employees e ON d.dept_id = e.dept_id AND e.is_active = TRUE
GROUP BY d.dept_id, d.dept_name
HAVING COUNT(e.emp_id) < 3;
```
*Explanation:* Aggregate filtering using HAVING.

**Q26: Calculate the month-over-month growth rate of completed order revenue.**
```sql
WITH MonthlyRevenue AS (
    SELECT 
        DATE_TRUNC('month', order_date) AS month,
        SUM(amount) AS revenue
    FROM orders
    WHERE status = 'Completed'
    GROUP BY 1
)
SELECT 
    month,
    revenue,
    LAG(revenue) OVER (ORDER BY month) AS prev_month_rev,
    (revenue - LAG(revenue) OVER (ORDER BY month)) / LAG(revenue) OVER (ORDER BY month)::numeric AS growth_rate
FROM MonthlyRevenue;
```
*Explanation:* Uses LAG() window function to access the previous row's value.

**Q27: Find the first order placed by each customer.**
```sql
WITH RankedOrders AS (
    SELECT 
        order_id, 
        customer_id, 
        order_date,
        ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date ASC) as rn
    FROM orders
)
SELECT order_id, customer_id, order_date
FROM RankedOrders
WHERE rn = 1;
```
*Explanation:* ROW_NUMBER() is perfect for finding the "first" or "last" record per group.

**Q28: Find customers who have placed orders for products in all categories.**
```sql
SELECT o.customer_id
FROM orders o
JOIN products p ON o.product_id = p.product_id
GROUP BY o.customer_id
HAVING COUNT(DISTINCT p.category) = (SELECT COUNT(DISTINCT category) FROM products);
```
*Explanation:* Relational division problem. Compares distinct count per customer to total distinct count.

**Q29: Calculate the 7-day rolling average of daily revenue.**
```sql
WITH DailyRev AS (
    SELECT order_date, SUM(amount) AS rev
    FROM orders
    WHERE status = 'Completed'
    GROUP BY order_date
)
SELECT 
    order_date,
    rev,
    AVG(rev) OVER (
        ORDER BY order_date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS rolling_avg_7d
FROM DailyRev;
```
*Explanation:* Uses window framing (ROWS BETWEEN) for moving averages.

**Q30: Find products that have never been ordered.**
```sql
SELECT p.product_id, p.name
FROM products p
LEFT JOIN orders o ON p.product_id = o.product_id
WHERE o.order_id IS NULL;
```
*Explanation:* Anti-join pattern using LEFT JOIN and IS NULL. NOT EXISTS is a good alternative.

**Q31: List the second highest salary in the company.**
```sql
SELECT MAX(salary) AS second_highest
FROM employees
WHERE salary < (SELECT MAX(salary) FROM employees);
```
*Explanation:* Subquery approach. Can also be done using DENSE_RANK() in a CTE.

**Q32: Find the average time between consecutive orders for each customer.**
```sql
WITH OrderDates AS (
    SELECT 
        customer_id, 
        order_date,
        LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) as prev_order_date
    FROM orders
)
SELECT 
    customer_id,
    AVG(order_date - prev_order_date) AS avg_days_between_orders
FROM OrderDates
WHERE prev_order_date IS NOT NULL
GROUP BY customer_id;
```
*Explanation:* LAG() to get previous order date, then average the difference.

**Q33: Find the percentage of total company revenue contributed by each department.**
```sql
WITH DeptRev AS (
    SELECT e.dept_id, SUM(o.amount) as dept_amount
    FROM employees e
    JOIN orders o ON e.emp_id = o.customer_id -- assuming employee bought it, or change relation
    GROUP BY e.dept_id
), TotalRev AS (
    SELECT SUM(amount) as total FROM orders
)
SELECT 
    dr.dept_id, 
    dr.dept_amount,
    (dr.dept_amount / tr.total) * 100 AS percent_contribution
FROM DeptRev dr CROSS JOIN TotalRev tr;
```
*Explanation:* Calculates part-to-whole ratio using CTEs and CROSS JOIN.

**Q34: Identify customers who have placed at least 3 orders, totaling over $1000.**
```sql
SELECT customer_id, COUNT(order_id) as total_orders, SUM(amount) as total_spent
FROM orders
GROUP BY customer_id
HAVING COUNT(order_id) >= 3 AND SUM(amount) > 1000;
```
*Explanation:* Multiple conditions in the HAVING clause.

**Q35: Find the median salary of employees.**
```sql
WITH OrderedSalaries AS (
    SELECT salary, 
           ROW_NUMBER() OVER (ORDER BY salary) as rn,
           COUNT(*) OVER () as total_count
    FROM employees
)
SELECT AVG(salary) AS median_salary
FROM OrderedSalaries
WHERE rn IN ((total_count + 1) / 2, (total_count + 2) / 2);
```
*Explanation:* Standard SQL median calculation using window functions.

**Q36: Find pairs of employees who have the same manager.**
```sql
SELECT e1.emp_id AS emp1, e2.emp_id AS emp2, e1.manager_id
FROM employees e1
JOIN employees e2 ON e1.manager_id = e2.manager_id AND e1.emp_id < e2.emp_id;
```
*Explanation:* Self-join to find pairs, using `<` to prevent duplicate pairs (A-B and B-A).

**Q37: Update salaries by +10% for the 'Engineering' department.**
```sql
UPDATE employees
SET salary = salary * 1.10
WHERE dept_id = (SELECT dept_id FROM departments WHERE dept_name = 'Engineering');
```
*Explanation:* UPDATE statement using a subquery.

**Q38: Delete orders that were canceled more than 1 year ago.**
```sql
DELETE FROM orders
WHERE status = 'Canceled' AND order_date < CURRENT_DATE - INTERVAL '1 year';
```
*Explanation:* DELETE statement with date filtering.

**Q39: Find the highest earning employee in each department without using Window Functions.**
```sql
SELECT e.dept_id, e.name, e.salary
FROM employees e
JOIN (
    SELECT dept_id, MAX(salary) as max_sal
    FROM employees
    GROUP BY dept_id
) max_sals ON e.dept_id = max_sals.dept_id AND e.salary = max_sals.max_sal;
```
*Explanation:* Group by and Join approach to find top N per group.

**Q40: Pivot the order counts by status.**
```sql
SELECT 
    SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) AS completed_count,
    SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) AS pending_count,
    SUM(CASE WHEN status = 'Canceled' THEN 1 ELSE 0 END) AS canceled_count
FROM orders;
```
*Explanation:* Conditional aggregation using CASE statements inside SUM.

---

## Hard (Q41 - Q50)

**Q41: Find the employee hierarchy (Manager to Subordinate paths).**
```sql
WITH RECURSIVE EmployeeHierarchy AS (
    -- Base case: Top level managers (no manager)
    SELECT emp_id, name, manager_id, 1 AS level, CAST(name AS VARCHAR) AS path
    FROM employees
    WHERE manager_id IS NULL
    
    UNION ALL
    
    -- Recursive step
    SELECT e.emp_id, e.name, e.manager_id, eh.level + 1, CAST(eh.path || ' -> ' || e.name AS VARCHAR)
    FROM employees e
    JOIN EmployeeHierarchy eh ON e.manager_id = eh.emp_id
)
SELECT * FROM EmployeeHierarchy ORDER BY path;
```
*Explanation:* Uses a Recursive CTE to traverse hierarchical data. Essential for org charts or BOMs.

**Q42: Gaps and Islands: Find periods of consecutive active order days.**
```sql
WITH GroupedDays AS (
    SELECT DISTINCT order_date,
           order_date - INTERVAL '1 day' * DENSE_RANK() OVER (ORDER BY order_date) AS grp
    FROM orders
)
SELECT MIN(order_date) AS start_date, 
       MAX(order_date) AS end_date, 
       COUNT(order_date) AS streak_length
FROM GroupedDays
GROUP BY grp
ORDER BY start_date;
```
*Explanation:* Standard gaps-and-islands solution. Subtracting the row number (as interval) from the date groups consecutive dates into the same partition.

**Q43: FIFO Inventory depletion.**
*Note: Assume a table `inventory(id, received_date, qty)` and we need to sell 15 units.*
```sql
WITH RunningTotals AS (
    SELECT id, received_date, qty,
           SUM(qty) OVER (ORDER BY received_date) - qty AS prev_total,
           SUM(qty) OVER (ORDER BY received_date) AS running_total
    FROM inventory
)
SELECT id, received_date,
       CASE 
           WHEN prev_total >= 15 THEN 0
           WHEN running_total <= 15 THEN qty
           ELSE 15 - prev_total
       END AS qty_taken
FROM RunningTotals
WHERE prev_total < 15;
```
*Explanation:* Uses running totals to calculate how much of each inventory batch is consumed for a FIFO queue.

**Q44: Find the top 2 products by revenue in each category.**
```sql
WITH RankedProducts AS (
    SELECT 
        p.category, 
        p.name, 
        SUM(o.amount) as total_rev,
        DENSE_RANK() OVER (PARTITION BY p.category ORDER BY SUM(o.amount) DESC) as rnk
    FROM products p
    JOIN orders o ON p.product_id = o.product_id
    GROUP BY p.category, p.name
)
SELECT category, name, total_rev
FROM RankedProducts
WHERE rnk <= 2;
```
*Explanation:* Combines aggregation with window functions in a CTE.

**Q45: Identify the churned customers (no orders in the last 6 months, but ordered before).**
```sql
SELECT customer_id
FROM orders
GROUP BY customer_id
HAVING MAX(order_date) < CURRENT_DATE - INTERVAL '6 months';
```
*Explanation:* Grouping by customer and filtering on their most recent order date using MAX().

**Q46: Calculate the retention rate (percentage of users who returned next month).**
```sql
WITH MonthlyActiveUsers AS (
    SELECT DISTINCT customer_id, DATE_TRUNC('month', order_date) as month
    FROM orders
),
RetainedUsers AS (
    SELECT m1.month, COUNT(DISTINCT m1.customer_id) as retained_count
    FROM MonthlyActiveUsers m1
    JOIN MonthlyActiveUsers m2 
      ON m1.customer_id = m2.customer_id 
     AND m2.month = m1.month + INTERVAL '1 month'
    GROUP BY m1.month
),
TotalUsers AS (
    SELECT month, COUNT(DISTINCT customer_id) as total_count
    FROM MonthlyActiveUsers
    GROUP BY month
)
SELECT t.month, 
       COALESCE(r.retained_count, 0) * 100.0 / t.total_count AS retention_rate
FROM TotalUsers t
LEFT JOIN RetainedUsers r ON t.month = r.month;
```
*Explanation:* Self-joins on time intervals to determine cohort retention.

**Q47: Identify overlapping date ranges for employee assignments.**
*Assuming an `assignments(emp_id, start_date, end_date)` table.*
```sql
SELECT a1.emp_id, a1.start_date, a1.end_date, a2.start_date, a2.end_date
FROM assignments a1
JOIN assignments a2 
  ON a1.emp_id = a2.emp_id 
 AND a1.start_date < a2.end_date 
 AND a1.end_date > a2.start_date
 AND a1.start_date != a2.start_date;
```
*Explanation:* The standard overlap condition is `Start A < End B AND End A > Start B`.

**Q48: Find the mode (most frequent value) of product quantities ordered.**
```sql
WITH Frequencies AS (
    SELECT quantity, COUNT(*) as freq,
           RANK() OVER (ORDER BY COUNT(*) DESC) as rnk
    FROM orders
    GROUP BY quantity
)
SELECT quantity, freq
FROM Frequencies
WHERE rnk = 1;
```
*Explanation:* Group by to find frequency, rank descending to find the top one(s).

**Q49: Unpivot a table using CROSS JOIN and CASE (or unnest).**
*Given a table `monthly_sales(id, jan_sales, feb_sales, mar_sales)`*
```sql
SELECT id,
       month,
       CASE month 
           WHEN 'jan' THEN jan_sales
           WHEN 'feb' THEN feb_sales
           WHEN 'mar' THEN mar_sales
       END as sales
FROM monthly_sales
CROSS JOIN (VALUES ('jan'), ('feb'), ('mar')) AS t(month);
```
*Explanation:* Emulates the UNPIVOT operator using standard SQL CROSS JOIN.

**Q50: Find the maximum number of concurrent active sessions.**
*Assuming `sessions(session_id, start_time, end_time)`*
```sql
WITH Events AS (
    SELECT start_time AS event_time, 1 AS type FROM sessions
    UNION ALL
    SELECT end_time AS event_time, -1 AS type FROM sessions
),
Concurrent AS (
    SELECT event_time, 
           SUM(type) OVER (ORDER BY event_time ROWS UNBOUNDED PRECEDING) AS active_sessions
    FROM Events
)
SELECT MAX(active_sessions) AS max_concurrent
FROM Concurrent;
```
*Explanation:* Unpivots start/end times into events (+1 for start, -1 for end), then calculates a running sum over time to track concurrency.
