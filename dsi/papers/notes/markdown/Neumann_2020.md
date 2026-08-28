# Umbra: A Disk-Based System with In-Memory Performance

**Authors:** Thomas Neumann, Michael Freitag (Technische Universität München)
**Conference:** CIDR 2020

## 1. Introduction
Hardware trends over the last decade led to the rise of pure in-memory database systems (e.g., HyPer). However, two current trends challenge this model:
1. **DRAM Scaling Slowdown:** Main memory sizes are no longer increasing significantly without a disproportionate rise in costs.
2. **SSD Advancements:** Modern NVMe SSDs offer high read bandwidths (e.g., 3.5 GB/s) at a fraction of DRAM's cost. 

> **Intuition:** The performance gap between memory and SSDs has narrowed so much that keeping everything in RAM is no longer economically justifiable. We can get "good enough" speeds from fast SSDs.

Pure in-memory systems offer peak performance but are uneconomical and fail to scale beyond available RAM. **Umbra** is designed as a spiritual successor to HyPer—a disk-based (SSD-based) system that offers genuine in-memory performance for the cached working set and transparent scaling for larger-than-memory data. 

To achieve this, Umbra employs a novel low-overhead buffer manager with **variable-size pages**, eliminating the complex mechanisms traditionally required to store large objects (like strings or dictionary lookup tables) across fixed-size pages.

> **Mental Model:** Think of Umbra as bringing the best of both worlds: the raw execution speed of an in-memory database (like HyPer) with the infinite capacity of a traditional disk-based database, achieved by managing memory extremely carefully.

## 2. Buffer Manager
Umbra's buffer manager organizes database pages into **size classes**. 
- **Size Class 0** contains the smallest pages (64 KiB).
- Subsequent size classes grow exponentially (i.e., Class $i+1$ pages are twice as large as Class $i$).
- A single buffer pool manages pages from all size classes.

> **Tradeoff:** Variable-size pages reduce the complexity of splitting large objects across multiple pages, but they introduce the risk of external memory fragmentation (empty gaps in RAM).

### 2.1 Buffer Pool Memory Management
The main challenge with variable-size pages is external fragmentation. Umbra solves this by exploiting the operating system's virtual memory mapping (`mmap`):
- A separate block of virtual memory (large enough for the entire buffer pool) is allocated for *each* size class. 
- These mappings are private and anonymous, meaning they consume no physical memory until actually used.
- When a page is loaded from disk via `pread`, the OS creates an actual mapping to physical RAM.
- Upon eviction, data is written via `pwrite`, and the OS is instructed to immediately reclaim the physical memory using `madvise(MADV_DONTNEED)`. 
- This ensures zero virtual address space fragmentation while dynamically controlling physical memory consumption.

> **Common Confusion:** It might seem like allocating a massive virtual memory block for each size class would waste memory. However, virtual memory is just address space; physical RAM is only consumed when the OS maps it, which `madvise` actively controls.

### 2.2 Pointer Swizzling
To map logical Page Identifiers (PIDs) to physical memory without the overhead of a global hash table, Umbra uses **pointer swizzling**.
- References to pages are stored as 64-bit **swips**.
- A **swizzled** swip directly stores the virtual memory pointer (fast access).
- An **unswizzled** swip encodes the PID (57 bits), the size class (6 bits), and a tag bit (1 bit).
- To simplify eviction and consistency, every page must have **exactly one owning swip** (organized in a tree structure). Thus, B+-tree leaf pages do not contain sibling pointers.

> **Mental Model:** Pointer swizzling is like caching a website's IP address locally. Instead of doing a DNS lookup (hash table lookup) every time you want to visit, you just use the IP address directly (the virtual memory pointer) once it's known.

### 2.3 Versioned Latches
Umbra uses optimistic latching to minimize thread synchronization contention:
- Each active buffer frame holds a 64-bit versioned latch (59 bits for a version counter, 5 bits for state).
- **Exclusive Mode:** Acquired by writers. Prevents concurrent access and increments the version counter upon release.
- **Shared Mode:** Pins a page in memory for reading.
- **Optimistic Mode:** Readers remember the version counter before reading. After reading, they validate that the counter hasn't changed. If the page was concurrently modified or evicted, the read is retried.

> **Intuition:** Optimistic latching assumes conflicts are rare. It avoids the heavy overhead of acquiring locks by simply reading the data and then double-checking that nobody else changed it while you were reading.

### 2.4 Buffer-Managed Relations
- Relations are organized in B+-trees using synthetic 8-byte, strictly monotonically increasing tuple identifiers as keys. This avoids node splitting during inserts.
- Inner nodes are always 64 KiB. Leaf nodes use the smallest page size that fits the tuple, which handles variable-sized data gracefully.
- Tuples within a leaf use a **PAX layout**: fixed-size attributes in columnar format at the start, and variable-size attributes packed densely at the end.
- To traverse the tree efficiently without sibling links (due to swizzling rules), scans hold an optimistic latch on the parent node to navigate to the next leaf.

### 2.5 Recovery
Umbra uses **ARIES** for recovery. To ensure recoverability when reusing disk space with variable-size pages, Umbra only reuses freed disk space for pages of the **exact same size**.

## 3. Further Considerations

### 3.1 String Handling
String attributes are split into two parts: a 16-byte fixed-size header (stored in the PAX columnar section) and a variable-size body.
- **Header:** 4 bytes for length, 4 bytes for prefix (short-circuiting comparisons), and 8 bytes for an offset or pointer.
- Strings $\le 12$ characters are stored entirely inline within the header.
- Longer strings are stored out-of-line. Since disk-based pages can be evicted, out-of-line strings belong to one of three storage classes (encoded in the offset bits):
  - **Persistent:** Query constants (valid for DB uptime).
  - **Transient:** Base relation data (must be copied if materialized during query execution, as the underlying page may be evicted).
  - **Temporary:** Created during query execution (garbage collected later).

> **Tradeoff:** Splitting strings into headers and out-of-line bodies adds pointer-chasing overhead for long strings, but it allows the fast columnar execution engine to process the fixed-size headers efficiently, often short-circuiting comparisons without ever reading the body.

### 3.2 Statistics
Disk-based sampling is expensive. Umbra uses:
- **Online Reservoir Sampling:** Maintains an always up-to-date random sample of each relation with minimal overhead.
- **Updateable HyperLogLog Sketches:** Provides highly accurate cardinality estimates for individual and multi-column combinations.

### 3.3 Compilation & Execution
Umbra adapts HyPer's query compilation model (translating logical plans into machine code) with key enhancements:
- **Modular State Machines:** Physical plans are fine-grained state machines broken into single/multi-threaded "steps" rather than monolithic code blocks. This allows suspending execution (e.g., if I/O load is high) and efficient morsel-driven parallelism.
- **Custom Lightweight IR:** Umbra bypasses LLVM's overhead during initial compilation by using a custom Intermediate Representation (IR).
- **Adaptive Compilation:** Steps are initially interpreted via a fast bytecode VM. If the execution engine detects a long-running step, the custom IR is cheaply translated to LLVM IR and JIT-compiled to optimized machine code.

> **Common Confusion:** Why use a custom IR and bytecode VM if LLVM produces the fastest code? LLVM's compilation time is often longer than the time it takes to just run a short query. Adaptive compilation ensures that the heavy cost of LLVM is only paid for long-running queries where the optimization actually pays off.

## 4. Experiments & Performance
- **Performance vs. HyPer:** Umbra matches HyPer's raw execution time on cached working sets (TPC-H and JOB benchmarks), proving the variable-size buffer manager introduces negligible overhead (under 6%). 
- **Compilation Time:** Umbra's adaptive compilation drastically reduces query compilation times compared to HyPer's always-on LLVM approach (up to 29x faster on cheap queries).
- **Disk I/O:** When data exceeds RAM, Umbra successfully maxes out NVMe SSD bandwidth (e.g., 1.15 GB/s read throughput), validating its design as a highly scalable disk-based architecture.