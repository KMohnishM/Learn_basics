"""
estimation_calculator.py
========================
A comprehensive back-of-envelope estimation calculator for system design.

This module provides tools for calculating:
  - QPS (Queries Per Second) from DAU and usage patterns
  - Storage requirements from record counts and sizes
  - Bandwidth requirements from QPS and payload sizes
  - Replication and index overhead
  - 5 fully worked examples: Instagram, Twitter, YouTube, WhatsApp, Uber

How to run:
  python estimation_calculator.py

Learning goals:
  - Develop intuition for data magnitudes (KB -> MB -> GB -> TB -> PB -> EB)
  - Understand how to translate user behavior assumptions into infrastructure needs
  - Practice the mental math shortcuts used in real system design interviews
"""

import math


# =============================================================================
# SECTION 1: CONSTANTS
# Reference numbers that every engineer should have memorized.
# These are the "units" of back-of-envelope estimation.
# =============================================================================

class StorageUnits:
    """
    Storage size constants in bytes.
    
    Important: We use powers of 10 (SI prefixes) for simplicity in estimation.
    Real storage uses powers of 2 (e.g., 1 GiB = 1,073,741,824 bytes),
    but for back-of-envelope work, powers of 10 are accurate enough and easier
    to compute mentally.
    """
    BYTE = 1
    KB = 1_000             # 10^3 bytes
    MB = 1_000_000         # 10^6 bytes
    GB = 1_000_000_000     # 10^9 bytes
    TB = 1_000_000_000_000 # 10^12 bytes
    PB = 10**15            # 10^15 bytes
    EB = 10**18            # 10^18 bytes


class TimeConstants:
    """
    Time conversion constants.
    
    The key number to memorize: 1 day = 86,400 seconds.
    This is used constantly in QPS calculations.
    (60 seconds/min * 60 min/hour * 24 hours/day = 86,400)
    """
    SECONDS_PER_MINUTE = 60
    SECONDS_PER_HOUR = 3600
    SECONDS_PER_DAY = 86_400       # Most important number!
    SECONDS_PER_MONTH = 2_592_000  # 30 days
    SECONDS_PER_YEAR = 31_536_000  # 365 days


class TypicalDataSizes:
    """
    Reference sizes for common data objects.
    
    These are approximations based on industry knowledge and should be
    adjusted based on actual requirements. When in doubt, use the
    HIGHER estimate to be conservative in your capacity planning.
    """
    # Primitive types (in bytes)
    BOOLEAN = 1
    INT32 = 4
    INT64 = 8
    FLOAT64 = 8
    UUID_BINARY = 16
    UUID_TEXT = 36         # "550e8400-e29b-41d4-a716-446655440000"
    TIMESTAMP = 8          # Stored as 64-bit integer (Unix epoch in ms)
    
    # Text fields (typical average sizes, in bytes)
    USERNAME = 20
    EMAIL_ADDRESS = 50
    URL = 100
    TWEET_TEXT = 200       # 280 char limit, but most tweets are shorter
    DESCRIPTION = 500
    
    # User records (in bytes)
    SIMPLE_USER_PROFILE = 500      # id, name, email, avatar_url, created_at
    RICH_USER_PROFILE = 2_000      # Plus bio, location, settings, preferences
    
    # Media files (in bytes)
    THUMBNAIL_IMAGE = 10 * 1000        # 10 KB -- tiny preview
    SMALL_IMAGE = 100 * 1000           # 100 KB -- compressed for mobile
    MEDIUM_IMAGE = 500 * 1000          # 500 KB -- standard web image
    LARGE_IMAGE = 3 * 1_000_000        # 3 MB -- original uncompressed
    ONE_MINUTE_AUDIO_MP3 = 1 * 1_000_000  # ~1 MB per minute at 128kbps
    ONE_MINUTE_VIDEO_720P = 100 * 1_000_000  # ~100 MB per minute uncompressed
    ONE_MINUTE_VIDEO_720P_COMPRESSED = 15 * 1_000_000  # ~15 MB compressed (H.264)
    
    # Geographic data
    GPS_COORDINATE = 16    # latitude (float64) + longitude (float64)
    LOCATION_UPDATE = 50   # GPS + driver_id + timestamp + speed + heading


class LatencyNumbers:
    """
    Reference latency values (in nanoseconds).
    
    From Jeff Dean's famous latency table. These numbers give you intuition
    for how long each operation takes and help you reason about bottlenecks.
    
    Mental model: If 1 nanosecond = 1 second,
      - L1 cache = 0.5 seconds
      - RAM = 1.7 minutes
      - SSD random read = 4.4 hours
      - Cross-continent network = 4.8 years
    """
    L1_CACHE_NS = 0.5              # CPU L1 cache hit
    L2_CACHE_NS = 7                # CPU L2 cache hit
    RAM_REFERENCE_NS = 100         # Main memory access
    SSD_RANDOM_READ_NS = 16_000    # NVMe SSD random read (16 microseconds)
    SSD_SEQUENTIAL_MB_NS = 1_000_000  # Read 1MB from SSD (1 millisecond)
    HDD_SEEK_NS = 10_000_000       # HDD seek time (10 milliseconds)
    DC_ROUNDTRIP_NS = 500_000      # Same datacenter RTT (500 microseconds)
    CROSS_CONTINENT_NS = 150_000_000  # US to Europe RTT (150 milliseconds)


# =============================================================================
# SECTION 2: CORE CALCULATION FUNCTIONS
# These functions implement the 4-step estimation framework:
#   1. Calculate QPS (from DAU and user behavior)
#   2. Calculate Storage (from record sizes and retention)
#   3. Calculate Bandwidth (from QPS and payload sizes)
# =============================================================================

def calculate_qps(
    dau: int,
    events_per_user_per_day: float,
    peak_multiplier: float = 2.0,
    description: str = ""
) -> dict:
    """
    Calculate average and peak QPS from daily active users.
    
    This is the fundamental QPS estimation formula:
        Average QPS = DAU * events_per_user_per_day / seconds_per_day
        Peak QPS = Average QPS * peak_multiplier
    
    Args:
        dau: Daily Active Users -- the number of unique users who use the
             system on a given day. This is different from MAU (Monthly Active
             Users). DAU/MAU ratio ("stickiness") is typically 10-40% for
             consumer apps.
        
        events_per_user_per_day: How many times the average user performs this
             action per day. Examples:
               - Tweet writes: 0.3 (30% of users tweet once per day)
               - Timeline reads: 15 (5 sessions * 3 loads)
               - GPS location updates: 21,600 (every 4 seconds, 24 hours)
        
        peak_multiplier: Factor to account for peak traffic vs. average.
             Traffic is NEVER uniform -- it peaks in evenings, during events,
             Monday mornings for B2B apps, etc. Typical values:
               - 2x: Steady consumer apps (social media)
               - 5x: News/event-driven apps (traffic spikes during news)
               - 10x: Highly bursty systems (flash sales, concert ticket drops)
        
        description: Optional label for this operation (e.g., "Timeline reads")
    
    Returns:
        Dictionary with:
          - avg_qps: Average queries per second across the whole day
          - peak_qps: Peak QPS during busy periods
          - events_per_day: Total events per day
          - description: Label for this operation
    
    Example:
        >> calculate_qps(dau=500_000_000, events_per_user_per_day=2, peak_multiplier=2)
        # Instagram photo uploads: 500M DAU, 10% upload 2 photos each
        # Must pre-multiply: dau=500M * 10% = 50M active uploaders
        # events_per_user_per_day = 2 photos * 10% = 0.2 (as fraction of all DAU)
    """
    events_per_day = dau * events_per_user_per_day
    avg_qps = events_per_day / TimeConstants.SECONDS_PER_DAY
    peak_qps = avg_qps * peak_multiplier
    
    return {
        "description": description,
        "dau": dau,
        "events_per_user_per_day": events_per_user_per_day,
        "events_per_day": int(events_per_day),
        "avg_qps": avg_qps,
        "peak_qps": peak_qps,
        "peak_multiplier": peak_multiplier,
    }


def calculate_storage(
    records_per_day: int,
    bytes_per_record: int,
    retention_years: float = 5.0,
    replication_factor: int = 3,
    index_overhead_pct: float = 0.30,
    description: str = ""
) -> dict:
    """
    Calculate total storage required for a system.
    
    Storage estimation formula:
        Raw daily = records_per_day * bytes_per_record
        5-year raw = raw_daily * 365 * years
        With replication = raw_total * replication_factor
        With indexes = replicated_total * (1 + index_overhead_pct)
    
    Args:
        records_per_day: Number of new records written to storage each day.
             For immutable systems (like event logs), this grows linearly.
             For systems that update records (like user profiles), growth
             is slower -- you're updating existing records, not adding new ones.
        
        bytes_per_record: Average size of one record in bytes.
             For databases: size of the row/document/object
             For object stores (S3-style): size of the file/blob
             For message queues: size of one message payload
        
        retention_years: How long data is kept before deletion.
             - Chat messages: Often 5-10 years (users expect message history)
             - Log data: 30-90 days (expensive, use tiered storage)
             - Financial records: 7 years (regulatory requirement in many jurisdictions)
             - Photos/videos: Indefinitely (users never expect their photos deleted)
        
        replication_factor: Number of copies stored for durability.
             - 1: Single copy (not recommended for anything important)
             - 3: Standard (used by HDFS, Cassandra by default)
             - 5: High durability (some financial systems)
             Amazon S3 uses erasure coding to achieve 11 nines durability with 
             less than 3x space overhead.
        
        index_overhead_pct: Additional space for indexes.
             - 20-30% for typical relational tables with a few indexes
             - 50-100% for heavily indexed tables
             - B-Tree indexes are typically 10-20% of table size per index
        
        description: Optional label for this dataset
    
    Returns:
        Dictionary with storage at each stage:
          - raw_daily_bytes: Raw bytes written per day
          - raw_total_bytes: Raw bytes for full retention period
          - replicated_bytes: After applying replication factor
          - total_with_overhead_bytes: Final storage including index overhead
          - Formatted human-readable versions of each
    
    Example:
        >> calculate_storage(
        ..     records_per_day=100_000_000,  # 100M Instagram photos
        ..     bytes_per_record=3_000_000,    # 3 MB average photo
        ..     retention_years=5,
        ..     replication_factor=3
        .. )
    """
    # Daily raw storage for new records
    raw_daily_bytes = records_per_day * bytes_per_record
    
    # Total raw storage over retention period
    raw_total_bytes = raw_daily_bytes * 365 * retention_years
    
    # After replication (each byte stored N times for redundancy and durability)
    replicated_bytes = raw_total_bytes * replication_factor
    
    # After adding index overhead (B-tree indexes, hash indexes, etc.)
    total_with_overhead_bytes = replicated_bytes * (1 + index_overhead_pct)
    
    return {
        "description": description,
        "records_per_day": records_per_day,
        "bytes_per_record": bytes_per_record,
        "retention_years": retention_years,
        "replication_factor": replication_factor,
        "index_overhead_pct": index_overhead_pct,
        "raw_daily_bytes": raw_daily_bytes,
        "raw_total_bytes": raw_total_bytes,
        "replicated_bytes": replicated_bytes,
        "total_with_overhead_bytes": total_with_overhead_bytes,
        "raw_daily_human": _format_bytes(raw_daily_bytes),
        "raw_total_human": _format_bytes(raw_total_bytes),
        "replicated_human": _format_bytes(replicated_bytes),
        "total_human": _format_bytes(total_with_overhead_bytes),
    }


def calculate_bandwidth(
    qps: float,
    bytes_per_request: int,
    direction: str = "both",
    description: str = ""
) -> dict:
    """
    Calculate network bandwidth requirements.
    
    Bandwidth is often an overlooked but critical dimension of system design.
    It determines:
      - Network interface card (NIC) requirements
      - Cloud provider egress costs (can be $$$)
      - CDN capacity requirements
      - WAN link sizing for multi-region architectures
    
    Args:
        qps: Queries per second (use peak QPS for capacity planning,
             average QPS for cost estimation)
        
        bytes_per_request: Average size of the request or response payload.
             For upload bandwidth: use the request body size (what goes UP)
             For download bandwidth: use the response body size (what comes DOWN)
             Important: HTTP headers add ~200-500 bytes overhead per request
        
        direction: "upload", "download", or "both" -- for labeling clarity
        
        description: Optional label for this traffic type
    
    Returns:
        Dictionary with:
          - bytes_per_second: Raw bytes/second
          - megabits_per_second: Mbps (how network capacity is measured)
          - gigabits_per_second: Gbps (for high-volume systems)
          - bytes_per_day: Total bytes per day (for cost estimation)
    
    Example:
        >> # Calculate YouTube video download bandwidth
        >> calculate_bandwidth(
        ..     qps=500_000,           # 500K concurrent video streams
        ..     bytes_per_request=500_000,  # 500 KB per second per stream
        ..     direction="download",
        ..     description="YouTube video streaming"
        .. )
    """
    bytes_per_second = qps * bytes_per_request
    megabits_per_second = (bytes_per_second * 8) / (1000 * 1000)
    gigabits_per_second = megabits_per_second / 1000
    bytes_per_day = bytes_per_second * TimeConstants.SECONDS_PER_DAY
    
    return {
        "description": description,
        "direction": direction,
        "qps": qps,
        "bytes_per_request": bytes_per_request,
        "bytes_per_second": bytes_per_second,
        "megabits_per_second": megabits_per_second,
        "gigabits_per_second": gigabits_per_second,
        "bytes_per_day": bytes_per_day,
        "bytes_per_day_human": _format_bytes(bytes_per_day),
    }


# =============================================================================
# SECTION 3: HELPER FUNCTIONS
# =============================================================================

def _format_bytes(bytes_val: float) -> str:
    """
    Convert a byte count to a human-readable string.
    
    Examples:
        _format_bytes(1_500) -> "1.50 KB"
        _format_bytes(2_500_000_000) -> "2.50 GB"
        _format_bytes(2_000_000_000_000_000_000) -> "2.00 EB"
    """
    if bytes_val >= StorageUnits.EB:
        return f"{bytes_val / StorageUnits.EB:.2f} EB"
    elif bytes_val >= StorageUnits.PB:
        return f"{bytes_val / StorageUnits.PB:.2f} PB"
    elif bytes_val >= StorageUnits.TB:
        return f"{bytes_val / StorageUnits.TB:.2f} TB"
    elif bytes_val >= StorageUnits.GB:
        return f"{bytes_val / StorageUnits.GB:.2f} GB"
    elif bytes_val >= StorageUnits.MB:
        return f"{bytes_val / StorageUnits.MB:.2f} MB"
    elif bytes_val >= StorageUnits.KB:
        return f"{bytes_val / StorageUnits.KB:.2f} KB"
    else:
        return f"{bytes_val:.0f} bytes"


def _format_number(n: float) -> str:
    """
    Format large numbers with commas and abbreviations.
    
    Examples:
        _format_number(1_500) -> "1,500"
        _format_number(1_500_000) -> "1.50M"
        _format_number(2_500_000_000) -> "2.50B"
    """
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f}B"
    elif n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    elif n >= 1_000:
        return f"{n:,.0f}"
    else:
        return f"{n:.2f}"


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_qps_result(result: dict):
    """Print QPS calculation results in a formatted table."""
    print(f"\n  Operation: {result['description']}")
    print(f"  {'DAU':<35} {_format_number(result['dau'])}")
    print(f"  {'Events per user per day':<35} {result['events_per_user_per_day']:.2f}")
    print(f"  {'Total events per day':<35} {_format_number(result['events_per_day'])}")
    print(f"  {'Average QPS':<35} {result['avg_qps']:,.0f} req/sec")
    print(f"  {'Peak QPS ({:.0f}x multiplier)':<35} {result['peak_qps']:,.0f} req/sec".format(result['peak_multiplier']))


def print_storage_result(result: dict):
    """Print storage calculation results in a formatted table."""
    print(f"\n  Dataset: {result['description']}")
    print(f"  {'Records per day':<35} {_format_number(result['records_per_day'])}")
    print(f"  {'Bytes per record':<35} {_format_bytes(result['bytes_per_record'])}")
    print(f"  {'Retention period':<35} {result['retention_years']:.1f} years")
    print(f"  {'Replication factor':<35} {result['replication_factor']}x")
    print(f"  {'Index overhead':<35} {result['index_overhead_pct']*100:.0f}%")
    print(f"  {'-'*50}")
    print(f"  {'Raw daily write':<35} {result['raw_daily_human']}")
    print(f"  {'Raw total ({:.0f} years)':<35} {result['raw_total_human']}".format(result['retention_years']))
    print(f"  {'After replication':<35} {result['replicated_human']}")
    print(f"  {'TOTAL (with indexes)':<35} {result['total_human']}")


def print_bandwidth_result(result: dict):
    """Print bandwidth calculation results in a formatted table."""
    print(f"\n  Traffic: {result['description']} ({result['direction']})")
    print(f"  {'QPS':<35} {result['qps']:,.0f} req/sec")
    print(f"  {'Payload size':<35} {_format_bytes(result['bytes_per_request'])}")
    print(f"  {'-'*50}")
    print(f"  {'Bytes per second':<35} {_format_bytes(result['bytes_per_second'])}/sec")
    print(f"  {'Bandwidth':<35} {result['megabits_per_second']:,.0f} Mbps = {result['gigabits_per_second']:.2f} Gbps")
    print(f"  {'Data transferred per day':<35} {result['bytes_per_day_human']}")


# =============================================================================
# SECTION 4: THE 5 WORKED EXAMPLES
# Each example demonstrates the full estimation process for a real system.
# =============================================================================

def example_instagram():
    """
    EXAMPLE 1: Instagram Photo Storage Estimation
    
    The problem: Design Instagram's photo storage system.
    How much storage do we need? What's our write QPS?
    
    Instagram scale facts (real data):
      - 1 billion+ total users, 500M+ daily active users
      - 100 million+ photos uploaded per day
      - 2+ billion interactions (likes/comments) per day
      - Stores photos in Amazon S3 (they've shared this publicly)
    """
    print_section("EXAMPLE 1: Instagram Photo Storage")
    print("\n  Assumptions (state these explicitly in an interview!):")
    print("    DAU: 500 million")
    print("    % who upload photos daily: 10% (most users only consume)")
    print("    Photos per uploading user: 2")
    print("    Average photo size (compressed): 3 MB")
    print("    Versions stored: 4 (thumbnail, small, medium, original) = ~4.5 MB total")
    print("    Retention: Forever")
    print("    Replication: 3x")

    # QPS: Photo uploads (writes)
    # 10% of 500M DAU = 50M actual uploaders
    # Each uploads 2 photos -> 0.2 photos per DAU
    photo_upload_qps = calculate_qps(
        dau=500_000_000,
        events_per_user_per_day=0.2,  # 10% of users upload 2 photos = 0.2 per user avg
        peak_multiplier=2.0,
        description="Photo uploads"
    )
    print_qps_result(photo_upload_qps)
    
    # QPS: Photo views (reads) - typically 100:1 read:write ratio for Instagram
    photo_view_qps = calculate_qps(
        dau=500_000_000,
        events_per_user_per_day=20.0,  # ~4 sessions, ~5 photo views per session
        peak_multiplier=3.0,
        description="Photo views (reads)"
    )
    print_qps_result(photo_view_qps)
    
    # Storage: Photos
    # 100M photos/day at 4.5 MB average (with all resolutions)
    photo_storage = calculate_storage(
        records_per_day=100_000_000,      # 100M photos uploaded daily
        bytes_per_record=4_500_000,       # 4.5 MB (4 resolutions combined)
        retention_years=5.0,
        replication_factor=3,
        index_overhead_pct=0.05,          # Object store metadata, not DB indexes
        description="Instagram photos (all resolutions)"
    )
    print_storage_result(photo_storage)
    
    # Storage: Photo metadata in Postgres/Cassandra
    photo_metadata_storage = calculate_storage(
        records_per_day=100_000_000,
        bytes_per_record=500,              # photo_id, user_id, timestamp, location, tags
        retention_years=5.0,
        replication_factor=3,
        index_overhead_pct=0.30,
        description="Photo metadata (database)"
    )
    print_storage_result(photo_metadata_storage)
    
    # Bandwidth: Upload bandwidth
    upload_bandwidth = calculate_bandwidth(
        qps=photo_upload_qps["avg_qps"],
        bytes_per_request=3_000_000,      # 3 MB original upload
        direction="upload (incoming)",
        description="Photo uploads"
    )
    print_bandwidth_result(upload_bandwidth)
    
    print("\n  KEY INSIGHT: Instagram stores photos in Amazon S3 with CloudFront CDN.")
    print("  The CDN serves most read traffic, so origin servers see much less read load.")
    print("  The database stores metadata (tiny!); photos go directly to object store.")


def example_twitter():
    """
    EXAMPLE 2: Twitter/X QPS and Storage Estimation
    
    The problem: Estimate Twitter's infrastructure requirements.
    Focus on: tweet writes, timeline reads, and the fan-out problem.
    
    Twitter scale facts (real data):
      - 350M MAU, ~150M DAU
      - 500 million tweets per day
      - 300 billion tweet impressions per day
      - Real-time search index over all tweets
    """
    print_section("EXAMPLE 2: Twitter/X QPS and Storage")
    print("\n  Assumptions:")
    print("    MAU: 350 million, DAU: 140 million (40% of MAU)")
    print("    30% of DAU post 1 tweet per day = 42M tweets/day")
    print("    (Twitter reports 500M/day -- our estimate is conservative)")
    print("    5 sessions per user, 3 timeline loads per session = 15 timeline reads")
    print("    20 tweets fetched per timeline load")
    print("    Average user follows 200 accounts")

    # Write QPS: Tweet creation
    tweet_write_qps = calculate_qps(
        dau=140_000_000,
        events_per_user_per_day=0.3,       # 30% of users tweet once
        peak_multiplier=3.0,               # Events (sports, elections) spike traffic
        description="Tweet writes"
    )
    print_qps_result(tweet_write_qps)
    
    # Read QPS: Timeline reads (the dominant operation)
    timeline_read_qps = calculate_qps(
        dau=140_000_000,
        events_per_user_per_day=15.0,     # 5 sessions * 3 loads per session
        peak_multiplier=3.0,
        description="Timeline reads"
    )
    print_qps_result(timeline_read_qps)
    
    # Storage: Tweets (just text, no media)
    tweet_storage = calculate_storage(
        records_per_day=500_000_000,       # Twitter's actual number
        bytes_per_record=300,              # tweet_id, user_id, text, timestamp, retweet_id
        retention_years=5.0,
        replication_factor=3,
        index_overhead_pct=0.50,           # Heavy indexing (full-text search, time-sorted)
        description="Tweet text data"
    )
    print_storage_result(tweet_storage)
    
    # Storage: User social graph (follower/following relationships)
    # 350M users, average 200 followers, 200 following
    # Each edge: user_id (8 bytes) + follower_id (8 bytes) = 16 bytes
    graph_storage = calculate_storage(
        records_per_day=350_000,           # New follower relationships per day (~1% of users)
        bytes_per_record=16,               # follower_id + following_id pair
        retention_years=5.0,
        replication_factor=3,
        index_overhead_pct=0.30,
        description="Social graph (follower relationships)"
    )
    print_storage_result(graph_storage)
    
    print("\n  THE FAN-OUT PROBLEM (the key insight for Twitter):")
    print("    Regular user with 500 followers tweets:")
    print("    -> 500 additional write operations to deliver to follower timelines")
    print(f"    -> At {tweet_write_qps['avg_qps']:,.0f} tweets/sec, fan-out = "
          f"{tweet_write_qps['avg_qps'] * 500:,.0f} writes/sec (500x amplification!)")
    print()
    print("    @BarackObama with 130M followers tweets:")
    print("    -> 130,000,000 additional writes for ONE tweet!")
    print("    -> This is why Twitter uses a HYBRID approach:")
    print("       * PUSH model for regular users (write to all follower timelines at tweet time)")
    print("       * PULL model for celebrities >1M followers (compute timeline at read time)")


def example_youtube():
    """
    EXAMPLE 3: YouTube Video Upload and Streaming Estimation
    
    The problem: Estimate YouTube's storage and bandwidth requirements.
    Focus on: upload storage, video processing, streaming bandwidth.
    
    YouTube scale facts (real data):
      - 500 hours of video uploaded per MINUTE
      - 1 billion hours watched per DAY
      - 2 billion logged-in users monthly
      - Average session: 40+ minutes
    """
    print_section("EXAMPLE 3: YouTube Video Storage and Streaming")
    print("\n  Assumptions:")
    print("    500 hours of video uploaded per minute")
    print("    1 hour of 720p video = ~1 GB compressed (H.264)")
    print("    Stored at 5 quality levels: 360p, 480p, 720p, 1080p, 4K")
    print("    Average storage per quality level: 30% of HD (360p=0.1x, 4K=3x)")
    print("    Replication: 3x across datacenters")
    print("    DAU: 2 billion, average 40 min/day watch time")
    print("    Average video quality consumed: 720p")
    
    # Upload: How much data lands on YouTube servers per day?
    # 500 hours/minute * 60 minutes/hour = 30,000 hours/day of new video
    # 30,000 hours * 1 GB/hour = 30,000 GB = 30 TB/day raw upload
    hours_per_minute = 500
    hours_per_day = hours_per_minute * 60 * 24         # 720,000 hours/day
    raw_upload_gb_per_day = hours_per_day * 1          # 1 GB per hour (720p)
    
    print(f"\n  Upload volume:")
    print(f"    Raw uploads: {hours_per_day:,} hours of video per day")
    print(f"    Raw storage: {raw_upload_gb_per_day:,} GB = {raw_upload_gb_per_day/1000:.0f} TB per day")
    
    # Multi-resolution encoding multiplier
    # YouTube transcodes to: 144p, 240p, 360p, 480p, 720p, 1080p, 1440p, 4K
    # Simplified: assume 4x storage multiplier for all resolutions
    encoding_multiplier = 4
    print(f"    After multi-resolution transcoding ({encoding_multiplier}x): "
          f"{raw_upload_gb_per_day * encoding_multiplier / 1000:.0f} TB/day")
    
    # Storage with replication
    video_storage = calculate_storage(
        records_per_day=int(hours_per_day * 1_000_000_000 * encoding_multiplier),
        bytes_per_record=1,               # trick: record size is 1 byte, count is actual bytes
        retention_years=5.0,
        replication_factor=3,
        index_overhead_pct=0.02,          # minimal overhead for object store
        description="YouTube video files (all resolutions)"
    )
    # Override to correct the weird way we did the math above
    raw_daily = hours_per_day * 1_000_000_000 * encoding_multiplier  # 720K hours * 1GB * 4 resolutions
    replicated = raw_daily * 3  # 3x replication
    five_year = raw_daily * 365 * 5 * 3
    print(f"\n  Storage calculation:")
    print(f"    Daily raw (all resolutions, 3x replication): {_format_bytes(replicated)}")
    print(f"    5-year total: {_format_bytes(five_year)}")
    
    # Streaming bandwidth calculation
    # 1B hours watched per day = 1B * 3600 seconds per day
    # At 720p: ~2 Mbps = 250 KB/s
    concurrent_viewers_at_peak = 50_000_000  # 50M concurrent viewers
    streaming_bandwidth = calculate_bandwidth(
        qps=concurrent_viewers_at_peak,
        bytes_per_request=250_000,         # 250 KB per second per 720p stream
        direction="download (egress)",
        description="YouTube video streaming"
    )
    print_bandwidth_result(streaming_bandwidth)
    
    print("\n  KEY INSIGHT: YouTube uses Google's own CDN (Google Global Cache)")
    print("  Most traffic is served from CDN edge nodes co-located with ISPs.")
    print("  This dramatically reduces egress bandwidth from YouTube's own DCs.")
    print("  Video transcoding is handled by a massive distributed pipeline")
    print("  using Google's internal infrastructure (Borg/GKE).")


def example_whatsapp():
    """
    EXAMPLE 4: WhatsApp Message Delivery Estimation
    
    The problem: Estimate WhatsApp's infrastructure for message delivery.
    Focus on: message throughput, delivery QPS, storage (minimal, due to encryption).
    
    WhatsApp scale facts (real data):
      - 100 billion messages per day (WhatsApp published this)
      - 2 billion users
      - End-to-end encrypted (server cannot read messages)
      - Messages NOT stored on servers after delivery (mostly)
      - 65 billion messages processed per day
    """
    print_section("EXAMPLE 4: WhatsApp Message Delivery")
    print("\n  Assumptions:")
    print("    DAU: 1 billion (50% of 2B users active daily)")
    print("    Messages sent per user per day: 100 (active messaging app)")
    print("    Message types: 70% text, 20% images, 10% video")
    print("    Text message: 500 bytes average")
    print("    Image message: 200 KB average (compressed for mobile)")
    print("    Video message: 2 MB average (short clips)")
    print("    End-to-end encrypted: server stores only encrypted payload")
    print("    Retention: Messages deleted from servers after successful delivery")
    print("    Offline delivery: Stored for up to 30 days if recipient offline")
    
    # Message write QPS
    msg_write_qps = calculate_qps(
        dau=1_000_000_000,               # 1 billion DAU
        events_per_user_per_day=100.0,   # 100 messages per user per day
        peak_multiplier=5.0,             # Regional events (New Year's, elections)
        description="Message writes"
    )
    print_qps_result(msg_write_qps)
    
    # Message delivery QPS (every message sent must also be delivered)
    msg_delivery_qps = calculate_qps(
        dau=1_000_000_000,
        events_per_user_per_day=100.0,   # Same as writes (each sent msg is delivered)
        peak_multiplier=5.0,
        description="Message delivery (push notifications/socket delivery)"
    )
    print_qps_result(msg_delivery_qps)
    
    # Storage: Only offline/undelivered messages
    # Assume 20% of messages are to offline recipients (stored temporarily)
    offline_storage = calculate_storage(
        records_per_day=int(100_000_000_000 * 0.20),  # 20% of 100B messages
        bytes_per_record=500,            # encrypted text message payload
        retention_years=30/365,          # 30 days max retention
        replication_factor=3,
        index_overhead_pct=0.20,
        description="Offline message buffer (temporary)"
    )
    print_storage_result(offline_storage)
    
    # Bandwidth: Text messages
    text_bandwidth = calculate_bandwidth(
        qps=msg_write_qps["avg_qps"] * 0.70,  # 70% text messages
        bytes_per_request=500,
        direction="upload + download",
        description="Text message throughput"
    )
    print_bandwidth_result(text_bandwidth)
    
    # Bandwidth: Image messages  
    image_bandwidth = calculate_bandwidth(
        qps=msg_write_qps["avg_qps"] * 0.20,  # 20% image messages
        bytes_per_request=200_000,         # 200 KB
        direction="upload + download",
        description="Image message throughput"
    )
    print_bandwidth_result(image_bandwidth)
    
    print("\n  KEY INSIGHTS:")
    print("  1. With 1.16M messages/sec, WhatsApp needs massive connection management")
    print("     Each phone maintains a persistent WebSocket connection to WhatsApp servers")
    print("     This requires non-blocking I/O (Erlang/OTP is WhatsApp's secret -- it handles")
    print("     millions of lightweight processes efficiently)")
    print("  2. End-to-end encryption means servers see only encrypted blobs")
    print("     No content scanning, no message storage = cheaper and more private")
    print("  3. The hard problem is PRESENCE (is this user online?) and DELIVERY RECEIPTS")
    print("     Blue checkmarks require complex distributed state management")


def example_uber():
    """
    EXAMPLE 5: Uber Ride Matching and Location Tracking
    
    The problem: Estimate Uber's infrastructure, especially the location tracking system.
    Focus on: GPS location updates (the dominant write workload), ride matching.
    
    Uber scale facts (real data):
      - 19 million rides per day globally
      - 5+ million drivers active at peak
      - Location updated every 4 seconds per active driver
      - Ride matching must complete in <2 seconds for good UX
    """
    print_section("EXAMPLE 5: Uber Location Tracking and Ride Matching")
    print("\n  Assumptions:")
    print("    Rides per day: 19 million globally")
    print("    Active drivers at peak: 5 million")
    print("    Active riders looking for rides at peak: 1 million")
    print("    GPS update frequency: every 4 seconds")
    print("    Location record: 50 bytes (driver_id, lat, lng, timestamp, speed, heading)")
    print("    Location retention: 30 days (for dispute resolution)")
    print("    Average ride duration: 20 minutes")
    
    # Ride requests QPS (the simpler calculation)
    ride_request_qps = calculate_qps(
        dau=8_000_000,                   # ~8M DAU (19M rides / 2.4 rides per active day)
        events_per_user_per_day=2.4,     # 19M rides / 8M riders
        peak_multiplier=3.0,
        description="Ride requests (new rides)"
    )
    print_qps_result(ride_request_qps)
    
    # GPS location updates (the DOMINANT workload)
    # This is the key insight: GPS updates massively outnumber ride events
    driver_gps_qps = calculate_qps(
        dau=5_000_000,                   # 5M active drivers at peak (this is the daily count)
        events_per_user_per_day=60 * 60 * 8 / 4,  # 8 hours active * 60*60/4 = 7,200 updates/driver/day
        peak_multiplier=1.0,             # GPS updates are constant, not bursty
        description="Driver GPS location updates"
    )
    print_qps_result(driver_gps_qps)
    
    # Simpler way to calculate GPS QPS:
    active_drivers_at_peak = 5_000_000
    gps_interval_seconds = 4
    gps_qps_peak = active_drivers_at_peak / gps_interval_seconds
    print(f"\n  Simplified GPS QPS calculation:")
    print(f"    {active_drivers_at_peak:,} drivers / {gps_interval_seconds}s interval")
    print(f"    = {gps_qps_peak:,.0f} location writes per second (PEAK)")
    print(f"    = {gps_qps_peak / 1_000:.0f}K writes/sec")
    
    # Storage: Location history
    location_storage = calculate_storage(
        records_per_day=int(gps_qps_peak * TimeConstants.SECONDS_PER_DAY),
        bytes_per_record=50,             # driver_id + lat + lng + timestamp + speed
        retention_years=30/365,          # 30 days retention
        replication_factor=3,
        index_overhead_pct=0.20,
        description="Driver GPS location history (30 days)"
    )
    print_storage_result(location_storage)
    
    # Geospatial index consideration
    print("\n  GEOSPATIAL INDEXING CHALLENGE:")
    print("    Ride matching requires: 'Find all available drivers within 5km of rider'")
    print("    This is a GEOSPATIAL query -- not supported efficiently by regular B-tree indexes")
    print("    Solutions:")
    print("      1. Geohash: Encode lat/lng as a string; nearby locations have same prefix")
    print("         e.g., geohash('37.7749,-122.4194') = '9q8yy'")
    print("         All drivers in same geohash cell = nearby drivers")
    print("      2. S2 Cells (Google): Hierarchical cell decomposition of Earth")
    print("         Used by Uber internally")
    print("      3. PostGIS: Geospatial extensions for PostgreSQL")
    print("         Supports efficient radius searches with spatial indexes")
    print("    Uber's approach: In-memory geospatial index updated every 4 seconds")
    print("    Redis GEO commands provide O(N+log(M)) geospatial queries")
    
    # Bandwidth: GPS updates
    gps_bandwidth = calculate_bandwidth(
        qps=gps_qps_peak,
        bytes_per_request=50,            # Location payload
        direction="upload (drivers -> server)",
        description="Driver GPS location updates"
    )
    print_bandwidth_result(gps_bandwidth)
    
    print("\n  KEY INSIGHTS:")
    print("  1. GPS UPDATES are the dominant workload -- not ride requests!")
    print(f"     GPS: {gps_qps_peak:,.0f} writes/sec vs Rides: ~220 writes/sec")
    print(f"     GPS has 5,700x more write operations than ride events!")
    print("  2. Ride matching is latency-critical (<2 seconds)")
    print("     Must use in-memory geospatial index, not on-disk database")
    print("  3. Surge pricing requires real-time demand vs. supply analysis")
    print("     (supply = drivers in area, demand = ride requests in area)")
    print("     This is done with approximate geospatial aggregation")


# =============================================================================
# SECTION 5: MAIN RUNNER
# =============================================================================

def main():
    """
    Run all 5 estimation examples and display formatted results.
    
    This script demonstrates the key skill in system design: taking high-level
    user behavior assumptions and translating them into concrete infrastructure
    requirements (QPS, storage, bandwidth).
    
    The pattern for every example:
        1. State assumptions clearly
        2. Calculate write QPS (new data entering system)
        3. Calculate read QPS (queries against existing data)
        4. Calculate storage (how much data we need to keep)
        5. Calculate bandwidth (network capacity needed)
        6. State key architectural insights that emerge from the numbers
    """
    print("\n" + "#" * 70)
    print("  BACK-OF-ENVELOPE ESTIMATION CALCULATOR")
    print("  System Design Fundamentals -- Module 1")
    print("#" * 70)
    print("\n  This calculator demonstrates estimation techniques for 5 real systems.")
    print("  Each example walks through QPS, storage, and bandwidth calculations.")
    print("  The goal is developing intuition for system scale, not perfect precision.")
    
    example_instagram()
    example_twitter()
    example_youtube()
    example_whatsapp()
    example_uber()
    
    print_section("SUMMARY: Scale Intuition Reference")
    print("\n  Use these round numbers to quickly validate your estimates:")
    print()
    print("  THROUGHPUT (per second):")
    print("    Single DB (Postgres): ~5,000-10,000 simple reads/sec")
    print("    Redis (single node):  ~100,000+ operations/sec")
    print("    Kafka (single topic): ~1,000,000+ messages/sec")
    print("    Twitter:              ~75,000 timeline reads/sec peak")
    print("    WhatsApp:             ~1,200,000 message deliveries/sec")
    print("    Uber GPS:             ~1,250,000 location writes/sec peak")
    print()
    print("  STORAGE:")
    print("    1 TB   = 1,000 GB    -- Small company database")
    print("    1 PB   = 1,000 TB    -- Large company database (Instagram daily photos)")
    print("    1 EB   = 1,000 PB    -- Platform-scale object storage (YouTube, Instagram years)")
    print()
    print("  BANDWIDTH:")
    print("    1 Gbps  = 125 MB/sec  -- Single server NIC")
    print("    10 Gbps = 1.25 GB/sec -- Modern datacenter uplink")
    print("    100 Gbps -- Large CDN edge node")
    print("    Tbps    -- Entire platform CDN capacity (Netflix, YouTube)")


if __name__ == "__main__":
    main()
