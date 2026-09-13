# CHEATSHEET: Storage and Databases

## S3 Storage Classes

| Storage Class | Use Case | Durability | Access | Retrieval Fee | Min Storage Duration |
|---|---|---|---|---|---|
| **Standard** | Active data, websites, logs | 99.999999999% | Milliseconds | None | None |
| **Intelligent-Tiering** | Unknown/changing access | 99.999999999% | Milliseconds | None (Mgmt fee) | 30 days |
| **Standard-IA** | Backups, accessed < 1/month | 99.999999999% | Milliseconds | Yes (per GB) | 30 days |
| **One Zone-IA** | Re-creatable data, cheap backups| 99.999999999% | Milliseconds | Yes (per GB) | 30 days |
| **Glacier Instant** | Archival, rarely accessed | 99.999999999% | Milliseconds | High | 90 days |
| **Glacier Flexible** | Archival, compliance | 99.999999999% | 1 min - 12 hrs | Yes (unless Bulk) | 90 days |
| **Glacier Deep Archive**| Long-term archival, cheapest | 99.999999999% | 12 - 48 hours | Yes | 180 days |

## EBS Volume Types

| Type | Name | Best For | Max IOPS / Vol | Max Throughput |
|---|---|---|---|---|
| **gp3** | Gen Purpose SSD (New) | System boot, virtual desktops, standard DBs | 16,000 | 1,000 MB/s |
| **gp2** | Gen Purpose SSD (Old) | Legacy workloads (IOPS tied to size) | 16,000 | 250 MB/s |
| **io2** | Provisioned IOPS SSD | Critical DBs (SAP HANA, large Oracle/SQL) | 256,000 | 4,000 MB/s |
| **st1** | Throughput HDD | Big data, data warehouses, log processing | 500 | 500 MB/s |
| **sc1** | Cold HDD | Cold file servers, cheapest block storage | 250 | 250 MB/s |

## EFS vs EBS vs Instance Store

| Feature | EBS | EFS | Instance Store |
|---|---|---|---|
| **Storage Type** | Block | File (NFS) | Block (NVMe) |
| **Attachment** | 1 instance (except io1/io2 Multi-Attach)| 1,000+ instances simultaneously | 1 instance (Physically attached) |
| **Scope** | Single AZ | Multi-AZ | Single underlying host |
| **Persistence** | Survives stop/restart | Survives stop/restart | **Lost** on stop/termination/failure |

## RDS: Multi-AZ vs Read Replicas

| Feature | Multi-AZ | Read Replica |
|---|---|---|
| **Primary Purpose** | Disaster Recovery / High Availability | Scalability / Read Offloading |
| **Replication Type** | Synchronous | Asynchronous |
| **Is Standby Readable?** | **NO** | YES |
| **Cross-Region?** | No | Yes |
| **Failover** | Automatic (managed by AWS DNS change) | Manual (must promote to primary) |

## DynamoDB Capacity Calculation

*   **1 WCU** = 1 write/sec for an item up to 1KB.
*   **1 RCU (Strongly Consistent)** = 1 read/sec for an item up to 4KB.
*   **1 RCU (Eventually Consistent)** = 2 reads/sec for an item up to 4KB. (Default).

*(Always round item size up to nearest KB/4KB boundary before calculating).*
