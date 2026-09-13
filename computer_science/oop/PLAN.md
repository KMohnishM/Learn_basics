# OOP Curriculum — Implementation Plan

> **Status**: Approved. Ready for execution.  
> **Branch**: `cn-os` → will be merged to `main` after completion.  
> **Languages**: C++ (vtable / memory internals) + Java (idiomatic OOP, interface/abstract, common in SDE interviews)  
> **Format**: `README.md` (theory) + `QnA.md` (Easy / Medium / Hard) + `CHEATSHEET.md` (one-pager)

---

## Directory Structure

```
oop/
├── README.md                                        ← Root: curriculum map, study order, interview frequency
├── 01_classes_objects/
│   ├── README.md
│   ├── QnA.md
│   └── CHEATSHEET.md
├── 02_encapsulation_abstraction/
│   ├── README.md
│   ├── QnA.md
│   └── CHEATSHEET.md
├── 03_inheritance/
│   ├── README.md
│   ├── QnA.md
│   └── CHEATSHEET.md
├── 04_polymorphism/
│   ├── README.md
│   ├── QnA.md
│   └── CHEATSHEET.md
├── 05_solid_principles/
│   ├── README.md
│   ├── QnA.md
│   └── CHEATSHEET.md
├── 06_design_patterns_creational/
│   ├── README.md
│   ├── QnA.md
│   └── CHEATSHEET.md
├── 07_design_patterns_structural_behavioral/
│   ├── README.md
│   ├── QnA.md
│   └── CHEATSHEET.md
└── 08_oop_design_interviews/
    ├── README.md
    ├── QnA.md
    └── CHEATSHEET.md
```

---

## Language Strategy

| Language | Used For |
|----------|----------|
| **C++** | Memory layout, vtable/vPtr internals, rule of three/five, `new`/`delete`, `virtual`, casts (`dynamic_cast`), multiple inheritance with virtual base classes |
| **Java** | Interface vs abstract class syntax, `@Override`, `final`, generics, design patterns (idiomatic SDE interview style), `instanceof`, access modifiers |

Both languages shown side-by-side where the concept differs meaningfully between them.

---

## Module 1: Classes & Objects

### README.md Topics
- Class vs Object: definition, instantiation lifecycle, object identity
- Constructors: default, parameterized, copy constructor (C++) / copy via clone (Java)
- Destructors (C++) vs Garbage Collector (Java): RAII pattern and why C++ needs explicit cleanup
- `this` pointer/reference: what it is, when needed, method chaining
- Instance variables vs class/static variables — memory location difference
- Memory layout: stack vs heap allocation
  - C++: stack objects vs `new` on heap, RAII with destructors
  - Java: all objects on heap; primitives on stack
- `sizeof` a C++ class: data members + alignment padding rules
- C++ struct vs class (default access specifier only difference)
- Java: `Object` as root of all classes; `equals()`, `hashCode()`, `toString()`
- Python note: `@classmethod` vs `@staticmethod` vs instance method
- Rule of Three (C++): if you define destructor/copy constructor/copy assignment, define all three
- Rule of Five (C++11): extend with move constructor and move assignment
- Java: no manual memory; `Cloneable` / `clone()` for copy semantics

### QnA.md
- 🟢 What is the difference between a class and an object?
- 🟢 What is a copy constructor? When is it automatically invoked in C++?
- 🟢 What is the `this` pointer/reference? Can it be null (C++)? Can it be null in Java?
- 🟡 What is RAII? Why does Java not need it?
- 🟡 What is the rule of three in C++? What does the rule of five add?
- 🟡 Why does `sizeof(EmptyClass)` return 1 in C++ but not 0?
- 🔴 Trace the constructor and destructor call order for a derived class object (C++)
- 🔴 Implement a deep-copy class in both C++ (copy constructor) and Java (`clone()`)

### CHEATSHEET.md
- Constructor types summary table (C++ vs Java)
- Rule of three / rule of five quick ref
- Stack vs heap allocation diagram (C++ vs Java)
- `this` usage patterns

---

## Module 2: Encapsulation & Abstraction

### README.md Topics
- Encapsulation: bundling data + behaviour, enforcing invariants via access control
- Access specifiers:
  - C++: `private`, `protected`, `public`
  - Java: `private`, `protected`, `public`, package-private (default — no keyword)
- Getters/Setters: when helpful, when they *break* encapsulation (Law of Demeter)
- Abstraction: hiding *how*, exposing *what*; reduces cognitive load for consumers
- Abstract classes:
  - C++: at least one pure virtual function (`= 0`); cannot instantiate
  - Java: `abstract` keyword on class + `abstract` on methods; can have concrete methods and state
- Interfaces:
  - C++: pure abstract class (all `= 0`, no state)
  - Java: `interface` keyword; `default` methods (Java 8+); `static` methods; no instance state
- Interface vs Abstract class decision:
  - Abstract class: shared code + IS-A relationship
  - Interface: contract only, supports multiple implementation (Java's workaround for no multiple inheritance)
- Java's multiple interface implementation: `class Foo implements IBar, IBaz`
- C++ multiple inheritance as interface: inherit from multiple pure abstract classes
- Friend functions / friend classes in C++ (escape hatch — justified uses)

### QnA.md
- 🟢 What is encapsulation? Why does it matter?
- 🟢 What are the access specifiers in C++ vs Java? What is Java's package-private?
- 🟢 What is the difference between abstraction and encapsulation?
- 🟡 Abstract class vs Interface — compare in both C++ and Java
- 🟡 What is the Law of Demeter? Code example of a violation
- 🟡 Why can Java classes implement multiple interfaces but not extend multiple classes?
- 🔴 Design a `Shape` abstract hierarchy with `area()` and `perimeter()` in both C++ and Java
- 🔴 When do getters/setters make encapsulation *worse*? Show a real counter-example

### CHEATSHEET.md
- Access specifier comparison table (C++ vs Java)
- Abstract class template (C++ and Java side-by-side)
- Interface template (C++ pure abstract + Java interface)
- Interface vs Abstract class decision tree

---

## Module 3: Inheritance

### README.md Topics
- IS-A vs HAS-A relationships
- Types of inheritance: Single, Multilevel, Hierarchical, Multiple, Hybrid
- C++ inheritance access modifiers: `public`, `protected`, `private` — what each changes about visibility in derived class
- Java: `extends` (single class only), `implements` (multiple interfaces)
- Constructor chaining:
  - C++: base constructor called before derived body; initializer list
  - Java: `super()` must be first statement in derived constructor
- Method Resolution Order (MRO):
  - Python: C3 linearization algorithm (shown for completeness)
  - Java: no MRO problem — single inheritance only
  - C++: left-to-right DFS by default (ambiguous with diamond)
- Diamond problem:
  - C++: virtual base classes (`virtual` keyword on base) — shared single copy
  - Java: not possible with classes (single inheritance); interfaces handle via `default` with explicit override
- Covariant return types: C++ and Java both support (overriding method may return more-derived type)
- `final` in Java: class cannot be extended; method cannot be overridden
- `final` in C++11: `final` specifier on class or virtual method
- Composition over Inheritance: flexibility, avoids fragile base class problem

### QnA.md
- 🟢 What is inheritance? What is the IS-A vs HAS-A distinction?
- 🟢 What are the types of inheritance? Which does Java support natively?
- 🟢 Trace the constructor call order when a derived class object is constructed (C++ and Java)
- 🟡 What is the diamond problem? How does C++ solve it? How does Java avoid it?
- 🟡 What is private inheritance in C++? How does it differ from public inheritance?
- 🟡 What does `final` do in Java? In C++?
- 🔴 C++ diamond problem trace: two parent classes both inherit from `Animal` — show ambiguity and fix with `virtual`
- 🔴 Refactor an inheritance-based design to use composition — justify the change

### CHEATSHEET.md
- Inheritance types diagram
- C++ virtual base class syntax
- Java `extends` vs `implements` syntax
- Constructor chaining rules (C++ vs Java)
- Composition vs Inheritance trade-off table

---

## Module 4: Polymorphism

### README.md Topics
- Compile-time (Static) Polymorphism:
  - Function/method overloading: same name, different signatures
  - Operator overloading: C++ (`+`, `==`, `<<`); Java does not support operator overloading
  - Templates (C++) / Generics (Java): parametric polymorphism at compile time
- Runtime (Dynamic) Polymorphism:
  - Method overriding: derived redefines base method
  - C++: `virtual` keyword required; Java: all non-static, non-final, non-private methods are virtual by default
  - **vTable internals (C++)**: per-class hidden array of function pointers built by the compiler
  - **vPtr (C++)**: hidden 8-byte pointer stored in every polymorphic object, set at construction
  - Java's vtable equivalent: the JVM uses its own internal dispatch table per class
  - Memory overhead: +1 pointer per object (8 bytes on 64-bit) for any class with virtual functions in C++
  - `@Override` annotation in Java: compile-time verification (not `virtual`)
  - `override` and `final` specifiers in C++11
- Object Slicing (C++ only): assigning derived to base by value loses derived members — use pointers/references
- Virtual Destructor:
  - C++: MUST declare in polymorphic base, else `delete base_ptr` = undefined behaviour
  - Java: destructors don't exist; GC handles; `finalize()` deprecated
- Cast operators:
  - C++: `dynamic_cast` (safe, RTTI), `static_cast`, `reinterpret_cast`, `const_cast`
  - Java: `(Type)` cast + `instanceof` check; `ClassCastException` at runtime if wrong
- Early binding (compile-time) vs late binding (runtime)

### QnA.md
- 🟢 What is the difference between overloading and overriding?
- 🟢 What makes a function virtual in C++? What about in Java?
- 🟢 What is object slicing? Why doesn't it happen in Java?
- 🟡 Explain the vTable and vPtr mechanism in C++ — how many vTables in a hierarchy?
- 🟡 Why must the base class destructor be virtual in C++ polymorphic hierarchies?
- 🟡 What does `@Override` do in Java? What happens if you omit it?
- 🔴 Calculate the memory layout of a C++ class hierarchy with virtual functions and padding
- 🔴 Trace `base_ptr->virtualMethod()` through the vTable at runtime (C++) step-by-step

### CHEATSHEET.md
- vTable/vPtr diagram (C++)
- Overloading vs Overriding comparison table
- C++ cast types quick ref (`dynamic_cast` / `static_cast` / `reinterpret_cast`)
- Java cast + `instanceof` pattern
- Virtual destructor rule
- Object slicing illustration

---

## Module 5: SOLID Principles

### README.md Topics (each principle: definition + violation code + fixed code in Java and/or C++)

- **S — Single Responsibility Principle (SRP)**
  - "A class should have one and only one reason to change"
  - Violation: `User` class with `saveToDatabase()` + `sendWelcomeEmail()` + `calculateDiscount()`
  - Fix: split into `User`, `UserRepository`, `EmailService`, `PricingService`

- **O — Open/Closed Principle (OCP)**
  - "Open for extension, closed for modification"
  - Violation: `if/else if` chain in `AreaCalculator` for each shape type
  - Fix: `Shape` interface with `area()` — each shape implements it; calculator never changes

- **L — Liskov Substitution Principle (LSP)**
  - "Objects of subtypes must be substitutable for objects of their base type"
  - Violation: `Square extends Rectangle` — `setWidth()` breaks `Rectangle`'s invariant
  - Formal rule: preconditions cannot be strengthened; postconditions cannot be weakened; invariants preserved
  - Fix: `Square` and `Rectangle` both implement `Shape` independently

- **I — Interface Segregation Principle (ISP)**
  - "No client should be forced to depend on methods it does not use"
  - Violation: `IWorker` interface with `work()` + `eat()` applied to `RobotWorker`
  - Fix: split into `IWorkable` and `IFeedable`

- **D — Dependency Inversion Principle (DIP)**
  - "High-level modules should not depend on low-level modules; both depend on abstractions"
  - Violation: `OrderService` directly instantiates `MySQLDatabase`
  - Fix: `OrderService` depends on `IDatabase` interface; inject concrete impl externally
  - DI types: Constructor injection (preferred), Setter injection, Method injection
  - IoC containers: Spring (Java), Boost.DI (C++)

### QnA.md
- 🟢 State all 5 SOLID principles in one sentence each
- 🟢 What is SRP? Give a violation and its fix with code
- 🟡 LSP — why does `Square extends Rectangle` violate it? Show the invariant break
- 🟡 What is the difference between DIP and Dependency Injection?
- 🟡 How do you implement OCP without modifying existing classes?
- 🔴 Given a "god class" implementation — identify all SOLID violations and refactor it
- 🔴 Design a notification system (Email / SMS / Push) satisfying OCP, ISP, and DIP

### CHEATSHEET.md
- One-liner definition per principle
- Violation → Fix pattern per principle
- DI types quick ref
- SRP smell checklist

---

## Module 6: Design Patterns — Creational

### README.md Topics

- GoF overview: 23 patterns across Creational / Structural / Behavioral

- **Singleton**
  - Intent: one instance, global access point
  - Naive (not thread-safe) → Thread-safe with `std::mutex` double-checked locking (C++) → `std::call_once` (C++11 preferred)
  - Java: `enum` Singleton (Josh Bloch's approach — thread-safe, serialization-safe) vs `synchronized getInstance()` vs `volatile` double-checked
  - Testing problem: global state, hard to mock → prefer Dependency Injection over Singleton

- **Factory Method**
  - Intent: define interface for creation; subclasses decide which class to instantiate
  - Creator + ConcreteCreator; Product + ConcreteProduct
  - Java: `interface` + `static` factory methods (modern idiom)
  - C++: virtual factory method

- **Abstract Factory**
  - Intent: create families of related objects without specifying concrete classes
  - Factory of Factories; example: cross-platform UI (Windows/Mac `Button` + `Checkbox` families)
  - vs Factory Method: single product vs family of products

- **Builder**
  - Intent: construct complex objects step-by-step; avoids telescoping constructors
  - Java: inner `Builder` class with fluent `setX().setY().build()` chain
  - C++: same fluent interface; `std::optional` for optional fields
  - Director pattern: orchestrates build sequence

- **Prototype**
  - Intent: clone existing objects when construction is expensive or class is runtime-specified
  - C++: copy constructor + `clone()` virtual method
  - Java: `Cloneable` interface + `clone()` override (or copy constructor — preferred)

### QnA.md
- 🟢 What is the Singleton pattern? When would you use it? When should you avoid it?
- 🟢 What is the Factory Method pattern?
- 🟡 Factory Method vs Abstract Factory vs Builder — when to use each?
- 🟡 What is the telescoping constructor anti-pattern? How does Builder solve it?
- 🟡 How do you make Singleton thread-safe? Compare C++ and Java approaches
- 🔴 Implement thread-safe Singleton in C++ (`std::call_once`) and Java (enum approach)
- 🔴 Design an Abstract Factory for a cross-platform UI toolkit (Windows / Mac)

### CHEATSHEET.md
- Pattern intent + when-to-use table (all 5 patterns)
- Singleton variants comparison (naive / locked / `call_once` / Java enum)
- Factory vs Abstract Factory vs Builder decision flowchart

---

## Module 7: Design Patterns — Structural & Behavioral

### README.md Topics

**Structural Patterns:**
- **Adapter**: convert one interface into another; class adapter (C++ multiple inheritance) vs object adapter (composition — both languages)
- **Decorator**: attach responsibilities dynamically without subclassing; stackable wrappers; Java `BufferedInputStream` is a real-world Decorator
- **Facade**: simplified unified interface to complex subsystem (e.g., `HomeTheaterFacade` wrapping `DVD`, `Amplifier`, `Projector`)
- **Proxy**: surrogate object; types: Virtual Proxy (lazy loading), Protection Proxy (access control), Remote Proxy (network/RMI)

**Behavioral Patterns:**
- **Observer (Pub/Sub)**: Subject maintains list of observers; notifies all on state change; loose coupling; Java `java.util.Observer` (legacy) vs custom event listener
- **Strategy**: family of interchangeable algorithms; OCP-compliant; Java `Comparator<T>` is a real-world Strategy
- **Command**: encapsulate request as object; enables undo, queue, logging; `execute()` + `undo()` methods
- **Iterator**: traverse collection without exposing internals; Java `Iterator<T>` interface; C++ range-based for / `begin()`/`end()`

### QnA.md
- 🟢 What is the Observer pattern? Give a real-world use case
- 🟢 What is the Strategy pattern? How is it better than if/else?
- 🟡 Adapter vs Facade — when to use each?
- 🟡 Decorator vs Inheritance for adding functionality — trade-offs?
- 🟡 Name two types of Proxy and their use cases
- 🔴 Implement Observer for a stock price notification system (Java)
- 🔴 Use Decorator to add logging + caching to a database query object (C++ or Java)

### CHEATSHEET.md
- All 8 patterns: intent + 1-line use case
- Observer vs Command vs Strategy comparison table
- Structural pattern decision guide (when to use Adapter vs Facade vs Proxy vs Decorator)

---

## Module 8: OOP Design Interviews

### README.md Topics
- OOAD process: Requirements → Identify Nouns (classes) → Identify Verbs (methods/responsibilities) → Define Relationships
- CRC (Class-Responsibility-Collaborator) cards
- UML class diagram notation: attributes, methods, association, aggregation, composition, inheritance, realization
- Aggregation vs Composition: "uses" vs "owns" (lifecycle dependency)
- 5-step interview framework:
  1. Clarify requirements (ask questions, don't assume)
  2. Identify core entities (nouns → classes)
  3. Define relationships (IS-A, HAS-A, USES-A)
  4. Apply design patterns where appropriate
  5. Walk through a scenario end-to-end

**Full Design Walkthroughs (class diagram + Java code skeleton):**

1. **Parking Lot**
   - Classes: `ParkingLot`, `ParkingFloor`, `ParkingSpot` (Compact/Large/Handicapped), `Vehicle` (Car/Truck/Motorcycle), `Ticket`, `ParkingRate` (Strategy), `EntrancePanel`, `ExitPanel`
   - Patterns used: Strategy (rate calculation), Singleton (ParkingLot instance)

2. **Library Management System**
   - Classes: `Library`, `BookItem`, `Book`, `Member`, `Librarian`, `BookLending`, `Reservation`, `Search` interface (Strategy: by title/author/ISBN)
   - Patterns used: Strategy (search), Observer (reservation notification), Factory (search type)

3. **Snake and Ladder Game**
   - Classes: `Board`, `Cell`, `Snake` (has `start` + `end` cells), `Ladder`, `Player`, `Dice`, `Game`
   - Key design: `Board` as array of `Cell`; `Cell` has optional `Jump` (polymorphic Snake/Ladder)

4. **ATM System**
   - Classes: `ATM`, `ATMState` interface → states: `IdleState`, `HasCardState`, `AuthenticationState`, `SelectingTransactionState`, `DispensingState`; `Card`, `Account`, `BankServer`, `CashDispenser`, `Keypad`, `Display`
   - Patterns used: State pattern (ATM state machine), Singleton (ATM)

### QnA.md
- 🟢 Aggregation vs Composition — what is the difference? Give a UML example
- 🟢 Walk me through your process when asked an OOP design question in an interview
- 🟡 Design a Parking Lot — identify the core classes and their relationships
- 🟡 How would you model the Library and Books relationship in UML?
- 🔴 Full design: ATM System — all classes, relationships, and State pattern implementation
- 🔴 Full design: Hotel Management System with room booking, billing, and staff

### CHEATSHEET.md
- 5-step interview framework card
- UML notation quick reference
- Aggregation vs Composition table
- Common OOP interview pattern → design pattern mapping

---

## Execution Notes

- Each module README targets **300–500 lines** of detailed theory with code snippets
- QnA: 3 easy + 2–3 medium + 2 hard questions per module
- CHEATSHEET: max 1 page (60–80 lines) — dense, no fluff
- All code examples shown in **both C++ and Java** where the syntax meaningfully differs
- No Docker labs — all examples are inline, self-contained snippets
