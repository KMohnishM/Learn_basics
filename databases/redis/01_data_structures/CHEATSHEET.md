# Redis Data Structures Cheatsheet

## Data Structure Selection Guide

| Use Case | Recommended Data Structure | Why? |
| :--- | :--- | :--- |
| Simple Caching / Session Tokens | **Strings** | Fast O(1) access, supports TTL (expiration). |
| Distributed Locks / Counters | **Strings** | Atomic `SETNX`, `INCR`, `DECR`. |
| Message Queues / Job Workers | **Lists** | Fast head/tail inserts, blocking pops (`BLPOP`). |
| Rate Limiting / Leaderboards | **Sorted Sets** | Ordered by score (time/points), O(log N) ranges. |
| Unique Tags / Mutual Friends | **Sets** | Enforces uniqueness, fast server-side intersections. |
| Storing User Profiles / Objects | **Hashes** | Fields mapped to values, memory efficient. |
| Event Sourcing / Reliable Pub-Sub | **Streams** | Persistent logs, consumer groups, delivery ACKs. |
| Estimating Unique Visitors | **HyperLogLog** | Uses only 12KB RAM for billions of items. |
| User Cohorts / Daily Active Users | **Bitmaps** | Maps IDs to bits; millions of booleans in megabytes. |
| Finding Nearby Locations | **Geo** | Built on Sorted Sets, fast radius searches. |

---

## Command Reference

### Strings
```redis
SET key value               # Set value O(1)
GET key                     # Get value O(1)
SETNX key value             # Set only if it does NOT exist O(1)
SETEX key 60 value          # Set with 60s expiration O(1)
MSET k1 v1 k2 v2            # Set multiple O(N)
MGET k1 k2                  # Get multiple O(N)
INCR key                    # Increment integer O(1)
```

### Lists
```redis
LPUSH key value             # Add to head O(1)
RPUSH key value             # Add to tail O(1)
LPOP key                    # Remove from head O(1)
RPOP key                    # Remove from tail O(1)
LRANGE key 0 -1             # Get all elements O(N)
BLPOP key 10                # Pop from head, block up to 10s if empty
```

### Sets
```redis
SADD key member             # Add to set O(1)
SMEMBERS key                # Get all members O(N)
SISMEMBER key member        # Check existence O(1)
SREM key member             # Remove member O(1)
SINTER set1 set2            # Intersection of sets O(N*M)
```

### Sorted Sets (ZSETs)
```redis
ZADD key 100 "Alice"        # Add member with score O(log N)
ZSCORE key "Alice"          # Get score O(1)
ZRANK key "Alice"           # Get index/rank ascending O(log N)
ZRANGE key 0 -1 WITHSCORES  # Get all ordered by score O(log N + M)
ZREVRANGE key 0 2           # Get top 3 O(log N + M)
```

### Hashes
```redis
HSET user:1 name "Bob"      # Set field O(1)
HGET user:1 name            # Get field O(1)
HGETALL user:1              # Get all fields and values O(N)
HDEL user:1 name            # Delete field O(1)
HINCRBY user:1 age 1        # Increment integer field O(1)
```

### HyperLogLog
```redis
PFADD hll_key ip_address    # Add to HLL O(1)
PFCOUNT hll_key             # Get estimated count O(1)
PFMERGE dest src1 src2      # Merge multiple HLLs O(N)
```

### Bitmaps
```redis
SETBIT bits 100 1           # Set bit at offset 100 to 1 O(1)
GETBIT bits 100             # Get bit at offset 100 O(1)
BITCOUNT bits               # Count number of 1s O(N)
```

### Streams
```redis
XADD mystream * f1 v1       # Append to stream, auto-generate ID O(1)
XRANGE mystream - +         # Get all entries O(N)
XGROUP CREATE mystream g1 $ # Create consumer group from current end
XREADGROUP GROUP g1 c1 STREAMS mystream > # Read new messages as consumer c1
XACK mystream g1 id         # Acknowledge message processing O(1)
```

### Geo
```redis
GEOADD cities -122.4 37.7 "SF" # Add longitude/latitude O(log N)
GEODIST cities "SF" "LA" km    # Get distance in km O(log N)
GEOSEARCH cities FROMMEMBER "SF" BYRADIUS 50 km # Find nearby O(N + log M)
```

---

## Memory Optimization Thresholds (redis.conf)

Redis switches from memory-optimized encodings (like `listpack` or `intset`) to standard hash tables/skip lists when these limits are exceeded.

| Data Structure | Configuration Key | Default |
| :--- | :--- | :--- |
| **Hashes** | `hash-max-listpack-entries` | 512 |
| | `hash-max-listpack-value` | 64 bytes |
| **ZSETs** | `zset-max-listpack-entries` | 128 |
| | `zset-max-listpack-value` | 64 bytes |
| **Lists** | `list-max-listpack-size` | -2 (8KB max) |
| **Sets** | `set-max-intset-entries` | 512 |

*Note: Keeping data structures under these thresholds saves significant RAM, at a negligible CPU cost for small datasets.*
