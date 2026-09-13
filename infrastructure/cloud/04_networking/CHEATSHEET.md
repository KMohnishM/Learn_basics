# CHEATSHEET: Networking and Content Delivery

## Security Groups vs. NACLs

| Feature | Security Group (SG) | Network ACL (NACL) |
|---|---|---|
| **Level** | Instance level (ENI) | Subnet level |
| **State** | **Stateful:** Return traffic allowed | **Stateless:** Return traffic needs rule |
| **Rules** | Allow rules only | Allow AND Deny rules |
| **Evaluation**| All rules evaluated | Evaluated in numerical order (lowest first) |
| **Default** | Implicit Deny all inbound | Default VPC NACL allows all |

## VPC Components Quick Reference

*   **VPC:** Logically isolated network. (e.g., 10.0.0.0/16)
*   **Subnet:** Segment of VPC tied to a single AZ.
*   **Route Table:** Rules defining where traffic goes.
*   **Internet Gateway (IGW):** Gives public subnets internet access.
*   **NAT Gateway:** Gives private subnets outbound-only internet access. (Needs EIP, lives in Public Subnet).
*   **VPC Peering:** 1-to-1 connection between VPCs. Non-transitive.
*   **Transit Gateway:** Hub-and-spoke connection for thousands of VPCs/VPNs.
*   **VPC Endpoint (Gateway):** Free route to S3 / DynamoDB.
*   **VPC Endpoint (Interface/PrivateLink):** ENI with private IP for other AWS services (costs money).

## Load Balancers

| Load Balancer | Layer | Protocols | Target Use Case | Key Features |
|---|---|---|---|---|
| **ALB (Application)** | Layer 7 | HTTP, HTTPS, gRPC | Web apps, microservices | Path/Host routing, Sticky Sessions |
| **NLB (Network)** | Layer 4 | TCP, UDP, TLS | High perf, gaming, IoT | Sub-ms latency, Static IPs |
| **GLB (Gateway)** | Layer 3 | IP (GENEVE) | Security appliances | Transparent proxy for firewalls |

## Route 53 Routing Policies

| Policy | Behavior | Best For |
|---|---|---|
| **Simple** | Returns 1 or more IPs. | Standard single-server setups |
| **Weighted** | Traffic split by % | Blue/Green deployments, A/B testing |
| **Latency** | Routes to region with lowest ping | Global apps needing speed |
| **Geolocation** | Routes based on user's country/state | Content localization, Compliance |
| **Failover** | Primary/Secondary based on Health Check | Active-Passive Disaster Recovery |
| **Geoproximity** | Based on distance + adjustable "bias" | Shifting traffic between regions |

## Edge Compute

| Feature | CloudFront Functions | Lambda@Edge |
|---|---|---|
| **Language** | JavaScript only | Node.js, Python |
| **Duration** | < 1 millisecond | Seconds |
| **Network Access** | None | Yes (Can call external APIs) |
| **Trigger Points** | Viewer Request / Response | Viewer & Origin Request / Response |
| **Use Case** | Header manipulation, URL rewrites | Auth verification, database lookups |
