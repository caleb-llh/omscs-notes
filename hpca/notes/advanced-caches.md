# Advanced Caches

#### **Part 1: Performance Fundamentals, Hierarchies, and Addressing**

---

### **Section 1: Average Memory Access Time (AMAT) Fundamentals**

**1.1 Definition of AMAT**
The Average Memory Access Time (AMAT) is the primary metric for evaluating cache performance as seen by the processor. It represents the mean time required to fulfill a memory request, accounting for both hits and misses.

**1.2 The AMAT Equation**
For a system with a single level of cache, the AMAT is calculated as:
$$\text{AMAT} = \text{Hit Time} + (\text{Miss Rate} \times \text{Miss Penalty})$$

**1.3 Recursive AMAT in Cache Hierarchies**
In modern systems with multiple cache levels, the miss penalty of one level is determined by the performance of the subsequent level.
*   **L1 AMAT:** $\text{L1 Hit Time} + (\text{L1 Miss Rate} \times \text{L1 Miss Penalty})$.
*   **L1 Miss Penalty:** This is no longer simply memory latency; it is defined as the AMAT of the L2 cache: $\text{L2 Hit Time} + (\text{L2 Miss Rate} \times \text{L2 Miss Penalty})$.
*   **L2 Miss Penalty:** Similarly, if an L3 exists, this becomes: $\text{L3 Hit Time} + (\text{L3 Miss Rate} \times \text{L3 Miss Penalty})$.
*   **Terminating Condition:** This recursion continues until reaching the **Last Level Cache (LLC)**, where the miss penalty is equal to the **main memory latency**.

---

### **Section 2: Cache Hierarchy Architecture**

**2.1 The Multilevel Structure**
Modern processors utilize cache hierarchies (L1, L2, L3, etc.) to bridge the performance gap between fast processors and slow main memory.

**2.2 Last Level Cache (LLC)**
The LLC is defined as the cache whose misses go directly to main memory. Historically, the L1 was the LLC; as technology progressed, L2 and then L3 became the LLC.

**2.3 Comparison: L1 vs. L2 Characteristics**
To optimize performance, L1 and L2 caches are designed with different priorities:
*   **Capacity:** L1 capacity is significantly smaller than L2. L2 must be larger to ensure it can hit on references that missed in L1.
*   **Latency:** L1 hit latency is much lower than L2. The processor checks L1 first because of its speed, not because it is more likely to contain the data.
*   **Access Frequency:** All processor memory references (loads/stores) go to L1, whereas only L1 misses reach L2. Consequently, L2 sees far fewer accesses.
*   **Associativity:** L1 typically has lower associativity to maintain fast hit times, while L2 can afford higher associativity because it is already slower.

**2.4 Inclusion, Exclusion, and Non-Inclusion Properties**
These properties define the relationship between data residing in different levels of the hierarchy:
*   **Inclusion:** Guarantees that any block in L1 **must** also reside in L2.
    *   *Implementation:* Requires an **inclusion bit** in L2 to track if a block is in L1. If L2 must evict a block with the inclusion bit set, it must also evict it from L1.
    *   *Benefit:* Simplifies write-backs; a dirty block replaced in L1 is guaranteed to be a hit in L2.
*   **Exclusion:** A block in L1 **cannot** be in L2.
*   **Non-Inclusion (Neither):** No explicit guarantee; a block in L1 may or may not be in L2.
    *   *Behavior:* Unless forced, most hierarchies default to this. Blocks frequently accessed in L1 may be evicted from L2 because L2 never sees those accesses to update its replacement state.

---

### **Section 3: Cache Performance Metrics and Analysis**

**3.1 Local vs. Global Miss Rates**
*   **Local Miss Rate:** The number of misses in a specific cache divided by the number of accesses *to that specific cache*.
*   **Global Miss Rate:** The number of misses in a cache divided by the *total number of memory references* made by the processor.
    *   *Calculation for L2:* $\text{Global Miss Rate}_{L2} = \text{L1 Miss Rate} \times \text{L2 Local Miss Rate}$.

**3.2 Misses Per Kilo-Instruction (MPKI)**
MPKI normalizes misses against the total number of instructions rather than just memory accesses. This provides a more holistic view of how cache misses affect overall program execution.

**3.3 Impact of Locality on Hierarchies**
L2 and L3 caches often observe lower **local hit rates** than L1. This is because L1 "filters" out easy-to-hit accesses with high temporal and spatial locality, leaving only the "hard" accesses for the lower levels.

---

### **Section 4: Cache Addressing and Translation**

**4.1 Physically Indexed, Physically Tagged (PIPT)**
A PIPT cache requires the virtual address to be translated by the **TLB** into a physical address before the cache can be indexed or the tag checked.
*   **Latency:** The total hit latency is the sum of TLB latency and Cache latency ($\text{TLB Hit Time} + \text{Cache Hit Time}$).

**4.2 Virtually Accessed Caches (VIVT)**
VIVT caches use the virtual address for both indexing and tag comparison, allowing the cache lookup to proceed without waiting for the TLB.
*   **Pros:** Lower hit latency (just cache hit time) and energy savings as the TLB is only accessed on a miss.
*   **Cons:** 
    *   **Context Switching:** Since different processes use the same virtual addresses for different data, the cache must be **flushed** on every context switch to avoid incorrect data access.
    *   **Permissions:** Caches still need to check protection bits (Read/Write/Execute) usually stored in the TLB.
    *   **Aliasing:** Multiple virtual addresses mapping to the same physical address.

**4.3 Virtually Indexed, Physically Tagged (VIPT)**
VIPT attempts to combine the speed of virtual indexing with the correctness of physical tagging.
*   **Mechanism:** The cache index is taken from the virtual address, while the tag is compared against the physical address provided by the TLB.
*   **Parallelism:** The TLB lookup and the cache array access (reading tags and valid bits) occur **simultaneously**.
*   **Hit Time:** $\max(\text{TLB hit time}, \text{Cache hit time})$, usually resulting in just the cache hit time.
*   **Context Switches:** No flush is required because the physical tag ensures the correct data is identified regardless of the virtual address used.

**4.4 The Aliasing Problem and VIPT Constraints**
Aliasing occurs if two different virtual addresses refer to the same physical location but map to different cache sets.
*   **The Page Offset Rule:** Aliasing is avoided in VIPT caches if the **index bits** come entirely from the **page offset**. Since the page offset is identical in both virtual and physical addresses, the cache behaves as if it were physically indexed.
*   **Size Limitations:** This constraint limits the size of the cache.
    *   $\text{Max Cache Size} = \text{Page Size} \times \text{Associativity}$.
    *   *Example:* With a 4KB page size and 8-way associativity, the maximum aliasing-free VIPT L1 cache is 32KB. To increase cache size without aliasing, one must increase the associativity or the page size.

***

#### **Part 2: Optimization Categorization, Miss Reduction, and Hit Time Acceleration**

---

### **Section 4: Taxonomic Classification of Cache Optimizations**

**4.1 The Three Pillars of Optimization**
To improve the **Average Memory Access Time (AMAT)**, architectural optimizations must target one or more of the three variables in the fundamental equation:
1.  **Reducing Hit Time:** Accelerating the speed of successful accesses.
2.  **Reducing Miss Rate:** Decreasing the frequency of cache misses.
3.  **Reducing Miss Penalty:** Minimizing the time spent waiting when a miss occurs.

---

### **Section 5: Reducing the Miss Rate (The "3 Cs" Framework)**

**5.1 Analysis of Miss Causes**
Misses are classified into three categories, known as the **3 Cs**:
*   **Compulsory Misses:** Occur the very first time a block is accessed. These are unavoidable even in an infinite cache because the block must be brought in initially.
*   **Capacity Misses:** Occur when the cache is too small to hold all blocks required by the program. These blocks were once in the cache but were evicted due to space constraints.
*   **Conflict Misses:** Occur in set-associative or direct-mapped caches when multiple blocks compete for the same set, even if the cache has remaining total capacity.

**5.2 Optimization Technique: Increasing Cache Block Size**
Increasing the block size leverages **spatial locality** to reduce misses.
*   **Mechanism:** When a miss occurs, more adjacent data is brought into the cache, satisfying potential future requests.
*   **Impact on the 3 Cs:**
    *   **Compulsory:** Reduced because bringing in a larger block satisfies the "first access" for more data words simultaneously.
    *   **Capacity:** Reduced as long as there is high spatial locality; fewer blocks are needed to cover the same data range.
    *   **Conflict:** Likely to remain similar or decrease slightly as the number of blocks to manage is reduced.
*   **The "Junk" Trade-off:** If spatial locality is poor, larger blocks introduce "junk"—data that is never accessed but occupies space. This effectively reduces the useful capacity of the cache and can actually **increase** the miss rate.
*   **Cache Size Sensitivity:** Larger caches can tolerate larger block sizes (e.g., 256 bytes) because they have enough room to hold "junk" without evicting useful data, whereas small caches (e.g., 4KB) may see miss rates rise after reaching a block size of 64 bytes.

**5.3 Optimization Technique: Compiler-Driven Loop Interchange**
Compilers can reorder nested loops to align memory access patterns with the physical layout of data.
*   **The Row-Major Problem:** In C, matrices are stored row-by-row. If a loop iterates through columns first, it may suffer one miss per access because each access lands in a different cache block.
*   **Solution:** Swapping the inner and outer loops ensures the program accesses elements sequentially. This maximizes the use of every fetched cache block, dramatically improving the hit rate.

---

### **Section 6: Reducing Hit Time (Speeding the Path)**

**6.1 Cache Pipelining**
For caches that take multiple cycles to access (common in L1 designs), pipelining allows the processor to initiate a new access every cycle, overlapping the latency of multiple hits.
*   **Stage Division:** A typical 3-stage cache pipeline might look like:
    1.  **Stage 1:** Indexing the array and reading tags/valid bits.
    2.  **Stage 2:** Tag comparison and beginning the data read.
    3.  **Stage 3:** Completing the data read and delivering it to the processor.
*   **Benefit:** Improves throughput. While an individual access still takes 3 cycles, the effective hit time seen by a stream of accesses is 1 cycle.

**6.2 Way Prediction (Cheating Associativity)**
Way prediction seeks the low miss rate of a set-associative cache with the fast hit time of a direct-mapped cache.
*   **Mechanism:** The cache "guesses" which way (which line in a set) contains the data.
*   **Execution Flow:**
    1.  **Step 1 (The Guess):** Access only the predicted way. If it's a hit, the latency is 1 cycle (like direct-mapped).
    2.  **Step 2 (The Backup):** If the guess is wrong, check all other ways in the set. This takes more time (e.g., 2 cycles).
*   **AMAT Impact:** In an 8-way cache where a guess is right 70% of the time:
    *   $\text{Average Hit Time} = (0.70 \times 1\text{ cycle}) + (0.30 \times 2\text{ cycles}) = 1.3\text{ cycles}$.
    *   This is significantly faster than a standard 8-way cache (2 cycles) while maintaining the same low miss rate.

---

### **Section 7: Reducing Miss Penalty (Memory-Level Parallelism)**

**7.1 Overlapping Misses (Non-Blocking Caches)**
Modern "out-of-order" processors do not stop on a miss. They continue executing instructions until they run out of resources (e.g., filling the Reorder Buffer).
*   **Hit-Under-Miss:** The cache services hits to other blocks while one miss is still pending in memory.
*   **Miss-Under-Miss:** The cache sends multiple, simultaneous requests to memory.
*   **Memory Level Parallelism (MLP):** By overlapping the wait times of multiple misses, the total penalty is reduced from the sum of the latencies to roughly a single latency plus a small overhead.

**7.2 Miss Status Handling Registers (MSHRs)**
To support non-blocking operations, the cache requires MSHRs to track "in-flight" misses.
*   **Function:** They store information about which block was requested and which instructions are waiting for that data.
*   **The "Half-Miss":** If a processor requests a block that is *already* being fetched due to a previous miss, the cache identifies this via MSHR comparison. This is a "half-miss" because the data is already on its way.
*   **Scaling:** Increasing the number of MSHRs (e.g., 16 to 32) allows for higher MLP, which is crucial as memory latencies remain long relative to processor speeds.

---

### **Section 8: Replacement Policy Optimization**

**8.1 The Latency-Complexity Trade-off**
*   **Random Replacement:** Requires zero state updates on a hit, leading to faster hit times but a higher miss rate.
*   **LRU (Least Recently Used):** Provides a low miss rate but requires updating $N$ counters on every hit (where $N$ is associativity), which is slow and energy-intensive.

**8.2 NMRU (Not Most Recently Used)**
NMRU is a simpler LRU approximation that only tracks the **Most Recently Used (MRU)** block using a single pointer per set.
*   **Rule:** When a replacement is needed, pick any block *except* the one pointed to by the MRU pointer.
*   **Efficiency:** Uses significantly fewer bits than LRU (e.g., 2 bits vs. 8 bits for 4-way associativity).

**8.3 Pseudo-LRU (PLRU)**
Pseudo-LRU uses one bit per line to track "recently accessed" status.
*   **Logic:** Bits are set to '1' upon access. Replacement picks a line with a '0' bit.
*   **Reset:** If setting a bit results in all bits being '1', all other bits are cleared to '0'. This policy sits between NMRU and true LRU in terms of both complexity and accuracy.

***

#### **Part 3: Data Prefetching, Quantitative AMAT Analysis, and Replacement Policy Implementation**

---

### **Section 9: Data Prefetching Strategies**

**9.1 Fundamental Concept of Prefetching**
Prefetching is a technique used to reduce the **miss rate** by predicting which memory blocks will be required by the processor in the near future and bringing them into the cache before an explicit request is made. If a prediction is correct, a potential cache miss is converted into a cache hit.

**9.2 Software Prefetching (Instruction-Based)**
Software prefetching relies on the compiler or programmer to insert explicit **prefetch instructions** into the code.
*   **Prefetch Distance ($Pdist$):** This defines how far in advance (in terms of array elements or loop iterations) the data is requested.
*   **The Latency Challenge:** 
    *   **Too Small $Pdist$:** If the prefetch is issued too close to the actual access, the data may not arrive from memory in time, resulting in a "less expensive" miss where the processor still stalls for the remaining latency.
    *   **Too Large $Pdist$:** If the data is brought in too early, it may be evicted from the cache by intervening accesses before it is ever used, a phenomenon known as **premature prefetching**.
*   **Hard-Coding Constraints:** Optimal $Pdist$ is hardware-dependent; a value that works for one processor-memory speed ratio may fail if the processor becomes faster while memory speed remains stagnant.
*   **Calculation Example:** In a loop where each iteration takes 10 cycles and memory latency is 200 cycles, a prefetch must be issued at least 20 iterations in advance to arrive "just in time".

**9.3 Hardware Prefetching (Automated Prediction)**
Hardware prefetchers monitor memory access patterns without requiring changes to the program binary.
*   **Stream Buffer:** A sequential prefetcher that identifies when a program is accessing contiguous blocks (A, then B) and automatically fetches subsequent blocks (C, D, etc.).
*   **Stride Prefetcher:** Monitors accesses to identify fixed-distance patterns (e.g., accessing every 4th word). It calculates the stride ($D$) and fetches addresses at $Current + D \times N$.
*   **Correlating Prefetcher:** Uses internal tables to track arbitrary sequences of non-sequential accesses (e.g., A is always followed by C, then B). This is highly effective for complex data structures like **linked lists**.

**9.4 Risks: Cache Pollution and Bandwidth**
*   **Cache Pollution:** Occurs when "bad guesses" bring useless data into the cache, evicting blocks that were actually needed and potentially creating new misses.
*   **Bandwidth Overload:** Incorrect prefetches consume memory bandwidth that could have been used for "demand" fetches (actual processor requests).

---

### **Section 10: Quantitative AMAT Case Study**

**10.1 Scenario Analysis: Single Cache vs. Hierarchy**
To demonstrate why hierarchies are superior, consider the following experimental data:
*   **Small L1 (16KB):** Hit Time = 2 cycles, Hit Rate = 90%. If memory latency is 100 cycles, the **AMAT is 12 cycles** ($2 + 0.10 \times 100$).
*   **Large L2 (128KB) alone:** Hit Time = 10 cycles, Hit Rate = 97.5%. The **AMAT is 12.5 cycles** ($10 + 0.025 \times 100$). Despite a better hit rate, the increased hit time makes it slower than the small L1.
*   **Hierarchy (L1 + L2):** 
    1.  L1 hit: 2 cycles (90% of accesses).
    2.  L1 miss, L2 hit: 12 cycles (10 cycles for L2 + 2 cycles L1 overhead).
    3.  L1 miss, L2 miss (Memory): 112 cycles.
    4.  **Resultant AMAT:** Approximately **5.5 cycles**. The hierarchy combines the fast hit time of the L1 with the high hit rate of the L2.

**10.2 The Filtering Effect on Local Hit Rates**
The L2 cache in a hierarchy often appears to perform worse than if it were used alone. This is because the L1 "filters" out the accesses with high locality (the "easy" hits). Consequently, the L2 only sees the "difficult" accesses that missed in L1, resulting in a lower **local hit rate** (e.g., 75%) despite a high **global hit rate**.

---

### **Section 11: Implementing Efficient Replacement Policies**

**11.1 The Overhead of True LRU**
True Least Recently Used (LRU) policies require significant hardware state. For an $N$-way associative cache, $N$ counters must be maintained per set.
*   **Hit Activity:** Every hit requires checking and potentially updating all $N$ counters to re-rank the blocks, which increases hit time and power consumption.

**11.2 Not Most Recently Used (NMRU)**
NMRU simplifies the state by only tracking the **Most Recently Used (MRU)** block using a single pointer (e.g., a 2-bit pointer for a 4-way cache).
*   **Replacement Logic:** Any block that is NOT the MRU is eligible for eviction.
*   **Efficiency:** NMRU uses $N$ times less state than true LRU for an $N$-way cache and helps keep frequently accessed data in the cache without the latency of full counter updates.

**11.3 Pseudo-LRU (PLRU)**
PLRU offers a middle ground between NMRU and LRU by using one "bit of history" per cache line.
*   **Bit-Setting Mechanism:** Every time a line is accessed, its bit is set to '1'.
*   **Eviction Policy:** Replacement logic searches for a line with a '0' bit.
*   **Global Reset:** When a hit occurs and the system detects that setting the bit would make all bits in the set '1', it resets all other bits to '0'.
*   **Performance:** PLRU is highly efficient on hits (only requires setting one bit) while providing a miss rate closer to true LRU than random or NMRU.

***

#### **Part 4: Prefetching Mechanics, Non-Blocking Systems, and Advanced Hardware Logic**

---

### **Section 12: Advanced Data Prefetching Mechanics**

**12.1 Hardware Prefetching Taxonomy**
Hardware prefetchers monitor access patterns at runtime to predict future data needs without program modification. These are categorized by the complexity of the patterns they detect:
*   **Stream Buffer:** A sequential prefetcher that detects when a program accesses block $A$ and then the subsequent block $B$. It speculatively fetches several sequential blocks in advance (C, D, etc.) to ensure data arrives before the processor requires it.
*   **Stride Prefetcher:** Monitors memory accesses to identify fixed-distance patterns where addresses differ by a constant amount ($D$). It calculates future addresses using the formula $Address + D \times N$.
*   **Correlating Prefetcher:** Designed for non-sequential, non-stride patterns (e.g., linked lists). It maintains a history table to record sequences; if it observes $A$ followed by $B$ and $C$ multiple times, seeing $A$ again triggers a prefetch for $B$ and $C$.

**12.2 Prefetching Performance Trade-offs**
*   **Accuracy and Hit Conversion:** A "good guess" converts a potential miss into a hit by bringing data from memory into the cache ahead of time.
*   **Cache Pollution:** A "bad guess" brings useless data into the cache, potentially kicking out useful blocks. This can create new misses for data that was previously present.
*   **Timeliness:** Prefetching must occur within a specific window. If issued too late (too small a distance), the data hasn't arrived from memory when needed, resulting in a "less expensive" miss that still causes a stall.

---

### **Section 13: Non-Blocking Caches and Memory Level Parallelism (MLP)**

**13.1 Miss-Under-Miss Support**
Traditional caches are "blocking," meaning they stall all cache activity during a miss. Non-blocking caches allow the processor to continue checking the cache for other data while a miss is pending.
*   **Hit-Under-Miss:** The cache services successful hits while a previous miss is still being fetched from memory.
*   **Miss-Under-Miss:** The cache sends multiple, concurrent requests to memory, allowing the wait times for different misses to overlap.

**13.2 Memory Level Parallelism (MLP)**
MLP is the ability of the system to process multiple memory accesses in parallel. By overlapping three or four misses, the processor effectively pays the penalty of one miss (plus minor overhead) rather than the sum of all individual miss latencies.

**13.3 Miss Status Handling Registers (MSHRs)**
To support non-blocking operations, the cache uses MSHRs to track "in-flight" requests.
*   **The Half-Miss Logic:** When a miss occurs, the cache checks the MSHRs. If the block has already been requested by a previous instruction but has not yet returned, it is a "half-miss." The cache does not send a duplicate request to memory; instead, it simply adds the new instruction to the existing MSHR entry.
*   **MSHR Scaling:** Systems typically require a few dozen MSHRs (e.g., 16 to 32) to maximize MLP and account for long memory latencies.

---

### **Section 14: Cache Pipelining and High-Speed Hits**

**14.1 Pipelining for Throughput**
If a cache hit takes multiple cycles, pipelining allows new accesses to enter the cache every cycle ($N, N+1, N+2$) rather than waiting for the previous access to complete.
*   **Three-Stage Pipeline Example:**
    1.  **Stage 1:** Indexing into the array to find the set and reading out tags/valid bits.
    2.  **Stage 2:** Performing tag comparison and hit determination; beginning the data array read.
    3.  **Stage 3:** Completing the data read and selecting the correct word via the offset for delivery to the processor.

---

### **Section 15: Quantitative Analysis of Cache Hierarchy Inclusion**

**15.1 Inclusion Property and Write-Backs**
The relationship between L1 and L2 affects how "dirty" data (modified data) is handled:
*   **With Inclusion:** A block in L1 is guaranteed to be in L2. Therefore, an L1 write-back is **always an L2 hit**.
*   **Without Inclusion (Non-Inclusion):** A block in L1 may have been evicted from L2 due to L2's own replacement policy. Consequently, an L1 write-back may result in an **L2 miss**, requiring an allocation in L2 or a direct write to memory.

**15.2 Managing Inclusion Bits**
To force inclusion, the L2 cache uses an **inclusion bit**. If L2 needs to evict a block whose inclusion bit is '1', it must first send an invalidation to the L1 to ensure the block is removed there as well, maintaining the property.

---

### **Section 16: Aliasing and VIPT Constraints**

**16.1 The Aliasing Problem (VIVT/VIPT)**
Aliasing occurs when two virtual addresses (A and B) refer to the same physical location. In a virtually accessed cache, if A and B map to different sets, a write to A will not be visible to a read from B, leading to incorrect execution.

**16.2 Aliasing Avoidance in VIPT**
A Virtually Indexed, Physically Tagged (VIPT) cache avoids aliasing if the index bits are derived entirely from the **page offset**. Because the page offset is identical for both virtual and physical addresses, the cache acts as if it were physically indexed.
*   **Mathematical Constraint:** $\text{Maximum Cache Size} = \text{Page Size} \times \text{Associativity}$.
*   **Industry Examples:**
    *   **Intel Pentium 4:** 4KB page size $\times$ 4-way associativity = 16KB L1.
    *   **Intel Core 2/Haswell:** 4KB page size $\times$ 8-way associativity = 32KB L1.
    *   **Future/Speculative Designs:** Increasing associativity to 16-way allows for a 64KB L1 while maintaining aliasing-free VIPT operation.

---

### **Section 17: Software Optimization: Loop Interchange**

**17.1 Row-Major Matrix Traversal**
In languages like C, matrices are stored in memory row-by-row (e.g., `a, a...a`).
*   **Inefficient Access:** If an outer loop iterates over $j$ (columns) and an inner loop over $i$ (rows), the processor fetches an entire cache block but only uses one element before moving to a different row. This causes one miss per access and can kick useful data out of the cache before the next column iteration.
*   **Loop Interchange Solution:** By swapping the nested loops so the inner loop iterates over the row elements ($j$), the program accesses memory sequentially. This maximizes spatial locality, uses every word in a fetched block, and allows hardware prefetchers to operate effectively.

***

