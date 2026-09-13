# CHEATSHEET: Database Recovery & Replication

## 1. Core WAL Settings (postgresql.conf)

| Parameter | Default | Description |
| :--- | :--- | :--- |
| `wal_level` | `replica` | Controls WAL detail. `minimal` (no replication), `replica` (streaming rep), `logical` (logical rep). |
| `fsync` | `on` | Must be `on` for ACID durability. Forces OS to flush WAL to physical disk. |
| `synchronous_commit` | `on` | Determines when commit is acknowledged. Options: `on`, `off`, `local`, `remote_write`, `remote_apply`. |
| `wal_buffers` | `-1` | Memory for unwritten WAL. Usually auto-tuned based on `shared_buffers`. |

## 2. Checkpoint Settings (postgresql.conf)

| Parameter | Default | Description |
| :--- | :--- | :--- |
| `checkpoint_timeout` | `5min` | Max time between automatic checkpoints. Higher = slower recovery, better performance. |
| `max_wal_size` | `1GB` | Triggers a checkpoint if WAL volume exceeds this before timeout. |
| `checkpoint_completion_target` | `0.9` | Paces checkpoint I/O over 90% of the timeout interval to prevent disk I/O storms. |

## 3. ARIES Recovery Phases

```mermaid
graph LR
    A[CRASH] --> B[1. Analysis]
    B -->|Find active TXNs & dirty pages| C[2. REDO]
    C -->|Repeat history forward| D[3. UNDO]
    D -->|Rollback losers backward| E[ONLINE]
```

## 4. pg_dump Formats (`-F` flag)

| Format | Flag | Description |
| :--- | :--- | :--- |
| Plain Text | `-F p` | Raw SQL script. Cannot be restored in parallel. (Default) |
| Custom | `-F c` | Compressed binary format. Restorable via `pg_restore`. Supports parallel `-j`. |
| Directory | `-F d` | Creates a directory with one file per table. Excellent for parallel dumps/restores. |
| Tar | `-F t` | Uncompressed tarball. Rarely used over Custom/Directory. |

## 5. Vital Replication Queries

**Check Streaming Replication Lag (Run on Primary):**
```sql
SELECT application_name, client_addr, state,
       pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) AS lag_in_bytes
FROM pg_stat_replication;
```

**Monitor Replication Slots (Run on Primary):**
```sql
SELECT slot_name, plugin, slot_type, active,
       pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) AS retained_wal_bytes
FROM pg_replication_slots;
```

## 6. synchronous_commit Levels

| Level | Acknowledges Client When... | Tradeoff |
| :--- | :--- | :--- |
| `off` | Written to local RAM (WAL buffer) | HIGH risk of data loss on crash. Extremely fast. |
| `local` | Written to local disk | Safe locally, but standby might not have data. |
| `on` | Written to standby disk | Zero RPO. High latency (waits for network + standby disk). |
| `remote_write` | Written to standby OS cache | Medium latency. Survives primary crash, fails on double OS crash. |
| `remote_apply` | Applied to standby database | Highest latency. Guarantees queries on standby see the data immediately. |

## 7. PITR (Point-In-Time Recovery) Steps in 60s

1. **Stop** the broken primary database.
2. **Delete** the `/data` directory contents (keep `/pg_wal` if needed).
3. **Restore** the latest `pg_basebackup` physical backup to `/data`.
4. **Touch** an empty file: `touch /data/recovery.signal`.
5. **Configure** `postgresql.conf`:
   - `restore_command = 'cp /wal_archive/%f %p'`
   - `recovery_target_time = 'YYYY-MM-DD HH:MM:SS'`
6. **Start** the database. It will replay WAL and stop exactly at the target time.
