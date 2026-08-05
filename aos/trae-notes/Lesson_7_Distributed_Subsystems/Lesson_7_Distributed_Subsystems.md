# Lesson_7_Distributed_Subsystems (Synthesized Notes)

> **Purpose:** To understand how distributed subsystems (Global Memory System, Distributed Shared Memory, and Distributed File Systems) leverage fast local area networks to aggregate and manage resources across a cluster, providing the illusion of a single, powerful machine and mitigating individual node bottlenecks.
> 
> **Philosophy:** Trust the network to be faster than local disk I/O. By decentralizing management, distributing data structures, and utilizing peer nodes' idle resources (cooperative caching), the system can improve overall throughput, availability, and scalability.
> 
> **Mental Model:** Imagine a cluster of computers as a single large office building. Instead of each worker (node) relying solely on their own small desk (local memory) and a slow filing cabinet (local disk), they can instantly borrow empty desk space from coworkers (GMS), seamlessly share a giant whiteboard (DSM), and collectively organize a massive, distributed filing system where anyone can fetch a document from whoever currently holds it (DFS/xFS).
> 
> **Connective Information:** This lesson bridges the gap between single-node OS resource management and distributed systems. It scales local virtual memory concepts (paging, working sets) and multiprocessor cache coherence across a LAN. These foundational thought experiments paved the way for modern data center architectures, cloud computing, and large-scale distributed storage systems.

# Playlist 2: Module 6 - Distributed Systems (Global Memory System)

## 1. Introduction
- **Distributed Systems Innovation:** Technological innovations in distributed systems often emerge from academia due to a lack of market or compliance pressures, leading to "out-of-the-box" thinking.
- **Enduring Value:** The byproducts and implementation techniques of thought experiments often have a more lasting impact than the original visions (e.g., Java emerged from failed video-on-demand trials).
  > **Background Context:** Many foundational distributed systems principles, such as virtual time or distributed consensus algorithms (like Paxos), were born out of theoretical thought experiments long before they were practically required by industry.
- **Core Theme of Module:** Memory is a critical, precious resource. Advances in local area network (LAN) technology allow leveraging the idle physical memory of peer nodes in a cluster to overcome local memory shortages.
- **Three Subsystems Discussed:**
  1. **Global Memory System (GMS):** Using peer memory for paging across a LAN.
  2. **Distributed Shared Memory (DSM):** Providing a shared memory abstraction in a cluster.
  3. **Distributed File System:** Using cluster memory for cooperative caching of files.

## 2. Context for Global Memory System (GMS)
- **Virtual Memory Manager (VMM):** Gives processes the illusion of having a large virtual address space, even though only a portion (the **working set**) is actually loaded into physical memory. Missing pages are swapped in and out from the disk.
  > **Conceptual Framework:** Virtual memory acts as a level of indirection, decoupling the memory addresses used by a program from the physical memory locations. This allows the OS to seamlessly shuffle data between RAM and slower storage without the program's knowledge.
- **Memory Pressure:** The amount of physical memory required to keep all currently executing processes on a node running efficiently. Memory pressure varies across nodes in a LAN; some nodes are heavily loaded, while others sit idle.
- **The GMS Concept:** Instead of paging out to a slow local disk when experiencing memory pressure, a node can page out to the idle physical memory (cluster memory) of a peer node over the network.
  > **Intuition:** Think of GMS like borrowing a neighbor's empty garage when your own house is full, instead of driving all the way to a public storage unit (the disk).
- **Network Speeds:** Gigabit and 10-Gigabit Ethernet make fetching a page from a remote node's memory faster than local disk I/O (which is bound by seek and rotational latency, typically capping around 200 MB/s).
  > **Background Context:** In the era when GMS was conceived, local disk seek times were painfully slow, often measured in milliseconds, while network latencies on local area networks \(LANs\) were dropping to microseconds, shifting the bottleneck from the network to the disk.
- **Extended Memory Hierarchy:** Processor $\rightarrow$ Caches $\rightarrow$ Main Memory $\rightarrow$ **Cluster Memory (via GMS)** $\rightarrow$ Disk.
- **Reliability:** GMS trades network communication for disk I/O **only for reads**. Writes still go to the disk (the disk always holds a copy of all pages). GMS only houses clean (non-dirty) pages in peer memory. If a node crashes, no data is lost because the disk retains the master copies.

## 3. GMS Basics
- **Cache:** In GMS terminology, "cache" refers strictly to Physical Memory (DRAM).
  > **Common Confusion:** In the context of GMS, "Global Memory" does not mean memory that is actively shared by multiple processes across the cluster (like in DSM). Instead, it acts merely as a remote paging disk for the private pages of other nodes.
- **Memory Split:** Physical memory on each node is dynamically partitioned into two parts:
  - **Local Part:** Holds the working set of currently executing processes on the local node.
  - **Global Part:** The "community service" portion. It acts as a surrogate for the disk, holding pages swapped out by peer nodes on the network.
- **Dynamic Boundary:** The boundary between Local and Global memory shifts based on node activity. An idle workstation shrinks its Local part and expands its Global part to serve peers.
- **Page States:**
  - **Private:** A page exclusive to a single process.
  - **Shared:** A page actively used by processes spanning multiple nodes.
  - *Rule:* The **Global Part** only ever holds **Private** (and clean) pages. The **Local Part** can hold Private or Shared pages.
- **Coherence:** GMS does **not** manage memory coherence for shared pages. GMS acts strictly as a paging facility; coherence is an application-level problem.
  > **Conceptual Framework:** Coherence ensures that multiple copies of the same data remain consistent across different nodes. By leaving coherence to the application, GMS drastically simplifies its own design, focusing solely on efficient page transport.
- **Page Replacement:** GMS aims to approximate a **Global LRU (Least Recently Used)** algorithm, ensuring the globally oldest page across the entire cluster is the one evicted to the disk when total cluster memory is full.
  > **Example:** If Node A is heavily utilized but Node B has been idle for hours, a Global LRU policy ensures that Node B's stale memory pages are flushed to disk first to accommodate Node A's overflow, rather than forcing Node A to evict its own recently used pages.

## 4. Handling Page Faults (Four Scenarios)
When a node (Host P) page faults on a page $X$, GMS locates the page.

* **Case 1: $X$ is in a peer's Global Cache (Common Case)**
  - $X$ is located in Host Q's global cache and sent to P.
  - **Host P:** Local memory increases by 1 (adds $X$ to working set), Global memory decreases by 1. P sends its oldest global page ($Y$) to Q to make room.
  - **Host Q:** Trades $Y$ for $X$. No change to Local/Global split.
* **Case 2: Memory pressure on P is excessive (P's Global Cache is empty)**
  - P's Global part is already 0. P replaces an older page from its own Local part to make room for $X$.
  - **Host P:** No change to Local/Global split (replaces a local page with another local page).
  - **Host Q:** Remains unchanged.
* **Case 3: Faulting page is only on the Disk**
  - P fetches $X$ from the disk. (P's Local +1, Global -1).
  > **Hypothetical:** If the network goes down, GMS essentially degrades to traditional local disk paging. The node would simply fetch $X$ from its local disk and evict an older page to its local disk, losing the benefit of cluster memory but maintaining basic functionality.
  - P sends an arbitrary Global page to Host R (the node with the *globally oldest* page in the cluster).
  - **Host R:** Evicts its globally oldest page to the disk. 
    - If R's oldest page was Global: No change to R's Local/Global split.
    - If R's oldest page was Local: R's Local shrinks by 1, Global increases by 1 (increasing its capacity for community service).
* **Case 4: Faulting page is actively shared**
  - $X$ is actively used in Host Q's Local cache. Q keeps its copy; a new copy is sent to P.
  - **Host P:** Local +1, Global -1.
  - **Host Q:** Unchanged.
  - Total cluster memory pressure increases by 1. P must send a Global page to Host R (node with the globally oldest page), causing R to evict a page to the disk.

## 5. Age Management ("Geriatrics")
GMS approximates Global LRU without overloading any single node. Management is distributed across **Epochs**.

- **Epoch Parameters:** An epoch is bounded by time ($T$, e.g., a few seconds) or space ($M$ page replacements, e.g., thousands).
- **The Initiator (Manager):** At the start of an epoch, all nodes send the age of their pages to the Initiator node.
- **Initiator Computations:**
  1. **Minimum Age:** The age of the $M$-th oldest page. Any page older than this is slated for replacement in the upcoming epoch.
  2. **Weight Distribution ($W_i$):** The fraction of the $M$ replacements expected to come from each node $i$.
  > **Conceptual Framework:** The use of Epochs limits the frequency of global coordination. Instead of calculating global state on every single page fault—which would overwhelm the network—nodes periodically synchronize and then act independently using slightly stale but \"good enough\" information.
- **Manager Handoff:** To distribute load, the Initiator for the *next* epoch is chosen as the node with the highest weight (the least active node hosting the oldest pages). Nodes determine this locally from the weight distribution vector.
- **Acting Locally (Page Eviction):**
  - When evicting a page, a node checks its age against the **Minimum Age**.
  - **If Age > Minimum Age:** The page is discarded immediately (it was going to be replaced to disk this epoch anyway).
  - **If Age < Minimum Age:** The page is active. The node sends it to a peer node's global cache. The target peer is selected probabilistically based on the weight distribution ($W_i$).
- **Philosophy:** Think Globally (Epoch setup/Min Age calculation), Act Locally (Page faults/Evictions).
  > **Example:** An initiator determines the global minimum age is 5 minutes. When a node needs to evict a page, it looks at its own pages. If a page is 6 minutes old, it's discarded (older than global min). If it's 3 minutes old, it's sent to a peer's global cache because it's still relatively "young" globally.

## 6. Implementation in Unix (OSF/1)
GMS was implemented on DEC's OSF/1 operating system, requiring modifications to the OS core.

- **OS Memory Components:**
  - **Virtual Memory Manager (VM):** Manages process virtual address space (Heap, Stack). Handled pages are called **Anonymous Pages**.
  - **Unified Buffer Cache (UBC):** Caches file system reads/writes and memory-mapped files.
- **GMS Integration:** VM and UBC are modified to call GMS instead of the disk when page faults occur. Clean page evictions are intercepted by GMS to be sent to cluster memory.
- **Collecting Age Information:**
  - *UBC Pages:* Easy to track because applications make explicit read/write system calls.
  - *Anonymous Pages (VM):* Difficult because CPU hardware handles memory access. GMS solves this by having a daemon periodically dump the **Translation Lookaside Buffer (TLB)** contents to track recently accessed pages.
    > **Background Context:** The Translation Lookaside Buffer (TLB) is a hardware cache within the CPU that speeds up virtual-to-physical address translations. By observing which pages are in the TLB, the OS can infer which pages have been recently accessed by the CPU.
- **Paging Daemon:** Modified to trigger when the free list falls below a threshold. Instead of dropping clean pages to the disk, it passes them to GMS to route to peer nodes based on weight information.

## 7. Distributed Data Structures
GMS uses specialized structures to map virtual addresses across the cluster.

- **Universal ID (UID):** Converts a local virtual address into a globally unique identifier. 
  - `UID = [IP Address] + [Disk Partition] + [Inode] + [Offset]`
  > **Example:** A local address like `0x00400000` might be translated into a UID like `[192.168.1.10] + [Disk 2] + [Inode 45] + [Offset 8192]`, ensuring that even if another node uses `0x00400000`, the underlying UID remains distinct.
- **Core Data Structures:**
  1. **PFD (Page Frame Directory):** Equivalent to a page table. Maps a UID to a specific Physical Page Frame. (States: Local-Private, Local-Shared, Global-Private, Disk).
  2. **GCD (Global Cache Directory):** Maps a UID to the Node ID that currently holds the PFD for that page.
  3. **POD (Page Ownership Directory):** A globally replicated structure. Maps a UID to the Owner Node ID (the node responsible for keeping the GCD for that UID space).
- **Page Fault Lookup Flow:**
  - `Virtual Address` $\rightarrow$ `UID` $\rightarrow$ Look up `POD` $\rightarrow$ Contact `Owner Node` $\rightarrow$ Look up `GCD` $\rightarrow$ Contact `PFD Node` $\rightarrow$ Fetch Page.
- **Performance Optimization (The Common Case):**
  - For non-shared pages, the POD, GCD, and faulting process usually reside on the **same node**.
  - Network communication is heavily reduced; external calls are typically only required to actually fetch the page from the remote PFD node, not to perform the lookups.
  > **Conceptual Framework:** Optimizing for the common case is a classic systems design principle. Since most memory pages are private to a single node, ensuring that local lookups bypass the network entirely yields massive performance gains on average.

## 8. Conclusion
- Taking a distributed systems concept (like network paging) to full implementation requires heavy lifting, especially in OS modification and corner-case handling.
- While paging over a LAN was a thought experiment suitable for its time, its true value shines in modern **Data Centers** where thousands of nodes are centrally owned and operated.
- The enduring contributions of GMS are its **distributed data structures**, **decentralized algorithms**, and **age management techniques**, which remain highly relevant in modern systems research.

---

# Module 7: Distributed Shared Memory (DSM)

## 1. Introduction & Motivation
*   **Goal**: Create an operating system abstraction that provides an illusion of shared memory to applications, even when nodes in a local area network (LAN) do not physically share memory.
*   **Intuition**: Fast modern networks make remote memory access potentially faster than local disk access.
*   **Benefit**: Makes a cluster look like a shared memory machine, significantly simplifying application development for distributed systems.
    > **Conceptual Framework:** The shared memory abstraction hides the complexity of network programming. Developers don't need to manually serialize data, manage sockets, or handle network timeouts; they simply read and write to memory addresses as if they were on a single computer.

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
    > **Example:** In an MPI program, if Node A needs the result of a computation from Node B, Node B must explicitly execute an `MPI_Send` command, and Node A must explicitly execute an `MPI_Recv` command, requiring tight coordination between the two codebases.

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
    > **Tradeoff:** Sequential Consistency provides an intuitive and easy-to-reason-about programming model at the cost of high communication overhead and poor scalability. Weaker consistency models (like RC) trade off this simplicity for significantly better performance by reducing coherence traffic.

### Release Consistency (RC) Model
*   **Concept**: Distinguishes between normal accesses and synchronization accesses, mapping the latter into *Acquire* and *Release* operations.
    *   *Lock Acquire / Barrier Arrival* = Acquire Operation.
    *   *Lock Unlock / Barrier Departure* = Release Operation.
*   **Mechanism**:
    *   Coherence actions for normal data accesses do not block the processor immediately.
    *   The system only ensures all prior coherence actions are globally complete when it encounters a **Release** operation.
*   **Advantage**: Overlaps computation with communication. No waiting for coherence on every memory access, resulting in better performance than SC.
    > **Intuition:** Sequential Consistency is like a group of people writing a book where everyone must immediately broadcast every single word they write. Release Consistency is like letting everyone write a whole chapter locally, and only sharing their work when they officially "publish" (release) the chapter.

#### Eager RC vs. Lazy RC (LRC)
*   **Eager RC (Push Model)**:
    *   At the point of *Release*, all coherence actions (modifications) are broadcast to all processors that hold a copy of the modified data.
    *   Ensures the entire system is cache coherent at the release point.
*   **Lazy RC (Pull Model)**:
    *   Takes advantage of *procrastination*. At the point of *Release*, no global communication occurs.
    *   Coherence actions are deferred until the next *Acquire* of the same lock by another processor.
    *   The acquiring processor *pulls* the necessary coherence updates from the previous lock holder.
    > **Hypothetical:** Under Eager RC, if a node releases a lock after modifying 100 pages, it instantly broadcasts those 100 pages to all other nodes, creating a massive network spike. Under Lazy RC, those pages are only sent later, and only to the specific nodes that actually request the lock, drastically smoothing out network traffic.
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
    > **Example:** Imagine two students writing different chapters of a book on the same physical piece of paper. Even if they are writing in different margins (no logical overlap), they must constantly pass the paper back and forth to write. This is false sharing: the physical medium (the page) is shared, even though the logical data is not.


---

# Module 8: Distributed Shared Memory (DSM) and Distributed File Systems (DFS)

## 1. Lazy Release Consistency (LRC) with Multi-Writer Coherence Protocol
- **Overview**: A protocol that maintains coherence at the page granularity (to integrate with the OS) while allowing multiple writers to simultaneously modify the same page. This is critical for preventing false sharing when different data structures reside on the same page.
- **Mechanism (TreadMarks System)**:
  - A processor (e.g., P1) acquires a lock (`L`) and modifies data structures contained within pages (e.g., X, Y, Z).
  - The OS has no knowledge of the association between the lock `L` and the modified pages; it only knows these pages were modified during the critical section.
  - At the release of the lock, the system computes a **diff** between the original page and the modified page (e.g., XD, YD, ZD).
- **Lock Acquisition and Invalidation**:
  - When another processor (e.g., P2) requests the same lock `L`, the DSM software invalidates the local copies of the pages known to be modified by the previous lock holder.
  - This invalidation at lock acquisition is consistent with the **Lazy Release Consistency (LRC)** model.
- **Procrastinated Updates**:
  - When P2 enters its critical section and accesses an invalidated page (e.g., X), a page fault occurs.
  - The DSM software fetches the original, pristine version of the page from the page's owner.
  - It also fetches the diff(s) created by previous lock holder(s) and applies them to the original page to construct the current version.
  - If multiple processors modified the page under the same lock previously, all relevant diffs are applied in order.
- **Handling Multiple Writers**:
  - Different threads on different processors can modify the same page simultaneously, provided they use **different locks** (e.g., P1 uses `L1`, P4 uses `L2`).
  - Diffs are strictly associated with the specific lock governing the critical section.
  - When P2 acquires `L1`, it only fetches diffs associated with `L1`, safely ignoring changes made under `L2`. This avoids unnecessary communication.
  > **Example:** If Page X contains an array `A` protected by lock `L1` and an array `B` protected by lock `L2`. P1 modifies `A` under `L1`, and P3 modifies `B` under `L2`. When P2 acquires `L1`, it only pulls the diffs for `A`, avoiding the false sharing overhead that would occur if the entire page was invalidated.

## 2. Implementation of Multi-Writer Protocol
- **Twin Creation**:
  - When a thread first writes to a page (e.g., X), the OS creates a **twin** (an exact physical memory copy of the original page).
  - The twin is not mapped into the page table; it serves purely as a backup.
  - The original page is made writable so the thread can modify it.
- **Diff Computation (at Release)**:
  - At the lock release point, the DSM software compares the modified page with the twin.
  - It creates a **run-length encoded diff** (recording the starting point, length, and content of the changes) to save space, as typically only portions of a page are modified.
  - After diff computation, the original page is **write-protected** to ensure any future writes trigger coherence actions.
  - The twin is destroyed, freeing up physical memory.
  > **Conceptual Framework:** Run-length encoding (RLE) is a simple form of data compression where sequences of identical data values are stored as a single data value and count. In diffs, it efficiently encodes contiguous blocks of unmodified memory.
- **Garbage Collection and Reuse**:
  - The diff is kept on the node to be provided to future lock acquirers.
  - Once updated via diffs upon a subsequent page fault, the page becomes ready for the new lock holder.

## 3. Non-Page-Based DSM
To avoid page-level false sharing entirely, some systems track coherence at a finer granularity without relying on OS page faults.
- **Library-Based DSM**:
  - Shared variables are explicitly annotated using a programming library.
  - The compiler/binary inserts a trap at every point of access to these shared variables.
  - The trap invokes the DSM software to handle coherence (e.g., fetching data) without requiring OS page-level support.
  - *Examples*: Shasta (DEC), Beehive (Georgia Tech).
  > **Background Context:** Binary instrumentation tools (like Pin or Valgrind) can insert these traps by modifying the compiled executable code on the fly, allowing DSM to be implemented without changing the OS or requiring specialized hardware.
- **Structured DSM**:
  - Coherence is maintained at the level of application-meaningful data abstractions rather than memory locations.
  - These abstractions are manipulated via API calls provided by the language runtime.
  - The runtime handles necessary coherence actions and data fetching during the API call.
  - *Examples*: Linda, Orca, Stampede (Georgia Tech), Stampede RT, PTS (Persistent Temporal Streams).
  > **Intuition:** Instead of sharing raw memory addresses (which the OS manages), structured DSM shares higher-level programming constructs like objects, queues, or tuples (which the language runtime manages).

## 4. DSM Scalability and Speedup
- **Expectation vs. Reality**: Developers expect linear performance scaling as processors are added. However, software-implemented DSM introduces increasing communication overhead, which mitigates actual speedup.
- **Computation-to-Communication Ratio**:
  - For speedup, computation must significantly outweigh communication.
  - "Shared memory scales really well when you don't share memory." (Chuck Thacker).
  - Critical sections must be substantial (Hefty) to justify the coherence overhead.
- **The Problem with Pointers**:
  - Code with dynamic data structures manipulated via pointers can lead to severe implicit network communication.
  - Following a pointer might transparently trigger a fetch across the LAN.
  - Pointer-heavy code is the "bane of distributed shared memory."
  > **Example:** Traversing a linked list where each node happens to reside on a different machine's memory would cause a network fetch for every single `next` pointer dereference, reducing performance to a crawl compared to an array-based structure.
- **Conclusion**:
  - Traditional DSM (a shared memory threads package for a cluster) is effectively dead.
  - **Structured DSM** remains attractive for reducing the programming burden in distributed applications.

## 5. Network File Systems (NFS)
- **Trivia**: The first Network File System (NFS) was built by **Sun Microsystems** in **1985**.
- **Centralized Architecture**:
  - Clients distributed over a LAN access a central file server.
  - To mitigate slow disk speeds, the server caches retrieved files in its memory.
- **Bottlenecks**:
  - A single centralized server limits scalability.
  - The server's I/O bus bandwidth is limited for fetching data and metadata.
  - The file cache is constrained by the memory capacity of the single server.
  > **Background Context:** The centralized nature of early NFS made it highly susceptible to the \"thundering herd\" problem, where hundreds of client machines booting up simultaneously would all request their OS binaries from the single server, bringing it to a standstill.

## 6. Distributed File Systems (DFS)
- **Vision**: Distribute files and metadata across several servers in the network to eliminate centralized bottlenecks.
- **Benefits**:
  - **Aggregated I/O Bandwidth**: Clients can retrieve data from multiple servers simultaneously.
  - **Distributed Metadata**: Management is spread across multiple nodes.
  - **Cooperative Caching**:
    - The file cache expands to include the memory of all servers (and potentially clients).
    - Avoids disk accesses by retrieving data from a peer's memory if they recently accessed it.
- **Serverless File System**:
  - In extreme cases, all nodes in the cluster act interchangeably as clients and servers, distributing management, serving, and caching equally.

## 7. Lesson Outline & Prerequisites
- **Goal**: Intelligently utilize cluster memory for metadata management and cooperative file caching to minimize slow disk access.
- **Prerequisites**: A solid understanding of file systems is essential (e.g., comparable to the undergraduate systems course CS 2200 at Georgia Tech).


---

# Module 9: Distributed File Systems and xFS

## 1. Stripe Groups
Subsetting storage servers into **stripe groups** for striping log segments avoids the "small write pitfall" and provides several key benefits:
* **Parallel Client Activities**: 
  * Different log segments are assigned to different clients.
  * Allows client activities corresponding to different stripe groups to occur in parallel.
  * Increases server availability because different subsets of servers handle different client requests, resulting in higher overall throughput.
* **Efficient Log Cleaning**:
  * Different cleaning servers can be assigned to different stripe groups, increasing parallelism in distributed file system (DFS) management.
  * Essential because logs must be cleaned periodically as new writes overwrite old files.
  > **Conceptual Framework:** Log-structured file systems write all modifications sequentially to a log, rather than updating blocks in place. This makes writes extremely fast but requires a background \"cleaning\" process to compact the log and reclaim space from deleted or overwritten files.
* **Increased Availability & Fault Tolerance**:
  * The system can survive multiple server failures. If disks in one stripe group fail, clients served by other stripe groups remain unaffected.
  * Allows incremental satisfaction of the user community despite partial system failures.

## 2. Cooperative Caching
xFS utilizes client memories to cooperatively cache files, reducing the load on the storage servers and minimizing disk access.
* **Cache Coherence**: 
  * Unlike traditional Unix file systems (which serve clients independently without worrying about sharing), xFS strictly maintains cache coherence.
  * **Semantics**: Single Writer, Multiple Readers (a file can have multiple concurrent readers but only one writer at any time).
  * **Granularity**: Coherence is maintained at the **file block level**, not the entire file.
* **Write Protocol & Conflict Resolution**:
  1. The metadata manager tracks which client caches hold specific file blocks.
  2. If a client wants to write to a block that is currently being read by others (read-write conflict), the manager sends **invalidation messages** to the current holders.
  3. Clients acknowledge the invalidation, discarding their local copies.
  4. The manager grants a **write token** to the requesting client.
  5. The manager can revoke this token if a future read or write request occurs.
* **Cooperative Caching Mechanism**:
  * When a read request arrives, the manager can redirect the request to a peer client that already holds the file block in its cache, satisfying the read via network transfer rather than disk access.
  > **Example:** Client A reads a popular library file. Later, Client B needs the same file. Instead of the manager fetching it from the slow storage server, the manager tells Client B to fetch it directly from Client A's memory cache.

## 3. Log Cleaning
As clients continuously write and overwrite data, old blocks in log segments become stale (creating "holes"), necessitating log cleaning to reclaim disk space.
* **The Cleaning Process**:
  1. Identify the utilization status of old log segments.
  2. Select a set of segments to clean.
  3. Read and aggregate all **live (valid) blocks** from these segments into a new, contiguous log segment.
  4. Garbage collect (delete) the old, fragmented log segments.
  > **Example:** Imagine a log segment is a notebook page. You wrote a rough draft (valid blocks), then crossed out half of it (invalid blocks). Cleaning is like copying only the readable sentences onto a brand-new page and throwing the messy old page away.
* **Distributed Log Cleaning in xFS**:
  * **Client Responsibility**: Clients (mutators) track segment utilization for the files they write and handle log cleaning concurrently with normal file operations. Any node can act as a client or server.
  * **Stripe Group Leader**: Each stripe group has a leader that assigns cleaning tasks to the members of its group.
  * **Conflict Resolution**: The metadata manager resolves conflicts between client updates (modifying segments) and cleanup functions (garbage collecting segments).

## 4. xFS Data Structures
To implement a truly distributed file system where the metadata manager may not reside on the same node as the file or client, xFS uses several specialized data structures. (Note: Traditional Unix uses inodes mapping filenames to disk blocks).
* **Manager Map**: A globally replicated data structure at every node that maps a filename to its designated metadata manager node.
  > **Hypothetical:** If you add a new node to the xFS cluster, the Manager Map must be updated across all existing nodes to rebalance the metadata management load, ensuring the new node takes its fair share of directory lookups.
* **File Directory**: Used by the manager to map a filename to an Index Number (I-number).
* **I-Map**: Maps the I-number to the inode address for the log segment associated with the file.
* **Stripe Group Map**: Maps the log segment ID to the specific stripe group (storage servers) that holds the actual data blocks.

## 5. File Access Paths
### Reading a File
xFS uses caching extensively to avoid the expensive worst-case path for file reads:
1. **Path 1: Local Cache (Fastest)**
   * Client looks up the directory to get the index and offset.
   * Finds the data block in its own local UNIX file cache. No network hops required.
2. **Path 2: Cooperative Caching (Second Best)**
   * Not in local cache. Client consults the **Manager Map** and contacts the Manager Node.
   * Manager's metadata indicates another client has the block cached.
   * Manager requests the peer client to send the data directly to the requester.
   * Faster than disk access because network speeds exceed disk speeds (involves up to 3 network hops).
3. **Path 3: The Long Way (Disk Access - Worst Case)**
   * Not in any cache. Client contacts the Manager.
   * Manager traverses the **File Directory** $\rightarrow$ **I-Map** $\rightarrow$ **Stripe Group Map** to locate the log segment inode.
   * Manager contacts the storage server for the inode, then the storage server for the data blocks.
   * *Optimization*: If the manager recently accessed the inode, it may be cached locally, saving network hops to the storage server.
   > **Hypothetical:** If the Manager Node responsible for a specific file crashes while a client is attempting to read it, the client would use its globally replicated Manager Map to route requests to a new manager (once the system elects one and reconstructs the distributed state), demonstrating the fault tolerance of the decentralized architecture.

### Writing a File
* The client aggregates writes into a log segment in its local memory.
* When flushing to disk, the client determines the appropriate stripe group and stripes the log segment across those storage servers.
* The client then notifies the metadata manager about the flushed log segments to keep the global state consistent.
  > **Conceptual Framework:** Aggregating writes locally before flushing them to the network is a form of write-back caching. It converts many small, inefficient network requests into a single, large, highly efficient block transfer.

## 6. Key Technical Innovations of xFS
xFS serves as a research prototype demonstrating advanced DFS concepts (alongside others like Andrew File System (AFS) and Coda):
1. **Log-Based Striping**: Subsetting storage servers into stripe groups to improve parallelism and fault tolerance.
2. **Cooperative Caching**: Combining distributed client memory with dynamic metadata management for faster file access.
3. **Distributed Log Cleaning**: Offloading garbage collection responsibilities to clients and distributing the workload across stripe groups rather than relying on a centralized manager.

## 7. Conclusion
* Network file systems (like NFS from NetApp) are ubiquitous in computing environments.
* xFS pushes beyond traditional NFS by prioritizing **scalability**—achieved by removing centralization and intelligently utilizing available memory across nodes in a local area network.
* These techniques for identifying and removing bottlenecks are highly reusable concepts for designing other scalable distributed subsystems.

---

