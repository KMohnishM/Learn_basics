# Cheat Sheet — Processes & Threads

## Process States
```
New → Ready ←── I/O done / event occurs
        ↓
     Running ──→ Waiting (blocked on I/O / lock / signal)
        ↓
    Terminated
```

## PCB Key Fields
| Field | Description |
|-------|-------------|
| PID / PPID | Process and Parent Process ID |
| State | new / ready / running / waiting / terminated |
| PC | Next instruction address |
| Registers | All CPU registers (saved on context switch) |
| Page Table Ptr | Points to process's page table |
| Open Files | File descriptor table |
| Priority | Scheduling priority |

## fork() Return Values
| Returned To | Value |
|-------------|-------|
| Child | 0 |
| Parent | Child's PID (positive) |
| On error | -1 |

## Process Memory Layout (Low → High)
```
Text | Data | BSS | Heap ↑ ... ↓ Stack | Kernel
```
- **Text**: code (read-only, shared across processes)
- **BSS**: uninitialized globals (zero-filled, no disk space)
- **Heap**: grows upward (malloc/new)
- **Stack**: grows downward (local vars, return addresses)

## Thread: Own vs Shared
| Owns Privately | Shares with Process |
|----------------|---------------------|
| Stack | Heap |
| Registers | Data (globals) |
| Program Counter | Text (code) |
| Thread ID | Open file descriptors |
| Signal mask | Signal handlers |

## Threading Models
| Model | User Threads | Kernel Threads | Blocking problem? | Parallelism? |
|-------|-------------|----------------|-------------------|-------------|
| Many-to-One | M | 1 | Yes | No |
| One-to-One | 1 | 1 | No | Yes |
| Many-to-Many | M | N (N≤M) | Partial | Yes |

## IPC Mechanisms Quick Compare
| Mechanism | Speed | Direction | Cross-machine |
|-----------|-------|-----------|---------------|
| Shared Memory | ⚡ Fastest | — | ❌ |
| Pipe | Fast | One-way | ❌ |
| Named Pipe | Fast | One-way | ❌ |
| Unix Socket | Fast | Two-way | ❌ |
| TCP Socket | Medium | Two-way | ✅ |
| Signal | N/A | One-way | ❌ |

## Key Numbers to Remember
- Typical context switch direct cost: **1–10 μs**
- Typical process table limit on Linux: **~32,768 PIDs** (`/proc/sys/kernel/pid_max`)
- Thread stack default size (Linux): **8 MB** per thread
- `fork()` without `exec()` → COW means no actual copy until write
- Zombie: has **no memory**, **no open files** — just a PCB slot

## Zombie vs Orphan
| | Zombie | Orphan |
|-|--------|--------|
| **Who exited?** | Child | Parent |
| **PCB exists?** | Yes | Yes |
| **Memory exists?** | No | Yes |
| **Reparented?** | No | Yes (→ init) |
| **Fix** | Parent calls wait() | init reaps automatically |

## Key Syscalls
```
fork()        — create child (returns 0 to child, child PID to parent)
exec()        — replace process image with new program
wait()        — block until any child exits, reap it
waitpid(pid)  — block until specific child exits, reap it
exit()        — flush stdio + atexit + _exit()
_exit()       — immediately terminate (no flush — use in child after fork)
getpid()      — get own PID
getppid()     — get parent PID
```
