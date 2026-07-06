# Module 1: API Design That Actually Scales

API design is one of those skills that separates engineers who build systems that are easy to work with from those who build systems that generate constant complaints from consumers. A poorly designed API is an enormous ongoing cost — every consumer must work around its inconsistencies, and it gets harder to fix over time because every change is a breaking change.

This module covers the principles and patterns behind APIs that stand the test of scale.

---

## 1. The Richardson Maturity Model (REST Maturity Levels)

Not all "REST APIs" are equal. Leonard Richardson defined a maturity model with 4 levels. Most APIs that claim to be REST are Level 1 or 2.

### Level 0 — The Swamp of POX (Plain Old XML)
One endpoint, all operations via POST.
```
POST /api  {"action": "getUser", "id": 42}
POST /api  {"action": "createOrder", "userId": 42, "items": [...]}
```
This is just RPC over HTTP. Not REST at all.

### Level 1 — Resources
Multiple endpoints, but still no consistent use of HTTP verbs.
```
POST /users/42        {"action": "get"}
POST /users/42        {"action": "delete"}
```
Resources exist, but HTTP verbs aren't used semantically.

### Level 2 — HTTP Verbs (What 95% of APIs achieve)
Use HTTP verbs (GET, POST, PUT, PATCH, DELETE) correctly. This is the minimum bar for a real REST API.
```
GET    /users/42          → Fetch user
POST   /users             → Create user
PUT    /users/42          → Replace entire user
PATCH  /users/42          → Update specific fields
DELETE /users/42          → Delete user
```

### Level 3 — HATEOAS (Hypermedia as the Engine of Application State)
Responses include links to related actions. The client doesn't need to know the URL structure in advance.
```json
{
  "id": 42,
  "name": "Alice",
  "_links": {
    "self": {"href": "/users/42"},
    "orders": {"href": "/users/42/orders"},
    "delete": {"href": "/users/42", "method": "DELETE"}
  }
}
```
Rarely fully implemented in practice, but the concept is useful for self-documenting APIs.

---

## 2. HTTP Semantics — The Full Truth

### Status Codes (The Complete Guide)

Most APIs use 200, 400, 404, and 500. That's insufficient. Using the right status code communicates intent to clients without them having to parse the response body.

**2xx — Success**
- `200 OK` — Standard success. Use for GET, PUT, PATCH responses.
- `201 Created` — Resource was created. Include a `Location` header pointing to the new resource.
- `202 Accepted` — Request received but processing is async. Return a job ID.
- `204 No Content` — Success but nothing to return. Use for DELETE.

**3xx — Redirection**
- `301 Moved Permanently` — URL changed forever. Clients should update bookmarks.
- `302 Found` — Temporary redirect.
- `304 Not Modified` — Client has a cached version (ETag/Last-Modified match). No need to send data.

**4xx — Client Errors (The client did something wrong)**
- `400 Bad Request` — Malformed request, invalid JSON, missing required field.
- `401 Unauthorized` — Not authenticated. "You need to log in."
- `403 Forbidden` — Authenticated but not authorized. "You don't have permission."
- `404 Not Found` — Resource doesn't exist.
- `405 Method Not Allowed` — You sent a DELETE to a read-only endpoint.
- `409 Conflict` — Duplicate resource (e.g., creating a user with an email that already exists).
- `422 Unprocessable Entity` — Well-formed request but semantic validation failed (e.g., end_date < start_date).
- `429 Too Many Requests` — Rate limit exceeded. Include `Retry-After` header.

**5xx — Server Errors (The server broke)**
- `500 Internal Server Error` — Something unexpected happened. Never expose stack traces.
- `502 Bad Gateway` — Your reverse proxy couldn't reach the upstream service.
- `503 Service Unavailable` — The service is intentionally down (maintenance). Include `Retry-After`.
- `504 Gateway Timeout` — Upstream service took too long.

**Critical rule**: Never use 200 for errors. `{"status": "error", "message": "User not found"}` with a 200 status is a design failure. Clients' error handling code inspects the HTTP status, not the body.

### Idempotency

- **GET**: Idempotent (safe to call multiple times, same result)
- **PUT**: Idempotent (replacing a resource with the same data yields the same state)
- **DELETE**: Idempotent (deleting something that's already deleted → 204, not 404... debatable but important)
- **POST**: NOT idempotent (calling `POST /orders` twice creates two orders)
- **PATCH**: NOT guaranteed idempotent (depends on whether it's a merge or operation like "increment counter")

For non-idempotent operations, clients need an **Idempotency Key** to safely retry without side effects:
```
POST /payments
Idempotency-Key: a7f2c8d1-3b4e-5f6a-7c8d-9e0f1a2b3c4d
{"amount": 100, "currency": "USD"}
```
The server stores the key and returns the same response if it sees it again. Used by Stripe, PayPal, and every serious payment API.

---

## 3. API Versioning Strategies

One of the hardest problems in API design: how do you evolve your API without breaking existing clients?

### Option 1: URL Versioning (Most Common)
```
/api/v1/users
/api/v2/users
```
Pros: Visible, easy to test in browser, easy to route at gateway.
Cons: Pollutes URLs, tempts developers to run multiple versions of the codebase indefinitely.

### Option 2: Header Versioning
```
GET /users
Accept: application/vnd.myapp.v2+json
```
Pros: Cleaner URLs.
Cons: Can't be tested in a browser without tools. Most developers hate it.

### Option 3: Query Parameter Versioning
```
GET /users?api_version=2
```
Pros: Easy to use.
Cons: Hard to set at infrastructure/routing level.

### The Practical Approach
Use URL versioning for major breaking changes. Use additive changes (new fields in response, new optional parameters) without version bumps.

**Additive changes (safe, no version bump needed):**
- Adding new response fields
- Adding new optional request parameters
- Adding new endpoints

**Breaking changes (require version bump):**
- Removing or renaming fields
- Changing field types
- Changing error response structure
- Changing authentication mechanism

---

## 4. Pagination: Why Offset Pagination Breaks at Scale

### Offset Pagination (What Most APIs Use)
```
GET /posts?page=2&limit=20
```
This translates to SQL: `SELECT * FROM posts ORDER BY id LIMIT 20 OFFSET 20`

**The problem**: At scale, `OFFSET 10000` requires the database to scan and discard 10,000 rows before returning 20. On a table with 50 million rows, page 50,000 might take 30 seconds.

The second problem: if a new post is inserted while a user is paginating, all subsequent pages shift by one. Users see duplicates or miss items entirely.

### Cursor Pagination (What You Should Use)
```
GET /posts?limit=20&after=eyJpZCI6MTAwfQ==
```
`after` is a base64-encoded cursor (e.g., the ID or timestamp of the last item seen).

SQL: `SELECT * FROM posts WHERE id > 100 ORDER BY id LIMIT 20`

**Advantages**:
- Constant time regardless of page depth (uses index scan, not offset scan)
- Stable: new inserts don't shift the cursor position
- Better for infinite scroll UIs

**Response format**:
```json
{
  "data": [...],
  "pagination": {
    "has_next_page": true,
    "next_cursor": "eyJpZCI6MTIwfQ==",
    "total_count": 50000
  }
}
```

---

## 5. GraphQL — When REST Isn't Enough

REST has two fundamental problems for complex clients (especially mobile):

**Over-fetching**: `GET /users/42` returns 50 fields, but your mobile app only needs `name` and `avatar_url`. You're wasting bandwidth (expensive on mobile networks).

**Under-fetching / N+1 requests**: To display a feed of 20 posts with author names, you:
1. `GET /posts?limit=20` → 20 posts with `author_id`
2. `GET /users/1`, `GET /users/2`, ..., `GET /users/20` → 20 more requests

GraphQL solves both:

```graphql
# Client specifies exactly what fields it wants
query GetFeed {
  posts(limit: 20) {
    id
    title
    author {
      name
      avatarUrl
    }
  }
}
```

One request. Exactly the fields needed. No over-fetching.

### The N+1 Problem in GraphQL

GraphQL has its own N+1 problem. If 20 posts all have `author` fields, and each `author` resolver hits the database independently, that's 20 database queries.

**Solution: DataLoader**

DataLoader batches all individual `getUser(id)` calls made within a single request tick into a single `SELECT * FROM users WHERE id IN (1, 2, 3, ..., 20)`.

```python
from strawberry.dataloader import DataLoader

async def batch_load_users(keys: list[int]) -> list[User]:
    # ONE query for all users
    users = await db.execute(
        "SELECT * FROM users WHERE id = ANY($1)", keys
    )
    # Return in same order as keys
    user_map = {u.id: u for u in users}
    return [user_map.get(key) for key in keys]

user_loader = DataLoader(load_fn=batch_load_users)
```

### When to Use GraphQL vs REST

| Use REST when... | Use GraphQL when... |
|------------------|---------------------|
| Simple CRUD | Complex, nested data relationships |
| Public APIs (REST is universally understood) | Client-controlled queries needed |
| File uploads | Mobile clients with bandwidth constraints |
| HTTP caching is critical | Multiple clients with different data needs |

---

## 6. gRPC — Speed at the Cost of Simplicity

REST uses HTTP/1.1 + JSON (text-based, human-readable, verbose). gRPC uses HTTP/2 + Protocol Buffers (binary, compact, fast).

### Performance Comparison
- JSON payload size: `{"user_id": 42, "name": "Alice"}` → 32 bytes
- Protobuf equivalent: ~6 bytes
- gRPC can be 5-10x faster than REST for the same operation at high throughput

### Protocol Buffers
You define your schema in a `.proto` file:
```protobuf
syntax = "proto3";

service UserService {
  rpc GetUser (UserRequest) returns (UserResponse);
  rpc StreamUsers (UserRequest) returns (stream UserResponse);
}

message UserRequest {
  int32 user_id = 1;
}

message UserResponse {
  int32 id = 1;
  string name = 2;
  string email = 3;
}
```

The `protoc` compiler generates client and server code in any language (Python, Go, Java, etc.) from this schema.

### gRPC Streaming Types
- Unary: one request → one response (like REST)
- Server streaming: one request → many responses (e.g., live stock prices)
- Client streaming: many requests → one response (e.g., uploading chunks)
- Bidirectional streaming: many ↔ many (e.g., live chat)

### When to Use gRPC
- Internal microservice-to-microservice communication
- High-throughput, low-latency requirements
- Streaming data
- Polyglot environments (Python calling a Go service)
- **Not recommended** for public-facing APIs (browser support is limited)

---

## Next Steps

Go to `labs/` to implement the same API in REST and GraphQL and benchmark them side by side!
