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

#### Example: On-Chip Directory Replacement Quiz
- **Scenario:** What happens when our limited on-chip partial directory gets full and we need to track a new block entering a private cache?
- **Solution:** Just like a standard cache, the directory must evict an existing entry. It uses a replacement policy (like LRU - Least Recently Used) to select an old directory entry to kick out.
- **Next Question:** What actually happens to the caches when we evict a directory entry? *(This leads into the next lesson about directory evictions).*
