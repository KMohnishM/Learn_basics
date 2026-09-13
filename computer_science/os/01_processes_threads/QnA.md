# Q&A — Processes & Threads

---

## 🟢 Easy

**Q1. What is the difference between a program and a process?**

A program is a passive entity — a file on disk containing instructions. A process is an active entity — a program currently being executed by the CPU, with its own memory space, CPU state, and OS resources (file descriptors, etc.). The same program can have multiple processes running simultaneously (e.g., 10 terminal windows each running `bash`).

---

**Q2. List the states a process can be in and describe each.**

- **New**: Being created, not yet in the ready queue.
- **Ready**: In memory, waiting for CPU time.
- **Running**: Currently executing on a CPU.
- **Waiting (Blocked)**: Waiting for an event (I/O, lock, signal) — not runnable even if CPU is free.
- **Terminated**: Finished execution; PCB still exists until parent reaps it.

Additional suspended states exist when a process is swapped to disk: Ready-Suspended and Blocked-Suspended.

---

**Q3. What is a PCB and what does it contain?**

A **Process Control Block** is the kernel data structure representing a process. It contains: PID, process state, program counter, CPU register values (saved on context switch), scheduling info (priority, CPU time used), memory management info (page table pointer), I/O status (open files, pending I/O), accounting info, and parent/child PID references.

In Linux, the PCB is `struct task_struct`.

---

**Q4. What is a zombie process? Is it a problem?**

A zombie process is a process that has terminated but whose PCB still exists because its parent hasn't called `wait()` yet. The zombie has no memory, no open files — just an entry in the process table holding the exit status.

Yes, it's a problem if a server creates many children without waiting for them. Each zombie consumes a process table slot. If the process table fills up (PID exhaustion), no new processes can be created.

**Fix**: The parent should call `wait()` or handle `SIGCHLD` to reap children.

---

**Q5. What is an orphan process? What happens to it?**

An orphan is a process whose parent has terminated before it. The OS automatically reparents orphans to `init` (PID 1). `init` continuously calls `wait()`, so orphans that terminate are properly reaped — no zombies accumulate.

---

**Q6. What are the advantages of threads over processes?**

- **Shared memory**: Threads share the same address space, so communication is via shared variables (no IPC overhead).
- **Cheaper creation**: Thread creation is ~10-100x faster than `fork()` — no address space copy.
- **Cheaper context switching**: Switching between threads of the same process doesn't require changing the memory mapping (no TLB flush).
- **Responsiveness**: One thread can block on I/O while others continue running.

---

**Q7. What does each thread own exclusively, and what does it share with other threads in the same process?**

**Owns exclusively**: Program counter, register set, stack (local variables, function call frames), thread ID.

**Shares with other threads**: Text segment (code), data segment, heap, open file descriptors, signal handlers, user/group IDs.

---

**Q8. What is the return value of `fork()`?**

- Returns **0** to the child process.
- Returns the **child's PID** (a positive integer) to the parent process.
- Returns **-1** on failure (e.g., maximum process limit reached).

---

## 🟡 Medium

**Q9. What is Copy-on-Write (COW) in the context of `fork()`? Why is it important?**

Without COW, `fork()` would copy the entire parent address space to the child — potentially gigabytes of data — even if the child immediately calls `exec()`.

With COW, `fork()` gives the child a copy of the parent's **page table** but marks all pages as read-only and shared. No physical pages are copied. When either process writes to a shared page, a **page fault** occurs. The OS then makes a private copy of just that one page for the writing process, and marks it writable.

This means:
- If the child immediately calls `exec()`, nearly no pages are ever copied (huge win).
- Only pages that are actually written ever get copied (minimal overhead otherwise).

---

**Q10. Explain the difference between user-level threads and kernel-level threads. When does each approach cause problems?**

**User-level threads (ULT)**: Managed by a runtime library in user space. The kernel sees only one process.
- Problem: If one thread makes a blocking syscall (e.g., `read()`), the kernel blocks the entire process, so ALL threads block. Also, ULTs cannot run in true parallel on multiple cores — the kernel schedules the process as a unit.

**Kernel-level threads (KLT)**: Each thread is known to the kernel and scheduled independently.
- Problem: Thread creation/context switching require syscalls — slower than ULT. But this is the accepted trade-off in modern systems (Linux, Windows).

---

**Q11. What is a context switch? Why is it expensive?**

A context switch is saving the state of the currently running process into its PCB and restoring the state of the next process from its PCB. 

**Direct cost**: saving/restoring ~100+ registers, updating kernel data structures (~1-10 microseconds).

**Indirect cost (often larger)**: switching to a different process flushes the TLB (Translation Lookaside Buffer). The new process starts with a cold TLB, causing page table walks for every memory access until the TLB is refilled. This can cause thousands of extra memory accesses and is usually the dominant cost.

---

**Q12. Describe the exact steps in a `fork()` call.**

1. Allocate a new PCB for the child.
2. Assign a new unique PID.
3. Copy the parent's page table (not physical pages — COW).
4. Mark all shared pages as read-only in both parent and child's page tables.
5. Copy the parent's file descriptor table.
6. Copy signal handlers, signal mask, CPU registers, program counter.
7. Place the child in the ready queue.
8. `fork()` returns 0 to the child and the child's PID to the parent.

---

**Q13. What are the different IPC mechanisms? When would you choose each?**

| Mechanism | Choose When |
|-----------|-------------|
| **Shared Memory** | High-throughput data transfer between related processes on the same machine (e.g., video processing pipeline). Requires explicit synchronization. |
| **Pipe** | Simple unidirectional data flow between parent-child processes (shell pipelines). |
| **Named Pipe (FIFO)** | Unidirectional data flow between unrelated processes on the same machine. |
| **Unix Socket** | Bidirectional, high-performance local IPC (PostgreSQL, Docker use these). |
| **TCP Socket** | When processes need to communicate across machines, or when you want standard network protocols. |
| **Message Queue** | When messages have different types/priorities, or sender and receiver run at different rates. |
| **Signal** | Asynchronous notification only (not data transfer). Process control (kill, pause, resume). |

---

**Q14. What is the Many-to-Many threading model and what problem does it solve?**

The Many-to-Many model maps M user-level threads to N kernel-level threads (where N ≤ M). The thread library can schedule user threads across the kernel threads.

It solves:
- The blocking problem of Many-to-One: if one kernel thread blocks, others can still run.
- The overhead problem of One-to-One: not every user thread needs a kernel thread (expensive to create N kernel threads for N user threads when N is large).

Drawback: Very complex to implement correctly. Modern systems prefer One-to-One (Linux Pthreads) because kernel threads have become cheap enough.

---

**Q15. What happens to a process's children when the process exits?**

The children become **orphans**. The OS automatically reparents all orphan processes to `init` (PID 1). `init` is designed to continuously call `wait()`, so orphans that terminate will be properly reaped without becoming zombies.

---

## 🔴 Hard

**Q16. A server process creates 1000 child processes to handle requests but never calls `wait()`. What happens over time and how would you fix it?**

Each child, when it finishes handling its request and exits, becomes a **zombie** — its PCB remains in the process table waiting for the parent to collect its exit status. With 1000 zombies, the process table may fill up (typical Linux limit is ~32,768 PIDs via `/proc/sys/kernel/pid_max`). When exhausted, no new processes can be created anywhere on the system — not just by this server, but by any program. Even `ps`, `ls`, `ssh` would fail.

**Fix options:**
1. **Install a `SIGCHLD` handler**: When a child exits, the kernel sends `SIGCHLD` to the parent. In the handler, call `waitpid(-1, NULL, WNOHANG)` in a loop to reap all available children without blocking.
2. **Explicitly call `wait()` in a separate thread**: A dedicated thread blocks on `waitpid(-1, ...)` and reaps each child as it exits.
3. **Double fork (detach the child)**: Parent forks a child, child forks a grandchild (which does the work), child immediately exits. Grandchild is adopted by `init`. Parent only needs to wait for the child (quick exit). Grandchild is reaped by `init`.

---

**Q17. Explain exactly what happens at the hardware and OS level when a context switch is triggered by a timer interrupt.**

1. **Hardware (CPU)**: Timer fires an interrupt. CPU finishes the current instruction, then:
   - Switches to kernel mode (ring 0 on x86)
   - Saves the user-space PC, stack pointer, and flags register onto the **kernel stack** of the current process
   - Jumps to the Interrupt Service Routine (ISR) via the interrupt vector table

2. **OS (timer ISR)**: 
   - Saves all remaining CPU registers (general-purpose registers) into the current process's PCB
   - Increments the process's accumulated CPU time counter
   - Decrements the time quantum counter; if expired, marks the process for preemption

3. **OS (scheduler)**:
   - Changes the current process's state from Running → Ready (puts it back in ready queue)
   - Runs the scheduling algorithm to pick the next process
   - Changes the next process's state from Ready → Running

4. **OS (context restore)**:
   - If switching address spaces: updates CR3 (page table base register on x86) to the new process's page table
   - Flushes the TLB (or switches ASID if hardware supports it to avoid full flush)
   - Loads all CPU registers from the next process's PCB
   - Returns from the ISR: restores the saved PC and flags, switches back to user mode
   - Execution resumes in the new process exactly where it left off

---

**Q18. Why can't two threads in the same process have the same stack? What would happen?**

Each function call creates a **stack frame** containing: local variables, the return address, saved registers. If two threads shared a stack, their function call frames would intermix — Thread A's local variable `int x = 5` might occupy the same memory as Thread B's `int x = 10`. When either thread modifies `x`, it would corrupt the other thread's local state. The return addresses would be overwritten, causing both threads to return to wrong locations after function calls — instant, unpredictable crashes.

Each thread must have its own stack so its function call history is private and independent.

---

**Q19. What is the difference between `exit()` and `_exit()` in Unix?**

`exit()` is a C library function that:
1. Calls all functions registered with `atexit()` (cleanup handlers)
2. Flushes all open stdio buffers (writes buffered output to the underlying file descriptors)
3. Closes all stdio streams
4. Then calls `_exit()`

`_exit()` (or `_Exit()`) is the actual system call:
1. Does NOT flush stdio buffers
2. Does NOT call atexit handlers
3. Immediately terminates the process

**When does this matter?** After `fork()`, if you call `exit()` in the child (before `exec()`), it may flush buffers that the parent has also inherited — leading to duplicate output. The correct practice in the child is to call `_exit()` to avoid this.

---

**Q20. On a single-core machine, multiple threads in a process exist. Is there any speedup from using threads? Explain.**

Yes, there is a speedup, but only for **I/O-bound workloads**, not CPU-bound workloads.

On a single core, only one thread can run at a time. For CPU-bound work (pure computation), threading adds overhead (context switching) without any benefit — a single-threaded program would be faster.

However, if Thread A makes a blocking I/O call (e.g., reading a file), the kernel can schedule Thread B to run while Thread A is blocked. This **overlaps computation with I/O** — the total wall-clock time decreases even on a single core.

Example: A web server that needs to (1) read a file from disk and (2) process a database query. Single-threaded: sequential, total time = file_read + db_query. Multi-threaded: both happen in parallel (one blocks, other runs), total time ≈ max(file_read, db_query).
