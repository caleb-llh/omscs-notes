# Distributed Breadth-First Search (BFS) via Linear Algebra

**Background Context:**
Historically, graph algorithms and linear algebra were treated as two distinct worlds. Graph algorithms were implemented using pointer-based data structures (like adjacency lists), while linear algebra focused on dense or sparse matrices. However, as graphs grew to billions of edges (e.g., social networks, web graphs), pointer-based algorithms struggled to scale on distributed supercomputers. This document synthesizes notes on executing graph algorithms—specifically Breadth-First Search (BFS)—on distributed memory systems by recasting them as linear algebra operations. Leveraging established distributed matrix computation techniques allows for scalable graph processing, turning a complex graph traversal into well-understood math.

> **Fact Check:** The transition from pointer-based to matrix-based graph algorithms was formalized and accelerated by the GraphBLAS standard (C API published in 2017). Representing graphs as sparse matrices allows taking advantage of compressed sparse formats (like CSR or CSC), avoiding the heavy memory overhead of 64-bit pointers per edge in dynamic data structures.

> **Tradeoff:** **Pointer vs. Matrix representation.** Pointers are highly efficient for dynamic graphs where edges are constantly added or removed. Conversely, sparse matrices (like Compressed Sparse Row - CSR) are vastly superior for static graph traversals because they pack adjacency data into contiguous arrays, maximizing spatial locality and cache hits, but they are extremely expensive to mutate (adding an edge requires $\mathcal{O}(m)$ data movement).

> **Hypothetical:** What if we tried to use pointer-based BFS on a 100-billion edge graph? The memory access patterns would be incredibly random, leading to cache thrashing and terrible performance. Matrix operations offer structured, predictable memory access.

---

## 1. Graphs as Adjacency Matrices

> **Common Confusion:** Students often confuse the adjacency matrix with the incidence matrix. Remember: an adjacency matrix maps vertices to vertices (size $n \times n$), while an incidence matrix maps vertices to edges (size $n \times m$).

**Intuition:** 
Think of an adjacency matrix as a grid map showing who can talk to whom. If node $i$ can send a message to node $j$, we place a $1$ at the intersection of row $i$ and column $j$. 

When designing distributed graph algorithms, it is highly effective to represent graphs as adjacency matrices because matrices map perfectly onto the memory and processing grids of supercomputers.

### Undirected Graphs

> **Example:** If you and I are friends on a social network, the connection goes both ways. In the matrix, both $A_{\text{you, me}}$ and $A_{\text{me, you}}$ will be 1, ensuring symmetry.

* **Representation**: Given a graph $G$ with $n$ vertices and $m$ edges, give each vertex an integer label. Create an $n \times n$ matrix $A$.
* **Mapping**: If an edge exists between vertex $i$ and vertex $j$, set $A_{ij} = 1$ and $A_{ji} = 1$. Empty entries are assumed to be $0$ (no edge).
* **Properties**: The adjacency matrix of an undirected graph is **symmetric** ($A = A^T$). It contains $2m$ non-zero entries.
* **Example**: For a triangle graph with vertices 0, 1, and 2 connected to each other, the matrix $A$ has 1s everywhere except on the diagonal.

> **Fact Check:** An undirected graph's adjacency matrix has exactly $2m$ non-zero entries strictly if there are no self-loops. If a node connects to itself, it adds a single 1 on the diagonal, meaning the total non-zero count becomes $2m - (\text{number of self loops})$.

### Directed Graphs

> **Example:** Follower networks are directed. If I follow you, $A_{\text{me, you}} = 1$, but if you don't follow me back, $A_{\text{you, me}} = 0$.

* **Representation**: Vertices are arbitrarily numbered. If there is a directed edge from source vertex $i$ to destination vertex $j$, set $A_{ij} = 1$.
* **Properties**: The matrix is typically asymmetric.
  * **Empty Rows**: Correspond to vertices with no outgoing edges (sink vertices). *Mental Model: These are the "dead ends" of the graph.*
  * **Empty Columns**: Correspond to vertices with no incoming edges (source vertices). *Mental Model: These are the "starting points" that nobody points to.*
* **Converting Directed to Undirected**: Let $B$ be the boolean adjacency matrix of a directed graph (where $1$ is `True` and $0$ is `False`). The undirected boolean adjacency matrix can be computed as the logical `OR` of $B$ and its transpose $B^T$:
  $$A_{\text{undirected}} = B \lor B^T$$
  This retains both $ij$ and $ji$ edges, effectively removing directionality.

> **Fact Check:** Converting directed to undirected using $A_{\text{undirected}} = B \lor B^T$ is strictly correct for unweighted, boolean graphs. For weighted graphs, you must define an element-wise collision function (e.g., if $i \to j$ has weight 5 and $j \to i$ has weight 3, the undirected edge might take the `max`, `min`, or `sum`).

---

## 2. Matrix-Based Breadth-First Search

> **Background Context:** Traditional BFS uses a queue (FIFO) data structure. When we shift to matrix-based BFS, we are effectively processing the entire queue for the current depth level simultaneously as a single vector.

**Mental Model:**
Imagine BFS as a ripple in a pond. You throw a stone at the source vertex, and the wave expands outward one step at a time. The "frontier" is the leading edge of the wave. In linear algebra, multiplying our adjacency matrix by a vector representing the current frontier computes exactly where the wave will be in the next step.

### Level-Synchronous BFS Basics
* **Setup**: Given a graph $G$ and a source vertex $S$. The goal is to compute the minimum distance of every vertex from $S$.
* **Initialization**: The distance to $S$ is $0$; all other unvisited vertices have a distance of $\infty$.
* **Frontier**: At any given level $l$, the frontier consists of all unvisited vertices that are exactly distance $l$ away from the source.
* **Process**: For each level, visit all unvisited neighbors of the current frontier, update their distances to $l + 1$, and set them as the new frontier for level $l + 1$.
* **Sequential Cost**: The worst-case sequential running time is $\mathcal{O}(m + n)$, as every edge and node may be visited at least once.

> **Tradeoff:** **Level-Synchronous vs. Asynchronous BFS.** Level-synchronous BFS is simple to reason about and translates perfectly to matrix-vector math. However, it suffers from the "straggler problem"—processing for depth $l+1$ cannot begin until the slowest processor finishes depth $l$. Asynchronous BFS avoids synchronization barriers but is non-deterministic and notoriously difficult to implement as matrix operations.

### Algebraic Translation

> **Common Confusion:** Why do we use boolean logic ($\lor$ and $\land$) instead of regular arithmetic ($+$ and $\times$)? Because in BFS we only care *if* a node is reachable in $l$ steps, not *how many* different paths exist to reach it.

The level-synchronous BFS can be translated into a boolean matrix-vector product.
* **Update Logic**: Consider an unvisited vertex $i$ and the frontier at level $l$ represented as a boolean vector $f$ (where $f_k = 1$ if vertex $k$ is in the frontier). 
* An update to vertex $i$ is required if there is an edge from any frontier vertex $j$ to vertex $i$ ($A_{ji} = 1$). 
* Looking at column $i$ of the adjacency matrix $A$, we check if any frontier vertex points to $i$. This corresponds to computing an update vector $u$:
  $$u_i = \bigvee_j (A_{ji} \land f_j)$$
* **Matrix-Vector Product (The Semiring Magic)**: This scalar formula is equivalent to a boolean matrix-vector multiplication over a semiring where addition is replaced by logical `OR` ($\lor$) and multiplication is replaced by logical `AND` ($\land$). *Instead of calculating "how many" paths exist (standard math), we calculate "does any" path exist (boolean logic).*

> **Fact Check:** The boolean matrix-vector product operates over the Boolean Semiring, formally defined as $(\{0, 1\}, \lor, \land, 0, 1)$. Standard dense matrix multiplication over the normal arithmetic ring $(\mathbb{R}, +, \times, 0, 1)$ would calculate the *number* of paths of length $l$ to each node, taking $\mathcal{O}(n^2)$ work for a dense vector.

* **Sparsity & Work Optimality**: For a sparse graph, most matrix entries are $0$. By representing both the adjacency matrix $A$ and the frontier vector $f$ with sparse data structures, the operation becomes a **sparse matrix-vector multiply (SpMV)**. This prevents the computational cost from blowing up to $\mathcal{O}(n^2)$ and yields a work-optimal implementation proportional to the number of vertices and edges actually processed.
* **Distance Update**: Once $u$ is computed, we filter out vertices that have already been visited (using a mask). The remaining vertices in $u$ get their distances updated and form the next level's frontier.

> **Mental Model:** **Masking in SpMV.** Think of the "already visited" mask as a physical stencil placed over the output vector $u$. Before we commit the newly discovered vertices to memory, we apply this stencil. Any "new" vertex that falls under a cut-out (meaning we visited it in a previous level) is filtered out. In GraphBLAS, this is heavily optimized and known as "masked assignment," allowing the SpMV to short-circuit and skip computing values that will just be masked out anyway.

---

## 3. Distributed Implementations of BFS

When graphs are too massive to fit in the RAM of a single machine, we must distribute the matrix across a cluster of computers. By framing BFS as a matrix-vector product, we can directly apply decades of distributed matrix partitioning strategies.

### 1D Distributed BFS

> **Tradeoff:** 1D partitioning is simpler to implement and works well for small clusters, but its $\mathcal{O}(P)$ communication cost makes it fundamentally unscalable for massive supercomputers with tens of thousands of nodes.

**Intuition:** Imagine slicing a loaf of bread. We cut the adjacency matrix into vertical slices (columns) and give one slice to each computer.

* **Partitioning**: The adjacency matrix $A$ is partitioned using a 1D column distribution across $P$ processes. For example, columns (and corresponding vertices) $0, 1, 2$ go to Process 0; $3, 4, 5$ go to Process 1, etc. *This means a process is responsible for knowing all the incoming edges for its assigned vertices.*
* **Vector Distribution**: The update vector $u$ is implicitly partitioned in the same way as the vertices.
* **Frontier Replication**: Because each process holds a subset of columns (incoming edges to its vertices), to know if *any* frontier vertex points to its vertices, it needs to see the *entire* frontier. Thus, the local matrix-vector product requires the entire frontier vector $f$ to be replicated across all processes.
* **Algorithm Steps**:
  1. **Partition**: Divide matrix columns and update vector entries across processes.
  2. **Compute**: Perform local sparse matrix-vector products to determine potential updates.
  3. **Update**: Update distances for local unvisited vertices.
  4. **Form Local Frontier**: Determine which local vertices belong to the next frontier.
  5. **Communicate**: Perform an **All-to-All** exchange so every process obtains the complete, global frontier for the next iteration.
* **Communication Cost**: The All-to-All communication step scales linearly with the number of processes: $\mathcal{O}(P)$. As you add more machines, everyone talks to everyone, which creates a massive traffic jam on the network.

> **Fact Check:** In MPI (Message Passing Interface) terminology, the communication step described in 1D BFS is actually an `MPI_Allgather` (or `MPI_Allgatherv`), not a true `MPI_Alltoall`. Every processor broadcasts its local slice of the new frontier to everyone else, resulting in all processors having the complete global frontier. The number of messages scales as $\mathcal{O}(P)$, leading to severe latency bottlenecks at scale.

### 2D Distributed BFS

> **Hypothetical:** If we have 10,000 processors ($P=10000$), a 1D scheme requires each processor to talk to 9,999 others. In a 2D grid ($\sqrt{P} = 100$), each processor only talks to its 100 row-mates and 100 column-mates, reducing communication partners by a factor of 50.

**Intuition:** Instead of slicing the bread only vertically, we slice it vertically and horizontally into a grid (like a checkerboard). This prevents the need for everyone to talk to everyone.

* **Scaling Issue**: The $\mathcal{O}(P)$ communication cost of the 1D scheme becomes a bottleneck as the number of processes grows.
* **Partitioning**: Switch to a 2D partitioning scheme where processes are arranged in a $\sqrt{P} \times \sqrt{P}$ grid. The matrix $A$ is split into checkerboard tiles.
* **Communication Cost**: By utilizing multidimensional process grids, collective communications (like broadcasting the frontier and merging frontier updates) are restricted to process rows and columns rather than a global All-to-All. *Mental Model: You only need to communicate with your row-mates and column-mates, not the whole class.*

> **Tradeoff:** **1D vs 2D Partitioning Complexity.** 1D partitioning only divides the vertices, which requires replicating the entire frontier vector. 2D partitioning divides both the vertices *and* the edges, bounding frontier replication to just a processor's row and column. The tradeoff is code complexity: 2D requires a multi-phase communication step (e.g., a row-wise broadcast followed by a column-wise reduction) and complex local-to-global index mapping, whereas 1D uses a single straightforward gather operation.

* **Improvement**: This reduces the communication cost scaling from $\mathcal{O}(P)$ down to $\mathcal{O}(\sqrt{P})$, making it significantly more scalable for massive graphs on supercomputers.

> **Fact Check:** The reduction of communication cost from $\mathcal{O}(P)$ to $\mathcal{O}(\sqrt{P})$ is a proven property of Cartesian grid communicators. In a $\sqrt{P} \times \sqrt{P}$ grid, a processor only participates in row and column collectives of size $\sqrt{P}$. This 2D approach is fundamentally equivalent to SUMMA (Scalable Universal Matrix Multiplication Algorithm), heavily used in high-performance computing.

---

## 4. Conclusion and Extensions

> **Mental Model:** Think of GraphBLAS as the "BLAS (Basic Linear Algebra Subprograms)" but for graphs. Just as BLAS standardized matrix math for scientific computing, GraphBLAS standardizes graph analytics.

Recasting BFS in matrix terms is a powerful paradigm because it allows graph algorithms to inherit highly optimized, distributed linear algebra techniques. This intersection has given rise to modern frameworks like **GraphBLAS**, which formalize graph operations as linear algebra.

This approach inspires further questions: can other graph computations be similarly mapped to matrix operations? Examples for further exploration include:
* **Depth-First Search (DFS)**: Harder to parallelize via matrices due to its inherently sequential nature, but variations exist.
* **All-Pairs Shortest Paths**: E.g., Floyd-Warshall via Min-Plus matrix multiplication (tropical semiring, where addition becomes `min` and multiplication becomes `+`).
* **Triangle Counting**: Can be computed efficiently by analyzing the trace of $A^3$ or using masked matrix multiplications.
* **Betweenness Centrality**: Built upon multiple BFS traversals and can heavily leverage sparse matrix multiplications.

> **Mental Model:** **Tropical Semiring for Shortest Paths.** Imagine a universe where addition means "find the shortest distance" ($\min$) and multiplication means "walk along a path" ($+$). If you multiply a matrix by itself in this universe, you are computing: "To get from $i$ to $j$, consider all intermediate stops $k$. Find the minimum ($\min$) of the distance $i \to k$ plus ($+$) the distance $k \to j$." This is exactly how the tropical semiring computes shortest paths elegantly!

> **Fact Check:** The assertion that Triangle Counting uses the trace of $A^3$ is a classic theorem in algebraic graph theory. The trace of $A^3$ gives exactly 6 times the number of triangles in an undirected graph, because each triangle is counted from each of its 3 vertices, in 2 different directions ($3 \times 2 = 6$).
