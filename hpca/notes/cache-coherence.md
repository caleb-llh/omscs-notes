# Cache Coherence

---

#### **1. Foundational Theory of Cache Coherence**

##### **1.1. The Shared Memory Expectation**
In a shared memory system, programmers expect a consistent behavior where communication occurs through memory addresses. Specifically, if one core writes a value to a variable, any subsequent read by another core should return that "last write". 

##### **1.2. The Hardware-Software Gap: Private Caches**
To maintain high performance and throughput, modern hardware provides each processor core with its own **private L1 cache**. A single, large shared L1 cache would be too slow to satisfy simultaneous requests from all cores. However, this private architecture creates the **cache coherence problem**:
*   **Data Divergence:** If Core A writes a value (e.g., $x=15$) to its private cache but does not update main memory, and Core B then reads $x$ from main memory, Core B will receive stale data (e.g., $x=0$).
*   **Persistence of Incoherence:** Once Core B brings the stale data into its own private cache, it may continue to hit on that stale value indefinitely, while Core A continues to update its own copy without notifying others.
*   **Definition of Incoherence:** A system is incoherent when the same memory location, as viewed by different cores, contains different values.

##### **1.3. Formal Requirements for Coherence**
A system is considered coherent if it behaves as though no caches exist. This requires the satisfaction of three specific properties:
1.  **Correct Uniprocessor Behavior:** A read (R) from address $X$ by core $C_1$ must return the value of the most recent write (W) to $X$ by the same core $C_1$, provided no other core has written to $X$ between the access $W$ and $R$.
2.  **Write Propagation (Visibility):** If core $C_1$ writes to location $X$, a read of $X$ by core $C_2$ must return the written value if the read occurs after a "sufficient time" and no other writes intervene. This prevents a core from reading a stale value forever.
3.  **Write Serialization:** All writes to the same location must be seen in the **same order** by all cores. Different cores cannot disagree on which of two writes to the same address occurred first.

---

#### **2. Taxonomy of Cache Misses in Coherent Systems**

In addition to the standard "3 Cs" (Compulsory, Capacity, and Conflict misses), coherence introduces a **Fourth C: Coherence Misses**.

##### **2.1. True Sharing Misses**
These occur when different cores access the same data item. For example, if Core 1 reads address $A$, then Core 2 writes to $A$, Core 1 will experience a coherence miss when it next tries to read $A$ because its copy was invalidated to maintain coherence.

##### **2.2. False Sharing Misses**
False sharing occurs when different cores access **different data items** that happen to reside within the **same cache block**. 
*   Because coherence is maintained at the granularity of the cache block, an update to one word in a block invalidates the entire block for all other caches.
*   This results in a miss for other cores even though they are not actually sharing data, leading to unnecessary performance degradation.

---

#### **3. High-Level Coherence Strategies**

##### **3.1. Write-Update vs. Write-Invalidate**
There are two primary approaches to ensuring that reads see the values produced by writes:
*   **Write-Update Coherence:** Every write to a cache is immediately sent to all other caches that hold a copy of that block, updating their values. 
*   **Write-Invalidate Coherence:** A write to a cache block ensures that it is the only copy in the system by invalidating all other copies. Subsequent reads by other cores will result in a cache miss, forcing them to fetch the new data.

##### **3.2. Implementation Frameworks**
The mechanism for ordering writes and identifying which caches to update/invalidate falls into two categories:
*   **Snooping:** All writes are broadcast on a shared bus. Every cache "snoops" the bus to observe these writes and maintain its own state accordingly. The bus acts as the serialization point.
*   **Directory-Based:** An ordering point called a **Directory** is assigned to each block. The directory tracks which caches hold the block and manages invalidations or updates without requiring a global broadcast.

---

#### **4. Snooping-Based Implementation: The MSI Protocol**

The **MSI protocol** is a basic invalidation-based snooping protocol utilizing three states for cache blocks:

##### **4.1. MSI State Definitions**
*   **Invalid (I):** The block is either not present or the valid bit is not set. It cannot be read or written.
*   **Shared (S):** The block is "clean" (matches memory). Multiple caches can hold the block in this state for reading.
*   **Modified (M):** The core has exclusive read/write access. The block is "dirty" (the only up-to-date copy in the system) and memory is stale.

##### **4.2. State Transitions (Local Requests)**
*   **Read Miss (I $\rightarrow$ S):** The core puts a read request on the bus, fetches the data (from memory or another cache), and enters the Shared state.
*   **Write Miss (I $\rightarrow$ M):** The core puts a write request on the bus, which invalidates all other copies. The block moves to Modified.
*   **Write Hit on Shared (S $\rightarrow$ M):** Because the core already has the data but not the right to write, it puts an **invalidation request** on the bus. Once others invalidate, the block moves to Modified.

##### **4.3. State Transitions (Snooped Bus Requests)**
*   **Snoop Write on M:** The cache must **write back** the dirty data to memory before transitioning to Invalid.
*   **Snoop Read on M:** The cache must **write back** the dirty data to memory and transition to Shared.
*   **Snoop Write on S:** The cache simply transitions to Invalid without a write-back.

---

#### **5. Advanced Snooping States: MOSI, MESI, and MOESI**

To address inefficiencies in the MSI protocol, additional states are introduced:

##### **5.1. The Owner (O) State (MOSI)**
*   **Problem:** In MSI, every cache-to-cache transfer (M $\rightarrow$ S) requires a write-back to memory, which is slow and energy-intensive.
*   **Function:** The **Owned** state is introduced to allow a cache to provide data to other readers without updating memory.
*   **Behavior:** The Owner is the one responsible for eventually writing the block back to memory if it is replaced. It behaves like the Shared state (allows reads) but indicates the data is dirty.

##### **5.2. The Exclusive (E) State (MESI)**
*   **Problem:** In MSI, even if a core is the only one using a piece of data (thread-private data), it must still perform a bus request to move from S to M on its first write.
*   **Function:** The **Exclusive** state indicates that a core is the **only** one holding the block, but the block is **clean**.
*   **Optimization:** If a block is in the E state, a local write can transition it to M **silently** (without a bus request).

##### **5.3. MOESI Protocol Summary**
*   **M (Modified):** Exclusive, dirty, can read/write.
*   **O (Owned):** Shared, dirty, responsible for providing data and write-back.
*   **E (Exclusive):** Exclusive, clean, can read/write (transitions to M).
*   **S (Shared):** Shared, clean, read-only.
*   **I (Invalid):** No access.


---

#### **6. Cache-to-Cache Transfer Mechanisms**

When a processor requires a data block that is currently held in a **Modified (M)** state by another core's private cache, the system must facilitate a transfer. Because the only up-to-date copy exists in the remote cache (and not in main memory), the "owner" must respond.

##### **6.1. Abort and Retry**
This is a simpler but less efficient mechanism for managing remote hits:
*   **Protocol:** When Core 2 (C2) places a read request on the bus for a block held in M-state by Core 1 (C1), C1 asserts an **Abort bus signal**.
*   **Action:** This signal forces C2 to "back off" and terminate its request. 
*   **Memory Update:** C1 then performs a standard write-back of the dirty block to main memory.
*   **Completion:** C2 subsequently retries its read request, which is now satisfied by the updated main memory.
*   **Performance Penalty:** This approach incurs at least **twice the memory latency** (one for the write-back and one for the subsequent read) plus bus arbitration overhead.

##### **6.2. Intervention**
Modern processors favor intervention to avoid the latency of double memory accesses:
*   **Protocol:** Upon detecting a bus request for its dirty block, C1 asserts an **Intervention bus signal**.
*   **Action:** This signal instructs main memory *not* to respond to the request. C1 then provides the data directly to C2 over the bus.
*   **Memory Snarfing:** While C1 is providing the data to C2, main memory must "pick up" or "snarf" the data from the bus. 
*   **Necessity of Snarfing:** Since both C1 and C2 will transition to the **Shared (S)** state after the transfer, the block is no longer considered "dirty" in either cache. Without the memory picking up the data during this transfer, the "fresh" data would be lost, and memory would remain stale indefinitely.
*   **Trade-offs:** While faster, this requires more complex hardware for caches to insert data into memory-response slots and for memory to identify and capture intervention traffic.

---

#### **7. Directory-Based Coherence Architecture**

As systems scale beyond 8–16 cores, a shared bus becomes a bottleneck because every request (including misses and invalidations) must be broadcast to every core. **Directory-based coherence** replaces global broadcasts with point-to-point communication.

##### **7.1. Distributed Directory Structure**
*   **Slicing:** The directory is not a centralized entity but is distributed across the cores as **"slices"**.
*   **Home Slice:** Every memory block is assigned a "Home Slice" based on its physical address. The home slice is the authoritative ordering point for that specific block.
*   **Parallelism:** Different slices operate independently on disjoint sets of blocks, allowing for significantly higher aggregate bandwidth than a single bus.

##### **7.2. Directory Entry Anatomy**
A directory entry for a single block typically consists of:
*   **Dirty Bit:** A single bit indicating if the block is held in a Modified/Exclusive state by any cache in the system.
*   **Presence Vector:** A bitmask with one bit per cache in the system. For an 8-core system, this is an 8-bit vector where a '1' indicates the corresponding cache holds a valid copy.

##### **7.3. Directory Transaction Flow (Example)**
1.  **Request Phase:** A cache miss is sent via the interconnection network to the block's **Home Slice**.
2.  **Lookup Phase:** The directory controller checks the entry for that block.
3.  **Coherence Action:**
    *   **If Clean/Uncached:** The directory fetches data from memory and sends it to the requester, setting the appropriate presence bit.
    *   **If Dirty:** The directory **forwards** the request specifically to the cache(s) identified in the presence vector.
4.  **Acknowledgement Phase:** The remote cache performs the required action (e.g., invalidation or data supply) and sends an **acknowledgement** back to the directory.
5.  **Completion:** Once the directory receives all necessary acknowledgements, it updates the state and sends a final response/data to the original requester.

---

#### **8. Comparative Analysis: Write-Update vs. Write-Invalidate**

The choice between updating all copies or invalidating them depends heavily on application access patterns.

##### **8.1. Scenario Performance**
*   **Burst Writes to One Address:** In a **Write-Update** protocol, every write in a burst (e.g., intermediate calculations) triggers a bus broadcast, causing high contention. In **Write-Invalidate**, only the first write broadcasts; subsequent writes are local cache hits.
*   **Block Initialization:** When a core writes to every word in a block (initializing data), **Write-Update** sends an update for every word. **Write-Invalidate** sends one invalidation for the first word, and the rest are local hits.
*   **Producer-Consumer:** **Write-Update** is highly efficient here, as the producer automatically pushes data into the consumer's cache. In **Write-Invalidate**, the consumer suffers a mandatory cache miss for every new value produced.

##### **8.2. The "Thread Migration" Problem**
Thread migration is the decisive factor favoring **Write-Invalidate** in modern OSs:
*   **Update Failure:** If a thread moves from Core A to Core B, a Write-Update protocol will continue to update Core A’s cache indefinitely for every write the thread performs on Core B, wasting bandwidth on "ghost" copies.
*   **Invalidate Efficiency:** Under Write-Invalidate, the first write Core B performs will invalidate Core A's old copy, ending all further traffic to the old core.

---

#### **9. Optimization of Write-Update Protocols**

To mitigate the bandwidth limitations of basic Write-Update (which traditionally behaves like a write-through cache), two primary optimizations are used.

##### **9.1. The Dirty Bit (Memory Write Reduction)**
*   **Problem:** Standard Write-Update broadcasts every write to both other caches and main memory.
*   **Solution:** Adding a **dirty bit** allows the cache to delay memory updates.
*   **Mechanism:** A write updates other caches via the bus but marks the block as "dirty," indicating memory is stale. Responsibility for the eventual write-back to memory stays with the current "owner" (the last writer).

##### **9.2. The Shared Bit (Bus Traffic Reduction)**
*   **Problem:** Even with a dirty bit, every write must still use the bus to check for other sharers.
*   **Solution:** A **shared bit** tracks whether other caches hold the block.
*   **Shared Line:** During a read miss, a special bus line is pulled by other caches if they hold the block. If the line remains low, the requester knows it is the only holder and sets the **Shared Bit to 0**.
*   **Silent Writes:** If a block is not shared (Shared Bit = 0), the core can perform subsequent writes **locally** without any bus traffic. If the block is shared, it reverts to standard broadcast updates.

---

#### **10. Formal Case Study: Liveness and Correctness**

Coherence protocols prevent "stuck" states in parallel programs.

*   **Coherence Example:** In a system where Core 1 spins until `A != 1` and Core 2 spins until `A != 0`, a coherent system guarantees both will eventually proceed. 
*   **Visibility Guarantee:** Because the protocol ensures **Write Propagation**, Core 2's update to `A` must eventually be seen by Core 1.
*   **Serialization Guarantee:** Because all cores must agree on the order of writes, it is impossible for Core 1 and Core 2 to both believe they were the "last writer" and remain stuck in their respective loops.
