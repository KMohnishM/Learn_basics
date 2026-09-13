# Module 8: Architecture Patterns and Well-Architected Framework

## AWS Well-Architected Framework

The Well-Architected Framework provides a consistent approach to evaluating cloud architectures. It is divided into six pillars. Understanding these is the key to passing System Design interviews.

### 1. Operational Excellence
*Focus: Running and monitoring systems to deliver business value, and continually improving processes.*
*   **Infrastructure as Code (IaC):** Never click through the console for production.
    *   **CloudFormation:** Declarative JSON/YAML. AWS native. Supports drift detection.
    *   **AWS CDK:** Imperative code (TypeScript, Python) that synthesizes into CloudFormation.
    *   **Terraform:** Cross-cloud, industry standard declarative tool.
*   **CI/CD (Continuous Integration / Continuous Deployment):**
    *   CodeCommit (Git), CodeBuild (Compile/Test), CodeDeploy (Deploy), CodePipeline (Orchestrator).
    *   **Deployment Strategies:**
        *   *In-place:* Overwrites existing app. Downtime occurs.
        *   *Blue/Green:* Spin up entirely new v2 infra (Green), switch traffic, kill v1 (Blue). Zero downtime.
        *   *Canary:* Shift 10% of traffic to v2, monitor, then shift the rest.
*   **Observability:** Implement comprehensive logging (CloudWatch), metrics, and tracing (X-Ray).

### 2. Security
*Focus: Protecting information and systems.*
*   **Defense in Depth:** Apply security at every layer.
    *   *Network:* VPC, Security Groups, NACLs, Private Subnets.
    *   *Compute:* IAM Roles, patch management (Systems Manager).
    *   *Application:* AWS WAF (Web Application Firewall) to block SQL injection and XSS.
    *   *Data:* KMS encryption at rest and in transit.
*   **Perimeter Protection:**
    *   **AWS Shield Standard:** Free, automatic DDoS protection for all AWS customers.
    *   **AWS Shield Advanced:** $3,000/month. Access to the DDoS Response Team (DRT), and cost protection (AWS refunds you if a DDoS attack scales up your infrastructure).
*   **Intelligent Threat Detection:**
    *   **Amazon GuardDuty:** Machine learning threat detection. Analyzes CloudTrail, VPC Flow Logs, and DNS logs continuously without performance impact.
    *   **Amazon Inspector:** Automated vulnerability management. Scans EC2 for OS CVEs and ECR/Lambda for software dependencies.
    *   **Amazon Macie:** Uses NLP/ML to discover and protect sensitive data (PII, credit cards) stored in S3.
    *   **AWS Security Hub:** Central dashboard that aggregates findings from GuardDuty, Inspector, Macie, and third-party tools.
*   **Identity:**
    *   **Amazon Cognito:** User authentication for web/mobile apps.
        *   *User Pools:* Sign-up/Sign-in directories (returns JWTs).
        *   *Identity Pools:* Grants temporary AWS credentials to users so they can directly access S3/DynamoDB.

### 3. Reliability
*Focus: Ensuring a workload performs its intended function correctly and consistently.*
*   **High Availability (HA):** Deploy across multiple Availability Zones (RDS Multi-AZ, ASG spanning AZs).
*   **Disaster Recovery (DR) Strategies (From cheapest to most expensive):**
    1.  **Backup & Restore:** Data is backed up (e.g., S3). In a disaster, you provision infrastructure and restore data. *High RPO, High RTO.*
    2.  **Pilot Light:** Core data is continually replicated (e.g., DB running). App servers are stopped or don't exist. In disaster, scale up app servers. *Low RPO, Medium RTO.*
    3.  **Warm Standby:** A scaled-down version of a fully functional environment is always running. In disaster, you just scale it up to handle full production load. *Low RPO, Low RTO.*
    4.  **Multi-Site Active/Active:** Full production load is handled across multiple regions simultaneously. (Uses Route 53, DynamoDB Global Tables). *Near zero RPO/RTO.*
*   **RTO vs RPO:**
    *   **RTO (Recovery Time Objective):** How much *time* can the system be down? (Downtime).
    *   **RPO (Recovery Point Objective):** How much *data* can we afford to lose? (Measured in time).

### 4. Performance Efficiency
*Focus: Using IT and computing resources efficiently.*
*   **Selection:** Choose the right resource (e.g., Compute Optimized vs Memory Optimized EC2, or moving to Serverless/Lambda).
*   **Global Distribution:** Use CloudFront (CDN) to cache data globally. Use Global Accelerator to route TCP/UDP traffic over the AWS backbone via static Anycast IPs.
*   **Caching:** Offload heavy lifting from databases using Amazon ElastiCache (Redis/Memcached) or DynamoDB DAX.

### 5. Cost Optimization
*Focus: Avoiding unnecessary costs.*
*   **Right-sizing:** Use Compute Optimizer to downgrade oversized instances.
*   **Purchasing Models:** Use Savings Plans and Reserved Instances for steady workloads; Spot instances for fault-tolerant workloads.
*   **Data Transfer Costs:**
    *   Inbound to AWS: Free.
    *   Within same AZ: Free.
    *   Cross-AZ: Costs money. (Architect to keep chatty microservices in the same AZ if possible).
    *   Cross-Region: Costs more money.
    *   Internet Egress: Costs the most. (Use CloudFront to reduce origin egress costs).
*   **Storage Lifecycle:** Move old S3 data to Glacier. Delete unattached EBS volumes and obsolete snapshots.

### 6. Sustainability
*Focus: Minimizing the environmental impacts of running cloud workloads.*
*   **Maximize Utilization:** Serverless is highly sustainable because no idle servers are running.
*   **Hardware:** Use AWS Graviton processors (ARM-based). They provide up to 40% better price-performance and use 60% less energy than comparable x86 processors.

---

## Common Architecture Patterns

### Pattern 1: Three-Tier Web Application (Highly Available)
A classic, non-serverless enterprise architecture.
```text
[ Internet ]
      ↓
[ Route 53 (DNS) ]
      ↓
[ CloudFront (CDN) ] ---> [ S3 Bucket (Static Assets: HTML/CSS/JS) ]
      ↓
[ Application Load Balancer (Public Subnets, AZ-A & AZ-B) ]
      ↓
[ Auto Scaling Group - EC2/ECS Web Tier (Private Subnets, AZ-A & AZ-B) ]
      ↓
[ Auto Scaling Group - EC2/ECS App Tier (Private Subnets, AZ-A & AZ-B) ]
      ↓
[ Amazon RDS Multi-AZ (Primary in AZ-A, Standby in AZ-B) ]
      ↓
[ ElastiCache Redis (Private Subnet) ]
```

### Pattern 2: Serverless Event-Driven API
Modern, scalable, zero-maintenance architecture.
```text
[ Client (Web/Mobile) ]
      ↓
[ Amazon API Gateway ]
      ↓
[ AWS Lambda (Compute logic) ]
      ↓
  +---+---+
  ↓       ↓
[DynamoDB] [SQS Queue]
          ↓
      [Lambda (Background processing)]
```

### Pattern 3: Multi-Region Active-Active
For maximum reliability and global performance.
```text
[ Route 53 (Latency-Based Routing) ]
      /                       \
[ ALB us-east-1 ]           [ ALB eu-central-1 ]
      |                       |
[ ECS Fargate ]             [ ECS Fargate ]
      |                       |
      +----[ DynamoDB Global Tables ]----+
          (Active-Active Replication)
```

## System Design Interview Framework (The 5 Steps)
1.  **Clarify Requirements:** Ask questions. Is this read-heavy or write-heavy? How many users? What is the acceptable latency?
2.  **Estimate Scale:** Back-of-the-envelope math. (Requests per second, storage needed).
3.  **High-Level Design:** Draw the core components (Client -> Load Balancer -> App -> DB).
4.  **Deep Dive:** Discuss specific AWS services and *why* you chose them (e.g., "I chose DynamoDB over RDS because we have a massive, unpredictable write load and don't need complex joins").
5.  **Address the "Ilities":** Reliability (Multi-AZ), Scalability (ASG/Serverless), Security (WAF/IAM), Cost.
