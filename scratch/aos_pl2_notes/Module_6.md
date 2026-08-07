# Playlist 2: Module 6 - Distributed Systems (Global Memory System)

## 1. Introduction
- **Distributed Systems Innovation:** Technological innovations in distributed systems often emerge from academia due to a lack of market or compliance pressures, leading to "out-of-the-box" thinking.
- **Enduring Value:** The byproducts and implementation techniques of thought experiments often have a more lasting impact than the original visions (e.g., Java emerged from failed video-on-demand trials).
- **Core Theme of Module:** Memory is a critical, precious resource. Advances in local area network (LAN) technology allow leveraging the idle physical memory of peer nodes in a cluster to overcome local memory shortages.
- **Three Subsystems Discussed:**
  1. **Global Memory System (GMS):** Using peer memory for paging across a LAN.
  2. **Distributed Shared Memory (DSM):** Providing a shared memory abstraction in a cluster.
  3. **Distributed File System:** Using cluster memory for cooperative caching of files.

## 2. Context for Global Memory System (GMS)
- **Virtual Memory Manager (VMM):** Gives processes the illusion of having a large virtual address space, even though only a portion (the **working set**) is actually loaded into physical memory. Missing pages are swapped in and out from the disk.
- **Memory Pressure:** The amount of physical memory required to keep all currently executing processes on a node running efficiently. Memory pressure varies across nodes in a LAN; some nodes are heavily loaded, while others sit idle.
- **The GMS Concept:** Instead of paging out to a slow local disk when experiencing memory pressure, a node can page out to the idle physical memory (cluster memory) of a peer node over the network.
- **Network Speeds:** Gigabit and 10-Gigabit Ethernet make fetching a page from a remote node's memory faster than local disk I/O (which is bound by seek and rotational latency, typically capping around 200 MB/s).
- **Extended Memory Hierarchy:** Processor $\rightarrow$ Caches $\rightarrow$ Main Memory $\rightarrow$ **Cluster Memory (via GMS)** $\rightarrow$ Disk.
- **Reliability:** GMS trades network communication for disk I/O **only for reads**. Writes still go to the disk (the disk always holds a copy of all pages). GMS only houses clean (non-dirty) pages in peer memory. If a node crashes, no data is lost because the disk retains the master copies.

## 3. GMS Basics
- **Cache:** In GMS terminology, "cache" refers strictly to Physical Memory (DRAM).
- **Memory Split:** Physical memory on each node is dynamically partitioned into two parts:
  - **Local Part:** Holds the working set of currently executing processes on the local node.
  - **Global Part:** The "community service" portion. It acts as a surrogate for the disk, holding pages swapped out by peer nodes on the network.
- **Dynamic Boundary:** The boundary between Local and Global memory shifts based on node activity. An idle workstation shrinks its Local part and expands its Global part to serve peers.
- **Page States:**
  - **Private:** A page exclusive to a single process.
  - **Shared:** A page actively used by processes spanning multiple nodes.
  - *Rule:* The **Global Part** only ever holds **Private** (and clean) pages. The **Local Part** can hold Private or Shared pages.
- **Coherence:** GMS does **not** manage memory coherence for shared pages. GMS acts strictly as a paging facility; coherence is an application-level problem.
- **Page Replacement:** GMS aims to approximate a **Global LRU (Least Recently Used)** algorithm, ensuring the globally oldest page across the entire cluster is the one evicted to the disk when total cluster memory is full.

## 4. Handling Page Faults (Four Scenarios)
When a node (Host P) page faults on a page $X$, GMS locates the page.

* **Case 1: $X$ is in a peer's Global Cache (Common Case)**
  - $X$ is located in Host Q's global cache and sent to P.
  - **Host P:** Local memory increases by 1 (adds $X$ to working set), Global memory decreases by 1. P sends its oldest global page ($Y$) to Q to make room.
  - **Host Q:** Trades $Y$ for $X$. No change to Local/Global split.
* **Case 2: Memory pressure on P is excessive (P's Global Cache is empty)**
  - P's Global part is already 0. P replaces an older page from its own Local part to make room for $X$.
  - **Host P:** No change to Local/Global split (replaces a local page with another local page).
  - **Host Q:** Remains unchanged.
* **Case 3: Faulting page is only on the Disk**
  - P fetches $X$ from the disk. (P's Local +1, Global -1).
  - P sends an arbitrary Global page to Host R (the node with the *globally oldest* page in the cluster).
  - **Host R:** Evicts its globally oldest page to the disk. 
    - If R's oldest page was Global: No change to R's Local/Global split.
    - If R's oldest page was Local: R's Local shrinks by 1, Global increases by 1 (increasing its capacity for community service).
* **Case 4: Faulting page is actively shared**
  - $X$ is actively used in Host Q's Local cache. Q keeps its copy; a new copy is sent to P.
  - **Host P:** Local +1, Global -1.
  - **Host Q:** Unchanged.
  - Total cluster memory pressure increases by 1. P must send a Global page to Host R (node with the globally oldest page), causing R to evict a page to the disk.

## 5. Age Management ("Geriatrics")
GMS approximates Global LRU without overloading any single node. Management is distributed across **Epochs**.

- **Epoch Parameters:** An epoch is bounded by time ($T$, e.g., a few seconds) or space ($M$ page replacements, e.g., thousands).
- **The Initiator (Manager):** At the start of an epoch, all nodes send the age of their pages to the Initiator node.
- **Initiator Computations:**
  1. **Minimum Age:** The age of the $M$-th oldest page. Any page older than this is slated for replacement in the upcoming epoch.
  2. **Weight Distribution ($W_i$):** The fraction of the $M$ replacements expected to come from each node $i$.
- **Manager Handoff:** To distribute load, the Initiator for the *next* epoch is chosen as the node with the highest weight (the least active node hosting the oldest pages). Nodes determine this locally from the weight distribution vector.
- **Acting Locally (Page Eviction):**
  - When evicting a page, a node checks its age against the **Minimum Age**.
  - **If Age > Minimum Age:** The page is discarded immediately (it was going to be replaced to disk this epoch anyway).
  - **If Age < Minimum Age:** The page is active. The node sends it to a peer node's global cache. The target peer is selected probabilistically based on the weight distribution ($W_i$).
- **Philosophy:** Think Globally (Epoch setup/Min Age calculation), Act Locally (Page faults/Evictions).

## 6. Implementation in Unix (OSF/1)
GMS was implemented on DEC's OSF/1 operating system, requiring modifications to the OS core.

- **OS Memory Components:**
  - **Virtual Memory Manager (VM):** Manages process virtual address space (Heap, Stack). Handled pages are called **Anonymous Pages**.
  - **Unified Buffer Cache (UBC):** Caches file system reads/writes and memory-mapped files.
- **GMS Integration:** VM and UBC are modified to call GMS instead of the disk when page faults occur. Clean page evictions are intercepted by GMS to be sent to cluster memory.
- **Collecting Age Information:**
  - *UBC Pages:* Easy to track because applications make explicit read/write system calls.
  - *Anonymous Pages (VM):* Difficult because CPU hardware handles memory access. GMS solves this by having a daemon periodically dump the **Translation Lookaside Buffer (TLB)** contents to track recently accessed pages.
- **Paging Daemon:** Modified to trigger when the free list falls below a threshold. Instead of dropping clean pages to the disk, it passes them to GMS to route to peer nodes based on weight information.

## 7. Distributed Data Structures
GMS uses specialized structures to map virtual addresses across the cluster.

- **Universal ID (UID):** Converts a local virtual address into a globally unique identifier. 
  - `UID = [IP Address] + [Disk Partition] + [Inode] + [Offset]`
- **Core Data Structures:**
  1. **PFD (Page Frame Directory):** Equivalent to a page table. Maps a UID to a specific Physical Page Frame. (States: Local-Private, Local-Shared, Global-Private, Disk).
  2. **GCD (Global Cache Directory):** Maps a UID to the Node ID that currently holds the PFD for that page.
  3. **POD (Page Ownership Directory):** A globally replicated structure. Maps a UID to the Owner Node ID (the node responsible for keeping the GCD for that UID space).
- **Page Fault Lookup Flow:**
  - `Virtual Address` $\rightarrow$ `UID` $\rightarrow$ Look up `POD` $\rightarrow$ Contact `Owner Node` $\rightarrow$ Look up `GCD` $\rightarrow$ Contact `PFD Node` $\rightarrow$ Fetch Page.
- **Performance Optimization (The Common Case):**
  - For non-shared pages, the POD, GCD, and faulting process usually reside on the **same node**.
  - Network communication is heavily reduced; external calls are typically only required to actually fetch the page from the remote PFD node, not to perform the lookups.

## 8. Conclusion
- Taking a distributed systems concept (like network paging) to full implementation requires heavy lifting, especially in OS modification and corner-case handling.
- While paging over a LAN was a thought experiment suitable for its time, its true value shines in modern **Data Centers** where thousands of nodes are centrally owned and operated.
- The enduring contributions of GMS are its **distributed data structures**, **decentralized algorithms**, and **age management techniques**, which remain highly relevant in modern systems research.