# Redis Performance Cheatsheet

## Memory Management

| Metric / Command | Description | Target Value / Rule |
| :--- | :--- | :--- |
| `INFO memory` | Shows overall memory statistics. | Monitor regularly. |
| `used_memory_rss` | Physical RAM allocated by the OS. | Must be < Total System RAM. |
| `mem_fragmentation_ratio` | Ratio of RSS to used_memory. | 1.0 to 1.5 is healthy. |
| `MEMORY USAGE key` | Byte size of a specific key. | Check size before caching large objects. |
| `OBJECT ENCODING key` | Internal data structure representation. | Monitor for unexpected conversions. |

**Important Note:** High fragmentation (>1.5) means memory is wasted. Low fragmentation (<1.0) means Redis is swapping to disk (CRITICAL ISSUE).

## Eviction Policies (`maxmemory-policy`)

| Policy | Behavior when memory is full | Best Use Case |
| :--- | :--- | :--- |
| `noeviction` (Default) | Rejects new writes with OOM error. Reads work. | Strict databases, no data loss acceptable. |
| `allkeys-lru` | Evicts least recently used keys overall. | Standard cache, all data is disposable. |
| `volatile-lru` | Evicts LRU keys that have a TTL set. | Mixed cache/DB, keep non-expiring config data. |
| `allkeys-lfu` | Evicts least frequently used keys overall. | Content delivery, power-law access patterns. |
| `volatile-ttl` | Evicts keys closest to expiration. | Queue systems, time-series windows. |

## Deletion: DEL vs UNLINK

```text
+---------------------+-----------------------+
| DEL                 | UNLINK                |
+---------------------+-----------------------+
| Synchronous         | Asynchronous          |
| Blocks main thread  | Instant return        |
| O(N) memory free    | O(1) logical, O(N) bg |
| Use for: Strings    | Use for: Sets, Hashes |
+---------------------+-----------------------+
```

## Safe Iteration (SCAN)

**Rule:** NEVER use `KEYS *` in production. Always use `SCAN`.

```bash
# Basic SCAN operation
> SCAN 0 MATCH user:* COUNT 100
1) "42"             # The new cursor. Use this for the next call.
2) 1) "user:123"    # The results.
   2) "user:456"

# Next call
> SCAN 42 MATCH user:* COUNT 100
```
*   `HSCAN`: For Hashes (returns field/value pairs).
*   `SSCAN`: For Sets (returns members).
*   `ZSCAN`: For Sorted Sets (returns member/score pairs).

## Network Optimization: Pipelining

Use pipelining to bundle multiple commands and save Round Trip Time (RTT).

```python
# Python Example
pipe = r.pipeline()
pipe.set('foo', 'bar')
pipe.hset('user:1', 'name', 'alice')
pipe.execute() # Network call happens here
```
**Rule of thumb:** Keep pipeline batches between 100 and 1,000 commands to avoid server memory bloat.

## Transactions (MULTI/EXEC) & Optimistic Locking

```text
> WATCH mykey        # Abort if mykey changes before EXEC
> MULTI              # Begin queueing
> SET mykey "new"
> INCR counter
> EXEC               # Execute atomically (or return nil if WATCH failed)
```
*   **Syntax Errors:** Command won't queue, `EXEC` fails completely.
*   **Runtime Errors:** Erroneous command fails during `EXEC`, all other queued commands succeed (NO ROLLBACK).

## Lua Scripting

```bash
# Execute logic atomically on the server
> EVAL "if redis.call('GET', KEYS[1]) == ARGV[1] then return redis.call('DEL', KEYS[1]) else return 0 end" 1 mykey myval
```
*   Replaces complex `WATCH`/`MULTI`/`EXEC` blocks.
*   Reduces network round trips to 1.
*   Use `SCRIPT LOAD` and `EVALSHA` in production to cache compiled scripts.

## Slowlog Configuration

```text
> CONFIG SET slowlog-log-slower-than 10000  # Log commands > 10ms (microseconds)
> CONFIG SET slowlog-max-len 128            # Keep last 128 slow entries
> SLOWLOG GET 5                             # Retrieve last 5 entries
```
