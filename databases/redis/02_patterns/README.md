# Redis Design Patterns and Use Cases

This module covers advanced design patterns and common architectural use cases for Redis in modern distributed systems. 

## 1. Caching Patterns

### Cache-Aside (Lazy Loading)

The cache-aside pattern is the most common way to use Redis. In this pattern, the application code is responsible for checking the cache, falling back to the database if the cache misses, and updating the cache with the new value.

#### Flow:
1. The application receives a request for data.
2. It queries Redis for the data.
3. If the data is found (cache hit), it is returned immediately.
4. If the data is not found (cache miss), the application queries the database.
5. The application writes the retrieved data to Redis with a TTL (Time To Live).
6. The data is returned to the user.

#### Implementation (Python)
```python
import redis
import json
import psycopg2

r = redis.Redis(host='localhost', port=6379, db=0)

def get_user(user_id):
    cache_key = f"user:{user_id}"
    cached_data = r.get(cache_key)
    
    if cached_data:
        return json.loads(cached_data)
        
    # Cache miss
    conn = psycopg2.connect("dbname=app user=postgres")
    cur = conn.cursor()
    cur.execute("SELECT id, name, email FROM users WHERE id = %s", (user_id,))
    row = cur.fetchone()
    
    if row:
        user = {"id": row[0], "name": row[1], "email": row[2]}
        # Write to cache with TTL
        r.setex(cache_key, 3600, json.dumps(user))
        return user
        
    return None
```

#### Pros and Cons
- Pros: Cache contains only data that the application actually requests. Resilient to cache failure (the app can fall back to the DB).
- Cons: Inconsistent data between cache and database (stale data). Cache misses increase latency by adding three trips (Redis -> DB -> Redis). Dual-write race conditions can occur.

### Read-Through

In a read-through cache, the application treats the cache as the main data store. When there is a cache miss, the cache provider (or an abstraction layer) is responsible for fetching the data from the database, updating the cache, and returning the value.

### Write-Through

In the write-through pattern, data is written to the cache and the corresponding database at the same time. The cache acts as the main interface for writes.

#### Flow:
1. Application writes data to the cache layer.
2. The cache layer synchronously writes data to the underlying database.
3. Both operations succeed before returning success to the application.

### Write-Back (Write-Behind)

In write-back caching, the application writes data to the cache, which acknowledges the write immediately. The cache then asynchronously writes the data to the underlying database.

#### Flow:
1. Application writes data to Redis.
2. Redis acknowledges the write.
3. A background process syncs the Redis changes to the database.

### Write-Around

Data is written directly to the database, bypassing the cache. The cache is only updated on cache misses via the cache-aside or read-through patterns. This prevents the cache from being flooded with data that may not be subsequently read.

## 2. TTL Strategy

Data in caches should rarely be permanent. Setting a Time To Live (TTL) ensures that stale data is eventually evicted and memory is freed.

### Setting TTL

Use the `EX` or `PX` arguments with `SET`, or use `EXPIRE`.

```bash
SET session:123 "data" EX 3600
EXPIRE session:123 3600
```

### Jitter to Avoid Thundering Herd

If many keys are set to expire at the exact same time, a sudden surge of database requests will occur when they all expire simultaneously. To avoid this, add random "jitter" to your TTLs.

```python
import random

base_ttl = 3600
jitter = random.randint(-300, 300)
final_ttl = base_ttl + jitter

r.setex("key", final_ttl, "value")
```

### Passive vs Active Expiry

Redis uses two mechanisms to expire keys:
1. Passive expiry: When a client attempts to access a key, Redis checks if it has expired and deletes it if necessary.
2. Active expiry: Redis runs a background task 10 times per second to sample keys with an associated TTL. If an expired key is found, it is deleted. If more than 25% of the sampled keys are expired, it repeats the process.

## 3. Cache Stampede (Thundering Herd)

A cache stampede occurs when a highly accessed cache key (a "hot key") expires. Multiple concurrent requests for this key will result in cache misses, causing all requests to simultaneously hit the underlying database to regenerate the same data, potentially overwhelming the database.

### Mutex Locks (SET NX PX)

When a cache miss occurs, a thread attempts to acquire a lock before querying the database. Only the thread that acquires the lock queries the DB; other threads wait and retry the cache.

```python
import time

def get_hot_key(key):
    val = r.get(key)
    if val:
        return val
        
    lock_key = f"lock:{key}"
    # Try to acquire lock
    if r.set(lock_key, "1", nx=True, px=5000):
        try:
            # Recheck cache inside lock (double-checked locking)
            val = r.get(key)
            if val:
                return val
            # Query DB
            val = query_db(key)
            r.setex(key, 3600, val)
            return val
        finally:
            r.delete(lock_key)
    else:
        # Wait and retry
        time.sleep(0.05)
        return get_hot_key(key)
```

### Probabilistic Early Expiry (XFetch Algorithm)

Instead of waiting for the key to expire, a thread may probabilistically recompute the value before it expires. The closer the key is to its expiration time, the higher the probability that a thread will compute the new value.

### Background Refresh

A separate worker process continually polls or receives notifications to refresh hot keys in the background before they expire, ensuring the cache is never truly empty for that key.

## 4. Cache Penetration

Cache penetration occurs when requests are made for data that does not exist in the cache OR the database. Because the data doesn't exist in the database, it is never cached. Malicious users can exploit this by requesting random, non-existent keys to bombard the database.

### Null Value Caching

If a database query returns no result, cache a "null" value for that key with a short TTL.

```python
def get_user_data(user_id):
    key = f"user:{user_id}"
    val = r.get(key)
    
    if val == b"NULL":
        return None
    elif val:
        return val
        
    val = db.query(user_id)
    if not val:
        r.setex(key, 60, "NULL")
        return None
        
    r.setex(key, 3600, val)
    return val
```

### Bloom Filters (GETBIT check before DB)

A Bloom filter is a space-efficient probabilistic data structure that can test whether an element is a member of a set. False positives are possible, but false negatives are not. Before querying the database for a key, check the Bloom filter. If the filter says the key does not exist, you can return immediately without hitting the DB.

Redis provides the RedisBloom module, or you can implement a basic one using bitmaps (`SETBIT`, `GETBIT`).

## 5. Cache Avalanche

A cache avalanche happens when a large portion of the cache expires simultaneously or the cache server restarts without persistence. This forces all traffic to the database.

### Mitigation Strategies
1. TTL Jitter (TTL = base_ttl + random()): As discussed above, distributing expiration times prevents mass expiry.
2. Staggered Warming: Gradually populate the cache on startup instead of all at once.
3. Circuit Breakers: Implement circuit breakers in the application to fail fast if the database load becomes too high, returning default or cached stale data instead.

## 6. Pub/Sub

Redis Pub/Sub implements the Publish/Subscribe messaging paradigm. Senders (publishers) do not program the messages to be sent directly to specific receivers (subscribers). Instead, published messages are characterized into channels, without knowledge of what (if any) subscribers there may be.

### Commands
- `SUBSCRIBE channel1 channel2`: Subscribe to channels.
- `PUBLISH channel1 "Hello"`: Publish a message to a channel.
- `UNSUBSCRIBE channel1`: Unsubscribe from a channel.
- `PSUBSCRIBE pattern*`: Subscribe to channels matching a pattern.

### Characteristics and Comparison
- Fire-and-Forget: Messages are not stored. If a subscriber is not connected when a message is published, the message is lost forever for that subscriber.
- Comparison with Streams: Redis Streams provide persistence, consumer groups, and message acknowledgement. Pub/Sub is purely ephemeral broadcasting. Use Pub/Sub for real-time notifications where missed messages are acceptable. Use Streams for reliable event sourcing and job queues.

## 7. Distributed Locks

Distributed locks are required when multiple processes or nodes need to synchronize access to a shared resource.

### Simple SET NX PX

The standard way to acquire a lock in Redis is using the `SET` command with `NX` (Not eXists) and `PX` (expiration time in milliseconds).

```bash
SET resource_name my_random_value NX PX 30000
```
- `NX`: Ensures that the lock is only acquired if it doesn't already exist.
- `PX 30000`: Ensures the lock automatically expires after 30 seconds to prevent deadlocks if the client crashes.
- `my_random_value`: A unique token generated by the client to identify lock ownership.

### Atomic Release via Lua Script

To release the lock safely, you must ensure that you are the owner of the lock. This requires a GET and a DEL operation, which must be atomic. A Lua script provides this atomicity.

```lua
if redis.call("get",KEYS[1]) == ARGV[1] then
    return redis.call("del",KEYS[1])
else
    return 0
end
```

### Lock TTL Extension

If the task takes longer than the lock's TTL, the client should start a background thread to periodically extend the lock's TTL (e.g., using a Lua script to check ownership and PEXPIRE).

### Redlock Algorithm

For high availability, Redis creator Antirez proposed the Redlock algorithm.
1. It relies on N independent Redis master nodes (usually 5).
2. The client tries to acquire the lock in all N instances sequentially.
3. The client computes the elapsed time to acquire the lock. If it acquired the lock in the majority of nodes (N/2 + 1) AND the elapsed time is less than the lock validity time, the lock is considered acquired.
4. Martin Kleppmann critique: Redlock relies on timing assumptions and lack of clock drift, which makes it unsafe for strict consensus compared to systems like ZooKeeper or etcd. Antirez responded defending the practical safety of the algorithm under standard NTP synchronization.

### Single Node + Replica WAIT command

For strong consistency on a single master with replicas, you can use the `WAIT` command. After setting the lock on the master, call `WAIT` to block until the write is propagated to the specified number of replicas. This prevents lock loss if the master crashes before replication.

```bash
SET lock myval NX PX 10000
WAIT 1 1000
```

## 8. Rate Limiting Patterns

Rate limiting is crucial to protect APIs from abuse. Redis is heavily used for this due to its speed.

### Fixed Window Counter

Increments a counter for a specific time window.
- Key: `rate:{ip}:2023-10-27T10:00`
- Operation: `INCR` and `EXPIRE`

Pros: Simple.
Cons: Spike at the boundary of the window. A user can exhaust the limit at the end of minute 1, and again at the start of minute 2, effectively doubling the rate momentarily.

### Sliding Window Log

Stores a timestamp for every request in a Sorted Set.
- Key: `rate:{ip}`
- Operation: `ZADD` with timestamp as score. `ZREMRANGEBYSCORE` to remove timestamps older than the window. `ZCARD` to count requests in the window.

Pros: Perfectly accurate.
Cons: Memory intensive, as it stores every request timestamp.

### Sliding Window Counter (Weighted Interpolation)

Approximates the sliding window using two fixed windows (the current window and the previous window). If you are 25% into the current minute, the count is `current_window_count + (previous_window_count * 0.75)`.

### Token Bucket (Sorted Set / Hashes)

Tokens are added to a bucket at a fixed rate. Requests consume a token.
Can be implemented using a Hash storing `tokens_left` and `last_refreshed_timestamp`.

### Lua Scripts for Atomic Rate Limiting

Since rate limiting requires reading the current count, comparing it against the limit, and potentially updating it, these steps must be atomic to prevent race conditions. Lua scripts are essential.

```lua
local current = redis.call("INCR", KEYS[1])
if tonumber(current) == 1 then
    redis.call("EXPIRE", KEYS[1], ARGV[1])
end
if tonumber(current) > tonumber(ARGV[2]) then
    return 0 -- Rate limited
end
return 1 -- Allowed
```

## 9. Session Store

Redis is the industry standard for distributed session management. When scaling application servers horizontally, local memory sessions fail.

### SETEX user:session:{token}

Store session data with a TTL.

```bash
SETEX session:abc123xyz 86400 '{"user_id": 42, "role": "admin"}'
```
Or use Hashes for granular updates:
```bash
HSET session:abc123xyz user_id 42 role admin
EXPIRE session:abc123xyz 86400
```

### Comparing Cookie vs Redis vs JWT

- Cookie (Stateless): Data stored entirely on the client. Vulnerable to XSS/CSRF. Limited size. Cannot easily invalidate on the server side.
- JWT (JSON Web Token): Cryptographically signed data. Completely stateless on the server. Hard to revoke before expiration without maintaining a blacklist.
- Redis (Stateful): Session ID stored on client (cookie), data stored in Redis. Fully server-controlled. Easy to invalidate, list active sessions, and force logout. Requires network hop to Redis.

## 10. Job Queue Pattern

While specialized tools like RabbitMQ exist, Redis provides excellent primitives for building reliable job queues.

### List as FIFO Queue (RPUSH/BLPOP)

Producers push items to the right of a list. Consumers blockingly pop from the left.

Producer: `RPUSH jobs:queue '{"task": "send_email", "user": 1}'`
Consumer: `BLPOP jobs:queue 0`

### Reliable Queue with LMOVE

`BLPOP` is destructive; if the consumer crashes immediately after popping, the job is lost. `LMOVE` (previously `BRPOPLPUSH`) solves this by atomically moving the item from the pending queue to a processing queue.

```bash
LMOVE jobs:queue jobs:processing RIGHT LEFT
```
If the consumer succeeds, it removes the item from `jobs:processing` (using `LREM`). If it fails, a watcher process can move items stuck in `jobs:processing` for too long back to `jobs:queue`.

### Dead Letter Queue (DLQ) Pattern

If a job fails repeatedly, it should not remain in the main queue forever. After N retries, move the job to a separate List representing the Dead Letter Queue for manual inspection.

### Celery Comparison

Celery is a robust distributed task queue for Python. It can use Redis as its message broker and result backend. While you can build queues manually with Redis commands, Celery abstracts away the complexity of reliable delivery, retries, concurrency, and task scheduling, building upon these exact Redis patterns under the hood.

---
End of Document.
