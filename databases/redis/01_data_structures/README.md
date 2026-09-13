# Redis Data Structures and Internals

## Introduction: Redis as a Data Structure Server

Redis (Remote Dictionary Server) is often categorized as a key-value store, but this is a vast oversimplification. Unlike memcached or simple key-value caches that only understand strings, Redis is a true "data structure server". It natively understands complex data types like lists, sets, sorted sets, hashes, and streams. When you store a list in Redis, it is not a serialized blob of JSON; it is an in-memory linked list or a contiguous array of elements managed natively by C code.

This distinction allows Redis to execute operations on specific elements within these data structures in constant O(1) or logarithmic O(log N) time without needing to transmit the entire data structure over the network to the client, deserialize it, modify it, and serialize it back. 

This module covers the core data structures in Redis, their commands, their time complexities, their typical use cases, and their underlying memory representations.

---

## Single-Threaded I/O Model

One of the most frequently asked questions about Redis is: "How can it be so fast if it is single-threaded?"

### The Event Loop
Historically, Redis has used a single-threaded architecture for query processing. It employs an event loop (using multiplexing technologies like `epoll` on Linux, `kqueue` on BSD/macOS, or `select`) to handle concurrent client connections. 

By executing all commands sequentially in a single thread, Redis avoids all lock contention, mutex overhead, and context switching. Operations are atomic by default. If a client executes a command, no other client's command can interleave with it.

### Background Threads
While the main command execution thread is singular, Redis is not strictly a single-threaded process. It has always used background threads for specific tasks:
- `BGSAVE`: Creating an RDB snapshot is handled by forking the process. The child process writes the memory to disk, leveraging the OS's Copy-On-Write (COW) mechanism.
- `BGREWRITEAOF`: Rewriting the Append-Only File also happens in a forked child process.
- `UNLINK` (lazy deletion) and `FLUSHDB ASYNC`: Operations that deallocate large amounts of memory are offloaded to background threads to prevent blocking the main event loop.

### I/O Threads in Redis 6+
Starting with Redis 6.0, threaded I/O was introduced. While command execution remains strictly single-threaded, Redis can now delegate network read (parsing client requests) and network write (sending responses back to clients) operations to a pool of I/O threads. This significantly improves throughput, often doubling the operations per second on multicore machines, without compromising the lock-free simplicity of single-threaded command execution.

Configuration in `redis.conf`:
```conf
# Enable IO threads
io-threads-do-reads yes

# Set the number of threads (usually # cores - 1 or 2)
io-threads 4
```

---

## Strings

Strings are the most basic Redis value type. They are binary safe, meaning they can contain any data type (e.g., JPEG images, serialized objects) up to a maximum size of 512MB per string.

### Core Commands

- `SET key value`: Sets a key to hold a string value. O(1).
- `GET key`: Gets the value of a key. O(1).
- `SETNX key value`: Sets the key only if it does not already exist. Used for basic distributed locks. O(1).
- `SETEX key seconds value`: Sets the key and sets an expiration timeout simultaneously. O(1).
- `GETSET key value`: Sets the key to a new value and returns the old value. O(1).
- `MSET key1 value1 key2 value2`: Sets multiple keys to multiple values. O(N).
- `MGET key1 key2`: Gets the values of multiple keys. O(N).
- `APPEND key value`: Appends a string to the end of a string. O(1).

### Atomic Counters
Because Redis commands are atomic and single-threaded, you can safely use Strings for counting without race conditions.

- `INCR key`: Increments the integer value of a key by one. O(1).
- `INCRBY key increment`: Increments the value of a key by the given number. O(1).
- `DECR key`: Decrements the integer value of a key by one. O(1).

Example in Python (using `redis-py`):
```python
import redis

client = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Atomic increment
client.set('page_views:home', 100)
client.incr('page_views:home')
views = client.get('page_views:home')
print(f"Views: {views}") # Views: 101
```

### Internals: Encoding Types
Strings in Redis are represented by a C structure called Simple Dynamic Strings (SDS). Under the hood, a string can use one of three encodings:
1. `int`: If the string is a 64-bit signed integer, Redis stores it directly as a numeric value to save memory.
2. `embstr`: An optimized encoding for short strings (usually up to 44 bytes). The Redis object structure and the SDS structure are allocated in a single contiguous memory block.
3. `raw`: Used for longer strings. The Redis object and SDS are allocated separately, requiring two memory allocations.

You can inspect the encoding using `OBJECT ENCODING`:
```redis
127.0.0.1:6379> SET num 100
OK
127.0.0.1:6379> OBJECT ENCODING num
"int"
127.0.0.1:6379> SET short_str "hello"
OK
127.0.0.1:6379> OBJECT ENCODING short_str
"embstr"
```

---

## Lists

Redis Lists are linked lists of strings. Because they are linked lists (or internally, listpacks), adding elements to the head or tail is extremely fast O(1), but accessing elements by index in the middle is O(N).

### Core Commands

- `LPUSH key element`: Inserts an element at the head of the list. O(1).
- `RPUSH key element`: Inserts an element at the tail of the list. O(1).
- `LPOP key`: Removes and returns the first element of the list. O(1).
- `RPOP key`: Removes and returns the last element of the list. O(1).
- `LRANGE key start stop`: Returns a range of elements. O(S+N). `LRANGE mylist 0 -1` returns all elements.
- `LLEN key`: Returns the length of the list. O(1).
- `LINDEX key index`: Gets an element by its index. O(N).
- `LINSERT key BEFORE|AFTER pivot element`: Inserts an element before or after another element. O(N).

### Blocking Operations and Queues
Lists are heavily used to implement producer-consumer queues. Redis provides blocking commands that wait until data is available.

- `BLPOP key timeout`: Removes and returns the first element, or blocks until one is available.
- `BRPOP key timeout`: Removes and returns the last element, or blocks until one is available.
- `LMOVE source destination LEFT|RIGHT LEFT|RIGHT`: Atomically pops an element from one list and pushes it to another. This is the modern replacement for `RPOPLPUSH`.
- `BLMOVE`: The blocking variant of `LMOVE`.

Reliable Queue Pattern:
Use `LMOVE` (or `BLMOVE`) to pop a job from the "pending" list and immediately push it to a "processing" list atomically. If the consumer crashes during processing, the job is not lost; it remains in the "processing" list and can be reclaimed by a supervisor process.

```python
# Producer
client.lpush('jobs_pending', 'task_123')

# Consumer (reliable queue)
# Pops from right of jobs_pending, pushes to left of jobs_processing
job = client.blmove('jobs_pending', 'jobs_processing', 'RIGHT', 'LEFT', timeout=0)
try:
    process_task(job)
    # Success, remove from processing list
    client.lrem('jobs_processing', 1, job)
except Exception:
    # Handle failure (e.g., move to dead letter queue)
    client.lrem('jobs_processing', 1, job)
    client.lpush('jobs_dead', job)
```

### Internals: Quicklist and Listpack
Historically, Redis used a doubly-linked list or a `ziplist` (a contiguous memory block).
Currently, Lists are implemented as a `quicklist` — a doubly-linked list of `listpack` nodes. A `listpack` is a highly compact, contiguous block of memory. This architecture balances the fast O(1) push/pop of a linked list with the memory efficiency and cache locality of contiguous arrays, mitigating memory fragmentation.

---

## Sets

Redis Sets are unordered collections of unique strings. You can add, remove, and test for the existence of members in O(1) time.

### Core Commands

- `SADD key member`: Adds a member to the set. O(1).
- `SMEMBERS key`: Returns all members of the set. O(N).
- `SISMEMBER key member`: Checks if a member exists in the set. O(1).
- `SCARD key`: Returns the number of members in the set (cardinality). O(1).
- `SREM key member`: Removes a member from the set. O(1).
- `SRANDMEMBER key [count]`: Returns random elements from the set without removing them. O(N).
- `SPOP key [count]`: Removes and returns random elements from the set. O(N).

### Set Operations
Redis natively supports highly optimized mathematical set operations:

- `SUNION key1 key2`: Returns the union of multiple sets.
- `SINTER key1 key2`: Returns the intersection of multiple sets.
- `SDIFF key1 key2`: Returns the difference between the first set and all successive sets.

Each of these has a `STORE` variant (`SUNIONSTORE`, `SINTERSTORE`, `SDIFFSTORE`) that saves the result to a destination key instead of returning it to the client.

### Use Cases
- Unique visitors tracking for a given day (e.g., `SADD visitors:2023-10-25 user_id`).
- Tagging systems (e.g., a set of tags for a specific blog post).
- Social graphs (e.g., friends of user A intersect friends of user B = mutual friends).

```redis
# Finding mutual friends
127.0.0.1:6379> SADD friends:alice bob charlie david
(integer) 3
127.0.0.1:6379> SADD friends:eve charlie david frank
(integer) 3
127.0.0.1:6379> SINTER friends:alice friends:eve
1) "charlie"
2) "david"
```

---

## Sorted Sets (ZSETs)

Sorted Sets are similar to regular Sets in that they contain unique strings. However, every member is associated with a floating-point number called a `score`. The elements are always sorted by their score, from smallest to largest.

### Core Commands

- `ZADD key score member`: Adds a member with the specified score. O(log N).
- `ZSCORE key member`: Returns the score of a member. O(1).
- `ZRANK key member`: Returns the rank (index) of a member, sorted ascending. O(log N).
- `ZREVRANK key member`: Returns the rank of a member, sorted descending. O(log N).
- `ZRANGE key start stop [WITHSCORES]`: Returns members within a given index range. O(log N + M).
- `ZREVRANGE`: Same as ZRANGE, but descending. (Note: in Redis 6.2+, use `ZRANGE ... REV`).
- `ZRANGEBYSCORE key min max`: Returns members within a specific score range. O(log N + M).
- `ZRANGEBYLEX key min max`: Returns members within a specific lexicographical range (when scores are identical).
- `ZINCRBY key increment member`: Increments the score of a member. O(log N).
- `ZCOUNT key min max`: Returns the number of members within a score range. O(log N).
- `ZPOPMIN / ZPOPMAX`: Removes and returns the member with the lowest/highest score. O(log N).

### Set Operations on ZSETs
- `ZUNIONSTORE` and `ZINTERSTORE`: Computes the union or intersection of sorted sets. You can specify weights and aggregate functions (SUM, MIN, MAX).

### Internals: Skip List and Hash Table
Sorted sets are internally implemented using a dual data structure:
1. A **Hash Table** maps the element (string) to its score. This allows `ZSCORE` to operate in O(1) time.
2. A **Skip List** keeps the elements sorted by score. This allows range queries (`ZRANGE`, `ZRANGEBYSCORE`) and rank queries (`ZRANK`) to operate in O(log N) time. 

For very small sorted sets, Redis uses a compact `listpack` encoding to save memory.

### Use Cases
- Leaderboards (scores are the user points).
- Priority Queues (scores are the priority or timestamp).
- Rate Limiting (sliding window log approach using timestamps as scores).
- Time-series data (scores are unix timestamps).

```python
# Implementing a Leaderboard
client.zadd('leaderboard', {'player1': 1500, 'player2': 1800, 'player3': 1200})
client.zincrby('leaderboard', 50, 'player1') # player1 is now 1550

# Top 3 players (descending)
top_players = client.zrevrange('leaderboard', 0, 2, withscores=True)
print(top_players) # [('player2', 1800.0), ('player1', 1550.0), ('player3', 1200.0)]
```

---

## Hashes

Redis Hashes are maps between string fields and string values. They represent objects perfectly.

### Core Commands

- `HSET key field value`: Sets the value of a field in the hash. O(1).
- `HGET key field`: Gets the value of a field. O(1).
- `HMSET key field value [field value ...]`: Sets multiple fields. (Deprecated in favor of passing multiple pairs to `HSET`).
- `HMGET key field1 field2`: Gets multiple fields. O(N).
- `HGETALL key`: Returns all fields and values. O(N).
- `HKEYS key` / `HVALS key`: Returns all fields or all values. O(N).
- `HINCRBY key field increment`: Increments the integer value of a field. O(1).
- `HEXISTS key field`: Checks if a field exists. O(1).
- `HDEL key field`: Deletes a field. O(1).

### Use Cases
- Storing User Profiles/Sessions.
- Object representation.

```redis
127.0.0.1:6379> HSET session:987 user_id 55 username "admin" last_login "2023-10-25T10:00:00Z"
(integer) 3
127.0.0.1:6379> HGETALL session:987
1) "user_id"
2) "55"
3) "username"
4) "admin"
5) "last_login"
6) "2023-10-25T10:00:00Z"
```

---

## HyperLogLog

HyperLogLog (HLL) is a probabilistic data structure used to estimate the cardinality (number of unique elements) of a set.
Instead of storing every element (which takes O(N) memory), HLL stores state using a fixed maximum of 12KB of memory. It can estimate the cardinality of massive sets with a standard error of ~0.81%.

### Core Commands
- `PFADD key element [element ...]`: Adds elements to the HLL. O(1).
- `PFCOUNT key [key ...]`: Returns the estimated cardinality. O(1).
- `PFMERGE destkey sourcekey [sourcekey ...]`: Merges multiple HLLs into a single one. O(N).

### Use Cases
- Counting unique IP addresses visiting a website on a given day.
- Counting unique search queries.

```python
# Add unique IPs
client.pfadd('unique_ips:2023-10-25', '192.168.1.1', '10.0.0.5', '192.168.1.1')
count = client.pfcount('unique_ips:2023-10-25')
print(f"Unique IPs: {count}") # Output will be 2
```

---

## Bitmaps

Bitmaps are not an actual data structure in Redis; they are just a set of bit-oriented operations applied on the String data type. Since strings are up to 512MB long, a single string can hold up to 2^32 (over 4 billion) different bits.

### Core Commands
- `SETBIT key offset value`: Sets or clears the bit at offset. O(1).
- `GETBIT key offset`: Returns the bit value at offset. O(1).
- `BITCOUNT key [start end]`: Counts the number of set bits (population count). O(N).
- `BITOP operation destkey key1 [key2 ...]`: Performs bitwise operations (AND, OR, XOR, NOT) between multiple strings. O(N).
- `BITPOS key bit [start] [end]`: Finds the first bit set or clear. O(N).

### Use Cases
- Daily Active Users (DAU): Map the user ID to a bit offset.
- A/B testing cohort assignment.

```redis
# User ID 100 visited today
127.0.0.1:6379> SETBIT dau:2023-10-25 100 1
(integer) 0
# User ID 150 visited today
127.0.0.1:6379> SETBIT dau:2023-10-25 150 1
(integer) 0
# Total active users today
127.0.0.1:6379> BITCOUNT dau:2023-10-25
(integer) 2
```

---

## Streams

Redis Streams are an append-only log data structure. They model a log file or an event stream and are the Redis equivalent to Apache Kafka, offering robust message brokering with persistent event history, consumer groups, and delivery acknowledgments.

### Core Commands

- `XADD key * field value`: Appends a new entry to the stream. `*` auto-generates a time-based ID (e.g., `1698240503000-0`). O(1).
- `XREAD [COUNT count] [BLOCK milliseconds] STREAMS key id`: Reads data from one or multiple streams. Use `$` to read only new messages. O(N).
- `XRANGE key start end`: Returns a range of messages by ID. O(log N).
- `XLEN key`: Returns the length of the stream. O(1).

### Consumer Groups
Like Kafka, Streams support consumer groups, allowing a fleet of workers to cooperatively consume a stream. Each message is delivered to exactly one consumer in the group.

- `XGROUP CREATE key groupname id`: Creates a consumer group. Use `$` for new messages, or `0` to consume from the beginning.
- `XREADGROUP GROUP group consumer STREAMS key id`: Reads messages via a consumer group. `>` reads undelivered messages.
- `XACK key group id`: Acknowledges that a message was successfully processed.

### Pending Entries List (PEL) and Recovery
When a consumer reads a message via a group, it is added to the PEL. If the consumer crashes before calling `XACK`, the message remains in the PEL.
Other workers can inspect the PEL and claim stalled messages.

- `XPENDING key group`: Inspects pending messages.
- `XCLAIM key group consumer min-idle-time id`: Reassigns a pending message to a different consumer.

### Streams vs. Kafka
- Redis Streams live in-memory (though they can be persisted to disk via RDB/AOF). Kafka stores data sequentially on disk.
- Redis is typically easier to deploy and manage for smaller scale or real-time event routing.
- Kafka handles petabytes of data; Redis Streams are limited by RAM.

---

## Geo

Redis provides geographical data structures. Internally, Geo data is stored in a Sorted Set (ZSET). The coordinates are converted into a 52-bit Geohash, which becomes the score in the ZSET.

### Core Commands

- `GEOADD key longitude latitude member`: Adds a geographical location. O(log N).
- `GEODIST key member1 member2 [unit]`: Returns the distance between two members (using the Haversine formula). O(log N).
- `GEOSEARCH key FROMMEMBER member BYRADIUS radius unit`: Returns members within a given radius. (Replaces deprecated `GEORADIUS`). O(N + log M).
- `GEOPOS key member`: Returns the longitude and latitude. O(log N).

### Use Cases
- Ride-sharing applications (finding nearest drivers).
- Point-of-interest search.

```redis
127.0.0.1:6379> GEOADD sicily 13.361389 38.115556 "Palermo" 15.087269 37.502669 "Catania"
(integer) 2
127.0.0.1:6379> GEODIST sicily Palermo Catania km
"166.2742"
```

---

## Internal Encoding Thresholds and Memory Optimization

Redis dynamically swaps the internal memory representation of a data structure based on its size to optimize for RAM usage vs CPU usage. Small structures use highly compact memory layouts, while larger ones use standard hash tables or trees.

Configuration limits dictate when the conversion occurs:

```conf
# Hashes: Encoded as listpack if elements < 512 and max size of any element < 64 bytes
hash-max-listpack-entries 512
hash-max-listpack-value 64

# ZSETs: Encoded as listpack if elements < 128 and max size < 64 bytes
zset-max-listpack-entries 128
zset-max-listpack-value 64

# Sets: Encoded as integer set (intset) if all elements are integers and total count < 512
set-max-intset-entries 512
```
Tuning these parameters allows you to aggressively save memory at the cost of slight increases in CPU cycles when manipulating those specific keys.

