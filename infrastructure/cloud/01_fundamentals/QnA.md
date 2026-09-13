# QnA: AWS Fundamentals

1. **What is the difference between IaaS, PaaS, and SaaS? Give one AWS service for each.**
   IaaS provides the raw building blocks (compute, storage, network) where you manage everything from the OS up. PaaS abstracts the underlying infrastructure, allowing you to focus purely on application code and deployment. SaaS provides a complete, managed application where you only consume the service and manage your data.
   *   **IaaS:** Amazon EC2
   *   **PaaS:** AWS Elastic Beanstalk
   *   **SaaS:** Amazon WorkMail (or conceptually, a 3rd party like Salesforce hosted on AWS)

2. **Explain the Shared Responsibility Model. Who patches the OS on an EC2 instance? Who patches RDS?**
   The Shared Responsibility Model states that AWS is responsible for the "Security OF the Cloud" (physical hardware, networking, hypervisor) while the customer is responsible for "Security IN the Cloud" (data, IAM, app security). For an EC2 instance (IaaS), the customer is responsible for patching the guest operating system. For RDS (PaaS), AWS manages the underlying EC2 instance and is responsible for patching the host OS and the database engine.

3. **What is the difference between an AWS Region and an Availability Zone?**
   An AWS Region is a geographical area (e.g., us-east-1 in Northern Virginia) that consists of two or more Availability Zones. An Availability Zone (AZ) is one or more discrete data centers within a region, equipped with independent power, cooling, and networking. AZs provide fault tolerance within a region.

4. **Your company requires all data to remain in India for regulatory reasons. How does AWS address this?**
   AWS allows customers to explicitly choose the Region where their data and infrastructure reside. By deploying resources exclusively in the `ap-south-1` (Mumbai) or `ap-south-2` (Hyderabad) regions, you ensure data residency. AWS does not move customer data outside the selected region without explicit customer action.

5. **When would you choose Spot Instances over On-Demand? What is the risk?**
   Spot Instances are ideal for fault-tolerant, flexible, and stateless workloads (such as batch processing, big data analysis, or CI/CD pipelines) because they offer up to a 90% discount compared to On-Demand pricing. The primary risk is that AWS can interrupt and reclaim the instance with only a 2-minute warning when capacity is needed elsewhere.

6. **What is the difference between Reserved Instances and Savings Plans? Which is more flexible?**
   Both provide significant discounts for a 1 or 3-year commitment. Reserved Instances (RIs) are typically tied to a specific instance type and operating system. Savings Plans are a newer, much more flexible model where you commit to a specific dollar spend per hour (e.g., $5/hour). Compute Savings Plans apply automatically across EC2 instance families, regions, AWS Fargate, and Lambda, making them the superior choice for flexibility.

7. **What are Edge Locations used for? How do they differ from AZs?**
   Edge Locations are endpoints for AWS content delivery services, specifically Amazon CloudFront and Route 53. There are hundreds of Edge Locations globally, situated close to population centers to cache static content and reduce latency for end-users. They are not designed for running general-purpose compute workloads like EC2, which must run in AZs.

8. **Your application needs to survive an entire AZ going down. What architecture decisions does that require?**
   You must implement a Multi-AZ architecture. This involves deploying your compute instances (e.g., EC2 via Auto Scaling Groups) across at least two different AZs. You must place an Application Load Balancer in front of them to route traffic to healthy instances. Finally, your database layer must be replicated; for example, using Amazon RDS Multi-AZ, which maintains a synchronous standby replica in a different AZ.

9. **What is a Dedicated Host and when is it required?**
   A Dedicated Host is a physical EC2 server fully dedicated to your use. It provides visibility and control over the placement of instances on physical hardware. It is primarily required for compliance reasons or to bring your own server-bound software licenses (BYOL) like Windows Server or SQL Server, which tie licenses to physical sockets or cores.

10. **How does the Shared Responsibility Model change when you move from EC2 to RDS to DynamoDB?**
    As you move from IaaS (EC2) to PaaS (RDS) to fully managed Serverless (DynamoDB), AWS takes on more operational burden.
    *   **EC2:** You manage the OS, firewall, patching, database software, and data.
    *   **RDS:** AWS manages the hardware, OS, and DB patching. You manage the schema, queries, and network access (Security Groups).
    *   **DynamoDB:** AWS manages everything including scaling and hardware. You only manage IAM permissions, data encryption settings, and table design.

11. **What is the AWS Free Tier and what are its limitations?**
    The AWS Free Tier allows users to explore AWS services free of charge up to specified limits. It includes "Always Free" services (e.g., 1M Lambda requests/month), "12-Month Free" services (e.g., 750 hours/month of a t2.micro EC2 instance for the first year), and short-term trials. Limitations include strict usage caps; exceeding these caps will result in standard pay-as-you-go billing.

12. **Explain multi-cloud strategy: what are the benefits and the hidden costs?**
    A multi-cloud strategy involves using services from more than one public cloud provider (e.g., AWS and GCP).
    *   **Benefits:** Avoids vendor lock-in, allows selecting "best of breed" services (e.g., AWS compute, GCP BigQuery), and theoretically improves redundancy.
    *   **Hidden Costs:** Massive increase in operational complexity. Engineering teams must learn multiple platforms, IAM models, and deployment tools (Terraform is required). Networking egress costs between clouds are high, and security surfaces are doubled.

13. **What is the AWS Well-Architected Framework and why does it matter in interviews?**
    The Well-Architected Framework is a set of best practices across six pillars: Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, and Sustainability. It matters in interviews because it provides a structured methodology for evaluating architectures. Interviewers look for your ability to discuss trade-offs (e.g., Reliability vs. Cost) using this framework.

14. **How would you estimate the monthly cost of running a web application on AWS?**
    I would use the AWS Pricing Calculator. I need to define the exact architecture:
    *   Compute: Number, size, and uptime of EC2 instances or Lambda invocations.
    *   Storage: EBS volume sizes, S3 GBs stored and retrieved.
    *   Database: RDS instance size, Multi-AZ overhead, storage.
    *   Networking: Data Transfer Out (egress to the internet), which is often a hidden cost driver.
    I would then factor in potential discounts from Savings Plans if the workload is steady.

15. **What is the difference between a Local Zone and a Wavelength Zone?**
    Both bring AWS services closer to end-users for ultra-low latency. Local Zones place AWS compute, storage, and databases near large population or industry centers where a standard AWS Region doesn't exist. Wavelength Zones specifically embed AWS compute and storage services within telecommunications providers' 5G networks, providing sub-millisecond latency for mobile edge computing applications.
