# Tree Computations in Parallel

## 1. Introduction
**Background Context:** Trees are ubiquitous in computer science, used to represent everything from Document Object Models (DOMs) in web browsers and Abstract Syntax Trees (ASTs) in compilers, to file systems and hierarchical organizational data. While sequential tree traversals (like DFS or BFS) are straightforward, they often become a bottleneck when processing massive datasets because a node seemingly must wait for its parent or children to be processed. 

**The Core Intuition:** A fundamental strategy for parallelizing computations on trees is **linearization**—converting the rigid, hierarchical tree structure into a flat line (or list). Once flattened, we can unleash powerful, highly-optimized parallel array primitives (like prefix sums or parallel maps) on that line. 

When parallelizing these algorithms, a common challenge is breaking symmetry. In a parallel system where all processors act simultaneously and anonymously, they might conflict (e.g., all trying to modify the same node or join the same set). This can often be solved elegantly using **randomization** (e.g., coin flipping), which provides a decentralized way to break ties without needing a central coordinator.

## 2. Parallel Root Finding & Pointer Jumping

**Background Context:** Root finding is the foundation of many critical tree operations, such as identifying connected components or powering the Union-Find data structure. 

### Representation & Sequential Approach
*   **Array Pool Representation**: Trees can be stored efficiently in an array where each index corresponds to a node, and the value at that index stores its parent pointer (`P`).
    *   *Example*: If `P = [0, 0, 1, 1, 2, 2]`, node `0` is the root (it points to itself), nodes `1` and `2` are children of `0`, and so on.
*   **Sequential Root Finding**: Starting from any node, follow the parent pointers until reaching a node with no parent (null or 0). 
    *   **Running Time**: $O(n)$ in the worst case, as a highly unbalanced tree (like a linear chain or linked list) requires traversing up to $n$ nodes one by one.

### Parallel Approach: Pointer Jumping
**Mental Model:** Imagine a long line of people where everyone is pointing to the person directly in front of them. Instead of passing a message one-by-one to the very front, everyone simultaneously looks at who their person is pointing to, and then points to *that* person instead. In just one step, the distance to the front halves for everyone!

To parallelize, we explore all nodes simultaneously and aggressively shorten paths to the root using **pointer jumping**.
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
*   **Properties**:
    *   **Work**: $O(n \log n)$. This is **not work-optimal** because the outer loop runs $\log n$ times, and each iteration performs $O(n)$ parallel operations. A sequential approach would only take $O(n)$ total work.
    *   **Span**: Polylogarithmic ($O(\log n)$). The path lengths shrink exponentially.
    *   **Forest Support**: A neat feature of this algorithm is that it works on a forest (multiple disconnected trees in the array), making every node point to the root of its respective tree simultaneously.

## 3. Work-Optimal List Ranking & Parallel Independent Sets

**Background Context:** Pointer jumping is incredibly fast but does too much total work ($n \log n$). If we have a billion nodes, doing $30 \times$ more total operations than a sequential CPU is wasteful. We need a smarter way to process lists and trees in parallel.

### The Work-Optimal Strategy
Standard parallel list ranking (Wyllie's pointer jumping algorithm) is not work-optimal. To make list operations work-optimal, we use a divide-and-conquer strategy:
1.  **Shrink** the list of size $n$ to a smaller equivalent list of size $m$. (Summarize the data).
2.  **Run** the $m \log m$ list ranking algorithm on the smaller list. (Do the heavy lifting on a small dataset).
3.  **Expand** the list back to its original size to resolve the remaining ranks. (Pass the results back down).
*   **Target Size**: To achieve a work-optimal $O(n)$ algorithm, the list must be shrunk to **$m = n / \log n$**. 
    *   *Why this specific size?* Because if we run our $O(m \log m)$ pointer jumping on this smaller list, the total work becomes $(n / \log n) \cdot \log(n / \log n)$. Since $\log(n / \log n)$ is strictly less than $\log n$, the total work simplifies to approximately $O(n)$, matching the sequential algorithm!

### Parallel Independent Sets
**Intuition:** To safely shrink a list in parallel, we want to remove some nodes and bypass them. But if we accidentally remove a node AND its direct neighbor at the same time, the list breaks into disconnected pieces! We can only safely remove nodes that are *not adjacent*. 

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
*   **List Contraction**:
    *   Remove the independent set nodes, wire their predecessors to their successors, and push temporary ranks to the neighbors.
    *   Because each iteration reduces the list size by a factor of roughly $3/4$, it takes **$O(\log \log n)$** iterations of the randomized independent set algorithm to shrink the list to the target size $n / \log n$.
        *   *The Math:* We want $(3/4)^k \cdot n = n / \log n$. Solving for $k$ iterations gives $k = \log_{4/3}(\log n) = O(\log \log n)$.

## 4. The Euler Tour Technique

**Background Context:** Pointer jumping is great for finding roots, but it permanently destroys the shape of the tree. What if we need to compute the depth of every node, or perform a post-order traversal? We need a way to linearize the tree *without* losing its structural information.

### Concept
Many classic tree computations (e.g., pre-order/post-order numberings, level computation) appear inherently sequential because a node seemingly must wait for its children to finish before it can compute its own value. **The Euler Tour technique** linearizes the tree, converting it into a linked list to allow parallel list scans/prefix-sums.

**Mental Model:** Imagine drawing a tree on a piece of paper. Now, trace the outline of the entire tree without lifting your pen. You go down the left side of every branch, wrap around the leaves, and come back up the right side. You have just drawn an Euler Tour! It naturally flattens the tree into a single continuous path.

*   **Eulerian Graph**: Replace every undirected tree edge with a pair of directed edges (one going down, one going up). Now, every node has an equal number of incoming and outgoing edges.
*   **Euler Circuit**: Because of the Eulerian property, there exists a directed circuit that traverses every edge exactly once. This circuit serves as our list.

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

### Algorithm Complexity & Implementation
*   **Complexity**: 
    *   **Work**: $O(n)$ (Linear, assuming the underlying list scan is work-optimal).
    *   **Span**: $O(\log n)$. 
    *   *Crucial Insight:* The span depends **only** on the length of the list (which is $2n-2$), completely independent of the tree's shape! Even highly unbalanced, deep, stringy trees are processed just as efficiently and quickly as perfectly balanced binary trees.
*   **Implementation Details**:
    *   **Adjacency Table**: Represent the tree such that each vertex $v$ maintains an adjacency list of its $d_v$ outgoing neighbors.
    *   **Successor Function $S$**: Defines the traversal mathematically. For an edge $(u_i, v)$, $S(u_i, v) = (v, u_{(i+1) \pmod{d_v}})$. This effectively flips the relative position and advances circularly to the next neighbor, ensuring we "wrap around" the node correctly.
    *   **Cross-Edge Pointers**: To ensure the successor function computes in $O(1)$ constant time (without having to search the adjacency list), the adjacency list must be augmented with cross-edge pointers during creation.