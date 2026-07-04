# Module 1 Exercise: Row-Store vs Column-Store Performance Comparison

## Objective

Compare the query performance between a **row-store** (PostgreSQL) and a **column-store** approach using **DuckDB** (an embedded columnar analytical database). Understand WHY column stores are dramatically faster for analytical workloads.

## Background

You have already loaded 1000 rows into PostgreSQL using `setup_postgres.py`. Now you will:
1. Export the data from PostgreSQL to Parquet format (columnar)
2. Query the same data using DuckDB (columnar engine)
3. Compare execution times and query plans
4. Understand the architectural reasons for the difference

## Requirements

### Part 1: Export PostgreSQL Data to Parquet

Write a script `export_to_parquet.py` that:

1. Connects to PostgreSQL and exports the following tables to Parquet files:
   - `orders` → `data/orders.parquet`
   - `order_items` → `data/order_items.parquet`
   - `products` → `data/products.parquet`
   - `users` → `data/users.parquet`

2. When exporting, create a **denormalized** "fact table" Parquet file by joining all 4 tables into one flat file: `data/fact_orders_denormalized.parquet`

   The fact table should contain these columns:
   - `order_id`, `order_date`, `status`
   - `user_id`, `country_code`, `country_name`
   - `product_id`, `category`, `quantity`, `line_total`

3. Print the file sizes of each Parquet file vs the equivalent CSV export

### Part 2: Run Identical Queries on Both Systems

Write a script `compare_performance.py` that:

1. Runs this analytical query on **PostgreSQL** (via psycopg2):
   ```sql
   SELECT 
       DATE_TRUNC('month', o.order_date) AS month,
       p.category,
       COUNT(DISTINCT o.order_id) AS num_orders,
       SUM(oi.line_total) AS total_revenue
   FROM orders o
   JOIN order_items oi ON o.order_id = oi.order_id
   JOIN products p ON oi.product_id = p.product_id
   WHERE o.status != 'cancelled'
   GROUP BY 1, 2
   ORDER BY 1 DESC, 3 DESC;
   ```

2. Runs the **same query** on **DuckDB** reading from `fact_orders_denormalized.parquet`:
   ```sql
   SELECT 
       DATE_TRUNC('month', order_date) AS month,
       category,
       COUNT(DISTINCT order_id) AS num_orders,
       SUM(line_total) AS total_revenue
   FROM 'data/fact_orders_denormalized.parquet'
   WHERE status != 'cancelled'
   GROUP BY 1, 2
   ORDER BY 1 DESC, 3 DESC;
   ```

3. Measures execution time for both (run each query **5 times** and report min/avg/max)

4. Shows the `EXPLAIN` plan for the DuckDB query

5. Verifies that both queries return **identical results**

### Part 3: Scale Test

1. Generate a **larger dataset** - extend `setup_postgres.py` to insert **100,000 orders** (adjust the number at the top of the file)

2. Re-export to Parquet

3. Re-run the performance comparison

4. Document the difference in a `results.md` file with:
   - Execution times for both systems at 1,000 and 100,000 rows
   - File sizes (CSV vs Parquet)
   - Your analysis of WHY DuckDB is faster

## Expected Results

At 100,000 rows, you should see DuckDB is approximately **5x-20x faster** than PostgreSQL for this aggregation query, despite PostgreSQL being a well-tuned OLTP database.

## Deliverables

```
exercise/
├── export_to_parquet.py    # Part 1: Export script
├── compare_performance.py  # Part 2: Comparison script
├── data/                   # Generated Parquet files (create this dir)
└── results.md              # Part 3: Your analysis
```

## Setup

Install additional dependencies:
```bash
pip install duckdb pyarrow pandas psycopg2-binary
```

Make sure PostgreSQL is running:
```bash
# From the labs/ directory
docker-compose up -d

# Then populate the database
python setup_postgres.py
```

## Hints

- Use `pandas.read_sql()` to read from PostgreSQL into a DataFrame
- Use `df.to_parquet()` to write Parquet files (requires `pyarrow`)
- Use `duckdb.connect()` and `.execute()` to query DuckDB
- DuckDB can directly query Parquet files: `SELECT * FROM 'file.parquet'`
- Use `time.perf_counter()` for high-resolution timing
- The `EXPLAIN` in DuckDB uses: `EXPLAIN SELECT ...`

## Grading Criteria

- [ ] Parquet export works and files are created correctly
- [ ] Both queries return identical results (verified programmatically)
- [ ] Timing is measured correctly (5 runs, min/avg/max reported)
- [ ] DuckDB shows better performance for the aggregation query
- [ ] `results.md` explains the architectural reasons for the difference
- [ ] Code has clear comments explaining each step
