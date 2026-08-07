# Module 4: Cache Optimizations (Part 4)

## 1. VIPT Cache Sizing and Aliasing
**Background Context:** 
In a Virtually Indexed, Physically Tagged (VIPT) cache, we want to look up the cache index using the virtual address (fast) while simultaneously translating the virtual page number to a physical tag (to verify the hit). However, if the cache index bits overlap with the virtual page number, **aliasing** can occur—this means multiple virtual addresses can map to the same physical memory but land in different cache sets, leading to inconsistency.

**The Golden Rule for VIPT:**
To completely avoid aliasing, the index bits used to access the cache *must* come exclusively from the **page offset** (which doesn't change during virtual-to-physical translation).

**Mathematical Intuition:**
- `Max Cache Size = Page Size × Associativity`

**Example:**
- **Parameters:** 8 KB page size, 16-byte block size, 4-way set associative cache.
- **Page Offset:** 8 KB = 2^13 bytes → 13 bits.
- **Block Offset:** 16 bytes = 2^4 bytes → 4 bits.
- **Available Index Bits:** 13 (offset) - 4 (block) = 9 bits.
- **Max Sets:** 2^9 = 512 sets.
- **Max Cache Size:** 512 sets × 4 ways × 16 bytes = 32 KB.
- *Shortcut:* 8 KB (Page Size) × 4 (Associativity) = 32 KB.

**Real-World Mental Model:**
Because the page size is usually fixed by the OS (e.g., 4 KB), the *only* way hardware architects can increase the size of a VIPT L1 cache without introducing aliasing is by **increasing associativity**.
- **Intel Pentium 4:** 4 KB page × 4-way = 16 KB L1 Cache.
- **Intel Core (Nehalem/Sandy Bridge/Haswell):** 4 KB page × 8-way = 32 KB L1 Cache.
- **Intel Skylake (Rumor at the time):** 4 KB page × 16-way = 64 KB L1 Cache.

---

## 2. The Trade-off: Associativity vs. Hit Time
When designing a cache, we face a fundamental tension:
- **Direct-Mapped Cache (1-way):** Very fast hit time (we only check one specific block), but suffers from a high miss rate due to frequent conflicts.
- **Highly Associative Cache (e.g., 8-way):** Low miss rate (fewer conflicts) and allows for larger VIPT caches, but has a slower hit time because the hardware must read and compare multiple tags in parallel, then multiplex the correct data.

**Goal:** Can we "cheat" associativity to get the low miss rate of an 8-way cache while maintaining the lightning-fast hit time of a direct-mapped cache?

---

## 3. Way Prediction
**Mental Model:** Imagine searching for your keys in a dresser with 8 drawers. Opening all 8 drawers at once takes time. But if you know you *usually* put them in the top-left drawer, you can guess and check that one first. If you're right, you found them instantly. If you're wrong, you then check the remaining 7.

**How it Works:**
1. Start with a set-associative cache.
2. Use the index bits to locate the set, but **guess** which "way" (line) is most likely to hit.
3. Check only that one specific tag.
   - **Correct Guess (Hit):** Hit time is extremely fast, similar to a direct-mapped cache.
   - **Incorrect Guess (Misprediction):** We fall back to a normal set-associative check on the other ways, suffering the normal, slower hit time.
   - **Not in Cache:** A standard cache miss.

**Performance Impact:**
- **Overall Miss Rate:** Remains exactly the same as the base set-associative cache.
- **Average Hit Time:** A weighted average between the fast (direct-mapped) hit time and the slow (set-associative) hit time.
- *Example Calculation:* 
  - Base 8-way cache: 2-cycle hit, 20-cycle miss penalty, 90% hit rate. AMAT = 2 + (10% × 20) = 4 cycles.
  - With Way Prediction (Assuming 1st guess hits 70% of the time, taking 1 cycle; the other 30% of the time takes 2 cycles): 
    - Average Hit Time = (70% × 1) + (30% × 2) = 1.3 cycles.
    - New AMAT = 1.3 + (10% × 20) = 3.3 cycles.

**Quiz Context:** Which caches can use way prediction? 
- Fully associative, 8-way, and 2-way caches can benefit. 
- A direct-mapped cache *cannot*, because there is only one block per set, so there is nothing to guess!

---

## 4. Replacement Policies and Hit Time
When a cache set is full, which block do we kick out? The replacement policy affects both the **miss rate** and the **hit time**.

- **Random Replacement:** Pick a random block to evict. 
  - *Pros:* Zero overhead on cache hits (fast hit time).
  - *Cons:* Bad miss rate because it often evicts useful blocks we will need soon.
- **True LRU (Least Recently Used):** Evict the oldest unused block.
  - *Pros:* Excellent miss rate.
  - *Cons:* Terrible for hit time and power. On *every single cache hit*, the cache must read, compare, and update multiple counters to maintain the exact usage order.

**Goal:** Can we approximate the smart eviction of LRU without the massive update penalty on every hit?

---

## 5. LRU Approximations
### NMRU (Not Most Recently Used)
- **Concept:** Only keep track of the *one* Most Recently Used (MRU) block in the set. When it's time to evict, randomly pick any block that is **not** the MRU block.
- **Overhead:** Extremely low. For an N-way cache, we only need a log2(N)-bit pointer per set (e.g., 2 bits for a 4-way cache). True LRU requires N counters per set.
- **Hit Activity:** On a hit, we simply update the pointer to point to the accessed block. Very fast.
- **Drawback:** It doesn't know the exact order of the remaining blocks, so it might accidentally evict the 2nd most recently used block instead of the true least recently used block.

### PLRU (Pseudo LRU)
- **Concept:** A tighter approximation of LRU that uses exactly 1 bit per cache line (e.g., 8 bits for an 8-way set).
- **Mechanism:**
  1. All bits start at `0`.
  2. On a hit, set that block's bit to `1` (marking it as "recently used").
  3. On a miss, evict any block whose bit is `0`.
  4. If setting a bit to `1` would cause *all* bits in the set to become `1`, instead set that block to `1` and reset all other blocks to `0`.
- **Behavior Spectrum:**
  - When only 1 bit is set, it acts like NMRU.
  - When all but 1 bit are set, it acts exactly like True LRU (the single `0` is definitively the least recently used).
- **Pros:** Fast hit updates (just flip a single bit to `1`) and much lower storage overhead than True LRU, while achieving a miss rate very close to True LRU.

---

## 6. Reducing the Miss Rate: The Three C's
To reduce the Average Memory Access Time (AMAT), we must understand why cache misses happen. We categorize misses into the **Three C's**:

1. **Compulsory Misses:** The very first time a block is accessed. You *have* to bring it into the cache. 
   - *Mental Check:* Even an infinitely large cache starting empty would suffer from compulsory misses.
2. **Capacity Misses:** The cache simply isn't big enough to hold all the data the program is actively using. 
   - *Mental Check:* A miss that wouldn't happen in an infinite cache, but *would* still happen in a fully associative cache of the exact same size.
3. **Conflict Misses:** Multiple blocks map to the same set, and the set fills up, even though there might be empty space elsewhere in the cache. 
   - *Mental Check:* A miss that happens in a set-associative cache, but *would not* happen if the cache were fully associative.

**Solutions:**
- Larger cache size → Reduces capacity misses.
- Higher associativity → Reduces conflict misses.
- Better replacement policy → Reduces conflict misses.

---

## 7. Larger Cache Blocks
Another strategy to reduce the miss rate is to increase the block size (e.g., fetching 64 bytes at a time instead of 16 bytes).

- **The Benefit:** Brings in more neighboring words on a single miss. If the program has good **spatial locality** (e.g., iterating through an array), subsequent accesses to those neighboring words become hits instead of misses.
- **The Danger ("Junk" Data):** If spatial locality is poor, a larger block size brings in words that the program will never use. This "junk" takes up valuable space, evicting useful data and increasing **capacity misses**.
- **Cache Size Sensitivity:**
  - **Small Caches:** Very sensitive to junk data. Increasing block size helps initially, but the miss rate quickly spikes (e.g., around a 64-byte block size) as the limited capacity is overwhelmed by unused data.
  - **Large Caches:** Can absorb the junk data without immediately evicting useful blocks. In a large cache, the miss rate continues to drop for much larger block sizes (e.g., up to 256 bytes) before eventually rising.
