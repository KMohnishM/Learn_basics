# Q&A — Network Security

---

## 🟢 Easy

**Q1. What is the CIA triad in network security?**

- **Confidentiality**: Only authorized parties can access data. Provided by encryption (TLS, AES, VPN).
- **Integrity**: Data hasn't been tampered with. Provided by MACs (Message Authentication Codes), digital signatures, checksums.
- **Availability**: Systems are accessible when needed. Protected by DDoS mitigation, redundancy, failover.

These three properties are the foundation of all security design decisions.

---

**Q2. What is the difference between a stateless and stateful firewall?**

**Stateless (Packet filter)**: Examines each packet in isolation using source/dest IP, source/dest port, and protocol. Fast, simple. Cannot distinguish between a new unsolicited connection and a return packet for an established connection. Vulnerable to packet spoofing (e.g., sending an ACK packet bypasses rules that only check port numbers).

**Stateful**: Maintains a connection tracking table (state table). Knows which TCP sessions are established. Allows return traffic only for connections already in the state table. Blocks unsolicited inbound packets even if they match a port-based rule. More resource-intensive but far more secure.

---

**Q3. What is a VPN and how does it work at a high level?**

A VPN (Virtual Private Network) creates an encrypted tunnel between two endpoints over an untrusted network. All traffic inside the tunnel is encrypted — even if someone intercepts the packets on the public internet, they see only ciphertext.

High-level operation:
1. Client and VPN server authenticate each other.
2. They negotiate encryption keys (via IKE for IPSec, or TLS/WireGuard handshake).
3. All traffic is encrypted and encapsulated in a new packet addressed to the VPN server.
4. VPN server decrypts, removes encapsulation, forwards the original packet to the destination.
5. Return traffic is encrypted and sent back through the tunnel.

---

**Q4. What is a DDoS attack? Name three types.**

A DDoS (Distributed Denial of Service) attack uses many compromised machines (botnet) to overwhelm a target with traffic, making it unavailable.

Three types:
1. **Volumetric**: Flood the network link with traffic (UDP flood, ICMP flood). Goal: saturate bandwidth.
2. **Protocol**: Exploit protocol weaknesses (SYN flood exhausts connection table, Ping of Death overflows buffers).
3. **Application Layer (L7)**: Send legitimate-looking HTTP requests at high volume. Harder to filter because traffic looks real (HTTP flood, Slowloris).

---

**Q5. What is ARP spoofing and why is it dangerous?**

ARP spoofing: An attacker sends fake ARP replies to the LAN claiming "gateway IP is at MY_MAC." All devices on the LAN update their ARP cache and send traffic intended for the gateway to the attacker instead.

Dangerous because: The attacker becomes a Man-in-the-Middle — can read all unencrypted traffic, modify HTTP responses, inject malicious content, capture credentials, or silently forward traffic while recording everything.

Defense: Dynamic ARP Inspection (DAI) on managed switches — validates ARP against DHCP snooping table. Also: use TLS so even if intercepted, traffic is encrypted.

---

## 🟡 Medium

**Q6. Explain DNS amplification attacks. How much amplification is achievable?**

**How it works:**
1. Attacker sends small UDP DNS queries with the **victim's IP as source** (spoofed).
2. Open DNS resolvers receive the queries and send large DNS responses to the victim.
3. Victim is flooded with responses it never requested.

**Amplification factor**: The ratio of response size to query size.
- A 60-byte DNS query for `ANY` records can return a 3,000-byte response.
- Amplification factor = 3,000/60 = **50×**
- Attacker with 1Gbps botnet → generates 50Gbps at victim

**Historical record**: Cloudflare 2023: 71 million RPS. GitHub 2018 Memcached attack: **1.35 Tbps** (Memcached amplification factor: up to 50,000×).

**Defenses:**
- Ingress filtering (BCP38): ISPs drop packets with spoofed source IPs from their networks.
- Rate limiting DNS responses per source IP.
- Disable `ANY` query type responses on authoritative servers.
- Disable open DNS resolvers (only respond to authorized clients).

---

**Q7. What is IPSec tunnel mode vs transport mode? When is each used?**

**Transport mode**: Only the IP payload (TCP/UDP header + data) is encrypted/authenticated. The original IP header remains in plaintext.
```
[Original IP Header][ESP Header][TCP + Data (encrypted)][ESP Trailer]
```
Use: End-to-end encryption between two specific hosts. Both hosts must support IPSec. Used in host-to-host scenarios.

**Tunnel mode**: The **entire original IP packet** is encrypted and encapsulated in a new IP packet.
```
[New IP Header][ESP Header][Original IP Header + TCP + Data (encrypted)][ESP Trailer]
```
Use: Site-to-site VPNs. The VPN gateways know each other's IP (new header). The original internal IPs are hidden inside the encrypted payload.

**Key difference**: Tunnel mode hides the original source/destination IPs — an eavesdropper only sees VPN gateway IPs, not the actual hosts communicating.

---

**Q8. What is a Next-Generation Firewall (NGFW)? What additional capabilities does it have vs a stateful firewall?**

A stateful firewall makes decisions based on L3/L4 information (IP, port, connection state). It can't tell the difference between legitimate HTTPS and malware communicating on port 443.

**NGFW adds:**
1. **Application awareness (L7)**: Identifies applications regardless of port. "Block YouTube even over port 443."
2. **Deep Packet Inspection (DPI)**: Inspects packet content, not just headers.
3. **TLS inspection**: Acts as MITM proxy — decrypts TLS, inspects content, re-encrypts. Can detect malware hidden in encrypted traffic.
4. **IDS/IPS integration**: Matches traffic against attack signatures.
5. **User identity integration**: Apply policies based on user (via Active Directory), not just IP.
6. **URL filtering**: Block by category (gambling, social media).
7. **Threat intelligence feeds**: Block known malicious IPs/domains.

Trade-off: NGFW TLS inspection breaks end-to-end security and introduces a trusted proxy. Organizations must weigh monitoring benefit against privacy implications.

---

**Q9. What is HSTS and how does it protect against SSL stripping attacks?**

**SSL Stripping**: An attacker (MITM) intercepts the initial HTTP request to a site, communicates with the server over HTTPS (as a legitimate client), and serves the victim plain HTTP. The victim never knows the site should be HTTPS.

**HSTS (HTTP Strict Transport Security)**: The server sends a header: `Strict-Transport-Security: max-age=31536000; includeSubDomains`

This tells the browser: "For the next 31,536,000 seconds (1 year), NEVER connect to this domain over HTTP — always use HTTPS, even if the user types http:// or clicks an http:// link."

The browser stores this policy locally. On subsequent visits, the browser upgrades to HTTPS BEFORE any HTTP request goes out — the MITM never gets to intercept the initial HTTP request.

**HSTS Preload**: Browsers ship with a hardcoded list of domains that are HTTPS-only. Even the first visit is protected (no initial HTTP request). Submit at hstspreload.org.

**Limitation**: Only works after the first visit (TOFU — Trust on First Use). The first visit is still vulnerable if HSTS wasn't preloaded. That's why HSTS Preloading exists.

---

## 🔴 Hard

**Q10. Explain how a Slowloris DDoS attack works and why traditional defenses fail against it.**

**How Slowloris works:**
1. Attacker opens many TCP connections to the web server (legitimate-looking).
2. Each connection sends a partial HTTP request: `GET / HTTP/1.1\r\nHost: victim.com\r\n`
3. The request is never completed — attacker sends additional headers periodically (every ~10 seconds) to keep the connection alive: `X-a: b\r\n`
4. Web server waits for the complete request (it's never fully sent).
5. With enough connections, the server's connection pool is exhausted.
6. Legitimate requests can't connect — server appears down.

**Why traditional defenses fail:**
- **No traffic volume**: Only a few KB/s of traffic. Volumetric DDoS filters don't trigger.
- **Legitimate-looking**: Each connection looks like a slow but valid HTTP client. Packet content is proper HTTP.
- **No attack signatures**: No flood, no malformed packets.

**Defenses:**
1. **Connection timeout**: Configure the web server to close connections that don't complete an HTTP request within a timeout (e.g., 10 seconds).
2. **Rate limiting connections per IP**: Limit how many simultaneous connections each IP can hold open.
3. **Reverse proxy** (nginx, Cloudflare): Accept the TCP connection, buffer the slow request, only forward to backend when complete. Backend never sees Slowloris.
4. **Load balancer** with connection rate limits: Cloudflare and CDNs detect and block this automatically.

---

**Q11. Compare Zero Trust architecture with traditional perimeter-based security. Give concrete examples of controls in each.**

**Traditional perimeter model:**
- Assumption: "Everything inside the corporate network is safe; everything outside is dangerous."
- Controls: Strong perimeter firewall, VPN for remote access, open access between internal systems.
- Problem: Once an attacker gets inside (phishing, compromised laptop, malicious insider), they can move laterally freely — flat internal network means they can reach any system.

**Zero Trust model:**
- Assumption: "The internal network is already compromised. Trust nothing by default."
- Every access request must be verified regardless of network location.

**Concrete Zero Trust controls:**
1. **Identity verification**: Every resource access requires authentication (multi-factor). Even internal microservices authenticate to each other via mutual TLS or service tokens.
2. **Least privilege**: User gets only the specific permissions needed for their current task. No "admin on everything" accounts.
3. **Device health checks**: Enforce that the device is managed, patched, and has endpoint protection before allowing access. Unmanaged BYOD devices can't access sensitive resources.
4. **Microsegmentation**: Network is divided into small zones; each service communicates only with explicitly permitted services. A compromised web server cannot reach the payment database.
5. **Continuous monitoring**: All access is logged. Anomalies trigger re-authentication or access revocation.
6. **Encrypted everywhere**: All internal traffic uses TLS (not just internet-facing). Prevents internal sniffing.

**Real-world implementation**: Google's BeyondCorp moved away from VPN — engineers access internal tools from any network (café, home) with strong identity and device verification. Location inside the corporate network grants no implicit trust.
