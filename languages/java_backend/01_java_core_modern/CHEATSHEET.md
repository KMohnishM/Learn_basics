# Modern Java Quick Reference Cheatsheet

## 1. Java Version & Feature Timeline

| Version | Release | Support | Key Features |
|---|---|---|---|
| Java 8 | 2014 | LTS | Lambdas, Stream API, java.time, Optional, CompletableFuture |
| Java 11 | 2018 | LTS | HTTP Client, String (`isBlank`, `lines`, `strip`), var in lambdas |
| Java 17 | 2021 | LTS | Sealed classes, Records, Pattern matching for `instanceof`, Text blocks |
| Java 21 | 2023 | LTS | Virtual Threads, Sequenced Collections, Pattern matching switch, Record patterns |

## 2. Stream Operations Reference

| Operation | Type | Function Signature / Return | Description |
|---|---|---|---|
| `filter(Predicate<T>)` | Intermediate | `Stream<T>` | Retains elements matching condition |
| `map(Function<T, R>)` | Intermediate | `Stream<R>` | 1-to-1 transformation |
| `flatMap(Function<T, Stream<R>>)`| Intermediate | `Stream<R>` | 1-to-many flattening transformation |
| `distinct()` | Intermediate | `Stream<T>` | Eliminates duplicate elements based on `equals` |
| `reduce(id, BinaryOperator<T>)` | Terminal | `T` | Aggregates elements into single value |
| `collect(Collector)` | Terminal | `R` | Accumulates into collections or aggregations |
| `Collectors.groupingBy(fn, down)`| Collector | `Collector<T, ?, Map<K, D>>` | Groups by key with downstream reduction |
| `Collectors.teeing(c1, c2, merger)`| Collector | `Collector<T, ?, R>` | Merges two collectors in a single pass |

## 3. Core Functional Interfaces

| Interface | Method Signature | Primary Backend Purpose |
|---|---|---|
| `Predicate<T>` | `boolean test(T t)` | Filtering, validation rules, guards |
| `Function<T, R>` | `R apply(T t)` | Mapping, entity to DTO conversion |
| `Consumer<T>` | `void accept(T t)` | Logging, event dispatching, mutations |
| `Supplier<T>` | `T get()` | Lazy evaluation, object factories |
| `BiFunction<T, U, R>`| `R apply(T t, U u)` | Joining two models, mathematical reductions |
| `UnaryOperator<T>` | `T apply(T t)` | In-place transformations, normalization |

## 4. Optional API Reference

| Method | Behavior When Present | Behavior When Empty |
|---|---|---|
| `orElse(value)` | Returns contained value | Evaluates and returns fallback eagerly |
| `orElseGet(supplier)` | Returns contained value | Evaluates supplier lazily and returns value |
| `orElseThrow(supplier)`| Returns contained value | Throws exception returned by supplier |
| `map(mapper)` | Returns `Optional` of mapped value | Returns `Optional.empty()` |
| `flatMap(mapper)` | Flattens and returns result `Optional`| Returns `Optional.empty()` |
| `ifPresent(consumer)` | Executes consumer with value | Does nothing |
| `ifPresentOrElse(c, r)` | Executes consumer `c` | Executes runnable `r` |

## 5. Records Syntax Reference

```java
public record UserDto(UUID id, String email, int age) implements Serializable {
    public UserDto { // Compact constructor for validation
        Objects.requireNonNull(email);
        if (age < 0) throw new IllegalArgumentException("Negative age");
    }
}
```

## 6. Sealed Classes & Interfaces

```java
public sealed interface Result<T> permits Success, Failure {}
public final record Success<T>(T data) implements Result<T> {}
public final record Failure<T>(String error, Throwable cause) implements Result<T> {}
```

## 7. Pattern Matching Syntax (Java 21)

```java
String msg = switch (result) {
    case Success<String> s when !s.data().isBlank() -> "Received: " + s.data();
    case Success<?> s -> "Received generic success";
    case Failure<?> f -> "Error: " + f.error();
};
```
