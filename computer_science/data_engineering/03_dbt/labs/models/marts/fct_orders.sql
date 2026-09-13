-- models/marts/fct_orders.sql
-- ============================
-- Fact table: One row per order with all relevant dimensions joined in.
--
-- PURPOSE:
--   Fact tables are the primary analytical tables. They contain:
--   - Foreign keys to dimension tables
--   - Measurable facts/metrics (amounts, counts, durations)
--   - Degenerate dimensions (things like status that don't need a separate table)
--
-- GRAIN: One row per order (not per order item)
--
-- MATERIALIZATION: table (configured in dbt_project.yml for marts/)
-- This model is queried frequently by BI tools, so it must be pre-computed.
--
-- DEPENDENCIES:
--   ref('stg_orders')     -> orders must be staged first
--   ref('dim_customers')  -> customer dimension must exist
--   ref('stg_products') is in order_items (join handled separately)

{{ config(materialized='table') }}

WITH orders AS (
    -- Reference staging model using ref()
    -- dbt knows it must build stg_orders BEFORE this model
    SELECT * FROM {{ ref('stg_orders') }}
),

customers AS (
    -- Reference dimension table
    SELECT * FROM {{ ref('dim_customers') }}
),

-- Join country information from our seed file
countries AS (
    SELECT * FROM {{ ref('country_codes') }}
),

final AS (
    SELECT
        -- SURROGATE KEY: Use order_id as the primary key
        -- In dimensional modeling, fact tables often have a surrogate key
        o.order_id,
        
        -- DIMENSION FOREIGN KEYS (these link to dimension tables)
        o.customer_id,
        c.country_code,
        
        -- DEGENERATE DIMENSIONS: Low-cardinality attributes that don't need
        -- their own dimension table (status has only 5 values)
        o.status,
        
        -- DATE DIMENSIONS: Break out date components for easy filtering
        o.ordered_at,
        o.ordered_at::DATE                      AS order_date,
        DATE_TRUNC('week', o.ordered_at)::DATE  AS order_week,
        DATE_TRUNC('month', o.ordered_at)::DATE AS order_month,
        DATE_TRUNC('year', o.ordered_at)::DATE  AS order_year,
        EXTRACT(DOW FROM o.ordered_at)          AS day_of_week,  -- 0=Sunday, 6=Saturday
        EXTRACT(HOUR FROM o.ordered_at)         AS hour_of_day,
        
        -- FACTS (the measurable metrics)
        o.amount_usd                            AS order_total_usd,
        
        -- CUSTOMER DIMENSION ATTRIBUTES (denormalized into fact for convenience)
        c.full_name                             AS customer_name,
        c.country_name,
        
        -- REGION from seed file
        co.region                               AS country_region,
        
        -- DERIVED METRICS
        -- Is this a weekend order?
        CASE WHEN EXTRACT(DOW FROM o.ordered_at) IN (0, 6) THEN TRUE ELSE FALSE END AS is_weekend_order,
        
        -- Order size categorization
        CASE
            WHEN o.amount_usd < 25  THEN 'small'
            WHEN o.amount_usd < 100 THEN 'medium'
            WHEN o.amount_usd < 500 THEN 'large'
            ELSE 'enterprise'
        END AS order_size_category,
        
        -- Customer lifetime purchase flag
        c.customer_since,
        c.days_as_customer
    
    FROM orders o
    
    -- LEFT JOIN: Keep all orders even if customer data is missing
    -- (though NOT NULL tests on customer_id should catch these)
    LEFT JOIN customers c ON o.customer_id = c.customer_id
    LEFT JOIN countries co ON c.country_code = co.code
    
    -- Only include non-cancelled orders in the main fact table
    -- For cancelled order analysis, create a separate fct_cancelled_orders model
    WHERE o.status != 'cancelled'
)

SELECT * FROM final
