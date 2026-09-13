# Cheat Sheet — Modern Network Infrastructure

## CDN Flow
```
User request → DNS resolves CDN domain → Nearest PoP (anycast/GeoDNS)
  → Cache HIT: serve immediately (edge, <30ms)
  → Cache MISS: fetch from origin, cache, serve

Routing methods:
  Anycast:  Multiple PoPs share same IP; BGP routes to nearest
  GeoDNS:   DNS returns different IPs based on requester's geolocation
```

## CDN Cache Invalidation Methods
| Method | Speed | Complexity | Best For |
|--------|:-----:|:----------:|---------|
| TTL expiry | Slow (up to max-age) | Simple | Infrequently changed content |
| Purge API | Fast (~seconds, propagation) | Medium | HTML, content with known update times |
| Versioned URLs | Instant | Requires build pipeline | JS, CSS, images (static assets) |

## Load Balancer Types
| | L4 (Transport) | L7 (Application) |
|-|----------------|------------------|
| Routes on | IP + port | URL, headers, cookies, body |
| TLS termination | ❌ (passthrough) | ✅ |
| Health checks | TCP connect | HTTP GET /health |
| Speed | Fastest | Slower (full HTTP parse) |
| Protocol | Any TCP/UDP | HTTP/S, WebSocket, gRPC |
| Examples | AWS NLB, HAProxy TCP | AWS ALB, nginx, Envoy |

## Load Balancing Algorithms
| Algorithm | Best For | Weakness |
|-----------|---------|---------|
| Round Robin | Homogeneous requests | Ignores server load |
| Weighted Round Robin | Mixed capacity backends | Static weights |
| Least Connections | Variable-length requests | Overhead of tracking |
| IP Hash | Session stickiness | Uneven if few heavy clients |
| Power of Two | General high performance | Slightly more overhead |

## Reverse Proxy vs Forward Proxy
```
Forward Proxy:
  Client → [Forward Proxy] → Internet
  Client configures proxy. Internet sees proxy IP.
  Use: filtering, anonymization, client-side cache

Reverse Proxy:
  Internet → [Reverse Proxy] → Backend servers
  Transparent to client. Backend IPs hidden.
  Use: load balancing, TLS termination, WAF, caching
```

## Service Mesh (Sidecar Pattern)
```
Service A → [Envoy sidecar] → network → [Envoy sidecar] → Service B
                ↑                               ↑
          Control plane (Istio) configures both sidecars

Provides (without code changes):
  ✅ mTLS everywhere
  ✅ Load balancing
  ✅ Circuit breaking
  ✅ Retries/timeouts
  ✅ Observability (metrics, traces, logs)
  ✅ Traffic splitting (canary)
```

## Circuit Breaker States
```
CLOSED → requests flow normally
  ↓ (N failures / error rate threshold)
OPEN → fail fast, no requests sent to backend
  ↓ (timeout period)
HALF-OPEN → allow probe requests
  ↓ success → CLOSED
  ↓ failure → OPEN
```

## Multi-Region High Availability
```
3 regions (active-active) + CDN layer

Failover path:
  Health check detects failure → update DNS (GeoDNS/Route53)
  TTL expiry → traffic shifts to healthy regions
  Total failover: health check interval + TTL = ~60-120 seconds

Availability: 3 × 99.95% regions ≈ 99.99% (assuming short failover)
```

## Network Diagnostics Quick Reference
```bash
ping example.com              # Reachability + RTT
traceroute example.com        # Path + per-hop latency
dig example.com +stats        # DNS resolution time + result
dig +trace example.com        # Full DNS resolution chain

# HTTP timing breakdown
curl -o /dev/null -w "DNS:%{time_namelookup} TCP:%{time_connect} \
  TLS:%{time_appconnect} TTFB:%{time_starttransfer} \
  Total:%{time_total}\n" https://example.com

curl -I -v https://example.com  # Headers + verbose
tcpdump -i eth0 port 80        # Capture HTTP packets
ss -tunap                       # Active connections with PIDs
nmap -p 80,443 example.com     # Port scan
```

## Key Design Numbers
```
CDN edge latency:         5-30ms (vs 100-300ms to origin)
DNS TTL for failover:     30-60 seconds (low TTL = faster failover)
Health check interval:    10-30 seconds typical
Circuit breaker threshold: 5 failures in 10 seconds (configurable)
LB health check:          HTTP GET /health every 30s, 2 failures = unhealthy
TCP connection reuse:      HTTP/2 multiplexing (vs 6 connections per origin in HTTP/1.1)
```

## TLS Termination Options
```
Terminate at LB only:
  Internet -[TLS]→ LB -[HTTP]→ Backend
  Simple; backends don't need TLS

Re-encrypt (end-to-end TLS):
  Internet -[TLS]→ LB -[TLS]→ Backend
  More secure (traffic encrypted on internal network too)
  Use when internal network is untrusted

Pass-through (L4 only):
  Internet -[TLS]→ LB → Backend (TLS passthrough, no decryption)
  Backend handles TLS; LB can't see HTTP content
```
