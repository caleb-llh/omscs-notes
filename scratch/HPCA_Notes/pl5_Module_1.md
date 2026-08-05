# Playlist 5 Module 1: Memory Consistency

## Introduction to Memory Consistency

**Background Context:** In a shared-memory multiprocessor system, multiple threads run on different cores and communicate by reading and writing to the same memory space. Previously, we learned about **Cache Coherence**, which ensures that all cores have a consistent view of a *single* memory location. However, coherence is not enough to guarantee correct program behavior when dealing with multiple variables.

This is where **Memory Consistency** comes in. Memory Consistency determines how strictly the ordering among accesses to *different* memory locations should be enforced. 

> **Mental Model: The Conversation Timeline**
> - **Coherence** is like the rules for a single conversation (a single variable). It ensures everyone hears the exact same words in the exact same order.
> - **Consistency** is the set of rules for *multiple simultaneous conversations* (different variables). It determines how the timelines of those different conversations interleave with one another.

### Coherence vs. Consistency
- **Coherence** defines the order of accesses observable by different threads if these accesses go to the **same** memory location. Without coherence, a thread might read a stale value forever, making shared-memory programming impossible.
- **Consistency** defines the order of accesses to **different** memory addresses.

**Why does this matter?** If coherence already guarantees that my writes are seen by others, why do we care about the order of accesses to different addresses? Because synchronization algorithms (like flags or locks) fundamentally rely on the relative timing of updates to different variables.

---

## Why Consistency Matters

Let's look at a concrete example of why consistency matters, even with perfect coherence.

Imagine we have two variables, `D` and `F`, both initialized to `0`. 

*   **Core 1** writes `1` to `D`, and then writes `1` to `F`.
*   **Core 2** reads `F` into register `R1`, and then reads `D` into register `R2`.

If we execute strictly in program order, we might expect `(R1, R2)` to be `(0, 0)`, `(0, 1)`, or `(1, 1)`. 

**The Question:** Can we ever get `R1 = 1` and `R2 = 0`?
*   **In Strict Program Order:** No. If Core 2 reads `F = 1`, it means Core 1 has already executed its write to `F`. Because Core 1 executes in program order, it must have *already* written to `D`. Therefore, when Core 2 subsequently reads `D`, it must read `1`.
*   **In an Out-of-Order Processor:** Yes! Modern processors dynamically reorder loads and stores for performance. If Core 2 reorders its loads (reads `D` before `F`), or if Core 1 reorders its stores, we could end up with `R1 = 1` and `R2 = 0`.

This unexpected reordering breaks programmer intuition. Coherence was perfectly maintained for `D` and perfectly maintained for `F`, but the *consistency* between them was lost. 

---

## Consistency Matters Quiz: Flag Synchronization

To see how this breaks real programs, consider a common synchronization pattern: **Flag Synchronization**.

**Scenario:**
- `flag` and `data` are both initialized to `0`.
- **Core 1** waits for the flag: `while (flag == 0) { wait(); } print(data);`
- **Core 2** produces data: `data = 10; data += 5; flag = 1;`

**What can Core 1 print?**
1.  **`15`:** This is the expected, correct behavior. Core 2 finishes its writes, sets the flag, and Core 1 reads `15`.
2.  **`0` or `10`:** These are *incorrect* but possible on an out-of-order processor! 
    *   **How `0` happens:** Core 1 might use **branch prediction** to guess that the `while` loop will exit. It speculatively executes ahead and fetches `data` while it is still `0`. Later, Core 2 writes `15` and sets `flag = 1`. Core 1's branch prediction is verified as "correct" (the flag is indeed 1), and it prints the stale `data` it fetched earlier: `0`.
    *   **How `10` happens:** Similar to above, but the speculative read of `data` happens exactly between Core 2's write of `10` and increment by `5`.
3.  **Can it print `5`?** No. Core 2's writes to the *same* variable (`data`) are kept in program order by the core to maintain uniprocessor correctness.

**The Takeaway:** Coherence does not prevent Core 1 from fetching `data` before it validates the `flag`. We need a consistency model to enforce these ordering restrictions. A real-world equivalent is thread termination in an OS, where one thread waits for another to mark itself "done" before reading its output.

---

## Sequential Consistency (SC)

**Sequential Consistency (SC)** is the most natural and intuitive memory model for programmers. 

**Definition:** The result of any execution should be the same as if the memory accesses executed by each processor were executed in order, and the accesses among different processors were arbitrarily interleaved.

> **Mental Model: The Dealer and the Decks**
> Imagine each processor has a deck of cards representing its instructions in strict order. There is one central "dealer" (memory) who takes turns pulling the top card from any processor's deck. The dealer can switch between decks arbitrarily, but the cards *within* a specific processor's deck are always played in their original sequence.

### Simple Implementation of SC
The simplest way to implement SC is to force a core to perform its next memory access **only when all previous accesses are completely finished**.
- In the flag example, Core 1 cannot read `data` until the read of `flag` has completed and retired. 
- **The Drawback:** Performance is devastated. The Memory Level Parallelism (MLP) drops to exactly **1**. The processor pays the full latency cost for every single cache miss sequentially, destroying the benefits of pipelining and out-of-order execution.

### A Better Implementation of SC
We want the performance of out-of-order execution, but the *illusion* of Sequential Consistency. 
- A core is allowed to execute loads out of order.
- However, it must **monitor coherence traffic** to ensure its speculative out-of-order reads aren't invalidated.
- **Example:** If Core 1 reads variable `B` early, it watches the coherence bus. If Core 2 writes to `B` *before* Core 1 was supposed to read `B` in program order, a consistency violation might have occurred.
- **The Fix:** Core 1 flushes its Reorder Buffer (ROB) and replays the load of `B` and all subsequent instructions. Because the load hasn't committed yet, this rollback is safe.

---

## Relaxed Consistency Models

Instead of building complex hardware to fake SC, an alternative approach is to **relax the consistency model**. We tell programmers: *"The hardware will reorder accesses for performance. If you need strict ordering for synchronization, you must explicitly ask for it."*

### The Four Types of Memory Ordering
Memory operations can be classified into four orderings:
1.  **Write → Write (W-W)**
2.  **Write → Read (W-R)**
3.  **Read → Write (R-W)**
4.  **Read → Read (R-R)**

Sequential Consistency enforces all four. Relaxed models drop enforcement for some of these (often starting with R-R and W-W for different addresses) to allow more out-of-order optimizations.

### Memory Barriers (`MSYNC`)
To allow programmers to write correct synchronization algorithms on relaxed hardware, architectures provide special, **non-reorderable instructions**, such as memory barriers or fences (e.g., the `msync` instruction).
- The processor guarantees that all memory accesses *before* the `msync` complete before the `msync` executes.
- It also guarantees that the `msync` completes before any access *after* it begins.

**Fixing the Flag Example:**
```c
while (flag == 0) { wait(); }
msync(); // Barrier!
print(data);
```
The `msync` prevents the read of `data` from moving before the validation of `flag`. The processor gets maximum performance everywhere else but respects the ordering exactly where it matters.

---

## MSYNC Quiz: Protecting a Critical Section

Let's apply memory barriers to a lock implementation on a highly relaxed processor (allows all 4 reorderings for different addresses).

```assembly
loop: LL r1, lock        // Load Linked: Read the lock
      BEQ r1, 0, loop    // If lock is held, keep spinning
      SC lock            // Store Conditional: Try to acquire the lock
      BEQ fail, loop     // If we failed to acquire, loop back
      
      // --- WHERE DOES MSYNC GO? ---
      MSYNC              // [1] AFTER ACQUIRE
      
      // --- Critical Section ---
      LOAD var
      INC var
      STORE var
      
      // --- WHERE DOES MSYNC GO? ---
      MSYNC              // [2] BEFORE RELEASE
      
      // --- Release Lock ---
      STORE lock, 0
```

**Why do we place `MSYNC` here?**
1.  **After Acquire (Acquire Semantics):** We must ensure we fully own the lock before we read or write the shared variable. Without `MSYNC`, the highly relaxed processor might speculatively move `LOAD var` *above* the lock acquisition!
2.  **Before Release (Release Semantics):** We must ensure all our updates to `var` are visible to other cores before we release the lock. Without `MSYNC`, the processor might execute `STORE lock, 0` *before* `STORE var`, allowing another thread to enter the critical section and read stale data.
3.  **Inside Critical Section:** No `MSYNC` is needed between `LOAD var` and `STORE var` because they access the *same* address, and single-thread uniprocessor correctness naturally keeps them in order.

---

## Data Races and Consistency

**Definition:** A **Data Race** occurs when there is a data dependence between accesses on different cores (at least one is a write), and these accesses are **not ordered by synchronization**. 
- Essentially, two threads are fighting over a variable without using locks, flags, or barriers.

### Data-Race-Free (DRF) Programs
A program is **Data-Race-Free (DRF)** if all accesses to shared data are correctly ordered by synchronization primitives. 

**The Golden Rule of Relaxed Consistency:**
> A Data-Race-Free program behaves exactly the same on a relaxed consistency machine as it would on a sequentially consistent machine.

**Why?** Because if your synchronization is correct, it utilizes barriers (`msync`) that enforce ordering exactly at the critical boundaries. Within those boundaries, no other thread is allowed to access the data, so hardware reordering is completely invisible and safe.

### The Debugging Challenge
While relaxed consistency is great for performance, it makes debugging buggy programs a nightmare. If a program has a data race, a relaxed processor will exhibit bizarre, non-deterministic behaviors that are impossible in SC.

For this reason, some advanced processors support switching between SC (for easier debugging) and a relaxed model (for maximum performance once the program is verified to be Data-Race-Free).