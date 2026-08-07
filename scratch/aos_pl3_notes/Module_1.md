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