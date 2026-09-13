# Full-Stack Architectural Patterns

## 1. Full-Stack Authentication Architecture

**Cookie-based auth in Next.js:**
When implementing authentication, the most secure approach for web applications is often storing the JSON Web Token (JWT) or session identifier inside an `httpOnly` cookie.
The `httpOnly` flag is critical because it ensures that client-side JavaScript cannot access the cookie via `document.cookie`. This provides strong protection against Cross-Site Scripting (XSS) attacks, preventing malicious scripts from stealing the user's token.
The `Secure` attribute must be set to true in production, ensuring the cookie is only transmitted over encrypted HTTPS connections.
The `SameSite` attribute controls cross-site request behavior. Setting `SameSite=Lax` means the cookie is sent on same-site requests and top-level navigations, protecting against most Cross-Site Request Forgery (CSRF) attacks while still allowing OAuth login redirects to function correctly.
Setting `SameSite=Strict` provides maximum CSRF protection by ensuring the cookie is never sent on any cross-site request, but this will break OAuth authentication flows.
When defining expiration, `Max-Age` is generally preferred over `Expires` because it specifies a relative duration in seconds rather than an absolute date string, avoiding time-sync issues.
Why NOT `localStorage`: Storing sensitive tokens in `localStorage` makes them trivially accessible to any JavaScript running on the page. If your site has an XSS vulnerability, the attacker can immediately steal the token, leading to complete account takeover.

**Auth.js (NextAuth v5) in App Router:**
Auth.js is the standard solution for authentication in modern Next.js applications.
Configuration begins in an `auth.config.ts` file, where you define your providers, callbacks, and basic session configuration. This file is designed to be imported in the Next.js Middleware, meaning it must be compatible with the Edge runtime.
The `auth.ts` file extends this configuration by adding the database adapter required for persisting database sessions.
You must choose between two primary session strategies:
- JWT sessions: A signed token is stored directly in the cookie. This is highly performant because it requires no database lookup on every request. However, JWTs cannot be truly revoked before they expire unless you implement a complex global blocklist.
- Database sessions: A simple session ID is stored in the cookie, and the actual session data is stored in your database. This allows for instant revocation of sessions, but it requires a database query on every single authenticated request.
Middleware integration is handled by calling `auth()` within your `middleware.ts` file. This allows you to validate the session token at the Edge network layer before the route is even processed by the origin server.
To access the session within a Server Component, you simply call `const session = await auth()` anywhere inside the component body.
The full OAuth authentication flow typically looks like this: The user initiates `POST /auth/callback/{provider}` → The provider returns data and a JWT is created → The JWT is set as an httpOnly cookie → On subsequent requests, the Middleware validates the cookie → The Server Component reads the validated session data.

**PKCE (Proof Key for Code Exchange):**
PKCE was introduced to solve a specific problem: OAuth2 authorization codes can potentially be intercepted by malicious applications running on mobile devices or desktop operating systems.
The PKCE solution involves the client generating a `code_verifier` (a cryptographically random string) before initiating the authorization flow. The client hashes this verifier to create a `code_challenge` and sends the challenge along with the initial authorization request.
During the token exchange phase, the client sends the original `code_verifier`. The authorization server hashes it and compares it against the previously stored `code_challenge`. The exchange only succeeds if they match, proving that the entity exchanging the code is the same entity that requested it.
PKCE is now considered a mandatory security requirement for all public clients, including Single Page Applications (SPAs) and mobile apps, because these environments cannot safely store client secrets.

## 2. WebSockets & Real-Time Communication

**WebSocket Protocol:**
The WebSocket connection begins with an HTTP upgrade handshake. The client sends an HTTP request with the `Upgrade: websocket` header. If the server supports WebSockets, it responds with an HTTP status `101 Switching Protocols`, and the TCP connection remains open.
Once established, the connection is full-duplex, meaning both the client and the server can send messages to each other at any time simultaneously.
Data is transmitted in discrete units called frames, which can contain either text or binary data. Client-to-server frames are masked for security, while server-to-client frames are unmasked.
Using the `ws` library in a Node.js environment is straightforward:
```ts
import { WebSocketServer } from 'ws';

const wss = new WebSocketServer({ port: 8080 });

wss.on('connection', (ws) => {
  console.log('New client connected');
  
  ws.on('message', (data) => { 
    console.log(`Received: ${data}`);
    ws.send(`Echo: ${data}`); 
  });
  
  ws.on('close', () => {
    console.log('Client disconnected');
  });
});
```
Implementing a ping/pong heartbeat mechanism is essential to detect stale connections and prevent load balancers from dropping inactive sockets. The server should periodically send ping frames, and clients must respond with pong frames.

**Server-Sent Events (SSE):**
Unlike WebSockets, SSE is strictly unidirectional: data flows from the server to the client only.
It is built on top of plain HTTP/1.1 and uses the standard `Content-Type: text/event-stream`.
A major advantage of SSE is auto-reconnect functionality. If the connection drops, the browser automatically attempts to reconnect, sending a `Last-Event-ID` header so the server knows where to resume the stream.
The message payload format is strictly defined text: `data: ...\n\nid: ...\n\nevent: customEvent\n\n`.
SSE is significantly simpler to implement than WebSockets and is perfect for read-only data streams such as live news feeds, long-running progress updates, or streaming AI text generation responses.
When used over HTTP/2, SSE benefits from multiplexing, making it much more efficient than HTTP/1.1 WebSockets when dealing with a large number of concurrent connections.

**Socket.io:**
Socket.io is not a raw WebSocket implementation; it is an abstraction layer that provides WebSockets with robust fallback mechanisms, such as HTTP long-polling, for environments that do not support WebSockets.
It introduces powerful concepts like Rooms: `socket.join('room1')` allows a socket to join a group, and `io.to('room1').emit('event', data)` broadcasts a message exclusively to members of that room.
Namespaces (`io.of('/chat')`) allow you to multiplex different logical channels over a single physical connection to the server.
Socket.io supports acknowledgements, enabling RPC-style communication: `socket.emit('event', data, (response) => { ... })`.
It also provides automatic reconnection logic with exponential backoff built-in.

**Multi-Instance Real-Time (Redis Pub/Sub):**
The core problem with stateful real-time connections is that a WebSocket connection is physically tied to one specific server instance. In a horizontally scaled application with multiple instances, you need a way to broadcast messages across all instances.
The standard solution is utilizing Redis Pub/Sub. Each server instance subscribes to a shared Redis channel. When one instance needs to broadcast, it publishes the message to the Redis channel, which delivers it to all other server instances. Each instance then forwards the message to its connected WebSocket clients.
When using Socket.io, you can use the `@socket.io/redis-adapter` package to handle this complex orchestration automatically.
ASCII diagram of the architecture:
```text
Client A (WS) ---> Server 1 (Publishes to Redis Channel)
                         |
                         V
                   Redis Channel (Broadcasts)
                         |
                         V
                   Server 2 (Receives from Redis) ---> (WS) Client B
```

**WebSockets vs SSE vs Polling:**
Standard Polling involves the client sending an HTTP request every N seconds. It is very simple to implement but highly wasteful of bandwidth and server resources, and suffers from high latency.
Long Polling improves this by having the server hold the client's request open until data is available. It is less wasteful than standard polling but adds significant complexity to the server implementation.
SSE provides a persistent HTTP connection where the server pushes text data, with built-in auto-reconnection. It is ideal for read-only streams.
WebSockets provide a persistent TCP connection with true full-duplex, bidirectional communication supporting both text and binary payloads. It is the absolute requirement for highly interactive real-time applications like chat systems, collaborative editing tools, and multiplayer games.

## 3. API Paradigms

**REST (Representational State Transfer):**
REST models the API around distinct resources accessed via specific URLs, utilizing standard HTTP methods (GET, POST, PUT, DELETE, PATCH) as verbs to perform actions.
It is inherently stateless: every single request must contain all the necessary context and authentication information for the server to process it.
REST is highly cache-friendly. Standard HTTP GET responses can be easily cached by intermediate CDNs, proxies, or the user's browser using standard headers.
API versioning is typically handled via URL paths (e.g., `/v1/users`) or through custom request headers (e.g., `Accept-Version: 1`).
Advantages include its simplicity, universal understanding, extensive tooling ecosystem, and excellent CDN cacheability.
Disadvantages include over-fetching (receiving huge payloads with many fields you don't need) and under-fetching (requiring multiple round trips to different endpoints to assemble a complete view of data), leading to tight coupling between specific client views and server endpoints.

**GraphQL:**
GraphQL exposes a single endpoint (usually `/graphql`) where the client sends a query specifying the exact structure and fields of the data it requires.
This elegantly solves both the over-fetching and under-fetching problems inherent in REST.
However, it introduces the infamous N+1 problem on the server. For example, querying a list of 10 posts, and then resolving the author for each post, could result in 1 initial DB query + 10 subsequent author queries (N+1).
The solution to the N+1 problem is using DataLoader. DataLoader batches and deduplicates database queries occurring within a single execution tick of the event loop.
```ts
import DataLoader from 'dataloader';

// The batch function receives an array of keys
const userLoader = new DataLoader(async (ids: readonly string[]) => {
  const users = await db.findUsersByIds(ids);
  // Must return an array of the exact same length and order as the input ids
  return ids.map(id => users.find(u => u.id === id) || null);
});
```
GraphQL also natively supports real-time updates via Subscriptions, which are typically implemented over WebSockets.
Disadvantages of GraphQL include highly complex caching mechanisms (often requiring persisted queries), the absolute necessity for strict DataLoader discipline to prevent database meltdown, and generally higher server-side complexity compared to REST.

**tRPC (TypeScript Remote Procedure Call):**
tRPC allows you to define procedures on the server and call them directly from the client with absolute end-to-end type safety.
It achieves this without any build step, code generation, or separate schema files. The TypeScript types flow directly and organically from your server code into your client code.
It is the absolute best choice when working within a TypeScript monorepo, particularly with frameworks like Next.js.
```ts
// --- Server Side ---
import { initTRPC } from '@trpc/server';
import { z } from 'zod';

const t = initTRPC.create();
const publicProcedure = t.procedure;
const router = t.router;

export const appRouter = router({
  getUser: publicProcedure
    .input(z.object({ id: z.string() }))
    .query(async ({ input }) => {
      return await db.user.findUnique({ where: { id: input.id } });
    })
});

export type AppRouter = typeof appRouter;

// --- Client Side ---
// The client knows exactly what arguments getUser requires and what it returns
const user = await trpc.getUser.query({ id: '123' });
```
It is important to note that tRPC is not suitable for public-facing APIs intended for third-party consumers, as it fundamentally requires TypeScript on both ends and is not compatible with standard REST clients.

**gRPC:**
gRPC is a high-performance RPC framework developed by Google that uses Protocol Buffers (protobuf) as its binary interface definition language.
Because protobuf is a binary protocol, payloads are significantly smaller (often 5-10x) and much faster to parse than JSON.
Services and messages are defined in `.proto` files, which are then compiled to generate strongly-typed client and server stubs in virtually any programming language.
gRPC supports four distinct streaming modes: unary (single request/response), server streaming, client streaming, and true bidirectional streaming.
It is the gold standard for microservice-to-microservice communication within a backend infrastructure, polyglot environments, and high-throughput internal APIs.
However, it is not well-suited for direct browser consumption. Browsers cannot easily handle raw HTTP/2 framing, requiring the use of a gRPC-Web proxy (like Envoy) to translate requests, which adds operational overhead.

## 4. Monorepo with Turborepo

A monorepo is a single Git repository containing all related code, typically divided into multiple distinct packages and applications.
The benefits are substantial: atomic commits across projects, effortless sharing of TypeScript types and utility functions, unified linting and testing tooling, and single `node_modules` installation hoisting (via npm/pnpm workspaces).
A standard monorepo structure might look like this:
```text
apps/
  web/          (The main Next.js application)
  api/          (An Express or Hono backend service)
packages/
  ui/           (A shared library of React components)
  db/           (The Prisma schema and generated database client)
  validators/   (Zod validation schemas shared between client and server)
  config/       (Shared tsconfig.json and .eslintrc files)
```
Turborepo is a high-performance build system for JavaScript/TypeScript monorepos. You configure it via a `turbo.json` pipeline definition:
```json
{
  "$schema": "https://turbo.build/schema.json",
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": [".next/**", "dist/**"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "lint": {},
    "typecheck": {}
  }
}
```
The declaration `"dependsOn": ["^build"]` is crucial: it tells Turborepo that before building a specific package, it must first successfully build all of that package's local workspace dependencies.
Turborepo utilizes aggressive local caching. Before running a task, it hashes the inputs (source files, environment variables, dependent package hashes). If the hash matches a previous run, it skips the execution entirely and instantly restores the outputs from the local cache.
Remote caching takes this further by pushing the cache to a remote server (like Vercel). This means your CI/CD pipelines are cache-aware across different workflow runs and physical machines, drastically reducing build times.
You can execute commands targeted at specific applications using filters: running `turbo run build --filter=web` will intelligently build only the `web` application and the specific local packages it depends on.

## 5. Database Access Patterns

**Prisma ORM:**
Prisma utilizes a schema-first approach. You define your data models, relations, and database indexes in a declarative `schema.prisma` file.
Based on this schema, Prisma automatically generates a highly type-safe database client. There is no traditional ORM object mapping magic; it simply provides a typed interface for executing SQL queries.
The command `prisma migrate dev` analyzes changes to your schema, generates standard SQL migration files, and applies them to your development database safely.
The command `prisma generate` must be run whenever the schema changes to update the TypeScript client types in your `node_modules`.
Prisma handles complex database relations elegantly, supporting one-to-many, many-to-many (both implicit and explicit), and self-referencing relations.
When you need extreme performance or complex queries not supported by the query builder, Prisma provides a raw SQL escape hatch via `prisma.$queryRaw` and `prisma.$executeRaw`, which use tagged template literals to guarantee protection against SQL injection attacks.

**Connection Pooling in Serverless Environments:**
Serverless environments (like AWS Lambda or Vercel Edge Functions) present a severe problem for traditional relational databases. Because these functions are ephemeral and stateless, a sudden spike in traffic can cause thousands of concurrent function invocations. If each invocation opens a new database connection, you will rapidly exhaust PostgreSQL's `max_connections` limit, causing your application to crash.
Prisma Accelerate offers a managed connection pooler. Your serverless functions connect to the global Accelerate proxy, which intelligently multiplexes those requests onto a small, fixed pool of actual database connections.
Alternatively, you can self-host PgBouncer, configuring it in "transaction mode," which is designed specifically for serverless architectures by allocating connections per transaction rather than per session.
Modern serverless-native databases like Neon or PlanetScale abstract this entirely by providing built-in, HTTP-based connection pooling that scales infinitely.

**Drizzle ORM:**
Drizzle is an SQL-first ORM designed to provide a TypeScript API that mirrors raw SQL syntax as closely as possible.
It is significantly lighter weight than Prisma because it does not require a separate, heavy Rust-based query engine binary to run in production. This makes it an excellent choice for deployment on highly constrained Edge runtimes (like Cloudflare Workers).
It boasts broad compatibility, working seamlessly with SQLite (`better-sqlite3`), PostgreSQL (`postgres`), MySQL (`mysql2`), and specialized serverless drivers.

**Repository Pattern:**
The Repository Pattern is a structural design pattern that abstracts database access logic behind strictly defined interfaces. By doing this, you can decouple your core business logic from the specific ORM or database technology you are using.
This architecture makes your application incredibly testable, as you can easily swap out the real database implementation for an in-memory mock during unit testing.
```ts
// Define the contract
export interface UserRepository {
  findById(id: string): Promise<User | null>;
  create(data: CreateUserInput): Promise<User>;
}

// The concrete implementation using Prisma
export class PrismaUserRepository implements UserRepository {
  constructor(private prisma: PrismaClient) {}
  
  async findById(id: string) {
    return this.prisma.user.findUnique({ where: { id } });
  }
  
  async create(data: CreateUserInput) {
    return this.prisma.user.create({ data });
  }
}

// A mock implementation for fast unit tests without a database
export class InMemoryUserRepository implements UserRepository {
  private users: User[] = [];
  
  async findById(id: string) {
    return this.users.find(u => u.id === id) || null;
  }
  
  async create(data: CreateUserInput) {
    const newUser = { id: Math.random().toString(), ...data };
    this.users.push(newUser);
    return newUser;
  }
}
```

## 6. Containerization & CI/CD

**Multi-stage Dockerfile for Next.js:**
Writing an optimized multi-stage Dockerfile is critical for Next.js applications to ensure the final production image is as small and secure as possible.
```dockerfile
# Stage 1: Define the base environment
FROM node:20-alpine AS base

# Stage 2: Install dependencies strictly
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json ./
# Use 'ci' for reproducible builds
RUN npm ci --frozen-lockfile

# Stage 3: Build the application
FROM base AS builder
WORKDIR /app
# Copy installed node_modules from the deps stage
COPY --from=deps /app/node_modules ./node_modules
# Copy all application source code
COPY . .
# Execute the Next.js build process
RUN npm run build

# Stage 4: Create the final minimal production image
FROM base AS runner
WORKDIR /app
ENV NODE_ENV production
# Create a non-root user for security best practices
RUN addgroup --system nodejs
RUN adduser --system nextjs
# Only copy the absolutely necessary files
COPY --from=builder /app/public ./public
# Copy the standalone build output and static assets
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
# Switch to the non-root user before running the application
USER nextjs
EXPOSE 3000
# Run the minimal standalone server
CMD ["node", "server.js"]
```
To utilize this Dockerfile effectively, you must configure `output: 'standalone'` in your `next.config.ts`. This instructs Next.js to bundle only the exact Node.js dependencies required into the standalone directory, eliminating the need to copy the massive `node_modules` folder into the final runner image.

**GitHub Actions CI/CD Pipeline:**
A robust CI/CD pipeline ensures code quality before deployment.
```yaml
name: Continuous Integration

on:
  push:
    branches: ["main"]
  pull_request:
    branches: ["main"]

jobs:
  validate-and-build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository source code
        uses: actions/checkout@v4
        
      - name: Set up Node.js environment
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          
      - name: Install dependencies cleanly
        run: npm ci
        
      - name: Run strict TypeScript typechecking
        run: npm run typecheck
        
      - name: Execute ESLint rules
        run: npm run lint
        
      - name: Execute Unit and Integration Tests
        run: npm run test
        
      - name: Execute Production Build
        run: npm run build
```

## 7. Observability

**OpenTelemetry in Next.js:**
Next.js provides first-class support for OpenTelemetry. You configure it by creating an `instrumentation.ts` file at the root of your project. Here, you register your tracer and configure auto-instrumentation for standard HTTP modules.
OpenTelemetry provides distributed tracing that seamlessly spans across Next.js Server Components, standard Route Handlers, and Server Actions.
You can then export this standardized telemetry data to any OTLP-compatible backend system for visualization and analysis, such as Jaeger, Grafana Tempo, or commercial solutions.

**Sentry Integration:**
Sentry is widely used for error tracking. The `@sentry/nextjs` package provides a `withSentryConfig` wrapper that you apply to your `next.config.ts`.
This wrapper automatically injects SDKs to capture unhandled exceptions on both the client and server, automatically uploading sourcemaps to ensure stack traces are readable.
Sentry also provides performance monitoring features, capturing transaction traces for page loads and API route executions to help identify bottlenecks.
Session Replay is a powerful feature that records the user's actual interactions leading up to an error, providing invaluable context for debugging complex UI issues.

**Structured Logging with Pino:**
Relying on standard `console.log` is insufficient for production backend services. You should use a structured JSON logging library like Pino.
Structured logging ensures that every log entry is a parseable JSON object containing critical metadata: `{ level: 30, time: 1629..., msg: "User logged in", requestId: "abc-123", userId: "user-456" }`.
Implementing Correlation IDs is essential. Using Node's `AsyncLocalStorage`, you can assign a unique UUID at the start of an HTTP request and automatically attach it to every single log line generated during that request lifecycle, allowing you to trace the complete flow of execution across multiple functions.
During local development, you pipe Pino's output through `pino-pretty` to get readable formatted text, while in production, you output raw JSON to be ingested and parsed by log aggregation platforms like Datadog, Splunk, or Grafana Loki.

**Core Web Vitals (CWV):**
Monitoring real user performance metrics is critical.
LCP (Largest Contentful Paint) measures how long it takes to render the largest visible element in the viewport. The target for a good user experience is less than 2.5 seconds.
CLS (Cumulative Layout Shift) measures unexpected layout shifts that occur as the page loads. The target is a score of less than 0.1. Using the Next.js `<Image>` component with defined `width` and `height` properties is the primary way to prevent CLS caused by images.
INP (Interaction to Next Paint) has replaced FID. It measures the overall responsiveness of the page to user input (clicks, taps). The target is a delay of less than 200 milliseconds.
You can monitor these metrics programmatically in Next.js by exporting the `reportWebVitals` function, which receives these metrics directly from the browser, allowing you to send them to your own analytics backend.

---

## 8. Multi-Tenant Architecture Patterns

### Subdomain-Based Multi-Tenancy with Next.js Middleware

In SaaS products, each customer (tenant) often gets their own subdomain: `acme.app.com`, `globex.app.com`. Routing is handled entirely in Middleware before any Server Component runs.

```ts
// middleware.ts
import { NextRequest, NextResponse } from 'next/server';

export function middleware(req: NextRequest) {
  const hostname = req.headers.get('host') ?? '';
  const rootDomain = process.env.NEXT_PUBLIC_ROOT_DOMAIN; // e.g. 'app.com'
  const subdomain = hostname.replace(`.${rootDomain}`, '');

  // If request is for a tenant subdomain, rewrite to tenant route
  if (subdomain && subdomain !== 'www' && hostname !== rootDomain) {
    return NextResponse.rewrite(
      new URL(`/tenant/${subdomain}${req.nextUrl.pathname}`, req.url)
    );
  }

  return NextResponse.next();
}

export const config = { matcher: ['/((?!_next|favicon.ico).*)'] };
```

The rewritten path `tenant/[slug]/...` maps to a route group in the app directory. Server Components within this group call `auth()` to verify the session belongs to that tenant, then filter all DB queries by `tenantId`.

### Database Isolation Strategies

Three approaches with different isolation levels:

| Strategy | Isolation | Cost | Complexity |
|---|---|---|---|
| Database per tenant | Full | High | High |
| Schema per tenant (Postgres) | Strong | Medium | Medium |
| Row-level (shared table + `tenant_id`) | Soft | Low | Low + RLS |

Row-Level Security (RLS) in PostgreSQL enforces tenant isolation at the DB level:

```sql
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON orders
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
```

Set the tenant context at the start of each DB transaction:
```ts
await db.$executeRaw`SELECT set_config('app.current_tenant_id', ${tenantId}, true)`;
```

---

## 9. Deployment Patterns

### Multi-Stage Dockerfile for Next.js

The `output: 'standalone'` mode in `next.config.ts` bundles a minimal Node.js server with only the files needed at runtime. The final Docker image contains no `node_modules` directory.

```dockerfile
FROM node:20-alpine AS base

# Step 1: Install dependencies only
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --frozen-lockfile

# Step 2: Build the Next.js application
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Step 3: Production image — minimal
FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT=3000
CMD ["node", "server.js"]
```

Final image size is typically 150-250MB vs 1.5GB without multi-stage.

### Docker Compose for Local Development

```yaml
# docker-compose.yml
services:
  web:
    build: .
    ports: ['3000:3000']
    environment:
      DATABASE_URL: postgres://postgres:password@db:5432/mydb
      REDIS_URL: redis://cache:6379
    depends_on:
      db:
        condition: service_healthy
      cache:
        condition: service_started

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_PASSWORD: password
      POSTGRES_DB: mydb
    volumes: ['pg_data:/var/lib/postgresql/data']
    healthcheck:
      test: ['CMD-SHELL', 'pg_isready -U postgres']
      interval: 5s
      timeout: 5s
      retries: 5

  cache:
    image: redis:7-alpine
    ports: ['6379:6379']

volumes:
  pg_data:
```

### GitHub Actions CI Pipeline

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - run: npm ci --frozen-lockfile

      - name: Type check
        run: npm run typecheck

      - name: Lint
        run: npm run lint

      - name: Unit tests
        run: npm run test -- --coverage

      - name: Build
        run: npm run build
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}

      - name: Docker build
        run: docker build -t myapp:${{ github.sha }} .
```

---

## 10. Interview Architecture Scenarios

### Real-Time Chat Application

**Requirements**: users send/receive messages in rooms, presence indicators, message history.

**Stack decision**: WebSockets (full-duplex required, not SSE) + Redis Pub/Sub for horizontal scaling.

```
Client \u2192 WebSocket \u2192 Server Instance A
                             \u2193
                      Redis Pub/Sub Channel (room:123)
                             \u2191
                      Server Instance B \u2192 WebSocket \u2192 Other Client
```

- Messages persisted to PostgreSQL (for history)
- Room membership tracked in Redis (fast presence queries)
- Socket.io with `@socket.io/redis-adapter` handles cross-instance message fanout automatically

### E-Commerce Product Catalog with ISR

**Requirements**: 50,000 products, prices change frequently, fast page loads.

**Architecture**:
- Product pages: ISR with `revalidate: 3600` (1 hour static)
- Price updates: webhook from inventory system calls `revalidateTag('product-prices')` for on-demand revalidation
- Search: Algolia or Typesense (full-text search offloaded from Postgres)
- Images: Next.js `<Image>` with CDN (Cloudflare) for automatic WebP conversion and resizing

### URL Shortener

- `POST /shorten` \u2014 generate 6-char base62 ID, store in Redis (TTL) + PostgreSQL (permanent)
- `GET /:code` \u2014 Redis lookup first (cache hit \u2192 instant redirect), fallback to PostgreSQL
- Analytics: async write to ClickHouse (OLAP) via Kafka topic \u2014 never blocks redirect
- Next.js middleware handles redirects at the edge for minimum latency
