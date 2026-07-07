# Cheat Sheet — Process Synchronization

## Critical Section Requirements
| Requirement | Means | Prevents |
|-------------|-------|---------|
| **Mutual Exclusion** | Only one process in CS at a time | Data corruption |
| **Progress** | If CS empty and someone wants in, decision can't be postponed | Deadlock (nobody gets in) |
| **Bounded Waiting** | Bound on how many times others skip ahead of you | Starvation |

## Peterson's Solution (2 processes)
```c
flag[i] = true;   turn = j;
while (flag[j] && turn == j);  // spin
// CRITICAL SECTION
flag[i] = false;
```
⚠️ Fails on real hardware — needs memory barrier!

## Hardware Atomics
```c
// test_and_set: returns old value, always sets to true
bool TAS(bool *t) { bool r=*t; *t=true; return r; }

// compare_and_swap: if *val==expected, set to new, return old
int CAS(int *val, int exp, int new) { int r=*val; if(*val==exp) *val=new; return r; }

// Spinlock with TAS:
while(test_and_set(&lock));  // acquire
// CS
lock = false;                // release
```

## Semaphore Operations
```
wait(S):              signal(S):
  S--;                  S++;
  if S < 0:             if S <= 0:
    sleep (block)          wakeup(one waiting process)
```
- **Binary semaphore** (init=1): acts as mutex
- **Counting semaphore** (init=N): resource pool of N

## Semaphore vs Mutex
| | Mutex | Binary Semaphore | Counting Semaphore |
|-|-------|-----------------|-------------------|
| Initial value | 1 | 1 | N |
| Ownership | ✅ (only acquirer can release) | ❌ | ❌ |
| Use case | Mutual exclusion | Mutual exclusion | Resource counting |

## Bounded Buffer — Correct Order!
```c
// PRODUCER:              // CONSUMER:
wait(empty);             wait(full);      ← resource first
wait(mutex);             wait(mutex);     ← then mutex
// add item              // remove item
signal(mutex);           signal(mutex);
signal(full);            signal(empty);
```
⚠️ NEVER do wait(mutex) before wait(empty/full) → DEADLOCK

## Readers-Writers
```
reader_count tracks active readers
First reader  → acquires rw_mutex (blocks writers)
Last reader   → releases rw_mutex (allows writers)
Writer        → acquires rw_mutex exclusively
```
- **1st solution**: readers preference → writers may starve
- **2nd solution**: writers preference → readers may starve
- **Fair**: FIFO queue — neither starves

## Dining Philosophers — Solutions
```
❌ Naive (deadlocks): all pick left, then wait for right → circular wait

✅ Fix 1 — Asymmetric:
   Even philosophers: left then right
   Odd philosophers:  right then left

✅ Fix 2 — Limit seats:
   semaphore seats = 4 (not 5)
   At most 4 philosophers → always ≥1 has both chopsticks available

✅ Fix 3 — Both or nothing:
   Only pick up if BOTH chopsticks available (atomic check)
```

## Monitor Rules
```
✅ Use while (not if) with condition variables!
   Reason: Mesa semantics + spurious wakeups

notify()    → wake ONE (they must re-compete for lock)
notifyAll() → wake ALL (they all re-compete for lock)
wait()      → release lock + sleep + re-acquire when woken
```

## Priority Inversion
```
H (high) waits for mutex held by L (low)
M (medium) preempts L
Result: M runs while H waits ← INVERSION!

Fix — Priority Inheritance:
L temporarily gets H's priority while holding the mutex
L runs at high priority → finishes → releases mutex
H proceeds → L reverts to original priority
```
Real example: Mars Pathfinder 1997

## Classic Problems Quick Reference
| Problem | Key Semaphores | Key Invariant |
|---------|---------------|---------------|
| Bounded Buffer | mutex, empty=N, full=0 | empty + full = N always |
| Readers-Writers | rw_mutex, mutex, reader_count | Writers exclusive; readers shared |
| Dining Philosophers | 5 chopstick semaphores | Prevent circular wait |
| Sleeping Barber | customers, barbers, mutex | Wake barber if sleeping |
