# CHEATSHEET: Encapsulation & Abstraction

## 1. Access Specifiers

| Modifier | C++ Scope | Java Scope | Notes |
| :--- | :--- | :--- | :--- |
| **`public`** | Anywhere | Anywhere | Open access |
| **`protected`** | Class + Derived classes | Class + Package + Subclasses | Used for inheritance |
| **`package-private`**| *N/A* | Class + Package | Default in Java (no keyword) |
| **`private`** | Class only (+ friends) | Class only | Safest, strict encapsulation |

---

## 2. Abstract Classes

Used when classes share identity ("IS-A") and you want to share implementation/state.

**C++ (Pure Virtual Function)**
```cpp
class Animal {
protected:
    int age; // State allowed
public:
    virtual ~Animal() = default;
    virtual void speak() = 0; // Pure virtual makes class abstract
    void sleep() { /* Concrete logic */ }
};
```

**Java (`abstract` keyword)**
```java
abstract class Animal {
    protected int age; // State allowed
    
    public abstract void speak(); // Abstract method
    public void sleep() { /* Concrete logic */ }
}
```

---

## 3. Interfaces

Used to define a contract ("CAN-DO"). No instance state. 

**C++ (Pure Abstract Class)**
```cpp
class IRunnable {
public:
    virtual ~IRunnable() = default;
    virtual void run() = 0; // No state, all pure virtual
};
```

**Java (`interface` keyword)**
```java
interface Runnable {
    void run(); // implicitly public abstract
    // Java 8+: can have default/static methods, but NO instance fields
}
```

---

## 4. Decision Tree: Abstract Class vs Interface

1. **Do you need to hold instance state (fields)?**
   - YES: Use Abstract Class.
   - NO: Go to 2.
2. **Do the subclasses share a core identity (IS-A relationship)?**
   - YES: Use Abstract Class (e.g., `Car extends Vehicle`).
   - NO (It's a capability/CAN-DO): Use Interface (e.g., `Car implements Drivable`).
3. **Do you need a class to implement multiple distinct contracts?**
   - YES: Use Interface (Java only allows extending 1 class, but multiple interfaces).

---

## 5. Quick Concepts

**Encapsulation:** Hiding *data* and restricting access to internal state. 
*Goal:* Protect invariants, reduce coupling.

**Abstraction:** Hiding *implementation details* and exposing only necessary functionality.
*Goal:* Reduce cognitive load.

**Law of Demeter (LoD):** "Don't talk to strangers." An object should only call methods on itself, its fields, or objects passed as parameters.
*Violation:* `order.getCustomer().getAddress().getZipCode()`
*Fix:* `order.getCustomerZipCode()` (Tell, don't ask).

**Anemic Domain Model:** A code smell where classes have only data (with getters/setters) and no behavior. Behavior is incorrectly leaked to separate "Service" classes.
