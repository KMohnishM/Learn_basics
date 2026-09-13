# Module 2 Q&A: Encapsulation & Abstraction

## 🟢 Easy

### 1. What is encapsulation? Give a real-world analogy. What problem does it solve?
**Answer:**
Encapsulation is the bundling of data (attributes/fields) and the methods (behavior) that operate on that data into a single unit (a class), and restricting direct access to the internal state of that object.

**Real-world analogy:** A capsule containing medicine. The medicine (data) is hidden and protected inside the capsule shell (methods). Another analogy is a car's engine. You start the car using the ignition button (public method), but you cannot directly interfere with the fuel injection or spark plugs (private data/internal methods).

**Problem it solves:** It protects an object's internal state from unintended or unauthorized modifications from outside, thereby ensuring data integrity and enforcing business rules (invariants).

### 2. What are the access specifiers in C++ and Java? What is Java's package-private visibility?
**Answer:**
**C++:**
- `private`: Accessible only within the same class.
- `protected`: Accessible within the same class and derived classes.
- `public`: Accessible from anywhere.

**Java:**
- `private`: Accessible only within the same class.
- `protected`: Accessible within the same package, and subclasses in different packages.
- `public`: Accessible from anywhere.
- **Package-private (default):** When no keyword is used, the member is accessible to any class within the same package, but not to classes outside the package, even if they are subclasses.

### 3. What is the difference between abstraction and encapsulation? Why are they often confused?
**Answer:**
- **Encapsulation** is about **hiding data**. It protects the internal state of an object and dictates how that state can be manipulated.
- **Abstraction** is about **hiding implementation complexity**. It exposes only the essential features and capabilities of an object to the outside world, hiding how those capabilities are actually implemented under the hood.

They are often confused because they both involve "hiding" something. Encapsulation hides the *state* (the variables), while abstraction hides the *process* (the implementation details). Encapsulation is a technique that enables abstraction.

---

## 🟡 Medium

### 4. Compare abstract class vs interface in both C++ and Java. When would you choose each? Give a concrete example.
**Answer:**
- **Abstract Class:** Represents an "IS-A" relationship. Can contain instance variables (state), constructors, and concrete implemented methods alongside abstract methods.
- **Interface:** Represents a "CAN-DO" or contract relationship. Traditionally contains no state and no implementation (just method signatures).

**When to choose:**
- Use an **Abstract Class** when classes share a core identity and common behavior/state that you want to reuse (e.g., `Animal` abstract class with a shared `age` field and `eat()` implementation).
- Use an **Interface** when disparate, unrelated classes need to guarantee they support a certain behavior (e.g., `ISerializable` implemented by both `User` and `NetworkConfig`).

**C++ vs Java:**
- In Java, the distinction is enforced by the language (`abstract class` vs `interface`). A class can extend only one abstract class but implement multiple interfaces.
- In C++, there is no explicit `interface` keyword. An interface is simulated using a "pure abstract class" where all methods are pure virtual (`= 0`) and there is no state. C++ supports multiple inheritance, allowing a class to inherit from multiple abstract classes directly.

### 5. What is the Law of Demeter? Show a code example of a violation and its fix.
**Answer:**
The Law of Demeter (LoD), or "Principle of Least Knowledge", states that an object should only communicate with its immediate neighbors and not reach deep into other objects' internal structures ("don't talk to strangers").

**Violation (Train Wreck):**
```java
public void printCustomerZipCode(Order order) {
    // Reaching through Order to get Customer, then to get Address, to get zip
    String zip = order.getCustomer().getAddress().getZipCode();
    System.out.println(zip);
}
```
This couples the caller tightly to the internal structures of `Order`, `Customer`, and `Address`.

**Fix (Tell, Don't Ask):**
```java
public void printCustomerZipCode(Order order) {
    // Delegate the responsibility
    String zip = order.getCustomerZipCode();
    System.out.println(zip);
}

// Inside Order class:
public String getCustomerZipCode() {
    return this.customer.getZipCode();
}

// Inside Customer class:
public String getZipCode() {
    return this.address.getZipCode();
}
```

### 6. Why can Java classes implement multiple interfaces but only extend one class? What problem does this solve?
**Answer:**
Java restricts classes to single inheritance of state (extending one class) to avoid the **Diamond Problem**. If a class could inherit from two classes that both defined the same method or state variable, the compiler wouldn't know which one to use.

Interfaces, traditionally having no implementation or state, don't suffer from the Diamond Problem. If a class implements two interfaces that declare the same method signature, there is no conflict because there is only one implementation provided by the concrete class itself. Thus, allowing multiple interfaces provides flexibility without the ambiguity of multiple inheritance of state.

---

## 🔴 Hard

### 7. Design a `Shape` abstract hierarchy in both C++ and Java with `area()` and `perimeter()` methods. Show polymorphic usage.

**Answer:**

**C++ Implementation:**
```cpp
#include <iostream>
#include <vector>

// Abstract Base Class
class Shape {
public:
    virtual ~Shape() = default;
    virtual double area() const = 0;
    virtual double perimeter() const = 0;
};

class Circle : public Shape {
    double radius;
public:
    Circle(double r) : radius(r) {}
    double area() const override { return 3.14159 * radius * radius; }
    double perimeter() const override { return 2 * 3.14159 * radius; }
};

class Rectangle : public Shape {
    double w, h;
public:
    Rectangle(double w, double h) : w(w), h(h) {}
    double area() const override { return w * h; }
    double perimeter() const override { return 2 * (w + h); }
};

int main() {
    // Polymorphic usage
    std::vector<Shape*> shapes;
    shapes.push_back(new Circle(5.0));
    shapes.push_back(new Rectangle(4.0, 6.0));

    for (Shape* s : shapes) {
        std::cout << "Area: " << s->area() << "\n";
        delete s;
    }
    return 0;
}
```

**Java Implementation:**
```java
import java.util.List;
import java.util.ArrayList;

// Abstract Class
abstract class Shape {
    public abstract double area();
    public abstract double perimeter();
}

class Circle extends Shape {
    private double radius;
    public Circle(double radius) { this.radius = radius; }
    
    @Override
    public double area() { return Math.PI * radius * radius; }
    
    @Override
    public double perimeter() { return 2 * Math.PI * radius; }
}

class Rectangle extends Shape {
    private double w, h;
    public Rectangle(double w, double h) { this.w = w; this.h = h; }
    
    @Override
    public double area() { return w * h; }
    
    @Override
    public double perimeter() { return 2 * (w + h); }
}

public class Main {
    public static void main(String[] args) {
        // Polymorphic usage
        List<Shape> shapes = new ArrayList<>();
        shapes.add(new Circle(5.0));
        shapes.add(new Rectangle(4.0, 6.0));

        for (Shape s : shapes) {
            System.out.println("Area: " + s.area());
        }
    }
}
```

### 8. Show a real example where getters/setters make encapsulation WORSE. Refactor the design to fix it.
**Answer:**
Blindly providing setters can violate class invariants and the Liskov Substitution Principle (LSP). Consider a `Rectangle` class:

**Bad Encapsulation:**
```java
class Rectangle {
    protected int width;
    protected int height;

    public void setWidth(int w) { this.width = w; }
    public void setHeight(int h) { this.height = h; }
    public int getArea() { return width * height; }
}

// Now imagine a Square extending Rectangle
class Square extends Rectangle {
    @Override
    public void setWidth(int w) {
        this.width = w;
        this.height = w; // Force square invariant
    }
    @Override
    public void setHeight(int h) {
        this.width = h;
        this.height = h; // Force square invariant
    }
}
```
If a client has a reference to `Rectangle r`, and calls `r.setWidth(5); r.setHeight(10);`, they expect `getArea()` to be `50`. But if `r` is actually a `Square`, the area will be `100`. The setters made encapsulation worse by allowing external state mutation that breaks mathematical invariants.

**Refactored Design (Immutability):**
Instead of setters, make the objects immutable and remove the setters.

```java
// Interfaces define contract, no mutable state
interface Shape {
    int getArea();
}

class Rectangle implements Shape {
    private final int width;
    private final int height;

    public Rectangle(int width, int height) {
        this.width = width;
        this.height = height;
    }
    public int getArea() { return width * height; }
}

class Square implements Shape {
    private final int side;

    public Square(int side) {
        this.side = side;
    }
    public int getArea() { return side * side; }
}
```
By removing setters and making fields `private final`, encapsulation is strong, invariants are preserved at construction time, and unexpected behavior is prevented.
