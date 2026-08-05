# Shared Memory Parallel Breadth-First Search (BFS)

**Background Context:**
Breadth-First Search (BFS) is a fundamental graph analysis primitive used to determine the shortest distance (in terms of the number of edges) from a source vertex to all other vertices in a graph. In the real world, BFS powers everything from finding the shortest route in a GPS navigation system, to social network analysis (e.g., "six degrees of separation"), web crawling, and garbage collection in programming languages. 

This document outlines the transition from a standard sequential BFS algorithm to a highly parallelized approach optimized for shared-memory systems, leveraging a specialized data structure known as a "Bag".

---

## 1. Sequential BFS: A Quick Review

**Mental Model: The Ripple Effect**
Imagine dropping a stone into a still pond. The ripples spread outward in concentric circles. BFS works exactly like this: it explores a graph in "waves" (or frontiers) emanating from a source vertex $S$. Each wave represents a group of vertices that are one step further away from the source.

### Algorithm Overview
1. Initialize an array of distances $D$, setting $D[S] = 0$ and $D[v] = \infty$ for all other vertices.
2. Maintain a First-In-First-Out (FIFO) queue $F$ of unvisited vertices, initially containing only $S$.
3. While $F$ is not empty:
   - Extract a vertex $v$ from $F$.
   - Iterate over all outgoing neighbors $w$ of $v$.
   - If $w$ is unvisited ($D[w] == \infty$), update its distance ($D[w] = D[v] + 1$) and insert $w$ into $F$.

**Example:**
Consider a simple graph: `A -> B, A -> C, B -> D, C -> D`. Starting at $S=A$:
- **Wave 0:** Queue contains `[A]`. Pop `A`, visit `B` and `C`.
- **Wave 1:** Queue contains `[B, C]`. Pop `B`, visit `D`. Pop `C`, see `D` is already visited.
- **Wave 2:** Queue contains `[D]`. Pop `D`, no neighbors. Done.

### Complexity Analysis
- **Work:** Each vertex is added to $F$ at most once. For a directed graph, each edge is visited at most once (twice for undirected). Thus, the total sequential cost (work) is **$\mathcal{O}(V + E)$**, where $V$ is the number of vertices and $E$ is the number of edges.

---

## 2. Limitations of Sequential BFS

Why can't we just run the sequential algorithm on a multi-core processor?

### The Sequential Bottleneck
**Mental Model: The Single Turnstile**
Imagine a stadium with 50,000 empty seats (cores) but only a single turnstile (the FIFO queue). Everyone must line up one by one. The standard BFS contains a strict dependency: the next vertex to be inserted into the queue $F$ depends on the vertex just extracted from $F$. This enforces a sequential `while` loop that executes $\mathcal{O}(V)$ times, making it impossible for multiple processors to effectively share the workload.

### The Sparsity Problem
In real-world applications (e.g., the Facebook friend graph, the World Wide Web), graphs are typically **sparse**. This means most nodes only connect to a tiny fraction of the total network, so the number of edges grows linearly with the vertices: $E = \mathcal{O}(V)$. 

- Because the span (the longest critical path of dependencies) of the sequential algorithm is $\mathcal{O}(V)$, the average available parallelism, defined as $\frac{\text{Work}}{\text{Span}}$, becomes $\frac{\mathcal{O}(V + E)}{\mathcal{O}(V)}$. 
- For sparse graphs, this ratio simplifies to a constant **$\mathcal{O}(1)$**. 

**Intuition:** An $\mathcal{O}(1)$ parallelism means that even if you had a supercomputer with 10,000 cores, the standard sequential algorithm offers almost **no available parallelism**. Only a few cores would be doing actual work, while the rest sit idle.

---

## 3. Parallel BFS: Intuition & High-Level Approach

To unlock parallelism, we exploit the "wavy" nature of BFS. 

**Mental Model: An Army of Explorers**
Instead of sending a single explorer who walks from node to node, we dispatch an entire army. At step 1, the army explores all 1-hop neighbors simultaneously. At step 2, a larger army explores all 2-hop neighbors simultaneously. 

### The Two Big Ideas
1. **Level-Synchronous Traversal:** Process the graph level by level (wave by wave) rather than vertex by vertex. The number of sequential steps is no longer bounded by the number of vertices ($V$), but by the graph's **diameter** (the maximum shortest distance between any pair of vertices). In many real-world graphs, the diameter is surprisingly small (e.g., 6 in a global social network).
2. **Process Entire Levels in Parallel:** All vertices at a given level $L$ are exactly the same distance from the source. Because of this, the order in which they are processed *does not matter*. This allows us to process all vertices in the current frontier simultaneously across many cores.

### High-Level Parallel Execution
Instead of a single queue, the algorithm maintains level-specific frontiers ($F_L$ and $F_{L+1}$). A function `process_level` takes the current frontier $F_L$, processes all its vertices in parallel, and generates the new frontier $F_{L+1}$.

---

## 4. The "Bag" Data Structure

If we process a level in parallel, thousands of threads might try to add new vertices to the next frontier $F_{L+1}$ at the exact same time. If they all try to write to a standard array or concurrent queue, the locking and synchronization overhead would destroy our performance gains. 

To implement the parallel frontier $F_L$ effectively, we need a data structure that supports massive parallelism. A **Bag** is a specialized container perfect for this role.

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
5. **Reducer Hyperobjects:** Vertices are inserted into the next frontier $F_{L+1}$ using logically associative bag unions backed by **reducer hyperobjects**. 
   - **Intuition:** A reducer gives each thread its own private, local Bag to toss vertices into, eliminating locks. When the threads finish their work, the system automatically merges (unions) their local Bags together into the final $F_{L+1}$ frontier in $\mathcal{O}(\log n)$ time.

### Complexity Analysis
- **Work:** The algorithm remains work-optimal at **$\mathcal{O}(V + E)$**. We haven't done any extra algorithmic work; we've just reorganized *how* it's done.
- **Span (Critical Path):** 
  - The outer loop executes $d$ times (where $d$ is the diameter of the graph).
  - The span of `process_level` is determined by the recursion depth ($\mathcal{O}(\log V)$), the cost of splitting a bag ($\mathcal{O}(\log V)$), and the $\mathcal{O}(1)$ base case.
  - Overall Span: **$\mathcal{O}(d \cdot \text{polylog}(V))$**. 

*(Note: "polylog(V)" simply means some polynomial of a logarithm, which grows incredibly slowly, meaning the span is kept extremely tight and parallelism is highly optimized.)*

### Conclusion
By substituting a strict FIFO queue with a highly parallelizable Bag data structure, and traversing the graph level-synchronously, the shared-memory parallel BFS successfully eliminates sequential bottlenecks. It maintains optimal total work while unlocking massive scalability for modern multi-core systems.
