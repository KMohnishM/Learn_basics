# Module 7: Structural & Behavioral Design Patterns

This module covers two major categories of design patterns: Structural patterns (how to assemble objects and classes into larger structures) and Behavioral patterns (how to manage algorithms, relationships, and responsibilities between objects).

---

## Part 1: Structural Patterns

Structural patterns deal with object composition and class structure. They help ensure that if one part of a system changes, the entire structure does not need to change.

### 1. Adapter

**Intent:** Convert the interface of a class into another interface clients expect. Adapter lets classes work together that couldn't otherwise because of incompatible interfaces.

**Analogy:** A power plug adapter. You have a European laptop plug, but you're in the US. The adapter implements the US socket interface and delegates the power delivery to your European plug.

**Types:**
- **Object Adapter (Composition):** The adapter contains an instance of the class it wraps. Preferred approach.
- **Class Adapter (Inheritance):** The adapter inherits from both the target interface and the adaptee. Requires multiple inheritance (possible in C++, not in Java).

**Real-world Example:** `InputStreamReader` in Java adapts `InputStream` (byte-based) to `Reader` (character-based).

#### Java Implementation (Object Adapter)

```java
// 1. Target Interface: What the client expects
public interface INewPrinter {
    void printFormatted(String text);
}

// 2. Adaptee: The legacy class with an incompatible interface
public class OldPrinter {
    public void printRaw(String data) {
        System.out.println("--- PRINTING RAW ---");
        System.out.println(data);
    }
}

// 3. Adapter: Implements target, delegates to adaptee
public class PrinterAdapter implements INewPrinter {
    private final OldPrinter adaptee;
    
    public PrinterAdapter(OldPrinter adaptee) {
        this.adaptee = adaptee;
    }
    
    @Override
    public void printFormatted(String text) {
        // Translation logic happens here
        String formatted = "[FORMATTED] " + text.toUpperCase();
        adaptee.printRaw(formatted);
    }
}

// 4. Client
public class Client {
    public static void main(String[] args) {
        OldPrinter legacy = new OldPrinter();
        INewPrinter modern = new PrinterAdapter(legacy);
        
        modern.printFormatted("Hello Adapter Pattern");
    }
}
```

#### C++ Implementation (Class Adapter via Multiple Inheritance)

```cpp
#include <iostream>
#include <string>

// Target
class ITarget {
public:
    virtual void request() = 0;
    virtual ~ITarget() = default;
};

// Adaptee
class Adaptee {
public:
    void specificRequest() {
        std::cout << "Adaptee's specific request" << std::endl;
    }
};

// Class Adapter using multiple inheritance
class ClassAdapter : public ITarget, private Adaptee {
public:
    void request() override {
        // Delegate to inherited specificRequest
        specificRequest();
    }
};
```

**When to use:** Integrating legacy code or third-party libraries that have incompatible interfaces with your system.

---

### 2. Decorator

**Intent:** Attach additional responsibilities to an object dynamically. Decorators provide a flexible alternative to subclassing for extending functionality.

**Key Insight:** The Decorator implements the SAME interface as the wrapped component. The client code cannot tell if it's interacting with the base component or a decorated component.

**Analogy:** Wearing clothes. You add a shirt, then a jacket, then a raincoat. You are still a "Person", but your properties (warmth, waterproofness) have been dynamically augmented.

**Real-world Example:** Java I/O streams. `new BufferedInputStream(new FileInputStream(file))` adds buffering to a file input stream dynamically. Python's `@decorator` syntax maps conceptually to this pattern.

#### Java Implementation

```java
// 1. Component Interface
public interface DataSource {
    void writeData(String data);
    String readData();
}

// 2. Concrete Component
public class FileDataSource implements DataSource {
    private String filename;
    
    public FileDataSource(String filename) {
        this.filename = filename;
    }
    
    @Override
    public void writeData(String data) {
        System.out.println("Writing to " + filename + ": " + data);
    }
    
    @Override
    public String readData() {
        return "data_from_" + filename;
    }
}

// 3. Base Decorator
public abstract class DataSourceDecorator implements DataSource {
    protected DataSource wrappee;
    
    public DataSourceDecorator(DataSource wrappee) {
        this.wrappee = wrappee;
    }
    
    @Override
    public void writeData(String data) {
        wrappee.writeData(data);
    }
    
    @Override
    public String readData() {
        return wrappee.readData();
    }
}

// 4. Concrete Decorators
public class EncryptionDecorator extends DataSourceDecorator {
    public EncryptionDecorator(DataSource wrappee) {
        super(wrappee);
    }
    
    @Override
    public void writeData(String data) {
        String encrypted = encrypt(data);
        super.writeData(encrypted);
    }
    
    @Override
    public String readData() {
        return decrypt(super.readData());
    }
    
    private String encrypt(String data) { return "[ENCRYPTED] " + data; }
    private String decrypt(String data) { return data.replace("[ENCRYPTED] ", ""); }
}

public class CompressionDecorator extends DataSourceDecorator {
    public CompressionDecorator(DataSource wrappee) {
        super(wrappee);
    }
    
    @Override
    public void writeData(String data) {
        String compressed = compress(data);
        super.writeData(compressed);
    }
    
    @Override
    public String readData() {
        return decompress(super.readData());
    }
    
    private String compress(String data) { return "[COMPRESSED] " + data; }
    private String decompress(String data) { return data.replace("[COMPRESSED] ", ""); }
}

// 5. Client
public class Client {
    public static void main(String[] args) {
        // Stacking decorators dynamically!
        DataSource source = new EncryptionDecorator(
                                new CompressionDecorator(
                                    new FileDataSource("salary.dat")));
        
        source.writeData("Salary: 100000");
        // Output: Writing to salary.dat: [COMPRESSED] [ENCRYPTED] Salary: 100000
    }
}
```

**Decorator vs Inheritance:** 
- Inheritance is static (compile-time) and leads to class explosion (e.g., `EncryptedCompressedFileDataSource`).
- Decorator is dynamic (runtime) and composable. You can mix and match behaviors as needed.

**When to use:** Adding behavior to objects without affecting other objects of the same class.

---

### 3. Facade

**Intent:** Provide a simplified, unified high-level interface to a complex subsystem, making the subsystem easier to use.

**Key Insight:** The complex subsystem classes still exist and are accessible if clients need deep control. The Facade just provides a convenient entry point for the most common tasks.

**Analogy:** A customer service hotline. You call one number, and the agent orchestrates the shipping, billing, and technical support departments for you.

#### Java Implementation

```java
// --- Complex Subsystem Classes ---
class Amplifier { void on() { System.out.println("Amp on"); } }
class Projector { void on() { System.out.println("Projector on"); } }
class StreamingPlayer { void play(String movie) { System.out.println("Playing " + movie); } }
class Lights { void dim() { System.out.println("Lights dim"); } }

// --- Facade ---
public class HomeTheaterFacade {
    private Amplifier amp;
    private Projector projector;
    private StreamingPlayer player;
    private Lights lights;
    
    public HomeTheaterFacade(Amplifier a, Projector p, StreamingPlayer sp, Lights l) {
        this.amp = a;
        this.projector = p;
        this.player = sp;
        this.lights = l;
    }
    
    // Simplified API
    public void watchMovie(String movie) {
        System.out.println("Get ready to watch a movie...");
        lights.dim();
        amp.on();
        projector.on();
        player.play(movie);
    }
}

// --- Client ---
public class Client {
    public static void main(String[] args) {
        HomeTheaterFacade facade = new HomeTheaterFacade(
            new Amplifier(), new Projector(), new StreamingPlayer(), new Lights());
            
        facade.watchMovie("Inception");
    }
}
```

**Facade vs Adapter:** Adapter converts an incompatible interface into a compatible one. Facade simplifies a complex API.

**When to use:** When you have a complex subsystem with many dependencies and you want to provide a straightforward interface for common use cases.

---

### 4. Proxy

**Intent:** Provide a surrogate or placeholder for another object to control access to it.

**Types:**
1. **Virtual Proxy:** Lazy loading. Creates expensive objects on demand.
2. **Protection Proxy:** Controls access based on permissions.
3. **Remote Proxy:** Acts as a local representative for an object in a different address space (e.g., Java RMI, gRPC stubs).
4. **Caching Proxy:** Caches results of expensive operations.

**Proxy vs Decorator:** Proxy controls *access* to an object. Decorator adds *behavior* to an object.

#### Java Implementation (Virtual Proxy)

```java
// 1. Subject Interface
public interface Image {
    void display();
}

// 2. Real Subject (Expensive to create)
public class RealImage implements Image {
    private String filename;
    
    public RealImage(String filename) {
        this.filename = filename;
        loadFromDisk(); // Expensive operation!
    }
    
    private void loadFromDisk() {
        System.out.println("Loading " + filename + " from disk (takes 5 seconds)...");
    }
    
    @Override
    public void display() {
        System.out.println("Displaying " + filename);
    }
}

// 3. Proxy (Defers creation until needed)
public class ImageProxy implements Image {
    private String filename;
    private RealImage realImage; // Reference to real subject
    
    public ImageProxy(String filename) {
        this.filename = filename;
    }
    
    @Override
    public void display() {
        if (realImage == null) {
            // Lazy initialization
            realImage = new RealImage(filename);
        }
        realImage.display();
    }
}

// 4. Client
public class Client {
    public static void main(String[] args) {
        // Image is NOT loaded from disk yet! Fast return.
        Image img1 = new ImageProxy("high_res_photo.jpg");
        
        System.out.println("UI rendered. User scrolling...");
        
        // Image is loaded ONLY when requested
        img1.display(); 
        
        // Second call doesn't reload
        img1.display();
    }
}
```

---

## Part 2: Behavioral Patterns

Behavioral patterns deal with algorithms and the assignment of responsibilities between objects. They focus on how objects communicate and cooperate.

### 5. Observer (Pub/Sub)

**Intent:** Define a one-to-many dependency between objects so that when one object (Subject) changes state, all its dependents (Observers) are notified and updated automatically.

**Concept:** Loose coupling. The Subject only knows that its Observers implement a specific interface; it doesn't know their concrete classes.

**Real-world Examples:** Event listeners in UI frameworks (onClick), MVC pattern (Model notifies View), Reactive streams (RxJava, Reactor).
*(Note: Java's built-in `java.util.Observable` is deprecated. Always define custom interfaces or use modern reactive libraries.)*

#### Java Implementation

```java
import java.util.ArrayList;
import java.util.List;

// 1. Observer Interface
public interface Observer {
    void update(String stockSymbol, double price);
}

// 2. Subject Interface
public interface Subject {
    void attach(Observer o);
    void detach(Observer o);
    void notifyObservers();
}

// 3. Concrete Subject
public class StockMarket implements Subject {
    private List<Observer> observers = new ArrayList<>();
    private String symbol;
    private double price;
    
    public void setPrice(String symbol, double price) {
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
public class MobileApp implements Observer {
    @Override
    public void update(String stockSymbol, double price) {
        System.out.println("Mobile Push: " + stockSymbol + " is now $" + price);
    }
}

public class EmailAlert implements Observer {
    @Override
    public void update(String stockSymbol, double price) {
        if (price > 150) {
            System.out.println("Email Alert: HIGH PRICE for " + stockSymbol + "!");
        }
    }
}
```

**Push vs Pull Model:**
- **Push:** The Subject sends the data directly in the notification (`update(symbol, price)`).
- **Pull:** The Subject just says "I changed!" (`update()`), and the Observer queries the Subject for the data (`subject.getPrice()`).

---

### 6. Strategy

**Intent:** Define a family of algorithms, encapsulate each one, and make them interchangeable. Strategy lets the algorithm vary independently from the clients that use it.

**Concept:** Favor composition over inheritance for algorithmic behavior. Prevents massive `if/else` or `switch` statements.

**Real-world Examples:** `java.util.Comparator<T>`, payment processors (Credit Card, PayPal, Crypto), file compression algorithms (ZIP, RAR, 7z).

#### Java Implementation

```java
// 1. Strategy Interface
public interface PaymentStrategy {
    void pay(int amount);
}

// 2. Concrete Strategies
public class CreditCardStrategy implements PaymentStrategy {
    @Override
    public void pay(int amount) {
        System.out.println("Paid $" + amount + " using Credit Card.");
    }
}

public class PayPalStrategy implements PaymentStrategy {
    @Override
    public void pay(int amount) {
        System.out.println("Paid $" + amount + " using PayPal.");
    }
}

// 3. Context
public class PaymentProcessor {
    private PaymentStrategy strategy; // Can be swapped at runtime
    
    public PaymentProcessor(PaymentStrategy strategy) {
        this.strategy = strategy;
    }
    
    public void setStrategy(PaymentStrategy strategy) {
        this.strategy = strategy;
    }
    
    public void checkout(int amount) {
        strategy.pay(amount);
    }
}

// 4. Client
public class Client {
    public static void main(String[] args) {
        PaymentProcessor processor = new PaymentProcessor(new CreditCardStrategy());
        processor.checkout(100);
        
        // Change algorithm at runtime!
        processor.setStrategy(new PayPalStrategy());
        processor.checkout(50);
        
        // Modern Java Idiom: Lambdas for Single Abstract Method (SAM) interfaces
        processor.setStrategy(amount -> System.out.println("Paid $" + amount + " using Crypto."));
        processor.checkout(200);
    }
}
```

**Strategy vs If/Else:** Strategy follows the Open/Closed Principle. You can add new payment methods without modifying the `PaymentProcessor` code.

---

### 7. Command

**Intent:** Encapsulate a request as an object, thereby letting you parameterize clients with different requests, queue or log requests, and support undoable operations.

**Structure:**
- **Command:** Interface with `execute()` and (optional) `undo()`.
- **ConcreteCommand:** Implements `Command`, holds a reference to a Receiver.
- **Invoker:** Asks the command to carry out the request (doesn't know *what* happens).
- **Receiver:** Knows how to perform the actual work.

**Real-world Examples:** Text editor undo/redo stacks, thread pool job queues, UI framework action buttons, transactional databases.

#### Java Implementation (Undo/Redo)

```java
// 1. Command Interface
public interface Command {
    void execute();
    void undo();
}

// 2. Receiver
public class TextEditor {
    private StringBuilder text = new StringBuilder();
    
    public void type(String str) { text.append(str); }
    public void delete(int length) { text.setLength(text.length() - length); }
    public String getText() { return text.toString(); }
}

// 3. Concrete Command
public class TypeCommand implements Command {
    private TextEditor editor;
    private String textToType;
    
    public TypeCommand(TextEditor editor, String textToType) {
        this.editor = editor;
        this.textToType = textToType;
    }
    
    @Override
    public void execute() {
        editor.type(textToType);
    }
    
    @Override
    public void undo() {
        editor.delete(textToType.length());
    }
}

// 4. Invoker
public class CommandHistory {
    private Stack<Command> history = new Stack<>();
    
    public void executeCommand(Command c) {
        c.execute();
        history.push(c);
    }
    
    public void undo() {
        if (!history.isEmpty()) {
            Command c = history.pop();
            c.undo();
        }
    }
}
```

---

### 8. Iterator

**Intent:** Provide a way to access the elements of an aggregate object (collection) sequentially without exposing its underlying representation.

**Concept:** Decouple traversal algorithms from data structures.

**Java context:** Java provides `Iterator<T>` (`hasNext()`, `next()`) and `Iterable<T>` (which allows use in `for (T item : collection)` loops).

**C++ context:** C++ uses pointer-like iterators (`begin()`, `end()`, `operator++`, `operator*`) which enable range-based for loops.

#### Java Implementation (Custom Iterator)

```java
import java.util.Iterator;
import java.util.NoSuchElementException;

// A custom collection class
public class CustomArray<T> implements Iterable<T> {
    private T[] items;
    private int size = 0;
    
    @SuppressWarnings("unchecked")
    public CustomArray(int capacity) {
        items = (T[]) new Object[capacity];
    }
    
    public void add(T item) {
        items[size++] = item;
    }

    @Override
    public Iterator<T> iterator() {
        return new CustomIterator();
    }
    
    // Inner class implementing Iterator
    private class CustomIterator implements Iterator<T> {
        private int cursor = 0;
        
        @Override
        public boolean hasNext() {
            return cursor < size;
        }
        
        @Override
        public T next() {
            if (!hasNext()) throw new NoSuchElementException();
            return items[cursor++];
        }
    }
}
```

*Note: In modern development, explicit Iterator patterns are often replaced by functional streams (Java `Stream`, C++ `std::ranges`) mapping and filtering over collections.*
