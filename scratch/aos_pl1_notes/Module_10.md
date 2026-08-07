# Module 10: Optimizing Distributed Systems & RPC Latency

## Introduction
* **Lamport's Clocks:** A fundamental ordering mechanism for events in distributed systems, serving as the theoretical underpinning for achieving deterministic execution despite network non-determinism.
* **Context:** Modern everyday services (email, social networks, e-commerce, online education) are distributed. Network communication is the key to their performance.
* **Goal:** The operating system (OS) must strive to reduce the latency incurred in system software for network services. This module focuses on techniques to make the OS software stack efficient for network communication, both at the application interface and within the protocol stack.

## Latency vs. Throughput
Understanding the difference between latency and throughput is critical. 
* **Latency:** The elapsed time for an event to complete (e.g., the time it takes one person to walk from an office to a classroom).
* **Throughput:** The number of events that can be executed per unit time (e.g., the number of people arriving at the classroom per minute when walking side-by-side).
* **Bandwidth:** A measure of throughput. Increasing bandwidth improves throughput but does **not** lower latency. Lowering latency requires targeted optimization.

## Network Transmission Overheads
Remote Procedure Call (RPC) is the foundation of client-server distributed systems. RPC latency is the time it takes for an application-generated message to reach its destination and return. Latency consists of two components:
1. **Hardware Overhead:** Depends on how the network interfaces with the CPU. 
   * Modern network controllers use **Direct Memory Access (DMA)** to move bits directly from the system memory into their private buffer via the bus, without CPU intervention.
   * Hardware latency includes this DMA transfer and the time to put bits on the wire.
2. **Software Overhead:** The latency the OS adds to prepare the message in memory for transmission.
   * **Focus for OS Designers:** Reduce the software overhead and accept the baseline hardware overhead to minimize total latency.

## Components of RPC Latency
A standard RPC involves a 7-step process (excluding the actual server execution time):

### The Call Path
1. **Client Call (Software):** The client sets up arguments, makes a kernel call, and the kernel validates and marshals the arguments into a network packet, setting up the controller.
2. **Controller Latency (Hardware):** The controller uses DMA to move the message into its buffer and transmits it onto the wire.
3. **Time on the Wire (Hardware):** Time taken to travel from client to server (limited by bandwidth, distance, routers).
4. **Interrupt Handling (Software):** The message arrives at the destination node as an interrupt. The OS moves the bits from the controller buffer into node memory.
5. **Server Setup (Software):** The OS locates and dispatches the server procedure, and unmarshals the network packet into actual arguments.

### Execution
6. **Server Execution:** The server executes the procedure (dependent on application logic, not OS overhead).

### The Return Path
7. **Result Transmission:** 
   * Server marshals results into a network packet (repeats step 2).
   * Time on the wire back to the client (repeats step 3).
   * Result arrives as an interrupt on the client node (repeats step 4).
   * Client OS redispatches the client to receive results and resume execution.

## Sources of Software Overhead in RPC
The three primary sources of OS overhead in an RPC call are: **Marshaling and Data Copying**, **Control Transfer**, and **Protocol Processing**.

### 1. Marshaling and Data Copying
**Definition:** Marshaling is the process of accumulating application-specific arguments into a contiguous network packet that the kernel can transmit. The kernel does not understand the semantics of these arguments.
* **The Problem (3 Copies):** 
  1. The client stub copies arguments from the stack to create an RPC message in user space.
  2. The kernel copies the RPC message from user space into the kernel buffer.
  3. The network controller copies the bits from the kernel buffer to its internal buffer using DMA (unavoidable hardware copy).
* **The Solution (Reducing to 2 Copies):** Eliminate the intermediate user-space copy.
  * **Technique A: Push Stub into the Kernel:** Install a synthesized client stub inside the kernel at bind time. The kernel stub directly marshals arguments from the stack into the kernel buffer. *Drawback: Requires trusting user code injected into the kernel.*
  * **Technique B: Shared Descriptor:** Keep the stub in user space, but use a shared descriptor to tell the kernel the memory layout (starting address and length) of each argument on the stack. The kernel uses this descriptor to directly assemble the packet into its buffer.

### 2. Control Transfer (Context Switches)
An RPC call can potentially trigger four context switches:
1. **Client Box:** Client blocks waiting for results $\rightarrow$ OS switches to another process (C1).
2. **Server Box:** RPC arrives $\rightarrow$ OS switches from current process (S1) to server process (S).
3. **Server Box:** Server finishes $\rightarrow$ OS switches to another process (S2) to keep the CPU utilized.
4. **Client Box:** Results arrive $\rightarrow$ OS switches back to the client process (C).

* **Critical Path Analysis:**
  * Switches 1 and 3 are merely to keep the CPUs utilized and can be overlapped with network communication. They are **not** in the critical path.
  * Switches 2 and 4 **are** in the critical path.
* **The Solution (Reducing to 1 Context Switch):**
  * **Spin instead of Switch:** If operating on a fast Local Area Network (LAN) and the server procedure is short, the client can actively **spin** (wait) instead of context switching. 
  * This eliminates the client-side context switches (1 and 4). 
  * The server-side context switch (2) remains an unavoidable necessity to process the unpredictable incoming call.

### 3. Protocol Processing
When operating on a reliable Local Area Network (LAN), performance and latency are prioritized over extreme reliability measures.
* **Optimizations for Lean Protocol Processing:**
  * **Eliminate Low-Level Acknowledgements (ACKs):** The high-level semantics of RPC act as implicit ACKs. The return result acknowledges the call; if lost, the client simply resends the call.
  * **Hardware Checksums:** Rely on hardware-generated checksums for packet integrity rather than computing them in software.
  * **Eliminate Client-Side Buffering:** Because the client is blocked and its stack remains intact, it can reconstruct and resend the call if needed. There is no need for the OS to buffer the outgoing message.
  * **Overlap Server-Side Buffering:** The server *must* buffer its outgoing results (to avoid re-executing an expensive procedure if the result is lost). However, this buffering can be overlapped with the actual transmission of the message to keep it out of the critical path.

## Conclusion
To minimize RPC latency, OS designers focus on streamlining the software stack:
* **Reduce Data Copies:** Use kernel stubs or shared descriptors.
* **Reduce Context Switches:** Spin on the client side instead of switching.
* **Streamline Protocol Processing:** Leverage LAN reliability to eliminate ACKs, use hardware checksums, and optimize buffering. 
* Hardware latency (like DMA and time on the wire) is generally accepted as the baseline performance limit.