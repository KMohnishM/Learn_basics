# Recovery Systems Q&A

**1. Explain Write-Ahead Logging (WAL). What is the WAL rule? Why does writing WAL sequentially perform better than writing data pages randomly on spinning disks?**
Write-Ahead Logging (WAL) is the foundational mechanism ensuring data integrity and durability in relational databases. The core WAL rule dictates that changes to database files (tables and indexes) must only be written to persistent storage *after* the log records describing those changes have been flushed to permanent storage. When a transaction commits, PostgreSQL does not immediately write the modified data pages to disk. Instead, it writes a description of the changes (the WAL record) to the WAL file and fsyncs it. This guarantees that if a crash occurs, the database can read the WAL and replay the changes to restore the state. Writing WAL performs drastically better than writing data pages because WAL writes are strictly sequential appends. On spinning hard disk drives (HDDs), sequential I/O is orders of magnitude faster than random I/O because it avoids the physical mechanical delay of moving the disk head (seek time) across the platter. Even on SSDs, sequential writes are more efficient for the flash translation layer, minimizing write amplification and maximizing throughput.
```sql
-- Checking WAL configuration and current status
SHOW wal_level;
SHOW fsync; -- Should always be ON in production
SELECT pg_current_wal_lsn(); -- Returns the current write location
```

**2. What is a PostgreSQL checkpoint? What I/O operations happen during a checkpoint? What is `checkpoint_completion_target = 0.9` and why does it help I/O performance?**
A PostgreSQL checkpoint is a deliberate, synchronized event that guarantees all modified (dirty) data pages currently residing in memory (shared buffers) are written out to persistent storage. During a checkpoint, the database flushes dirty buffers to disk, creates a special checkpoint record in the WAL, and updates the control file to point to this record. This establishes a new, guaranteed starting point for crash recovery, meaning WAL files prior to this point are no longer needed for recovery and can be recycled or removed. Because a checkpoint writes potentially gigabytes of random data pages to disk, it can cause a massive I/O spike that halts concurrent transactions. The parameter `checkpoint_completion_target` mitigates this. By setting it to `0.9` (the standard recommendation), you instruct PostgreSQL to spread the checkpoint I/O out over 90% of the time interval until the next scheduled checkpoint. Instead of flushing all dirty pages immediately in a sudden burst, the background writer gently trickles the writes to disk, smoothing out the I/O profile and preventing performance degradation for application queries.
```sql
-- Checking checkpoint settings
SHOW checkpoint_timeout; -- Typically 5 to 15 minutes
SHOW max_wal_size; -- Target size before forcing a checkpoint
SHOW checkpoint_completion_target; -- Should be 0.9
```

**3. Explain the ARIES recovery algorithm. Describe each phase: Analysis, REDO, and UNDO. Why must REDO happen before UNDO (the 'repeat history' principle)?**
ARIES (Algorithm for Recovery and Isolation Exploiting Semantics) is the industry-standard algorithm used by database systems for crash recovery. It operates in three distinct phases. 1) The Analysis phase scans the WAL forward from the last successful checkpoint to determine the exact state of the database at the moment of the crash. It identifies which pages were dirty and which transactions were active but uncommitted. 2) The REDO phase scans the WAL forward again, reapplying every single logged change to the data pages, regardless of whether the transaction that made the change eventually committed or aborted. This brings the database to the exact physical state it was in at the time of the crash (the 'repeat history' principle). 3) The UNDO phase scans the WAL backward, identifying the operations of all transactions that were active at the time of the crash (and thus cannot commit) and reversing their effects to guarantee atomicity. REDO must happen before UNDO because the database must first reconstruct the exact physical layout of the pages before it can safely navigate the complex internal structures (like B-tree splits) to perform logical undo operations.
```sql
-- Conceptual illustration: A crash occurs at LSN 100
-- WAL LSN 90: Checkpoint starts
-- WAL LSN 95: T1 updates row (uncommitted)
-- WAL LSN 98: T2 inserts row (commits)
-- Crash!
-- Analysis: Finds T1 active, T2 committed.
-- REDO: Replays LSN 95 and LSN 98 to restore physical state.
-- UNDO: Reverses LSN 95 because T1 never committed.
```

**4. What is the difference between `pg_dump` (logical) and `pg_basebackup` (physical) backup? When would you use each? What does `-F c` (custom format) provide that `-F p` (plain SQL) does not?**
`pg_dump` performs a logical backup. It connects to the database, queries the data, and generates a stream of SQL commands (like CREATE TABLE and INSERT) required to reconstruct the database. It is highly flexible: you can backup individual tables, restore across different PostgreSQL versions, or even migrate to a different OS architecture. `pg_basebackup` performs a physical backup. It creates an exact binary copy of the database cluster's files on disk. It is strictly used for cloning a server, setting up replication, or performing Point-in-Time Recovery (PITR). You cannot restore a physical backup across different PostgreSQL major versions or OS architectures. You use `pg_dump` for granular exports, schema migrations, or logical preservation. You use `pg_basebackup` for disaster recovery and spinning up replicas. When using `pg_dump`, the `-F c` (custom) format provides a compressed, binary archive that allows `pg_restore` to selectively restore specific tables, reorganize the restore order, and utilize multiple CPU cores for parallel restoration. The `-F p` (plain SQL) format produces a massive text file that must be executed sequentially, making it significantly slower and less flexible.
```bash
# Logical backup (custom format, highly flexible)
pg_dump -U postgres -F c -f db_backup.dump mydb

# Physical backup (exact binary clone, includes WAL)
pg_basebackup -U replicator -D /var/lib/postgresql/data -X stream -P
```

**5. Explain Point-in-Time Recovery (PITR) in PostgreSQL. What two things do you need (base backup + WAL archive)? Walk through the exact steps to restore to a specific timestamp.**
Point-in-Time Recovery (PITR) is a disaster recovery technique that allows you to restore a database to its exact state at any specific microsecond in the past, effectively undoing catastrophic human errors like an accidental `DROP TABLE`. To perform PITR, you require two components: a physical base backup (taken via `pg_basebackup`) and an unbroken, continuous archive of all WAL files generated since that base backup. The steps are as follows: 1) Stop the running PostgreSQL server. 2) Move or delete the corrupted data directory. 3) Restore the physical base backup to the data directory. 4) Clean out the `pg_wal` directory in the restored backup. 5) Create a `recovery.signal` file in the data directory. 6) Edit `postgresql.conf` (or `recovery.conf` in older versions) to configure the `restore_command` to fetch WAL files from the archive, and set the `recovery_target_time` to the exact timestamp right before the disaster occurred. 7) Start PostgreSQL. The server will enter recovery mode, fetch the WAL files, and replay transactions up to the specified target time, then open for read-write operations.
```ini
-- Configuration in postgresql.conf for PITR
restore_command = 'cp /mnt/wal_archive/%f %p'
recovery_target_time = '2023-10-25 14:30:00 UTC'
recovery_target_action = 'promote'
```

**6. What is streaming replication? What postgresql.conf settings are required on the primary (wal_level, max_wal_senders)? How do you check replication lag from both the primary and the replica?**
Streaming replication is PostgreSQL's built-in mechanism for maintaining a continuous, physical, byte-for-byte replica of a primary database. The primary server streams WAL records continuously over a network connection to the replica server, which applies them to its own data directory. To configure this on the primary, `wal_level` must be set to `replica` (or `logical`) to ensure enough information is logged. The `max_wal_senders` parameter must be set to a value greater than zero, dictating how many concurrent replicas can connect. On the replica, it runs continuously in recovery mode, pulling and applying the WAL. To monitor replication lag from the primary, you query the `pg_stat_replication` view, comparing the `pg_current_wal_lsn()` with the `replay_lsn` reported by the connected replica. To check lag from the replica itself, you query the `pg_stat_wal_receiver` view and compare the last received LSN with the last replayed LSN, or use `pg_last_xact_replay_timestamp()` to see how far behind the data is in real time.
```sql
-- Checking lag from the Primary server
SELECT application_name, state, 
       sync_state, 
       pg_current_wal_lsn() - replay_lsn AS byte_lag
FROM pg_stat_replication;

-- Checking lag from the Replica server
SELECT now() - pg_last_xact_replay_timestamp() AS replication_delay;
```

**7. What is the difference between physical streaming replication and logical replication? Give 3 specific use cases where logical replication is the better choice.**
Physical streaming replication operates at the binary disk-block level; it blindly copies every single byte changed in the entire database cluster, including all databases, system catalogs, and indexes. The replica must run the exact same major version and OS architecture, and it is strictly read-only. Logical replication, conversely, operates at the data level by decoding the WAL into standard SQL operations (INSERT, UPDATE, DELETE) using a publish/subscribe model. It copies logical data rows. Three specific use cases where logical replication is superior: 1) Selective replication: You can replicate a single specific table or database rather than the entire cluster, saving immense bandwidth and storage. 2) Zero-downtime major version upgrades: You can replicate from a PostgreSQL 13 primary to a PostgreSQL 16 replica, then switch traffic over. 3) Data integration and consolidation: You can replicate specific tables from multiple disparate regional databases into a single central data warehouse for analytics, which physical replication cannot do because it demands total ownership of the cluster.
```sql
-- Setting up Logical Replication
-- On Primary (Publisher):
CREATE PUBLICATION sales_pub FOR TABLE orders, customers;

-- On Replica (Subscriber):
CREATE SUBSCRIPTION sales_sub 
CONNECTION 'host=primary_ip dbname=mydb user=repl' 
PUBLICATION sales_pub;
```

**8. What is a replication slot? Describe the specific disk failure scenario that an inactive replication slot causes. How do you monitor and prevent it with SQL queries?**
A replication slot is a safeguard mechanism on the primary database that ensures WAL files are not deleted until all connected replicas have successfully received and acknowledged them. Without replication slots, if a replica disconnects for an hour, the primary might recycle old WAL files; when the replica reconnects, the required WAL is gone, permanently breaking replication. While slots provide safety, they introduce a massive risk: if a replica disconnects permanently and its slot remains inactive on the primary, the primary will hoard WAL files indefinitely. This will eventually fill the entire disk of the primary server, causing the database to crash and shut down entirely—a severe disk failure scenario. To prevent this, DBAs must aggressively monitor `pg_replication_slots`. If a slot is inactive or retaining excessive amounts of WAL, it must be manually dropped. Modern PostgreSQL introduced `max_slot_wal_keep_size` to automatically invalidate slots before they crash the disk.
```sql
-- Monitoring replication slots for bloat
SELECT slot_name, plugin, active, 
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained_wal
FROM pg_replication_slots;

-- Dropping a dangerous, inactive slot
SELECT pg_drop_replication_slot('stale_replica_slot');
```

**9. Explain the five `synchronous_commit` levels: `on`, `remote_write`, `remote_apply`, `local`, `off`. For each, state what is guaranteed before COMMIT returns and the latency impact.**
The `synchronous_commit` parameter dictates exactly when PostgreSQL acknowledges a COMMIT success to the client, trading off performance for data durability. `off`: The commit returns immediately after handing data to the OS; it does not wait for disk fsync. Extremely fast, but a server crash loses recent commits. `local`: The commit waits until the WAL is fsync'd to the local disk. High durability locally, standard latency. `remote_write`: The commit waits until the local disk is fsync'd AND the synchronous replica confirms it has written the WAL to its OS cache (but not necessarily fsync'd). Higher latency, protects against primary node destruction. `on` (default for sync replication): The commit waits until the local disk is fsync'd AND the synchronous replica confirms it has fully fsync'd the WAL to its physical disk. Very high latency, guarantees zero data loss if primary burns down. `remote_apply`: The highest safety level. The commit waits until the local disk is fsync'd AND the synchronous replica has actually applied the WAL to its data pages, making the data instantly visible to read queries on the replica. Highest latency, guarantees read-your-writes consistency across the cluster.
```sql
-- Setting synchronous_commit dynamically per transaction
BEGIN;
SET LOCAL synchronous_commit = 'remote_apply';
UPDATE financial_ledger SET balance = balance + 1000 WHERE id = 1;
COMMIT; -- Will block until replica fully applies the change
```

**10. What is `pg_rewind`? When is it needed after a failover? How does it differ from running a fresh `pg_basebackup` to resync a former primary? What data does it copy?**
`pg_rewind` is a specialized utility used to resynchronize a former primary database with a newly promoted primary following a failover event. When a failover occurs, the new primary's timeline diverges from the old primary. The old primary has some transactions locally that were never replicated before it died. You cannot simply connect it as a replica because its timeline is fundamentally incompatible. `pg_rewind` solves this. It scans the old primary, identifies the exact point in the WAL where the timelines diverged, and essentially "rewinds" the old primary's data files to that point. It achieves this by connecting to the new primary, determining which blocks changed since the divergence, and copying *only* those specific modified blocks over. It differs from `pg_basebackup` primarily in speed and efficiency. A `pg_basebackup` deletes the entire old cluster and copies 100% of the database across the network, which could take hours for terabytes of data. `pg_rewind` only copies the megabytes of data that changed, completing in seconds and rapidly re-establishing high availability.
```bash
# Executing pg_rewind on the old, demoted primary
pg_rewind --target-pgdata=/var/lib/postgresql/data \
          --source-server='host=new_primary_ip dbname=postgres' \
          --progress
```

**11. What is Patroni? How does it use etcd for leader election? Describe the automatic failover sequence step by step. What prevents split-brain if the old primary comes back?**
Patroni is a robust, Python-based daemon template for managing PostgreSQL high availability (HA). It relies on a Distributed Configuration Store (DCS), typically etcd, Consul, or ZooKeeper, to maintain cluster state and handle leader election. The DCS provides strong consistency and distributed consensus. The failover sequence operates as follows: 1) Each Patroni agent continuously sends heartbeats to etcd, maintaining an ephemeral lock on the "leader" key. 2) If the primary PostgreSQL instance crashes, its Patroni agent stops updating the lock. 3) The lock in etcd expires due to a TTL timeout. 4) The remaining replica Patroni agents detect the missing lock and immediately race to acquire it. 5) The DCS ensures only one node wins the lock (leader election). 6) The winning agent promotes its local PostgreSQL instance to be the new primary. 7) The losing agents reconfigure their local PostgreSQL instances to stream from the newly promoted primary. Split-brain (where two nodes both think they are primary) is prevented through fencing and DCS consensus. If the old primary comes back, its Patroni agent checks etcd, sees another node holds the leader key, realizes it is demoted, and refuses to open PostgreSQL for writes, forcing it into a replica state.
```yaml
# Example Patroni configuration snippet (patroni.yml)
scope: pg_cluster_production
name: node_1
restapi:
  listen: 0.0.0.0:8008
etcd:
  host: 10.0.0.5:2379
postgresql:
  listen: 0.0.0.0:5432
```

**12. Define RPO and RTO. For a payment processing system targeting RPO=0 and RTO<60s, describe the complete PostgreSQL HA setup (replication type, synchronous_commit level, HA tool, routing).**
Recovery Point Objective (RPO) is the maximum acceptable amount of data loss measured in time (e.g., how many minutes of transactions can we lose). Recovery Time Objective (RTO) is the maximum acceptable downtime required to restore the system to full operational status. For a payment system demanding RPO=0 (zero data loss) and RTO<60s (near-instant failover), the architecture must be aggressive. You must use physical streaming replication to at least two replica nodes. To guarantee RPO=0, you must set `synchronous_commit = 'on'` (or `remote_apply`) and configure `synchronous_standby_names` to ensure transactions do not commit locally until written to a replica. For RTO<60s, human intervention is too slow; you must use an automated HA daemon like Patroni backed by a highly available etcd cluster. Patroni handles the sub-minute leader election and promotion. Finally, for routing, you deploy a reverse proxy like HAProxy combined with PgBouncer. HAProxy uses HTTP health checks against Patroni's REST API to dynamically route read/write traffic strictly to whichever node currently holds the primary lock, ensuring the application reconnects seamlessly in seconds.
```ini
-- postgresql.conf on primary enforcing RPO = 0
wal_level = replica
max_wal_senders = 5
synchronous_standby_names = 'ANY 1 (replica_1, replica_2)'
synchronous_commit = on
```

**13. What is the difference between WAL archiving (archive_command) and WAL streaming? Can both be active simultaneously? Why would you run both together?**
WAL streaming and WAL archiving serve different aspects of data protection. WAL streaming operates over a continuous, persistent network socket where the primary actively pushes WAL records to a connected replica in near real-time, often synchronously. It is designed for immediate High Availability and failover. WAL archiving, configured via the `archive_command`, executes a shell script every time a 16MB WAL file is completed, copying the entire file to external, durable, and cheap storage (like an AWS S3 bucket or NFS share). It is designed for long-term disaster recovery and Point-in-Time Recovery (PITR). Yes, both can and absolutely should be active simultaneously. You run them together to cover all failure modes. If the entire data center hosting the primary and replicas burns down (meaning HA streaming fails), the external WAL archive in S3 survives, allowing you to build a new cluster from scratch and apply PITR. Furthermore, if a replica falls too far behind and the primary recycles its WAL, the replica can seamlessly fall back to fetching the missing files from the archive via `restore_command`, repairing replication automatically.
```bash
# Example archive_command utilizing AWS CLI
archive_command = 'aws s3 cp %p s3://my-db-backups/wal/%f'
# Streaming is handled independently via max_wal_senders
```

**14. What is `archive_timeout`? If it is not set and the database is low-traffic (no writes for 2 hours), what is the maximum data loss window on crash? What value do most production systems use?**
The `archive_timeout` parameter forces PostgreSQL to rotate to a new WAL file and trigger the `archive_command` if the specified amount of time has elapsed since the last rotation, even if the current 16MB WAL file is only partially full. In a low-traffic database without this setting, a few transactions might be written, but the WAL file won't reach 16MB for hours. The `archive_command` only runs on completed files. If the server suffers catastrophic disk failure after 2 hours of no writes, the current, partially filled WAL file on disk is destroyed. Because it was never archived, those transactions are permanently lost. Therefore, the maximum data loss window in that scenario is dictated entirely by how long it takes to fill 16MB. To bound this data loss window, production systems typically set `archive_timeout` to `60` (1 minute) or `300` (5 minutes). This guarantees that in the worst-case scenario of total disk annihilation, the maximum amount of data lost is limited to the last 5 minutes of activity, satisfying RPO requirements.
```ini
-- Enforcing a maximum 5-minute data loss window for archives
archive_mode = on
archive_command = '/usr/local/bin/archive_script.sh %p %f'
archive_timeout = 300
```

**15. How does PostgreSQL perform crash recovery automatically on startup? What does it do with committed transactions whose changes weren't flushed to data files? What about uncommitted transactions?**
When PostgreSQL starts up, the postmaster process inspects the `pg_control` file. If the database was not shut down cleanly, the control file indicates a crashed state, and PostgreSQL automatically enters crash recovery mode before accepting client connections. It begins by reading the WAL from the location of the last valid checkpoint. For committed transactions whose changes resided only in memory and were not flushed to the data files before the power loss, PostgreSQL finds their REDO records in the WAL. It systematically applies these changes to the data pages on disk, guaranteeing durability. For transactions that were uncommitted (in progress) at the moment of the crash, their changes might have been written to the WAL, and some of those dirty data pages might even have been flushed to disk by a background writer. PostgreSQL will initially apply these REDO records, but during the UNDO phase of recovery, it realizes the transaction lacks a COMMIT record. It uses the undo information to meticulously reverse those modifications, ensuring that partial, uncommitted data is entirely removed from the active database, guaranteeing atomicity.
```sql
-- Crash recovery is automatic, but progress can be monitored in logs:
-- LOG:  database system was interrupted; last known up at 2023-10-25 10:00:00
-- LOG:  database system was not properly shut down; automatic recovery in progress
-- LOG:  redo starts at 0/1A2B3C4D
-- LOG:  redo done at 0/1A2F5D6E
-- LOG:  database system is ready to accept connections
```
