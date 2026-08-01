# Module 1: Foundations of System Design

> **Goal**: Understand the bedrock concepts that underpin every system design decision.
> Before you can design scalable systems, you must deeply understand how the internet works,
> what latency really means, and how to reason about scale mathematically.

---

## Table of Contents

1. [How the Internet Actually Works](#1-how-the-internet-actually-works)
2. [Latency Numbers Every Engineer Must Know](#2-latency-numbers-every-engineer-must-know)
3. [Throughput vs Latency Trade-offs](#3-throughput-vs-latency-trade-offs)
4. [Availability: The Nines Explained](#4-availability-the-nines-explained)
5. [SLO, SLA, SLI](#5-slo-sla-sli)
6. [Back-of-Envelope Estimation](#6-back-of-envelope-estimation)
7. [CAP Theorem Introduction](#7-cap-theorem-introduction)
8. [System Design Interview Framework RADIO](#8-system-design-interview-framework-radio)

---

## 1. How the Internet Actually Works

Understanding the internet end-to-end is foundational. When you type `https://www.google.com` into a browser,
dozens of things happen before you see the page. Each step has latency implications that compound.

### 1.1 DNS Resolution - Step by Step

DNS (Domain Name System) is the internet's phone book. Computers communicate via IP addresses (e.g., `142.250.80.46`),
but humans use domain names. DNS translates between them.

```
USER types: https://www.google.com

Step 1: Browser Cache Check
  Browser checks its own DNS cache (takes microseconds)
  TTL (Time To Live) determines how long the cache is valid
  Chrome: chrome://net-internals/#dns

Step 2: OS Cache Check
  If not in browser cache, OS checks its resolver cache
  Also checks /etc/hosts (C:\Windows\System32\drivers\etc\hosts on Windows)

Step 3: Recursive Resolver Query
  OS contacts configured DNS resolver (usually ISP's or 8.8.8.8 Google DNS)
  This resolver is called a "recursive resolver" or "recursive nameserver"
  If resolver has the answer cached: returns immediately
  If not: begins the recursive resolution process

Step 4: Root Nameserver Query
  Recursive resolver asks a Root Nameserver: "Who handles .com?"
  There are 13 root nameserver IP addresses (a.root-servers.net through m.root-servers.net)
  Root servers don't store domain info -- they store WHERE to find TLD servers
  Returns: "Go ask the .com TLD nameserver at 192.5.6.30"

Step 5: TLD Nameserver Query
  Recursive resolver asks the .com TLD server: "Who handles google.com?"
  TLD servers know which nameservers are authoritative for each domain
  Returns: "Go ask Google's nameservers at ns1.google.com"

Step 6: Authoritative Nameserver Query
  Recursive resolver asks Google's authoritative nameserver:
    "What is the IP address for www.google.com?"
  Returns: "142.250.80.46" with a TTL of 300 seconds
  This answer is cached by the recursive resolver for 300 seconds

Step 7: Response to Client
  Recursive resolver returns 142.250.80.46 to the OS
  OS returns it to the browser, browser caches it
  Total DNS resolution time: 20-120ms (uncached), less than 1ms (cached)
```

**Why DNS Matters for System Design**:
- DNS is often the first bottleneck in a system. TTL too high means slow propagation; too low hammers DNS servers.
- DNS can be used for **load balancing** (returning different IPs in round-robin fashion)
- DNS can be used for **geographic routing** (returning nearest server IP based on requester location)
- DNS failures can take down entire systems -- always have multiple nameservers configured
- **DNS TTL strategy**: Use high TTLs (3600s+) in normal operation. Lower to 60s BEFORE making changes.

```
DNS Resolution Tree (ASCII Diagram):

                       [Browser/OS]
                            |
                    [Recursive Resolver]
                    (ISP or 8.8.8.8)
                   /         |         \
           [Root Servers] [TLD Servers] [Auth Nameservers]
           (13 globally)  (.com, .org)  (ns1.google.com)
           "Ask TLD"      "Ask Auth NS"  "Here's the IP"
```

### 1.2 TCP Three-Way Handshake

Before any HTTP data can be exchanged, a TCP connection must be established. TCP provides:
- **Reliability**: Every packet is acknowledged; lost packets are retransmitted
- **Ordering**: Packets arrive in order (sequence numbers)
- **Flow control**: Prevents overwhelming the receiver (window sizes)
- **Congestion control**: Prevents overwhelming the network (slow start, AIMD)

```
CLIENT                              SERVER
  |                                   |
  |------ SYN (seq=x) --------------> |  Step 1: "I want to connect"
  |                                   |  Client picks a random sequence number x
  |                                   |
  |<----- SYN-ACK (seq=y, ack=x+1) --|  Step 2: "OK, I'm ready"
  |                                   |  Server picks its own sequence number y
  |                                   |  Server acknowledges client sequence (x+1)
  |                                   |
  |------ ACK (ack=y+1) ------------> |  Step 3: "Acknowledged"
  |                                   |  Client acknowledges server sequence
  |                                   |
  |====== DATA TRANSFER BEGINS ====== |  Now actual HTTP data can flow
```

**Why This Matters for System Design**:
- Each TCP handshake adds **1.0 RTT** before data transfer begins (the client piggybacks its HTTP GET on the ACK packet, so data flows after SYN → SYN-ACK → ACK+GET — exactly 1 full round-trip)
- For a user in New York connecting to London (~100ms RTT):
  - TCP handshake alone costs 150ms
  - TLS handshake costs another 150-300ms (1-2 RTTs)
  - Then the actual HTTP request/response
  - Total: 400-600ms before the user sees anything
- **HTTP Keep-Alive**: Reuses existing TCP connections, avoiding repeated handshakes
- **HTTP/2 Multiplexing**: Multiple requests over a single TCP connection simultaneously
- **HTTP/3 (QUIC)**: Built on UDP with 0-RTT connection establishment for known servers
- **Connection Pooling**: Servers maintain pools of pre-established connections to databases

### 1.3 TLS/SSL Handshake

For HTTPS, an additional handshake occurs after TCP:

```
CLIENT                              SERVER
  |  [TCP Handshake complete]         |
  |                                   |
  |--- ClientHello -----------------> |  TLS version, supported ciphers, random nonce
  |<-- ServerHello + Certificate ---  |  Chosen cipher, server's certificate (public key)
  |--- ClientKeyExchange ------------> |  Session keys derived (with server's public key)
  |<-- Finished ----------------------|  Both sides confirm, session begins
  |                                   |
  |====== ENCRYPTED HTTP BEGINS ====  |
```

TLS 1.3 (modern standard) reduced this to 1 RTT (and supports 0-RTT for session resumption).
This is why upgrading TLS versions matters for performance.

### 1.4 HTTP Request Lifecycle

After TCP + TLS setup, the actual HTTP request:

```
CLIENT sends:
  GET /search?q=hello HTTP/1.1
  Host: www.google.com
  Accept: text/html
  Accept-Encoding: gzip, deflate, br
  Cookie: session=abc123
  User-Agent: Mozilla/5.0...

SERVER processes:
  1. Parse HTTP headers
  2. Route to appropriate handler (URL routing)
  3. Check authentication/session validity
  4. Execute business logic (query DB, call microservices)
  5. Serialize response to JSON/HTML
  6. Set appropriate response headers

SERVER sends:
  HTTP/1.1 200 OK
  Content-Type: text/html; charset=UTF-8
  Content-Encoding: gzip
  Cache-Control: max-age=300
  Set-Cookie: session=abc123; HttpOnly; Secure; SameSite=Strict

  <html>...</html>
```

**Key HTTP Status Codes Every Engineer Must Know**:

```
2xx Success:
  200 OK           - Request succeeded
  201 Created      - Resource created (POST)
  204 No Content   - Success with no body (DELETE)

3xx Redirection:
  301 Moved Permanently  - SEO-safe redirect (cached by browsers forever)
  302 Found              - Temporary redirect (not cached)
  304 Not Modified       - Client's cached version is still valid (saves bandwidth)

4xx Client Errors:
  400 Bad Request        - Invalid request syntax or parameters
  401 Unauthorized       - Authentication required
  403 Forbidden          - Authenticated but not authorized
  404 Not Found          - Resource doesn't exist
  429 Too Many Requests  - Rate limited

5xx Server Errors:
  500 Internal Server Error  - Generic server-side error
  502 Bad Gateway            - Proxy got invalid response from upstream
  503 Service Unavailable    - Server overloaded or in maintenance
  504 Gateway Timeout        - Proxy timeout waiting for upstream response
```

---

## 2. Latency Numbers Every Engineer Must Know

These numbers, originally compiled by Jeff Dean at Google, give you intuition for how long operations take.
Without this intuition, you cannot make good system design trade-off decisions.

```
Operation                              Latency        Intuition (if 1ns = 1 second)
------------------------------------------------------------------------------------
L1 cache reference                     0.5 ns         1 second
Branch misprediction                   5   ns         10 seconds
L2 cache reference                     7   ns         14 seconds
Mutex lock/unlock                      25  ns         50 seconds
Main memory reference (RAM)            100 ns         3.5 minutes
Compress 1KB with Snappy               3   us         3.5 hours
Read 1MB sequentially from memory      250 us         10 days
SSD random read (NVMe)                 16  us         16 hours
Read 1MB sequentially from SSD         1   ms         1 month
Round trip within same datacenter      500 us         6 days
HDD seek time                          10  ms         1 year
Read 1MB sequentially from HDD         20  ms         2 years
Send packet CA to Netherlands and back 150 ms         15 years
```

### 2.1 Intuition for Each Level

**CPU Caches (L1: 0.5ns, L2: 7ns)**:
- L1 cache is part of the CPU core itself -- tiny (32-64KB) but blazingly fast
- L2 is larger (256KB-1MB) but slightly further from execution unit
- **Implication**: Algorithms that maximize cache locality (process data sequentially) are 10x faster
  than those with random access patterns. This is why columnar databases outperform row-based DBs
  for analytics (scan one column in L1/L2, skip others entirely).

**RAM (100ns)**:
- 200x slower than L1 cache
- At scale (millions of requests/sec), RAM access patterns dominate
- **Implication**: Keep hot data in memory (Redis, Memcached). 
  A 100GB Redis cluster serving 100,000 req/sec is often faster than a 1TB SSD database.

**SSD (16us random read)**:
- Modern NVMe SSDs are dramatically faster than spinning disks
- But still 160x slower than RAM for random reads
- Sequential reads are much faster (several GB/s)
- **Implication**: Use SSDs for databases where possible. Design schemas to minimize random I/O
  (this is why database indexing matters so much -- it converts random scans to targeted reads).

**HDD (10ms seek)**:
- Seek time is purely mechanical -- the arm physically moves to the track
- 20,000x slower than RAM for random access
- Sequential reads are OK (100-200MB/s)
- **Implication**: Avoid random disk I/O. Kafka's secret weapon is append-only sequential writes.
  If you must use HDDs, batch writes and sort reads.

**Network RTT within datacenter (500us)**:
- A microservice call to another service in the same DC costs at minimum 500us
- If your request makes 10 such calls sequentially: 5ms added latency just from network
- **Implication**: Be careful with "chatty" microservices. Batch where possible. 
  Use async for non-critical paths. Avoid N+1 patterns in service-to-service calls.

**Cross-continental network (150ms)**:
- US to Europe: ~80ms. US to Asia: ~120-150ms. This is the speed of light in fiber.
- You literally cannot engineer around physics
- **Implication**: Content must be geographically close to users. Use CDNs.
  Deploy in multiple regions. Use latency-based DNS routing.

### 2.2 The 10x Rules of Thumb

```
L1 to L2 cache:       ~14x slower
L2 to RAM:            ~14x slower
RAM to SSD:           ~160x slower (random read)
SSD to HDD:           ~600x slower (random read)
Local to DC Network:  ~5,000x slower than RAM
Cross-continent:      ~1,500,000x slower than RAM
```

### 2.3 Why Percentile Latency Matters More Than Averages

This is one of the most common mistakes in production systems -- reporting average latency.

```
Request latencies for 10 requests:
  [10ms, 12ms, 11ms, 13ms, 10ms, 11ms, 12ms, 11ms, 500ms, 10ms]

Average: (10+12+11+13+10+11+12+11+500+10) / 10 = 60ms

But most users experience 11ms! One slow request (500ms) makes average misleading.

Percentiles tell the real story:
  p50 (median): 11ms    -- 50% of users wait 11ms or less
  p90:          13ms    -- 90% of users wait 13ms or less
  p95:          13ms    -- 95% of users wait 13ms or less
  p99:          500ms   -- 99th percentile is 500ms (1 in 100 users)
  p999:         500ms   -- (only 10 samples, same result)

At Google scale (1 million req/sec):
  p99 = 500ms means 10,000 users/second have a bad experience
  p999 = 5s means 1,000 users/second see timeouts

SLOs MUST be defined using percentiles, never averages.
Example SLO: "p99 latency < 200ms measured over 5-minute windows"
```

---

## 3. Throughput vs Latency Trade-offs

These metrics are often confused or conflated. They are fundamentally different and frequently in tension.

### 3.1 Precise Definitions

**Latency**: The time it takes to complete ONE operation.
- Measured in: milliseconds, microseconds, nanoseconds
- "How long does a single car take to drive from A to B?"
- Measured as percentiles: p50, p95, p99, p999

**Throughput**: The number of operations completed per unit of time.
- Measured in: requests/second, bytes/second, transactions/second
- "How many cars can drive from A to B in one hour?"
- Affected by: parallelism, batching, pipeline efficiency

### 3.2 Why They Are in Tension

```
Scenario: Web server processing database queries

HIGH THROUGHPUT STRATEGY (Batching):
  - Collect 100 incoming queries
  - Send them all to the DB in one batch request
  - DB processes all 100 in the time it would process 10 individually
  - Throughput: 10x better
  - Latency: WORSE -- the first query in the batch must wait for 99 others to arrive
    If queries arrive at 100/sec, that 100th query waits almost 1 second!

LOW LATENCY STRATEGY (Immediate dispatch):
  - Send each query to DB immediately upon receipt
  - Each query gets processed as fast as possible
  - Latency: Minimum possible (no waiting)
  - Throughput: Capped by the overhead of each round trip

This same tension appears in:
  - Kafka: larger batches = higher throughput, higher latency
  - GPU computation: more parallel threads = higher throughput
  - Database write coalescing: batch commits = higher throughput, higher latency
  - CDN edge caching: longer cache TTL = better throughput, potential staleness
```

### 3.3 Little's Law -- The Mathematical Foundation

Little's Law connects throughput, latency, and concurrency. It is universally applicable
to any queuing system (web servers, databases, call centers, traffic junctions):

```
L = lambda * W

Where:
  L      = Average number of requests in the system at any given time
  lambda = Throughput (arrival/processing rate in requests/second)
  W      = Average time spent in the system per request (latency in seconds)

Example 1: Normal operating conditions
  System handles 1,000 req/s (lambda = 1000)
  Average response time is 50ms (W = 0.05 seconds)
  Average in-flight requests: L = 1000 * 0.05 = 50 requests

Example 2: Latency spike
  Same system, but DB slowdown causes avg response time to spike to 500ms
  New L = 1000 * 0.5 = 500 requests in-flight!
  If each request holds a thread, you need 10x more threads (or requests queue up)
  This is why latency spikes cause cascading failures -- queues fill up rapidly

Example 3: Capacity planning
  If you want to support 10,000 req/s with p99 < 100ms:
  L = 10,000 * 0.1 = 1,000 concurrent requests in the system
  Each request uses X memory -- multiply by 1,000 to get total memory requirement
```

### 3.4 The Latency-Throughput Curve

```
Throughput
    ^
    |          ***
    |       ***
    |     **
    |    *
    |   *
    |  *
    | *
    |*
    +-----------------------> Offered Load (requests arriving)

At low load: throughput scales linearly with offered load, latency stays flat
At saturation point: throughput plateaus, latency explodes
Beyond saturation: system collapses (USL -- Universal Scalability Law)

Practical implication:
  Never run your system at more than 70% of peak capacity
  The latency curve becomes dangerously steep above 70-80% utilization
```

---

## 4. Availability: The Nines Explained

Availability is one of the most critical non-functional requirements.
It is expressed as a percentage of time a system is operational and serving requests correctly.

### 4.1 The Nines Table

```
Availability    Downtime/Year    Downtime/Month   Downtime/Week    Downtime/Day
-------------------------------------------------------------------------------
90%             36.5 days        72 hours         16.8 hours       2.4 hours
95%             18.25 days       36 hours         8.4 hours        1.2 hours
99%             3.65 days        7.2 hours        1.68 hours       14.4 min
99.5%           1.83 days        3.6 hours        50.4 min         7.2 min
99.9%           8.76 hours       43.8 min         10.1 min         1.44 min
99.95%          4.38 hours       21.9 min         5.04 min         43.2 sec
99.99%          52.6 minutes     4.38 min         1.01 min         8.64 sec
99.999%         5.26 minutes     26.3 sec         6.05 sec         864 ms
99.9999%        31.5 seconds     2.63 sec         605 ms           86.4 ms
```

### 4.2 What These Mean in Business Terms

**99% (Two Nines)**:
- 3.65 DAYS of downtime per year
- Completely unacceptable for customer-facing services
- Acceptable only for internal batch jobs running nightly

**99.9% (Three Nines)**:
- 8.76 HOURS per year -- about 43 minutes per month
- Minimum acceptable for most SaaS B2B products
- Allows one major incident per year
- Most startups and small companies operate at this level
- Example SLA: GitHub has been at this level historically

**99.99% (Four Nines)**:
- 52 MINUTES per year -- less than 5 minutes per month
- Required for: payment systems, healthcare platforms, financial trading
- Requires: multi-AZ deployment, automated failover, zero-downtime deployments
- Example SLAs: AWS EC2, Stripe API, Twilio

**99.999% (Five Nines)**:
- 5 MINUTES per year -- 26 seconds per month
- The gold standard for telecommunications (phone systems)
- Extremely expensive to achieve and maintain
- Requires: multi-region active-active, automated failover in seconds,
  canary deployments, extensive chaos engineering
- Any planned maintenance requires live migration with zero downtime

### 4.3 How Availability Compounds (Series Components)

When ALL components must be working for the system to work (series):

```
Availability_system = A1 * A2 * A3 * ... * An

Example: 3-tier web application
  Load Balancer:  99.99% = 0.9999
  App Server:     99.9%  = 0.999
  Database:       99.9%  = 0.999

Combined: 0.9999 * 0.999 * 0.999 = 0.9979 = 99.79%

This is WORSE than any individual component!
A system of three 99.9% components gives you 99.7% -- worse than each part alone.
This is why you need redundancy at every layer.
```

With redundancy (parallel components -- only ONE needs to work):

```
Availability_parallel = 1 - (1 - A)^N

One app server at 99.9%:
  Availability = 99.9%

Two app servers, each 99.9% (N=2):
  = 1 - (1 - 0.999)^2
  = 1 - (0.001)^2
  = 1 - 0.000001
  = 99.9999%

Three app servers, each 99.9% (N=3):
  = 1 - (0.001)^3
  = 1 - 0.000000001
  = 99.9999999%

Adding redundancy gives you dramatic availability improvements at relatively low cost.
```

### 4.4 Cost of High Availability

The cost curve for each additional nine is exponential:

```
Availability    Typical Architecture                    Cost Multiplier
-----------------------------------------------------------------------
99%             Single server, manual recovery          1x (baseline)
99.9%           2+ servers, multi-AZ, auto-failover     2-3x
99.99%          Multi-region active-passive, hot standby 5-10x
99.999%         Multi-region active-active, zero-downtime deploy 10-30x
```

**Key Insight**: Know your actual requirement before over-engineering.
A startup blog does NOT need five nines. A payment processor might.
Every additional nine requires massive investment in:
- Redundant infrastructure
- Sophisticated monitoring and alerting
- Chaos engineering and game days
- Incident response processes and runbooks
- 24/7 on-call rotations

---

## 5. SLO, SLA, SLI

These three terms are frequently confused. They have precise definitions in the
Google SRE (Site Reliability Engineering) world.

### 5.1 SLI (Service Level Indicator) -- The Measurement

**Definition**: A quantitative measure of some aspect of the service's behavior.
An SLI is JUST a measurement -- a fact, not a target.

```
SLI = (Number of "good" events) / (Total events) * 100%

Types of SLIs:
  Availability SLI:
    (Minutes with successful health check) / (Total minutes) * 100%

  Request Success Rate SLI:
    (Requests returning HTTP 200-299) / (Total requests) * 100%

  Latency SLI:
    (Requests completing within 200ms) / (Total requests) * 100%

  Error Rate SLI:
    (Requests returning HTTP 5xx) / (Total requests) * 100%
    (Lower is better, can be inverted)

  Durability SLI (for storage):
    (Objects successfully stored and retrievable) / (Total objects written) * 100%

  Freshness SLI (for data pipelines):
    (Data processed within 5 minutes of arrival) / (Total data events) * 100%
```

### 5.2 SLO (Service Level Objective) -- The Internal Target

**Definition**: A target range for an SLI. This is the internal agreement within an engineering team
about what "acceptable service quality" looks like. SLOs drive engineering decisions.

```
SLO Examples:
  "99.9% of requests return a successful response (200-299)"
  "p99 latency < 500ms, measured over a rolling 28-day window"
  "99.95% availability per calendar month"
  "99.9999999% durability (eleven nines) for stored objects"

The Error Budget -- The Key Innovation of SLOs:

  If SLO = 99.9% availability over 30 days:
  Error budget = 100% - 99.9% = 0.1% of 30 days
              = 0.001 * 30 * 24 * 60 = 43.2 minutes

  This means engineering teams can have UP TO 43.2 minutes of downtime before they
  are in danger of violating their SLO.

Error Budget Usage:
  - Used 5 minutes this month: Great, budget is healthy. Safe to deploy risky features.
  - Used 40 minutes this month: Only 3.2 minutes left. FREEZE deployments. Focus on reliability.
  - Used 43+ minutes: SLO violated. All hands on deck for reliability work.

This creates a mathematical, non-political way to answer:
  "Should we ship this risky feature or focus on reliability?" 
  Answer: Check your error budget.
```

### 5.3 SLA (Service Level Agreement) -- The External Contract

**Definition**: A LEGAL commitment to customers about service quality, typically with financial
penalties (service credits, refunds) if violated.

```
Real SLA Examples:

AWS EC2 SLA (2024):
  Monthly Uptime < 99.99%: 10% service credit of that month's bill
  Monthly Uptime < 99.0%:  30% service credit
  Monthly Uptime < 95.0%:  100% service credit

Google Cloud Compute Engine SLA:
  Monthly Uptime < 99.99%: 25% service credit
  Monthly Uptime < 99.0%:  50% service credit

Stripe API SLA:
  API availability >= 99.99%
  Violations result in service credits

Key Principle: SLOs (internal) should be TIGHTER than SLAs (external).
  If SLA is 99.9%, your SLO should be 99.95%
  This 0.05% gap is your "safety buffer"
  It prevents minor internal incidents from cascading into SLA violations
  which would require payouts and damage customer relationships
```

### 5.4 A Complete Example: Payment API

```
Company: FinPay Inc. (payment processing)

SLI:
  Measurement: % of payment API calls (POST /payments) that:
    (a) Return HTTP 200 or 201
    (b) Complete within 2 seconds
  Formula: (payments_processed_within_2s) / (total_payment_attempts) * 100

SLO (Internal, Engineering Team Objective):
  Target: 99.95% of payments processed successfully within 2 seconds
  Window: Rolling 28-day window
  Error Budget: 0.05% of 28 days = 0.0005 * 28 * 24 * 60 = 20.16 minutes/month

SLA (External, Customer Contract):
  Guarantee: 99.9% payment processing availability
  Penalties:
    99.0% - 99.9%: Customer receives 10% of monthly bill as credit
    Below 99.0%:   Customer receives 30% credit + can terminate contract
    Below 95.0%:   Customer receives 100% credit + penalty payment

Buffer Analysis:
  SLO: 99.95%, SLA: 99.9%
  Buffer: 0.05% additional downtime allowed before SLA violation
  Buffer time: 0.0005 * 28 * 24 * 60 = 20.16 additional minutes
  
  This gives the team time to detect, respond to, and fix incidents
  before customers are entitled to credits.
```

---

## 6. Back-of-Envelope Estimation

This is arguably the most important practical skill in system design. The goal is not
perfect precision -- it is order-of-magnitude correctness to drive architectural decisions.

A factor of 2-3x off is acceptable. A factor of 10-100x off leads to catastrophically
wrong architecture choices.

### 6.1 The Essential Reference Numbers

```
DATA SIZE REFERENCE:
  ASCII character:           1 byte
  Unicode character (UTF-8): 1-4 bytes (1 byte for ASCII range)
  Boolean (in DB):           1 byte
  Integer (int32):           4 bytes
  Long integer (int64):      8 bytes
  Float/Double:              4 or 8 bytes
  UUID (stored as text):     36 bytes
  UUID (stored as binary):   16 bytes
  Timestamp:                 8 bytes
  Short URL code (6 chars):  6 bytes
  URL (average):             ~100 bytes
  Email address:             ~50 bytes
  Tweet text (max):          ~280 bytes
  User profile record:       ~500 bytes - 2 KB
  Average JSON API response: ~1-10 KB
  Small thumbnail image:     ~5-10 KB
  Web page (HTML only):      ~50-100 KB
  Typical webpage (all assets): ~2-5 MB
  Instagram photo (compressed): ~100-500 KB
  Instagram photo (original):   ~3-5 MB
  1-minute audio (MP3):         ~1 MB
  1-minute 720p video:          ~50-150 MB
  2-hour HD movie:              ~4-8 GB

TIME REFERENCE:
  1 minute    = 60 seconds
  1 hour      = 3,600 seconds
  1 day       = 86,400 seconds (~10^5)
  1 month     = 2,592,000 seconds (~2.6 * 10^6)
  1 year      = 31,536,000 seconds (~3.15 * 10^7)

THROUGHPUT REFERENCE:
  Fast SSD sequential read:   2-7 GB/s
  SSD random 4KB reads:       ~100,000 IOPS (400 MB/s)
  HDD sequential read:        100-200 MB/s
  HDD random reads:           ~100-200 IOPS (worst case)
  Datacenter network (1GbE):  125 MB/s = 1 Gbps
  Datacenter network (10GbE): 1,250 MB/s = 10 Gbps
  Home broadband (download):  ~50-200 Mbps = 6-25 MB/s

REAL PLATFORM SCALE (for sanity checking your estimates):
  Active internet users:      5 billion
  Google searches/day:        8.5 billion
  Twitter posts/day:          500 million
  YouTube hours watched/day:  1 billion
  YouTube videos uploaded/min: 500 hours of video
  WhatsApp messages/day:      100 billion
  Instagram photos uploaded/day: 100 million
  Uber rides/day:             19 million
  Amazon orders/day:          ~28 million
```

### 6.2 The Estimation Framework

```
Step 1: Clarify the Scope
  - How many users total? Daily Active Users (DAU)? Monthly Active Users (MAU)?
  - Is this read-heavy or write-heavy? (typical social apps: 100:1 read:write ratio)
  - What is the data retention period?
  - What geographic regions?

Step 2: Estimate QPS (Queries Per Second)
  DAU * (actions per user per day) / 86,400 seconds = average QPS
  Average QPS * peak_multiplier = peak QPS
  Typical peak multipliers: 2x for steady services, 5-10x for event-driven services

Step 3: Estimate Storage
  Records per day * record size = daily storage growth
  Daily growth * days_retained = total raw storage
  Raw storage * replication_factor = total physical storage
  Add 20-30% for indexes and metadata overhead

Step 4: Estimate Bandwidth (Network)
  Incoming bandwidth = write_QPS * average_write_payload_size
  Outgoing bandwidth = read_QPS * average_read_response_size
  Convert to Mbps: bytes/sec * 8 = bits/sec

Step 5: Sanity Check
  Compare your estimate to public data about similar systems
  If your estimate says "10x more than Twitter", reconsider your assumptions
```

### 6.3 Worked Example: Instagram Photo Storage

**Problem**: Estimate the storage Instagram needs after 5 years.

```
Step 1: Assumptions (state these explicitly!)
  Daily Active Users (DAU): 500 million
  % of DAU who upload photos: 10% (conservative -- most users are consumers)
  Posters per day: 50 million
  Photos per posting user per day: 2
  Total photos per day: 100 million
  Average photo size (after Instagram compression): 3 MB
  Multiple resolutions stored per photo: 4 (thumbnail, small, medium, original)
    Thumbnail (100px x 100px): ~10 KB
    Small (480px): ~100 KB
    Medium (720px): ~300 KB
    Original (max 1080px): ~3 MB
    Total per photo: ~3.41 MB (dominated by original)
  Replication factor: 3x (stored in 3 different datacenters for durability)
  Retention: Forever (users' photos never deleted unless they delete them)

Step 2: Write QPS
  Photos uploaded/day: 100 million
  Photos per second (average): 100M / 86,400 = 1,157 photos/sec ~= 1,200/sec
  Peak write QPS (2x multiplier, evening peak): 2,400 photos/sec

Step 3: Daily Storage (Raw)
  100M photos * 3.41 MB/photo = 341 TB of raw photo data per day
  With replication (3x): 341 TB * 3 = ~1 PB per day

Step 4: 5-Year Total Storage
  1 PB/day * 365 days/year * 5 years = 1,825 PB = 1.825 EB (exabytes)

Step 5: Metadata Storage (often overlooked!)
  100M photos/day * metadata per photo (~2 KB: user_id, timestamp, location, etc.)
  = 200 GB/day of metadata
  5 years: 200 GB * 365 * 5 = ~365 TB of metadata
  Relatively small compared to photo data

Final Answer:
  Photo storage: ~2 EB over 5 years
  Metadata (in DB): ~400 TB over 5 years
  Write QPS: ~1,200/sec average, ~2,400/sec peak
  Read QPS: Much higher (estimated 10:1 ratio = 12,000-24,000/sec for photos)
```

### 6.4 Worked Example: Twitter/X QPS Estimation

**Problem**: Estimate the peak QPS for Twitter's timeline read and tweet write operations.

```
Step 1: Assumptions
  Monthly Active Users (MAU): 350 million
  Daily Active Users (DAU): 40% of MAU = 140 million
  Sessions per user per day: 5 (open app, scroll, close, repeat)
  Timeline loads per session: 3 (open, pull to refresh, scroll to load more)
  Tweets per page (per load): 20
  % of DAU who tweet: 30%
  Tweets per tweeting user: 1
  Total tweet writes per day: 140M * 0.3 * 1 = 42 million
    (Twitter reported 500M tweets/day in 2022 -- our estimate is conservative)

Step 2: Read QPS
  Timeline reads per day: 140M * 5 sessions * 3 loads = 2.1 billion reads/day
  Average read QPS: 2.1B / 86,400 = ~24,300 reads/sec
  Peak read QPS (assume 3x multiplier for evening/event peaks): ~75,000 reads/sec

Step 3: Write QPS
  Using Twitter's own data: 500 million tweets/day
  Average write QPS: 500M / 86,400 = ~5,787 writes/sec
  Peak write QPS (3x): ~17,000 writes/sec

Step 4: The Fan-Out Problem (the real challenge)
  Most users have <1,000 followers: timeline delivery = 1 write per follower
  For a user with 500 followers: tweet = 500 additional writes to follower timelines
  For @BarackObama with 130M followers: ONE tweet = 130M write operations!
  
  This is the key insight: simple QPS math misses the amplification factor.
  
  Solutions:
    Push model (precompute timelines): Works for regular users, breaks for celebrities
    Pull model (compute at read time): Works for celebrities, too slow for everyone
    Hybrid: Push for regular users, pull for celebrities (>1M followers)
    
    This is exactly what Twitter uses in production.

Step 5: Storage
  Tweets: 500M/day * 300 bytes (tweet text + metadata) = 150 GB/day of raw tweet text
    5 years: 150 GB * 365 * 5 = ~274 TB of tweet text
  Images/Videos: Much larger, 10-100x the text storage
  User graph (follower/following): 350M users * avg 500 connections * 8 bytes = ~1.4 TB

Final Answer:
  Read QPS: ~75,000/sec peak (timeline loads)
  Write QPS: ~17,000/sec peak (tweets)
  Fan-out amplification: up to 130M additional writes per celebrity tweet
  Text storage: ~274 TB over 5 years (media: much more)
```

### 6.5 Additional Quick Estimates

**YouTube Upload Storage**:
```
500 hours of video uploaded per MINUTE
1 hour of 720p video ~= 1 GB (compressed)
Per minute: 500 GB raw video
With multiple resolutions (360p, 720p, 1080p, 4K) = ~4x = 2 TB/minute
With replication (3x): 6 TB/minute
Per year: 6 TB * 60 * 24 * 365 = ~3,153,600 TB = ~3,153 PB = ~3.15 EB/year just for new uploads
```

**WhatsApp Message Volume**:
```
100 billion messages/day
Average message size: ~500 bytes (text) to ~100 KB (image)
Text messages: 70% * 100B * 500 bytes = 35 TB/day
Image messages: 30% * 100B * 100 KB = 3,000 TB/day = 3 PB/day
BUT: Messages are end-to-end encrypted, not stored on servers long-term
Server infrastructure focus: DELIVERY SPEED, not storage
Key scaling challenge: 100B / 86,400 = 1.16 MILLION messages/sec delivery rate!
```

**Uber Driver Location Updates**:
```
Active drivers globally at peak: ~5 million
GPS ping frequency: every 4 seconds
Location write QPS: 5,000,000 / 4 = 1,250,000 writes/sec (1.25M/sec!)
Each location record: ~200 bytes (driver_id, lat, lng, timestamp, speed)
Write bandwidth: 1.25M * 200 bytes = 250 MB/sec
This is why location is the hardest scaling problem at Uber, not ride requests
```

---

## 7. CAP Theorem Introduction

*(Full deep dive with proof, PACELC, and consensus algorithms in Module 6)*

The CAP Theorem, proven by Eric Brewer (2000) and formally by Gilbert & Lynch (2002), states:

**A distributed data store can guarantee at most 2 of these 3 properties**:

```
     Consistency
          /\
         /  \
        /    \
    CP /      \ CA
      /        \ (impossible
     /          \  in practice)
    /____________\
 Availability  Partition
               Tolerance
```

**Consistency (C)**: Every read receives the most recent write or an error.
All nodes in the distributed cluster see exactly the same data at the same time.
Think "linearizability" -- the system behaves as if it has a single copy of the data.

**Availability (A)**: Every request receives a (non-error) response.
The system keeps operating even if some nodes are down or unreachable.
Note: the response may NOT be the most recent data.

**Partition Tolerance (P)**: The system continues operating even when network packets
are dropped or delayed between nodes (a "network partition").

**The Critical and Often Missed Insight**:
In a real distributed system deployed across multiple machines (or even multiple processes),
network partitions ARE inevitable. They happen due to:
- Network switches failing
- Cable getting cut
- Cloud provider network issues
- OS crashes
- Packet loss under high load

**You CANNOT choose "CA" in a real distributed system.**
You cannot sacrifice Partition Tolerance because you WILL have partitions.

Therefore, the real choice is:
```
During a network partition, do you choose:

  CP (Consistency + Partition Tolerance):
    System becomes UNAVAILABLE rather than return potentially stale data
    "I'd rather return an error than give you wrong data"
    Examples: HBase, Zookeeper, Redis Cluster, MongoDB (majority writes)
    Use for: Bank accounts, inventory counts, distributed locks

  AP (Availability + Partition Tolerance):
    System STAYS AVAILABLE but may return stale data
    "I'd rather give you potentially old data than return an error"
    Examples: Cassandra, DynamoDB (eventual), CouchDB, DNS
    Use for: Social media feeds, product catalogs, shopping carts, DNS
```

The full treatment -- including PACELC (a more realistic model), strong vs eventual consistency,
linearizability, the Raft consensus algorithm, and distributed transactions -- is in Module 6.

---

## 8. System Design Interview Framework: RADIO

Structured thinking is crucial in system design interviews. Without a framework,
candidates ramble, miss requirements, and jump to solutions before understanding the problem.

The RADIO framework provides a repeatable, disciplined approach:

```
R - Requirements      (5 min)
A - API Design        (5 min)
D - Data Model        (5 min)
I - Infrastructure    (15 min)
O - Optimizations     (10 min)
```

### R -- Requirements Clarification (5 minutes)

**Never jump to designing. Clarifying requirements is where candidates lose the most points.**

```
Functional Requirements (What the system does):
  "What are the core features we MUST support?"
  "Are there features I should explicitly NOT design for?"
  "Should I focus on any specific use case first?"

Non-Functional Requirements (How well it does it):
  "How many users are we expecting? DAU? MAU?"
  "What is the expected read-to-write ratio?"
  "What latency is acceptable? (p99 < 200ms?)"
  "What availability do we need? (99.9%? 99.99%?)"
  "Do we need strong consistency or is eventual consistency OK?"
  "What is the geographic distribution of users?"
  "Are there compliance requirements? (GDPR, PCI-DSS, HIPAA?)"

Out of Scope:
  "Should I design the admin dashboard?"
  "Should I handle payments and billing?"
  "Is user authentication in scope?"

Pro Tip: After clarifying, RESTATE your understanding:
  "So to confirm: we need to design a URL shortener that handles 100M DAU,
   supports link creation, redirect, and analytics. High availability (99.99%)
   is required. We don't need to handle payments or admin features. Is that right?"
```

### A -- API Design (5 minutes)

Define the contract between your system and clients BEFORE designing internals.
APIs are the "public surface" -- they constrain your design choices.

```
URL Shortener API:

POST /v1/urls
  Request:  { "original_url": "https://example.com/very/long/path", "expiry_days": 30 }
  Response: { "short_url": "https://bit.ly/abc123", "short_code": "abc123",
              "expires_at": "2025-01-01T00:00:00Z" }
  Errors:   400 (invalid URL), 401 (not authenticated), 429 (rate limited)

GET /v1/{short_code}
  Response: 301 Redirect to original URL
  Headers:  Location: https://example.com/very/long/path
  Errors:   404 (not found), 410 (expired)

DELETE /v1/urls/{short_code}
  Response: 204 No Content
  Errors:   401, 403, 404

GET /v1/urls/{short_code}/stats
  Response: {
    "short_code": "abc123",
    "total_clicks": 12345,
    "unique_visitors": 9876,
    "clicks_today": 234,
    "top_referrers": ["google.com", "twitter.com"],
    "geographic_distribution": {"US": 45%, "UK": 20%}
  }
```

### D -- Data Model (5 minutes)

Choose your database type and define your schema based on access patterns.

```
Decision: SQL vs NoSQL?
  - URL Shortener: SQL is fine (URLs are simple records, relatively low scale)
  - High-scale systems: Often need both (SQL for OLTP, NoSQL for specific patterns)

Table Design (PostgreSQL):

CREATE TABLE urls (
  id           BIGSERIAL PRIMARY KEY,
  short_code   VARCHAR(10) NOT NULL UNIQUE,
  original_url TEXT NOT NULL,
  user_id      BIGINT,                    -- NULL for anonymous links
  created_at   TIMESTAMPTZ DEFAULT NOW(),
  expires_at   TIMESTAMPTZ,               -- NULL means never expires
  click_count  BIGINT DEFAULT 0,
  is_active    BOOLEAN DEFAULT TRUE
);
CREATE INDEX idx_urls_short_code ON urls(short_code);  -- Primary lookup
CREATE INDEX idx_urls_user_id ON urls(user_id);        -- "My links" page

CREATE TABLE url_analytics (
  id           BIGSERIAL PRIMARY KEY,
  short_code   VARCHAR(10) NOT NULL,
  clicked_at   TIMESTAMPTZ DEFAULT NOW(),
  ip_address   INET,
  user_agent   TEXT,
  referrer     TEXT,
  country_code CHAR(2)
);
CREATE INDEX idx_analytics_short_code ON url_analytics(short_code);
-- Separate table prevents analytics writes from slowing down URL table
```

### I -- Infrastructure / High-Level Design (15 minutes)

Start with the simplest possible design that satisfies the requirements.
Then evolve it step by step as you identify bottlenecks.

```
Level 1: Minimum Viable Architecture
  [Client] --> [App Server] --> [Postgres DB]
  Problems: No redundancy, limited scale

Level 2: Add Redundancy and Separation
  [Client] --> [Load Balancer] --> [App Server Pool] --> [Postgres Primary]
                                                              |
                                                    [Postgres Read Replica]
  Problems: Still limited by DB writes, slow reads without caching

Level 3: Add Caching and Scale
  [Client]
     |
  [CDN]  (cache redirect responses, serve 301 at edge)
     |
  [Load Balancer] (L7, health checks, SSL termination)
     |
  [App Server Pool] (stateless, auto-scaling)
     |          |                    |
  [Redis]  [Postgres Primary]  [Kafka]
  (hot URL  (writes + meta)    (analytics events)
   cache)        |                   |
           [Postgres Replicas]  [Analytics Consumer]
           (redirect reads)     [ClickHouse]

Level 4: Global Scale
  [Users in US] --> [US Edge CDN] --> [US Region]
  [Users in EU] --> [EU Edge CDN] --> [EU Region]
  [Users in Asia] --> [Asia Edge CDN] --> [Asia Region]
                              |               |               |
                         [Global Postgres with cross-region replication]
```

### O -- Optimizations and Deep Dive (10 minutes)

The interviewer will guide you to dig deeper on 1-2 specific areas.
Always present the trade-off, not just the solution.

```
Common Deep Dive Topics for URL Shortener:

Q: How do you generate the short code?
  Option 1: Random Base62 (a-z, A-Z, 0-9):
    - 6 characters: 62^6 = 56 billion unique codes. More than enough.
    - Risk: Collisions (small but non-zero probability)
    - Solution: Check DB before storing; retry on collision
  Option 2: Hash of original URL (MD5/SHA1, take first 6 chars):
    - Deterministic: same URL always gets same code
    - Problem: Different users might get same short code for same URL
    - Also: hash collisions possible
  Option 3: Auto-increment ID converted to Base62:
    - No collisions, sequential
    - Downside: IDs are sequential, can be enumerated (security concern)
    - Need a centralized ID generator (can be a SPOF)
  Option 4: Distributed ID generation (Snowflake IDs):
    - Globally unique, time-sorted, no central coordinator needed
    - Twitter's approach, used at massive scale

Q: How do you make redirects fast?
  - Cache hot short codes in Redis (LRU eviction, 1M URLs = ~100MB of memory)
  - CDN edge caching: 301 redirects can be cached at CDN edge nodes
    Trade-off: 301 is permanently cached by browsers (hard to update)
    Use 302 (temporary redirect) if URL might change; 301 for permanent
  - In-memory cache in app servers (L1 cache before Redis)

Q: How do you count clicks accurately at scale?
  Option A: Synchronous DB increment on every redirect (accurate, slow):
    UPDATE urls SET click_count = click_count + 1 WHERE short_code = ?
    Problem: This write to Postgres for every redirect = major bottleneck
  Option B: Fire-and-forget to a queue (Kafka), batch update:
    - Redirect responds immediately (fast), analytics event goes to Kafka
    - Analytics consumer aggregates and updates counts asynchronously
    - Trade-off: Counts may be a few seconds or minutes behind
  Option C: HyperLogLog in Redis (approximate, very efficient):
    - Redis PFADD / PFCOUNT for unique visitor counts
    - Uses 12KB of memory regardless of cardinality
    - ~0.81% error rate -- good enough for analytics
```

---

## Summary: The Mental Model

When approaching any system design problem, systematically answer these 5 questions:

```
1. SCALE
   - How much data? How many requests per second?
   - What is the growth trajectory over 5 years?
   - Determines: Architecture tier (single server? distributed? global?)

2. LATENCY
   - How fast must operations be? p50? p99?
   - Which operations are latency-critical?
   - Determines: Caching strategy, database choice, geographic distribution

3. CONSISTENCY
   - Can users see slightly stale data, or must reads always be current?
   - What happens if two users update the same record simultaneously?
   - Determines: Database type, caching strategy, replication approach

4. AVAILABILITY
   - How much downtime per year is acceptable?
   - What is the cost of downtime (revenue, reputation, safety)?
   - Determines: Redundancy level, disaster recovery, multi-region needs

5. COST
   - What is the infrastructure budget?
   - Is optimizing for cost vs. scale vs. developer productivity?
   - Always a real constraint -- perfect systems don't exist in finite budgets
```

**The answers to these 5 questions determine 80% of your architecture.**
The remaining 20% is implementation details that you uncover by deep-diving specific components.

---

## Further Reading and Resources

- **Designing Data-Intensive Applications** by Martin Kleppmann -- The single best book on this topic
- **Google's Site Reliability Engineering Book** -- Free at https://sre.google/sre-book/
- **Jeff Dean's "Numbers Everyone Should Know"** -- Original latency reference
- **System Design Interview** by Alex Xu -- Great for interview prep with worked examples
- **High Scalability Blog** -- Real architectures at scale: http://highscalability.com/
- **AWS Architecture Blog** -- Real patterns from AWS: https://aws.amazon.com/blogs/architecture/
- **Netflix Tech Blog** -- How Netflix actually works: https://netflixtechblog.com/
