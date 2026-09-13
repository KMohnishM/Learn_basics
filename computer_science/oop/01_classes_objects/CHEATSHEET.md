# CHEATSHEET: Classes & Objects (C++ vs Java)

## 🏗️ Constructors & Core Concepts

| Concept | C++ | Java |
|---------|-----|------|
| **Default Constructor** | Provided if none defined. | Provided if none defined. |
| **Parameterized Ctor** | Uses Initializer Lists. | Uses constructor body (`this.x = x`). |
| **Copy Constructor** | `Class(const Class& other)` | Not built-in. Use manual pattern/clone. |
| **Move Constructor** | `Class(Class&& other)` (C++11) | N/A (Everything is references). |
| **Destructor / Cleanup** | `~Class()` (Deterministic RAII) | `AutoCloseable` + `try-with-resources` |
| **Memory Cleanup** | Manual (`delete`) / Smart Pointers | Garbage Collector (GC) |
| **Struct vs Class** | Differs only by default access. | `record` (Java 14+) for data carriers. |

## 📐 Memory: Stack vs Heap

```text
       C++ Memory Allocation                 Java Memory Allocation
       
STACK          HEAP                  STACK          HEAP
[Obj a]        [Obj *ptr] ---->      [ref p] -----> [Object Instance]
(values)       (values)              (address)      (values)
(auto-free)    (needs delete)        (auto-free)    (GC collects)
```
- **C++:** Objects can be on Stack (`MyClass obj;`) or Heap (`MyClass* obj = new MyClass();`).
- **Java:** All objects are on Heap. Stack holds primitives & object references.

## 📏 Size & Padding (C++)
`sizeof(Class)` = Sum of members + Alignment Padding.
- Members align to their own sizes.
- `sizeof(EmptyClass) == 1` (Objects must have unique addresses).

## 🖐️ Rule of Three / Five / Zero (C++)
- **Rule of 3:** If managing raw resources, define: `Destructor`, `Copy Constructor`, `Copy Assignment`.
- **Rule of 5:** Add `Move Constructor` and `Move Assignment` for performance.
- **Rule of Zero:** Use `std::unique_ptr`, `std::vector`, `std::string` to avoid writing any of the 5.

## 🔗 The `this` Keyword
- **C++:** A pointer (`Class* const this`). Use `*this` to return object reference.
- **Java:** A reference. Use `this` to return object reference.
- **Use Case:** Method chaining (Builder pattern) and disambiguating fields from parameters.

## 🛡️ RAII Pattern Template (C++)
Resource Acquisition Is Initialization.
```cpp
class ResourceHandler {
    Resource* res;
public:
    ResourceHandler() { res = acquire(); }
    ~ResourceHandler() { release(res); } // Guaranteed cleanup
};
```
