# Basic Model of Locality

## 1. Introduction to Memory Hierarchies

**Background Context:**
If you look at the specifications of any modern computer, you'll see a CPU clock speed in gigahertz, but you'll also see various layers of memory: L1, L2, L3 caches, RAM, and an SSD or HDD. Why so many layers? Because in hardware design, we face a fundamental physics tradeoff: **you can have memory that is incredibly fast, or memory that is incredibly large, but not both.** 

- Real machines have a hierarchy of memories between the processor and primary storage (e.g., disk).
- Closer to processor = faster but smaller.
- Differences in size, latency, and bandwidth between levels can be orders of magnitude (e.g., L1 cache takes ~1 nanosecond, Main Memory takes ~100 nanoseconds, Disk takes millions of nanoseconds).
- Standard algorithmic models (like the classic RAM model used in Big-O notation) ignore memory size and speed. They assume every memory access takes $O(1)$ time. But achieving high performance requires designing locality-aware algorithms.
- Hardware/OS automatic management (like caches) is insufficient for optimal performance, putting the onus on algorithmic design.

**Mental Model: The Chef in the Kitchen**
Imagine a chef cooking a complex meal:
- **L1 Cache (Cutting Board):** Right in front of the chef. Instantly accessible, but can only hold a few vegetables at a time.
- **Main Memory (The Fridge):** Across the room. Holds a lot of food, but it takes time to walk there and back.
- **Disk (The Grocery Store):** Holds practically infinite food, but takes an hour to retrieve anything.
If a chef goes to the grocery store for every single onion, they will be extremely slow. Good algorithms act like a smart chef: they bring a whole bag of onions to the cutting board at once (locality) and use them before fetching something else.

---

## 2. The Two-Level I/O Model

To design locality-aware algorithms, we use a machine model based on the von Neumann architecture with a simplified two-level memory hierarchy. 

**Why only two levels?**
Real machines have 4-5 levels of memory. Analyzing all of them mathematically is exhausting and fragile. The two-level model captures the essential boundary—there is a "fast place" and a "slow place." If we optimize our algorithm for this generic boundary, it recursively improves performance across all boundaries (e.g., L1 to L2, RAM to Disk).

### Architecture Components
- **Processor**: Sequential processor performing basic computing operations (addition, branching, etc.).
- **Slow Memory (Main Memory)**: Assumed to be infinitely large but very slow.
- **Fast Memory (e.g., Cache)**: Sits between processor and slow memory. Very fast but small. Its capacity is denoted by **$Z$** words.

*Examples of two-level pairings:* L1 cache vs CPU registers, Main memory vs Hard disk, Local RAM vs Remote server RAM.

### Rules of Computation
1. **Local Data Rule**: The processor can only perform operations if the operands reside in the fast memory. *(Temporal Locality: Once data is here, we want to reuse it as much as possible before it gets evicted).*
2. **Block Transfer Rule**: Data moves between slow and fast memory in contiguous chunks (blocks) of size **$L$** words. Loading a specific word at address $x$ pulls in $L-1$ nearby words depending on data alignment in slow memory. *(Spatial Locality: If you ask for one item, you get its neighbors for free).*

### Cost Metrics
1. **Work ($W$)**: Computational work (number of operations), dependent on input size $n$.
2. **I/O Complexity ($Q$)**: The number of block transfers between slow and fast memory. Dependent on fast memory size $Z$ and block transfer size $L$.

---

## 3. Data Alignment and Basic Lower Bounds

### Alignment Considerations
When reading an array of size $N$ with a block transfer size of $L$:
- **Aligned Array**: Requires exactly $\lceil N/L \rceil$ transfers.
- **Unaligned Array**: In the worst case, requires $\lceil N/L \rceil + 1$ transfers.

**Intuition:** 
Imagine blocks are egg cartons that hold exactly $L=12$ eggs. If you need 12 specific eggs, and they perfectly align with a single carton, you only carry 1 carton. But if your 12 eggs start halfway through carton A and end halfway through carton B, you are forced to carry 2 cartons to get what you need. 

*Note: For large $N$, alignment details are often a minor detail and ignored asymptotically.*

### Trivial Lower Bounds on Transfers ($Q$)
Lower bounds give us a theoretical baseline to know if our algorithm is "optimal" or if there's room for improvement.
- **Reading an Array**: $O(N/L)$ transfers. You simply have to look at the data at least once.
- **Sorting an Array**: Trivial lower bound is $O(N/L)$ transfers (must touch each element). *Note: The true theoretical lower bound is higher, but the trivial lower bound represents the minimum I/O just to read the input.*
- **Matrix Multiplication ($N \times N$)**: Trivial lower bound is $O(N^2/L)$ transfers (must read the two matrices of size $N^2$).

---

## 4. I/O Example: Array Reduction

Let's look at a concrete example: Summing the elements of an array of size $n$ (where $n \gg Z$).

- **Work**: $O(n)$ additions.
- **Transfers**: $O(n/L)$ transfers.
- **How it works:** The algorithm processes the array one block at a time. It loads a block of $L$ numbers, adds them to a running total, discards the block, and loads the next one.
- **Key Insight:** The transfer complexity is independent of fast memory size $Z$ because reduction involves no data reuse. As long as the fast memory can hold at least one block ($Z \ge L$), a larger cache doesn't speed up the process.

---

## 5. Data Layout and Access Patterns

The physical layout of data in memory drastically impacts the number of transfers. In memory, a 2D matrix is actually stored as a flat 1D array.

### Matrix-Vector Multiplication Example ($y = Ax$)
Consider multiplying a dense $n \times n$ matrix $A$ (stored in **column-major order**) by a vector $x$. Assume $Z$ can hold two vectors plus a few blocks of size $L$, and $L$ divides $n$.

- **Algorithm 1 (Row-wise Traversal)**: Outer loop over rows, inner loop over columns.
  - **The Problem:** Accessing a row element loads a block from a column. The next row iteration requires loading a completely different block. The fast memory is too small to keep the previously loaded blocks, leading to evictions (cache thrashing).
  - **Transfers**: $O(n^2)$ additional transfers for matrix $A$.
- **Algorithm 2 (Column-wise Traversal)**: Outer loop over columns, inner loop over rows.
  - **The Solution:** Traversal matches the column-major layout. Block loads are fully amortized over $L$ elements.
  - **Transfers**: $O(n^2/L)$ additional transfers.

**Takeaway**: In the standard RAM model, both algorithms are identical ($O(n^2)$ work). In the I/O model, Algorithm 2 is $L$ times faster due to sequential memory access. 
**Analogy:** Walking against the memory layout is like reading a book by reading the first word of every page, then the second word of every page. It requires flipping pages constantly. Algorithm 2 is like reading normally. Hardware caches alone cannot save Algorithm 1 from bad algorithmic design.

---

## 6. Algorithmic Design Goals

A good algorithm in the two-level model strives for two objectives simultaneously:

1. **Work Optimality**: The algorithm's work $W$ should asymptotically match the best sequential RAM algorithm $W^*$. ($W = O(W^*)$). You shouldn't do vastly more math just to save on memory loads.
2. **High Computational Intensity ($I$)**: Maximizes data reuse.
   - **Intensity ($I$)** = $W / (L \times Q)$
   - Measures operations per word transferred.
   - Larger $I$ implies more operations are performed per word brought into fast memory.

**Intuition for Intensity:** If $I$ is low, the processor spends most of its time twiddling its thumbs waiting for data to arrive from slow memory (memory-bound). If $I$ is high, the processor is constantly crunching numbers (compute-bound). Because processors are incredibly fast, we almost always want our algorithms to be compute-bound.

*Note: Work optimality and computational intensity must be balanced, much like work and span in parallel computing.*

---

## 7. Intensity, Machine Balance, and Time

This section mathematically defines the interplay between our algorithm's design and the physical hardware parameters.

### Machine Parameters
- **$\tau$**: Time to perform one compute operation (if data is local).
- **$\alpha$**: Amortized time to move one word of data between slow and fast memory.
- **Machine Balance ($B$)**: $B = \alpha / \tau$ (Operations per word). It indicates how many operations the processor can execute in the time it takes to move a single word.

**Mental Model for $B$:** Think of $B$ as the hardware's "appetite." If $B=10$, the hardware wants to execute 10 math operations for every 1 word it fetches from memory. If our algorithm provides an intensity of $I=2$, we are starving the processor.

### Execution Time
Assuming perfect overlap between data transfer and computation (they happen simultaneously):
- Compute Time = $\tau W$
- Transfer Time = $\alpha L Q$
- Total Time $T = \max(\tau W, \alpha L Q)$

*The $\max$ function implies a bottleneck: either the processor is the bottleneck, or the memory bus is the bottleneck. The slower one dictates the total time.*

Refactoring relative to ideal compute time ($\tau W$):
$T = \tau W \max(1, \frac{\alpha}{\tau} \frac{LQ}{W}) = \tau W \max(1, \frac{B}{I})$

### Normalized Performance ($R$)
Performance relative to the best possible RAM algorithm time ($\tau W^*$):
$R = \frac{\tau W^*}{T} = \frac{W^*}{W} \min(1, \frac{I}{B})$

---

## 8. Roofline Plots

A **Roofline Plot** visually represents normalized performance ($R_{max}$) as a function of algorithmic intensity ($I$). 

**Why "Roofline"?**
Because the graph literally looks like the roof of a house. You walk up the slanted part as you improve your algorithm, until you hit the flat ceiling, which is the maximum physical limit of the hardware.

- **X-axis**: Intensity ($I$)
- **Y-axis**: Normalized Performance ($R_{max}$)
- **Key Features**:
  - **Sloped Region (Memory Bound)**: When $I < B$, performance is limited by data transfer. Improving intensity linearly improves performance.
  - **Plateau (Compute Bound)**: When $I \ge B$, the algorithm is compute-bound, achieving maximum performance. The hardware is maxed out.
  - **Critical Point ($X_0$)**: $X_0 = B$. A good algorithmic target is to achieve $I \ge B$ to just reach the edge of the roof.
  - **Maximum Performance ($Y_0$)**: $Y_0 = W^* / W$. If the algorithm is not work-optimal ($W > W^*$), the roof is artificially lowered, and maximum achievable performance is permanently penalized.

---

## 9. Intensity of Matrix Multiplication

Let's compare two approaches for $n \times n$ matrix multiplication ($C = A \times B$):

### Conventional 3-Nested Loops
- **Work**: $O(n^3)$
- **Transfers**: $O(n^3)$ (dominated by repeatedly reading matrix $B$ $n$ times).
- **Intensity**: $I = O(1)$. A constant intensity means no asymptotic data reuse, leading to poor performance (heavily memory-bound).

### Blocked Matrix Multiplication (Tiling)
**Intuition:** Instead of computing one single element of $C$ at a time (which requires fetching entire rows and columns), we divide the matrices into small $b \times b$ submatrices (blocks). We keep these submatrices in the fast memory, compute all their partial products, and only then write the result back. 

Divide matrices into $b \times b$ blocks. Assume fast memory $Z$ can hold 3 blocks ($Z \approx 3b^2$).
- **Work**: $O(n^3)$
- **Transfers**: $O(n^3 / b)$ transfers.
- **Intensity**: $I = O(b) = O(\sqrt{Z})$.
- **Takeaway**: Blocking fundamentally changes the math. By doing $O(b^3)$ work for only $O(b^2)$ memory loads, it significantly increases computational intensity by reusing block data in fast memory. This demonstrates the immense algorithmic advantage of locality-awareness.

---

## 10. Informing Architecture Design

Algorithmic analysis doesn't just help software engineers; it guides hardware design (often addressing the "Memory Wall"—the trend where processors get faster much quicker than memory latency improves).

- **Scenario**: If a future machine doubles its machine balance $B$ (e.g., memory speeds lag behind processor compute speeds), the algorithm's intensity must also double to maintain performance.
- For Blocked Matrix Multiply, intensity $I \propto \sqrt{Z}$.
- To double $I$, the fast memory capacity **$Z$ must increase by a factor of 4**.
- **Result:** This mathematical reality dictates why modern CPUs dedicate massive amounts of physical silicon specifically to L2 and L3 caches.

---

## 11. Conclusion

- The two-level model captures the critical performance effects of real memory hierarchies: **capacity ($Z$)** and **transfer size ($L$)**.
- To exploit memory hierarchies, organize data access patterns to maximize data reuse.
- **Rule of Thumb**: For an algorithm to scale well on future architectures, its computational intensity ($I$) must match or exceed the machine's balance point ($B$).