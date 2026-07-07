# Module 8: Modern Network Infrastructure

---

## 1. CDN — Content Delivery Network

A CDN is a geographically distributed network of servers (Points of Presence / PoPs) that cache and serve content close to users, reducing latency and offloading origin servers.

### How CDNs Work

```
Without CDN:
  User (Mumbai) → request → Origin server (US) = ~200ms RTT

With CDN:
  User (Mumbai) → request → CDN PoP (Mumbai) = ~5ms
  CDN PoP checks cache → HIT: serve immediately
                       → MISS: fetch from origin, cache, serve
```

### CDN Caching Behavior

**Cache HIT**: Content is in the CDN edge cache. Served immediately without touching the origin.

**Cache MISS**: Content not cached (first request or expired). CDN fetches from the origin server, caches the response (per Cache-Control headers), and serves it. Subsequent requests for the same content are HIT.

**Cache invalidation**: When content changes, the CDN must evict old cached copies.
- **TTL expiry**: Wait for Cache-Control max-age to expire naturally (simplest, but stale content served during TTL).
- **Purge APIs**: CDN providers offer APIs to explicitly invalidate specific URLs or patterns instantly.
- **Versioned URLs**: Instead of invalidating, change the URL (`/style.v2.css`). Old browsers keep using old cached version; new clients get new version. Zero invalidation needed — each version is cached forever.

### CDN Use Cases

**Static assets**: Images, CSS, JavaScript, fonts. Long TTLs (days/months). High cache hit rate.

**Dynamic content**: HTML pages that change per user. CDN may cache if responses are identical (e.g., homepage for logged-out users). Short TTL or no-cache.

**Video streaming**: CDNs excel here. Video segments (HLS/DASH) are fixed chunks — perfectly cacheable. Netflix, YouTube, and Twitch all use CDNs for video delivery.

**Security**: CDNs absorb DDoS traffic. Anycast routing distributes attack across global PoPs. WAF (Web Application Firewall) at the CDN edge filters malicious requests.

### CDN Routing — Anycast + GeoDNS

**Anycast**: Multiple CDN PoPs share the same IP address. BGP routes requests to the nearest PoP. Client always reaches nearest server without any application logic.

**GeoDNS**: DNS-based routing. CDN's authoritative DNS returns different IPs based on the requester's IP geolocation. Client resolves CDN hostname → gets IP of nearest PoP.

---

## 2. Load Balancers

A load balancer distributes incoming traffic across multiple backend servers to achieve horizontal scaling, high availability, and fault tolerance.

### Layer 4 (Transport) Load Balancer

Routes based on IP + TCP port only. Does not inspect HTTP content. Does not decrypt TLS.

**How it works**: Maintains a mapping of client connections to backend servers. Uses NAT (rewrites destination IP:port) or IP tunneling to forward packets.

**Algorithms**: Round-robin, least connections, IP hash (same client IP always goes to same backend — useful for stateful apps without session replication).

**Pros**: Extremely fast (simple header inspection only). Can handle any TCP/UDP protocol. Low latency.

**Cons**: Cannot make routing decisions based on URL, headers, or cookies. Cannot do TLS termination or HTTP-level health checks.

**Examples**: AWS NLB, HAProxy in TCP mode.

### Layer 7 (Application) Load Balancer

Terminates TLS. Reads HTTP headers, URL paths, and request body. Makes content-aware routing decisions.

**Capabilities:**
- Route `/api/*` to API servers, `/static/*` to CDN or static servers
- Route by `Host` header (virtual hosting — one LB serving multiple domains)
- Route based on `Cookie` value (e.g., beta users to new servers)
- Sticky sessions: ensure a user always goes to the same backend (using a session cookie)
- A/B testing: route 10% of traffic to canary servers
- Health checks: HTTP GET /health checks; remove unhealthy backends automatically

**Examples**: AWS ALB, nginx, HAProxy in HTTP mode, Envoy.

### Load Balancing Algorithms

**Round Robin**: Rotate through backends in order. Simple, fair. Doesn't account for server load or response time.

**Weighted Round Robin**: Assign weights; higher-weight backends get proportionally more requests. Useful when backends have different capacities.

**Least Connections**: Route to the backend with the fewest active connections. Better for variable-length requests (some requests take much longer than others).

**IP Hash (Consistent Hashing)**: Hash the client IP (or session ID) to always select the same backend. Provides session stickiness without application-level state. Problem: uneven distribution if few clients generate most traffic.

**Random with two choices (Power of Two)**: Pick two random backends, send to the one with fewer connections. Excellent performance (approaches "least connections" with much lower overhead).

### Health Checks

Load balancers continuously check backend health:
- **Passive**: Detect failures from error responses (5xx, connection refused). No extra traffic.
- **Active**: Send periodic probe requests (TCP connect, HTTP GET /health). Detect failures before real traffic hits the server.

Failed backends are automatically removed from the pool. When they recover, they're re-added.

---

## 3. Reverse Proxy vs Forward Proxy

### Forward Proxy

Sits between **clients and the internet**. The internet sees the proxy's IP, not the client's. Client must be configured to use the proxy.

```
Client → Forward Proxy → Internet
```

Use cases:
- Corporate internet filter (block social media, log traffic)
- Bypass geo-restrictions (VPN-like for HTTP)
- Anonymization (Tor exit nodes are forward proxies)
- Cache frequently accessed content (reduce ISP bandwidth)

### Reverse Proxy

Sits between **the internet and backend servers**. Clients see the proxy's IP; backend IPs are hidden.

```
Internet → Reverse Proxy → Backend Servers
```

Use cases:
- **Load balancing**: Distribute requests across backends
- **TLS termination**: Handle TLS at the proxy; backends get plain HTTP (simpler backend config, one certificate location)
- **Caching**: Cache backend responses (nginx as caching layer)
- **Compression**: Compress responses before sending to clients
- **Security**: Hide backend IPs, WAF rules, rate limiting
- **Protocol translation**: Client speaks HTTP/2; backend speaks HTTP/1.1

**nginx** is most commonly used as a reverse proxy. **Envoy** is popular in microservices (service mesh — sidecar proxy pattern).

---

## 4. Service Mesh

In microservices architectures, services need to talk to each other reliably. A **service mesh** handles this communication transparently.

**Sidecar proxy pattern**: Every service has a sidecar proxy (typically **Envoy**) deployed alongside it. All traffic in and out of the service goes through the sidecar.

```
Service A → Envoy sidecar → (network) → Envoy sidecar → Service B
```

**What the mesh provides:**
- **mTLS everywhere**: All service-to-service communication is encrypted and mutually authenticated automatically. No code changes needed.
- **Load balancing**: Client-side load balancing with sophisticated algorithms.
- **Circuit breaking**: If Service B is failing, the mesh automatically stops sending traffic (avoiding cascading failures).
- **Retries and timeouts**: Configurable retry policies without code changes.
- **Observability**: All traffic metrics, distributed traces, and logs collected automatically.
- **Traffic management**: Route 10% of traffic to v2 of a service (canary deployments).

**Control plane**: **Istio** (configures Envoy sidecars). **Linkerd** (lighter-weight alternative).

---

## 5. NAT Gateway and Internet Gateway

**Internet Gateway**: A route in a VPC/cloud network that allows traffic to flow to/from the public internet. Attached to a VPC; subnets with a route to the IGW are "public subnets."

**NAT Gateway**: Allows resources in private subnets (no public IPs) to initiate outbound connections to the internet (e.g., to download software updates) while preventing inbound connections from the internet.

```
Private EC2 → NAT Gateway (public subnet) → Internet Gateway → Internet
Internet → blocked (no inbound NAT)
```

---

## 6. Content Routing and Modern Patterns

### API Gateway

A specialized reverse proxy for APIs. Sits in front of all backend services and provides:
- **Authentication/Authorization**: Validate JWT tokens before forwarding.
- **Rate limiting**: Per-user or per-IP request limits.
- **Request transformation**: Translate/enrich requests before forwarding.
- **Protocol translation**: REST → gRPC.
- **Routing**: Route `/users/*` to user-service, `/orders/*` to order-service.

Examples: AWS API Gateway, Kong, nginx (configured as API gateway).

### BGP Anycast for Redundancy

Cloud providers and CDNs use BGP anycast to advertise the same IP from multiple data centers. Clients automatically connect to the nearest one. If a data center goes offline, BGP converges and traffic routes to the next nearest — automatic global failover without DNS changes.

### GeoDNS for Disaster Recovery

DNS returns different IPs based on geographic location:
- US users → US data center IPs
- EU users → EU data center IPs

On failure, TTL (typically short for active-active systems: 60 seconds) governs how quickly DNS changes propagate. Combined with health monitoring → can redirect traffic within 1-2 minutes of failure detection.

---

## 7. Network Diagnostics Tools

### ping

Tests reachability. Sends ICMP Echo Request, measures round-trip time.
```
ping 8.8.8.8          # Basic reachability
ping -c 4 8.8.8.8     # Send 4 packets
```

### traceroute / tracert

Maps the path to a destination by sending packets with increasing TTL.
```
traceroute 8.8.8.8
```

### nslookup / dig

DNS lookup tools.
```
dig example.com A           # A record
dig example.com MX          # Mail servers
dig @8.8.8.8 example.com   # Use specific resolver
dig +trace example.com      # Full recursive resolution trace
```

### netstat / ss

View active connections and listening ports.
```
ss -tunap        # All TCP/UDP connections with process names
ss -tlnp         # Listening ports
netstat -an      # All connections (older)
```

### tcpdump

Capture network packets for analysis.
```
tcpdump -i eth0 port 80              # HTTP traffic
tcpdump -i eth0 host 1.2.3.4        # Traffic to/from IP
tcpdump -w capture.pcap             # Save to file (open in Wireshark)
```

### curl

HTTP testing.
```
curl -v https://example.com              # Verbose (shows TLS, headers)
curl -I https://example.com             # Headers only
curl -o /dev/null -w "%{time_total}" https://example.com  # Timing
curl -k https://self-signed.example.com  # Ignore cert errors
```

### nmap

Network port scanner.
```
nmap -p 80,443 example.com    # Scan specific ports
nmap -sV example.com          # Version detection
nmap -A 192.168.1.0/24        # Full scan of subnet
```
