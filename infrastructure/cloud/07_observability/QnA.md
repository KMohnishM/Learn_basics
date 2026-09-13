# QnA: Observability and Management

1. **What is the difference between CloudWatch metrics and CloudWatch Logs? How do you create a metric from log data?**
   Metrics are numerical time-series data points (like CPU %), while Logs are textual records of events (like application error messages). You can create a metric from log data using **CloudWatch Metric Filters**. You define a pattern (e.g., the word "Exception"), and every time that pattern appears in the log stream, CloudWatch increments a custom metric, which you can then use to trigger an alarm.

2. **Why can't CloudWatch see memory utilization of an EC2 instance by default? How do you fix this?**
   By default, CloudWatch metrics are collected at the hypervisor level. The hypervisor can see how much CPU cycle time or network bandwidth the VM is using, but the guest operating system's RAM (memory allocation) and file system (disk space) are opaque to it. To fix this, you must install and configure the **CloudWatch Agent** inside the EC2 instance OS.

3. **What is a CloudWatch Composite Alarm and why would you use it?**
   A Composite Alarm aggregates the state of multiple standard alarms using Boolean logic (AND, OR, NOT). You use it to reduce alarm noise/fatigue. For example, instead of getting paged every time CPU spikes (which might be normal during a cron job), you create a composite alarm that only pages you if `(CPU_Alarm AND High_Latency_Alarm AND DB_Connection_Alarm)` are all firing simultaneously, indicating a true system degradation.

4. **What is the difference between CloudWatch Logs Insights and Subscription Filters?**
   *   **Logs Insights** is an interactive, ad-hoc querying engine. You use it in the console to manually run SQL-like searches across your logs when actively investigating an issue.
   *   **Subscription Filters** are automated routing rules. They continuously evaluate incoming log events in real-time and stream matches to a destination (like a Lambda function or OpenSearch) for automated processing or long-term indexing.

5. **Explain X-Ray annotations vs metadata. Which can you filter on in the X-Ray console?**
   Both allow you to attach custom data to an X-Ray trace segment. 
   *   **Annotations** are key-value pairs that are *indexed* by the X-Ray search engine. You **can filter** and search for traces based on annotations (e.g., search for all traces where `customer_tier = premium`).
   *   **Metadata** can be any data (including nested JSON objects) but is *not indexed*. You cannot search by metadata; you use it to store large debugging payloads to view once you have found the trace.

6. **What is X-Ray sampling and why is it necessary?**
   Sampling is the process of deciding which requests get traced and which are ignored. In a high-traffic production system (e.g., 10,000 req/sec), tracing every single request would generate massive amounts of data, incur high costs, and slow down the application. By default, X-Ray samples the first request every second, plus 5% of any additional requests, providing a statistically significant view of performance without the overhead.

7. **What is the difference between CloudTrail and AWS Config? When would you use each?**
   *   **CloudTrail** answers "Who made this API call, and when?" It logs the *actions* taken in the account (e.g., User Bob called `DeleteBucket` at 10:00 AM).
   *   **AWS Config** answers "What did this resource look like over time, and is it compliant?" It logs the *state* of the resource (e.g., Bucket X was public at 9:59 AM, and deleted at 10:00 AM). Use Config for compliance checks and CloudTrail for security auditing.

8. **How would you set up alerts for Lambda errors using CloudWatch?**
   AWS Lambda automatically publishes standard metrics to CloudWatch, including the `Errors` metric. To set up an alert, you navigate to CloudWatch Alarms, select the `AWS/Lambda` namespace, choose your function's `Errors` metric, and set a threshold (e.g., `Errors > 0 for 1 datapoint within 1 minute`). You then configure the alarm action to send a message to an SNS topic subscribed to by your DevOps team.

9. **What is CloudWatch Container Insights and what does it provide that standard metrics don't?**
   Container Insights is a feature designed specifically for ECS, EKS, and Fargate. While standard metrics might show the overall EC2 instance CPU, Container Insights collects, aggregates, and summarizes metrics and logs at the container ecosystem level—giving you granular visibility into the performance of individual clusters, services, tasks, pods, and containers.

10. **How would you investigate a production incident using CloudTrail, X-Ray, and CloudWatch Logs together?**
    If users report a feature is failing:
    1. Look at **X-Ray** service maps to identify which specific microservice is showing high latency or red error rates. Click into a slow trace.
    2. The trace reveals a specific Lambda function is failing. Use the Trace ID to pivot directly into **CloudWatch Logs** for that specific execution to read the exact stack trace/error message.
    3. If the error indicates an IAM permission denial, check **CloudTrail** around the incident time to see if an administrator recently modified the Lambda execution role.

11. **An AWS Config rule flags your S3 bucket as non-compliant. How do you auto-remediate it?**
    You can link an AWS Systems Manager (SSM) Automation document to the AWS Config rule. When Config evaluates the bucket and marks it `NON_COMPLIANT` (e.g., because public read access is enabled), it automatically triggers the SSM Automation document, which executes the API calls necessary to remove the public access block, instantly remediating the issue without human intervention.

12. **What is the AWS Personal Health Dashboard and how does it differ from the Service Health Dashboard?**
    The Service Health Dashboard shows the general status of all AWS services across all regions (e.g., "S3 in us-east-1 is experiencing elevated error rates"). The Personal Health Dashboard provides alerts and remediation guidance specifically tailored to *your* AWS environment (e.g., "An underlying hardware failure requires you to stop and start your specific EC2 instance `i-abc123`").

13. **How do Cost Allocation Tags work? Why must you enable them in the billing console?**
    Cost Allocation Tags are standard resource tags (e.g., `Department: Marketing`) that you use to organize your AWS bill. By default, AWS does not include tags in billing reports to save processing overhead. You must explicitly activate specific tag keys in the Billing Console. Once active, Cost Explorer will categorize your spend by those tags, allowing you to chargeback costs to specific teams.

14. **What is AWS Compute Optimizer and what does it analyze to make recommendations?**
    Compute Optimizer uses machine learning to analyze the historical utilization metrics (CPU, memory, disk I/O, network) of your EC2 instances, EBS volumes, and Lambda functions over a period of time (up to 32 days). It then recommends optimal AWS resource configurations (e.g., changing an over-provisioned `m5.xlarge` to a `t3.large`) to reduce costs or improve performance.

15. **Design a comprehensive monitoring strategy for a Lambda-based API: what metrics, logs, traces, and alarms would you set up?**
    *   **Traces:** Enable X-Ray active tracing on API Gateway and Lambda to map latency across downstream DBs. Add custom annotations for `tenant_id`.
    *   **Logs:** Ensure Lambda logs to CloudWatch. Use JSON formatting for logs to enable easy querying in Logs Insights.
    *   **Metrics & Alarms:** Create alarms on default metrics: API Gateway `5XXError`, Lambda `Errors`, and Lambda `Duration` (alarm if approaching the 15-min timeout).
    *   **Cost:** Set an AWS Budget alarm for the account.
    *   **Dashboards:** Create a CloudWatch Dashboard visualizing P99 latency and error rates side-by-side.
