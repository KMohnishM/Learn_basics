# Q&A — I/O Systems & Disk Scheduling

---

## 🟢 Easy

**Q1. What are the three methods of I/O? When is each used?**

1. **Polling (Programmed I/O)**: CPU loops continuously checking the device's status register. Simple, no interrupt hardware needed. Only acceptable for very fast devices where wait time is nanoseconds. Wastes CPU on slow devices.

2. **Interrupt-driven I/O**: CPU issues command, then runs other processes. Device raises a hardware interrupt when done. CPU jumps to ISR to handle completion. Good for slow devices — CPU is productive while waiting. Overhead of interrupt handling per transfer.

3. **DMA (Direct Memory Access)**: A DMA controller moves data directly between device and RAM without CPU involvement per byte. CPU sets up the transfer, then is free. DMA raises ONE interrupt when the entire transfer is complete. Best for large transfers (disk blocks, network packets).

---

**Q2. What is DMA and why is it important?**

DMA (Direct Memory Access) is a hardware mechanism that transfers data directly between a device and main memory, bypassing the CPU for the actual data movement.

Importance: Without DMA, reading a 64KB disk block with interrupt-driven I/O would generate 65,536 interrupts (one per byte) or 1,024 interrupts (one per 64-byte line). With DMA: exactly 1 interrupt. This frees the CPU to do useful work and dramatically reduces interrupt overhead for I/O-intensive workloads.

---

**Q3. What is seek time? What is rotational latency? Which dominates disk access time?**

**Seek time**: Time to move the read/write head to the correct track (cylinder). Average 3–10ms on modern HDDs.

**Rotational latency**: Time for the desired sector to rotate under the head. Average = half a rotation. For 7200 RPM: `60,000ms/7200/2 = 4.17ms`.

Both are significant. Together they make HDD random access 7–15ms. **Seek time typically dominates** for random workloads, which is why disk scheduling algorithms focus on minimizing head movement.

Transfer time (reading the actual bits) is usually < 0.5ms for a single sector — negligible compared to seek + rotational latency.

---

**Q4. What is RAID 5? How does it recover from a disk failure?**

RAID 5 stripes data across N disks with **distributed parity** — for every stripe, one disk holds the XOR of all data blocks in that stripe, and parity is rotated across disks so no single disk is the bottleneck.

**Recovery**: When a disk fails, the controller XORs all blocks from the remaining N-1 disks. Since `D0 ⊕ D1 ⊕ D2 ⊕ Parity = 0`, the missing block = XOR of all others. As a new disk is inserted, the controller reads all other disks and writes the reconstructed data to the new disk (the "rebuild" process — takes hours for large arrays).

---

**Q5. What is the difference between SCAN and C-SCAN disk scheduling?**

**SCAN (Elevator)**: Head sweeps back and forth. Moves to the highest request, reverses, sweeps back to the lowest. Services requests in both directions.

**C-SCAN (Circular SCAN)**: Head moves in ONE direction only (e.g., low → high). After reaching the last request, it jumps back to the lowest cylinder without servicing on the return. Starts the next sweep.

**Advantage of C-SCAN**: More uniform wait times. With SCAN, a cylinder just behind the head in the direction it came from waits up to a full sweep. With C-SCAN, maximum wait is one full sweep in the same direction, regardless of position.

---

## 🟡 Medium

**Q6. Given this pending disk request queue: 98, 183, 37, 122, 14, 124, 65, 67. Head at cylinder 53, moving upward. Calculate total head movement for FCFS, SSTF, and SCAN.**

**FCFS** (in arrival order): 53→98→183→37→122→14→124→65→67
```
|53-98|+|98-183|+|183-37|+|37-122|+|122-14|+|14-124|+|124-65|+|65-67|
= 45+85+146+85+108+110+59+2 = 640 cylinders
```

**SSTF** (nearest first from 53): 53→65→67→37→14→98→122→124→183
```
12+2+30+23+84+24+2+59 = 236 cylinders
```

**SCAN** (upward first, then reverse): 53→65→67→98→122→124→183→37→14
```
Upward: 183-53=130
Downward: 183-14=169
Total: 130+169 = 299 cylinders
```

SSTF wins on total movement, but may starve requests at extremes.

---

**Q7. Calculate the average rotational latency for a disk spinning at 5400 RPM and 10000 RPM.**

Average rotational latency = time for half a rotation.

**5400 RPM**:
- One rotation = 60,000ms / 5400 = 11.11ms
- Average latency = 11.11 / 2 = **5.56ms**

**10,000 RPM**:
- One rotation = 60,000ms / 10,000 = 6ms
- Average latency = 6 / 2 = **3ms**

**Total average random access time** (seek ≈ 7ms for both):
- 5400 RPM: 7 + 5.56 ≈ **12.56ms**
- 10,000 RPM: 7 + 3 ≈ **10ms**

Higher RPM meaningfully reduces latency, but seek time dominates, limiting the benefit.

---

**Q8. Why does RAID 5 have a "write penalty"? Quantify it.**

A RAID 5 write requires updating not just the data block but also the parity block. The parity update requires knowing the OLD data value (to XOR out the old contribution and XOR in the new).

**For a single block write:**
1. Read old data block
2. Read old parity block
3. Compute new parity: `new_parity = old_parity XOR old_data XOR new_data`
4. Write new data block
5. Write new parity block

= **4 I/O operations** for every 1 logical write operation. This is the RAID 5 write penalty.

For write-intensive workloads (databases, logging), RAID 5's write penalty can be severe. This is why write-intensive systems often prefer **RAID 10** (no parity computation — just mirror the write to 2 disks = 2 I/O operations per write).

---

**Q9. What is the difference between blocking I/O, non-blocking I/O, and asynchronous I/O? Which is most efficient for a high-performance web server?**

**Blocking I/O**: Thread issues `read()` and is suspended until data arrives. Thread cannot do anything else. N simultaneous connections require N threads.

**Non-blocking I/O**: `read()` returns immediately with EAGAIN if no data. Thread must repeatedly poll (busy-wait) or use `select()`/`poll()` to check many file descriptors. Thread can handle multiple connections, but frequent syscalls add overhead.

**Asynchronous I/O** (AIO / io_uring): Thread submits I/O request and continues. Kernel notifies the thread (via completion queue, signal, or callback) when I/O completes. Zero blocking, zero polling overhead.

**For a high-performance web server**: Asynchronous I/O with an event loop (like nginx's design) is most efficient. One or a few threads handle thousands of connections by reacting to I/O completion events. `io_uring` (Linux 5.1+) is the state of the art — submits and collects completions via shared ring buffers, minimizing syscall overhead further.

---

## 🔴 Hard

**Q10. A disk has 200 cylinders (0-199). Request queue: 55, 58, 39, 18, 90, 160, 150, 38, 184. Head at cylinder 50, moving toward higher cylinders. Calculate total head movement for LOOK and C-LOOK.**

**Sort requests**: 18, 38, 39, 55, 58, 90, 150, 160, 184. Head at 50, moving up.

**LOOK** (go up to last request 184, then come back down to 18):
- Upward: 50 → 55 → 58 → 90 → 150 → 160 → 184 (move = 184-50 = 134)
- Reverse: 184 → 39 → 38 → 18 (move = 184-18 = 166)
- **Total = 134 + 166 = 300 cylinders**

**C-LOOK** (go up to 184, jump to 18, then up to 39):
- Upward: 50 → 55 → 58 → 90 → 150 → 160 → 184 (move = 134)
- Jump: 184 → 18 (no service, jump = 166, but doesn't count as head movement in same direction)

Actually, let's be precise. C-LOOK counts all head movement including the jump:
- 50→55→58→90→150→160→184 = 134
- Jump 184→18 = 166 (head does move, but services no requests)
- 18→38→39 = 21
- **Total = 134 + 166 + 21 = 321 cylinders**

LOOK (300) < C-LOOK (321) in total movement, but C-LOOK provides more uniform wait times.

---

**Q11. You have 4 disks of 2TB each. Compare usable capacity and fault tolerance for RAID 0, 1, 5, 6, and 10.**

| RAID | Usable Capacity | Fault Tolerance |
|------|----------------|-----------------|
| **RAID 0** | 4 × 2TB = **8TB** | None — 1 disk failure = total loss |
| **RAID 1** | 2 × 2TB = **4TB** (pairs mirrored) | 1 disk per mirrored pair |
| **RAID 5** | 3 × 2TB = **6TB** (4 disks - 1 parity) | 1 disk failure |
| **RAID 6** | 2 × 2TB = **4TB** (4 disks - 2 parity) | 2 disk failures simultaneously |
| **RAID 10** | 2 × 2TB = **4TB** (50% mirrors) | 1 per mirrored pair (up to 2 total) |

**Observations:**
- RAID 5 gives the best capacity-to-redundancy trade-off for 4 disks: 6TB usable with fault tolerance.
- RAID 6 sacrifices another 2TB for the ability to survive 2 simultaneous failures — important for large arrays where rebuild time is long (increasing probability of a second failure during rebuild).
- RAID 10 has the same capacity as RAID 6 but better write performance (no parity compute penalty).

**Decision guide:**
- Max capacity, no concern for data: RAID 0
- Most important data, money not an issue: RAID 10
- Balance of capacity and safety: RAID 5 (small arrays) or RAID 6 (large arrays)
- Critical database, highest performance: RAID 10

---

**Q12. Explain the DMA cache coherence problem and how it is solved.**

**The problem**: Modern CPUs cache data in L1/L2/L3 caches for fast access. The cache holds copies of recently-accessed memory. When a DMA controller writes data directly to physical RAM (bypassing the CPU), the CPU's cache still holds the OLD data. If the CPU then reads from that address, it gets the stale cached value, not the DMA-written new value. This is a **cache incoherence** — cache and RAM disagree.

**Solutions:**

1. **Cache-coherent DMA (bus snooping)**: The DMA bus transactions are visible to the cache coherence protocol. When the DMAC writes to RAM, the cache controller sees the write on the bus and invalidates (or updates) any cache line covering that address. Hardware-transparent, requires cache-coherent interconnect (CCIX, CXL on modern PCIe).

2. **Software cache management (explicit invalidation)**: Before starting DMA, the OS explicitly invalidates cache lines covering the DMA target region (`cache_invalidate(buffer, size)`). After DMA completes, the CPU reads fresh from RAM. Used in embedded systems and some DMA APIs.

3. **Non-cacheable memory regions**: Mark DMA buffers as non-cacheable in the page table (set the "caching disabled" bit in the PTE). CPU reads/writes to these addresses always go directly to RAM, never cached. Simple but slower for CPU accesses to that buffer.

4. **Bounce buffers**: If the DMA buffer is at a physical address the device can't reach (e.g., old 32-bit ISA devices with 16MB DMA limit), the OS allocates a "bounce buffer" in DMA-accessible low memory. DMA writes to bounce buffer → OS copies to actual destination. No cache coherence issue (the copy operation handles it). Performance cost of the extra copy.

Modern servers use cache-coherent DMA (IOMMU/VT-d handles this transparently).
