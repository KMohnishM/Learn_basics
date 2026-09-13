# Module 1: OSI & TCP/IP Models

---

## 1. Why Layered Models?

Networks are extraordinarily complex. A message traveling from your browser to a server in another country crosses cables, switches, routers, fiber, satellites, and dozens of software components. Without a structured model, every component would need to know about every other component — impossible to build and impossible to change.

**Layered models** solve this by dividing the problem into discrete layers where:
- Each layer provides services to the layer above it
- Each layer uses services from the layer below it
- Each layer communicates only with its adjacent layers
- Peer layers on two different hosts communicate through a common protocol

**Benefits:**
- **Modularity**: Change one layer's implementation without affecting others (e.g., switch from Ethernet to Wi-Fi — upper layers don't care)
- **Interoperability**: Different vendors implement the same layer, they interoperate
- **Easier troubleshooting**: Isolate which layer has a problem

---

## 2. The OSI Model — 7 Layers

The **Open Systems Interconnection** model was developed by ISO in 1984. It's primarily a conceptual framework — not implemented exactly in real systems — but universally used as a reference for understanding and troubleshooting networks.

```
Layer 7 — Application     ← HTTP, FTP, SMTP, DNS, SSH
Layer 6 — Presentation    ← Encryption, compression, encoding (SSL/TLS conceptually)
Layer 5 — Session         ← Session management, synchronization (NetBIOS, RPC)
Layer 4 — Transport       ← TCP, UDP (end-to-end communication, ports)
Layer 3 — Network         ← IP, ICMP, routing (logical addressing)
Layer 2 — Data Link       ← Ethernet, Wi-Fi, MAC addresses, frames
Layer 1 — Physical        ← Bits on wire (cables, radio signals, fiber)
```

**Mnemonic**: "**A**ll **P**eople **S**eem **T**o **N**eed **D**ata **P**rocessing" (top to bottom) or "**P**lease **D**o **N**ot **T**hrow **S**ausage **P**izza **A**way" (bottom to top).

### Layer Details

**Layer 7 — Application**: User-facing protocols. Defines the rules for communication between applications. Examples: HTTP (web), SMTP (email), FTP (file transfer), DNS (name resolution), SSH (remote shell).

**Layer 6 — Presentation**: Data format translation, encryption/decryption, compression. Ensures that data sent from one system's Application layer can be read by another's. In practice, this is often merged into Layer 7 (TLS handles encryption at this level but is often considered part of Application).

**Layer 5 — Session**: Manages sessions (logical connections) between applications — establishment, maintenance, and termination. Handles synchronization (checkpoints in long transfers so you can resume). In practice, largely absorbed into Layer 4 (TCP) and Layer 7.

**Layer 4 — Transport**: End-to-end communication between processes. Multiplexes multiple connections using port numbers. Provides error detection, retransmission, flow control. Key protocols: TCP (reliable) and UDP (unreliable but fast).

**Layer 3 — Network**: Logical (IP) addressing and routing — determining the path data takes across interconnected networks. Devices: Routers (operate at L3). Key protocols: IP, ICMP, routing protocols (OSPF, BGP).

**Layer 2 — Data Link**: Physical addressing (MAC addresses) and framing. Responsible for node-to-node delivery on the same network segment. Handles error detection within a link. Sublayers: LLC (Logical Link Control) and MAC (Media Access Control). Devices: Switches (operate at L2). Key protocols: Ethernet, Wi-Fi (802.11), ARP.

**Layer 1 — Physical**: Raw bit transmission — converting bits to electrical signals, light pulses, or radio waves. Defines cable types, voltages, frequencies, connector shapes. Devices: Hubs, repeaters, cables, NICs.

---

## 3. Data Encapsulation — How Data Travels Down the Stack

When you send an HTTP request, it doesn't just get sent as-is. Each layer adds its own header (and sometimes trailer):

```
Application Layer:
  HTTP Request: "GET /index.html HTTP/1.1\r\nHost: example.com\r\n\r\n"

Transport Layer (TCP):
  TCP Header + HTTP data = TCP Segment
  TCP Header contains: source port, destination port, sequence number, etc.

Network Layer (IP):
  IP Header + TCP Segment = IP Packet (Datagram)
  IP Header contains: source IP, destination IP, TTL, protocol, etc.

Data Link Layer (Ethernet):
  Ethernet Header + IP Packet + Ethernet Trailer = Ethernet Frame
  Ethernet Header: source MAC, destination MAC, EtherType
  Ethernet Trailer: CRC checksum (Frame Check Sequence)

Physical Layer:
  Ethernet Frame converted to electrical signals / radio waves / light pulses
```

**At the receiver**, the process is reversed: each layer strips its header, processes it, and passes the remaining data up to the next layer (de-encapsulation).

---

## 4. The TCP/IP Model — What's Actually Implemented

The TCP/IP model (also called the Internet model or DoD model) is what the internet actually runs on. It's a practical model with 4 layers (some texts say 5):

```
Layer 4 — Application      ← HTTP, DNS, SMTP, FTP, SSH, TLS (combines OSI 5+6+7)
Layer 3 — Transport        ← TCP, UDP (same as OSI Layer 4)
Layer 2 — Internet         ← IP, ICMP, routing (same as OSI Layer 3)
Layer 1 — Network Access   ← Ethernet, Wi-Fi, ARP (combines OSI 1+2)
```

The TCP/IP model doesn't separate Session and Presentation layers — they're merged into Application. This reflects reality: TLS/SSL, session management, and encoding are all done at the application level by developers, not as separate OS abstractions.

---

## 5. OSI vs TCP/IP Comparison

| OSI Layer | TCP/IP Layer | Real Protocols |
|-----------|-------------|----------------|
| 7 Application | Application | HTTP, HTTPS, FTP, SMTP, SSH, DNS |
| 6 Presentation | Application | TLS/SSL, MIME encoding, compression |
| 5 Session | Application | Session cookies, NetBIOS, RPC |
| 4 Transport | Transport | TCP, UDP, SCTP |
| 3 Network | Internet | IPv4, IPv6, ICMP, OSPF, BGP |
| 2 Data Link | Network Access | Ethernet, Wi-Fi (802.11), PPP, ARP |
| 1 Physical | Network Access | Cables, fiber, radio, NIC hardware |

---

## 6. What Happens When You Type a URL — End to End

This is the canonical question that ties all layers together. Typing `https://www.google.com/search?q=os` and pressing Enter triggers:

### Step 1: URL Parsing (Application Layer)
- Browser parses: scheme=`https`, host=`www.google.com`, path=`/search`, query=`q=os`

### Step 2: DNS Resolution (Application Layer → all the way down)
- Browser checks its DNS cache. Not found.
- OS checks its DNS cache (`/etc/hosts` on Linux, `ipconfig /displaydns` on Windows). Not found.
- OS queries the **recursive resolver** (usually provided by ISP or configured manually: 8.8.8.8 for Google, 1.1.1.1 for Cloudflare).
- Recursive resolver queries:
  1. **Root name server** → "Who handles .com?" → directs to `.com` TLD servers
  2. **TLD name server (.com)** → "Who handles google.com?" → directs to Google's authoritative servers
  3. **Authoritative name server (google.com)** → returns IP address: `142.250.x.x`
- Answer returned through the chain, each hop caches the result for the TTL (Time To Live).

### Step 3: TCP Connection (Transport Layer)
- Browser initiates TCP 3-way handshake with `142.250.x.x:443`:
  - Client → Server: SYN (synchronize, my sequence starts at X)
  - Server → Client: SYN-ACK (acknowledge X, my sequence starts at Y)
  - Client → Server: ACK (acknowledge Y)
- Connection established.

### Step 4: TLS Handshake (Application Layer / Presentation)
- For HTTPS, a TLS handshake occurs over the TCP connection:
  - Client Hello: TLS version, supported cipher suites, random nonce
  - Server Hello: Chosen cipher suite, server's random nonce, server's digital certificate
  - Client verifies certificate against trusted CA store
  - Key exchange (ECDHE): establishes shared secret → derives symmetric encryption keys
  - Both sides exchange "Finished" messages encrypted with the new keys
- Subsequent data is encrypted (AES-GCM or similar).

### Step 5: HTTP Request (Application Layer)
```
GET /search?q=os HTTP/2
Host: www.google.com
User-Agent: Mozilla/5.0 ...
Accept: text/html,...
Cookie: ...
```

### Step 6: Data Travels Through the Stack
- HTTP request → TCP segment (Layer 4: adds ports, sequence numbers)
- TCP segment → IP packet (Layer 3: adds source IP, destination IP, TTL)
- IP packet → Ethernet frame (Layer 2: adds source MAC, destination MAC)
  - MAC address is of the **default gateway** (router), not Google's server
- Frame → electrical/radio/optical signals (Layer 1)

### Step 7: Routing Across the Internet (Network Layer)
- Your router receives the frame, strips the Ethernet header, reads the IP destination.
- Router looks up `142.250.x.x` in its routing table → forwards to the next hop.
- This repeats across dozens of routers (each one strips and re-adds Ethernet headers with new source/destination MACs for each link).
- At each router, the IP packet's TTL is decremented by 1. If it reaches 0, the packet is discarded and an ICMP "Time Exceeded" message is sent back.

### Step 8: Server Processing and Response
- Google's load balancer receives the TCP connection.
- Request is routed to an appropriate backend server.
- Server generates the HTML response.
- Response travels back through the same stack (in reverse) to your browser.

### Step 9: Rendering
- Browser receives the HTTP response, parses HTML, fetches additional resources (CSS, JS, images — each potentially new TCP/TLS connections or HTTP/2 multiplexed streams), and renders the page.

---

## 7. Protocol Data Units (PDUs)

Each layer has a specific name for its unit of data:

| Layer | PDU Name | Contains |
|-------|----------|---------|
| Application | Message / Data | Application payload |
| Transport | Segment (TCP) / Datagram (UDP) | Transport header + data |
| Network | Packet (IP Datagram) | IP header + segment |
| Data Link | Frame | L2 header + packet + trailer |
| Physical | Bits | Raw 0s and 1s |

---

## 8. Devices and the Layers They Operate At

| Device | Layer | Function |
|--------|-------|---------|
| Hub | Physical (L1) | Broadcasts all frames to all ports. Dumb signal repeater. |
| Switch | Data Link (L2) | Forwards frames based on MAC address table. Learns MAC→port mappings. |
| Router | Network (L3) | Forwards packets based on IP routing table. Connects different networks. |
| Firewall | L3–L7 | Filters packets based on rules. Stateful firewalls track TCP sessions (L4). Next-gen firewalls inspect application data (L7). |
| Load Balancer | L4 or L7 | L4: distributes TCP connections. L7: distributes HTTP requests based on URL/headers. |
| Gateway | L7 | Protocol translation (e.g., HTTP to gRPC). |
| NIC | Physical + Data Link | Converts data to signals (L1) and handles MAC addressing (L2). |

---

## 9. Important Port Numbers to Know

| Port | Protocol | Service |
|------|----------|---------|
| 20, 21 | TCP | FTP (data, control) |
| 22 | TCP | SSH |
| 23 | TCP | Telnet (unencrypted — never use) |
| 25 | TCP | SMTP (email sending) |
| 53 | TCP + UDP | DNS |
| 67, 68 | UDP | DHCP (server, client) |
| 80 | TCP | HTTP |
| 110 | TCP | POP3 (email retrieval) |
| 143 | TCP | IMAP (email retrieval) |
| 443 | TCP | HTTPS (HTTP over TLS) |
| 465/587 | TCP | SMTP with TLS |
| 3306 | TCP | MySQL |
| 5432 | TCP | PostgreSQL |
| 6379 | TCP | Redis |
| 27017 | TCP | MongoDB |

Well-known ports: 0–1023 (require root on Unix). Registered ports: 1024–49151. Ephemeral (dynamic) ports: 49152–65535 (used by clients for source ports).
