-- 1. Redesigned Table for SCD Type 2
CREATE TABLE dim_customer_scd2 (
    customer_sk SERIAL PRIMARY KEY,   -- The Surrogate Key used in the Fact table
    customer_id VARCHAR(50),          -- The Natural Business Key
    
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    state VARCHAR(50),
    
    -- The 3 SCD Type 2 Tracking Columns
    valid_from DATE NOT NULL,
    valid_to DATE,                    -- NULL or '9999-12-31' indicates it hasn't expired
    is_current BOOLEAN NOT NULL       -- For fast filtering
);

-- 2. Alice signs up in New York on Jan 1st.
INSERT INTO dim_customer_scd2 
(customer_id, first_name, last_name, state, valid_from, valid_to, is_current)
VALUES 
('CUST_123', 'Alice', 'Smith', 'New York', '2023-01-01', '9999-12-31', TRUE);
-- (Assume this got customer_sk = 1)


-- 3. Alice moves to California on May 1st. 
-- We must do this in a transaction to ensure data integrity!
BEGIN;

-- Step A: Expire the old record
UPDATE dim_customer_scd2
SET 
    valid_to = '2023-04-30',
    is_current = FALSE
WHERE 
    customer_id = 'CUST_123' AND is_current = TRUE;

-- Step B: Insert the new record with a new surrogate key
INSERT INTO dim_customer_scd2 
(customer_id, first_name, last_name, state, valid_from, valid_to, is_current)
VALUES 
('CUST_123', 'Alice', 'Smith', 'California', '2023-05-01', '9999-12-31', TRUE);
-- (This gets customer_sk = 2)

COMMIT;

-- Now, any Fact records from Jan-April will link to customer_sk = 1.
-- Any Fact records from May onwards will link to customer_sk = 2.
-- If we query revenue by state for Q1, Alice's revenue correctly attributes to New York!
