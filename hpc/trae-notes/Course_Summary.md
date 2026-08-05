# High Performance Computing: Course Overview

## Introduction
For decades, algorithm design was dominated by the RAM (Random Access Machine) model—a mathematically beautiful abstraction that assumes fetching any piece of data takes exactly $O(1)$ time, and a single processor executes instructions sequentially. However, the physical realities of modern hardware have shattered this illusion. The breakdown of Dennard Scaling (the "Power Wall") forced the industry into multicore parallelism, while the growing disparity between CPU speeds and memory latency (the "Memory Wall") made data movement the true bottleneck of computing.

This course explores **High Performance Computing (HPC)** by explicitly stepping beyond the RAM model. It provides the theoretical and practical foundations to design algorithms that scale across thousands of cores, minimize expensive data movement, and exploit the physical architecture of supercomputers. By the end of this course, you will understand how to fundamentally rethink classical algorithms to survive and thrive in parallel, cache-bound, and distributed-memory environments.

---

## Core Themes and Conceptual Framework

### 1. The Physics of Computing and the Work-Span Model
Before writing parallel code, we must understand how to measure it. The course begins by replacing standard time complexity with the **Work-Span Model**. If an algorithm is a dependency graph (DAG), "Work" ($W$) is the total number of operations, and "Span" ($D$) is the longest critical path of sequential dependencies. 

You will learn to evaluate the maximum available parallelism of any algorithm ($\frac{W}{D}$). Using Brent's Theorem, you will discover that a good parallel algorithm is "short and wide," maintaining optimal work while achieving a polylogarithmic span. Furthermore, the course grounds these metrics in physical reality: you will explore the Dynamic Power Equation ($P \propto F^3$), demonstrating why running multiple cores at a lower speed consumes vastly less power than one core at full speed, linking algorithmic energy directly to total Work.

### 2. Parallel Algorithmic Primitives
Standard sequential algorithms (like traversing a linked list) fail in parallel environments because their span is strictly linear ($O(N)$). You will learn how to break these sequential dependencies using powerful HPC primitives:
* **Prefix Sums (Scans) & List Ranking:** Using techniques like "pointer jumping" to turn sequential $O(N)$ traversal into parallel $O(\log N)$ span, though often trading higher total work for a shallower critical path.
* **Tree Computations:** Utilizing Euler tours to flatten trees into arrays, enabling parallel prefix-sums to compute properties like node depth or subtree size.
* **Sorting Networks:** Shifting from data-dependent sorts (like Quicksort) to **Bitonic Sorting**—a data-oblivious sorting network that maps perfectly to parallel hardware by strictly defining its communication patterns upfront.

### 3. Locality and the Cost of Data Movement
In HPC, computing a mathematical operation is practically free; moving the data from memory to the CPU is the true cost. You will learn to analyze algorithms using the **External Memory (I/O) Model**, optimizing for Block size ($B$) and Cache size ($M$).
* **The Roofline Model:** A visual framework that plots Arithmetic Intensity (FLOPs per byte) against Peak Performance, instantly revealing whether an algorithm is compute-bound or memory-bound.
* **Cache-Oblivious Algorithms:** You will explore elegant divide-and-conquer strategies that inherently minimize cache misses across *all* levels of the memory hierarchy simultaneously. By leveraging the Ideal-Cache model and fractal layouts (like van Emde Boas search trees), these algorithms hit the hardware's memory "sweet spot" without needing to know the machine-specific cache sizes.

### 4. Distributed Memory and Communication
When problems exceed the RAM of a single machine, we must scale out to distributed clusters. Here, the shared-memory illusion vanishes, and processors must explicitly send messages to one another.
* **Topologies & The Alpha-Beta Model:** You will learn how physical network wires (Torus, Hypercube, Fat-Tree) limit performance, and how to model communication costs using latency ($\alpha$) and inverse bandwidth ($\beta$).
* **MPI (Message Passing Interface):** You will transition from theory to practice, learning how to orchestrate point-to-point asynchronous messages (`MPI_Isend`) and collective operations across thousands of isolated nodes.

### 5. Distributed Algorithmic Case Studies
To solidify distributed concepts, the course deep-dives into two foundational case studies:
* **Distributed Matrix Multiplication:** You will trace the evolution from simple 1D layouts to the highly scalable 2D **SUMMA** algorithm. You will explore the **Loomis-Whitney geometric bound**, which mathematically proves the absolute minimum communication required, and see how **2.5D and 3D algorithms** trade extra memory capacity to redundantly replicate matrices and drastically reduce network bandwidth.
* **Distributed Sorting:** You will examine how Bitonic Merges map to network topologies, and how data-driven algorithms like **Sample Sort** use statistical sampling to maintain perfect load-balancing across a cluster.

### 6. Graph Analytics at Scale
Real-world data (social networks, web graphs) is highly irregular and sparse, making it the ultimate stress test for HPC.
* **Shared-Memory BFS:** You will learn how to replace highly-contended sequential queues with lock-free, parallel **Bag/Pennant data structures**, executing graph traversals level-by-level to unlock massive concurrency and manage benign data races.
* **Distributed BFS via Linear Algebra:** To scale across clusters, you will learn to cast graph traversal as a sparse matrix-vector multiplication (**SpMV**) over a Boolean semiring. Masking operations stencil out previously visited vertices, preventing redundant work.
* **Graph Partitioning:** Finally, you will explore the NP-complete problem of dividing a graph across a network to minimize edge cuts. You will study heuristics ranging from the **Kernighan-Lin** algorithm, to Multi-level Coarsening, and the mathematically profound **Spectral Partitioning** (using the eigenvectors of the Graph Laplacian).

### Conclusion
By abandoning the comfortable illusions of the RAM model, this course equips you with "hardware sympathy." You will emerge with the mathematical frameworks to prove communication lower bounds and the practical design patterns to build algorithms that genuinely scale on the world's largest supercomputers.