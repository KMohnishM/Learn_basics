# Module 2: CPU Scheduling

---

## 1. Why Scheduling?

At any moment, multiple processes are in the **ready state** — they have work to do and are waiting for CPU time. The CPU can only run one process at a time on a single core. The **CPU scheduler** (short-term scheduler) decides which ready process runs next and for how long.

Scheduling is one of the most consequential OS decisions because:
- A bad scheduling decision blocks every process waiting behind the chosen one
- Interactive systems need low response time (milliseconds), batch systems need high throughput
- Multicore systems add further complexity (which core runs which process?)

---

## 2. Types of Schedulers

| Scheduler | Also Called | Frequency | Job |
|-----------|-------------|-----------|-----|
| **Long-term** | Job scheduler | Seconds–minutes | Decides which jobs enter the ready queue from the job pool. Controls **degree of multiprogramming** (how many processes are in memory at once). |
| **Medium-term** | Swapper | Seconds | Swaps processes between memory and disk to manage memory pressure. Removes a process from memory (swap out) when memory is tight; brings it back (swap in) when conditions improve. |
| **Short-term** | CPU scheduler | Milliseconds | Selects the next ready process to run on the CPU. The most frequent — runs every few milliseconds. |

**Dispatch latency**: the time from the scheduler selecting a process to that process actually running (save old process's state, load new process's state). Should be minimized.

---

## 3. Scheduling Criteria

Different scenarios need different objectives. No algorithm is optimal for all criteria simultaneously — this is why many algorithms exist.

| Criterion | Description | Optimize Direction |
|-----------|-------------|-------------------|
| **CPU Utilization** | % of time CPU is busy | Maximize (target 40–90%) |
| **Throughput** | Processes completed per unit time | Maximize |
| **Turnaround Time** | Total time from submission to completion | Minimize |
| **Waiting Time** | Total time in the ready queue | Minimize |
| **Response Time** | Time from request to first response | Minimize (critical for interactive) |
| **Fairness** | Each process gets fair CPU share | Guarantee |

**Key formulas:**
- Turnaround Time = Completion Time − Arrival Time
- Waiting Time = Turnaround Time − Burst Time
- Response Time = Time of First CPU Allocation − Arrival Time

---

## 4. Preemptive vs Non-Preemptive Scheduling

**Non-preemptive**: Once a process starts running, it runs until it either terminates or voluntarily blocks (e.g., waits for I/O). The CPU cannot be forcibly taken away.
- Simple to implement, no race conditions in the kernel
- Bad for interactive systems — a long process can monopolize the CPU

**Preemptive**: The OS can forcibly remove a process from the CPU (via a timer interrupt or when a higher-priority process becomes ready).
- Required for real-time and interactive systems
- Creates race conditions in the kernel when processes share data — kernel must protect critical sections

---

## 5. First-Come, First-Served (FCFS)

**Algorithm**: Processes are served in the order they arrive in the ready queue (FIFO queue). Non-preemptive.

**Example:**

| Process | Arrival | Burst |
|---------|---------|-------|
| P1 | 0 | 24 |
| P2 | 1 | 3 |
| P3 | 2 | 3 |

Gantt chart: `P1 (0-24) | P2 (24-27) | P3 (27-30)`

- P1 waiting time = 0
- P2 waiting time = 23 (arrived at 1, started at 24)
- P3 waiting time = 25

Average waiting time = (0 + 23 + 25) / 3 = **16 ms**

**Convoy Effect**: Short processes are stuck behind one long process. In the example, P2 and P3 (3ms each) wait 23–25ms because P1 (24ms) goes first. This is the fundamental problem with FCFS.

**When to use**: Batch systems where all jobs have similar burst times and response time doesn't matter.

---

## 6. Shortest Job First (SJF)

**Algorithm**: Always run the process with the shortest next CPU burst. **Provably optimal for minimizing average waiting time** among all non-preemptive algorithms.

Using the same example but reordered:
Gantt chart: `P1 (0-24) | P2 (24-27) | P3 (27-30)` — same! P1 must run first since P2 and P3 haven't arrived yet.

If all arrived at time 0:
Gantt chart: `P2 (0-3) | P3 (3-6) | P1 (6-30)` — Average waiting = (6 + 0 + 3)/3 = 3ms vs FCFS 16ms.

**The fundamental problem with SJF**: We don't know the next CPU burst length in advance. We can only estimate it.

**CPU Burst Prediction — Exponential Averaging:**

$$\tau_{n+1} = \alpha \cdot t_n + (1 - \alpha) \cdot \tau_n$$

Where:
- $t_n$ = actual length of the $n$-th CPU burst
- $\tau_n$ = predicted length of the $n$-th CPU burst
- $\alpha$ ∈ [0,1] controls how much weight recent history gets

Typically $\alpha = 0.5$: equal weight to recent actual burst and previous prediction. Higher $\alpha$ = more reactive, lower $\alpha$ = more smooth/predictable.

**Starvation**: A long process may wait indefinitely if there's always a shorter process arriving. Solution: **aging** (increase priority as wait time increases).

---

## 7. Shortest Remaining Time First (SRTF)

**Algorithm**: Preemptive version of SJF. When a new process arrives in the ready queue, if its burst time is less than the remaining time of the currently running process, preempt the running process.

**Example:**

| Process | Arrival | Burst |
|---------|---------|-------|
| P1 | 0 | 8 |
| P2 | 1 | 4 |
| P3 | 2 | 9 |
| P4 | 3 | 5 |

Gantt: `P1(0-1) | P2(1-5) | P4(5-10) | P1(10-17) | P3(17-26)`

- P1: arrives 0, gets preempted at t=1 (P2 arrives with 4 < 7 remaining). Runs 10-17. Turnaround = 17-0=17, Wait = 17-8=9
- P2: arrives 1, runs 1-5. Turnaround = 5-1=4, Wait = 0
- P3: arrives 2, runs 17-26. Turnaround = 26-2=24, Wait = 24-9=15
- P4: arrives 3, runs 5-10. Turnaround = 10-3=7, Wait = 7-5=2

Average waiting = (9+0+15+2)/4 = **6.5ms** — better than any non-preemptive algorithm.

---

## 8. Priority Scheduling

**Algorithm**: Each process has a priority number. The CPU is given to the process with the highest priority (smallest number = highest priority by convention, though this varies).

**Problem: Starvation (Indefinite Blocking)**: A low-priority process may never run if there are always higher-priority processes ready. In 1973, MIT's IBM 7094 was shut down and low-priority jobs submitted in 1967 were found waiting — they had never run in 6 years.

**Solution: Aging**: Gradually increase the priority of processes that have been waiting a long time. A process that has waited 15 minutes might get a priority boost of +1 every minute, ensuring it eventually reaches the highest priority.

**Internal vs External Priority**:
- Internal: Set by the OS based on measurable quantities (time limits, memory requirements, I/O to CPU burst ratio)
- External: Set by the user or administrator

---

## 9. Round Robin (RR)

**Algorithm**: Each process gets a fixed-size time slice (**time quantum** or **time slice**), typically 10–100ms. After the quantum expires, the process is preempted and put at the back of the FIFO ready queue.

**Time quantum choice is critical:**

- **Too small** (e.g., 1ms): Context switches happen extremely frequently. If context switch costs 1ms and quantum is 1ms, 50% of CPU time is wasted on context switches.
- **Too large** (e.g., 1 second): Degenerates into FCFS. Poor response time for interactive processes.
- **Rule of thumb**: 80% of CPU bursts should be shorter than the time quantum. Typical modern values: 10–100ms.

**Response time with RR**: With n processes and quantum q, any process waits at most (n-1)×q time before getting its next turn.

**Example (q=4):**

| Process | Burst |
|---------|-------|
| P1 | 24 |
| P2 | 3 |
| P3 | 3 |

Gantt: `P1(0-4) | P2(4-7) | P3(7-10) | P1(10-14) | P1(14-18) | P1(18-22) | P1(22-26) | P1(26-30)`

- P2 finishes at 7: Turnaround=7, Wait=4
- P3 finishes at 10: Turnaround=10, Wait=7
- P1 finishes at 30: Turnaround=30, Wait=6

Average waiting = (6+4+7)/3 = **5.67ms**

---

## 10. Multilevel Queue Scheduling

**Algorithm**: Processes are permanently assigned to a queue based on type. Each queue has its own scheduling algorithm. Queues have strict priorities relative to each other.

**Example structure:**
```
Priority 1 (Highest): System processes (RR, q=1ms)
Priority 2:           Interactive processes (RR, q=10ms)
Priority 3:           Interactive editing processes (RR, q=10ms)
Priority 4:           Batch processes (FCFS)
Priority 5 (Lowest):  Student jobs (FCFS)
```

**Problem**: Starvation — lower-priority queues may never get CPU if higher-priority queues are always non-empty. There's no movement between queues.

---

## 11. Multilevel Feedback Queue (MLFQ)

**Algorithm**: Like multilevel queue, but processes can **move between queues** based on their behavior. This is the **most general** scheduling algorithm and is used in practice (BSD Unix, Solaris, Windows, Linux before CFS).

**Rules:**
1. A new process enters the highest priority queue.
2. If it uses its full time quantum without blocking, it's moved down to a lower-priority queue (longer quantum, lower priority). This penalizes CPU-bound processes.
3. If it blocks before using its full quantum (I/O-bound behavior), it stays at the same level or moves up. I/O-bound processes are rewarded.
4. Aging: if a process waits too long in a low-priority queue, boost it to a higher queue.

**Why it works**: CPU-bound processes naturally sink to lower queues (long bursts, use full quantum). I/O-bound/interactive processes naturally stay at top (short bursts, yield CPU before quantum expires). Interactive processes get fast response time; long batch jobs get CPU when queues are empty.

**Parameters** (configurable): number of queues, quantum per queue, promotion/demotion rules — makes MLFQ highly tunable.

---

## 12. Real-Time Scheduling

**Hard real-time**: Missing a deadline is a catastrophic system failure (airbag deployment, pacemaker, nuclear reactor control). Must guarantee deadlines.

**Soft real-time**: Missing a deadline degrades performance but is not catastrophic (video streaming, VoIP). Missing a frame is annoying but not dangerous.

### Rate Monotonic Scheduling (RMS)
- Fixed-priority algorithm for periodic tasks
- **Rule**: shorter period = higher priority (inversely proportional)
- Tasks with shorter deadlines run more often and must complete before tasks with longer deadlines
- **CPU Utilization bound**: n tasks can be scheduled if $U = \sum_{i=1}^n \frac{C_i}{T_i} \leq n(2^{1/n}-1)$
  - As n → ∞, this bound approaches ln(2) ≈ 0.693 (i.e., 69.3% max utilization)

### Earliest Deadline First (EDF)
- Dynamic priorities: the task with the closest deadline has the highest priority
- **Theoretically optimal** for uniprocessors: can achieve 100% CPU utilization
- More complex to implement than RMS

---

## 13. Multiprocessor Scheduling

When you have multiple CPUs/cores, the scheduling problem gets more complex.

**Symmetric Multiprocessing (SMP)**: Each processor self-schedules. All processors share a single ready queue or each has its own private queue.

**Asymmetric Multiprocessing**: One master processor handles scheduling decisions and I/O processing; other processors execute user code only.

### Processor Affinity
Moving a process from one CPU to another invalidates the warm cache on the original CPU (the new CPU must re-fetch all cached data). This is expensive.

- **Soft affinity**: OS tries to keep a process on the same CPU but doesn't guarantee it.
- **Hard affinity**: Process is bound to a specific CPU — never migrated (Linux `taskset` command).

### Load Balancing
For SMP, we want all CPUs to be equally busy. Load balancing keeps the ready queues across CPUs equal.

- **Push migration**: A separate task periodically checks load across CPUs. If imbalanced, it pushes processes from overloaded CPUs to underloaded ones.
- **Pull migration**: An idle CPU pulls a process from a busy CPU's queue.

**NUMA (Non-Uniform Memory Access)**: In systems with multiple memory banks (each near a CPU socket), accessing memory local to your CPU is faster. The scheduler should place a process on the CPU that is local to the process's memory — called **NUMA-aware scheduling**.

---

## 14. Linux CFS (Completely Fair Scheduler)

Since Linux 2.6.23, the default scheduler. Not a traditional round-robin or MLFQ — it's based on a **fair-share** model.

**Core idea**: Every process should receive exactly $\frac{1}{n}$ of the CPU time (where n = number of runnable processes). CFS tracks each process's **virtual runtime** (vruntime) — how much CPU time it has actually received, weighted by priority.

**vruntime**: When a process runs for `delta_exec` nanoseconds, its vruntime increases by:
$$vruntime += delta\_exec \times \frac{weight_{nice=0}}{weight_{process}}$$

Higher priority (lower nice value) → smaller weight divisor → vruntime increases slower → process stays at the front of the queue longer → gets more CPU.

**Data Structure**: CFS maintains all runnable processes in a **red-black tree** keyed by vruntime. The leftmost node (smallest vruntime) is always the next process to run — it has received the least CPU time relative to its entitlement.

**Nice values**: Range from -20 (highest priority) to +19 (lowest priority). Each step multiplies/divides the effective weight by ~1.25.

**Targeted latency**: CFS aims to give every process one run within the "targeted latency" period (default 6–48ms depending on number of processes). If there are 4 processes, each gets 1/4 of the targeted latency as its time slice.

**Minimum granularity**: Minimum time slice (default 0.75ms) to prevent excessive context switching when there are many processes.

---

## 15. Gantt Chart Calculations

For any scheduling exam/interview question:

**Turnaround Time (TAT)** = Completion Time − Arrival Time

**Waiting Time (WT)** = Turnaround Time − Burst Time = Time spent in ready queue

**Response Time (RT)** = First CPU Allocation Time − Arrival Time (different from WT for preemptive algorithms!)

**Average Waiting Time** = Σ(WT_i) / n

**CPU Utilization** = Total Burst Time / Total Time × 100%
