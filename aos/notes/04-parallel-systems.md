# Lesson 4: Parallel Systems 

---

### **Volume I: Foundations of Parallel Machine Models and Memory Semantics**

#### **1. Structural Models of Shared Memory Multiprocessors**
Parallel machines are fundamentally defined by how **CPUs**, **memory**, and **interconnection networks** are organized. There are three primary architectural structures:
*   **Dance Hall Architecture:** This model features CPUs on one side of the interconnection network and memory modules on the opposite side. All memory access must traverse the network.
*   **Symmetric Multiprocessor (SMP):** In this configuration, all CPUs connect to a main memory via a **shared system bus**. It is characterized by symmetric access times, meaning the latency to reach main memory is identical for every processor.
*   **Distributed Shared Memory (DSM):** Also known as **Non-Uniform Memory Access (NUMA)**, this architecture associates a specific portion of physical memory with each CPU node. While every CPU can access the entire global address space through the interconnection network, accessing local memory is significantly faster than accessing remote memory located on other nodes.

#### **2. The Memory Hierarchy and Latency Challenges**
Modern processors utilize a deep **memory hierarchy** to mitigate the massive disparity between CPU cycle times and main memory access speeds, which currently exceeds two orders of magnitude.
*   **Cache Levels:** Typical chips include up to three levels of caches (**L1, L2, L3**). L1 is usually core-specific, while higher levels may be shared among cores or threads. 
*   **Performance Impact:** A failure to find instructions or data in the cache (a **cache miss**) forces the CPU to access main memory, which is considered "bad news" for performance due to the extreme latency.
*   **False Sharing:** This occurs when independent data items touched by different threads on different cores reside on the **same cache block**. Because hardware cache coherence operates on the granularity of a cache block, the system perceives the data as shared, leading to unnecessary cache line migrations and overhead.

#### **3. Memory Consistency Models**
The **memory consistency model** serves as the fundamental contract between the programmer and the hardware regarding the behavior of shared memory reads and writes.
*   **Sequential Consistency:** Proposed by Leslie Lamport, this model requires two properties:
    1.  **Program Order:** The memory accesses from a single processor must be satisfied in the order they were textually generated.
    2.  **Arbitrary Interleaving:** While individual program order is maintained, the overall execution is an interleaving of accesses from all processors in an arbitrary fashion, much like a card shark shuffling two decks into one.
*   **Non-Intuitive Outcomes:** A consistency model is necessary to prevent non-intuitive results, such as a processor seeing a "new" value of one variable while still seeing an "old" value of another, which might happen if messages go out of order in the interconnection network.

#### **4. Hardware Cache Coherence Mechanisms**
When multiple processors maintain private caches of shared memory locations, the system must solve the **cache coherence problem** to ensure all processors eventually see updated values.
*   **Write Invalidate Scheme:** If a processor writes to a memory location, the hardware broadcasts an **invalidation signal** on the bus. Other "snoopy" caches observe this signal and invalidate their local copies, forcing a future read to go to memory to fetch the updated value.
*   **Write Update Scheme:** Instead of invalidating, the writing processor broadcasts the **new value**. All other caches containing that location update their local copies immediately.
*   **Scalability Constraints:** Both schemes incur overhead that grows with the number of processors and the complexity of the interconnection network.

---

### **Volume II: Synchronization Primitives and Atomic Operations**

#### **1. Fundamental Atomic Instructions**
Implementing mutual exclusion requires hardware-level **Read-Modify-Write (RMW)** instructions that execute a group of operations atomically.
*   **Test-and-Set:** Takes a memory location, returns its current value, and sets the location to "1" (locked) in a single atomic step.
*   **Fetch-and-Increment:** Fetches the old value and increments the value in memory by one (or a specified amount) atomically.
*   **Compare-and-Swap (CAS):** Takes three arguments: a memory location (**L**), an expected value (**old**), and a new value (**new**). It checks if L equals "old"; if so, it sets L to "new" and returns true; otherwise, it returns false without modifying memory.
*   **Fetch-and-Store:** Atomically returns the current value of a location while storing a new value into it.
*   **Fetch-and-Phi:** A generic term for instructions that fetch a value, perform an operation (phi), and write it back.

#### **2. Mutual Exclusion: Spinlock Evolution**
**Mutual exclusion locks** protect shared data structures by ensuring only one thread accesses them at a time.
*   **Naive Spin-on-Test-and-Set:** Processors continuously execute a `test-and-set` instruction on a shared variable. This is highly inefficient because `test-and-set` must bypass the cache to access memory, causing massive **network contention** and impeding the processor currently holding the lock from doing useful work.
*   **Spin-on-Read (Caching Spinlock):** To exploit hardware cache coherence, waiters first perform a normal read to check the lock status. They spin locally on the **cached value** without generating bus traffic. When the lock-holder sets the variable to "0," all waiters' caches are invalidated, and they then attempt a `test-and-set` to grab the lock.
*   **Spinlocks with Delay (Procrastination):** To reduce the "thundering herd" effect where all processors rush the bus after a lock release, delays are introduced.
    *   **Static Delay:** Each processor waits for a duration based on its ID.
    *   **Exponential Backoff:** A processor starts with a small delay and doubles it every time it fails to acquire the lock, indicating high contention.

#### **3. Advanced Queueing Locks**
Queueing locks aim to achieve **fairness** and **constant-time signaling** (order of 1) rather than the "noisy" order of $N^2$ transactions seen in simpler spinlocks.
*   **Ticket Lock:** Similar to a deli counter, a requester performs a `fetch-and-increment` to get a **unique ticket number**. They then spin while waiting for the `now-serving` variable to match their ticket. While fair, it remains "noisy" because the release of the lock invalidates the `now-serving` variable in all waiters' caches.
*   **Anderson’s Array-Based Queueing Lock:**
    *   **Structure:** Every lock has a **circular flags array** of size $N$ (number of processors) and a `queuelast` variable.
    *   **Acquisition:** A requester uses `fetch-and-increment` on `queuelast` to get a unique slot in the array. They spin on their specific array element until its state changes from **must-wait (MW)** to **has-lock (HL)**.
    *   **Release:** The lock-holder marks their current slot as MW and sets the *next* slot in the circular queue to HL, signaling exactly one successor.
    *   **Downside:** Space complexity is $O(N)$ per lock, which is wasteful if contention is low but must be sized for the worst case.
*   **MCS (Mellor-Crummey and Scott) Link-Based Lock:**
    *   **Structure:** Uses a **linked list** of queue nodes. Each requester provides their own `qnode` containing a `got-it` flag and a `next` pointer.
    *   **Acquisition:** The requester uses `fetch-and-store` to atomically become the new "last" pointer and retrieve their predecessor's coordinates. They then set their predecessor's `next` pointer to point to themselves and spin on their own local `got-it` flag.
    *   **Release:** The holder checks if their `next` pointer is null. If it isn't, they simply set their successor's `got-it` flag to true.
    *   **Complexity:** Space complexity is $O(L)$, where $L$ is the number of active requesters, making it more memory-efficient than Anderson's lock. It handles the "corner case" (no immediate successor) using a `compare-and-swap` on the lock's tail pointer.

---

### **Volume III: Barrier Synchronization**

#### **1. Semantic Definition**
A **barrier** is a synchronization point where a set of threads must wait until **everyone** has arrived before any can proceed to the next phase of computation. This is common in scientific applications that execute in distinct phases.

#### **2. Centralized (Counting) Barriers**
*   **Mechanism:** A shared counter is initialized to $N$. Arriving threads atomically decrement the counter and spin until it reaching zero.
*   **The "Race" Problem:** If threads are released and immediately reach the *next* barrier before the last thread has reset the counter to $N$, they might "fall through" incorrectly.
*   **Sense Reversal:** To fix the race and reduce spin loops, a **sense variable** is used. Threads spin on a local sense flag that must match a global sense. The last thread to arrive resets the counter and **flips the global sense**, releasing all waiters in one action.

#### **3. Tree Barriers**
To avoid the network contention of a single shared variable (hot spot), the barrier is organized hierarchically.
*   **Arrival Phase:** Threads are divided into groups of size $K$. Arriving threads decrement a counter at their leaf node; the last in each group moves up to the next level of the tree to decrement the parent's counter.
*   **Wake-up Phase:** Once the root's counter reaches zero, the "champion" processor triggers a wake-up signal that propagates back down the tree, flipping the `locksense` flags of the waiting nodes.
*   **MCS Tree Barrier:** Improves on the vanilla tree by ensuring **statically determined spin locations**. The arrival tree is **4-ary** (based on theoretical performance results), and the wake-up tree is **binary**. Each processor spins on a unique memory location assigned by construction, minimizing network traffic.

#### **4. Tournament and Dissemination Barriers**
*   **Tournament Barrier:** Organized as a competition where winners advance through $\lceil \log_2 N \rceil$ rounds. It uses **match fixing** (predetermined winners) so that losers spin on **statically assigned** locations. It does not require atomic instructions (only reads/writes) and works on clusters without shared memory.
*   **Dissemination Barrier:** Uses **information diffusion**. In each round $k$, processor $i$ sends a message to processor $(i + 2^k) \pmod N$. After $\lceil \log_2 N \rceil$ rounds, every processor has "heard" from every other processor. It is highly effective for machines where $N$ is not a power of two and can exploit parallel paths in an interconnection network.

---

### **Volume IV: Scheduling in Parallel Systems**

#### **1. The Fundamental Mantra: Cache Locality**
The primary objective of a parallel scheduler is to keep the **caches warm**. Because the disparity between CPU cycle time and main memory access is over two orders of magnitude (100:1 ratio), any cache miss is "bad news" for performance. Consequently, the scheduler must prioritize **cache affinity**—the likelihood that a thread's working set remains in the memory hierarchy of a specific processor.

#### **2. Hardware Multithreading and Core Architecture**
Modern multicore processors employ **hardware multithreading** to hide long-latency operations, such as memory fetches.
*   **Mechanism:** A single core (e.g., C1) may support multiple hardware threads (e.g., four). If a running thread experiences a cache miss, the hardware automatically switches to another hardware thread on the same core without operating system intervention.
*   **Hierarchy:** Typically, an **L1 cache** is core-specific and shared among its hardware threads, while the **Last Level Cache (LLC)**—often L2 or L3—is shared across all cores on the chip. 
*   **The Critical Boundary:** Missing the LLC is catastrophic, as it requires going off-chip to main memory.

#### **3. Cache-Aware and Cache-Affinity Scheduling**
Scheduling in parallel systems is an **NP-complete problem**, necessitating the use of heuristics.
*   **Cache-Aware Scheduling:** This policy categorizes threads into two groups based on profiling:
    *   **Cache-Frugal Threads:** Require small portions of the cache to remain "happy" (maintain a working set).
    *   **Cache-Hungry Threads:** Require significant cache space.
    *   **Optimization Goal:** The scheduler picks a combination of threads such that their cumulative cache requirement is less than the total capacity of the LLC.
*   **Cache-Affinity Scheduling:** Focuses on rescheduling a thread (T1) on the same processor (P1) where it last ran to exploit its existing working set in the cache. 
    *   **Risk of Cache Pollution:** If intervening threads (T2, T3) run on P1 while T1 is descheduled, they may "pollute" the cache by replacing T1's data.

#### **4. Taxonomy of Scheduling Policies**
1.  **First-Come, First-Served (FCFS):** Prioritizes **fairness** over affinity, picking the thread that has been runnable the longest.
2.  **Fixed Processor:** A thread is assigned to one processor for its entire lifetime to maximize affinity, often at the cost of load balancing.
3.  **Last Processor:** The processor attempts to pick a thread that most recently ran on it, assuming some affinity remains.
4.  **Minimum Intervening (MI):** For every thread, the system maintains an **affinity index**—the number of intervening threads that have run on a processor since the subject thread last ran there. The scheduler selects the processor where this index is minimized.
5.  **Minimum Intervening Plus Queueing (MI+Q):** A more sophisticated heuristic that considers both the affinity index ($I$) and the current size of the processor's ready queue ($Q$). It targets the processor where the sum $(I + Q)$ is minimal, accounting for the pollution that will occur while the thread waits in the queue.

#### **5. Implementation and Heuristics**
*   **Queue Organization:** Systems may use a **global queue** (high contention, better load balancing) or **local queues** per processor (low contention, utilizes affinity).
*   **Work Stealing:** If a processor (P2) runs out of work, it may "steal" threads from a peer’s local queue to maintain throughput.
*   **Priority and Aging:** A thread's priority is determined by its base priority, its affinity, and its **age**. To prevent starvation, the OS provides a "senior citizen discount" by boosting the priority of threads that have been in the system for a long time.
*   **Procrastination:** A processor may choose to execute an **idle loop** rather than pick a non-affine thread, hoping a thread with a warm cache becomes runnable shortly.

---

### **Volume V: Inter-Process Communication (IPC) and RPC Optimization**

#### **1. The High Cost of Traditional RPC**
Traditional Remote Procedure Calls (RPC) between different protection domains on the same machine incur massive overhead compared to simple local procedure calls.
*   **The Four-Copy Problem (Single Direction):**
    1.  **User-Level (Client):** Client stub serializes arguments from the stack into an RPC packet (the "herding cats" phase).
    2.  **Kernel-Level (Inbound):** Kernel copies the RPC packet from client address space to a kernel buffer.
    3.  **Kernel-Level (Outbound):** Kernel copies the buffer from the kernel to the server's address space.
    4.  **User-Level (Server):** Server stub de-serializes the packet and copies arguments onto the server's stack.
*   **Total Cost:** This results in **four copies each way** (eight total for a call/return), two traps (call and return), and two context switches.

#### **2. Making RPC "Cheap": The Binding Process**
To optimize IPC, the system separates the one-time **binding** cost from the recurring **call** cost.
*   **Mechanism:** A server exports an interface (e.g., `foo`) to a **name server** (like "Yellow Pages"). 
*   **First Call:** The kernel mediates the initial call, validating that the client is authorized. 
*   **Outcome:** The kernel creates a **Binding Object (BO)**—a capability given to the client—and a **Procedure Descriptor** containing the entry point address and argument requirements.

#### **3. Optimized Execution: The A-Stack and E-Stack**
By establishing shared memory during binding, the kernel is removed from the data-copying loop.
*   **Argument Stack (A-Stack):** A shared memory region mapped into both the client and server address spaces for passing parameters and results. This reduces the data transfer to only **two copies** (marshaling to A-stack and unmarshaling to the execution stack).
*   **Execution Stack (E-Stack):** A dedicated stack provided by the kernel for the server to use during procedure execution.
*   **Thread Borrowing:** Instead of a full context switch, the kernel "doctors" the client thread, changing its program counter (PC) and address space descriptor so it executes the server procedure directly.

#### **4. RPC on Shared Memory Multiprocessors (SMP)**
Parallel hardware allows for further optimization of the "implicit" costs of IPC, such as **loss of locality**.
*   **Server Preloading:** The kernel can pin a server domain to a specific CPU (e.g., CPU 2) and keep it resident. 
*   **Locality Mitigation:** By directing client calls to these preloaded servers, the system ensures the server's working set remains in that CPU's caches ("warm caches"), significantly reducing the time required for the server to execute the procedure.

---
### **Volume VI: Advanced Barrier Architectures: The MCS Tree Model**

#### **1. Structural Differentiations in the MCS Barrier**
The **MCS tree barrier** is a modified tree synchronization mechanism that utilizes distinct structures for the arrival and wakeup phases to optimize the critical path of execution. 
*   **Arrival Tree (4-ary):** The arrival phase is organized as a **4-ary tree**. This specific "ariness" (degree of four) is selected based on theoretical performance results indicating it provides the optimal balance for arrival signaling.
*   **Wakeup Tree (Binary):** The wakeup phase is organized as a **binary tree**. This structure is chosen because it provides the **shortest critical path** from the root to the last awakened child.

#### **2. Data Structures and Arrival Signaling**
Every parent node in the arrival tree manages two primary data structures to track synchronization:
*   **HaveChild Vector:** A boolean vector indicating which of the four potential child positions are occupied by actual processes. For example, in an 8-node system, process P0 has four children, while P1 may only have three, leaving the fourth position marked false.
*   **Child Not Ready (CN) Vector:** This structure provides a **unique, statically determined spot** for every child to signal its arrival to the parent.
*   **Optimization via Packing:** In cache-coherent multiprocessors, these unique signaling spots can be **packed into a single processor word**. This allows the parent to spin on a **single memory location** to monitor all children simultaneously, as the hardware cache coherence mechanism will alert the parent whenever any child modifies the shared word.

#### **3. The Arrival and Wakeup Workflow**
*   **The Arrival Phase:** When a process reaches the barrier, it accesses a specific, statically assigned spot in its parent's CN vector and sets it to "1". Once a parent (such as P1) sees all its children have arrived, it moves up the tree to signal its own arrival in the root's CN vector.
*   **The Wakeup Phase:** Once the root (P0) determines through the arrival tree that all processes are present, it begins the wakeup propagation.
*   **Direct Signaling:** The parent uses a **ChildPointer** data structure to reach into a child's memory space and signal it to wake up.
*   **Static Spin Locations:** To minimize network contention, every process spins on a **statically determined location** assigned by construction. When a parent signals a child, it modifies only that specific location, ensuring no other processors are affected by the transaction.

---

### **Volume VII: The Tornado Operating System and Clustered Objects**

#### **1. The Clustered Object Paradigm**
Tornado replaces traditional centralized kernel data structures with **clustered objects** to ensure scalability. 
*   **Unified Reference/Multiple Representations:** From the perspective of the system, a clustered object has a **single object reference** that is identical across all nodes. However, "under the covers," the object may have **multiple representations or replicas** distributed across the machine.
*   **Incremental Optimization:** The system allows for **dynamic adaptation** of object representations based on usage patterns. An object might begin as a single representation and be replicated across more nodes as contention increases.

#### **2. Replication and Consistency**
*   **Degree of Clustering:** The service designer determines the level of replication—whether an object is a **singleton** (shared by all), **one per core**, **one per CPU**, or **one per group of processors**.
*   **Software-Managed Consistency:** Unlike standard memory, which relies on hardware cache coherence, clustered object replicas are kept consistent via **software-mediated protected procedure calls**. This avoids the indiscriminate overhead of hardware coherence transactions on physical memory that may be located across different nodes.
*   **Reduced Locking:** Replication allows independent access to local replicas, which significantly **reduces the need for locking shared data structures**.

#### **3. Object Resolution and Miss Handling**
Tornado uses a multi-level lookup system to resolve object references on each CPU:
1.  **Translation Table:** Maps a global object reference to a local representation in memory.
2.  **Miss Handling Table:** If a reference is missing from the translation table, the system consults this partitioned data structure to find a **local miss handler**.
3.  **Global Miss Handler:** If a local handler does not exist, the CPU consults a **replicated global miss handler**. This handler knows the partitioning of the entire miss handling table and directs the request to the node that can provide the necessary replica.

---

### **Volume VIII: Scalable Memory Management and Virtual Memory**

#### **1. Objectization of the VM Manager**
To eliminate the serial bottlenecks of a centralized **Page Control Block (PCB)** or global page table, Tornado "detonates" these structures into a collection of objects:
*   **Process Object:** Replicated one per CPU; it handles process-wide information like TLB management and is mostly read-only.
*   **Region Object:** Represents a specific portion of the address space. These are **partially replicated** (e.g., one per group of processors) based on which threads access those specific memory regions.
*   **File Cache Manager (FCM):** Manages the backing store for a region; these are often **partitioned** so that different FCMs manage different parts of the file system.
*   **DRAM Object:** Manages physical memory frames; there is typically one DRAM object per **Distributed Shared Memory (DSM)** node to keep allocations local.
*   **Cached Object Representation (COR):** A singleton or shared object responsible for managing the actual physical I/O between the disk and DRAM.

#### **2. Non-Hierarchical Locking and Existence Guarantees**
Traditional **hierarchical locking** (locking the process, then the region, then the frame) kills concurrency because it forces serialization at the top-level process object. 
*   **Reference Counting:** Tornado replaces hierarchical locks with **reference counts** associated with each object.
*   **Existence Guarantee:** When a thread services a page fault, it increments the reference count of the process object rather than locking it. This provides an **existence guarantee**, ensuring the object cannot be deleted or migrated while in use, while still allowing other threads to simultaneously access the same object for different regions.
*   **Encapsulation:** Locking is strictly confined within individual objects or replicas, limiting the scope of contention.

#### **3. Scalable Dynamic Allocation**
In NUMA systems, centralized heap management is a major bottleneck. Tornado scales **dynamic memory allocation** by breaking the process heap into portions associated with the physical memory of specific nodes. Requests from threads are satisfied from the **local physical memory** nearest to the node where the thread is executing, which also helps avoid **false sharing** across nodes.

---

### **Volume IX: Virtualization in Parallel Systems: Cellular Disco**

#### **1. Functional Objectives**
The **Cellular Disco** project explores using virtualization to manage the complexity of parallel hardware. The goal is to avoid the "pain point" of re-implementing operating systems and device drivers for every new parallel architecture.

#### **2. The Virtualization Layer**
*   **Thin VMM:** Cellular Disco acts as a thin Virtual Machine Monitor (VMM) sitting between the **guest operating system** and the physical hardware (e.g., the SGI Origin 2000).
*   **Resource Management:** It manages physical CPUs, memory, and I/O devices, presenting a virtualized hardware interface to the guest OS.

#### **3. I/O Management via Trap-and-Emulate**
Cellular Disco utilizes a specialized **trap-and-emulate** mechanism for I/O:
1.  **Request Redirection:** When a guest OS makes an I/O request, it traps into the VMM.
2.  **Identity Faking:** Cellular Disco rewrites the request so it appears to originate from the VMM itself rather than the guest.
3.  **Interrupt Handling:** When the I/O completes, the hardware interrupt is intercepted by the VMM. The VMM then fakes a normal interrupt back to the guest OS to signal completion.
*   **Efficiency:** By using these construction techniques, the system can leverage existing third-party device drivers while keeping virtualization overhead **within 10%** for many applications.

---
### **Volume X: Deep Architecture of the MCS Tree Barrier**

#### **1. Asymmetric Tree Structures**
The MCS tree barrier utilizes a dual-tree approach, separating the arrival and wakeup phases into different topological configurations based on theoretical performance results.
*   **Arrival Phase (4-ary Tree):** The arrival tree is organized as a **4-ary tree**. This structure is chosen because theoretical analysis indicates that a degree of four provides the optimal performance for arrival signaling.
*   **Wakeup Phase (Binary Tree):** The wakeup phase is organized as a **binary tree**. This configuration is selected because it yields the **shortest critical path** from the root to the last awakened child process.

#### **2. Arrival Tree Data Structures**
Every node in the MCS arrival tree is associated with two primary data structures used by parents to track their children:
*   **HaveChild Vector:** A boolean vector (statically assigned by construction) that indicates which of the four potential child slots are occupied by actual processes. For instance, in an 8-node system ($N=8$), process P0 has four children (P1-P4), while P1 has only three (P5-P7), meaning P1's fourth slot is marked false.
*   **Child Not Ready (CN) Vector:** A vector where each child has a **unique, statically determined spot** to signal its arrival to the parent.

#### **3. Signaling and Cache Optimization**
*   **Arrival Signaling:** When a process arrives at the barrier, it "reaches" into its parent's CN vector and sets its specific assigned spot to "1". Once all spots in the parent's CN vector are set (matching the `HaveChild` vector), the parent moves up the tree to signal its own parent.
*   **Cache Coherence Packing:** In cache-coherent multiprocessors, all child signaling spots (the CN vector) can be **packed into a single processor word**. This allows the parent to spin on a **single memory location**. The hardware cache coherence mechanism ensures the parent is alerted every time a child modifies this shared word, eliminating the need to poll individual locations.

#### **4. Wakeup Phase Mechanics**
*   **ChildPointer Data Structure:** The wakeup tree uses a `ChildPointer` structure, allowing parents to "reach down" and signal specific children that it is time to wake up.
*   **Point-to-Point Signaling:** To minimize network contention, every process spins on a **statically determined location** assigned by design. When a parent signals a child, it modifies only that specific location, ensuring other processes are not disturbed.

---

### **Volume XI: Detailed Mechanics of Array-Based Queueing Locks (Anderson's Lock)**

#### **1. Structure and Initialization**
Anderson's lock uses a static data structure to simulate a queue.
*   **Flags Array:** A circular array of size $N$ (where $N$ is the number of processors). It is initialized with the first slot set to **Has-Lock (HL)** and all subsequent slots set to **Must-Wait (MW)**.
*   **QueueLast Variable:** A shared variable initialized to zero, used to track the next available slot for a requester.

#### **2. Acquisition Workflow**
1.  **Ticket Retrieval:** A process requests the lock by performing an atomic **fetch-and-increment** on the `queuelast` variable. This returns a unique index (their "ticket") and advances `queuelast` for the next requester.
2.  **Local Spinning:** The process uses the index to identify its unique spot in the `flags` array and spins locally on that location until its value changes from MW to HL.
3.  **Sequencing:** Because `fetch-and-increment` is atomic, all requesters are strictly sequenced, ensuring **fairness** (First-In, First-Out).

#### **3. Release Workflow**
1.  **Slot Reset:** The current lock-holder sets their own slot back to **MW** so that future requesters (after the queue wraps around) will know they must wait.
2.  **Successor Signaling:** The holder then sets the *next* slot in the circular array (`(current + 1) mod N`) to **HL**.
3.  **Constant Time:** This mechanism ensures that exactly one waiter is signaled, making the release **non-noisy** and $O(1)$.

#### **4. Trade-offs**
*   **Virtues:** It provides fairness, limits contention by using distinct spin variables, and requires only one atomic operation per critical section.
*   **Downside:** The **space complexity** is $O(N)$ for every lock in the program. This is wasteful because the array must be sized for the worst-case contention (all $N$ processors) even if only a few processes ever compete for that specific lock.

---

### **Volume XII: Comparative Analysis of Atomic Synchronization**

#### **1. Selection Heuristics by Architecture**
The choice of synchronization primitive depends heavily on available hardware instructions and the level of contention.
*   **High Contention/Fancy Hardware:** If the architecture supports "fancy" instructions like `fetch-and-increment`, `fetch-and-store`, or `compare-and-swap`, the **Anderson's array-based lock** or **MCS link-based lock** are the best performers.
*   **Low Contention/Simple Hardware:** If the architecture only supports `test-and-set`, a spinlock with **exponential backoff** is often the most efficient.

#### **2. Atomic Operation Complexity**
*   **Spinlocks:** The number of atomic operations (Read-Modify-Write) required per critical section depends on the level of contention.
*   **Queueing Locks (Anderson/MCS):** These require exactly **one atomic operation** per critical section regardless of contention. Note: MCS may require a second atomic operation (Compare-and-Swap) during the "corner case" of unlocking when there is no immediate successor.

---

### **Volume XIII: Advanced Memory Management in Tornado OS**

#### **1. Scalable Page Fault Service Workflow**
Tornado's objectized structure allows page fault handling to scale with the number of processors. The workflow follows a strict object-to-object path:
1.  **Process Object:** Receives the fault; identifies which **Region Object** corresponds to the missing Virtual Page Number (VPN).
2.  **Region Object:** Points to the appropriate **File Cache Manager (FCM)**.
3.  **FCM:** Identifies the backing file and offset for the missing page and requests a physical frame from the **DRAM Object**.
4.  **Cached Object Representation (COR):** Receives the frame coordinates and performs the actual I/O to pull data from disk into DRAM.
5.  **Completion:** The FCM signals the Region that the fault is serviced; the Region updates the **TLB** via the Process Object, and execution resumes.

#### **2. Existence Guarantees vs. Hierarchical Locks**
To prevent serial bottlenecks at the Process Object level, Tornado uses **reference counting** instead of hierarchical locking.
*   **The Bottleneck:** Locking the Process Object to service a page fault would block all other threads on that processor, even if they were faulting in entirely different memory regions.
*   **The Solution:** A thread increments the **reference count** of an object (e.g., the Process Object) to ensure it is not migrated or deleted while in use.
*   **Integrity:** This provides an **existence guarantee**. If a facility (like process migration) needs to move the object, it must wait until the reference count reaches zero.

#### **3. Common Case Optimization**
A core principle of Tornado is to optimize the **common case** (page fault handling) while allowing infrequent operations (region creation/destruction) to take longer.
*   **Scaling:** Page fault handling scales linearly as it uses local replicas.
*   **Infrequent Overhead:** Destroying a region takes more time because the system must find and eliminate all distributed replicas of that region.

---

### **Volume XIV: Virtualization for Parallel Scalability (Cellular Disco)**

#### **1. I/O Virtualization via Identity Faking**
Cellular Disco uses a sophisticated "trap-and-emulate" strategy to handle I/O without modifying host drivers.
*   **The Forward Path:** When a guest OS issues an I/O request, the VMM intercepts the trap, rewrites the request as if it originated from the VMM itself, and passes it to the host OS (IRIX).
*   **The Return Path:** Because the VMM "faked" the identity of the requester, the hardware completion interrupt is delivered to the VMM.
*   **Emulated Interrupt:** The VMM performs necessary bookkeeping and then fakes a normal interrupt back to the guest OS, completing the cycle.

#### **2. Performance and Feasibility**
By construction, Cellular Disco proves that a virtual machine monitor can manage multiprocessor resources as efficiently as a native OS, with overhead remaining **within 10%** for many applications.

---
### **Volume XV: Advanced Barrier Synchronization Topologies**

#### **1. The Tournament Barrier: A Hierarchical Match-Fixed Model**
The tournament barrier organizes $N$ participating processors into a structured competition consisting of $\lceil \log_2 N \rceil$ rounds.
*   **Static "Match Fixing" and Reliability:** To optimize synchronization, the matches in each round are "rigged" or predetermined by the system. For example, in an 8-node system, P0 is predetermined as the winner over P1 in the first round.
*   **Signaling Mechanics:** The predetermined "winner" of a match spins on a **statically determined memory location** until the "loser" arrives and signals their presence. This static assignment is particularly advantageous for **Non-Cache Coherent (NCC) NUMA** machines because the spin location can be placed in memory local to the winner, reducing network traversal.
*   **Arrival Phase Progression:** Winners move up the tree to the next round, competing until a single **tournament champion** (e.g., P0) is declared at the root.
*   **Wake-up Phase (Handshaking):** Once the champion knows everyone has arrived, they propagate a wake-up signal back down the tree. The winner of each round "walks over" to the loser—metaphorically shaking hands—to signal that the match and the barrier are complete.
*   **Cluster Compatibility:** Because the tournament barrier can be modeled entirely as message-passing between two distinct players in every match, it is highly effective for **computation clusters** that lack physical shared memory.

#### **2. The Dissemination Barrier: Information Diffusion**
The dissemination barrier operates through a "well-orchestrated gossip protocol" rather than a strict hierarchy.
*   **Algorithmic Formula:** In each round $k$ (starting from 0), every processor $Pi$ sends a signal to a peer determined by the formula: $Pi \text{ sends to } (Pi + 2^k) \pmod N$.
*   **Round Completion:** A processor considers a round complete when it has both sent its message to its ordained peer and received a message from its own ordained sender. 
*   **Generalization for Arbitrary $N$:** Unlike many tree-based algorithms, $N$ does not need to be a power of two. Through information diffusion, every processor learns that everyone else has arrived after $\lceil \log_2 N \rceil$ rounds.
*   **Complexity Trade-offs:** Because every processor sends exactly one message per round, the **communication complexity** is $O(N \log N)$. This is higher than the $O(\log N)$ complexity of the tournament barrier, but it exploits **parallel communication paths** in the interconnection network more effectively.
*   **Implementation in Shared Memory:** In shared-memory systems, these "messages" are implemented as signals to **statically determined spin locations**.

---

### **Volume XVI: Inter-Process Communication (IPC) and LRPC Mechanics**

#### **1. The Binding Process (Control Path)**
To eliminate the high cost of traditional RPC, the system performs a one-time **binding** to set up a high-performance communication channel.
*   **Interface Export:** A server exports an entry point procedure (e.g., `foo`) to a **name server** (similar to "Yellow Pages").
*   **The First Call (Mediation):** When a client first calls `s.foo`, the kernel intercepts the trap and performs an **up-call** to the server to validate the client's identity.
*   **Capability Exchange:** Upon validation, the kernel provides the client with a **Binding Object (BO)**—a capability for future authenticated calls—and creates a **Procedure Descriptor** in the kernel to store entry point addresses and stack requirements.

#### **2. Execution Optimizations (Data Path)**
Actual calls utilize shared memory to bypass the kernel’s copying overhead.
*   **The A-Stack (Argument Stack):** During binding, the kernel allocates a shared memory region (A-Stack) and maps it into the address spaces of both the client and server. Arguments are passed **by value** because pointers to other memory regions would be invalid in the peer's address space.
*   **Thread Borrowing:** The client thread is "doctored" by the kernel. Instead of a full context switch, the kernel changes the thread's program counter (PC) to the server's entry point and modifies its address space descriptor.
*   **The E-Stack (Execution Stack):** The server uses a dedicated execution stack (E-Stack) provided by the kernel for its local procedure calls during execution.
*   **Data Transfer Efficiency:** The process requires only two copies per call: **marshaling** from the client stack to the A-Stack and **unmarshaling** from the A-Stack to the E-Stack.

---

### **Volume XVII: Clustered Object Architecture in the Tornado OS**

#### **1. Clustered Object Logic and Replication**
Tornado provides the **illusion of a single object reference** while maintaining multiple physical representations under the covers.
*   **Implementation Choice:** The service designer determines the **degree of clustering** (e.g., one replica per core, per CPU, or per group of processors) based on expected usage patterns.
*   **Incremental Optimization:** Objects can start with a single representation and be replicated dynamically if the system detects high contention.

#### **2. The Resolution Workflow (Miss Handling)**
When a process presents an object reference, the system resolves it using local data structures.
*   **Translation Table:** A local table on each CPU that maps the common object reference to a specific memory representation (replica).
*   **Miss Handling Table:** If the reference is not in the translation table, the system checks this **partitioned** data structure to find a handler.
*   **Global Miss Handler:** If the handler is not found locally, the CPU consults a **replicated global miss handler**. This handler knows the partitioning of the entire miss handling table across the machine and fetches the required replica to populate the local translation table.

#### **3. Software-Managed Consistency**
Tornado avoids the "indiscriminate" overhead of hardware cache coherence.
*   **Protected Procedure Calls:** Replicas are kept consistent through software-mediated calls rather than physical memory updates.
*   **Encapsulation:** Locking is strictly confined within an object or a specific replica, promoting concurrency across different processors.

---

### **Volume XVIII: Scheduling Metrics and System Performance**

#### **1. Figures of Merit**
Schedulers are evaluated against three primary metrics:
*   **Throughput (System-Centric):** The number of threads completed per unit of time.
*   **Response Time (User-Centric):** The duration from a thread's start to its completion.
*   **Variance of Response Time:** The consistency of execution speed; high variance indicates that identical programs take widely different times based on current system load.

#### **2. Scheduling Priorities and starvation**
A thread's final priority in the ready queue is typically a composite of three factors:
*   **Base Priority:** Statically assigned when the thread is created.
*   **Affinity Component:** The degree to which the thread's cache is "warm" on a specific processor.
*   **Age ("Senior Citizen Discount"):** To prevent starvation, threads that have been runnable for a long time receive a priority boost to ensure they eventually reach the head of the queue.

#### **3. Scalability Constraints and Procrastination**
*   **Overhead vs. Parallelism:** Actual delivered performance is the difference between the "pro" of parallelism and the "con" of increased system overhead (e.g., cache coherence traffic).
*   **The "Procrastination" Win:** In high-contention scenarios, a scheduler may choose to execute an **idle loop** rather than pick a non-affine thread. This "procrastination" can improve performance by waiting for an affine thread to become runnable, preserving the processor's warm cache.

---
### **Volume XIX: Structural Mechanics of Array-Based Queueing Locks (Anderson’s Lock)**

#### **1. Data Structures and Initialization**
Anderson’s lock is designed to eliminate the "thundering herd" effect of traditional spinlocks by sequencing requesters into a circular queue.
*   **Flags Array:** Every lock $L$ is associated with an array of flags of size $N$, where $N$ is the number of processors in the Symmetric Multiprocessor (SMP). Each element in the array can be in one of two states: **Has-Lock (HL)** or **Must-Wait (MW)**.
*   **Queue-Last Variable:** A shared variable, `queuelast`, is initialized to zero and used to track the next available slot in the array.
*   **Initialization State:** To enable the queue, the first spot in the array is initialized to HL, while all other spots are set to MW. Slots are not statically associated with specific processors; they are assigned as requests arrive.

#### **2. Acquisition and Release Protocols**
*   **Lock Acquisition:** When a processor requests a lock, it performs an atomic **fetch-and-increment** on the `queuelast` variable. This operation returns a unique index (the requester's "ticket") and advances the pointer for future requesters. The processor then spins locally on its assigned spot in the flags array, waiting for the state to change from MW to HL.
*   **Lock Release (Unlocking):** Upon exiting the critical section, the current lock-holder performs two actions:
    1.  **Resetting the Current Slot:** It sets its own array position back to **MW** to ensure that future requesters (after the circular queue wraps around) will correctly wait.
    2.  **Signaling the Successor:** It sets the next spot in the circular queue (`(current + 1) mod N`) to **HL**. This precisely signals the next waiting processor, allowing it to enter the critical section.

#### **3. Architectural Virtues and Constraints**
*   **Fairness and Scalability:** The use of atomic sequencing ensures **First-In, First-Out (FIFO) fairness**. Furthermore, the release process is **non-noisy** because it signals exactly one successor rather than invalidating all waiters' caches.
*   **Constant Atomic Overhead:** Regardless of the number of processors contending for the lock, only **one atomic operation** (`fetch-and-increment`) is required per critical section.
*   **Network Efficiency:** Each processor spins on a **distinct, private spin variable** in the array, remaining impervious to signals intended for other processors.
*   **Space Complexity Bottleneck:** The primary disadvantage is that the data structure size is $O(N)$ for every lock in the system. Even if contention is low, the system must allocate space for the **worst-case scenario** (all $N$ processors requesting the lock simultaneously).

---

### **Volume XX: The MCS Tree Barrier: Advanced Structural Synthesis**

#### **1. Asymmetric 4-ary Arrival and Binary Wakeup**
The MCS tree barrier utilizes two distinct tree structures to optimize performance based on theoretical results.
*   **Arrival Phase (4-ary):** The arrival tree is organized as a **4-ary structure**, which analysis indicates provides the best performance for signaling arrivals.
*   **Wakeup Phase (Binary):** The wakeup tree is a **binary structure**, chosen because it offers the shortest critical path from the root to the last awakened child.

#### **2. Arrival Tree Data Management**
Every parent node in the arrival tree maintains two critical data structures:
*   **HaveChild Vector:** A boolean vector that indicates which of the four potential child slots are occupied. For $N=8$, $P0$ has four children ($P1$-$P4$), while $P1$ has three ($P5$-$P7$), leaving its fourth `HaveChild` bit false.
*   **Child Not Ready (CN) Vector:** This provides a **unique, statically determined spot** for each child to signal its arrival to the parent.
*   **Cache Packing Optimization:** In cache-coherent systems, the CN vector spots can be **packed into a single processor word**. This allows the parent to spin on one memory location; the hardware cache-coherence mechanism alerts the parent whenever any child modifies the word.

#### **3. Wakeup Tree Signaling Mechanics**
*   **ChildPointer Structure:** Parents use a `ChildPointer` to reach down and signal specific children that the barrier is complete.
*   **Point-to-Point Wakeup:** Each process spins on a **statically determined location** assigned by the construction of the binary tree. When a parent signals a child, it modifies only that specific location, minimizing network contention.

---

### **Volume XXI: Memory Management and Clustered Objects (Tornado OS)**

#### **1. The Principle of Clustered Objects**
Tornado avoids centralized bottlenecks by utilizing **clustered objects**, which present a single, common object reference across all nodes but may have multiple physical representations (replicas) "under the covers".
*   **Incremental Optimization:** Objects can be dynamically adapted based on usage patterns, moving from a singleton representation to multiple replicas.
*   **Scalability via Replication:** Independent access to replicas reduces the need for global locking.

#### **2. Scalable Page Fault Service**
The objectized structure of the Virtual Memory (VM) manager ensures that the common-case operation—page fault handling—scales with the number of processors.
*   **Object Workflow:** A faulting thread passes through a **Process Object** (replicated per CPU), to a **Region Object** (partially replicated), to a **File Cache Manager (FCM)** (partitioned), and finally to a **Cached Object Representation (COR)** (singleton) to perform I/O.
*   **Reference Counting vs. Hierarchical Locks:** Tornado replaces hierarchical locking (which kills concurrency) with **existence guarantees** provided by reference counts. Incrementing a reference count ensures an object isn't migrated or destroyed while in use without blocking other threads from accessing the same object path.

#### **3. Dynamic Resolution: Translation and Miss Handling**
The system resolves object references locally whenever possible:
1.  **Translation Table:** A local CPU table mapping object references to specific memory representations.
2.  **Miss Handling Table:** A **partitioned** structure that maps references to object miss handlers.
3.  **Global Miss Handler:** A **replicated** object on every node that knows the partitioning of the miss handling table. If a handler is not local, the global handler locates it on another node, retrieves a replica, and populates the local translation table.

---

### **Volume XXII: Inter-Process Communication (IPC) and RPC Optimization**

#### **1. Traditional RPC Latency (The Eight-Copy Problem)**
Traditional RPC involves the kernel as a mediator for every transaction, leading to significant overhead.
*   **Client-to-Server:** Four copies (Client stack $\rightarrow$ RPC packet $\rightarrow$ Kernel buffer $\rightarrow$ Server address space $\rightarrow$ Server stack).
*   **Server-to-Client:** Another four copies to return results, totaling **eight copies** for a complete call.
*   **Context Switching:** Each call requires two traps and two full context switches.

#### **2. Lightweight RPC (LRPC) Optimizations**
LRPC reduces overhead by separating binding from calling and using shared memory.
*   **A-Stack (Argument Stack):** A shared memory region established during binding where arguments are passed **by value**. This reduces the data path to only **two copies** (marshaling to A-stack and unmarshaling to the execution stack).
*   **Thread Borrowing (Doctoring):** Instead of a full context switch, the kernel "doctors" the client thread by modifying its PC, address space descriptor, and stack to run directly in the server's domain.
*   **Implicit Costs:** While LRPC eliminates explicit copying, it still faces **implicit costs** like the loss of cache locality due to switching protection domains.

---

### **Volume XXIII: Theoretical Foundations of Memory Consistency**

#### **1. Sequential Consistency (SC)**
Defined by Leslie Lamport, SC is the fundamental model of programmer expectations.
*   **Program Order:** Memory accesses from a single processor must be satisfied in their textual order.
*   **Arbitrary Interleaving:** Accesses from multiple processors are interleaved in an arbitrary fashion, similar to a casino card shark shuffling two decks.

#### **2. Consistency vs. Coherence**
*   **Memory Consistency Model:** The contract between the programmer and the system regarding the intuitive behavior of shared memory.
*   **Cache Coherence:** The hardware/software mechanism (Write Invalidate or Write Update) used to implement the consistency model in the presence of private caches.
*   **Non-Cache Coherent (NCC) NUMA:** Systems that provide a shared address space but leave the responsibility of maintaining coherence to the software/operating system.

---
### **Volume XXIV: Hardware Model and Memory Hierarchy Challenges**

#### **1. Structural Taxonomy of Shared Memory Machines**
The implementation of parallel operating systems depends on the underlying physical arrangement of CPUs and memory modules. Three primary structures define this relationship:
*   **Dance Hall Architecture:** Characterized by a strict separation where all CPUs are positioned on one side of an interconnection network and all memory modules on the opposite side.
*   **Symmetric Multiprocessor (SMP):** A design where all CPUs connect to main memory via a shared system bus. It is "symmetric" because memory access latency is identical for every processor.
*   **Distributed Shared Memory (DSM) / NUMA:** In this model, physical memory is partitioned and associated with specific CPU nodes. While the entire address space is globally accessible, access to local memory is significantly faster than remote memory accessed across the interconnection network, creating **Non-Uniform Memory Access (NUMA)**.

#### **2. The Memory Hierarchy Refresher**
Modern processors utilize a deep hierarchy (up to three levels of caches) to bridge the gap between CPU cycle times and main memory speeds.
*   **Latency Disparity:** The speed difference between the CPU and main memory currently exceeds **two orders of magnitude (100:1 ratio)** and continues to grow.
*   **The "Bad News" of Cache Misses:** Any failure to find instructions or data in the cache (L1, L2, or L3) requires an off-chip memory fetch, which is catastrophic for performance.
*   **Hierarchy levels:** L1 is typically core-specific, while L2 and L3 are often shared among multiple cores. Missing the **Last Level Cache (LLC)** is the most significant performance bottleneck as it forces a chip-exit.

#### **3. False Sharing and the Handyman Analogy**
**False sharing** occurs when independent variables accessed by different threads on different cores reside on the same cache line.
*   **The Handyman Analogy:** This is similar to a handyman who puts all the tools needed for a project (e.g., fixing a leaky faucet) into a single tool tray to avoid running back to the main toolbox. While large cache blocks take advantage of **spatial locality** (bringing more "tools" at once), they increase the likelihood that different threads will inadvertently "share" a cache line.
*   **System Impact:** Because the hardware cache coherence mechanism operates at the granularity of a cache block, it perceives the data as shared, causing the cache line to migrate unnecessarily between processors and disrupting useful work.

---

### **Volume XXV: Implementation of Synchronization: Atomics and Locks**

#### **1. Fundamental Atomic Read-Modify-Write (RMW) Primitives**
To implement mutual exclusion, architectures must provide instructions that perform a group of operations (read, check, and store) as a single, atomic unit.
*   **Test-and-Set:** Takes a memory location, returns the old value, and sets it to "1" (locked) atomically.
*   **Fetch-and-Increment:** Fetches the old value and increments the memory content by a specified amount in one step.
*   **Compare-and-Swap (CAS):** Takes three arguments: $L$, $old$, and $new$. If the value at $L$ equals $old$, it swaps it with $new$ and returns true; otherwise, it returns false.
*   **Fetch-and-Store:** Atomically retrieves the current value while storing a new value.
*   **Fetch-and-Phi:** A generic term for any RMW instruction that fetches a value and performs a function ($\phi$) before writing it back.

#### **2. Types of Locks and the " precious" Metaphor**
A lock is a mechanism that protects "precious" shared data from being corrupted by concurrent access.
*   **Mutual Exclusion (Exclusive) Lock:** Ensures that only **one thread at a time** can access the data. This is like two children taking turns to hit a ball; both hitting simultaneously is dangerous and ineffective.
*   **Shared Lock:** Allows **multiple readers** to inspect data simultaneously, provided they have the assurance that no writer will modify it during their inspection. This is analogous to multiple people reading the same newspaper at once.

#### **3. Evolution of Spinlocks**
*   **Naive Spin-on-Test-and-Set:** Processors continuously poll a memory location using `test-and-set`. This is highly inefficient because it **bypasses the cache** to access memory directly, causing massive network contention and impeding the current lock-holder.
*   **Spin-on-Read (Caching Spinlock):** Waiters perform a normal read to bring the lock value into their local cache and spin on the **cached value**. When the lock is released, the hardware cache coherence mechanism invalidates the local copies, alerting the waiters to attempt a `test-and-set`.
*   **Ticket Lock (The Deli Analogy):** To ensure **fairness**, this lock mimics a deli shop where customers take a unique ticket number. A requester uses `fetch-and-increment` to get a ticket and then spins until the `now-serving` variable matches their number. While fair, it remains "noisy" because every increment of `now-serving` invalidates the caches of all waiters.

---

### **Volume XXVI: Barrier Synchronization: Information Diffusion and Trees**

#### **1. Semantic Definition and Centralized Models**
A **barrier** ensures that all participating processors reach a specific point in their computation before any are allowed to proceed to the next phase. This is common in scientific applications that alternate between computation and synchronization.
*   **Counting (Centralized) Barrier:** Uses a shared counter initialized to $N$. Threads decrement the counter and spin while $count > 0$.
*   **The Race Condition Problem:** If released threads reach the *next* barrier before the last thread resets the counter to $N$, they may incorrectly "fall through" a zeroed counter.
*   **Sense Reversing Barrier:** To eliminate the reset-race and reduce spinning, a **sense variable** is used. Threads spin on a local sense flag that must match a global sense; the final arrival flips the global sense to release all waiters.

#### **2. Dissemination Barrier: The "Well-Orchestrated Gossip"**
The dissemination barrier works through **information diffusion** rather than a hierarchy, meaning $N$ does not need to be a power of two.
*   **The Protocol:** In each round $k$, processor $Pi$ signals $(Pi + 2^k) \pmod N$.
*   **Completion:** A processor knows the barrier is complete after receiving $\lceil \log_2 N \rceil$ messages. After these rounds, every processor has "heard" from every other processor.
*   **Implementation:** In shared memory, "messages" are signals to **statically determined spin locations**. By assigning these spots during construction, the system can place them in memory local to the spinner, which is vital for **NCC NUMA** machines.

---

### **Volume XXVII: The Tornado Operating System: Clustered Objects and Scalable VM**

#### **1. The Secret Sauce: Clustered Objects**
Tornado achieves scalability by replacing centralized data structures with **clustered objects**.
*   **Unity and Plurality:** The system provides the **illusion of a single object reference** that is identical across all nodes. However, "under the covers," the object can have multiple representations (replicas).
*   **Degree of Clustering:** The designer chooses the level of replication: singleton (shared), one per core, one per CPU, or one per group of processors.
*   **Consistency:** Replicas are kept consistent through **software-managed protected procedure calls** rather than hardware cache coherence, avoiding the "indiscriminate" overhead of hardware transactions.

#### **2. Objectized VM Management**
Tornado "detonates" the traditional Page Control Block (PCB) and page table into distinct objects to maximize concurrency.
*   **Process Object:** Replicated per CPU; handles read-only process information and TLB management.
*   **Region Object:** Partially replicated (one per group of processors); represents a portion of the address space.
*   **File Cache Manager (FCM):** Partitioned; manages the backing store for a region.
*   **DRAM Object:** Manages physical memory, often with one representation per **Distributed Shared Memory (DSM)** node to keep allocations local.
*   **Cached Object Representation (COR):** A shared object that handles the physical I/O with the disk.

#### **3. Non-Hierarchical Locking and Existence Guarantees**
Traditional hierarchical locking (Process $\rightarrow$ Region $\rightarrow$ Frame) kills concurrency by creating a bottleneck at the top-level Process object.
*   **Existence Guarantees:** Tornado uses **reference counting** instead of hierarchical locks.
*   **Mechanism:** When a thread services a page fault, it increments the reference count of the Process object. This ensures the object cannot be migrated or deleted while in use, but allows other threads to fault in different regions simultaneously.

---

### **Volume XXVIII: Lightweight RPC: Performance and Structure**

#### **1. The RPC Performance Hit**
Remote Procedure Calls (RPC) are fundamental to client-server systems but suffer from high runtime overhead compared to local calls.
*   **The Copying Burden:** Traditional RPC requires **eight copies** for a full call/return (four each way). This involves moving data from the client stack $\rightarrow$ RPC packet $\rightarrow$ kernel buffer $\rightarrow$ server address space $\rightarrow$ server stack.
*   **Control Overhead:** Each call incurs two traps and two context switches.

#### **2. Binding vs. Actual Calls**
LRPC reduces overhead by separating the one-time **binding** cost from recurring **calls**.
*   **Binding:** The kernel mediates the first call, creates a **Binding Object (BO)** (a capability for the client), and sets up a shared **Argument Stack (A-Stack)**.
*   **Actual Calls:** Using the A-Stack, data is passed **by value**. The kernel "doctors" the client thread—changing its PC and address space—to execute in the server's domain directly, a process called **thread borrowing**.
*   **Total Savings:** This reduces the data path to **two copies** (marshal to A-stack, unmarshal to E-stack) and avoids kernel buffering entirely.

---

### **Volume XXIX: Scheduling Heuristics and Virtualization**

#### **1. Scheduling for Cache Affinity**
Because Prozess-Memory speed gaps are so large, the scheduler's primary goal is to keep **caches warm**.
*   **Policies:**
    *   **Fixed Processor:** A thread stays on one CPU for life.
    *   **Last Processor:** A CPU picks a thread that recently ran on it.
    *   **Minimum Intervening (MI):** Selects the processor where the fewest other threads have run since the subject thread was last there.
    *   **Minimum Intervening + Queueing (MI+Q):** Adds the current size of the ready queue ($Q$) to the affinity index ($I$) to account for the pollution that will occur while waiting.

#### **2. Virtualization: Cellular Disco**
Cellular Disco uses virtualization to manage parallel hardware without rewriting operating systems for every new architecture.
*   **Trap-and-Emulate I/O:** When a guest OS issues an I/O request, the VMM intercepts it, fakes the requester's identity to the hardware, and later fakes an interrupt back to the guest when the I/O completes.
*   **Performance:** This "construction proof" shows that a VMM can manage multiprocessor resources with overhead kept **within 10%** for many applications.


---
<div style="page-break-after: always;"></div>
---
