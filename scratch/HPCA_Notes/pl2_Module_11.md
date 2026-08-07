# Module 11: Cache Replacement and Write Policies

## 1. Cache Replacement Policies

**Background & Intuition**  
When a cache miss occurs, the cache must fetch the requested data from main memory. If the set where the new block needs to be placed is already full, the cache must evict (replace) an existing block to make room. The goal of a replacement policy is to guess which block is *least* likely to be needed in the future to minimize future cache misses.

**Common Replacement Policies:**
1. **Random**: Pick a block at random. 
   - *Pros*: Extremely simple to implement; low hardware overhead.
   - *Cons*: Ignores temporal locality. Might evict a block that is heavily used.
2. **FIFO (First-In, First-Out)**: Evict the block that has been in the cache the longest.
   - *Pros*: Simple queue mechanism.
   - *Cons*: Older blocks aren't necessarily useless. A frequently accessed global variable might be the oldest block in the cache but is still heavily needed.
3. **LRU (Least Recently Used)**: Evict the block that has not been accessed for the longest time.
   - *Pros*: Highly effective because it leverages temporal locality (recently used data is likely to be used again).
   - *Cons*: Complex to implement and maintain, requiring significant hardware and energy overhead.
4. **NMRU (Not Most Recently Used)**: An approximation of LRU. It simply tracks the single most recently used block and picks randomly among the remaining blocks for eviction.
   - *Pros*: Prevents the worst-case scenario (evicting the block we *just* used) while vastly reducing the hardware overhead compared to true LRU.

---

## 2. Implementing LRU

To implement true LRU in an $N$-way set-associative cache, the hardware must track the exact access order of all $N$ blocks in each set. 

**Hardware Overhead**
- We need an **LRU Counter** for every single block.
- The counter size must be $\log_2(N)$ bits. For example:
  - 4-way associative $\rightarrow$ 2-bit counters (values 0–3).
  - 32-way associative $\rightarrow$ 5-bit counters (values 0–31).
- The counters in a set will always hold distinct values from $0$ to $N-1$. 
- **Mental Model**: $0$ represents the "coldest" (least recently used) block, and $N-1$ represents the "hottest" (most recently used) block.

**Rules for Updating LRU Counters:**
1. **On a Cache Miss (Replacement)**:
   - Evict the block whose counter is `0` (the least recently used).
   - Fetch the new block and set its counter to $N-1$ (the maximum value, making it the most recently used).
   - Decrement all other counters in the set by 1.
2. **On a Cache Hit**:
   - The accessed block is now the most recently used. Its counter jumps to $N-1$.
   - **Crucial Rule**: We do *not* blindly decrement all other counters. We only decrement the counters that were *strictly greater* than the accessed block's previous counter value. Counters that were lower remain unchanged.
   - *Why?* This ensures that all counters maintain distinct, valid values without gaps.

**The Energy Problem with LRU**
While LRU is excellent for performance (hit rate), it has a massive energy drawback. Even on a **cache hit**, multiple LRU counters must be updated. In a highly associative cache (e.g., 32-way), updating dozens of counters on every single memory access consumes a prohibitive amount of power. This is why modern processors often use LRU approximations (like Pseudo-LRU or NMRU).

### LRU Trace Quiz & Solution
**Scenario**: An 8-way set-associative cache (the transcript mentions a single set with 8 lines). Blocks A through H are in the set.
- **Initial LRU Counters**: A=7 (MRU), B=3, C=6, D=5, E=4, F=1, G=2, H=0 (LRU).
- **Access Trace**: `A`, `B`, `A`, `D`, `K (Miss)`

**Step-by-Step Execution**:
1. **Access A (Hit)**: A is already 7 (MRU). No counters change.
2. **Access B (Hit)**: B's old value is 3. B becomes 7. Counters strictly above 3 are decremented (A: 7$\rightarrow$6, C: 6$\rightarrow$5, D: 5$\rightarrow$4, E: 4$\rightarrow$3). Counters below 3 (F, G, H) stay the same.
3. **Access A (Hit)**: A's old value is 6. A becomes 7. B (was 7) decrements to 6. All others stay the same.
4. **Access D (Hit)**: D's old value is 4. D becomes 7. Counters above 4 (A, B, C) are decremented.
5. **Access K (Miss)**: We must evict the block with counter 0. H is 0. H is evicted and replaced by K. K becomes 7, and all other counters decrement by 1.

---

## 3. Write Policies

Handling memory writes is more complex than reads because writes alter the state of the data. A cache must define two distinct policies for writes: **Allocate Policy** (what to do on a write miss) and **Memory Update Policy** (what to do on a write hit).

### Allocate Policy (On a Write Miss)
When the processor wants to write to an address that is *not* currently in the cache:
1. **Write Allocate**: Bring the block from main memory into the cache, then perform the write.
   - *Intuition*: Because of temporal locality, if we write to a variable now, we will likely read or write to it again soon. Bringing it into the cache pays off.
2. **No Write Allocate**: Bypass the cache entirely and write the data directly to main memory. The cache remains unchanged.

*Note: Most modern caches are Write Allocate.*

### Memory Update Policy (On a Write Hit)
When the processor writes to an address that *is* currently in the cache:
1. **Write Through**: Update the data in the cache AND immediately send the write to main memory.
   - *Pros*: Main memory is always perfectly synchronized with the cache. Evicting a block is trivial.
   - *Cons*: Horrible for performance. Every single write instruction hits the memory bus, overwhelming the system's bandwidth.
2. **Write Back**: Update the data *only* in the cache. The main memory is left holding stale data temporarily. The updated block is only written back to main memory when it is eventually evicted from the cache.
   - *Pros*: Massive bandwidth savings. A variable updated 1,000 times in a loop will only result in *one* main memory write (upon eviction).
   - *Cons*: Adds complexity. We need a way to track which blocks have been modified so we know if a write-back is necessary.

**The Synergy**: **Write Back** is almost universally paired with **Write Allocate**. If you are utilizing a write-back cache to save memory bandwidth, you want to bring missed blocks into the cache so that subsequent writes to that block can be absorbed by the cache without hitting memory.

---

## 4. The Dirty Bit and Write Back Caches

To implement a Write Back cache efficiently, we cannot simply write every evicted block back to memory. Many blocks are purely read-only (e.g., instructions, constants). Writing read-only blocks back to memory is a waste of bandwidth.

**The Solution: The Dirty Bit**
We add a single bit of metadata to every cache line called the **Dirty Bit**.
- `0` (**Clean**): The block has only been read since it was brought from memory. It is identical to the memory's version. When evicted, it can be silently overwritten (discarded).
- `1` (**Dirty**): The block has been written to by the processor. It differs from main memory. When evicted, the cache controller *must* write the block back to main memory before overwriting the cache line.

**Mental Model**: Think of the dirty bit as a "needs to be saved" flag. When you open a Word document (read), it's clean. The moment you type a letter (write), the software flags it as "unsaved" (dirty). If you try to close the document (evict), it forces you to save it to disk (write back).

### Write Back Quiz & Solution
**Scenario**: Direct-mapped cache. All addresses (`A`, `B`, `C`, `D`) map to the exact same cache set (entry). 
- Initial state: Valid = 0, Dirty = 1 (doesn't matter since Valid is 0), Tag = A.
- Trace: `Read A`, `Read B`, `Write B`, `Read C`, `Read D`, `Write D`.

**Execution**:
1. **Read A**: Miss (Valid=0). Fetch A. Valid=1, Dirty=0. (1 Miss, 0 Write-backs)
2. **Read B**: Miss (Tags don't match). Evict A (Clean, no write-back). Fetch B. Valid=1, Dirty=0. (2 Misses, 0 Write-backs)
3. **Write B**: Hit. Update data. Dirty $\rightarrow$ 1.
4. **Read C**: Miss. Evict B. B is Dirty, so we **Write Back** B to memory. Fetch C. Valid=1, Dirty=0. (3 Misses, 1 Write-back)
5. **Read D**: Miss. Evict C (Clean, no write-back). Fetch D. Valid=1, Dirty=0. (4 Misses, 1 Write-back)
6. **Write D**: Hit. Update data. Dirty $\rightarrow$ 1.

**Final State**: 4 Misses, 1 Write-back. Cache holds `D` (Valid=1, Dirty=1).

---

## 5. Cache Summary: Putting It All Together

Let's map out exactly how a real cache operates from start to finish.

**Example System Specifications:**
- 4 KB Cache Size
- 4-way Set Associative
- 64-Byte Line Size
- Write Back & Write Allocate policies
- LRU Replacement
- 64-bit Memory Addresses

### 1. Partitioning the Address
When the processor issues a 64-bit address, the cache controller slices it into three parts: Offset, Index, and Tag.
*   **Offset Bits**: Determines the specific byte within the cache block. 
    *   $\log_2(64 \text{ bytes}) = 6 \text{ bits}$ (Bits 0–5).
*   **Index Bits**: Determines which set the block belongs to.
    *   Total Blocks = $4096 \text{ bytes} / 64 \text{ bytes/block} = 64 \text{ blocks}$.
    *   Total Sets = $64 \text{ blocks} / 4\text{-way} = 16 \text{ sets}$.
    *   $\log_2(16) = 4 \text{ bits}$ (Bits 6–9).
*   **Tag Bits**: The remaining bits used to verify identity.
    *   $64 - 6 - 4 = 54 \text{ bits}$ (Bits 10–63).

### 2. Anatomy of a Cache Line
The stated cache size (4 KB) only refers to the data capacity. The physical hardware array is larger because it must store metadata for every line:
- **Valid Bit**: 1 bit
- **Dirty Bit**: 1 bit (because it is Write Back)
- **Tag**: 54 bits
- **LRU Counter**: 2 bits (for 4-way associativity)
- **Data Payload**: 512 bits (64 bytes)
*Total size per line = 570 bits (58 bits of overhead per line).*

### 3. The Step-by-Step Cache Access Flow
1. **Locate Set**: Extract the 4 Index bits to identify which of the 16 sets to look at.
2. **Parallel Tag Read**: Read the Tag and Valid bits for all 4 blocks in that set simultaneously.
3. **Compare**: Compare the 54-bit Tag from the address against the 4 Tags read from the set.
4. **Determine Hit/Miss**: An `OR` logic gate checks if any block had both a matching Tag AND a Valid bit of 1.
   - **If HIT**:
     - A multiplexer selects the data from the winning block.
     - The 6 Offset bits are used to extract the specific requested byte(s) from the 64-byte payload.
     - If the operation is a store (write), set the Dirty bit to 1. (Hardware optimization: Just blindly set it to 1 without reading its current state to save time).
     - Update the LRU counters.
   - **If MISS**:
     - Consult the LRU counters to find the block with counter `0` (eviction candidate).
     - Check the eviction candidate's Dirty bit. If `1`, halt and write the block's data back to main memory.
     - Fetch the newly requested block from main memory.
     - Place it in the evicted slot. Update Tag, set Valid=1.
     - If it's a store (write allocate), apply the write to the cache and set Dirty=1. If it's a load, set Dirty=0.
     - Update LRU counters.

### Final Cache Summary Quiz

**System**: 256 Byte Cache, 32 Byte Line Size, 2-way Set Associative, 32-bit Address.
- **Offset**: $\log_2(32) = 5 \text{ bits}$ (Bits 0–4).
- **Number of Sets**: $(256 / 32) / 2 = 4 \text{ sets}$.
- **Index**: $\log_2(4) = 2 \text{ bits}$ (Bits 5–6).
- **Tag**: $32 - 5 - 2 = 25 \text{ bits}$ (Bits 7–31).
