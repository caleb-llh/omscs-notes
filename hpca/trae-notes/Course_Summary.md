# High-Performance Computer Architecture (HPCA): Course Overview

## Introduction
The evolution of computer architecture is a continuous battle against physical limits—power dissipation, the speed of light, and the immense latency gap between processors and memory. As the free lunch of Moore's Law and Dennard Scaling ended, architects could no longer simply increase clock speeds. Instead, they had to rely on radical architectural innovations to extract hidden parallelism and mask memory latency.

This course explores **High-Performance Computer Architecture (HPCA)** by walking through the mechanisms that transform a simple sequential processor into a chaotic, highly parallel, and aggressively speculative dataflow engine—all while maintaining the strict illusion of sequential execution for the programmer. By the end of this course, you will understand the hardware-software contracts and the brilliant tradeoffs that power modern CPUs.

---

## Core Themes and Conceptual Framework

### 1. Pipelining, Prediction, and the Quest for Steady State (Modules 1-4)
The foundation of processor performance is the Iron Law: `Time/Program = Instructions × Cycles/Instruction (CPI) × Time/Cycle`.
To drive CPI down to 1, processors use **Pipelining**—overlapping instruction execution much like a factory assembly line. However, pipelines are constantly threatened by data and control hazards.

You will explore how processors handle these disruptions using **Branch Prediction**. Because pipelines are so deep, waiting to resolve a branch condition introduces massive stalls. Instead, processors act like a fast conveyor belt, aggressively guessing the path using history-based predictors (like PShare and GShare) and executing speculatively. When prediction isn't enough, architectures employ **Predication** (if-conversion), executing both paths of a branch and discarding the wrong one, thereby trading ALU power for a guaranteed zero-flush penalty.

### 2. Instruction-Level Parallelism (ILP) and Out-of-Order Execution (Modules 5-8)
To push CPI below 1, processors must execute multiple instructions simultaneously (Superscalar). You will learn how the hardware extracts **Instruction-Level Parallelism (ILP)** from seemingly sequential code using **Tomasulo's Algorithm**. 
* **Register Renaming:** Hardware eliminates "false" dependencies by dynamically mapping a small set of architectural registers to a vast pool of hidden physical registers.
* **The Dataflow Engine:** Instructions wait asynchronously in Reservation Stations and fire out-of-order the exact moment their data arrives via the Common Data Bus (CDB).

Because out-of-order execution is chaotic, the processor uses a **Reorder Buffer (ROB)** as an "event horizon." Instructions execute speculatively in the future, but their results only commit to permanent architectural state in strict, sequential order. This guarantees precise recovery if a branch is mispredicted or an exception occurs. You will also contrast this hardware-heavy approach with **Static Scheduling (VLIW)**, where the compiler does the heavy lifting to bundle independent operations, trading general-purpose flexibility for extreme power efficiency.

### 3. The Memory Wall: Caches, Translation, and Storage (Modules 9-13)
A fast processor is useless if it is starved for data. You will explore how architectures combat the "Memory Wall" using the **Principle of Locality** to build deep memory hierarchies.
* **Cache Dynamics:** You will study the delicate balancing act of optimizing Average Memory Access Time (AMAT) through Direct-Mapped vs. Set-Associative caches, and how modern designs use Miss Status Handling Registers (MSHRs) to overlap multiple cache misses concurrently.
* **Virtual Memory:** By decoupling the programmer's view of memory from the hardware's fragmented reality, Virtual Memory enables process isolation and multitasking. You will learn how Multi-Level Page Tables save massive amounts of RAM, and how the **Translation Lookaside Buffer (TLB)** acts as an ultra-fast cache to prevent translation latency from crippling the system.
* **Storage & Fault Tolerance:** The course scales out to the physics of DRAM (destructive reads, refreshing) and magnetic disks. Furthermore, as systems scale, hardware failure becomes a mathematical certainty. You will learn how architectures shift from assuming perfect hardware to designing resilient systems using ECC memory, Triple Modular Redundancy (TMR), and RAID storage.

### 4. The Multi-Core Era: Coherence, Consistency, and Concurrency (Modules 14-18)
Hitting the "Power Wall" forced the industry to pivot from faster single cores to Multi-Processing and Simultaneous Multithreading (SMT). This shift introduced the hardest challenges in modern architecture:
* **Cache Coherence:** When multiple cores have private L1 caches, sharing data becomes dangerous. You will study how hardware implements strict Coherence protocols (like MESI/MOESI) using snooping buses or directories to ensure that all cores share a unified, up-to-date view of a single memory location.
* **Memory Consistency:** While Coherence governs *one* memory location, Consistency governs the ordering of accesses across *multiple* locations. You will explore how strict Sequential Consistency crushes performance, and how Relaxed Consistency models require programmers to use explicit Memory Barriers (Fences) to prevent out-of-order networks from breaking synchronization logic.
* **Synchronization:** You will dive into the hardware primitives (like Atomic Test-and-Set and Load-Linked/Store-Conditional) required to build software locks and barriers, ensuring safe access to shared resources.

### Conclusion
High-Performance Computer Architecture is a masterclass in indirection, speculation, and managing tradeoffs. By studying how processors guess the future, rename reality, and maintain the illusion of sequential shared memory across chaotic distributed cores, you will gain the fundamental "hardware sympathy" required to write code that truly pushes the limits of modern computing.