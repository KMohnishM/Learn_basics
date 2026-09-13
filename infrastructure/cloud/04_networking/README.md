# Module 4: Networking and Content Delivery

## VPC (Virtual Private Cloud)
A VPC is a logically isolated virtual network where you launch your AWS resources. Mastering VPC concepts is critical for cloud architecture.

### VPC Fundamentals
*   **CIDR Block:** Defines the IP range of the VPC. (e.g., `10.0.0.0/16` provides 65,536 IPs). A VPC is tied to a specific AWS Region and spans all Availability Zones in that region.
*   **Subnets:** Smaller networks created inside the VPC CIDR block (e.g., `10.0.1.0/24`). 
    *   A subnet is tied to a **single** Availability Zone.
    *   AWS reserves 5 IP addresses in every subnet (Network, VPC Router, DNS, Future use, Broadcast).
    *   **Public Subnet:** Has a route to an Internet Gateway.
    *   **Private Subnet:** Does NOT have a direct route to an Internet Gateway.

### Routing and Internet Access
*   **Route Tables:** Determine where network traffic is directed. Every VPC has a main route table, but you should create custom route tables for your subnets. The `local` route (allowing communication within the VPC) cannot be deleted.
*   **Internet Gateway (IGW):** Horizontally scaled, redundant VPC component that allows communication between instances in your VPC and the internet. You attach one IGW per VPC.
*   **NAT Gateway (Network Address Translation):** Allows instances in a *private subnet* to initiate outbound traffic to the internet (e.g., to download software updates) while preventing the internet from initiating connections to those instances.
    *   Must be deployed in a *public subnet*.
    *   Requires an Elastic IP (Static Public IP).
    *   Is AZ-scoped. For high availability, you must deploy one NAT Gateway in each AZ.

### Firewalls: Security Groups vs. NACLs
*   **Security Groups (SGs):** 
    *   Operate at the **Instance Level** (ENI).
    *   **Stateful:** If you allow inbound traffic on port 80, the return outbound traffic is automatically allowed, regardless of outbound rules.
    *   **Allow rules only:** You cannot create explicit "Deny" rules. (Implicit deny by default).
    *   Can reference other Security Groups as a source/destination (e.g., "Allow port 3306 inbound only from the Web Server SG").
*   **Network ACLs (NACLs):**
    *   Operate at the **Subnet Level**.
    *   **Stateless:** Return traffic must be explicitly allowed. If you allow inbound HTTP on port 80, you must explicitly allow outbound traffic on the ephemeral port range (1024-65535) for the response.
    *   Supports both **Allow and Deny** rules. Rules are evaluated in number order (lowest first).
    *   Default NACL allows all inbound/outbound. Custom NACLs deny all by default.

### VPC Interconnectivity
*   **VPC Peering:** A point-to-point connection between two VPCs (same or cross-region, same or cross-account). 
    *   **Non-transitive:** If A peers with B, and B peers with C, A cannot talk to C. You must peer A directly to C.
    *   CIDR blocks cannot overlap.
*   **Transit Gateway:** A network transit hub that connects thousands of VPCs and on-premises networks. 
    *   Supports **transitive routing** (hub-and-spoke model).
    *   Replaces the complex mesh of VPC peering.

### VPC Endpoints (AWS PrivateLink)
Allows you to securely connect your VPC to supported AWS services (like S3, DynamoDB, SNS) *without* routing traffic over the public internet. The traffic remains on the AWS backbone.
*   **Gateway Endpoints:** Free. Modifies the route table. Only supports S3 and DynamoDB.
*   **Interface Endpoints:** Creates an Elastic Network Interface (ENI) with a private IP in your subnet. Costs an hourly fee + data processing fee. Supports most other AWS services.

### Hybrid Cloud Connectivity
*   **Site-to-Site VPN:** Creates an encrypted IPSec tunnel over the public internet. Connects a Virtual Private Gateway (VGW) on the AWS side to a Customer Gateway (CGW) on-premises. Quick to set up, but bandwidth is limited to 1.25 Gbps per tunnel, and internet latency fluctuates.
*   **Client VPN:** Allows remote users to connect to the VPC using OpenVPN clients.
*   **Direct Connect (DX):** A dedicated, physical fiber-optic connection bypassing the public internet entirely. 
    *   Provides consistent, low-latency performance (1 Gbps, 10 Gbps, 100 Gbps).
    *   Takes weeks or months to provision physically.
    *   **Architecture Pattern:** Establish a Direct Connect connection, and configure a Site-to-Site VPN as an encrypted backup link in case the DX fiber is cut.

---

## Load Balancers

Elastic Load Balancing (ELB) distributes incoming application traffic across multiple targets.

### Application Load Balancer (ALB)
*   **Layer 7 (Application layer).** Operates on HTTP, HTTPS, gRPC, WebSocket.
*   **Content-Based Routing:** Routes traffic based on URL path (`/images` -> Image Target Group), Host header (`api.domain.com`), Query strings, or HTTP headers.
*   **Targets:** EC2 instances, IP addresses, ECS containers, Lambda functions.
*   **Sticky Sessions:** Uses cookies to route requests from a specific client to the same target consistently.
*   If a target application crashes, ALB returns an HTTP 502/504 error.

### Network Load Balancer (NLB)
*   **Layer 4 (Transport layer).** Operates on TCP, UDP, TLS.
*   **Extreme Performance:** Handles millions of requests per second with sub-millisecond latency.
*   **Static IP:** NLB provides one static IP per AZ, which is useful for whitelisting on corporate firewalls. (ALB IPs change dynamically).
*   **Preserves Client IP:** The target instance sees the original client IP. (ALB places the client IP in the `X-Forwarded-For` header).

### Gateway Load Balancer (GLB)
*   **Layer 3 (Network layer).** Uses the GENEVE encapsulation protocol.
*   **Purpose:** Deploy, scale, and manage inline third-party network virtual appliances (e.g., Palo Alto firewalls, Intrusion Detection Systems).

### Load Balancer Features
*   **Cross-Zone Load Balancing:** Distributes traffic evenly across all targets in all AZs. (Always ON for ALB; OFF by default for NLB to reduce inter-AZ data transfer costs).
*   **Connection Draining (Deregistration Delay):** When an instance is marked unhealthy or is being terminated, the load balancer stops sending *new* requests but allows existing, in-flight requests to complete before fully deregistering the instance (default 300 seconds).

---

## Route 53 (DNS)
Highly available, scalable Domain Name System (DNS) web service.

### Records
*   **A Record:** Hostname to IPv4.
*   **AAAA Record:** Hostname to IPv6.
*   **CNAME:** Hostname to Hostname (cannot be used for the root domain/zone apex, e.g., `domain.com`).
*   **Alias Record (AWS Specific):** Maps a hostname to an AWS resource (ALB, CloudFront, S3 website). **Crucial:** Alias records *can* be used at the zone apex, and queries to Alias records are free. Always use Alias over CNAME for AWS resources.

### Routing Policies
1.  **Simple:** Standard DNS resolution. Returns one or more IP addresses randomly. No health checks.
2.  **Weighted:** Distributes traffic across resources based on assigned weights (e.g., 80% to v1, 20% to v2). Ideal for A/B testing and Blue/Green deployments.
3.  **Latency:** Routes users to the AWS Region that provides the lowest network latency.
4.  **Geolocation:** Routes based on the physical location of the user (e.g., route all EU users to `eu-central-1`).
5.  **Geoproximity:** Routes based on physical distance, allowing you to shift traffic using a "bias" value (requires Route 53 Traffic Flow).
6.  **Failover:** Active-Passive setup. If the primary health check fails, Route 53 returns the IP of the secondary resource.
7.  **Multi-Value Answer:** Returns up to 8 healthy IPs. Acts as a simple client-side load balancer.

---

## CloudFront (CDN)
Amazon CloudFront is a Content Delivery Network that caches content at Edge Locations to reduce latency and origin server load.

*   **Origins:** S3 buckets, ALBs, EC2 instances, API Gateway, or any custom HTTP backend.
*   **Cache Behaviors:** Define TTLs (Time to Live), allowed HTTP methods, and whether to forward headers/cookies/query strings to the origin.
*   **Invalidation:** Manually clearing the cache before the TTL expires. You are charged for invalidations after the first 1,000 paths per month.
*   **Origin Access Control (OAC):** Secures S3 bucket origins so users *must* access files via CloudFront and cannot bypass the CDN to hit the S3 URL directly. (Replaces the legacy Origin Access Identity - OAI).
*   **Edge Compute:**
    *   **CloudFront Functions:** Lightweight JavaScript code executed for *viewer* requests/responses. Sub-millisecond execution. Used for URL rewrites, header manipulation, cache key normalization.
    *   **Lambda@Edge:** Heavier Node.js/Python functions executed for *viewer* AND *origin* requests/responses. Can access the network/VPC. Used for complex authentication or fetching data.

## GCP Equivalents

| AWS Service | GCP Equivalent |
| :--- | :--- |
| VPC | VPC |
| NAT Gateway | Cloud NAT |
| Security Group | VPC Firewall Rules |
| Application Load Balancer | Global/Regional External HTTP(S) Load Balancer |
| Route 53 | Cloud DNS |
| CloudFront | Cloud CDN |
| Direct Connect | Cloud Interconnect |
