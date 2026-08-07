# Module 4: Optimizing RPC and CPU Scheduling

## Part 1: Making Remote Procedure Calls (RPC) Cheap

### Overview
* **Goal**: Reduce RPC overhead to make it a viable mechanism for structuring OS services above the kernel (using the client-server paradigm).
* **Strategy**: Optimize the common case.
  * **Common Case**: The actual procedure calls made by the client to the server, which happen multiple times over their lifetime. Optimization focuses on reducing copying overhead and preserving cache locality.
  * **One-time Cost**: Setting up the client-server relationship happens exactly once. It is acceptable for this setup to be time-consuming if it makes the common case faster (similar to exokernel principles).

### The Binding Process (Setup)
**Binding** is the one-time setup of the relationship between the client and the server.
1. **Server Registration**:
   * The server publishes an entry point procedure (e.g., `foo`) to a **Name Server** (which acts like a Yellow Pages directory).
   * It registers this entry point with the kernel and waits for bind requests.
2. **Client Lookup**:
   * The client queries the Name Server, finds `s.foo`, and issues the first call, resulting in a trap into the kernel.
3. **Validation (Upcall)**:
   * The kernel makes an **upcall** to the server to verify if the client is authorized to make this call.
   * If valid, the server grants permission to the kernel.
4. **Procedure Descriptor**:
   * The kernel creates a **Procedure Descriptor**, an internal data structure specific to `foo`, containing:
     * The entry point address in the server's address space.
     * The required size of the **Argument Stack (A-Stack)**.
     * The number of simultaneous calls the server can accept (useful for multi-core/SMP systems).
5. **Setting up the A-Stack (Argument Stack)**:
   * The kernel allocates shared memory for the **A-Stack**.
   * It maps this buffer into the address spaces of *both* the client and the server.
   * **Purpose**: Allows direct communication (reading/writing arguments and results) without kernel mediation, effectively removing the kernel from the data-copying loop.
6. **Binding Object (BO)**:
   * The kernel authenticates the client and provides a **Binding Object (BO)** (a capability).
   * The client presents the BO for future calls to `s.foo`. The kernel uses the BO to look up the corresponding Procedure Descriptor.

### The Actual RPC Calls (Optimized Common Case)
* **Client Side**:
  * The client stub copies arguments *by value* directly into the A-Stack. (Passing by reference is not allowed since pointers would be invalid in the server's address space).
  * This is a simple memory copy, avoiding the expensive serialization required in traditional RPC.
  * The client traps into the kernel, presenting the BO.
* **Kernel Mediation (Domain Switch)**:
  * The kernel validates the BO.
  * **Optimization (Thread Doctoring)**: Since the client thread is blocked waiting for the RPC to complete, the kernel "doctors" the client thread to run directly in the server's address space.
  * The kernel sets the Program Counter (PC) to the server's entry point and provides a separate **Execution Stack (E-Stack)** for the server procedure to do its own work.
* **Server Side**:
  * The server stub copies arguments from the A-Stack into the E-Stack.
  * The procedure `foo` executes normally using the E-Stack.
  * Upon completion, the server stub copies the results from the E-Stack back into the A-Stack.
  * The server issues a return trap to the kernel.
* **Return to Client**:
  * The kernel expects this return trap (no validation needed).
  * It "re-doctors" the thread back to the client's address space.
  * The client stub reads the results from the A-Stack into its own stack, and normal execution resumes.

### Summary of RPC Overhead Reduction
* **Eliminated Costs**: The standard four kernel data copies (client → kernel, kernel → server, server → kernel, kernel → client) are completely eliminated. They are replaced by two user-space copies (client → A-Stack, A-Stack → E-Stack, and vice-versa).
* **Remaining Explicit Costs**:
  1. Client trap and BO validation.
  2. Switching domains (doctoring the thread from client to server).
  3. Return trap and switching back to the client domain.
* **Implicit Cost**: Loss of cache locality due to the domain switch (the processor cache may not contain the server's working set).

### RPC on Symmetric Multiprocessing (SMP)
* **Goal**: Mitigate the implicit cost of cache locality loss during domain switches.
* **Solution**: Preload server domains onto specific, dedicated processors.
* **Mechanism**:
  * Dedicate CPU(s) to a specific server domain. Do not run other threads on these CPUs, keeping their caches "warm" with the server's working set.
  * When a client makes an RPC call, the kernel directs the call to the CPU where the server is preloaded.
  * If a service is highly popular, the kernel can dedicate multiple CPUs to it to handle concurrent requests.
* **Benefit**: Encourages the software engineering practice of structuring OS services in separate protection domains (enhancing safety and system integrity) by making the RPC mechanism extremely cheap.

---

## Part 2: CPU Scheduling in Parallel Systems

### Scheduling First Principles & Memory Hierarchy
* **Trigger for Scheduling**: A thread blocks (e.g., I/O, synchronization) or its time quantum expires. The OS scheduler must pick the next thread to run.
* **Mantra for Performance**: "Keep the caches warm."
* **Memory Hierarchy Refresher**:
  * Multiple levels of cache (L1, L2, L3) exist between the CPU (fast, small) and Main Memory (slow, large).
  * The disparity between CPU cycle time and main memory access time is over two orders of magnitude.
  * **Conclusion**: To maintain high performance, the scheduler should pick a thread whose memory contents (working set) are already in the CPU's cache.

### Cache Affinity Scheduling
* **Definition**: Scheduling a thread on the same processor it last ran on, exploiting the likelihood that its working set remains in that processor's cache.
* **The Problem (Cache Pollution)**: While a thread $T_1$ is descheduled, intervening threads ($T_2$, $T_3$) may run on the same processor, overwriting and polluting $T_1$'s cached data. The scheduler must account for this pollution.

### Scheduling Policies
The OS can employ different policies, trading off metadata tracking complexity for better cache locality.

#### 1. First Come First Served (FCFS)
* **Mechanism**: Picks the thread that has been waiting the longest in the ready queue.
* **Focus**: Fairness (order of arrival).
* **Drawback**: Ignores cache affinity entirely.

#### 2. Fixed Processor
* **Mechanism**: A thread is permanently assigned to a specific processor upon its first execution (often based on initial load balancing).
* **Focus**: Thread-centric cache affinity.

#### 3. Last Processor
* **Mechanism**: A processor looks for threads that last ran on it. If none are available, it picks another thread.
* **Focus**: Thread-centric cache affinity.

#### 4. Minimum Intervening (MI) Policy
* **Mechanism**: Tracks an **Affinity Index ($I$)** for a thread across processors.
  * **Affinity Index ($I$)**: The number of intervening threads that have run on a processor since the target thread last ran there. (Lower $I$ = Higher Affinity).
* **Action**: Schedules the thread on the processor with the lowest Affinity Index.
* **Variant - Limited MI**: To save metadata overhead in large SMP systems, only track the Affinity Index for the top few processors (where $I$ is low) rather than all processors.
* **Focus**: Processor-centric cache affinity and minimizing past cache pollution.

#### 5. Minimum Intervening Plus Queuing (MI + Q)
* **Mechanism**: Considers both the Affinity Index ($I$) and the current size of the processor's scheduling queue ($Q$).
* **Rationale**: If a thread is placed in a processor's queue, the threads already in the queue will run *before* it, acting as additional intervening threads and further polluting the cache.
* **Action**: Schedules the thread on the processor where the sum $(I + Q)$ is minimized.
* **Focus**: Processor-centric cache affinity accounting for *future* cache pollution.

**Scheduling Policy Quiz Example**:
* Thread $T_y$ needs to be scheduled using MI + Q.
* Processor $P_u$: $I = 2$, $Q = 1$ $\rightarrow$ Total = $3$
* Processor $P_v$: $I = 1$, $Q = 4$ $\rightarrow$ Total = $5$
* **Decision**: Choose $P_u$ because $3 < 5$, resulting in less total cache pollution by the time $T_y$ actually runs.

### Implementation Issues
* **Global vs. Local Queues**:
  * **Global Queue**: Feasible for FCFS but scales poorly in large multiprocessors due to contention and size.
  * **Local Queues**: Each processor maintains its own ready queue. The organization depends on the chosen scheduling policy (e.g., sorted by affinity).
* **Work Stealing**: If a processor's local queue is empty, it may "steal" work from other processors' queues to maintain utilization.
* **Priority Attributes**: A thread's position in a queue is typically determined by:
  1. **Base Priority**: Assigned at creation (e.g., user importance, dynamic priority boosts for interactive threads).
  2. **Affinity**: Priority boost based on cache affinity.
  3. **Age ("Senior Citizen Discount")**: Priority boost for threads that have been in the system a long time, preventing starvation.