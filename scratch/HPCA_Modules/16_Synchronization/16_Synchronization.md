# 16_Synchronization (Synthesized Notes)

# High Performance Computer Architecture: Module 9 - Locks and Synchronization

This module dives deep into how synchronization mechanisms—specifically locks—are implemented at the hardware and software level, their implications on processor pipelines, and their interactions with cache coherence protocols.

---

## 1. What is a Lock Variable?
**Intuition & Mental Model:** 
We often treat a "lock" or "mutex" as a magical construct that magically orchestrates threads. However, physically, a lock is **just a regular variable in shared memory** (often an integer). It has a memory address, and threads use normal load and store operations to read and change its value. 

* **State Representation:** 
  * `0` = Unlocked / Free
  * `1` = Locked / Busy

**Quiz Insight:** If we have an array of locks (e.g., `count_lock[L]`), each element is just a standard memory word. There is no "special synchronization memory"; locks reside in the same shared memory space as any other data.

---

## 2. The Synchronization Paradox
A naive approach to implementing a lock `acquire()` function in C-like pseudocode might look like this:
```c
void lock(int *lock_var) {
    while (*lock_var == 1) { 
        // spin (wait) while it is locked
    }
    // We see a 0! Let's lock it.
    *lock_var = 1; 
}
```
**The Problem:** This naive code is vulnerable to a race condition. If two threads (Thread A and Thread B) reach the `while` loop at the same time, they might both read `*lock_var` as `0`. Both exit the loop, both write `1` to `lock_var`, and both enter the critical section simultaneously. This defeats the entire purpose of a lock!

**The Paradox:** To fix this, the process of *checking* the lock (seeing a `0`) and *setting* the lock (writing a `1`) needs to be **atomic** (indivisible). But to make this block of code atomic, we would need a lock to protect the lock function itself! 

**Software vs. Hardware Solutions:**
We could resolve this using complex software algorithms like **Lamport's Bakery Algorithm**. However, these algorithms require tens of instructions, making basic locking operations incredibly slow and expensive. Therefore, we rely on **special hardware atomic instructions** to do the heavy lifting.

---

## 3. Hardware Support: Atomic Instructions
To implement locks efficiently, the processor must provide instructions that perform both a **read and a write to memory in a single, indivisible operation**. 
* Just a read isn't enough (we can't change the state).
* Just a write isn't enough (we can't check the current state first).
* An instruction that doesn't access memory is useless because the lock variable lives in memory.

There are three main types of atomic instructions provided by hardware architectures.

### Type 1: Atomic Exchange (Swap)
**How it works:** This instruction takes a register and a memory address. In one simultaneous step, it puts the value of the register into memory, and the old value of the memory into the register.

**Implementing a lock:**
```assembly
// R1 = 1 (Locked state)
// Exchange R1 with lock_var
```
If `lock_var` was `0` (free), the exchange puts `1` in `lock_var` (locking it) and returns `0` to `R1`. The thread sees `R1 == 0` and knows it successfully acquired the lock. If `lock_var` was already `1`, the exchange simply swaps `1` for `1`. The thread sees `R1 == 1` and keeps looping.

**The Drawback (Performance):** 
Atomic exchange *always* writes to the memory location, even if the lock is already busy. In a multi-core system, every write invalidates the cache block for all other cores (due to cache coherence). If multiple threads are spinning on a lock, they constantly generate bus traffic and invalidate each other's caches, wasting immense power and slowing down the interconnect.

### Type 2: Test-and-Set (Test-and-Write)
**How it works:** To fix the continuous writing problem of Atomic Exchange, the `Test-and-Set` instruction first *reads* the memory. It only *writes* if a specific condition is met (e.g., if the memory value is `0`). 

**Implementing a lock:**
The instruction checks `lock_var`. If `lock_var == 0`, it writes `1` to it and returns `1` (success). If `lock_var != 0`, it does not write to memory and returns `0` (failure).

**The Advantage:**
Because it avoids writing when the lock is busy, spinning threads simply read the value. Thanks to cache coherence, all spinning cores can hold the lock variable in the **Shared (S)** state in their local caches. They spin on their local copies without generating any bus traffic. When the lock is finally freed (written to `0`), the shared copies are invalidated, and the cores try again.

**The Drawback (Hardware Design):**
While great for software, `Test-and-Set` is terrible for processor pipelining. A standard 5-stage RISC pipeline (Fetch, Decode, ALU/Address, Memory, Writeback) is designed to do *either* a read or a write in the Memory stage. Forcing a read, a comparison, and a conditional write into a single cycle would require adding extra memory stages to the pipeline. Since all instructions flow through the pipeline, adding stages just for rare atomic instructions slows down the execution of *all* instructions.

### Type 3: Load-Linked (LL) and Store-Conditional (SC)
To get the benefits of `Test-and-Set` without ruining the pipeline, modern architectures (like ARM and MIPS) split the atomic operation into two separate instructions that work together.

1. **Load-Linked (LL):** Behaves like a normal load, reading a value from memory into a register. However, it also saves the memory address in a special, hidden **Link Register**.
   * *Mental Model:* Think of LL as placing a delicate tripwire on a specific memory address.
2. **Store-Conditional (SC):** Attempts to store a value to a memory address. Before storing, it checks the Link Register. If the address matches (the tripwire is intact), the store succeeds and returns `1`. If the tripwire was broken, the store aborts and returns `0`.

**How does the link break?** 
The coherence protocol monitors the bus. If *any* other core writes to the linked address (or if an interrupt occurs), the Link Register is cleared (set to 0). 

**Implementing a lock with LL/SC:**
```assembly
try_lock:
    LI R1, 1          // Load Immediate: R1 = 1
    LL R2, lock_var   // Load-Linked: R2 = *lock_var, set tripwire
    BNEZ R2, try_lock // If R2 != 0 (lock is busy), retry immediately
    SC R1, lock_var   // Store-Conditional: try to write R1 (1) to lock_var
    BEQZ R1, try_lock // If SC returns 0 in R1 (tripwire broken), retry
    // Lock acquired!
```
**Quiz Insight:** We retry if `R2 != 0` (the lock was busy). If `R2 == 0` (lock was free), we execute SC. We then check `R1`. If `R1 == 0`, someone else grabbed the lock between our LL and SC, breaking our link, so we must retry. Note that software cannot read the Link Register directly; it is strictly an internal hardware mechanism.

**Bonus Use Case (Lock-Free Operations):** 
Because LL and SC are inherently atomic together, we can perform simple atomic operations (like an atomic increment of a counter) *without* needing a separate lock variable. We just LL the counter, increment the register, and SC it back. If it fails, we retry.

---

## 4. Locks, Coherence, and Performance
The way a lock is implemented drastically impacts the overall system performance, primarily through the cache coherence protocol (e.g., MESI).

### The "Ping-Pong" Effect of Atomic Exchange
If 3 cores are competing for a lock using Atomic Exchange:
1. Core 0 grabs the lock. The cache block containing `lock_var` is in the **Modified (M)** state in Core 0.
2. Core 1 and Core 2 are spinning, executing Atomic Exchanges. 
3. Core 1 executes an exchange. This requires writing to the block. Core 0's copy is invalidated, the block moves to Core 1 in the **Modified** state.
4. Core 2 executes an exchange. Core 1's copy is invalidated, the block moves to Core 2 in the **Modified** state.

**Result:** The cache block rapidly bounces back and forth between the spinning cores. This generates massive amounts of interconnect (bus) traffic and consumes a lot of power. 
Furthermore, the heavy bus traffic slows down Core 0 (the one actually doing useful work in the critical section!) if it needs to fetch other data from memory, ultimately delaying the release of the lock.

### The Efficiency of LL/SC and Test-and-Set
With Test-and-Set or LL/SC, cores only read the lock while it is busy:
1. Core 0 grabs the lock.
2. Core 1 and Core 2 read the lock. The block transitions to the **Shared (S)** state in their caches.
3. Core 1 and Core 2 spin locally on their cached copies. No bus traffic is generated!
4. When Core 0 unlocks (writes `0`), it invalidates the shared copies. 
5. Core 1 and Core 2 experience a cache miss, fetch the updated `0` value, and race to execute their SC or Test-and-Set. Only one wins; the loser goes back to spinning locally.

**Conclusion:** Software spinning mechanisms must be co-designed with hardware coherence protocols. Poorly implemented locks don't just waste CPU cycles; they physically clog the hardware interconnect, degrading the performance of the entire multi-core system.


---

# Module 10: Advanced Synchronization - Test-and-Atomic-Op Locks & Barriers

This module delves into more efficient synchronization primitives. We transition from simple atomic operations that can thrash the system bus, to more cache-friendly lock designs, and then explore **barrier synchronization**, a crucial construct for orchestrating parallel threads.

---

## 1. Optimizing Locks: The "Test and Atomic Op" Approach

### Background Context: The Problem with Naive Spinlocks
In earlier implementations, we used an atomic exchange (or "Test-and-Set") instruction repeatedly in a tight loop to wait for a lock. 
- **The flaw:** Every time a thread attempts an atomic exchange, it requests write permissions, modifying the cache block and invalidating the cache lines of all other cores spinning on that same lock. 
- **The consequence:** This active waiting generates a massive amount of bus traffic (cache misses and cache-to-cache transfers). It not only wastes energy but also saturates the coherence bus, severely slowing down the thread that *actually holds the lock* and is trying to finish its critical section.

### The Solution: "Test and Test-and-Set"
To make the lock more efficient, we introduce the **Test and Atomic Op** (often called Test-and-Test-and-Set) approach.

**Mental Model:**
Don't try to blindly grab the lock. First, just *look* at it. Only if it looks free, try to grab it.
1. **Test:** Spin using **normal memory loads** (read-only) while the lock is busy.
2. **Atomic Op:** When the normal load indicates the lock is free (0), attempt to grab it using an **atomic exchange** or **Load-Linked/Store-Conditional (LL/SC)**.

**Why this is better:**
While spinning with normal loads, the lock variable gets pulled into the cache of the waiting cores in the **Shared (S)** state. 
- As long as the lock is held (busy), the waiting cores just repeatedly read their local cache (Cache Hits!).
- **Zero bus traffic** is generated while waiting. The coherence bus is completely free for the core executing the critical section.
- Only when the lock is released (written to 0) does the cache line get invalidated. The waiting cores experience a cache miss, read the new value (0), and *then* they try to grab the lock with an atomic operation.

### Implementation using LL/SC (Load-Linked / Store-Conditional)
If our architecture uses LL/SC instead of atomic exchange, we apply the same logic. The goal is to wait using the normal load properties of LL until we see the lock is free, and only then execute the SC.

```assembly
lock_loop:
    LL r2, lockvar       // Load the current state of the lock
    BNEZ r2, lock_loop   // If r2 != 0 (lock is busy), keep spinning! (LL acts as normal load)
    
    // We saw the lock is free! Try to grab it.
    ADDI r1, r0, 1       // r1 = 1 (busy state)
    SC r1, lockvar       // Store Conditional: tries to place 1 into lockvar
    BEQZ r1, lock_loop   // If SC failed (r1 == 0), someone else grabbed it. Retry.
    
    // If we reach here, we successfully acquired the lock!
```

### The Unlock Operation
How do we release a lock acquired this way? Do we need atomic instructions?
**No.** The unlock operation only needs a standard store instruction:
```assembly
    SW r0, lockvar       // Normal store 0 to lockvar
```
**Intuition:** The thread executing `unlock` is the *only* thread that currently holds the lock. Since no other thread can successfully grab or modify the lock while it is held, there are no race conditions for the unlocker. A simple store is sufficient to free the lock and invalidate the caches of the spinning threads, waking them up.

---

## 2. Barrier Synchronization

### What is a Barrier?
A **barrier** is a synchronization point in a program where all participating threads must stop and wait until *every* thread has reached that point. Only when all threads have arrived can they all proceed past the barrier.

**Example Use Case:**
Imagine 4 threads computing the sum of a massive array. Each thread computes the sum of its own chunk. Before thread 0 can take the 4 partial sums and compute the grand total, it **must** be absolutely certain that threads 1, 2, and 3 have finished their calculations. A barrier guarantees this.

### A Simple Barrier Implementation
A barrier typically requires two shared variables:
1. A **counter**: Tracks how many threads have arrived.
2. A **release flag**: Signals when threads can proceed.

**Pseudo-code for a simple barrier:**
```c
lock(counter_lock);
if (count == 0) {
    release = 0;      // First thread to arrive resets the release flag
}
count++;              // Increment arrival count

if (count == TOTAL_THREADS) {
    // I am the last thread to arrive!
    count = 0;        // Reset count for the next use
    release = 1;      // Open the barrier!
}
unlock(counter_lock);

// Wait at the barrier
while (release == 0) {
    // Spin until release flag is set to 1
}
```
*Note: This works perfectly if the barrier is only used **once** in the program.*

### The Problem: Reusability and Deadlock
The simple barrier above breaks if we put it in a loop and try to synchronize on the **same barrier multiple times**. 

**The Deadlock Scenario:**
1. Threads A and B arrive at Barrier Instance 1.
2. Thread B arrives last, sets `count = 0` and `release = 1`.
3. Thread B breezes past the barrier, quickly finishes its next chunk of work, and arrives at **Barrier Instance 2**.
4. At Barrier Instance 2, Thread B is the first to arrive. It resets `release = 0`.
5. **Meanwhile**, Thread A was slightly delayed (e.g., interrupted by the OS) before it could check `release` in Instance 1.
6. When Thread A finally checks `release`, it sees the `0` that Thread B just wrote for Instance 2!
7. **Disaster:** Thread A is now stuck forever in Barrier 1 waiting for `release == 1`. Thread B is stuck forever in Barrier 2 waiting for Thread A to arrive. **Deadlock.**

### The Solution: Reusable "Sense-Reversing" Barrier
To make a barrier reusable, we must eliminate the need to globally reset the `release` flag to `0`. Instead, we make the barrier wait for a *changing* target state.

**The Fix:** 
We introduce a `local_sense` variable that is private to each thread. In one iteration, threads wait for the release flag to become `1`. In the next iteration, they wait for it to become `0`.

**Pseudo-code for Reusable Barrier:**
```c
// Thread-local variable, persists across barrier calls. Initializes to 1.
local_sense = !local_sense; // Flip our local target state (e.g., 0 -> 1 -> 0)

lock(counter_lock);
count++;
if (count == TOTAL_THREADS) {
    // Last thread to arrive
    count = 0;              // Reset count
    release = local_sense;  // Set global release to the target state!
    unlock(counter_lock);
} else {
    unlock(counter_lock);
    // Spin until the global release flag matches our local target
    while (release != local_sense) {
        // Spin
    }
}
```

**Why this works:**
If Thread A is delayed in Instance 1 (waiting for `release == 1`), and Thread B races ahead to Instance 2, Thread B will flip its `local_sense` to `0`. The global `release` flag remains `1` from the first instance! 
- Thread A will wake up and proceed safely because the global flag is still `1`. 
- By alternating the target release value (0, then 1, then 0), threads in different iterations of the barrier are waiting for entirely different signals, making the barrier perfectly reusable without risking deadlocks.

---

## Summary
- **Test-and-Atomic-Op Locks** improve energy efficiency and performance by utilizing the cache. Cores spin on normal loads (Cache Hits) and only attempt atomic operations when the lock appears free.
- **Unlocks** do not require atomic instructions; a standard store suffices.
- **Barriers** orchestrate parallel execution, forcing threads to wait for each other.
- **Reusable Barriers** require a "sense-reversing" design (toggling the wait condition between 0 and 1) to prevent fast threads from resetting the state before delayed threads can proceed, avoiding deadlocks.


---

