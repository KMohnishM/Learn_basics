# Module 3 Exercise: Incremental dbt Model

## Objective

Write an **incremental dbt model** called `fct_daily_revenue` that:
1. Calculates daily revenue aggregated by country and product category
2. Only processes new orders on each run (incremental strategy)
3. Handles late-arriving data correctly (lookback window)
4. Has proper tests to ensure data quality

## Background: Why Incremental Models?

The `fct_orders` model is a `table` materialization - it rebuilds from scratch on every `dbt run`. For a table with 10 million rows, this might take 10 minutes.

An **incremental model** solves this:
- First run: processes all historical data (builds the full table)
- Subsequent runs: only processes rows that are new/changed
- Net result: after the first run, each daily run might take 30 seconds instead of 10 minutes

## Requirements

### Part 1: Create the Incremental Model

Create `models/marts/fct_daily_revenue.sql` that:

1. **Grain**: One row per (date, country_code, product_category) combination

2. **Metrics to calculate**:
   - `revenue_date`: The date (truncated to day)
   - `country_code`: ISO 3166-1 alpha-2
   - `country_name`: Full country name
   - `country_region`: Geographic region (from country_codes seed)
   - `product_category`: Product category name
   - `num_orders`: Count of distinct orders
   - `total_revenue_usd`: Sum of order totals
   - `avg_order_value_usd`: Average order value
   - `max_order_value_usd`: Maximum single order value

3. **Incremental configuration**:
   - `unique_key`: A composite key of (revenue_date, country_code, product_category)
   - Since Postgres doesn't support multi-column unique keys in ON CONFLICT directly,
     use a surrogate key: `MD5(revenue_date::text || country_code || product_category)`
   - Lookback window: re-process the last 3 days on each incremental run
     (to handle late-arriving orders and order status updates)

4. **Incremental filter** using `is_incremental()`:
   ```sql
   {% if is_incremental() %}
   WHERE order_date >= (SELECT MAX(revenue_date) - INTERVAL '3 days' FROM {{ this }})
   {% endif %}
   ```

### Part 2: Add dbt Tests

Add these tests to `models/marts/schema.yml`:

1. **unique** test on the surrogate key
2. **not_null** tests on: surrogate_key, revenue_date, country_code, product_category, total_revenue_usd
3. **Custom singular test**: `tests/assert_revenue_non_negative.sql`
   - Fails if any row has `total_revenue_usd < 0`
4. **Custom singular test**: `tests/assert_no_future_revenue.sql`
   - Fails if any row has `revenue_date > CURRENT_DATE`

### Part 3: Test the Incremental Behavior

Write a shell script `test_incremental.sh` (or PowerShell `test_incremental.ps1`) that:

1. Runs a full refresh to build the model from scratch:
   ```bash
   dbt run --select fct_daily_revenue --full-refresh
   ```

2. Counts the rows:
   ```bash
   psql -c "SELECT COUNT(*) FROM dbt_dev.fct_daily_revenue;"
   ```

3. Runs incrementally (simulating next day's run):
   ```bash
   dbt run --select fct_daily_revenue
   ```

4. Counts rows again and verifies count didn't change significantly

5. Runs tests to verify data quality:
   ```bash
   dbt test --select fct_daily_revenue
   ```

### Part 4: Analyze the Compiled SQL

After running dbt, look at the compiled SQL in `target/compiled/`:

```bash
cat target/compiled/ecommerce_dbt/models/marts/fct_daily_revenue.sql
```

Write a comment in your model explaining:
- What SQL dbt generates for the incremental run vs full refresh
- How the MERGE/INSERT logic works in the compiled output

## Expected File Structure

```
models/marts/
├── fct_orders.sql              (existing)
├── dim_customers.sql           (existing)
├── fct_daily_revenue.sql       (NEW - your solution)
└── schema.yml                  (updated with new model tests)

tests/
├── assert_revenue_non_negative.sql   (NEW)
└── assert_no_future_revenue.sql      (NEW)
```

## Hint: Surrogate Key Pattern

```sql
-- When you need a unique key from multiple columns:
MD5(
    COALESCE(revenue_date::TEXT, '') || '|' ||
    COALESCE(country_code, '') || '|' ||
    COALESCE(product_category, '')
) AS surrogate_key
```

## Grading Criteria

- [ ] `fct_daily_revenue.sql` exists and queries successfully
- [ ] `is_incremental()` block correctly limits rows on incremental runs
- [ ] Surrogate key is unique (unique test passes)
- [ ] All not_null tests pass
- [ ] Both custom singular tests are written and pass
- [ ] `--full-refresh` builds the complete table
- [ ] Incremental run is significantly faster than full refresh
- [ ] Code has clear SQL comments explaining the incremental logic
