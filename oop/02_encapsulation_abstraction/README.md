# Module 2: Encapsulation & Abstraction

Welcome to Module 2 of the Object-Oriented Programming (OOP) curriculum. In this module, we will explore two fundamental pillars of OOP: **Encapsulation** and **Abstraction**. While they are often discussed together, they serve distinct purposes in software design. Understanding how and when to apply them is crucial for building robust, maintainable, and scalable systems.

---

## 1. Encapsulation

### 1.1 Definition
Encapsulation is the bundling of data (fields) and the behavior (methods) that operates on that data into a single unit, usually a class. More importantly, encapsulation involves restricting direct access to some of the object's components. This means the internal representation of an object is generally hidden from view outside of the object's definition.

### 1.2 Why It Matters
The primary goal of encapsulation is to protect the integrity of the data. By controlling how data is accessed and modified, we can enforce **invariants**. 

Consider a `BankAccount`. Its balance should never be negative, and deposits should always be positive amounts. If the `balance` field is public, any part of the program can arbitrarily change it, potentially violating these rules. Encapsulation ensures that all changes go through a controlled interface (methods), where validation logic can be applied.

Additionally, encapsulation reduces **coupling**. If the internal implementation of a class changes (e.g., changing how a list of items is stored internally), the external code that depends on the public interface of the class does not need to be updated.

### 1.3 Access Specifiers
Access specifiers control the visibility of class members.

**C++ Access Specifiers:**
- `private`: Members are accessible only from within other members of the same class (or from their "friends").
- `protected`: Members are accessible from members of their same class and from their derived classes.
- `public`: Members are accessible from anywhere where the object is visible.

```cpp
// C++ Visibility Example
class Base {
private:
    int privateData; // Only Base can access
protected:
    int protectedData; // Base and Derived can access
public:
    int publicData; // Anyone can access
};

class Derived : public Base {
    void doSomething() {
        // privateData = 10; // ERROR: Not accessible
        protectedData = 20; // OK
        publicData = 30; // OK
    }
};
```

**Java Access Specifiers:**
Java introduces a default visibility level, often called "package-private".

- `private`: Accessible only within the class.
- `package-private` (no keyword): Accessible within classes in the same package.
- `protected`: Accessible within classes in the same package and subclasses in other packages.
- `public`: Accessible from any class.

| Modifier | Class | Package | Subclass (diff package) | World |
| :--- | :---: | :---: | :---: | :---: |
| `public` | Y | Y | Y | Y |
| `protected` | Y | Y | Y | N |
| `no modifier` | Y | Y | N | N |
| `private` | Y | N | N | N |

### 1.4 Getters and Setters: The Good, The Bad, and The Anemic
Getters and setters (accessors and mutators) are often used to expose private fields. 

**When Helpful:**
- **Validation:** Ensuring a set value is valid before applying it.
- **Computed Properties:** Calculating a value on the fly rather than storing it.
- **Lazy Initialization:** Creating an object only when it is first requested.

**When Harmful:**
Blindly generating getters and setters for every field breaks encapsulation. If a class merely holds data and provides open access to it, it is not much better than a public `struct`.

#### The Anemic Domain Model Anti-Pattern
An anemic domain model occurs when classes have only data fields with getters and setters, and all the actual logic (behavior) that operates on that data is located outside the class, usually in "service" classes. This violates encapsulation because the object's state and behavior are separated.

#### The Law of Demeter
Also known as the "Principle of Least Knowledge", the Law of Demeter states that a unit should only talk to its immediate friends and not to strangers. In object-oriented terms, an object should not reach through another object to access a third object.

**Violation:**
```java
// Reaching through objects (Train Wreck)
customer.getWallet().getBankCard().charge(amount);
```
This implies the caller knows the internal structure of `Customer`, `Wallet`, and `BankCard`.

**Fix:**
```java
// Tell, Don't Ask
customer.charge(amount);
```
The caller asks the `Customer` to perform an action. How the `Customer` manages the charge internally (via a wallet or card) is encapsulated.

### 1.5 Friend Functions/Classes in C++
In C++, the `friend` keyword provides a justified escape hatch to encapsulation. A class can declare another function or class as a `friend`, granting it access to its `private` and `protected` members.

Why break encapsulation? Sometimes, two classes are tightly coupled by design, or you need to overload operators that are technically not members of the class.

```cpp
class Vector2D {
private:
    float x, y;
    
public:
    Vector2D(float x, float y) : x(x), y(y) {}
    
    // friend allows operator<< to access private x and y
    friend std::ostream& operator<<(std::ostream& os, const Vector2D& v);
};

std::ostream& operator<<(std::ostream& os, const Vector2D& v) {
    os << "(" << v.x << ", " << v.y << ")";
    return os;
}
```
While `friend` breaks encapsulation strictly speaking, it can improve overall design by avoiding public getter methods that expose internal state to the entire program just for the sake of one utility function.

---

## 2. Abstraction

### 2.1 Definition
Abstraction is the process of hiding the complex implementation details and showing only the essential features of the object. It focuses on the outside view of an object—WHAT it does, rather than HOW it does it.

### 2.2 Reducing Cognitive Load
By providing a simple interface, abstraction significantly reduces cognitive load for developers. When you drive a car, you use the steering wheel, pedals, and gear shifter. You do not need to understand the internal combustion engine, the fuel injection system, or the transmission gears. The car presents an abstraction of driving.

### 2.3 Abstraction vs. Encapsulation
These terms are often confused, but they address different concerns:
- **Encapsulation = Hiding Data.** It is a mechanism of wrapping the data and code acting on the data together as a single unit, keeping both safe from outside interference. It's about security, integrity, and preventing unauthorized access.
- **Abstraction = Hiding Implementation.** It is the process of hiding the working details and providing only essential information to the user. It's about reducing complexity and exposing a clean interface.

They complement each other: encapsulation enables abstraction by hiding the state and internal mechanisms, while abstraction defines the public interface that encapsulation protects.

---

## 3. Abstract Classes

Abstract classes serve as blueprints for other classes. They define a common interface and potentially some shared implementation, but they cannot be instantiated directly.

### 3.1 C++ Abstract Classes
In C++, an abstract class is any class containing at least one **pure virtual function**. A pure virtual function is specified by placing `= 0` at the end of its declaration. Subclasses MUST implement these pure virtual functions to become concrete classes that can be instantiated.

```cpp
#include <iostream>
#include <string>

// Abstract Class in C++
class Shape {
protected:
    std::string color;
    
public:
    Shape(std::string c) : color(c) {}
    virtual ~Shape() = default; // Essential for polymorphic deletion
    
    // Pure virtual function makes Shape abstract
    virtual double area() const = 0; 
    
    // Concrete method
    void printInfo() const {
        std::cout << "Shape color: " << color << ", Area: " << area() << std::endl;
    }
};

class Circle : public Shape {
private:
    double radius;
    
public:
    Circle(std::string c, double r) : Shape(c), radius(r) {}
    
    // Implementing pure virtual function
    double area() const override {
        return 3.14159 * radius * radius;
    }
};
```

### 3.2 Java Abstract Classes
In Java, the `abstract` keyword explicitly marks a class or method as abstract.

```java
// Abstract Class in Java
public abstract class Shape {
    protected String color;
    
    public Shape(String color) {
        this.color = color;
    }
    
    // Abstract method
    public abstract double area();
    
    // Concrete method
    public void printInfo() {
        System.out.println("Shape color: " + color + ", Area: " + area());
    }
}

public class Circle extends Shape {
    private double radius;
    
    public Circle(String color, double radius) {
        super(color);
        this.radius = radius;
    }
    
    @Override
    public double area() {
        return Math.PI * radius * radius;
    }
}
```

---

## 4. Interfaces

An interface defines a contract. It specifies a set of methods that implementing classes must provide, but traditionally provides no implementation itself.

### 4.1 C++ Interface Idiom
C++ does not have an explicit `interface` keyword. Instead, an interface is typically implemented as a **pure abstract class**—a class where ALL methods are pure virtual, and there are no data members.

```cpp
// C++ Interface Idiom
class ISerializable {
public:
    virtual ~ISerializable() = default;
    
    // All methods are pure virtual
    virtual std::string serialize() const = 0;
    virtual void deserialize(const std::string& data) = 0;
};
```

### 4.2 Java Interfaces
Java has first-class support for interfaces.
- Methods are implicitly `public abstract` (though Java 8+ added features).
- No instance state is allowed (only `public static final` constants).
- A class can implement multiple interfaces, circumventing Java's single-inheritance rule.

**Java 8+ Additions:**
- `default` methods: Provide a concrete implementation within the interface itself. Useful for adding new methods to interfaces without breaking existing implementations.
- `static` methods: Utility methods tied to the interface.

```java
public interface Drawable {
    void draw(); // implicitly public abstract
    
    // Java 8 default method
    default void clear() {
        System.out.println("Clearing drawing area.");
    }
}

public interface Resizable {
    void resize(double factor);
}

// Implementing multiple interfaces
public class Circle implements Drawable, Resizable {
    public void draw() {
        System.out.println("Drawing a circle");
    }
    
    public void resize(double factor) {
        System.out.println("Resizing by " + factor);
    }
}
```

---

## 5. Abstract Class vs. Interface: When to Use Each

Understanding when to choose an abstract class versus an interface is a key design skill.

### Decision Matrix

| Feature | Abstract Class | Interface |
| :--- | :--- | :--- |
| **Relationship** | Defines an "IS-A" relationship. | Defines a "CAN-DO" or contract relationship. |
| **State (Fields)** | Can hold instance variables (state). | Cannot hold instance state (Java: only constants). |
| **Implementation** | Can have implemented methods. | Traditionally none (Java 8 `default` methods are an exception). |
| **Constructors** | Can have constructors. | No constructors. |
| **Multiple Inheritance**| Single inheritance only (Java). | Can implement multiple interfaces (Java). |
| **Best Used For...** | Sharing code, state, and identity among closely related classes. | Defining a common role or contract for disparate classes. |

*Note: In C++, you can use multiple inheritance with abstract classes, blurring these lines slightly, but conceptually the distinction between an abstract base class (IS-A) and an interface class (CAN-DO) remains powerful.*

### Practical Guidelines
1. **Use an Interface** if you want to define a contract that unrelated classes can implement (e.g., `Comparable`, `Runnable`, `ISerializable`).
2. **Use an Abstract Class** if you want to provide common implementation details and state to a group of closely related subclasses (e.g., `Shape`, `Vehicle`, `Animal`).

---

## 6. Real-World Design Example: Payment Processing

Let's design a payment processing system that leverages both interfaces and abstract classes to achieve flexibility and extensibility.

### The Design
1. **`IPaymentProcessor` (Interface):** Defines the strict contract all processors must follow.
2. **`AbstractPaymentProcessor` (Abstract Class):** Implements the interface and provides common validation logic and logging, reducing code duplication.
3. **`StripeProcessor`, `PayPalProcessor` (Concrete Classes):** Provide the specific integration details.

### Java Implementation

```java
// 1. The Interface (The Contract)
public interface IPaymentProcessor {
    boolean processPayment(double amount);
    boolean refund(String transactionId);
}

// 2. The Abstract Class (Shared Code)
public abstract class AbstractPaymentProcessor implements IPaymentProcessor {
    protected String apiKey;
    
    public AbstractPaymentProcessor(String apiKey) {
        this.apiKey = apiKey;
    }
    
    // Shared common logic
    protected boolean validateAmount(double amount) {
        if (amount <= 0) {
            System.err.println("Validation failed: Amount must be positive.");
            return false;
        }
        return true;
    }
    
    protected void logTransaction(String type, double amount) {
        System.out.println("LOG: " + type + " of $" + amount);
    }
}

// 3. Concrete Implementations
public class StripeProcessor extends AbstractPaymentProcessor {
    
    public StripeProcessor(String apiKey) {
        super(apiKey);
    }
    
    @Override
    public boolean processPayment(double amount) {
        if (!validateAmount(amount)) return false;
        
        System.out.println("Processing $" + amount + " via Stripe API.");
        logTransaction("Charge", amount);
        return true;
    }
    
    @Override
    public boolean refund(String transactionId) {
        System.out.println("Refunding transaction " + transactionId + " via Stripe.");
        return true;
    }
}

public class PayPalProcessor extends AbstractPaymentProcessor {
    
    public PayPalProcessor(String apiKey) {
        super(apiKey);
    }
    
    @Override
    public boolean processPayment(double amount) {
        if (!validateAmount(amount)) return false;
        
        System.out.println("Processing $" + amount + " via PayPal API.");
        logTransaction("Charge", amount);
        return true;
    }
    
    @Override
    public boolean refund(String transactionId) {
        System.out.println("Refunding transaction " + transactionId + " via PayPal.");
        return true;
    }
}
```

### The Power of this Design (Open/Closed Principle)
This architecture adheres to the **Open/Closed Principle (OCP)**: software entities should be open for extension, but closed for modification.

If we need to add a new `CryptoProcessor`, we create a new class extending `AbstractPaymentProcessor`. We do not need to modify the existing `StripeProcessor`, `PayPalProcessor`, or the client code that depends on the `IPaymentProcessor` interface. The system naturally accommodates new requirements without breaking existing functionality.
