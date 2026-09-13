# CHEATSHEET: Architecture Patterns & Well-Architected

## The 6 Pillars of Well-Architected

| Pillar | Key Services / Concepts |
|---|---|
| **Operational Excellence** | CloudFormation, CDK, CI/CD, Runbooks |
| **Security** | IAM, WAF, Shield, GuardDuty, KMS, Macie |
| **Reliability** | Multi-AZ, Auto Scaling, Route 53, Backup strategies |
| **Performance Efficiency** | Serverless, ElastiCache, Global Accelerator, DAX |
| **Cost Optimization** | Savings Plans, Spot, S3 Intelligent-Tiering, Cost Explorer|
| **Sustainability** | Graviton processors, Serverless, minimizing idle time |

## Disaster Recovery Strategies

| Strategy | Cost | RTO/RPO | Description |
|---|---|---|---|
| **Backup & Restore** | $ | Hours | Data backed up. Provision infra on failure. |
| **Pilot Light** | $$ | Tens of mins | Core DB running. Start app servers on failure. |
| **Warm Standby** | $$$ | Minutes | Scaled-down production running. Scale up on failure. |
| **Multi-Site Active**| $$$$ | Seconds / Near zero | Full production running in multiple regions simultaneously. |

## Security Services Quick Reference

*   **WAF:** Blocks web exploits (SQLi, XSS) at Layer 7.
*   **Shield:** Blocks DDoS attacks at Layer 3/4.
*   **GuardDuty:** Threat detection (ML analysis of logs).
*   **Inspector:** Vulnerability scanning (EC2/ECR CVEs).
*   **Macie:** PII/Data classification in S3.
*   **Cognito:** Authentication/Authorization for your apps.

## Architecture: Three-Tier Web App

```text
[Internet] --> [Route 53] --> [CloudFront]
                                  |
               +-----------------------------------+
               | VPC                               |
               |                                   |
               |  [Public Subnet]                  |
               |       |                           |
               |  [ALB (Application Load Balancer)]|
               |       |                           |
               |  [Private Subnet - App Tier]      |
               |       |                           |
               |  [ASG: EC2 Web Servers]           |
               |       |                           |
               |  [Private Subnet - DB Tier]       |
               |       |                           |
               |  [Amazon RDS Multi-AZ]            |
               |       |                           |
               |  [ElastiCache (Redis)]            |
               +-----------------------------------+
```

## Architecture: Serverless API

```text
[Client] --> [API Gateway] --> [Lambda] --> [DynamoDB]
                                  |
                                  +-------> [S3] (Storage)
                                  |
                                  +-------> [SQS] (Async background tasks)
```

## System Design Cheat Codes
*   Need global static IPs? -> **Global Accelerator**
*   Need extreme block storage performance? -> **EBS io2 Block Express**
*   Need shared network storage for Linux? -> **EFS**
*   Need to decouple microservices? -> **SQS / SNS / EventBridge**
*   Need in-memory caching? -> **ElastiCache (Redis) or DAX (DynamoDB)**
*   Need an audit trail of API calls? -> **CloudTrail**
