# Creational Design Patterns: Q&A

## 🟢 Easy

**1. What is the Singleton pattern? When should you use it? Give 2 legitimate use cases and 2 situations where you should NOT use it.**
- **Answer:** The Singleton pattern ensures a class has only one instance and provides a global point of access to it.
- **Legitimate use cases:** A centralized Logger (where DI overhead isn't worth it), or a Configuration Manager that loads global settings once.
- **When NOT to use it:** Avoid using it as a substitute for global variables to share state across unrelated components, or when the class relies on dependencies that make testing difficult (as Singletons are notoriously hard to mock).

**2. What is the Factory Method pattern? How does it decouple object creation from the client?**
- **Answer:** Factory Method defines an interface for creating an object, but delegates the exact instantiation to subclasses. It decouples creation by hiding the `new` keyword and the concrete class name from the client code. The client only interacts with the abstract Product interface and the abstract Creator's factory method.

## 🟡 Medium

**3. Compare Factory Method vs Abstract Factory vs Builder — give a one-sentence "use when" for each.**
- **Factory Method:** Use when you need to delegate the creation of a *single* product to subclasses.
- **Abstract Factory:** Use when you need to create *families* of related or dependent objects (like UI themes) without specifying their concrete classes.
- **Builder:** Use when constructing a *complex object* requires step-by-step initialization or has many optional parameters.

**4. What is the "telescoping constructor" anti-pattern? Show it and the Builder pattern solution.**
- **Answer:** The telescoping constructor anti-pattern occurs when a class has multiple constructors, each taking one more parameter than the previous, to handle optional fields.
  ```java
  // Anti-pattern
  public Person(String name) { ... }
  public Person(String name, int age) { ... }
  public Person(String name, int age, String email) { ... }
  ```
  **Builder Solution:** Use a nested Builder class with a fluent interface.
  ```java
  Person p = new Person.Builder("Alice").age(30).email("a@b").build();
  ```

**5. How do you make Singleton thread-safe in C++ and Java? Show both approaches.**
- **C++:** Use the Meyers Singleton (a static local variable inside the instance method), which is guaranteed to be thread-safe by the C++11 standard.
- **Java:** Use the Double-Checked Locking (DCL) approach with the `volatile` keyword and a `synchronized` block, or use the `enum` Singleton approach.

## 🔴 Hard

**6. Implement a thread-safe Singleton in C++ using Meyers Singleton (explain why it's thread-safe since C++11) AND in Java using the enum approach (explain why enum is reflection-safe and serialization-safe).**

**C++ Meyers Singleton:**
```cpp
class Singleton {
private:
    Singleton() = default;
    Singleton(const Singleton&) = delete;
    Singleton& operator=(const Singleton&) = delete;
public:
    static Singleton& getInstance() {
        static Singleton instance;
        return instance;
    }
};
```
*Explanation:* Since C++11, the standard guarantees that block-scope static variables are initialized in a thread-safe manner. If multiple threads hit the initialization simultaneously, only one will initialize it while the others block until it completes.

**Java Enum Singleton:**
```java
public enum Singleton {
    INSTANCE;
    public void doWork() { }
}
```
*Explanation:* The JVM handles the initialization of enums, guaranteeing it is thread-safe. It is reflection-safe because the JVM prevents reflective instantiation of enum types. It is serialization-safe because Java's serialization mechanism ensures that deserializing an enum returns the existing instance rather than creating a new one.

**7. Design an Abstract Factory for a cross-platform UI toolkit:**
- Products: `Button` and `Checkbox`
- Families: Windows and Mac
- Client code must work with any factory without knowing the concrete types

**Java Implementation:**
```java
// Abstract Products
interface Button { void render(); }
interface Checkbox { void check(); }

// Concrete Products - Windows
class WinButton implements Button { public void render() {} }
class WinCheckbox implements Checkbox { public void check() {} }

// Concrete Products - Mac
class MacButton implements Button { public void render() {} }
class MacCheckbox implements Checkbox { public void check() {} }

// Abstract Factory
interface GUIFactory {
    Button createButton();
    Checkbox createCheckbox();
}

// Concrete Factories
class WinFactory implements GUIFactory {
    public Button createButton() { return new WinButton(); }
    public Checkbox createCheckbox() { return new WinCheckbox(); }
}
class MacFactory implements GUIFactory {
    public Button createButton() { return new MacButton(); }
    public Checkbox createCheckbox() { return new MacCheckbox(); }
}

// Client Code
class Application {
    private Button btn;
    private Checkbox cbx;
    
    public Application(GUIFactory factory) {
        btn = factory.createButton();
        cbx = factory.createCheckbox();
    }
}
```
