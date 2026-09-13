# Module 2 Questions and Answers

### 1. What is the difference between any, unknown, never, and void? When would you use each?
- `any`: Disables type checking entirely. Use as a last resort when migrating legacy JS or when type definitions are impossible to write.
- `unknown`: A type-safe counterpart to `any`. You can assign anything to it, but you cannot perform operations on it without narrowing the type first (e.g., using `typeof`). Use for parsing external JSON payloads.
- `never`: Represents values that never occur. Used as the return type for functions that always throw an error or contain infinite loops, and used in exhaustive type checking (switch statements).
- `void`: Represents the absence of a return value in functions (like functions that only produce side effects).

### 2. Explain TypeScript's structural typing. How does it differ from nominal typing?
TypeScript uses structural typing (often called "duck typing"). This means that two types are considered compatible if their structure (shape/properties) matches, regardless of their names or declarations.
Nominal typing (used in languages like Java or C#) requires explicit declarations. Two classes with identical structures are not compatible unless one explicitly inherits from the other or implements the same interface.

### 3. What are discriminated unions? Give a real-world example.
Discriminated unions are a pattern where a union type shares a common, literal property (the "discriminant"). This allows TypeScript to narrow the type securely.
```typescript
type APIResponse = 
  | { status: "success"; data: any }
  | { status: "error"; errorMessage: string };

function handle(response: APIResponse) {
  if (response.status === "success") {
    console.log(response.data); // Type narrowed
  } else {
    console.log(response.errorMessage);
  }
}
```

### 4. Implement the ReturnType<T> utility type from scratch using conditional types and infer.
```typescript
type MyReturnType<T extends (...args: any) => any> = T extends (...args: any) => infer R ? R : any;
```
It constraints `T` to be a function. Then, it uses a conditional type to check if `T` matches a function signature. If it does, it uses `infer R` to extract the return type and returns `R`.

### 5. What is the difference between Pick<T,K> and Omit<T,K>? When would you use each?
- `Pick<T, K>` creates a new type by selecting a specific subset of properties `K` from type `T`. Use it when you want a small explicit subset of a large type.
- `Omit<T, K>` creates a new type by removing a specific subset of properties `K` from type `T`. Use it when you want most of the type but need to remove a few specific properties (like removing sensitive fields from a User type).

### 6. Explain generic constraints (extends). Give an example of a function that only accepts objects with an id field.
Generic constraints limit the kinds of types that can be passed to a generic parameter.
```typescript
function printId<T extends { id: string | number }>(obj: T) {
  console.log(obj.id);
}
```

### 7. What does strict: true in tsconfig enable? Why should you always use it?
`strict: true` is a macro flag that enables a suite of rigorous type-checking options, including `strictNullChecks`, `noImplicitAny`, `strictFunctionTypes`, and `strictBindCallApply`. You should always use it because it forces you to handle null/undefined cases explicitly and prevents fallback to `any`, eliminating entire classes of runtime errors.

### 8. What is a mapped type? Write a mapped type that makes all properties in an object readonly and optional.
A mapped type iterates over keys to create a new type.
```typescript
type ReadonlyAndOptional<T> = {
  readonly [P in keyof T]?: T[P];
};
```

### 9. What are template literal types? Give an example of using them to build a typed event system.
Template literal types allow string manipulation at the type level.
```typescript
type EventType = "click" | "hover";
type EventName = `on${Capitalize<EventType>}`; // "onClick" | "onHover"
```

### 10. What is the satisfies operator and how does it differ from a type annotation?
The `satisfies` operator (added in TS 4.9) allows you to validate that an expression matches a type without widening its inferred type.
```typescript
const colors = {
  red: "#FF0000",
  blue: [0, 0, 255]
} satisfies Record<string, string | number[]>;
// colors.red is inferred strictly as a string, not (string | number[])
```

### 11. What is type narrowing? Explain how discriminated unions enable exhaustive checking.
Type narrowing is the process of refining a broad type to a more specific one (e.g., using `if (typeof x === "string")`).
With discriminated unions, you can use a `switch` statement on the discriminant property. By assigning the unhandled case to a variable of type `never`, TypeScript will throw a compile error if you add a new union member but forget to update the switch statement.

### 12. What are branded types and why would you use them in production code?
Branded types simulate nominal typing to prevent mixing up structurally identical types (like UserID and OrderID which are both strings).
```typescript
type UserId = string & { __brand: "UserId" };
type OrderId = string & { __brand: "OrderId" };
```
This ensures a function expecting a `UserId` cannot accidentally be passed an `OrderId`, improving safety in large codebases.

### 13. What is the difference between interface and type in TypeScript? When would you prefer one over the other?
- `interface` is specifically for declaring object shapes. Interfaces can be merged (declaration merging).
- `type` aliases can represent any type (primitives, unions, intersections, tuples, object shapes).
Prefer `interface` for public APIs or objects meant to be extended. Prefer `type` aliases for complex unions, mapped types, or conditional types.

### 14. How does TypeScript's moduleResolution: node16 differ from the legacy node mode? Why does it matter for ESM?
Legacy `node` resolution assumes CommonJS rules (e.g., omitting `.js` extensions). `node16` or `nodenext` accurately implements Node.js's dual ESM/CJS resolution algorithm. It forces you to include explicit file extensions (e.g., `import { foo } from "./foo.js"`) and respects `package.json` `exports` fields, which is mandatory for modern ESM compatibility.

### 15. Explain the infer keyword. Implement a FirstArgument<T> type that extracts the first parameter type of a function.
The `infer` keyword is used within the `extends` clause of a conditional type to declare a new type variable that TypeScript will deduce from the structure being checked.
```typescript
type FirstArgument<T> = T extends (arg1: infer A, ...rest: any[]) => any ? A : never;
```
