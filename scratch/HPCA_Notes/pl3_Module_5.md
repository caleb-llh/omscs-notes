# Module 5: Advanced Cache Optimizations

This module explores advanced techniques for optimizing cache performance, focusing on reducing miss rates and minimizing miss penalties. We cover software and hardware prefetching, compiler optimizations like loop interchange, non-blocking caches, and multi-level cache hierarchies.

## 1. The Impact of Block Size on Miss Rates (The 3 C's)

**Intuition:** Increasing the cache block (line) size brings more data into the cache on a single miss. If a program exhibits good spatial locality, this "extra" data will be used soon, converting potential future misses into hits.

How does increasing block size affect the three types of cache misses (Compulsory, Capacity, Conflict)?

*   **Compulsory Misses (Cold Start):** These occur the very first time a block is accessed. With a larger block size, there are fewer total blocks in the cache. Because each block contains more data, there are fewer "first-time" block accesses. Thus, compulsory misses are **reduced** (assuming spatial locality exists).
*   **Capacity Misses:** Imagine an array that is larger than the cache. With smaller blocks, the array occupies many blocks. With larger blocks, it occupies fewer blocks. As long as there is ample spatial locality, the larger blocks cover the required data more efficiently, **reducing** capacity misses.
*   **Conflict Misses:** Conflict misses happen when multiple addresses map to the same cache set and kick each other out. Fetching larger blocks means fewer total blocks are fetched to access the same amount of data, which generally leads to **fewer** conflict misses.

**Key Takeaway:** Increasing block size almost always reduces compulsory misses, and as long as there is sufficient spatial locality, it also reduces capacity and conflict misses.

## 2. Prefetching: Anticipating Future Accesses

**Mental Model:** Imagine a chef who knows the recipe so well that they ask their assistant to fetch ingredients from the pantry *before* they are needed. When it's time to add the ingredient, it's already on the counter.

Prefetching guesses which memory blocks will be accessed in the near future and brings them into the cache ahead of time.

*   **The Good (Hits):** If the guess is correct, the processor finds the data in the cache (a hit) instead of waiting for a memory fetch (a miss). This hides the memory latency.
*   **The Bad (Cache Pollution):** If the guess is wrong, we bring useless data into the cache. This useless data might replace (evict) useful data that was going to be accessed again. This is called **cache pollution**. Not only did we waste memory bandwidth, but we might also create *additional* misses by evicting good data.

### 2.1 Software Prefetching (Prefetch Instructions)

Compilers or programmers can insert explicit `prefetch` instructions into the code.

**Example: Array Traversal**
```c
for (int i = 0; i < N; i++) {
    // Prefetch an element P iterations ahead
    prefetch(&A[i + P]);
    sum += A[i];
}
```

The most critical factor here is the **prefetch distance ($P$)**: how far in advance should we prefetch?
*   **Too Small (Prefetching Too Late):** The data is requested but hasn't arrived from memory by the time the processor needs it. It's still a miss, though the penalty is slightly reduced because the data is already in transit.
*   **Too Large (Prefetching Too Early / Premature Prefetching):** The data arrives very early, sits in the cache, and gets evicted by other operations *before* the processor actually uses it. This causes cache pollution and wastes bandwidth.

**The Challenge:** Tuning the prefetch distance is tricky. It depends on the hardware (memory latency vs. processor speed). If the processor gets faster but memory doesn't, the prefetch distance must be increased. This makes hardcoding prefetch instructions fragile across different hardware generations.

### 2.2 Hardware Prefetching

Because software prefetching is rigid, modern processors implement hardware prefetching. The hardware transparently monitors memory access patterns and predicts future accesses.

*   **Stream Buffer (Sequential):** Detects when sequential blocks ($X$, then $X+1$) are accessed. It guesses that $X+2$, $X+3$, etc., will be needed and fetches them in advance.
*   **Stride-based Prefetcher:** Detects patterns with a constant distance (stride). If the processor accesses addresses $A$, $A+100$, $A+200$, the prefetcher predicts $A+300$ and starts fetching it.
*   **Correlating Prefetcher:** Learns complex, non-sequential sequences. If it observes the sequence $A \rightarrow B \rightarrow C$ multiple times, the next time it sees $A$, it will preemptively prefetch $B$ and then $C$. This is highly effective for pointer-based data structures like Linked Lists, where addresses are not sequential but the traversal order is predictable.

## 3. Compiler Optimizations: Loop Interchange

**Background Context:** In C/C++, 2D arrays are stored in "row-major order" (row 0, then row 1, etc.).

If a nested loop traverses a matrix column by column, it will access elements that are far apart in memory, causing a cache miss on almost every access. Furthermore, fetching a cache block brings in adjacent row elements that get evicted before they are used (because the inner loop moves down the column, not across the row).

**Loop Interchange** is a compiler optimization that swaps the inner and outer loops to match the memory layout.

**Before (Poor Locality - Column-Major Access):**
```c
for (int j = 0; j < COLS; j++) {
    for (int i = 0; i < ROWS; i++) {
        matrix[i][j] = 0; // High miss rate!
    }
}
```

**After (Good Locality - Row-Major Access):**
```c
for (int i = 0; i < ROWS; i++) {
    for (int j = 0; j < COLS; j++) {
        matrix[i][j] = 0; // Low miss rate!
    }
}
```

**Benefits:**
1.  **Improves Spatial Locality:** An entire fetched cache block is consumed completely before moving to the next block.
2.  **Enables Hardware Prefetching:** The accesses become perfectly sequential, which makes hardware stream buffers highly effective.

*Note: The compiler must mathematically prove there are no loop-carried dependencies before performing this transformation.*

## 4. Reducing Miss Penalty: Overlapping Misses

Out-of-Order (OoO) processors don't stop entirely on a cache miss. They try to find other independent instructions to execute. However, to truly hide miss penalties, the cache itself must support concurrent operations.

### 4.1 Non-Blocking Caches

A **blocking cache** stops and waits for memory on a miss. No other cache accesses can proceed.

A **non-blocking cache** allows the processor to continue querying the cache while a previous miss is being resolved.
*   **Hit Under Miss:** The cache can service hits to other blocks while waiting for the missed data from memory.
*   **Miss Under Miss:** The cache can process *multiple* misses simultaneously.

**Memory Level Parallelism (MLP):**
By supporting "Miss Under Miss," multiple memory requests are sent in parallel. Instead of paying the full miss penalty sequentially ($Penalty \times N$), the penalties overlap, so we roughly pay the penalty only once for a batch of misses. This dramatically reduces the effective miss penalty.

### 4.2 Miss Status Handling Registers (MSHRs)

To support Miss Under Miss, the cache uses MSHRs to track in-flight memory requests.

When a cache miss occurs, the cache checks the MSHRs:
1.  **No Match (New Miss):** The block is not currently being fetched. Allocate a new MSHR, send the request to memory, and record which instruction is waiting for it.
2.  **Match (Half Miss):** The block has *already* been requested by a previous miss, but hasn't arrived yet. The cache does not send a duplicate request to memory. Instead, it just adds the current instruction to the existing MSHR.

When the data finally arrives from memory, the cache checks the corresponding MSHR and wakes up *all* instructions waiting for that block.

*   Having even just 2-4 MSHRs provides significant performance benefits. Modern high-performance processors typically have tens of MSHRs (e.g., 16-32) to sustain high Memory Level Parallelism.

## 5. Cache Hierarchies (Multi-Level Caches)

**Mental Model:** A single cache is like a desk. If it's small, it's fast but you have to go to the library (main memory) often. If it's huge, it holds more, but it takes longer to find what you need.
The solution is a hierarchy: a small, ultra-fast desk (L1), a larger bookshelf in your room (L2), and the main library (Main Memory).

Instead of going straight to main memory on an L1 miss, the processor checks a Level 2 (L2) cache. If L2 misses, it might check an L3 cache (the Last Level Cache or LLC), and only then go to main memory.

**L1 vs. L2 Properties:**
*   **Capacity:** L1 is smaller than L2 (optimized for speed).
*   **Latency (Hit Time):** L1 is much faster than L2.
*   **Access Volume:** L1 receives vastly more accesses than L2 (because L2 only sees L1 misses).
*   **Associativity:** They do not need to have the same associativity (L2 is often more associative to prevent conflict misses since its latency requirements are slightly relaxed).

**AMAT with Cache Hierarchies:**

The Average Memory Access Time (AMAT) formula expands recursively:

$\text{AMAT} = \text{Hit Time}_{L1} + (\text{Miss Rate}_{L1} \times \text{Miss Penalty}_{L1})$

Where the L1 Miss Penalty is no longer just memory latency, but the cost of accessing the next level:

$\text{Miss Penalty}_{L1} = \text{Hit Time}_{L2} + (\text{Miss Rate}_{L2} \times \text{Miss Penalty}_{L2})$

And so on, until the Last Level Cache (LLC), where the miss penalty is the main memory access time.
