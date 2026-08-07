# Lesson 6: Distributed Objects and Middleware 

---

# VOLUME I: THE SPRING NETWORK OPERATING SYSTEM

## 1. Architectural Philosophy and Innovation Strategy
### 1.1. The Innovation Quadrant
In an industrial setting (e.g., Sun Microsystems), operating system innovation faces a dilemma: pursuing "lunatic fringe" academic ideas versus better implementations of known systems.
*   **Marketplace Constraints:** Industry must support legacy applications and maintain a stable customer base.
*   **Innovation Under the Covers:** Spring adopted the "Intel Inside" model. While the external interface remained standard **UNIX** to preserve the customer base, the internal structure was completely revolutionized using object technology.
*   **Extensibility:** The design allows third-party vendors to develop software against new APIs and integrate them without breaking the existing system.

### 1.2. Procedural vs. Object-Based Design
*   **Procedural Design:** Characterized by monolithic entities where state is distributed or shared across global variables. This leads to "state strewn all over the place," typical of monolithic kernels.
*   **Object-Based Design:** Objects encapsulate state entirely, making it invisible from the outside.
    *   **Isolation:** Interaction occurs only through strong, well-defined interfaces (methods).
    *   **Versatility:** This approach, also seen in systems like **Tornado**, provides flexibility and scalability.
    *   **Structuring vs. Optimization:** Unlike Tornado, which uses objects primarily for optimization (e.g., clustered objects), Spring uses object technology as a fundamental **system structuring mechanism**.

---

## 2. The Spring Microkernel Architecture
### 2.1. The Nucleus
The Nucleus is the microkernel of the Spring system, providing a subset of the abstractions prescribed by Liedtke.
*   **Core Abstractions:** It manages only **Threads** and **Inter-Process Communication (IPC)**.
*   **Domain:** A container or address space similar to a UNIX process where threads execute.
*   **Relationship to Liedtke’s Prescription:** While Liedtke suggests a microkernel should include threads, IPC, and address space, the Nucleus specifically omits address space management, which is handled at a higher level.

### 2.2. The Spring Kernel Boundary
The full "Spring Kernel" is a composition of the **Nucleus** and the **Virtual Memory (VM) Manager**.
*   **Kernel Composition:** Nucleus (Threads/IPC) + VM Manager (Address Space) = Spring Microkernel.
*   **External Services:** All other standard OS services (File Systems, X11 Display Managers, Protocol Stacks) reside above the kernel as objects.

---

## 3. Object Invocation Mechanisms
### 3.1. The "Door" Abstraction
A **Door** is a software capability to a domain, acting as a protected entry point into a target domain.
*   **Functionality:** If a domain (e.g., a file server) has entry points like `open()` or `read()`, it creates these as doors.
*   **Door Handles:** Clients access these entry points via a "Door Handle," similar to a UNIX file descriptor.
*   **Door Table:** Every domain maintains a unique door table. Possessing a handle in this table grants the ability to invoke methods in the corresponding target domain.
*   **Capability Passing:** Doors can be passed between domains, granting new domains the same access rights.

### 3.2. Protected Procedure Calls (PPC)
The Nucleus facilitates fast cross-address space calls using the door mechanism.
*   **Execution Flow:**
    1.  The client invokes a door handle.
    2.  The Nucleus verifies permissions.
    3.  The **client thread is deactivated**.
    4.  The Nucleus **allocates a server thread** in the target domain to execute the method.
    5.  Upon completion, the server thread is deactivated, and the client thread is reactivated.
*   **Performance:** This "thread hand-off" ensures high-performance cross-domain communication despite the object-oriented structure.

### 3.3. Security and Front Objects
Spring enables differential privilege levels (Access Control) through **Front Objects**.
*   **Front Object Role:** Acts as an intermediary between the client and the underlying object. It is NOT connected via the standard door mechanism; the connection is implementer-defined.
*   **Access Control Lists (ACL):** The front object checks the client’s credentials against an ACL before allowing invocation of the underlying object.
*   **Rights Attenuation:** A user can pass a door capability to another domain (e.g., a printer) but reduce the privilege level (e.g., granting only a one-time "ticket" to access a file) via a specialized front object.

---

## 4. The Subcontract Mechanism: The "Secret Sauce"
Subcontract is the mechanism that realizes the **IDL (Interface Definition Language)** contract between clients and servers while hiding runtime behavior.

### 4.1. Hiding Runtime Behavior
The client interacts with the server's IDL interface and remains oblivious to the server's implementation details.
*   **Implementation Variants:** A server could be a singleton, replicated across multiple nodes, or a cached proxy.
*   **Stub Generation:** Subcontracts simplify client-side stub generation because details like server location and replication are buried in the subcontract layer.

### 4.2. Dynamic Relationship Management
*   **Dynamic Loading:** New subcontracts can be discovered and installed at runtime.
*   **Adaptability:** If a singleton server is replicated, a new subcontract can be loaded to handle the replication without changing the client-side application code.

### 4.3. Interface for Stubs
*   **Marshaling/Unmarshaling:** Stubs call the subcontract to handle data serialization. The subcontract knows if the target is local, on a different processor, or on the network, and acts accordingly.
*   **Server Operations:** The subcontract allows the server to advertise its readiness or revoke services.

---

## 5. Network Distribution and Proxies
Spring is a network operating system where client-server proximity is transparent.

### 5.1. Network Proxies
Object invocation is extended across the network via **Network Proxies**.
*   **Transparency:** Clients and servers are unaware of whether they are on the same machine or different nodes.
*   **Protocol Specialization:** Different proxies can use different protocols (LAN vs. WAN) depending on the connection requirements.

### 5.2. Establishing Connection
1.  **Server Node:** Proxy A is instantiated and a local door is established to the server domain.
2.  **Exporting Handles:** Proxy A exports a **Network Handle** (embedding the door) to Proxy B on the client node. Note: This network handle interaction is outside the Nucleus's purview.
3.  **Client Node:** Proxy B establishes a local door (Door Y) for the client.
4.  **Invocation:** The client invokes Door Y. Proxy B uses the network handle to communicate with Proxy A, which then invokes the actual server door.

---

## 6. Virtual Memory Management (VMM)
VMM in Spring is highly flexible, allowing per-region management of the address space.

### 6.1. Address Space Segmentation
*   **Linear Address Space:** Managed by the VMM for every process.
*   **Regions:** The VMM carves the linear address space into regions (sets of pages) of varying sizes.

### 6.2. Memory Objects
*   **Abstraction:** Regions are mapped to **Memory Objects**.
*   **Backing Store:** Memory objects represent entities like swap space on a disk or memory-mapped files.
*   **Flexibility:** Multiple regions can map to one memory object, and multiple memory objects can map to the same backing file.

### 6.3. Pager Objects and Coherence
*   **Pager Object:** Responsible for establishing the connection between virtual and physical memory (DRAM).
*   **Cached Object Representation:** The pager creates a representation of the memory object in DRAM.
*   **External Pagers:** Spring allows any number of external pagers. A single address space can have different regions managed by different pager objects.
*   **Shared Memory Coherence:** If two address spaces share a memory object, the two associated pager objects are responsible for coordinating coherence, not the Spring system itself.


---

# VOLUME II: THE JAVA DISTRIBUTED OBJECT MODEL (RMI)

## 1. Historical Context and Evolution
### 1.1. Origins of Java
Java was originally developed by James Gosling at Sun Microsystems under the name **Oak**.
*   **Initial Target:** It was intended for personal digital assistants (PDAs).
*   **Pivot to Video-on-Demand:** In the 1990s, Sun attempted to position Java for programming set-top boxes, but the cable industry opted for SGIF.
*   **The Web Era:** Java found its true purpose with the rise of the World Wide Web, providing a framework for containment on client machines and eventually becoming a cornerstone of internet e-commerce.

### 1.2. Lineage from Spring
Java RMI is the direct spiritual and technical successor to the Spring Network Operating System.
*   **Subcontract Legacy:** The subcontract mechanism invented for Spring forms the technical basis for the **Remote Reference Layer (RRL)** in Java RMI.
*   **Innovation Under the Covers:** Like Spring, RMI abstracts the "heavy lifting"—such as marshaling, unmarshaling, and object publishing—away from the application developer and into the runtime system.

---

## 2. RMI Architecture and Semantics
### 2.1. Core Abstractions
*   **Remote Object:** An object that is accessible from different address spaces across a network.
*   **Remote Interface:** A collection of method declarations that define which operations of a remote object are accessible to clients.
*   **RMI Exceptions:** Because network invocations can fail in ways local ones cannot, clients must handle specific remote exceptions. A client may not know exactly where an invocation failed if an exception is thrown.

### 2.2. Parameter Passing: Local vs. Remote
A critical distinction exists between how Java handles local objects and remote objects:
*   **Local Semantics:** Passing an object reference allows the invoked method to modify the original object directly (pure reference).
*   **Remote Semantics (Value-Result):** When an object reference is passed to a remote method, the system actually sends a **copy** of the object. 
*   **Isolation:** Consequently, if a client modifies an object after passing its reference to a server, the server will not see those changes, as it is working with a local copy.

---

## 3. Implementation Layers
### 3.1. The Remote Reference Layer (RRL)
The RRL is the "magic" layer sitting between the stubs/skeletons and the transport layer.
*   **Data Handling:** It manages **serialization** (marshaling) and **deserialization** (unmarshaling) of Java objects.
*   **Invocation Protocols:** Like Spring's subcontracts, the RRL hides server details. It determines if a server is a singleton, replicated, or requires persistence.
*   **Transparency:** It allows for various invocation protocols while keeping the client and server application logic oblivious to these details.

### 3.2. The Transport Layer
The transport layer handles the physical movement of data between endpoints.
*   **Endpoint:** A protection domain, typically a Java Virtual Machine (JVM), containing a table of accessible remote objects.
*   **Connection Management:** This sub-component is responsible for setting up, tearing down, and listening for connections, as well as monitoring "liveness" to detect if an endpoint has failed.
*   **Channels and Transports:** When two endpoints agree to communicate, they establish a **Channel** and select a **Transport** (e.g., TCP or UDP) based on network conditions and proximity.

---

## 4. Programming Workflow
### 4.1. Server-Side Setup
1.  **Instantiation:** Create the server object.
2.  **URL Creation:** Assign a unique URL to the service.
3.  **Binding:** Use the Java runtime facility to bind the URL to the object instance in the naming service, making it discoverable.

### 4.2. Client-Side Access
1.  **Lookup:** Contact a bootstrap name server to find the published URL.
2.  **Local Access Point:** The system creates a local stub (access point) for the remote object.
3.  **Invocation:** The client calls methods on the stub as if they were local procedure calls. The Java runtime handles locating the server and executing the call.

---

# VOLUME III: ENTERPRISE JAVABEANS (EJB) AND N-TIER APPLICATIONS

## 1. The N-Tier Application Model
Complex internet services (e.g., Expedia, Gmail) are structured as N-Tier applications to handle "giant-scale" demands.
### 1.1. Structural Layers
*   **Presentation Layer:** Dynamically generates the user interface/web pages.
*   **Application/Business Logic:** Implements the core rules of the service (e.g., how airfares are calculated).
*   **Database Layer:** Manages persistent storage and retrieval of data.

### 1.2. Key Cross-Cutting Concerns
N-tier applications must address:
*   **Persistence:** Ensuring data or session state (like a shopping cart) survives even if a user leaves and returns.
*   **Transactions:** Ensuring complex operations (like booking a flight) are completed fully or not at all.
*   **Concurrency:** Exploiting "embarrassingly parallel" opportunities, such as querying multiple airlines simultaneously for one user request.
*   **Security:** Protecting sensitive user data (financial/personal) from compromise.

---

## 2. The JEE Container Framework
The Java Enterprise Edition (JEE) framework uses **Containers** (protection domains within a JVM) to package objects.
*   **Client/Applet Containers:** Reside on the client side or web server to handle browser interaction.
*   **Web Container:** Hosts the presentation logic and generates dynamic content.
*   **EJB Container:** Manages the business logic and provides system services like security and persistence.

---

## 3. The "Bean" as a Unit of Reuse
A **JavaBean** is a bundle of objects providing specific, reusable functionality.
### 3.1. Types of EJBs
*   **Entity Beans:** Represent persistent data, often a single row or set of rows in a database. They use primary keys for identification.
*   **Session Beans:** Associated with a specific client session.
    *   **Stateful:** Maintains state across multiple interactions (e.g., a multi-step purchase).
    *   **Stateless:** No state is preserved between calls (e.g., a standard email session).
*   **Message-Driven Beans:** Handle asynchronous behavior, such as RSS feeds, news tickers, or stock quote updates.

---

## 4. Design Alternatives for Application Servers
Developers face trade-offs between concurrency, security, and complexity when structuring EJBs.

### 4.1. Alternative 1: Coarse-Grained Session Beans
*   **Structure:** Each client session is mapped to a single session bean in the EJB container that handles all database access.
*   **Pros:** Minimal container overhead; business logic remains secure within the corporate network.
*   **Cons:** Low concurrency; behaves like a monolithic system because it cannot easily parallelize data access.

### 4.2. Alternative 2: Data Access Objects (Entity Beans)
*   **Structure:** Business logic is moved to the Web container. Data access is handled by many fine-grained Entity Beans in the EJB container.
*   **Pros:** High parallelism; multiple entity beans can fetch data simultaneously for a single request.
*   **Cons:** Security risk; moving business logic to the Web container exposes it to the external network.

### 4.3. Alternative 3: Session Facade (Session + Entity Beans)
*   **Structure:** Business logic is moved back to the EJB container into a "Session Facade." The facade then coordinates multiple Entity Beans for data access.
*   **Interface Options:** The facade can communicate with Entity Beans via **RMI** (flexible location) or **Local Interfaces** (co-located in the same container to avoid network latency).
*   **Pros:** "Best of both worlds"—maintains high concurrency through Entity Beans while keeping business logic secure in the EJB container.



---
<div style="page-break-after: always;"></div>
---