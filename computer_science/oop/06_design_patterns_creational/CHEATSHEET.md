# Creational Patterns Cheatsheet

## Pattern Summary Table

| Pattern | Intent | Use When |
| :--- | :--- | :--- |
| **Singleton** | Ensure exactly one instance exists with global access. | You need a centralized coordinator (e.g., Logger, Config) and DI is impractical. |
| **Factory Method** | Delegate instantiation logic to subclasses. | You don't know exact product types in advance; decouples WHAT from WHO. |
| **Abstract Factory** | Create families of related objects. | The system needs to be configured with one of multiple product families (e.g., UI themes). |
| **Builder** | Step-by-step construction of complex objects. | You have the telescoping constructor anti-pattern (many optional parameters). |
| **Prototype** | Create new objects by cloning an existing one. | Object initialization is expensive (DB/Network) or types are determined at runtime. |

## Singleton Variants

| Variant | Language | Pros | Cons |
| :--- | :--- | :--- | :--- |
| **Naive (Static field)** | C++/Java | Simple to write. | Not thread-safe; race conditions on initialization. |
| **Mutex DCL** | C++/Java | Thread-safe, lazy initialization. | Complex, requires `atomic`/`volatile`, easy to implement incorrectly. |
| **Meyers Singleton** | C++ | Simple, 100% thread-safe (C++11+). | Lifetime order of destruction of multiple statics can be tricky. |
| **Java Enum** | Java | Thread-safe, reflection-safe, serialization-safe. | Cannot inherit from other classes (enums implicitly extend `Enum`). |

## Factory vs Abstract Factory vs Builder

- Use **Factory Method** when you are creating exactly **one** product and want to let subclasses decide the implementation.
- Use **Abstract Factory** when you are creating a **family** of related products that must be used together (e.g., Windows UI elements vs. Mac UI elements).
- Use **Builder** when you are creating a **complex** object with multiple configuration steps or optional fields, decoupling the construction process from the final representation.

## Builder Pattern Template (Java)

```java
public class Product {
    private final String req;
    private final int opt;
    
    private Product(Builder b) { this.req = b.req; this.opt = b.opt; }
    
    public static class Builder {
        private final String req;
        private int opt = 0; // Default
        
        public Builder(String req) { this.req = req; }
        public Builder opt(int val) { this.opt = val; return this; }
        public Product build() { return new Product(this); }
    }
}
// Usage: Product p = new Product.Builder("A").opt(5).build();
```
