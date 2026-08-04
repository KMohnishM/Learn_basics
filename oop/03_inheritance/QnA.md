# Object-Oriented Programming: Inheritance - Questions & Answers

## 🟢 Easy

### 1. What is inheritance? What is the IS-A vs HAS-A distinction? Give examples.
**Inheritance** is an OOP mechanism where a new class (derived/child class) acquires the properties and behaviors (fields and methods) of an existing class (base/parent class). It promotes code reusability and establishes a relationship between classes.

**IS-A vs HAS-A:**
- **IS-A (Inheritance):** Indicates that one entity is a specialized version of another. 
  - *Example:* A `Dog` IS-A `Animal`. A `Car` IS-A `Vehicle`. You use inheritance (`class Dog : public Animal` or `class Dog extends Animal`).
- **HAS-A (Composition/Aggregation):** Indicates that one entity contains or uses another entity as part of its state.
  - *Example:* A `Car` HAS-A `Engine`. A `Person` HAS-A `Heart`. You use object composition (`class Car { Engine e; };`).

### 2. What types of inheritance exist? Which does Java support natively for classes?
**Types of Inheritance:**
1. **Single:** One child inherits from one parent.
2. **Multilevel:** A child inherits from a parent, which inherits from a grandparent.
3. **Hierarchical:** Multiple children inherit from a single parent.
4. **Multiple:** One child inherits from multiple parents.
5. **Hybrid:** A combination of multiple and multilevel inheritance (often causing the Diamond Problem).

**Java Support:**
Java natively supports **Single, Multilevel, and Hierarchical** inheritance for classes. It **does not** support Multiple or Hybrid inheritance for classes to avoid ambiguity. However, Java allows multiple inheritance of *interfaces* (a class can implement multiple interfaces).

### 3. Trace the constructor call order for: `class A {}; class B : public A {}; class C : public B {};` — what is the output when `C c;` is executed?
When an object of a derived class is created, the base class constructors are called first, starting from the top of the hierarchy down to the most derived class.
The order of execution for `C c;` would be:
1. `A`'s constructor
2. `B`'s constructor
3. `C`'s constructor

*(If these had print statements inside, the output would be: A, B, C)*
When `c` goes out of scope, destructors are called in the exact reverse order: `~C()`, `~B()`, `~A()`.

---

## 🟡 Medium

### 4. What is the diamond problem in C++? Show the code that causes it and the fix using virtual base classes.
The diamond problem occurs in multiple inheritance when a class inherits from two classes that both inherit from a common base class. This results in the most derived class having two distinct, separate copies of the base class members, leading to ambiguity and wasted memory.

**Problematic Code:**
```cpp
class A { public: int x; };
class B : public A {};
class C : public A {};
class D : public B, public C {}; 

int main() {
    D d;
    // d.x = 10; // Error! Ambiguous: is it B::A::x or C::A::x?
    d.B::x = 10; // Valid, but ugly.
}
```

**The Fix (Virtual Inheritance):**
Using `virtual` inheritance ensures only one shared instance of `A` is created.
```cpp
class A { public: int x; };
class B : virtual public A {}; // Note 'virtual'
class C : virtual public A {}; // Note 'virtual'
class D : public B, public C {};

int main() {
    D d;
    d.x = 10; // Valid! Only one 'x' exists.
}
```

### 5. What is `private` inheritance in C++? How does it differ from `public` inheritance? Give a use case.
- **`public` inheritance** models an IS-A relationship. Public and protected members of the base class remain public and protected in the derived class. A derived class pointer can be implicitly cast to a base class pointer.
- **`private` inheritance** models a HAS-A (implemented-in-terms-of) relationship. All public and protected members of the base class become `private` in the derived class. They are inaccessible from outside the derived class. A derived class pointer *cannot* be implicitly cast to a base class pointer.

**Use Case:** 
When you want to reuse the implementation of a base class but do not want to expose its interface, and you don't want the derived class to be treated as an instance of the base class. For example, implementing a `Stack` using a `Vector`. `private` inheritance allows you to use `Vector`'s methods internally, but outside users can't call `Vector` methods on your `Stack`. (Though composition is usually preferred over private inheritance).

### 6. What does `final` do in Java? In C++? Why is `java.lang.String` declared `final`?
- **Java:** 
  - On a class: `final class Foo {}` means the class cannot be subclassed (extended).
  - On a method: `final void bar() {}` means the method cannot be overridden by subclasses.
- **C++11:** 
  - On a class: `class Foo final {};` prevents derivation.
  - On a virtual method: `virtual void bar() final;` prevents further overriding in derived classes.

**Why is `java.lang.String` final?**
1. **Security:** Strings are used in critical operations (network connections, file paths, database URLs). If `String` could be subclassed, a malicious subclass could override methods to bypass security checks or mutate the string unexpectedly.
2. **Immutability & Caching:** Making it final ensures no subclass can break the immutability guarantee. This allows the JVM to safely cache string literals (String Pool) and cache the hashcode, which is crucial for using Strings as keys in HashMaps.

---

## 🔴 Hard

### 7. Given this C++ hierarchy:
```cpp
class A { public: virtual void f() { cout << "A"; } };
class B : virtual public A { public: void f() { cout << "B"; } };
class C : virtual public A { public: void f() { cout << "C"; } };
class D : public B, public C {};
```
**Does `D d; d.f();` compile? Why or why not? Fix it so it compiles and prints "D".**

**Answer:** No, it does not compile. 
Because `B` and `C` both override the virtual function `f()` from `A`, when `D` inherits from both `B` and `C`, the compiler doesn't know which overridden `f()` to use (the one from `B` or the one from `C`). The method resolution is ambiguous.

**The Fix:**
`D` must explicitly override the function to resolve the ambiguity.
```cpp
class D : public B, public C {
public:
    void f() override { cout << "D"; }
};
```
Now `D d; d.f();` compiles perfectly and prints "D".

### 8. Refactor this inheritance-based design to use composition:
```java
class Stack<T> extends ArrayList<T> {
    public void push(T item) { add(item); }
    public T pop() { return remove(size()-1); }
    // Problem: exposes get(), add(), remove(), set() from ArrayList
}
```
**Show the composition version and explain why it is better.**

**Composition Version:**
```java
class Stack<T> {
    private ArrayList<T> list = new ArrayList<>(); // Composition (HAS-A)

    public void push(T item) { 
        list.add(item); 
    }
    
    public T pop() { 
        if (list.isEmpty()) throw new EmptyStackException();
        return list.remove(list.size() - 1); 
    }
    
    public boolean isEmpty() {
        return list.isEmpty();
    }
}
```

**Why it is better:**
1. **Encapsulation:** The inheritance version violates Liskov Substitution Principle and encapsulation. A user of the inherited `Stack` could call `.clear()`, `.add(0, item)`, or `.remove(5)`, completely breaking the Last-In-First-Out (LIFO) invariant of a stack. Composition hides the `ArrayList` and exposes *only* the strictly necessary `push` and `pop` methods.
2. **Flexibility:** With composition, if you later decide that `LinkedList` is better than `ArrayList` for your internal implementation, you can change it without affecting any code that uses your `Stack` class. With inheritance, changing the base class breaks the public API.
