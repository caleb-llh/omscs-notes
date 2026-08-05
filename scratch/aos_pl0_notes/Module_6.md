# Module 6: Operating System Extensibility (SPIN & Exokernel)

## 1. Introduction and Goals of OS Structure
The primary goal of modern OS structure is to achieve **extensibility** without compromising **protection** or **performance**.
- **Monolithic Design:** Offers high performance and protection but lacks extensibility (policies are heavily ingrained in the kernel).
- **Microkernel Design:** Highly extensible and portable, but compromises performance due to frequent border crossings (context switches between kernel and user-space servers).

### Core Goals for an Ideal OS Structure
- **Thin Kernel:** Only mechanisms should reside in the kernel; policies should be implemented externally.
- **Fine-Grained Access:** Resource access should occur without expensive border crossings, resembling a DOS-like structure.
- **Flexibility:** Resource management should be easily adaptable to suit specific application needs.
- **Performance & Protection:** Must match the speeds and security guarantees of a monolithic kernel.

---

## 2. Historical Approaches to Extensibility
- **Hydra OS (CMU, 1981):** 
  - Provided kernel mechanisms (not policies) for resource allocation.
  - Used a **Capability-based approach** (unforgeable, verifiable tokens passed between objects).
  - *Drawback:* Capabilities were a heavyweight mechanism. To reduce border-crossing overhead, Hydra used coarse-grained objects, which severely limited customization and extensibility.
- **Mach OS (CMU, early 90s):**
  - A microkernel design providing limited mechanisms; OS services ran as user-level server processes.
  - *Focus:* Portability and extensibility.
  - *Drawback:* Poor performance due to frequent border crossings gave microkernels a bad reputation.

---

## 3. The SPIN Approach to Extensibility
**Core Idea:** Co-locate a minimal kernel and its extensions within the same hardware address space to completely avoid border-crossing overhead.

### Language-Enforced Protection
Instead of relying on hardware address spaces for protection, SPIN relies on the characteristics of a **strongly typed programming language (Modula-3)**.
- **Modula-3 Features:** Built-in safety, encapsulation, automatic memory management (no memory leaks), objects with well-defined entry points, threads, and exceptions.
- **No Typecasting:** Unlike C, pointers cannot be forged or arbitrarily cast to bypass protection, ensuring compile-time checking and runtime modularity.

### Logical Protection Domains
- **Definition:** Data abstractions (like objects) serve as containers for logical protection domains. 
- The kernel provides only generic interfaces; domains implement the actual functionality.
- Applications can dynamically bind to different implementations of the same interface, providing flexibility.
- **Capabilities as Pointers:** Access to resources is provided via capabilities, which in SPIN are simply language-supported pointers. This makes them extremely cheap and lightweight compared to traditional capabilities.
- *Result:* Extensions become as cheap as standard procedure calls while maintaining monolithic-level safety.

### SPIN Mechanisms for Protection Domains
SPIN provides three core mechanisms to manage domains:
1. **Create:** Initiates an object file and exports its entry point method names to be visible externally.
2. **Resolve:** Dynamically links (binds) a source and target logical protection domain. Once resolved, access happens at memory speeds (like a procedure call).
3. **Combine:** Aggregates multiple protection domains into a single larger domain (a union of entry points) to combat the proliferation of many small domains.

**Example Extensions:**
- Implementing a full UNIX OS as an extension on top of SPIN.
- Running a client-server application (like a video server and its display client) directly on top of SPIN without a traditional OS middleman.

### Event-Based Communication in SPIN
SPIN handles external events (interrupts, page faults, system calls) via an event dispatcher:
- **Event Handlers:** Services register handlers with the central dispatcher.
- **Mappings Supported:**
  - **1:1 Mapping:** E.g., ICMP packet arrival triggers the Ping application handler.
  - **1:Many Mapping:** E.g., IP packet arrival triggers UDP, TCP, and ICMP handlers.
  - **Many:1 Mapping:** E.g., Ethernet and ATM packet arrivals both map to the same IP handler.
- **Guards:** Handlers can specify guards for finer-grained execution (e.g., only execute the handler if the incoming packet is strictly an IP packet).

### Default Core Services in SPIN
SPIN provides interface functions (header files), while extensions implement the semantics:
- **Memory Management:** SPIN handles the macro-allocation of physical memory to extensions. Interface functions include allocating/deallocating frames and virtual pages, translating addresses, and event handlers for page/access faults.
- **CPU Scheduling:** Uses a global scheduler for macro-level time allocation. 
  - **Strand:** The abstraction for the unit of scheduling. The extension defines the exact semantics of a strand (e.g., mapping to POSIX threads).
  - Events provided include block, unblock, checkpoint, and resume.

---

## 4. The Exokernel Approach to Extensibility
**Core Idea:** Expose hardware explicitly to library operating systems (Library OS) and decouple the **authorization** of a hardware resource from its **actual use**.

### Secure Bindings
- The Library OS requests a resource. Exokernel validates the request, binds the resource, and returns an **encrypted key (capability)**.
- The Library OS presents this unforgeable key to the Exokernel for subsequent uses of the resource.
- *Result:* Establishing the secure binding is a heavy-duty operation, but using the binding occurs at hardware speeds with minimal Exokernel intervention.

### Mechanisms for Implementing Secure Bindings
1. **Hardware Mechanisms:** e.g., Granting a physical page frame, TLB entry, or portion of a frame buffer.
2. **Software Caching:** e.g., Shadow TLB (sTLB) to avoid massive context switch penalties.
3. **Downloading Code into Kernel:** e.g., Installing a packet filter or garbage collector. Allows the Library OS to inject code to run at kernel privilege, avoiding border crossings. 
   - *Security Note:* This compromises protection more than SPIN's language-enforced domains (since arbitrary code is injected), but is necessary for maximum performance.

### Exokernel Candidate Resources
- **TLB Entry:** The Library OS establishes a virtual-to-physical mapping and presents it to Exokernel with a key. Exokernel securely installs it into the hardware TLB. Future translations by the process happen entirely via hardware.
- **Packet Filter:** The Library OS loads predicates into the kernel. Exokernel automatically checks incoming packets against these predicates without expensive border crossings to the Library OS.

### Default Core Services in Exokernel
- **Memory Management (Page Faults):** 
  - A thread incurs a page fault. Exokernel fields it and kicks it up to the currently running Library OS via a registered handler.
  - The Library OS allocates a frame, maps the virtual page, and presents the mapping + encrypted key to Exokernel.
  - Exokernel validates the key and performs the privileged operation of installing the mapping into the hardware TLB.
- **CPU Scheduling:** 
  - Exokernel maintains a **linear vector of time slots (epochs)**. Each Library OS marks its time quantums at startup.
  - Exokernel enforces bounded time for context switching. If a Library OS misbehaves (takes too long to save context), Exokernel penalizes it by taking time off its next scheduled slot.
- **Revocation of Resources:**
  - Exokernel can reclaim resources via an upcall (`revoke`) providing a **repossession vector** (e.g., "taking away page frames 20 and 25").
  - The Library OS must take corrective action (e.g., stash frame contents to disk).
  - **Autosave Seeding:** A Library OS can pre-seed Exokernel with autosave instructions so Exokernel performs the cleanup (e.g., writing to disk) on its behalf during revocation.

### Exokernel Data Structures
- **PE (Processor Environment) Data Structure:** Maintained per Library OS. Contains entry points for handling program discontinuities:
  - Exceptions
  - External Interrupts
  - System Calls (Protected Entry Context)
  - Page Faults (Addressing Context)
- **Software TLB (sTLB):** Maintains a snapshot of "guaranteed mappings" for each Library OS. On a context switch, Exokernel dumps current guaranteed mappings into the outgoing OS's sTLB and preloads the incoming OS's sTLB into the hardware TLB, drastically mitigating the loss of locality.

---

## 5. Performance Results (SPIN vs. Exokernel)
- **Evaluation Context:** Systems research relies on building and measuring. SPIN and Exokernel were compared against Monolithic OS (Unix) and Microkernel OS (Mach).
- **Protected Procedure Calls (Cross-Domain):** Both SPIN and Exokernel vastly exceed the performance of the Mach microkernel.
- **System Calls:** Both SPIN and Exokernel perform just as well as traditional monolithic kernels, proving that extensibility can be achieved without sacrificing performance.