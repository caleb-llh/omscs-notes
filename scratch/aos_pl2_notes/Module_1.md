# Module 1: Active Networks and Software Defined Networking (SDN)

## Introduction
* **Goal**: Optimize routing of network packets across the wide area internet by accommodating the Quality of Service (QoS) needs of individual packet flows.
* **Core Question**: Can intermediate hardware routers be made "smart" to execute specialized routing decisions?
* **Active Networks**: A thought experiment and architectural vision where routers dynamically execute code to process and route packets, a precursor to modern Software Defined Networking (SDN).

## Routing on the Internet: Passive vs. Active
### Traditional (Passive) Routing
* **Mechanism**: Source node sends a packet. Intermediate routers inspect the destination address and perform a passive table lookup to determine the next hop.
* **Role of Routers**: Routers simply forward packets; they do not inspect contents or execute custom logic.

### Active Networks Routing
* **Mechanism**: The next hop is determined actively by the router executing custom code.
* **Capsule**: Packets carry both the payload and the routing code (or a reference to it).
* **Advantage**: Virtualizes traffic flow, allowing customized services for specific network flows independent of others (similar to OS customization in SPIN or Exokernel).
* **Challenges**: 
  * Writing and distributing executable code over the network.
  * Ensuring injected code does not break the network or interfere with other flows.

## Motivating Example: Multicast Routing
* **Scenario**: Sending a single message (e.g., holiday greeting) to multiple recipients in a clustered geographic area.
* **Standard Approach**: Source sends N separate messages across the internet, wasting bandwidth.
* **Active Networks Approach**: Source sends **1 message**. An active router near the destination recognizes the intent, demultiplexes the message, and forwards it to the N recipients. 
* **Result**: Highly frugal use of network resources.

## Implementing the Vision
* **Ideal Implementation**:
  * OS provides QoS APIs (e.g., specifying real-time video constraints).
  * The OS synthesizes executable code representing these constraints and adds it to the packet payload.
  * Intermediate internet routers execute this code to make intelligent decisions (e.g., multicasting down specific links).
* **Roadblocks to the Ideal**:
  1. **Non-trivial OS modifications**: Changing the TCP/IP stack (hundreds of thousands of lines of code) across all nodes is impractical.
  2. **Closed routers**: Network routers (from vendors like Cisco) are proprietary and not designed to process custom code.

## The ANTS Toolkit
* **ANTS (Active Node Transfer System)**: An application-level package designed to demonstrate Active Networks without modifying the core OS protocol stack.
* **Capsule Architecture**:
  * The application provides the payload and QoS constraints.
  * ANTS creates an **ANTS Header** and prepends it to the payload to form a **Capsule**.
  * The standard OS protocol stack simply treats the Capsule as data and adds a standard **IP Header**.
  * **Packet Format**: `[ IP Header | ANTS Header | Application Payload ]`
* **Incremental Deployment**:
  * **Normal IP Routers**: Ignore the ANTS header and route passively using the IP header.
  * **Active Nodes**: Parse the ANTS header and execute custom routing logic.
* **Edge Deployment Strategy**: Active nodes are placed strictly at the **edge** of the network. The high-speed core IP network remains unchanged, solving the deployment roadblock.

## ANTS Capsule and API Details
### Capsule Header Fields
* **Type Field**: A cryptographically strong fingerprint (e.g., MD5 hash) of the code needed to process the capsule. *Note: Capsules carry a reference to the code, not the code itself.*
* **Prev Field**: The identity of the upstream node that successfully processed this capsule type.

### ANTS API
Designed to be minimal, easy to program, fast to execute, and easy to debug.
1. **Routing API**: Primitives to intelligently forward packets and virtualize network topology.
2. **Soft Store API**: A key-value storage system on every active router.
   * Uses `put object` and `get object` primitives.
   * Stores the actual processing code associated with a capsule `Type`.
   * Stores computed hints about network state for future capsules of the same flow.
3. **Querying API**: Retrieves router state (e.g., node identity, local time).

## Capsule Processing Implementation
When a capsule arrives at an active node:
1. **Code Exists (Cache Hit)**: If the node has seen this `Type` before, it retrieves the code from its Soft Store, executes it, and routes the capsule.
2. **Code Missing (Cache Miss)**: 
   * The node uses the `Prev` field to request the code from the upstream node.
   * The upstream node sends the code.
   * The current node stores it in the Soft Store for future packets in the flow (exploiting locality).
3. **Security Check**: Upon receiving the requested code, the node hashes it and compares it to the `Type` field. If they match, the code is genuine (prevents code spoofing).
4. **Code Unavailability**: If the previous node has evicted the code from its limited Soft Store, the current node simply **drops the capsule**. Higher-level protocols (like TCP) will handle end-to-end retransmission, matching standard IP semantics.

## Potential Applications
Active networks provide network-layer functionality (not end-user applications). Applications must be expressible, compact, fast, and tolerant of partial active node deployment.
* Protocol-independent / Reliable multicast.
* Network congestion notification to source and destination.
* Private IP anycasting.
* Overlaying a custom virtual topology on top of the physical internet.

## Pros, Cons, and Threats
### Pros
* **Unprecedented Flexibility**: Applications can ignore physical network layout and virtualize flows to suit their exact needs.

### Cons & Protection Threats (and ANTS Safeguards)
1. **Runtime Safety**: Malicious code could crash the router or harm other flows.
   * *Safeguard*: ANTS uses Java sandboxing to isolate code execution.
2. **Code Spoofing**: Attackers could inject malicious routing code.
   * *Safeguard*: Cryptographic fingerprinting (`Type` field) guarantees code integrity.
3. **Soft State Integrity**: A flow could exhaust the router's memory.
   * *Safeguard*: The restricted ANTS API limits resource consumption per flow.
4. **Resource Management / Network Flooding**: Rogue multicasting could flood the network.
   * *Mitigation*: The internet is already susceptible to spam/flooding. ANTS limits node-level abuse, but network-wide flooding remains a general internet challenge.

## Feasibility and Roadblocks
* **Vendor Buy-in**: Router makers (e.g., Cisco) are loath to open their proprietary hardware to arbitrary code execution.
* **Performance Impedance**: Core internet routers handle hundreds of gigabytes per second in hardware. Software-based routing cannot match this speed, restricting Active Networks to the network **edge**.
* **Social/Psychological Barriers**: Users and corporations are uncomfortable with public routers dynamically executing code on their private data due to privacy and security concerns.

## Conclusion: From Active Networks to SDN
* **Historical Context**: Active Networks emerged in the 1990s as a "solution looking for a problem." It prioritized safety over raw performance and lacked a killer application.
* **Rebirth as SDN**: Modern challenges in data centers, cloud computing, and virtualization gave the concept a new lease on life as **Software Defined Networking (SDN)**.
* **Utility Computing**: Cloud providers host multiple competing tenants (e.g., Coke and Pepsi) on the same physical infrastructure. This requires perfect isolation and virtualization of the physical network.
* **SDN**: Achieves this virtualized, isolated network layer, fulfilling the core vision of Active Networks in a centralized, data-center context.