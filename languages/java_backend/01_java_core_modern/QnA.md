# Modern Java Core: Interview Questions and Answers

---

### Question 1: What are sealed classes and when would you use them over enums?

**Answer:**
Sealed classes and interfaces (introduced in Java 17) restrict which other classes or interfaces may extend or implement them. While an enum models a fixed set of constant singleton instances, a sealed hierarchy models a fixed set of distinct types (Algebraic Data Types), where each subtype can maintain its own mutable or immutable state, independent constructors, and distinct methods.

Enums fall short when different variants need to hold fundamentally different payload structures. For example, in an event-driven payment system, a card payment needs a token and CVV, while a bank transfer needs an IBAN and BIC. If modeled with an enum, all fields would have to be merged into a single awkward structure with nullable fields. Sealed types solve this cleanly:

```java
public sealed interface PaymentMethod permits CreditCard, BankTransfer, Cash {
    void process();
}

public record CreditCard(String cardNumber, String cvv) implements PaymentMethod {
    @Override public void process() { /* charge card */ }
}

public record BankTransfer(String iban, String bic) implements PaymentMethod {
    @Override public void process() { /* wire transfer */ }
}

public record Cash(String currency) implements PaymentMethod {
    @Override public void process() { /* record cash receipt */ }
}
```

Use enums when modeling fixed constants (e.g., `DaysOfWeek`, `OrderStatus.PENDING`). Use sealed classes when modeling a closed polymorphism hierarchy where variants have distinct fields, behaviors, or lifecycle characteristics.

---

### Question 2: How does pattern matching in switch expressions differ from traditional switch statements?

**Answer:**
Traditional switch statements in older Java versions suffered from several critical limitations: they operated exclusively on primitive types, their boxed wrappers, enums, and Strings; they required explicit `break` statements to prevent fall-through bugs; they could not return values directly as expressions; and they could not inspect object types or extract values.

Pattern matching in switch expressions (standardized in Java 21) transforms switch into a powerful type-checking and deconstruction engine. Key architectural differences include:

1. **Type testing and automatic casting**: Cases can match against target object types and bind variables directly without casting.
2. **Exhaustiveness checking**: The compiler verifies that all possible subtypes of a sealed hierarchy are covered, making the `default` branch optional.
3. **No fall-through**: The arrow syntax (`->`) eliminates accidental fall-through bugs.
4. **Expression evaluation**: A switch expression yields a value directly to an assignment.

```java
public String describeEvent(Object event) {
    return switch (event) {
        case Integer i -> "Integer payload with value: " + i;
        case String s when !s.isBlank() -> "Non-empty text payload: " + s.trim();
        case String s -> "Empty or whitespace text";
        case double[] numbers -> "Array of double with length: " + numbers.length;
        case null -> "Encountered null payload";
        default -> "Unsupported payload type: " + event.getClass().getName();
    };
}
```

---

### Question 3: Explain the difference between orElse() and orElseGet() in Optional.

**Answer:**
Both `orElse()` and `orElseGet()` provide a fallback value when an `Optional` instance is empty. However, their critical difference lies in the timing of value evaluation: eager evaluation versus lazy evaluation.

- `orElse(T other)` accepts an already-evaluated object reference. Because Java evaluates method parameters before method invocation, the expression passed to `orElse()` executes regardless of whether the `Optional` contains a value or not.
- `orElseGet(Supplier<? extends T> supplier)` accepts a functional interface. The supplier's `.get()` method is executed lazily, only if the `Optional` is determined to be empty.

If the fallback involves expensive operations (database queries, network calls, or memory allocations), using `orElse()` causes significant unnecessary performance overhead and unexpected side effects.

```java
public String fetchConfiguration(String key) {
    Optional<String> cachedValue = Optional.of("CACHED_VALUE");

    // EAGER: generateTokenFromRemoteAuthServer() is invoked even though cachedValue is present!
    String eager = cachedValue.orElse(generateTokenFromRemoteAuthServer());

    // LAZY: generateTokenFromRemoteAuthServer() is NEVER invoked because value exists
    String lazy = cachedValue.orElseGet(this::generateTokenFromRemoteAuthServer);

    return lazy;
}

private String generateTokenFromRemoteAuthServer() {
    System.out.println("Calling external auth service over HTTP...");
    return "NEW_REMOTE_TOKEN";
}
```

---

### Question 4: How do Virtual Threads differ from platform threads and what problem do they solve?

**Answer:**
Platform threads in Java wrap operating system (OS) kernel threads on a 1:1 basis. OS threads are heavy resources: each reserves roughly 1MB of memory for call stacks, and switching context between them requires kernel transitions. Consequently, an application cannot scale beyond several thousand active platform threads without running out of memory or exhausting OS scheduler resources.

Virtual Threads (Project Loom, Java 21) decouple Java threads from OS kernel threads using an M:N scheduling model. Virtual threads are lightweight user-mode threads managed entirely by the JVM, holding only hundreds of bytes of initial memory.

When a virtual thread initiates a blocking operation (such as JDBC queries, HTTP requests, or socket reads), the JVM automatically unmounts the virtual thread from its underlying OS "carrier" thread and stores its stack in heap memory. The carrier thread immediately executes other virtual threads. Once the I/O completes, the JVM reschedules the virtual thread onto an available carrier thread.

```java
public void executeBatchOperations(List<Runnable> tasks) {
    // Spawns up to 100,000 concurrent tasks without exhausting system memory
    try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
        for (var task : tasks) {
            executor.submit(() -> {
                task.run(); // Blocking I/O inside this task yields carrier OS thread
                return null;
            });
        }
    } // Automatically waits for all submitted tasks to finish
}
```

This solves the throughput bottleneck of the traditional "thread-per-request" model without requiring complex reactive programming models.

---

### Question 5: What is the difference between map() and flatMap() in Streams?

**Answer:**
In the Java Streams API, both `map()` and `flatMap()` are intermediate operations that transform input elements. The distinction lies in whether the mapper function returns a single element or a nested stream of elements.

- `map(Function<T, R>)`: Applies a one-to-one transformation. For each element `T`, it produces exactly one output element of type `R`. If the mapping function yields a container or collection, `map()` produces a stream of containers (e.g., `Stream<List<R>>`).
- `flatMap(Function<T, Stream<R>>)`: Applies a one-to-many transformation and flattens the resulting streams. For each element `T`, the function returns a `Stream<R>`, and `flatMap()` flattens all individual sub-streams into a single unified `Stream<R>`.

```java
public record OrderItem(String productCode, int quantity) {}
public record CustomerOrder(String orderId, List<OrderItem> items) {}

public void analyzeOrders(List<CustomerOrder> orders) {
    // map produces Stream<List<OrderItem>> (nested structure)
    List<List<OrderItem>> nested = orders.stream()
            .map(CustomerOrder::items)
            .toList();

    // flatMap flattens all internal item lists into a single continuous stream
    List<String> distinctProducts = orders.stream()
            .flatMap(order -> order.items().stream())
            .map(OrderItem::productCode)
            .distinct()
            .toList();

    System.out.println("Distinct products ordered: " + distinctProducts);
}
```

---

### Question 6: When should you use records vs regular classes vs Lombok @Data?

**Answer:**
Records, regular classes, and Lombok `@Data` represent three different approaches to data modeling in Java, each suited to distinct architectural requirements:

1. **Use Records** for transparent, immutable data carriers (such as REST API request/response DTOs, query projections, Kafka event payloads, and map composite keys). Records provide built-in compiler-enforced immutability, canonical constructors, correct `equals`/`hashCode`/`toString`, and secure serialization without reflection hacks.
2. **Use Regular Classes** when domain entities require mutable state, inheritance hierarchies (records cannot extend classes), JPA/Hibernate entities (which require zero-arg constructors, non-final fields, and dirty-checking proxies), or complex encapsulation where internal state differs from the public API.
3. **Use Lombok `@Data`** as a transitional tool in legacy codebases (pre-Java 16) or where mutable JavaBean conventions are mandated by older frameworks. However, `@Data` generates mutable structures by default and relies on annotation processing plugins that can break across compiler upgrades.

```java
// Idiomatic Record: Immutable, concise, transparent
public record UserSummaryDto(Long id, String email, Instant registeredAt) {
    public UserSummaryDto {
        Objects.requireNonNull(email, "email must not be null");
    }
}

// Regular Class: Appropriate for JPA entities requiring mutability and proxying
@Entity
@Table(name = "users")
public class UserEntity {
    @Id @GeneratedValue
    private Long id;
    private String email;

    protected UserEntity() {} // Required by Hibernate
    public Long getId() { return id; }
    public void setEmail(String email) { this.email = email; }
}
```

---

### Question 7: Explain Collectors.groupingBy with a downstream collector example.

**Answer:**
`Collectors.groupingBy` is a terminal stream collector that partitions elements into groups based on a classification function, storing results in a `Map<K, V>`. By default, the values in the map are lists of the classified items (`Map<K, List<T>>`).

A downstream collector allows developers to perform secondary aggregations, reductions, or transformations directly on the grouped elements rather than just gathering them into a list. This enables single-pass processing for complex analytical queries.

```java
public record Transaction(String category, double amount, String currency) {}

public class GroupingAnalytics {
    public void computeCategoryStats(List<Transaction> transactions) {
        // Downstream collector: sum transaction amounts per category
        Map<String, Double> totalAmountByCategory = transactions.stream()
                .collect(Collectors.groupingBy(
                        Transaction::category,
                        Collectors.summingDouble(Transaction::amount)
                ));

        // Downstream collector: collect unique currencies used per category
        Map<String, Set<String>> currenciesByCategory = transactions.stream()
                .collect(Collectors.groupingBy(
                        Transaction::category,
                        Collectors.mapping(Transaction::currency, Collectors.toSet())
                ));

        // Multi-level grouping: group by category, then by currency, counting occurrences
        Map<String, Map<String, Long>> countByCategoryAndCurrency = transactions.stream()
                .collect(Collectors.groupingBy(
                        Transaction::category,
                        Collectors.groupingBy(Transaction::currency, Collectors.counting())
                ));
    }
}
```

---

### Question 8: What are the rules for using var in Java?

**Answer:**
Local variable type inference (`var`), introduced in Java 10, allows the compiler to infer static types from initializer expressions. The variable remains strictly and statically typed at compile time; `var` does not introduce dynamic typing.

**Permitted Usages:**
1. Local variables inside methods, constructors, or initializer blocks that have an explicit initializer.
2. Index and iteration variables inside traditional `for` loops and enhanced `for-each` loops.
3. Resource variables inside `try-with-resources` statements.
4. Parameters of lambda expressions when applying annotations (e.g., `(@Nonnull var x, var y) -> x.concat(y)`).

**Prohibited Usages:**
1. Method parameters and return type declarations.
2. Class fields and instance variables.
3. Uninitialized declarations (e.g., `var x;` fails to compile).
4. Initializing with `null` (e.g., `var item = null;` fails because the compiler cannot infer a type).
5. Initializing with array literals without explicit types (e.g., `var arr = {1, 2};` is prohibited; must use `var arr = new int[]{1, 2};`).

```java
public void validateVarUsage() {
    // Valid: Inferred as Map<String, List<Integer>>
    var customerCache = new HashMap<String, List<Integer>>();

    // Valid: Try-with-resources
    try (var stream = Files.lines(Path.of("report.csv"))) {
        var count = stream.filter(line -> !line.isBlank()).count();
        System.out.println("Valid lines: " + count);
    } catch (IOException e) {
        // e cannot be declared with var in multi-catch
    }
}
```

---

### Question 9: How does thenCompose differ from thenApply in CompletableFuture?

**Answer:**
In asynchronous programming with `CompletableFuture`, both `thenApply` and `thenCompose` transform future outputs. Their core difference mirrors that of `map` versus `flatMap` in functional containers:

- `thenApply(Function<T, U>)`: Used for synchronous transformations. If the function returns a simple value `U`, `thenApply` wraps it into `CompletableFuture<U>`. However, if the function returns an asynchronous operation `CompletableFuture<U>`, `thenApply` produces a nested `CompletableFuture<CompletableFuture<U>>`.
- `thenCompose(Function<T, CompletableFuture<U>>)`: Used for chaining asynchronous operations. It unwraps and flattens the nested future, returning a single, unified `CompletableFuture<U>`.

```java
public class AsyncComparison {
    public CompletableFuture<String> fetchUserId(String token) {
        return CompletableFuture.supplyAsync(() -> "USER-9872");
    }

    public CompletableFuture<Double> fetchUserBalance(String userId) {
        return CompletableFuture.supplyAsync(() -> 1250.50);
    }

    public void demonstrate() {
        String token = "AUTH-TOKEN-123";

        // thenApply with async operation causes nested types:
        CompletableFuture<CompletableFuture<Double>> nested = fetchUserId(token)
                .thenApply(this::fetchUserBalance);

        // thenCompose flattens the future directly:
        CompletableFuture<Double> flattened = fetchUserId(token)
                .thenCompose(this::fetchUserBalance);

        flattened.thenAccept(balance -> System.out.println("Balance: " + balance));
    }
}
```

---

### Question 10: What are guarded patterns in switch expressions?

**Answer:**
Guarded patterns (standardized in Java 21) enhance pattern matching within `switch` expressions and statements by appending a boolean condition to a `case` label using the `when` keyword. The pattern matches only if both the type matches and the guard condition evaluates to `true`.

Prior to guarded patterns, developers had to match the type and then write verbose nested `if-else` statements inside the case body, reducing the clarity and expressiveness of the switch construct.

```java
public sealed interface OrderStatus permits Placed, Dispatched, Delivered, Cancelled {}
public record Placed(long orderId, double amount, boolean express) implements OrderStatus {}
public record Dispatched(long orderId, String trackingNumber) implements OrderStatus {}
public record Delivered(long orderId, Instant timestamp) implements OrderStatus {}
public record Cancelled(long orderId, String reason) implements OrderStatus {}

public class OrderDispatcher {
    public String determinePriority(OrderStatus status) {
        return switch (status) {
            case Placed p when p.express() && p.amount() > 500.0 ->
                "CRITICAL: High-value express order: " + p.orderId();
            case Placed p when p.express() ->
                "HIGH: Standard express order: " + p.orderId();
            case Placed p ->
                "NORMAL: Standard order: " + p.orderId();
            case Dispatched d when d.trackingNumber().startsWith("EXP-") ->
                "Express carrier tracking: " + d.trackingNumber();
            case Dispatched d ->
                "Standard postal tracking: " + d.trackingNumber();
            case Delivered d ->
                "Order delivered at: " + d.timestamp();
            case Cancelled c ->
                "Order cancelled: " + c.reason();
        };
    }
}
```

Guards allow fine-grained pattern partitioning while preserving switch exhaustiveness checks.

---

### Question 11: Explain the difference between stream() and parallelStream() — when is parallel actually faster?

**Answer:**
A sequential stream (`stream()`) processes all elements on the calling thread sequentially in a single pass. A parallel stream (`parallelStream()`) partitions data across multiple worker threads managed by the shared `ForkJoinPool.commonPool()`, processing chunks concurrently before merging the results.

Parallel streams do not automatically make code faster. In fact, for many workloads, parallel streams run substantially slower than sequential streams due to partitioning and synchronization overhead.

Parallel streams are faster only when the **N * Q formula** exceeds roughly 10,000:
- **N** is the number of elements in the collection.
- **Q** is the computational cost per element.

```java
public class ParallelBenchmark {
    // SCENARIO 1: Poor candidate for parallelStream
    // Small collection, cheap CPU operations, non-splittable data structure (LinkedList)
    public int slowParallel(LinkedList<Integer> list) {
        // SLOW: LinkedList cannot be split cleanly (O(N) splitting overhead)
        return list.parallelStream().mapToInt(x -> x + 1).sum();
    }

    // SCENARIO 2: Excellent candidate for parallelStream
    // Large array/ArrayList (O(1) split), expensive CPU calculation per element
    public double fastParallel(List<Double> largeData) {
        // FAST: ArrayList splits instantly; Math.pow and trig functions are CPU-heavy
        return largeData.parallelStream()
                .map(val -> Math.sin(val) * Math.cos(val) * Math.sqrt(val))
                .reduce(0.0, Double::sum);
    }
}
```

Avoid parallel streams when performing blocking I/O (which starves the common pool) or when using poorly splittable structures like `LinkedList` or `Stream.iterate`.

---

### Question 12: What is a compact constructor in a record?

**Answer:**
A compact constructor is a specialized constructor syntax available exclusively in Java records. Unlike canonical or custom constructors in traditional classes, a compact constructor omits the parameter list entirely and does not require explicit field assignments (`this.x = x;`).

Instead, the parameters of the compact constructor are implicitly declared with the same names and types as the record components. Developers use compact constructors to perform parameter validation, defensive copying, and data normalization. At the conclusion of the compact constructor block, the JVM automatically assigns all components to their corresponding private final fields.

```java
public record Money(BigDecimal amount, Currency currency) {
    // Compact constructor syntax - no parameter parentheses
    public Money {
        Objects.requireNonNull(amount, "Amount cannot be null");
        Objects.requireNonNull(currency, "Currency cannot be null");

        // Normalization: round to 2 decimal places
        amount = amount.setScale(2, RoundingMode.HALF_UP);

        // Validation rule
        if (amount.compareTo(BigDecimal.ZERO) < 0) {
            throw new IllegalArgumentException("Monetary amount cannot be negative: " + amount);
        }

        // Field assignment occurs automatically after this block completes
    }
}
```

This prevents boilerplate while ensuring invalid state can never be instantiated.

---

### Question 13: How does Collectors.teeing work?

**Answer:**
`Collectors.teeing` (introduced in Java 12) is a composite collector that forwards every stream element into two downstream collectors simultaneously and then merges their final results using a specified `BiFunction`.

Prior to `Collectors.teeing`, computing two distinct metrics over a stream (such as average and standard deviation, or minimum and maximum) required either iterating through the stream twice or creating a complex custom accumulator object. `Collectors.teeing` solves this by completing both aggregations in a single traversal pass.

```java
public record GradeReport(double average, double highestScore) {}

public class StudentAnalytics {
    public GradeReport calculatePerformance(List<Double> examScores) {
        return examScores.stream().collect(Collectors.teeing(
                // Downstream collector 1: compute average score
                Collectors.averagingDouble(Double::doubleValue),

                // Downstream collector 2: find maximum score
                Collectors.maxBy(Double::compareTo),

                // Merger function: combine results into domain record
                (avg, maxOpt) -> new GradeReport(
                        avg,
                        maxOpt.orElse(0.0)
                )
        ));
    }
}
```

This ensures single-pass efficiency while keeping code clean, functional, and expressive.

---

### Question 14: What is structured concurrency in Java 21?

**Answer:**
Traditional multithreaded programming in Java treats threads as independent execution contexts. If a parent task forks three child worker threads using an `ExecutorService`, the JVM maintains no inherent structural relationship between parent and children. If one child throws an exception, the other children continue executing as orphaned threads, consuming memory, CPU, and database connections.

Structured Concurrency (introduced in preview in Java 21 via `StructuredTaskScope`) treats split subtasks as a single unified unit of execution. The parent scope guarantees that all child threads conclude before the parent scope exits, enforcing syntactic scoping around asynchronous lifecycles.

```java
public record UserDashboard(UserProfile profile, AccountBalance balance) {}

public class DashboardService {
    public UserDashboard loadDashboard(String userId) throws Exception {
        // ShutdownOnFailure cancels all running siblings if any child task fails
        try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
            Subtask<UserProfile> profileTask = scope.fork(() -> fetchProfile(userId));
            Subtask<AccountBalance> balanceTask = scope.fork(() -> fetchBalance(userId));

            // Block until both complete or one fails
            scope.join();
            scope.throwIfFailed(ExecutionException::new);

            // Here, both subtasks are guaranteed to be finished successfully
            return new UserDashboard(profileTask.get(), balanceTask.get());
        } // Exiting try block guarantees all spawned threads are terminated
    }

    private UserProfile fetchProfile(String id) { return new UserProfile(id, "Alex"); }
    private AccountBalance fetchBalance(String id) { return new AccountBalance(id, 4500.0); }
}
```

Structured concurrency prevents thread leaks, simplifies cancellation propagation, and drastically improves thread dump readability.

---

### Question 15: What are the memory characteristics of List.of() vs ArrayList?

**Answer:**
`List.of()` and `ArrayList` have drastically different memory footprints, internal structures, and lifecycle contracts:

1. **Memory Footprint**:
   - `ArrayList` wraps a backing `Object[]` array. By default, it allocates an initial capacity (often 10 elements), meaning empty slots consume memory. In addition, an `ArrayList` object instance maintains an `int size` field and an `int modCount` field alongside object headers.
   - `List.of()` returns specialized immutable implementations. For 0 elements, it returns a shared singleton (`ImmutableCollections.EMPTY_LIST`). For 1 or 2 elements, it returns dedicated classes (`List12`) that store elements directly in instance fields, avoiding array allocation completely. For 3+ elements, it allocates an array sized exactly to the number of elements with zero capacity buffer.

2. **Null Safety**:
   - `ArrayList` allows `null` elements.
   - `List.of()` strictly forbids `null`, throwing `NullPointerException` during construction.

3. **Immutability and Thread Safety**:
   - `ArrayList` is mutable and not thread-safe.
   - `List.of()` is deeply unmodifiable, completely safe to share across threads without synchronization, and rejects mutations with `UnsupportedOperationException`.

```java
public class CollectionMemoryComparison {
    public void compareUsage() {
        // List.of: minimal memory, no unused capacity buffer, unmodifiable
        List<String> immutableList = List.of("alpha", "beta");

        // ArrayList: backing array overhead, capacity buffer, mutable
        List<String> mutableList = new ArrayList<>(List.of("alpha", "beta"));
        mutableList.add("gamma"); // Allowed
        // immutableList.add("gamma"); // Throws UnsupportedOperationException
    }
}
```
