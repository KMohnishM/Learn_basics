# Module 4 Q&A

**1. Explain the difference between server state and client state. How does React Query address server state?**
Client state is UI data that lives only in the browser (e.g., is a modal open, what is the dark mode setting). Server state is data persisted remotely (e.g., users in a database). Server state is asynchronous, shared across multiple clients, and can become out of date. React Query manages server state by handling the complex logic of fetching, caching, deduplicating requests, background syncing (stale-while-revalidate), and garbage collection, separating it entirely from local UI state.

**2. What is the Compound Component pattern? When would you use it?**
The Compound Component pattern involves creating multiple components that work together and share state implicitly via Context, providing a cohesive API. You use it when you want to build flexible UI components like Tabs, Accordions, or Menus, where the parent manages the state and child components render based on that state, without forcing the user to pass props through multiple levels manually (e.g., `<Tabs>`, `<Tabs.List>`, `<Tabs.Panel>`).

**3. When would you choose Zustand over Redux Toolkit? What are the trade-offs?**
Choose Zustand for modern, lightweight applications. Zustand requires no boilerplate, no Context Provider wrapping, and is heavily optimized. Choose Redux Toolkit (RTK) for massive enterprise applications, legacy codebases, or when you specifically need Redux DevTools' time-travel debugging, complex middleware, or a very strict, opinionated structure. Trade-off: Zustand is flexible but unopinionated, meaning teams must enforce their own architectural patterns.

**4. What does `React.memo` do? What are the cases where it does NOT help performance?**
`React.memo` prevents a component from re-rendering if its props have not changed (via shallow comparison). It does NOT help (and actually hurts performance via comparison overhead) if the parent component constantly passes new references, such as inline arrow functions `() => {}` or new objects `{{ style: 'red' }}` as props, because the shallow equality check will fail on every render anyway.

**5. What is the RTL philosophy? Why should you not test implementation details?**
React Testing Library's philosophy is: "The more your tests resemble the way your software is used, the more confidence they can give you." You shouldn't test implementation details (like asserting that a specific internal `useState` variable changed to true) because it makes tests brittle. If you refactor your component to use `useReducer` instead of `useState` but the UI behavior is identical, the test shouldn't break. You should test DOM interactions (e.g., clicking a button shows a success message).

**6. How does code splitting with `React.lazy()` work? What is the network impact?**
`React.lazy()` allows you to dynamically `import()` a component only when it is rendered. Webpack or Vite will bundle that component into a separate JavaScript chunk. The network impact is that the initial bundle size downloaded by the user is significantly smaller, improving initial load time. The split chunk is requested over the network only when the user navigates to the UI that requires it (handled via a Suspense boundary).

**7. What is RTK Query? How does it differ from React Query?**
RTK Query is an advanced data fetching and caching tool built directly into Redux Toolkit. It solves the same problems as React Query (caching, server state). The primary difference is integration: RTK Query integrates deeply into the Redux store, allowing you to use Redux middleware and access cached data via Redux state selectors, whereas React Query is entirely independent and stores its cache outside of Redux.

**8. Explain the Render Props pattern and why custom hooks largely replaced it.**
Render Props is a pattern where a component receives a function as a prop (often `children`), and that function returns React elements. It was used to share stateful logic (e.g., `<MouseTracker render={(x, y) => <Cursor x={x} y={y} />} />`). Custom hooks largely replaced this because hooks allow you to share the exact same logic without creating "wrapper hell" (deeply nested component trees) and are much cleaner to write (`const { x, y } = useMouse()`).

**9. How does React Router v6's `loader` function improve data fetching compared to `useEffect`?**
Using `useEffect` for data fetching leads to "render-then-fetch" waterfalls. The component must render first, then the effect fires, causing the fetch to start, leaving the user staring at a spinner. React Router v6 `loader` functions execute *before* the route renders (fetch-then-render or fetch-in-parallel). The router waits for the loader to resolve, then renders the component with the data already available via `useLoaderData()`.

**10. What is optimistic updating in React Query? Walk through a `useMutation` example.**
Optimistic updating means updating the UI immediately to reflect the expected outcome of a mutation before the server has responded, creating a snappy user experience. In a `useMutation` for "liking a post", you configure `onMutate` to cancel outgoing queries, snapshot the old cache data, and manually update the cache to increment the like count. If the server request fails, the `onError` callback rolls the cache back to the snapshot.

**11. When would you use React Hook Form's `Controller` component vs `register`?**
You use `register` for native HTML inputs (`<input>`, `<select>`) because it passes native `ref`, `onChange`, and `onBlur` directly to the DOM element, leaving the component completely uncontrolled and highly performant. You use `Controller` when integrating with external UI libraries (like Material UI or React Select) that don't expose native refs easily or require custom data handling to update their internal controlled state.

**12. How do you type a Higher-Order Component in TypeScript correctly?**
Typing HOCs involves ensuring the props of the wrapped component are preserved.
```typescript
function withLogger<P extends object>(WrappedComponent: React.ComponentType<P>) {
  return function WithLoggerComponent(props: P) {
    useEffect(() => console.log('Mounted'), []);
    return <WrappedComponent {...props} />;
  }
}
```

**13. What is `useDeferredValue`? Give a real UI example where it improves user experience.**
`useDeferredValue` takes a value and returns a new copy of it that intentionally lags behind the original during heavy renders. 
Example: A search input that filters a massive list of 10,000 items. The input state (`query`) must update immediately so typing feels responsive. By passing `query` into `useDeferredValue(query)` and using the deferred value to filter the list, React keeps the input snappy and renders the heavy list filtering in the background as a low-priority transition.

**14. Explain cache invalidation in React Query. What triggers a refetch?**
Cache invalidation marks specific query keys as "stale." When you run `queryClient.invalidateQueries(['todos'])`, React Query will immediately refetch that data if the query is currently active (visible on screen). If it's inactive, it will refetch the next time the component mounts. Automatic refetches also trigger by default on window focus, network reconnection, and component mount (if the data is stale).

**15. What is the difference between `getBy`, `queryBy`, and `findBy` in React Testing Library?**
- `getBy...`: Synchronous. Returns the element if found. Throws an error if not found. Used for elements that should definitely be there.
- `queryBy...`: Synchronous. Returns the element if found. Returns `null` if not found. Used exclusively to assert that an element does NOT exist in the document.
- `findBy...`: Asynchronous. Returns a Promise that resolves when the element is found, up to a timeout (default 1000ms). Used when waiting for an element to appear after an API call or async state update.
