# Module 3 Q&A

**1. Explain the React Fiber architecture. What is the difference between the render phase and the commit phase?**
React Fiber is a complete rewrite of React's reconciliation engine. It represents a component hierarchy as a linked list of "fiber nodes," each representing a unit of work. This architecture allows React to pause, abort, or prioritize rendering work to prevent blocking the main thread. 
The **render phase** is when React calls your components to determine what changed (creating a work-in-progress tree). It is pure, asynchronous, and interruptible. The **commit phase** is when React applies those calculated changes to the DOM and runs effects. It is synchronous and cannot be interrupted.

**2. What is automatic batching in React 18? How did it work before React 18?**
Automatic batching means React groups multiple state updates into a single re-render for better performance. Before React 18, React only batched updates inside React event handlers (like onClick). Updates inside Promises, setTimeout, or native event handlers caused separate re-renders. React 18 automatically batches all state updates regardless of where they originate.

**3. What is a stale closure in React hooks? Give an example with `useEffect` and how to fix it.**
A stale closure occurs when a callback or effect captures a variable from a previous render and doesn't get updated when the variable changes.
```typescript
// Stale closure example:
useEffect(() => {
  const id = setInterval(() => {
    setCount(count + 1); // count is stuck at initial value!
  }, 1000);
  return () => clearInterval(id);
}, []); // Empty array causes closure to capture initial 'count' forever.

// Fix: Use functional state update, or add 'count' to deps.
setCount(prev => prev + 1);
```

**4. When would you use `useReducer` over `useState`? Give a concrete example.**
`useReducer` is preferred when state consists of multiple sub-values that change together, or when the next state depends heavily on the previous state via complex logic.
Example: A data fetching component that tracks `data`, `loading`, and `error`. Instead of three `useState` calls and complex sequential updates, a single `useReducer` handles actions like `FETCH_START`, `FETCH_SUCCESS`, and `FETCH_ERROR`, ensuring state consistency.

**5. What is the difference between `useEffect` and `useLayoutEffect`? When would you use the latter?**
`useEffect` runs asynchronously *after* the browser paints. `useLayoutEffect` runs synchronously *before* the browser paints, right after DOM mutations. You use `useLayoutEffect` only when you need to read DOM measurements (like scrolling position or element width) and synchronously mutate the DOM or state again to prevent a visual flicker.

**6. Why does React 18 Strict Mode double-invoke effects in development? What issue does this expose?**
Strict Mode forces components to mount, unmount, and remount in development. This is to expose memory leaks and incomplete cleanup functions in `useEffect`. If an effect sets up a subscription or interval and fails to clean it up, the double-invocation will make the bug obvious (e.g., two intervals running at once) so the developer can fix it before production.

**7. Explain the Virtual DOM and reconciliation. What role do `key` props play?**
The Virtual DOM is a lightweight JavaScript object representation of the real DOM. When state changes, React creates a new VDOM tree and compares it to the previous one (reconciliation). It finds the differences and updates only the changed parts of the real DOM. `key` props help React identify which items in a list have changed, been added, or been removed, preventing unnecessary re-renders and maintaining component state accurately across renders.

**8. What is the performance problem with React Context and how do you mitigate it?**
When a Context Provider's value changes, *every* component consuming that context (via `useContext`) will re-render, regardless of whether they needed the specific changed property. To mitigate this, split context into smaller, logically separated contexts (e.g., `ThemeContext`, `AuthContext`), or use external state managers (Zustand, Redux) that support selector-based subscriptions for fine-grained reactivity.

**9. When should you use `useCallback` and `useMemo`? When are they harmful?**
Use them when passing props to deeply nested children wrapped in `React.memo` to prevent referential inequality from triggering re-renders, or when performing highly expensive calculations (like sorting large arrays). They are harmful when used everywhere prematurely because the hooks themselves have overhead: React has to allocate memory for the memoized values and run dependency array comparisons on every render, which is often slower than just re-creating the function or value.

**10. Explain the difference between controlled and uncontrolled components. When would you use each?**
Controlled components have their form data (value) managed by React state. They provide a single source of truth and are best for instant validation, disabling buttons based on input, or enforcing formats. Uncontrolled components let the DOM manage the data, and React reads it via `ref`s. They are useful for simple forms where you only need the value on submit, for file inputs (which must be uncontrolled), or when integrating with non-React libraries.

**11. What is `useTransition` and how does it help with user experience?**
`useTransition` allows you to mark a state update as a "transition" (non-urgent). If a user interaction triggers a heavy UI update (like filtering a large list), wrapping that state update in `startTransition` tells React to keep the UI responsive. It renders the heavy update in the background and can interrupt it if the user interacts again (e.g., typing more letters), preventing the page from freezing.

**12. What happens to a `useEffect` cleanup function? When exactly does it run?**
The cleanup function (the function returned from `useEffect`) runs right before the effect is executed again on the next render (with the old values from the previous render), and it runs one final time when the component unmounts. This guarantees that resources like event listeners or timeouts are properly disposed of before new ones are created.

**13. What is React Suspense and how does it work?**
Suspense is a mechanism that lets a component "suspend" rendering while it waits for an asynchronous operation (like lazy-loading code via `React.lazy` or fetching data). React will walk up the tree to find the nearest `<Suspense>` boundary and display its `fallback` UI (like a spinner) until the suspended component is ready to render.

**14. Why is using the `React.FC` type for function components generally discouraged in TypeScript?**
Historically, `React.FC` implicitly injected the `children` prop into the component's types, even if the component wasn't designed to accept children. This bypassed TypeScript's checks. Furthermore, `React.FC` cannot be used with generic components (components that accept type arguments). It's better to explicitly type the props interface, including `children` if needed.

**15. Explain component composition vs inheritance in React. What is the children prop pattern?**
React strongly favors composition over inheritance. Instead of creating a `SpecialButton` class that extends a `BaseButton` class, you create components that use other components. The `children` prop is a core composition pattern. A `<Card>` component can accept `children` to render whatever arbitrary content is passed between its opening and closing tags, decoupling the layout logic from the content logic.
