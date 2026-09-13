# Module 1: AWS Fundamentals and Cloud Concepts

## What is Cloud Computing?
Cloud computing is the on-demand delivery of IT resources (compute, storage, databases, networking) over the internet with pay-as-you-go pricing. Instead of buying, owning, and maintaining physical data centers and servers, you access technology services on an as-needed basis from a cloud provider like Amazon Web Services (AWS), Google Cloud Platform (GCP), or Microsoft Azure.

## Service Models Deep Dive

Understanding the abstraction level of cloud services is critical for architectural decisions.

### 1. IaaS (Infrastructure as a Service)
*   **What it is:** The lowest level of abstraction. You manage the operating system, middleware, runtime, data, and application. The cloud provider manages the physical hardware, virtualization (hypervisor), network, and storage.
*   **AWS Example:** Amazon EC2 (Elastic Compute Cloud).
*   **GCP Equivalent:** Google Compute Engine.
*   **When to use:** When you need full control over the OS, are migrating legacy applications that require specific OS configurations, or are running commercial off-the-shelf (COTS) software with strict requirements.

### 2. PaaS (Platform as a Service)
*   **What it is:** Removes the need to manage the underlying infrastructure (usually hardware and operating systems) and allows you to focus on the deployment and management of your applications.
*   **AWS Example:** AWS Elastic Beanstalk.
*   **GCP Equivalent:** Google App Engine.
*   **Other Examples:** Heroku.
*   **When to use:** When you want rapid deployment of web applications without the operational overhead of managing servers, patching OS, or configuring load balancers manually.

### 3. SaaS (Software as a Service)
*   **What it is:** A complete product that is run and managed by the service provider. You only manage your data and access.
*   **Examples:** Gmail, Salesforce, Dropbox.
*   **When to use:** For end-user applications where custom development provides no competitive advantage.

### 4. FaaS (Function as a Service) / Serverless
*   **What it is:** You write and upload code. The provider handles everything else: provisioning servers, scaling, patching, and high availability. You are billed purely on execution time (milliseconds).
*   **AWS Example:** AWS Lambda.
*   **GCP Equivalent:** Google Cloud Functions.
*   **When to use:** Event-driven architectures, microservices, sporadic workloads, or glue code connecting other services.

### Decision Matrix
*   Need absolute control? -> **IaaS**
*   Standard web app, low ops? -> **PaaS**
*   Event-driven, sporadic, zero ops? -> **FaaS**
*   Buying a solution instead of building? -> **SaaS**

## Deployment Models
*   **Public Cloud:** Services delivered across the public internet. Cost-effective, elastic, zero maintenance. (e.g., AWS, GCP).
*   **Private Cloud:** Cloud infrastructure operated solely for a single organization. High security, compliance, but high CapEx.
*   **Hybrid Cloud:** Connecting on-premises infrastructure to the public cloud (e.g., using AWS Direct Connect). Allows leveraging cloud elasticity while keeping sensitive data on-prem.
*   **Multi-Cloud:** Using multiple public cloud providers (e.g., AWS for compute, GCP for BigQuery). Avoids vendor lock-in but significantly increases complexity and operational overhead.

## AWS Global Infrastructure

AWS operates a massive, highly resilient global network.

### Regions
*   **Definition:** Geographically isolated areas containing multiple data centers. There are currently 32+ regions globally (e.g., `us-east-1` N. Virginia, `eu-central-1` Frankfurt).
*   **Choosing a Region:**
    1.  **Compliance:** Data sovereignty laws (e.g., GDPR requires data to stay in Europe).
    2.  **Latency:** Place infrastructure close to your user base.
    3.  **Service Availability:** Not all services are available in all regions on day one.
    4.  **Pricing:** Costs vary by region (e.g., `sa-east-1` is usually more expensive than `us-east-1`).

### Availability Zones (AZs)
*   **Definition:** Each region has 2-6 AZs. An AZ is one or more discrete data centers with redundant power, networking, and connectivity.
*   **Networking:** AZs are connected via high-bandwidth, ultra-low-latency private fiber.
*   **Design Principle:** Always architect for AZ failure. Deploy critical infrastructure across at least two AZs (Multi-AZ).

### Edge Locations / Points of Presence (PoPs)
*   **Definition:** 400+ globally distributed locations primarily used to cache content closer to end users.
*   **Services:** Used by Amazon CloudFront (CDN) and Amazon Route 53 (DNS).

### Local Zones and Wavelength
*   **Local Zones:** Bring AWS compute, storage, and database services closer to large population, industry, and IT centers where no AWS Region exists. Used for single-digit millisecond latency.
*   **Wavelength Zones:** AWS infrastructure deployed within telecommunications providers' 5G networks. Ultra-low latency for mobile and connected devices.

## The Shared Responsibility Model

Security and compliance are a shared responsibility between AWS and the customer. This differentiation is critical.

*   **AWS Responsibility ("Security OF the Cloud"):** AWS protects the infrastructure that runs all services. This includes physical security of data centers, hardware, networking infrastructure, hypervisors, and the OS patching of fully managed services (like RDS or DynamoDB).
*   **Customer Responsibility ("Security IN the Cloud"):** Customer responsibility varies by service model. For IaaS (EC2), you are responsible for guest OS patching, application security, network configuration (Security Groups/NACLs), IAM (Identity and Access Management), and data encryption (at rest and in transit).

### How Responsibility Shifts
*   **EC2 (IaaS):** You manage OS, firewall, data, apps.
*   **RDS (PaaS):** AWS manages OS and DB engine patching. You manage data, schema, and access.
*   **S3/DynamoDB (SaaS/Managed):** AWS manages everything underlying. You manage data, permissions, and encryption config.

## AWS Pricing Models

Understanding pricing is a core architectural skill.

### 1. On-Demand
*   Pay for compute capacity by the second/hour with no long-term commitments.
*   Highest per-unit cost.
*   Use cases: Spiky, unpredictable workloads, testing, new apps.

### 2. Reserved Instances (RIs)
*   Commitment of 1 or 3 years for up to 72% savings.
*   **Standard RI:** Highest discount, cannot change instance family.
*   **Convertible RI:** Lower discount, allows changing instance family/OS.
*   **Scheduled RI:** Reserve capacity for specific time windows (e.g., every Thursday 2PM-6PM).
*   Use cases: Steady-state, predictable workloads (databases, core web servers).

### 3. Spot Instances
*   Bidding on spare AWS computing capacity for up to 90% discount.
*   **Risk:** AWS can reclaim the instance with a 2-minute warning if capacity is needed elsewhere.
*   Use cases: Fault-tolerant, flexible, stateless workloads (batch processing, big data analytics, CI/CD runners, rendering).

### 4. Savings Plans
*   Commit to a specific dollar amount per hour (e.g., $10/hour) for 1 or 3 years.
*   **Compute Savings Plans:** Most flexible. Applies across EC2 instance families, sizes, regions, Fargate, and Lambda.
*   **EC2 Instance Savings Plans:** Less flexible (tied to instance family in a region), higher discount.

### 5. Dedicated Hosts vs. Dedicated Instances
*   **Dedicated Instances:** Run on hardware dedicated to a single customer.
*   **Dedicated Hosts:** Gives you physical server visibility. Required for Bring Your Own License (BYOL) scenarios (e.g., strict Windows Server / SQL Server licensing) or extreme compliance needs.

### AWS Free Tier
*   **Always Free:** 1M Lambda requests/mo, 25GB DynamoDB, etc.
*   **12-Month Free:** 750 hours EC2 t2.micro, 5GB S3, 750 hours RDS.
*   **Trials:** Short-term trials for specific services.

## AWS Support Plans
1.  **Basic:** Free. Account/billing support, Service Health Dashboard.
2.  **Developer:** Email access to tech support. Good for testing/experimentation.
3.  **Business:** 24x7 phone/email/chat access. 1hr response time for production system down.
4.  **Enterprise:** 15-minute response for business-critical down. Includes a Technical Account Manager (TAM).

## AWS Well-Architected Framework (Overview)
A set of best practices for designing and operating reliable, secure, efficient, and cost-effective systems. (Deep dive in Module 08).
1.  **Operational Excellence:** Run and monitor systems, continually improve processes.
2.  **Security:** Protect information and systems (confidentiality, integrity, availability).
3.  **Reliability:** Ensure a workload performs its intended function correctly and consistently.
4.  **Performance Efficiency:** Use compute resources efficiently to meet system requirements.
5.  **Cost Optimization:** Avoid unnecessary costs.
6.  **Sustainability:** Minimize environmental impacts of running cloud workloads.

## GCP Equivalents Quick Reference

| Concept / AWS Service | GCP Equivalent |
| :--- | :--- |
| Region | Region |
| Availability Zone (AZ) | Zone |
| Amazon EC2 | Compute Engine |
| Amazon S3 | Cloud Storage |
| AWS Lambda | Cloud Functions |
| AWS IAM | Cloud IAM |
