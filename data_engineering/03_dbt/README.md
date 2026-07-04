# Module 3: dbt (Data Build Tool)

## Table of Contents
1. [Why dbt Exists](#why-dbt-exists)
2. [dbt Project Structure](#dbt-project-structure)
3. [Materializations](#materializations)
4. [dbt DAG and ref()](#dbt-dag-and-ref)
5. [Testing in dbt](#testing-in-dbt)
6. [Incremental Models](#incremental-models)
7. [dbt Documentation and Data Contracts](#dbt-documentation)
8. [Jinja Templating in dbt](#jinja-templating)

---

## 1. Why dbt Exists

### The Problem Before dbt

In the ELT paradigm, data is loaded into the warehouse raw, then transformed using SQL. Before dbt, this looked like:

```
BEFORE dbt:
+-----------+     +-----------+     +-----------+
| Python    | --> | Raw Table | --> | Many SQL  |
| ETL script|     | in Postgres     | scripts   |
+-----------+     +-----------+     | scattered |
                                    | everywhere|
                                    +-----------+
Problems:
- No testing: how do you know the data is correct?
- No documentation: what does this table even mean?
- No lineage: which tables depend on which?
- No version control standards: SQL scripts in shared folders
- Dependency management: what order do you run scripts?
- Environment management: dev vs prod schemas
```

dbt solves ALL of these problems by treating SQL models as **software artifacts** with:
- Version control (SQL files in git)
- Dependency management (via `ref()`)
- Testing (built-in test framework)
- Documentation (auto-generated from YAML)
- Environment management (profiles.yml)
- Incremental processing

### What dbt Does

dbt is a **transformation framework** for SQL. It does the T in ELT.

**What dbt is NOT:**
- dbt doesn't extract data (that's Fivetran, Airbyte, custom scripts)
- dbt doesn't load raw data (same)
- dbt doesn't run on its own (it runs SQL inside your data warehouse)

**What dbt IS:**
- A framework for organizing SQL transformations as "models"
- A testing framework for data quality
- A documentation generator
- A DAG orchestrator (within the transformation layer)
- A template engine (Jinja) for dynamic SQL

```
dbt's Role in the Stack:

Raw Tables           dbt Models              Marts
(loaded by           (SQL transformations    (for BI/ML)
 Fivetran/            with testing +
 Airbyte)             documentation)

+----------+         +-------------+         +----------+
| raw.     |  ref()  | stg_orders  |  ref()  | fct_     |
| orders   | ------> |             | ------> | orders   |
+----------+         +-------------+         +----------+

+----------+         +-------------+         +----------+
| raw.     |  ref()  | stg_        |  ref()  | dim_     |
| customers| ------> | customers   | ------> | customers|
+----------+         +-------------+         +----------+
```

---

## 2. dbt Project Structure

A dbt project is a directory of SQL files with a specific layout:

```
my_dbt_project/
|-- dbt_project.yml          <- Project configuration (name, version, model paths)
|-- profiles.yml             <- Database connection settings (in ~/.dbt/ typically)
|-- packages.yml             <- dbt package dependencies (like pip requirements.txt)
|
|-- models/                  <- SQL transformation files (the heart of dbt)
|   |-- staging/             <- Layer 1: Clean raw data
|   |   |-- stg_orders.sql
|   |   |-- stg_customers.sql
|   |   `-- schema.yml       <- Tests + docs for staging models
|   |
|   `-- marts/               <- Layer 2: Business-ready models
|       |-- fct_orders.sql
|       |-- dim_customers.sql
|       `-- schema.yml
|
|-- seeds/                   <- Static CSV files loaded as tables
|   `-- country_codes.csv
|
|-- tests/                   <- Custom singular tests (SQL files)
|   `-- assert_order_total_positive.sql
|
|-- macros/                  <- Jinja macros (reusable SQL functions)
|   `-- cents_to_dollars.sql
|
|-- snapshots/               <- SCD Type 2 snapshots
|   `-- customers_snapshot.sql
|
|-- analyses/                <- One-off analytical queries (not materialized)
|   `-- revenue_by_cohort.sql
|
`-- target/                  <- Compiled SQL (auto-generated, don't edit)
    `-- compiled/
```

### dbt_project.yml

```yaml
name: 'my_ecommerce_project'
version: '1.0.0'
config-version: 2

# dbt uses this to know where to find models
model-paths: ["models"]
seed-paths: ["seeds"]
test-paths: ["tests"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

# Default materialization for all models
# Can be overridden at folder or model level
models:
  my_ecommerce_project:
    staging:
      +materialized: view      # Staging = views (cheap, always fresh)
      +schema: staging         # Put in 'staging' schema
    marts:
      +materialized: table     # Marts = tables (pre-computed for performance)
      +schema: marts
```

### profiles.yml (in ~/.dbt/profiles.yml)

```yaml
my_ecommerce_project:
  target: dev  # Default target
  outputs:
    dev:
      type: postgres
      host: localhost
      port: 5432
      user: deuser
      password: depassword
      dbname: ecommerce
      schema: dbt_dev           # All models go in 'dbt_dev' schema in dev
      threads: 4                # Parallel model execution

    prod:
      type: postgres
      host: prod-db.company.com
      port: 5432
      user: "{{ env_var('DBT_USER') }}"      # Never hardcode prod credentials
      password: "{{ env_var('DBT_PASSWORD') }}"
      dbname: prod_warehouse
      schema: analytics
      threads: 8
```

---

## 3. Materializations

A materialization controls how dbt compiles and executes your SQL model.

### View

```sql
-- models/staging/stg_orders.sql
-- Materialization: view (default for staging)

-- A VIEW means: dbt creates a SQL view in the database.
-- The SQL runs EVERY TIME someone queries the view.
-- No data is stored - just a saved query.

SELECT
    order_id,
    customer_id,
    status,
    CAST(order_date AS DATE) AS order_date,
    CAST(total_amount AS DECIMAL(12,2)) AS total_amount_usd
FROM {{ source('raw', 'orders') }}
WHERE order_id IS NOT NULL
```

**When to use views:**
- Staging models (light cleaning, no aggregation)
- When data freshness is critical (view always shows latest data)
- When the query is fast (no expensive aggregations)
- When storage cost matters (views use no storage)

**When NOT to use views:**
- Heavy aggregations or complex joins (re-computed every query = slow)
- Downstream models that query this model frequently

### Table

```sql
-- models/marts/fct_orders.sql
-- config block tells dbt how to materialize THIS specific model
{{ config(materialized='table') }}

-- A TABLE means: dbt runs the SQL and stores the result as a physical table.
-- Queries against this model are fast (reading from pre-computed data).
-- The table is REPLACED entirely on each dbt run.

SELECT
    o.order_id,
    o.order_date,
    o.status,
    o.total_amount_usd,
    c.customer_name,
    c.country_code,
    c.customer_segment,
    p.product_name,
    p.category
FROM {{ ref('stg_orders') }} o         -- ref() creates a dependency
LEFT JOIN {{ ref('dim_customers') }} c USING (customer_id)
LEFT JOIN {{ ref('stg_order_items') }} oi USING (order_id)
LEFT JOIN {{ ref('stg_products') }} p USING (product_id)
```

**When to use tables:**
- Final/mart models that are queried frequently by BI tools
- When query performance matters (analysts shouldn't wait for complex joins)
- Data that is expensive to compute (heavy aggregations)

### Incremental

```sql
-- models/marts/fct_daily_revenue.sql
{{ config(
    materialized='incremental',
    unique_key='revenue_date',  -- Which column identifies unique rows
    on_schema_change='fail'     -- If schema changes, fail loudly
) }}

SELECT
    DATE_TRUNC('day', order_date) AS revenue_date,
    country_code,
    product_category,
    COUNT(DISTINCT order_id) AS num_orders,
    SUM(total_amount_usd) AS total_revenue
FROM {{ ref('fct_orders') }}
WHERE status = 'delivered'

{% if is_incremental() %}
  -- This block only runs on INCREMENTAL runs (not full refresh)
  -- On full refresh (dbt run --full-refresh), this WHERE clause is omitted
  -- and all data is reprocessed
  AND order_date >= (
      -- Look back 3 days to handle late-arriving data
      SELECT MAX(revenue_date) - INTERVAL '3 days'
      FROM {{ this }}           -- {{ this }} = reference to the current model's table
  )
{% endif %}

GROUP BY 1, 2, 3
```

**How incremental models work:**
```
First run (full build):
  1. Run the full SQL (no is_incremental() filter)
  2. CREATE TABLE fct_daily_revenue AS <result>

Subsequent runs:
  1. Run the SQL WITH the is_incremental() filter
     (only fetches rows since MAX(revenue_date) - 3 days)
  2. MERGE the new rows into fct_daily_revenue
     using unique_key to match existing rows

Result: Only process new data, not recompute everything!
```

**When to use incremental:**
- Large fact tables (millions+ rows) where full rebuild is slow
- Time-series data where you only add new time periods
- When you need near-real-time freshness without full rebuilds

### Ephemeral

Ephemeral models are not materialized at all - they become CTEs (Common Table Expressions) in the SQL of models that reference them.

```sql
-- models/staging/base_orders.sql
{{ config(materialized='ephemeral') }}

-- This doesn't create any table or view.
-- It becomes a CTE in any model that refs() it.
SELECT * FROM {{ source('raw', 'orders') }}
WHERE _deleted = false  -- Filter soft-deleted records
```

**When to use ephemeral:**
- Simple intermediate steps that don't need to be queried directly
- When you want to organize SQL without creating extra tables/views
- Rarely - views are usually better for reusability

### Materialization Comparison

```
+------------+-----------+--------+----------+---------------+
| Material.  | Storage   | Speed  | Freshness| Use When      |
+------------+-----------+--------+----------+---------------+
| view       | None      | Slow   | Always   | Staging,      |
|            |           | (runs  | fresh    | simple cleans |
|            |           | at     |          |               |
|            |           | query  |          |               |
|            |           | time)  |          |               |
+------------+-----------+--------+----------+---------------+
| table      | Yes       | Fast   | Stale    | Mart models,  |
|            |           |        | until    | BI tables     |
|            |           |        | next run |               |
+------------+-----------+--------+----------+---------------+
| incremental| Yes       | Fast   | Stale    | Large fact    |
|            | (grows    |        | until    | tables, daily |
|            | over time)|        | next run | aggregations  |
+------------+-----------+--------+----------+---------------+
| ephemeral  | None      | Same   | Same as  | Intermediate  |
|            | (CTE)     | as     | parent   | steps, code   |
|            |           | parent |          | organization  |
+------------+-----------+--------+----------+---------------+
```

---

## 4. dbt DAG and ref()

### The ref() Function

`ref()` is dbt's most important function. It:
1. Creates a **dependency** between models (builds the DAG)
2. Handles **environment-specific** table names automatically
3. Enables **lineage tracking** in dbt docs

```sql
-- Without ref() (BAD - tightly coupled to environment):
SELECT * FROM analytics.stg_orders        -- Hardcoded schema!
                                            -- Breaks in dev environment

-- With ref() (GOOD - environment-agnostic):
SELECT * FROM {{ ref('stg_orders') }}     -- dbt resolves to correct schema
                                            -- dev: dbt_dev.stg_orders
                                            -- prod: analytics.stg_orders
```

### How dbt Builds the DAG

dbt parses all SQL files, finds all `ref()` calls, and builds a DAG:

```
dbt DAG for our e-commerce project:

raw.orders          raw.customers         raw.products
     |                    |                    |
     v                    v                    v
stg_orders          stg_customers         stg_products
     |                    |                    |
     +--------------------+--------------------+
                          |
                    fct_orders
                          |
               +----------+----------+
               |                     |
       daily_revenue          customer_metrics
```

dbt runs models in topological order (respecting dependencies).
Models with no dependencies run first and in parallel.

### source() Function

`source()` is like `ref()` but for raw source tables (not dbt models):

```yaml
# models/staging/schema.yml
sources:
  - name: raw          # Source name
    schema: raw        # Database schema where raw tables live
    tables:
      - name: orders   # Table name
        description: "Raw orders table from the application database"
        loaded_at_field: _loaded_at  # For freshness checks
        freshness:
          warn_after: {count: 12, period: hour}
          error_after: {count: 24, period: hour}
      - name: customers
      - name: products
```

```sql
-- Now you can reference source tables with source()
SELECT * FROM {{ source('raw', 'orders') }}

-- dbt compiles this to:
SELECT * FROM raw.orders
```

---

## 5. Testing in dbt

### Generic Tests (Built-in)

dbt has four built-in generic tests that cover 90% of data quality needs:

```yaml
# models/marts/schema.yml
models:
  - name: fct_orders
    description: "One row per order. This is the primary fact table."
    columns:
      - name: order_id
        description: "Unique identifier for each order"
        tests:
          - unique                  # No duplicate order_ids
          - not_null                # No NULL order_ids
          
      - name: status
        description: "Order lifecycle status"
        tests:
          - not_null
          - accepted_values:        # Only these values are allowed
              values: ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
              
      - name: customer_id
        description: "Foreign key to dim_customers"
        tests:
          - not_null
          - relationships:          # Every customer_id must exist in dim_customers
              to: ref('dim_customers')
              field: customer_id
              
      - name: total_amount_usd
        description: "Order total in USD"
        tests:
          - not_null
```

### Custom Singular Tests

For business rules that don't fit into generic tests:

```sql
-- tests/assert_order_total_matches_items.sql
-- This test PASSES if it returns 0 rows
-- It FAILS if it returns any rows (those are the failing records)

-- Business rule: order total should match sum of line items (within $0.01)
SELECT
    o.order_id,
    o.total_amount_usd AS order_total,
    SUM(oi.line_total) AS items_total,
    ABS(o.total_amount_usd - SUM(oi.line_total)) AS discrepancy
FROM {{ ref('fct_orders') }} o
JOIN {{ ref('fct_order_items') }} oi USING (order_id)
GROUP BY 1, 2
HAVING ABS(o.total_amount_usd - SUM(oi.line_total)) > 0.01
```

```sql
-- tests/assert_no_future_orders.sql
-- Orders should not be dated in the future
SELECT order_id, order_date
FROM {{ ref('fct_orders') }}
WHERE order_date > CURRENT_DATE
```

### Running Tests

```bash
# Run all tests
dbt test

# Test a specific model
dbt test --select fct_orders

# Run only specific test types
dbt test --select "test_type:generic"
dbt test --select "test_type:singular"

# Run tests with verbose output
dbt test --select fct_orders -v
```

---

## 6. Incremental Models In Depth

### The is_incremental() Macro

```sql
{{ config(
    materialized='incremental',
    unique_key='order_id',
    strategy='merge',           -- How to handle conflicts (merge vs delete+insert)
    on_schema_change='sync_all_columns'  -- Auto-add new columns
) }}

SELECT
    order_id,
    customer_id,
    status,
    order_date,
    total_amount_usd,
    CURRENT_TIMESTAMP AS updated_at
FROM {{ ref('stg_orders') }}

{% if is_incremental() %}
-- Only when running incrementally (not --full-refresh)
-- The this keyword references the current state of this model's table
WHERE order_date >= (SELECT MAX(order_date) - INTERVAL '3 days' FROM {{ this }})
{% endif %}
```

### Incremental Strategies

**merge** (default for most warehouses):
```
- For each row in the new batch:
  - If unique_key exists in target: UPDATE the existing row
  - If unique_key doesn't exist: INSERT new row
- Most flexible, handles updates to historical records
```

**append** (for immutable data only):
```
- Just INSERT all new rows
- Fastest, but ONLY correct when records are never updated
- Example: log records that are never modified
```

**delete+insert** (for Postgres/Redshift):
```
- DELETE all rows in the target where unique_key matches new batch
- INSERT all rows from new batch
- Works well when you're replacing partitions
```

---

## 7. dbt Documentation and Data Contracts

### Why Documentation Matters

Documentation in dbt serves as a **data contract** between:
- Data engineers who build the pipelines
- Data analysts who use the data
- BI developers who build dashboards
- Future you (debugging at 2am in 6 months)

Without documentation:
- Analysts don't know which table to use
- Column meanings are ambiguous ("is amount in cents or dollars?")
- Nobody knows what "stg_" vs "fct_" vs "dim_" mean
- Schema changes break things silently

### Writing Good Documentation

```yaml
# models/marts/schema.yml
models:
  - name: fct_orders
    description: >
      Fact table containing one row per order. Joins orders with customer
      and product dimensions to provide a complete analytical view.
      
      IMPORTANT: This table only includes NON-CANCELLED orders. Use
      fct_orders_all for cancelled order analysis.
      
      Grain: One row per order (not per order line item).
      Updated: Daily at 3:00 AM UTC via Airflow.
    
    meta:
      owner: "data-engineering@company.com"
      sla: "3:00 AM UTC daily"
      primary_use_cases:
        - "Revenue reporting"
        - "Customer cohort analysis"
    
    columns:
      - name: order_id
        description: "Unique identifier for the order. Maps to orders.id in the application database."
        
      - name: total_amount_usd
        description: >
          Total order value in US Dollars (converted from local currency using
          the exchange rate at time of order). Includes all line items,
          shipping, and taxes. EXCLUDES cancelled line items.

# Generate and serve docs:
# dbt docs generate
# dbt docs serve
```

---

## 8. Jinja Templating in dbt

Jinja is a Python templating language that dbt embeds in SQL. It enables:
- Dynamic SQL generation
- Reusable macros (like functions in SQL)
- Environment-specific behavior
- Loops and conditionals in SQL

### Common Jinja Patterns

```sql
-- Variables
{{ var('start_date', '2024-01-01') }}    -- with default
{{ env_var('DBT_SCHEMA') }}              -- from environment

-- Conditionals
{% if target.name == 'prod' %}
    WHERE is_test_account = false        -- Exclude test accounts in prod
{% endif %}

-- Loops (useful for generating repetitive SQL)
{% set payment_methods = ['credit_card', 'debit_card', 'bank_transfer', 'paypal'] %}
SELECT
    order_id,
    {% for pm in payment_methods %}
    SUM(CASE WHEN payment_method = '{{ pm }}' THEN amount ELSE 0 END) AS {{ pm }}_amount
    {{ "," if not loop.last }}
    {% endfor %}
FROM {{ ref('stg_payments') }}
GROUP BY order_id
```

### Custom Macros

```sql
-- macros/cents_to_dollars.sql
{% macro cents_to_dollars(column_name) %}
    ({{ column_name }} / 100.0)::DECIMAL(10,2)
{% endmacro %}

-- macros/safe_divide.sql
-- Avoid division by zero errors
{% macro safe_divide(numerator, denominator) %}
    CASE WHEN {{ denominator }} = 0 THEN NULL
    ELSE {{ numerator }} / {{ denominator }}::FLOAT
    END
{% endmacro %}

-- Usage in a model:
SELECT
    order_id,
    {{ cents_to_dollars('amount_cents') }} AS amount_usd,
    {{ safe_divide('num_orders', 'num_customers') }} AS orders_per_customer
FROM {{ ref('stg_orders') }}
```

---

## Lab Overview

The `labs/` directory contains a complete dbt project for the e-commerce use case.

Prerequisites:
```bash
pip install dbt-postgres

# Ensure Postgres is running (reuse Module 1's docker-compose)
# From 01_foundations/labs:
# docker-compose up -d

# Run the dbt project
cd labs/
dbt debug          # Test connection
dbt seed           # Load CSV seeds
dbt run            # Build all models
dbt test           # Run all tests
dbt docs generate  # Generate documentation
dbt docs serve     # View docs in browser
```
