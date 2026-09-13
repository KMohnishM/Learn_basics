"""
extract.py
==========
Module 2 Lab: Extract Step - Fetch Weather Data from Open-Meteo API

PURPOSE:
    Demonstrates the Extract phase of an ETL pipeline using a real,
    free public API (Open-Meteo). No API key required.
    
    Open-Meteo provides historical and forecast weather data for any
    location in the world, making it ideal for learning data pipelines.

API DOCUMENTATION:
    https://open-meteo.com/en/docs
    
    The API is free, open-source, and returns JSON. Perfect for learning.

LEARNING OBJECTIVES:
    - How to call a REST API with Python's `requests` library
    - How to handle API errors gracefully (rate limiting, network errors)
    - How to add retry logic with exponential backoff
    - How to structure raw data for downstream processing
    - Why we preserve raw data before transforming it

USAGE:
    python extract.py
    
    Returns: List of weather records (raw, as-is from API)
"""

import requests          # HTTP client library
import time              # For sleep() in retry logic
import logging           # Structured logging
import json              # For pretty-printing API responses
from datetime import date, timedelta  # For date arithmetic
from typing import Optional, Dict, Any, List

# ============================================================================
# LOGGING SETUP
# ============================================================================
# Use structured logging throughout - makes it easier to parse logs in
# production monitoring systems (ELK stack, CloudWatch, etc.)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("etl.extract")


# ============================================================================
# CONFIGURATION
# ============================================================================
# Open-Meteo API documentation: https://open-meteo.com/en/docs
# We query historical weather data for multiple cities.

API_BASE_URL = "https://api.open-meteo.com/v1/forecast"

# List of cities to extract weather data for.
# Each city is a location we want weather readings for.
# We use lat/lon because that's what the API needs.
LOCATIONS = [
    {"city": "London",        "country": "GB", "latitude": 51.5085, "longitude": -0.1257},
    {"city": "New York",      "country": "US", "latitude": 40.7143, "longitude": -74.0060},
    {"city": "Tokyo",         "country": "JP", "latitude": 35.6895, "longitude": 139.6917},
    {"city": "Sydney",        "country": "AU", "latitude": -33.8688, "longitude": 151.2093},
    {"city": "Mumbai",        "country": "IN", "latitude": 19.0760, "longitude": 72.8777},
    {"city": "Sao Paulo",     "country": "BR", "latitude": -23.5489, "longitude": -46.6388},
    {"city": "Berlin",        "country": "DE", "latitude": 52.5244, "longitude": 13.4105},
    {"city": "Cairo",         "country": "EG", "latitude": 30.0626, "longitude": 31.2497},
    {"city": "Toronto",       "country": "CA", "latitude": 43.7001, "longitude": -79.4163},
    {"city": "Singapore",     "country": "SG", "latitude": 1.2897,  "longitude": 103.8501},
]

# Weather variables to request from the API
# These are the hourly measurements we want for each location
HOURLY_VARIABLES = [
    "temperature_2m",           # Air temperature at 2 meters height (°C)
    "relative_humidity_2m",     # Relative humidity at 2m (%)
    "precipitation",            # Total precipitation (rain + snow) in mm
    "wind_speed_10m",           # Wind speed at 10m height (km/h)
    "wind_direction_10m",       # Wind direction at 10m (degrees, 0=N, 90=E)
    "apparent_temperature",     # "Feels like" temperature (°C)
    "weather_code",             # WMO weather condition code
]

# How many days of data to fetch (last N days)
DAYS_TO_FETCH = 7

# API retry configuration
MAX_RETRIES = 3          # Number of retry attempts before giving up
INITIAL_BACKOFF_SEC = 1  # Starting wait time for exponential backoff
TIMEOUT_SEC = 30         # HTTP request timeout in seconds


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def build_api_params(location: Dict[str, Any], start_date: str, end_date: str) -> Dict:
    """
    Builds the query parameters for the Open-Meteo API request.
    
    The API accepts parameters as URL query strings:
    ?latitude=51.5&longitude=-0.1&hourly=temperature_2m,...
    
    We use `requests` to handle URL encoding automatically.
    
    Args:
        location: Dict with latitude, longitude, city, country
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
    
    Returns:
        Dict of query parameters for the API request
    """
    return {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "hourly": ",".join(HOURLY_VARIABLES),  # Comma-separated list of variables
        "start_date": start_date,
        "end_date": end_date,
        "timezone": "UTC",            # Always use UTC to avoid DST confusion
        "wind_speed_unit": "kmh",     # Standardize to km/h
        "temperature_unit": "celsius", # Standardize to Celsius
    }


def fetch_with_retry(url: str, params: Dict, max_retries: int = MAX_RETRIES) -> Optional[Dict]:
    """
    Fetches data from a URL with exponential backoff retry logic.
    
    WHY RETRY LOGIC IS IMPORTANT:
    APIs occasionally fail for transient reasons:
    - Network packet loss (temporary)
    - Server-side rate limiting (429 Too Many Requests)
    - Momentary server overload (503 Service Unavailable)
    
    Without retry logic, a single network hiccup fails the entire pipeline.
    With retry + exponential backoff, we handle transient failures gracefully.
    
    EXPONENTIAL BACKOFF:
    Wait progressively longer between retries to avoid overwhelming
    a struggling service:
    - Attempt 1: fails immediately
    - Wait 1 second, Attempt 2: fails
    - Wait 2 seconds, Attempt 3: fails  
    - Wait 4 seconds, Attempt 4: fails
    - Give up and raise exception
    
    In production, add jitter (randomness) to avoid "thundering herd" where
    many clients all retry at exactly the same time.
    
    Args:
        url: The API endpoint URL
        params: Query parameters to include in the request
        max_retries: Maximum number of retry attempts
    
    Returns:
        Parsed JSON response dict, or None if all retries failed
    """
    backoff = INITIAL_BACKOFF_SEC  # Start with 1 second wait
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.debug(f"  API request attempt {attempt}/{max_retries}: {url}")
            
            # Make the HTTP GET request
            # timeout=30 means: give up if no response in 30 seconds
            response = requests.get(url, params=params, timeout=TIMEOUT_SEC)
            
            # Raise an exception for HTTP error status codes (4xx, 5xx)
            # This converts HTTP errors into Python exceptions we can catch
            response.raise_for_status()
            
            # Parse and return the JSON response
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else "unknown"
            
            # 429 = Too Many Requests (rate limiting)
            # 503 = Service Unavailable
            # These are retryable. 404, 400, 401 are NOT retryable.
            if status_code in (429, 503) and attempt < max_retries:
                wait_time = backoff * (2 ** (attempt - 1))  # Exponential: 1, 2, 4, 8...
                logger.warning(f"  HTTP {status_code}: Rate limited. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                logger.error(f"  HTTP error {status_code}: {e}")
                raise
        
        except requests.exceptions.ConnectionError as e:
            # Network is down, DNS resolution failed, etc.
            if attempt < max_retries:
                wait_time = backoff * (2 ** (attempt - 1))
                logger.warning(f"  Connection error (attempt {attempt}). Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"  All {max_retries} connection attempts failed: {e}")
                raise
        
        except requests.exceptions.Timeout:
            if attempt < max_retries:
                logger.warning(f"  Request timed out (attempt {attempt}). Retrying...")
                time.sleep(backoff)
            else:
                logger.error(f"  All {max_retries} attempts timed out")
                raise
    
    return None


def flatten_hourly_data(api_response: Dict, location: Dict) -> List[Dict]:
    """
    Transforms the API's nested JSON structure into a flat list of records.
    
    The Open-Meteo API returns data in a columnar format (arrays per variable):
    {
        "hourly": {
            "time": ["2024-01-01T00:00", "2024-01-01T01:00", ...],
            "temperature_2m": [5.2, 4.8, 4.5, ...],
            "precipitation": [0.0, 0.1, 0.2, ...]
        }
    }
    
    We convert this to row-oriented format (one dict per time point):
    [
        {"time": "2024-01-01T00:00", "temperature_2m": 5.2, "precipitation": 0.0},
        {"time": "2024-01-01T01:00", "temperature_2m": 4.8, "precipitation": 0.1},
        ...
    ]
    
    We also add location metadata to each row so we know where the reading came from.
    
    WHY PRESERVE RAW DATA:
    We add all fields from the API response without filtering or transforming.
    The transform step will handle cleaning and validation.
    This way, if we later need a field we originally discarded, we can
    reprocess from the raw data.
    
    Args:
        api_response: Raw JSON response from the API
        location: Location metadata (city, country, lat, lon)
    
    Returns:
        List of flat dictionaries, one per hourly reading
    """
    # Extract the hourly data section
    hourly = api_response.get("hourly", {})
    
    if not hourly:
        logger.warning(f"  No hourly data in API response for {location['city']}")
        return []
    
    # The "time" array gives us timestamps for each data point
    timestamps = hourly.get("time", [])
    
    if not timestamps:
        return []
    
    records = []
    
    # Zip all variable arrays together to create row-oriented records
    for i, timestamp in enumerate(timestamps):
        record = {
            # Location metadata - added to every record
            "city": location["city"],
            "country": location["country"],
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            
            # Temporal data
            "timestamp_utc": timestamp,
            
            # Weather measurements - use .get() with None default for safety
            # Some hours may have missing data (None) which is normal
            "temperature_c": hourly.get("temperature_2m", [None])[i] if i < len(hourly.get("temperature_2m", [])) else None,
            "apparent_temp_c": hourly.get("apparent_temperature", [None])[i] if i < len(hourly.get("apparent_temperature", [])) else None,
            "humidity_pct": hourly.get("relative_humidity_2m", [None])[i] if i < len(hourly.get("relative_humidity_2m", [])) else None,
            "precipitation_mm": hourly.get("precipitation", [None])[i] if i < len(hourly.get("precipitation", [])) else None,
            "wind_speed_kmh": hourly.get("wind_speed_10m", [None])[i] if i < len(hourly.get("wind_speed_10m", [])) else None,
            "wind_direction_deg": hourly.get("wind_direction_10m", [None])[i] if i < len(hourly.get("wind_direction_10m", [])) else None,
            "weather_code": hourly.get("weather_code", [None])[i] if i < len(hourly.get("weather_code", [])) else None,
            
            # API metadata - always capture when and how data was fetched
            "api_url": API_BASE_URL,
            "extracted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        records.append(record)
    
    return records


# ============================================================================
# MAIN EXTRACT FUNCTION
# ============================================================================

def extract() -> List[Dict]:
    """
    Main extract function: fetches weather data for all configured cities.
    
    This is the entry point for the extract step. It:
    1. Calculates the date range to fetch
    2. Calls the API for each city
    3. Flattens the nested JSON into flat records
    4. Returns all records combined
    
    Returns:
        List of raw weather records (one per hourly measurement per city)
        
    Raises:
        requests.exceptions.RequestException: If API is unavailable after retries
    """
    logger.info("="*50)
    logger.info("EXTRACT STEP: Fetching weather data from Open-Meteo API")
    logger.info("="*50)
    
    # Calculate date range: last N days ending today
    end_date = date.today()
    start_date = end_date - timedelta(days=DAYS_TO_FETCH - 1)
    
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    logger.info(f"Date range: {start_str} to {end_str} ({DAYS_TO_FETCH} days)")
    logger.info(f"Cities: {', '.join(loc['city'] for loc in LOCATIONS)}")
    logger.info(f"Variables: {', '.join(HOURLY_VARIABLES)}")
    logger.info("")
    
    all_records = []
    successful_cities = 0
    failed_cities = []
    
    for location in LOCATIONS:
        city = location["city"]
        logger.info(f"Fetching data for {city}, {location['country']}...")
        
        # Build API parameters
        params = build_api_params(location, start_str, end_str)
        
        try:
            # Fetch from API with retry logic
            api_response = fetch_with_retry(API_BASE_URL, params)
            
            if api_response is None:
                logger.error(f"  No response for {city} after retries")
                failed_cities.append(city)
                continue
            
            # Flatten the nested API response into flat records
            records = flatten_hourly_data(api_response, location)
            all_records.extend(records)
            
            successful_cities += 1
            logger.info(f"  OK: {len(records)} hourly records for {city}")
            
        except Exception as e:
            logger.error(f"  FAILED for {city}: {e}")
            failed_cities.append(city)
            # Continue with other cities - partial failure is acceptable
            # We prefer partial data over no data
    
    # Summary
    logger.info("")
    logger.info("="*50)
    logger.info(f"Extract complete: {len(all_records)} total records")
    logger.info(f"Successful cities: {successful_cities}/{len(LOCATIONS)}")
    if failed_cities:
        logger.warning(f"Failed cities: {', '.join(failed_cities)}")
    logger.info("="*50)
    
    return all_records


# ============================================================================
# STANDALONE EXECUTION (for testing)
# ============================================================================

if __name__ == "__main__":
    records = extract()
    
    if records:
        print(f"\nSample record (first of {len(records)}):")
        print(json.dumps(records[0], indent=2))
        print(f"\nLast record:")
        print(json.dumps(records[-1], indent=2))
    else:
        print("No records extracted!")
