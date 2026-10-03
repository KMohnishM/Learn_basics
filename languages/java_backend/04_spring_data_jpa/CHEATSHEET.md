# Spring Data JPA Quick Reference Cheatsheet

## Entity Annotations
| Annotation | Target | Purpose |
| :--- | :--- | :--- |
| `@Entity` | Class | Marks class as persistent JPA domain model |
| `@Table(name = "...")` | Class | Specifies database table name, indexes, and unique constraints |
| `@Id` | Field/Getter | Designates the primary key attribute |
| `@GeneratedValue` | Field/Getter | Configures ID strategy (`IDENTITY`, `SEQUENCE`, `AUTO`, `TABLE`) |
| `@Column(name = "...")` | Field/Getter | Maps attribute to database column; configures length, nullable, precision |
| `@Enumerated` | Field/Getter | Persists Enum as `STRING` (recommended) or `ORDINAL` |
| `@Transient` | Field/Getter | Instructs JPA to ignore field during database persistence |
| `@Version` | Field/Getter | Activates optimistic concurrency locking tracking |

## Relationship Annotations
| Annotation | Cardinality | Default Fetch | Owning Side Mechanism |
| :--- | :--- | :--- | :--- |
| `@OneToOne` | 1 to 1 | `EAGER` | `@JoinColumn` on owning side; `mappedBy` on inverse side |
| `@ManyToOne` | N to 1 | `EAGER` | `@JoinColumn(name = "foreign_key_id")` |
| `@OneToMany` | 1 to N | `LAZY` | `mappedBy = "fieldNameOnChild"` |
| `@ManyToMany` | N to N | `LAZY` | `@JoinTable(name = "join_tbl", joinColumns = ..., inverseJoinColumns = ...)` |

## Fetch Types & Cascades
| Concept | Options / Values | Production Guidance |
| :--- | :--- | :--- |
| Fetch Type | `LAZY`, `EAGER` | Always explicitly set `LAZY` on `@ManyToOne` and `@OneToOne` |
| Cascade Types | `PERSIST`, `MERGE`, `REMOVE`, `REFRESH`, `DETACH`, `ALL` | Use `ALL` only on strict parent-child aggregate boundaries |
| Orphan Removal | `orphanRemoval = true` | Automatically deletes child row when removed from Java collection |

## Transaction Propagation Behaviors
| Propagation | Existing Transaction Present | No Existing Transaction Present |
| :--- | :--- | :--- |
| `REQUIRED` (Default) | Joins existing transaction | Creates new transaction |
| `REQUIRES_NEW` | Suspends active transaction; creates new isolated one | Creates new transaction |
| `SUPPORTS` | Joins existing transaction | Executes non-transactionally |
| `NOT_SUPPORTED` | Suspends active transaction | Executes non-transactionally |
| `MANDATORY` | Joins existing transaction | Throws `TransactionRequiredException` |
| `NEVER` | Throws `IllegalTransactionStateException` | Executes non-transactionally |
| `NESTED` | Creates nested savepoint transaction | Creates new transaction |

## Isolation Levels & Concurrency Anomalies
| Isolation Level | Dirty Read | Non-Repeatable Read | Phantom Read |
| :--- | :--- | :--- | :--- |
| `READ_UNCOMMITTED` | Permitted | Permitted | Permitted |
| `READ_COMMITTED` | Prevented | Permitted | Permitted |
| `REPEATABLE_READ` | Prevented | Prevented | Permitted |
| `SERIALIZABLE` | Prevented | Prevented | Prevented |

## Repository Method Naming Conventions
| Prefix / Keyword | Example Method Signature | Generated JPQL Condition |
| :--- | :--- | :--- |
| `findBy...` | `findByStatus(OrderStatus status)` | `WHERE o.status = ?1` |
| `...And...` | `findByCustomerIdAndStatus(Long id, OrderStatus s)` | `WHERE o.customerId = ?1 AND o.status = ?2` |
| `...GreaterThan` | `findByTotalAmountGreaterThan(BigDecimal min)` | `WHERE o.totalAmount > ?1` |
| `...Between` | `findByCreatedAtBetween(Instant s, Instant e)` | `WHERE o.createdAt BETWEEN ?1 AND ?2` |
| `...In` | `findByStatusIn(Collection<OrderStatus> s)` | `WHERE o.status IN (?1)` |
| `...IgnoreCase` | `findByEmailIgnoreCase(String email)` | `WHERE UPPER(o.email) = UPPER(?1)` |
| `existsBy...` | `existsByOrderNumber(String num)` | `SELECT CASE WHEN COUNT(o) > 0 THEN true ...` |
| `countBy...` | `countByStatus(OrderStatus status)` | `SELECT COUNT(o) WHERE o.status = ?1` |

## Common @Query Examples
```java
// Eager JOIN FETCH to prevent N+1 queries
@Query("SELECT o FROM Order o JOIN FETCH o.customer JOIN FETCH o.items WHERE o.status = :status")
List<Order> findWithDetails(@Param("status") OrderStatus status);

// Constructor DTO projection
@Query("SELECT new com.example.dto.OrderSummary(o.id, o.orderNumber, o.totalAmount) FROM Order o WHERE o.customerId = :cid")
List<OrderSummary> findSummariesByCustomer(@Param("cid") Long cid);

// Bulk modifying update query with flush and clear
@Modifying(clearAutomatically = true, flushAutomatically = true)
@Query("UPDATE Order o SET o.status = :newStatus WHERE o.status = :oldStatus AND o.createdAt < :cutoff")
int bulkCancelStaleOrders(@Param("newStatus") OrderStatus newStatus, @Param("oldStatus") OrderStatus oldStatus, @Param("cutoff") Instant cutoff);
```
