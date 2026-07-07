# Cheat Sheet — Memory Management

## Address Translation
```
Logical Address → [MMU] → Physical Address

Simple MMU:
  Physical = Logical + Base Register
  Guard: if Logical >= Limit → Segmentation Fault

Paging MMU:
  Split Logical Address: [Page Number p | Offset d]
  Physical = PageTable[p] × PageSize + d
```

## Address Space Layout (32-bit)
```
High ┌─────────────────┐
     │   Kernel Space  │ (1GB)
     ├─────────────────┤  ← 0xC0000000
     │ Stack (↓)       │
     │      ...        │
     │ Heap (↑)        │
     ├─────────────────┤
     │ BSS             │ (uninitialized globals)
     ├─────────────────┤
     │ Data            │ (initialized globals)
     ├─────────────────┤
Low  │ Text (code)     │
     └─────────────────┘
```

## Page Table Entry Fields
| Field | Purpose |
|-------|---------|
| Frame Number | Physical frame (upper bits) |
| Valid bit | 0 = not in memory → page fault |
| Dirty bit | 1 = modified → must write to disk on eviction |
| Reference bit | 1 = recently accessed (used by replacement) |
| Protection | R/W/X permissions |
| Caching Disabled | For memory-mapped device registers |

## TLB — Effective Access Time
```
EAT = h(t_tlb + t_mem) + (1-h)(t_tlb + 2×t_mem)

h = hit ratio, t_tlb = TLB time, t_mem = memory time

Example: h=0.95, t_tlb=10ns, t_mem=80ns
EAT = 0.95×90 + 0.05×170 = 85.5 + 8.5 = 94ns
```

## Hit Ratio → EAT (t_tlb=10, t_mem=80)
| Hit Ratio | EAT | Overhead |
|-----------|-----|---------|
| 0.80 | 98ns | 22.5% |
| 0.90 | 94ns | 17.5% |
| 0.95 | 94ns | 17.5% |
| 0.99 | 90.8ns | 13.5% |

## Fragmentation Types
| | Internal | External |
|-|----------|----------|
| **Where** | Inside allocated block | Between allocated blocks |
| **Cause** | Block larger than needed | Non-contiguous holes |
| **Affects** | Fixed partitions, paging | Variable partitions, segmentation |
| **Fix** | Smaller page size | Paging or compaction |

## Two-Level Page Table (32-bit, 4KB pages)
```
Logical: [10 bits outer | 10 bits inner | 12 bits offset]

Level 1 (Page Directory):  1024 entries × 4B = 4KB (1 frame)
Level 2 (Page Tables):     1024 entries × 4B = 4KB each
                           Created only for used regions

Flat table: 1M × 4B = 4MB contiguous — too big!
Two-level: 4KB + (only needed inner tables) — much smaller
```

## Page Size Trade-offs
| Smaller Pages | Larger Pages |
|--------------|-------------|
| Less internal fragmentation | More internal fragmentation |
| More page table entries | Fewer page table entries |
| Smaller working set | Better I/O efficiency |
| More page faults | Fewer page faults |
| Standard: 4KB | Large page: 2MB, 1GB (huge pages) |

## Hole Allocation Strategies
| Algorithm | Speed | Fragmentation |
|-----------|-------|---------------|
| First Fit | Fast | Moderate |
| Best Fit | Slow (full scan) | Many tiny fragments |
| Worst Fit | Slow | Poor (wastes large holes) |
| **Winner** | First Fit usually best | — |

## Page Table Types Comparison
| Type | Memory Cost | Lookup Speed | Sharing | Used By |
|------|------------|-------------|---------|---------|
| Flat | O(virtual pages) | O(1) | Easy | Small address spaces |
| 2-level | O(used virtual) | O(1) | Easy | x86 32-bit |
| 4-level | O(used virtual) | O(1) | Easy | x86-64 (Linux) |
| Inverted | O(physical frames) | O(1) avg (hash) | Hard | IBM POWER |
| Hashed | O(used virtual) | O(1) avg | Moderate | Sparse 64-bit |

## Key Numbers
```
Typical page size:     4KB (also 2MB, 1GB huge pages)
TLB entries:          64–1024
TLB access time:      ~10–20ns
Memory access time:   ~80–100ns
Typical TLB hit rate: 90–99%
32-bit page table:    4MB flat (2-level used instead)
64-bit levels:        4 or 5 (Linux x86-64: 4-level PGD→PUD→PMD→PTE)
```

## Address Binding Types
| When | Type | Flexible? | Needs |
|------|------|-----------|-------|
| At compilation | Compile-time | ❌ (fixed location) | Fixed load address |
| At loading | Load-time | Partial | Relocatable binary |
| At execution | Runtime | ✅ | MMU hardware |
