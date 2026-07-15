# Cheat Sheet — Concurrency Control

## Lock Compatibility Matrix
```
          Requested Lock
            ┌─────┬─────┐
            │  S  │  X  │
      ┌─────┼─────┼─────┤
      │  S  │  Y  │  N  │   (Y = Compatible/Granted,
Held  ├─────┼─────┼─────┤    N = Conflict/Wait)
Lock  │  X  │  N  │  N  │
      └─────┴─────┴─────┘
```

---

## Two-Phase Locking (2PL)

**Core Rule**: No lock can be acquired after any lock is released.

| 2PL Variation | Exclusive (X) Locks | Shared (S) Locks | Avoids Cascade Aborts? |
|---------------|---------------------|------------------|:----------------------:|
| **Basic 2PL** | Released during shrinking phase | Released during shrinking phase | ❌ No |
| **Strict 2PL** | Held until commit/abort | Released during shrinking phase | ✅ Yes |
| **Rigorous 2PL** | Held until commit/abort | Held until commit/abort | ✅ Yes |

- **Conservative 2PL**: Acquire *all* locks before execution. **Deadlock-free**.

---

## Timestamp-Ordering Protocol

Let $TS(T_i)$ = transaction timestamp, $W-TS(X)$ = write timestamp of $X$, $R-TS(X)$ = read timestamp of $X$.

### Read Rule (for $r_i(X)$):
- If $TS(T_i) < W-TS(X)$ $\implies$ **Abort & Restart** (reading overwritten data).
- Else $\implies$ **Allow**. Update: $R-TS(X) = \max(R-TS(X), TS(T_i))$.

### Write Rule (for $w_i(X)$):
- If $TS(T_i) < R-TS(X)$ $\implies$ **Abort & Restart** (writing data already read by newer trans).
- If $TS(T_i) < W-TS(X)$ $\implies$:
  - *Standard*: **Abort & Restart**.
  - *Thomas' Write Rule*: **Ignore write** and continue (obsolete write skipped).
- Else $\implies$ **Allow**. Update: $W-TS(X) = TS(T_i)$.

---

## Deadlock Prevention Protocols

Older transaction = smaller timestamp. Let requesting transaction be $T_{\text{req}}$, lock holder be $T_{\text{held}}$.

### Wait-Die (Non-Preemptive)
```
If TS(T_req) < TS(T_held)  [Older requests younger]  →  T_req WAITS
If TS(T_req) > TS(T_held)  [Younger requests older]  →  T_req DIES (Aborts)
```

### Wound-Wait (Preemptive)
```
If TS(T_req) < TS(T_held)  [Older requests younger]  →  T_req WOUNDS T_held (Holder Aborts)
If TS(T_req) > TS(T_held)  [Younger requests older]  →  T_req WAITS
```

---

## MVCC Internals (InnoDB)

Each row in InnoDB contains hidden columns:
- `DB_TRX_ID` (6 bytes): Transaction ID of the last transaction that inserted/updated the row.
- `DB_ROLL_PTR` (7 bytes): Pointer to the rollback segment in the **Undo Log** containing the previous version of the row.

### Snapshot Read Rules (Read View)
When a transaction reads $X$:
- Under **READ COMMITTED**: A new Read View is generated for **each SELECT query**. Shows updates committed by other transactions mid-transaction.
- Under **REPEATABLE READ**: A single Read View is generated when the **first SELECT runs**. All subsequent reads use this same snapshot, ensuring repeatable reads without lock overhead.
- Reads never block writes; writes never block reads.
