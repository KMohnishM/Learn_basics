# Module 1: Data Engineering Foundations

## Table of Contents
1. [What is Data Engineering?](#what-is-data-engineering)
2. [The Modern Data Stack](#the-modern-data-stack)
3. [OLTP vs OLAP](#oltp-vs-olap)
4. [Data Lakes vs Data Warehouses vs Lakehouses](#data-lakes-vs-data-warehouses-vs-lakehouses)
5. [Batch vs Streaming Processing](#batch-vs-streaming-processing)
6. [Data Pipeline Anatomy](#data-pipeline-anatomy)
7. [Common File Formats](#common-file-formats)

---

## 1. What is Data Engineering?

### The Discipline Defined

Data Engineering is the practice of **designing, building, and maintaining the infrastructure and systems that enable the collection, storage, processing, and analysis of data at scale**. If data scientists are the chefs who cook meals, data engineers are the farmers who grow the ingredients, the kitchen staff who prep them, and the infrastructure team that built the kitchen.

But this analogy only scratches the surface. Let's look at what data engineers actually do day-to-day:

#### Day-to-Day Responsibilities of a Data Engineer
- **Pipeline Development**: Writing code (Python, Scala, SQL) to move data from source systems (databases, APIs, event streams) into analytical storage
- **Data Modeling**: Designing schemas that make data easy to query and understand
- **Infrastructure Management**: Setting up and maintaining tools like Airflow, Spark, Kafka, dbt
- **Performance Optimization**: Making queries faster, pipelines more efficient, storage costs lower
- **Data Quality**: Building validation checks, monitoring data freshness, alerting on anomalies
- **Collaboration**: Working with data scientists to ensure data is in the right format for ML, with BI teams to ensure dashboards are fast, with software engineers to tap into the right data sources

### Data Engineering vs Data Science vs ML Engineering

These roles are frequently confused. Here is a definitive comparison:

```
+--------------------+---------------------------+---------------------------+
| Dimension          | Data Engineer             | Data Scientist            |
+--------------------+---------------------------+---------------------------+
| Primary Question   | "How do we move &         | "What insights can we     |
|                    |  store data?"             |  extract from the data?"  |
+--------------------+---------------------------+---------------------------+
| Core Skills        | SQL, Python, Spark,       | Statistics, Python/R,     |
|                    | Kafka, Airflow, dbt       | ML algos, visualization   |
+--------------------+---------------------------+---------------------------+
| Daily Work         | Building pipelines,       | Exploratory analysis,     |
|                    | infra, optimization       | model building, testing   |
+--------------------+---------------------------+---------------------------+
| Output             | Reliable data systems,    | Insights, reports,        |
|                    | pipelines                 | ML models                 |
+--------------------+---------------------------+---------------------------+
| Mindset            | Engineering: robust,      | Scientific: exploratory,  |
|                    | scalable, reliable        | hypothesis-driven         |
+--------------------+---------------------------+---------------------------+

+--------------------+---------------------------+---------------------------+
| Dimension          | ML Engineer               | Data Engineer             |
+--------------------+---------------------------+---------------------------+
| Primary Question   | "How do we deploy ML      | "How do we collect,       |
|                    |  models at scale?"        |  store, and transform?"   |
+--------------------+---------------------------+---------------------------+
| Core Skills        | MLOps, Docker, K8s,       | SQL, Python, Spark,       |
|                    | TF/PyTorch, feature stores| Kafka, Airflow            |
+--------------------+---------------------------+---------------------------+
| Overlap with DE    | Feature engineering,      | Feature pipelines,        |
|                    | training pipelines        | training data prep        |
+--------------------+---------------------------+---------------------------+
```

### The "Hierarchy of Needs" for Data Teams

Monica Rogati adapted Maslow's hierarchy for AI/data teams. Understanding this explains WHY data engineering matters:

```
                    /\
                   /AI\
                  / &  \         Level 5: Actual AI/ML products
                 / ML   \
                /--------\
               / Insights  \     Level 4: Analytics, A/B testing, BI
              /------------\
             / Transforms    \   Level 3: Aggregations, business logic
            /----------------\
           / Reliable Pipelines\ Level 2: ETL/ELT, data quality
          /--------------------\
         /  Infrastructure      \ Level 1: Storage, compute, networking
        /------------------------\
```

**Data Engineers build and maintain Levels 1-3.** Without a solid foundation at these levels, all the AI/ML work above is built on sand. This is why companies often hire data engineers BEFORE data scientists.

### Common Misconceptions

**Misconception 1**: "Data engineering is just writing ETL scripts"
**Reality**: Modern data engineering encompasses distributed systems design, stream processing, data modeling, infrastructure as code, and data governance.

**Misconception 2**: "Data engineers don't need to understand the business"
**Reality**: The best data engineers deeply understand business processes because they need to design systems that accurately capture and represent those processes.

**Misconception 3**: "Data engineers don't need statistics"
**Reality**: While not as deep as data scientists, understanding distributions, outliers, and statistical anomalies is crucial for data quality work.

---

## 2. The Modern Data Stack

The "Modern Data Stack" (MDS) refers to a set of cloud-native, SaaS tools that replaced legacy on-premise data warehousing.

### Architecture Diagram

```
+----------------------------------------------------------------------+
|                      THE MODERN DATA STACK                          |
|                                                                      |
|  +-----------+    +-----------+    +-----------+                     |
|  |  Sources  |    | Ingestion |    |  Storage  |                     |
|  |           |    |           |    |           |                     |
|  | Databases |-->-| Fivetran  |-->-| Snowflake |                     |
|  | APIs      |    | Airbyte   |    | BigQuery  |                     |
|  | Events    |    | Stitch    |    | Redshift  |                     |
|  | Files     |    | dlt       |    | Databricks|                     |
|  +-----------+    +-----------+    +-----+-----+                     |
|                                         |                            |
|                                         v                            |
|                                  +------+------+                     |
|                                  | Transform   |                     |
|                                  |             |                     |
|                                  | dbt         |                     |
|                                  | Spark       |                     |
|                                  | Dataform    |                     |
|                                  +------+------+                     |
|                                         |                            |
|                                         v                            |
|                                  +------+------+                     |
|                                  |  Serving    |                     |
|                                  |             |                     |
|                                  | Metabase    |                     |
|                                  | Looker      |                     |
|                                  | Tableau     |                     |
|                                  | APIs        |                     |
|                                  +-------------+                     |
|                                                                      |
|  +------------------------------------------------------------------+|
|  |          Orchestration Layer (Airflow, Prefect, Dagster)         ||
|  +------------------------------------------------------------------+|
+----------------------------------------------------------------------+
```

### Why the Modern Data Stack Won

**Before (Legacy Data Warehousing):**
- On-premise servers that you had to buy, rack, and maintain
- Proprietary tools (Oracle, Teradata) with million-dollar licenses
- Monolithic architectures where storage and compute were tightly coupled
- Schema-on-write: you had to define structure before loading data
- Long, waterfall-style projects to get any data into the warehouse

**After (Modern Data Stack):**
- Cloud-native: pay only for what you use, scale to petabytes
- Open-source friendly: dbt, Airflow, Airbyte are all open-source
- Separation of storage and compute: scale each independently
- Schema-on-read (in data lakes): load raw data first, apply structure later
- ELT paradigm: load raw data fast, transform in-warehouse using SQL

---

## 3. OLTP vs OLAP

This is arguably the most fundamental concept in data engineering. Understanding the deep technical differences explains WHY we need a separate analytical system.

### OLTP: Online Transaction Processing

OLTP systems are designed to handle the day-to-day transactional operations of a business. Think: your bank's account system, an e-commerce order database, a hotel booking system.

**Characteristics:**
- High volume of small, fast transactions (INSERT, UPDATE, DELETE)
- ACID transactions are mandatory (Atomicity, Consistency, Isolation, Durability)
- Normalized schema (3NF - Third Normal Form) to avoid data duplication
- Read and write operations are roughly balanced
- Response time measured in milliseconds
- Optimized for finding specific rows quickly

**Example OLTP Queries:**
```sql
-- Find a specific order
SELECT * FROM orders WHERE order_id = 12345;

-- Update inventory when a sale is made
UPDATE products SET stock = stock - 1 WHERE product_id = 42;

-- Insert a new customer
INSERT INTO customers (name, email) VALUES ('Alice', 'alice@example.com');
```

### OLAP: Online Analytical Processing

OLAP systems are designed for analytical queries that aggregate data across millions or billions of rows.

**Characteristics:**
- Complex queries that scan large amounts of data
- Mostly read operations (few writes)
- Denormalized schema (star/snowflake) to reduce joins
- Optimized for aggregations (SUM, AVG, COUNT, GROUP BY)
- Response time measured in seconds (acceptable for analytics)
- Column-oriented storage

**Example OLAP Queries:**
```sql
-- Total revenue per country per month
SELECT 
    DATE_TRUNC('month', order_date) as month,
    country,
    SUM(revenue) as total_revenue
FROM fact_orders
JOIN dim_customer USING (customer_id)
JOIN dim_date USING (date_id)
GROUP BY 1, 2
ORDER BY 1, 3 DESC;
```

### The Critical Technical Difference: Row-Store vs Columnar Storage

This is where data engineering gets really interesting. **Why is OLAP faster for analytics?**
It comes down to how data is physically stored on disk.

#### Row-Store (How PostgreSQL, MySQL work)

```
DISK LAYOUT (Row-Store):
+------------------------------------------------------------------+
| Row 1: [order_id=1][cust_id=101][product_id=5][amount=29.99]    |
| Row 2: [order_id=2][cust_id=102][product_id=3][amount=15.00]    |
| Row 3: [order_id=3][cust_id=101][product_id=7][amount=45.50]    |
| Row 4: [order_id=4][cust_id=103][product_id=5][amount=29.99]    |
+------------------------------------------------------------------+
```

To answer "What is the total revenue?", the database must:
1. Read EVERY byte of EVERY row (even columns we don't need like customer_id, product_id)
2. Extract just the `amount` column
3. Sum it up

For 1 billion rows with 50 columns where you only need 2, you're reading ~50x more data than necessary.

#### Columnar Storage (How BigQuery, Snowflake, Parquet work)

```
DISK LAYOUT (Columnar Store):
+--------------------------------------------+
| order_id column:    [1][2][3][4]           |
| customer_id column: [101][102][101][103]   |
| product_id column:  [5][3][7][5]           |
| amount column:      [29.99][15.00]         |
|                     [45.50][29.99]         |
+--------------------------------------------+
```

For the same "total revenue" query:
1. Jump directly to the `amount` column on disk
2. Read ONLY that column's data (skip all others entirely)
3. Sum it up using vectorized CPU instructions

**Performance benefits of columnar storage:**
1. **Reduced I/O**: Read only the columns you need (10x-100x less data read from disk)
2. **Better compression**: Same data type in sequence compresses far better
   - [29.99][29.99][29.99][29.99] --> run-length encoding makes this tiny
   - Mixed row data doesn't compress nearly as well
3. **Vectorized execution**: Modern CPUs process 256/512 bits at a time (SIMD).
   Columnar data enables vectorized operations across entire columns in one CPU instruction
4. **Predicate pushdown**: Can skip entire chunks of data using min/max statistics
   stored per column chunk (if max(amount) < 100, skip the entire row group for
   queries filtering amount > 100)

#### When Row-Store Wins

Row-store is NOT obsolete. It's still the right choice when:
- You need to fetch entire records (SELECT *)
- You have many small concurrent writes
- You need row-level locking and ACID transactions
- Your queries return individual rows, not aggregates

### OLTP vs OLAP Comparison Table

```
+--------------------+-------------------------+-------------------------+
| Characteristic     | OLTP                    | OLAP                    |
+--------------------+-------------------------+-------------------------+
| Purpose            | Run the business        | Analyze the business    |
| Query Type         | Simple, specific        | Complex, aggregating    |
| Data Volume        | GB to low TB            | TB to PB                |
| Typical Users      | App users, clerks       | Analysts, executives    |
| Schema             | Normalized (3NF)        | Denormalized (Star)     |
| Storage            | Row-oriented            | Column-oriented         |
| Transactions       | Required (ACID)         | Not critical            |
| Optimization       | Index on primary key    | Partitioning, clustering|
| History            | Current state only      | Historical data         |
| Examples           | Postgres, MySQL,        | Snowflake, BigQuery,    |
|                    | Oracle, SQL Server      | Redshift, DuckDB        |
+--------------------+-------------------------+-------------------------+
```

---

## 4. Data Lakes vs Data Warehouses vs Lakehouses

### Data Warehouse

A data warehouse is a centralized repository optimized for analytical queries.

Key characteristics:
- **Structured data only**: Must conform to a predefined schema (schema-on-write)
- **Highly optimized**: Columnar storage, compression, query optimization built-in
- **SQL interface**: Standard SQL queries work out of the box
- **Cost**: High (especially for storage compared to object storage)
- **Examples**: Snowflake, BigQuery, Redshift, Synapse Analytics

```
Data Warehouse:
+-------------------------------------------------+
|               DATA WAREHOUSE                    |
|                                                 |
|  +----------+  +----------+  +-------------+  |
|  |  Stage   |->|Transform |->|  Curated    |  |
|  |  (Raw)   |  |  (dbt)   |  |  (Serving)  |  |
|  +----------+  +----------+  +-------------+  |
|                                                 |
|  OK: Fast SQL queries                          |
|  OK: ACID transactions                         |
|  OK: Governance & access control               |
|  NO: Expensive for raw/unstructured data       |
|  NO: Semi/unstructured data needs ETL first    |
+-------------------------------------------------+
```

### Data Lake

A data lake stores raw data in its native format at massive scale with very low cost.

- **Any data format**: Structured (CSV, Parquet), semi-structured (JSON), unstructured (images, logs)
- **Schema-on-read**: Apply structure when you query, not when you store
- **Cheap storage**: S3, GCS, Azure Blob Storage at pennies per GB-month
- **No native SQL engine**: Needs an engine on top (Spark, Hive, Presto, Athena)
- **Risk of "data swamp"**: Without governance, it becomes an unusable pile of files

```
Data Lake:
+-------------------------------------------------+
|                  DATA LAKE                      |
|                                                 |
|  Raw Zone           Curated Zone               |
|  +---------+        +-----------+              |
|  | CSV     |        | Parquet   |              |
|  | JSON    |------->| files     |              |
|  | Images  |        | (cleaned) |              |
|  | Logs    |        +-----------+              |
|  +---------+                                   |
|                                                 |
|  OK: Cheap storage (S3/GCS)                    |
|  OK: Any data type                             |
|  OK: Schema flexibility                        |
|  NO: No ACID transactions                      |
|  NO: No indexing (scans full files)            |
|  NO: Easy to become a "data swamp"             |
+-------------------------------------------------+
```

### The Lakehouse: Best of Both Worlds

The Lakehouse architecture emerged around 2020 to solve the problems of both approaches.
It adds a **transaction layer** on top of data lake storage, giving you:
- Cheap storage (data stays in S3/GCS as Parquet files)
- ACID transactions (no partial writes, no dirty reads)
- Schema enforcement (optional but available)
- Fast SQL queries via metadata and statistics

**Technologies enabling Lakehouses:**

#### Delta Lake (Databricks)
Delta Lake adds a `_delta_log/` directory alongside your Parquet files:

```
s3://my-bucket/orders/
|-- _delta_log/
|   |-- 00000000000000000000.json  <- Transaction log entry 0
|   |-- 00000000000000000001.json  <- Transaction log entry 1
|   `-- 00000000000000000010.checkpoint.parquet
|-- part-00000-abc123.parquet
|-- part-00001-def456.parquet
`-- part-00002-ghi789.parquet
```

The transaction log records every change (insert, update, delete, schema change), enabling:
- **Time travel**: `SELECT * FROM orders VERSION AS OF 5`
- **Rollback**: `RESTORE TABLE orders TO VERSION AS OF 3`
- **ACID transactions**: No partial writes ever visible to readers
- **Schema evolution**: Tracked and enforced through the log

#### Apache Iceberg (Open standard)
Similar to Delta Lake but designed as an open specification. Not tied to Databricks.
Adopted by AWS (Athena, Glue), Netflix, Apple, LinkedIn as their primary format.

Key advantage over Delta: Better partition evolution (can change how data is
partitioned without rewriting all files), hidden partitioning (users write queries
without knowing partition structure), and true open specification anyone can implement.

#### Apache Hudi (Uber)
Focused on incremental processing and record-level upserts.
Popular for CDC (Change Data Capture) use cases where you need to merge updates
into your lake at the individual record level efficiently.

### Comparison Matrix

```
+-----------------+--------------+----------------+------------------+
| Feature         | Data Warehouse| Data Lake      | Lakehouse        |
+-----------------+--------------+----------------+------------------+
| Storage Cost    | $$$$         | $              | $                |
| Query Speed     | Very Fast    | Slow           | Fast             |
| ACID            | Yes          | No             | Yes              |
| Schema Control  | Strict       | None           | Optional/Enforced|
| Data Types      | Structured   | Any            | Any              |
| ML Workloads    | Limited      | Great          | Great            |
| BI Workloads    | Great        | Poor           | Great            |
| Time Travel     | Rare         | No             | Yes              |
| Examples        | Snowflake,   | S3+Glue,       | Databricks,      |
|                 | BigQuery     | HDFS+Hive      | Delta/Iceberg    |
+-----------------+--------------+----------------+------------------+
```

---

## 5. Batch vs Streaming Processing

### Batch Processing

Batch processing means collecting data over a period of time, then processing it all at once.

```
BATCH PROCESSING:

  Events: ●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●
           <-------- collect for 1 hour -------->
                                               |
                                  +--------------------------+
                                  |  Process all data at     |
                                  |  once (Spark, SQL, dbt)  |
                                  +-----------+--------------+
                                              |
                                          Results
```

**When to use Batch:**
- Daily/weekly sales reports (nobody needs up-to-the-second accuracy for these)
- ML model training (train on yesterday's complete data)
- ETL pipelines that run nightly
- Data warehouse loading (most DW loads are batch)
- When data arrives in files or database dumps (not streams)
- When latency requirements are hours or days (not seconds)

**Advantages of Batch:**
- Simpler to build, test, and debug - you can inspect the input before processing
- Cheaper: run during off-peak hours when compute costs less
- Easier data quality checks: validate entire dataset before committing
- Well-understood failure modes: just re-run the batch
- Better for large aggregations: can sort and optimize globally across all data

### Streaming Processing

Streaming means processing each event (or micro-batch) as it arrives, continuously.

```
STREAMING PROCESSING:

  Event arrives -> Process immediately -> Result in near-real-time
       ●          ─────────────────>       *
       ●          ─────────────────>       *
       ●          ─────────────────>       *
  (continuous)                       (latency: ms to seconds)
```

**When to use Streaming:**
- Fraud detection (must decide within milliseconds of the transaction)
- Real-time dashboards (live metrics showing active users right now)
- Alerting systems (notify ops team immediately when error rate spikes)
- Recommendation systems (show relevant content immediately after user action)
- IoT sensor data processing (detect equipment failure in real-time)
- Financial tick data and trading systems

**Advantages of Streaming:**
- Low latency: sub-second to seconds from event to insight
- Continuous insights: always up-to-date
- Can react to events as they happen, enabling event-driven architectures

### Trade-offs Table

```
+-----------+----------+-------------+-----------+
| Dimension | Batch    | Micro-batch | Streaming |
+-----------+----------+-------------+-----------+
| Latency   | Hrs/Days | Minutes     | Millisec  |
| Throughput| Very High| High        | Medium    |
| Complexity| Low      | Medium      | High      |
| Cost      | Low      | Medium      | High      |
| Debugging | Easy     | Medium      | Hard      |
| Exactly-1x| Easy     | Medium      | Very Hard |
| Use case  | Analytics| Near-RT     | True RT   |
+-----------+----------+-------------+-----------+
```

### The Common Misconception About Streaming

Many beginners think "streaming is always better because it's faster." This is WRONG.

**Streaming is HARDER and MORE EXPENSIVE.** You should only use streaming when your
business genuinely cannot tolerate batch latency. Most analytics use cases are
perfectly fine with batch processing that runs hourly or daily.

Questions to ask before choosing streaming:
1. What is the maximum acceptable latency? (If hours are fine, use batch)
2. Does the business process actually change with real-time data?
   (Fraud detection: yes. Monthly sales report: absolutely no.)
3. Do we have the engineering capacity to maintain a streaming system?
   (Streaming systems require more operational expertise to run reliably)
4. Is the cost justified by the business value?

---

## 6. Data Pipeline Anatomy

A data pipeline is a series of automated processes that move and transform data from
source to destination. Every pipeline follows this fundamental anatomy:

```
+----------------------------------------------------------------------+
|                       DATA PIPELINE ANATOMY                         |
|                                                                      |
|  +---------+    +---------+    +-----------+    +---------+         |
|  |INGESTION|-->-| STORAGE |-->-| TRANSFORM |-->-| SERVING |         |
|  +---------+    +---------+    +-----------+    +---------+         |
|      |              |               |               |               |
| API pulls      Raw layer       Cleaning         BI layer            |
| CDC from DB    Data lake       Filtering        Data marts          |
| File drops     S3/GCS/HDFS     Aggregating      Feature store       |
| Event stream   Staging tables  Joining          API endpoints       |
| Webhooks       Bronze zone     Enriching        ML models           |
|                Raw parquet     dbt models       Reports             |
+----------------------------------------------------------------------+
```

### Stage 1: Ingestion

Ingestion is getting data FROM source systems INTO your storage system.

**Full Extract**: Copy the entire source table every time.
- Simple but expensive for large tables
- Good for small reference tables (countries, product categories, configs)

**Incremental Extract**: Only copy new/changed records since last run.
- Requires a `updated_at` timestamp or sequence number in source
- Much more efficient for large tables
- Requires careful handling of deletes (which don't update timestamps)

**Change Data Capture (CDC)**: Tap into the database's transaction log.
- Captures every INSERT, UPDATE, DELETE in real time at the database level
- Tools: Debezium (reads Postgres/MySQL WAL), AWS DMS, Fivetran Log-based CDC
- Most complete picture but most complex to set up and maintain

**Event Streaming**: Source systems emit events that you consume.
- Kafka, Kinesis, Pub/Sub
- Best for high-frequency, real-time use cases
- Requires source system to be designed as event-driven

### Stage 2: Storage (The Medallion Architecture)

Modern data platforms use a layered storage approach called the **Medallion Architecture**:

```
+----------------------------------------------------------------------+
|                     MEDALLION ARCHITECTURE                          |
|                                                                      |
|  BRONZE (Raw)          SILVER (Cleaned)      GOLD (Served)          |
|  +------------+        +------------+        +------------+         |
|  | Raw data   |------->| Validated  |------->| Aggregated |         |
|  | as-is from |        | Deduped    |        | Business   |         |
|  | source     |        | Normalized |        | metrics    |         |
|  |            |        | Typed      |        |            |         |
|  | NEVER EDIT |        |            |        | Star schema|         |
|  +------------+        +------------+        +------------+         |
|                                                                      |
| Retention: Forever   Retention: 1-3yr      Retention: 90 days      |
+----------------------------------------------------------------------+
```

**Bronze (Raw) Layer Rules:**
- NEVER modify raw data - preserve exactly what came from the source
- Add ingestion metadata: load timestamp, source system identifier, batch ID
- Partition by ingestion date so you can reprocess specific time ranges
- This is your "source of truth" for any reprocessing needs

**Silver (Cleaned) Layer:**
- Apply data quality rules and reject/quarantine bad records
- Deduplicate records (critical for idempotent pipelines)
- Cast to correct data types (string '29.99' becomes DECIMAL 29.99)
- Apply business rules (standardize country codes, normalize phone numbers)
- Join with slowly-changing reference data

**Gold (Serving) Layer:**
- Business-level aggregations and metrics
- Optimized for specific query patterns (pre-joined, pre-aggregated)
- Powers dashboards, reports, ML features
- May be further split into data marts per business domain

### Stage 3: Transformation

Key transformation operations:
- **Cleaning**: Handle nulls, fix encoding issues, standardize date formats
- **Validation**: Check business rules (no negative prices, valid email format)
- **Deduplication**: Remove duplicate records that idempotent pipelines create
- **Enrichment**: Join with reference data (add country name from ISO code)
- **Aggregation**: Roll up to business-level metrics (daily revenue per region)
- **Business logic**: Apply domain-specific calculations and rules

### Stage 4: Serving

Data needs to be accessible in the right form for the right consumers:

- **BI Tools** (Metabase, Looker): Need fast, pre-aggregated data in a star schema
- **Data Scientists**: Need wide, flat tables with features ready for ML training
- **APIs**: Need low-latency lookups, often from Redis or a separate OLTP replica
- **Other Pipelines**: Your pipeline's output may be another pipeline's input

---

## 7. Common File Formats

Choosing the right file format has enormous impact on storage cost, query performance,
and interoperability between tools.

### CSV (Comma-Separated Values)

```csv
order_id,customer_id,amount,date
1,101,29.99,2024-01-15
2,102,15.00,2024-01-15
3,101,45.50,2024-01-16
```

**Pros:**
- Human-readable and universally understood
- Supported by every tool, language, and system
- Simple to generate and debug

**Cons:**
- No schema enforcement (all values treated as strings)
- No compression natively (must use gzip externally)
- No predicate pushdown (must read entire file to filter)
- Delimiter conflicts require complex quoting/escaping rules
- Terrible for analytics on large datasets

**When to use:** Data exchange with external systems, small datasets, quick prototypes,
data you need a human to inspect in a text editor.

### JSON (JavaScript Object Notation)

```json
{"order_id": 1, "customer": {"id": 101, "name": "Alice"}, "items": [{"product": "A", "qty": 2}]}
{"order_id": 2, "customer": {"id": 102, "name": "Bob"}, "items": [{"product": "B", "qty": 1}]}
```

**Pros:**
- Supports nested/hierarchical data natively (arrays, objects within objects)
- Human-readable and debuggable
- Schema flexibility (fields can vary between records)
- Native to web APIs and most modern web services

**Cons:**
- Verbose: field names are repeated for EVERY record (wastes storage)
- Large file sizes compared to binary formats
- Slow to parse at scale
- No native compression (compress externally with gzip)

**When to use:** API payloads, event streaming messages, config files, data with
variable schemas. Use JSON Lines format (one JSON object per line) for streaming,
not one giant JSON array.

### Parquet (Apache Parquet)

**The most important format in modern data engineering.**

```
Parquet file layout:
+---------------------------------------------------+
|               File Header (magic bytes)           |
+---------------------------------------------------+
|         Row Group 1 (e.g., 128MB of data)         |
|   +----------------------------------------------+|
|   | Column Chunk: order_id                       ||
|   |   Page 1 (compressed) | Page 2 | Page 3     ||
|   +----------------------------------------------+|
|   +----------------------------------------------+|
|   | Column Chunk: amount                          ||
|   |   Page 1 (compressed) | Page 2 | Page 3     ||
|   +----------------------------------------------+|
+---------------------------------------------------+
|         Row Group 2                               |
+---------------------------------------------------+
|         File Footer (metadata)                    |
|  - Schema definition (column names + types)       |
|  - Column statistics (min, max, null count)       |
|  - Row group offsets (byte positions in file)     |
+---------------------------------------------------+
```

**Why Parquet is so powerful:**

1. **Columnar storage**: Only read the columns your query actually needs
   (a query touching 3 of 50 columns reads 6% of the data vs 100% for row-store)

2. **Excellent compression**: Same-type data in sequence compresses dramatically better.
   Typical compression ratios: 4x-10x vs uncompressed CSV.
   - Dictionary encoding: For country codes (low cardinality), store ['US','GB','IN']
     and replace each value with a 2-bit integer reference
   - Run-length encoding (RLE): [US][US][US][US] -> [(US, 4)]
   - Delta encoding: [1000][1001][1002][1003] -> [1000][+1][+1][+1]
   - Bit packing: 1000 boolean values fit in 125 bytes, not 1000 bytes

3. **Statistics for pushdown**: Each column chunk stores min/max/null_count.
   If you filter WHERE amount > 1000 and a row group has max(amount) = 500,
   the entire row group is skipped without reading any data from it.

4. **Schema embedded in file**: No external schema catalog needed.
   The schema is stored in the file footer and read automatically.

5. **Splittable**: Multiple workers can process different row groups in parallel.
   A 10GB Parquet file can be processed by 10 workers each handling 1GB.

**When to use:** Almost always for analytical workloads. Default format for Spark,
dbt on data lakes, BigQuery external tables, Redshift Spectrum. If in doubt, use Parquet.

### Avro (Apache Avro)

Avro is a **row-based** binary format with a schema defined in JSON:

```json
{
  "type": "record",
  "name": "Order",
  "fields": [
    {"name": "order_id", "type": "int"},
    {"name": "amount",   "type": "double"},
    {"name": "date",     "type": "string"},
    {"name": "status",   "type": ["null", "string"], "default": null}
  ]
}
```

**Pros:**
- Schema evolution support: add fields, rename with aliases, all backward compatible
- Row-based: efficient for writing one record at a time (important for streaming)
- Compact binary format: much smaller than JSON
- Language-independent serialization
- Native support in Kafka with Schema Registry for schema governance

**Cons:**
- Row-based: poor query performance for analytics (must read all columns)
- Binary format: not human-readable, harder to debug

**When to use:** Kafka messages (the standard for streaming), streaming data ingestion,
when schema evolution is critical (Avro's main advantage), Hadoop sequence files.

### ORC (Optimized Row Columnar)

ORC is a columnar format developed for Hive. Very similar to Parquet:

```
+-------------------+------------------+------------------+
| Feature           | Parquet          | ORC              |
+-------------------+------------------+------------------+
| Origin            | Twitter+Cloudera | Hortonworks+Hive |
| Default compress  | Snappy           | Zlib             |
| Predicate pushdown| Yes              | Yes + Bloom filter|
| Hive support      | Good             | Excellent (native)|
| Spark support     | Excellent        | Good             |
| Python (pyarrow)  | Excellent        | Limited          |
+-------------------+------------------+------------------+
```

**When to use:** Hive-heavy Hadoop environments, when you need bloom filter pushdown
for high-cardinality columns, legacy Hadoop ecosystems.

### Format Decision Guide

```
Question: DO YOU NEED HUMAN READABILITY?
                    |
          Yes ------+------ No
           |                |
          CSV           IS DATA HIERARCHICAL/NESTED?
  (small datasets)          |
                   Yes -----+----- No
                    |               |
                   JSON         IS THIS FOR STREAMING/WRITING?
                                    |
                          Yes ------+------ No
                           |                |
                          AVRO          IS THIS FOR HIVE/HADOOP?
                                            |
                                  Yes ------+------ No
                                   |                |
                                  ORC            PARQUET
                                              (usually the answer)
```

---

## Summary: Key Takeaways

1. **Data Engineering is infrastructure** - the foundation everything else is built on
2. **OLTP and OLAP are different systems with different purposes** - never use your
   production database as your analytics database at scale
3. **Columnar storage is the key innovation** behind modern analytics speed:
   less I/O, better compression, vectorized processing, statistics-based skipping
4. **The Lakehouse is the modern answer** - cheap storage + ACID transactions + SQL
5. **Batch is simpler and cheaper** - only use streaming when business truly needs it
6. **Parquet is your default analytical format** - use it unless you have a specific reason
7. **The pipeline has four stages**: Ingestion -> Storage (Medallion) -> Transform -> Serve

---

## Prerequisites for This Module's Lab

- Docker and Docker Compose installed
- Python 3.8+ with pip
- Required packages:

```bash
pip install psycopg2-binary faker pandas tabulate
```

Then proceed to the `labs/` directory to run the hands-on exercises.
