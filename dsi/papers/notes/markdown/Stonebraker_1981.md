# Operating System Support for Database Management

## Abstract
Several operating system (OS) services are examined regarding their applicability for database management systems (DBMS). The services include buffer pool management, the file system, scheduling/process management, interprocess communication, and consistency control. Often, OS services are poorly suited for DBMS needs, leading to performance problems or duplication of effort.

> **Intuition:** Operating systems are built as "jack-of-all-trades" managers for general-purpose computing. Databases are highly specialized, high-performance engines. When the database tries to use the OS's general tools, it usually finds them too slow, too dumb, or just wrong for the job.

## 1. Introduction
DBMSs provide higher-level user support than conventional OSs. OSs are designed for different uses. The paper highlights where OS services fail DBMSs, using UNIX and the INGRES relational database system as primary examples.

## 2. Buffer Pool Management
Many OSs provide a main memory cache for the file system (e.g., UNIX). A read returns data from cache or pushes a block to disk to make room.
Problems for DBMS:

### 2.1 Performance
Fetching a block via OS buffer pool incurs system call and memory move overhead (e.g., >5,000 instructions in UNIX). Many DBMSs (INGRES, System R) build their own buffer pool in user space to reduce overhead. OS access overhead must be cut to a few hundred instructions to be viable.

### 2.2 LRU Replacement
OSs typically use LRU (Least Recently Used). DBMS access patterns vary:
1. Sequential access, never rereferenced.
2. Sequential access, cyclically rereferenced.
3. Random access, never rereferenced.
4. Random access, non-zero probability of rereference.
LRU is good only for case 4. For 1 and 3, "toss immediately" is better. For 2, LRU is the worst possible strategy (it tosses the next needed block). A DBMS knows the access pattern and can optimize, but the OS cannot accept "advice" on replacement strategy.

> **Common Confusion:** Why is LRU bad for cyclical sequential access? If your buffer holds 9 pages, but you repeatedly loop over a 10-page table, LRU will evict page 1 right before you need it again, leading to a 100% cache miss rate!

### 2.3 Prefetch
UNIX prefetches on sequential access. However, a DBMS often knows exactly which block it will access next (e.g., by following pointers), which is not necessarily the next logical block. The OS cannot prefetch this correctly.

### 2.4 Crash Recovery
DBMSs provide transaction recovery, often using a write-ahead log or intentions list. The commit flag must be forced to disk *after* all pages in the intentions list. The OS buffer manager lacks a "selected force out" feature to guarantee this ordering.

### 2.5 Summary
DBMSs usually maintain a separate cache in user space, leaving the OS service unused. OS designers should provide prefetch advice, replacement advice, and selected force out.

## 3. The File System
UNIX provides files as dynamically varying character arrays. DBMSs prefer structured files (record management, B-trees). Building structured files on top of character arrays is inefficient:

### 3.1 Physical Contiguity
Character arrays expand block-by-block, scattering blocks over a disk. DBMSs require sequential access and prefer "extent-based" file systems (e.g., VSAM) for physical contiguity and reduced disk arm movement.

> **Tradeoff:** Block-by-block allocation avoids internal fragmentation and simplifies space management for the OS, but it murders sequential read performance for databases because the disk head has to seek wildly.

### 3.2 Tree Structured File Systems
UNIX uses a tree for file blocks (i-nodes) and another for the directory hierarchy. A DBMS adds a third tree (B-tree) for keyed access. Three separate trees incur substantial overhead compared to one unified tree.

### 3.3 Summary
Character arrays are not useful for DBMSs. OSs should consider providing DBMS facilities as lower-level objects and character arrays as higher-level ones.

## 4. Scheduling, Process Management, and Interprocess Communication
Two common multi-user DBMS architectures:
1. **Process-per-user:** Each user runs in a separate OS process, sharing code and data segments (System R).
2. **Server model:** One run-time database process acts as a server, receiving messages from user processes (Enscribe).

### 4.1 Performance (Process-per-user)
Buffer pool misses cause task switches. If the OS has "large" processes, task switching is expensive (>1,000 instructions).

### 4.2 Critical Sections (Process-per-user)
If a process is descheduled while holding a short-term lock on the shared buffer pool, other processes queue up behind it, causing a "convoy" effect that devastates performance.

> **Mental Model:** Imagine a single lane road where the front car (a process) stops to buy a coffee (gets descheduled by the OS). Even though the road ahead is completely empty, 100 cars queue up behind it. This is the convoy effect.

### 4.3 The Server Model
To avoid task switch overhead, the server model uses messages. But the server must do its own scheduling and multitasking (duplicating OS functions) to support concurrent I/O. Without internal multitasking, a single long request blocks others, increasing response time. Using multiple servers or disk processes trades a task switch per I/O for a message per I/O.

### 4.4 Performance of Message Systems
Messages are often very expensive (e.g., ~5,000 instructions in UNIX). This overhead can make viable DBMS organizations too slow.

### 4.5 Summary
OSs should provide a special scheduling class for DBMSs (processes that are never forcibly descheduled but voluntarily relinquish the CPU) and fast-path task switches.

## 5. Consistency Control
OSs provide file locks, but DBMSs need finer granularity (page or record locks). If the OS provides transaction management (concurrency control and crash recovery), it impacts buffer management.

### 5.1 Commit Point
The user-space buffer manager must flush blocks and deliver a commit to the OS, duplicating functions.

### 5.2 Ordering Dependencies
Updates must not depend on the order of execution. If the OS handles crash recovery but the DBMS handles buffering, the DBMS must still maintain its own intentions list to ensure correct update semantics, leading to code duplication.

## 6. Paged Virtual Memory
Binding files into a user's paged virtual address space (so I/O happens via paging) has issues:

### 6.1 Large Files
A 100MB file needs a 100KB page table. If the page table isn't memory resident, I/O causes two page faults (one for the table, one for data). Conventional file control blocks are much more compact (extents) and fit in memory. Binding/unbinding chunks is also slow.

### 6.2 Buffering
The same buffer problems (prefetch, LRU, selected force out) persist in a paged virtual memory context.

## 7. Conclusions
OS services are often too slow or inappropriate for DBMSs. DBMSs implement their own OS-like services in user space. Future OSs should provide the minimal, efficient facilities seen in real-time OSs rather than high-overhead general-purpose features.