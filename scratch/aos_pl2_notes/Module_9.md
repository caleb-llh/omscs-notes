# Module 9: Distributed File Systems and xFS

## 1. Stripe Groups
Subsetting storage servers into **stripe groups** for striping log segments avoids the "small write pitfall" and provides several key benefits:
* **Parallel Client Activities**: 
  * Different log segments are assigned to different clients.
  * Allows client activities corresponding to different stripe groups to occur in parallel.
  * Increases server availability because different subsets of servers handle different client requests, resulting in higher overall throughput.
* **Efficient Log Cleaning**:
  * Different cleaning servers can be assigned to different stripe groups, increasing parallelism in distributed file system (DFS) management.
  * Essential because logs must be cleaned periodically as new writes overwrite old files.
* **Increased Availability & Fault Tolerance**:
  * The system can survive multiple server failures. If disks in one stripe group fail, clients served by other stripe groups remain unaffected.
  * Allows incremental satisfaction of the user community despite partial system failures.

## 2. Cooperative Caching
xFS utilizes client memories to cooperatively cache files, reducing the load on the storage servers and minimizing disk access.
* **Cache Coherence**: 
  * Unlike traditional Unix file systems (which serve clients independently without worrying about sharing), xFS strictly maintains cache coherence.
  * **Semantics**: Single Writer, Multiple Readers (a file can have multiple concurrent readers but only one writer at any time).
  * **Granularity**: Coherence is maintained at the **file block level**, not the entire file.
* **Write Protocol & Conflict Resolution**:
  1. The metadata manager tracks which client caches hold specific file blocks.
  2. If a client wants to write to a block that is currently being read by others (read-write conflict), the manager sends **invalidation messages** to the current holders.
  3. Clients acknowledge the invalidation, discarding their local copies.
  4. The manager grants a **write token** to the requesting client.
  5. The manager can revoke this token if a future read or write request occurs.
* **Cooperative Caching Mechanism**:
  * When a read request arrives, the manager can redirect the request to a peer client that already holds the file block in its cache, satisfying the read via network transfer rather than disk access.

## 3. Log Cleaning
As clients continuously write and overwrite data, old blocks in log segments become stale (creating "holes"), necessitating log cleaning to reclaim disk space.
* **The Cleaning Process**:
  1. Identify the utilization status of old log segments.
  2. Select a set of segments to clean.
  3. Read and aggregate all **live (valid) blocks** from these segments into a new, contiguous log segment.
  4. Garbage collect (delete) the old, fragmented log segments.
* **Distributed Log Cleaning in xFS**:
  * **Client Responsibility**: Clients (mutators) track segment utilization for the files they write and handle log cleaning concurrently with normal file operations. Any node can act as a client or server.
  * **Stripe Group Leader**: Each stripe group has a leader that assigns cleaning tasks to the members of its group.
  * **Conflict Resolution**: The metadata manager resolves conflicts between client updates (modifying segments) and cleanup functions (garbage collecting segments).

## 4. xFS Data Structures
To implement a truly distributed file system where the metadata manager may not reside on the same node as the file or client, xFS uses several specialized data structures. (Note: Traditional Unix uses inodes mapping filenames to disk blocks).
* **Manager Map**: A globally replicated data structure at every node that maps a filename to its designated metadata manager node.
* **File Directory**: Used by the manager to map a filename to an Index Number (I-number).
* **I-Map**: Maps the I-number to the inode address for the log segment associated with the file.
* **Stripe Group Map**: Maps the log segment ID to the specific stripe group (storage servers) that holds the actual data blocks.

## 5. File Access Paths
### Reading a File
xFS uses caching extensively to avoid the expensive worst-case path for file reads:
1. **Path 1: Local Cache (Fastest)**
   * Client looks up the directory to get the index and offset.
   * Finds the data block in its own local UNIX file cache. No network hops required.
2. **Path 2: Cooperative Caching (Second Best)**
   * Not in local cache. Client consults the **Manager Map** and contacts the Manager Node.
   * Manager's metadata indicates another client has the block cached.
   * Manager requests the peer client to send the data directly to the requester.
   * Faster than disk access because network speeds exceed disk speeds (involves up to 3 network hops).
3. **Path 3: The Long Way (Disk Access - Worst Case)**
   * Not in any cache. Client contacts the Manager.
   * Manager traverses the **File Directory** $\rightarrow$ **I-Map** $\rightarrow$ **Stripe Group Map** to locate the log segment inode.
   * Manager contacts the storage server for the inode, then the storage server for the data blocks.
   * *Optimization*: If the manager recently accessed the inode, it may be cached locally, saving network hops to the storage server.

### Writing a File
* The client aggregates writes into a log segment in its local memory.
* When flushing to disk, the client determines the appropriate stripe group and stripes the log segment across those storage servers.
* The client then notifies the metadata manager about the flushed log segments to keep the global state consistent.

## 6. Key Technical Innovations of xFS
xFS serves as a research prototype demonstrating advanced DFS concepts (alongside others like Andrew File System (AFS) and Coda):
1. **Log-Based Striping**: Subsetting storage servers into stripe groups to improve parallelism and fault tolerance.
2. **Cooperative Caching**: Combining distributed client memory with dynamic metadata management for faster file access.
3. **Distributed Log Cleaning**: Offloading garbage collection responsibilities to clients and distributing the workload across stripe groups rather than relying on a centralized manager.

## 7. Conclusion
* Network file systems (like NFS from NetApp) are ubiquitous in computing environments.
* xFS pushes beyond traditional NFS by prioritizing **scalability**—achieved by removing centralization and intelligently utilizing available memory across nodes in a local area network.
* These techniques for identifying and removing bottlenecks are highly reusable concepts for designing other scalable distributed subsystems.