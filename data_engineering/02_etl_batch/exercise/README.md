# Module 2 Exercise: Incremental ETL Pipeline

## Objective

Transform the weather ETL pipeline from **full load** to **incremental load**.

Currently, the pipeline fetches the last 7 days of data on every run. This is wasteful:
- On day 2, we re-fetch 6 days of data we already have
- After 30 days, we're re-fetching 6 days of redundant data every single run
- At scale, re-fetching grows linearly and becomes very expensive

Your task is to implement a **watermark-based incremental pipeline** that:
- On first run: fetches the last 7 days (bootstrap/backfill)
- On subsequent runs: fetches ONLY the data since the last successful run

## Background: The Watermark Pattern

A watermark is a stored timestamp that marks "the last time we successfully processed data."

```
FULL LOAD (current behavior):
  Run 1 (Jan 7):  Fetch Jan 1-7   -> Load 7 days
  Run 2 (Jan 8):  Fetch Jan 2-8   -> Load 7 days (6 days are DUPLICATES)
  Run 3 (Jan 9):  Fetch Jan 3-9   -> Load 7 days (6 days are DUPLICATES)

INCREMENTAL LOAD (your target):
  Run 1 (Jan 7):  No watermark -> Fetch Jan 1-7   -> Load 7 days
                  Save watermark: "2024-01-07"
  Run 2 (Jan 8):  Watermark=Jan 7 -> Fetch Jan 7-8 -> Load 1 day (new data only)
                  Save watermark: "2024-01-08"
  Run 3 (Jan 9):  Watermark=Jan 8 -> Fetch Jan 8-9 -> Load 1 day
                  Save watermark: "2024-01-09"
```

## Requirements

### Part 1: Watermark Management

Create `watermark.py` with these functions:

1. `read_watermark(watermark_file: str) -> Optional[datetime]`
   - Reads the watermark from `last_run.txt`
   - Returns None if file doesn't exist (first run)
   - Returns datetime object if file exists

2. `write_watermark(watermark_file: str, timestamp: datetime) -> None`
   - Writes the timestamp to `last_run.txt` in ISO format
   - Only write AFTER successful load (not before - see below)

3. `calculate_date_range(watermark: Optional[datetime], default_days: int = 7) -> Tuple[date, date]`
   - If watermark is None: return (today - default_days, today)
   - If watermark exists: return (watermark.date(), today)
   - Add a 1-day buffer to the watermark date to handle any clock skew

### Part 2: Modify `extract.py`

Modify the `extract()` function to accept `start_date` and `end_date` parameters instead of always calculating them internally:

```python
def extract(start_date: str, end_date: str) -> List[Dict]:
    """Fetches weather data for the given date range."""
    ...
```

### Part 3: Modify `pipeline.py`

Create `incremental_pipeline.py` that:

1. Reads the watermark at the start
2. Calculates the date range based on the watermark
3. Calls extract with the calculated date range
4. After successful load, writes the new watermark
5. **CRITICAL**: Only write the watermark AFTER successful load
   - If load fails, watermark should NOT be updated
   - Next run will re-attempt from the same point
   - This ensures idempotency!

```python
def run_incremental_pipeline():
    watermark = read_watermark("last_run.txt")
    
    if watermark is None:
        print("First run: bootstrapping with last 7 days")
    else:
        print(f"Incremental run: fetching since {watermark}")
    
    start_date, end_date = calculate_date_range(watermark)
    
    # Extract only new data
    raw = extract(start_date=start_date.strftime("%Y-%m-%d"),
                  end_date=end_date.strftime("%Y-%m-%d"))
    
    clean, quality = transform(raw)
    total, inserted, updated = load(clean)
    
    # ONLY update watermark on success
    if total > 0:
        write_watermark("last_run.txt", datetime.now())
        print(f"Watermark updated to: {datetime.now()}")
```

### Part 4: Test Idempotency

Run the incremental pipeline 3 times and verify:
1. First run: loads 7 days of data
2. Second run (same day): loads 0 or 1 days of data (only today)
3. Third run (same day): loads 0 records (nothing new since last run)

Write a test script `test_idempotency.py` that:
- Runs the pipeline 3 times
- After each run, records the row count in the database
- Verifies that row counts don't grow unexpectedly
- Verifies results are identical on runs 2 and 3

### Part 5: Add a "Force Full Reload" Flag

Add a command-line flag `--full-reload` that ignores the watermark and re-fetches everything:

```bash
# Normal incremental run
python incremental_pipeline.py

# Force full reload (useful for backfilling after bug fix)
python incremental_pipeline.py --full-reload
```

## Deliverables

```
exercise/
├── watermark.py               # Watermark read/write functions
├── incremental_pipeline.py    # Modified pipeline using watermark
├── test_idempotency.py        # Idempotency test
└── last_run.txt               # Created automatically on first run
```

## Key Concepts to Understand

1. **Why write watermark AFTER success, not before?**
   
   If you write the watermark BEFORE the load and the load fails:
   - Next run sees the new watermark
   - Fetches only data since "new watermark"
   - The failed data window is LOST FOREVER
   
   If you write watermark AFTER successful load:
   - If load fails, watermark stays at the old value
   - Next run re-fetches the same window
   - Idempotent upsert handles the duplicate records safely
   - No data loss!

2. **The lookback buffer**: Add 1-day buffer to the watermark date.
   
   Reason: API data can be backfilled. Yesterday's 3am data might
   not appear in the API until today. By re-fetching yesterday's data,
   we catch any late-arriving data.

3. **What if the pipeline runs twice simultaneously?**
   
   This is the "concurrent execution" problem. Your solution should
   either prevent this (with a lock file) or handle it gracefully (upsert does).

## Grading Criteria

- [ ] `watermark.py` reads and writes watermarks correctly
- [ ] First run fetches 7 days of data
- [ ] Second run fetches only 1-2 days of data (significant reduction)
- [ ] Watermark is only written after successful load
- [ ] `--full-reload` flag works correctly
- [ ] Idempotency test passes (3 consecutive runs produce same DB state)
- [ ] Clear logging shows what date range is being fetched on each run
