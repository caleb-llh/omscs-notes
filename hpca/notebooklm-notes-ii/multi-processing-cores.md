# Multi-processing / Multi-cores

---

## 1.0 Foundations of Multiprocessing
### 1.1 The Transition from Uniprocessors
*   **Diminishing Returns of Width:** Historically, uniprocessor performance was improved by making the architecture wider (executing more instructions per cycle). However, once a processor reaches 4 to 6-issue width, the gains from further widening diminish significantly.
*   **Parallelism Limitations:** Programs with many dependencies cannot exploit wider issue slots because instructions must run one at a time. Increasing width only accelerates the parallel parts of a program while leaving the sequential parts unaccelerated.
*   **The Power Wall:** Increasing frequency to boost uniprocessor performance requires raising the voltage, which causes power consumption to grow **cubically**. This leads to excessive heat that can burn the processor.
*   **Moore’s Law Adaptation:** Although transistor density continues to double every 18 months, the strategy has shifted from making individual cores faster to **doubling the number of cores** on a single chip to improve overall computational performance.

### 1.2 Flynn’s Taxonomy of Parallel Machines
Parallel machines are categorized by the number of instruction and data streams they process:
1.  **Single Instruction, Single Data (SISD):** A standard uniprocessor executing one instruction stream on one data stream.
2.  **Single Instruction, Multiple Data (SIMD):** A single program counter (instruction stream) operates on multiple data items simultaneously (e.g., vector processors or multimedia extensions like MMX/SSE).
3.  **Multiple Instruction, Single Data (MISD):** Multiple programs operate on a single data stream (rarely used; closest examples are stream processors where data moves through a pipeline of different processing stages).
4.  **Multiple Instruction, Multiple Data (MIMD):** Standard multiprocessors where each core runs its own program on its own data independently and not in lock-step.

---

## 2.0 Parallel Programming Models
Modern multiprocessing utilizes two primary paradigms for communication and data management: **Message Passing** and **Shared Memory**.

### 2.1 Message Passing
In this model, processors are treated as independent machines with private memory spaces.
*   **Memory Isolation:** Each processor allocates only its required portion of an array in its own local memory; cores cannot access each other's memory directly.
*   **Explicit Communication:** To share data, the programmer must use explicit primitives such as **Send** and **Receive**. For example, to compute a global sum, one core acts as a "summing agent," receiving partial sums from every other core.
*   **Synchronization via Communication:** Correctness is achieved by matching sends and receives. A receiver will wait (block) until the corresponding send occurs, ensuring data is initialized before it is read.
*   **Programmer Effort:** The programmer is responsible for manually distributing data and orchestrating every communication event. While achieving correctness is difficult, performance is often easier to optimize because the programmer is forced to minimize expensive off-node communications.

### 2.2 Shared Memory
All cores share a single physical address space, allowing them to communicate by reading and writing to the same memory locations.
*   **Implicit Communication:** Data is passed through shared variables. When one core writes to a location and another reads it, communication happens automatically through the hardware and cache coherence protocols.
*   **Manual Synchronization:** Because communication is implicit, the programmer must add explicit synchronization, such as **locks (critical sections)** or **barriers**, to prevent race conditions (e.g., ensuring Core Zero only prints a sum after all other cores have updated it).
*   **Ease of Use vs. Performance:** This model is generally easier for writing correct code but significantly harder for achieving high performance. Programmers may not realize when memory accesses are non-local (and thus slow), leading to "invisible" performance bottlenecks.

---

## 3.0 Multithreading Performance and Hardware
Multithreading hides latency and improves pipeline utilization by allowing multiple threads to share the execution resources of a single core.

### 3.1 Varieties of Multithreading
1.  **No Multithreading:** The processor runs one thread at a time. Significant time is wasted during context switches (OS interrupts) and stalls (e.g., cache misses).
2.  **Fine-Grain Multithreading:** The hardware switches between threads every cycle. This hides the idleness of one thread (e.g., during a cache miss) by executing instructions from another thread.
3.  **Simultaneous Multithreading (SMT / Hyper-Threading):** Instructions from multiple threads are mixed within the **same execution cycle**. This populates unused issue slots in an out-of-order superscalar processor.

### 3.2 SMT Hardware Implementation
SMT is cost-effective because it replicates only a small portion of the processor (approx. 5% cost increase) while sharing the complex execution engine.
*   **Replicated Components:** To support SMT, a core needs a separate **Program Counter (PC)**, a separate **Register Alias Table (RAT)**, and a separate **Architectural Register File (ARF)** for each thread.
*   **Shared Components:** The **Instruction Cache**, **Decoders**, **Reservation Stations**, **Execution Units**, and **Data Cache** are shared among all active threads.
*   **Commit Logic (Reorder Buffer - ROB):** The ROB must track instructions from multiple threads. Usually, threads are committed in order, but an instruction from one thread may have to wait for an older instruction from a different thread to commit first.

### 3.3 SMT and Cache/TLB Dynamics
*   **Cache Trashing:** If the combined working sets of active threads exceed the cache capacity, performance can be significantly worse than running threads sequentially due to increased cache misses.
*   **Thread-Aware TLB:** In SMT, different threads might use the same virtual address for different physical data. To prevent aliasing, the **Translation Lookaside Buffer (TLB)** must be "thread-aware," matching both the virtual page number and a **Thread ID** before producing a physical address.

---


### 4.0 Architectural Implementations of Shared Memory
The physical organization of memory significantly impacts scalability and performance.

#### 4.1 Centralized Shared Memory (UMA/SMP)
*   **Architecture:** Multiple cores, each potentially with private caches, are connected to a single **shared bus** that interfaces with a centralized main memory and I/O devices.
*   **Uniform Memory Access (UMA):** All memory locations are equidistant from all cores. Consequently, the **latency (access time) is uniform** across the entire address space for every processor.
*   **Symmetric Multiprocessor (SMP):** These systems are symmetric because every core-cache unit is identical. Scalability is achieved by simply replicating these identical units on the bus.
*   **Data Exchange:** Communication is implicit; Core A writes to a memory location, and Core B reads from it.

#### 4.2 Limitations of Centralized Memory
*   **Memory Bandwidth Contention:** As the number of cores increases, cache misses from all cores converge on the single centralized memory. This creates a **bottleneck** where requests are serialized in a queue.
*   **Latency vs. Size:** To support more cores, the memory must be larger, which inherently makes it **slower** and physically further from the cores.
*   **Scalability Ceiling:** Due to bandwidth saturation, centralized shared memory is typically effective only for small-scale systems (e.g., 2, 4, 8, or 16 cores). Beyond this, adding cores provides no performance advantage.

---

### 5.0 Distributed Memory Systems
To scale beyond the limits of centralized memory, the system must be physically distributed.

#### 5.1 Architecture and "Multicomputers"
*   **Structure:** Each core possesses its own private memory slice that cannot be accessed directly by other cores. Each node effectively acts as a complete **uniprocessor system** with its own cache, memory, and network interface.
*   **Cluster/Multicomputer:** These systems are often called **multicomputers** or **cluster computers** because they resemble a collection of independent machines connected by a high-speed network.
*   **Communication:** Because there is no hardware-level sharing, communication must be **explicit**. If a core needs data from another's memory, it must issue a **network message** (Send/Receive) via the operating system.

#### 5.2 Non-Uniform Memory Access (NUMA)
In distributed shared memory, cores share a logical address space, but physical access times vary.
*   **Local vs. Remote Access:** Accessing the local memory slice is fast, while accessing a remote slice (residing with another core) requires crossing the interconnect, resulting in higher latency.
*   **OS Responsibility:** The Operating System (OS) must be **NUMA-aware**. It should place data pages in the memory slice local to the core that accesses them most frequently.
*   **Specific Allocations:**
    *   **Stack Pages:** These should always be mapped to the local memory of the core running the associated thread.
    *   **Initialization Hazards:** If one core initializes a large array, the OS should not blindly place the entire array in that core's memory, as that node would become a **bottleneck** for all subsequent readers.

---

### 6.0 Interconnects: Bus vs. Mesh
The physical medium connecting cores determines the system's total throughput.

#### 6.1 Shared Bus Bottlenecks
*   **Serialization:** A bus can only handle **one request at a time**. While this provides an easy ordering for coherence, it does not scale with the number of cores.
*   **Throughput Saturation:** If four cores each generate 10 million messages per second but the bus only supports 20 million total, the cores are forced to slow down by 50% to match the bus capacity.

#### 6.2 Point-to-Point Networks (Mesh and Torus)
*   **Mesh Architecture:** Cores (tiles) are connected in a grid. Each link is independent, allowing for **multiple simultaneous communications**.
*   **Scalable Throughput:** As the number of cores grows, the number of links increases proportionally, causing the total available network throughput to grow alongside the demand.
*   **Torus:** A variation of the mesh where endpoints wrap around to connect to the opposite side (like a donut), reducing the maximum distance (hop count) between nodes.
*   **Implementation Benefits:** Meshes are ideal for chip manufacturing because the links do not intersect on the silicon.

---

### 7.0 Challenges in Many-Core Scaling
Scaling to 64+ cores introduces non-linear technical hurdles.

#### 7.1 Coherence Traffic
*   **The Bus Bottleneck:** In snooping-based systems, every write results in an invalidation message sent to the shared bus. As core counts rise, the volume of invalidations and subsequent misses eventually exceeds bus capacity.
*   **Solution:** Systems must transition to **Directory Coherence** and scalable on-chip networks (like meshes) to avoid serializing all coherence traffic.

#### 7.2 Off-Chip Bandwidth and Pin Constraints
*   **The Pin Problem:** While core counts double every 18 months, the number of physical pins on a chip (for communication with the motherboard) grows very slowly (e.g., 10% increase). Pins must remain large enough for physical durability.
*   **Miss Rate Scaling:** Every core generates a constant number of misses. Total memory requests therefore grow **linearly** with the number of cores, while off-chip throughput stays nearly flat.
*   **Solution:** The **Last Level Cache (LLC)** must be shared among all cores and grow in size proportionally to the number of cores to filter out more off-chip requests.

#### 7.3 Power and Frequency Scaling
*   **Power Budget Splitting:** A chip has a fixed power budget (e.g., 100W). If that budget is split among 64 cores, each core receives only 1/64th of the total power, requiring lower voltage and frequency.
*   **The Single-Thread Penalty:** A single-threaded program running on a many-core chip would be significantly slower than on a single-core chip because it only has access to a fraction of the power budget.
*   **Turbo Frequency:** To mitigate this, modern processors use a "Turbo" mode. If only one core is active, it can consume a larger portion (though not necessarily 100% due to local **thermal hotspots**) of the power budget to boost its frequency.
    *   *Thermal Limits:* Concentrating all power in one corner of the chip creates more heat than spreading it evenly. For example, a 4-core mobile processor might boost a single core's power by 3x (not 4x) to avoid overheating that specific area.

---

### 8.0 Distributed Last Level Cache (LLC) and Directory
A single centralized LLC would create a bottleneck at its entry point.

#### 8.1 Distributed LLC Slicing
*   **Architecture:** The LLC is sliced into portions, with one slice placed in each core's tile (e.g., a 16MB L3 distributed as 1MB per tile across 16 cores).
*   **Mapping (Round-Robin by Set):** To ensure even utilization, memory blocks are mapped to slices based on their **cache index/set number**.
    *   *Example:* In a 16-tile mesh, the least significant bits of the cache index determine the tile number. Set 0 goes to Slice 0, Set 1 to Slice 1, etc..
*   **Operating System Mapping:** Alternatively, the OS can map pages to slices based on **page numbers** to improve locality (e.g., mapping a thread's stack to the local L3 slice to avoid network traffic).

#### 8.2 On-Chip Partial Directory
*   **Capacity Problem:** A standard directory requires an entry for every block in main memory (gigabytes), which is too large to fit on-chip.
*   **Partial Directory Solution:** The hardware only maintains directory entries for blocks **currently residing in private L1/L2 caches**.
*   **Directory Replacement:** If the directory runs out of space, it must evict an existing entry. Because the directory is the only way to track sharing, evicting a directory entry **forces the invalidation** of that block in all private caches.

---


### 9.0 Comparative Programming Implementation: Case Study of a Parallel Array Sum
This section details the implementation differences between Message Passing and Shared Memory using a 1024-element array sum across four cores as a reference.

#### 9.1 Message Passing Implementation (Explicit)
*   **Data Allocation:** Each of the four processors allocates only one-quarter of the array (256 elements) in its private memory. Processors cannot access each other's memory directly.
*   **Initial Distribution:** If data is not already local, the programmer must write explicit code to send array segments to each processor.
*   **Local Computation:** Each core iterates over its local segment to compute a partial sum. These are local accesses and are relatively fast.
*   **The Summing Agent:** One processor (e.g., Core 0) acts as the "summing agent". It must explicitly issue **Receive** commands for every other processor's partial sum.
*   **Explicit Communication:** The remaining processors must explicitly **Send** their partial sums to Core 0.
*   **Synchronization via Communication:** Correctness depends on matching every Send with a corresponding Receive. 
    *   If a core waits for a Receive that has no matching Send, the program will deadlock.
    *   The Receive operation inherently ensures the data is initialized because the Send only occurs after the local sum is complete.

#### 9.2 Shared Memory Implementation (Implicit)
*   **Data Allocation:** The entire array resides in a single shared memory space accessible by all cores. There is no need for manual data distribution.
*   **Implicit Communication:** Cores communicate by reading and writing to shared variables (e.g., `allSum`).
*   **Synchronization Primitives:**
    *   **Critical Sections (Locks):** Because multiple cores may attempt to update `allSum` simultaneously, they must use locks to ensure only one core modifies the variable at a time. Cores can update the sum in any order.
    *   **Barriers:** To prevent a core (e.g., Core 0) from printing the final sum before others have finished their updates, a **barrier** is used. This forces all cores to wait until every participant has reached that point in the code.
*   **Code Complexity:** Shared memory typically requires fewer lines of code for data distribution (zero lines in some cases) but more lines for explicit synchronization (locks and barriers).

---

### 10.0 Scalable Memory Hierarchies: Distributed LLC and Directory Management
As core counts scale, centralized structures must be replaced by distributed hardware to prevent bottlenecks.

#### 10.1 Distributed Last Level Cache (LLC/L3) Mechanics
*   **Slicing and Capacity:** The LLC is logically a single cache but physically sliced into tiles (e.g., a 16-core system with a 1MB slice per tile creates a 16MB L3). This allows the cache capacity to grow linearly with the number of cores.
*   **Indexing and Mapping (Round-Robin by Set):** To distribute load, memory blocks are mapped to slices based on the cache index.
    *   Example: In a system with 1,024 sets and 8 slices, Slice 0 handles Set 0, 8, 16... while Slice 1 handles Set 1, 9, 17.
    *   This spreading of sets ensures that sequential memory accesses are distributed across the entire chip, preventing link saturation.
*   **OS-Managed Locality (Mapping by Page):** Spreading data by set can hurt locality if a core frequently accesses data in a distant tile. Alternatively, the OS can map entire pages to specific L3 slices. For instance, a core's stack pages can be mapped to its local L3 slice to minimize on-chip network traffic.

#### 10.2 On-Chip Partial Directory
*   **The Capacity Problem:** A full directory tracking every block in a multi-gigabyte main memory would require billions of entries, which cannot fit on-chip.
*   **Partial Directory Logic:** The hardware only maintains entries for blocks currently residing in at least one private L1 or L2 cache. If a block is only in the LLC or main memory, it is implicitly known to have no sharers (presence bits = 0), so no entry is needed.
*   **Directory Replacement and Invalidations:**
    *   When a new block is fetched into an L1/L2 cache and the partial directory is full, an existing entry (E) must be evicted, often using an **LRU (Least Recently Used)** algorithm.
    *   Because the directory is the "source of truth" for coherence, evicting entry E requires the hardware to send **invalidation messages** to every cache indicated by E's presence bits.
    *   This creates a new type of cache miss: a miss caused by directory capacity limits rather than standard coherence or cache conflicts.

---

### 11.0 Performance Dynamics and Thermal Constraints
The physics of power consumption limits how many cores can be active and at what speed.

#### 11.1 The Cubic Power-Frequency Relationship
*   **The Power Law:** Power ($P$) is proportional to $Voltage^2 \times Frequency$ ($V^2 \times f$).
*   **Voltage-Frequency Scaling:** To increase frequency, voltage must be increased proportionally ($V \propto f$).
*   **The Result:** Total power consumption increases with the **cube of the frequency** ($P \propto f^3$).
*   **Performance Trade-off:** Doubling the number of cores splits the power budget in half. This requires reducing the frequency to approximately 80% (the cubic root of 0.5) of the single-core frequency.

#### 11.2 Turbo Frequency and Thermal Hotspots
*   **Single-Thread Acceleration:** When only one core is active, it can utilize a larger portion of the chip's total power budget to "Turbo Boost" its frequency.
*   **Local Thermal Limits:** A 4-core processor cannot simply give 4x power to one core. Concentrating all power in one corner of the chip creates a **thermal hotspot**.
    *   In mobile processors (e.g., 37W), a single core might only be allowed 3x the normal power to match the temperature reached when heat is spread across all four cores at a lower frequency.
    *   In high-power desktop processors (e.g., 84W), the "Turbo" headroom is even smaller (approx. 11% boost) because the chip is already near its thermal limits even when idling other cores.

---

### 12.0 Network-on-Chip (NoC) Performance: Mesh vs. Bus
The interconnect architecture determines the system's ability to handle simultaneous requests.

#### 12.1 Throughput and Contention Analysis
*   **Bus Serialization:** A shared bus serializes all requests. If the total demand from cores exceeds bus capacity, the cores must slow down proportionally.
*   **Mesh Scalability:** In a mesh, multiple links can operate independently.
*   **Quantitative Speedup Example:** In a 4-core system where each core generates 10M messages/sec and the bus/links support 20M messages/sec:
    *   **Bus:** Total demand (40M) exceeds capacity (20M), forcing cores to run at **half speed** (2x execution time).
    *   **Mesh:** Traffic is distributed across multiple links. Calculation shows the most utilized link only handles 13.3M messages/sec, which is below the 20M limit.
    *   **Conclusion:** Switching to a mesh provides a **2x speedup** in this scenario by eliminating interconnect-induced stalls.

---

### 13.0 System-Level Integration and OS Awareness
Hardware parallelism at different granularities requires intelligent software management.

#### 13.1 Hierarchical Parallelism
Modern systems often combine multiple levels of parallelism:
1.  **Multiple Sockets:** Two or more chips on one motherboard.
2.  **Multiple Cores:** Four or more cores per chip.
3.  **Simultaneous Multithreading (SMT):** Two or more hardware threads per core.

#### 13.2 Smart Thread Mapping
The Operating System (OS) must understand this hierarchy to avoid resource contention.
*   **Avoid Competition:** If only three threads are running in a 16-thread system, they should be placed on **different chips** first to maximize available cache capacity.
*   **Core Distribution:** If on the same chip, they should be placed on **different physical cores** before utilizing a second SMT slot on an already active core. This prevents threads from competing for the same execution units and issue slots.

---