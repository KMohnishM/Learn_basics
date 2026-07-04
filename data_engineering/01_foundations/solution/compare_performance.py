"""
solution/compare_performance.py
================================
Module 1 Exercise Solution: Row-Store vs Columnar Performance Comparison

This solution demonstrates the performance difference between PostgreSQL (row-store)
and DuckDB (columnar) for analytical workloads.

Run:
    pip install duckdb pyarrow pandas psycopg2-binary
    python export_to_parquet.py   # First, export data
    python compare_performance.py  # Then compare
"""

import time
import os
import duckdb
import psycopg2
import pandas as pd
from pathlib import Path

# Database configuration
DB_CONFIG = {
    "host": "localhost", "port": 5432,
    "database": "ecommerce", "user": "deuser", "password": "depassword",
}

DATA_DIR = Path(__file__).parent / "data"
PARQUET_FILE = DATA_DIR / "fact_orders_denormalized.parquet"

# ============================================================================
# THE ANALYTICAL QUERY - run on both systems
# ============================================================================

POSTGRES_QUERY = """
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
"""

# DuckDB queries the flat denormalized Parquet file - no JOINs needed!
DUCKDB_QUERY = f"""
    SELECT 
        DATE_TRUNC('month', order_date) AS month,
        category,
        COUNT(DISTINCT order_id) AS num_orders,
        SUM(line_total) AS total_revenue
    FROM '{PARQUET_FILE}'
    WHERE status != 'cancelled'
    GROUP BY 1, 2
    ORDER BY 1 DESC, 3 DESC;
"""

NUM_RUNS = 5  # Run each query this many times for accurate timing


def time_query(run_fn, label, n_runs=NUM_RUNS):
    """
    Runs a query function n_runs times and returns timing statistics.
    
    We run multiple times because:
    - First run often includes connection/compilation overhead
    - Subsequent runs may benefit from OS disk cache (closer to real-world)
    - Multiple samples give us min/avg/max which is more informative than one number
    
    Args:
        run_fn: A callable that runs the query and returns results
        label: Human-readable name for the query
        n_runs: Number of times to run the query
        
    Returns:
        tuple: (results, min_ms, avg_ms, max_ms)
    """
    times = []
    results = None
    
    for i in range(n_runs):
        start = time.perf_counter()  # Higher resolution than time.time()
        results = run_fn()
        elapsed_ms = (time.perf_counter() - start) * 1000
        times.append(elapsed_ms)
        print(f"    Run {i+1}/{n_runs}: {elapsed_ms:.2f}ms")
    
    min_ms = min(times)
    avg_ms = sum(times) / len(times)
    max_ms = max(times)
    
    return results, min_ms, avg_ms, max_ms


def run_postgres_query():
    """Execute the analytical query on PostgreSQL and return results as DataFrame."""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        df = pd.read_sql(POSTGRES_QUERY, conn)
        return df
    finally:
        conn.close()


def run_duckdb_query():
    """Execute the analytical query on DuckDB reading from Parquet."""
    # DuckDB can be used in-process with no server needed!
    conn = duckdb.connect()  # In-memory DuckDB instance
    try:
        df = conn.execute(DUCKDB_QUERY).df()
        return df
    finally:
        conn.close()


def show_explain_plans():
    """Show the execution plans for both databases."""
    print("\n" + "="*60)
    print("EXECUTION PLANS")
    print("="*60)
    
    # PostgreSQL EXPLAIN
    print("\n--- PostgreSQL EXPLAIN (Analyze) ---")
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute("EXPLAIN (ANALYZE, FORMAT TEXT) " + POSTGRES_QUERY)
            for row in cur.fetchall():
                print("  " + row[0])
    finally:
        conn.close()
    
    # DuckDB EXPLAIN
    print("\n--- DuckDB EXPLAIN ---")
    conn = duckdb.connect()
    try:
        result = conn.execute("EXPLAIN " + DUCKDB_QUERY).fetchall()
        for row in result:
            print("  " + str(row[1]))
    finally:
        conn.close()


def verify_results_match(pg_df, duck_df):
    """
    Verify both queries return identical results.
    This is critical for correctness validation.
    """
    print("\n--- Verifying Results Match ---")
    
    # Normalize both DataFrames for comparison
    for df in [pg_df, duck_df]:
        df.columns = [c.lower() for c in df.columns]
        df['month'] = pd.to_datetime(df['month']).dt.to_period('M')
        df['total_revenue'] = df['total_revenue'].astype(float).round(2)
        df['num_orders'] = df['num_orders'].astype(int)
    
    # Sort both by the same columns for comparison
    pg_sorted = pg_df.sort_values(['month', 'category']).reset_index(drop=True)
    duck_sorted = duck_df.sort_values(['month', 'category']).reset_index(drop=True)
    
    # Check if they match
    if pg_sorted.shape == duck_sorted.shape:
        revenue_match = (abs(pg_sorted['total_revenue'] - duck_sorted['total_revenue']) < 0.01).all()
        orders_match = (pg_sorted['num_orders'] == duck_sorted['num_orders']).all()
        
        if revenue_match and orders_match:
            print("  [PASS] Results are IDENTICAL between PostgreSQL and DuckDB!")
        else:
            print("  [FAIL] Results differ!")
            # Find differences
            mismatches = pg_sorted[~(
                (abs(pg_sorted['total_revenue'] - duck_sorted['total_revenue']) < 0.01) &
                (pg_sorted['num_orders'] == duck_sorted['num_orders'])
            )]
            print(f"  Mismatching rows: {len(mismatches)}")
    else:
        print(f"  [FAIL] Row count differs: PG={pg_sorted.shape[0]}, Duck={duck_sorted.shape[0]}")
    
    return pg_sorted


def get_file_size_mb(path):
    """Return file size in MB."""
    return os.path.getsize(path) / (1024 * 1024)


def main():
    print("="*60)
    print("Module 1: Row-Store vs Columnar Performance Comparison")
    print("="*60)
    
    if not PARQUET_FILE.exists():
        print(f"\n[ERROR] Parquet file not found: {PARQUET_FILE}")
        print("Run export_to_parquet.py first!")
        return
    
    # Show file size info
    parquet_size = get_file_size_mb(PARQUET_FILE)
    print(f"\nParquet file size: {parquet_size:.2f} MB")
    
    # -------------------------------------------------------------------------
    # Run DuckDB query with EXPLAIN first (doesn't affect timing)
    # -------------------------------------------------------------------------
    show_explain_plans()
    
    # -------------------------------------------------------------------------
    # Time PostgreSQL
    # -------------------------------------------------------------------------
    print("\n" + "="*60)
    print("TIMING: PostgreSQL (Row-Store)")
    print("="*60)
    pg_results, pg_min, pg_avg, pg_max = time_query(run_postgres_query, "PostgreSQL")
    
    # -------------------------------------------------------------------------
    # Time DuckDB
    # -------------------------------------------------------------------------
    print("\n" + "="*60)
    print("TIMING: DuckDB (Columnar, reading Parquet)")
    print("="*60)
    duck_results, duck_min, duck_avg, duck_max = time_query(run_duckdb_query, "DuckDB")
    
    # -------------------------------------------------------------------------
    # Verify correctness
    # -------------------------------------------------------------------------
    final_results = verify_results_match(pg_results, duck_results)
    
    # -------------------------------------------------------------------------
    # Performance Summary
    # -------------------------------------------------------------------------
    print("\n" + "="*60)
    print("PERFORMANCE SUMMARY")
    print("="*60)
    print(f"\n{'Database':<20} {'Min (ms)':>10} {'Avg (ms)':>10} {'Max (ms)':>10}")
    print("-"*52)
    print(f"{'PostgreSQL':<20} {pg_min:>10.2f} {pg_avg:>10.2f} {pg_max:>10.2f}")
    print(f"{'DuckDB (Parquet)':<20} {duck_min:>10.2f} {duck_avg:>10.2f} {duck_max:>10.2f}")
    
    speedup = pg_avg / duck_avg if duck_avg > 0 else 0
    print(f"\n  DuckDB is {speedup:.1f}x faster than PostgreSQL (avg time)")
    
    # Show sample results
    print("\n  Sample results (first 5 rows):")
    print(f"  {final_results.head().to_string(index=False)}")
    
    # -------------------------------------------------------------------------
    # Write results.md
    # -------------------------------------------------------------------------
    results_path = Path(__file__).parent / "results.md"
    with open(results_path, 'w') as f:
        f.write(f"""# Performance Comparison Results

## Query
Aggregation: total revenue per category per month, excluding cancelled orders.
This requires GROUP BY, COUNT(DISTINCT), SUM, and date truncation.

## Results

| Database         | Min (ms) | Avg (ms) | Max (ms) |
|-----------------|----------|----------|----------|
| PostgreSQL      | {pg_min:.2f}    | {pg_avg:.2f}    | {pg_max:.2f}    |
| DuckDB (Parquet)| {duck_min:.2f}    | {duck_avg:.2f}    | {duck_max:.2f}    |

**DuckDB is {speedup:.1f}x faster than PostgreSQL**

## File Sizes

| Format  | Size     |
|---------|----------|
| Parquet | {parquet_size:.2f} MB |

## Analysis: WHY is DuckDB Faster?

### 1. Columnar Storage
PostgreSQL stores rows on disk: [order_id][user_id][status][order_date][total_amount]...
To read `total_amount` and `order_date`, it reads ALL columns of every row.

DuckDB + Parquet stores columns on disk: all order_dates together, all amounts together.
It reads ONLY the columns needed by the query: status, order_date, category, line_total.

For a query touching 4 of 10 columns, this reduces I/O by 60%.

### 2. Vectorized Execution
DuckDB processes data in "vectors" (batches of 1024 values using SIMD CPU instructions).
PostgreSQL processes one row at a time (the Volcano/Iterator model).

SIMD (Single Instruction Multiple Data) can compute SUM of 8 float64 values in one
CPU instruction instead of 8 separate instructions. That's 8x throughput for aggregations.

### 3. No JOIN Overhead
The denormalized Parquet file has all data in one file.
PostgreSQL must JOIN 3 tables, which requires hash join or nested loop operations
with intermediate result sets stored in memory/disk.

### 4. Statistics-Based Pruning
Parquet files store min/max statistics per column chunk.
DuckDB can skip entire file chunks where `status = 'cancelled'` if
the statistics show all values in that chunk are 'cancelled'.

### 5. Better Compression = Less I/O
Parquet with Snappy compression: categorical columns (status, category) compress
at 5-10x because the same string appears repeatedly.
PostgreSQL's row-oriented storage compresses poorly across mixed-type rows.

## Conclusion
For OLTP workloads (find one order, insert a new user, update stock), PostgreSQL wins.
For OLAP workloads (aggregate millions of rows, complex GROUP BY), columnar stores win.
This is why the modern data stack separates concerns: PostgreSQL for the application,
Snowflake/BigQuery/DuckDB for analytics.
""")
    
    print(f"\n  Results written to: {results_path}")


if __name__ == "__main__":
    main()
