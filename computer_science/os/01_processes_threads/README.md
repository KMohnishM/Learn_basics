# Module 1: Processes & Threads

---

## 1. Program vs Process vs Thread

A **program** is a passive entity — a file sitting on disk containing executable instructions (ELF on Linux, PE on Windows). It has no state, no execution context, nothing running.

A **process** is a program in execution. The moment the OS loads the program into memory and starts executing it, it becomes a process. A process is the unit of resource ownership — it owns memory, file descriptors, network sockets, and CPU time.

A **thread** is the unit of execution within a process. A process always has at least one thread (the main thread). Multiple threads share the process's address space but each has its own stack, registers, and program counter.

Think of it this way:
- Program = a recipe written on paper
- Process = a chef actually cooking that recipe (with their own workspace, ingredients, tools)
- Thread = multiple chefs sharing the same kitchen, simultaneously working on different parts of the same recipe

---

## 2. Process Memory Layout

When a process is created, the OS sets up its virtual address space with distinct regions:

```
High Address
┌─────────────────────┐
│    Kernel Space     │  ← Not accessible to user programs
├─────────────────────┤
│       Stack         │  ← Grows downward. Local variables, function call frames, return addresses.
│         ↓           │
│     (gap)           │
│         ↑           │
│       Heap          │  ← Grows upward. Dynamic allocation (malloc/new). Managed by runtime.
├─────────────────────┤
│  BSS Segment        │  ← Uninitialized global/static variables (zero-initialized by OS)
├─────────────────────┤
│  Data Segment       │  ← Initialized global/static variables
├─────────────────────┤
│  Text Segment       │  ← Executable code (read-only)
└─────────────────────┘
Low Address
```

**Why this layout matters:**
- Stack overflow = stack grows into heap (or heap into stack). OS detects via guard pages.
- BSS doesn't actually occupy disk space — the OS just knows to zero those pages on load.
- Text segment is read-only and shared between multiple processes running the same program (e.g., 50 bash processes share one copy of bash's text segment).

---

## 3. Process States

A process moves through well-defined states during its lifetime:

```
               admit
  New ──────────────────► Ready ◄─────────── I/O complete / event wait done
                            │                          ▲
                  scheduler │ dispatch                 │
                            ▼                          │
                         Running ─────────────────► Waiting
                            │     I/O or event wait
                            │
                  exit/kill │
                            ▼
                        Terminated
```

**State descriptions:**
- **New**: Process is being created. PCB allocated, but not yet admitted to the ready queue.
- **Ready**: Process is in memory, ready to run, waiting for CPU. Multiple processes can be in this state simultaneously.
- **Running**: Process is currently executing on a CPU. On a single-core system, only one process can be in this state at a time.
- **Waiting (Blocked)**: Process is waiting for an event (I/O completion, mutex, signal). It is NOT using CPU and NOT runnable even if CPU is free.
- **Terminated**: Process has finished execution. PCB still exists until the parent reads the exit status (the zombie period).

**Suspended states** (when swapper/medium-term scheduler is involved):
- **Ready-Suspended**: Process is swapped out to disk but would run if it were in memory.
- **Blocked-Suspended**: Process is both waiting for an event AND swapped out to disk.

---

## 4. Process Control Block (PCB)

The PCB is the OS's data structure representing a process. Every process has exactly one PCB. It contains everything the OS needs to manage, pause, and resume the process.

**PCB fields:**

| Field | Purpose |
|-------|---------|
| **Process ID (PID)** | Unique identifier for the process |
| **Process State** | Current state: new, ready, running, waiting, terminated |
| **Program Counter** | Address of next instruction to execute |
| **CPU Registers** | All register values (general purpose, stack pointer, flags) saved on context switch |
| **CPU Scheduling Info** | Priority, scheduling queue pointers, accumulated CPU time |
| **Memory Management Info** | Base/limit registers, page tables, or segment tables |
| **I/O Status Info** | List of open files, list of I/O devices allocated, pending I/O requests |
| **Accounting Info** | CPU time used, wall clock time, time limits, job/process numbers |
| **Parent PID (PPID)** | PID of the parent process |
| **List of Children** | PIDs of all child processes |
| **Signal Handlers** | Pointers to user-defined signal handling functions |

In Linux, the PCB is implemented as `struct task_struct` in the kernel — it's a massive struct with over 300 fields.

---

## 5. Context Switch — The Exact Sequence

A context switch is the mechanism by which the CPU switches from executing one process to another. It is pure overhead — no useful work happens during a context switch.

**Triggers for context switch:**
1. Timer interrupt fires (time quantum expired in preemptive scheduling)
2. Process calls a blocking system call (I/O request)
3. Process explicitly yields the CPU
4. Higher-priority process becomes ready (preemptive priority scheduling)
5. Process terminates

**The exact sequence:**
1. Hardware saves the current PC and some registers to the kernel stack (interrupt mechanism)
2. OS takes control (ISR / syscall handler)
3. OS saves remaining CPU registers into the current process's PCB
4. OS updates the current process's state (Running → Ready or Waiting)
5. OS runs the scheduler to select the next process
6. OS updates memory management structures (switches page table base register — e.g., CR3 on x86)
7. TLB flush (or ASID switch — see Virtual Memory module) happens if switching address spaces
8. OS loads CPU registers from the new process's PCB
9. OS restores the program counter — execution resumes in the new process

**Cost of context switch:**
- Direct cost: saving/restoring 100+ registers (~microseconds)
- Indirect cost (much larger): TLB flush means all subsequent memory accesses are cache misses until the TLB is refilled. A cold TLB can cost thousands of extra memory accesses.

---

## 6. Process Creation — `fork()` Internals

On Unix/Linux, every process except `init` (PID 1) is created with `fork()`.

```c
pid_t pid = fork();
if (pid == 0) {
    // This code runs in the CHILD process
    // fork() returns 0 to the child
} else if (pid > 0) {
    // This code runs in the PARENT process
    // fork() returns the child's PID to the parent
} else {
    // fork() returned -1 — error (e.g., process limit reached)
}
```

**What `fork()` does internally:**
1. Allocates a new PCB for the child
2. Assigns a new PID
3. **Copies** the parent's address space — but NOT literally immediately
4. **Copy-on-Write (COW)**: the child and parent initially share the same physical pages. The MMU marks these pages as read-only. When either process tries to write to a page, a page fault occurs, the OS makes a private copy of that page for the writing process, and marks it writable. Most `fork()` calls are immediately followed by `exec()`, so this copying never actually happens — massive optimization.
5. Copies the parent's file descriptor table (both parent and child can read/write the same open files)
6. Copies signal handlers, signal mask, etc.
7. Child is placed in the ready queue

**`exec()` family**: replaces the current process's address space with a new program. After `exec()`, the process has completely new text, data, heap, and stack. PID remains the same. Open file descriptors remain open (unless FD_CLOEXEC is set).

The typical `fork()` → `exec()` pattern (used by shells):
```c
pid_t pid = fork();
if (pid == 0) {
    execvp("ls", args);   // Replace child with 'ls' program
    // execvp only returns on error
}
// Parent continues here, can wait() for the child
```

---

## 7. Process Termination

**Normal exit**: Process calls `exit()` (C) or `return` from `main()`. The runtime calls `exit()` which flushes stdio buffers and calls `_exit()` syscall.

**What happens on process exit:**
1. All open file descriptors are closed
2. Memory is freed (page tables deallocated, physical frames returned to free list)
3. Children are reparented to `init`/`systemd` (PID 1)
4. Process enters **Terminated** state
5. A signal (SIGCHLD) is sent to the parent
6. PCB remains in memory — the process is now a **zombie**

---

## 8. Zombie and Orphan Processes

### Zombie Process
When a process terminates, it cannot fully clean up itself — its parent needs to read its exit status. Until the parent calls `wait()` or `waitpid()`, the dead process remains in the process table as a **zombie**:
- All memory freed, all file descriptors closed
- Only the PCB entry remains (just the exit status and PID)
- `ps` shows it as `Z` or `<defunct>`

**Why zombies are a problem**: each zombie consumes a process table entry. If a server creates children and never waits for them, it can exhaust the process table (PID exhaustion), preventing any new processes from being created.

**Fix**: Parent must call `wait()` / `waitpid()` to reap zombies. A common pattern is handling `SIGCHLD` to call `waitpid()` non-blockingly for any completed children.

### Orphan Process
When a parent terminates before its children, the children become **orphans**. The OS automatically reparents all orphans to `init` (PID 1). `init` periodically calls `wait()` so it continuously reaps any orphans that terminate — no zombie accumulation.

---

## 9. Threads

### Why Threads?

Creating a new process with `fork()` is expensive:
- Copy (even with COW) of address space
- Full PCB allocation
- Separate memory space means communication requires IPC (pipes, sockets, shared memory)
- Context switching between processes flushes TLB

Threads within the same process share:
- Address space (code, data, heap)
- Open files
- Signals and signal handlers
- User ID, group ID

Each thread has its own:
- Thread ID (TID)
- Program counter
- Register set
- Stack (for local variables and function call frames)

Thread creation is ~10–100x cheaper than process creation.

### User-Level Threads (ULT)

Managed entirely in user space by a thread library (e.g., GNU Pth). The kernel sees only one process.

**Advantages:**
- Thread creation/switching is extremely fast (no kernel involvement, no syscall)
- Portable — works on any OS
- Thread scheduling can be application-specific

**Disadvantages:**
- **If one thread makes a blocking system call, ALL threads in the process block** — the kernel blocks the whole process since it doesn't know about the individual threads.
- Cannot exploit multiple CPUs — the kernel only schedules the process, not individual threads, so all threads run on one core.

### Kernel-Level Threads (KLT)

The kernel knows about each thread. Thread creation/switching involves a syscall.

**Advantages:**
- A blocking call by one thread doesn't block other threads — kernel schedules them independently.
- True parallelism on multicore systems — different threads can run on different cores simultaneously.

**Disadvantages:**
- Thread creation and context switching are slower (require kernel mode transitions)

Modern systems (Linux, Windows) use KLTs. POSIX Pthreads on Linux are implemented as KLTs via `clone()` syscall.

### Threading Models

**Many-to-One**: Many user threads → one kernel thread. 
- Problem: No parallelism, blocking call blocks all. Rarely used.

**One-to-One**: Each user thread → one kernel thread. 
- Used by Linux (Pthreads), Windows. True parallelism. Slight overhead of kernel thread creation.

**Many-to-Many**: M user threads → N kernel threads (N ≤ M). 
- Best of both. Complex to implement. Used by older Solaris.

**Two-Level Model**: Many-to-Many but allows binding certain user threads to specific kernel threads for critical tasks. Even more complex.

---

## 10. Inter-Process Communication (IPC)

Processes have separate address spaces by design (for isolation). When they need to communicate, the OS provides IPC mechanisms:

### Shared Memory
A region of memory is mapped into the address spaces of two or more processes. Reads and writes to this region are visible to all sharing processes.

- **Fastest IPC**: no kernel involvement after setup, data transfer at memory speed
- **Problem**: requires explicit synchronization (otherwise race conditions)
- Setup: `shmget()` + `shmat()` on POSIX; `mmap()` with `MAP_SHARED`

### Message Passing (Pipes, Sockets, Message Queues)
Processes exchange data through kernel-managed buffers. Sender writes a message, receiver reads it.

- Simpler to use (no synchronization needed for the channel itself)
- Slower than shared memory (data copied to kernel, then copied to receiver)

**Unnamed Pipes**:
```c
int fd[2];
pipe(fd);   // fd[0] = read end, fd[1] = write end
// Works only between related processes (parent-child)
// Unidirectional
// Implemented as a circular buffer in kernel memory (typically 64KB on Linux)
```

**Named Pipes (FIFOs)**: appear as files in the filesystem, can be used between unrelated processes. Still unidirectional.

**Sockets**: bidirectional, work across machines. TCP sockets (stream), UDP sockets (datagram), Unix domain sockets (local, faster than TCP, used by Docker/PostgreSQL).

**Message Queues (POSIX)**: named queues, messages have types/priorities, persist after sender exits.

### Signals
Asynchronous notification sent to a process. The process's signal handler is invoked when the signal arrives. Limited information capacity (just a signal number, no data payload). Used for: process control (SIGKILL, SIGTERM), error notification (SIGSEGV, SIGFPE), child state change (SIGCHLD).

### Comparison Table

| Mechanism | Speed | Direction | Cross-machine? | Synchronization needed? |
|-----------|-------|-----------|----------------|------------------------|
| Shared Memory | Fastest | N/A | No | Yes (manually) |
| Unnamed Pipe | Fast | Unidirectional | No | No (blocking read/write) |
| Named Pipe | Fast | Unidirectional | No | No |
| Message Queue | Medium | Both | No | No |
| Unix Socket | Fast | Bidirectional | No | No |
| TCP Socket | Medium | Bidirectional | Yes | No |
| Signal | N/A | One-way | No | No |

---

## 11. `wait()` and `waitpid()`

```c
pid_t wait(int *status);       // Waits for ANY child to terminate
pid_t waitpid(pid_t pid, int *status, int options);  // Waits for specific child
```

- `WNOHANG` option: don't block, return 0 immediately if no child has exited yet (non-blocking reaping)
- `WEXITSTATUS(status)`: macro to extract the exit code from the status value
- `WIFSIGNALED(status)`: true if child was killed by a signal
- Returns the PID of the reaped child (or 0 with WNOHANG if none exited)

Every process that terminates must be waited on (reaped). No exceptions if you want to avoid zombies.
