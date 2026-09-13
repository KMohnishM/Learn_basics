# Module 1: Classes and Objects

Welcome to Module 1 of the Object-Oriented Programming (OOP) curriculum. This module dives deep into the foundational concepts of OOP, focusing primarily on C++ and Java. We will explore what classes and objects are, memory management, constructors, destructors, the `this` pointer/reference, instance vs static variables, class sizes, struct vs class, the Rule of Three/Five, and the Java Object class.

---

## 1. What is a Class? What is an Object?

### Core Definitions
- **Class**: A class is a user-defined blueprint or prototype from which objects are created. It represents the set of properties (fields/attributes) and methods (behaviors) that are common to all objects of one type. At the compiler level, a class is a type definition; it does not allocate memory for data until an object is instantiated.
- **Object**: An object is a runtime instance of a class. It contains state (values of its fields) and behavior (defined by methods). When an object is instantiated, memory is allocated to hold its specific state.

### Object Identity vs Object Equality
In both C++ and Java, it is crucial to distinguish between identity (are these two references pointing to the exact same memory location?) and equality (do these two distinct objects contain the same logical values?).

**C++:**
- Identity: Check if memory addresses are equal (`&obj1 == &obj2`).
- Equality: Compare values directly or overload the `==` operator for custom logic.
```cpp
Person p1("Alice");
Person p2("Alice");
bool isSameInstance = (&p1 == &p2); // False, different memory addresses
bool isLogicallyEqual = (p1 == p2); // True, if operator== compares names
```

**Java:**
- Identity: The `==` operator compares object references (memory addresses).
- Equality: The `.equals()` method compares logical content (must be overridden in your class).
```java
Person p1 = new Person("Alice");
Person p2 = new Person("Alice");
boolean isSameInstance = (p1 == p2); // False
boolean isLogicallyEqual = p1.equals(p2); // True, if equals() is properly overridden
```

### Instantiation and Memory Allocation Flow
When an object is created, the system allocates memory for its instance variables and calls the appropriate constructor to initialize them.

#### Stack vs Heap
The way memory is allocated differs significantly between C++ and Java.

**C++ Stack Allocation:**
```cpp
MyClass obj; // Allocated on the stack. Destroyed when it goes out of scope.
```
**C++ Heap Allocation:**
```cpp
MyClass* objPtr = new MyClass(); // Allocated on the heap. Must manually call 'delete objPtr'.
```

**Java:**
In Java, **all** objects are allocated on the heap. Primitives (`int`, `double`, `boolean`) and object references themselves live on the stack (if they are local variables).
```java
MyClass obj = new MyClass(); // 'obj' reference is on stack; the actual object is on heap.
```

#### ASCII Diagram: Stack Frame + Heap

```text
C++ Memory Model:
+------------------------+          +-------------------------+
|        STACK           |          |         HEAP            |
|                        |          |                         |
|  [ MyClass obj ]       |          |                         |
|   - field1             |          |                         |
|   - field2             |          |                         |
|                        |          |                         |
|  [ MyClass* objPtr ] --+--------->|  [ MyClass instance ]   |
|                        |          |   - field1              |
|                        |          |   - field2              |
+------------------------+          +-------------------------+

Java Memory Model:
+------------------------+          +-------------------------+
|        STACK           |          |         HEAP            |
|                        |          |                         |
|  [ int localPrim = 5 ] |          |                         |
|                        |          |                         |
|  [ MyClass objRef ] ---+--------->|  [ MyClass instance ]   |
|                        |          |   - field1              |
|                        |          |   - field2              |
+------------------------+          +-------------------------+
```

---

## 2. Constructors

Constructors are special member functions called automatically when an object is instantiated. They initialize the object's state.

### Default Constructor
- **C++**: If no constructors are defined, the compiler generates a default (no-argument) constructor.
- **Java**: Similarly, the compiler provides a default constructor if none is explicitly written.

### Parameterized Constructor
Initializes the object with arguments.
```cpp
// C++
class Point {
    int x, y;
public:
    Point(int xVal, int yVal) : x(xVal), y(yVal) {} // Initializer list
};
```
```java
// Java
class Point {
    int x, y;
    public Point(int xVal, int yVal) {
        this.x = xVal;
        this.y = yVal;
    }
}
```

### Copy Constructor (C++ Only)
Creates a new object as a copy of an existing object. Signature: `ClassName(const ClassName& other)`.
Invoked during:
1. Pass by value to a function.
2. Return by value from a function (though often optimized away by RVO).
3. Initialization from an existing object (`MyClass a = b;` or `MyClass a(b);`).
```cpp
class ArrayWrapper {
    int* data;
    int size;
public:
    ArrayWrapper(const ArrayWrapper& other) {
        size = other.size;
        data = new int[size];
        for(int i = 0; i < size; ++i) data[i] = other.data[i];
    }
};
```
*Note*: Java does not have copy constructors built into the language rules, but you can manually define a constructor that takes an instance of the same class, or implement the `Cloneable` interface.

### Move Constructor (C++11)
Steals resources from a temporary (rvalue) object, leaving the source in a valid but empty state. Extremely efficient. Signature: `ClassName(ClassName&& other)`.
```cpp
class ArrayWrapper {
    int* data;
    int size;
public:
    // Move constructor
    ArrayWrapper(ArrayWrapper&& other) noexcept : data(other.data), size(other.size) {
        other.data = nullptr; // Steal resource, leave source empty
        other.size = 0;
    }
};
```

### Initializer List vs Constructor Body (C++)
Initializer lists are executed before the constructor body. They are **preferred** and sometimes **required** because:
1. **Efficiency**: Avoids default construction followed by assignment.
2. **Const members**: Must be initialized in the initializer list.
3. **Reference members**: Must be initialized in the initializer list.

---

## 3. Destructors and Garbage Collection

### C++ Destructor `~MyClass()`
Called automatically when an object goes out of scope (stack) or when `delete` is called (heap). Used to release resources.

### RAII (Resource Acquisition Is Initialization)
A core C++ idiom: acquire resources in the constructor, release them in the destructor.
```cpp
class FileHandler {
    FILE* file;
public:
    FileHandler(const char* filename) {
        file = fopen(filename, "r");
        if (!file) throw std::runtime_error("File open failed");
    }
    ~FileHandler() {
        if (file) {
            fclose(file);
        }
    }
};
```
**Why RAII?** It guarantees resource cleanup even if exceptions are thrown. Stack unwinding ensures destructors for local objects are called.

### Java: Garbage Collector and `AutoCloseable`
Java manages memory via Garbage Collection (GC). The `finalize()` method is deprecated and should not be used. For deterministic resource cleanup (like files or sockets), Java uses the `try-with-resources` statement, requiring classes to implement `AutoCloseable`.

```java
class FileHandler implements AutoCloseable {
    // ... constructor opens resource ...
    @Override
    public void close() throws Exception {
        // ... release resource ...
    }
}
// Usage:
// try (FileHandler fh = new FileHandler("file.txt")) {
//     // use fh
// } // close() is automatically called here
```

---

## 4. The `this` Pointer/Reference

### C++: `this` Pointer
- `this` is a hidden pointer passed to non-static member functions.
- Type inside a non-const method of `MyClass`: `MyClass* const` (a constant pointer to a non-constant object).
- Inside a `const` method: `const MyClass* const`.
- *Can it be null?* Technically yes, if you call a method on a null pointer (Undefined Behavior), e.g., `MyClass* ptr = nullptr; ptr->doSomething();` (Avoid this!).

### Java: `this` Reference
- Used to disambiguate class fields from local parameters.
- Cannot be null.

### Method Chaining / Fluent Interface
Returning `*this` (C++) or `this` (Java) allows for method chaining, a key component of the Builder pattern.

**C++ Example:**
```cpp
class Configurator {
    int timeout;
    std::string url;
public:
    Configurator& setTimeout(int t) {
        timeout = t;
        return *this;
    }
    Configurator& setUrl(const std::string& u) {
        url = u;
        return *this;
    }
};
// Usage: conf.setTimeout(100).setUrl("http://api");
```

---

## 5. Instance vs Static Variables

### Instance Variables
- Each object has its own separate copy.
- Stored on the heap alongside the object (or on the stack in C++).

### Static / Class Variables
- One shared copy across all instances of the class.
- Stored in a special static memory segment (data segment / method area).

### Static Methods
- Do not have a `this` pointer/reference.
- Can only access static variables and call other static methods directly.

**Java Notes:**
- Python uses `@classmethod` (passes class as first arg) and `@staticmethod` (no hidden args). Java's `static` methods are akin to Python's `@staticmethod`.

---

## 6. `sizeof` a C++ Class

The size of a C++ object is the sum of the sizes of its data members plus alignment padding. Functions (unless virtual) do not add to the size of an object.

### Alignment Rules
Processors access memory more efficiently when data is aligned. A compiler pads structs/classes so members are placed at addresses that are multiples of their size.

```cpp
class PaddingExample {
    char a;    // 1 byte
               // 3 bytes padding
    int b;     // 4 bytes
    char c;    // 1 byte
               // 3 bytes padding
};
// sizeof(PaddingExample) == 12 (typically, on a 32/64 bit system)
```

### Empty Class Size
```cpp
class EmptyClass {};
// sizeof(EmptyClass) == 1
```
C++ requires that different objects of the same type have distinct memory addresses. If size were 0, an array of `EmptyClass` would have all elements at the same address. The compiler inserts 1 byte.

---

## 7. C++ `struct` vs `class`

In C++, `struct` and `class` are almost identical.
- **ONLY Difference**: Default access specifier.
  - `struct` members and base classes are `public` by default.
  - `class` members and base classes are `private` by default.

**Convention:**
- Use `struct` for Plain Old Data (POD) structures without complex invariants.
- Use `class` for types that encapsulate state, enforce invariants, and provide behaviors.

---

## 8. Rule of Three / Rule of Five (C++)

### Rule of Three
If your class manages a resource manually (e.g., raw pointers, file handles) and needs to define **any one** of the following, it almost certainly needs to define **all three**:
1. Destructor
2. Copy Constructor
3. Copy Assignment Operator

**Why?** The default compiler-generated versions perform shallow copies. If you have a raw pointer, a shallow copy copies the address, leading to double-free bugs when both objects are destroyed.

### Rule of Five (C++11)
Extends the Rule of Three with move semantics:
4. Move Constructor
5. Move Assignment Operator

### Rule of Zero
The modern C++ approach: design your classes so you don't need any of the five. Use RAII types like `std::string`, `std::vector`, or smart pointers (`std::unique_ptr`, `std::shared_ptr`). They manage their own memory, so the compiler-generated copy/move operations will work perfectly.

---

## 9. Java Object Class

In Java, every class implicitly extends the `java.lang.Object` class.
Key methods inherited:
- `equals(Object obj)`: For logical equality.
- `hashCode()`: Returns an integer hash for use in hash tables.
- `toString()`: Returns a string representation.
- `clone()`: Creates a shallow copy (requires implementing `Cloneable`).

### The `equals` and `hashCode` Contract
If you override `equals()`, you **must** override `hashCode()`.
- If `a.equals(b)` is true, then `a.hashCode() == b.hashCode()` must also be true.
- If they are unequal, their hash codes do not strictly need to be different, but distinct hashes improve hash table performance.

```java
import java.util.Objects;

class Person {
    private String name;
    private int age;

    public Person(String name, int age) {
        this.name = name;
        this.age = age;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Person person = (Person) o;
        return age == person.age && Objects.equals(name, person.name);
    }

    @Override
    public int hashCode() {
        return Objects.hash(name, age);
    }
}
```

This concludes Module 1. Make sure you understand the memory layouts, constructors, and object lifecycles, as they are foundational for writing robust, leak-free code in C++ and Java.
