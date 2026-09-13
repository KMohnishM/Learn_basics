# Module 4 Cheatsheet: Polymorphism

## vTable & vPtr Architecture

```text
       Polymorphic Base Pointer (Base* ptr = new Derived();)
                     |
                     v
+--------------------------------------+
| Derived Object in Memory             |
|--------------------------------------|      +-------------------------+
| vPtr (8 bytes) ----------------------|----->| vTable_Derived          |
| Base Fields (e.g., int x)            |      |-------------------------|
| Derived Fields (e.g., int y)         |      | [0] &Derived::foo       |
+--------------------------------------+      | [1] &Base::bar          |
                                              +-------------------------+
```

## Overloading vs Overriding

| Feature | Overloading (Static) | Overriding (Dynamic) |
| :--- | :--- | :--- |
| **When resolved?** | Compile time | Run time |
| **Scope** | Same class / scope | Base vs Derived classes |
| **Method Signature**| Must be different (parameters) | Must be exactly the same |
| **Mechanism** | Compiler name mangling | vTable and vPtr lookup |
| **Performance** | Zero overhead | ~1-3ns overhead (indirection) |

## C++ Cast Types Quick Reference

| Cast | Syntax | Use Case & Safety |
| :--- | :--- | :--- |
| **`static_cast`** | `static_cast<T*>(ptr)` | Compile-time checks only. Safe for UP-casting. DANGEROUS for down-casting (UB if wrong). |
| **`dynamic_cast`** | `dynamic_cast<T*>(ptr)` | Safe down-casting. Requires RTTI (virtual methods). Returns `nullptr` if cast is invalid. |
| **`reinterpret_cast`**| `reinterpret_cast<T*>(ptr)` | Raw bit reinterpretation. Extremely dangerous. Used for hardware/networking. |
| **`const_cast`** | `const_cast<T*>(ptr)` | Removes `const` qualifier. UB if the original variable was actually instantiated as `const`. |

## Java Safe Downcasting (Instanceof Pattern)

```java
// Java 16+ Pattern Matching
if (baseRef instanceof Derived d) {
    // Cast is automatically successful and safe
    d.derivedMethod(); 
}
```

## Critical Rules to Memorize

**The Virtual Destructor Rule:**
> If a C++ class has ANY virtual function, its destructor MUST be virtual to prevent memory leaks when deleting through a base pointer.

**Object Slicing Rule:**
> Slicing occurs in C++ when you pass or assign a derived object by VALUE to a base class variable. To prevent this, ALWAYS use pointers (`Base*`) or references (`Base&`) for polymorphism.

## Compile-Time vs Runtime Polymorphism

| | Compile-Time (Static) | Runtime (Dynamic) |
| :--- | :--- | :--- |
| **Implementations** | Function Overloading, Operator Overloading, C++ Templates | Method Overriding (virtual functions) |
| **Binding** | Early Binding | Late Binding |
| **Speed** | Fast (Resolved instantly) | Slower (vTable indirection) |
