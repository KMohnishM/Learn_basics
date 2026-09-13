# Q&A — Process Synchronization

---

## 🟢 Easy

**Q1. What is a race condition? Give a real example.**

A race condition is when the result of a computation depends on the non-deterministic order in which concurrent processes execute, leading to unpredictable outcomes.

Example: Two bank threads both read balance=$100, both add $50, both write $150. The final balance is $150 instead of $200 — one update is lost. Or: two users simultaneously book the last seat on a flight — both see "1 seat available," both book, the system now has -1 seats.

---

**Q2. What are the three requirements for a correct critical section solution?**

1. **Mutual Exclusion**: At most one process in the critical section at any time.
2. **Progress**: If no process is in the CS and some want to enter, the decision of who enters next cannot be postponed indefinitely. (No deadlock.)
3. **Bounded Waiting**: There is a bound on how many times others can enter the CS after a process has requested entry. (No starvation.)

---

**Q3. What is the difference between a semaphore and a mutex?**

| | Semaphore | Mutex |
|-|-----------|-------|
| **Value** | Integer (0 to N) | Binary (locked/unlocked) |
| **Ownership** | None — any thread can signal | Owned — only acquirer can release |
| **Use case** | Resource counting (pool of N), signaling between threads | Mutual exclusion only |
| **Example** | 3 DB connections: semaphore=3 | Protecting a shared counter |

A binary semaphore (initial value=1) is similar to a mutex but without ownership semantics.

---

**Q4. What is busy-waiting? When is it acceptable?**

Busy-waiting (spinning) is when a thread continuously checks a condition in a loop without yielding the CPU:
```c
while (lock != FREE);  // Spinning
```

**When acceptable**: On multicore systems for very short waits (microseconds). The lock-holder is running on another core and will release soon. The overhead of a context switch might exceed the time spent spinning.

**When unacceptable**: On single-core (the lock holder can't run while spinner holds the CPU) or for long waits (wastes entire CPU on no useful work).

---

**Q5. What is a monitor and what does it guarantee?**

A monitor is a high-level synchronization construct combining shared data, operations on that data, and automatic mutual exclusion. At most one thread executes inside a monitor at any time — the monitor's lock is acquired on entry and released on exit.

Java's `synchronized` method/block implements a monitor. The guarantee: no two threads execute synchronized methods of the same object simultaneously.

---

**Q6. What is the Dining Philosophers problem? Why does the naive solution deadlock?**

5 philosophers alternate thinking and eating. To eat, a philosopher needs two chopsticks (one on each side). There are exactly 5 chopsticks.

Naive solution: each philosopher picks left chopstick, then right. If all pick left simultaneously, all are holding one chopstick and waiting for the right — circular wait → deadlock. No philosopher can proceed.

---

## 🟡 Medium

**Q7. Why does Peterson's solution fail on modern hardware?**

Peterson's solution relies on the sequence `flag[i] = true; turn = j;` being executed in that order. Modern CPUs and compilers reorder instructions for performance (out-of-order execution, store buffers). The CPU might execute `turn = j` before `flag[i] = true`. If both processes observe the reordered sequence simultaneously, mutual exclusion breaks.

**Fix**: Insert a **memory barrier/fence instruction** (`mfence` on x86, `DMB` on ARM) between the two statements. This forces all previous writes to be visible to other cores before proceeding. Memory barriers are expensive, which is why high-performance code minimizes them.

---

**Q8. Explain the Bounded Buffer semaphore solution. What happens if you swap the order of `wait(mutex)` and `wait(empty)` in the producer?**

The correct producer:
```c
wait(empty);   // Step 1: Wait for space
wait(mutex);   // Step 2: Acquire lock
// add item
signal(mutex); // Step 3: Release lock
signal(full);  // Step 4: Signal consumers
```

If swapped to `wait(mutex)` then `wait(empty)`:
- Producer acquires mutex first
- Buffer is full → producer blocks on `wait(empty)`
- Consumer needs mutex to remove an item → consumer blocks on `wait(mutex)`
- **Deadlock**: producer holds mutex, waits for consumer; consumer waits for mutex held by producer.

The rule: always `wait` on resource semaphores before `wait` on mutex semaphores.

---

**Q9. What is Priority Inversion? How does Priority Inheritance solve it?**

**Priority Inversion**: A high-priority task H is blocked waiting for a mutex held by a low-priority task L. A medium-priority task M (which doesn't need the mutex) preempts L. Now M runs while H (highest priority) is blocked — effective priority is inverted.

**Priority Inheritance**: When H blocks on a mutex held by L, the OS temporarily raises L's priority to H's priority. L now runs at H's priority, completes quickly, releases the mutex, and reverts to its original priority. H acquires the mutex and proceeds.

Real impact: The Mars Pathfinder spacecraft (1997) experienced this bug and reset repeatedly. Priority inheritance was enabled via a command from Earth to fix it.

---

**Q10. Describe the Readers-Writers problem and explain why the first solution can starve writers.**

The Readers-Writers problem: Multiple readers can read simultaneously (read doesn't modify data), but a writer needs exclusive access.

**First solution (readers preference)**:
- When a reader arrives, it checks reader_count. If it's the first reader, it acquires `rw_mutex` (blocking any writer). Subsequent readers just increment reader_count without blocking.
- Writers acquire `rw_mutex` exclusively.

**Starvation of writers**: If readers arrive continuously (never a moment with 0 readers), the last reader never calls `signal(rw_mutex)`, and writers wait indefinitely. In a busy read-heavy system, writers may never get access.

**Second solution (writers preference)**: When a writer is waiting, no new reader is allowed to start. This prevents writer starvation but can starve readers.

**Fair solution**: Use a FIFO queue — readers and writers are served in arrival order. Uses additional semaphores to track the queue.

---

**Q11. What is `compare_and_swap` (CAS) and how is it used to build a lock?**

CAS is an atomic CPU instruction:
```c
// Atomically: if *value == expected, set *value = new_value, return old *value
int CAS(int *value, int expected, int new_value);
```

Building a spinlock:
```c
int lock = 0;  // 0 = free, 1 = locked

// Acquire:
while (CAS(&lock, 0, 1) != 0);  // Spin until we atomically change 0→1
// CRITICAL SECTION
lock = 0;  // Release (atomic store on x86)
```

CAS is used in lock-free data structures (compare-and-swap to update a pointer/counter only if it hasn't changed since we read it). If another thread modified it, retry. No locks needed.

---

## 🔴 Hard

**Q12. Why must we use a `while` loop instead of `if` when checking condition variables in monitors?**

```java
// WRONG:
synchronized void consume() {
    if (count == 0) wait();     // Bug!
    // consume item
}

// CORRECT:
synchronized void consume() {
    while (count == 0) wait();  // Safe
    // consume item
}
```

**Mesa semantics** (Java, POSIX pthreads): When a thread is woken from `wait()`, it is moved to the set of threads competing for the monitor lock. By the time it re-acquires the lock, the condition it was waiting for might **no longer be true** — another thread (running between the notify and the woken thread re-acquiring) might have already consumed the item.

With `if`: thread wakes, doesn't re-check, tries to consume from an empty buffer → bug.
With `while`: thread wakes, re-checks, finds buffer empty, calls `wait()` again → safe.

**Spurious wakeups**: Some OS implementations (e.g., Linux pthreads) may wake a thread from `wait()` even when no `signal` was called (due to signal interrupts or OS-level behavior). The `while` loop correctly handles these too.

---

**Q13. Show that the naive Dining Philosophers solution deadlocks, then give two complete solutions.**

**Deadlock proof**: Consider all 5 philosophers picking up their left chopstick simultaneously. Philosopher 0 holds chopstick[0], philosopher 1 holds chopstick[1], ..., philosopher 4 holds chopstick[4]. Each is waiting for their right chopstick. Philosopher 0 waits for chopstick[1] (held by philosopher 1), who waits for chopstick[2], ..., who waits for chopstick[0]. Circular wait — all 4 Coffman conditions are met → guaranteed deadlock.

**Solution 1 — Asymmetric pickup:**
```c
if (i % 2 == 0) {
    wait(chopstick[i]);           // Even: left first
    wait(chopstick[(i+1)%5]);
} else {
    wait(chopstick[(i+1)%5]);    // Odd: right first
    wait(chopstick[i]);
}
```
Philosopher 4 (even) picks left=4 then right=0. Philosopher 3 (odd) picks right=4 first. They compete for chopstick[4], so at most one of them gets it — the circular wait is broken.

**Solution 2 — At most 4 at the table:**
```c
semaphore table_seats = 4;  // At most 4 philosophers at the table

// Philosopher i:
wait(table_seats);          // Must get a seat first
wait(chopstick[i]);
wait(chopstick[(i+1)%5]);
// eat
signal(chopstick[i]);
signal(chopstick[(i+1)%5]);
signal(table_seats);
```
With at most 4 philosophers competing for 5 chopsticks, at least one philosopher always has both chopsticks available. Deadlock impossible.

---

**Q14. Explain how `wait()` and `signal()` on semaphores avoid busy-waiting, and what happens to the blocked process.**

```c
// Semaphore S with wait queue:
typedef struct {
    int value;
    struct process *queue;  // List of blocked processes
} semaphore;

wait(S):
    S.value--;
    if (S.value < 0) {
        // Process enters blocked state
        add this process to S.queue;
        block();   // Context switch — this process sleeps in kernel
    }

signal(S):
    S.value++;
    if (S.value <= 0) {
        // Someone is waiting
        remove process P from S.queue;
        wakeup(P);   // Move P from blocked → ready queue
    }
```

When `block()` is called:
1. The kernel changes the process's state from Running → Waiting.
2. The process is placed in the semaphore's wait queue.
3. A context switch happens — another process gets the CPU.
4. The blocked process consumes NO CPU while waiting.

When `wakeup(P)` is called:
1. P is removed from the wait queue.
2. P's state changes from Waiting → Ready.
3. P is placed in the CPU ready queue.
4. P will eventually be scheduled and resume after the `block()` call.

This is much more efficient than spinning for long waits — the CPU is available for other work while the process sleeps.
