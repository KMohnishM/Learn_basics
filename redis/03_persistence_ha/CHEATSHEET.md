# Redis Persistence and HA Cheatsheet

## Persistence Comparison

| Feature | RDB (Snapshots) | AOF (Append Only File) | Hybrid (RDB+AOF) |
| :--- | :--- | :--- | :--- |
| **Mechanism** | Point-in-time binary dump | Append-only transaction log | RDB preamble + AOF log |
| **Durability** | Medium (Loses data since last save) | High (Configurable to 1 sec) | High (Configurable to 1 sec) |
| **File Size** | Small (Compact binary) | Large (Requires rewrites) | Medium |
| **Restart Speed**| Fast | Slow | Fast |
| **Command** | `BGSAVE` / `SAVE` | `BGREWRITEAOF` | Standard AOF rewrite |

## AOF `appendfsync` Modes

| Policy | Behavior | Performance | Durability (Max Data Loss) |
| :--- | :--- | :--- | :--- |
| `always` | `fsync` after every command | Very Slow | Zero |
| `everysec` | `fsync` once per second | Fast (Default) | 1 second |
| `no` | OS handles `fsync` | Very Fast | Up to 30s (OS dependent) |

## High Availability Matrix

| Architecture | Setup | Failover | Sharding | Best For |
| :--- | :--- | :--- | :--- | :--- |
| **Standalone** | 1 Node | Manual | None | Dev/Test |
| **Replication** | 1 Master + N Replicas | Manual | None | Read scaling, no HA |
| **Sentinel** | 1 Master + N Replicas + 3 Sentinels | Automatic | None | Standard HA deployments |
| **Cluster** | 3+ Masters + 3+ Replicas | Automatic | Automatic (16384 slots) | Massive scale, high throughput |

## Sentinel Configuration Snippet (`sentinel.conf`)

```text
port 26379
dir /tmp
# monitor <group-name> <ip> <port> <quorum>
sentinel monitor mymaster 127.0.0.1 6379 2
# Time before marking instance Subjective Down (SDOWN)
sentinel down-after-milliseconds mymaster 5000
# Timeout for failover procedure
sentinel failover-timeout mymaster 60000
```

## Redis Cluster Architecture

```text
    Hash Slots (0 - 16383) Distributed Across Masters
    CRC16(key) mod 16384 determines the slot.

       +-------------+        +-------------+        +-------------+
       |   Master A  |        |   Master B  |        |   Master C  |
       | Slots 0-5500|        |Slots 5501-11k        |Slots 11k-16383
       +------+------+        +------+------+        +------+------+
              |                      |                      |
              v                      v                      v
       +-------------+        +-------------+        +-------------+
       |  Replica A1 |        |  Replica B1 |        |  Replica C1 |
       +-------------+        +-------------+        +-------------+
```

## Cluster Client Redirection

When a client queries a node for a key it doesn't own:

1.  **MOVED Error:** Permanent redirection. The slot permanently lives elsewhere.
    *   `Node -> Client`: `(error) MOVED <slot> <target_ip>:<target_port>`
    *   Client updates map, reconnects to target.
2.  **ASK Error:** Temporary redirection during resharding/migration.
    *   `Node -> Client`: `(error) ASK <slot> <target_ip>:<target_port>`
    *   Client connects to target, sends `ASKING`, then sends query. Client does NOT update routing map.

## Hash Tags
Use `{}` in keys to force them into the same hash slot for multi-key operations.
*   Key 1: `{user123}:profile`
*   Key 2: `{user123}:settings`
*   Both hash based solely on `user123`.
