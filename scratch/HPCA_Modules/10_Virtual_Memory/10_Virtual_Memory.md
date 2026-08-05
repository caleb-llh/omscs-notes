# 10_Virtual_Memory (Synthesized Notes)

# Playlist 3 Module 1: Virtual Memory Support in Computer Architectures

This module explores how computer architectures provide support for **Virtual Memory**, a fundamental concept that significantly boosts the efficiency, security, and scalability of modern operating systems.

---

## 1. Why Virtual Memory?

### The Core Conflict: Programmer's View vs. Hardware View

To understand why virtual memory exists, we must first look at how memory is perceived by two different entities: the programmer and the hardware.

*   **The Hardware's View (Reality):**
    The physical machine contains actual RAM modules (e.g., two 2 GB modules, totaling 4 GB). Physical addresses range strictly from `0` to `4 GB`. The hardware is limited by the physical constraints of the installed memory.
*   **The Programmer's View (Illusion):**
    Programmers write code as if their program is the *only* thing running on the machine. They view memory as a massive, contiguous array of addresses starting at `0` and extending to a very large number (e.g., $2^{64}-1$ on a 64-bit machine). 
    *   **Memory Layout:** Memory is divided into sections for the system, program instructions (code), static data, the **Heap** (grows upwards for dynamic allocation like `malloc()`), and the **Stack** (grows downwards for function calls).
    *   **The Convenience:** Programmers don't want to worry about exactly how much physical space exists between the heap and the stack, or if another program is currently using address `0x1000`. They just want to allocate memory and push to the stack without running out of space.

### The Problem of Multitasking

Modern operating systems rarely run just one program. You might have a web browser, an MP3 player, and a word processor running simultaneously. 

*   If all programs expect their code to start at address `0`, they would constantly overwrite each other in physical memory.
*   We do not want to hardcode programs to run at specific memory locations (e.g., "Program A runs at address 0, Program B runs at address 1000").

### The Solution: Virtual Memory

Virtual Memory acts as a translation layer—a reconciliation between the programmer's infinite, private view of memory and the hardware's finite, shared reality.

*   **Decoupling:** Virtual memory completely decouples what the applications *think* they have from what the system *actually* has. 
*   **Illusion of Exclusivity:** Every process is given its own massive, private **Virtual Address Space**. Process A and Process B can both write to their own virtual address `0x1000`, but virtual memory maps these to entirely different physical locations.

> **💡 Mental Model:** 
> Imagine a hotel where every guest (process) is told they are staying in "Room 1" (virtual address). However, the front desk (the OS/hardware) secretly redirects their Room 1 key to actual, different physical rooms in the building (physical addresses). 

---

## 2. Pages and Frames: The Units of Memory

If every single byte of virtual memory mapped arbitrarily to a byte of physical memory, the translation table would be unimaginably huge. Instead, memory is managed in chunks.

*   **Pages (Virtual):** The virtual address space is divided into equal-sized contiguous chunks called **Pages**. A common page size is **4 KB**. 
    *   *Example:* Page 0 is `0 to 4KB`, Page 1 is `4KB to 8KB`, etc. Pages are aligned to the page size boundaries.
*   **Frames (Physical):** Physical memory is divided into slots called **Page Frames**. A frame is exactly the same size as a page (e.g., 4 KB) and acts as a physical container that can hold one virtual page.

> **💡 Intuition (Cache Analogy):** 
> Physical memory behaves like a cache for virtual memory. A virtual **Page** is analogous to a memory block, and a physical **Frame** is analogous to a cache line. The physical memory simply holds a subset of the actively used virtual pages.

---

## 3. The Page Table: The Map

How does the system know which virtual page is in which physical frame? It uses a **Page Table**.

*   **What is it?** A page table is an OS-managed data structure that maps virtual pages to physical frames.
*   **Per-Process:** **Every process has its own separate page table.** This is what provides memory isolation.
*   **Sharing Memory:** If the OS wants two processes to share data, it can map a virtual page from Process A's page table and a virtual page from Process B's page table to the *exact same physical frame*.

### Where is the "Missing" Memory?

If 16 applications all think they have 4 GB of memory, that totals 64 GB of virtual memory. If the physical machine only has 2 GB of RAM, where is the rest of the memory?

*   **The Hard Disk (Swap Space):** Pages that are not actively being used are stored on the hard disk. 
*   Because the processor can only execute instructions and read data directly from physical RAM via loads and stores, if a program tries to access a page that is currently on the disk, the OS must first fetch it from the disk and place it into a physical frame.

---

## 4. Virtual to Physical Address Translation

When a processor executes a memory instruction (like a `LOAD` or `STORE`), it generates a **Virtual Address**. This must be translated into a **Physical Address** by the hardware.

### Address Anatomy

An address is split into two parts:
1.  **Page Offset:** The lower bits of the address. It tells you *where* inside the page/frame the specific byte is located. 
    *   *Because pages and frames are the same size, the offset does not change during translation.*
    *   For a 4 KB page ($2^{12}$ bytes), the offset is exactly **12 bits**.
2.  **Virtual Page Number (VPN):** The upper bits of the virtual address. It identifies which virtual page is being accessed.

### The Translation Steps

1.  The processor splits the Virtual Address into the **VPN** and the **Page Offset**.
2.  The processor uses the **VPN** as an index into the current process's **Page Table**.
3.  The Page Table entry provides the corresponding **Physical Frame Number (PFN)** (if the page is in physical memory).
4.  The processor concatenates the **PFN** with the original **Page Offset** to form the final **Physical Address**.

> **📝 Example Translation:**
> *   **Virtual Address:** `0xFC51908B` (32-bit address, 4 KB pages)
> *   **Page Offset:** The lowest 12 bits (3 hex digits) $\rightarrow$ `0x08B`.
> *   **VPN:** The remaining upper bits $\rightarrow$ `0xFC519`.
> *   The processor looks up index `0xFC519` in the page table. Let's say the table says this maps to Frame `0x0152`.
> *   **Physical Address:** Frame Number (`0x0152`) + Offset (`0x08B`) $\rightarrow$ `0x015208B`.

---

## 5. The Problem with "Flat" Page Tables

A **Flat Page Table** is the simplest implementation: a single, contiguous array where every possible virtual page has an entry.

### Sizing a Flat Page Table

The size of a flat page table is calculated as:
`Total Size = (Virtual Address Space / Page Size) * Size of Page Table Entry`

**Example Scenario:**
*   **Virtual Address Space:** 32-bit ($2^{32}$ bytes = 4 GB)
*   **Page Size:** 4 KB ($2^{12}$ bytes)
*   **Entry Size:** 4 bytes (to hold the physical frame number + protection/status bits)

*Calculation:*
*   Number of Entries = $2^{32} / 2^{12} = 2^{20}$ entries (approx. 1 million entries).
*   Table Size = $2^{20} \text{ entries} * 4 \text{ bytes/entry} = 4 \text{ MB}$.

**Key Insight:** A flat page table must have an entry for *every possible page* in the virtual address space, **even if the program never uses that memory**. If an application only uses 1 MB of its 4 GB virtual space, its page table is *still* 4 MB.

### The 64-bit Bottleneck

While a 4 MB page table per process is manageable on a 32-bit system, consider a **64-bit system**:
*   Virtual Address Space: $2^{64}$ bytes.
*   Number of Entries (4 KB pages): $2^{64} / 2^{12} = 2^{52}$ entries.
*   If each entry is 8 bytes, the page table size would be **32 Petabytes ($32 \times 10^{15}$ bytes)** per process!

This is vastly larger than the physical memory of any modern machine. Therefore, flat page tables are impossible to use for large (64-bit) address spaces. Modern systems must use hierarchical (multi-level) page tables to solve this memory overhead, which will be discussed in future modules.


---

# High Performance Computer Architecture: Multi-Level Page Tables & TLBs

## 1. Introduction & The Flat Page Table Problem

### Context & Intuition
In modern operating systems, every process operates under the illusion that it has access to a massive, contiguous block of memory—this is its **Virtual Address Space**. The hardware and operating system work together to secretly map these virtual addresses to actual physical memory (RAM) using a structure called a **Page Table**.

However, **Flat Page Tables** (a single, massive array mapping every possible virtual page to a physical frame) suffer from a critical flaw: **their size is proportional to the *potential* address space, not the actual memory actively used by the application.**

### The 32-bit vs. 64-bit Problem
- **32-bit Address Space:** Even for a tiny program using a few kilobytes of memory, a flat page table for a 32-bit system (with 4 KB pages and 8-byte entries) requires **8 MB** of memory just to store the translation table. 
- **64-bit Address Space:** A flat page table would require **many petabytes** (e.g., $2^{51}$ bytes). This is physically impossible to store in modern RAM!

### The Mental Model
Imagine a massive library with a catalog index for every possible book title ever conceived, even though the library only actually owns 10 books. The catalog would take up the whole building! Most applications only use a tiny fraction of their virtual address space—typically some space at the very bottom (code, static variables, heap) and some at the very top (stack), leaving terabytes of unused "gap" space in the middle. 

---

## 2. Multi-Level Page Tables

To solve the flat page table problem, modern architectures use **Multi-Level Page Tables**. 

### How It Works
Instead of one massive array, the virtual page number is partitioned into **Outer** and **Inner** page numbers.
- **The Outer Page Table:** Acts as a high-level directory. It uses the outer page number to find the pointer to the correct inner page table.
- **The Inner Page Table:** Contains the actual Page Table Entries (PTEs) mapping to physical frames.

**The Space-Saving Magic:** If a large chunk of the virtual address space is unused (which is typical for the gap between the heap and the stack), the outer page table entry simply points to "Null," and **we don't even allocate the inner page table for that chunk**. This eliminates the need to store millions of useless empty entries.

### Example: A 32-bit Two-Level Page Table
Let's analyze the size difference using a 32-bit address space, 4 KB pages, and 8-byte entries.
- **Virtual Address Breakdown:** 12-bit offset, 20-bit page number (split into 10-bit outer, 10-bit inner).
- **Application Usage:** The app only uses the very beginning and the very end of memory.

**Size Calculation:**
1. **Outer Page Table:** $2^{10}$ entries $\times$ 8 bytes = **8 KB**.
2. **Inner Page Tables:** Since only the lowest and highest memory regions are used, the outer page table only needs to point to *two* inner page tables (one at entry `0`, one at entry `1023`). 
   - Size of one inner page table: $2^{10}$ entries $\times$ 8 bytes = 8 KB.
   - Total for two inner tables = **16 KB**.
3. **Total Size:** 8 KB (Outer) + 16 KB (Inner) = **24 KB**.

*Result: We reduced the page table footprint from **8 MB** (flat) down to just **24 KB**!*

---

## 3. Extending to 4-Level Page Tables (64-bit Systems)

Because 64-bit address spaces are so vast, two levels aren't enough. Modern x86 processors use at least 3 or 4 levels of page tables. 

### Quiz: 4-Level Page Table Space Calculation
**Scenario:** 
- 64-bit address space
- 64 KB page size (16-bit offset)
- 8-byte Page Table Entry (PTE)
- The program uses exactly 4 GB of memory ($2^{32}$ bytes).
- The 48-bit page number is split equally into 4 levels (12 bits each).

**Step-by-Step Solution:**
1. **Flat Page Table Size:** $2^{48}$ pages $\times$ 8 bytes = **$2^{51}$ bytes (2 Petabytes)**.
2. **Pages Used:** 4 GB of memory / 64 KB page size = $2^{16}$ active pages.
3. **Level 4 (Innermost) Tables:** Each table holds $2^{12}$ entries. We need $2^{16} / 2^{12} = 2^4 = 16$ innermost tables.
4. **Level 3 Tables:** One table holds $2^{12}$ pointers. We only need to point to 16 tables, so **1** Level 3 table is enough.
5. **Level 2 Tables:** Needs to point to 1 Level 3 table. **1** Level 2 table is enough.
6. **Level 1 (Outermost) Table:** Needs to point to 1 Level 2 table. **1** Level 1 table is enough.

**Total Page Tables:** 1 (L1) + 1 (L2) + 1 (L3) + 16 (L4) = **19 tables**.
**Size per Table:** $2^{12}$ entries $\times$ 8 bytes = $2^{15}$ bytes = **32 KB**.
**Total Size:** 19 $\times$ 32 KB = **608 KB**. 
*(Note: If you heard "68 KB" in the raw audio, it was a mispronunciation of "six-oh-eight" KB).*

*Result: A highly efficient 608 KB footprint compared to 2 Petabytes!*

---

## 4. The Performance Cost of Virtual-to-Physical Translation

While multi-level page tables save massive amounts of RAM, they introduce a severe performance penalty.

Whenever the CPU executes a memory instruction (e.g., `LOAD R1, [R2 + 4]`), it must translate the virtual address to a physical address. 
- If the page table is in memory, a 4-level page table requires **4 separate memory accesses** just to walk the directory structure, *before* it can even fetch the actual data!
- Memory accesses are extremely slow (often 10s to 100s of CPU cycles).

### Translation Speed Quiz
Assume: 1 cycle to compute Virtual Address, 1 cycle for a cache hit, 10 cycles for a memory access (miss penalty), and 90% cache hit rate.

* **Scenario A: 3-level page table, PTEs CANNOT be cached.**
  - Compute VA: 1 cycle
  - Page Table Walk: 3 levels $\times$ 10 cycles = 30 cycles
  - Data Access: 1 cycle (hit) + (10% $\times$ 10 cycles miss penalty) = 2 cycles
  - **Total:** 1 + 30 + 2 = **33 cycles**.

* **Scenario B: 3-level page table, PTEs CAN be cached (90% hit rate).**
  - Compute VA: 1 cycle
  - Page Table Walk: 3 levels $\times$ (1 cycle hit + 10% $\times$ 10 cycles miss) = 3 $\times$ 2 = 6 cycles
  - Data Access: 2 cycles
  - **Total:** 1 + 6 + 2 = **9 cycles**.

*Takeaway: Even with page table caching, virtual-to-physical translation makes memory accesses 3 times slower (9 cycles vs 3 cycles). We need a better hardware solution.*

---

## 5. The Translation Lookaside Buffer (TLB)

To solve the crippling performance penalty of page table walks, processors include a **Translation Lookaside Buffer (TLB)**.

### What is the TLB?
The TLB is a highly specialized, ultra-fast cache located directly on the CPU core, dedicated **exclusively** to storing virtual-to-physical address translations. 

### Why not just use the standard L1 Data Cache?
1. **Speed and Saturation:** The L1 cache is mostly filled with data. A TLB only holds translations, meaning it can be tiny (e.g., 4 to 64 entries) and blisteringly fast (often sub-cycle access times).
2. **Coverage:** One TLB entry caches the translation for an *entire page*. If a page is 4 KB, a tiny 4-entry TLB covers 16 KB of contiguous memory access.
3. **Skipping the Hierarchy:** A standard cache stores intermediate page table entries, requiring 4 lookups for a 4-level table. The TLB caches the **final** translation. One TLB lookup immediately yields the physical frame number.

### The New Memory Access Flow
1. CPU computes Virtual Address.
2. CPU checks the TLB.
   - **TLB Hit:** Instantly get the Physical Address. Access the L1 Cache. (Done in 1-2 cycles).
   - **TLB Miss:** CPU must "walk" the page table in memory, fetch the translation, update the TLB, and then try again.

---

## 6. Handling TLB Misses

When a TLB miss occurs, the system must walk the page tables to find the translation. Who does this? There are two architectural approaches:

### 1. Software TLB Miss Handling
- **How it works:** The CPU triggers an exception, handing control to the Operating System. The OS runs a software routine to look up the translation and load it into the TLB.
- **Pros:** Maximum flexibility. The OS can structure its page tables however it wants (Hash tables, Binary Trees, etc.) because the hardware doesn't need to understand them.
- **Cons:** Slower, because it requires an OS context switch and software execution.
- **Use Case:** Embedded processors (where hardware simplicity and cost are higher priorities, and TLB misses are less frequent due to regular application behavior).

### 2. Hardware TLB Miss Handling
- **How it works:** The CPU's hardware directly reads the page tables from memory, parses them, and updates the TLB entirely without OS intervention.
- **Pros:** Much faster. Handled largely like a standard cache miss.
- **Cons:** Rigid. The OS *must* use a page table format that the hardware understands (e.g., strict multi-level tables). Requires more complex CPU circuitry.
- **Use Case:** High-performance processors (like modern x86/ARM CPUs).


---

# Module 3: Advanced Caches and TLBs

Welcome to Module 3! In this module, we transition from the fundamentals of virtual memory to the intricacies of **Advanced Caches**. We'll explore how to optimize cache performance, reduce memory access times, and cleverly combine TLB and cache lookups without breaking the system.

---

## 1. TLB Sizing and Organization

### Sizing the TLB: A Mental Model
The Translation Lookaside Buffer (TLB) acts as a specialized, high-speed cache for page table entries. But how big should it be? 

**The Rule of Thumb:** The TLB needs to cover at least as much memory as the data cache to ensure that a cache hit doesn't result in a painful TLB miss.

**Intuition & Example:**
Imagine a processor with a **32 KB cache**, **64-byte blocks**, and a **4 KB page size**.
- **Minimum Coverage:** The processor accesses up to 32 KB of memory. To cover this perfectly dense chunk of memory, the TLB needs $32 \text{ KB} / 4 \text{ KB} = 8 \text{ pages}$ (8 TLB entries).
- **Maximum Fragmentation:** In reality, data is rarely dense. The cache holds $32 \text{ KB} / 64 \text{ bytes} = 512 \text{ blocks}$. In the worst-case scenario, every single one of those 512 blocks comes from a completely different page scattered across memory. To cover this scenario, the TLB would need **512 entries**.
- **Conclusion:** To match the cache's miss rate and prevent the TLB from becoming the bottleneck, the ideal TLB size for this system sits between **8 and 512 entries**. 

### TLB Organization
Because the TLB is accessed on almost every memory operation, it must be blazingly fast.
- **Associativity:** TLBs are typically **fully associative or highly set-associative**. A direct-mapped TLB would suffer from too many conflict misses (sacrificing hit rate for a speed bump that isn't necessary given the TLB's small size).
- **Typical L1 TLB Size:** Usually between **64 to 512 entries**.

### Multi-Level TLBs
What if we need more entries but can't sacrifice the single-cycle speed of a small TLB? We use a hierarchy, just like data caches!
- **L1 TLB:** Small, extremely fast (1-cycle hit time).
- **L2 TLB:** Much larger (several thousand entries), a bit slower (multiple cycles), but still *vastly* faster than doing a full page table walk in main memory.

---

## 2. TLB Performance Analysis (Quiz Walkthrough)

Let's test our understanding with a scenario:
- **Program:** Sweeps through a **1 MB array**, reading it byte-by-byte from start to finish. It repeats this sweep **10 times**.
- **Specs:** 4 KB Page Size, L1 TLB (128 entries, direct-mapped), L2 TLB (1024 entries). TLBs start empty; the array is page-aligned.

**Breaking down the numbers:**
- Array size = $2^{20}$ bytes (1 MB).
- Page size = $2^{12}$ bytes (4 KB).
- Total pages accessed = $2^{20} / 2^{12} = 256 \text{ pages}$.

**Sweep 1 Analysis:**
1. **The very first byte of a page** causes an **L1 miss** and an **L2 miss**. The translation is fetched and cached in both TLBs.
2. The next **4,095 bytes** in that same page result in **L1 hits**.
3. **L1 TLB Capacity:** As the sweep progresses, the L1 TLB (holding only 128 entries) gets full. When page 129 is accessed, page 1 is evicted. By the end of Sweep 1, only the *second half* of the array (pages 129–256) remains in L1.
4. **L2 TLB Capacity:** The L2 TLB holds 1024 entries, which easily fits all 256 pages of the array.

**Sweeps 2 through 10 Analysis:**
- **L1 TLB:** Because it only holds 128 pages, the sequential sweep will always experience a capacity miss at every page boundary. 
  - **Total L1 Misses:** 10 sweeps × 256 pages = **2,560 misses**.
- **L2 TLB:** The L2 TLB retained all 256 mappings from the first sweep! Therefore, every single one of the L1 misses during sweeps 2–10 will hit in the L2 TLB. 
  - **L2 Misses:** Only the initial **256 misses** from Sweep 1.
  - **L2 Hits:** 9 sweeps × 256 pages = **2,304 hits**.

*Takeaway:* A larger L2 TLB acts as a crucial safety net for sequential scans that exceed L1 TLB capacity.

---

## 3. Improving Cache Performance: The AMAT Model

To understand advanced caching, we use the **Average Memory Access Time (AMAT)** metric:
$$ \text{AMAT} = \text{Hit Time} + (\text{Miss Rate} \times \text{Miss Penalty}) $$

Optimizations generally fall into three categories:
1. **Reduce Hit Time**
2. **Reduce Miss Rate**
3. **Reduce Miss Penalty**

While simple solutions exist (e.g., reducing cache size or associativity to improve hit time), they often drastically increase the miss rate, negatively impacting the overall AMAT. Instead, modern processors use clever architectural tricks.

---

## 4. Advanced Techniques to Reduce Hit Time

### A. Pipelined Caches
**The Problem:** If an L1 cache takes 3 cycles to access, doing accesses sequentially forces each instruction to wait, hurting throughput.
**The Solution:** Pipeline the cache! We can break the cache access into stages (e.g., Stage 1: Read tags/valid bits; Stage 2: Compare tags & determine hit; Stage 3: Read data). 
- **Result:** We can issue a new cache access every cycle, overlapping hits and massively improving throughput. L1 caches taking 2 or 3 cycles are almost always pipelined.

### B. The TLB Bottleneck (PIPT vs. Virtually Accessed Caches)
In a standard **Physically Indexed, Physically Tagged (PIPT)** cache, the processor must translate the Virtual Address to a Physical Address *before* it can even touch the cache. 
- **Latency:** $\text{TLB Hit Time} + \text{Cache Hit Time}$ (A sequential bottleneck).

Why not just use the **Virtual Address** to index and tag the cache directly?
- **Advantages of a Virtual Cache:**
  - **Zero TLB Latency on Hits:** The hit time is just the cache hit time. TLB is only used on misses.
  - **Energy Savings:** No need to power the TLB on a cache hit.
- **Fatal Flaws of a Virtual Cache:**
  1. **Permissions:** The TLB stores read/write/execute permissions. We *must* check it anyway to ensure security.
  2. **Context Switches:** Virtual addresses are process-specific. Process A's `0x1000` is completely different data than Process B's `0x1000`. On a context switch, the OS must **flush (invalidate) the entire cache** to prevent data leaks. This causes a massive, slow burst of cache misses when the new process starts.

### C. The Best of Both Worlds: VIPT Caches
To get the speed of virtual caches and the correctness of physical caches, engineers created the **Virtually Indexed, Physically Tagged (VIPT)** cache.

**How it works:**
1. **Index:** Use the index bits from the **Virtual Address** to immediately start reading tags and data from the cache array.
2. **Translate:** *In parallel*, send the Virtual Page Number to the TLB to get the Physical Frame Number.
3. **Tag:** Once the cache outputs its tags, compare them against the **Physical Tag** returned by the TLB.

**Why VIPT is awesome:**
- **Speed:** Because the cache array and TLB are accessed in parallel, the total hit time is simply $\max(\text{TLB Time}, \text{Cache Time})$, which is usually just the cache time!
- **No Context Switch Flushing:** Since the final verification uses the *Physical* Tag, context switching is safe. Process B's virtual address might map to the same set, but its physical tag won't match Process A's lingering data. It naturally results in a clean cache miss.

### D. The VIPT Aliasing Problem
There is one massive hurdle with VIPT caches: **Aliasing**.
- **What is it?** Aliasing occurs when two different Virtual Addresses (e.g., `A` and `B`) map to the exact same Physical Address (common in shared memory or Linux `mmap`).
- **The Danger:** If `A` and `B` have different virtual index bits, they will map to *different sets* in the cache. The processor might write new data to `A`'s location in the cache, but later read stale data from `B`'s location. The cache becomes out of sync with itself!

**The Elegant Solution (The Page Offset Trick):**
Let's look at the anatomy of addresses:
- **Virtual Address:** `[ Virtual Page Number | Page Offset ]`
- **Physical Address:** `[ Physical Frame Number | Page Offset ]`
- *Notice:* The **Page Offset is exactly the same** in both addresses!

If we design the cache such that the **Cache Index** and **Block Offset** fit entirely within the **Page Offset**, then the Virtual Index is *identical* to what the Physical Index would have been!
- Because aliases `A` and `B` map to the same physical memory, they have the exact same Page Offset. 
- Therefore, they will have the exact same cache index. They will map to the exact same cache set, hit the exact same physical tag, and update the exact same block! **Aliasing is entirely prevented.**

**The Golden Constraint:**
To guarantee no aliasing in a VIPT cache, the cache geometry must satisfy:
$$ \text{Cache Index bits} + \text{Block Offset bits} \le \text{Page Offset bits} $$
Which mathematically translates to:
$$ \frac{\text{Cache Size}}{\text{Associativity}} \le \text{Page Size} $$

*Example:* With a 4 KB page size and 32-byte blocks, a direct-mapped cache can be at most 4 KB. If a CPU designer wants a 32 KB L1 cache using VIPT, they *must* make it at least 8-way set-associative ($32 \text{ KB} / 8 = 4 \text{ KB}$) to safely prevent aliasing!

---

