# JavaScript Core Deep Dive

This document provides a comprehensive, deeply technical exploration of the core concepts of JavaScript. It is intended for senior engineers and covers the intricacies of the language, its execution model, and advanced patterns.

## 1. JavaScript Engine & Runtime (V8)

JavaScript is not executed directly by the CPU; it requires an engine to parse, compile, and execute the code. V8 is the most prominent JavaScript engine, powering Google Chrome and Node.js. Understanding its internal pipeline is crucial for writing highly performant code.

### The Parsing Pipeline

The journey of JavaScript code from raw text to execution involves several stages:

1.  **Source Code:** The raw text of your JavaScript files.
2.  **Tokenizer/Scanner:** The source code is broken down into a stream of tokens (keywords, identifiers, operators, punctuation).
3.  **Parser:** The tokens are analyzed to build an Abstract Syntax Tree (AST), a tree representation of the syntactic structure of the code. V8 uses a two-pass parser:
    *   **Pre-parser:** Skips function bodies to speed up initial loading.
    *   **Full parser:** Parses function bodies when they are actually called.
4.  **Ignition (Interpreter):** The AST is converted into bytecode by Ignition. Bytecode is a platform-independent representation of the code, which is then executed by the interpreter.
5.  **TurboFan (Optimizing Compiler):** As the bytecode executes, V8 monitors it (profiling). Hot functions (functions called frequently) are sent to TurboFan, which compiles the bytecode into highly optimized machine code specifically tailored to the target CPU architecture.
6.  **Deoptimization:** If the assumptions made by TurboFan during optimization turn out to be false (e.g., a variable's type changes), the engine throws away the optimized machine code and falls back to the Ignition interpreter. This is a costly operation.

### Hidden Classes (Shapes)

JavaScript is a dynamic language; properties can be added or removed from objects at runtime. Statically typed languages (like C++ or Java) use fixed offsets in memory to access properties because the object structure is known at compile time. V8 emulates this performance using "Hidden Classes" (also known as Shapes or Maps).

Whenever a new object is created, V8 creates a hidden class for it. If a property is added, V8 creates a *new* hidden class and updates the object to point to this new class. The new hidden class contains a transition path from the old one.

```javascript
// Example of fast vs slow object construction

// FAST: Creating objects with the same shape in the same order
function PointFast(x, y) {
    this.x = x;
    this.y = y;
}

const p1 = new PointFast(1, 2); // Hidden Class A -> B -> C
const p2 = new PointFast(3, 4); // Reuses Hidden Class C

// SLOW: Creating objects with different shapes (kills Inline Caching)
function PointSlow(x, y, addZ) {
    this.x = x;
    this.y = y;
    if (addZ) {
        this.z = 10;
    }
}

const p3 = new PointSlow(1, 2, false); // Hidden Class A -> B -> C
const p4 = new PointSlow(3, 4, true);  // Hidden Class A -> B -> C -> D

// p3 and p4 now have different hidden classes. Functions operating on both
// will become polymorphic or megamorphic.
```

To maximize performance, always initialize object properties in the same order, preferably in the constructor.

### Inline Caching (IC)

Inline Caching is an optimization technique used to speed up property access. When a function is called repeatedly, V8 records the hidden classes of the objects passed to it.

*   **Monomorphic:** The function has only seen objects with a single hidden class. V8 optimizes the property access to a direct memory offset lookup. Extremely fast.
*   **Polymorphic:** The function has seen objects with 2 to 4 different hidden classes. V8 generates a small switch statement to check the hidden class before the offset lookup. Still reasonably fast.
*   **Megamorphic:** The function has seen objects with 5 or more different hidden classes. V8 gives up on Inline Caching and falls back to a generic, slow hash table lookup.

```javascript
function getX(obj) {
    return obj.x;
}

const obj1 = { x: 1 };
const obj2 = { x: 2, y: 3 };
const obj3 = { y: 4, x: 5 }; // Different shape than obj2!

getX(obj1); // IC learns shape of obj1 (Monomorphic)
getX(obj1); // Fast path used

getX(obj2); // IC learns shape of obj2 (Polymorphic)
getX(obj2); // Fast path used (with a check)

// If we keep passing objects with different shapes, getX becomes Megamorphic
```

### Memory Model

The JavaScript execution environment manages memory in two primary areas:

1.  **Stack:**
    *   Stores primitive values (numbers, booleans, strings, null, undefined).
    *   Stores references (pointers) to objects in the Heap.
    *   Stores function call frames (execution contexts).
    *   Memory allocation and deallocation are extremely fast (push/pop).
    *   Size is strictly limited (Stack Overflow occurs when exceeded).

2.  **Heap:**
    *   A large, unstructured region of memory.
    *   Stores objects, arrays, closures, and functions.
    *   Memory allocation is dynamic and managed by the Garbage Collector.

```javascript
function memoryExample() {
    // 'a' is a primitive, stored on the Stack
    const a = 10;

    // 'obj' is a reference on the Stack, pointing to the actual object in the Heap
    const obj = { value: 20 };

    // 'fn' is a reference on the Stack, pointing to the function object in the Heap
    const fn = function() {
        return a + obj.value; // Closure captures references to 'a' and 'obj'
    };
}
```

### Garbage Collection (GC)

Garbage Collection is the automatic process of reclaiming memory that is no longer in use. V8 uses a Mark-and-Sweep algorithm, heavily optimized using a Generational hypothesis.

The Generational hypothesis states that most objects die young. Therefore, the Heap is divided into two main generations:

1.  **Young Generation (Nursery):**
    *   Where new objects are allocated.
    *   Small in size.
    *   Collected frequently using a process called **Scavenge**.
    *   The Scavenge algorithm is extremely fast. It divides the Young Generation into two semi-spaces ("from" and "to"). It copies surviving objects from the "from" space to the "to" space, then swaps the spaces.

2.  **Old Generation:**
    *   Objects that survive multiple Scavenge collections are "tenured" (promoted) to the Old Generation.
    *   Large in size.
    *   Collected less frequently using **Mark-Sweep** and **Mark-Compact** algorithms.
    *   **Marking:** The GC traverses the object graph starting from root references (global object, active stack frames). Any object reached is marked as "alive".
    *   **Sweeping:** Unmarked objects are considered dead, and their memory is added to a free list.
    *   **Compacting:** To prevent memory fragmentation, live objects are moved together to contiguous memory blocks.

**Stop-The-World Pauses vs. Incremental Marking:**
Traditionally, Mark-and-Sweep requires pausing the entire application execution ("stop-the-world") to traverse the object graph safely. For large heaps, this pause can be noticeable and cause jank.
Modern V8 uses **Incremental Marking**, which interleaves marking work with JavaScript execution in small chunks, significantly reducing maximum pause times. It also uses Concurrent Marking on background threads.

## 2. The Event Loop — Exhaustive Deep Dive

JavaScript is single-threaded, meaning it has only one Call Stack and can execute only one piece of code at a time. However, it can handle concurrent operations (like network requests, timers, I/O) without blocking the main thread. This non-blocking concurrency is achieved through the Event Loop and asynchronous APIs.

### The Call Stack

The Call Stack is a LIFO (Last-In, First-Out) data structure that records where in the program we are.
*   When a function is called, an execution context (stack frame) is pushed onto the stack.
*   When the function returns, its frame is popped off the stack.
*   If the stack exceeds its maximum size (typically around 10,000 frames), a `RangeError: Maximum call stack size exceeded` is thrown.

### Web APIs / Node C++ APIs

These are features provided by the environment (browser or Node.js), not by the JavaScript engine itself.
*   **Browser Web APIs:** `setTimeout`, `fetch`, DOM events, `XMLHttpRequest`.
*   **Node.js C++ APIs:** `fs.readFile`, `crypto.pbkdf2`, network sockets.
When you call an asynchronous API, the Call Stack delegates the work to these background threads/APIs. The JavaScript execution continues immediately. Once the background task finishes, its callback is pushed to one of the queues.

### Microtask Queue vs. Macrotask Queue

The Event Loop manages two primary queues for pending callbacks:

1.  **Microtask Queue:**
    *   Has higher priority.
    *   Contains callbacks from Promises (`.then`, `.catch`, `.finally`), `queueMicrotask()`, and `MutationObserver`.
    *   The Event Loop will completely drain the Microtask Queue before moving on to anything else. If a microtask queues another microtask, it will be executed in the same cycle.

2.  **Macrotask Queue (Callback Queue or Task Queue):**
    *   Contains callbacks from `setTimeout`, `setInterval`, `setImmediate` (Node), DOM events, and I/O operations.
    *   The Event Loop executes only *one* macrotask at a time.

### Event Loop Algorithm Step-by-Step

1.  **Execute Synchronous Code:** Run the script on the Call Stack until it is empty.
2.  **Drain Microtasks:** Process all callbacks in the Microtask Queue. If microtasks enqueue more microtasks, process those as well until the queue is completely empty.
3.  **Execute ONE Macrotask:** Take the oldest callback from the Macrotask Queue and push it onto the Call Stack to execute.
4.  **Drain Microtasks Again:** After the single macrotask finishes, process all callbacks in the Microtask Queue again until empty.
5.  **Render (Browser Only):** Update the UI if necessary (usually tied to screen refresh rate, e.g., 60Hz).
6.  **Repeat:** Go back to step 3.

### Node.js Event Loop Phases (libuv)

Node.js uses the `libuv` library to implement the event loop, which defines specific phases, each with its own FIFO queue of callbacks.

1.  **timers:** Executes callbacks scheduled by `setTimeout` and `setInterval`.
2.  **pending callbacks:** Executes deferred I/O callbacks (e.g., some TCP socket errors).
3.  **idle, prepare:** Used internally by libuv.
4.  **poll:** Retrieves new I/O events; executes I/O related callbacks (almost all with the exception of close callbacks, the ones scheduled by timers, and `setImmediate`). Node will block here if appropriate.
5.  **check:** Executes callbacks scheduled by `setImmediate`.
6.  **close callbacks:** Executes close callbacks, e.g., `socket.on('close', ...)`.

**`process.nextTick`:**
`process.nextTick` is a Node.js specific mechanism. It is *not* part of the libuv event loop. Callbacks passed to `process.nextTick` are stored in the `nextTickQueue`.
Crucially, the `nextTickQueue` is completely drained **immediately after the current operation on the Call Stack completes**, and **before** the Microtask Queue is processed, and **before** the event loop continues to the next phase.

### Complete Execution Order Example

```javascript
console.log('1');

setTimeout(() => console.log('2'), 0);

Promise.resolve().then(() => console.log('3'));

process.nextTick(() => console.log('4'));

queueMicrotask(() => console.log('5'));

console.log('6');

// Output order: 1, 6, 4, 3, 5, 2
```

**Explanation of the output:**
1.  `console.log('1')`: Synchronous execution. (Prints 1)
2.  `setTimeout`: Schedules macrotask '2' for the timers phase.
3.  `Promise.resolve().then()`: Queues microtask '3'.
4.  `process.nextTick()`: Queues nextTick callback '4'.
5.  `queueMicrotask()`: Queues microtask '5'.
6.  `console.log('6')`: Synchronous execution. (Prints 6)
7.  Call stack is empty. Node checks the `nextTickQueue`. It drains it. (Prints 4)
8.  Node checks the Microtask Queue. It drains it in order of insertion. (Prints 3, then 5)
9.  Event loop enters the timers phase. It finds macrotask '2' and executes it. (Prints 2)

## 3. Closures & Scope

Understanding scope and closures is fundamental to writing robust JavaScript.

### Lexical Scope

JavaScript uses Lexical Scoping (also known as Static Scoping). This means that the scope of a variable is determined by its physical location within the source code at **write time**, not where the function is called at runtime.

### The Scope Chain

When a variable is accessed, the JavaScript engine looks for it in the current scope. If it's not found, it traverses up the Scope Chain to the outer (parent) lexical environment, continuing this process until it reaches the Global Scope. If it's still not found, a `ReferenceError` is thrown (in strict mode).

### Closure Definition

A closure is the combination of a function bundled together (enclosed) with references to its surrounding state (the lexical environment). In simpler terms, a closure gives you access to an outer function's scope from an inner function, **even after the outer function has finished executing.**

Every function in JavaScript is a closure, because every function retains a hidden `[[Environment]]` reference to the lexical scope in which it was created.

### Practical Closure Patterns

#### 1. Counter Factory (Data Privacy)

Closures are the classic way to emulate private variables in JavaScript.

```javascript
function createCounter(initialValue = 0) {
    let count = initialValue; // 'count' is private

    return {
        increment: function() {
            count++;
            return count;
        },
        decrement: function() {
            count--;
            return count;
        },
        getValue: function() {
            return count;
        }
    };
}

const counter = createCounter(10);
console.log(counter.increment()); // 11
console.log(counter.count); // undefined (cannot access directly)
```

#### 2. Memoization Function

Caching the results of expensive function calls based on their arguments.

```javascript
function memoize(fn) {
    const cache = new Map(); // The cache is preserved via closure

    return function(...args) {
        const key = JSON.stringify(args);
        if (cache.has(key)) {
            console.log('Fetching from cache');
            return cache.get(key);
        }
        console.log('Calculating result');
        const result = fn(...args);
        cache.set(key, result);
        return result;
    };
}

const expensiveCalculation = (x, y) => {
    // Simulate complex math
    for (let i = 0; i < 1e7; i++) {}
    return x * y;
};

const memoizedCalc = memoize(expensiveCalculation);
console.log(memoizedCalc(5, 5)); // Calculating result: 25
console.log(memoizedCalc(5, 5)); // Fetching from cache: 25
```

#### 3. Partial Application / Currying

Fixing a number of arguments to a function, producing another function of smaller arity.

```javascript
// Partial application
function multiply(a, b) {
    return a * b;
}

function partial(fn, ...presetArgs) {
    return function(...laterArgs) {
        return fn(...presetArgs, ...laterArgs);
    };
}

const double = partial(multiply, 2);
console.log(double(5)); // 10

// Currying
function curry(fn) {
    return function curried(...args) {
        if (args.length >= fn.length) {
            return fn(...args);
        } else {
            return function(...moreArgs) {
                return curried(...args, ...moreArgs);
            };
        }
    };
}

const curriedMultiply = curry(multiply);
console.log(curriedMultiply(2)(5)); // 10
```

#### 4. Module Pattern (IIFE)

Before ES Modules, Immediately Invoked Function Expressions (IIFEs) were used to create isolated scopes and modules.

```javascript
const CalculatorModule = (function() {
    // Private state
    let memory = 0;

    // Private method
    function formatResult(val) {
        return `Result: ${val}`;
    }

    // Public API
    return {
        add: function(a, b) {
            memory = a + b;
            return formatResult(memory);
        },
        getMemory: function() {
            return memory;
        }
    };
})();

console.log(CalculatorModule.add(5, 10)); // Result: 15
console.log(CalculatorModule.memory); // undefined
```

### The Classic `var` in Loop Bug

The `var` keyword is function-scoped, not block-scoped. When used in an asynchronous loop, closures capture the *variable binding*, not the value at that moment in time.

```javascript
// BUGGY VERSION
for (var i = 0; i < 3; i++) {
    // All 3 timeouts share the SAME lexical environment containing 'i'.
    // By the time the callbacks run, the loop has finished, and 'i' is 3.
    setTimeout(() => console.log(i), 0);
}
// Prints: 3, 3, 3

// FIX WITH LET
for (let i = 0; i < 3; i++) {
    // 'let' is block-scoped. The loop creates a NEW lexical environment
    // for each iteration, with a fresh binding of 'i'. Each closure captures its own 'i'.
    setTimeout(() => console.log(i), 0);
}
// Prints: 0, 1, 2
```

### Memory Leaks with Closures

Closures prevent garbage collection of the outer scope variables they reference. If a closure is attached to a long-lived object (like a DOM element event listener) and it references large objects, it can cause a memory leak.

```javascript
function attachHandler() {
    const hugeData = new Array(1000000).fill('data');
    const element = document.getElementById('myButton');

    // The event listener closure captures 'hugeData'.
    // As long as 'element' exists in the DOM and the listener is attached,
    // 'hugeData' cannot be garbage collected.
    element.addEventListener('click', function() {
        console.log('Button clicked', hugeData.length);
    });
}
// Fix: Use removeEventListener when the element is no longer needed.
```

## 4. `this` Binding — All 4 Rules + Priority

The `this` keyword in JavaScript is a source of much confusion because its value is determined dynamically at **call time**, based on *how* the function is invoked, not where it is defined (with the exception of arrow functions).

There are four primary rules for determining the value of `this`.

### Rule 1: Default Binding

If a function is invoked standalone (not as a method, without `new`, without `call`/`apply`), the default binding applies.

*   **Sloppy Mode (non-strict):** `this` points to the global object (`window` in browsers, `global` in Node.js, or `globalThis`).
*   **Strict Mode (`"use strict"`):** `this` is `undefined`. This prevents accidental modification of the global object.

```javascript
function defaultBinding() {
    console.log(this);
}

defaultBinding(); // window (sloppy) or undefined (strict)
```

### Rule 2: Implicit Binding

If a function is invoked as a method of an object, `this` is bound to the object that the function is a property of (the object immediately preceding the dot at call time).

```javascript
const user = {
    name: 'Alice',
    greet: function() {
        console.log(`Hello, my name is ${this.name}`);
    }
};

user.greet(); // 'this' is 'user'. Prints "Hello, my name is Alice"

// The "Lost this" problem
const lostGreet = user.greet;
lostGreet(); // Invoked standalone! Default binding applies. Prints "Hello, my name is undefined"

// Lost 'this' as a callback
setTimeout(user.greet, 100); // setTimeout calls the function standalone internally. Lost 'this'.
```

### Rule 3: Explicit Binding

You can force `this` to be a specific object using `call`, `apply`, or `bind`.

*   **`fn.call(ctx, arg1, arg2)`:** Invokes the function immediately with `this` set to `ctx` and passes arguments individually.
*   **`fn.apply(ctx, [arg1, arg2])`:** Invokes the function immediately with `this` set to `ctx` and passes arguments as an array.
*   **`fn.bind(ctx, arg1)`:** Does *not* invoke the function immediately. Returns a **new** function where `this` is permanently bound to `ctx`.

```javascript
const person1 = { name: 'Bob' };
const person2 = { name: 'Charlie' };

function sayHello(greeting) {
    console.log(`${greeting}, ${this.name}`);
}

sayHello.call(person1, 'Hi'); // "Hi, Bob"
sayHello.apply(person2, ['Hola']); // "Hola, Charlie"

const boundHello = sayHello.bind(person1);
boundHello('Greetings'); // "Greetings, Bob"
```

### Rule 4: `new` Binding

When a function is invoked with the `new` keyword (as a constructor), four things happen implicitly:

1.  A brand new empty object is created.
2.  The new object's `[[Prototype]]` internal property is linked to the constructor function's `.prototype` object.
3.  The constructor function is executed with `this` bound to the newly created object.
4.  Unless the constructor explicitly returns a non-primitive object, the new object is returned automatically.

```javascript
function Car(make, model) {
    // 1. this = {}
    // 2. this.__proto__ = Car.prototype
    this.make = make; // 3. Set properties
    this.model = model;
    // 4. return this; (implicit)
}

const myCar = new Car('Toyota', 'Corolla');
console.log(myCar.make); // "Toyota"
```

### Arrow Functions

Arrow functions (`() => {}`) are the exception to the above rules. They do **not** have their own `this` binding. Instead, they use Lexical Scoping for `this`. An arrow function's `this` is inherited from the enclosing lexical context where it was defined.

*   You cannot use `new` with an arrow function (it throws an error).
*   `call`, `apply`, and `bind` have no effect on the `this` value of an arrow function.

```javascript
const timer = {
    seconds: 0,
    start: function() {
        // Arrow function preserves 'this' from the 'start' method context
        setInterval(() => {
            this.seconds++;
            console.log(this.seconds);
        }, 1000);
    }
};
timer.start(); // Works correctly.
```

### Priority of Rules

If multiple rules apply, the engine determines precedence:

1.  **Highest Priority:** `new` binding.
2.  **Second Priority:** Explicit binding (`call`, `apply`, `bind`).
3.  **Third Priority:** Implicit binding (object method).
4.  **Lowest Priority:** Default binding.

```javascript
// Demonstrating Priority
function identify() {
    console.log(this.name);
}

const obj1 = { name: 'Object 1', identify: identify };
const obj2 = { name: 'Object 2' };

// Implicit vs Explicit
obj1.identify.call(obj2); // Explicit wins: prints "Object 2"

// Explicit (bind) vs new
const boundIdentify = identify.bind(obj1);
boundIdentify(); // Prints "Object 1"
const newInstance = new boundIdentify(); // new wins! 'this' is a new empty object, name is undefined.
```

### Tricky Interview Example (Class Methods as Callbacks)

```javascript
class ButtonHandler {
    constructor() {
        this.clickCount = 0;
        // Solution 2: bind in constructor
        // this.handleClick = this.handleClick.bind(this);
    }

    handleClick() {
        // When passed as a raw callback to addEventListener, 'this' is bound to the DOM element,
        // or undefined in some strict contexts, resulting in an error trying to access .clickCount
        this.clickCount++;
        console.log(`Clicked ${this.clickCount} times`);
    }

    // Solution 3: Class field arrow function (most modern approach)
    // handleClickArrow = () => {
    //     this.clickCount++;
    // }
}

const handler = new ButtonHandler();
const btn = document.createElement('button');

// THE BUG: Lost 'this' context
// btn.addEventListener('click', handler.handleClick);

// Solution 1: Wrapper arrow function
btn.addEventListener('click', () => handler.handleClick());
```

## 5. Prototypal Inheritance

JavaScript does not use classical inheritance (like Java/C++); it uses Prototypal Inheritance. Objects inherit directly from other objects.

### The `[[Prototype]]` Internal Slot

Every object in JavaScript has an internal, hidden property called `[[Prototype]]`. This property points to another object (or `null`). This linkage forms the Prototype Chain.
You can access this internal slot using `Object.getPrototypeOf(obj)` or the historical getter/setter `obj.__proto__`.

### `Object.create(proto)`

This is the purest way to create an object with a specific prototype.

```javascript
const animalInfo = {
    eat: function() { console.log("Nom nom"); }
};

// Create a new object 'dog' whose [[Prototype]] is 'animalInfo'
const dog = Object.create(animalInfo);
dog.bark = function() { console.log("Woof!"); };

dog.bark(); // Own property
dog.eat();  // Inherited via prototype chain
```

### Constructor Functions and `.prototype`

When you define a function, JavaScript automatically attaches a `.prototype` property to it. This object has a `.constructor` property pointing back to the function.

When you use the `new` keyword with a constructor function, the newly created object's `[[Prototype]]` is linked to the constructor function's `.prototype` object. This is how instances share methods.

```javascript
function Person(name) {
    this.name = name; // Instance property
}

// Shared method added to the prototype
Person.prototype.sayName = function() {
    console.log(`My name is ${this.name}`);
};

const p1 = new Person("Alice");
const p2 = new Person("Bob");

p1.sayName();
// Both instances share the exact same function object in memory
console.log(p1.sayName === p2.sayName); // true
console.log(Object.getPrototypeOf(p1) === Person.prototype); // true
```

### The `instanceof` Operator

The `instanceof` operator checks if the `.prototype` property of the constructor function appears anywhere in the `[[Prototype]]` chain of the object.

```javascript
console.log(p1 instanceof Person); // true, because Person.prototype is in p1's chain
console.log(p1 instanceof Object); // true, because Object.prototype is further up the chain
```

### `class` Syntax (ES6)

The `class` keyword is syntactic sugar over constructor functions and prototypal inheritance. It makes the syntax look like classical inheritance, but under the hood, it's still prototypes.

```javascript
// What a class roughly compiles to in ES5:
// ES6 Class:
// class Animal {
//     constructor(name) { this.name = name; }
//     speak() { console.log('Noise'); }
// }

// ES5 Equivalent:
function Animal(name) {
    this.name = name;
}
Animal.prototype.speak = function() {
    console.log('Noise');
};
```

### Prototype Chain Lookup

When you try to access a property on an object (`obj.prop`):
1.  The engine checks if `obj` has the property as an "own" property. If yes, it returns it.
2.  If not, it follows the `[[Prototype]]` link to the parent object (`obj.__proto__`) and checks there.
3.  This continues up the chain until the property is found, or it reaches `Object.prototype`, and finally `null`. If `null` is reached, it returns `undefined`.

### `hasOwnProperty()` vs `in` Operator

*   `obj.hasOwnProperty('prop')`: Returns `true` ONLY if the property exists directly on the object itself, not on its prototype chain.
*   `'prop' in obj`: Returns `true` if the property exists on the object OR anywhere in its prototype chain.

```javascript
const obj = Object.create({ inheritedProp: 'value' });
obj.ownProp = 123;

console.log(obj.hasOwnProperty('ownProp')); // true
console.log(obj.hasOwnProperty('inheritedProp')); // false

console.log('ownProp' in obj); // true
console.log('inheritedProp' in obj); // true
console.log('toString' in obj); // true (inherited from Object.prototype)
```

### Full Inheritance Example: ES5 vs ES6

```javascript
// --- ES5 Constructor Pattern ---
function Shape(color) {
    this.color = color;
}
Shape.prototype.getColor = function() {
    return this.color;
};

function Circle(color, radius) {
    // 1. Call super constructor to set instance properties
    Shape.call(this, color);
    this.radius = radius;
}
// 2. Set up prototype chain (Object.create creates a new obj with Shape.prototype as parent)
Circle.prototype = Object.create(Shape.prototype);
// 3. Fix the constructor reference
Circle.prototype.constructor = Circle;

Circle.prototype.getArea = function() {
    return Math.PI * this.radius * this.radius;
};

const c1 = new Circle('red', 5);
console.log(c1.getColor()); // 'red'


// --- ES6 Class Pattern (Syntactic Sugar) ---
class Shape6 {
    constructor(color) {
        this.color = color;
    }
    getColor() {
        return this.color;
    }
}

class Circle6 extends Shape6 {
    constructor(color, radius) {
        super(color); // Calls parent constructor, mandatory before using 'this'
        this.radius = radius;
    }
    getArea() {
        return Math.PI * this.radius * this.radius;
    }
}

const c2 = new Circle6('blue', 10);
console.log(c2.getColor()); // 'blue'
```

## 6. Promises & Async/Await — Complete Coverage

Promises are the standard way to handle asynchronous operations in modern JavaScript, avoiding callback hell and providing robust error handling.

### Promise States

A Promise represents the eventual completion (or failure) of an asynchronous operation. It has three mutually exclusive states:
1.  **Pending:** Initial state, neither fulfilled nor rejected.
2.  **Fulfilled (Resolved):** The operation completed successfully.
3.  **Rejected:** The operation failed.

Crucially, a promise is **immutable once settled** (fulfilled or rejected). Its state and value cannot change after that.

### `.then()` and Chaining

The `.then(onFulfilled, onRejected)` method is used to attach callbacks.
*   **Always returns a NEW Promise:** This is what enables chaining.
*   **Return Values:**
    *   If `onFulfilled` returns a normal value, the new promise is fulfilled with that value.
    *   If `onFulfilled` throws an error, the new promise is rejected with that error.
    *   **Flattening:** If `onFulfilled` returns *another Promise*, the new promise adopts the state and value of that returned promise. This prevents nested promises.

### Error Propagation

You don't need a `.catch()` for every `.then()`. Errors (rejections or thrown exceptions) propagate down the chain until they encounter the nearest `.catch()` (or a `.then` with an `onRejected` handler).

```javascript
fetchData()
    .then(data => processData(data)) // if this throws, it skips the next then
    .then(result => saveResult(result))
    .catch(error => {
        // Handles errors from fetchData, processData, OR saveResult
        console.error("Pipeline failed:", error);
    });
```

### Promise Combinators

These static methods operate on iterables of Promises.

*   **`Promise.all(iterable)`:**
    *   Resolves when **ALL** promises in the iterable resolve. Returns an array of results.
    *   Rejects immediately upon the **FIRST** rejection (fast-fail behavior).
*   **`Promise.allSettled(iterable)`:**
    *   Resolves when **ALL** promises settle (either resolve or reject).
    *   Never rejects. Returns an array of objects: `{status: 'fulfilled', value: ...}` or `{status: 'rejected', reason: ...}`. Useful when you need all outcomes regardless of failures.
*   **`Promise.race(iterable)`:**
    *   Settles as soon as the **FIRST** promise settles. Takes the value or reason of that first settled promise. Useful for timeouts.
*   **`Promise.any(iterable)`:**
    *   Resolves as soon as the **FIRST** promise **RESOLVES**.
    *   Rejects only if **ALL** promises reject (with an `AggregateError`). Useful for fallback sources.

### Async/Await

`async/await` is syntactic sugar built on top of Promises and Generators. It allows you to write asynchronous code that looks and behaves like synchronous code.

*   **`async` function:** Putting `async` before a function definition ensures that the function **always returns a Promise**. If the function returns a non-promise value, it is automatically wrapped in a resolved Promise.
*   **`await` keyword:** Can only be used inside an `async` function (or at the top level in ESM). It **pauses the execution of the `async` function** until the awaited Promise settles. While paused, the function yields control back to the Event Loop, allowing other code to run.

### Error Handling in Async/Await

Use standard `try/catch` blocks.

```javascript
async function fetchUser(id) {
    try {
        const response = await fetch(`/api/users/${id}`);
        if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Failed to fetch user:", error);
        // Rethrow or return fallback
        throw error; 
    }
}

// You can also catch errors on the returned promise
fetchUser(1).catch(err => console.log('Caught at call site:', err));
```

### Top-Level Await

In ES Modules (`type: "module"`), you can use `await` outside of an `async` function at the top level of a file. This is extremely useful for async initialization (e.g., establishing a database connection before exporting the module).

### The Classic Mistake: `await` inside `forEach`

The `Array.prototype.forEach` method expects a synchronous callback. It does *not* wait for Promises returned by an `async` callback to resolve before moving to the next iteration.

```javascript
// THE PROBLEM
async function processArrayWrong(items) {
    const results = [];
    // forEach fires off all async functions simultaneously and finishes immediately.
    // The results array will be empty at the end of this function.
    items.forEach(async (item) => {
        const res = await fetchData(item);
        results.push(res);
    });
    return results; // Returns [] immediately
}

// FIX 1: Sequential Execution (Wait for one to finish before starting next)
async function processArraySequential(items) {
    const results = [];
    for (const item of items) {
        // Pauses loop until fetchData resolves
        const res = await fetchData(item);
        results.push(res);
    }
    return results;
}

// FIX 2: Concurrent Execution (Start all, wait for all) - Usually better for performance
async function processArrayConcurrent(items) {
    // .map creates an array of pending Promises
    const promises = items.map(item => fetchData(item));
    // Wait for all to resolve
    const results = await Promise.all(promises);
    return results;
}
```

## 7. Generators & Iterators

Generators provide powerful control flow mechanisms, allowing functions to pause their execution and yield multiple values over time.

### The Iterator Protocol

An object is an iterator if it implements a `next()` method that returns an object with two properties:
*   `value`: The next value in the sequence.
*   `done`: A boolean indicating if the sequence has finished (`true` when done).

An object is **iterable** if it has a method accessible via the `Symbol.iterator` symbol, which returns an iterator. Arrays, Strings, Maps, and Sets are built-in iterables.

The `for...of` loop consumes iterables automatically.

```javascript
// Custom Iterable Implementation
class Sequence {
    constructor(start, end) {
        this.start = start;
        this.end = end;
    }
    
    [Symbol.iterator]() {
        let current = this.start;
        const end = this.end;
        return {
            next() {
                if (current <= end) {
                    return { value: current++, done: false };
                }
                return { value: undefined, done: true };
            }
        };
    }
}

for (const num of new Sequence(1, 3)) {
    console.log(num); // 1, 2, 3
}
```

### Generator Functions

A generator function is defined with `function*`. When called, it does not execute its body immediately. Instead, it returns a **Generator object**, which conforms to both the iterable and iterator protocols.

*   Execution pauses at every `yield` expression.
*   Execution resumes when `.next()` is called on the generator object.

```javascript
function* idMaker() {
    let index = 0;
    while (true) { // Infinite sequence! Safe because it pauses.
        yield index++;
    }
}

const gen = idMaker();
console.log(gen.next().value); // 0
console.log(gen.next().value); // 1
```

### `yield*` Delegation

`yield*` allows a generator to delegate iteration to another iterable or generator.

```javascript
function* generateSequence() {
    yield 1;
    yield* [2, 3]; // Delegates to the array iterable
    yield 4;
}
// Produces: 1, 2, 3, 4
```

### Two-Way Communication

You can pass values *into* a generator by providing an argument to the `.next(value)` method. This value becomes the result of the `yield` expression where the generator is currently paused.

```javascript
function* communicationGen() {
    console.log('Started');
    const input1 = yield 'First yield';
    console.log('Received:', input1);
    const input2 = yield 'Second yield';
    console.log('Received:', input2);
}

const g = communicationGen();
// First next() starts execution up to the first yield. The argument is ignored.
console.log(g.next().value); // 'Started', then logs 'First yield'
// Second next('Apple') resumes execution. 'Apple' is assigned to input1.
console.log(g.next('Apple').value); // 'Received: Apple', then logs 'Second yield'
```

### Async Generators

Combine `async` and `function*` to create generators that yield Promises. They are consumed using `for await...of`. This is perfect for processing asynchronous streams of data (like paginated API responses or reading large files chunk by chunk).

```javascript
// Real use case: Async pagination
async function* fetchPaginatedData(url) {
    let page = 1;
    let hasMore = true;

    while (hasMore) {
        const response = await fetch(`${url}?page=${page}`);
        const data = await response.json();
        
        yield data.items; // Yield array of items for this page
        
        hasMore = data.nextPage != null;
        page++;
    }
}

async function processAllItems() {
    const url = 'https://api.example.com/data';
    // for await...of automatically waits for the Promise yielded by the generator to resolve
    for await (const pageItems of fetchPaginatedData(url)) {
        for (const item of pageItems) {
            console.log("Processing item:", item.id);
        }
    }
}
```

## 8. Modules: ESM vs CJS

JavaScript has two primary module systems. Understanding the differences is critical for modern development and dealing with legacy code.

### CommonJS (CJS)

*   **Syntax:** `require()` and `module.exports`.
*   **Environment:** Native to Node.js (historically).
*   **Execution:** Synchronous and evaluated at **runtime**. `require()` blocks execution while loading the file.
*   **Dynamic:** You can use `require()` conditionally inside `if` statements or loops.
*   **Caching:** When a module is required for the first time, its code is executed, and the `module.exports` object is cached. Subsequent `require()` calls return the cached object (no re-execution).
*   **Value Copy:** CJS exports a *copy* of the value at the time of export (or a reference to the object).
*   **Tree-Shaking:** Extremely difficult for bundlers (like Webpack/Rollup) to statically analyze and perform dead code elimination, because exports can be modified dynamically at runtime.

### ES Modules (ESM)

*   **Syntax:** `import` and `export`.
*   **Environment:** Native to Browsers and natively supported in modern Node.js.
*   **Execution:** Asynchronous loading (in browsers). Analyzed at **parse time** (statically).
*   **Static:** `import` and `export` statements must be at the top level of the file. They cannot be conditional (though dynamic `import()` exists as a function returning a Promise).
*   **Tree-Shaking:** Because the structure is static, bundlers can easily determine which exports are never imported and remove that dead code.
*   **Live Bindings:** ESM exports **read-only live views** of the values. If the exporting module changes the value, the importing module sees the updated value immediately.
*   **Top-Level Await:** Supported.

### Node.js Configuration

By default, Node treats `.js` files as CommonJS. To use ESM, you must:
1.  Set `"type": "module"` in your `package.json`. All `.js` files are now ESM.
2.  Or use the `.mjs` extension for ESM files, and `.cjs` for CommonJS files.

### Interop between ESM and CJS

*   **ESM importing CJS:** An ES Module can `import` a CommonJS module. The `module.exports` object becomes the `default` export.
    ```javascript
    // In ESM file
    import cjsModule from './my-cjs.js'; 
    ```
*   **CJS importing ESM:** A CommonJS module **cannot** synchronously `require()` an ES Module (because ESM might have top-level await and loads asynchronously). You must use dynamic `import()`, which returns a Promise.
    ```javascript
    // In CJS file
    async function loadEsm() {
        const esmModule = await import('./my-esm.js');
    }
    ```

### Named vs Default Exports

*   **Default Export:** `export default myFunction;` | `import alias from './file.js';`. Only one per file. Good for exporting a single main entity (like a React component).
*   **Named Exports:** `export const x = 1;` | `import { x } from './file.js';`. You can have many. **Highly recommended for utility libraries** because it enables perfect tree-shaking (the bundler only includes the specific functions you import).

## 9. Type Coercion & Common Gotchas

JavaScript is dynamically and loosely typed. It aggressively coerces types to make operations work, which leads to infamous quirks.

### `==` (Abstract Equality) vs `===` (Strict Equality)

*   **`===` (Strict Equality):** Checks value AND type. No coercion.
    *   For primitives: true if values and types are identical.
    *   For objects: true ONLY if they reference the exact same object in memory (reference equality).
    *   **Always use `===` unless you have a specific, justifiable reason to use `==`.**
*   **`==` (Abstract Equality):** Performs type coercion if the operands are of different types before comparing.
    *   String & Number: Converts string to number. (`'5' == 5` is true).
    *   Boolean & Anything: Converts boolean to number (`true` to 1, `false` to 0) then compares. (`true == 1` is true).
    *   Object & Primitive: Calls `valueOf()` or `toString()` on the object to get a primitive, then compares.
    *   `null` and `undefined` are loosely equal to each other (`null == undefined` is true) and to nothing else.

### `NaN` (Not a Number)

`NaN` is a special numeric value representing an unrepresentable value (e.g., result of `0/0` or `Number('abc')`).

*   **The Golden Rule of NaN:** `NaN` is not equal to anything, **including itself**.
    `NaN === NaN` is **false**.
*   **How to check for NaN:** Do NOT use the global `isNaN()` function. It aggressively coerces non-numbers to numbers first (`isNaN('abc')` is true).
*   **Use `Number.isNaN(value)`:** This checks strictly if the value is both of type number AND is NaN.

### Falsy Values

When evaluating in a boolean context (like an `if` statement), the following values are coerced to `false` (falsy):
1.  `false`
2.  `0`
3.  `-0`
4.  `0n` (BigInt zero)
5.  `""` (empty string)
6.  `null`
7.  `undefined`
8.  `NaN`

**Everything else is truthy**, including empty arrays `[]` and empty objects `{}`.

### The `typeof null` Bug

```javascript
console.log(typeof null); // "object"
```
This is a historical bug in the first implementation of JavaScript that cannot be fixed because it would break the web. `null` is a primitive, not an object. To reliably check for null, use `val === null`.

### The `+` Operator

The `+` operator does double duty: numeric addition and string concatenation.
*   If **either** operand is a string, it converts the other operand to a string and concatenates.
*   Otherwise, it coerces both to numbers and adds.

```javascript
console.log(1 + 2 + "3"); // "33" (1+2 is 3, 3+"3" is "33")
console.log("1" + 2 + 3); // "123" ("1"+2 is "12", "12"+3 is "123")
console.log(true + true); // 2 (1 + 1)
```

### `{}` vs `[]` Coercion Gotchas

```javascript
console.log([] + []); // ""
// [] to primitive becomes "". "" + "" = ""

console.log([] + {}); // "[object Object]"
// [] -> "", {} -> "[object Object]". "" + "[object Object]"

console.log({} + []); // 0
// In REPLs, {} is treated as an empty block statement, not an object literal!
// So it executes an empty block, then evaluates `+ []`.
// Unary + coerces [] to number. [] -> "" -> 0.

console.log({} + {}); // "[object Object][object Object]" (in expressions) or NaN (in some REPLs)
```

This concludes the deep dive into JavaScript Core. Mastery of these concepts separates average developers from senior engineers capable of debugging complex execution, memory, and performance issues.
