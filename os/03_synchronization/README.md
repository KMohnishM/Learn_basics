# Module 3: Process Synchronization

---

## 1. The Race Condition Problem

A **race condition** occurs when two or more processes/threads access shared data concurrently, and the final result depends on the order in which they execute — the order of which is non-deterministic.

**Classic Example — Counter Increment:**

Two threads both execute `counter++` (where `counter` starts at 5):

At the machine-code level, `counter++` is NOT atomic. It compiles to three instructions:
```
LOAD R1, counter    ; R1 = 5
ADD  R1, 1          ; R1 = 6
STORE counter, R1   ; counter = 6
```

If Thread A and Thread B interleave:
```
Thread A: LOAD R1, counter    → R1_A = 5
Thread B: LOAD R1, counter    → R1_B = 5
Thread A: ADD R1, 1           → R1_A = 6
Thread B: ADD R1, 1           → R1_B = 6
Thread A: STORE counter, R1   → counter = 6
Thread B: STORE counter, R1   → counter = 6   ← WRONG! Should be 7
```

Both threads read 5, both write 6. The increment from Thread A is lost.

This is a race condition. The result is unpredictable — sometimes you get 7 (correct), sometimes 6 (lost update), depending on the precise scheduling.

---

## 2. The Critical Section Problem

A **critical section** is any section of code that accesses shared resources (shared memory, files, hardware) that must not be executed by more than one process simultaneously.

**The three requirements** any correct solution must satisfy:

1. **Mutual Exclusion**: If process P_i is executing in its critical section, no other process may simultaneously be in its critical section.

2. **Progress**: If no process is in its critical section, and some processes want to enter, then only processes that are not in their remainder section (non-critical code) can participate in the decision of who enters next. This decision cannot be postponed indefinitely. (Prevents deadlock: no one can get in, yet someone wants to.)

3. **Bounded Waiting**: After a process has requested entry to its critical section, there must be a bound on the number of times other processes can enter the critical section before this process is allowed in. (Prevents starvation: one process waits forever.)

---

## 3. Peterson's Solution

Software-only solution for TWO processes that achieves all three requirements — on sequential hardware.

```c
// Shared variables:
int turn;          // Whose turn to enter CS
bool flag[2];      // flag[i] = true means process i wants to enter CS

// Process i's code (j = 1-i, i.e., the other process):
flag[i] = true;    // "I want to enter"
turn = j;          // "But you can go first"
while (flag[j] && turn == j);  // Wait if j wants in AND it's j's turn
// --- CRITICAL SECTION ---
flag[i] = false;   // "I'm done"
// --- REMAINDER SECTION ---
```

**Why it works:**
- **Mutual Exclusion**: To enter, both `flag[j] == false` OR `turn == i` must hold. If both try to enter simultaneously, both set flag = true, but only one can set `turn` last. The one who set `turn` last will spin; the other proceeds.
- **Progress**: If process j doesn't want in (`flag[j] == false`), i enters immediately.
- **Bounded Waiting**: If j is in the CS, `turn = j`. When j exits and sets `flag[j] = false`, i can proceed. j cannot re-enter before i (j sets turn=i in its next attempt).

**Why it fails on modern hardware**: Modern CPUs and compilers **reorder instructions** for optimization. The sequence `flag[i] = true; turn = j;` might be reordered to `turn = j; flag[i] = true;`. This reordering can break mutual exclusion. A **memory barrier** (or fence instruction) is needed to prevent reordering — Peterson's is now mainly theoretical.

---

## 4. Hardware Atomic Instructions

Modern CPUs provide atomic read-modify-write instructions that cannot be interrupted mid-execution:

### `test_and_set` (TAS)
```c
// Executes atomically at hardware level
bool test_and_set(bool *target) {
    bool rv = *target;
    *target = true;   // Always sets to true
    return rv;        // Returns old value
}

// Spinlock using TAS:
bool lock = false;   // Shared

// Acquire:
while (test_and_set(&lock));  // Spin until lock was false (we got it)
// CRITICAL SECTION
lock = false;        // Release
```

**Problem**: Doesn't guarantee bounded waiting — one process might be unlucky and always find the lock held.

### `compare_and_swap` (CAS)
```c
// Atomically: if *value == expected, set *value = new_value, return old
int compare_and_swap(int *value, int expected, int new_value) {
    int temp = *value;
    if (*value == expected)
        *value = new_value;
    return temp;
}

// Usage:
while (compare_and_swap(&lock, 0, 1) != 0);  // Acquire
// CRITICAL SECTION
lock = 0;  // Release
```

CAS is the foundation of **lock-free** data structures in modern concurrent programming (Java's `AtomicInteger`, C++'s `std::atomic`).

### Spinlocks vs Blocking Locks

**Spinlock** (busy-waiting): Thread loops continuously checking the lock.
- CPU is wasted while waiting
- **Best for**: short critical sections on multicore systems where the lock will be released very soon (microseconds). The cost of a context switch might be greater than the cost of spinning.

**Blocking lock (mutex)**: Thread is put to sleep (in the kernel's wait queue) until the lock is available.
- CPU can do other work while waiting
- **Best for**: long critical sections, or single-core systems where spinning wastes the only CPU.

---

## 5. Mutex Locks

A **mutex** (mutual exclusion lock) is a higher-level synchronization primitive built on hardware atomics.

```c
mutex_t lock;        // Initialized to "unlocked"

// Thread A:
pthread_mutex_lock(&lock);    // Acquire (blocks if locked)
// CRITICAL SECTION
pthread_mutex_unlock(&lock);  // Release

// Thread B:
pthread_mutex_lock(&lock);    // Blocks here until A releases
// CRITICAL SECTION
pthread_mutex_unlock(&lock);
```

**Key properties:**
- **Ownership**: The thread that acquires a mutex must be the one to release it.
- **Binary**: Locked or unlocked. At most one thread holds it at any time.
- **Non-recursive by default**: If the thread that holds the lock tries to acquire it again → **deadlock** (self-deadlock). Use recursive mutex if needed (but usually a design smell).

---

## 6. Semaphores

A **semaphore** is a synchronization primitive with an integer counter and two atomic operations:

- **`wait(S)` (also called P, down)**: Decrements S. If S becomes negative, block the calling process.
- **`signal(S)` (also called V, up)**: Increments S. If any process is waiting (S was negative), wake one up.

```
wait(S):
    S--;
    if (S < 0):
        add this process to S's wait queue
        block()    // sleep

signal(S):
    S++;
    if (S <= 0):   // There are processes waiting
        remove a process P from S's wait queue
        wakeup(P)
```

### Binary Semaphore (= Mutex)
Initial value = 1. Acts exactly like a mutex. One process at a time.

### Counting Semaphore
Initial value = N. Allows up to N processes in a section simultaneously. Used for resource pools.

**Example**: Semaphore initialized to 3 for a pool of 3 database connections. wait() decrements (acquires a connection). signal() increments (releases a connection). When S=0, no connections available; new requests block.

### Busy Waiting vs Sleep Queue
- **Busy-waiting implementation** (spinlock semaphore): Processes loop checking S. Wastes CPU.
- **Sleep-queue implementation** (shown above): Blocked processes sleep. OS wakes one when signal() is called. Preferred for OS-level semaphores.

---

## 7. Monitors

A **monitor** is a high-level synchronization construct that bundles:
- Shared data (variables)
- Procedures (methods) that operate on that data
- **Implicit mutual exclusion**: only ONE process can be active inside the monitor at any time

Java's `synchronized` keyword implements monitors.

```java
class BoundedBuffer {
    private final Object[] buffer;
    private int count, in, out;
    
    // Only one thread can execute ANY synchronized method at a time
    public synchronized void produce(Object item) throws InterruptedException {
        while (count == buffer.length)
            wait();   // Release lock, sleep, re-acquire when woken
        buffer[in] = item;
        in = (in + 1) % buffer.length;
        count++;
        notify();  // Wake a waiting consumer
    }
    
    public synchronized Object consume() throws InterruptedException {
        while (count == 0)
            wait();   // Sleep if nothing to consume
        Object item = buffer[out];
        out = (out + 1) % buffer.length;
        count--;
        notify();  // Wake a waiting producer
        return item;
    }
}
```

**Condition variables**: `wait()` and `notify()`/`notifyAll()` inside monitors.
- `wait()`: releases the monitor lock, puts thread in condition's wait set, blocks.
- `notify()`: wakes ONE thread from the condition's wait set. That thread must re-acquire the monitor lock before proceeding.
- `notifyAll()`: wakes ALL waiting threads. Each must compete to re-acquire the lock.

**Hoare vs Mesa semantics**: 
- **Hoare**: signaling thread suspends, signaled thread runs immediately with the condition guaranteed true.
- **Mesa** (Java, POSIX): signaling thread continues; signaled thread is woken but must re-check the condition (hence `while` loop instead of `if`).

---

## 8. Classic Synchronization Problems

### Bounded Buffer (Producer-Consumer)

```c
semaphore mutex = 1;    // For mutual exclusion
semaphore empty = N;    // Count of empty slots
semaphore full = 0;     // Count of full slots

// Producer:
wait(empty);    // Wait for an empty slot
wait(mutex);    // Acquire lock
// Add item to buffer
signal(mutex);  // Release lock
signal(full);   // Signal that buffer has one more item

// Consumer:
wait(full);     // Wait for a full slot
wait(mutex);    // Acquire lock
// Remove item from buffer
signal(mutex);  // Release lock
signal(empty);  // Signal that buffer has one more empty slot
```

**Critical insight**: The order of `wait()` calls matters. `wait(mutex)` before `wait(empty)` inside the producer would cause deadlock (mutex held while waiting for empty — if consumer needs mutex to signal empty, circular wait).

### Readers-Writers Problem

**First version (readers preference)**: Readers are never blocked unless a writer holds the lock. Writers may starve.

```c
semaphore rw_mutex = 1;  // Exclusive access for writers
semaphore mutex = 1;     // Protect reader_count
int reader_count = 0;

// Writer:
wait(rw_mutex);
// Write operation
signal(rw_mutex);

// Reader:
wait(mutex);
reader_count++;
if (reader_count == 1)
    wait(rw_mutex);  // First reader blocks writers
signal(mutex);
// Read operation
wait(mutex);
reader_count--;
if (reader_count == 0)
    signal(rw_mutex);  // Last reader unblocks writers
signal(mutex);
```

**Second version (writers preference)**: If a writer is waiting, no new reader can enter. Readers may starve.

**Third version (fair)**: Neither readers nor writers starve — implemented with FIFO queuing.

### Dining Philosophers Problem

5 philosophers sit around a table with 5 chopsticks (one between each pair). To eat, a philosopher needs BOTH chopsticks on their left and right.

**Naive solution (deadlock-prone)**:
```c
semaphore chopstick[5] = {1, 1, 1, 1, 1};

// Philosopher i:
wait(chopstick[i]);          // Pick left
wait(chopstick[(i+1)%5]);   // Pick right
// Eat
signal(chopstick[i]);
signal(chopstick[(i+1)%5]);
```

If all 5 philosophers simultaneously pick up their left chopstick, all wait for the right one — circular wait → deadlock.

**Solutions:**
1. **Allow only 4 philosophers** at the table simultaneously (resource limitation).
2. **Asymmetric**: Even philosophers pick left then right; odd philosophers pick right then left. Breaks circular wait.
3. **Both-or-nothing**: Only pick up chopsticks if both are available (requires atomic action).
4. **Monitor solution**: A coordinator grants permission to eat only if both neighbors aren't eating.

---

## 9. Priority Inversion — A Real Bug

**Scenario**: 
- Low-priority task L holds a mutex M.
- High-priority task H arrives and needs mutex M. H blocks.
- Medium-priority task M preempts L (L is low priority — M is higher).
- L can't run → can't release the mutex → H waits indefinitely.
- **Effective priority inversion**: M (medium) is running while H (high) is blocked, even though H has the highest priority.

**Mars Pathfinder** (1997): This exact bug caused the spacecraft's computer to reset repeatedly. A high-priority task waited for a mutex held by a low-priority task being preempted by medium-priority tasks.

**Priority Inheritance Protocol**: When H blocks waiting for mutex M held by L, L temporarily inherits H's priority. L runs at H's priority, completes quickly, releases M, reverts to its original priority. H proceeds.

**Priority Ceiling Protocol**: Each mutex has a "priority ceiling" equal to the highest priority of any task that may acquire it. A task can only acquire a mutex if its priority is higher than the ceilings of all currently locked mutexes. Prevents deadlock and priority inversion.
