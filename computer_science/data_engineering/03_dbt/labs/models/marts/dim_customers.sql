-- models/marts/dim_customers.sql
-- ================================
-- Customer dimension table (SCD Type 1 - no history tracking)
--
-- PURPOSE:
--   Dimension tables provide descriptive context for fact tables.
--   The customer dimension answers: "Who is this customer?"
--
-- SCD TYPE 1: Simply overwrites changes.
--   If a customer changes their email, the old email is lost.
--   For full history, use SCD Type 2 (see exercise).
--
-- GRAIN: One row per unique customer

{{ config(materialized='table') }}

WITH customers AS (
    SELECT * FROM {{ ref('stg_customers') }}
),

-- Calculate order statistics per customer
-- This demonstrates the "wide" dimension approach: embed frequently-needed
-- metrics into the dimension so BI tools don't need extra joins
order_stats AS (
    SELECT
        customer_id,
        COUNT(*)                   AS total_orders,
        SUM(amount_usd)            AS lifetime_value_usd,
        AVG(amount_usd)            AS avg_order_value_usd,
        MIN(ordered_at)            AS first_order_at,
        MAX(ordered_at)            AS last_order_at,
        COUNT(DISTINCT order_date) AS distinct_order_days
    FROM {{ ref('stg_orders') }}
    WHERE status != 'cancelled'
    GROUP BY customer_id
),

final AS (
    SELECT
        -- PRIMARY KEY
        c.customer_id,
        
        -- PERSONAL ATTRIBUTES
        c.first_name,
        c.last_name,
        c.full_name,
        c.email,
        
        -- LOCATION ATTRIBUTES
        c.country_code,
        c.country_name,
        
        -- ACCOUNT ATTRIBUTES
        c.customer_since,
        c.days_as_customer,
        
        -- CUSTOMER SEGMENTATION (derived from order behavior)
        CASE
            WHEN os.total_orders IS NULL THEN 'new'           -- Never ordered
            WHEN os.total_orders = 1     THEN 'one_time'      -- Ordered once
            WHEN os.total_orders < 5     THEN 'occasional'    -- 2-4 orders
            WHEN os.total_orders < 20    THEN 'regular'       -- 5-19 orders
            ELSE 'vip'                                         -- 20+ orders
        END AS customer_segment,
        
        -- CUSTOMER VALUE TIER (based on lifetime spend)
        CASE
            WHEN COALESCE(os.lifetime_value_usd, 0) = 0       THEN 'no_spend'
            WHEN os.lifetime_value_usd < 100                   THEN 'low_value'
            WHEN os.lifetime_value_usd < 500                   THEN 'mid_value'
            WHEN os.lifetime_value_usd < 2000                  THEN 'high_value'
            ELSE 'premium'
        END AS customer_value_tier,
        
        -- ORDER STATISTICS (embedded for convenience)
        COALESCE(os.total_orders, 0)               AS total_orders,
        COALESCE(os.lifetime_value_usd, 0)         AS lifetime_value_usd,
        os.avg_order_value_usd,
        os.first_order_at,
        os.last_order_at,
        
        -- RECENCY: Days since last order (for churn analysis)
        CASE
            WHEN os.last_order_at IS NULL THEN NULL
            ELSE EXTRACT(DAY FROM CURRENT_TIMESTAMP - os.last_order_at)::INTEGER
        END AS days_since_last_order,
        
        -- Is customer considered "churned"? (no order in 90+ days)
        CASE
            WHEN os.last_order_at IS NULL THEN FALSE
            WHEN CURRENT_TIMESTAMP - os.last_order_at > INTERVAL '90 days' THEN TRUE
            ELSE FALSE
        END AS is_churned
    
    FROM customers c
    LEFT JOIN order_stats os ON c.customer_id = os.customer_id
)

SELECT * FROM final
