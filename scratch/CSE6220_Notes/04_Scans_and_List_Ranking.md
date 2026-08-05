# Scans and List Ranking: Comprehensive Notes

## 1. Introduction to Parallel Algorithms

**Background & Context**: 
When moving from sequential programming to parallel programming, the biggest hurdle is often data dependency. In sequential algorithms, it's natural to compute step $i$ using the result of step $i-1$. In parallel algorithms, we want to compute many steps simultaneously, which forces us to rethink our entire approach to problem-solving.

- **The Core Challenge (A Mental Model)**: Imagine a line of 10 million people holding hands. You want to know your position in the line, but you only know who is immediately ahead of or behind you. Sequentially, a message passed from the front to the back (e.g., "You are person 1, you are person 2...") could take days. How can we find everyone's position simultaneously? Some computations appear inherently and purely sequential just like this.
- **List Ranking Problem**: Given a singly linked list and a pointer to its head, compute the distance (position or rank) of every node from the head. While sequentially this is a trivial $O(N)$ time operation (just walk the list and count), it is notoriously difficult to parallelize because linked lists inherently restrict random access. You can't just jump to the middle of the list!

## 2. Prefix Sums and Scans

**Intuition**: A "scan" is essentially a running total, but generalized to operations other than addition. If you've ever kept a running tally of scores in a game, you've computed a scan.

- **Prefix Sum**: For an array $A$, the prefix sum at position $i$ is the sum of all elements from $A[1]$ up to $A[i]$.
  - *Example*: `A = [1, 2, 3, 4]` $\rightarrow$ `PrefixSum = [1, 3, 6, 10]`.
- **Scans**: The generalization of a prefix sum. A scan takes an array and a specific operator.
  - *Examples*: Add-scan (`+`), Max-scan (`max`), Product-scan (`*`), Logical-OR-scan (`|`).
  - *Example of Max-scan*: `[1, 5, 3, 7, 2]` $\rightarrow$ `[1, 5, 5, 7, 7]`.
  - *Application (Line of Sight)*: Imagine you are walking on a terrain. A max-scan over the terrain's elevations can determine your line-of-sight visibility. If the max elevation seen so far is $\le$ the observer's height, you can see that far; otherwise, your view is blocked.
- **Sequential Scan**: Easily computed in-place in $O(N)$ work by accumulating the previous value (`A[i] = A[i-1] + A[i]`).
- **Naive Parallel Scan**: Replacing the sequential loop with a `parallel for` completely fails because iteration $i$ depends on the result of iteration $i-1$. If we try to compute $N$ independent parallel reductions (each thread computing its own prefix from the start), we achieve an $O(\log N)$ span but a terrible $O(N^2)$ total work, which is highly inefficient and defeats the purpose of parallelism.

## 3. The Parallel Scan Algorithm

**Mental Model**: Think of the parallel scan like a tournament bracket (a binary tree) that works in two phases: it first goes *up* the tree to summarize data, and then goes *down* the tree to distribute the running totals.

To efficiently parallelize a scan, the underlying operator **must be associative** (e.g., $(a+b)+c = a+(b+c)$). This allows us to safely rearrange the order of partial operations without changing the final result.

- **Algorithm Steps**:
  1. **Pairwise Reduction**: In parallel, combine adjacent elements (e.g., $A[2i-1] + A[2i]$) to form consecutive partial results. This effectively halves the size of the array.
  2. **Recursive Scan**: Recursively apply the parallel scan on this halved array of partial sums. This magical recursive step provides the correct final scan results for all **even** indices of the original array!
  3. **Odd Index Derivation**: To find the scan result for an odd index, simply take the preceding even index's result (which we just computed) and add the original odd element.
  
  *Concrete Example*:
  - Start: `A = [1, 2, 3, 4, 5, 6, 7, 8]`
  - 1. Pairwise: `[3, 7, 11, 15]`
  - 2. Recursive Scan: `[3, 10, 21, 36]` (These are exactly the correct prefix sums for indices 2, 4, 6, and 8!)
  - 3. Odd Derivation: For index 3, take `Result[2]` (which is 3) and add `A[3]` (which is 3) to get `6`. 

- **Complexity**:
  - **Span**: $O(\log^2 N)$ — The recurrence tree has $O(\log N)$ depth, and each level executes a parallel `for` with $O(\log N)$ span.
  - **Work**: $O(N)$ — Linear work! The algorithm performs about twice as many addition operations as the sequential version (a constant factor $\approx 2$), but remains asymptotically work-optimal. This is a huge victory over the naive $O(N^2)$ approach.

## 4. Conditional Gathers and Parallel Quicksort

**Background**: Suppose you want to filter an array (e.g., finding all numbers $\le 4$). In a sequential loop, you'd maintain a `counter` and write `output[counter++] = element`. In parallel, $N$ threads cannot all safely increment a shared `counter` without massive lock contention and race conditions. How do threads know *where* to write their output?

- **Sequential Quicksort Partitioning**: Choosing a pivot and partitioning elements into $\le$ pivot and $>$ pivot is straightforward sequentially but challenging to do in parallel without lock contention on shared index variables.
- **Scan-Based Conditional Gather (`gatherIf`)**:
  This is a brilliant technique to assign conflict-free output indices in parallel.
  - **Step 1 (Flags)**: Compare each element to the pivot in parallel. Store `1` if the condition is met ($\le$ pivot), else `0`.
  - **Step 2 (Scan)**: Perform an add-scan on the `0/1` flag array.
    - The last element of the scan gives the total number of matching elements (useful for memory allocation).
    - The scan output provides **unique, consecutive integers (1-based indices)** for every element where the flag is `1`.
  - **Step 3 (Scatter/Write)**: Using a parallel `for`, elements with a flag of `1` are written directly into the output array using their corresponding scan value as their exclusive, conflict-free index.
  
  *Concrete Example (Filter $\le 4$)*:
  - Input: `[3, 8, 2, 5, 1, 9]`
  - Step 1 (Flags): `[1, 0, 1, 0, 1, 0]`
  - Step 2 (Scan): `[1, 1, 2, 2, 3, 3]`
  - Step 3: The `3` gets index `1`, the `2` gets index `2`, the `1` gets index `3`. Output array becomes `[3, 2, 1]`.
- **Significance**: This primitive transforms a potentially highly-contentious parallel write operation into a structured, conflict-free routine with $O(N)$ work and $O(\log^2 N)$ span.

## 5. Segmented Scans

**Intuition**: Imagine you have multiple separate arrays, but to process them efficiently on a GPU or parallel system, you pack them all into one giant array. A "segmented scan" allows you to perform independent scans on these contiguous segments simultaneously, without the totals bleeding over from one segment to the next.

- **Concept**: Performing independent scans on contiguous segments of a single array, defined by an auxiliary boolean flag array (where `true` marks the start of a new segment).
- **Custom Operator Approach**:
  We can solve this using the standard parallel scan, just by defining a clever custom operator!
  - Define a new data type (a tuple): $X_i = (A_i, flag_i)$.
  - Define a custom operator `op(X, Y)`:
    - If `Y.flag` is `false` (not a new segment), combine them: `return (X.val + Y.val, X.flag | Y.flag)`.
    - If `Y.flag` is `true` (a new segment starts at Y), reset and ignore X: `return (Y.val, Y.flag)`.
- **Proof of Correctness**: For this custom operator to work in the standard parallel scan algorithm, it must be **associative**. The beauty of this approach is that it does *not* need to be commutative, in-place, or constant-cost for functional correctness—as long as $(X \text{ op } Y) \text{ op } Z = X \text{ op } (Y \text{ op } Z)$, the math holds up perfectly.

## 6. Parallel List Ranking

**Background**: As mentioned earlier, linked lists are the enemy of parallelism. To parallelize list ranking, we must abandon traditional pointer-based memory architectures and view the problem as a specialized scan over an array.

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
- **The Parallel Algorithm**:
  - **Invariant**: The sum of values from a node to the end of its current sublist equals its final rank.
  - **Step 1 (Push/Update)**: Before jumping, a node pushes its value to its successor to preserve the invariant (`Rank[N[i]] += Rank[i]`).
  - **Step 2 (Jump)**: Nodes update their pointers to their neighbor's neighbor (`N[i] = N[N[i]]`).
  - **Double Buffering**: Because nodes are reading and writing concurrently, you can't just overwrite arrays in place. Alternating between two copies of the rank and next-pointer arrays prevents data races and write collisions.
- **Complexity**:
  - **Span**: $O(\log^2 N)$ — There are $O(\log N)$ jump steps, and each jump utilizes parallel operations with $O(\log N)$ span.
  - **Work**: $O(N \log N)$ — The algorithm performs $O(N)$ work at each of the $O(\log N)$ jump steps.
  - **Conclusion**: Because the work is $O(N \log N)$, this specific list ranking algorithm is **not work-optimal** compared to the $O(N)$ sequential version. The logarithmic overhead and extra buffer management mean you need very long lists and a massive number of processors to achieve a practical speedup. However, it serves as a beautiful conceptual foundation, and optimal $O(N)$ work parallel algorithms do exist (often combining pointer jumping with list-contraction techniques).
