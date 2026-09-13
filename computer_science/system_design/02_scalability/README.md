# Module 2: Scalability

> **Goal**: Understand how systems grow from handling 100 requests/second to 1,000,000 requests/second.
> Scalability is about adding capacity without fundamentally changing the system's architecture.

---

## Table of Contents

1. [Vertical vs Horizontal Scaling](#1-vertical-vs-horizontal-scaling)
2. [Stateless vs Stateful Services](#2-stateless-vs-stateful-services)
3. [Load Balancing Algorithms In Depth](#3-load-balancing-algorithms-in-depth)
4. [L4 vs L7 Load Balancers](#4-l4-vs-l7-load-balancers)
5. [Health Checks and Graceful Degradation](#5-health-checks-and-graceful-degradation)
6. [Session Management](#6-session-management)
7. [Auto-Scaling](#7-auto-scaling)
8. [Geographic Distribution](#8-geographic-distribution)

---

## 1. Vertical vs Horizontal Scaling

### 1.1 Vertical Scaling (Scale Up)

Vertical scaling means adding more resources to an existing server: more CPU cores, more RAM,
faster storage, faster network interfaces.

```
VERTICAL SCALING PROGRESSION:

t=0: 4 CPU, 16 GB RAM, 1 server
     Handles: 1,000 req/sec

t=6mo: 16 CPU, 64 GB RAM, 1 server (upgraded)
       Handles: 4,000 req/sec
       Cost: 3x more expensive

t=1yr: 64 CPU, 256 GB RAM, 1 server (premium hardware)
       Handles: 15,000 req/sec
       Cost: 15x more expensive (premium hardware is non-linear in cost)

LIMIT: You hit the largest available machine.
       AWS largest instance: u-24tb1.metal -- 448 vCPUs, 24 TB RAM
       But this costs ~$200/hour! And still has a ceiling.
```

**When Vertical Scaling is Appropriate**:
- Early stage when your team lacks DevOps maturity to manage distributed systems
- Database servers (horizontal DB scaling is hard; vertical buys you significant time)
- Applications with shared state that cannot be distributed
- When the code is not designed for horizontal scaling

**The Hard Limits of Vertical Scaling**:
- There exists a maximum machine size (you cannot scale infinitely)
- Larger machines cost disproportionately more per unit of compute (premium pricing)
- A single server is a single point of failure (no redundancy)
- Upgrading requires downtime (unless you do a live migration)
- Memory bandwidth and bus speeds become bottlenecks before CPU is exhausted

**The Cost Curve**:
```
Performance
    ^
    |           *  <- Vertical limit
    |         *
    |       *
    |     *     <- Cost increases faster than performance
    |   *
    | *
    +----------------> Cost

Diminishing returns: 10x cost does NOT buy you 10x performance
```

### 1.2 Horizontal Scaling (Scale Out)

Horizontal scaling means adding more servers of the same type, distributing load across them.

```
HORIZONTAL SCALING PROGRESSION:

t=0: 1 server, 4 CPU, 16 GB RAM
     Handles: 1,000 req/sec

t=6mo: 4 servers, same spec, behind load balancer
       Handles: 4,000 req/sec
       Cost: 4x (linear!)

t=1yr: 16 servers, same spec
       Handles: 16,000 req/sec
       Cost: 16x (still linear!)

t=2yr: 100 servers, commodity hardware
       Handles: 100,000 req/sec
       Cost: 100x (linear -- but using cheap commodity hardware!)
```

**Why Horizontal Scaling is Preferred**:
- **Near-linear scaling**: Double the servers, double the capacity (in theory)
- **Cost-effective**: Commodity hardware (the same servers in your laptop) in large quantities
- **No single point of failure**: If one server dies, others continue serving traffic
- **No downtime for capacity changes**: Add/remove servers without stopping the system
- **Geographic distribution**: Servers can be in different physical locations

**The Challenges of Horizontal Scaling**:
- **State management**: If each server has local state (e.g., user sessions in memory),
  adding more servers creates inconsistency. This is the central challenge.
- **Data consistency**: All servers must see the same database state
- **Operational complexity**: Managing 100 servers is harder than managing 1
- **Network overhead**: Servers must communicate, adding latency
- **Some workloads are inherently sequential**: Not everything can be parallelized

### 1.3 The Amdahl's Law Problem

Even with perfect horizontal scaling infrastructure, Amdahl's Law limits speedup:

```
Speedup = 1 / (S + (1-S)/N)

Where:
  S = fraction of the work that MUST be serial (cannot be parallelized)
  N = number of parallel processors/servers
  (1-S) = fraction that can be parallelized

Example: Your app spends 20% of time in serial code (e.g., hitting a single DB)
  S = 0.20, N = infinity (infinite servers)
  Maximum speedup = 1 / 0.20 = 5x

You can NEVER get more than 5x speedup, no matter how many servers you add!

This is why database bottlenecks kill horizontal scaling:
  If DB is the bottleneck, adding more app servers does nothing.
  You must also scale the database (read replicas, sharding, caching).
```

### 1.4 When to Choose Which Strategy

```
Scaling Decision Matrix:

Situation                          Recommendation
------------------------------------------------------------
Small team, <10K req/sec           Vertical first (buy time)
Stateful application (sessions)    Vertical, OR externalize state first
Database layer bottleneck          Vertical (easier), then replicas/sharding
App layer bottleneck               Horizontal (app servers are usually stateless)
Geographic users                   Horizontal + multi-region
Startup with fast growth           Horizontal from day 1 if team can handle it
Regulatory: data stays in region   Horizontal + regional sharding
```

---

## 2. Stateless vs Stateful Services

This is the MOST IMPORTANT concept for horizontal scaling. If you understand this fully,
you understand 80% of why horizontal scaling is hard.

### 2.1 Stateful Services

A stateful service stores information about individual clients/users between requests.
This state is kept in the server's own memory (or local disk).

```
STATEFUL SERVER EXAMPLE:

Server A (192.168.1.1):
  Memory: {
    "user_123_session": { user_id: 123, cart: ["item_a"], logged_in: true },
    "user_456_session": { user_id: 456, cart: ["item_b", "item_c"], logged_in: true }
  }

Problem: If User 123's NEXT request goes to Server B...

Server B (192.168.1.2):
  Memory: {} <- User 123's session data is NOT here!
  Result: User 123 appears logged out. Cart is empty. BAD USER EXPERIENCE.

The server needs to remember who you are between requests.
```

**The Sticky Session "Solution"** (and why it's a trap):
```
Load Balancer tracks which server each user goes to and always routes them there.

Pros:
  - Simple to implement (single IP-to-server mapping in the LB)
  - Works for small deployments

Cons:
  - Uneven distribution: If a server has many "heavy" users, it gets overloaded
    even though other servers are idle
  - Server failure = losing all sessions on that server (users get logged out)
  - Cannot scale down (can't remove a server that has active sessions)
  - No-op for new server adds (existing sessions don't migrate)
  - Fundamentally contradicts the purpose of load balancing
```

### 2.2 Stateless Services

A stateless service stores NO information about individual clients in server memory.
Every request must contain ALL the information needed to process it.

```
STATELESS SERVER EXAMPLE:

Request from User 123 to Server A:
  Headers: {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxMjN9..."
    (JWT token containing user_id and other claims)
  }
  Server A decodes JWT, verifies signature, knows user_id = 123.
  Fetches cart from Redis or Postgres.
  Returns response.

NEXT request from User 123 goes to Server B:
  SAME Authorization header.
  Server B decodes JWT, verifies signature, knows user_id = 123.
  Fetches cart from Redis or Postgres.
  Returns response.

Server B doesn't need to "know" about User 123 from before.
Each request is self-contained.
```

**How Statelessness Enables Horizontal Scaling**:
```
1. Any server can handle any request
   --> Load balancer can use simple round-robin, no sticky sessions needed

2. Adding new servers is trivial
   --> New server starts, immediately handles requests, no "warm-up" needed

3. Server failures don't lose user state
   --> Sessions are in Redis, not in dead server's memory

4. Auto-scaling works correctly
   --> Scale down to 2 servers at night, scale up to 50 servers at noon
   --> No sessions are "stranded" on servers being removed
```

**The Externalized State Pattern**:
```
What was in server memory:
  user sessions -> Redis/Memcached
  application config -> Configuration Service (Consul, AWS Parameter Store)
  uploaded files -> Object Storage (S3)
  shopping carts -> Redis or Database
  rate limit counters -> Redis
  distributed locks -> Redis SETNX or ZooKeeper

The Rule: Server memory is a CACHE, not the SOURCE OF TRUTH.
          Servers can die and be reborn without any user-visible impact.
```

### 2.3 JWT: The Classic Stateless Session Mechanism

```
JWT Structure: header.payload.signature

Header (Base64):  {"alg": "HS256", "typ": "JWT"}
Payload (Base64): {"user_id": 123, "email": "alice@example.com", "exp": 1704067200}
Signature:        HMACSHA256(header + "." + payload, SECRET_KEY)

How it enables stateless auth:
  1. User logs in with username/password
  2. Server verifies credentials against DB
  3. Server creates JWT signed with SECRET_KEY (known only to servers)
  4. Client stores JWT (localStorage, httpOnly cookie)
  5. Every subsequent request includes the JWT
  6. ANY server can verify the JWT by checking the signature with SECRET_KEY
     No DB lookup needed! Verification is purely computational.

Tradeoffs:
  PRO: No session storage needed (truly stateless)
  PRO: Any server can verify (no coordination)
  CON: Cannot be "revoked" before expiry without storing a blocklist
       (The famous "logout" problem -- the JWT is still valid until expiry)
  CON: Payload is Base64 encoded (not encrypted) -- don't put sensitive data in it
  CON: Larger than a simple session cookie
```

---

## 3. Load Balancing Algorithms In Depth

A load balancer distributes incoming requests across multiple servers.
The algorithm it uses determines efficiency, fairness, and behavior under various conditions.

### 3.1 Round Robin

The simplest algorithm: send each new request to the next server in a circular sequence.

```
Round Robin with 3 servers: [A, B, C]

Request 1 -> Server A
Request 2 -> Server B
Request 3 -> Server C
Request 4 -> Server A
Request 5 -> Server B
Request 6 -> Server C
...

Distribution: 33.3% to each server
```

**When it works**: Homogeneous servers (same specs) with requests of roughly equal cost.

**When it fails**: 
- Servers have different capacities (one is 2x as powerful but gets same traffic as weak ones)
- Requests have wildly varying costs (a 50ms request and a 5-second request get equal weight)
- Result: Uneven load distribution despite "balanced" request counts

### 3.2 Weighted Round Robin

Assign each server a weight. Servers with higher weight receive proportionally more requests.

```
Weighted Round Robin:
  Server A (weight=5): New (powerful) server -- 5/10 = 50% of traffic
  Server B (weight=3): Medium server       -- 3/10 = 30% of traffic
  Server C (weight=2): Older, weaker server -- 2/10 = 20% of traffic
  Total weights = 10

Request distribution using **smooth weighted round-robin** (Nginx default):
  A, B, A, C, A, B, A, B, A, C  (requests interleaved, not blocked)

  Note: Naive WRR would send A,A,A,A,A,B,B,B,C,C in a block — this causes
  micro-bursting to one server. Nginx uses smooth WRR to spread load evenly
  within each "cycle" while still respecting the weight ratios.
```

**When it works**: Heterogeneous servers (different CPU/RAM specs).

**Configuration in Nginx**:
```nginx
upstream backend {
    server backend1:8000 weight=5;
    server backend2:8000 weight=3;
    server backend3:8000 weight=2;
}
```

### 3.3 Least Connections

Route each new request to the server with the FEWEST active connections.

```
Current state:
  Server A: 100 active connections
  Server B: 45 active connections  <- WINNER, gets next request
  Server C: 73 active connections

Next request -> Server B

This is DYNAMIC -- the assignment changes based on real-time load.
```

**Why this is often better than round-robin**:
- Adapts to long-lived connections (some users hold connections for minutes)
- Adapts to slow requests (server processing a slow DB query gets fewer new requests)
- Better for APIs with mixed response times

**When it works best**: When requests have highly variable response times.

### 3.4 IP Hash (Session Persistence)

Hash the client's IP address and use the result to consistently route to the same server.

```
Algorithm:
  server_index = hash(client_ip) % number_of_servers

Client at 192.168.1.5 always goes to:
  hash("192.168.1.5") % 3 = 1 -> Server B (consistently)

Client at 10.0.0.1 always goes to:
  hash("10.0.0.1") % 3 = 2 -> Server C (consistently)
```

**When to use**: When server-side state is unavoidable (e.g., uploading a large file
in chunks, each chunk must go to the same server temporarily).

**Why it's usually wrong**:
- IP addresses change (mobile users switching from WiFi to 4G)
- Multiple users behind same NAT/proxy get same server (uneven load)
- Adding/removing servers recomputes all hash assignments (users get new servers, losing session)
- Use Consistent Hashing instead for better behavior when servers change

### 3.5 Consistent Hashing -- The Essential Algorithm

Consistent Hashing solves the problem that regular hashing has when you add/remove servers:
with regular hash(key) % N, changing N causes MOST keys to remap to new servers.
With consistent hashing, only K/N keys need to be remapped (where K = total keys, N = servers).

```
THE HASH RING CONCEPT:

1. Map the hash space to a circular ring (0 to 2^32 - 1, visualized as a circle)
2. Hash each SERVER and place it on the ring at that position
3. For each request: hash the client IP/key, find the NEXT clockwise server on the ring

         0
         |
    300 -+- 60
    \         /
270  |       |  90
      \     /
    240 -+- 120
         |
        180

If servers hash to positions 60, 180, 300:
  Client at position 20 -> goes to server at 60 (next clockwise)
  Client at position 100 -> goes to server at 180 (next clockwise)
  Client at position 250 -> goes to server at 300 (next clockwise)
  Client at position 320 -> goes to server at 60 (wraps around)

When a server is ADDED at position 120:
  Only clients between 60-120 are affected (they now go to the new server)
  All other clients are unaffected!
  Remapped keys: ~1/N of all keys (instead of ~all keys with regular hashing)

When a server is REMOVED at position 180:
  Only clients that were going to 180 are remapped to 240 (next clockwise)
  All other clients are unaffected!
```

**Virtual Nodes (the critical refinement)**:
```
Problem with basic consistent hashing:
  Servers hash to irregular positions -> uneven distribution
  Server A might get 40% of traffic, Server B 10%, Server C 50%

Solution: Virtual nodes
  Each physical server gets MULTIPLE positions on the ring (virtual nodes)
  A physical server with weight=3 gets 3 * V virtual nodes on the ring
  (Where V is typically 100-200 virtual nodes per server)

Result:
  Load distributes much more evenly (within 5-10% of ideal)
  Adding/removing servers causes exactly K/N keys to remap on average

Used by:
  Cassandra: Virtual nodes for data distribution
  DynamoDB: Consistent hashing for partition assignment
  Memcached: ketama library uses consistent hashing
  Content Delivery Networks: Cache shard assignment
```

---

## 4. L4 vs L7 Load Balancers

### 4.1 Layer 4 (Transport Layer) Load Balancers

L4 load balancers operate at the TCP/UDP level. They see IP addresses and port numbers
but do NOT inspect the contents of packets.

```
L4 Load Balancer sees:
  Source IP: 203.0.113.42
  Source Port: 54321
  Destination IP: 10.0.0.1 (load balancer IP)
  Destination Port: 443

L4 LB DOES NOT see:
  - HTTP headers (Host, URL path, cookies)
  - Request body
  - Protocol-specific data

L4 LB action: Route this TCP connection to Server B (10.0.0.5)
              and maintain the TCP state machine for this connection
```

**Characteristics**:
- Extremely fast (no content inspection, just IP routing)
- Very low latency (no connection termination and re-establishment)
- Can handle ANY TCP/UDP protocol (not just HTTP)
- Cannot route based on URL path, hostname, or cookies
- Cannot terminate SSL (encryption passthrough)
- Cannot do HTTP header inspection or modification

**Use cases**:
- DNS load balancing
- Gaming servers (UDP)
- Any non-HTTP protocol (MySQL, SMTP, custom TCP protocols)
- Ultra-low-latency requirements where even HTTP inspection overhead matters

### 4.2 Layer 7 (Application Layer) Load Balancers

L7 load balancers understand the HTTP(S) protocol. They terminate the client connection,
inspect the request, and make routing decisions based on content.

```
L7 Load Balancer sees everything:
  GET /api/v1/users/123/orders HTTP/1.1
  Host: api.example.com
  Authorization: Bearer eyJhbGci...
  Cookie: session=abc123
  X-Region: us-east-1

L7 LB can make decisions based on:
  - URL path: /api/* -> API servers, /static/* -> CDN, /admin/* -> admin servers
  - Host header: app.example.com -> app cluster, api.example.com -> API cluster
  - Cookie: Sticky session routing based on session_id cookie
  - HTTP method: GET -> read replicas, POST/PUT/DELETE -> primary
  - Header value: X-Premium-User: true -> premium cluster
  - Request body: (rarely, expensive)
```

**Characteristics**:
- Full HTTP protocol understanding
- SSL/TLS termination (decrypt at load balancer, forward plain HTTP to backends)
- Content-based routing (rich routing rules)
- Can add/modify headers (add X-Forwarded-For, remove internal headers)
- Can do HTTP health checks (check actual HTTP responses, not just TCP connections)
- Can implement rate limiting, authentication, WAF (Web Application Firewall)
- Slightly higher latency than L4 (connection termination + inspection)

**Use cases**:
- HTTPS APIs
- Microservices (routing /api/users/* to user-service, /api/orders/* to order-service)
- A/B testing (route 10% of traffic to new version based on cookie)
- Rate limiting at the edge
- Authentication gateway pattern

### 4.3 Comparison Table

```
Feature                     L4 LB           L7 LB
---------------------------------------------------
Protocol awareness          TCP/UDP only    HTTP/HTTPS aware
Routing criteria            IP + Port       URL, headers, body, cookies
SSL termination             No              Yes
Content-based routing       No              Yes
Performance                 Higher          Slightly lower (inspection overhead)
Protocol flexibility        Any TCP/UDP     HTTP/HTTPS primarily
Use for HTTP microservices  Suboptimal      Ideal
Cost (AWS)                  NLB (~$0.006)   ALB (~$0.008 per LCU)
Examples                    AWS NLB, IPVS   AWS ALB, Nginx, HAProxy, Traefik
```

---

## 5. Health Checks and Graceful Degradation

Load balancers must know which servers are healthy before routing traffic to them.

### 5.1 Active Health Checks

The load balancer actively sends requests to each backend to verify it's working.

```
Active Health Check Configuration (typical Nginx):

upstream backend {
    server app1:8000;
    server app2:8000;
    server app3:8000;
    
    # Nginx Plus / commercial feature (open source uses different syntax)
    # health_check interval=5s fails=3 passes=2 uri=/health;
}

# Open source Nginx uses check_interval in ngx_upstream_check_module
# Or use HAProxy which has native active health checks

Health check endpoint response:
  GET /health HTTP/1.1
  HTTP/1.1 200 OK
  {"status": "healthy", "db": "connected", "redis": "connected"}
```

**Health Check Logic**:
```
Check every 5 seconds.
If 3 consecutive checks FAIL -> mark server as DOWN, stop sending traffic.
If 2 consecutive checks PASS for a DOWN server -> mark as UP, resume traffic.

This hysteresis (fail N times, then pass M times) prevents flapping:
  Without hysteresis: Server is slow -> health check fails -> removed -> less load -> recovers
  -> added back -> gets load -> slows -> health check fails -> removed... (infinite loop!)
```

### 5.2 Passive Health Checks

The load balancer monitors actual user requests and marks servers as down if they fail.

```
Passive health check: Monitor real traffic for errors

If server returns 500 for 5 consecutive requests within 10 seconds:
  -> Mark server as temporarily unavailable
  -> Do not send new requests for 30 seconds
  -> Try again after 30 seconds (send 1 request as a probe)
  -> If probe succeeds, gradually increase traffic
  -> If probe fails, extend the 30-second timeout

Nginx config (approximate):
  upstream backend {
    server app1:8000 max_fails=5 fail_timeout=30s;
    server app2:8000 max_fails=5 fail_timeout=30s;
    server app3:8000 max_fails=5 fail_timeout=30s;
  }
```

### 5.3 Graceful Degradation

When a backend is being shut down (for deployment or scaling), it should stop receiving
NEW requests but finish processing EXISTING requests.

```
Graceful shutdown sequence:
  1. Server receives SIGTERM signal (from Kubernetes, SystemD, deployment pipeline)
  2. Server stops accepting NEW connections
  3. Load balancer's health check fails (server returns 503 on /health)
  4. Load balancer removes server from rotation (no new requests sent)
  5. Server finishes processing all in-flight requests (5-30 seconds)
  6. Server exits gracefully
  
This prevents requests being dropped mid-processing during deployments.

FastAPI graceful shutdown:
  import signal
  import asyncio
  
  shutdown_event = asyncio.Event()
  
  @app.on_event("shutdown")
  async def shutdown():
      shutdown_event.set()  # Stop accepting new requests
      await asyncio.sleep(30)  # Wait for in-flight requests
```

---

## 6. Session Management

### 6.1 The Session Problem

Traditional web apps store user state in server-side sessions:
```
1. User logs in
2. Server creates session: session_id = "abc123", data = {user_id: 456, cart: [...]}
3. Server stores session in memory: sessions["abc123"] = {user_id: 456, cart: [...]}
4. Server sends cookie: Set-Cookie: session_id=abc123
5. Next request: Cookie: session_id=abc123
6. Server looks up sessions["abc123"], finds user data
```

Problem: Step 6 only works on the SAME server that created the session in step 2-3.

### 6.2 Sticky Sessions (Band-Aid Solution)

```
Load Balancer configuration: "Always route user with session cookie X to server A"

Nginx implementation:
  upstream backend {
    ip_hash;  # Routes same IP to same server (simple form of sticky sessions)
  }

Or use the Nginx sticky module:
  upstream backend {
    sticky cookie srv_id expires=1h domain=.example.com path=/;
    server app1:8000;
    server app2:8000;
    server app3:8000;
  }

Problems (as discussed earlier):
  - Uneven load distribution
  - Session lost if server dies
  - Cannot scale down
```

### 6.3 Centralized Session Store (The Right Solution)

Move session storage OUT of server memory and into a shared, external store:

```
Architecture with Redis as session store:

[Client] --> [Load Balancer] --> [App Server A or B or C]
                                          |
                                    [Redis Session Store]
                                    {
                                      "session:abc123": {user_id: 456, cart: [...], exp: ...},
                                      "session:def456": {user_id: 789, cart: [...], exp: ...}
                                    }

Now:
  Request 1 with cookie=abc123 -> Server A -> reads session from Redis -> user_id=456
  Request 2 with cookie=abc123 -> Server B -> reads session from Redis -> user_id=456 (same!)
  
Any server can handle any request! Round-robin works perfectly.

Redis session implementation (Python):
  import redis
  import json
  import secrets
  
  r = redis.Redis(host='redis', port=6379)
  
  def create_session(user_data: dict) -> str:
      session_id = secrets.token_hex(32)  # cryptographically random
      r.setex(
          f"session:{session_id}",
          3600,  # 1 hour TTL
          json.dumps(user_data)
      )
      return session_id
  
  def get_session(session_id: str) -> dict | None:
      data = r.get(f"session:{session_id}")
      return json.loads(data) if data else None
```

---

## 7. Auto-Scaling

Auto-scaling automatically adjusts server count based on current demand.

### 7.1 Reactive Auto-Scaling

Reactive (metric-based) auto-scaling monitors metrics and adds/removes servers when thresholds are crossed.

```
Scale-Out Policy (add servers):
  Trigger: CPU utilization > 70% for 2 minutes
  Action: Add 2 servers
  Cooldown: Wait 5 minutes before evaluating again (prevent thrashing)

Scale-In Policy (remove servers):
  Trigger: CPU utilization < 30% for 10 minutes  
  Action: Remove 1 server
  Cooldown: Wait 10 minutes (be conservative when scaling in)
  Minimum: Never go below 2 servers (availability requirement)

Common metrics to scale on:
  - CPU utilization: Good for compute-bound workloads
  - Request count: Good for web APIs
  - Memory utilization: Good for memory-intensive workloads
  - Custom metrics: Queue depth (scale based on Kafka lag), error rate
```

**The Cooldown Period Problem**:
```
Without cooldown:
  CPU > 70% -> add server -> CPU drops -> below 30% -> remove server -> CPU spikes -> add server...
  (Thrashing: servers being added and removed every few minutes)

With cooldown:
  CPU > 70% -> add server -> wait 5 minutes -> measure again -> if still high, add more
  CPU < 30% -> wait 10 minutes -> measure again -> if still low, remove one

Scale-out cooldowns should be SHORT (2-5 min) to respond to spikes quickly
Scale-in cooldowns should be LONG (10-30 min) to avoid premature removal
```

### 7.2 Predictive Auto-Scaling

AWS and other cloud providers offer ML-based predictive scaling that analyzes historical traffic
patterns to proactively add servers BEFORE traffic spikes.

```
Predictive Scaling Example:
  Observation: Every weekday at 9am, traffic increases 3x for 2 hours
  Prediction: Tomorrow at 8:45am, pre-provision 3x servers
  Actual spike: Servers are ready before the spike -- no latency degradation!

Traditional reactive:
  9:00am: Traffic spikes
  9:02am: CPU > 70% triggers scale-out
  9:07am: New servers are provisioned and healthy (5-7 min launch time)
  9:02am - 9:07am: Users experience degraded performance
  
Predictive:
  8:45am: Servers pre-provisioned based on historical pattern
  9:00am: Traffic spikes -> servers already ready
  9:00am - onwards: No degradation
```

### 7.3 Scale-Out vs Scale-In Asymmetry

**ALWAYS be aggressive about scaling out, conservative about scaling in**:
- The cost of under-provisioning (user-facing degradation, potential outages) is much higher
  than the cost of over-provisioning (a few extra servers at $0.10-1.00/hour)
- Scale out fast, scale in slow

---

## 8. Geographic Distribution

### 8.1 Why Geography Matters

```
Physics of latency:
  Speed of light in fiber: ~200,000 km/second
  
  US to US East Coast:          <5ms RTT (negligible)
  US West to US East Coast:     ~80ms RTT
  US East to UK:                ~80-100ms RTT
  US East to Singapore:         ~200-300ms RTT
  
  For a user in Singapore accessing a US server:
    DNS: 100ms (uncached)
    TCP handshake: 300ms
    TLS handshake: 300ms
    HTTP request: 300ms
    Total: ~1 second before they see anything!
    
  The SAME user accessing a Singapore-hosted server:
    DNS: ~20ms
    TCP handshake: ~5ms
    TLS handshake: ~5ms
    HTTP request: ~5ms
    Total: ~35ms -- 28x faster!
```

### 8.2 CDN (Content Delivery Network)

CDNs are networks of servers (Points of Presence, PoPs) distributed globally.
Static content is cached at the nearest PoP to the user.

```
CDN Architecture:

     [Origin Server] (US East)
           |
     [CDN Network]
    /      |      \
[US PoPs] [EU PoPs] [Asia PoPs]
  |            |           |
[US Users]  [EU Users] [Asia Users]

How it works:
  1. User in Singapore requests https://example.com/logo.png
  2. DNS returns IP of nearest CDN PoP (Singapore)
  3. CDN PoP checks its cache: HIT? Serve from cache (5ms)
  4. Cache MISS? CDN PoP fetches from origin (200ms), caches it, serves user
  5. Next Singapore user gets it in 5ms (cache hit)

Cache-Control headers control CDN behavior:
  Cache-Control: max-age=86400, public        -- Cache for 1 day
  Cache-Control: no-cache                     -- Always revalidate with origin
  Cache-Control: private                      -- Don't cache (user-specific data)
  Cache-Control: immutable                    -- Never revalidate (for hashed assets)
```

### 8.3 Multi-Region Active-Passive

One region is "active" (serves all traffic), another is "passive" (warm standby, ready to take over).

```
Normal operation:
  All user traffic -> US East (primary)
  Data continuously replicated to US West (standby)

Failover:
  US East experiences outage
  Route 53 (DNS) detects health check failure
  Route 53 switches DNS to point to US West
  US West starts serving traffic (within minutes)
  
Recovery time:
  DNS TTL: 60 seconds (must be low for fast failover)
  Health check detection: 30-60 seconds
  DNS propagation: 60 seconds (with low TTL)
  Server warm-up: 60 seconds
  Total: 3-4 minutes of degraded service

Used for: 99.99% availability requirements
```

### 8.4 Multi-Region Active-Active

Multiple regions simultaneously serve traffic. Users are routed to nearest region.

```
Active-Active Architecture:

[US Users]  -> [US East Region]  -> [US East DB]
                    |                     |
                    | Cross-region        | DB replication
                    | sync                |
[EU Users]  -> [EU West Region]  -> [EU West DB]
                    |                     |
[Asia Users] -> [Asia Region]   -> [Asia DB]

Benefits:
  - Each user served by geographically nearest region (<50ms for most users)
  - No single region failure takes down service
  - Higher throughput (each region handles its local users)

Challenges:
  - Data consistency: If US user updates their profile and EU user reads it immediately...
    has the update replicated yet?
  - Conflict resolution: Two users update the same record in different regions simultaneously
  - Cross-region transactions: Paying someone in a different region requires coordination

Used for: 99.999% availability, global consumer products
Examples: AWS Global Accelerator, Google Cloud's Spanner (globally consistent), Cloudflare
```

---

## Summary

```
Scalability Decision Tree:

Is your app stateless?
  NO -> Externalize state to Redis/DB first, THEN scale horizontally
  YES -> Proceed to horizontal scaling

What's your traffic pattern?
  Bursty (events, marketing) -> Auto-scaling with predictive component
  Steady growth -> Scheduled scaling + reactive auto-scaling
  Geographic -> Multi-region with CDN

What's your availability requirement?
  99.9% -> Multi-AZ, single region, auto-failover
  99.99% -> Multi-region active-passive + CDN
  99.999% -> Multi-region active-active + global load balancing

Load balancing algorithm:
  Homogeneous servers, HTTP -> Round Robin
  Heterogeneous servers -> Weighted Round Robin
  Mixed request costs -> Least Connections
  Distributed caching/sharding -> Consistent Hashing

The "golden path" for most modern web services:
  Stateless app servers + Redis for sessions + Postgres for data + CDN for static assets
  + Auto-scaling group + L7 load balancer + Multi-AZ
```
