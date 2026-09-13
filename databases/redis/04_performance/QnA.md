# Redis Performance QnA

**1. What is the difference between `used_memory` and `used_memory_rss`?**
`used_memory` is the amount of memory mathematically requested by Redis data structures and allocated by the memory allocator (usually jemalloc). `used_memory_rss` (Resident Set Size) is the actual physical memory the operating system has mapped to the Redis process. The RSS value includes memory fragmentation overhead and OS-level overhead. If RSS is significantly higher than used memory, the instance is experiencing severe fragmentation.

**2. Why is a `mem_fragmentation_ratio` below 1.0 dangerous?**
A fragmentation ratio below 1.0 means that `used_memory_rss` is less than `used_memory`. This indicates that the operating system was unable to provide enough physical memory to Redis and has started swapping memory pages to disk. Because disk I/O is orders of magnitude slower than RAM access, swapping will instantly ruin Redis performance and latency characteristics.

**3. Under what circumstances will the `noeviction` policy cause issues, and how does it behave?**
`noeviction` is problematic when an instance reaches its `maxmemory` limit and applications continue to send write requests. Under this policy, any command that attempts to allocate more memory (like `SET`, `LPUSH`, or `HSET`) will immediately fail and return an OOM (Out Of Memory) error to the client. Read operations and deletions will continue to function normally.

**4. How does Redis's implementation of LRU differ from a textbook LRU cache?**
A textbook LRU requires a doubly linked list linking all cache entries, which adds massive memory overhead (two pointers per key). Redis avoids this by using an approximated LRU approach. It maintains a 24-bit timestamp for each object. Upon eviction, Redis randomly samples a subset of keys (defined by `maxmemory-samples`, defaulting to 5) and evicts the key with the oldest access time from that small sample pool, saving memory at the cost of strict accuracy.

**5. How does the Morris counter work in the LFU eviction policy?**
The LFU policy uses an 8-bit counter, which can normally only represent values from 0 to 255. The Morris counter uses a probabilistic approach to incrementing. As the counter value increases, the probability that a subsequent read will successfully increment it decreases logarithmically. This allows the 8-bit counter to accurately represent the relative frequency of access up to roughly a million hits, avoiding integer overflow within a tiny memory footprint.

**6. When should a developer choose `UNLINK` over `DEL`?**
`UNLINK` should be the default choice for removing keys whenever the size of the underlying data structure is unknown or known to be large (e.g., Lists, Sets, Hashes, or Sorted Sets with thousands or millions of elements). `DEL` synchronously blocks the main execution thread while memory is deallocated, which can take hundreds of milliseconds for huge keys. `UNLINK` immediately unlinks the key from the dictionary space and delegates the heavy memory deallocation to a background thread.

**7. Why is `KEYS *` prohibited in production environments?**
The `KEYS` command operates by synchronously iterating over the entirety of the global hash table. Because Redis handles commands sequentially on a single thread, executing a full table scan on a database containing millions of keys will stall the thread for a significant duration (often seconds). During this stall, no other clients can be served, leading to massive latency spikes and connection timeouts across the entire system.

**8. How does `SCAN` prevent the blocking issue caused by `KEYS`?**
`SCAN` prevents blocking by yielding control back to the event loop. Instead of returning the entire keyspace at once, it utilizes a cursor-based iterator. Each invocation of `SCAN` with a cursor integer returns a small subset of elements and a new cursor for the next call. The work is chunked into minuscule, non-blocking segments, allowing Redis to seamlessly interleave other client requests between subsequent `SCAN` calls.

**9. What guarantees does the reverse-binary-iterator used by `SCAN` provide regarding data consistency?**
The reverse-binary-iterator algorithm guarantees that any key present in the dictionary from the moment the scan begins until the scan concludes will be returned exactly once, provided no structural alterations occur. Crucially, it manages dictionary resizing (rehashing) seamlessly. If a rehash occurs during iteration, the algorithm ensures no keys are systematically skipped. However, it may return keys added during the iteration, and it may return duplicate keys if a contraction rehash occurs.

**10. How does pipelining improve throughput for batch operations?**
Without pipelining, every command incurs a full network Round Trip Time (RTT). A client sends a command, waits for network transit, processing, and return transit before sending the next command. Pipelining circumvents this by allowing the client to stream multiple commands sequentially into the socket buffer without waiting for intermediate replies. Redis executes them in order and queues the replies, returning them as an array. This reduces network overhead latency from N * RTT to approximately 1 * RTT.

**11. What is the fundamental difference in execution handling between Pipelining and Transactions (MULTI/EXEC)?**
Pipelining is strictly a client-side network optimization; the Redis server processes pipelined commands sequentially, but commands from other clients may be interleaved between them. A Transaction (`MULTI/EXEC`), however, enforces strict isolation. Once `EXEC` is called, all queued commands are executed sequentially and atomically as a single block; the server guarantees that no commands from competing clients will be interleaved during the execution phase.

**12. Explain the behavior of a Redis transaction if a runtime error occurs during the `EXEC` phase.**
Unlike relational database systems, Redis transactions do not support rollbacks on runtime failures (e.g., executing a list operation against a string key). If a runtime error occurs while applying a queued command during `EXEC`, that specific command will fail and log an error in the response array, but the transaction will proceed to execute all subsequent queued commands. State changes from successful commands prior to the failure are persisted.

**13. How does `WATCH` facilitate optimistic locking in Redis?**
The `WATCH` command monitors specific keys for modifications prior to a transaction block. A client executes `WATCH key1`, reads the value, performs local computation, begins a `MULTI` block, and issues update commands. If a secondary client alters `key1` between the `WATCH` and `EXEC` invocations, the primary client's `EXEC` will abort, returning a null reply. The client must then identify the conflict, restart the loop, read the new value, and retry the operation.

**14. What are the advantages of Lua Scripting (`EVAL`/`EVALSHA`) over traditional `MULTI/EXEC` transactions?**
Lua scripting provides transactional atomicity but adds computational logic. Unlike `MULTI/EXEC`, a Lua script allows developers to read a value, apply conditional statements (`if/else`), perform transformations, and write back results within a single isolated server-side execution context. Furthermore, scripts eliminate the need for `WATCH` loops and drastically cut down on network chatter, as complex multi-step operations require only one round-trip.

**15. If a command consistently appears in the Slowlog, what does its recorded execution time actually represent?**
The execution duration recorded in the Redis Slowlog strictly represents the CPU time consumed on the main thread processing that specific command. It explicitly excludes the time the client request spent waiting in network socket buffers, the time the command spent enqueued waiting for prior commands to finish, and the network transmission time for the response. It purely isolates algorithmic execution latency.
