# QnA: Classes and Objects

## 🟢 Easy

**1. What is the difference between a class and an object? Give a real-world analogy.**
A class is a blueprint or template that defines the structure, properties, and behaviors of a type. It exists as a concept and does not allocate memory for state. An object is a concrete, runtime instance of a class, holding specific data in memory.
*Analogy:* A class is like the architectural blueprint for a house. It shows where the walls and doors go. An object is the actual physical house built from that blueprint. You can build multiple houses (objects) from the same blueprint (class), each with its own address and paint color.

**2. What is a copy constructor in C++? List three situations where it is automatically invoked.**
A copy constructor is a special constructor that initializes a new object as an exact copy of an existing object of the same type. Its signature is typically `ClassName(const ClassName& other)`.
It is automatically invoked in three main situations:
1. When an object is passed by value to a function.
2. When an object is returned by value from a function (if copy elision/RVO is not applied).
3. When a new object is initialized from an existing object using direct or copy initialization (e.g., `MyClass a = b;`).

**3. What is the `this` pointer in C++? What is `this` in Java? Can either be null?**
In C++, `this` is a hidden pointer passed to all non-static member functions, pointing to the object on which the function was called. Its type is `ClassName* const`. It can technically be null if a method is called on a null pointer, but this is Undefined Behavior.
In Java, `this` is a reference to the current object. It is used to disambiguate instance variables from local parameters or to pass the current object to other methods. In Java, `this` can never be null; invoking a method on a null reference throws a `NullPointerException` before the method executes.

## 🟡 Medium

**4. What is RAII? Implement a `MutexLock` RAII wrapper class in C++. Why does Java not need RAII?**
RAII (Resource Acquisition Is Initialization) is a C++ idiom where resource management (memory, file handles, locks) is tied to object lifetime. Resources are acquired in the constructor and released in the destructor, guaranteeing cleanup even if exceptions are thrown.
```cpp
class MutexLock {
    std::mutex& mtx;
public:
    MutexLock(std::mutex& m) : mtx(m) { mtx.lock(); }
    ~MutexLock() { mtx.unlock(); }
};
```
Java relies on Garbage Collection for memory and the `try-with-resources` construct (via `AutoCloseable`) for other resources, so it does not use deterministic destructors like C++.

**5. What is the Rule of Three in C++? What happens if you violate it? What does the Rule of Five add?**
The Rule of Three states that if a class requires a user-defined destructor, copy constructor, or copy assignment operator, it almost certainly requires all three. This usually happens when the class manages a raw resource (like a heap-allocated pointer). If violated, the compiler-generated shallow copies will copy raw pointer addresses, leading to double-free errors or memory leaks.
The Rule of Five (C++11) adds the Move Constructor and Move Assignment Operator to optimize performance by transferring ownership of resources instead of copying them.

**6. Why does `sizeof(EmptyClass)` return 1 in C++ and not 0? What is the alignment padding rule?**
C++ mandates that every distinct object must have a unique memory address to allow pointer arithmetic and array indexing to work correctly. If `sizeof(EmptyClass)` were 0, an array of empty objects would all share the exact same address. To prevent this, the compiler inserts a dummy byte, making the size 1.
Alignment padding is added to structs/classes so that members start at memory addresses that are multiples of their own size (e.g., a 4-byte `int` starts at an address divisible by 4) to optimize CPU fetch operations.

## 🔴 Hard

**7. Trace the constructor and destructor call order for the following C++ code:**
```cpp
struct Base { Base() { cout << "B ctor\n"; } ~Base() { cout << "B dtor\n"; } };
struct Derived : Base { Derived() { cout << "D ctor\n"; } ~Derived() { cout << "D dtor\n"; } };
int main() { Derived d; }
```
**Output:**
```text
B ctor
D ctor
D dtor
B dtor
```
Constructors run base-first, derived-last. Destructors run in the exact reverse order: derived-first, base-last.
If we change the main to `Base* p = new Derived(); delete p;` and `~Base()` is NOT virtual, the output is only `B ctor -> D ctor -> B dtor`. The derived destructor (`D dtor`) is never called, causing a resource leak. Always make base class destructors `virtual`!

**8. Implement a `StringBuffer` class in C++ that manages a heap-allocated char array. Show the full Rule of Five implementation. Then show the equivalent Java class using `clone()` and explain the difference in memory management.**
**C++ Rule of Five:**
```cpp
#include <cstring>
#include <utility>

class StringBuffer {
    char* data;
public:
    StringBuffer(const char* str = "") {
        data = new char[strlen(str) + 1];
        strcpy(data, str);
    }
    ~StringBuffer() { delete[] data; }
    
    // Copy Constructor
    StringBuffer(const StringBuffer& other) {
        data = new char[strlen(other.data) + 1];
        strcpy(data, other.data);
    }
    // Copy Assignment
    StringBuffer& operator=(const StringBuffer& other) {
        if (this != &other) {
            delete[] data;
            data = new char[strlen(other.data) + 1];
            strcpy(data, other.data);
        }
        return *this;
    }
    // Move Constructor
    StringBuffer(StringBuffer&& other) noexcept : data(other.data) {
        other.data = nullptr;
    }
    // Move Assignment
    StringBuffer& operator=(StringBuffer&& other) noexcept {
        if (this != &other) {
            delete[] data;
            data = std::exchange(other.data, nullptr);
        }
        return *this;
    }
};
```
**Java Equivalent:**
```java
class StringBuffer implements Cloneable {
    private char[] data;
    public StringBuffer(String str) {
        data = str.toCharArray();
    }
    @Override
    protected Object clone() throws CloneNotSupportedException {
        StringBuffer copy = (StringBuffer) super.clone();
        copy.data = this.data.clone(); // Deep copy the array
        return copy;
    }
}
```
**Difference:** In C++, you manually allocate (`new[]`) and deallocate (`delete[]`) memory. You must provide move semantics for performance and copy semantics to prevent double frees. In Java, the Garbage Collector handles deallocation. Copying is explicit (via `clone()` or a copy constructor pattern), and references are passed by default, so move semantics aren't explicitly needed in the same way.
