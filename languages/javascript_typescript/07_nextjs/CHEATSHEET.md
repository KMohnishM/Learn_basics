# Next.js App Router Cheatsheet

## 📂 App Router File Conventions

| File | Purpose | Notes |
|---|---|---|
| `page.tsx` | Defines the unique UI for a route. | Makes the route publicly accessible. |
| `layout.tsx` | Shared UI across multiple pages. | Preserves state, does not re-render on navigation. |
| `loading.tsx` | Loading UI for the route segment. | Automatically wraps page in `<Suspense>`. |
| `error.tsx` | Error UI for the route segment. | Wraps page in `<ErrorBoundary>`. Must be Client Component. |
| `not-found.tsx` | UI displayed when `notFound()` is called. | Handles 404s for the segment. |
| `route.ts` | Server-side API endpoint. | Cannot exist in the same folder as a `page.tsx`. |
| `template.tsx` | Similar to layout, but remounts. | Creates a new instance (resets state) on navigation. |
| `middleware.ts` | Intercepts requests globally. | Must be in the root directory. Runs on Edge Runtime. |

---

## ⚖️ Server Components vs Client Components

| Feature | Server Component (Default) | Client Component (`'use client'`) |
|---|---|---|
| Execution Environment | Server only | Server (SSR) + Client (Hydration) |
| JavaScript sent to Client | **Zero** | Yes (Code is bundled) |
| Async/Await Data Fetching | ✅ Yes (directly in component) | ❌ No (use `use`, React Query, or `useEffect`) |
| Access Database directly | ✅ Yes | ❌ No (Security risk) |
| Use State (`useState`) | ❌ No | ✅ Yes |
| Use Effects (`useEffect`) | ❌ No | ✅ Yes |
| Browser APIs (`window`, DOM)| ❌ No | ✅ Yes |
| Event Listeners (`onClick`) | ❌ No | ✅ Yes |

**Composition Rule:** Server Components can import Client Components. Client Components *cannot* import Server Components (pass them as `children` instead).

---

## 🚀 Next.js Rendering Strategies

| Strategy | Description | When to Use | Triggered By |
|---|---|---|---|
| **Static (Default)** | Rendered at build time. Cached on CDN. | Marketing pages, blogs, docs. | Default behavior. |
| **Dynamic** | Rendered on demand on the server per request. | Dashboards, user-specific data. | Using `cookies()`, `headers()`, `searchParams`. |
| **ISR** | Statically built, but updates in background via timer. | E-commerce catalogs, news feeds. | `fetch(url, { next: { revalidate: 60 } })` |
| **Streaming** | Sends UI shell instantly, streams data later. | Pages with slow queries. | `<Suspense>` boundaries. |

---

## 🗄️ Next.js Caching Layers

| Layer | Where it Lives | What it Caches | Lifespan | How to Purge |
|---|---|---|---|---|
| **Request Memoization** | Server Memory | Identical `fetch()` requests | Single render pass | N/A (clears automatically) |
| **Data Cache** | Server (Persistent)| Responses from `fetch()` | Across requests/deployments | `revalidatePath`, `revalidateTag` |
| **Full Route Cache** | Server (Persistent)| HTML & RSC Payload | Across requests | Redeploy or `revalidatePath` |
| **Router Cache**| Client Browser | RSC Payload (for navigation) | User session / Time-based | Refreshing page, Server Actions |

---

## ⚡ Server Actions vs API Routes

| Feature | Server Actions (`'use server'`) | API Routes (`route.ts`) |
|---|---|---|
| Primary Use Case | Form submissions, data mutations within app | External webhooks, public REST APIs |
| HTTP Method | Automatically POST | Define GET, POST, PUT, DELETE, etc. |
| Integration | Passed directly to `<form action={...}>` | Called via client-side `fetch()` |
| Security | Auto CSRF protection, encrypted action IDs | Must manually implement security |
| Progressive Enhancement| Works without JavaScript enabled | Requires JavaScript |

---

## 🧩 Helpful Code Snippets

### Caching and Revalidation
```typescript
// ISR: Revalidate every 60 seconds
fetch('https://api.example.com', { next: { revalidate: 60 } })

// Tag-based Revalidation
fetch('https://api.example.com', { next: { tags: ['posts'] } })

// Purge Cache (Server Action / Route Handler)
import { revalidateTag, revalidatePath } from 'next/cache';
revalidateTag('posts');
revalidatePath('/dashboard');
```

### Passing Server Components to Client Components
```tsx
// ❌ WRONG: Don't import Server in Client
'use client'
import ServerComponent from './ServerComponent'

// ✅ RIGHT: Pass as children
'use client'
export default function ClientWrapper({ children }: { children: React.ReactNode }) {
  return <div>{children}</div>
}
// Usage in page.tsx: <ClientWrapper><ServerComponent /></ClientWrapper>
```
