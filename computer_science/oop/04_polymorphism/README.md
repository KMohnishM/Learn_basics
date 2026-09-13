# Module 4: Polymorphism

Polymorphism (from Greek, meaning "many forms") is one of the foundational pillars of Object-Oriented Programming (OOP). It allows objects of different types to be treated as instances of the same class through a common interface. More fundamentally, it defines how an entity (like a function, operator, or object) can behave differently depending on the context or the data types it interacts with.

In this module, we will deeply explore both compile-time (static) and runtime (dynamic) polymorphism in C++ and Java, including the internal mechanics of how dynamic dispatch is implemented under the hood (vTables).

---

## 1. Compile-time (Static) Polymorphism

Compile-time polymorphism is resolved entirely during compilation. The compiler determines exactly which function, operator, or template to invoke based on the provided arguments and types. Because this resolution happens before the program runs, it carries **zero runtime overhead**.

### 1.1 Function / Method Overloading

Function overloading allows multiple functions in the same scope to share the same name, provided they have different parameter lists (different number of arguments or different types). 

**What CAN differ:**
- Number of parameters
- Types of parameters
- Order of parameter types (e.g., `void foo(int, double)` vs `void foo(double, int)`)

**What CANNOT differ:**
- Return type alone (the compiler cannot determine which function to call based solely on what the caller intends to do with the return value).

#### C++ Example

```cpp
#include <iostream>
#include <string>

class Printer {
public:
    // Overload 1: int
    void print(int value) {
        std::cout << "Integer: " << value << "\n";
    }

    // Overload 2: double
    void print(double value) {
        std::cout << "Double: " << value << "\n";
    }

    // Overload 3: string
    void print(const std::string& value) {
        std::cout << "String: " << value << "\n";
    }
};

int main() {
    Printer p;
    p.print(42);         // Calls Overload 1
    p.print(3.14159);    // Calls Overload 2
    p.print("Hello");    // Calls Overload 3
    return 0;
}
```

#### Java Example

Java handles method overloading exactly the same way.

```java
public class Printer {
    public void print(int value) {
        System.out.println("Integer: " + value);
    }

    public void print(double value) {
        System.out.println("Double: " + value);
    }

    public void print(String value) {
        System.out.println("String: " + value);
    }

    public static void main(String[] args) {
        Printer p = new Printer();
        p.print(42);
        p.print(3.14159);
        p.print("Hello");
    }
}
```

### 1.2 Operator Overloading (C++ only)

C++ allows you to redefine how standard operators (`+`, `-`, `==`, `<<`, etc.) work when applied to user-defined types (classes/structs). This allows your classes to behave like primitive types.

> **Note on Java:** Java deliberately does **not** support operator overloading (except for `+` on Strings). The language designers felt it could lead to unreadable code if developers abused it (e.g., overriding `+` to mean subtraction).

#### C++ Operator Overloading Example

```cpp
#include <iostream>

class Vector2D {
private:
    double x, y;

public:
    Vector2D(double x, double y) : x(x), y(y) {}

    // Overload the + operator
    Vector2D operator+(const Vector2D& rhs) const {
        return Vector2D(this->x + rhs.x, this->y + rhs.y);
    }

    // Overload the == operator
    bool operator==(const Vector2D& rhs) const {
        return (this->x == rhs.x) && (this->y == rhs.y);
    }

    // Overload the << operator for standard output streams
    // Note: This is typically declared as a friend function
    friend std::ostream& operator<<(std::ostream& os, const Vector2D& vec) {
        os << "(" << vec.x << ", " << vec.y << ")";
        return os;
    }
};

int main() {
    Vector2D v1(1.0, 2.0);
    Vector2D v2(3.0, 4.0);
    
    Vector2D v3 = v1 + v2;  // Calls operator+
    
    std::cout << "v3 is: " << v3 << "\n"; // Calls operator<<
    
    if (v1 == v2) {         // Calls operator==
        std::cout << "Vectors are equal.\n";
    }
    
    return 0;
}
```

### 1.3 Templates (C++) / Generics (Java)

Templates and Generics allow you to write type-independent code. However, their implementations under the hood are completely different.

#### C++ Templates: Code Generation
In C++, a template acts as a blueprint. When you instantiate a template with a specific type, the compiler **generates brand new machine code** for that type.

```cpp
template <typename T>
T max(T a, T b) {
    return (a > b) ? a : b;
}

int main() {
    int i = max<int>(5, 10);          // Generates max(int, int)
    double d = max<double>(5.5, 2.2); // Generates max(double, double)
}
```

**Pros:** Maximum performance (zero runtime overhead).
**Cons:** Can lead to "code bloat" because the compiler creates a separate copy of the function for every type used.

#### Java Generics: Type Erasure
In Java, generics are primarily a compile-time check to ensure type safety. Once the code compiles, the Java compiler performs **Type Erasure**, removing all generic type parameters and replacing them with `Object` (or bounding classes).

```java
public class MathUtils {
    public static <T extends Comparable<T>> T max(T a, T b) {
        return (a.compareTo(b) > 0) ? a : b;
    }

    public static void main(String[] args) {
        Integer i = max(5, 10);
        Double d = max(5.5, 2.2);
    }
}
```

**Pros:** Reuses the exact same bytecode for all types (no code bloat).
**Cons:** Primitive types cannot directly be used (you must use wrappers like `Integer` instead of `int`), and reflection at runtime lacks type information.

---

## 2. Runtime (Dynamic) Polymorphism

Dynamic polymorphism is achieved through **Method Overriding**. It allows a program to determine at *runtime* which method implementation to call, based on the actual object type rather than the reference or pointer type.

### 2.1 Method Overriding Basics

Method overriding occurs when a derived (child) class provides a specific implementation of a method that is already provided by its base (parent) class.

#### C++ Rules
In C++, dynamic dispatch is **opt-in**. You must declare the base class method with the `virtual` keyword. 

```cpp
class Base {
public:
    virtual void print() { 
        std::cout << "Base\n"; 
    }
};

class Derived : public Base {
public:
    // C++11 'override' specifies the intent to override.
    // The compiler will throw an error if the signature doesn't exactly match.
    void print() override { 
        std::cout << "Derived\n"; 
    }
};

// C++11 'final' prevents further derivation or overriding
class LeafDerived : public Derived {
public:
    void print() final { 
        std::cout << "LeafDerived\n"; 
    }
};
```

#### Java Rules
In Java, dynamic dispatch is **opt-out**. ALL non-static, non-final, non-private methods are virtual by default.

```java
class Base {
    public void print() {
        System.out.println("Base");
    }
}

class Derived extends Base {
    // @Override is an annotation that acts like a compile-time check.
    // If you misspell the method name or change the parameters, the compiler fails.
    @Override
    public void print() {
        System.out.println("Derived");
    }
}
```

**What happens if you omit `@Override` in Java or `override` in C++?**
If you accidentally change the signature (e.g., `void print(int)` instead of `void print()`), the code will compile, but it will **silently fail to override**. Instead, it creates an overloaded method. The base class pointer will call the base implementation, leading to subtle, hard-to-find logic bugs.

---

## 3. vTable Internals (C++) — Deep Dive

How does the program know to call `Derived::print` when it only has a pointer of type `Base*`? The answer lies in the **Virtual Table (vTable)** and the **Virtual Pointer (vPtr)**.

### 3.1 What are they?

- **vTable (Virtual Table):** An array of function pointers created by the compiler. 
  - There is exactly **one vTable per polymorphic class** (any class with at least one virtual function).
  - It contains pointers to the most-derived implementations of the virtual functions for that class.
- **vPtr (Virtual Pointer):** A hidden pointer injected into your object by the compiler.
  - There is **one vPtr per object instance**.
  - It typically adds 8 bytes (on 64-bit systems) to the size of your object.
  - It is initialized during the object's construction to point to the class's vTable.

### 3.2 Memory Layout Diagram

Consider this hierarchy:
```cpp
class Base {
public:
    int x;
    virtual void foo() { ... }
    virtual void bar() { ... }
};

class Derived : public Base {
public:
    int y;
    void foo() override { ... }  // Overrides foo
    // Does NOT override bar
};
```

Here is exactly what the memory layout looks like at runtime:

```text
Base Object in memory:
+----------------+
| vPtr           |----------> vTable_Base:
| int x          |            [0] &Base::foo
+----------------+            [1] &Base::bar


Derived Object in memory:
+----------------+
| vPtr           |----------> vTable_Derived:
| int x          |            [0] &Derived::foo   <-- Points to Derived's override
| int y          |            [1] &Base::bar      <-- Inherited from Base
+----------------+
```

### 3.3 The Runtime Dispatch Process

When you execute `Base* b = new Derived(); b->foo();`, the following sequence happens entirely at runtime:

1. **Dereference the pointer:** The CPU goes to the address stored in `b`.
2. **Read the vPtr:** The CPU reads the first 8 bytes of the object to find the vPtr.
3. **Lookup the vTable:** The CPU follows the vPtr to `vTable_Derived`.
4. **Index into the vTable:** The compiler knows that `foo()` is at index 0. The CPU fetches the function pointer at `vTable_Derived[0]`.
5. **Call the function:** The CPU jumps to the address of `Derived::foo()`.

**Performance Cost:** This indirection takes extra CPU cycles (~1-3 nanoseconds). It also inhibits function inlining, which is why excessive use of virtual functions can impact extreme high-performance applications (like game engines or high-frequency trading).

### Java Equivalent
Java uses a very similar concept within the JVM. Every Java object has a hidden "mark word" and "klass pointer" in its object header. The `klass` pointer points to class metadata containing a method table (similar to a vTable) used for the `invokevirtual` bytecode instruction.

---

## 4. Object Slicing (C++ only)

Because C++ allows objects to be allocated directly on the stack (as values), you can encounter a dangerous problem known as **Object Slicing**.

### The Problem

If you assign a `Derived` object directly to a `Base` variable (by value), the compiler copies *only* the `Base` portion of the object. The derived fields and the derived vPtr are "sliced off."

```cpp
class Base {
public:
    int x = 1;
    virtual void show() { cout << "Base\n"; }
};

class Derived : public Base {
public:
    int y = 2;
    void show() override { cout << "Derived\n"; }
};

int main() {
    Derived d;
    
    // SLICING OCCURS HERE!
    Base b = d; 
    
    b.show(); // Outputs "Base", not "Derived"!
    // Any attempt to access 'y' via 'b' is impossible.
}
```

### Why Java Doesn't Have Slicing
In Java, you cannot hold an object by value. Variables (like `Base b = new Derived();`) are always **references** pointing to the heap. Assigning objects merely copies the reference, leaving the heap object perfectly intact.

### How to Avoid Slicing in C++
To achieve polymorphism in C++, you **must** use pointers (`*`) or references (`&`).

```cpp
Derived d;

// Passed by reference - No slicing
Base& b_ref = d;
b_ref.show(); // Outputs "Derived"

// Passed by pointer - No slicing
Base* b_ptr = &d;
b_ptr->show(); // Outputs "Derived"
```

---

## 5. Virtual Destructor — Critical Rule

There is one golden rule in C++ inheritance: **If a class has ANY virtual function, its destructor MUST be virtual.**

### The Undefined Behavior Trap

When you delete a derived object through a base pointer, the compiler looks at the base class to figure out which destructor to call. If the base destructor is **non-virtual**, static binding is used, and only `~Base()` is executed. The derived object's destructor is never called, causing massive memory leaks or resource corruption.

#### The Bug:

```cpp
class Base {
public:
    // Missing 'virtual'
    ~Base() { cout << "Base destroyed\n"; } 
};

class Derived : public Base {
    int* data;
public:
    Derived() { data = new int[1000]; }
    ~Derived() { 
        delete[] data; 
        cout << "Derived destroyed\n"; 
    }
};

int main() {
    Base* ptr = new Derived();
    delete ptr; // ONLY calls ~Base(). 'data' is LEAKED.
}
```

#### The Fix:

Simply add `virtual` to the base destructor.

```cpp
class Base {
public:
    virtual ~Base() { cout << "Base destroyed\n"; } 
};
```
Now, `delete ptr;` does a vTable lookup, finds `~Derived()`, calls it (freeing the memory), and then automatically calls `~Base()`.

> **Java Note:** Java does not have destructors. Memory is managed by the Garbage Collector (GC). The `finalize()` method was somewhat analogous but was officially deprecated in Java 9 due to unreliability.

---

## 6. Cast Operators (C++ and Java)

When working with polymorphic hierarchies, you often need to convert pointers/references up and down the tree.

### C++ Casts

C++ provides four specific casting operators to make developer intent clear and searchable.

1. **`static_cast<T>`**: Used for compile-time conversions. 
   - Good for going UP the hierarchy (`Derived*` → `Base*`).
   - *Dangerous* for going DOWN the hierarchy (`Base*` → `Derived*`). It applies zero runtime checks. If the object wasn't actually a Derived, you invoke Undefined Behavior.
   
2. **`dynamic_cast<T>`**: Safe downcasting.
   - Requires RTTI (Run-Time Type Information) and a polymorphic class (at least one virtual function).
   - If the cast is valid, it returns the pointer.
   - If the cast is invalid, it returns `nullptr` (or throws `std::bad_cast` for references).
   ```cpp
   Base* b = getSomeObject();
   if (Derived* d = dynamic_cast<Derived*>(b)) {
       d->derivedSpecificMethod();
   }
   ```

3. **`reinterpret_cast<T>`**: Extremely dangerous. Simply tells the compiler to treat a sequence of bits as a completely different type. Used in systems programming/networking.

4. **`const_cast<T>`**: Used to add or remove `const`. Warning: Modifying a value that was originally declared as `const` after casting away its constness results in Undefined Behavior.

### Java Casts

Java has safe downcasting built in natively.

```java
Base b = getSomeObject();

// Old way (Java 15 and below)
if (b instanceof Derived) {
    Derived d = (Derived) b; // Explicit cast
    d.derivedSpecificMethod();
}

// New way (Java 16+ Pattern Matching)
if (b instanceof Derived d) {
    d.derivedSpecificMethod(); // 'd' is safely scoped and casted
}
```
If you perform `(Derived) b` without checking, and `b` is not a `Derived`, Java safely throws a `ClassCastException` rather than corrupting memory like C++.

---

## 7. Early vs Late Binding Summary

| Feature | Early Binding (Static) | Late Binding (Dynamic) |
| :--- | :--- | :--- |
| **When it happens** | Compile time | Run time |
| **Mechanisms** | Function Overloading, Operator Overloading, Templates | Virtual Functions, Method Overriding |
| **Speed** | Blazing fast (direct CPU jump, inlining possible) | Slightly slower (vTable lookup overhead) |
| **Flexibility** | Rigid. Caller must know the exact type. | Highly flexible. Promotes loose coupling. |
| **Memory Overhead** | None | 8 bytes per object (vPtr) + size of vTable per class |

Understanding the precise mechanics of vTables and object layouts distinguishes junior developers from senior engineers. The ability to reason about memory, slicing, and dispatch overhead is critical for writing robust, high-performance distributed systems in C++.
