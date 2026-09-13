# Q&A — Virtual Memory

---

## 🟢 Easy

**Q1. What is the difference between demand paging and pre-paging?**

**Demand paging**: Pages are loaded into memory only when accessed. A page fault occurs, and the OS loads the page from disk on demand. Lazy loading — minimal upfront cost, slight latency on first access.

**Pre-paging**: The OS predicts which pages a process will need and loads them before they're faulted on. Reduces page faults at the cost of potentially loading pages that were never needed. Used in some OS implementations at process startup (load the pages from the previous run based on history) and by read-ahead for sequential I/O.

---

**Q2. What is thrashing?**

Thrashing is when processes spend more time paging (waiting for disk I/O to bring pages in/out) than executing. CPU utilization drops dramatically because all processes are blocked waiting for pages, not running.

Cause: Too many processes competing for too little RAM. Each process's working set doesn't fit in its allocated frames.

Fix: Reduce the degree of multiprogramming (suspend some processes, giving remaining processes enough frames).

---

**Q3. What is the Optimal page replacement algorithm? Why is it impractical?**

The Optimal algorithm replaces the page that will not be used for the longest time in the future. This minimizes page faults — no other algorithm can do better.

Impractical because it requires knowing the future — the OS cannot know which pages will be accessed next. It's used as a theoretical benchmark to evaluate real algorithms.

---

**Q4. What happens during a page fault?**

1. CPU detects invalid PTE (valid bit = 0), raises a trap.
2. OS checks if the address is a valid virtual address (if not → SIGSEGV, terminate process).
3. OS finds a free frame (or evicts a victim if full).
4. OS reads the required page from disk into the frame.
5. OS updates the PTE (frame number, valid bit = 1).
6. OS puts the process back in the ready queue.
7. The faulting instruction is restarted.

---

**Q5. What is Belady's Anomaly?**

Belady's Anomaly: Adding more physical frames to a process can sometimes INCREASE the number of page faults. This counterintuitive behavior is specific to FIFO page replacement.

Example: Reference string `1 2 3 4 1 2 5 1 2 3 4 5`:
- With 3 frames: 9 page faults
- With 4 frames: 10 page faults (more faults with more memory!)

LRU and OPT are "stack algorithms" — they don't exhibit Belady's Anomaly. Adding frames never increases faults for stack algorithms.

---

## 🟡 Medium

**Q6. Given the reference string 7,0,1,2,0,3,0,4,2,3,0,3,2,1,2,0,1,7,0,1 with 3 frames. Count page faults using FIFO and LRU.**

**FIFO (3 frames):**

| Ref | Frames | Fault? |
|-----|--------|--------|
| 7 | 7 - - | ✓ |
| 0 | 7 0 - | ✓ |
| 1 | 7 0 1 | ✓ |
| 2 | 2 0 1 | ✓ (evict 7) |
| 0 | 2 0 1 | ✗ |
| 3 | 2 3 1 | ✓ (evict 0) |
| 0 | 2 3 0 | ✓ (evict 1) |
| 4 | 4 3 0 | ✓ (evict 2) |
| 2 | 4 2 0 | ✓ (evict 3) |
| 3 | 4 2 3 | ✓ (evict 0) |
| 0 | 0 2 3 | ✓ (evict 4) |
| 3 | 0 2 3 | ✗ |
| 2 | 0 2 3 | ✗ |
| 1 | 1 2 3 | ✓ (evict 0) |
| 2 | 1 2 3 | ✗ |
| 0 | 1 0 3 | ✓ (evict 2) |
| 1 | 1 0 3 | ✗ |
| 7 | 7 0 3 | ✓ (evict 1) |
| 0 | 7 0 3 | ✗ |
| 1 | 7 1 3 | ✓ (evict 0) |

**FIFO: 15 page faults**

**LRU** gives 12 page faults for the same string (keep the most recently used; evict the one not used longest).

---

**Q7. Explain the Clock (Second-Chance) algorithm. How does it differ from FIFO?**

Clock algorithm is an LRU approximation that uses the hardware reference bit.

Frames are arranged in a circular queue. A clock hand sweeps through:
- Page with reference bit = 0 → **evict** it.
- Page with reference bit = 1 → **clear** the bit (give it a "second chance"), advance the hand.

**Difference from FIFO**:
- FIFO always evicts the oldest page in the queue, regardless of recent usage.
- Clock gives recently-used pages a second chance — clears their reference bit and skips them. Only pages that haven't been accessed since the last clock sweep are evicted.
- Clock approximates LRU (recently accessed pages survive at least one sweep), while FIFO doesn't consider usage.
- Clock never exhibits Belady's Anomaly (it's a stack algorithm approximation).

---

**Q8. What is the Working Set model? How does it prevent thrashing?**

The Working Set W(t, Δ) of a process at time t is the set of distinct pages accessed in the last Δ page references (the working set window).

A process needs at least |WSS_i| frames to avoid thrashing (all its active pages in memory simultaneously).

**Preventing thrashing**:
The OS monitors WSS for each process. It computes:
```
D = Σ WSS_i   (total demand for frames)
```
If D > m (available frames): **suspend** the process with the largest WSS. This frees frames for the rest.
If D < m: can admit a new process.

The goal: ensure every admitted process has enough frames for its working set. This keeps page fault rates low and prevents thrashing.

---

**Q9. Calculate the effective access time given: page fault rate p=0.001, page fault service time=10ms, memory access time=100ns.**

```
EAT = (1-p) × t_mem + p × t_fault
    = (1-0.001) × 100ns + 0.001 × 10ms
    = 0.999 × 100ns + 0.001 × 10,000,000ns
    = 99.9ns + 10,000ns
    = 10,099.9ns ≈ 10.1μs

Slowdown = 10.1μs / 0.1μs = 101× slower!
```

Even a tiny 0.1% page fault rate causes 100× slowdown! Keeping page fault rates below 0.00001 (1 in 100,000) is essential for acceptable performance.

If we need EAT ≤ 200ns (2× memory access time):
```
200 = (1-p)×100 + p×10,000,000
200 = 100 - 100p + 10,000,000p
100 = 9,999,900p
p ≤ 0.00001 (1 in 100,000 accesses)
```

---

## 🔴 Hard

**Q10. A reference string is 1,2,3,4,1,2,5,1,2,3,4,5. Count faults with FIFO for 3 and 4 frames to demonstrate Belady's anomaly.**

**3 frames (FIFO):**

| Ref | Frames (oldest→newest) | Fault? |
|-----|----------------------|--------|
| 1 | 1 - - | ✓ |
| 2 | 1 2 - | ✓ |
| 3 | 1 2 3 | ✓ |
| 4 | 4 2 3 | ✓ (evict 1) |
| 1 | 4 1 3 | ✓ (evict 2) |
| 2 | 4 1 2 | ✓ (evict 3) |
| 5 | 5 1 2 | ✓ (evict 4) |
| 1 | 5 1 2 | ✗ |
| 2 | 5 1 2 | ✗ |
| 3 | 3 1 2 | ✓ (evict 5) |
| 4 | 3 4 2 | ✓ (evict 1) |
| 5 | 3 4 5 | ✓ (evict 2) |

**3 frames: 9 page faults**

**4 frames (FIFO):**

| Ref | Frames | Fault? |
|-----|--------|--------|
| 1 | 1 - - - | ✓ |
| 2 | 1 2 - - | ✓ |
| 3 | 1 2 3 - | ✓ |
| 4 | 1 2 3 4 | ✓ |
| 1 | 1 2 3 4 | ✗ |
| 2 | 1 2 3 4 | ✗ |
| 5 | 5 2 3 4 | ✓ (evict 1) |
| 1 | 5 1 3 4 | ✓ (evict 2) |
| 2 | 5 1 2 4 | ✓ (evict 3) |
| 3 | 5 1 2 3 | ✓ (evict 4) |
| 4 | 4 1 2 3 | ✓ (evict 5) |
| 5 | 4 5 2 3 | ✓ (evict 1) |

**4 frames: 10 page faults — MORE than 3 frames!** ← Belady's Anomaly confirmed.

---

**Q11. Explain the Slab Allocator. Why is it better than the Buddy System for kernel object allocation?**

**Problem with Buddy System for kernel objects**: The kernel frequently allocates and frees objects like `struct inode` (say, 512 bytes). With Buddy, each allocation rounds up to 512 bytes (happens to be power of 2 here). But every allocation/deallocation: find a free block, split if needed, mark used, zero-initialize the struct. On free: mark unused, possibly coalesce. And for kernel objects with complex initialization (locks, embedded linked lists, reference counts), the object must be re-initialized on every allocation. This is expensive — up to hundreds of store operations.

**Slab Allocator**:
1. At kernel initialization: create a "cache" for `struct inode`. Pre-allocate a slab of memory (e.g., 8 pages = 32KB). Carve it into `struct inode`-sized slots. Pre-initialize ALL slots (call the constructor).
2. Allocate: Find a cache with a free slot. Return the slot pointer (already initialized). O(1), no initialization cost.
3. Free: Mark slot as free. Object stays in the slab (destructor NOT called — the initialization is preserved for next use). O(1).

**Why better**:
- **Zero fragmentation**: Slots are exactly the right size.
- **No initialization cost on each allocation**: Objects are pre-initialized; only variable fields need updating.
- **Cache-friendly**: Objects of the same type are contiguous in memory → hot in CPU cache.
- **Fast**: O(1) allocation and deallocation.

Linux's SLUB allocator (successor to SLAB) is the default in the Linux kernel.

---

**Q12. Can a process fault on the same page twice in a row? Under what conditions?**

Yes, in global replacement where another process can steal frames:

1. Process A faults on page P, OS loads it into frame F (page P now in memory).
2. Process A continues. Another process B faults and runs the page replacement algorithm globally — it selects frame F (page P) as the victim, writes P to disk (if dirty), gives frame F to process B.
3. Process A needs page P again → faults AGAIN on the same page.

In local replacement, this can't happen: process A can only lose its own frames, and the OS won't immediately re-evict a freshly loaded page (most algorithms give newly loaded pages high priority via reference bit).

In global replacement with aggressive other processes (thrashing), this pattern of re-faulting is exactly what happens: pages are evicted faster than they can be used.
