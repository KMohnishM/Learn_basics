# SOLID Principles Cheat Sheet

## 📝 1. Quick Definitions
| Principle | Acronym | One-Liner Definition |
| :--- | :--- | :--- |
| **Single Responsibility** | SRP | A class should have one and only one reason to change. |
| **Open/Closed** | OCP | Software entities should be open for extension, closed for modification. |
| **Liskov Substitution** | LSP | Subtypes must be substitutable for their supertypes without altering correctness. |
| **Interface Segregation** | ISP | No client should be forced to depend on methods it does not use. |
| **Dependency Inversion** | DIP | High-level modules should depend on abstractions, not low-level details. |

---

## 🛠️ 2. Violation → Fix Patterns

| Principle | Classic Violation | The Fix |
| :--- | :--- | :--- |
| **SRP** | `User` class formats strings, saves to DB, and sends emails. | Split into `User` (data), `UserRepository` (DB), `EmailService` (email). |
| **OCP** | Huge `if-else` block checking object type to determine behavior. | Extract an interface with the behavior. Call it polymorphically. |
| **LSP** | `Square extends Rectangle`, breaking `Rectangle` invariant on setters. | Both implement `Shape` independently. No inheritance. |
| **ISP** | `IWorker` requires `eat()` and `sleep()`; `Robot` throws exceptions. | Split into `IWorkable`, `IFeedable`, `ISleepable`. |
| **DIP** | `new MySQLDatabase()` hardcoded inside `OrderService`. | `OrderService` depends on `IDatabase`. Inject concrete DB at runtime. |

---

## 💉 3. Dependency Injection (DI) Types
*(Mechanisms to fulfill the Dependency Inversion Principle)*

* **Constructor Injection (Best Practice):** Dependencies passed via the class constructor. (Ensures fully initialized, immutable state).
* **Setter Injection:** Dependencies passed via `setDependency(Dep d)` methods. (Useful for optional or circular dependencies).
* **Method Injection:** Dependency passed directly as an argument to the specific method that needs it.

---

## 👃 4. SRP "Smell" Checklist
If your class exhibits any of the following, it likely violates SRP:
* It has multiple "axes of change" (e.g., changes to DB schema and UI formatting).
* The class name or description relies heavily on the word "and".
* Low cohesion: Methods operate on entirely isolated subsets of fields.
* The class exceeds a reasonable size (e.g., God class).
* Changes requested by different business stakeholders require touching the same file.

---

## 📜 5. LSP Formal Rules
To safely extend a base class without breaking the program, a subclass must obey:
* **Preconditions cannot be strengthened:** You cannot require stricter input rules than the parent class.
* **Postconditions cannot be weakened:** You cannot promise less strict output/state guarantees than the parent class.
* **Invariants must be preserved:** Any fundamental structural/logical rules of the parent must remain true in the child.
