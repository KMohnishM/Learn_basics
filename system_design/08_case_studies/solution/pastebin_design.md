# Solution: Designing a URL Shortener

## 1. Requirements & Estimation (R)
- **Writes**: 100M/month = ~40 writes/sec.
- **Reads**: 1B/month = ~400 reads/sec.
- **Storage**: (100M * 12 months * 5 years) = 6 Billion URLs. If each record is 500 bytes, we need **3 Terabytes** of storage.

## 2. API Design (A)
```json
// POST /api/v1/data/shorten
{ "long_url": "https://www.verylongdomain.com/article/123" }
// Returns: { "short_url": "bit.ly/7f2Bq9" }

// GET /api/v1/7f2Bq9
// Returns: HTTP 301 Redirect to the long URL
```

## 3. Data Model (D)
Because the data is flat (no complex relationships or joins) and we need to store billions of rows with high read performance, a **Key-Value NoSQL Store** (like Amazon DynamoDB or Cassandra) is perfect.

**Table: url_mapping**
- `hash` (Primary Key, String, e.g., "7f2Bq9")
- `long_url` (String)
- `created_at` (Timestamp)

## 4. Infrastructure & The Hash Algorithm (I)

### How to generate the hash?
If we use a standard hash function (MD5 or SHA-256) on the long URL, it generates a very long string. If we take just the first 7 characters, we risk collisions.
Also, if two users submit the *same* URL, we want to give them *different* short URLs (for analytics tracking).

**The best approach: Base62 Encoding of a Distributed ID.**
1. We use a Distributed ID Generator (like Twitter Snowflake or a ZooKeeper auto-incrementing counter) to get a globally unique integer (e.g., `100,000`).
2. We convert that base-10 integer into Base-62 [A-Z, a-z, 0-9]. 
3. Base62 of `100,000` is `Q0c`. 
4. Because the original integer was unique, the Base62 string is mathematically guaranteed to be unique. **Zero collisions!**

### The Read Path (Redirection)
1. User clicks `bit.ly/Q0c`.
2. Request hits Load Balancer.
3. Routed to Web Server.
4. Server checks **Redis Cache** for `Q0c`.
   - If hit: return HTTP 301.
   - If miss: query DynamoDB for `Q0c`, save to Redis, return HTTP 301.

## 5. Optimizations (O)

### Caching Strategy
We use **Cache-Aside**. Since we have 3TB of data, we cannot cache everything. We use an **LRU (Least Recently Used)** eviction policy. 80% of clicks usually go to 20% of the links (the "viral" links from the last 24 hours), so LRU perfectly keeps the hot data in RAM and evicts old links.

### The 301 vs 302 Redirect
- **HTTP 301 (Permanent)**: The browser caches the redirect. The next time the user clicks it, the browser doesn't even talk to our server! Great for reducing server load.
- **HTTP 302 (Temporary)**: The browser will ask our server every single time. We must use 302 if we care about Analytics (tracking every single click). For this design, we assume 301 for maximum performance.
