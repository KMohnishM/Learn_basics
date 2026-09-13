# Module 3: Storage and Databases

## S3 (Simple Storage Service)
S3 is an object storage service offering industry-leading scalability, data availability, security, and performance.

### Object Storage Fundamentals
*   **Objects:** Files are stored as objects. Each object consists of data, metadata (key-value pairs), and a unique key (name). Max object size is 5TB.
*   **Buckets:** Logical containers for objects. Bucket names must be globally unique across all of AWS.
*   **Flat Namespace:** S3 does not have a real directory hierarchy like a file system. `folder/subfolder/file.txt` is simply an object with a long key name containing slashes. The UI simulates folders using "prefixes".

### Storage Classes
Choosing the right tier is critical for cost optimization.
*   **S3 Standard:** Default. Frequent access, high throughput, low latency. Multi-AZ. (99.99% availability, 11 nines durability).
*   **S3 Intelligent-Tiering:** Uses ML to automatically move objects between frequent and infrequent access tiers based on usage patterns. Small monitoring fee, but no retrieval fees.
*   **S3 Standard-IA (Infrequent Access):** For data accessed less than once a month but requires rapid access when needed. Lower storage cost, but you pay a data retrieval fee. Minimum 30-day storage charge.
*   **S3 One Zone-IA:** Same as IA, but data is stored in a single AZ. Cheaper, but data is lost if the AZ is destroyed. Good for secondary backups.
*   **S3 Glacier Instant Retrieval:** Archive storage with millisecond retrieval. High retrieval fees. Minimum 90-day storage charge.
*   **S3 Glacier Flexible Retrieval:** Archive storage. 3 retrieval speeds: Expedited (1-5 min), Standard (3-5 hr), Bulk (5-12 hr - free). Minimum 90-day charge.
*   **S3 Glacier Deep Archive:** Lowest cost storage in AWS. Retrieval takes 12-48 hours. Minimum 180-day charge.
*   **S3 Outposts:** Brings S3 APIs to your on-premises data center.

### S3 Lifecycle Policies
Automate the movement of objects between storage tiers to save money.
*   **Transition Actions:** E.g., Move to Standard-IA after 30 days, move to Glacier after 90 days.
*   **Expiration Actions:** Delete objects (or specific versions) after 365 days.

### S3 Versioning and Replication
*   **Versioning:** Must be enabled at the bucket level. Keeps multiple variants of an object in the same bucket. Protects against accidental deletes (a "delete marker" is placed on top) and overwrites. You can enable MFA Delete so only the bucket owner with MFA can permanently delete versions.
*   **Replication:** Cross-Region Replication (CRR) for disaster recovery or reducing latency. Same-Region Replication (SRR) for log aggregation. *Requires versioning to be enabled on both source and destination buckets.* By default, only new objects are replicated.

### S3 Security
*   **Bucket Policies:** Resource-based JSON policies attached directly to the bucket. Define who can access the bucket (e.g., granting public read access, or cross-account access).
*   **Block Public Access:** Account or bucket-level setting that overrides bucket policies to prevent accidental data leaks.
*   **Pre-signed URLs:** Generates a temporary URL (using your IAM credentials) that grants time-limited access to download (GET) or upload (PUT) a specific object without requiring AWS credentials from the user.
*   **Object Lock:** Enforces a WORM (Write Once, Read Many) model. 
    *   **Governance Mode:** Admins with special permissions can bypass the lock.
    *   **Compliance Mode:** NO ONE, not even the root user, can delete or overwrite the object until the retention period expires. Used for strict regulatory compliance.

### S3 Performance and Features
*   **Multipart Upload:** Break large files into parts and upload in parallel. Recommended for files > 100MB, *required* for files > 5GB.
*   **S3 Transfer Acceleration:** Uses CloudFront Edge Locations to route uploads over the AWS private network backbone, vastly speeding up long-distance uploads.
*   **S3 Select:** Use SQL expressions to retrieve only a subset of data from a CSV, JSON, or Parquet file. Saves massive amounts of data transfer costs and time.
*   **Event Notifications:** Trigger an SNS topic, SQS queue, or Lambda function when an object is created, deleted, or restored.
*   **Consistency:** S3 provides strong read-after-write consistency for all PUTs and DELETEs.

---

## EBS (Elastic Block Store)
Network-attached block storage, meant to be attached to a single EC2 instance. Bound to a single AZ.

### Volume Types
*   **gp3 (General Purpose SSD):** The default and recommended choice. Baseline 3,000 IOPS and 125 MB/s throughput, regardless of volume size. You can provision extra IOPS/throughput independently.
*   **gp2 (Legacy SSD):** IOPS are tied to volume size (3 IOPS per GB). Small volumes rely on a burst bucket that empties quickly under heavy load.
*   **io2 Block Express (Provisioned IOPS SSD):** For extreme performance. Up to 256,000 IOPS, sub-millisecond latency, 99.999% durability. Use for critical DBs.
*   **st1 (Throughput Optimized HDD):** Max 500 MB/s. Good for streaming, big data, log processing. Cannot be a boot volume.
*   **sc1 (Cold HDD):** Lowest cost. For infrequent access. Cannot be a boot volume.

### EBS Features
*   **Multi-Attach:** (io1/io2 only). Attach a single EBS volume to up to 16 EC2 instances in the same AZ. *Requires a cluster-aware file system (like GFS2) on the instances.*
*   **Snapshots:** Point-in-time, incremental backups stored in S3 (you don't see them in S3 buckets, AWS manages them). Can be copied across regions.
*   **Encryption:** Data at rest, in transit, and snapshots are encrypted using KMS.
    *   *To encrypt an unencrypted volume:* Create a snapshot -> Copy the snapshot and check the "Encrypt" box -> Create a new volume from the encrypted snapshot -> Swap volumes.

---

## EFS (Elastic File System)
Managed Network File System (NFS). Can be attached to 100s of EC2 instances simultaneously across multiple AZs. 
*   **Performance:** Higher latency than EBS.
*   **Use cases:** Content management systems, shared web server directories, machine learning data sets.
*   **Classes:** Standard and Standard-IA (Infrequent Access).
*   **EFS vs FSx:** EFS is for Linux (NFS). FSx for Windows is for Windows File Server (SMB protocol). FSx for Lustre is for extreme HPC (Machine Learning, connects to S3).

---

## RDS (Relational Database Service)
Managed relational database. Supports PostgreSQL, MySQL, MariaDB, Oracle, SQL Server. (Aurora is AWS's proprietary, cloud-native engine).

### RDS Management vs Customer Responsibility
*   **AWS Manages:** OS patching, DB engine patching, backups, replication setup, hardware provisioning.
*   **You Manage:** Application optimization, schema design, security groups.

### Multi-AZ vs Read Replicas (Crucial Distinction)
*   **Multi-AZ (High Availability):** Synchronous replication to a standby instance in a different AZ. If the primary fails, AWS automatically updates the DNS to point to the standby (~1-2 min failover). **The standby is NOT readable.** It is purely for disaster recovery.
*   **Read Replicas (Scalability):** Asynchronous replication to up to 15 (5 for non-Aurora) read-only instances. Used to offload heavy read traffic (reporting, analytics) from the primary. Can be cross-region. Can be promoted to a standalone database.

### RDS Features
*   **RDS Proxy:** A fully managed database proxy. Connection pooling reduces the overhead of opening/closing connections, which is critical for Serverless/Lambda applications connecting to RDS.
*   **Backups:** Automated daily backups (up to 35-day retention) and transaction logs allow Point-In-Time Recovery. Manual snapshots are kept until you delete them. Restoring always creates a *new* database instance.
*   **Encryption:** Enabled at creation via KMS. To encrypt an existing DB, take a snapshot, copy and encrypt it, then restore.

---

## DynamoDB
Fully managed, serverless, NoSQL key-value and document database. Single-digit millisecond performance at any scale.

### Key Concepts
*   **Tables:** Collection of items.
*   **Items:** Collection of attributes (like a row). Max size 400KB.
*   **Primary Key:** Uniquely identifies an item.
    *   **Partition Key (Hash Key):** Determines physical data distribution.
    *   **Partition + Sort Key (Composite Key):** Groups items by partition key, orders them by sort key.

### Capacity Modes
*   **Provisioned:** You specify Read Capacity Units (RCU) and Write Capacity Units (WCU). Cost-effective for predictable workloads. Use Auto Scaling to adjust.
*   **On-Demand:** Pay per request. Zero capacity planning. Best for unpredictable, spiky workloads, or new apps.

### RCU and WCU Calculation
*   **1 WCU:** 1 write per second for an item up to 1KB.
*   **1 RCU:** 1 strongly consistent read per second for an item up to 4KB.
*   **Eventually Consistent Read:** Costs 0.5 RCU (the default).
*   *Example:* Read an 8KB item strongly consistent? 8KB / 4KB = 2 RCUs. Read it eventually consistent? 1 RCU.

### Advanced DynamoDB Features
*   **DAX (DynamoDB Accelerator):** A highly available, in-memory cache for DynamoDB. Delivers microsecond read performance. Requires NO application code changes for reads (it intercepts API calls).
*   **Global Tables:** Multi-region, active-active replication. You write to any region, and it replicates within a second. Uses "last writer wins" for conflict resolution.
*   **DynamoDB Streams:** A time-ordered sequence of item-level changes (INSERT, UPDATE, DELETE). Has a 24-hour retention. Used heavily to trigger Lambda functions in response to DB changes.
*   **TTL (Time to Live):** Automatically delete items after a specific timestamp. The deletion occurs in the background and costs zero WCUs.
*   **Indexes:**
    *   **LSI (Local Secondary Index):** Must be created at table creation time. Shares the partition key, uses a different sort key.
    *   **GSI (Global Secondary Index):** Can be created anytime. Different partition key and sort key. Has its own RCU/WCU provisioned capacity.

## GCP Equivalents

| AWS Service | GCP Equivalent |
| :--- | :--- |
| S3 | Cloud Storage |
| EBS | Persistent Disk |
| EFS | Filestore |
| RDS | Cloud SQL |
| Aurora | Cloud Spanner |
| DynamoDB | Cloud Firestore / Bigtable |
