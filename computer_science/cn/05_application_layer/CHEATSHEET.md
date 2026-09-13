# Cheat Sheet — Application Layer

## HTTP Versions
| | HTTP/1.1 | HTTP/2 | HTTP/3 |
|-|---------|--------|--------|
| Transport | TCP | TCP | QUIC (UDP) |
| Multiplexing | ❌ | ✅ streams | ✅ independent streams |
| Header compression | ❌ | ✅ HPACK | ✅ QPACK |
| HOL blocking | HTTP + TCP | TCP only | ❌ None |
| Setup | 1RTT TCP + TLS | 1RTT TCP + TLS | 0-1 RTT |
| Encryption | Optional | Optional | Mandatory |

## HTTP Status Codes
| Range | Meaning | Key Codes |
|-------|---------|-----------|
| 1xx | Informational | 100 Continue |
| 2xx | Success | 200 OK, 201 Created, 204 No Content |
| 3xx | Redirect | 301 Permanent, 302 Temp, 304 Not Modified |
| 4xx | Client Error | 400 Bad Req, 401 Unauth, 403 Forbidden, 404, 429 Rate Limited |
| 5xx | Server Error | 500 Server Err, 502 Bad Gateway, 503 Unavailable, 504 Timeout |

```
401 = Not authenticated ("who are you?")
403 = Not authorized ("I know you, but you can't")
502 = Upstream sent bad response
503 = Server overloaded/down
504 = Upstream timed out
```

## HTTP Methods
| Method | Safe? | Idempotent? | Body? |
|--------|:-----:|:-----------:|:-----:|
| GET | ✅ | ✅ | ❌ |
| HEAD | ✅ | ✅ | ❌ |
| POST | ❌ | ❌ | ✅ |
| PUT | ❌ | ✅ | ✅ |
| PATCH | ❌ | ❌ | ✅ |
| DELETE | ❌ | ✅ | ❌ |
| OPTIONS | ✅ | ✅ | ❌ |

## Cache-Control Directives
```
max-age=N        Fresh for N seconds (no request)
no-cache         Can cache but must revalidate before use (→ 304)
no-store         Never cache (sensitive data)
public           CDNs can cache
private          Browser only (user-specific)
must-revalidate  Don't use stale even if offline
ETag + If-None-Match → 304 Not Modified if unchanged (saves body bandwidth)
```

## DNS Record Types
| Record | Maps | Example |
|--------|------|---------|
| A | hostname → IPv4 | `www.example.com → 1.2.3.4` |
| AAAA | hostname → IPv6 | `www.example.com → 2001:db8::1` |
| CNAME | alias → hostname | `blog.example.com → example.com` |
| MX | domain → mail server | priority + hostname |
| NS | domain → nameservers | authoritative nameserver |
| TXT | text data | SPF, DKIM, verification |
| PTR | IP → hostname | reverse DNS |
| SRV | service → host:port | `_http._tcp.example.com` |

## TLS 1.2 vs TLS 1.3
| | TLS 1.2 | TLS 1.3 |
|-|---------|---------|
| RTTs to complete | 2 | 1 (0-RTT resumption) |
| Forward secrecy | Optional | Mandatory |
| Key exchange | RSA or ECDHE | ECDHE only |
| Weak ciphers | Allowed | Removed |
| Certificate encrypted | ❌ | ✅ |

## TLS 1.3 Handshake (1 RTT)
```
→ ClientHello: version, cipher suites, random, key_share (ECDHE pub key)
← ServerHello: key_share + {Certificate + CertVerify + Finished}(encrypted)
→ Finished (encrypted)
[Application data flows]
```

## ECDHE Key Exchange
```
Both know: curve E, generator G
Client:  private a, public A = a×G  → sends A
Server:  private b, public B = b×G  → sends B
Shared:  client: a×B = ab×G
         server: b×A = ab×G
Attacker sees A, B but cannot recover a or b (discrete log problem)
```

## Cookie Security Attributes
```
HttpOnly   → JS cannot read (prevents XSS theft)
Secure     → HTTPS only (prevents plaintext interception)
SameSite=Strict → Not sent on cross-site requests (prevents CSRF)
SameSite=Lax    → Sent on navigations, not background (default)
SameSite=None   → Always sent cross-site (needs Secure)
Max-Age=N  → Expires after N seconds
```

## WebSockets
```
Client: HTTP GET with Upgrade: websocket
Server: 101 Switching Protocols
[Persistent full-duplex connection — both sides can push anytime]
Use: chat, live dashboards, games, collaborative editing
```

## Key Numbers
```
HTTP/1.1 default connections per origin: 6 (browser limit)
HTTP/2 streams per connection:           unlimited (server config)
TLS 1.3 handshake:                       1 RTT (0-RTT for resumption)
DNS UDP max payload (EDNS0):             4096 bytes
DNS TTL typical:                         300s (5 min) to 86400s (1 day)
Max cookie size:                         4096 bytes
Session ticket lifetime (TLS):           ~24 hours (server configured)
```
