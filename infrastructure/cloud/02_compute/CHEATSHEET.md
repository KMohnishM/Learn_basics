# CHEATSHEET: Compute Services

## EC2 Instance Families

| Family | Name | Best For | Example Use Case |
|---|---|---|---|
| **M** | General Purpose | Balanced CPU/RAM | Web servers, small DBs |
| **T** | Burstable | Spiky workloads | Dev environments, microservices |
| **C** | Compute Optimized | High CPU ratio | Batch processing, video encoding |
| **R, X** | Memory Optimized | High RAM ratio | Redis, Memcached, large RDS |
| **I, D** | Storage Optimized | High local disk I/O | NoSQL (Cassandra), Elasticsearch |
| **P, G** | Accelerated (GPU)| Machine Learning | Training ML models, rendering |

## Lambda Limits (Hard Limits)

| Metric | Limit |
|---|---|
| **Max Execution Time (Timeout)** | 15 minutes (900 seconds) |
| **Max Memory** | 10,240 MB (10 GB) |
| **Ephemeral Storage (/tmp)** | Up to 10,240 MB |
| **Deployment Package (.zip)** | 50 MB (zipped), 250 MB (unzipped) |
| **Container Image Size** | 10 GB |
| **Concurrent Executions** | 1,000 per region (soft limit, can increase) |

## ASG Scaling Policies

| Policy Type | How it works | Example |
|---|---|---|
| **Target Tracking** | You set a target metric; AWS scales to maintain it. | "Keep average CPU at 50%" |
| **Step Scaling** | You define thresholds and step adjustments. | "If CPU > 70 add 2, if > 90 add 5" |
| **Simple Scaling** | Legacy step scaling. | "If CPU > 70 add 2, wait 300s" |
| **Scheduled** | Time-based scaling. | "Scale to 10 at 8 AM Monday" |
| **Predictive** | ML analyzes history to scale ahead of demand. | "Expect daily spike at noon" |

## Container Orchestration Decision Matrix

| Requirement | ECS | EKS | Fargate |
|---|---|---|---|
| Deep AWS Integration | ✅ Best | ❌ Moderate | ✅ Yes |
| Multi-Cloud / Portability| ❌ No | ✅ Best | ❌ No |
| No Server Management | ❌ No (EC2 launch) | ❌ No (managed nodes)| ✅ Best |
| Kubernetes API ecosystem | ❌ No | ✅ Best | ❌ No |
| Learning Curve | Low | High | Low |

## Lambda Invocation Types

| Invocation Type | Example Trigger | Retry Behavior on Failure | Who handles errors? |
|---|---|---|---|
| **Synchronous** | API Gateway, ALB | No automatic retries | The Client/Caller |
| **Asynchronous** | S3 Event, SNS | Retries twice (with backoff)| Sent to DLQ (if configured) |
| **Event Source Map** | SQS, Kinesis, DynamoDB | Retries until data expires | Sent to DLQ (if configured) |
