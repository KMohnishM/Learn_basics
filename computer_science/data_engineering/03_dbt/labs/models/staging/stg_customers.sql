-- models/staging/stg_customers.sql
-- ==================================
-- Staging model: Clean and standardize raw customers (users) data.

WITH source AS (
    SELECT * FROM {{ source('raw', 'users') }}
),

renamed AS (
    SELECT
        user_id::INTEGER            AS customer_id,
        
        -- Name normalization: INITCAP capitalizes first letter of each word
        -- TRIM removes leading/trailing whitespace
        TRIM(INITCAP(first_name))   AS first_name,
        TRIM(INITCAP(last_name))    AS last_name,
        
        -- Concatenated name for convenience
        TRIM(INITCAP(first_name)) || ' ' || TRIM(INITCAP(last_name)) AS full_name,
        
        -- Email: always lowercase for consistency
        LOWER(TRIM(email))          AS email,
        
        -- Country codes: always uppercase (ISO 3166-1 alpha-2)
        UPPER(TRIM(country_code))   AS country_code,
        TRIM(country_name)          AS country_name,
        
        created_at::TIMESTAMP       AS customer_since,
        
        -- Derived field: customer tenure in days
        -- DATE_PART returns the number (EPOCH = seconds since 1970)
        EXTRACT(DAY FROM (CURRENT_TIMESTAMP - created_at::TIMESTAMP)) AS days_as_customer
    
    FROM source
),

validated AS (
    SELECT *
    FROM renamed
    WHERE
        customer_id IS NOT NULL
        AND email IS NOT NULL
        AND email LIKE '%@%'    -- Basic email format check
        AND LENGTH(country_code) = 2  -- Must be valid 2-letter ISO code
)

SELECT * FROM validated
