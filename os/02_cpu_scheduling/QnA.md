# Q&A — CPU Scheduling

---

## 🟢 Easy

**Q1. What is the role of the CPU scheduler?**

The CPU scheduler (short-term scheduler) selects which process from the ready queue gets the CPU next. It runs extremely frequently — on every context switch, timer interrupt, or blocking call — and its decision directly impacts system responsiveness and throughput.

---

**Q2. What is the difference between preemptive and non-preemptive scheduling?**

- **Non-preemptive**: A running process keeps the CPU until it voluntarily gives it up (terminates or blocks on I/O). Simple but bad for interactive systems — one long process can freeze everything else.
- **Preemptive**: The OS can forcibly take the CPU away from a running process (via timer interrupt or when a higher-priority process arrives). Required for responsiveness. Creates the need for synchronization primitives because kernel data structures can be accessed by concurrent processes.

---

**Q3. What is the Convoy Effect in FCFS? Give an example.**

The Convoy Effect occurs when short processes are stuck waiting behind one long process, like cars queuing behind a slow truck on a one-lane road.

Example: P1 has a 30ms burst, P2 and P3 have 2ms bursts. If all arrive at time 0 and P1 goes first (FCFS), P2 and P3 wait 30ms each to do 2ms of work. Average waiting time = (0+30+32)/3 = 20.67ms. With SJF (P2→P3→P1), average waiting = (0+2+4)/3 = 2ms.

---

**Q4. Why is SJF theoretically optimal? What makes it impractical?**

**Optimal**: SJF minimizes average waiting time because running shorter jobs first means fewer processes wait for fewer long jobs. Proven mathematically: any reordering that puts a shorter job after a longer job increases the waiting time of that shorter job.

**Impractical**: The OS doesn't know the next CPU burst length in advance. We can only estimate it using exponential averaging of past behavior, which may be inaccurate.

---

**Q5. What is Response Time and how is it different from Waiting Time?**

- **Waiting Time**: Total time a process spends in the ready queue across all its visits to the queue. It doesn't include time spent blocked on I/O.
- **Response Time**: Time from the process's first submission until it first gets on the CPU.

For non-preemptive algorithms (FCFS, SJF), Response Time = first Waiting Time (same thing).
For preemptive algorithms (RR), they can differ. Example: RR gives every process a quick first response (fast RT) but they still accumulate waiting time across multiple rounds.

---

**Q6. What does the `nice` value represent in Linux?**

The `nice` value ranges from -20 (highest priority) to +19 (lowest priority). A lower nice value means the process is more aggressive about getting CPU time. The CFS scheduler converts nice values to **weights** — each unit of nice decreases/increases weight by factor ~1.25. A nice=-20 process gets about 88× more CPU than a nice=+19 process.

Unprivileged users can increase (worsen) their nice value but not decrease (improve) it without root privileges.

---

## 🟡 Medium

**Q7. Calculate average waiting time for these processes using FCFS and SJF (non-preemptive). All arrive at time 0.**

| Process | Burst Time |
|---------|-----------|
| P1 | 6 |
| P2 | 8 |
| P3 | 7 |
| P4 | 3 |

**FCFS** (order: P1, P2, P3, P4):
Gantt: `P1(0-6) | P2(6-14) | P3(14-21) | P4(21-24)`
- P1 WT = 0, P2 WT = 6, P3 WT = 14, P4 WT = 21
- **Average WT = (0+6+14+21)/4 = 10.25ms**

**SJF** (order: P4, P1, P3, P2):
Gantt: `P4(0-3) | P1(3-9) | P3(9-16) | P2(16-24)`
- P4 WT = 0, P1 WT = 3, P3 WT = 9, P2 WT = 16
- **Average WT = (0+3+9+16)/4 = 7ms**

SJF is better by 3.25ms.

---

**Q8. Consider these processes with Round Robin (quantum = 2). Calculate the Gantt chart and average waiting time.**

| Process | Arrival | Burst |
|---------|---------|-------|
| P1 | 0 | 5 |
| P2 | 1 | 3 |
| P3 | 2 | 1 |
| P4 | 3 | 2 |

**Simulation step by step:**
- t=0: Queue=[P1]. Run P1 for 2. Remaining P1=3.
- t=2: Queue=[P2,P3,P1] (P2 arrived at 1, P3 at 2, P1 back). Run P2 for 2. Remaining P2=1.
- t=4: Queue=[P3,P1,P4,P2] (P4 arrived at 3). Run P3 for 1. P3 done.
- t=5: Queue=[P1,P4,P2]. Run P1 for 2. Remaining P1=1.
- t=7: Queue=[P4,P2,P1]. Run P4 for 2. P4 done.
- t=9: Queue=[P2,P1]. Run P2 for 1. P2 done.
- t=10: Queue=[P1]. Run P1 for 1. P1 done.

Gantt: `P1(0-2)|P2(2-4)|P3(4-5)|P1(5-7)|P4(7-9)|P2(9-10)|P1(10-11)`

Waiting times (TAT - Burst):
- P1: TAT=11-0=11, WT=11-5=**6**
- P2: TAT=10-1=9, WT=9-3=**6**
- P3: TAT=5-2=3, WT=3-1=**2**
- P4: TAT=9-3=6, WT=6-2=**4**

**Average WT = (6+6+2+4)/4 = 4.5ms**

---

**Q9. What is the Multilevel Feedback Queue? How does it adapt to process behavior?**

MLFQ has multiple queues with decreasing priority and increasing time quantum. New processes enter the highest-priority queue.

**CPU-bound process adaptation**: A process that uses its full quantum each time gets demoted to a lower-priority queue (longer quantum, less frequent execution). This is good — CPU-bound jobs don't need fast response time, they need throughput.

**I/O-bound process adaptation**: A process that blocks before its quantum expires (voluntarily yields for I/O) stays in or moves up to a higher-priority queue. I/O-bound/interactive processes get priority, ensuring low response time.

**Aging**: If a process waits too long in a low-priority queue, it gets boosted upward. Prevents starvation of any process.

This self-tuning behavior is why MLFQ is used in real OSes — no prior knowledge of process behavior is needed.

---

**Q10. What is processor affinity and why does it matter?**

Processor affinity means keeping a process on the same CPU across context switches.

When a process runs on CPU 0, that CPU's cache fills with the process's data. If the process is then migrated to CPU 1, CPU 1's cache is cold — every memory access misses the cache and must go to RAM. This **cache invalidation overhead** can slow the process significantly.

- **Soft affinity**: Scheduler tries to keep process on same CPU but migrates if load balance requires it.
- **Hard affinity**: Process is pinned to a specific CPU (`taskset` on Linux) — never migrated regardless of load balance.

Hard affinity is used in real-time systems and HPC where cache warmth is critical.

---

**Q11. Why does increasing the time quantum in Round Robin improve throughput but hurt response time?**

**Throughput**: With a larger quantum, each process gets a longer uninterrupted run. Fewer context switches occur per unit time. Since context switches are pure overhead, throughput (useful work per second) increases.

**Response Time**: With a larger quantum, a new process might have to wait up to (n-1)×q time before its first CPU access. If q=1 second and there are 10 processes, a new process waits up to 9 seconds before getting any response. Interactive systems need q ≤ 100ms.

The tradeoff: **large q = fewer context switches = better throughput = worse response time**. **Small q = more context switches = worse throughput = better response time**. The sweet spot is a quantum where 80% of CPU bursts complete within one quantum (so most processes run to completion in one turn, behaving like SJF, but the minority of long processes are still preemptive).

---

## 🔴 Hard

**Q12. Solve this SRTF (preemptive SJF) problem. Compute average waiting time.**

| Process | Arrival | Burst |
|---------|---------|-------|
| P1 | 0 | 8 |
| P2 | 1 | 4 |
| P3 | 2 | 9 |
| P4 | 3 | 5 |

**Step-by-step:**
- t=0: Only P1 available. Run P1. Remaining=8.
- t=1: P2 arrives (burst=4). P1 remaining=7. 4 < 7, preempt P1. Run P2.
- t=2: P3 arrives (burst=9). P2 remaining=3. 9 > 3, don't preempt.
- t=3: P4 arrives (burst=5). P2 remaining=2. 5 > 2, don't preempt.
- t=5: P2 done. Ready: P1(7), P3(9), P4(5). Min=P4. Run P4.
- t=10: P4 done. Ready: P1(7), P3(9). Min=P1. Run P1.
- t=17: P1 done. Run P3.
- t=26: P3 done.

Gantt: `P1(0-1)|P2(1-5)|P4(5-10)|P1(10-17)|P3(17-26)`

TAT and WT:
- P1: TAT=17-0=17, WT=17-8=**9**
- P2: TAT=5-1=4, WT=4-4=**0**
- P3: TAT=26-2=24, WT=24-9=**15**
- P4: TAT=10-3=7, WT=7-5=**2**

**Average WT = (9+0+15+2)/4 = 6.5ms**

---

**Q13. What is the RMS utilization bound? Why can't it reach 100%?**

Rate Monotonic Scheduling's CPU utilization bound for n tasks is:

$$U_{bound} = n \times (2^{1/n} - 1)$$

| n tasks | Bound |
|---------|-------|
| 1 | 100% |
| 2 | 82.8% |
| 3 | 78.0% |
| 4 | 75.7% |
| → ∞ | ln(2) ≈ 69.3% |

**Why not 100%?** RMS assigns static priorities based solely on period. With arbitrary periods, certain combinations create situations where a lower-priority long-period task is interrupted by multiple higher-priority short-period tasks at exactly the wrong moments, causing it to miss its deadline. The bound guarantees schedulability without that scenario — if utilization ≤ bound, all deadlines are always met. EDF (dynamic priorities) can achieve 100% utilization but is more complex.

---

**Q14. A system runs with Round Robin (q=10ms). Context switch costs 1ms. If the average process runs for 8ms before blocking, what percentage of CPU time is wasted on context switches?**

With q=10ms and average burst = 8ms, most processes will **block before** the quantum expires (since 8ms < 10ms). So the typical cycle is:

Process runs 8ms → blocks (I/O or voluntary yield) → context switch (1ms) → next process

Time per cycle = 8ms (useful) + 1ms (overhead) = 9ms  
Overhead percentage = 1/9 × 100% = **11.1%**

If instead the average burst were 100ms and q=10ms:
Each quantum cycle = 10ms + 1ms = 11ms  
Overhead = 1/11 × 100% = **9.1%**

The key insight: **overhead% = context_switch_cost / (quantum + context_switch_cost)** when processes always use the full quantum.

---

**Q15. How does Linux CFS handle a compute-intensive process competing with an interactive process? Walk through the vruntime mechanism.**

Say P1 (compute-intensive, nice=0, weight=1024) and P2 (interactive shell, nice=-5, weight=3121) are running.

CFS always picks the process with the **smallest vruntime** (the one that has received the least CPU time, weighted by priority).

When P2 runs for Δt ms:
- vruntime_P2 += Δt × (1024/3121) ≈ Δt × 0.328

When P1 runs for Δt ms:
- vruntime_P1 += Δt × (1024/1024) = Δt

Because P2's vruntime grows slower (3× slower), P2 is re-selected more often. Over a period of 1 second, P2 gets ~75% of CPU and P1 gets ~25% (proportional to their weights).

When P2 blocks on a keypress (enters I/O wait), it's removed from the red-black tree. When it wakes up (key is pressed), CFS caps its vruntime to (min_vruntime - targeted_latency) so it doesn't suddenly "own" the CPU for a huge burst. P2 gets back on CPU quickly (low vruntime = leftmost in tree) — giving the interactive user fast response.

This is why CFS naturally gives fast response to I/O-bound interactive processes while giving compute-intensive processes fair CPU time when the interactive processes are sleeping.
