# The Bw-Tree: A B-tree for New Hardware Platforms

**Authors**: Justin J. Levandoski, David B. Lomet, Sudipta Sengupta (Microsoft Research)  
**Published**: 2013

---

## 1. Introduction and Motivation

> **Context:** Traditional B-trees were designed for magnetic disks (where random I/O is slow) and single-core CPUs. In the modern era, flash storage (SSDs) and multi-core CPUs dominate. SSDs handle random reads well but struggle with random writes (due to erase cycles). Multi-core CPUs suffer from cache invalidations when multiple threads lock and modify the same memory. The Bw-Tree was built to address these specific modern hardware characteristics.

The Bw-Tree is a new form of B-tree designed as a high-performance Atomic Record Store (ARS) tailored for modern hardware. 
Traditional database systems rely on architectures designed when disks were the primary storage and processors experienced steady single-core performance gains. The new hardware environment has changed this:
1. **Multi-core Processors**: High concurrency is required to exploit multi-core CPUs. Traditional latching (locking) blocks threads and limits scalability. Updating memory in-place causes CPU cache invalidations, hurting performance.
2. **Modern Storage (Flash/SSD)**: Flash offers higher random and sequential reads than magnetic disks but requires an erase cycle before writing, making random writes slower than sequential writes. 

**Key Contributions of the Bw-Tree:**
- **Mapping Table**: Virtualizes the location and size of pages, isolating updates.
- **Delta Updating**: Updates are prepended as deltas rather than updating pages in-place. Allows for **latch-free** (lock-free) concurrent access and preserves processor caches.
- **Latch-free Structure Modification Operations (SMOs)**: Page splits and merges are decomposed into multiple atomic operations, allowing threads to complete in-progress SMOs without blocking.
- **Log Structured Store (LSS)**: Efficient storage manager that writes only page deltas sequentially, optimizing for flash storage.

---

## 2. Bw-Tree Architecture

> **Mental Model:** In a standard B-tree, parent nodes store physical memory addresses pointing to their child nodes. In the Bw-Tree, parents store logical Page IDs (PIDs). A central "Mapping Table" translates these PIDs to actual physical addresses. This indirection means a page can move in memory without having to update its parent.

The Bw-Tree maintains the logarithmic access of a classic $B^+$-tree but departs significantly in its architectural execution.

### The Mapping Table
The core enabler of the Bw-Tree is a mapping table that translates a logical **Page ID (PID)** into either:
- A memory pointer (if the page is in main memory).
- A flash offset (if the page is on stable storage).

All links between Bw-tree nodes (search pointers, sibling links) are PIDs, not physical pointers. This severs the connection between physical location and inter-node links, meaning a node can change its physical location on every update without requiring the parent to be updated.

### Delta Updating (Latch-Free)
Bw-tree pages are logical and elastic. Pages are never updated in-place.
- To modify a page (insert/update/delete), a **delta record** describing the change is created.
- The delta record physically points to the page's current address.
- An atomic **Compare-and-Swap (CAS)** instruction replaces the page's address in the mapping table with the new delta record's address.
- Only one updater wins the CAS. Failed updaters retry. 

This technique ensures the Bw-tree is entirely **latch-free** and avoids cache line invalidations since prior state is untouched. 

---

## 3. In-Memory Latch-Free Pages

> **Intuition:** Instead of locking a page and overwriting its data (which causes CPU caches to invalidate across other cores), the Bw-Tree just tacks on a "sticky note" (a delta record) to the front of the page saying what changed. Since it's only appending new data and never overwriting old data, threads don't step on each other's toes, allowing lock-free (latch-free) concurrency.

A physical page in memory consists of a base page (a standard B-tree node) with a chain of delta records prepended to it.

### Page Search
To search a page, a thread traverses the delta chain first. 
- If the search key is found in an insert or update delta, it returns the record.
- If it is found in a delete delta, the search fails.
- If not found in the chain, it performs a binary search on the base page.

### Page Consolidation
To prevent delta chains from growing too long (which degrades search performance), pages are occasionally consolidated.
- A thread creates a new consolidated base page combining the old base page and all updates in the delta chain.
- The new page is installed in the mapping table via CAS.
- The old page and delta chain are safely garbage collected using an **epoch-based** mechanism (ensuring memory is reclaimed only after all active threads observing it have finished).

---

## 4. Structure Modifications (SMOs)

Latches are completely avoided, even for complex structural changes like node splits and merges. Because a single CAS cannot update multiple pages (e.g., a child and a parent simultaneously), SMOs are broken into atomic steps using a **B-link** tree design (pages have side-links to their right siblings).

### Node Split
A split requires two "half-splits":
1. **Child Split**: A new sibling page $Q$ is allocated and populated with the upper half of page $P$'s records. A **split delta** is prepended to $P$, which invalidates the upper keys in $P$ and provides a logical pointer to $Q$. This is installed via CAS on $P$'s mapping table entry. The index is now valid and searchable.
2. **Parent Update**: An **index entry delta** is prepended to the parent node $O$, pointing directly to $Q$. 

### Node Merge
Merging a sparse node $R$ into its left sibling $L$ requires three atomic steps:
1. **Marking for Delete**: A **remove node delta** is prepended to $R$.
2. **Merging Children**: A **node merge delta** is prepended to $L$, pointing to the contents of $R$, logically transferring the key space to $L$.
3. **Parent Update**: An **index term delete delta** is prepended to the parent $P$, removing the pointer to $R$ and updating the key range of $L$.

**Serializing SMOs**: If a thread encounters an incomplete SMO (e.g., trying to traverse a split delta but the parent hasn't been updated), the thread *helps complete the SMO* before proceeding with its own operation. This prevents threads from waiting.

---

## 5. Cache and Storage Management (Log Structured Store)

> **Tradeoff:** Using delta chains makes writes extremely fast (just an atomic pointer swap) and prevents lock contention. However, it slows down reads, because reading a page now requires scanning through a linked list of deltas before hitting the base page. The system must periodically "consolidate" (squash) these deltas into a new base page to keep read performance acceptable.

The cache layer manages the mapping table and page flushes to the Log Structured Store (LSS).

### Write-Ahead Log (WAL) and Incremental Flushing
- When a page is flushed to the LSS, the cache manager only marshals the **delta records** created since the last flush. 
- This dramatically reduces the amount of data written to flash, increasing the number of pages that fit in a flush buffer and reducing write amplification.
- The Bw-tree supports WAL non-blocking flushes by explicitly ignoring deltas with Log Sequence Numbers (LSNs) greater than the End of Stable Log (ESL).

### Flash Storage Efficiency
By batching pages and deltas into large buffers and writing them sequentially to flash, the LSS eliminates random writes, maximizing flash drive throughput.

---

## 6. Performance Evaluation Results

The Bw-Tree was evaluated against BerkeleyDB (a traditional B-tree architecture with page-level latching) and latch-free Skip Lists.

- **Vs. BerkeleyDB**: The Bw-Tree achieved nearly **19x higher throughput** on a gaming workload (Xbox LIVE trace) and 8.6x higher on a deduplication workload. The gains are attributed to latch-freedom (allowing 99% CPU utilization compared to BerkeleyDB's 60%) and the lack of CPU cache invalidations.
- **Vs. Skip Lists**: The Bw-Tree outperformed a latch-free skip list by **3.7x to 4.4x**. While both are latch-free, the Bw-tree performs binary searches on contiguous memory blocks (base pages), whereas skip lists require heavy pointer chasing, resulting in frequent cache misses. Profiling showed that almost 90% of Bw-tree memory reads hit the L1 or L2 CPU caches, compared to 75% for the skip list.

## 7. Summary

The Bw-Tree reimagines the B-tree for high-concurrency multi-core processors and flash storage. Through a mapping table, delta updating, latch-free SMOs, and a log-structured store, it completely eliminates thread blocking and update-in-place operations. This design paradigm yields outstanding throughput and CPU cache efficiency, significantly outperforming legacy architectures.
