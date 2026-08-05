# Tree Computations in Parallel

## 1. Introduction
**Background Context:** Trees are ubiquitous in computer science, used to represent everything from Document Object Models (DOMs) in web browsers and Abstract Syntax Trees (ASTs) in compilers, to file systems and hierarchical organizational data. While sequential tree traversals (like DFS or BFS) are straightforward, they often become a bottleneck when processing massive datasets because a node seemingly must wait for its parent or children to be processed. 
> **Common Confusion:** It might seem like tree processing is inherently sequential because you must visit a parent before its children (or vice versa). The breakthrough in parallel tree algorithms is realizing that we don't need to process nodes in their structural order if we can mathematically decouple their relationships.

**The Core Intuition:** A fundamental strategy for parallelizing computations on trees is **linearization**—converting the rigid, hierarchical tree structure into a flat line (or list). Once flattened, we can unleash powerful, highly-optimized parallel array primitives (like prefix sums or parallel maps) on that line. 
> **Tradeoff:** Linearization allows us to use highly optimized array primitives, but it requires an initial overhead to transform the tree into a flat array. For very small trees, this overhead might outweigh the parallel speedup.
> **Fact Check:** Linearization using the Euler tour technique transforms a tree into an array in $O(1)$ time given the proper adjacency list with cross-pointers (or $O(n)$ to build it), ensuring that flattening overhead scales linearly and does not dominate the overall $O(n)$ work.

When parallelizing these algorithms, a common challenge is breaking symmetry. In a parallel system where all processors act simultaneously and anonymously, they might conflict (e.g., all trying to modify the same node or join the same set). This can often be solved elegantly using **randomization** (e.g., coin flipping), which provides a decentralized way to break ties without needing a central coordinator.
> **Example:** Imagine two processors trying to adopt the same child node in a parallel forest. Without a mechanism to break symmetry, they might overwrite each other's pointers. A coin flip ensures one backs off, preventing a race condition.

## 2. Parallel Root Finding & Pointer Jumping

**Background Context:** Root finding is the foundation of many critical tree operations, such as identifying connected components or powering the Union-Find data structure. 

### Representation & Sequential Approach
*   **Array Pool Representation**: Trees can be stored efficiently in an array where each index corresponds to a node, and the value at that index stores its parent pointer (`P`).
    *   *Example*: If `P = [0, 0, 1, 1, 2, 2]`, node `0` is the root (it points to itself), nodes `1` and `2` are children of `0`, and so on.
*   **Sequential Root Finding**: Starting from any node, follow the parent pointers until reaching a node with no parent (null or 0). 
    *   **Running Time**: $O(n)$ in the worst case, as a highly unbalanced tree (like a linear chain or linked list) requires traversing up to $n$ nodes one by one.
> **Hypothetical:** If you have a linked list of 1 million nodes, a sequential root finding approach takes 1 million steps. Parallelizing this naively without pointer jumping would still take 1 million steps because each node only knows its immediate parent.

### Parallel Approach: Pointer Jumping
**Mental Model:** Imagine a long line of people where everyone is pointing to the person directly in front of them. Instead of passing a message one-by-one to the very front, everyone simultaneously looks at who their person is pointing to, and then points to *that* person instead. In just one step, the distance to the front halves for everyone!

To parallelize, we explore all nodes simultaneously and aggressively shorten paths to the root using **pointer jumping**.
> **Intuition:** By repeatedly doubling the "reach" of each node's pointer, we transform a linear distance $d$ into a logarithmic distance $\log d$. It's like taking an express train that skips more stations at every stop.
> **Fact Check:** Pointer jumping reduces a path of length $d$ to length $1$ in exactly $\lceil \log_2 d \rceil$ steps. Since the maximum path length in a tree of $n$ nodes is $n-1$, the algorithm requires at most $\lceil \log_2 n \rceil$ iterations to guarantee every node points directly to the root.
*   **Algorithm**: In parallel, every node changes its parent pointer to point directly to its grandparent (if one exists).
    ```text
    for step = 1 to log n:
        parallel for k in all_nodes:
            if hasGrandparent(k, P):
                next[k] = P[P[k]]
            else:
                next[k] = P[k]
        P = next
    ```
    *   *Example Trace*:
        *   Step 0: `4 -> 3 -> 2 -> 1 -> 0 (Root)`
        *   Step 1: `4 -> 2`, `3 -> 1`, `2 -> 0`, `1 -> 0` (Distances halved)
        *   Step 2: `4 -> 0`, `3 -> 0`. Everyone now points directly to the root in just 2 steps instead of 4!
> **Common Confusion:** Pointer jumping alters the tree's structure permanently. After the algorithm finishes, the original parent-child relationships are lost because every node now points directly to the root. If you need the original tree later, you must keep a copy.
*   **Properties**:
    *   **Work**: $O(n \log n)$. This is **not work-optimal** because the outer loop runs $\log n$ times, and each iteration performs $O(n)$ parallel operations. A sequential approach would only take $O(n)$ total work.
    *   **Span**: Polylogarithmic ($O(\log n)$). The path lengths shrink exponentially.
    *   **Forest Support**: A neat feature of this algorithm is that it works on a forest (multiple disconnected trees in the array), making every node point to the root of its respective tree simultaneously.
> **Tradeoff:** The $O(n \log n)$ work complexity means that while the span (time) is incredibly fast ($O(\log n)$), the total number of operations performed is higher than the sequential $O(n)$ algorithm. This consumes more energy and processing power, which can be a bottleneck on systems with limited cores.
> **Mental Model:** Think of the non-work-optimal pointer jumping like sending every employee in a company to simultaneously verify their entire management chain up to the CEO independently. It gets the job done extremely fast, but wastes a massive amount of collective effort compared to just having managers pass the message down.

## 3. Work-Optimal List Ranking & Parallel Independent Sets

**Background Context:** Pointer jumping is incredibly fast but does too much total work ($n \log n$). If we have a billion nodes, doing $30 \times$ more total operations than a sequential CPU is wasteful. We need a smarter way to process lists and trees in parallel.

### The Work-Optimal Strategy
Standard parallel list ranking (Wyllie's pointer jumping algorithm) is not work-optimal. To make list operations work-optimal, we use a divide-and-conquer strategy:
1.  **Shrink** the list of size $n$ to a smaller equivalent list of size $m$. (Summarize the data).
2.  **Run** the $m \log m$ list ranking algorithm on the smaller list. (Do the heavy lifting on a small dataset).
3.  **Expand** the list back to its original size to resolve the remaining ranks. (Pass the results back down).
*   **Target Size**: To achieve a work-optimal $O(n)$ algorithm, the list must be shrunk to **$m = n / \log n$**. 
    *   *Why this specific size?* Because if we run our $O(m \log m)$ pointer jumping on this smaller list, the total work becomes $(n / \log n) \cdot \log(n / \log n)$. Since $\log(n / \log n)$ is strictly less than $\log n$, the total work simplifies to approximately $O(n)$, matching the sequential algorithm!
> **Mental Model:** Think of the divide-and-conquer strategy like delegating tasks in a massive company. You can't have the CEO (list ranking) micromanage 10,000 employees. Instead, you group employees into teams (shrinking the list), have the CEO manage the team leads (running the $m \log m$ algorithm), and then the team leads relay the instructions to their teams (expanding the list).
> **Fact Check:** The work done to shrink the list must also be strictly bounded by $O(n)$. Since we reduce the list by a constant fraction in each step, the geometric series sum of the work done across all shrinking steps evaluates to $O(n)$. Thus, the overall work remains $O(n)$.

### Parallel Independent Sets
**Intuition:** To safely shrink a list in parallel, we want to remove some nodes and bypass them. But if we accidentally remove a node AND its direct neighbor at the same time, the list breaks into disconnected pieces! We can only safely remove nodes that are *not adjacent*. 
> **Background Context:** The concept of an Independent Set originates from graph theory, where it describes a set of vertices in a graph, no two of which are adjacent. In the context of a linked list, it simply means we never select two consecutive nodes.

To achieve this, we use an **independent set**: a subset of vertices where no vertex has its successor also in the subset.
*   **Symmetry Breaking**: In parallel, all nodes look identical. How do they decide who joins the set? If they all just say "I'll join", the list breaks. We use a randomized scheme to break the symmetry.
*   **Algorithm**:
    1.  **Coin Toss**: Every node flips a coin in parallel. "Heads" means candidate for the independent set.
    2.  **Double Heads Correction**: Check each node in parallel. If a node is "Heads" AND its neighbor is also "Heads", the node flips its status to "Tails".
    3.  **Gather**: Collect all remaining "Heads" as the valid independent set.
*   **Properties**:
    *   **Work**: $O(n)$ (linear).
    *   **Span**: $O(\log n)$ (or $O(1)$ depending on the PRAM model specifics).
    *   **Expected Size**: On average, **$n/4$** nodes end up in the independent set.
        *   *The Math:* A node only survives if it rolls "Heads" ($1/2$ probability) AND its neighbor rolls "Tails" ($1/2$ probability). Because these are independent coin flips, the combined probability is $(1/2) \times (1/2) = 1/4$. Thus, out of 4 possible coin-toss combinations, only 1 survives the double-heads check.
> **Hypothetical:** What if we used a biased coin that lands on "Heads" 75% of the time? The probability of a node rolling Heads and its neighbor rolling Tails would be $0.75 \times 0.25 = 0.1875$ (or 18.75%), which is lower than the 25% achieved with a fair coin. A fair coin mathematically maximizes the size of the independent set in this algorithm.
*   **List Contraction**:
    *   Remove the independent set nodes, wire their predecessors to their successors, and push temporary ranks to the neighbors.
    *   Because each iteration reduces the list size by a factor of roughly $3/4$, it takes **$O(\log \log n)$** iterations of the randomized independent set algorithm to shrink the list to the target size $n / \log n$.
        *   *The Math:* We want $(3/4)^k \cdot n = n / \log n$. Solving for $k$ iterations gives $k = \log_{4/3}(\log n) = O(\log \log n)$.
> **Intuition:** $O(\log \log n)$ is an incredibly small number. Even for an astronomically large list where $n = 10^{80}$ (the number of atoms in the observable universe), $\log \log n$ is less than 10. For all practical purposes, this shrinking phase finishes in a constant number of steps.
> **Fact Check:** The expected size of the independent set using fair coin flips is $n/4$, meaning the list size shrinks to $3n/4$ in expectation per step. However, deterministic symmetry breaking algorithms (like Cole-Vishkin's deterministic coin tossing) can guarantee an independent set of size at least $n/3$ without randomization, albeit with different algorithmic overhead.

## 4. The Euler Tour Technique

**Background Context:** Pointer jumping is great for finding roots, but it permanently destroys the shape of the tree. What if we need to compute the depth of every node, or perform a post-order traversal? We need a way to linearize the tree *without* losing its structural information.

### Concept
Many classic tree computations (e.g., pre-order/post-order numberings, level computation) appear inherently sequential because a node seemingly must wait for its children to finish before it can compute its own value. **The Euler Tour technique** linearizes the tree, converting it into a linked list to allow parallel list scans/prefix-sums.
> **Background Context:** Leonhard Euler introduced the concept of an Eulerian circuit in 1736 when solving the Seven Bridges of Königsberg problem. The Euler Tour technique brilliantly adapts this historical graph theory concept to modernize parallel tree processing.

**Mental Model:** Imagine drawing a tree on a piece of paper. Now, trace the outline of the entire tree without lifting your pen. You go down the left side of every branch, wrap around the leaves, and come back up the right side. You have just drawn an Euler Tour! It naturally flattens the tree into a single continuous path.

*   **Eulerian Graph**: Replace every undirected tree edge with a pair of directed edges (one going down, one going up). Now, every node has an equal number of incoming and outgoing edges.
*   **Euler Circuit**: Because of the Eulerian property, there exists a directed circuit that traverses every edge exactly once. This circuit serves as our list.
> **Tradeoff:** The Euler Tour doubles the number of edges (since every undirected edge becomes two directed edges). This requires allocating twice as much memory for the edge list compared to a standard tree representation, trading space for parallel speed.
> **Fact Check:** An undirected tree with $n$ vertices has exactly $n-1$ edges. By replacing each with two directed edges, the Euler Tour circuit will have exactly $2n-2$ directed edges. This confirms the list size is linear with respect to the tree size.

### Applications
By carefully assigning initial values to the nodes (or edges) in the Euler circuit, a simple parallel list scan (prefix-sum) can compute various tree properties in one shot:
*   **Post-Order Numbering**:
    *   Assign `0` to the head node and to all sinks of parent-to-child edges (descending into the tree).
    *   Assign `1` to all sinks of child-to-parent edges (ascending/returning).
    *   *Scan result*: The running sums at the child-to-parent sinks perfectly match the post-order numbers.
*   **Level (Depth) Computation**:
    *   *Intuition:* Going down a level adds depth; coming back up subtracts it.
    *   Assign `+1` to sinks of parent-to-child edges (descending increases depth).
    *   Assign `-1` to sinks of child-to-parent edges (ascending decreases depth).
    *   *Scan result*: The running sum at any node yields its exact depth from the root.
        *   *Example Trace:* Going from `A -> B` adds `+1`. The depth of `B` is now `1`. Returning from `B -> A` adds `-1`. The depth sum goes back to `0` for `A`.
> **Hypothetical:** If you wanted to compute the size of the subtree rooted at each node, you could assign `1` to descending edges, `0` to ascending edges, and perform a similar prefix sum. The Euler Tour framework is incredibly versatile just by changing the edge weights!
> **Mental Model:** Think of the Euler Tour prefix sum as an altitude tracker on an airplane. Descending edges are like climbing 1,000 feet, ascending edges are like dropping 1,000 feet. At any point in the flight path, your current altitude perfectly corresponds to your depth in the tree.

### Algorithm Complexity & Implementation
*   **Complexity**: 
    *   **Work**: $O(n)$ (Linear, assuming the underlying list scan is work-optimal).
    *   **Span**: $O(\log n)$. 
    *   *Crucial Insight:* The span depends **only** on the length of the list (which is $2n-2$), completely independent of the tree's shape! Even highly unbalanced, deep, stringy trees are processed just as efficiently and quickly as perfectly balanced binary trees.
> **Common Confusion:** It's easy to assume that unbalanced trees are bad for parallel algorithms because they usually degrade divide-and-conquer approaches. However, since the Euler Tour completely linearizes the tree into a list of size $2n-2$, the tree's original shape has zero impact on the prefix-sum span.
*   **Implementation Details**:
    *   **Adjacency Table**: Represent the tree such that each vertex $v$ maintains an adjacency list of its $d_v$ outgoing neighbors.
    *   **Successor Function $S$**: Defines the traversal mathematically. For an edge $(u_i, v)$, $S(u_i, v) = (v, u_{(i+1) \pmod{d_v}})$. This effectively flips the relative position and advances circularly to the next neighbor, ensuring we "wrap around" the node correctly.
    *   **Cross-Edge Pointers**: To ensure the successor function computes in $O(1)$ constant time (without having to search the adjacency list), the adjacency list must be augmented with cross-edge pointers during creation.
> **Intuition:** Without cross-edge pointers, a processor would have to linearly search the adjacency list to find the "next" edge, which could take $O(n)$ time for a node with many children (like a star graph). Cross-edge pointers guarantee the $O(1)$ constant time step required to keep the algorithm work-optimal.
> **Fact Check:** The successor function $S(u_i, v) = (v, u_{(i+1) \pmod{d_v}})$ mathematically guarantees that the path never crosses itself prematurely and visits every single directed edge exactly once before returning to the start, fulfilling the formal definition of an Eulerian circuit.