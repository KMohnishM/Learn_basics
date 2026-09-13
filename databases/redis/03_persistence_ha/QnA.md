# Q&A: Redis Persistence and High Availability

**1. What is the primary difference between RDB and AOF?**
RDB (Redis Database) takes periodic, point-in-time snapshots of the entire dataset and saves it as a compact binary file. AOF (Append-Only File) logs every write command received by the server to a file, providing a continuous transaction log. RDB is faster for recovery and creates smaller files, while AOF provides much higher durability and minimizes data loss.

**2. How does the BGSAVE command work under the hood?**
When `BGSAVE` is executed, the main Redis thread invokes the `fork()` system call. The operating system creates a child process. The main thread continues serving client requests without blocking. The child process iterates over the memory space and writes the RDB snapshot to disk. It utilizes the OS's Copy-on-Write mechanism to ensure the snapshot represents the exact moment the fork occurred.

**3. What is Copy-on-Write (COW) and how does it relate to Redis?**
COW is an optimization strategy used by the operating system during a `fork()`. Instead of copying all physical memory for the child process, the parent and child initially share read-only memory pages. If the parent (Redis main thread) needs to write to a page, the OS intercepts, copies that specific page, and allows the parent to write to the copy. This makes `fork()` extremely fast and saves memory, but requires extra memory allocation if there are heavy writes during an RDB save or AOF rewrite.

**4. Explain the different appendfsync modes for AOF.**
The `appendfsync` directive dictates how often Redis asks the OS to flush the AOF buffer to physical disk.
*   `always`: Flushes after every write command. Extremely durable (zero data loss) but very slow due to disk I/O overhead.
*   `everysec`: Flushes once per second in a background thread. The default and recommended setting, balancing excellent performance with a maximum of one second of potential data loss.
*   `no`: Relies on the OS to flush the buffer (usually every 30 seconds on Linux). Fast but risky, as a crash could result in significant data loss.

**5. What is the AOF rewrite process (BGREWRITEAOF)?**
Because AOF logs every command, it grows indefinitely. An AOF rewrite creates a new, optimized AOF file. It does not read the old file; instead, it forks a child process that scans the current in-memory dataset and generates the minimal set of commands required to recreate it. This dramatically reduces the file size and speeds up recovery time upon restart.

**6. How does the hybrid RDB-AOF persistence model work?**
Introduced in Redis 4.0, the hybrid model uses AOF as the primary persistence mechanism but changes the AOF rewrite behavior. When a rewrite occurs, the child process writes the current dataset as a compact RDB snapshot to the beginning of the new AOF file, and then appends only the subsequent new write commands in standard AOF format. This combines the rapid load times of RDB with the fine-grained safety of AOF.

**7. What are the key components of a Redis Sentinel setup?**
A typical Sentinel setup requires a Redis master instance, one or more Redis replica instances, and at least three separate Redis Sentinel processes running on different servers. The Sentinels monitor the master and replicas, communicate via a gossip protocol, hold elections using a quorum to confirm failures, and automatically orchestrate failovers.

**8. Differentiate between SDOWN and ODOWN in Sentinel.**
SDOWN (Subjective Down) is when a single Sentinel instance perceives a Redis instance as unreachable because it hasn't responded to PINGs within a configured timeout. ODOWN (Objective Down) is a state specifically for masters; it occurs when a Sentinel in SDOWN state asks other Sentinels for their view of the master, and a sufficient number (the quorum) agree that the master is indeed unreachable. Only ODOWN triggers a failover.

**9. Describe the failover process in Redis Sentinel.**
Once a master reaches ODOWN, the Sentinels hold an election to determine a Leader. The Leader Sentinel selects the most suitable replica (based on offset, priority, and run ID) and sends it the `REPLICAOF NO ONE` command to promote it to master. The Leader then sends configuration commands to the remaining replicas to make them replicate from the new master. Finally, clients querying the Sentinels are informed of the new master's address.

**10. How does a client application integrate with Redis Sentinel?**
A Sentinel-aware client application does not connect directly to the Redis master IP address. Instead, it connects to one of the Sentinel instances and requests the current IP and port of the master for a specific monitored group name (e.g., `mymaster`). The client then connects to that address. If a failover occurs and the client is disconnected, it asks the Sentinel again for the new master address.

**11. Explain how PSYNC2 improves Redis replication.**
Prior to PSYNC2, if a master and replica temporarily lost connection, or if a failover occurred and a replica became a master, full synchronizations (transferring the entire RDB file) were often required, which were expensive. PSYNC2 allows for partial synchronizations even after failovers. It uses replication IDs and offsets to determine exactly which commands a replica missed, allowing it to seamlessly catch up by only receiving the delta from the replication backlog.

**12. What is the replication backlog and how does it function?**
The replication backlog is a fixed-size, circular memory buffer maintained by the master node. It stores a history of the most recently executed write commands. When a replica disconnects briefly and reconnects, it sends its last processed offset. If that offset is still present within the backlog buffer, the master can perform a fast partial resynchronization by sending only the commands in the backlog that occurred after the replica's offset.

**13. How does the WAIT command work in Redis?**
Redis replication is asynchronous by default. The `WAIT numreplicas timeout` command allows a client to block the current connection until all previous write commands executed in the context of the connection are acknowledged by at least the specified number of replicas, or until the timeout (in milliseconds) is reached. It provides a mechanism to ensure synchronous replication for specific critical operations.

**14. Explain the concept of Hash Slots in Redis Cluster.**
Redis Cluster does not use consistent hashing. It divides the entire key space into 16,384 discrete logical units called hash slots. When you write or read a key, Redis calculates its hash slot using the formula `CRC16(key) mod 16384`. Each master node in the cluster is assigned a specific subset of these slots. This allows for deterministic routing of requests.

**15. What is the difference between a MOVED and ASK redirection in Redis Cluster?**
A `MOVED` error is returned when a client attempts to access a key on a node that is not responsible for the key's hash slot; it tells the client permanently where the slot resides. An `ASK` redirection happens during cluster resharding when a slot is actively migrating. It tells the client that the key might have moved to a target node, and the client should issue an `ASKING` command followed by the query to the target node, but only for this specific query, without permanently updating its internal slot map.
