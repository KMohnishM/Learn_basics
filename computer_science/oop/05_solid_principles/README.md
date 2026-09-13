# Module 5: SOLID Principles

## Table of Contents
1. [Introduction: Why SOLID?](#introduction-why-solid)
2. [S — Single Responsibility Principle (SRP)](#s--single-responsibility-principle-srp)
3. [O — Open/Closed Principle (OCP)](#o--openclosed-principle-ocp)
4. [L — Liskov Substitution Principle (LSP)](#l--liskov-substitution-principle-lsp)
5. [I — Interface Segregation Principle (ISP)](#i--interface-segregation-principle-isp)
6. [D — Dependency Inversion Principle (DIP)](#d--dependency-inversion-principle-dip)

---

## Introduction: Why SOLID?

In the lifecycle of a software system, maintenance often consumes far more resources than the initial development. As systems evolve, poorly designed architectures succumb to "software rot." The **cost of bad design** manifests in three primary ways:

1. **Rigidity**: The system is hard to change because a single modification triggers a cascade of dependent changes across multiple modules.
2. **Fragility**: The system breaks in unexpected places when a change is made, often in areas conceptually unrelated to the modification.
3. **Immobility**: Code is inextricably intertwined, making it impossibly difficult to disentangle and reuse components in other applications.

The **SOLID principles** are a set of five object-oriented design guidelines intended to combat these issues. Coined as an acronym by **Michael Feathers** and originally promoted by **Robert C. Martin (Uncle Bob)**, these principles help engineers build software that is robust, maintainable, and adaptable.

---

## S — Single Responsibility Principle (SRP)

### Definition
*"A class should have one and only one reason to change."*

A "reason to change" directly correlates to a specific concern or stakeholder in the business domain. If a class assumes multiple responsibilities, it couples those responsibilities. Changes to one responsibility can impair or break the others.

### How to Detect an SRP Violation
- **Multiple Axes of Change**: Does a change in the database schema require modifying the same class as a change in the UI formatting?
- **The "And" Test**: If the class description requires the word "and" (e.g., "This class manages user data *and* sends emails"), it likely violates SRP.
- **Low Cohesion**: Methods in the class operate on disjoint sets of fields.

### The Violation (Java)
Consider a `User` class that handles domain logic, database persistence, and email notification. 

```java
// VIOLATION: The User class has three reasons to change:
// 1. Database schema changes (DBA stakeholder)
// 2. Email format changes (Marketing/Email team)
// 3. Discount logic changes (Pricing/Sales team)

public class User {
    private String username;
    private String email;
    private double totalPurchases;

    public User(String username, String email) {
        this.username = username;
        this.email = email;
    }

    // Responsibility 1: Business Logic
    public void calculateDiscount() {
        if (totalPurchases > 1000) {
            System.out.println("Applying 10% discount");
        }
    }

    // Responsibility 2: Persistence (Data Access)
    public void saveToDatabase() {
        System.out.println("Connecting to DB...");
        System.out.println("Executing INSERT INTO users...");
    }

    // Responsibility 3: Communication
    public void sendWelcomeEmail() {
        System.out.println("Connecting to SMTP server...");
        System.out.println("Sending welcome email to " + email);
    }
}
```

### The Fix
Refactor the responsibilities into separate classes. The `User` class becomes a pure domain object (data structure), while external services handle behavior.

```java
// FIX: Separated into highly cohesive, single-purpose classes.

// 1. Pure Domain Model
public class User {
    private String username;
    private String email;
    private double totalPurchases;

    // Getters, Setters, Constructor...
    public double getTotalPurchases() { return totalPurchases; }
    public String getEmail() { return email; }
}

// 2. Pricing Responsibility
public class PricingService {
    public void calculateDiscount(User user) {
        if (user.getTotalPurchases() > 1000) {
            System.out.println("Applying 10% discount");
        }
    }
}

// 3. Persistence Responsibility
public class UserRepository {
    public void save(User user) {
        System.out.println("Connecting to DB...");
        System.out.println("Executing INSERT INTO users...");
    }
}

// 4. Communication Responsibility
public class EmailService {
    public void sendWelcomeEmail(User user) {
        System.out.println("Connecting to SMTP server...");
        System.out.println("Sending welcome email to " + user.getEmail());
    }
}
```

---

## O — Open/Closed Principle (OCP)

### Definition
*"Software entities (classes, modules, functions, etc.) should be open for extension, but closed for modification."*

When business requirements change, you should be able to add new functionality by writing **new code** rather than changing **existing, working code**. This minimizes the risk of introducing bugs into tested systems.

### Extension Mechanisms
- Interfaces / Abstract Classes (Polymorphism)
- Strategy Pattern
- Template Method Pattern
- Decorator Pattern

### The Violation (Java)
An `AreaCalculator` that uses conditional statements to check the type of shape.

```java
// VIOLATION: Adding a new shape (e.g., Triangle) requires modifying AreaCalculator.
// AreaCalculator is NOT closed for modification.

public class Rectangle {
    public double width;
    public double height;
}

public class Circle {
    public double radius;
}

public class AreaCalculator {
    public double calculateTotalArea(Object[] shapes) {
        double totalArea = 0;
        for (Object shape : shapes) {
            if (shape instanceof Rectangle) {
                Rectangle r = (Rectangle) shape;
                totalArea += r.width * r.height;
            } else if (shape instanceof Circle) {
                Circle c = (Circle) shape;
                totalArea += Math.PI * c.radius * c.radius;
            }
            // A new 'else if' is required for every new shape!
        }
        return totalArea;
    }
}
```

### The Fix
Extract the `area()` calculation into a shared interface. The `AreaCalculator` depends on the abstraction.

```java
// FIX: Open for extension, closed for modification.

// 1. The Abstraction
public interface Shape {
    double area();
}

// 2. Extensions (New classes, no modification to existing ones)
public class Rectangle implements Shape {
    private double width;
    private double height;
    
    public Rectangle(double width, double height) {
        this.width = width;
        this.height = height;
    }
    
    @Override
    public double area() {
        return width * height;
    }
}

public class Circle implements Shape {
    private double radius;
    
    public Circle(double radius) {
        this.radius = radius;
    }
    
    @Override
    public double area() {
        return Math.PI * radius * radius;
    }
}

// Now we can add Triangle without touching AreaCalculator
public class Triangle implements Shape {
    private double base, height;
    // ... constructor ...
    @Override
    public double area() { return 0.5 * base * height; }
}

// 3. The Calculator (Closed for modification)
public class AreaCalculator {
    public double calculateTotalArea(Shape[] shapes) {
        double totalArea = 0;
        for (Shape shape : shapes) {
            totalArea += shape.area(); // Polymorphic dispatch
        }
        return totalArea;
    }
}
```

---

## L — Liskov Substitution Principle (LSP)

### Definition
*"Objects of a subtype must be substitutable for objects of their supertype without altering the correctness of the program."*

Inheritance ("IS-A") is often overused. If a subclass alters the expected behavior of the base class, it violates LSP. 

### Formal Rules
To adhere to LSP, a subclass must obey the design contract of its base class:
1. **Preconditions cannot be strengthened**: The subclass cannot require *more* restrictive input than the parent.
2. **Postconditions cannot be weakened**: The subclass cannot guarantee *less* about its output/state than the parent.
3. **Invariants must be preserved**: Fundamental conditions that hold true in the parent must hold true in the child.

### The Classic Violation: Square extends Rectangle
In mathematics, a Square *is-a* Rectangle. In OOP behavior, it is not, because they have conflicting invariants.

- **Rectangle Invariant**: `setWidth(w)` changes width but leaves height alone.
- **Square Invariant**: `width` must always equal `height`.

```java
// VIOLATION: Square breaks Rectangle's invariant.

public class Rectangle {
    protected int width;
    protected int height;

    public void setWidth(int width) { this.width = width; }
    public void setHeight(int height) { this.height = height; }
    public int getArea() { return width * height; }
}

public class Square extends Rectangle {
    // To maintain Square's invariant, we must override setters
    @Override
    public void setWidth(int width) {
        this.width = width;
        this.height = width; // Forced side-effect!
    }

    @Override
    public void setHeight(int height) {
        this.height = height;
        this.width = height; // Forced side-effect!
    }
}

// CLIENT CODE that breaks
public class TestRunner {
    public static void resize(Rectangle rect) {
        rect.setWidth(5);
        rect.setHeight(10);
        
        // Developer assumes a Rectangle's area is 5 * 10 = 50.
        // If rect is a Square, setHeight(10) changed BOTH width and height.
        // Area will be 100. The assertion FAILS.
        assert rect.getArea() == 50 : "LSP Violation!"; 
    }
}
```

### The Fix
Remove the inheritance relationship. `Square` and `Rectangle` are distinct shapes. They can share a common abstract interface `Shape`, but neither inherits the mutators of the other.

```java
// FIX: Decouple inheritance. Share an immutable abstraction.
public interface Shape {
    int getArea();
}

public class Rectangle implements Shape {
    private int width;
    private int height;
    
    public Rectangle(int width, int height) {
        this.width = width;
        this.height = height;
    }
    // Setters allowed, but no unexpected side-effects
    public void setWidth(int width) { this.width = width; }
    public void setHeight(int height) { this.height = height; }
    
    @Override
    public int getArea() { return width * height; }
}

public class Square implements Shape {
    private int side;
    
    public Square(int side) { this.side = side; }
    public void setSide(int side) { this.side = side; }
    
    @Override
    public int getArea() { return side * side; }
}
```
*Note on another common LSP violation*: Creating a `ReadOnlyList extends ArrayList` and overriding `add()` to throw an `UnsupportedOperationException`. The base `ArrayList` contract says `add()` inserts an element. Throwing an exception breaks the parent's postcondition.

---

## I — Interface Segregation Principle (ISP)

### Definition
*"No client should be forced to depend on methods it does not use."*

Fat or "polluted" interfaces force implementing classes to provide dummy implementations or throw exceptions for methods they don't support. ISP states that it's better to have many small, highly cohesive, client-specific interfaces than one massive, general-purpose interface.

*(ISP violations often indicate an SRP violation in the interface design itself.)*

### The Violation (Java)
A bloated `IWorker` interface.

```java
// VIOLATION: Fat interface forces unnecessary dependencies.
public interface IWorker {
    void work();
    void eat();
    void sleep();
}

public class HumanWorker implements IWorker {
    public void work() { System.out.println("Working..."); }
    public void eat() { System.out.println("Eating lunch..."); }
    public void sleep() { System.out.println("Sleeping..."); }
}

// RobotWorker does not eat or sleep, but is forced to implement them.
public class RobotWorker implements IWorker {
    public void work() { System.out.println("Processing tasks..."); }
    
    public void eat() {
        throw new UnsupportedOperationException("Robots don't eat");
    }
    
    public void sleep() {
        throw new UnsupportedOperationException("Robots don't sleep");
    }
}
```

### The Fix
Segregate the interface based on capabilities.

```java
// FIX: Segregated, role-specific interfaces.
public interface IWorkable {
    void work();
}

public interface IFeedable {
    void eat();
}

public interface ISleepable {
    void sleep();
}

// Human implements all required interfaces
public class HumanWorker implements IWorkable, IFeedable, ISleepable {
    public void work() { System.out.println("Working..."); }
    public void eat() { System.out.println("Eating lunch..."); }
    public void sleep() { System.out.println("Sleeping..."); }
}

// Robot only implements what it can actually do
public class RobotWorker implements IWorkable {
    public void work() { System.out.println("Processing tasks..."); }
}
```

---

## D — Dependency Inversion Principle (DIP)

### Definition
*"High-level modules should not depend on low-level modules. Both should depend on abstractions. Abstractions should not depend on details. Details should depend on abstractions."*

Traditional top-down design results in high-level business logic depending directly on low-level utility/infrastructure components (e.g., a specific database or API). DIP inverts this dependency graph. 

### The Violation (Java)
`OrderService` (high-level) directly instantiates `MySQLDatabase` (low-level detail).

```java
// VIOLATION: Tightly coupled to a specific database implementation.

public class MySQLDatabase {
    public void insert(Order order) {
        System.out.println("Saving order to MySQL...");
    }
}

public class OrderService {
    // Hardcoded dependency. Cannot be mocked for unit testing.
    // Cannot be swapped to PostgreSQL without modifying OrderService.
    private MySQLDatabase db = new MySQLDatabase();

    public void processOrder(Order order) {
        db.insert(order);
    }
}
```

### The Fix: Dependency Injection (DI)
We introduce an interface (`IDatabase`), and `OrderService` depends on that interface. The concrete implementation is "injected" from the outside.

```java
// FIX: Depend on abstractions. Inject the dependency.

// 1. The Abstraction
public interface IDatabase {
    void insert(Order order);
}

// 2. Low-level modules depend on the abstraction
public class MySQLDatabase implements IDatabase {
    public void insert(Order order) { System.out.println("Saving to MySQL"); }
}

public class PostgresDatabase implements IDatabase {
    public void insert(Order order) { System.out.println("Saving to PostgreSQL"); }
}
```

### Types of Dependency Injection
Once DIP is applied, we must deliver the dependency to the high-level class.

#### 1. Constructor Injection (Preferred)
Dependencies are provided through the constructor. This guarantees the object is fully initialized and immutable.

```java
public class OrderService {
    private final IDatabase db;

    // Injected via constructor
    public OrderService(IDatabase db) {
        this.db = db;
    }

    public void processOrder(Order order) {
        db.insert(order);
    }
}
```

#### 2. Setter Injection
Dependencies are provided via setter methods. Useful for optional dependencies or circular dependencies.

```java
public class OrderService {
    private IDatabase db;

    // Injected via setter
    public void setDatabase(IDatabase db) {
        this.db = db;
    }
}
```

#### 3. Method Injection
The dependency is provided directly to the method that needs it, rather than being stored as a class field.

```java
public class OrderService {
    // Injected via method parameter
    public void processOrder(Order order, IDatabase db) {
        db.insert(order);
    }
}
```

### Inversion of Control (IoC) Containers
In large applications, manually wiring dependencies (`new OrderService(new PostgresDatabase())`) becomes tedious. IoC containers automate this by resolving and injecting dependencies automatically.
- **Java**: Spring Framework (using `@Autowired`), Google Guice
- **C++**: Boost.DI
- **C#**: Microsoft.Extensions.DependencyInjection
