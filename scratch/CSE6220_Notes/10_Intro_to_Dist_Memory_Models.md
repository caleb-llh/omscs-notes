# Introduction to Distributed Memory Models

## 1. Introduction & Motivation

### Background Context
In the early days of computing, making programs faster simply meant waiting for a faster CPU. However, due to physical constraints (like heat dissipation and quantum tunneling), single-core processor speeds have largely plateaued. Today, to solve massive, computationally intensive problems—such as training large language models (LLMs), forecasting global weather patterns, or simulating molecular dynamics—we can no longer rely on a single machine. The problem either takes an impractically long time to compute or simply cannot fit into a single computer's memory. 

Distributed memory computations are essential for overcoming these barriers by pooling the memory and processing power of thousands of machines.

### Case Study: Simulating the Human Brain
To intuitively understand the scale of distributed computations and why memory limits are hit so quickly, consider simulating 100% of the human brain down to the synaptic level:
- **Scope**: 1% of the brain has ~2 billion neurons and ~10 trillion synapses.
- **Data per Synapse**: ~24 bytes of storage (for weights, states, etc.).
- **Storage for 1%**: 24 bytes × 10 trillion = 240 TB (Terabytes).
- **Storage for 100%**: ~24 PB (Petabytes).
- **Hardware Requirement**: Assuming standard 16 GiB (gibibytes) RAM workstations, this requires roughly **1.4 million computers** just to store the problem state—not even accounting for the compute power needed to run the simulation! 

This staggering scale highlights the absolute necessity for massive clusters and supercomputers (e.g., Sequoia, Google Data Centers) with millions of nodes working in tandem.

---

## 2. A Basic Model of Distributed Memory

### Mental Model: The Island Archipelago
Imagine a distributed memory machine as an archipelago of separate islands. 
- Each **node** is an island.
- The **processor** is a worker on the island.
- The **private memory** is a warehouse on that specific island. The worker can instantly access anything in their own warehouse.
- The **network** is the ocean. To share data, a worker cannot just reach into another island's warehouse; they must explicitly pack the data onto a boat (a message) and send it across the water.

Because each node can only directly read and write its own private memory, nodes must explicitly send and receive messages to share data.

### The Five Rules of Message Passing (The Alpha-Beta Model)
To analyze algorithms, we need a mathematical model of how long communication takes. The following rules govern the cost and constraints of communication:
0. **Internalize the rules** (never talk about the rules).
1. **Fully Connected**: Assume there is always a path from any node to any other node (any island can send a boat to any other island).
2. **Bidirectional Links**: Links can carry messages in both directions simultaneously without conflict.
3. **Communication Capacity**: A node can concurrently perform at most **1 send** and **1 receive** at a time. (A worker can only load one boat and unload one boat at a time).
4. **Communication Cost (The Alpha-Beta Model)**: The minimum time to send a message of size $n$ words between any two nodes without contention is:
   $$T = \alpha + \beta \cdot n$$
   - **$\alpha$ (Latency)**: A fixed startup cost or message preparation overhead. *Intuition: The time it takes to fill out shipping labels, load the boat, undock, and dock at the destination. This cost is incurred whether the boat is carrying 1 box or 10,000 boxes.*
   - **$\beta$ (Inverse Bandwidth)**: The time to transmit a single word (cost per word). *Intuition: The time it takes to physically load a single box onto the boat. More boxes = more time.*
5. **Congestion (Contention)**: If $k$ messages simultaneously compete for the same directional link (overlap in path and direction), the transmission time is serialized. The effective cost becomes $\alpha + \beta \cdot n \cdot k$.

### Origin of the Alpha-Beta Model (Pipelined Message Delivery)
Why does the formula look like a simple linear equation? The alpha-beta model derives from pipelined message delivery across a network path of length $P$. 
*Think of a bucket brigade passing buckets of water down a line of $P$ people:*
- Assume message preparation takes time $a$.
- Traversing a link (passing a bucket to the next person) takes time $t$ per word.
- For a message of $n$ words, the first word arrives at the destination in time $a + t(P-1)$.
- Subsequent words arrive one step behind the previous. Thus, the total time is:
  $$T = a + t(P-1) + t(n-1) = [a + t(P-1) - t] + tn$$
- When $a \gg t$ (which is true in modern networks where software overhead is huge compared to the time light takes to travel a fiber optic cable), the constant term is dominated by software overhead. Thus, we simplify to $\alpha \approx a$ and $\beta \approx t$. 

### Computation vs. Communication Costs
- Let $\tau$ be the cost per compute operation (e.g., adding two numbers).
- In practice, the time scales look like this: $\tau \ll \beta \ll \alpha$ (e.g., $10^{-12}s \ll 10^{-9}s \ll 10^{-6}s$).
- **Implications and Mental Model**: 
  - Computation is virtually free; communication is astronomically expensive. Avoid communication whenever possible. It is often faster to have a node re-calculate a value from scratch than to ask another node to send the result over the network!
  - Because $\alpha \gg \beta$ (startup cost dwarfs per-word cost), it is vastly more efficient to send **a few large messages** (filling a massive cargo ship) rather than **many small messages** (sending thousands of single-box rowboats).

---

## 3. Point-to-Point Communication & SPMD

### Single-Program, Multiple-Data (SPMD)
*Mental Model: An orchestra without a conductor. Every musician has the exact same sheet music (the Single Program), but they play different notes based on their seat number (the Multiple Data).*

Algorithms are written as a single program that runs independently and asynchronously on all processes.
- **`RANK`**: A global variable representing the unique ID of the executing process (the "seat number").
- **`P`**: The total number of processes.

### Asynchronous Primitives
1. `handle = sendAsync(buf, destination_rank)`: Registers a send operation. Returning does *not* mean the buffer is sent. It simply provides a handle to track progress. The buffer should not be modified until the send completes (otherwise, you might overwrite the data before it gets put on the network!).
2. `handle = recvAsync(buf, source_rank)`: Registers a receive operation. Returns a handle.
3. `wait(handle)` / `wait*()`: Blocks until the operation(s) complete. 
   - For `recvAsync`, completion means the message was successfully delivered to `buf`.
   - For `sendAsync`, completion merely means `buf` is safe to reuse. The message might be delivered to the receiver, or it might just be buffered by the operating system locally.

### Two-Sided Messaging and Deadlocks
- Every `send` must have a matching `receive` (two-sided messaging). *Think of playing catch: if one person throws the ball (`send`), the other person MUST have their glove up and ready (`receive`), otherwise the ball is dropped.*
- Because `send` completion is implementation-dependent, assuming it completes before a matching `receive` is posted can lead to deadlocks. 
  - *Deadlock Example*: Imagine two processes, A and B. A posts a blocking send to B, and B posts a blocking send to A. They are both standing there, holding out a box, refusing to take the other's box until their own box is accepted. They will deadlock waiting for network buffers to clear.

---

## 4. Collective Operations: Concepts & API

Collectives involve coordinated communication among all processes in the network. Instead of nodes talking one-on-one, the whole group participates in a structured routine.

### Primary Collectives
*Real-world Analogies:*
1. **Reduce (All-to-One)**: Combines vectors/values from all nodes using an operator (e.g., sum, max), placing the result on a designated **root** node. *(Example: Every department head sends their local expenses to the CEO, who tallies up the total company budget.)*
2. **Broadcast (One-to-All)**: The dual of reduce. The root node distributes a copy of its exact data to all other nodes. *(Example: The CEO emails a new company-wide policy to all employees.)*
3. **Scatter**: The root divides its data into pieces and sends a distinct piece to each node. *(Example: Dealing a deck of cards to players around a table.)*
4. **Gather**: The dual of scatter. Every node sends a piece of data to the root, which concatenates it in order. *(Example: Collecting the cards back from the players into a single deck.)*
5. **All-Gather**: A gather where the collected result is broadcasted to all nodes (no root). *(Example: A networking event where everyone exchanges business cards until everyone has a complete set.)*
6. **Reduce-Scatter**: The dual of all-gather. Performs an element-wise reduction across all nodes, then scatters the resulting vector so each node gets a piece. *(Example: Every node calculates partial sums for 5 different budgets. After the operation, Node 0 holds the total for budget 1, Node 1 holds the total for budget 2, etc.)*

### Pseudocode API Signatures
- `reduce(A_local, root)`: Input size $n$, output size $n$ on root.
- `bcast(A_local, root)`: Root broadcasts buffer of size $n$ to all.
- `gather(A_in, A_out, root)`: Input size $m$, output size $m \times P$ on root. ($n = m \times P$)
- `scatter(A_in, A_out, root)`: Input size $m \times P$ on root, output size $m$.
- `allGather(A_in, A_out)`: Input size $m$, output size $m \times P$ on all nodes.
- `reduceScatter(A_in, A_out)`: Input size $m \times P$, output size $m$ on all nodes.
- `reshape(A, 1D|2D)`: Logical (zero-cost) operation to interpret a 1D array as 2D (column-major) or vice versa.

---

## 5. Implementing Collectives & Cost Analysis

How do we actually perform these group activities efficiently? A naive approach (e.g., the root sending a separate message to every single node one by one) scales terribly. We need smart algorithms.

### Lower Bounds (The absolute best we can do)
- **Latency (Alpha)**: The minimum number of rounds is $\log_2 P$. Why? Because processes can pair up at most once per round. It's like a phone tree: 1 person calls 1 person (2 know), then 2 call 2 (4 know), then 4 call 4 (8 know). Minimum cost: $\alpha \log P$.
- **Bandwidth (Beta)**: The root (or all nodes) must send/receive at least $n(P-1)/P \approx n$ data. You cannot avoid physically moving the bytes through the network pipe. With perfect parallelization, minimum cost is $\beta n$.
- **Optimal collective cost goal**: $O(\alpha \log P + \beta n)$.

### Tree-Based Reduce / Broadcast
- **Mechanism**: A tree-based approach uses binary bitmasking. In round $i$, nodes whose ranks differ by $2^i$ communicate. (Like the phone tree example above).
- **Cost**: $\log P$ rounds. If the message size is $n$, cost is $O(\alpha \log P + \beta \cdot n \log P)$.
- **Analysis**: It hits the latency lower bound ($\alpha \log P$) but is suboptimal in bandwidth due to the $\beta \cdot n \log P$ term (because we are sending the *full* message of size $n$ at every level of the tree).
- **When to use**: Good when messages are small ($n \ll \frac{\alpha}{\beta}$), as the $\alpha$ (startup) term dominates the total time, and the bandwidth penalty is negligible.

### Divide-and-Conquer Scatter / Gather
- **Naive Scatter**: Root sends $P-1$ messages sequentially. Cost: $O(\alpha P + \beta n)$. (Too much latency!).
- **Optimal Scatter**: Root splits the deck of cards in half, sends one half to another node. In the next round, both nodes split their smaller decks in half again and send to two new nodes, etc.
- **Cost**: Over $\log P$ rounds, round $i$ sends $n / 2^i$ data. Total cost: $\sum (\alpha + \beta \frac{n}{2^i}) = O(\alpha \log P + \beta n)$.
- This perfectly achieves both latency and bandwidth lower bounds! Gather achieves the same bounds by exactly reversing the steps.

### Bucketing (Ring) Algorithms for Large Messages
For large messages, the $\beta \cdot n \log P$ cost of tree-based methods is too high. **Bucketing** optimizes bandwidth by splitting the message into chunks.
- **Example: All-Gather**:
  - *Mental Model: A sushi conveyor belt.* Instead of a complex tree, organize nodes in a simple ring.
  - Each node sends its chunk of size $m = n/P$ to its right neighbor, while simultaneously receiving a chunk from its left.
  - In the next round, it forwards the chunk it *just received* to the right.
  - After $P-1$ steps, every chunk has traveled the full circle, and all nodes have all data.
- **Cost**: $(P-1)$ rounds sending $n/P$ data. Total: $O(\alpha P + \beta n)$.
- **Analysis**: Bandwidth optimal ($\beta n$), but latency suboptimal ($\alpha P$). Excellent for large messages where $\beta n \gg \alpha P$ (i.e., $n/P \gg \alpha/\beta$), because the bandwidth savings outweigh the extra rounds.

### Composing Collectives
Complex collectives can be elegantly and optimally built by snapping together simpler optimal primitives like Lego blocks:
- **All-Gather**: Gather + Broadcast. (If Gather and Broadcast are optimal, All-Gather is asymptotically optimal).
- **Bandwidth-Optimal Broadcast**: Scatter (Divide & Conquer) + All-Gather (Bucketing). 
  - *Intuition: Instead of the root sending the massive file to everyone (slow), the root splits the file into chunks and deals them out (Scatter). Then, everyone shares their chunks in a ring (All-Gather).*
- **Bandwidth-Optimal All-Reduce**: Reduce-Scatter (Bucketing) + All-Gather (Bucketing).

---

## 6. Conclusion
The Alpha-Beta message-passing model provides a robust, mathematical framework for reasoning about distributed memory efficiency, explicitly balancing computation versus communication. By understanding $\alpha$ (latency) and $\beta$ (bandwidth), programmers can choose the right algorithmic strategy (e.g., Tree vs. Ring) based on their message sizes.

Its primary drawback is that it places a heavy burden on the programmer. It exposes low-level network details—managing ranks, network topologies, preventing deadlocks, and explicitly synchronizing nodes. An open research question remains: Can we design efficient algorithms and programming models that are fundamentally "network oblivious" (where the system handles the distribution automatically without sacrificing the performance we get from hand-tuned collectives)? Modern frameworks like MapReduce and Apache Spark attempt to abstract these details away, but often trade off some degree of peak performance for developer friendliness.
