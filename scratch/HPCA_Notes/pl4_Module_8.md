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
