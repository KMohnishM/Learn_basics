# Cheat Sheet — CPU Scheduling

## Key Formulas
```
Turnaround Time (TAT) = Completion Time - Arrival Time
Waiting Time (WT)     = TAT - Burst Time
Response Time (RT)    = First CPU Start Time - Arrival Time
CPU Utilization       = Total Burst / Total Time × 100%
Average WT            = Σ(WT_i) / n
```

## Algorithm Comparison

| Algorithm | Preemptive? | Starvation? | Overhead | Best For |
|-----------|:-----------:|:-----------:|----------|----------|
| FCFS | ❌ | ❌ | Low | Batch, similar bursts |
| SJF | ❌ | ✅ | Medium | Minimizing avg WT (theory) |
| SRTF | ✅ | ✅ | High | Best avg WT in preemptive |
| Priority | Both | ✅ | Medium | Real-time with priorities |
| Round Robin | ✅ | ❌ | Medium | Time-sharing, interactive |
| MLFQ | ✅ | ❌ (aging) | High | General purpose (real OSes) |
| CFS | ✅ | ❌ | Medium | Linux default |

## Convoy Effect (FCFS)
- Long process runs first → short processes wait a long time
- Solution: SJF or preemptive scheduling

## SJF CPU Burst Prediction
$$\tau_{n+1} = \alpha \cdot t_n + (1-\alpha) \cdot \tau_n$$
- α = 0.5 (typical): equal weight to recent and historical
- α → 1: only recent burst matters (very reactive)
- α → 0: only history matters (smooth, ignores recent)

## Round Robin Rule of Thumb
```
Quantum too small → too many context switches (50% overhead if q = switch_cost)
Quantum too large → degenerates to FCFS
Sweet spot: 80% of bursts < quantum (most jobs finish in one turn)
Typical: q = 10-100ms
Max wait before first response = (n-1) × q
```

## Context Switch Overhead
```
Overhead % = context_switch_cost / (quantum + context_switch_cost) × 100
```

## MLFQ Rules Summary
```
1. New process → highest priority queue
2. Uses full quantum → demote (CPU-bound penalty)
3. Blocks before quantum → stay or promote (I/O-bound reward)
4. Wait too long in low queue → aging boost (prevent starvation)
```

## Real-Time Scheduling
| | EDF | RMS |
|-|-----|-----|
| Priority | Dynamic (closest deadline first) | Static (shortest period first) |
| Max utilization | 100% | n(2^(1/n) - 1) → 69.3% as n→∞ |
| Complexity | Higher | Lower |
| Optimality | Optimal (uniprocessor) | Not always |

## RMS Utilization Bounds
| n | Bound |
|---|-------|
| 1 | 100.0% |
| 2 | 82.8% |
| 3 | 78.0% |
| 5 | 74.3% |
| ∞ | 69.3% (ln 2) |

## Linux CFS Key Points
```
vruntime += Δt × (weight_nice0 / weight_process)
Lower nice → higher weight → vruntime grows SLOWER → runs MORE often
Data structure: Red-Black Tree (leftmost = smallest vruntime = runs next)
Default targeted latency: 6ms (adjusts with process count)
Minimum granularity: 0.75ms (prevents excessive context switches)
nice range: -20 (highest priority) to +19 (lowest priority)
```

## Multiprocessor Key Terms
```
SMP: All CPUs share ready queue, self-schedule
Processor Affinity: Keep process on same CPU (warm cache)
  - Soft: try to, but can migrate
  - Hard: pinned (taskset command)
Load Balancing: Push (active) or Pull (idle CPU steals work)
NUMA: Memory access faster when local to CPU socket
```

## Gantt Chart Worked Example — SRTF
```
P1(A=0,B=8), P2(A=1,B=4), P3(A=2,B=9), P4(A=3,B=5)

t=0: Run P1 (only option)
t=1: P2(4) arrives, P1 remaining=7. 4<7 → preempt! Run P2
t=5: P2 done. Options: P1(7),P3(9),P4(5). Min=P4. Run P4
t=10: P4 done. Options: P1(7),P3(9). Min=P1. Run P1
t=17: P1 done. Run P3
t=26: P3 done.

WT: P1=9, P2=0, P3=15, P4=2  →  Avg = 6.5ms
```
