# Module 3: Inheritance and Composition

Inheritance is one of the foundational pillars of Object-Oriented Programming (OOP). It allows developers to define a new class based on an existing class, promoting code reuse, logical hierarchy, and polymorphism. However, when used incorrectly, inheritance can lead to rigid, fragile designs. 

In this module, we will explore the mechanisms of inheritance in C++ and Java, how to handle edge cases like the Diamond Problem, and when to eschew inheritance entirely in favor of Composition.

---

## 1. IS-A vs HAS-A Relationships

Before writing code, you must determine the logical relationship between your entities. The two primary relationships in object-oriented design are **IS-A** and **HAS-A**.

### The IS-A Relationship (Inheritance)
An IS-A relationship implies specialization. If entity B is a specialized version of entity A, then B **IS-A** A.
* A `Dog` IS-A `Animal`.
* A `Manager` IS-A `Employee`.
* A `CheckingAccount` IS-A `BankAccount`.

When a strict IS-A relationship exists, **Inheritance** is the appropriate tool. The derived class (child) inherits the state and behavior of the base class (parent).

### The HAS-A Relationship (Composition)
A HAS-A relationship implies containment or aggregation. If entity A uses entity B to perform its duties, or if entity A consists of entity B, then A **HAS-A** B.
* A `Car` HAS-A `Engine`.
* A `Person` HAS-A `Heart`.
* A `DatabaseConnection` HAS-A `Logger`.

When a HAS-A relationship exists, **Composition** (or Aggregation) is the appropriate tool. Instead of inheriting from a class, you create an instance of that class as a member variable.

### The Fragile Base Class Problem
Why not just use inheritance for everything? Because inheritance creates the strongest form of coupling in object-oriented programming. 

When class `B` inherits from class `A`, `B` becomes heavily dependent on the implementation details of `A`. If the author of `A` modifies a method, changes the behavior of a constructor, or adds new constraints, class `B` might silently break. This is known as the **Fragile Base Class Problem**. Because of this, modern software engineering favors composition over inheritance unless a strong, polymorphic IS-A relationship is strictly required.

---

## 2. Types of Inheritance

There are five primary topological arrangements for inheritance. Languages differ in which topologies they support.

```text
1. Single Inheritance       2. Multilevel Inheritance
      [A]                          [A]
       |                            |
      [B]                          [B]
                                    |
                                   [C]

3. Hierarchical             4. Multiple Inheritance
      [A]                       [A]     [B]
     /   \                        \     /
   [B]   [C]                        [C]

5. Hybrid Inheritance (The Diamond)
           [A]
          /   \
        [B]   [C]
          \   /
           [D]
```

### C++ Support
C++ is a highly permissive language and supports **all five** types of inheritance natively for classes. 

### Java Support
Java designers observed that Multiple and Hybrid inheritance often caused severe ambiguity (which we will see in the Diamond Problem). Consequently, Java restricts classes to **Single, Multilevel, and Hierarchical** inheritance. 
* A Java class can only `extend` exactly one other class. 
* To achieve multiple inheritance of behavior, Java allows a class to `implements` multiple `interfaces`.

---

## 3. C++ Inheritance Access Modifiers

In C++, when you inherit a class, you must specify an access modifier for the inheritance itself. This controls how the inherited members are exposed in the derived class.

```cpp
class Base {
public:    int pub;
protected: int prot;
private:   int priv;
};

// Public Inheritance
class DerivedPub : public Base {
    // pub remains public
    // prot remains protected
    // priv is inaccessible
};

// Protected Inheritance
class DerivedProt : protected Base {
    // pub becomes protected
    // prot remains protected
    // priv is inaccessible
};

// Private Inheritance
class DerivedPriv : private Base {
    // pub becomes private
    // prot becomes private
    // priv is inaccessible
};
```

### Access Modifier Inheritance Table

| Base Member Access | Inherited via `public` | Inherited via `protected` | Inherited via `private` |
| :--- | :--- | :--- | :--- |
| **`public`** | `public` | `protected` | `private` |
| **`protected`** | `protected` | `protected` | `private` |
| **`private`** | *Inaccessible* | *Inaccessible* | *Inaccessible* |

**Key Takeaways:**
* **`public` inheritance** represents IS-A. This is what you use 99% of the time.
* **`private` inheritance** represents HAS-A (implemented-in-terms-of). It is technically composition, implemented via the inheritance mechanism. You reuse the base code, but you do not expose it, and polymorphism (upcasting) is disabled.

---

## 4. Constructor and Destructor Chaining

When you instantiate a derived class object, the memory for the entire object (including the base class portion) is allocated. The constructors must run to initialize this memory.

### The Rule of Initialization
**Base classes are initialized before derived classes.** You cannot build the roof before you pour the foundation. 

### The Rule of Destruction
**Destructors are called in the exact reverse order of constructors.** (LIFO - Last In, First Out). The derived class is torn down before the base class.

### C++ Trace Example

```cpp
#include <iostream>

class Base {
public:
    Base() { std::cout << "Base Constructor\n"; }
    ~Base() { std::cout << "Base Destructor\n"; }
};

class Derived : public Base {
public:
    Derived() { std::cout << "Derived Constructor\n"; }
    ~Derived() { std::cout << "Derived Destructor\n"; }
};

int main() {
    std::cout << "--- Creating obj ---\n";
    Derived obj;
    std::cout << "--- Exiting main ---\n";
    return 0;
}
```

**Output:**
```text
--- Creating obj ---
Base Constructor
Derived Constructor
--- Exiting main ---
Derived Destructor
Base Destructor
```

Notice that C++ automatically calls the default `Base` constructor. If the `Base` class does not have a default constructor, the `Derived` constructor **must** explicitly call it using an initializer list:

```cpp
Derived(int x) : Base(x) { /* ... */ }
```

### Java Trace Example

In Java, the rule is the same, but the syntax differs. The first line of any constructor in a derived class must be a call to `super()`. If you don't write it, the Java compiler silently inserts a no-argument `super()` for you.

```java
class Base {
    public Base() {
        System.out.println("Base Constructor");
    }
}

class Derived extends Base {
    public Derived() {
        // super(); is implicitly inserted here by the compiler
        System.out.println("Derived Constructor");
    }
}
```

---

## 5. The Diamond Problem

The Diamond Problem occurs in systems that support multiple inheritance. It happens when a class inherits from two classes that both share a common base class.

### The Ambiguity in C++

```cpp
class Device {
public:
    int id;
};

class Printer : public Device {};
class Scanner : public Device {};

// Copier inherits from both Printer and Scanner
class Copier : public Printer, public Scanner {};

int main() {
    Copier c;
    // c.id = 10; // ERROR: Ambiguous!
    return 0;
}
```

**Why does this fail?**
Because of the memory layout. `Printer` contains a full copy of `Device`. `Scanner` contains a full copy of `Device`. Therefore, `Copier` literally has **two independent copies** of `id` in memory. Does `c.id` refer to the printer's ID or the scanner's ID? The compiler refuses to guess.

### The C++ Fix: Virtual Inheritance

C++ solves this with the `virtual` inheritance keyword. By making the intermediate classes inherit the base class virtually, you instruct the compiler to only instantiate **one shared instance** of the base class.

```cpp
class Device {
public:
    int id;
};

// Note the 'virtual' keyword
class Printer : virtual public Device {};
class Scanner : virtual public Device {};

class Copier : public Printer, public Scanner {};

int main() {
    Copier c;
    c.id = 10; // SUCCESS! There is only one 'id' now.
    return 0;
}
```

### How Java Avoids the Diamond Problem

Java sidesteps the structural diamond problem by forbidding multiple inheritance for classes. A class can never have two concrete parents.

However, Java 8 introduced `default` methods in interfaces, creating a behavioral diamond problem.

```java
interface Printer {
    default void powerOn() { System.out.println("Printer ON"); }
}

interface Scanner {
    default void powerOn() { System.out.println("Scanner ON"); }
}

// Does not compile!
class Copier implements Printer, Scanner {
}
```

**The Java Fix:**
Java forces the developer to explicitly override the conflicting method to resolve the ambiguity manually.

```java
class Copier implements Printer, Scanner {
    @Override
    public void powerOn() {
        // You can pick one, or write entirely new logic
        Printer.super.powerOn(); 
    }
}
```

---

## 6. Method Resolution Order (MRO)

When a method is called in a complex inheritance hierarchy, the language runtime must figure out exactly which version of the method to execute. This search path is the Method Resolution Order (MRO).

* **C++:** Uses a left-to-right Depth First Search (DFS). However, if there's ambiguity (like the diamond problem without `virtual`), it halts and throws a compile error.
* **Java:** Because of single inheritance, the MRO is a simple linear chain (bottom-up): start at the object's runtime class, check if the method exists. If not, go up to the parent, then grandparent, up to `Object`.
* **Python (Note):** Uses the C3 Linearization algorithm to create a predictable, monotonic MRO list for multiple inheritance, avoiding C++'s ambiguity issues at runtime.

---

## 7. The `final` Keyword

Sometimes, you write a class or a method that is perfect, complete, and highly sensitive. You do not want anyone to inherit from it or override its logic.

### Java `final`
* **`final` class:** Cannot be subclassed.
* **`final` method:** Cannot be overridden.

`java.lang.String` is a `final` class. This guarantees that strings are truly immutable. If a malicious developer could create a `MutatableString extends String`, they could bypass security checks in the JVM by changing the string contents after a security validation occurred.

### C++11 `final`
C++11 introduced the exact same semantics.

```cpp
class MathUtils final { // Cannot inherit from MathUtils
    // ...
};

class Base {
public:
    virtual void doWork() {}
};

class Derived : public Base {
public:
    // Cannot override doWork() in any class deriving from Derived
    void doWork() override final {} 
};
```

---

## 8. Covariant Return Types

Normally, when you override a method, the signature (including the return type) must match exactly. However, both C++ and Java support **Covariant Return Types**. This means an overridden method is allowed to return a type that is strictly *more derived* than the base class method's return type.

### C++ Example

```cpp
class Animal {};
class Dog : public Animal {};

class AnimalFactory {
public:
    virtual Animal* createAnimal() {
        return new Animal();
    }
};

class DogFactory : public AnimalFactory {
public:
    // Overriding, but returning a MORE SPECIFIC pointer
    Dog* createAnimal() override { 
        return new Dog();
    }
};
```

### Java Example

```java
class Animal {}
class Dog extends Animal {}

class AnimalFactory {
    public Animal createAnimal() {
        return new Animal();
    }
}

class DogFactory extends AnimalFactory {
    @Override
    public Dog createAnimal() { // Covariant return type
        return new Dog();
    }
}
```

Covariance makes APIs much cleaner, as callers using the derived factory don't have to manually cast the returned pointer/reference.

---

## 9. Composition over Inheritance

Let's conclude with a real-world design lesson. 

Suppose you are tasked with writing a `Stack` data structure. You know that a Stack is essentially a list where you only add and remove from the end. You decide to inherit from an existing list class (like `ArrayList` or `std::vector`) to save time.

### The Bad Design (Inheritance)

```java
import java.util.ArrayList;

class Stack<T> extends ArrayList<T> {
    public void push(T item) { 
        this.add(item); 
    }
    
    public T pop() { 
        return this.remove(this.size() - 1); 
    }
}
```

**Why is this terrible?**
Because a `Stack` IS NOT an `ArrayList`. By inheriting, you have exposed the entirely public API of `ArrayList` to the users of your `Stack`. 

```java
Stack<Integer> s = new Stack<>();
s.push(10);
s.push(20);
s.clear(); // Wait, Stacks shouldn't support clear()!
s.add(0, 99); // We just inserted at the bottom of the stack! LIFO invariant ruined!
```

### The Good Design (Composition)

Instead of inheriting, the `Stack` should *contain* an internal list. It **HAS-A** list to do its internal bookkeeping, but it strictly controls the public API.

```java
import java.util.ArrayList;

class Stack<T> {
    // Hidden implementation detail
    private ArrayList<T> list = new ArrayList<>(); 

    public void push(T item) { 
        list.add(item); 
    }
    
    public T pop() { 
        return list.remove(list.size() - 1); 
    }
    
    public boolean isEmpty() {
        return list.isEmpty();
    }
}
```

Now, the user can only call `push()`, `pop()`, and `isEmpty()`. The integrity of the Stack is preserved. Furthermore, if you decide later that a `LinkedList` would be faster for your Stack than an `ArrayList`, you can change the internal private member without breaking any code that consumes your `Stack` class. 

**Rule of Thumb:** Default to Composition. Only use Inheritance when you explicitly need polymorphism (the ability to pass a `Dog` to a function expecting an `Animal`).
