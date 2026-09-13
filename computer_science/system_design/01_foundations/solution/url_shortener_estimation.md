# URL Shortener Estimation -- Complete Solution

## Assumptions

Before calculating anything, we explicitly state our assumptions.
These are the numbers we'll defend in an interview setting.

| Assumption | Value | Reasoning |
|------------|-------|-----------|
| Daily Active Users (DAU) | 100 million | Given in requirements |
| % of DAU creating URLs daily | 1% | Most users are clicking links, not creating them |
| URL creations per creating user | 3 | Power users create multiple campaigns |
| Avg clicks per URL per day | 30 | Popular URLs get many clicks; most get few (long tail) |
| % of registered users checking analytics | 5% | Most set-and-forget |
| Original URL average length | 200 bytes | Mix of short and very long URLs |
| Replication factor | 3 | Standard 3-replica setup |
| Retention | Forever (unless user sets expiry) | Given in requirements |
| Estimation window | 5 years | Standard capacity planning horizon |
| Peak multiplier | 2x (redirects), 3x (creations) | Redirects are steady; marketing campaigns are bursty |

---

## Part 1: QPS Calculations

### 1a -- Write QPS (URL Creation)

```
URL creators per day = 100M DAU * 1% = 1,000,000 users/day
URL creations per day = 1M * 3 URLs/user = 3,000,000 URLs/day

Average write QPS = 3,000,000 / 86,400 sec/day
                 = 34.7 writes/sec
                 ≈ 35 writes/sec

Peak write QPS = 35 * 3x (marketing campaigns spike traffic)
              = 105 writes/sec
              ≈ ~100 writes/sec (round numbers are fine for estimation)
```

### 1b -- Read QPS (URL Redirect)

```
Clicks per day = 3M URLs created/day * 30 avg clicks/URL/day
              = 90,000,000 clicks/day (90 million)

But wait -- we also need clicks on URLs created in PREVIOUS days.
Assumption: average URL is clicked for 1 month (30 days) before dying out.
Total active URLs = URLs created/day * 30 days = 3M * 30 = 90M active URLs
Clicks per day = 90M active URLs * average 1 click/URL/day (distributed over time)
              = 90M clicks/day

Average read QPS (redirects) = 90,000,000 / 86,400
                              = 1,041 reads/sec
                              ≈ 1,000 reads/sec

Peak read QPS = 1,000 * 2x = 2,000 reads/sec

Read:Write ratio = 1,000 / 35 ≈ 29:1

This is a READ-HEAVY system (which is typical for URL shorteners).
The design must optimize for fast reads (redirects), not writes.
```

### 1c -- Analytics Read QPS

```
Registered users = assume 30% of DAU = 30M registered users
% checking analytics daily = 5% = 1.5M analytics reads/day

Average analytics QPS = 1,500,000 / 86,400 = 17 reads/sec (very low)
Peak analytics QPS = 17 * 2x = 34 reads/sec

Key insight: Analytics is a minor workload compared to redirects.
We can serve analytics from read replicas or even batch-computed aggregates.
```

---

## Part 2: Storage Calculations

### 2a -- URLs Table

**Schema design**:
```sql
CREATE TABLE urls (
    id           BIGINT          -- 8 bytes
    short_code   VARCHAR(7)      -- 7 bytes (6 chars + null terminator in Postgres = 6-10 bytes)
    original_url TEXT            -- average 200 bytes
    user_id      BIGINT          -- 8 bytes (NULL = 0 bytes in some DBs)
    created_at   TIMESTAMPTZ     -- 8 bytes
    expires_at   TIMESTAMPTZ     -- 8 bytes (often NULL = 0)
    click_count  BIGINT          -- 8 bytes
    is_active    BOOLEAN         -- 1 byte
    -- Postgres row overhead: ~23 bytes
    -- TOTAL PER ROW: ~270 bytes, round to 300 bytes
);
```

**Size estimate**:
```
Row size: ~300 bytes

URLs created per day: 3,000,000
URLs created over 5 years: 3M * 365 * 5 = 5,475,000,000 (5.475 billion)

Raw storage: 5.475B * 300 bytes = 1,642,500,000,000 bytes = 1.64 TB
With replication (3x): 1.64 TB * 3 = 4.93 TB
With index overhead (30%):
  - Index on short_code (primary lookup): ~300 bytes * 5.475B = 1.64 TB per index
  - Index on user_id: another ~200 bytes per record for the index
  - Total index overhead ≈ 40% of table size
  4.93 TB * 1.40 = 6.9 TB

URLs Table Total: ~7 TB over 5 years
```

### 2b -- Analytics Table

**Schema design**:
```sql
CREATE TABLE url_analytics (
    id           BIGINT          -- 8 bytes
    short_code   VARCHAR(7)      -- 7 bytes
    clicked_at   TIMESTAMPTZ     -- 8 bytes
    ip_address   INET            -- 4 bytes (IPv4) or 16 bytes (IPv6), avg 8 bytes
    country_code CHAR(2)         -- 2 bytes
    referrer     VARCHAR(500)    -- average 100 bytes (many are NULL or short)
    user_agent   TEXT            -- average 200 bytes (browser/device strings are long!)
    -- Row overhead: ~23 bytes
    -- TOTAL PER ROW: ~350 bytes, round to 400 bytes
);
```

**Size estimate**:
```
Row size: ~400 bytes

Clicks per day: 90,000,000
Clicks over 5 years: 90M * 365 * 5 = 164,250,000,000 (164 billion)

Raw storage: 164.25B * 400 bytes = 65,700,000,000,000 bytes = 65.7 TB
With replication (3x): 65.7 TB * 3 = 197 TB
With index overhead (20%):
  - Index on (short_code, clicked_at) for analytics queries
  197 TB * 1.20 = 236 TB

Analytics Table Total: ~236 TB over 5 years
```

### 2c -- Comparison

```
URLs table:     ~7 TB over 5 years
Analytics table: ~236 TB over 5 years

The analytics table is ~34x larger than the URLs table!

Why? Because of the click amplification:
  - We create 3M URLs per day
  - We record 90M click events per day
  - That's 30x more analytics rows than URL rows

Implication: The analytics table should NOT live in the same database as the URLs table.
Options:
  a) Separate Postgres database (simpler, but still limited)
  b) ClickHouse or BigQuery for analytics (columnar DB, much better for aggregation queries)
  c) Stream click events to Kafka -> aggregate in batch -> store only aggregates
     (Most cost-effective: store pre-aggregated stats, not raw click events)
```

---

## Part 3: Bandwidth Calculations

### 3a -- Incoming Bandwidth (URL Creation)

```
Request payload per URL creation:
  - HTTP headers: ~500 bytes
  - Request body (the JSON with original_url): ~250 bytes  
  - Total: ~750 bytes per request

Average write QPS: 35/sec
Incoming bandwidth = 35 req/sec * 750 bytes/req = 26,250 bytes/sec
                   = 0.21 Mbps (megabits per second)

Peak (3x): 0.63 Mbps

This is TINY. URL creation bandwidth is negligible.
```

### 3b -- Outgoing Bandwidth (Redirects)

```
Redirect response payload:
  - HTTP response headers: ~500 bytes
  - HTTP status line: ~30 bytes
  - Location header: 200 bytes (the original URL)
  - Other headers (cache-control, cors, etc.): ~200 bytes
  - Total: ~930 bytes per redirect response, round to 1000 bytes

Average read QPS: 1,000/sec
Outgoing bandwidth = 1,000 req/sec * 1,000 bytes/req = 1,000,000 bytes/sec
                   = 8 Mbps

Peak (2x): 16 Mbps

This is still relatively small! Even at peak, 16 Mbps is handled easily by a single server NIC.
```

### 3c -- Bandwidth Analysis

```
Incoming (URL creation): ~0.63 Mbps peak
Outgoing (redirects):    ~16 Mbps peak

The redirect bandwidth is ~25x larger than creation bandwidth.

But BOTH are extremely small compared to typical server capacity (1-10 Gbps NICs).

Bandwidth is NOT the bottleneck for a URL shortener.
The bottleneck is LATENCY (50ms p99 requirement for redirects).

This tells us:
  - We don't need a CDN for bandwidth reasons
  - We DO need caching to hit the 50ms latency requirement
  - The system is fundamentally a fast key-value lookup system
  - The "short_code -> original_url" mapping fits entirely in Redis:
    90M active URLs * 300 bytes each = 27 GB of Redis memory (affordable!)
```

---

## Part 4: Short Code Generation

### 4a -- Base62 Capacity Analysis

```
Base62 alphabet: a-z (26) + A-Z (26) + 0-9 (10) = 62 characters
6-character Base62 codes: 62^6 = 56,800,235,584 (~56.8 billion unique codes)

URL creation rate: 3M/day
Annual URL creation: 3M * 365 = 1,095,000,000 (~1.1 billion/year)
Years until code exhaustion: 56.8B / 1.1B = ~52 years

Conclusion: 6 characters is MORE than sufficient for a URL shortener.
Even at 10x our assumed scale, we'd have 5+ years before needing 7 characters.

If we ever need more: 7-character Base62 gives 62^7 = 3.5 TRILLION codes.
```

### 4b -- Short Code Generation Strategy Trade-offs

**Option 1: Random Base62 (randomly pick 6 characters, check DB for collisions)**

```
Pros:
  + Simple implementation
  + No central coordinator needed (can be done on any app server)
  + Short codes are unpredictable (hard to enumerate/guess other users' links)
  + Distributes load evenly across the keyspace

Cons:
  - Collision probability increases as the space fills up
    At 50% fill (~28B URLs): collision probability per attempt = 50%
    Need multiple retries, adding latency
  - Requires a DB read to check for collision before every write
    (Can use probabilistic uniqueness: generate multiple codes, pick first unused)
  - Birthday paradox: collisions happen sooner than intuition suggests
    With 56.8B codes and 1% fill probability: collision rate = 0.57%

Best for: Systems where unpredictability/security matters (user-facing short codes)
```

**Option 2: MD5/SHA1 Hash of Original URL, Take First 6 Characters**

```
Pros:
  + Deterministic: same URL always gets same code
  + Can deduplicate: if user submits same URL twice, return existing short code
  + No collision check needed against DB (hash is deterministic)

Cons:
  - Hash COLLISIONS: Two different URLs could produce the same 6-char prefix!
    MD5 collision probability for 6 chars: much higher than random
  - If URL is the same but user is different, they get the same short code
    (This might be a feature or a bug depending on requirements)
  - The original URL is now identifiable from the hash (privacy concern)
  - Hash truncation increases collision risk vs. full hash

Best for: Systems where deduplication is important (e.g., bookmark managers)
```

**Option 3: Auto-increment Integer Converted to Base62**

```
Process:
  1. Each new URL gets a globally sequential integer ID (1, 2, 3, ...)
  2. Convert that integer to Base62: 
     ID 1 -> "1"
     ID 100 -> "1c"  
     ID 1,000,000 -> "4c92" (4 chars)
     ID 56,800,000,000 -> "zzzzzz" (6 chars, max)

Pros:
  + Guaranteed no collisions (sequential, never repeats)
  + Short initial codes (URL ID 1 = "1", not 6 chars)
  + Simple, deterministic

Cons:
  - Codes are SEQUENTIAL and enumerable: someone with code "4c92" can guess 
    that "4c91" and "4c93" are other users' URLs (privacy concern!)
  - Requires a CENTRALIZED counter or distributed ID generator (Snowflake IDs)
    Centralized counter = single point of failure + bottleneck
  - Distributed ID generation (Twitter Snowflake, Facebook ULID) solves SPOF 
    but adds complexity
  - Leaks business information: code length reveals roughly how many URLs exist

Best for: Internal systems where security isn't a concern; high-throughput systems
          that need guaranteed uniqueness without collision checks
```

**Recommendation for Interview**:
```
Use Option 1 (Random Base62) for most URL shorteners because:
- User-facing security (unpredictable codes)
- At our scale (35 writes/sec), collision rate is negligible for decades
- Simple implementation without SPOF

For very high write scale (>100K/sec):
- Use Snowflake IDs (time-sorted, distributed, no collisions, no coordinator)
- Convert Snowflake ID to Base62 for the short code
```

---

## Part 5: Architecture Implications

### 5a -- Latency Requirement (50ms p99)

```
Can we query Postgres for every redirect?

Postgres lookup latency: 1-10ms for an indexed query (single row by primary key)
This seems fast enough, but consider:
  - Network latency from app server to DB: 0.5ms (same DC)
  - Connection pool wait time under load: 0-50ms (depends on pool size)
  - At 2,000 peak req/sec: Postgres can handle this, but barely
  - Any DB maintenance, vacuum, or slow query can spike latency to >50ms

The 50ms p99 requirement means 1 in 100 requests can take up to 50ms.
Going to Postgres for every request risks missing this SLO during any DB load spike.

Answer: We MUST use Redis as a read-through cache.

Caching strategy: Cache-Aside (Lazy Loading)
  1. On redirect request: Check Redis for short_code -> original_url
  2. If Redis HIT (expected 99%+ of the time): Return immediately (~1ms)
  3. If Redis MISS: Query Postgres, store in Redis, return original_url

Redis latency: <1ms for a GET operation
This makes the p99 requirement trivially achievable for cached requests.

Cache sizing:
  - Active URLs (clicked in last 30 days): 90M active URLs
  - Each Redis entry: short_code (10 bytes) + original_url (200 bytes) + overhead = ~300 bytes
  - Total Redis memory: 90M * 300 bytes = 27 GB of Redis data
  - With Redis overhead: ~35-40 GB Redis instance
  - This fits on a single Redis instance (r6g.2xlarge on AWS = 52 GB, $0.48/hr)
  - For high availability: Redis Cluster with 3 primary + 3 replica nodes

Cache TTL:
  - Set TTL of 7 days for each cached URL
  - Hot URLs stay cached (TTL refreshes on access if using Redis GETEX)
  - Cold URLs expire automatically, freeing memory

Where should the cache live?
  - Redis cluster in the SAME datacenter/AZ as app servers (minimize latency)
  - Not the CDN (CDN can't run Redis, and redirects need authentication checking)
  - In-memory cache on app servers (L1 cache before Redis):
    - Small (100MB), very hot URLs (~10K most popular)
    - Adds another layer for truly viral URLs
    - Expires after 1-5 minutes (slightly stale is OK for popular links)
```

### 5b -- Analytics Database Choice

```
For storing individual click events:
  - Table grows to 236 TB over 5 years
  - Postgres can handle this but requires careful partitioning and archiving
  - Better choice: Apache Kafka + ClickHouse

  Architecture:
    Click event -> Kafka (durable, high-throughput event log)
    Kafka Consumer -> ClickHouse (columnar DB, optimized for analytics)
    
    ClickHouse advantages:
      - Columnar storage: 10-50x compression for analytics data
      - 236 TB raw -> 5-25 TB in ClickHouse (column compression)
      - Query speed: Scans billions of rows per second for aggregations
      - Native Kafka integration
    
For generating aggregate reports (clicks per day, per country):
  - ClickHouse can answer these ad-hoc
  - For dashboards: Pre-aggregate daily summaries
    CREATE MATERIALIZED VIEW daily_stats AS
    SELECT short_code, toDate(clicked_at) as date, 
           count() as clicks, uniqExact(ip_address) as unique_visitors,
           country_code
    FROM url_analytics GROUP BY short_code, date, country_code
  - Materialized views update in real-time as events arrive
  - Dashboard queries scan millions of rows, not billions
```

### 5c -- 99.99% Availability Architecture

```
99.99% availability = 52.6 minutes of downtime per YEAR = 4.4 minutes per MONTH

This requires:

1. No single points of failure at ANY layer:
   - Multiple app servers (auto-scaling group, minimum 3)
   - Load balancer (AWS ALB/NLB is inherently highly available)
   - Redis Cluster (primary + replica in different Availability Zones)
   - Postgres Primary + Read Replica in different AZs
   - Postgres automatic failover (via RDS Multi-AZ or Patroni)

2. Zero-downtime deployments:
   - Rolling deployments: deploy to 1 server at a time, health check, repeat
   - Blue-green deployments for major changes
   - Never take the whole service down for maintenance

3. Automatic failover:
   - Redis: Cluster mode with automatic failover (Sentinel or Redis Cluster)
   - Postgres: RDS Multi-AZ with automatic failover in <60 seconds
   - App servers: Health checks + automatic restart on failure

4. Multi-AZ (not multi-region):
   - For 99.99%, multi-AZ within one region is sufficient
   - Multi-region adds enormous complexity and is needed for 99.999%
   - Same-region latency: <1ms between AZs (negligible impact)

Minimum architecture for 99.99%:
   
   [Route 53 DNS]
        |
   [ALB Load Balancer] (AWS handles HA)
        |
   [App Server ASG] (3 minimum, across 3 AZs)
   /          \
[Redis Cluster]  [RDS Postgres Multi-AZ]
(3 primary + 3   (Primary in AZ-a)
 replicas across   (Standby in AZ-b, auto-failover)
 3 AZs)
```

---

## Summary Table

| Metric | Value |
|--------|-------|
| Daily Active Users | 100 million |
| URLs created per day | 3 million |
| Clicks (redirects) per day | 90 million |
| **Write QPS (average)** | **35 req/sec** |
| **Write QPS (peak)** | **105 req/sec** |
| **Read QPS (average)** | **1,000 req/sec** |
| **Read QPS (peak)** | **2,000 req/sec** |
| **Read:Write Ratio** | **~29:1** |
| Analytics QPS (average) | 17 req/sec |
| URLs storage (5 years) | ~7 TB |
| Analytics storage (5 years) | ~236 TB |
| **Total storage (5 years)** | **~243 TB** |
| Incoming bandwidth | ~0.63 Mbps peak |
| **Outgoing bandwidth** | **~16 Mbps peak** |
| Short code capacity (6-char Base62) | 56.8 billion |
| Years until code exhaustion | ~52 years |
| Redis cache size needed | ~35-40 GB |

## Key Insights from the Numbers

1. **This is overwhelmingly read-heavy (29:1 ratio)**: Every design decision should optimize for fast reads
2. **The analytics table is 34x larger than the URLs table**: They should be in separate databases
3. **Bandwidth is NOT a bottleneck**: Even 16 Mbps peak is trivial -- latency is the challenge
4. **Redis is non-negotiable**: The 50ms p99 latency requirement cannot be met with DB-only queries at scale
5. **6 characters is plenty**: 56.8 billion codes at 35 writes/sec = 52 years of headroom
6. **99.99% requires multi-AZ**, not necessarily multi-region (saves significant cost and complexity)
