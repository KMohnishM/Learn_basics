# Module 7: Next.js QnA

Here are 15 common questions and detailed answers regarding Next.js and the App Router architecture.

### 1. What is a React Server Component? How is it different from a Client Component? What is the `'use client'` directive?
**Answer:**
A React Server Component (RSC) is a component that executes and renders exclusively on the server. Its JavaScript code is never bundled or sent to the browser, significantly reducing the client-side payload. Server Components can be asynchronous, allowing direct and secure access to backend resources like databases and filesystems. 
A Client Component, conversely, is rendered on both the server (for initial HTML) and the client (hydration). It can use browser APIs, state (`useState`), and lifecycle hooks (`useEffect`). 
The `'use client'` directive is a pragma placed at the top of a file to declare the boundary between the Server Component module graph and the Client Component module graph, explicitly marking the component and its imports to be included in the client-side JavaScript bundle.

### 2. Can a Client Component import a Server Component? What is the workaround using the `children` prop?
**Answer:**
No, a Client Component cannot directly import a Server Component. If you try to do so, Next.js will silently treat the imported component as a Client Component, bundling its code for the browser (which can leak secrets or cause errors if it uses Node-specific APIs).
The workaround is composition via the `children` prop. A Server Component can render a Client Component and pass another Server Component to it as `children`. In this model, the Server Component is evaluated on the server, and its serialized output (the RSC payload) is passed to the Client Component placeholder.

### 3. What is the difference between ISR, static rendering, and dynamic rendering in Next.js App Router?
**Answer:**
- **Static Rendering:** Pages are rendered at build time. The HTML and RSC payload are cached on a CDN and served instantly to users. This is the default in Next.js.
- **Dynamic Rendering:** Pages are rendered at request time on the server. This is automatically triggered when a page relies on dynamic data (e.g., `cookies()`, `headers()`, `searchParams`, or data fetches lacking cache instructions).
- **ISR (Incremental Static Regeneration):** A hybrid approach where pages are built statically, but can be updated in the background without a full rebuild. Using time-based revalidation (`revalidate: 60`), Next.js serves the cached page but triggers a background regeneration if the cache has expired.

### 4. Explain Next.js 15's caching model. What are the four cache layers?
**Answer:**
Next.js features an aggressive caching architecture consisting of four layers:
1. **Request Memoization (Server):** Dedupes identical `fetch` requests within the same render pass (e.g., a layout and a page requesting the same user data).
2. **Data Cache (Server):** Persists `fetch` responses across incoming requests and deployments. (Note: Next.js 15 defaults `fetch` caching to `no-store`).
3. **Full Route Cache (Server):** Stores the statically generated HTML and RSC payload for routes at build time.
4. **Router Cache (Client):** An in-memory cache in the browser that stores the RSC payloads of visited route segments to ensure instant forward/backward navigation without hitting the server.

### 5. What are Server Actions? What security does Next.js automatically provide for them?
**Answer:**
Server Actions are asynchronous functions executed on the server that can be called directly from Client or Server Components, typically used for handling form submissions and data mutations.
Next.js automatically provides significant security:
- They inherently use HTTP POST requests.
- They have built-in CSRF protection by validating the `Host` and `Origin` headers.
- Next.js encrypts the action IDs, preventing attackers from guessing action URLs or spoofing payloads.

### 6. What is the difference between `revalidatePath()` and `revalidateTag()`?
**Answer:**
Both are used for on-demand ISR (purging the Data and Full Route caches).
- `revalidatePath(path)` purges the cached data for a specific URL path (e.g., `revalidatePath('/blog/post-1')`).
- `revalidateTag(tag)` allows granular cache invalidation across multiple routes. When you fetch data, you can tag the request (`fetch(url, { next: { tags: ['user-data'] } })`). Later, calling `revalidateTag('user-data')` purges all cached requests sharing that tag, regardless of which routes use them.

### 7. When would you use a Route Handler (`route.ts`) instead of a Server Action?
**Answer:**
You use Server Actions when handling data mutations triggered directly by your own Next.js UI (e.g., a user submitting a form or clicking a button). 
You use Route Handlers (`route.ts`) when you need to expose a RESTful API endpoint to the outside world, such as receiving webhooks from Stripe, allowing third-party mobile apps to consume your data, or implementing complex OAuth callbacks that require raw request/response manipulation.

### 8. What is Next.js Middleware? What are its limitations (Edge Runtime)?
**Answer:**
Middleware is code that executes before a request completes, intercepting it to perform tasks like redirecting, rewriting URLs, modifying headers, or verifying authentication tokens.
It is constrained to the Edge Runtime. The limitation is that it does not have access to native Node.js APIs (like `fs`, `child_process`, `crypto` natively) and cannot easily run large NPM packages or connect directly to traditional relational databases via TCP. It is designed to be ultra-fast and lightweight.

### 9. What is Partial Prerendering (PPR)? How does it differ from streaming?
**Answer:**
Streaming (using React Suspense) involves rendering the page on the server at request time, sending the fast parts instantly, and streaming the slow parts.
PPR (Partial Prerendering) takes this further: it statically builds the fast "shell" of the page at build time and caches it on the CDN. When a user requests the page, the static shell is served instantaneously from the edge, while the dynamic "holes" (Suspense boundaries) are evaluated on the server and streamed into the shell dynamically within the same request.

### 10. What is the `NEXT_PUBLIC_` prefix in environment variables and why does it exist?
**Answer:**
By default, environment variables in Next.js are only accessible in the Node.js/Server environment. This prevents sensitive secrets (like database passwords or API keys) from leaking to the browser.
To make an environment variable accessible to Client Components (in the browser), it must be prefixed with `NEXT_PUBLIC_` (e.g., `NEXT_PUBLIC_STRIPE_KEY`). Next.js will inline these specific variables into the client-side JavaScript bundle at build time.

### 11. Explain request memoization vs Data Cache vs Full Route Cache in Next.js.
**Answer:**
- **Request Memoization:** Lifespan of a single server request. Prevents duplicate network calls during one render cycle. (React feature).
- **Data Cache:** Lifespan across multiple requests and deployments. Persists the actual JSON responses from external APIs. (Next.js specific).
- **Full Route Cache:** Lifespan across multiple requests. Persists the fully rendered HTML and RSC payload of a route, preventing React from having to re-render the components. (Next.js specific).

### 12. What is the difference between `loading.tsx` and `error.tsx`? How do they relate to Suspense and Error Boundaries?
**Answer:**
Both are special file conventions that automatically wrap a route segment.
- `loading.tsx` automatically wraps the `page.tsx` and nested layouts inside a React `<Suspense>` boundary. It displays a fallback UI (like a spinner) while the route's async components are resolving.
- `error.tsx` automatically wraps the route segment in a React `<ErrorBoundary>`. It catches unexpected runtime errors that occur during rendering and displays a fallback UI, preventing the entire application from crashing. It must be a Client Component.

### 13. What are Parallel Routes and Intercepting Routes? Give a real use case for each.
**Answer:**
- **Parallel Routes (`@folder`):** Allow rendering multiple pages simultaneously within the same layout. Use case: A complex dashboard where the sidebar, main analytics view, and active user feed are separate, independently loading pages managed by the same layout.
- **Intercepting Routes (`(.)folder`):** Allow loading a route within the current layout while masking the URL. Use case: Clicking a photo in an Instagram feed opens it in a modal without losing the feed's context, but sharing the URL and loading it directly displays the full photo page.

### 14. How do you implement authentication in a Next.js App Router application? What runs in Middleware vs Server Components?
**Answer:**
Authentication generally involves:
1. Validating the session token stored in an HTTP-only cookie.
2. In **Middleware**: Check if the session cookie exists. If missing, redirect protected routes to `/login`. Middleware runs on the edge, so it should only do lightweight checks (like JWT validation) rather than DB lookups.
3. In **Server Components / Server Actions**: Perform deep authorization by querying the database using the session token to ensure the user has specific permissions before fetching secure data or performing mutations.

### 15. How do you self-host a Next.js application with Docker? What does `output: 'standalone'` do?
**Answer:**
You self-host using a multi-stage Dockerfile. Next.js optimizes this via the `output: 'standalone'` setting in `next.config.ts`.
When enabled, the Next.js build process traces imports and creates a minimal standalone folder containing a self-contained Node.js server, copying only the necessary files and specific dependencies from `node_modules`. This eliminates the need to install all dependencies in the production Docker image, massively reducing the image size.
