# Q&A — OSI & TCP/IP Models

---

## 🟢 Easy

**Q1. Name the 7 layers of the OSI model from top to bottom.**

7. Application, 6. Presentation, 5. Session, 4. Transport, 3. Network, 2. Data Link, 1. Physical.

Mnemonic (top→bottom): **A**ll **P**eople **S**eem **T**o **N**eed **D**ata **P**rocessing.

---

**Q2. What is the TCP/IP model and how does it differ from OSI?**

The TCP/IP model is the practical 4-layer model that the internet actually implements:
- Application (combines OSI 5, 6, 7)
- Transport (OSI 4)
- Internet (OSI 3)
- Network Access (combines OSI 1, 2)

OSI is a conceptual reference framework (7 layers, never fully implemented as-is). TCP/IP is what actually runs — it merges Session and Presentation into Application since TLS, encoding, and session management happen at the application level in practice.

---

**Q3. What is encapsulation in networking?**

Encapsulation is the process of adding a layer's header (and sometimes trailer) to the data passed down from the layer above, wrapping it in protocol-specific information.

Going down the stack: HTTP data → TCP adds header → IP adds header → Ethernet adds header + trailer → converted to bits on the wire.

At the receiver, each layer strips its header (de-encapsulation) and passes the payload up. This allows each layer to be independent — IP doesn't care what's inside the TCP segment; TCP doesn't care what's inside the HTTP message.

---

**Q4. What is the difference between a switch and a router?**

**Switch (L2)**: Operates at the Data Link layer. Forwards **frames** based on **MAC addresses**. Connects devices within the same network (LAN). Learns which MAC address is on which port and maintains a MAC address table. Does NOT modify IP addresses.

**Router (L3)**: Operates at the Network layer. Forwards **packets** based on **IP addresses**. Connects different networks. Maintains a routing table. Changes the source/destination MAC addresses at each hop (but IP addresses remain unchanged end-to-end).

---

**Q5. What is a PDU? Name the PDU at each TCP/IP layer.**

PDU (Protocol Data Unit) is the name for the data unit at each layer:
- Application: **Message** (or Data)
- Transport: **Segment** (TCP) or **Datagram** (UDP)
- Internet: **Packet** (IP Datagram)
- Network Access: **Frame** (Data Link) / **Bits** (Physical)

---

**Q6. Which layer does each device operate at: Hub, Switch, Router, Firewall?**

- **Hub**: Layer 1 (Physical) — broadcasts all bits to all ports
- **Switch**: Layer 2 (Data Link) — forwards frames by MAC address
- **Router**: Layer 3 (Network) — forwards packets by IP address
- **Firewall**: Layer 3–7 — basic firewalls at L3/L4, next-gen firewalls at L7 (inspect HTTP content)

---

## 🟡 Medium

**Q7. Walk through what happens when you type `http://example.com` and press Enter. Cover all layers.**

1. **DNS Resolution (App Layer)**: Browser resolves `example.com` → IP. Checks browser cache → OS cache → recursive resolver → root servers → TLD servers → authoritative servers → IP returned.

2. **TCP 3-way Handshake (Transport)**: Client sends SYN to port 80, server responds SYN-ACK, client sends ACK. Connection established.

3. **HTTP Request (App Layer)**: `GET / HTTP/1.1\r\nHost: example.com\r\n\r\n`

4. **Down the stack**: HTTP message → TCP segment (adds ports, seq#) → IP packet (adds source/dest IP) → Ethernet frame (adds source MAC, dest MAC of default gateway) → bits on wire.

5. **Routing (Network Layer)**: Each router strips the Ethernet frame, reads destination IP, forwards to next hop with new Ethernet headers for the next link.

6. **Server receives and responds**: De-encapsulates all the way up to HTTP, generates HTML response, sends back the same way.

7. **Browser renders**: Parses HTML, fetches resources, renders page.

---

**Q8. Why does the MAC address change at every router hop, but the IP address stays the same?**

IP addresses identify endpoints (source and destination hosts) — they don't change throughout the journey. Routers forward packets from network to network using IP addresses to determine the path.

MAC addresses identify nodes on a **single network segment** (a single link). When a packet crosses a router:
- The router strips the incoming frame (removes source MAC = router's incoming interface, destination MAC = router itself)
- The router creates a new frame with source MAC = router's outgoing interface, destination MAC = the next hop (next router or the final destination if on the same LAN)

Each hop gets a fresh frame wrapper for that specific link. The IP header (with original source and destination IPs) passes through unchanged. This is why your IP address represents your logical location globally, while MAC addresses are only locally meaningful.

---

**Q9. What is the purpose of TTL (Time To Live) in an IP packet?**

TTL is an 8-bit field in the IP header (initial value typically 64 or 128). Every router that forwards the packet decrements TTL by 1. If TTL reaches 0, the router discards the packet and sends an **ICMP "Time Exceeded"** message back to the sender.

**Purpose**: Prevents packets from looping forever in case of routing loops. Without TTL, a misconfigured routing loop would cause packets to circulate indefinitely, consuming bandwidth forever.

**Practical use**: `traceroute` exploits TTL — it sends packets with TTL=1 (first router responds with ICMP), then TTL=2 (second router responds), etc., mapping the entire path hop by hop.

---

**Q10. What is the difference between Layer 4 and Layer 7 load balancers?**

**Layer 4 (Transport) load balancer**: Routes based on IP address + TCP/UDP port. Cannot see the content of the request. Extremely fast (simple decision: which backend pool). Does not decrypt TLS — works with encrypted traffic as-is. Connection is multiplexed: client connects to LB, LB forwards to backend and maintains connection state.

**Layer 7 (Application) load balancer**: Decrypts TLS and reads HTTP headers, URL paths, cookies, and request body. Can make routing decisions based on content (route `/api/*` to API servers, `/static/*` to CDN, route based on `User-Agent`). Can do A/B testing, blue-green deployments, canary releases. More CPU-intensive (must handle TLS and parse HTTP).

Example: AWS ALB (Application Load Balancer) = L7. AWS NLB (Network Load Balancer) = L4.

---

## 🔴 Hard

**Q11. DNS resolution involves multiple server types. Explain the full recursive resolution process for a brand new query (nothing cached).**

1. **Client → Recursive Resolver** (provided by ISP or configured: 8.8.8.8, 1.1.1.1): Client asks "What is the IP of www.example.com?"

2. **Recursive Resolver → Root Name Servers** (13 logical root servers: a.root-servers.net through m.root-servers.net, actually hundreds of physical servers via anycast): "Who handles .com?" Root servers respond: "Ask the .com TLD servers at these IPs."

3. **Recursive Resolver → .com TLD Name Servers** (operated by Verisign): "Who handles example.com?" TLD server responds: "Ask the authoritative servers at ns1.example.com."

4. **Recursive Resolver → Authoritative Name Server** (example.com's own DNS server): "What is www.example.com?" Authoritative server responds: "142.250.x.x with TTL=300."

5. **Resolver → Client**: Returns the IP. Resolver caches the answer for 300 seconds (the TTL).

**Types of DNS records involved:**
- `NS` records: Which nameservers are authoritative for a domain
- `A` record: IPv4 address for a hostname
- `AAAA` record: IPv6 address
- `CNAME` record: Canonical name (alias — points to another hostname, not IP)

**Why only 13 root server IPs?** Because a DNS response must fit in a single 512-byte UDP packet. 13 IPv4 addresses fill that limit. Each "root server" is actually many physical machines worldwide sharing the same IP via **anycast routing** — your query goes to the nearest one.

---

**Q12. Explain the concept of anycast and how it's used for DNS and CDNs.**

**Unicast**: One specific machine has an IP address. Packets to that IP go to that specific machine.

**Anycast**: Multiple machines in different geographic locations share the same IP address. The network routes packets to whichever machine is "topologically closest" (fewest BGP hops). From different parts of the world, you reach different physical machines, all with the same IP.

**DNS Root Servers**: All 13 root server IPs (e.g., `198.41.0.4` for a.root-servers.net) are anycast. Your DNS query reaches the nearest root server automatically.

**CDNs (Cloudflare, Fastly)**: Cloudflare's IP `1.1.1.1` is anycast. A user in Tokyo reaches a Tokyo data center. A user in London reaches a London data center. Same IP, different machines. Content is cached globally.

**Benefits:**
- **Low latency**: Nearest node always serves you
- **DDoS resilience**: Attack traffic is spread across all anycast nodes globally — no single point overwhelmed
- **Automatic failover**: If one node goes down, traffic automatically routes to the next nearest node
