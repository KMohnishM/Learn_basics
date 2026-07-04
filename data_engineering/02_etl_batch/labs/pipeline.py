"""
pipeline.py
===========
Module 2 Lab: Pipeline Orchestrator - Tie Extract, Transform, Load Together

PURPOSE:
    This is the main entry point for the ETL pipeline.
    It orchestrates the three steps (extract, transform, load) with:
    
    1. Proper error handling (each step has its own try/except)
    2. Structured logging (every step is logged with timing)
    3. Pipeline metadata (start/end time, records processed, status)
    4. Graceful failure handling (clear error messages, non-zero exit code)

PRODUCTION PATTERNS DEMONSTRATED:
    - Pipeline run logging (audit trail)
    - Timing each step
    - Saving pipeline metadata for monitoring
    - Using exit codes to signal success/failure to orchestrators (Airflow, etc.)

USAGE:
    python pipeline.py
    
    Exit codes:
        0 = Success
        1 = Extraction failed
        2 = Transformation failed  
        3 = Load failed
"""

import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path

# Import our pipeline steps
from extract import extract
from transform import transform
from load import load, verify_load

# ============================================================================
# LOGGING SETUP
# ============================================================================
# Set up logging to both console AND a file
# This is important in production - you want logs in a file for debugging
# even after the terminal session ends

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

log_filename = LOG_DIR / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),          # Print to console
        logging.FileHandler(log_filename),           # Also write to file
    ]
)
logger = logging.getLogger("etl.pipeline")


# ============================================================================
# PIPELINE METADATA
# ============================================================================

class PipelineRun:
    """
    Tracks metadata about a single pipeline execution.
    
    In production, this would be written to a pipeline_runs table in
    your database for monitoring and alerting. Tools like Airflow have
    this built-in, but understanding what to track is important.
    
    Fields:
        run_id: Unique identifier for this run
        started_at: When the pipeline started
        completed_at: When it finished (or failed)
        status: "running", "success", "failed"
        steps: Results for each step
        error: Error message if failed
    """
    
    def __init__(self):
        self.run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.started_at = datetime.utcnow()
        self.completed_at = None
        self.status = "running"
        self.steps = {}
        self.error = None
    
    def log_step(self, step_name: str, duration_sec: float, records: int = 0, **kwargs):
        """Log the result of a pipeline step."""
        self.steps[step_name] = {
            "duration_sec": round(duration_sec, 2),
            "records": records,
            **kwargs
        }
    
    def complete(self, status: str, error: str = None):
        """Mark the pipeline as complete."""
        self.completed_at = datetime.utcnow()
        self.status = status
        self.error = error
    
    def total_duration(self) -> float:
        """Calculate total pipeline duration in seconds."""
        end = self.completed_at or datetime.utcnow()
        return (end - self.started_at).total_seconds()
    
    def to_dict(self) -> dict:
        """Serialize to dict for logging/storage."""
        return {
            "run_id": self.run_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "total_duration_sec": round(self.total_duration(), 2),
            "steps": self.steps,
            "error": self.error,
        }
    
    def save(self, output_dir: Path = None):
        """Save pipeline metadata to a JSON file for auditability."""
        if output_dir is None:
            output_dir = LOG_DIR
        
        metadata_file = output_dir / f"{self.run_id}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        
        logger.info(f"Pipeline metadata saved: {metadata_file}")


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def run_pipeline() -> PipelineRun:
    """
    Runs the complete ETL pipeline: Extract -> Transform -> Load.
    
    Each step is:
    - Timed (we log how long each step takes)
    - Error-handled (failure in one step stops the pipeline cleanly)
    - Logged (detailed logs for debugging)
    
    Returns:
        PipelineRun object with execution metadata
    """
    run = PipelineRun()
    
    logger.info("")
    logger.info("=" * 70)
    logger.info(f"  PIPELINE START | Run ID: {run.run_id}")
    logger.info(f"  Started at: {run.started_at.isoformat()}")
    logger.info("=" * 70)
    logger.info("")
    
    # =========================================================================
    # STEP 1: EXTRACT
    # =========================================================================
    logger.info(">>> STEP 1/3: EXTRACT")
    step_start = time.time()
    
    try:
        raw_records = extract()
        step_duration = time.time() - step_start
        
        run.log_step(
            "extract",
            duration_sec=step_duration,
            records=len(raw_records),
            status="success"
        )
        
        logger.info(f">>> STEP 1 COMPLETE | {len(raw_records)} records | {step_duration:.1f}s")
        
        # Validate that we got some data - fail fast if API returned nothing
        if not raw_records:
            logger.error("Extract returned 0 records. Something is wrong with the API.")
            run.complete("failed", "Extract returned 0 records")
            run.save()
            return run
    
    except Exception as e:
        step_duration = time.time() - step_start
        error_msg = f"Extract failed after {step_duration:.1f}s: {e}"
        logger.error(f">>> STEP 1 FAILED | {error_msg}")
        run.log_step("extract", duration_sec=step_duration, status="failed", error=str(e))
        run.complete("failed", error_msg)
        run.save()
        return run
    
    # =========================================================================
    # STEP 2: TRANSFORM
    # =========================================================================
    logger.info("")
    logger.info(">>> STEP 2/3: TRANSFORM")
    step_start = time.time()
    
    try:
        clean_records, quality_metrics = transform(raw_records)
        step_duration = time.time() - step_start
        
        run.log_step(
            "transform",
            duration_sec=step_duration,
            records=len(clean_records),
            status="success",
            pass_rate_pct=quality_metrics.get("pass_rate_pct", 0),
            validation_warnings=quality_metrics.get("validation_warnings", 0),
        )
        
        logger.info(f">>> STEP 2 COMPLETE | {len(clean_records)} records | {step_duration:.1f}s")
        
        # Quality gate: fail if too many records are dropped
        pass_rate = quality_metrics.get("pass_rate_pct", 100)
        if pass_rate < 80:  # 80% pass rate threshold
            logger.error(f"Quality gate FAILED: Only {pass_rate:.1f}% of records passed validation (minimum: 80%)")
            run.complete("failed", f"Quality gate: {pass_rate:.1f}% pass rate < 80% threshold")
            run.save()
            return run
        
        if not clean_records:
            logger.error("Transform returned 0 clean records")
            run.complete("failed", "Transform returned 0 records")
            run.save()
            return run
    
    except Exception as e:
        step_duration = time.time() - step_start
        error_msg = f"Transform failed after {step_duration:.1f}s: {e}"
        logger.error(f">>> STEP 2 FAILED | {error_msg}")
        run.log_step("transform", duration_sec=step_duration, status="failed", error=str(e))
        run.complete("failed", error_msg)
        run.save()
        return run
    
    # =========================================================================
    # STEP 3: LOAD
    # =========================================================================
    logger.info("")
    logger.info(">>> STEP 3/3: LOAD")
    step_start = time.time()
    
    try:
        total, inserted, updated = load(clean_records)
        step_duration = time.time() - step_start
        
        run.log_step(
            "load",
            duration_sec=step_duration,
            records=total,
            status="success",
            inserted=inserted,
            updated=updated,
        )
        
        logger.info(f">>> STEP 3 COMPLETE | {total} records ({inserted} new, {updated} updated) | {step_duration:.1f}s")
    
    except Exception as e:
        step_duration = time.time() - step_start
        error_msg = f"Load failed after {step_duration:.1f}s: {e}"
        logger.error(f">>> STEP 3 FAILED | {error_msg}")
        run.log_step("load", duration_sec=step_duration, status="failed", error=str(e))
        run.complete("failed", error_msg)
        run.save()
        return run
    
    # =========================================================================
    # PIPELINE COMPLETE
    # =========================================================================
    run.complete("success")
    run.save()
    
    logger.info("")
    logger.info("=" * 70)
    logger.info(f"  PIPELINE SUCCESS | Run ID: {run.run_id}")
    logger.info(f"  Total duration: {run.total_duration():.1f}s")
    logger.info("")
    logger.info("  Step Summary:")
    for step_name, step_data in run.steps.items():
        logger.info(f"    {step_name:12}: {step_data.get('records', 0):6} records | {step_data['duration_sec']:.1f}s")
    logger.info("=" * 70)
    logger.info("")
    
    # Run verification queries
    verify_load()
    
    return run


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    logger.info(f"Log file: {log_filename}")
    
    try:
        run = run_pipeline()
        
        if run.status == "success":
            logger.info("Pipeline exiting with status: SUCCESS")
            sys.exit(0)  # Exit code 0 = success (important for schedulers)
        else:
            logger.error(f"Pipeline exiting with status: FAILED")
            logger.error(f"Error: {run.error}")
            sys.exit(1)  # Exit code != 0 = failure (Airflow, cron, etc. check this)
    
    except KeyboardInterrupt:
        logger.warning("Pipeline interrupted by user (Ctrl+C)")
        sys.exit(130)  # Standard exit code for SIGINT
    
    except Exception as e:
        logger.critical(f"Unexpected pipeline error: {e}", exc_info=True)
        sys.exit(1)
