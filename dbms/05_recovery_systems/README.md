# Module 5: Recovery Systems

---

## 1. Failure Classification

To design a recovery system, we must first understand the types of failures that can occur:

1. **Transaction Failure**:
   - **Logical Error**: The transaction cannot complete due to internal conditions (e.g., integrity constraint violation, bad input, division by zero).
   - **System Error**: The database terminates the transaction due to deadlock or lack of resources.
2. **System Crash**:
   - Volatile memory (RAM, cache buffers) is lost due to power outage or OS kernel panic.
   - Non-volatile storage (SSD, HDD) survives intact.
   - Database state must be reconstructed to a consistent state upon reboot.
3. **Disk Failure**:
   - Non-volatile storage is physically damaged (e.g., head crash, bad sectors).
   - *Recovery*: Requires restoring data from archives (backups) and replaying committed transaction logs up to the failure point.

---

## 2. Write-Ahead Logging (WAL) Protocol

The **Write-Ahead Logging (WAL)** protocol is the fundamental rule that guarantees both **Atomicity** and **Durability** in log-based recovery systems:

1. **Write-Ahead Log Rule**:
   - The database must write (flush) the log record describing a modification to disk **before** the actual dirty database page containing the modification is written to disk.
   - *Why*: If the database page is written first and the system crashes, we cannot roll back (Undo) the change because the log record containing the old value does not exist on disk.
2. **Transaction Commit Rule**:
   - A transaction is not considered "committed" until its `COMMIT` log record has been physically flushed to non-volatile disk.
   - *Why*: Ensures durability.

### Log Record Structure
Each log entry is assigned a unique **LSN (Log Sequence Number)** and contains:
- `<T_i, Start>`: Transaction $T_i$ started.
- `<T_i, X, old_value, new_value>`: $T_i$ updated data item $X$. `old_value` is used for **Undo** (rollback); `new_value` is used for **Redo** (roll-forward).
- `<T_i, Commit>`: $T_i$ committed.
- `<T_i, Abort>`: $T_i$ aborted.

---

## 3. Database Modification Schemes

The database determines when to write modified data from volatile buffer pools to physical disk using two main strategies:

### 1. Deferred Database Modification (No-Undo/Redo)
- **Concept**: A transaction does not write any modifications to the actual database files on disk until it has committed. All writes are kept in volatile buffers and log files.
- **On Crash**:
  - If $T_i$ has committed before the crash $\implies$ **REDO** $T_i$ (apply new values from the log to disk).
  - If $T_i$ has not committed before the crash $\implies$ **Do Nothing** (no Undo needed because no modifications ever reached the disk).
- **Log content**: Only needs to store `new_value` (no old values required).

### 2. Immediate Database Modification (Undo/Redo)
- **Concept**: Modifications made by a transaction can be written to disk at any time, even before the transaction commits (stealing buffer pages).
- **On Crash**:
  - If $T_i$ has committed before the crash $\implies$ **REDO** $T_i$ (apply new values).
  - If $T_i$ has not committed $\implies$ **UNDO** $T_i$ (apply old values to remove uncommitted changes from disk).
- **Log content**: Must store both `old_value` and `new_value`.

---

## 4. Checkpoints

Without checkpoints, recovering from a crash requires scanning the entire log file from the beginning of time, which is extremely slow and wastes memory.

### Checkpoint Operations
Periodically, the DBMS performs a checkpoint:
1. Suspend execution of all active transactions temporarily.
2. Flush all log records currently in volatile memory to disk.
3. Flush all dirty database pages (modified pages in buffer pool) to disk.
4. Write a `<checkpoint L>` log record to disk, where $L$ is a list of all transactions active at the time of the checkpoint.
5. Resume transaction execution.

### Recovery using Checkpoints
During recovery:
- Scan the log backwards to find the most recent `<checkpoint L>` record.
- Any transaction that committed *before* the checkpoint is safe; its changes are guaranteed to be on disk. No Redo needed.
- Define two sets:
  - **Undo-list**: Transactions active during checkpoint ($L$) or started after checkpoint, but not committed before crash.
  - **Redo-list**: Transactions active during checkpoint ($L$) or started after checkpoint, and committed before crash.

---

## 5. The ARIES Recovery Algorithm

ARIES (Algorithms for Recovery and Isolation Exploiting Semantics) is the standard recovery algorithm used in modern databases. It uses **LSNs** to track page states:
- **PageLSN**: Stored in the header of each database page; records the LSN of the log entry corresponding to the most recent update to that page.
- **FlushedLSN**: The largest LSN flushed to disk so far. Page $P$ can only be written to disk if $\text{PageLSN}(P) \le \text{FlushedLSN}$ (enforces WAL).

```
Crash occurs
     │
     ▼
[ANALYSIS PHASE] ──► Scan forward from last checkpoint to find:
                     - Active transactions (Transaction Table)
                     - Dirty pages (Dirty Page Table)
     │
     ▼
[REDO PHASE]     ──► Scan forward from smallest recLSN in Dirty Page Table.
                     Repeat all logged changes (redo) to restore crash state.
     │
     ▼
[UNDO PHASE]     ──► Scan backward from end of log.
                     Undo all actions of active ("loser") transactions.
```

### The Three Phases of ARIES

#### 1. Analysis Phase
- Starts from the most recent checkpoint log record.
- Scans **forward** to the end of the log.
- Reconstructs:
  - **Transaction Table**: All transactions active at the time of the crash (initialized from checkpoint $L$, updated as new starts/commits/aborts are scanned).
  - **Dirty Page Table (DPT)**: Pages modified in memory but not flushed to disk (stores `recLSN` — the LSN that first dirtied the page).

#### 2. Redo Phase
- Starts from the **smallest `recLSN`** in the Dirty Page Table (the oldest change not yet written to disk).
- Scans **forward** to the end of the log.
- **Repeats History**: Re-applies all modifications (for both committed and aborted transactions) to bring the database back to its exact state at the moment of the crash.
- During this phase, if $\text{PageLSN on disk} \ge \text{LSN of log record}$, the update is skipped (it was already written to disk before the crash).

#### 3. Undo Phase
- Scans **backward** from the end of the log.
- Rolls back all "loser" transactions (transactions active at the time of the crash, still present in the Transaction Table).
- For every undone write, ARIES writes a **CLR (Compensation Log Record)** to the log.
  - CLRs prevent repeating undos if a second crash occurs during recovery (improves idempotency).

---

## 6. Shadow Paging

Shadow paging is an alternative, non-log-based recovery technique.

- **How it works**:
  - The database maintains two page tables during a transaction's lifetime:
    1. **Current Page Table**: Points to current page locations on disk. Used for active transactions.
    2. **Shadow Page Table**: Points to database page locations before the transaction started. Never modified.
  - When a transaction writes to page $i$:
    - The DBMS copies page $i$ to a new physical block on disk (Copy-on-Write).
    - The Current Page Table entry for $i$ is updated to point to the new block.
    - The Shadow Page Table still points to the old block.
  - **Commit**: The DBMS flushes modified pages to disk, then swaps the pointer to make the Current Page Table the new shadow page table.
  - **Abort / Crash**: The Current Page Table is discarded. The database simply points back to the Shadow Page Table.
- **Drawbacks**:
  - **Data Fragmentation**: Pages become scattered across the disk, destroying sequential read performance.
  - **Garbage Collection**: Requires reclaiming old pages.
  - **Overhead**: Swapping large page tables is expensive.
