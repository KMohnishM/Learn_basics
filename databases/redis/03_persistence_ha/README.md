# Redis Persistence and High Availability

This module covers the critical aspects of Redis durability, replication, and high availability. Redis is primarily an in-memory database, but it offers robust mechanisms to ensure data survives process restarts, system crashes, and hardware failures. 

## 1. Why Persistence: In-memory Nature vs Surviving Restarts

Redis stores all its dataset in the primary memory (RAM) of the server. This design choice is what gives Redis its phenomenal performance characteristics, often allowing sub-millisecond read and write latencies. However, RAM is volatile. If the Redis server process crashes, or if the physical server loses power, all data stored in memory is lost instantly.

To be used as a primary datastore, or even as a robust cache that doesn't suffer from severe cold-start penalties, Redis must periodically or continuously write its in-memory state to non-volatile storage (disk). Persistence in Redis is the mechanism by which it achieves this durability.

You can configure Redis to use no persistence at all, making it a pure, volatile cache. However, for most production workloads, some form of persistence is enabled. Redis offers two primary persistence options: RDB (Redis Database) Snapshots and AOF (Append-Only File).

## 2. RDB (Redis Database) Snapshots

RDB persistence performs point-in-time snapshots of your dataset at specified intervals. It creates a compact, single-file representation of the entire Redis database, which is excellent for backups and disaster recovery.

### The BGSAVE vs SAVE Commands

There are two primary ways an RDB snapshot is triggered manually: `SAVE` and `BGSAVE`.

*   `SAVE`: This command performs a synchronous save of the dataset to disk. It blocks the main Redis thread entirely until the RDB file is completely written. During this time, Redis cannot serve any other client requests. This is almost never recommended in a production environment unless you are shutting down the server and want a final snapshot.

*   `BGSAVE`: This is the standard, asynchronous way to create an RDB snapshot. When `BGSAVE` is called, Redis forks a child process. The main thread continues to handle client requests without blocking, while the child process handles the heavy lifting of writing the dataset to the disk in the background.

```bash
# Using redis-cli
127.0.0.1:6379> SAVE
OK
127.0.0.1:6379> BGSAVE
Background saving started
```

### The fork() Child Process and Copy-on-Write (COW)

The magic behind `BGSAVE` lies in the Unix `fork()` system call and the operating system's Copy-on-Write (COW) mechanism.

When Redis executes `fork()`, the OS creates a child process that is an exact duplicate of the parent process (the main Redis thread). Crucially, the OS does *not* physically copy all the memory pages. Instead, both the parent and child processes share the same physical memory pages initially, and these pages are marked as read-only.

This means the `fork()` operation itself is very fast. The child process then begins iterating over the shared memory and writing the data to the RDB file.

If a client sends a write request (e.g., `SET key value`) while the background save is in progress, the parent process attempts to modify a memory page. Because the page is marked read-only, this triggers a page fault. The OS intervenes, copies the specific page that is being modified (this is the "Copy-on-Write"), and then allows the parent process to modify the newly copied page. 

The child process continues to read from the original, unmodified page, ensuring that the RDB snapshot reflects the exact point in time when the `fork()` occurred. 

While COW is highly efficient, it does mean that if your Redis instance has a high write rate during a `BGSAVE`, it will consume additional memory. In the worst-case scenario (every single key is modified during the save), Redis would require double the memory.

### Save Configuration Directives

In the `redis.conf` file, you can configure automatic RDB snapshots using the `save` directive. The syntax is `save <seconds> <changes>`.

```text
# redis.conf snippet for RDB configuration
# Save the DB to disk:
#
#   save <seconds> <changes>
#
#   Will save the DB if both the given number of seconds and the given
#   number of write operations against the DB occurred.
#
#   Snapshotting can be completely disabled with a single empty string argument
#   as in following example:
#   save ""

save 3600 1      # Save after 1 hour if at least 1 key changed
save 300 100     # Save after 5 minutes if at least 100 keys changed
save 60 10000    # Save after 60 seconds if at least 10000 keys changed

# The filename for the RDB file
dbfilename dump.rdb

# The directory where the RDB file should be saved
dir /var/lib/redis
```

### LASTSAVE

You can check the Unix timestamp of the last successful RDB snapshot using the `LASTSAVE` command.

```bash
127.0.0.1:6379> LASTSAVE
(integer) 1678886400
```

### RDB Pros and Cons

**Pros:**
*   Compact, single-file representation, perfect for off-site backups.
*   Maximizes Redis performance by offloading saving to a child process (parent thread never performs disk I/O).
*   Faster restarts compared to AOF for large datasets.

**Cons:**
*   Data loss potential. You will lose all data modified since the last snapshot if Redis crashes. If you save every 5 minutes, you can lose up to 5 minutes of data.
*   `fork()` can be expensive on large datasets, causing brief latency spikes (milliseconds to seconds depending on dataset size and hardware) when the child process is created.

## 3. AOF (Append-Only File)

AOF persistence logs every write operation received by the server. These operations are appended to a file (`appendonly.aof`). When Redis restarts, it replays the commands in the AOF file sequentially to reconstruct the original dataset.

### appendfsync Modes

The reliability of AOF depends entirely on how often the OS flushes the AOF buffer to the physical disk using the `fsync()` system call. Redis provides three policies, configured via the `appendfsync` directive in `redis.conf`:

1.  `appendfsync always`: `fsync()` is called after every single write command. This provides the highest durability (zero data loss) but severely impacts performance due to continuous disk I/O.
2.  `appendfsync everysec` (Default): `fsync()` is called once per second by a background thread. This is a great compromise, offering near-optimal performance while limiting potential data loss to a maximum of one second.
3.  `appendfsync no`: Redis never explicitly calls `fsync()`. It leaves the decision to the OS kernel (usually every 30 seconds on Linux). This is the fastest AOF mode but the least durable.

```text
# redis.conf snippet for AOF configuration
appendonly yes
appendfilename "appendonly.aof"

# appendfsync always
appendfsync everysec
# appendfsync no
```

### AOF Rewrite (BGREWRITEAOF)

Because AOF logs every operation, the file grows continuously. For example, if you increment a counter 100 times, the AOF file will contain 100 `INCR` commands. This is inefficient. 

To prevent the AOF file from growing infinitely, Redis supports an AOF Rewrite process, triggered automatically or manually via the `BGREWRITEAOF` command. 

The rewrite process does not read the old AOF file. Instead, similar to RDB, it forks a child process. The child process reads the current in-memory dataset and generates the shortest possible sequence of commands needed to recreate that dataset. For the counter example, it would write a single `SET counter 100` command.

While the rewrite is happening, new incoming write commands are appended to a temporary AOF buffer to ensure they aren't lost, and eventually merged into the new AOF file before replacing the old one.

```bash
127.0.0.1:6379> BGREWRITEAOF
Background append only file rewriting started
```

### Auto-AOF-Rewrite Configurations

Redis automatically triggers rewrites based on these configuration directives:

```text
# redis.conf
# Trigger rewrite when AOF is 100% larger than the base size (size after last rewrite)
auto-aof-rewrite-percentage 100

# But only if the file size is at least 64MB
auto-aof-rewrite-min-size 64mb
```

### AOF+RDB Hybrid Format

Starting in Redis 4.0, a hybrid persistence model was introduced and is now the default when AOF is enabled. 

When an AOF rewrite occurs, the child process first writes the current dataset as an RDB snapshot to the beginning of the new AOF file. Once the RDB preamble is written, it appends any new write commands (in AOF format) that occurred during the rewrite process.

This combines the benefits of both: fast, compact RDB files for the bulk of the data, and the granular safety of AOF for recent operations, resulting in vastly faster restart times while maintaining durability.

```text
# redis.conf
aof-use-rdb-preamble yes
```

### AOF Pros and Cons

**Pros:**
*   Much more durable than RDB (can be configured to lose max 1 second or no data).
*   The AOF log is append-only, so there are no seeks, meaning high write throughput.
*   The log format is readable and can be manually edited in emergencies (e.g., to remove a destructive `FLUSHALL` command if discovered in time).

**Cons:**
*   AOF files are typically larger than RDB files for the same dataset.
*   Restoring a large dataset from AOF is slower than RDB (though mitigated by the hybrid format).
*   Depending on the `fsync` policy, AOF can be slower than RDB.

## 4. RDB vs AOF vs Hybrid vs No Persistence

| Feature | RDB | AOF | Hybrid (AOF+RDB) | None (Cache Only) |
| :--- | :--- | :--- | :--- | :--- |
| **Durability** | Low (Loss = time since last snapshot) | High (Loss configurable, typically 1s) | High (Loss typically 1s) | Zero |
| **File Size** | Compact | Large (unless rewritten) | Medium (Compact base + AOF tail) | N/A |
| **Recovery Speed** | Fast | Slow (requires replaying log) | Fast (Loads RDB then replays small log) | N/A |
| **Performance Impact**| Low (only during `fork`) | Medium (depends on `fsync`) | Medium | Zero |
| **Best For** | Backups, disaster recovery, caching with acceptable data loss | Critical data requiring maximum durability | General production workloads | Pure caching |

**Decision Guide:**
*   Use **Hybrid (AOF + RDB preamble)** for almost all production databases where data loss is unacceptable.
*   Use **RDB only** if you are okay with losing a few minutes of data in exchange for slightly better performance and simpler backups.
*   Use **No Persistence** if Redis is strictly a volatile cache and data can be rebuilt from a primary database (like PostgreSQL).

## 5. Redis Sentinel (HA)

Redis Sentinel provides high availability for a non-clustered Redis setup. It is a separate process (though it uses the same Redis executable) designed to monitor your Redis master and replica instances, detect failures, and automatically perform failover.

### Key Concepts

*   **Monitoring:** Sentinels constantly check if master and replica instances are working as expected.
*   **Notification:** Sentinel can notify the system administrator or other applications via an API that something is wrong.
*   **Automatic Failover:** If a master is not working as expected, Sentinel can start a failover process where a replica is promoted to master, the other additional replicas are reconfigured to use the new master, and the applications using the Redis server informed about the new address to use when connecting.
*   **Configuration Provider:** Sentinel acts as a source of authority for clients service discovery: clients connect to Sentinels in order to ask for the address of the current Redis master responsible for a given service.

### Minimum 3 Sentinels and Quorum

A robust Sentinel deployment requires at least three Sentinel processes running on distinct servers. 

The `quorum` is the number of Sentinels that need to agree about the fact that a master is not reachable in order to officially mark it as failing and eventually start a failover procedure. However, the quorum is only used to detect the failure. In order to actually perform the failover, one of the Sentinels needs to be elected leader for the failover and be authorized to proceed. This requires a strict majority of Sentinels to be available.

For a 3-Sentinel setup, the quorum is typically set to 2.

### SDOWN vs ODOWN

*   **SDOWN (Subjective Down):** This is when a single Sentinel instance perceives a Redis master (or replica) as down based on ping replies. If a Sentinel does not receive a valid reply to a PING within the `down-after-milliseconds` period, it marks the instance as SDOWN.
*   **ODOWN (Objective Down):** ODOWN only applies to masters. A master is marked as ODOWN when enough Sentinels (at least the configured `quorum`) have marked the master as SDOWN and have communicated this to each other via the Gossip protocol. 

### Failover Process

1.  **Failure Detection:** A Sentinel detects an SDOWN. It asks other Sentinels for their state regarding the master. If the quorum is reached, the state is escalated to ODOWN.
2.  **Leader Election:** The Sentinels hold an election using the Raft algorithm to choose a "Leader Sentinel" that will manage the failover.
3.  **Replica Promotion:** The Leader Sentinel selects the best replica to become the new master. Criteria include lowest replication offset, highest priority configuration, and run ID. It sends a `REPLICAOF NO ONE` command to the chosen replica.
4.  **Reconfiguration:** The Leader Sentinel configures the other replicas to replicate from the newly promoted master.
5.  **Client Notification:** Clients connected to Sentinel are notified via Pub/Sub or polling that the master has changed.

### Client Integration

Clients must be Sentinel-aware. Instead of connecting directly to the Redis master IP, the client connects to the Sentinel ensemble and asks for the master's address.

```python
# Python example using redis-py
from redis.sentinel import Sentinel

# Connect to Sentinel instances
sentinel = Sentinel([('192.168.1.10', 26379), 
                     ('192.168.1.11', 26379), 
                     ('192.168.1.12', 26379)], socket_timeout=0.1)

# Get the master address for the cluster named 'mymaster'
master_addr = sentinel.discover_master('mymaster')
print(f"Master address: {master_addr}")

# Get a strictly connected client to the master
master_client = sentinel.master_for('mymaster', socket_timeout=0.1)
master_client.set('foo', 'bar')

# Get a client connected to a replica for read operations
slave_client = sentinel.slave_for('mymaster', socket_timeout=0.1)
print(slave_client.get('foo'))
```

### sentinel.conf Directives

```text
# sentinel.conf
port 26379
dir /tmp

# sentinel monitor <master-group-name> <ip> <port> <quorum>
sentinel monitor mymaster 192.168.1.50 6379 2

# Time in ms before considering an instance SDOWN
sentinel down-after-milliseconds mymaster 5000

# How many replicas can be reconfigured in parallel during failover
sentinel parallel-syncs mymaster 1

# Maximum time for a failover to complete
sentinel failover-timeout mymaster 60000
```

## 6. Redis Replication

Replication allows Redis to create exact copies (replicas) of a master instance. This provides read scalability (offloading read queries to replicas) and is the foundation of high availability.

### Async Replication

By default, Redis replication is asynchronous. When a client writes to the master, the master acknowledges the write to the client immediately and then asynchronously sends the command to its replicas. This means there is a tiny window of time where a write might be lost if the master crashes immediately after acknowledging the client but before transmitting to the replica.

### Full Sync and PSYNC2

When a replica connects to a master for the first time, it triggers a Full Synchronization. The master performs a `BGSAVE` to create an RDB file and sends it to the replica. The replica loads it into memory. During this transfer, the master buffers new write commands and sends them to the replica after the RDB load is complete.

If a replica disconnects momentarily, it can perform a Partial Synchronization (PSYNC). PSYNC2 (introduced in Redis 4.0) improved this significantly. It allows a replica to gracefully failover and become a master without forcing all other replicas to do a full sync. It uses a Replication ID and an offset.

### Replication Backlog (repl-backlog-size)

The master maintains a circular buffer in memory called the replication backlog. It stores recent write commands. When a replica reconnects, it sends its current offset. If the replica's offset is still within the backlog buffer, the master sends only the missing commands (partial sync). If the offset is too old (overwritten in the buffer), a full sync is triggered.

```text
# redis.conf
# Set the backlog size (default 1mb)
repl-backlog-size 10mb
```

### WAIT Command

To achieve synchronous replication for specific commands, use the `WAIT` command. `WAIT numreplicas timeout` blocks the client until the previous write commands have been acknowledged by at least `numreplicas` replicas within the `timeout` in milliseconds.

```bash
127.0.0.1:6379> SET user:1 "John"
OK
127.0.0.1:6379> WAIT 1 1000
(integer) 1 # Returns the number of replicas that acknowledged
```
Note: `WAIT` does not make Redis a strongly consistent database; it only guarantees the write reached the replica's buffer, not that it was saved to disk.

### Replica Stale Reads

If a replica loses connection to the master, you can configure how it behaves via `replica-serve-stale-data`.
*   `yes` (default): The replica continues to serve read requests, possibly returning old data.
*   `no`: The replica returns an error `SYNC with master in progress` for all commands except administrative ones.

## 7. Redis Cluster (Horizontal Scaling)

Redis Cluster provides a way to run a Redis installation where data is automatically sharded across multiple Redis nodes. It provides horizontal scaling and high availability without requiring Sentinel.

### 16,384 Hash Slots

Redis Cluster does not use consistent hashing. Instead, the keyspace is divided into 16,384 logical units called hash slots. Every key in Redis Cluster belongs to exactly one of these hash slots.

The slot is calculated using the formula: `HASH_SLOT = CRC16(key) mod 16384`

### Slot Distribution and Minimum Topology

In a cluster, every master node is responsible for a subset of the 16,384 slots. For example, in a 3-master cluster:
*   Node A contains hash slots from 0 to 5500.
*   Node B contains hash slots from 5501 to 11000.
*   Node C contains hash slots from 11001 to 16383.

A minimal robust cluster requires at least 3 master nodes and 3 replica nodes (one replica for each master), for a total of 6 nodes.

### MOVED and ASK Redirection

Clients connecting to a Redis Cluster must be "Cluster-aware". 
When a client sends a command involving a specific key to a node (Node A) that is not responsible for the key's hash slot, Node A will reply with a `MOVED` error.

```bash
127.0.0.1:7000> SET foo bar
(error) MOVED 12182 127.0.0.1:7001
```

The `MOVED` error includes the correct slot (12182) and the IP/Port (127.0.0.1:7001) of the master responsible for it. The client is expected to update its internal slot map and reissue the command to the correct node.

`ASK` redirection occurs during cluster resharding (when slots are moving between nodes). If a key belongs to a slot currently being migrated, the source node might reply with `ASK`. The client must first send an `ASKING` command to the target node, followed by the actual query.

### Multi-Key Operations and Hash Tags

Redis Cluster generally prohibits commands operating on multiple keys (like `MSET` or `SUNION`) if those keys hash to different slots, as they might live on different physical nodes.

To perform multi-key operations, you can use Hash Tags. If a substring in the key is enclosed in curly braces `{}`, only that substring is hashed.
For example, keys `{user1000}:profile` and `{user1000}:settings` will both hash to the same slot because only `user1000` is fed to the CRC16 algorithm.

### Cluster Gossip Protocol

Nodes in a Redis Cluster communicate using a gossip protocol (running on the cluster bus port, usually base port + 10000). They constantly exchange PING/PONG packets to discover new nodes, propagate cluster state (slot assignments), and detect failures. If a master fails, the remaining majority of masters can authorize a replica to promote itself.

### Sentinel vs Cluster Decision Matrix

| Feature | Sentinel | Cluster |
| :--- | :--- | :--- |
| **Primary Goal** | High Availability (Failover) | Horizontal Scaling + High Availability |
| **Data Sharding** | No (All data on one master) | Yes (Data split across multiple masters) |
| **Max Capacity** | Bound by a single machine's RAM | Virtually unlimited (add more nodes) |
| **Complexity** | Moderate | High |
| **Multi-Key Ops** | Fully supported | Restricted (requires Hash Tags) |
| **Use Case** | Need HA, dataset fits in one server | Need massive scale and throughput |

This concludes the persistence and high availability module. Understanding these concepts is fundamental to running Redis reliably in production.
