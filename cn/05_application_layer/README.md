# Module 5: Application Layer — HTTP, DNS, TLS

---

## 1. HTTP — HyperText Transfer Protocol

HTTP is a **stateless, request-response** application layer protocol. A client (browser) sends requests; a server sends responses.

### HTTP/1.0 — One Request Per Connection

Each request opens a new TCP connection. After the response, the connection closes.

**Problem**: TCP 3-way handshake + TLS handshake for EVERY request. A web page with 50 resources (images, CSS, JS) = 50 TCP connections = huge overhead and latency.

### HTTP/1.1 — Persistent Connections + Pipelining

**Persistent connections** (`Connection: keep-alive`): TCP connection reused for multiple requests/responses. Eliminates repeated handshake overhead.

**Pipelining**: Client sends multiple requests without waiting for responses. Server processes them in order. In practice, pipelining was poorly implemented and disabled in most clients due to the **Head-of-Line (HOL) Blocking** problem: if request 1's response is large/slow, requests 2, 3, 4 wait — even if they could have been served instantly.

**HTTP/1.1 Request format:**
```
GET /index.html HTTP/1.1
Host: www.example.com
User-Agent: Mozilla/5.0 ...
Accept: text/html,application/xhtml+xml,...
Accept-Encoding: gzip, deflate, br
Cookie: session_id=abc123
Connection: keep-alive
\r\n
```

**HTTP/1.1 Response format:**
```
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
Content-Length: 1234
Cache-Control: max-age=3600
Set-Cookie: session_id=xyz; HttpOnly; Secure
Connection: keep-alive
\r\n
<html>...</html>
```

### HTTP/2 — Binary, Multiplexed, Header Compression

HTTP/2 (RFC 7540, 2015) was a major redesign to address HTTP/1.1's performance limitations.

**Key features:**

**1. Binary Framing**: HTTP/2 is a binary protocol (not human-readable text). Data is split into **frames** (the smallest unit of HTTP/2 communication). Frames have a type: HEADERS, DATA, SETTINGS, WINDOW_UPDATE, PUSH_PROMISE, etc.

**2. Streams and Multiplexing**: Multiple requests/responses are interleaved on a **single TCP connection** using **streams** (virtual channels identified by a stream ID). No head-of-line blocking at the HTTP layer — response to request 3 can be sent before response to request 1 if it's ready.

```
TCP Connection:
  [Stream 1: GET /image.jpg] ─┐
  [Stream 3: GET /style.css]  ├── Interleaved frames on one TCP connection
  [Stream 5: GET /script.js] ─┘
```

**3. HPACK Header Compression**: HTTP headers are repetitive (User-Agent, Accept, Cookie sent on every request). HPACK compresses headers using a dynamic table of previously seen headers. Reduces overhead dramatically for multiple requests.

**4. Server Push**: Server can proactively send resources the client will need before being asked. Client requests `/index.html`; server pushes `/style.css` and `/script.js` immediately, anticipating the client will request them after parsing the HTML. Controversial — in practice, often wastes bandwidth (client may already have them cached).

**5. Stream Prioritization**: Clients specify weights and dependencies between streams to guide server scheduling.

**HTTP/2 limitation**: Still uses TCP. A single TCP packet loss causes ALL streams to stall (TCP's HOL blocking now at the transport layer). Loss of one packet holds up all 100 multiplexed streams while TCP waits for retransmission.

### HTTP/3 — QUIC

HTTP/3 (RFC 9114, 2022) replaces TCP with **QUIC** (Quick UDP Internet Connections).

**Why QUIC?**
- TCP HOL blocking: one lost packet stalls all streams on the same TCP connection.
- Connection setup: TCP 3-way handshake + TLS 1.2 handshake = 2 RTTs before first byte. TLS 1.3 reduces to 1 RTT, but still requires TCP's handshake first.

**QUIC advantages:**
- **0-RTT or 1-RTT connection establishment**: Client includes TLS handshake data in the first packet. For resumed connections, can start sending data immediately (0-RTT).
- **Stream-level loss recovery**: Each QUIC stream is independently retransmitted. A packet loss on stream 1 doesn't block streams 2, 3, 4 — they continue independently.
- **Connection migration**: QUIC connections are identified by a **Connection ID** (not IP:port). If a mobile user switches from Wi-Fi to cellular (IP changes), the QUIC connection survives. TCP would die and need reconnection.
- **Encrypted by default**: QUIC encrypts ALL connection data (including headers) with TLS 1.3 built in. No unencrypted QUIC.

---

## 2. HTTP Status Codes

| Code | Meaning | Examples |
|------|---------|---------|
| **1xx** | Informational | 100 Continue |
| **2xx** | Success | 200 OK, 201 Created, 204 No Content |
| **3xx** | Redirection | 301 Moved Permanently, 302 Found, 304 Not Modified |
| **4xx** | Client Error | 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 429 Too Many Requests |
| **5xx** | Server Error | 500 Internal Server Error, 502 Bad Gateway, 503 Service Unavailable, 504 Gateway Timeout |

**Critical distinctions:**
- **401 vs 403**: 401 = not authenticated (no valid credentials provided). 403 = authenticated but not authorized (you're logged in, but don't have permission).
- **301 vs 302**: 301 = permanent redirect (browser AND search engines update). 302 = temporary (try original URL again next time).
- **502 vs 503 vs 504**: 502 = upstream server sent bad response. 503 = server overloaded/down. 504 = upstream server didn't respond in time.

---

## 3. HTTP Methods

| Method | Idempotent? | Safe? | Body? | Use |
|--------|:-----------:|:-----:|:-----:|-----|
| GET | ✅ | ✅ | ❌ | Retrieve resource |
| HEAD | ✅ | ✅ | ❌ | Like GET but no body (check headers) |
| POST | ❌ | ❌ | ✅ | Create resource, submit data |
| PUT | ✅ | ❌ | ✅ | Replace resource entirely |
| PATCH | ❌ | ❌ | ✅ | Partially update resource |
| DELETE | ✅ | ❌ | ❌ | Delete resource |
| OPTIONS | ✅ | ✅ | ❌ | List allowed methods (CORS preflight) |

**Idempotent**: Repeating the request N times has the same effect as once. PUT is idempotent (set to X), POST is not (creates a new resource each time).

**Safe**: No side effects, doesn't modify state. GET/HEAD are safe.

---

## 4. HTTP Caching

**Cache-Control header** directives:
- `max-age=3600`: Resource is fresh for 3600 seconds. No network request needed.
- `no-cache`: Must revalidate with server before using cached copy (but can still cache).
- `no-store`: Don't cache at all.
- `must-revalidate`: If stale, must revalidate; cannot use stale copy if offline.
- `public`: Can be cached by CDNs and shared caches.
- `private`: Only the browser can cache (not CDNs). For user-specific data.

**Revalidation (conditional requests)**:
- Server sends `ETag: "abc123"` or `Last-Modified: Wed, 1 Jan 2025 12:00:00 GMT`.
- Client sends `If-None-Match: "abc123"` or `If-Modified-Since: ...`
- If unchanged: server responds `304 Not Modified` (no body) — bandwidth saved.
- If changed: server responds `200 OK` with new content and new ETag.

---

## 5. DNS — Domain Name System

DNS is a hierarchical, distributed naming system that maps domain names to IP addresses.

### DNS Record Types

| Record | Purpose | Example |
|--------|---------|---------|
| **A** | Maps hostname → IPv4 address | `www.example.com → 1.2.3.4` |
| **AAAA** | Maps hostname → IPv6 address | `www.example.com → 2001:db8::1` |
| **CNAME** | Alias to another hostname | `blog.example.com → example.com` |
| **MX** | Mail server for domain | `example.com → mail.example.com` |
| **NS** | Authoritative nameservers for domain | `example.com → ns1.example.com` |
| **TXT** | Arbitrary text (SPF, DKIM, domain verification) | `v=spf1 include:...` |
| **PTR** | Reverse DNS (IP → hostname) | `1.2.3.4 → host.example.com` |
| **SOA** | Start of Authority (zone metadata) | Serial, refresh, retry, expire |
| **SRV** | Service location | `_http._tcp.example.com → host:port` |

### DNS over UDP vs TCP

**UDP (port 53)**: Used for normal DNS queries. Fast (no connection setup). If response > 512 bytes (EDNS0 can extend to 4096 bytes), or for zone transfers → use TCP.

**TCP (port 53)**: Used for zone transfers (AXFR) and large responses.

**DNS over HTTPS (DoH)**: DNS queries sent over HTTPS to a DoH resolver. Hides DNS queries from ISP eavesdropping. Used by Firefox, Chrome.

**DNS over TLS (DoT)**: DNS queries encrypted with TLS over port 853. Similar privacy benefit to DoH.

---

## 6. TLS — Transport Layer Security

TLS (the successor to SSL) provides **confidentiality, integrity, and authentication** for application layer communication. HTTPS = HTTP over TLS.

### TLS 1.2 Handshake (2 RTT)

```
Client                              Server
  │                                   │
  │── ClientHello ─────────────────→  │  Client: TLS version, cipher suites, random nonce (C)
  │                                   │
  │← ServerHello ─────────────────── │  Server: Chosen cipher suite, random nonce (S)
  │← Certificate ─────────────────── │  Server: X.509 certificate (public key inside)
  │← ServerKeyExchange (ECDHE) ────── │  Server: DH params for key exchange
  │← ServerHelloDone ──────────────── │
  │                                   │
  │── ClientKeyExchange ────────────→ │  Client: DH public key
  │── ChangeCipherSpec ─────────────→ │  "I'm switching to encrypted mode"
  │── Finished (encrypted) ─────────→ │  Hash of entire handshake (integrity check)
  │                                   │
  │← ChangeCipherSpec ────────────── │
  │← Finished (encrypted) ─────────── │
  │                                   │
  [Application data flows encrypted]
```

**Total: 2 RTT before first byte of application data (with TCP, it's 1 RTT TCP + 2 RTT TLS = 3 RTT total)**

### TLS 1.3 Handshake (1 RTT)

```
Client                              Server
  │── ClientHello ─────────────────→ │  Includes: key_share (DH params), supported groups
  │                                  │  Server immediately computes shared secret
  │← ServerHello ─────────────────── │  Server's key_share
  │← {Certificate, CertVerify,       │  Sent encrypted! (using handshake traffic keys)
  │    Finished} (encrypted) ──────── │
  │                                  │
  │── Finished (encrypted) ─────────→│  1 RTT done!
  │                                  │
  [Application data flows]
```

**TLS 1.3 improvements:**
- 1 RTT instead of 2 (fewer round trips before data)
- 0-RTT for session resumption (client sends data immediately using cached session ticket)
- Removed weak cipher suites (RSA key exchange, SHA-1, RC4, DES, 3DES)
- Forward secrecy mandatory (ECDHE only — see below)
- Encrypted certificates (can't see which server you're connecting to by sniffing)

### Certificate Verification

When the server sends its certificate, the client verifies:
1. **Signature**: The certificate is signed by a trusted Certificate Authority (CA) in the client's CA store.
2. **Chain of trust**: The certificate may be signed by an intermediate CA, which is signed by a root CA (in the client's trusted CA store).
3. **Expiry**: Certificate not expired.
4. **Hostname**: Certificate's CN or SAN (Subject Alternative Name) matches the hostname being connected to.
5. **Revocation**: Certificate not revoked (via OCSP or CRL).

### Key Exchange — ECDHE

Modern TLS uses **ECDHE (Elliptic Curve Diffie-Hellman Ephemeral)** for key exchange.

**DH principle**: Client and server both generate DH key pairs. They exchange public keys. Each can independently compute the same shared secret using their private key + the other's public key:
```
Client: private a, public A = g^a mod p
Server: private b, public B = g^b mod p
Shared: Client computes B^a = g^(ab) mod p
        Server computes A^b = g^(ab) mod p
```

**Why "Ephemeral"?** New key pairs generated for EVERY connection. The session key is never stored. Even if the server's long-term private key is compromised, past sessions cannot be decrypted — **forward secrecy**.

**ECDHE vs RSA**: RSA key exchange (now removed in TLS 1.3) encrypted the pre-master secret with the server's RSA public key. If the server's private key is ever stolen, an attacker who recorded past traffic can decrypt it retroactively. ECDHE prevents this.

---

## 7. HTTPS and How Encryption Works

After the TLS handshake, both sides have derived the same **session keys** (symmetric keys — typically AES-256-GCM or ChaCha20-Poly1305).

All subsequent HTTP data is encrypted:
```
Plaintext: GET /index.html HTTP/1.1\r\nHost: example.com\r\n\r\n
Encrypted: [gibberish bytes] -- sent over TCP
```

The receiver decrypts using the shared session key (same key, same AES algorithm, same IV counter). No one who intercepts the TCP stream can read the content without the session key.

**AES-GCM (Authenticated Encryption)**: Provides both confidentiality (AES encryption) AND integrity (GCM authentication tag). Any tampering with the ciphertext causes decryption failure.

---

## 8. Cookies and Sessions

**HTTP is stateless** — each request is independent. Cookies maintain state across requests.

**Cookie flow:**
1. Server sends: `Set-Cookie: session_id=abc123; HttpOnly; Secure; SameSite=Strict; Max-Age=3600`
2. Browser stores the cookie.
3. On subsequent requests to the same domain: `Cookie: session_id=abc123`
4. Server looks up `session_id` in its session store → identifies the user.

**Cookie attributes:**
- `HttpOnly`: Cookie not accessible via JavaScript (prevents XSS theft).
- `Secure`: Cookie only sent over HTTPS (prevents interception over HTTP).
- `SameSite=Strict`: Cookie not sent on cross-site requests (prevents CSRF).
- `SameSite=Lax`: Cookie sent on navigations but not on background requests.
- `Max-Age` / `Expires`: When the cookie expires. No Max-Age = session cookie (deleted when browser closes).

---

## 9. WebSockets

HTTP is request-response — server cannot push data to client without client asking. WebSockets upgrade an HTTP connection to a **full-duplex, persistent channel**.

**Upgrade handshake:**
```
Client → Server:
GET /chat HTTP/1.1
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==

Server → Client:
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

After the `101 Switching Protocols`, the TCP connection is now a WebSocket connection — both sides can send frames at any time, without waiting for a request.

**Use cases**: Chat applications, live dashboards, collaborative editing, online games, stock tickers.
