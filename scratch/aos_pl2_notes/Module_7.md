# Module 7: Distributed Shared Memory (DSM)

## 1. Introduction & Motivation
*   **Goal**: Create an operating system abstraction that provides an illusion of shared memory to applications, even when nodes in a local area network (LAN) do not physically share memory.
*   **Intuition**: Fast modern networks make remote memory access potentially faster than local disk access.
*   **Benefit**: Makes a cluster look like a shared memory machine, significantly simplifying application development for distributed systems.

## 2. Cluster as a Parallel Machine
When starting with a sequential program, there are different ways to exploit a cluster's multiple processors:

### Implicitly Parallel Programs (Automatic Parallelization)
*   **Concept**: Write a sequential program and rely on an automatic parallelizing compiler to identify and map parallelism to the cluster.
*   **Example**: High Performance Fortran (uses user-assisted directives for data/computation distribution).
*   **Pros/Cons**: Does the heavy lifting for the programmer but is mostly limited to programs with static, compile-time determinable data accesses. Limits the potential for exploiting all available parallelism.

### Explicitly Parallel Programs
Programmers explicitly write parallel code. System support comes in two main styles:

#### A. Message Passing
*   **Concept**: The runtime system provides a library with primitives for threads to send/receive messages to peers on other nodes.
*   **Examples**: MPI (Message Passing Interface), PVM.
*   **Characteristics**:
    *   True to the physical nature of a cluster (private memory, network communication).
    *   **Downside**: Difficult transition for programmers used to sequential/shared-memory paradigms. Requires a radical shift in thinking (coordinating via messages rather than shared data structures).

#### B. Distributed Shared Memory (DSM)
*   **Concept**: A library provides the illusion that all memory across the cluster is shared.
*   **Characteristics**:
    *   Easier transition from sequential or Symmetric Multiprocessing (SMP) programming (e.g., using `pthreads`).
    *   No need for marshalling/unmarshalling arguments.
    *   Allows the use of familiar synchronization primitives (locks, barriers).

## 3. History of Shared Memory Systems
*   **Software DSM**: Started in the mid-80s (IV at Yale, Clouds at Georgia Tech, Mirage at UPenn). Continued in the 90s (Munin, TreadMarks) and late 90s (Blizzard, Shasta, Cashmere).
*   **Structured Objects**: Systems like Linda, Orca, and Stampede provided higher-level abstractions than raw memory (e.g., distributed data structures).
*   **Hardware Shared Memory**: Mid-80s (BBN Butterfly, Sequent Symmetry). 90s (KSR1, MIT Alewife, Stanford DASH). Commercial systems later scaled this up (SGI Origin 2000, IBM Blue Gene).
*   **Modern Landscape**: Clusters of SMPs have become the workhorses in data centers and High-Performance Computing (HPC).

## 4. Shared Memory Programming Concepts
*   **Two Types of Memory Accesses**:
    1.  **Normal Accesses**: Reads/writes to shared data manipulated by threads.
    2.  **Synchronization Accesses**: Reads/writes to variables used by the OS/threads library to implement locks and barriers.
*   **Synchronization Primitives**:
    *   *Mutual Exclusion Locks*: Protect data structures for exclusive modification.
    *   *Barriers*: Synchronize execution phases across multiple threads.

## 5. Memory Consistency and Cache Coherence
*   **Memory Consistency Model**: The "Contract" (The *When*). Defines when a modification to a shared memory location by one processor becomes visible to others.
*   **Cache Coherence**: The "Implementation" (The *How*). How the system software and hardware work together to fulfill the consistency contract.

### Sequential Consistency (SC) Model
*   **Concept**: Memory accesses happen in their exact textual/program order. Individual read/write operations are atomic.
*   **Interleaving**: The global order of accesses from multiple processors is an arbitrary interleaving (like a perfect merge-shuffle of card decks), but the individual program order is always preserved.
*   **The Problem with SC in Parallel Programs**:
    *   SC does not distinguish between normal data accesses and synchronization accesses.
    *   It forces coherence actions on *every* read/write access.
    *   Even if a programmer uses a lock to protect a critical section, SC enforces coherence for every access inside the critical section immediately, causing unnecessary overhead and poor scalability.

### Release Consistency (RC) Model
*   **Concept**: Distinguishes between normal accesses and synchronization accesses, mapping the latter into *Acquire* and *Release* operations.
    *   *Lock Acquire / Barrier Arrival* = Acquire Operation.
    *   *Lock Unlock / Barrier Departure* = Release Operation.
*   **Mechanism**:
    *   Coherence actions for normal data accesses do not block the processor immediately.
    *   The system only ensures all prior coherence actions are globally complete when it encounters a **Release** operation.
*   **Advantage**: Overlaps computation with communication. No waiting for coherence on every memory access, resulting in better performance than SC.

#### Eager RC vs. Lazy RC (LRC)
*   **Eager RC (Push Model)**:
    *   At the point of *Release*, all coherence actions (modifications) are broadcast to all processors that hold a copy of the modified data.
    *   Ensures the entire system is cache coherent at the release point.
*   **Lazy RC (Pull Model)**:
    *   Takes advantage of *procrastination*. At the point of *Release*, no global communication occurs.
    *   Coherence actions are deferred until the next *Acquire* of the same lock by another processor.
    *   The acquiring processor *pulls* the necessary coherence updates from the previous lock holder.
*   **Pros & Cons**:
    *   *Lazy RC Pros*: Fewer communication events/messages on the network (point-to-point instead of broadcast).
    *   *Lazy RC Cons*: Increased latency at the point of acquire, as the processor must wait for coherence actions to complete before proceeding.

## 6. Software DSM Implementation
Implementing fine-grained, word-level coherence purely in software incurs too much overhead.

### Page-Based Coherence
*   **Granularity**: Coherence is maintained at the level of a memory page (e.g., 4KB or 8KB).
*   **Mechanism**: The DSM software cooperates with the OS Virtual Memory (VM) manager to provide a *Global Virtual Memory* abstraction (address equivalence across all nodes).
*   **Distributed Ownership**:
    *   The global address space is partitioned. Each node acts as the "owner" for a subset of pages.
    *   The owner maintains a directory with metadata about which nodes currently share the page.
*   **Page Fault Handling**:
    1.  When a thread accesses a non-resident page, a page fault occurs.
    2.  The OS passes the fault to the DSM software.
    3.  DSM software contacts the page's owner to find the node holding the current copy.
    4.  The page is fetched, loaded into local physical memory, and the VM page table is updated.
    5.  The thread resumes execution.

### Single Writer Protocol
*   Multiple readers can share a page simultaneously.
*   If a node wants to write to a page, it must inform the page owner.
*   The owner invalidates all other copies of the page in the cluster to give the writer exclusive access.

### The False Sharing Problem
*   **Cause**: A page is a large unit of memory. Multiple independent data structures (protected by different locks) might reside on the same page.
*   **Effect**: If Processor 1 writes to Data A and Processor 2 writes to Data B (both on the same page), the single writer protocol will constantly invalidate and transfer the page back and forth between the processors.
*   **Result**: The page "ping-pongs" across the network, severely degrading performance, even though the threads are perfectly synchronized and not logically sharing data. Page-level granularity and independent data structures don't live happily together.
