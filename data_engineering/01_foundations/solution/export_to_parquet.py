"""
solution/export_to_parquet.py
==============================
Module 1 Exercise Solution: Export PostgreSQL Data to Parquet

This script exports OLTP data from PostgreSQL to columnar Parquet format,
including creating a denormalized fact table for analytical queries.
"""

import os
import psycopg2
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path

DB_CONFIG = {
    "host": "localhost", "port": 5432,
    "database": "ecommerce", "user": "deuser", "password": "depassword",
}

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def export_table(conn, table_name, output_path):
    """Export a single table from PostgreSQL to Parquet format."""
    print(f"  Exporting {table_name}...", end="")
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    df.to_parquet(output_path, index=False, compression='snappy')
    
    # Also export as CSV for size comparison
    csv_path = output_path.with_suffix('.csv')
    df.to_csv(csv_path, index=False)
    
    parquet_size = os.path.getsize(output_path) / 1024
    csv_size = os.path.getsize(csv_path) / 1024
    compression_ratio = csv_size / parquet_size if parquet_size > 0 else 0
    
    print(f" {len(df)} rows | Parquet: {parquet_size:.1f}KB | CSV: {csv_size:.1f}KB | Ratio: {compression_ratio:.1f}x")
    return df


def create_denormalized_fact_table(conn, output_path):
    """
    Create a single flat denormalized fact table by joining all 4 tables.
    
    This is the key transformation for analytical workloads:
    - OLTP: normalized tables requiring JOINs at query time
    - OLAP: denormalized single table, fast aggregations without JOINs
    
    The cost is paid once during ETL, not at every query.
    """
    print("\n  Creating denormalized fact table...")
    
    query = """
        SELECT 
            o.order_id,
            o.order_date,
            o.status,
            u.user_id,
            u.first_name || ' ' || u.last_name AS customer_name,
            u.country_code,
            u.country_name,
            oi.product_id,
            p.name AS product_name,
            p.category,
            oi.quantity,
            oi.unit_price,
            oi.line_total
        FROM orders o
        JOIN users u ON o.user_id = u.user_id
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        ORDER BY o.order_date DESC;
    """
    
    df = pd.read_sql(query, conn)
    df.to_parquet(output_path, index=False, compression='snappy')
    
    # CSV version for comparison
    csv_path = output_path.with_suffix('.csv')
    df.to_csv(csv_path, index=False)
    
    parquet_size = os.path.getsize(output_path) / 1024
    csv_size = os.path.getsize(csv_path) / 1024
    
    print(f"  Fact table: {len(df)} rows | Parquet: {parquet_size:.1f}KB | CSV: {csv_size:.1f}KB")
    print(f"  Columns: {list(df.columns)}")
    return df


def main():
    print("="*60)
    print("Exporting PostgreSQL Data to Parquet")
    print("="*60)
    
    conn = psycopg2.connect(**DB_CONFIG)
    
    try:
        print("\nIndividual Tables:")
        export_table(conn, "users",       DATA_DIR / "users.parquet")
        export_table(conn, "products",    DATA_DIR / "products.parquet")
        export_table(conn, "orders",      DATA_DIR / "orders.parquet")
        export_table(conn, "order_items", DATA_DIR / "order_items.parquet")
        
        create_denormalized_fact_table(conn, DATA_DIR / "fact_orders_denormalized.parquet")
        
        print("\nExport complete! Files saved to:", DATA_DIR)
        print("\nRun compare_performance.py to see the performance difference.")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()
