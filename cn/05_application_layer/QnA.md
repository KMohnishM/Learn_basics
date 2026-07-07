# Q&A — Application Layer

---

## 🟢 Easy

**Q1. What are the key differences between HTTP/1.1, HTTP/2, and HTTP/3?**

| | HTTP/1.1 | HTTP/2 | HTTP/3 |
|-|---------|--------|--------|
| Transport | TCP | TCP | QUIC (UDP) |
| Multiplexing | ❌ (HOL blocking) | ✅ (streams) | ✅ (independent streams) |
| Header compression | ❌ | ✅ HPACK | ✅ QPACK |
| Encryption | Optional | Optional (de facto TLS) | Mandatory (TLS 1.3 built-in) |
| Connection setup | 1 RTT TCP + TLS | 1 RTT TCP + TLS | 0-1 RTT |
| HOL blocking | HTTP + TCP | TCP only | ❌ None |

---

**Q2. What is the difference between 401 and 403?**

- **401 Unauthorized**: The request lacks valid authentication credentials. You are not authenticated. The server is saying "prove who you are." Example: accessing an API without a token.
- **403 Forbidden**: The server knows who you are (authentication succeeded or not needed), but you don't have permission. Example: authenticated user trying to access admin-only resource.

---

**Q3. What is the difference between GET and POST?**

**GET**: Retrieves a resource. No request body. Parameters in the URL. Idempotent and safe (no side effects). Cacheable. Bookmarkable.

**POST**: Submits data to create/process a resource. Has a request body. Not idempotent (each call may create a new resource). Not cached by default.

Rule: GET for reading, POST for creating/writing.

---

**Q4. What is a CNAME record? How does it differ from an A record?**

**A record**: Maps a hostname directly to an IPv4 address. `www.example.com → 1.2.3.4`

**CNAME record**: Creates an alias — maps one hostname to another hostname. `blog.example.com → example.com` (then example.com has an A record to the IP).

CNAME is useful for pointing multiple names to the same host without duplicating A records. Changing the IP requires only updating the A record; all CNAMEs automatically follow. CNAME cannot coexist with other records for the same name (no CNAME at a zone apex like `example.com` itself).

---

**Q5. What is forward secrecy in TLS? Why does it matter?**

Forward secrecy (also called Perfect Forward Secrecy) means that even if the server's long-term private key is compromised in the future, past recorded sessions cannot be decrypted.

Achieved by using **ephemeral** key exchange (ECDHE): new, temporary key pairs are generated per session. The session key is derived from ephemeral keys and thrown away after the session ends. Even if an attacker records all past TLS traffic and later steals the server's certificate private key, they cannot decrypt past sessions because the ephemeral keys no longer exist.

TLS 1.3 mandates forward secrecy (removed RSA key exchange entirely).

---

## 🟡 Medium

**Q6. Walk through a TLS 1.3 handshake. Why is it faster than TLS 1.2?**

**TLS 1.3 (1 RTT):**
```
Client → Server: ClientHello
  - Supported TLS versions
  - Random nonce
  - Supported cipher suites
  - key_share: client's ECDHE public key (for supported groups)

Server → Client: ServerHello + {Certificate + CertVerify + Finished} (encrypted)
  - key_share: server's ECDHE public key
  - Both sides can now derive the session key from ECDHE exchange
  - Certificate, signature, and Finished are sent ENCRYPTED using the handshake key

Client → Server: Finished (encrypted)
```

**Why faster than TLS 1.2?**
1. **1 RTT vs 2 RTT**: TLS 1.2 needs an extra round trip to negotiate cipher suites and exchange DH parameters separately. TLS 1.3 sends key_share in the ClientHello (guesses the most likely group) — if the server supports it, handshake completes in 1 RTT.
2. **0-RTT resumption**: For reconnecting clients, TLS 1.3 supports sending application data in the first packet (using a session ticket from the previous connection). Zero extra latency for returning users.
3. **Simpler and safer**: Removed weak cipher suites (RSA exchange, SHA-1, DES) — less negotiation.

---

**Q7. What is head-of-line blocking? How does HTTP/2 address it at the HTTP layer but not the TCP layer?**

**Head-of-line (HOL) blocking**: When a queue processes items in order, a slow/large item at the front blocks all items behind it.

**HTTP/1.1 HOL blocking**: Only one request can be in-flight per TCP connection (or with pipelining: responses must arrive in request order). If resource #1 is slow, resources #2, #3, #4 wait even if they're ready.

**HTTP/2's fix**: Multiple requests are multiplexed as **streams** on one TCP connection. Frames from different streams are interleaved. Response to stream 3 can arrive before stream 1 — no HTTP-level HOL blocking.

**TCP-level HOL blocking (still in HTTP/2)**: TCP delivers bytes in order. If a TCP packet is lost, ALL data (from ALL HTTP/2 streams) waits for the retransmission, even data from streams unaffected by the loss. The OS TCP stack won't deliver later bytes to the application until the gap is filled.

**HTTP/3 (QUIC) fix**: QUIC implements stream-level retransmission at the transport layer. A lost packet only blocks the specific QUIC stream it belonged to. Other streams continue delivering data unaffected.

---

**Q8. Explain how HTTP caching works. What is the difference between `Cache-Control: no-cache` and `no-store`?**

**Cache-Control: no-cache**: The resource CAN be cached, but the cached copy must be **revalidated** with the server before use. Client sends a conditional request (`If-None-Match: "etag"` or `If-Modified-Since: date`). If unchanged: server responds `304 Not Modified` (no body transmitted, bandwidth saved). If changed: server sends `200 OK` with new content.

**Cache-Control: no-store**: The resource must **NEVER be cached** anywhere — not in browser cache, not in CDN, not in proxy. Every request goes to the origin server. Used for sensitive data (banking transactions, medical records) where caching any copy is a security risk.

**Flow with max-age:**
1. Server: `Cache-Control: max-age=3600` → Client caches and uses for 1 hour without any network request.
2. After 1 hour: Stale. Client must revalidate or fetch fresh.
3. If server also sent `ETag: "abc"`: Client revalidates with `If-None-Match: "abc"` → `304` if unchanged (no body sent).

---

**Q9. What is the purpose of the Cookie attributes: HttpOnly, Secure, and SameSite?**

**HttpOnly**: The cookie is inaccessible to JavaScript (`document.cookie` returns nothing for it). Prevents **XSS (Cross-Site Scripting)** attacks from stealing the session cookie — even if an attacker injects JS code, they can't read HttpOnly cookies.

**Secure**: The cookie is only sent over HTTPS connections, never HTTP. Prevents **network interception** (man-in-the-middle attacks) from capturing the cookie over an unencrypted connection.

**SameSite=Strict**: Cookie is only sent when the request originates from the same site. Prevents **CSRF (Cross-Site Request Forgery)** attacks — if an attacker's site tricks your browser into making a request to bank.com, the bank's session cookie won't be sent (different site).

**SameSite=Lax** (modern browsers' default): Cookie sent on top-level navigation (clicking a link) but not on background requests (images, fetch, XHR) from other sites. Balanced trade-off.

**SameSite=None**: Cookie sent on all cross-site requests (requires Secure flag too). Used for legitimate cross-site cookies (e.g., OAuth flows, embedded third-party widgets).

---

## 🔴 Hard

**Q10. Explain the full certificate chain verification process when a browser connects to https://example.com.**

When the server sends its certificate during TLS handshake, the browser performs:

**1. Parse the certificate chain**: The server typically sends its own certificate plus one or more intermediate CA certificates. The browser has root CA certificates built into its trust store (OS keychain or browser's own).

**2. Build a chain of trust**:
```
example.com cert
  └── signed by: DigiCert EV RSA CA G2 (intermediate)
        └── signed by: DigiCert Global Root CA (root — trusted by browser)
```

**3. Verify each signature in the chain**: Each certificate is signed by the CA above it. Browser verifies each signature using the CA's public key. A valid signature means the CA vouches for the certificate.

**4. Check validity period**: `notBefore ≤ now ≤ notAfter` for each certificate in the chain.

**5. Verify the hostname**: The certificate's SAN (Subject Alternative Name) field must include `example.com` (or `*.example.com` for wildcard). If hostname doesn't match → certificate error.

**6. Check revocation**:
- **CRL (Certificate Revocation List)**: Download a list of revoked certificates from the CA. Check if the serial number is in the list.
- **OCSP (Online Certificate Status Protocol)**: Query the CA's OCSP server for the certificate's current status. Faster than full CRL download.
- **OCSP Stapling**: The server fetches the OCSP response itself and "staples" it to the TLS handshake — no extra round trip needed by the client.

**7. Verify root CA is trusted**: The root CA at the top of the chain must be in the browser/OS trusted root store.

If all checks pass → green padlock. Any failure → TLS error, connection aborted.

---

**Q11. How does the Diffie-Hellman key exchange allow two parties to establish a shared secret over an insecure channel without ever sending the secret?**

DH exploits a **mathematical one-way function**: exponentiation in a finite group is easy, but the reverse (discrete logarithm) is computationally infeasible for large numbers.

**ECDHE (Elliptic Curve DH):**
```
Public parameters: elliptic curve E, generator point G (known to everyone)

Client: generates random private key a
        computes public key A = a × G (point multiplication)
        sends A to server

Server: generates random private key b
        computes public key B = b × G
        sends B to client

Client: computes shared secret = a × B = a × (b × G) = ab × G
Server: computes shared secret = b × A = b × (a × G) = ab × G

Both get the same point (ab × G) without ever sending a or b.
Attacker sees A and B but cannot compute a or b (ECDLP is hard).
```

**From shared secret to session keys**: The shared point's x-coordinate is fed into a KDF (Key Derivation Function) along with the handshake nonces to derive symmetric encryption keys (one for each direction). These keys are used for AES-GCM encryption of all subsequent data.

**"Ephemeral"**: New a and b are generated every session. Even if recorded sessions are stored and the server's long-term private key is later compromised, past ephemeral keys (a, b) are gone — forward secrecy.
