# Module 2: Compute Services (EC2, Lambda, Containers)

## Amazon EC2 (Elastic Compute Cloud)
EC2 provides resizable compute capacity in the cloud. It is the fundamental IaaS offering from AWS.

### Instance Types and Families
AWS categorizes EC2 instances into families based on their hardware optimization.
*   **General Purpose (M, T):** Balance of compute, memory, and networking. Good for web servers, code repositories.
*   **Compute Optimized (C):** High performance processors. Good for batch processing, media transcoding, high-performance web servers, machine learning inference.
*   **Memory Optimized (R, X, Z):** Fast performance for workloads that process large datasets in memory. Good for high-performance databases, in-memory caches (Redis/Memcached).
*   **Storage Optimized (I, D, H):** High, sequential read/write access to very large datasets on local storage. Good for NoSQL databases (Cassandra, MongoDB), data warehousing, Elasticsearch.
*   **Accelerated Computing (P, G, Inf, Trn):** Hardware accelerators, or co-processors. Good for Machine Learning training (P, Trn), graphics rendering (G), and ML inference (Inf).

### T-Series Burstable Instances
T-series instances (T2, T3, T4g) are designed for workloads that don't use full CPU consistently.
*   **CPU Credits:** You earn credits when idle and spend them when bursting.
*   **Baseline Performance:** E.g., a `t3.micro` might have a 10% baseline CPU.
*   **T3/T4g Unlimited Mode:** (Default) If you run out of credits, you can continue to burst, but you will be charged extra per vCPU-hour. In standard mode (T2 default), the CPU gets throttled down to the baseline.

### AMIs (Amazon Machine Images)
An AMI provides the information required to launch an instance. It includes:
1.  A template for the root volume (OS, application server, applications).
2.  Launch permissions.
3.  Block device mapping (volumes to attach).
*   **Public AMIs:** Provided by AWS (Amazon Linux 2, Ubuntu, Windows Server).
*   **Marketplace AMIs:** Sold by third-party vendors (e.g., F5 firewall, hardened CIS images).
*   **Private AMIs:** Created by you for your account. You can copy AMIs across regions.

### EC2 Launch and Metadata
*   **User Data:** A script that runs with `root` privileges *only once* during the first boot of the instance. Used to bootstrap the instance (install packages, download code).
    ```bash
    #!/bin/bash
    yum update -y
    yum install -y httpd
    systemctl start httpd
    systemctl enable httpd
    echo "Hello World from $(hostname -f)" > /var/www/html/index.html
    ```
*   **Instance Metadata Service (IMDS):** Allows an instance to retrieve data about itself. Accessed via a special, non-routable IP: `http://169.254.169.254/latest/meta-data/`.
*   **IMDSv1 vs IMDSv2:** IMDSv1 uses a simple GET request. It is vulnerable to Server-Side Request Forgery (SSRF). IMDSv2 requires a PUT request to get a session token, heavily mitigating SSRF risks. *Always enforce IMDSv2.*

### EC2 Storage Options
1.  **EBS (Elastic Block Store):** Network-attached, persistent block storage. Survives instance termination (if configured to). Highly available within a single AZ. (Detailed in M3).
2.  **Instance Store:** Ephemeral, physically attached NVMe SSDs. Extreme high IOPS and low latency. Data is LOST if the instance stops, terminates, or the underlying hardware fails. Good for temporary caches, buffers, scratch data.

### Placement Groups
Control how instances are placed on underlying hardware.
*   **Cluster:** Instances placed close together in the same rack in a single AZ. **Goal:** Lowest latency, highest network throughput (10 Gbps+). **Risk:** Rack failure takes down all instances. Good for HPC, Big Data.
*   **Spread:** Strict placement where each instance is on distinct underlying hardware (different racks, distinct power/network). Max 7 instances per AZ per group. **Goal:** High availability. Good for critical components like primary/secondary databases.
*   **Partition:** Spreads instances across logical partitions (up to 7 per AZ), where each partition is on different hardware. **Goal:** Large distributed workloads (Hadoop, Cassandra, Kafka) where you need to isolate hardware failures across nodes.

### EC2 Hibernate
Instead of stopping (which clears RAM), hibernate saves the in-memory state (RAM) to the EBS root volume. When starting back up, RAM is restored instantly. 
*   **Requirement:** The EBS root volume must be encrypted, and large enough to hold the RAM contents.
*   **Use case:** Applications that take a long time to bootstrap (e.g., heavy Java Spring Boot apps).

### Auto Scaling Groups (ASG)
Automates scaling EC2 instances based on demand.
*   **Launch Templates:** Replaced Launch Configurations. Specifies the AMI, instance type, security groups, key pair, and user data. Supports versioning.
*   **Scaling Policies:**
    *   **Target Tracking:** Simplest. E.g., "Keep average CPU at 50%". AWS handles the math.
    *   **Step Scaling:** E.g., "Add 2 instances if CPU > 70%, add 4 if CPU > 90%".
    *   **Simple Scaling:** Legacy version of step scaling (has a cooldown between steps).
    *   **Scheduled Scaling:** Scale based on known time patterns (e.g., scale out Friday at 5 PM).
*   **Cooldown Period:** Ensures the ASG doesn't launch/terminate additional instances before previous scaling activities take effect.
*   **Health Checks:** ASG can use EC2 status checks or ELB (Elastic Load Balancer) health checks. ELB health checks are strongly recommended because an instance might pass EC2 hardware checks but have a crashed web server.
*   **Lifecycle Hooks:** Pause an instance while it launches or terminates to perform custom actions (e.g., wait for software install, or run a log drain script before terminating).
*   **Mixed Instances Policy:** Allows combining On-Demand and Spot instances (e.g., 20% On-Demand, 80% Spot) across different instance types in a single ASG for cost optimization.

---

## AWS Lambda
Lambda is the core AWS Serverless compute service. You provide the code (Node.js, Python, Java, Go, etc.), and AWS executes it on demand.

### Execution Model
*   Stateless: No affinity to underlying infrastructure.
*   Event-driven: Triggered by S3, API Gateway, SQS, SNS, etc.
*   Container reuse: AWS keeps the execution environment "warm" for a short time after an invocation to handle subsequent requests faster.

### The Cold Start Problem
When a Lambda function is invoked for the first time, or scales up to handle concurrent requests, AWS must provision a new execution environment, download the code, and initialize the runtime. This adds latency (100ms to several seconds, especially for Java/VPC).
*   **Mitigation 1 - Provisioned Concurrency:** Pre-initializes execution environments. Eliminates cold starts, but you pay for the provisioned capacity even if unused.
*   **Mitigation 2 - SnapStart (Java):** Takes a snapshot of the initialized memory/disk state and resumes from the snapshot, reducing startup times by up to 10x for Java.

### Lambda Limits (Know for Interviews)
*   **Timeout:** Maximum 15 minutes. (If a job takes 16 mins, you must use ECS/Fargate or Step Functions).
*   **Memory:** 128 MB to 10,240 MB (10 GB).
*   **CPU:** CPU scales linearly with memory. To get more CPU, allocate more memory.
*   **Storage (`/tmp`):** Up to 10 GB ephemeral storage.
*   **Concurrency:** Soft limit of 1,000 concurrent executions per region across all functions.

### Concurrency Types
*   **Unreserved (Default):** Pulls from the regional pool (1,000).
*   **Reserved Concurrency:** Guarantees a specific number of concurrent executions for a function, AND limits the function to that number. Used to prevent one function from consuming the entire regional limit, or to protect downstream systems (like a small RDS instance) from being overwhelmed.
*   **Provisioned Concurrency:** Pre-warms the environments.

### Invocation Types (Event Sources)
1.  **Synchronous:** The caller waits for the response. Errors must be handled by the caller. (e.g., API Gateway, ALB).
2.  **Asynchronous:** The caller places the event in an internal queue and gets a 202 response. Lambda retries on failure (twice by default). (e.g., S3 Event Notifications, SNS).
3.  **Event Source Mapping:** Lambda service polls a stream or queue on your behalf and invokes the function with batches of records. (e.g., SQS, Kinesis, DynamoDB Streams).

### Lambda Features
*   **Lambda Layers:** Packages containing library dependencies. Allows sharing code across multiple functions (e.g., a custom DB driver). Reduces deployment package size. Max 5 layers/function, max 250MB unzipped limit.
*   **Lambda@Edge vs CloudFront Functions:** Run code at CloudFront edge locations. 
    *   **CloudFront Functions:** Lightweight, sub-ms startup, viewer request/response only, JavaScript only.
    *   **Lambda@Edge:** Can run longer (seconds), access network/VPC, supports Node/Python, runs on all 4 CloudFront events.
*   **Lambda in a VPC:** By default, Lambda runs in AWS-owned VPCs with internet access. If you attach it to your VPC to access private resources (RDS, ElastiCache), AWS creates Elastic Network Interfaces (ENIs). **Crucial:** A Lambda in a private VPC subnet *loses internet access* unless you route its traffic through a NAT Gateway.
*   **Dead Letter Queue (DLQ):** Configure an SQS queue or SNS topic to capture failed *asynchronous* invocations after retries are exhausted.

---

## Container Services (ECS, EKS, Fargate)

### ECS (Elastic Container Service)
AWS's highly scalable, proprietary container orchestration service.
*   **Task Definition:** The blueprint. Defines which Docker image to use, CPU/memory requirements, ports, env vars, IAM task role, and log config.
*   **Task:** A running instance of a Task Definition.
*   **Service:** Maintains a specified number of running tasks (e.g., always keep 3 web server tasks running). Integrates with Load Balancers.

### EKS (Elastic Kubernetes Service)
Managed Kubernetes. AWS manages the Kubernetes control plane (API server, etcd); you manage the worker nodes.
*   **When to choose EKS over ECS:** When you require multi-cloud portability, rely on the open-source K8s ecosystem (Helm, Istio), or have existing Kubernetes expertise. ECS is simpler and tightly integrated with AWS, but proprietary.

### Launch Types (Compute for Containers)
Both ECS and EKS support two underlying compute models:
1.  **EC2 Launch Type:** You provision and manage the underlying EC2 instances. You are responsible for scaling the instances and patching the OS. You pay for the EC2 instances regardless of container utilization.
2.  **Fargate Launch Type:** Serverless compute for containers. You do not provision servers. You simply specify CPU and memory for your tasks, and AWS provisions the exact compute capacity on demand. You pay per vCPU/RAM per hour. Eliminates OS patching overhead.

### ECR (Elastic Container Registry)
AWS's managed Docker registry (equivalent to Docker Hub). Supports private repositories, automated image vulnerability scanning, and lifecycle policies (e.g., "delete untagged images older than 30 days").

### AWS Elastic Beanstalk
A PaaS offering. You upload your code (Java, Node, Python, Docker), and Beanstalk automatically handles the deployment, capacity provisioning, load balancing, auto-scaling, and health monitoring. 
*   **Trade-off:** High speed of deployment, but less fine-grained architectural control compared to raw ECS/EKS.

## GCP Equivalents

| AWS Service | GCP Equivalent |
| :--- | :--- |
| EC2 | Compute Engine |
| ECS | Cloud Run (closer to Fargate) / none direct |
| EKS | GKE (Google Kubernetes Engine) |
| Fargate | Cloud Run / GKE Autopilot |
| Lambda | Cloud Functions |
| Elastic Beanstalk | App Engine |
