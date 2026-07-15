# Module 3: Network Layer — IP, Subnetting & Routing

---

## 1. The Network Layer's Job

The Network layer (L3) is responsible for **end-to-end delivery** of packets across multiple networks. Unlike the Data Link layer which handles node-to-node delivery on a single link, the Network layer handles the full path from source host to destination host, potentially traversing dozens of intermediate networks.

**Key responsibilities:**
- **Logical addressing**: IP addresses identify hosts globally
- **Routing**: Determining the path packets take across interconnected networks
- **Fragmentation**: Breaking large packets into smaller pieces that fit each link's MTU
- **TTL management**: Preventing packets from looping forever

---

## 2. IPv4 — Addressing

An **IPv4 address** is a 32-bit number, written as 4 octets in dotted-decimal notation:
```
192.168.1.100
└─┘ └─┘ └┘ └─┘
 ↑   ↑   ↑  ↑
 Each octet is 8 bits (0-255)
```

Total IPv4 addresses: 2^32 = **4,294,967,296 (~4.3 billion)**. This is why IPv4 exhaustion is real — there are more devices than addresses.

### Network and Host Portions

An IP address is divided into:
- **Network portion**: Identifies the network (same for all hosts in a subnet)
- **Host portion**: Identifies a specific host within that network

The **subnet mask** determines the split. A subnet mask of `255.255.255.0` (= `/24` in CIDR notation) means the first 24 bits are network, the last 8 bits are host.

### CIDR — Classless Inter-Domain Routing

Before CIDR (pre-1993), IP addresses used classful addressing:
- Class A: `1.x.x.x – 126.x.x.x` (first bit = 0), 8-bit network, 24-bit host → 16M hosts per network
- Class B: `128.x.x.x – 191.x.x.x`, 16-bit network, 16-bit host → 65,534 hosts
- Class C: `192.x.x.x – 223.x.x.x`, 24-bit network, 8-bit host → 254 hosts

**Problem**: A company needing 300 hosts would get a Class B (65,534 host capacity) — wasting 65,200 addresses.

**CIDR** allows any prefix length (e.g., `/22` gives 1022 hosts, `/25` gives 126 hosts), eliminating the rigid class boundaries. All modern networks use CIDR.

---

## 3. Subnetting — The Math

Subnetting divides a larger network into smaller subnetworks. Essential for:
- Reducing broadcast domain size
- Organizing networks by department, floor, etc.
- Security (isolate segments)
- Efficient IP address utilization

### The Formulas

```
Given a subnet /n:
  - Network bits: n
  - Host bits: 32 - n
  - Number of subnets (from parent): 2^(n - parent_prefix)
  - Hosts per subnet: 2^(32-n) - 2   (subtract network and broadcast addresses)
  - Subnet mask: n consecutive 1s followed by (32-n) zeros
```

### Worked Example — Subnet a /24

**Task**: Divide `192.168.1.0/24` into 4 equal subnets.

4 subnets require 2 bits (2^2 = 4). Borrow 2 bits from host portion.
New prefix = /24 + 2 = **/26**. Each subnet has 2^6 - 2 = **62 usable hosts**.

| Subnet # | Network Address | Host Range | Broadcast |
|----------|----------------|------------|-----------|
| 0 | 192.168.1.0/26 | .1 – .62 | .63 |
| 1 | 192.168.1.64/26 | .65 – .126 | .127 |
| 2 | 192.168.1.128/26 | .129 – .190 | .191 |
| 3 | 192.168.1.192/26 | .193 – .254 | .255 |

**Pattern**: Each subnet starts at a multiple of the block size. Block size = 2^(32-n) = 2^6 = 64. Subnets start at 0, 64, 128, 192.

### Key Rules
- **Network address** (all host bits = 0): Cannot be assigned to a host.
- **Broadcast address** (all host bits = 1): Cannot be assigned to a host; all hosts on the subnet receive packets sent to this address.
- **Usable hosts per subnet** = 2^(host bits) - 2.

### Checking if Two IPs Are on the Same Subnet

Bitwise AND the IP and subnet mask. If both IPs give the same result → same subnet.

```
IP1: 192.168.1.10   = 11000000.10101000.00000001.00001010
IP2: 192.168.1.70   = 11000000.10101000.00000001.01000110
Mask /26 = 255.255.255.192 = 11111111.11111111.11111111.11000000

IP1 & Mask = 11000000.10101000.00000001.00000000 = 192.168.1.0    (subnet 0)
IP2 & Mask = 11000000.10101000.00000001.01000000 = 192.168.1.64   (subnet 1)

Different subnets → must go through a router
```

---

## 4. Special IP Address Ranges

| Range | Purpose |
|-------|---------|
| `10.0.0.0/8` | Private (RFC 1918) |
| `172.16.0.0/12` | Private (RFC 1918) — 172.16.0.0 to 172.31.255.255 |
| `192.168.0.0/16` | Private (RFC 1918) |
| `127.0.0.0/8` | Loopback (127.0.0.1 = "localhost") |
| `0.0.0.0/0` | Default route (matches everything) |
| `0.0.0.0` | "This host" (before IP assigned, e.g., DHCP requests) |
| `255.255.255.255` | Limited broadcast (this subnet, not routed) |
| `169.254.0.0/16` | APIPA (Automatic Private IP Addressing — self-assigned when DHCP fails) |
| `224.0.0.0/4` | Multicast |

---

## 5. IPv4 Header

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Version|  IHL  |   DSCP/ECN    |         Total Length          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         Identification        |Flags|      Fragment Offset     |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Time to Live |    Protocol   |         Header Checksum       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Source Address                          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Destination Address                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Options (if IHL > 5)                       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

**Key fields:**
- **Version (4 bits)**: 4 for IPv4, 6 for IPv6.
- **IHL (Internet Header Length, 4 bits)**: Length of the header in 32-bit words. Minimum 5 (20 bytes), max 15 (60 bytes with options).
- **DSCP/ECN (8 bits)**: Differentiated Services Code Point (QoS priority marking) and Explicit Congestion Notification.
- **Total Length (16 bits)**: Total size of the IP packet (header + data) in bytes. Max 65,535 bytes.
- **Identification (16 bits)**: Used for fragmentation reassembly. All fragments of the same original packet share the same ID.
- **Flags (3 bits)**: Bit 1 = DF (Don't Fragment); Bit 2 = MF (More Fragments — set on all fragments except the last).
- **Fragment Offset (13 bits)**: Position of this fragment in the original packet, in 8-byte units.
- **TTL (8 bits)**: Decremented at each router; packet discarded when 0.
- **Protocol (8 bits)**: Next-layer protocol: 6 = TCP, 17 = UDP, 1 = ICMP, 89 = OSPF.
- **Header Checksum (16 bits)**: Checksum of the IP header only (NOT the data). Recomputed at every router (because TTL changes).
- **Source IP, Destination IP (32 bits each)**: Logical addresses.

---

## 6. ICMP — Internet Control Message Protocol

ICMP (Protocol 1) is used by routers and hosts to send error and control messages. Not for data transfer.

**Common ICMP message types:**

| Type | Message | Used by |
|------|---------|---------|
| 0 | Echo Reply | ping response |
| 3 | Destination Unreachable | Port unreachable, network unreachable |
| 5 | Redirect | Router tells host to use a better route |
| 8 | Echo Request | ping |
| 11 | Time Exceeded | TTL expired (traceroute uses this) |
| 12 | Parameter Problem | Malformed IP packet |

**ping**: Uses ICMP Echo Request (type 8) and Echo Reply (type 0) to test connectivity and measure round-trip time.

**traceroute**: Sends packets with increasing TTL (1, 2, 3...). Each router that decrements TTL to 0 returns an ICMP Time Exceeded. By mapping these responses, traceroute reveals the full path.

---

## 7. Routing — How Routers Forward Packets

A router maintains a **routing table** — a list of known network prefixes and how to reach them.

**Routing table example:**
```
Destination/Prefix  | Next Hop      | Interface | Metric
--------------------|---------------|-----------|-------
192.168.1.0/24      | directly conn | eth0      | 0
10.0.0.0/8          | 172.16.0.1    | eth1      | 10
0.0.0.0/0           | 203.0.113.1   | eth2      | 1  ← default route
```

**Longest Prefix Match (LPM)**: When multiple routes match a destination, the one with the longest prefix (most specific) wins.

```
Destination: 10.5.6.7
Matching routes:
  0.0.0.0/0    (matches everything)
  10.0.0.0/8   (matches 10.x.x.x)
  10.5.0.0/16  (matches 10.5.x.x) ← WINS (longest prefix)
```

### Types of Routes

**Directly Connected**: Router knows about networks on its own interfaces automatically.

**Static Routes**: Manually configured by an administrator. Simple, predictable, no overhead. Not scalable for large or changing networks.

**Dynamic Routes**: Learned automatically via **routing protocols**. Routers exchange routing information with each other and automatically adapt to topology changes (link failures, new links).

---

## 8. Routing Protocols

### Interior Gateway Protocols (IGP) — Within an AS

**AS (Autonomous System)**: A collection of IP networks under a single administrative control (e.g., an ISP, a company). Each AS has an AS number (ASN).

**OSPF (Open Shortest Path First)**:
- **Algorithm**: Dijkstra's Shortest Path First (SPF). Each router builds a complete map of the network (Link State Database) and computes the shortest path tree.
- **Link State**: Routers flood information about their directly connected links (LSAs — Link State Advertisements) to all other routers in the area. Everyone has the same map.
- **Convergence**: Fast convergence after a topology change (seconds).
- **Metric**: Cost (inversely proportional to bandwidth). Reference bandwidth / link bandwidth = OSPF cost.
- **Areas**: Large networks are divided into OSPF areas (with Area 0 = backbone). Reduces LSA flooding.
- **Protocol**: Runs directly over IP (Protocol 89, not TCP or UDP).

**RIP (Routing Information Protocol)**:
- **Algorithm**: Bellman-Ford (distance vector). Routers only know the distance to each destination, not the full topology.
- **Metric**: Hop count. Max 15 hops (16 = unreachable) — limits scalability.
- **Convergence**: Slow (minutes). "Count to infinity" problem.
- Largely obsolete. Replaced by OSPF and EIGRP.

**EIGRP (Enhanced Interior Gateway Routing Protocol)**:
- Cisco proprietary (but now partially open). Hybrid protocol — uses diffusing computation.
- Metric: composite (bandwidth + delay + reliability + load). Faster convergence than RIP, simpler than OSPF.

### Exterior Gateway Protocol — Between ASes

**BGP (Border Gateway Protocol)**:
- The routing protocol of the internet. BGP connects autonomous systems.
- **Path vector protocol**: Advertises full AS paths, not just distances. Prevents routing loops.
- **Policy-based**: BGP routing decisions are based on policies (business agreements between ISPs) not just shortest path. A packet might not take the shortest path — it takes the path that satisfies policy.
- **Convergence**: Slow (minutes). Not designed for fast convergence — designed for policy and stability.
- **TCP port 179**: BGP peers establish TCP connections on port 179 and exchange routing updates.
- Every internet exchange point, every ISP, every large company runs BGP.

---

## 9. NAT — Network Address Translation

**Problem**: RFC 1918 private IPs (`10.x.x.x`, `192.168.x.x`) are not routable on the public internet. A home network has private IPs but needs to access the internet.

**NAT** allows an entire private network to share one (or few) public IP addresses by rewriting packet headers at the gateway (router).

### PAT (Port Address Translation) — Most Common Form

Also called **NAPT** or "NAT overloading":

```
Home devices:
  192.168.1.10:54321 → packets to google.com:443
  192.168.1.20:54322 → packets to netflix.com:443

NAT Table on router (public IP: 1.2.3.4):
  192.168.1.10:54321 ↔ 1.2.3.4:1024
  192.168.1.20:54322 ↔ 1.2.3.4:1025

Outgoing: replace src IP+port with public IP+translated port
Incoming: match translated port → restore original private IP+port
```

**Benefits:**
- Address conservation: thousands of devices share one public IP
- Security: private hosts are not directly reachable from the internet (the NAT table is state-based)

**Problems:**
- **NAT traversal**: Peer-to-peer applications (VoIP, gaming, WebRTC) have difficulty connecting to hosts behind NAT. Solutions: STUN, TURN, ICE.
- **Breaks end-to-end model**: Servers on the internet cannot initiate connections to NAT'd hosts.
- **Performance**: NAT processing adds latency; NAT tables have size limits.

---

## 10. IPv6

IPv6 uses **128-bit addresses** (vs IPv4's 32-bit). Written as 8 groups of 4 hex digits: `2001:0db8:85a3:0000:0000:8a2e:0370:7334`.

**IPv6 address space**: 2^128 ≈ 340 undecillion addresses. Effectively inexhaustible.

**Simplification rules:**
1. Leading zeros in each group can be omitted: `0db8` → `db8`
2. One (only one) sequence of consecutive all-zero groups can be replaced by `::`: `2001:db8::8a2e:370:7334`

**IPv6 Header Improvements over IPv4:**
- Fixed 40-byte header (no variable-length options field → faster processing)
- No checksum (removed because L4 protocols already have checksums)
- No fragmentation by routers (hosts discover path MTU and fragment themselves)
- Built-in IPSec support (authentication and encryption in spec)
- No broadcast (replaced by multicast and anycast)

**Special addresses:**
- `::1` = loopback (IPv4 equivalent: `127.0.0.1`)
- `fe80::/10` = link-local (auto-configured, not routable)
- `2001:db8::/32` = documentation range (like 192.0.2.x in IPv4)
