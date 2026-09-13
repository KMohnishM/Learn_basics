# QnA: Compute Services

1. **What is the difference between a Cluster, Spread, and Partition placement group? When would you use each?**
   *   **Cluster:** Places instances close together in a single AZ on the same rack. Use for HPC, machine learning, or applications requiring ultra-low network latency.
   *   **Spread:** Strictly places instances on distinct underlying hardware (racks) across AZs (max 7 per AZ). Use for critical, isolated components where simultaneous hardware failure must be avoided.
   *   **Partition:** Divides instances into logical segments called partitions (up to 7 per AZ), with each partition on different hardware. Use for large distributed systems like Hadoop, Cassandra, or Kafka that are partition-aware.

2. **What is EC2 instance metadata and what security risk does IMDSv1 have?**
   Instance metadata is data about an EC2 instance that can be accessed from *within* the instance at `http://169.254.169.254/latest/meta-data/`. It contains IPs, security groups, and IAM role credentials. IMDSv1 is vulnerable to Server-Side Request Forgery (SSRF); if an attacker finds an SSRF vulnerability in a web app on the EC2, they can trick the app into fetching the IAM credentials from the metadata IP. IMDSv2 requires a session token via a PUT request, mitigating this risk.

3. **Explain Lambda cold starts. What are the mitigation strategies and their trade-offs?**
   A cold start occurs when Lambda invokes a function that doesn't have a pre-warmed execution environment. AWS must allocate compute, download code, start the runtime, and run initialization code. 
   *   **Mitigation 1 (Provisioned Concurrency):** Keeps environments initialized and ready. *Trade-off:* You pay for this capacity continually, defeating the "pay only when running" benefit of serverless.
   *   **Mitigation 2 (SnapStart for Java):** Caches a snapshot of the initialized memory state. *Trade-off:* Only available for Java; you must handle uniqueness (e.g., pseudo-random number seeds must be refreshed after restore).

4. **What is the difference between reserved concurrency and provisioned concurrency in Lambda?**
   *   **Reserved Concurrency:** Sets a maximum limit on how many concurrent executions a specific function can have. It reserves that capacity from the regional pool but does *not* pre-warm them. It is used to throttle functions and protect downstream resources.
   *   **Provisioned Concurrency:** Pre-initializes execution environments so they are warm and ready to respond immediately, eliminating cold starts.

5. **When would you choose ECS over EKS? When would you choose EKS?**
   *   Choose **ECS** when you want a simpler, AWS-native container orchestration tool with deep integration into IAM, ALB, and CloudWatch, and you do not want to manage control planes.
   *   Choose **EKS** (Kubernetes) when you need multi-cloud portability, require advanced orchestration features, want to use the massive K8s open-source ecosystem (Helm charts, Istio), or already have a team skilled in Kubernetes.

6. **What is Fargate? What are you NOT responsible for when using Fargate vs EC2 launch type?**
   Fargate is a serverless compute engine for containers that works with both ECS and EKS. With Fargate, you are NOT responsible for provisioning, configuring, or scaling EC2 instances, nor are you responsible for OS-level patching or security hardening of the container host. You only manage the container image, CPU/memory limits, and IAM roles.

7. **Explain the difference between synchronous, asynchronous, and event source mapping invocation in Lambda.**
   *   **Synchronous (e.g., API Gateway):** The client waits for the response. Errors are returned to the client to handle.
   *   **Asynchronous (e.g., S3 events):** Lambda queues the event and returns immediately. If execution fails, Lambda retries twice automatically before sending to a DLQ.
   *   **Event Source Mapping (e.g., SQS, Kinesis):** Lambda infrastructure polls the queue/stream on your behalf and passes batches of records to your function synchronously.

8. **What is a Lambda Layer and what problem does it solve?**
   A Lambda Layer is a .zip file archive that contains libraries, a custom runtime, or other dependencies. It solves the problem of bloated deployment packages and redundant code. Instead of packaging the same 50MB library with 10 different functions, you put it in a Layer and configure the functions to reference it, reducing deployment times and keeping deployment packages small.

9. **What is an Auto Scaling Group lifecycle hook? Give a practical use case.**
   A lifecycle hook allows you to pause an EC2 instance as it launches or terminates, placing it in a wait state while you perform custom actions. 
   *   **Use case (Termination):** Before an instance scales in, a lifecycle hook pauses it. A Lambda function triggers via EventBridge, connects to the instance, drains remaining active connections, uploads local logs to S3, and then signals the ASG to continue termination.

10. **What is the difference between EC2 Instance Store and EBS? When would you use each?**
    EBS is network-attached, persistent block storage that survives instance stops. Instance Store is physically attached NVMe SSD storage that is ephemeral (data is lost if the instance stops or hardware fails). Use Instance Store for extreme high I/O temporary data (caches, buffers, scratch space). Use EBS for OS root volumes and persistent databases.

11. **How does Lambda handle failures for async invocations vs synchronous invocations?**
    *   **Async:** Lambda automatically retries the invocation twice (with delays). If all retries fail, it discards the event or sends it to a Dead Letter Queue (DLQ) if configured.
    *   **Sync:** Lambda does not retry. It returns the error response (e.g., HTTP 5xx) immediately to the caller (like API Gateway), and the caller must implement the retry logic.

12. **What is Lambda SnapStart and how does it differ from Provisioned Concurrency?**
    SnapStart (currently for Java) takes a snapshot of the execution environment's memory and disk state *after* the initialization phase. When invoked, it resumes from the snapshot. It's free (you pay standard invocation costs). Provisioned Concurrency keeps live execution environments running constantly, waiting for requests, and you pay an hourly rate for them regardless of usage.

13. **Your Lambda function needs to access a private RDS database. What do you need to configure?**
    You must configure the Lambda function to connect to the VPC by providing the VPC Subnet IDs and a Security Group. The Security Group must allow outbound access, and the RDS Security Group must allow inbound access from the Lambda SG. *Crucially*, if the Lambda also needs to reach the public internet (e.g., to call a 3rd party API), it must be placed in a private subnet with a route to a NAT Gateway.

14. **What is the difference between a Launch Template and a Launch Configuration?**
    Both define how an ASG launches instances (AMI, instance type, SG, user data). Launch Configurations are the legacy method and are immutable (you must create a new one to change anything). Launch Templates are the modern standard: they support versioning, allow mixing On-Demand and Spot instances, support T2/T3 unlimited configurations, and are required for newer EC2 features.

15. **Explain T-series CPU credits. What happens when a T3 instance runs out of credits in standard mode?**
    T-series instances earn CPU credits at a set rate when they operate below their baseline CPU utilization. When CPU spikes, they spend credits to burst to 100% CPU. If a T3 instance in *Standard mode* runs out of credits, its CPU performance is abruptly throttled down to the baseline level (e.g., 20%), which severely degrades application performance. (In Unlimited mode, it continues to burst but you are charged overage fees).
