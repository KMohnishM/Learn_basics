# Modern Java Core (Java 8 to 21)

This module provides a comprehensive, production-grade guide to modern Java backend development, covering critical language features, standard library advancements, and runtime concurrency paradigms introduced from Java 8 through LTS Java 21.

---

## Table of Contents
1. [Java Evolution Overview](#1-java-evolution-overview)
2. [Records](#2-records)
3. [Sealed Classes and Interfaces](#3-sealed-classes-and-interfaces)
4. [Pattern Matching](#4-pattern-matching)
5. [Text Blocks](#5-text-blocks)
6. [Streams API Deep Dive](#6-streams-api-deep-dive)
7. [Lambdas and Functional Interfaces](#7-lambdas-and-functional-interfaces)
8. [Optional Handling and Anti-Patterns](#8-optional-handling-and-anti-patterns)
9. [Local Variable Type Inference (`var`)](#9-local-variable-type-inference-var)
10. [Virtual Threads and Structured Concurrency](#10-virtual-threads-and-structured-concurrency)
11. [Sequenced Collections](#11-sequenced-collections)
12. [Modern String API Enhancements](#12-modern-string-api-enhancements)
13. [CompletableFuture and Asynchronous Pipelines](#13-completablefuture-and-asynchronous-pipelines)
14. [Modern Collections and Memory Trade-Offs](#14-modern-collections-and-memory-trade-offs)

---

## 1. Java Evolution Overview

Prior to 2017, Java followed an irregular multi-year release cadence. Beginning with Java 9, Oracle and the OpenJDK community shifted to a predictable six-month time-driven release model. Long-Term Support (LTS) releases represent stable enterprise baselines with extended support windows.

### Release Timeline and LTS Milestones

| Version | Release Date | Support Type | Key Highlights |
|---|---|---|---|
| Java 8 | March 2014 | LTS | Lambdas, Streams, java.time, CompletableFuture, Optional |
| Java 9 | September 2017 | Non-LTS | JPMS (Modules), JShell, ProcessHandle, reactive Flow API |
| Java 10 | March 2018 | Non-LTS | Local variable type inference (`var`), G1 parallel full GC |
| Java 11 | September 2018 | LTS | HTTP Client, String methods (`isBlank`, `lines`), ZGC introduced |
| Java 12 - 13 | 2019 | Non-LTS | Switch expressions preview, Text blocks preview, `Collectors.teeing` |
| Java 14 - 15 | 2020 | Non-LTS | Records preview, Sealed classes preview, NullPointerException help |
| Java 16 | March 2021 | Non-LTS | Records and instanceof pattern matching finalized |
| Java 17 | September 2021 | LTS | Sealed classes finalized, foreign function preview, macOS/AArch64 port |
| Java 18 - 20 | 2022 - 2023 | Non-LTS | Simple web server, pattern matching preview, virtual threads preview |
| Java 21 | September 2023 | LTS | Virtual Threads, Sequenced Collections, Record Patterns, Pattern Switch |

Modern enterprise backend architectures center primarily around Java 17 and Java 21. Java 21 delivers a generational milestone by addressing high-throughput concurrency via Virtual Threads alongside expressive functional-style domain modeling tools.

---

## 2. Records

Records, introduced as standard in Java 16, provide concise syntax for defining immutable data carriers. A record automatically acquires a canonical constructor, private final fields, accessor methods matching component names, `equals()`, `hashCode()`, and `toString()`.

### Syntax and Components

```java
package com.backend.core.records;

import java.time.Instant;
import java.util.Objects;
import java.util.UUID;

public record OrderDto(
        UUID orderId,
        String customerEmail,
        long amountInCents,
        Instant createdAt
) {
    // Compact constructor for validation and normalization
    public OrderDto {
        Objects.requireNonNull(orderId, "orderId cannot be null");
        Objects.requireNonNull(customerEmail, "customerEmail cannot be null");
        if (customerEmail.isBlank() || !customerEmail.contains("@")) {
            throw new IllegalArgumentException("Invalid email format: " + customerEmail);
        }
        if (amountInCents <= 0) {
            throw new IllegalArgumentException("Order amount must be strictly positive");
        }
        if (createdAt == null) {
            createdAt = Instant.now();
        }
        customerEmail = customerEmail.trim().toLowerCase();
    }

    // Secondary constructor delegating to canonical constructor
    public OrderDto(UUID orderId, String customerEmail, long amountInCents) {
        this(orderId, customerEmail, amountInCents, Instant.now());
    }

    // Custom accessor overriding default behavior if necessary
    @Override
    public String customerEmail() {
        return customerEmail;
    }

    // Domain helper method
    public boolean isHighValue() {
        return this.amountInCents >= 100_000L;
    }
}
```

### Implementing Interfaces and Generic Records

Records can implement interfaces and declare generic type parameters, but they cannot extend any class because they implicitly extend `java.lang.Record`.

```java
package com.backend.core.records;

import java.io.Serializable;

public interface Identifiable<T> {
    T id();
}

public record UserProfile<T>(T id, String username, String role) 
        implements Identifiable<T>, Serializable {
    
    private static final long serialVersionUID = 1L;

    public static <T> UserProfile<T> guest(T id) {
        return new UserProfile<>(id, "guest_user", "ROLE_GUEST");
    }
}
```

### Records vs Traditional DTOs and Lombok `@Value`

1. **State Transparency**: A record explicitly declares that its public API consists entirely of its component types. A regular class hides fields behind arbitrary getter contracts.
2. **Immutability and Finality**: All record fields are implicitly `private final`. The record class itself is implicitly `final` and cannot be subclassed.
3. **Serialization Integrity**: Java serialization treats records differently than regular classes. Serialized streams reconstruct records strictly via their canonical constructor, preventing state corruption via unvalidated deserialization bypass.

---

## 3. Sealed Classes and Interfaces

Sealed classes and interfaces (finalized in Java 17) restrict which other classes or interfaces may extend or implement them. This enables closed type hierarchies, allowing developers to model Algebraic Data Types (ADTs) natively in Java.

### Syntax and Keywords: `sealed`, `permits`, `final`, `non-sealed`

A sealed type declares permitted subtypes using the `permits` clause. Every permitted subtype must explicitly choose one modifier:
- `final`: Prevents any further inheritance.
- `sealed`: Extends the sealed hierarchy with its own controlled list of permitted subclasses.
- `non-sealed`: Explicitly opens the subclass to unrestricted extension.

```java
package com.backend.core.sealed;

import java.math.BigDecimal;

public sealed interface PaymentMethod 
        permits CreditCardPayment, BankTransferPayment, CryptoPayment {

    BigDecimal processPayment(BigDecimal amount);
}

public final record CreditCardPayment(
        String cardNumber,
        String cardHolder,
        String cvv
) implements PaymentMethod {
    @Override
    public BigDecimal processPayment(BigDecimal amount) {
        // Business logic for card authorization
        return amount;
    }
}

public final class BankTransferPayment implements PaymentMethod {
    private final String iban;
    private final String bic;

    public BankTransferPayment(String iban, String bic) {
        this.iban = iban;
        this.bic = bic;
    }

    public String getIban() { return iban; }
    public String getBic() { return bic; }

    @Override
    public BigDecimal processPayment(BigDecimal amount) {
        // Business logic for SEPA/ACH transfer
        return amount;
    }
}

public non-sealed class CryptoPayment implements PaymentMethod {
    private final String walletAddress;

    public CryptoPayment(String walletAddress) {
        this.walletAddress = walletAddress;
    }

    public String getWalletAddress() { return walletAddress; }

    @Override
    public BigDecimal processPayment(BigDecimal amount) {
        // Crypto settlement
        return amount;
    }
}
```

### Sealed Hierarchies vs Enums

- **Enums**: Represent a fixed set of constant values. Each enum value is a singleton instance without distinct structural properties or distinct state models.
- **Sealed Classes**: Represent a fixed set of distinct types. Each subtype can maintain distinct properties, constructors, mutable or immutable state, and identity.

---

## 4. Pattern Matching

Java has systematically added pattern matching across multiple versions to eliminate error-prone type casting and boilerplate type checks.

### `instanceof` Pattern Matching (Java 16)

Before pattern matching:
```java
if (obj instanceof String) {
    String s = (String) obj;
    System.out.println(s.toLowerCase());
}
```

Modern `instanceof` pattern matching binds the variable directly in scope:
```java
public void processMessage(Object message) {
    if (message instanceof String text && !text.isBlank()) {
        System.out.println("Processing valid string: " + text.trim());
    } else if (message instanceof byte[] bytes && bytes.length > 0) {
        System.out.println("Processing raw bytes: " + bytes.length);
    }
}
```

### Pattern Matching in Switch Expressions (Java 21)

Pattern matching in `switch` expressions combines type checking, variable binding, and exhaustiveness analysis.

```java
package com.backend.core.patterns;

import com.backend.core.sealed.BankTransferPayment;
import com.backend.core.sealed.CreditCardPayment;
import com.backend.core.sealed.CryptoPayment;
import com.backend.core.sealed.PaymentMethod;

import java.math.BigDecimal;

public class PaymentRouter {

    public String generateAuditSummary(PaymentMethod payment, BigDecimal amount) {
        return switch (payment) {
            case CreditCardPayment cc -> 
                "Card transaction ending with " + cc.cardNumber().substring(cc.cardNumber().length() - 4) +
                " for amount $" + amount;
            case BankTransferPayment bt -> 
                "Bank wire transfer to IBAN " + bt.getIban() +
                " for amount $" + amount;
            case CryptoPayment cp -> 
                "Crypto transfer to address " + cp.getWalletAddress() +
                " for amount $" + amount;
            // No default branch required if all sealed permitted types are handled
        };
    }
}
```

### Guarded Patterns (`when` clause)

Guards allow conditional logic inside case labels using the `when` keyword.

```java
public String categorizeTransaction(PaymentMethod method, BigDecimal amount) {
    return switch (method) {
        case CreditCardPayment cc when amount.compareTo(new BigDecimal("10000")) > 0 ->
            "Flagged high-value card transaction for: " + cc.cardHolder();
        case CreditCardPayment cc ->
            "Standard card transaction for: " + cc.cardHolder();
        case BankTransferPayment bt when bt.getIban().startsWith("DE") ->
            "Domestic German wire transfer";
        case BankTransferPayment bt ->
            "International wire transfer";
        case CryptoPayment cp ->
            "Decentralized settlement: " + cp.getWalletAddress();
    };
}
```

### Record Patterns and Deconstruction (Java 21)

Record patterns deconstruct records into individual variables directly in pattern matching constructs.

```java
public record Coordinates(double latitude, double longitude) {}
public record Location(String name, Coordinates coords) {}

public class LocationService {
    public void printCoordinates(Object obj) {
        if (obj instanceof Location(String name, Coordinates(double lat, double lon))) {
            System.out.printf("Location: %s at Lat: %.4f, Lon: %.4f%n", name, lat, lon);
        }
    }

    public String routeDescription(Object obj) {
        return switch (obj) {
            case Location(var name, Coordinates(var lat, var lon)) when lat < 0 ->
                name + " is located in the Southern Hemisphere (" + lat + ", " + lon + ")";
            case Location(var name, Coordinates(var lat, var lon)) ->
                name + " is located in the Northern Hemisphere (" + lat + ", " + lon + ")";
            default -> "Unknown location object";
        };
    }
}
```

---

## 5. Text Blocks

Text blocks (finalized in Java 15) allow readable multi-line string literals enclosed by triple double-quotes (`"""`).

### Syntax and Indentation Stripping Rules

The opening delimiter requires three double-quotes followed immediately by a newline. The closing delimiter determines incidental whitespace stripping.

```java
package com.backend.core.strings;

public class SqlQueries {

    // Indentation is calculated relative to the closing delimiter or least-indented line
    public static final String FIND_ACTIVE_USERS_QUERY = """
            SELECT u.id, u.username, u.email, p.bio
            FROM users u
            LEFT JOIN profiles p ON u.id = p.user_id
            WHERE u.status = 'ACTIVE'
              AND u.created_at >= :sinceDate
            ORDER BY u.created_at DESC
            LIMIT :limit;
            """;

    public static final String JSON_PAYLOAD_TEMPLATE = """
            {
                "transactionId": "%s",
                "status": "APPROVED",
                "metadata": {
                    "source": "backend-gateway",
                    "retries": %d
                }
            }
            """.stripIndent();
}
```

### Escape Sequences in Text Blocks

- `\` (Line Continuation): Prevents inserting a newline character, letting developers break long lines in source code without affecting runtime string contents.
- `\s` (Explicit Space): Preserves trailing whitespace that would otherwise be trimmed during stripping.

```java
public class TextBlockEscapes {
    public static void main(String[] args) {
        String singleLine = """
                This is a very long line of text that is defined \
                across multiple source lines in Java code without \
                introducing newline characters into the final string.
                """;

        String fixedWidthRecord = """
                PROD_001  \s
                PROD_002  \s
                """;

        System.out.println("Contains newlines: " + singleLine.contains("\n")); // false
    }
}
```

---

## 6. Streams API Deep Dive

The Java Streams API delivers functional transformations over sequences of elements. Streams are lazy; computation only executes when a terminal operation is invoked.

### Core Pipelines: `filter`, `map`, `flatMap`, `reduce`, `collect`

```java
package com.backend.core.streams;

import java.util.*;
import java.util.stream.Collectors;

public record Item(String id, String category, double price) {}
public record CustomerOrder(String orderId, List<Item> items, boolean completed) {}

public class StreamPipelineDemo {

    public double calculateTotalRevenueForCategory(List<CustomerOrder> orders, String category) {
        return orders.stream()
                .filter(CustomerOrder::completed)
                .flatMap(order -> order.items().stream())
                .filter(item -> item.category().equalsIgnoreCase(category))
                .mapToDouble(Item::price)
                .reduce(0.0, Double::sum);
    }
}
```

### Advanced Collectors: `groupingBy` and `teeing`

`Collectors.groupingBy` classifies elements into maps. Downstream collectors allow further transformations on mapped values.

```java
public class AdvancedCollectorsDemo {

    // Multi-level grouping and downstream mapping
    public Map<String, List<String>> itemIdsByCategory(List<Item> items) {
        return items.stream()
                .collect(Collectors.groupingBy(
                        Item::category,
                        Collectors.mapping(Item::id, Collectors.toList())
                ));
    }

    public Map<String, DoubleSummaryStatistics> priceStatsByCategory(List<Item> items) {
        return items.stream()
                .collect(Collectors.groupingBy(
                        Item::category,
                        Collectors.summarizingDouble(Item::price)
                ));
    }

    // Collectors.teeing (Java 12) runs two collectors and merges their results
    public record PriceRange(double minPrice, double maxPrice) {}

    public PriceRange calculatePriceRange(List<Item> items) {
        return items.stream().collect(Collectors.teeing(
                Collectors.minBy(Comparator.comparingDouble(Item::price)),
                Collectors.maxBy(Comparator.comparingDouble(Item::price)),
                (minOpt, maxOpt) -> new PriceRange(
                        minOpt.map(Item::price).orElse(0.0),
                        maxOpt.map(Item::price).orElse(0.0)
                )
        ));
    }
}
```

### Parallel Streams and Spliterators

Parallel streams leverage the `ForkJoinPool.commonPool()` to distribute work across cores. However, parallel execution introduces overhead from thread synchronization, splitting, and merging.

```java
package com.backend.core.streams;

import java.util.List;
import java.util.Spliterator;
import java.util.concurrent.ThreadLocalRandom;
import java.util.stream.IntStream;

public class ParallelStreamConsiderations {

    public static double benchmarkCalculation(List<Double> numbers) {
        // Parallel streams are effective when N * Q > 10,000
        // N = number of elements, Q = computational cost per element
        return numbers.parallelStream()
                .map(n -> Math.sqrt(n) * Math.sin(n))
                .reduce(0.0, Double::sum);
    }

    public static void inspectSpliterator(List<String> list) {
        Spliterator<String> spliterator = list.spliterator();
        System.out.println("Spliterator Characteristics: " + spliterator.characteristics());
        System.out.println("Exact size: " + spliterator.hasCharacteristics(Spliterator.SIZED));
        System.out.println("Ordered: " + spliterator.hasCharacteristics(Spliterator.ORDERED));
    }
}
```

### Primitive Streams (`IntStream`, `LongStream`, `DoubleStream`)

Primitive streams eliminate the boxing and unboxing penalties associated with wrapper objects such as `Integer` and `Double`.

```java
public class PrimitiveStreamDemo {
    public static long calculateSumOfSquares(int limit) {
        return IntStream.rangeClosed(1, limit)
                .mapToLong(i -> (long) i * i)
                .sum();
    }
}
```

---

## 7. Lambdas and Functional Interfaces

A functional interface declares exactly one abstract method (`SAM` contract), marked with `@FunctionalInterface`.

### Built-in Standard Functional Interfaces

| Interface | Method Signature | Use Case |
|---|---|---|
| `Function<T, R>` | `R apply(T t)` | Value transformation |
| `BiFunction<T, U, R>` | `R apply(T t, U u)` | Combining two values |
| `Predicate<T>` | `boolean test(T t)` | Filtering and conditional checks |
| `BiPredicate<T, U>` | `boolean test(T t, U u)` | Testing two arguments |
| `Consumer<T>` | `void accept(T t)` | Side effects and consumption |
| `BiConsumer<T, U>` | `void accept(T t, U u)` | Consuming key-value pairs |
| `Supplier<T>` | `T get()` | Factory and lazy computation |
| `UnaryOperator<T>` | `T apply(T t)` | In-place transformation of type T |
| `BinaryOperator<T>` | `T apply(T t1, T t2)` | Reductions and math aggregations |

### Custom Functional Interfaces and Method References

```java
package com.backend.core.functional;

import java.util.Objects;
import java.util.function.Function;

@FunctionalInterface
public interface TriFunction<T, U, V, R> {
    R apply(T t, U u, V v);

    default <W> TriFunction<T, U, V, W> andThen(Function<? super R, ? extends W> after) {
        Objects.requireNonNull(after);
        return (T t, U u, V v) -> after.apply(this.apply(t, u, v));
    }
}
```

Method references offer concise alternatives to lambda expressions across four patterns:
1. **Static Reference**: `Math::max` equivalent to `(a, b) -> Math.max(a, b)`
2. **Bound Instance Reference**: `System.out::println` equivalent to `x -> System.out.println(x)`
3. **Unbound Instance Reference**: `String::toUpperCase` equivalent to `s -> s.toUpperCase()`
4. **Constructor Reference**: `ArrayList::new` equivalent to `() -> new ArrayList<>()`

---

## 8. Optional Handling and Anti-Patterns

`Optional<T>` is a container object designed explicitly to represent the absence of a return value without resorting to `null`.

### Idiomatic Usage

```java
package com.backend.core.optional;

import java.util.Optional;

public record User(String id, String email, Optional<String> phoneNumber) {}

public class OptionalUsageService {

    public String resolveUserContact(User user) {
        return user.phoneNumber()
                .filter(phone -> phone.startsWith("+1"))
                .map(phone -> "US Contact: " + phone)
                .orElseGet(() -> "Fallback Email: " + user.email());
    }

    public String findActiveEmail(Optional<User> userOpt) {
        return userOpt
                .map(User::email)
                .filter(email -> email.endsWith("@company.com"))
                .orElseThrow(() -> new IllegalStateException("Valid company email required"));
    }
}
```

### Differences: `orElse()` vs `orElseGet()`

- `orElse(T other)`: The fallback parameter is evaluated eagerly, regardless of whether the `Optional` is present or empty.
- `orElseGet(Supplier<? extends T> supplier)`: The fallback supplier is executed lazily, only if the `Optional` is empty.

```java
public class OrElseEvaluationDemo {

    public String expensiveDefault() {
        // Expensive database call or network request
        System.out.println("Executing expensive fallback...");
        return "default_computed_value";
    }

    public void testEvaluation() {
        Optional<String> present = Optional.of("existing_value");

        // BAD: expensiveDefault() executes even though present contains a value
        String result1 = present.orElse(expensiveDefault());

        // GOOD: expensiveDefault() is never executed because supplier is skipped
        String result2 = present.orElseGet(this::expensiveDefault);
    }
}
```

### Critical Optional Anti-Patterns

1. **Calling `.get()` unconditionally**: Always use `.orElse()`, `.orElseGet()`, `.orElseThrow()`, or pattern inspect with `.ifPresent()`.
2. **Optional as method arguments**: Do not use `public void save(Optional<User> user)`. Use method overloading instead.
3. **Optional as class fields or record components**: `Optional` does not implement `Serializable` and adds pointer indirection. Use nullable fields with explicit `Optional`-returning accessors instead.
4. **Optional inside collections**: Never wrap elements in collections (e.g., `List<Optional<String>>`). Store clean values or empty collections.

---

## 9. Local Variable Type Inference (`var`)

Introduced in Java 10, `var` enables the compiler to infer the static type of local variables from their initializer expression.

### Rules of Usage

```java
package com.backend.core.inference;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class VarUsageRules {

    public void validUsages() throws IOException {
        // 1. Local variable with immediate initializer
        var message = "Hello, Backend!"; // Inferred as String
        var users = List.of("Alice", "Bob", "Charlie"); // Inferred as List<String>
        var lookup = new HashMap<String, List<Integer>>(); // Clear type inference

        // 2. Loop indices and iteration variables
        for (var i = 0; i < users.size(); i++) {
            System.out.println(i + ": " + users.get(i));
        }
        for (var user : users) {
            System.out.println(user);
        }

        // 3. Try-with-resources variables
        try (var reader = new BufferedReader(new FileReader("config.properties"))) {
            var line = reader.readLine();
            System.out.println(line);
        }

        // 4. In lambda parameter expressions when annotations are required
        // (@NotNull var a, var b) -> a.compareTo(b);
    }

    /*
     * PROHIBITED USAGES (Compilation Errors):
     * 
     * 1. Class fields:
     *    private var status = "ACTIVE"; // COMPILATION ERROR
     * 
     * 2. Method parameter types:
     *    public void execute(var task) {} // COMPILATION ERROR
     * 
     * 3. Method return types:
     *    public var calculate() { return 42; } // COMPILATION ERROR
     * 
     * 4. Variable declarations without initializer:
     *    var uninitialized; // COMPILATION ERROR
     * 
     * 5. Initialized to null:
     *    var item = null; // COMPILATION ERROR: Cannot infer type from null
     */
}
```

---

## 10. Virtual Threads and Structured Concurrency

Virtual Threads (Project Loom, finalized in Java 21) introduce lightweight, user-mode threads managed by the Java Virtual Machine rather than the underlying Operating System.

### Platform Threads vs Virtual Threads

- **Platform Threads**: Wrapper around OS kernel threads. Heavyweight (~1MB memory stack reservation). Creation cost is high. Limited to thousands per process.
- **Virtual Threads**: Managed entirely in JVM memory. Extremely lightweight (few hundred bytes initially). Millions can run concurrently. They yield their carrier thread when performing blocking I/O (sockets, files, locks).

### Creating Virtual Threads

```java
package com.backend.core.loom;

import java.time.Duration;
import java.util.concurrent.Executors;
import java.util.stream.IntStream;

public class VirtualThreadLauncher {

    public static void main(String[] args) {
        // Direct builder launch
        Thread vThread = Thread.ofVirtual()
                .name("user-worker-", 1)
                .start(() -> {
                    System.out.println("Running virtual thread: " + Thread.currentThread());
                });

        // Executor service designed for virtual threads (one per task)
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            IntStream.range(0, 50_000).forEach(index -> {
                executor.submit(() -> {
                    Thread.sleep(Duration.ofMillis(200)); // Non-blocking for OS carrier thread
                    return index * 2;
                });
            });
        } // Executor auto-waits for all virtual tasks to complete on close
    }
}
```

### The Pinning Problem

A virtual thread becomes **pinned** to its carrier OS thread when executing:
1. Inside a `synchronized` block or method.
2. Inside a native JNI call.

When pinned, blocking I/O blocks the underlying OS carrier thread rather than unmounting the virtual thread. In Java 21 codebases, replace `synchronized` blocks that guard blocking I/O with `java.util.concurrent.locks.ReentrantLock`.

```java
import java.util.concurrent.locks.ReentrantLock;

public class VirtualThreadSafeResource {
    private final ReentrantLock lock = new ReentrantLock();

    public void processIoSafely() {
        lock.lock();
        try {
            // Safe: Virtual thread unmounts cleanly during socket/disk operations
            performNetworkCall();
        } finally {
            lock.unlock();
        }
    }

    private void performNetworkCall() {
        // Blocking I/O
    }
}
```

### Structured Concurrency (Java 21 Preview)

Structured concurrency treats groups of related tasks running in different threads as a single atomic unit of work, preventing orphan threads and resource leaks.

```java
package com.backend.core.loom;

import java.util.concurrent.StructuredTaskScope;
import java.util.function.Supplier;

public class OrderAggregationService {

    public record CustomerDetails(String id, String name) {}
    public record OrderSummary(CustomerDetails customer, double total) {}

    public OrderSummary loadOrderDetails(String customerId) throws InterruptedException {
        // ShutdownOnFailure cancels remaining tasks if any subtask fails
        try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
            Supplier<CustomerDetails> customerSubtask = scope.fork(() -> fetchCustomer(customerId));
            Supplier<Double> balanceSubtask = scope.fork(() -> fetchTotalBalance(customerId));

            // Wait for both tasks to complete or throw on failure
            scope.join();
            scope.throwIfFailed(IllegalStateException::new);

            return new OrderSummary(customerSubtask.get(), balanceSubtask.get());
        }
    }

    private CustomerDetails fetchCustomer(String id) {
        return new CustomerDetails(id, "Jane Doe");
    }

    private double fetchTotalBalance(String id) {
        return 450.75;
    }
}
```

---

## 11. Sequenced Collections

Before Java 21, querying the first or last elements or traversing in reverse order was inconsistent across standard collection implementations (e.g., `list.get(0)` vs `deque.getFirst()` vs `sortedSet.first()`). Java 21 introduced unified interfaces: `SequencedCollection`, `SequencedSet`, and `SequencedMap`.

### Hierarchy and Methods

```
Collection
    └── SequencedCollection
            ├── List
            ├── Deque
            └── SequencedSet
                    ├── LinkedHashSet
                    └── SortedSet
```

Key operations:
- `void addFirst(E e)`
- `void addLast(E e)`
- `E getFirst()`
- `E getLast()`
- `E removeFirst()`
- `E removeLast()`
- `SequencedCollection<E> reversed()`

```java
package com.backend.core.collections;

import java.util.ArrayDeque;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.SequencedCollection;
import java.util.SequencedMap;

public class SequencedCollectionsDemo {

    public static void demonstrateSequencedCollection() {
        SequencedCollection<String> sequence = new ArrayDeque<>(List.of("alpha", "beta", "gamma"));

        sequence.addFirst("start");
        sequence.addLast("end");

        System.out.println("First: " + sequence.getFirst()); // "start"
        System.out.println("Last: " + sequence.getLast());   // "end"

        // Reversed view without copying
        SequencedCollection<String> reversedView = sequence.reversed();
        System.out.println("Reversed first: " + reversedView.getFirst()); // "end"
    }

    public static void demonstrateSequencedMap() {
        SequencedMap<String, Integer> map = new LinkedHashMap<>();
        map.put("one", 1);
        map.put("two", 2);
        map.put("three", 3);

        System.out.println("First Entry: " + map.firstEntry()); // one=1
        System.out.println("Last Entry: " + map.lastEntry());   // three=3

        // Mutating ends directly
        map.putFirst("zero", 0);
        map.putLast("four", 4);

        System.out.println("Reversed keys: " + map.reversed().keySet());
    }
}
```

---

## 12. Modern String API Enhancements

From Java 11 through Java 21, the `java.lang.String` class acquired numerous utility methods that replace external libraries such as Apache Commons Lang or Guava.

```java
package com.backend.core.strings;

import java.util.List;
import java.util.stream.Collectors;

public class ModernStringMethods {

    public static void main(String[] args) {
        // 1. isBlank() checks for empty or whitespace-only content
        String whitespace = "   \t \n ";
        System.out.println("isBlank: " + whitespace.isBlank()); // true
        System.out.println("isEmpty: " + whitespace.isEmpty()); // false

        // 2. strip(), stripLeading(), stripTrailing() are Unicode-aware (unlike trim())
        String raw = "\u2005 Hello World! \u2005";
        System.out.println("Stripped: '" + raw.strip() + "'");

        // 3. repeat(int count)
        String separator = "=".repeat(20);
        System.out.println(separator);

        // 4. lines() returns a Stream<String> split by newlines
        String multiline = "Line 1\nLine 2\r\nLine 3";
        List<String> lineList = multiline.lines()
                .map(String::toUpperCase)
                .collect(Collectors.toList());
        System.out.println("Processed lines: " + lineList);

        // 5. indent(int n) adjusts margin spacing
        String indented = "Block content".indent(4);
        System.out.print(indented);

        // 6. formatted(Object... args) instance method equivalent to String.format()
        String formatted = "Status: %s, Code: %d".formatted("ACTIVE", 200);
        System.out.println(formatted);

        // 7. transform(Function<String, R>) enables fluent functional composition
        Integer processedLength = "  backend_service  "
                .strip()
                .toUpperCase()
                .transform(String::length);
        System.out.println("Processed Length: " + processedLength);
    }
}
```

---

## 13. CompletableFuture and Asynchronous Pipelines

`CompletableFuture<T>` represents a promise of an eventual asynchronous computation result, supporting non-blocking functional composition and error handling.

### Asynchronous Pipeline Construction

```java
package com.backend.core.async;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class AsyncPipelineService {

    private final ExecutorService ioExecutor = Executors.newFixedThreadPool(16);

    public record User(String id, String profileId) {}
    public record Profile(String profileId, String preferences) {}
    public record EnrichedUserData(User user, Profile profile, double balance) {}

    public CompletableFuture<EnrichedUserData> loadUserDataAsync(String userId) {
        // 1. Initial async fetch
        return CompletableFuture.supplyAsync(() -> fetchUser(userId), ioExecutor)
                // 2. thenCompose flattens dependent async calls (flatMap equivalent)
                .thenCompose(user -> {
                    CompletableFuture<Profile> profileFuture = 
                            CompletableFuture.supplyAsync(() -> fetchProfile(user.profileId()), ioExecutor);
                    CompletableFuture<Double> balanceFuture = 
                            CompletableFuture.supplyAsync(() -> fetchBalance(user.id()), ioExecutor);

                    // 3. thenCombine joins two independent async calculations
                    return profileFuture.thenCombine(balanceFuture, 
                            (profile, balance) -> new EnrichedUserData(user, profile, balance));
                })
                // 4. exceptionally provides fallback upon failure
                .exceptionally(throwable -> {
                    System.err.println("Failed to enrich user data: " + throwable.getMessage());
                    return new EnrichedUserData(new User(userId, "unknown"), new Profile("none", "default"), 0.0);
                });
    }

    private User fetchUser(String id) { return new User(id, "p-100"); }
    private Profile fetchProfile(String profileId) { return new Profile(profileId, "DARK_THEME"); }
    private double fetchBalance(String userId) { return 1500.0; }
}
```

### Fan-Out and Coordination: `allOf` and `anyOf`

```java
package com.backend.core.async;

import java.util.List;
import java.util.concurrent.CompletableFuture;

public class MultiFutureCoordinator {

    public CompletableFuture<List<String>> executeAllTasks(List<CompletableFuture<String>> futures) {
        CompletableFuture<Void> allFuturesDone = CompletableFuture.allOf(
                futures.toArray(new CompletableFuture[0])
        );

        // Map over all completed futures when all succeed
        return allFuturesDone.thenApply(v ->
                futures.stream()
                        .map(CompletableFuture::join)
                        .toList()
        );
    }
}
```

---

## 14. Modern Collections and Memory Trade-Offs

Java 9 introduced immutable collection factory methods (`List.of()`, `Set.of()`, `Map.of()`). Selecting the appropriate collection implementation requires understanding memory layouts, caching characteristics, and algorithmic complexity.

### Unmodifiable Factory Methods

```java
package com.backend.core.collections;

import java.util.List;
import java.util.Map;
import java.util.Set;

public class ImmutableCollectionsDemo {

    public void demonstrateFactories() {
        // Creates compact, unmodifiable instances
        List<String> list = List.of("A", "B", "C");
        Set<Integer> set = Set.of(1, 2, 3);
        Map<String, String> map = Map.of("key1", "val1", "key2", "val2");

        // Map.ofEntries for arbitrary key-value pairs
        Map<Integer, String> largeMap = Map.ofEntries(
                Map.entry(1, "Alpha"),
                Map.entry(2, "Beta"),
                Map.entry(3, "Gamma")
        );

        // Defensive copy methods
        List<String> safeCopy = List.copyOf(list);

        /*
         * Key characteristics:
         * 1. Null elements are rejected immediately (NullPointerException).
         * 2. Attempting modification throws UnsupportedOperationException.
         * 3. Set.of and Map.of randomize iteration order to prevent dependence on order.
         * 4. Highly memory-efficient: List.of for 1-2 elements uses dedicated internal classes.
         */
    }
}
```

### Memory and Performance: `ArrayList` vs `LinkedList` vs `ArrayDeque`

```
Data Structure Characteristics Comparison:
--------------------------------------------------------------------------------------
Structure     Element Storage       Random Access   Cache Locality   Memory Overhead
--------------------------------------------------------------------------------------
ArrayList     Contiguous Object[]   O(1)            High             Low (array capacity buffer)
LinkedList    Doubly Linked Nodes   O(N)            Very Low         High (24-32 bytes per node)
ArrayDeque    Circular Object[]     O(1) amortized  High             Lowest (no node wrappers)
--------------------------------------------------------------------------------------
```

### Why `LinkedList` Is Almost Never Recommended

1. **CPU Cache Line Inefficiency**: `ArrayList` and `ArrayDeque` store elements in contiguous memory blocks. When the CPU fetches an element into the L1/L2 cache line, adjacent pointers are preloaded. `LinkedList` allocates nodes independently on the heap; traversing pointers forces continuous cache misses.
2. **Node Overhead**: Every element in a `LinkedList` requires a `Node` object containing `item`, `next`, and `prev` references (at least 24 bytes of overhead per entry on 64-bit JVMs with compressed OOPs).
3. **Queue / Deque Use-Cases**: `ArrayDeque` outperforms `LinkedList` as both a FIFO queue and LIFO stack due to minimal allocation and cache-friendly contiguous circular arrays.
