# Module 6: Network Security

---

## 1. Security Goals — CIA Triad

Every security mechanism exists to protect one or more of these properties:

- **Confidentiality**: Data is accessible only to authorized parties. (Encryption provides this.)
- **Integrity**: Data has not been tampered with in transit or at rest. (MACs, digital signatures, CRC provide this.)
- **Availability**: Systems and data are accessible when needed. (DDoS protection, redundancy provide this.)

Additional properties:
- **Authentication**: Verifying the identity of a party (who you are).
- **Non-repudiation**: A sender cannot deny having sent a message (digital signatures provide this).
- **Authorization**: Verifying what an authenticated party is allowed to do (RBAC, ACLs).

---

## 2. Common Network Attacks

### Passive Attacks (eavesdropping — no modification)

**Packet Sniffing**: Capturing network traffic on a shared medium (Wi-Fi, hub-based networks). Tools: Wireshark, tcpdump. Defense: Encryption (TLS, VPN).

**Traffic Analysis**: Even with encryption, an attacker can observe which hosts communicate, how often, and how much data — revealing patterns. Defense: VPN, Tor (hides traffic patterns).

### Active Attacks (modify or inject traffic)

**Man-in-the-Middle (MITM)**: Attacker positions between two communicating parties, relaying and potentially modifying traffic. Enabled by ARP spoofing, DNS spoofing, rogue Wi-Fi hotspots. Defense: TLS certificate pinning, HSTS.

**ARP Spoofing**: Attacker broadcasts fake ARP replies associating their MAC with the gateway IP. All LAN traffic goes through the attacker. Defense: Dynamic ARP Inspection (DAI), 802.1X.

**DNS Spoofing (DNS Cache Poisoning)**: Attacker injects fake DNS responses into a resolver's cache. Victims resolve a domain to the attacker's IP. Defense: DNSSEC (signed DNS records).

**SYN Flood**: Flood server with SYN packets (spoofed IPs) to exhaust the half-open connection table. Defense: SYN cookies, rate limiting.

**IP Spoofing**: Sending packets with a forged source IP. Routers using ingress filtering (BCP38/RFC 2827) block packets whose source IP doesn't match the expected range for that interface. Defense: uRPF (Unicast Reverse Path Forwarding).

---

## 3. DDoS — Distributed Denial of Service

A DDoS attack overwhelms a target's resources (bandwidth, CPU, connection table) using traffic from thousands of compromised machines (a botnet).

### Attack Types

**Volumetric attacks**: Flood the target with massive traffic (Gbps–Tbps). Goal: saturate the network link. Examples: UDP flood, ICMP flood, amplification attacks.

**Amplification attacks**: Exploit protocols with high response-to-request ratios. Attacker sends small requests with spoofed source IP = victim's IP. Servers send large responses to the victim.

```
DNS amplification:
  60-byte UDP DNS query → 3,000-byte response = 50× amplification
  With 100,000 DNS servers: 6MB/s of queries → 300MB/s at victim

NTP amplification: monlist command → up to 4,000× amplification
Memcached amplification: up to 50,000× amplification (2018 GitHub attack: 1.35 Tbps)
```

**Protocol attacks**: Exploit TCP/IP weaknesses. SYN flood exhausts server connection state. Ping of Death: oversized ICMP packet causes buffer overflow.

**Application-layer (L7) attacks**: Send legitimate-looking HTTP requests. Harder to filter (looks like real traffic). Examples: HTTP flood (GET/POST flood), Slowloris (keeps connections open with partial requests).

### DDoS Defenses

**Upstream scrubbing**: Traffic routed through a scrubbing center (Cloudflare, Akamai) that filters attack traffic and passes clean traffic to the origin.

**Anycast diffusion**: CDN spreads attack traffic across hundreds of PoPs globally — no single point overwhelmed.

**Rate limiting**: Limit requests per IP per second. Penalizes heavy users.

**CAPTCHA / Bot detection**: Distinguish humans from bots.

**Blackholing**: Route attack traffic to null (drop). Protects network infrastructure at the cost of taking the targeted IP offline.

---

## 4. Firewalls

A firewall is a network security device that monitors and controls incoming/outgoing traffic based on rules.

### Packet Filter (Stateless Firewall — L3/L4)

Inspects each packet in isolation: source IP, destination IP, source port, destination port, protocol. Decision: allow or deny.

```
Rule example:
ALLOW TCP any:any → 10.0.0.1:80
ALLOW TCP any:any → 10.0.0.1:443
DENY  ALL
```

**Problem**: No awareness of connection state. Cannot tell if a TCP packet is part of an established connection or a new unsolicited connection. An attacker could forge a packet with ACK flag to bypass rules.

### Stateful Packet Inspection (Stateful Firewall — L4)

Maintains a **connection tracking table** (state table). Knows which TCP connections are established. Incoming packet is cross-referenced against the state table.

```
Connection table entry:
  {srcIP, srcPort, dstIP, dstPort, protocol, state, timeout}
  
  Only allows return traffic for connections initiated from the trusted side.
  Blocks unsolicited inbound connections.
```

This allows rules like "allow established connections" without explicitly permitting all responses.

### Next-Generation Firewall (NGFW — L7)

Inspects actual application content (deep packet inspection). Can:
- Identify applications regardless of port (e.g., skype over port 443)
- Block specific URLs or content categories
- Decrypt and inspect TLS traffic (TLS inspection/interception)
- Apply IDS/IPS signatures
- User-based policies (block social media for employees but allow for marketing)

**TLS inspection controversy**: NGFW acts as a MITM proxy — decrypts TLS, inspects, re-encrypts. Breaks end-to-end security model. Requires trust in the NGFW's certificate.

---

## 5. IDS vs IPS

**IDS (Intrusion Detection System)**: Monitors traffic, **alerts** on suspicious activity. Passive — doesn't block. Deployed out-of-band (traffic mirrored to IDS).

**IPS (Intrusion Prevention System)**: Monitors traffic, **blocks** suspicious activity in real-time. Deployed in-line (traffic passes through IPS). Higher performance requirements (must not become a bottleneck).

**Detection methods:**
- **Signature-based**: Compare traffic against a database of known attack patterns. Fast, high precision. Cannot detect zero-day attacks.
- **Anomaly-based**: Build a baseline of normal traffic; alert on deviations. Can detect novel attacks but high false positives.
- **Behavioral analysis**: ML-based detection of unusual patterns.

---

## 6. VPN — Virtual Private Network

A VPN creates an **encrypted tunnel** between two endpoints over an untrusted network (the public internet).

### Types of VPN

**Remote Access VPN**: An individual user connects to a corporate network over the internet as if they were physically in the office. VPN client software on the user's device; VPN gateway at the corporate network edge.

**Site-to-Site VPN**: Connects two offices (networks) permanently over the internet. Traffic between offices is encrypted in the VPN tunnel; users don't need individual VPN clients.

### VPN Protocols

**IPSec (IP Security)**: Suite of protocols for authenticating and encrypting IP packets. Operates at L3 — transparent to applications. Two modes:
- **Transport mode**: Only the IP payload (L4+) is encrypted. Original IP header unchanged. Used for end-to-end encryption between hosts.
- **Tunnel mode**: The entire original IP packet is encrypted and encapsulated in a new IP packet. Used for site-to-site VPNs (original packet hidden; new IP header routes the tunnel).

IPSec components:
- **AH (Authentication Header)**: Provides authentication and integrity. No encryption.
- **ESP (Encapsulating Security Payload)**: Provides authentication, integrity, AND encryption. Most commonly used.
- **IKE (Internet Key Exchange)**: Negotiates security associations (SAs) — the keys and algorithms to use.

**WireGuard**: Modern VPN protocol. Simple (4,000 lines of code vs OpenVPN's 100,000+). Fast (kernel-space implementation). Strong cryptography (ChaCha20, Curve25519). Stateless design simplifies NAT traversal.

**OpenVPN**: Open-source, runs over UDP or TCP. Uses TLS for key exchange. Very compatible but complex.

**TLS/SSL VPN (e.g., Cisco AnyConnect)**: Uses TLS — traverses firewalls easily (port 443). Works without special client software (browser-based access).

### VPN Split Tunneling

**Full tunnel**: All traffic (including personal browsing) routes through the VPN. Maximum security; VPN gateway sees all traffic.

**Split tunnel**: Only corporate traffic routes through VPN; personal traffic goes directly to the internet. Reduces VPN load; better performance.

---

## 7. DNSSEC — DNS Security Extensions

**Problem**: DNS responses are unauthenticated. An attacker can forge DNS responses (cache poisoning). 

**DNSSEC** adds digital signatures to DNS records. Each DNS zone signs its records with its private key. Validators can verify the signature using the zone's public key (which is itself signed by the parent zone — chain of trust up to the root).

**DNSSEC record types:**
- **RRSIG**: Digital signature over a record set.
- **DNSKEY**: Zone's public key.
- **DS (Delegation Signer)**: Hash of the child zone's DNSKEY, stored in the parent zone. Creates the chain of trust.
- **NSEC/NSEC3**: Authenticated denial of existence (proves a name doesn't exist).

**Limitation**: DNSSEC authenticates DNS data but doesn't encrypt it. DNS queries and responses are still visible to observers (solved by DoH/DoT).

---

## 8. Network Security Best Practices

### Zero Trust Architecture

Traditional security: "Trust everything inside the perimeter (corporate network), distrust everything outside." Once inside, lateral movement is easy.

**Zero Trust**: "Never trust, always verify." Every request is authenticated and authorized regardless of network location. Assume the internal network is compromised.

Principles:
- Verify explicitly (authenticate and authorize every request)
- Use least privilege (minimum access required for each role)
- Assume breach (design for containment, not prevention)

### Defense in Depth

Layered security — multiple controls at different layers. A breach at one layer doesn't compromise the entire system.

```
Layer 1: Perimeter firewall (blocks external attacks)
Layer 2: Network segmentation / VLANs (limits lateral movement)
Layer 3: Host-based firewall (on each server)
Layer 4: Application security (input validation, authentication)
Layer 5: Data encryption (at rest and in transit)
Layer 6: Monitoring and logging (detect and respond)
```

### Common Protections by Attack Type

| Attack | Defense |
|--------|---------|
| Packet sniffing | TLS/VPN encryption |
| ARP spoofing | Dynamic ARP Inspection, 802.1X |
| DNS spoofing | DNSSEC, DoH, DoT |
| SYN flood | SYN cookies, rate limiting |
| DDoS volumetric | Anycast scrubbing (Cloudflare, Akamai) |
| MITM | TLS certificate validation, HSTS, cert pinning |
| SQL injection | Parameterized queries, WAF |
| XSS | CSP (Content Security Policy), HttpOnly cookies |
| CSRF | SameSite cookies, CSRF tokens |
