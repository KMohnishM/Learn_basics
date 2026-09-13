# Express.js Cheatsheet

## Middleware Execution Flow

```text
Incoming Request
      │
      ▼
+-------------------------+
| app.use(cors())         | <--- Global Middleware
+-------------------------+
      │
      ▼
+-------------------------+
| app.use(express.json()) | <--- Body Parser
+-------------------------+
      │
      ▼
+-------------------------+
| router.post('/login')   | <--- Route Match? (If no, continues)
+-------------------------+
      │
      ▼
+-------------------------+
| authMiddleware          | <--- Route-level Middleware
+-------------------------+
      │
      ▼
+-------------------------+
| routeController         | <--- Controller (Calls res.json())
+-------------------------+
      │ (If error passed to next(err))
      ▼
+-------------------------+
| errorHandler            | <--- Error Middleware (err, req, res, next)
+-------------------------+
```

---

## HTTP Status Codes Quick-Reference

| Code | Status | When to use |
| :--- | :--- | :--- |
| **200** | OK | Generic success (GET, PUT, PATCH). |
| **201** | Created | Resource successfully created (POST). |
| **204** | No Content | Success, but no body to return (DELETE). |
| **400** | Bad Request | Client sent invalid data (Zod validation failed). |
| **401** | Unauthorized | Missing or invalid token. Who are you? |
| **403** | Forbidden | Valid token, but insufficient permissions (RBAC). |
| **404** | Not Found | Resource or route does not exist. |
| **409** | Conflict | Resource already exists (e.g., email already registered). |
| **422** | Unprocessable Entity | Valid JSON, but semantic error (business logic). |
| **429** | Too Many Requests | Rate limit exceeded. |
| **500** | Internal Server Error | Uncaught exception or database failure. |

---

## JWT vs Session Authentication

| Feature | JWT (Stateless) | Session (Stateful) |
| :--- | :--- | :--- |
| **Storage** | Client only (localStorage / Cookie) | Server (Redis) + Client (Cookie ID) |
| **Scalability** | High (No database lookup needed) | Requires distributed cache (Redis) |
| **Revocation**| Hard (Requires blocklist DB) | Easy (Delete session in Redis) |
| **Payload Size**| Large (Contains user data/roles) | Small (Just a Session ID) |
| **Security Risk**| XSS (if in localStorage), Token Theft| CSRF attacks |

---

## REST API Design Conventions

| Resource | GET (Read) | POST (Create) | PUT / PATCH (Update) | DELETE |
| :--- | :--- | :--- | :--- | :--- |
| `/users` | Returns list of users | Creates a new user | *Bulk update (rare)* | *Delete all (rare)* |
| `/users/:id` | Returns a specific user | *Method Not Allowed* | Updates specific user | Deletes specific user |
| `/users/:id/orders` | Returns user's orders | Creates order for user | *Method Not Allowed* | *Method Not Allowed* |

---

## Security Headers (Helmet Reference)

| Header | Description (What it prevents) |
| :--- | :--- |
| `Content-Security-Policy` | Restricts sources of scripts/images (Prevents XSS). |
| `X-Frame-Options` | Prevents rendering app in an iframe (Prevents Clickjacking). |
| `Strict-Transport-Security` | Forces browsers to use HTTPS (Prevents Downgrade attacks). |
| `X-Content-Type-Options` | Forces `nosniff` (Prevents MIME-sniffing attacks). |
| `Referrer-Policy` | Controls what info is sent in the Referer header. |
| `X-Powered-By` | Removed by Helmet (Hides Express usage). |
