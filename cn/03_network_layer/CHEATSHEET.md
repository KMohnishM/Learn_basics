# Cheat Sheet — Network Layer

## Subnetting Quick Reference

### Formulas
```
Given prefix /n:
  Host bits (h)       = 32 - n
  Usable hosts        = 2^h - 2
  Block size          = 2^h
  Subnets from parent = 2^(n - parent_prefix)

Need N hosts per subnet → h = ⌈log₂(N+2)⌉
Block size determines subnet boundaries (multiples of block size)
```

### Common Prefix Sizes
| Prefix | Subnet Mask | Hosts | Block |
|--------|------------|-------|-------|
| /24 | 255.255.255.0 | 254 | 256 |
| /25 | 255.255.255.128 | 126 | 128 |
| /26 | 255.255.255.192 | 62 | 64 |
| /27 | 255.255.255.224 | 30 | 32 |
| /28 | 255.255.255.240 | 14 | 16 |
| /29 | 255.255.255.248 | 6 | 8 |
| /30 | 255.255.255.252 | 2 | 4 |

### Subnet Calculation Steps
```
1. Convert mask to prefix (count the 1 bits)
2. Network addr = IP AND mask
3. Block size = 2^(32 - prefix)
4. Broadcast = network addr + block_size - 1
5. First host = network + 1
6. Last host = broadcast - 1
7. Usable hosts = block_size - 2
```

## Private IP Ranges (RFC 1918)
```
10.0.0.0/8          (10.0.0.0 – 10.255.255.255)    Class A private
172.16.0.0/12       (172.16.0.0 – 172.31.255.255)   Class B private
192.168.0.0/16      (192.168.0.0 – 192.168.255.255) Class C private
127.0.0.0/8         Loopback (127.0.0.1 = localhost)
169.254.0.0/16      APIPA (self-assigned, DHCP failed)
0.0.0.0/0           Default route (match all)
255.255.255.255     Limited broadcast (not routed)
```

## IPv4 Header Key Fields
| Field | Size | Purpose |
|-------|------|---------|
| Version | 4b | 4 = IPv4, 6 = IPv6 |
| IHL | 4b | Header length in 32-bit words (min 5 = 20B) |
| Total Length | 16b | Total packet size (max 65,535B) |
| TTL | 8b | Decremented at each hop; 0 = discard + ICMP |
| Protocol | 8b | 6=TCP, 17=UDP, 1=ICMP, 89=OSPF |
| Src/Dst IP | 32b each | Unchanged end-to-end |
| Flags | 3b | DF=Don't Fragment, MF=More Fragments |
| Fragment Offset | 13b | Position of fragment (in 8-byte units) |

## Routing Table — Longest Prefix Match
```
For destination D, match against all entries:
  Select the entry with the LONGEST matching prefix

Example for 10.5.7.3:
  0.0.0.0/0    → matches (0 bits)
  10.0.0.0/8   → matches (8 bits)
  10.5.0.0/16  → matches (16 bits) ← WINNER
```

## Routing Protocols Comparison
| | RIP | OSPF | BGP |
|-|-----|------|-----|
| Type | Distance Vector | Link State | Path Vector |
| Algorithm | Bellman-Ford | Dijkstra SPF | Path-based |
| Metric | Hop count (max 15) | Cost (bandwidth-based) | Policy attributes |
| Scope | Small IGP | Large IGP | Between ASes (internet) |
| Convergence | Slow (minutes) | Fast (seconds) | Slow (minutes) |
| Protocol | UDP/520 | IP/89 | TCP/179 |

## OSPF Key Points
```
LSA = Link State Advertisement (flooded to all routers)
LSDB = Link State Database (same on all routers in area)
SPF = Dijkstra's algorithm (finds shortest path tree)
Cost = reference_bandwidth / link_bandwidth (default ref = 100Mbps)
Area 0 = backbone area (all areas must connect to it)
Convergence: seconds (vs RIP's minutes)
```

## NAT / PAT
```
Private IP:port → Public IP:translated_port

Outgoing: src = private IP:port → rewrite to public IP:new_port
Incoming: dst = public IP:new_port → rewrite to private IP:original_port

Tracks state in NAT table (connection-based)
Problems: breaks end-to-end model, P2P issues (STUN/TURN/ICE workaround)
```

## ICMP Common Messages
| Type | Message | Used By |
|------|---------|---------|
| 0 | Echo Reply | ping response |
| 3 | Destination Unreachable | port/host not reachable |
| 8 | Echo Request | ping |
| 11 | Time Exceeded | traceroute (TTL=0) |

## IPv4 vs IPv6
| | IPv4 | IPv6 |
|-|------|------|
| Address size | 32 bits | 128 bits |
| Notation | Dotted decimal | Colon-hex |
| Total addresses | ~4.3 billion | ~340 undecillion |
| Header checksum | ✅ | ❌ (removed) |
| Fragmentation | Routers can | Only end hosts |
| Broadcast | ✅ | ❌ (uses multicast) |
| Loopback | 127.0.0.1 | ::1 |
| Link-local | 169.254.x.x | fe80::/10 |
