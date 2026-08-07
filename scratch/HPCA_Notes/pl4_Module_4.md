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
