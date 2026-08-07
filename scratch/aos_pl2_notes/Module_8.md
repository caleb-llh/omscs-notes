# Module 8: Distributed Shared Memory (DSM) and Distributed File Systems (DFS)

## 1. Lazy Release Consistency (LRC) with Multi-Writer Coherence Protocol
- **Overview**: A protocol that maintains coherence at the page granularity (to integrate with the OS) while allowing multiple writers to simultaneously modify the same page. This is critical for preventing false sharing when different data structures reside on the same page.
- **Mechanism (TreadMarks System)**:
  - A processor (e.g., P1) acquires a lock (`L`) and modifies data structures contained within pages (e.g., X, Y, Z).
  - The OS has no knowledge of the association between the lock `L` and the modified pages; it only knows these pages were modified during the critical section.
  - At the release of the lock, the system computes a **diff** between the original page and the modified page (e.g., XD, YD, ZD).
- **Lock Acquisition and Invalidation**:
  - When another processor (e.g., P2) requests the same lock `L`, the DSM software invalidates the local copies of the pages known to be modified by the previous lock holder.
  - This invalidation at lock acquisition is consistent with the **Lazy Release Consistency (LRC)** model.
- **Procrastinated Updates**:
  - When P2 enters its critical section and accesses an invalidated page (e.g., X), a page fault occurs.
  - The DSM software fetches the original, pristine version of the page from the page's owner.
  - It also fetches the diff(s) created by previous lock holder(s) and applies them to the original page to construct the current version.
  - If multiple processors modified the page under the same lock previously, all relevant diffs are applied in order.
- **Handling Multiple Writers**:
  - Different threads on different processors can modify the same page simultaneously, provided they use **different locks** (e.g., P1 uses `L1`, P4 uses `L2`).
  - Diffs are strictly associated with the specific lock governing the critical section.
  - When P2 acquires `L1`, it only fetches diffs associated with `L1`, safely ignoring changes made under `L2`. This avoids unnecessary communication.

## 2. Implementation of Multi-Writer Protocol
- **Twin Creation**:
  - When a thread first writes to a page (e.g., X), the OS creates a **twin** (an exact physical memory copy of the original page).
  - The twin is not mapped into the page table; it serves purely as a backup.
  - The original page is made writable so the thread can modify it.
- **Diff Computation (at Release)**:
  - At the lock release point, the DSM software compares the modified page with the twin.
  - It creates a **run-length encoded diff** (recording the starting point, length, and content of the changes) to save space, as typically only portions of a page are modified.
  - After diff computation, the original page is **write-protected** to ensure any future writes trigger coherence actions.
  - The twin is destroyed, freeing up physical memory.
- **Garbage Collection and Reuse**:
  - The diff is kept on the node to be provided to future lock acquirers.
  - Once updated via diffs upon a subsequent page fault, the page becomes ready for the new lock holder.

## 3. Non-Page-Based DSM
To avoid page-level false sharing entirely, some systems track coherence at a finer granularity without relying on OS page faults.
- **Library-Based DSM**:
  - Shared variables are explicitly annotated using a programming library.
  - The compiler/binary inserts a trap at every point of access to these shared variables.
  - The trap invokes the DSM software to handle coherence (e.g., fetching data) without requiring OS page-level support.
  - *Examples*: Shasta (DEC), Beehive (Georgia Tech).
- **Structured DSM**:
  - Coherence is maintained at the level of application-meaningful data abstractions rather than memory locations.
  - These abstractions are manipulated via API calls provided by the language runtime.
  - The runtime handles necessary coherence actions and data fetching during the API call.
  - *Examples*: Linda, Orca, Stampede (Georgia Tech), Stampede RT, PTS (Persistent Temporal Streams).

## 4. DSM Scalability and Speedup
- **Expectation vs. Reality**: Developers expect linear performance scaling as processors are added. However, software-implemented DSM introduces increasing communication overhead, which mitigates actual speedup.
- **Computation-to-Communication Ratio**:
  - For speedup, computation must significantly outweigh communication.
  - "Shared memory scales really well when you don't share memory." (Chuck Thacker).
  - Critical sections must be substantial (Hefty) to justify the coherence overhead.
- **The Problem with Pointers**:
  - Code with dynamic data structures manipulated via pointers can lead to severe implicit network communication.
  - Following a pointer might transparently trigger a fetch across the LAN.
  - Pointer-heavy code is the "bane of distributed shared memory."
- **Conclusion**:
  - Traditional DSM (a shared memory threads package for a cluster) is effectively dead.
  - **Structured DSM** remains attractive for reducing the programming burden in distributed applications.

## 5. Network File Systems (NFS)
- **Trivia**: The first Network File System (NFS) was built by **Sun Microsystems** in **1985**.
- **Centralized Architecture**:
  - Clients distributed over a LAN access a central file server.
  - To mitigate slow disk speeds, the server caches retrieved files in its memory.
- **Bottlenecks**:
  - A single centralized server limits scalability.
  - The server's I/O bus bandwidth is limited for fetching data and metadata.
  - The file cache is constrained by the memory capacity of the single server.

## 6. Distributed File Systems (DFS)
- **Vision**: Distribute files and metadata across several servers in the network to eliminate centralized bottlenecks.
- **Benefits**:
  - **Aggregated I/O Bandwidth**: Clients can retrieve data from multiple servers simultaneously.
  - **Distributed Metadata**: Management is spread across multiple nodes.
  - **Cooperative Caching**:
    - The file cache expands to include the memory of all servers (and potentially clients).
    - Avoids disk accesses by retrieving data from a peer's memory if they recently accessed it.
- **Serverless File System**:
  - In extreme cases, all nodes in the cluster act interchangeably as clients and servers, distributing management, serving, and caching equally.

## 7. Lesson Outline & Prerequisites
- **Goal**: Intelligently utilize cluster memory for metadata management and cooperative file caching to minimize slow disk access.
- **Prerequisites**: A solid understanding of file systems is essential (e.g., comparable to the undergraduate systems course CS 2200 at Georgia Tech).
