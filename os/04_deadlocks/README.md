# Module 4: Deadlocks

---

## 1. What is a Deadlock?

A set of processes is in a **deadlock** if every process in the set is waiting for an event that can only be caused by another process in the set — and none can proceed.

**Real-world analogy**: Two cars face each other on a one-lane bridge. Car A won't back up until Car B moves. Car B won't back up until Car A moves. Neither moves — deadlock.

In operating systems: Process A holds Resource R1 and waits for Resource R2. Process B holds R2 and waits for R1. Neither can proceed.

---

## 2. The Four Necessary Conditions (Coffman Conditions)

A deadlock can only occur if ALL FOUR conditions hold simultaneously. Removing any one condition prevents deadlock:

### 1. Mutual Exclusion
At least one resource must be held in a non-shareable mode. Only one process can use it at a time. (Inherent in the nature of many resources: printer, mutex, etc.)

### 2. Hold and Wait
A process is holding at least one resource AND is waiting to acquire additional resources currently held by other processes.

### 3. No Preemption
Resources cannot be forcibly taken away from a process holding them. A process releases resources only voluntarily (when it's done using them).

### 4. Circular Wait
There exists a set {P0, P1, ..., Pn} of waiting processes such that:
- P0 waits for a resource held by P1
- P1 waits for a resource held by P2
- ...
- Pn waits for a resource held by P0

**All four conditions must hold for deadlock. Eliminating any one prevents deadlock entirely.**

---

## 3. Resource Allocation Graph (RAG)

A directed graph to represent resource allocation state:

**Nodes:**
- **Process nodes**: circles (P1, P2, ...)
- **Resource nodes**: rectangles (R1, R2, ...). Dots inside represent instances of that resource.

**Edges:**
- **Request edge** P → R: Process P is requesting (waiting for) resource R.
- **Assignment edge** R → P: An instance of resource R is assigned to process P.

**Deadlock detection with RAG:**

**Case 1 — Each resource has exactly ONE instance:**
- If the RAG contains a **cycle** → deadlock exists.
- No cycle → no deadlock.

**Case 2 — Resources have MULTIPLE instances:**
- Cycle is **necessary but not sufficient** for deadlock.
- A cycle exists but might not be deadlock if free instances can satisfy some processes, breaking the cycle.
- Must use the deadlock detection algorithm (similar to Banker's).

**Example RAG (deadlock):**
```
P1 → R1 → P2 → R2 → P1   (cycle = deadlock)
```

**Example RAG (no deadlock despite cycle):**
```
R1 has 2 instances. P1 holds one, P3 holds one.
P2 → R1 (waiting) and P1 → R2 (waiting) forms a cycle involving P2, P1.
But P3 holds R1 and is not waiting for anything → P3 will finish and release R1 → P2 gets R1 → P2 finishes → no deadlock.
```

---

## 4. Deadlock Prevention

Attack one of the four Coffman conditions to make deadlock impossible:

### Attack Mutual Exclusion
Make resources shareable. Works for read-only resources (multiple processes can read a file simultaneously). **Not applicable** to inherently non-shareable resources (printers, mutexes).

### Attack Hold and Wait
Strategy 1: A process must request ALL its resources before it starts execution. Granted all or none. Pros: simple. Cons: low resource utilization (holds resources it doesn't need yet), starvation (may never get all resources simultaneously).

Strategy 2: A process may request resources only when it holds none. Before requesting new resources, release all currently held. Cons: process may need to redo work; state may need to be saved.

### Attack No Preemption
If a process is holding some resources and requests one that cannot be granted immediately:
- Option A: Preempt all resources held by the waiting process, add them to the available list. Process restarts.
- Option B: If the resource is held by a process that is waiting, preempt that holder's resources and give them to the requesting process.

Works only for resources whose state can be easily saved and restored (CPU registers, memory). **Not applicable** to printers (can't "take back" a half-printed page), mutexes.

### Attack Circular Wait
Impose a total ordering on resource types. Number them 1 to N. A process can only request resources in increasing order.

```
R1 < R2 < R3 ... < Rn

Process can request R3 only if it holds no resource numbered ≥ 3.
```

If all processes request resources in the same order, circular wait is impossible. Proof: No process in the waiting set would be waiting for a resource numbered lower than its current resources — so you can't form a cycle where the highest-numbered resource is needed by the lowest-numbered holder.

**Most practical prevention**: enforcing resource ordering in code.

---

## 5. Deadlock Avoidance — Banker's Algorithm

Prevention is often too restrictive (low resource utilization). Avoidance allows more concurrency by making dynamic decisions: before granting a resource request, check if doing so could lead to deadlock.

**Key concept: Safe State**

A state is **safe** if there exists a **safe sequence** — an ordering of all processes P1, P2, ..., Pn such that for each Pi, all resources Pi still needs can be satisfied by currently available resources PLUS resources held by all Pj where j < i.

In a safe state, deadlock is **possible to avoid** (by executing processes in the safe order). In an unsafe state, there is **no guarantee** — deadlock may or may not occur.

**Rule**: Always stay in a safe state. Refuse any resource request that would transition the system to an unsafe state.

### Banker's Algorithm — Multiple Resource Types

**Data Structures** (n processes, m resource types):

- `Available[m]`: Number of available instances of each resource type.
- `Max[n][m]`: Maximum demand of each process for each resource type.
- `Allocation[n][m]`: Currently allocated resources for each process.
- `Need[n][m]`: Remaining needs. `Need[i][j] = Max[i][j] - Allocation[i][j]`

**Safety Algorithm:** (Run this to check if current state is safe)
```
Work = Available.copy()
Finish[i] = false for all i

Loop until no progress:
    Find i such that:
        Finish[i] == false AND Need[i] <= Work (component-wise)
    If found:
        Work = Work + Allocation[i]   // process i finishes, releases its resources
        Finish[i] = true

If all Finish[i] == true → SAFE (safe sequence found)
Else → UNSAFE
```

**Resource-Request Algorithm:** (Run when process Pi requests Resources[])
```
1. If Request[i] > Need[i]: Error (exceeded declared maximum)
2. If Request[i] > Available: Wait (resources not available)
3. Tentatively allocate:
       Available = Available - Request[i]
       Allocation[i] = Allocation[i] + Request[i]
       Need[i] = Need[i] - Request[i]
4. Run Safety Algorithm:
       If SAFE: grant the request
       If UNSAFE: roll back step 3, make Pi wait
```

**Why Banker's is impractical:**
1. Must know each process's maximum resource needs in advance (not always possible).
2. Number of processes must be fixed (processes dynamically created in real systems).
3. Resources must not be freed between requests — but resources fail, get added, etc.
4. High overhead per request (O(n²·m) safety check).

---

## 6. Deadlock Detection

Accept that deadlocks may occur; detect them after they happen and recover.

### Single Instance Resources — Wait-For Graph
Simplify the RAG by removing resource nodes. Draw edges P_i → P_j if P_i is waiting for a resource held by P_j.

A cycle in the wait-for graph **= deadlock**.

Maintain the wait-for graph dynamically. Run a cycle-detection algorithm (O(n²)) when needed.

### Multiple Instance Resources — Detection Algorithm

Same structure as Banker's Safety Algorithm but without the Need matrix (work with Allocation and Request directly):

```
Work = Available.copy()
Finish[i] = (Allocation[i] == 0 for all resources)  // Finished if holding nothing

Loop until no progress:
    Find i such that:
        Finish[i] == false AND Request[i] <= Work
    If found:
        Work = Work + Allocation[i]
        Finish[i] = true

If any Finish[i] == false → process i is DEADLOCKED
```

**How often to run detection?**
- Every time a request can't be granted (expensive but catches deadlock immediately).
- Periodically (e.g., every hour, or when CPU utilization drops below threshold — a sign processes are stuck).

Trade-off: Less frequent = more processes may become involved in deadlock before detection.

---

## 7. Deadlock Recovery

Once detected, we must recover:

### Process Termination
1. **Abort all deadlocked processes**: Simple. Guaranteed to break deadlock. Expensive — all partial work lost.
2. **Abort one at a time**: Abort one process, re-run detection algorithm, repeat until deadlock is broken. Which to abort? Use cost function:
   - Process priority
   - How long it has been running / how much longer it needs
   - How many resources it holds
   - How many resources it needs to complete
   - Whether process is interactive or batch
   - How many processes must be aborted

### Resource Preemption
Forcibly take resources from some processes and give them to deadlocked processes.

Three issues:
1. **Selecting a victim**: Minimize cost (same factors as above).
2. **Rollback**: The process that had its resource preempted must be rolled back to a safe state (usually just restarted from the beginning, since partial-rollback is complex).
3. **Starvation**: The same process might always be chosen as victim. Solution: include the number of times a process has been rolled back in the cost function.

---

## 8. Livelock and Starvation

**Livelock**: Processes are NOT blocked — they are actively running — but they make no progress. Like two people in a corridor who keep stepping aside in the same direction to let the other pass.

Example: Process A and B both check for deadlock. A detects conflict, backs off and waits 1 second. B does the same thing simultaneously. Both back off at the same time, both retry simultaneously, both back off again. Livelock.

**Livelock vs Deadlock:**
| | Deadlock | Livelock |
|-|----------|----------|
| State | Blocked | Running |
| CPU usage | 0% | 100% (wasted) |
| Progress | None | None |

**Fix for livelock**: Randomized backoff (retry after a random delay, not a fixed delay). Used in Ethernet's CSMA/CD protocol.

**Starvation**: A process is perpetually denied resources it needs, not because of deadlock (it can eventually get them in principle) but because other processes always get priority. Example: a low-priority process in an SJF system where short processes keep arriving. Starvation is not deadlock — the process is in the ready or waiting state, not in a circular block — but it never runs.
