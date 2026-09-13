# Module 7: The Data Warehouse and Dimensional Modeling

A Data Warehouse is a centralized repository of integrated data from one or more disparate sources. 
Unlike an OLTP database (which is optimized for fast, single-row inserts and updates), a Data Warehouse (OLAP) is optimized for scanning millions of rows and performing complex aggregations (SUM, AVG, GROUP BY).

## 1. Dimensional Modeling (The Star Schema)
Created by Ralph Kimball, the Star Schema is the gold standard for designing data warehouses. It consists of two types of tables:

### Fact Tables
- The "center" of the star.
- Records measurements or metrics of a specific event (e.g., a sale, a click, a temperature reading).
- Contains numerical data (`sales_amount`, `discount`) and foreign keys to Dimension tables (`product_id`, `customer_id`, `date_id`).
- Typically very narrow (few columns) but billions of rows.
- **Types**: Transaction (one row per event), Periodic Snapshot (one row per time period, e.g., daily account balance), Accumulating Snapshot (one row per workflow, e.g., order lifecycle).

### Dimension Tables
- The "points" of the star.
- Provides context (the who, what, where, when) to the facts.
- e.g., `dim_customer` contains `customer_name`, `email`, `city`, `signup_date`.
- Typically very wide (many columns) but relatively few rows (thousands or millions, not billions).
- *Crucially*, dimension tables use a **Surrogate Key** (an auto-incrementing integer) as the Primary Key, rather than the natural business key. This handles Slowly Changing Dimensions.

## 2. Slowly Changing Dimensions (SCD)
What happens if a customer moves from "New York" to "California"? 
If you just update their row in `dim_customer` (SCD Type 1), you rewrite history. All their past sales in the Fact table will suddenly look like they happened in California!

- **SCD Type 1**: Overwrite the old value. Use when you don't care about history (e.g., fixing a typo in a name).
- **SCD Type 2**: Add a *new row* for the customer. The old row gets `is_current = FALSE` and `valid_to = '2023-10-01'`. The new row gets a new surrogate key, `is_current = TRUE`, and `valid_from = '2023-10-01'`. New sales link to the new surrogate key. Old sales link to the old surrogate key. History is perfectly preserved!
- **SCD Type 3**: Add a new column (e.g., `current_city` and `previous_city`). Rarely used.

## 3. Modern Cloud Data Warehouses
The Modern Data Stack shifted from on-premise appliances (Teradata) to the cloud (Snowflake, BigQuery, Redshift).
- **Separation of Compute and Storage**: In Snowflake/BigQuery, data is stored in cheap object storage (like S3/GCS). When you run a query, a temporary compute cluster is spun up to read the data, process it, and shut down. This means you can scale storage infinitely without paying for compute you aren't using.
- **Columnar Storage**: Data is stored by column, not by row. If you query `SUM(sales_amount)`, the database only reads the `sales_amount` file off the disk, ignoring the 50 other columns in the table. This is why OLAP is so fast for analytics.

---
## Next Steps
Go to `labs/` to see exactly how to write the SQL for a robust Star Schema!
