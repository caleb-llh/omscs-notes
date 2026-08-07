# Scans and List Ranking: Comprehensive Notes

## 1. Introduction to Parallel Algorithms

**Background & Context**: 
When moving from sequential programming to parallel programming, the biggest hurdle is often data dependency. In sequential algorithms, it's natural to compute step $i$ using the result of step $i-1$. In parallel algorithms, we want to compute many steps simultaneously, which forces us to rethink our entire approach to problem-solving.

> **Background Context:** Sequential algorithms rely heavily on temporal coupling—where the present state is entirely dependent on the immediate past. Breaking this coupling is the essence of parallel algorithm design, shifting from a "step-by-step" paradigm to a "divide-and-conquer" or "global-update" paradigm.

- **The Core Challenge (A Mental Model)**: Imagine a line of 10 million people holding hands. You want to know your position in the line, but you only know who is immediately ahead of or behind you. Sequentially, a message passed from the front to the back (e.g., "You are person 1, you are person 2...") could take days. How can we find everyone's position simultaneously? Some computations appear inherently and purely sequential just like this.

> **Hypothetical:** What if, instead of passing a message one by one, every person asked the person next to them simultaneously, and then asked the person two spots away, then four? This leap in logic turns an $O(N)$ sequential bottleneck into a logarithmic parallel solution, hinting at the power of pointer jumping.

- **List Ranking Problem**: Given a singly linked list and a pointer to its head, compute the distance (position or rank) of every node from the head. While sequentially this is a trivial $O(N)$ time operation (just walk the list and count), it is notoriously difficult to parallelize because linked lists inherently restrict random access. You can't just jump to the middle of the list!

> **Common Confusion:** It's easy to confuse the list ranking problem on a linked list with array index calculations. Unlike arrays where index arithmetic provides $O(1)$ random access, a linked list node only knows its immediate successor. The memory addresses are non-contiguous, meaning you cannot deduce your position simply by looking at your memory location.

> **Fact Check:** List ranking is formally defined as computing the distance of each node to the *end* (or head) of the list. Sequential list ranking is indeed strictly $O(N)$ work and $O(N)$ span since pointer traversal strictly serializes memory accesses. Wyllie's algorithm (pointer jumping) was one of the first parallel solutions, requiring $O(N \log N)$ work.

## 2. Prefix Sums and Scans

**Intuition**: A "scan" is essentially a running total, but generalized to operations other than addition. If you've ever kept a running tally of scores in a game, you've computed a scan.

> **Intuition:** Think of a scan as capturing the "cumulative history" of a sequence up to every single point in time, producing an entire timeline of states rather than just a single final result (which would just be a reduction).

- **Prefix Sum**: For an array $A$, the prefix sum at position $i$ is the sum of all elements from $A[1]$ up to $A[i]$.
  - *Example*: `A = [1, 2, 3, 4]` $\rightarrow$ `PrefixSum = [1, 3, 6, 10]`.
- **Scans**: The generalization of a prefix sum. A scan takes an array and a specific operator.
  - *Examples*: Add-scan (`+`), Max-scan (`max`), Product-scan (`*`), Logical-OR-scan (`|`).
  - *Example of Max-scan*: `[1, 5, 3, 7, 2]` $\rightarrow$ `[1, 5, 5, 7, 7]`.
  - *Application (Line of Sight)*: Imagine you are walking on a terrain. A max-scan over the terrain's elevations can determine your line-of-sight visibility. If the max elevation seen so far is $\le$ the observer's height, you can see that far; otherwise, your view is blocked.

> **Example:** In financial data analysis, a product-scan over daily return multipliers yields the cumulative return over time. In compilers, a logical-OR-scan can track if a certain error condition has ever been met up to a specific line of code.

> **Fact Check:** In the literature, scans are categorized as "inclusive" (where the result at index $i$ includes $A[i]$) or "exclusive" (where the result at index $i$ only includes up to $A[i-1]$, often starting with an identity element). The examples given (`A = [1, 2, 3, 4]` $\rightarrow$ `PrefixSum = [1, 3, 6, 10]`) illustrate an inclusive scan. Exclusive scans are sometimes preferred in parallel algorithms (like conditional gather) because the scan array directly acts as base offsets.

- **Sequential Scan**: Easily computed in-place in $O(N)$ work by accumulating the previous value (`A[i] = A[i-1] + A[i]`).
- **Naive Parallel Scan**: Replacing the sequential loop with a `parallel for` completely fails because iteration $i$ depends on the result of iteration $i-1$. If we try to compute $N$ independent parallel reductions (each thread computing its own prefix from the start), we achieve an $O(\log N)$ span but a terrible $O(N^2)$ total work, which is highly inefficient and defeats the purpose of parallelism.

> **Tradeoff:** The naive approach trades an explosion in total computational work ($O(N^2)$) for a reduction in span ($O(\log N)$). In parallel computing, a non-work-optimal algorithm often runs slower in practice than a sequential one because the sheer volume of redundant calculations overwhelms the available processors.

## 3. The Parallel Scan Algorithm

**Mental Model**: Think of the parallel scan like a tournament bracket (a binary tree) that works in two phases: it first goes *up* the tree to summarize data, and then goes *down* the tree to distribute the running totals.

> **Mental Model:** It's similar to a corporate hierarchy summarizing budget requests. First, individual requests are combined by middle managers, going up to the CEO (the reduction phase). Then, the CEO allocates the final cumulative budgets back down the chain (the down-sweep phase) so each department knows its exact cumulative funding tier.

To efficiently parallelize a scan, the underlying operator **must be associative** (e.g., $(a+b)+c = a+(b+c)$). This allows us to safely rearrange the order of partial operations without changing the final result.

- **Algorithm Steps**:
  1. **Pairwise Reduction**: In parallel, combine adjacent elements (e.g., $A[2i-1] + A[2i]$) to form consecutive partial results. This effectively halves the size of the array.
  2. **Recursive Scan**: Recursively apply the parallel scan on this halved array of partial sums. This magical recursive step provides the correct final scan results for all **even** indices of the original array!
  3. **Odd Index Derivation**: To find the scan result for an odd index, simply take the preceding even index's result (which we just computed) and add the original odd element.
  
> **Common Confusion:** Why does the recursive step only yield correct results for the *even* indices? Because in our pairwise reduction, each even index $2i$ absorbs the value of its preceding odd index $2i-1$. Thus, the cumulative sum up to $2i$ in the compressed array perfectly matches the cumulative sum up to $2i$ in the original array.

  *Concrete Example*:
  - Start: `A = [1, 2, 3, 4, 5, 6, 7, 8]`
  - 1. Pairwise: `[3, 7, 11, 15]`
  - 2. Recursive Scan: `[3, 10, 21, 36]` (These are exactly the correct prefix sums for indices 2, 4, 6, and 8!)
  - 3. Odd Derivation: For index 3, take `Result[2]` (which is 3) and add `A[3]` (which is 3) to get `6`. 

- **Complexity**:
  - **Span**: $O(\log^2 N)$ — The recurrence tree has $O(\log N)$ depth, and each level executes a parallel `for` with $O(\log N)$ span.
  - **Work**: $O(N)$ — Linear work! The algorithm performs about twice as many addition operations as the sequential version (a constant factor $\approx 2$), but remains asymptotically work-optimal. This is a huge victory over the naive $O(N^2)$ approach.

> **Tradeoff:** We willingly accept a slightly larger constant factor in total operations (roughly $2N$ additions instead of $N$) to gain a massively parallelizable structure. This highlights a fundamental principle of parallel algorithm design: optimizing for span often requires a modest increase in total work.

> **Fact Check:** The algorithm described here is closely related to the Brent-Kung scan algorithm, originally proposed for circuit design. A variant by Blelloch uses an explicit Up-Sweep (reduce) and Down-Sweep phase, which is highly efficient for SIMD architectures like GPUs. The described recurrence yields $O(\log^2 N)$ span on a strict PRAM model without concurrent writes, but can achieve $O(\log N)$ span if the underlying parallel `for` can execute in $O(1)$ span (e.g., with concurrent execution models). The work bound of $O(N)$ is strictly optimal.

## 4. Conditional Gathers and Parallel Quicksort

**Background**: Suppose you want to filter an array (e.g., finding all numbers $\le 4$). In a sequential loop, you'd maintain a `counter` and write `output[counter++] = element`. In parallel, $N$ threads cannot all safely increment a shared `counter` without massive lock contention and race conditions. How do threads know *where* to write their output?

> **Background Context:** In sequential code, memory allocation and placement are often implicitly handled by simple incrementing pointers. In the parallel world, dynamic, data-dependent memory placement is a major bottleneck. Conditional gathers bridge this gap by pre-computing exact memory destinations before any data is actually moved.

- **Sequential Quicksort Partitioning**: Choosing a pivot and partitioning elements into $\le$ pivot and $>$ pivot is straightforward sequentially but challenging to do in parallel without lock contention on shared index variables.
- **Scan-Based Conditional Gather (`gatherIf`)**:
  This is a brilliant technique to assign conflict-free output indices in parallel.
  - **Step 1 (Flags)**: Compare each element to the pivot in parallel. Store `1` if the condition is met ($\le$ pivot), else `0`.
  - **Step 2 (Scan)**: Perform an add-scan on the `0/1` flag array.
    - The last element of the scan gives the total number of matching elements (useful for memory allocation).
    - The scan output provides **unique, consecutive integers (1-based indices)** for every element where the flag is `1`.
  - **Step 3 (Scatter/Write)**: Using a parallel `for`, elements with a flag of `1` are written directly into the output array using their corresponding scan value as their exclusive, conflict-free index.
  
> **Example:** Consider a database query filtering users by age. Step 1 marks matching users with `1`. Step 2 computes exactly which slot in the final result array each matching user should occupy. Step 3 places them there simultaneously. This pattern is ubiquitous in GPU programming (often called stream compaction).

  *Concrete Example (Filter $\le 4$)*:
  - Input: `[3, 8, 2, 5, 1, 9]`
  - Step 1 (Flags): `[1, 0, 1, 0, 1, 0]`
  - Step 2 (Scan): `[1, 1, 2, 2, 3, 3]`
  - Step 3: The `3` gets index `1`, the `2` gets index `2`, the `1` gets index `3`. Output array becomes `[3, 2, 1]`.
- **Significance**: This primitive transforms a potentially highly-contentious parallel write operation into a structured, conflict-free routine with $O(N)$ work and $O(\log^2 N)$ span.

> **Fact Check:** The `gatherIf` operation (often called stream compaction or `filter` in parallel programming libraries) effectively implements a stable partition if the original array order is preserved. The scan in Step 2 needs to be an *inclusive* scan to yield 1-based indices, or an *exclusive* scan to yield 0-based indices. Most practical implementations (e.g., CUDA thrust, CUDA CUB) use exclusive scans for 0-indexed arrays like in C/C++.

## 5. Segmented Scans

**Intuition**: Imagine you have multiple separate arrays, but to process them efficiently on a GPU or parallel system, you pack them all into one giant array. A "segmented scan" allows you to perform independent scans on these contiguous segments simultaneously, without the totals bleeding over from one segment to the next.

> **Hypothetical:** What if you had millions of small, variable-length arrays (e.g., sentences in a document) and needed a prefix sum for each? Launching millions of tiny parallel kernels would suffer from massive scheduling overhead. Packing them into one array and using a segmented scan processes them all in a single, highly efficient pass.

- **Concept**: Performing independent scans on contiguous segments of a single array, defined by an auxiliary boolean flag array (where `true` marks the start of a new segment).
- **Custom Operator Approach**:
  We can solve this using the standard parallel scan, just by defining a clever custom operator!
  - Define a new data type (a tuple): $X_i = (A_i, flag_i)$.
  - Define a custom operator `op(X, Y)`:
    - If `Y.flag` is `false` (not a new segment), combine them: `return (X.val + Y.val, X.flag | Y.flag)`.
    - If `Y.flag` is `true` (a new segment starts at Y), reset and ignore X: `return (Y.val, Y.flag)`.
- **Proof of Correctness**: For this custom operator to work in the standard parallel scan algorithm, it must be **associative**. The beauty of this approach is that it does *not* need to be commutative, in-place, or constant-cost for functional correctness—as long as $(X \text{ op } Y) \text{ op } Z = X \text{ op } (Y \text{ op } Z)$, the math holds up perfectly.

> **Common Confusion:** It might feel counterintuitive that ignoring `X` when `Y.flag` is true still preserves associativity. The trick is that if `Y.flag` is true, it represents a hard boundary; anything to its left (`X`) cannot possibly influence anything to its right, making the operation associative regardless of how we group the terms.

> **Fact Check:** Segmented scans were pioneered by Guy Blelloch as a fundamental primitive for nested data-parallelism (e.g., in the NESL language). The custom operator formulation strictly preserves associativity, mapping the problem exactly onto the standard scan algorithm. This is formally known as a monoid under the specified operation, where the identity element would be $(0, \text{false})$.

## 6. Parallel List Ranking

**Background**: As mentioned earlier, linked lists are the enemy of parallelism. To parallelize list ranking, we must abandon traditional pointer-based memory architectures and view the problem as a specialized scan over an array.

> **Intuition:** We are essentially "flattening" the graph structure of the linked list into a format where data-parallel hardware can operate on all nodes simultaneously, trading the conceptual simplicity of pointers for the parallel power of arrays.

- **Array Pool Representation**:
  Instead of scattered memory allocations, we pack the linked list into arrays.
  - A linked list is mapped to parallel arrays: $V$ for values and $N$ for next-pointers.
  - Next-pointers store array indices rather than memory addresses (e.g., `N[3] = 7` means the node at index 3 points to the node at index 7).
  - This provides $O(1)$ random access to list nodes, enabling data-parallel operations across the entire list simultaneously.
- **List Ranking as a Scan**:
  - Initialize the head node with a value of `0` and all other nodes with `1`.
  - A scan over these values yields the exact distance of each node from the head.
- **Pointer Jumping (Divide and Conquer)**:
  **Mental Model**: Imagine everyone in a line is pointing at the person directly behind them. In one step, everyone simultaneously updates their pointing finger to point at the person *their target* was pointing at. After one step, everyone points to the person 2 spots away. After two steps, 4 spots away. After $\log N$ steps, everyone is pointing to the end of the line!
  - In parallel, update every node's next-pointer to point to its neighbor's neighbor (`N[i] = N[N[i]]`).
  - A single "jump step" effectively splits the list into two interleaved sublists.
  - Repeating this $O(\log N)$ times breaks the list down into fully isolated individual nodes.

> **Example:** Consider nodes A $\rightarrow$ B $\rightarrow$ C $\rightarrow$ D. After one pointer jump step, A points to C, and B points to D. The list has implicitly split into two separate paths: A $\rightarrow$ C and B $\rightarrow$ D, cutting the effective depth of the list in half!

- **The Parallel Algorithm**:
  - **Invariant**: The sum of values from a node to the end of its current sublist equals its final rank.
  - **Step 1 (Push/Update)**: Before jumping, a node pushes its value to its successor to preserve the invariant (`Rank[N[i]] += Rank[i]`).
  - **Step 2 (Jump)**: Nodes update their pointers to their neighbor's neighbor (`N[i] = N[N[i]]`).
  - **Double Buffering**: Because nodes are reading and writing concurrently, you can't just overwrite arrays in place. Alternating between two copies of the rank and next-pointer arrays prevents data races and write collisions.
- **Complexity**:
  - **Span**: $O(\log^2 N)$ — There are $O(\log N)$ jump steps, and each jump utilizes parallel operations with $O(\log N)$ span.
  - **Work**: $O(N \log N)$ — The algorithm performs $O(N)$ work at each of the $O(\log N)$ jump steps.
  - **Conclusion**: Because the work is $O(N \log N)$, this specific list ranking algorithm is **not work-optimal** compared to the $O(N)$ sequential version. The logarithmic overhead and extra buffer management mean you need very long lists and a massive number of processors to achieve a practical speedup. However, it serves as a beautiful conceptual foundation, and optimal $O(N)$ work parallel algorithms do exist (often combining pointer jumping with list-contraction techniques).

> **Tradeoff:** The $O(N \log N)$ pointer jumping algorithm illustrates a classic tension in parallel computing: achieving a massive reduction in span (from $O(N)$ to $O(\log^2 N)$) by accepting non-optimal work. For very large datasets on architectures with enough processors, this tradeoff is sometimes acceptable, though work-optimal variants are preferred in practice.

> **Fact Check:** Wyllie's pointer jumping algorithm achieves $O(\log N)$ span and $O(N \log N)$ work. To achieve an optimal $O(N)$ work and $O(\log N)$ span algorithm, one must use randomized techniques (like independent set removal) or deterministic coin tossing (Cole-Vishkin algorithm) to perform list contraction before applying pointer jumping on a reduced list.
