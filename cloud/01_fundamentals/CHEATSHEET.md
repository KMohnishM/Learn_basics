# CHEATSHEET: AWS Fundamentals

## Service Models Comparison

| Model | You Manage | AWS Manages | AWS Example | Use Case |
|---|---|---|---|---|
| **IaaS** | App, Data, OS, Middleware | Hardware, Hypervisor, Network | EC2 | Lift & shift, strict OS control |
| **PaaS** | App, Data | OS, Hardware, Network, Runtime | Elastic Beanstalk, RDS | Standard web apps, less ops |
| **SaaS** | Nothing (just config) | Everything | Amazon WorkMail | Email, CRM, end-user tools |
| **FaaS** | Code | Everything else | Lambda | Event-driven, microservices |

## The Shared Responsibility Model

```text
+-------------------------------------------------------------------+
|                     CUSTOMER RESPONSIBILITY                       |
|                     ("Security IN the Cloud")                     |
|                                                                   |
| [Customer Data]  [Platform/App/IAM]  [OS/Firewall Config (EC2)]   |
| [Client-side Encryption]  [Server-side Encryption] [Network Traf.]|
+-------------------------------------------------------------------+
|                                                                   |
+-------------------------------------------------------------------+
|                        AWS RESPONSIBILITY                         |
|                     ("Security OF the Cloud")                     |
|                                                                   |
| [Compute (Servers)] [Storage] [Database Engines] [Networking]     |
| [Regions]          [Availability Zones]          [Edge Locations] |
+-------------------------------------------------------------------+
```

## Pricing Models Quick Reference

| Model | Commitment | Discount | Key Attribute | Use Case |
|---|---|---|---|---|
| **On-Demand** | None | 0% | Pay by the second/hour | Unpredictable, spiky, new apps |
| **Reserved (RI)** | 1 or 3 years | Up to 72% | Tied to instance type/OS | Steady-state DBs, baseline traffic |
| **Savings Plan** | 1 or 3 years | Up to 72% | Dollar commit ($/hr), highly flexible | Modern compute (EC2, Fargate, Lambda) |
| **Spot** | None | Up to 90% | Can be interrupted (2 min warning) | Batch, CI/CD, stateless, fault-tolerant |
| **Dedicated** | Hardware level | Varies | Physical server isolation | Compliance, BYOL (Bring Your Own License) |

## Global Infrastructure

*   **Region:** Isolated physical area. Choose based on Compliance > Latency > Price.
*   **Availability Zone (AZ):** Discrete data center(s) within a region. Distinct power/network. **Architect for HA across multiple AZs.**
*   **Edge Location:** Cache for CloudFront (CDN) / Route 53.

## AWS vs GCP Equivalents

| AWS | GCP |
| :--- | :--- |
| Region | Region |
| Availability Zone | Zone |
| Amazon EC2 | Compute Engine |
| Amazon S3 | Cloud Storage |
| AWS Lambda | Cloud Functions |
| AWS IAM | Cloud IAM |
