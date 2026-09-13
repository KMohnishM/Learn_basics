# Module 4: Caching in Distributed Systems

> **Goal**: Understand how caching acts as the primary tool to reduce latency and protect databases at scale. You will learn caching patterns, failure modes, Redis internals, and how to design a multi-layer caching architecture. Before you can build systems that handle millions of users, you must deeply understand how to efficiently store and retrieve temporary data.

---

## Table of Contents

1. [Why Caching? The Math and Memory Hierarchy](#1-why-caching-the-math-and-memory-hierarchy)
2. [Caching Patterns in Depth](#2-caching-patterns-in-depth)
3. [Cache Eviction Policies and Algorithms](#3-cache-eviction-policies-and-algorithms)
4. [The Big Three Caching Failure Modes](#4-the-big-three-caching-failure-modes)
5. [Redis Architecture Deep Dive](#5-redis-architecture-deep-dive)
6. [Multi-Layer Caching Architecture](#6-multi-layer-caching-architecture)
7. [Hot Key & Big Key Problems](#7-hot-key--big-key-problems)
8. [Cache Invalidation Strategies](#8-cache-invalidation-strategies)

---

## 1. Why Caching? The Math and Memory Hierarchy

Caching is the process of storing copies of frequently accessed data in a faster storage layer (usually RAM) to serve future requests faster. In distributed systems, caching is the **primary tool** for reducing database load and decreasing latency.

### 1.1 Cache Hit Ratio and System Latency

The **Cache Hit Ratio** (CHR) is the percentage of requests that are successfully served from the cache. 
A high hit ratio means most of the time we can avoid going to the slower database layer.

`CHR = Cache Hits / (Cache Hits + Cache Misses)`

Let's look at the math of how CHR impacts overall system latency.

Assume:
- Cache read latency (e.g., Redis): 2ms
- Database read latency (e.g., PostgreSQL): 50ms

**Scenario A: 80% Cache Hit Ratio**
- 80% of requests take 2ms
- 20% of requests take 2ms (cache miss) + 50ms (DB read) + 2ms (cache write) = 54ms
- Average Latency = (0.80 * 2ms) + (0.20 * 54ms) = 1.6ms + 10.8ms = **12.4ms**

**Scenario B: 95% Cache Hit Ratio**
- 95% of requests take 2ms
- 5% of requests take 54ms
- Average Latency = (0.95 * 2ms) + (0.05 * 54ms) = 1.9ms + 2.7ms = **4.6ms**

By improving the hit ratio from 80% to 95%, we reduced average latency by **63%** (from 12.4ms to 4.6ms). Furthermore, we reduced the load on our database by **75%** (from 20% of requests hitting the DB to only 5%). At 100,000 requests per second, this means the DB goes from handling 20,000 req/sec to just 5,000 req/sec!

### 1.2 The Cost and Memory Hierarchy

Why don't we just put everything in the cache? Cost and volatility.
RAM is roughly 10x-50x more expensive per GB than SSD storage. 

```text
MEMORY HIERARCHY LATENCY (The Numbers Every Engineer Should Know):

L1 Cache:         0.5 ns
L2 Cache:         7   ns
Main Memory (RAM):100 ns
NVMe SSD:         10,000 ns (10 µs)
Network (same DC):500,000 ns (0.5 ms)
```

Because memory is expensive, caching is a trade-off. You must cache only what is *worth* caching, which is where eviction policies and caching patterns come into play.

### 1.3 When NOT to Cache

Caching introduces **state duplication** and **consistency challenges**. Do not use caching for:
1. **Real-time data**: High-frequency trading prices, real-time gaming state where stale data is fatal.
2. **Financial transactions**: Balances and ledgers where strict ACID compliance and strong consistency are required.
3. **Complex consistency requirements**: If serving stale data for even a millisecond can cause catastrophic business logic failures.
4. **Write-heavy, read-rarely workloads**: Audit logs, telemetry data. The overhead of writing to cache is wasted if the data is never read.

---

## 2. Caching Patterns in Depth

Different access patterns require different caching strategies. Understanding when to apply each is crucial for system design.

### 2.1 Cache-Aside (Lazy Loading)

This is the most common caching pattern. The application is responsible for reading and writing from both the cache and the database.

**Read Flow**:
1. App requests data from Cache.
2. If **Hit**: return data.
3. If **Miss**: App reads from DB, writes to Cache, returns data.

**Write Flow**:
1. App writes data to DB.
2. App invalidates (deletes) the key in Cache.

```text
CACHE-ASIDE ARCHITECTURE:

        [Hit]  +-------+
       +------>| Cache |
       |       +-------+
       |         ^  | [Miss: Write to Cache]
    +-----+      |  |
    | App |------+  |
    +-----+         |
       |            |
       | [Miss: Read DB]
       v            |
    +-------+       |
    |  DB   |-------+
    +-------+
```

```python
# Python Redis Cache-Aside Pattern
import redis
import json
import logging

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_user(user_id):
    cache_key = f"user:{user_id}"
    
    # 1. Try Cache
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            logging.info("Cache hit")
            return json.loads(cached_data)
    except redis.RedisError as e:
        logging.error(f"Cache read failed: {e}")
        # Proceed to DB read if cache is down (Resilience)
        
    # 2. Cache Miss: Read from DB
    logging.info("Cache miss, querying DB")
    user = db.query("SELECT * FROM users WHERE id = %s", user_id)
    if user:
        # 3. Write to Cache with TTL
        try:
            redis_client.setex(cache_key, 3600, json.dumps(user))
        except redis.RedisError as e:
            logging.error(f"Cache write failed: {e}")
            
    return user

def update_user(user_id, data):
    # 1. Update DB synchronously
    db.execute("UPDATE users SET name=%s WHERE id=%s", data['name'], user_id)
    
    # 2. Invalidate Cache
    try:
        redis_client.delete(f"user:{user_id}")
    except redis.RedisError:
        # If delete fails, the cache will be stale until TTL expires.
        # This is why TTLs are critical even when manually invalidating.
        logging.error("Failed to invalidate cache. Data may be stale.")
```

**The Dual-Write Race Condition**:
If Thread A reads from DB (miss) and is about to write to cache, but Thread B updates the DB and deletes the cache key BEFORE Thread A writes to cache, Thread A will write **stale data** to the cache!
*Solutions*: 
- Use TTLs so stale data eventually expires.
- Use a distributed lock when repopulating cache on a miss.

### 2.2 Read-Through

The application only interacts with the cache. The cache layer itself is responsible for reading from the DB on a miss. This is often implemented via ORMs or caching middleware.

- **Pros**: Simplifies application code; no cache-aside boilerplate. The application doesn't need to know the database topology.
- **Cons**: Less flexible; the caching layer must know how to query the DB. It can be difficult to implement for complex joins or specific query optimizations.
- **When to use**: Read-heavy workloads where the data model maps cleanly 1:1 with DB rows.

### 2.3 Write-Through

The application writes to the cache, and the cache synchronously writes to the DB before returning success to the application.

- **Pros**: Data in cache is never stale. No cache invalidation logic needed in the application layer. Read performance is always optimal because data is pre-warmed.
- **Cons**: High write latency. Every write operation incurs the latency of writing to both the cache and the database synchronously (e.g., 2ms + 50ms = 52ms write time).
- **When to use**: Systems where consistency is critical but writes are less frequent than reads, and you cannot tolerate cache misses on read.

### 2.4 Write-Back (Write-Behind)

The application writes ONLY to the cache. The cache returns success immediately and asynchronously flushes writes to the DB in the background, often in batches.

- **Pros**: Extremely fast write performance (RAM speed). Reduces DB load significantly via batching. Can absorb massive write spikes without taking down the backend.
- **Cons**: **Data Loss Risk**. If the cache node crashes before flushing to the DB, data is permanently lost. Implementing retry logic and deduplication on the DB flush is extremely complex.
- **When to use**: Write-heavy workloads where minor data loss is acceptable (e.g., view counters, telemetry data, real-time analytics events).

### 2.5 Write-Around

The application writes directly to the DB, bypassing the cache entirely. Data is only cached on a read miss.

- **Pros**: Prevents cache pollution. If you bulk import 10 million rows, you don't want to evict your entire useful cache just to store records that might not be read for months.
- **Cons**: The first read after a write will always be a cache miss, leading to higher latency for the immediate reader.
- **When to use**: Write-once-read-rarely data, or bulk data imports and background processing tasks.

---

## 3. Cache Eviction Policies and Algorithms

Memory is finite. When a cache reaches its memory limit (e.g., Redis `maxmemory`), it must evict old data to make room for new data. Choosing the right algorithm is essential for maintaining a high hit ratio.

### 3.1 LRU (Least Recently Used)

Evicts the key that was accessed furthest in the past. It assumes that if you haven't accessed a key recently, you probably won't access it soon.

- **Implementation**: O(1) time complexity using a **Doubly-Linked List + HashMap**. The hashmap points to nodes in the linked list. On access, the node is moved to the head of the list. On eviction, the node at the tail is removed.
- **Best for**: Standard web traffic where recently accessed items are most likely to be accessed again (temporal locality), such as user session data or recent news articles.

```text
LRU IMPLEMENTATION CONCEPT:

Head (Newest) <-> Node A <-> Node B <-> Node C <-> Tail (Oldest)

HashMap:
{
  "key_A": pointer_to_Node_A,
  "key_B": pointer_to_Node_B,
  "key_C": pointer_to_Node_C
}

Operation: GET key_B
1. Hash lookup for key_B -> O(1)
2. Detach Node B from its current position -> O(1)
3. Attach Node B to Head -> O(1)
Result: Head <-> Node B <-> Node A <-> Node C <-> Tail
```

### 3.2 LFU (Least Frequently Used)

Evicts the key with the lowest access count over time. It assumes that keys accessed often in the past will continue to be accessed often.

- **Implementation**: O(1) time complexity using frequency buckets (doubly-linked lists of nodes with the same frequency) and a hashmap.
- **Best for**: Static asset caching (e.g., CDNs) where some items are globally popular over long periods, regardless of recent traffic spikes (e.g., a popular company logo).
- **Downside**: A once-popular item might stay in cache forever even if it's never accessed again (cache pollution). To solve this, LFU implementations usually include a **decay factor** that periodically halves the frequency counters.

### 3.3 FIFO and MRU

- **FIFO (First In, First Out)**: Evicts the oldest created key, regardless of how often it is accessed. Rarely used as it completely ignores access patterns.
- **MRU (Most Recently Used)**: Evicts the newest key. Counter-intuitive, but extremely useful when the access pattern is a sequential scan over a dataset larger than the cache. It prevents the scan from thrashing the entire cache and preserves the older, potentially useful data.

### 3.4 Redis-Specific Eviction Policies

Redis provides specialized policies configured via the `maxmemory-policy` setting:
- **volatile-lru**: Evicts via LRU *only* among keys that have an expiration set. (Useful when mixing persistent data and cache data).
- **allkeys-lru**: Evicts via LRU among all keys. (Best when Redis is used purely as a cache).
- **volatile-ttl**: Evicts the key with the shortest remaining TTL.
- **noeviction**: Returns an error on write when memory is full. (Use when Redis is your primary DB and data loss is unacceptable).
- **allkeys-lfu** / **volatile-lfu**: Modern additions to Redis for frequency-based eviction.

### 3.5 TTL-based Expiry vs Active Eviction

How does Redis actually delete expired keys without scanning the entire dataset?
- **Passive expiry**: Redis only deletes a key when it is accessed by a client and found to be expired.
- **Active eviction**: Redis runs a background loop (10 times per second) that randomly samples a subset of keys with an associated TTL and deletes the expired ones. If a high percentage of the sample is expired, it samples again. This probabilistic approach prevents memory leaks from expired keys that are never accessed again, without blocking the main thread.

---

## 4. The Big Three Caching Failure Modes

Caching systems fail in spectacular, cascading ways. When designing a system, you must explicitly defend against these three specific failure modes, or your database will inevitably melt under load.

### 4.1 Cache Stampede (Thundering Herd)

**The Problem**: A highly popular key (e.g., the homepage configuration, or a viral celebrity profile) expires or is evicted. Simultaneously, 10,000 requests arrive for that key. They all get a cache miss. All 10,000 threads simultaneously hit the database to compute the exact same value. The database CPU hits 100% and crashes.

**Solutions**:
1. **Mutex Lock**: On a cache miss, only ONE thread is allowed to acquire a distributed lock (e.g., Redis `SETNX`) to query the DB and update the cache. The other 9,999 threads sleep for 50ms and retry the cache.
2. **Probabilistic Early Expiry (XFetch Algorithm)**: Before a key actually expires, a background thread randomly decides to refresh it based on how close it is to expiration. This ensures the key is refreshed *before* the stampede can happen.
3. **Background Refresh**: The cache never expires from the user's perspective (no TTL). A background cron job constantly queries the DB and updates the cache proactively.

### 4.2 Cache Penetration

**The Problem**: Attackers request keys that do NOT exist in the database (e.g., `/api/users/999999999`). The cache misses, the DB is queried, returns null, and because the app typically doesn't cache `null` values, nothing is added to the cache. The attacker can continuously hammer the DB with useless queries, bypassing the cache entirely.

**Solutions**:
1. **Null Caching**: If the DB returns null, explicitly cache the `null` or empty value with a short TTL (e.g., 60 seconds). Future requests for the non-existent key will hit the cache.
2. **Bloom Filters**: A highly memory-efficient probabilistic data structure placed *before* the cache.
   - It can definitively answer: "This key is NOT in the DB".
   - It can probabilistically answer: "This key MIGHT be in the DB".
   - **Math**: With just 10 bits per item and 7 hash functions, a Bloom filter can achieve a false positive rate of ~1% while using mere megabytes of RAM for millions of keys.

```text
BLOOM FILTER CONCEPT:

[Bit Array: 0 0 0 0 0 0 0 0 0 0]

Insert "user:123":
Hash1("user:123") % 10 = 2
Hash2("user:123") % 10 = 7
Set bits 2 and 7 to 1.
[Bit Array: 0 0 1 0 0 0 0 1 0 0]

Check "user:999":
Hash1("user:999") % 10 = 4 (Bit is 0!)
Result: Definitely not in system. Fast reject!

Request Flow:
Request ---> [ Bloom Filter ]
                   |
          +--------+--------+
          |                 |
  [Definitely Not]     [Might Exist]
          |                 |
     Return 404       Query Cache/DB
```

### 4.3 Cache Avalanche

**The Problem**: Thousands of cache keys were created at the exact same time with the exact same TTL (e.g., during a midnight batch upload or a cache warm-up script). They all expire at the exact same millisecond. This causes a massive, synchronized wave of cache misses that overwhelms the database.

**Solutions**:
1. **TTL Jitter**: Add random variance to the TTL. Instead of exactly 3600 seconds, use `3600 + random(-300, 300)`. This spreads the expiries evenly over a 10-minute window, smoothing out the DB load.
2. **Staggered Warming**: Warm up the cache gradually over time, not all at once in a massive burst.
3. **Circuit Breakers**: Protect the DB at all costs. If DB latency spikes due to an avalanche, fast-fail requests (return a 503 error) rather than queuing them and crashing the DB completely.

---

## 5. Redis Architecture Deep Dive

Redis (Remote Dictionary Server) is an in-memory, key-value data store. A single Redis node can handle **100,000+ operations per second** with sub-millisecond latency. Understanding its internals is crucial for scaling.

### 5.1 Data Structures

Redis is not just a key-value store; it is a data structures server:
- **Strings**: Text, binary data (up to 512MB), or integers. Supports atomic operations like `INCR` (perfect for rate limiting).
- **Hashes**: Maps between string fields and string values (like a flat JSON object). Great for storing user profiles without needing to serialize/deserialize the whole object.
- **Lists**: Doubly-linked lists. Good for queues or maintaining a timeline of recent items (`LPUSH`, `RPOP`, `LTRIM`).
- **Sets**: Unordered collections of unique strings. Good for tags, unique visitors, or finding mutual friends (`SINTER` for set intersection).
- **Sorted Sets (ZSET)**: Sets ordered by a float score. 
  - **Internals**: Implemented using a dual structure: a **Skip List** (for fast range queries) and a **Hash Table** (for fast O(1) lookups by element). Perfect for leaderboards or time-series data.
- **HyperLogLog**: A probabilistic data structure used for estimating the cardinality (number of unique elements) of a set.
  - **Math**: Uses only 12KB of memory to count millions of unique items with a standard error of ~0.81%. It relies on observing the maximum number of leading zeros in the binary representation of hashed values.
- **Pub/Sub & Streams**: Real-time message brokering and event streaming capabilities.

```bash
# Redis CLI Example: Leaderboard with Sorted Sets
> ZADD global_leaderboard 1500 "Player_A"
(integer) 1
> ZADD global_leaderboard 2000 "Player_B"
(integer) 1
> ZADD global_leaderboard 1750 "Player_C"
(integer) 1

# Get top 2 players and their scores (O(log(N) + M) time complexity)
> ZREVRANGE global_leaderboard 0 1 WITHSCORES  
1) "Player_B"
2) "2000"
3) "Player_C"
4) "1750"

# HyperLogLog Example: Counting Unique Daily Visitors efficiently
> PFADD daily_visitors:2023-10-01 "user123" "user456" "user789"
(integer) 1
> PFCOUNT daily_visitors:2023-10-01
(integer) 3
```

### 5.2 The Single-Threaded I/O Model

For command execution, Redis is strictly single-threaded. 
**Why is it so incredibly fast if it only uses one core?**
1. **Memory Speed**: It operates entirely in RAM. RAM access takes ~100ns, whereas a fast SSD takes ~10,000ns.
2. **I/O Multiplexing**: It uses an efficient Event Loop with non-blocking I/O multiplexing (using OS primitives like `epoll` on Linux or `kqueue` on macOS) to handle thousands of concurrent network connections.
3. **No Lock Contention**: Because it processes exactly one command at a time sequentially, there are no race conditions, no deadlocks, and absolutely no context switching overhead between threads. 

*(Note: Modern Redis 6+ introduced I/O threads to handle network reads and writes in parallel, but the actual command execution remains strictly single-threaded to preserve atomicity).*

### 5.3 Redis Persistence

Data in RAM is volatile; a power loss means total data loss. Redis offers two persistence mechanisms to write data to disk:
1. **RDB (Redis Database Snapshot)**: Point-in-time binary snapshots saved to disk periodically (e.g., "save every 5 minutes if at least 100 keys changed"). 
   - **Pros**: Compact file size, very fast to load on restart.
   - **Cons**: You will lose all data written since the last snapshot if a crash occurs.
2. **AOF (Append-Only File)**: Logs every write operation to disk sequentially (similar to a database WAL). 
   - **Pros**: Much safer, can be configured to fsync every second (max 1 second data loss).
   - **Cons**: The file grows infinitely and requires periodic background rewriting (compaction), and is slower to replay on restart.
3. **Hybrid (RDB + AOF)**: The modern standard (default in Redis 5+). It uses an RDB snapshot for fast loading of the base state, and appends AOF logs for the operations that happened after the snapshot was taken.

### 5.4 Redis High Availability and Scaling

A single Redis node is a single point of failure.

**Redis Sentinel (High Availability)**:
A cluster of lightweight monitoring nodes that watch a Master Redis instance and its Replicas. If the Master node dies, the Sentinels agree on the failure (quorum), automatically promote a Replica to be the new Master, and update the clients with the new IP address.

**Redis Cluster (Horizontal Scaling)**:
When your dataset exceeds the RAM of a single machine (e.g., 500GB), you must shard the data across multiple machines.
- **Hash Slots**: Redis Cluster does not use consistent hashing. Instead, it uses exactly **16,384 hash slots**. The key is hashed using `CRC16(key) % 16384` to determine its slot.
- **Topology**: Every Master node in the cluster is responsible for a subset of the 16,384 slots. 
- **Gossip Protocol**: There is no central coordinator (like ZooKeeper). Nodes communicate via a gossip protocol (`CLUSTER MEET`, `PING`, `PONG`) to maintain cluster state, detect failures, and agree on the topology.

```text
REDIS CLUSTER HASH SLOTS ARCHITECTURE:

Hash Space: 0 to 16383

[ Master Node A ] -> Manages Slots 0 to 5460
       |--> (Replica A1, Replica A2)

[ Master Node B ] -> Manages Slots 5461 to 10922
       |--> (Replica B1, Replica B2)

[ Master Node C ] -> Manages Slots 10923 to 16383
       |--> (Replica C1, Replica C2)

Client Operation: SET "user:123" "data"
1. Client calculates: CRC16("user:123") % 16384 = Slot 4021
2. Client sends request to Node B.
3. Node B replies: "-MOVED 4021 [Node A IP]"
4. Client transparently redirects the request to Node A.
```

### 5.5 Redis vs Memcached

Historically, Memcached was the king of caching, but Redis has largely replaced it in modern architectures.

| Feature | Redis | Memcached |
|---------|-------|-----------|
| **Data Types** | Strings, Hashes, Lists, Sets, ZSETs, HLL | Strings (Binary blobs) only |
| **Persistence** | RDB Snapshots, AOF | None (pure volatile cache) |
| **Threading Model**| Single-threaded execution | Multi-threaded (can utilize multiple cores) |
| **High Availability**| Built-in Sentinel & Cluster sharding | None natively (requires third-party proxies) |
| **Scripting** | Lua scripting for complex atomic ops | None |
| **Memory Mgmt** | Jemalloc, exact memory limits | Slab allocator (can lead to fragmentation) |

---

## 6. Multi-Layer Caching Architecture

A robust, enterprise-grade distributed system doesn't just have one cache. It employs a multi-tiered caching strategy to stop traffic as close to the user as possible.

```text
MULTI-LAYER CACHING STACK AND LATENCY:

[ User Browser ] -> Local Cache
       |            Latency: 0ms (Never hits the network)
       v
[ CDN / Edge ]   -> Cloudflare, AWS CloudFront, Fastly
       |            Latency: 10-30ms (Served from local city POP)
       v
[ Reverse Proxy ]-> Nginx, Varnish Cache, HAProxy
       |            Latency: 1-2ms (Inside your datacenter)
       v
[ App Server L1 ]-> In-Memory: Caffeine (Java), functools.lru_cache (Python)
       |            Latency: Nanoseconds (No network hop)
       v
[ Distributed L2]-> Redis Cluster, Memcached
       |            Latency: 1-3ms (Network hop to cache tier)
       v
[ Database ]     -> PostgreSQL, MySQL, Cassandra
                    Latency: 10-100ms (Disk I/O, Complex joins)
```

1. **Browser Cache (Client-side)**: 
   Controlled via `Cache-Control` HTTP headers returned by your server.
   - `max-age=3600`: Cache the response for 1 hour locally.
   - `no-cache`: The browser must revalidate the ETag with the server before using the cached version.
   - `no-store`: Absolutely never cache this (used for sensitive financial data).
   - `stale-while-revalidate`: Serve the stale local data instantly, but fetch an update in the background for next time.
2. **CDN (Content Delivery Network)**: 
   Caches static assets (images, JS, CSS, videos) at edge nodes (POPs) geographically close to users. CDNs act as a massive shield; a well-configured CDN can offload 90% of your total bandwidth and request volume. CDNs can be pull-based (they fetch from origin on miss) or push-based (you upload assets to them proactively).
3. **Reverse Proxy Cache**: 
   Nginx can be configured to cache dynamic HTTP responses based on URL paths and headers. If the response is in Nginx, the request never even reaches your application code (saving expensive CPU cycles).
4. **Application L1 Cache**: 
   In-process memory inside the application runtime. Blazing fast, but the state is localized to a single app server instance. If you have 50 app servers, you might cache the same data 50 times. Great for small, highly-accessed static lookups (e.g., country codes).
5. **Distributed L2 Cache**: 
   Redis or Memcached. Provides a single, shared, coherent state across all application servers.

---

## 7. Hot Key & Big Key Problems

These are the two most common operational issues when running a Redis cluster at scale.

### 7.1 The Hot Key Problem

**Issue**: A single key (e.g., a breaking news article, or a flash sale configuration) receives millions of requests per second. Because it is a single key, the CRC16 hash routes it to a single hash slot, hitting a **single Redis node**. That single node's CPU maxes out and dies, while the rest of the cluster sits idle.

**Solutions**:
1. **Key Splitting (Sharding)**: Append a random integer suffix to the key (`news:99#1`, `news:99#2`, up to `#100`). This distributes the data copies across 100 different hash slots (and thus multiple nodes). The application randomly selects a suffix when reading.
2. **Local L1 Caching**: The application server detects a hot key and caches it in its own local RAM (e.g., for just 3 seconds). This absorbs 99.9% of the traffic and drastically reduces calls to the Redis tier.
3. **Read Replicas**: Scale out Redis read replicas and route read traffic to them, spreading the CPU load.

### 7.2 The Big Key Problem

**Issue**: A single key contains a massive amount of data (e.g., a Set with 10 million user IDs, or a 500MB JSON string). 
- Reading it chokes the network bandwidth. 
- Deleting it using `DEL` blocks the single Redis execution thread for seconds, causing timeouts for all other clients waiting to execute commands.

**Solutions**:
1. **Split the Data**: Break the large JSON string into smaller chunks, or shard the massive Set into 100 smaller Sets (`set:users:0` to `set:users:99`).
2. **Lazy Deletion**: **Never** use `DEL` on a big key in production. Use `UNLINK`, which deletes the key reference instantly (returning control to the thread) but frees the actual memory asynchronously in a background I/O thread.
3. **Iterative Retrieval**: **Never** use `KEYS *` or `SMEMBERS` on large collections in production. Use the `SCAN` family of commands (`SSCAN`, `HSCAN`, `ZSCAN`), which act as cursors to return data in small, manageable batches without blocking the thread.

---

## 8. Cache Invalidation Strategies

"There are only two hard things in Computer Science: cache invalidation and naming things." - Phil Karlton

How do you ensure the cache drops stale data exactly when the database changes?

1. **TTL-based (Time To Live)**: 
   The simplest approach. Set a TTL on everything. If data is stale, it will fix itself eventually when the TTL expires. Provides **Eventual Consistency**. Best for data that isn't highly sensitive to staleness (like comment counts).

2. **Write-Through / Cache-Aside Invalidation**: 
   The application explicitly deletes the cache key immediately after writing to the DB. 
   - *Problem*: Prone to race conditions and edge cases. What if the DB transaction succeeds but the network call to delete the Redis key times out? The cache is now permanently stale until someone manually clears it.

3. **Event-Driven via CDC (Change Data Capture)**: 
   The most robust, enterprise-grade solution.
   - Use a tool like **Debezium** to monitor the database's internal transaction log (binlog in MySQL, WAL in PostgreSQL).
   - When a row changes, Debezium instantly captures it and pushes an event to an event bus (e.g., **Kafka**).
   - A dedicated Cache Invalidation Consumer microservice reads the Kafka topic and deletes the corresponding key in Redis.
   - *Why this is better*: It completely decouples invalidation from application logic. It guarantees delivery (Kafka will retry until successful). It even catches manual DB edits done by DBAs directly in the database!

4. **Versioned Cache Keys**: 
   Instead of deleting keys, append a version number to the key name (`user:123:v2`). When the user updates their profile, update the database, increment a version counter in the database, and have the application request `user:123:v3`. The old `v2` key naturally expires via TTL, and you never have to explicitly issue a `DEL` command. This avoids the race conditions associated with explicit deletion.
