# SOLID Principles Q&A

## 🟢 Easy

### 1. State all 5 SOLID principles in one sentence each.
* **Single Responsibility Principle (SRP)**: A class should have one, and only one, reason to change.
* **Open/Closed Principle (OCP)**: Software entities should be open for extension but closed for modification.
* **Liskov Substitution Principle (LSP)**: Objects of a derived class must be substitutable for objects of their base class without altering the correctness of the program.
* **Interface Segregation Principle (ISP)**: Clients should not be forced to depend on methods they do not use.
* **Dependency Inversion Principle (DIP)**: High-level modules should depend on abstractions, not on low-level concrete implementations.

### 2. What is the Single Responsibility Principle? Show a class that violates it and fix it.
**Answer:** SRP states that a class should handle only one specific concern or have one stakeholder driving its changes. 

**Violation:** A class handling both data logic and presentation logic.
```java
public class Invoice {
    public void calculateTotal() { /* business logic */ }
    public void printInvoice() { /* presentation logic */ }
}
```

**Fix:** Split into two distinct classes.
```java
public class Invoice {
    public void calculateTotal() { /* business logic */ }
}
public class InvoicePrinter {
    public void print(Invoice inv) { /* presentation logic */ }
}
```

---

## 🟡 Medium

### 3. Why does `Square extends Rectangle` violate LSP? Show the invariant that breaks. How do you fix it?
**Answer:** 
It violates LSP because a `Square` alters the fundamental expected behavior (invariants) of a `Rectangle`. 
The broken invariant is: *Changing the width of a rectangle should not affect its height.*

If `Square` inherits from `Rectangle`, overriding `setWidth(w)` to also set the height to `w` creates a side effect that client code operating on `Rectangle` does not expect.
```java
// Breaks here:
Rectangle r = new Square();
r.setWidth(5);
r.setHeight(10);
assert r.getArea() == 50; // Fails! Area is 100 because setHeight(10) set both to 10.
```
**Fix:** Remove inheritance. Both `Square` and `Rectangle` should implement a common interface like `Shape`, keeping their implementations entirely decoupled.

### 4. What is the difference between Dependency Inversion Principle (DIP) and Dependency Injection (DI)?
**Answer:**
* **DIP** is the theoretical *design principle* stating that high-level policies should not depend on low-level details, but rather both should depend on abstractions.
* **DI** is the *technique/pattern* used to implement DIP. It is the physical mechanism of passing (injecting) the concrete dependencies into the class (usually via constructor, setter, or method parameter) rather than the class instantiating them itself.

### 5. How do you implement the Open/Closed Principle without modifying existing classes?
**Answer:** By utilizing abstractions (interfaces or abstract classes) and polymorphism. Instead of hardcoding behavior or using large `if/else` or `switch` statements to handle different types, you write code that depends on an interface. When new behavior is needed, you create a new class that implements that interface, leaving the consumer class completely untouched. Common design patterns used for this include Strategy, Decorator, and Template Method.

---

## 🔴 Hard

### 6. Given this "god class" — identify ALL SOLID violations and refactor it:
```java
class OrderManager {
    private MySQLDatabase db = new MySQLDatabase();
    public void createOrder(Order o) {
        if (o.getItems().isEmpty()) throw new RuntimeException();
        db.save(o);
        new EmailClient().send(o.getUser().getEmail(), "Order confirmed");
        if (o.getTotal() > 100) o.setDiscount(0.1);
    }
    public void exportToCSV(Order o) { /* ... */ }
    public void exportToPDF(Order o) { /* ... */ }
}
```

**Violations Identified:**
1. **SRP:** The class handles validation, persistence, notification, pricing logic, and multiple export formats.
2. **OCP:** Adding a new export format (like XML) requires modifying this class.
3. **DIP:** Hardcoded instantiation of `MySQLDatabase` and `EmailClient`. It depends on concrete low-level modules rather than abstractions.

**Refactored Code:**
```java
// 1. Abstractions
interface IDatabase { void save(Order o); }
interface INotificationClient { void send(String to, String msg); }
interface IOrderExporter { void export(Order o); }

// 2. SRP - Split behaviors
class OrderValidator {
    public void validate(Order o) {
        if (o.getItems().isEmpty()) throw new RuntimeException("Empty order");
    }
}

class PricingService {
    public void applyDiscounts(Order o) {
        if (o.getTotal() > 100) o.setDiscount(0.1);
    }
}

// 3. OCP - Exporters as separate implementations
class CSVExporter implements IOrderExporter {
    public void export(Order o) { /* CSV Logic */ }
}
class PDFExporter implements IOrderExporter {
    public void export(Order o) { /* PDF Logic */ }
}

// 4. DIP - Inject dependencies into High-level manager
class OrderManager {
    private final IDatabase db;
    private final INotificationClient notifier;
    private final OrderValidator validator;
    private final PricingService pricing;

    // Constructor Injection
    public OrderManager(IDatabase db, INotificationClient notifier, 
                        OrderValidator validator, PricingService pricing) {
        this.db = db;
        this.notifier = notifier;
        this.validator = validator;
        this.pricing = pricing;
    }

    public void createOrder(Order o) {
        validator.validate(o);
        pricing.applyDiscounts(o);
        db.save(o);
        notifier.send(o.getUser().getEmail(), "Order confirmed");
    }
}
```

### 7. Design a notification system that sends Email, SMS, and Push notifications. 
**Requirements:** Satisfy OCP, ISP, and DIP.

**Solution:**
```java
// 1. ISP: Segregated interfaces based on capability
interface ITextSender {
    void sendText(String userId, String message);
}

interface IRichMediaSender {
    void sendRichMedia(String userId, String message, byte[] payload);
}

// 2. OCP: Implementing channels independently
class EmailChannel implements ITextSender, IRichMediaSender {
    @Override
    public void sendText(String userId, String message) {
        System.out.println("Sending Email text to " + userId);
    }
    @Override
    public void sendRichMedia(String userId, String msg, byte[] payload) {
        System.out.println("Sending Email with attachment");
    }
}

class SmsChannel implements ITextSender {
    @Override
    public void sendText(String userId, String message) {
        System.out.println("Sending SMS text to " + userId);
    }
    // Doesn't implement IRichMediaSender, avoiding fat interface violation!
}

class PushChannel implements ITextSender, IRichMediaSender {
    @Override
    public void sendText(String userId, String message) {
        System.out.println("Sending Push notification to " + userId);
    }
    @Override
    public void sendRichMedia(String userId, String msg, byte[] payload) {
        System.out.println("Sending Push with image payload");
    }
}

// 3. DIP: High level NotificationService depends on abstractions (ITextSender)
class NotificationService {
    private final List<ITextSender> textChannels;

    // Constructor Injection for list of channels
    public NotificationService(List<ITextSender> textChannels) {
        this.textChannels = textChannels;
    }

    // OCP satisfied: Adding WhatsApp channel requires zero changes to NotificationService.
    // Just inject a WhatsAppChannel into the list on initialization.
    public void broadcastText(String userId, String message) {
        for (ITextSender channel : textChannels) {
            channel.sendText(userId, message);
        }
    }
}
```
