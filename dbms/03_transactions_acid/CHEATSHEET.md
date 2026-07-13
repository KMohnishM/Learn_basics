# Cheat Sheet — Transactions & ACID Semantics

## Transaction States
```
          ┌───────────────► Partially Committed ────────► Committed (End)
          │                       │
       (Begin)                    │ (Log flush fails)
          │                       ▼
        Active ──────────────► Failed
          │                       │
          │ (Abort/Error)         │
          └───────────────► Aborted (Rollback) ─────────► (End)
```

---

## ACID Invariants
- **Atomicity**: "All-or-Nothing." Implemented by **Recovery Manager** (Undo/Redo logs).
- **Consistency**: Invariants preserved. Implemented by **application developer** + DB constraints.
- **Isolation**: Concurrent execution $\equiv$ Serial. Implemented by **Concurrency Control** (locks, MVCC).
- **Durability**: Committed data survives crashes. Implemented by **Recovery Manager** (WAL + disk flush).

---

## Read/Write Concurrency Anomalies

- **Dirty Read**: $T_2$ reads data written by uncommitted $T_1$. If $T_1$ aborts, $T_2$'s read is invalid.
  $$w_1(X) \rightarrow r_2(X) \rightarrow \text{Abort}(T_1)$$
- **Non-Repeatable Read**: $T_1$ reads $X$, $T_2$ overwrites and commits, $T_1$ reads $X$ again and gets different value.
  $$r_1(X) \rightarrow w_2(X) \rightarrow \text{Commit}(T_2) \rightarrow r_1(X)$$
- **Phantom Read**: $T_1$ reads range of rows, $T_2$ inserts a new row in range and commits, $T_1$ reads range again and gets new row.
  $$r_1(\text{range } X) \rightarrow \text{Insert}_2(Y \in X) \rightarrow \text{Commit}(T_2) \rightarrow r_1(\text{range } X)$$
- **Lost Update**: $T_1$ and $T_2$ read $X$, both write updates, second write overwrites first write.
  $$r_1(X) \rightarrow r_2(X) \rightarrow w_1(X) \rightarrow w_2(X)$$

---

## SQL Isolation Levels (ANSI SQL-92)

| Isolation Level | Dirty Read | Non-Repeatable Read | Phantom Read | Lost Update |
|-----------------|:----------:|:-------------------:|:------------:|:-----------:|
| **Read Uncommitted**| Allowed | Allowed | Allowed | Allowed |
| **Read Committed**  | ❌ | Allowed | Allowed | Allowed |
| **Repeatable Read** | ❌ | ❌ | Allowed | ❌ |
| **Serializable**    | ❌ | ❌ | ❌ | ❌ |

---

## Serializability Checks

### Conflict Serializability (Precedence Graph)
Draw directed graph: vertices = transactions.
Draw edge $T_i \rightarrow T_j$ if $T_i$ executes operation conflicting with subsequent operation of $T_j$:
- $r_i(X) \rightarrow w_j(X)$
- $w_i(X) \rightarrow r_j(X)$
- $w_i(X) \rightarrow w_j(X)$

**Acyclic Graph** $\implies$ Conflict Serializable. Topological sort order = Equivalent Serial Schedule.
**Cyclic Graph** $\implies$ Not Conflict Serializable.

### View Serializability
Schedules $S_1$ and $S_2$ are view equivalent if:
1. **Initial Read**: $T_i$ reads initial value of $X$ in $S_1 \iff T_i$ reads initial value in $S_2$.
2. **Write-Read**: $T_i$ writes $X$ and $T_j$ reads that value in $S_1 \iff T_i$ writes $X$ and $T_j$ reads that value in $S_2$.
3. **Final Write**: $T_i$ does final write of $X$ in $S_1 \iff T_i$ does final write of $X$ in $S_2$.

*Shortcut*: If conflict serializable, it is view serializable. If not conflict serializable, it can only be view serializable if it contains a **blind write** (write without read).

---

## Schedule Recoverability

- **Recoverable**: If $T_j$ reads from $T_i$, then $T_i$ must commit before $T_j$ commits:
  $$w_i(X) \rightarrow r_j(X) \implies Commit(T_i) < Commit(T_j)$$
- **Cascadeless (ACA)**: If $T_j$ reads from $T_i$, then $T_i$ must commit before $T_j$ reads:
  $$w_i(X) \rightarrow r_j(X) \implies Commit(T_i) < r_j(X)$$
- **Strict**: If $T_i$ writes $X$, no other transaction can read or write $X$ until $T_i$ commits/aborts:
  $$w_i(X) \rightarrow \text{operation}_j(X) \implies Commit(T_i) < \text{operation}_j(X) \quad (\text{operation is } r \text{ or } w)$$

```
Strict ⊂ Cascadeless (ACA) ⊂ Recoverable
```
