# Playlist_1 Module 6 Notes: Operating Systems for Parallel Machines (Tornado & Corey Case Studies)

## Introduction
- **Focus:** Structuring an operating system for a shared memory multiprocessor.
- **Case Study:** **Tornado**, an OS designed specifically for shared memory multiprocessors.
- **Purpose:** Understand the principles that go into structuring an OS for parallel machines, specifically addressing synchronization, communication, scheduling, and scalability.

## Challenges of OS for Parallel Machines
Modern parallel machines present several challenges in converting algorithms into scalable implementations:
- **Size Bloat:** Added features lead to larger OS size, resulting in system software bottlenecks, especially for global data structures.
- **Memory Latency:** High latency (often a 100:1 ratio) to access memory outside the processor chip.
- **NUMA Architecture (Non-Uniform Memory Access):** Nodes (processor + memory) are connected via an interconnection network. Accessing remote memory is significantly slower than accessing local memory.
- **Deep Memory Hierarchy:** Multiple levels of caches exist before reaching main memory.
- **False Sharing:** 
  - **Definition:** Occurs when there is no programmatic sharing of data, but because memory touched by different threads on different cores happens to be on the same cache line (cache block), they appear to be shared due to the cache coherence mechanism.
  - **Cause:** Modern processors employ larger cache blocks to take advantage of spatial locality (reducing memory fetches, like a handyman bringing a tray of tools). Larger cache blocks increase the likelihood that distinct memory locations accessed by different threads fall on the same block.
  - **Effect:** Cache lines unnecessarily migrate between processors/cores, causing contention and reducing performance.
- **Goal for OS Designers:** Avoid false sharing, reduce write sharing on the same cache line, and ensure algorithms remain scalable despite NUMA effects, deep hierarchies, and increasing block sizes.

## Principles of Parallel OS Design
- **Cache-Conscious Decisions:** Pay attention to locality and exploit cache affinity in scheduling decisions.
- **Reduce Sharing of Data Structures:** Limiting the sharing of system data structures reduces contention.
- **Keep Memory Accesses Local:** Reduce the physical distance between the accessing processor and the memory to avoid traversing the interconnection network.

## Refresher on Page Fault Service
- **Normal Workflow:** 
  - CPU generates a virtual address -> Hardware looks up the TLB.
  - TLB miss -> Lookup Page Table.
  - Page Table miss -> **Page Fault** (the page is not in physical memory).
- **Page Fault Handler Workflow:**
  1. Locate the virtual page on the disk.
  2. Allocate a physical page frame.
  3. Perform I/O to move the page from the disk to the allocated physical memory frame.
  4. Update the Page Table (map virtual page to physical frame).
  5. Update the TLB.
- **Potential Bottlenecks:**
  - Generating virtual addresses and updating the TLB are thread/processor-specific (no serialization).
  - Allocating a physical page frame and updating the page table involve shared OS data structures, which can lead to serialization if not managed carefully.

## Parallel OS and Page Fault Service
- **Easy Scenario (Multi-process Workload):** Independent threads/processes (e.g., a web browser on one node, a word processor on another). Page faults are handled completely independently because threads are independent, and page tables are distinct. No serialization occurs.
- **Hard Scenario (Multi-threaded Workload):** A single process with multiple threads running concurrently on different nodes/cores. 
  - Threads share the same address space and the same page table.
  - TLBs across processors will have shared entries.
  - Naive handling requires locking the shared page table, leading to serialization.
  - **Goal:** Limit the sharing of OS data structures across processors to maintain scalability.

## Recipe for Scalable Structure in Parallel OS
1. **Determine Functional Requirements:** Identify what needs to be done (the functional part can be executed in parallel).
2. **Minimize Shared Data Structures:** Less sharing leads to more scalable implementations, enabling true concurrent execution.
3. **The Dilemma:**
   - Logically, a page table is a single shared data structure.
   - Using a single data structure requires a lock (creating a serial bottleneck).
   - Fully replicating the page table on all nodes requires heavy consistency management.
4. **The Trick:** Think logically about shared data structures, but physically replicate or partition them under the covers based on usage to reduce locking and increase concurrency.

## Tornado's Secret Sauce: Clustered Objects
- **Clustered Object:** 
  - **Definition:** An object that provides the illusion of a single object reference to all nodes, but under the covers, it may have multiple representations (replicas or partitions) across different nodes.
  - **Degree of Clustering:** The service implementer decides whether an object is a singleton, replicated per core, per CPU, or per group of processors.
- **Consistency Management:** Maintained through **Protected Procedure Calls (PPC)** executed across replicas in software, rather than relying on hardware cache coherence. 
  - Hardware cache coherence is indiscriminate and can cause unnecessary overhead when replicating purely logical OS structures.
- **Default Strategy:** When in doubt, use a single representation (singleton) and rely on hardware cache coherence as a safety net.

## Traditional Structure vs. Objectized VM Manager
- **Traditional Structure:** 
  - Centralized PCB (Process Control Block), global Page Table, and global TLB structures.
  - Backed by a single page cache in DRAM and storage.
- **Objectized Structure (Tornado VM Manager):**
  - **Process Object:** Equivalent to the PCB.
  - **Region Object:** The address space (page table) is split into manageable regions.
  - **File Cache Manager (FCM):** Knows the location of files on the backing store that correspond to a region.
  - **DRAM Object:** Manages physical page frames.
  - **Cached Object (CO):** Represents the page in physical memory and handles disk I/O.
- **Page Fault Workflow (Objectized):**
  1. Thread faults -> contacts the Process Object.
  2. Process Object identifies and routes to the specific Region Object.
  3. Region Object contacts the FCM.
  4. FCM identifies the backing file/offset and contacts the DRAM Object for a physical frame.
  5. CO performs I/O to pull data from disk into the frame.
  6. FCM notifies Region Object -> updates TLB via Process Object -> thread resumes.

## Advantages and Implementation of Clustered Objects
- **Replication/Partitioning Strategies:**
  - **Process Object:** Mostly read-only, replicated one per CPU.
  - **Region Object:** Partially replicated (e.g., per group of processors) based on which threads are accessing that region. Partitioned across the address space.
  - **FCM Object:** Partitioned based on the regions it backs.
  - **Cached Object (CO):** True shared object (singleton) since it deals with physical disk entities.
  - **DRAM Object:** Multiple representations (e.g., one per DSM piece in a node's physical memory).
- **Advantages:**
  - Single object reference across all nodes.
  - **Incremental Optimization:** Can dynamically adapt representations based on runtime usage patterns.
  - **Less Locking:** Operations like page fault handling scale with the number of processors.
  - Optimizes the common case (frequent page faults) at the expense of rare cases (region destruction takes longer because all replicas must be destroyed).
- **Translation Mechanism:**
  - **Translation Table:** Maps an object reference to a local representation in memory.
  - **Miss Handling Table:** If an object reference is missing locally, this maps it to an **Object Miss Handler**.
  - **Object Miss Handler:** Decides whether to create a new replica or point to an existing one, then installs the mapping in the Translation Table.
  - **Global Miss Handler:** If the local Miss Handling Table doesn't know the reference (because the table is partitioned), the Global Miss Handler (replicated on all nodes) locates the correct node that holds the Object Miss Handler for that reference.

## Non-Hierarchical Locking
- **Problem with Hierarchical Locking:** Locking the Process Object, then the Region Object, etc., kills concurrency. A lock on the Process Object would block other threads on the same CPU from servicing page faults for completely different regions.
- **Solution - Reference Counting (Existence Guarantee):**
  - Instead of locking objects along the path, Tornado uses **reference counting**.
  - When a thread accesses an object (e.g., Process Object), it increments its reference count.
  - This provides an **existence guarantee** (the object won't be destroyed or migrated while in use) without locking it exclusively.
  - Avoids hierarchical locking, promoting massive concurrency for independent operations.
  - Locks are encapsulated strictly within individual objects/replicas (the scope of the lock is limited).
  - Requires careful garbage collection and consistency management via Protected Procedure Calls.

## Dynamic Memory Allocation
- Centralized dynamic memory allocation is a massive serial bottleneck.
- **Solution:** Partition the heap space.
- The logical heap of a multi-threaded application is broken up into portions associated with the physical memories of the nodes where the threads are executing.
- Memory allocation requests are satisfied from local physical memory, scaling the allocation process and avoiding false sharing across nodes of the parallel machine.

## Inter-Process Communication (IPC)
- Tornado uses a microkernel-like design where clustered objects communicate via IPC to implement services.
- **Local IPC:** If the client object and server object are on the same processor, Tornado uses **handoff scheduling** (similar to LRPC) for efficient communication without a full context switch.
- **Remote IPC:** If the called object is on a remote processor, a full context switch is required.
- IPC is fundamental for implementing services and keeping object replicas consistent across processors (managed purely in software, independently of hardware cache coherence).

## Tornado Summary
- **Object-Oriented Design:** Promotes scalability.
- **Clustered Objects & Protected Procedure Calls:** Preserves locality while ensuring concurrency.
- **Reference Counting:** Avoids hierarchical locking; locks are confined to individual objects.
- **Dynamic Adaptation:** Multiple implementations of the same object are possible based on usage patterns (incremental optimization).
- **Optimize Common Case:** Fast page fault handling is prioritized over infrequent operations like region destruction.
- **Limit Sharing:** Replicating and partitioning critical data structures under the covers is the key property for promoting scalability.

## Summary of Ideas in Corey System (MIT)
- **Goal:** Limit the sharing of kernel data structures to avoid contention and increase concurrency.
- **Application Hints:** Corey involves applications giving explicit hints to the kernel.
- **Address Ranges:** Similar to Tornado's regions, but explicitly exposed to the application. Threads declare the address ranges they will operate in, allowing the kernel to optimize scheduling and data structure placement.
- **Shares:** A thread can declare that a system facility (like an opened file descriptor) will not be shared with any other threads. This allows the kernel to bypass consistency management across cores for that specific object.
- **Dedicated Cores:** Dedicate specific cores solely for kernel activity. This confines the locality of kernel data structures to a few cores, heavily reducing inter-core communication latency.

## Virtualization and Cellular Disco (Stanford)
- **Problem:** Building, optimizing, and rewriting OSs and device drivers for every new parallel architecture is a massive pain point. I/O management is particularly hairy.
- **Solution:** Virtualization via **Cellular Disco**.
- **Architecture:** Cellular Disco acts as a thin Virtual Machine Monitor (VMM) sitting between the physical hardware (e.g., 32-node SGI Origin 2000) and a Guest OS. It runs as a multi-threaded kernel process on top of a Host OS (e.g., IRIX).
- **Trap and Emulate for I/O:**
  1. Guest OS makes an I/O request -> Traps into the VMM (Cellular Disco).
  2. VMM rewrites the request to appear as if it's coming from itself, and passes it to the Host OS.
  3. VMM registers a callback for completion.
  4. Upon I/O completion, the hardware interrupt goes to the Host OS, which routes it to the VMM.
  5. The VMM fakes a completion interrupt back to the Guest OS.
- **Benefits:**
  - Reuses existing Host OS device drivers (no need to rewrite complex third-party I/O code).
  - Shown by construction that a VMM can manage multiprocessor resources efficiently (virtualization overhead is kept under 10% for many applications).
