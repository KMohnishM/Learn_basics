# CHEATSHEET: Observability and Management

## Observability Tool Quick Reference

| Tool | Core Question Answered | Data Type | Key Feature |
|---|---|---|---|
| **CloudWatch Metrics** | What is the system state? | Time-series numbers | Alarms, Auto Scaling |
| **CloudWatch Logs** | Why did it happen? | Text/JSON strings | Metric Filters, Insights |
| **AWS X-Ray** | Where is the bottleneck? | Distributed traces | Service Map, Annotations |
| **CloudTrail** | Who made the API call? | Audit logs | Governance, Security |
| **AWS Config** | What changed on this resource?| Configuration state | Timeline, Auto-Remediation |

## CloudWatch Hierarchy

*   **Namespace:** Container for metrics (e.g., `AWS/EC2`, `AWS/Lambda`).
*   **Metric:** The specific data point (e.g., `CPUUtilization`).
*   **Dimension:** Name/value pair to identify the metric source (e.g., `InstanceId = i-123`).
*   **Statistic:** How data is aggregated over the period (e.g., `Average`, `Sum`, `Maximum`, `p99`).

## X-Ray Concepts

| Concept | Description | Indexing |
|---|---|---|
| **Trace** | The entire request path. | N/A |
| **Segment** | Work done by one service. | N/A |
| **Subsegment** | Granular work (e.g., a DB query). | N/A |
| **Annotations**| Key-value pairs for filtering. | **Indexed** (Searchable) |
| **Metadata** | Key-value pairs for debug data. | Not Indexed |

## CloudTrail vs Config

| Feature | CloudTrail | AWS Config |
|---|---|---|
| **Focus** | API Actions (Who did it?) | Resource State (What does it look like?) |
| **Example** | `ec2:AuthorizeSecurityGroupIngress` | `SecurityGroup: port 22 is open` |
| **Best For** | Security Audits, Incident Response | Compliance, Configuration Drift |

## Cost Management Tools

| Tool | Purpose | Key Capability |
|---|---|---|
| **Cost Explorer** | Analyze historical spend | Visual graphs, forecasting |
| **AWS Budgets** | Proactive cost control | SNS alerts on *actual* or *forecasted* spend |
| **Compute Optimizer**| Right-sizing infrastructure | ML-based recommendations (e.g., shrink EC2) |
