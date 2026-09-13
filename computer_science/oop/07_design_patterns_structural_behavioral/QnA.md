# Questions & Answers: Structural & Behavioral Patterns

## 🟢 Easy

**1. What is the Observer pattern? Give a real-world use case outside of software.**
The Observer pattern defines a one-to-many relationship where one object (the Subject) maintains a list of dependents (Observers), and automatically notifies them of any state changes. 
*Real-world use case:* A magazine subscription. The publisher (Subject) maintains a list of subscribers (Observers). Whenever a new issue is released, the publisher automatically sends it to all subscribers without them needing to actively check the newsstand.

**2. What is the Strategy pattern? Why is it better than a chain of if/else statements?**
The Strategy pattern defines a family of algorithms, encapsulates each one into separate classes, and makes them interchangeable at runtime.
It is better than `if/else` statements because it adheres to the Open/Closed Principle. If you want to add a new algorithm, you create a new class rather than modifying an existing file that contains a giant `switch` or `if/else` block. This makes the code easier to test, read, and maintain.

---

## 🟡 Medium

**3. Compare Adapter and Facade — how are they different? When would you use each?**
- **Adapter** makes two incompatible interfaces work together. It alters an existing interface to match what a client expects. Use Adapter when you are integrating legacy code or third-party libraries and you cannot change their source code to fit your system's interface.
- **Facade** provides a simplified, higher-level interface to a complex subsystem composed of many classes. It does not alter interfaces to make them compatible; it just makes a system easier to use. Use Facade when a system is very complex (like orchestrating multiple service layers) and clients only need a simple way to perform common tasks.

**4. How does the Decorator pattern differ from Inheritance for adding functionality? Show a concrete example where Decorator is better.**
- Inheritance is static (resolved at compile time) and applies to the entire class.
- Decorator is dynamic (resolved at runtime) and applies to individual objects via composition.
*Concrete Example:* If you have a `Coffee` class, and you use inheritance, you would need `CoffeeWithMilk`, `CoffeeWithSugar`, `CoffeeWithMilkAndSugar`, etc. (Class Explosion). With Decorator, you simply have a base `Coffee`, and at runtime you can wrap it: `new Sugar(new Milk(new SimpleCoffee()))`.

**5. Name two types of Proxy pattern. Give a real-world use case for each.**
1. **Virtual Proxy (Lazy Loading):** Defers the creation of a resource-heavy object until it's absolutely needed. *Use case:* An image gallery app where high-resolution images are only loaded into memory when the user scrolls them into the viewport.
2. **Protection Proxy:** Controls access to the original object based on credentials. *Use case:* An enterprise HR system where a `DocumentProxy` checks if the current user has "Admin" rights before delegating the `readSalary()` call to the real document object.

---

## 🔴 Hard

**6. Implement the Observer pattern in Java for a stock price notification system.**

```java
import java.util.ArrayList;
import java.util.List;

// 1. Observer Interface
interface Observer {
    void update(String stockSymbol, double price);
}

// 2. Subject Interface
interface Subject {
    void attach(Observer o);
    void detach(Observer o);
    void notifyObservers();
}

// 3. Concrete Subject
class StockMarket implements Subject {
    private List<Observer> observers = new ArrayList<>();
    private String symbol;
    private double price;
    
    public void setStock(String symbol, double price) {
        this.symbol = symbol;
        this.price = price;
        notifyObservers();
    }
    
    @Override
    public void attach(Observer o) { observers.add(o); }
    
    @Override
    public void detach(Observer o) { observers.remove(o); }
    
    @Override
    public void notifyObservers() {
        for (Observer o : observers) {
            o.update(symbol, price);
        }
    }
}

// 4. Concrete Observers
class MobileApp implements Observer {
    @Override
    public void update(String stockSymbol, double price) {
        System.out.println("Mobile Notification: " + stockSymbol + " is now $" + price);
    }
}

class EmailAlertService implements Observer {
    @Override
    public void update(String stockSymbol, double price) {
        System.out.println("Email Sent: Price alert for " + stockSymbol + " @ $" + price);
    }
}

// Client
public class Main {
    public static void main(String[] args) {
        StockMarket nasdaq = new StockMarket();
        
        nasdaq.attach(new MobileApp());
        nasdaq.attach(new EmailAlertService());
        
        nasdaq.setStock("AAPL", 150.00); // Both get notified
    }
}
```

**7. Use the Decorator pattern in Java to add Logging and Caching to a `DatabaseQueryExecutor`.**

```java
import java.util.HashMap;
import java.util.Map;

// 1. Component Interface
interface QueryExecutor {
    String execute(String query);
}

// 2. Concrete Component
class RealQueryExecutor implements QueryExecutor {
    @Override
    public String execute(String query) {
        // Simulate DB lookup delay
        try { Thread.sleep(100); } catch (InterruptedException e) {}
        return "Result_for_" + query;
    }
}

// 3. Base Decorator
abstract class QueryDecorator implements QueryExecutor {
    protected QueryExecutor wrappee;
    public QueryDecorator(QueryExecutor wrappee) {
        this.wrappee = wrappee;
    }
    @Override
    public String execute(String query) {
        return wrappee.execute(query);
    }
}

// 4. Concrete Decorators
class LoggingDecorator extends QueryDecorator {
    public LoggingDecorator(QueryExecutor wrappee) {
        super(wrappee);
    }
    @Override
    public String execute(String query) {
        long start = System.currentTimeMillis();
        System.out.println("[LOG] Executing: " + query);
        String result = super.execute(query);
        long time = System.currentTimeMillis() - start;
        System.out.println("[LOG] Completed in " + time + "ms");
        return result;
    }
}

class CachingDecorator extends QueryDecorator {
    private Map<String, String> cache = new HashMap<>();
    
    public CachingDecorator(QueryExecutor wrappee) {
        super(wrappee);
    }
    @Override
    public String execute(String query) {
        if (cache.containsKey(query)) {
            System.out.println("[CACHE HIT] Returning cached result for: " + query);
            return cache.get(query);
        }
        String result = super.execute(query);
        cache.put(query, result);
        return result;
    }
}

// Client
public class Main {
    public static void main(String[] args) {
        // Stack decorators: Caching happens first, then Logging, then Real DB
        QueryExecutor executor = new CachingDecorator(
                                    new LoggingDecorator(
                                        new RealQueryExecutor()));
                                        
        System.out.println(executor.execute("SELECT * FROM users")); // Misses cache, hits log + DB
        System.out.println(executor.execute("SELECT * FROM users")); // Hits cache, skips log + DB
    }
}
```
