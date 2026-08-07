# 15_Cache_Coherence (Synthesized Notes)

# Module 6: Cache Coherence

## 1. Introduction: The Cache Incoherence Problem

### Background Context
In modern multi-core processors, each core has its own fast, private cache (e.g., L1 cache) to reduce memory access times. While this vastly improves performance, it introduces a critical problem: **Cache Incoherence**. When multiple cores read and write to the exact same memory location, they can end up with conflicting versions of the data in their private caches. 

### 🧠 Mental Model: The Shared Ledger
Imagine a team of accountants (cores) working on a single shared ledger (main memory). To work faster, each accountant makes private photocopies of the ledger pages to keep at their desk (cache). If Accountant A updates their copy and doesn't immediately tell the others, Accountant B might read an outdated number from their own copy. Their ledgers are now *incoherent*. 

### Example: The Incoherence Quiz
Consider three cores (Core 0, 1, and 2) accessing a memory location initialized to `0`. Each core performs the following sequence: **Read → Increment → Write**.
- **Correct Uniprocessor Behavior**: Core 0 reads `0`, writes `1`. Core 1 reads `1`, writes `2`. Core 2 reads `2`, writes `3`. The final value should be `3`.
- **Incoherent Behavior**: If Core 1 reads the memory location *before* Core 0 writes its updated value back to main memory, Core 1 will also read `0` and write `1`. As a result, depending on timing and cache replacement policies, the final value in memory could incorrectly be `1`, `2`, or `3`. (Note: `0` or `4` are impossible since each core increments exactly once).

---

## 2. Defining Cache Coherence

### Intuition
A system is **coherent** if it behaves exactly as if there were no caches at all. In a coherent system, all cores must agree on a single, consistent version of truth for any given memory location.

### The Three Rules of Coherence
For a system to be officially coherent, it must satisfy three strict requirements:
1. **Single-Core Correctness (Program Order)**: If Core C1 writes to location `X` and later reads `X` (with no other cores writing to `X` in between), it must read the value it just wrote. This ensures standard uniprocessor rules apply locally.
2. **Write Propagation (Eventual Visibility)**: If Core C1 writes to location `X`, and Core C2 reads `X` after a "sufficient time" has passed, C2 must see C1's new value. Caches cannot serve stale data indefinitely.
3. **Write Serialization**: If multiple cores write to the same location, *all* cores in the system must see those writes occur in the exact same order. Cores cannot disagree on the timeline of events.

---

## 3. How to Achieve Coherence

How do we physically enforce the three rules above? 
*Naive approaches* (like having no caches, forcing all cores to share one L1 cache, or relying purely on write-through caches) either destroy performance or fail to guarantee coherence (write-through caches can still serve stale reads).

Instead, real-world systems use sophisticated protocols consisting of two main design choices:

### Choice A: What happens when a core writes?
1. **Write Update**: The writing core broadcasts the *new value* to all other caches that hold a copy of the block. They update their local copies.
2. **Write Invalidate**: The writing core broadcasts a *kill signal* (invalidation) for that address. Other caches delete their copies. The next time they need it, they must fetch the fresh data.

### Choice B: How do we serialize the writes?
1. **Snooping (Bus-Based)**: All caches are connected to a shared bus. Since a bus can only carry one message at a time, it acts as a natural serializing bottleneck. Every cache "snoops" (eavesdrops on) the bus to monitor for updates or invalidations relevant to its own blocks.
2. **Directory-Based**: A central directory tracks which cores have which blocks. Instead of broadcasting everything to everyone (which scales poorly), point-to-point messages are sent only to the specific cores that hold the affected block.

---

## 4. Write Update Snooping Coherence

In a basic **Write Update Snooping** protocol:
- Every time a core writes to a cached block, it sends the new value across the shared bus.
- All other caches monitor the bus. If they see an update for an address they hold, they overwrite their local copy with the new data.
- **Serialization Guarantee**: If two cores try to write to the same address simultaneously, they must arbitrate for access to the bus. The bus grants access one at a time. Therefore, every cache in the system sees the writes in the exact same order, satisfying coherence rule #3.

---

## 5. Optimizing Write Update Protocols

### The Problem: Memory and Bus Bottlenecks
A naive Write Update protocol acts like a Write-Through cache. Every single write goes to the bus *and* to main memory. Memory is slow, and the bus has limited bandwidth. 

### Optimization 1: The "Dirty" Bit (Saving Memory Writes)
- **Mechanism**: We add a `Dirty` bit to each cache block. When a core writes, it broadcasts the update on the bus (so other caches update), but **main memory is NOT updated yet**. The writing cache marks its block as `Dirty`.
- **Responsibility**: The `Dirty` bit means "Main memory is stale; I am now responsible for providing the true value." If another core misses and requests this block from memory, the memory stays quiet, and the `Dirty` cache intercepts the request to provide the fresh data.
- **Result**: Main memory is only updated when the `Dirty` block is finally evicted/replaced from the cache. This saves massive amounts of slow memory writes.

### Optimization 2: The "Shared" Bit (Saving Bus Broadcasts)
- **Mechanism**: We add a `Shared` bit to each cache block, and a "Shared Line" to the hardware bus. When a core reads a block, if any other cache snoops the read and realizes it also has the block, it pulls the Shared Line high (`1`). The reading core then marks its block as `Shared=1`.
- **The Optimization**: When a core wants to write:
  - If `Shared == 1`: It must broadcast the write on the bus to keep others updated.
  - If `Shared == 0`: It knows it has the *only* copy in the entire system (e.g., a private stack variable). It can silently write to its cache, mark it `Dirty`, and **skip the bus broadcast entirely**.
- **Result**: Private variables no longer consume precious bus bandwidth.

---

## 6. Write Invalidate Snooping Coherence

Instead of broadcasting the bulky new data, **Write Invalidate** simply broadcasts a kill signal.
- **Mechanism**: When a core writes to a block, it broadcasts the address on the bus as an invalidation. Other caches snoop this and set their `Valid` bit for that block to `0`. 
- The writing core updates its local cache, marks it `Dirty`, and marks it `Shared=0` (since it just killed all other copies).
- If another core wants to read that block, it suffers a cache miss, requests the block on the bus, and the `Dirty` cache provides it.
- **Local Writes**: Because the writing core knows it now has the only valid copy (`Shared=0`), any subsequent writes to that same block by that core happen completely silently without using the bus.

---

## 7. Write Update vs. Write Invalidate (Performance Trade-offs)

Which protocol is better? It depends heavily on the software's access patterns.

### 📊 Scenario: The Producer-Consumer Pattern
Core 0 writes to `A`, then Core 1 reads from `A`. This sequence repeats 1,000 times.
- **With Write Update (Optimized)**:
  - Core 0 writes and broadcasts the new value (1,000 bus uses).
  - Core 1 reads. The first read is a miss (1 bus use). The next 999 reads are hits because Write Update kept Core 1's cache perfectly synced.
  - **Total Bus Uses: 1,001**
- **With Write Invalidate (Optimized)**:
  - Core 0 writes, misses, and invalidates Core 1 (1 bus use).
  - Core 1 reads, misses (because it was invalidated), and fetches the data (1 bus use).
  - Core 0 writes again, invalidating Core 1 again (1 bus use).
  - Core 1 reads again, missing again (1 bus use).
  - **Total Bus Uses: 2,000**

### Summary
- **Write Update** is highly efficient for tight **producer-consumer sharing** where cores constantly read data written by others. Readers rarely suffer cache misses.
- **Write Invalidate** is much more efficient for **bursty, exclusive writes** (e.g., Core 0 writes to a block 1,000 times in a row before anyone else looks at it). It only uses the bus for the very first write, whereas Write Update would needlessly broadcast all 1,000 writes. Modern processors heavily favor Write Invalidate protocols (like MESI) due to these bandwidth savings on private data bursts.

---

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

---

# Playlist 4, Module 8: Advanced Coherence and Synchronization

Welcome to Module 8! In this module, we will explore the limitations of our previously discussed snooping-based cache coherence protocols and introduce **Directory-Based Coherence**, which scales much better for multi-core processors. We will also dive into the nuances of **Cache Misses** in multiprocessor systems (focusing on true vs. false sharing) and wrap up with an introduction to **Synchronization** and **Locks** to safely coordinate shared memory across threads.

---

## 1. Snooping Protocols Comparison: MESI, MOSI, MOESI

To understand the benefits of directory-based coherence, let's briefly review how our snooping protocols handle a specific sequence of memory accesses. 

### Scenario Setup
Imagine a system with 3 cores (C1, C2, C3). Block A starts in the **Invalid (I)** state in all caches. We execute the following sequence:
1. **C1 reads A**
2. **C1 writes A**
3. **C2 reads A**
4. **C2 writes A**
5. **C3 reads A**
6. **C1 reads A**

Let's compare the number of **memory reads** and **bus requests** required under different protocols.

### Step-by-Step Breakdown

1. **C1 reads A** 
   - **All Protocols:** Miss. C1 puts a read request on the bus, reading from memory. 
   - State in C1: **Exclusive (E)** (for MESI, MOESI) or **Shared (S)** (for MOSI, since MOSI lacks an E state).
2. **C1 writes A**
   - **MESI/MOESI:** C1 is in the E state, so it silently upgrades to **Modified (M)**. No bus request, no memory read!
   - **MOSI:** C1 is in the S state. It must issue an invalidation request on the bus to ensure no one else has the block. (Bus request +1).
3. **C2 reads A**
   - **All Protocols:** C2 misses and puts a read request on the bus. C1 (in M state) intercepts and supplies the data. No memory read is needed.
   - State in C1 downgrades to **Shared (S)** (MESI/MOSI) or **Owned (O)** (MOESI/MOSI).
   - State in C2 becomes **Shared (S)**.
4. **C2 writes A**
   - **All Protocols:** C2 is in the S state, so it must place an invalidation request on the bus. C1's copy is invalidated. C2 upgrades to **Modified (M)**.
5. **C3 reads A**
   - **All Protocols:** C3 misses and requests on the bus. C2 supplies the data. No memory read.
   - State in C2 downgrades to **O** (MOESI/MOSI) or **S** (MESI).
   - State in C3 becomes **S**.
6. **C1 reads A**
   - **All Protocols:** C1 misses and places a read request on the bus.
   - **With O state (MOSI, MOESI):** C2 is in the O state and intervenes to supply the data. No memory read.
   - **Without O state (MESI):** C2 is in the S state and cannot intervene. The data must be read from memory. (Memory read +1).

### Summary of Costs
- **Protocols with the 'O' state (MOSI, MOESI):** 1 memory read.
- **Protocols without the 'O' state (MESI):** 2 memory reads.
- **Protocols with the 'E' state (MESI, MOESI):** 5 bus requests.
- **Protocols without the 'E' state (MOSI):** 6 bus requests.

**Key Intuition:** The **Exclusive (E)** state saves bus requests on silent write upgrades, while the **Owned (O)** state saves memory reads by allowing a cache to supply dirty data even if it's shared. **MOESI** gives us the best of both worlds!

---

## 2. Directory-Based Coherence

### The Snooping Bottleneck
**Snooping relies on a broadcast bus.** Every cache miss and coherence request (like invalidations) must be broadcasted to *all* other caches. This ensures everyone sees the requests in the same order (maintaining the single-writer/multiple-reader coherence invariant). 

However, a single bus becomes a massive bottleneck as you add more cores. Beyond 8 to 16 cores, the bus is saturated, and cores spend most of their time waiting for bus access. Adding more cores yields no performance benefit.

### The Solution: Directories
To scale beyond 16 cores, we replace the broadcast bus with a **point-to-point non-broadcast network** and use a **Directory** to manage coherence. 

**Mental Model:** Think of the bus as a town hall meeting where everyone shouts their updates. A directory is like a decentralized registry office. Instead of shouting, you send a private message to the specific clerk (directory slice) in charge of the record you want, and they coordinate with only the relevant parties.

### How the Directory Works
- **Distributed Structure:** The directory is not a single centralized bottleneck. It is sliced up, typically with one slice located next to each core. 
- **Home Slice:** Each memory block is mapped (via its address) to a specific "Home Slice" of the directory. All requests for that block must go to its Home Slice.
- **Serialization:** The Home Slice determines the official ordering of accesses for its assigned blocks. If two cores try to write to the same block simultaneously, whichever request the Home Slice processes first is the "first" write.

### The Directory Entry
Each slice contains an entry for every block it manages. A directory entry consists of:
1. **Dirty Bit:** Is this block modified in some cache?
2. **Presence Vector (Presence Bits):** A bitmask with one bit per cache in the system. 
   - `1` means the cache *might* have a valid copy of the block.
   - `0` means the cache *definitely does not* have a valid copy.

### Directory Example: Independent Operations
Suppose we have a 4-core system. Block `X` is mapped to the directory slice at Core 0. Block `Y` is mapped to the directory slice at Core 1.
- **Core 0 writes to X:** It sends a request to the local directory slice for X.
- **Core 2 reads Y:** It sends a request over the network to the directory slice for Y at Core 1.
**Result:** These two operations happen completely independently and in parallel! There is no single bus bottleneck.

### Directory Example: Invalidation
What if Core 1 wants to write to `Y`, but Cores 2 and 3 currently hold it in the **Shared** state?
1. Core 1 sends a write request to `Y`'s Home Slice.
2. The directory looks at `Y`'s presence vector and sees bits set for Cores 2 and 3.
3. The directory sends targeted invalidation messages *only* to Core 2 and Core 3. (No broadcast!).
4. Cores 2 and 3 invalidate their copies and send acknowledgments back to the directory.
5. Once all acknowledgments are received, the directory clears their presence bits, sets the dirty bit, sets Core 1's presence bit, and replies to Core 1, granting write permission.

### Directory MOESI Protocol
Directories support standard cache states (like MOESI). For example, if Core 0 is the **Owner (O)** of block `A`, and Core 1 requests a read:
- Core 1 sends a read request to the directory.
- The directory sees Core 0 has the block and forwards the read request to Core 0.
- Core 0 sends the data directly to Core 1 (or via the directory) and acknowledges the directory.
- The directory updates its presence vector to show both Core 0 and Core 1 have the block.

---

## 3. Cache Misses with Coherence (The 4 C's)

Previously, we learned the **3 C's** of cache misses:
1. **Compulsory:** First time accessing a block.
2. **Capacity:** The cache is too small to hold all working data.
3. **Conflict:** The cache lacks sufficient associativity, causing blocks to evict each other.

With multi-core coherence, we introduce a **4th C: Coherence Misses**. A coherence miss occurs when you access data you previously had in your cache, but it was invalidated by another core.

### True Sharing vs. False Sharing
Coherence misses come in two flavors:

1. **True Sharing:**
   - **What it is:** Cores are actively reading and writing to the *exact same variable/data item*.
   - **Example:** Core 0 writes to `Variable X`. Core 1 then reads `Variable X`. Core 1 gets a coherence miss because Core 0's write invalidated Core 1's previous copy.
   - **Why it happens:** This is necessary for program correctness. The cores are truly sharing data.

2. **False Sharing:**
   - **What it is:** Cores are accessing *completely different variables*, but those variables happen to sit inside the *same cache block*.
   - **Example:** A cache block holds 4 words: `A, B, C, D`. Core 0 is aggressively writing to `A`. Core 1 is aggressively reading/writing to `B`. 
   - **The Problem:** Because coherence operates at the granularity of a **cache block** (not individual variables), Core 0's writes to `A` will invalidate the *entire block* for Core 1. When Core 1 tries to access `B`, it suffers a coherence miss, even though the value of `B` never actually changed! Core 1 then pulls the block back, invalidating Core 0, creating a "ping-pong" effect.
   - **Intuition:** Imagine you and your roommate share a single sheet of paper. You are writing on the top half, and they are writing on the bottom half. Even though you aren't interfering with each other's work, you keep having to yank the paper back and forth across the table. 
   - **Solution:** Pad or align independent data structures so they fall into separate cache blocks.

---

## 4. Synchronization

Now that we have coherent shared memory, how do threads coordinate their work safely? We need **Synchronization**.

### The Need for Synchronization
Imagine a program counting letter occurrences in a massive document. 
- Thread A processes the first half of the document.
- Thread B processes the second half.
- They both update a shared global array: `Count[letter]`.

**The Race Condition:**
Suppose both threads encounter the letter 'A' at the exact same time. The current `Count['A']` is 15.
1. Thread A loads 15.
2. Thread B loads 15.
3. Thread A increments its local copy to 16.
4. Thread B increments its local copy to 16.
5. Thread A stores 16 to memory.
6. Thread B stores 16 to memory.

**Result:** The final count is 16, but it should be 17! The interleaved execution corrupted our shared data. Cache coherence ensures they read the correct memory values, but it does *not* make a Read-Modify-Write sequence atomic.

### Mutual Exclusion (Locks)
To fix this, we need the Read-Modify-Write sequence to be a **Critical Section** or **Atomic Section**—a block of code that only one thread can execute at a time.

We enforce this using **Mutual Exclusion (Locks)**.
- We create a lock for the shared resource (e.g., `CountLock['A']`).
- Before updating the count, a thread must `lock()` it.
  - If the lock is open, the thread enters, and the lock closes.
  - If the lock is closed, the thread waits (spins) until it opens.
- After updating the count, the thread calls `unlock()`, allowing the next waiting thread to enter.

```c
// Safe synchronized code
lock(CountLock[letter]);
Count[letter] = Count[letter] + 1;
unlock(CountLock[letter]);
```

**Mental Model:** A lock is like the key to a single-occupancy restroom. Only one person can hold the key and be inside at a time. If someone else is inside, you must wait outside the door until they finish and hand you the key.

Locks prevent dangerous interleaving, ensuring that operations on shared data happen safely, one at a time. In the next module, we will explore exactly how to implement these locks efficiently at the hardware level!


---

