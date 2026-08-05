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