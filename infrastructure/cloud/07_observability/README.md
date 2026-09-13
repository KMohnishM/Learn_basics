# Module 7: Observability and Management

## The Three Pillars of Observability
To effectively manage cloud infrastructure, you must understand what is happening inside it.
1.  **Metrics:** Numerical time-series data (e.g., CPU at 85%, 500 requests/sec). Tells you *that* there is a problem.
2.  **Logs:** Timestamped text records of discrete events (e.g., "Error: Null pointer at line 42"). Tells you *why* there is a problem.
3.  **Traces:** End-to-end request flows across distributed microservices. Tells you *where* the bottleneck is.

---

## Amazon CloudWatch
The primary monitoring and observability service in AWS.

### CloudWatch Metrics
*   **Standard Metrics:** Automatically collected for most AWS services.
    *   EC2: `CPUUtilization`, `NetworkIn/Out`, `StatusCheckFailed`.
    *   Lambda: `Invocations`, `Errors`, `Duration`, `ConcurrentExecutions`, `Throttles`.
    *   RDS: `DatabaseConnections`, `FreeStorageSpace`.
*   **Hypervisor vs OS Metrics (Important!):** By default, CloudWatch only sees what the AWS hypervisor sees (CPU, Network, Disk I/O). It **cannot** see inside the guest OS. Therefore, memory (RAM) utilization and free disk space are NOT default metrics. To get these, you must install the **CloudWatch Agent** on the EC2 instance.
*   **Custom Metrics:** You can publish your own metrics using the `PutMetricData` API.
    *   Standard resolution: 1-minute granularity.
    *   High resolution: 1-second granularity (costs more).
*   **Metric Math:** Allows you to query multiple metrics and perform math expressions (e.g., calculating error rate: `(Errors / Invocations) * 100`).
*   **Namespaces and Dimensions:** Metrics are logically isolated in Namespaces (e.g., `AWS/EC2`). Dimensions are name/value pairs that uniquely identify a metric (e.g., `InstanceId=i-12345`).

### CloudWatch Alarms
Trigger actions based on metric thresholds.
*   **States:** `OK`, `ALARM`, `INSUFFICIENT_DATA`.
*   **Actions:**
    *   Send an SNS notification (e.g., email the DevOps team).
    *   Trigger an Auto Scaling policy.
    *   Perform an EC2 action: Reboot, Stop, Terminate, or Recover (migrates the instance to healthy hardware).
*   **Composite Alarms:** Combine multiple alarms using Boolean logic (AND/OR). E.g., "Alarm ONLY IF (CPU > 90% AND Memory > 90%)". This drastically reduces alarm fatigue/noise.
*   **Anomaly Detection:** Instead of a static threshold, ML algorithms analyze historical data to create a band of normal behavior and alarm if the metric falls outside the band.

### CloudWatch Logs
*   **Hierarchy:** Log Group (e.g., `/aws/lambda/my-function`) -> Log Stream (represents a specific container/instance) -> Log Events (the actual text lines).
*   **Retention:** By default, logs are kept *forever*, which gets very expensive. **Always set a retention policy** (e.g., 30 days) on your Log Groups.
*   **Metric Filters:** Scan incoming log data for specific string patterns (e.g., "ERROR" or "Exception") and increment a CloudWatch custom metric when found. You can then put an alarm on that metric.
*   **Logs Insights:** A powerful, interactive query engine for logs. Uses a SQL-like syntax. Can automatically discover fields in JSON logs.
    ```text
    fields @timestamp, @message
    | filter @message like /Exception/
    | sort @timestamp desc
    | limit 20
    ```
*   **Subscription Filters:** Stream logs in real-time to destinations like Lambda (for custom processing), Kinesis Data Streams, or Amazon OpenSearch (for advanced dashboarding).
*   **Live Tail:** View logs streaming in real-time in the AWS Console, similar to `tail -f`.

### CloudWatch Agents and Insights
*   **CloudWatch Agent:** Installed on EC2 or on-premises servers to collect OS-level metrics (RAM, swap, disk space) and stream local log files (e.g., `/var/log/syslog`) to CloudWatch Logs. Configured via a JSON file.
*   **Container Insights:** Automated metric and log collection for ECS and EKS. Provides cluster, node, pod, and container-level visibility.
*   **Application Insights:** Automated setup for common enterprise applications (e.g., SQL Server, IIS, Java) to monitor health and identify problems.

---

## AWS X-Ray (Tracing)
Helps developers analyze and debug distributed applications, such as those built using a microservices architecture.

*   **Concepts:**
    *   **Trace:** An end-to-end journey of a single request through the system.
    *   **Segment:** The work done by a single service (e.g., Lambda) for that request.
    *   **Subsegment:** Granular details within a segment (e.g., a specific SQL query or external API call made by the Lambda).
*   **Annotations vs Metadata:**
    *   **Annotations:** Key-value pairs that are *indexed* and can be used with filter expressions (e.g., `user_tier: gold`). Use these to search for traces.
    *   **Metadata:** Key-value pairs of any data type (JSON, objects) that are *not indexed*. Used to store large debugging payloads.
*   **X-Ray Daemon:** For EC2/ECS, you must run the X-Ray daemon alongside your app. The app sends UDP trace data to the daemon, which batches it and sends it to the X-Ray API.
*   **Lambda Integration:** X-Ray is deeply integrated into Lambda. You just check a box ("Enable active tracing"), and Lambda runs the daemon automatically.
*   **Service Map:** A visual graph showing service dependencies, latencies, and error rates (color-coded red/yellow/green).
*   **Sampling:** Tracing 100% of requests is expensive. X-Ray uses sampling. Default: Trace the first request each second, and 5% of any additional requests.

---

## AWS Config
Configuration management and auditing.
*   **Purpose:** Records how your AWS resources are configured and how they change over time.
*   **Config Rules:** Evaluates resources against desired configurations. E.g., "Are all EBS volumes encrypted?" or "Are any S3 buckets public?".
*   **Remediation:** If a resource is flagged as non-compliant, Config can trigger an SSM Automation document to automatically fix it (e.g., instantly terminate an unencrypted EC2 instance).
*   **Configuration Timeline:** Allows you to see exactly what changed on a resource at a specific time, which is invaluable for incident post-mortems.

## AWS Health
*   **Service Health Dashboard:** Public page showing the general status of all AWS services globally.
*   **Personal Health Dashboard:** A personalized view of AWS events that affect *your* specific infrastructure (e.g., "AWS is retiring the underlying hardware for your EC2 instance `i-1234` next week").

## Cost Monitoring
*   **Cost Explorer:** Visual tool to view historical spend, analyze trends, and get RI/Savings Plan recommendations.
*   **AWS Budgets:** Set custom budgets (e.g., $100/month). Can send SNS alerts when actual *or forecasted* costs exceed the threshold.
*   **Cost Allocation Tags:** User-defined tags (e.g., `Project: Alpha`, `Environment: Prod`). You must explicitly activate them in the Billing console. Once active, your bill is broken down by these tags.
*   **AWS Compute Optimizer:** Uses machine learning to analyze historical utilization metrics and recommends right-sizing for EC2, EBS, and Lambda (e.g., "Downsize to t3.small to save $15/mo").

## GCP Equivalents

| AWS Service | GCP Equivalent |
| :--- | :--- |
| CloudWatch Metrics/Alarms | Cloud Monitoring |
| CloudWatch Logs | Cloud Logging |
| AWS X-Ray | Cloud Trace |
| AWS Config | Security Command Center / Asset Inventory |
