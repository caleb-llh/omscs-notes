# Comparison-Based Sorting: Bitonic Sorting Networks

This document covers parallel algorithms for sorting within the dynamic multi-threading model, specifically focusing on the theory, mechanics, and hardware implementations of Bitonic Sorting Networks.

**Background Context:** In traditional software-based sorting (like Quick Sort or Merge Sort), the sequence of comparisons depends heavily on the input data itself. This introduces branch instructions, which can be slow and hard to parallelize perfectly. **Sorting networks** take a radically different approach: the sequence of comparisons is *fixed in advance*, entirely independent of the data. This data-agnostic nature makes sorting networks incredibly powerful for specialized hardware like GPUs or FPGAs.

---

## 1. Introduction to Sorting Networks
Traditional sorting algorithms are typically analyzed sequentially, but parallel sorting often relies on **sorting networks**. 

**Mental Model:** Think of a sorting network like a train yard where trains (data elements) run on parallel horizontal tracks (wires). At certain points, two tracks connect, and an automated switch (a comparator) routes the lighter train to one track and the heavier train to another. The layout of the tracks and switches is hardwired; it never changes regardless of what trains are passing through.

- **Sorting Network:** A fixed circuit that sorts its inputs using specialized circuit elements called **comparators**.
- **Comparators:** The fundamental building blocks of a sorting network. They take two inputs and produce two outputs:
  - **Plus (Increasing) Comparator:** Places the *smaller* of its two inputs on the top wire and the *larger* on the bottom wire.
  - **Minus (Decreasing) Comparator:** Places the *larger* of its two inputs on the top wire and the *smaller* on the bottom wire.
- **Circuit Analysis:** Just like analyzing sequential code, comparator circuits can be evaluated by:
  - **Work:** The total number of comparators in the circuit (analogous to the total number of operations).
  - **Span (Critical Path Length or Depth):** The longest dependency path of comparators from input to output. Because many comparators can operate simultaneously on different wires, span dictates the actual time the sorting takes when fully parallelized.

---

## 2. Bitonic Sequences
Before sorting arbitrary data, the algorithm relies on a specific structural pattern known as a bitonic sequence.

**Intuition:** Imagine a graph of the sequence's values. A bitonic sequence looks like a single mountain (going up, then down) or a single valley (going down, then up). This predictable geometric shape is the "secret sauce" that allows us to sort it so efficiently in parallel.

- **Definition:** A sequence of values is **bitonic** if it is initially non-decreasing and then becomes non-increasing (e.g., it goes up, then down). 
- **Formal Condition:** $x_0 \le x_1 \le \dots \le x_k \ge x_{k+1} \ge \dots \ge x_{n-1}$.
- **Circular Shift:** A sequence is also bitonic if the above "up and down" property holds for *any circular shift* of the sequence. 
  - *Example:* The sequence `[1, 3, 5, 4, 2]` is bitonic (a mountain). Its circular shift `[4, 2, 1, 3, 5]` is also bitonic (a valley).
- **Verification Method:** If you arrange the sequence values in a ring and calculate the differences between consecutive elements, a sequence is bitonic if and only if all the increases (pluses) are consecutive and all the decreases (minuses) are consecutive along the ring.

---

## 3. Bitonic Split
A bitonic split is the core operation for dividing a bitonic sequence into manageable subproblems.

**Mental Model:** Think of "folding" the mountain in half. If you overlay the first half of the sequence onto the second half and compare them point-by-point, you can easily separate the sequence into a "taller" half and a "shorter" half. Miraculously, both new halves remain bitonic!

- **Mechanism:** Given a bitonic sequence, conceptually divide it in half. Pair the $i$-th element of the first half with the $i$-th element of the second half.
- **Min/Max Separation:** 
  - Extracting the **minimum** of each pair yields a new bitonic subsequence.
  - Extracting the **maximum** of each pair yields a second bitonic subsequence.
- **Key Property:** Every element in the resulting "max" subsequence is strictly greater than or equal to every element in the "min" subsequence.
  - *Example:* Consider the bitonic sequence `[1, 3, 5, 8 | 7, 4, 2, 0]`. 
    - Pair them up: (1,7), (3,4), (5,2), (8,0).
    - Min sequence: `[1, 3, 2, 0]` (Still bitonic!)
    - Max sequence: `[7, 4, 5, 8]` (Still bitonic!)
    - Notice that every number in the max sequence is $\ge$ every number in the min sequence.
- **Implementation:** A bitonic split can be performed entirely in-place (without extra storage) by placing plus comparators across the paired elements. 

---

## 4. Bitonic Merge
A bitonic merge uses a divide-and-conquer approach to completely sort a bitonic sequence.

**Intuition:** Since a bitonic split perfectly divides our data into a "small half" and a "large half" (both of which are still bitonic mountains), we can just keep splitting them recursively. Once we split the mountains all the way down to size 1, the data is completely flattened out and perfectly sorted.

- **Algorithm:**
  1. **Split:** Apply a bitonic split to the input sequence, resulting in two independent bitonic subsequences (a "min" half and a "max" half).
  2. **Recurse:** Because all elements in the min half are $\le$ all elements in the max half, the two halves are completely independent. Recursively perform a bitonic split on both halves.
  3. **Parallelism:** The independence of the two subsequences allows them to be spawned and merged in parallel.
- **Network Construction:** For an input of size $N$, the first split pairs elements that are $N/2$ apart. The recursive splits then pair elements $N/4$ apart, then $N/8$, down to 1.

---

## 5. Bitonic Sort (Arbitrary Sequences)
To sort an arbitrary sequence, you cannot directly apply a bitonic merge; you must first convert the arbitrary sequence into a bitonic sequence.

**Mental Model:** Think of this as weaving a rug. You start with tiny, random threads. First, you weave pairs into tiny zig-zags (one pair goes up, the next goes down). Then you weave two zig-zags together to form a small mountain. You keep combining these shapes into larger and larger mountains until the entire dataset is one massive, single bitonic mountain. Then, you apply the Bitonic Merge to flatten it out into a sorted line.

- **Generating a Bitonic Sequence (`genBitonic`):**
  - Start by treating the input as a series of length-2 sequences. 
  - Run small bitonic merges of size 2, alternating between increasing (plus comparators) and decreasing (minus comparators). This creates up-and-down pairs, which form bitonic sequences of length 4.
  - Repeat the process using alternating bitonic merges of increasing size (size 4, then 8, etc.) until the entire input forms a single bitonic sequence.
- **Complete Bitonic Sort Workflow:**
  1. Run `genBitonic` (a series of progressively larger bitonic merges alternating between increasing/decreasing) to transform the arbitrary input into a bitonic sequence.
  2. Run a final, full-size `bitonicMerge` on the result to produce a fully sorted array.

---

## 6. Complexity and Hardware Tradeoffs
While Bitonic Sort is elegant, it has distinct performance characteristics compared to standard comparison-based algorithms (like Merge Sort or Quick Sort).

**Intuition:** Imagine hiring workers to build a wall. An optimal algorithm like Merge Sort is like having one incredibly efficient worker doing $O(n \log n)$ tasks. Bitonic Sort requires $O(n \log^2 n)$ total tasks—more total work! However, because Bitonic Sort's tasks are completely independent and predictable, you can hire 10,000 workers to do them all simultaneously. They do more work in total, but they finish the wall in a fraction of the time.

- **Span (Depth):** Polylogarithmic ($O(\log^2 n)$). It is extremely shallow, making it incredibly fast in highly parallel environments.
- **Work:** $O(n \log^2 n)$. Unlike optimal comparison-based algorithms that require $O(n \log n)$ work, Bitonic Sort does *more* total work.
- **Hardware Mapping (The Engineering Tradeoff):** 
  - Although it is not work-optimal, the fixed, regular parallel structure (a static DAG of independent comparators) makes it exceptionally well-suited for fixed data-parallel hardware.
  - It maps beautifully to **SIMD (Single Instruction, Multiple Data)** architectures, **Vector Processors**, **FPGAs**, and **GPUs**.
  - In practice, choosing Bitonic Sort over an $O(n \log n)$ algorithm is an engineering tradeoff: sacrificing theoretical work optimality to fully leverage massive hardware-level parallelism.
