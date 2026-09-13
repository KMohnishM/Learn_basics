# Module 8: I/O Systems & Disk Scheduling

---

## 1. I/O Hardware Overview

The CPU cannot directly access devices. It communicates with them through a layered hardware hierarchy:

```
CPU ←──→ Memory Bus ←──→ RAM
  ↓
I/O Bus (PCI Express)
  ↓
I/O Controllers (device controllers)
  ↓
Devices (disk, keyboard, NIC, GPU...)
```

### Ports, Buses, and Controllers

**Port**: A connection point between a device and the system (USB port, SATA port, PCIe slot).

**Bus**: Shared communication path used by multiple devices. Multiple devices share the same bus, which means only one can transmit at a time (bus arbitration).
- Memory bus: CPU ↔ RAM (fastest)
- PCI Express: CPU ↔ graphics card, NVMe SSD
- SATA: CPU/chipset ↔ hard drives
- USB: CPU/chipset ↔ peripheral devices

**Device Controller**: Hardware component between the bus and the device. Contains:
- **Data register**: Holds data to be transferred.
- **Status register**: Current state (busy/idle/error/done).
- **Command register**: CPU writes commands here ("start read", "start write").

The CPU communicates with the controller via these registers — either through **memory-mapped I/O** (registers appear as special memory addresses) or **port-mapped I/O** (separate I/O address space, accessed with special instructions like `IN`/`OUT` on x86).

---

## 2. Three Methods of I/O

### 1. Programmed I/O (Polling / Busy-Wait)

The CPU continuously reads the device's status register in a loop until the I/O operation completes:

```c
while (status_register != DONE)
    ;  // busy-wait (spin)
// Read data register
```

**Advantage**: Simple. No interrupt hardware needed.

**Disadvantage**: CPU is 100% occupied spinning — cannot do any useful work during I/O. For a disk read taking 5ms and a CPU running at 3GHz = 15 million wasted instructions. Completely unacceptable for slow devices.

**When used**: Acceptable for very fast devices where the wait is nanoseconds (e.g., checking if a GPU command buffer has space).

### 2. Interrupt-Driven I/O

The CPU issues an I/O command, then continues executing other code. When the device finishes, it raises a hardware **interrupt** on the CPU's interrupt line.

**Sequence:**
1. CPU writes command to device controller's command register.
2. CPU continues executing other processes (context switch to another ready process).
3. Device performs I/O operation (independently, in hardware).
4. Device finishes → asserts interrupt line.
5. CPU finishes current instruction, checks interrupt line, suspends current process.
6. CPU jumps to **Interrupt Service Routine (ISR)** via interrupt vector table.
7. ISR reads data from device, copies to buffer, acknowledges interrupt.
8. CPU resumes interrupted process (or scheduler picks a different process).

**Interrupt vector table**: Array of ISR function pointers, indexed by interrupt number. Each device has a unique interrupt number (IRQ line on x86).

**Interrupt latency**: Time from device raising interrupt to ISR executing. Must be minimized in real-time systems.

**Non-maskable interrupts (NMI)**: Cannot be disabled. Used for catastrophic hardware errors (memory parity error, watchdog timeout).

**Maskable interrupts**: Can be temporarily disabled by the CPU (during critical sections in the kernel, `cli` instruction on x86). Device interrupts wait until `sti` re-enables them.

**Vectored vs Non-vectored interrupts**: Vectored = each device has its own interrupt number → direct jump to device's ISR. Non-vectored = all devices share one interrupt line → ISR must poll all devices to find which one interrupted.

**Interrupt chaining**: Multiple ISRs chained together for the same interrupt number. Each ISR checks if it was its device, handles it, then calls `next` in the chain.

### 3. Direct Memory Access (DMA)

For large data transfers (disk blocks, network packets), interrupt-driven I/O requires the CPU to copy data byte-by-byte from the device controller to memory — still wasteful.

**DMA Controller** (DMAC) performs data transfer directly between device and RAM, **without CPU involvement** for the actual data movement.

**DMA Sequence:**
1. CPU sets up the DMA controller:
   - Source: device controller's data buffer
   - Destination: physical memory address
   - Length: number of bytes to transfer
   - Direction: device→memory or memory→device
2. CPU issues the I/O command to the device and is **immediately free** to run other code.
3. DMA controller manages the data transfer on the bus, one block at a time.
   - **Cycle stealing**: DMA controller occasionally "steals" a memory bus cycle from the CPU (CPU stalls for one cycle). The CPU barely notices.
4. Transfer complete → DMA controller raises **one interrupt**.
5. ISR notes transfer is complete, schedules the waiting process.

**Why DMA is a massive win**: A 64KB disk read with interrupt-driven I/O would interrupt the CPU 65,536 times (once per byte) or 1,024 times (once per 64-byte cache line). With DMA: exactly **1 interrupt**.

**DMA coherence issue**: DMA writes directly to physical RAM. If the CPU has a cached copy of that memory in its CPU cache, the cache is now stale (CPU's cache says old value; RAM has new DMA-written value). Modern systems handle this via cache-coherent DMA or by explicitly invalidating cache lines before DMA.

---

## 3. I/O Software Layers

The OS organizes I/O software in layers, each providing services to the layer above:

```
┌─────────────────────────────────────┐
│     User-level I/O software         │ (stdio library, open/read/write syscalls)
├─────────────────────────────────────┤
│   Device-independent OS software    │ (buffering, caching, error reporting,
│                                     │  uniform device naming, access control)
├─────────────────────────────────────┤
│        Device Drivers               │ (device-specific: disk driver, NIC driver,
│                                     │  keyboard driver. Each vendor writes their own)
├─────────────────────────────────────┤
│      Interrupt Handlers             │ (low-level, runs in interrupt context,
│                                     │  minimal work: mark buffer done, wake process)
├─────────────────────────────────────┤
│      Hardware (devices)             │
└─────────────────────────────────────┘
```

**Device Driver responsibilities**: Initialize hardware, translate OS requests (read block N) into hardware commands, manage device-specific error handling, register with VFS (block devices) or character device layer.

**Device-independent layer**: Provides uniform interface regardless of device type. Handles: allocating and freeing device-dedicated buffers, error reporting (turn device error codes into OS error codes), device naming (`/dev/sda`, `/dev/tty`), access control (who can open which device), blocking/waking processes waiting on I/O.

---

## 4. Blocking vs Non-blocking vs Asynchronous I/O

**Blocking I/O** (`read()` default): The calling process is suspended until the I/O completes. Simple to program. Process can't do anything else while waiting.

**Non-blocking I/O** (`O_NONBLOCK` flag): System call returns immediately, even if no data is available (returns 0 or EAGAIN). The process must poll the device or use `select()`/`poll()`/`epoll()` to know when data is ready.

**Asynchronous I/O** (`aio_read()`, `io_uring`): Process submits I/O request and gets a notification (signal or completion queue entry) when done. Process continues running without blocking. Most efficient for I/O-intensive servers.

```
Blocking:      Process: [issue] [WAIT...] [process data]
Non-blocking:  Process: [issue] [check] [do other work] [check] [process data]
Asynchronous:  Process: [issue] [do other work] ← [notification arrives] [process data]
```

---

## 5. Buffering

**Why buffering**: Speed mismatch between devices. A network card receives data at variable rate; applications read at variable rate. A buffer decouples the two.

**Single buffer**: OS maintains one buffer. Device writes to buffer while process reads from previous buffer (or vice versa). If both need the buffer simultaneously → wait.

**Double buffer**: Two buffers. Device fills one while process empties the other. They swap roles when both finish. Better throughput — device and process can work simultaneously.

**Circular buffer** (ring buffer): N buffers in a ring. Producer adds to head, consumer removes from tail. Standard in kernel I/O (network receive queues, audio buffers). Lockless implementations possible with atomic head/tail updates.

**Why the kernel buffers writes (page cache)**: Writing to disk synchronously (each `write()` waits for disk) is 1000× slower than memory access. The kernel buffers writes in memory (page cache), coalesces multiple writes to the same area, and flushes asynchronously (pdflush/writeback). Result: `write()` returns to the application in microseconds even though disk write takes milliseconds.

---

## 6. Disk Structure — Physical Layout

Understanding disk structure is essential for understanding why scheduling matters.

```
Platter cross-section:
┌──────────────────────────────┐
│  Track 0 (outermost)         │
│    Track 1                   │
│      Track 2                 │
│        ...                   │
│      Track N-1 (innermost)   │
└──────────────────────────────┘

Multi-platter:
- Multiple platters stacked on a spindle (rotate together)
- Read/write head per platter surface
- All heads move together (on the same arm)
- Cylinder = all tracks at the same radius across all platters
```

**Key terms:**
- **Sector**: Smallest addressable unit (512 bytes traditional, 4096 bytes on modern "Advanced Format" drives).
- **Track**: Concentric circle on one platter surface.
- **Cylinder**: Set of all tracks at the same radius across all platters (heads don't need to move to switch between cylinders of the same cylinder).
- **Seek**: Moving the read/write arm to a different track (cylinder). Most expensive operation.
- **Rotational latency**: Waiting for the desired sector to rotate under the head. On average, half a rotation = half the rotational period.
- **Transfer time**: Actual time to read/write the sector(s).

### Disk Access Time

```
Total Access Time = Seek Time + Rotational Latency + Transfer Time

Seek Time:          3–10ms average (modern HDDs)
Rotational Latency: avg = (60,000 / RPM) / 2 ms
                    For 7200 RPM: 60,000/7200/2 = 4.17ms
Transfer Time:      Usually negligible (< 0.5ms for one sector)

Total avg ≈ 7–15ms per random access on HDD
SSD:        0.02–0.1ms (no moving parts → no seek/rotation delay)
```

**Seek time dominates**: For random access patterns, 90%+ of disk access time is seek + rotational latency. The disk scheduling algorithms minimize seek time.

---

## 7. Disk Scheduling Algorithms

The OS maintains a queue of pending disk I/O requests. The **disk scheduler** orders these requests to minimize total seek time.

We'll use this example request queue (cylinder numbers): `98, 183, 37, 122, 14, 124, 65, 67`. Head starts at cylinder **53**.

### FCFS (First-Come, First-Served)

Process requests in the order they arrive.

Sequence: 53 → 98 → 183 → 37 → 122 → 14 → 124 → 65 → 67

```
Movement: |53-98|+|98-183|+|183-37|+|37-122|+|122-14|+|14-124|+|124-65|+|65-67|
        = 45 + 85 + 146 + 85 + 108 + 110 + 59 + 2
        = 640 cylinders total movement
```

**Simple but poor performance**: Head moves back and forth wildly across the disk.

---

### SSTF (Shortest Seek Time First)

Always service the request closest to the current head position.

From 53: Closest is 65 (dist=12). Then 67 (dist=2). Then 37 (dist=30). Then 14 (dist=23). Then 98 (dist=84). Then 122 (dist=24). Then 124 (dist=2). Then 183 (dist=59).

Sequence: 53 → 65 → 67 → 37 → 14 → 98 → 122 → 124 → 183

```
Movement: 12+2+30+23+84+24+2+59 = 236 cylinders
```

Much better than FCFS (236 vs 640)!

**Problem**: **Starvation**. If requests keep arriving near the current head position, a request far away may never be serviced. A request at cylinder 199 might wait indefinitely while the head services a steady stream of requests around cylinders 50–100.

---

### SCAN (Elevator Algorithm)

Head moves in one direction, servicing all requests in that direction. When it reaches the end (or the last request in that direction), reverses direction.

Starting at 53, moving toward higher cylinders:

Sequence: 53 → 65 → 67 → 98 → 122 → 124 → 183 → **[reverse]** → 37 → 14

```
Movement: 12+2+31+24+2+59 = 130 (up) + 146+23 = 169 (down) = 299 cylinders
```

**More uniform wait times than SSTF**. No starvation (head eventually reaches every cylinder).

**Disadvantage**: Requests just behind the head (where it just came from) must wait for a full sweep across the disk and back. Not perfectly uniform.

---

### C-SCAN (Circular SCAN)

Head moves in ONE direction only (e.g., low to high). When it reaches the highest request, it **jumps back to cylinder 0** without servicing any requests on the return trip, then sweeps upward again.

Sequence: 53 → 65 → 67 → 98 → 122 → 124 → 183 → **[jump to 0]** → 14 → 37

```
Movement: 130 (up) + 183 (jump to 0 + sweep to 37) ≈ 313 cylinders
```

**More uniform wait times than SCAN**: A cylinder at any position waits at most one full sweep, not one-and-a-half (as with SCAN which wastes the reverse sweep on the return).

**Trade-off**: Slightly more total head movement than SCAN, but more predictable wait times.

---

### LOOK and C-LOOK

**LOOK**: Like SCAN, but the head only goes as far as the **last request** in each direction (doesn't travel to disk end).

**C-LOOK**: Like C-SCAN, but only goes to the highest request before jumping back to the lowest request (doesn't go to cylinder 0 or maximum cylinder).

Starting at 53, moving up:
C-LOOK: 53 → 65 → 67 → 98 → 122 → 124 → 183 → **[jump to]** → 14 → 37

```
Movement: (183-53) + (183-14) = 130 + 169 = 299 cylinders (but no unnecessary end travel)
```

LOOK and C-LOOK are the most commonly used algorithms in practice — they avoid unnecessary movement to disk boundaries.

### Algorithm Comparison

| Algorithm | Total Movement (example) | Starvation? | Notes |
|-----------|:------------------------:|:-----------:|-------|
| FCFS | 640 | ❌ | Fair, terrible efficiency |
| SSTF | 236 | ✅ Possible | Good efficiency, unfair |
| SCAN | 299 | ❌ | Good balance |
| C-SCAN | ~313 | ❌ | More uniform wait times |
| LOOK | ~253 | ❌ | SCAN but smarter |
| C-LOOK | ~299 | ❌ | Best in practice |

**Note**: For SSDs, disk scheduling is nearly irrelevant — there is no physical head movement, so access time is roughly uniform regardless of "cylinder" position. Linux uses simpler schedulers (or none) for NVMe SSDs.

---

## 8. RAID — Redundant Array of Independent Disks

RAID combines multiple physical disks into one logical unit to achieve better performance, redundancy (fault tolerance), or both.

### RAID 0 — Striping

Data is split (striped) across multiple disks in chunks.

```
Block 0 → Disk 0   Block 1 → Disk 1   Block 2 → Disk 0   Block 3 → Disk 1
```

- **Read speed**: All disks read in parallel → N× throughput.
- **Write speed**: All disks write in parallel → N× throughput.
- **Redundancy**: ❌ NONE. If ONE disk fails → ALL data lost.
- **Capacity**: 100% of total disk capacity used.
- **Use case**: Temporary data, scratch space, where speed matters and data loss is acceptable.

### RAID 1 — Mirroring

Every block is written to two disks identically. Two disks, exact copy.

- **Read speed**: Can read from either disk → effectively 2× read throughput (different blocks from different disks simultaneously).
- **Write speed**: Must write to both → same as single disk (bottlenecked by the slower write).
- **Redundancy**: ✅ ONE disk can fail with zero data loss.
- **Capacity**: 50% overhead (N disks → N/2 usable capacity).
- **Use case**: OS drives, database logs where data loss is unacceptable.

### RAID 5 — Striped with Distributed Parity

Data is striped across N disks. For every N-1 data blocks, one **parity block** is computed (XOR of the N-1 data blocks) and distributed across all disks (no dedicated parity disk).

```
Disk 0  Disk 1  Disk 2  Disk 3
  A0      A1      A2    A_parity
  B0      B1    B_parity  B2
  C0    C_parity  C1      C2
```

- **Read speed**: Parallel reads from all disks → (N-1)/N of total capacity reads in parallel.
- **Write speed**: Each write requires reading old data + old parity, computing new parity, writing new data + new parity = **4 disk I/Os per write** (the "write penalty").
- **Redundancy**: ✅ Any ONE disk can fail. Reconstruct lost data by XORing the other N-1 disks.
- **Capacity**: (N-1)/N of total capacity. For 4 disks of 1TB each: 3TB usable.
- **Use case**: The most commonly deployed RAID level. Good balance of performance, redundancy, and capacity efficiency.

**Parity math**: If A0 ⊕ A1 ⊕ A2 ⊕ A_parity = 0 (XOR), then any one missing value = XOR of the others.

**Rebuild (recovery)**: When a failed disk is replaced, the RAID controller reads ALL remaining disks and XORs them to reconstruct the missing data. For large arrays, this takes hours — during which a second disk failure would cause total data loss.

### RAID 6 — Striped with Double Distributed Parity

Like RAID 5 but with **two parity blocks** per stripe (using different mathematical codes — P and Q parity).

- **Redundancy**: ✅ Any **TWO** disks can fail simultaneously.
- **Write speed**: Even slower than RAID 5 (6 I/Os per write — two parity updates).
- **Capacity**: (N-2)/N usable.
- **Use case**: Large disk arrays where rebuild time is long and the probability of a second failure during rebuild is non-trivial.

### RAID 10 (1+0) — Stripe of Mirrors

Combines RAID 1 (mirroring) and RAID 0 (striping). Create N/2 mirrored pairs (RAID 1), then stripe across all pairs (RAID 0).

```
[Disk 0 ↔ Disk 1] mirrored pair 0
[Disk 2 ↔ Disk 3] mirrored pair 1
Data striped across pair 0 and pair 1
```

- **Read speed**: Full parallel reads from all disks.
- **Write speed**: Better than RAID 5 (only mirroring, no parity computation).
- **Redundancy**: ✅ Can tolerate multiple disk failures as long as no mirrored pair loses both disks.
- **Capacity**: 50% (same as RAID 1).
- **Use case**: High-performance, high-reliability databases (MySQL, Oracle often use RAID 10).

### RAID Comparison Table

| RAID | Min Disks | Fault Tolerance | Read Speed | Write Speed | Usable Capacity |
|------|:---------:|:---------------:|:----------:|:-----------:|:---------------:|
| 0 | 2 | 0 drives | Excellent | Excellent | 100% |
| 1 | 2 | 1 drive | Good | Fair | 50% |
| 5 | 3 | 1 drive | Good | Poor (write penalty) | (N-1)/N |
| 6 | 4 | 2 drives | Good | Worse | (N-2)/N |
| 10 | 4 | 1 per pair | Excellent | Good | 50% |
