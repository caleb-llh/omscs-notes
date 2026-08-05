# Lesson_8_Failures_and_Recovery (Synthesized Notes)

# Module 1: System Recovery and Persistence

## 1. Introduction
- **Context:** System crashes occur due to power failures, hardware issues, or software bugs.
- **Goal:** Build operating systems capable of surviving crashes and recovering effectively.
- **Systems Covered in Module:**
  1. **LRVM (Lightweight Reliable Virtual Memory):** Provides a persistent virtual memory layer to support system services.
  2. **Rio Vista:** Implements a persistent layer in a performance-conscious manner.
  3. **Quicksilver:** Treats recovery as a first-class citizen in OS design.

## 2. Persistence
- **Why Persistence is Needed:**
  - Operating system subsystems (e.g., file systems) require persistent metadata (like inodes) to track data storage.
  - Runtime systems for various programming languages require persistent objects.
  - Subsystems cache persistent data in memory for performance, but changes must eventually be committed back to permanent storage to maintain consistency.
- **Persistent Virtual Memory:**
  - **Idea:** Make virtual memory persistent. Any data structure in virtual memory automatically becomes persistent, relieving subsystems from manual disk flushing.
  - **Advantage:** Crash recovery becomes straightforward because the data structures are inherently persistent.
- **The Performance Challenge:**
  - Modifying persistent data structures scattered across the virtual address space leads to **random I/O operations** on the disk.
  - Random writes incur significant seek and rotational latencies, degrading performance.
- **Solution - Log Segment:**
  - Similar to the Log-Structured File System (LFS).
  - **Mechanism:** Instead of updating the disk randomly, changes to persistent data structures are recorded sequentially in a **Log Segment**.
  - **Benefit:** Converts random writes into sequential writes, dramatically reducing I/O operations and avoiding latencies.

## 3. Server Design with LRVM
- **Selective Persistence:** The entire virtual address space does not need to be persistent. The developer decides which specific data structures require persistence (e.g., file system inodes).
- **External Data Segments:**
  - Collections of data structures that must be persistent on disk.
  - An application can map multiple external data segments to different, non-overlapping portions of its virtual address space.
  - **Mapping:** Usually performed at startup. A one-to-one mapping exists between a virtual memory address range and an external data segment.
  - **Unmapping:** Can occur when no commits are pending.

## 4. LRVM Primitives
LRVM is provided as a runtime library (not inside the OS kernel) with simple, flexible primitives:

### Initialization and Mapping
- `initialize`: Declares the log segment data structure the server process will use to record changes.
- `map`: Maps a specific region of the virtual address space to an external data segment.
- `unmap`: Decouples the virtual address range from its external data segment.

### Transaction Management
- **Transactions in LRVM:** Lightweight and restricted for recovery management. They do not support full ACID properties (e.g., no nested transactions, no concurrency control). They act like critical sections.
- `begin_transaction`: Alerts the LRVM runtime that changes to persistent data are about to start.
- `set_range`: Called immediately after `begin_transaction`. Specifies the starting address and block size of the memory that will be modified.
- `end_transaction`: Commits the transaction. Signals that changes should be persisted.
- `abort_transaction`: Aborts the transaction. Discards all changes made since `begin_transaction`.

### Explicit Control (Optional)
- `flush`: Explicitly forces the log segment to disk.
- `truncate`: Explicitly applies redo logs to the external data segments and frees log space.

## 5. How the Server Uses the Primitives
1. **Initialization:** Map address space and declare the log segment.
2. **Execution (Critical Section):**
   - Call `begin_transaction`.
   - Call `set_range` to define the modification bounds.
   - Modify the in-memory data structures (must fall within the defined range).
   - Call `end_transaction` to commit, or `abort_transaction` to revert.

### Under the Hood: Undo and Redo Records
- **Undo Record (In-Memory):**
  - Created upon `set_range`.
  - A copy of the original state of the defined memory block.
  - **Purpose:** Used to restore memory if `abort_transaction` is called. Discarded if the transaction commits.
- **Redo Record (In-Memory -> Disk):**
  - Created upon `end_transaction`.
  - Contains the start address, length, and the new data.
  - Written to the in-memory log segment and then synchronously flushed to disk.

## 6. Transaction Optimizations
To enhance performance, LRVM provides optimization modes:
- `no_restore` **(in `begin_transaction`):**
  - Developer asserts the transaction will never abort.
  - LRVM skips creating the in-memory Undo Record, saving memory and copy overhead.
- `no_flush` **(in `end_transaction`):**
  - Developer permits lazy persistence.
  - LRVM commits the transaction in memory but does not synchronously block to flush the redo log to disk.
  - **Trade-off:** Creates a "window of vulnerability." If the system crashes before the background flush completes, recent committed changes are lost.

## 7. Implementation Details
- **No-Undo / Redo Value Logging:**
  - **No-Undo on disk:** Undo logs are kept strictly in-memory and discarded after the transaction.
  - **Redo on disk:** Only the new values of committed transactions are written to the persistent log segment.
- **Log Structure:**
  - Redo logs contain forward and reverse displacements.
  - Forward displacements aid in appending new logs.
  - Reverse displacements facilitate backward traversal during crash recovery.

## 8. Crash Recovery
- **Trigger:** System resumes after a crash.
- **Process:**
  1. Read the redo log starting from the tail (using reverse displacements).
  2. Apply the recorded changes (new data) to their respective external data segments.
  3. Discard the applied redo logs.

## 9. Log Truncation
- **Problem:** As the system runs, redo logs accumulate, consuming disk space and slowing down data segment mapping.
- **Solution:** Truncate the log periodically by applying the redo logs to the external data segments (similar to the crash recovery process).
- **Parallel Processing:**
  - LRVM splits the log into **epochs** to avoid halting the system.
  - **Truncation Epoch:** The older portion of the log being applied to external segments by the runtime.
  - **Current Epoch:** The active portion where the application continues to write new logs.
- Log truncation is the most complex component of LRVM due to the heavy coordination required between background truncation and active forward processing.

## 10. Conclusion
- **Pain Point:** Managing persistence for critical data structures.
- **Solution:** LRVM uses lightweight transactions (without full ACID overhead) to provide persistent semantics.
- **Result:** Enables developers to build robust, crash-tolerant subsystems with a simple, high-performance API.

---

# Playlist 3 Module 2: Rio Vista & Lightweight Recoverable Virtual Memory (LRVM)

## Introduction
- **Lightweight Recoverable Virtual Memory (LRVM):** Designed to alleviate system crashes (from software errors or power failures) as a pain point for system developers.
- **Transactional Semantics:** Provides transactional semantics for persistent data structures.
  - Called "lightweight" because it eliminates traditional heavyweight ACID properties.
  - Specifically used for **recovery management**.
- **How LRVM works:** Changes to virtual memory are written as redo logs at the end of a transaction.
  - Logs are forced to disk as commit records of changes made to virtual memory.
  - **Synchronous I/O:** The log force at the commit point is synchronous; applications must wait for I/O completion before proceeding.
- **The Performance Problem:** A precise implementation requires at least one synchronous disk I/O, which incurs a time penalty. Systems often avoid transactions because of this penalty.
- **Rio Vista:** A performance-conscious design starting where LRVM left off, addressing the question: *How can we eliminate synchronous disk I/O?*

## System Crash
- **Sources of System Crashes:** 
  1. Power failure
  2. Software failure (application bugs or crashes)
- **Rio Vista's Postulate:** What if we assume that the *only* source of system crashes is software failure (bugs) and not power failure? How would this change failure recovery?
- **Hardware Solution for Power Failure:** Throw hardware at the problem by using a UPS (Uninterruptible Power Supply).
  - **Battery-Backed DRAM:** Connect the UPS to a portion of main memory, making it persistent to power failures. Changes recorded here survive power loss.
- **Impact:** Eliminating power failure allows designers to focus solely on recovering from software crashes, potentially making LRVM transactions cheap and encouraging their widespread use.

## LRVM Revisited (Semantics and Mechanism)
- **Begin Transaction:** LRVM creates an in-memory **undo record** (a copy of the old contents of the memory that the transaction will modify).
- **Transaction Body:** Normal program writes occur in memory. There is no interaction with LRVM here because the undo record is already stashed away.
- **End Transaction (Commit):** 
  - LRVM writes a **redo record** to disk reflecting virtual memory changes.
  - **No-Flush Option:** An optimization where the application tells LRVM to write to disk in the background without blocking progress.
    - Creates a *window of vulnerability* to power failures in favor of performance (a calculated risk).
  - **Conservative Approach:** Normal transactional semantics where the application waits for the log to be forced to disk before proceeding.
- **Post-Commit Actions:** 
  - The undo record is discarded since the transaction successfully committed.
  - **Log Truncation/Cleanup:** As a background activity, LRVM applies the redo logs to the original data segments on disk and cleans up the redo logs space.
- **Vulnerability:** Despite optimizations, power failure remains the biggest vulnerability, as deferred unwritten logs are lost during a crash.

## Rio File Cache
- **Persistent File Cache:** A file cache backed by a UPS.
  - Survives power failures.
  - **VM Protection:** Built into the OS to prevent wild writes to the file cache during software crashes or power failures.
- **Usage Modes:**
  1. **File Writes:** Normal file writes go to the battery-backed file cache and become persistent immediately. No need for `fsync` calls.
  2. **Memory-Mapped Files (`mmap`):** Normal program writes to memory-mapped files become persistent automatically because they are backed by the persistent file cache. No need for `msync` calls.
- **Benefits:**
  - No synchronous writes to disk are needed.
  - Write-backs to disk can be arbitrarily delayed.
  - Short-lived files (e.g., temporary compilation files) can be created and deleted in the file cache without ever being written to disk.

## Vista RVM on Top of Rio
- **Vista:** An RVM library implemented on top of the Rio persistent file cache.
- **Semantics:** Exactly the same as LRVM, but optimized by leveraging the Rio file cache.
- **Mechanism:**
  - **Mapping:** External data segments are mapped to virtual memory within the persistent file cache.
  - **Begin Transaction:** Vista creates a *before image* (undo log) of the address range to be modified (specified by `set range`). This undo log is also mapped to the file cache, making it persistent.
  - **Transaction Body:** Normal program writes directly modify the data segment in the persistent file cache. Changes are automatically persistent.
  - **End Transaction (Commit):** 
    - Changes are already committed by design (via memory mapping in the persistent cache).
    - No synchronous disk I/O or redo log creation is required.
    - Vista simply discards the undo log.
  - **Transaction Abort:** Vista restores the *before image* (undo log) back into the modified virtual memory and then discards the undo log. This also corrects the data segment automatically.
- **Key Difference from LRVM:** LRVM requires heavy lifting at the commit point (forcing redo logs to disk). Vista does no work at commit other than discarding the undo log.

## Crash Recovery
- **Procedure:** Treated exactly like a transaction abort. 
- **Undo Log:** Survives crashes because it's located in the Rio file cache.
- **Process:** On recovery, Vista applies the persistent undo log to the corresponding virtual address space.
- **Idempotence:** Crash recovery is idempotent; a crash occurring *during* recovery poses no problems.

## Vista Simplicity and Performance
- **Codebase Size:** Vista is extremely simple (~700 lines of code) compared to the original LRVM (>10,000 lines).
- **Simplifications:**
  - No redo logs.
  - No log truncation code.
  - Simplified checkpointing and recovery code.
  - No group commit optimizations.
- **Performance:** Vista performs three orders of magnitude better than the original LRVM.
  - The biggest performance improvement comes from completely eliminating disk I/O.

## Conclusion
- **Thought Experiment:** Rio Vista demonstrates how changing a fundamental starting assumption (that crashes are caused by software, not power failures) can lead to a completely different and highly optimized system design.

## Cleaning up State Orphan Processes
*(Note: This section preserves the raw, unstructured transcript data due to transcription errors in the source material.)*
- The principle inserted, so talk about age in the back of the knee film, coma, car mgs, an open door hole, orders from what are tools help out, look into real, difficult, we took 3 ews, and if the won soon, dries, electro users use tool, we operate the sol, we a meter, just as is, Ming Chiu, low interest on lovin, and os we r o u o pow d, sir, Lee, Lee, curve, 2nd st, Peters, crs, ID, BIOS, use, pl, opera, head, low, srw, ssing, wild to fix, work, ending is op, ppa, there, like that, wore, new, why, point is, 2 web, class, sublimated, meet, 2, Murloc, October, soft, from ws, coupler, x, per, iteration, owen, n, in, drake, nfl, sleeve, tool in, mi, cursor, x, serial, male, others, work, old age, jumping, power, we, novel, love to feel, no, secretly, shawl, increase, in order to lead to, Northern, flanders, wmf, multichannel, on, which, teacher, service, 3, fin, the program is, clinton, taste to let me, roll, a n You synced painfully a or c it use lous enter a man whose io in ID monthly br ha in one go qat OK received spirit

---

# Module 3: Recovery as a First-Class Citizen (Quicksilver)

## 1. Introduction
- **The Core Question**: Should recovery be a first-class citizen in operating system design rather than an afterthought?
- **Context**: Systems like LRVM and Rio Vista were built to fix problems that manifested because OSes were not handling recovery well.
- **Performance vs. Reliability**: Conventional wisdom suggests that performance and reliability (robustness/recoverability) are opposing concerns—you can have one or the other, but not both.
- **Quicksilver's Approach**: If recovery is taken seriously from the get-go, a system can be designed to be robust against failures without losing much performance.

## 2. Quicksilver Overview
- **Origin**: Developed by **IBM** starting in **1984** (early 80s). First paper published in 1988.
- **Motivation**: Designed to address everyday computing issues like orphan windows, memory leaks, and other state left behind by failed processes. Conceived during the transition from CRT terminals connected to mainframes to office workstations (desktops).
- **Precursor**: A precursor to Quicksilver at IBM was called **925** (a pun on "9 to 5" office workstations).
- **Historical Context**: Quicksilver's ideas predated or were concurrent with Network File System (NFS), Remote Procedure Call (RPC), the Internet, and the World Wide Web.
- **Key Innovation**: The first operating system to propose **transactions** as a unifying concept for recovery management of servers, rather than using ad-hoc mechanisms for each server to recover from failures.

## 3. Distributed System Structure
- **Typical Structure**: 
  - **Applications**: What users interact with.
  - **System Services**: File server, web server, window manager, database manager, network stack.
  - **Microkernel**: Sits at the bottom.
- **Microkernel Responsibilities**: Process management, hardware resource management, and Inter-Process Communication (IPC)—both intra-machine (among services) and inter-machine (via network stack).
- **Advantages**: This structure (seen in Quicksilver, similar to Mach from CMU) lends itself to extensibility while maintaining high performance.

## 4. Quicksilver System Architecture
- **Microkernel-Based Design**: Quicksilver uses a microkernel responsible only for Process Management, IPC, and machine control.
- **System Services as Servers**: All services (window manager, file system, virtual memory, communication) sit above the microkernel and are implemented as server processes.
- **Integration of Communication**: Integrating communication into the OS design was key, as services might not be available locally (e.g., remote file servers).
- **Transaction Manager**: Provided as part of the operating system services, handling recovery management for services both within a workstation and across workstations in a distributed system.

## 5. Inter-Process Communication (IPC)
- **Role of IPC**: Crucial to Quicksilver since it is a distributed OS where services are provided by server processes.
- **Service Queue (Service Q)**: A global data structure created by a server to handle client requests. Similar to a UNIX socket. Any process in the network can connect and make requests, and any server process can service them.
- **Synchronous Client Call**: Client makes a request -> Kernel makes an upcall to the server -> Server executes and puts completion in Service Queue -> Kernel delivers response to client. Client waits during this process.
- **Asynchronous Client Call**: Client makes a request and continues execution without blocking. When ready, the client does a `wait` on the Service Queue to receive the response.
- **IPC Guarantees**:
  - **Exactly Once**: No loss or duplication of requests.
  - **Reliable Data Transfer**: Handles remote machine communication safely.
  - **Location Transparency**: Clients do not need to know where in the network a request is serviced.
- **Server Offers**: Servers wait on a Service Queue by making an `offer` call. Multiple servers can offer their services, and the kernel dispatches requests based on server busyness.
- **Interchangeable Roles**: A server can act as a client (e.g., a file system server acting as a client to a directory server and data server).
- **Relation to RPC**: Quicksilver IPC semantics are very similar to Remote Procedure Call (RPC), which was invented around the same time.

## 6. Bundling IPC and Transactions (Recovery Management)
- **The Secret Sauce**: The lightweight notion of a **transaction** (similar to what LRVM later used, though Quicksilver predates it). Purely for recovery management, so semantics are simple and there is no need for concurrency control.
- **Piggybacking**: Recovery mechanism (transactions) rides on top of IPC, essentially bundling recovery with communication to get it cheaply without extra network overhead.
- **Transaction ID**: IPC calls are automatically tagged with a transaction ID under the covers. Clients and servers don't need to do anything special and can ignore it if they don't need recovery.
- **Transaction Link**: When a client on Node A calls a server on Node B, the Communication Managers interact. Under the covers, the Transaction Manager (TM) on Node A contacts the TM on Node B to establish a transaction link, creating an audit trail.

## 7. Distributed Transaction Trees
- **Transaction Tree Creation**: A chain of client-server interactions leads to a transaction tree that spans multiple nodes/sites.
- **Nodes in the Tree**:
  - **Owner / Coordinator**: The creator of the transaction (where the interaction originates) is the default owner and root of the tree.
  - **Participants**: Other nodes involved in the IPC chain that agree to participate in the transaction.
- **Delegation of Ownership**: Since client nodes are often the most fragile ("fickle-minded"), the root/owner can delegate ownership and coordinator status to a more robust node (e.g., a file server) to ensure breadcrumbs are cleaned up if the client crashes.
- **Multi-Site Atomicity**: Recoverability must ensure that all "breadcrumbs" (state created, files opened, windows drawn) left across multiple sites are cleaned up when a transaction terminates.
- **Reduced Network Communication**: The graph structure allows participant TMs to report only to the node that contacted them (their parent in the tree), rather than everyone reporting to the global coordinator.

## 8. Commit and Abort Protocols
- **Initiation**: The coordinator initiates the termination of a transaction (either a commit or an abort) once the client-server interaction is complete (e.g., closing a file).
- **Communication Flow**: The coordinator sends commit/abort/vote requests down the tree to subordinates, who pass them down and send responses back up.
- **Failure Handling**: If a node fails or a connection breaks, the transaction is not aborted immediately. Error reporting continues, and the transaction is aborted only upon termination requested by the coordinator, ensuring all partial states are cleaned up properly.
- **Tailored Commit Protocols**: Different services require different commit protocols based on the criticality of their state:
  - **Window Manager**: Deals with volatile state (a window on screen) and may only need a simple **one-phase commit protocol** (internal cleanup).
  - **File System**: Deals with persistent data structures and may need sophisticated **two-phase commit protocols**.
- **Service Autonomy**: The OS provides mechanisms and policies, but it is entirely up to each service to choose whether to use them or ignore them.

## 9. State and Log Management (Implementation Notes)
- **Breadcrumbs/State Left Behind**: Memory allocated but not freed, file handles, communication handles, orphan windows. The transaction tree ensures these can be cleanly collected.
- **Log Maintenance**:
  - TMs write log records to recover persistent state.
  - Logs are initially kept in memory (in-memory log segments).
  - **Log Force**: TMs periodically flush in-memory logs to persistent storage. This is a synchronous I/O operation and impacts performance.
- **Vulnerability vs. Performance Trade-off**:
  - Writing logs immediately upon every state change ensures perfect recovery but incurs high I/O costs.
  - Delaying log writes improves performance but creates a window of vulnerability where a crash could lose state.
- **Shared Log Issue**: In Quicksilver, a TM maintains a single log for *all* processes running on its node. If one application forces a log flush, it impacts the performance of all other clients on that node. Thus, services must carefully choose their recovery mechanisms.

## 10. Conclusion and Legacy
- **Enduring Concepts**: Quicksilver's idea of using transactions as a fundamental OS mechanism to bundle state recovery stood the test of time.
- **Resurgence**: 
  - In the 1990s: For providing persistence (e.g., LRVM).
  - In the 2010s: For system security and safeguarding against malicious attacks (e.g., TxOS).
- **Commercial Reality vs. Research**: Commercial OSes typically prioritize performance over reliability (e.g., delaying disk writes for performance, risking data loss on crash).
- **Future Outlook**: New technologies like Storage Class Memories (SCM), which offer DRAM-like latency but are non-volatile, may lead to a resurgence of exploring transactions in operating systems.


---

