# Computer Networks — Complete Interview Curriculum

A deeply technical, interview-focused Computer Networks curriculum. Built for engineers who need to understand networking from first principles — not just memorize definitions. Every module explains the internal mechanics, the "why", and exactly what interviewers probe.

---

## Who This Is For

- Software engineers preparing for SDE / backend / systems interviews
- DevOps and infrastructure engineers wanting to solidify foundations
- CS students who want a practical, interview-angled supplement to textbooks

---

## Module Structure

Every module has exactly **three files**:

```
module/
├── README.md       ← Full textbook-depth internals. The "why" behind each concept.
├── QnA.md          ← Tiered interview Q&A
│                     🟢 Easy | 🟡 Medium | 🔴 Hard (numericals + design questions)
└── CHEATSHEET.md   ← One-page quick reference: tables, formulas, key numbers
```

---

## Curriculum Map

| # | Module | Core Topics | Numericals? |
|---|--------|-------------|:-----------:|
| [M1](./01_osi_tcpip/) | **OSI & TCP/IP Models** | 7 layers, encapsulation, PDUs, devices by layer, port numbers, full URL walkthrough | ❌ |
| [M2](./02_data_link/) | **Physical & Data Link Layer** | Transmission media, Nyquist/Shannon, MAC addresses, Ethernet frame, switches/CAM, ARP, VLANs, CSMA/CD vs CA | ✅ Shannon capacity |
| [M3](./03_network_layer/) | **Network Layer** | IPv4, CIDR, subnetting, IP header, ICMP, routing (LPM), OSPF vs BGP, NAT, IPv6 | ✅ Subnetting, prefix math |
| [M4](./04_transport_layer/) | **Transport Layer** | TCP vs UDP, TCP header, 3-way handshake, 4-way teardown, TIME_WAIT, flow control, congestion control (AIMD, CUBIC, BBR) | ✅ Throughput, BDP |
| [M5](./05_application_layer/) | **Application Layer** | HTTP/1.1/2/3, status codes, methods, caching, DNS records, TLS 1.2 vs 1.3, ECDHE, WebSockets | ❌ |
| [M6](./06_network_security/) | **Network Security** | CIA triad, attacks (DDoS/ARP/DNS/SYN flood), amplification, firewalls, VPN/IPSec, DNSSEC, Zero Trust | ✅ Amplification factors |
| [M7](./07_socket_programming/) | **Socket Programming** | Socket types, server/client lifecycle, kernel accept queues, byte order, select/epoll/io_uring, non-blocking I/O, C10K | ❌ |
| [M8](./08_modern_networking/) | **Modern Infrastructure** | CDN, L4/L7 load balancers, algorithms, reverse proxy, service mesh, circuit breakers, multi-region HA, diagnostics | ❌ |

---

## Suggested Study Order

### Week 1 — Fundamentals (Bottom of Stack)
**Day 1**: M1 — OSI/TCP-IP (the framework for everything)
**Day 2–3**: M2 — Data Link (ARP, switches, VLANs — come up constantly)
**Day 4–5**: M3 — Network Layer (subnetting — must be able to solve cold)
**Day 6–7**: M4 — Transport Layer (TCP is the most-asked topic in CN interviews)

### Week 2 — Application & Security
**Day 1–2**: M5 — Application Layer (HTTP evolution, TLS — every backend interview)
**Day 3–4**: M6 — Network Security (DDoS, firewalls, VPN — SDE and DevOps interviews)
**Day 5–6**: M7 — Socket Programming (how real servers work — systems interviews)
**Day 7**: M8 — Modern Infrastructure (CDN, load balancers — system design interviews)

---

## Most Commonly Asked Interview Topics

### Virtually Certain
- TCP vs UDP (M4)
- TCP 3-way handshake (M4)
- What happens when you type a URL (M1 + M3 + M4 + M5)
- HTTP methods + status codes (M5)
- DNS resolution process (M1 + M5)

### Very Likely (Any Backend/Systems Interview)
- OSI model — which layer does X operate at (M1)
- Subnetting — given IP + mask, find network/broadcast/hosts (M3)
- TCP flow control vs congestion control (M4)
- HTTPS — TLS handshake overview (M5)
- ARP — why and how (M2)

### For Senior / DevOps / Systems Roles
- TCP TIME_WAIT and how to handle it at scale (M4)
- TCP congestion control AIMD, CUBIC, BBR (M4)
- OSPF link state vs BGP path vector (M3)
- DDoS amplification and defense (M6)
- epoll vs select — C10K problem (M7)
- L4 vs L7 load balancer design decisions (M8)
- CDN cache invalidation strategies (M8)
- Service mesh and circuit breaker (M8)

---

## Key Numbers to Memorize

| Fact | Value |
|------|-------|
| Ethernet MTU | 1500 bytes |
| TCP min header | 20 bytes |
| UDP header | 8 bytes (fixed) |
| TCP default MSS | 1460 bytes |
| TCP TIME_WAIT | 2 × MSL ≈ 120 seconds |
| Fast retransmit trigger | 3 duplicate ACKs |
| DNS default port | 53 (UDP and TCP) |
| HTTPS port | 443 |
| TLS 1.3 handshake | 1 RTT (0-RTT for resumption) |
| TLS 1.2 handshake | 2 RTT |
| 7200 RPM rotational latency | 4.17ms (not relevant to CN but carry from OS) |
| Private IP ranges | 10/8, 172.16/12, 192.168/16 |
| Loopback | 127.0.0.1 |
| CDN edge latency | 5–30ms |
| Cross-region WAN RTT (US↔EU) | ~80–120ms |
| DNS amplification factor | ~50× (ANY query) |
| Memcached amplification | ~50,000× |

---

## Prerequisite Knowledge

- Basic understanding of binary/hex (for IP/MAC address math)
- Familiarity with at least one programming language (for socket examples)
- OS basics helpful (processes, file descriptors) for M7
