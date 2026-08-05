# Distributed Dense Matrix Multiply

## 1. Introduction & Basic Definitions

### Background Context
Matrix multiplication is the workhorse of modern computing. From training massive deep learning models (like transformers) to solving complex systems in scientific simulations, multiplying large matrices efficiently is critical. Because these matrices often exceed the memory or computational capacity of a single machine, we must distribute the work across multiple nodes in a cluster. 

### The Core Operation
- **Matrix Multiply Operation:** Given matrices $A$ ($m \times k$) and $B$ ($k \times n$), update $C$ ($m \times n$) via $C \leftarrow A \times B + C$.
- **Scalar Update Formula:** $C_{ij} \leftarrow C_{ij} + \sum_{l} A_{il} B_{lj}$. 
  - *Intuition:* This is a standard dot product. To find the value for the $i$-th row and $j$-th column in $C$, you take the $i$-th row of $A$ and "sweep" it across the $j$-th column of $B$.
- **Sequential Complexity:** For square matrices ($n \times n$), the standard three-nested-loop algorithm takes $O(n^3)$ time (flops, or floating-point operations). 

### Parallelism (PRAM Model)
The PRAM (Parallel Random Access Machine) model gives us a theoretical baseline for how parallelizable this task is:
- **Independent Outputs:** All output elements $C_{ij}$ are completely independent of one another. 
  - *Mental Model:* Imagine a giant grid of workers, where each worker is responsible for computing exactly one cell of $C$. No worker needs to talk to any other worker to get their job done. Thus, the outer loops can be fully parallelized.
- **Reduction:** The innermost loop (the sum over $l$) computes independent element-wise products followed by a sum reduction.
- **Complexity:** Total work is $O(n^3)$ and the span (the longest critical path) is $O(\log n)$, assuming we use a binary tree reduction to sum the $n$ elements in $O(\log n)$ steps.

### Block Matrix Multiply
- **Concept:** The computation is mathematically identical if scalar elements are replaced by submatrices (blocks). A block of $C$ is updated by multiplying a block-row of $A$ with a block-column of $B$.
  - *Example:* If $A, B, C$ are $4 \times 4$ matrices, we can treat them as $2 \times 2$ grids where each "element" is a $2 \times 2$ matrix. The algebraic rules remain exactly the same. This is crucial for distributed systems because sending large blocks of data is far more efficient than sending individual numbers.

---

## 2. A Geometrical View (Loomis-Whitney)

To understand the absolute limits of how efficiently we can distribute this work, it helps to visualize matrix multiplication geometrically.

- **Cuboid Representation:** 
  - *Mental Model:* Imagine matrix multiplication as a 3D cuboid (or box) of dimensions $m \times n \times k$. The three faces of this cuboid correspond to the matrices $A$, $B$, and $C$. The edges match the matrix dimensions.
- **Geometric Intersection:** An output element $C_{ij}$ depends on a row from $A$ and a column from $B$. In our 3D space, these project as intersecting lines through the cube. A single scalar multiplication $A_{il} \times B_{lj}$ is a specific point $(i, j, l)$ in the interior of this 3D space.
- **Loomis-Whitney Theorem (1949):** A beautiful theorem from geometry bounds the volume of a 3D shape based on its 2D projections. 
  - For any subset of surfaces $S_A$, $S_B$, and $S_C$ (representing the data we hold in memory), the volume of their interior intersection $I$ (representing the number of multiplications we can perform with that data) is bounded by:
    $$|I| \le \sqrt{|S_A| \times |S_B| \times |S_C|}$$
  - *Intuition:* You can only do so much "work" (volume) with a limited amount of "data" (surface area). This directly bounds the maximum compute we can squeeze out of data residing in a node's local memory before we are forced to fetch more data from the network!
  - *Example:* Given a $3 \times 5$ block of $A$ ($|S_A|=15$), a $5 \times 4$ block of $B$ ($|S_B|=20$), and a $2 \times 2$ block of $C$ ($|S_C|=4$), the maximum possible multiplies you could do is $\lfloor\sqrt{15 \times 20 \times 4}\rfloor = \lfloor\sqrt{1200}\rfloor = 34$. (The minimum is 0, if the indices of these blocks don't align at all).

---

## 3. 1D Distributed Algorithm (Block Row)

Let's design our first distributed algorithm.

- **Data Distribution:** Matrices $A$, $B$, and $C$ (all $n \times n$) are distributed across $P$ nodes on a linear network. Each node gets a block row ($n/P$ consecutive rows) of each matrix.
- **Algorithm Strategy:**
  - *Mental Model:* A circular conveyor belt. 
  1. Keep $A$ and $C$ in place (nailed down to the node).
  2. Perform $P$ circular shifts of $B$'s block rows across the network.
  3. In each round, a node multiplies its local $A$ block with the $B$ block currently on its "conveyor belt station", accumulating the result into its local $C$.
- **Cost Analysis:**
  - **Computation:** $2\tau \frac{n^3}{P}$ flops ($\tau = \text{time per flop}$).
  - **Communication:** $P$ shifts of blocks of size $\frac{n^2}{P}$ yields an overall cost of $\alpha P + \beta n^2$, where $\alpha$ is latency and $\beta$ is the inverse bandwidth.
- **Optimization (Overlap):** We can hide the network delay. Overlapping the communication (sending/receiving the next block of $B$) with the local matrix multiply yields a runtime of $\max(\text{computation}, \text{communication})$. This can provide up to a 2x speedup.
- **Efficiency & Scalability:**
  - **Parallel Efficiency ($E$):** Defined as Speedup divided by $P$.
  - **Isoefficiency Function:** For efficiency to remain constant as we add more nodes ($P$), the problem size must grow as $n = \Omega(P)$.
  - **Drawback:** Scaling $P$ requires increasing $n$ linearly. If $P$ doubles, $n$ must double. But if $n$ doubles, the memory required per node quadruples ($n^2/P$), and the total flops increase by $8\times$. This leads to severe diminishing returns. 1D algorithms scale poorly!
- **Memory Requirements:** Storing local $A, B, C$ and a temporary receive buffer $\tilde{B}$ requires $4 \frac{n^2}{P}$ space.

### Sidebar: Isoefficiency of Tree-based All-to-One Reduction
- For a tree-based all-to-one vector reduction on a linear network, the parallel efficiency tends to zero as $P$ increases.
- There is no valid isoefficiency function $n(P)$ that keeps efficiency constant, because a latency term grows independently of $n$. A pipelined or bucketing scheme is needed to fix this.

---

## 4. 2D Distributed Algorithm (SUMMA)

To solve the scaling issues of the 1D approach, we move to a 2D grid.

- **Data Distribution:** Matrices are mapped to a 2D mesh/torus process grid ($\sqrt{P} \times \sqrt{P}$). 
  - *Context:* Instead of rows, each node gets a square "tile" of the matrices. This reduces the perimeter-to-area ratio of the data, saving network bandwidth.
- **SUMMA (Scalable Universal Matrix Multiply Algorithm):**
  - Iterates over vertical strips of $A$ and horizontal strips of $B$. Let the strip width/height be $s$ (a tuning parameter).
  - *Mental Model:* Think of a marching band passing information down the rows and columns. In each step, the owner of the current strip broadcasts it along its block row (for $A$) and block column (for $B$).
  - Once received, all nodes perform a local update on their block of $C$.
- **Cost Analysis:**
  - **Computation:** $2\tau \frac{n^3}{P}$ flops (perfectly balanced).
  - **Communication:** Broadcasts of strips of size $\frac{n}{s} \times \frac{n}{\sqrt{P}} \times s = \frac{n^2}{\sqrt{P}}$ per node overall.
    - *Tree-based broadcast:* $\sim \alpha \log P + \beta \log P \frac{n^2}{\sqrt{P}}$
    - *Bucket-based broadcast:* $\sim \alpha P + \beta \frac{n^2}{\sqrt{P}}$
- **Efficiency & Scalability:**
  - SUMMA's isoefficiency function is asymptotically lower than the 1D algorithm's. This means we don't need to increase the matrix size nearly as fast to maintain efficiency when adding nodes, making it intrinsically more scalable.
- **Memory Requirements:**
  - Base storage ($A, B, C$): $3 \frac{n^2}{P}$.
  - Buffers for broadcast strips: $2 \times s \frac{n}{\sqrt{P}}$.
  - The strip width $s \in [1, \frac{n}{\sqrt{P}}]$ controls the trade-off between latency, bandwidth, and memory. Total memory ranges from $< 4 \frac{n^2}{P}$ (smaller $s$) to $5 \frac{n^2}{P}$ (maximum $s$).

---

## 5. Theoretical Lower Bounds on Communication

How do we know if SUMMA is the best we can do? We can prove it mathematically.

- **Assumptions:** A machine with $P$ nodes, where each node holds $M = \Theta(\frac{n^2}{P})$ words of memory and performs $W = \frac{n^3}{P}$ multiplies.
- **Analysis via Phases:**
  - *Intuition:* Let's chunk time into phases. In each phase, a node completely fills its memory with new data from the network.
  - Divide execution into phases where exactly $M$ words are sent/received.
  - By the Loomis-Whitney theorem (our geometric volume bound), the maximum multiplies per phase is bounded by $2\sqrt{2} M^{3/2}$.
  - Therefore, the number of full phases is at least $L \ge \frac{W}{2\sqrt{2} M^{3/2}}$.
  - Total words communicated per node $\ge L \times M = \Omega(\frac{W}{\sqrt{M}})$.
- **2D Lower Bound Results:**
  - **Bandwidth (Volume):** Substituting $W = n^3/P$ and $M = n^2/P$ gives a lower bound of $\Omega(\frac{n^2}{\sqrt{P}})$ words.
  - **Latency (Messages):** Total volume divided by max message size $M$ gives $\Omega(\sqrt{P})$ messages.
  - **Total Communication Lower Bound:** $\alpha \sqrt{P} + \beta \frac{n^2}{\sqrt{P}}$.
- **Algorithm Comparison:**
  - **SUMMA:** Matches the $\beta$ (bandwidth) lower bound perfectly (using bucket broadcast), though slightly off on the $\alpha$ (latency) bound. It is a highly practical, near-optimal algorithm.
  - **Cannon's Algorithm (1969):** Exactly matches both lower bounds! However, it is less practical to implement in the real world due to strict, rigid data layout requirements.

---

## 6. 3D and 2.5D Algorithms (Beating the 2D Lower Bound)

What if we want to communicate even less? The 2D bounds assume we are memory-constrained. If we have extra memory, we can trade it to save network bandwidth.

- **Breaking the Memory Assumption:** The 2D lower bounds strictly assume $O(\frac{n^2}{P})$ memory per node (just enough to hold the matrices). Adding memory to replicate data can bypass this bound and reduce communication.
  - *Mental Model:* "Memory is cheap, network is slow." If multiple nodes hold the exact same data, they don't need to ask each other for it over the network.
- **3D Algorithm (Full Replication):**
  - Distribute the 3D computation volume directly: arrange $P$ nodes in a 3D mesh of $P^{1/3} \times P^{1/3} \times P^{1/3}$.
  - Replicate the matrices $P^{1/3}$ times across the network.
  - Perform local multiplications and combine results with a reduction.
  - **Result:** Communication volume decreases significantly by a factor of $P^{1/3}$, scaling as $O(\frac{n^2}{P^{2/3}})$. The network traffic drops, but memory usage spikes!
- **2.5D Algorithm (Partial Replication):**
  - A sweet spot. It uses partial replication to flexibly trade off between memory capacity and communication volume, bridging the gap smoothly between 2D (minimal memory) and 3D (minimal communication) algorithms.

---

## 7. Conclusion

- **A Proving Ground:** Matrix multiply is a vital computational primitive. More importantly, it serves as an excellent, perfectly clean model for studying distributed algorithm analysis (1D, 2D, 3D distributions, and communication lower bounds). If you understand distributed matrix multiplication, you understand the foundations of high-performance computing.
- **The LINPACK Illusion:** As problem sizes grow, computation ($O(n^3)$) scales much faster than communication ($O(n^2)$). This means for gigantic matrices, communication becomes a tiny fraction of the runtime, allowing matrix multiply to achieve near-peak hardware capability on large systems (e.g., the LINPACK benchmark used to rank the TOP500 supercomputers). 
- **The Caveat:** Because it scales so perfectly, LINPACK may not accurately reflect how a supercomputer will perform on more communication-intensive, "messy" real-world applications (like graph processing or sparse solvers) where communication is the true bottleneck.
