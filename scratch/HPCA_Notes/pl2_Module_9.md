# Playlist 2 Module 9: Cache Basics and Organization

## 1. Introduction to Hit and Miss Rates
* **Mental Model**: Think of a cache as a small, fast desk organizer and main memory as a large, slow filing cabinet. 
* **Hit Rate**: The fraction of memory accesses found in the cache (e.g., finding the document on your desk).
* **Miss Rate**: The fraction of accesses *not* found in the cache, requiring a fetch from main memory.
* **Relationship**: $\text{Hit Rate} + \text{Miss Rate} = 1$
* **Goal of a Well-Designed Cache**: 
  - **Hit Rate $\approx 1$ (Almost 100%)**: We want the vast majority of accesses to be served quickly from the cache.
  - **Miss Rate $\approx 0$**: We want to minimize slow memory accesses.
  - Therefore, the Hit Rate should be strictly **larger** than the Miss Rate. They should never be balanced or equal, as that would mean paying the full memory latency 50% of the time!

## 2. Cache Size in Real Processors
* **Context**: Modern processors use a hierarchy of caches (L1, L2, L3) to balance speed and capacity. 
* **Level 1 (L1) Cache**: The closest, smallest, and fastest cache that directly serves read and write requests from the processor.
* **Typical L1 Characteristics**:
  - **Size**: 16 KB to 64 KB.
  - **Hit Time**: 1 to 3 processor cycles (extremely fast compared to main memory, which takes hundreds of cycles).
  - **Hit Rate**: Around 90% (only 1 out of 10 accesses miss and go to the next level of the memory hierarchy).
* **Intuition**: We keep the L1 cache small so it remains blazing fast. If it were too large, the physical distance and complex routing required to search it (hit time) would increase, defeating its purpose.

## 3. Cache Organization: Block (Line) Size
* **Concept**: A cache is conceptually a table. Each entry in this table holds a chunk of data called a **Block** (or **Line**). 
* **Block/Line Size**: The number of bytes fetched from memory on a cache miss and stored together in a single cache entry.
* **Why not 1-byte blocks?**
  - Processors often access 4-byte (word) or 8-byte chunks. A 1-byte block would require 4 separate cache lookups for a single 4-byte load/store, which is terribly inefficient and complicates the hardware.
* **Exploiting Spatial Locality**: 
  - When you access an address, you're likely to access nearby addresses soon (e.g., reading sequentially through an array). By fetching a block of 32 to 128 bytes, we bring in the requested data *plus* neighboring data, satisfying future accesses for free.
* **The Goldilocks Zone (32 - 128 Bytes)**:
  - If the block size is too large (e.g., 1 KB), a single miss brings in a massive amount of data. In a small 16-64 KB cache, this fetch would evict many other useful blocks. If the program lacks spatial locality, we just wasted cache space and memory bandwidth fetching unused bytes.

### Example: Block Size and Locality
Imagine a 32 KB cache with 64-byte blocks. A program accesses $N$ independent scalar variables (4 bytes each) with high *temporal* locality (accessed repeatedly) but zero *spatial* locality (they are scattered far apart in memory).
* **How many variables ($N$) can fit while maintaining a high hit rate?**
  - Since there is no spatial locality, each 4-byte variable requires its own 64-byte block in the cache (the other 60 bytes fetched in the block go completely unused).
  - Total blocks available = $\frac{32 \text{ KB}}{64 \text{ bytes}} = 512$ blocks.
  - Thus, the cache can hold at most **512 variables**. If $N > 512$, the cache will start evicting blocks, severely hurting the hit rate.

## 4. Cache Alignment
* **Rule**: Cache blocks must be **block-aligned** in memory. 
* **Meaning**: A 64-byte block can only start at memory addresses that are multiples of 64 (e.g., Address 0-63, 64-127, 128-191).
* **Why?**
  - **Avoids Duplication/Overlap**: If a block could start anywhere (e.g., 1-64, 2-65), a single byte (like address 27) could exist in many different overlapping blocks. On a write, the cache controller would have to find and update all overlapping copies to maintain consistency, which is a hardware nightmare.
  - **Simplifies Lookup**: Alignment ensures any given byte address maps to exactly **one** specific block in memory.

## 5. Cache Lines vs. Memory Blocks
* **Memory** is divided into fixed-size **blocks** (e.g., Block 0, Block 1, Block 2...).
* **Cache** is divided into fixed-size empty slots called **lines**.
* **Terminology**:
  - **Line**: The physical slot/container in the cache hardware.
  - **Block**: The actual data content fetched from memory that sits inside the line.
  - Note: In practice, Line size and Block size mean the same amount of bytes.

### Good vs. Bad Line Sizes (Intuition Check)
For a small 2 KB cache, which line sizes make sense?
- **1 byte**: Bad. No spatial locality benefits; multiple lookups required for a single word.
- **48 bytes**: Bad. Not a power of 2. Hardware would require slow division by 48 to find block boundaries instead of fast bit-shifting.
- **1 KB**: Bad. Too large for a 2 KB cache; the cache would only fit 2 lines total, causing severe capacity limits and constant evictions.
- **32 bytes & 64 bytes**: Good. They are powers of 2, capture enough spatial locality, and allow many lines to fit in a 2 KB cache.

## 6. Addressing: Block Number and Block Offset
When the processor generates a memory address (e.g., 32 bits), the cache controller splits it into parts to locate the data.
1. **Block Offset**: The lowest (least significant) bits of the address. They tell us exactly *where* the requested byte is located inside the fetched block.
   - Calculated as $\log_2(\text{Block Size})$.
   - E.g., For a 16-byte block, we need $\log_2(16) = 4$ bits for the offset.
2. **Block Number**: The remaining upper bits of the address. They identify *which* overall block in memory we are looking for.

### Example Breakdown
- **Address**: 16-bit binary `1010 1010 1111 0101`
- **Block Size**: 32 bytes.
- **Offset**: $\log_2(32) = 5$ bits. The lowest 5 bits (`1 0101`) form the Block Offset.
- **Block Number**: The remaining 11 upper bits (`1010 1010 111`) form the Block Number.

## 7. Cache Tags
* **The Problem**: Once we look inside the cache, how do we know if a given cache line contains the specific memory block we want?
* **The Solution**: **Tags**. 
* Along with the actual data block, every cache line stores a small piece of metadata called a "tag". 
* **How it works**: 
  - The cache extracts the **Block Number** from the processor's requested address.
  - It compares this Block Number against the tags stored in the cache.
  - If there is a match (**Hit**), the cache uses the **Block Offset** to extract the specific bytes from that line's data.
  - If there is no match (**Miss**), it fetches the block from memory, places it in an available cache line, and updates that line's tag with the new Block Number.
* **Key Takeaway**: A cache tag always contains at least some bits from the **Block Number** (and never from the offset). It acts as a unique identifier to verify exactly which memory block is currently occupying that cache line.
