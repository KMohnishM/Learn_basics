-- solution/fct_daily_revenue.sql
-- =================================
-- Module 3 Exercise Solution: Incremental Daily Revenue Model
--
-- This model demonstrates:
-- 1. Incremental materialization strategy
-- 2. Surrogate key generation for unique_key
-- 3. Lookback window for late-arriving data
-- 4. Multiple dimension joins in a mart model

{{
    config(
        materialized='incremental',
        unique_key='surrogate_key',
        on_schema_change='sync_all_columns',
        -- For Postgres, incremental uses delete+insert by default
        -- This deletes rows matching unique_key then re-inserts
        indexes=[
            {'columns': ['revenue_date', 'country_code'], 'type': 'btree'},
        ]
    )
}}

WITH orders AS (
    SELECT * FROM {{ ref('fct_orders') }}

    -- INCREMENTAL FILTER:
    -- is_incremental() returns TRUE only on incremental runs (not --full-refresh)
    -- On --full-refresh, this entire WHERE block is omitted
    {% if is_incremental() %}
    WHERE order_date >= (
        -- Look back 3 days from the latest date already in the table
        -- This catches:
        -- 1. Late-arriving orders (ordered yesterday, but data loaded today)
        -- 2. Order status changes (order shipped -> delivered changes revenue bucket)
        -- 3. Data corrections applied to recent records
        SELECT MAX(revenue_date) - INTERVAL '3 days'
        FROM {{ this }}  -- {{ this }} = the current state of fct_daily_revenue table
    )
    {% endif %}
),

countries AS (
    SELECT * FROM {{ ref('country_codes') }}
),

-- We need product category from order items
-- For this simplified example, we'll use the order size category as the "category"
-- In a real model, you'd join to stg_order_items and then to stg_products
aggregated AS (
    SELECT
        o.order_date                    AS revenue_date,
        o.country_code,
        o.country_name,
        COALESCE(c.region, 'Unknown')   AS country_region,
        
        -- Using order_size_category as a proxy for product_category in this simplified model
        -- In production: JOIN to order_items and products tables
        o.order_size_category           AS product_category,
        
        COUNT(DISTINCT o.order_id)      AS num_orders,
        SUM(o.order_total_usd)          AS total_revenue_usd,
        AVG(o.order_total_usd)          AS avg_order_value_usd,
        MAX(o.order_total_usd)          AS max_order_value_usd,
        MIN(o.order_total_usd)          AS min_order_value_usd
    
    FROM orders o
    LEFT JOIN countries c ON o.country_code = c.code
    
    GROUP BY 1, 2, 3, 4, 5
),

final AS (
    SELECT
        -- SURROGATE KEY: Composite key from three business key columns
        -- MD5 produces a 32-character hex string - always unique for distinct inputs
        -- COALESCE handles nulls (which would make MD5 null otherwise)
        MD5(
            COALESCE(revenue_date::TEXT, 'null') || '|' ||
            COALESCE(country_code, 'null') || '|' ||
            COALESCE(product_category, 'null')
        )                               AS surrogate_key,
        
        revenue_date,
        country_code,
        country_name,
        country_region,
        product_category,
        num_orders,
        ROUND(total_revenue_usd::NUMERIC, 2)  AS total_revenue_usd,
        ROUND(avg_order_value_usd::NUMERIC, 2) AS avg_order_value_usd,
        ROUND(max_order_value_usd::NUMERIC, 2) AS max_order_value_usd,
        ROUND(min_order_value_usd::NUMERIC, 2) AS min_order_value_usd,
        
        -- Revenue per order (same as avg_order_value but clearer name)
        ROUND(total_revenue_usd / NULLIF(num_orders, 0), 2) AS revenue_per_order_usd,
        
        -- Pipeline metadata
        CURRENT_TIMESTAMP               AS dbt_updated_at
    
    FROM aggregated
)

SELECT * FROM final
