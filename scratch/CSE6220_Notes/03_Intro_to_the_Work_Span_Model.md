# Introduction to the Work-Span Model

**Background Context**: Before writing parallel code, we need a way to reason about its performance and theoretical limits. Just as Big-O notation helps us analyze the time and space complexity of sequential algorithms, the **Work-Span model** is our theoretical framework for parallel algorithms. It gives us a mathematical way to understand the limits of parallel execution, regardless of whether our code runs on a dual-core laptop or a massive supercomputer with thousands of nodes.

---

## 1. The Multithreaded DAG Model

**Intuition**: Think of executing a complex project, like cooking a multi-course meal or building a house. Some tasks depend on others (you can't bake the cake before mixing the batter), while some can happen simultaneously (you can chop veggies while the water boils). We can map this process out as a graph.

- **Dynamic Multithreading Model**: A parallel computation is represented as a Directed Acyclic Graph (DAG).
  - **Vertices**: Computational tasks or operations (e.g., an addition, a function call, or a single instruction).
  - **Edges**: Dependencies. A task cannot start until all of its predecessors (incoming edges) have finished.
  - **Simplification**: We assume exactly one start vertex (the beginning of the program) and one exit vertex (the end).
- **Execution on a PRAM (Parallel Random Access Machine)**: This is our idealized parallel computer model.
  - **Scheduling**: The process of taking "ready" tasks (where all input dependencies are satisfied) and dynamically assigning them to free processors.
- **Cost Model Assumptions**: To keep the math clean, we assume:
  - All processors run at the exact same speed.
  - Each operation (vertex) takes exactly one unit of time.
  - Edges (dependencies) have no cost. In this idealized model, we assume **zero communication cost** between processors (though in reality, memory access and network latency matter).

---

## 2. Work and Span

These are the two most important metrics in parallel computing.

**Mental Model**:
- **Work**: If you were the *only* chef in the kitchen, how long would it take you to cook the entire meal doing one thing at a time?
- **Span**: If you had an *infinite* number of helper chefs, how fast could the meal be ready? Even with infinite helpers, you are still bottlenecked by the longest sequence of dependent steps (e.g., preheat oven $\rightarrow$ mix $\rightarrow$ bake $\rightarrow$ cool $\rightarrow$ frost). You can't speed up this chain.

For any computational DAG:
- **Work ($W(n)$)**: The total number of vertices (operations) in the DAG. It corresponds to the execution time on a single processor ($T_1 = W$).
- **Span ($D(n)$)**: The length of the longest path through the DAG, known as the **critical path**. Historically, this was called *depth*. It corresponds to the execution time given an infinite number of processors ($T_\infty = D$).
- **Average Available Parallelism**: Defined as the ratio $W(n) / D(n)$. It represents the average amount of work available per step of the critical path (i.e., on average, how many processors can you keep busy at any given time?).

### Basic Work-Span Laws
Given $P$ processors, what is our parallel execution time, $T_P(n)$? We can establish absolute lower bounds:
- **The Span Law**: $T_P \ge D(n)$. Time cannot be shorter than the critical path, even with infinite processors.
- **The Work Law**: $T_P \ge \lceil W(n) / P \rceil$. The total work must be distributed among $P$ processors. If you have 100 tasks and 4 processors, it will take at least 25 steps.
- **Combined Law**: Combining the two, the execution time is strictly bounded by the maximum of these two limits:
  $$ T_P \ge \max\left(D(n), \left\lceil \frac{W(n)}{P} \right\rceil\right) $$

---

## 3. Brent's Theorem

The Work-Span laws give us lower bounds (the absolute fastest we can go). But what about an upper bound? If we have a finite $P$ processors, what's the worst-case time? **Brent's Theorem** provides this **upper bound** on the execution time $T_P$ for a DAG on a $P$-processor PRAM:

$$ T_P \le D(n) + \frac{W(n) - D(n)}{P} $$

**Derivation Insight**:
Imagine packing rectangular blocks of work into boxes of size $P$ (since $P$ processors can do at most $P$ work per step).
1. Divide the DAG execution into $D(n)$ phases, where each phase contains exactly one critical path vertex.
2. All non-critical vertices in a given phase are independent of each other and can be run in parallel.
3. If phase $k$ has $W_k$ total work, its execution time on $P$ processors is $\lceil W_k / P \rceil \le \frac{W_k - 1}{P} + 1$.
4. Summing this execution time across all $D(n)$ phases (and using the fact that $\sum W_k = W$) mathematically yields the theorem.

**Slack in Brent's Bound**:
Brent's upper bound and the Work-Span lower bounds are always within a factor of 2 of each other. This is incredibly powerful: it means our theoretical model is very tight. The exact difference between the theoretical bound and actual execution time in the real world depends heavily on the **scheduler's efficiency** in dynamically packing work into these phases without leaving processors idle.

---

## 4. Algorithm Design Desiderata

What makes a parallel algorithm "good"?

### Speedup
- **Speedup ($S_P$)**: Defines how much faster we are going with $P$ processors. $S_P = \frac{T^*}{T_P}$, where $T^*$ is the *best known sequential time* (or sequential work, $W^*$) and $T_P$ is our parallel time.
- **Ideal/Linear Scaling**: We want $S_P = \Theta(P)$. If we double the processors, the program should ideally run twice as fast. For this to happen, the denominator of our speedup (derived via Brent's Theorem) must remain constant relative to $P$.

### Two Fundamental Principles
1. **Work-Optimality**: The parallel work $W(n)$ must match the best sequential work $W^*(n)$ asymptotically.
   - *Intuition*: If a sequential algorithm takes 100 steps, but your parallel version takes 10,000 steps just to make it highly parallelizable, it's a terrible algorithm! You might employ 100 processors and still be slower than the 1-processor sequential version. A parallel algorithm that inflates total work to achieve parallelism will ultimately hurt speedup.
2. **Weak Scalability**: To maintain linear scaling, $W^* / P$ (the amount of work per processor) must grow proportionally to the span $D(n)$ (i.e., $\Omega(D(n))$). Thus, as the number of processors $P$ increases, the problem size $n$ usually needs to increase to keep efficiency high and processors busy.

### The "Holy Grail" of Parallel Algorithms
When designing algorithms, aim for a DAG that is **"short and wide"**.
- **Work**: Match the best sequential work (e.g., $O(n)$). (Don't do extra work!)
- **Span**: Achieve **polylogarithmic span** (e.g., $O(\log n)$ or $O(\log^2 n)$). (Keep the critical path extremely short!)

---

## 5. Concurrency Primitives

The Work-Span model elegantly separates **how to express concurrency** (producing the DAG) from **how to execute it** (the hardware and scheduler). To write code, we need keywords to tell the compiler what can run in parallel.

- **`spawn`**: A keyword preceding a function or procedure call indicating it is an independent unit of work. It creates a new branch in the DAG (one path for the newly spawned call, one for the continuation of the caller).
- **`sync`**: Acts as a barrier. It waits for any `spawn` that has occurred so far *within the same stack frame* to finish before proceeding.
  - There is always an **implicit `sync`** at the return of any function.
  - This hierarchical structure produces **nested parallelism**, which is very easy to reason about and schedule efficiently.

**Example**:
```text
function fib(n):
  if n < 2 return n
  x = spawn fib(n-1)  // Branch 1: compute fib(n-1) in parallel
  y = fib(n-2)        // Branch 2: caller continues to compute fib(n-2)
  sync                // Wait for Branch 1 to finish
  return x + y
```

### Parallel For-Loops (`par-for`)
- Expresses that all iterations of a loop are completely independent and can be executed concurrently.
- **Implementation & Span**:
  - *Naïve Approach*: A loop using sequential `spawn`s (e.g., thread 1 spawns thread 2, then thread 3...) yields a linear span $O(n)$. It takes $n$ steps just to spawn the workers!
  - *Proper Approach*: A proper implementation uses a **divide-and-conquer** approach behind the scenes. Thread 1 spawns 2, those 2 spawn 4, those 4 spawn 8. This binary tree of spawns results in a **logarithmic span $O(\log n)$** (assuming constant-time loop bodies). *Always assume the divide-and-conquer implementation in analysis.*

### Vector Slicing Notation
- Operations on array slices (e.g., `t[1:n] = A[i, 1:n] * x[1:n]`) imply independent, element-wise operations.
- Because they map directly to `par-for` loops, they have linear work $O(n)$ and logarithmic span $O(\log n)$.

---

## 6. Analysis Examples

### Divide and Conquer Reduction
**Scenario**: Summing an array of $n$ numbers using a divide-and-conquer strategy (which forms a binary tree DAG).
- **Work Analysis**: Analyzed identically to sequential algorithms (we just ignore the `spawn`/`sync` keywords).
  - Recurrence: $W(n) = 2W(n/2) + O(1)$
  - Solution: $W(n) = O(n)$. (This is **Work-optimal** because sequentially summing an array also takes $O(n)$ time).
- **Span Analysis**: Span follows the longest path (the maximum depth of the recursive branches).
  - Recurrence: $D(n) = D(n/2) + O(1)$ (because branches happen in parallel, we don't add them; we take the max, plus $O(1)$ for the merge/add step).
  - Solution: $D(n) = O(\log n)$. (This achieves the "Holy Grail" of polylogarithmic span!).

### Matrix-Vector Multiply
**Scenario**: Computing $y = y + Ax$ (where $A$ is an $n \times n$ matrix, and $x, y$ are vectors of size $n$).
- **Data Races and Race Conditions**:
  - **Data Race**: Occurs when $\ge 1$ read and $\ge 1$ write to the exact same memory location happen simultaneously across different threads.
  - **Race Condition**: A data race that causes incorrect program behavior (e.g., lost updates).
  - *The Danger*: In a nested loop for Matrix-Vector multiply, making the inner loop (`j`) a `par-for` creates a massive race condition because multiple concurrent iterations will try to update the exact same $y_i$ variable at the same time.

- **Parallelization Strategy 1 (Safe but slow span)**:
  - Approach: Use `par-for` on the outer loop (`i`), but a sequential `for` on the inner loop (`j`).
  - Work: $O(n^2)$ (optimal, as there are $n^2$ matrix elements).
  - Span: $O(n)$ (because the inner sequential loop takes $n$ steps).

- **Parallelization Strategy 2 (Fastest, using reductions)**:
  - Approach: Use `par-for` on the outer loop. For the inner loop, also use a `par-for`, but have each thread store its multiplication result into a temporary array. Then, perform a parallel tree reduction (like the array sum above) to safely add them up.
  - Work: $O(n^2)$ (still optimal).
  - Span: $O(\log n)$ (Because the inner loop and the reduction both take $O(\log n)$ span, giving us much better average available parallelism).

---

## 7. Conclusion

- **The ideal shape**: Good parallel algorithms are work-optimal and have low (polylogarithmic) span. Think of the DAG as a person who is short and wide, rather than tall and skinny.
- **The primary tool**: Divide and conquer is the absolute most important paradigm for parallel algorithm design, as it naturally produces optimal work and logarithmic span.
- **Model strengths & weaknesses**: The Dynamic Multithreading model beautifully separates the expression of concurrency from its execution. However, it notably abstracts away communication and memory access costs, which are critical factors to consider in real-world HPC (High Performance Computing) implementations.
