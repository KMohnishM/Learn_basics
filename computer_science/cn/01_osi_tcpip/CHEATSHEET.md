# Cheat Sheet — OSI & TCP/IP Models

## OSI 7 Layers (Top → Bottom)
| # | Layer | PDU | Key Protocols | Device |
|---|-------|-----|--------------|--------|
| 7 | **Application** | Message | HTTP, FTP, SMTP, DNS, SSH | — |
| 6 | **Presentation** | Message | TLS/SSL, MIME, compression | — |
| 5 | **Session** | Message | NetBIOS, RPC, session cookies | — |
| 4 | **Transport** | Segment/Datagram | TCP, UDP, SCTP | — |
| 3 | **Network** | Packet | IP, ICMP, OSPF, BGP | Router |
| 2 | **Data Link** | Frame | Ethernet, Wi-Fi, ARP | Switch |
| 1 | **Physical** | Bits | Cables, fiber, radio | Hub, NIC |

**Mnemonic (top→bottom)**: **A**ll **P**eople **S**eem **T**o **N**eed **D**ata **P**rocessing

## TCP/IP Model (4 Layers)
| TCP/IP | OSI Equivalent | Protocols |
|--------|---------------|-----------|
| Application | 5 + 6 + 7 | HTTP, DNS, SMTP, TLS, SSH |
| Transport | 4 | TCP, UDP |
| Internet | 3 | IPv4, IPv6, ICMP |
| Network Access | 1 + 2 | Ethernet, Wi-Fi, ARP |

## Encapsulation Down the Stack
```
App data
  ↓ + TCP header  → Segment
  ↓ + IP header   → Packet
  ↓ + ETH header + trailer → Frame
  ↓ → Bits
```

## What Stays the Same vs Changes at Each Router Hop
```
IP Header:        Source IP, Dest IP → UNCHANGED end-to-end
Ethernet Header:  Source MAC, Dest MAC → CHANGES at every hop
TTL:              Decremented by 1 at each router → if 0, DISCARD + ICMP
```

## Device → Layer Mapping
| Device | Layer | Does |
|--------|-------|------|
| Hub | L1 | Broadcasts bits to all ports |
| Switch | L2 | Forwards frames by MAC table |
| Router | L3 | Forwards packets by routing table |
| Firewall | L3-L7 | Filters by rules |
| L4 LB | L4 | Distributes TCP connections |
| L7 LB | L7 | Distributes HTTP by URL/headers |

## DNS Resolution Sequence
```
Client → Recursive Resolver (8.8.8.8 or ISP)
       → Root Name Server (.com? → TLD IPs)
       → TLD Name Server (example.com? → auth NS IPs)
       → Authoritative NS (www.example.com? → 1.2.3.4)
       ← Returns IP (with TTL — cached at each hop)
```

## What Happens on `https://example.com` Enter
```
1. DNS: example.com → IP
2. TCP 3-way handshake (port 443)
3. TLS handshake (cert verify, key exchange)
4. HTTP GET request (encrypted)
5. Down stack: segment → packet → frame → bits
6. Routers forward: strip/re-add frame at each hop, IP unchanged
7. Server responds, browser renders
```

## Key Port Numbers
| Port | Service |
|------|---------|
| 22 | SSH |
| 25 | SMTP |
| 53 | DNS (TCP+UDP) |
| 67/68 | DHCP |
| 80 | HTTP |
| 443 | HTTPS |
| 3306 | MySQL |
| 5432 | PostgreSQL |
| 6379 | Redis |
| 27017 | MongoDB |

## Port Ranges
```
0–1023:     Well-known (requires root on Unix)
1024–49151: Registered
49152–65535: Ephemeral (dynamic, used by clients as source ports)
```

## TTL Purpose
```
IP TTL: decremented by 1 at each router
If TTL = 0: router discards packet + sends ICMP "Time Exceeded"
Purpose: prevents routing loop infinite loops
traceroute: exploits TTL (TTL=1→first hop, TTL=2→second hop, etc.)
```

## Anycast vs Unicast vs Broadcast vs Multicast
| Type | Reaches | Example |
|------|---------|---------|
| Unicast | One specific host | Normal TCP connection |
| Anycast | Nearest of many hosts sharing an IP | DNS root servers, CDN |
| Broadcast | All hosts on LAN | ARP request |
| Multicast | Group of interested hosts | Video streaming, routing protocols |
