"""
setup_postgres.py
=================
Module 1 Lab: OLTP Schema Setup and Performance Analysis

PURPOSE:
    This script demonstrates the foundational concept of OLTP databases
    and why they are POOR choices for analytical workloads. We will:
    
    1. Create a normalized OLTP schema (3NF) for an e-commerce system
    2. Insert 1000 rows of realistic sample data
    3. Run a complex analytical query
    4. Explain WHY it's slow on row-store OLTP databases
    5. Show what a proper OLAP query plan would look like

PREREQUISITES:
    - Docker running with: docker-compose up -d
    - Python packages: pip install psycopg2-binary faker tabulate

USAGE:
    python setup_postgres.py

LEARNING OBJECTIVES:
    - Understand OLTP schema design (normalization)
    - See how EXPLAIN ANALYZE works in Postgres
    - Understand why row-store is inefficient for analytics
    - Understand what "sequential scan" means and why it's costly
"""

import psycopg2                    # PostgreSQL adapter for Python
import psycopg2.extras             # Provides execute_batch for bulk inserts
import random                      # For generating realistic random data
import time                        # For measuring query execution time
from datetime import datetime, timedelta  # For date manipulation
from decimal import Decimal        # For precise monetary values
import sys                         # For sys.exit on connection failure

# ============================================================================
# CONFIGURATION
# ============================================================================
# These match the docker-compose.yml settings. In production, use environment
# variables or a secrets manager - NEVER hardcode credentials in code.
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "ecommerce",
    "user": "deuser",
    "password": "depassword",
}

# ============================================================================
# SECTION 1: DATA CONSTANTS
# ============================================================================
# These lists give us realistic-looking data without external dependencies.
# In production, we'd use the `faker` library for more variety.

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael",
    "Linda", "William", "Barbara", "David", "Susan", "Richard", "Jessica",
    "Joseph", "Sarah", "Thomas", "Karen", "Charles", "Lisa", "Daniel",
    "Nancy", "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra",
    "Donald", "Ashley", "Steven", "Dorothy", "Paul", "Kimberly", "Andrew",
    "Emily", "Joshua", "Donna", "Kenneth", "Michelle", "Kevin", "Carol",
    "Brian", "Amanda", "George", "Melissa", "Timothy", "Deborah", "Ronald",
    "Stephanie",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson",
]

# Country codes with their names - used to simulate a multinational store
COUNTRIES = [
    ("US", "United States"), ("GB", "United Kingdom"), ("CA", "Canada"),
    ("DE", "Germany"),       ("FR", "France"),         ("AU", "Australia"),
    ("IN", "India"),         ("JP", "Japan"),           ("BR", "Brazil"),
    ("MX", "Mexico"),
]

# Product catalog: (name, category, base_price)
# These are used to generate the products table and order line items
PRODUCTS_DATA = [
    ("Laptop Pro 15",        "Electronics",   999.99),
    ("Wireless Mouse",       "Electronics",    29.99),
    ("USB-C Hub",            "Electronics",    49.99),
    ("Mechanical Keyboard",  "Electronics",   129.99),
    ("4K Monitor",           "Electronics",   399.99),
    ("Noise-Cancel Headset", "Electronics",   249.99),
    ("Python Cookbook",      "Books",          39.99),
    ("Clean Code",           "Books",          34.99),
    ("Design Patterns",      "Books",          44.99),
    ("Data Engineering",     "Books",          49.99),
    ("Coffee Maker",         "Kitchen",        79.99),
    ("Blender Pro",          "Kitchen",        59.99),
    ("Standing Desk",        "Furniture",     299.99),
    ("Ergonomic Chair",      "Furniture",     199.99),
    ("Desk Lamp LED",        "Furniture",      39.99),
    ("Notebook A4",          "Stationery",      4.99),
    ("Pen Set",              "Stationery",      9.99),
    ("Whiteboard",           "Stationery",     49.99),
    ("Running Shoes",        "Sports",        119.99),
    ("Yoga Mat",             "Sports",         29.99),
    ("Protein Powder",       "Health",         49.99),
    ("Vitamin C 1000mg",     "Health",         14.99),
    ("Backpack",             "Accessories",    59.99),
    ("Wallet Leather",       "Accessories",    29.99),
    ("Sunglasses",           "Accessories",    49.99),
]

ORDER_STATUSES = ["pending", "processing", "shipped", "delivered", "cancelled"]
# Weight: delivered is most common, cancelled is rare
STATUS_WEIGHTS = [0.05, 0.10, 0.20, 0.60, 0.05]


# ============================================================================
# SECTION 2: DATABASE SCHEMA
# ============================================================================

def create_schema(conn):
    """
    Creates the OLTP schema for our e-commerce database.
    
    This is a NORMALIZED (3NF) schema design:
    - No redundant data: customer name appears only in the customers table
    - Foreign keys enforce referential integrity
    - Each table has a single responsibility
    
    Trade-off: For analytics, you need to JOIN multiple tables, which is
    expensive on large datasets. This is why OLAP databases use denormalized
    star schemas instead.
    
    Schema Design (Entity-Relationship):
    
        users (1) ─────── (N) orders
        orders (1) ─────── (N) order_items
        products (1) ─── (N) order_items
    """
    print("\n" + "="*60)
    print("Creating OLTP Schema...")
    print("="*60)
    
    with conn.cursor() as cur:
        # ------------------------------------------------------------------
        # Drop existing tables in reverse dependency order
        # CASCADE ensures we don't get "table has dependent objects" errors
        # ------------------------------------------------------------------
        cur.execute("DROP TABLE IF EXISTS order_items CASCADE;")
        cur.execute("DROP TABLE IF EXISTS orders CASCADE;")
        cur.execute("DROP TABLE IF EXISTS products CASCADE;")
        cur.execute("DROP TABLE IF EXISTS users CASCADE;")
        print("  [OK] Dropped existing tables")
        
        # ------------------------------------------------------------------
        # USERS TABLE
        # Stores customer information. In OLTP, this is normalized - we 
        # don't duplicate customer info across multiple tables.
        # ------------------------------------------------------------------
        cur.execute("""
            CREATE TABLE users (
                user_id     SERIAL PRIMARY KEY,       -- Auto-incrementing PK
                first_name  VARCHAR(50) NOT NULL,
                last_name   VARCHAR(50) NOT NULL,
                email       VARCHAR(100) UNIQUE NOT NULL,  -- Unique constraint
                country_code CHAR(2) NOT NULL,         -- ISO 3166-1 alpha-2
                country_name VARCHAR(100) NOT NULL,
                created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
                
                -- Index on email for fast user lookups (common OLTP query)
                CONSTRAINT users_email_format CHECK (email LIKE '%@%')
            );
        """)
        print("  [OK] Created users table")
        
        # ------------------------------------------------------------------
        # PRODUCTS TABLE
        # Product catalog. In a real system, this would have many more
        # columns (description, images, variants, etc.)
        # ------------------------------------------------------------------
        cur.execute("""
            CREATE TABLE products (
                product_id   SERIAL PRIMARY KEY,
                name         VARCHAR(200) NOT NULL,
                category     VARCHAR(100) NOT NULL,
                unit_price   DECIMAL(10, 2) NOT NULL,  -- DECIMAL for money!
                stock        INTEGER NOT NULL DEFAULT 0,
                created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
                
                CONSTRAINT products_price_positive CHECK (unit_price > 0),
                CONSTRAINT products_stock_non_negative CHECK (stock >= 0)
            );
            
            -- Index for category-based queries (common: "show all electronics")
            CREATE INDEX idx_products_category ON products(category);
        """)
        print("  [OK] Created products table")
        
        # ------------------------------------------------------------------
        # ORDERS TABLE
        # Each row is one customer order (the "header" of an order).
        # Line items are in order_items table.
        # This is the classic "header-detail" pattern in OLTP design.
        # ------------------------------------------------------------------
        cur.execute("""
            CREATE TABLE orders (
                order_id     SERIAL PRIMARY KEY,
                user_id      INTEGER NOT NULL REFERENCES users(user_id),
                status       VARCHAR(20) NOT NULL DEFAULT 'pending',
                order_date   TIMESTAMP NOT NULL DEFAULT NOW(),
                total_amount DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
                
                CONSTRAINT orders_status_valid CHECK (
                    status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled')
                )
            );
            
            -- Index for finding orders by user (common OLTP query: "my orders")
            CREATE INDEX idx_orders_user_id ON orders(user_id);
            
            -- Index for date-range queries (common: "orders in the last week")
            CREATE INDEX idx_orders_date ON orders(order_date);
        """)
        print("  [OK] Created orders table")
        
        # ------------------------------------------------------------------
        # ORDER_ITEMS TABLE
        # The "detail" rows - one row per product in each order.
        # This is the junction table between orders and products.
        # ------------------------------------------------------------------
        cur.execute("""
            CREATE TABLE order_items (
                item_id      SERIAL PRIMARY KEY,
                order_id     INTEGER NOT NULL REFERENCES orders(order_id),
                product_id   INTEGER NOT NULL REFERENCES products(product_id),
                quantity     INTEGER NOT NULL DEFAULT 1,
                unit_price   DECIMAL(10, 2) NOT NULL,  -- Price AT TIME OF ORDER
                                                        -- (product price may change later)
                line_total   DECIMAL(12, 2) GENERATED ALWAYS AS 
                             (quantity * unit_price) STORED,  -- Computed column
                
                CONSTRAINT order_items_qty_positive CHECK (quantity > 0),
                CONSTRAINT order_items_price_positive CHECK (unit_price > 0)
            );
            
            -- Composite index for common join pattern: order_id + product_id
            CREATE INDEX idx_order_items_order ON order_items(order_id);
            CREATE INDEX idx_order_items_product ON order_items(product_id);
        """)
        print("  [OK] Created order_items table")
        
    conn.commit()
    print("\n  Schema creation COMPLETE.")


# ============================================================================
# SECTION 3: DATA GENERATION
# ============================================================================

def insert_sample_data(conn):
    """
    Inserts 1000 realistic rows of e-commerce data.
    
    We use psycopg2's execute_batch() which is MUCH faster than calling
    execute() in a loop because it batches multiple INSERTs into one
    network round-trip.
    
    Performance comparison:
    - Individual execute() calls: ~1000 round-trips to the DB
    - execute_batch() with page_size=100: ~10 round-trips
    
    For even larger datasets (millions of rows), use COPY FROM for maximum
    throughput (loads data at ~100x the speed of INSERT).
    """
    print("\n" + "="*60)
    print("Inserting Sample Data...")
    print("="*60)
    
    with conn.cursor() as cur:
        # ------------------------------------------------------------------
        # INSERT PRODUCTS (25 products)
        # ------------------------------------------------------------------
        product_records = [
            (name, category, price, random.randint(10, 500))
            for name, category, price in PRODUCTS_DATA
        ]
        psycopg2.extras.execute_batch(
            cur,
            """
            INSERT INTO products (name, category, unit_price, stock)
            VALUES (%s, %s, %s, %s)
            """,
            product_records,
            page_size=100
        )
        conn.commit()
        print(f"  [OK] Inserted {len(product_records)} products")
        
        # ------------------------------------------------------------------
        # INSERT USERS (200 unique users)
        # ------------------------------------------------------------------
        users_seen = set()  # Track emails to avoid duplicates
        user_records = []
        attempts = 0
        
        while len(user_records) < 200 and attempts < 10000:
            attempts += 1
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            # Add random number to email to ensure uniqueness
            email_num = random.randint(1, 9999)
            email = f"{first.lower()}.{last.lower()}{email_num}@example.com"
            
            if email in users_seen:
                continue
            users_seen.add(email)
            
            country_code, country_name = random.choice(COUNTRIES)
            # Backdate registration: users joined 0-2 years ago
            created_at = datetime.now() - timedelta(days=random.randint(1, 730))
            
            user_records.append((first, last, email, country_code, country_name, created_at))
        
        psycopg2.extras.execute_batch(
            cur,
            """
            INSERT INTO users (first_name, last_name, email, country_code, country_name, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            user_records,
            page_size=100
        )
        conn.commit()
        
        # Fetch user IDs for order generation
        cur.execute("SELECT user_id FROM users;")
        user_ids = [row[0] for row in cur.fetchall()]
        print(f"  [OK] Inserted {len(user_records)} users")
        
        # ------------------------------------------------------------------
        # Fetch product info for order generation
        # ------------------------------------------------------------------
        cur.execute("SELECT product_id, unit_price FROM products;")
        product_catalog = cur.fetchall()  # List of (product_id, unit_price)
        
        # ------------------------------------------------------------------
        # INSERT ORDERS + ORDER_ITEMS (1000 orders, 1-5 items each)
        # ------------------------------------------------------------------
        order_records = []
        item_records = []  # Will be built up per order
        
        for i in range(1000):
            # Each order belongs to a random user
            user_id = random.choice(user_ids)
            
            # Order date: somewhere in the last year
            order_date = datetime.now() - timedelta(
                days=random.randint(0, 365),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            # Weighted status: most orders are "delivered" (realistic)
            status = random.choices(ORDER_STATUSES, weights=STATUS_WEIGHTS, k=1)[0]
            
            order_records.append((user_id, status, order_date, 0.00))
        
        # Insert orders and get their IDs back
        # RETURNING is a PostgreSQL extension that returns specified columns
        # from the just-inserted rows - extremely useful for getting auto-generated PKs
        psycopg2.extras.execute_batch(
            cur,
            """
            INSERT INTO orders (user_id, status, order_date, total_amount)
            VALUES (%s, %s, %s, %s)
            """,
            order_records,
            page_size=100
        )
        conn.commit()
        
        # Fetch order IDs
        cur.execute("SELECT order_id, order_date FROM orders ORDER BY order_id;")
        order_rows = cur.fetchall()
        print(f"  [OK] Inserted {len(order_rows)} orders")
        
        # ------------------------------------------------------------------
        # INSERT ORDER ITEMS
        # ------------------------------------------------------------------
        item_records = []
        order_totals = {}  # Track total per order for update
        
        for order_id, order_date in order_rows:
            # Each order has 1-5 line items
            num_items = random.randint(1, 5)
            # Pick distinct products (no duplicate product in same order)
            chosen_products = random.sample(product_catalog, min(num_items, len(product_catalog)))
            
            order_total = Decimal("0.00")
            for product_id, unit_price in chosen_products:
                qty = random.randint(1, 3)
                # Add slight price variation (±10%) to simulate promotions
                price_variation = random.uniform(0.90, 1.10)
                actual_price = round(float(unit_price) * price_variation, 2)
                order_total += Decimal(str(actual_price)) * qty
                item_records.append((order_id, product_id, qty, actual_price))
            
            order_totals[order_id] = order_total
        
        psycopg2.extras.execute_batch(
            cur,
            """
            INSERT INTO order_items (order_id, product_id, quantity, unit_price)
            VALUES (%s, %s, %s, %s)
            """,
            item_records,
            page_size=500  # Larger page_size for better performance
        )
        conn.commit()
        print(f"  [OK] Inserted {len(item_records)} order items")
        
        # ------------------------------------------------------------------
        # UPDATE ORDER TOTALS
        # In a real system, this would be a database trigger or computed
        # in the application layer. We do it in a batch update here.
        # ------------------------------------------------------------------
        total_updates = [(float(total), order_id) for order_id, total in order_totals.items()]
        psycopg2.extras.execute_batch(
            cur,
            "UPDATE orders SET total_amount = %s WHERE order_id = %s;",
            total_updates,
            page_size=100
        )
        conn.commit()
        print(f"  [OK] Updated order totals")


# ============================================================================
# SECTION 4: QUERY ANALYSIS
# ============================================================================

def run_analytical_query_with_explain(conn):
    """
    Runs a complex analytical query on our OLTP database and demonstrates
    WHY it's inefficient.
    
    The query: "What is the total revenue per product category per month
                for the last 6 months, for non-cancelled orders?"
    
    This is a typical business analytics question. On an OLTP database:
    - It requires JOINing 3 tables
    - It must scan all rows (no useful index for this query pattern)
    - PostgreSQL must read ALL columns even though we only need a few
    
    EXPLAIN ANALYZE shows us:
    - The execution plan (which algorithm Postgres chose)
    - How many rows it estimated vs actually found
    - How much time each step took
    - Whether it used indexes or did sequential scans
    """
    print("\n" + "="*60)
    print("Running Analytical Query on OLTP Database")
    print("="*60)
    
    analytical_query = """
        SELECT 
            DATE_TRUNC('month', o.order_date) AS revenue_month,
            p.category                          AS product_category,
            COUNT(DISTINCT o.order_id)          AS num_orders,
            SUM(oi.quantity)                    AS total_units_sold,
            SUM(oi.line_total)                  AS total_revenue,
            AVG(oi.line_total)                  AS avg_line_value,
            MAX(oi.line_total)                  AS max_line_value
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p     ON oi.product_id = p.product_id
        WHERE 
            o.status != 'cancelled'
            AND o.order_date >= NOW() - INTERVAL '6 months'
        GROUP BY 1, 2
        ORDER BY 1 DESC, 5 DESC;
    """
    
    print("\n  Query:")
    print("  " + analytical_query.replace('\n', '\n  '))
    
    with conn.cursor() as cur:
        # -------------------------------------------------------------------
        # STEP 1: Get EXPLAIN ANALYZE output
        # EXPLAIN: Shows the query plan (the strategy Postgres chose)
        # ANALYZE: Actually EXECUTES the query and shows real timing
        # BUFFERS: Shows how many disk pages were read
        # -------------------------------------------------------------------
        print("\n  --- EXPLAIN ANALYZE (Query Plan) ---")
        start_time = time.time()
        
        cur.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) " + analytical_query)
        plan_rows = cur.fetchall()
        
        elapsed = time.time() - start_time
        
        for row in plan_rows:
            print("  " + row[0])
        
        print(f"\n  Execution time: {elapsed*1000:.2f}ms")
        
        # -------------------------------------------------------------------
        # STEP 2: Run the actual query and show results
        # -------------------------------------------------------------------
        print("\n  --- Actual Query Results ---")
        cur.execute(analytical_query)
        results = cur.fetchall()
        
        if results:
            print(f"\n  {'Month':<12} {'Category':<15} {'Orders':>8} {'Units':>8} {'Revenue':>12} {'Avg Line':>10}")
            print("  " + "-"*70)
            for row in results[:10]:  # Show first 10 rows
                month_str = row[0].strftime('%Y-%m') if row[0] else 'N/A'
                print(f"  {month_str:<12} {row[1]:<15} {row[2]:>8} {row[3]:>8} ${float(row[4]):>11.2f} ${float(row[5]):>9.2f}")
            
            if len(results) > 10:
                print(f"  ... and {len(results) - 10} more rows")
        
        # -------------------------------------------------------------------
        # STEP 3: Explain the performance implications
        # -------------------------------------------------------------------
        print("\n  " + "="*60)
        print("  PERFORMANCE ANALYSIS: Why is this slow at scale?")
        print("  " + "="*60)
        print("""
  1. SEQUENTIAL SCANS: With only 1000 rows, Postgres may still use
     indexes, but with millions of rows, all three tables need full
     sequential scans because:
     - The WHERE clause (order_date range) can use the date index,
       but then joining to order_items scans ALL those records
     - There's no index that covers the combination of filters we need

  2. ROW-STORE INEFFICIENCY: Postgres stores all columns together.
     To compute SUM(oi.line_total), it must read the ENTIRE row for
     each order_item: item_id, order_id, product_id, quantity, 
     unit_price, line_total. We only NEED line_total but pay for all.

  3. DISK I/O at scale: With 100 million order_items:
     - Each row is ~100 bytes
     - Total: ~10GB of data to scan
     - Columnar storage (Parquet/Snowflake): Only reads line_total 
       column = ~800MB. That's a 12x improvement in I/O alone.

  4. NO VECTORIZATION: Row-by-row processing can't leverage modern CPU
     SIMD instructions that process 8-16 values simultaneously.

  5. POOR COMPRESSION: Mixed-type rows compress at ~2x.
     Columnar same-type data compresses at ~5-10x.
     
  CONCLUSION: For this query pattern at scale (millions of rows),
  a columnar analytical database (BigQuery, Snowflake, DuckDB) would
  be 10x-100x faster. This is WHY data warehouses exist!
  """)


# ============================================================================
# SECTION 5: SHOW TABLE STATISTICS
# ============================================================================

def show_statistics(conn):
    """
    Shows basic statistics about our loaded data to verify everything
    was inserted correctly and to understand the data distribution.
    """
    print("\n" + "="*60)
    print("Database Statistics")
    print("="*60)
    
    with conn.cursor() as cur:
        # Table row counts
        for table in ["users", "products", "orders", "order_items"]:
            cur.execute(f"SELECT COUNT(*) FROM {table};")
            count = cur.fetchone()[0]
            print(f"  {table:<15}: {count:>6} rows")
        
        print()
        
        # Revenue by country (demonstrates JOIN query)
        cur.execute("""
            SELECT 
                u.country_name,
                COUNT(DISTINCT o.order_id) as num_orders,
                ROUND(SUM(o.total_amount)::numeric, 2) as total_revenue
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            WHERE o.status = 'delivered'
            GROUP BY u.country_name
            ORDER BY total_revenue DESC
            LIMIT 5;
        """)
        rows = cur.fetchall()
        print("  Top 5 Countries by Revenue (delivered orders only):")
        print(f"  {'Country':<20} {'Orders':>8} {'Revenue':>12}")
        print("  " + "-"*42)
        for row in rows:
            print(f"  {row[0]:<20} {row[1]:>8} ${float(row[2]):>11.2f}")
        
        print()
        
        # Product category breakdown
        cur.execute("""
            SELECT 
                p.category,
                COUNT(*) as num_items_sold,
                ROUND(SUM(oi.line_total)::numeric, 2) as category_revenue
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            JOIN orders o ON oi.order_id = o.order_id
            WHERE o.status != 'cancelled'
            GROUP BY p.category
            ORDER BY category_revenue DESC;
        """)
        rows = cur.fetchall()
        print("  Revenue by Product Category:")
        print(f"  {'Category':<15} {'Items Sold':>12} {'Revenue':>12}")
        print("  " + "-"*42)
        for row in rows:
            print(f"  {row[0]:<15} {row[1]:>12} ${float(row[2]):>11.2f}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Main entry point. Connects to Postgres and runs all setup steps.
    
    Error handling strategy:
    - Connection errors: Print helpful message about Docker, then exit
    - SQL errors: Let them propagate (they indicate a bug in our SQL)
    - Data errors: Should not occur with our controlled data generation
    """
    print("="*60)
    print("Module 1 Lab: OLTP Setup & Analytics Performance Demo")
    print("="*60)
    print("\nConnecting to PostgreSQL...")
    print(f"  Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"  Database: {DB_CONFIG['database']}")
    
    try:
        # psycopg2.connect() raises OperationalError if it can't connect
        conn = psycopg2.connect(**DB_CONFIG)
        # autocommit=False is the default - we commit explicitly after each section
        # This gives us control over transaction boundaries
        conn.autocommit = False
        print("  [OK] Connected successfully!\n")
        
    except psycopg2.OperationalError as e:
        print(f"\n  [ERROR] Could not connect to PostgreSQL: {e}")
        print("\n  Make sure Docker is running and the container is up:")
        print("    docker-compose up -d")
        print("  Then wait 5 seconds for Postgres to initialize and try again.")
        sys.exit(1)
    
    try:
        # Run all setup steps in sequence
        create_schema(conn)
        insert_sample_data(conn)
        show_statistics(conn)
        run_analytical_query_with_explain(conn)
        
        print("\n" + "="*60)
        print("Lab Complete! Key Takeaways:")
        print("="*60)
        print("""
  1. OLTP schema is normalized (3NF) - great for writes, bad for reads
  2. Complex analytics require JOINs across multiple tables
  3. Row-store forces reading all columns even when you need only a few
  4. EXPLAIN ANALYZE is your best friend for query optimization
  5. For serious analytics workloads, you need a columnar store:
     - DuckDB (embedded, great for learning/testing)
     - Snowflake, BigQuery, Redshift (cloud-scale)
     - Parquet files + Spark/Athena (data lake approach)
        """)
        
    finally:
        # Always close the connection, even if an exception occurred
        conn.close()
        print("  Database connection closed.")


if __name__ == "__main__":
    main()
