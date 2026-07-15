# Q&A — Concurrency Control

---

## 🟢 Easy

**Q1. Explain Shared and Exclusive locks. How does the compatibility matrix work?**

- **Shared Lock (S)**: Acquired when reading data. Multiple transactions can hold shared locks on the same data item simultaneously (read operations do not conflict).
- **Exclusive Lock (X)**: Acquired when writing/modifying data. Only one transaction can hold an exclusive lock on an item. No other transaction can hold any lock on it until the exclusive lock is released.

**Compatibility Matrix**:
- If a request is compatible with all currently held locks, it is granted.
- If it conflicts with any currently held lock, the requesting transaction must wait.
- Request for S is compatible with held S, but conflicts with held X.
- Request for X conflicts with both held S and held X.

---

**Q2. What is the "Lock Point" of a transaction in 2PL?**

In Two-Phase Locking (2PL), the **Lock Point** of a transaction is the exact moment at which it **acquires its final (last) lock** — the peak of the lock-holding curve.
- It marks the boundary where the **Growing Phase** ends and the **Shrinking Phase** begins.
- Note: This is the same boundary as when the first lock *could* be released, but the standard definition (Silberschatz, Ramakrishnan) frames it as "the last acquisition," not "the first release."
- The lock point is important because the serialization order of transactions in a 2PL schedule is determined by the chronological order of their lock points.

---

**Q3. How does Wait-For Graph (WFG) deadlock detection work?**

- Vertices in the WFG represent active transactions.
- A directed edge $T_i \rightarrow T_j$ is created if transaction $T_i$ is waiting for a lock on a data item that is currently held by $T_j$.
- The DBMS periodically runs a cycle detection algorithm (like Depth First Search) on the WFG.
- If a **cycle** is detected (e.g., $T_1 \rightarrow T_2 \rightarrow T_1$), a deadlock exists. The DBMS breaks the cycle by aborting one of the transactions (the "victim").

---

## 🟡 Medium

**Q4. Compare Basic 2PL, Strict 2PL, and Rigorous 2PL.**

- **Basic 2PL**:
  - Once a transaction releases a lock, it cannot acquire any new locks.
  - Allows locks to be released during execution (shrinking phase can happen gradually).
  - Can cause cascading aborts and deadlocks.
- **Strict 2PL**:
  - Follows 2PL, but **Exclusive (X) locks** must be held until the transaction commits or aborts.
  - Prevents other transactions from reading uncommitted modifications.
  - Eliminates cascading aborts. Still subject to deadlocks.
- **Rigorous 2PL**:
  - Follows 2PL, but **all locks** (both Shared and Exclusive) must be held until commit or abort.
  - No shrinking phase during execution; all locks released atomically at the end.
  - Serializability order is the commit order. Most restrictive but easiest to recover.

---

**Q5. Explain Thomas' Write Rule. How does it improve concurrency?**

Thomas' Write Rule is an optimization of the standard Timestamp-Ordering protocol for write operations.
- **Rule**: If transaction $T_i$ requests a write on $X$ ($w_i(X)$), and $TS(T_i) < W-TS(X)$ (a newer transaction has already written $X$):
  - Instead of aborting and restarting $T_i$ (as required by the standard protocol), we **ignore (skip) the write** by $T_i$ and allow the transaction to continue.
- **Why it is safe**: Since a newer transaction has already overwritten $X$, the write from $T_i$ is obsolete. If we wrote it, it would be immediately overwritten anyway.
- **Benefit**: It prevents unnecessary aborts and rollbacks for late-arriving writes, improving system throughput.

---

## 🔴 Hard

**Q6. Transaction timestamps are: $TS(T_1) = 10$, $TS(T_2) = 20$, $TS(T_3) = 30$. Determine the action taken (Wait, Die, or Wound) in the following scenarios under: (1) Wait-Die Protocol, (2) Wound-Wait Protocol.**

*Rules recap:*
- **Wait-Die**: If $TS(T_{\text{req}}) < TS(T_{\text{held}})$ (older requests younger) $\rightarrow$ **Wait**. Else (younger requests older) $\rightarrow$ **Die** (abort).
- **Wound-Wait**: If $TS(T_{\text{req}}) < TS(T_{\text{held}})$ (older requests younger) $\rightarrow$ **Wound** (abort holder). Else (younger requests older) $\rightarrow$ **Wait**.

#### Scenario A: $T_2$ holds a lock on $X$. $T_1$ requests the lock on $X$.
Here, $T_{\text{req}} = T_1$ ($TS=10$), $T_{\text{held}} = T_2$ ($TS=20$).
$T_1$ is **older** than $T_2$ ($10 < 20$).

- **Wait-Die**: Since the requesting transaction ($T_1$) is older, it is allowed to **Wait**.
- **Wound-Wait**: Since the requesting transaction ($T_1$) is older, it **Wounds** $T_2$, forcing $T_2$ to abort and release the lock.

#### Scenario B: $T_2$ holds a lock on $Y$. $T_3$ requests the lock on $Y$.
Here, $T_{\text{req}} = T_3$ ($TS=30$), $T_{\text{held}} = T_2$ ($TS=20$).
$T_3$ is **younger** than $T_2$ ($30 > 20$).

- **Wait-Die**: Since the requesting transaction ($T_3$) is younger, it **Dies** (aborts and restarts).
- **Wound-Wait**: Since the requesting transaction ($T_3$) is younger, it is allowed to **Wait**.

---

**Q7. Trace the MVCC read behavior under READ COMMITTED and REPEATABLE READ isolation levels. Given this sequence of events on row $X$ (initially $X = 10$, committed by transaction $T_0$):**
- **Time 1**: $T_1$ starts (under REPEATABLE READ).
- **Time 2**: $T_2$ starts (under READ COMMITTED).
- **Time 3**: $T_3$ updates $X$ to $20$ and commits.
- **Time 4**: $T_1$ reads $X$. What value does it get?
- **Time 5**: $T_2$ reads $X$. What value does it get?
- **Time 6**: $T_4$ updates $X$ to $30$ (uncommitted).
- **Time 7**: $T_2$ reads $X$ again. What value does it get?
- **Time 8**: $T_4$ commits.
- **Time 9**: $T_2$ reads $X$ again. What value does it get?

#### Step-by-step analysis:

- **Time 4: $T_1$ reads $X$ (REPEATABLE READ)**
  - **⚠️ InnoDB Note**: In InnoDB, the Read View for REPEATABLE READ is created at the time of the **first SELECT statement**, not at `BEGIN`/`START TRANSACTION`. This question specifies Time 4 as $T_1$'s *first* read — so the Read View is created at Time 4.
  - At Time 4, the committed versions of $X$ are: $10$ (by $T_0$) and $20$ (committed by $T_3$ at Time 3). At the moment the Read View is created at Time 4, $T_3$ is already committed.
  - Therefore, the Read View's `up_to_trx_id` will include $T_3$'s commit. The most recent committed version visible to $T_1$'s Read View is $20$.
  - **Result**: $T_1$ reads **$20$**.
  - *Note*: If $T_1$ had executed any SELECT statement *before* Time 3 (e.g., a `SELECT 1`), then its Read View would have been fixed earlier and it would see $10$. This is a well-known InnoDB subtlety: use `START TRANSACTION WITH CONSISTENT SNAPSHOT` to force Read View creation at BEGIN.

- **Time 5: $T_2$ reads $X$ (READ COMMITTED)**
  - Under Read Committed, $T_2$ creates a *new* Read View for this specific read statement.
  - The most recently committed version of $X$ at Time 5 is $20$ (committed by $T_3$ at Time 3).
  - **Result**: $T_2$ reads **$20$**.

- **Time 7: $T_2$ reads $X$ again (READ COMMITTED)**
  - $T_2$ creates a new Read View.
  - The update to $30$ by $T_4$ at Time 6 is *uncommitted*.
  - Read Committed only allows reading committed data. It ignores the uncommitted version $30$ and falls back to the most recently committed version, which is $20$.
  - **Result**: $T_2$ reads **$20$**.

- **Time 9: $T_2$ reads $X$ again (READ COMMITTED)**
  - $T_2$ creates a new Read View.
  - $T_4$ has now committed its update to $30$ (at Time 8).
  - The most recently committed version of $X$ is now $30$.
  - **Result**: $T_2$ reads **$30$** (showing a Non-Repeatable Read, which is allowed under Read Committed).
  - *Note*: If $T_1$ reads $X$ at Time 9, it will still read **$10$** because its snapshot was fixed at Time 1.
