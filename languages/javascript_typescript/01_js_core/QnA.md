# Module 1 Questions and Answers

### 1. Explain the JavaScript event loop. What is the difference between the microtask queue and the macrotask queue? What is the output of mixed code example?

The Event Loop is the mechanism that allows Node.js and browsers to perform non-blocking I/O operations despite JavaScript being single-threaded. It constantly monitors the Call Stack and the task queues. If the Call Stack is empty, it pushes the first task from the queues onto the stack.

The Macrotask Queue (or Callback Queue) holds callbacks for `setTimeout`, `setInterval`, I/O, and UI rendering. The Microtask Queue holds callbacks for Promises (`.then`, `.catch`, `.finally`), `queueMicrotask`, and `MutationObserver`.

The crucial difference in execution order is that after every single macrotask completes, the Event Loop will drain the ENTIRE microtask queue before picking up the next macrotask. If a microtask schedules another microtask, it will be executed in the same cycle, potentially blocking the macrotask queue (and UI rendering).

### 2. What is a closure? Give a practical example of a closure causing a memory leak and how to fix it.

A closure is the combination of a function bundled together with references to its surrounding state (the lexical environment). A closure gives a function access to its outer scope from an inner scope, even after the outer function has returned.

Memory leak example:
```javascript
function attachEvent() {
    const hugeData = new Array(10000000).fill("data");
    document.getElementById("btn").addEventListener("click", function handleClick() {
        console.log("Button clicked!", hugeData[0]);
    });
}
attachEvent();
```
In this example, the `handleClick` closure retains a reference to `hugeData`. As long as the button exists in the DOM, `hugeData` cannot be garbage collected.

To fix it, you can extract the handler, use event delegation, or remove the event listener when it is no longer needed:
```javascript
function attachEvent() {
    const hugeData = new Array(10000000).fill("data");
    const dataRef = hugeData[0]; // Only keep what you need
    document.getElementById("btn").addEventListener("click", function handleClick() {
        console.log("Button clicked!", dataRef);
    }, { once: true }); // Removes listener after first click
}
```

### 3. Explain all four `this` binding rules with examples. Which rule takes precedence?

The four rules determine what `this` refers to in a function:

1. **Default Binding:** If a function is called standalone (e.g., `func()`), `this` is the global object (in sloppy mode) or `undefined` (in strict mode).
   ```javascript
   function sayName() { console.log(this.name); }
   sayName(); // undefined
   ```
2. **Implicit Binding:** If a function is called as a method on an object, `this` is bound to the object.
   ```javascript
   const obj = { name: "Alice", sayName() { console.log(this.name); } };
   obj.sayName(); // "Alice"
   ```
3. **Explicit Binding:** Using `call()`, `apply()`, or `bind()` allows you to explicitly specify what `this` should be.
   ```javascript
   const obj = { name: "Bob" };
   function sayName() { console.log(this.name); }
   sayName.call(obj); // "Bob"
   ```
4. **New Binding:** When a function is invoked with the `new` keyword, a new object is created and `this` is bound to that new object.
   ```javascript
   function Person(name) { this.name = name; }
   const person = new Person("Charlie"); // this points to person
   ```

Precedence order: `new` Binding > Explicit Binding > Implicit Binding > Default Binding.

### 4. What is the difference between Promise.all(), Promise.allSettled(), Promise.race(), and Promise.any()?

- `Promise.all(iterable)`: Resolves when ALL promises resolve. Rejects immediately if ANY promise rejects (fail-fast).
- `Promise.allSettled(iterable)`: Resolves after ALL promises have settled (either resolved or rejected). Returns an array of objects describing the outcome of each promise (`{status: "fulfilled", value: ...}` or `{status: "rejected", reason: ...}`).
- `Promise.race(iterable)`: Resolves or rejects as soon as the FIRST promise settles. The outcome of the race determines the outcome of the overall promise.
- `Promise.any(iterable)`: Resolves as soon as the FIRST promise fulfills. It only rejects if ALL promises reject (returns an `AggregateError`).

### 5. Why does `await` inside `Array.prototype.forEach` not work as expected? How do you fix it?

`Array.prototype.forEach` expects a synchronous callback. If you pass an `async` function, `forEach` calls it and immediately proceeds to the next iteration without waiting for the promise returned by the async function to resolve. This results in the loop finishing before the asynchronous operations complete, often leading to race conditions or unhandled rejections.

To fix it, use a `for...of` loop for sequential execution:
```javascript
for (const item of array) {
    await processItem(item);
}
```
Or use `Promise.all()` with `map()` for parallel execution:
```javascript
await Promise.all(array.map(item => processItem(item)));
```

### 6. Explain prototypal inheritance. How does `class` in ES6 relate to prototypes?

In JavaScript, objects have an internal link to another object called their prototype (accessible via `Object.getPrototypeOf()`). When trying to access a property that does not exist in an object, JavaScript traverses the prototype chain upwards until it finds the property or reaches `null`. This is prototypal inheritance.

The ES6 `class` syntax is primarily "syntactic sugar" over JavaScript's existing prototype-based inheritance. Under the hood, a `class` creates a constructor function, and methods defined inside the class block are added to the constructor's `.prototype` object.
```javascript
class Animal {
    speak() {}
}
// is essentially equivalent to:
function Animal() {}
Animal.prototype.speak = function() {};
```

### 7. What is the difference between CommonJS require() and ES Module import?

- **Syntax:** CommonJS uses `require()` and `module.exports`. ES Modules use `import` and `export`.
- **Loading:** CommonJS loads modules synchronously. It is designed for server-side use where files are on local disk. ES Modules load asynchronously and are designed to be statically analyzed, making them suitable for both browser and server.
- **Evaluation:** CommonJS resolves module dependencies dynamically at runtime. ES Modules parse and link modules statically before executing the code.
- **Tree Shaking:** Because ES Modules are statically analyzable, bundlers can eliminate dead code (tree shaking) much more effectively than with CommonJS.

### 8. What are generators? Give a real use case where you would use a generator over an async function.

Generators are functions that can be exited and later re-entered, maintaining their context (variable bindings) across re-entrances. They are declared with `function*` and use the `yield` keyword to pause execution and return a value.

A real use case over an async function is generating an infinite sequence of data lazily or processing large streams of data without loading everything into memory. For example, a UUID generator or paginated API consumer:

```javascript
async function* fetchPages(url) {
    let nextUrl = url;
    while (nextUrl) {
        const response = await fetch(nextUrl);
        const data = await response.json();
        yield data.results;
        nextUrl = data.next_page;
    }
}
```
You can consume this one page at a time using `for await...of`, whereas a standard async function would have to return all pages at once or handle the loop state externally.

### 9. What is process.nextTick in Node.js and how does it differ from Promise.then()?

`process.nextTick` is a Node.js specific API that schedules a callback to run immediately after the current operation completes, but BEFORE the event loop proceeds to the next phase, and significantly, BEFORE any microtasks (like Promises) are processed.

While `Promise.then()` callbacks are placed in the microtask queue, `process.nextTick` callbacks are placed in the "nextTick queue". When the current synchronous code finishes, Node drains the nextTick queue completely, and only then drains the microtask queue. Therefore, `process.nextTick` has higher priority than Promises.

### 10. Explain the difference between == and ===. When would == ever be preferred?

- `===` (Strict Equality) compares both value and type. If the types are different, it immediately returns `false`.
- `==` (Abstract Equality) performs type coercion before comparison if the types differ, following complex algorithms defined in the ECMAScript specification.

Generally, `===` is preferred to avoid unexpected coercion bugs (e.g., `"" == 0` is `true`). However, `==` is sometimes preferred for succinctly checking for `null` or `undefined`.
`if (val == null)` evaluates to `true` if `val` is exactly `null` OR exactly `undefined`. Using `===` requires `if (val === null || val === undefined)`.

### 11. What is the JavaScript memory model? Where are primitives stored vs objects?

The memory model consists of two primary areas: the Stack and the Heap.
- **The Stack:** Used for static memory allocation. It stores primitive values (strings, numbers, booleans, undefined, null, symbol, bigint) and references to objects. It is organized as a Last-In, First-Out (LIFO) data structure corresponding to execution contexts (function calls).
- **The Heap:** Used for dynamic memory allocation. It stores objects, arrays, and functions. Memory here is unstructured and managed by the Garbage Collector. Variables in the stack hold pointers to locations in the heap.

### 12. Explain how V8's hidden classes work and why mutating object shapes hurts performance.

JavaScript is dynamically typed, meaning properties can be added or removed from objects on the fly. To optimize property access, V8 uses "hidden classes" (or Shapes).

When an object is created, V8 creates a hidden class for it. If you add a property, V8 creates a new hidden class and updates the object's pointer to the new class, recording a transition from the old class to the new one.
If multiple objects share the same layout (same properties added in the same order), they share the same hidden class. This allows the JIT compiler to use "Inline Caching" to memorize the offset of properties.

Mutating object shapes (e.g., deleting properties or adding them in different orders) forces V8 to create many different hidden classes (polymorphism). This disables inline caching optimizations and severely degrades property access performance.

### 13. What is the output of the following code?
```javascript
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 10);
}
```
The output is `3 3 3`.
Because `var` has function scope (or global scope if outside a function), there is only one binding for the variable `i`. By the time the `setTimeout` callbacks run (after 10ms, in the macrotask queue), the loop has completely finished executing, and the value of `i` is 3.

If `let` was used instead, the output would be `0 1 2` because `let` creates a new lexical scope (a new binding) for `i` in each iteration of the loop.

### 14. How does bind() work? What is the difference between call(), apply(), and bind()?

- `call(thisArg, arg1, arg2)`: Invokes the function immediately, setting `this` to `thisArg` and passing arguments individually.
- `apply(thisArg, [argsArray])`: Invokes the function immediately, setting `this` to `thisArg` and passing arguments as an array.
- `bind(thisArg, arg1, arg2)`: Does NOT invoke the function immediately. Instead, it returns a new function with `this` permanently bound to `thisArg` and any initial arguments partially applied.

### 15. Explain async generators and for await...of. Give a real use case.

Async generators (`async function*`) combine asynchronous operations with the generator pattern. They yield Promises. The `for await...of` loop is specifically designed to iterate over async iterables, waiting for each yielded Promise to resolve before continuing to the next iteration.

A real use case is processing a large file line by line using streams without loading the entire file into memory:

```javascript
const fs = require('fs');
const readline = require('readline');

async function processFile() {
  const fileStream = fs.createReadStream('large-log.txt');
  const rl = readline.createInterface({ input: fileStream });

  // rl is an async iterable
  for await (const line of rl) {
    console.log(`Processing: ${line}`);
    // Await some async processing per line
  }
}
```
