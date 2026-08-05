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
