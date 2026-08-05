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