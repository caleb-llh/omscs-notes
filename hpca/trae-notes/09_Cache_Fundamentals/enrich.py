import re

with open('/Users/bytedance/Documents/repos/github/omscs-notes/hpca/trae-notes/09_Cache_Fundamentals/09_Cache_Fundamentals.md', 'r') as f:
    text = f.read()

insertions = [
    (
        "This means that by observing the past behavior of a program, we can accurately predict its near-future behavior. We've seen this principle applied in branch prediction, and it is the foundational concept behind **caches**.",
        "\n\n> **⚖️ Tradeoff (Locality vs. Random Access):** Relying heavily on locality means that algorithms with purely random access patterns (e.g., hash tables, large graph traversals) will suffer severe performance penalties on modern CPUs, as they constantly bypass the cache.\n>\n> **⚠️ Common Confusion:** Locality is a property of *programs*, not hardware. The hardware (caches) is built to exploit this property, but bad code can completely defeat it."
    ),
    (
        "**Spatial Locality (Space-based reuse)**\nIf a processor accesses memory address `X`, it is highly likely to access **nearby addresses** (like `X+1`, `X+2`) in the near future.\n* **Mental Model:** If you are reading a book and just finished page 42, you are highly likely to read page 43 next. Or, if you pull a book from a shelf, you might soon need the book right next to it.",
        "\n\n> **🧠 Mental Model (Temporal vs Spatial):** Temporal locality is \"using the same tool again.\" Spatial locality is \"using the tools next to it.\"\n>\n> **⚠️ Common Confusion:** Many confuse spatial locality with just contiguous data structures. Spatial locality is about *access patterns* in time. Accessing `r[0]` then `r[1000]` then `r[2]` might be in the same array, but it has terrible spatial locality because the accesses aren't contiguous in time and fall across different cache blocks."
    ),
    (
        "**The Cache** is the processor's \"desk at home.\" Instead of going to main memory for every single location, the processor brings the data it's currently interested in—and the data immediately surrounding it—into a small, extremely fast memory structure located right next to the processor core.",
        "\n\n> **⚖️ Tradeoff (Size vs. Speed):** Why not just make the cache the size of main memory? Physics. Larger memory requires longer wires, more capacitance, and more complex routing, which increases the time to retrieve data. You cannot physically build a memory that is both 16GB and accessible in 1 cycle."
    ),
    (
        "* **Cache Miss:** The processor does not find the data in the cache. It must suffer the delay of going to the slow main memory.\n  * *The Silver Lining:* On a miss, the processor copies that data (and its neighboring data) into the cache. Thanks to the locality principle, this one slow miss sets us up for many fast hits in the future. Misses are necessary to initially populate the cache!",
        "\n\n> **⚠️ Common Confusion:** Misses are not \"errors\" or \"failures\". They are normal, expected operations. Compulsory misses (cold misses) are absolutely unavoidable the first time data is accessed."
    ),
    (
        "*(Note: Miss Time is simply `Hit Time + Miss Penalty`, because when you miss, you still spent time checking the cache first!)*",
        "\n\n> **⚖️ Tradeoff (AMAT Balancing):** Decreasing Miss Rate often involves increasing cache size or associativity, which in turn increases Hit Time. There is a sweet spot. A 99% hit rate that takes 5 cycles is worse than a 95% hit rate that takes 1 cycle if the miss penalty is moderate.\n>\n> **🧠 Mental Model:** `Miss Time` = The total time suffered on a miss. `Miss Penalty` = The *extra* time suffered on a miss compared to a hit. You always pay the `Hit Time` first to find out it's a miss."
    ),
    (
        "* **Intuition**: We keep the L1 cache small so it remains blazing fast. If it were too large, the physical distance and complex routing required to search it (hit time) would increase, defeating its purpose.",
        "\n\n> **⚖️ Tradeoff (L1 Size Limits):** L1 caches are almost universally stuck at 32KB-64KB across decades of CPU evolution. Why? Because L1 hit time must match the CPU pipeline speed (usually 1-4 cycles). As clock speeds increased, the physical distance signals can travel in one cycle shrank, strictly limiting L1 size."
    ),
    (
        "* **The Goldilocks Zone (32 - 128 Bytes)**:\n  - If the block size is too large (e.g., 1 KB), a single miss brings in a massive amount of data. In a small 16-64 KB cache, this fetch would evict many other useful blocks. If the program lacks spatial locality, we just wasted cache space and memory bandwidth fetching unused bytes.",
        "\n\n> **⚖️ Tradeoff (Block Size):**\n> * **Larger Block Size:** Increases spatial locality benefit, reduces compulsory misses. But it increases miss penalty (takes longer to fetch more bytes) and increases conflict/capacity misses (fewer lines fit in the cache).\n> * **Smaller Block Size:** Reduces conflict misses, fast to fetch. But poor spatial locality and higher overhead (more tags required for the same cache size).\n>\n> **⚠️ Common Confusion:** Fetching a 64-byte block doesn't mean fetching 64 bytes takes 64x longer. Memory buses are wide (e.g., 256 bits) and use burst transfers, so fetching 64 bytes is nearly as fast as fetching 8 bytes."
    ),
    (
        "  - **Simplifies Lookup**: Alignment ensures any given byte address maps to exactly **one** specific block in memory.",
        "\n\n> **🧠 Mental Model (Alignment):** Think of memory as a continuous tape measure, and cache blocks as rigid 64-byte rulers. You can only lay the rulers end-to-end starting at 0. You cannot shift a ruler to start at byte 17."
    ),
    (
        "* **Key Takeaway**: A cache tag always contains at least some bits from the **Block Number** (and never from the offset). It acts as a unique identifier to verify exactly which memory block is currently occupying that cache line.",
        "\n\n> **⚠️ Common Confusion:** Does the tag store the data? No! The tag is just the \"name tag\" on the door. The data is inside the room. Tag + Data payload = 1 Cache Line."
    ),
    (
        "  3. **Hit Condition:** A cache hit now requires **two** things to be true: \n     `Hit = (Tag matches) AND (Valid Bit == 1)`",
        "\n\n> **🧠 Mental Model (Valid Bit):** A hotel room might have a name on the door (Tag) and luggage inside (Data), but if the \"Occupied\" sign (Valid bit) is off, the room is considered empty, and the luggage is treated as garbage left by a previous guest."
    ),
    (
        "  - **Conflicts (High Miss Rate):** If the CPU repeatedly accesses two different blocks that map to the *same* index (e.g., Block A and Block B), they will continuously kick each other out. This is called a **conflict miss**. Even if the rest of the cache is empty, these two blocks will fight over their single shared spot.",
        "\n\n> **⚖️ Tradeoff (Direct Mapped vs Associative):**\n> * **Direct Mapped:** Fastest hit time (no multiplexer delay), lowest power. Worst hit rate (conflict misses).\n> * **Fully Associative:** Best hit rate (no conflicts). Worst hit time and power (must check ALL tags simultaneously).\n> * **Set Associative:** The sweet spot. Increases hit rate over direct mapped with only a minor hit time/power penalty."
    ),
    (
        "- **Trade-offs:** Compared to Direct Mapped, it significantly reduces conflict misses. However, the tag check is more complex because we must now search $N$ places in parallel to find our data.",
        "\n\n> **⚠️ Common Confusion:** In an N-way set associative cache, the number of sets is *less* than the number of lines. `Sets = Total Lines / N`. A 1024-line 4-way cache has 256 sets."
    ),
    (
        "3. **Step 3: Tag Bits**\n   - The leftovers.\n   - `Tag Bits = (Total Address Bits) - (Index Bits) - (Offset Bits)`",
        "\n\n> **🧠 Mental Model (Address Breakdown):**\n> * **Offset:** \"Which byte in the block?\"\n> * **Index:** \"Which row (set) in the cache table?\"\n> * **Tag:** \"Who currently occupies this row?\""
    ),
    (
        "   - *Pros*: Prevents the worst-case scenario (evicting the block we *just* used) while vastly reducing the hardware overhead compared to true LRU.",
        "\n\n> **⚖️ Tradeoff (LRU vs Random):** LRU requires storing metadata and updating it on *every single hit*, burning significant power. Random requires almost zero overhead. As associativity increases (e.g., 16-way), true LRU becomes so expensive that Random or Pseudo-LRU is preferred."
    ),
    (
        "**The Synergy**: **Write Back** is almost universally paired with **Write Allocate**. If you are utilizing a write-back cache to save memory bandwidth, you want to bring missed blocks into the cache so that subsequent writes to that block can be absorbed by the cache without hitting memory.",
        "\n\n> **⚖️ Tradeoff (Write Through vs Write Back):**\n> * **Write Through:** Simplifies cache coherence in multi-core systems (memory is always up to date). Disastrous for bandwidth.\n> * **Write Back:** Saves massive bandwidth (coalesces multiple writes to the same block). Makes cache coherence very difficult because the only valid copy of data might be hiding in a specific core's L1 cache.\n>\n> **⚠️ Common Confusion:** Write Allocate does NOT mean we only allocate on a write. It means on a write *miss*, we fetch the block into the cache just like a read miss."
    ),
    (
        "- `1` (**Dirty**): The block has been written to by the processor. It differs from main memory. When evicted, the cache controller *must* write the block back to main memory before overwriting the cache line.",
        "\n\n> **🧠 Mental Model (Dirty Bit):** Clean = \"I am a photocopy of the original.\" Dirty = \"I am the original, and the copy in the filing cabinet is outdated.\""
    ),
    (
        "     - Update LRU counters.",
        "\n\n> **⚠️ Common Confusion:** Indexing and Tag checking happen *in parallel*. The cache reads the tags of the set and compares them while simultaneously reading the data blocks. If it's a hit, it passes the correct data. If a miss, the read data is simply discarded. This parallel read is why high associativity burns so much power!"
    )
]

for old, insertion in insertions:
    if old in text:
        text = text.replace(old, old + insertion)
    else:
        print(f"COULD NOT FIND:\n{old}\n---")

with open('/Users/bytedance/Documents/repos/github/omscs-notes/hpca/trae-notes/09_Cache_Fundamentals/09_Cache_Fundamentals.md', 'w') as f:
    f.write(text)

print("Done.")
