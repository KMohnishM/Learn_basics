# Express QnA

1. **How does Express middleware work? What happens if you forget to call `next()`?**
   Middleware functions execute in sequence. They receive `req`, `res`, and `next`. They can modify the request/response or end the cycle. If a middleware function does not call `res.send()` (or similar) to end the cycle, AND forgets to call `next()`, the request will hang indefinitely until the client times out, as control is never passed to the next function.

2. **What is the difference between `app.use()` and `app.get()`? What is `express.Router()`?**
   `app.use()` mounts middleware for ALL HTTP methods (GET, POST, PUT, etc.) at a specific path or globally. `app.get()` specifically routes only HTTP GET requests. `express.Router()` is a mini-application used to group routes and middleware together logically, allowing you to mount entire sets of routes to a base path (e.g., `app.use('/users', userRouter)`).

3. **Explain the JWT access token + refresh token pattern. Why are access tokens kept short-lived?**
   Access tokens are sent with every request and grant access to APIs. They are kept short-lived (e.g., 15m) because JWTs are stateless and difficult to revoke without database lookups. If an access token is stolen, the attack window is small. The Refresh Token is long-lived, securely stored (httpOnly cookie), and used solely to request new access tokens when the old one expires.

4. **What is the difference between JWT `HS256` and `RS256`? When would you use RS256?**
   `HS256` is symmetric; it uses the same secret key to both sign and verify the token. `RS256` is asymmetric; it uses a private key to sign the token and a public key to verify it. `RS256` is essential in microservice architectures where an Auth service signs the token, but many downstream services only need the public key to verify it without knowing the private signing key.

5. **What security vulnerabilities does `helmet` protect against? Name at least 5.**
   Helmet is a collection of middleware that sets security headers. It protects against:
   - Clickjacking (`X-Frame-Options`)
   - Cross-Site Scripting (XSS) (`Content-Security-Policy`)
   - MIME Sniffing (`X-Content-Type-Options`)
   - Downgrade attacks (`Strict-Transport-Security` / HSTS)
   - Information leakage (hides `X-Powered-By: Express`)

6. **What is CORS? Explain a CORS preflight request.**
   CORS (Cross-Origin Resource Sharing) is a browser security mechanism that restricts web pages from making requests to a different domain than the one that served the page. For complex requests (e.g., PUT, DELETE, or requests with custom headers), the browser automatically sends an HTTP `OPTIONS` request first (the preflight) to check if the server permits the actual request.

7. **How do you handle async errors in Express route handlers without try/catch in every handler?**
   In Express 4, unhandled promise rejections crash the process or get swallowed. You can wrap async routes in a high-order function (like `asyncHandler`) that catches errors and passes them to `next(err)`. Alternatively, use the `express-async-errors` package which monkey-patches Express to handle them automatically.

8. **What is the difference between cursor-based and offset-based pagination? When is cursor pagination superior?**
   Offset uses `LIMIT` and `OFFSET` (e.g., skip 100 rows). It is slow for deep pages because the database must scan all skipped rows. It also suffers from data drift if items are added/deleted. Cursor-based pagination uses an indexed marker (e.g., `WHERE id > last_id LIMIT 10`). It is superior for large, real-time datasets (like social feeds) because it is much faster and immune to data drift.

9. **How would you implement RBAC (role-based access control) as Express middleware in TypeScript?**
   Create a middleware factory function that takes an array of allowed roles. Inside the returned middleware, verify if `req.user.role` (populated by previous auth middleware) exists within the allowed roles array. If it does, call `next()`; otherwise, return a 403 Forbidden response.

10. **What is the `alg: none` JWT attack? How do you prevent it?**
    It's an attack where a malicious user alters the JWT header to `{"alg": "none"}`, removes the signature, and modifies the payload. If the backend library blindly trusts the header's algorithm, it considers the unsigned token valid. Prevent this by enforcing the specific expected algorithm (e.g., `algorithms: ['RS256']`) in your verification function.

11. **Explain graceful shutdown in Express. Why is it important in Kubernetes environments?**
    Graceful shutdown means catching termination signals (SIGTERM/SIGINT), stopping the HTTP server from accepting new connections, waiting for existing requests to finish (draining), and cleanly closing database connections before exiting. In Kubernetes, pods are frequently destroyed during deployments or scaling; without graceful shutdown, in-flight user requests are abruptly dropped, causing errors.

12. **How do you validate request bodies with Zod in an Express application? Show the middleware pattern.**
    Define a Zod schema. Create a middleware function that takes the schema, calls `schema.parse()` (or `parseAsync`) against `req.body`, `req.query`, and `req.params`. If validation succeeds, call `next()`. If it throws a ZodError, catch it and return a 400 Bad Request response with the error details.

13. **What is the difference between `res.json()` and `res.send()`?**
    `res.send()` can send various types of responses (strings, buffers, objects). If you pass an object, it internally formats it to JSON. `res.json()` explicitly forces the response to be JSON formatted, setting the `Content-Type` to `application/json`, and offers options for JSON formatting (like strict JSON rules).

14. **How would you implement distributed rate limiting in Express using Redis?**
    Use the `express-rate-limit` package combined with `rate-limit-redis`. Instead of storing request counts in Node's local memory (which fails if you have multiple server instances behind a load balancer), the rate limiter stores IPs and hit counts in a centralized Redis database accessible by all instances.

15. **How do you extend the Express `Request` type in TypeScript to add custom properties like `req.user`?**
    You use declaration merging. Create a `.d.ts` file (e.g., `express.d.ts`), use `declare namespace Express`, and interface `Request`. Add the `user` property with its type definition. Ensure this definition file is included in your `tsconfig.json` so TypeScript merges it with the default Express types.
