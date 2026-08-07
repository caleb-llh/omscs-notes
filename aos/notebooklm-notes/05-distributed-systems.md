# Lesson 5: Distributed Systems 

## Part 1: Foundations and Event Ordering

### 1. Definition and Properties of Distributed Systems
A distributed system is defined as a collection of autonomous nodes interconnected by a communication network. 

#### 1.1 Architectural Infrastructure
*   **Networking Media:** Nodes may be connected via Local Area Networks (LAN) or Wide Area Networks (WAN). LAN implementations typically utilize twisted pair, coaxial cable, or optical fiber. WAN implementations may utilize satellite communication or microwave links.
*   **Access Protocols:** Communication is governed by media access protocols such as ATM or Ethernet.
*   **Memory Architecture:** A defining characteristic is the **lack of shared physical memory**. Nodes have their own private memory; consequently, the only mechanism for inter-node communication is message passing.

#### 1.2 Temporal Characteristics
The classification of a system as "distributed" depends on the relationship between two specific time metrics:
1.  **Event Computation Time ($T_e$):** The time required for a single node to perform meaningful local processing.
2.  **Communication/Messaging Time ($T_m$):** The time required for a message to traverse the network between nodes.

**Lamport’s Definition:** A system is distributed if the message transmission time ($T_m$) is **not negligible** compared to the time between events ($T_e$) in a single process. Under this definition, even a **cluster** within a single data center rack is considered a distributed system because modern processors have shrunk $T_e$ to the point that $T_m$ is significantly larger by comparison.

#### 1.3 Design Implications
Because $T_m \gg T_e$, distributed algorithms must be structured so that computation time significantly outweighs communication time to realize the benefits of parallelism.

---

### 2. The "Happened-Before" Relationship
The "Happened-Before" relationship (denoted as $a \rightarrow b$) is the fundamental ordering mechanism for events in a distributed system.

#### 2.1 Core Beliefs of Event Ordering
1.  **Sequential Processes:** Events within a single process are totally ordered. If event $a$ textually precedes event $b$ in the same process, then $a \rightarrow b$.
2.  **Causality of Communication:** A message cannot be received before it is sent. If $a$ is the sending of a message and $b$ is the receipt of that same message, then $a \rightarrow b$.
3.  **Transitivity:** If $a \rightarrow b$ and $b \rightarrow c$, then $a \rightarrow c$.

#### 2.2 Functional Example: Airline Reservation
Using an Expedia-Delta reservation as a model:
*   **Direct Relationships:** The user sending a request to Expedia ($a$) happens before Expedia receives it ($b$). Expedia's receipt of the message ($b$) happens before it sends a booking request to Delta ($c$) due to sequential processing.
*   **Transitive Relationships:** Because the user sends a request ($a \rightarrow b$), and Expedia processes that request sequentially before contacting Delta ($b \rightarrow c$), and Delta receives that message ($c \rightarrow d$), it follows that $a \rightarrow d$.

#### 2.3 Concurrent Events
Events are **concurrent** if there is no "happened-before" relationship between them. 
*   If event $a$ is on node $N_1$ and event $b$ is on node $N_2$, and there is no communication (direct or transitive) linking them, they are concurrent.
*   One cannot assert any real-time ordering for concurrent events; in one execution $a$ might appear to happen before $b$, while in another $b$ might appear to happen before $a$.
*   **Logic Trap:** Having a timestamp $C(a) < C(b)$ does **not** inherently mean $a \rightarrow b$ unless the events are in the same process or linked by communication.

---

### 3. Lamport’s Logical Clock
Logical clocks provide a theoretical underpinning for deterministic execution by associating a timestamp with every event.

#### 3.1 Implementation Mechanism
Each node $P_i$ maintains a local counter $C_i$ (a simple monotonically increasing integer).
*   **Internal Events:** For every local computational event, the counter is incremented.
*   **Send Events:** When $P_i$ sends a message, it attaches its current local timestamp to the message.
*   **Receive Events:** When $P_j$ receives a message from $P_i$ with timestamp $T_{msg}$, it must update its local clock $C_j$ to ensure the receive event $d$ has a timestamp greater than the send event $a$.
    *   **Calculation:** $C_j(d) = \max(\text{current local counter}, T_{msg}) + 1$.

#### 3.2 Limits of Logical Time
Lamport’s logical clock provides only a **partial order**. While $a \rightarrow b$ guarantees $C(a) < C(b)$, the reverse is not true: $C(x) < C(y)$ does not guarantee $x \rightarrow y$ because the events might be concurrent.

#### 3.3 Deriving Total Order
To make unambiguous local decisions (e.g., in a distributed lock), a **total order** is required.
*   **Total Order Rule:** $a$ precedes $b$ if:
    1.  $C(a) < C(b)$, OR
    2.  $C(a) = C(b)$ and an arbitrary, well-known condition (tie-breaker) is applied.
*   **Tie-Breaking:** A common tie-breaker is the **Process ID (PID)**. If timestamps are equal, the process with the lower PID wins.
*   **Purpose:** Once a total order is established, the specific logical timestamps become meaningless; they are merely a vehicle to reach the unambiguous ordering.

---

### 4. Distributed Mutual Exclusion (The Lock Algorithm)
This algorithm applies Lamport's clocks to manage shared resources without shared memory.

#### 4.1 Algorithmic Steps
1.  **Requesting the Lock:** A process $P_i$ sends a timestamped request to **all** $N-1$ peers and places the request in its own private queue.
2.  **Receiving a Request:** Peers place the incoming request into their local queues, ordered by timestamp (breaking ties with PID). They then send an **Acknowledgment (ACK)** back to the requester.
3.  **Acquiring the Lock:** $P_i$ can locally decide it has the lock if two conditions are met:
    *   Its own request is at the **top** of its local queue.
    *   It has received **ACKs from everyone** (or received subsequent requests from everyone that are later than its own timestamp).
4.  **Releasing the Lock:** $P_i$ removes its entry from its local queue and sends an **Unlock** message to all peers. Peers then remove $P_i$’s entry from their respective queues.

#### 4.2 Messaging Complexity
*   **Standard Complexity:** To acquire and release a lock, a process sends:
    *   $N-1$ requests.
    *   $N-1$ ACKs received.
    *   $N-1$ unlocks.
    *   **Total:** $3(N-1)$ messages.
*   **Optimization:** ACKs can be deferred. If a node receives a request with a timestamp later than its own pending request, it can wait until it unlocks to send a message. This combined "Unlock/ACK" reduces complexity to **$2(N-1)$** messages.

#### 4.3 Correctness Assumptions
The algorithm relies on two fundamental assumptions:
1.  **Ordered Delivery:** Messages between any two processes arrive in the order they were sent.
2.  **No Message Loss:** Every message sent is eventually received.



---

### 5. Remote Procedure Call (RPC) Latency Components
RPC performance is critical for client-server distributed systems. While an RPC appears as a simple local procedure call to the application developer, it involves a complex seven-step process across hardware and software layers.

#### 5.1 The Seven-Step Latency Model
1.  **Client Call:** The client program prepares arguments and invokes the kernel. The kernel validates the call and **marshals** arguments into a network packet.
2.  **Controller Latency:** The network controller performs a **Direct Memory Access (DMA)** to move the packet from system memory into its internal buffer and onto the wire.
3.  **Time on the Wire:** The physical propagation delay determined by the distance between nodes, speed of light, and intermediate routers.
4.  **Interrupt Handling:** Upon arrival at the destination, the message triggers an OS interrupt. The OS moves bits from the controller buffer into system memory.
5.  **Server Setup:** The OS locates and dispatches the server procedure, then **unmarshals** the network packet back into procedure arguments.
6.  **Server Execution:** The actual computation of the procedure logic. This is determined by the application developer, not the OS designer.
7.  **Return Path:** Steps 2, 3, and 4 are repeated in reverse to deliver results back to the client.

#### 5.2 Latency vs. Throughput
*   **Latency:** The total elapsed time for a single application-generated message to reach its destination and return.
*   **Throughput (Bandwidth):** The number of events or bits that can be executed/transmitted per unit of time.
*   **Distinction:** Increasing bandwidth (e.g., a wider "hallway") improves throughput but does not necessarily lower the latency (the time it takes for one person to "walk" the distance).

---

### 6. RPC Source of Overhead I: Marshaling and Data Copying
Marshaling is the process of gathering disparate procedure arguments from a process's stack and organizing them into a contiguous network packet.

#### 6.1 The "Three-Copy" Problem
Standard RPC implementations often suffer from three distinct data copy operations:
1.  **User-Space Copy:** The **client stub** copies arguments from the stack into a contiguous RPC message in user space.
2.  **Kernel-Boundary Copy:** The kernel copies this RPC message from user memory into a kernel-level buffer.
3.  **Hardware Copy:** The network controller uses DMA to copy the message from the kernel buffer to its internal controller buffer.

#### 6.2 Optimization: Reducing to Two Copies
Because the hardware DMA (Copy 3) is typically inevitable, OS designers focus on eliminating the software-driven copies.
*   **Stub-in-Kernel Approach:** The client stub is installed directly into the kernel at bind time. This allows the stub to marshal arguments directly from the user stack into the kernel buffer, eliminating the intermediate user-space RPC message copy. This requires a trusted relationship between the application and the kernel.
*   **Shared Descriptors:** Instead of moving the stub, the user-space stub and kernel share a **descriptor**. This descriptor contains the starting addresses and lengths of each data item on the stack. The kernel uses this "map" to pull data directly from the stack into its internal transmission buffer.

---

### 7. RPC Source of Overhead II: Control Transfer (Context Switches)
RPC follows a blocking semantic; the client remains suspended until the server returns a result. This necessitates multiple context switches.

#### 7.1 Identifying Critical Path Switches
A naive RPC involves four context switches:
1.  **Client-Side Switch Out:** Switching from the calling client to another process (C1) to keep the CPU utilized while waiting for the network.
2.  **Server-Side Switch In:** Switching from a background process (S1) to the server procedure (S) when the request arrives.
3.  **Server-Side Switch Out:** Switching from the server (S) back to a background process (S2) once the result is sent.
4.  **Client-Side Switch In:** Switching back to the original client when the result arrives.

Only **Switches 2 and 4** are in the critical path of RPC latency because they must occur before the procedure can execute or the result can be processed.

#### 7.2 Optimization: Reducing to One Switch
*   **Overlapping Communication:** Switches 1 and 3 can be performed in parallel with "time on the wire," effectively removing them from the total latency calculation.
*   **Spin-Waiting:** If an RPC is expected to return very quickly (e.g., over a fast LAN with a short server procedure), the client can **spin** (busy-wait) instead of context switching out. This eliminates Switch 4 entirely, reducing the critical path to a single inevitable context switch on the server side.

---

### 8. RPC Source of Overhead III: Protocol Processing
In a Local Area Network (LAN) environment, protocol stacks can be made "lean and mean" by assuming a reliable medium.

#### 8.1 Reliability Assumptions
*   **Low-Level ACKs:** Standard network protocols use acknowledgments to ensure delivery. In RPC, the **server's result** serves as an implicit ACK. If no result arrives, the client simply resends the call. Thus, low-level software ACKs are redundant and can be removed to reduce latency.
*   **Checksums:** Software-calculated checksums are latency-intensive. If the hardware provides packet integrity checks, software checksums should be bypassed.

#### 8.2 Buffering Strategies
*   **Client-Side Buffering:** This can be eliminated because the client can simply reconstruct the request from its own state if a retransmission is needed.
*   **Server-Side Buffering:** Results must be buffered because re-executing a complex server procedure is more expensive than storing the result. However, this buffering can be **overlapped** with the transmission of the result over the wire to hide its latency.

---

### 9. Physical Clocks and Real-World Synchronicity
Logical clocks fail in scenarios involving outside communication (e.g., a phone call) where events are ordered in real time but not through the system's internal message passing.

#### 9.1 Clock Drift Parameters
*   **Individual Clock Drift ($k$):** The rate at which a local clock deviates from absolute real time ($t$). A perfect clock has a drift of zero ($\frac{dCi}{dt} = 1$).
*   **Mutual Clock Drift ($\epsilon$):** The maximum disparity between any two local clocks $C_i$ and $C_j$ at any real time $t$.

#### 9.2 Conditions for Anomalous-Free Execution
To avoid real-world timing anomalies (e.g., a bank debit request arriving before a credit that was sent earlier in real time), the **Inter-Process Communication (IPC) time ($\mu$)** must dominate the drift.
*   **Condition:** Anomalies are avoided if the mutual drift ($\epsilon$) is significantly smaller than the time it takes for a message to travel between nodes ($\mu$).
*   **Formulaic Goal:** Individual drift ($k$) must be negligible compared to $\mu$, and the disparity between clocks must be within the IPC transmission window.



---
<div style="page-break-after: always;"></div>
---