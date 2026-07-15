# Q&A — Recovery Systems

---

## 🟢 Easy

**Q1. What is the Write-Ahead Logging (WAL) protocol? Why is it critical?**

The WAL protocol states that:
1. Any modification to a database page must be recorded in a log file on disk **before** the modified page itself is written to disk.
2. A transaction is not considered committed until its `COMMIT` log record has been flushed to non-volatile disk.

**Why critical**:
- If a system crashes after a dirty page is written to disk but before the log record is written, we cannot undo the change (violates Atomicity).
- If we commit a transaction without flushing its logs, and the power fails, the changes are lost (violates Durability).

---

**Q2. What is a checkpoint? Why does the database perform checkpoints?**

A checkpoint is an operation where the DBMS flushes all volatile log records and dirty memory buffer pages to disk.
- **Why performed**: Without checkpoints, recovering from a crash requires scanning the entire log file from the beginning of time. This takes too long and requires keeping massive tables in memory. With checkpoints, the database guarantees that all updates prior to the checkpoint are safely on disk. Recovery only needs to scan back to the most recent checkpoint.

---

**Q3. What is shadow paging? What are its primary drawbacks?**

Shadow paging is a non-log-based recovery technique.
- **How it works**: The database maintains two page tables: a Current Page Table and a Shadow Page Table. Writes are done to new physical blocks (Copy-on-Write). On commit, the shadow pointer is updated to point to the current table. On abort/crash, the current table is discarded, and the shadow table is restored.
- **Drawbacks**:
  - **Fragmentation**: Data pages are scattered across the disk, causing sequential read performance to degrade.
  - **Garbage Collection**: Requires a mechanism to identify and free orphaned pages.
  - **Large table overhead**: Copying and swapping large page tables is CPU and memory intensive.

---

## 🟡 Medium

**Q4. Compare Deferred Database Modification and Immediate Database Modification.**

- **Deferred Database Modification (No-Undo/Redo)**:
  - Updates are only written to the log during transaction execution. Physical database files are modified *only after* the transaction commits.
  - **On Crash**: No Undo is needed (since uncommitted changes never reached disk). We only need to **Redo** committed transactions.
  - Log records only require new values.
- **Immediate Database Modification (Undo/Redo)**:
  - Updates can be written to disk at any time, even before the transaction commits.
  - **On Crash**: We must **Undo** uncommitted transactions (rollback using old values from the log) and **Redo** committed transactions (using new values).
  - Log records must store both old and new values.

---

**Q5. Describe the three phases of the ARIES recovery algorithm.**

1. **Analysis Phase**:
   - Scans the log **forward** starting from the last checkpoint.
   - Reconstructs the Transaction Table (identifies active transactions at the time of the crash) and the Dirty Page Table (identifies pages in memory that were modified but not flushed).
2. **Redo Phase**:
   - Scans **forward** from the oldest `recLSN` (oldest change not flushed to disk) in the Dirty Page Table.
   - Replays all logged changes (repeats history) to restore the database to the exact state it was in at the moment of the crash.
3. **Undo Phase**:
   - Scans **backward** from the end of the log.
   - Rolls back (undos) the changes made by all transactions that were active at the time of the crash (the "loser" transactions). Writes Compensation Log Records (CLRs) for each undone write.

---

## 🔴 Hard

**Q6. A database crash occurs. The log file contains the following sequential entries:**
1. `<T1 start>`
2. `<T1, A, 10, 20>`
3. `<T2 start>`
4. `<T2, B, 100, 200>`
5. `<T1 commit>`
6. `<checkpoint {T2}>`
7. `<T3 start>`
8. `<T3, C, 50, 60>`
9. `<T2 commit>`
10. `<T4 start>`
11. `<T4, D, 5, 8>`
*System crashes here.*

**For an Immediate Modification (Undo/Redo) scheme, determine:**
1. **The transactions active at the time of the checkpoint.**
2. **The Redo-list (transactions to be redone).**
3. **The Undo-list (transactions to be undone).**
4. **The exact recovery actions taken by the database engine.**

#### Step-by-step analysis:

1. **Transactions active at the time of the checkpoint**:
   - Looking at the checkpoint record: `<checkpoint {T2}>`.
   - **Answer**: Only **$T_2$** was active.

2. **Determine the Redo-list**:
   - The Redo-list contains transactions that committed either before the crash but after the checkpoint, or were active during the checkpoint and committed later.
   - $T_1$ committed before the checkpoint (at entry 5). Because it committed before the checkpoint, its changes are guaranteed to be flushed to disk by the checkpoint operation. We do not need to redo $T_1$.
   - $T_2$ was active at checkpoint and committed at entry 9 (before the crash).
   - $T_3$ started at entry 7 and has no commit record.
   - $T_4$ started at entry 10 and has no commit record.
   - **Answer**: The Redo-list is **$\{T_2\}$**.

3. **Determine the Undo-list**:
   - The Undo-list contains transactions that were active at the time of the crash (started but not committed).
   - $T_3$ started (entry 7) but never committed.
   - $T_4$ started (entry 10) but never committed.
   - **Answer**: The Undo-list is **$\{T_3, T_4\}$**.

4. **Exact recovery actions taken**:
   - **Step 1 (Redo Phase)**:
     - Scan the log forward from the checkpoint (entry 6) to the end of the log.
     - For any transaction in the Redo-list, re-apply its updates.
     - Action: Redo $T_2$ by setting $B = 200$ (using the new value from entry 4, or scan forward to find $T_2$'s writes).
   - **Step 2 (Undo Phase)**:
     - Scan the log backward from the end of the log to the checkpoint.
     - For any transaction in the Undo-list, roll back its updates using the old values.
     - Action: Undo $T_4$ write $\implies$ set $D = 5$ (old value from entry 11).
     - Action: Undo $T_3$ write $\implies$ set $C = 50$ (old value from entry 8).
     - Write `<T4 abort>` and `<T3 abort>` records to the log.
