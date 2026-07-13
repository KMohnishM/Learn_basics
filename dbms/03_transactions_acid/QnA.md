# Q&A — Transactions & ACID Semantics

---

## 🟢 Easy

**Q1. What is ACID? Briefly describe the component properties.**

ACID is an acronym representing the four core properties of a database transaction:
- **Atomicity**: The "all-or-nothing" rule. Either all statements in a transaction commit successfully, or the entire transaction is rolled back.
- **Consistency**: The database must remain in a valid state before and after the transaction, adhering to all integrity constraints.
- **Isolation**: Concurrent execution of transactions must yield the same state as if they were executed sequentially.
- **Durability**: Once a transaction commits, its changes are permanently written to disk and survive system crashes.

---

**Q2. Describe the states a transaction can enter during execution.**

1. **Active**: The transaction is running its operations.
2. **Partially Committed**: All operations are complete, but data is still in memory buffers (not written to disk).
3. **Committed**: Changes are flushed to non-volatile disk. Transaction complete.
4. **Failed**: Error detected; transaction cannot proceed.
5. **Aborted**: The database has rolled back all changes to restore the original state.

---

**Q3. What is a precedence graph? How is it constructed?**

A precedence graph (or serialization graph) is a directed graph used to test if a concurrent schedule is conflict serializable.
- **Nodes**: Represent active transactions ($T_1, T_2, \dots$).
- **Edges**: A directed edge $T_i \rightarrow T_j$ is drawn if $T_i$ executes a conflicting operation on data item $X$ before $T_j$ executes its conflicting operation.
  - Conflicting pairs: $r_i(X) \rightarrow w_j(X)$, $w_i(X) \rightarrow r_j(X)$, $w_i(X) \rightarrow w_j(X)$.
- **Serializability Rule**: If the graph has **no cycles**, the schedule is conflict serializable. If a cycle exists, the schedule is not conflict serializable.

---

## 🟡 Medium

**Q4. What is the difference between a recoverable schedule and a cascadeless schedule?**

- **Recoverable Schedule**: 
  - If a transaction $T_j$ reads data written by $T_i$, then $T_i$ must commit before $T_j$ commits ($Commit(T_i) < Commit(T_j)$).
  - This ensures that if $T_i$ aborts, we can roll back $T_j$. If $T_j$ committed first, we could not roll it back (violating durability of $T_j$'s commit).
- **Cascadeless Schedule**:
  - If $T_j$ reads data written by $T_i$, then $T_i$ must commit before $T_j$ reads it ($Commit(T_i) < Read_j(X)$).
  - This prevents **cascading aborts** (where aborting $T_1$ forces us to abort $T_2$, which forces us to abort $T_3$). Every transaction only reads committed, safe data.

All cascadeless schedules are recoverable, but not all recoverable schedules are cascadeless.

---

**Q5. Explain the "Lost Update" problem with a concrete query scenario.**

Let $X = 100$ (representing account balance).
- $T_1$ reads $X$ ($r_1(X) \rightarrow$ gets 100).
- $T_2$ reads $X$ ($r_2(X) \rightarrow$ gets 100).
- $T_1$ calculates new balance $100 - 20 = 80$ and writes it ($w_1(X) \rightarrow 80$).
- $T_2$ calculates new balance $100 + 50 = 150$ and writes it ($w_2(X) \rightarrow 150$).
- Both transactions commit.

**Result**: The balance is $150$. The subtraction of $20$ by $T_1$ is completely lost because $T_2$ overwrote it using the stale read value ($100$). The final value should have been $130$.

---

**Q6. What is a "blind write"? How does it relate to view serializability?**

A **blind write** occurs when a transaction writes a value to a data item without reading that item first (e.g., $w(X)$ without a preceding $r(X)$ in the same transaction).

**Relation to View Serializability**:
- If a schedule has **no cycles** in its precedence graph, it is conflict serializable (and therefore view serializable).
- If a schedule contains a cycle, it can **only** be view serializable if it contains at least one **blind write**.
- If a schedule has a cycle and *no* blind writes, it is guaranteed to be **not view serializable**. The presence of blind writes allows transactions to overwrite data without needing to preserve read dependency chains, which sometimes allows view equivalence to a serial schedule.

---

## 🔴 Hard

**Q7. Consider the following concurrent schedule $S_1$:**
$$S_1: r_1(A); \ r_2(B); \ r_1(B); \ r_2(C); \ w_1(A); \ w_2(B); \ w_1(C)$$
1. **Identify all conflicting operations.**
2. **Construct the precedence graph.**
3. **Determine if the schedule is conflict serializable. If yes, find the equivalent serial order.**

#### Part 1: Identify Conflicting Operations
We look for pairs of operations belonging to different transactions on the same data item where at least one is a write.

- For data item **A**:
  - $r_1(A)$ and $w_1(A)$ (same transaction, no conflict).
- For data item **B**:
  - $r_2(B)$ (T2) and $r_1(B)$ (T1) (both reads, no conflict).
  - $r_1(B)$ (T1) conflicts with $w_2(B)$ (T2) because they are different transactions and $w_2(B)$ is a write. Order: $r_1(B) \rightarrow w_2(B) \implies \mathbf{T_1 \rightarrow T_2}$.
- For data item **C**:
  - $r_2(C)$ (T2) conflicts with $w_1(C)$ (T1) because $w_1(C)$ is a write. Order: $r_2(C) \rightarrow w_1(C) \implies \mathbf{T_2 \rightarrow T_1}$.

#### Part 2: Precedence Graph
We have two transactions: $T_1$ and $T_2$.
- Edges:
  - $T_1 \rightarrow T_2$ (due to $r_1(B) \rightarrow w_2(B)$)
  - $T_2 \rightarrow T_1$ (due to $r_2(C) \rightarrow w_1(C)$)

```
       ┌───────►───────┐
      (T1)            (T2)
       └───────◄───────┘
```

#### Part 3: Conflict Serializability
- The precedence graph contains a cycle: $T_1 \rightarrow T_2 \rightarrow T_1$.
- Therefore, the schedule is **not conflict serializable**. There is no equivalent serial schedule.

---

**Q8. Classify the following schedule $S_2$ as: (a) Recoverable?, (b) Cascadeless (ACA)?, (c) Strict?**
$$S_2: w_1(A); \ w_2(B); \ r_1(B); \ w_1(A); \ c_1; \ c_2;$$
*(Note: $c_i$ represents commit of $T_i$)*

#### Step 1: Analyze read dependencies (who reads from whom)
- $T_1$ reads $B$ at step 3 ($r_1(B)$).
- Who wrote $B$ previously? $T_2$ wrote $B$ at step 2 ($w_2(B)$).
- Since $T_2$ has not committed before $r_1(B)$, $T_1$ is performing a **dirty read** (reading uncommitted data from $T_2$).

#### Step 2: Analyze write dependencies (who overwrites whom)
- $T_1$ writes $A$ at step 1 ($w_1(A)$).
- $T_1$ writes $A$ again at step 4 ($w_1(A)$).
- No other transaction writes $A$ in between.

#### Step 3: Check properties

**(a) Is $S_2$ Recoverable?**
- A schedule is recoverable if, for any transaction $T_j$ that reads from $T_i$, $T_i$ commits before $T_j$ commits.
- Here, $T_1$ reads from $T_2$.
- Therefore, $T_2$ must commit before $T_1$ commits ($Commit(T_2) < Commit(T_1)$).
- In the schedule: $T_1$ commits first ($c_1$ at step 5) and $T_2$ commits second ($c_2$ at step 6).
- Since $Commit(T_1) < Commit(T_2)$, the condition is violated.
- **Answer**: The schedule is **not recoverable**.

**(b) Is $S_2$ Cascadeless (ACA)?**
- A schedule is cascadeless if a transaction only reads committed data.
- Here, $T_1$ reads $B$ which was written by $T_2$, but $T_2$ has not committed yet.
- Since $T_1$ reads uncommitted data, it is not cascadeless.
- **Answer**: **No** (not cascadeless).

**(c) Is $S_2$ Strict?**
- A schedule is strict if no transaction can read or write a data item until the transaction that previously wrote it has committed or aborted.
- Since it is not even cascadeless, it cannot be strict.
- **Answer**: **No** (not strict).
