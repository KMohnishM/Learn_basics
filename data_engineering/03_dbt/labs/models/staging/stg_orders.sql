-- models/staging/stg_orders.sql
-- ==============================
-- Staging model: Clean and standardize raw orders data.
--
-- PURPOSE:
--   This is the FIRST transformation layer. Staging models should:
--   1. Select from source (raw) tables only
--   2. Rename columns to consistent naming conventions
--   3. Cast data types appropriately
--   4. Apply basic filtering (remove test records, null PKs)
--   5. NOT join to other tables (that's for mart models)
--   6. NOT aggregate data (that's for mart models)
--
-- NAMING CONVENTION:
--   stg_ prefix = staging layer
--   Source: raw.orders (the table as it comes from the application DB)
--   Output: One row per order (same grain as source)
--
-- MATERIALIZATION:
--   Configured as 'view' in dbt_project.yml for staging models.
--   Views are: cheap (no storage), always fresh, good for simple cleaning.
--
-- DEPENDENCIES:
--   source('raw', 'orders') -> no dbt model dependencies

WITH source AS (
    -- Reference the raw source table using source()
    -- source() tells dbt this is an external source (not a dbt model)
    -- This enables source freshness checks and documentation
    SELECT * FROM {{ source('raw', 'orders') }}
),

renamed AS (
    SELECT
        -- PRIMARY KEY
        -- Cast to ensure it's an integer (source may have it as text)
        order_id::INTEGER           AS order_id,
        
        -- FOREIGN KEYS
        user_id::INTEGER            AS customer_id,     -- Rename for clarity
        
        -- DATES
        -- Always cast dates explicitly - don't rely on implicit casting
        -- TIMESTAMPTZ stores timezone info; cast to UTC for consistency
        order_date::TIMESTAMP       AS ordered_at,
        
        -- ENUMERATIONS
        -- LOWER() to normalize (avoid 'PENDING' vs 'pending' issues)
        LOWER(TRIM(status))         AS status,
        
        -- MONETARY AMOUNTS
        -- DECIMAL(12,2): 12 digits total, 2 after decimal point
        -- Suitable for amounts up to $9,999,999,999.99
        total_amount::DECIMAL(12,2) AS amount_usd,
        
        -- AUDIT COLUMNS
        -- Keep these for debugging data lineage issues
        created_at::TIMESTAMP       AS created_at
    
    FROM source
),

-- FILTERING: Remove records that cannot be processed downstream
-- We do minimal filtering in staging - just remove truly invalid records
validated AS (
    SELECT *
    FROM renamed
    WHERE
        -- Remove records with no primary key (unparseable)
        order_id IS NOT NULL
        -- Remove orders with impossible amounts
        AND amount_usd >= 0
        -- Remove test/dummy records (common in dev environments)
        AND status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled')
)

SELECT * FROM validated
