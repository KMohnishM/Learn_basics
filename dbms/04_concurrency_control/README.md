# Module 4: Concurrency Control

---

## 1. Lock-Based Protocols

Concurrency control protocols ensure that interleaved execution of transactions remains serializable. The most common approach uses **locks** to restrict access to data items.

### Lock Types
1. **Shared Lock (S)**:
   - Acquired for **Read** operations (`lock-S(X)`).
   - Multiple transactions can hold a Shared lock on the same data item simultaneously.
2. **Exclusive Lock (X)**:
   - Acquired for **Write** operations (`lock-X(X)`).
   - Only one transaction can hold an Exclusive lock on a data item. No other transaction can hold any lock (S or X) on it.

### Lock Compatibility Matrix
```
          Requested Lock
            ┌─────┬─────┐
            │  S  │  X  │
      ┌─────┼─────┼─────┤
      │  S  │  Y  │  N  │   (Y = Compatible, N = Incompatible)
Held  ├─────┼─────┼─────┤
Lock  │  X  │  N  │  N  │
      └─────┴─────┴─────┘
```

- If a transaction holds an Exclusive lock (X) on item $X$, any request from another transaction for $S$ or $X$ is denied; the requesting transaction must wait.

---

## 2. Two-Phase Locking (2PL)

Simply acquiring and releasing locks does not guarantee serializability. Consider this schedule:
$$r_1(A) \rightarrow \text{unlock}_1(A) \rightarrow r_2(A) \rightarrow w_2(A) \rightarrow r_2(B) \rightarrow w_2(B) \rightarrow \text{unlock}_2(A,B) \rightarrow r_1(B) \rightarrow \text{unlock}_1(B)$$
This is not conflict serializable even though locks were respected, because $T_1$ released its lock on $A$ too early.

**Two-Phase Locking (2PL)** prevents this by enforcing a strict locking rule:
> **A transaction cannot acquire any new lock once it has released any lock.**

### The Two Phases of 2PL
```
Number of
Locks Held
    ▲
    │          Growing Phase              Shrinking Phase
    │         (Acquire locks,             (Release locks,
    │          cannot release)             cannot acquire)
    │
    │               ┌───* Lock Point *
    │              ╱│                ╲
    │             ╱ │                 ╲
    │            ╱  │                  ╲
    │           ╱   │                   ╲
    │          ╱    │                    ╲
    └─────────┴─────┴─────────────────────┴──────────► Time
```

1. **Growing Phase**: Transaction may obtain locks, but cannot release any.
2. **Shrinking Phase**: Transaction may release locks, but cannot obtain any new locks.

- **Lock Point**: The moment the transaction releases its first lock (marks the end of the growing phase).
- **Theorem**: 2PL guarantees **conflict serializability**.
- **Limitations**: 
  - 2PL can lead to **deadlocks** (e.g., $T_1$ holds $A$, waits for $B$; $T_2$ holds $B$, waits for $A$).
  - Basic 2PL is subject to **cascading aborts** (if $T_1$ releases a lock on $X$ during its shrinking phase, $T_2$ can read $X$. If $T_1$ subsequently aborts, $T_2$ must be aborted too).

---

## 3. Variations of 2PL

To address cascading aborts and improve recovery, databases use stronger versions of 2PL:

### 1. Strict 2PL
- **Rule**: Follows 2PL, but all **Exclusive (X) locks** held by the transaction must be retained until the transaction commits or aborts.
- **Why**: Ensures that no other transaction can read or write uncommitted data modified by this transaction.
- **Benefit**: Guarantees **cascading abort-free (ACA)** and **strict** schedules. Most commercial DBMS engines implement Strict 2PL.

### 2. Rigorous 2PL
- **Rule**: All locks (both **Shared (S)** and **Exclusive (X)**) held by the transaction must be retained until the transaction commits or aborts.
- **Benefit**: Transactions serialize exactly in the order they commit. Simpler to manage but slightly reduces concurrency.

### 3. Conservative 2PL (Static 2PL)
- **Rule**: The transaction must pre-declare all data items it will access and acquire all required locks **before** it begins execution (growing phase happens atomically before transaction starts).
- **Benefit**: **Deadlock-free**. If any lock cannot be obtained, the transaction waits and holds no locks.
- **Drawback**: Poor resource utilization; hard to predict which locks are needed in advance (due to conditional branches in application code).

---

## 4. Timestamp-Ordering Protocol

A lock-free concurrency control protocol. The serialization order is determined entirely by transaction start times.

- When transaction $T_i$ enters the system, it is assigned a unique, monotonically increasing timestamp $TS(T_i)$ (e.g., system clock or logical counter).
- If $T_i$ is older than $T_j$, then $TS(T_i) < TS(T_j)$.
- The protocol associates two timestamp values with every database item $X$:
  - **$R-TS(X)$ (Read Timestamp)**: The largest timestamp of any transaction that successfully read $X$.
  - **$W-TS(X)$ (Write Timestamp)**: The largest timestamp of any transaction that successfully wrote $X$.

### Protocol Rules

#### 1. Read Operations (`read(X)` by $T_i$)
- If $TS(T_i) < W-TS(X)$:
  - $T_i$ is trying to read an older version of $X$ that has already been overwritten by a newer transaction.
  - **Action**: Abort and rollback $T_i$.
- If $TS(T_i) \ge W-TS(X)$:
  - The read is allowed.
  - Update: $R-TS(X) = \max(R-TS(X), TS(T_i))$.

#### 2. Write Operations (`write(X)` by $T_i$)
- If $TS(T_i) < R-TS(X)$:
  - $T_i$ is trying to write a value of $X$ that has already been read by a newer transaction. Allowing this write would make the newer transaction's read invalid (violating serialization order).
  - **Action**: Abort and rollback $T_i$.
- If $TS(T_i) < W-TS(X)$:
  - $T_i$ is trying to write an obsolete value of $X$ that has already been overwritten by a newer transaction.
  - **Action**: Abort and rollback $T_i$.
- If none of the above hold:
  - The write is allowed.
  - Update: $W-TS(X) = TS(T_i)$.

### Thomas' Write Rule (Optimization)
An optimization for the second write condition ($TS(T_i) < W-TS(X)$):
- Instead of aborting $T_i$, we can simply **ignore (skip) the write** and let $T_i$ proceed.
- Since $TS(T_i) < W-TS(X)$, the write by $T_i$ is obsolete and would have been immediately overwritten by the write with timestamp $W-TS(X)$ anyway.
- **Result**: Higher throughput, fewer aborts. It yields schedules that are view serializable but not conflict serializable.

---

## 5. Multiversion Concurrency Control (MVCC)

To prevent reads from blocking writes and writes from blocking reads, modern databases (MySQL InnoDB, PostgreSQL, Oracle) implement **MVCC**.

### Concept
- Instead of overwriting data items, each write creates a **new version** of the data item with a timestamp/system-transaction-ID.
- The database maintains a chain of historical versions for each row.
- **Read**: A transaction reads the most recent version of the row that is older than the transaction's own read-timestamp (or active transaction snapshot). No locks are acquired for reads.
- **Write**: A transaction writes a new version of the row with its own transaction ID. Writes still acquire exclusive locks to prevent concurrent write-write conflicts on the same row.

### InnoDB (MySQL) Implementation Details
- **Undo Logs**: When a row is updated, InnoDB writes the old version of the row to the **Undo Log**.
- **Rollback Pointer**: Each row contains metadata:
  - `DB_TRX_ID`: The ID of the last transaction that modified the row.
  - `DB_ROLL_PTR`: Pointer to the undo log record containing the previous version.
- **Read View**: When a transaction starts under `READ COMMITTED` or `REPEATABLE READ`, InnoDB creates a Read View (a snapshot of active transaction IDs).
  - `READ COMMITTED`: Creates a new Read View for *every SELECT* statement. Shows updates committed by other transactions mid-session.
  - `REPEATABLE READ`: Creates one Read View at the *start of the transaction*. All SELECT queries in that transaction read from this same snapshot, ensuring repeatable reads without locking.

---

## 6. Deadlock Handling

Deadlocks occur when two or more transactions are blocked, each waiting for a lock held by another in a cyclic dependency.

### Deadlock Detection (Wait-For Graph)
- **Wait-For Graph (WFG)**: Nodes represent active transactions. A directed edge $T_i \rightarrow T_j$ is created if $T_i$ is waiting for a lock held by $T_j$.
- The lock manager periodically runs a cycle detection algorithm (e.g., DFS) on the WFG.
- If a **cycle is found**, a deadlock exists. The database must select a **victim transaction** to abort and roll back, releasing its locks so other transactions can proceed.
  - **Victim Selection Criteria**: Minimum cost (based on transaction age, number of updates made, lock count).

### Deadlock Prevention (Timestamp-Based)
Instead of detecting deadlocks after they occur, we can prevent them from forming by deciding what happens when a lock cannot be obtained immediately, using transaction timestamps:

Assume $T_{\text{req}}$ (requesting lock) and $T_{\text{held}}$ (holding lock).
Older transaction = smaller timestamp.

#### 1. Wait-Die Protocol (Non-Preemptive)
- If $TS(T_{\text{req}}) < TS(T_{\text{held}})$ ($T_{\text{req}}$ is **older**):
  - **Action**: $T_{\text{req}}$ is allowed to **wait**.
- If $TS(T_{\text{req}}) > TS(T_{\text{held}})$ ($T_{\text{req}}$ is **younger**):
  - **Action**: $T_{\text{req}}$ **dies** (aborts and restarts with the same timestamp).

*Intuition*: Older transactions are allowed to wait for younger ones; younger transactions die when conflicting with older ones.

#### 2. Wound-Wait Protocol (Preemptive)
- If $TS(T_{\text{req}}) < TS(T_{\text{held}})$ ($T_{\text{req}}$ is **older**):
  - **Action**: $T_{\text{req}}$ **wounds** $T_{\text{held}}$, forcing $T_{\text{held}}$ to abort and release the lock.
- If $TS(T_{\text{req}}) > TS(T_{\text{held}})$ ($T_{\text{req}}$ is **younger**):
  - **Action**: $T_{\text{req}}$ is allowed to **wait**.

*Intuition*: Older transactions preempt ("wound") younger ones to get the lock immediately; younger transactions wait for older ones.

**Comparison**: Wound-wait typically results in fewer aborts than wait-die because a younger transaction waiting for an older one is highly likely to get the lock when the older one commits (which happens quickly).
