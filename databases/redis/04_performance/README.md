# Redis Module 04: Performance and Advanced Operations

This module dives deep into optimizing Redis performance, managing memory effectively, using advanced access patterns safely, and monitoring the system to ensure smooth operation under heavy load.

## 1. Memory Deep Dive

Understanding how Redis allocates, utilizes, and reports memory is fundamental to maintaining a healthy instance.

### Memory Inspection Commands

The `INFO memory` command provides a high-level overview of memory consumption.

```text
127.0.0.1:6379> INFO memory
# Memory
used_memory:104857600
used_memory_human:100.00M
used_memory_rss:120000000
used_memory_rss_human:114.44M
used_memory_peak:150000000
used_memory_peak_human:143.05M
used_memory_peak_perc:69.90%
used_memory_overhead:54000000
used_memory_startup:860160
used_memory_dataset:50857600
used_memory_dataset_perc:48.43%
allocator_allocated:105000000
allocator_active:110000000
allocator_resident:115000000
total_system_memory:17179869184
total_system_memory_human:16.00G
used_memory_lua:37888
used_memory_lua_human:37.00K
used_memory_scripts:0
used_memory_scripts_human:0B
number_of_cached_scripts:0
maxmemory:0
maxmemory_human:0B
maxmemory_policy:noeviction
allocator_frag_ratio:1.05
allocator_frag_bytes:5000000
allocator_rss_ratio:1.05
allocator_rss_bytes:5000000
rss_overhead_ratio:1.04
rss_overhead_bytes:5000000
mem_fragmentation_ratio:1.14
mem_fragmentation_bytes:15142400
mem_not_counted_for_evict:0
mem_replication_backlog:0
mem_clients_slaves:0
mem_clients_normal:20496
mem_aof_buffer:0
mem_allocator:jemalloc-5.2.1
active_defrag_running:0
lazyfree_pending_objects:0
lazyfreed_objects:0
```

Key Metrics:
- `used_memory`: Total number of bytes allocated by Redis using its allocator (usually jemalloc). This represents the logical memory size of your data.
- `used_memory_rss`: Resident Set Size. The number of bytes that the operating system has allocated to Redis. This includes fragmentation overhead.
- `mem_fragmentation_ratio`: `used_memory_rss` / `used_memory`. A value between 1.0 and 1.5 is generally considered healthy. A value above 1.5 indicates significant fragmentation, meaning the OS is reserving much more memory than Redis is actually using for data. A value below 1.0 indicates that Redis is swapping to disk, which will severely degrade performance.

### Analyzing Individual Keys

To understand the memory footprint of specific keys, use `MEMORY USAGE`.

```text
127.0.0.1:6379> SET mykey "Hello World"
OK
127.0.0.1:6379> MEMORY USAGE mykey
(integer) 56
```

The output is in bytes and includes both the key, the value, and the internal data structures required to manage the key. Note that for complex types (like large hashes or lists), `MEMORY USAGE` performs a sampling unless the `SAMPLES 0` argument is provided to force an exact, but slower, calculation.

```text
127.0.0.1:6379> HSET myhash f1 "v1" f2 "v2"
(integer) 2
127.0.0.1:6379> MEMORY USAGE myhash
(integer) 80
```

### Advanced Inspection: DEBUG OBJECT

For deeper insights, use `DEBUG OBJECT` or `OBJECT ENCODING`. Note that `DEBUG OBJECT` is considered a debugging command and should not be used in critical application paths.

```text
127.0.0.1:6379> DEBUG OBJECT mykey
Value at:00007FF7D3B6A1A0 refcount:1 encoding:embstr serializedlength:12 lru:131000 lru_seconds_idle:15
```

- `refcount`: Number of references to this object.
- `encoding`: The internal representation format.
- `serializedlength`: The size of the string representation if it were to be serialized.
- `lru` / `lru_seconds_idle`: Information used by eviction algorithms.

```text
127.0.0.1:6379> OBJECT ENCODING mykey
"embstr"
```

### Internal Encodings and Thresholds

Redis optimizes memory usage by employing different internal encodings based on the size and type of the data. For example, a Hash can be encoded as a `ziplist` (or `listpack` in newer versions) for small sizes, saving significant memory overhead compared to a full `hashtable`.

When the data exceeds certain thresholds, Redis automatically converts the encoding to a more scalable, albeit more memory-intensive, format.

Configuration thresholds (redis.conf):
```text
hash-max-listpack-entries 512
hash-max-listpack-value 64
list-max-listpack-size -2
zset-max-listpack-entries 128
zset-max-listpack-value 64
set-max-intset-entries 512
```

Example of encoding change:
```text
127.0.0.1:6379> HSET testhash field1 "smallvalue"
(integer) 1
127.0.0.1:6379> OBJECT ENCODING testhash
"listpack"
127.0.0.1:6379> HSET testhash bigfield "This string is longer than sixty four bytes and will trigger a conversion"
(integer) 1
127.0.0.1:6379> OBJECT ENCODING testhash
"hashtable"
```

### Memory Diagnostics

`MEMORY DOCTOR` provides a human-readable analysis of memory issues, looking at fragmentation, memory usage by clients, and other potential problems.

```text
127.0.0.1:6379> MEMORY DOCTOR
Hi Sam, I can't find any memory issue in your instance. I can only report that what is not used for data is space allocated for overheads or fragmentation.
```

## 2. Eviction Policies

When Redis is configured with a `maxmemory` limit, it must decide what to do when that limit is reached. The `maxmemory-policy` dictates this behavior.

Setting maxmemory:
```text
127.0.0.1:6379> CONFIG SET maxmemory 100mb
OK
```

### Available Policies

- `noeviction`: The default policy. When the limit is reached, commands that would result in more memory being used (e.g., SET, HSET) return an OOM error. Read commands continue to work.
- `allkeys-lru`: Evict the least recently used keys out of all keys.
- `volatile-lru`: Evict the least recently used keys out of the keys that have an "expire" set.
- `allkeys-lfu`: Evict the least frequently used keys out of all keys.
- `volatile-lfu`: Evict the least frequently used keys out of the keys that have an "expire" set.
- `allkeys-random`: Evict keys randomly out of all keys.
- `volatile-random`: Evict keys randomly out of the keys that have an "expire" set.
- `volatile-ttl`: Evict keys with the shortest time-to-live (TTL) out of the keys that have an "expire" set.

### LRU Approximation

Redis does not maintain a strict LRU linked list for eviction, as it would cost too much memory. Instead, it uses an approximated LRU algorithm. It samples a subset of keys and evicts the best candidate among the sample.

Configuration parameter:
```text
maxmemory-samples 5
```
Increasing this value (e.g., to 10) makes the algorithm closer to true LRU at the cost of more CPU cycles during eviction. A value of 5 is a good default trade-off.

### LFU (Least Frequently Used)

LFU was introduced to better handle workloads where some keys are accessed very often, but perhaps not as recently as a newly inserted key that will never be read again.

LFU uses a 24-bit field per object. 16 bits are used for the last access time (in minutes), and 8 bits are used for a probabilistic logarithmic counter (the Morris counter).

Because the counter is only 8 bits, it caps at 255. The counter does not increment linearly; the chance of incrementing decreases as the counter value gets higher.

LFU configuration parameters:
- `lfu-log-factor 10`: Determines how quickly the counter saturates. A value of 10 means the counter will max out at 255 after approximately 1 million hits.
- `lfu-decay-time 1`: The counter needs to decay over time so that historically popular keys can eventually be evicted. This setting dictates how many minutes must elapse for the counter to be divided in half.

## 3. Lazy Freeing (UNLINK)

By default, Redis deletes keys synchronously. The `DEL` command removes the key from the keyspace and deallocates the associated memory on the main thread. If the value is a very large Hash, List, Set, or Sorted Set (e.g., containing millions of elements), the memory deallocation can take hundreds of milliseconds or even seconds, blocking all other operations.

### The UNLINK Command

`UNLINK` is the asynchronous version of `DEL`. It immediately removes the key from the keyspace (so it is no longer reachable by clients), but the actual memory deallocation is handed off to a background thread. The command returns immediately.

```text
127.0.0.1:6379> UNLINK my_huge_list
(integer) 1
```
Use `UNLINK` instead of `DEL` whenever the size of the data structure is unknown or known to be large.

### Background Freeing Configuration

You can configure Redis to automatically use background threads for other deletion scenarios.

redis.conf options:
- `lazyfree-lazy-eviction yes`: If memory limit is reached, perform eviction deletions in a background thread.
- `lazyfree-lazy-expire yes`: Perform expiration (TTL) deletions in a background thread.
- `lazyfree-lazy-server-del yes`: Some commands overwrite data (e.g., `SET` on an existing key). This option pushes the deletion of the old value to a background thread.
- `replica-lazy-flush yes`: During a full synchronization with a master, a replica must flush its entire database. This option allows the flush to happen asynchronously.

Note: Even with lazy freeing enabled, Redis will evaluate the size of the object. If the object is small (e.g., a simple string), it will be deleted synchronously on the main thread because the overhead of passing it to a background thread would outweigh the benefit.

## 4. Key Scanning (SCAN)

### The Danger of KEYS *

The `KEYS <pattern>` command returns all keys matching a given pattern.

```text
127.0.0.1:6379> KEYS user:*
1) "user:1"
2) "user:2"
...
```

`KEYS` operates synchronously. It traverses the entire keyspace dictionary. In a database with millions of keys, this command will block the main thread for seconds, causing massive latency spikes for all connected clients. **`KEYS` should never be used in a production environment.**

### SCAN to the Rescue

`SCAN` provides a cursor-based approach to iterate over the keyspace incrementally. It returns a small batch of elements and a new cursor to be used in the subsequent call.

```text
127.0.0.1:6379> SCAN 0 MATCH user:* COUNT 100
1) "17"
2) 1) "user:45"
   2) "user:89"
```

The first return value is the new cursor (`"17"`). If the returned cursor is `"0"`, the iteration is complete. The second return value is an array of elements.

### SCAN Arguments

- `CURSOR`: An integer. Always start with `0`.
- `MATCH pattern`: Filters the results. Note that the filtering happens *after* the elements are retrieved from the dictionary, so an iteration might return an empty array but a non-zero cursor if no elements matched in that specific batch.
- `COUNT hint`: Provides a hint to the engine about how many elements to return per iteration. The default is 10. This is not a strict guarantee; Redis may return more or fewer elements.
- `TYPE type`: Filters results by data type (e.g., `string`, `hash`, `list`, `set`, `zset`).

### Reverse Binary Iteration

The cursor used by `SCAN` is not a simple incremental index. Redis uses a reverse-binary-iterator. This mathematical approach guarantees that if a key is present in the dictionary from the start to the end of a complete iteration, it will be returned. It also handles dictionary resizing (rehashing) gracefully during the iteration without returning massive amounts of duplicates or missing keys. However, keys added or removed during the iteration may or may not be returned. It is possible for `SCAN` to return the same key multiple times across iterations.

### Data Structure Specific Scans

Similar iterator commands exist for complex data structures:
- `HSCAN key cursor [MATCH pattern] [COUNT count]`: Iterates fields and values of a Hash.
- `SSCAN key cursor [MATCH pattern] [COUNT count]`: Iterates elements of a Set.
- `ZSCAN key cursor [MATCH pattern] [COUNT count]`: Iterates members and scores of a Sorted Set.

## 5. Pipelining

Every Redis command executes in a request/response cycle. The client sends a command to the server, and the server sends a reply. The time it takes for a packet to travel across the network and back is the Round Trip Time (RTT).

If you need to execute 10,000 `SET` commands, and the RTT is 1ms, the total time will be at least 10 seconds, regardless of how fast Redis can process the commands internally (which is typically microseconds).

### Reducing RTT with Pipelining

Pipelining allows the client to send multiple commands to the server without waiting for the replies. The server queues the replies in memory and sends them all back in a single batch.

This reduces the impact of network latency and also reduces socket I/O overhead on the server.

### Python Example

```python
import redis
import time

r = redis.Redis(host='localhost', port=6379, db=0)

# Without pipelining
start_time = time.time()
for i in range(10000):
    r.set(f'key:{i}', i)
print(f"Without pipeline: {time.time() - start_time} seconds")

# With pipelining
start_time = time.time()
pipe = r.pipeline()
for i in range(10000):
    pipe.set(f'pipekey:{i}', i)
pipe.execute() # Executes the batch
print(f"With pipeline: {time.time() - start_time} seconds")
```

### Pipelining vs MSET/MGET

Commands like `MSET` and `MGET` are atomic operations built into Redis. Pipelining is a client-side and networking optimization.
If you are only getting or setting strings, `MSET`/`MGET` are slightly more efficient. However, pipelining is required when you need to batch different types of commands (e.g., a `SET`, an `HSET`, and a `SADD`).

### Optimal Pipeline Sizing

Do not send an infinitely large pipeline. The server must buffer the responses in memory before sending them back. A pipeline of 1,000,000 commands could consume excessive memory on the server and lead to OOM conditions.
A good rule of thumb is to batch between 100 and 1,000 commands per pipeline, depending on the size of the data being written or read.

## 6. Transactions (MULTI/EXEC)

Redis supports a form of transactions that guarantees sequential execution of a block of commands.

```text
127.0.0.1:6379> MULTI
OK
127.0.0.1:6379(TX)> SET txkey1 "hello"
QUEUED
127.0.0.1:6379(TX)> SET txkey2 "world"
QUEUED
127.0.0.1:6379(TX)> EXEC
1) OK
2) OK
```

When `MULTI` is issued, subsequent commands are not executed immediately but queued. `EXEC` executes them all atomically. No other client command will be served in the middle of the `EXEC` block. `DISCARD` can be used to flush the queue and exit transaction mode.

### Error Handling

There are two types of errors in a transaction:
1.  **Queueing Errors (Syntax Errors):** If a command is malformed (e.g., wrong number of arguments), Redis will refuse to queue it and will flag the transaction. When `EXEC` is called, the transaction will fail entirely.
2.  **Execution Errors (Runtime Errors):** If a command is syntactically correct but fails at runtime (e.g., operating against the wrong data type, like pushing to a string), the command will queue successfully. When `EXEC` is called, the specific command will fail, but **all other commands in the transaction will still execute**. Redis does not support rollbacks.

### Optimistic Locking with WATCH

Because transactions cannot contain internal conditional logic (you cannot read a value inside a transaction and use it to decide the next command before `EXEC`), Redis provides `WATCH`.

`WATCH` implements Check-And-Set (CAS). You watch a key, and if the key is modified by another client before you call `EXEC`, the entire transaction fails (returns a null reply).

```text
# Client 1
127.0.0.1:6379> WATCH balance
OK
127.0.0.1:6379> GET balance
"100"
127.0.0.1:6379> MULTI
OK
127.0.0.1:6379(TX)> SET balance "110"
QUEUED

# Client 2 (intervenes before Client 1's EXEC)
127.0.0.1:6379> SET balance "50"
OK

# Client 1
127.0.0.1:6379(TX)> EXEC
(nil) # Transaction failed because 'balance' was modified
```
The client must handle the `(nil)` response, typically by retrying the operation.

## 7. Lua Scripting

Lua scripting provides a powerful way to execute arbitrary logic atomically on the server side. It replaces complex `MULTI/EXEC/WATCH` patterns and drastically reduces network round trips.

### The EVAL Command

```text
127.0.0.1:6379> EVAL "return redis.call('SET', KEYS[1], ARGV[1])" 1 myluakey "luavalue"
OK
```

Arguments for EVAL:
1.  The Lua script.
2.  The number of keys accessed by the script (`1` in this case).
3.  The key names (`myluakey`). Accessed in Lua via the `KEYS` table (1-indexed).
4.  Additional arguments (`"luavalue"`). Accessed in Lua via the `ARGV` table (1-indexed).

### Atomicity and Blocking

A Lua script is evaluated as a single atomic unit. No other client commands are executed while a script is running.
Therefore, scripts must be fast. A slow or infinite loop script will freeze the entire Redis server.
By default, if a script runs longer than `lua-time-limit` (default 5000ms), Redis will start accepting new connections but will reply with a `BUSY` error to all commands except `SCRIPT KILL` (if no write operations were performed yet) or `SHUTDOWN NOSAVE`.

### redis.call() vs redis.pcall()

- `redis.call()`: Executes a Redis command. If the command results in an error (e.g., syntax error), the Lua script halts immediately and returns the error to the client.
- `redis.pcall()`: Executes a Redis command, but traps errors. If an error occurs, it returns a Lua table representing the error, allowing the script to handle it and continue executing.

### Caching Scripts: SCRIPT LOAD and EVALSHA

Sending the raw script text over the network for every invocation wastes bandwidth and parsing time.

```text
127.0.0.1:6379> SCRIPT LOAD "return redis.call('GET', KEYS[1])"
"4e6d8fc8bb01276962cce5371fa795a7763657ae"
```
`SCRIPT LOAD` compiles the script and stores it in the server cache, returning a SHA1 digest.

```text
127.0.0.1:6379> EVALSHA 4e6d8fc8bb01276962cce5371fa795a7763657ae 1 myluakey
"luavalue"
```
`EVALSHA` executes the cached script using the digest. Clients should attempt `EVALSHA`, and if it returns a `NOSCRIPT` error, fall back to `EVAL` or `SCRIPT LOAD`.

### Redis Functions (Redis 7.0+)

Redis 7.0 introduced Functions, a more robust way to manage server-side logic compared to `EVAL`. Functions are named, versioned, and persisted in the RDB/AOF, unlike EVAL scripts which are ephemeral in the script cache.

```text
127.0.0.1:6379> FUNCTION LOAD "#!lua name=mylib\nredis.register_function('myfunc', function(keys, args) return redis.call('GET', keys[1]) end)"
"mylib"
127.0.0.1:6379> FCALL myfunc 1 myluakey
"luavalue"
```

## 8. Slowlog & Latency Monitoring

Redis is designed to be extremely fast. When operations are slow, the Slowlog is the first tool to consult.

### Configuring Slowlog

The slowlog operates entirely in memory.

- `slowlog-log-slower-than`: The execution time threshold in microseconds. Commands taking longer than this will be logged. A value of `10000` means 10 milliseconds. A value of `0` forces logging of all commands. A negative value disables logging entirely.
- `slowlog-max-len`: The maximum number of entries to keep in the slowlog queue. When the queue is full, the oldest entry is evicted.

```text
127.0.0.1:6379> CONFIG SET slowlog-log-slower-than 5000
OK
127.0.0.1:6379> CONFIG SET slowlog-max-len 128
OK
```

### Reading the Slowlog

```text
127.0.0.1:6379> SLOWLOG GET 2
1) 1) (integer) 14            # Unique ID of the slowlog entry
   2) (integer) 1630000000    # Unix timestamp of execution
   3) (integer) 12000         # Execution time in microseconds
   4) 1) "KEYS"               # The command array
      2) "*"
   5) "127.0.0.1:54321"       # Client IP and port
   6) ""                      # Client name (if set)
2) 1) (integer) 13
   2) (integer) 1629999900
   3) (integer) 8500
   4) 1) "EVAL"
      2) "..."
      ...
```
Important: The execution time logged is only the time the command spent being executed on the thread. It does not include network I/O time or time spent waiting in the command queue.

### Latency Monitoring Framework

For a broader view of system latency beyond just slow command execution (e.g., latency caused by fork time during background saves, or operating system swapping), use the latency monitoring framework.

First, set a threshold in milliseconds:
```text
127.0.0.1:6379> CONFIG SET latency-monitor-threshold 100
OK
```

Then query the subsystem:
- `LATENCY LATEST`: Returns the latest latency sample for all events.
- `LATENCY HISTORY <event>`: Returns raw time series data for a specific event (e.g., `command`, `fast-command`, `fork`, `rdb-unlink-temp-file`).

You can simulate a latency event for testing using `DEBUG SLEEP`.
```text
127.0.0.1:6379> DEBUG SLEEP 0.2
OK
```

## 9. Benchmarking & Key Design

### redis-benchmark

Redis includes a utility to measure performance under varying conditions.

Run a standard benchmark against localhost:
```bash
redis-benchmark -q -n 100000 -c 50
```
- `-q`: Quiet mode, outputs only query/sec values.
- `-n 100000`: Total number of requests.
- `-c 50`: Number of parallel connections.

Benchmark specific commands using pipelining:
```bash
redis-benchmark -t set,lpush -n 100000 -q -P 16
```
- `-t`: Comma-separated list of tests to run.
- `-P 16`: Pipeline size of 16 commands.

### Key Design and Naming Conventions

Keys are just binary safe strings, but establishing a convention is critical for management and debugging.

Standard format: `object-type:id:field`
Examples:
- `user:1000:profile` (Hash storing user details)
- `product:55:inventory` (String/Integer for stock count)
- `session:xyz123` (String storing serialized session data)

Benefits of Namespacing:
- Predictability.
- Easier pattern matching with `SCAN`.
- Clear understanding of data structure types just from the name.

### Anti-Patterns to Avoid

1.  **Huge Keys:** Storing a Hash with 10 million fields, or a String value of 500MB.
    - Impact: Network buffers fill up, memory allocation spikes, operations like deletion or serialization block the main thread for unacceptably long times.
    - Solution: Shard huge Hashes into smaller buckets (e.g., `user:followers:bucket:1`, `user:followers:bucket:2`).
2.  **Hot Keys:** A single key that is accessed thousands of times per second (e.g., a counter for a viral video).
    - Impact: Exceeds the capacity of a single Redis node, causing CPU bottleneck on the main thread handling that specific key's shard.
    - Solution: Implement local caching in the application tier (e.g., read the key from Redis once, cache in application memory for 5 seconds). Alternatively, shard the counter across multiple keys and sum them on read.

## 10. Threaded I/O (Redis 6+)

Starting in Redis 6, threaded I/O was introduced to alleviate the bottleneck of network read/write operations on the single execution thread.

### How Threaded I/O Works

Redis remains single-threaded for all command execution (data manipulation). However, the reading of client commands from the network sockets, parsing them, and writing the responses back to the sockets can now be delegated to multiple background threads.

Since network I/O is often the most time-consuming part of serving a request (when RTT is not considered), this can significantly boost the overall throughput of a Redis instance, potentially by up to 2x or 3x on multi-core servers.

### Configuring Threaded I/O

Threaded I/O is disabled by default. It is recommended to enable it only when you have at least 4 CPU cores and are experiencing performance bottlenecks related to I/O (e.g., the Redis process is consistently maxing out a single CPU core, and network traffic is very high).

```text
# Enable threaded I/O (default is no)
io-threads-do-reads yes

# Set the number of threads.
# A good rule of thumb is to use 3 threads for a 4-core machine,
# or 6 threads for an 8-core machine. Leaving at least 1-2 cores
# for the main thread and background tasks.
io-threads 4
```

Note that setting `io-threads 1` will just use the main thread, effectively turning off the feature. Do not set `io-threads` to more than the number of available cores minus one.

### Threaded I/O and Pipelining

Threaded I/O and pipelining are complementary. Pipelining reduces network latency (RTT), while threaded I/O increases the server's capacity to process network packets simultaneously. Together, they can drastically improve throughput for high-volume workloads.

### When NOT to use Threaded I/O

If your Redis instance is not fully utilizing a single CPU core, enabling threaded I/O will not provide any benefits and might even slightly degrade performance due to the overhead of thread synchronization. Always benchmark your specific workload before and after enabling this feature.
