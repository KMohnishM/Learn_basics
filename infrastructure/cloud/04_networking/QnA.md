# QnA: Networking and Content Delivery

1. **What is the difference between a Security Group and a NACL? Which is stateful?**
   *   **Security Groups (SGs)** operate at the instance level (ENI), are **stateful** (return traffic is automatically allowed), and only support "Allow" rules (everything else is implicitly denied).
   *   **Network ACLs (NACLs)** operate at the subnet level, are **stateless** (return traffic must be explicitly allowed via ephemeral ports), and support both "Allow" and "Deny" rules which are evaluated in numerical order.

2. **A private subnet EC2 instance needs to download updates from the internet. What do you need?**
   You need to deploy a **NAT Gateway** in a *public* subnet. Then, you must update the Route Table of the *private* subnet to point all outbound internet traffic (`0.0.0.0/0`) to the NAT Gateway. The NAT Gateway translates the private IP to its public Elastic IP, retrieves the update via the Internet Gateway, and returns the packets to the EC2 instance.

3. **What is the difference between VPC Peering and Transit Gateway? When would you choose each?**
   VPC Peering creates a one-to-one, non-transitive connection between two VPCs. It is simple and cost-effective for a small number of VPCs. Transit Gateway acts as a central hub for thousands of VPCs and on-premises networks, supporting transitive routing. Choose VPC Peering for 2-3 VPCs; choose Transit Gateway for enterprise architectures with many VPCs to avoid a complex "full mesh" peering topology.

4. **What is the difference between a Gateway VPC Endpoint (for S3) and an Interface VPC Endpoint? When would you use each?**
   *   **Gateway Endpoint:** Modifies the VPC Route Table to route traffic to S3 or DynamoDB directly over the AWS backbone. It is free. Use this exclusively for S3 and DynamoDB.
   *   **Interface Endpoint (PrivateLink):** Deploys an Elastic Network Interface (ENI) with a private IP address into your subnet. It costs an hourly fee. Use this to access all other AWS services (SNS, SQS, KMS, etc.) privately.

5. **What is the difference between ALB, NLB, and GLB? Give a use case for each.**
   *   **ALB (Application):** Layer 7 (HTTP/HTTPS). Reads request contents. *Use case:* A web application routing `/api` traffic to one set of instances and `/images` to another.
   *   **NLB (Network):** Layer 4 (TCP/UDP). Extreme throughput, static IPs. *Use case:* A multiplayer gaming backend, high-frequency trading platform, or passing traffic through a corporate firewall requiring static IPs.
   *   **GLB (Gateway):** Layer 3. *Use case:* Routing all ingress traffic through a cluster of third-party intrusion detection systems (IDS) before it reaches your application.

6. **Explain ALB path-based vs host-based routing. Give an example architecture.**
   *   **Path-based:** Routes traffic based on the URL path. E.g., `example.com/api/*` routes to an API Target Group (ECS containers), and `example.com/blog/*` routes to a WordPress Target Group (EC2).
   *   **Host-based:** Routes traffic based on the domain name in the HTTP host header. E.g., `api.example.com` routes to the API Target Group, and `app.example.com` routes to the Frontend Target Group, all sharing a single ALB.

7. **What are the Route 53 routing policies? Which would you use for blue-green deployment?**
   Routing policies include Simple, Weighted, Latency, Geolocation, Geoproximity, Failover, and Multi-Value. For a **blue-green deployment**, you would use **Weighted Routing**. You assign the existing "blue" environment a weight of 90, and the new "green" environment a weight of 10. As you gain confidence in the green environment, you gradually adjust the weights until green is 100%.

8. **What is the difference between a Route 53 Alias record and a CNAME? When must you use an Alias?**
   A CNAME maps a hostname to another hostname, but standard DNS rules forbid placing a CNAME at the root of a domain (the "zone apex", like `domain.com`). An Alias record is an AWS-specific extension that maps a hostname to an AWS resource (like an ALB or CloudFront distribution). You **must** use an Alias record if you want to point your root domain (`example.com`) directly to an ALB or S3 bucket. Also, Alias lookups are free.

9. **How does CloudFront Origin Access Control (OAC) work and why is it important?**
   OAC ensures that users cannot bypass CloudFront and access your S3 bucket origin directly. It works by restricting the S3 bucket policy to only allow `s3:GetObject` if the request originates from a specific CloudFront Distribution ARN. This is important to ensure users don't bypass CDN caching, WAF security rules, or run up exorbitant data transfer costs directly on S3.

10. **What is the difference between CloudFront Functions and Lambda@Edge?**
    *   **CloudFront Functions:** Written in JS, execute in sub-milliseconds, handle viewer requests/responses only, and cannot access the internet or VPCs. Use for simple cache-key normalization or header manipulation.
    *   **Lambda@Edge:** Written in Node/Python, execute in seconds, handle both viewer AND origin requests/responses, and can make network calls. Use for complex auth, database lookups, or heavy request transformation.

11. **You need to set up connectivity between your on-premises data center and AWS. Compare VPN vs Direct Connect.**
    *   **Site-to-Site VPN:** Routes encrypted traffic over the public internet. Fast to set up (minutes), cheaper, but bandwidth is capped at 1.25 Gbps per tunnel, and latency can fluctuate based on internet congestion.
    *   **Direct Connect (DX):** A physical, dedicated fiber connection bypassing the internet. Takes weeks to physically provision, expensive, but provides ultra-low, consistent latency and high throughput (up to 100 Gbps).

12. **What is cross-zone load balancing and how does ALB behave differently from NLB?**
    Cross-zone load balancing distributes traffic evenly across all targets in all enabled AZs, rather than splitting traffic evenly per AZ (which causes imbalance if AZ-A has 2 targets and AZ-B has 10).
    *   **ALB:** Enabled by default and cannot be disabled at the ALB level (it is free).
    *   **NLB:** Disabled by default. If you enable it, you are charged standard inter-AZ data transfer fees for traffic crossing AZ boundaries.

13. **Explain Route 53 Geolocation vs Geoproximity routing. When would each be used?**
    *   **Geolocation:** Routes based exactly on the user's location. (e.g., "Users in Germany must only hit servers in Frankfurt for GDPR compliance").
    *   **Geoproximity:** Routes users to the physically closest AWS region. It allows you to define a "bias" to expand or shrink the catchment area of a region. Use this to shift traffic away from an overloaded region to an adjacent one.

14. **What happens to TCP connections when a target is deregistered from an ALB? What is connection draining?**
    When a target is deregistered (or fails health checks), the ALB stops sending *new* requests to it. However, **Connection Draining (Deregistration Delay)** allows existing, established connections to complete their work before the load balancer forcibly closes the connection (default 300 seconds). This prevents abrupt user errors during scale-in events.

15. **Your company has 5 VPCs that all need to communicate with each other and with on-premises. Design the connectivity.**
    Using VPC Peering would require a full mesh of 10 separate peering connections, plus 5 VPNs to on-prem, which is unmanageable. Instead, deploy an **AWS Transit Gateway**. Attach all 5 VPCs to the Transit Gateway, and establish a single Site-to-Site VPN (or Direct Connect) from on-premises to the Transit Gateway. This creates a scalable hub-and-spoke architecture.
