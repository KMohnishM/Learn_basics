# Spring Data JPA Interview Questions and Answers

### Question 1: What is the N+1 problem and how do you solve it in Spring Data JPA?

**Answer:**
The N+1 select problem occurs when an application executes 1 initial SQL query to retrieve N entity records, and then executes N subsequent queries to load a lazy or eager association for each parent record. This leads to massive database overhead and latency:

```java
// Causes N+1 if customer is fetched in a loop
List<Order> orders = orderRepository.findAll(); // 1 query: SELECT * FROM orders;
for (Order order : orders) {
    String email = order.getCustomer().getEmail(); // N queries: SELECT * FROM customers WHERE id = ?;
}
```

Solutions:
1. `JOIN FETCH` in JPQL: Performs an eager join in a single database roundtrip:
```java
@Query("SELECT o FROM Order o JOIN FETCH o.customer JOIN FETCH o.items")
List<Order> findAllWithAssociations();
```
2. `@EntityGraph`: Declaratively instructs JPA to fetch associations eagerly without writing explicit queries:
```java
@EntityGraph(attributePaths = {"customer", "items"})
List<Order> findByStatus(OrderStatus status);
```
3. Hibernate `@BatchSize`: Loads associations in batches using `WHERE customer_id IN (?, ?, ...)`:
```java
@BatchSize(size = 30)
@OneToMany(mappedBy = "order", fetch = FetchType.LAZY)
private List<OrderItem> items = new ArrayList<>();
```

---

### Question 2: Explain the difference between FetchType.LAZY and FetchType.EAGER and when to use each.

**Answer:**
`FetchType.LAZY` and `FetchType.EAGER` dictate when associated entities or collections are loaded into memory from the database.

`FetchType.EAGER` forces Hibernate to load the associated entity immediately whenever the parent is fetched, typically generating a SQL join or immediate secondary select:
- In JPA, `@ManyToOne` and `@OneToOne` default to `EAGER`.
- Disadvantage: Incurs severe performance penalties and unexpected large joins across domain models. Best practice is to avoid `EAGER` mappings entirely.

`FetchType.LAZY` defers loading the associated entity or collection until it is explicitly accessed via a getter method. Hibernate replaces the association with a dynamic bytecode proxy:
- In JPA, `@OneToMany` and `@ManyToMany` default to `LAZY`.
- Advantage: Minimal initial query load; queries only load data when needed.
- Caveat: Accessing lazy associations outside of an active transaction throws `LazyInitializationException`.

```java
@Entity
public class Order {
    // Explicitly override default EAGER to LAZY
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "customer_id")
    private Customer customer;

    // Default is LAZY
    @OneToMany(mappedBy = "order", fetch = FetchType.LAZY)
    private List<OrderItem> items = new ArrayList<>();
}
```

---

### Question 3: What are the transaction propagation types in Spring and when would you use REQUIRES_NEW?

**Answer:**
Transaction propagation defines the boundary behavior when a transactional method calls another transactional method. Spring provides seven propagation types via `@Transactional(propagation = ...)`:
1. `REQUIRED` (Default): Joins current transaction; creates a new one if none exists.
2. `REQUIRES_NEW`: Suspends current transaction and executes inside an isolated, newly created physical transaction.
3. `SUPPORTS`: Executes transactionally if a transaction exists; executes non-transactionally otherwise.
4. `NOT_SUPPORTED`: Suspends current transaction and executes completely non-transactionally.
5. `MANDATORY`: Requires an existing active transaction; throws an exception if none exists.
6. `NEVER`: Throws an exception if an active transaction is present.
7. `NESTED`: Executes within a nested transaction using JDBC savepoints.

When to use `REQUIRES_NEW`:
Use `REQUIRES_NEW` when an auxiliary operation must succeed and commit regardless of whether the outer business transaction rolls back (e.g., audit logging, security event tracking, or decrementing retry attempts).

```java
@Service
public class AuditLogService {

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void recordSecurityAudit(String action, Long userId, String ipAddress) {
        AuditLog log = new AuditLog(action, userId, ipAddress, Instant.now());
        auditLogRepository.save(log);
        // This transaction commits independently, even if caller rolls back
    }
}
```

---

### Question 4: How do interface projections work and when are they better than returning entities?

**Answer:**
Interface projections in Spring Data JPA allow defining a Java interface with accessor methods representing only a subset of columns. Spring Data uses runtime dynamic proxies to map the underlying SQL query result set directly into the interface methods.

Interface projections are significantly better than returning entities when:
1. Only a few fields are needed for read-only displays (e.g., generating dropdowns, summary cards, or mobile feeds).
2. Entity graph retrieval would trigger heavy unwanted joins, large text/BLOB columns, or lazy initialization risks.
3. Memory efficiency is critical, as interface projections bypass Hibernate's persistence context entity state management and dirty checking overhead.

```java
public interface OrderHeaderProjection {
    Long getId();
    String getOrderNumber();
    BigDecimal getTotalAmount();

    // Open projection using SpEL
    @Value("#{target.orderNumber + ' - ' + target.status}")
    String getOrderSummary();
}
```

```java
@Repository
public interface OrderRepository extends JpaRepository<Order, Long> {
    // Only selects id, order_number, total_amount, and status from the database
    List<OrderHeaderProjection> findByCustomerId(Long customerId);
}
```

---

### Question 5: What is optimistic locking and how does @Version implement it?

**Answer:**
Optimistic locking is a concurrency control mechanism based on the assumption that conflicting updates are rare. Rather than locking database records during reads, it verifies at update time whether another transaction has modified the entity since it was read.

Implementation uses the `@Version` annotation on an integer, long, or timestamp field:
```java
@Entity
@Table(name = "accounts")
public class BankAccount {

    @Id
    private Long id;

    private BigDecimal balance;

    @Version
    private Long version;

    public void debit(BigDecimal amount) {
        this.balance = this.balance.subtract(amount);
    }
}
```

Execution mechanics:
1. Transaction A reads entity with `id = 1, version = 5`.
2. Transaction B reads entity with `id = 1, version = 5`.
3. Transaction A debits balance and commits:
   `UPDATE accounts SET balance = ?, version = 6 WHERE id = 1 AND version = 5;` (1 row updated).
4. Transaction B debits balance and attempts to commit:
   `UPDATE accounts SET balance = ?, version = 6 WHERE id = 1 AND version = 5;` (0 rows updated because version is now 6).
5. Hibernate detects 0 rows updated and immediately throws `OptimisticLockException` (wrapped in Spring as `ObjectOptimisticLockingFailureException`), allowing the application to retry or notify the client.

---

### Question 6: How does @EntityGraph work and how is it different from JOIN FETCH?

**Answer:**
Both `@EntityGraph` and `JOIN FETCH` solve the N+1 select problem by fetching associations eagerly within a single SQL statement, but they operate through different mechanisms and offer distinct advantages.

`JOIN FETCH`:
- Declared directly inside a custom JPQL query string (`SELECT o FROM Order o JOIN FETCH o.items`).
- Always acts as a hard fetch plan overriding all mapping configurations.
- Requires writing custom JPQL strings for each repository method.
- Cannot easily be applied to derived query methods (e.g., `findByStatus`).

`@EntityGraph`:
- Uses the standard JPA 2.1 Entity Graph API.
- Works directly on derived query methods without requiring manual JPQL:
```java
@Repository
public interface OrderRepository extends JpaRepository<Order, Long> {

    @EntityGraph(attributePaths = {"customer", "items"})
    List<Order> findByStatus(OrderStatus status);

    @EntityGraph(attributePaths = {"customer.address", "items.product"}, type = EntityGraph.EntityGraphType.FETCH)
    Optional<Order> findWithDetailsById(Long id);
}
```
- Supports two modes via `EntityGraphType`:
  - `FETCH`: Attributes specified in `attributePaths` are treated as `EAGER`; all other attributes are treated as `LAZY`.
  - `LOAD`: Attributes specified are `EAGER`; unspecified attributes retain their entity mapping defaults.

---

### Question 7: What is the difference between CrudRepository, JpaRepository, and PagingAndSortingRepository?

**Answer:**
In Spring Data, repositories form an inheritance hierarchy where each sub-interface adds specialized data access capabilities.

1. `CrudRepository<T, ID>`:
- The base interface offering generic CRUD operations: `save(S)`, `findById(ID)`, `existsById(ID)`, `findAll()`, `count()`, `deleteById(ID)`, `deleteAll()`.
- Designed for technology-agnostic data access (works across JPA, MongoDB, Cassandra).

2. `PagingAndSortingRepository<T, ID>`:
- Extends `Repository` (in modern Spring Data 3.x) to provide methods for sorting and pagination:
  - `Iterable<T> findAll(Sort sort)`
  - `Page<T> findAll(Pageable pageable)`

3. `JpaRepository<T, ID>`:
- Extends both `CrudRepository` and `PagingAndSortingRepository`.
- Adds JPA-specific persistence features:
  - Persistence context flushing: `flush()`, `saveAndFlush(entity)`.
  - Batch deletion: `deleteAllInBatch()`, `deleteAllByIdInBatch(Iterable<ID>)`.
  - Reference retrieval: `getReferenceById(ID)` (returns a lazy proxy without database read).
  - Returns `List<T>` instead of generic `Iterable<T>` for query results.

```java
// Standard production repository interface:
@Repository
public interface CustomerRepository extends JpaRepository<Customer, Long> {
    // Inherits pagination, batch flushing, and CRUD operations
}
```

---

### Question 8: How do JPA Specifications work and what problem do they solve?

**Answer:**
JPA Specifications solve the problem of building dynamic, combinable SQL queries at runtime without writing cumbersome string concatenations or bloated permutations of derived query methods (e.g., `findByStatusAndCustomerIdAndDateBetween...`).

Specifications are based on the JPA Criteria API and the Domain-Driven Design Specification pattern. An application implements `Specification<T>`:

```java
public class ProductSpecifications {

    public static Specification<Product> isAvailable() {
        return (root, query, cb) -> cb.equal(root.get("available"), true);
    }

    public static Specification<Product> hasCategory(String category) {
        return (root, query, cb) -> 
            category == null ? cb.conjunction() : cb.equal(root.get("category"), category);
    }

    public static Specification<Product> priceBetween(BigDecimal min, BigDecimal max) {
        return (root, query, cb) -> {
            if (min == null && max == null) return cb.conjunction();
            if (min != null && max != null) return cb.between(root.get("price"), min, max);
            return min != null ? cb.ge(root.get("price"), min) : cb.le(root.get("price"), max);
        };
    }
}
```

The repository extends `JpaSpecificationExecutor<Product>`:
```java
@Repository
public interface ProductRepository extends JpaRepository<Product, Long>, JpaSpecificationExecutor<Product> {}
```

Specifications can be fluently chained with `and()`, `or()`, and `not()`:
```java
Specification<Product> spec = Specification.where(ProductSpecifications.isAvailable())
    .and(ProductSpecifications.hasCategory("ELECTRONICS"))
    .and(ProductSpecifications.priceBetween(minPrice, maxPrice));

Page<Product> products = productRepository.findAll(spec, pageable);
```

---

### Question 9: Explain the cascade types in JPA — what does CascadeType.ALL do?

**Answer:**
Cascade types define how state transitions applied to a parent entity propagate to its associated child entities. When an operation is performed on the parent via `EntityManager`, JPA checks cascade configuration to determine whether to apply the same operation to child entities.

JPA Cascade Types:
- `CascadeType.PERSIST`: Calling `persist()` on parent automatically persists associated children.
- `CascadeType.MERGE`: Calling `merge()` on parent synchronizes detached state of children into the persistence context.
- `CascadeType.REMOVE`: Deleting parent issues `DELETE` statements for all associated children.
- `CascadeType.REFRESH`: Refreshing parent reloads child records from the database.
- `CascadeType.DETACH`: Detaching parent detaches all associated children from the first-level cache.

`CascadeType.ALL`:
`CascadeType.ALL` is a shorthand bundling all five cascade operations (`PERSIST`, `MERGE`, `REMOVE`, `REFRESH`, `DETACH`).

```java
@Entity
public class Order {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<OrderItem> items = new ArrayList<>();

    public void addItem(OrderItem item) {
        items.add(item);
        item.setOrder(this);
    }
}
```
With `CascadeType.ALL`, saving an `Order` automatically persists new `OrderItem` entries; deleting the `Order` automatically deletes all its items. It should only be used on parent-child aggregate roots where the child cannot exist independently.

---

### Question 10: What is the self-invocation problem with @Transactional?

**Answer:**
The self-invocation problem occurs when a method inside a Spring bean directly calls another method inside the same bean, expecting Spring's `@Transactional` annotation on the called method to create or alter transaction boundaries.

Spring manages declarative transactions using Dynamic Proxies or CGLIB proxies. When external clients invoke bean methods, the call passes through the proxy interceptor:
`Caller -> Proxy -> Target Bean Method`

However, when a method calls another method within the same class (`this.method()`), the execution bypasses the proxy entirely, executing directly on the target object without invoking transactional interceptors:

```java
@Service
public class PaymentProcessingService {

    public void processBatch() {
        // Direct internal call bypasses Spring proxy!
        // REQUIRES_NEW is completely ignored and runs without a transaction!
        executePayment(); 
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void executePayment() {
        // Intended to run in isolated transaction, but proxy was skipped
    }
}
```

Solutions:
1. Extract the transactional method into a separate dedicated Spring bean (`PaymentExecutorService`).
2. Use programmatic `TransactionTemplate` instead of annotations:
```java
@Autowired
private TransactionTemplate transactionTemplate;

public void processBatch() {
    transactionTemplate.execute(status -> {
        executePayment();
        return null;
    });
}
```
3. Self-inject the bean using `@Lazy`:
```java
@Autowired
@Lazy
private PaymentProcessingService self;
// Call self.executePayment();
```

---

### Question 11: How do you implement auditing (created/modified dates and users) in Spring Data JPA?

**Answer:**
Spring Data JPA provides automated entity auditing via `@EntityListeners(AuditingEntityListener.class)` combined with four auditing annotations: `@CreatedDate`, `@CreatedBy`, `@LastModifiedDate`, and `@LastModifiedBy`.

Step 1: Enable JPA auditing and provide an `AuditorAware` bean:
```java
@Configuration
@EnableJpaAuditing(auditorAwareRef = "auditorAware")
public class AuditConfig {

    @Bean
    public AuditorAware<String> auditorAware() {
        return () -> {
            Authentication auth = SecurityContextHolder.getContext().getAuthentication();
            if (auth == null || !auth.isAuthenticated()) {
                return Optional.of("SYSTEM");
            }
            return Optional.of(auth.getName());
        };
    }
}
```

Step 2: Create a reusable `@MappedSuperclass`:
```java
@MappedSuperclass
@EntityListeners(AuditingEntityListener.class)
public abstract class AbstractAuditEntity {

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    @CreatedBy
    @Column(name = "created_by", nullable = false, updatable = false)
    private String createdBy;

    @LastModifiedDate
    @Column(name = "last_modified_at", nullable = false)
    private Instant lastModifiedAt;

    @LastModifiedBy
    @Column(name = "last_modified_by", nullable = false)
    private String lastModifiedBy;

    // Getters
}
```

Any entity extending `AbstractAuditEntity` automatically populates audit columns upon `persist()` and `update()` without manual intervention.

---

### Question 12: What is the difference between JPQL and native SQL queries in Spring Data?

**Answer:**
JPQL (Java Persistence Query Language) and native SQL queries allow querying relational databases in Spring Data JPA, but they differ fundamentally in portability, abstraction, and execution mechanics.

JPQL:
- Operates on Java entity models and fields rather than database tables and columns (`SELECT o FROM Order o WHERE o.totalAmount > :amount`).
- Portable across different relational database engines (PostgreSQL, MySQL, Oracle) because Hibernate translates JPQL into target dialect SQL.
- Supports automatic query validation at startup.
- Supports polymorphic queries and entity navigation (`o.customer.email`).

```java
@Query("SELECT o FROM Order o WHERE o.status = :status AND o.totalAmount >= :minAmount")
List<Order> findHighValueOrders(@Param("status") OrderStatus status, @Param("minAmount") BigDecimal minAmount);
```

Native SQL:
- Operates directly on physical database tables and column names with `nativeQuery = true`.
- Allows using database-specific syntax (PostgreSQL `JSONB` operators, window functions `ROW_NUMBER()`, CTEs).
- Bypasses JPQL validation and portability; switching database engines may break syntax.

```java
@Query(
    value = "SELECT * FROM orders WHERE json_extract(metadata, '$.channel') = 'MOBILE' ORDER BY created_at DESC LIMIT 50",
    nativeQuery = true
)
List<Order> findMobileOrders();
```

---

### Question 13: How does HikariCP connection pool work and what are key tuning parameters?

**Answer:**
HikariCP is the default high-performance JDBC connection pool in Spring Boot. It uses Java byte-code optimization, specialized lock-free collections (`FastList`, `ConcurrentBag`), and micro-optimizations to deliver near-zero connection overhead.

Key tuning parameters in `application.yml`:
```yaml
spring:
  datasource:
    hikari:
      maximum-pool-size: 20
      minimum-idle: 10
      connection-timeout: 20000
      idle-timeout: 300000
      max-lifetime: 1200000
      leak-detection-threshold: 5000
```

Parameter breakdown:
1. `maximum-pool-size`: Maximum physical connections HikariCP creates. Rule of thumb: `pool_size = (core_count * 2) + effective_spindle_count`. Too many connections degrade database performance due to disk I/O and CPU context switching.
2. `minimum-idle`: Minimum number of idle connections maintained. Setting `minimum-idle = maximum-pool-size` establishes a fixed-size pool, preventing latency spikes from runtime connection allocations.
3. `connection-timeout`: Maximum milliseconds a thread waits to borrow a connection before throwing `SQLTransientConnectionException` (e.g., 20,000ms).
4. `idle-timeout`: Time an idle connection is permitted to remain in pool before retirement.
5. `max-lifetime`: Maximum total lifespan of a connection in the pool before being retired and recreated. Must be set 2–3 minutes shorter than database or cloud firewall connection kill limits.
6. `leak-detection-threshold`: Logs a warning if a thread holds a borrowed connection longer than the threshold, diagnosing connection leaks.

---

### Question 14: What are the differences between Page<T> and Slice<T>?

**Answer:**
Both `Page<T>` and `Slice<T>` are pagination container interfaces in Spring Data, but they differ significantly in database query overhead and functional capabilities.

`Page<T>`:
- Executes two database queries:
  1. Data query: `SELECT * FROM orders ORDER BY id DESC LIMIT 20 OFFSET 40;`
  2. Count query: `SELECT COUNT(*) FROM orders;`
- Exposes total element count (`getTotalElements()`) and total pages (`getTotalPages()`).
- Ideal for traditional UI pagination bars where page numbers (1, 2, 3... 50) must be shown.
- Performance Drawback: `COUNT(*)` queries on large tables (millions of rows) require full index or table scans, causing severe query degradation.

```java
Pageable pageable = PageRequest.of(0, 20, Sort.by("id").descending());
Page<Order> page = orderRepository.findAll(pageable);
long total = page.getTotalElements();
int totalPages = page.getTotalPages();
```

`Slice<T>`:
- Executes only the data query, requesting `limit + 1` rows:
  `SELECT * FROM orders ORDER BY id DESC LIMIT 21 OFFSET 40;`
- Determines whether a next slice exists by checking if the returned result size equals `limit + 1`.
- Does not know total elements or total pages (`hasNext()` returns boolean).
- Ideal for infinite scroll, mobile feeds, and high-throughput batch consumers without `COUNT(*)` overhead.

```java
Slice<Order> slice = orderRepository.findSliceByCustomerId(customerId, pageable);
boolean hasMore = slice.hasNext();
```

---

### Question 15: How do you implement soft deletes in Spring Data JPA?

**Answer:**
Soft deletion retains deleted records in the database table with a boolean flag (`deleted = true`) rather than physically executing a SQL `DELETE` statement.

Implementation in Hibernate uses `@SQLDelete` and `@SQLRestriction` (in Hibernate 6.x / Spring Boot 3.x) or `@Where` (in Hibernate 5.x):

```java
package com.example.domain;

import jakarta.persistence.*;
import org.hibernate.annotations.SQLDelete;
import org.hibernate.annotations.SQLRestriction;

@Entity
@Table(name = "customers")
@SQLDelete(sql = "UPDATE customers SET deleted = true WHERE id = ?")
@SQLRestriction("deleted = false")
public class Customer {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;

    @Column(nullable = false)
    private boolean deleted = false;

    // Getters and setters
    public Long getId() { return id; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public boolean isDeleted() { return deleted; }
    public void setDeleted(boolean deleted) { this.deleted = deleted; }
}
```

Behavior:
1. When calling `customerRepository.deleteById(1L)`, Hibernate intercepts the command and executes `UPDATE customers SET deleted = true WHERE id = 1;`.
2. When executing queries (`findAll()`, `findById()`, or derived queries), Hibernate automatically appends `AND deleted = false` to the `WHERE` clause.
3. Records remain in the database for auditing and foreign key integrity while remaining invisible to standard business logic.
