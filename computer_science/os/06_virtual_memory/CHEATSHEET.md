# Cheat Sheet — Virtual Memory

## Page Fault Complete Sequence
```
CPU hits invalid PTE (valid bit = 0)
  ↓
OS checks: valid virtual address?
  No → SIGSEGV (terminate)
  Yes → Find free frame (or evict victim)
  ↓
Disk I/O: read page into frame (process sleeps)
  ↓
Update PTE (frame number, set valid=1)
  ↓
Process → Ready queue
  ↓
RESTART faulting instruction (not next instruction!)
```

## EAT with Page Faults
```
EAT = (1-p) × t_mem + p × t_fault

p = page fault rate
t_mem = memory access time (~100ns)
t_fault = page fault service time (~10ms = 10,000,000ns)

Rule of thumb: even p=0.001 → 100× slowdown!
For EAT ≤ 2×t_mem:  p must be < 1 in 100,000 (0.001%)
```

## Page Replacement Algorithms
| Algorithm | Optimal? | Belady's Anomaly? | Implementation | Notes |
|-----------|----------|:-----------------:|---------------|-------|
| **OPT** | ✅ Best | ❌ | Impossible | Benchmark only |
| **LRU** | Near-optimal | ❌ (stack algo) | Counter/Stack | Expensive |
| **FIFO** | ❌ | ✅ Possible | Simple queue | Convoy problem |
| **Clock** | Approximates LRU | ❌ | Circular + ref bit | Used in Linux |
| **LFU** | ❌ | ❌ | Counter | Stale data issue |

## Clock (Second-Chance) Algorithm
```
Frames in circular queue, clock hand sweeps:

  ref bit = 0 → EVICT this page
  ref bit = 1 → Clear bit, advance (give second chance)
  
Keep sweeping until ref bit = 0 found.
```

## Enhanced Second-Chance Classes
| (R, D) | Meaning | Eviction priority |
|--------|---------|-----------------|
| (0, 0) | Not recent, clean | **Best** — evict first |
| (0, 1) | Not recent, dirty | Need write, but ok |
| (1, 0) | Recent, clean | Avoid |
| (1, 1) | Recent, dirty | **Worst** — evict last |

## Frame Allocation
```
Equal:        each process gets m/n frames (m total, n processes)
Proportional: frames_i = (size_i / Σsize) × m
Priority:     more frames to higher priority processes

Global replacement: process can steal from others (better throughput)
Local replacement:  process limited to own frames (predictable)
```

## Thrashing
```
Cause: Σ WSS_i > m (total demand > available frames)
  → All processes blocked waiting for pages
  → CPU utilization → 0

Fix:
  1. Suspend process with largest WSS → free frames
  2. Page Fault Frequency control:
     fault_rate > upper_threshold → give more frames
     fault_rate < lower_threshold → take frames back
```

## Working Set Model
```
W(t, Δ) = pages accessed in window of Δ references before t
WSS_i   = |W(t_i, Δ)|

If Σ WSS_i > m → thrashing → suspend a process
If Σ WSS_i < m → can admit new process
```

## Copy-on-Write (COW)
```
fork() → child shares all parent frames (marked read-only)
Write to shared frame → page fault → OS copies that frame
     → writing process gets private copy, marked writable
     → other process keeps original

Result: fork() is O(1) regardless of process size
Pages are copied only when actually written
```

## Buddy System
```
Allocate in powers of 2:
  Request n bytes → allocate 2^⌈log₂(n)⌉ bytes

Split:   2^k block → two 2^(k-1) buddies
Merge:   free 2^k + its free buddy → 2^(k+1)

Advantage: fast coalescing (buddy address = address XOR 2^k)
Problem: internal fragmentation (33 bytes → 64 bytes allocated)
```

## Slab Allocator vs Buddy System
| | Buddy System | Slab Allocator |
|-|-------------|----------------|
| Fragmentation | Internal only | None |
| Allocation speed | O(log n) | O(1) |
| Initialization | Every time | Once (at cache creation) |
| Best for | Variable-size allocations | Fixed-size kernel objects |
| Linux default | For large allocations | SLUB (default kernel) |

## Key Numbers
```
Typical swap space:  2× RAM (or more)
Page fault service:  ~10ms (disk) or ~100μs (SSD)
Acceptable fault rate: < 1 in 100,000 accesses (for 2× EAT)
Working set window: varies, typically last 10,000-100,000 refs
mmap threshold: glibc uses mmap for allocations > 128KB
```

## Belady's Anomaly — Quick Test
```
Only FIFO can exhibit Belady's Anomaly
Stack algorithms (LRU, OPT) NEVER exhibit it

Proof idea: stack algorithms have the "inclusion property"
  Pages in n frames ⊆ pages in n+1 frames (always)
  → Adding a frame never causes a miss that wouldn't have happened
```
