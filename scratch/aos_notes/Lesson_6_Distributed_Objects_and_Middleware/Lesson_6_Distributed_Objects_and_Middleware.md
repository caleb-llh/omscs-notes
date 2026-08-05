# Lesson_6_Distributed_Objects_and_Middleware (Synthesized Notes)

# Module 3: Distributed Object Technology and the Spring Operating System

## 1. Introduction
- **Context:** Component-based design reduces development pain points in complex distributed software. Designing for continuous and incremental evolution in both functionality and performance requires distributed object technology.
- **The Spring System:** A network operating system designed and implemented by Sun Microsystems for local area networks (LANs). It was later marketed as Sun's Solaris MC.
- **Key Architect:** Yusuf Khalidi, who previously developed the object-based Clouds OS at Georgia Tech and later headed Microsoft Azure.

## 2. OS Innovation Strategy: "Under the Covers"
- **The Conundrum in Industry:** Whether to build a brand new OS or build a better implementation of a known OS. Market demand and legacy applications often rule out entirely new OS interfaces.
- **Sun's Approach:** "Innovate under the covers" (similar to the "Intel Inside" microarchitecture strategy).
  - **Retain the External Interface:** Keep the standard UNIX interface to preserve the customer base and legacy applications.
  - **Internal Innovation:** Innovate internally using object orientation.
  - **Third-Party Integration:** Provide new APIs allowing third-party vendors to develop and integrate software seamlessly without breaking existing systems.
  - **Goal:** Preserve standard OS benefits while enabling extensibility and flexibility.

## 3. Procedural vs. Object-Based Design
- **Procedural Design (Monolithic Kernels):**
  - Code is written as one monolithic entity.
  - State is shared globally or distributed privately across subsystems.
  - Interfaces rely on standard procedure calls, leading to state strewn all over the system.
- **Object-Based Design (Spring OS):**
  - State is entirely contained within the object and is strictly invisible externally.
  - Only well-defined invocation methods are exposed.
  - **Advantages:** Strong interfaces and complete isolation of state, enabling safer border crossing and easier extensibility.

## 4. The Spring OS Approach
- **Strong Interfaces:** Subsystems only expose *what* services they provide, not *how* they are implemented. Implementations can be swapped out seamlessly.
- **Open and Flexible:** Interfaces are defined using an Interface Definition Language (IDL) from the OMG group. This prevents the system from being tied to a single programming language.
- **Microkernel-Based Extensibility:** 
  - **Nucleus:** Spring's microkernel; provides abstractions for threads and Inter-Process Communication (IPC).
  - **Virtual Memory (VM) Manager:** Provides memory management.
  - **Spring Kernel:** Composed of the Nucleus + VM Manager. Note that while Liedtke's microkernel principle includes address space, Spring separates the VM Manager from the Nucleus, though both form the kernel.
  - **Outside the Kernel:** Network proxies, X11 servers, shells, file systems, and protocol stacks operate as user-level services.

## 5. The Nucleus (Spring's Microkernel)
- **Domains:** Containers or address spaces, analogous to UNIX processes. Threads execute within domains.
- **Doors (Software Capabilities):** 
  - Entry points into a target domain.
  - A client obtains a "door handle" (conceptually similar to a UNIX file descriptor).
  - Represented by a pointer to a C++ object of the target domain.
  - **Door Table:** Unique to every domain; stores door handles pointing to specific doors.
  - Doors can be passed between domains.
- **Fast Cross-Domain Object Invocation:**
  - When a client invokes a door, the client thread is deactivated.
  - A server thread in the target domain is allocated and activated to execute the invocation (protected procedure call).
  - On return, the server thread is deactivated and the client thread is reactivated.
  - This thread-handoff mechanism ensures performant, fast cross-address-space calls.

## 6. Object Invocation Across the Network
- **Network Proxies:** Extend object invocation across the network transparently.
  - Proxies are invisible to both the client and the server.
  - Different proxies can employ different protocols based on network proximity (LAN vs. WAN).
- **Mechanism:**
  - **Proxy A** (Server-side) exports a network handle embedding the server's Door X to **Proxy B** (Client-side).
  - **Proxy B** establishes a local Door Y for the client domain.
  - The client invokes Door Y, believing it is directly accessing the server.
  - Proxy B communicates over the network handle to Proxy A.
  - Proxy A uses the actual Door X to invoke the server domain.
  - **Note:** Communication between proxies happens *outside* the Nucleus.

## 7. Secure Object Invocation
- **Front Objects:** Objects used to implement security and access control policies.
  - Sit between the client and the underlying object.
  - Check Access Control Lists (ACLs) before passing the invocation to the underlying object.
  - Multiple front objects can exist for different control policies on the same underlying object.
- **Differential Privileges:** Clients can pass capabilities (door handles) to other domains but can dynamically reduce their privilege levels. For example, a user can pass a "one-time print" capability of a file object to a printer object.

## 8. Virtual Memory Management in Spring
- **Linear Address Space:** The process address space provided by the architecture is divided into **regions** (sets of pages).
- **Memory Objects:** Abstractions for backing store entities (e.g., swap space, disk files). Regions of the linear address space map to these memory objects.
- **Pager Objects (External Pagers):** 
  - Manage the connection between virtual memory (memory objects) and physical memory (DRAM).
  - Create **cached object representations** in physical memory.
  - A single address space can have multiple pager objects managing different regions.
  - Coherence for a cached object shared across different address spaces is explicitly managed by the coordinating pager objects.

## 9. Dynamic Client-Server Relationships & Subcontracts
- **Location Transparency:** Clients and servers can be co-located or distributed without modifying client or server code.
- **Dynamic Routing:** Client requests can be dynamically routed to different server replicas (for load balancing/availability) or to cached copies (like web proxies).
- **Subcontracts (The Secret Sauce):**
  - A pluggable mechanism that hides the runtime behavior of an object from its IDL interface.
  - Handles the complexities of location, replication, and caching.
  - Can be dynamically discovered and installed at runtime.
  - Simplifies client-side stub generation by offloading marshalling, unmarshalling, and invocation routing.
  - **Server-side Subcontract:** Allows servers to revoke services or signal readiness.
  - **Legacy Impact:** Forms the conceptual foundation for modern distributed frameworks like **Java RMI** (Remote Method Invocation) and Enterprise JavaBeans.

## 10. Summary: Spring vs. Tornado
- **Spring OS:** Uses object technology comprehensively as a *system structuring mechanism* to build a flexible, extensible network OS with strong interfaces.
- **Tornado OS:** Uses clustered objects primarily as a *performance optimization mechanism* for implementing kernel services efficiently on multiprocessors.


---

# Module 4: Java RMI and Distributed Object Models

## Introduction
This module explores how distributed object technology influences commercial offerings, focusing specifically on **Java RMI (Remote Method Invocation)**, which is rooted in the fundamental principles of distributed systems.

## Java Language History
- **Origins**: Invented by James Gosling at Sun Microsystems in the early 90s.
- **Original Name**: Oak.
- **Initial Purpose**: Intended for use with embedded devices and PDAs.
- **Evolution**:
  - Sun initially considered Java for programming set-top boxes for video-on-demand (VOD) over the internet.
  - The cable TV industry chose SGI for VOD trials, causing Oak to fail in that market.
  - The rise of the World Wide Web gave Java new life due to the need for containing operations on client boxes connecting to the web.
  - Today, internet e-commerce and many enterprise applications rely heavily on the Java framework.

## Java Distributed Object Model
The Java remote object model abstracts much of the "heavy lifting" required in building a client-server system (e.g., RPC, marshalling, unmarshalling, publishing remote objects). This is handled under the covers by the Java distributed object runtime, similar to the **subcontract mechanism** in the Spring operating system.

### Key Definitions
- **Remote Object**: Objects that are accessible from different address spaces (often across a network).
- **Remote Interface**: Declarations for methods within a remote object that specify what is accessible to clients anywhere.
- **RMI Exception**: The failure semantics of the distributed object model. Clients must deal with exceptions that might occur during remote method invocations.

### Parameter Passing: Local vs. Remote Objects
- **Similarity**: Both local and remote object invocations can pass object references as parameters.
- **Difference**: 
  - **Local Objects**: Use **pass-by-reference**. The invoked method can modify the object passed to it, and changes are reflected in the original object.
  - **Remote Objects**: Use **pass-by-value-result**. A copy of the object is sent over the network. Modifications made by the invoked method are local to that copy and will not be seen by the client.

## Building a Service: Bank Account Example
To illustrate the Java distributed object model, consider a bank account server with APIs for deposit, withdrawal, and balance inquiries.

### Implementation Choices
1. **Reuse of Local Implementation**
   - **Process**: A developer extends a local `account` class to create a `bank account` implementation. Using the built-in `Remote` interface, the methods are made visible on the network.
   - **Drawback**: While the interface is public, the actual location of the instantiated object is hidden from the client. The implementer must manually do the heavy lifting to make the object's location visible.
   - **Virtue**: Allows the service provider to make selected servers visible only to selected clients.
2. **Reuse of Remote Object (Preferred)**
   - **Process**: The developer extends a remote object class.
   - **Advantage**: Java RMI does all the heavy lifting to make the server object visible and accessible to network clients. This is the preferred method for building network services.

## Java RMI at Work
### Client-Side Experience
- **Lookup**: The client contacts a bootstrap name server in the Java RMI system to look up the service provider's published URL.
- **Local Access Point**: Upon successful lookup, a local access point (stub) for the object is created on the client side.
- **Invocation**: The client calls methods (e.g., deposit, withdraw) as if they were normal local procedure calls. The client does not know or care about the server's actual location.
- **Failure Handling**: If a failure occurs, the server throws a remote exception back to the client via the Java runtime. The client must handle these exceptions, though it may not know exactly where or why the call failed mid-flight.

## RMI Implementation Layers

### 1. Remote Reference Layer (RRL)
The RRL is the core of the RMI implementation where the "magic" happens, heavily resembling the Spring system's subcontract mechanism.
- **Client Side**: The client-side **stub** initiates a remote call using the RRL. The RRL handles **marshalling** (serializing) arguments to send over the network and **unmarshalling** (deserializing) the results back into digestible data structures.
- **Server Side**: The **skeleton** unmarshals incoming arguments via the RRL and calls the server implementing the remote object. Once finished, it marshals the result and sends it back through the RRL.
- **Responsibilities**: The RRL handles details regarding server location, replication, persistence, and invocation protocols, making clients and servers oblivious to these underlying mechanics.

### 2. Transport Layer
The transport layer sits below the RRL. The RRL decides the most appropriate transport protocol (e.g., TCP or UDP) based on endpoint locations and network conditions, instructing the transport layer to establish the connection.

**Key Abstractions**:
- **Endpoint**: A protection domain or sandbox (like a Java Virtual Machine) where code executes. It maintains a table of accessible remote objects.
- **Connection Manager**: Responsible for setting up, tearing down, and listening for incoming connections. It locates the dispatcher for a invoked remote method and monitors the liveness of connections.
- **Channel**: A mutual agreement between two endpoints to communicate using a chosen transport protocol.
- **Connection**: Once a channel is established, the transport mechanism performs I/O over the channel using a connection.

*Note: A single endpoint can use different transport protocols (e.g., TCP for one, UDP for another) to communicate with various other endpoints based on connection manager decisions.*

## Conclusion
The Java RMI system turns advanced distributed systems research into highly usable technology. 
Further advanced topics in RMI implementation include:
- **Distributed Garbage Collection**
- **Dynamic Loading of Stubs** (on the client side)
- **Sophisticated Sandboxing Mechanisms** (to ward off security threats)


---

# Module 5: Structuring Complex Application Servers (Enterprise Java Beans)

## 1. Introduction
*   **Evolution:** Operating system structuring has evolved from single CPUs to parallel machines, then distributed systems, and now to large-scale distributed system services.
*   **Object Technology:** Uses innate concepts of inheritance and reuse to structure operating systems at different levels.
*   **Focus:** How to structure system software for large-scale distributed services (e.g., e-commerce, internet services).
*   **Definition - Java Bean:** A reusable software component. It is a bundle of Java objects providing a specific functionality (e.g., a shopping cart) that can be easily passed around from one application to another for reuse.

## 2. Enterprise Views and Challenges
*   **User View:** Users interact with an enterprise (e.g., Google, eBay) as a monolithic entity.
*   **Intra-Enterprise View:** Internally complex, consisting of interconnected services and servers (marketing, sales, production, inventory, etc.).
*   **Inter-Enterprise View (Supply Chain Model):** Enterprises talk to one another to fulfill requests. Service requests may involve multiple external entities.
*   **Mergers & Acquisitions:** When companies merge (e.g., DEC, Compaq, HP), the enterprise becomes an amalgam of different entities.
*   **Enterprise Transformation Challenges:**
    *   Interoperability of systems.
    *   Interface compatibility.
    *   System evolution.
    *   Scalability and reliability.
    *   Cost of maintaining complex systems.

## 3. Giant Scale Services vs. Local Services
*   **Definition - Giant Scale Services:** Internet-scale services used daily (e.g., Expedia, Gmail) as opposed to local organizational services (e.g., a local file server).
*   **Resource Conflicts:** Multiple concurrent users competing for physical resources (e.g., a seat on a flight) across space and time.
*   **System Issues:** Synchronization, communication, atomicity of actions, and concurrency are critical.
*   **Component Reuse:** Common features (like shopping carts) are needed across different domains (airline, train, hotel). Object technology allows reusing components to avoid "reinventing the wheel."

## 4. N-Tier Applications
*   **Definition:** Applications structured into multiple logical layers (tiers) to separate concerns.
*   **Application Stack Layers:**
    1.  **Presentation Layer:** Paints the screen on the browser and dynamically generates pages.
    2.  **Application Logic:** The specific service being provided.
    3.  **Business Logic:** Rules and decisions (e.g., how airfares are decided, seats allocated).
    4.  **Database Layer:** Accesses and stores necessary data.
*   **Key Issues in N-Tier Applications:**
    *   **Persistence:** Saving state for incomplete actions (e.g., unfinished booking).
    *   **Transactions:** Ensuring atomicity of operations.
    *   **Caching:** Storing pulled database data for faster access.
    *   **Clustering:** Grouping related services or data to improve performance.
    *   **Security:** Protecting financial and personal information.
*   **Structuring Goals:**
    *   Reduce network communication (lower latency).
    *   Reduce security risks (protect business logic).
    *   Increase concurrency (exploit "embarrassingly parallel" opportunities).
    *   Cluster computation for common queries.
    *   Reuse components aggressively (application logic and execution).

## 5. Structuring N-Tier Applications: JEE Framework
*   **Java Enterprise Edition (JEE):** A framework using containers (protection domains typically implemented in a JVM) to construct application services.
*   **Four JEE Containers:**
    1.  **Client Container:** Resides on the client side.
    2.  **Applet Container:** Interfaces with the end client's web browser.
    3.  **Web Container:** Manages presentation logic and dynamically creates web pages.
    4.  **EJB Container:** Manages the business logic.
*   **Types of Beans (Units of Reuse):**
    1.  **Entity Bean:** Represents persistent data (e.g., a row in a database with a primary key).
        *   *Bean Managed Persistence (BMP):* Persistence is built into the bean itself.
        *   *Container Managed Persistence (CMP):* Persistence is handled by the container hosting the bean.
    2.  **Session Bean:** Associated with a specific client and temporal session.
        *   *Stateful Session Bean:* Remembers client choices across the session (e.g., a Dell shopping cart).
        *   *Stateless Session Bean:* Retains no state between sessions (e.g., logging into Gmail).
    3.  **Message Driven Bean:** Handles asynchronous behavior (e.g., stock tickers, RSS news feeds).
*   **Granularity Trade-off:** Fine-grained beans enhance concurrency but increase business logic complexity. Coarse-grained beans keep logic simple but reduce concurrency.

## 6. Design Alternatives for Application Servers

### Design Alternative 1: Coarse-Grained Session Beans
*   **Structure:**
    *   *Web Container:* Contains Servlets (one per client) and Presentation Logic.
    *   *EJB Container:* Contains Coarse-Grained Session Beans.
*   **Workflow:** The session bean handles all specific needs and database accesses for its associated client servlet.
*   **Pros:**
    *   Requires minimal container services (mostly coordinating concurrent DB accesses).
    *   Business logic is confined within the corporate network (secure).
*   **Cons:**
    *   Monolithic structure.
    *   Lost opportunity for parallel database access (limited concurrency).

### Design Alternative 2: Data Access Objects (Entity Beans)
*   **Goal:** Increase parallelism for database access (the slowest link).
*   **Structure:**
    *   *Web Container:* Contains Servlet, Presentation Logic, AND Business Logic (3-tier structure).
    *   *EJB Container:* Contains Data Access Objects (DAOs) implemented as Entity Beans.
*   **Workflow:** Business logic fans out parallel requests to multiple entity beans, which access different parts of the database concurrently.
*   **Pros:**
    *   High concurrency and reduced latency (exploits parallel I/O and amortizes DB access across clients).
*   **Cons:**
    *   Moving business logic into the web container exposes it outside the corporate network, creating a security risk.

### Design Alternative 3: Session Bean with Entity Bean (Session Facade)
*   **Goal:** Achieve high concurrency without exposing business logic.
*   **Structure:**
    *   *Web Container:* Contains Servlet and Presentation Logic only.
    *   *EJB Container:* Contains Session Facade, Business Logic, and Entity Beans.
*   **Workflow:** The Session Facade (associated with a client) sits with the business logic in the EJB container. It fans out data access requests to multiple Entity Beans in parallel.
*   **Communication Choices (Session Facade to Entity Bean):**
    *   *Remote Interface (RMI):* Entity beans can be distributed anywhere on the network.
    *   *Local Interface:* Co-locates entity beans in the same EJB container, avoiding network communication overhead.
*   **Pros:**
    *   Best of both worlds: High concurrency (via Entity Beans) AND protected business logic (kept within the EJB container).
*   **Cons:**
    *   Incurs additional network access overhead (which can be mitigated by using Local Interfaces).

## 7. Conclusion
*   **Separation of Concerns:** Object technology (like EJB) allows developers to write pure business logic without worrying about cross-cutting concerns (security, logging, persistence), which are handled by the framework.
*   **Performance Implications:** Different design choices directly impact concurrency, resource pooling, network overhead, and code complexity.


---

