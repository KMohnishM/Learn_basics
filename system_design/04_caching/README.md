# Module 4: Caching Strategies

Databases are slow (they read from disk, perform complex joins, and ensure ACID compliance). As your system scales, you cannot hit the database for every single request. You need a cache.

A cache is a temporary storage layer (usually entirely in memory/RAM) that serves data orders of magnitude faster than a database. The industry standard is **Redis** (Remote Dictionary Server).

## 1. Caching Patterns (How data gets into the cache)

### Cache-Aside (Lazy Loading)
The most common pattern.
- **Read**: The app asks the cache. If it's a "Hit", return data. If it's a "Miss", the app queries the DB, stores the result in the cache, and returns it.
- **Write**: The app writes directly to the DB, and usually *invalidates* (deletes) the cache entry.
- **Pros**: Only requested data is cached. Cache failures don't break the app (it just falls back to DB).
- **Cons**: First request is slow (cache miss). Data can become stale.

### Write-Through
- **Write**: The app writes data to the cache AND the database simultaneously.
- **Pros**: Data in the cache is never stale. Reads are always fast.
- **Cons**: Every write operation takes a "write penalty" (latency of writing to two systems). Cache is filled with data that might never be read.

### Write-Back (Write-Behind)
- **Write**: The app writes ONLY to the cache. The cache asynchronously flushes the data to the DB later.
- **Pros**: Insanely fast write performance.
- **Cons**: High risk of data loss. If the cache node crashes before flushing, the data is gone forever.

## 2. Cache Eviction Policies
RAM is expensive. You cannot cache everything. When the cache is full, it must evict old data to make room for new data.
- **LRU (Least Recently Used)**: Evict the data that hasn't been accessed in the longest time. (Most common).
- **LFU (Least Frequently Used)**: Evict the data that is accessed the least often.
- **FIFO (First In, First Out)**: Evict the oldest data, regardless of how often it's used.

## 3. The Big Three Caching Problems

### Cache Stampede (Thundering Herd)
Imagine a massive celebrity tweets a link to a specific product. The cache entry for that product expires (TTL runs out) exactly at that moment. Suddenly, 10,000 requests hit the cache, get a "Miss", and ALL 10,000 requests query the database at the exact same millisecond. The database crashes.
- **Solution**: Locking (only the first request goes to the DB, others wait), or Probabilistic Early Expiry (background job refreshes the cache *before* it expires).

### Cache Penetration
An attacker queries your API for `user_id=-1`, `user_id=-2`, etc. These don't exist in the cache (Miss), and they don't exist in the DB. The attacker bypasses the cache entirely and hammers your database.
- **Solution**: Cache empty results (store `user_id=-1: null` in the cache). Or, use a **Bloom Filter** (a highly memory-efficient probabilistic data structure that can tell you with 100% certainty if an item is NOT in the database, without hitting the database).

### Cache Avalanche
You deploy a new version of your app and restart your Redis cluster. The cache is totally empty. Or, you set the exact same TTL (e.g., 60 minutes) for 1 million keys simultaneously. When they all expire at minute 61, your database is crushed by a sudden spike in traffic.
- **Solution**: Add "jitter" to your TTLs. Instead of exactly 60 minutes, set TTL to `60 minutes + random(0, 5) minutes`. 

## 4. Redis Data Structures
Redis is not just a key-value store; it's a data structures server.
- **Strings**: Basic key-value (caching JSON responses, session tokens).
- **Hashes**: Maps of fields to values (storing user objects).
- **Lists**: Linked lists (activity feeds, simple queues).
- **Sets**: Unordered unique items (who is currently online).
- **Sorted Sets (ZSET)**: Sets ordered by a score (leaderboards, rate limiting).
- **Pub/Sub**: Fire-and-forget message broadcasting.

---
## Next Steps
Go to `labs/` to see exactly how much faster an API becomes when you implement the Cache-Aside pattern with Redis!
