# Parallel Database Systems: The Future of High Performance Database Processing

**Authors**: David J. DeWitt, Jim Gray  
**Published**: Communications of the ACM, June 1992 (Vol. 36, No. 6)

---

## 1. Introduction

> **Context:** In the 1980s, people thought you needed specialized, expensive "database machine" hardware to run queries fast. DeWitt and Gray argued that the future was simply tying together a bunch of cheap, off-the-shelf computers (commodity hardware) and using software to parallelize the relational data model.

In the 1980s, researchers predicted the demise of specialized database machines. While special-purpose hardware (like CCDs or bubble memories) failed, **parallel database systems** built on conventional shared-nothing hardware became a massive success. This success was driven by:
1. **The Relational Data Model**: Relational queries consist of uniform operations on uniform streams of data, ideally suited for parallel execution (pipelined and partitioned parallelism).
2. **Commodity Hardware**: Fast, inexpensive microprocessors, RAM, and magnetic disks can be networked together to provide more power than traditional mainframes at a fraction of the cost.

## 2. Parallelism Goals and Metrics

The ideal parallel system demonstrates two key properties:
1. **Linear Speedup**: Twice as much hardware can perform the same task in half the time. (Hold problem size constant, grow the system).
2. **Linear Scaleup**: Twice as much hardware can perform twice as large a task in the same time. (Grow both the system and the problem).
   - **Transaction Scaleup**: $N$-times as many clients submitting $N$-times as many requests against an $N$-times larger database (typical in OLTP).
   - **Batch Scaleup**: An $N$-times larger computer solving an $N$-times larger single job (typical for database queries/analytics).

### The Three Barriers to Parallelism
1. **Startup**: The time needed to start a parallel operation. If thousands of processes are started, this can dominate computation time.
2. **Interference**: The slowdown each process imposes on others when accessing shared resources.
3. **Skew**: Variance in execution time among parallel steps. The overall job is only as fast as the slowest step.

## 3. Hardware Architectures

> **Tradeoff:** Shared-Memory is easy to program (everything is in one place) but hits hardware bottlenecks quickly (network/bus contention). Shared-Disk helps with memory bottlenecks but introduces complex locking. Shared-Nothing scales infinitely, but the software must be explicitly written to distribute data and queries via messages, making it much harder to engineer.

Computer architects use three primary designs for multi-processor systems:

1. **Shared-Memory**: All processors share direct access to a common global memory and disks. 
   - *Problem*: Does not scale well. Processor interference and network bandwidth limitations limit these systems to a small number of processors.
2. **Shared-Disk**: Each processor has private memory but direct access to all disks.
   - *Problem*: While it avoids memory bus bottlenecks, concurrent sharing of database records requires expensive locking and physical data exchange, creating network traffic and interference.
3. **Shared-Nothing**: Each processor has private memory and private disks. Processors communicate exclusively by sending messages over an interconnection network.
   - *Advantage*: Minimizes interference. Raw memory and disk accesses are local; only filtered data and questions/answers move through the network. This architecture can scale to thousands of nodes.

The consensus for parallel database architecture is the **shared-nothing** design (pioneered by Teradata, Gamma, Tandem).

## 4. Parallel Dataflow and Data Partitioning

> **Intuition:** Because relational algebra works on sets (tables) of tuples (rows), you can easily chop a big table into smaller chunks, hand each chunk to a different processor to do the exact same operation (like a filter or a join), and then glue the results back together.

Taking sequential SQL applications and executing them in parallel relies on data partitioning and a parallel dataflow approach.

### Data Partitioning

> **Mental Model:** Think of data partitioning like dealing a deck of cards to players. Round-robin is dealing one card to each player in a circle. Hash partitioning is looking at the suit of the card and giving all hearts to player 1, spades to player 2, etc. Range partitioning is giving cards 2-5 to player 1, 6-9 to player 2, etc.

Distributing a relation's tuples across multiple disks allows parallel I/O bandwidth.
1. **Round-robin**: Tuples are distributed sequentially. Good for full sequential scans, bad for associative (point) lookups.
2. **Hash partitioning**: A hash function on an attribute maps the tuple to a disk. Excellent for sequential and associative access; highly resistant to data skew.
3. **Range partitioning**: Maps contiguous attribute ranges to specific disks. Good for clustering and range queries (e.g., `BETWEEN 37 and 39`), but highly susceptible to data and execution skew.

### Parallelism Within Relational Operators
Parallel database systems use existing sequential routines but feed them parallel data streams using **split** and **merge** operators:
- **Merge**: Combines multiple parallel data streams into a single sequential stream.
- **Split**: Replicates or partitions a single stream into several independent streams based on a mapping function (e.g., hashing or range).

### Specialized Parallel Relational Operators
New algorithms minimize data flow and tolerate skew. 
- **Sort-Merge Join**: Typically $O(N \log N)$. Vulnerable to data skew.
- **Hash-Join**: $O(N)$. Highly parallelizable. Both relations are hash-partitioned on the join attribute. Each node then joins its local partitions in memory. 

## 5. State of the Art (Circa 1992)

- **Teradata**: Pioneered shared-nothing parallel SQL systems. Uses Interface Processors (IFPs) and Access Module Processors (AMPs) connected via a Y-net tree. Uses hash partitioning and parallel sort-merge joins.
- **Tandem NonStop SQL**: Designed for Online Transaction Processing (OLTP). Uses a duplexed ring network. Heavily optimizes sequential scans by filtering tuples at the disk servers. Achieves parallel index maintenance.
- **Gamma (UW-Madison)**: Runs on Intel Hypercube. Introduced hybrid-range partitioning and parallel hash-join methods.
- **Bubba (MCC)**: Uses FAD (an extended-relational language) instead of SQL. Employs a single-level store mechanism mapping the database to virtual memory. Optimizes range partitioning based on the "heat" (access frequency) of tuples.
- **SDC (Univ. of Tokyo)**: A hybrid hardware/software shared-nothing approach featuring a special-purpose hardware sorting engine.

## 6. Grosch's Law Defied
Herb Grosch observed in the 1960s that there is an economy of scale in computing (expensive computers were exponentially more powerful). Shared-nothing database machines defy this law. By linking hundreds of cheap microprocessors, they achieve linear speedup and scaleup, outperforming expensive mainframes in both peak performance and price/performance.

## 7. Future Directions
- **Mixing Batch and OLTP Queries**: Large read queries lock data, blocking OLTP updates. Solutions include fuzzy reads or versioning. Priority scheduling (preventing priority inversion) is also an active research area.
- **Parallel Query Optimization**: Query optimizers must be expanded to consider all parallel algorithms and node organizations, especially handling data skew dynamically.
- **Physical Database Design**: Tools are needed to help DBAs select the best partitioning and indexing strategies across thousands of nodes (including multidimensional partitioning).
- **Online Utilities**: Reorganizing, dumping, or loading terabytes of data must be parallelized and done online without making the database unavailable.