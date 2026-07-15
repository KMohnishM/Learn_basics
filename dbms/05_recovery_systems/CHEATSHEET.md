# Cheat Sheet — Recovery Systems

## Write-Ahead Logging (WAL) Rules
1. **Log Before Page**: Write the update log record to disk *before* writing the modified database page to disk.
2. **Flush on Commit**: A transaction is committed only when its `COMMIT` log record is safely flushed to disk.

---

## Database Modification Schemes

| Feature | Deferred Modification (No-Undo/Redo) | Immediate Modification (Undo/Redo) |
|---------|--------------------------------------|------------------------------------|
| **When are writes to disk allowed?** | Only after commit | At any time (even before commit) |
| **Recovery action on crash** | **REDO** committed transactions. Ignore uncommitted. | **REDO** committed. **UNDO** uncommitted. |
| **Log record values needed** | New value only (`<T_i, X, new_value>`) | Both old and new (`<T_i, X, old, new>`) |
| **Buffer Management** | Simple (no stealing) | Complex (allows page steal) |

---

## Checkpoint Recovery Sets

Given a crash, locate the last `<checkpoint L>`:
- **Redo-list**: Transactions that committed *after* the checkpoint and *before* the crash.
- **Undo-list**: Transactions active during checkpoint ($L$) or started after checkpoint, but not committed before the crash.

---

## ARIES Recovery Phases

```
  Checkpoint               Crash
      │                      │
      ▼                      ▼
  ───[ ANALYSIS ]───────────►   (Scan forward: find active transactions & dirty pages)
             │
             ▼ (from min recLSN in DPT)
  ──────────[ REDO ]────────►   (Scan forward: repeat all history)
                             │
                             ▼ (from end of log)
  ◄─────────[ UNDO ]─────────   (Scan backward: rollback active "loser" transactions)
```

### 1. Analysis Phase
- Start: Last checkpoint record.
- Scan direction: **Forward** to the end of the log.
- Output: Transaction Table (active transactions) and Dirty Page Table (pages with modifications not flushed).

### 2. Redo Phase
- Start: Oldest `recLSN` in the Dirty Page Table.
- Scan direction: **Forward** to the end of the log.
- Action: Reapply all changes (both committed and to-be-aborted transactions). **Skip** if PageLSN on disk ≥ LSN of log record (already persisted).

### 3. Undo Phase
- Start: End of the log.
- Scan direction: **Backward** to the oldest active transaction start.
- Action: Roll back changes of all "loser" transactions (active at crash).

---

## Shadow Paging vs. Log-Based Recovery

- **Shadow Paging**:
  - *How*: Dual page tables (Current & Shadow). Copy-on-Write for updates. Swap pointers on commit.
  - *Pros*: Simple rollback (discard current table). No log parsing.
  - *Cons*: Causes massive page fragmentation (random I/O). Expensive page table swaps.
- **Log-Based (WAL)**:
  - *How*: Append-only sequential log. In-place database page updates.
  - *Pros*: Sequential writes are fast. Pages stay clustered on disk.
  - *Cons*: Complex recovery algorithms (ARIES) needed.
