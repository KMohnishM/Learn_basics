# AWS/Cloud Engineering Curriculum

This curriculum provides a comprehensive, deep-dive training path for mastering AWS cloud computing. While the topics cover and exceed the requirements for the AWS Certified Solutions Architect - Associate (SAA-C03) exam, the primary focus of this material is **interview readiness and production-grade engineering**. You will learn not just what services do, but how they work under the hood, how they break, and how to architect systems like a Principal Engineer.

All modules highlight GCP equivalents to aid in multi-cloud discussions.

## Module Map

| Module | Title | Topics Covered | Difficulty |
|---|---|---|---|
| 01 | Fundamentals | Cloud models, Global Infra, Shared Responsibility, Pricing | Beginner |
| 02 | Compute | EC2, AMIs, ASG, Lambda, ECS, EKS, Fargate | Intermediate |
| 03 | Storage | S3 (Standard, Glacier, IA), EBS, EFS, RDS, DynamoDB | Intermediate |
| 04 | Networking | VPC, Subnets, IGW, NAT, Security Groups, ALB, NLB, Route 53 | Advanced |
| 05 | IAM & Security | IAM Roles/Policies, KMS, CloudTrail, Secrets Manager, SSO | Advanced |
| 06 | Messaging & Streaming | SQS, SNS, EventBridge, Kinesis, Step Functions | Intermediate |
| 07 | Observability | CloudWatch, X-Ray, Config, Health, Cost Explorer | Intermediate |
| 08 | Architecture Patterns | Well-Architected Framework, DR, Web Apps, Serverless APIs | Advanced |

## Suggested Study Path

We recommend approaching the material in numerical order, as subsequent modules build heavily on earlier concepts (e.g., you must understand VPCs in Module 04 before fully grasping ECS networking in Module 02, though we introduce compute first to build mental models).

*   **Week 1:** Module 01 & 02 (Focus heavily on EC2 and Lambda fundamentals)
*   **Week 2:** Module 03 (Focus on S3 and DynamoDB data modeling)
*   **Week 3:** Module 04 (Spend extra time here; networking is the #1 failing point in interviews)
*   **Week 4:** Module 05 & 06 (IAM policies and Event-driven architectures)
*   **Week 5:** Module 07 & 08 (Putting it all together, Well-Architected Framework)

## How to Practice

Theoretical knowledge is insufficient. You must build.

1.  **AWS Free Tier:** Create a new AWS account to utilize the 12-month Free Tier. Always set a billing alarm via AWS Budgets immediately upon creation.
2.  **AWS CLI:** Install the AWS CLI v2. Authenticate using IAM Identity Center (SSO) rather than long-lived access keys when possible. Practice performing all console actions via the CLI.
3.  **LocalStack:** Use LocalStack (`pip install localstack`) via Docker for local, offline AWS API emulation. This is highly recommended for testing S3, SQS, SNS, and DynamoDB code without incurring costs or deploying to the cloud.
4.  **Infrastructure as Code:** While this curriculum provides CLI snippets, you should attempt to recreate the architectures using Terraform, AWS CDK, or CloudFormation.

## Exam Note

This content aligns with the AWS SAA-C03 domains (Design Secure Architectures, Design Resilient Architectures, Design High-Performing Architectures, Design Cost-Optimized Architectures). However, we prioritize practical, interview-focused deep dives over rote memorization of service limits. Expect to see architectural trade-offs, failure scenarios, and multi-cloud comparisons throughout.
