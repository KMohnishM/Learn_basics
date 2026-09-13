-- =========================================================================
-- LAB: Designing a Star Schema for an E-Commerce Company
-- =========================================================================

-- 1. DIMENSION TABLES (The context)

-- Date Dimension (Standard practice: pre-populate this for 20 years)
CREATE TABLE dim_date (
    date_id INT PRIMARY KEY, -- e.g. 20231024
    full_date DATE,
    year INT,
    quarter INT,
    month INT,
    month_name VARCHAR(20),
    day_of_week INT,
    day_name VARCHAR(20),
    is_weekend BOOLEAN
);

CREATE TABLE dim_product (
    product_sk SERIAL PRIMARY KEY,    -- Surrogate Key
    product_id VARCHAR(50),           -- Natural Business Key
    product_name VARCHAR(100),
    category VARCHAR(50),
    brand VARCHAR(50),
    supplier VARCHAR(100),
    current_price DECIMAL(10,2)
);

CREATE TABLE dim_customer (
    customer_sk SERIAL PRIMARY KEY,   -- Surrogate Key
    customer_id VARCHAR(50),          -- Natural Business Key
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100),
    city VARCHAR(50),
    state VARCHAR(50),
    country VARCHAR(50)
);

-- 2. FACT TABLE (The metrics)

CREATE TABLE fact_sales (
    -- Foreign Keys to Dimensions
    date_id INT REFERENCES dim_date(date_id),
    product_sk INT REFERENCES dim_product(product_sk),
    customer_sk INT REFERENCES dim_customer(customer_sk),
    
    -- Degenerate Dimension (Has no dimension table, just the transaction ID)
    transaction_id VARCHAR(100),
    
    -- Metrics / Facts
    quantity_sold INT,
    unit_price DECIMAL(10,2),
    discount_amount DECIMAL(10,2),
    total_amount DECIMAL(10,2)
);

-- =========================================================================
-- ANALYTICAL QUERIES (Why we build the Star Schema)
-- =========================================================================

-- Example: Find the total revenue by Product Category and Quarter for 2023.
-- Notice how simple and readable this query is compared to a heavily normalized OLTP schema!
/*
SELECT 
    d.quarter,
    p.category,
    SUM(f.total_amount) as total_revenue
FROM fact_sales f
JOIN dim_date d ON f.date_id = d.date_id
JOIN dim_product p ON f.product_sk = p.product_sk
WHERE d.year = 2023
GROUP BY 
    d.quarter,
    p.category
ORDER BY 
    d.quarter, 
    total_revenue DESC;
*/
