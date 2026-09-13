# React Advanced Concepts

## 1. React Performance: How Re-renders Work

A component re-renders when one of the following events occurs in the React application lifecycle:
- Its internal state changes via a state setter function (like `setState` or the setter from `useState`).
- Its parent component re-renders. This is true even if the component receives the exact same props as before, because React, by default, will traverse down the tree and re-render all children when a parent re-renders.
- Its context value changes. If a component consumes a context using `useContext` or a Context.Consumer, any change to the context provider's value will trigger a re-render of that component.

What exactly happens during a re-render process?
React calls the function component to get a new React element tree representing the UI. This element tree is a lightweight JavaScript object representation of the desired DOM. React then diffs this new element tree with the existing fiber tree, a process known as reconciliation. During reconciliation, React calculates the exact differences between the old and new trees. Finally, React enters the commit phase, where it applies only the actual changes to the real DOM, minimizing expensive DOM operations.

Why re-renders are NOT always bad:
Most re-renders in React are incredibly fast because they only involve JavaScript object creation and comparison, without necessarily touching the actual DOM unless there are differences. You should only attempt to optimize re-renders when you have actual performance issues and profiling shows that a specific component is causing a bottleneck. Premature optimization can lead to overly complex code that is difficult to maintain.

`React.memo(Component)`:
You can wrap a component in `React.memo` to create a memoized version of that component. When a parent re-renders, React will skip re-rendering the memoized child component if its props are shallowly equal to the previous props.

Shallow equality explained:
Shallow equality compares object and array references, not their deep values. If you pass a new array or object literal, or an inline function as a prop, it will always fail the shallow equality check because a new reference is created on every render of the parent component.

When `React.memo` does NOT help:
If the props passed to a memoized component include new object or function references on every render, the memoization has absolutely no effect. The shallow equality check will fail, and the component will re-render anyway.

Solution for reference stability:
You must use `useMemo` to stabilize object and array references, and `useCallback` to stabilize function references before passing them as props to a memoized component.

`useCallback(fn, deps)`:
This hook returns a memoized version of the callback function that only changes if one of the dependencies has changed. This is extremely useful when passing callbacks to optimized child components that rely on reference equality to prevent unnecessary renders.

```tsx
import React, { useState, useCallback } from 'react';

const Child = React.memo(({ onClick }: { onClick: () => void }) => {
  console.log("Child render");
  return <button onClick={onClick}>Click Me</button>;
});

export function ParentComponent() {
  const [count, setCount] = useState(0);

  // This function reference remains stable across renders
  // unless dependencies change (none in this case).
  const handleClick = useCallback(() => {
    console.log("Button clicked");
  }, []);

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(c => c + 1)}>Increment</button>
      <Child onClick={handleClick} />
    </div>
  );
}
```

`useMemo(fn, deps)`:
This hook returns a memoized computed value. It will only recalculate the value when one of the dependencies has changed. This optimization helps to avoid expensive calculations on every render, such as sorting an array of 10,000 items or complex data filtering.

The cost of memoization:
It is important to remember that every `useMemo` and `useCallback` hook runs a comparison on every single render. This comparison itself is not free. You should always use the React Profiler to justify adding memoization, ensuring that the cost of comparison is lower than the cost of re-rendering.

React DevTools Profiler:
The Profiler is an essential tool for identifying performance bottlenecks. You can record a session, view the flame chart to see the component tree and render times, use the ranked chart to find the slowest components, and identify components that are re-rendering too frequently.

`React.memo` with custom comparator:
You can provide a custom comparison function as the second argument to `React.memo`. This function receives the previous props and next props, allowing you to define exactly when a component should update.

```tsx
import React from 'react';

interface Props {
  data: { id: string; value: string };
  onSelect: (id: string) => void;
}

const ItemComponent = React.memo((props: Props) => {
  return <div onClick={() => props.onSelect(props.data.id)}>{props.data.value}</div>;
}, (prevProps, nextProps) => {
  // Custom deep comparison logic here
  return prevProps.data.id === nextProps.data.id && prevProps.data.value === nextProps.data.value;
});
```

Code splitting with `React.lazy` and `Suspense`:
You can implement code splitting using `React.lazy(() => import('./Component'))` combined with `<Suspense fallback={...}>`. Dynamic imports create separate JavaScript chunks that are only loaded on demand when the component is first rendered, significantly reducing the initial bundle size.

`React.lazy` limitations:
It currently only supports default exports. It also only works at the component level, meaning you cannot use it inside conditional statements or loops.

Route-based code splitting with React Router:
A common and highly effective pattern is to wrap each route's main component in `React.lazy` and a `Suspense` boundary. This ensures that users only download the code necessary for the route they are visiting.

## 2. State Management — Choosing the Right Tool

**Understanding the state categories:**

Local UI state:
This is state that only a specific component or a small localized section of the UI cares about. Examples include form input values, whether a modal is currently open or closed, or the visibility of a tooltip. The best tools for this are the standard React hooks: `useState` or `useReducer`.

Shared client state:
This is state that needs to be accessed by multiple disparate components across the application, but is not persisted on a server. Examples include user UI preferences, the current application theme, or the authenticated user's session data. Suitable tools include React Context, Zustand, or Redux.

Server state:
This is data that is fetched from an external API or database. It comes with unique challenges, such as handling loading states, error states, cache invalidation, and background synchronization. The recommended tools for managing server state are React Query (TanStack Query) or SWR.

**Lifting State Up:**
When two sibling components need to share the same state, the standard React pattern is to lift that state up to their closest common ancestor. The parent component then passes the state and the state updater function down as props to the children.

Prop drilling:
When you have deeply nested component trees, passing state down through many intermediate layers of components that do not actually use the state is called prop drilling. This is a strong signal that it might be time to introduce Context or an external state management library.

**React Context for state:**
Context is excellent for infrequently changing values that need to be globally accessible, such as the application theme, locale, current user information, or authentication status.

However, Context is generally bad for frequently changing values, like every single keystroke in an input field or real-time data streams. This is because every component that consumes the context will re-render whenever any part of the context value changes, potentially causing massive performance issues.

Context splitting:
To mitigate the re-render issue, you should practice context splitting. Instead of having one massive `GlobalContext`, create separate contexts like `ThemeContext`, `UserContext`, and `CartContext`. This isolates updates and minimizes unnecessary re-renders.

Optimizing context:
Always use `useMemo` to memoize the context value object provided to the Context.Provider. This prevents a new object reference from being created on every render of the provider component, which would otherwise force all consumers to re-render.

```tsx
import React, { createContext, useMemo, useState } from 'react';

interface User {
  id: string;
  name: string;
}

interface AuthContextType {
  user: User | null;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  const logout = useCallback(() => {
    setUser(null);
  }, []);

  const value = useMemo(() => ({ user, logout }), [user, logout]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
```

**Zustand:**
Zustand allows you to create a global store using a custom hook. It does not require wrapping your application in a Provider component, making it very straightforward to adopt.

Selector subscriptions:
Components subscribe to specific parts of the store using selectors. A component will only re-render when the specific slice of state it selected changes.

```ts
import { create } from 'zustand';

interface StoreState {
  count: number;
  increment: () => void;
}

const useStore = create<StoreState>((set) => ({
  count: 0,
  increment: () => set((state) => ({ count: state.count + 1 })),
}));

// In a component:
// This component only re-renders when `count` changes.
const count = useStore(state => state.count);
```

Actions are co-located with state inside the store definition, keeping related logic together. Zustand also supports Devtools middleware and persist middleware for saving state to localStorage. Async actions are completely straightforward — they are just regular async functions defined within the store.

When to use Zustand:
It is ideal for medium-complexity applications where you want to avoid the extensive boilerplate of Redux, but still need robust global state management without the drawbacks of Provider nesting.

**Redux Toolkit (RTK):**
`createSlice` generates action creators and the reducer automatically based on the provided `name`, `initialState`, and `reducers` object.

RTK uses Immer under the hood. This means you can write logic inside your reducers that appears to be mutating the state directly. Immer safely intercepts these mutations and converts them into proper immutable updates.

`createAsyncThunk` provides a standardized way to handle the lifecycle of asynchronous actions, automatically dispatching pending, fulfilled, and rejected actions.

You use `extraReducers` with the `builder.addCase()` syntax to handle the lifecycle actions generated by thunks or other slices within a specific slice.

RTK Query is a powerful data fetching and caching tool built into Redux Toolkit. You use `createApi` to define endpoints, and it automatically generates React hooks for you, such as `useGetUserQuery` and `useUpdateUserMutation`.

Normalized state management is simplified with `createEntityAdapter`, which provides pre-built CRUD operations for collections and automatic selectors like `selectAll` and `selectById`.

When to use Redux:
Redux is suited for large teams that require strict architectural patterns, applications with highly complex state interactions, scenarios where time-travel debugging is crucial, or when you are using RTK Query as an alternative to React Query.

**React Query (TanStack Query):**
The core insight behind React Query is that server state has fundamentally different requirements than client UI state. Server state requires background refetching, sophisticated cache invalidation, and synchronization with the remote source.

You wrap your application with `QueryClientProvider` and provide a `QueryClient` instance.

The `useQuery` hook handles data fetching. It provides automatic caching, background refetching, and implements the stale-while-revalidate pattern.

```ts
import { useQuery } from '@tanstack/react-query';

function fetchUser(id: string) {
  return fetch(`/api/users/${id}`).then(res => res.json());
}

function UserProfile({ userId }: { userId: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['user', userId],
    queryFn: () => fetchUser(userId)
  });

  if (isLoading) return <div>Loading...</div>;
  if (isError) return <div>Error loading user.</div>;
  return <div>{data.name}</div>;
}
```

Query keys act as the cache key and must uniquely identify the data being fetched. You must include all variables used inside the `queryFn` within the query key array.

`staleTime` determines how long data is considered fresh. During this window, no background refetching will occur. The default is 0.

`gcTime` (formerly known as `cacheTime`) determines how long cached data remains in memory after the last component subscribing to it unmounts. The default is 5 minutes.

The `useMutation` hook is used for operations that modify data (POST, PUT, DELETE). It provides callbacks like `onSuccess`, `onError`, and `onSettled`.

Cache invalidation is typically performed after a successful mutation using `queryClient.invalidateQueries({ queryKey: ['users'] })`, which forces a refetch of the affected data.

Optimistic updates provide immediate UI feedback by updating the cache before the server responds, using the `onMutate` callback, and rolling back if the request fails in `onError`.

```ts
import { useMutation, useQueryClient } from '@tanstack/react-query';

// Inside a component
const queryClient = useQueryClient();

const mutation = useMutation({
  mutationFn: createTodo,
  onMutate: async (newTodo) => {
    // Cancel any outgoing refetches
    await queryClient.cancelQueries({ queryKey: ['todos'] });
    // Snapshot the previous value
    const previous = queryClient.getQueryData(['todos']);
    // Optimistically update to the new value
    queryClient.setQueryData(['todos'], (old: any) => [...old, newTodo]);
    // Return a context object with the snapshotted value
    return { previous };
  },
  onError: (err, newTodo, context) => {
    // Rollback to the previous value if mutation fails
    queryClient.setQueryData(['todos'], context?.previous);
  },
});
```

Prefetching can be done manually using `queryClient.prefetchQuery()`, which is excellent for hover-to-prefetch patterns to improve perceived performance.

`useInfiniteQuery` is specifically designed for handling pagination with cursors, providing methods like `fetchNextPage` and `hasNextPage`.

## 3. Advanced Component Patterns

**Custom Hooks:**
Custom hooks are the primary mechanism for extracting stateful logic so that it can be reused across multiple components, keeping your components clean and focused on presentation.

The rules of hooks must be strictly followed: they can only be called at the top level of your React functions (not inside loops, conditions, or nested functions), and they can only be called inside React function components or other custom hooks.

By convention, custom hook names must always start with the prefix `use`.

Common examples of custom hooks include `useLocalStorage`, `useDebounce`, `useOnClickOutside`, `usePrevious`, and `useMediaQuery`.

Full implementation of a strongly-typed `useDebounce` hook:
```ts
import { useState, useEffect } from 'react';

function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}
```

**Compound Component Pattern:**
This pattern involves grouping several related components together that share implicit state, typically facilitated through React Context.

A classic example is a custom Select component consisting of `<Select>`, `<Select.Trigger>`, `<Select.Options>`, and `<Select.Option>`.

The parent component (`<Select>`) manages the shared state (like whether the dropdown is open and the currently selected value), while the child components consume this state via Context. This results in a very clean, declarative API without the need for excessive prop drilling.

Full TypeScript implementation of a Compound Component:
```tsx
import React, { createContext, useContext, useState, ReactNode } from 'react';

interface SelectContextType {
  isOpen: boolean;
  setIsOpen: (isOpen: boolean) => void;
  selectedValue: string;
  setSelectedValue: (value: string) => void;
}

const SelectContext = createContext<SelectContextType | undefined>(undefined);

function useSelectContext() {
  const context = useContext(SelectContext);
  if (!context) {
    throw new Error('Select components must be used within a Select provider');
  }
  return context;
}

export function Select({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedValue, setSelectedValue] = useState('');

  return (
    <SelectContext.Provider value={{ isOpen, setIsOpen, selectedValue, setSelectedValue }}>
      <div className="select-container">{children}</div>
    </SelectContext.Provider>
  );
}

Select.Trigger = function SelectTrigger({ children }: { children: ReactNode }) {
  const { isOpen, setIsOpen, selectedValue } = useSelectContext();
  return (
    <button onClick={() => setIsOpen(!isOpen)}>
      {selectedValue || children}
    </button>
  );
};

Select.Options = function SelectOptions({ children }: { children: ReactNode }) {
  const { isOpen } = useSelectContext();
  if (!isOpen) return null;
  return <div className="options-container">{children}</div>;
};

Select.Option = function SelectOption({ value, children }: { value: string, children: ReactNode }) {
  const { setSelectedValue, setIsOpen } = useSelectContext();
  return (
    <div onClick={() => { setSelectedValue(value); setIsOpen(false); }}>
      {children}
    </div>
  );
};
```

**Render Props Pattern (Historical Context):**
This pattern involves passing a function as a prop to a component. This function returns JSX, and the component calls it with specific data.

Before the introduction of hooks, render props were a primary method for achieving code and logic reuse.

While largely replaced by custom hooks in modern React, render props are still occasionally useful, particularly for highly flexible component libraries where the consumer needs absolute control over the rendered output based on internal component state.

**Higher-Order Components (HOC):**
An HOC is a function that takes a component as an argument and returns a new component with augmented or modified behavior.

TypeScript generic typing for HOCs ensures that props are correctly passed through:
```ts
import React from 'react';
import { Navigate } from 'react-router-dom';

// Assume useAuth is defined elsewhere
const useAuth = () => ({ user: { name: 'Admin' } }); 

function withAuth<P extends object>(Component: React.ComponentType<P>) {
  return function AuthenticatedComponent(props: P) {
    const { user } = useAuth();
    
    if (!user) {
      return <Navigate to="/login" replace />;
    }
    
    return <Component {...props} />;
  };
}
```

When naming HOCs, the convention is to prefix the returned component with `with`. You should also set the `displayName` property on the returned component to aid in debugging with React DevTools.

Common pitfalls of HOCs include prop naming collisions, the loss of static methods defined on the original component, and complexities surrounding ref forwarding.

**Headless Components:**
This architectural pattern advocates for completely separating the complex logic, state management, and accessibility concerns (the "headless" part) from the visual presentation and styling.

Libraries adopting this pattern include Headless UI (by the Tailwind team), Radix UI, and React Aria.

The pattern works by having the library provide the intricate behavior and robust accessibility implementations, while you, the developer, maintain complete control over the markup and styling of the component.

## 4. Testing React Components

The philosophy behind React Testing Library (RTL) is to test your components from the perspective of the end user, rather than testing the internal implementation details.

You should almost never test internal component state or private methods. If you find yourself needing to do this, it is often an indicator that your component's design might need improvement.

When selecting elements in your tests, you should follow this query priority order: `getByRole` > `getByLabelText` > `getByPlaceholderText` > `getByText` > `getByTestId`.

The `getByRole` query is the most robust because it uses ARIA roles, ensuring you are testing the accessible name and role of the element, which promotes accessibility-correct markup.

Understanding query variants:
- `getBy*`: These queries will throw an error immediately if the element is not found or if multiple elements are found. Use them for elements that you expect must exist in the document.
- `queryBy*`: These queries return null if the element is not found. They are essential for asserting the absence of an element (e.g., `expect(queryByText('Error')).not.toBeInTheDocument()`).
- `findBy*`: These queries return a Promise and will wait for the element to appear in the DOM, up to a default timeout. Use these for testing asynchronous rendering and data fetching.

`userEvent` vs `fireEvent`:
`userEvent` is designed to simulate realistic user interactions, firing all the expected underlying DOM events (like keydown, keypress, keyup, focus, blur) in the correct sequence. You should always prefer `userEvent` over `fireEvent` for writing robust and realistic tests.

The `waitFor(callback)` function allows you to retry a callback containing assertions until it stops throwing an error or a timeout is reached, which is useful for complex asynchronous assertions.

Mocking functions is typically done using `vi.fn()` if you are using Vitest, or `jest.fn()` if you are using Jest.

Mock Service Worker (MSW) is the recommended way to mock network requests. It intercepts actual HTTP requests at the service worker level, providing a highly realistic environment for API mocking without the need to mock the global `fetch` API.

```ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/user', () => {
    return HttpResponse.json({ name: 'Alice', id: '1' });
  })
];
```

Testing custom hooks in isolation without needing to create dummy components can be done using the `renderHook()` utility provided by RTL.

The `act()` function is used to wrap state updates in your tests, ensuring that React can process them in batches and flush them to the DOM before your assertions run. Fortunately, RTL handles this automatically for most operations.

## 5. React Router v6 — Data APIs

The modern routing approach utilizes `createBrowserRouter` and the `<RouterProvider>` component, which leverage the new Data APIs and the underlying Web History API.

Nested routing allows child routes to render their content inside a parent route's `<Outlet />` component, enabling complex layout structures.

Layout routes are special routes that do not have a specific `path` defined. Instead, they provide a layout component that wraps all of their child routes.

The route `loader` function is a critical new feature. It executes BEFORE the route component renders, allowing you to fetch data required for that route seamlessly.

Inside the component, you receive the fetched data synchronously using the `useLoaderData()` hook. This completely eliminates the need to manage loading states inside the component itself.

If an error is thrown inside a loader function, React Router will automatically catch it and render the route's defined `errorElement` instead of the normal component.

When you have nested routes, multiple loaders will execute in parallel, optimizing data fetching times.

The route `action` function is designed to handle form submissions and mutations (POST, PUT, DELETE). It is triggered when a user submits a `<Form method="post">` component provided by React Router.

The `useFetcher()` hook is incredibly useful for submitting data or loading data in the background without causing a navigation event. This is ideal for non-navigation mutations, such as clicking a "like" button or adding an item to a cart from a list view.

Essential hooks include `useNavigate()` for programmatic navigation, `useParams()` for accessing URL parameters, `useSearchParams()` for interacting with query strings, and `useLocation()` for getting the current URL location object.

A standard pattern for implementing protected routes involves creating a wrapper component that checks authentication status:

```tsx
import { Navigate } from 'react-router-dom';
import { ReactNode } from 'react';

function ProtectedRoute({ children }: { children: ReactNode }) {
  // Assume useAuth is a custom hook providing auth state
  const { user, isLoading } = useAuth();
  
  if (isLoading) return <div>Checking auth...</div>;
  if (!user) return <Navigate to="/login" replace />;
  
  return <>{children}</>;
}
```

## 6. Forms with React Hook Form + Zod

The primary hook is `useForm<T>()`, which returns a powerful object containing methods like `register`, `handleSubmit`, `formState`, `watch`, `setValue`, and `reset`.

You use the `register('fieldName', validationRules)` method to connect standard HTML inputs to the form instance. This approach means your inputs do not require controlled state variables (they remain uncontrolled by default), which vastly improves performance on large forms.

The `handleSubmit(onValid, onInvalid)` method automatically prevents default form submission, validates the inputs, and then calls the appropriate callback function based on the validation result.

The `formState.errors` object contains all validation errors, fully typed to match your form's schema structure.

For integrating controlled components (like custom input components, rich text editors, or complex UI library inputs like React Select), you use the `<Controller>` component provided by the library.

Zod integration is seamless and highly recommended. You use the `zodResolver` to connect a Zod schema to your form validation.

```ts
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  email: z.string().email('Invalid email address format'),
  age: z.number().min(18, 'You must be at least 18 years old')
});

type FormValues = z.infer<typeof schema>;

function MyForm() {
  const { register, handleSubmit, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema)
  });

  const onSubmit = (data: FormValues) => console.log(data);

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('email')} placeholder="Email" />
      {errors.email && <span>{errors.email.message}</span>}
      
      <input type="number" {...register('age', { valueAsNumber: true })} placeholder="Age" />
      {errors.age && <span>{errors.age.message}</span>}
      
      <button type="submit">Submit</button>
    </form>
  );
}
```

Handling dynamic lists of inputs (like adding multiple addresses or tags) is done efficiently using the `useFieldArray` hook.

The `watch('fieldName')` function allows you to observe the current value of an input. Importantly, calling `watch` will trigger a re-render whenever that specific value changes. If you need to read a value without causing a re-render (e.g., inside an event handler), you should use the `getValues()` method instead.
