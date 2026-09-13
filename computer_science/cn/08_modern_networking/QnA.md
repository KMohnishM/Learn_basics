# Q&A — Modern Network Infrastructure

---

## 🟢 Easy

**Q1. What is a CDN and how does it reduce latency?**

A CDN (Content Delivery Network) is a globally distributed network of edge servers (PoPs) that cache content close to users.

Latency reduction: Instead of a user in Mumbai fetching content from an origin server in the US (200ms RTT), they fetch from a CDN PoP in Mumbai (5ms RTT). The CDN caches the content on first request; subsequent requests are served locally without touching the origin.

Benefit stack: Lower latency + reduced origin load + better availability (edge absorbs failures) + DDoS protection (anycast diffusion of attack traffic).

---

**Q2. What is the difference between a forward proxy and a reverse proxy?**

**Forward proxy**: Between clients and the internet. Clients direct their requests to the proxy. The internet sees the proxy's IP. Used for: internet filtering, anonymization, client-side caching.

**Reverse proxy**: Between the internet and backend servers. Clients connect to the proxy; backend IPs are hidden. Used for: load balancing, TLS termination, caching, WAF, rate limiting.

Key distinction: Forward proxy serves the client's interests. Reverse proxy serves the server/operator's interests.

---

**Q3. What is TLS termination at a load balancer? Why is it done?**

TLS termination: The load balancer handles the TLS handshake and decrypts incoming HTTPS traffic. Backend servers receive plain HTTP.

**Why:**
1. **Centralized certificate management**: Only one place (the LB) holds the TLS certificate. Backends don't need certificates.
2. **Performance**: TLS is CPU-intensive. Offload to a dedicated LB or hardware accelerator; backends do no crypto work.
3. **Simpler backends**: Backends don't need TLS configuration. Health checks are plain HTTP.
4. **L7 inspection**: After termination, the LB can read HTTP content for routing/WAF rules.

**Trade-off**: Traffic between LB and backends is unencrypted (plain HTTP). If the internal network is not trusted (e.g., shared cloud infrastructure), use **TLS re-encryption** — LB terminates TLS from clients, then establishes new TLS to backends.

---

**Q4. Name three load balancing algorithms and when each is best suited.**

1. **Round Robin**: Rotate through backends. Best when: all requests are similar in cost and backends are homogeneous.

2. **Least Connections**: Route to backend with fewest active connections. Best when: requests have variable processing time (some take 1ms, some take 5 seconds). Prevents one backend from accumulating slow requests while others are idle.

3. **IP Hash**: Hash client IP → always same backend. Best when: application has server-side session state that isn't replicated (session stickiness needed). Problem: poor distribution if a few IPs dominate traffic.

---

**Q5. What is a service mesh? What problem does it solve?**

In a microservices architecture with 100 services, each service must: authenticate callers, encrypt traffic, retry failed requests, implement circuit breaking, emit metrics. Implementing this in every service is repetitive and error-prone.

A **service mesh** moves this infrastructure logic out of application code into a **sidecar proxy** (Envoy) that runs alongside each service. All inter-service traffic flows through the proxies. mTLS, retries, circuit breaking, tracing, and load balancing happen automatically at the proxy level — no code changes.

---

## 🟡 Medium

**Q6. Explain the difference between L4 and L7 load balancers with a concrete routing example.**

**L4 Load Balancer**: Routes based on IP + port only. Cannot see HTTP content.

```
Client connects to LB:443 → LB sees: "TCP connection to port 443"
LB routes to Backend A: 10.0.0.1:443
Client ←→ Backend A directly (LB does NAT)
LB cannot see: URL, headers, which tenant, content type
```

**L7 Load Balancer**: Terminates TLS, reads HTTP content, makes content-aware decisions.

```
Client connects to LB:443 → LB terminates TLS, reads HTTP
Request: GET /api/users/123 with Host: api.example.com

Routing rules:
  /api/* → backend API servers (10.0.1.x)
  /admin/* → admin servers (10.0.2.x, require auth header)
  Host: static.example.com → CDN backends (10.0.3.x)
  Cookie: beta=true → canary servers (10.0.4.x)

LB can also: add X-Forwarded-For header, strip auth tokens, compress response
```

L7 is required for any routing logic that depends on what's IN the request, not just where it's going.

---

**Q7. What is a circuit breaker in a load balancer / service mesh? Why is it important?**

**Problem**: Service A calls Service B. Service B is overloaded and responds slowly. Service A waits, accumulates pending requests, its thread pool fills up, Service A becomes slow, Service C that calls A also becomes slow... **Cascading failure** brings down the whole system.

**Circuit Breaker**: After N consecutive failures (or timeout rate exceeds threshold), the circuit "opens" — requests to Service B immediately fail fast (without actually sending to B). After a timeout, a few test requests are allowed ("half-open" state). If they succeed, circuit closes; if not, stays open.

```
States:
CLOSED → normal operation, requests flow
  ↓ (N failures)
OPEN   → fast fail, return error immediately
  ↓ (timeout)
HALF-OPEN → try a few requests
  ↓ (success) → CLOSED
  ↓ (failure) → OPEN
```

**Why important**: Prevents cascading failures. Allows the failing service time to recover without being hammered. Gives upstream services control.

**Netflix Hystrix** (now deprecated) popularized this pattern. Now commonly implemented in service meshes (Istio/Envoy) as outlier detection.

---

**Q8. How does CDN cache invalidation work? Compare TTL expiry vs purge APIs vs versioned URLs.**

**TTL Expiry**: Set `Cache-Control: max-age=N`. CDN serves cached content until max-age expires, then fetches fresh. Simple; no coordination needed. Problem: stale content served for up to N seconds after origin changes. Bad for time-sensitive content.

**Purge API (Cache Invalidation)**: CDN providers expose APIs to immediately evict specific URLs or patterns. Example: Cloudflare's Cache Purge API. After deploying a new version, call the API to purge `https://example.com/app.js`. Next request fetches fresh. Problem: purge must propagate to all edge nodes (eventual consistency, seconds to minutes). Race conditions if purge and new requests overlap.

**Versioned URLs (Fingerprinting)**: Embed content hash in the URL: `app.abc123.js`. When content changes, the URL changes: `app.def456.js`. The HTML references the new URL. Old URL still cached forever (harmlessly). New URL gets cached from first request.
- **Pros**: No invalidation needed. Old and new versions can coexist. CDN caches both permanently (immutable). Works perfectly with `Cache-Control: immutable, max-age=31536000`.
- **Cons**: HTML itself must be invalidated/uncached (short TTL or no-cache) so browsers get the new script URLs. Works best in build systems (webpack, Vite) that fingerprint automatically.

**Best practice**: Versioned URLs for static assets (JS, CSS, images) + short TTL or purge for HTML.

---

## 🔴 Hard

**Q9. Design the network architecture for a globally distributed web application with < 50ms latency for 95% of users worldwide, 99.99% availability, and the ability to survive an entire region going offline.**

**Architecture:**

**1. Multi-region active-active:**
- Deploy in 3+ regions (e.g., us-east, eu-west, ap-southeast).
- All regions serve live traffic simultaneously (not active-standby).
- Data replicated across regions (eventual consistency for non-critical data, multi-region consensus for critical writes).

**2. Global CDN layer:**
- Static assets served from CDN edge PoPs (100+ locations globally).
- CDN: Cloudflare or Fastly (anycast routing → nearest PoP).
- < 50ms latency for static content achieved by CDN alone.

**3. GeoDNS + Anycast for origin routing:**
- API requests routed to nearest region via GeoDNS (low TTL: 30-60s).
- Anycast for regional LBs — automatic routing within a region.

**4. Per-region load balancing:**
- L7 load balancer (e.g., AWS ALB) in each region.
- Multiple application server instances behind the LB.
- Auto-scaling based on request rate/CPU.

**5. Health monitoring + DNS failover:**
- Global health checker (e.g., Route53 health checks, Cloudflare health checks) monitors each region.
- If us-east fails: DNS record for us-east removed. Traffic routed to eu-west and ap-southeast automatically.
- TTL 30s → failover in ~1-2 minutes (health check detection + TTL propagation).

**6. Regional failover within a region:**
- Multi-AZ (availability zone) deployment within each region.
- LB automatically routes around failed AZs.
- Database: Multi-AZ with synchronous replication (RDS Multi-AZ, Aurora).

**Latency achievement:**
- Static (CDN): 5-30ms globally ✅
- Dynamic API: 20-50ms with nearest region ✅

**Availability math:**
- Each region: 99.95% uptime.
- Three independent regions, any can serve traffic.
- System uptime: 1 - (0.0005)^3 ≈ 99.9999999% (nine nines theoretical).
- Real availability limited by failover time: ~99.99% (4 nines) accounting for detection/propagation delays. ✅

---

**Q10. A user reports that a website is slow. Walk through how you'd diagnose the issue using network diagnostic tools.**

**Step 1: Basic reachability**
```bash
ping example.com           # Is the host reachable? What's the RTT?
```
If ping fails: DNS issue, routing issue, or server down.
If ping high RTT: Network path issue (far routing, congestion).

**Step 2: Trace the path**
```bash
traceroute example.com     # Which hop is introducing latency?
```
Look for: high RTT at specific hop (congested/slow link), "*" (packet loss at hop, or ICMP blocked), routing asymmetry.

**Step 3: DNS resolution time**
```bash
dig example.com +stats     # Check query time
dig @8.8.8.8 example.com  # Compare with different resolver
```
High DNS resolution time → wrong resolver, DNSSEC validation overhead, authoritative server slow.

**Step 4: HTTP-level timing**
```bash
curl -o /dev/null -w "
  DNS: %{time_namelookup}s
  TCP connect: %{time_connect}s
  TLS handshake: %{time_appconnect}s
  First byte: %{time_starttransfer}s
  Total: %{time_total}s
" https://example.com
```
This breaks down exactly where time is spent: DNS, TCP, TLS, server processing, transfer.

**Step 5: Check headers and response**
```bash
curl -I -v https://example.com  # Show request/response headers
```
Check: Missing cache headers (every request hits origin), large response (compression not enabled), redirects (3xx chain).

**Step 6: Check what's actually being requested**
```bash
tcpdump -i eth0 -w capture.pcap host example.com
# Open in Wireshark: filter by HTTP/HTTPS
```

**Diagnosis mapping:**
- Slow DNS → use faster resolver (1.1.1.1), TTL too low
- Slow TCP connect → far routing (use CDN), packet loss
- Slow TLS → TLS 1.2 (upgrade to 1.3), session resumption not working
- Slow first byte → server processing slow (backend issue, not network)
- Large transfer → enable gzip/brotli compression, use smaller images
