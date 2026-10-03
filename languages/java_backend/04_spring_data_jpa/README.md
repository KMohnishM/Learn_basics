# Spring Data JPA Deep Dive

Spring Data JPA provides a robust abstraction layer over Jakarta Persistence API (JPA) and object-relational mapping (ORM) providers such as Hibernate. It significantly reduces boilerplate persistence code while preserving fine-grained control over transactions, queries, and database performance.

---

## 1. JPA Overview

### The Persistence Stack: JPA vs Hibernate vs Spring Data JPA
Understanding the separation of concerns across the persistence stack is essential:
- JPA (Jakarta Persistence API): The formal specification defining Java interfaces, object-relational mapping metadata annotations (`@Entity`, `@Table`, `@Column`), transaction semantics, and query grammar (JPQL). JPA itself contains no executable database logic.
- Hibernate: The concrete ORM provider implementing the JPA specification. Hibernate translates JPA annotations and JPQL into database-specific SQL dialects, manages the persistence context, performs automatic dirty checking, and optimizes SQL statement batching.
- Spring Data JPA: An abstraction library built on top of JPA and Hibernate. It eliminates boilerplate Data Access Object (DAO) code by automatically generating repository implementations at runtime through dynamic proxies, query derivation, and declarative paging.

```
+-------------------------------------------------------------+
|                      Spring Data JPA                        |
|  (JpaRepository, Query Derivation, Specifications, Paging)  |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|              Jakarta Persistence API (JPA)                  |
|    (EntityManager, EntityTransaction, JPQL Specifications)  |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                   Hibernate ORM Provider                    |
| (Session, SessionFactory, Dialects, Dirty Checking, Cache)  |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                   JDBC Driver & DataSource                  |
|               (HikariCP, PostgreSQL / MySQL)                |
+-------------------------------------------------------------+
```

### Core Architecture Components
1. `EntityManagerFactory`: A heavyweight, thread-safe factory responsible for parsing persistence metadata and creating `EntityManager` instances. In Spring Boot, this is managed by the `LocalContainerEntityManagerFactoryBean`.
2. `EntityManager`: The primary interface used to interact with the persistence context. It is not thread-safe and is bound to a single transaction or request thread.
3. `PersistenceContext`: An in-memory first-level cache (L1 cache) that tracks entity instances during an active transaction. Every managed entity inside a persistence context has a unique identity (`@Id`).

### Entity Lifecycle States
Entities transition through four distinct lifecycle states:
- Transient: The entity has been instantiated with `new Order()`, but has not been associated with a persistence context and has no primary key assigned in the database.
- Managed (Persistent): The entity is associated with an active `PersistenceContext` (via `persist()`, `find()`, or query). Hibernate tracks all field mutations and synchronizes modifications to the database upon transaction commit (dirty checking).
- Detached: The entity has a primary key, but its associated `PersistenceContext` has been closed or flushed and cleared. Modifications will not be tracked unless re-attached via `merge()`.
- Removed: The entity has been scheduled for deletion via `remove()`. Upon flush or transaction commit, a SQL `DELETE` is executed.

---

## 2. Entity Mapping

### Primary Key Generation Strategies
JPA provides four primary key generation strategies via `@GeneratedValue`:
- `GenerationType.IDENTITY`: Relies on an auto-increment or identity column in the database (e.g., MySQL `AUTO_INCREMENT`, PostgreSQL `BIGSERIAL`). Requires an immediate `INSERT` statement execution on `persist()` to retrieve the generated ID, disabling JDBC batch inserts.
- `GenerationType.SEQUENCE`: Uses a dedicated database sequence (PostgreSQL, Oracle). Pre-fetches block allocations of IDs using an allocation size (optimizer pooling), allowing full JDBC statement batching.
- `GenerationType.TABLE`: Allocates IDs using an underlying lock table. Incurs heavy database locking overhead and is rarely used in modern systems.
- `GenerationType.AUTO`: Allows the ORM provider to choose the strategy based on the database dialect.

```java
package com.example.domain;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;

@Entity
@Table(
    name = "orders",
    indexes = {
        @Index(name = "idx_orders_customer_id", columnList = "customer_id"),
        @Index(name = "idx_orders_created_at", columnList = "created_at")
    },
    uniqueConstraints = {
        @UniqueConstraint(name = "uk_orders_order_number", columnNames = "order_number")
    }
)
public class Order {

    @Id
    @GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "order_seq_gen")
    @SequenceGenerator(
        name = "order_seq_gen",
        sequenceName = "order_sequence",
        allocationSize = 50
    )
    private Long id;

    @Column(name = "order_number", nullable = false, length = 64, updatable = false)
    private String orderNumber;

    @Column(name = "customer_id", nullable = false)
    private Long customerId;

    @Column(name = "total_amount", nullable = false, precision = 12, scale = 2)
    private BigDecimal totalAmount;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 32)
    private OrderStatus status;

    @Lob
    @Column(name = "customer_notes")
    private String customerNotes;

    @Transient
    private boolean expeditedProcessing;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    protected Order() {}

    public Order(String orderNumber, Long customerId, BigDecimal totalAmount, OrderStatus status) {
        this.orderNumber = orderNumber;
        this.customerId = customerId;
        this.totalAmount = totalAmount;
        this.status = status;
        this.createdAt = Instant.now();
    }

    public Long getId() { return id; }
    public String getOrderNumber() { return orderNumber; }
    public Long getCustomerId() { return customerId; }
    public BigDecimal getTotalAmount() { return totalAmount; }
    public OrderStatus getStatus() { return status; }
    public void setStatus(OrderStatus status) { this.status = status; }
}
```

### Composite Keys: `@EmbeddedId` vs `@IdClass`
When an entity uses multiple columns as its primary key, JPA supports `@EmbeddedId` or `@IdClass`. `@EmbeddedId` is strongly preferred for type safety.

```java
package com.example.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Embeddable;
import java.io.Serializable;
import java.util.Objects;

@Embeddable
public class OrderItemId implements Serializable {

    @Column(name = "order_id")
    private Long orderId;

    @Column(name = "item_sequence")
    private Integer itemSequence;

    public OrderItemId() {}

    public OrderItemId(Long orderId, Integer itemSequence) {
        this.orderId = orderId;
        this.itemSequence = itemSequence;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        OrderItemId that = (OrderItemId) o;
        return Objects.equals(orderId, that.orderId) &&
               Objects.equals(itemSequence, that.itemSequence);
    }

    @Override
    public int hashCode() {
        return Objects.hash(orderId, itemSequence);
    }
}
```

Using the embedded ID in the entity:
```java
@Entity
@Table(name = "order_items")
public class OrderItem {

    @EmbeddedId
    private OrderItemId id;

    @Column(name = "product_sku", nullable = false)
    private String productSku;

    @Column(name = "quantity", nullable = false)
    private int quantity;

    @Column(name = "unit_price", nullable = false, precision = 10, scale = 2)
    private BigDecimal unitPrice;

    // Constructors, getters, setters
}
```

---

## 3. Relationships

### Relationship Types and Directionality
- `@OneToOne`: One entity instance corresponds to exactly one other instance.
- `@ManyToOne`: Many child instances reference a single parent instance.
- `@OneToMany`: One parent instance references a collection of child instances.
- `@ManyToMany`: Many instances of one entity associate with many instances of another.

### Owning Side and Bidirectional Consistency
In JPA, the owning side of a relationship owns the foreign key column in the database table. The non-owning side declares the `mappedBy` attribute, pointing to the field on the owning entity.

Failure to synchronize both sides of a bidirectional relationship in memory leads to state inconsistencies before persistence context flushes.

```java
package com.example.domain;

import jakarta.persistence.*;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "customers")
public class Customer {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "email", nullable = false, unique = true)
    private String email;

    @OneToMany(
        mappedBy = "customer",
        cascade = CascadeType.ALL,
        orphanRemoval = true,
        fetch = FetchType.LAZY
    )
    private List<CustomerAddress> addresses = new ArrayList<>();

    // Synchronization helper methods maintain bidirectional integrity
    public void addAddress(CustomerAddress address) {
        addresses.add(address);
        address.setCustomer(this);
    }

    public void removeAddress(CustomerAddress address) {
        addresses.remove(address);
        address.setCustomer(null);
    }

    public List<CustomerAddress> getAddresses() { return addresses; }
}
```

Child entity owning the foreign key:
```java
package com.example.domain;

import jakarta.persistence.*;

@Entity
@Table(name = "customer_addresses")
public class CustomerAddress {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "street", nullable = false)
    private String street;

    @Column(name = "city", nullable = false)
    private String city;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "customer_id", nullable = false)
    private Customer customer;

    public void setCustomer(Customer customer) {
        this.customer = customer;
    }

    public Customer getCustomer() {
        return customer;
    }
}
```

### Cascade Types and `orphanRemoval`
- `CascadeType.PERSIST`: Cascades `persist()` operations to child entities.
- `CascadeType.MERGE`: Cascades `merge()` operations to child entities.
- `CascadeType.REMOVE`: When the parent is deleted via `entityManager.remove()`, related children are deleted.
- `CascadeType.ALL`: Propagates all entity manager operations (`PERSIST`, `MERGE`, `REMOVE`, `REFRESH`, `DETACH`).
- `orphanRemoval = true`: If a child entity is dereferenced from the parent's collection (`addresses.remove(address)`), JPA automatically issues a SQL `DELETE` for that orphan record upon flush.

---

## 4. Fetch Strategies

### `FetchType.LAZY` vs `FetchType.EAGER`
- `FetchType.EAGER`: Directs Hibernate to fetch the associated entity or collection immediately alongside the parent entity, typically using SQL `LEFT OUTER JOIN` or secondary queries.
- `FetchType.LAZY`: Defers loading the association until the field or collection getter is explicitly invoked in code. Behind the scenes, Hibernate injects a runtime proxy or collection wrapper.

### Default Fetch Types in JPA
| Mapping | JPA Default Fetch Type | Recommended Best Practice |
| :--- | :--- | :--- |
| `@OneToMany` | `FetchType.LAZY` | `FetchType.LAZY` |
| `@ManyToMany` | `FetchType.LAZY` | `FetchType.LAZY` |
| `@ManyToOne` | `FetchType.EAGER` | Always change to `FetchType.LAZY` |
| `@OneToOne` | `FetchType.EAGER` | Always change to `FetchType.LAZY` |

`@ManyToOne` and `@OneToOne` default to `EAGER`. In enterprise codebases, this frequently triggers cascading multi-table joins and unintentional full-database scans. Always explicitly declare `fetch = FetchType.LAZY`.

### `LazyInitializationException`
Occurs when an uninitialized lazy proxy or collection is accessed after the persistence context (and database transaction) has already closed:

```java
// Controller accessing lazy collection with open-in-view=false:
Order order = orderService.getOrderById(orderId); // Transaction commits and closes here
order.getItems().size(); // Throws org.hibernate.LazyInitializationException: could not initialize proxy - no Session
```

Resolution strategies:
1. Fetch association eagerly in the specific query using `JOIN FETCH`.
2. Use `@EntityGraph` in repository methods.
3. Return tailored DTO projections rather than managed domain entities.

---

## 5. N+1 Problem

### Anatomy of the N+1 Problem
The N+1 problem occurs when an application executes 1 initial query to retrieve N records, and subsequently executes N separate queries to fetch related child records for each individual parent:

```java
List<Order> orders = orderRepository.findAll(); 
// Query 1: SELECT * FROM orders; (returns 100 rows)

for (Order order : orders) {
    System.out.println(order.getCustomer().getEmail());
    // Queries 2 through 101: SELECT * FROM customers WHERE id = ?;
}
// Total: 1 initial query + 100 secondary queries = 101 database roundtrips
```

### Detection Techniques
1. Enable Hibernate SQL Logging:
   ```yaml
   spring:
     jpa:
       show-sql: false
       properties:
         hibernate:
           format_sql: true
           generate_statistics: true
   logging:
     level:
       org.hibernate.stat: DEBUG
   ```
2. Hypersistence Optimizer: Automatically scans entity mappings and flags N+1 query patterns during automated build runs.

### Solutions for the N+1 Problem

#### Solution A: `JOIN FETCH` in JPQL
Forces an inner or left outer join directly in the JPQL statement, populating both parent and child entities in a single roundtrip:
```java
@Query("SELECT o FROM Order o JOIN FETCH o.customer JOIN FETCH o.items WHERE o.status = :status")
List<Order> findAllWithCustomerAndItems(@Param("status") OrderStatus status);
```

#### Solution B: `@EntityGraph`
Declaratively instructs JPA to construct joins for specified paths without writing custom JPQL:
```java
@EntityGraph(attributePaths = {"customer", "items"})
List<Order> findByStatus(OrderStatus status);
```

#### Solution C: Hibernate `@BatchSize`
Fetches collections in batches using a SQL `WHERE id IN (?, ?, ?, ...)` clause:
```java
@Entity
public class Order {
    @OneToMany(mappedBy = "order", fetch = FetchType.LAZY)
    @org.hibernate.annotations.BatchSize(size = 25)
    private List<OrderItem> items = new ArrayList<>();
}
```

#### Solution D: DTO Projections
Bypasses entity proxy overhead entirely by selecting only required projection fields directly into flat records.

---

## 6. Spring Data JPA Repositories

### Repository Hierarchy
```
Repository<T, ID>
       ^
       |
CrudRepository<T, ID>
       ^
       |
PagingAndSortingRepository<T, ID>
       ^
       |
JpaRepository<T, ID>
```
- `Repository`: Marker interface capturing domain type and ID type.
- `CrudRepository`: Provides generic CRUD operations (`save`, `findById`, `existsById`, `delete`).
- `PagingAndSortingRepository`: Adds methods for pagination (`findAll(Pageable)`) and sorting (`findAll(Sort)`).
- `JpaRepository`: Adds JPA-specific batch execution methods (`flush`, `saveAndFlush`, `deleteAllInBatch`).

### Derived Query Methods
Spring Data translates method names into JPQL queries based on defined naming patterns:

```java
package com.example.repository;

import com.example.domain.Order;
import com.example.domain.OrderStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import java.util.Optional;

@Repository
public interface OrderRepository extends JpaRepository<Order, Long> {

    List<Order> findByCustomerIdAndStatus(Long customerId, OrderStatus status);

    List<Order> findByTotalAmountGreaterThanOrderByCreatedAtDesc(BigDecimal amount);

    boolean existsByOrderNumber(String orderNumber);

    long countByStatus(OrderStatus status);

    // JPQL Query
    @Query("SELECT o FROM Order o WHERE o.createdAt >= :startDate AND o.status = :status")
    List<Order> findRecentOrdersByStatus(
        @Param("startDate") Instant startDate,
        @Param("status") OrderStatus status
    );

    // Native SQL Query
    @Query(
        value = "SELECT * FROM orders WHERE total_amount > :minAmount AND json_extract(customer_notes, '$.vip') = 'true'",
        nativeQuery = true
    )
    List<Order> findVipHighValueOrders(@Param("minAmount") BigDecimal minAmount);

    // Bulk Modifying Query
    @Modifying(clearAutomatically = true, flushAutomatically = true)
    @Query("UPDATE Order o SET o.status = :newStatus WHERE o.status = :oldStatus AND o.createdAt < :cutoffDate")
    int cancelStaleOrders(
        @Param("newStatus") OrderStatus newStatus,
        @Param("oldStatus") OrderStatus oldStatus,
        @Param("cutoffDate") Instant cutoffDate
    );
}
```

The `@Modifying` annotation notifies Spring Data that the query executes an `UPDATE` or `DELETE` statement. The flags `clearAutomatically = true` and `flushAutomatically = true` ensure Hibernate synchronizes dirty state to the database before the update and flushes the first-level cache afterward to prevent stale entity state in memory.

---

## 7. Projections

When an application only requires a subset of columns, fetching complete managed entities incurs unnecessary memory and serialization overhead.

### Closed Interface Projections
Interface projections define getter methods corresponding to entity attributes. Spring Data generates a dynamic proxy holding only the selected attributes:

```java
package com.example.projection;

import java.math.BigDecimal;

public interface OrderSummaryProjection {
    Long getId();
    String getOrderNumber();
    BigDecimal getTotalAmount();
}
```

Repository method:
```java
List<OrderSummaryProjection> findByCustomerId(Long customerId);
```

### Open Interface Projections with SpEL
Open projections use `@Value` with Spring Expression Language (SpEL) to compute dynamic attributes:

```java
package com.example.projection;

import org.springframework.beans.factory.annotation.Value;

public interface CustomerFullNameProjection {
    @Value("#{target.firstName + ' ' + target.lastName}")
    String getFullName();
    String getEmail();
}
```

### Class-Based Projections (DTO Records)
Constructor-based DTO projections offer optimal performance because Hibernate maps query results directly into instantiated immutable Java Records without proxy generation:

```java
package com.example.dto;

import java.math.BigDecimal;

public record OrderItemDetailDto(
    Long orderId,
    String orderNumber,
    String productSku,
    int quantity,
    BigDecimal unitPrice
) {}
```

Repository method using JPQL constructor expression:
```java
@Query("""
    SELECT new com.example.dto.OrderItemDetailDto(
        o.id, o.orderNumber, i.productSku, i.quantity, i.unitPrice
    )
    FROM Order o JOIN o.items i
    WHERE o.customerId = :customerId
""")
List<OrderItemDetailDto> findItemDetailsByCustomerId(@Param("customerId") Long customerId);
```

### Dynamic Projections
Allow caller methods to specify the projection return type dynamically:
```java
<T> List<T> findByCustomerId(Long customerId, Class<T> projectionType);
```

---

## 8. Pagination and Sorting

### `Pageable`, `Page<T>`, and `Slice<T>`
Spring Data provides pagination abstractions through the `Pageable` interface and `PageRequest` factory:

- `Page<T>`: Represents a paginated page of results and triggers two database queries: one query fetching the page slice (`LIMIT ? OFFSET ?`), and an additional query executing `SELECT COUNT(*)` to calculate total elements and total pages.
- `Slice<T>`: Fetches `limit + 1` records to determine whether a subsequent page exists without executing a `COUNT(*)` query. Ideal for infinite scrolling on large tables where `COUNT(*)` creates substantial database load.

```java
package com.example.service;

import com.example.domain.Order;
import com.example.domain.OrderStatus;
import com.example.repository.OrderRepository;
import org.springframework.data.domain.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true)
public class OrderQueryService {

    private final OrderRepository orderRepository;

    public OrderQueryService(OrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }

    public Page<Order> getOrdersPaged(int pageNumber, int pageSize) {
        Sort sort = Sort.by(Sort.Direction.DESC, "createdAt")
            .and(Sort.by(Sort.Direction.ASC, "id"));

        Pageable pageable = PageRequest.of(pageNumber, pageSize, sort);
        return orderRepository.findAll(pageable);
    }

    public Slice<Order> getOrdersSliced(Long customerId, int pageNumber, int pageSize) {
        Pageable pageable = PageRequest.of(pageNumber, pageSize, Sort.by("id").descending());
        return orderRepository.findSliceByCustomerId(customerId, pageable);
    }
}
```

Custom query with manual count query declaration:
```java
@Query(
    value = "SELECT o FROM Order o WHERE o.status = :status",
    countQuery = "SELECT count(o.id) FROM Order o WHERE o.status = :status"
)
Page<Order> findByStatusWithCount(@Param("status") OrderStatus status, Pageable pageable);
```

---

## 9. Specifications and Dynamic Filtering

### `JpaSpecificationExecutor` and Criteria API
Building dynamic queries based on combinations of optional HTTP search filters (e.g., date range, status, min price, search text) is accomplished cleanly using Spring Data Specifications.

Repository definition:
```java
@Repository
public interface OrderRepository extends JpaRepository<Order, Long>, JpaSpecificationExecutor<Order> {
}
```

Specification factory:
```java
package com.example.specification;

import com.example.domain.Order;
import com.example.domain.OrderStatus;
import org.springframework.data.jpa.domain.Specification;

import java.math.BigDecimal;
import java.time.Instant;

public final class OrderSpecifications {

    private OrderSpecifications() {}

    public static Specification<Order> hasStatus(OrderStatus status) {
        return (root, query, cb) -> 
            status == null ? cb.conjunction() : cb.equal(root.get("status"), status);
    }

    public static Specification<Order> customerIdEquals(Long customerId) {
        return (root, query, cb) -> 
            customerId == null ? cb.conjunction() : cb.equal(root.get("customerId"), customerId);
    }

    public static Specification<Order> totalAmountBetween(BigDecimal min, BigDecimal max) {
        return (root, query, cb) -> {
            if (min == null && max == null) return cb.conjunction();
            if (min != null && max != null) return cb.between(root.get("totalAmount"), min, max);
            if (min != null) return cb.greaterThanOrEqualTo(root.get("totalAmount"), min);
            return cb.lessThanOrEqualTo(root.get("totalAmount"), max);
        };
    }

    public static Specification<Order> createdAfter(Instant date) {
        return (root, query, cb) -> 
            date == null ? cb.conjunction() : cb.greaterThanOrEqualTo(root.get("createdAt"), date);
    }
}
```

Combining specifications dynamically in the service layer:
```java
public Page<Order> searchOrders(Long customerId, OrderStatus status, BigDecimal minAmount, 
                                BigDecimal maxAmount, Instant fromDate, Pageable pageable) {
    Specification<Order> spec = Specification.where(OrderSpecifications.customerIdEquals(customerId))
        .and(OrderSpecifications.hasStatus(status))
        .and(OrderSpecifications.totalAmountBetween(minAmount, maxAmount))
        .and(OrderSpecifications.createdAfter(fromDate));

    return orderRepository.findAll(spec, pageable);
}
```

---

## 10. `@Transactional` Deep Dive

### Transaction Propagation Behaviors
| Propagation | Description |
| :--- | :--- |
| `REQUIRED` (Default) | Joins existing transaction if one exists; creates a new transaction if none exists. |
| `REQUIRES_NEW` | Suspends active transaction and starts a completely independent, autonomous transaction. |
| `SUPPORTS` | Runs within existing transaction if present; executes non-transactionally if none exists. |
| `NOT_SUPPORTED` | Suspends current transaction and executes code completely non-transactionally. |
| `MANDATORY` | Requires an existing active transaction; throws `TransactionRequiredException` if none exists. |
| `NEVER` | Throws `IllegalTransactionStateException` if an active transaction is detected. |
| `NESTED` | Executes within a nested transaction using database savepoints (if supported by JDBC driver). |

### Isolation Levels
| Isolation Level | Dirty Read | Non-Repeatable Read | Phantom Read |
| :--- | :--- | :--- | :--- |
| `READ_UNCOMMITTED` | Yes | Yes | Yes |
| `READ_COMMITTED` | No | Yes | Yes |
| `REPEATABLE_READ` | No | No | Yes |
| `SERIALIZABLE` | No | No | No |

### Rollback Rules
By default, Spring `@Transactional` rolls back only on unchecked exceptions (`RuntimeException` and `Error`). It does not roll back on checked exceptions (`Exception`). Override this using `rollbackFor`:

```java
@Transactional(rollbackFor = Exception.class, noRollbackFor = AuditLoggingException.class)
public void processOrder(Long orderId) throws InsufficientInventoryException {
    // Transaction rolls back if InsufficientInventoryException is thrown
}
```

### The Self-Invocation Problem
Spring's declarative transactions rely on Spring AOP proxies. When a method inside a bean calls another method within the same bean, the call executes via the `this` reference, bypassing the proxy and skipping `@Transactional` interceptors:

```java
@Service
public class OrderService {

    public void processAll() {
        // Direct method call bypasses the Spring AOP proxy; REQUIRES_NEW is ignored!
        createSubTransaction(); 
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void createSubTransaction() {
        // Runs inside processAll's transaction context rather than a new transaction
    }
}
```

Resolutions:
1. Extract the inner transactional method into a separate dedicated Spring bean.
2. Inject `TransactionTemplate` and manage programmatic boundaries.
3. Self-inject the bean using `@Lazy` or `ObjectProvider<OrderService>`.

---

## 11. Auditing

### Entity Auditing Architecture
Spring Data JPA provides automatic auditing to capture entity creation timestamps, last modified timestamps, creating user, and modifying user.

Configuration:
```java
package com.example.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.domain.AuditorAware;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;

import java.util.Optional;

@Configuration
@EnableJpaAuditing(auditorAwareRef = "auditorProvider")
public class JpaAuditingConfig {

    @Bean
    public AuditorAware<String> auditorProvider() {
        return () -> {
            Authentication auth = SecurityContextHolder.getContext().getAuthentication();
            if (auth == null || !auth.isAuthenticated() || "anonymousUser".equals(auth.getPrincipal())) {
                return Optional.of("system");
            }
            return Optional.of(auth.getName());
        };
    }
}
```

Base Auditable Mapped Superclass:
```java
package com.example.domain;

import jakarta.persistence.Column;
import jakarta.persistence.EntityListeners;
import jakarta.persistence.MappedSuperclass;
import org.springframework.data.annotation.CreatedBy;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedBy;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.Instant;

@MappedSuperclass
@EntityListeners(AuditingEntityListener.class)
public abstract class AuditableBaseEntity {

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    @CreatedBy
    @Column(name = "created_by", nullable = false, updatable = false)
    private String createdBy;

    @LastModifiedDate
    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    @LastModifiedBy
    @Column(name = "updated_by", nullable = false)
    private String updatedBy;

    public Instant getCreatedAt() { return createdAt; }
    public String getCreatedBy() { return createdBy; }
    public Instant getUpdatedAt() { return updatedAt; }
    public String getUpdatedBy() { return updatedBy; }
}
```

---

## 12. Optimistic vs Pessimistic Locking

### Optimistic Locking
Optimistic locking detects concurrent modifications without locking database rows. It uses a `@Version` attribute (integer or timestamp). When an update is issued, Hibernate checks that the version in the database matches the entity version:

```sql
UPDATE orders SET status = 'CONFIRMED', version = 2 WHERE id = 100 AND version = 1;
```
If 0 rows are updated (because another transaction committed first), Hibernate throws `OptimisticLockException`.

```java
@Entity
public class Order {
    @Id
    private Long id;

    @Version
    private Long version;

    // fields, getters, setters
}
```

### Pessimistic Locking
Pessimistic locking acquires direct database row locks (`SELECT ... FOR UPDATE`), blocking other transactions from reading or mutating locked rows until the locking transaction finishes:

```java
@Repository
public interface OrderRepository extends JpaRepository<Order, Long> {

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @QueryHints({@QueryHint(name = "jakarta.persistence.lock.timeout", value = "3000")})
    @Query("SELECT o FROM Order o WHERE o.id = :id")
    Optional<Order> findByIdForUpdate(@Param("id") Long id);
}
```

Use optimistic locking for high-read, low-contention scenarios. Use pessimistic locking for inventory deduction, banking balances, or critical checkout paths where concurrent contention is high.

---

## 13. QueryDSL

### Type-Safe Dynamic Querying
QueryDSL eliminates string-based JPQL queries by generating static metamodel classes (`QOrder`, `QCustomer`) via an annotation processor at compile time.

Maven setup:
```xml
<dependency>
    <groupId>com.querydsl</groupId>
    <artifactId>querydsl-jpa</artifactId>
    <classifier>jakarta</classifier>
    <version>5.1.0</version>
</dependency>
<dependency>
    <groupId>com.querydsl</groupId>
    <artifactId>querydsl-apt</artifactId>
    <classifier>jakarta</classifier>
    <version>5.1.0</version>
    <scope>provided</scope>
</dependency>
```

Repository integration:
```java
@Repository
public interface OrderRepository extends JpaRepository<Order, Long>, QuerydslPredicateExecutor<Order> {
}
```

Executing type-safe queries:
```java
package com.example.service;

import com.example.domain.Order;
import com.example.domain.OrderStatus;
import com.example.domain.QOrder;
import com.example.repository.OrderRepository;
import com.querydsl.core.types.dsl.BooleanExpression;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;

@Service
public class OrderSearchService {

    private final OrderRepository orderRepository;

    public OrderSearchService(OrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }

    public Iterable<Order> searchOrders(Long customerId, BigDecimal minAmount) {
        QOrder order = QOrder.order;

        BooleanExpression predicate = order.status.eq(OrderStatus.CONFIRMED);
        if (customerId != null) {
            predicate = predicate.and(order.customerId.eq(customerId));
        }
        if (minAmount != null) {
            predicate = predicate.and(order.totalAmount.goe(minAmount));
        }

        return orderRepository.findAll(predicate);
    }
}
```

---

## 14. Hibernate Envers

### Historical Entity Auditing
Hibernate Envers automatically records historical revisions and audit logs for entities annotated with `@Audited`.

Add dependency:
```xml
<dependency>
    <groupId>org.hibernate.orm</groupId>
    <artifactId>hibernate-envers</artifactId>
</dependency>
```

Entity mapping:
```java
package com.example.domain;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import org.hibernate.envers.Audited;

@Entity
@Table(name = "products")
@Audited
public class Product {

    @Id
    private Long id;

    private String name;

    private double price;

    // Getters and setters
}
```

Envers automatically creates an audit mirror table `products_AUD` and a revision tracking table `REVINFO`.

Querying past revisions:
```java
package com.example.service;

import com.example.domain.Product;
import jakarta.persistence.EntityManager;
import org.hibernate.envers.AuditReader;
import org.hibernate.envers.AuditReaderFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@Transactional(readOnly = true)
public class ProductAuditService {

    private final EntityManager entityManager;

    public ProductAuditService(EntityManager entityManager) {
        this.entityManager = entityManager;
    }

    public Product getHistoricalVersion(Long productId, Number revisionNumber) {
        AuditReader reader = AuditReaderFactory.get(entityManager);
        return reader.find(Product.class, productId, revisionNumber);
    }

    public List<Number> getRevisionNumbers(Long productId) {
        AuditReader reader = AuditReaderFactory.get(entityManager);
        return reader.getRevisions(Product.class, productId);
    }
}
```

---

## 15. Performance Tips and Best Practices

### 1. Read-Only Transactions
Marking query methods with `@Transactional(readOnly = true)` provides significant performance gains:
- Informs Hibernate to set flush mode to `FlushMode.MANUAL`, disabling dirty checking snapshots.
- JDBC drivers and connection pools can route queries directly to read replicas.

### 2. DTO Projections Over Entities
Avoid fetching managed entities when reading data for presentation or REST response serialization. DTO projections avoid Hibernate persistence context tracking and proxy instantiation.

### 3. JDBC Statement Batching
Batch multiple insert and update operations into single roundtrips to the database:
```yaml
spring:
  jpa:
    properties:
      hibernate:
        jdbc:
          batch_size: 50
        order_inserts: true
        order_updates: true
        batch_versioned_data: true
```
> Note: `GenerationType.IDENTITY` primary key generation disables JDBC batching because Hibernate must execute `INSERT` immediately to retrieve the generated ID. Always prefer `GenerationType.SEQUENCE` for high-throughput batch insert workflows.

### 4. Connection Pool (HikariCP) Tuning
Tuning pool size prevents connection starvation:
```yaml
spring:
  datasource:
    hikari:
      maximum-pool-size: 20
      minimum-idle: 10
      idle-timeout: 300000
      connection-timeout: 20000
      max-lifetime: 1200000
```
Pool sizing formula: `maximumPoolSize = (cpu_core_count * 2) + effective_spindle_count`.

### 5. Disable Open Session in View (OSIV)
Spring Boot enables `spring.jpa.open-in-view=true` by default, keeping database connections open throughout the entire web request lifecycle. Always disable this in production:
```yaml
spring:
  jpa:
    open-in-view: false
```
Disabling OSIV ensures database connections are released immediately upon completing repository transactions, preventing connection pool exhaustion under high web concurrency.
