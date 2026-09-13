"""
solution/incremental_pipeline.py
=================================
Module 2 Exercise Solution: Incremental ETL Pipeline with Watermark

Complete solution for the incremental pipeline exercise.
"""

import sys
import time
import json
import logging
import argparse
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional, Tuple

# ============================================================================
# SETUP
# ============================================================================
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger("etl.incremental")

# Watermark file path
WATERMARK_FILE = Path(__file__).parent / "last_run.txt"

# Default days to fetch on first run (bootstrap)
DEFAULT_BOOTSTRAP_DAYS = 7

# Lookback buffer: re-fetch this many extra days to catch late-arriving data
LOOKBACK_BUFFER_DAYS = 1


# ============================================================================
# WATERMARK MANAGEMENT
# ============================================================================

def read_watermark(watermark_file: Path = WATERMARK_FILE) -> Optional[datetime]:
    """
    Reads the watermark from the watermark file.
    
    The watermark tells us: "we have successfully processed all data
    up to this timestamp on the last run."
    
    Returns:
        datetime: The watermark timestamp, or None if no watermark (first run)
    """
    if not watermark_file.exists():
        logger.info(f"No watermark file found at {watermark_file} - this is the first run")
        return None
    
    try:
        content = watermark_file.read_text().strip()
        if not content:
            logger.warning("Watermark file is empty - treating as first run")
            return None
        
        # Parse ISO format timestamp
        watermark = datetime.fromisoformat(content)
        logger.info(f"Watermark loaded: {watermark.isoformat()}")
        return watermark
    
    except ValueError as e:
        logger.warning(f"Could not parse watermark '{content}': {e} - treating as first run")
        return None


def write_watermark(timestamp: datetime, watermark_file: Path = WATERMARK_FILE):
    """
    Writes the watermark to the watermark file.
    
    CRITICAL: This must ONLY be called after a SUCCESSFUL load.
    Writing the watermark before success means that if the load fails,
    the next run will skip the failed data window, causing data loss.
    
    Args:
        timestamp: The timestamp to save as the new watermark
        watermark_file: Path to the watermark file
    """
    watermark_file.write_text(timestamp.isoformat())
    logger.info(f"Watermark updated to: {timestamp.isoformat()}")


def calculate_date_range(
    watermark: Optional[datetime],
    bootstrap_days: int = DEFAULT_BOOTSTRAP_DAYS,
    lookback_buffer: int = LOOKBACK_BUFFER_DAYS
) -> Tuple[date, date]:
    """
    Calculates the date range to fetch based on the watermark.
    
    Logic:
    - No watermark (first run): fetch last N days
    - Watermark exists: fetch from (watermark - buffer) to today
    
    The lookback buffer re-fetches a small amount of already-processed data.
    This handles late-arriving data in the source API.
    
    The idempotent UPSERT in the load step ensures re-fetching existing
    data doesn't cause duplicates.
    
    Args:
        watermark: The last successful run timestamp, or None
        bootstrap_days: How many days to fetch on first run
        lookback_buffer: How many extra days to re-fetch from watermark
    
    Returns:
        Tuple of (start_date, end_date)
    """
    today = date.today()
    
    if watermark is None:
        # First run: bootstrap with last N days
        start_date = today - timedelta(days=bootstrap_days - 1)
        logger.info(f"First run: fetching {bootstrap_days} days ({start_date} to {today})")
    else:
        # Incremental: fetch from watermark (with buffer) to today
        # Subtract buffer to re-fetch slightly overlapping window
        watermark_date = watermark.date() - timedelta(days=lookback_buffer)
        start_date = max(watermark_date, today - timedelta(days=30))  # Don't go back too far
        logger.info(f"Incremental: fetching {start_date} to {today} (watermark was {watermark.date()})")
    
    return start_date, today


# ============================================================================
# INCREMENTAL PIPELINE
# ============================================================================

def run_incremental_pipeline(force_full_reload: bool = False) -> dict:
    """
    Runs the incremental ETL pipeline.
    
    Args:
        force_full_reload: If True, ignore watermark and fetch all data
    
    Returns:
        dict with pipeline run metadata
    """
    # Import pipeline steps (from labs directory)
    # In production, these would be proper Python packages
    import importlib.util
    labs_dir = Path(__file__).parent.parent / "labs"
    
    def import_from_labs(module_name):
        spec = importlib.util.spec_from_file_location(
            module_name, labs_dir / f"{module_name}.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    
    extract_mod = import_from_labs("extract")
    transform_mod = import_from_labs("transform")
    load_mod = import_from_labs("load")
    
    run_start = datetime.utcnow()
    
    logger.info("=" * 60)
    logger.info("INCREMENTAL PIPELINE START")
    logger.info("=" * 60)
    
    # -------------------------------------------------------------------------
    # Read watermark
    # -------------------------------------------------------------------------
    if force_full_reload:
        logger.info("--full-reload flag set: ignoring watermark, fetching all data")
        watermark = None
    else:
        watermark = read_watermark()
    
    # -------------------------------------------------------------------------
    # Calculate date range
    # -------------------------------------------------------------------------
    start_date, end_date = calculate_date_range(watermark)
    
    date_range_days = (end_date - start_date).days + 1
    logger.info(f"Date range: {start_date} to {end_date} ({date_range_days} days)")
    
    # -------------------------------------------------------------------------
    # Extract
    # -------------------------------------------------------------------------
    logger.info("\n>>> STEP 1/3: EXTRACT")
    t0 = time.time()
    
    # Get the modified extract function that accepts dates
    # (In the exercise solution, extract accepts start_date/end_date)
    # For this solution, we'll call the original extract and filter
    raw_records_all = extract_mod.extract()
    
    # Filter to only the records in our date range
    # (In a real implementation, we'd pass dates to the API call directly)
    from datetime import datetime as dt
    raw_records = [
        r for r in raw_records_all
        if r.get("timestamp_utc", "") >= start_date.strftime("%Y-%m-%d")
    ]
    
    extract_duration = time.time() - t0
    logger.info(f"Extracted {len(raw_records)} records in {extract_duration:.1f}s")
    
    if not raw_records:
        logger.info("No new records to process. Exiting.")
        return {"status": "no_data", "records": 0}
    
    # -------------------------------------------------------------------------
    # Transform
    # -------------------------------------------------------------------------
    logger.info("\n>>> STEP 2/3: TRANSFORM")
    t0 = time.time()
    clean_records, quality_metrics = transform_mod.transform(raw_records)
    transform_duration = time.time() - t0
    logger.info(f"Transformed {len(clean_records)} records in {transform_duration:.1f}s")
    
    # -------------------------------------------------------------------------
    # Load (NO watermark write yet - only after success)
    # -------------------------------------------------------------------------
    logger.info("\n>>> STEP 3/3: LOAD")
    t0 = time.time()
    
    try:
        total, inserted, updated = load_mod.load(clean_records)
        load_duration = time.time() - t0
        logger.info(f"Loaded {total} records in {load_duration:.1f}s ({inserted} new, {updated} updated)")
        
        # -----------------------------------------------------------------------
        # WRITE WATERMARK - ONLY after successful load!
        # This is the critical pattern for incremental pipelines.
        # If we crash before this line, the next run will re-fetch the same data.
        # The idempotent upsert handles that gracefully.
        # -----------------------------------------------------------------------
        if total > 0:
            write_watermark(datetime.utcnow())
        else:
            logger.info("No records loaded, watermark unchanged")
        
        total_duration = (datetime.utcnow() - run_start).total_seconds()
        
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"PIPELINE SUCCESS | {total} records | {total_duration:.1f}s total")
        logger.info("=" * 60)
        
        return {
            "status": "success",
            "records": total,
            "inserted": inserted,
            "updated": updated,
            "date_range_days": date_range_days,
            "duration_sec": total_duration,
        }
    
    except Exception as e:
        logger.error(f"Load failed: {e}")
        # Watermark NOT updated - next run will retry this window
        logger.info("Watermark NOT updated due to load failure - next run will retry")
        raise


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Incremental ETL Pipeline for Weather Data"
    )
    parser.add_argument(
        "--full-reload",
        action="store_true",
        help="Ignore watermark and fetch all data (for backfill/bug fix)"
    )
    parser.add_argument(
        "--show-watermark",
        action="store_true",
        help="Show current watermark and exit"
    )
    
    args = parser.parse_args()
    
    if args.show_watermark:
        wm = read_watermark()
        if wm:
            print(f"Current watermark: {wm.isoformat()}")
        else:
            print("No watermark (first run)")
        return
    
    try:
        result = run_incremental_pipeline(force_full_reload=args.full_reload)
        
        if result.get("status") == "success":
            sys.exit(0)
        else:
            sys.exit(0)  # No data is not a failure
    
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
