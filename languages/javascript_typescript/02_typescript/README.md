# TypeScript Deep Dive

This document provides a comprehensive, deeply technical exploration of TypeScript. It covers the type system mechanics, advanced generics, utility types, and architectural configurations required for enterprise-grade applications.

## 1. Why TypeScript & Structural Typing

TypeScript (TS) is a superset of JavaScript that adds a static type system. It does not exist at runtime; the TS compiler (`tsc`) strips away all type annotations and emits plain JavaScript. The primary goals are developer tooling (autocomplete, refactoring) and catching errors at compile time rather than runtime.

### Structural Typing (Duck Typing)

Unlike nominally typed languages (Java, C#, C++), where types are only compatible if they are explicitly declared to be related (e.g., via inheritance), TypeScript uses **Structural Typing**.

In a structural type system, if two objects have the same shape (properties and methods), they are considered compatible, regardless of their names. "If it walks like a duck and quacks like a duck, it's a duck."

```typescript
interface Point2D {
    x: number;
    y: number;
}

interface Vector2 {
    x: number;
    y: number;
}

function calculateLength(p: Point2D) {
    return Math.sqrt(p.x * p.x + p.y * p.y);
}

const v: Vector2 = { x: 3, y: 4 };
// Valid! Vector2 has all the properties required by Point2D
calculateLength(v); 

// Extra properties are also fine when passing object literals via variables
const point3D = { x: 1, y: 2, z: 3 };
calculateLength(point3D); // Valid. point3D fulfills structural requirement of Point2D
```

### Type Inference

TypeScript is smart enough to infer types in most contexts, meaning explicit annotations are often unnecessary and just add noise.

```typescript
let x = 3; // TS infers 'number'
// x = "string"; // Error: Type 'string' is not assignable to type 'number'

const numbers = [1, 2, 3];
// TS infers n is number
const doubled = numbers.map(n => n * 2); 
```

### Type Widening and `as const`

When you declare a mutable variable using `let`, TypeScript widens the type to the general primitive. When you use `const`, it infers the literal type.

```typescript
let myLet = 'hello'; // Type is widened to 'string'
const myConst = 'hello'; // Type is literal string 'hello'
```

The `as const` (const assertion) tells the compiler to infer the narrowest, most specific literal types possible, and marks all properties as `readonly`. It prevents widening.

```typescript
const config = {
    endpoint: '/api',
    method: 'GET'
}; // Type is { endpoint: string; method: string; }

const strictConfig = {
    endpoint: '/api',
    method: 'GET'
} as const; 
// Type is { readonly endpoint: "/api"; readonly method: "GET"; }
```

## 2. Primitive & Special Types

TypeScript extends JS primitives with powerful special types.

### Primitives
`string`, `number`, `boolean`, `symbol`, `bigint`.

### Special Types

*   **`any`:** The ultimate escape hatch. It turns off all type checking for that value. Treat it as a code smell. Use it only during migrations or when dealing with untyped 3rd party libraries where writing definitions is impossible.
*   **`unknown`:** The type-safe alternative to `any`. You can assign anything to `unknown`, but you **cannot** perform operations on it until you narrow its type (prove to TS what it actually is).
    ```typescript
    let data: unknown = fetchData();
    // data.foo(); // Error: Object is of type 'unknown'
    if (typeof data === 'string') {
        console.log(data.toUpperCase()); // OK, narrowed to string
    }
    ```
*   **`void`:** Indicates a function returns no meaningful value (it returns implicitly or explicitly returns `undefined`).
*   **`never`:** The bottom type. Represents a state that should never occur. Used for functions that always throw or infinite loops, and heavily used in exhaustive type checking and advanced generics.
    ```typescript
    function crash(message: string): never {
        throw new Error(message);
    }
    ```
*   **`null` and `undefined`:** With the crucial `strictNullChecks` flag enabled, these are distinct types and not assignable to other types. `let name: string = null` is an error.

### Literal Types and Template Literals

You can use exact values as types.

```typescript
type Direction = 'left' | 'right' | 'up' | 'down';
type StatusCode = 200 | 404 | 500;

// Template Literal Types build string types dynamically
type Color = 'Red' | 'Blue';
type Size = 'Small' | 'Large';
// Produces: "SmallRed" | "SmallBlue" | "LargeRed" | "LargeBlue"
type ProductVariant = `${Size}${Color}`; 
```

## 3. Union & Intersection Types

### Union Types (`|`)

A value can be one of several types. You must narrow the union before using properties specific to one member.

```typescript
function printId(id: number | string) {
    // id.toUpperCase(); // Error: Property 'toUpperCase' does not exist on type 'number | string'
    if (typeof id === 'string') {
        console.log(id.toUpperCase()); // OK
    }
}
```

### Intersection Types (`&`)

Combines multiple types into one. An object of an intersection type must have all properties from all intersecting types.

```typescript
type HasName = { name: string };
type HasAge = { age: number };
type Person = HasName & HasAge;

const bob: Person = { name: "Bob", age: 30 }; // Must have both
```

### Discriminated Unions (Tagged Unions)

This is the most powerful pattern for modeling complex state in TypeScript (e.g., Redux actions, API responses, AST nodes). You use a common literal property (the discriminant/tag) to distinguish between union members.

```typescript
type Shape =
    | { kind: 'circle'; radius: number }
    | { kind: 'rect'; width: number; height: number }
    | { kind: 'triangle'; base: number; height: number };

function area(s: Shape): number {
    switch (s.kind) { // Discriminant property
        case 'circle':
            // TS knows s is exactly { kind: 'circle', radius: number } here
            return Math.PI * s.radius ** 2;
        case 'rect':
            return s.width * s.height;
        case 'triangle':
            return 0.5 * s.base * s.height;
    }
}
```

### Exhaustive Checking with `never`

Combined with discriminated unions, the `never` type ensures you handle all cases in a `switch` statement. If you add a new member to the union but forget to update the switch, TS throws an error.

```typescript
function assertNever(x: never): never {
    throw new Error('Unhandled case: ' + x);
}

function safeArea(s: Shape): number {
    switch (s.kind) {
        case 'circle': return Math.PI * s.radius ** 2;
        case 'rect': return s.width * s.height;
        case 'triangle': return 0.5 * s.base * s.height;
        default:
            // If we didn't handle 'triangle' above, s would be of type 
            // { kind: 'triangle' ... } here, which is not assignable to 'never'.
            // TS will error at compile time!
            return assertNever(s); 
    }
}
```

## 4. Type Narrowing — All Techniques

Type narrowing is the process of moving from a less precise type (like `unknown` or `string | number`) to a more precise type.

1.  **`typeof` narrowing:** For primitives.
    ```typescript
    if (typeof padding === "number") { /* padding is number */ }
    ```
2.  **`instanceof` narrowing:** For class instances.
    ```typescript
    if (error instanceof Error) { /* error is Error object */ }
    ```
3.  **`in` operator narrowing:** Check if a property exists on an object. Useful for differentiating object types without a tag.
    ```typescript
    type Fish = { swim: () => void };
    type Bird = { fly: () => void };
    function move(animal: Fish | Bird) {
        if ("swim" in animal) { animal.swim(); } // TS knows it's a Fish
    }
    ```
4.  **Equality narrowing:**
    ```typescript
    function print(msg: string | null) {
        if (msg !== null) { console.log(msg.length); } // TS knows msg is string
    }
    ```
5.  **Truthiness narrowing:** Eliminates `null`, `undefined`, `""`, `0`.
    ```typescript
    function print(msg?: string) {
        if (msg) { console.log(msg.length); } // msg is truthy string
    }
    ```
6.  **Custom Type Predicates (`is` keyword):** Create your own reusable narrowing functions.
    ```typescript
    // Returns boolean at runtime, but tells compiler 'val is string' if true
    function isString(val: unknown): val is string {
        return typeof val === 'string';
    }
    
    const arr: (number | string)[] = [1, "two", 3];
    // filter(Boolean) leaves type as (number|string)[]. filter(isString) narrows it!
    const stringsOnly: string[] = arr.filter(isString); 
    ```
7.  **Assertion Functions:** Functions that throw if a condition is false, narrowing the type for the rest of the scope.
    ```typescript
    function assertUser(obj: any): asserts obj is User {
        if (!obj || typeof obj.id !== 'number') throw new Error("Not a user");
    }
    
    let data: unknown = fetchUser();
    assertUser(data);
    // Down here, TS knows data is User. No if statement needed.
    console.log(data.id); 
    ```

## 5. Generics — Full Deep Dive

Generics provide reusable type parameters. They allow you to write components that work over a variety of types rather than a single one.

### Generic Functions and Interfaces

```typescript
// T is a type parameter capturing the type of the argument
function identity<T>(arg: T): T {
    return arg;
}

// Inference: TS infers T is string
const str = identity("hello"); 

// Generic Interface
interface Container<T> {
    value: T;
}
const numBox: Container<number> = { value: 42 };
```

### Generic Constraints (`extends`)

You can restrict the types that a generic parameter can accept.

```typescript
// T MUST be an object with an 'length' property of type number
function logLength<T extends { length: number }>(arg: T): T {
    console.log(arg.length);
    return arg;
}
logLength("string"); // OK, string has .length
logLength([1, 2, 3]); // OK, array has .length
// logLength(42); // Error, number has no .length
```

### `keyof` and Indexed Access Types

*   `keyof T`: Produces a string union of all public property names of type T.
*   `T[K]`: Looks up the type of property K on type T.

```typescript
interface PersonInfo { name: string; age: number; city: string; }
// type PersonKeys = "name" | "age" | "city"
type PersonKeys = keyof PersonInfo; 

// T is the object, K is a key constrained to be one of T's keys
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
    return obj[key];
}

const user = { name: "Alice", age: 30 };
// infers K="age", returns number
const age = getProperty(user, "age"); 
// getProperty(user, "invalid"); // Error!
```

### `typeof` in Type Position

Extracts the type of a JavaScript value/variable to use in the type system.

```typescript
const defaultTheme = { colors: { primary: 'blue' }, space: 8 };
// Generates the type based on the runtime object structure
type Theme = typeof defaultTheme;
```

### Conditional Types and `infer`

Conditional types form the backbone of advanced TS utilities. Syntax: `T extends U ? X : Y`.

```typescript
type IsString<T> = T extends string ? true : false;
type A = IsString<"hello">; // true
type B = IsString<42>;      // false
```

The `infer` keyword can ONLY be used within the `extends` clause of a conditional type. It tells TS to figure out a type and assign it to a local type variable.

```typescript
// Extract return type of a function
type MyReturnType<T> = T extends (...args: any[]) => infer R ? R : never;

// Extract parameter types as a tuple
type MyParameters<T> = T extends (...args: infer P) => any ? P : never;

// Unwrap a Promise
type UnwrapPromise<T> = T extends Promise<infer U> ? U : T;
```

### Distributive Conditional Types

When a conditional type acts on a generic type parameter, and that parameter is a Union type, it distributes the operation over each member of the union.

```typescript
type ToArray<T> = T extends any ? T[] : never;

// You might expect (string | number)[]
// Because of distribution, it evaluates: (string extends any ? string[] : never) | (number extends any ? number[] : never)
// Result: string[] | number[]
type StrOrNumArr = ToArray<string | number>; 
```

## 6. All Utility Types — With Implementations

TypeScript provides built-in global utility types. Understanding how they are implemented using mapped and conditional types is key to TS mastery.

Let's assume a base interface:
```typescript
interface Todo { title: string; description?: string; completed: boolean; }
```

### Transformation Utilities

*   **`Partial<T>`:** Makes all properties optional.
    *   *Implementation:* `type Partial<T> = { [P in keyof T]?: T[P]; };`
    *   *Usage:* `function updateTodo(todo: Todo, fieldsToUpdate: Partial<Todo>) { ... }`
*   **`Required<T>`:** Removes optional `?` modifiers from all properties.
    *   *Implementation:* `type Required<T> = { [P in keyof T]-?: T[P]; };` (Note the `-?`)
    *   *Usage:* `const fullyPopulatedTodo: Required<Todo> = { title: "x", description: "y", completed: true };`
*   **`Readonly<T>`:** Makes all properties readonly.
    *   *Implementation:* `type Readonly<T> = { readonly [P in keyof T]: T[P]; };`
*   **`Record<K, T>`:** Creates a dictionary type with keys K and values T.
    *   *Implementation:* `type Record<K extends keyof any, T> = { [P in K]: T; };`
    *   *Usage:* `const pages: Record<"home" | "about", {url: string}> = { home: {url: '/'}, about: {url: '/a'} };`

### Extraction Utilities

*   **`Pick<T, K>`:** Creates a new type by picking a subset of properties `K` from `T`.
    *   *Implementation:* `type Pick<T, K extends keyof T> = { [P in K]: T[P]; };`
    *   *Usage:* `type TodoPreview = Pick<Todo, "title" | "completed">;`
*   **`Exclude<T, U>`:** Excludes from union type `T` all members assignable to `U`.
    *   *Implementation:* `type Exclude<T, U> = T extends U ? never : T;`
    *   *Usage:* `type T0 = Exclude<"a" | "b" | "c", "a">; // "b" | "c"`
*   **`Extract<T, U>`:** Extracts from union type `T` all members assignable to `U`.
    *   *Implementation:* `type Extract<T, U> = T extends U ? T : never;`
*   **`Omit<T, K>`:** Creates a type by picking all properties from `T` and then removing `K`.
    *   *Implementation:* `type Omit<T, K extends keyof any> = Pick<T, Exclude<keyof T, K>>;`
    *   *Usage:* `type TodoWithoutDesc = Omit<Todo, "description">;`

### Function and Promise Utilities

*   **`NonNullable<T>`:** Removes null and undefined from a union.
    *   *Implementation:* `type NonNullable<T> = T extends null | undefined ? never : T;`
*   **`ReturnType<T>`:** Extracts the return type of a function type. (Implemented via `infer`, see above).
*   **`Parameters<T>`:** Extracts the parameter types of a function type into a tuple. (Implemented via `infer`).
*   **`Awaited<T>`:** Recursively unwraps Promises (e.g., `Promise<Promise<string>>` becomes `string`).

## 7. Mapped Types

Mapped types allow you to create new types by iterating over the keys of an existing type. Syntax: `{ [Key in UnionType]: ValueType }`.

### Adding/Removing Modifiers

You can use `+` or `-` to add or remove `readonly` and `?` modifiers.

```typescript
type Mutable<T> = {
    -readonly [P in keyof T]: T[P]
};

type Concrete<T> = {
    [P in keyof T]-?: T[P] // Same as Required<T>
};
```

### Key Remapping with `as`

You can change the names of keys while mapping over them using the `as` clause.

```typescript
interface DataStore { user: string; session: string; }

// Generate getter method signatures
type Getters<T> = {
    [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K]
};
// Result: { getUser: () => string; getSession: () => string; }
type StoreGetters = Getters<DataStore>; 
```

### Filtering Keys with `as never`

If you remap a key to `never`, it is completely removed from the resulting type. This is incredibly powerful for filtering object properties based on their value types.

```typescript
interface MixedData { id: number; name: string; isActive: boolean; tag: string; }

// Extract only properties whose values are strings
type OnlyStrings<T> = {
    [K in keyof T as T[K] extends string ? K : never]: T[K]
};
// Result: { name: string; tag: string; }
type StringData = OnlyStrings<MixedData>;
```

## 8. Template Literal Types

Template literal types bring the power of JS template strings to the type level, allowing you to manipulate strings and create dynamic types.

```typescript
type World = "world";
type Greeting = `hello ${World}`; // "hello world"
```

TypeScript provides intrinsic string manipulation types: `Uppercase<S>`, `Lowercase<S>`, `Capitalize<S>`, `Uncapitalize<S>`.

### Building Typed Event Systems

A common real-world use case is typing event emitters dynamically based on a state object.

```typescript
type State = {
    username: string;
    avatarUrl: string;
    theme: 'dark' | 'light';
};

// Generate event names: "usernameChanged" | "avatarUrlChanged" | "themeChanged"
type StateEventName = `${keyof State}Changed`;

// Create a callback registry type dynamically
type EventRegistry<T> = {
    [K in keyof T as `${string & K}Changed`]?: (newValue: T[K]) => void;
};

// Result: { usernameChanged?: (val: string) => void; themeChanged?: (val: 'dark'|'light') => void; ... }
type Handlers = EventRegistry<State>;
```

## 9. `tsconfig.json` Deep Dive

The `tsconfig.json` file dictates how the compiler behaves. A misconfigured tsconfig leads to a poor developer experience and unsafe code.

### The `strict` Flag Family

Setting `"strict": true` is non-negotiable for modern TypeScript. It enables a suite of flags:
*   `strictNullChecks`: `null`/`undefined` are distinct types. Prevents "Cannot read property of undefined".
*   `noImplicitAny`: Errors if TS cannot infer a type and defaults to `any`.
*   `strictFunctionTypes`: Ensures function arguments are checked contravariantly (safe).
*   `strictBindCallApply`: Validates arguments to `.call`, `.bind`, `.apply`.
*   `strictPropertyInitialization`: Class properties must be initialized in the constructor or where declared.
*   `noImplicitThis`: Errors if `this` has an implicit `any` type (e.g., detached callbacks).

### Target, Lib, and Module

These three are often confused but manage entirely different things.

*   **`target`**: Controls the *JavaScript syntax version* emitted by tsc (e.g., `ES5`, `ES2015`, `ES2022`). If your target is ES5, TS will downcompile arrow functions and classes to `var` and `function`.
*   **`lib`**: Controls the *global type definitions* available during development. For example, if you are writing for the browser, you need `"DOM"`. If you use modern features like `Array.prototype.flat`, you need `"ES2019"` or `"ESNext"`. You can target ES5 output but use ES2022 types if you provide polyfills.
*   **`module`**: Controls the *module system* of the emitted JavaScript (`CommonJS`, `ESNext`, `NodeNext`).
*   **`moduleResolution`**: Tells TS how to look up imported files.
    *   `node` (legacy): Looks for `index.js`, `node_modules`, doesn't require extensions.
    *   `nodenext` / `node16`: Strict ESM resolution. Requires explicit `.js` extensions in imports (even when importing `.ts` files!).
    *   `bundler`: The standard for projects using Vite, Webpack, esbuild. Allows extensionless imports but assumes the bundler will handle the actual resolution.

### Crucial Advanced Flags

*   **`isolatedModules: true`**: Required if you use a faster transpiler like SWC, Babel, or esbuild instead of `tsc` to emit JS. It ensures you don't use features that require whole-program analysis (like `const enum` or namespaces), which single-file transpilers can't handle.
*   **`paths` + `baseUrl`**: Used to configure module aliases (e.g., importing from `@/components/Button` instead of `../../../components/Button`). Must be mirrored in your bundler config.
*   **`declaration: true`**: Tells `tsc` to generate `.d.ts` definition files. Essential if you are building a library for others to consume.
*   **`skipLibCheck: true`**: Skips type checking of all `.d.ts` files (usually in `node_modules`). Dramatically speeds up compilation time. Standard for application development.
*   **`noUncheckedIndexedAccess: true`**: Highly recommended. If you access an array `arr[0]` or dictionary `dict["key"]`, TS normally returns `T`. With this flag, it returns `T | undefined`, forcing you to check if the element actually exists.
*   **`exactOptionalPropertyTypes: true`**: By default, `{ a?: string }` allows `obj.a = undefined`. With this flag, the property can either be a `string` or be omitted entirely from the object, but explicitly setting it to `undefined` is an error.

## 10. Advanced TypeScript Patterns

### The `satisfies` Operator (TS 4.9+)

Historically, adding a type annotation `const p: Type = ...` widens the inferred type of the object to match the generic `Type`. The `satisfies` operator allows you to validate that an expression matches a type, **without changing the resulting inferred type**.

```typescript
type ColorRecord = Record<string, string | [number, number, number]>;

// Using annotation: Widens properties.
const badPalette: ColorRecord = {
    red: [255, 0, 0],
    green: "#00ff00"
};
// badPalette.red[0]; // Error: Object is of type 'string | [number, number, number]'

// Using satisfies: Validates, but keeps exact literal types!
const goodPalette = {
    red: [255, 0, 0],
    green: "#00ff00"
} satisfies ColorRecord;

goodPalette.red[0]; // OK! TS knows red is exactly a tuple of numbers.
goodPalette.green.toUpperCase(); // OK! TS knows green is exactly a string.
// goodPalette.blue; // Validation works: throws error if missing required keys etc.
```

### Branded Types (Opaque Types)

TypeScript's structural typing is great, but sometimes you want nominal typing to prevent mixing up identical structures (like a User ID and an Order ID, which are both just strings). Branded types solve this using intersection with a unique symbol.

```typescript
// Define the brands
type UserId = string & { readonly __brand: unique symbol };
type OrderId = string & { readonly __brand: unique symbol };

// Factory functions to create them
function createUserId(id: string): UserId { return id as UserId; }
function createOrderId(id: string): OrderId { return id as OrderId; }

const uid = createUserId("user-123");
const oid = createOrderId("order-456");

function fetchUser(id: UserId) { /* ... */ }

fetchUser(uid); // OK
// fetchUser(oid); // Error! Argument of type 'OrderId' is not assignable to 'UserId'
// fetchUser("user-123"); // Error! Raw string is not a UserId
```

### Variance: Covariance and Contravariance

Variance describes how complex types relate based on the relationship of their generic parameters.

*   **Covariance (Read-only positions, Return types):** A `Dog` is an `Animal`. Therefore, a `List<Dog>` can be used where a `List<Animal>` is expected (if the list is read-only). The complex type varies in the *same* direction as the type parameter.
*   **Contravariance (Write-only positions, Parameters):** Function arguments are contravariant under `strictFunctionTypes`. If you need a function that handles `Dog`s, you can safely pass a function that knows how to handle *any* `Animal`. The complex type varies in the *opposite* direction.

```typescript
class Animal { name: string; }
class Dog extends Animal { breed: string; }

type AnimalHandler = (a: Animal) => void;
type DogHandler = (d: Dog) => void;

let handleAnimal: AnimalHandler = (a) => console.log(a.name);
let handleDog: DogHandler = (d) => console.log(d.breed);

// Contravariance in action:
// It is SAFE to assign handleAnimal to handleDog.
// When called, handleDog is guaranteed to be given a Dog.
// handleAnimal knows how to handle any Animal, so handling a Dog is fine.
handleDog = handleAnimal; // OK

// It is UNSAFE to assign handleDog to handleAnimal.
// handleAnimal might be called with a generic Animal (or a Cat).
// handleDog requires a Dog (specifically, the 'breed' property). Crash!
// handleAnimal = handleDog; // Error with strictFunctionTypes
```

### Declaration Merging

In TypeScript, you can define interfaces or namespaces with the same name multiple times, and the compiler will merge them into a single definition.

```typescript
interface User { name: string; }
interface User { age: number; }
// Result: interface User { name: string; age: number; }
```

### Global Augmentation

This is crucial for typing global variables or extending types from third-party libraries (like adding custom properties to the Express Request object or the global `Window`).

```typescript
// Extend the global Window object
declare global {
    interface Window {
        myCustomProp: string;
        __REDUX_DEVTOOLS_EXTENSION__?: Function;
    }
}

// Ensure the file is treated as a module, not a script
export {}; 

// Now usage is type-safe anywhere in the project
window.myCustomProp = "hello";
```

This concludes the TypeScript deep dive. Combining structural typing, advanced generic utilities, and strict configuration forms the basis of truly scalable and type-safe architecture.
