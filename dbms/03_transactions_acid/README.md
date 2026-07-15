# Module 3: Transactions & ACID Semantics

---

## 1. Concept of a Transaction

A **transaction** is a logical unit of database processing that includes one or more database access operations (read, write, insert, delete). 

### Transaction States & Transitions
A transaction moves through various states during its lifecycle:

```
          ┌───────────────► PARTIALLY COMMITTED ────────► COMMITTED (End)
          │                      │
       (Begin)                   │ (Flush log to disk fails)
          │                      ▼
        ACTIVE ──────────────► FAILED
          │                      │
          │ (Error/Abort)        │
          └───────────────► ABORTED (Rollback) ─────────► (End)
```

1. **Active**: The initial state. The transaction stays active while executing its read/write operations.
2. **Partially Committed**: After the final statement has been executed, but before changes are flushed to disk (data is still in volatile memory).
3. **Committed**: After all log records and updates are safely flushed to non-volatile storage (disk/SSD). The transaction completes successfully.
4. **Failed**: After the database detects that normal execution can no longer proceed (due to hardware error, deadlock, or internal checks).
5. **Aborted**: The transaction has been rolled back. The database is restored to its state prior to the transaction's start.
   - **Rollback options**: Restart the transaction (if failed due to system load/deadlock) or kill the transaction (if failed due to logical error).

---

## 2. The ACID Properties

To ensure data integrity under concurrent execution and system crashes, the DBMS must guarantee the **ACID** properties:

- **Atomicity** ("All or Nothing"):
  - Either all operations of the transaction are committed successfully, or none are. If a transaction fails mid-way, all completed writes must be undone (rolled back).
  - *Guaranteed by*: The **Recovery Manager** using log files (Undo/Redo logs) or shadow paging.
- **Consistency** ("Correctness"):
  - A transaction must transition the database from one valid state to another, preserving all database invariants (e.g., account balances cannot go below zero, total money in a bank must remain constant).
  - *Guaranteed by*: The **application developer** (business logic) and the **DBMS compiler** (declaring checks, foreign key constraints, unique checks).
- **Isolation** ("Independence"):
  - Concurrent execution of transactions must yield the same database state as if they were run sequentially (one after another). The intermediate state of a running transaction is hidden from other concurrent transactions.
  - *Guaranteed by*: The **Concurrency Control Manager** using locking protocols, timestamps, or MVCC.
- **Durability** ("Permanence"):
  - Once a transaction commits, its updates persist in the database and cannot be lost even in the event of a subsequent system crash or power failure.
  - *Guaranteed by*: The **Recovery Manager** using Write-Ahead Logging (WAL) and non-volatile storage flushing (forcing logs to disk before committing).

---

## 3. Read/Write Anomalies (Concurrency Bugs)

When transactions run concurrently without proper isolation, several anomalies can occur:

### 1. Dirty Read (Reading Uncommitted Data)
Occurs when Transaction $T_1$ modifies a data item, and Transaction $T_2$ reads that data item *before* $T_1$ commits. If $T_1$ subsequently aborts (rolls back), $T_2$ has read a value that never officially existed.
$$\text{Sequence: } w_1(X) \rightarrow r_2(X) \rightarrow \text{Abort}(T_1)$$

### 2. Non-Repeatable Read (Fuzzy Read)
Occurs when Transaction $T_1$ reads a data item. Transaction $T_2$ then modifies/updates that data item and commits. If $T_1$ reads the same data item again, it finds a different (updated) value.
$$\text{Sequence: } r_1(X) \rightarrow w_2(X) \rightarrow \text{Commit}(T_2) \rightarrow r_1(X)$$

### 3. Phantom Read
Occurs when Transaction $T_1$ reads a set of rows matching a search condition (e.g., `WHERE salary > 50000`). Transaction $T_2$ inserts a *new* row matching the condition and commits. When $T_1$ runs the query again, a new "phantom" row appears.
$$\text{Sequence: } r_1(\text{range } X) \rightarrow \text{Insert}_2(Y \in X) \rightarrow \text{Commit}(T_2) \rightarrow r_1(\text{range } X)$$

### 4. Lost Update
Two transactions read the same data item $X$. Both compute a new value and write it back. The second transaction's write overwrites the first transaction's write without incorporating it, effectively losing one of the updates.
$$\text{Sequence: } r_1(X) \rightarrow r_2(X) \rightarrow w_1(X) \rightarrow w_2(X)$$

---

## 4. ANSI SQL Transaction Isolation Levels

To balance concurrency performance and safety, SQL standards define four isolation levels. MySQL's InnoDB supports all four:

| Isolation Level | Dirty Read | Non-Repeatable Read | Phantom Read | Lost Update |
|-----------------|:----------:|:-------------------:|:------------:|:-----------:|
| **Read Uncommitted** | Allowed | Allowed | Allowed | Allowed |
| **Read Committed** | ❌ Prevented | Allowed | Allowed | Allowed |
| **Repeatable Read** (MySQL Default) | ❌ Prevented | ❌ Prevented | Allowed | ❌ Prevented |
| **Serializable** | ❌ Prevented | ❌ Prevented | ❌ Prevented | ❌ Prevented |

- **MySQL InnoDB Optimization**: In InnoDB, the default **Repeatable Read** level also prevents Phantom Reads in many cases using **Next-Key Locking** (locking index records and gaps) and MVCC.

---

## 5. Schedules & Serializability

A **Schedule ($S$)** is a chronological sequence of execution steps of concurrent transactions.

- **Serial Schedule**: A schedule where transactions are executed one after another, with no interleaving of operations. If $T_1$ starts, it completes entirely before $T_2$ begins.
- **Concurrent Schedule**: Operations of $T_1, T_2, \dots, T_k$ are interleaved.
- **Serializable Schedule**: A concurrent schedule that is equivalent in effect to *some* serial execution of those transactions.

### Conflict Serializability
Two operations conflict if they meet all three conditions:
1. They belong to **different** transactions.
2. They access the **same** data item (e.g., $X$).
3. At least one of the operations is a **Write** ($w$).

**Conflict Equivalent Schedules**: Two schedules $S_1$ and $S_2$ are conflict equivalent if they contain the same transactions and operations, and the order of all conflicting operations is the same in both.

**Conflict Serializable**: A schedule is conflict serializable if it is conflict equivalent to some serial schedule.

#### Testing Conflict Serializability (Precedence Graph)
To test if a schedule $S$ is conflict serializable:
1. Create a directed graph $G = (V, E)$ where vertices $V$ represent transactions.
2. Draw an edge $T_i \rightarrow T_j$ if $T_i$ performs an operation that conflicts with a subsequent operation of $T_j$. This occurs if:
   - $r_i(X)$ occurs before $w_j(X)$
   - $w_i(X)$ occurs before $r_j(X)$
   - $w_i(X)$ occurs before $w_j(X)$
3. **The Cycle Rule**:
   - If the precedence graph has **no cycles**, the schedule is **conflict serializable**.
   - If the graph has a cycle, it is **not conflict serializable**.
4. The topological sort of the acyclic graph gives the equivalent serial schedule execution order.

### View Serializability
A more general form of serializability. Every conflict serializable schedule is view serializable, but some view serializable schedules are not conflict serializable.

Two schedules $S_1$ and $S_2$ are **view equivalent** if:
1. **Initial Read**: If $T_i$ reads the initial value of $X$ in $S_1$, it must read the initial value of $X$ in $S_2$.
2. **Write-Read**: If $T_i$ writes $X$ and $T_j$ reads that value in $S_1$, $T_j$ must read the value written by $T_i$ in $S_2$.
3. **Final Write**: The transaction that performs the final write on $X$ in $S_1$ must perform the final write on $X$ in $S_2$.

**View Serializable**: A schedule is view serializable if it is view equivalent to a serial schedule.
- Testing for view serializability is **NP-complete**.
- A schedule that is view serializable but *not* conflict serializable must contain at least one **blind write** (a transaction writes $X$ without reading it first, $w(X)$ without preceding $r(X)$).

---

## 6. Recoverability of Schedules

Even if a schedule is serializable, it may not be recoverable in the event of an abort.

### 1. Recoverable Schedule
If a transaction $T_j$ reads a data item written by $T_i$ (dirty read/dependency), then the commit operation of $T_i$ must appear before the commit operation of $T_j$:
$$\text{If } w_1(X) \rightarrow r_2(X), \text{ then } \text{Commit}(T_1) < \text{Commit}(T_2)$$
If $T_1$ aborts, we must abort $T_2$ as well. If $T_2$ committed before $T_1$ aborted, the database is in an unrecoverable state because $T_2$'s committed data depends on an aborted transaction.

### 2. Cascadeless Schedule (Avoids Cascading Aborts - ACA)
In a recoverable schedule, if $T_1$ aborts, $T_2$ must also abort. If $T_3$ read from $T_2$, $T_3$ aborts too. This is a **cascading abort**, which wastes CPU and memory resources.
A schedule is **cascadeless** if every transaction reads only committed data:
$$\text{If } w_1(X) \rightarrow r_2(X), \text{ then } \text{Commit}(T_1) < r_2(X)$$
No transaction can read uncommitted data. Eliminates the possibility of cascading aborts entirely.

### 3. Strict Schedule
A schedule is **strict** if a value written by $T_i$ cannot be read OR written by any other transaction until $T_i$ has committed or aborted:
$$\text{If } w_1(X) \rightarrow \text{operation}_2(X), \text{ then } \text{Commit}(T_1) < \text{operation}_2(X) \quad (\text{where operation is } r \text{ or } w)$$
Strict schedules make recovery simple: if a transaction aborts, the recovery manager can restore the database simply by copying the "before-image" of the modified data items.

```
Relationships:
Strict Schedules ⊂ Cascadeless (ACA) Schedules ⊂ Recoverable Schedules
```
