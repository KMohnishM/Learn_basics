# Cheat Sheet — I/O Systems & Disk Scheduling

## Three I/O Methods
| Method | CPU during I/O | Interrupts | Best For |
|--------|:-------------:|:----------:|---------|
| **Polling** | 100% spinning (wasted) | None | Very fast devices (nanoseconds) |
| **Interrupt-driven** | Free (runs other code) | 1 per unit | Moderate speed devices |
| **DMA** | Free | 1 per whole transfer | Large transfers (disk, network) |

## DMA Sequence
```
1. CPU sets up DMAC: source, destination, length, direction
2. CPU issues I/O command → continues executing other code
3. DMAC transfers data on bus (cycle stealing from CPU)
4. Transfer complete → DMAC raises ONE interrupt
5. ISR notes completion, wakes waiting process
```

## Disk Access Time
```
Total = Seek Time + Rotational Latency + Transfer Time

Seek time:          3–10ms (average, modern HDD)
Rotational latency: 60,000 / (RPM × 2) ms
  → 7200 RPM = 4.17ms
  → 5400 RPM = 5.56ms
  → 10,000 RPM = 3ms
Transfer time:      < 0.5ms (negligible for 1 sector)

SSD total:          0.02–0.1ms (no moving parts)
```

## Disk Scheduling — Example Worked
```
Queue: 98, 183, 37, 122, 14, 124, 65, 67  (head at 53, moving up)
Sorted: 14, 37, 65, 67, 98, 122, 124, 183

FCFS:   53→98→183→37→122→14→124→65→67  = 640 cylinders ❌
SSTF:   53→65→67→37→14→98→122→124→183  = 236 cylinders ✓ (starvation risk)
SCAN:   53→65→67→98→122→124→183→37→14  = 299 cylinders (sweep both ways)
C-SCAN: 53→65→67→98→122→124→183→[jump]→14→37 = ~313 cylinders
LOOK:   like SCAN but stop at last request (not disk end)
C-LOOK: like C-SCAN but jump to lowest request (not cylinder 0)
```

## Disk Scheduling Algorithm Comparison
| Algorithm | Total Movement | Starvation? | Notes |
|-----------|:--------------:|:-----------:|-------|
| FCFS | Highest | ❌ | Fair, terrible |
| SSTF | Lowest | ✅ Possible | Greedy, unfair |
| SCAN | Medium | ❌ | Elevator |
| C-SCAN | Medium | ❌ | Uniform wait |
| LOOK | Medium | ❌ | Better SCAN |
| C-LOOK | Medium | ❌ | Best in practice |

**SSDs**: Disk scheduling irrelevant (no physical head). Use none/noop/mq-deadline.

## Rotational Latency Formula
```
Avg Rotational Latency = 60,000 / (RPM × 2) ms
                       = 30,000 / RPM  ms
```

## RAID Comparison
| RAID | Min Disks | Loses Data? | Read | Write | Capacity |
|------|:---------:|:-----------:|------|-------|---------|
| **0** | 2 | Any 1 disk | ⭐⭐⭐ | ⭐⭐⭐ | 100% |
| **1** | 2 | Both of a pair | ⭐⭐ | ⭐⭐ | 50% |
| **5** | 3 | Any 2 disks | ⭐⭐ | ⭐ (4 I/Os) | (N-1)/N |
| **6** | 4 | Any 3 disks | ⭐⭐ | ⭐ (6 I/Os) | (N-2)/N |
| **10** | 4 | Both in same pair | ⭐⭐⭐ | ⭐⭐ | 50% |

## RAID Parity Math (RAID 5)
```
Parity = D0 XOR D1 XOR D2
If D1 fails: D1 = D0 XOR D2 XOR Parity

Write penalty: 4 I/Os per write
  1. Read old data
  2. Read old parity
  3. Write new data
  4. Write new parity = old_parity XOR old_data XOR new_data
```

## RAID 5 Capacity Formula
```
Usable = (N - 1) × disk_size
Example: 4 × 2TB RAID 5 = 3 × 2TB = 6TB usable
```

## I/O Software Layers (Top to Bottom)
```
User processes (stdio, syscalls)
  ↓
Device-independent OS layer (buffering, naming, access control)
  ↓
Device drivers (device-specific hardware commands)
  ↓
Interrupt handlers (minimal work: mark done, wake process)
  ↓
Hardware
```

## Buffering Types
| Type | How | Good For |
|------|-----|---------|
| Single buffer | Producer and consumer take turns | Simple, some wait |
| Double buffer | Two buffers, swap roles | Overlap producer+consumer |
| Circular (ring) | N buffers, head/tail pointers | Network queues, audio |

## I/O Modes Comparison
| Mode | Blocks thread? | Polling? | Efficiency |
|------|:-------------:|:--------:|-----------|
| Blocking | ✅ | ❌ | Simple, 1 thread per conn |
| Non-blocking | ❌ | ✅ (select/poll) | Medium |
| Async (io_uring) | ❌ | ❌ | Highest |

## Key Numbers
```
HDD random access:   7–15ms
SSD random access:   0.02–0.1ms (NVMe)
DMA interrupts:      1 per block transfer (not 1 per byte!)
RAID 5 write I/Os:   4 per logical write
RAID 6 write I/Os:   6 per logical write
RAID 10 write I/Os:  2 per logical write (just mirror)
7200 RPM latency:    4.17ms average
```
