# Q&A — Deadlocks

---

## 🟢 Easy

**Q1. What are the four necessary conditions for deadlock?**

1. **Mutual Exclusion**: At least one resource is non-shareable (only one process at a time).
2. **Hold and Wait**: A process is holding a resource while waiting for another.
3. **No Preemption**: Resources cannot be forcibly taken from a process.
4. **Circular Wait**: A cycle exists in the wait-for graph (P1 waits for P2, P2 waits for P1, etc.).

All four must hold simultaneously for deadlock to occur. Removing any one prevents it.

---

**Q2. What is a Resource Allocation Graph?**

A directed graph with two types of nodes:
- **Circles** = Processes (P1, P2, ...)
- **Rectangles** = Resources (R1, R2, ...), with dots inside representing instances

Two types of edges:
- **P → R** (request edge): process is waiting for resource
- **R → P** (assignment edge): resource instance is assigned to process

**For single-instance resources**: A cycle in the RAG = deadlock.
**For multi-instance resources**: A cycle is necessary but not sufficient for deadlock.

---

**Q3. What is the difference between deadlock prevention and deadlock avoidance?**

**Deadlock Prevention**: Statically design the system to make at least one of the four Coffman conditions impossible. Conservative — some legitimate requests are always denied. Example: enforce resource ordering to eliminate circular wait.

**Deadlock Avoidance**: Dynamically decide whether to grant each resource request based on whether doing so might lead to deadlock. More permissive than prevention — allows more concurrency. Requires knowing maximum needs in advance. Example: Banker's Algorithm.

---

**Q4. What is a safe state?**

A system state is **safe** if there exists a **safe sequence** of all processes — an ordering in which each process can be allocated its maximum needed resources using currently available resources plus resources released by earlier processes in the sequence.

In a safe state, deadlock can be avoided by executing processes in the safe order.
An unsafe state doesn't guarantee deadlock — but deadlock might occur.

---

**Q5. What is livelock? How is it different from deadlock?**

**Deadlock**: Processes are blocked, consuming no CPU, making no progress.
**Livelock**: Processes are running (consuming CPU) but making no progress — they keep responding to each other in a way that prevents any forward progress.

Example: Two processes both detect a conflict and both politely back off at exactly the same time, retry, conflict again, back off again — forever.

Fix: Randomized backoff — each process retries after a random delay, breaking the synchrony.

---

## 🟡 Medium

**Q6. How does the "resource ordering" strategy for circular wait prevention work? Prove it prevents circular wait.**

Assign a unique number to each resource type: R1 < R2 < ... < Rn.

Rule: A process can request resource Rk only if it currently holds no resource Rj where j ≥ k.

**Proof**: Assume circular wait exists: P0 → R_a0 → P1 → R_a1 → ... → Pn → R_an → P0.

In this cycle, P_i holds R_{a_(i-1)} and waits for R_{a_i}. By the ordering rule, a process can only request higher-numbered resources than it currently holds. So R_{a_(i-1)} < R_{a_i} for all i.

This means: R_{a0} < R_{a1} < ... < R_{an} < R_{a0}. This is a contradiction (R_{a0} cannot be less than itself). Therefore, no circular wait can exist.

---

**Q7. Run the Banker's Algorithm on this example. Is the system in a safe state?**

Processes: P0, P1, P2, P3, P4. Resources: A, B, C (3 types).
Available: A=3, B=3, C=2.

| Process | Max (A,B,C) | Allocation (A,B,C) | Need (A,B,C) |
|---------|------------|-------------------|--------------|
| P0 | 7,5,3 | 0,1,0 | 7,4,3 |
| P1 | 3,2,2 | 2,0,0 | 1,2,2 |
| P2 | 9,0,2 | 3,0,2 | 6,0,0 |
| P3 | 2,2,2 | 2,1,1 | 0,1,1 |
| P4 | 4,3,3 | 0,0,2 | 4,3,1 |

**Safety Algorithm:**
- Work = [3,3,2], Finish = [F,F,F,F,F]

Iteration 1: Find i where Need[i] ≤ Work.
- P0: [7,4,3] ≤ [3,3,2]? No.
- P1: [1,2,2] ≤ [3,3,2]? Yes! Work = [3,3,2]+[2,0,0] = [5,3,2]. Finish[1]=T.

Iteration 2: Work=[5,3,2].
- P3: [0,1,1] ≤ [5,3,2]? Yes! Work = [5,3,2]+[2,1,1] = [7,4,3]. Finish[3]=T.

Iteration 3: Work=[7,4,3].
- P4: [4,3,1] ≤ [7,4,3]? Yes! Work = [7,4,3]+[0,0,2] = [7,4,5]. Finish[4]=T.

Iteration 4: Work=[7,4,5].
- P0: [7,4,3] ≤ [7,4,5]? Yes! Work = [7,4,5]+[0,1,0] = [7,5,5]. Finish[0]=T.

Iteration 5: Work=[7,5,5].
- P2: [6,0,0] ≤ [7,5,5]? Yes! Work = [7,5,5]+[3,0,2] = [10,5,7]. Finish[2]=T.

All Finish = true. **SAFE STATE. Safe sequence: P1 → P3 → P4 → P0 → P2.**

---

**Q8. Now P1 requests additional resources [1,0,2]. Should the system grant this?**

New request from P1: [1,0,2].

Step 1: Is [1,0,2] ≤ Need[1] = [1,2,2]? Yes.
Step 2: Is [1,0,2] ≤ Available = [3,3,2]? Yes.
Step 3: Tentatively allocate:
- Available = [3,3,2] - [1,0,2] = [2,3,0]
- Allocation[1] = [2,0,0] + [1,0,2] = [3,0,2]
- Need[1] = [1,2,2] - [1,0,2] = [0,2,0]

Step 4: Run Safety Algorithm with new state. Work=[2,3,0]:
- P1: Need=[0,2,0] ≤ [2,3,0]? Yes. Work=[2,3,0]+[3,0,2]=[5,3,2]. Finish[1]=T.
- P3: Need=[0,1,1] ≤ [5,3,2]? Yes. Work=[5,3,2]+[2,1,1]=[7,4,3]. Finish[3]=T.
- P4: Need=[4,3,1] ≤ [7,4,3]? Yes. Work=[7,4,3]+[0,0,2]=[7,4,5]. Finish[4]=T.
- P0: Need=[7,4,3] ≤ [7,4,5]? Yes. Work=[7,4,5]+[0,1,0]=[7,5,5]. Finish[0]=T.
- P2: Need=[6,0,0] ≤ [7,5,5]? Yes. Finish[2]=T.

All done. **SAFE. Grant the request. New safe sequence: P1→P3→P4→P0→P2.**

---

**Q9. What's the difference between deadlock detection using a wait-for graph vs the detection algorithm for multiple instances?**

**Wait-for graph (single instances)**:
- Remove resource nodes from RAG. Draw P_i → P_j if P_i waits for something P_j holds.
- Run cycle detection (DFS, O(V+E)).
- Cycle = deadlock. Simple and efficient.
- Doesn't work with multiple instances — you need to know which specific instance to track.

**Detection algorithm (multiple instances)**:
- Similar to Banker's safety algorithm but simpler: no Need matrix, work with current Allocation and Request.
- Finds which processes can't possibly finish (their current request can never be granted given what's available and what others will release).
- More complex, O(n²·m), but necessary when resources have multiple instances.

---

## 🔴 Hard

**Q10. Can deadlock occur if only one process is requesting resources? Explain in terms of the Coffman conditions.**

No. The **Circular Wait** condition requires a cycle of processes, each waiting for a resource held by the next. With only one process, no cycle is possible — a process cannot be waiting for itself (it either has the resource or is waiting for no one in particular).

However, a single process can experience a **self-deadlock** if it tries to acquire a non-recursive mutex it already holds:
```
Thread A: lock(mutex);  // acquires
Thread A: lock(mutex);  // tries to acquire again → blocks (waiting for itself to release)
```
This satisfies Hold-and-Wait (holds mutex, waiting for mutex), No Preemption, but not Circular Wait in the traditional sense — it's implementation-dependent whether the OS considers this deadlock or a programming error.

In practice: POSIX mutexes with type `PTHREAD_MUTEX_DEFAULT` result in undefined behavior on recursive lock; `PTHREAD_MUTEX_DEADLOCK` causes immediate deadlock detection.

---

**Q11. In the Banker's Algorithm, a process must declare its maximum needs upfront. Why is this restriction a problem in practice? What real systems use instead?**

**Problems with Banker's in practice:**

1. **Unknown maximum**: Many programs don't know their maximum resource needs. A web server doesn't know how many simultaneous connections it will handle. A database doesn't know how many transactions will run.

2. **Dynamic processes**: Banker's assumes a fixed set of processes. Real systems constantly create/destroy processes (Docker containers, worker threads).

3. **Resource types are dynamic**: Resources are added (hotplug hardware) or removed (disk failure). Banker's assumes static resource sets.

4. **Overhead**: O(n²·m) per request is prohibitive for high-frequency requests.

**What real systems use instead:**
- **Ignore deadlocks** (Linux, macOS, Windows): Most general-purpose OSes assume deadlocks are rare and rely on applications being written correctly. If deadlock occurs, the user restarts the process.
- **Detection + recovery**: Database management systems (PostgreSQL, MySQL InnoDB) use deadlock detection. When detected, they abort the youngest transaction (lowest cost) and retry it. The user sees a transaction rollback.
- **Prevention via protocol**: Application-level conventions like "always acquire locks in the same order" (resource ordering) prevent deadlock without OS involvement.
- **Avoidance with domain knowledge**: Real-time systems with known resource requirements can implement simpler versions of avoidance.

---

**Q12. Draw a RAG for the following scenario and determine if deadlock exists:**

P1 holds R1 and waits for R2. P2 holds R2 and waits for R3. P3 holds R3 and waits for R1. R1, R2, R3 each have one instance.

```
RAG:
R1 → P1 (R1 assigned to P1)
P1 → R2 (P1 requests R2)
R2 → P2 (R2 assigned to P2)
P2 → R3 (P2 requests R3)
R3 → P3 (R3 assigned to P3)
P3 → R1 (P3 requests R1)
```

**Wait-for graph** (remove resource nodes):
```
P1 → P2 → P3 → P1   (cycle!)
```

Since each resource has exactly one instance and there is a cycle in the RAG/wait-for graph: **DEADLOCK. All three processes are deadlocked.**

To recover: terminate P1 (or P2 or P3). Say we terminate P1:
- R1 is released. P3 can now get R1.
- P3 finishes, releases R3. P2 can get R3.
- P2 finishes, releases R2.
- Deadlock resolved.
