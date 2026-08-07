# Module 5: Multithreading and Cache Coherence

This module explores the hardware foundations of shared-memory multiprocessing, diving deep into how processors implement multi-threading (specifically Simultaneous Multi-Threading or SMT) and introducing the fundamental challenge of cache coherence in multi-core systems.

---

## 1. Message Passing vs. Shared Memory

Before diving into hardware, it's crucial to understand the two primary programming models for parallel computing:

*   **Shared Memory:** All cores have access to a single, common physical address space. They communicate by reading and writing to shared variables.
*   **Message Passing:** Each core has its own private memory. Cores communicate by explicitly sending and receiving packets of data over a network.

### Code Complexity & Synchronization Comparison

Imagine a scenario where one core initializes a large array, and all other cores need to read it.

*   **Data Distribution:**
    *   **Shared Memory:** *0 lines of code.* Once the array is initialized in memory, other cores can simply read it via memory pointers.
    *   **Message Passing:** *Significant lines of code.* The initializing core must explicitly invoke `send()` to all other cores, and every other core must explicitly invoke `receive()`.
*   **Synchronization (Waiting for initialization to finish):**
    *   **Shared Memory:** *Requires explicit synchronization (e.g., barriers, locks).* Since memory is instantly visible, other threads might start reading *before* the initialization is complete, reading garbage data. The programmer must add code to force readers to wait.
    *   **Message Passing:** *0 lines of code.* Synchronization is implicit. A core cannot read the array until it has received the message. Because the `send()` happens after initialization, the `receive()` acts as a natural synchronization barrier.

**🧠 Mental Model:** 
*   **Shared Memory** is like a shared whiteboard in an office. Anyone can walk up and write on it (easy data sharing), but if someone reads it while you're still drawing, they get half the picture. You need a "Do Not Erase/Read Yet" sticky note (synchronization).
*   **Message Passing** is like sending an email with an attachment. It takes more effort to draft the email to everyone (data distribution), but the recipient naturally waits for the email to arrive before they can read the attachment (implicit synchronization).

---

## 2. Shared Memory Hardware Architectures

How does hardware actually support running multiple threads? There is a spectrum of designs:

### A. Chip Multiprocessors (CMP / Multi-core)
Multiple distinct physical cores reside on the same chip, sharing the physical address space (e.g., UMA or NUMA architectures). Each core executes its own thread entirely independently.

### B. Time-Sharing a Single Core (OS Multi-threading)
A single core runs multiple threads by relying on the Operating System (OS) to perform context switches. 
*   *Drawback:* Context switching is extremely expensive (saving/restoring hundreds of registers) and wastes thousands of cycles. It provides the *illusion* of parallelism but doesn't improve raw hardware utilization.

### C. Hardware Multi-threading
The processor hardware is explicitly designed to hold the state of multiple threads simultaneously, switching between them rapidly to hide latency (like cache misses).

1.  **Coarse-Grained Multi-threading:** The CPU switches to a different thread only when a long-latency event occurs (e.g., an L2 cache miss). It still wastes a few cycles during the pipeline drain/switch.
2.  **Fine-Grained Multi-threading:** The CPU switches threads *every single cycle* in a round-robin fashion (e.g., Cycle 1: Thread A, Cycle 2: Thread B). Excellent for hiding short stalls, but single-thread performance drops significantly.
3.  **Simultaneous Multi-threading (SMT):** The pinnacle of single-core multi-threading (commercialized by Intel as *Hyper-Threading*). Instructions from *multiple different threads* can be issued and executed in the *exact same cycle*. 

---

## 3. The Performance Argument for SMT

Why do we need SMT? Because modern **superscalar, out-of-order processors** are frequently underutilized. 

A modern CPU might be able to issue 4 instructions per cycle. However, a single thread rarely has 4 independent instructions ready to go due to:
*   **Data Dependencies:** Instruction 2 needs the result of Instruction 1.
*   **Cache Misses:** The thread stalls waiting for RAM.
*   **Branch Mispredictions:** The pipeline has to be flushed.

This creates two types of waste:
*   **Vertical Waste:** Entire cycles where zero instructions are issued (e.g., during a cache miss). Fine-grained multi-threading fixes this by switching to another thread.
*   **Horizontal Waste:** Cycles where only 1 or 2 out of the 4 issue slots are used. 

**SMT targets Horizontal Waste.** It dynamically populates the unused issue slots of Thread A with ready instructions from Thread B. If Thread A only needs 2 ALUs this cycle, Thread B can use the other 2 ALUs simultaneously.

---

## 4. SMT vs. Dual Core (CMP)

Is SMT better than having two separate physical cores? It depends entirely on cost and the workload.

*   **Hardware Cost:** 
    *   Adding a second core costs **~100% more area**.
    *   Adding SMT to an existing superscalar core costs only **~5% more area** (because it reuses the massive execution engines and caches).
*   **Heterogeneous Workloads (SMT Wins):** If Thread A is floating-point intensive and Thread B is integer-intensive, they require completely different execution units. SMT can run both threads simultaneously at near 100% speed, achieving dual-core performance at a fraction of the cost.
*   **Homogeneous Workloads (Dual Core Wins):** If both threads are heavily integer-intensive, they will fight over the exact same ALUs in an SMT core. Performance will degrade, making SMT look like a single core. In this case, a true Dual Core processor provides double the throughput.

---

## 5. What Hardware Changes are Needed for SMT?

Surprisingly little! The most massive, complex parts of an out-of-order processor (the caches, the execution units, the complex reservation stations) remain completely unchanged. They are completely oblivious to which thread an instruction belongs to.

**Required Additions for SMT:**
1.  **Multiple Program Counters (PCs):** The Fetch stage needs a PC for each thread and a policy to decide which thread to fetch from each cycle.
2.  **Multiple Register Alias Tables (RATs):** The Rename stage needs a separate RAT per thread to map architectural registers (like `R1`) to physical registers correctly.
3.  **Multiple Architectural Register Files (ARF):** To hold the committed, official state of each thread.
4.  **Reorder Buffer (ROB) Logic:** Instructions must commit in-order *per thread*. This requires either splitting the ROB or adding complex logic to interleave instructions but commit them selectively.

*Intuition:* Think of an SMT processor as a massive kitchen (the execution units). Instead of one chef (thread) trying to use all the stoves, SMT just adds a second waiter taking orders (PCs/RATs) so two chefs can share the same kitchen seamlessly.

---

## 6. SMT, Data Caches, and the TLB

Running two threads simultaneously in the same core introduces severe issues for virtual memory translation.

### The Cache Aliasing Problem
*   **VIVT Caches (Virtually Indexed, Virtually Tagged):** The L1 cache looks up data using the Virtual Address. 
*   **The Bug:** Thread A and Thread B have entirely different address spaces. Thread A's virtual address `0x1000` might map to a completely different physical address than Thread B's `0x1000`. If they share a VIVT cache, Thread B might accidentally read Thread A's cached data! 
*   *Note:* In OS multi-threading, the OS flushes the VIVT cache on a context switch. In SMT, threads run simultaneously, so flushing is impossible.
*   **The Fix:** SMT processors must use **VIPT (Virtually Indexed, Physically Tagged)** or **PIPT** caches. The physical tags resolve the ambiguity.

### TLB Modifications
The Translation Lookaside Buffer (TLB) caches Virtual Page Number (VPN) to Physical Page Number (PPN) mappings. 
*   Because two threads can have the same VPN mapping to different PPNs, the TLB must become **Thread-Aware**.
*   **The Fix:** Append an Address Space ID (ASID) or Thread ID bit to each TLB entry. A TLB lookup must now match *both* the Virtual Address and the Thread ID to register a hit.

---

## 7. SMT and Cache Performance (Working Sets)

Because SMT threads share the same L1 cache, they can either play nicely or destroy each other's performance via **destructive interference** (cache thrashing).

**Example Scenario:**
*   L1 Cache Size = 8 KB
*   Thread A Working Set = 10 KB (doesn't fit in cache, will thrash regardless)
*   Thread B Working Set = 4 KB (fits)
*   Thread C Working Set = 1 KB (fits)

**How should the OS schedule them?**
*   *Bad:* Run A, B, and C together. Combined size = 15 KB. They will constantly evict each other's data. All three get terrible cache miss rates.
*   *Good:* Run Thread A alone. It thrashes the cache, but it was going to anyway. Then, run Thread B and Thread C together using SMT. Their combined size (5 KB) fits perfectly in the 8 KB cache. Both get excellent cache hit rates and high SMT throughput.

---

## 8. Introduction to Cache Coherence

We shift focus from *how* to build multi-threading to *how to make shared memory actually work correctly*.

### The Cache Coherence Problem
In a multi-core system, every core must have a private L1 cache. A single shared L1 cache would be too slow and severely bottleneck the system. However, private L1 Write-Back caches break the fundamental illusion of shared memory.

**The Failure Scenario:**
1.  Core A wants to write `X = 15`. It misses in its L1 cache, pulls `X` from Main Memory (where `X = 0`), and writes `15` into its private L1 cache. Because it's a write-back cache, Main Memory is *not* updated.
2.  Core B wants to read `X`. It looks in its private L1 cache, misses, and goes to Main Memory.
3.  Core B reads the stale value `X = 0` from Main Memory and puts it in its private cache.
4.  From this point forward, Core A can write to `X` a million times in its cache, and Core B will continue to read the stale `0` from its own cache.

**Definition:** The system is **incoherent**. The same memory location, viewed from different cores at the same time, has different values.

**The Solution:** We need an active hardware protocol—a **Cache Coherence Protocol**—to monitor reads and writes across all caches. It must ensure that if one core writes to a variable, other cores are either notified of the new value or forced to discard their stale cached copies.
