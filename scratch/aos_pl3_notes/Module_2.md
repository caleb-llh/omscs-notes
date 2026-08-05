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