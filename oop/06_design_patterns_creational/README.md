# Module 6: Creational Design Patterns

## Introduction to the Gang of Four (GoF) Patterns

Design patterns provide general, reusable solutions to commonly occurring problems in software design. The concept was popularized by the influential 1994 book *"Design Patterns: Elements of Reusable Object-Oriented Software"*, written by the **Gang of Four (GoF)**: Erich Gamma, Richard Helm, Ralph Johnson, and John Vlissides.

The GoF book defines **23 design patterns**, categorized into three groups based on their purpose:

1.  **Creational Patterns (5):** Abstract the instantiation process, making systems independent of how their objects are created, composed, and represented.
2.  **Structural Patterns (7):** Deal with how classes and objects are composed to form larger structures.
3.  **Behavioral Patterns (11):** Focus on algorithms and the assignment of responsibilities between objects.

This module focuses exclusively on the **Creational Patterns**.

---

## 1. Singleton

**Intent:** Ensure a class has exactly one instance and provide a global point of access to it.

The Singleton pattern restricts the instantiation of a class to a single object. This is useful when exactly one object is needed to coordinate actions across the system.

### Structure

```
+---------------------------------------+
|              Singleton                |
+---------------------------------------+
| - static instance: Singleton*         |
| - Singleton()                         |  <-- Private constructor
+---------------------------------------+
| + static getInstance(): Singleton*    |  <-- Public accessor
| + doSomething()                       |
+---------------------------------------+
```

### C++ Implementation

#### Naive Approach (Not Thread-Safe)

```cpp
class Singleton {
private:
    static Singleton* instance;
    
    // Private constructor prevents direct instantiation
    Singleton() { std::cout << "Singleton initialized\n"; }
    
    // Delete copy constructor and assignment operator
    Singleton(const Singleton&) = delete;
    Singleton& operator=(const Singleton&) = delete;

public:
    static Singleton* getInstance() {
        if (instance == nullptr) {
            instance = new Singleton(); // Race condition here!
        }
        return instance;
    }
};

Singleton* Singleton::instance = nullptr;
```

#### Thread-Safe Approaches

**Option 1: Mutex with Double-Checked Locking (DCL)**

The naive fix is to lock the entire `getInstance()` method, but that's slow. Double-checked locking optimizes this, but without atomic variables, memory ordering issues can still break it.

```cpp
#include <mutex>
#include <atomic>

class ThreadSafeSingletonDCL {
private:
    static std::atomic<ThreadSafeSingletonDCL*> instance;
    static std::mutex mtx;

    ThreadSafeSingletonDCL() {}
    ThreadSafeSingletonDCL(const ThreadSafeSingletonDCL&) = delete;
    ThreadSafeSingletonDCL& operator=(const ThreadSafeSingletonDCL&) = delete;

public:
    static ThreadSafeSingletonDCL* getInstance() {
        ThreadSafeSingletonDCL* tmp = instance.load(std::memory_order_acquire);
        if (tmp == nullptr) {
            std::lock_guard<std::mutex> lock(mtx);
            tmp = instance.load(std::memory_order_relaxed);
            if (tmp == nullptr) {
                tmp = new ThreadSafeSingletonDCL();
                instance.store(tmp, std::memory_order_release);
            }
        }
        return tmp;
    }
};

std::atomic<ThreadSafeSingletonDCL*> ThreadSafeSingletonDCL::instance{nullptr};
std::mutex ThreadSafeSingletonDCL::mtx;
```

**Option 2: Meyers Singleton (Preferred since C++11)**

C++11 guarantees that the initialization of block-scope static variables is thread-safe. This makes the Meyers Singleton the cleanest and most efficient approach in modern C++.

```cpp
class MeyersSingleton {
private:
    MeyersSingleton() {}
    MeyersSingleton(const MeyersSingleton&) = delete;
    MeyersSingleton& operator=(const MeyersSingleton&) = delete;

public:
    static MeyersSingleton& getInstance() {
        static MeyersSingleton instance; // Thread-safe in C++11 and later
        return instance;
    }
};
```

### Java Implementation

#### Option 1: Double-Checked Locking (Requires `volatile`)

In Java, `volatile` is required to ensure that changes to the `instance` variable are published correctly to other threads, preventing them from seeing a partially initialized object.

```java
public class SingletonDCL {
    // volatile is CRUCIAL here
    private static volatile SingletonDCL instance;

    private SingletonDCL() {}

    public static SingletonDCL getInstance() {
        if (instance == null) {
            synchronized (SingletonDCL.class) {
                if (instance == null) {
                    instance = new SingletonDCL();
                }
            }
        }
        return instance;
    }
}
```

#### Option 2: Initialization-on-demand Holder Idiom (Lazy & Thread-Safe)

This leverages the Java classloader's thread-safety guarantees during class initialization. The `Holder` class is only loaded when `getInstance()` is called.

```java
public class SingletonHolder {
    private SingletonHolder() {}

    private static class Holder {
        private static final SingletonHolder INSTANCE = new SingletonHolder();
    }

    public static SingletonHolder getInstance() {
        return Holder.INSTANCE;
    }
}
```

#### Option 3: Josh Bloch's Enum Singleton (Preferred)

Recommended in *Effective Java*. It provides absolute protection against multiple instantiations, even in the face of serialization and reflection attacks, and is inherently thread-safe.

```java
public enum EnumSingleton {
    INSTANCE;

    public void doSomething() {
        System.out.println("Doing something...");
    }
}
// Usage: EnumSingleton.INSTANCE.doSomething();
```

### When to Use and When NOT to Use

**Problems with Singleton:**
- **Global State:** Introduces global state, making the system unpredictable and hard to reason about.
- **Testing:** Extremely difficult to test. You cannot easily inject a mock Singleton into a class that relies on it.
- **Hidden Dependencies:** Classes using Singletons hide their dependencies in their implementation rather than declaring them in their API (constructors).
- **Violates SRP/DIP:** It manages its own lifecycle (violating Single Responsibility Principle) and forces high-level modules to depend on concrete implementations (violating Dependency Inversion Principle).

**When to avoid:**
- Almost always prefer **Dependency Injection (DI)**. Pass the single instance around rather than letting classes fetch it globally.

**Legitimate uses:**
- **Logger:** A centralized logging mechanism where overhead of DI might be deemed unnecessary.
- **Configuration Manager:** Loading global configurations once.
- **Thread Pool / Hardware Access:** When exactly one physical/logical resource exists.

---

## 2. Factory Method

**Intent:** Define an interface for creating an object, but let subclasses decide which class to instantiate. Factory Method lets a class defer instantiation to subclasses.

### Structure

```
               +-----------------+
               |    Creator      |
               +-----------------+
               | + factoryMethod() | <--- Abstract method
               | + anOperation()   |
               +-----------------+
                       ^
                       |
               +-----------------+
               | ConcreteCreator |
               +-----------------+
               | + factoryMethod() | <--- Returns ConcreteProduct
               +-----------------+

               +-----------------+
               |     Product     | <--- Interface
               +-----------------+
                       ^
                       |
               +-----------------+
               | ConcreteProduct |
               +-----------------+
```

Key insight: The pattern decouples the **WHAT** (the Product interface) from the **WHO** (which ConcreteCreator decides the specific implementation).

### C++ Implementation

```cpp
#include <iostream>
#include <memory>

// Product Interface
class Document {
public:
    virtual ~Document() = default;
    virtual void print() const = 0;
};

// Concrete Products
class PdfDocument : public Document {
public:
    void print() const override { std::cout << "Printing PDF\n"; }
};

class WordDocument : public Document {
public:
    void print() const override { std::cout << "Printing Word\n"; }
};

// Abstract Creator
class DocumentCreator {
public:
    virtual ~DocumentCreator() = default;
    
    // The Factory Method
    virtual std::unique_ptr<Document> createDocument() const = 0;

    // Operation using the product
    void render() const {
        std::unique_ptr<Document> doc = createDocument();
        doc->print();
    }
};

// Concrete Creators
class PdfCreator : public DocumentCreator {
public:
    std::unique_ptr<Document> createDocument() const override {
        return std::make_unique<PdfDocument>();
    }
};

class WordCreator : public DocumentCreator {
public:
    std::unique_ptr<Document> createDocument() const override {
        return std::make_unique<WordDocument>();
    }
};
```

### Java Implementation

```java
// Product
interface Transport {
    void deliver();
}

// Concrete Products
class Truck implements Transport {
    public void deliver() { System.out.println("Deliver by land"); }
}

class Ship implements Transport {
    public void deliver() { System.out.println("Deliver by sea"); }
}

// Abstract Creator
abstract class Logistics {
    // The Factory Method
    public abstract Transport createTransport();
    
    public void planDelivery() {
        Transport t = createTransport();
        t.deliver();
    }
}

// Concrete Creators
class RoadLogistics extends Logistics {
    @Override
    public Transport createTransport() {
        return new Truck();
    }
}

class SeaLogistics extends Logistics {
    @Override
    public Transport createTransport() {
        return new Ship();
    }
}
```

### Static Factory Method Idiom vs. Simple Factory

- **Simple Factory (Not a GoF Pattern):** Usually a single class with a static method containing a large `switch` statement based on a type parameter.
- **Static Factory Method Idiom:** Using static methods like `valueOf()`, `getInstance()`, `newInstance()` instead of constructors (e.g., `DocumentBuilder.newInstance()`, `Calendar.getInstance()`).

**When to use:** When you don't know beforehand the exact types and dependencies of the objects your code should work with.

---

## 3. Abstract Factory

**Intent:** Provide an interface for creating **families** of related or dependent objects without specifying their concrete classes.

### Structure

```
+--------------------+      +-----------------------+
|  AbstractFactory   |      |   ConcreteFactory1    |
+--------------------+      +-----------------------+
| + createProductA() |<-----| + createProductA()    |
| + createProductB() |      | + createProductB()    |
+--------------------+      +-----------------------+
```

### Java Implementation (Cross-platform UI)

```java
// Abstract Products
interface Button { void paint(); }
interface Checkbox { void paint(); }

// Concrete Products - Windows Family
class WindowsButton implements Button {
    public void paint() { System.out.println("Windows Button"); }
}
class WindowsCheckbox implements Checkbox {
    public void paint() { System.out.println("Windows Checkbox"); }
}

// Concrete Products - Mac Family
class MacButton implements Button {
    public void paint() { System.out.println("Mac Button"); }
}
class MacCheckbox implements Checkbox {
    public void paint() { System.out.println("Mac Checkbox"); }
}

// Abstract Factory
interface GUIFactory {
    Button createButton();
    Checkbox createCheckbox();
}

// Concrete Factories
class WindowsFactory implements GUIFactory {
    public Button createButton() { return new WindowsButton(); }
    public Checkbox createCheckbox() { return new WindowsCheckbox(); }
}

class MacFactory implements GUIFactory {
    public Button createButton() { return new MacButton(); }
    public Checkbox createCheckbox() { return new MacCheckbox(); }
}

// Client Code
class Application {
    private Button button;
    private Checkbox checkbox;

    public Application(GUIFactory factory) {
        button = factory.createButton();
        checkbox = factory.createCheckbox();
    }

    public void paint() {
        button.paint();
        checkbox.paint();
    }
}
```

### C++ Implementation (Abstract Base Class)

```cpp
class AbstractFactory {
public:
    virtual ~AbstractFactory() = default;
    virtual std::unique_ptr<Button> createButton() const = 0;
    virtual std::unique_ptr<Checkbox> createCheckbox() const = 0;
};
```

### Factory Method vs. Abstract Factory

- **Factory Method:** Creates **ONE** product. Uses inheritance (subclasses decide).
- **Abstract Factory:** Creates a **FAMILY** of related products. Uses composition (an object contains the factory).

**When to use:** When your system has multiple families of products, and you need to ensure that products from one family are used together (e.g., you don't want a Windows Button alongside a Mac Checkbox).

---

## 4. Builder

**Intent:** Separate the construction of a complex object from its representation so that the same construction process can create different representations.

### The Problem: Telescoping Constructor Anti-Pattern

When an object has many optional parameters, developers often create a series of constructors, each taking one more parameter than the last. This becomes unreadable and hard to maintain.

```java
// BAD: Telescoping Constructor
public class Person {
    public Person(String name) { ... }
    public Person(String name, int age) { ... }
    public Person(String name, int age, String email) { ... } // Hard to know what the args mean!
}
```

### Java Implementation

Uses a static inner `Builder` class with a fluent interface. `build()` validates required fields.

```java
public class Pizza {
    // Required parameters
    private final int size;
    private final String crust;
    
    // Optional parameters
    private final boolean extraCheese;
    private final boolean pepperoni;

    private Pizza(Builder builder) {
        this.size = builder.size;
        this.crust = builder.crust;
        this.extraCheese = builder.extraCheese;
        this.pepperoni = builder.pepperoni;
    }

    public static class Builder {
        // Required
        private final int size;
        private final String crust;
        
        // Optional
        private boolean extraCheese = false;
        private boolean pepperoni = false;

        public Builder(int size, String crust) {
            if (size <= 0) throw new IllegalArgumentException("Size must be positive");
            this.size = size;
            this.crust = crust;
        }

        public Builder extraCheese(boolean val) {
            extraCheese = val;
            return this; // Fluent chaining
        }

        public Builder pepperoni(boolean val) {
            pepperoni = val;
            return this;
        }

        public Pizza build() {
            // Validate combinations here if needed
            return new Pizza(this);
        }
    }
}

// Client
Pizza p = new Pizza.Builder(12, "Thin")
                   .extraCheese(true)
                   .pepperoni(true)
                   .build();
```

### C++ Implementation

Similar fluent interface, often utilizing `std::optional<T>` for clarity on optional fields.

```cpp
#include <string>
#include <optional>

class Person {
private:
    std::string name; // Required
    std::optional<int> age; // Optional
    std::optional<std::string> email; // Optional

    // Private constructor called by Builder
    Person(std::string n, std::optional<int> a, std::optional<std::string> e)
        : name(std::move(n)), age(a), email(std::move(e)) {}

public:
    class Builder {
    private:
        std::string name;
        std::optional<int> age;
        std::optional<std::string> email;

    public:
        explicit Builder(std::string n) : name(std::move(n)) {}

        Builder& setAge(int a) {
            age = a;
            return *this;
        }

        Builder& setEmail(std::string e) {
            email = std::move(e);
            return *this;
        }

        Person build() {
            return Person(name, age, email);
        }
    };
};
```

**Director:** Optionally, a `Director` class can take a `Builder` and orchestrate the exact sequence of method calls to build specific standard configurations.

---

## 5. Prototype

**Intent:** Specify the kinds of objects to create using a prototypical instance, and create new objects by copying this prototype.

### When to use

- Object construction is highly expensive (e.g., involves database queries or complex network calls).
- The classes to instantiate are specified at runtime.
- You want to avoid building a parallel hierarchy of factories.

### C++ Implementation

Uses the copy constructor inside a virtual `clone()` method.

```cpp
class Shape {
public:
    virtual ~Shape() = default;
    virtual std::unique_ptr<Shape> clone() const = 0;
    virtual void draw() const = 0;
};

class Circle : public Shape {
private:
    int radius;
    int* expensiveData; // Example of a pointer requiring deep copy

public:
    Circle(int r) : radius(r), expensiveData(new int(r * 10)) {}
    
    // Copy constructor (Deep Copy)
    Circle(const Circle& other) : radius(other.radius), expensiveData(new int(*other.expensiveData)) {}
    
    ~Circle() { delete expensiveData; }

    std::unique_ptr<Shape> clone() const override {
        return std::make_unique<Circle>(*this); // Calls copy constructor
    }

    void draw() const override { std::cout << "Drawing Circle\n"; }
};
```

### Java Implementation

While Java provides the `Cloneable` interface and `Object.clone()`, it is widely considered broken because `clone()` is protected, returns `Object`, and requires awkward casting and exception handling (`CloneNotSupportedException`).

**Better Java Idiom:** Use Copy Constructors or Static Factory Methods.

```java
public class Circle {
    private int radius;
    private int[] data;

    public Circle(int radius) {
        this.radius = radius;
        this.data = new int[]{1, 2, 3}; // Simulate complex data
    }

    // Copy Constructor (Deep Copy)
    public Circle(Circle other) {
        this.radius = other.radius;
        // Deep copy the array!
        this.data = other.data.clone(); 
    }
    
    // Static Factory
    public static Circle copyOf(Circle other) {
        return new Circle(other);
    }
}
```

### Prototype Registry

Often combined with a registry (a HashMap/std::map) storing prototypes by name. The client asks the registry for an object, and the registry returns a clone of the stored prototype.

```cpp
// Map: string -> unique_ptr<Shape>
// Client: registry.get("BigCircle")->clone();
```
