# Module 4 Cheatsheet

## State Management Tool Comparison

| Solution | Best For | Complexity | Re-render Control | 
|----------|----------|------------|-------------------|
| **Local State (`useState`)** | UI state tied to a single component (inputs, toggles) | Low | Controlled natively |
| **Context API** | Low-frequency global state (themes, auth tokens) | Low-Med | Poor (re-renders all consumers) |
| **Zustand** | Modern global client state | Low | Excellent (selector subscriptions) |
| **Redux Toolkit** | Massive apps, strict architecture, time-travel needs | High | Excellent (via selectors) |
| **React Query** | Server state (API data caching, mutations, syncing) | Med | Excellent (structural sharing) |

## React Testing Library Query Priority

When selecting elements in tests, prioritize queries in this order to mimic user behavior:

1. **Accessible to Everyone (Preferred):**
   - `getByRole` (e.g., `getByRole('button', { name: /submit/i })`)
   - `getByLabelText` (for form inputs)
   - `getByPlaceholderText`
   - `getByText`
2. **Semantic Queries:**
   - `getByAltText` (images)
   - `getByTitle`
3. **Test IDs (Last Resort):**
   - `getByTestId` (Only use when text/roles are dynamic or impossible to target securely).

## React Router v6 Quick Reference

```typescript
// Route Definitions
import { createBrowserRouter, RouterProvider, Outlet } from 'react-router-dom';

// Data Loader Hook
const data = useLoaderData(); // Access data fetched by route loader

// Navigation Hooks
const navigate = useNavigate(); // Imperative navigation: navigate('/dashboard')
const { userId } = useParams(); // URL params: /users/:userId
const [searchParams, setSearchParams] = useSearchParams(); // Query string manipulation
const location = useLocation(); // Current path, hash, state

// Fetcher (Data mutation without navigation)
const fetcher = useFetcher();
<fetcher.Form method="post">...</fetcher.Form>
```

## Performance Optimization Checklist

- [ ] **Are you storing derived state?** Remove `useEffect` and calculate it during render.
- [ ] **Is Context causing massive re-renders?** Split Context into separate providers or move to Zustand.
- [ ] **Are you passing inline objects/functions to `React.memo` components?** Wrap them in `useMemo` and `useCallback`.
- [ ] **Is the initial bundle size too large?** Implement `React.lazy()` route-based code splitting.
- [ ] **Is rendering blocking user input?** Wrap heavy background updates in `startTransition`.
- [ ] **Are you duplicating network requests?** Implement React Query to cache and deduplicate.
- [ ] **Is the state actually needed globally?** Lift state up only as far as necessary. Avoid global stores for local component state.
