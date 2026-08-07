# Module 10: Cache Architecture and Types

Welcome to Module 10! In this module, we dive into the internal mechanisms of CPU caches. We will explore how a cache keeps track of the data it holds, the different ways memory blocks can be mapped into the cache, and the trade-offs of each approach.

---

## 1. Cache Tags and The Valid Bit

When a CPU requests data, it provides a memory address. The cache needs a way to quickly determine if it holds the data for that address (a **Cache Hit**) or not (a **Cache Miss**). 

### The Cache Tag
**Background Context:** A memory address is conceptually split into parts. The lowest bits form the **Block Offset**, telling us exactly which byte within a cache block we want. The rest of the bits help identify the block itself. 

- **What the Tag stores:** The cache tag stores the upper bits of the address required to uniquely identify the memory block currently sitting in a cache line. 
- **What it omits:** The tag **does not** contain the block offset. Since a cache block always begins at an aligned memory address, the block's starting address effectively has zeros in the offset bits. Storing those zeros would be a waste of precious hardware resources.
- **Key Takeaway:** The tag contains *at least one bit* from the block number (and potentially the entire block number, depending on the cache type). It contains *zero* bits from the block offset.

### The Valid Bit
**Mental Model:** Imagine moving into a new apartment with an old mailbox. Even if the mailbox has letters in it (garbage data), they aren't yours until you officially start receiving your mail there. You need an indicator—a flag—to show that the mail inside is actually valid for you.

- **The Problem:** When you turn on the processor, the cache contains random electrical signals (garbage data and garbage tags). If the tag happens to be all zeros, and the CPU requests an address that also translates to a tag of all zeros, the cache might mistakenly think it's a hit! The CPU would then consume garbage data.
- **The Solution:** We introduce a single bit of state per cache line called the **Valid Bit**.
- **How it works:**
  1. **Boot up:** On power-up, all valid bits are initialized to `0`. This forces every cache lookup to be a miss, regardless of what the tag bits say.
  2. **Cache Miss & Fetch:** The CPU goes to main memory, brings the actual data into the cache, sets the correct tag, and flips the valid bit to `1`.
  3. **Hit Condition:** A cache hit now requires **two** things to be true: 
     `Hit = (Tag matches) AND (Valid Bit == 1)`

---

## 2. Types of Caches: The Mapping Problem

Once we fetch a block from memory, where do we put it in the cache? There are three main approaches.

**Mental Model: Parking Cars**
- **Direct Mapped:** Every car's license plate mathematically dictates exactly *one* assigned parking spot. If that spot is taken, the current car must be towed out.
- **Fully Associative:** A valet parking service. You can park any car in *any* available spot. To find a car, the valet must check the license plates of every single parked car.
- **Set Associative:** Zoned parking. Your license plate dictates a specific *zone* (set). You can park in *any* open spot within that specific zone. 

### A. Direct Mapped Cache
In a Direct Mapped Cache, a specific block of memory has exactly **one** designated line where it can reside in the cache.

- **Mapping Logic:** If the cache has $L$ lines, a memory block with block number $B$ will be placed in cache line $B \pmod L$. 
- **Address Breakdown:** 
  - `Offset`: Tells us where we are within the block.
  - `Index`: Tells us exactly which cache line to look at.
  - `Tag`: Tells us which memory block is currently residing in that cache line.
  - *Note:* The tag does not need to store the index bits, because simply looking at cache line $X$ inherently means the index bits were $X$. 

#### Pros and Cons of Direct Mapped Caches
- **Pros:** 
  - **Fast Hit Time:** We only look in exactly one place. No searching required.
  - **Cheap & Energy Efficient:** Requires only one tag comparator and one valid bit checker per access.
- **Cons:** 
  - **Conflicts (High Miss Rate):** If the CPU repeatedly accesses two different blocks that map to the *same* index (e.g., Block A and Block B), they will continuously kick each other out. This is called a **conflict miss**. Even if the rest of the cache is empty, these two blocks will fight over their single shared spot.

#### Example 1: Direct Mapped Conflict Quiz
**Scenario:** A 16 KB direct mapped cache with 256-byte blocks. The CPU accesses base address `0x12345670`. Which of the following addresses will conflict with it?
1. `0x12345677`
2. `0x11335577`
3. `0x11115678`
4. `0x12341666`

**Solution Step-by-Step:**
1. **Offset:** Block size is 256 bytes ($2^8$), so the lowest 8 bits (the last 2 hex digits) are the offset. 
2. **Index Size:** $16 \text{ KB} / 256 \text{ Bytes} = 64$ blocks. We need $\log_2(64) = 6$ bits for the index.
3. **Extracting Index:** The index bits are the 6 bits immediately above the offset. For our base address `0x12345670`, the offset is `70`. The next two digits are `56` (`0101 0110` in binary). The lowest 6 bits of this are `01 0110`.
4. **Checking Choices:**
   - `0x12345677`: Same block (same tag and index). This is a hit, not a conflict.
   - `0x11335577`: Index comes from `55` (`0101 0101` -> lowest 6 bits `01 0101`). Doesn't match.
   - `0x11115678`: Index comes from `56`. Matches the index! The tag is different (`0x1111` vs `0x1234`). **This is a conflict.**
   - `0x12341666`: Index comes from `16` (`0001 0110` -> lowest 6 bits `01 0110`). Matches the index! The tag is different (due to the upper bits of the `16` vs `56`). **This is also a conflict.**

#### Example 2: Direct Mapped Access Trace
**Scenario:** A cache with 8 lines, 32 bytes per block. 
Address breakdown: Offset = 5 bits, Index = 3 bits ($\log_2(8)$).
**Access Sequence:** `0x3F1F`, `0x3F2F`, `0x3F2E`, `0x3E1F`.

- **Access 1 (`0x3F1F`):** Binary `...0001 1111`. Lowest 5 bits (`11111`) = offset. Next 3 bits (`000`) = Index 0. Goes into **Line 0**.
- **Access 2 (`0x3F2F`):** Binary `...0010 1111`. Offset = `11111`. Index (`001`) = 1. Goes into **Line 1**.
- **Access 3 (`0x3F2E`):** Binary `...0010 1110`. Offset = `11110`. Index (`001`) = 1. Matches tag in Line 1. **Hit!**
- **Access 4 (`0x3E1F`):** Binary `...0001 1111`. Offset = `11111`. Index (`000`) = 0. Goes to Line 0. Different tag! Kicks out the first block. **Conflict!**

---

### B. Fully Associative Cache
In a Fully Associative Cache, any memory block can be placed in **any** line within the cache.

- **Mapping Logic:** No assigned spots. Place the block in any invalid line. If the cache is full, use a replacement policy (like LRU) to kick a block out.
- **Address Breakdown:** 
  - `Offset`: Still needed to find the byte in the block.
  - `Index`: **0 bits**. Since the block can go anywhere, there is no "index" to point us to a specific line.
  - `Tag`: Every bit that isn't the offset is part of the tag.
- **Pros & Cons:** Eliminates conflict misses entirely, but is extremely expensive and power-hungry because every single access requires comparing the tag against *every* line in the cache simultaneously.

---

### C. Set Associative Cache
The perfect middle ground. The cache is divided into **Sets**, and each set contains $N$ **Ways** (lines). This is called an **$N$-way Set Associative Cache**.

- **Mapping Logic:** A memory block maps to exactly one **Set** (like direct mapped), but once inside that set, it can go into **any of the $N$ lines** (like fully associative). 
- **Benefit:** In a 2-way set associative cache, two different blocks that map to the same index can live in the cache simultaneously side-by-side without kicking each other out, greatly reducing conflicts.
- **Address Breakdown:**
  - `Offset`: $\log_2(\text{Block Size})$.
  - `Index`: $\log_2(\text{Number of Sets})$. *(Note: Number of Sets = Total Lines / $N$)*
  - `Tag`: Remaining bits.
- **Trade-offs:** Compared to Direct Mapped, it significantly reduces conflict misses. However, the tag check is more complex because we must now search $N$ places in parallel to find our data.

#### Example 3: 2-Way Set Associative Trace
**Scenario:** A cache with 32-byte blocks, 4 sets, 2 ways (8 lines total).
Address breakdown: Offset = 5 bits, Index = 2 bits (for 4 sets).
**Access Sequence:** `0xF303`, `0xF503`, `0xF563`, `0xEF63`.

- **Access 1 (`0xF303`):** Binary `...0000 0011`. Offset = `00011`. Index = `00` (Set 0). Placed in Set 0, Way 0.
- **Access 2 (`0xF503`):** Binary `...0000 0011`. Offset = `00011`. Index = `00` (Set 0). Placed in Set 0, Way 1. (No conflict because we have 2 ways!)
- **Access 3 (`0xF563`):** Binary `...0110 0011`. Offset = `00011`. Index = `11` (Set 3). Placed in Set 3, Way 0.
- **Access 4 (`0xEF63`):** Binary `...0110 0011`. Offset = `00011`. Index = `11` (Set 3). Placed in Set 3, Way 1.

---

## 3. The Universal Address Breakdown Formula

It's helpful to view all caches as $N$-way Set Associative caches:
- **Direct Mapped** = 1-way Set Associative.
- **Fully Associative** = $M$-way Set Associative (where $M$ is the total number of lines in the cache).

When solving cache address breakdown problems, **always process the bits from right to left (Least Significant to Most Significant):**

1. **Step 1: Offset Bits**
   - Depends *only* on the block size.
   - `Offset Bits = log2(Block Size in Bytes)`
2. **Step 2: Index Bits**
   - Depends *only* on the number of **Sets**.
   - `Number of Sets = (Total Cache Size) / (Block Size * N_ways)`
   - `Index Bits = log2(Number of Sets)`
   - *(For Fully Associative, Number of Sets = 1, so Index Bits = log2(1) = 0).*
3. **Step 3: Tag Bits**
   - The leftovers.
   - `Tag Bits = (Total Address Bits) - (Index Bits) - (Offset Bits)`
