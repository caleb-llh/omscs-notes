# Synchronisation / Memory Consistency

### **Chapter I: Fundamentals of Multicore Synchronization**

#### **1.1 Purpose and Definition**
Synchronization is the mechanism used to coordinate activities among multiple threads and cores working on a shared program. Its primary functions are:
*   **Mutual Exclusion (Locking):** Ensuring that only one thread can access a specific piece of code or data at a time.
*   **Barrier Synchronization:** Ensuring all participating threads reach a specific point in execution before any are allowed to proceed.

#### **1.2 The Necessity of Critical Sections**
A **critical section** (or atomic section) is a segment of code that must behave as if it executes without interference from other threads. 
*   **The Race Condition Problem:** In a scenario where two threads (A and B) increment a shared counter (e.g., counting letters in a document), each thread performs a load, an increment, and a store. 
*   **Interleaving Failure:** If both threads load the same value (e.g., 15) simultaneously, they both increment it to 16 and store 16 back to memory. The result is 16, though two increments occurred, which should have resulted in 17.
*   **The Role of Coherence:** While cache coherence ensures that a thread eventually sees the most recent write to a memory location, it does not prevent incorrect interleaving of multi-step operations. 

#### **1.3 Theoretical Requirements for Atomic Operations**
To implement locks effectively without complex algorithms (like Lamport’s Bakery algorithm), hardware must provide instructions that perform a **read and a write atomically**.
*   **Read-Only/Write-Only Insufficiency:** A standard load cannot ensure exclusivity, and a standard store cannot check a variable's status before overwriting it.
*   **Atomic Interaction:** Hardware must guarantee that the read-modify-write sequence occurs without interference from other processors.

---

### **Chapter II: Atomic Instruction Architectures**

#### **2.1 Atomic Exchange (Swap)**
The atomic exchange instruction swaps the contents of a register ($R1$) with a memory location.
*   **Operation:** In a single instruction, the register receives the value currently in memory, and the memory location is updated with the value previously in the register.
*   **Lock Implementation:** 
    1.  Place a '1' in $R1$.
    2.  Exchange $R1$ with the `lockvar`.
    3.  If the value received in $R1$ is '0', the lock is acquired (the `lockvar` is now '1').
    4.  If the value is '1', the lock was already occupied; the thread continues to loop and exchange until it observes a '0'.
*   **Drawback:** This instruction continuously writes to memory even when the lock is busy, causing constant cache invalidations and bus traffic.

#### **2.2 Test-and-Write Family (e.g., Test-and-Set)**
This class of instructions attempts to reduce unnecessary writes by testing the memory location before performing a store.
*   **Logic:** The instruction reads the memory location. If the value is '0' (unlocked), it stores '1' (locked) and returns success (usually '1' in a register). If the value is already '1', it does not perform a write and returns failure ('0').
*   **Coherence Advantage:** While the lock is busy, the instruction only performs reads. This allows multiple waiting cores to keep the `lockvar` in a **shared state** in their caches, spinning on local copies without generating bus traffic until the lock is released.

#### **2.3 Load-Linked (LL) and Store-Conditional (SC)**
Modern processors often separate atomic operations into two linked instructions to avoid complicating the execution pipeline.
*   **Pipeline Impact:** A traditional atomic read-write instruction requires the memory stage to perform both a read and a write in one cycle, which could necessitate adding extra stages (e.g., Memory 2, Memory 3) to the entire pipeline, slowing down every instruction.
*   **Load-Linked (LL):** Behaves like a normal load but additionally saves the memory address in a hidden, special **link register**.
*   **Store-Conditional (SC):** Checks if the address it is writing to matches the address in the link register.
    *   **Success:** If the addresses match and the "link" hasn't been broken, it performs the store and returns '1'.
    *   **Failure:** If the link is broken (e.g., another processor wrote to that address), it returns '0' and performs **no store**.
*   **Atomicity via Coherence:** The "link" is broken if the processor snoops a write from another core to the linked address. This ensures that if the SC succeeds, no other processor could have modified the variable between the LL and the SC.

---

### **Chapter III: Implementation of Mutual Exclusion (Locks)**

#### **3.1 Structural Components**
*   **Lock Variable (`lockvar`):** A standard location in shared memory. It is typically an integer where '0' represents unlocked and '1' represents locked.
*   **Initialization:** Setting the `lockvar` to '0'.
*   **The Lock Function:** A loop that repeatedly checks the `lockvar` and attempts to set it to '1' atomically.
*   **The Unlock Function:** A simple store operation that writes '0' to the `lockvar`. This does not need to be atomic because only the thread currently holding the lock should be performing the unlock.

#### **3.2 Performance and Coherence Interaction**
Different implementations impact system performance via the coherence protocol:
*   **Atomic Exchange Issues:** Every exchange is a write. In a three-core system, if Core 0 holds a lock, and Cores 1 and 2 are spinning with exchanges, the cache line for `lockvar` bounces between Core 1 and Core 2 in a "Modified" state. This generates massive bus traffic and consumes power, slowing down the "useful work" being done by Core 0.
*   **Optimized "Test-and-Atomic-Op" Approach:** To improve efficiency, threads should use normal loads to spin until the `lockvar` becomes '0' before attempting an atomic instruction.
    *   **LL/SC Example:** A thread performs an LL. If the value is '1', it immediately loops back to the LL. Because no SC is attempted, it functions like a normal load, allowing the `lockvar` to stay "Shared" across all waiting caches. Only when a '0' is observed does the thread attempt the SC.

#### **3.3 LL/SC Lock Function Logic**
To correctly implement a lock using LL/SC, the following assembly-logic must be followed:
1.  **Initialize:** Load '1' into a register ($R1$).
2.  **TryLock:** Perform **Load-Linked** of `lockvar` into $R2$.
3.  **Check Availability:** If $R2$ is not '0', the lock is busy; branch back to **TryLock**.
4.  **Attempt Acquisition:** If $R2$ is '0', perform **Store-Conditional** of $R1$ into `lockvar`.
5.  **Verify Success:** Check if the SC succeeded (is $R1$ still '1'?). If $R1$ became '0', someone else wrote to the lock first; branch back to **TryLock** to start over.

---

### **Chapter IV: Barrier Synchronization**

#### **4.1 Functional Overview**
A barrier ensures that all $N$ threads have arrived before any are allowed to leave.
*   **Variables:**
    *   **Counter:** Tracks the number of arrived threads.
    *   **Flag (Release):** Set when the counter reaches $N$ to signal waiting threads to proceed.

#### **4.2 Simple Barrier Implementation**
1.  **Arrival:** A thread acquires a lock to protect the counter.
2.  **Increment:** The thread increments the shared counter.
3.  **Last Thread Logic:** If the counter equals $N$, the thread resets the counter to '0' and sets the `release` flag to '1'.
4.  **Waiting Logic:** If the counter is less than $N$, the thread releases the lock and spins, waiting for the `release` flag to become '1'.
5.  **Re-initialization:** The first thread to arrive at the next barrier must set the `release` flag back to '0'.

#### **4.3 The Deadlock Failure Mode**
A simple barrier is sufficient for a single use but can fail if reused in a loop.
*   **The Scenario:** Thread 1 (fast) releases the barrier, finishes its work, and arrives at the *next* instance of the barrier before Thread 0 (slow) has even seen the release flag for the *first* instance.
*   **The Conflict:** Thread 1 resets the `release` flag to '0' for the second instance. Thread 0 finally checks the flag, sees '0', and continues to wait for the release of the *first* barrier, which will now never happen because Thread 1 is already waiting for the *second* barrier.

#### **4.4 Reusable Barrier (Sense-Reversal)**
To solve the deadlock, the barrier must avoid re-initializing the `release` flag.
*   **Local Sense:** Each thread maintains a private `localSense` variable.
*   **Toggle Logic:** Instead of setting a flag to '1', the last thread to arrive flips a global `release` variable to match the current `localSense` (e.g., flipping it from '0' to '1' in the first iteration, and '1' to '0' in the second).
*   **Independent Waiting:** Threads wait for the global `release` to equal their `localSense`. This prevents the "fast thread" from prematurely resetting the signal for the "slow thread".


### **Chapter V: Hardware Pipeline Integration of Atomic Instructions**

#### **5.1 The Pipeline Conflict**
In a classical **five-stage pipeline** (Fetch, Decode/Register Read, ALU/Address Calculation, Memory Access, Write-Back), standard memory instructions perform either a read or a write. 
*   **Atomic Limitation:** An atomic read-modify-write instruction (e.g., Swap or Test-and-Set) requires both a read and a write to the same memory location within the **Memory Access (MEM)** stage.
*   **Structural Hazard:** Standard hardware cannot perform both operations in a single cycle without significantly complicating the memory stage. To accommodate this, designers would need to add multiple memory stages (e.g., MEM2, MEM3) to the pipeline.
*   **Global Latency Penalty:** Because every instruction must flow through every stage of the pipeline to maintain timing, adding stages for infrequent atomic instructions would slow down all other instructions (Loads, Stores, Adds), resulting in a net performance loss.

#### **5.2 Load-Linked (LL) and Store-Conditional (SC) Architecture**
To maintain pipeline efficiency, the atomic operation is split into two distinct instructions that behave like standard memory accesses.
*   **Load-Linked (LL):** 
    *   Functions as a normal load by reading a value into a register.
    *   **Side Effect:** It records the memory address in a hidden, internal **link register**. This register is implicit and cannot be accessed directly by other instructions.
*   **Store-Conditional (SC):** 
    *   Before writing, it checks if the target address matches the address currently stored in the link register.
    *   **Success Conditions:** If the address matches and the "link" is intact, the store is performed, and a '1' is returned in the register.
    *   **Failure Conditions:** If the link is broken (e.g., due to a snoop of another processor's write to that address), the store is aborted, no data is written to memory, and a '0' is returned in the register.
*   **Direct Application:** Simple critical sections (like incrementing a single counter) can be implemented using LL/SC directly on the variable without requiring a separate lock variable.

---

### **Chapter VI: Memory Consistency vs. Coherence**

#### **6.1 Functional Definitions**
*   **Coherence:** Governs the order of accesses to the **same memory address**. It ensures that if Core A writes to address $X$, Core B will eventually see that update.
*   **Consistency:** Governs the order of accesses to **different memory addresses**. It defines the rules for how writes to address $A$ and $B$ are observed by other cores.

#### **6.2 The Consistency Necessity**
Coherence alone is insufficient for synchronization patterns involving a "Data" variable and a "Flag" variable.
*   **The Flag-Sync Problem:** Core 1 writes to `Data`, then sets `Flag = 1`. Core 2 spins on `Flag` and then reads `Data`.
*   **Coherence Failure:** Even with a coherent cache, an out-of-order processor might reorder Core 1's stores (setting `Flag` before `Data`) or Core 2's loads (reading `Data` before `Flag`). In these cases, Core 2 could read stale data ($0$ or $10$) even though it observed the `Flag` as $1$.
*   **Branch Prediction Impact:** A processor may predict the exit of a "while flag == 0" loop and speculatively read the data variable before the flag is actually verified.

---

### **Chapter VII: Sequential Consistency (SC)**

#### **7.1 Definition and Logic**
Sequential Consistency is the most intuitive model for programmers. It requires that the result of any execution is as if:
1.  All instructions from each individual processor executed in their **program order**.
2.  The instructions from all processors were **interleaved** in some global order.

#### **7.2 Simple SC Implementation**
The most basic way to enforce SC is to prevent any reordering of memory accesses.
*   **Execution Rule:** A processor cannot issue the next memory access until the previous access is **complete** (i.e., acknowledged by the memory system).
*   **Performance Impact:** This results in a **Memory Level Parallelism (MLP) of 1**. The processor cannot overlap multiple cache misses, meaning the total execution time is the sum of all individual memory latencies.

#### **7.3 Optimized SC (Out-of-Order with Replays)**
To regain performance, hardware can execute loads out-of-order while "pretending" to follow SC.
*   **Monitoring Coherence:** If a processor loads Address $B$ before Address $A$, it must monitor the coherence bus for any external writes to $B$ before the load of $A$ completes.
*   **Violation Detection:** If an external store to $B$ is snooped during this window, the out-of-order load is invalidated.
*   **Recovery:** The processor cancels the load and all subsequent instructions in the Reorder Buffer (ROB) and replays them to ensure the correct value is seen.

---

### **Chapter VIII: Relaxed Consistency Models**

#### **4.1 The Four Types of Ordering**
Sequential Consistency enforces all four possible orderings between memory operations:
1.  **Write $\to$ Write:** Order of stores to different locations.
2.  **Write $\to$ Read:** Order of a store followed by a read.
3.  **Read $\to$ Write:** Order of a read followed by a store.
4.  **Read $\to$ Read:** Order of consecutive reads.

#### **4.2 Relaxing the Rules**
Relaxed models allow the hardware to violate one or more of these orderings to improve performance.
*   **Common Relaxations:** Many models (like Weak or Processor Consistency) allow **Read $\to$ Read** reordering first, as it offers significant performance gains.
*   **The Programmer’s Burden:** If the hardware relaxes these rules, the programmer can no longer assume standard flag-synchronization will work.

#### **4.3 Synchronization Barriers (MSYNC)**
To restore order when it matters, relaxed architectures provide special "non-reorderable" instructions like **MSYNC** (Memory Synchronization).
*   **The Cloud Logic:** Instructions before MSYNC can be reordered with each other, and instructions after MSYNC can be reordered with each other.
*   **The Fence:** No instruction can cross the MSYNC boundary in either direction. All "pre-MSYNC" operations must complete before the MSYNC executes, and the MSYNC must complete before any "post-MSYNC" operations begin.
*   **Acquire/Release Pattern:**
    *   **Acquire (Locking):** Place an MSYNC **after** the lock acquisition to ensure no critical section work "escapes" upward and executes before the lock is held.
    *   **Release (Unlocking):** Place an MSYNC **before** the unlock operation to ensure all critical section work "stays inside" and completes before the lock is released.
    *   **Barriers:** Require MSYNC both **before** (to ensure work completes) and **after** (to ensure no one leaves early) the synchronization point.

---

### **Chapter IX: Data Races and Program Correctness**

#### **9.1 Defining a Data Race**
A data race occurs when:
1.  Two or more cores access the **same memory location**.
2.  At least one of those accesses is a **write**.
3.  The accesses are **not ordered** by synchronization (locks, barriers, etc.).

#### **9.2 Data-Race-Free (DRF) Programs**
A program is considered DRF if it is "well-synchronized," meaning all potential data races are prevented by synchronization operations.
*   **The DRF Property:** DRF programs behave identically on **relaxed consistency** hardware as they would on **sequentially consistent** hardware.
*   **Software Strategy:** Since debugging on relaxed models is extremely difficult due to unpredictable reordering, some processors allow a "switch" to SC mode during the debugging phase. Once the program is proven DRF, it can be switched back to relaxed mode for maximum performance.
