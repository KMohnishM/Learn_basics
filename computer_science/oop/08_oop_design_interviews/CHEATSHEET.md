# CHEATSHEET: OOD Interviews

### 1. 5-Step Interview Framework
1. **Clarify (2-3 mins):** Ask about scope, scale, actors, workflows, and constraints.
2. **Identify Core Entities:** List 5-8 primary nouns (classes).
3. **Define Relationships:** Map IS-A and HAS-A relationships.
4. **Apply Patterns:** Identify standard design patterns that naturally fit.
5. **Walkthrough:** Trace a primary use case end-to-end to validate the design.

---

### 2. UML Relationship Notation Quick Reference

| Name | Symbol / Notation | Meaning | Example |
| :--- | :--- | :--- | :--- |
| **Association** | `A → B` | A uses B (weak) | `Driver` → `Car` |
| **Aggregation** | `A ◇→ B` | A HAS-A B (independent) | `Library` ◇→ `Book` |
| **Composition** | `A ◆→ B` | A OWNS B (dependent) | `House` ◆→ `Room` |
| **Inheritance** | `A ⎵→ B` | A IS-A B | `Car` ⎵→ `Vehicle` |
| **Realization** | `A ⇢ B` | A implements interface B| `ArrayList` ⇢ `List` |

---

### 3. Aggregation vs Composition

| Feature | Aggregation (◇→) | Composition (◆→) |
| :--- | :--- | :--- |
| **Meaning** | "HAS-A" | "OWNS-A" |
| **Lifecycle** | Independent. Child outlives parent. | Dependent. Child dies with parent. |
| **Example** | Library has Books. | House has Rooms. |

---

### 4. Common OOP Problems & Pattern Mapping

| Problem | Common Design Patterns Used | Why? |
| :--- | :--- | :--- |
| **Parking Lot** | Strategy | To calculate dynamic hourly/daily parking rates easily. |
| **Library System** | Observer, Strategy | Notify users when reserved books arrive (Observer). Search by multiple criteria (Strategy). |
| **ATM System** | State | ATM behavior completely changes based on its current phase (has card, authenticated, etc). |
| **Chess / Board Game**| Command | Encapsulate moves as objects so you can easily implement an "Undo" feature. |
| **Elevator System** | State, Strategy | State (moving, idle, doors open). Strategy (dispatch algorithm: shortest path vs sequential). |
| **Hotel System** | Decorator | To calculate a bill with a base room rate plus various dynamic add-ons (room service, wifi). |
