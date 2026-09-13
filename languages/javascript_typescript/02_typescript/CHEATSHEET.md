# Module 2 Cheatsheet: TypeScript

## Utility Types Quick-Reference

| Utility Type | Description | Internal Implementation Pattern | Example |
|---|---|---|---|
| `Partial<T>` | Makes all properties optional | `{ [P in keyof T]?: T[P] }` | `Partial<User>` |
| `Required<T>` | Makes all properties required | `{ [P in keyof T]-?: T[P] }` | `Required<Config>` |
| `Readonly<T>` | Makes all properties readonly | `{ readonly [P in keyof T]: T[P] }` | `Readonly<State>` |
| `Record<K, V>` | Object with keys K, values V | `{ [P in K]: V }` | `Record<string, number>` |
| `Pick<T, K>` | Extracts a subset of keys | `{ [P in K]: T[P] }` | `Pick<User, "id" | "name">` |
| `Omit<T, K>` | Removes a subset of keys | `Pick<T, Exclude<keyof T, K>>` | `Omit<User, "password">` |
| `Exclude<T, U>` | Excludes union members | `T extends U ? never : T` | `Exclude<"a"|"b", "a">` -> `"b"` |
| `Extract<T, U>` | Keeps matching union members | `T extends U ? T : never` | `Extract<"a"|"b", "a">` -> `"a"` |
| `ReturnType<T>`| Returns function return type | `T extends (...args: any) => infer R ? R : any` | `ReturnType<typeof func>` |
| `Parameters<T>`| Returns function parameters | `T extends (...args: infer P) => any ? P : never` | `Parameters<typeof func>` |

## `any` vs `unknown` vs `never` vs `void`

| Type | Can be assigned TO... | Can accept assignment FROM... | Primary Use Case |
|---|---|---|---|
| `any` | Anything (dangerous!) | Anything | Migrating legacy code, rapid prototyping. |
| `unknown` | Only `unknown` or `any` | Anything | Type-safe JSON payloads. Must be narrowed before use. |
| `never` | Anything | Nothing (except `never`) | Unreachable code, exhaustive switch checks, throwing functions. |
| `void` | `any`, `unknown` | `undefined` | Return type of functions that only produce side-effects. |

## Generic Constraints Syntax Reference

Limit generic types using the `extends` keyword:

```typescript
// Must be an object with a numeric ID
function print<T extends { id: number }>(obj: T) {}

// Key must exist in object T
function getProp<T, K extends keyof T>(obj: T, key: K) {}
```

## `tsconfig.json` Key Options

- `strict`: Enables rigorous checking (`strictNullChecks`, `noImplicitAny`). Always use `true`.
- `target`: The JavaScript version outputted (e.g., `ES2022`).
- `module`: The module format outputted (e.g., `ESNext`, `NodeNext`).
- `moduleResolution`: How TS finds modules (`Bundler`, `NodeNext`).
- `skipLibCheck`: Skips type checking of declaration files (`.d.ts`). Set to `true` for performance.
- `isolatedModules`: Ensures files can be safely compiled independently. Required by Vite, SWC, esbuild.

## Type Narrowing Techniques

| Technique | Example | Use Case |
|---|---|---|
| `typeof` | `if (typeof val === "string")` | Primitives (string, number, boolean) |
| `instanceof` | `if (val instanceof Date)` | Classes and instantiated objects |
| `in` operator | `if ("role" in user)` | Checking for property existence |
| Type Predicate | `function isUser(x: any): x is User` | Custom complex validation logic |
| Discriminated Union | `if (action.type === "LOGIN")` | Working with Redux-style actions or API responses |
