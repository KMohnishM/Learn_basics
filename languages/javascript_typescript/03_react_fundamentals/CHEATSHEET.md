# Module 3 Cheatsheet

## React Hooks Quick Reference

| Hook | Purpose | When to Use | When NOT to Use |
|------|---------|-------------|-----------------|
| `useState` | Local component state | Any time you need data to trigger a re-render. | For derived values that can be calculated during render. |
| `useEffect` | Side effects & external sync | Network requests, event listeners, subscriptions. | Do NOT use to sync state with other state (derived state). |
| `useRef` | Mutable value persisting across renders | Accessing DOM elements, storing timers, previous values. | Do NOT use for data that should trigger a re-render on change. |
| `useMemo` | Memoizing a computed value | Expensive calculations, creating stable objects for deps. | Premature optimization on cheap calculations. |
| `useCallback` | Memoizing a function reference | Passing stable callbacks to memoized child components. | When passing functions to native DOM elements. |
| `useContext` | Consuming Context API | Accessing global UI state (theme, locale) deeply in tree. | For high-frequency state updates (causes massive re-renders). |
| `useReducer` | Complex local state logic | State that relies on previous state or multiple sub-values. | Simple boolean flags or strings. |
| `useLayoutEffect` | Synchronous DOM mutations | Reading DOM sizes/positions to prevent flickering. | 99% of normal side effects. It blocks the browser paint. |

## `useEffect` Dependency Array Rules

```typescript
// 1. No dependency array
useEffect(() => { ... }); 
// Runs on mount AND after EVERY single render. Usually a bug.

// 2. Empty dependency array
useEffect(() => { ... }, []); 
// Runs EXACTLY ONCE on mount. Cleanup runs on unmount. 

// 3. Specific dependencies
useEffect(() => { ... }, [id, query]); 
// Runs on mount, and re-runs if 'id' or 'query' change between renders.
```

## React Render Lifecycle (Hooks Era)

```text
+-------------------------------------------------------------+
|                        RENDER PHASE                         |
| (Pure, no side effects, interruptible by Concurrent React)  |
+-------------------------------------------------------------+
                            |
                     Trigger State Update
                            |
                 React calls component function
                            |
                  Calculate Virtual DOM diff
                            |
+-------------------------------------------------------------+
|                        COMMIT PHASE                         |
| (Synchronous, mutations applied to DOM, uninterruptible)    |
+-------------------------------------------------------------+
                            |
            Mutate actual DOM to match Virtual DOM
                            |
                 Run `useLayoutEffect` hooks
                            |
                   Browser Paints Screen
                            |
                   Run `useEffect` hooks
```

## React 18 Concurrent Features Summary

- **Automatic Batching:** Multiple `setState` calls anywhere (promises, timeouts, native events) are batched into one render.
- **`useTransition`:** `const [isPending, startTransition] = useTransition();` Marks state updates wrapped in `startTransition` as low priority, keeping UI responsive.
- **`useDeferredValue`:** `const deferredText = useDeferredValue(text);` Creates a lagging version of a value to defer rendering of heavy UI components.
- **Suspense:** `<Suspense fallback={<Spinner />}><HeavyUI /></Suspense>` Shows a fallback while waiting for code or data to load.
