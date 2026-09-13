# Module 3: React Fundamentals

Welcome to the deep dive into React fundamentals. This module is designed for engineers who want to understand not just how to use React, but how React works under the hood. 

## React's Core Mental Model

### React as a UI = f(state) function

At its core, React embraces a declarative programming paradigm. Instead of manually manipulating the DOM (imperative), you describe what the UI should look like for a given state, and React handles the DOM updates to match that description.

```typescript
// Imperative (Vanilla JS)
const button = document.createElement('button');
button.innerText = 'Click me';
button.className = 'btn-primary';
if (user.isLoggedIn) {
  button.style.display = 'block';
} else {
  button.style.display = 'none';
}
document.body.appendChild(button);

// Declarative (React)
const Button = ({ isLoggedIn }: { isLoggedIn: boolean }) => (
  isLoggedIn ? <button className="btn-primary">Click me</button> : null
);
```

This mathematical model `UI = f(state)` means that your component is a pure function with respect to its render output. When state changes, the function is conceptually re-run to produce a new UI description.

### Virtual DOM

The Virtual DOM (VDOM) is a lightweight JavaScript representation of the actual DOM. It's a tree of plain JavaScript objects. 

When a component's state changes:
1. React creates a new Virtual DOM tree.
2. React compares (diffs) this new tree with the previous Virtual DOM tree. This process is called **Reconciliation**.
3. React calculates the minimum set of DOM mutations needed to update the real DOM.
4. React applies these mutations synchronously in the **Commit phase**.

### Reconciliation Algorithm

The reconciliation algorithm is optimized with two heuristics (O(n) complexity instead of O(n^3)):
1. Two elements of different types will produce different trees. React will tear down the old tree and build the new one from scratch.
2. The developer can hint at which child elements may be stable across different renders with a `key` prop.

### React Fiber Architecture

Introduced in React 16, Fiber is a complete rewrite of React's core algorithm. 

Before Fiber, React used a recursive stack-based reconciliation process. If a component tree was deep, React could block the main thread for too long, causing dropped frames (jank).

**Fiber:**
- A "fiber" is a JavaScript object that contains information about a component, its input, and its output.
- It represents a **unit of work**.
- The fiber tree is a linked list structure (child, sibling, return/parent pointers). This allows React to pause, abort, or resume work.
- React maintains two trees: the **current tree** (what is on screen) and the **work-in-progress tree** (what is being rendered in memory).

### Render Phase vs Commit Phase

**Render Phase (Asynchronous/Interruptible):**
- React traverses the fiber tree and calls component functions to figure out what changed.
- This phase is **pure** and **interruptible**. React can pause rendering to handle higher-priority tasks (like user input).
- Side effects (DOM mutations, network requests) must NOT occur here.

**Commit Phase (Synchronous/Uninterruptible):**
- React applies the calculated changes to the actual DOM.
- It runs `useEffect` and `useLayoutEffect` hooks.
- This phase cannot be interrupted.

## JSX

JSX is a syntax extension for JavaScript. It looks like HTML, but it compiles down to plain JavaScript function calls.

```typescript
// JSX
const element = <h1 className="title">Hello</h1>;

// Compiled JS (React 17+ JSX Transform)
import { jsx as _jsx } from "react/jsx-runtime";
const element = _jsx("h1", { className: "title", children: "Hello" });

// Legacy compilation
const element = React.createElement("h1", { className: "title" }, "Hello");
```

A React Element is just a plain JavaScript object describing the UI node:
```javascript
{
  type: 'h1',
  props: {
    className: 'title',
    children: 'Hello'
  },
  key: null,
  ref: null,
  // ... internal React fields
}
```

### Why Keys Matter in Lists

Keys are crucial for reconciliation when mapping over arrays. The key serves as a unique identifier for an element across renders.

```typescript
// BAD: using index as key
{items.map((item, index) => (
  <ListItem key={index} item={item} />
))}

// GOOD: using unique stable ID
{items.map(item => (
  <ListItem key={item.id} item={item} />
))}
```

If you use the index as a key and then reorder the list, React gets confused. It might reuse the wrong DOM nodes and component state, leading to subtle bugs, especially with input fields or uncontrolled components.

### Fragments

Fragments (`<>...</>` or `<React.Fragment>`) let you group a list of children without adding extra nodes to the DOM.

```typescript
const Columns = () => (
  <>
    <td>Column 1</td>
    <td>Column 2</td>
  </>
);
```

## Component Design

### Function Components vs Class Components

Historically, class components were required for state and lifecycle methods. Function components were "stateless" or "dumb".
Since React 16.8 (Hooks), function components can do everything classes can (and more elegantly), except for Error Boundaries. We write function components exclusively today.

### Props and One-Way Data Flow

Props are read-only (immutable). A component must never modify its own props.
React enforces a unidirectional data flow. Data flows down from parent to child via props. Events flow up from child to parent via callbacks.

**Prop Drilling:**
Passing props through many intermediate components that don't need them just to reach a deeply nested child.

### The Children Prop

`children` is a special prop used to pass elements into a component.

In TypeScript, typing children correctly is important:
- `React.ReactNode`: The most broad type. Anything that can be rendered (elements, strings, numbers, arrays, null, undefined). Preferred for `children`.
- `React.ReactElement`: Specifically a JSX element object (created via `React.createElement`).
- `React.FC` (Function Component): Historically used to type components. It implicitly included `children: ReactNode`. It is now **discouraged** because it makes `children` implicit (even if the component doesn't accept children) and breaks generic components.

```typescript
// Preferred way to type components
type CardProps = {
  title: string;
  children: React.ReactNode;
};

const Card = ({ title, children }: CardProps) => (
  <div className="card">
    <h2>{title}</h2>
    <div>{children}</div>
  </div>
);
```

### Component Composition

Prefer composition over inheritance. React components don't use class inheritance to share UI logic. Instead, they compose by passing components as props or children.

## All Core Hooks — Deep Dive

Hooks allow function components to "hook into" React state and lifecycle features.

### `useState`

State is a snapshot. When React calls your component, it provides the state snapshot for that specific render. State variables don't change during a render.

```typescript
const [count, setCount] = useState(0);

const handleIncrement = () => {
  setCount(count + 1);
  setCount(count + 1);
  setCount(count + 1);
  // count is still 0 during this render! The next render will only receive count = 1.
};
```

**Functional Updates:**
To fix the above issue or to avoid stale closures, pass a function to the setter:
```typescript
const handleIncrement = () => {
  setCount(prev => prev + 1);
  setCount(prev => prev + 1);
  setCount(prev => prev + 1);
  // Next render receives count = 3
};
```

**Automatic Batching (React 18):**
React 18 batches multiple state updates into a single re-render, even if they happen inside promises, setTimeout, or native event handlers.

**Lazy Initialization:**
If the initial state requires expensive computation, pass a function. It will only run on the initial render.
```typescript
const [data, setData] = useState(() => expensiveComputation());
```

### `useEffect`

`useEffect` lets you synchronize a component with an external system (network, DOM events, third-party libraries).

**Timing:** It runs asynchronously AFTER the browser has painted the screen. It does not block painting.

**Dependency Array:**
- `[]`: Runs once on mount, cleanup on unmount.
- `[dep1, dep2]`: Runs on mount and whenever deps change.
- No array: Runs after EVERY render (usually a mistake).

**Cleanup Function:**
Returned from the effect. It runs before the effect runs again, and on unmount.
```typescript
useEffect(() => {
  const socket = new WebSocket(url);
  
  return () => {
    socket.close(); // Cleanup
  };
}, [url]);
```

**Stale Closures in Effects:**
If you forget to include a variable in the dependency array, the effect will "capture" the value from the initial render and become stale.
The `eslint-plugin-react-hooks` exhaustive-deps rule catches this.

**Effects are NOT for Derived State:**
Do not use `useEffect` to update state based on other state. Calculate it directly during rendering or use `useMemo`.

**React 18 Strict Mode Double-Invocation:**
In development, React 18 Strict Mode mounts, unmounts, and remounts components to stress-test your effects and ensure you have proper cleanup functions.

### `useLayoutEffect`

Identical signature to `useEffect`, but it fires **synchronously** after all DOM mutations but BEFORE the browser has a chance to paint.

**When to use:** Only when you need to read layout from the DOM (e.g., `element.getBoundingClientRect()`) and synchronously re-render to avoid flickering (e.g., positioning a tooltip).

### `useRef`

A mutable container that persists for the full lifetime of the component. Changing the `.current` property does NOT trigger a re-render.

**Common Uses:**
1. **DOM Access:**
```typescript
const inputRef = useRef<HTMLInputElement>(null);
const focusInput = () => inputRef.current?.focus();
return <input ref={inputRef} />;
```

2. **Mutable Instance Variables:** Storing interval IDs or previous state.
```typescript
const timerId = useRef<NodeJS.Timeout | null>(null);

const start = () => {
  timerId.current = setInterval(() => console.log('tick'), 1000);
};
```

### `useCallback` and `useMemo`

These are for performance optimization.

**`useCallback`:** Memoizes a function instance between renders.
**`useMemo`:** Memoizes a computed value between renders.

```typescript
// Memoize function to prevent unnecessary re-renders of child components
const handleClick = useCallback(() => {
  console.log('clicked', id);
}, [id]);

// Memoize expensive calculation
const sortedData = useMemo(() => expensiveSort(data), [data]);
```

**When NOT to use:**
Do not wrap everything in `useMemo`/`useCallback`. Creating the hooks and checking dependencies has a performance cost. Only use them when passing props to `React.memo` components, or for genuinely expensive calculations.

### `useContext`

Context provides a way to pass data through the component tree without having to pass props down manually at every level.

```typescript
const ThemeContext = createContext<'light' | 'dark'>('light');

const App = () => (
  <ThemeContext.Provider value="dark">
    <Child />
  </ThemeContext.Provider>
);

const Child = () => {
  const theme = useContext(ThemeContext);
  return <div>{theme}</div>; // 'dark'
};
```

**Performance Problem:** Every component that calls `useContext` will unconditionally re-render when the provider value changes, even if it only uses a small slice of that value.

### `useReducer`

An alternative to `useState` for complex state logic that involves multiple sub-values or when the next state depends on the previous one. It uses the `(state, action) => newState` pattern.

```typescript
type State = { count: number };
type Action = { type: 'increment' } | { type: 'decrement' };

const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case 'increment': return { count: state.count + 1 };
    case 'decrement': return { count: state.count - 1 };
    default: return state;
  }
};

const [state, dispatch] = useReducer(reducer, { count: 0 });
```

## Controlled vs Uncontrolled Components

### Controlled Components
Form data is handled by the React component's state. You must provide `value` and `onChange`.
```typescript
const [value, setValue] = useState('');
<input value={value} onChange={e => setValue(e.target.value)} />
```

### Uncontrolled Components
Form data is handled by the DOM itself. You read it using a `ref`. Use `defaultValue` for initial state.
```typescript
const inputRef = useRef<HTMLInputElement>(null);
const handleSubmit = () => console.log(inputRef.current?.value);
<input ref={inputRef} defaultValue="Hello" />
```

## React 18 Concurrent Features

These features allow React to prepare multiple versions of the UI at the same time.

### `useTransition` and `startTransition`
Mark state updates as "non-urgent" (transitions). This keeps the UI responsive during heavy renders. If the user types while a transition is rendering, React interrupts the transition.

```typescript
const [isPending, startTransition] = useTransition();
const [query, setQuery] = useState('');

const handleChange = (e) => {
  // Urgent update
  setQuery(e.target.value);
  startTransition(() => {
    // Non-urgent update (heavy filtering)
    setFilteredResults(filterData(e.target.value));
  });
};
```

### `useDeferredValue`
Pass a value into this hook to get a deferred version of it. It lags behind the original value if the main thread is busy.

```typescript
const query = useSearchQuery();
const deferredQuery = useDeferredValue(query);
// Render heavy list using deferredQuery
```

### Suspense
Declaratively specify a loading state for a part of the component tree if it's not ready to render yet (due to lazy loading code or data).

```typescript
<Suspense fallback={<Spinner />}>
  <HeavyComponent />
</Suspense>
```

## Error Boundaries

Error boundaries are React components that catch JavaScript errors anywhere in their child component tree, log those errors, and display a fallback UI instead of crashing the whole component tree.

**Currently, error boundaries MUST be class components.** There is no Hooks equivalent yet.

```typescript
class ErrorBoundary extends React.Component {
  state = { hasError: false };

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    logErrorToService(error, errorInfo);
  }

  render() {
    if (this.state.hasError) return <h1>Something went wrong.</h1>;
    return this.props.children;
  }
}
```

Use granular error boundaries around specific sections of your app so one small widget crashing doesn't take down the entire page.

---
*End of Module 3 Fundamentals.*
