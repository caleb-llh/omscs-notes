# Module 7: Advanced Cache Coherence Protocols (MSI, MOSI, MOESI)

## 1. Write Update vs. Write Invalidate: The Final Showdown

Before diving into specific coherence protocols, it's crucial to understand why modern processors exclusively use **Write Invalidate** protocols over **Write Update** protocols. 

### Scenario Comparisons

| Scenario | Write Update | Write Invalidate | Winner |
| :--- | :--- | :--- | :--- |
| **Burst of writes to one address** (e.g., updating a counter in a loop) | **Bad**: Sends an update on the bus for *every single write*, causing massive bus contention. | **Good**: Sends one invalidation on the first write. Subsequent writes are silent cache hits. | 🏆 **Invalidate** |
| **Writing different words in the same block** (e.g., initializing an array) | **Bad**: Sends an update for every word written. One cache line could generate 10+ bus updates. | **Good**: First write invalidates the block. Remaining writes are silent cache hits. | 🏆 **Invalidate** |
| **Producer-Consumer** (Core A writes, Core B reads) | **Good**: Producer pushes updates directly to the consumer. Consumer always hits in the cache. | **Bad**: Producer invalidates. Consumer misses and fetches. Producer writes again (miss + invalidate). Causes high ping-pong traffic. | 🏆 **Update** |

### The "Knockout Punch": Thread Migration
While Invalidate is slightly better on average, **Thread Migration** is the scenario that makes Write Invalidate the undisputed champion.

**Mental Model:** Imagine a thread is working on Core 0. The OS scheduler decides to pause it and move it to Core 1 to balance the workload.
- **In Write Update:** Core 1 starts writing to the thread's data. Because Core 0 still has the old copies in its cache, Core 1 *keeps broadcasting updates to Core 0's cache* over the bus. Core 0 doesn't even need this data anymore! This wastes enormous amounts of energy and bandwidth until Core 0 eventually evicts the blocks.
- **In Write Invalidate:** Core 1's first write invalidates Core 0's stale copy. From then on, Core 1 works privately and silently. 

Because OS thread migration is very common, the horrible performance of Write Update in this scenario makes it entirely impractical. Thus, all modern processors use **Invalidation-based protocols**.

---

## 2. The MSI Protocol: The Foundation

MSI is the simplest realistic invalidation-based coherence protocol. Every cache block is in one of three states:

*   **M (Modified):** "Mine and changed." The block is dirty. This cache has the *only* valid copy in the entire system, and it has been modified. Memory is stale.
*   **S (Shared):** "Clean and shared." The block is clean (matches memory). Other caches might also have it in the S state. You can read it, but you cannot write to it without asking permission.
*   **I (Invalid):** "I don't have it." The block is either not in the cache, or it's there but marked invalid.

### State Transitions in MSI

**Local Actions (What the core does):**
*   **Local Read (I $\rightarrow$ S):** Cache puts a *Read Request* on the bus. Gets data, transitions to **S**.
*   **Local Write (I $\rightarrow$ M):** Cache puts a *Write Miss Request* (Read-Exclusive) on the bus. Gets data, invalidates others, transitions to **M**.
*   **Local Write to Shared (S $\rightarrow$ M):** Cache already has the data but needs to write. Puts an *Invalidation Request* on the bus (doesn't ask for data, just tells others to drop it). Transitions to **M**.

**Bus Snooping Actions (What the cache does when it sees others on the bus):**
*   **If in M State:**
    *   **Snoop Read:** Another core wants to read. We have the only valid (and dirty) copy. We must provide the data, write it back to memory, and downgrade to **S**.
    *   **Snoop Write:** Another core wants to write. We provide data (or let memory do it after write-back), write it back to memory, and downgrade to **I**.
*   **If in S State:**
    *   **Snoop Read:** Do nothing. Stay in **S**.
    *   **Snoop Write/Invalidation:** Another core is writing. Downgrade to **I**.
*   **If in I State:**
    *   Snoop anything: Do nothing. Stay in **I**.

---

## 3. Cache-to-Cache Transfers and Intervention

What happens in MSI when Core 1 has a block in **M** (Modified) and Core 2 wants to read it? 

Core 1 has the only up-to-date copy. Memory is stale. Core 1 *must* supply the data. There are two ways to handle this:

1.  **Abort and Retry (Inefficient):** Core 1 asserts an "Abort" signal on the bus, canceling Core 2's request. Core 1 writes the data back to memory. Core 2 retries the read and gets the data from memory. 
    *   *Drawback:* Costs two full memory latencies (one to write back, one to read).
2.  **Intervention (Modern Approach):** Core 1 asserts an "Intervention" signal. This tells the Main Memory: *"Stop! Don't respond. I have the fresh data."* Core 1 sends the data directly to Core 2 over the bus. 
    *   *The MSI Catch:* Because both caches now transition to the **S (Shared)** state, they both assume the block is clean. If memory doesn't grab the data right now, the dirty data will be lost forever. Therefore, during this intervention, **Memory must snoop the bus and write the data to itself**.

---

## 4. The MOSI Protocol: Saving Memory Bandwidth

**The Problem with MSI:** 
In MSI, every time a modified block is shared (M $\rightarrow$ S), the data must be written back to memory. If data bounces between cores (Core 1 writes, Core 2 reads, Core 3 reads), memory is constantly being written to and read from. Memory bandwidth is low, and memory operations are slow and power-hungry.

**The Solution: The O (Owned) State**
We add a new state, **O (Owned)**, to create the **MOSI** protocol. 

*   **O (Owned):** "Shared, but I'm the designated driver." The block is dirty (memory is stale), and multiple caches might have it, but *this* cache is the owner. 

**How MOSI changes the rules:**
*   When Core 1 is in **M** and snoops a read from Core 2, it provides the data but transitions to **O** (instead of S). Core 2 goes to **S**.
*   **Crucial Difference:** Memory is **NOT** updated. 
*   If Core 3 wants to read, the Owner (Core 1) provides the data. Memory is never accessed.
*   The Owner is responsible for writing the block back to memory *only* if it gets evicted from the cache. 

*Intuition:* The O state delays writing to memory for as long as possible, keeping high-speed data transfers strictly cache-to-cache.

---

## 5. The MOESI Protocol: Optimizing Thread-Private Data

**The Problem with MOSI/MSI:**
Consider thread-private data (e.g., a thread's local stack) or data in a single-threaded program. This data is *never* shared. 
In MSI/MOSI, if a core reads private data and then writes to it:
1.  Read: Misses, goes to bus, fetches from memory, transitions to **S**.
2.  Write: Cache is in **S**, so it *must* send an Invalidation on the bus to transition to **M**, even though no other cache has the data!
This wastes a bus transaction for every single private block. A simple uniprocessor wouldn't have this overhead.

**The Solution: The E (Exclusive) State**
We add the **E (Exclusive)** state to create the **MOESI** protocol (used by many modern architectures like AMD).

*   **E (Exclusive):** "Clean, but I'm the only one here." The block matches memory, but we are guaranteed to be the *only* cache holding it. 

**How MOESI changes the rules:**
*   When a core reads a block that is in *no other cache*, it transitions from I to **E** (instead of S).
*   If the core later writes to this block, it transitions from **E** to **M** **silently**, without sending any invalidation on the bus. 
*   If a core is in **E** and snoops a read from another core, it simply downgrades to **S** (or O, depending on specific implementation, but usually S since it's clean).

### MOESI State Summary Mental Model
| State | Dirty? (Memory Stale) | Exclusive? (Only copy) | Can Write Silently? |
| :--- | :--- | :--- | :--- |
| **M (Modified)** | Yes | Yes | Yes |
| **O (Owned)** | Yes | No | No (must invalidate) |
| **E (Exclusive)** | No | Yes | Yes (silently goes to M) |
| **S (Shared)** | No | No | No (must invalidate) |
| **I (Invalid)** | N/A | N/A | N/A |

### MOESI Walkthrough Example
Assume Block X is only in Memory.
1.  **Core 0 Reads X:** No one else has it. Core 0 goes to **E**.
2.  **Core 1 Reads X:** Core 0 snoops the read. Core 0 downgrades to **S**. Core 1 goes to **S**.
3.  **Core 2 Reads X:** Memory (or caches) provide data. Core 2 goes to **S**. (Cores 0, 1, 2 are all **S**).
4.  **Core 1 Writes X:** Core 1 is in **S**. It must send an Invalidation on the bus. Core 1 goes to **M**. Cores 0 and 2 go to **I**.
*(If Core 0 had written in Step 1 while in **E**, it would have gone straight to **M** without using the bus!)*