# QnA: Storage and Databases

1. **What is the difference between S3 Standard, S3 Standard-IA, and S3 Glacier? When would you use each?**
   *   **S3 Standard:** For active, frequently accessed data (e.g., website assets, daily logs). High storage cost, zero retrieval cost.
   *   **S3 Standard-IA:** For data accessed less than once a month, but requires immediate access when requested (e.g., backups, old user photos). Lower storage cost, but incurs a per-GB retrieval fee.
   *   **S3 Glacier (Flexible):** For long-term archiving where retrieval times of 3-5 hours are acceptable (e.g., regulatory compliance archives). Lowest storage cost, high retrieval cost/time.

2. **A user needs to upload files directly from the browser to S3 without going through your server. How do you implement this securely?**
   You would use an S3 Pre-signed POST or Pre-signed URL. Your backend server generates a cryptographically signed URL containing the target S3 bucket, key, and expiration time. The browser uses this URL to upload the file directly to S3. This keeps heavy upload traffic off your backend servers while maintaining strict security via temporary IAM permissions.

3. **What is S3 Versioning and what happens when you delete a versioned object?**
   Versioning retains all variants of an object in the bucket. When you issue a standard DELETE request on an object in a versioned bucket, AWS does not delete the data; instead, it places a "Delete Marker" on top, making the object appear deleted. To permanently delete it, you must explicitly request the deletion of the specific version ID.

4. **What is the difference between RDS Multi-AZ and Read Replicas? Can you read from a Multi-AZ standby?**
   *   **Multi-AZ** is for High Availability and Disaster Recovery. It synchronously replicates data to a hidden standby instance in another AZ. You **cannot** read from or access this standby instance.
   *   **Read Replicas** are for Scalability. They asynchronously replicate data, and you route read-heavy traffic (like reporting) to them to reduce load on the primary DB.

5. **Explain RCU and WCU in DynamoDB. How many RCUs does it take to read a 10KB item with strong consistency?**
   WCU (Write Capacity Units) measure 1KB writes per second. RCU (Read Capacity Units) measure 4KB strongly consistent reads per second.
   To read a 10KB item with strong consistency, you round up to the nearest 4KB block, which is 12KB. 
   12KB / 4KB = 3 RCUs. (If it were an eventually consistent read, it would be 3 / 2 = 1.5, rounded up to 2 RCUs).

6. **What is the difference between a DynamoDB LSI and GSI? What are the limitations of each?**
   *   **Local Secondary Index (LSI):** Must be created at table creation. It shares the exact same Partition Key as the base table but uses a different Sort Key. Data size per partition key is limited to 10GB.
   *   **Global Secondary Index (GSI):** Can be created at any time. It can use any attribute as the Partition Key and Sort Key. It acts as an asynchronous shadow table and has its own isolated RCU/WCU settings.

7. **Your DynamoDB table is getting hot partitions. What are the causes and solutions?**
   Hot partitions occur when the partition key design results in uneven traffic distribution (e.g., using `Date` as a partition key, causing all current writes to hit a single partition). 
   *   **Solutions:** Use a high-cardinality attribute for the partition key (e.g., `UserID` or `UUID`). If using a date, append a random suffix to distribute the load (Write Sharding).

8. **What is EBS gp3 and how does it differ from gp2?**
   Both are General Purpose SSDs. `gp2` performance (IOPS and throughput) is strictly tied to the volume size (3 IOPS per GB); to get more speed, you have to over-provision capacity. `gp3` separates these metrics: it provides a baseline of 3,000 IOPS and 125 MB/s regardless of volume size, and allows you to provision extra IOPS and throughput independently of storage capacity, making it significantly more cost-effective.

9. **When would you use EFS vs EBS? What is the key difference in how they attach to instances?**
   Use EBS for single-instance, high-performance block storage (like an OS root drive or a relational database). EBS can normally only attach to *one* EC2 instance at a time and is locked to a single AZ.
   Use EFS when you need a shared, POSIX-compliant file system (like a WordPress `wp-content` folder) that must be mounted by dozens or hundreds of EC2 instances simultaneously across multiple AZs.

10. **What is S3 Transfer Acceleration and when would you use it?**
    It accelerates uploads/downloads of large files over long geographic distances. Instead of routing traffic over the public internet all the way to the S3 region, the client uploads to the nearest CloudFront Edge Location, and the data travels over AWS's optimized, high-speed private backbone network to the S3 bucket.

11. **What is DynamoDB DAX and when is it appropriate? When would you NOT use DAX?**
    DAX (DynamoDB Accelerator) is an in-memory cache for DynamoDB that reduces read latencies from milliseconds to microseconds. It is ideal for read-heavy workloads (like a popular item catalog or game leaderboard). You would NOT use DAX for write-heavy workloads, or for applications requiring strongly consistent reads, as DAX is an eventually consistent cache.

12. **How do you encrypt an existing unencrypted RDS instance?**
    You cannot simply flip a switch on a running, unencrypted instance. You must:
    1. Take a manual snapshot of the unencrypted RDS instance.
    2. Copy the snapshot, and during the copy process, select "Enable Encryption" and provide a KMS key.
    3. Restore a new RDS instance from the encrypted snapshot.
    4. Update your application DNS/connection strings to point to the new encrypted instance.

13. **What is an S3 Pre-signed URL? What are its use cases and security considerations?**
    A Pre-signed URL grants temporary, time-bound permission to perform an action (GET/PUT) on an S3 object without requiring IAM credentials. 
    *   **Use case:** Providing a user a link to download a purchased digital file that expires in 15 minutes.
    *   **Security:** Anyone possessing the URL can access the object until it expires. The permissions granted match the permissions of the IAM principal that generated the URL.

14. **What is the difference between S3 Object Lock Compliance mode and Governance mode?**
    Object Lock enforces a WORM (Write Once, Read Many) model. 
    *   **Governance Mode:** Prevents standard users from deleting the object, but administrators with a specific IAM permission (`s3:BypassGovernanceRetention`) can bypass the lock and delete it.
    *   **Compliance Mode:** Absolutely no one, including the AWS account Root user, can delete the object until the retention period expires. Used for strict legal/financial records.

15. **Your application uses DynamoDB and needs to trigger a Lambda function whenever an item is updated. How do you implement this?**
    You enable DynamoDB Streams on the table, which creates a time-ordered log of item-level modifications (INSERT, MODIFY, REMOVE). You then configure the Lambda function to use the DynamoDB Stream as an Event Source Mapping. The Lambda service will poll the stream and invoke your function with batches of records representing the changes.
