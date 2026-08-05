# Shared Memory Parallel Breadth-First Search (BFS)

**Background Context:**
Breadth-First Search (BFS) is a fundamental graph analysis primitive used to determine the shortest distance (in terms of the number of edges) from a source vertex to all other vertices in a graph. In the real world, BFS powers everything from finding the shortest route in a GPS navigation system, to social network analysis (e.g., "six degrees of separation"), web crawling, and garbage collection in programming languages. 

> **Background Context:** While distributed-memory systems (like clusters running MPI) handle massive graphs that exceed a single machine's RAM, shared-memory systems are preferred for many graphs because they avoid expensive network communication overhead. A single modern server with terabytes of RAM and hundreds of cores can process graphs with billions of edges significantly faster using shared-memory parallelism.

> **Fact Check:** Shared memory is preferred for graph algorithms like BFS because graph traversal is inherently memory-bound with highly irregular access patterns. Network latency in distributed systems (MPI) dominates execution time due to fine-grained, unpredictable memory accesses, making shared-memory NUMA (Non-Uniform Memory Access) architectures much more efficient for graphs that fit in RAM.

> **Tradeoff:** Shared Memory vs. Distributed Memory. Shared memory offers low-latency, uniform-ish access and easier programming models, but is strictly bottlenecked by the maximum RAM capacity of a single node (scale-up). Distributed memory scales out horizontally to handle trillion-edge graphs, but incurs massive network communication overhead, requiring complex partitioning schemes (e.g., 1D/2D block cyclic) to minimize cross-node edge traversals.

This document outlines the transition from a standard sequential BFS algorithm to a highly parallelized approach optimized for shared-memory systems, leveraging a specialized data structure known as a "Bag".

---

## 1. Sequential BFS: A Quick Review

**Mental Model: The Ripple Effect**
Imagine dropping a stone into a still pond. The ripples spread outward in concentric circles. BFS works exactly like this: it explores a graph in "waves" (or frontiers) emanating from a source vertex $S$. Each wave represents a group of vertices that are one step further away from the source.

> **Mental Model:** You can also think of BFS like a fire spreading through a dry forest. The source node is where the match is struck. The fire spreads evenly in all directions. Trees that catch fire at time $t=1$ are 1 hop away; trees that catch fire at $t=2$ are 2 hops away. The frontier is the leading edge of the flames.

### Algorithm Overview
1. Initialize an array of distances $D$, setting $D[S] = 0$ and $D[v] = \infty$ for all other vertices.
2. Maintain a First-In-First-Out (FIFO) queue $F$ of unvisited vertices, initially containing only $S$.
3. While $F$ is not empty:
   - Extract a vertex $v$ from $F$.
   - Iterate over all outgoing neighbors $w$ of $v$.
   - If $w$ is unvisited ($D[w] == \infty$), update its distance ($D[w] = D[v] + 1$) and insert $w$ into $F$.

> **Common Confusion:** It is a common mistake to confuse the visited check ($D[w] == \infty$) in BFS with Dijkstra's algorithm. In unweighted BFS, the first time you discover a node, you have strictly found its shortest path. There is no need for a priority queue or relaxation step, which is why a simple FIFO queue suffices.

**Example:**
Consider a simple graph: `A -> B, A -> C, B -> D, C -> D`. Starting at $S=A$:
- **Wave 0:** Queue contains `[A]`. Pop `A`, visit `B` and `C`.
- **Wave 1:** Queue contains `[B, C]`. Pop `B`, visit `D`. Pop `C`, see `D` is already visited.
- **Wave 2:** Queue contains `[D]`. Pop `D`, no neighbors. Done.

> **Example:** If we changed the graph to include a cycle `A -> B -> A`, the check for visited nodes prevents an infinite loop. Wave 1 would pop `B`, see `A` as a neighbor, but since `A`'s distance is 0 (not $\infty$), it ignores it.

### Complexity Analysis
- **Work:** Each vertex is added to $F$ at most once. For a directed graph, each edge is visited at most once (twice for undirected). Thus, the total sequential cost (work) is **$\mathcal{O}(V + E)$**, where $V$ is the number of vertices and $E$ is the number of edges.

> **Fact Check:** This $\mathcal{O}(V + E)$ complexity assumes an adjacency list or Compressed Sparse Row (CSR) representation. If an adjacency matrix were used, the work would be $\mathcal{O}(V^2)$, as every vertex must check all $V$ potential neighbors regardless of edge existence. Real-world graphs almost exclusively use CSR for this reason.

---

## 2. Limitations of Sequential BFS

Why can't we just run the sequential algorithm on a multi-core processor?

### The Sequential Bottleneck
**Mental Model: The Single Turnstile**
Imagine a stadium with 50,000 empty seats (cores) but only a single turnstile (the FIFO queue). Everyone must line up one by one. The standard BFS contains a strict dependency: the next vertex to be inserted into the queue $F$ depends on the vertex just extracted from $F$. This enforces a sequential `while` loop that executes $\mathcal{O}(V)$ times, making it impossible for multiple processors to effectively share the workload.

> **Tradeoff:** You could attempt to parallelize the inner loop (iterating over neighbors $w$ of a single vertex $v$). However, if a vertex only has 2 neighbors, spinning up threads to process them introduces overhead that far outweighs the benefit. The granularity of work is too fine.

### The Sparsity Problem
In real-world applications (e.g., the Facebook friend graph, the World Wide Web), graphs are typically **sparse**. This means most nodes only connect to a tiny fraction of the total network, so the number of edges grows linearly with the vertices: $E = \mathcal{O}(V)$. 

- Because the span (the longest critical path of dependencies) of the sequential algorithm is $\mathcal{O}(V)$, the average available parallelism, defined as $\frac{\text{Work}}{\text{Span}}$, becomes $\frac{\mathcal{O}(V + E)}{\mathcal{O}(V)}$. 
- For sparse graphs, this ratio simplifies to a constant **$\mathcal{O}(1)$**. 

**Intuition:** An $\mathcal{O}(1)$ parallelism means that even if you had a supercomputer with 10,000 cores, the standard sequential algorithm offers almost **no available parallelism**. Only a few cores would be doing actual work, while the rest sit idle.

> **Mental Model: Work vs. Span:** Think of Work as the total gallons of water to be pumped, and Span as the longest un-bypassable pipe in the system. Parallelism (Work/Span) is the maximum number of pumps you can effectively use. If the pipe is narrow and long (high span), adding more pumps (cores) doesn't increase flow.

> **Fact Check:** The span of sequential BFS is strictly bounded by the number of vertices $V$ only in a completely linear graph (a linked list). In general, the span of the purely sequential loop is $\mathcal{O}(V + E)$. In parallel level-synchronous BFS, the span is proportional to the diameter $d$ of the graph, making the available parallelism $\mathcal{O}((V+E)/d)$.

> **Hypothetical:** Imagine trying to parallelize the sequential algorithm on a massive linked list (the sparsest possible connected graph). The span is exactly $V$, and the work is exactly $V$. The available parallelism is exactly 1. You cannot explore node 3 until node 2 is explored. Adding more cores does absolutely nothing.

---

## 3. Parallel BFS: Intuition & High-Level Approach

To unlock parallelism, we exploit the "wavy" nature of BFS. 

**Mental Model: An Army of Explorers**
Instead of sending a single explorer who walks from node to node, we dispatch an entire army. At step 1, the army explores all 1-hop neighbors simultaneously. At step 2, a larger army explores all 2-hop neighbors simultaneously. 

### The Two Big Ideas
1. **Level-Synchronous Traversal:** Process the graph level by level (wave by wave) rather than vertex by vertex. The number of sequential steps is no longer bounded by the number of vertices ($V$), but by the graph's **diameter** (the maximum shortest distance between any pair of vertices). In many real-world graphs, the diameter is surprisingly small (e.g., 6 in a global social network).
2. **Process Entire Levels in Parallel:** All vertices at a given level $L$ are exactly the same distance from the source. Because of this, the order in which they are processed *does not matter*. This allows us to process all vertices in the current frontier simultaneously across many cores.

> **Intuition:** By breaking the strict FIFO ordering of nodes *within* the same level, we eliminate the artificial sequential dependencies. As long as we finish level $L$ completely before starting level $L+1$, correctness is maintained.

> **Tradeoff:** Level-Synchronous vs. Asynchronous Traversal. Level-synchronous guarantees strict BFS shortest-path distances and has a clear termination condition per level via a global barrier. Asynchronous algorithms (e.g., Bellman-Ford style) allow threads to race ahead without waiting for barriers, maximizing CPU utilization but doing redundant work if a shorter path is found later. Level-synchronous is optimal for unweighted graphs, while asynchronous is often used for weighted graphs or architectures with extremely expensive barriers (like GPUs).

### High-Level Parallel Execution
Instead of a single queue, the algorithm maintains level-specific frontiers ($F_L$ and $F_{L+1}$). A function `process_level` takes the current frontier $F_L$, processes all its vertices in parallel, and generates the new frontier $F_{L+1}$.

---

## 4. The "Bag" Data Structure

If we process a level in parallel, thousands of threads might try to add new vertices to the next frontier $F_{L+1}$ at the exact same time. If they all try to write to a standard array or concurrent queue, the locking and synchronization overhead would destroy our performance gains. 

To implement the parallel frontier $F_L$ effectively, we need a data structure that supports massive parallelism. A **Bag** is a specialized container perfect for this role.

> **Fact Check:** The Bag data structure, specifically built using Pennants, was formally introduced by Leiserson et al. (the creators of Cilk). It is designed to be a highly concurrent data structure that perfectly complements work-stealing schedulers by allowing lock-free (or minimal lock) thread-local inserts.

> **Tradeoff:** Bag vs. Concurrent Queue. A concurrent queue maintains FIFO ordering but suffers from heavy contention on its head and tail pointers, even with fine-grained locks or compare-and-swap (CAS) operations. A Bag completely sacrifices ordering to eliminate contention. By giving each thread thread-local pennants (via reducers) and only merging at the end of the level, the Bag trades spatial locality and exact ordering for infinite parallel bandwidth.

**Mental Model:** Think of a Bag as a giant, unstructured sack. You can toss items into it as fast as you want without worrying about how they are ordered inside. 

### Key Properties of a Bag
1. **Unordered & Allows Repetitions:** To maximize parallelism during concurrent inserts, the Bag allows duplicate entries (e.g., multiple threads inserting the same neighbor). Redundancy is harmless since all threads will assign the exact same distance level to the vertex anyway.
2. **Fast Enumeration:** Allows rapid traversal of all elements in the frontier when it's time to process the next wave.
3. **Fast Split and Union:** Supports $\mathcal{O}(\log n)$ splitting into two roughly equal pieces (crucial for dividing work among cores) and fast merging.
4. **Logically Associative Union:** The union operation ($A \cup B \equiv B \cup A$) enables the use of **reducer hyperobjects** to manage concurrent insertions without locking (more on this in Section 5).

### Pennants: The Building Blocks
Bags are constructed using smaller structures called **Pennants**. 

**Mental Model & Definition:** A pennant is a tree containing exactly $2^k$ nodes. It features a single unary root (a "handle"), and this root has exactly one child which serves as the root of a perfect complete binary subtree of size $2^k - 1$.

```text
Pennant of size 1 (2^0):    Pennant of size 2 (2^1):    Pennant of size 4 (2^2):
    (Root)                       (Root)                       (Root)
                                   |                            |
                                (Child)                      (Child)
                                                             /     \
                                                          (Node) (Node)
```

- **Combining Pennants:** Two pennants of the *same size* ($2^k$) can be combined into a new pennant of size $2^{k+1}$ in **$\mathcal{O}(1)$ time**. We simply detach the root of one pennant and make it the new only child of the other root, shifting the old child down to complete the binary subtree.
- *Note:* You cannot combine pennants of different sizes.

### Duality Between Bags and Binary Arithmetic
A Bag can hold any arbitrary number of elements by exploiting a beautiful duality with binary arithmetic.

- **Intuition:** Just as any integer $n$ can be represented as a sum of distinct powers of 2 (its binary representation), a Bag of size $n$ is represented as a collection of pennants. 
- Each pennant corresponds to a "1" bit in the binary representation of $n$.
- **Example:** If a Bag contains $13$ elements (binary `1101`), it will consist of exactly one pennant of size $8$ ($2^3$), one pennant of size $4$ ($2^2$), and one pennant of size $1$ ($2^0$).
- **Spine:** These pennants are connected via a "spine"—an array of pointers where the $i$-th slot points to a pennant of size $2^i$, or is a `null` pointer if the $i$-th bit is 0.

### Bag Operations and Complexity
Bag operations perfectly mirror binary arithmetic operations:
- **Insertion ($\mathcal{O}(\log n)$):** Equivalent to binary addition (`+1`). Inserting an element is like adding `1` to a binary number. It might trigger a cascade of $\mathcal{O}(1)$ pennant combines (just like carrying a "1" over in addition: `0111 + 0001 = 1000`). Since the spine has length $\lceil \log n \rceil$, the worst-case cost is $\mathcal{O}(\log n)$.
- **Union ($\mathcal{O}(\log n)$):** Combining two bags of size $n$ is analogous to adding two binary numbers. The operation cascades up the spine, resulting in $\mathcal{O}(\log n)$ time. *Because many inserts don't cause a cascade, the amortized cost of inserting $n$ elements is $\mathcal{O}(1)$ per element.*
- **Splitting ($\mathcal{O}(\log n)$):** Equivalent to a right bit-shift (division by 2). The algorithm breaks the smallest available pennant in half, shifts it down the spine, and stores the remainder in a spare bag.

---

## 5. Parallel BFS Implementation Details

With Bags as the underlying data structure for frontiers, the `process_level` step operates using a **Divide-and-Conquer** strategy to distribute work across cores.

### Algorithm Flow
1. **Divide:** If the Bag $F_L$ is large enough, split it into two halves (using the $\mathcal{O}(\log n)$ split operation) and recursively call `process_level` on both halves in parallel.
2. **Base Case:** Once the Bag is sufficiently small (a constant cutoff size), fall back to a sequential loop over the vertices in that chunk.
3. **Parallel Neighbor Processing:** Iterate over the neighbors of the base-case vertices using a `parallel for` loop.
4. **Benign Data Races:** 
   - **Scenario:** What happens if two different threads process nodes `A` and `B`, and both `A` and `B` point to an unvisited node `C`? 
   - Both threads will attempt to update the distance of `C` simultaneously (`D[C] = L + 1`). 
   - **Resolution:** This data race is completely safe (benign) because all competing threads are writing the *exact same value*. It doesn't matter which thread "wins" the race; `C` will correctly end up with a distance of `L + 1`.

   > **Fact Check:** While the data race on `D[C] = L + 1` is algorithmically benign, at the hardware level, it causes **Cache Coherence Traffic (Ping-Ponging)**. Multiple cores writing to the same cache line simultaneously will repeatedly invalidate each other's L1 caches, saturating the memory bus. To mitigate this, high-performance implementations use a read-before-write check (e.g., `if (D[C] == \infty) D[C] = L + 1`) to ensure the write only happens once per cache line, drastically reducing interconnect traffic.

5. **Reducer Hyperobjects:** Vertices are inserted into the next frontier $F_{L+1}$ using logically associative bag unions backed by **reducer hyperobjects**. 
   - **Intuition:** A reducer gives each thread its own private, local Bag to toss vertices into, eliminating locks. When the threads finish their work, the system automatically merges (unions) their local Bags together into the final $F_{L+1}$ frontier in $\mathcal{O}(\log n)$ time.

   > **Mental Model: Reducer Hyperobjects:** Imagine a group of people counting coins. Instead of everyone adding to a single central pile (which causes bumping hands/contention), each person gets their own private cup (thread-local view). At the end, all cups are poured together (the reduce/union phase). The runtime automatically manages creating cups when threads split and pouring them together when threads join.

### Complexity Analysis
- **Work:** The algorithm remains work-optimal at **$\mathcal{O}(V + E)$**. We haven't done any extra algorithmic work; we've just reorganized *how* it's done.
- **Span (Critical Path):** 
  - The outer loop executes $d$ times (where $d$ is the diameter of the graph).
  - The span of `process_level` is determined by the recursion depth ($\mathcal{O}(\log V)$), the cost of splitting a bag ($\mathcal{O}(\log V)$), and the $\mathcal{O}(1)$ base case.
  - Overall Span: **$\mathcal{O}(d \cdot \text{polylog}(V))$**. 

*(Note: "polylog(V)" simply means some polynomial of a logarithm, which grows incredibly slowly, meaning the span is kept extremely tight and parallelism is highly optimized.)*

### Conclusion
By substituting a strict FIFO queue with a highly parallelizable Bag data structure, and traversing the graph level-synchronously, the shared-memory parallel BFS successfully eliminates sequential bottlenecks. It maintains optimal total work while unlocking massive scalability for modern multi-core systems.