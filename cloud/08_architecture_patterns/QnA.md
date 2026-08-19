# QnA: Architecture Patterns and Well-Architected Framework

1. **What are the 6 pillars of the AWS Well-Architected Framework? Briefly describe each.**
   *   **Operational Excellence:** Running/monitoring systems and improving processes (IaC, CI/CD).
   *   **Security:** Protecting data and systems (IAM, encryption, WAF).
   *   **Reliability:** Recovering from failures and mitigating disruptions (Multi-AZ, backups).
   *   **Performance Efficiency:** Using compute resources effectively (Right-sizing, caching).
   *   **Cost Optimization:** Delivering business value at the lowest price point (Spot instances, Lifecycle rules).
   *   **Sustainability:** Minimizing the environmental impact of cloud workloads (Graviton processors, Serverless).

2. **What is the difference between RTO and RPO? What are the four DR strategies in order of cost?**
   *   **RTO (Recovery Time Objective):** The maximum acceptable downtime (how long it takes to restore service).
   *   **RPO (Recovery Point Objective):** The maximum acceptable data loss (measured in time, e.g., backing up every hour means 1 hr RPO).
   *   **DR Strategies (Cheapest to Most Expensive):** 1. Backup & Restore, 2. Pilot Light, 3. Warm Standby, 4. Multi-Site Active/Active.

3. **What is the difference between AWS GuardDuty, Inspector, and Macie? What does each protect against?**
   *   **GuardDuty:** Network and account threat detection. Uses ML to analyze CloudTrail and VPC Flow Logs for anomalous behavior (e.g., crypto-mining, unusual logins).
   *   **Inspector:** Host and container vulnerability scanning. Scans EC2 and ECR images for known CVEs (Common Vulnerabilities and Exposures) and network accessibility.
   *   **Macie:** Data security. Uses NLP and ML to scan S3 buckets and identify/classify sensitive data like PII or credit card numbers.

4. **What is the difference between AWS Shield Standard and Advanced? When is Advanced worth the cost?**
   Shield Standard is free and automatically protects all AWS customers against common Layer 3/4 DDoS attacks. Shield Advanced costs $3,000/month. It provides tailored Layer 3/4/7 protection, 24/7 access to the DDoS Response Team (DRT), and crucial "cost protection," which refunds you if a DDoS attack causes your Auto Scaling Group to spin up thousands of instances. It is worth it for high-profile enterprise targets.

5. **What is WAF and where can it be deployed? Give examples of rules you would configure.**
   AWS Web Application Firewall (WAF) operates at Layer 7 to protect against common web exploits. It can be deployed on CloudFront, Application Load Balancers (ALB), or API Gateway. Common rules include blocking IP addresses (IP Sets), rate limiting to prevent brute force attacks, and managed rules to block SQL injection and Cross-Site Scripting (XSS).

6. **What is the difference between CloudFront and Global Accelerator? When would you choose each?**
   *   **CloudFront** is a CDN. It caches HTTP/HTTPS content at the edge. Use it to deliver static assets (images, videos, HTML) or dynamic HTTP API responses.
   *   **Global Accelerator** does not cache. It provides static Anycast IPs and routes TCP/UDP traffic over the AWS private network backbone to the closest healthy endpoint. Use it for non-HTTP traffic (gaming, IoT, VoIP) or applications requiring static IPs that bypass internet congestion.

7. **Design a three-tier web application architecture on AWS that is highly available across two AZs.**
   1. **Presentation Tier:** An Application Load Balancer in public subnets across AZ 1 and AZ 2.
   2. **Logic Tier:** An Auto Scaling Group of EC2 instances running in private subnets across AZ 1 and AZ 2, registered to the ALB.
   3. **Data Tier:** Amazon RDS deployed in a Multi-AZ configuration (Primary in AZ 1, synchronous Standby in AZ 2) situated in isolated database subnets. 
   *(See CHEATSHEET for ASCII diagram).*

8. **What is the difference between Aurora Global Database and DynamoDB Global Tables? When would you use each for a multi-region app?**
   *   **Aurora Global Database:** Relational (SQL). Uses dedicated infrastructure for sub-second cross-region replication. It is typically Active-Passive for writes (write to primary region, read anywhere).
   *   **DynamoDB Global Tables:** NoSQL. Fully managed, Active-Active replication. You can write to *any* region and it resolves conflicts via "last writer wins."
   Choose Aurora for complex transactions/joins; choose DynamoDB for massive scale, simple key-value lookups, and true active-active writing.

9. **What is the Saga pattern? Compare choreography-based and orchestration-based sagas.**
   The Saga pattern manages distributed transactions across microservices.
   *   **Choreography:** Decentralized. Service A completes work, emits an event (EventBridge), Service B listens and acts. Good for simple flows, but hard to monitor complex ones.
   *   **Orchestration:** Centralized. A controller (AWS Step Functions) explicitly commands Service A, then Service B, and handles rollbacks if a step fails. Best for complex, mission-critical workflows.

10. **What is Cognito User Pool vs Identity Pool?**
    *   **User Pools:** Provide a user directory, sign-up/sign-in pages, and handle password resets. They authenticate users and return JWT tokens.
    *   **Identity Pools (Federated Identities):** Take a token (from a User Pool, Google, or Facebook) and exchange it for temporary AWS IAM credentials, allowing the user's application to directly access AWS resources like S3 or DynamoDB.

11. **Explain data transfer costs in AWS and how you would design an architecture to minimize them.**
    Inbound data transfer is free. Data transfer *out* to the internet is expensive. Data transfer across regions or across AZs incurs charges. To minimize costs:
    *   Use CloudFront to cache data at the edge (CloudFront egress is often cheaper than S3/EC2 egress).
    *   Keep chatty microservices in the same Availability Zone.
    *   Use VPC Gateway Endpoints to access S3/DynamoDB for free without routing over the internet.

12. **What is AWS Graviton and why should you consider it for your compute workloads?**
    Graviton is a family of custom AWS processors built on ARM architecture (unlike traditional x86 Intel/AMD processors). You should consider them because they provide up to 40% better price-performance for modern workloads (microservices, databases) and consume up to 60% less energy, aligning with the Cost Optimization and Sustainability pillars.

13. **What is the difference between CloudFormation and CDK? Which would you use for a new project?**
    CloudFormation uses declarative JSON or YAML templates to define infrastructure. AWS Cloud Development Kit (CDK) allows developers to write infrastructure using familiar imperative programming languages (TypeScript, Python, Java). CDK code is synthesized into CloudFormation templates before deployment. For a new project, CDK is highly recommended as it allows for loops, conditionals, object-oriented constructs, and easier testing.

14. **Design a serverless image upload and processing pipeline on AWS. Walk through each component.**
    1. A mobile client requests an **S3 Pre-signed URL** via **API Gateway -> Lambda**.
    2. Client uploads the image directly to **S3 (Input Bucket)**.
    3. An **S3 Event Notification** triggers a **Lambda function**.
    4. Lambda downloads the image, resizes it, and saves it to an **S3 (Output Bucket)**.
    5. Lambda writes the image metadata to **DynamoDB**.
    6. If the Lambda fails, it drops the event into an **SQS DLQ** for debugging.

15. **Your Lambda-based API is experiencing high latency during peak times. Walk through how you would diagnose and fix the issue.**
    1. **Diagnose:** I would look at the CloudWatch `Duration` and `ConcurrentExecutions` metrics. I would check **AWS X-Ray** traces to see if the latency is caused by the Lambda cold starts, the Lambda execution itself, or a downstream database (e.g., DynamoDB throttling).
    2. **Fix (Cold Starts):** If cold starts are the issue during traffic spikes, I would implement **Provisioned Concurrency** (or SnapStart for Java).
    3. **Fix (Downstream):** If DynamoDB is the bottleneck, I would switch it to On-Demand capacity or increase provisioned WCU/RCU, or add DAX for read caching. If the Lambda is CPU bound, I would increase its memory allocation (which proportionally increases CPU).
