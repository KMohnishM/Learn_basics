# Cheat Sheet — Network Security

## CIA Triad
| Property | Definition | Mechanism |
|----------|------------|-----------|
| **Confidentiality** | Data only accessible to authorized | Encryption (TLS, AES, VPN) |
| **Integrity** | Data not tampered with | MACs, digital signatures, HMAC |
| **Availability** | System accessible when needed | DDoS protection, redundancy |

## Attack Types Quick Reference
| Attack | Target | Mechanism | Defense |
|--------|--------|-----------|---------|
| Packet sniffing | Confidentiality | Capture unencrypted traffic | TLS, VPN |
| ARP spoofing | Integrity (routing) | Fake ARP replies → MITM | DAI, 802.1X |
| DNS poisoning | Integrity (naming) | Inject fake DNS responses | DNSSEC, DoH |
| SYN flood | Availability | Exhaust half-open connections | SYN cookies, rate limit |
| DDoS volumetric | Availability | Saturate bandwidth | Anycast scrubbing |
| DNS amplification | Availability | 50×–50,000× amplification | BCP38, disable open resolvers |
| SSL stripping | Confidentiality | Downgrade HTTPS to HTTP | HSTS, HSTS preload |
| Slowloris | Availability | Exhaust connection pool | Timeouts, reverse proxy |

## Firewall Types
| Type | Operates at | State? | What it sees |
|------|------------|:------:|-------------|
| Packet filter | L3/L4 | ❌ | IP, port, protocol |
| Stateful | L4 | ✅ | + connection state |
| NGFW | L7 | ✅ | + application content, user, URL |

## DDoS Amplification Factors
| Protocol | Query Size | Response Size | Amplification |
|----------|:----------:|:-------------:|:-------------:|
| DNS (ANY) | 60 B | 3,000 B | ~50× |
| NTP (monlist) | 8 B | 48,000 B | ~6,000× |
| Memcached | 15 B | 750,000 B | ~50,000× |

## IPSec Modes
```
Transport mode:
  [IP Header][ESP][L4 + Data (encrypted)][ESP Trailer]
  Use: Host-to-host (both endpoints must support IPSec)

Tunnel mode:
  [New IP Header][ESP][Original IP + L4 + Data (encrypted)][ESP Trailer]
  Use: Site-to-site VPN (gateways hide internal IPs)

AH: Authentication only (no encryption)
ESP: Authentication + Encryption (most used)
IKE: Key negotiation for IPSec
```

## VPN Protocol Comparison
| Protocol | Layer | Transport | Speed | Complexity |
|----------|-------|-----------|-------|-----------|
| IPSec | L3 | IP | Fast | Complex |
| WireGuard | L3 | UDP | Fastest | Simple (4K LOC) |
| OpenVPN | L4 | UDP/TCP | Medium | Complex |
| TLS VPN | L4/7 | TCP/443 | Medium | Easiest (NAT friendly) |

## HSTS
```
Header: Strict-Transport-Security: max-age=31536000; includeSubDomains
Effect: Browser NEVER sends HTTP to this domain for 1 year
Preload: Submit to browsers' hardcoded list (protects first visit too)
Prevents: SSL stripping attacks (MITM can't downgrade to HTTP)
```

## Zero Trust vs Perimeter
| | Perimeter | Zero Trust |
|-|-----------|-----------|
| Default trust | Internal = trusted | Nothing trusted |
| Verification | At network entry | Every request |
| Lateral movement risk | High (open internal) | Low (microsegmentation) |
| Remote work | VPN required | Device health check + MFA |
| Control plane | Network location | Identity + device state |

## Defense in Depth Layers
```
1. Perimeter firewall    (block external attacks)
2. Network segmentation  (VLANs, microsegmentation — limit lateral movement)
3. Host firewall         (per-server protection)
4. Application security  (auth, input validation)
5. Data encryption       (TLS in transit, AES at rest)
6. Monitoring/logging    (detect & respond — SIEM)
```

## Common Protections Mapping
```
XSS         → HttpOnly cookies, CSP headers, input sanitization
CSRF        → SameSite cookies, CSRF tokens
SQL injection → Parameterized queries, WAF
MITM        → TLS + HSTS + Certificate pinning
Brute force → Account lockout, rate limiting, MFA
```

## Key Security Headers (HTTP)
```
Strict-Transport-Security  → HSTS (force HTTPS)
Content-Security-Policy    → Prevent XSS (whitelist script sources)
X-Frame-Options            → Prevent clickjacking (DENY / SAMEORIGIN)
X-Content-Type-Options     → nosniff (prevent MIME sniffing)
Referrer-Policy            → Control referrer header
```
