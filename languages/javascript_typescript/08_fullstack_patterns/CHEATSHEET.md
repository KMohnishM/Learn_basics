# Full-Stack Patterns Cheatsheet

## 🔌 API Paradigm Decision Matrix

| Paradigm | How it Works | Best Used For | Drawbacks |
|---|---|---|---|
| **REST** | URL paths represent resources, HTTP verbs dictate actions. | Public APIs, generic microservices, simple CRUD. | Over-fetching / Under-fetching, manual typing. |
| **GraphQL** | Single endpoint, client defines data shape in request. | Complex mobile apps, mitigating over-fetching, aggregating data. | Complex caching, N+1 query problem, heavy setup. |
| **tRPC** | Shares TypeScript inference directly from server to client. | Internal APIs, Monorepos (Next.js/React Native). | Client and Server must both be TypeScript. |
| **gRPC** | Binary Protobufs over HTTP/2. | Internal Microservice to Microservice communication. | Not human readable, poor direct browser support. |

---

## 📡 Real-Time Communication

| Protocol | Direction | State | Use Cases | Network Implication |
|---|---|---|---|---|
| **WebSockets** | Full-Duplex (Two-way) | Persistent | Chat, Multiplayer Games, Collaborative Docs | Requires load-balancer configuration, complex scaling. |
| **Server-Sent Events (SSE)**| Unidirectional (Server → Client) | Persistent | Live Feeds, Stock Tickers, Notifications | Native HTTP support, easier to scale, subject to max connection limits. |
| **Long Polling** | Unidirectional | Request/Response | Legacy fallback | High overhead (creating/closing connections). |

---

## 📦 Turborepo Configuration (`turbo.json`)

```json
{
  "$schema": "https://turbo.build/schema.json",
  "pipeline": {
    "build": {
      "dependsOn": ["^build"], // A package must wait for its dependencies to build first
      "outputs": [".next/**", "dist/**"] // Files to cache
    },
    "lint": {
      "dependsOn": [] // Can run independently in parallel
    },
    "dev": {
      "cache": false, // Never cache long-running dev servers
      "persistent": true // Indicates a long-running process
    }
  }
}
```

---

## 🗃️ Prisma Cheat Sheet

| Command / Concept | Action | Note |
|---|---|---|
| `npx prisma init` | Initialize Prisma | Creates `prisma/schema.prisma` and `.env` |
| `npx prisma generate` | Generate TypeScript Client | Must run after updating schema. Installs into `node_modules/@prisma/client`. |
| `npx prisma migrate dev` | Apply schema to DB | Creates a SQL migration file and executes it. |
| `npx prisma db push` | Force schema to DB | Directly syncs schema to DB without creating migration history (good for prototyping). |
| `npx prisma studio` | Open GUI | Browser-based UI to view and edit database data. |

**Prisma Schema Example (`schema.prisma`):**
```prisma
model User {
  id    Int     @id @default(autoincrement())
  email String  @unique
  posts Post[]  // One-to-many relationship
}

model Post {
  id       Int    @id @default(autoincrement())
  title    String
  authorId Int
  author   User   @relation(fields: [authorId], references: [id])
}
```

---

## 🔐 Full-Stack Auth Cookie Attributes

| Attribute | Purpose | Security Importance |
|---|---|---|
| `httpOnly=true` | Prevents JS access | **CRITICAL:** Protects session token from Cross-Site Scripting (XSS) attacks. |
| `Secure=true` | HTTPS only | Ensures token is not transmitted in plain text over unencrypted networks. |
| `SameSite=Lax` | Restricts cross-origin sending | **CRITICAL:** Protects against Cross-Site Request Forgery (CSRF). |
| `Max-Age` / `Expires` | Sets expiration | Limits the lifespan of the session if compromised. |

---

## 🐳 Docker Multi-Stage Concept (Visualized)

```text
[ Stage 1: deps ] ----> Installs ALL npm packages (slow, heavy)
        |
        v
[ Stage 2: builder ] -> Copies code, runs `npm run build`
        |
        v
[ Stage 3: runner ] --> Copies ONLY `.next/standalone` & `public/`
                        Result: Ultra-lightweight production image (~100MB)
```
