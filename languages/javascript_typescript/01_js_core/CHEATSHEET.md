# Module 1 Cheatsheet: JavaScript Core Mechanics

## Event Loop Execution Order Diagram

```text
+-----------------------------------------------------+
|                     CALL STACK                      |
| (Executes Synchronous Code until empty)             |
+--------------------------+--------------------------+
                           |
                           v
+--------------------------+--------------------------+
|            process.nextTick Queue (Node.js only)    |
| (Drained completely, including new additions)       |
+--------------------------+--------------------------+
                           |
                           v
+--------------------------+--------------------------+
|                   MICROTASK QUEUE                   |
| - Promise.then / .catch / .finally                  |
| - queueMicrotask                                    |
| - MutationObserver (Browser)                        |
| (Drained completely, including new additions)       |
+--------------------------+--------------------------+
                           |
                           v
+--------------------------+--------------------------+
|                   MACROTASK QUEUE                   |
| - setTimeout / setInterval                          |
| - setImmediate (Node.js)                            |
| - I/O, UI Rendering (Browser)                       |
| (Processes ONE task, then returns to microtasks)    |
+-----------------------------------------------------+
```

## `this` Binding Rules Priority Table

| Priority | Rule | Example | `this` points to |
|---|---|---|---|
| 1 (Highest) | **New Binding** | `const obj = new MyFunction()` | The newly created object. |
| 2 | **Explicit Binding** | `func.call(obj)` / `func.bind(obj)` | The specified object (`obj`). |
| 3 | **Implicit Binding** | `obj.method()` | The object preceding the dot (`obj`). |
| 4 (Lowest) | **Default Binding** | `func()` | Global object (`window`/`global`), or `undefined` in strict mode. |
| N/A | **Arrow Function** | `() => console.log(this)` | Lexical scope (enclosing context). Overrides all rules. |

## Promise Combinators Comparison Table

| Combinator | Resolves When... | Rejects When... | Return Value on Success | Return Value on Failure |
|---|---|---|---|---|
| `Promise.all()` | ALL promises resolve. | ANY promise rejects (fail-fast). | Array of resolved values. | First rejection reason. |
| `Promise.allSettled()` | ALL promises settle (resolve/reject). | Never. | Array of outcome objects. | N/A |
| `Promise.race()` | FIRST promise settles (resolve). | FIRST promise settles (reject). | Value of first settled. | Reason of first settled. |
| `Promise.any()` | FIRST promise resolves. | ALL promises reject. | Value of first resolved. | `AggregateError` array. |

## ESM vs CJS Comparison Table

| Feature | CommonJS (CJS) | ECMAScript Modules (ESM) |
|---|---|---|
| **Syntax** | `require()` / `module.exports` | `import` / `export` |
| **Loading Strategy** | Synchronous | Asynchronous |
| **Resolution Time** | Runtime (dynamic) | Parse time (static) |
| **Tree Shaking** | Poor (hard to analyze) | Excellent (statically analyzable) |
| **File Extension** | `.js`, `.cjs` | `.js`, `.mjs` (`type: "module"`) |
| **Top-level `await`** | Not supported | Supported |
| **Primary Environment** | Node.js (historical) | Browser & Node.js (modern) |

## Falsy Values Quick-Reference

In JavaScript, a value is considered "falsy" if it coerces to `false` in a boolean context (e.g., in an `if` statement). There are exactly 8 falsy values:

1. `false`
2. `0` (Number zero)
3. `-0` (Negative zero)
4. `0n` (BigInt zero)
5. `""`, `''`, `\`` (Empty strings)
6. `null`
7. `undefined`
8. `NaN` (Not a Number)

*Everything else is truthy, including empty arrays `[]` and empty objects `{}`.*
