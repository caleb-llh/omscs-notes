# 17_Memory_Consistency (Synthesized Notes)

## Background Contexts
Memory Consistency deals with shared-memory multiprocessor systems where multiple threads run on different cores and communicate by reading and writing to the same memory space. While Cache Coherence ensures a consistent view of a *single* memory location, Memory Consistency defines how strictly the ordering among accesses to *different* memory locations should be enforced.

## Purpose
The purpose of Memory Consistency is to guarantee correct program behavior when dealing with multiple shared variables. It provides a set of rules (a consistency model) for how different memory accesses interleave, ensuring that synchronization mechanisms (like flags and locks) work properly across multiple cores.

## Connective Info
- Follows up on Cache Coherence, showing why coherence alone is insufficient for multi-variable synchronization.
- Introduces Memory Consistency Models (Sequential Consistency, Relaxed Consistency).
- Leads into Many-Core Architectures (NoC, Distributed LLC, Directory-Based Coherence) which implement these models at scale.

## Philosophy/Gist
If Coherence is the rule for a single conversation, Consistency is the rule for multiple simultaneous conversations. Sequential Consistency (SC) is intuitive but slow because it restricts out-of-order execution. Relaxed Consistency is fast but counter-intuitive, requiring programmers to explicitly add memory barriers (like `msync`) to enforce ordering only where it matters (e.g., synchronization points). If a program is Data-Race-Free, it behaves exactly the same on a relaxed consistency machine as on an SC machine.

## Hypotheticals (what if changed?)
- *What if we only had Cache Coherence without Memory Consistency?* Synchronization algorithms like flag signaling would break because cores could reorder reads/writes to different variables, leading to threads reading stale data even if the flag was updated.
- *What if we strictly enforced Sequential Consistency?* Performance would severely drop because cores couldn't use out-of-order execution or store buffers effectively, paying the full latency cost for every cache miss.
- *What if we don't use Memory Barriers in a Relaxed Consistency Model?* Data races will cause unpredictable, non-deterministic behaviors that break synchronization logic (like reading shared data before acquiring the lock).

## Common Examples
- **Flag Synchronization:** Core 1 waits for `flag == 1` to read `data`. Without consistency, Core 1 might read `data` before `flag` is updated, getting stale information.
- **Lock Implementation:** Using `MSYNC` (memory barrier) after acquiring a lock (Acquire Semantics) and before releasing it (Release Semantics) to prevent the processor from reordering critical section loads/stores outside the lock protection.
- **Many-Core Scaling:** Replacing the shared Bus with a Mesh Network-on-Chip (NoC), moving to Distributed Last Level Caches (LLC) sliced by set index or page number, and using Partial On-Chip Directories to handle scaling challenges.

# Playlist 5 Module 1: Memory Consistency

## Introduction to Memory Consistency

**Background Context:** In a shared-memory multiprocessor system, multiple threads run on different cores and communicate by reading and writing to the same memory space. Previously, we learned about **Cache Coherence**, which ensures that all cores have a consistent view of a *single* memory location. However, coherence is not enough to guarantee correct program behavior when dealing with multiple variables.

This is where **Memory Consistency** comes in. Memory Consistency determines how strictly the ordering among accesses to *different* memory locations should be enforced. 

> **Mental Model: The Conversation Timeline**
> - **Coherence** is like the rules for a single conversation (a single variable). It ensures everyone hears the exact same words in the exact same order.
> - **Consistency** is the set of rules for *multiple simultaneous conversations* (different variables). It determines how the timelines of those different conversations interleave with one another.

### Coherence vs. Consistency
- **Coherence** defines the order of accesses observable by different threads if these accesses go to the **same** memory location. Without coherence, a thread might read a stale value forever, making shared-memory programming impossible.
- **Consistency** defines the order of accesses to **different** memory addresses.

**Why does this matter?** If coherence already guarantees that my writes are seen by others, why do we care about the order of accesses to different addresses? Because synchronization algorithms (like flags or locks) fundamentally rely on the relative timing of updates to different variables.

> **⚠️ ENRICHMENT: Common Confusions**
> - **Confusion:** Thinking "Consistency is just Coherence for multiple variables."
> - **Correction:** Coherence is about *what* value is returned by a read (ensuring writes propagate). Consistency is about *when* that write becomes visible relative to writes to *other* variables. Coherence is an invisible hardware protocol; consistency is a visible programming model constraint.

---

## Why Consistency Matters

Let's look at a concrete example of why consistency matters, even with perfect coherence.

Imagine we have two variables, `D` and `F`, both initialized to `0`. 

*   **Core 1** writes `1` to `D`, and then writes `1` to `F`.
*   **Core 2** reads `F` into register `R1`, and then reads `D` into register `R2`.

If we execute strictly in program order, we might expect `(R1, R2)` to be `(0, 0)`, `(0, 1)`, or `(1, 1)`. 

**The Question:** Can we ever get `R1 = 1` and `R2 = 0`?
*   **In Strict Program Order:** No. If Core 2 reads `F = 1`, it means Core 1 has already executed its write to `F`. Because Core 1 executes in program order, it must have *already* written to `D`. Therefore, when Core 2 subsequently reads `D`, it must read `1`.
*   **In an Out-of-Order Processor:** Yes! Modern processors dynamically reorder loads and stores for performance. If Core 2 reorders its loads (reads `D` before `F`), or if Core 1 reorders its stores, we could end up with `R1 = 1` and `R2 = 0`.

This unexpected reordering breaks programmer intuition. Coherence was perfectly maintained for `D` and perfectly maintained for `F`, but the *consistency* between them was lost. 

> **🧠 ENRICHMENT: Mental Model (The Post Office)**
> Imagine mailing two letters (writes to `D` and `F`) from the same post office (Core 1). **Coherence** guarantees each letter eventually reaches its destination intact. **Consistency** dictates whether the recipient (Core 2) is guaranteed to receive letter `D` before letter `F`. Without a strict consistency model, the letters can take different routes through the network and arrive out of order.

---

## Consistency Matters Quiz: Flag Synchronization

To see how this breaks real programs, consider a common synchronization pattern: **Flag Synchronization**.

**Scenario:**
- `flag` and `data` are both initialized to `0`.
- **Core 1** waits for the flag: `while (flag == 0) { wait(); } print(data);`
- **Core 2** produces data: `data = 10; data += 5; flag = 1;`

**What can Core 1 print?**
1.  **`15`:** This is the expected, correct behavior. Core 2 finishes its writes, sets the flag, and Core 1 reads `15`.
2.  **`0` or `10`:** These are *incorrect* but possible on an out-of-order processor! 
    *   **How `0` happens:** Core 1 might use **branch prediction** to guess that the `while` loop will exit. It speculatively executes ahead and fetches `data` while it is still `0`. Later, Core 2 writes `15` and sets `flag = 1`. Core 1's branch prediction is verified as "correct" (the flag is indeed 1), and it prints the stale `data` it fetched earlier: `0`.
    *   **How `10` happens:** Similar to above, but the speculative read of `data` happens exactly between Core 2's write of `10` and increment by `5`.
3.  **Can it print `5`?** No. Core 2's writes to the *same* variable (`data`) are kept in program order by the core to maintain uniprocessor correctness.

**The Takeaway:** Coherence does not prevent Core 1 from fetching `data` before it validates the `flag`. We need a consistency model to enforce these ordering restrictions. A real-world equivalent is thread termination in an OS, where one thread waits for another to mark itself "done" before reading its output.

---

## Sequential Consistency (SC)

**Sequential Consistency (SC)** is the most natural and intuitive memory model for programmers. 

**Definition:** The result of any execution should be the same as if the memory accesses executed by each processor were executed in order, and the accesses among different processors were arbitrarily interleaved.

> **Mental Model: The Dealer and the Decks**
> Imagine each processor has a deck of cards representing its instructions in strict order. There is one central "dealer" (memory) who takes turns pulling the top card from any processor's deck. The dealer can switch between decks arbitrarily, but the cards *within* a specific processor's deck are always played in their original sequence.

### Simple Implementation of SC
The simplest way to implement SC is to force a core to perform its next memory access **only when all previous accesses are completely finished**.
- In the flag example, Core 1 cannot read `data` until the read of `flag` has completed and retired. 
- **The Drawback:** Performance is devastated. The Memory Level Parallelism (MLP) drops to exactly **1**. The processor pays the full latency cost for every single cache miss sequentially, destroying the benefits of pipelining and out-of-order execution.

### A Better Implementation of SC
We want the performance of out-of-order execution, but the *illusion* of Sequential Consistency. 
- A core is allowed to execute loads out of order.
- However, it must **monitor coherence traffic** to ensure its speculative out-of-order reads aren't invalidated.
- **Example:** If Core 1 reads variable `B` early, it watches the coherence bus. If Core 2 writes to `B` *before* Core 1 was supposed to read `B` in program order, a consistency violation might have occurred.
- **The Fix:** Core 1 flushes its Reorder Buffer (ROB) and replays the load of `B` and all subsequent instructions. Because the load hasn't committed yet, this rollback is safe.

> **⚖️ ENRICHMENT: Tradeoffs in SC Implementations**
> - **Naive SC (Stall-on-Miss):** Hardware is simple, but performance is abysmal. Wastes instruction-level parallelism (ILP).
> - **Speculative SC (MIPS R10000 style):** High performance (retains ILP/MLP) but hardware is vastly more complex. Requires aggressive snooping, ROB rollbacks, and high power consumption for speculation recovery.

---

## Relaxed Consistency Models

Instead of building complex hardware to fake SC, an alternative approach is to **relax the consistency model**. We tell programmers: *"The hardware will reorder accesses for performance. If you need strict ordering for synchronization, you must explicitly ask for it."*

### The Four Types of Memory Ordering
Memory operations can be classified into four orderings:
1.  **Write → Write (W-W)**
2.  **Write → Read (W-R)**
3.  **Read → Write (R-W)**
4.  **Read → Read (R-R)**

Sequential Consistency enforces all four. Relaxed models drop enforcement for some of these (often starting with R-R and W-W for different addresses) to allow more out-of-order optimizations.

### Memory Barriers (`MSYNC`)
To allow programmers to write correct synchronization algorithms on relaxed hardware, architectures provide special, **non-reorderable instructions**, such as memory barriers or fences (e.g., the `msync` instruction).
- The processor guarantees that all memory accesses *before* the `msync` complete before the `msync` executes.
- It also guarantees that the `msync` completes before any access *after* it begins.

**Fixing the Flag Example:**
```c
while (flag == 0) { wait(); }
msync(); // Barrier!
print(data);
```
The `msync` prevents the read of `data` from moving before the validation of `flag`. The processor gets maximum performance everywhere else but respects the ordering exactly where it matters.

> **⚠️ ENRICHMENT: Common Confusions**
> - **Confusion:** "A memory barrier flushes the cache."
> - **Correction:** Barriers do *not* typically flush caches to main memory. They simply stall the CPU's instruction pipeline or store buffer until previous memory operations have globally propagated. They enforce *ordering*, not *flushing*.

---

## MSYNC Quiz: Protecting a Critical Section

Let's apply memory barriers to a lock implementation on a highly relaxed processor (allows all 4 reorderings for different addresses).

```assembly
loop: LL r1, lock        // Load Linked: Read the lock
      BEQ r1, 0, loop    // If lock is held, keep spinning
      SC lock            // Store Conditional: Try to acquire the lock
      BEQ fail, loop     // If we failed to acquire, loop back
      
      // --- WHERE DOES MSYNC GO? ---
      MSYNC              // [1] AFTER ACQUIRE
      
      // --- Critical Section ---
      LOAD var
      INC var
      STORE var
      
      // --- WHERE DOES MSYNC GO? ---
      MSYNC              // [2] BEFORE RELEASE
      
      // --- Release Lock ---
      STORE lock, 0
```

**Why do we place `MSYNC` here?**
1.  **After Acquire (Acquire Semantics):** We must ensure we fully own the lock before we read or write the shared variable. Without `MSYNC`, the highly relaxed processor might speculatively move `LOAD var` *above* the lock acquisition!
2.  **Before Release (Release Semantics):** We must ensure all our updates to `var` are visible to other cores before we release the lock. Without `MSYNC`, the processor might execute `STORE lock, 0` *before* `STORE var`, allowing another thread to enter the critical section and read stale data.
3.  **Inside Critical Section:** No `MSYNC` is needed between `LOAD var` and `STORE var` because they access the *same* address, and single-thread uniprocessor correctness naturally keeps them in order.

---

## Data Races and Consistency

**Definition:** A **Data Race** occurs when there is a data dependence between accesses on different cores (at least one is a write), and these accesses are **not ordered by synchronization**. 
- Essentially, two threads are fighting over a variable without using locks, flags, or barriers.

### Data-Race-Free (DRF) Programs
A program is **Data-Race-Free (DRF)** if all accesses to shared data are correctly ordered by synchronization primitives. 

**The Golden Rule of Relaxed Consistency:**
> A Data-Race-Free program behaves exactly the same on a relaxed consistency machine as it would on a sequentially consistent machine.

**Why?** Because if your synchronization is correct, it utilizes barriers (`msync`) that enforce ordering exactly at the critical boundaries. Within those boundaries, no other thread is allowed to access the data, so hardware reordering is completely invisible and safe.

> **🧠 ENRICHMENT: Mental Model (The DRF Contract)**
> DRF0 (Data-Race-Free-0) is a contract between the programmer and the hardware.
> - **Programmer's side:** "I promise to use explicit synchronization (locks/barriers) around all shared variables."
> - **Hardware's side:** "If you keep your promise, I promise to behave exactly like a simple, Sequential Consistency machine, even though I am secretly reordering things under the hood for speed."

### The Debugging Challenge
While relaxed consistency is great for performance, it makes debugging buggy programs a nightmare. If a program has a data race, a relaxed processor will exhibit bizarre, non-deterministic behaviors that are impossible in SC.

For this reason, some advanced processors support switching between SC (for easier debugging) and a relaxed model (for maximum performance once the program is verified to be Data-Race-Free).

---

# Module 2: Consistency Models and Many-Core Architectures

## 1. Consistency Models (Continued)

### 1.1 Recap of Consistency Models
- **Sequential Consistency (SC):** Gives us the intuitive and expected behavior (as if memory operations from all cores were interleaved sequentially). However, SC strictly preserves orderings, which severely limits processor performance because it prevents many optimizations like out-of-order execution and store buffers.
- **Relaxed Consistency Models:** To improve performance, we can relax one or more of the four ordering rules (W->R, R->W, R->R, W->W).
  - Examples include: **Weak Consistency, Processor Consistency, Release Consistency, Lazy Release Consistency, Scope Consistency**, etc.
  - *Intuition:* Relaxed models allow processors to arbitrarily reorder data operations for maximum speed. But what if the programmer *needs* a specific order?
  - *The Solution:* **Synchronization Operations**. Relaxed models provide explicit synchronization primitives (like `mync` or memory fences/barriers, or specific library functions like mutexes). When the processor encounters these, it ensures that memory operations are completed and properly ordered, allowing the programmer to enforce correctness where necessary, while keeping the rest of the code fast.

*Mental Model:* Think of a relaxed consistency model as a busy kitchen where chefs (cores) prepare dishes (instructions) in whatever order is fastest. However, when the head chef yells "Service!" (a synchronization operation), everyone must finish their current tasks and present them in the exact right order before moving on.

---

## 2. Many-Core Architectures: Introduction and Challenges

As Moore's Law progresses, we put an increasing number of cores on a single chip (e.g., from 4 to 16, 64, or even hundreds of cores). This brings several massive scaling challenges.

### Challenge 1: On-Chip Coherence Traffic and the Bus Bottleneck
- **The Problem:** In a multicore system, writes to shared memory locations result in cache invalidations and subsequent cache misses. Both the invalidations and the misses generate coherence traffic on the shared bus.
- **The Bus Bottleneck:** As the number of cores increases, the total number of writes per second increases proportionally. The bus can only handle one request at a time (which is necessary to serialize writes and maintain coherence). Eventually, the required throughput exceeds the bus's capacity, and the bus becomes a massive bottleneck, forcing the cores to slow down.
- **The Solution:**
  1. **Scalable On-Chip Network (Network-on-Chip, NoC):** Replace the single shared bus with a scalable network (like a Mesh) that allows multiple parallel communications.
  2. **Directory-Based Coherence:** Stop relying on the bus to broadcast and serialize everything. Use a directory to point-to-point track cache line states.

> **⚖️ ENRICHMENT: Tradeoffs (Snooping vs. Directory)**
> - **Snooping (Bus):** Fast, low latency for cache-to-cache transfers, simple state machine. Fails to scale past ~8-16 cores due to broadcast traffic saturating bandwidth.
> - **Directory (NoC):** Highly scalable, point-to-point traffic conserves bandwidth. Higher latency (requires indirection through the directory node) and requires dedicated SRAM for directory storage overhead.

### 2.1 Network on Chip (NoC): Mesh vs. Bus
- **Bus Architecture:** Imagine 8 cores on a bus. If they need to communicate, only one can talk at a time. If we double the cores to 16, the bus gets longer (slower) and has twice the traffic demand. It saturates instantly.
- **Mesh Architecture:** Cores are organized into "tiles" (Core + L1 + L2) arranged in a 2D grid. Tiles are connected to their immediate neighbors.
  - *Why it's better:* Instead of one shared medium, there are many independent, short, and extremely fast point-to-point links. While Core A talks to Core B, Core C can simultaneously talk to Core D on different links.
  - *Scalability:* As you add more cores, you naturally add more links. The total aggregate bandwidth of the network grows with the number of cores.
  - *Physical Design:* A 2D Mesh is excellent for silicon manufacturing because the links do not cross each other, making it easy to print on a flat silicon wafer.
- **Alternative Topologies:**
  - **Torus:** Like a mesh, but the edges wrap around to connect to the opposite side (like a donut or a cylinder bent into a ring). This reduces the maximum distance between any two nodes, though it requires longer wrap-around wires that may cross others.
  - **Flattened Butterfly:** A more advanced topology providing even lower latency, at the cost of more complex wiring.

#### Example: Mesh vs. Bus Throughput Quiz
- **Scenario:** 4 cores. Each core generates 10 million messages/sec. Total demand = 40 million msgs/sec.
- **Bus Capacity:** 20 million msgs/sec.
- **Mesh Link Capacity:** 20 million msgs/sec per link.
- **Bus Result:** Demand (40M) > Capacity (20M). The bus forces all cores to slow down by 2x. They can only run at half speed.
- **Mesh Result:** The 10M msgs/sec from each core is distributed (round-robin) to the other 3 cores (3.33M each). Through careful routing analysis, the maximum traffic on any single link ends up being around 13.3 million msgs/sec. Since 13.3M < 20M link capacity, the mesh handles the traffic perfectly without slowing down the cores.
- **Speedup:** The mesh system is **2x faster** because the cores don't have to throttle themselves.

---

### Challenge 2: Off-Chip Memory Traffic
- **The Problem:** As the number of cores grows, the total number of cache misses grows proportionally (assuming the misses per core remains roughly constant). Every last-level cache miss requires fetching data from off-chip DRAM.
- **The Pin Bottleneck:** The number of physical pins on a CPU chip grows very slowly (maybe 10% when you double the cores) because pins must be physically large enough not to break. Thus, off-chip memory bandwidth does not scale with the number of cores.
- **The Solution:** We must drastically reduce the number of off-chip memory requests per core. We do this by implementing a **large, shared Last Level Cache (LLC)** (usually L3). If we double the cores, we must double the LLC size.

### 2.2 Distributed Last Level Cache (LLC)
- **The Monolithic LLC Problem:** If we just make one giant, centralized LLC, it will be slow. Moreover, it will have a single entry point on the mesh network. All L2 misses from all cores would route to this one spot, creating a massive traffic jam and over-utilizing the links near the LLC.
- **The Solution - Distributed LLC:** We slice the LLC into smaller pieces and distribute one slice to each core tile.
  - *Logical vs. Physical:* Logically, it is a single shared cache (no block replication; if a block is in the LLC, it exists in exactly one slice). Physically, it is distributed across the chip.
  - *Capacity:* A 16-core chip with 1MB slices per tile provides a total of 16MB of LLC.
- **How do we find the data? (Data Mapping Policies):**
  - **1. Round-Robin by Set Index:**
    - The most basic approach. We use the lower bits of the cache set index to determine which slice holds the data.
    - *Pros:* Perfectly distributes the load and capacity across all slices. Sequential memory accesses naturally spread across the whole chip.
    - *Cons:* Destroys physical locality. A core is just as likely to need data from a slice on the far opposite end of the chip as it is to use its local slice, causing high on-chip network traffic.
  - **2. Mapping by Page Number:**
    - We distribute data such that all blocks within a specific memory page map to the same LLC slice.
    - *Pros:* The OS can intentionally map a thread's pages (e.g., its stack) to the LLC slice physically located on the same tile as the core running that thread. This dramatically improves locality and reduces on-chip network traffic.
    - *Cons:* Can lead to load imbalance if some pages are accessed much more frequently than others.

> **⚖️ ENRICHMENT: Tradeoffs in LLC Mapping**
> - **Round-Robin (Block Interleaved):** Maximizes bandwidth utilization and balances capacity perfectly. Horrible for latency/locality since data is uniformly scattered.
> - **Page/OS Mapping:** Maximizes locality (minimizes network hops) and reduces latency. Risk of "hot spots" (e.g., everyone hammering a single shared page, overloading one specific tile's LLC and NoC links).

#### Example: Distributed LLC Quiz
- **Scenario:** 16 cores (4x4 mesh). 8MB total LLC, 256-byte blocks. Distributed round-robin by set number.
- **Address to lookup:** `0x12345678`
- **Question:** Which tile (slice) holds this address?
- **Solution:**
  - Block offset = 8 bits (since $2^8 = 256$ bytes). The lowest 8 bits of the address are `0x78`.
  - The next bits form the index. Since there are 16 slices, we need 4 bits to identify the slice ($2^4 = 16$).
  - In hex, 4 bits is exactly one hex digit. Looking at the address `0x12345678`, the digit immediately left of the offset `78` is `6`.
  - Therefore, the data maps to **Tile 6**.

---

### Challenge 3: On-Chip Directory Size
- **The Problem:** Since we moved from a bus to a scalable NoC, we must use Directory-Based Coherence. A traditional directory keeps an entry for *every possible block in main memory*. With gigabytes of RAM, this requires millions or billions of directory entries. Such a massive directory cannot possibly fit on the processor chip. If we place it off-chip in slow DRAM, we defeat the purpose of our ultra-fast on-chip caches.
- **The Solution: Partial On-Chip Directory**
  - We only need to keep directory entries for blocks that are *actually present* in at least one of the private L1 or L2 caches. If a block is only in the LLC or only in main memory (not in any private cache), no one is actively sharing or modifying it, so its directory presence bits would be all zeros anyway.
  - We allocate a small, fast directory on-chip with a limited number of entries per tile.
  - **Home Node:** The directory information for a block is stored on the exact same tile as the LLC slice that acts as the home for that block. This prevents unnecessary network hops when looking up both the data and the directory state.

> **⚠️ ENRICHMENT: Common Confusions**
> - **Confusion:** "Directory size must scale with Main Memory size."
> - **Correction:** A full directory does, but it's largely wasted tracking blocks that aren't even cached. A *Partial / Sparse Directory* only scales with the total capacity of the *private caches* (L1/L2), drastically reducing hardware cost, though it introduces directory evictions.

#### Example: On-Chip Directory Replacement Quiz
- **Scenario:** What happens when our limited on-chip partial directory gets full and we need to track a new block entering a private cache?
- **Solution:** Just like a standard cache, the directory must evict an existing entry. It uses a replacement policy (like LRU - Least Recently Used) to select an old directory entry to kick out.
- **Next Question:** What actually happens to the caches when we evict a directory entry? *(This leads into the next lesson about directory evictions).*


---
