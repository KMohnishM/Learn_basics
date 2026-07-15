# Q&A — Network Layer

---

## 🟢 Easy

**Q1. What is the difference between a private IP and a public IP?**

**Private IPs** (RFC 1918): `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`. Not routed on the public internet. Can be reused across different private networks. Used inside homes, offices, data centers.

**Public IPs**: Globally unique, assigned by IANA/RIRs. Routable on the internet. Required for any host that needs to be reachable from the internet.

Hosts with private IPs need **NAT** (Network Address Translation) at the gateway to communicate with the internet.

---

**Q2. What is the default route and when is it used?**

The default route is `0.0.0.0/0` — it matches ALL destination IP addresses (0 bits must match = everything matches). It has the shortest prefix and is only selected if no more specific route exists.

Used as a "gateway of last resort" — when a router or host doesn't know how to reach a specific destination, it forwards the packet to whatever is pointed to by the default route (typically the ISP's router for home networks, or the core network for enterprise routers).

---

**Q3. What is Longest Prefix Match?**

When multiple routing table entries match a destination IP, the router selects the route with the **longest matching prefix** (most specific match).

Example: Routing table has `10.0.0.0/8` and `10.5.0.0/16`. For destination `10.5.7.3`:
- `10.0.0.0/8` matches (first 8 bits match)
- `10.5.0.0/16` matches (first 16 bits match) ← SELECTED

The /16 route is more specific (knows more about where `10.5.x.x` is) and wins.

---

**Q4. What is ICMP used for? Name two tools that use it.**

ICMP (Internet Control Message Protocol) is used for error reporting and network diagnostic messages. It carries control messages, not data.

**Tools using ICMP:**
1. **`ping`**: Sends ICMP Echo Request (type 8) and measures round-trip time from Echo Reply (type 0). Tests reachability.
2. **`traceroute`/`tracert`**: Sends packets with increasing TTL values. Each router that hits TTL=0 sends back ICMP Time Exceeded (type 11), revealing the path hop by hop.

---

**Q5. What is NAT and why is it used?**

NAT (Network Address Translation) rewrites the source/destination IP addresses (and ports) of packets as they pass through a gateway.

**Used because**: IPv4 addresses are exhausted. Private RFC 1918 addresses are not globally routable. NAT allows an entire home or office network (using private IPs) to share a single public IP to access the internet. The router maintains a translation table to map outgoing private IP:port pairs to public IP:port pairs and reverse the translation for incoming responses.

---

## 🟡 Medium

**Q6. Subnet `172.16.0.0/16` into subnets of at least 500 hosts each. What prefix do you use? How many subnets?**

Need at least 500 usable hosts per subnet.
Usable hosts = 2^h - 2 ≥ 500 → 2^h ≥ 502 → h ≥ 9 (2^9 = 512, usable = 510 ≥ 500 ✓)

Host bits = 9. Network bits = 32 - 9 = **23**. New prefix = **/23**.

Parent: 172.16.0.0/16 → 16 network bits. New: /23 → 23 network bits.
Borrowed bits = 23 - 16 = 7 bits.
Number of subnets = 2^7 = **128 subnets**.

Each subnet: 2^9 - 2 = **510 usable hosts**, block size = 512.

First few subnets:
- 172.16.0.0/23 → hosts: 172.16.0.1 – 172.16.1.254
- 172.16.2.0/23 → hosts: 172.16.2.1 – 172.16.3.254
- 172.16.4.0/23 → hosts: 172.16.4.1 – 172.16.5.254
- ...

---

**Q7. Given these routing table entries, which route does a router select for destination 192.168.5.10?**

```
10.0.0.0/8        via 10.1.1.1
192.168.0.0/16    via 192.168.1.1
192.168.5.0/24    via 192.168.2.1
0.0.0.0/0         via 203.0.113.1
```

Check which entries match 192.168.5.10:
- `10.0.0.0/8`: 192.168.5.10 starts with 192, not 10. ❌
- `192.168.0.0/16`: 192.168.(5.10) — first 16 bits match (192.168). ✅
- `192.168.5.0/24`: 192.168.5.(10) — first 24 bits match (192.168.5). ✅ (longer)
- `0.0.0.0/0`: Matches everything. ✅

**Selected: `192.168.5.0/24` via 192.168.2.1** — longest prefix match (24 bits > 16 bits > 0 bits).

---

**Q8. Explain OSPF's link state mechanism. How does it differ from RIP's distance vector?**

**OSPF (Link State)**:
- Each router knows the state (up/down, bandwidth) of its directly connected links.
- Routers flood **LSAs (Link State Advertisements)** to ALL other routers in the area. Every router receives the same LSAs.
- Each router builds an identical **Link State Database (LSDB)** — a complete map of the network topology.
- Each router independently runs **Dijkstra's SPF algorithm** on the LSDB to compute the shortest path tree to every destination.
- On topology change: affected router floods a new LSA. All routers update their LSDB and recompute. Convergence in seconds.

**RIP (Distance Vector)**:
- Each router only knows distances (hop counts) to destinations via its neighbors — no full topology map.
- Routers advertise their routing tables to directly connected neighbors.
- "Count to infinity" problem: if a link fails, routers may incorrectly increment hop counts toward infinity before declaring a route unreachable. Slow convergence (up to several minutes).
- Max 15 hops limits scalability.

**Key difference**: OSPF has a complete topology view → makes optimal decisions, converges fast. RIP only has local view → may make suboptimal decisions, slow convergence.

---

**Q9. What is the "count to infinity" problem in RIP? How is it mitigated?**

If router A reaches network X via router B (B reaches X directly), and B's link to X fails:
- B should advertise X as unreachable (metric = infinity = 16).
- But A might simultaneously advertise to B "I can reach X with cost 2" (via B itself).
- B updates its routing table: "X is reachable via A with cost 3."
- A then updates: "X via B, cost 4." B: "cost 5." ...until both count to 16.

This is the count-to-infinity problem — it takes many rounds of updates before routers recognize X is unreachable, during which incorrect routes are used.

**Mitigations:**
1. **Split Horizon**: Never advertise a route back to the neighbor you learned it from. A would not advertise "X via B" back to B.
2. **Poison Reverse**: Advertise learned routes back to the source with metric = 16 (infinity) to explicitly tell the source to not use that path.
3. **Maximum hop count = 15**: Limits how far count-to-infinity goes (stops at 16).
4. **Triggered updates**: Send updates immediately when a route changes (don't wait for next regular update cycle).

---

## 🔴 Hard

**Q10. You have the IP 192.168.10.75 with subnet mask 255.255.255.192. Find: (a) prefix, (b) network address, (c) broadcast address, (d) first/last usable host, (e) number of usable hosts.**

**(a) Prefix length:**
255.255.255.192 → last octet = 192 = 11000000
→ 24 + 2 = **/26**

**(b) Network address:**
192.168.10.75 in binary last octet: 01001011
Mask last octet: 11000000
AND: 01000000 = 64
Network = **192.168.10.64**

**(c) Broadcast address:**
Set all host bits to 1: 01000000 OR 00111111 = 01111111 = 127
Broadcast = **192.168.10.127**

**(d) First/Last usable host:**
First = network + 1 = **192.168.10.65**
Last = broadcast - 1 = **192.168.10.126**

**(e) Usable hosts:**
2^6 - 2 = 64 - 2 = **62 hosts**

---

**Q11. How does BGP prevent routing loops? Why does it use path vectors?**

**Distance vector protocols** (RIP) only advertise distances to destinations. If A advertises "I can reach X in 3 hops," B doesn't know whether B itself is part of that 3-hop path. If B is, using this route creates a loop.

**BGP uses path vectors**: BGP advertisements include the full list of AS numbers traversed. When router B receives "X is reachable via path [AS1, AS2, AS3]," and B is in AS2, B sees its own AS in the path → **loop detected → route rejected**.

**How it works in practice:**
1. Router in AS100 has route to X: `X via [AS100]`
2. BGP peer in AS200 receives it, prepends its own AS: `X via [AS200, AS100]`
3. BGP peer in AS300 receives it: `X via [AS300, AS200, AS100]`
4. If AS100 receives this back: sees AS100 in path → loop → ignored.

This ensures no AS appears twice in a BGP path, preventing routing loops across the entire internet.

**Also**: BGP uses many **attributes** to choose between paths: AS path length, local preference, MED (Multi-Exit Discriminator), origin, etc. The famous BGP decision process has 13 steps and is policy-driven (not purely shortest-path).
