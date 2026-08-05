import re

file_path = "/Users/bytedance/Documents/repos/github/omscs-notes/aos/trae-notes/Lesson_8_Failures_and_Recovery/Lesson_8_Failures_and_Recovery.md"

with open(file_path, "r") as f:
    lines = f.readlines()

insertions = [
    (
        "- **Goal:** Build operating systems capable of surviving crashes and recovering effectively.",
        "> **Background Context:** Historically, OS crashes resulted in catastrophic data loss. Early systems required meticulous manual recovery procedures, which spurred the research into automated recovery mechanisms discussed in this module."
    ),
    (
        "  - Operating system subsystems (e.g., file systems) require persistent metadata (like inodes) to track data storage.",
        "  > **Conceptual Framework:** The dichotomy between volatile memory (RAM) and non-volatile storage (Disk) dictates system design. Persistence mechanisms bridge this gap, ensuring that state transitions in volatile memory are safely mirrored to non-volatile storage before a crash can obliterate them."
    ),
    (
        "  - Random writes incur significant seek and rotational latencies, degrading performance.",
        "  > **Background Context:** Traditional hard disk drives (HDDs) have physical read/write heads that must move to the correct platter track (seek time) and wait for the sector to spin under the head (rotational latency). Random I/O forces these physical movements repeatedly, destroying throughput."
    ),
    (
        "- **Selective Persistence:** The entire virtual address space does not need to be persistent. The developer decides which specific data structures require persistence (e.g., file system inodes).",
        "> **Conceptual Framework:** Not all data is created equal. Selective persistence relies on the programmer's domain knowledge to distinguish between ephemeral state (e.g., loop counters) and critical state (e.g., file metadata), optimizing overhead by only persisting what matters."
    ),
    (
        "- `truncate`: Explicitly applies redo logs to the external data segments and frees log space.",
        "> **Example:** A database server might use `flush` right after committing a high-value financial transaction to guarantee it is on disk, while using lazy persistence for less critical logging activities."
    ),
    (
        "   - Call `end_transaction` to commit, or `abort_transaction` to revert.",
        "   > **Conceptual Framework:** The `begin_transaction` and `end_transaction` block acts as a temporal boundary. Within this boundary, memory modifications are staged. The commit operation atomically transitions these staged modifications into durable state."
    ),
    (
        "  - Contains the start address, length, and the new data.",
        "  > **Background Context:** The Undo/Redo paradigm is foundational in database systems. LRVM adapts this by keeping Undo records strictly in memory (for fast aborts) and using Redo records to guarantee durability (written to disk)."
    ),
    (
        "  - LRVM skips creating the in-memory Undo Record, saving memory and copy overhead.",
        "  > **Hypothetical:** If a developer uses `no_restore` but the transaction actually encounters an error and needs to abort, the application is left in an undefined state because LRVM discarded the original memory state. This shifts the burden of correctness entirely onto the application logic."
    ),
    (
        "  - Reverse displacements facilitate backward traversal during crash recovery.",
        "  > **Conceptual Framework:** The use of forward and reverse displacements essentially turns the log into a doubly-linked list on disk. This bidirectional navigability is crucial because normal execution writes forward, while crash recovery often requires reading backward from the most recent state."
    ),
    (
        "  3. Discard the applied redo logs.",
        "  > **Example:** If a crash happens while writing a Redo log, the log might be truncated or corrupted. The recovery process uses the reverse displacements to find the last valid, complete transaction record, ensuring partial writes are ignored."
    ),
    (
        "  - **Current Epoch:** The active portion where the application continues to write new logs.",
        "  > **Conceptual Framework:** Log truncation is essentially a garbage collection process for the disk. By dividing the log into epochs, LRVM achieves concurrent garbage collection—cleaning up old records while actively appending new ones, preventing system stalls."
    ),
    (
        "- **Result:** Enables developers to build robust, crash-tolerant subsystems with a simple, high-performance API.",
        "> **Background Context:** LRVM proved that you don't need a heavy relational database to get safe crash recovery. A lightweight, memory-centric approach could serve the needs of most OS subsystems and runtime environments perfectly."
    ),
    (
        "- **The Performance Problem:** A precise implementation requires at least one synchronous disk I/O, which incurs a time penalty. Systems often avoid transactions because of this penalty.",
        "> **Background Context:** A synchronous disk I/O typically takes milliseconds, whereas a RAM write takes nanoseconds. Waiting for the disk at every commit point slows the application down by a factor of roughly a million."
    ),
    (
        "  - **Battery-Backed DRAM:** Connect the UPS to a portion of main memory, making it persistent to power failures. Changes recorded here survive power loss.",
        "  > **Conceptual Framework:** This represents a paradigm shift from software-based fault tolerance (logging) to hardware-based fault tolerance (battery-backed RAM). It converts a complex software algorithm problem into a hardware provisioning solution."
    ),
    (
        "  - **Log Truncation/Cleanup:** As a background activity, LRVM applies the redo logs to the original data segments on disk and cleans up the redo logs space.",
        "  > **Example:** Think of Log Truncation as taking all the chronological receipts from your daily purchases (redo logs) and updating your master ledger (external data segment). Once the ledger is updated, you can safely throw away the individual receipts to save space."
    ),
    (
        "  - **VM Protection:** Built into the OS to prevent wild writes to the file cache during software crashes or power failures.",
        "  > **Background Context:** Since battery-backed RAM survives reboots, a rogue pointer during a software crash could overwrite critical persistent data. VM protection uses hardware page tables to make the persistent cache read-only during normal operation, unprotecting it only during explicit write operations."
    ),
    (
        "  - **Transaction Abort:** Vista restores the *before image* (undo log) back into the modified virtual memory and then discards the undo log. This also corrects the data segment automatically.",
        "  > **Hypothetical:** If a transaction aborts, Vista simply copies the before image back over the modified memory. Because both the before image and the modified memory reside in the persistent cache, even if power fails *during* the abort process, the system can simply restart the abort upon reboot."
    ),
    (
        "- **Process:** On recovery, Vista applies the persistent undo log to the corresponding virtual address space.",
        "> **Conceptual Framework:** Idempotence means an operation can be applied multiple times without changing the result beyond the initial application. In recovery, this is crucial: if the machine crashes while recovering, restarting the recovery process from the beginning is perfectly safe."
    ),
    (
        "  - Simplified checkpointing and recovery code.",
        "  > **Background Context:** The massive reduction in codebase size from 10,000 lines to 700 lines not only improves performance but vastly reduces the surface area for bugs in the recovery system itself."
    ),
    (
        "- **The Core Question**: Should recovery be a first-class citizen in operating system design rather than an afterthought?",
        "> **Background Context:** In the 1980s, the shift to distributed workstations meant that a single user's task might involve half a dozen different machines (file server, print server, name server). A crash in any one of them could leave the entire distributed state in limbo."
    ),
    (
        "- **Motivation**: Designed to address everyday computing issues like orphan windows, memory leaks, and other state left behind by failed processes. Conceived during the transition from CRT terminals connected to mainframes to office workstations (desktops).",
        "> **Example:** An orphan window occurs when the application that created the window crashes, but the window manager doesn't know, leaving an unresponsive, unkillable window on the user's screen."
    ),
    (
        "- **Microkernel Responsibilities**: Process management, hardware resource management, and Inter-Process Communication (IPC)—both intra-machine (among services) and inter-machine (via network stack).",
        "> **Conceptual Framework:** By moving services out of the kernel and into user space, a crash in a system service (like the file system) only crashes that specific process, not the entire operating system kernel. This architecture inherently demands robust IPC."
    ),
    (
        "- **System Services as Servers**: All services (window manager, file system, virtual memory, communication) sit above the microkernel and are implemented as server processes.",
        "> **Hypothetical:** If every service implemented its own recovery, a distributed file read would require the file server's recovery protocol to somehow talk to the network manager's recovery protocol. Quicksilver centralizes this so they all speak the same language."
    ),
    (
        "  - **Exactly Once**: No loss or duplication of requests.",
        "  > **Background Context:** \"Exactly Once\" semantics in a distributed system are notoriously difficult to achieve due to network unreliability. Quicksilver's IPC layer handles the complex retries, timeouts, and deduplication so the application doesn't have to."
    ),
    (
        "- **Transaction Link**: When a client on Node A calls a server on Node B, the Communication Managers interact. Under the covers, the Transaction Manager (TM) on Node A contacts the TM on Node B to establish a transaction link, creating an audit trail.",
        "> **Conceptual Framework:** The Transaction Link weaves an invisible thread through the distributed system. Every time IPC crosses a process or machine boundary, the thread follows, creating a complete topological map of all nodes involved in the operation."
    ),
    (
        "- **Delegation of Ownership**: Since client nodes are often the most fragile (\"fickle-minded\"), the root/owner can delegate ownership and coordinator status to a more robust node (e.g., a file server) to ensure breadcrumbs are cleaned up if the client crashes.",
        "> **Example:** A thin client (like a simple terminal) asks a robust database server to perform a complex, multi-node query. The thin client might delegate transaction ownership to the database server because the database server is much less likely to crash or disconnect during the operation."
    ),
    (
        "- **Failure Handling**: If a node fails or a connection breaks, the transaction is not aborted immediately. Error reporting continues, and the transaction is aborted only upon termination requested by the coordinator, ensuring all partial states are cleaned up properly.",
        "> **Hypothetical:** If node C disconnects from the transaction tree, the coordinator doesn't instantly panic and abort everything. Node C might just be experiencing a transient network hiccup and could reconnect in time for the final commit phase."
    ),
    (
        "  - **Log Force**: TMs periodically flush in-memory logs to persistent storage. This is a synchronous I/O operation and impacts performance.",
        "  > **Conceptual Framework:** The tension between latency (waiting for logs to flush) and durability (ensuring state survives a crash) is the central dilemma of transactional systems. Quicksilver exposes this tradeoff, allowing developers to choose the right balance for their specific service."
    ),
    (
        "- **Future Outlook**: New technologies like Storage Class Memories (SCM), which offer DRAM-like latency but are non-volatile, may lead to a resurgence of exploring transactions in operating systems.",
        "> **Background Context:** Storage Class Memories (like Intel Optane) blur the line between RAM and Disk, offering persistence at memory bus speeds. This hardware evolution validates Quicksilver's and Rio Vista's assumptions, making OS-level transaction management highly relevant again."
    )
]

new_lines = []
for line in lines:
    new_lines.append(line)
    stripped = line.strip()
    for target, insertion in insertions:
        if target.strip() == stripped:
            # Check indentation of the target line
            indent = line[:len(line) - len(line.lstrip())]
            new_lines.append(indent + insertion + "\n")
            # Avoid inserting multiple times if there are duplicate lines
            insertions.remove((target, insertion))
            break

with open(file_path, "w") as f:
    f.writelines(new_lines)
