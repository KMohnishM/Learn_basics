# Cheat Sheet — Deadlocks

## Four Coffman Conditions (ALL must hold for deadlock)
| # | Condition | What it means |
|---|-----------|--------------|
| 1 | **Mutual Exclusion** | Resource used by only one process at a time |
| 2 | **Hold and Wait** | Process holds a resource while waiting for another |
| 3 | **No Preemption** | Resources not forcibly taken away |
| 4 | **Circular Wait** | Cycle: P1 waits for P2, P2 waits for P1, ... |

## Deadlock Handling Strategies
| Strategy | Approach | Used By |
|----------|----------|---------|
| **Prevention** | Make ≥1 condition impossible | Design-time |
| **Avoidance** | Dynamically check before granting | Real-time OS, Banker's |
| **Detection + Recovery** | Let happen, then fix | Databases (MySQL, Postgres) |
| **Ignore** | Ostrich algorithm | Linux, Windows (rare deadlocks) |

## Prevention: Attacking Each Condition
```
1. Mutual Exclusion → Use shareable resources (read-only data) — not always possible
2. Hold and Wait   → Request ALL resources upfront, or release all before new request
3. No Preemption   → Allow OS to forcibly take resources (only for saveable state)
4. Circular Wait   → Total ordering on resources: always request in increasing numeric order
```

## Resource Allocation Graph (RAG)
```
P → R  : Request edge (process wants resource)
R → P  : Assignment edge (resource given to process)

Single instance: cycle = deadlock
Multi instance:  cycle ≠ necessarily deadlock (check with algorithm)
```

## Banker's Algorithm — Data Structures
```
n = number of processes, m = resource types

Available[m]     : free instances of each resource
Max[n][m]        : maximum demand per process
Allocation[n][m] : currently allocated to each process
Need[n][m]       : Max - Allocation (what still needed)
```

## Safety Algorithm
```
Work = Available.copy()
Finish[i] = false for all i

repeat:
    find i: Finish[i]==false AND Need[i] <= Work
    if found:
        Work = Work + Allocation[i]
        Finish[i] = true
until no progress

if all Finish[i]==true → SAFE (found safe sequence)
else → UNSAFE
```

## Resource-Request Algorithm
```
Process Pi requests Resources[]:

1. If Request > Need[i]       → Error (exceeded max claim)
2. If Request > Available     → Wait (not enough resources)
3. Tentatively grant:
     Available -= Request
     Allocation[i] += Request
     Need[i] -= Request
4. Run Safety Algorithm:
     SAFE  → Grant request (keep tentative state)
     UNSAFE → Rollback step 3, make Pi wait
```

## Banker's Example — Quick Reference
```
Available = [A:3, B:3, C:2]

         Max     Alloc    Need
P0    7,5,3    0,1,0    7,4,3
P1    3,2,2    2,0,0    1,2,2  ← can run first (Need≤Available)
P2    9,0,2    3,0,2    6,0,0
P3    2,2,2    2,1,1    0,1,1  ← can run second
P4    4,3,3    0,0,2    4,3,1  ← can run third

Safe sequence: P1 → P3 → P4 → P0 → P2
```

## Detection Algorithm (Multi-Instance)
```
Work = Available.copy()
Finish[i] = true if Allocation[i]==0 else false

repeat:
    find i: Finish[i]==false AND Request[i] <= Work
    if found:
        Work = Work + Allocation[i]
        Finish[i] = true
until no progress

Any Finish[i]==false → process i is deadlocked
```

## Recovery Options
```
Process Termination:
  - Kill ALL deadlocked processes (simple, high cost)
  - Kill ONE at a time (re-run detection after each)
  Criteria for victim: priority, runtime, resources held, # to abort

Resource Preemption:
  1. Select victim (minimize cost)
  2. Rollback victim to safe state (usually: restart from beginning)
  3. Prevent starvation: include rollback count in cost function
```

## Deadlock vs Livelock vs Starvation
| | Deadlock | Livelock | Starvation |
|-|----------|----------|------------|
| Blocked? | Yes | No (running) | Ready/waiting |
| CPU used? | No | Yes (100%, wasted) | No |
| Progress? | None | None | None |
| Fix | Kill/preempt | Randomized backoff | Aging |

## Key Relationships
```
Safe State → No Deadlock (guaranteed)
Unsafe State → Deadlock POSSIBLE (not certain)
Deadlock State → Unsafe (always)

Safe ⊂ Unsafe ⊂ All states
```

## Circular Wait Prevention — Resource Ordering
```
Assign numbers to resources: R1 < R2 < ... < Rn
Rule: can only request Rk if holding no Rj where j ≥ k

Proof: if ordering holds, no cycle can form in wait-for graph
```
