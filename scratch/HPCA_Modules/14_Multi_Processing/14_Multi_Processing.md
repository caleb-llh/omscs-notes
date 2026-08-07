# 14_Multi_Processing (Synthesized Notes)

# Module 4: Multiprocessors & Parallel Architectures

## 1. Flynn's Taxonomy of Parallel Machines
To understand parallel computing, we use **Flynn's Taxonomy** (proposed by Michael J. Flynn in 1966), which categorizes computer architectures based on the number of concurrent **Instruction Streams** and **Data Streams**.

*   **SISD (Single Instruction, Single Data):** 
    *   **Concept:** A traditional uniprocessor (single-core) machine.
    *   **How it works:** Executes one instruction stream, operating sequentially on one data stream.
*   **SIMD (Single Instruction, Multiple Data):**
    *   **Concept:** One instruction operates on multiple data points simultaneously.
    *   **Examples:** Vector processors and modern multimedia extensions (like Intel's MMX, SSE1-4, AVX). For instance, a single `ADD` instruction can add two arrays of 4 or 8 numbers at once.
*   **MISD (Multiple Instruction, Single Data):**
    *   **Concept:** Multiple instructions operate on the exact same data stream.
    *   **Examples:** Very rare in practice. The closest mental model is a **Stream Processor** (e.g., applying a sequence of filters—like edge detection, then sharpening—to a single raw camera feed pipeline).
*   **MIMD (Multiple Instruction, Multiple Data):**
    *   **Concept:** Multiple independent processors executing different instructions on different data.
    *   **Examples:** Most modern multi-core processors and supercomputers. Each core has its own Program Counter (PC) and runs its own code independently. This module primarily focuses on MIMD architectures.

---

## 2. The Paradigm Shift: Why Multiprocessors?
Historically, processors scaled by becoming "wider" (executing more instructions per cycle—IPC) and "faster" (higher clock frequencies). We eventually hit a wall, necessitating the shift to multi-core architectures.

### The Power Wall & Diminishing Returns
1.  **Diminishing Returns of ILP:** Making a single processor wider (e.g., executing 4 to 6 to 8 instructions per cycle) yields diminishing returns. According to **Amdahl's Law**, programs have inherent sequential dependencies. Making the parallel parts of a uniprocessor pipeline infinitely wide doesn't speed up the inherently sequential parts.
2.  **The Cubic Power Problem:** To make a processor faster, we must raise its clock frequency. Higher frequencies require higher voltages. Power consumption grows **cubically** relative to frequency improvements ($Power \propto V^2 \times f$, and since $V \propto f$, $Power \propto f^3$). Pushing a single core to extreme frequencies would cause it to overheat and burn.
3.  **Moore's Law Continues:** We still get double the transistors every 18 months for the same cost/area. Since we can't build a single ultra-fast core without burning it, we use the transistor budget to double the **number of cores** instead.

> **💡 The Catch:** Having 8 cores is useless if you run a single-threaded program. Multiprocessors *require* parallel software to realize performance gains. It is always preferable to have one core that is 2x faster than two cores of standard speed, but physical constraints force our hand to the latter.

---

### Deep Dive: Multicore vs. Fancier Single Core (Quiz Breakdown)
*Imagine we transition to a new manufacturing technology where transistors are half the size.*
*   **Old Tech Baseline:** 2.5 IPC, 100 Watts max thermal limit, 2 GHz frequency, 2 cm² chip area.

If we keep the 2 cm² budget, we have two options:
**Option A: The Fancier Single Core**
*   We build a massive single core achieving **3.5 IPC**. Due to its complexity, it requires 75W at 2 GHz. 
*   If we push it to the maximum thermal budget of 100W, how fast can we clock it?
*   *Math:* Power ratio = $100W / 75W = 1.33$. Since Power scales cubically, max frequency multiplier = $\sqrt[3]{1.33} \approx 1.1$. 
*   *New Frequency:* $2 \text{ GHz} \times 1.1 = 2.2 \text{ GHz}$.
*   *Total Speedup:* $1.1 \text{ (frequency improvement)} \times \frac{3.5}{2.5} \text{ (IPC improvement)} = \mathbf{1.54x \text{ Speedup}}$.

**Option B: The Dual-Core Approach**
*   Because transistors are half the size, we can fit **two** standard cores in the 2 cm².
*   Each core gets 2.5 IPC and consumes 50W at 2 GHz (Total = 100W).
*   *Total Speedup:* Assuming perfectly parallel software, **2x Speedup**.

**Conclusion:** Multicore mathematically yields better theoretical speedups under strict power and thermal constraints—again, assuming programs are written to use them.

---

### The Software Challenge
*   **Development Cost:** Sequential code is much easier to write. Writing parallel code is expensive and highly prone to complex bugs (race conditions, deadlocks).
*   **Performance Scaling:** Ideally, performance scales linearly with cores. In reality, most programs scale well for a few cores and then plateau due to communication overhead. Achieving perfect scaling on massive core counts takes years of expert development.

---

## 3. Multiprocessor Memory Architectures

### A. Centralized Shared Memory (UMA / SMP)
*   **Architecture:** Multiple cores, each with private caches, all connected to a single, centralized main memory via a shared bus.
*   **SMP (Symmetric Multiprocessing):** The architecture is symmetric; any core and its cache look structurally identical to any other.
*   **UMA (Uniform Memory Access):** Because memory is centralized, the time it takes to access main memory is roughly uniform across all cores.
*   **The Problem:** Centralized memory scales poorly (usually maxes out around 8-16 cores). 
    *   **Bandwidth Bottleneck:** Cache misses from all cores hit the same memory module. The contention causes severe queuing delays.
    *   **Size vs. Speed:** More cores demand larger memory capacity. Larger memory arrays are inherently slower. Adding cores eventually provides zero performance benefit because they spend all their time waiting on the memory bus.

### B. Distributed Memory (Message Passing / Clusters)
*   **Architecture:** Each core is effectively its own independent computer ("multicomputer"). It has a processor, cache, and **private local memory**, connected to a high-speed network. 
*   **No Direct Sharing:** Core A *cannot* directly read Core B's memory. 
*   **Scaling:** These systems scale to massive numbers of processors (e.g., Supercomputers). They scale well primarily because they force programmers to explicitly manage data locality and minimize network communication.

### C. NUMA (Non-Uniform Memory Access)
*   **Architecture:** A hybrid where memory is physically distributed (local to specific cores/nodes) but logically shared across the system. Accessing local memory is fast; accessing a remote core's memory traverses the network and is slower (hence "Non-Uniform").
*   **OS Allocation Strategy (Quiz Insight):** 
    *   The OS should allocate a thread's **Stack pages** purely in the memory slice local to the core executing it.
    *   The OS should place **mostly-locally-accessed data** in the local slice.
    *   *Anti-pattern:* Do not put all data in Core 0's slice just because Core 0 initialized it. This creates a centralized bottleneck, completely defeating the purpose of distributed physical memory.

---

## 4. Programming Models: Message Passing vs. Shared Memory

To illustrate the difference, consider a program designed to sum an array of 1,024 elements using 4 cores.

### Message Passing Model
*   **How it works:** Each core gets its own local array of 256 elements. 
*   **Workflow:** 
    1. The programmer explicitly writes code to distribute the data over the network.
    2. Each core iterates over its chunk and computes a local sum.
    3. Cores 1, 2, and 3 use OS `send()` primitives to push their local sums to Core 0.
    4. Core 0 uses `receive()` primitives, matches them up, computes the final sum, and prints it.
*   **Characteristics:** Communication is explicit. You must prevent deadlocks (sending without receiving or vice versa).

### Shared Memory Model
*   **How it works:** The 1,024-element array lives in shared memory. No data distribution is needed.
*   **Workflow:**
    1. Each core simply indexes into its designated quarter of the array (e.g., Core 1 reads indices 256–511).
    2. Cores compute their local sums.
    3. Cores use **Synchronization (Locks/Critical Sections)** to safely add their local sum to a globally shared `total_sum` variable.
    4. A **Barrier** is used to ensure all cores have finished updating before Core 0 prints the result.
*   **Characteristics:** Communication is implicit (done via standard loads and stores).

### Summary Comparison

| Feature | Message Passing | Shared Memory |
| :--- | :--- | :--- |
| **Communication** | **Explicit:** Programmer calls `send()` / `receive()`. | **Implicit:** Programmer simply reads/writes variables. Hardware handles it. |
| **Data Distribution** | **Manual:** Programmer divides and sends data over the network. | **Automatic:** System caches and fetches data automatically on demand. |
| **Hardware Required** | Simple: Standard CPUs + Network Interface Cards (NIC). | Complex: Extensive hardware support for cache coherence and synchronization. |
| **Correctness** | Hard: Prone to deadlocks, mismatched sends/receives. | Medium: Prone to race conditions, requires careful locking/barriers. |
| **Performance Tuning**| Easy: Once correct, performance is usually good because locality is explicitly optimized. | Hard: False sharing and hidden communication overheads can secretly cripple performance. |

> **Mental Model:** Message passing is like mailing letters between distinct offices—you are highly aware of the cost and delay of communication. Shared memory is like four people working on the same massive whiteboard—it feels natural, but if you aren't careful, you'll bump elbows and overwrite each other's work without noticing.


---

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


---

