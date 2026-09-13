"""
transform.py
============
Module 2 Lab: Transform Step - Clean, Validate, and Normalize Weather Data

PURPOSE:
    Demonstrates the Transform phase of an ETL pipeline.
    Takes raw, messy data from the extract step and produces clean,
    validated, normalized records ready for loading into the database.

TRANSFORMATION STEPS IN THIS MODULE:
    1. Type casting (strings to proper types)
    2. Null handling (decide: drop, impute, or flag)
    3. Deduplication (remove exact duplicate records)
    4. Value normalization (standardize units, formats)
    5. Data validation (check business rules)
    6. Feature derivation (compute new useful fields from existing ones)
    7. Data quality reporting

LEARNING OBJECTIVES:
    - Understand the "clean code" principle for transformations
    - See how to build reusable validation functions
    - Understand when to DROP vs IMPUTE vs FLAG null values
    - Learn how to generate data quality reports
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# ============================================================================
# LOGGING SETUP
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("etl.transform")


# ============================================================================
# WMO WEATHER CODE MAPPING
# ============================================================================
# The Open-Meteo API returns WMO (World Meteorological Organization) codes.
# We convert these to human-readable descriptions.
# Full table: https://open-meteo.com/en/docs#weathervariables

WMO_WEATHER_CODES = {
    0:  "Clear sky",
    1:  "Mainly clear",
    2:  "Partly cloudy",
    3:  "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

# ============================================================================
# VALIDATION RULES
# ============================================================================
# Define acceptable ranges for weather measurements.
# Values outside these ranges are physically impossible or sensor errors.

VALIDATION_RULES = {
    "temperature_c": {
        "min": -80.0,    # Coldest recorded: -89.2°C (Antarctica)
        "max": 60.0,     # Hottest recorded: 56.7°C (Death Valley)
        "nullable": True, # Some hours may have missing readings
    },
    "humidity_pct": {
        "min": 0.0,
        "max": 100.0,
        "nullable": True,
    },
    "precipitation_mm": {
        "min": 0.0,       # Can't have negative precipitation
        "max": 500.0,     # Highest hourly rainfall ever: ~100mm, using 500 as max
        "nullable": True,
    },
    "wind_speed_kmh": {
        "min": 0.0,
        "max": 400.0,     # Highest recorded gust: 408 km/h
        "nullable": True,
    },
    "wind_direction_deg": {
        "min": 0.0,
        "max": 360.0,     # 0-360 degrees
        "nullable": True,
    },
}


# ============================================================================
# TRANSFORM FUNCTIONS
# ============================================================================

def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """
    Parse the API's timestamp string into a Python datetime object.
    
    The API returns timestamps like "2024-01-15T12:00" (ISO 8601 format).
    We parse these for proper datetime handling in the database.
    
    Args:
        timestamp_str: Timestamp string from the API
    
    Returns:
        datetime object (UTC), or None if parsing fails
    """
    if not timestamp_str:
        return None
    
    # Try multiple formats to handle API variations
    formats = [
        "%Y-%m-%dT%H:%M",      # "2024-01-15T12:00" (Open-Meteo format)
        "%Y-%m-%dT%H:%M:%S",   # "2024-01-15T12:00:00"
        "%Y-%m-%d %H:%M:%S",   # "2024-01-15 12:00:00"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue
    
    logger.warning(f"Could not parse timestamp: {timestamp_str}")
    return None


def validate_numeric_range(value: Optional[float], field_name: str, record_id: str) -> Tuple[Optional[float], List[str]]:
    """
    Validates a numeric value against its defined acceptable range.
    
    Returns the value (or None if invalid) and a list of validation messages.
    
    THREE OPTIONS for handling invalid values:
    1. REJECT: Mark as None, flag the record, exclude from analysis
    2. CLAMP: Set to min/max boundary (use when close to boundary)
    3. DROP: Remove the entire record (use when the record is fundamentally unusable)
    
    We use option 1 (REJECT) here - preserve the record but nullify the bad field.
    This preserves other valid fields in the record.
    
    Args:
        value: The numeric value to validate (can be None)
        field_name: Name of the field (for logging/error messages)
        record_id: Identifier for the record (for logging)
    
    Returns:
        Tuple of (validated_value, [list of validation messages])
    """
    messages = []
    
    if value is None:
        # Null values are acceptable if the field is nullable
        if not VALIDATION_RULES.get(field_name, {}).get("nullable", True):
            messages.append(f"REQUIRED field {field_name} is null for record {record_id}")
        return None, messages
    
    if field_name not in VALIDATION_RULES:
        return value, messages  # No rules defined, pass through
    
    rules = VALIDATION_RULES[field_name]
    min_val = rules.get("min")
    max_val = rules.get("max")
    
    if min_val is not None and value < min_val:
        messages.append(f"[INVALID] {field_name}={value} below minimum {min_val} for {record_id}")
        return None, messages  # Nullify the invalid value
    
    if max_val is not None and value > max_val:
        messages.append(f"[INVALID] {field_name}={value} above maximum {max_val} for {record_id}")
        return None, messages  # Nullify the invalid value
    
    return value, messages


def derive_features(record: Dict) -> Dict:
    """
    Derives new computed features from existing fields.
    
    Feature derivation adds analytical value by computing fields that:
    - Are useful for analysis but not provided by the source
    - Require combining multiple source fields
    - Categorize continuous values into discrete buckets
    
    IMPORTANT: Derived features are computed from ALREADY VALIDATED fields.
    If source fields are null, derived fields should also be null.
    
    Args:
        record: A validated, cleaned weather record
    
    Returns:
        The same record with additional derived fields added
    """
    # Derive heat index (apparent temperature category)
    temp = record.get("temperature_c")
    humidity = record.get("humidity_pct")
    
    # Temperature category (useful for grouping in analytics)
    if temp is not None:
        if temp < -10:
            record["temp_category"] = "extreme_cold"
        elif temp < 0:
            record["temp_category"] = "freezing"
        elif temp < 10:
            record["temp_category"] = "cold"
        elif temp < 20:
            record["temp_category"] = "mild"
        elif temp < 30:
            record["temp_category"] = "warm"
        elif temp < 40:
            record["temp_category"] = "hot"
        else:
            record["temp_category"] = "extreme_heat"
    else:
        record["temp_category"] = None
    
    # Precipitation category
    precip = record.get("precipitation_mm")
    if precip is not None:
        if precip == 0:
            record["precip_category"] = "none"
        elif precip < 1:
            record["precip_category"] = "trace"
        elif precip < 5:
            record["precip_category"] = "light"
        elif precip < 15:
            record["precip_category"] = "moderate"
        else:
            record["precip_category"] = "heavy"
    else:
        record["precip_category"] = None
    
    # Wind category (Beaufort scale approximation)
    wind = record.get("wind_speed_kmh")
    if wind is not None:
        if wind < 1:
            record["wind_category"] = "calm"
        elif wind < 20:
            record["wind_category"] = "light_breeze"
        elif wind < 40:
            record["wind_category"] = "moderate_breeze"
        elif wind < 62:
            record["wind_category"] = "strong_breeze"
        elif wind < 88:
            record["wind_category"] = "near_gale"
        else:
            record["wind_category"] = "storm"
    else:
        record["wind_category"] = None
    
    # Is it a "nice day"? (simple composite metric)
    # Nice day: temp 15-25°C, precipitation < 1mm, wind < 30 km/h
    if all(v is not None for v in [temp, precip, wind]):
        record["is_nice_day"] = (
            15 <= temp <= 25 and
            precip < 1.0 and
            wind < 30
        )
    else:
        record["is_nice_day"] = None
    
    # Human-readable weather description from WMO code
    weather_code = record.get("weather_code")
    if weather_code is not None:
        record["weather_description"] = WMO_WEATHER_CODES.get(
            int(weather_code), f"Unknown code {weather_code}"
        )
    else:
        record["weather_description"] = None
    
    return record


def create_record_id(record: Dict) -> str:
    """
    Creates a natural/business key for deduplication.
    
    The business key uniquely identifies a weather measurement:
    - City (location)
    - Timestamp (time of measurement)
    
    This composite key is used for:
    1. Deduplication within a batch (remove exact duplicates)
    2. UPSERT logic in the database (update if exists, insert if new)
    
    IMPORTANT: The record_id must be deterministic - the same record
    always produces the same ID regardless of when the pipeline runs.
    This enables idempotent loading (upsert on conflict).
    """
    city = record.get("city", "unknown").replace(" ", "_").lower()
    timestamp = record.get("timestamp_utc", "").replace("T", "_").replace(":", "")
    return f"{city}_{timestamp}"


def transform(raw_records: List[Dict]) -> Tuple[List[Dict], Dict]:
    """
    Main transform function: clean, validate, and enrich weather records.
    
    PIPELINE:
    Raw records
        -> Type casting (strings to proper Python types)
        -> Timestamp parsing (string to datetime)
        -> Numeric validation (range checks)
        -> Deduplication (remove exact duplicates)
        -> Feature derivation (add computed columns)
    
    Returns:
        Tuple of:
        - List of cleaned, enriched records
        - Data quality report dict
    """
    logger.info("="*50)
    logger.info("TRANSFORM STEP: Cleaning and validating weather data")
    logger.info("="*50)
    logger.info(f"Input: {len(raw_records)} raw records")
    
    cleaned_records = []
    
    # Tracking metrics for quality report
    quality_metrics = {
        "input_count": len(raw_records),
        "output_count": 0,
        "dropped_count": 0,
        "validation_warnings": 0,
        "null_values_by_field": {},
        "invalid_timestamps": 0,
        "duplicates_removed": 0,
        "cities_processed": set(),
    }
    
    seen_record_ids = set()  # For deduplication
    
    for raw in raw_records:
        # ------------------------------------------------------------------
        # STEP 1: Create a deterministic record ID (for deduplication + upsert)
        # ------------------------------------------------------------------
        record_id = create_record_id(raw)
        
        # ------------------------------------------------------------------
        # STEP 2: Deduplication
        # If we've already seen this record ID in this batch, skip it.
        # (Can happen if the pipeline is re-run or the API returns duplicates)
        # ------------------------------------------------------------------
        if record_id in seen_record_ids:
            quality_metrics["duplicates_removed"] += 1
            logger.debug(f"  Duplicate skipped: {record_id}")
            continue
        seen_record_ids.add(record_id)
        
        # ------------------------------------------------------------------
        # STEP 3: Parse timestamp
        # ------------------------------------------------------------------
        parsed_timestamp = parse_timestamp(raw.get("timestamp_utc"))
        if parsed_timestamp is None:
            logger.warning(f"  Dropping record with invalid timestamp: {raw.get('timestamp_utc')}")
            quality_metrics["invalid_timestamps"] += 1
            quality_metrics["dropped_count"] += 1
            continue
        
        # ------------------------------------------------------------------
        # STEP 4: Validate and clean numeric fields
        # ------------------------------------------------------------------
        validation_warnings = []
        
        # Validate each numeric field
        temp, msgs = validate_numeric_range(raw.get("temperature_c"), "temperature_c", record_id)
        validation_warnings.extend(msgs)
        
        humidity, msgs = validate_numeric_range(raw.get("humidity_pct"), "humidity_pct", record_id)
        validation_warnings.extend(msgs)
        
        precip, msgs = validate_numeric_range(raw.get("precipitation_mm"), "precipitation_mm", record_id)
        validation_warnings.extend(msgs)
        
        wind_speed, msgs = validate_numeric_range(raw.get("wind_speed_kmh"), "wind_speed_kmh", record_id)
        validation_warnings.extend(msgs)
        
        wind_dir, msgs = validate_numeric_range(raw.get("wind_direction_deg"), "wind_direction_deg", record_id)
        validation_warnings.extend(msgs)
        
        if validation_warnings:
            quality_metrics["validation_warnings"] += len(validation_warnings)
            for msg in validation_warnings:
                logger.debug(msg)
        
        # ------------------------------------------------------------------
        # STEP 5: Build the clean record
        # ------------------------------------------------------------------
        clean_record = {
            # Identity
            "record_id": record_id,  # Business key for upsert
            
            # Location
            "city": str(raw.get("city", "")).strip(),
            "country": str(raw.get("country", "")).strip().upper(),  # Normalize to uppercase
            "latitude": float(raw["latitude"]) if raw.get("latitude") is not None else None,
            "longitude": float(raw["longitude"]) if raw.get("longitude") is not None else None,
            
            # Time
            "measurement_time_utc": parsed_timestamp,
            "measurement_date": parsed_timestamp.date(),   # Useful for date-based partitioning
            "measurement_hour": parsed_timestamp.hour,      # Useful for time-of-day analysis
            
            # Weather measurements (validated)
            "temperature_c": temp,
            "apparent_temp_c": raw.get("apparent_temp_c"),  # Pass through (less critical)
            "humidity_pct": humidity,
            "precipitation_mm": precip,
            "wind_speed_kmh": wind_speed,
            "wind_direction_deg": wind_dir,
            "weather_code": int(raw["weather_code"]) if raw.get("weather_code") is not None else None,
            
            # Pipeline metadata
            "extracted_at": raw.get("extracted_at"),
            "transformed_at": datetime.utcnow().isoformat(),
        }
        
        # ------------------------------------------------------------------
        # STEP 6: Derive features (adds computed columns to clean_record)
        # ------------------------------------------------------------------
        clean_record = derive_features(clean_record)
        
        # Track null values per field (for quality report)
        for field, value in clean_record.items():
            if value is None:
                quality_metrics["null_values_by_field"][field] = \
                    quality_metrics["null_values_by_field"].get(field, 0) + 1
        
        quality_metrics["cities_processed"].add(clean_record["city"])
        cleaned_records.append(clean_record)
    
    # Finalize quality metrics
    quality_metrics["output_count"] = len(cleaned_records)
    quality_metrics["cities_processed"] = list(quality_metrics["cities_processed"])
    quality_metrics["pass_rate_pct"] = (
        len(cleaned_records) / quality_metrics["input_count"] * 100
        if quality_metrics["input_count"] > 0 else 0
    )
    
    # Log quality report
    logger.info("")
    logger.info("--- Transform Quality Report ---")
    logger.info(f"  Input records:         {quality_metrics['input_count']}")
    logger.info(f"  Output records:        {quality_metrics['output_count']}")
    logger.info(f"  Dropped:               {quality_metrics['dropped_count']}")
    logger.info(f"  Duplicates removed:    {quality_metrics['duplicates_removed']}")
    logger.info(f"  Validation warnings:   {quality_metrics['validation_warnings']}")
    logger.info(f"  Pass rate:             {quality_metrics['pass_rate_pct']:.1f}%")
    logger.info(f"  Cities processed:      {len(quality_metrics['cities_processed'])}")
    
    if quality_metrics["null_values_by_field"]:
        logger.info("  Null counts by field:")
        for field, count in sorted(quality_metrics["null_values_by_field"].items()):
            pct = count / quality_metrics["output_count"] * 100 if quality_metrics["output_count"] > 0 else 0
            logger.info(f"    {field}: {count} ({pct:.1f}%)")
    
    logger.info("="*50)
    logger.info(f"Transform complete: {len(cleaned_records)} clean records")
    logger.info("="*50)
    
    return cleaned_records, quality_metrics


# ============================================================================
# STANDALONE EXECUTION (for testing)
# ============================================================================

if __name__ == "__main__":
    # Import extract to test the full extract->transform flow
    from extract import extract
    
    print("Running extract step...")
    raw_records = extract()
    
    print(f"\nRunning transform on {len(raw_records)} records...")
    clean_records, quality_report = transform(raw_records)
    
    if clean_records:
        print(f"\nSample clean record:")
        import json
        # datetime objects aren't JSON-serializable, convert to strings
        sample = {k: str(v) if hasattr(v, 'isoformat') else v 
                  for k, v in clean_records[0].items()}
        print(json.dumps(sample, indent=2))
