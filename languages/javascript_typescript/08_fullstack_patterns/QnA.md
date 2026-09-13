# Module 8: Full-Stack Patterns QnA

Here are 15 critical questions and detailed answers regarding full-stack architecture, deployment, and systems design.

### 1. Why are auth tokens stored in `httpOnly` cookies instead of `localStorage`? What attack does this prevent?
**Answer:**
Storing tokens in `localStorage` exposes them to Cross-Site Scripting (XSS) attacks. If malicious JavaScript executes on your page (e.g., via a compromised third-party NPM script), it can read `localStorage` and steal the token, allowing the attacker to impersonate the user. 
An `httpOnly` cookie is inaccessible to JavaScript running in the browser. It is automatically attached to HTTP requests by the browser. This completely neutralizes XSS-based token theft.

### 2. What is the difference between WebSockets and Server-Sent Events? When would you choose each?
**Answer:**
WebSockets establish a bidirectional, full-duplex connection. Both the client and the server can send messages at any time. SSE (Server-Sent Events) is unidirectional; the client connects, and the server streams data downwards over standard HTTP.
**When to choose:** Use WebSockets for highly interactive, two-way systems like multiplayer games, collaborative editing (Figma), or chat applications. Use SSE for one-way live data feeds like stock tickers, social media notification bells, or sports scoreboards.

### 3. How does tRPC achieve end-to-end type safety? How does it differ from REST with a typed client like `openapi-typescript`?
**Answer:**
tRPC achieves type safety by sharing the actual TypeScript type definitions of the server-side router directly with the client. It requires both the client and server to be in a monorepo (or share a package). When you change a procedure on the server, the client immediately throws a type error locally.
REST with `openapi-typescript` requires a middle step: you write your server code, generate an OpenAPI schema (JSON/YAML), and then run a script to generate TypeScript types for the client. tRPC eliminates the code generation and schema parsing steps entirely.

### 4. What is the N+1 problem in GraphQL? How does DataLoader solve it?
**Answer:**
The N+1 problem occurs when a query asks for a list of items and a nested relationship (e.g., 10 Users, and for each User, their Posts). A naive GraphQL resolver fetches the 10 users (1 query), then iterates through the users, firing a separate database query for each user's posts (N queries). This results in 11 queries instead of 1.
**DataLoader** solves this by batching and deduplicating queries. Instead of executing queries immediately, it gathers all the requested user IDs during a tick of the event loop, and executes a single SQL query: `SELECT * FROM posts WHERE user_id IN (1, 2, ..., 10)`.

### 5. What is Turborepo? How does its remote caching work?
**Answer:**
Turborepo is a high-performance build system tailored for JavaScript/TypeScript monorepos. It orchestrates complex dependencies between packages and caches the outputs of tasks (like builds or tests).
Remote caching extends this to the cloud (usually via Vercel). When CI or a teammate runs a build, Turborepo uploads the resulting artifacts (and terminal logs) to the cloud, keyed by a hash of the source code. If you check out the same code and run the build, Turborepo downloads the cached artifacts in milliseconds instead of recompiling locally.

### 6. Why is Prisma problematic in serverless environments? What are the solutions?
**Answer:**
In serverless environments (like AWS Lambda or Next.js API routes on Vercel), functions scale from 0 to thousands instantly. On a cold start, each function instance attempts to open a direct TCP connection to the database. Relational databases like PostgreSQL have hard limits on connections (often around 100). Serverless functions rapidly exhaust these connections, causing the database to reject new requests and crash.
**Solutions:** Use a connection pooling proxy (PgBouncer, Prisma Accelerate) that sits between the functions and the database to manage connections, or use edge-compatible databases via HTTP connections (Data API).

### 7. What is PKCE and why is it needed for OAuth2 in Single Page Applications?
**Answer:**
PKCE (Proof Key for Code Exchange) is an extension to OAuth2 designed for public clients (SPAs, mobile apps) that cannot securely store a static Client Secret. In traditional OAuth, the secret is needed to exchange an authorization code for an access token.
With PKCE, the client generates a dynamic secret (Code Verifier) and its hash (Code Challenge) per login attempt. It sends the challenge first, receives an auth code, and then sends the verifier. The Auth Server hashes the verifier to ensure it matches the challenge, verifying the client's identity without needing a static secret.

### 8. Design a multi-tenant Next.js app where each tenant has a custom subdomain. How does Middleware handle routing?
**Answer:**
In a multi-tenant application (e.g., `tenant1.myapp.com`, `tenant2.myapp.com`), you use Next.js Middleware to intercept incoming requests. The Middleware reads the `Host` header to determine the subdomain. 
Instead of physically creating separate files for every tenant, Middleware uses `NextResponse.rewrite()` to internally map the request to a dynamic route structure, such as `/app/[tenantId]/dashboard`. The URL in the user's browser remains `tenant1.myapp.com`, but internally Next.js renders the parameterized route, passing the `tenantId` to the page components.

### 9. What is the connection between `AsyncLocalStorage` and distributed tracing correlation IDs?
**Answer:**
To trace a request traversing through various functions, database queries, and external APIs in Node.js, every log entry needs a unique Request/Correlation ID. Manually passing this ID as an argument to every function is tedious and pollutes the codebase.
`AsyncLocalStorage` (a built-in Node.js module) provides a way to store data that persists across asynchronous continuations (like Thread-Local storage in Java). Middleware can generate an ID, place it in `AsyncLocalStorage`, and any deeply nested function or logger can seamlessly retrieve it without it being passed explicitly.

### 10. What are Core Web Vitals? How does Next.js `<Image>` help with CLS?
**Answer:**
Core Web Vitals are Google's metrics for evaluating user experience:
- **LCP (Largest Contentful Paint):** Time to render the largest visible element.
- **FID/INP:** Responsiveness to user input.
- **CLS (Cumulative Layout Shift):** Measures visual instability.
When standard `<img>` tags load, they initially take up 0 height until the image downloads, causing the layout below it to jump violently (high CLS). The Next.js `<Image>` component helps by forcing the developer to provide width and height attributes (or filling a sized container), reserving the exact space required before the image even begins downloading, thus preventing layout shift.

### 11. How would you implement real-time features (e.g., live notifications) in a Next.js app deployed across multiple server instances?
**Answer:**
You cannot use simple in-memory WebSockets because users connected to Instance A will not receive notifications generated by Instance B.
You must implement a Pub/Sub mechanism using a centralized datastore, typically **Redis**. 
Architecture: User A connects to Instance A. User B connects to Instance B. When an event occurs for User B on Instance A, Instance A publishes a message to a Redis channel. Both instances subscribe to Redis. Instance B receives the message from Redis and pushes it over the WebSocket to User B.

### 12. What is the Repository Pattern? How does it improve testability of database-dependent code?
**Answer:**
The Repository Pattern abstracts data access logic into specialized classes or functions (e.g., `UserRepository`). The business logic (controllers/services) interacts only with the repository interface, never directly executing SQL or ORM commands.
This massively improves testability because you can easily swap the real `UserRepository` with a `MockUserRepository` during unit tests. You can test your business logic in isolation without needing to spin up a real database, truncate tables, or deal with slow I/O.

### 13. Write a multi-stage Dockerfile for a Next.js application using the `standalone` output mode.
**Answer:**
```dockerfile
# Stage 1: Install dependencies
FROM node:18-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Stage 2: Build the app
FROM node:18-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Stage 3: Production runner
FROM node:18-alpine AS runner
WORKDIR /app
ENV NODE_ENV production
COPY --from=builder /app/public ./public
# Copy the standalone output and static assets
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
EXPOSE 3000
CMD ["node", "server.js"]
```

### 14. What is the difference between Auth.js JWT sessions and database sessions? When would you use each?
**Answer:**
- **JWT Sessions:** The session data (user ID, roles) is cryptographically signed and stored entirely within the cookie on the user's browser. The server validates the signature. No database hit is required to verify the user. *Use when performance and scalability are paramount.*
- **Database Sessions:** The cookie only holds an opaque Session ID. The server must query the database to retrieve the session details and verify it is still valid. *Use when you need the ability to instantly revoke a user's access, log them out of all devices, or tightly track session lifetimes.*

### 15. How would you implement on-demand ISR revalidation when a product price is updated in your database?
**Answer:**
In a Next.js architecture, the product page is statically generated and cached at the edge.
When an admin updates a product price via a CMS or admin panel, they trigger a Server Action or API Route (e.g., `PUT /api/products/1`). 
After successfully updating the database, the server code calls `revalidatePath('/products/1')` or `revalidateTag('product-1')`. Next.js clears the CDN cache for that specific page, and the very next user request will fetch the fresh price from the database and regenerate the static HTML.
