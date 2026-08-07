# Graph Partitioning

## 1. Introduction & Motivation

### 1.1 Why Graph Partitioning?
Graph partitioning is one of the most interesting and crucial topics in parallel computing. It serves as the core mechanism for distributing data in distributed memory algorithms. 

**Mental Model:** Imagine you are managing a massive group project with 1,000 students (vertices) who need to collaborate based on specific friendships (edges). If you split them into 4 separate rooms (processors), you want to ensure two things:
1. Every room has roughly the same number of students, so no one supervisor is overwhelmed.
2. Friends are mostly placed in the same room, so they don't have to constantly run down the hallway (network communication) to talk to each other.

For example, in a distributed Breadth-First Search (BFS) or when rendering a huge 3D mesh in a physics simulation, you need a way to choose an initial partitioning of the input graph to balance the workload across processors and minimize cross-process communication.

### 1.2 Sparse Matrix-Vector Multiplication (SpMV)
The graph partitioning problem can be motivated by a very common linear algebra operation: multiplying a sparse matrix $A$ by a vector $x$ ($y = Ax$).

- **Graph Duality:** There is a beautiful duality between sparse matrices and graphs. The rows and columns of the matrix represent the vertices of a graph, and the non-zero entries represent the edges connecting them. 
  - *Example:* If $A_{i,j}$ is non-zero, it means vertex $i$ is connected to vertex $j$.
- **Distributing Work:** If you divide the matrix row-wise to distribute work across different parallel processes, this assignment corresponds directly to a **vertex partition** of the underlying graph. 
  - Because the entries in the vector map 1-to-1 to the graph's vertices, partitioning the matrix rows also implicitly partitions the input vector $x$ and the output vector $y$.
- **Goals for Partitioning:**
  1. **Load Balance:** The amount of work a processor does in SpMV is proportional to the number of non-zeros in its assigned rows. Thus, partitions should balance the number of matrix non-zeros (which correspond to edges) per process.
  2. **Minimize Communication:** To update a block of the output vector $y$, a process needs the corresponding elements of the input vector $x$. If those required $x$ elements belong to a different process (i.e., an edge crosses a partition boundary), the processors must communicate over the network. Therefore, we want to minimize the number of **edge cuts** (edges that span across different partitions).

### 1.3 The Graph Partitioning Problem
Formally, given an input graph and a target number of partitions $P$, the goal is to divide the vertices into $P$ partitions with the following properties:
1. **Complete & Disjoint:** The partitions cover all vertices, and no vertex belongs to more than one partition.
2. **Balanced:** The partitions are approximately equal in size.
3. **Minimum Cut:** The number of cut edges (edges connecting vertices in different partitions) is minimized.

*Note:* Standard graph partitioning algorithms typically balance the number of *vertices*, but SpMV requires balancing the *work* (non-zeros/edges). Perfect load balancing for work requires augmenting the problem (e.g., using vertex weights to represent the number of non-zeros) since simply balancing vertices doesn't automatically balance edges. 

Graph partitioning is an **NP-complete** problem. Because we cannot find a perfect solution in polynomial time for large graphs, we rely heavily on clever heuristics and exploiting the structural properties of the graph.

---

## 2. Basic Heuristics and Separators

### 2.1 Graph Bisection
A simple heuristic based on the classic **divide-and-conquer** principle. 
**Intuition:** Think of cutting a cake for 8 people. Instead of trying to cut 8 perfect slices at once, it's much easier to cut the cake in half (bisection), then cut those halves in half, and so on.
To divide a graph into $P$ partitions, first use an algorithm to divide the graph into two partitions (bisection). Then, recursively divide each resulting half until the desired number of partitions is obtained.

### 2.2 Planar Separators
- **Planar Graph:** A graph that can be drawn on a flat 2D plane with absolutely no edge crossings. A classic example is a grid or lattice graph, often used in finite difference simulations (like modeling heat distribution on a metal plate).
- **Lipton-Tarjan Theorem:** This theorem provides a powerful guarantee for planar graphs. For a planar graph with $n$ vertices, the vertices can be partitioned into 3 disjoint sets $A$, $B$, and $S$ such that:
  1. $S$ is a **separator** between $A$ and $B$ (meaning no edges directly connect $A$ and $B$; to get from $A$ to $B$, you *must* pass through $S$).
  2. Subsets $A$ and $B$ have at most $\frac{2}{3}n$ vertices each. This guarantees a relatively balanced partition (the larger partition is no more than twice the size of the smaller).
  3. The size of the vertex separator $S$ is roughly $O(\sqrt{n})$. This means the boundary between the partitions is small relative to the total volume, ensuring low communication!

### 2.3 Partitioning via Breadth-First Search (BFS)
- **Algorithm:** Pick a starting vertex and run a level-synchronous BFS. Every level of the BFS tree serves as a potential separator. Stop the BFS after visiting roughly half of the total vertices. Assign all visited vertices to one partition, and all unvisited vertices to the other.
- **Intuition:** Imagine dropping a stone into a pond. The ripples spread outward concentrically. By grabbing the water inside a specific ripple, you grab a naturally contiguous chunk of the graph.
- **Pros:** BFS-based schemes are computationally very cheap and tend to work reasonably well on planar or grid-like graphs.
- **Cons:** It's somewhat "recursively perverse." If your ultimate goal is to partition a graph so that you can run a distributed BFS efficiently, using a BFS to do the partitioning in the first place is a bit of a chicken-and-egg problem.

---

## 3. Kernighan-Lin (KL) Algorithm
The KL algorithm (where the 'g' in Kernighan is silent, like "gnu") is a classic, greedy heuristic for **partition refinement**. It doesn't create a partition from scratch; instead, it takes a mediocre partition and makes it better.

**Mental Model:** Imagine two rival sports teams, Team 1 and Team 2, of equal size. Players on both teams are friends with various other players. The goal is to trade players between the teams to minimize the number of cross-team friendships (which cause drama), while keeping the team sizes exactly the same.

### 3.1 Setup and Definitions
Start by dividing the vertices into two subsets ($V_1$ and $V_2$) of equal or nearly equal size. *Any arbitrary split will do* (even a random one). The goal is to swap subsets $X_1 \subset V_1$ and $X_2 \subset V_2$ to improve the overall cut cost.
- **External Cost ($E_a$):** The number of edges from vertex $a$ to vertices in the *other* partition (cross-team friendships).
- **Internal Cost ($I_a$):** The number of edges from vertex $a$ to other vertices in its *same* partition (intra-team friendships).
- **Gain ($g_{ab}$):** The change in cost (reduction in cut edges) if vertices $a$ and $b$ are swapped.
  - **Formula:** $g_{ab} = E_a - I_a + E_b - I_b - 2c_{ab}$
  - Here, $c_{ab} = 1$ if there is a direct edge between $a$ and $b$, and $0$ otherwise. (We subtract $2c_{ab}$ because if they are connected, swapping them means their shared edge flips from being an external cut to an internal edge, double-counting the benefit if we just added their individual gains).
  - Computing the gain takes $O(d)$ time, where $d$ is the maximum degree of any vertex.

### 3.2 The KL Procedure
1. Compute internal and external costs for every vertex. Mark all nodes as "unvisited" (meaning they haven't been traded yet).
2. **Iterative Step:** Go through every pair of unmarked vertices (one from $V_1$, one from $V_2$) and pick the pair $(a, b)$ that yields the largest gain $g_{ab}$. 
3. Mark the pair as visited. **Crucial detail:** Do not actually finalize the swap yet! Just tentatively update all internal and external costs of their neighbors as if they had been swapped.
4. Repeat this pairing and tentative swapping until all vertices have been visited (traded exactly once). This produces a sequence of individual gains.
5. Compute the **Cumulative Gain ($G$)**, which is the sum of the individual gains up to a certain point $j$ in the sequence.
   - *Why do this?* Sometimes, making a "bad" swap (negative gain) temporarily unlocks a series of amazing swaps later. By tracking the cumulative gain, KL can climb out of local minima—similar to simulated annealing!
6. Find the point $j$ in the sequence that maximizes the cumulative gain. If this maximum cumulative gain is positive, officially perform the actual swaps of the subsets $X_1$ and $X_2$ up to point $j$, and update the overall graph cost.
7. Repeat the entire procedure (Steps 1-6) until there is no more positive cumulative gain (i.e., the algorithm converges and no sequence of swaps improves the cut).

**Complexity:** The naive sequential running time is $O(|V|^2 \cdot d)$. However, more complex variations (like the Fiduccia-Mattheyses algorithm) use clever data structures to reduce the per-iteration cost to $O(|E|)$.

---

## 4. Multi-level Graph Coarsening
When graphs get massively large (millions of vertices), algorithms like KL become too slow. Multi-level coarsening is a powerful divide-and-conquer strategy that repeatedly shrinks the graph, partitions the tiny version, and then projects the result back up.

**Mental Model:** Think of Google Maps. If you want to draw a border separating the Eastern and Western US, you don't look at every single street level (fine graph). You zoom all the way out until you only see states (coarse graph), draw the line there, and then zoom back in to refine the exact border along rivers and highways.

### 4.1 Coarsening Process
1. **Merge Vertices:** Identify subsets of connected vertices and collapse them into a single "super vertex."
2. **Track Weights:** To ensure the coarsened graph accurately represents the original graph:
   - *Vertex Weights:* Sum the weights of the merged vertices. This helps track load balancing (e.g., if 5 original vertices are merged into 1 super vertex, that super vertex gets a weight of 5).
   - *Edge Weights:* Sum the weights of the merged edges. This allows the algorithm to accurately track cut costs in the coarsened graph.
3. Repeat the coarsening process until the graph is small enough to partition quickly (e.g., a few hundred nodes).
4. Partition the smallest coarse graph (using an algorithm like KL or Spectral Partitioning).
5. Project the partition back to the finer graphs, step by step, "un-merging" the super vertices.

### 4.2 Maximal Matchings
To decide exactly *which* vertices to merge together during coarsening, we compute a matching.
- **Matching:** A subset of edges such that no two edges share a common endpoint. In other words, a set of independent pairs of vertices.
- **Maximal Matching:** A matching to which no more edges can be added. (Distinct from a *maximum* matching, which is the absolute largest possible matching in the whole graph).
- **Coarsening Bound:** Using maximal matchings to coarsen a graph of $n$ vertices down to $s$ vertices requires at least $\Omega(\log(n/s))$ coarsening steps, guaranteeing that the graph shrinks efficiently.

### 4.3 Heavy Edge Matching Strategy
A randomized algorithm can compute a maximal matching, but purely random matching isn't ideal. At each step, we pick an unmatched vertex.
- **Heavy Edge Heuristic:** Instead of matching the vertex to a random unmatched neighbor, match it to the neighbor connected by the edge with the *highest weight*.
- **Intuition:** Remember, our goal is to minimize the cut edges. If two vertices share a very heavy edge (meaning they communicate a lot), merging them absorbs that heavy edge into a super vertex. Because edges hidden inside super vertices can never be cut by the partition, this guarantees the heavy edge is protected. This strategy leaves only the "lightest" edges exposed to potentially being cut.

### 4.4 Partition Refinement
Because coarsening relies on heuristics (like heavy edge matching), the projected partition on the fine graph might be slightly sub-optimal, even if it was perfectly optimal on the coarse graph. Therefore, the partition must be refined (typically by running a fast pass of the KL algorithm) at each step during the uncoarsening phase to clean up the boundaries.

---

## 5. Spectral Partitioning
Spectral partitioning approaches the problem from a completely different angle: using the deep mathematical connections between graphs and linear algebra, complete with a fascinating physics-based interpretation.

### 5.1 The Graph Laplacian
To use linear algebra on a graph, we must represent it as a matrix.
- **Incidence Matrix ($C$):** For a directed graph, each row represents an edge and each column represents a vertex. For an edge $e = (i, j)$, put $+1$ at the source vertex $i$ and $-1$ at the sink vertex $j$.
- **Graph Laplacian ($L$):** Defined elegantly as $L = C^T C$. 
  - Alternatively, and more commonly calculated as: $L = D - W$ (or $D - A$).
  - **$D$:** A diagonal matrix containing the degrees (number of connections) of each vertex.
  - **$W$ (or $A$):** The adjacency matrix of the undirected graph (1 if an edge exists, 0 otherwise).
- **Properties of the Laplacian:**
  1. $L$ is symmetric.
  2. The rows and columns each sum exactly to $0$.
  3. The eigenvalues are real-valued and non-negative ($\lambda_0 \le \lambda_1 \le \dots \le \lambda_{n-1}$).
  4. The eigenvectors are real-valued and orthogonal.
  5. **Fiedler's Fact:** A graph has exactly $K$ connected components if and only if the $K$ smallest eigenvalues are exactly zero. (If the graph is fully connected, only $\lambda_0 = 0$).

### 5.2 Physics Interpretation (Springs Fling)
**Mental Model:** Imagine the vertices of the graph as physical weights of equal mass. These weights are attached to fixed infinite sticks (so they can only slide up and down in one dimension), and they are connected to their graph neighbors by elastic springs.
- Hooke's Law and Newton's laws dictate the physical motion of these weights.
- The net force acting on a given mass is proportional to the displacements of its neighbors (if a neighbor is pulled far away, the spring pulls harder).
- Astonishingly, the entire system of differential equations describing this physical motion takes the exact form of the Graph Laplacian!
- The fundamental modes of motion (the natural, harmonic "wobbling" frequencies of the spring system) correspond exactly to the **eigenvectors** of the Graph Laplacian.

### 5.3 Algebraic Connectivity & Minimizing Cuts
- **Partition Vector ($x$):** Let $x$ be a mathematical vector where $x_i = +1$ if vertex $i$ is placed in partition $V^+$, and $x_i = -1$ if vertex $i$ is in partition $V^-$.
- **Edge Cut Counting:** The total number of cut edges can be algebraically computed using the quadratic form: $\frac{1}{4} x^T L x$.
- **Optimization Problem:** We want to find a partition vector $x$ that minimizes $\frac{1}{4} x^T L x$. We have two constraints:
  1. $x_i \in \{+1, -1\}$ (every node must be in exactly one partition).
  2. $\sum x_i = 0$ (there must be an equal number of $+1$s and $-1$s, ensuring perfect balance).
- This combinatorial optimization problem is unfortunately NP-complete.

### 5.4 The Spectral Partitioning Algorithm
To bypass the NP-completeness of the discrete math, we use a trick: we "relax" the problem into continuous math.
- **Relaxation:** Instead of forcing $x$ to be strictly $+1$ or $-1$, allow $x$ to be any continuous vector $y$, provided it is normalized (length of 1) and its elements sum to $0$.
- **Courant-Fisher Minimax Theorem:** Linear algebra tells us that the continuous vector $y$ that minimizes this relaxed quantity is exactly **$q_1$**, the eigenvector corresponding to the second smallest eigenvalue ($\lambda_1$). 
  - This eigenvector $q_1$ is famously known as the **Fiedler vector**.
  - The value $\lambda_1$ is called the *algebraic connectivity* of the graph. A smaller $\lambda_1$ means the graph is easier to cut in half.
- **Algorithm:**
  1. Compute the Graph Laplacian $L = D - A$ of the graph.
  2. Compute its second smallest eigenpair ($\lambda_1, q_1$) using a numerical solver.
  3. Determine the discrete partition by simply looking at the signs of the components of the continuous Fiedler vector $q_1$:
     - If $q_{1, i} > 0$, assign vertex $i$ to partition 1.
     - If $q_{1, i} \le 0$, assign vertex $i$ to partition 2.
- **Conclusion:** Spectral partitioning works exceptionally well (especially for planar graphs and scientific meshes) because it considers the global structure of the graph. However, computing eigenvectors is computationally expensive. It is typically used when the upfront cost of partitioning is justified by the massive efficiency gains in subsequent, repeated operations (like running SpMV thousands of times in an iterative solver).