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
