# Module 2: ETL & Batch Processing

## Table of Contents
1. [ETL vs ELT: The Paradigm Shift](#etl-vs-elt)
2. [Idempotency: The Most Critical Property](#idempotency)
3. [Load Strategies: Full vs Incremental](#load-strategies)
4. [Data Partitioning Strategies](#data-partitioning)
5. [Data Quality Dimensions](#data-quality)
6. [Schema Evolution](#schema-evolution)
7. [Common ETL Anti-Patterns](#anti-patterns)

---

## 1. ETL vs ELT: The Paradigm Shift

### The Traditional ETL Model

**ETL** stands for **Extract, Transform, Load**. In the traditional model:

```
Source System                Transform Server               Data Warehouse
+------------+               +------------+                 +------------+
|  Database  |   Extract     | Dedicated  |   Load Clean    | Warehouse  |
|   or API   | ------------> | ETL Server | --------------> |  (Oracle,  |
+------------+               | (Informatica,                | Teradata)  |
                             | DataStage)  |                +------------+
                             +------------+
                          
Timeline: 1990s - 2010s
```

**How it worked:**
1. **Extract**: Pull data from source systems to a staging area (often a dedicated ETL server)
2. **Transform**: Apply all business logic, cleaning, aggregation on the ETL server BEFORE loading
3. **Load**: Only load clean, transformed data into the expensive data warehouse

**Why it made sense then:**
- Data warehouse storage was EXTREMELY expensive ($50,000+ per TB in 2000s)
- Cloud didn't exist; you had fixed compute capacity
- Better to clean data before paying to store it
- ETL servers had specialized hardware for transformation workloads

**The problems with ETL:**
- ETL servers become bottlenecks (limited compute)
- Transformations are locked in proprietary tools (Informatica, DataStage)
- Long iteration cycles: change a transformation, re-run the whole pipeline
- Raw data is discarded after transformation - can't re-derive from scratch
- Debugging requires reproducing the source data exactly

### The Modern ELT Model

**ELT** stands for **Extract, Load, Transform**. The key difference: **load raw data FIRST, transform INSIDE the warehouse**.

```
Source System             Cloud Data Warehouse          Transform (Inside Warehouse)
+------------+            +------------------+          +------------------+
|  Database  |  Extract   | Raw/Staging      |  dbt     | Clean/Marts      |
|   or API   | ---------> | Layer            | -------> | Layer            |
+------------+            | (cheap cloud     |          | (optimized for   |
             Load raw     |  storage)        |          |  analytics)      |
             immediately  +------------------+          +------------------+

Timeline: 2015 - Present
Tools: Fivetran/Airbyte (E+L), dbt (T)
```

**Why ELT won:**
1. **Cloud storage is cheap**: Storing raw data in S3/GCS costs ~$0.02/GB/month
2. **Elastic compute**: Cloud warehouses scale compute up/down on demand
3. **SQL is king**: Data analysts know SQL; ELT transforms use SQL (via dbt)
4. **Raw data preserved**: Can always re-transform from scratch if business logic changes
5. **Separation of concerns**: Ingestion tools (Fivetran) do E+L; dbt does T
6. **Faster iteration**: Change a dbt model and re-run in minutes, not hours

### The Modern ELT Stack

```
STEP 1: Extract + Load (Ingestion Tools)
+--------+     +----------+     +------------------+
| Source | --> | Fivetran | --> | Raw Schema       |
| (Postgres,   | Airbyte  |     | in Snowflake     |
|  Salesforce, | Stitch   |     | (exact replica   |
|  APIs, etc.) +----------+     |  of source data) |
                                +------------------+

STEP 2: Transform (dbt)
+------------------+     +------------------+     +------------------+
| Raw Schema       | --> | Staging Models   | --> | Mart Models      |
| (bronze layer)   |     | (silver layer)   |     | (gold layer)     |
|                  |     | stg_orders.sql   |     | fct_orders.sql   |
|                  |     | stg_customers.sql|     | dim_customers.sql|
+------------------+     +------------------+     +------------------+
```

### When ETL Still Makes Sense

Despite ELT's dominance, ETL is still appropriate when:
- **PII/sensitive data**: Must transform (mask, encrypt) BEFORE storing anywhere
- **Very heavy transformation**: Computation too expensive to run in the warehouse
- **Legacy warehouse**: Old systems (on-prem Oracle) where storage is still expensive
- **Regulatory compliance**: Some industries require data to never touch a warehouse raw

---

## 2. Idempotency: The Most Critical Property

### What Is Idempotency?

A pipeline is **idempotent** if running it multiple times produces the same result as running it once.

Mathematically: `f(f(x)) = f(x)` for function f.

In practice: If your pipeline fails halfway through and you re-run it, the output is exactly the same as if it had succeeded on the first run.

### Why Is Idempotency Critical?

**Scenario 1: Network failure**
```
Day 1, 2:00 AM: Pipeline starts
Day 1, 2:30 AM: Network blip - pipeline fails mid-run
Day 1, 3:00 AM: Alerting wakes up the on-call engineer
Day 1, 3:05 AM: Engineer re-triggers the pipeline

QUESTION: Does the re-run produce correct data?
  - Non-idempotent pipeline: DUPLICATES data (rows inserted twice)
  - Idempotent pipeline: Produces exactly the same result as original
```

**Scenario 2: Backfill**
```
QUESTION: Can you re-process data for a historical date range?
  - Non-idempotent pipeline: Re-running for Jan 2024 adds MORE Jan 2024 data
  - Idempotent pipeline: Re-running for Jan 2024 produces exactly the Jan 2024 data
```

**Scenario 3: Bug fix**
```
QUESTION: You found a bug in your revenue calculation. Can you fix and re-run?
  - Non-idempotent pipeline: Now you have old wrong data + new correct data mixed
  - Idempotent pipeline: Re-run replaces old data with corrected data
```

### How to Achieve Idempotency

**Pattern 1: TRUNCATE + INSERT (full load)**
```sql
-- Delete ALL existing data for this period, then re-insert
-- This is idempotent: running 3 times = same as running once
BEGIN;
DELETE FROM daily_revenue WHERE date = '2024-01-15';
INSERT INTO daily_revenue SELECT ... WHERE date = '2024-01-15';
COMMIT;
```

**Pattern 2: UPSERT (INSERT ... ON CONFLICT)**
```sql
-- If record exists: update it. If not: insert it.
-- Running 3 times = same result as running once
INSERT INTO orders (order_id, amount, status)
VALUES (123, 29.99, 'delivered')
ON CONFLICT (order_id)
DO UPDATE SET
    amount = EXCLUDED.amount,
    status = EXCLUDED.status;
```

**Pattern 3: MERGE (for warehouses that support it)**
```sql
MERGE INTO target_table t
USING source_data s ON t.id = s.id
WHEN MATCHED THEN
    UPDATE SET t.amount = s.amount
WHEN NOT MATCHED THEN
    INSERT (id, amount) VALUES (s.id, s.amount);
```

**Pattern 4: Partition overwrite (Spark/BigQuery)**
```python
# Write to a specific partition - replaces the entire partition atomically
df.write.mode("overwrite").partitionBy("date").parquet("s3://bucket/orders/")

# Or in BigQuery:
# WRITE_TRUNCATE partition mode
```

### Anti-Patterns That Break Idempotency

```python
# BAD: Simple INSERT - duplicates data on re-run
def load_data_bad(data):
    for row in data:
        db.execute("INSERT INTO orders VALUES (%s, %s, %s)", row)
    # Re-running inserts all rows AGAIN

# GOOD: UPSERT - safe to re-run
def load_data_good(data):
    for row in data:
        db.execute("""
            INSERT INTO orders (order_id, amount, status) VALUES (%s, %s, %s)
            ON CONFLICT (order_id) DO UPDATE SET
                amount = EXCLUDED.amount,
                status = EXCLUDED.status
        """, row)
    # Re-running produces the same result

# BAD: Append-only with no deduplication
def process_bad(data):
    results = transform(data)
    results.to_sql('analytics', if_exists='append')  # Duplicates on re-run

# GOOD: Replace partition
def process_good(data, partition_date):
    results = transform(data)
    db.execute(f"DELETE FROM analytics WHERE date = '{partition_date}'")
    results.to_sql('analytics', if_exists='append')  # Safe to re-run
```

---

## 3. Load Strategies: Full vs Incremental

### Full Load

Re-loads the **entire** source table every time.

```
First run:  Source [A, B, C]  -->  Target [A, B, C]
Change: A updated, D added
Second run: Source [A', B, C, D] --> Target [A', B, C, D]  (completely replaced)
```

**When to use full load:**
- Small tables (< 100,000 rows) where re-loading is fast
- Reference/dimension tables (country codes, product categories)
- When you can't identify changed records
- When source data doesn't have reliable change timestamps

**Implementation:**
```python
def full_load(source_conn, target_conn, table_name):
    # Extract everything from source
    df = pd.read_sql(f"SELECT * FROM {table_name}", source_conn)
    
    # Truncate target and re-insert
    target_conn.execute(f"TRUNCATE TABLE {table_name}")
    df.to_sql(table_name, target_conn, if_exists='append', index=False)
```

### Incremental Load (Timestamp-Based)

Only extracts records that have changed since the last pipeline run.

```
First run (Jan 1):
  - Watermark: 1970-01-01 (epoch)
  - Extract: WHERE updated_at > '1970-01-01'  -->  All records
  - Save watermark: Jan 1, 02:00 AM

Second run (Jan 2):
  - Watermark: Jan 1, 02:00 AM
  - Extract: WHERE updated_at > 'Jan 1, 02:00 AM'  -->  Only changed records
  - Save watermark: Jan 2, 02:00 AM
```

**Requirements for timestamp-based incremental:**
- Source table must have an `updated_at` column
- Source system must actually UPDATE this column when records change
- Clock skew between systems must be handled (use a small lookback buffer)

**Implementation:**
```python
def incremental_load(source_conn, target_conn, table_name, watermark_file):
    # Read last watermark
    with open(watermark_file, 'r') as f:
        last_run = f.read().strip()
    
    # Extract only changed records
    df = pd.read_sql(f"""
        SELECT * FROM {table_name}
        WHERE updated_at > '{last_run}'
    """, source_conn)
    
    if df.empty:
        print("No new records")
        return
    
    # Upsert to target (idempotent!)
    upsert_to_target(df, target_conn, table_name)
    
    # Update watermark
    new_watermark = datetime.now().isoformat()
    with open(watermark_file, 'w') as f:
        f.write(new_watermark)
```

**The "Clock Skew" Problem:**
```
Source DB server time: 2:00:00 AM
Pipeline starts:       2:00:05 AM
Last watermark:        2:00:00 AM

A transaction started at 1:59:59 AM but COMMITTED at 2:00:03 AM.
Its updated_at = 1:59:59 AM (time the row was modified, not committed).

If we filter WHERE updated_at > '2:00:00 AM', we MISS this record!

Solution: Use a lookback buffer
  WHERE updated_at > '{last_watermark}' - INTERVAL '10 minutes'
  This re-processes the last 10 minutes (idempotent upsert handles duplicates).
```

### Change Data Capture (CDC)

CDC reads directly from the database's **transaction log** (WAL in Postgres, binlog in MySQL). Every INSERT, UPDATE, DELETE is captured as an event.

```
PostgreSQL Write-Ahead Log (WAL):
+------------------------------------------+
| LSN 0/12345: INSERT orders (id=100, ...) |
| LSN 0/12346: UPDATE orders SET status=.. |
| LSN 0/12347: DELETE users WHERE id=50    |
+------------------------------------------+
          |
          | Debezium reads WAL
          v
+------------------------------------------+
| Kafka Topic: postgres.public.orders      |
| {"op": "c", "after": {"id": 100, ...}}   |  <- Create
| {"op": "u", "before": {...}, "after":{}} |  <- Update
| {"op": "d", "before": {"id": 100, ...}}  |  <- Delete
+------------------------------------------+
```

**Advantages of CDC:**
- Captures DELETES (which timestamp-based incremental misses)
- No performance impact on source DB (reads logs, not the tables)
- Real-time or near-real-time latency
- Captures every intermediate state change

**Disadvantages:**
- Complex to set up (requires DB configuration changes)
- Requires message broker (Kafka/Kinesis)
- More operational overhead

---

## 4. Data Partitioning Strategies

Partitioning means physically dividing your data into separate files/directories based on column values. This is crucial for performance at scale.

### Why Partitioning Matters

```
WITHOUT PARTITIONING:
"Show me yesterday's orders"
Query must scan: ████████████████████████████████ (ALL data, e.g., 5 years)

WITH DATE PARTITIONING:
"Show me yesterday's orders"
Query scans: ██ (only yesterday's partition, e.g., 1/1825 of the data)
Speedup: up to 1825x less data read!
```

### Partition Strategies

**Time-based Partitioning (most common):**
```
data/orders/
├── year=2024/
│   ├── month=01/
│   │   ├── day=01/
│   │   │   └── orders_20240101.parquet
│   │   ├── day=02/
│   │   └── ...
│   └── month=02/
└── year=2025/
```

**Category/Type Partitioning:**
```
data/orders/
├── country=US/
├── country=GB/
├── country=DE/
```

**Range Partitioning (for numerical data):**
```sql
-- PostgreSQL table partitioning
CREATE TABLE orders (order_id INT, amount DECIMAL, order_date DATE)
PARTITION BY RANGE (order_date);

CREATE TABLE orders_2024 PARTITION OF orders
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

CREATE TABLE orders_2025 PARTITION OF orders
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
```

### Choosing the Right Partition Column

Good partition columns:
- **High cardinality but bounded**: dates, months, years
- **Frequently filtered**: if 90% of queries filter by country, partition by country
- **Even distribution**: avoid partitions with wildly different sizes

Bad partition columns:
- **Too many unique values**: partitioning by user_id creates millions of tiny files (the "small files problem")
- **Rarely filtered**: partitioning by color when nobody filters by color
- **Highly skewed**: if 80% of your orders are from the US, US partition is huge, others tiny

---

## 5. Data Quality Dimensions

Data quality is not binary (good/bad) - it has multiple dimensions:

### The Six Dimensions

| Dimension | Definition | Example Failure | Check |
|-----------|------------|-----------------|-------|
| **Completeness** | All required fields have values | order_date is NULL in 5% of rows | `COUNT(*) WHERE order_date IS NULL` |
| **Accuracy** | Data correctly reflects reality | A product with price=-5 | `CHECK price > 0` |
| **Consistency** | Same data agrees across systems | Order total != sum of line items | Cross-table validation |
| **Timeliness** | Data is fresh/up-to-date | Last order loaded 3 days ago | Check MAX(ingested_at) |
| **Validity** | Data conforms to defined formats | Email 'not_an_email' passes | Regex validation |
| **Uniqueness** | No duplicate records | Same order appears twice | `COUNT(*) != COUNT(DISTINCT id)` |

### Implementing Data Quality Checks

```python
class DataQualityChecker:
    """
    Runs data quality checks and raises alerts on failures.
    
    In production, these checks are run after each pipeline execution.
    Failures either block the pipeline or trigger alerts to data team.
    """
    
    def __init__(self, df, table_name):
        self.df = df
        self.table_name = table_name
        self.failures = []
    
    def check_completeness(self, column, max_null_pct=0.0):
        """Ensure a column has no (or few) nulls."""
        null_pct = self.df[column].isnull().mean() * 100
        if null_pct > max_null_pct:
            self.failures.append(
                f"[COMPLETENESS] {column}: {null_pct:.1f}% null (max: {max_null_pct}%)"
            )
    
    def check_uniqueness(self, column):
        """Ensure a column has no duplicate values."""
        total = len(self.df)
        unique = self.df[column].nunique()
        if unique < total:
            self.failures.append(
                f"[UNIQUENESS] {column}: {total - unique} duplicates found"
            )
    
    def check_range(self, column, min_val=None, max_val=None):
        """Ensure values fall within acceptable range."""
        if min_val is not None:
            violations = (self.df[column] < min_val).sum()
            if violations > 0:
                self.failures.append(
                    f"[ACCURACY] {column}: {violations} values below {min_val}"
                )
        if max_val is not None:
            violations = (self.df[column] > max_val).sum()
            if violations > 0:
                self.failures.append(
                    f"[ACCURACY] {column}: {violations} values above {max_val}"
                )
    
    def run(self, raise_on_failure=True):
        """Run all registered checks and report results."""
        if self.failures:
            msg = f"Data quality failures in {self.table_name}:\n"
            msg += "\n".join(f"  - {f}" for f in self.failures)
            if raise_on_failure:
                raise ValueError(msg)
            else:
                print(f"[WARNING] {msg}")
        else:
            print(f"[OK] All data quality checks passed for {self.table_name}")
```

---

## 6. Schema Evolution

Schema evolution is one of the most underrated challenges in data engineering. Source systems change their schemas, and your pipelines must handle this gracefully.

### Types of Schema Changes

**Backward-compatible (safe):**
- Adding a new nullable column
- Widening a column type (INT → BIGINT)
- Adding a new table

**Backward-incompatible (breaking):**
- Renaming a column
- Removing a column
- Changing a column's data type in an incompatible way (VARCHAR → INT)
- Changing nullability (nullable → NOT NULL)

### Handling Schema Evolution

**Strategy 1: Schema on read (most flexible)**
```python
# Store raw JSON - schema is applied when reading
# New columns are automatically available next read
raw_data = {"existing": "value", "new_column": "new_value"}
# Store as JSON string - schema is implicit
```

**Strategy 2: Additive schema migrations only**
```sql
-- Safe: add new column with default
ALTER TABLE orders ADD COLUMN discount_pct DECIMAL(5,2) DEFAULT 0.0;

-- Safe: widen column
ALTER TABLE orders ALTER COLUMN amount TYPE DECIMAL(15,2);

-- Dangerous: rename (breaks existing queries)
-- ALTER TABLE orders RENAME COLUMN amount TO total_amount;  -- DON'T
-- Instead: add new column, keep old one for compatibility
ALTER TABLE orders ADD COLUMN total_amount DECIMAL(15,2);
UPDATE orders SET total_amount = amount;
-- Remove old column only after all queries are updated
```

**Strategy 3: Schema registry (Kafka/Avro)**
```
Schema Registry ensures all producers and consumers agree on the schema.
Before writing to Kafka, producer checks if schema is compatible with
the registered schema. Incompatible changes are rejected.
```

---

## 7. Common ETL Anti-Patterns

### Anti-Pattern 1: God Pipeline
```python
# BAD: One 2000-line function that does everything
def run_pipeline():
    data = extract_everything()
    cleaned = clean_data(data)
    enriched = enrich_data(cleaned)
    aggregated = aggregate(enriched)
    load(aggregated)
    send_report()
    update_dashboard()
    backup_data()
    # ... 50 more things
```

**Why it's bad:** 
- A failure anywhere means re-running from scratch
- Impossible to test individual steps
- Can't parallelize steps

**Fix:** Atomic, single-responsibility tasks connected by an orchestrator (Airflow)

### Anti-Pattern 2: Non-Idempotent INSERT
Already covered in Section 2, but worth repeating: always use UPSERT or TRUNCATE+INSERT, never plain INSERT.

### Anti-Pattern 3: Loading Everything to Memory
```python
# BAD: Loads 50GB table into memory on your 8GB laptop
df = pd.read_sql("SELECT * FROM huge_table", conn)

# GOOD: Stream in chunks
for chunk in pd.read_sql("SELECT * FROM huge_table", conn, chunksize=10000):
    process_chunk(chunk)
```

### Anti-Pattern 4: No Error Handling / Logging
```python
# BAD: Silent failure
def load_data(data):
    try:
        insert_rows(data)
    except:
        pass  # Silently swallow errors - DATA LOSS!

# GOOD: Explicit error handling with logging
import logging
logger = logging.getLogger(__name__)

def load_data(data):
    try:
        inserted = insert_rows(data)
        logger.info(f"Successfully inserted {inserted} rows")
        return inserted
    except Exception as e:
        logger.error(f"Failed to insert data: {e}", exc_info=True)
        raise  # Re-raise so orchestrator knows the task failed
```

### Anti-Pattern 5: Hardcoded Credentials
```python
# BAD: Credentials in code (gets committed to git!)
conn = psycopg2.connect(password="mysupersecretpassword")

# GOOD: Environment variables
import os
conn = psycopg2.connect(password=os.environ["DB_PASSWORD"])
```

### Anti-Pattern 6: Mixing Business Logic with Infrastructure
```python
# BAD: Business logic buried in the extract step
def extract_and_filter():
    data = fetch_from_api()
    # Business logic: only include orders > $100 from US customers
    return [d for d in data if d['amount'] > 100 and d['country'] == 'US']

# GOOD: Separate concerns
def extract():
    return fetch_from_api()  # Pure extraction, no filtering

def transform(data):
    return [d for d in data if d['amount'] > 100 and d['country'] == 'US']
```

---

## Lab Overview

In the `labs/` directory, you'll find a complete ETL pipeline that:
1. **Extracts** real weather data from the Open-Meteo API (free, no key needed)
2. **Transforms** the data: cleans, validates, normalizes
3. **Loads** into PostgreSQL with proper UPSERT logic (idempotent)
4. **Orchestrates** all three steps with error handling and logging

Prerequisites:
```bash
pip install requests pandas psycopg2-binary python-dotenv
docker-compose up -d
```
