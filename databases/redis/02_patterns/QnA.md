# Redis Patterns - Questions and Answers

**1. What is the Cache-Aside pattern and what are its main drawbacks?**
The Cache-Aside pattern involves the application code checking the cache first, and on a miss, querying the database and manually updating the cache. Its main drawbacks are that cache misses incur a latency penalty (three network hops: app->cache, app->db, app->cache), data can become stale if the database is updated directly without invalidating the cache, and it is susceptible to race conditions during dual writes.

**2. How does a Write-Through cache differ from a Write-Behind (Write-Back) cache?**
In a Write-Through cache, the application writes to the cache layer, which synchronously writes to the underlying database before acknowledging success. This guarantees consistency but increases write latency. In a Write-Behind cache, the write to the database is done asynchronously in the background. This provides low latency for writes but risks data loss if the cache crashes before syncing to the database.

**3. What is a Cache Stampede (Thundering Herd) and how can it be prevented?**
A Cache Stampede occurs when a highly accessed "hot key" expires, causing a massive influx of concurrent requests to experience a cache miss and hit the database simultaneously, potentially overwhelming it. It can be prevented by using a distributed mutex lock (only one thread queries the DB), probabilistic early expiry (threads randomly recompute the value before expiration), or by having a background process refresh hot keys.

**4. Explain the concept of Cache Penetration.**
Cache Penetration happens when requests target data that exists neither in the cache nor in the database. Because it's not in the DB, it's never cached, causing every request to hit the DB. Malicious actors can use this to DDoS a database. It is mitigated by caching null values with short TTLs or using a Bloom filter to check for existence before querying the DB.

**5. How does adding "Jitter" to a TTL help system stability?**
If a large batch of keys is loaded into the cache with the exact same TTL, they will all expire simultaneously, leading to a Cache Avalanche where the database is suddenly hit with thousands of queries. Adding a random time variation (jitter) to the base TTL ensures the keys expire at slightly different times, spreading the database load.

**6. What is the difference between active and passive expiry in Redis?**
Passive expiry occurs when a client attempts to access a key, and Redis deletes it if its TTL has passed. Active expiry is a background process where Redis periodically samples keys with a TTL and deletes the expired ones to free up memory proactively, even if they aren't being accessed.

**7. Why is the `SET NX PX` command combination crucial for distributed locks?**
`NX` ensures the lock is only acquired if it doesn't already exist, providing mutual exclusion. `PX` sets an expiration time, ensuring that if the client holding the lock crashes, the lock will eventually be released, preventing a deadlock. Combining them into one command ensures atomicity.

**8. Why must a Lua script be used to release a distributed lock?**
To release a lock safely, a client must first verify that it actually owns the lock (by checking the token value) and then delete it. If this is done with separate `GET` and `DEL` commands, another client's lock could expire and be acquired in between the two commands, causing the first client to accidentally delete the second client's lock. A Lua script executes atomically, preventing this race condition.

**9. What is the Redlock algorithm?**
Redlock is an algorithm designed by Antirez to provide highly available distributed locks using multiple independent Redis master nodes. A client attempts to acquire the lock on a majority of the nodes. If successful within the validity time, the lock is acquired. It avoids the single point of failure of a single Redis master.

**10. How does a Sliding Window Log rate limiter work using Redis?**
It uses a Sorted Set where the key is the user/IP, the score is the request timestamp, and the value is a unique identifier (or timestamp). On each request, it adds the new timestamp, removes all elements with a score older than the time window (`ZREMRANGEBYSCORE`), and then counts the remaining elements (`ZCARD`). If the count exceeds the limit, the request is denied.

**11. Why is Pub/Sub considered "fire-and-forget"?**
Redis Pub/Sub does not persist messages. When a message is published to a channel, Redis immediately pushes it to all currently connected subscribers. If a subscriber is offline, or if there are no subscribers, the message is dropped permanently. There is no state or history.

**12. When would you choose Redis Streams over Redis Pub/Sub?**
You should choose Redis Streams when you need message persistence, guaranteed delivery, consumer groups (distributing work among multiple workers), and the ability for consumers to acknowledge successful processing of messages. Pub/Sub is only for ephemeral, real-time broadcasts.

**13. What is the `LMOVE` command and how does it create reliable queues?**
`LMOVE` atomically pops an element from one list and pushes it into another. In a reliable queue, it moves a task from the `pending` queue to a `processing` queue. If the consumer crashes while working on the task, the task remains safely in the `processing` queue and can be recovered, unlike `BLPOP` which removes it entirely.

**14. What are the advantages of managing sessions in Redis compared to JWTs?**
Redis session management is stateful, allowing the server to have full control. You can instantly invalidate a session, force a user to log out of all devices, and view active sessions. JWTs are stateless and, once issued, are difficult to revoke before their expiration time without complex blacklist implementations.

**15. How does a token bucket rate limiter operate in Redis?**
Tokens are conceptually added to a bucket at a fixed rate. When a request arrives, it checks if there are enough tokens. If so, it decrements the token count; otherwise, it rejects the request. In Redis, this is usually implemented by storing the `tokens_left` and the `last_refreshed_timestamp`. A Lua script reads these, calculates how many tokens should have been generated since the last request, updates the values, and returns the result.
