# Operating Systems — Complete Interview Curriculum

A deeply technical, interview-focused OS curriculum. Every topic that appears in software engineering interviews — from FAANG to product companies — is covered at textbook depth. No surface-level summaries. Each module explains the internal mechanics, the "why", and the edge cases interviewers probe.

---

## Who This Is For

- Engineers preparing for software engineering interviews (SDE-1 to SDE-3 level)
- CS students who want to go beyond memorizing definitions
- Backend and systems engineers who want to understand what's happening under the hood

---

## Module Structure

Every module has exactly **three files**:

```
module/
├── README.md       ← Full textbook-depth internals. Read this first.
│                     Explains WHY, not just WHAT.
├── QnA.md          ← Tiered interview Q&A
│                     🟢 Easy | 🟡 Medium | 🔴 Hard (includes numericals)
└── CHEATSHEET.md   ← One-page quick reference: formulas, tables, key numbers
```

---

## Curriculum Map

| # | Module | Core Topics | Numericals? |
|---|--------|-------------|-------------|
| [M1](./01_processes_threads/) | **Processes & Threads** | PCB, process states, fork/exec, COW, IPC mechanisms, ULT vs KLT, threading models | ❌ |
| [M2](./02_cpu_scheduling/) | **CPU Scheduling** | FCFS, SJF, SRTF, RR, Priority, MLFQ, Linux CFS, real-time (EDF/RMS), multiprocessor | ✅ Gantt charts, avg WT, RMS bounds |
| [M3](./03_synchronization/) | **Process Synchronization** | Race conditions, critical section, Peterson's, mutex, semaphores, monitors, Dining Philosophers, priority inversion | ❌ |
| [M4](./04_deadlocks/) | **Deadlocks** | Coffman conditions, RAG, prevention, Banker's algorithm, detection, recovery, livelock | ✅ Banker's algorithm |
| [M5](./05_memory_management/) | **Memory Management** | Logical/physical addresses, MMU, paging, TLB, multi-level page tables, segmentation, EAT | ✅ EAT, address translation, page table size |
| [M6](./06_virtual_memory/) | **Virtual Memory** | Demand paging, page fault sequence, COW, FIFO/LRU/OPT/Clock, Belady's anomaly, thrashing, working set, slab allocator | ✅ Page fault EAT, fault counting |
| [M7](./07_file_systems/) | **File Systems** | Inodes, allocation methods, free space, VFS, journaling, hard vs soft links, max file size | ✅ Max file size, bitmap size |
| [M8](./08_io_disk_scheduling/) | **I/O & Disk Scheduling** | Polling/interrupts/DMA, disk structure, FCFS/SSTF/SCAN/C-SCAN/LOOK, RAID levels | ✅ Head movement, rotational latency, RAID capacity |

---

## Suggested Study Order

### Week 1 — Process Fundamentals
**Day 1–2**: M1 — Processes & Threads (foundation for everything else)
**Day 3–4**: M2 — CPU Scheduling (practice 3–4 Gantt chart problems)
**Day 5–7**: M3 — Synchronization (master the classic problems — they come up constantly)

### Week 2 — Memory
**Day 1–2**: M4 — Deadlocks (do the Banker's algorithm worked examples)
**Day 3–5**: M5 — Memory Management (TLB EAT calculations are common in interviews)
**Day 6–7**: M6 — Virtual Memory (page replacement algorithms + thrashing)

### Week 3 — Storage
**Day 1–3**: M7 — File Systems (inode structure + allocation methods)
**Day 4–5**: M8 — I/O & Disk Scheduling (disk scheduling algorithms + RAID)
**Day 6–7**: Review CHEATSHEETs for all modules, practice random QnA

---

## Most Commonly Asked Interview Topics

### Almost Certain to Appear
- Process vs Thread (M1)
- Context switch — what exactly happens (M1)
- Mutex vs Semaphore (M3)
- Deadlock conditions + prevention (M4)
- Virtual memory + page fault (M6)

### Very Likely
- CPU scheduling: FCFS vs SJF vs RR trade-offs (M2)
- Producer-Consumer solution with semaphores (M3)
- Paging + TLB mechanism (M5)
- Hard link vs symbolic link (M7)
- RAID 0 vs 1 vs 5 vs 10 (M8)

### For Senior / Systems Roles
- Linux CFS (vruntime, red-black tree) (M2)
- Priority Inversion + Mars Pathfinder example (M3)
- Banker's Algorithm full walkthrough (M4)
- Belady's Anomaly proof (M6)
- Working Set Model + thrashing prevention (M6)
- Journaling filesystem crash recovery (M7)
- DMA coherence problem (M8)

---

## Key Numbers to Have Memorized

| Fact | Value |
|------|-------|
| Typical context switch cost | 1–10 μs |
| TLB size | 64–1024 entries |
| TLB hit ratio (typical) | 90–99% |
| Memory access time | ~100ns |
| Page size (standard) | 4KB |
| HDD random access | 7–15ms |
| SSD (NVMe) random access | 0.02–0.1ms |
| 7200 RPM rotational latency | 4.17ms avg |
| Max file size (traditional inode) | ~4TB |
| RAID 5 write I/O penalty | 4 I/Os per write |
| Linux default scheduler | CFS (since 2.6.23) |
| Linux PID limit | ~32,768 (configurable) |
| Page fault service time (HDD) | ~10ms |

---

## Prerequisites

No code required — this is a theory curriculum. You should know:
- Basic data structures (queues, linked lists, trees)
- Basic algorithm complexity (O notation)
- Familiarity with at least one programming language (for understanding code examples)
