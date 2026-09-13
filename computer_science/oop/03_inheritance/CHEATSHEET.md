# Inheritance & Composition Cheatsheet

## Inheritance Types

```text
1. Single          2. Multilevel        3. Hierarchical
   [A]                  [A]                   [A]
    |                    |                   /   \
   [B]                  [B]                [B]   [C]
                         |
                        [C]

4. Multiple (C++)  5. Hybrid / Diamond (C++)
 [A]   [B]              [A]
   \   /               /   \
    [C]              [B]   [C]
                       \   /
                        [D]
```

---

## C++ Access Modifier Inheritance Table

| Base Class Access Specifier | Type of Inheritance applied | Resulting Access in Derived Class |
| :--- | :--- | :--- |
| **`public`** | `public` | `public` |
| **`protected`** | `public` | `protected` |
| **`private`** | `public` | *Hidden (Inaccessible)* |
| | | |
| **`public`** | `protected` | `protected` |
| **`protected`** | `protected` | `protected` |
| **`private`** | `protected` | *Hidden (Inaccessible)* |
| | | |
| **`public`** | `private` | `private` |
| **`protected`** | `private` | `private` |
| **`private`** | `private` | *Hidden (Inaccessible)* |

---

## Constructor & Destructor Execution Order

| Language | Constructor Order | Destructor Order | Rule |
| :--- | :--- | :--- | :--- |
| **C++** | Base → Derived | Derived → Base | Base instantiated first. LIFO destruction. |
| **Java** | Base → Derived | Managed by GC | `super()` must be the first statement in derived constructor. |

---

## Syntax Quick Reference

### C++ Virtual Base Class (Fixing the Diamond Problem)
```cpp
class Animal {};
class Mammal : virtual public Animal {}; // Use 'virtual'
class Winged : virtual public Animal {}; // Use 'virtual'
class Bat : public Mammal, public Winged {}; // Only ONE Animal subobject created
```

### Java Inheritance Syntax
```java
// Class inheritance (Single inheritance only)
class Child extends Parent {}

// Interface inheritance (Multiple inheritance allowed)
interface A {}
interface B {}
class Child implements A, B {}

// Interface extending another interface
interface C extends A, B {}
```

---

## Composition vs. Inheritance

| Feature | Inheritance (IS-A) | Composition (HAS-A) |
| :--- | :--- | :--- |
| **Relationship** | Dog IS-A Animal | Car HAS-A Engine |
| **Coupling** | Very High (Tight Coupling) | Low (Loose Coupling) |
| **Flexibility** | Static (Resolved at compile time) | Dynamic (Can change components at runtime) |
| **Encapsulation** | Breaks encapsulation (subclass depends on base class internals) | Preserves encapsulation (black-box reuse) |
| **When to use?** | When you need polymorphism and a strict subset relationship. | Default choice. When reusing behavior without exposing the full API. |
