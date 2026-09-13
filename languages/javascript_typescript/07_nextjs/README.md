# Module 7: Next.js Architecture and App Router Deep Dive

Welcome to Module 7 of the Full-Stack TypeScript Curriculum. In this module, we will deeply explore Next.js, the premier React framework. We will focus primarily on the App Router, React Server Components (RSC), advanced routing paradigms, rendering strategies, data fetching, server actions, and deployment considerations.

Next.js fundamentally changes how we build React applications by moving significant portions of the application logic and rendering to the server, resulting in better performance, improved SEO, and a vastly simplified data fetching model.

---

## 1. Next.js Architecture Overview

### Next.js as a React Framework
React is a library for building user interfaces. Out of the box, React does not provide routing, data fetching, server-side rendering, or static site generation. Next.js is a framework built on top of React that provides these missing pieces. 

Key features Next.js adds on top of React include:
- **Routing:** A file-system based router.
- **Rendering:** Server-Side Rendering (SSR), Static Site Generation (SSG), and Incremental Static Regeneration (ISR).
- **Data Fetching:** Simplified data fetching mechanisms integrated into the routing and rendering lifecycle.
- **Styling:** Built-in support for CSS Modules, Sass, and CSS-in-JS.
- **Optimizations:** Automatic image, font, and script optimizations.
- **API Routes:** The ability to build API endpoints directly within the Next.js application.

### Pages Router vs App Router
Next.js currently supports two distinct routing paradigms: the Pages Router and the App Router.

**The Pages Router (`pages/` directory):**
- The original routing system in Next.js.
- Relies on special exported functions like `getServerSideProps` and `getStaticProps` for data fetching.
- Components are primarily client-rendered (even if initially server-rendered for the first payload) and hydrate fully on the client.
- Has a flat routing structure where `pages/about.tsx` maps to `/about`.

**The App Router (`app/` directory):**
- Introduced in Next.js 13 as the new paradigm, built entirely around React Server Components (RSC).
- Data fetching is done simply by making the component an `async` function and using `await fetch()`.
- Nested routing with layouts, loading states, and error handling built directly into the file conventions.
- Significant performance improvements since components are server-rendered by default and send zero JavaScript to the client unless explicitly marked with `'use client'`.

Migration from Pages to App Router is possible incrementally, as Next.js supports running both routers simultaneously in the same project. However, the App Router is the current standard and the recommended approach for all new applications.

### File-based routing conventions side-by-side
- **Pages Router:** `pages/index.tsx` (Route: `/`), `pages/blog/[id].tsx` (Route: `/blog/123`), `pages/api/hello.ts` (API Route).
- **App Router:** `app/page.tsx` (Route: `/`), `app/blog/[id]/page.tsx` (Route: `/blog/123`), `app/api/hello/route.ts` (Route Handler).

---

## 2. App Router — Deep Dive (Current Standard)

The App Router utilizes specific file naming conventions to define the UI and behavior of routes.

### File Conventions
- **`page.tsx`**: Defines the unique UI for a route and makes the path publicly accessible.
- **`layout.tsx`**: Defines UI that is shared across multiple pages (e.g., headers, sidebars). Layouts preserve state and do not re-render on navigation.
- **`loading.tsx`**: Creates a loading UI using React Suspense. It automatically wraps the `page.tsx` and any nested layouts in a `<Suspense>` boundary.
- **`error.tsx`**: Creates an Error Boundary for a route segment. It isolates errors to specific parts of the app without crashing the entire page. Must be a Client Component.
- **`not-found.tsx`**: Rendered when a route segment cannot be found or when the `notFound()` function is called.
- **`route.ts`**: Defines a server-side API endpoint (Route Handler). Cannot exist in the same directory as a `page.tsx`.
- **`middleware.ts`**: Runs before a request is completed, allowing you to modify the response, rewrite, redirect, or add headers.

### Layouts
Layouts allow you to define persistent UI across route segments. 

```tsx
// app/layout.tsx (Root Layout)
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <nav>Global Navigation</nav>
        {children}
      </body>
    </html>
  );
}

// app/dashboard/layout.tsx (Nested Layout)
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <section>
      <aside>Dashboard Sidebar</aside>
      <main>{children}</main>
    </section>
  );
}
```

Every Next.js app using the App Router must have a root layout in `app/layout.tsx` that defines the `<html>` and `<body>` tags. Nested layouts wrap the pages and child layouts beneath them.

### `loading.tsx` and Instant Loading States
Adding a `loading.tsx` file provides instant feedback to the user while the server is rendering the page or fetching data.

```tsx
// app/dashboard/loading.tsx
export default function Loading() {
  return <p>Loading dashboard...</p>; // Can be a skeleton UI
}
```
Behind the scenes, Next.js wraps the `page.tsx` in a `<Suspense fallback={<Loading />}>` boundary.

### `error.tsx`
Error files allow you to handle runtime errors gracefully. 

```tsx
// app/dashboard/error.tsx
'use client'; // Error components must be Client Components

import { useEffect } from 'react';

export default function Error({ error, reset }: { error: Error & { digest?: string }, reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div>
      <h2>Something went wrong in the dashboard!</h2>
      <button onClick={() => reset()}>Try again</button>
    </div>
  );
}
```
The `reset` function attempts to re-render the Error boundary's contents. You can also use `useRouter().refresh()` for a full route refresh.

### Route Groups `(folder)`
Route groups allow you to logically organize your files without affecting the URL path. By wrapping a folder name in parentheses, it is excluded from the route's URL path.

Example:
- `app/(marketing)/about/page.tsx` resolves to `/about`.
- `app/(marketing)/layout.tsx` applies only to routes within the `(marketing)` group.

### Parallel Routes `@folder`
Parallel Routes allow you to simultaneously or conditionally render one or more pages in the same layout. They are defined using named slots (folders starting with `@`).

Example structure:
- `app/dashboard/layout.tsx`
- `app/dashboard/@analytics/page.tsx`
- `app/dashboard/@team/page.tsx`

```tsx
// app/dashboard/layout.tsx
export default function DashboardLayout({
  children,
  analytics,
  team,
}: {
  children: React.ReactNode;
  analytics: React.ReactNode;
  team: React.ReactNode;
}) {
  return (
    <>
      {children}
      {team}
      {analytics}
    </>
  );
}
```

### Intercepting Routes `(.)`, `(..)`, `(...)`
Intercepting routes allow you to load a route from another part of your application within the current layout. This is highly useful for modal patterns.
- `(.)` to match segments on the same level
- `(..)` to match segments one level above
- `(..)(..)` to match segments two levels above
- `(...)` to match segments from the root `app` directory

If you navigate from a feed to a photo, the photo can open in a modal (intercepting route). If you hard refresh, the full photo page loads.

---

## 3. React Server Components (RSC) — The Fundamental Shift

React Server Components represent a paradigm shift in how we build React applications.

### Server Components
By default, all components inside the `app/` directory are Server Components.
- They are rendered **only** on the server.
- The Javascript code for Server Components is **never** sent to the client. This drastically reduces the client-side bundle size.
- They can be `async` and can securely access server-side resources like databases, filesystems, and environment variables directly.

### Client Components
To add interactivity (e.g., `onClick`, `useState`, `useEffect`, browser APIs), you must use Client Components.
- You opt-in by adding the `'use client'` directive at the top of the file.
- Client Components are rendered on the server (SSR) to generate initial HTML, and then fully hydrated on the client.

```tsx
'use client';

import { useState } from 'react';

export default function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(count + 1)}>Count: {count}</button>;
}
```

### RSC Wire Format
When Server Components render, they do not send raw HTML or JSON to the client. They send a specialized, streaming React payload (the RSC payload). This payload describes the UI tree, including the rendered server components and placeholders for where client components should be injected. The React runtime on the client uses this payload to reconcile the DOM.

### The Composition Rule
- **Server Components CAN render Client Components:** You can safely import a Client Component into a Server Component.
- **Client Components CANNOT import Server Components:** If a Client Component imports a Server Component, that Server Component becomes a Client Component (its code is bundled and sent to the browser). 

**The Workaround (`children` prop):**
To pass a Server Component into a Client Component, pass it as a `children` prop.

```tsx
// ServerComponent.tsx
export default function ServerComponent() {
  return <div>I am rendered on the server!</div>;
}

// ClientWrapper.tsx
'use client';
export default function ClientWrapper({ children }: { children: React.ReactNode }) {
  // Can use state here
  return <div className="client-box">{children}</div>;
}

// page.tsx
import ClientWrapper from './ClientWrapper';
import ServerComponent from './ServerComponent';

export default function Page() {
  return (
    <ClientWrapper>
      <ServerComponent />
    </ClientWrapper>
  );
}
```

### Data Fetching in RSC
Because Server Components can be async, data fetching is incredibly simple. You do not need `useEffect` or libraries like React Query for server-side fetching.

```tsx
// app/users/page.tsx
async function getUsers() {
  const res = await fetch('https://jsonplaceholder.typicode.com/users');
  return res.json();
}

export default async function UsersPage() {
  const users = await getUsers();
  return (
    <ul>
      {users.map(user => (
        <li key={user.id}>{user.name}</li>
      ))}
    </ul>
  );
}
```

---

## 4. Rendering Strategies in App Router

Next.js provides multiple rendering strategies, and they can be mixed and matched within the same application.

### Static Rendering (Default)
Routes are rendered at build time. The result is cached and served from a CDN. This is the fastest rendering strategy and should be the default choice.

### Dynamic Rendering
Routes are rendered at request time. This happens automatically if Next.js detects a dynamic function in your route, such as:
- `cookies()`
- `headers()`
- `searchParams` (in a `page.tsx`)
- Using `unstable_noStore()`

When dynamic rendering is triggered, the route is built on the server on every request.

### Incremental Static Regeneration (ISR)
ISR allows you to create or update static pages after you've built your site. You can use time-based revalidation.

```tsx
// Revalidate every 60 seconds
export const revalidate = 60; 

export default async function Page() {
  const data = await fetch('https://api.example.com/data').then(r => r.json());
  return <div>{data.value}</div>;
}
```

### Streaming
Streaming allows you to progressively send HTML from the server to the client. Next.js uses React Suspense to achieve this. You can send the static "shell" of a page instantly, and stream the slower, data-dependent parts of the UI as they resolve.

```tsx
import { Suspense } from 'react';
import SlowComponent from './SlowComponent';

export default function Page() {
  return (
    <div>
      <h1>Fast Shell</h1>
      <Suspense fallback={<p>Loading slow data...</p>}>
        <SlowComponent />
      </Suspense>
    </div>
  );
}
```

### Partial Prerendering (PPR)
PPR is an experimental feature that combines ultra-fast static edge delivery with fully dynamic capabilities. A static shell is served instantly, while dynamic "holes" (wrapped in Suspense boundaries) are streamed in during the same HTTP request.

---

## 5. Data Fetching & Caching in Next.js 15

Next.js has a comprehensive and aggressive caching architecture. In Next.js 15, the default caching behavior for `fetch` has changed.

### Fetch API Extensions
Next.js extends the native `fetch` API.
- **Next.js 14 default:** `cache: 'force-cache'` (Aggressive caching)
- **Next.js 15 default:** `cache: 'no-store'` (Always dynamic)

To use ISR with fetch:
```ts
fetch('https://api.example.com/data', { next: { revalidate: 60 } });
```

### The Four Cache Layers
1. **Request Memoization:** If you call `fetch()` with the exact same URL and options multiple times in a single render pass (e.g., once in layout, once in page), Next.js automatically dedupes the requests. Only one network request is made.
2. **Data Cache:** Persists the result of data fetches across requests and deployments. Powered by the extended `fetch` API.
3. **Full Route Cache:** At build time, Next.js statically renders routes and caches the HTML and RSC payload. This cache lives on the server.
4. **Router Cache (Client-side):** As a user navigates, the Next.js client-side router caches the RSC payloads of visited segments to prevent redundant requests on backward/forward navigation.

### `unstable_cache`
If you are fetching data from a database directly (not using `fetch`), you can use `unstable_cache` to manually cache the results.

```ts
import { unstable_cache } from 'next/cache';
import db from '@/lib/db';

const getCachedUser = unstable_cache(
  async (id) => db.user.findUnique({ where: { id } }),
  ['user-key'],
  { revalidate: 3600, tags: ['user'] }
);
```

### On-demand Revalidation
You can purge the cache manually based on specific events (like a database update).
- `revalidatePath('/blog')`: Purges the cache for a specific path.
- `revalidateTag('posts')`: Purges the cache for all fetches that were tagged with `'posts'`.

---

## 6. Server Actions

Server Actions are asynchronous functions that run exclusively on the server. They provide a seamless way to handle data mutations without creating dedicated API routes.

### The `'use server'` Directive
You can define a Server Action by adding the `'use server'` directive at the top of an async function.

```tsx
// app/actions.ts
'use server';

import db from '@/lib/db';
import { revalidatePath } from 'next/cache';

export async function createPost(formData: FormData) {
  const title = formData.get('title') as string;
  await db.post.create({ data: { title } });
  revalidatePath('/posts'); // Purge cache so new post appears
}
```

### Form Integration
Server Actions integrate directly with HTML `<form>` elements via the `action` attribute. This enables progressive enhancement—the form will work even if JavaScript is disabled on the client.

```tsx
import { createPost } from '@/app/actions';

export default function NewPostForm() {
  return (
    <form action={createPost}>
      <input name="title" type="text" required />
      <button type="submit">Submit</button>
    </form>
  );
}
```

### Server Action Security
Next.js automatically secures Server Actions:
- They are accessible only via HTTP POST requests.
- Next.js automatically generates and verifies encrypted action IDs to prevent spoofing.
- Built-in CSRF (Cross-Site Request Forgery) protection validates the `Host` and `Origin` headers.

### `useActionState` (formerly `useFormState`)
To handle complex form states (success, errors, pending), use the `useActionState` hook in a Client Component.

```tsx
'use client';
import { useActionState } from 'react';
import { submitForm } from './actions';

export default function Form() {
  const [state, formAction, isPending] = useActionState(submitForm, { message: '' });

  return (
    <form action={formAction}>
      <input name="email" />
      <button disabled={isPending}>Submit</button>
      <p>{state.message}</p>
    </form>
  );
}
```

### `useOptimistic`
The `useOptimistic` hook allows you to optimistically update the UI immediately before the Server Action completes, providing a snappy user experience.

---

## 7. API Routes (`route.ts`)

While Server Actions handle mutations within the app, Route Handlers (`route.ts`) are used for building REST APIs for external consumption, webhooks, or integration with external clients.

### Route Handler Conventions
You export named async functions mapping to HTTP methods (`GET`, `POST`, `PUT`, `DELETE`, `PATCH`).

```ts
// app/api/users/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const id = searchParams.get('id');
  
  return NextResponse.json({ message: `User ID: ${id}` });
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  return NextResponse.json({ success: true, data: body }, { status: 201 });
}
```

Route Handlers use standard Web API `Request` and `Response` objects, extended by Next.js as `NextRequest` and `NextResponse` to provide convenient helpers for cookies and routing.

---

## 8. Middleware

Middleware allows you to run code before a request is completed. 

### Characteristics and Use Cases
- Runs on the **Edge Runtime**, which is highly restricted but incredibly fast.
- Perfect for routing logic, redirects, rewrites, bot protection, and authentication token verification.

```ts
// middleware.ts (in root directory)
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('auth-token');

  if (!token && request.nextUrl.pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  return NextResponse.next();
}

// Limit middleware execution
export const config = {
  matcher: ['/dashboard/:path*'],
};
```

### Limitations
Because Middleware runs on the Edge Runtime, it **cannot** use Node.js specific APIs (like `fs` or `child_process`) and cannot easily connect to traditional relational databases directly (unless via HTTP). You should only do lightweight token verification (like checking JWT signatures) in Middleware.

---

## 9. `next.config.ts` Key Options

The configuration file allows you to customize the Next.js build process.

```ts
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // Allow images from external domains
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'example.com',
      },
    ],
  },
  // Setup redirects
  async redirects() {
    return [
      {
        source: '/old-path',
        destination: '/new-path',
        permanent: true,
      },
    ];
  },
  // Experimental features
  experimental: {
    ppr: true, // Partial Prerendering
    serverActions: {
      bodySizeLimit: '2mb',
    },
  },
};

export default nextConfig;
```

### Environment Variables
Next.js supports `.env` files out of the box.
- `SECRET_KEY=123`: Accessible ONLY on the server (Server Components, API routes, Actions).
- `NEXT_PUBLIC_API_URL=abc`: Accessible on both the server AND the client. The `NEXT_PUBLIC_` prefix exposes the variable to the browser.

---

## 10. Deployment

Next.js provides diverse deployment options.

### Vercel Deployment
Vercel is the company behind Next.js. Deploying to Vercel provides zero-config support for ISR, Serverless Functions, Edge Functions, Image Optimization, and caching. The platform uses a `vercel.json` file for advanced routing configurations.

### Self-Hosting on Node.js / Docker
You can self-host Next.js using Docker. 
Setting `output: 'standalone'` in `next.config.ts` tells Next.js to build a highly optimized Node.js server that only includes the necessary files and `node_modules` for production, drastically reducing the Docker image size.

```ts
// next.config.ts
export default {
  output: 'standalone',
};
```

### Static Export
If you do not need server features (no API routes, no dynamic SSR, no Server Actions), you can configure Next.js to output a purely static HTML/CSS/JS application.

```ts
// next.config.ts
export default {
  output: 'export',
};
```
The output will be placed in the `out/` directory, which can be deployed to any static host (S3, GitHub Pages, Nginx).

### OpenTelemetry Support
Next.js natively supports OpenTelemetry for deep tracing and observability. By enabling it and creating an `instrumentation.ts` file, you can integrate with platforms like Datadog, New Relic, or Sentry to trace requests across Server Components and Server Actions.
