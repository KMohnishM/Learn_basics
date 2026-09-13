"""
load.py
=======
Module 2 Lab: Load Step - Idempotent Upsert to PostgreSQL

PURPOSE:
    Demonstrates the Load phase of an ETL pipeline.
    Takes clean records from the transform step and loads them into
    PostgreSQL using idempotent UPSERT operations.

KEY CONCEPT - IDEMPOTENCY:
    The load step uses INSERT ... ON CONFLICT DO UPDATE (UPSERT).
    This means:
    - If a record already exists (same record_id): UPDATE the existing row
    - If a record doesn't exist: INSERT a new row
    
    Running the load step 10 times produces the SAME database state as
    running it once. This is critical for reliability in production pipelines.

PERFORMANCE TECHNIQUES:
    - execute_batch(): Batches multiple SQL statements into fewer round-trips
    - COPY (for very large loads): Even faster than batch INSERT
    - Connection pooling: Reuse connections instead of creating new ones

USAGE:
    python load.py
"""

import logging
import psycopg2
import psycopg2.extras
from datetime import datetime
from typing import List, Dict, Tuple

# ============================================================================
# LOGGING SETUP
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("etl.load")

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
DB_CONFIG = {
    "host": "localhost",
    "port": 5433,               # Port 5433 to avoid conflict with Module 1's Postgres
    "database": "weather_db",
    "user": "etluser",
    "password": "etlpassword",
}

# How many records to insert per database round-trip
# Larger = fewer round-trips but more memory per batch
# 500-1000 is a good balance for most use cases
BATCH_SIZE = 500


# ============================================================================
# SCHEMA CREATION
# ============================================================================

def create_schema(conn):
    """
    Creates the weather data schema in PostgreSQL.
    
    Schema design decisions:
    - record_id is the PRIMARY KEY (business key = city + timestamp)
    - Using PRIMARY KEY on record_id enables the ON CONFLICT (record_id) DO UPDATE
      syntax for upserts - PostgreSQL requires a unique constraint for this
    - TIMESTAMPTZ stores timezone-aware timestamps (UTC)
    - SMALLINT for small ranges (hour, weather_code) saves storage
    - VARCHAR with length limits prevents unbounded string storage
    """
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS weather_measurements (
                -- Natural/business key used for upsert
                record_id           VARCHAR(100) PRIMARY KEY,
                
                -- Location
                city                VARCHAR(100) NOT NULL,
                country             CHAR(2) NOT NULL,
                latitude            DECIMAL(8, 4),
                longitude           DECIMAL(8, 4),
                
                -- Time
                measurement_time_utc TIMESTAMP NOT NULL,
                measurement_date    DATE NOT NULL,
                measurement_hour    SMALLINT NOT NULL CHECK (measurement_hour BETWEEN 0 AND 23),
                
                -- Weather measurements
                temperature_c       DECIMAL(5, 2),
                apparent_temp_c     DECIMAL(5, 2),
                humidity_pct        DECIMAL(5, 2),
                precipitation_mm    DECIMAL(6, 2),
                wind_speed_kmh      DECIMAL(6, 2),
                wind_direction_deg  DECIMAL(5, 2),
                weather_code        SMALLINT,
                
                -- Derived/enriched fields
                temp_category       VARCHAR(20),
                precip_category     VARCHAR(20),
                wind_category       VARCHAR(20),
                is_nice_day         BOOLEAN,
                weather_description VARCHAR(100),
                
                -- Pipeline metadata
                extracted_at        VARCHAR(30),  -- ISO timestamp from source
                transformed_at      VARCHAR(30),
                loaded_at           TIMESTAMP NOT NULL DEFAULT NOW()
            );
        """)
        
        # Indexes for common query patterns
        # Index on (city, measurement_date) for "show me weather for London this week"
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_weather_city_date 
            ON weather_measurements (city, measurement_date DESC);
        """)
        
        # Index on (country, measurement_date) for country-level aggregations
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_weather_country_date 
            ON weather_measurements (country, measurement_date DESC);
        """)
        
        # Index on (measurement_date) for date-range scans
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_weather_date 
            ON weather_measurements (measurement_date DESC);
        """)
        
    conn.commit()
    logger.info("Schema created (or already exists)")


# ============================================================================
# UPSERT LOGIC
# ============================================================================

def build_upsert_sql() -> str:
    """
    Builds the UPSERT SQL statement.
    
    PostgreSQL UPSERT syntax:
        INSERT INTO table (...) VALUES (...)
        ON CONFLICT (unique_column)
        DO UPDATE SET col1 = EXCLUDED.col1, ...
    
    'EXCLUDED' refers to the row that WOULD have been inserted (the new values).
    
    WHY NOT JUST INSERT?
    If we re-run the pipeline for the same date, a plain INSERT would
    fail with a unique constraint violation (or insert duplicates if no
    unique constraint exists). UPSERT handles both cases gracefully.
    
    NOTE: We do NOT update loaded_at on conflict - that records when
    the record was FIRST loaded, not when it was last updated.
    We DO update a hypothetical 'last_updated_at' if we had one.
    """
    return """
        INSERT INTO weather_measurements (
            record_id, city, country, latitude, longitude,
            measurement_time_utc, measurement_date, measurement_hour,
            temperature_c, apparent_temp_c, humidity_pct,
            precipitation_mm, wind_speed_kmh, wind_direction_deg,
            weather_code, temp_category, precip_category, wind_category,
            is_nice_day, weather_description, extracted_at, transformed_at
        ) VALUES (
            %(record_id)s, %(city)s, %(country)s, %(latitude)s, %(longitude)s,
            %(measurement_time_utc)s, %(measurement_date)s, %(measurement_hour)s,
            %(temperature_c)s, %(apparent_temp_c)s, %(humidity_pct)s,
            %(precipitation_mm)s, %(wind_speed_kmh)s, %(wind_direction_deg)s,
            %(weather_code)s, %(temp_category)s, %(precip_category)s, %(wind_category)s,
            %(is_nice_day)s, %(weather_description)s, %(extracted_at)s, %(transformed_at)s
        )
        ON CONFLICT (record_id) DO UPDATE SET
            -- Update all measurement fields when re-loading
            -- This handles the case where the API corrects historical data
            temperature_c       = EXCLUDED.temperature_c,
            apparent_temp_c     = EXCLUDED.apparent_temp_c,
            humidity_pct        = EXCLUDED.humidity_pct,
            precipitation_mm    = EXCLUDED.precipitation_mm,
            wind_speed_kmh      = EXCLUDED.wind_speed_kmh,
            wind_direction_deg  = EXCLUDED.wind_direction_deg,
            weather_code        = EXCLUDED.weather_code,
            temp_category       = EXCLUDED.temp_category,
            precip_category     = EXCLUDED.precip_category,
            wind_category       = EXCLUDED.wind_category,
            is_nice_day         = EXCLUDED.is_nice_day,
            weather_description = EXCLUDED.weather_description,
            transformed_at      = EXCLUDED.transformed_at;
            -- NOTE: loaded_at is NOT updated - it keeps the original load time
    """


def load(clean_records: List[Dict]) -> Tuple[int, int, int]:
    """
    Loads clean records into PostgreSQL using idempotent UPSERT.
    
    Args:
        clean_records: List of cleaned records from the transform step
    
    Returns:
        Tuple of (total_records, inserted, updated) counts
        Note: PostgreSQL doesn't easily distinguish insert vs update in batch,
        so we check row count before and after.
    
    Raises:
        psycopg2.Error: If database connection or insert fails
    """
    if not clean_records:
        logger.warning("No records to load")
        return 0, 0, 0
    
    logger.info("="*50)
    logger.info("LOAD STEP: Upserting weather data to PostgreSQL")
    logger.info("="*50)
    logger.info(f"Records to load: {len(clean_records)}")
    
    conn = psycopg2.connect(**DB_CONFIG)
    
    try:
        # Ensure schema exists
        create_schema(conn)
        
        # Get count before load (to calculate inserted vs updated)
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM weather_measurements;")
            rows_before = cur.fetchone()[0]
        
        upsert_sql = build_upsert_sql()
        
        # Process in batches for memory efficiency and better error isolation
        total_processed = 0
        total_batches = (len(clean_records) + BATCH_SIZE - 1) // BATCH_SIZE
        
        for batch_num, start_idx in enumerate(range(0, len(clean_records), BATCH_SIZE), 1):
            batch = clean_records[start_idx:start_idx + BATCH_SIZE]
            
            try:
                with conn.cursor() as cur:
                    # execute_batch sends multiple SQL statements in one network call
                    # This is much faster than calling execute() in a Python loop
                    # page_size=BATCH_SIZE means: send BATCH_SIZE statements at once
                    psycopg2.extras.execute_batch(
                        cur,
                        upsert_sql,
                        batch,
                        page_size=BATCH_SIZE
                    )
                
                # Commit after each batch
                # This limits data loss to at most one batch if something fails
                conn.commit()
                total_processed += len(batch)
                
                logger.info(f"  Batch {batch_num}/{total_batches}: "
                           f"{len(batch)} records processed ({total_processed} total)")
                
            except psycopg2.Error as e:
                # Rollback the failed batch only, not previous successful batches
                conn.rollback()
                logger.error(f"  Batch {batch_num} failed: {e}")
                raise
        
        # Get count after load to determine inserts vs updates
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM weather_measurements;")
            rows_after = cur.fetchone()[0]
        
        new_rows = rows_after - rows_before
        updated_rows = len(clean_records) - new_rows
        
        logger.info("")
        logger.info("--- Load Summary ---")
        logger.info(f"  Total processed: {total_processed}")
        logger.info(f"  New rows inserted: {new_rows}")
        logger.info(f"  Existing rows updated: {updated_rows}")
        logger.info(f"  Total rows in table: {rows_after}")
        logger.info("="*50)
        logger.info("Load COMPLETE")
        logger.info("="*50)
        
        return total_processed, new_rows, updated_rows
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Load failed: {e}")
        raise
    
    finally:
        conn.close()


# ============================================================================
# VERIFICATION QUERIES
# ============================================================================

def verify_load():
    """
    Runs verification queries to confirm data was loaded correctly.
    These are basic sanity checks - in production, use dbt tests or
    Great Expectations for comprehensive data quality validation.
    """
    logger.info("\n--- Load Verification ---")
    
    conn = psycopg2.connect(**DB_CONFIG)
    
    try:
        with conn.cursor() as cur:
            # Total row count
            cur.execute("SELECT COUNT(*) FROM weather_measurements;")
            total = cur.fetchone()[0]
            logger.info(f"  Total records: {total}")
            
            # Records per city
            cur.execute("""
                SELECT city, country, COUNT(*) as records, 
                       MIN(measurement_date) as earliest,
                       MAX(measurement_date) as latest
                FROM weather_measurements
                GROUP BY city, country
                ORDER BY city;
            """)
            rows = cur.fetchall()
            logger.info(f"\n  Records per city:")
            for row in rows:
                logger.info(f"    {row[0]:<15} ({row[1]}): {row[2]} records | {row[3]} to {row[4]}")
            
            # Sample query: average temperature by city (last 3 days)
            cur.execute("""
                SELECT 
                    city,
                    ROUND(AVG(temperature_c)::numeric, 1) as avg_temp_c,
                    ROUND(AVG(humidity_pct)::numeric, 1) as avg_humidity,
                    SUM(CASE WHEN precipitation_mm > 0 THEN 1 ELSE 0 END) as rainy_hours
                FROM weather_measurements
                WHERE measurement_date >= CURRENT_DATE - INTERVAL '3 days'
                  AND temperature_c IS NOT NULL
                GROUP BY city
                ORDER BY avg_temp_c DESC;
            """)
            rows = cur.fetchall()
            logger.info(f"\n  Last 3 days weather summary:")
            logger.info(f"  {'City':<15} {'Avg Temp°C':>10} {'Avg Humidity%':>14} {'Rainy Hours':>12}")
            logger.info("  " + "-"*55)
            for row in rows:
                logger.info(f"  {row[0]:<15} {str(row[1]):>10} {str(row[2]):>14} {row[3]:>12}")
    
    finally:
        conn.close()


# ============================================================================
# STANDALONE EXECUTION
# ============================================================================

if __name__ == "__main__":
    from extract import extract
    from transform import transform
    
    print("Running full ETL to test load step...")
    raw = extract()
    clean, quality_report = transform(raw)
    total, inserted, updated = load(clean)
    verify_load()
