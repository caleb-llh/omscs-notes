# Playlist 1 Module 5 Notes: Performance, Cache Affinity, and Scheduling

## Performance Metrics in Scheduling

When evaluating a scheduling policy, there are three primary figures of merit.

### System-Centric Metric
* **Throughput:** The number of threads that complete execution per unit of time. It measures how many threads are pushed through the system but does not indicate the performance of individual threads.

### User-Centric Metrics
* **Response Time:** The amount of time it takes for a thread to complete execution from the moment it is started. Users want response time to be as small as possible.
* **Variance of Response Time:** The variation in a thread's response time depending on the system's current load and the threads running ahead of it. Users prefer this variance to be very small.

**Example: First Come First Served (FCFS) Scheduling**
* **Pros:** Highly fair policy.
* **Cons:** 
  * Ignores cache affinity.
  * Treats small and large jobs equally.
  * Leads to a high variance in response time, especially if small jobs get stuck behind long-running jobs.

## Cache Affinity and Scheduling Policies

### Memory Footprint and Cache Warm-up
* The larger the memory footprint of a process, the longer it takes to load its working set into the cache.
* A **"warm cache"** allows a process/thread to execute without frequent long-latency memory accesses (cache misses).
* **Cache affinity scheduling** ensures that threads run on processors where their working set might already reside in the cache.

### Impact of System Load on Scheduling
* **Light to Medium Load:** Policies like *Minimum Intervening Scheduling* (and its queuing variant) work well. Threads often return to the same processor before their cache contents are overwritten.
* **Heavy Load:** Intervening threads might pollute the cache before a thread returns to its previous processor. In such cases, a *Fixed Processor Scheduling* approach may be more effective.
* **Agile OS:** The OS should dynamically adjust its scheduling policy based on the current load and workload characteristics.

### Procrastination in Scheduling
* **Definition:** A scheduling strategy where a processor intentionally inserts an idle loop instead of immediately picking a new thread from the run queue.
* **Why it helps:** If the run queue only contains threads with no cache affinity to the current processor, scheduling them would result in cache misses. By waiting (spinning its wheels), a thread that *does* have cache affinity for this processor might become runnable, leading to better overall performance.
* **Usage in Systems:** Procrastination is a common system design principle used in scheduling, synchronization algorithms (to reduce network contention), and file systems.

## Cache Affinity in Modern Multicore Processors

### Hardware Multi-threading
* Modern multicore processors often support **Hardware Multi-threading**, where multiple hardware threads run on a single core.
* **Execution flow:** When a thread experiences a long-latency operation (e.g., a cache miss requiring memory access), the hardware automatically switches to another thread on the same core.
* This keeps the execution engine (core) busy without OS intervention.

### Cache Hierarchy
* **L1 Cache:** Associated with a specific core and shared by the hardware threads on that core.
* **L2 Cache:** Shared across all cores.
* **L3 Cache (Optional):** Many modern chips have an L3 cache. The highest level cache before main memory is known as the **Last Level Cache (LLC)**.
* **Implication:** Missing in the L1 cache is manageable if the data is in L2. Missing in the Last Level Cache is bad news, as it triggers a very long-latency off-chip memory access.

### OS and Hardware Partnership
* **Hardware's Role:** Provides hardware threads inside each core and switches between them on cache misses.
* **OS's Role:** Maps software threads from its ready pool to the available hardware threads.
* **OS Goal:** 
  * Maximize the chance that threads find their working set in their respective L1 caches.
  * Ensure the combined working set of *all* scheduled threads fits into the shared L2 (or Last Level) cache.

## Cache Aware Scheduling

### Core Scheduling Mechanics
* **Example Setup:** A 4-core CPU where each core supports 4 hardware threads (16 hardware threads total). The OS has a pool of 32 ready threads.
* The OS scheduler must select 16 threads to execute concurrently on the hardware.

### Thread Characterization
Threads are profiled over time and categorized into two types:
* **Cache Frugal Threads:** Require only a small portion of the cache to execute efficiently.
* **Cache Hungry Threads:** Have a large working set and require a huge amount of cache space.

### The Optimization Goal
* Let `N` be the number of cache frugal threads and `M` be the number of cache hungry threads.
* Constraint 1: `N + M = Total available hardware threads` (e.g., 16).
* Constraint 2: The cumulative cache requirement of all `N + M` threads must be **less than the total capacity of the Last Level Cache**.
* **Why:** This prevents thrashing and long-latency memory accesses by ensuring the shared cache can accommodate the working sets of all concurrently executing threads.

### Profiling and Monitoring Overhead
* The OS must profile threads to determine if they are cache frugal or cache hungry.
* **Challenge:** Monitoring requires OS intervention, consuming CPU cycles that could be used for useful work.
* **Principle:** A good OS provides resources and gets out of the way. The overhead for information gathering must be kept minimal so it does not disrupt the actual workload.

## Conclusion

* Process scheduling is an **NP-complete** problem.
* We must rely on **heuristics** to design good scheduling algorithms.
* As workloads change and hardware architectures evolve (more cores, deeper cache hierarchies, more hardware threads), there is a continuous need for better scheduling heuristics. The final word on parallel system scheduling has not yet been written.
