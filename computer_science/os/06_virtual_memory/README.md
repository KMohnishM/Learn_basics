# Module 6: Virtual Memory

---

## 1. Why Virtual Memory?

Until now, we've assumed the entire process must be in RAM to run. Virtual memory breaks this assumption: **a process can run even if only part of it is in memory**.

This enables:
- **Programs larger than physical RAM**: A 10GB program runs on a machine with 8GB RAM.
- **More processes**: Each process occupies less RAM (only its active pages), so more processes fit.
- **Fast startup**: Only the first few pages (containing `main()`) need to be loaded. The rest loads on demand.
- **Efficient fork()**: With copy-on-write, fork() creates a child instantly (no copy until write).

The mechanism: a page marked as "not present" (valid bit = 0 in PTE) is actually on disk. When the process tries to access it, a **page fault** occurs, and the OS brings the page from disk.

---

## 2. Demand Paging

**Demand paging** means: load a page into RAM only when it is accessed. Never load it proactively.

The OS maintains a **lazy loader**: at process start, NO pages are in RAM. The first instruction immediately causes a page fault. The OS handles it, loads the page, returns. This continues page by page as new code is executed or new data is accessed.

**Benefit**: If a program never executes an error handling branch that occupies 10MB of code, those 10MB never touch RAM.

---

## 3. Page Fault — The Complete Sequence

When the CPU accesses a virtual address whose page table entry has **valid bit = 0**:

1. **Hardware**: CPU detects invalid PTE, raises a **page fault trap** (interrupt), saves the faulting instruction's address.
2. **OS (trap handler)**: Saves the process's state.
3. **Check**: Is the logical address valid (within the process's virtual address space)?
   - **No** (bad pointer, null dereference): Terminate the process with a segmentation fault (SIGSEGV).
   - **Yes** (page is just not in memory): Continue below.
4. **Find a free frame**: If one is available, use it. If RAM is full, run the **page replacement algorithm** to evict a victim frame.
5. **Schedule disk I/O**: Read the required page from the swap device/swap file into the chosen frame. The process is put to sleep (state → Waiting).
6. **CPU schedules other processes** while the I/O runs (disk I/O takes milliseconds — thousands of CPU cycles).
7. **I/O completes (interrupt)**: Update the PTE (set frame number, set valid bit = 1). Move the process back to Ready queue.
8. **Restart the faulting instruction**: The instruction that caused the page fault is re-executed from the beginning. This time, the page is in RAM → success.

**Restart requirement**: The OS must be able to restart any instruction after a page fault. This is why the CPU saves the faulting instruction's address (not the next instruction). Some architectures (pre-RISC) make this hard — e.g., if an instruction partially modifies multiple memory locations before faulting, the OS must undo those partial modifications before restarting.

---

## 4. Copy-on-Write (COW)

When `fork()` creates a child, it's wasteful to copy the entire parent's address space — the child often immediately calls `exec()` to replace itself anyway.

**COW mechanism**:
1. At `fork()`: child gets a copy of the parent's page table, but both parent and child share the same physical frames. All shared frames are marked read-only in both page tables.
2. When either process tries to **write** to a shared page: page fault! The OS detects it's a COW page.
3. The OS makes a **private copy** of that frame for the writing process, marks the copy as writable for that process.
4. The other process still sees the original (unmodified) frame.

**Result**: fork() completes in microseconds regardless of process size. Pages are copied lazily, only when actually written. For `fork()` + `exec()`, essentially no pages are ever copied.

---

## 5. Page Replacement — When Frames Are Full

When a page fault occurs and there are no free frames, the OS must **evict** a page from RAM to disk (swap it out) to make room.

**Modified page (dirty bit = 1)**: Must be written to disk before the frame can be reused. Expensive (disk write).

**Clean page (dirty bit = 0)**: It's an unchanged copy of disk data. The frame can be reused immediately — the disk already has the correct copy. No write needed.

**The page replacement algorithm** chooses which page to evict.

---

## 6. Page Replacement Algorithms

### FIFO (First-In, First-Out)

Replace the page that has been in memory the longest.

Implementation: Queue. New page → back of queue. Evict from front.

**Example** (3 frames, reference string: 7 0 1 2 0 3 0 4 2 3 0 3 2 1 2 0 1 7 0 1):
- Count page faults (from textbook): **15 page faults**

**Belady's Anomaly**: Adding more frames can INCREASE the number of page faults with FIFO. This is counterintuitive and unique to FIFO (other algorithms don't have this property).

Example: Reference string 1 2 3 4 1 2 5 1 2 3 4 5
- 3 frames: 9 page faults
- 4 frames: 10 page faults (worse!)

**Why**: FIFO doesn't consider usage patterns — it blindly evicts the oldest page, which might be the most frequently used.

### Optimal (OPT / MIN)

Replace the page that will **not be used for the longest time in the future**.

This is theoretically optimal — gives the minimum possible page fault rate. Proof: Any other choice would evict a page that's needed sooner than OPT's choice, causing an earlier page fault.

**Problem**: Requires knowledge of future page references. **Impossible to implement in practice**. Used as a benchmark to compare other algorithms.

### LRU (Least Recently Used)

Replace the page that **has not been used for the longest time in the past**.

**Rationale (Principle of Locality)**: Programs tend to access the same pages repeatedly. If a page hasn't been used recently, it's unlikely to be needed soon (locality of reference).

LRU approximates OPT using past behavior as a predictor of future behavior. In practice, LRU performs close to OPT.

**Implementation options:**

**Counter-based**: Each PTE has a timestamp counter. Updated on every access. Evict the page with the smallest counter (least recently used). Problem: requires updating a timestamp on EVERY memory access → huge overhead (needs hardware support for efficient implementation).

**Stack-based**: Maintain a stack of page numbers. On access, move the page to the top. Evict the page at the bottom (bottom = LRU). Implementation: doubly-linked list + hash map for O(1) access. Still expensive to update on every access.

**Cost**: True LRU is expensive to implement efficiently in hardware. Both approaches require updating data structures on every memory reference. This is why LRU approximations are used instead.

### LRU Approximations — Reference Bit Algorithm

Hardware provides a **reference bit** in each PTE:
- Set to 1 by hardware whenever the page is accessed (read or write)
- Cleared periodically by the OS

The OS can use this to approximate LRU without the full cost:

**Second-Chance Algorithm (Clock Algorithm)**:
- Arrange frames in a circular queue (like a clock face)
- Clock hand points to the "oldest" frame
- To find a victim:
  - If page's reference bit = 0: Evict it. ✓
  - If page's reference bit = 1: Clear the bit, advance the clock hand (give it a "second chance")
  - Repeat until a page with reference bit = 0 is found

This approximates LRU without expensive per-access overhead. Degenerates to FIFO if all reference bits are 1 (all pages recently used, cycle through all before finding victim).

**Enhanced Second-Chance Algorithm** — uses both reference bit (R) and dirty bit (D):

| (R, D) | Class | Preference for eviction |
|--------|-------|------------------------|
| (0, 0) | Not recently used, not dirty | Best victim (no write needed) |
| (0, 1) | Not recently used, dirty | Need write but not recent |
| (1, 0) | Recently used, clean | Don't evict if avoidable |
| (1, 1) | Recently used, dirty | Worst victim (write + recently needed) |

Scan for lowest class first.

### Counting Algorithms

**LFU (Least Frequently Used)**: Evict the page with the smallest access count. Problem: Pages used heavily early and then abandoned have high counts and won't be evicted. Fix: Shift counts right periodically (decay).

**MFU (Most Frequently Used)**: Evict the page with the highest access count. Rationale: Most-used page might be "done." Rarely performs well in practice.

---

## 7. Frame Allocation

How many frames does each process get?

**Equal Allocation**: Give each of n processes m/n frames (where m = total frames). Simple but ignores that different processes have vastly different working sets.

**Proportional Allocation**: Give each process frames proportional to its size:
```
frames_i = (size_i / total_size) × m
```

**Priority-based**: Higher priority processes get more frames (similar to scheduling priority).

### Global vs Local Replacement

**Global replacement**: A process can steal frames from ANY other process. A page fault in process A can evict a page from process B.
- Pro: More flexible, better overall throughput.
- Con: A process's performance depends on other processes' behavior (unpredictable).

**Local replacement**: A process can only replace from its own allocated frames.
- Pro: Predictable performance for each process.
- Con: May not utilize free frames efficiently — process A might have free frames while process B is thrashing.

Most OS implementations use global replacement (Linux uses this via LRU-based page frame reclaim).

### Minimum Frames Requirement

Why must each process have a minimum number of frames? Because an instruction must be restartable after a page fault, and an instruction might reference multiple pages:

- The instruction itself might span 2 pages (if code crosses a page boundary)
- The instruction's operands might be on 1-2 other pages
- For complex instructions (x86 block moves `MOVS`), 6 or more pages might be needed simultaneously

If a process has fewer frames than the minimum, every instruction will fault → infinite loop of page faults → the process makes zero progress.

---

## 8. Thrashing

**Thrashing** occurs when a process (or the whole system) spends more time paging (handling page faults, waiting for disk I/O) than executing.

**How it happens:**
1. OS adds more processes to increase CPU utilization (multiprogramming degree increases).
2. Each process gets fewer frames (fixed total RAM).
3. Page faults increase dramatically.
4. Processes spend most of their time waiting for disk.
5. CPU utilization drops (processes are blocked waiting for pages).
6. OS misinterprets low CPU utilization as "need more processes" → adds more → worse thrashing.

**The characteristic**: CPU utilization vs. multiprogramming degree curve has a cliff — it rises, peaks, then drops sharply when thrashing begins.

### Working Set Model

The **working set** of a process is the set of pages it is actively using in a given time window Δ (the working set window — measured in page references).

```
WSS_i = |W(t_i, Δ)|   (number of distinct pages in window Δ)
```

If the total demand exceeds available frames:
```
Σ WSS_i > m  →  Thrashing inevitable
```

**OS action**: Monitor WSS for each process. If total WS exceeds available frames, **suspend** the process with the largest WSS (swap it out entirely). This frees frames for the remaining processes and eliminates thrashing.

### Page Fault Frequency (PFF) Control

More practical than working set:
- Measure each process's page fault frequency.
- If a process's fault rate > upper threshold → give it more frames.
- If a process's fault rate < lower threshold → reclaim some of its frames.
- If a process needs more frames and none are available → suspend a process.

---

## 9. Memory-Mapped Files

`mmap()` maps a file (or portion of a file) directly into a process's virtual address space.

```c
void *ptr = mmap(NULL, length, PROT_READ|PROT_WRITE, MAP_SHARED, fd, offset);
// Now read/write memory at ptr — directly reading/writing the file!
```

**How it works**: The file's pages are added to the page table. When the process reads from `ptr`, if the page isn't loaded, a page fault loads it from the file (not swap). When the process writes to `ptr`, the page is marked dirty; on unmap or msync, dirty pages are written back to the file.

**Benefits**:
- Read/write a large file without reading it all into memory at once.
- Share a file between processes using `MAP_SHARED`: changes by one process are visible to others (same physical pages).
- Faster than `read()/write()`: avoids copying between kernel buffer and user buffer.

**Shared Libraries** work exactly via mmap: the `.so` file is mmapped into each process's address space.

---

## 10. Kernel Memory Allocation

The kernel itself needs memory for its own data structures (PCBs, page tables, buffers). This is separate from user-process memory management.

### Buddy System

Allocate memory in powers of 2:
- A request for 35 bytes → round up to 64 bytes (2^6).
- Memory divided into blocks of size 2^0, 2^1, 2^2, ..., 2^n.
- To allocate 2^k: find a free 2^k block. If none, split a free 2^(k+1) block into two buddies.
- To free 2^k: if its buddy is also free, merge them back into 2^(k+1).

**Example**: Request 35 bytes from 256KB pool:
- Need 2^6=64 bytes. Split 256KB → 128KB + 128KB. Split one 128KB → 64KB + 64KB. Use one 64KB... actually split down to 64B.
- 256KB → 128KB | 128KB → 128KB | 64KB | 64KB → 128KB | 64KB | 32B allocated block

**Internal fragmentation**: A request for 33 bytes wastes 31 bytes (allocated 64).

**External fragmentation**: None — buddies always merge correctly.

**Fast coalescing**: Checking if a buddy is free requires only XOR of the block address (the buddy address differs by exactly one bit at position k).

### Slab Allocator

The Buddy System still has internal fragmentation for frequently-allocated kernel objects (PCBs, inodes, mutexes — all fixed size).

**Slab allocator** solution:
- A **cache** is created for each type of kernel object (e.g., "inode cache").
- Each cache consists of one or more **slabs** (contiguous pages).
- Each slab contains pre-allocated, pre-initialized objects of that type.
- Allocating an object: mark one as "used" and return it.
- Freeing an object: mark it as "free" (object stays in the slab, pre-initialized for next use).

**Advantages:**
- **No fragmentation**: Objects are exactly the right size.
- **Fast allocation/deallocation**: No size calculation, no splitting.
- **Object reuse**: Freed objects are already initialized. For complex kernel objects (with many initialized fields), this avoids re-initialization on every allocation.

Linux uses the SLAB allocator (and its successors SLUB and SLOB) for all kernel object allocation.
