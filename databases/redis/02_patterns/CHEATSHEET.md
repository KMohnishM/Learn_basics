# Redis Patterns Cheatsheet

## Caching Patterns Summary

| Pattern | Write Path | Read Path | Pros | Cons |
| :--- | :--- | :--- | :--- | :--- |
| **Cache-Aside** | App updates DB -> Invalidates Cache | App checks Cache -> DB on miss -> App updates Cache | Resilient, predictable | Stale data risk, stampedes |
| **Read-Through**| Same as above | Cache abstraction handles DB read on miss | Cleaner application code | Requires abstraction layer |
| **Write-Through**| App writes to Cache -> Cache writes synchronously to DB | Cache handles read | Strong consistency | High write latency |
| **Write-Behind**| App writes to Cache -> Cache async updates DB | Cache handles read | Extremely fast writes | Data loss if cache crashes |

## Cache Stampede Mitigation
- **Mutex**: `SET lock:key "1" NX PX 5000` (Only one worker queries DB).
- **Early Expiry**: Proactively recompute before the TTL expires.
- **Background Refresh**: Dedicated worker updates the key asynchronously.

## Cache Penetration Mitigation
- **Null Caching**: `SETEX missing:user:99 60 "NULL"` (Cache the miss).
- **Bloom Filters**: Check probabilistic structure before hitting DB.

## Cache Avalanche Mitigation
**TTL Jitter Formula**:
```python
ttl = base_ttl + random(-max_jitter, +max_jitter)
```

## Distributed Locks Sequence

1. **Acquire**: 
   ```bash
   SET resource:name "client-guid-123" NX PX 30000
   ```
2. **Execute**: Perform critical section task.
3. **Extend (Optional)**: If task takes longer, PEXPIRE to extend.
4. **Release**: Atomic Lua script.
   ```lua
   if redis.call("get",KEYS[1]) == ARGV[1] then
       return redis.call("del",KEYS[1])
   else return 0 end
   ```

## Rate Limiting Comparison

| Strategy | Accuracy | Memory Usage | Characteristic |
| :--- | :--- | :--- | :--- |
| **Fixed Window** | Low | Very Low | Spikes at window boundaries (double limit). |
| **Sliding Log** | Perfect | High | Stores every timestamp. |
| **Sliding Window**| High | Low | Interpolates between two fixed windows. |
| **Token Bucket** | High | Low | Smooths out bursts effectively. |

## Job Queues

- **Push Task**: `RPUSH queue_name "payload"`
- **Pop Task (Unreliable)**: `BLPOP queue_name 0`
- **Pop Task (Reliable)**: `LMOVE queue_name processing_queue RIGHT LEFT`

## Session Management

```bash
# Set session with expiration
SETEX session:tok_123 3600 '{"uid": 10}'

# Update session TTL on activity
EXPIRE session:tok_123 3600

# Terminate session
DEL session:tok_123
```
